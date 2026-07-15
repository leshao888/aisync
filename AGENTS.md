# AIsync Project Guidance

[简体中文翻译](AGENTS.zh-CN.md) | English

This file is the normative project guidance for Codex. The Simplified Chinese file is a translation for human readers.

## Project Mission

AIsync is a local AI app data safety sync tool. It should help users sync selected local data for tools such as Codex, Claude Code, Cursor, and similar AI developer apps across machines without relying on the same product account.

The tool must be privacy-first. It should never treat a private Git repository as sufficient protection. The intended storage model is:

1. Collect only allowlisted files from each app profile.
2. Block denied files before packaging.
3. Scan plaintext staging data for secrets.
4. Encrypt the package with age.
5. Commit only encrypted vault files and non-sensitive manifests to Git.

## Current Phase

This repository is in `v0.2` alpha development. The user explicitly approved starting implementation after the planning phase.

Allowed work now:

- Python CLI implementation and alpha iteration
- Codex and Claude Code experimental profile implementation
- Local fake-data tests
- Documentation updates
- Safety checks and restore logic

Avoid unless the user explicitly asks:

- Touching real Codex or Claude data
- Running real sync or restore operations against `~/.codex` or `~/.claude`
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

## Required Development Workflow

When the user gives a development request, handle it end to end unless the user explicitly asks for planning only.

Default workflow:

1. Read the relevant code and project guidance before editing.
2. Define the narrow implementation scope.
3. Implement the change.
4. Add or update tests for normal paths, failure paths, and security boundaries.
5. Run the full local verification suite.
6. Fix failures until all required tests pass.
7. Update user-facing docs when commands, behavior, safety rules, or workflows change.
8. Commit only after tests pass.
9. Use Chinese commit messages.
10. Use `gh` for GitHub repository and pull request operations when network/auth are available.

Do not commit code with failing tests. Do not skip boundary tests for sync, restore, encryption, secret scanning, Git, path handling, or profile behavior.

Required local verification before commit:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPYCACHEPREFIX=$(mktemp -d) python3 -m compileall -q src tests
```

Use additional targeted tests when a change affects:

- denied-file rules
- secret scanning
- age encryption/decryption
- Git remote behavior
- restore backup behavior
- symlink handling
- archive extraction
- cross-platform path resolution

## Commit And GitHub Rules

Commit messages must be Chinese and should use this style:

```text
功能: 添加 Codex 同步预览
修复: 修复恢复备份失败时未中止的问题
文档: 添加简体中文 README
测试: 增加危险文件边界测试
安全: 增加私钥文件拦截规则
重构: 拆分 profile 校验逻辑
构建: 添加 GitHub Actions CI
```

Prefer feature branches and pull requests for non-trivial work:

```bash
git checkout -b feature/short-topic
git add .
git commit -m "功能: 添加 xxx"
git push -u origin feature/short-topic
gh pr create --title "功能: 添加 xxx" --body "..."
```

Small documentation-only changes may be committed directly to `main` when the user asks for it.

## Planned CLI Surface

Initial commands:

```bash
aisync init
aisync doctor
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
aisync key list
aisync recipient list
aisync recipient add <age-recipient>
aisync recipient remove <age-recipient>
aisync history codex
```

Later commands:

```bash
aisync keygen
aisync key list
aisync recipient add
aisync recipient remove
aisync history codex
aisync pull
aisync conflicts
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

Implemented commands currently include:

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

## References

Project planning documents live in `docs/`.

- `docs/ARCHITECTURE.md`
- `docs/ROADMAP.md`
- `docs/SECURITY_STANDARD.md`
- `docs/PREPARATION.md`
- `docs/PROFILE_SPEC.md`
- `docs/WORKFLOW.md`
- `docs/TESTING.md`
- `CONTRIBUTING.md`
