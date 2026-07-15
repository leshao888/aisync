# AIsync

[简体中文](README.zh-CN.md) | English

![Version](https://img.shields.io/badge/version-0.1.0-0A7AFF)
![Python](https://img.shields.io/badge/python-%3E%3D3.10-3776AB)
![Profile](https://img.shields.io/badge/profile-Codex-111827)
![Encryption](https://img.shields.io/badge/encryption-age-22C55E)
![Secret Scan](https://img.shields.io/badge/secret%20scan-gitleaks-F97316)
![License](https://img.shields.io/badge/license-MIT-64748B)

AIsync is a privacy-first sync tool for selected local AI app data.

The `v0.1` target is safe Codex session sync through a Git repository that stores only encrypted packages. Later targets may include Claude Code, Cursor, Gemini CLI, and other local AI tools.

## Highlights

- Allowlist-first app profiles
- Denied-file guard for auth files, databases, private keys, tokens, and `.env`
- Plaintext secret scanning with `gitleaks`
- Encrypted vault packages with `age`
- Git-backed storage for encrypted packages only
- Restore preview and backup-before-write behavior
- App-agnostic profile model for future tools

## Repository Split

Use two repositories:

```text
aisync       public source repository
aisync-vault private encrypted data repository
```

This repository should contain only source code, docs, tests, and app profiles. Chat history and local AI app data should go into a separate private vault repository as encrypted `.age` packages.

## Safety Model

AIsync uses this default flow:

```text
allowlist collection
-> denied-file guard
-> gitleaks plaintext scan
-> tar.gz archive
-> age encryption
-> Git commit/push of encrypted package only
```

Private Git repositories are not treated as encryption. Confidentiality comes from `age`.

## Install For Local Development

```bash
cd /Users/yaojiale/Developer/projects/aisync
python3 -m pip install -e .
```

Or run without installation:

```bash
PYTHONPATH=src python3 -m aisync --version
```

## Required Tools

- `git`
- `age`
- `gitleaks`

On macOS:

```bash
brew install age gitleaks
```

## Quick Start

Create a separate private sync repository:

```bash
mkdir -p ~/Developer/projects/aisync-vault
cd ~/Developer/projects/aisync-vault
git init
git branch -M main
```

Initialize the vault through AIsync:

```bash
cd /Users/yaojiale/Developer/projects/aisync
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault init
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault keygen
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault doctor
```

Add a private Git remote manually:

```bash
cd ~/Developer/projects/aisync-vault
git remote add origin git@github.com:YOUR_USER/aisync-vault.git
```

AIsync cannot verify remote privacy offline. Confirm the repository is private on GitHub or your Git host.

Preview Codex sync:

```bash
cd /Users/yaojiale/Developer/projects/aisync
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault sync codex --dry-run
```

Run Codex sync:

```bash
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault sync codex
```

Preview restore:

```bash
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault restore codex --dry-run
```

Restore in merge mode:

```bash
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault restore codex
```

Close Codex before running real restore. AIsync v0.1 stops restore if it detects a matching app process on macOS/Linux.

## Commands

```bash
aisync init
aisync doctor
aisync keygen
aisync profile list
aisync profile show codex
aisync profile validate codex
aisync sync codex --dry-run
aisync sync codex
aisync restore codex --dry-run
aisync restore codex
aisync status
aisync logs
```

## Current Limitations

- `doctor` requires `git`, `age`, and `gitleaks`.
- `sync` stops if the repo is not initialized with Git.
- `sync` with push enabled stops if no Git remote is configured.
- Remote privacy must be confirmed manually.
- Restore supports `merge` and `replace-file`; destructive tree replacement is intentionally not available.
- v0.1 uses `tar.gz` from the Python standard library. `zstd` can be added later.

## Project Docs

- `AGENTS.md` for durable project guidance
- `docs/ARCHITECTURE.md` for system design
- `docs/ROADMAP.md` for release planning
- `docs/SECURITY_STANDARD.md` for safety rules
- `docs/PREPARATION.md` for pre-development work
- `docs/PROFILE_SPEC.md` for app profile design

