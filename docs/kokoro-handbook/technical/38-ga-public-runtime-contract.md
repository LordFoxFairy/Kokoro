# 38. GA 公共运行契约

状态：当前首发契约，2026-08-27。

本页只定义 **Session/Client 如何请求 GA**。GA 的内部实现以
[42 GA 核心架构](42-ga-core-architecture.md) 和
[36 GA 整体 Agent 技术方案](36-ga-final-agent-technical-plan.md) 为准。
Root `contract/` 的 Proto、manifest 和生成物是唯一 wire authority；本页不复制字段编号，也不
在子仓创建第二份 DTO。

## 1. 唯一入口

```text
LaunchRunRequest
  -> Redis
  -> GA worker
  -> FeatureCatalog(feature_key)
  -> AgentFactory
  -> DeepAgents native Agent
     或官方 langgraph-swarm
```

调用方只表达三件事：**谁在什么主体下发起、进入哪个 Feature、输入是什么**。Agent 如何组装、
使用哪些 Skill/MCP、是否使用 Swarm，都由 GA 内置的 Feature 声明决定。

### 1.1 请求字段

```text
Root `kokoro.agent.v1.LaunchRunRequest` {
  request_id
  run_id
  session_id
  feature_key
  execution_identity {
    tenant_ref
    actor { kind, opaque_ref }
    subject { kind, opaque_ref }
    identity_assertion_ref
  }
  message_id
  content
  requested_model_label?
  trace_json
}

当前 Redis worker 使用内部 envelope：`kind=run.request`，以上字段保持同一语义，
`message_id/content` 暂收在 `input={message_id,content}`；Root generated transport 接入时
只做一次字段映射，不把 Redis envelope 当成第二份 Root schema。
```

- `feature_key` 是 GA Feature 目录键，不是 Agent 名称，也不是用户传入的 graph 配方。
- `execution_identity` 由 IAM/Session 生成。`tenant_ref` 是租户边界，`actor` 是当前发起者，
  `subject` 是个人、项目或服务主体；GA 用它完成授权复验、审计和计费归属。
- `session_id` 是产品会话唯一标识。GA 将它作为 DeepAgents/LangGraph 的 checkpoint thread
  输入；调用方不再单独指定 `thread_id`。
- `requested_model_label` 只能在 Feature 允许的模型集合中选择模型句柄，不改变 Agent 结构。

请求不携带 Agent、member、prompt、tool、Skill、MCP、subagent、sandbox、namespace 或 graph
配置。不存在额外的 Session 配置对象；Session 只保存产品会话和主体归属。

## 2. 身份与内部 namespace

GA 在入站处把 `execution_identity` 转成自己的内部运行上下文：

```text
ExecutionIdentity
  -> GA 计算 RuntimeNamespace
  -> workspace = RuntimeNamespace + session_id
  -> checkpoint thread = session_id
```

`RuntimeNamespace` 只用于 GA 内部隔离，外部永远不传、不保存、不选择。`subject` 与 namespace
是两件事：前者用于计费/审计/权限，后者用于 GA 的工作区和 Store 隔离。相同主体下换一个已
授权 actor，不会产生新的会话空间。

同一个 Session 的普通消息在上一 Run 已结束后继续同一个 native checkpoint；只有 fork 才创建
新的 Session/thread/state。恢复、HITL 和取消都使用 GA 已保存的 Run 数据，不要求浏览器重新
提交 namespace 或 Agent 配置。

## 3. Agent、Feature 和 Swarm

```text
Feature
  -> AgentFactory
  -> create_deep_agent(...)
```

单 Agent Feature 直接运行 DeepAgents。需要 peer 交接时：

```text
Feature.agents
  -> 每个 Agent 都由 create_deep_agent 构造
  -> 官方 create_handoff_tool
  -> 官方 langgraph_swarm.create_swarm
```

DeepAgents 拥有 loop、native state、subagent、interrupt 和 checkpoint；官方 Swarm 拥有 peer
handoff state。GA 不实现自己的 router、Graph、State 或编排 runtime。

## 4. 职责边界

| 能力 | Owner | GA 的使用方式 |
|---|---|---|
| Agent loop / state / checkpoint | DeepAgents / LangGraph | 直接调用官方 API |
| Feature 与 Agent 组合 | GA | `features/` + `AgentFactory` |
| 默认 Skill、find/load | GA | 内置工具和本地目录 |
| 用户/项目/session Skill CRUD 与路径 | Capability | `clients/skills.py` 按需调用 |
| MCP 注册与连接 | Capability / MCP owner | GA client 按需调用 |
| package bytes、Artifact | Storage | `clients/storage.py` 按需调用 |
| Workbench 文件 | GA | `S3Workspace` S3-compatible adapter |
| 用户聊天历史 | GA | `chat_messages` |
| 用户实时与 replay 事件 | GA | `chat_events`，持久化后发布 Redis |
| 浏览器鉴权、AG-UI/SSE | Session | 查询/replay/投影，不执行 Agent |
| 调用计费 | Billing | 按 provider accepted invocation 次数结算 |

外部 client 是按能力启用的旁路。未声明外部操作的 Feature，即使 Capability、Storage 或 Studio
暂时不可用，GA 核心仍可以执行和恢复。

## 5. ID 与事件

LangChain/DeepAgents 的 native ID 与 GA 产品 ID 完全分开：

```text
DeepAgents: Message.id / checkpoint_id / tool_call_id
GA:         run_id / chat_message_id / chat_event_id / seq
```

GA 不读取或改造 LangChain checkpoint 表。`chat_events` 是用户可见事件的唯一持久事实；Redis
只是实时传输，断线后由 Session 按 `seq` replay。raw framework event、prompt、secret、sandbox
路径和外部响应不进入产品事件。

## 6. 契约同步

```text
Root contract/proto + manifest
  -> 生成 GA / Session / Web consumer
  -> 各仓 adapter 与测试
  -> 本页 API/AIP 摘录
```

修改字段必须先修改 Root contract 并重新生成消费者；GA、Session、Web 只实现各自 adapter，
不手写平行字段或本地 wire schema。

## 7. 验收清单

- `music` 可独立作为 Feature，也可被组合 Feature 复用。
- 多 Agent 只经官方 Swarm 交接；没有 GA 自有 router、Graph、State 或 runtime。
- Session/Client 只传 `feature_key + execution_identity + message_id/content`（Redis 内部
  envelope 使用 `input`），不传 Agent 配方和 namespace。
- GA 的聊天历史与实时事件可在 Redis 丢失后按 `chat_events.seq` replay。
- LangChain checkpoint 表与 GA 聊天表互不修改。
- 计费按 provider accepted invocation 次数记录，`invocation_id` 保证幂等。
