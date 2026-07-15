from __future__ import annotations

import os
from pathlib import Path

from .errors import AisyncError


class RepoLock:
    def __init__(self, repo: Path):
        self.path = repo / ".aisync.lock"
        self.fd: int | None = None

    def __enter__(self):
        try:
            self.fd = os.open(str(self.path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(self.fd, str(os.getpid()).encode("utf-8"))
        except FileExistsError as exc:
            raise AisyncError(
                "Another aisync operation appears to be running.",
                next_action="If the lock is stale, remove .aisync.lock after confirming no aisync process is active.",
            ) from exc
        return self

    def __exit__(self, exc_type, exc, tb):
        if self.fd is not None:
            os.close(self.fd)
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass

