# Pre-Development Preparation

[简体中文](PREPARATION.zh-CN.md) | English

Before implementation continues beyond the v0.1 skeleton, settle these items.

## Product Decisions

- Final project name and CLI name.
- v0.1 is macOS-first with graceful path support for Linux/Windows profile fields.
- Python is the initial implementation language.
- YAML profiles are accepted for v0.1 through a restricted built-in parser.
- `age`, `gitleaks`, and `git` are required external dependencies.
- `zstd` is deferred; v0.1 uses standard-library `tar.gz`.

## Security Decisions

- Exact location for local config and state files.
- Exact location for age private keys in v0.1: default is `~/.config/aisync/keys/identity.txt`, override with `AISYNC_AGE_IDENTITY`.
- Missing gitleaks is fatal.
- Users cannot bypass secret scanning in v0.1.
- Symlink behavior: v0.1 stops on symlinks in sync scope.
- Whether restore requires the target app to be closed still needs process detection.

## Codex Profile Research

Confirm the Codex local data layout on macOS:

- `~/.codex/sessions/`
- `~/.codex/session_index.jsonl`
- `~/.codex/history.jsonl`
- `~/.codex/config.toml`
- `~/.codex/skills/`

Confirm denied paths:

- `auth.json`
- `installation_id`
- `chrome-native-hosts-v2.json`
- `*.sqlite`
- `*.sqlite-shm`
- `*.sqlite-wal`
- `plugins/`
- `.tmp/`
- `tmp/`
- `computer-use/`
- `process_manager/`
- `node_repl/`
- `vendor_imports/`
- `visualizations/`
- `ambient-suggestions/`
- `shell_snapshots/`

Do not read or copy real user data unless explicitly requested.

## UX Decisions

Define exact output format for:

- success
- warning
- danger
- dependency missing
- secret found
- restore backup created
- dry-run result
- git conflict

Every error should include a `NEXT` action.

## Test Plan

Required tests before v0.1 release:

- profile validation fails on invalid schema
- denied file stops sync
- fake secret stops sync
- missing age stops sync
- missing recipient stops sync
- missing git remote stops push
- dry-run writes no files
- restore creates backup before writing
- restore stops if backup fails
- symlink escaping source root stops sync
- logs do not include secret values

## Documentation Plan

Required docs before anyone else uses the tool:

- quickstart
- threat model
- recovery guide
- profile authoring guide
- key backup guide
- uninstall guide
