# kokoro-agent 模块说明

状态：GA 首发执行底座，2026-08-27。

总体架构以 [42 GA 核心架构](../technical/42-ga-core-architecture.md) 和
[36 GA 技术方案](../technical/36-ga-final-agent-technical-plan.md) 为准；本页只说明子仓的
owner、入口和目录，不复制 Root wire 契约。

## 1. 定位、目标与非目标

`kokoro-agent` 是基于 DeepAgents 的闭环执行底座。它从 Redis 接收 Root 生成的
`LaunchRunRequest`，按可信 `feature_key` 找到 GA 内置 Feature，由 `AgentFactory` 直接调用
DeepAgents；需要 peer 交接时使用官方 `langgraph-swarm`。

```text
LaunchRunRequest
  -> Redis worker
  -> RunLedger claim
  -> FeatureCatalog
  -> AgentFactory
  -> create_deep_agent(...) 或 official create_swarm(...)
  -> native state/checkpoint
  -> GA chat_messages/chat_events
  -> Root Chat query boundary -> kokoro-session / AG-UI / SSE
```

DeepAgents 拥有 Agent loop、native state、subagent、interrupt、backend 和 checkpoint。GA
拥有 Feature/Agent 声明、装配、Run 生命周期、外部 client 接线和产品事件事实；GA 不实现
第二套 Runtime、Graph、State、router 或编译器。

## 2. 输入、输出与公开契约

最小 canonical `CanonicalRunRequest` 由 Session 负责把业务命令投递为 Root generated `LaunchRunRequest` 及 control 请求；输出是 GA durable facts、公开
`ProductEvent` 投影和明确的运行状态。调用方不提交 Agent/Skill/MCP/graph 配方，也不读取
Agent 的 native checkpoint、Redis key、数据库表或 S3 object key。

## 3. 生命周期与正确性不变量

Run 先经过单 active-run admission 和 durable claim，之后才产生第一条 RunPhase、checkpoint、
provider submit 或 ProductEvent。重复请求只返回 receipt；terminal 后普通消息才创建新的 Run，
迟到结果不能复活已终止的 Run 或副作用。

## 4. 实际目录与职责

目标源码树：

```text
src/kokoro_agent/
├── contract/        Root generated contract facade
├── worker/          Redis ingress、claim、recovery、readiness
├── agents/          DeepAgents Agent 定义
├── features/        Feature 组装声明
├── clients/         外部 owner public contract 窄协议
├── agent_factory.py 唯一内部装配协调器
├── execution/       Run、control、HITL、事件投影与终态
├── tools/           GA 固定工具、工具集合与 middleware
├── skills/          Capability Skill 只读 backend adapter
├── mcp/             MCP 配置、连接与 egress
├── sandbox/         Workbench 与 S3-compatible Workspace
├── model/           模型 provider adapter
├── storage/         RunLedger、Store 与 checkpoint adapter
├── prompts/         静态 prompt 资产
├── config.py         runtime 接线配置
├── config_file.py    文件配置读取
├── metrics.py        metrics 适配
├── observability.py  trace、private audit
└── hitl/             HITL 实现边界
```

### GA 拥有

- 完整 Agent 定义和对外 Feature 组装；
- `AgentFactory` 与官方 Swarm 接线；
- RunLedger、lease、HITL、恢复、workbench；
- Agent Skill 声明解析与 DeepAgents 原生 Skill backend 接线；
- `chat_messages`、`chat_events` 和安全 ProductEvent；
- Redis ingress 与实时发布。

### 外部 owner

```text
IAM/Session  -> ExecutionIdentity、会话鉴权和浏览器交付
Capability   -> 用户/项目/session Skill CRUD/path、MCP registry/授权
Storage      -> package bytes、Asset、Artifact 生命周期
Studio       -> Job/provider 生命周期
Billing      -> invocation 计费与结算
Model        -> 模型目录与 provider 句柄
```

GA 只调用这些 owner 的 public contract，不读取外部数据库、Redis key 或 S3 bucket。标准 CLI 不接 owner 私库；部署在 worker 启动时注入可选 public clients，缺席时基础 Agent 继续运行。`S3Workspace`
是 GA Workbench 的 S3-compatible adapter；MinIO、AWS S3、Ceph RGW 等实现可以替换。

GA 的持久边界是 `durable safe ProductEvent outbox + private evidence + terminal claim`；Root
generated `ProductEvent` oneof 只承载可投影产品事实。`bounded-fanout WorkItem` 只是父 Run 的
私有账本事实，不是新的 public subtask API。`FeatureEvalSuite、质量/成本 baseline` 属于离线
发布证据，不进入 Session 或 native state。

## 5. 一次 run 的装配语义

```text
music      -> music Agent
chat       -> general Agent
music_chat -> general Agent + music Agent + official handoff
```

`Agent` 是完整、可复用的 DeepAgent 能力；`Feature` 是业务产品能力的唯一组装入口。Music
可以独立对外，也可以被组合 Feature 复用。无需 composer/arranger/reviewer、Role、Team 或
额外的业务编排对象。

Agent 文件只声明 prompt、固定工具、默认 Skill/MCP、是否支持产物交付与 native
subagent 需求。Feature 文件只
声明所选 Agent、入口 Agent、Feature 级配置和 peer handoff。Factory 通过 Capability client 解析
Agent 声明的 Skill，再交给 DeepAgents 原生 SkillsMiddleware / `read_file`；用户/项目/session Skill CRUD 仍由 Capability 完成。

`delivery=True` 是 Agent 的明确能力声明。Factory 只在部署注入 Storage
`DeliveryClient` 时挂载 deliver tool；工具经该 Agent 同一 DeepAgents backend 读取
workspace 字节，由 Storage facade 闭环 upload/asset/artifact。GA 不写 bucket key，
不把 Skill package `PackageStore` 当交付面；client 缺席时不挂载空壳工具，基础
Agent 循环仍可运行。

## 6. 数据 owner、唯一 writer 与当前原型边界

外部请求只携带：

```text
feature_key + session_id + input + ExecutionIdentity (+ opaque trace/asset references when the Root contract declares them)
```

请求不携带 Agent、member、prompt、Tool、Skill、MCP、sandbox、namespace、LangGraph thread 或
依赖句柄。GA 在 ingress 处从稳定的 `ExecutionIdentity.tenant_ref + subject` 派生内部 `RuntimeNamespace`；actor/assertion 仅用于授权、审计和计费，并以
`session_id` 作为 DeepAgents checkpoint 的 thread 标识。

GA 不继承或包装 DeepAgents 原生 state，也不定义 Session 配置对象或 Agent 绑定。LangChain native message/
checkpoint ID 与 GA 的 `chat_message_id/chat_event_id` 分离；GA 不修改 LangChain checkpoint 表。

同一 Session 只有前一 Run terminal 后，下一次普通消息才继续同一 native checkpoint；fork 才创建
新的 Session、thread 和 state。

`ExecutionIdentity.subject -> billing_subject`；`RuntimeNamespace`、actor、IAM assertion 与短时
attestation 不传给 Billing。GA 按 provider 接受调用计数，`ModelInvocationAccepted` 是 durable
usage receipt；token 仅用于 provider 成本、预算和诊断。cancel 先停止新调度，in-flight accepted
仍只 capture 一次，`submit_unknown` 后台 reconcile，但不重开 Product Run。

## 7. Sandbox workspace 与 S3-compatible 边界

GA Workbench 使用 S3-compatible workspace adapter，默认部署可接 Docker MinIO，
也可接 AWS S3 或 Ceph RGW。它保存 GA workspace；Skill 是 `/.skills/` 逻辑 backend
route，不复制进 workspace。Storage 仍是 Asset/Artifact lifecycle owner，GA 不把 workspace
写入 Storage 表。
当前 V1 源码说明（不是目标编排 contract）：`sandbox/archive.py` + `S3Archiver` 只是原型旁路快照，
目标的 thread workbench 由 GA `WorkbenchPersistence` 管理；`tests/test_workbench_persistence.py`
验证其 durable 行为，`workspace_prefix` 是 GA-only logical root。

## 8. 失败语义与安全边界

Redis ingress、claim、lease、checkpoint、public client 或 Workbench 不可用时按对应错误返回，
不使用进程内 Map 绕过 durable boundary；未声明外部操作的 Feature 仍可运行。secret、raw provider
payload、native state 和内部路径不得进入 ProductEvent。

## 9. 可观测性、诊断与无 client 行为

每个 Run 记录 request/command identity、trace、claim、invocation、terminal 和 replay 事实；
日志只输出脱敏标识。缺少 Capability/Storage client 时，只有实际需要该能力的 Feature 被拒绝，
无关 Feature 不被强行绑定。

`RuntimeNamespace`、actor、IAM assertion 与短时 attestation 不传给 Billing；`ExecutionIdentity.subject -> billing_subject`。

## 10. 验收矩阵（设计 100 分）

架构 test 检查目标目录与依赖方向；unit test 覆盖 Factory、Skill/MCP reader、scope、control
和失败语义；integration/contract test 覆盖 public client 与 owner contract；smoke/E2E 覆盖
Redis、MinIO/S3-compatible workspace、Run terminal、HITL、replay 和 cleanup。

## 11. 验证命令与变更门禁

子仓运行 `uv run pytest -q`、`uv run ruff check .` 和 `uv run pyright`；根仓运行 generated
contract check、`python3 scripts/verify-backend-design.py` 与 Slice A native runner。所有 Root
wire 变更先更新 contract source 和 provenance，再更新 client facade 与测试。

### 目录证据（源码树）

`kokoro-agent/` 是仓库/distribution，`src/kokoro_agent/` 是标准 Python `src layout` 下的 import
package，不是两层业务架构。

```text
src/kokoro_agent/
├── agents/          完整、可复用的 DeepAgents Agent 声明
├── features/        对外 Feature 组装入口
├── agent_factory.py 唯一内部装配入口，直接调用 DeepAgents
├── swarm.py         official langgraph-swarm 薄接线
├── execution/       Run、恢复、HITL、事件转换与终态
├── worker/          Redis ingress、共享服务、claim、recovery、readiness
├── tools/           GA 固定工具、工具集合和 middleware
├── skills/          Capability Skill 只读 backend adapter
├── clients/         Capability/Storage/Studio/Billing/Model public clients
├── sandbox/         DeepAgents backend 与 S3-compatible Workspace
├── storage/         RunLedger、LangGraph Store、checkpoint adapter
├── mcp/             MCP 连接与工具接线
├── model/           模型选择与 provider adapter
├── prompts/         静态 prompt 资产
└── observability.py metrics、trace、private audit
```

不新增 `ga/`、`factory/`、`framework/`、`compiler/`、`runtime/`、`ports/`、根目录 `agent.py`、自定义
Graph/State、Binding、Release/Version 或请求级 `deps`。

### 验收门补充

- `music` 可单独运行，也可成为组合 Feature 的 Agent；
- 多 Agent 交接只使用官方 Swarm；
- DeepAgents 是唯一 Agent loop、native state 和 checkpoint owner；
- Feature/Agent API 不出现 namespace、thread、binding、release/version 或 deps；
- GA 聊天历史和 replay 来自 `chat_messages/chat_events`；GA internal safe
  envelope 不直写 Session browser-live stream，两者 generated envelope/seq owner 分离；
- 计费按 provider accepted invocation 次数，以稳定 `invocation_id` 幂等结算。
