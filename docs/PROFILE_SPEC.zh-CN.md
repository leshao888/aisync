# Profile Spec Draft

简体中文 | [English](PROFILE_SPEC.md)

Profiles 描述一个 app 可以安全 sync 什么。

## Draft Shape

```yaml
schema_version: 1
name: codex
stability: stable

source:
  macos: "~/.codex"
  linux: "~/.codex"
  windows: "%USERPROFILE%\\.codex"

include:
  - sessions/**
  - session_index.jsonl
  - history.jsonl
  - config.toml
  - skills/**

deny:
  - auth.json
  - installation_id
  - chrome-native-hosts-v2.json
  - "*.sqlite"
  - "*.sqlite-shm"
  - "*.sqlite-wal"
  - ".env"
  - "**/*token*"
  - "**/*secret*"
  - "**/*credential*"
  - "**/id_rsa"
  - "**/id_ed25519"

risk:
  sessions/**: scan-required
  history.jsonl: scan-required
  config.toml: warn-and-scan

restore:
  default_mode: merge
  allow_overwrite: false

capabilities:
  supports_restore: true
  supports_merge: true
  requires_app_closed_for_restore: true
```

## Stability Levels

- `stable`: intended for regular use
- `experimental`: available, but layout may change
- `research`: planning only, do not run without explicit confirmation

## Include Rules

Includes 是 allowlist entries。Profile 只应 include 恢复有用 app state 所需的 files。

## Deny Rules

Deny rules 是 fatal。如果 staging 中出现 denied path，sync 停止。

## Restore Rules

初始 restore modes：

- `preview`: show what would happen
- `merge`: add missing files, avoid overwriting existing files where possible
- `replace-file`: replace same-named allowlisted files after backup

MVP 中避免 `replace-tree`。

