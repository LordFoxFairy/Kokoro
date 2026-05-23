# Claude Code 的 agent 原语：subagents / plan mode / tools / MCP / parallel agents

## 一句话概括

> Claude Code 不是单 LLM 在回话，而是**一个主循环 + 一组可派工的 agent 原语**。主控始终是一个 Claude 会话，它通过 `Agent`、`Skill`、`Bash`、MCP server 这些**显式声明的工具**来调度其他能力；上下文隔离、权限收窄、并行派工都靠这些原语提供的"边界"实现，而不是靠 prompt 里写一句"请扮演 xxx"。

## 抓到的 URL 清单

| URL | 状态 | 要点 |
|---|---|---|
| https://code.claude.com/docs/en/sub-agents | OK | subagent 完整定义、frontmatter、scope、built-in、fork 模式、resume |
| https://code.claude.com/docs/en/mcp | OK | MCP 协议、三种 transport、scope 层级、tool search 延迟加载、托管/policy 配置 |
| https://code.claude.com/docs/en/tools | OK | 全量工具清单 + 每个工具的权限模型与行为细节（Agent / Bash / Edit / Monitor 等） |
| https://code.claude.com/docs/en/agent-sdk | OK | Agent SDK 概述、`query()` API、与 CLI / Client SDK / Managed Agents 对比 |
| https://code.claude.com/docs/en/permission-modes | OK | plan mode 本质是一种 permission mode；附 acceptEdits / auto / dontAsk / bypassPermissions |
| https://code.claude.com/docs/en/agent-view | OK | `claude agents` 全屏调度界面、background session、supervisor 进程模型 |
| https://code.claude.com/docs/en/agent-teams | OK | 实验性 teammate 协作（共享任务列表 + mailbox），与 subagent 的根本区别 |

未抓到（404）：

- https://code.claude.com/docs/en/plan-mode  → 实际不存在，plan mode 内容已并入 `permission-modes`
- https://code.claude.com/docs/en/parallel-agents → 实际不存在，并行能力分布在 `agent-view` / `agent-teams` / `sub-agents#fork` 三页

## 6 个问题逐条回答

### 1. Subagents：怎么定义？身份感来自什么？什么场景用？

**定义形态**：YAML frontmatter + Markdown 系统提示，存为 `.md` 文件。最小例：

```markdown
---
name: code-reviewer
description: Reviews code for quality and best practices
tools: Read, Glob, Grep
model: sonnet
---

You are a code reviewer. When invoked, analyze the code and provide
specific, actionable feedback on quality, security, and best practices.
```

也可以通过 `--agents '{...}'` CLI flag 或 `/agents` 交互界面创建。

**身份感的四根柱子**（文档原话："Each subagent runs in its own context window with a custom system prompt, specific tool access, and independent permissions."）：

1. **独立 context window**：完全隔离的会话历史，主控只看到最终一段 summary，看不到中间工具调用。
2. **自定义 system prompt**：frontmatter 下面那段 Markdown 就是它的全部 system prompt（不是主控 prompt 的衍生），加上 Claude Code 追加的环境信息。
3. **工具白名单 / 黑名单**：`tools` 字段 allowlist，或 `disallowedTools` denylist。两个都设时 deny 优先。
4. **可选独立模型 / permission mode / MCP server 集合**：`model: haiku|sonnet|opus|inherit`、`permissionMode: plan|acceptEdits|...`、`mcpServers: [...]`。

**Scope 五级优先级**：Managed > `--agents` CLI > `.claude/agents/` 项目 > `~/.claude/agents/` 用户 > 插件。

**典型场景**（来自文档）：

- 隔离会污染主上下文的高产出操作（跑测试、抓文档、读日志）
- 强制工具约束（"只读评审员"不许 Write/Edit）
- 跑廉价模型省钱（Haiku 干搜索）
- 并行做独立调研，主控负责汇总

**关键引用**："Claude uses each subagent's description to decide when to delegate tasks." —— 自动派工靠 `description` 字段的措辞质量；想"主动派工"就在 description 里写 `Use proactively`。

**关键约束**：**subagent 不能再 spawn subagent**（没有嵌套），要嵌套用 fork 或 chain。

### 2. Plan mode：是什么？为什么独立？

**本质**：plan mode 是 `permission-modes` 页面下的一个 mode，**不是独立功能**。它的定义是："Claude reads files, runs shell commands to explore, and writes a plan, but does not edit your source."

**进入方式**：

- 交互式：`Shift+Tab` 循环到 plan，状态栏显示
- 单次：prompt 前缀 `/plan`
- 启动：`claude --permission-mode plan`
- 项目默认：`.claude/settings.json` 写 `permissions.defaultMode: "plan"`

**退出方式**：

- 再按 `Shift+Tab` 离开但不批准
- Claude 写完 plan → 弹出审批面板，用户选 4 种之一：
  1. Approve and start in **auto mode**
  2. Approve and **accept edits**
  3. Approve and **review each edit manually**
  4. Keep planning with feedback

也就是**批准的同时切换到下一阶段的 permission mode**——plan mode 是个"前置阶段"，批准动作本身决定接下来怎么干活。

**plan 的展现形态**：Claude 写出一段文字 plan，按 `Ctrl+G` 可以在 `$EDITOR` 里直接改。

**为什么做成独立 mode 而不是 inline**：

- plan 期间任何 write/edit 工具都被禁，**研究阶段不会顺手改文件**
- 批准 plan 是个**显式的状态转换动作**，模型生成了 plan 但不允许偷偷越权
- 内置 `Plan` subagent 会被 plan mode 自动调用来做代码搜索，**研究上下文留在 subagent 里**，主控只拿到 plan 文本

### 3. Tools：清单 + 显式/隐式

**完整内置工具表**（来自 tools 页面）：

| 工具 | 权限 | 用户可见度 |
|---|---|---|
| `Agent` | No | 派工时显示新 subagent 行 |
| `AskUserQuestion` | No | 弹出选择题 |
| `Bash` | Yes | 每次执行前可能要批准 |
| `CronCreate/Delete/List` | No | 隐式 |
| `Edit` | Yes | 改文件需批准 |
| `EnterPlanMode` / `ExitPlanMode` | No / Yes | mode 切换 |
| `EnterWorktree` / `ExitWorktree` | No | 隐式 |
| `Glob` / `Grep` | No | 隐式 |
| `ListMcpResourcesTool` / `ReadMcpResourceTool` | No | 隐式 |
| `LSP` | No | 自动跑，错误自动报回 |
| `Monitor` | Yes（沿用 Bash 规则） | 后台脚本，事件回流 |
| `NotebookEdit` | Yes | 改 cell 需批准 |
| `PowerShell` | Yes | Windows 优先 |
| `PushNotification` | No | 隐式发桌面通知 |
| `Read` | No | 隐式 |
| `RemoteTrigger` | No | 调度 routine |
| `SendMessage` | No | 给 teammate 或 resume subagent |
| `Skill` | Yes | 主对话内跑技能 |
| `TaskCreate/Get/List/Update/Stop/Output` | No | 任务清单 |
| `TeamCreate/Delete` | No | 建/解散 agent team |
| `ToolSearch` | No | 延迟加载 MCP 工具 |
| `WaitForMcpServers` | No | 等 MCP 连接 |
| `WebFetch` | Yes | 首次访问域名要批准 |
| `WebSearch` | Yes | 全开/全关 |
| `Write` | Yes | 创建/覆盖文件 |

**用户可见度的关键设计**：所有"会改世界"的工具（Bash / Edit / Write / WebFetch / NotebookEdit / Skill / Monitor）**默认显式拦截**，每次调用走 permission 链——`allow` 规则、`ask` 规则、`deny` 规则、permission mode、protected paths。每个工具有规则格式 `ToolName(specifier)`：

```
Bash(npm run *)
Read(~/secrets/**)
Edit(/src/**)
Agent(Explore)
WebFetch(domain:example.com)
```

**隐式调用**：`Read / Glob / Grep / LSP / Agent` 不需要权限——它们不改世界，只读上下文或派 subagent（subagent 自己再走自己的权限）。

**重要的一条**："For the most part, Claude decides when to use these tools and you do not need to name them yourself when interacting with Claude." —— 工具名只在配置（permissions / hooks / 白名单）里才需要写。

### 4. MCP：协议、目的、典型集成、配置

**是什么**：Model Context Protocol，开源标准，让 Claude Code 连"外部工具/数据源"。文档原话："Connect a server when you find yourself copying data into chat from another tool, like an issue tracker or a monitoring dashboard."

**典型集成**（文档列出）：

- Sentry（`mcp.sentry.dev/mcp`）
- GitHub（`api.githubcopilot.com/mcp/`）
- Notion（`mcp.notion.com/mcp`）
- Asana（`mcp.asana.com/sse`，SSE 已弃用）
- Stripe / PayPal / HubSpot
- Slack / Figma / Gmail / Jira / Statsig
- PostgreSQL（via `@bytebase/dbhub`）
- Airtable / BigQuery
- Playwright（浏览器自动化）
- Filesystem / 自家 SaaS

**三种 transport**：

```bash
# HTTP（推荐远程）
claude mcp add --transport http notion https://mcp.notion.com/mcp

# SSE（已弃用）
claude mcp add --transport sse asana https://mcp.asana.com/sse

# stdio（本地进程）
claude mcp add --transport stdio --env AIRTABLE_API_KEY=KEY airtable \
  -- npx -y airtable-mcp-server
```

**Scope 三级**：

| Scope | 加载位置 | 共享 |
|---|---|---|
| local（默认） | 当前项目 | 否，存 `~/.claude.json` |
| project | 当前项目 | 是，存项目根 `.mcp.json`（入版本控制） |
| user | 全部项目 | 否 |

**与内置工具的关系**：MCP 工具在工具列表里和内置工具**并列**，命名形如 `mcp__servername__toolname`。MCP prompt 变成斜杠命令 `/mcp__github__pr_review 456`。MCP resource 可以 `@github:issue://123` 这样 @-mention。

**为什么需要它**：内置工具集合是固定的（Read/Edit/Bash/WebFetch/...），MCP 是**唯一的扩展点**让 Claude 看到自定义工具。Anthropic 自己说："To add custom tools, connect an MCP server."

**权限/审批**：

- project scope 的 `.mcp.json` 第一次启用要弹批准（防止恶意 PR 偷偷加 server）
- 远程 server 走 OAuth 2.0（401/403 自动触发 `/mcp` 走浏览器登录）
- `headersHelper` 支持非 OAuth 的自定义鉴权（Kerberos、SSO）
- managed `managed-mcp.json` 让 IT 锁定一组允许的 server

**Tool Search**（这是个有意思的扩展）：默认开启。MCP 工具不是 session 一开始就全部塞进 prompt，而是只塞名字，Claude 用 `ToolSearch` 工具按需加载 schema。这是**为了让你装 50 个 MCP server 也不会爆 context**。

### 5. Parallel agents：契约？

并行能力**分布在三种原语里**，对应不同的并行粒度：

#### 5a. Subagent 并行（最轻）

主控同一条消息里 spawn 多个 subagent（`Agent` 工具调用），它们各自跑在独立 context window，结束后**只有 final summary 回流**到主控。

```text
Research the authentication, database, and API modules in parallel using
separate subagents
```

**契约**：

- 不能再嵌套（subagent 不能 spawn subagent）
- 后台 subagent 自动 deny 会弹权限的工具调用（不会卡死）
- 前台 subagent 的权限提示走主控终端
- subagent 完成后 ID 留在主控，可用 `SendMessage` resume（要开 agent-teams 实验旗标）
- 返回结果**会消耗主控 context**，所以"多 subagent 各返回大段结果"反而费上下文

#### 5b. Fork（实验，`CLAUDE_CODE_FORK_SUBAGENT=1`）

Fork = **继承全部主对话 + 跑在后台**的特殊 subagent。用来"从同一个起点跑几种方案":

```text
/fork draft unit tests for the parser changes so far
```

复用主对话 prompt cache → 便宜。fork 不能再 fork。

#### 5c. Background agents / agent view（`claude agents`）

这是**会话级别的并行**，不是 subagent。`claude agents` 打开全屏调度台：

```
Pinned       ✽ clawd walk cycle          Write assets/sprites/...   3m
Needs input  ✻ power-up design           needs input: double jump?  1m
Working      ✽ collision detection       Edit src/physics/...       2m
Completed    ✻ title screen              result: menu, options...   9m
```

- 每行 = 一个**完整的 Claude Code 会话**，由 supervisor 进程托管
- session 跑在自动建的 git worktree（`.claude/worktrees/<id>`）里，**避免互改同文件**
- 用户用 `Space` peek、`Enter` 附身、`←` 后台化、`Ctrl+X` 停
- 支持 `claude --bg "task"` 从 shell 派一个后台 session

**收回结果的契约**：每个 session 独立开 PR，UI 用 ●（黄/绿/紫/灰）显示 PR 状态。本质上用 **PR / worktree / 文件系统**作为 join 点，而不是消息回流。

#### 5d. Agent teams（实验，`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`）

这是**最强的并行模型**：lead + teammates，共享 task list + mailbox。

```text
Create an agent team to review PR #142. Spawn three reviewers:
- One focused on security implications
- One checking performance impact
- One validating test coverage
```

与 subagent 的根本区别（文档原图）：

|  | Subagents | Agent teams |
|---|---|---|
| 通信 | 只能 report 回主控 | teammate 之间**直接发消息** |
| 协调 | 主控管所有 | 共享 task list，自取任务 |
| Context | 完成后 summary 回流 | 各自独立，不汇总 |
| Token | 低 | 高（每人一个完整 Claude） |

任务用文件锁防抢占。lead 可以要求 teammate 走 plan mode → 提交 plan → lead 审批后才开工。

### 6. Agent-to-agent vs main-agent-to-subagent：层级关系

总图：

```
                        User
                          ↓
                    Main agent (always Claude)
        ┌─────────────────┼─────────────────┐
        │                 │                 │
   Skill 调用       Subagent (Agent 工具)   Background session (supervisor)
        │                 │                 │
        │           ┌─────┴─────┐           ↓
        │           │           │      另一个 Main agent
        │      Fork (继承)  Named (新开)  (完整 Claude Code，
        │           │           │       自己也能开 subagent)
        │           └─────┬─────┘
        │                 │
        │           （不能再嵌套）
        │
   Agent team（lead + teammates）
   teammate <—mailbox—> teammate
   shared task list
```

关键层级规则：

1. **主控永远是一个 Claude 会话**——不能"提升 teammate 为 lead"。
2. **subagent 单层**：subagent 不能 spawn subagent；要嵌套用 chain（让主控顺序派）或 fork 或 skill。
3. **background session 是平级**：每个都是完整 Claude Code，**它们自己能开 subagent**——所以 supervisor 看到的是一棵浅树（agent view → 多个独立 Claude → 各自 subagent）。
4. **agent team 是带通信的平级**：teammate 之间直接消息（不必经过 lead），但**teammate 不能再开 team**（无嵌套 team）。
5. **Skill ≠ subagent**：Skill 跑在主对话上下文里（除非 `context: fork`），subagent 跑在隔离 context 里。

## 原语对照表

| 原语 | 作用域 | 用户可见度 | 主要解决什么 | Context 隔离 | 并发 |
|---|---|---|---|---|---|
| **Tool**（Read/Edit/Bash/…） | 单次工具调用 | 显式（敏感工具）/ 隐式（只读） | 让 LLM 改世界，权限可拦 | 无 | 单条线程内串行 |
| **MCP server** | session 全程 | 工具列表里出现 `mcp__name__tool` | 把"任何外部系统"包装成工具 | 无（共享主上下文）；可 scope 给 subagent | 多 server 可同时存在 |
| **Skill** | 主对话内 | 显式 `Skill(name)` 权限 | 复用 prompt-级工作流 | 默认不隔离，可 `context: fork` | 单次串行 |
| **Plan mode** | 一段对话 | 显式（状态栏 + 审批面板） | 研究/编辑分阶段 | 用内置 Plan subagent 隔离搜索噪声 | N/A |
| **Subagent**（named） | 单次任务 | 显式（任务列表里一行） | 上下文隔离 + 工具约束 + 模型选型 | 完全隔离，新 system prompt | 主控同回合可并发多个，不嵌套 |
| **Fork subagent** | 单次任务 | 显式（panel） | 同起点多方案 / 不污染主上下文 | 继承主对话历史 | 后台并发，不能再 fork |
| **Background session**（agent view） | 跨会话 | 显式（全屏调度台） | 长任务 + 多任务调度 + PR 拉回 | 完整独立 Claude，自带 worktree | 受订阅配额限制的真并发 |
| **Agent team**（teammate） | 跨会话 + 协作 | 显式（panel/tmux 分屏） | 多人协作、互相 challenge | 各自独立 context，通过 mailbox + task list 协调 | 一个 lead 管 N 个 teammate |
| **Hook** | 工具调用前后 | 隐式 | 验证/拦截/审计/转换 | 跑在你机器上的脚本 | N/A |

## 给 Kokoro 的具体启示（4-6 条）

### 启示 1：plan mode 不是"花活"，是"研究 / 编辑分阶段"的产品语言

Claude Code 把 plan mode 做成**独立 permission mode + 强制审批闸门**，背后的产品判断是：**"AI 想好怎么改"和"AI 真的去改"必须是用户看得见的两个动作**。

Kokoro 是 Gemini 风格 Canvas，类似"plan→execute"的场景天然存在：

- 用户说"帮我重写这段文档"——LLM 应该先给大纲，等用户点 confirm 才动 Canvas
- 用户说"重构这段代码"——先给方案，再动文件

**建议**：Kokoro 的 Canvas 应该原生支持一种 **"草稿层"模式**——LLM 给出 plan/diff，**不立即落到 Canvas 主文档**，用户有审批面板（接受 / 改方案 / 手动逐处接受 / 让 LLM 继续探索）。Claude Code 的 4 选项审批面板是个抄作业的好对象。

### 启示 2：subagent 不要做太早；先做"工具白名单 + 模型路由"

Claude Code 的 subagent 是个工程上很重的原语（独立 context、独立 system prompt、独立工具、独立模型、独立 memory、可选独立 MCP）。**但 80% 的好处其实来自两件事**：

1. **工具白名单**：让一个对话只能用 Read/Grep（不许写），这是廉价的安全边界
2. **模型路由**：搜索/汇总走 Haiku，决策走 Opus，省钱不卡顿

**建议**：Kokoro 不要直接抄 subagent 的全套机制。**先内化两件事**：

- 工具调用有 allowlist（用户能看到/管理）
- 任务自动按"重任务/轻任务"路由到不同模型

只有当用户反馈"我希望让 AI 专门负责审稿/翻译/写代码，且互不污染"时，再上 subagent 那套独立 context 的设计。

### 启示 3：MCP 是"工具生态"叙事的基石——但是个**长期**承诺，不是 v1 该做的

MCP 的真正价值不是"我能接 GitHub"，而是**"Kokoro 是开放协议，不是封闭工具集"**。Anthropic 抢先把 MCP 立成事实标准，OpenAI 后跟，所以新接入的所有 SaaS 都会有 MCP server。

**判断 Kokoro 要不要做**：

- 短期（v1 v2）：**不做** MCP，自带 Web 搜索 + 文件 + Canvas 编辑就够。每多一个工具系统都是文档+UI+权限+错误处理的成本。
- 中期（有 prosumer 用户开始问"能不能接我自己的 X"）：**接 MCP**，不要自造协议。直接接 `@modelcontextprotocol/sdk`，让 Kokoro 成为 MCP 客户端。
- 重点：MCP 接入要有**权限审批 UI**（Claude Code 的 project-scope 第一次启用要批准是个好默认）和**输出大小限制**（默认 25k token，可配）。

### 启示 4：并行 agent 的产品形态决定了"AI 是助手还是同事"

Claude Code 的 `agent view`（`claude agents`）是个**根本性的产品形态选择**：

- 单 session：AI 是"工具"——你打开它，问它，关掉它
- agent view：AI 是"协作者"——你派给它任务，它在后台跑，你回来收

**建议 Kokoro 不要急着做 agent view，但要在数据模型上为它留口**：

- 会话不要绑死到当前 tab——后端要支持"detached session"概念
- Canvas 要支持多版本/分支（agent view 本质上是 git worktree + 多 session）
- 收回路径用"产物"而不是"消息"——AI 跑完产出一个新版本 Canvas / 一个 diff，用户回头评审

如果 Kokoro 想差异化于 ChatGPT，**这是最有戏的方向**。但成本巨大（要做调度器、状态机、产物比较 UI）。建议先做 **demo 级别**：用户能 fork 当前对话开第二条线，两条线并行跑，结果回流 Canvas。

### 启示 5：Hook 机制比 subagent 更早值得做

Claude Code 的 hook（`PreToolUse` / `PostToolUse` / `Stop` / `SessionStart` 等）是**给开发者塞自定义逻辑的口子**，比 subagent 轻得多但同样关键。

Kokoro 哪怕只支持 4 种 hook：

- `BeforeCanvasEdit`：用户/扩展能拦截、改写、拒绝 LLM 对 Canvas 的修改
- `AfterCanvasEdit`：跑 linter、format、自动保存
- `BeforeToolCall`：审批/审计
- `OnSessionStart`：注入项目上下文

这就足以让 prosumer / 团队用户做出 Kokoro 没原生支持的工作流。**比 subagent 早做 hook**。

### 启示 6：「身份感」从 4 件事来，prompt 只是其中一件

Claude Code 的 subagent 身份来自：**独立 system prompt + 工具白名单 + 模型选型 + 上下文隔离**。

Kokoro 现在多半只能做到第一项（不同对话/不同 system prompt）。**真要做"AI 分工"，剩下三项不能省**：

- 没有工具白名单 → "翻译助手"也能改文件
- 没有模型选型 → 所有助手都跑同一个贵模型
- 没有上下文隔离 → "审稿助手"看到了用户和其他助手的全部历史

**建议**：当 Kokoro 决定做"多角色/多助手"时，**4 件套一起上**，不要只做"换个 system prompt"假装有了分工。这是 Claude Code 文档里非常明确的设计纪律。

## 未抓到的 URL 清单

- `https://code.claude.com/docs/en/plan-mode` —— **404，不存在**。plan mode 内容并入 `permission-modes`。
- `https://code.claude.com/docs/en/parallel-agents` —— **404，不存在**。并行能力分布在 `sub-agents`（基础并行 + fork）、`agent-view`（background session）、`agent-teams`（teammate 协作）三页。
- `https://code.claude.com/docs/en/agents`（agents overview） —— 文档反复引用为"Run agents in parallel"对比页，未抓取。如果后续要深挖"原语对比"的官方说法，应补抓。
- `https://code.claude.com/docs/en/context-window` —— subagent 页面提到"context window visualization"在这里，未抓取（不属于本主题）。
