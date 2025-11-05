import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional, Tuple

import boto3
from boto3.s3.transfer import TransferConfig
from botocore.config import Config
from botocore.exceptions import ClientError, NoCredentialsError
from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    TaskID,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from leap_bundle.types.create import StsCredentials

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client
else:
    from botocore.client import BaseClient as S3Client

console = Console()

MULTIPART_THRESHOLD = 25 * 1024 * 1024  # 25MB
MULTIPART_CHUNKSIZE = 25 * 1024 * 1024  # 25MB
MAX_CONCURRENCY = 5
CONNECTION_TIMEOUT = 60
READ_TIMEOUT = 300


class UploadError(Exception):
    pass


class S3UploadManager:
    """Simplified S3 upload manager for directory uploads."""

    def __init__(self, max_workers: int = MAX_CONCURRENCY):
        self.max_workers = max_workers

        self.config = Config(
            retries={"max_attempts": 3, "mode": "adaptive"},
            max_pool_connections=50,
            connect_timeout=CONNECTION_TIMEOUT,
            read_timeout=READ_TIMEOUT,
        )
        self.transfer_config = TransferConfig(
            multipart_threshold=MULTIPART_THRESHOLD,
            max_concurrency=max_workers,
            multipart_chunksize=MULTIPART_CHUNKSIZE,
            use_threads=True,
        )
        self._s3_client: Optional[S3Client] = None

    @staticmethod
    def _extract_bucket_info(
        signed_url_data: Dict[str, Any],
    ) -> Tuple[str, str, Optional[str]]:
        """
        Extract bucket name, region, and key prefix from signed URL data.

        Returns:
            Tuple of (bucket_name, region, key_prefix)
        """
        fields = signed_url_data.get("fields", {})
        bucket_name = fields.get("bucket", "liquid-models-export")
        region: str = fields.get("region", "us-east-1")

        try:
            # Extract key prefix from fields
            key_prefix = None
            if "key" in fields:
                key_template = fields["key"]
                # Remove the filename placeholder to get the prefix
                key_prefix = key_template.replace("/${filename}", "").replace(
                    "${filename}", ""
                )
                if key_prefix and not key_prefix.endswith("/") and key_prefix:
                    key_prefix += "/"

            return bucket_name, region, key_prefix

        except Exception as e:
            console.print(
                f"[yellow]⚠[/yellow] Could not extract bucket info from signed URL: {e}"
            )
            return bucket_name, region, None

    def _get_s3_client(self, sts_credentials: StsCredentials) -> Optional[S3Client]:
        """Get or create S3 client for the specified region."""
        try:
            if self._s3_client is None:
                self._s3_client = boto3.client(
                    "s3",
                    region_name=sts_credentials.region,
                    aws_access_key_id=sts_credentials.access_key_id,
                    aws_secret_access_key=sts_credentials.secret_access_key,
                    aws_session_token=sts_credentials.session_token,
                    config=self.config,
                )
            return self._s3_client
        except NoCredentialsError:
            console.print("[yellow]⚠[/yellow] AWS credentials not available")
            return None

    @staticmethod
    def _get_files_to_upload(directory_path: str) -> Tuple[list[Tuple[Path, str]], int]:
        """
        Get list of files to upload and calculate total size.

        Returns:
            Tuple of (list of (file_path, relative_path) pairs, total_size_bytes)
        """
        directory = Path(directory_path)
        if not directory.exists():
            raise UploadError(f"Directory does not exist: {directory_path}")

        if not directory.is_dir():
            raise UploadError(f"Path is not a directory: {directory_path}")

        files_to_upload = []
        total_size = 0

        for root, dirs, files in os.walk(directory):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith(".")]

            for filename in files:
                # Skip hidden files
                if filename.startswith("."):
                    continue

                file_path = Path(root) / filename
                relative_path = str(file_path.relative_to(directory)).replace("\\", "/")

                files_to_upload.append((file_path, relative_path))
                total_size += file_path.stat().st_size

        return files_to_upload, total_size

    @staticmethod
    def _create_progress_callback(
        progress: Progress, task_id: TaskID
    ) -> Callable[[int], None]:
        """Create a progress callback for file uploads."""

        def callback(bytes_transferred: int) -> None:
            progress.update(task_id, advance=bytes_transferred)

        return callback

    def _upload_single_file(
        self,
        file_path: Path,
        s3_key: str,
        s3_client: S3Client,
        bucket_name: str,
        progress: Progress,
        task_id: TaskID,
    ) -> bool:
        """Upload a single file to S3."""
        try:
            file_size = file_path.stat().st_size

            # Only show progress for files larger than 1MB
            if file_size > 1024 * 1024:
                callback = self._create_progress_callback(progress, task_id)
                progress.update(task_id, description=f"Uploading {file_path.name}...")
            else:
                callback = None

            s3_client.upload_file(
                str(file_path),
                bucket_name,
                s3_key,
                Config=self.transfer_config,
                Callback=callback,
                ExtraArgs={"ContentType": "application/octet-stream"},
            )

            # Update progress for small files that don't use callbacks
            if file_size <= 1024 * 1024:
                progress.update(task_id, advance=file_size)

            return True

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            console.print(
                f"[red]✗[/red] Failed to upload {file_path}: {error_code} - {e}"
            )
            return False
        except Exception as e:
            console.print(f"[red]✗[/red] Failed to upload {file_path}: {e}")
            return False

    def upload_directory(
        self, sts_credentials: StsCredentials, directory_path: str
    ) -> None:
        """
        Upload a local directory to S3 using STS credentials or signed URL information.

        Args:
            sts_credentials: Temporarily STS credentials from the server
            directory_path: Path to the local directory to upload

        Raises:
            UploadError: If upload fails
        """
        bucket_name = sts_credentials.bucket_name
        s3_prefix = sts_credentials.s3_prefix.rstrip("/")

        s3_client = self._get_s3_client(sts_credentials)
        if not s3_client:
            raise UploadError(
                "Could not create S3 client. Please check your AWS credentials."
            )

        # Get files to upload
        files_to_upload, total_size = self._get_files_to_upload(directory_path)
        if not files_to_upload:
            console.print("[yellow]⚠[/yellow] No files found to upload")
            return

        console.print(
            f"[blue]ℹ[/blue] Uploading {len(files_to_upload)} files "
            f"({total_size / (1024 * 1024):.1f} MB) to cloud storage..."
        )

        # Upload files with progress tracking
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            "[progress.percentage]{task.percentage:>3.0f}%",
            TransferSpeedColumn(),
            TimeRemainingColumn(),
            console=console,
        ) as progress:
            overall_task = progress.add_task("Overall progress", total=total_size)
            failed_files = []

            # Upload files in parallel
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all upload tasks
                future_to_file = {}
                for file_path, relative_path in files_to_upload:
                    s3_key = f"{s3_prefix}/{relative_path}"

                    future = executor.submit(
                        self._upload_single_file,
                        file_path,
                        s3_key,
                        s3_client,
                        bucket_name,
                        progress,
                        overall_task,
                    )
                    future_to_file[future] = (relative_path, s3_key)

                # Process completed uploads
                for future in as_completed(future_to_file):
                    relative_path, s3_key = future_to_file[future]
                    try:
                        success = future.result()
                        if not success:
                            failed_files.append(relative_path)
                    except Exception as e:
                        console.print(
                            f"[red]✗[/red] Unexpected error uploading {relative_path}: {e}"
                        )
                        failed_files.append(relative_path)

        # Report results
        if failed_files:
            console.print(f"[red]✗[/red] Failed to upload {len(failed_files)} files:")
            for failed_file in failed_files:
                console.print(f"- {failed_file}")
            raise UploadError(f"Upload failed for {len(failed_files)} files")
        else:
            console.print(
                f"[green]✓[/green] Successfully uploaded all {len(files_to_upload)} files"
            )
