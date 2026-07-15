# AIsync Roadmap

简体中文 | [English](ROADMAP.md)

## v0.1: Codex Safe Sync MVP

目标：为 macOS 上的 Codex 完成一个安全 sync 和 restore 闭环。

必需：

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
- `aisync keygen` 用于 local age identity 和 public recipient setup

非目标：

- GUI
- automatic background sync
- automatic GitHub repository creation
- automatic conflict merge
- broad app support
- Windows production support

## v0.2: Private Beta

目标：让其他 developer 可以更安全地试用。

当前 alpha 进度：

- `aisync key list`
- `aisync recipient list`
- `aisync recipient add`
- `aisync recipient remove`
- `aisync history <profile>`
- `aisync pull`
- `aisync conflicts`
- richer `doctor`
- stricter profile validation
- sync 写入新的 vault package 前进行 conflict detection
- symlink policy
- app-running warnings
- Claude Code experimental sync-only profile
- capability-gated restore behavior
- Claude allowlist 和 denied-file boundary tests

新增：

- Linux support
- installation through `pipx`
- dangerous scenarios 的 tests

## v0.3: Public Preview

目标：让项目可以公开安装并具备合理 portability。

新增：

- Windows support
- Cursor experimental profile
- CI matrix for macOS/Linux/Windows
- release checksums
- Homebrew tap or packaged binaries
- profile authoring docs
- better recovery docs
- telemetry-free diagnostics bundle

## v1.0: Stable

目标：成为用户可以长期信任、反复使用的工具。

必需：

- stable profile schema
- documented threat model
- tested restore paths
- signed releases or verifiable checksums
- migration policy
- backward-compatible manifests where practical
- unsafe profile fields 的 clear deprecation policy
