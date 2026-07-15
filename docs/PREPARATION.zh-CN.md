# Pre-Development Preparation

简体中文 | [English](PREPARATION.md)

在 implementation 继续超过 v0.1 skeleton 前，需要确认以下事项。

## Product Decisions

- 最终 project name 和 CLI name。
- v0.1 是 macOS-first，并为 Linux/Windows profile fields 提供 graceful path support。
- Python 是初始 implementation language。
- v0.1 接受 YAML profiles，并使用 restricted built-in parser。
- `age`、`gitleaks` 和 `git` 是 required external dependencies。
- `zstd` 暂缓；v0.1 使用 standard-library `tar.gz`。

## Security Decisions

- local config 和 state files 的确切位置。
- v0.1 age private keys 默认位置：`~/.config/aisync/keys/identity.txt`，可用 `AISYNC_AGE_IDENTITY` 覆盖。
- Missing gitleaks 是 fatal。
- v0.1 不允许 users bypass secret scanning。
- Symlink behavior：v0.1 在 sync scope 中发现 symlink 时停止。
- Restore 是否要求 target app 关闭仍需要 process detection。

## Codex Profile Research

确认 macOS 上 Codex local data layout：

- `~/.codex/sessions/`
- `~/.codex/session_index.jsonl`
- `~/.codex/history.jsonl`
- `~/.codex/config.toml`
- `~/.codex/skills/`

确认 denied paths：

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

除非用户明确要求，不要读取或复制真实 user data。

## UX Decisions

为以下情况定义精确 output format：

- success
- warning
- danger
- dependency missing
- secret found
- restore backup created
- dry-run result
- git conflict

每个 error 都应包含 `NEXT` action。

## Test Plan

v0.1 release 前需要的 tests：

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

其他人使用前需要的 docs：

- quickstart
- threat model
- recovery guide
- profile authoring guide
- key backup guide
- uninstall guide

