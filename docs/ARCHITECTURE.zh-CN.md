# AIsync Architecture

简体中文 | [English](ARCHITECTURE.md)

## Positioning

AIsync 是一个 local-first sync framework，用于同步选定的 AI app data。它不应绑定某一个 app。每个 supported app 都由一个 profile 描述，共用的安全逻辑放在 core。

## High-Level Flow

Sync：

```text
profile
-> platform path resolution
-> dependency check
-> acquire lock
-> collect allowlisted files into staging
-> block denied files
-> scan plaintext staging
-> generate manifest
-> archive
-> encrypt with age
-> write vault package atomically
-> git commit and push
-> cleanup staging
-> update state
```

Restore：

```text
git pull
-> select vault package
-> acquire lock
-> decrypt into temporary directory
-> verify manifest/profile
-> dry-run preview
-> backup local target
-> restore allowlisted files only
-> verify restored count/hash where possible
-> cleanup temporary plaintext
-> update state
```

## Repository Layout

Development repository：

```text
aisync/
├── AGENTS.md
├── README.md
├── docs/
├── profiles/
├── schemas/
├── src/               # later
├── tests/             # later
└── pyproject.toml     # later
```

User sync repository：

```text
aisync-repo/
├── vault/
│   └── codex-20260715-133000.tar.zst.age
├── manifests/
│   └── codex-20260715-133000.json
├── profiles/
├── .aisync-state.json
└── .gitignore
```

User sync repository 不应包含 plaintext staging data、app auth files、app databases、private keys 或 secret values。

## Core Modules

```text
cli           command parsing and UX
profile       load, validate, and version profiles
platform      macOS/Linux/Windows path resolution
doctor        dependency and environment checks
collect       allowlist copying into staging
guard         deny rules and dangerous file detection
scan          gitleaks and lightweight fallback scans
archive       tar.zst or tar.gz packaging
crypto        age encrypt/decrypt and recipient handling
gitstore      git pull/add/commit/push 和 conflict inspection wrappers
restore       backup, preview, merge, replace-file policies
lock          prevent concurrent operations
state         local status and last operation metadata
log           privacy-safe structured logs
errors        error codes and suggested next actions
```

## Extension Model

新增 app 主要应当意味着新增一个 profile：

```text
profiles/<app>.yaml
```

Core logic 不应包含 hard-coded app-specific paths，除了 bundled default profiles。

## Platform Strategy

所有 source paths 必须按 platform 定义：

```yaml
source:
  macos: "~/.codex"
  linux: "~/.codex"
  windows: "%USERPROFILE%\\.codex"
```

Platform layer 负责：

- environment variable expansion
- home directory expansion
- path normalization
- Windows path handling
- detection of unsupported platforms

## Manifest Strategy

Manifest files 可以包含：

- profile name and version
- created timestamp
- hostname
- platform
- encrypted package path
- file count
- byte count
- app profile hash
- tool version

Manifest files 不得包含 chat text、file contents、tokens、cookies、private keys 或 raw config secrets。
