"""Resume command for bundle requests."""

import json
from pathlib import Path
from typing import Literal, Optional

import typer
from rich.console import Console

from leap_bundle.types.list import BundleRequestResponse
from leap_bundle.utils.api_client import APIClient
from leap_bundle.utils.config import is_logged_in
from leap_bundle.utils.exception import handle_cli_exception
from leap_bundle.utils.s3_upload_manager import S3UploadManager
from leap_bundle.utils.upload import upload_directory_with_signed_url

console = Console()


# User-friendly statuses from EXTERNAL_STATUS_MAP
# in apps/web/src/lib/bundle-requests/constants.ts
RESUMABLE_STATUSES = ["Uploading", "Uploading Failed"]


def resume(
    request_id: Optional[str] = typer.Argument(
        None,
        help="Optional request ID to resume. If not provided, resumes the latest request.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output result in JSON format for programmatic parsing",
    ),
    sequential: bool = typer.Option(
        False,
        "--sequential",
        help="Upload files sequentially (this is the fallback option if parallel upload fails)",
    ),
    parallel: bool = typer.Option(
        False,
        "--parallel",
        help="Upload files parallelly (this is the default behavior if neither --sequential nor --parallel is specified)",
    ),
) -> None:
    """Resume uploading for a failed or interrupted bundle request."""

    if not is_logged_in():
        if json_output:
            console.print(
                json.dumps(
                    {"error": "You must be logged in. Run 'leap-bundle login' first."}
                )
            )
        else:
            console.print(
                "[red]✗[/red] You must be logged in. Run 'leap-bundle login' first."
            )
        raise typer.Exit(1)

    upload_mechanism: Literal["sequential", "parallel"] = "parallel"
    if sequential and parallel:
        warning_msg = "Both --sequential and --parallel flags are provided. Will default to parallel upload and fall back to sequential if anything fails."
        if json_output:
            console.print(json.dumps({"warning": warning_msg}))
        else:
            console.print(f"[yellow]⚠[/yellow] {warning_msg}")
    elif sequential:
        upload_mechanism = "sequential"

    try:
        client = APIClient()
        request: BundleRequestResponse

        if request_id:
            console.print(f"[blue]ℹ[/blue] Retrieving bundle request {request_id}...")
            request = client.get_bundle_request(request_id)
        else:
            console.print("[blue]ℹ[/blue] Retrieving latest bundle request...")
            requests = client.list_bundle_requests()
            if not requests:
                error_msg = "No bundle requests found"
                if json_output:
                    console.print(json.dumps({"error": error_msg}))
                else:
                    console.print(f"[red]✗[/red] {error_msg}")
                raise typer.Exit(1)

            request = requests[0]  # Latest request

        if request.status not in RESUMABLE_STATUSES:
            error_msg = f"Resume only works for model uploading. Current status: {request.status}"
            if json_output:
                console.print(json.dumps({"error": error_msg}))
            else:
                console.print(f"[red]✗[/red] {error_msg}")
            raise typer.Exit(1)

        input_path: str = request.input_path
        resume_request_id: int = request.external_id
        path = Path(input_path)
        if not path.exists() or not path.is_dir():
            error_msg = f"Original input directory no longer exists: {input_path}"
            if json_output:
                console.print(json.dumps({"error": error_msg}))
            else:
                console.print(f"[red]✗[/red] {error_msg}")
            raise typer.Exit(1)

        console.print(
            f"[green]✓[/green] Resuming upload for request {resume_request_id}..."
        )
        console.print(f"[blue]ℹ[/blue] Input path: {input_path}")
        result = client.resume_bundle_request(resume_request_id)
        client.update_bundle_request_status(resume_request_id, "uploading_started")

        try:
            if upload_mechanism == "sequential":
                console.print("[blue]ℹ[/blue] Using sequential uploading...")
                upload_directory_with_signed_url(
                    result.signed_url, str(path.absolute())
                )
            else:
                console.print(
                    "[blue]ℹ[/blue] Using parallel upload with multipart support..."
                )
                # noinspection PyBroadException
                try:
                    manager = S3UploadManager()
                    manager.upload_directory(
                        result.sts_credentials, str(path.absolute())
                    )
                except Exception:
                    console.print(
                        "[yellow]⚠[/yellow] Parallel upload failed, falling back to sequential upload"
                    )
                    upload_directory_with_signed_url(
                        result.signed_url, str(path.absolute())
                    )

            client.update_bundle_request_status(
                resume_request_id, "uploading_completed"
            )
            console.print(
                f"[green]✓[/green] Upload completed successfully! Request ID: {resume_request_id}"
            )
            if json_output:
                print(
                    json.dumps({"request_id": resume_request_id, "status": "success"})
                )

        except ConnectionError as conn_error:
            client.update_bundle_request_status(
                resume_request_id,
                "uploading_failed",
                f"Upload failed due to connection error: {str(conn_error)}",
            )
            if json_output:
                print(
                    json.dumps(
                        {
                            "error": f"Upload failed due to connection error: {str(conn_error)}"
                        }
                    )
                )
            else:
                console.print(f"[red]✗[/red] {conn_error}")
            raise typer.Exit(1) from conn_error
        except Exception as upload_error:
            client.update_bundle_request_status(
                resume_request_id,
                "uploading_failed",
                f"Upload failed: {str(upload_error)}",
            )
            if json_output:
                print(json.dumps({"error": f"Upload failed: {str(upload_error)}"}))
            else:
                console.print(f"[red]✗[/red] Upload failed: {upload_error}")
            raise typer.Exit(1) from upload_error

    except Exception as e:
        handle_cli_exception(e, json_mode=json_output)
