# Permission Interruption Closed Loop Design

## Goal

在 **不接真实危险工具**、**不修改 agent 能力面** 的前提下，先把 Kokoro 的权限中断语义做成一条完整闭环：

- `kokoro-session` 能表达并 replay 一个 `permission.required` 生命周期
- `kokoro-web` 能在聊天线程中纯渲染 ask / resolved 卡片
- 用户能提交 `allow once` / `allow for session` / `deny` 决策
- 决策后卡片原地收敛，run 从“等待用户”恢复到后续状态

本轮是 **synthetic-first**：先验证 session / web / protocol 闭环，不接 `kokoro-agent` 的真实权限事件，也不放开 FS / execute / creation tools。

---

## Why this slice now

上一轮已经验证了 Kokoro 当前最稳的前进 seam：

- agent 保持 generic
- session 作为 harness 识别并投影会话语义
- web 保持 pure renderer

`write_todos -> Plan` 已经证明这条 seam 可行。权限中断与其本质相同：它不是底层工具细节，而是“run 暂停，等待用户决策”的 **会话语义**。同时，`docs/protocol/session-stream.md` 已经定义了 `permission.required`，但当前 `kokoro/chat/v1` catalog 还没有对应的对外渲染，因此这是最小、最干净、最能为后续真实副作用能力铺路的一刀。

---

## Scope

### In scope

1. 统一权限协议字段口径，消除 `decision_kind` vs `decision` 分叉
2. 在 session 内部支持一个 replayable 的 `permission.required` 生命周期
3. 在 A2UI catalog 中增加线程内 `PermissionCard`
4. 在 web 中提交三种决策：`allow once` / `allow for session` / `deny`
5. 决策后原地收敛卡片状态
6. 覆盖单测与 offline browser e2e

### Out of scope

1. 不接 `kokoro-agent` 原始权限事件
2. 不放开 DeepAgents `task` / subagents / FS / execute / real creation tools
3. 不做长期授权记忆、组织级策略、路径级规则
4. 不做 `artifact.available` 面板 / 三栏布局
5. 不顺手做 SSE mid-stream resume hardening
6. 不做 composer 邻近 banner / 全局浮层式权限 UI

---

## Primary design decision

### 权限请求放在线程里，不做 composer 邻近挂起条

`permission.required` 必须作为聊天 timeline 里的一个新卡片存在，和 `ThinkingBlock` / `ToolCard` / `Plan` 同级。原因：

1. **贴合现有架构**：A2UI timeline 已经是 Kokoro 当前被验证的 UI 承载层；权限请求本质上就是一条会话事件。
2. **replay 天然成立**：刷新或重连时，只需 replay 到对应事件即可重建挂起态，不需要额外从页面壳推导“当前有没有挂起请求”。
3. **后续可扩展**：将来的高风险确认、联网发布、外部写操作、付费动作都能走同一组件语义，不再新增第二套 suspend UI。

因此本轮不设计 composer 附近的 suspend banner，也不引入 modal-first 的全局中断机制。

### Conceptual model: a constrained ask form

是的，概念上它**很像一种 ask/query 表单**，但不是通用问答表单，而是一个**受约束的安全决策表单**：

- 相同点：都是 timeline 里的交互卡片，都在等待用户输入后才能继续
- 不同点：permission 请求不是为了收集开放信息，而是为了收集**有限决策**（`allow once` / `allow for session` / `deny`）
- 设计结论：UI 形态可以借鉴 ask card / query form，但协议语义必须单独保留 `permission.required`

换句话说，本轮把 `PermissionCard` 视为 **specialized ask card**，而不是另起一个完全不同的交互系统，也不是把它退化成普通文本提问。

---

## Canonical protocol shape

本轮将 `docs/protocol/session-stream.md` 与 `docs/protocol/safety-and-permission-envelope.md` 统一到以下 canonical shape。

### Ask state

```json
{
  "event": "permission.required",
  "payload": {
    "request_id": "perm_01J...",
    "decision": "ask",
    "scope": "session",
    "message": "我想访问这个外部资源，可以吗？",
    "options": ["once", "session", "deny"],
    "kind": "permission"
  }
}
```

### Resolved state

```json
{
  "event": "permission.required",
  "payload": {
    "request_id": "perm_01J...",
    "decision": "allow",
    "scope": "once",
    "message": "这一步已经允许继续了。",
    "kind": "permission"
  }
}
```

```json
{
  "event": "permission.required",
  "payload": {
    "request_id": "perm_01J...",
    "decision": "allow",
    "scope": "session",
    "message": "本会话内同类动作已允许继续。",
    "kind": "permission"
  }
}
```

```json
{
  "event": "permission.required",
  "payload": {
    "request_id": "perm_01J...",
    "decision": "deny",
    "message": "这一步未被允许继续。",
    "kind": "permission"
  }
}
```

### Canonical rules

1. 统一使用 `decision`，不再使用 `decision_kind`
2. `decision: "ask"` 表示 run 正在等待用户
3. `decision: "allow" | "deny"` 表示同一 `request_id` 已收敛
4. `scope` 在本轮只允许 `once | session`
5. `kind` 本轮只保留极小集合：`permission | circuit_breaker`
6. `options` 仅在 `ask` 态出现；resolved 态不再需要按钮选项

### Naming note

事件名继续沿用 `permission.required`。尽管它也承载后续 resolved 更新，但这比新增 `permission.updated` / `permission.resolved` 更薄，且更容易与当前已有文档和 UI 心智模型衔接。UI 通过 `request_id` 做同卡片原地更新，通过 `decision` 区分 ask 与 resolved。

---

## Session responsibilities

本轮的主角是 `kokoro-session`。它负责三件事：

1. **归一化权限生命周期**
2. **把权限生命周期投影成 timeline 中的 `PermissionCard`**
3. **接收用户决策并驱动挂起请求进入 resolved 状态**

### Internal session event

`SessionEvent` 增加 `permission.required` 事件名。其 payload 使用上面的 canonical shape。

### Storage and replay

session replay 层继续存 `SessionEvent`。当同一 `request_id` 先收到 `ask`，随后收到 `allow` 或 `deny` 时：

- replay 时仍按事件顺序重放
- projector 以 `request_id` 为稳定 identity
- 第一次 `ask` 时挂载组件并写入 data model
- 后续 `allow` / `deny` 时只更新相同 data-model path 的对象

这样刷新后会自然恢复到“已决后的卡片状态”，而不是重新 ask 一次。

### Decision endpoint

本轮新增一个 session 侧决策入口：

`POST /sessions/{session_id}/permissions/{request_id}/decision`

请求体：

```json
{
  "decision": "allow",
  "scope": "once"
}
```

或

```json
{
  "decision": "allow",
  "scope": "session"
}
```

或

```json
{
  "decision": "deny"
}
```

设计理由：

- 权限请求是 session 对浏览器暴露的挂起语义，放在 session API 下最清晰
- 不要求前端绑定到某个具体 run 路径才能提交决策
- `request_id` 自身足以标识要更新的挂起请求，session 内部再关联 run 即可

本轮不要求这个 endpoint 真正恢复一个正在等待 agent 的真实后台执行链；synthetic-first 只要求它能让 replay/event 流与 UI 收敛完整成立。

---

## Synthetic-first rollout

本轮故意不碰 `kokoro-agent`。权限请求由 session 侧合成，用于验证 UI / replay / 决策闭环。

### Rollout rule

1. 由 session 测试夹具、dev fixture、或 synthetic run 分支产出 `permission.required{decision:"ask"}`
2. 浏览器看到线程中的 `PermissionCard`
3. 用户点击 `allow once` / `allow for session` / `deny`
4. session 通过 decision endpoint 追加同一 `request_id` 的 resolved 事件
5. projector 仅更新该卡片绑定的数据对象，卡片原地变为 resolved

### Why synthetic-first

- 把 agent / tool exposure / safety policy 暂时留在本轮之外，避免扩大写区
- 先证明“会话中断语义”本身是对的，再把真实来源接进来
- 为后续 FS / execute / creation tools 的危险动作中断准备好表面与契约

---

## A2UI projection and web rendering

### Data-model shape

session projector 为每个权限请求写一份对象到：

`/permissions/{request_id}`

例如：

```json
{
  "requestId": "perm_01J...",
  "decision": "ask",
  "scope": "session",
  "message": "我想访问这个外部资源，可以吗？",
  "options": ["once", "session", "deny"],
  "kind": "permission"
}
```

### Component shape

A2UI catalog 新增：

- `PermissionCard{ requestPath: { path: "/permissions/{request_id}" } }`

与 `Plan{todosPath:{path}}` 相同，组件通过单个 `DynamicValueSchema` 绑定整对象，web 只负责纯渲染，不自己推导业务状态。

### Timeline behavior

- ask 首次出现时，thread children 里插入一个稳定 id 的 `PermissionCard`
- resolved 更新时，不替换 timeline 节点；只更新 data model
- `decision === "ask"` 时展示按钮
- `decision !== "ask"` 时按钮消失，改为展示收敛态文案

### Visual language

沿用当前米+木+纸感 chat shell，不引入 modal、toast、浮层式重 UI。`kind === "circuit_breaker"` 可以在同组件内提高强调级别（更强标题/描边/警示文案），但不拆新组件。

---

## User-visible interaction contract

### Ask state

用户看到：

- 标题：需要你的确认
- 正文：session 归一化后的可读 message
- 三个动作：
  - `Allow once`
  - `Allow for session`
  - `Deny`

### Resolved state

用户点击后，卡片原地收敛：

- allow once → 已允许这一步继续
- allow for session → 本会话内同类动作已允许继续
- deny → 这一步未被允许继续

按钮隐藏，不做“弹完就消失”。这样 replay、截图、审计都能保留完整会话痕迹。

---

## Failure handling

### Invalid decision payload

如果前端提交了非法组合（例如 `decision: allow` 但没有 `scope`，或 `scope: forever`）：

- session 返回 4xx
- 不改写当前挂起请求
- UI 保持 ask 态，并显示 session 返回的用户可读错误文案

### Duplicate decision

如果同一 `request_id` 已经 resolved，又重复提交决策：

- session 必须幂等处理
- 返回当前最终状态
- 不再新增第二次 ask 或第二张卡

### Refresh during ask

如果 ask 态时页面刷新：

- replay 后仍显示 ask 卡片
- 不丢按钮
- 不重复生成第二个 `request_id`

### Refresh after resolve

如果 resolved 后页面刷新：

- replay 后显示 resolved 卡片
- 不重新 ask

---

## Files likely touched in implementation

### docs

- `docs/protocol/session-stream.md`
- `docs/protocol/safety-and-permission-envelope.md`
- `docs/superpowers/plans/...`（下一步）

### kokoro-session

- `kokoro-session/src/domain/events.ts`
- `kokoro-session/src/application/a2ui-projector.ts`
- `kokoro-session/src/interfaces/http.ts`
- `kokoro-session/tests/...`

### kokoro-web

- `kokoro-web/src/interfaces/a2ui/catalog.ts`
- `kokoro-web/src/interfaces/a2ui/components/permission-card.tsx`
- `kokoro-web/src/app/globals.css`
- `kokoro-web/tests/...`

本轮**不应修改**：

- `kokoro-agent/src/kokoro_agent/infrastructure/model.py`
- `kokoro-agent/src/kokoro_agent/run_agent.py`
- 任何真实工具暴露或执行路径

---

## Test strategy

### Session unit / integration

1. `permission.required{decision:"ask"}` 能正确投影成 `PermissionCard`
2. 同一 `request_id` 的 resolved 事件会更新既有 data model，而不是新挂第二张卡
3. replay ask → resolve 后，最终 UI 状态可确定重建
4. decision endpoint 对非法 payload 返回 4xx，对重复决策幂等

### Web component tests

1. ask 态正确显示 message + 3 个动作
2. 点击 `Allow once` / `Allow for session` / `Deny` 发出正确请求体
3. resolved 态不再显示按钮，只显示收敛态文案
4. `kind === "circuit_breaker"` 时样式强调正确

### Offline browser e2e

1. synthetic run 流里插入 ask 事件
2. Playwright 看到线程中的权限卡片
3. 点击 `Allow once`
4. UI 原地收敛，并出现后续状态/消息
5. ask 态刷新仍在；resolved 后刷新不再 ask
6. console 0 error

---

## Deferred follow-ups

1. 把 synthetic session 权限事件替换为真实 agent/tool 触发源
2. 将相同语义复用到 FS / execute / creation tools / publish actions
3. 评估是否需要 session 级授权缓存命中逻辑
4. 与 subagents / Task slice 对齐更复杂的权限继承规则
5. 再考虑是否需要独立 `permission.resolved` 事件；在当前薄闭环下先不引入

---

## Final recommendation

本轮按 **线程内 `PermissionCard` + canonical `decision` 字段 + session-side synthetic-first** 落地，是当前最小、最稳、最符合 Kokoro 既有 harness 架构的前进方式。
