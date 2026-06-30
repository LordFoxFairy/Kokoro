# Agent 业务编排多期技术方案

本文约束 `kokoro-agent`、`kokoro-session`、`kokoro-web` 如何承载业务编排。
它不替代 music、credit、model、artifact 等平台域文档；这些域仍拥有自己的
数据和规则。本文只定义 agent runtime 如何调用、追踪和展示这些能力。

## 总原则

```text
Web 是入口和投影。
Session 是会话、run、message、event、snapshot 真源。
Agent 是执行和编排 runtime。
平台域拥有业务事实：credit、model、artifact、job、music project。
```

Agent 可以编排业务能力，但不能拥有业务账本、产物库、模型目录或 provider
订单。所有业务副作用必须通过 capability adapter 调用对应服务。

## 分期总览

```text
P0  Runtime 闭环
  目标：通用聊天主链路可跑、可恢复、可审计。
  范围：AgentRunInput、snapshot-first、message projection、HITL、
       manifest-first subagent gate。

P1  Capability Orchestration
  目标：通用 Agent 能在一次 run 内调用受治理的业务能力。
  范围：capability manifest、toolMode/approvalPolicy、job/artifact refs、usage refs。

P2  Music Entry
  目标：General Chat 能创建轻量 music job，Music Studio 能复用同一编排入口。
  范围：general.music.generate、studio.music.generate、music job card、artifact handoff。

P3  Professional Agents
  目标：music/video/image/code 等专业 Agent 作为 run-scoped capability 接入。
  范围：specialist agent profile、handoff event、project/job/artifact 上下文。

P4  Skill/MCP Hub Productization
  目标：官方/用户/workspace skills 和 MCP 连接形成可管理、可授权、可计费能力。
  范围：hub 管理、授权、审计、市场化，不在 V1 runtime 阻塞项内。
```

## Capability Model

业务能力进入 agent 时必须先被 session/platform 编译成 manifest。

```text
CapabilityRef
  capabilityKey
  source: builtin | skill | mcp | studio | specialist_agent
  displayName
  inputSchema
  outputSchema?
  risk
  billingPolicyRef?
  approvalRuleRef?
  artifactPolicy?
```

示例：

```text
general.music.generate
studio.music.generate
studio.music.extend
artifact.create
mcp.github.create_issue
skill.lyrics.rewrite
specialist.music.arrange
```

Agent 只能看到 manifest 中列出的 capability。未列出的能力本轮不可见。

## Lock And Replaceable Boundaries

三仓之间稳定的是 manifest、lock、policy 和 event projection。内部实现可以替换，
但不能把替换细节泄漏给 Web 或 session。

```text
稳定契约：
  AgentRunInput
  SkillLockEntry / CapabilityLockEntry
  ApprovalPolicy / BackendPolicy
  AgentEvent -> SessionEvent projection

可替换实现：
  DeepAgents adapter
  LangChain model/runtime adapter
  MCP adapter
  skill storage/loader backend
  execution sandbox adapter
  capability adapter
```

Skill/capability 在进入 AgentRunInput 前必须冻结：

```text
SkillLockEntry
  skillId
  source
  sourceType
  sourceUrl
  ref?
  skillPath
  folderHash
  version
  resolvedAt

CapabilityLockEntry
  capabilityKey
  source
  version
  schemaHash
  policyHash
  resolvedAt
```

Agent 不运行“最新版本”，只运行本次 manifest 锁定的版本。后续替换 skill
来源、MCP adapter、sandbox provider 或 specialist agent，只要 lock 和
event projection 不变，session/web 不需要跟着改。

## Capability Invocation

Agent 调用业务能力时，不直接写业务库：

```text
Agent
  -> capability tool
  -> adapter HTTP/RPC
  -> owning service
  -> job/artifact/credit/model/provider
```

capability tool 是 DeepAgents/LangChain tool wrapper，不是 Kokoro 自研工具
调度器。wrapper 的职责只有参数校验、idempotencyKey、policy/approval、
调用 owning service、返回 ref。

调用输入：

```text
CapabilityInvocation
  invocationId
  siteId
  workspaceId
  projectId?
  sessionId
  runId
  userId
  capabilityKey
  idempotencyKey
  input
  costContext
  artifactContext
  traceContext
```

调用输出：

```text
CapabilityResult
  invocationId
  status: queued | running | succeeded | failed | cancelled
  summary
  jobRef?
  artifactRefs[]
  usageRef?
  error?
```

## Event Projection

业务能力调用在浏览器里仍通过 session event 展示，不新增 web 直连。

```text
tool.invoked
  name = capabilityKey
  args = sanitized input summary

tool.returned
  result = human-readable summary
  artifactRef/jobRef 放 payload refs，不放大对象 body

subagent.started / subagent.finished
  专业 Agent 或 specialist agent 编排时使用

message.completed
  assistant 用自然语言解释结果
```

P1 可以先复用 tool event。P3 若需要更丰富的 studio job activity，再扩展
browser-facing session event，但必须从 `contract/events.yaml` 生成。

## Cost Context

Agent 不扣费，只携带上下文：

```text
CostContext
  featureKey
  quoteRequired
  holdRequired
  usageGroupId
  parentRunId
  parentJobId?
```

业务服务负责：

```text
quote
hold
capture
release
usage record
ledger
```

Agent 只能展示 quote/hold/capture 的结果引用，不能直接写账本。

## Artifact Context

```text
ArtifactContext
  workspaceId
  projectId?
  parentArtifactId?
  visibility
  allowedTypes[]
```

业务服务负责创建 artifact/job/result。Agent 只接收 ref：

```text
JobRef
  jobId
  capabilityKey
  status

ArtifactRef
  artifactId
  artifactType
  title
  previewUrl?
```

大对象、音频、视频、图片、工程文件都不能进 SSE body。

## Music Entry

Music 有两个入口，但复用同一个 capability 编排思想。

### General Chat Entry

```text
用户：「帮我做一首轻快广告歌」
Web -> session POST message
session -> agent AgentRunInput(capabilities includes general.music.generate)
agent 生成 MusicBrief
agent 调用 general.music.generate capability
music/job service 创建 job + hold
session SSE 展示 job card
assistant 回复可进入 Music Studio 精修
```

General Chat 的目标是轻量生成和解释，不承载完整 Studio 参数面。

### Music Studio Entry

```text
用户在 Music Studio 选择参数并点击生成
Web -> session/studio endpoint 创建 run 或 job
session 构建 AgentRunInput(capabilities includes studio.music.generate)
agent 可参与 prompt/lyrics/style 编排
music/job service 创建 job + hold + provider request
Web Studio 展示 job progress、artifact、版本
```

Music Studio 的目标是专业控制面。它可以复用 agent 编排，但 UI 和状态展示
不等同 General Chat。

## Music Brief

General Chat 到 Music 的最小结构：

```text
MusicBrief
  prompt
  language?
  lyrics?
  styleTags[]
  mood?
  tempo?
  vocalMode?
  durationHint?
  negativePrompt?
```

Agent 可以生成 `MusicBrief`，但 provider 参数归 music service 适配，不让 agent
直接拼 provider 原始参数。

## Studio Agent Profile

P3 专业 Agent 不应是硬编码 prompt：

```text
SpecialistAgentProfile
  profileId
  capabilityKeys[]
  systemPromptRef
  allowedTools[]
  allowedMcpServers[]
  backendPolicyRef
  approvalPolicyRef
  inputSchema
  outputSchema
```

Music specialist 可以做：

```text
lyrics rewrite
style arrangement
prompt refinement
variation planning
artifact comparison
```

provider job 提交和 artifact 写入仍由 owning service 执行。

## Session 职责

Session 在业务编排中的职责：

```text
把 web 请求转成 AgentRunInput。
把可用 capabilities 写入 manifest。
把 agent raw events normalize 为 session events。
把 message.completed 写入 messages。
把 jobRef/artifactRef 放入 session event payload。
snapshot 返回 messages + activeRun + recentActivity。
```

Session 不做：

```text
quote/hold/capture。
provider 调用。
artifact 文件写入。
MCP tool 实际执行。
skill 安装和市场管理。
```

## Web 职责

Web 在业务编排中的职责：

```text
展示 capability 入口。
提交用户意图。
snapshot hydrate。
渲染 assistant message、job card、artifact card、activity。
HITL approve/reject/cancel。
从 artifact/job ref 跳转到 Studio。
```

Web 不做：

```text
直接调用 provider。
直接调用 MCP tool。
直接写 artifact/job。
把 provider 大结果存 localStorage。
```

## Agent 职责

Agent 在业务编排中的职责：

```text
理解用户意图。
选择 manifest 中允许的 capability。
生成结构化 brief。
调用 capability tool。
处理 HITL。
解释结果。
编排 specialist agent。
```

Agent 不做：

```text
直接扣积分。
直接写 job/artifact 数据库。
绕过 manifest 查询全局 skill/MCP。
把 provider 原始大 JSON 或二进制吐给 session。
```

## P1 实施顺序

```text
1. 定义 CapabilityRef / CapabilityInvocation / CapabilityResult。
2. session 在 AgentRunInput.capabilities 中传入允许能力。
3. RunCapabilityCompiler 生成 capability tool wrapper。
4. capability tool wrapper 只调用 adapter，不直接写业务库。
5. session/web 渲染 jobRef/artifactRef card。
6. 增加 general.music.generate smoke。
```

## P2 Music Entry 实施顺序

```text
1. General Chat 增加 music intent -> MusicBrief。
2. general.music.generate adapter 接 music job service。
3. session event payload 支持 jobRef/artifactRef。
4. web 渲染 music job card 和进入 Studio action。
5. Music Studio 使用 studio.music.generate capability。
6. 端到端覆盖失败释放 hold、成功 artifact card、刷新恢复。
```

## 风险

```text
把 Music provider 参数直接暴露给 agent，后续 provider 切换困难。
让 agent 直接写 artifact/job，破坏业务所有权。
General Chat 和 Music Studio 共用一个 UI，导致专业参数面失控。
job 大结果进入 SSE，导致 replay 和内存膨胀。
capability 没有 idempotencyKey，重复调用重复扣费。
skill/MCP 未授权就进入 agent prompt。
```

## 验收标准

```text
General Chat 能创建 music job，并返回 job/artifact card。
Music Studio 能直接创建 studio.music.generate job。
两种入口都不让 agent 直接扣费或写 artifact。
刷新后 snapshot 能恢复 job card 和 assistant message。
失败/取消/超时能释放 hold。
capability invocation 有 idempotencyKey。
未授权 capability 不出现在 AgentRunInput。
```
