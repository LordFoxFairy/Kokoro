# 02 — Claude Code 的可扩展性机制

> 一句话：**Claude Code 的扩展哲学是"markdown 即配置"——把行为定义降到一个带 YAML frontmatter 的文本文件，让用户、项目和组织在同一套语法下分别拥有自己的扩展层。**

研究范围：slash commands / hooks / skills / output styles / settings / permissions。

---

## 0. 抓取的 URL 清单

| URL | 状态 | 要点 |
|---|---|---|
| `code.claude.com/docs/en/slash-commands` | 200，但**重定向到 skills 页**。"Custom commands have been merged into skills." `.claude/commands/*.md` 仍兼容但已是 legacy 形态 |
| `code.claude.com/docs/en/hooks` | 200，hooks reference。**31 个事件**，5 种处理器类型（command / http / mcp_tool / prompt / agent），完整 stdin/stdout JSON 契约 |
| `code.claude.com/docs/en/hooks-guide` | 200，hooks tutorial（输出过大已落盘） |
| `code.claude.com/docs/en/skills` | 200，主入口。`SKILL.md` + frontmatter + 目录形态，描述什么时候被加载 |
| `code.claude.com/docs/en/output-styles` | 200，**修改 system prompt**，built-in 有 Default / Proactive / Explanatory / Learning |
| `code.claude.com/docs/en/settings` | 200，**5 层 precedence**：Managed → CLI → Local → Project → User |
| `code.claude.com/docs/en/iam` | 200，是 authentication 页面（不是权限模型） |
| `code.claude.com/docs/en/permissions` | 200，**权限模型本体**。allow/ask/deny 三态，gitignore 风格 path matching，deny-first |
| `code.claude.com/docs/en/commands` | 200，全部 built-in 命令和 bundled skills 清单（输出过大已落盘） |

未抓到：无（hooks-guide / commands 落盘了完整文本但摘要够用，不重抓）。

---

## 1. Slash Commands

### 定义方式

Claude Code 在最近一次大改之后**把 custom slash commands 合并进了 skills**。这是关键变化：

- 老形态 `.claude/commands/<name>.md` —— 仍然能用，但被视作 legacy。
- 新形态 `.claude/skills/<name>/SKILL.md` —— 推荐，因为支持目录、附带文件、自动触发。

两者在同一个 `/<name>` 调用入口下统一，**skill 优先于同名 command**。

### 三种来源

| 来源 | 触发 | 例子 |
|---|---|---|
| **Built-in** | Claude Code 内置的固定逻辑 | `/help`, `/clear`, `/compact`, `/config`, `/model`, `/permissions`, `/hooks`, `/skills`, `/agents`, `/plugin`, `/init`, `/review` |
| **Bundled skills** | Anthropic 预装的 prompt-based skill | `/simplify`, `/batch`, `/debug`, `/loop`, `/claude-api`, `/run`, `/verify` |
| **User-defined skills/commands** | 用户在 `~/.claude/skills/` 或 `.claude/skills/` 写的 markdown | 你自己的 `/deploy`, `/commit` 等 |

### 最短示例

```yaml
---
description: Summarize uncommitted changes and flag risky ones
---

## Current changes

!`git diff HEAD`

## Instructions

Give 2-3 bullets summarizing the diff and list any risks.
```

放到 `.claude/skills/summarize-changes/SKILL.md`，输入 `/summarize-changes` 即可调用。`` !`git diff HEAD` `` 是 **dynamic context injection**：命令在文本送给 Claude 之前先执行，输出原地替换。

### 参数

```yaml
---
arguments: [issue, branch]
---
Fix issue $issue on branch $branch.
```

支持 `$ARGUMENTS`（全部）、`$ARGUMENTS[N]` / `$N`（位置）、`$name`（命名）三种占位符。

---

## 2. Hooks

### 哲学

> "Hooks are user-defined shell commands that execute at specific points in Claude Code's lifecycle. They provide deterministic control over Claude Code's behavior, ensuring certain actions always happen rather than relying on the LLM to choose to run them."

—— 与 skills 互补：**skills 是"建议 Claude 做什么"，hooks 是"强制发生什么"**。

### 31 个 hook 事件

按生命周期分组：

- **Session**：`SessionStart`, `Setup`, `SessionEnd`
- **Per-turn**：`UserPromptSubmit`, `UserPromptExpansion`, `Stop`, `StopFailure`
- **Tool loop**：`PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `PostToolBatch`, `PermissionRequest`, `PermissionDenied`
- **Subagent/Task**：`SubagentStart`, `SubagentStop`, `TeammateIdle`, `TaskCreated`, `TaskCompleted`
- **Context/Config**：`InstructionsLoaded`, `ConfigChange`, `CwdChanged`, `FileChanged`
- **Worktree**：`WorktreeCreate`, `WorktreeRemove`
- **Compaction**：`PreCompact`, `PostCompact`
- **MCP**：`Elicitation`, `ElicitationResult`
- **通知**：`Notification`

### 5 种处理器类型

| type | 怎么响应 |
|---|---|
| `command` | shell 命令，stdin 收 JSON，stdout/exit code 返回决策 |
| `http` | POST 到 URL，body 是相同的 JSON |
| `mcp_tool` | 调连接的 MCP 服务器的 tool |
| `prompt` | 单轮 LLM 评估 |
| `agent` | spawn subagent 做验证 |

### 输入输出契约

**输入（stdin JSON，所有事件通用字段）**：

```json
{
  "session_id": "abc123",
  "transcript_path": "/path/to/transcript.jsonl",
  "cwd": "/current/working/directory",
  "permission_mode": "default|plan|acceptEdits|auto|dontAsk|bypassPermissions",
  "hook_event_name": "EVENT_NAME"
}
```

**Exit codes**：
- `0` = 成功，stdout 可能含决策 JSON
- `2` = 阻塞错误，stderr 发给 Claude
- 其他 = 非阻塞错误

**JSON output（exit 0 时可选）**：

```json
{
  "continue": true,
  "suppressOutput": false,
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow|deny|ask",
    "permissionDecisionReason": "..."
  }
}
```

### 最短示例：阻挡 `rm -rf`

`.claude/settings.json`：

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{ "type": "command", "command": "./hooks/block-rm.sh" }]
    }]
  }
}
```

`./hooks/block-rm.sh`：

```bash
#!/bin/bash
CMD=$(jq -r '.tool_input.command')
if echo "$CMD" | grep -q 'rm -rf'; then
  jq -n '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"deny",permissionDecisionReason:"blocked"}}'
fi
exit 0
```

### 典型用途

- 阻挡危险命令（PreToolUse / Bash）
- 启动时注入项目状态（SessionStart）
- 编辑后 lint（PostToolUse / Edit|Write）
- 在用户 prompt 里发现密码就 block（UserPromptSubmit）
- 推送外部审计（HTTP hook 到企业日志服务）

### Matcher 语法

- `"*"` 或省略 = 全匹配
- 只含字母数字下划线和 `|` = 精确字符串或竖线分隔的列表
- 其他字符 = JS regex

事件特有 matcher：`PreToolUse` 匹配 tool 名，`SessionStart` 匹配 `startup|resume|clear|compact`，等等。

---

## 3. Skills

### 是什么

带 YAML frontmatter 的 markdown 文件 `SKILL.md`，放进一个目录就是一个 skill。Claude 启动时把所有 skill 的 **description** 加载进 context（不是全文），用户或 Claude 触发时再把完整内容注入。

> "Claude Code skills follow the **Agent Skills** open standard (agentskills.io)，which works across multiple AI tools."

这是**跨工具的开放标准**。Claude Code 在标准之上加了 invocation control / subagent execution / dynamic context injection。

### Anatomy

```
my-skill/
├── SKILL.md           # 必需，主入口
├── reference.md       # 可选，详细 API 文档（按需加载）
├── examples/sample.md # 可选，示例
└── scripts/           # 可选，Claude 可执行的脚本
    └── helper.py
```

`SKILL.md` 应保持在 500 行以内，详细参考材料拆到附属文件。

### 最短 `SKILL.md`

```yaml
---
name: api-conventions
description: API design patterns for this codebase
---

When writing API endpoints:
- Use RESTful naming conventions
- Return consistent error formats
- Include request validation
```

### Frontmatter 字段（精选）

| 字段 | 作用 |
|---|---|
| `name` | 显示名，默认目录名 |
| `description` | **关键**，Claude 用这个判断要不要加载 |
| `when_to_use` | 补充触发短语 |
| `disable-model-invocation` | true = 只能用户手动 `/name` 调用 |
| `user-invocable` | false = 隐藏在 `/` 菜单（只有 Claude 能用） |
| `allowed-tools` | 该 skill 激活时免审批的工具列表 |
| `model` / `effort` | 临时覆盖模型/思考深度 |
| `context: fork` + `agent` | 在 forked subagent 里跑 |
| `hooks` | 该 skill 生命周期内的局部 hooks |
| `paths` | glob 模式限定何时自动加载 |

### 触发方式

| 模式 | 用户能调 | Claude 能调 |
|---|---|---|
| 默认 | ✅ | ✅ |
| `disable-model-invocation: true` | ✅ | ❌ |
| `user-invocable: false` | ❌ | ✅ |

### 存放位置（precedence：高优先级覆盖低）

| 层 | 路径 |
|---|---|
| Enterprise | managed settings |
| Personal | `~/.claude/skills/<name>/SKILL.md` |
| Project | `.claude/skills/<name>/SKILL.md` |
| Plugin | `<plugin>/skills/<name>/SKILL.md` |

支持**实时变更检测**（添加/修改/删除 SKILL.md 当场生效，不需要重启），支持 **monorepo 自动发现**（子目录的 `.claude/skills/` 按需加载）。

### Lifecycle

skill 一旦被触发，全文进 context **并留到 session 结束**。auto-compaction 时按"最近触发优先 / 每个 skill 留 5000 tokens / 总预算 25000"重新挂回。

---

## 4. Output Styles

### 是什么

**直接修改 system prompt 的 markdown 文件**。改的是 Claude 的角色、语气、默认输出格式，不是知识。

> "Output styles change how Claude responds, not what Claude knows."

### 跟 prompts/skills/CLAUDE.md 的区别

| 机制 | 干什么 | 用在什么时候 |
|---|---|---|
| **Output style** | 改 system prompt | 想换 role / tone / 默认输出形式 |
| **CLAUDE.md** | 在 system prompt 后追加 user message | 想让 Claude 永远记住项目惯例 |
| `--append-system-prompt` | 追加到 system prompt 但不删 | 单次调用临时加一段 |
| **Subagent** | 跑一个独立 system prompt 的子 agent | 想要一个 scoped 助手 |
| **Skill** | 触发式加载任务指令 | 可复用的工作流 |

### Built-in styles

- **Default**：标准 software engineering 系统提示
- **Proactive**：立刻执行，少问、少 plan
- **Explanatory**：在做事的同时给"Insights"
- **Learning**：协作式，让用户自己实现 `TODO(human)` 标记

### 最短示例

```markdown
---
name: Diagrams first
description: Lead every explanation with a diagram
keep-coding-instructions: true
---

When explaining code, architecture, or data flow, start with a Mermaid diagram, then explain in prose.
```

存放：
- User：`~/.claude/output-styles/`
- Project：`.claude/output-styles/`
- Managed：managed settings directory

切换：`/config` → Output style 选择，或 `settings.json` 里 `{"outputStyle": "Explanatory"}`。**改完要 `/clear` 或开新 session 才生效**（output style 是启动时读一次的）。

`keep-coding-instructions: true` = 在内置 coding 指令上叠加；false（默认）= 完全替换（用于非 coding 场景如写作助手）。

---

## 5. Settings

### 5 层 precedence（高 → 低）

| 层 | 路径 | 作用域 |
|---|---|---|
| **Managed** | MDM / `/etc/claude-code/` / registry | 整台机器，企业 IT 部署 |
| **Command Line** | CLI flag / env var | 当前 session |
| **Local** | `.claude/settings.local.json` | 当前项目、不入 git |
| **Project** | `.claude/settings.json` | 当前项目、入 git |
| **User** | `~/.claude/settings.json` | 当前用户所有项目 |

**合并规则**：标量值取高优先级；数组（permissions、hooks、MCP）**合并去重**。

### settings.json 能配什么（精选）

- `model`, `availableModels`, `outputStyle`, `effortLevel`
- `permissions.{allow,ask,deny,defaultMode,additionalDirectories}`
- `env`, `apiKeyHelper`, `awsCredentialExport`
- `hooks`
- `language`, `editorMode`, `tui`, `spinnerTipsEnabled`
- `autoMemoryEnabled`, `autoMemoryDirectory`
- `skillOverrides`, `disableSkillShellExecution`, `disableAllHooks`
- `sandbox.{filesystem,network}`
- `worktree.{baseRef,symlinkDirectories,sparsePaths}`

### 最短示例

```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "model": "claude-sonnet-4-6",
  "outputStyle": "Explanatory",
  "permissions": {
    "allow": ["Bash(npm run *)", "Bash(git diff)"],
    "deny": ["Bash(curl *)", "Read(./.env)"],
    "defaultMode": "plan"
  },
  "hooks": {
    "PostToolUse": [{
      "matcher": "Edit|Write",
      "hooks": [{ "type": "command", "command": "./lint.sh" }]
    }]
  }
}
```

### 权限规则语法（permissions 子系统）

格式：`Tool` 或 `Tool(specifier)`。

- `Bash` = 全部 bash
- `Bash(npm run *)` = 通配前缀
- `Read(./.env)` = 精确文件
- `Read(//path)` = 绝对路径，`Read(~/path)` = home，`Read(/path)` = 项目根，`Read(path)` = cwd
- `WebFetch(domain:example.com)`
- `mcp__server__tool` = MCP tool
- `Agent(Explore)` = subagent
- `Skill(commit)` / `Skill(review-pr *)` = skill

**评估顺序**：`deny → ask → allow`，**deny 永远胜**。

权限模式：`default` / `acceptEdits` / `plan` / `auto` / `dontAsk` / `bypassPermissions`。

---

## 6. 跨机制的统一感

是的，**这五种机制共享一套设计语言**：

| 设计选择 | slash commands | hooks | skills | output styles | settings |
|---|---|---|---|---|---|
| 文件格式 | markdown + YAML | JSON | markdown + YAML | markdown + YAML | JSON |
| 层级 | user / project / plugin | user / project / local / managed / plugin / skill / agent | enterprise / personal / project / plugin | user / project / managed | managed / CLI / local / project / user |
| 子目录附属文件 | ✅（skills 形态下） | — | ✅（脚本、模板、reference） | — | — |
| 通过 `/` 命令打开管理 UI | `/skills` | `/hooks` | `/skills` | `/config` | `/config`, `/permissions` |
| 热重载 | ✅ | ✅ | ✅ | ❌（要 /clear） | 大多数 ✅ |
| 是否能被插件打包 | ✅ | ✅ | ✅ | ✅ | 部分 |
| 共同安全模型 | 受 trust dialog + permissions 约束 | 同上 | 同上 | — | 受 managed settings 强制 |

**核心抽象**：每种扩展都是一个**带 frontmatter 的文本文件 + 一个明确的生命周期挂载点**。这让 Claude Code 的整个扩展生态都可以靠"会写 markdown"就上手，**复杂度按需展开**——简单需求一个文件搞定，复杂需求才需要 JSON 配置或 hook 脚本。

另一个值得注意的设计：**custom commands 主动并入 skills**。这说明团队在意识到"两套语法在做同一件事"之后，宁可破坏向后兼容也要收敛。这是产品设计成熟度的标志。

---

## 7. 机制对照表

| 名字 | 触发方式 | 文件位置 | 主要用途 |
|---|---|---|---|
| **Slash command** (legacy) | 用户输入 `/name` | `.claude/commands/<name>.md` | 已合并入 skills，仅向后兼容 |
| **Skill** | 用户 `/name` 或 Claude 自动加载（基于 description） | `.claude/skills/<name>/SKILL.md` 等四层 | 可复用工作流、领域知识、命令 |
| **Hook** | 生命周期事件自动触发（31 种） | `.claude/settings.json` 的 `hooks` 字段，或 skill/agent frontmatter 内 | **强制性**自动化：阻挡、注入、审计 |
| **Output style** | 启动时加载，整个 session 持续 | `~/.claude/output-styles/<name>.md` 等三层 | 改 role / tone / 默认输出格式 |
| **Settings** | 启动时（部分热重载） | `.claude/settings.json` 等五层 | 全局配置、权限、模型、环境变量 |
| **Permission rule** | 每次工具调用前评估 | 嵌在 settings.json 的 `permissions` 字段 | 控制 Claude 能用什么工具/读哪些文件 |

---

## 8. 给 Kokoro 的启示

Kokoro 是 Gemini 风格的 AI 对话 + Canvas web app。Claude Code 的扩展体系给到的具体设计借鉴：

1. **把"用户自定义命令"和"模板"合并成一种东西**。Claude Code 走过把它们分开的弯路，最终发现没必要——"一段可命名、可调用的预设文本 + 可选附件 + 可选触发条件" 就是同一个抽象。Kokoro 如果要做 prompt 模板系统，**别建两套：一套手动 `/slash`，一套自动触发，要做就做成同一个"带 description 的 markdown 单元"**。description 决定 LLM 何时自动用、`/name` 决定用户何时手动用。

2. **把 description 当 first-class，body 当 lazy-load**。Claude Code 只把 description 常驻 context，body 按需加载。Kokoro 如果未来要做"用户可装载的提示库"，这个模式直接抄：用户写的每个模板都有简短 description 列入 system prompt 让模型知道存在，但完整内容只在被触发时才进 context。**这是省 token 的核心机制**，对长会话尤其关键。

3. **Canvas 自然适合 hooks 的"前置/后置"事件模型**。Kokoro 的 Canvas 也有强生命周期：用户提交 prompt 前、Canvas 内容变更后、AI 响应完成后……都可以暴露成事件钩子（不一定要让用户写 shell 脚本，但起码要让前端代码 / 插件能 subscribe）。建议至少先实现 `BeforeUserSubmit`、`AfterAssistantResponse`、`OnCanvasUpdate` 三个，作为后续扩展点的基底。

4. **设置必须分层并合并**。Claude Code 的 5 层 settings 看起来重，但每一层都有明确用户：managed = 公司 IT，user = 我自己，project = 这个项目，local = 我的本机偏好。Kokoro 至少要有 **"用户全局" / "对话级"** 两层；如果未来要做团队/企业版，可以预留 "managed" 层。**数组类配置合并去重而不是覆盖**这条尤其要照抄。

5. **权限模型用 deny-first**。Claude Code 的 `deny → ask → allow` 顺序非常清晰。Kokoro 如果未来涉及插件调用外部 API、文件读写或浏览器自动化，**别用单纯的 allowlist**，要支持 deny 规则永远胜，并支持 `ask` 这个中间态——用户能授权一次就别每次都问，但永远保留 deny 的兜底。

6. **Output style 这个抽象值得偷**。它独立于"知识/项目惯例（CLAUDE.md）"和"工作流（skills）"，专管"Claude 这次扮演什么角色 / 输出什么风格"。Kokoro 完全可以做"角色预设"——比如"导师模式 / 创意模式 / 严肃报告模式"——独立于具体 prompt 模板。**关键洞见：tone 是一个独立的维度，不该混在内容预设里**。

---

## 9. 最关键的一个洞见

**Claude Code 的扩展系统是反复融合的产物，不是一上来就设计成这样。**

证据：
- custom slash commands 现在并入了 skills（"Custom commands have been merged into skills"）；
- skills 本身遵循一个**外部开放标准** Agent Skills；
- bundled built-in commands 里有一部分是"硬编码逻辑"，另一部分是 prompt-based 的"bundled skills"——也就是说连"内置"和"用户扩展"的边界都在主动模糊；
- hooks 在 skills 和 agents 的 frontmatter 里也可以局部声明——同一种机制可以**作为全局配置**也可以**作为某个 skill 的内部细节**。

对 Kokoro 的隐性教训：**先不要急着把所有扩展机制设计齐全，而是确保每个机制的核心抽象长期不变**。Claude Code 真正稳定的核心抽象只有一个：**"带 frontmatter 的 markdown + 一个明确的挂载点"**。其他都是这条之上的变种。Kokoro 如果做扩展系统，第一性原则就是先定下"用户写的扩展长什么样"（建议也是 markdown + YAML，因为这是 LLM 时代最自然的格式），然后让所有扩展形态（命令、模板、角色、自动化）都从这一个核心抽象长出来。
