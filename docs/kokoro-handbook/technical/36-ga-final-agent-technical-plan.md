# 36. Kokoro GA Agent 最终技术方案

状态：当前总体技术方案，2026-08-27。

本方案只定义 kokoro-agent。它严格建立在 DeepAgents 之上：DeepAgents 是唯一 Agent runtime，
LangGraph 是 DeepAgents 使用的原生执行基础；需要多个 peer 交接时使用官方 langgraph-swarm。
GA 不再定义自己的 Graph、State、router、compiler 或 runtime。

## 1. 核心模型

    Agent        = 完整、可复用的 DeepAgent 能力声明
    Feature      = 对外产品能力及 Agent 组合入口
    AgentFactory = GA 内部唯一装配器
    Run          = 一次调用的生命周期事实

Agent 定义包含 prompt、固定工具、Skill/MCP 名称和可选 native subagent。Feature 可以只选择
一个 Agent，也可以选择多个 Agent 并声明 peer handoff。music Agent 可以直接成为 music
Feature，也可以作为 music_chat 的成员；不增加 composer、arranger、reviewer、Role、Team 或
另一层业务编排对象。

## 2. 唯一运行链路

    Root LaunchRunRequest(feature_key, message_id, content, ExecutionIdentity)
      -> Redis internal envelope input={message_id,content}
      -> Redis worker
      -> RunLedger claim
      -> FeatureCatalog.get(feature_key)
      -> AgentFactory.build(request)
      -> create_deep_agent(...)
         或 create_deep_agent(...) + official create_swarm(...)
      -> DeepAgents native state/checkpoint
      -> GA RunLedger、chat_messages、chat_events、Workbench
      -> Root Chat query boundary
      -> Session 查询/replay 与 AG-UI/SSE

请求只选择可信 Feature 和本次输入，不携带 Agent、Skill、MCP、graph、namespace、thread 或
worker 依赖。Feature 是 worker 内受管声明，运行中不接收临时配方。

## 3. Agent 与 Feature

agents/general.py、agents/music.py 等文件各自定义一个完整 Agent。Agent 文件不读取 Session、
Redis 或外部数据库，也不处理产品交付。

features/chat.py、features/music.py、features/music_chat.py 等文件各自定义一个对外 Feature：

    chat       -> general
    music      -> music
    music_chat -> general + music + declared handoff

单 Agent Feature 直接调用 DeepAgents。只有需要同一会话内互相接手时才创建 official Swarm。
一个 Agent 需要后台隔离工作时，使用 DeepAgents native subagent，不把后台任务改造成新的
GA runtime。

## 4. AgentFactory

worker 启动时创建一个 AgentFactory 实例。模型、checkpointer、RunLedger、Workbench 和部署注入的
public clients 作为实例字段保存；它们不通过请求或 Feature 参数传播，也不称为 deps。标准 CLI
不直读 owner 私库；`tools/`、`agents/` 等叶子模块只接收自身所需窄参数，不接收整个 WorkerServices。

Factory 只有两条构造路径：

1. 一个 Agent：准备官方参数，直接调用 deepagents.create_deep_agent。
2. 多个 peer：分别调用 create_deep_agent，添加官方 handoff tool，再调用
   langgraph_swarm.create_swarm。

不设置 `factory/` 目录。`agent_factory.py` 保留构造顺序和唯一的 `create_deep_agent` 调用；参数
准备回到真实 owner：共享资源在 `worker/services.py`，工具与守卫在 `tools/`，静态 prompt 资产在
`prompts/`，DeepAgents native subagent 在 `agents/subagents.py`。它们不保存 Session 状态、
不执行第二套 loop，也不产生 GA 自有 Graph 或 State。

## 5. 状态、Session 与身份

DeepAgents/LangGraph 拥有 native state 和 checkpoint；Swarm 使用官方 SwarmState。GA 不继承、
包装或重命名这些类型。

Root 只提供 ExecutionIdentity。GA 在 ingress 以稳定的 `tenant_ref + subject` 派生 RuntimeNamespace，用于自身隔离；actor/assertion 仅用于授权、审计和计费，不参与隔离键。RuntimeNamespace 用于
Workbench key；caller 不传 namespace 或 thread_id。Session 不保存 Agent 绑定、图配置、
release 或 version。

同一 Session 只有前一 Run terminal 后，下一条普通消息才继续同一 native checkpoint；fork
创建新的 Session/thread/state。LangChain 原生 message、thread、checkpoint ID 与 GA 的
chat_message_id、chat_event_id 分离，GA 不改造 LangChain checkpoint 表。

## 6. Skill、MCP、Storage 与 Workbench

Agent/Feature 只声明 Skill 名称；Factory 在本次构造时使用 ExecutionIdentity 和 GA 派生的
RuntimeNamespace 解析当前 Run 可见引用，并将只读 `/.skills/` route 交给 DeepAgents 原生 SkillsMiddleware。其他外部能力调用：

    Capability client -> 用户、项目、session Skill CRUD/path 与 MCP registry
    Storage client    -> package bytes、Asset、Artifact 生命周期
    S3Workspace       -> GA Workbench 的 S3-compatible adapter
    Model/Billing     -> 各自 public contract

MinIO 只是当前 S3-compatible 实现，未来可以替换 AWS S3、Ceph RGW 等。S3Workspace 不拥有
Storage Artifact 生命周期。外部 client 缺席时，未声明外部操作的 Feature 仍可执行。

## 7. GA 持久事实、事件与计费

GA 只保存产品聊天所需的 chat_messages 和 chat_events，Session 通过 Root
Chat query boundary 读取历史和 replay。GA internal safe envelope 不直写 Session
browser-live stream；LangChain checkpoint 仍由框架拥有。GA 不新增 conversation_messages、
run_events 或 event_outbox 表。

计费按 provider accepted invocation 次数结算，以稳定 invocation_id 幂等；token 只用于上下文、
预算和诊断，不是计费单位。

## 8. 目录

`kokoro-agent/` 是仓库/distribution，`src/kokoro_agent/` 是标准 Python `src layout` 下的 import
package；这只是打包与 import 隔离，不是业务架构套娃。

    src/kokoro_agent/
    ├── agents/          完整、可复用的 DeepAgents Agent 定义
    ├── features/        对外 Feature 与 Agent 组合声明
    ├── agent_factory.py 唯一内部装配入口
    ├── swarm.py         official langgraph-swarm 薄接线
    ├── execution/       Run、控制、HITL、事件与终态
    ├── worker/          Redis ingress、共享服务、claim、recovery、drain
    ├── tools/           GA 固定工具、工具集合与 middleware
    ├── skills/          Capability Skill 只读 backend adapter
    ├── clients/         Capability/Storage/Model 等 public clients
    ├── sandbox/         DeepAgents backend 与 S3Workspace adapter
    ├── storage/         RunLedger、LangGraph Store 与 checkpoint adapter
    ├── mcp/             MCP 连接与工具接线
    ├── model/           模型与 provider adapter
    └── prompts/         静态 prompt 资产

禁止新增 ga、factory、framework、compiler、runtime、ports、根目录 agent.py、deepagents.py、graph.py、
flow.py、state.py 或自定义 Graph/State。配置只负责接线，Compose/Kubernetes 不决定 Feature、
Agent 或权限。

## 9. 实施顺序与验收

1. Root contract 生成 feature_key 和 ExecutionIdentity，GA 只消费生成物。
2. 在 agents/ 定义 general、music 等完整 Agent。
3. 在 features/ 定义 chat、music 以及真实需要的组合 Feature。
4. 让 AgentFactory 的单 Agent 路径直接调用 create_deep_agent。
5. 只有出现真实 peer handoff 需求时才接入官方 Swarm。
6. 接入 RunLedger、聊天事实、Workbench 和 Capability/Storage public clients。
7. 可视化 Builder 只生成同一套 Agent/Feature 声明，复用 AgentFactory，不进入 Session 或 Run。

验收必须证明：

- music 可单独运行，也可被组合 Feature 复用；
- 多 Agent 交接只由 official Swarm 提供；
- DeepAgents 是唯一 Agent loop、native state 和 checkpoint owner；
- Feature/Agent API 没有 deps、namespace、thread、binding、release 或 version；
- chat_messages/chat_events 可支撑历史、实时和 replay；
- 外部 client 暂不可用时，未声明其操作的 Feature 仍可执行；
- deliver 只在 Agent 显式声明且 Storage `DeliveryClient` 可用时装配；通过
  DeepAgents backend 读取 workspace，不直写 S3/MinIO/PackageStore；
- 计费以 accepted invocation 次数幂等结算。
