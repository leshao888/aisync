# Profile Spec Draft

[简体中文](PROFILE_SPEC.zh-CN.md) | English

Profiles describe what one app can safely sync.

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
- `research`: planning only; sync is blocked

## Include Rules

Includes are allowlist entries. A profile should include only files required to restore useful app state.

## Deny Rules

Deny rules are fatal. If a denied path appears in staging, sync stops.

## Restore Rules

`capabilities.supports_restore` is a runtime safety gate, not descriptive metadata. Missing capability values default to the safer `false` behavior. When restore is disabled, AIsync must stop before creating repository directories, pulling Git data, decrypting an archive, creating a backup, or writing the app directory.

Capability values must be booleans. A profile cannot declare `supports_merge: true` while restore is disabled. Experimental profiles may support sync while keeping restore disabled until their app layout and restore behavior have dedicated safety tests.

Initial restore modes:

- `preview`: show what would happen
- `merge`: add missing files, avoid overwriting existing files where possible
- `replace-file`: replace same-named allowlisted files after backup

Avoid `replace-tree` in the MVP.
