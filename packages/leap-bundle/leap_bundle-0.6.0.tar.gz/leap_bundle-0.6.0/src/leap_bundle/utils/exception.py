import json

import requests
import typer
from rich.console import Console


def extract_error_message(response: requests.Response) -> str:
    """Extract error message from HTTP response, preferring server-provided error field."""
    try:
        error_data = response.json()
        return str(error_data.get("error", f"HTTP {response.status_code} error"))
    except ValueError:
        return f"HTTP {response.status_code} error"


def handle_cli_exception(e: Exception, json_mode: bool = False) -> None:
    """Handle CLI exceptions with proper error message extraction and display."""
    console = Console()

    if hasattr(e, "response") and e.response is not None:
        error_message = extract_error_message(e.response)
        if json_mode:
            print(json.dumps({"error": error_message}))
        else:
            console.print(f"[red]✗[/red] {error_message}")
    else:
        if json_mode:
            print(json.dumps({"error": str(e)}))
        else:
            console.print(f"[red]✗[/red] Error: {e}")
    raise typer.Exit(1) from e
