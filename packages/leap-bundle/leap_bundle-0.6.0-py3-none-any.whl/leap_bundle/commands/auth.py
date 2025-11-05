"""Authentication commands for leap-bundle."""

import requests
import typer
from rich.console import Console

from leap_bundle.utils.api_client import APIClient
from leap_bundle.utils.config import (
    clear_api_token,
    get_api_token,
    is_logged_in,
    set_api_token,
)

console = Console()
app = typer.Typer()


@app.command("login")
def login(
    api_token: str = typer.Argument(..., help="API token for LEAP platform"),
) -> None:
    """Login to LEAP platform."""
    if is_logged_in():
        current_token = get_api_token()

        if current_token == api_token:
            console.print(
                "[yellow]⚠[/yellow] You are already logged in with the same API token."
            )
            return
        else:
            console.print(
                "[yellow]⚠[/yellow] You are already logged in with a different API token."
            )
            if not typer.confirm(
                "Do you want to log out and log in with the new token?"
            ):
                console.print("[blue]ℹ[/blue] Login cancelled.")
                return

            clear_api_token()

    console.print("[blue]ℹ[/blue] Validating API token...")
    client = APIClient()
    if not client.validate_token(api_token):
        console.print(
            "[red]✗[/red] Invalid API token. Please check your token and try again."
        )
        raise typer.Exit(1)

    try:
        set_api_token(api_token)
        console.print("[green]✓[/green] Successfully logged in to LEAP platform!")
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to save login credentials: {e}")
        raise typer.Exit(1) from None


@app.command("logout")
def logout() -> None:
    """Logout from LEAP platform."""
    if not is_logged_in():
        console.print("[blue]ℹ[/blue] You are not currently logged in.")
        return

    try:
        clear_api_token()
        console.print("[green]✓[/green] Successfully logged out from LEAP platform!")
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to clear login credentials: {e}")
        raise typer.Exit(1) from None


@app.command("whoami")
def whoami() -> None:
    """Show current user information."""
    if not is_logged_in():
        console.print(
            "[red]✗[/red] You are not logged in. Run 'leap-bundle login' first."
        )
        raise typer.Exit(1)

    try:
        client = APIClient()
        data = client.whoami()
        console.print(f"[green]✓[/green] Logged in as: {data['email']}")
    except requests.HTTPError as e:
        console.print(f"[red]✗[/red] {e}")
        raise typer.Exit(1) from None
    except requests.RequestException as e:
        console.print(f"[red]✗[/red] Failed to connect to server: {e}")
        raise typer.Exit(1) from None
    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[red]✗[/red] Unexpected error: {e}")
        raise typer.Exit(1) from None
