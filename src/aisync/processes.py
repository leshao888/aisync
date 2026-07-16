from __future__ import annotations

import platform
import shutil
from pathlib import Path

from .deps import run


def running_processes(names: list[str], *, proc_root: Path = Path("/proc")) -> list[str]:
    if not names:
        return []
    system = platform.system().lower()
    if system not in {"darwin", "linux"}:
        return []
    found = []
    for name in names:
        if shutil.which("pgrep"):
            result = run(["pgrep", "-x", name])
            if result.returncode == 0:
                found.append(name)
                continue
        if system == "linux" and _linux_proc_has_name(name, proc_root):
            found.append(name)
    return found


def _linux_proc_has_name(name: str, proc_root: Path) -> bool:
    if not proc_root.exists():
        return False
    for proc_dir in proc_root.iterdir():
        if not proc_dir.name.isdigit():
            continue
        comm = proc_dir / "comm"
        try:
            if comm.read_text(encoding="utf-8", errors="replace").strip() == name:
                return True
        except OSError:
            pass
        cmdline = proc_dir / "cmdline"
        try:
            args = [part.decode("utf-8", errors="replace") for part in cmdline.read_bytes().split(b"\0") if part]
        except OSError:
            continue
        if args and (args[0] == name or Path(args[0]).name == name):
            return True
    return False
