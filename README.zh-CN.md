# AIsync

简体中文 | [English](README.md)

![版本](https://img.shields.io/badge/version-0.2.0a6-0A7AFF)
![Python](https://img.shields.io/badge/python-%3E%3D3.10-3776AB)
![Profiles](https://img.shields.io/badge/profiles-Codex%20%7C%20Claude%20experimental-111827)
![加密](https://img.shields.io/badge/encryption-age-22C55E)
![密钥扫描](https://img.shields.io/badge/secret%20scan-gitleaks-F97316)
![CI](https://github.com/leshao888/aisync/actions/workflows/ci.yml/badge.svg)
![许可证](https://img.shields.io/badge/license-MIT-64748B)

AIsync 用来在多台机器之间安全同步选定的本地 AI app data。

第一个 stable profile 是 `Codex`，现在也提供 sync-only 的 `Claude Code` experimental profile。AIsync 不会把明文聊天记录直接上传到 GitHub：它只收集 allowlist 文件，拦截危险文件，用 `gitleaks` 扫描 plaintext staging data，再用 `age` 加密 package，最后只把 encrypted vault package 存入 Git。

## 适合谁？

如果你想做这些事，可以使用 AIsync：

- 不依赖同一个 Codex account，也能在多台机器之间迁移 Codex sessions
- 把 sync data 存在自己的 GitHub repository
- 避免提交 auth files、`.env`、tokens、sqlite databases 或 private keys
- 使用 profile-based framework，支持 Codex、experimental Claude Code sync，并逐步扩展更多本地 AI tools

## 两个仓库

请把 source code 和 personal sync data 分开：

```text
aisync        public source repository
aisync-vault  private encrypted data repository
```

```text
~/.codex
  |
  | allowlist + scan + age encrypt
  v
aisync-vault private Git repository
  |
  | decrypt + backup + restore
  v
another machine ~/.codex
```

本 source repository 可以公开。你的 `aisync-vault` repository 应当是 private，并且只包含 encrypted `.age` packages 和 non-sensitive manifests。

## Quick Start

在 macOS 安装必需工具：

```bash
brew install age gitleaks
```

Linux 上请通过发行版包管理器或 upstream release pages 安装 `git`、`age` 和 `gitleaks`。

使用 `pipx` 安装 AIsync：

```bash
pipx install git+https://github.com/leshao888/aisync.git
aisync --version
```

也可以从源码运行：

```bash
git clone git@github.com:leshao888/aisync.git
cd aisync
PYTHONPATH=src python3 -m aisync --version
```

创建 private vault repository 并初始化：

```bash
mkdir -p ~/Developer/projects/aisync-vault
cd ~/Developer/projects/aisync-vault
git init
git branch -M main
gh repo create aisync-vault --private --source . --remote origin

cd ~/Developer/projects/aisync
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault init
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault keygen
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault doctor
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault recipient list
```

查看每个 profile 支持的完整流程：

```bash
PYTHONPATH=src python3 -m aisync profile workflow codex
PYTHONPATH=src python3 -m aisync profile workflow claude
```

Codex 是 stable profile，支持完整 sync 和 restore 流程：

```bash
PYTHONPATH=src python3 -m aisync profile validate codex
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault sync codex --dry-run
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault sync codex
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault restore codex --dry-run
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault restore codex
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault history codex
```

Restore 写入前会创建 backup。完整恢复指南见：[Recovery](docs/RECOVERY.zh-CN.md)。

Claude Code 是 experimental 且 sync-only：

```bash
PYTHONPATH=src python3 -m aisync profile validate claude
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault sync claude --dry-run
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault sync claude
```

`restore claude` 被有意禁用。完整指南见：[Quick Start](docs/QUICKSTART.zh-CN.md)。

## Commands

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
aisync profile workflow codex
aisync profile show claude
aisync profile validate claude
aisync profile workflow claude
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

## Expected Output

成功 sync 的输出大致像这样：

```text
INFO    profile: codex
OK      matched allowlist: 128 files, 42 MB
OK      copied to staging: 128 files
OK      deny guard passed
OK      gitleaks scan passed
OK      encrypted package: vault/codex-20260715-133000.tar.gz.age
OK      git push completed
```

## 当前状态

`v0.2.0a6` 是完成 v0.2 规划收尾并在 CLI 中提供完整 profile workflow 的 alpha 迭代版本。Codex 是第一个 stable profile。Claude Code 提供 experimental sync-only profile，并由严格的 capability gate 阻止 restore，直到其 layout 和 restore behavior 通过验证。

当前限制：

- `doctor` 要求安装 `git`、`age` 和 `gitleaks`。
- 支持从 Git repository 使用 `pipx` 安装；正式发布包仍规划在 v0.3。
- Linux path handling 支持 `XDG_CONFIG_HOME`，restore 的 app-running 检测在没有 `pgrep` 时会 fallback 到 `/proc`。
- `sync` 会在 repo 未执行 Git 初始化时中止。
- `sync` 默认启用 push；没有 Git remote 时会中止。
- 如果 vault repository 是 behind、diverged 或无法 fetch remote state，`sync` 会在写入新的 encrypted package 前中止。
- Remote privacy 需要用户手动确认。
- `profile workflow` 会显示每个 profile 支持的命令流程。
- `sync claude` 是 experimental，必须先使用 `--dry-run` 预览；`restore claude` 已禁用。
- Restore 支持 `merge` 和 `replace-file`；暂不提供危险的整目录替换。
- 当前 archive format 使用 Python 标准库的 `tar.gz`。后续可添加 `zstd`。

## Documentation

- [Quick Start](docs/QUICKSTART.zh-CN.md)
- [Recovery](docs/RECOVERY.zh-CN.md)
- [FAQ](docs/FAQ.zh-CN.md)
- [Architecture](docs/ARCHITECTURE.zh-CN.md)
- [Roadmap](docs/ROADMAP.zh-CN.md)
- [Security Standard](docs/SECURITY_STANDARD.zh-CN.md)
- [Profile Spec](docs/PROFILE_SPEC.zh-CN.md)
- [Workflow](docs/WORKFLOW.zh-CN.md)
- [Testing](docs/TESTING.zh-CN.md)
- [Contributing](CONTRIBUTING.zh-CN.md)

简体中文翻译使用 `.zh-CN.md` 后缀。专有名词保留原文，例如 `AIsync`、`Codex`、`GitHub`、`profile`、`vault`、`manifest`、`age`、`gitleaks`、`sync`、`restore`、`dry-run` 和 `CI`。
