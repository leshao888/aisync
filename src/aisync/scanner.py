from __future__ import annotations

from pathlib import Path

from .deps import require_tool, run
from .errors import DangerError
from .matcher import matches_any
from .profile import Profile


def guard_staging(profile: Profile, staging: Path) -> None:
    if not staging.exists():
        return
    for path in staging.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(staging).as_posix()
        if matches_any(rel, profile.deny):
            raise DangerError(
                f"Denied file found in staging: {rel}",
                why="Denied files are never safe to upload, even inside an encrypted sync package.",
                next_action="Fix the profile include rules and run sync again.",
            )


def scan_secrets(staging: Path) -> None:
    gitleaks = require_tool(
        "gitleaks",
        "Install gitleaks first. macOS: brew install gitleaks",
    )
    result = run([gitleaks, "detect", "--no-git", "--source", str(staging), "--redact", "--verbose"])
    if result.returncode != 0:
        raise DangerError(
            "Secret scanner found a possible secret or failed.",
            why="gitleaks returned a non-zero exit code. Scanner output is hidden to avoid leaking local secrets.",
            next_action="Remove or redact the secret from local app data, then run sync again.",
        )
