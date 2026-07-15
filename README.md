# AIsync

AIsync is a privacy-first sync tool for selected local AI app data.

The v0.1 target is safe Codex session sync through a Git repository that stores only encrypted packages. Later targets may include Claude Code, Cursor, Gemini CLI, and other local AI tools.

## Status

`v0.1` is under development. Codex is the first stable profile.

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

## Basic Usage

Create a separate sync repository:

```bash
mkdir -p ~/Developer/projects/aisync-repo
aisync --repo ~/Developer/projects/aisync-repo init
aisync --repo ~/Developer/projects/aisync-repo keygen
aisync --repo ~/Developer/projects/aisync-repo doctor
```

Add a private Git remote manually:

```bash
cd ~/Developer/projects/aisync-repo
git remote add origin git@github.com:YOUR_USER/aisync-repo.git
```

AIsync cannot verify remote privacy offline. Confirm the repository is private on GitHub or your Git host.

Preview Codex sync:

```bash
aisync --repo ~/Developer/projects/aisync-repo sync codex --dry-run
```

Run Codex sync:

```bash
aisync --repo ~/Developer/projects/aisync-repo sync codex
```

Preview restore:

```bash
aisync --repo ~/Developer/projects/aisync-repo restore codex --dry-run
```

Restore in merge mode:

```bash
aisync --repo ~/Developer/projects/aisync-repo restore codex
```

Close Codex before running real restore. AIsync v0.1 stops restore if it detects a matching app process on macOS/Linux.

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
