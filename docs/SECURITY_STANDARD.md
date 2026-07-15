# Security Standard

## Security Model

AIsync assumes local app data can contain:

- API keys
- access tokens
- OAuth sessions
- cookies
- passwords
- private chat content
- private project paths
- customer or company data
- SSH private keys pasted into chats

Therefore the tool must treat plaintext staging data as sensitive.

## Required Defaults

- Remote storage must be encrypted by default.
- Secret scanning must run before encryption.
- Deny rules must run before encryption.
- Restore must create a backup before writing.
- Restore should stop if the target app appears to be running.
- Dry-run must be available for sync and restore.
- Logs must be privacy-safe.

## Fatal Conditions

The operation must stop on:

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

Profiles should deny:

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

Logs may contain:

- timestamps
- profile name
- operation status
- file count
- byte count
- package name
- error code
- high-level path names

Logs must not contain:

- file contents
- chat snippets
- tokens
- cookies
- API keys
- private key material
- full secret scanner matches

## Key Management

MVP may store age private keys in a local config path, but must warn clearly.

Preferred future storage:

- macOS Keychain
- Linux Secret Service
- Windows Credential Manager

The sync repository must never include private keys.

## GitHub Private Repository Warning

A private Git repository is access control, not end-to-end encryption. AIsync should only rely on Git as transport/storage. Confidentiality should come from age encryption.
