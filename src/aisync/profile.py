from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .errors import ProfileError
from .matcher import normalize_rel
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
    source = {str(k): str(v) for k, v in raw["source"].items()}
    _validate_source(source, path)
    if not isinstance(raw["include"], list) or not raw["include"]:
        raise ProfileError(f"Profile {path} include must be a non-empty list.")
    if not isinstance(raw["deny"], list):
        raise ProfileError(f"Profile {path} deny must be a list.")
    include = [str(v) for v in raw["include"]]
    deny = [str(v) for v in raw["deny"]]
    _validate_patterns("include", include, path)
    _validate_patterns("deny", deny, path)
    stability = str(raw.get("stability", "experimental"))
    if stability not in {"stable", "experimental", "research"}:
        raise ProfileError(
            f"Profile {path} has invalid stability: {stability}",
            next_action="Use stable, experimental, or research.",
        )
    restore = _optional_map(raw, "restore", path)
    default_mode = restore.get("default_mode")
    if default_mode is not None and default_mode not in {"merge", "replace-file", "preview"}:
        raise ProfileError(
            f"Profile {path} has invalid restore.default_mode: {default_mode}",
            next_action="Use merge, replace-file, or preview.",
        )
    allow_overwrite = restore.get("allow_overwrite")
    if allow_overwrite is not None and not isinstance(allow_overwrite, bool):
        raise ProfileError(f"Profile {path} restore.allow_overwrite must be true or false.")
    process_names = raw.get("process_names") or []
    if not isinstance(process_names, list):
        raise ProfileError(f"Profile {path} process_names must be a list.")
    name = str(raw["name"])
    if name != path.stem and not path.stem.endswith(".experimental"):
        raise ProfileError(f"Profile filename and name differ: {path.stem} != {name}")
    return Profile(
        name=name,
        schema_version=int(raw["schema_version"]),
        stability=stability,
        source=source,
        include=include,
        deny=deny,
        risk={str(k): str(v) for k, v in _optional_map(raw, "risk", path).items()},
        restore=restore,
        capabilities=_optional_map(raw, "capabilities", path),
        process_names=[str(v) for v in process_names],
        path=path,
        raw=raw,
    )


def _optional_map(raw: dict[str, Any], key: str, path: Path) -> dict[str, Any]:
    value = raw.get(key) or {}
    if not isinstance(value, dict):
        raise ProfileError(f"Profile {path} {key} must be a map.")
    return dict(value)


def _validate_source(source: dict[str, str], path: Path) -> None:
    if not source:
        raise ProfileError(f"Profile {path} source must not be empty.")
    supported = {"macos", "linux", "windows"}
    unknown = sorted(set(source) - supported)
    if unknown:
        raise ProfileError(
            f"Profile {path} has unsupported source platforms: {', '.join(unknown)}",
            next_action="Use macos, linux, or windows.",
        )
    for key, value in source.items():
        if not value.strip():
            raise ProfileError(f"Profile {path} source.{key} must not be empty.")


def _validate_patterns(kind: str, patterns: list[str], path: Path) -> None:
    for pattern in patterns:
        normalized = normalize_rel(pattern)
        if not normalized:
            raise ProfileError(f"Profile {path} {kind} contains an empty pattern.")
        if pattern.startswith(("/", "\\")):
            raise ProfileError(
                f"Profile {path} {kind} pattern must be relative: {pattern}",
                next_action="Use paths relative to the app source directory.",
            )
        parts = normalized.split("/")
        if ".." in parts:
            raise ProfileError(
                f"Profile {path} {kind} pattern must not escape the source root: {pattern}",
                next_action="Remove '..' from profile patterns.",
            )
