from __future__ import annotations

import os
from pathlib import Path

from .deps import require_tool, run
from .errors import CryptoError, DangerError
from .platforms import default_config_dir, expand_path


def recipients_path(repo: Path) -> Path:
    return repo / "recipients.txt"


def parse_recipients(path: Path) -> list[str]:
    if not path.exists():
        return []
    recipients = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            recipients.append(line)
    return recipients


def write_recipients(repo: Path, recipients: list[str]) -> None:
    path = recipients_path(repo)
    path.parent.mkdir(parents=True, exist_ok=True)
    body = [
        "# Add age public recipients here, one per line.",
        "# Native age recipients start with age1.",
        "# SSH public key recipients may start with ssh-ed25519 or ssh-rsa.",
        "",
    ]
    body.extend(dict.fromkeys(recipients))
    path.write_text("\n".join(body).rstrip() + "\n", encoding="utf-8")


def validate_recipient(recipient: str) -> str:
    recipient = recipient.strip()
    if not recipient:
        raise DangerError(
            "Empty age recipient.",
            why="An empty recipient would make encryption configuration ambiguous.",
            next_action="Use a valid age recipient, for example one starting with age1.",
        )
    if recipient.startswith(("age1", "ssh-ed25519 ", "ssh-rsa ")):
        return recipient
    raise DangerError(
        "Unsupported age recipient format.",
        why="AIsync v0.2 accepts native age recipients and SSH public key recipients.",
        next_action="Use an age recipient starting with age1, or an SSH public key starting with ssh-ed25519 or ssh-rsa.",
    )


def read_recipients(repo: Path) -> list[str]:
    path = recipients_path(repo)
    if not path.exists():
        raise DangerError(
            "No age recipients configured.",
            why="AIsync will not create a remote package that nobody can decrypt.",
            next_action="Add a public age recipient to recipients.txt or run aisync keygen.",
        )
    recipients = parse_recipients(path)
    if not recipients:
        raise DangerError(
            "recipients.txt is empty.",
            why="At least one public age recipient is required before syncing.",
            next_action="Add a public age recipient or run aisync keygen.",
        )
    return recipients


def default_identity_path() -> Path:
    override = os.environ.get("AISYNC_AGE_IDENTITY")
    if override:
        return expand_path(override)
    return default_config_dir() / "keys" / "identity.txt"


def encrypt_file(input_path: Path, output_path: Path, recipients: list[str]) -> None:
    age = require_tool("age", "Install age first. macOS: brew install age")
    partial = output_path.with_suffix(output_path.suffix + ".partial")
    partial.parent.mkdir(parents=True, exist_ok=True)
    cmd = [age]
    for recipient in recipients:
        cmd.extend(["-r", recipient])
    cmd.extend(["-o", str(partial), str(input_path)])
    result = run(cmd)
    if result.returncode != 0:
        if partial.exists():
            partial.unlink()
        raise CryptoError(
            "age encryption failed.",
            why=result.stderr.strip()[:1200] or result.stdout.strip()[:1200],
            next_action="Check recipients.txt and confirm every recipient is a valid age public key.",
        )
    partial.replace(output_path)


def decrypt_file(input_path: Path, output_path: Path, identity: Path | None = None) -> None:
    age = require_tool("age", "Install age first. macOS: brew install age")
    identity = identity or default_identity_path()
    if not identity.exists():
        raise CryptoError(
            f"age identity file not found: {identity}",
            next_action="Set AISYNC_AGE_IDENTITY or run aisync keygen on this machine.",
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result = run([age, "-d", "-i", str(identity), "-o", str(output_path), str(input_path)])
    if result.returncode != 0:
        raise CryptoError(
            "age decryption failed.",
            why=result.stderr.strip()[:1200] or result.stdout.strip()[:1200],
            next_action="Check that this machine has the matching age private key.",
        )
