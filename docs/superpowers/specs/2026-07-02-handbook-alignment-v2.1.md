# v2.1 Handbook 对齐实施规格（2026-07-02）

> 法源：docs/kokoro-handbook/{decisions/ADR-004, technical/11, technical/12, technical/03, modules/kokoro-agent.md, business-flows/agent-handoff.md}。
> 基线：v2 重写（blueprint 2026-07-02）已完成三仓门禁绿；本规格是 v2 → handbook 的收敛增量，不是再推倒。
> 原则：handbook 为法；v2 的真实改进（契约 codegen 单源、TTL 租约、显式状态机、DB-first）保留并反哺 handbook；冲突处本文逐条裁决。

## 0. 裁决矩阵（法 vs v2 现状 → 决议）

| # | 主题 | handbook | v2 现状 | 决议 |
|---|---|---|---|---|
| 1 | RunRequest 形状 | `{kind, runId, threadId, input, runtime, context, trace}`；**禁 conversationId/permissionMode** | `{run_id, session_id, conversation_id, message, execution_style, permission_mode}` | **按法改**（§1） |
| 2 | 事件词汇 | `message.delta/message.completed` + `session.created/run.created`（browser 面 15 kind） | `text.delta/text.completed`，killed session.created/run.created | **按法改**：raw 14 kind（run.started 起），session 合成 session.created/run.created，browser 面 15 kind；session.created 携带 sessions 集合的真实元数据（修 v2 审计指出的 owner 造假，而非删事件） |
| 3 | HITL awaiting payload | + `kind(tool_approval\|ask_user)`, `risk{level,source,reason}`, `editable`, `input_schema` | 有 awaiting_kind/editable，无 risk/input_schema | **按法补齐**；保留 v2 的 `pending_tool_ids`（同帧完备判据，web staging 消费）为**有意扩展** |
| 4 | 控制通道 | `kokoro:run:{runId}:control` 独立流 | resume/cancel 复用请求流 | **按法改**：per-run control 流，agent 认领 run 后订阅 |
| 5 | Session HITL 校验 | session 必须按自己的 pending_pauses 校验 control（归属/allowed/tool_id/respond 限 ask_user/decisionId 幂等） | v2 删除了 session 预裁决（判为第二真理源） | **按法恢复**：校验对象是 session 自己拥有的 pending_pauses 投影（非重建 agent 状态），agent 仍是执行真源 |
| 6 | Session 数据模型 | sessions/messages/runs/session_events/pending_pauses；聊天主数据=messages；snapshot 端点 | 仅 session_events + runs 记录 | **按法补**（§3） |
| 7 | HTTP 面 | POST messages{idempotencyKey,content,...}=202；GET /sessions/:id snapshot；必删 executionStyle/permissionMode/conversationId | body 带 executionStyle/permissionMode/conversationId；无 snapshot | **按法改**（§4） |
| 8 | Agent 目录 | worker/run/execution/tools/subagents/skills/mcp/sandbox/storage/streams/model；**禁 run.invoke 类命名** | run/{builder,invoke,pump,emit,hitl} | **按法改回**执行链路布局（§2）；v2 的实质修复全部保留搬迁 |
| 9 | ToolPolicyMiddleware | P0：awrap_tool_call 做能力校验/参数规范化/审计 | v2 删除（判为空转投机） | **按法恢复**，但必须带真实行为：capabilities 白名单校验 + 审计 metadata（不留空壳） |
| 10 | 契约 codegen | handbook 未涉及（run/events.py 手写） | contract/spec 单源生成 14 镜像 + 字节门禁 | **保留 v2**（用户已认可的地基），反哺 handbook：wire 类型一律生成，run/ 只留非 wire 领域模型 |
| 11 | permissions | RuntimeConfig.permissions + interrupt_on；respond 只给 ask_user | permission_mode auto/default | **按法改**：wire 传已解析 permissions（approval 工具集、subagent_create、backend 策略）；respond 收紧 |
| 12 | namespace | RunContext.namespace = 隔离键（checkpoint/memory/lease/secret 按其隔离） | 无 | **落地**：RuntimeContext.namespace（V1 = session 派生 `local:{sessionId 前缀}` 或显式配置），thread_id/lease key/checkpoint 键带前缀 |
| 13 | skills/MCP | V1 必须支持 mount 加载 + MCP HTTP client；agent 不拥有 Hub | 无（v2 删了空壳） | **skills 全落地**（deepagents 原生 skills=路径挂载 + lock 校验 + fail-closed，本地目录 fixture 实测）；**MCP 落地 schema+装配+fail-closed**，真连接经 langchain-mcp-adapters（新增依赖），live smoke 单列后续（诚实标注） |
| 14 | swarm/TeamSpec | P2（更复杂专业 agent 编排） | 无 | **本轮不做**，维持讨论态（memory 已记） |
| 15 | 终态同 commit | terminal event + runs.status + activeRunId 清零同 Mongo commit | 无投影 | 单机 Mongo 无事务：**有序写**（event→projection→activeRunId）+ recover 收敛，规格注记；生产上 replica set 事务为后续 |
| 16 | 流名 | 11 号文档=kokoro:runs:requests / kokoro:run:{id}:events / kokoro:session:{id}:live（module 文档旧名作废） | 同 11 号 | 一致，仅新增 control 流 |

## 1. 契约（contract/spec 改版）

### control.yaml → run.request 新形状（wire, snake_case）
```
run.request:
  kind, run_id, thread_id            # thread_id = LangGraph configurable.thread_id（V1 取值=session_id，命名只在 agent 边界）
  input:      { message_id, content?, content_ref?, attachments? }   # V1 实现 message_id+content
  runtime:    RuntimeConfig
  context:    RuntimeContext
  trace:      { langfuse_trace_id?, ... }（record，观测专用不参与业务）
RuntimeConfig:
  model: { provider, name, effort? }          # effort 取代 execution_style 档位映射
  tools: [string]                             # 本次 run 启用的内建工具名
  skills: [ { name, path, lock } ]
  mcp:    [ { name, transport(http|streamable_http), url, allowed_tools[], timeout_s? } ]
  subagents: [ { name, description, system_prompt, tools[], model? } ]
  backend: state|local_shell|e2b|custom
  permissions: { approval_tools: [string], subagent_create: deny|ask|allow, filesystem: read_only|workspace_write }
RuntimeContext:
  namespace, session_id, site_id?, user_id?, workspace_id?, project_id?,
  recent_messages?, summary?, memory_scope?, feature_flags?
run.resume: { kind, run_id, thread_id, decisions: ResumeDecision[] }   # 走 control 流
run.cancel: { kind, run_id, thread_id }                                # 走 control 流
ResumeDecision 不变（approve{tool_id,args?}|edit{tool_id,args}|reject{tool_id,reason?}|respond{tool_id,response}）
```
删除：conversation_id、message 平铺字段、execution_style、permission_mode。checkpointer/store 是进程 infra 不上 wire（对 handbook 的注记性偏差）。

### events.yaml → 词汇改版
- raw（agent-out，信封 {kind, run_id, index, timestamp}）14 kind：`run.started, thinking.delta, message.delta, message.completed, tool.invoked, tool.awaiting_approval, tool.returned, todo.updated, subagent.started, subagent.finished, subagent.text.delta, subagent.text.completed, run.completed, run.failed`（text.* → message.*，字段 `text`→`delta`/`content` 按 handbook 旧 agui 语义：delta 事件用 `delta`，completed 用 `content`）
- session/browser 面 = raw 直透 + 合成 `session.created {title, owner_id}`（真实来自 sessions 集合）与 `run.created {run_id}`；15 kind
- tool.awaiting_approval payload：`segment_id, tool_id, name, args, description, allowed_decisions, kind(tool_approval|ask_user), risk{level,source,reason}?, editable, input_schema?, pending_tool_ids`
- tool.returned payload：`segment_id, tool_id, name, result, is_error, rejected?, reject_reason?, responded?, artifact_ref?, summary?`（后两者 optional，P1 生产者）
- run.completed：`{status, token_usage?}` 不变

### streams.yaml
+ `run_control: kokoro:run:{run_id}:control`（owner: session 写，agent 读，run 终态后 agent 认领方删除）
+ lease key 模板 `kokoro:agent:lease:{run_id}`（文档化现 RunStateStore 行为）

### http.yaml
- POST /sessions/:sid/messages → 202：body `{idempotency_key, content, selected_model?}`；receipt `{run_id, user_message_id, assistant_message_id}`；idempotency_key 命中返回同 receipt；活跃 run 存在 → 409 `session_run_active`
- GET /sessions/:sid → snapshot：`{session{...}, messages[], active_run?, pending_pauses[], event_watermark}`
- GET /sessions/:sid/events（SSE）与 POST control 不变；control body + `decision_id`（幂等）

## 2. kokoro-agent（回归执行链路布局，保留 v2 实质）

```
kokoro_agent/
  contract/            # 生成物（保留 v2 地基）
  worker/ main.py supervisor.py messages.py(薄：inbound=contract 校验+安全丢弃)
  run/ context.py(RunContext 非 wire 侧领域模型+namespace 派生) lifecycle.py(终态规则,消费 contract) 
  execution/ build_agent.py protocols.py run_agent.py resume_agent.py approvals.py events.py publish_agent_events.py prompts/
  tools/ registry.py permissions.py ask_user.py names.py middleware.py(ToolPolicyMiddleware: capabilities 校验+审计,真实现)
  subagents/ catalog.py definitions.py types.py
  skills/ mounts.py    # 路径+lock 校验，fail-closed → deepagents skills=
  mcp/ servers.py tools.py  # RuntimeConfig.mcp → langchain-mcp-adapters 客户端，fail-closed
  sandbox/ backend.py policy.py
  storage/ (v2 的 run_state TTL 租约/checkpoints 原样，键带 namespace)
  streams/ model/ config.py observability.py
```
映射：v2 `run/builder→execution/build_agent`、`run/invoke→execution/run_agent`、`run/pump+emit→execution/publish_agent_events+events`、`run/hitl→execution/{resume_agent,approvals}`、`worker/supervisor` 留 worker/。**行为保持**：TTL 租约、claim-before-emit、index 单调、pending 单点、fail-loud 对齐全部原样搬。
- interrupt_on 由 RuntimeConfig.permissions 生成；respond 只给 ask_user；awaiting 事件补 kind/risk/editable/input_schema。
- checkpoint thread_id = `{namespace}:{thread_id}`；lease/run-state 键带 namespace。
- 新依赖：langchain-mcp-adapters（仅 mcp/ 使用）。

## 3. kokoro-session

- store/ 扩为 sessions/messages/runs/session_events/pending_pauses 五集合（memory 同语义）：
  - POST messages：idempotency_key 查重 → 条件写 activeRunId（单 active run 准入）→ 写 user message + assistant placeholder + run 记录 → 构建 RunRequest（解析 RuntimeConfig 默认档 + RuntimeContext{namespace, session_id}）→ 发请求流 → 就地拉起 relay
  - relay：DB-first（event→append；投影：message.delta/completed 更新 assistant message、tool.awaiting→pending_pauses(pending)、tool.returned/终态→pause 收口；终态：runs.status+activeRunId=null+terminal event 有序写）→ live publish
  - session.created/run.created 合成于 run 首事件，元数据读 sessions 集合
- control：校验（run 归属/active、pause pending、tool_id 匹配、decision∈allowed、respond 限 ask_user、edit 参数过 schema 校验、decision_id 幂等）→ 写 pause decision → 发 `kokoro:run:{id}:control`
- snapshot 端点：GET /sessions/:sid
- recover：未终态 run 续 relay（不变）

## 4. kokoro-web

- engine：先 GET snapshot 水合（messages/active_run/pending_pauses）再 EventSource（Last-Event-ID=水位）；localStorage 不再承载 run 状态（只留 UI 偏好与会话列表索引）
- 词汇跟契约（message.*；session.created/run.created 解析，run.created 忽略投影）
- HITL 双 UI：kind=tool_approval → 审批卡（只展示 allowed_decisions 按钮，editable 且有定制 UI 才给编辑）；kind=ask_user → 问答卡（respond 提交、可取消 run）
- staging 仍以 pending_tool_ids 为完备判据；decision_id 随提交生成

## 5. 验收（在 v2 门禁上追加）

- contract：check.py + golden 全绿（词汇/形状改版后）
- agent：pytest+pyright+ruff；新增 skills mount fixture 实测、middleware 校验/审计单测、namespace 隔离断言、respond 限 ask_user 反例
- session：admission（双发同 key 同 receipt / 活跃 run 409）、pending_pauses 生命周期、control 校验矩阵、snapshot 恢复暂停点
- web：snapshot 水合、双 UI 分离、刷新后 pending pause 可继续
- 跨栈 e2e：POST→SSE 15 kind、HITL approve/reject/edit/respond（ask_user）、刷新 snapshot 续处理、cancel、SSE 断线 Last-Event-ID 续传
- handbook 反哺：modules/kokoro-agent.md 与 11/12 号文档更新「契约 codegen 单源 + pending_tool_ids 扩展 + checkpointer/store 不上 wire + 单机 Mongo 有序写」四处注记

## 6. 明示不做（本轮）

swarm/TeamSpec（P2）；MCP live smoke（依赖真 server，单列）；artifact_ref/summary 生产者（P1）；schema-driven 编辑器（P2）；多 active run。
