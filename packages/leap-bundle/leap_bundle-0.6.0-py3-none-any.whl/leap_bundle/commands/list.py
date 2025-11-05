"""List command for bundle requests."""

import json
from typing import Any, Optional

import typer
from rich.console import Console
from rich.table import Table

from leap_bundle.commands.create import DEFAULT_QUANTIZATION
from leap_bundle.types.list import (
    BundleRequestResponse,
)
from leap_bundle.utils.api_client import APIClient
from leap_bundle.utils.config import is_logged_in
from leap_bundle.utils.exception import handle_cli_exception

console = Console()


def display_request_details(request: BundleRequestResponse) -> None:
    """Display details for a single bundle request."""
    console.print("[green]✓[/green] Request Details:")
    console.print(f"  ID:           {request.external_id}")
    console.print(f"  Input Path:   {request.input_path}")
    console.print(f"  Status:       {request.status}")
    console.print(f"  Quantization: {request.quantization or DEFAULT_QUANTIZATION}")
    console.print(f"  Creation:     {request.created_at}")
    console.print(f"  Update:       {request.created_at}")
    if request.user_message:
        console.print(f"  Notes:        {request.user_message}")


def generate_request_details(request: BundleRequestResponse) -> dict[str, Any]:
    """Generate a dictionary of details for a single bundle request."""
    return {
        "request_id": request.external_id,
        "input_path": request.input_path,
        "status": request.status,
        "quantization": request.quantization or DEFAULT_QUANTIZATION,
        "created_at": request.created_at,
        "user_message": request.user_message,
    }


def display_requests_table(
    requests: list[BundleRequestResponse], is_last: bool = False
) -> None:
    """Display a table of bundle requests."""
    title = (
        "Most Recent Bundle Request" if is_last else "Bundle Requests (50 most recent)"
    )
    table = Table(title=title)
    table.add_column("ID", style="cyan")
    table.add_column("Input Path", style="green")
    table.add_column("Status", style="yellow")
    table.add_column("Creation", style="blue")
    table.add_column("Notes", style="magenta")

    for request in requests:
        table.add_row(
            str(request.external_id),
            request.input_path,
            request.status,
            request.created_at,
            request.user_message or "",
        )

    console.print(table)
    console.print(
        f"[green]✓[/green] Found {len(requests)} bundle request{'s' if len(requests) != 1 else ''}."
    )


def list_requests(
    request_id: Optional[str] = typer.Argument(
        None, help="Optional request ID to get details for a specific request"
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output result in JSON format for programmatic parsing",
    ),
    last: bool = typer.Option(
        False,
        "--last",
        help="Show only the most recent request",
    ),
) -> None:
    """List bundle requests or get details for a specific request."""

    if not is_logged_in():
        console.print(
            "[red]✗[/red] You must be logged in. Run 'leap-bundle login' first."
        )
        raise typer.Exit(1)

    try:
        client = APIClient()

        if request_id:
            if not json_output:
                console.print(
                    f"[blue]ℹ[/blue] Fetching details for request {request_id}..."
                )

            bundle_request = client.get_bundle_request(request_id)
            if json_output:
                print(json.dumps(generate_request_details(bundle_request)))
            else:
                display_request_details(bundle_request)
        else:
            if not json_output:
                console.print("[blue]ℹ[/blue] Fetching bundle requests...")
            requests = client.list_bundle_requests()
            if not requests:
                if json_output:
                    print(json.dumps({"requests": []}))
                else:
                    console.print("[yellow]⚠[/yellow] No bundle requests found.")
                return

            if last:
                requests = requests[:1]

            if json_output:
                print(
                    json.dumps(
                        {
                            "requests": [
                                {
                                    "request_id": request.external_id,
                                    "input_path": request.input_path,
                                    "status": request.status,
                                    "created_at": request.created_at,
                                    "user_message": request.user_message,
                                }
                                for request in requests
                            ]
                        }
                    )
                )
            else:
                display_requests_table(requests, is_last=last)

    except Exception as e:
        handle_cli_exception(e, json_mode=json_output)
