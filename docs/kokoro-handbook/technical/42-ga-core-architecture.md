# 42. GA 核心架构：一个闭环底座，多个 Agent 产品

状态：当前总体架构，2026-08-27。

kokoro-agent 严格建立在 DeepAgents 之上。DeepAgents 是唯一 Agent runtime，LangGraph 是其
原生执行基础；需要多个 Agent 在同一会话中交接时，使用官方 langgraph-swarm。GA 不实现
第二套 runtime、Graph、State、router 或 compiler。

## 1. 一句话模型

    Agent        = 完整、可复用的 DeepAgent 能力
    Feature      = 对外产品能力和 Agent 组合
    AgentFactory = 唯一内部装配器
    Run          = 一次调用事实

music Agent 可以直接成为 music Feature，也可以在 music_chat Feature 中和 general Agent 组合。
Agent 不是 composer、arranger、reviewer 等角色，Feature 本身就是业务组装入口。

## 2. 端到端链路

    Site / Session / Client
      -> Root LaunchRunRequest(feature_key, message_id, content, ExecutionIdentity)
      -> Redis internal envelope input={message_id,content}
      -> Redis worker
      -> RunLedger claim
      -> FeatureCatalog
      -> AgentFactory
      -> create_deep_agent(...)
         或 official langgraph-swarm
      -> DeepAgents native state/checkpoint
      -> GA RunLedger + chat_messages + chat_events + Workbench
      -> Redis live -> Session / AG-UI / SSE

外部请求只选择受信 Feature 和输入，不提交 Agent、Skill、MCP、graph、namespace、thread 或
worker 依赖。Feature 在 worker 内静态注册，运行中不临时改图。

## 3. Agent 和 Feature

agents/general.py、agents/music.py 等文件定义完整 Agent，包含 prompt、固定工具、默认
Skill/MCP 名称和可选 native subagent。

features/chat.py、features/music.py、features/music_chat.py 等文件定义对外 Feature：

    chat       -> general Agent
    music      -> music Agent
    music_chat -> general Agent + music Agent + handoff edges

单 Agent 直接由 DeepAgents 执行；多个 peer 只有在需要同一会话交接时才使用官方 Swarm。后台
隔离工作使用 DeepAgents 原生 subagent。不存在额外 Role、Team 或业务编排层。

## 4. AgentFactory 与官方框架

AgentFactory 在 worker 启动时创建并持有模型、checkpointer、RunLedger、Workbench 和 clients。
这些服务是内部字段，不出现在 Feature/Agent 签名中，也不命名为 deps。

Factory 只做参数翻译：

1. 从 Feature 取一个 Agent，准备工具、middleware、backend、prompt 后调用
   deepagents.create_deep_agent。
2. 从 Feature 取多个 peer，分别调用 create_deep_agent，添加官方 handoff tool，再调用
   langgraph_swarm.create_swarm。

包内不设置第二个 `factory/`。`agent_factory.py` 保存构造顺序和唯一的
`create_deep_agent` 调用；共享资源、工具/守卫、prompt 与 native subagent 分别归
`worker/services.py`、`tools/`、`prompts/`、`agents/subagents.py`。`swarm.py` 只做 official
Swarm 薄接线。

## 5. 状态、Session 与身份

DeepAgents/LangGraph 拥有 native state 和 checkpoint；Swarm 使用官方 SwarmState。GA 不继承
或包装这些类型。

入口身份是 ExecutionIdentity。GA 从它派生内部 RuntimeNamespace，用于自身隔离、Workbench
和 Capability/Storage 调用上下文；caller 不可指定 namespace 或 thread_id。Session 不保存
Agent 绑定、图选择、release 或 version。

同一 Session 只有前一 Run terminal 后，下一条普通消息才继续同一 native checkpoint；fork 才
创建新的 Session/thread/state。LangChain 原生 message/thread/checkpoint ID 与 GA 的
chat_message_id/chat_event_id 分离，GA 不读取或改造 LangChain checkpoint 表。

## 6. 能力、Storage 和 Workbench

GA 内置 default Skill 与 find_skills/load_skill。Agent/Feature 只声明名称；Factory 在构造
本次 DeepAgent 时调用窄 public clients：

    Capability -> Skill CRUD/path、可见性和 MCP registry
    Storage    -> package bytes、Asset、Artifact 生命周期
    S3Workspace -> GA Workbench 的 S3-compatible adapter
    Model/Billing/Studio -> 各自 public contract

MinIO 只是当前 S3-compatible 实现，未来可替换 AWS S3、Ceph RGW 等。S3Workspace 不拥有
Storage Artifact。未声明外部操作的 Feature 不依赖这些 client 才能运行。

## 7. 事件、聊天与计费

GA 的 chat_messages 是用户历史，chat_events 是用户可见实时/replay 事实。事件先持久化，再
发布 Redis；Redis 只负责实时传输，断线按 seq replay。GA 不创建 conversation_messages、
run_events 或 event_outbox，也不改动 LangChain checkpoint 表。

计费按 provider accepted invocation 次数结算，以 invocation_id 幂等；token 只用于上下文、
预算和诊断。

## 8. 目录

`kokoro-agent/` 是仓库/distribution，`src/kokoro_agent/` 是标准 Python `src layout` 下的 import
package，不构成两层 GA 架构。

    src/kokoro_agent/
    ├── agents/          完整 Agent 定义
    ├── features/        对外 Feature 组装入口
    ├── agent_factory.py 唯一内部装配入口
    ├── swarm.py         official langgraph-swarm 薄接线
    ├── execution/       Run、控制、HITL、事件和终态
    ├── worker/          Redis ingress、共享服务、claim、recovery、drain
    ├── tools/           GA 固定工具、工具集合与 middleware
    ├── skills/          default Skill、find/load、Workbench mount
    ├── clients/         Capability/Storage/Model 等 public clients
    ├── sandbox/         DeepAgents backend 与 S3Workspace
    ├── storage/         RunLedger、LangGraph Store、checkpoint adapter
    ├── mcp/             MCP 连接与工具接线
    ├── model/           模型与 provider adapter
    └── prompts/         静态 prompt 资产与渲染

禁止新增 ga、factory、framework、compiler、runtime、ports、deepagents.py、graph.py、flow.py、state.py
或自定义 Graph/State。Compose/Kubernetes 只负责承载和连接。

## 9. 设计收益和验收

- DeepAgents 的 loop、native state、checkpoint、subagent、interrupt 直接复用。
- 一个 Agent 可以直接对外，也可以被多个 Feature 复用。
- Feature 是唯一业务组装面；未来可视化 Builder 只生成 Agent/Feature 声明，继续使用同一 Factory。
- Swarm 只解决 peer handoff，不混入后台 subagent。
- Capability、Storage、Studio、Billing 缺席时，未声明其操作的 Feature 仍可执行。
- Session 历史来自 chat_messages，实时和 replay 来自 chat_events。
- 单 active Run、terminal、HITL 和 accepted invocation 都可在 GA facts 中审计。
- `kokoro-agent inspect [feature] [--json]` 只读同一个 `FeatureCatalog`，供开发诊断、CI 和未来
  可视化 Builder 使用；输出不包含 prompt、secret、identity、namespace、checkpoint 或 Run 状态。
