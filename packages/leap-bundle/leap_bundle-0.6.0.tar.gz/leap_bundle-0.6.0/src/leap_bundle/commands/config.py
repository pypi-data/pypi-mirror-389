"""Configuration commands for leap-bundle."""

from typing import List, Optional

import typer
from rich.console import Console

from leap_bundle.utils.config import (
    DEFAULT_SERVER_URL,
    clear_headers,
    get_config_file_path,
    get_headers,
    load_config,
    parse_header,
    set_headers,
    set_server_url,
)

console = Console()
app = typer.Typer()


@app.command("config")
def config(
    server: str = typer.Option(
        None, "--server", help="[Internal only] Set the server URL", hidden=True
    ),
    header: Optional[List[str]] = typer.Option(
        None,
        "--header",
        help="[Internal only] Add request header in format 'name:value'",
        hidden=True,
    ),
    reset: bool = typer.Option(
        False,
        "--reset",
        help=f"Reset server URL to default ({DEFAULT_SERVER_URL}) and clear all headers",
        hidden=True,
    ),
) -> None:
    """Configure leap-bundle settings."""
    if reset:
        set_server_url(DEFAULT_SERVER_URL)
        clear_headers()
        console.print(
            f"[green]✓[/green] Reset server URL to {DEFAULT_SERVER_URL} and cleared all headers"
        )
        return

    if server:
        set_server_url(server)
        console.print(f"[green]✓[/green] Server URL set to: {server}")
    if header:
        try:
            current_headers = get_headers()
            for header_str in header:
                name, value = parse_header(header_str)
                current_headers[name] = value
            set_headers(current_headers)
            console.print(f"[green]✓[/green] Added {len(header)} header(s)")
            for header_str in header:
                name, value = parse_header(header_str)
                console.print(f"  {name}: {value}")
        except ValueError as e:
            console.print(f"[red]✗[/red] {e}")
            raise typer.Exit(1) from e
    if not (server or header):
        config_path = get_config_file_path()
        console.print(f"[blue]ℹ[/blue] Config file location: {config_path}")

        config_data = load_config()
        if config_data:
            console.print("\n[blue]Current configuration:[/blue]")
            for key, value in config_data.items():
                if key == "api_token":
                    continue
                elif key == "headers":
                    console.print(f"  {key}:")
                    for header_name, header_value in value.items():
                        console.print(f"    {header_name}: {header_value}")
                else:
                    console.print(f"  {key}: {value}")
        else:
            console.print("\n[yellow]No configuration found.[/yellow]")
