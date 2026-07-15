# Development Workflow

简体中文 | [English](WORKFLOW.md)

本文档定义 AIsync development 的默认 workflow。

## Goal

每个用户需求都应作为完整 engineering task 处理：

```text
understand
-> implement
-> test
-> document
-> commit
-> push or open PR with gh
```

唯一例外：用户明确要求只做 planning、analysis 或不做 code changes。

## Standard Flow

1. 阅读 `AGENTS.md` 和相关 docs。
2. 编辑前检查受影响代码。
3. 将改动限制在需求范围内。
4. 实现改动。
5. 添加或更新 tests。
6. 运行 local verification。
7. 当 user-facing behavior 改变时更新 README/docs。
8. 检查 `git status --short`。
9. 使用中文 commit message。
10. 使用 `gh` 处理 GitHub operations。

## Required Local Verification

每次 code commit 前运行：

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPYCACHEPREFIX=$(mktemp -d) python3 -m compileall -q src tests
```

Documentation-only changes 可以不跑 test suite，除非 docs 包含 runnable commands 或 workflow changes。如果跳过 tests，需要在 final summary 说明。

## GitHub CLI Usage

使用 `gh` 处理 repository 和 PR operations：

```bash
gh auth status
gh repo view
gh repo edit
gh pr create
gh pr view
gh pr merge
gh run list
gh run view
```

使用 `git` 处理 local source control：

```bash
git status --short
git add .
git commit -m "文档: 添加开发工作流规范"
git push
```

## Branch Strategy

非平凡改动优先使用 feature branches：

```bash
git checkout -b feature/topic
git add .
git commit -m "功能: 添加 xxx"
git push -u origin feature/topic
gh pr create --title "功能: 添加 xxx" --body "..."
```

用户要求快速更新时，小型 documentation-only changes 可以直接进入 `main`。

## Chinese Commit Messages

Commit messages 必须使用中文。

推荐 prefixes：

```text
功能: 添加 xxx
修复: 修复 xxx
文档: 更新 xxx
测试: 增加 xxx
安全: 加强 xxx
重构: 拆分 xxx
构建: 添加 xxx
发布: 准备 xxx
```

## Definition Of Done

满足以下条件才算完成：

- implementation is complete
- tests cover normal paths and risky failure paths
- required verification passes
- docs are updated when behavior changes
- no secrets or local private data are staged
- commit message is Chinese
- GitHub push or PR is completed when requested and network/auth are available

## Secret And Privacy Check

Commit 前检查 high-risk files：

```bash
git status --short
git ls-files | rg '(^|/)id_(rsa|ed25519)$|\\.ssh|\\.pem|\\.key|agekey|\\.env'
```

该命令对 tracked files 应无输出。

