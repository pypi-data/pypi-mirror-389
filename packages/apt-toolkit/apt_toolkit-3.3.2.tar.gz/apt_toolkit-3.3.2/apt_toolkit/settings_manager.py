"""
Utility functions for loading and persisting user-specific settings.

The configuration is stored outside the package so that it can be ignored by git
and safely customised per installation. The default filename is
``config/user_settings.json``; if a legacy ``config/secrets.json`` already
exists it will be read for backward compatibility and migrated on the next
save.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

DEFAULT_CONFIG_FILENAME = "user_settings.json"
LEGACY_CONFIG_FILENAME = "secrets.json"

_active_config_path: Path | None = None


def _config_directory() -> Path:
    base = Path(__file__).resolve().parent.parent / "config"
    base.mkdir(parents=True, exist_ok=True)
    return base


def get_settings_path() -> Path:
    """
    Return the path that should be used for reading and writing settings.

    Preference order:
    1. ``config/user_settings.json`` if it already exists.
    2. ``config/secrets.json`` if it exists (legacy support).
    3. New ``config/user_settings.json`` file if none are present.
    """
    global _active_config_path
    if _active_config_path is not None:
        return _active_config_path

    config_dir = _config_directory()
    new_path = config_dir / DEFAULT_CONFIG_FILENAME
    legacy_path = config_dir / LEGACY_CONFIG_FILENAME

    if new_path.exists():
        _active_config_path = new_path
    elif legacy_path.exists():
        # Migrate on next save by pointing active path to the new filename.
        _active_config_path = new_path
        return legacy_path
    else:
        _active_config_path = new_path

    return _active_config_path


def load_settings() -> Dict[str, Any]:
    """Load the persisted settings as a dictionary."""
    path = get_settings_path()
    if not path.exists():
        return {}

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
        return {}
    except (json.JSONDecodeError, OSError):
        return {}


def save_settings(settings: Dict[str, Any]) -> Path:
    """Persist settings to disk and return the path used."""
    config_dir = _config_directory()
    path = config_dir / DEFAULT_CONFIG_FILENAME
    try:
        path.write_text(json.dumps(settings, indent=4), encoding="utf-8")
    except OSError:
        raise

    global _active_config_path
    _active_config_path = path
    return path


def mask_value(value: str, visible: int = 2) -> str:
    """Return a masked representation of a sensitive value."""
    if not value:
        return ""
    if len(value) <= visible:
        return "*" * len(value)
    return f"{value[:visible]}{'*' * max(len(value) - (visible * 2), 0)}{value[-visible:]}"
