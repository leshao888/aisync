from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .errors import ProfileError
from .platforms import expand_path, platform_key
from .simple_yaml import load_simple_yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BUILTIN_PROFILES = PROJECT_ROOT / "profiles"


@dataclass(frozen=True)
class Profile:
    name: str
    schema_version: int
    stability: str
    source: dict[str, str]
    include: list[str]
    deny: list[str]
    risk: dict[str, str]
    restore: dict[str, Any]
    capabilities: dict[str, Any]
    process_names: list[str]
    path: Path
    raw: dict[str, Any]

    @property
    def digest(self) -> str:
        data = self.path.read_bytes()
        return hashlib.sha256(data).hexdigest()

    def source_path(self) -> Path:
        key = platform_key()
        raw = self.source.get(key)
        if not raw:
            raise ProfileError(
                f"Profile {self.name} does not support {key}.",
                next_action="Add a source path for this platform or use another profile.",
            )
        return expand_path(raw)


def profile_dirs(extra: Path | None = None) -> list[Path]:
    dirs = []
    if extra:
        dirs.append(extra)
    dirs.append(BUILTIN_PROFILES)
    return dirs


def list_profiles(extra: Path | None = None) -> list[str]:
    names: set[str] = set()
    for directory in profile_dirs(extra):
        if directory.exists():
            for path in directory.glob("*.yaml"):
                names.add(path.stem)
    return sorted(names)


def find_profile(name: str, extra: Path | None = None) -> Path:
    candidates = []
    for directory in profile_dirs(extra):
        candidates.append(directory / f"{name}.yaml")
    for path in candidates:
        if path.exists():
            return path
    raise ProfileError(f"Profile not found: {name}", next_action="Run: aisync profile list")


def load_profile(name: str, extra: Path | None = None) -> Profile:
    path = find_profile(name, extra)
    raw = load_simple_yaml(path)
    return validate_profile(raw, path)


def validate_profile(raw: dict[str, Any], path: Path) -> Profile:
    required = ["schema_version", "name", "source", "include", "deny"]
    missing = [key for key in required if key not in raw]
    if missing:
        raise ProfileError(f"Profile {path} is missing: {', '.join(missing)}", next_action="Fix the profile.")
    if raw["schema_version"] != 1:
        raise ProfileError(
            f"Unsupported profile schema version: {raw['schema_version']}",
            next_action="Use schema_version: 1 for aisync v0.1.",
        )
    if not isinstance(raw["source"], dict):
        raise ProfileError(f"Profile {path} source must be a map.")
    if not isinstance(raw["include"], list) or not raw["include"]:
        raise ProfileError(f"Profile {path} include must be a non-empty list.")
    if not isinstance(raw["deny"], list):
        raise ProfileError(f"Profile {path} deny must be a list.")
    name = str(raw["name"])
    if name != path.stem and not path.stem.endswith(".experimental"):
        raise ProfileError(f"Profile filename and name differ: {path.stem} != {name}")
    return Profile(
        name=name,
        schema_version=int(raw["schema_version"]),
        stability=str(raw.get("stability", "experimental")),
        source={str(k): str(v) for k, v in raw["source"].items()},
        include=[str(v) for v in raw["include"]],
        deny=[str(v) for v in raw["deny"]],
        risk={str(k): str(v) for k, v in (raw.get("risk") or {}).items()},
        restore=dict(raw.get("restore") or {}),
        capabilities=dict(raw.get("capabilities") or {}),
        process_names=[str(v) for v in (raw.get("process_names") or [])],
        path=path,
        raw=raw,
    )
