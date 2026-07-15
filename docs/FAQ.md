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

Use this to inspect configured recipients:

```bash
aisync --repo ~/Developer/projects/aisync-vault recipient list
```

Use this to add another recipient:

```bash
aisync --repo ~/Developer/projects/aisync-vault recipient add <age-recipient>
```

## What happens if I lose the age private key?

You cannot decrypt old vault packages unless another recipient can decrypt them. Back up the age private key separately.

## Can AIsync sync Claude Code or Cursor?

Not yet as a stable profile. The architecture is profile-based, so future versions can add Claude Code, Cursor, Gemini CLI, and other local AI tools.

## Can multiple machines sync at the same time?

Use `aisync pull` and `aisync conflicts` before `sync`, and avoid simultaneous writes. Automatic conflict merge is a future feature.

## Does restore overwrite my current Codex data?

Default restore mode is `merge`. AIsync creates a backup before writing. Use `restore --dry-run` first.

## Why does restore ask me to close Codex?

Restoring while Codex is writing can race with app writes and corrupt local state. AIsync stops restore if it detects Codex running on macOS/Linux.

## Where are logs stored?

Logs are stored in the vault repository under `logs/`. Logs should not include chat snippets, file contents, tokens, or secrets.

## How do I see previous sync packages?

Use:

```bash
aisync --repo ~/Developer/projects/aisync-vault history codex
```

## How do I update my local vault before syncing?

Use:

```bash
aisync --repo ~/Developer/projects/aisync-vault pull
```

It runs `git pull --ff-only` and stops if the vault has diverged.

## How do I check whether the vault has Git conflicts?

Use:

```bash
aisync --repo ~/Developer/projects/aisync-vault conflicts
```

The safe states are `synced`, `ahead`, and `no-upstream`. `behind`, `diverged`, `dirty`, or `fetch-failed` need attention before sync.
