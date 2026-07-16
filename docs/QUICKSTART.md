# Quick Start

[简体中文](QUICKSTART.zh-CN.md) | English

This guide walks through the first Codex sync with AIsync.

## What You Will Create

You need two repositories:

```text
aisync        public source repository
aisync-vault  private encrypted data repository
```

`aisync-vault` should be private. It stores encrypted `.age` packages, not plaintext Codex sessions.

## 1. Install Required Tools

On macOS:

```bash
brew install age gitleaks gh
```

On Linux, install `git`, `age`, `gitleaks`, and optionally `gh` from your distro packages or upstream release pages. AIsync uses `XDG_CONFIG_HOME` for its local config directory when it is set.

Check:

```bash
git --version
age --version
gitleaks version
gh auth status
```

## 2. Install AIsync

Recommended for an isolated CLI install:

```bash
pipx install git+https://github.com/leshao888/aisync.git
aisync --version
```

For source development:

```bash
mkdir -p ~/Developer/projects
cd ~/Developer/projects
git clone git@github.com:leshao888/aisync.git
cd aisync
PYTHONPATH=src python3 -m aisync --version
```

You should see:

```text
aisync 0.2.0a5
```

The remaining examples use the source checkout form, `PYTHONPATH=src python3 -m aisync`. If you installed with `pipx`, use `aisync` instead.

## 3. Create A Private Vault Repository

Create the local vault directory:

```bash
mkdir -p ~/Developer/projects/aisync-vault
cd ~/Developer/projects/aisync-vault
git init
git branch -M main
```

Create the private GitHub repository:

```bash
gh repo create aisync-vault --private --source . --remote origin
```

Confirm it is private on GitHub. AIsync cannot verify remote privacy offline.

## 4. Initialize The Vault

```bash
cd ~/Developer/projects/aisync
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault init
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault keygen
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault doctor
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault key list
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault recipient list
```

`keygen` creates a local age private key and adds its public recipient to `recipients.txt`.

Back up the age private key separately. Without it, another machine cannot decrypt the vault.

To add another machine or public recipient later:

```bash
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault recipient add <age-recipient>
```

## 5. Preview Codex Sync

Always preview first:

```bash
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault sync codex --dry-run
```

Expected output:

```text
INFO    profile: codex
INFO    source: /Users/YOU/.codex
OK      matched allowlist: ...
INFO    dry-run: no files copied, scanned, encrypted, committed, or pushed
```

If you see denied files, stop and inspect the profile or local data.

## 6. Run Codex Sync

```bash
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault sync codex
```

Successful sync should:

- copy allowlisted files into temporary staging
- block denied files
- run `gitleaks`
- create a `tar.gz`
- encrypt it with `age`
- write `vault/*.age`
- write `manifests/*.json`
- commit and push encrypted data to `aisync-vault`

## 7. Optional: Preview Claude Code Sync

Claude Code support is experimental and sync-only. Always inspect the profile and preview before a real sync:

```bash
PYTHONPATH=src python3 -m aisync profile show claude
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault sync claude --dry-run
```

The profile includes selected project sessions, history, `CLAUDE.md`, commands, agents, and skills. Credentials, `.env` files, databases, private keys, and token-like files are denied. `restore claude` is intentionally disabled.

## 8. Daily Usage

```bash
cd ~/Developer/projects/aisync
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault pull
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault conflicts
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault sync codex --dry-run
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault sync codex
```

`conflicts` should report `synced`, `ahead`, or `no-upstream` before you sync. If it reports `behind`, run `pull`; if it reports `diverged`, `dirty`, or `fetch-failed`, inspect the vault repository first.

## 9. Verify The Vault

```bash
cd ~/Developer/projects/aisync-vault
git status --short
find vault manifests -maxdepth 2 -type f | sort
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault history codex
```

The vault should contain encrypted packages and manifests. It should not contain:

```text
auth.json
.env
*.sqlite
id_rsa
id_ed25519
plaintext sessions outside encrypted packages
```

## Next

- Read [Recovery](RECOVERY.md) before restoring on another machine.
- Read [FAQ](FAQ.md) for common safety questions.
