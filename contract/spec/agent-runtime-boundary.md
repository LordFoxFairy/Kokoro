# Agent Runtime API/AIP 边界说明

本页是 Root contract 的语义说明，不分配 Proto 字段编号，也不替代 `contract/proto`。字段和 wire 形状仍由
`slice-a-contract-manifest.yaml` 与生成器决定。

## Cross-repository owner

```text
Root contract/proto + manifest
  -> kokoro-agent generated consumer
  -> kokoro-bff / kokoro-app contract adapters
```

- Root：定义 Launch、Control、Fork、Cleanup、ProductEvent 和 Chat DTO 的跨仓语义。
- kokoro-agent：实现 GA ingress、RunRepository、native graph、`chat_messages/chat_events` 和安全事件转换；其 control command ledger 只属于 Agent 运行可靠性内部事实。
- kokoro-bff：实现 Web-facing Chat、会话/消息/事件查询、AG-UI/SSE 投影和业务适配。
- kokoro-app：只消费 BFF 的产品 DTO，不读取 Agent 或业务仓 private facts。

实现方案分别维护在 `kokoro-agent/docs/agent/technical-plan.md` 与
`kokoro-bff/docs/api/`；两份文档只解释各自 consumer 的实现，
不改变本 Root 语义。

子仓可以有实现文档，不能复制 Proto/OpenAPI、修改字段编号或建立平行 request/event DTO。

当前实现状态：GA 与 BFF 使用严格的 Redis/TypeScript internal adapters；它们与 Root
语义对齐，但 Redis launch envelope 的 `input={message_id,content}` 与 Root protobuf 顶层
`message_id/content` 之间需要由 transport mapping 转换。Root generated consumers 与
ChatQuery transport 是下一次跨仓接线，不在任一子仓单独声明已完成。

## Launch 与 Control 语义

```text
LaunchRunRequest
  request_id / run_id / session_id / feature_key
  ExecutionIdentity(tenant_ref, actor, subject, identity_assertion_ref)
  message_id / content / optional model label / trace_json

ApplyControlRequest
  agent_run_id / command identity / control_kind
  decisions[] / optional message_id + content

当前 Redis control envelope 仍带 `session_id`，因为 worker 的本地控制流按
`run_id -> session_id` 做隔离；接入 Root generated transport 时由 GA RunRepository 补齐这层
opaque 映射，Root caller 不需要传 `session_id`。
```

caller 不传 `namespace`、`thread_id`、Agent、members、prompt、Tool、Skill、MCP、sandbox、provider 或 checkpoint selector。
GA 从 `ExecutionIdentity` 派生内部 `RuntimeNamespace`，从 `feature_key` 取得内置 Feature。

## ProductEvent 与聊天存储

`ProductEvent` 是安全事件载荷，不是 raw AgentEvent。它只允许 run phase、assistant delta/final、activity、approval、plan、ArtifactReady、StudioJobLinked 和 terminal。

```text
ProductEvent
  -> GA chat_events durable record (chat_event_id + seq)
  -> Redis live publish
  -> BFF query/replay -> AG-UI/SSE

GA chat_messages -> 用户可见历史 canonical source

Run control
  -> Agent `run_control_commands`（HTTP admission/idempotency + worker delivery state）
  -> Redis per-run control stream
  -> `run.control.receipt`（execution progress event）

上述 control 记录不写入 `chat_messages`，也不由 BFF 直接读 Agent 数据库；BFF 只消费 Agent ingress
返回的 HTTP receipt 和允许对外的产品事件投影。
```

不定义 `conversation_messages`、`run_events` 或独立 `event_outbox`。LangChain `Message.id/thread_id/checkpoint_id/tool_call_id` 只属于 native checkpoint，
与 GA chat IDs 完全分离。

## 身份与计费

`ExecutionIdentity.subject` 是 Billing/审计/外部 owner 的业务归属；`RuntimeNamespace` 只做 GA 隔离。模型按 provider accepted invocation 次数计费，使用稳定 `invocation_id` 幂等结算，token 不是用户计费单位。
