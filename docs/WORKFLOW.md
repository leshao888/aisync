# Development Workflow

This document defines the default workflow for AIsync development.

## Goal

Every user request should be handled as a complete engineering task:

```text
understand
-> implement
-> test
-> document
-> commit
-> push or open PR with gh
```

The only exception is when the user explicitly asks for planning, analysis, or no code changes.

## Standard Flow

1. Read `AGENTS.md` and relevant docs.
2. Inspect the affected code before editing.
3. Keep the change scoped to the request.
4. Implement the change.
5. Add or update tests.
6. Run local verification.
7. Update README/docs when user-facing behavior changes.
8. Review `git status --short`.
9. Commit with a Chinese commit message.
10. Use `gh` for GitHub operations.

## Required Local Verification

Run these before every code commit:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPYCACHEPREFIX=$(mktemp -d) python3 -m compileall -q src tests
```

For documentation-only changes, the test suite is optional unless the docs include runnable commands or workflow changes. If tests are skipped, say so in the final summary.

## GitHub CLI Usage

Use `gh` for repository and PR operations:

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

Use `git` for local source control:

```bash
git status --short
git add .
git commit -m "文档: 添加开发工作流规范"
git push
```

## Branch Strategy

Prefer feature branches for non-trivial changes:

```bash
git checkout -b feature/topic
git add .
git commit -m "功能: 添加 xxx"
git push -u origin feature/topic
gh pr create --title "功能: 添加 xxx" --body "..."
```

Small documentation-only changes may go directly to `main` when the user asks for a quick update.

## Chinese Commit Messages

Commit messages must be Chinese.

Recommended prefixes:

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

A task is not done until:

- implementation is complete
- tests cover normal paths and risky failure paths
- required verification passes
- docs are updated when behavior changes
- no secrets or local private data are staged
- commit message is Chinese
- GitHub push or PR is completed when requested and network/auth are available

## Secret And Privacy Check

Before committing, check for high-risk files:

```bash
git status --short
git ls-files | rg '(^|/)id_(rsa|ed25519)$|\\.ssh|\\.pem|\\.key|agekey|\\.env'
```

The command should produce no output for tracked files.

