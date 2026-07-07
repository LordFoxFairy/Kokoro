# Agent 存储收敛 + 配置 pydantic-settings + local==prod 一致 — 设计

**Goal:** 消灭「拍扁成字符串再反解析」的配置写法与冗余的假件/落盘后端，让 agent（及 session）的存储收敛为「一个轴一个真后端」，配置用 pydantic-settings 优美表达，local 与 prod 走同一套真服务。

**Architecture:** 三个可独立验证的 spec 顺序推进（A′ → B → C），外加一个未来 spec（model 库）。每个 spec 各自 plan、各自测试、各自交付。

**Tech Stack:** Python 3.14 / pydantic v2 / pydantic-settings 2.14 / langgraph checkpoint(mongo) & store(mongo) / redis streams；session TS（transport=redis / store=mongo）。

---

## 0. 指导原则

1. **一个轴一个真后端，local == prod。** 有 docker 起 redis/mongo，就不再维护并行的假件/落盘后端。
2. **无静默 skip。** 真后端恒在 → 存储测试永远真跑；服务缺失 fail-loud，不 skip 灌绿数。
3. **默认值 = 字段默认。** 配置默认值就地声明在 pydantic 字段上，类型/约束/别名一处可读，删除手写 `_int/_float/_stringify` 与映射表。
4. **env 名是对外契约，零改名。** 现有 `KOKORO_*` 与 SDK 原生名（`OPENAI_*`/`ANTHROPIC_*`/`LANGFUSE_*`）全部保留。
5. **wire 保持 provider 无关的意图。** 模型 provider-SDK 机制翻译留在 agent，选择/解析留在 session。

---

## 1. 关键澄清：「memory」是两个不同的东西

- **memory = 内存假件后端**（本次要删）：`MemoryStream`、`InMemorySaver`、`InMemoryStore`、session `MemoryTransport`/`MemoryStore`。非持久、进程内，仅为快测/零基建存在。
- **memory = 长期记忆功能**（**保留**）：`memory_store`（`make_memory_store`）是 agent 跨会话记忆能力，按租户 namespace 隔离。功能不动，只把它的**后端**从 `InMemoryStore/MongoDBStore` 收敛为 mongo。

> 实施红线：删的是①假件后端，绝不删②长期记忆功能。

---

## 2. 目标状态（每轴收敛）

| 轴 | 现在 | 收敛后 | 删除物 |
|---|---|---|---|
| checkpoint | memory/sqlite/mongo | **mongo** | `InMemorySaver` 分支、sqlite 分支、`sqlite_path` |
| ledger | sqlite/mongo | **mongo** | `SqliteLedger`、`sqlite_path`；**不新增 MemoryLedger** |
| streams（agent） | memory/redis | **redis** | `streams/memory.py`、`MemoryStream` |
| 长期记忆 store | memory/mongo | **mongo** | `InMemoryStore` 分支 |
| transport（session） | memory/redis | **redis** | `transport/memory.ts` |
| store（session） | memory/mongo | **mongo** | `store/memory.ts` |

收敛后各 `backend` 选择字段（`KOKORO_CHECKPOINT_BACKEND` / `KOKORO_LEDGER_BACKEND` / `KOKORO_STREAM_BACKEND` 及 session 的 `TransportConfig`/`StoreConfig` 联合类型）**整体消失**——只剩一种实现，无需选择器。

依赖删除：`langgraph-checkpoint-sqlite`、`aiosqlite`（agent）。

---

## 3. 边界：模型/provider 不在范围内

模型 provider、凭据解析、模型注册/选择等一切「模型库」职责归 **kokoro-model**（后续独立处理），**不在本轮、不由本 spec 设计或改动**。本轮只碰存储与配置的**写法**；模型相关字段保持原样、原义，一个不加不减。

---

## 4. 分解为 Spec

### Spec A′ — agent 存储收敛（先做）

**做什么：** 把 checkpoint/ledger/长期记忆 store/streams 四轴的假件与 sqlite 后端删除，收敛为 mongo/redis 单实现；删除 `backend` 选择与 `sqlite_path`；删依赖。

**改动面：**
- 删 `storage/sqlite.py`、`streams/memory.py`。
- `storage/checkpoints.py`、`storage/ledger.py`、`storage/memory_store.py`、`streams/factory.py`：去掉多后端分支，直接构造 mongo/redis。
- `LedgerSettings`/`CheckpointSettings`/`StreamSettings`：删 `backend`、`sqlite_path` 字段（本 spec 仅删字段，机制迁移留 B）。
- `pyproject.toml`：删 `langgraph-checkpoint-sqlite`、`aiosqlite`。
- **脚本对齐**：`e2e-v21-gate.py`（现用 `sqlite` ledger/checkpoint → mongo）；`chaos-verify.py`（已 mongo，删多余 env）；`real-model-verify.py`/`trace-verify.py` 同步。
- **测试**：`test_storage.py` 从「sqlite/mongo 矩阵」收敛为 mongo 单档，且 mongo 缺失由 **skip 改 fail-loud**（CI 恒有 mongo）；删依赖 memory 后端的单测或改真后端。
- **文档**：handbook（`local-development`/`08-deployment`/`03-agent-architecture`/`11-...runtime`/`modules/kokoro-agent`）、`kokoro-agent/README.md` 去掉 sqlite/memory 后端叙述。

**保留行为：** 崩溃恢复 / 多 worker 收养 / 跨 pod 去重（CH-01/02/03）全绿；长期记忆功能可用。

### Spec B — agent config → pydantic-settings

**做什么：** 在 A′ 削小的面上，把 `config.py` + `config_file.py` 迁到 pydantic-settings。

**要点：**
- 默认值=字段默认；`_DEFAULT_*` 常量、`_int/_float/_secret`、`_stringify`、`_YAML_TO_ENV` 全删。
- **扁平 `KOKORO_*` env 名保留**。T1 spike 定论：pydantic-settings 原生 env 源**无法**穿透嵌套 `BaseModel` 的扁平 `validation_alias`（静默取默认），但**顶层字段的 `validation_alias` 原生生效**。
  → **首选机制（B plan 定死）：扁平 `AppSettings(BaseSettings)`**——所有叶子字段在顶层、各带 `validation_alias`=现有 env 名（env 原生命中、零自定义源）；域分组（`model/stream/ledger/…`）由 `@computed_field` / cached property 视图暴露，消费方 API 不变。
  - yaml：域嵌套树 → 一个**小型自定义 yaml 源**摊平进扁平键（比现 `config_file.py` 轻，且不再 stringify round-trip）；或收敛 yaml 为扁平结构（plan 权衡）。
- 优先级 `env > yaml > 默认` 由 `settings_customise_sources` 声明；进程单例用 `@lru_cache(maxsize=1)`。
- 凭据 fail-loud：凭据键落 yaml 即报错（保留现有安全属性），凭据仅走 env/secret；启动摘要打印**掩码后**的 secret（head/tail）便于诊断。
- **模型相关字段（`openai_*`/`anthropic_*`/`local_fake`/`openai_reasoning` 等）保持原样、原义**，只随 config 重构换写法，不加不减、不迁移（模型职责归 kokoro-model，见 §3）。

### Spec C — session 假件移除（agent 之后对齐）

**做什么：** 删 `transport/memory.ts`、`store/memory.ts`，`transport/factory.ts`/`store/factory.ts` 收敛单实现，`main.ts` 去掉后端选择；单测改真后端（redis/mongo）或删除；docs 对齐。达成两仓真正 local==prod 一致。

---

## 5. 测试策略

- **A′ 后单测分层**：纯逻辑测试（契约/reducer/factory 参数/中间件）仍快且零依赖；**碰存储/传输的测试需 mongo+redis 起着**（docker），且**缺失 fail-loud 不 skip**。
- 每测隔离并行安全：mongo 用唯一 db 名、redis 用唯一 stream/key 前缀。
- 回归底线：CH-01/02/03（mongo 跨 pod 崩溃恢复）、E2E 全量、long-term memory 读写。
- 交付判据：`uv run pytest`（有 mongo+redis）全绿且**无 skip 计数**在存储域；`pyright`/`ruff` 0 error；session `npm test`（Spec C 后）同理。

---

## 6. 影响面与风险

- **破坏性**：删 memory 假件后，无 docker 服务无法跑存储测试——已确认接受（docker 由用户保障）。
- **跨仓**：A′（agent）先行，C（session）对齐；两者独立可验证，避免同一文件双写。
- **脚本/文档广**：4 个 verify 脚本 + handbook 5 篇 + README 需同步，纳入各自 spec 的交付判据，不得遗漏造成「文档说 sqlite、代码已删」。
- **不在本轮**：model 库；wire 契约不变；session 业务归一化逻辑不动。

---

## 7. 交付顺序

1. **Spec A′**（agent 存储收敛）→ plan → 实施 → 验证。
2. **Spec B**（agent config → pydantic-settings）。
3. **Spec C**（session 假件移除对齐）。
4. 未来：model 库（独立 spec）。
