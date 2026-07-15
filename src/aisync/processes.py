from __future__ import annotations

import platform
import shutil

from .deps import run


def running_processes(names: list[str]) -> list[str]:
    if not names:
        return []
    if platform.system().lower() not in {"darwin", "linux"}:
        return []
    if not shutil.which("pgrep"):
        return []
    found = []
    for name in names:
        result = run(["pgrep", "-x", name])
        if result.returncode == 0:
            found.append(name)
    return found
