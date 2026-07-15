# AIsync 项目规范

简体中文 | [English](AGENTS.md)

本文件是 `AGENTS.md` 的简体中文翻译，方便人工阅读。Codex 的规范源以 `AGENTS.md` 为准。

## 项目使命

AIsync 是一个本地 AI app 数据安全同步工具。它帮助用户在多台机器之间同步 Codex、Claude Code、Cursor 等 AI developer app 的选定本地数据，而不依赖同一个产品账号。

工具必须隐私优先。不能把 private Git repository 当作足够的安全保护。预期存储模型是：

1. 只从每个 app profile 收集 allowlist 文件。
2. 打包前拦截 denied 文件。
3. 对 plaintext staging 数据进行 secret 扫描。
4. 使用 `age` 加密 package。
5. 只把 encrypted vault 文件和 non-sensitive manifest 提交到 Git。

## 当前阶段

本 repository 处于 `v0.2` alpha 开发阶段。用户已经明确批准从规划进入实现。

当前允许：

- Python CLI 实现和 alpha 迭代
- Codex profile 实现
- 本地 fake-data 测试
- 文档更新
- 安全检查和 restore 逻辑

除非用户明确要求，否则避免：

- 触碰真实 Codex 或 Claude 数据
- 对 `~/.codex` 执行真实 sync 或 restore
- 创建或 push 远程 GitHub repository
- 弱化 encryption、scanning 或 denied-file 行为

## 强制安全规则

- 默认 allowlist collection。永远不要 sync 整个 app directory。
- 默认 encryption。正常 workflow 不支持 plaintext remote sync。
- 默认 secret scanning。如果 scanning 不能运行，sync 必须停止，除非用户显式选择有文档说明的不安全模式。
- Denied files 是 fatal。发现 auth files、token files、private keys、sqlite databases、cookies 或 `.env` 必须停止操作。
- Restore 写入 app directory 前必须创建 backup。
- Restore 必须支持 dry-run preview。
- 工具不得把 age private keys、GitHub tokens、app auth files、cookies 或 API keys 存进 sync repository。
- Logs 不得包含 file contents、chat snippets、tokens 或 secrets。
- App profiles 必须 versioned 并通过 schema validation。
- Cross-platform paths 必须通过 platform layer 解析，不得写死在 core sync logic。

## 产品原则

- 让安全路径成为默认路径。
- 每个危险状态都要说明原因和下一步动作。
- 用户应当能从 command output 判断是否成功，不需要读 logs。
- Profiles 应该容易添加，但很难写得不安全。
- Core 应当 app-agnostic。Codex 是第一个 profile，不是写死在 engine 里的特殊逻辑。

## 必需开发工作流

用户给出开发需求时，除非用户明确要求只做规划，否则要端到端处理。

默认 workflow：

1. 编辑前阅读相关代码和 project guidance。
2. 明确窄范围 implementation scope。
3. 实现改动。
4. 为 normal paths、failure paths 和 security boundaries 添加或更新 tests。
5. 运行完整 local verification suite。
6. 修复失败，直到所有 required tests 通过。
7. 当 commands、behavior、safety rules 或 workflows 变化时，更新用户文档。
8. 测试通过后再 commit。
9. 使用中文 commit message。
10. 在 network/auth 可用时，使用 `gh` 处理 GitHub repository 和 pull request 操作。

不要提交 failing tests。涉及 sync、restore、encryption、secret scanning、Git、path handling 或 profile behavior 时，不要跳过 boundary tests。

每次 commit 前必跑：

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPYCACHEPREFIX=$(mktemp -d) python3 -m compileall -q src tests
```

这些区域变化时要增加 targeted tests：

- denied-file rules
- secret scanning
- age encryption/decryption
- Git remote behavior
- restore backup behavior
- symlink handling
- archive extraction
- cross-platform path resolution

## Commit 和 GitHub 规则

Commit messages 必须使用中文，建议格式：

```text
功能: 添加 Codex 同步预览
修复: 修复恢复备份失败时未中止的问题
文档: 添加简体中文 README
测试: 增加危险文件边界测试
安全: 增加私钥文件拦截规则
重构: 拆分 profile 校验逻辑
构建: 添加 GitHub Actions CI
```

非平凡改动优先使用 feature branch 和 pull request：

```bash
git checkout -b feature/short-topic
git add .
git commit -m "功能: 添加 xxx"
git push -u origin feature/short-topic
gh pr create --title "功能: 添加 xxx" --body "..."
```

用户要求快速更新时，小型 documentation-only changes 可以直接 commit 到 `main`。

## Planned CLI Surface

Initial commands：

```bash
aisync init
aisync doctor
aisync profile list
aisync profile show codex
aisync profile validate codex
aisync sync codex --dry-run
aisync sync codex
aisync restore codex --dry-run
aisync restore codex
aisync status
aisync logs
aisync key list
aisync recipient list
aisync recipient add <age-recipient>
aisync recipient remove <age-recipient>
aisync history codex
```

Later commands：

```bash
aisync keygen
aisync key list
aisync recipient add
aisync recipient remove
aisync history codex
aisync pull
aisync unlock --stale
```

## Output Levels

所有 user-facing output 使用这些 levels：

- `INFO`: normal progress
- `OK`: successful step
- `WARN`: can continue, but user should notice
- `DANGER`: leak、overwrite、deletion 或 credential risk；默认停止
- `ERROR`: operation failure
- `NEXT`: concrete next command or action

## MVP 定义

`v0.1` 应当为 macOS 上的 Codex 提供完整安全 sync loop：

- `doctor`
- profile validation
- `sync --dry-run`
- allowlist collection
- deny guard
- gitleaks scanning
- age encryption
- Git commit and push
- `restore --dry-run`
- restore with backup
- state file
- privacy-safe logs

Codex flow 足够稳定前，不要扩展到太多 app。

当前已经实现的 commands：

```bash
aisync init
aisync doctor
aisync pull
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

## References

Project planning documents 位于 `docs/`。

- `docs/ARCHITECTURE.md`
- `docs/ROADMAP.md`
- `docs/SECURITY_STANDARD.md`
- `docs/PREPARATION.md`
- `docs/PROFILE_SPEC.md`
- `docs/WORKFLOW.md`
- `docs/TESTING.md`
- `CONTRIBUTING.md`
