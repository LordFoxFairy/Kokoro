# Zero-Debt Closeout Implementation Plan（一口气清零）

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 清零 agent 自身完善余项 C（长期记忆 store）+ 全部已知妥协（clip 静默截断、pyright 豁免无政策、thinking/subagent 真栈盲区、悬而未决的设计决策），此后不再有"已知缺陷"清单。

**Architecture:** 记忆 = langgraph BaseStore 官方三后端（InMemory/AsyncSqliteStore/MongoDBStore）经 `create_deep_agent(store=)` 挂图，自研 `save_memory`/`search_memory` 工具经 `get_runtime(RunContext)` 读 namespace 做前缀隔离。截断经 contract `"truncated?"` 可选字段显性化。豁免经 allowlist 测试变成可执行政策。盲区经真实模型（glm，本地 .env 凭据）端到端压实。

**Tech Stack:** langgraph-store-mongodb 0.3.0（官方，已装）、langgraph.store.sqlite（langgraph-checkpoint-sqlite 3.1.0 自带）、deepagents 0.6.6、contract generate.py（per-kind `"field?"` 机制已存在）。

## Global Constraints

- 禁 Workflow 工具、禁 teams 模式；最多普通 subagent，主线串行（用户明令）。
- web 仓冻结：只允许 contract 生成镜像的机械更新，零产品代码。
- 禁 `type: ignore`/`cast`/函数内 deferred import/`if TYPE_CHECKING`（项目铁律）；第三方边界文件级豁免必须进 allowlist 测试。
- wire 法则：可选字段缺席=省略（exclude_none），永不发 null。
- 每 task 门禁：`uv run ruff check . && uv run pyright && uv run pytest`（agent 仓）全绿才 commit；跨栈改动加 `python3 scripts/e2e-v21-gate.py`。
- 提交信息英文、不带 Co-Authored-By 以外的装饰；每 task 独立 commit。

## 已实证事实（计划依据，勿重查）

- `create_deep_agent(store: BaseStore | None = None)` 存在（deepagents 0.6.6）。
- `ToolRuntime` dataclass 字段含 `context` 与 `store`；`langgraph.runtime.get_runtime(RunContext)` 在图内工具可用（tests/test_context_injection.py 先例）。
- `AsyncSqliteStore.from_conn_string(path)` 是 async context manager（镜像 AsyncSqliteSaver 用法）。
- `MongoDBStore(collection)` 接 pymongo **sync** Collection，`abatch` 内部 run_in_executor（镜像 MongoDBSaver 模式）。
- deepagents `memory=` 参数是文件型 AGENTS.md 记忆（与 BaseStore 无关），两者正交，互不影响。
- contract events.yaml 可选字段：全局 `payload_optional` 列表 + per-kind `"name?"` 后缀（先例 `"result?"`）。
- `InMemoryStore.asearch(prefix)` 天然按 namespace 元组前缀隔离（已实证 ns2 查不到 ns1）。
- kokoro-agent/.env 有 glm 真实凭据（OPENAI_BASE_URL + OPENAI_API_KEY），provider=openai。

---

### Task 1: 记忆 store 工厂（storage/memory_store.py）

**Files:**
- Create: `kokoro-agent/src/kokoro_agent/storage/memory_store.py`
- Test: `kokoro-agent/tests/test_memory_store.py`
- Modify: `kokoro-agent/pyproject.toml`（langgraph-store-mongodb 已由 uv add 落锁，确认在 dependencies）

**Interfaces:**
- Consumes: `CheckpointSettings`（storage/checkpoints.py：backend/sqlite_path/mongo_url/mongo_db）— 记忆 store 与 checkpoint 后端对齐，不新增配置面。
- Produces: `make_memory_store(settings: CheckpointSettings) -> AsyncGenerator[BaseStore, None]`（asynccontextmanager，供 worker/main 与 checkpointer 同级进入）。

- [ ] **Step 1: 写失败测试**（sqlite 落盘跨进入可读、memory 易失、mongo 分支构造不报错——mongo 真读写归 Task 5 e2e）

```python
"""memory store 工厂规格：后端与 checkpoint 对齐，sqlite 落盘持久。"""

from pathlib import Path

import pytest

from kokoro_agent.storage.checkpoints import CheckpointSettings
from kokoro_agent.storage.memory_store import make_memory_store


def _settings(backend: str, tmp_path: Path) -> CheckpointSettings:
    return CheckpointSettings(
        backend=backend,  # type: pyright 若报 Literal 请在调用点写字面量
        sqlite_path=str(tmp_path / "memory.sqlite3"),
        mongo_url="mongodb://localhost:27017",
        mongo_db="kokoro_test",
    )


@pytest.mark.asyncio
async def test_memory_backend_is_volatile(tmp_path: Path) -> None:
    async with make_memory_store(_settings("memory", tmp_path)) as store:
        await store.aput(("ns", "memories"), "k", {"content": "v"})
        assert (await store.aget(("ns", "memories"), "k")) is not None
    async with make_memory_store(_settings("memory", tmp_path)) as store:
        assert (await store.aget(("ns", "memories"), "k")) is None


@pytest.mark.asyncio
async def test_sqlite_backend_persists_across_reopen(tmp_path: Path) -> None:
    settings = _settings("sqlite", tmp_path)
    async with make_memory_store(settings) as store:
        await store.aput(("team-a", "memories"), "pref", {"content": "dark mode"})
    async with make_memory_store(settings) as store:
        item = await store.aget(("team-a", "memories"), "pref")
        assert item is not None and item.value == {"content": "dark mode"}


@pytest.mark.asyncio
async def test_sqlite_namespace_prefix_isolation(tmp_path: Path) -> None:
    settings = _settings("sqlite", tmp_path)
    async with make_memory_store(settings) as store:
        await store.aput(("team-a", "memories"), "k", {"content": "secret"})
        assert await store.asearch(("team-b",)) == []
```

注意：`_settings` 的 backend 参数类型直接用 `Literal["sqlite", "mongo", "memory"]` 注解，不留注释里的权宜。

- [ ] **Step 2: 跑测试确认失败**：`uv run pytest tests/test_memory_store.py -x`，预期 `ModuleNotFoundError: kokoro_agent.storage.memory_store`。

- [ ] **Step 3: 最小实现**

```python
"""长期记忆 store 工厂：后端与 checkpoint 对齐（memory/sqlite/mongo），全官方实现。"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from langgraph.store.base import BaseStore
from langgraph.store.memory import InMemoryStore
from langgraph.store.mongodb import MongoDBStore
from langgraph.store.sqlite.aio import AsyncSqliteStore
from pymongo import MongoClient

from kokoro_agent.storage.checkpoints import CheckpointSettings

MEMORY_COLLECTION = "kokoro_agent_memory"


@asynccontextmanager
async def make_memory_store(
    settings: CheckpointSettings,
) -> AsyncGenerator[BaseStore, None]:
    if settings.backend == "memory":
        yield InMemoryStore()
        return
    if settings.backend == "sqlite":
        async with AsyncSqliteStore.from_conn_string(settings.sqlite_path) as store:
            yield store
        return
    # MongoDBStore 接 sync Collection，async 方法内部 run_in_executor（同 MongoDBSaver 模式）。
    client: MongoClient[dict[str, object]] = MongoClient(settings.mongo_url)
    try:
        yield MongoDBStore(client[settings.mongo_db][MEMORY_COLLECTION])
    finally:
        client.close()
```

若 sqlite checkpoint 与 store 共用同一文件路径冲突（建表撞名），store 路径改为 `settings.sqlite_path + ".store"` 并在测试断言该行为——**先实证再定**。

- [ ] **Step 4: 门禁**：`uv run pytest tests/test_memory_store.py -v && uv run pyright src/kokoro_agent/storage/memory_store.py && uv run ruff check .` 全绿。
- [ ] **Step 5: Commit**：`git add -A && git commit -m "Add memory store factory aligned with checkpoint backends"`

### Task 2: 记忆工具 save_memory / search_memory（namespace 前缀隔离）

**Files:**
- Create: `kokoro-agent/src/kokoro_agent/tools/memory.py`
- Modify: `kokoro-agent/src/kokoro_agent/tools/registry.py`（KOKORO_TOOLS 增两名）
- Test: `kokoro-agent/tests/test_memory_tools.py`

**Interfaces:**
- Consumes: `get_runtime(RunContext)`（langgraph.runtime）→ `.context.namespace` 与 `.store`；`RunContext`（run/context.py）。
- Produces: `MEMORY_TOOLS: tuple[BaseTool, ...]`（save_memory, search_memory），worker/main 装配时并入工具序列；store namespace 元组 = `(context.namespace, "memories")`。

- [ ] **Step 1: 写失败测试**——真 deepagents 图 + InMemoryStore + LocalFake 脚本驱动工具调用（模式照抄 tests/test_context_injection.py 的装配骨架）：

```python
"""记忆工具规格：真图内经 RunContext.namespace 前缀读写 store，跨 run 可读、跨 namespace 不可见。"""

# 断言矩阵（每条独立 test）：
# 1. save_memory 后同 namespace 的 search_memory 命中 content。
# 2. 第二次 invoke（新 run 同 store）search_memory 仍命中——跨 run 持久。
# 3. namespace=team-b 的 RunContext 下 search_memory 查不到 team-a 记忆——隔离。
# 4. search_memory 无命中返回明确"无记忆"文案而非空串。
# 5. save_memory 空 content → 工具报错文案（fail-loud），不落库。
```

测试骨架（完整可运行，LocalFake 脚本先 save 后 search）：

```python
import pytest
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.store.memory import InMemoryStore

from kokoro_agent.execution.build_agent import build_agent
from kokoro_agent.model.local_fake import make_local_fake_chat_model
from kokoro_agent.run.context import RunContext
from kokoro_agent.tools.memory import MEMORY_TOOLS


def _ctx(namespace: str, run_id: str) -> RunContext:
    return RunContext(
        namespace=namespace, session_id="s1", run_id=run_id, thread_id="t1"
    )


def _agent(store: InMemoryStore):  # 返回 InvokableAgent
    script = [
        AIMessage(content="", tool_calls=[{
            "name": "save_memory", "args": {"key": "pref", "content": "user likes dark mode"},
            "id": "m1", "type": "tool_call"}]),
        AIMessage(content="saved"),
    ]
    return build_agent(
        model=make_local_fake_chat_model(script),
        tools=list(MEMORY_TOOLS),
        system_prompt="test",
        subagents=[], checkpointer=None, permissions=[], interrupt_on={},
        context_schema=RunContext, store=store,
    )
```

（search 场景用第二份 script 调 search_memory 并断言 ToolMessage 内容含 "dark mode"。store 参数 build_agent 现在还没有——正是本 task 要加的最小接线，见 Step 3。）

- [ ] **Step 2: 跑测试确认失败**：`uv run pytest tests/test_memory_tools.py -x`，预期 import error（tools/memory.py 不存在）。

- [ ] **Step 3: 实现工具 + build_agent 接 store 参数**

`tools/memory.py`：

```python
"""长期记忆工具：store 前缀 = RunContext.namespace，跨租户结构性不可见。"""

from __future__ import annotations

from langchain_core.tools import BaseTool, tool
from langgraph.runtime import get_runtime

from kokoro_agent.run.context import RunContext

SAVE_MEMORY_TOOL_NAME = "save_memory"
SEARCH_MEMORY_TOOL_NAME = "search_memory"
_MEMORY_SEGMENT = "memories"
_SEARCH_LIMIT = 8


def _store_and_prefix() -> tuple[object, tuple[str, str]]:
    runtime = get_runtime(RunContext)
    if runtime.store is None:
        raise RuntimeError("memory store is not wired into the graph")
    return runtime.store, (runtime.context.namespace, _MEMORY_SEGMENT)


@tool(SAVE_MEMORY_TOOL_NAME)
async def save_memory(key: str, content: str) -> str:
    """Persist a durable memory for this workspace. Use a short kebab-case key."""
    if not content.strip():
        raise ValueError("memory content must be non-empty")
    store, prefix = _store_and_prefix()
    await store.aput(prefix, key, {"content": content})
    return f"memory saved under key {key!r}"


@tool(SEARCH_MEMORY_TOOL_NAME)
async def search_memory(query: str) -> str:
    """Search durable memories saved in earlier runs of this workspace."""
    store, prefix = _store_and_prefix()
    items = await store.asearch(prefix, query=query, limit=_SEARCH_LIMIT)
    if not items:
        return "no memories found"
    return "\n".join(f"- {item.key}: {item.value['content']}" for item in items)


MEMORY_TOOLS: tuple[BaseTool, ...] = (save_memory, search_memory)
```

注意：`_store_and_prefix` 返回类型写真类型 `BaseStore` 而非 object（`from langgraph.store.base import BaseStore`）；`item.value["content"]` 若 pyright 报 unknown，用 `str(item.value.get("content", ""))` 收窄，不用 cast。

`build_agent.py`：签名加 `store: BaseStore | None = None`，两个 create_deep_agent 分支各自透传 `store=store`（import `from langgraph.store.base import BaseStore`）。

`registry.py`：KOKORO_TOOLS 并入 `SAVE_MEMORY_TOOL_NAME`、`SEARCH_MEMORY_TOOL_NAME`（保持现有元组/frozenset 风格）。

- [ ] **Step 4: 跑测试到绿** + `uv run pyright src/kokoro_agent/tools/memory.py src/kokoro_agent/execution/build_agent.py && uv run ruff check . && uv run pytest`（全量，防登记回归——test_assembly/test_registry 可能断言工具清单，按新增两名更新断言）。
- [ ] **Step 5: Commit**：`git commit -am "Add namespace-scoped long-term memory tools over langgraph store"`

### Task 3: worker 装配接线（main.py）+ e2e 回归

**Files:**
- Modify: `kokoro-agent/src/kokoro_agent/worker/main.py`（make_memory_store 与 checkpointer 同级进入；build() 传 store + MEMORY_TOOLS 进工具序列）
- Test: `kokoro-agent/tests/test_assembly.py`（现存装配测试补 store 断言）

**Interfaces:**
- Consumes: Task 1 `make_memory_store(config.checkpoint)`、Task 2 `MEMORY_TOOLS`/build_agent store 参数。
- Produces: 生产 worker 每 run 图带 store；记忆工具默认在授权集内（与 ask_user_question 同级核心工具）。

- [ ] **Step 1:** main.py 的 AsyncExitStack/with 链加 `make_memory_store(config.checkpoint) as memory_store`；build() 内工具序列并入 MEMORY_TOOLS；`build_agent(..., store=memory_store)`。授权集：跟现有核心工具同路径（查 `_authorized`/permissions 构造处，把两个记忆工具名并入默认授权，样式照 ask_user_question 的处理）。
- [ ] **Step 2:** test_assembly.py 加断言：装配产物调用 build_agent 时收到非 None store、工具名单含 save_memory/search_memory（照现有 test_assembly 的桩/捕获模式写）。
- [ ] **Step 3:** 门禁全量：`uv run ruff check . && uv run pyright && uv run pytest`。
- [ ] **Step 4:** 跨栈回归：仓根 `python3 scripts/e2e-v21-gate.py` → 期望 "E2E PASS"。
- [ ] **Step 5: Commit + push**：`git commit -am "Wire memory store through worker assembly" && git push`。

### Task 4: clip 原则化——contract `truncated?` 显性字段

**Files:**
- Modify: `contract/spec/events.yaml`（tool.returned payload 加 `"truncated?"`；notes 加语义行）
- Modify: `contract/generate.py` 仅当 `"field?"` 机制需要 bool 类型映射时（先看 `"result?"` 如何声明类型；同机制则零改动）
- Regenerate: 14 处生成镜像（`python3 contract/generate.py`），三仓 + 父仓
- Modify: `kokoro-agent/src/kokoro_agent/execution/events.py`（clip_result 返回 `(str, bool)` 或新增 `clipped()` 判定；tool.returned 组装处 truncated=True 仅在截断时携带）
- Test: `contract/tests/test_generate.py` golden 更新；agent 仓 events 测试补两条（不截断→字段缺席；截断→truncated=True 且 exclude_none 下上 wire）

**Interfaces:**
- Produces: wire 语义——`tool.returned.truncated` 缺席=结果完整，true=wire 层截断（完整结果在后端，canvas P1 经 artifact_ref 读取）。web 反序列化天然兼容（optional），零 web 产品代码。

- [ ] **Step 1:** 看 events.yaml 中 `"result?"` 与 payload 类型声明的既有机制，同样式加 `"truncated?"`；notes: `tool.returned.truncated: "wire 层展示截断标记；缺席=完整。完整结果在后端，canvas 预览（P1）经 artifact_ref 取。"`。检查 http.yaml 是否有需要同步的副本（先例教训：http.yaml 有自己的 enums 副本）。
- [ ] **Step 2:** `python3 contract/generate.py && python3 contract/check.py` → 镜像同步；`python3 -m pytest contract/tests/ -x` golden 按新产物更新（golden 是字节断言，重新生成后核对 diff 语义仅多一字段）。
- [ ] **Step 3:** agent events.py：

```python
def clip_result(text: str) -> tuple[str, bool]:
    if len(text) <= TOOL_RESULT_MAX_CHARS:
        return text, False
    omitted = len(text) - TOOL_RESULT_MAX_CHARS
    return f"{text[:TOOL_RESULT_MAX_CHARS]}…[truncated {omitted} chars]", True
```

调用点（events.py 两处 + supervisor 直发 tool.returned 处，grep `clip_result` 全量替换调用形态）把 bool 写进 payload：`truncated=True if clipped else None`（exclude_none 缺席语义）。

- [ ] **Step 4:** 测试：agent 仓 tool.returned 测试补「不截断字段缺席 / 截断 truncated=True」两条；session zod 镜像重新生成后 `npm test` 回归；web `npm run build` 或现有 CI 门禁本地命令回归。
- [ ] **Step 5:** 门禁：agent 三件套 + session `npm test` + `python3 scripts/e2e-v21-gate.py`。
- [ ] **Step 6: Commit + push**（contract 在父仓、镜像在各仓——四仓分别 commit，信息统一 `Make wire truncation explicit via tool.returned.truncated`）。

### Task 5: pyright 豁免清剿 + allowlist 政策化

**Files:**
- Modify（尝试消除）: `kokoro-agent/src/kokoro_agent/execution/build_agent.py`、`tests/test_context_injection.py`、`tests/e2e/test_mcp_live.py`
- Create: `kokoro-agent/tests/test_boundary_pragmas.py`

**Interfaces:**
- Produces: 仓内 pragma 集合 = allowlist 常量，任何新增/漂移即测试红。

- [ ] **Step 1（逐文件实证消除）:** 对三个文件依次删掉 pragma 行 → `uv run pyright <file>` 看确切报错 → 尝试结构性修复（如 `probe: BaseTool` 显式注解收 @tool 返回、FastMCP 调用点变量注解）。修得掉的修掉；修不掉的（上游未导出 StateLike、create_deep_agent 未解 ResponseT 泛型）保留并确保 WHY 注释含上游坐标。
- [ ] **Step 2（政策化）:** 写 allowlist 测试：

```python
"""第三方边界豁免政策：pragma 全量清单锁死，新增必过评审（改本测试）。"""

import re
from pathlib import Path

ALLOWED: dict[str, frozenset[str]] = {
    # 实证后按 Step 1 幸存者填写；每项必须能指认上游缺口。
    "src/kokoro_agent/execution/build_agent.py": frozenset(
        {"reportUnknownVariableType", "reportPrivateImportUsage"}
    ),
}

_PRAGMA = re.compile(r"^#\s*pyright:\s*(.+)$", re.MULTILINE)


def test_pragma_inventory_matches_allowlist() -> None:
    root = Path(__file__).resolve().parents[1]
    found: dict[str, frozenset[str]] = {}
    for path in root.glob("**/*.py"):
        if ".venv" in path.parts:
            continue
        match = _PRAGMA.search(path.read_text(encoding="utf-8"))
        if match:
            rules = frozenset(
                part.split("=")[0].strip() for part in match.group(1).split(",")
            )
            found[str(path.relative_to(root))] = rules
    assert found == ALLOWED
```

- [ ] **Step 3:** 门禁三件套；Commit：`git commit -am "Eliminate or police pyright boundary pragmas via allowlist test"`；push。

### Task 6: 真实模型盲区压实（thinking 通道 + subagent 事件）

**Files:**
- Create: `scripts/real-model-verify.py`（仓根 scripts/，骨架照抄 e2e-v21-gate.py 的进程编排：docker redis/mongo + session + agent，但 agent 环境用 kokoro-agent/.env 的真实凭据、去掉 KOKORO_LOCAL_FAKE_MODEL）
- 不改产品代码，除非实证发现 thinking 事件链路真 bug——那走 systematic-debugging 修根因。

**Interfaces:**
- Consumes: kokoro-agent/.env（OPENAI_BASE_URL/OPENAI_API_KEY，glm）；session model_policy 允许该模型（namespace profile 文件按 gate 现例生成）。
- Produces: 两项此前盲区的实证判定，写进 handbook 注记与 claude-progress.md。

- [ ] **Step 1:** 脚本场景 A（subagent）：prompt 明令 "delegate to the <声明集内子代理名> subagent via the task tool to answer X"，SSE 收流断言出现 `subagent.started` 与 `subagent.finished`（及至少一条 subagent.text.*），run.completed 收尾。
- [ ] **Step 2:** 脚本场景 B（thinking）：glm 走 openai 兼容层，先实证 langchain 是否透出 reasoning（收流看 thinking.delta）。若无：查 GLM API thinking 开关（`extra_body={"thinking": {"type": "enabled"}}`）能否经 model factory 的现有配置面传入；能则最小接入（ModelConfig 已有的扩展点，无则加一个 pydantic 字段，走 contract 无关的 agent 内部配置），再验。仍不可达则记录"glm openai 兼容层不透 reasoning"的实证证据（原始 chunk 样本）进 handbook 注记——这是上游事实不是我们的债。
- [ ] **Step 3:** 两场景 PASS/实证结论打印成清单；脚本退出码非 0 即失败。产物贴进最终报告。
- [ ] **Step 4:** Commit：`git commit -am "Add real-model verification for thinking channel and subagent events"`；push。

### Task 7: 设计决策入册 + 收尾

**Files:**
- Modify: `docs/kokoro-handbook/technical/11-agent-session-web-v1-runtime.md`（或其实现注记区）：① result_review 终局法则——run 终止时未裁决审核 = void-by-design，无事后补审；② wire 截断法则——truncated 字段语义 + canvas P1 读后端；③ 记忆 store 三后端与 namespace 前缀隔离。
- Modify: `docs/kokoro-handbook/modules/kokoro-agent.md`（memory 归属注记：store 三后端 + save/search 工具）。
- Modify: `docs/kokoro-handbook/technical/`（合适文档）：namespace profile JSON 文件 = V1 配置真源，多租户升级路径（配置服务/DB）一段注记。
- Modify: `claude-progress.md`、`docs/superpowers/specs/2026-07-03-agent-self-completion-design.md`（C 置 ✅）。
- 各仓 `git status` 清场、全量 push、CI 绿确认（`gh run list` 三仓 + 父仓）。

- [ ] **Step 1:** handbook 四条注记落盘（每条 ≤5 行，语气=法律不是缺陷）。
- [ ] **Step 2:** progress/spec 状态更新；四仓 push；`gh run watch` 或 list 确认 CI 绿。
- [ ] **Step 3:** 收尾报告四件套：做了什么/关键改动/跑了什么验证/还有什么没验（预期"没验"仅剩外部资源挂账：e2b 池、Langfuse、canvas 产品面——它们是待外部条件，不是缺陷）。

## 明确不在本计划（等外部条件，非债务）

- e2b sandbox 池 `(namespace, session_id)` 键入——等部署环境。
- Langfuse HITL trace 连续性——等凭据。
- canvas 预览产品面 + artifact_ref 生产者——P1 产品工作，web 冻结中。
- music/platform job 链路——用户明令后置。
