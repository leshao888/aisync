# FAQ

简体中文 | [English](FAQ.md)

## Private GitHub repository 足够安全吗？

不够。Private repository 是 access control，不是 end-to-end encryption。AIsync 使用 `age`，让 Git repository 只保存 encrypted packages。

## 数据已经加密了，为什么还需要 `gitleaks`？

因为 chat history 可能包含 API keys、tokens、passwords 或 private keys。AIsync 会在 encryption 前扫描 plaintext staging data，让明显 secret 尽早中止 sync。

## AIsync 会 sync `auth.json` 吗？

不会。Codex profile 会 deny `auth.json`、sqlite databases、`.env`、token-like files、private keys、plugin caches 和其他 risky paths。

## 如果我曾经把 secret 粘贴进 chat 怎么办？

`gitleaks` 可能会发现它。如果发现，sync 会停止。你应该 rotate 这个 secret，并在 sync 前从本地数据中删除或 redact。

## Source repository 可以公开吗？

可以。`aisync` source repository 可以公开。Personal data 应放到单独的 private `aisync-vault` repository，并且只以 encrypted `.age` packages 形式保存。

## 可以多台机器共用一个 vault 吗？

可以，只要每台机器都能访问 Git repository，并且拥有可以 decrypt packages 的 age identity。

查看当前 recipients：

```bash
aisync --repo ~/Developer/projects/aisync-vault recipient list
```

添加另一个 recipient：

```bash
aisync --repo ~/Developer/projects/aisync-vault recipient add <age-recipient>
```

## 如果 age private key 丢了怎么办？

除非还有其他 recipient 可以 decrypt，否则你无法解密旧 vault packages。请单独备份 age private key。

## AIsync 可以 sync Claude Code 或 Cursor 吗？

Claude Code 已有 experimental sync-only profile。真实 sync 前请运行 `aisync profile show claude` 和 `aisync sync claude --dry-run`。由于 Claude Code data layout 和 restore behavior 尚未验证，restore 当前禁用。Cursor 和其他 profiles 仍在规划中。

## 多台机器可以同时 sync 吗？

建议 sync 前先运行 `aisync pull` 和 `aisync conflicts`，并避免同时写入。Automatic conflict merge 是未来功能。

## Restore 会覆盖我当前的 Codex data 吗？

默认 restore mode 是 `merge`。AIsync 写入前会创建 backup。请先使用 `restore --dry-run`。

## 为什么 restore 前要关闭 Codex？

如果 Codex 正在写入，restore 可能和 app writes 竞争并破坏 local state。AIsync 在 macOS/Linux 上检测到 Codex running 时会中止 restore。

## Logs 存在哪里？

Logs 存在 vault repository 的 `logs/` 下。Logs 不应包含 chat snippets、file contents、tokens 或 secrets。

## 如何查看之前的 sync packages？

使用：

```bash
aisync --repo ~/Developer/projects/aisync-vault history codex
```

## sync 前如何更新本地 vault？

使用：

```bash
aisync --repo ~/Developer/projects/aisync-vault pull
```

它会运行 `git pull --ff-only`，如果 vault 出现分叉会停止。

## 如何检查 vault 是否有 Git conflicts？

使用：

```bash
aisync --repo ~/Developer/projects/aisync-vault conflicts
```

安全状态是 `synced`、`ahead` 和 `no-upstream`。`behind`、`diverged`、`dirty` 或 `fetch-failed` 都需要先处理再 sync。
