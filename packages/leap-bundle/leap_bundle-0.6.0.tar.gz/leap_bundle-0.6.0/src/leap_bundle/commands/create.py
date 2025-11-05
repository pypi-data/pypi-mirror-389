"""Create command for bundle requests."""

import json
from pathlib import Path
from typing import Literal

import typer
from rich.console import Console

from leap_bundle.types.create import BundleRequestExistsResponse
from leap_bundle.utils.api_client import APIClient
from leap_bundle.utils.config import is_logged_in
from leap_bundle.utils.exception import handle_cli_exception
from leap_bundle.utils.hash import calculate_directory_hash
from leap_bundle.utils.s3_upload_manager import S3UploadManager
from leap_bundle.utils.upload import upload_directory_with_signed_url
from leap_bundle.utils.validation import (
    ValidationError,
    get_model_type,
    validate_directory,
)

console = Console()


VALID_QUANTIZATIONS = ["8da4w_output_8da8w", "8da8w_output_8da8w"]
DEFAULT_QUANTIZATION = "8da4w_output_8da8w"


def create(
    input_path: str = typer.Argument(..., help="Directory path to upload"),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Perform a dry run that validates the input model path without uploading or creating a request",
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
    quantization: str = typer.Option(
        DEFAULT_QUANTIZATION,
        "--quantization",
        help="Quantization type: " + ", ".join(VALID_QUANTIZATIONS),
    ),
    # TODO: allow force recreate in the future
    # force_recreate: bool = typer.Option(
    #     False, "--force", help="Force recreate even if request exists"
    # ),
) -> None:
    """Create a new bundle request and upload directory."""

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

    path = Path(input_path)
    if not path.exists():
        if json_output:
            console.print(
                json.dumps({"error": f"Directory does not exist: {input_path}"})
            )
        else:
            console.print(f"[red]✗[/red] Directory does not exist: {input_path}")
        raise typer.Exit(1)

    if not path.is_dir():
        if json_output:
            console.print(
                json.dumps({"error": f"Path is not a directory: {input_path}"})
            )
        else:
            console.print(f"[red]✗[/red] Path is not a directory: {input_path}")
        raise typer.Exit(1)

    if quantization not in VALID_QUANTIZATIONS:
        error_message = " ".join(
            [
                f"Invalid quantization type: {quantization}.",
                f"Valid options: {', '.join(VALID_QUANTIZATIONS)}.",
                f"Default: {DEFAULT_QUANTIZATION}.",
            ]
        )
        if json_output:
            console.print(json.dumps({"error": error_message}))
        else:
            console.print(f"[red]✗[/red] {error_message}")
        raise typer.Exit(1)

    try:
        try:
            validate_directory(path)
            if not json_output:
                console.print("[green]✓[/green] Directory validation passed")
        except ValidationError as e:
            if json_output:
                print(json.dumps({"error": f"Validation failed: {e}"}))
            else:
                console.print(f"[red]✗[/red] Validation failed: {e}")
            raise typer.Exit(1) from e

        if not json_output:
            console.print("[blue]ℹ[/blue] Calculating directory hash...")
        input_hash = calculate_directory_hash(str(path.absolute()))

        if dry_run:
            if json_output:
                console.print(
                    json.dumps(
                        {
                            "status": "dry_run_completed",
                            "message": "Dry run mode completed. No request is created.",
                        }
                    )
                )
            else:
                console.print(
                    "[green]✓[/green] Dry run mode completed. No request is created."
                )
            return

        model_type = get_model_type(path)
        if not json_output:
            console.print(f"[blue]ℹ[/blue] Model type: {model_type}")

        client = APIClient()
        if not json_output:
            console.print("[blue]ℹ[/blue] Submitting bundle request...")

        result = client.create_bundle_request(
            str(path.absolute()), input_hash, quantization, model_type, False
        )

        if isinstance(result, BundleRequestExistsResponse):
            if json_output:
                console.print(json.dumps({"error": result.message, "status": "exists"}))
            else:
                console.print(f"[yellow]⚠[/yellow] {result.message}")
            return

        request_id = result.new_request_id
        if not json_output:
            console.print(
                f"[green]✓[/green] Bundle request created with ID: {request_id}"
            )
            console.print("[blue]ℹ[/blue] Starting upload...")
        client.update_bundle_request_status(request_id, "uploading_started")

        try:
            if upload_mechanism == "sequential":
                if not json_output:
                    console.print("[blue]ℹ[/blue] Using sequential uploading...")
                upload_directory_with_signed_url(
                    result.signed_url, str(path.absolute())
                )
            else:
                if not json_output:
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
                    if not json_output:
                        console.print(
                            "[yellow]⚠[/yellow] Parallel upload failed, falling back to sequential upload"
                        )
                    upload_directory_with_signed_url(
                        result.signed_url, str(path.absolute())
                    )

            client.update_bundle_request_status(request_id, "uploading_completed")
            if json_output:
                print(json.dumps({"request_id": request_id, "status": "success"}))
            else:
                console.print(
                    f"[green]✓[/green] Upload completed successfully! Request ID: {request_id}"
                )

        except ConnectionError as conn_error:
            client.update_bundle_request_status(
                request_id,
                "uploading_failed",
                f"Upload failed due to connection error: {str(conn_error)}",
            )

            console.print(f"[red]✗[/red] {conn_error}")
            console.print("\n[blue]ℹ[/blue] Possible next steps:")
            console.print(
                f'  - For transient issues, try uploading again: "leap-bundle resume {request_id}"'
            )
            console.print(
                f'  - For persistent issues, cancel the request: "leap-bundle cancel {request_id}", and create the request again'
            )
            console.print("  - Contact support: leap@liquid.ai")

            if json_output:
                print(
                    json.dumps(
                        {
                            "error": f"Upload failed due to connection error: {str(conn_error)}"
                        }
                    )
                )
            raise typer.Exit(1) from conn_error
        except Exception as upload_error:
            client.update_bundle_request_status(
                request_id,
                "uploading_failed",
                f"Upload failed: {str(upload_error)}",
            )

            console.print(f"[red]✗[/red] Upload failed: {upload_error}")
            console.print("\n[blue]ℹ[/blue] Possible next steps:")
            console.print(
                f'  - For transient issues, try uploading again: "leap-bundle resume {request_id}"'
            )
            console.print(
                f'  - For persistent issues, cancel the request: "leap-bundle cancel {request_id}", and create the request again'
            )
            console.print("  - Contact support: leap@liquid.ai")
            if json_output:
                print(json.dumps({"error": f"Upload failed: {str(upload_error)}"}))
            raise typer.Exit(1) from upload_error

    except Exception as e:
        handle_cli_exception(e, json_mode=json_output)
