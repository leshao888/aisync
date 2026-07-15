# AIsync Roadmap

[简体中文](ROADMAP.zh-CN.md) | English

## v0.1: Codex Safe Sync MVP

Goal: complete one safe sync and restore loop for Codex on macOS.

Required:

- `aisync init`
- `aisync doctor`
- `aisync profile list`
- `aisync profile show codex`
- `aisync profile validate codex`
- `aisync sync codex --dry-run`
- `aisync sync codex`
- `aisync restore codex --dry-run`
- `aisync restore codex`
- `aisync status`
- privacy-safe logs
- Codex stable profile
- age encryption
- gitleaks scanning
- Git storage
- restore backup
- lock file
- `aisync keygen` for a local age identity and public recipient setup

Non-goals:

- GUI
- automatic background sync
- automatic GitHub repository creation
- automatic conflict merge
- broad app support
- Windows production support

## v0.2: Private Beta

Goal: make the tool safe for other developers to try.

Current alpha progress:

- `aisync key list`
- `aisync recipient list`
- `aisync recipient add`
- `aisync recipient remove`
- `aisync history <profile>`
- `aisync pull`
- `aisync conflicts`
- richer `doctor`
- stricter profile validation
- conflict detection before sync writes a new vault package
- symlink policy
- app-running warnings

Add:

- Linux support
- Claude Code experimental profile
- installation through `pipx`
- tests for dangerous scenarios

## v0.3: Public Preview

Goal: make the project publicly installable and reasonably portable.

Add:

- Windows support
- Cursor experimental profile
- CI matrix for macOS/Linux/Windows
- release checksums
- Homebrew tap or packaged binaries
- profile authoring docs
- better recovery docs
- telemetry-free diagnostics bundle

## v1.0: Stable

Goal: a tool people can trust for repeated personal use.

Required:

- stable profile schema
- documented threat model
- tested restore paths
- signed releases or verifiable checksums
- migration policy
- backward-compatible manifests where practical
- clear deprecation policy for unsafe profile fields
