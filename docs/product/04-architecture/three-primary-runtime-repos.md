---
status: 🟢 已定
updated: 2026-06-02
locked-by: ADR-009
---

# 三主仓运行时总览（Three Primary Runtime Repositories）

> 这份文档回答：为什么 Kokoro 当前先围绕 `kokoro-web`、`kokoro-session`、`kokoro-agent` 三个主仓收拢，以及它们之间的最小闭环如何成立。

---

## 一句话

`Kokoro` 主仓负责产品、原型与协议文档；当前真正需要先稳定的运行时主干是 3 个独立仓：`kokoro-web`、`kokoro-session`、`kokoro-agent`。

---

## 为什么当前优先只看这三个仓

- 当前已实现、已被测试覆盖、且直接影响用户体验的闭环只穿过这三个运行时仓。
- 浏览器渲染、session / replay、agent execution 的边界已经明确分离；先把这条链路收敛，比提前拆出 billing / admin / model-registry 一类未来中台仓更重要。
- `kokoro-agent` 已经用 `DeepAgents` + `LangChain` 承担上下文、工具编排与执行流；现阶段的瓶颈是协议稳定性、replay 收敛和前端体验，而不是再造一层新的编排中台。
- 未来若新增中台仓，也必须建立在这三个运行时仓的契约已稳定、回放已可靠、权限边界已清晰的前提上。

---

## 三个主仓与各自栈

| Repo | 当前主栈 | 负责 | 不负责 |
|---|---|---|---|
| `kokoro-web` | Next.js 16, React 19, TypeScript, Zod, Tailwind 4, Vitest, `@a2ui/*` | UI 壳、严格 session-stream 解析、reducer、渲染 | session 生命周期、replay 存储、raw agent 事件 |
| `kokoro-session` | Bun, TypeScript, Zod, `ioredis`, HTTP + SSE | session / conversation / run 生命周期、raw→session 归一化、replay / resume、浏览器契约 | 浏览器组件渲染、DeepAgents 编排、最终工具执行 |
| `kokoro-agent` | Python 3.11, Pydantic v2, DeepAgents, LangChain, Redis, pytest / pyright / ruff | 规划、执行、工具编排、raw execution 事件产出 | 浏览器可见 envelope、replay cursor、SSE 暴露 |

补充：`Kokoro` 主仓仍然是 spec / ADR / prototype / protocol 的源头仓，但它不是当前要先稳定的运行时主干之一。

---

## ASCII 架构图

```text
Kokoro (docs / ADR / prototype / protocol source)
    |
    | defines contracts and ownership
    v
+---------------------------+
| kokoro-web                |
| Next.js UI                |
| parse + reduce + render   |
+---------------------------+
    | POST /sessions/:id/runs
    | GET  /sessions/:id/stream  (SSE replay + live)
    v
+-------------------------------------------+
| kokoro-session                            |
| session lifecycle + normalize + replay    |
| browser-facing session-stream owner       |
+-------------------------------------------+
    | Redis: run.request / raw agent events
    v
+-------------------------------------------+
| kokoro-agent                              |
| DeepAgents/LangChain execution runtime    |
| raw execution-event producer              |
+-------------------------------------------+
```

核心原则：浏览器只消费 `kokoro-session` 的会话流；`kokoro-agent` 不直接面向浏览器暴露内部执行事件。

---

## 原始事件层 vs 会话事件层

### 1. Raw agent events（`kokoro-agent` -> `kokoro-session`）

**Owner:** `kokoro-agent`

**当前事件族：**
- `run.started`
- `text.delta`
- `text.completed`
- `tool.invoked`
- `tool.returned`
- `run.completed`
- `run.failed`

**当前 envelope：**
- `kind`
- `run_id`
- `seq`
- `payload`

**语义定位：**
- 这是执行侧事件，不是浏览器契约。
- 只表达执行语义和顺序，不表达 replay / resume / UI ownership。
- 不包含 `event_id`、`cursor`、`timestamp`、`session_id`、`conversation_id`。

### 2. Session events（`kokoro-session` -> `kokoro-web`）

**Owner:** `kokoro-session`

**当前最小事件族：**
- `session.created`
- `run.created`
- `message.delta`
- `message.completed`
- `run.completed`
- `run.failed`

**统一 envelope：**
- `event`
- `event_id`
- `session_id`
- `conversation_id`
- `run_id`
- `cursor`
- `timestamp`
- `payload`

**语义定位：**
- 这是 replay-safe、browser-safe 的会话契约。
- `event_id` 用于幂等去重；`cursor` 用于 replay / resume；`timestamp` 代表归一化后的发出时间。
- `payload` 只承载事件自身字段，不重复顶层上下文。

**当前边界收敛规则：**
- `tool.invoked` / `tool.returned` 目前停在 session 边界，不进入 `kokoro-web` 的 v1 会话流。
- `kokoro-session` 负责把 raw text 事件收敛成 `message.delta` / `message.completed`，并保持 `message_id` 稳定。

---

## 最小闭环（Minimal Closed Loop）

1. `kokoro-web` 发起 `POST /sessions/:sessionId/runs`，提交 `conversation_id`、`input`、`execution_style`。
2. `kokoro-session` 严格校验请求，并发布 `run.request` 给 agent 侧运行通道。
3. `kokoro-agent` 消费请求，使用 DeepAgents / LangChain 执行，并产出 raw agent events。
4. `kokoro-session` 订阅 raw events，做严格解析、按 `(run_id, seq)` 去重、分配 `event_id` 和单调 `cursor`，再写入 replay store。
5. 浏览器通过 `GET /sessions/:sessionId/stream` 接收 replay + live SSE；`kokoro-session` 既回放历史，也继续推送新事件。
6. `kokoro-web` 严格解析 session events，reducer 按 `event_id` 去重、按 `message_id` 合并文本，并在 `message.completed` / `run.completed` / `run.failed` 时收敛 UI 状态。

这就是当前 v1 已经成立的最小闭环：**prompt in, normalized text stream out, replay-safe convergence, terminal run state visible in UI**。

---

## 为什么未来中台仓现在不要抢主线

在这三个主仓之外，未来当然可能出现 admin、billing、workspace、model-registry、analytics 等中台仓；但它们现在不是主线，原因很简单：

1. **它们不构成当前用户闭环。** 用户今天是否能稳定发起一次 run、看到流式回复、断线恢复、重放收敛，取决于这三个运行时仓，而不是未来中台。
2. **它们依赖主干契约先稳定。** 如果 `kokoro-web`、`kokoro-session`、`kokoro-agent` 的边界还在漂移，提前拆中台只会放大协议 churn。
3. **编排能力已经有现成承载层。** 只要 `DeepAgents` / `LangChain` 还能覆盖当前 context / tools / orchestration 需求，就不应该为了“平台感”提前在 Kokoro 体系内重造一层。
4. **最该守住的是 ownership。** `kokoro-web` 只管消费和渲染，`kokoro-session` 只管会话与回放契约，`kokoro-agent` 只管执行与工具编排；中台仓的引入不应打乱这条主链。

---

## 当前方向的硬护栏

- 先改 `Kokoro` 主仓里的协议与架构文档，再改运行时仓实现。
- 浏览器侧永远只对齐 `kokoro-session` 的 session-stream 契约，不直连 `kokoro-agent` raw events。
- 新的 orchestration / context / tool-routing 需求，默认先看 `kokoro-agent` 中现有 DeepAgents / LangChain 能否承接；只有出现明确缺口时才考虑新增 Kokoro 自有中台层。
- 在未来中台仓真正有独立、稳定、不可替代的职责前，不要让它们抢走这三个主仓的主线优先级。
