from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import ProfileError


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if not value:
        return ""
    if value in {"true", "True"}:
        return True
    if value in {"false", "False"}:
        return False
    if value in {"null", "None"}:
        return None
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    try:
        return int(value)
    except ValueError:
        return value


def load_simple_yaml(path: Path) -> dict[str, Any]:
    """Parse the small YAML subset used by bundled profiles.

    Supported:
    - top-level scalar keys
    - top-level lists
    - top-level maps with scalar values
    - comments and blank lines
    """
    root: dict[str, Any] = {}
    current_key: str | None = None
    current_kind: str | None = None

    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        if indent == 0:
            if ":" not in stripped:
                raise ProfileError(f"Invalid YAML at {path}:{lineno}", next_action="Fix the profile syntax.")
            key, value = stripped.split(":", 1)
            key = key.strip()
            value = value.strip()
            if value:
                root[key] = _parse_scalar(value)
                current_key = None
                current_kind = None
            else:
                root[key] = None
                current_key = key
                current_kind = None
            continue

        if current_key is None:
            raise ProfileError(f"Unexpected indentation at {path}:{lineno}", next_action="Fix the profile syntax.")

        if stripped.startswith("- "):
            if current_kind is None:
                root[current_key] = []
                current_kind = "list"
            if current_kind != "list":
                raise ProfileError(f"Mixed YAML types at {path}:{lineno}", next_action="Use either a list or map.")
            root[current_key].append(_parse_scalar(stripped[2:]))
            continue

        if ":" in stripped:
            if current_kind is None:
                root[current_key] = {}
                current_kind = "map"
            if current_kind != "map":
                raise ProfileError(f"Mixed YAML types at {path}:{lineno}", next_action="Use either a list or map.")
            key, value = stripped.split(":", 1)
            root[current_key][key.strip()] = _parse_scalar(value.strip())
            continue

        raise ProfileError(f"Unsupported YAML at {path}:{lineno}", next_action="Use simple scalar, list, or map values.")

    return root

