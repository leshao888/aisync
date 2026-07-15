# AIsync

简体中文 | [English](README.md)

![版本](https://img.shields.io/badge/version-0.1.0-0A7AFF)
![Python](https://img.shields.io/badge/python-%3E%3D3.10-3776AB)
![Codex](https://img.shields.io/badge/profile-Codex-111827)
![加密](https://img.shields.io/badge/encryption-age-22C55E)
![密钥扫描](https://img.shields.io/badge/secret%20scan-gitleaks-F97316)
![许可证](https://img.shields.io/badge/license-MIT-64748B)

AIsync 是一个面向本地 AI 工具数据的隐私优先同步器。

`v0.1` 的目标是先把 Codex 会话数据安全同步起来：本地只按白名单收集需要的文件，先扫描敏感信息，再用 `age` 加密，最后只把加密包提交到 Git 仓库。后续可以扩展 Claude Code、Cursor、Gemini CLI 和其他本地 AI 工具。

## 核心特性

- 基于 profile 的白名单同步
- 默认拦截认证文件、数据库、私钥、token、`.env` 等危险文件
- 使用 `gitleaks` 在明文阶段扫描疑似密钥
- 使用 `age` 生成加密同步包
- Git 仓库只保存加密包和非敏感 manifest
- 恢复前支持 dry-run 预览，并自动备份目标文件
- App 无关的扩展模型，后续新增工具主要靠新增 profile

## 仓库建议

建议分成两个仓库：

```text
aisync       公开仓库，放工具源码
aisync-vault 私有仓库，只放加密后的个人同步数据
```

`aisync` 可以公开，因为它只包含源码、文档、测试和 profile。真正的聊天记录、会话、配置备份应该放到单独的私有 vault 仓库里，并且只能以 `.age` 加密包形式保存。

## 安全模型

AIsync 默认流程：

```text
白名单收集
-> 危险文件拦截
-> gitleaks 明文扫描
-> tar.gz 打包
-> age 加密
-> 只提交/推送加密包
```

私有 Git 仓库不是端到端加密。AIsync 的保密性来自 `age` 加密，Git 只负责传输和版本存储。

## 本地开发安装

```bash
cd /Users/yaojiale/Developer/projects/aisync
python3 -m pip install -e .
```

也可以不安装，直接运行：

```bash
PYTHONPATH=src python3 -m aisync --version
```

## 必需依赖

- `git`
- `age`
- `gitleaks`

macOS 安装：

```bash
brew install age gitleaks
```

## 快速开始

先创建一个单独的私有同步仓库目录：

```bash
mkdir -p ~/Developer/projects/aisync-vault
cd ~/Developer/projects/aisync-vault
git init
git branch -M main
```

使用 AIsync 初始化 vault：

```bash
cd /Users/yaojiale/Developer/projects/aisync
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault init
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault keygen
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault doctor
```

手动添加私有 Git 远程仓库：

```bash
cd ~/Developer/projects/aisync-vault
git remote add origin git@github.com:YOUR_USER/aisync-vault.git
```

AIsync 不能离线判断远程仓库是否私有。请你在 GitHub 或自己的 Git 托管平台里确认 vault 仓库是私有仓库。

预览 Codex 同步：

```bash
cd /Users/yaojiale/Developer/projects/aisync
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault sync codex --dry-run
```

确认无误后执行真实同步：

```bash
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault sync codex
```

预览恢复：

```bash
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault restore codex --dry-run
```

以 merge 模式恢复：

```bash
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault restore codex
```

真实恢复前请关闭 Codex。AIsync v0.1 在 macOS/Linux 上检测到 Codex 进程时会中止恢复，避免 App 正在写入时被覆盖。

## 常用命令

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

## 当前限制

- `doctor` 要求本机安装 `git`、`age`、`gitleaks`。
- `sync` 会在同步仓库没有 `git init` 时中止。
- `sync` 默认推送远程仓库；如果没有 Git remote 会中止。
- 远程仓库是否私有需要用户自己确认。
- 恢复支持 `merge` 和 `replace-file`，暂不提供危险的整目录替换。
- v0.1 使用 Python 标准库的 `tar.gz`，后续可以增加 `zstd`。

## 项目文档

- `AGENTS.md`：Codex 长期项目规范
- `docs/ARCHITECTURE.md`：系统架构
- `docs/ROADMAP.md`：版本路线
- `docs/SECURITY_STANDARD.md`：安全标准
- `docs/PREPARATION.md`：开发准备事项
- `docs/PROFILE_SPEC.md`：profile 设计草案
- `docs/WORKFLOW.md`：开发工作流和 GitHub CLI 使用规范
- `docs/TESTING.md`：测试标准和边界测试清单
- `CONTRIBUTING.md`：贡献规范
