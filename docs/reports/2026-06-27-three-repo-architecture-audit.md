# 三仓库架构审计与清理白皮书

日期: 2026-06-27
范围: `kokoro-agent` / `kokoro-session` / `kokoro-web`，外加根仓 `contract/` 与规范文档作为控制面。
结论: 运行时主链路已经成型，MessageStore 分层正确；当前主要问题不是“大模块脏”，而是跨仓模型仍有几处多头维护、文档与代码源头错位，以及少量旧 codegen 残留。

## 一、三仓库拓扑与核心链路蓝图

```mermaid
flowchart LR
  W[kokoro-web\nNext.js UI / SSE consumer] -->|POST /sessions/:id/runs| S[kokoro-session\nHTTP/SSE + normalize + MessageStore]
  S -->|run.request / run.resume / run.cancel\nRedis stream kokoro:runs:requests| A[kokoro-agent\nDeepAgents/LangGraph worker]
  A -->|agent wire events\nkokoro:run:{run_id}:events| S
  S -->|DB history + bounded live bus\nSSE named events| W
  R[Kokoro root\ncontract/docs/prototypes] -. defines .-> A
  R -. defines .-> S
  R -. defines .-> W
```

核心链路:
- 发送与流式: web `consumeLiveSession()` 发 run URL，session `startRun()` 写 `run.request`，agent `RunSupervisor` 执行，session `Normalizer` 转 AGUI，SSE 回 web reducer。
- HITL: web `sendRunControl()` 发 `run.resume/run.cancel`，session 透传请求流，agent 根据 checkpoint/pending tools 续跑或取消。
- Replay/Resume: session 先从 MessageStore 读 DB 历史，再 tail `kokoro:session:{id}:live`；redis live 只是 512 条窗口，DB 是长期真源。

## 二、核心数据模型对比清单

| 模型 | 当前源头 | 其他镜像 | 审计结论 |
|---|---|---|---|
| Agent wire event | `kokoro-agent/src/kokoro_agent/interfaces/envelope.py` | `kokoro-session/src/domain/agent-event.ts` 由 `contract/agent_wire.py` 生成 | 源头清楚，但根 `events.yaml` 仍保留旧 `agent_out` 视图，易误导。 |
| AGUI/session event | `contract/events.yaml` | session `session-event.ts`、web `transport-event-schema.ts` / `session-stream-event.ts` | `verify.py` 与 `generate.py --check` 当前通过。 |
| RunRequest | session `run-request.ts`、agent `run_request.py`、web `PermissionMode` | 手写 | 存在真实 drift: session 接受 `plan`，agent/web 不接受。 |
| HITL control | agent `inbound.py`、session `run-control.ts`、web `transport.ts` | 手写 | 三处维护，无 contract/codegen gate。 |
| Web SessionStreamState | web `types.ts` + `state-schema.ts` | 手写 | 运行态字段与落盘 schema 漂移，会导致 localStorage 快照被严格丢弃。 |
| Run terminal status | `contract/events.yaml` | session schema / web schema / reducer | web wire 接收 `status`，domain/reducer 丢弃，取消/超时 replay 语义丢失。 |

## 三、架构缺陷与脏代码诊断报告

### H1 - 模型异构 - High

代码定位: `kokoro-session/src/domain/run-request.ts:11` 接受 `permission_mode` = `auto/default/plan`; `kokoro-agent/src/kokoro_agent/domain/run_request.py:12` 只接受 `auto/default`; `kokoro-web/src/application/session-stream/transport.ts:42` 也只定义 `auto/default`。文档 `docs/requirements/00-product/trust-modes.md:19` 明确说 Plan 已建。

病灶分析: session 测试还专门断言 `plan` 合法(`kokoro-session/tests/run-request.test.ts:43`)，但同一请求到 agent 后会被 Pydantic 拒收。web 不暴露 Plan，所以这个 bug 目前被 UI 掩盖；一旦 API 或测试直接发 `plan`，链路会在 agent 入站解析失败。

### H2 - 职责/模型丢失 - High

代码定位: agent 工具事件已经带 `subagent_id`，见 `kokoro-agent/src/kokoro_agent/interfaces/envelope.py:41`、`kokoro-agent/src/kokoro_agent/application/run/consumer.py:152`；session 入站也接收它，见 `kokoro-session/src/domain/agent-event.ts:20`。但 `kokoro-session/src/application/normalize.ts:78` 到 `:110` 归一化为顶层 `tool.*` 时丢掉 `subagent_id`。

病灶分析: 子代理内工具调用会在 web 上表现成顶层工具，归属关系消失。现有 `subagent.text.*` 已有独立通道，工具通道没有同等建模，导致 agent 已产出的结构化信息在 session 层被截断。

### H3 - 契约字段被消费端吞掉 - High

代码定位: `contract/events.yaml:48` 定义 `run.completed.status = completed/cancelled/timeout`；web 入站 schema 接收它，见 `kokoro-web/src/infrastructure/transport-event-schema.ts:197`。但 mapper 只投影 `finalMessageId`，见 `kokoro-web/src/infrastructure/transport-event-mapper.ts:49`；domain union 也没有 `status`，见 `kokoro-web/src/domain/session-stream-event.ts:147`；reducer 一律写 `runStatus = "completed"`，见 `kokoro-web/src/application/session-stream/reducer.ts:362`。

病灶分析: 取消或超时在 replay 后会退化成普通完成。停止按钮本地有乐观收口，但刷新、换设备、DB replay 只能看到后端权威事件，web 当前不保留终态原因。

### H4 - 本地持久化模型漂移 - High

代码定位: 运行态 `SessionToolCall` 有 `rejectReason/responded`，见 `kokoro-web/src/application/session-stream/types.ts:20`; `SessionSubagent.status` 有 `failed`，见 `:33`。落盘 schema 的 tool 没有这些字段，见 `kokoro-web/src/application/session-stream/state-schema.ts:14`; subagent status 只允许 `running/done`，见 `:25`。

病灶分析: `serializeSessionState()` 会把运行态对象原样写入 localStorage，`parseStoredSessionState()` 又用 `.strict()` 读回。包含 reject reason、人工答复或 failed subagent 的会话，刷新后可能被判为脏数据并整体丢弃。

### H5 - 协议文档与当前代码不一致 - High

代码定位: `docs/protocol/agent-events.md:53` 仍描述旧 `kind/run_id/seq/payload` agent 事件；实际当前是 `event/request_id/timestamp/data`，见 `kokoro-agent/src/kokoro_agent/interfaces/envelope.py:127` 与 `kokoro-session/src/domain/agent-event.ts:14`。`docs/protocol/session-stream.md:16` 仍写最小 6 事件和 `message_id`，但当前 contract 是 15 wire events 和 `segment_id`，见 `contract/events.yaml:66` 起。

病灶分析: 根仓是规范源头，但最显眼的 protocol 文档落后于 codegen 事实。新贡献者按文档实现会写回旧字段；这比普通注释过时更危险，因为它处在跨仓契约层。

### M1 - 三套 control schema 手写 - Medium

代码定位: agent `kokoro-agent/src/kokoro_agent/interfaces/inbound.py:21`; session `kokoro-session/src/domain/run-control.ts:5`; web `kokoro-web/src/application/session-stream/transport.ts:31`。

病灶分析: `run.resume` 的 approve/edit/reject/respond 是跨仓协议，但不在根 contract gate 内。当前 web 只暴露 approve/reject 是合理 UI 子集，但 schema 本身没有单源，后续 edit/respond UI 或多工具审批很容易漂移。

### M2 - codegen 旧方案死代码 - Medium

代码定位: `contract/generate.py:30` 的 `AGENT_EVENT_PY` 指向不存在的旧生成物；`emit_session_agent_event()` 在 `:308`、`emit_agent_event_py()` 在 `:403`，但 `EMITTERS` 只使用 `agent_wire.emit_agent_event_ts()`，见 `:451`。设计勘察文档也已承认这是遗留死码，见 `docs/superpowers/specs/2026-06-24-tool-call-status-model-design.md:160`。

病灶分析: 这会让人误以为 `events.yaml.agent_out` 仍驱动 agent 端模型，实际 agent-out 单源已经变成 `envelope.py`。

### M3 - 新贡献者入口文档过时 - Medium

代码定位: `kokoro-agent/README.md:13` 仍写 `domain/agent_event.py` 与 `application/run_agent.py`; `:60` 仍写 agent `seq` per-run 单调。实际 normalize 注释明确“agent 不再发 seq”，见 `kokoro-session/src/application/normalize.ts:5`。

病灶分析: README 是贡献者第一入口。当前会把人带到不存在的文件和旧排序模型。

### M4 - 仓库卫生与工具链信号混乱 - Medium

证据: 根 `git status` 当前在 `test/hitl-e2e-gate` 分支，并有未跟踪 `.superpowers/`、`kokoro-platform/`；`kokoro-web` 有未跟踪 `docs/` 与 `pnpm-workspace.yaml`。`kokoro-session` 与 `kokoro-web` 同时存在 `bun.lock` 和 `pnpm-lock.yaml`，而 README/脚本主张 Bun。

病灶分析: 这不一定破运行时，但会让“顶级仓库”观感变差：贡献者不知道该用 Bun 还是 pnpm，也不知道 `kokoro-platform` 是第四运行时、规划仓，还是临时目录。

## 四、彻底清理与重构实施方案

### 针对 H1 的清理指令

核心动作: 逻辑收敛。先决定 Plan 是否当前能力。根据现有产品文档，建议以 `Plan/Default/Auto` 为真实三态。

重构骨架:
```ts
// contract/run-request.yaml -> generate TS/Py
permission_mode: enum [auto, default, plan]
execution_style: enum [fast, thinking]
```
```py
def build_interrupt_on(mode: PermissionMode) -> dict[str, InterruptOnConfig]:
    if mode == "auto":
        return {}
    tools = config.approval.requires_approval_tools
    if mode == "plan":
        tools = tools | config.approval.plan_only_tools
    return {tool: InterruptOnConfig(allowed_decisions=_APPROVAL_DECISIONS) for tool in tools}
```
同步改 agent/web/session 三处类型和测试；若暂不做 Plan，则从 session schema 与文档删掉 `plan`，不要保留半能力。

### 针对 H2 的清理指令

核心动作: 跨库解耦 + 契约补全。Source of Truth 是 agent `envelope.py` 对子代理归属的事实，AGUI 层应显式承载。

推荐方案: 在 `events.yaml` 加 `subagent.tool.invoked / subagent.tool.awaiting_approval / subagent.tool.returned`，payload = 顶层 tool payload + `subagent_id`。`normalize.ts` 按 `event.data.subagent_id` 拆通道；web reducer 将这些步骤挂到对应 subagent step 内，而不是顶层 steps。

### 针对 H3 的清理指令

核心动作: 逻辑收敛。把 `run.completed.status` 传到 web domain。

重构骨架:
```ts
type RunCompleted = {
  kind: "run-completed"
  status: "completed" | "cancelled" | "timeout" | string
}

case "run-completed":
  nextState.runStatus =
    event.status === "cancelled" ? "cancelled" :
    event.status === "timeout" ? "timeout" : "completed"
```
同时更新 `SessionStreamState.runStatus`、落盘 schema、UI 文案和 replay 测试。

### 针对 H4 的清理指令

核心动作: 收敛 web 运行态与落盘态。`types.ts` 与 `state-schema.ts` 必须同轮更新。

必须补的测试:
- rejected tool 带 `rejectReason` round-trip。
- responded tool round-trip。
- `subagent.status="failed"` + `error` round-trip。

### 针对 H5/M3 的清理指令

核心动作: 删除旧协议叙述，保留一个当前真相。

执行顺序:
1. `docs/protocol/agent-events.md` 改写为 `event/request_id/timestamp/data`，声明 agent-out 单源是 `interfaces/envelope.py`。
2. `docs/protocol/session-stream.md` 改写为当前 15 wire events、`segment_id`、MessageStore replay 事实。
3. 修 `kokoro-agent/README.md` 的目录树、生成物说明、seq 说明。
4. 修 `docs/requirements/00-product/scope-and-boundary.md:45`，HITL 不能同时“已建”和“未实现”。

### 针对 M1/M2/M4 的清理指令

核心动作:
- M1: 新建 `contract/control.yaml` 或 `contract/run-command.yaml`，生成 agent Pydantic、session Zod、web TS 子集类型；至少加 drift test。
- M2: 从 `contract/generate.py` 删除 `AGENT_EVENT_PY`、`_agent_events`、`emit_session_agent_event`、`emit_agent_event_py`，并从 `events.yaml` 移除不再驱动代码的 `agent_out` 视图。
- M4: 选择每个 TS 仓唯一包管理器信号。若三 runtime 继续独立仓，`kokoro-web/pnpm-workspace.yaml` 不应留在 web 子仓根；`kokoro-platform` 要么正式纳入 ADR，要么移出/归档为规划工作区。清掉 `kokoro-agent/.coverage` 与 `src/**/__pycache__` 缓存。

## 第二轮深扫补充（2026-06-27）

### H6 根仓拓扑事实与 ADR/CI 自相矛盾

证据: 根仓存在 `.gitmodules:1-9`，`git ls-files --stage kokoro-agent kokoro-session kokoro-web` 显示三项都是 `160000` gitlink。当前根仓 `kokoro-session` 的 dirty 状态不是普通文件改动，而是子模块指针从 `89eff98` 前进到 `b542656`。但 `ADR-009` 明确说 Kokoro 是 docs/prototype/protocol 源头仓、禁止 Monorepo 硬引用，并且 `.github/workflows/contract.yml:3-5` 注释还写“四仓独立(非 submodule)”。同一个 workflow 又在 `kokoro-agent` / `kokoro-session` / `kokoro-web` 路径重新 checkout sibling `main`，实际绕过了根仓 gitlink 指针。

病灶分析: 现在有两个互相竞争的 runtime 版本真相。开发者本地看到的是 submodule 指针；CI 看到的是 sibling `main`；文档声称的是独立非 submodule。后果是顶级仓库会长期表现为“子仓指针脏”，且无法解释当前检查到底验证了 gitlink 所指 commit，还是远端 main。

清理方向只能二选一:
1. **承认治理型 submodule 根仓**: 更新 ADR，把三 runtime 作为受控 gitlink；每次子仓合并后同步提交 gitlink bump；CI 使用 submodule SHA 或显式校验 gitlink 与 checkout 版本一致。
2. **恢复纯协议/docs 根仓**: 删除 `.gitmodules` 与 gitlink，把 runtime checkout 放到 `.gitignore` 的 workspace 路径或脚本生成路径；用 `repos.yaml` / `docs/CODEBASE_MAP.md` 记录应读仓库和分支，而不是把 runtime 作为根仓索引项。

不要保持当前混合态。若目标是“看着是一个顶级的代码仓库”，这一步应先于任何目录重排。

### H7 门禁只锁字段名，锁不住语义和落盘 round-trip

证据:
- 根 `contract/test_contract.py:23-109` 证明 drift compare 能发现 kind/payload 字段名差异，但不覆盖字段语义、枚举收敛、mapper 投影和 web 落盘 round-trip。
- `kokoro-web/tests/infrastructure/transport-event.test.ts:52-64` 只断言 `run.completed{status:"cancelled"}` 能 parse 并映射到 `kind="run-completed"`，没有断言 status 被保留。
- 实现上 `kokoro-web/src/infrastructure/transport-event-mapper.ts:49-54` 丢弃 `payload.status`，`kokoro-web/src/application/session-stream/reducer.ts:362-365` 无条件把 run 置为 `completed`。
- `kokoro-web/tests/application/session-stream/state-schema.test.ts:16-48` 只覆盖 running tool / running subagent 的基本 shape；而运行时类型已经包含 `tool.rejectReason`、`tool.responded`、`subagent.status="failed"` 和 `subagent.error`。`state-schema.ts:14-34` 仍拒绝这些字段。

病灶分析: 当前门禁足以防止“字段名漏生成”，但不足以防止“字段被 parse 后丢失”“状态枚举被降级”“落盘 strict schema 拒绝当前运行态”。这正是 H3/H4 能在测试存在的情况下留下来的原因。

必须补的测试层:
1. contract 层加语义用例: `run.completed.status` 从 agent/session 到 web domain 必须保留；`cancelled/timeout` 不得在 reducer 里变成普通 completed。
2. web reducer + persistence 加 round-trip: rejected tool 带 `rejectReason`、responded tool 带 `responded`、failed subagent 带 `error`，经过 `serializeSessionState` / `parseStoredSessionState` 后仍能恢复。
3. CI 中把这些作为 blocking tests，而不是只依赖 `verify.py` 的字段集合检查。

### M5 手工 e2e gate 未进入 CI，真实跨进程链路仍靠人记得跑

证据: 三个子仓 workflow 都只跑本仓 lint/typecheck/test/build；根 workflow 只跑 `contract/verify.py`、`generate.py --check` 和 contract 自测。`scripts/sse-loopback-gate.sh` 覆盖真实 agent->Redis->session->SSE 主路径，`scripts/hitl-e2e-gate.sh` 覆盖真实 redis + worker + session 的 HITL approve/cancel 反向通道，但二者都没有被任何 workflow 调用。根 README 只把 SSE 回环列为“提交前跑”，HITL gate 甚至没有出现在门禁表里。

建议: 建一个 `e2e.yml`，至少 `workflow_dispatch` + nightly 运行；如果 PR 上跑成本太高，就把脚本标为 required manual gate，并把结果记录到 PR/checklist。当前这种“脚本存在但 CI 不知道”的状态会让跨仓回归继续漏出。

### M6 需求手册漂移不止 H5 的 protocol 文档

证据:
- `docs/requirements/00-product/trust-modes.md:19-23,40` 写 Plan/Default/Auto 工具审批已落地。
- `docs/requirements/00-product/scope-and-boundary.md:45`、`01-capabilities/agent-activity.md:37`、`01-capabilities/tools.md:34`、`02-flows/tool-run.md:45`、`01-capabilities/extension-points.md:31-35` 又把 HITL 写成未实现/留缝。
- `docs/requirements/01-capabilities/streaming.md:20`、`02-flows/send-and-stream.md:37-38` 仍写 `text.delta` / `text.completed`，而当前 session->web 合同是 `message.delta` / `message.completed` + `segment_id`。
- `docs/protocol/session-stream.md:38-60` 和 `session-replay-and-resume.md:14-39` 仍围绕 `cursor` / `message_id` 叙述；当前运行态使用一等 `seq`、`event_id` 和 `segment_id`。

建议: 文档清理不要只改 `docs/protocol/*`。应以 `contract/events.yaml` + runtime schema 为真相，批量修 `docs/requirements/00-product`、`01-capabilities`、`02-flows`、`03-contracts`，并把 HITL 从 extension-points 移到已建能力，单独标注“FS 写审批仍未建”。

### M7 `kokoro-platform` 是未纳入 ADR 的运行时工作区

证据: `kokoro-platform/README.md:1-67` 定义平台域父仓库、模块注册表、本地 MySQL、统一命令；`kokoro-platform/package.json:1-17` 是 pnpm workspace 根，依赖 `@kokoro/user/model/credit/payment`。其中 model/credit/payment 目前 `status: "planned"`，但 `kokoro-user` 已有 Prisma、HTTP routes 和集成测试。与此同时，`ADR-009:12-20` 仍声明系统按 4 个独立 Git 仓拆分，Kokoro 根仓不承载运行时代码。

建议: 若平台域是下一阶段方向，补 ADR 并把它作为独立 sibling 仓或受控 workspace 纳入规范；若只是规划草稿，移到 docs/规划区或从根仓移除。不要让一个真实 pnpm workspace 以 untracked 目录形态挂在协议根仓里。

### M8 并行治理素材缺失，外部 worker 无法按项目规范吃完整地图

证据: 当前没有 `docs/CODEBASE_MAP.md`，但项目 AGENTS 规则要求外部 worker prompt 注入它。第二轮我没有继续派外部 worker，避免在缺地图的情况下制造隐形工作。

建议: 在顶级重构前生成并维护 `docs/CODEBASE_MAP.md`，至少包括三 runtime、root contract/docs、平台域是否纳入、每仓测试/CI/包管理器命令。否则后续并行重构会反复浪费在定位和边界误解上。

## 优先级路线图

1. P0: H6 + H1 + H3 + H4。先决定根仓拓扑，再修用户可见或 API 可触发的真实 drift。
2. P1: H7 + H2 + M1。把语义测试、子代理工具归属和 control schema 纳入契约治理。
3. P2: H5/M2/M3/M6。更新 protocol + requirements + README，并删旧 codegen 分支，避免新贡献者按旧模型写代码。
4. P3: M4/M5/M7/M8。仓库卫生、包管理器统一、`kokoro-platform` 归属、e2e gate 自动化和 `CODEBASE_MAP`。

## 本次验证

- `python3 contract/verify.py`: PASS，agui/render/transport/envelope mirrors 当前匹配。
- `python3 contract/generate.py --check`: PASS，4 个当前生成镜像匹配。
- 三个并行 explorer 因并发额度中断，最终结论全部来自主会话逐文件核查。
