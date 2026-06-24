# Tool-Call 状态实体模型端到端补全 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让"工具调用"成为权威的、replay 安全的状态实体（running/awaiting/rejected/done/error）端到端贯通四仓，补全 HITL rejected、subagent 归属、多工具多决策三处缺口。

**Architecture:** 不重建 wire（消费端 `SessionToolCall.status` 已是规范模型、事件溯源支撑 replay）。在现有 `tool.invoked`/`tool.awaiting_approval`/`tool.returned` 事件上补字段：agent 侧权威发 `rejected`、给工具事件带 `subagent_id`；契约单源 `contract/events.yaml` 加可选字段后重生成 5 镜像；session 透传；web 丢弃乐观-only reject 改读后端权威。contract-first，四仓 coupled。

**Tech Stack:** kokoro-agent（Python 3.14 运行 / mypy targeting 3.11，Pydantic v2，langchain 1.x + langgraph + deepagents 0.6，pytest）；contract（events.yaml + generate.py + verify.py，纯 pyyaml+pydantic）；kokoro-session（Bun + Zod）；kokoro-web（Next.js + vitest）。

## Global Constraints

- **依赖已删除（打包态）**：执行**任何**任务前必须先恢复依赖，否则门禁跑不了：`cd kokoro-agent && uv sync`；`cd kokoro-session && bun install`；`cd kokoro-web && pnpm install`。
- **契约单源**：`contract/events.yaml` 是唯一真理源；改它后必须 `python3 contract/generate.py` 重生成 5 镜像，再 `python3 contract/generate.py --check`（无漂移）+ `python3 contract/verify.py`（exit 0）。**绝不手改生成文件**（顶部有 `DO NOT EDIT`）。
- **agent 门禁全绿且零 skip 新增**：`uv run --no-sync mypy src/kokoro_agent`（Success）、`uv run --no-sync pyright`（**0 errors**，看数值非 grep）、`uv run --no-sync pytest -q`、`uv run --no-sync ruff check`。
- **session 门禁**：`bun run typecheck` + `bun test`。**web 门禁**：`pnpm run typecheck`（tsc --noEmit）+ `pnpm test`（vitest run）。
- **代码铁律**：零 `# type: ignore`/`cast`/`Any`/`object` 兜底（框架边界 `**kwargs: Any` 除外）；注释只写 WHY ≤1 行；Pydantic `ConfigDict(strict=True, extra="forbid")`；Zod `.strict()`。
- **commit message 禁含** `Co-Authored-By: Claude ...`（用户硬禁，覆盖默认）。
- **wire 字节兼容**：新增字段一律 optional/NotRequired；现有不含新字段的测试断言必须保持绿（兼容铁证）。
- **新增字段命名**（全仓一致）：snake_case `subagent_id` / `reject_reason`（agent+contract+session payload）；camelCase `subagentId` / `rejectReason`（web render）。
- **分支与合并**：每仓开 `feat/tool-call-status` 分支；contract-first 落地后 coupled PR 一起合（web 先于 parent，参 stacked-squash playbook：parent contract CI 检出 sibling main）。

---

## 文件结构与职责（改动面地图）

**kokoro-agent**
- `interfaces/envelope.py` — `ToolStartData`/`ToolEndData` 加 `subagent_id: NotRequired[str]`；`ToolEndData` 加 `reject_reason: NotRequired[str]`；`SubagentFinishedStatus` 加 `failed: NotRequired[bool]` + `error: NotRequired[str]`。
- `application/projection/transformer.py` — `tool_start_event`/`tool_end_event` 增 `subagent_id` 形参并写入；`tool_end_event` 的 `rejected` 由真实来源派生（Task 0 机制）+ 写 `reject_reason`；`subagent_finished_event` 增 failed/error。
- `application/run/consumer.py` — `_consume_tools` 接收并透传 `subagent_id`；`_consume_subagents` 传子代理失败信息。
- `application/projection/awaiting.py` — 子代理待批：带 `subagent_id`。
- `interfaces/inbound.py` — `RunResume.decision: ResumeDecision` → `decisions: list[ResumeDecision]`，每 arm 加 `tool_id`。
- `application/run/supervisor.py` — `_on_resume` 组多决策 `Command(resume={"decisions":[...]})`；reject 关联（若 Task 0 选机制 B）。

**contract** — `events.yaml`（tool 三事件 + subagent.finished + field_types + render_optional + payload_optional + agui_out_web_extra），重生成 5 镜像。

**kokoro-session** — `application/normalize.ts`（tool_call_* 三 case 透传新字段）；`domain/agent-event.ts` + `domain/session-event.ts`（由 contract 重生成，勿手改）。

**kokoro-web** — `application/session-stream/types.ts`（`SessionToolCall` 加 `rejectReason?`/`subagentId?`）；`application/session-stream/state-mutations.ts`（删乐观-only reject，改读后端权威 rejected）；`application/session-stream/reducer.ts`（消费 rejected/reject_reason/subagent_id）；`infrastructure/transport-event-schema.ts` + `domain/session-stream-event.ts`（contract 重生成）。

---

## Task 0: SPIKE — reject 观测机制 + resume 决策匹配语义

**前置阻断**：Task 2 与 Task 5 依赖本任务结论。先做。需先 `cd kokoro-agent && uv sync`。

**两个必答问题（读 langchain HITL 中间件源 + 实证 probe）**：
1. **reject 观测**：用户 reject 一个被门控工具后，agent 在 `astream_events(v3)` 的 tool projection 里看到的那条工具结果，是否带**机器可读标记**（如 `ToolMessage.status == "error"`、或 metadata `decision/rejected`）？
2. **resume 匹配**：langchain HITL `Command(resume={"decisions":[...]})` 把多个 decision 匹配到多个 pending 工具，是按 **list 顺序**还是按 **tool_call_id**？

- [ ] **Step 1: 定位并读源**

```bash
cd /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-agent
uv sync
python3 -c "import langchain.agents.middleware.human_in_the_loop as m; print(m.__file__)"
# 读该文件：搜 reject / respond / edit / ToolMessage / status / Command / resume / decisions
```

- [ ] **Step 2: 实证 probe（最小可运行）**

写 `/tmp/probe_reject.py`：用 `KOKORO_LOCAL_FAKE_MODEL=1` 构 deepagents agent，interrupt_on 一个工具，跑到 awaiting，发 `Command(resume={"decisions":[{"type":"reject","message":"no"}]})`，打印 resume 后 `aget_state().values["messages"]` 里那条 ToolMessage 的 `repr` + `.status` + `.response_metadata`。同样对 2 个 pending 工具发乱序 decisions，看匹配是按序还是按 id。

```bash
KOKORO_LOCAL_FAKE_MODEL=1 uv run --no-sync python /tmp/probe_reject.py
```

- [ ] **Step 3: 记录结论 + 选型**

把结论写进 `docs/superpowers/specs/2026-06-24-tool-call-status-model-design.md` 的 §5（追加"SPIKE 结论"小节）：
- reject 观测 → **机制 A**（原生标记可读，Task 2 走 A 代码）或 **机制 B**（无标记，Task 2 走 supervisor 关联 + run_state 持久化 reject 的 tool_id 集合）。
- resume 匹配 → 顺序 or by-id（定 Task 5 的 RunResume.decisions 是否必须携带 tool_id 且 supervisor 是否需按 pending 顺序重排）。

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/specs/2026-06-24-tool-call-status-model-design.md
git commit -m "spike(hitl): 实证 reject 观测机制 + resume 决策匹配语义，定 Task2/5 选型"
```

**Produces:** 机制决策（A/B）+ 匹配语义（order/id），后续任务据此选具体代码路径。

---

## Task 1: contract — tool/subagent 事件加可选字段 + 重生成

**Files:**
- Modify: `contract/events.yaml`（tool.invoked/awaiting_approval/returned、subagent.finished、field_types、render_optional、payload_optional、agui_out_web_extra）
- Regenerated（勿手改）: `kokoro-web/src/{domain/session-stream-event.ts,infrastructure/transport-event-schema.ts}`、`kokoro-session/src/domain/{agent-event.ts,session-event.ts}`、`kokoro-agent/src/kokoro_agent/application/events/agent_event.py`

**Interfaces — Produces:** tool 三事件 payload 含可选 `subagent_id`；`tool.returned` 含可选 `reject_reason`；`subagent.finished` 含可选 `failed`/`error`。下游 Task 2/3/6/7/8 消费。

- [ ] **Step 1: 改 events.yaml — 给三个 tool 事件加 subagent_id（agent_out + agui_out_web_extra + render）**

`tool.invoked`/`tool.awaiting_approval`：`agent_out.payload` 与 `agui_out.payload` 末尾加 `subagent_id`；`agui_out` 加/合并 `agui_out_web_extra: [subagent_id]`；`render.payload` 加 `subagentId`。
`tool.returned`：`agent_out.payload` 与 `agui_out.payload` 加 `subagent_id, reject_reason`；`agui_out_web_extra: [subagent_id, reject_reason]`；`render.payload` 加 `subagentId, rejectReason`。

- [ ] **Step 2: 改 events.yaml — subagent.finished 加 failed/error（可选）**

找到 subagent.finished（agent_status 的 subagent_finished 投影对应 kind），其 payload 加 `failed, error`；`render` 加 `failed, error`。

- [ ] **Step 3: 改 events.yaml — 类型与可选声明**

`field_types` 加：`reject_reason: string`、`error: string`（若未有）、`failed: boolean`、`subagent_id: string`（默认即 string_nonempty，但 subagent_id 允许空？保持 string_nonempty）。
`render_optional` 加 `subagentId, rejectReason, failed, error`。
`payload_optional`（snake_case strict payload 的可选）加 `subagent_id, reject_reason, failed, error`。

- [ ] **Step 4: 重生成 + 门禁**

```bash
cd /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro
python3 contract/generate.py
python3 contract/generate.py --check   # 期望 OK — N mirrors match
python3 contract/verify.py             # 期望 exit 0
git -C kokoro-web diff --stat; git -C kokoro-session diff --stat; git -C kokoro-agent diff --stat
```
Expected: 仅上述 5 镜像因新可选字段变化；verify 绿。

- [ ] **Step 5: Commit（contract 仓 + 各 sibling 仓分别提交生成产物）**

```bash
cd /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro
git add contract/events.yaml && git commit -m "feat(contract): tool 事件加 subagent_id/reject_reason + subagent.finished 加 failed/error(均可选)"
git -C kokoro-agent add -A && git -C kokoro-agent commit -m "chore(agent): 重生成 agent_event 镜像(subagent_id/reject_reason/failed)"
git -C kokoro-session add -A && git -C kokoro-session commit -m "chore(session): 重生成 agent-event/session-event 镜像"
git -C kokoro-web add -A && git -C kokoro-web commit -m "chore(web): 重生成 transport/session-stream 镜像"
```

---

## Task 2: agent — rejected 权威化（replay 安全核心）

**依赖 Task 0 结论。** 下面给**机制 A**（原生标记）完整代码；若 Task 0 定为机制 B，见末尾「机制 B 变体」。

**Files:**
- Modify: `kokoro-agent/src/kokoro_agent/interfaces/envelope.py`（ToolEndData 加 `reject_reason: NotRequired[str]`）
- Modify: `kokoro-agent/src/kokoro_agent/application/protocols/agent.py`（`ToolCallInfo`/`ToolCallView` 暴露 reject 标记，如 `status: str`，按 Task 0 实测字段）
- Modify: `kokoro-agent/src/kokoro_agent/application/projection/transformer.py`（`tool_end_event`）
- Test: `kokoro-agent/tests/projection/test_transformer.py`、`kokoro-agent/tests/run/test_hitl_e2e.py`

**Interfaces — Consumes:** Task 0 的 reject 标记字段名。**Produces:** `tool_end_event` 在 reject 时发 `rejected: True` + `reject_reason`。

- [ ] **Step 1: 写失败测试 — rejected 权威 + replay 安全（test_transformer.py）**

```python
def test_tool_end_event_rejected_authoritative() -> None:
    # reject：is_error=False 但 rejected=True + 理由，replay 安全地区别于绿勾 done。
    tc = _FakeTool("t-rej", "danger", {}, output="rejected by human", rejected=True, reject_reason="no")
    ev = tool_end_event(tc, request_id=KORO)
    assert ev.data["rejected"] is True
    assert ev.data["is_error"] is False
    assert ev.data["reject_reason"] == "no"
```
（`_FakeTool` dataclass 增 `rejected: bool = False`、`reject_reason: str | None = None` 字段。）

- [ ] **Step 2: 跑测试确认失败**

```bash
cd kokoro-agent && uv run --no-sync pytest tests/projection/test_transformer.py::test_tool_end_event_rejected_authoritative -v
```
Expected: FAIL（rejected 恒 False / 无 reject_reason 键）。

- [ ] **Step 3: 实现 — envelope + transformer**

`envelope.py` `ToolEndData` 加 `reject_reason: NotRequired[str]`。
`transformer.py` `tool_end_event`：
```python
def tool_end_event(tc: ToolCallInfo, *, request_id: str, subagent_id: str | None = None) -> AgentEvent:
    rejected = tc.rejected  # Task 0 机制 A：来自 v3 ToolCallView 的原生 reject 标记
    data: ToolEndData = {
        "segment_id": tc.tool_call_id,
        "tool_id": tc.tool_call_id,
        "name": tc.tool_name,
        "result": _result_text(tc),
        "is_error": tc.error is not None,
        "rejected": rejected,
    }
    if rejected and tc.reject_reason:
        data["reject_reason"] = tc.reject_reason
    if subagent_id is not None:
        data["subagent_id"] = subagent_id
    return _make_event("tool_call_end", request_id, data)
```
（`ToolCallInfo` Protocol 加 `rejected: bool` + `reject_reason: str | None`，字段名按 Task 0 实测对齐。）

- [ ] **Step 4: 跑测试确认通过 + 全门**

```bash
cd kokoro-agent && uv run --no-sync pytest tests/projection/test_transformer.py -q
uv run --no-sync mypy src/kokoro_agent && uv run --no-sync pyright && uv run --no-sync ruff check
```

- [ ] **Step 5: 写 replay-safety e2e（test_hitl_e2e.py）**

在现有 reject 用例后加断言：reject 后 `tool_call_end` 的 data `rejected is True`、`is_error is False`；把发布的事件流重新喂一遍 reducer-like 累积（或直接断言事件序列），确认终态仍 rejected，不退化为 done。

- [ ] **Step 6: 全门 + Commit**

```bash
cd kokoro-agent && uv run --no-sync pytest -q  # 零新 skip
git add -A && git commit -m "feat(agent): HITL rejected 权威化 — tool_call_end 发 rejected/reject_reason(replay 安全)"
```

**机制 B 变体（若 Task 0 定 B）**：reject 标记不在 stream。改为：`supervisor._on_resume` 处理 RejectDecision 时，把 `(run_id, tool_id)` 存入 `RunStateStore`（新增 `mark_rejected`/`is_rejected`）；`invoke_once` 把 `rejected_tool_ids` 查询函数传入 projection，`tool_end_event` 据此置 rejected。测试相应注入 fake store。此变体多触及 `application/protocols/run_state.py` + 三 store 实现。

---

## Task 3: agent — subagent_id 贯穿工具事件

**Files:**
- Modify: `kokoro-agent/src/kokoro_agent/interfaces/envelope.py`（ToolStartData 加 `subagent_id: NotRequired[str]`，ToolEndData 已在 Task 2 加）
- Modify: `kokoro-agent/src/kokoro_agent/application/projection/transformer.py`（`tool_start_event`/`todo_event` 增 `subagent_id`）
- Modify: `kokoro-agent/src/kokoro_agent/application/run/consumer.py`（`_consume_tools` 增 `subagent_id` 形参，`_consume_subagents` 递归传入）
- Test: `tests/projection/test_transformer.py`、`tests/run/test_invoke.py`（子代理工具带 id）

**Interfaces — Produces:** 子代理内工具的 invoked/end 事件带 `subagent_id`。

- [ ] **Step 1: 失败测试**

```python
def test_tool_start_event_carries_subagent_id() -> None:
    tc = _FakeTool("c-1", "search", {"q": "x"})
    ev = tool_start_event(tc, request_id=KORO, subagent_id="sub-7")
    assert ev.data["subagent_id"] == "sub-7"

def test_tool_start_event_toplevel_omits_subagent_id() -> None:
    ev = tool_start_event(_FakeTool("c-1", "search", {}), request_id=KORO)
    assert "subagent_id" not in ev.data
```

- [ ] **Step 2: 确认失败** → `pytest tests/projection/test_transformer.py -k subagent_id`
- [ ] **Step 3: 实现** — `tool_start_event(tc, *, request_id, subagent_id=None)`：`if subagent_id is not None: data["subagent_id"] = subagent_id`。`consumer._consume_tools(tool_calls, request_id, queue, subagent_id)` 透传给 start/end；`_consume_subagents` 调 `consume_run(sub, ..., subagent_id=sub.trigger_call_id)` 已存在，确保 `_consume_tools` 收到该 id（当前 `consume_run` 的 tool 分支未传 subagent_id —— 补上）。
- [ ] **Step 4: 通过 + 全门**
- [ ] **Step 5: Commit** — `feat(agent): 工具事件带 subagent_id（子代理嵌套工具归属）`

---

## Task 4: agent — 子代理待批 awaiting 归属

**Files:**
- Modify: `kokoro-agent/src/kokoro_agent/application/projection/awaiting.py`（`awaiting_approval_events` 增 `subagent_id` 入参写入事件 data）
- Modify: `kokoro-agent/src/kokoro_agent/application/run/invoke.py`（子代理 run interrupt 时传 `subagent_id`；当前只对顶层 run 调 awaiting）
- Test: `tests/projection/test_awaiting.py`

**Interfaces — Consumes:** Task 3 的 `ToolStartData.subagent_id`。**Produces:** 子代理待批工具发 `tool_call_awaiting{subagent_id}`。

- [ ] **Step 1: 失败测试** — `awaiting_approval_events(..., subagent_id="sub-9")` 的事件 data 含 `subagent_id == "sub-9"`；顶层（None）不含。
- [ ] **Step 2: 确认失败**
- [ ] **Step 3: 实现** — `awaiting_approval_events(messages, action_requests, interrupt_on_names, *, request_id, subagent_id=None)`；data 末尾 `if subagent_id is not None: data["subagent_id"] = subagent_id`。invoke 侧：递归消费子代理 run 时若其 interrupted，则用其 trigger_call_id 作 subagent_id 调 awaiting。（注：当前 invoke 仅顶层处理 interrupt；子代理 interrupt 是否独立 surfacing 取决于 deepagents 行为——Task 0 probe 顺带确认子代理 interrupt 的 surfacing 路径；若子代理 interrupt 经顶层快照统一暴露，则 subagent_id 从 action_request 的 namespace 推导。）
- [ ] **Step 4: 通过 + 全门**
- [ ] **Step 5: Commit** — `feat(agent): 子代理待批工具 tool_call_awaiting 带 subagent_id`

---

## Task 5: agent — 多工具多决策 resume

**依赖 Task 0 的匹配语义结论。**

**Files:**
- Modify: `kokoro-agent/src/kokoro_agent/interfaces/inbound.py`（4 个 Decision arm 加 `tool_id: str`；`RunResume.decision` → `decisions: list[ResumeDecision]`）
- Modify: `kokoro-agent/src/kokoro_agent/application/run/supervisor.py`（`_on_resume`/`_decision_dict` 组多决策）
- Test: `tests/interfaces/test_inbound.py`、`tests/run/test_supervisor.py`、`tests/run/test_hitl_e2e.py`

**Interfaces — Produces:** `RunResume.decisions: list[ResumeDecision]`，每项带 `tool_id`。

- [ ] **Step 1: 失败测试（test_inbound.py）** — 解析含 `decisions: [{type:approve,tool_id:A},{type:reject,tool_id:B,message:no}]` 的 run.resume 帧成功；旧单 `decision` 帧解析失败（已迁移）。
- [ ] **Step 2: 确认失败**
- [ ] **Step 3: 实现** — 各 arm 加 `tool_id: str`；`RunResume`:
```python
class RunResume(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    kind: Literal["run.resume"]
    run_id: str
    decisions: list[ResumeDecision]
```
`supervisor._on_resume`：按 Task 0 匹配语义，若 by-order 则按 pending 顺序重排 decisions；组 `Command(resume={"decisions": [_decision_dict(d) for d in msg.decisions]})`。`_decision_dict` 仍 `decision.model_dump()`（含 tool_id；若 langchain 不接受多余 tool_id 键则 dump 时 exclude）。
- [ ] **Step 4: 通过 + 全门 + 现有单工具 e2e 改用单元素 decisions 列表保持绿**
- [ ] **Step 5: Commit** — `feat(agent): RunResume 多工具多决策(decisions 列表带 tool_id)`

---

## Task 6: agent — subagent failed 终态

**Files:**
- Modify: `kokoro-agent/src/kokoro_agent/interfaces/envelope.py`（`SubagentFinishedStatus` 加 `failed: NotRequired[bool]` + `error: NotRequired[str]`）
- Modify: `kokoro-agent/src/kokoro_agent/application/projection/transformer.py`（`subagent_finished_event` 增 failed/error）
- Modify: `kokoro-agent/src/kokoro_agent/application/protocols/agent.py`（`SubagentInfo` 暴露失败信息，如 `status`/`error`）
- Modify: `kokoro-agent/src/kokoro_agent/application/run/consumer.py`（`_consume_subagents` 传失败信息）
- Test: `tests/projection/test_transformer.py`

**Interfaces — Produces:** 子代理失败发 `subagent_finished{failed: True, error}`，不再吞成顶层 agent_error。

- [ ] **Step 1: 失败测试** — `_FakeSub(status="failed", error="boom")` → `subagent_finished_event` data `failed is True`、`error == "boom"`；成功子代理不含 failed。
- [ ] **Step 2: 确认失败**
- [ ] **Step 3: 实现** — `subagent_finished_event`：`if sub.status == "failed"` 或 `sub.error` 时写 `data["failed"]=True`、`data["error"]=sub.error`。`SubagentInfo` 加 `error: str | None`（按 deepagents AsyncSubagentRunStream 实测字段，Task 0 probe 顺带确认子代理失败如何 surfacing）。
- [ ] **Step 4: 通过 + 全门**
- [ ] **Step 5: Commit** — `feat(agent): subagent 失败终态 — subagent_finished 发 failed/error`

---

## Task 7: session — normalize 透传新字段

**Files:**
- Modify: `kokoro-session/src/application/normalize.ts`（`tool_call_start`/`tool_call_awaiting`/`tool_call_end` 三 case + subagent_finished case）
- Test: `kokoro-session/tests/...normalize...test.ts`

**Interfaces — Consumes:** Task 1 重生成的 agent-event/session-event Zod（已含可选字段）。**Produces:** AG-UI tool.invoked/awaiting_approval/returned 带 subagent_id/reject_reason；subagent 事件带 failed/error。

- [ ] **Step 1: 失败测试** — 喂带 `subagent_id`/`reject_reason` 的 agent tool 事件，断言 normalize 出的 AG-UI envelope payload 含对应字段；reject_reason/subagent_id 缺省时不出现。
- [ ] **Step 2: 确认失败** → `bun test`
- [ ] **Step 3: 实现** — 三 case 的 `this.envelope("tool.invoked"/"tool.awaiting_approval"/"tool.returned", {...})` 透传 `subagent_id: event.data.subagent_id`、`reject_reason: event.data.rejected ? event.data.reject_reason : undefined`（按 Zod optional 语义，缺省省略）。subagent_finished case 透传 failed/error。
- [ ] **Step 4: 通过 + `bun run typecheck` + `bun test`**
- [ ] **Step 5: Commit** — `feat(session): normalize 透传 subagent_id/reject_reason/failed`

---

## Task 8: web — 权威 rejected + 子代理工具渲染

**Files:**
- Modify: `kokoro-web/src/application/session-stream/types.ts`（`SessionToolCall` 加 `rejectReason?: string`、`subagentId?: string`）
- Modify: `kokoro-web/src/infrastructure/transport-event-mapper.ts`（tool.returned → 透传 rejected/rejectReason/subagentId）
- Modify: `kokoro-web/src/application/session-stream/state-mutations.ts`（删乐观-only reject 依赖，改以后端 `rejected` 为权威；保留乐观仅作即时反馈、后端回流覆盖）
- Modify: `kokoro-web/src/application/session-stream/reducer.ts`（tool.returned 事件按 `rejected` 置 `status:"rejected"` + `rejectReason`；subagentId 归属）
- Test: `kokoro-web/tests/application/session-stream/reducer.test.ts`

**Interfaces — Consumes:** Task 1 重生成的 transport schema（含 rejected/reject_reason/subagent_id）。

- [ ] **Step 1: 失败测试（replay 安全，reducer.test.ts）**

```ts
it("rejected tool 终态权威，replay 安全（不退化为 done）", () => {
  const events = [/* run.started, tool.awaiting_approval{tool_id:T}, tool.returned{tool_id:T,is_error:false,rejected:true,reject_reason:"no"} */]
  const state = events.reduce(applySessionEvent, createSessionStreamState())
  const tool = /* locate tool T */
  expect(tool.status).toBe("rejected")
  expect(tool.rejectReason).toBe("no")
})
```

- [ ] **Step 2: 确认失败** → `pnpm test`（当前 rejected 回流走 is_error=false → 被当 done）
- [ ] **Step 3: 实现** — mapper 透传 `rejected`/`reject_reason`/`subagent_id`；reducer 的 tool.returned 处理：`status = data.rejected ? "rejected" : data.is_error ? "error" : "done"`，写 `rejectReason`、`subagentId`；`state-mutations.ts` 删"乐观置 rejected 因后端不发"的注释与依赖，乐观保留但以回流为准。
- [ ] **Step 4: 通过 + `pnpm run typecheck` + `pnpm test`**
- [ ] **Step 5: Commit** — `feat(web): 权威 rejected(replay 安全) + 子代理工具归属渲染`

---

## Task 9: 跨仓集成 + 合并

- [ ] **Step 1: 四仓全门禁绿（逐仓）**

```bash
cd kokoro-agent && uv run --no-sync mypy src/kokoro_agent && uv run --no-sync pyright && uv run --no-sync pytest -q && uv run --no-sync ruff check
cd ../kokoro-session && bun run typecheck && bun test
cd ../kokoro-web && pnpm run typecheck && pnpm test
cd .. && python3 contract/generate.py --check && python3 contract/verify.py
```

- [ ] **Step 2: 残留扫描** — `rg 'rejected.*False.*后续接入'` agent 清零；`rg '乐观.*rejected.*绿勾'` web 注释已更新。

- [ ] **Step 3: 开 coupled PR（四仓 feat/tool-call-status）+ 合并顺序**

web/session/agent 先合（含重生成产物），parent contract 后合（其 contract CI 检出 sibling main，需 sibling 先落地；参 stacked-squash playbook：重跑 parent CI 后再合）。merge-commit 保留 submodule gitlink。

---

## Self-Review（spec 覆盖核对）

- spec §felt#1 pending → Task 4（awaiting 带归属）+ web 既有 status="awaiting"（无需改）。✅
- spec §felt#2 rejected replay 不安全 → Task 0(机制) + Task 2(agent 权威) + Task 8(web replay 测试)。✅
- spec §felt#3 subagent 审批归属 → Task 3(工具带 id) + Task 4(awaiting 带 id) + Task 8(渲染)。✅
- spec §8 多工具多决策 → Task 5。✅
- spec §7 subagent failed → Task 6。✅
- spec §6 四仓改动面 → Task 1(contract)/2-6(agent)/7(session)/8(web)。✅
- spec §5 SPIKE 前置 → Task 0。✅
- 类型一致性：`subagent_id`(snake)/`subagentId`(camel)、`reject_reason`/`rejectReason`、`failed`/`error` 全任务命名统一（Global Constraints 锁定）。✅
- **已知非完整代码处**（依赖 Task 0 实测 + 未读全的生成文件）：Task 2 reject 标记字段名、Task 4 子代理 interrupt surfacing 路径、Task 5 匹配语义、Task 6 子代理失败字段——均收口到 Task 0 probe 先定，再回填具体字段名；这是 spike-gated 计划的固有顺序，非占位符遗漏。
