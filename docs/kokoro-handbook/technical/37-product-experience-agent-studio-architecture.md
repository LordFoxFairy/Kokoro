# 37. Kokoro 统一入口、App、Feature 与 Agent 产品架构

状态：当前跨产品总体方案，2026-08-27。

本页只定义产品入口如何选择 GA 的 Feature。GA 的执行细节以 [42 GA 核心架构](42-ga-core-architecture.md)
和 [36 GA Agent 最终技术方案](36-ga-final-agent-technical-plan.md) 为准。

## 1. 四个词足够表达完整链路

```text
App      = 产品入口（Chat、Music、Image、Video、Code）
Feature  = 一件对外产品能力及其 Agent 组装
Agent    = 一个完整、可复用的 DeepAgents 能力
Run      = 一次用户调用
```

不再增加第二套业务编排对象。Feature 就是业务
组装层；DeepAgents 就是执行层。

```text
Browser / API
  -> App / Feature exposure
  -> Session 验证 Feature 与 ExecutionIdentity
  -> Root LaunchRunRequest(feature_key, message_id, content, identity)
  -> Redis internal envelope input={message_id,content}
  -> GA AgentFactory
  -> 一个 Agent：create_deep_agent(...)
     多个 peer：create_deep_agent(...) + official langgraph-swarm
  -> GA chat facts + Redis live
  -> Session replay / AG-UI / SSE
```

## 2. Feature 与 Agent 的组合

```text
chat       -> [general]
music      -> [music]
music_chat -> [general, music] + general <-> music handoff
```

- 单 Agent Feature 是默认路径，最适合快速上线一个 AI Music site 或其他垂类站点。
- Agent 可以直接对外，也可以被多个 Feature 复用；复用的是静态能力声明，不复用 Session 或
  checkpoint。
- 只有需要在同一用户会话中把控制权交给另一个 Agent 时，才使用官方 Swarm。
- 一个 Agent 需要后台隔离工作时，使用 DeepAgents 原生 `subagents`；这不是 peer handoff，
  也不创建新 Session。
- 不为了音乐能力拆出 composer、arranger、reviewer；这些若未来确有独立能力，应成为独立
  Agent，再由 Feature 选择是否组合。

## 3. App 只做产品映射

同一套后端可以服务多个 App：

```text
music.example.com -> Music App -> music Feature
chat.example.com  -> Chat App  -> chat Feature
统一入口          -> AppFeatureExposure -> global feature_key
```

域名、品牌、导航、SEO 和套餐属于 App/System；Feature key 是可信产品上下文，不是浏览器
任意提交的 Agent 参数。Session 首次创建时固化已验证的 Feature，后续消息沿用；改变产品能力
应创建新的 Feature Session，而不是在已有 Session 中换 Agent 或换图。

## 4. 能力 owner 边界

```text
GA                 -> DeepAgents、固定工具、default Skill、find/load、RunLedger、workbench、ProductEvent
Capability client  -> 用户/项目/session Skill 与 MCP 的 CRUD、可见性和授权路径
Storage client     -> bytes、Asset、Artifact 生命周期
Studio client      -> Job、provider callback、Job 状态
Billing client     -> accepted model invocation 的计费结算
Session            -> 产品消息、历史、鉴权、replay、AG-UI/SSE
```

Agent/Feature 只声明需要的能力；请求不携带 Skill/MCP 定义、凭据、namespace、thread 或 graph
配方。GA 在已授权的 Run 快照中装配能力，外部 client 缺席时，不依赖它的 Feature 仍可执行。

`S3Workspace` 只是 GA workbench 的 S3-compatible adapter。当前可使用 MinIO，未来可替换其他
S3-compatible 服务；它不拥有 Storage Artifact。

## 5. 状态、事件和交付

- DeepAgents native state/checkpoint 或官方 `SwarmState` 是唯一执行状态；GA 不继承、包装或
  重新命名它们。
- GA 的 `chat_messages` 是用户可见历史，`chat_events` 是 durable realtime/replay 事实；
  Redis 只负责实时传输。
- AG-UI 是 Session 对 Web 的交付协议，不进入 GA Agent state。
- Studio 可同时提供 direct view 与 session card；GA 只发安全的 Job link，Session 负责产品卡片。
- 同一 Session 只有前一 Run terminal 后才继续 native checkpoint；fork 才创建新的 Session、
  thread 和 state。

## 6. 未来可视化组装

可视化 Builder 只编辑/生成同一套 `Agent` 与 `Feature` 声明，经过校验后交给同一个
`AgentFactory`。Builder 不成为运行时，不向 Session/Run 写入图、版本、binding 或成员配置；
运行中的 checkpoint 也不会被 Builder 改写。

这样新增一个垂类产品只需：

1. 定义一个完整 Agent（或复用已有 Agent）；
2. 定义一个最小 Feature；
3. 在 App 中暴露该 Feature key；
4. 由 GA AgentFactory 直接构造 DeepAgents。

不新增 worker、runtime、编排服务或第二套状态系统。

## 7. Cross-owner closure evidence

产品架构不创建 `CapabilityGrant`。能力授权事实由 Capability public contract 提供，且
CA (kokoro-capability): subject/session Skill logical path, visibility, CRUD；GA 只在当前
Run 中解析并装配，不把授权写进 Session 或 Agent state。

Studio: CreateJob/QueryJob and Job lifecycle 由 Studio owner 管理；Storage 拥有 Asset/Artifact lifecycle，
包括 bytes、scan、immutable artifact 和短期引用。GA durable usage outbox → Billing 只记录已接受的
ModelInvocation 事实，Billing 不反向控制 Agent execution。

WorkItem 仍归同一父 Run；它是 GA 内部 bounded-fanout recovery ledger，不是 public task/subtask
资源。`deployment-only drain_required` 只表示部署排空状态，不进入 Feature、Session、Agent 或
Capability resource contract。

没有 `CapabilityGrant`；`deployment-only drain_required` 不是业务资源字段。产品层统称这一份 GA 执行态为 `ConversationState`。
deployment-only `drain_required` 只属于部署排空控制，不属于产品能力或业务状态。
GA 的 CreateJob effect 只得到 durable `JobRef`；直接 Studio 表单直接使用同一个 Studio Job，
不复制 GA Run 或 Session 状态。
