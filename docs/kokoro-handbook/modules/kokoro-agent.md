# kokoro-agent 技术方案

三仓 V1 运行时总方案见：
[Agent / Session / Web V1 标准运行时方案](../technical/11-agent-session-web-v1-runtime.md)。
HIL 和工具执行前后拦截专项方案见：
[Agent HIL 与工具拦截标准方案](../technical/12-agent-hitl-tool-interception.md)。

本文件是 `kokoro-agent` 专项方案。它只定义 Agent 仓自己的边界、目录、
模型和运行链路，不替代 `kokoro-session` / `kokoro-web` 文档。
如果你想先找阅读顺序，见
[Agent 文档地图](../technical/13-agent-docs-map.md)。

## 定位

`kokoro-agent` 是 Agent 执行服务。

它接收 `kokoro-session` 投递的 `RunRequest`，基于 DeepAgents、
LangChain 和 LangGraph 构造可运行 agent，执行模型、工具、Skills、MCP、
Subagents、HITL 和 sandbox/backend，输出 raw agent events 给
`kokoro-session`。

它不是业务域服务，不是浏览器 API，不拥有聊天消息，不直接扣积分，不拥有
Skill Hub / MCP Hub 的安装、审核和启用状态。

## 设计推理

### 第一步：从完整 Agent 链路开始

`kokoro-agent` 不是传统业务域服务，它更像一个受控 Agent worker。
目录必须贴着执行链路走，而不是先套 `domain/application/infrastructure`
模板。

完整链路：

```text
1. session 投递 run.request。
2. worker 领取 run，并用 runId lease 防重复执行。
3. 解析 RunRequest。
4. 校验本次 run 的 capabilities 和 permissions。
5. 准备 model、tools、skills、MCP、subagents、sandbox、memory。
6. 基于 DeepAgents 构建可运行 agent。
7. 执行 agent，或根据 run.resume 恢复 agent。
8. DeepAgents/LangChain/LangGraph 负责原生 stream、interrupt、checkpoint。
9. Agent 只发布 Kokoro 关心的 RawAgentEvent。
10. 遇到敏感工具时，输出 awaiting approval 并等待 session resume。
11. run completed / failed / cancelled 后明确通知 session。
```

这个链路决定目录，而不是目录决定链路。

### 第二步：明确 DeepAgents 已经负责什么

既然 `kokoro-agent` 深度依赖 DeepAgents，就不能伪装成可替换 adapter，
也不能再自造一套小 LangChain。

DeepAgents/LangChain/LangGraph 负责：

```text
可运行 agent。
模型调用。
tool calling。
subagents / task。
skills。
MCP tools。
interrupt / HITL。
Command(resume=...)。
thread_id / checkpoint。
stream events。
backend / sandbox。
memory/store。
```

Kokoro 不应重复实现：

```text
read_events.py / map_events.py 这种自造事件系统。
RuntimeSubagentRegistry 这种自造子代理注册中心。
_LangChainActionRequest 这种框架泄漏类型名。
自维护 tool approval state machine。
自维护 checkpoint 协议。
自维护 MCP 工具协议。
```

### 第三步：明确 Kokoro-agent 自己负责什么

Kokoro-agent 的价值是把产品请求变成一次可控执行：

```text
RunRequest
  -> Capabilities
  -> Permissions
  -> DeepAgents graph
  -> Execute / Resume
  -> RawAgentEvent
  -> Session 持久化和重放
```

因此 Agent 自己拥有：

```text
RunRequest 解析。
Capabilities 校验。
Permissions 策略落地。
DeepAgents 创建参数准备。
工具、skills、MCP、subagents、sandbox 的本次 run 装配。
run lease。
agent checkpoint / memory。
RawAgentEvent 输出边界。
```

不拥有：

```text
聊天消息事实源。
浏览器 event cursor。
Skill/MCP Hub 安装、审核、市场、启用状态。
价格、账务、扣积分。
session messages / session events / run snapshot。
```

### 第四步：为什么不用 DDD 四层目录

Agent 服务不像订单、支付、库存，不适合重 DDD。

硬套 DDD 会导致：

```text
domain 变成纯类型桶。
application 变成脚本壳。
infrastructure 变成巨大垃圾桶。
为了分层写 ports/protocols。
读代码的人找不到“run 是怎么执行的”。
```

所以采用执行链路架构。

保留的 DDD 思想只有三点：

```text
边界清晰：agent 不写 session messages，不扣积分，不拥有 Hub。
语言清晰：RunRequest、Capabilities、Permissions、RawAgentEvent。
依赖清晰：worker 调 execution，execution 使用各能力模块。
```

不保留：

```text
domain/application/infrastructure/interfaces 四层模板。
repository/service/entity/aggregate 命名。
ports 目录。
为了抽象而抽象的 protocol 层。
```

## 业务职责

### Owns

```text
RunRequest 解析。
Capabilities / RunContext 的 agent 侧模型。
DeepAgents graph 构造。
模型调用。
工具注册和工具权限映射。
Skills mount 加载。
MCP client tool wrapper。
Subagents 配置映射。
HITL interrupt_on 和 Command(resume=...)。
Backend/sandbox 选择和安全策略执行。
LangGraph checkpointer / store。
RawAgentEvent 生成。
run lease 和 worker 执行保护。
Agent 侧 checkpoint / memory。
```

### Does not own

```text
浏览器 session event 契约。
聊天窗口 messages。
session events / run snapshot。
Skill Hub / MCP Hub 安装、审核、市场、启用状态。
SiteContext 最终业务授权。
Web UI 状态。
账务、支付、价格、套餐和积分。
模型最终价格决策。
```

## 上游和下游

```text
上游：
  kokoro-session
    发送 run.request / run.resume / run.cancel。
    提供本次 run 已授权的 runtime 能力。

下游：
  Redis
    run request/control/event stream。

  Mongo
    agent checkpoint / memory / long-running state。

  DeepAgents / LangChain / LangGraph
    agent 执行、interrupt、stream、checkpoint/store 接口。

  Model provider
    OpenAI / Anthropic / local fake / other provider。

  MCP server
    HTTP / streamable HTTP / 受限 stdio。

  Sandbox provider
    state / local_shell / e2b / custom。
```

Agent 不直接调用 `kokoro-web`，不直接读写 `kokoro-session` 的 message
collections。

## 目录架构

当前目录按执行链路组织。分层叙事一句话：contract 进 → worker 调度 →
orchestration 拼装 → execution 执行 → agents 出人格；state 是图状态，
ledger 是账本。

```text
kokoro_agent/
  contract/
    __init__.py
    events.py
    control.py
    streams.py

  worker/
    main.py
    supervisor.py
    messages.py

  orchestration/
    assemble.py
    general.py
    context.py

  execution/
    build_agent.py
    protocols.py
    run_agent.py
    approvals.py
    events.py
    publish_agent_events.py

  prompts/
    __init__.py
    general.md
    web-researcher.md

  tools/
    registry.py
    permissions.py
    ask_user_question.py
    memory.py
    web_fetch.py
    web_search.py
    middleware.py

  subagents/
    __init__.py
    catalog.py

  skills/
    mounts.py

  mcp/
    servers.py
    tools.py

  sandbox/
    backend.py

  storage/
    __init__.py
    checkpoints.py
    memory_store.py
    ledger.py
    sqlite.py
    mongo.py

  streams/
    __init__.py
    factory.py
    protocol.py
    redis.py
    memory.py

  model/
    __init__.py
    factory.py
    local_fake.py

  config.py
  observability.py
  state.py
```

## 目录与文件职责说明

每个目录和 `.py` 文件都必须回答三句话：

```text
为什么存在？
为什么放在这里？
禁止放什么？
```

回答不上来，不创建文件。

### `contract/`

`contract/` 是 wire 契约的单源镜像，由仓根 `contract/spec/*.yaml` 经
`contract/generate.py` 生成（DO NOT EDIT，禁手改）。

```text
contract/__init__.py
  存在理由：
    导出生成的 wire 类型稳定入口。

  放置理由：
    生成物需要一个包级导入面。

  禁止：
    不手改。
    不写业务逻辑。

contract/events.py
  存在理由：
    定义 Agent 输出给 Session 的 RawAgentEvent 信封和 payload 类型（生成物）。

  放置理由：
    RawAgentEvent 是 run 的对外事实，不属于 DeepAgents 原生事件。

  禁止：
    不手改。
    不生成 browser cursor。
    不持久化 session event。

contract/control.py
  存在理由：
    定义入站控制帧联合，如 run.request、run.resume、run.cancel（生成物）。
    RunRequest 是整个执行链路的输入。

  放置理由:
    入站契约与出站事件同属 wire 单源镜像。

  禁止：
    不手改。
    不读取环境变量。
    不 import DeepAgents。

contract/streams.py
  存在理由：
    定义 stream 名常量（生成物）。

  放置理由：
    流名是跨服务 wire 约定的一部分。

  禁止：
    不手改。
    不放业务字段。
```

### `worker/`

`worker/` 是调度域：进程入口装配 + 长驻调度，不写执行逻辑。

```text
worker/main.py
  存在理由：
    进程入口（约 100 行纯装配）：env 一次解析为 AppConfig，创建共享件，
    把编排配方注入 Supervisor.serve。

  放置理由：
    这是进程入口，不是 Agent 执行逻辑。

  禁止：
    不写 graph 执行逻辑。
    不解析 DeepAgents stream。
    不注册工具。
    不写业务状态机。

worker/supervisor.py
  存在理由：
    长驻调度：请求流消费循环、per-run control 流独立化、per-message 隔离、
    租约心跳与过期重拾、HITL resume 恢复、SIGTERM drain 优雅停机。

  放置理由：
    调度是 worker 域职责，与进程装配（main.py）分开。

  禁止：
    不拼装 agent 能力（那是 orchestration）。
    不构造 wire 事件。
    不做权限判断。

worker/messages.py
  存在理由：
    入站帧薄解析：contract 校验 + 坏帧安全丢弃（skip-and-continue）。

  放置理由：
    这些是 worker 入站消息解析，不是 wire 契约本身。

  禁止：
    不创建 agent。
    不连接 MCP。
    不做权限判断。
    不发布 raw events。
```

### `orchestration/`

`orchestration/` 是编排域：RunRequest + RuntimeConfig → 可运行 InvokableAgent。
本次 run 被授权的能力（model、tools、skills、MCP、subagents、sandbox）
经 wire RuntimeConfig 传入，在这里落地为一次装配。

```text
orchestration/assemble.py
  存在理由：
    每请求主配方：工具解析 → 守卫构造 → 子代理装配 → 上下文组合 → 图构建。
    系统最重要的组装点。

  放置理由：
    编排是调度（worker）和执行（execution）之间的拼装层。

  禁止：
    不消费 Redis。
    不发布事件。
    不查询 Hub。
    不扩大 RuntimeConfig 授权范围。

orchestration/context.py
  存在理由：
    模型可见面的组合：compose_system_prompt（人格 + skills 全文）。
    工具用法不进 system prompt——活在各工具 description，
    由 LangChain 经工具 schema 交给模型。

  放置理由：
    system prompt 组合属于每请求编排，不属于成品定义或执行。

  禁止：
    不放 secret。
    不放 site/user/workspace 私有内容。
    不读用户配置。
```

### `execution/`

`execution/` 是 Agent 执行编排层。它基于 DeepAgents 实现 Kokoro 的执行链路，
但目录不叫 `deepagents`，因为 DeepAgents 是底座，不是架构语言。

```text
execution/build_agent.py
  存在理由：
    DeepAgents 装配：静态 import 并调用原生 create_deep_agent，
    出口收窄为 InvokableAgent 端口。

  放置理由：
    维护者要找的是“如何构建 agent”，不是 graph、adapter 或框架名。

  禁止：
    不消费 Redis。
    不发布事件。
    不查询 Hub。
    不做价格或账务判断。
    不变成 kokoro_agent/deepagents 目录。
    不隐藏或重写 DeepAgents 行为。
    不做 session 持久化。

execution/protocols.py
  存在理由：
    LangGraph/DeepAgents 的窄 runtime_checkable 端口
    （InvokableAgent、AgentRunStream 等），框架私有泛型止步于此。

  放置理由：
    这是 execution 使用的窄接口，不是全仓 ports 层。

  禁止：
    不创建 ports 目录。
    不复制 LangGraph 完整类型系统。
    不放具体 Redis/Mongo 实现。

execution/run_agent.py
  存在理由：
    invoke_once 单段执行编排：run.started → 投影泵 → interrupt 暂停 /
    claim-before-emit 终态收口（completed / failed / cancelled）。
    新 run 和 HITL resume 后的续段共用这一段主流程。

  放置理由：
    这是一次 run 段的主流程。

  禁止：
    不注册全局 mutable tool registry。
    不实现工具本身。
    不把 LangChain event system 重写一遍。

execution/approvals.py
  存在理由：
    HITL 权威唯一实现：pending 集合、awaiting 事件、resume 决策
    fail-loud 对齐为 Command(resume=...)（含子代理嵌套帧回退）、
    快照直发终态。

  放置理由：
    审批是 execution 的暂停和恢复边界。

  禁止：
    不把 reject 当正常 tool result。
    不让 respond 用于危险工具。
    不跳过 edit 后的参数校验。
    不伪造工具执行结果。

execution/events.py
  存在理由：
    wire 事件构造唯一地点（RunEmitter）：per-run 单调 index 单点递增，
    contract strict 模型构造即校验。

  放置理由：
    这是 DeepAgents 原生 stream 和 Kokoro raw event 之间的输出语言。

  禁止：
    不重写 LangChain/DeepAgents event system。
    不生成 browser cursor。
    不负责 session replay。

execution/publish_agent_events.py
  存在理由：
    v3 四投影并发消费 + queue 合流单点发布：把 DeepAgents typed stream
    投影为 wire 事件，哨兵必达 drain 收束，防回压死锁。

  放置理由：
    这里是执行过程的输出发布边界，不是独立 event framework。

  禁止：
    不命名为 read_events.py 或 map_events.py。
    不维护跨服务顺序字段。
    不做 Mongo 持久化。
```

### `agents/`

`agents/` 是成品域：封装好的对外 agent 定义，每个成品一个子包，
人格资源随包分发。

```text
agents/general/__init__.py
  存在理由：
    通用 agent 成品人格 GENERAL_PERSONA：Kokoro 缺省主 agent 的人格文本，
    session 入口表的内建 general 引用此身份。入口的名字/描述/能力束等
    元数据活在 session 入口表（入口是数据不是代码），本仓不重复维护。

  禁止：
    不放能力装配逻辑。
    不 import DeepAgents。

  放置理由：
    成品包结构约定：每个对外 agent 一个子包。

  禁止：
    不读用户配置。
    不拼接动态上下文。

agents/general/persona.md
  存在理由：
    通用 agent 的人格正文，随包分发。

  放置理由：
    人格资源与成品定义同居本包。

  禁止：
    不放 secret。
    不放 site/user/workspace 私有内容。
    不放用户动态数据。
```

### `tools/`

`tools/` 只放 Kokoro 自己明确拥有的工具和工具集合装配。

```text
tools/registry.py
  存在理由：
    工具集合治理：保留名/冲突断言 + runtime.tools 解析为本次 run
    可挂载工具集合，未知名 fail-loud。

  放置理由：
    工具集合是执行能力的一部分，但不是 run 请求类型。

  禁止：
    不维护跨 run 全局 mutable registry。
    不绕过 permissions。
    不自动暴露所有 MCP/skills 工具。

tools/permissions.py
  存在理由：
    HITL interrupt_on 构造：审批工具集合每请求经 RuntimeConfig.permissions
    注入，转换为工具可用性和 interrupt_on 配置。

  放置理由：
    这是工具调用前的治理，不是 UI 审批页面。

  禁止：
    不直接弹 UI。
    不写 session 状态。
    不让 sandbox 覆盖 deny。

tools/ask_user_question.py
  存在理由：
    模型向用户请求补充信息的标准工具，HITL respond 流程的语义暂停点。

  放置理由：
    这是 Kokoro 明确拥有的默认工具。

  禁止：
    不用于危险工具拒绝。
    不替代普通聊天消息。
    不直接调用 web。

tools/memory.py
  存在理由：
    长期记忆工具：通用存取原语；归属 scope 在装配时注入，
    工具体不含租户概念。

  放置理由：
    这是 Kokoro 自有的默认工具原语。

  禁止：
    不跨 namespace 泄漏。
    不在工具体内解析租户。

tools/web_fetch.py
  存在理由：
    web_fetch 底层工具：公网页面抓取 + 正文提取，SSRF 防御与
    流式大小封顶（零 vendor 依赖）。

  放置理由：
    自建 fetch 工具属于 Kokoro 自有工具原语，文件名表达业务动作。

  禁止：
    不放行内网地址（本地开发经配置显式放行除外）。
    不把大结果直接塞进 event。

tools/web_search.py
  存在理由：
    web_search 底层工具：上半部为通用检索原语（SearchProvider 协议注入），
    下半部为 provider 适配器注册表（tavily/searxng/zhipu）。

  放置理由：
    检索是 Kokoro 自有工具原语，provider 经配置即挂载。

  禁止：
    不在工具体内读环境变量。
    不把 provider 名写进业务类型名以外的公共接口。

tools/middleware.py
  存在理由：
    工具策略中间件集合：ToolPolicyMiddleware（未授权 fail-closed 拒绝、
    授权放行并审计）、TerminalGuardMiddleware、TokenBudgetMiddleware、
    ToolResultReviewMiddleware。

  放置理由：
    这些是工具调用前后的治理横切件，随工具域维护。

  禁止：
    不实现工具本身。
    不发布 wire 事件。

（原 tools/names.py 已解散：ask_user_question 名随工具本体（ask_user_question.py），
保留名集合与冲突断言归工具集合治理（registry.py），
mcp__{server}__{tool} 命名规则归其唯一消费者（mcp/tools.py）。
文件名要表达业务动作，"names" 表达不了任何动作。）
```

### `subagents/`

`subagents/` 描述可被本次 run 使用的子代理定义。

```text
subagents/__init__.py
  存在理由：
    导出稳定的子代理类型与 catalog API。

  放置理由：
    只作为包入口，便于编排层使用。

  禁止：
    不注册全局 mutable 状态。
    不读取环境变量以外的外部系统。

subagents/catalog.py
  存在理由：
    子代理目录：内建（如 web-researcher，经 KOKORO_BUILTIN_SUBAGENTS
    点名启用，默认全关）+ 配置自定义（JSON 经注入），source 标签解析单点，
    并产出 DeepAgents subagents 定义。

  放置理由：
    catalog 是本次 run 可用子代理定义的来源。

  禁止：
    不让模型静默写入。
    不查询 Hub。
    不让模型静默创建同权限子代理。
    不默认继承主 Agent 全部 tools/skills/MCP/sandbox。
    不维护 RuntimeSubagentRegistry。
```

### `skills/`

`skills/` 只消费已授权 skill mount，不拥有 Hub。

```text
skills/mounts.py
  存在理由：
    校验并加载本次 run 已授权、已解析、可读取的 skill mounts。

  放置理由：
    skill mount 是执行输入的一部分，但安装和审核不在 Agent。

  禁止：
    不做 git/http 安装。
    不拥有审核状态。
    不扩大工具、MCP 或 sandbox 权限。
```

### `mcp/`

`mcp/` 只连接本次 run 授权的 MCP server/tool。

```text
mcp/servers.py
  存在理由：
    根据 Capabilities 建立 MCP server 连接。

  放置理由：
    MCP server 是外部工具能力来源。

  禁止：
    不扫描全局 MCP 列表。
    不读取未授权 secrets。
    不绕过 namespace/TTL。

mcp/tools.py
  存在理由：
    把 allowed MCP tools 暴露给 DeepAgents。

  放置理由：
    MCP tool 暴露需要独立治理名称、schema、timeout 和结果大小。

  禁止：
    不绕过 allowedTools。
    不把大结果直接塞进 event。
```

### `sandbox/`

`sandbox/` 负责执行环境选择和安全策略。

```text
sandbox/backend.py
  存在理由：
    filesystem 权限 + 执行 backend 选择：state 虚拟盘 / local_shell 真盘；
    filesystem/backend 每请求经 wire 决定，local_shell 参数
    （SandboxSettings：root/timeout/输出上限）进程级注入。
    e2b/custom 在 V1 未落地，遇到即 fail-loud，不静默降级为 state。

  放置理由：
    backend 是工具和代码执行环境。

  禁止：
    不把 local_shell 作为生产默认。
    不吞掉 provider 初始化失败。
    不让 sandbox 覆盖工具 deny。
    不在这里做账务或 Hub 判断。
```

### `storage/`

`storage/` 存 Agent 自己的执行状态，不存聊天消息。

```text
storage/__init__.py
  存在理由：
    导出 storage 稳定入口，如 make_ledger。

  放置理由：
    只服务包导入，不承载业务逻辑。

  禁止：
    不创建连接。
    不读取配置。

storage/checkpoints.py
  存在理由：
    LangGraph checkpointer 工厂：sqlite（落盘）/ mongo（跨 pod）/
    memory（易失），用于 resume、HITL 和故障恢复。

  放置理由：
    checkpoint 是 Agent 执行侧状态。

  禁止：
    不写 session messages。
    不当作聊天历史事实源。

storage/memory_store.py
  存在理由：
    长期记忆 store 工厂（LangGraph BaseStore）：后端与 checkpoint 对齐
    （memory/sqlite/mongo），全官方实现。

  放置理由：
    memory 是 Agent 长期上下文，不是 session messages。

  禁止：
    不跨 namespace 泄漏。
    不替代 session 的消息存储。

storage/ledger.py
  存在理由：
    RunLedger 协议（控制面账本）与后端工厂 make_ledger / LedgerSettings：
    多 pod 去重、TTL 租约防重复执行、HITL 暂停哨兵、终态原子认领、
    add_tokens/add_usage 累计、tool_result keep-first。

  放置理由：
    这是 storage 内部稳定契约，不是 ports 目录。
    lease 是 worker 多实例执行保护，归账本统一承载。

  禁止：
    不写具体数据库逻辑（工厂选择除外）。
    不做 session 业务锁。
    不决定 session 是否可创建新消息。

storage/mongo.py
  存在理由：
    MongoLedger：跨 pod 共享的 run 状态存储，
    $setOnInsert/条件更新给原子认领。

  放置理由：
    Mongo 是多 Pod 下的共享执行状态后端。

  禁止：
    不存 session messages。
    不存浏览器事件。

storage/sqlite.py
  存在理由：
    SqliteLedger：跨进程/重启的 run 状态存储，
    WAL+busy_timeout 保真实争用下的原子性。

  放置理由：
    SQLite 服务本地开发、测试和单机部署。

  禁止：
    不跨 Pod 使用。
```

### `streams/`

`streams/` 负责 Agent 与 Session 之间的运行时 stream。

```text
streams/__init__.py
  存在理由：
    导出 stream 稳定入口，如 make_stream、MemoryStream、RedisStream。

  放置理由：
    只服务包导入，不承载业务逻辑。

  禁止：
    不创建连接。
    不读取配置。

streams/factory.py
  存在理由：
    根据配置选择 Redis 或 memory stream。

  放置理由：
    stream 后端选择属于传输层。

  禁止：
    不执行 Agent。
    不做 Mongo 轮询。

streams/protocol.py
  存在理由：
    定义与后端无关的事件流契约（StreamPort）：publish 带保留上限、
    consumer-group 订阅、cursor 不透明。

  放置理由：
    execution/worker 只依赖这个窄协议。

  禁止：
    不绑定 Redis。
    不生成 browser cursor。
    不放业务字段。

streams/redis.py
  存在理由：
    Redis Streams 传输：XADD maxlen 裁剪 + XREADGROUP/XACK
    consumer-group 消费，断线指数退避。

  放置理由：
    Redis 是跨服务传输层。

  禁止：
    不做 Mongo 轮询。
    不放 Agent 执行业务流程。
    不生成 browser cursor。

streams/memory.py
  存在理由：
    内存事件流：单进程默认后端，publish 即裁剪，
    group 订阅与 ack 给 redis 等价语义。

  放置理由：
    单测和单进程部署需要快速替代 Redis。

  禁止：
    不跨进程使用。
    不成为第二事实源。
```

### `model/`

`model/` 创建 chat model，不做价格和账务。

```text
model/__init__.py
  存在理由：
    导出 model 稳定入口，如 make_chat_model 和 LocalFakeChatModel。

  放置理由：
    只服务包导入，不承载业务逻辑。

  禁止：
    不创建模型实例。
    不读取配置。

model/factory.py
  存在理由：
    聊天模型工厂与 ChatModelSettings：provider/name/effort 每请求经
    wire ModelConfig 决定（openai/anthropic/local_fake），
    凭证进程级注入。

  放置理由：
    模型 provider 是执行依赖，配置类型属于 model 能力边界。

  禁止：
    不决定最终价格。
    不扣积分。
    不读取 session messages。

model/local_fake.py
  存在理由：
    LocalFakeChatModel：离线确定性脚本化假模型，
    无需凭证即可驱动真实 DeepAgents 循环。

  放置理由：
    fake model 是 model provider 的测试实现。

  禁止：
    不进入生产默认。
    不掩盖真实 provider 错误。
```

### 根文件

```text
config.py
  存在理由：
    AppConfig：全部环境变量的唯一解析点，仅 worker/main.py 调用一次
    并显式注入（含 KOKORO_LEDGER_BACKEND / KOKORO_LEDGER_DB 等）。

  放置理由：
    配置是全局启动输入。

  禁止：
    不执行业务逻辑。
    不创建 graph。
    不连接外部服务。

observability.py
  存在理由：
    Langfuse trace 配置构造：凭据齐备与否由注入的 settings 决定。

  放置理由：
    观测横切整个 worker。

  禁止：
    不影响业务决策。
    不吞异常。

state.py
  存在理由：
    “state”一词只指图状态轴：KokoroAgentState（DeepAgentState 扩展键
    scope）+ RunScope（一次 run 的领域身份四元组
    namespace/session_id/run_id/thread_id）。scope 随初始 input 进图、
    落 checkpoint、resume 不重供仍保持。

  放置理由：
    图状态是横切执行链路的领域身份载体，不属于任何单一子域。

  禁止：
    图节点不得改写 scope。
    不查数据库。
    不做 Hub 查询。
    不决定用户能用什么。
```

### 禁止目录和文件名

命名红线按读者视角定义，不按框架内部术语定义：

1. 不用框架品牌名或泛词做目录名。DeepAgents 是底座，可以 import，不成为 Kokoro 的架构语言；`runtime`、`adapters` 也太泛。
2. 不套重 DDD 四层模板。Agent worker 是执行链路，目录必须按 `contract/worker/orchestration/execution/agents/tools/subagents/skills/mcp/sandbox/storage/streams/model` 这条链路展开。
3. 不自造 LangChain/DeepAgents 已经有的事件系统，不新增 read/map event wrapper。
4. 不用框架动作名或学术词做文件名。`invoke`、`projection`、`transformer` 不能告诉维护者业务职责。
5. 不保留含糊类型名：`RuntimeSubagentRegistry`、`_LangChainActionRequest`、`RunJob`、`AgentRunOptions`、`KokoroRunContext`。

### `__init__.py` 规则

```text
只允许包说明或稳定导出。
不写业务逻辑。
不创建对象。
不读配置。
不隐式注册工具。
```

## 核心对象

### RunRequest

`RunRequest` 是 session 发给 agent 的执行输入。

```text
RunRequest
  kind
  runId
  threadId
  input
  runtime
  context
  trace
```

说明：

```text
runId
  Kokoro 一次执行的 ID，用于 event stream、幂等和追踪。

threadId
  LangGraph 线程 ID，传入 configurable.thread_id。
  它不是 conversationId，也不是 sessionId。

input
  本次用户输入和必要消息上下文。

runtime
  本次 run 被授权的模型、工具、skills、MCP、subagents、sandbox、approval。

context
  本次 run 的最小业务上下文，如 site/user/workspace/project/namespace。

trace
  观测字段，不参与业务判断。
```

禁止字段：

```text
conversationId
  容易和 sessionId/threadId 混用。

permissionMode
  太粗，应该表达为 runtime.approval 和 per-tool policy。

AgentRunInput / RunJob
  抽象但不清晰。

SkillSpec source union
  安装来源不是 agent 职责。
```

### Capabilities

```text
Capabilities
  model
  tools
  subagents
  skills
  mcpServers
  sandbox
  approval
  memory
```

规则：

```text
Capabilities 表示本次 run 可用能力。
它由 session 或上游业务编排层生成。
Agent 不查询 Hub 来决定用户有什么。
Agent 不扩大 Capabilities 授权范围。
```

### RunContext

推荐命名为 `RunContext`，不要加 `Kokoro` 前缀。

```text
RunContext
  namespace
  siteId
  userId
  workspaceId
  projectId
  sessionId
  artifactScope
  memoryScope
```

说明：

```text
namespace
  agent 侧资源隔离键。
  可由 site/user/workspace/project/session 组合生成。
  Agent 只把它当隔离字符串，不理解复杂业务。

sessionId
  Kokoro 聊天窗口或会话 ID，用于追踪和上下文。

threadId
  LangGraph checkpoint 线程 ID，不应和 sessionId 混用。
```

### RawAgentEvent

Agent 输出 raw event，不输出 browser-facing event。

```text
run.started
message.delta
message.completed
thinking.delta
tool.invoked
tool.awaiting_approval
tool.returned
todo.updated
subagent.started
subagent.finished
run.completed
run.failed
```

规则：

```text
raw event 不带 web cursor。
raw event 不依赖 BaseMessage.id 排序。
raw event 可以携带 provider/langchain message id 作为 metadata。
session 负责持久化、排序、重放和 browser event 映射。
```

### ToolPolicy

```text
ToolPolicy
  allow
  ask
  deny
```

策略应支持：

```text
按工具名。
按参数。
按 namespace。
按 sandbox。
按 secret grant。
按 MCP server/tool。
```

### ApprovalDecision

```text
approve
reject
edit
respond
```

规则：

```text
respond 只用于 ask_user_question。
危险工具不同意必须 reject。
edit 表示用户修改工具参数后继续。
approve 表示按原参数执行。
```

## DeepAgents 接入

Agent 必须顺着 DeepAgents/LangGraph 原生能力，而不是自造第二套 agent
framework。

基础映射：

```python
create_deep_agent(
    model=model,
    tools=tools,
    system_prompt=system_prompt,
    skills=skill_paths,
    backend=backend,
    permissions=filesystem_permissions,
    subagents=subagents,
    middleware=middleware,
    interrupt_on=interrupt_on,
    context_schema=RunContext,
    checkpointer=checkpointer,
    store=store,
)
```

Kokoro 只做三类事：

```text
RunRequest -> DeepAgents 参数。
DeepAgents/LangGraph stream -> RawAgentEvent。
Session control -> Command(resume=...)。
```

不做：

```text
复制 DeepAgents 的 subagent 机制。
复制 LangGraph 的 checkpoint 机制。
复制 LangChain middleware 机制。
复制 MCP 工具协议。
```

## Tools

V1 默认工具应少而标准。

```text
ask_user_question
  模型向用户提问。
  对应 HITL respond 的唯一默认场景。

task / delegate
  交给配置型或受控临时子代理。
  对齐 Claude Code 一类产品里常见的任务委派体验。

todo
  Agent 内部计划和进度。
  输出 todo.updated。
```

不默认提供：

```text
clock / now
  不是 agent 核心能力。测试可用 fixture。

自写 web_fetch
  如果 DeepAgents/LangChain/MCP 已有可用 fetch/search 工具，优先接入现有能力。
  确实要自建时，文件名必须表达清楚，如 web_fetch.py 或 web_search.py。
```

工具命名规则：

```text
工具名小写 snake_case。
文件名和工具语义一致。
不要用 fetch.py 这种含义过宽的名字。
不要把 provider 或框架名写进业务类型名。
```

## Subagents

Subagents 是 V1 核心能力，但必须按授权边界运行。

### 配置型 Subagents

由 `Capabilities.subagents` 传入，映射到 DeepAgents `subagents=`。

```text
name
description
system_prompt
tools
model
skills
mcpServers
approval
sandbox
```

规则：

```text
默认不继承主 agent 的全部工具。
默认不继承全部 MCP servers。
默认不继承全部 skills。
默认不能再创建子代理。
需要继承时必须显式配置。
```

### 临时 Delegate

模型可以请求临时委派，但必须经过策略。

```text
subagent_create = deny | ask | allow
```

默认建议：

```text
开发环境 ask。
生产环境 deny 或按官方策略 allowlist。
高权限工具永远 ask。
```

不允许：

```text
RuntimeSubagentRegistry 让模型静默注册同权限子代理。
模型自己写 system_prompt 后直接获得主 agent 权限。
临时子代理默认拥有 shell、MCP secrets、artifact 写权限。
```

## HITL / 审批

HITL 使用 DeepAgents/LangGraph 原生 interrupt / resume 机制。

链路：

```text
1. ToolPolicy 生成 interrupt_on。
2. DeepAgents 执行到敏感工具。
3. LangGraph interrupt 返回 action_requests 和 review_configs。
4. Agent 输出 tool.awaiting_approval raw event。
5. Session 持久化并转为前端可渲染审批状态。
6. Web 用户 approve / reject / edit / respond。
7. Session 发 run.resume。
8. Agent 转为 Command(resume=...)。
9. Graph 继续执行或终止。
```

审批模型：

```text
ApprovalRequest
  runId
  toolCallId
  toolName
  args
  description
  allowedDecisions
  risk

ApprovalDecision
  toolCallId
  decision
  editedArgs
  message
```

规则：

```text
respond 只给 ask_user_question。
reject 不应该伪装成工具正常结果。
edit 后必须重新校验参数和权限。
审批状态必须可恢复，worker 重启不丢。
```

## Skills

Skill 是 V1 能力，但 Agent 不拥有 Hub。

Agent 接收的是已授权、已解析、可加载的 mount：

```text
skills:
  - name: official/pdf
    path: /runtime/skills/official/pdf
    lock: sha256:...

  - name: user/release_note
    path: /runtime/skills/users/u_123/release_note
    lock: sha256:...
```

Agent 不接收：

```text
git url
http bundle url
artifact id
marketplace id
审核状态
定价
```

这些属于 Hub/Session/Web 或上游编排层。

Agent 侧规则：

```text
按 path/mount 加载 skill。
校验 lock/hash。
skill 不得扩大 tools/MCP/sandbox 权限。
skill supporting files 按需读取，不一次性全部塞进 prompt。
skill 加载失败要 fail closed，并输出明确错误。
```

## MCP

MCP 是 V1 外部工具接入能力。

推荐策略：

```text
生产主路径：
  HTTP / streamable HTTP。

受限路径：
  stdio，仅本地开发、桌面宿主或明确 sandbox。

兼容路径：
  SSE，不作为默认推荐。
```

Agent 接收：

```text
mcpServers:
  - name
    transport
    url
    allowedTools
    secretGrant
    timeout
```

规则：

```text
只连接 Capabilities 授权的 server。
只暴露 allowedTools。
工具命名 mcp__{server}__{tool}。
secret grant 绑定 namespace/run/tool/TTL。
大结果写 artifact/content ref，event 只给摘要和引用。
```

## Sandbox / Backend

V1 支持可配置 backend。

```text
state
  默认安全 backend。
  不执行本地 shell。

local_shell
  本地开发和明确测试。
  生产默认禁止。

e2b
  远程隔离执行。
  适合代码、文件、shell、浏览器类任务。

custom
  企业私有 sandbox provider。
```

策略：

```text
没有显式 sandbox policy 的高风险工具 fail closed。
local_shell 在 production profile 下必须拒绝。
文件系统权限由 RunRequest runtime.permissions 限定。
sandbox 输出大文件时写 artifact，不塞进 event。
```

## 数据模型

Mongo（agent 拥有）：

```text
kokoro_agent_checkpoints
  runId
  threadId
  checkpointId
  state
  metadata
  createdAt

kokoro_agent_memory
  namespace
  subjectId
  memoryType
  content
  metadata
  createdAt
```

Redis：

```text
kokoro:agent:run_requests
kokoro:agent:run_controls
kokoro:agent:run:{runId}:events
kokoro:agent:leases:{runId}
```

不使用：

```text
Agent 不写 MySQL 账务表。
Agent 不写 session messages。
Agent 不使用 SQLite 作为生产策略。
SQLite 只允许作为本地测试 checkpointer fixture。
```

## API / RPC / Events

入站消息：

```text
run.request
run.resume
run.cancel
```

出站 raw events：

```text
run.started
message.delta
message.completed
thinking.delta
tool.invoked
tool.awaiting_approval
tool.returned
todo.updated
subagent.started
subagent.finished
run.completed
run.failed
```

错误策略：

```text
配置错误：run.failed，错误明确。
权限错误：tool.awaiting_approval 或 tool.denied。
MCP/skill/sandbox 初始化失败：fail closed。
底层 event 解析失败：记录 raw metadata，输出 run.failed，不静默吞。
```

## Admin 管理

Agent 不提供独立后台页面，但需要暴露给平台后台的资源：

```text
run 详情。
worker lease。
checkpoint 状态。
tool approval 记录。
skill mount 结果。
MCP server 连接状态。
sandbox provider 状态。
错误和 trace。
```

权限 key 由平台统一定义，Agent 只输出可审计数据。

## 业务链路

### 普通聊天

```text
1. Web 提交消息给 Session。
2. Session 持久化用户消息。
3. Session 构造 RunRequest。
4. Agent 构造 DeepAgents graph。
5. Agent 输出 raw events。
6. Session 持久化并映射为聊天窗口事件。
7. Web 通过 SSE 接收。
```

### 工具审批

```text
1. Agent 调用敏感工具前 interrupt。
2. Agent 输出 tool.awaiting_approval。
3. Session 保存审批状态。
4. Web 展示审批 UI。
5. 用户选择 approve/reject/edit/respond。
6. Session 发 run.resume。
7. Agent Command(resume=...) 后继续。
```

### ask_user_question

```text
1. 模型需要用户补充信息。
2. 调用 ask_user_question。
3. Agent 输出 tool.awaiting_approval，allowedDecisions 只允许 respond。
4. Web 呈现为对话式提问。
5. 用户回答后 resume。
```

### Subagent

```text
1. 主 agent 调用 task/delegate。
2. Agent 根据 Capabilities 找到配置型 subagent。
3. 子代理只获得显式授权的 tools/skills/MCP/sandbox。
4. 子代理事件映射为 subagent.* raw events。
```

## 部署

```text
服务名：
  kokoro-agent-worker

入口：
  kokoro-agent-worker

运行时：
  Python + uv

关键环境变量：
  KOKORO_STREAM_BACKEND=memory|redis
  KOKORO_REDIS_URL
  KOKORO_MONGO_URL / KOKORO_MONGO_DB
  KOKORO_CHECKPOINT_BACKEND / KOKORO_CHECKPOINT_DB
  KOKORO_LEDGER_BACKEND / KOKORO_LEDGER_DB
  KOKORO_BUILTIN_SUBAGENTS / KOKORO_CUSTOM_SUBAGENTS
  OPENAI_API_KEY
  ANTHROPIC_API_KEY

多 Pod：
  runId lease。
  threadId checkpoint。
  control resume 幂等。
```

配置文件：

```text
.env.example.yaml
.env.dev
.env.development
.env.test
.env.prerelease
.env.prod
```

规则：

```text
本地开发可以启用 local_shell。
测试可以使用 local fake model 和 memory stream。
生产必须显式选择安全 backend。
K8s 用 env/configmap/secret 覆盖同名配置。
```

## 测试

单测：

```text
RunRequest parser。
Capabilities resolver。
RunContext namespace。
ToolPolicy -> interrupt_on。
ApprovalDecision -> Command(resume=...)。
Agent event mapper。
Skill mount loader。
MCP wrapper。
Sandbox policy。
Subagent config mapping。
```

集成：

```text
Redis run.request -> raw events。
HITL approve/reject/edit/respond。
ask_user_question -> respond。
checkpoint resume。
state backend smoke。
local_shell dev smoke。
e2b smoke。
MCP HTTP server smoke。
skill mount smoke。
```

必须覆盖的反例：

```text
未授权 MCP tool 不暴露。
未授权 skill 不加载。
local_shell 在 prod profile 下失败。
临时 subagent 不能继承主 agent 全部权限。
respond 不能用于危险工具。
edit 后参数必须重新校验。
重复 run.request 只执行一次。
worker 重启后 pending approval 可恢复。
BaseMessage.id 不参与跨服务排序。
```

## 风险和边界

最高风险：

```text
把 DeepAgents 依赖变成顶层架构名。
为 LangGraph event 自造第二套框架。
让模型静默创建同权限子代理。
让 skill/MCP 扩大权限。
把 local_shell 当生产 sandbox。
Agent 写 session messages。
Agent 扣积分或决定价格。
```

禁止项：

```text
不新增 kokoro-contracts。
不使用 ports 目录命名。
不引入 PostgreSQL。
不保留 legacy 兼容 shim。
不为了旧测试保留 seq/cursor 兼容字段。
不把安装来源 union 放进 agent request。
```

## 后续任务

P0：

```text
冻结目录架构。
把现有不清晰目录和文件命名收敛为执行链路架构。
删除 clock/now、自写 fetch、runtime subagent registry。
落地 ask_user_question。
RunRequest / Capabilities / RunContext 定稿。
HITL 走 interrupt_on + Command(resume=...)。
Subagents 改为 DeepAgents 标准配置映射。
```

P1：

```text
MCP HTTP / streamable HTTP client。
Skills mount loader 和 lock/hash 校验。
E2B backend。
OpenTelemetry / LangSmith trace。
Admin 可审计状态输出。
```

P2：

```text
更复杂的专业 agent 编排。
异步 subagent 调度。
多模型路由。
长任务 artifact 结果回写。
```

## 实现注记（2026-07-03，v2.1 落地）

```text
wire 类型改为生成物：RawAgentEvent / 入站联合 / 流名常量位于
kokoro_agent/contract/（由仓根 contract/spec 生成，DO NOT EDIT），
本文早期版本 run 包内 events/request 的手写镜像职责由生成物取代；
run 包当时仅保留非 wire 领域模型（该包后已删除，见下一条注记）。
raw 事件面为 14 kind（message.* 词汇，含 subagent.text.*），
browser 面 15 kind 由 session 合成补齐。
未创建零消费者的占位文件（lifecycle/definitions/policy 等），其职责落在
worker/supervisor.py / execution/approvals.py / subagents/catalog.py /
sandbox/backend.py / storage/ledger.py。
```

## 实现注记（2026-07-04，命名定案）

```text
旧 run/ 包已删除。“state”一词从此只指图状态轴：根文件 state.py 承载
KokoroAgentState（DeepAgentState 扩展键 scope）与 RunScope（身份四元组
namespace/session_id/run_id/thread_id）。
控制面账本改名 ledger：storage/ledger.py = RunLedger 协议 + make_ledger +
LedgerSettings，后端实现为 SqliteLedger（storage/sqlite.py）与
MongoLedger（storage/mongo.py）；env 变量为 KOKORO_LEDGER_BACKEND /
KOKORO_LEDGER_DB（原 KOKORO_RUN_STATE_* 拼写作废）。
分层叙事一句话：contract 进 → worker 调度 → orchestration 拼装 →
execution 执行 → agents 出人格；state 是图状态，ledger 是账本。
```

## 实现注记（2026-07-04，子代理执行面收口）

```text
契约新增 subagent.tool.invoked / subagent.tool.returned（raw 18 kind /
browser 19 kind）：子代理内工具过程上 wire（含其自有 todo，不再覆盖主
todo 面板），无输出增量通道，结果截断语义同 tool.returned。HITL 审批
仍走主通道嵌套帧。真模型实证：子代理内 web_search 的成对事件与
subagent_id 归属（real-model-verify 场景 A）。
deepagents 内生 general-purpose 守卫旁路收口：orchestration 传同名 spec
显式覆盖（tools/model 缺省继承主 agent），middleware 挂满守卫下发链
（TerminalGuard/TokenBudget/review）；可达性政策不变（不进 declared 集，
仍仅 subagent_create=allow 档可达）。此前 handbook 注记的
"general-purpose 仅 allow 档可达且不带闸" residual 至此消除。
```
