# FAQ

[简体中文](FAQ.zh-CN.md) | English

## Is a private GitHub repository enough?

No. A private repository is access control, not end-to-end encryption. AIsync uses `age` so the Git repository stores encrypted packages only.

## Why does AIsync need `gitleaks` if data is encrypted?

Because chat history can contain API keys, tokens, passwords, or private keys. AIsync scans plaintext staging data before encryption so obvious secrets can stop the sync early.

## Does AIsync sync `auth.json`?

No. The Codex profile denies `auth.json`, sqlite databases, `.env`, token-like files, private keys, plugin caches, and other risky paths.

## What if I pasted a secret into a chat?

`gitleaks` may catch it. If it does, sync stops. You should rotate the secret and remove or redact it from local data before syncing.

## Can the source repository be public?

Yes. The `aisync` source repository can be public. Personal data should go into a separate private `aisync-vault` repository as encrypted `.age` packages.

## Can I use one vault across machines?

Yes, if every machine has access to the Git repository and has an age identity that can decrypt the packages.

## What happens if I lose the age private key?

You cannot decrypt old vault packages unless another recipient can decrypt them. Back up the age private key separately.

## Can AIsync sync Claude Code or Cursor?

Not as a stable profile in v0.1. The architecture is profile-based, so future versions can add Claude Code, Cursor, Gemini CLI, and other local AI tools.

## Can multiple machines sync at the same time?

This is not fully automated in v0.1. Use `git pull --ff-only` before sync and avoid simultaneous writes. Automatic conflict merge is a future feature.

## Does restore overwrite my current Codex data?

Default restore mode is `merge`. AIsync creates a backup before writing. Use `restore --dry-run` first.

## Why does restore ask me to close Codex?

Restoring while Codex is writing can race with app writes and corrupt local state. AIsync stops restore if it detects Codex running on macOS/Linux.

## Where are logs stored?

Logs are stored in the vault repository under `logs/`. Logs should not include chat snippets, file contents, tokens, or secrets.

