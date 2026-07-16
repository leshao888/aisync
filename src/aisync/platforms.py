from __future__ import annotations

import os
import platform
from pathlib import Path

from .errors import ConfigError


def platform_key() -> str:
    name = platform.system().lower()
    if name == "darwin":
        return "macos"
    if name == "linux":
        return "linux"
    if name == "windows":
        return "windows"
    raise ConfigError(f"Unsupported platform: {platform.system()}", next_action="Use macOS, Linux, or Windows.")


def expand_path(raw: str) -> Path:
    expanded = os.path.expandvars(os.path.expanduser(raw))
    return Path(expanded).resolve()


def default_config_dir() -> Path:
    override = os.environ.get("AISYNC_CONFIG_DIR")
    if override:
        return expand_path(override)
    key = platform_key()
    if key == "windows":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "aisync"
    if key == "linux":
        xdg_config = os.environ.get("XDG_CONFIG_HOME")
        if xdg_config:
            return expand_path(xdg_config) / "aisync"
    return Path.home() / ".config" / "aisync"


def default_repo() -> Path:
    override = os.environ.get("AISYNC_REPO")
    if override:
        return expand_path(override)
    return Path.cwd().resolve()
