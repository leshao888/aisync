# Security Standard

简体中文 | [English](SECURITY_STANDARD.md)

## Security Model

AIsync 假设 local app data 可能包含：

- API keys
- access tokens
- OAuth sessions
- cookies
- passwords
- private chat content
- private project paths
- customer or company data
- SSH private keys pasted into chats

因此，工具必须把 plaintext staging data 当作 sensitive data。

## Required Defaults

- Remote storage 默认必须 encrypted。
- Encryption 前必须运行 secret scanning。
- Encryption 前必须运行 deny rules。
- Restore 写入前必须创建 backup。
- Restore 发现 target app 似乎仍在运行时应当停止。
- Sync 和 restore 必须支持 dry-run。
- Logs 必须 privacy-safe。

## Fatal Conditions

以下情况必须停止操作：

- denied file found
- gitleaks finding
- missing age recipient
- age encryption failure
- decrypt failure
- backup failure before restore
- git remote missing during push
- git push failure
- concurrent lock held by another running operation
- symlink escaping the source root
- target app appears to be running during restore

## Denied File Classes

Profiles 应当 deny：

```text
auth files
OAuth/session files
cookies
sqlite databases
environment files
SSH private keys
credential files
token files
temporary app caches
plugin caches unless explicitly allowlisted
```

## Logging Rules

Logs 可以包含：

- timestamps
- profile name
- operation status
- file count
- byte count
- package name
- error code
- high-level path names

Logs 不得包含：

- file contents
- chat snippets
- tokens
- cookies
- API keys
- private key material
- full secret scanner matches

## Key Management

MVP 可以把 age private keys 存在 local config path，但必须给出清晰 warning。

未来优先 storage：

- macOS Keychain
- Linux Secret Service
- Windows Credential Manager

Sync repository 永远不得包含 private keys。

## GitHub Private Repository Warning

Private Git repository 是 access control，不是 end-to-end encryption。AIsync 只应把 Git 当作 transport/storage。Confidentiality 应来自 age encryption。

