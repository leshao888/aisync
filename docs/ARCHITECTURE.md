# AIsync Architecture

## Positioning

AIsync is a local-first sync framework for selected AI app data. It should not be coupled to one app. Each supported app is described by a profile, while shared safety logic lives in the core.

## High-Level Flow

Sync:

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

Restore:

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

Development repository:

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

User sync repository:

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

The user sync repository should not contain plaintext staging data, app auth files, app databases, private keys, or secret values.

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
gitstore      git pull/add/commit/push wrappers
restore       backup, preview, merge, replace-file policies
lock          prevent concurrent operations
state         local status and last operation metadata
log           privacy-safe structured logs
errors        error codes and suggested next actions
```

## Extension Model

Adding a new app should primarily mean adding a profile:

```text
profiles/<app>.yaml
```

Core logic should not include hard-coded app-specific paths except for bundled default profiles.

## Platform Strategy

All source paths must be defined per platform:

```yaml
source:
  macos: "~/.codex"
  linux: "~/.codex"
  windows: "%USERPROFILE%\\.codex"
```

The platform layer is responsible for:

- environment variable expansion
- home directory expansion
- path normalization
- Windows path handling
- detection of unsupported platforms

## Manifest Strategy

Manifest files may include:

- profile name and version
- created timestamp
- hostname
- platform
- encrypted package path
- file count
- byte count
- app profile hash
- tool version

Manifest files must not include chat text, file contents, tokens, cookies, private keys, or raw config secrets.

