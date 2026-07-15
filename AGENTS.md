# AIsync Project Guidance

## Project Mission

AIsync is a local AI app data safety sync tool. It should help users sync selected local data for tools such as Codex, Claude Code, Cursor, and similar AI developer apps across machines without relying on the same product account.

The tool must be privacy-first. It should never treat a private Git repository as sufficient protection. The intended storage model is:

1. Collect only allowlisted files from each app profile.
2. Block denied files before packaging.
3. Scan plaintext staging data for secrets.
4. Encrypt the package with age.
5. Commit only encrypted vault files and non-sensitive manifests to Git.

## Current Phase

This repository is in `v0.1` development. The user explicitly approved starting implementation after the planning phase.

Allowed work now:

- Python CLI implementation
- Codex profile implementation
- Local fake-data tests
- Documentation updates
- Safety checks and restore logic

Avoid unless the user explicitly asks:

- Touching real Codex or Claude data
- Running real sync or restore operations against `~/.codex`
- Creating or pushing to remote GitHub repositories
- Weakening encryption, scanning, or denied-file behavior

## Hard Safety Rules

- Default to allowlist collection. Never sync a whole app directory.
- Default to encryption. Do not support plaintext remote sync in normal workflows.
- Default to secret scanning. If scanning cannot run, sync must stop unless the user explicitly chooses a documented unsafe mode.
- Denied files are fatal. Discovery of auth files, token files, private keys, sqlite databases, cookies, or `.env` files must stop the operation.
- Restore must create a backup before writing to an app directory.
- Restore must support dry-run preview before real writes.
- The tool must not store age private keys, GitHub tokens, app auth files, cookies, or API keys in the sync repository.
- Logs must not contain file contents, chat snippets, tokens, or secrets.
- App profiles must be versioned and schema-validated.
- Cross-platform paths must be resolved through the platform layer, not embedded in core sync logic.

## Product Principles

- Make the safe path the default path.
- Every dangerous state needs a clear reason and a next action.
- The user should be able to judge success from the command output without reading logs.
- Profiles should be easy to add, but hard to make unsafe.
- The core should be app-agnostic. Codex is the first profile, not a special case baked into the engine.

## Planned CLI Surface

Initial commands:

```bash
aisync init
aisync doctor
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

Later commands:

```bash
aisync keygen
aisync key list
aisync recipient add
aisync recipient remove
aisync history codex
aisync pull
aisync unlock --stale
```

## Output Levels

All user-facing output should use these levels:

- `INFO`: normal progress
- `OK`: successful step
- `WARN`: can continue, but user should notice
- `DANGER`: leak, overwrite, deletion, or credential risk; default stop
- `ERROR`: operation failure
- `NEXT`: concrete next command or action

## MVP Definition

Version `v0.1` should provide a complete safe sync loop for Codex on macOS:

- `doctor`
- profile validation
- `sync --dry-run`
- allowlist collection
- deny guard
- gitleaks scanning
- age encryption
- Git commit and push
- `restore --dry-run`
- restore with backup
- state file
- privacy-safe logs

Do not expand to many apps before the Codex flow is boringly reliable.

Implemented v0.1 commands currently include:

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

## References

Project planning documents live in `docs/`.

- `docs/ARCHITECTURE.md`
- `docs/ROADMAP.md`
- `docs/SECURITY_STANDARD.md`
- `docs/PREPARATION.md`
- `docs/PROFILE_SPEC.md`
