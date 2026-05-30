# Agent DeepAgents Engine + Planning Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 kokoro-agent 的核心引擎换成 **DeepAgents**(pin 0.6.7,放 Brain 接口后),`run_agent` 改为 `astream_events`→**通用**原始事件族映射器(write_todos 当普通工具,tool.invoked 带 args),并端到端点亮**规划(todo)**:agent 通用产出 → **session(harness)识别 write_todos** → web 渲染 CC/Gemini 式 Plan 卡片。

**Architecture:** agent 用 `create_deep_agent(model=…)`(仅启 todo 规划)→ `run_agent` 单趟消费 `astream_events`,把 `on_chat_model_stream`/`on_tool_start/end`(所有工具一视同仁,带 args)/异常 映射成 `run.started/thinking.delta/text.delta/text.completed/tool.invoked/tool.returned/run.completed/run.failed`(**agent 不认识 plan**)。**session(harness)识别 `tool_name==write_todos`** → 内部 `plan.updated{plan_id,todos}` SessionEvent(吞掉其工具卡)→ A2uiProjector 投影成 A2UI `Plan` 组件(原地更新);web 纯渲染,catalog 加 `Plan`。对标 Claude Code:TodoWrite/Task 是工具、harness 识别并特殊渲染。

**Tech Stack:** Python 3.11 / uv / `deepagents==0.6.7` / langchain / pytest（agent）；TS / Bun / Zod / `bun test`（session）；Next.js / React 19 / `@a2ui/react` / vitest（web）；Playwright（离线截图）。离线无 key：照搬 DeepAgents 的 `bind_tools`-override fake model。

**Contracts:** `agent-events.md` v0.3.0（`tool.invoked` 加可选 `args`）；`session-stream.md` catalog 加 `Plan` + write_todos→Plan 识别约定。Spec：`docs/superpowers/specs/2026-05-31-agent-deepagents-planning-design.md`。

**Conventions:** strict（Pydantic/Zod）、TDD red→green、surgical changes、no bare print（用 logging）、`asyncio.timeout`、频繁 commit、每仓收尾 LSP+linter+test 全绿、无 `any`/`Unknown` 泄漏。

**已锁定事实（代码探查）：**
- `kokoro-agent/src/kokoro_agent/events.py`：`AgentKind` 是 `Literal[...]`（现有 8 个 kind）；`AgentEvent`（`kind/run_id/seq/payload`，strict、extra forbid）；`RunRequest`（含 `execution_style`，默认 "fast"）。
- `run_agent.py`：现为手写循环 `run_agent(req, model)`，用 `model.ainvoke` 读 `.tool_calls`。本片整体替换其实现。
- `infrastructure/model.py`：`make_chat_model()` 读 `KOKORO_MODEL`，scripted 返回 `GenericFakeChatModel`，真分支 `init_chat_model(spec).bind_tools(TOOL_OBJECTS)`。本片改为 `make_agent()` 返回 deep agent 图。
- `worker.py`：`_serve` 里 `make_chat_model()` 建一次，`run_agent(request, model)`。改为 `make_agent()`。
- `tools.py`：`echo_search`/`clock` + `TOOL_OBJECTS`（StructuredTool）。保留（传给 `create_deep_agent(tools=...)`）；`run_tool` 不再被 run_agent 调用（DeepAgents 内部执行工具）。
- `deepagents` 已在 pyproject 依赖（未 pin）。测试用 pytest + `GenericFakeChatModel` 子类范式（见 `tests/test_run_agent.py`）。
- session/web 的 A2UI 管线见上轮 spec；catalog `kokoro/chat/v1` 现有 Thread/Message/ThinkingBlock/ToolCard。

---

## Chunk A — kokoro-agent：DeepAgents 引擎 + 核心循环 + plan 事件

Dir `kokoro-agent/`。`git checkout feat/tools-and-thinking && git checkout -b feat/agent-deepagents-planning`。测试：`uv run pytest`。LSP：`uv run ruff check . && uv run pyright`。

### Task A1: SPIKE — 锁死 DeepAgents 构造 + scripted fake + astream_events 事件形状

> **这是探针任务，不是 TDD。** DeepAgents 0.6.7 的构造裁剪、scripted fake、astream_events 事件 dict 形状均不确定，必须先实跑观测、把结论写成注释，后续 Task 据此实现。

**Files:**
- Create（临时探针，A5 删除）: `scripts/probe_deepagents.py`
- Create（保留）: `tests/_fake_chat_model.py`（照搬 DeepAgents 官方测试的 fake，供离线测试复用）

- [ ] **Step 1: pin 依赖** —— 编辑 `pyproject.toml`，把 `"deepagents"` 改为 `"deepagents==0.6.7"`，`uv sync`。
- [ ] **Step 2: 取官方 fake** —— 阅读已安装包的测试源：找 `deepagents` 仓的 `tests/unit_tests/chat_model.py`（或在 `.venv`/site-packages 里 `find . -name chat_model.py -path "*deepagents*"`；查不到则到 GitHub `langchain-ai/deepagents` 取）。把那个**覆写 `bind_tools` 返回 self、支持 scripted `AIMessage`（含 `tool_calls`）与 `stream_delimiter` 分块流**的 `GenericFakeChatModel` 子类抄到 `tests/_fake_chat_model.py`（保留许可/出处注释）。这是离线测试的基石。
- [ ] **Step 3: 写探针** `scripts/probe_deepagents.py` —— 构造一个 deep agent（仅 todo 规划，不要 FS/execute/subagent），用 fake model scripted 出「write_todos → echo_search → write_todos(改状态) → text」，`astream_events(version="v2")` 跑一遍并 `print(event["event"], event.get("name"), list(event.get("data",{}).keys()))`：

```python
import asyncio
from deepagents import create_deep_agent
from kokoro_agent.tools import TOOL_OBJECTS
from tests._fake_chat_model import FakeChatModel  # 按 Step2 实际类名
# scripted 出 write_todos / echo_search / write_todos / 最终 text，参照 deepagents test_graph.py
...
async def main():
    agent = create_deep_agent(model=fake, tools=TOOL_OBJECTS, system_prompt="probe")  # 裁剪开关见下
    async for e in agent.astream_events({"messages":[("user","plan and search")]}, version="v2"):
        print(e["event"], e.get("name"), list(e.get("data",{}).keys()))
asyncio.run(main())
```
Run: `uv run python scripts/probe_deepagents.py`

- [ ] **Step 4: 记录锁定结论** —— 把以下观测写成 `run_agent.py` 顶部的注释块（后续 Task 依赖）：
  1. `create_deep_agent` 的**仅-todo 裁剪开关**到底是什么（`middleware=[...]` 显式集 / `builtin_tools=` / 不传 subagents + 不注册 FS 工具）。若库强制注入 FS/execute/task 无法干净裁剪，记下来 + 决定"容忍存在但不映射其事件、system_prompt 抑制"。
  2. `write_todos` 的 `on_tool_start` 事件里 **todos 在哪个键**（`event["data"]["input"]["todos"]`？每项结构 `{content,status}`？）。
  3. `on_chat_model_stream` 的 chunk：`event["data"]["chunk"].content` 是 str 还是 block list？thinking/reasoning chunk 怎么区分（content block `{"type":"thinking"}`？还是 `additional_kwargs`/`reasoning`）？
  4. `on_chat_model_end` 是否给完整消息（`event["data"]["output"]`），用于 text.completed。
  5. 顶层 run 边界：是否需要靠 `event["event"]=="on_chain_start"`+`name` 判定，还是直接"流前 yield run.started / 流后 yield run.completed"即可（推荐后者）。
  6. 非 write_todos 工具（echo_search）的 `on_tool_start`/`on_tool_end` 的 name 与 `data.input`/`data.output` 形状。
- [ ] **Step 5: commit**（探针 + fake）

```bash
git add pyproject.toml uv.lock tests/_fake_chat_model.py scripts/probe_deepagents.py
git commit -m "spike(agent): lock DeepAgents construction + fake model + astream_events shapes"
```

### Task A2: events.py — tool.invoked 携带 args（无新 kind）

> **设计修订(B-精炼版):** agent **不**新增 `plan.updated` kind——它完全通用,不认识 plan。`write_todos` 跟其它工具一样走 `tool.invoked/returned`,唯一增强是 `tool.invoked` payload 带 `args`。`AgentEvent.payload` 是 `dict[str, object]`,已能容纳 `args`,**`AgentKind` Literal 不改**。本任务只加一个守护测试确认 tool.invoked 带 args 合法。

**Files:**
- Test: `tests/test_events.py`（追加，无源码改动）

- [ ] **Step 1: 写测试** —— 在 `tests/test_events.py` 追加：

```python
from kokoro_agent.events import AgentEvent


def test_tool_invoked_carries_args():
    ev = AgentEvent(
        kind="tool.invoked",
        run_id="run_1",
        seq=3,
        payload={
            "tool_call_ref": "call_1",
            "tool_name": "write_todos",
            "args": {"todos": [{"content": "step 1", "status": "pending"}]},
        },
    )
    assert ev.payload["args"]["todos"][0]["status"] == "pending"
```

- [ ] **Step 2: 跑测试确认通过**（payload 是 dict，本就合法；这是回归守护）

Run: `uv run pytest tests/test_events.py -q`
Expected: PASS

- [ ] **Step 3: commit**

```bash
git add tests/test_events.py
git commit -m "test(agent): tool.invoked carries generic args payload"
```

### Task A3: `make_agent` —— DeepAgents 引擎构造（含 scripted）

**Files:**
- Modify: `src/kokoro_agent/infrastructure/model.py`（`make_chat_model` → `make_agent`）
- Test: `tests/test_model.py`（改为断言 deep agent 图）

- [ ] **Step 1: 写失败测试** —— 重写 `tests/test_model.py`：

```python
from __future__ import annotations

import os

from kokoro_agent.infrastructure.model import make_agent


def test_scripted_builds_a_runnable_agent(monkeypatch):
    monkeypatch.setenv("KOKORO_MODEL", "scripted")
    agent = make_agent()
    # deep agent 是 langgraph CompiledStateGraph：可 astream_events。
    assert hasattr(agent, "astream_events")


def test_real_spec_builds_without_network(monkeypatch):
    # 仅构造（不调用），不应触网；缺 key 也不应在构造期抛。
    monkeypatch.setenv("KOKORO_MODEL", "anthropic:claude-sonnet-4-6")
    agent = make_agent()
    assert hasattr(agent, "astream_events")
```

- [ ] **Step 2: 跑测试确认失败**

Run: `uv run pytest tests/test_model.py -q`
Expected: FAIL（`make_agent` 不存在）

- [ ] **Step 3: 实现** —— `src/kokoro_agent/infrastructure/model.py`。用 A1 锁定的裁剪开关与 scripted fake：

```python
from __future__ import annotations

import os

from langchain.chat_models import init_chat_model
from langgraph.graph.state import CompiledStateGraph
from deepagents import create_deep_agent

from kokoro_agent.tools import TOOL_OBJECTS

DEFAULT_MODEL = "anthropic:claude-sonnet-4-6"

KOKORO_AGENT_PROMPT = (
    "You are Kokoro's creation orchestrator. Plan multi-step creative tasks with "
    "the todo tool, then execute. Do not use filesystem, code execution, or "
    "sub-agents in this build."
)


def _scripted_model():
    """Offline fake that drives the deep agent through todo->tool->text, no key.

    Uses the bind_tools-override fake copied in tests/_fake_chat_model.py.
    """
    from tests._fake_chat_model import scripted_planning_model  # A1 提供
    return scripted_planning_model()


def make_agent() -> CompiledStateGraph:
    """Build the DeepAgents engine selected by ``KOKORO_MODEL``.

    Only the todo-planning capability is enabled this slice (no FS / execute /
    sub-agents). ``KOKORO_MODEL=scripted`` uses an offline fake (no network/key).
    """
    spec = os.environ.get("KOKORO_MODEL", DEFAULT_MODEL)
    model = _scripted_model() if spec == "scripted" else init_chat_model(spec)
    # 裁剪：按 A1 锁定的开关只启 todo 规划。占位参数名以 A1 结论为准。
    return create_deep_agent(
        model=model,
        tools=TOOL_OBJECTS,
        system_prompt=KOKORO_AGENT_PROMPT,
    )
```
> A1 若发现 `scripted_planning_model` 应放生产路径（被 model.py import）而非 tests/，把它移到 `src/kokoro_agent/infrastructure/_scripted.py` 并相应改 import（避免生产代码 import tests）。**实现时择一并保持 pyright 干净。**

- [ ] **Step 4: 跑测试确认通过**

Run: `uv run pytest tests/test_model.py -q`
Expected: PASS

- [ ] **Step 5: commit**

```bash
git add src/kokoro_agent/infrastructure/ tests/test_model.py
git commit -m "feat(agent): make_agent builds DeepAgents engine (todo-only, scripted offline)"
```

### Task A4: run_agent 改为 astream_events 映射器

**Files:**
- Modify: `src/kokoro_agent/run_agent.py`（整体替换循环实现）
- Modify: `src/kokoro_agent/worker.py`（`make_chat_model`→`make_agent`，类型）
- Test: `tests/test_run_agent.py`（改为驱动 deep agent + 断言通用事件族：write_todos 走 tool.invoked 带 args、无 plan.updated）

- [ ] **Step 1: 写失败测试** —— 重写 `tests/test_run_agent.py` 核心用例（用 A1 的 scripted fake 构造一个真 deep agent，跑 `run_agent` 收集事件）：

```python
from __future__ import annotations

import pytest

from kokoro_agent.events import RunRequest
from kokoro_agent.infrastructure.model import make_agent
from kokoro_agent.run_agent import run_agent


def _req(text: str = "plan and search", style: str = "thinking") -> RunRequest:
    return RunRequest(
        kind="run.request", run_id="run_1", session_id="s",
        conversation_id="c", input=text, execution_style=style,
    )


async def _collect(req: RunRequest) -> list:
    agent = make_agent()  # KOKORO_MODEL=scripted via fixture/env
    return [e async for e in run_agent(req, agent)]


@pytest.mark.asyncio
async def test_scripted_run_emits_generic_tool_text_family(monkeypatch):
    monkeypatch.setenv("KOKORO_MODEL", "scripted")
    events = await _collect(_req())
    kinds = [e.kind for e in events]
    assert kinds[0] == "run.started"
    assert kinds[-1] == "run.completed"
    # agent 完全通用：不产 plan.updated（识别在 session）。
    assert "plan.updated" not in kinds
    assert "tool.invoked" in kinds and "tool.returned" in kinds
    assert "text.completed" in kinds
    # write_todos 当普通工具流出，且 tool.invoked 带 args（todos 在 args 里）。
    invoked = [e for e in events if e.kind == "tool.invoked"]
    tool_names = [e.payload.get("tool_name") for e in invoked]
    assert "write_todos" in tool_names and "echo_search" in tool_names
    wt = next(e for e in invoked if e.payload.get("tool_name") == "write_todos")
    assert isinstance(wt.payload["args"]["todos"], list)
    assert wt.payload["args"]["todos"][0]["status"] in {"pending", "in_progress", "completed"}
    # seq 单调
    seqs = [e.seq for e in events]
    assert seqs == sorted(seqs)


@pytest.mark.asyncio
async def test_fast_style_suppresses_thinking(monkeypatch):
    monkeypatch.setenv("KOKORO_MODEL", "scripted")
    events = await _collect(_req(style="fast"))
    assert all(e.kind != "thinking.delta" for e in events)
```

- [ ] **Step 2: 跑测试确认失败**

Run: `uv run pytest tests/test_run_agent.py -q`
Expected: FAIL（run_agent 仍是旧手写循环，签名/行为不符）

- [ ] **Step 3: 实现** —— 整体替换 `src/kokoro_agent/run_agent.py`（用 A1 锁定的事件键名；下方为基于 langchain astream_events v2 约定的起点，按 spike 调整 chunk/thinking 提取与 todos 键）：

```python
from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import cast

from langgraph.graph.state import CompiledStateGraph

from kokoro_agent.events import AgentEvent, RunRequest

ASTREAM_TIMEOUT_S = 120
RECURSION_LIMIT = 25

# A brain is now a DeepAgents graph; only astream_events is consumed.
Agent = CompiledStateGraph


def _text_and_thinking(chunk: object) -> tuple[str, str]:
    """Split a streamed chat-model chunk's content into (text, thinking).

    Content is either a str (text) or a list of blocks; thinking blocks carry
    {"type": "thinking", "thinking": ...}. Shapes confirmed in the A1 spike.
    """
    content = getattr(chunk, "content", "")
    if isinstance(content, str):
        return content, ""
    text_parts: list[str] = []
    think_parts: list[str] = []
    if isinstance(content, list):
        for block in cast("list[object]", content):
            if not isinstance(block, dict):
                continue
            b = cast("dict[object, object]", block)
            t = b.get("type")
            if t == "text" and isinstance(b.get("text"), str):
                text_parts.append(cast("str", b["text"]))
            elif t == "thinking" and isinstance(b.get("thinking"), str):
                think_parts.append(cast("str", b["thinking"]))
    return "".join(text_parts), "".join(think_parts)


async def run_agent(  # noqa: C901 — cohesive event mapper
    req: RunRequest, agent: Agent
) -> AsyncIterator[AgentEvent]:
    """Stream a DeepAgents run as raw agent events (fully generic).

    Maps ``astream_events`` (v2) to the raw family: model token chunks ->
    text.delta / thinking.delta (thinking only when execution_style=="thinking"),
    ALL tools (incl. write_todos) -> tool.invoked{...,args}/tool.returned (the
    agent does not know about "plan"; session recognizes write_todos), end ->
    run.completed, any error -> run.failed.
    """
    seq = 1
    message_ref = "m1"
    thinking_mode = req.execution_style == "thinking"
    text_buf = ""
    yield AgentEvent(kind="run.started", run_id=req.run_id, seq=seq, payload={})
    try:
        async with asyncio.timeout(ASTREAM_TIMEOUT_S):
            stream = agent.astream_events(
                {"messages": [("user", req.input)]},
                version="v2",
                config={"recursion_limit": RECURSION_LIMIT},
            )
            async for event in stream:
                kind = event["event"]
                name = event.get("name", "")
                data = cast("dict[str, object]", event.get("data", {}))

                if kind == "on_chat_model_stream":
                    text, thinking = _text_and_thinking(data.get("chunk"))
                    if thinking and thinking_mode:
                        seq += 1
                        yield AgentEvent(kind="thinking.delta", run_id=req.run_id, seq=seq, payload={"text": thinking})
                    if text:
                        text_buf += text
                        seq += 1
                        yield AgentEvent(kind="text.delta", run_id=req.run_id, seq=seq, payload={"message_ref": message_ref, "text": text})

                elif kind == "on_tool_start":
                    # 所有工具一视同仁（含 write_todos）；带上入参 args，由 session harness 识别。
                    payload: dict[str, object] = {
                        "tool_call_ref": str(event.get("run_id", "")),
                        "tool_name": name,
                    }
                    tool_input = data.get("input")
                    if isinstance(tool_input, dict):
                        payload["args"] = tool_input
                    seq += 1
                    yield AgentEvent(kind="tool.invoked", run_id=req.run_id, seq=seq, payload=payload)

                elif kind == "on_tool_end":
                    seq += 1
                    yield AgentEvent(kind="tool.returned", run_id=req.run_id, seq=seq, payload={"tool_call_ref": str(event.get("run_id", "")), "tool_name": name, "status": "ok"})

            if text_buf:
                seq += 1
                yield AgentEvent(kind="text.completed", run_id=req.run_id, seq=seq, payload={"message_ref": message_ref, "text": text_buf})
        seq += 1
        yield AgentEvent(kind="run.completed", run_id=req.run_id, seq=seq, payload={"status": "completed"})
    except Exception as error:  # noqa: BLE001 — boundary: any failure -> run.failed
        seq += 1
        yield AgentEvent(kind="run.failed", run_id=req.run_id, seq=seq, payload={"error_kind": type(error).__name__, "message": str(error)})
```
> 关键按 spike 调整:`_text_and_thinking` 的 thinking 提取、`tool.invoked` 的 `args` 来源（`event.data.input` 是否就是工具完整入参）、tool_call_ref 的来源（`event["run_id"]` 是否稳定配对 start/end）。若 start/end 的 run_id 不能配对，改用 name+计数器配对并测试锁定。`text.completed` 这里只在流末发一条（最终消息）；若 spike 显示多消息需按 `on_chat_model_end` 分段，则改为每个非空 end 发一条并轮换 message_ref。agent **不解析 todos 语义**——只把 `data.input` 原样当 args 透传,识别交给 session。

- [ ] **Step 4: 改 worker** —— `src/kokoro_agent/worker.py`：`from kokoro_agent.infrastructure.model import make_agent`；`from kokoro_agent.run_agent import run_agent`（去掉 `BrainModel`）；`_handle_request`/`run_once`/`_serve` 的 `model: BrainModel` 改为 `agent: CompiledStateGraph`（import `from langgraph.graph.state import CompiledStateGraph`）；`_serve` 里 `agent = make_agent()`，`run_agent(request, agent)`。

- [ ] **Step 5: 跑测试确认通过**

Run: `uv run pytest tests/test_run_agent.py tests/test_worker.py -q`
Expected: PASS（worker 测试若 mock 了 run_agent/model 需相应更新）

- [ ] **Step 6: commit**

```bash
git add src/kokoro_agent/run_agent.py src/kokoro_agent/worker.py tests/test_run_agent.py tests/test_worker.py
git commit -m "feat(agent): run_agent maps DeepAgents astream_events to generic raw event family (tool.invoked carries args)"
```

### Task A5: 清理 + 绿门

- [ ] **Step 1:** 删除探针 `scripts/probe_deepagents.py`（`git rm`）。确认 `tools.py` 的 `run_tool` 若已无人调用，保留其单测（`test_tools.py` 仍测它，作为注册表工具的纯函数测试，合法）。
- [ ] **Step 2:** `uv run ruff check . && uv run pyright && uv run pytest -q` 全绿（含 schema 崩塌/幂等/thinking 抑制）。贴输出。
- [ ] **Step 3: commit**

```bash
git add -A && git commit -m "chore(agent): deepagents/planning lint/type/test green; drop probe"
```

---

## Chunk B — 协议 agent-events.md v0.3.0

Dir 父仓 `Kokoro/`（本计划分支 `docs/agent-deepagents-planning`）。

### Task B1: tool.invoked 加可选 `args`

**Files:**
- Modify: `docs/protocol/agent-events.md`

- [ ] **Step 1:** frontmatter `version` → `0.3.0`。把 `tool.invoked` 行的 payload 改为带可选 `args`：

```
| `tool.invoked` | `tool_call_ref`, `tool_name`, `args`(可选) | 工具调用开始；`args`=工具入参原样（DeepAgents 的 event.data.input），供 session harness 识别/取数据 | `tool.started`（write_todos 例外，见 session 归一化） |
```
表下补：`args` 是任意 JSON 对象(工具入参原样);v0.3.0 新增、additive、向后兼容。**agent 不新增 plan/规划相关事件——planning 的 todo 列表通过 `write_todos` 这个普通工具的 `args` 流出,由 session 识别**(对标 Claude Code:TodoWrite/Task 本质都是工具,harness 识别并特殊渲染,模型层不特殊化)。

- [ ] **Step 2: commit**

```bash
git add docs/protocol/agent-events.md
git commit -m "docs(protocol): agent-events v0.3.0 — tool.invoked carries optional args"
```

---

## Chunk C — kokoro-session：归一化 plan + 投影 Plan 组件

Dir `kokoro-session/`。`git checkout feat/chat-shell-a2ui && git checkout -b feat/agent-deepagents-planning`。测试：`bun test`。

### Task C1: inbound zod — tool.invoked 加可选 `args`

> **设计修订(B-精炼版):** 不加 inbound `plan.updated`(agent 无此事件)。改为给现有 `tool.invoked` 变体加**可选 `args`**(任意对象),供 normalize 识别 write_todos 取 todos。

**Files:**
- Modify: `src/domain/agent-events.ts`（tool.invoked 变体加 args）
- Test: `tests/agent-events.test.ts`

- [ ] **Step 1: 写失败测试** `tests/agent-events.test.ts` 追加：

```ts
import { describe, expect, it } from "bun:test"
import { agentEventSchema } from "../src/domain/agent-events"

describe("agentEventSchema tool.invoked args", () => {
  it("accepts tool.invoked with optional args", () => {
    const ev = { kind: "tool.invoked", run_id: "run_1", seq: 4, payload: { tool_call_ref: "c1", tool_name: "write_todos", args: { todos: [{ content: "a", status: "pending" }] } } }
    expect(agentEventSchema.parse(ev)).toEqual(ev)
  })
  it("still accepts tool.invoked without args", () => {
    const ev = { kind: "tool.invoked", run_id: "run_1", seq: 4, payload: { tool_call_ref: "c1", tool_name: "echo_search" } }
    expect(agentEventSchema.parse(ev)).toEqual(ev)
  })
})
```

- [ ] **Step 2: 跑测试确认失败**

Run: `bun test tests/agent-events.test.ts`
Expected: FAIL（带 args 时现有 `.strict()` 变体拒绝多余键）

- [ ] **Step 3: 实现** —— `src/domain/agent-events.ts`：在现有 `tool.invoked` 变体的 payload `.object({...})` 里加一个可选字段（保持 `.strict()`）：

```ts
// 现有 tool.invoked 变体的 payload 内追加：
args: z.record(z.string(), z.unknown()).optional(),
```
（`z.record(z.string(), z.unknown())` = 任意对象;`.optional()` 兼容无 args 的旧事件。其余不动。）

- [ ] **Step 4: 跑测试确认通过**

Run: `bun test tests/agent-events.test.ts`
Expected: PASS

- [ ] **Step 5: commit**

```bash
git add src/domain/agent-events.ts tests/agent-events.test.ts
git commit -m "feat(session): tool.invoked carries optional args"
```

### Task C2: normalize — harness 识别 write_todos → 内部 plan.updated

> **设计修订(B-精炼版):** session 是 harness 层。归一化器在处理 `tool.invoked` 时**识别 `tool_name=="write_todos"`** → 产**内部会话事件** `plan.updated{plan_id, todos}`、**不**产 tool.started;其对应 `tool.returned` 被吞、不产 tool.completed。其它工具照旧。这是唯一的"特殊化",集中在此一处;agent 通用、web 纯渲染。

**Files:**
- Modify: `src/domain/events.ts`（`sessionEventNames` 加 `plan.updated` —— session 内部 AGUI 表示）
- Modify: `src/application/normalize.ts`（tool.invoked/returned 识别 write_todos）
- Test: `tests/normalize.test.ts`

- [ ] **Step 1: 写失败测试** `tests/normalize.test.ts` 追加：

```ts
it("recognizes write_todos tool.invoked as an internal plan.updated (suppressing tool card)", () => {
  const norm = new Normalizer({ sessionId: "s", conversationId: "c", runId: "run_1" }, clock())
  norm.ingest({ kind: "run.started", run_id: "run_1", seq: 1, payload: {} })
  const out = norm.ingest({ kind: "tool.invoked", run_id: "run_1", seq: 2, payload: { tool_call_ref: "wt1", tool_name: "write_todos", args: { todos: [{ content: "a", status: "pending" }] } } })
  const plan = out.find((e) => e.event === "plan.updated")
  expect(plan).toBeDefined()
  expect(plan!.payload.plan_id).toBe("run_1:plan")
  expect((plan!.payload.todos as unknown[]).length).toBe(1)
  // 不产 tool.started
  expect(out.some((e) => e.event === "tool.started")).toBe(false)
  // 其对应 tool.returned 被吞
  const ret = norm.ingest({ kind: "tool.returned", run_id: "run_1", seq: 3, payload: { tool_call_ref: "wt1", tool_name: "write_todos", status: "ok" } })
  expect(ret).toEqual([])
})

it("keeps non-write_todos tools as normal tool.started/completed", () => {
  const norm = new Normalizer({ sessionId: "s", conversationId: "c", runId: "run_1" }, clock())
  norm.ingest({ kind: "run.started", run_id: "run_1", seq: 1, payload: {} })
  const inv = norm.ingest({ kind: "tool.invoked", run_id: "run_1", seq: 2, payload: { tool_call_ref: "es1", tool_name: "echo_search", args: { query: "x" } } })
  expect(inv.some((e) => e.event === "tool.started")).toBe(true)
})
```
（`clock()` 用本文件已有的测试时钟工厂；若没有就内联 `{ newEventId: () => "evt", now: () => new Date("2026-05-31T00:00:00Z") }`。）

- [ ] **Step 2: 跑测试确认失败**

Run: `bun test tests/normalize.test.ts`
Expected: FAIL

- [ ] **Step 3: 实现**
  - `src/domain/events.ts`：`sessionEventNames` 数组加 `"plan.updated"`。
  - `src/application/normalize.ts`：加一个私有字段记录 write_todos 的 ref —— `private readonly writeTodosRefs = new Set<string>()`。把 `tool.invoked` / `tool.returned` 两个 case 改成：

```ts
case "tool.invoked": {
  if (event.payload.tool_name === "write_todos") {
    this.writeTodosRefs.add(event.payload.tool_call_ref)
    const args = (event.payload.args ?? {}) as Record<string, unknown>
    const todos = Array.isArray(args.todos) ? args.todos : []
    return [
      this.envelope("plan.updated", {
        plan_id: `${this.binding.runId}:plan`,
        todos,
      }),
    ]
  }
  const toolCallId = this.toolCallIdFor(event.payload.tool_call_ref)
  return [
    this.envelope("tool.started", {
      tool_call_id: toolCallId,
      tool_name: event.payload.tool_name,
    }),
  ]
}
case "tool.returned": {
  if (this.writeTodosRefs.has(event.payload.tool_call_ref)) {
    return [] // write_todos 已识别为 plan，吞掉其完成事件
  }
  const toolCallId = this.toolCallIds.get(event.payload.tool_call_ref)
  if (!toolCallId) {
    console.warn(`tool.returned with no matching tool.invoked (tool_call_ref=${event.payload.tool_call_ref}); ignoring`)
    return []
  }
  return [
    this.envelope("tool.completed", {
      tool_call_id: toolCallId,
      tool_name: event.payload.tool_name,
      status: event.payload.status,
    }),
  ]
}
```
（按现有 `tool.invoked`/`tool.returned` case 原样替换;`event.payload.args` 来自 C1 的 schema;若 `tool_name` 字段类型不含 args，确保 C1 已加。其余 case 不动。`plan.updated` 仍在 `mapNonThinkingEvent` 内、自动享受 flushThinking 前缀。）

- [ ] **Step 4: 跑测试确认通过**

Run: `bun test tests/normalize.test.ts`
Expected: PASS

- [ ] **Step 5: commit**

```bash
git add src/domain/events.ts src/application/normalize.ts tests/normalize.test.ts
git commit -m "feat(session): harness recognizes write_todos as internal plan.updated"
```

### Task C3: A2uiProjector 投影 Plan 组件

**Files:**
- Modify: `src/application/a2ui-projector.ts`
- Test: `tests/a2ui-projector.test.ts`

> Plan 与 message 类似：首个 `plan.updated` mount `Plan` 组件 + push 进 root.children + setData；后续 `plan.updated` 仅 setData（原地整列替换）。空 todos（`[]`）→ 不 mount，直到首个非空（边界）。

- [ ] **Step 1: 写失败测试** `tests/a2ui-projector.test.ts` 追加：

```ts
it("projects plan.updated into a Plan component mounted once + dataModel replace", () => {
  const p = new A2uiProjector("ses_1")
  p.project(ev("run.created", { run_id: "run_1" }, 1))
  const first = p.project(ev("plan.updated", { plan_id: "run_1:plan", todos: [{ content: "a", status: "pending" }] }, 2))
  expect(first[0]).toEqual({ version: "v0.9", updateComponents: { surfaceId: "ses_1", components: [{ id: "run_1:plan", component: "Plan", todosPath: { path: "/plans/run_1:plan" } }] } })
  expect(first[1]).toEqual({ version: "v0.9", updateDataModel: { surfaceId: "ses_1", path: "/plans/run_1:plan", value: [{ content: "a", status: "pending" }] } })
  expect(first[2]).toEqual({ version: "v0.9", updateComponents: { surfaceId: "ses_1", components: [{ id: "root", component: "Thread", children: ["run_1:plan"] }] } })
  // second plan.updated: dataModel only, no re-mount / no duplicate child
  const second = p.project(ev("plan.updated", { plan_id: "run_1:plan", todos: [{ content: "a", status: "completed" }] }, 3))
  expect(second).toEqual([{ version: "v0.9", updateDataModel: { surfaceId: "ses_1", path: "/plans/run_1:plan", value: [{ content: "a", status: "completed" }] } }])
})

it("plan.updated with empty todos mounts nothing until non-empty", () => {
  const p = new A2uiProjector("ses_1")
  p.project(ev("run.created", { run_id: "run_1" }, 1))
  expect(p.project(ev("plan.updated", { plan_id: "run_1:plan", todos: [] }, 2))).toEqual([])
})
```
（`ev(...)` 复用本文件已有的 `SessionEvent` 构造 helper；其 `event` 名传 `"plan.updated"`。）

- [ ] **Step 2: 跑测试确认失败**

Run: `bun test tests/a2ui-projector.test.ts`
Expected: FAIL

- [ ] **Step 3: 实现** —— `src/application/a2ui-projector.ts`：加字段 `private planMounted = false`；在 `map` 的 switch 加：

```ts
case "plan.updated": {
  const id = String(event.payload.plan_id)
  const path = `/plans/${id}`
  const todos = event.payload.todos
  if (!Array.isArray(todos) || todos.length === 0) {
    if (!this.planMounted) return []        // 空且未挂 → 不产
  }
  if (!this.planMounted) {
    this.planMounted = true
    this.children.push(id)
    return [
      this.mountComponent({ id, component: "Plan", todosPath: { path } }),
      this.setData(path, todos),
      this.rootOp(),
    ]
  }
  return [this.setData(path, todos)]
}
```
（`mountComponent`/`setData`/`rootOp` 复用现有私有方法；注意 `mountComponent` 的签名按现有实现传参。）

- [ ] **Step 4: 跑测试确认通过 + 绿门**

Run: `bunx tsc --noEmit && bunx eslint . && bun test`
Expected: 全绿

- [ ] **Step 5: commit**

```bash
git add src/application/a2ui-projector.ts tests/a2ui-projector.test.ts
git commit -m "feat(session): project plan.updated into A2UI Plan component (in-place update)"
```

### Task C4: 协议 doc — session-stream.md 加 Plan

**Files:**
- Modify: `src/../`（父仓 `docs/protocol/session-stream.md`，在本计划父仓分支上一并改；若分仓提交则在 Chunk B 同分支）

- [ ] **Step 1:** 在 `session-stream.md` v2.0.0 节的 catalog 组件表加 `Plan{todosPath}`（CC/Gemini 式 todo 清单，原地更新）；加**内部会话事件** `plan.updated{plan_id, todos}`；并补一条 **harness 约定**:session 归一化器识别 agent 的 `tool.invoked{tool_name:"write_todos"}` → 取 `args.todos` 产 `plan.updated`、吞掉其工具卡（agent 通用不识别 plan;对标 Claude Code harness 识别 TodoWrite）。
- [ ] **Step 2: commit**（在父仓分支）

```bash
git add docs/protocol/session-stream.md
git commit -m "docs(protocol): session-stream catalog adds Plan component"
```

---

## Chunk D — kokoro-web：Plan catalog 组件

Dir `kokoro-web/`。`git checkout feat/chat-shell-a2ui && git checkout -b feat/agent-deepagents-planning`。测试：`bun run test`。

### Task D1: ~~事件域 + 解析~~ —— 删除(无需)

> **设计修订:** 上轮(chat shell × A2UI)已删除 web 的 AGUI 解析层(`src/infrastructure/protocol/session-event.ts`、`src/domain/shared/session-stream-event.ts` 均不存在)。web **只消费 A2UI op**,通过 catalog 组件渲染——session 投影出的 `Plan` op 直接被 `MessageProcessor` 处理。**本任务删除,web 侧只需 Task D2 的 Plan catalog 组件。** 实现前可 `git grep -l "session-stream-event\|protocol/session-event"` 确认这两文件确实不存在(应为空)。

### Task D2: Plan 组件 + 注册

**Files:**
- Create: `src/interfaces/a2ui/components/plan.tsx`
- Modify: `src/interfaces/a2ui/catalog.ts`
- Modify: `src/app/globals.css`
- Test: `src/interfaces/a2ui/__tests__/plan.test.tsx`

- [ ] **Step 1: 写失败测试** `src/interfaces/a2ui/__tests__/plan.test.tsx`：

```tsx
import { render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"
import { A2uiSurface } from "@a2ui/react/v0_9"
import { MessageProcessor, type A2uiMessage } from "@a2ui/web_core/v0_9"
import { kokoroChatCatalog } from "../catalog"

describe("Plan (kokoro/chat/v1)", () => {
  it("renders a todo checklist with statuses", () => {
    const processor = new MessageProcessor([kokoroChatCatalog])
    processor.processMessages([
      { version: "v0.9", createSurface: { surfaceId: "s", catalogId: "kokoro/chat/v1" } },
      { version: "v0.9", updateComponents: { surfaceId: "s", components: [
        { id: "root", component: "Thread", children: ["p1"] },
        { id: "p1", component: "Plan", todosPath: { path: "/plans/p1" } },
      ] } },
      { version: "v0.9", updateDataModel: { surfaceId: "s", path: "/plans/p1", value: [
        { content: "draft outline", status: "completed" },
        { content: "write copy", status: "in_progress" },
        { content: "review", status: "pending" },
      ] } },
    ] as A2uiMessage[])
    render(<A2uiSurface surface={processor.model.getSurface("s")!} />)
    expect(screen.getByText("draft outline")).toBeInTheDocument()
    expect(screen.getByText("write copy")).toBeInTheDocument()
    const items = screen.getAllByTestId("kk-todo")
    expect(items).toHaveLength(3)
    expect(items[0].dataset.status).toBe("completed")
    expect(items[1].dataset.status).toBe("in_progress")
  })
})
```

- [ ] **Step 2: 跑测试确认失败**

Run: `bun run test src/interfaces/a2ui/__tests__/plan.test.tsx`
Expected: FAIL

- [ ] **Step 3: 写组件** `src/interfaces/a2ui/components/plan.tsx`（按 B 轮锁定的 `createComponentImplementation` `{props, buildChild, context}` 签名；todos 是 DynamicData 数组——若 a2ui 的数组绑定与 DynamicString 不同，按 .d.ts 调整，必要时用 `createBinderlessComponentImplementation` 直读 properties）：

```tsx
import { z } from "zod"
import { createComponentImplementation } from "@a2ui/react/v0_9"

const todoSchema = z.object({
  content: z.string(),
  status: z.enum(["pending", "in_progress", "completed"]),
})
const planSchema = z.object({ todos: z.array(todoSchema).default([]) })

const MARK: Record<string, string> = { pending: "○", in_progress: "◐", completed: "✓" }

// CC/Gemini 式 todo 清单（对标原型 .plan-block）；原地更新。
function PlanRender({ props }: { props: { todos: { content: string; status: string }[] } }) {
  return (
    <div className="kk-plan">
      <p className="kk-plan__title">📋 计划</p>
      <ul className="kk-plan__list">
        {props.todos.map((t, i) => (
          <li key={i} className="kk-todo" data-testid="kk-todo" data-status={t.status}>
            <span className="kk-todo__mark">{MARK[t.status] ?? "○"}</span>
            <span className="kk-todo__text">{t.content}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}

export const planComponent = createComponentImplementation(
  { name: "Plan", schema: planSchema },
  PlanRender,
)
```
> `todosPath:{path}` 绑定到一个**数组**——确认 a2ui 是否把数组 dynamic-data 解析进 `props.todos`。若它要求 `todos` 直接是 data-bound 字段名（而非 `todosPath`），改 session 投影与此处字段名一致（保持两侧字面一致：session 发 `todosPath`/`todos` 与 web schema 字段名必须对齐）。**以一处为准、两侧统一。**

- [ ] **Step 4: 注册 + 样式** —— `catalog.ts` 数组加 `planComponent`；`globals.css` 追加：

```css
.kk-plan { border: 1px solid var(--border-soft); border-radius: var(--radius-soft); background: var(--surface-soft); padding: 0.625rem 0.875rem; }
.kk-plan__title { font-size: 0.8125rem; color: var(--brand-wood); margin-bottom: 0.375rem; }
.kk-plan__list { display: flex; flex-direction: column; gap: 0.25rem; }
.kk-todo { display: flex; align-items: center; gap: 0.5rem; font-size: 0.875rem; color: var(--foreground); }
.kk-todo__mark { width: 1rem; text-align: center; color: var(--brand-wood); }
.kk-todo[data-status="completed"] .kk-todo__text { color: rgba(43,37,32,0.45); text-decoration: line-through; }
.kk-todo[data-status="in_progress"] .kk-todo__mark { color: var(--brand-wood); font-weight: 700; }
```

- [ ] **Step 5: 跑测试确认通过 + 绿门**

Run: `bunx tsc --noEmit && bun run lint && bun run test && bun run build`
Expected: 全绿

- [ ] **Step 6: commit**

```bash
git add src/interfaces/a2ui/ src/app/globals.css
git commit -m "feat(web): Plan component (CC/Gemini todo checklist) for kokoro/chat/v1"
```

---

## Chunk E — 集成离线浏览器验证（控制器执行）

### Task E1: 三进程离线 e2e + 截图

- [ ] **Step 1:** redis `redis-server --daemonize yes`。
- [ ] **Step 2:** 三进程 `KOKORO_STREAM_BACKEND=redis KOKORO_MODEL=scripted`：agent worker（`uv run kokoro-agent-worker`）、session（`bun run start`）、web（`bun run dev` 或 prod `bun run build && bun run start`）。**注意**：scripted fake 单 worker 单次（迭代器耗尽）——每次浏览器触发新 run 前重启 worker。
- [ ] **Step 3:** Playwright：开 web，输入并发送；等待 Plan 卡片出现。
- [ ] **Step 4:** 断言看到 **Plan 卡片**（todo 列表，含 completed ✓ / in_progress ◐ / pending ○，随 run 推进原地更新）+ 工具卡 + 正文。展开思考块。截图。0 console error。
- [ ] **Step 5:** 停进程 + redis；清 `dump.rdb`。

## Done criteria
- 四仓 LSP/linter/test 全绿；离线无 key。
- agent 引擎为 DeepAgents（pin 0.6.7），`run_agent` 走 `astream_events` 映射，真·token 流式 text；`plan.updated` 被点亮且 `write_todos` 不泄漏成 tool。
- `plan.updated` agent→session→web 贯通；web 渲染 CC/Gemini 式 todo 清单（三状态原地更新），浏览器 e2e 截图。
- agent 只产原始 kind；web 只消费 A2UI op；session 拥有归一化+投影。无跨仓 import。

## 自检（writing-plans self-review，含 B-精炼版修订）
- Spec 覆盖：§2 引擎选型→A3；§3 run_agent 通用映射→A4（+A1 spike 锁形状）；§4 协议(tool.invoked 加 args)→B1；§5 session harness 识别→C1(args schema)/C2(识别 write_todos)/C3(plan.updated→Plan)、web 纯渲染→D2(Plan 组件，D1 已删)；§5 doc→C4；§6 离线测试→A1 fake + A4/C2 测试 + E1；§8 边界（空 todos/原地更新/write_todos 识别/args 缺失容错）→C2/C3/A4 测试。子agent/真实工具/权限/Plan 交互明确不做（spec §10）。
- **架构一致(B-精炼版)**：agent **不产** plan 事件(A2/A4 测试断言 `"plan.updated" not in kinds`)；`plan.updated` 仅为 **session 内部 AGUI 表示**(C2 产、C3 消费、events.ts 名)，不进 agent 协议、不进 web；识别 `write_todos` 只在 session normalizer 一处(C2)；web 只加 Plan 组件、不判工具名(D2)。
- 类型一致：字符串字面 `"write_todos"` 跨 agent(发,A4)与 session(识别,C2)一致；`plan.updated` 仅 session 内部(C2/C3/events.ts)；todos 项 `{content,status}` + status enum 三值在 agent args→session→web 各处一致；Plan 组件名与 `todosPath`/`todos` 绑定字段名 session 投影(C3)与 web schema(D2)**必须对齐**（计划已标注"以一处为准两侧统一"）；`plan_id`=`{run_id}:plan` 贯穿 C2/C3。
- 已标注的实现期确认点（spike）：A1 锁 DeepAgents 裁剪开关 + astream_events 事件键 + 工具 args(data.input)形状 + scripted fake；A4 的 tool_call_ref 配对与 text.completed 分段按 spike 调整；D2 的数组绑定字段名按 @a2ui .d.ts 对齐。这些是对不稳定外部库（DeepAgents 0.x / @a2ui 0.x）的必要 spike，非占位。
