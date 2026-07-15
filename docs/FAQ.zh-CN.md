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

## 如果 age private key 丢了怎么办？

除非还有其他 recipient 可以 decrypt，否则你无法解密旧 vault packages。请单独备份 age private key。

## AIsync 可以 sync Claude Code 或 Cursor 吗？

v0.1 还没有 stable profile。AIsync 架构是 profile-based，未来版本可以添加 Claude Code、Cursor、Gemini CLI 和其他本地 AI tools。

## 多台机器可以同时 sync 吗？

v0.1 没有完整自动化处理这个场景。建议 sync 前先 `git pull --ff-only`，并避免同时写入。Automatic conflict merge 是未来功能。

## Restore 会覆盖我当前的 Codex data 吗？

默认 restore mode 是 `merge`。AIsync 写入前会创建 backup。请先使用 `restore --dry-run`。

## 为什么 restore 前要关闭 Codex？

如果 Codex 正在写入，restore 可能和 app writes 竞争并破坏 local state。AIsync 在 macOS/Linux 上检测到 Codex running 时会中止 restore。

## Logs 存在哪里？

Logs 存在 vault repository 的 `logs/` 下。Logs 不应包含 chat snippets、file contents、tokens 或 secrets。

