from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from .errors import DangerError
from .matcher import matches_any
from .profile import Profile


@dataclass(frozen=True)
class CollectedFile:
    rel: str
    size: int


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def discover_files(profile: Profile, source: Path) -> list[CollectedFile]:
    if not source.exists():
        return []
    root = source.resolve()
    files: list[CollectedFile] = []
    for path in source.rglob("*"):
        rel = path.relative_to(source).as_posix()
        if path.is_symlink():
            resolved = path.resolve()
            if not _is_relative_to(resolved, root):
                raise DangerError(
                    f"Symlink escapes source root: {rel}",
                    why="A symlink can make a narrow profile copy files outside the intended app directory.",
                    next_action="Remove this symlink or exclude it from the profile.",
                )
            raise DangerError(
                f"Symlink found in sync scope: {rel}",
                why="AIsync v0.1 does not copy symlinks to avoid surprising restore behavior.",
                next_action="Remove this symlink or exclude it from the profile.",
            )
        if not path.is_file():
            continue
        if not matches_any(rel, profile.include):
            continue
        if matches_any(rel, profile.deny):
            raise DangerError(
                f"Denied file matched include rules: {rel}",
                why="Denied files can contain auth sessions, tokens, databases, or private keys.",
                next_action="Tighten the profile include rules before syncing.",
            )
        files.append(CollectedFile(rel=rel, size=path.stat().st_size))
    return sorted(files, key=lambda item: item.rel)


def collect(profile: Profile, source: Path, staging: Path) -> list[CollectedFile]:
    files = discover_files(profile, source)
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True, exist_ok=True)
    for item in files:
        src = source / item.rel
        dst = staging / item.rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    return files

