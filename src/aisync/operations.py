from __future__ import annotations

import json
import shutil
import socket
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from . import __version__
from .archive import create_tar_gz, safe_extract_tar_gz
from .collector import CollectedFile, collect, discover_files
from .crypto import decrypt_file, default_identity_path, encrypt_file, read_recipients, recipients_path
from .deps import check_required, require_tool, run
from .errors import AisyncError, DangerError, RestoreError
from .gitstore import commit_and_push, init_repo, pull, require_git_repository, require_remote
from .lock import RepoLock
from .matcher import matches_any
from .processes import running_processes
from .profile import BUILTIN_PROFILES, Profile, list_profiles, load_profile
from .scanner import guard_staging, scan_secrets
from .state import load_state, update_state
from .ui import UI, write_log


def ensure_repo_layout(repo: Path) -> None:
    repo.mkdir(parents=True, exist_ok=True)
    for name in ["vault", "manifests", "profiles", "logs", "backups", "tmp"]:
        (repo / name).mkdir(parents=True, exist_ok=True)
    gitignore = repo / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text(
            "\n".join(
                [
                    "staging/",
                    "tmp/",
                    "logs/",
                    "backups/",
                    ".aisync.lock",
                    ".aisync-state.json.partial",
                    "keys/",
                    "*.agekey",
                    ".env",
                    "",
                ]
            ),
            encoding="utf-8",
        )
    recipients = recipients_path(repo)
    if not recipients.exists():
        recipients.write_text(
            "# Add age public recipients here, one per line.\n"
            "# Generate one with: aisync keygen --repo <this-repo>\n",
            encoding="utf-8",
        )
    for path in BUILTIN_PROFILES.glob("*.yaml"):
        dst = repo / "profiles" / path.name
        if not dst.exists():
            shutil.copy2(path, dst)


def init(repo: Path, ui: UI, *, git_init: bool = True) -> None:
    ensure_repo_layout(repo)
    if git_init:
        init_repo(repo)
    ui.ok(f"initialized sync repository: {repo}")
    ui.next("Add a private Git remote before real sync, then run: aisync doctor")
    ui.warn("AIsync cannot verify remote privacy offline. Use a private repository.")


def doctor(repo: Path, ui: UI) -> int:
    ui.info(f"repo: {repo}")
    ok = True
    for dep, path in check_required():
        if path:
            ui.ok(f"{dep.name}: {path}")
        else:
            ok = False
            ui.error(f"{dep.name}: missing")
            ui.next(dep.install_hint)
    if recipients_path(repo).exists():
        recipients = [line for line in recipients_path(repo).read_text(encoding="utf-8").splitlines() if line.strip() and not line.strip().startswith("#")]
        if recipients:
            ui.ok(f"age recipients: {len(recipients)} configured")
        else:
            ok = False
            ui.danger("age recipients: none configured")
            ui.next("Run: aisync keygen --repo <repo>")
    else:
        ok = False
        ui.danger("recipients.txt is missing")
        ui.next("Run: aisync init --repo <repo>")
    if (repo / ".git").exists():
        ui.ok("git repository: initialized")
        try:
            require_remote(repo)
            ui.ok("git remote: configured")
            ui.warn("remote privacy cannot be verified offline; confirm it is private on your Git host")
        except AisyncError as exc:
            ok = False
            ui.warn(exc.message)
            if exc.next_action:
                ui.next(exc.next_action)
    else:
        ok = False
        ui.warn("git repository: not initialized")
        ui.next("Run: aisync --repo <repo> init")
    return 0 if ok else 1


def profile_list(ui: UI) -> None:
    for name in list_profiles():
        ui.emit("OK", name)


def profile_show(name: str, ui: UI) -> None:
    profile = load_profile(name)
    ui.info(f"name: {profile.name}")
    ui.info(f"schema_version: {profile.schema_version}")
    ui.info(f"stability: {profile.stability}")
    ui.info(f"source: {profile.source_path()}")
    ui.info(f"include: {len(profile.include)} rules")
    ui.info(f"deny: {len(profile.deny)} rules")
    print(profile.path.read_text(encoding="utf-8"))


def profile_validate(name: str, ui: UI) -> None:
    profile = load_profile(name)
    ui.ok(f"profile valid: {profile.name}")
    ui.info(f"profile file: {profile.path}")
    ui.info(f"profile sha256: {profile.digest}")


def keygen(repo: Path, ui: UI, *, force: bool = False) -> None:
    ensure_repo_layout(repo)
    age_keygen = require_tool("age-keygen", "Install age first. macOS: brew install age")
    identity = default_identity_path()
    if identity.exists() and not force:
        raise DangerError(
            f"age identity already exists: {identity}",
            why="Overwriting this file may make old backups impossible to decrypt.",
            next_action="Use --force only if you have backed up the old identity.",
        )
    identity.parent.mkdir(parents=True, exist_ok=True)
    result = run([age_keygen, "-o", str(identity)])
    if result.returncode != 0:
        raise AisyncError("age-keygen failed.", why=result.stderr.strip(), next_action="Check age installation.")
    public_key = None
    for line in identity.read_text(encoding="utf-8").splitlines():
        if line.lower().startswith("# public key:"):
            public_key = line.split(":", 1)[1].strip()
            break
    if not public_key:
        raise AisyncError("Could not find public key in generated age identity.")
    recipients = recipients_path(repo)
    existing = recipients.read_text(encoding="utf-8") if recipients.exists() else ""
    if public_key not in existing:
        with recipients.open("a", encoding="utf-8") as fh:
            fh.write(public_key + "\n")
    ui.ok(f"created local age identity: {identity}")
    ui.ok("added public recipient to recipients.txt")
    ui.warn("Back up the age identity separately. It is not stored in the sync repository.")


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def _manifest(profile: Profile, archive_name: str, files: list[CollectedFile]) -> dict:
    return {
        "version": 1,
        "tool": "aisync",
        "tool_version": __version__,
        "profile": profile.name,
        "profile_version": profile.schema_version,
        "profile_sha256": profile.digest,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "hostname": socket.gethostname(),
        "archive": f"vault/{archive_name}",
        "encrypted": True,
        "crypto": "age",
        "compression": "tar.gz",
        "files": len(files),
        "bytes": sum(item.size for item in files),
    }


def sync(
    repo: Path,
    profile_name: str,
    ui: UI,
    *,
    dry_run: bool = False,
    source_override: Path | None = None,
    push: bool = True,
) -> None:
    profile = load_profile(profile_name)
    source = source_override or profile.source_path()
    ui.info(f"profile: {profile.name}")
    ui.info(f"source: {source}")
    if not source.exists():
        raise AisyncError(f"source directory does not exist: {source}", next_action="Install/use the app once, or pass --source for testing.")

    files = discover_files(profile, source)
    total = sum(item.size for item in files)
    ui.ok(f"matched allowlist: {len(files)} files, {total} bytes")
    if dry_run:
        ui.info("dry-run: no files copied, scanned, encrypted, committed, or pushed")
        for item in files[:25]:
            ui.info(f"would include: {item.rel}")
        if len(files) > 25:
            ui.info(f"would include: ... {len(files) - 25} more files")
        return

    ensure_repo_layout(repo)
    require_git_repository(repo)
    if push:
        require_remote(repo)
        ui.warn("AIsync cannot verify remote privacy offline; confirm the Git remote is private.")
    running = running_processes(profile.process_names)
    if running:
        ui.warn(f"app appears to be running: {', '.join(running)}")
        ui.warn("sync can continue, but files may still be changing")
    with RepoLock(repo):
        ts = _timestamp()
        temp_root = Path(tempfile.mkdtemp(prefix="aisync-", dir=str(repo / "tmp") if (repo / "tmp").exists() else None))
        staging = temp_root / "staging" / profile.name
        tmp_archive = temp_root / f"{profile.name}-{ts}.tar.gz"
        archive_name = f"{profile.name}-{ts}.tar.gz.age"
        encrypted = repo / "vault" / archive_name
        manifest_path = repo / "manifests" / f"{profile.name}-{ts}.json"
        try:
            copied = collect(profile, source, staging)
            ui.ok(f"copied to staging: {len(copied)} files")
            guard_staging(profile, staging)
            ui.ok("deny guard passed")
            scan_secrets(staging)
            ui.ok("gitleaks scan passed")
            create_tar_gz(staging, tmp_archive)
            recipients = read_recipients(repo)
            encrypt_file(tmp_archive, encrypted, recipients)
            ui.ok(f"encrypted package: {encrypted.relative_to(repo)}")
            manifest = _manifest(profile, archive_name, copied)
            manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            shutil.copy2(profile.path, repo / "profiles" / profile.path.name)
            commit = commit_and_push(repo, f"sync {profile.name} {ts}", push=push)
            if commit:
                ui.ok(f"git commit: {commit}")
                ui.ok("git push completed" if push else "git commit completed without push")
            else:
                ui.warn("nothing changed in git index")
            update_state(
                repo,
                "last_sync",
                profile.name,
                {"status": "ok", "files": len(copied), "bytes": sum(item.size for item in copied), "archive": f"vault/{archive_name}", "commit": commit},
            )
            write_log(repo, {"operation": "sync", "profile": profile.name, "status": "ok", "files": len(copied), "bytes": total})
        finally:
            shutil.rmtree(temp_root, ignore_errors=True)


def _latest_manifest(repo: Path, profile_name: str) -> Path:
    manifests = sorted((repo / "manifests").glob(f"{profile_name}-*.json"))
    if not manifests:
        raise RestoreError(f"No manifest found for profile: {profile_name}", next_action="Run sync first or pull the sync repository.")
    return manifests[-1]


def _list_extracted_files(extracted: Path, profile: Profile) -> list[Path]:
    files = []
    for path in extracted.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(extracted).as_posix()
        if not matches_any(rel, profile.include) or matches_any(rel, profile.deny):
            raise DangerError(
                f"Archive contains a file outside restore policy: {rel}",
                why="Restore only writes files allowed by the active profile.",
                next_action="Do not restore this package until the manifest/profile mismatch is understood.",
            )
        files.append(path)
    return sorted(files)


def _backup_target(target: Path, backup_root: Path, files: list[Path], extracted: Path) -> Path:
    backup_dir = backup_root / f"backup-{_timestamp()}"
    backup_dir.mkdir(parents=True, exist_ok=False)
    any_existing = False
    for src_file in files:
        rel = src_file.relative_to(extracted)
        existing = target / rel
        if existing.exists() and existing.is_file():
            any_existing = True
            dst = backup_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(existing, dst)
    if not any_existing:
        (backup_dir / "EMPTY_TARGET").write_text("No existing allowlisted files were present before restore.\n", encoding="utf-8")
    return backup_dir


def restore(
    repo: Path,
    profile_name: str,
    ui: UI,
    *,
    dry_run: bool = False,
    target_override: Path | None = None,
    pull_remote: bool = True,
    mode: str = "merge",
) -> None:
    ensure_repo_layout(repo)
    profile = load_profile(profile_name)
    target = target_override or profile.source_path()
    if mode not in {"merge", "replace-file"}:
        raise RestoreError("Unsupported restore mode.", next_action="Use --mode merge or --mode replace-file.")

    with RepoLock(repo):
        running = running_processes(profile.process_names)
        if running:
            raise DangerError(
                f"App appears to be running: {', '.join(running)}",
                why="Restoring while the app is open can race with app writes and corrupt local state.",
                next_action="Close the app, then run restore again.",
            )
        if pull_remote:
            pull(repo)
            ui.ok("git pull completed")
        manifest_path = _latest_manifest(repo, profile.name)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        archive = repo / manifest["archive"]
        if not archive.exists():
            raise RestoreError(f"Encrypted archive missing: {archive}", next_action="Run git pull or inspect the manifest.")
        temp_root = Path(tempfile.mkdtemp(prefix="aisync-restore-", dir=str(repo / "tmp") if (repo / "tmp").exists() else None))
        decrypted = temp_root / "package.tar.gz"
        extracted = temp_root / "extracted"
        try:
            decrypt_file(archive, decrypted)
            safe_extract_tar_gz(decrypted, extracted)
            files = _list_extracted_files(extracted, profile)
            ui.ok(f"restore package verified: {len(files)} files")
            ui.info(f"target: {target}")
            ui.info(f"mode: {mode}")
            if dry_run:
                ui.info("dry-run: no backup created and no files restored")
                for path in files[:25]:
                    ui.info(f"would restore: {path.relative_to(extracted).as_posix()}")
                if len(files) > 25:
                    ui.info(f"would restore: ... {len(files) - 25} more files")
                return
            backup = _backup_target(target, repo / "backups" / profile.name, files, extracted)
            ui.ok(f"backup created: {backup}")
            target.mkdir(parents=True, exist_ok=True)
            restored = 0
            skipped = 0
            for src_file in files:
                rel = src_file.relative_to(extracted)
                dst = target / rel
                if dst.exists() and mode == "merge":
                    skipped += 1
                    continue
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_file, dst)
                restored += 1
            ui.ok(f"restored files: {restored}")
            if skipped:
                ui.warn(f"skipped existing files in merge mode: {skipped}")
            update_state(repo, "last_restore", profile.name, {"status": "ok", "restored": restored, "skipped": skipped, "manifest": manifest_path.name})
            write_log(repo, {"operation": "restore", "profile": profile.name, "status": "ok", "restored": restored, "skipped": skipped})
        finally:
            shutil.rmtree(temp_root, ignore_errors=True)


def status(repo: Path, ui: UI) -> None:
    state = load_state(repo)
    print(json.dumps(state, indent=2, sort_keys=True))


def logs(repo: Path, ui: UI, *, last: int = 20) -> None:
    path = repo / "logs" / "aisync.jsonl"
    if not path.exists():
        ui.warn("no logs yet")
        return
    lines = path.read_text(encoding="utf-8").splitlines()[-last:]
    for line in lines:
        print(line)
