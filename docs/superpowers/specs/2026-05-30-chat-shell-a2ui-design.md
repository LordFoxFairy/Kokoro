# Chat Shell × A2UI 渲染设计（聊天外壳重做 + 采用 Google A2UI）

- **Date:** 2026-05-30
- **Status:** approved-by-user（"认可，落 spec 进 writing-plans"）
- **Scope:** 把 `kokoro-web` 的对话外壳按 `variant-a-mi-mu` 主选原型重做，并改用 **Google A2UI**（agent 驱动 UI）的渲染范式：**session 产出 A2UI operation 流，web 用自研最小 React renderer 渲染**。保留现有实时 SSE 接线。agent 不动。
- **Repos:** `Kokoro`(协议/spec)、`kokoro-session`(产出 A2UI)、`kokoro-web`(A2UI renderer + 外壳)；`kokoro-agent` 本轮不改。
- **Related:**
  - 原型 / 视觉铁律：`docs/prototypes/variant-a-mi-mu/`、`docs/PROJECT-STATE.md`（米+木+纸感）
  - 对齐决策：`docs/decisions/ADR-008-chat-alignment.md`（用户右气泡 / AI 左无气泡）、`ADR-006-color-palette.md`、`ADR-007`、`ADR-009-repository-boundaries-and-ownership.md`
  - 现有契约：`docs/protocol/session-stream.md`（v1.0.0 AGUI 信封，本轮 supersede 为 A2UI op 流）、`docs/protocol/agent-events.md`（v0.2.0，不改）
  - 外部：A2UI [github.com/google/A2UI](https://github.com/google/A2UI) · [spec v0.9](https://a2ui.org/specification/v0.9-a2ui/)

---

## 1. Goal

让一次 run 的"思考 → 调工具 → 出答案"以 **A2UI operation 流**从 session 流到 web，由 web 的自研 A2UI renderer 渲染成 `variant-a-mi-mu` 原型的"米+木+纸感"对话界面。**全程离线可测、无需 API key**（沿用 `KOKORO_MODEL=scripted` 脚本脑）。

**本轮只做聊天外壳这一片**：聊天入口（空状态/问候 + input-pill）+ 进行中对话（无气泡 AI 叙述流 + 可折叠思考块 + 工具卡）+ 侧栏 IA 外壳。

---

## 2. 为什么用 A2UI（调研结论）

- **范式契合**：A2UI = agent/服务端吐 UI 描述（JSON/JSONL operation 流），客户端用**白名单 catalog 组件**本地渲染。原生流式（逐行 op，配 SSE 完美）。与本项目"agent 纯生产、web 纯渲染"理念一致。
- **样式自控**：A2UI "is not a robust styling system"，**样式 100% 由客户端控制**，服务端只给 `variant` 这类语义提示 → 我们能把组件实现成自己的设计 token，不被 Google 视觉绑定。LLM-agnostic、transport-agnostic，**不强制 Gemini / A2A**。
- **已知硬伤（决定了实现策略）**：A2UI v0.8/v0.9 公开预览，明确 "Expect changes"（会 breaking）；**官方无 React renderer，只有 Lit**；Python SDK 细节未核实。→ 故**不依赖官方 SDK**，自研最小 React renderer（协议简单、可控）。

## 3. 关键选型（已决 + 否决理由）

| 选型 | 决定 | 否决的替代 |
|---|---|---|
| 谁产出 A2UI | **session 产出 A2UI operation 流** | ❌ agent 直接产 A2UI（让不稳定协议侵入 Python 纯生产层）；❌ web 把自研信封翻成 A2UI（浪费 A2UI 服务端驱动 UI 的核心价值） |
| 渲染器 | **web 自研最小 React renderer** | ❌ 官方 Lit renderer（非 React，融不进 Next.js）；❌ CopilotKit `A2UIMessageRenderer`（引入重运行时，与轻量纯渲染相悖） |
| catalog 来源 | **自定义 catalog**（少量语义组件，映射到 variant-a-mi-mu 实现） | ❌ 直接用官方 basic catalog（组件语义/样式不贴合我们的对话叙述流） |

## 4. 架构（本轮）

```
kokoro-agent（纯生产，不改）
   └─ 原始事件（agent-events v0.2.0：run.started/thinking.delta/text.delta/
      text.completed/tool.invoked/tool.returned/run.completed/run.failed）
        └─ StreamPort(memory|redis) ─▶ kokoro-session
                                         归一化（现有）→ A2UI 适配器（新）
                                         产出 A2UI JSONL operation 流
        ─── SSE ───▶ kokoro-web
                       <A2UIRenderer> + 自定义 catalog（米+木+纸感组件）
                       + 聊天页外壳（侧栏 IA / input-pill composer）
```

**职责边界（守 ADR-009）**：
- agent：只产原始执行事件，本轮零改动。
- session：拥有"原始事件 → A2UI op 流"的归一化/适配，分配 surface/component id、保证顺序与幂等。
- web：纯渲染，A2UI op 流是唯一输入，不反向理解 agent 语义。

## 5. A2UI 协议落地（session → web 线上格式）

采用 A2UI v0.9 的 operation 流（JSONL，每行一个 op；经 SSE 逐条发送）。本轮用到的 op：

- `createSurface { surfaceId, catalogId }` — run 开始，建一个会话 surface。
- `updateComponents { surfaceId, components:[{id, component, children?, ...props}] }` — 增量挂/更组件（同 id 重发即更新，append 语义）。
- `updateDataModel { surfaceId, path, value }` — 按 JSON Pointer 填/改数据（流式文本增量走这里）。

**最小 op 序列示例（一次 scripted run：思考 → echo_search → 正文）**
```jsonl
{"version":"v0.9","createSurface":{"surfaceId":"run_X","catalogId":"kokoro/chat/v1"}}
{"version":"v0.9","updateComponents":{"surfaceId":"run_X","components":[{"id":"root","component":"Thread","children":[]}]}}
{"version":"v0.9","updateComponents":{"surfaceId":"run_X","components":[{"id":"th_1","component":"ThinkingBlock","summaryPath":"/thinking/th_1"}]}}
{"version":"v0.9","updateDataModel":{"surfaceId":"run_X","path":"/thinking/th_1","value":"在想要不要先查一下…"}}
{"version":"v0.9","updateComponents":{"surfaceId":"run_X","components":[{"id":"root","component":"Thread","children":["th_1"]}]}}
{"version":"v0.9","updateComponents":{"surfaceId":"run_X","components":[{"id":"tc_1","component":"ToolCard","toolName":"echo_search","status":"running"}]}}
{"version":"v0.9","updateComponents":{"surfaceId":"run_X","components":[{"id":"root","component":"Thread","children":["th_1","tc_1"]}]}}
{"version":"v0.9","updateComponents":{"surfaceId":"run_X","components":[{"id":"tc_1","component":"ToolCard","toolName":"echo_search","status":"done"}]}}
{"version":"v0.9","updateComponents":{"surfaceId":"run_X","components":[{"id":"m_1","component":"Message","author":"ai","textPath":"/messages/m_1"}]}}
{"version":"v0.9","updateDataModel":{"surfaceId":"run_X","path":"/messages/m_1","value":"好的，"}}
{"version":"v0.9","updateDataModel":{"surfaceId":"run_X","path":"/messages/m_1","value":"好的，结果是…"}}
{"version":"v0.9","updateComponents":{"surfaceId":"run_X","components":[{"id":"root","component":"Thread","children":["th_1","tc_1","m_1"]}]}}
```
> 约定：流式文本用 `updateDataModel` 覆盖整段累计值（renderer 直接显示最新值），不做字符级 patch——简单且与现有"折叠 delta"一致。组件挂载与数据更新分离，children 顺序由 `root` 的 `Thread` 维护。

**SSE 封装**：沿用现有 SSE 端点；每个 SSE `data:` 行承载一条 A2UI op（JSON）。事件 `event:` 字段固定 `a2ui.op`。游标 / replay 仍由 session 负责：每条 op 落 replay store，断连后按序重放（本轮只保证"重连从头重放"，断连中点续传留后轮）。

## 6. 自定义 catalog（`kokoro/chat/v1`）

本轮组件白名单（语义组件，样式在 web 用 variant-a-mi-mu token 实现）：

| component | props | 渲染（对标原型 class） |
|---|---|---|
| `Thread` | `children[]` | 对话滚动容器（`.chat-thread`），按 children 顺序竖排 |
| `Message` | `author:"user"\|"ai"`, `textPath` | 用户=右气泡（`.message--user`，ADR-008）；AI=左无气泡叙述流（`.message--ai`），文本来自 dataModel[textPath] |
| `ThinkingBlock` | `summaryPath` | 可折叠 `💭 思考 ▸`（`.thinking`/`<details>`），展开显示 summary |
| `ToolCard` | `toolName`, `status:"running"\|"done"\|"error"` | `🔧 {toolName}`（`.tool-call-details`），running 呼吸 → done ✓ |

**应用外壳（本轮静态/视觉占位，不进 catalog——属页面框架而非 surface 内容）**：
- 侧栏 IA（`variant-a-mi-mu` 单列分组：新对话/搜索 · 创作 7 组件 flyout · 进阶 · 发现 · 最近 · 用户行）——本轮渲染为外壳，flyout/导航为视觉占位，不接路由。
- 顶栏 + 模式切换器（细想/普通，视觉占位）。
- `Composer`（input-pill）：附件按钮、模式 chip、发送；发送 = 触发 `start_run`（接现有后端）。空状态问候（"今天想做**什么**？"）。

**扩展点**：新增组件 = catalog 加一项 + web 加一个 renderer 映射，隔离改动（DeepAgents/canvas 后轮按此扩）。

## 7. 数据流（端到端）

```
web Composer 发送 ─POST─▶ session start_run ─run.request─▶ agent Brain(scripted/fake)
  agent: run.started→[thinking.delta]*→tool.invoked→tool.returned→text.delta*→text.completed→run.completed
   └─ StreamPort ─▶ session 归一化 + A2UI 适配:
        run.started        → createSurface + root(Thread)
        thinking.summary   → updateComponents(ThinkingBlock) + updateDataModel(summary) + root.children+=
        tool.started       → updateComponents(ToolCard status=running) + root.children+=
        tool.completed     → updateComponents(ToolCard status=done|error)
        message.delta      → updateDataModel(/messages/{id}=累计文本)（首次 delta 先挂 Message 组件 + root.children+=）
        message.completed  → updateDataModel(最终文本)
        run.completed      → （可选）无操作 / 标记完结
   ─ SSE(event:a2ui.op) ─▶ web A2UIRenderer：逐 op 维护 {components 树, dataModel}，渲染 catalog 组件
```

## 8. 错误 / 边界

- **session A2UI 适配**：每个 surface/component id 稳定且幂等（同 `(run_id, seq)` 不得产生重复 op）；缺字段的原始事件经现有 Zod strict 已被拒，不进适配器。
- **乱序保护**：children 始终由 session 按 seq 顺序重算后整发 `root`，renderer 不自行排序。
- **renderer**：未知 `component` 名 → 渲染占位（`未知组件: X`）+ console.warn，不崩；`textPath`/`summaryPath` 指向的 dataModel 缺失 → 渲染空，不崩；op JSON 解析失败 → 跳过该行 + warn。
- **tool error**：`tool.returned{status:"error"}` → `ToolCard status="error"`（红点/失败态），run 不必失败。
- **断连**：重连从 replay store 从头重放全部 op（中点续传留后轮）。
- **空 run / run.failed**：renderer 容忍空 Thread；`run.failed` 由 session 翻成一个错误态 Message 或保持外壳可用（实现时择一并测试锁定）。

## 9. 测试（离线、无 key、确定性）

- **session**：A2UI 适配器单测——给定一串归一化事件（thinking→tool→message），断言产出的 op 序列正确（surface 建立、组件挂载顺序、dataModel 累计、children 顺序、tool 状态翻转、幂等重放不重复）。Schema 崩塌（缺字段原始事件）仍被拒。Zod strict 校验 op 出站格式。
- **web**：renderer 纯函数 reducer 单测（逐 op 构建 {components, dataModel}，断言交错顺序 / 未知组件占位 / 缺数据不崩 / 幂等）；组件渲染测试（Message 右/左对齐、ThinkingBlock 折叠默认、ToolCard running→done）。
- **集成**：离线浏览器 e2e（`KOKORO_STREAM_BACKEND=redis KOKORO_MODEL=scripted` 起三进程），浏览器看到 思考块 + 工具卡 + 正文以原型样式渲染，展开/折叠交互可用，截图（折叠 + 展开）。0 console error。无真实 LLM 调用。
- **DoD**：三仓 LSP/linter 全绿、测试 100% pass（含 schema 崩塌/幂等/未知组件/工具错误/顺序边界）、浏览器截图存档。

## 10. 协议文档变更

- `docs/protocol/session-stream.md`：本轮 **supersede**——session→web 线上格式从自研 AGUI 信封改为 **A2UI v0.9 operation 流**。新增/改写为 `session-stream.md` v2.0.0（major bump，记录 catalog `kokoro/chat/v1` 定义 + 用到的 op 子集 + SSE 封装约定 + replay 语义）。保留旧版说明于"历史"段，注明 supersede。
- `docs/protocol/agent-events.md`：不改（agent 侧契约不变）。

## 11. 本轮明确不做（YAGNI / 留后轮）

- canvas / 产物面板（三栏布局、`canvas-*` 组件）。
- session/SSE 断连中点续传、游标精细化、replay 硬化边界（kill redis mid-run）。
- agent 选型/打磨（langchain vs deepagents、对标 Claude Code/Manus/OpenClaw）、真实 LLM。
- 侧栏导航真实路由、创作组件页、移动端响应式。
- A2UI 双向交互（用户在 agent 生成的表单里输入回填 dataModel → 回传 agent）——本轮只做单向"agent→UI 展示"，交互回传留后轮。

## 12. 风险与缓解

- **A2UI 不稳定（会 breaking）**：只取 v0.9 的极小 op 子集，自研 renderer 不依赖官方包；协议升级时改动集中在 session 适配器 + web renderer 两处。
- **catalog 与原型组件耦合**：catalog 只定义"语义 + props"，视觉实现全在 web，换皮不动协议。
- **过度工程**：本轮严格限定 4 个 surface 组件 + 外壳，canvas/交互回传一律不做。
