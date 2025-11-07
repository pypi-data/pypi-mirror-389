"""Configuration management for pi-ragbox CLI."""

import json
from pathlib import Path
from typing import Optional

from platformdirs import user_config_dir

CONFIG_DIR = Path(user_config_dir("pi-ragbox", "pi"))
CONFIG_FILE = CONFIG_DIR / "config.json"


def ensure_config_dir():
    """Ensure the config directory exists."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def save_credentials(cookies: dict, user_email: str):
    """Save authentication credentials to config file.

    Args:
        cookies: Dictionary of session cookies from NextAuth
        user_email: The user's email address
    """
    ensure_config_dir()

    # Load existing config to preserve options
    existing_config = load_credentials() or {}

    config = {
        "cookies": cookies,
        "user_email": user_email,
    }

    # Preserve existing options if they exist
    if "options" in existing_config:
        config["options"] = existing_config["options"]

    CONFIG_FILE.write_text(json.dumps(config, indent=2))


def load_credentials() -> Optional[dict]:
    """Load authentication credentials from config file.

    Returns:
        Dictionary with token and user_email, or None if not found
    """
    if not CONFIG_FILE.exists():
        return None

    try:
        return json.loads(CONFIG_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def clear_credentials():
    """Remove stored credentials."""
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()


def get_base_url() -> str:
    """Get the base URL for the pi-ragbox application.

    This URL is used for both API calls and browser-based authentication.

    Returns:
        The base URL for the application
    """
    import os

    return os.getenv("PI_RAGBOX_URL", "https://ragbox.withpi.ai")


def save_default_project(project_id: str):
    """Save the default project ID to config file.

    Args:
        project_id: The project ID to set as default
    """
    set_config_option("default_project_id", project_id)


def get_default_project() -> Optional[str]:
    """Get the default project ID from config.

    Returns:
        The default project ID, or None if not set
    """
    return get_config_option("default_project_id")


def set_config_option(key: str, value: str):
    """Set a configuration option in config file.

    Args:
        key: The configuration key to set
        value: The value to set
    """
    ensure_config_dir()

    # Load existing config or create new one
    config = load_credentials() or {}

    # Ensure options dict exists
    if "options" not in config:
        config["options"] = {}

    # Set the option
    config["options"][key] = value

    CONFIG_FILE.write_text(json.dumps(config, indent=2))


def get_config_option(key: str) -> Optional[str]:
    """Get a configuration option from config file.

    Args:
        key: The configuration key to retrieve

    Returns:
        The value of the option, or None if not set
    """
    config = load_credentials()
    if not config or "options" not in config:
        return None

    return config["options"].get(key)
