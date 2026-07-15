# Testing Standard

AIsync handles private local data, so tests must treat safety behavior as product behavior.

## Required Test Layers

Use these layers as the project grows:

```text
unit tests
-> integration tests with fake app data
-> end-to-end tests with fake age/gitleaks tools
-> CLI behavior tests
-> CI verification
```

## Required Local Commands

Run before every code commit:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPYCACHEPREFIX=$(mktemp -d) python3 -m compileall -q src tests
```

## Boundary Test Checklist

Add or update tests when touching these areas:

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

Security checks must be tested as fatal behavior:

```text
dangerous input
-> operation stops
-> clear DANGER or ERROR output
-> no encrypted package written
-> no restore writes happen
-> no secret appears in logs
```

## Fake Tool Tests

Use fake `age`, `age-keygen`, and `gitleaks` in tests to avoid requiring real external tools for the basic end-to-end suite.

The fake-tool test should cover:

- init
- sync
- encrypted vault file creation
- manifest creation
- restore
- backup creation

## CI Expectations

GitHub Actions should run on:

- `push`
- `pull_request`

Required Python versions:

- 3.10
- 3.11
- 3.12

Required CI commands:

```bash
python -m unittest discover -s tests -v
PYTHONPYCACHEPREFIX=$(mktemp -d) python -m compileall -q src tests
```

Future CI additions:

- ruff
- mypy or pyright
- coverage threshold
- gitleaks repository scan
- package build check

