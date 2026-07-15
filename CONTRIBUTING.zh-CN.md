# Contributing

简体中文 | [English](CONTRIBUTING.md)

感谢你帮助改进 AIsync。

## 开始之前

请先阅读：

- `AGENTS.md`
- `docs/WORKFLOW.md`
- `docs/TESTING.md`
- `docs/SECURITY_STANDARD.md`

## Development Setup

```bash
python3 -m pip install -e .
PYTHONPATH=src python3 -m aisync --version
```

真实 sync behavior 需要这些 external tools：

```bash
brew install age gitleaks
```

Tests 会尽可能使用 fake tools，所以基础 test suite 可以在没有真实 `age` 和 `gitleaks` 的情况下运行。

## Testing

运行：

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPYCACHEPREFIX=$(mktemp -d) python3 -m compileall -q src tests
```

需要为 normal behavior、failure behavior 和 safety boundaries 添加 tests。

## Commit Messages

使用中文 commit messages：

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

永远不要提交：

- real Codex sessions
- personal sync repositories 里的 vault packages
- `.env`
- SSH private keys
- age private keys
- API keys
- OAuth tokens
- cookies
- app auth files

Source repository 可以公开。Personal sync vault repositories 必须私有，并且只应包含 encrypted `.age` packages 和 non-sensitive manifests。

