# Contributing

Thanks for helping improve AIsync.

## Before You Start

Read:

- `AGENTS.md`
- `docs/WORKFLOW.md`
- `docs/TESTING.md`
- `docs/SECURITY_STANDARD.md`

## Development Setup

```bash
python3 -m pip install -e .
PYTHONPATH=src python3 -m aisync --version
```

Required external tools for real sync behavior:

```bash
brew install age gitleaks
```

Tests use fake tools where possible, so the basic test suite can run without real `age` and `gitleaks`.

## Testing

Run:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPYCACHEPREFIX=$(mktemp -d) python3 -m compileall -q src tests
```

Add tests for normal behavior, failure behavior, and safety boundaries.

## Commit Messages

Use Chinese commit messages:

```text
功能: 添加 xxx
修复: 修复 xxx
文档: 更新 xxx
测试: 增加 xxx
安全: 加强 xxx
重构: 拆分 xxx
构建: 添加 xxx
```

## Privacy Rules

Never commit:

- real Codex sessions
- vault packages from personal sync repositories
- `.env`
- SSH private keys
- age private keys
- API keys
- OAuth tokens
- cookies
- app auth files

The source repository can be public. Personal sync vault repositories must be private and should contain only encrypted `.age` packages plus non-sensitive manifests.

