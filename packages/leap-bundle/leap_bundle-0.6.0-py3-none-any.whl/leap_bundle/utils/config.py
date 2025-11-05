"""Configuration utilities for leap-bundle."""

import os
from pathlib import Path
from typing import Any, Optional

import yaml
from rich.console import Console

DEFAULT_SERVER_URL = "https://leap.liquid.ai"


def get_config_file_path() -> Path:
    """Get the path to the leap-bundle config file."""
    return Path.home() / ".liquid-leap"


def load_config() -> dict[str, Any]:
    """Load configuration from the config file."""
    config_path = get_config_file_path()
    if not config_path.exists():
        return {}

    try:
        with open(config_path) as f:
            return yaml.safe_load(f) or {}
    except (yaml.YAMLError, OSError):
        return {}


def save_config(config: dict[str, Any]) -> None:
    """Save configuration to the config file."""
    config_path = get_config_file_path()

    config_with_version = {"version": 1, **config}

    try:
        with open(config_path, "w") as f:
            yaml.safe_dump(config_with_version, f, default_flow_style=False)

        os.chmod(config_path, 0o600)
    except OSError:
        pass


def is_logged_in() -> bool:
    """Check if the user is currently logged in."""
    config = load_config()
    return bool(config.get("api_token"))


def get_api_token() -> Optional[str]:
    """Get the stored API token."""
    config = load_config()
    return config.get("api_token")


def get_server_url() -> str:
    """Get the configured server URL."""
    config = load_config()
    return str(config.get("server_url", DEFAULT_SERVER_URL))


def set_server_url(url: str) -> None:
    """Store the server URL in the config file."""
    config_path = get_config_file_path()
    config_exists = config_path.exists()

    config = load_config()
    config["server_url"] = url
    save_config(config)

    if not config_exists:
        console = Console()
        console.print(f"[blue]ℹ[/blue] Config file created at: {config_path}")


def set_api_token(token: str) -> None:
    """Store the API token in the config file."""
    config_path = get_config_file_path()
    config_exists = config_path.exists()

    config = load_config()
    config["api_token"] = token
    save_config(config)

    if not config_exists:
        console = Console()
        console.print(f"[blue]ℹ[/blue] Config file created at: {config_path}")


def clear_api_token() -> None:
    """Remove the API token from the config file."""
    config = load_config()
    if "api_token" in config:
        del config["api_token"]
        save_config(config)


def get_headers() -> dict[str, str]:
    """Get stored headers from config."""
    config = load_config()
    headers = config.get("headers", {})
    return dict(headers) if isinstance(headers, dict) else {}


def set_headers(headers: dict[str, str]) -> None:
    """Store headers in the config file."""
    config = load_config()
    config["headers"] = headers
    save_config(config)


def clear_headers() -> None:
    """Remove all headers from the config file."""
    config = load_config()
    if "headers" in config:
        del config["headers"]
        save_config(config)


def parse_header(header_str: str) -> tuple[str, str]:
    """Parse header string in format 'name:value'."""
    if ":" not in header_str:
        raise ValueError(f"Invalid header format: {header_str}. Expected 'name:value'")

    name, value = header_str.split(":", 1)
    name = name.strip()
    value = value.strip()

    if not name or not value:
        raise ValueError(
            f"Invalid header format: {header_str}. Both name and value are required"
        )

    return name, value
