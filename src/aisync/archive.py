from __future__ import annotations

import tarfile
from pathlib import Path

from .errors import RestoreError


def create_tar_gz(source_dir: Path, archive_path: Path) -> None:
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive_path, "w:gz") as tar:
        for path in sorted(source_dir.rglob("*")):
            if path.is_file():
                tar.add(path, arcname=path.relative_to(source_dir).as_posix())


def safe_extract_tar_gz(archive_path: Path, dest_dir: Path) -> None:
    dest_dir.mkdir(parents=True, exist_ok=True)
    root = dest_dir.resolve()
    with tarfile.open(archive_path, "r:gz") as tar:
        for member in tar.getmembers():
            target = (dest_dir / member.name).resolve()
            try:
                target.relative_to(root)
            except ValueError as exc:
                raise RestoreError(
                    f"Unsafe archive member: {member.name}",
                    next_action="Do not restore this package.",
                ) from exc
        tar.extractall(dest_dir)

