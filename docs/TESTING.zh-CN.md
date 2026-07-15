# Testing Standard

简体中文 | [English](TESTING.md)

AIsync 处理 private local data，因此 tests 必须把 safety behavior 当作 product behavior。

## Required Test Layers

随着项目增长，使用这些 layers：

```text
unit tests
-> integration tests with fake app data
-> end-to-end tests with fake age/gitleaks tools
-> CLI behavior tests
-> CI verification
```

## Required Local Commands

每次 code commit 前运行：

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPYCACHEPREFIX=$(mktemp -d) python3 -m compileall -q src tests
```

## Boundary Test Checklist

触碰以下区域时，添加或更新 tests：

- denied file appears in included scope
- secret scanner reports a finding
- `age` is missing
- `gitleaks` is missing
- `recipients.txt` is missing
- `recipients.txt` is empty
- Git repository is not initialized
- Git remote is missing
- Git push fails
- restore backup fails
- restore target app appears to be running
- symlink appears in sync scope
- symlink points outside source root
- tar archive contains path traversal
- manifest is missing
- manifest references a missing archive
- archive contains files outside the active profile
- paths contain spaces
- paths contain non-ASCII characters
- source directory is empty
- source directory does not exist

## Security Regression Tests

Security checks 必须作为 fatal behavior 测试：

```text
dangerous input
-> operation stops
-> clear DANGER or ERROR output
-> no encrypted package written
-> no restore writes happen
-> no secret appears in logs
```

## Fake Tool Tests

在 tests 中使用 fake `age`、`age-keygen` 和 `gitleaks`，避免基础 end-to-end suite 依赖真实 external tools。

Fake-tool test 应覆盖：

- init
- sync
- encrypted vault file creation
- manifest creation
- restore
- backup creation

## CI Expectations

GitHub Actions 应在以下场景运行：

- `push`
- `pull_request`

Required Python versions：

- 3.10
- 3.11
- 3.12

Required CI commands：

```bash
python -m unittest discover -s tests -v
PYTHONPYCACHEPREFIX=$(mktemp -d) python -m compileall -q src tests
```

Future CI additions：

- ruff
- mypy or pyright
- coverage threshold
- gitleaks repository scan
- package build check

