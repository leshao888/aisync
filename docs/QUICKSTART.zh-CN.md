# Quick Start

简体中文 | [English](QUICKSTART.md)

本指南带你完成第一次 Codex sync。

## 你会创建什么

你需要两个 repository：

```text
aisync        public source repository
aisync-vault  private encrypted data repository
```

`aisync-vault` 应当是 private。它保存 encrypted `.age` packages，不保存 plaintext Codex sessions。

## 1. 安装必需工具

macOS：

```bash
brew install age gitleaks gh
```

检查：

```bash
git --version
age --version
gitleaks version
gh auth status
```

## 2. Clone AIsync

```bash
mkdir -p ~/Developer/projects
cd ~/Developer/projects
git clone git@github.com:leshao888/aisync.git
cd aisync
PYTHONPATH=src python3 -m aisync --version
```

你应该看到：

```text
aisync 0.2.0a3
```

## 3. 创建 private vault repository

创建本地 vault directory：

```bash
mkdir -p ~/Developer/projects/aisync-vault
cd ~/Developer/projects/aisync-vault
git init
git branch -M main
```

创建 private GitHub repository：

```bash
gh repo create aisync-vault --private --source . --remote origin
```

请在 GitHub 上确认它是 private。AIsync 不能离线验证 remote privacy。

## 4. 初始化 vault

```bash
cd ~/Developer/projects/aisync
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault init
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault keygen
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault doctor
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault key list
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault recipient list
```

`keygen` 会创建 local age private key，并把对应 public recipient 加入 `recipients.txt`。

请单独备份 age private key。没有它，另一台机器无法 decrypt vault。

以后添加另一台机器或 public recipient：

```bash
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault recipient add <age-recipient>
```

## 5. 预览 Codex sync

永远先预览：

```bash
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault sync codex --dry-run
```

预期输出：

```text
INFO    profile: codex
INFO    source: /Users/YOU/.codex
OK      matched allowlist: ...
INFO    dry-run: no files copied, scanned, encrypted, committed, or pushed
```

如果看到 denied files，请停止并检查 profile 或本地数据。

## 6. 执行 Codex sync

```bash
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault sync codex
```

成功 sync 会：

- 把 allowlisted files 复制到 temporary staging
- 拦截 denied files
- 运行 `gitleaks`
- 创建 `tar.gz`
- 使用 `age` 加密
- 写入 `vault/*.age`
- 写入 `manifests/*.json`
- commit 并 push encrypted data 到 `aisync-vault`

## 7. 日常使用

```bash
cd ~/Developer/projects/aisync
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault pull
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault conflicts
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault sync codex --dry-run
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault sync codex
```

`conflicts` 在 sync 前应显示 `synced`、`ahead` 或 `no-upstream`。如果显示 `behind`，先运行 `pull`；如果显示 `diverged`、`dirty` 或 `fetch-failed`，请先检查 vault repository。

## 8. 检查 vault

```bash
cd ~/Developer/projects/aisync-vault
git status --short
find vault manifests -maxdepth 2 -type f | sort
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault history codex
```

Vault 应只包含 encrypted packages 和 manifests，不应包含：

```text
auth.json
.env
*.sqlite
id_rsa
id_ed25519
plaintext sessions outside encrypted packages
```

## 下一步

- 在另一台机器 restore 前先阅读 [Recovery](RECOVERY.zh-CN.md)。
- 常见安全问题见 [FAQ](FAQ.zh-CN.md)。
