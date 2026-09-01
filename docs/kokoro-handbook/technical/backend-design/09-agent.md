# kokoro-agent 设计卡

状态：GA 首发执行底座，2026-08-27。

总体裁决见 [42 GA 核心架构](../42-ga-core-architecture.md)、[36 GA 技术方案](../36-ga-final-agent-technical-plan.md)。
本卡只说明 `kokoro-agent` 的真实职责、命名和目录，不再引入第三套 Agent 概念。

## 定位

`kokoro-agent` 是一个**基于 DeepAgents 的闭环执行底座**：

```text
LaunchRunRequest
  -> Redis
  -> worker 认领 Run
  -> FeatureCatalog(feature_key)
  -> AgentFactory
  -> DeepAgents create_deep_agent(...)
     或官方 langgraph-swarm
  -> native state/checkpoint
  -> GA chat_messages/chat_events
  -> Redis live -> Session / AG-UI / SSE
```

DeepAgents 负责 Agent 的实际运行；GA 只负责产品能力声明、装配、Run 生命周期、外部能力接线和
用户可见事实。GA 不实现自己的 loop、Graph、State、router 或编译器。

## 架构等级

这是执行底座级设计，不把 `kokoro-agent` 强行改造成完整 DDD 领域服务。Agent/Feature 是
静态能力声明，Run/Execution 是运行语义；DeepAgents/LangGraph 继续拥有 loop、native
state、checkpoint、interrupt 和原生 subagent。GA 只在这些边界上提供装配、持久事实、恢复和
产品事件投影。

## 核心闭环与外部边界

唯一生产闭环是：

```text
LaunchRunRequest -> Redis ingress -> Run claim -> FeatureCatalog -> AgentFactory
-> native DeepAgents/Swarm -> durable GA facts -> Session projection
```

外部
请求只能选择可信 `feature_key` 并携带输入与 `ExecutionIdentity`；Agent、Skill、MCP、graph、
namespace 和 provider 配方均不由 caller 传入。

## 1. 四个核心名词

| 名称 | 精确定义 | 明确不表示 |
|---|---|---|
| `Agent` | 一个完整、可独立运行、可复用的 DeepAgents 能力声明 | 不是角色、Session 或 Run |
| `Feature` | 一个对外产品能力的 Agent 组装声明 | 不是 Runtime、Graph 或 State |
| `AgentFactory` | GA 内部唯一装配器，调用官方 DeepAgents/Swarm API | 不是 endpoint、依赖容器或请求配置 |
| `Run` | 一次调用的生命周期与持久事实 | 不是 Agent 定义或能力选择器 |

`music` 是完整 Agent，可以直接成为 `music` Feature，也可以被组合 Feature 复用。无需
`composer`、`arranger`、`reviewer`、`Role`、`Team` 或额外的业务编排层。

## 3. Feature 与 Agent

```text
chat       -> general Agent
music      -> music Agent
music_chat -> general Agent + music Agent + 官方 handoff
```

### Agent 文件

`agents/general.py`、`agents/music.py` 各自只声明：

- system prompt；
- 固定 GA 工具；
- 默认 Skill/MCP；
- 必要时的 DeepAgents native subagent。

Agent 不读取 Session、Redis、Capability/Storage 数据库，也不处理产品交付。

### Feature 文件

`features/*.py` 是唯一业务组装入口。每个文件产出一个对外 `Feature`，可选择一个或多个完整
Agent，并声明：

- 入口 Agent；
- 该产品需要的 Agent 配置（可通过 `Agent.configured(...)` 生成不可变副本）；
- peer handoff 边。

这些声明是 GA 内置代码/受管目录，不是浏览器或 Session 传入的 JSON 配方。

单 Agent Feature 直接走 `create_deep_agent`；只有多个 Agent 需要在同一用户会话中互相接手时，
才使用官方 `langgraph-swarm`。需要后台隔离工作时，使用 DeepAgents native subagent。

## 4. AgentFactory

worker 启动时构造一个 `AgentFactory`，共享模型、checkpointer、RunLedger、workbench 和 public
clients 作为实例字段保存。它们不会出现在 Feature/Agent 的方法签名中，也不命名为 `deps`。

Factory 只有两条构造路径：

```text
Feature.agents == 1
  -> create_deep_agent(...)

Feature 声明 peer handoff
  -> 每个 Agent 调用 create_deep_agent(...)
  -> 官方 create_handoff_tool
  -> 官方 langgraph_swarm.create_swarm(...)
```

Factory 内部可以拆出工具、审批、prompt、Skill materialization 等实现文件；这些文件只是
DeepAgents 参数准备，不是新的框架层。

## 5. 状态、身份和恢复

- 单 Agent/subagent 使用 DeepAgents 原生 state/checkpoint；Swarm 使用官方 `SwarmState`。
- GA 不继承或包装 DeepAgents 原生 state，也不定义任何自有 state 子类。
- `ExecutionIdentity` 只用于授权、审计和 Billing；GA 在 ingress 处派生内部 `RuntimeNamespace`。
- caller 不传 `namespace`、LangGraph `thread_id`、Agent、Skill、MCP 或 graph 配方。
- `ExecutionIdentity(tenant_ref, actor, subject, identity_assertion_ref)` 是唯一入站身份形状，Agent 不接收 caller namespace。
- `thread_id` 由 GA 内部从 `session_id` 得到；同一 Session 的普通消息仅在前一 Run terminal 后
  继续同一 native checkpoint，fork 才创建新的 Session/thread/state。

LangChain 的 `Message.id`、`thread_id`、`checkpoint_id` 与 GA 的 `chat_message_id`、
`chat_event_id` 完全分离；GA 不读取或改造 LangChain checkpoint 表。

## 数据 owner 与不负责项

### GA 拥有

- Feature/Agent 声明和 AgentFactory；
- DeepAgents、LangGraph、官方 Swarm 的原生接线；
- RunLedger、lease、control、HITL、恢复和 workbench；
- GA 默认 Skill、`find_skills/load_skill`；
- `chat_messages`、`chat_events` 和安全 ProductEvent；
- Redis ingress 与实时发布。

### GA 通过 public contract 使用

```text
Capability -> 用户/项目/session Skill CRUD、logical path、MCP registry/授权
Storage    -> package bytes、Asset、Artifact 生命周期
Studio     -> Job 创建与状态
Billing    -> provider accepted invocation 计费（按次数）
Model      -> 模型目录与 provider 句柄
```

`S3Workspace` 只是 GA Workbench 的 S3-compatible adapter。当前可用 MinIO，未来可以切换 AWS S3、
Ceph RGW 或其他兼容实现；它不是 Storage Artifact owner。

`WorkbenchPersistence` 是 GA thread workbench 的唯一持久化接口；当前 V1 `S3Archiver` 只是旁路
快照。目标测试包含 `tests/test_workbench_persistence.py`，并验证 `workspace_prefix` 与
`RuntimeNamespace:session_id` 的连续性。Skill source 只按 CA subject/session path 精确匹配，
actor 不形成个人 overlay；已 claim run 的 recovery/HITL/control 只对照 durable locator/ledger，
不等待新的 identity。后续新 Launch 才用当前 identity；已接受 delete 的 Cleanup 改用 delete-time durable。

`FeatureCatalog` 在 worker warm 时注册受管 Feature；Run 只按可信 `feature_key` 取静态声明，
然后交给同一个 `AgentFactory`。Factory 直接调用 DeepAgents `create_deep_agent`，需要 peer
交接时再调用官方 `langgraph-swarm`；GA 不缓存、编译或注册自有 Graph。首次 target bootstrap
由 GA 从 `ExecutionIdentity` 派生内部 `RuntimeNamespace` 和 thread 定位，caller 不可指定。

GA 不读取 Capability/Storage/Model/Session 的内部数据库、Redis key、bucket、checkpoint
表或 provider SDK 类型；未声明外部操作的 Feature 不因旁路服务不可用而改变核心执行语义。

## Sandbox workspace 与 S3-compatible 配置

Sandbox 的工作目录由 GA Workbench 管理，`S3Workspace / WorkbenchPersistence` 是 deployment
adapter，不是 Storage Artifact writer。默认开发环境可连接 S3-compatible Docker MinIO；AWS S3、
Ceph RGW 等通过相同的 S3 adapter，差异只在 endpoint、credentials、region 与 path-style 配置。
workspace prefix 由 GA 从 `RuntimeNamespace:session_id` 派生，调用方不能指定 bucket、object key
或 provider。

## 可执行目录与语义拓扑

`kokoro-agent/` 是仓库/distribution，`src/kokoro_agent/` 是标准 Python `src layout` 下的 import
package。这个重复视觉来自 Python 打包约定，不代表 GA 还有一层同名架构。

```text
src/kokoro_agent/
├── agents/          完整、可复用的 DeepAgents Agent 声明
├── features/        对外 Feature 组装入口
├── agent_factory.py 唯一内部装配入口，直接调用 DeepAgents
├── swarm.py         official langgraph-swarm 薄接线
├── execution/       Run、恢复、HITL、事件转换与终态
├── worker/          Redis ingress、共享服务、claim、recovery、readiness
├── tools/           GA 固定工具、工具集合和 middleware
├── skills/          GA 默认 Skill、find/load、workbench mount
├── clients/         Capability/Storage/Studio/Billing/Model public clients
├── sandbox/         DeepAgents backend 与 S3-compatible Workspace
├── storage/         RunLedger、LangGraph Store、checkpoint adapter
├── mcp/             MCP 连接与工具接线
├── model/           模型选择与 provider adapter
├── prompts/         静态 prompt 资产与渲染
└── observability.py metrics、trace、private audit
```

禁止新增：`ga/`、`factory/`、`framework/`、`compiler/`、`runtime/`、`ports/`、根目录 `agent.py`、
自定义 Graph/State、Session binding/release/version 字段或请求级 `deps`。

## 依赖规则与可自动化门禁

依赖方向固定为 `worker -> features -> agent_factory -> DeepAgents/official Swarm`，而
`execution -> storage + narrow public clients`，`skills/sandbox -> public clients`。
`clients/` 只消费 Root/owner generated contracts；不导入外部 repository 的数据库模型。
Architecture test 必须检查唯一入口、禁止业务层、public client 边界、Redis fail-closed、
S3-compatible 配置和 generated contract provenance。

## 公开契约

Root `kokoro/agent/v1` contract 是跨仓 wire authority。GA 对外暴露 `LaunchRun`、control、
evidence/projection acknowledgement 等明确动作；私有 native event、checkpoint、prompt、
secret 和 workbench path 不进入公共契约。Capability、Storage、Model、IAM 只通过各自 v1
generated client facade 消费；契约新增只追加 field/RPC/enum，不复用 field number。

## 100 分证据

- `FeatureCatalog` 只注册受管 Feature，单 Agent 使用 `create_deep_agent`，peer handoff 使用官方 Swarm。
- 同一 Session 只有一个 active outer Run；Run claim、lease、HITL、恢复和 terminal 都可审计且幂等。
- GA ProductEvent 先落 durable fact 再发布，terminal 后不再产生普通消息或控制副作用。
- dynamic Skill 经过 Capability client 解析后原子写入 durable thread workbench；恢复读取副本而不是重新读取外部 source。
- `S3Workspace / WorkbenchPersistence deployment adapter config` 只属于部署接线，不把它们解释成 Agent/Feature 配置。
- 架构、unit、integration、contract、smoke 和 generated provenance tests 共同覆盖上述不变量。
- 只读 `kokoro-agent inspect` 直接检查生产使用的 `FeatureCatalog`，不会形成第二份 Agent manifest
  或允许 caller 注入配置。

## 当前源码审计与首发前置条件

当前 Agent 接线由 `agents/`、`features/`、`clients/` 和 `AgentFactory` 承担；源码中的第二个
`factory/` 已删除，原实现已按真实 owner 归入 `worker/services.py`、`tools/`、`prompts/` 与
`agents/subagents.py`，没有兼容 re-export。Architecture verifier 已锁定 `agent_factory.py` 为
唯一 DeepAgents 构造点，后续 Agent test suite、contract tests 和 Slice A native E2E 只覆盖
这一条 DeepAgents-first 链路。

## 8. 验收门

- `music` 可以独立运行，也可以作为组合 Feature 的 Agent；
- 多 Agent 交接只使用官方 Swarm；
- DeepAgents 是唯一 Agent loop 和 native state owner；
- Feature/Agent API 不出现 namespace、thread、binding、release/version 或 deps；
- 外部 Capability/Storage/Studio 暂不可用时，未声明这些操作的 Feature 仍可运行；
- 用户可见历史和 replay 事实来自 GA `chat_messages/chat_events`，Redis 只做实时传输；
- 计费以 provider accepted invocation 次数结算，使用稳定 `invocation_id` 幂等。
- `RuntimeNamespace` 这个内部键绝不用于扣积分；`ModelInvocationAccepted` 是 billing usage receipt。
- cancel 先停止新调度、in-flight accepted 仍只 capture 一次、`submit_unknown` 后台 reconcile 但不重开 Product Run。
