# Recovery

[简体中文](RECOVERY.zh-CN.md) | English

This guide explains how to restore Codex data from an AIsync vault.

## Before You Restore

Restore is more dangerous than sync because it writes into an app data directory.

Before running real restore:

- close Codex
- run `restore --dry-run`
- confirm the active profile is `codex`
- confirm the vault repository is the right one
- confirm this machine has the matching age private key

## New Machine Setup

Clone both repositories:

```bash
mkdir -p ~/Developer/projects
cd ~/Developer/projects
git clone git@github.com:leshao888/aisync.git
git clone git@github.com:YOUR_USER/aisync-vault.git
```

Install dependencies:

```bash
brew install age gitleaks
```

Restore or configure the age identity:

```bash
export AISYNC_AGE_IDENTITY="$HOME/.config/aisync/keys/identity.txt"
```

The identity must match one of the recipients used to encrypt the vault package.

## Check Readiness

```bash
cd ~/Developer/projects/aisync
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault doctor
```

If `doctor` reports missing dependencies, recipients, Git remote, or identity issues, fix those first.

## Preview Restore

```bash
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault restore codex --dry-run
```

Dry-run should show the files that would be restored. It does not create a backup and does not write into `~/.codex`.

## Run Restore

```bash
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault restore codex
```

Default restore mode is `merge`:

- existing files are not overwritten where possible
- missing files are copied
- a backup directory is created before writes

## Replace Files

Use `replace-file` only when you understand the effect:

```bash
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault restore codex --mode replace-file
```

AIsync v0.1 does not provide destructive tree replacement.

## Backup Location

Backups are created inside the vault repository:

```text
backups/codex/backup-YYYYMMDD-HHMMSS/
```

Backups are local runtime data and should not be committed.

## Common Restore Failures

### Codex is running

Close Codex and rerun restore. AIsync stops restore when it detects a matching Codex process on macOS/Linux.

### age identity is missing

Restore the private age identity on this machine, or set:

```bash
export AISYNC_AGE_IDENTITY="/path/to/identity.txt"
```

### Manifest exists but archive is missing

Run:

```bash
cd ~/Developer/projects/aisync-vault
git pull --ff-only
```

Then retry restore.

### Backup failed

Do not force restore. Fix permissions or disk space first. AIsync should not write into the target directory if backup fails.

