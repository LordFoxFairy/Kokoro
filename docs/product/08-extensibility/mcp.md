---
status: 🔴 待你拍板
updated: 2026-05-20
---

# MCP（Model Context Protocol）

> Kokoro 作为 MCP 客户端，接入第三方 SaaS 工具（Notion / GitHub / Sentry / Slack ...）。
> 这是 Kokoro **唯一**的「跨厂商外部工具接入」路径。其余扩展（[skills](./skills.md) / [plugins](./plugins.md)）都是 Kokoro 自家私有的。
> v2+ 范围。MVP 不做。

---

## 0. 一句话

MCP 是 Anthropic 立的开放协议，已经成事实标准——GitHub / Notion / Sentry / Linear / Stripe / Slack / Figma 都有官方 MCP server。OpenAI 也在跟进。Kokoro 接入 MCP，等于一次性拿到整个生态。

**不自造协议**。

---

## 1. 为什么需要 MCP

Kokoro 是「通用 agent + Canvas」。"通用"意味着用户随时可能说：

> "看看我 Notion 里的 OKR，整理成一张 Canvas"
>
> "扫一遍我们的 Sentry 错误，写一份本周事故报告"
>
> "把 GitHub PR #423 的讨论总结成给非技术同事看的版本"

这些场景的共同点：

- 数据在外部 SaaS
- Kokoro 内置工具不可能覆盖所有 SaaS
- 自己写每个 SaaS 的接入 = 永远做不完

MCP 把这件事抽象成协议：**任何 SaaS 实现一个 MCP server，Kokoro 作为客户端就能用**。

> Anthropic 自己说："To add custom tools, connect an MCP server."
>
> 这是他们唯一开放给第三方加工具的路径。Kokoro 也这么做。

---

## 2. Kokoro 在 MCP 里的角色

Kokoro = **MCP 客户端**。

不是 server。Kokoro 不对外暴露 MCP 接口（至少 v2+ 路线里不做）。

作为客户端意味着：

- 连接其他人写的 MCP server
- 把 server 提供的 tool / resource / prompt 接入到我的能力里
- 处理鉴权 / 错误 / 配额 / 超时
- 把 server 暴露的内容，按 Kokoro 自己的 UI 语言重新呈现给用户

---

## 3. MCP 三件套（用户能感知到的）

| MCP 概念 | Kokoro 里长什么样 |
|---|---|
| **Tool** | 我能调用的能力。在工具列表里跟内置工具并列。命名 `mcp__<server>__<tool>`，UI 显示为"\<server\> · \<tool\>" |
| **Resource** | 外部数据源。用户可以 `@notion:doc/abc123` 这样 @-mention 到对话里 |
| **Prompt** | 服务器预设的命令模板。被注册为命令，写法 `/mcp__<server>__<prompt>` |

---

## 4. Transport（怎么连）

直接抄 Claude Code 的三种：

| Transport | 适用 | 例子 |
|---|---|---|
| **HTTP** | 远端服务，推荐 | `https://mcp.notion.com/mcp` |
| **stdio** | 本地进程，适合开发/自托管 | `npx -y airtable-mcp-server` |
| **SSE** | Server-Sent Events，已被 HTTP 取代 | 兼容老 server |

MVP-MCP（如果上线）只支持 HTTP。stdio 留给桌面版（如果做）和高级用户。

---

## 5. 配置 MCP server（用户视角）

### 5.1 入口

设置 → 扩展 → 「外部工具（MCP）」 → 「连接新的工具」

### 5.2 三种添加方式

**A. 从精选目录挑**

Kokoro 维护一个精选 MCP server 目录（GitHub / Notion / Linear / Slack / Sentry 等常用的）。用户点「Notion」→ 走 OAuth → 装好。

**B. 自填 URL**

用户知道一个 MCP server 的 URL，手动填。Kokoro 验证连通性，列出它声明的 tool / resource / prompt，让用户确认装哪些。

**C. 本地命令（stdio）**

桌面版 / 高级用户。让用户填一条本地命令，Kokoro 启动它作为 stdio MCP server。

### 5.3 鉴权

- 远端 server 大多走 OAuth 2.0（按 Claude Code 的实现：401/403 自动跳浏览器登录）
- 自定义鉴权用 header（支持环境变量 / API key）
- 鉴权信息**只存本机**（不上传 Kokoro 服务器）

### 5.4 Scope（作用域）

| Scope | 作用范围 | 存哪 |
|---|---|---|
| 当前对话 | 这次聊完就丢 | session |
| 项目 | 当前工作区 | 项目配置文件 |
| 用户 | 全局 | 用户目录 |
| 团队（v2+ 团队版） | 团队成员共用 | 团队配置 |

---

## 6. 权限审批

> 联动 [09-safety](../09-safety/)。

MCP 工具不该「装上就什么都能用」。每个工具调用走 Kokoro 的权限链：

- 装 MCP server 时：用户看到这个 server 声明的所有 tool/resource，**逐项授权**
- 第一次调用某个 tool：弹「这次允许 / 永远允许 / 拒绝」
- 永远不允许：进 deny 列表

**写操作要单独授权**。读 Notion 文档和"在 Notion 创建新页面"是两个权限等级，分开问。

### 项目级 MCP 配置的特殊审批

如果一个项目（工作区）的配置文件里写了 MCP server，**第一次启用项目时强制审批**——防止恶意分享的工作区配置偷偷连一个 evil server。抄 Claude Code 的设计。

---

## 7. Tool Search（按需加载）

MCP 工具有个尴尬：一个 server 可能暴露几十个 tool（GitHub 有几十个 API）。全塞进 prompt → context 爆炸。

Claude Code 的方案：**默认不把 MCP tool 全 schema 塞 system prompt**，只塞名字 + 简短描述。我在判断需要某个工具时，用 `ToolSearch` 工具按需加载完整 schema。

Kokoro 抄这个。意味着：

- 用户装 20 个 MCP server 也不会爆 context
- 我在调用前会有一次"找工具"的内部动作，可能让响应稍慢
- 用户能在设置里把高频工具标记为"常驻"，跳过 search

---

## 8. 跟 Plugins 的关系

经常会混。说清楚：

| | MCP | Plugin |
|---|---|---|
| **本质** | 协议（开放标准） | Kokoro 私有扩展机制 |
| **谁定义** | Anthropic + 社区 | Kokoro 团队 |
| **生态** | 跨厂商：Claude / ChatGPT / Cursor 都能用 | 只能在 Kokoro 用 |
| **解决的问题** | 接入外部 SaaS 的能力 | 给 Kokoro 加新的内部能力 |
| **能加 Canvas 类型？** | ❌（MCP 协议没这个概念） | ✅ |
| **能加 UI 面板？** | ❌ | ✅ |
| **能调外部服务？** | ✅（核心） | 可以但不该（让 plugin 内部去连 MCP 即可） |

**判断**：

- "我想接 Notion / GitHub / 自家 SaaS" → MCP
- "我想给 Kokoro 加流程图 Canvas 类型" → Plugin
- "我想加一个自定义命令" → Skill（最轻）或 Plugin（如果要跑代码）

**理想的协作**：plugin 可以**封装**一个 MCP server 调用，把若干 MCP 工具组合成一个更好的体验。例如「事故复盘」plugin 可以同时调 Sentry MCP + Linear MCP + Slack MCP，做一站式产物。

---

## 9. 输出大小 / 错误处理

MCP 工具的返回不可控（一个 SaaS API 可能丢回来 100k token 的 JSON）。

- 默认每次 MCP 工具调用的返回值上限 25k token，超出截断 + 提示
- 用户能在设置里调（上限 100k）
- 超时默认 30s，可配
- 错误用心人格语气包：「Notion 那边没响应。要不要稍后再试，或者你直接告诉我内容？」

---

## 10. v2+ 路线

| 阶段 | 内容 |
|---|---|
| v2.0 | MCP 客户端 MVP：HTTP transport + 精选目录 5-10 个 server + OAuth |
| v2.1 | 用户自填 URL + 权限管理 UI + Tool Search |
| v2.2 | stdio transport（桌面版前提） |
| v2.3 | 项目级 MCP 配置（团队场景）+ 强制审批 |
| v3.0 | Kokoro 自己暴露 MCP server？（反向：让别的工具调 Kokoro）—— 看市场需要 |

---

## 11. 待你拍板

- [ ] **MCP 是否进 MVP**？我的建议是不进——MVP 先验证 Canvas + 心人格 + 增长，外部工具接入是后置叙事。但如果首发用户群里 prosumer 比例高，MCP 早进有助于「通用 agent」叙事完整
- [ ] **首批精选 server 是什么**？默认建议：Notion / GitHub / Linear / Slack。但要看目标用户画像
- [ ] **桌面版是否必做**？stdio MCP 需要桌面版承载。如果只 Web，MCP 生态打了七折（很多 server 是本地 stdio）
- [ ] **是否反向暴露 Kokoro 为 MCP server**？让 Claude / Cursor 能调 Kokoro 当工具——这是把 Kokoro 变成"Canvas 后端"的有意思路径

---

## 关联

- [plugins.md](./plugins.md) — MCP vs Plugin 边界
- [skills.md](./skills.md) — skill 内可以调用 MCP 工具（v2+）
- [../09-safety/](../09-safety/) — 权限模型 / 鉴权
- [../03-product-form/feature-map.md](../03-product-form/feature-map.md) — MCP 在 v2+ 范围
- [../../research/claude-code/learnings/03-agentic-primitives.md](../../research/claude-code/learnings/03-agentic-primitives.md) — MCP 协议细节 + Tool Search 设计借鉴
