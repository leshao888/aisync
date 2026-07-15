# AIsync

[简体中文](README.zh-CN.md) | English

![Version](https://img.shields.io/badge/version-0.2.0a4-0A7AFF)
![Python](https://img.shields.io/badge/python-%3E%3D3.10-3776AB)
![Profiles](https://img.shields.io/badge/profiles-Codex%20%7C%20Claude%20experimental-111827)
![Encryption](https://img.shields.io/badge/encryption-age-22C55E)
![Secret Scan](https://img.shields.io/badge/secret%20scan-gitleaks-F97316)
![CI](https://github.com/leshao888/aisync/actions/workflows/ci.yml/badge.svg)
![License](https://img.shields.io/badge/license-MIT-64748B)

AIsync safely syncs selected local AI app data across machines.

The first stable profile is `Codex`. A sync-only experimental profile is also available for `Claude Code`. AIsync does not upload plaintext chat history to GitHub: it collects only allowlisted files, blocks dangerous files, scans plaintext staging data with `gitleaks`, encrypts the package with `age`, and stores only encrypted vault packages in Git.

## Who Is This For?

Use AIsync if you want to:

- move Codex sessions between machines without relying on the same Codex account
- keep sync data in your own GitHub repository
- avoid committing auth files, `.env`, tokens, sqlite databases, or private keys
- use a profile-based framework that can support Codex, experimental Claude Code sync, and more local AI tools over time

## Two Repositories

Keep source code and personal sync data separate:

```text
aisync        public source repository
aisync-vault  private encrypted data repository
```

```text
~/.codex
  |
  | allowlist + scan + age encrypt
  v
aisync-vault private Git repository
  |
  | decrypt + backup + restore
  v
another machine ~/.codex
```

This source repository can be public. Your `aisync-vault` repository should be private and should contain only encrypted `.age` packages plus non-sensitive manifests.

## Quick Start

Install required tools:

```bash
brew install age gitleaks
```

Clone and run AIsync:

```bash
git clone git@github.com:leshao888/aisync.git
cd aisync
PYTHONPATH=src python3 -m aisync --version
```

Create a private vault repository and initialize it:

```bash
mkdir -p ~/Developer/projects/aisync-vault
cd ~/Developer/projects/aisync-vault
git init
git branch -M main
gh repo create aisync-vault --private --source . --remote origin

cd ~/Developer/projects/aisync
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault init
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault keygen
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault doctor
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault recipient list
```

Preview and run Codex sync:

```bash
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault sync codex --dry-run
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault sync codex
```

Read the full guide: [Quick Start](docs/QUICKSTART.md).

## Restore

Close Codex before restore, then preview first:

```bash
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault restore codex --dry-run
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault restore codex
```

Restore creates a backup before writing. Read the full recovery guide: [Recovery](docs/RECOVERY.md).

## Commands

```bash
aisync init
aisync doctor
aisync pull
aisync conflicts
aisync keygen
aisync key list
aisync recipient list
aisync recipient add <age-recipient>
aisync recipient remove <age-recipient>
aisync profile list
aisync profile show codex
aisync profile validate codex
aisync profile show claude
aisync profile validate claude
aisync sync codex --dry-run
aisync sync codex
aisync sync claude --dry-run
aisync sync claude
aisync restore codex --dry-run
aisync restore codex
aisync status
aisync logs
aisync history codex
```

## Expected Output

Successful sync should look roughly like this:

```text
INFO    profile: codex
OK      matched allowlist: 128 files, 42 MB
OK      copied to staging: 128 files
OK      deny guard passed
OK      gitleaks scan passed
OK      encrypted package: vault/codex-20260715-133000.tar.gz.age
OK      git push completed
```

## Current Status

`v0.2.0a4` is an alpha iteration. Codex is the first stable profile. Claude Code now has an experimental sync-only profile with a strict capability gate that blocks restore until its layout and restore behavior are validated.

Current limitations:

- `doctor` requires `git`, `age`, and `gitleaks`.
- `sync` stops if the repo is not initialized with Git.
- `sync` with push enabled stops if no Git remote is configured.
- `sync` stops before writing a new encrypted package if the vault repository is behind, diverged, or cannot fetch remote state.
- Remote privacy must be confirmed manually.
- `sync claude` is experimental and must be previewed with `--dry-run`; `restore claude` is disabled.
- Restore supports `merge` and `replace-file`; destructive tree replacement is intentionally not available.
- The current archive format uses `tar.gz` from the Python standard library. `zstd` can be added later.

## Documentation

- [Quick Start](docs/QUICKSTART.md)
- [Recovery](docs/RECOVERY.md)
- [FAQ](docs/FAQ.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Roadmap](docs/ROADMAP.md)
- [Security Standard](docs/SECURITY_STANDARD.md)
- [Profile Spec](docs/PROFILE_SPEC.md)
- [Workflow](docs/WORKFLOW.md)
- [Testing](docs/TESTING.md)
- [Contributing](CONTRIBUTING.md)

Simplified Chinese translations use the `.zh-CN.md` suffix, such as `docs/QUICKSTART.zh-CN.md`.
