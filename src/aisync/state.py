from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def state_path(repo: Path) -> Path:
    return repo / ".aisync-state.json"


def load_state(repo: Path) -> dict[str, Any]:
    path = state_path(repo)
    if not path.exists():
        return {"version": 1, "last_sync": {}, "last_restore": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def save_state(repo: Path, state: dict[str, Any]) -> None:
    path = state_path(repo)
    tmp = path.with_suffix(".json.partial")
    tmp.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def update_state(repo: Path, section: str, profile: str, data: dict[str, Any]) -> None:
    state = load_state(repo)
    state.setdefault(section, {})
    state[section][profile] = {"time": datetime.now(timezone.utc).isoformat(), **data}
    save_state(repo, state)

