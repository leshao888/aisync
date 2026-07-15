from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class UI:
    def __init__(self, *, quiet: bool = False):
        self.quiet = quiet

    def emit(self, level: str, message: str) -> None:
        if not self.quiet:
            print(f"{level:<7} {message}")

    def info(self, message: str) -> None:
        self.emit("INFO", message)

    def ok(self, message: str) -> None:
        self.emit("OK", message)

    def warn(self, message: str) -> None:
        self.emit("WARN", message)

    def danger(self, message: str) -> None:
        self.emit("DANGER", message)

    def error(self, message: str) -> None:
        self.emit("ERROR", message)

    def next(self, message: str) -> None:
        self.emit("NEXT", message)


def write_log(repo: Path, event: dict[str, Any]) -> None:
    logs_dir = repo / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    safe_event = dict(event)
    safe_event.setdefault("time", datetime.now(timezone.utc).isoformat())
    with (logs_dir / "aisync.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(safe_event, sort_keys=True) + "\n")


def print_error(ui: UI, exc: Exception) -> None:
    level = getattr(exc, "level", "ERROR")
    message = getattr(exc, "message", str(exc))
    if level == "DANGER":
        ui.danger(message)
    else:
        ui.error(message)
    why = getattr(exc, "why", None)
    if why:
        ui.emit("WHY", why)
    next_action = getattr(exc, "next_action", None)
    if next_action:
        ui.next(next_action)


def fail(message: str, code: int = 1) -> int:
    print(message, file=sys.stderr)
    return code

