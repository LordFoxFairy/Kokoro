# Claude Code 学习笔记 04 — 安全/权限 + 多端集成 + SDK

## 一句话概括

Claude Code 用「分层权限 + OS 级沙箱 + 多 surface 共享同一配置」做安全：tier 化的工具默认（read-only 不问、bash 要问、edit 要问），可切换的 permission mode 决定打扰频率，OS 级 sandbox（macOS Seatbelt / Linux bubblewrap）兜底，managed settings + devcontainer 给企业治理；CLI、VS Code 插件、JetBrains 插件、Desktop app、Web、Agent SDK 共用 `~/.claude/` 与项目 `.claude/`，是同一个产品在不同 surface 上的呈现。

---

## 抓到的 URL 清单 + 各自要点

| URL | 要点 |
|---|---|
| https://code.claude.com/docs/en/iam | 实际是 Authentication 页：Pro/Max/Team/Enterprise/Console/Bedrock/Vertex/Foundry 多种 auth 方式；credential 在 macOS Keychain / Linux 0600 文件；`apiKeyHelper` 自定义脚本；6 级 auth 优先级；`claude setup-token` 生成长效 OAuth token 给 CI |
| https://code.claude.com/docs/en/security | 安全总览：默认只读、bash/edit 要批准；built-in 防护包含沙箱化 bash、write 限定在 cwd、accept-edits 模式、prompt-fatigue 缓解；防 prompt injection：context-aware 分析、input sanitization、curl/wget blocklist、isolated context window 给 web fetch、trust verification、fail-closed matching |
| https://code.claude.com/docs/en/devcontainer | Dev container feature `ghcr.io/anthropics/devcontainer-features/claude-code:1.0`；用 named volume 持久化 `~/.claude`；managed-settings.json 放 `/etc/claude-code/`；`init-firewall.sh` 限制网络出口；非 root 用户下可用 `--dangerously-skip-permissions` |
| https://code.claude.com/docs/en/ide-integrations | 重定向至 vs-code 页：spark 图标、@-mention、permission mode 选择器、checkpoint、内置 IDE MCP server（端口 127.0.0.1 随机高端口 + 一次性 token 写入 0600 lock 文件）；只暴露两个 tool 给模型：`mcp__ide__getDiagnostics`、`mcp__ide__executeCode`（Jupyter cell 执行有 Quick Pick 确认） |
| https://code.claude.com/docs/en/jetbrains | IntelliJ/PyCharm/WebStorm/PhpStorm/GoLand 等；plugin 仅做 IDE 集成，Claude Code 本体仍是 CLI；功能：diff 在 IDE 查看、selection 自动共享（受 Read deny 规则限制）、diagnostic 共享 |
| https://code.claude.com/docs/en/permissions | 三类 tool tier（read-only/Bash/Edit）；三种规则 deny → ask → allow；`Bash(*)` `Read(./.env)` `WebFetch(domain:example.com)` `mcp__name__tool` `Agent(Name)`；compound command 按子命令逐个匹配；read 与 edit 规则按 gitignore 语义；managed settings 优先级最高；hooks 可扩展 |
| https://code.claude.com/docs/en/permission-modes | 6 种 mode：`default` / `acceptEdits` / `plan` / `auto`（research preview）/ `dontAsk` / `bypassPermissions`；Shift+Tab 循环；protected paths（`.git`/`.vscode`/`.idea`/`.husky`/`.claude` 等）即使 acceptEdits 也仍 prompt；`rm -rf /` 和 `rm -rf ~` 在 bypass 模式仍 prompt 作 circuit breaker |
| https://code.claude.com/docs/en/sandboxing | `/sandbox` 命令；macOS Seatbelt / Linux bubblewrap；filesystem isolation（默认 cwd 可写、整机可读）；network 通过 proxy 限定域名；auto-allow 模式让 sandboxed bash 免确认；OS 级 enforce 子进程也受限；`@anthropic-ai/sandbox-runtime` 开源 npm 包 |
| https://code.claude.com/docs/en/headless | `-p` / `--print` 非交互；`--output-format json|text|stream-json`；`--json-schema` 结构化输出；`--allowedTools`、`--permission-mode acceptEdits|dontAsk`；`--bare` 跳过 hook/skill/plugin/MCP/CLAUDE.md 自动发现，是脚本推荐模式；stdin 上限 10MB |
| https://code.claude.com/docs/en/cli-reference | 完整 flag 表：含 `--add-dir` `--bare` `--dangerously-skip-permissions` `--max-budget-usd` `--max-turns` `--permission-prompt-tool`（非交互时用 MCP tool 处理审批） `--tools` 限制可用工具 `--worktree` |
| https://code.claude.com/docs/en/agent-sdk/overview | Python `claude_agent_sdk` / TypeScript `@anthropic-ai/claude-agent-sdk`；核心入口 `query(prompt, options)` 异步迭代消息；内置 tools 与 CLI 一致；支持 hooks 回调（`PreToolUse` 等）、subagents（`AgentDefinition`）、MCP server、permission mode；TypeScript SDK 内含 native binary |
| https://code.claude.com/docs/en/desktop | Desktop app（macOS + Windows，无 Linux）；三个 tab：Chat / Cowork / Code；Code tab 是 pane-based 布局（chat/diff/preview/terminal/file/plan/tasks）；mode selector 同 CLI；computer use（控制屏幕）独立于 sandboxed bash；Remote session 跑在 Anthropic 云上；side chats、PR monitoring、Dispatch 从手机起任务 |
| https://code.claude.com/docs/en/claude-code-on-the-web | Web 版跑在 Anthropic 管理的隔离 VM；每 session fresh VM + repo clone；GitHub 走 proxy 服务，scoped credential，push 限定 working branch；audit logging；自动 cleanup；网络分 None / Trusted（默认 allowlist）/ Custom；setup script + filesystem snapshot 缓存 |

未抓到：iam（重定向到 authentication）、headless（实际位于 /headless，已抓）。

---

## 6 个问题逐条回答

### 1. 权限模型：用户怎么授权工具调用？

**Tier 化默认**（来自 `/permissions` 页）：
- Read-only（File read、Grep）：永不询问
- Bash commands：必须批准；批准后「yes don't ask again」对该 project dir + command 永久允许
- File modification（Edit/Write）：必须批准；批准后只对该 session 有效

**规则形式**：`Tool` 或 `Tool(specifier)`，写进 `.claude/settings.json` 的 `permissions.allow / ask / deny`。规则评估顺序 **deny → ask → allow**，先匹配先决。

**Permission modes 区别**（来自 permission-modes 页）：

| Mode | 不问就跑的范围 | 适合 |
|---|---|---|
| `default` | 只 read | 起步、敏感工作 |
| `acceptEdits` | read + file edits + `mkdir touch mv cp rm sed` 等在 cwd 内 | 改完用 git diff 复审 |
| `plan` | 只 read（不准编辑源文件） | 探索代码后再改 |
| `auto` | 所有动作，但有 classifier 后台审查 | 长任务、减少打扰 |
| `dontAsk` | 只允许 pre-approved tools；其他全 auto-deny | 锁定的 CI |
| `bypassPermissions` | 全跳 | 隔离容器/VM only |

> "`bypassPermissions` mode skips all permission prompts... Removals targeting the filesystem root or home directory, such as `rm -rf /` and `rm -rf ~`, still prompt as a circuit breaker against model error."

CLI 切换：`Shift+Tab` 循环；启动：`claude --permission-mode plan`；默认：settings 里 `defaultMode`。

**破坏性操作的二次确认**：
- `bypassPermissions` 模式下 root/sudo 拒启动；`rm -rf /` 和 `rm -rf ~` 仍 prompt
- 即使 `acceptEdits`，写 `.git` / `.vscode` / `.idea` / `.husky` / `.claude` 等 protected paths 仍 prompt
- Auto mode 的 classifier 默认 block：`curl | bash`、production deploy、mass cloud deletion、force push、push 到 main、unrecognized infra、把 sensitive data 发到外部 endpoint

### 2. 沙箱 / devcontainer

**Native sandbox**（sandboxing 页）：
- macOS：Seatbelt；Linux/WSL2：bubblewrap（WSL1 不支持）
- 通过 `/sandbox` 命令启用；OS 级 enforce，所有子进程都受限
- 默认：cwd 内可写、整机可读、网络只允许 allowlist 域名
- 走 proxy server 强制 hostname 校验（**不做 TLS inspection**，所以 broad 域名如 `github.com` 可能被 domain fronting）

> "The sandboxed bash tool uses OS-level primitives to enforce both filesystem and network isolation."

**Auto-allow sandbox mode**：sandboxed 命令免 prompt 直接跑，因为 OS 边界已经在那。explicit deny 仍生效；`rm` 打到 `/` 或 home 仍 prompt。

**Devcontainer**（devcontainer 页）：通过 `ghcr.io/anthropics/devcontainer-features/claude-code:1.0` feature 安装；推荐配合 `init-firewall.sh` 限制出网域名；只在容器里跑非 root 用户时才能用 `--dangerously-skip-permissions`。

> "When executed with `--dangerously-skip-permissions`, dev containers do not prevent a malicious project from exfiltrating anything accessible inside the container, including the Claude Code credentials stored in `~/.claude`."

### 3. IDE 集成：VS Code 插件长什么样？

- VS Code 扩展自带 native binary，从扩展 panel 或 `claude` 在 integrated terminal 启动；**共享同一 `~/.claude` 配置和 session 历史**（`claude --resume` 在 CLI 里能恢复扩展 session）
- 扩展跑一个 local MCP server（绑 127.0.0.1 随机端口、一次性 token、lock 文件 0600 权限），CLI 通过它打开原生 diff viewer、读 selection、执行 Jupyter cell
- 暴露给模型的只有两个 tool：`mcp__ide__getDiagnostics`、`mcp__ide__executeCode`；后者每次都强制 native Quick Pick 确认
- Permission mode 通过 prompt box 底部 mode 指示器切换
- Checkpoint（Rewind code / Fork conversation）是 VS Code 独有的优势

**JetBrains** 插件（jetbrains 页）：只做 IDE 集成（diff viewer、selection 共享、diagnostic 共享、`Cmd+Esc` 快捷键），Claude Code 本体仍是 CLI 跑在 IDE 的 integrated terminal 里。

### 4. Desktop vs Web vs CLI vs IDE 对照

**Desktop app**（仅 macOS + Windows，无 Linux）：
- 三个 tab（Chat/Cowork/Code）；Code tab 是 pane layout（chat/diff/preview/terminal/file/plan/tasks/subagent 任意拖拽）
- 独有：integrated terminal、computer use（控屏）、app preview、PR monitoring（CI status bar）、Dispatch 从手机起 session、远程 SSH session
- Permission mode 与 CLI 等价；Ask permissions、Auto accept edits、Plan、Auto、Bypass（`dontAsk` 只在 CLI 有）

**Web**（claude.ai/code）：
- 跑在 Anthropic 管理的 isolated VM；fresh VM per session
- GitHub 走 proxy + scoped credential，**push 限定 working branch**
- 全 audit logging；session 结束自动清理
- 网络 None / Trusted（默认 allowlist：npm/PyPI/RubyGems/crates.io）/ Custom
- 不支持 Ask permissions（自动 accept edits）、Auto、Bypass；只支持 Auto-accept edits + Plan mode
- Remote Control 模式：web UI 接到本地跑的 Claude Code 进程，代码执行仍本地

**CLI**：功能最全；唯一支持 `dontAsk` mode、`!` bash shortcut、tab 补全；全部 MCP 配置；checkpoint 也有

**IDE 插件**：VS Code 是 native graphical panel（自带 binary）；JetBrains 是 thin wrapper（仍跑 CLI）

### 5. SDK：开发者怎么以编程方式调用？

**两种入口**（agent-sdk/overview 页）：

```python
# Python: pip install claude-agent-sdk
from claude_agent_sdk import query, ClaudeAgentOptions
async for message in query(
    prompt="Find and fix the bug in auth.py",
    options=ClaudeAgentOptions(allowed_tools=["Read", "Edit", "Bash"]),
):
    print(message)
```

```typescript
// TS: npm install @anthropic-ai/claude-agent-sdk  （TS SDK 内含 native binary）
import { query } from "@anthropic-ai/claude-agent-sdk";
for await (const message of query({
  prompt: "Find and fix the bug in auth.ts",
  options: { allowedTools: ["Read", "Edit", "Bash"] }
})) { console.log(message); }
```

或者用 `claude -p "query"` 当 SDK CLI，加 `--bare` 跳过自动 discovery 拿到 CI 可复现行为。

**SDK vs Client SDK**：Client SDK 只给原始 API，tool loop 你自己写；Agent SDK 把 agent loop + tools + context 管理打包好。

**SDK vs Managed Agents**：Agent SDK 跑在你自己的进程/基础设施上；Managed Agents 是 REST API，sandbox 在 Anthropic 托管。

**关键能力**：hooks 用 callback 函数（`PreToolUse` 阻止/改写工具调用）、`AgentDefinition` 自定义 subagent、MCP server 注入、`permission_mode`、`--json-schema` 结构化输出、session resume。

**典型场景**：CI/CD、定时任务、自定义 wrapper、production automation；prototype 用 CLI 然后 SDK 化是常见路径。

### 6. 企业 / 团队

**Managed settings**（permissions 页 + devcontainer 页）：
- 文件位置：Linux/macOS 是 `/etc/claude-code/managed-settings.json`、Windows 是 HKLM 注册表或 `C:\Program Files\ClaudeCode\managed-settings.json`
- 优先级最高，user 和 project 都不能覆盖
- Managed-only keys：`allowManagedPermissionRulesOnly`（只让 managed 定义 allow/ask/deny）、`allowManagedHooksOnly`、`allowManagedMcpServersOnly`、`disableBypassPermissionsMode`、`disableAutoMode`、`blockedMarketplaces`、`strictKnownMarketplaces`、`forceRemoteSettingsRefresh`（fail-closed startup）

**Server-managed settings**：从 Claude.ai admin console 推下来，不靠仓库里的文件（仓库可以被改）

**OpenTelemetry monitoring** + `ConfigChange` hooks 审计 settings 变更

**Plan 限制**：Claude for Teams 和 Enterprise 提供 SSO、role-based permissions、合规 API、managed policy

---

## Surface 对照表

| Surface | 平台 | 强项 | 限制 |
|---|---|---|---|
| **CLI** (`claude`) | macOS/Linux/Windows | 功能最全；`dontAsk` mode、`!`、tab 补全、全部 MCP；脚本化 `-p --bare` | 终端 UI；没有原生 diff 查看（除非接 IDE） |
| **VS Code 扩展** | VS Code/Cursor/Windsurf/Kiro | Native panel、@-mention、原生 diff、checkpoint、auto-save、session history 含 remote tab、自带 binary | 命令子集（部分 `/` 命令 CLI-only）；无 `!` bash 快捷、无 tab 补全 |
| **JetBrains 插件** | IntelliJ/PyCharm/WebStorm/PhpStorm/GoLand | IDE diff viewer、selection 自动共享、diagnostic 共享、`Cmd+Esc` | 只是 wrapper，Claude Code 本体仍跑 CLI；功能 = CLI |
| **Desktop app (Code tab)** | macOS + Windows（**无 Linux**） | Pane layout、integrated terminal、computer use、app preview、PR monitoring、Dispatch 手机起任务、Remote SSH/cloud session、parallel sessions | 无 Linux；computer use 风险高（不在 sandbox） |
| **Web** (claude.ai/code) | 浏览器 | Isolated VM、audit log、push 限 branch、setup-script 缓存、与移动 app 联动、auto-cleanup | 不支持 Ask/Auto/Bypass mode；只有 acceptEdits + plan；Zero Data Retention 用户不可用；rate limit |
| **Agent SDK** (Py/TS) | 任意 | 完整 agent loop + tools；hooks/subagents/MCP 都有；JSON schema 输出；session resume；可嵌入自己应用 | 不能用 claude.ai login（必须 API key 或 OAuth token）；2026-06-15 起订阅计划 SDK 走独立 credit |

---

## Permission mode 对照表

| Mode | 自动允许范围 | 用户须做 | 何时用 |
|---|---|---|---|
| `default` | 仅 read-only bash + read 工具 | 每次 edit/bash 都 approve | 起步、敏感代码 |
| `plan` | 仅 read | 看完 plan 后选择「approve and 进入 X 模式」 | 探索后再编辑 |
| `acceptEdits` | read + edit + `mkdir/touch/mv/cp/rm/sed` 在 cwd 内（protected paths 仍 prompt） | bash/网络仍要 approve | 改完用 git diff 复审 |
| `auto` | 一切（但 classifier 后台审；3 次连续或 20 次总 block 后 fallback 到 prompt） | 仅审 classifier 拦下的；可在对话里说"don't push"立 boundary | 长任务、信任大方向 |
| `dontAsk` | 只 pre-approved tools（`permissions.allow`）+ read-only bash；其余 auto-deny | 提前在 settings 里把白名单写齐 | 锁死的 CI / 脚本 |
| `bypassPermissions` | 全部（除 `rm -rf /` 和 `rm -rf ~`，protected paths 也跳） | 必须在隔离环境；root 拒启动 | 容器、VM、devcontainer |

模式正交于 sandbox：sandbox 是 OS 级，permission 是 Claude Code 进程级，两层防御。

---

## 给 Kokoro 的具体启示

1. **Kokoro 必须有自己的 permission mode 切换器，至少 3 档**：`Ask`（每次 file/tool 操作都弹审批）/ `Accept edits`（只对文件改动免审，跑命令仍弹）/ `Plan`（让 Claude 描述要做什么但不实施）。不要做"一个开关全开"，按 Claude Code 经验那会让用户审批疲劳进而盲点。Kokoro 的 mode 切换放在 input box 底部，不要藏到 settings 里。

2. **危险操作的二次确认必须是 OS 级 + Model 级双层**：模型说"我要跑 `rm -rf`"时一律弹原生确认框，不能模型自己说"安全"就放行。参考 Claude Code 的 protected paths（`.git`/`.vscode`/`.idea` 等）和 circuit-breaker (`rm -rf /` 永远 prompt)。Kokoro 至少要：(a) 写入特殊目录前永远弹框；(b) shell 执行类操作必须 prompt 或走沙箱白名单；(c) "全自动模式"启动时强制要求 isolated environment。

3. **Canvas 区域应被视为 "protected path"**：用户在 Canvas 里手动编辑过的内容，模型再去覆盖时必须二次确认（类似 Claude Code 的"如果你在 diff view 里改过提案，模型会被告知不再认为文件等于原提案"）。这避免模型悄悄覆盖用户改动。

4. **不做独立 IDE 插件，先做 Web + headless API**：Claude Code 的 IDE 插件本质是壳子（JetBrains 完全是、VS Code 半是），核心还是 CLI/SDK。Kokoro 起步资源紧张的话：(a) Web app 是主形态；(b) 暴露一个 headless / SDK 入口给开发者（类似 `claude -p` + Python/TS SDK），让用户/团队能在 CI 里调；(c) IDE 集成放到 v2，先用 `vscode://` URI handler 这种轻量挂钩。

5. **企业治理用 server-side managed settings，不要靠仓库文件**：Claude Code 学到的教训是 `.claude/settings.json` 可以被 cloned repo 注入，所以 `defaultMode: "auto"` 在 project settings 里被忽略，必须 user-level 或 managed。Kokoro 如果做团队版，policy（哪些工具能用、哪些域名能访问、是否允许 bypass mode）必须 server 下发 + 用户端 fail-closed verify，否则 trust 会被恶意 repo 撬开。

6. **SDK 是粘性放大器，但是要做就做"完整 agent loop"而不是"thin API wrapper"**：Claude Code 的 Agent SDK 卖点是 tools + hooks + subagents + MCP + session 全打包，不是只把 LLM call 包一层。Kokoro 如果要做 SDK，至少要暴露：(a) tool execution loop；(b) PreToolUse/PostToolUse hook；(c) 结构化输出（JSON schema）；(d) session resume。否则用户会绕过 SDK 直接打你的 API，反而更难治理。

---

## 未抓到的 URL

- `https://code.claude.com/docs/en/iam` — 该 URL 存在但实际渲染的是 Authentication 页（不是 IAM/permissions），权限相关内容在 `/permissions` 页
- `https://code.claude.com/docs/en/headless-mode` — 该路径返回 404；实际 URL 是 `/headless`（已抓）
