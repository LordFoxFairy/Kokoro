---
status: 🟢 accepted
version: 1.0.0
producer: kokoro-session
consumers:
  - kokoro-web
  - kokoro-agent
backward-compatibility: Envelope shapes are stable in v1; new optional fields may be added without breaking compatibility.
---

# Safety & Permission Envelope

> 统一 `kokoro-session` 发给前端的权限与安全决策包，不让 UI 直接理解底层工具细节。

关联：
- [../product/09-safety/permission-model.md](../product/09-safety/permission-model.md)
- [../product/09-safety/circuit-breakers.md](../product/09-safety/circuit-breakers.md)

## Decision kinds

### `allow`

```json
{
  "decision": "allow",
  "request_id": "perm_01J...",
  "scope": "session",
  "message": "这一步已经允许继续了。"
}
```

含义：当前动作已被放行，不需要前端再弹审批。

### `ask`

```json
{
  "decision": "ask",
  "request_id": "perm_01J...",
  "scope": "session",
  "message": "我想访问这个外部资源，可以吗？",
  "options": ["once", "session", "deny"]
}
```

含义：run 暂停，等待用户明确决策。

### `deny`

```json
{
  "decision": "deny",
  "request_id": "perm_01J...",
  "message": "这一步我不能直接做。",
  "reason": "policy"
}
```

含义：当前动作被拒绝，不进入执行。

## Circuit breaker interruption

```json
{
  "decision": "ask",
  "request_id": "perm_01J...",
  "kind": "circuit_breaker",
  "message": "这件事一旦做了就不太好回头，我想再跟你确认一次。",
  "danger_level": "high"
}
```

规则：
- 即使处在更自动化的档位，也必须中断等待用户确认
- 前端应以更强的确认样式展示，而不是普通轻提示

## Retryable transport error

```json
{
  "decision": "deny",
  "reason": "transport_error",
  "message": "连接出了点问题，可以稍后再试。",
  "retryable": true
}
```

规则：
- 这是用户可理解的错误，不暴露底层栈信息
- 前端可据此展示 retry CTA，但不能伪装成普通权限拒绝

## Decision endpoint

- 当收到 `decision: "ask"` 时，前端必须调用：`POST /sessions/{session_id}/permissions/{request_id}/decision`
- 合法请求体必须是且仅是：
  - `{ "decision": "allow", "scope": "once" }`
  - `{ "decision": "allow", "scope": "session" }`
  - `{ "decision": "deny" }`
- 明确禁止把 allow 写成 `{ "decision": "once" }` 或 `{ "decision": "session" }`；`once` / `session` 只能作为 `scope` 值出现
- `request_id` 必须来自对应的 `permission.required` 事件，禁止复用历史 request

## Normalization rule

- `kokoro-agent` 不直接决定面向用户的 UI 文案
- 最终呈现给浏览器的 envelope 由 `kokoro-session` 归一化
- 前端只理解 `allow / ask / deny` 与少量结构化补充字段
