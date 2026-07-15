# Recovery

简体中文 | [English](RECOVERY.md)

本指南说明如何从 AIsync vault 恢复 Codex data。

## Restore 前

Restore 比 sync 更危险，因为它会写入 app data directory。

执行真实 restore 前：

- 关闭 Codex
- 先运行 `restore --dry-run`
- 确认 active profile 是 `codex`
- 确认 vault repository 是正确的
- 确认这台机器有匹配的 age private key

## 新机器设置

Clone 两个 repositories：

```bash
mkdir -p ~/Developer/projects
cd ~/Developer/projects
git clone git@github.com:leshao888/aisync.git
git clone git@github.com:YOUR_USER/aisync-vault.git
```

安装依赖：

```bash
brew install age gitleaks
```

恢复或配置 age identity：

```bash
export AISYNC_AGE_IDENTITY="$HOME/.config/aisync/keys/identity.txt"
```

该 identity 必须匹配加密 vault package 时使用的某个 recipient。

## 检查准备状态

```bash
cd ~/Developer/projects/aisync
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault doctor
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault pull
```

如果 `doctor` 报告缺少 dependencies、recipients、Git remote 或 identity 问题，先修复这些问题。

## 预览 restore

```bash
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault restore codex --dry-run
```

Dry-run 会显示将恢复的 files。它不会创建 backup，也不会写入 `~/.codex`。

## 执行 restore

```bash
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault restore codex
```

默认 restore mode 是 `merge`：

- 尽量不覆盖 existing files
- 复制 missing files
- 写入前创建 backup directory

## Replace Files

只有在理解影响后才使用 `replace-file`：

```bash
PYTHONPATH=src python3 -m aisync --repo ~/Developer/projects/aisync-vault restore codex --mode replace-file
```

AIsync v0.1 不提供 destructive tree replacement。

## Backup Location

Backups 会创建在 vault repository 中：

```text
backups/codex/backup-YYYYMMDD-HHMMSS/
```

Backups 是 local runtime data，不应 commit。

## 常见 restore 失败

### Codex is running

关闭 Codex 后重新 restore。AIsync 在 macOS/Linux 上检测到匹配的 Codex process 时会中止 restore。

### age identity is missing

在本机恢复 private age identity，或设置：

```bash
export AISYNC_AGE_IDENTITY="/path/to/identity.txt"
```

### Manifest exists but archive is missing

运行：

```bash
cd ~/Developer/projects/aisync-vault
git pull --ff-only
```

然后重试 restore。

### Backup failed

不要强行 restore。先修复 permissions 或 disk space。Backup 失败时，AIsync 不应写入 target directory。
