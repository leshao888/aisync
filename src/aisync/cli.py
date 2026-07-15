from __future__ import annotations

import argparse
from pathlib import Path

from . import __version__
from .errors import AisyncError
from .operations import (
    doctor,
    history,
    init,
    key_list,
    keygen,
    logs,
    profile_list,
    profile_show,
    profile_validate,
    recipient_add,
    recipient_list,
    recipient_remove,
    restore,
    status,
    sync,
)
from .platforms import default_repo, expand_path
from .ui import UI, print_error


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aisync", description="Privacy-first sync for local AI app data")
    parser.add_argument("--version", action="version", version=f"aisync {__version__}")
    parser.add_argument("--repo", type=str, default=None, help="Path to the encrypted sync repository")
    parser.add_argument("--quiet", action="store_true", help="Reduce progress output")

    sub = parser.add_subparsers(dest="command", required=True)

    init_cmd = sub.add_parser("init", help="Initialize a sync repository")
    init_cmd.add_argument("--no-git", action="store_true", help="Create folders without running git init")

    sub.add_parser("doctor", help="Check dependencies and repository readiness")

    keygen_cmd = sub.add_parser("keygen", help="Generate a local age key and add its public recipient")
    keygen_cmd.add_argument("--force", action="store_true", help="Overwrite the local age identity")

    key_cmd = sub.add_parser("key", help="Manage local age keys")
    key_sub = key_cmd.add_subparsers(dest="key_command", required=True)
    key_sub.add_parser("list", help="Show local age identity status")

    recipient_cmd = sub.add_parser("recipient", help="Manage vault age recipients")
    recipient_sub = recipient_cmd.add_subparsers(dest="recipient_command", required=True)
    recipient_sub.add_parser("list", help="List configured age recipients")
    recipient_add_cmd = recipient_sub.add_parser("add", help="Add an age recipient")
    recipient_add_cmd.add_argument("recipient")
    recipient_remove_cmd = recipient_sub.add_parser("remove", help="Remove an age recipient")
    recipient_remove_cmd.add_argument("recipient")

    profile_cmd = sub.add_parser("profile", help="Manage app profiles")
    profile_sub = profile_cmd.add_subparsers(dest="profile_command", required=True)
    profile_sub.add_parser("list", help="List bundled profiles")
    show_cmd = profile_sub.add_parser("show", help="Show a profile")
    show_cmd.add_argument("name")
    validate_cmd = profile_sub.add_parser("validate", help="Validate a profile")
    validate_cmd.add_argument("name")

    sync_cmd = sub.add_parser("sync", help="Sync an app profile")
    sync_cmd.add_argument("profile")
    sync_cmd.add_argument("--dry-run", action="store_true")
    sync_cmd.add_argument("--source", type=str, help="Override source directory, mostly for tests")
    sync_cmd.add_argument("--no-push", action="store_true", help="Commit locally without git push")

    restore_cmd = sub.add_parser("restore", help="Restore an app profile")
    restore_cmd.add_argument("profile")
    restore_cmd.add_argument("--dry-run", action="store_true")
    restore_cmd.add_argument("--target", type=str, help="Override restore target, mostly for tests")
    restore_cmd.add_argument("--no-pull", action="store_true", help="Do not run git pull before restore")
    restore_cmd.add_argument("--mode", choices=["merge", "replace-file"], default="merge")

    sub.add_parser("status", help="Show local state")
    logs_cmd = sub.add_parser("logs", help="Show privacy-safe logs")
    logs_cmd.add_argument("--last", type=int, default=20)

    history_cmd = sub.add_parser("history", help="Show sync manifest history")
    history_cmd.add_argument("profile", nargs="?", help="Optional profile name, for example codex")
    history_cmd.add_argument("--limit", type=int, default=10)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    ui = UI(quiet=args.quiet)
    repo = expand_path(args.repo) if args.repo else default_repo()

    try:
        if args.command == "init":
            init(repo, ui, git_init=not args.no_git)
        elif args.command == "doctor":
            return doctor(repo, ui)
        elif args.command == "keygen":
            keygen(repo, ui, force=args.force)
        elif args.command == "key":
            if args.key_command == "list":
                key_list(ui)
        elif args.command == "recipient":
            if args.recipient_command == "list":
                recipient_list(repo, ui)
            elif args.recipient_command == "add":
                recipient_add(repo, ui, args.recipient)
            elif args.recipient_command == "remove":
                recipient_remove(repo, ui, args.recipient)
        elif args.command == "profile":
            if args.profile_command == "list":
                profile_list(ui)
            elif args.profile_command == "show":
                profile_show(args.name, ui)
            elif args.profile_command == "validate":
                profile_validate(args.name, ui)
        elif args.command == "sync":
            source = Path(args.source).expanduser().resolve() if args.source else None
            sync(repo, args.profile, ui, dry_run=args.dry_run, source_override=source, push=not args.no_push)
        elif args.command == "restore":
            target = Path(args.target).expanduser().resolve() if args.target else None
            restore(repo, args.profile, ui, dry_run=args.dry_run, target_override=target, pull_remote=not args.no_pull, mode=args.mode)
        elif args.command == "status":
            status(repo, ui)
        elif args.command == "logs":
            logs(repo, ui, last=args.last)
        elif args.command == "history":
            history(repo, args.profile, ui, limit=args.limit)
        return 0
    except AisyncError as exc:
        print_error(ui, exc)
        return 2 if getattr(exc, "level", "") == "DANGER" else 1
