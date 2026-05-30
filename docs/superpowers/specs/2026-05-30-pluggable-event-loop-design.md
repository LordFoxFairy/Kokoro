# Pluggable Event Loop Design（Redis/内存可插拔，端到端归位）

- **Date:** 2026-05-30
- **Status:** approved-by-user-delegation（用户「你先做」授权）
- **Scope:** 把 `kokoro-agent` → `kokoro-session` → `kokoro-web` 的事件链路从“近路实现”拉回 ADR-009 钦定架构：agent 纯执行经 **可插拔 StreamPort** 把原始事件送到 session，session 作为**业务层**归一化成 AGUI 信封 + replay，web 纯渲染消费 SSE。本轮 agent 脑保持**确定性桩**。
- **Runtime repos:** `kokoro-web` / `kokoro-session` / `kokoro-agent`
- **Related:** ADR-009（仓库边界）、`docs/protocol/session-stream.md`（session→web，已锁）、`docs/protocol/agent-events.md`（agent→session，本轮新增）、`docs/protocol/session-replay-and-resume.md`

---

## 1. Goal

让事件链路**按文档架构真正闭环**，且**零基础设施也能跑**：

1. agent 只产出**原始 agent 事件**（`run.started` / `text.delta` / …），不越权填 session 字段。
2. agent↔session 走 **`StreamPort` 抽象**，`memory`（单进程/测试）与 `redis`（跨语言端到端）两个适配器，`KOKORO_STREAM_BACKEND` 一行切换。
3. session 作为**业务层**：消费原始事件 → 归一化成 `session-stream.md` AGUI 信封（分配 event_id/cursor/timestamp、补全归属字段、按 seq 幂等）→ 写 replay store（同样走 port）→ SSE 输出。
4. web 接**真实 SSE client**，浏览器里实时渲染 message + run 生命周期。
5. 真实三进程浏览器 demo 用 `redis` 适配器跑通 + 截图。

**本轮不做：** 真实 LLM/DeepAgents 调用、tool 事件、artifact 富渲染、权限/mode UI、认证、生产部署。

## 2. 架构

```
kokoro-agent ──StreamPort──▶ kokoro-session ──HTTP+SSE(AGUI v1.0.0)──▶ kokoro-web
  纯执行 producer        memory|redis            业务层：归一化/replay          纯渲染 consumer
  run.started/text.*     KOKORO_STREAM_BACKEND   event_id/cursor/幂等/SSE
```

- **session=业务处理层**，复杂度收口于此，目的是让 agent 与 web 两头纯粹。
- 两段契约分离：`agent-events.md`（上游原始）与 `session-stream.md`（对外 AGUI）。

## 3. StreamPort 抽象（核心，两仓各一份）

最小接口（语义一致，各语言惯用法实现）：

- `publish(stream: string, event: Json): Promise<void>` — 追加一条事件。
- `subscribe(stream: string, fromCursor?: string): AsyncIterable<{cursor, event}>` — 从游标起订阅/消费。
- `readAll(stream: string): Promise<Array<{cursor, event}>>` — replay 用。

适配器：
- **memory**：进程内 append-only + 单调序号。仅单进程有效（**跨 Python↔TS 不可用**）。服务单测与单语言快速验证。
- **redis**：Redis Streams（`XADD` / `XREADGROUP` / `XRANGE`），entry id 即游标。服务真实跨语言端到端。

选择：`KOKORO_STREAM_BACKEND=memory|redis`（默认 `memory`，保证零依赖可跑）。
后续要加 NATS/Kafka 只是再写一个适配器，不动业务层。

## 4. 各仓改动

### kokoro-agent（Python，保持纯粹）
- 新增 `infrastructure/stream_port.py`：`StreamPort` 协议 + `MemoryStreamPort` + `RedisStreamPort`（用 `redis` 库的 streams）。
- 改造 `run_agent.py`：只产出 `agent-events.md` 的原始 `kind`（删掉自填 `owner_id`/AGUI 字段）。事件用 **Pydantic strict** 模型。
- 新增 worker 入口（console-script）：消费 `kokoro:runs:requests` → 跑确定性脑 → `publish` 到 `kokoro:run:{run_id}:events`。幂等：同 run 重复请求不重复产出。

### kokoro-session（TS，业务层）
- 新增 `infrastructure/stream-port.ts`：`StreamPort` 接口 + `MemoryStreamPort` + `RedisStreamPort`。替换现有 `redis_stream.ts` 桩与内存直存近路。
- `application/start_run.ts`：`POST /runs` → 生成 `run_id` → `publish` run 请求到 requests 流（**不再 HTTP 同步调 agent**）。
- 新增 `application/normalize.ts`：原始 agent 事件 → AGUI 信封映射（分配 event_id/cursor/timestamp、补全归属、按 seq 幂等）。Zod strict 校验两侧。
- replay store 走 `StreamPort`（memory/redis 可换）。
- `interfaces/http.ts`：`GET /stream` 从 replay 回放 + 续订实时事件（SSE）。补一个 server 启动入口。

### kokoro-web（TS，纯渲染）
- `application/session-stream-preview.ts`：接真实 `fetch` + `EventSource` 连 session（已有骨架，补实时消费 + reducer 落地）。
- 浏览器主路径：输入 → 看到流式 message → run 完结。artifact 槽位本轮留最小占位。

## 5. 数据流（happy path）

1. web `POST /sessions/{id}/runs?input=...` → session 生成 run_id，`publish` run.request 到 `kokoro:runs:requests`，立即回 `{run_id}`。
2. agent worker 消费请求 → `publish` `run.started`/`text.delta`*/`text.completed`/`run.completed` 到 `kokoro:run:{run_id}:events`。
3. session 消费该 events 流 → 归一化成 AGUI（`session.created`/`run.created`/`message.delta`/`message.completed`/`run.completed`）→ 写 replay → 经 `GET /stream` SSE 推给 web。
4. web reducer 折叠事件 → 渲染对话。

## 6. 测试 / 验收（DoD）

- **agent**：`MemoryStreamPort` 下投 1 请求 → events 流出现完整序列；重复请求幂等；缺字段 Pydantic strict 崩塌拒绝。
- **session**：normalize 映射单测（每个 agent kind → 正确 AGUI 字段、cursor 单调、seq 幂等去重）；replay 单测；空流/断连不崩。
- **web**：SSE→reducer 单测；**真实浏览器主路径 + 截图**。
- **跨语言端到端**：`redis` 适配器起 agent worker + session server + web dev，浏览器走通并截图。
- **门槛**：三仓 LSP/Linter 全绿（ruff/pyright、tsc/eslint），测试 100% pass，含 schema 崩塌与幂等边界。

## 7. 风险 / 取舍

- **内存适配器跨不了进程**：已显式约束——memory 仅单进程/测试，端到端必须 redis。不假装内存能桥 Python↔TS。
- **触发也走 Redis**：agent↔session 零 HTTP、纯 port，agent 最纯；代价是 agent 多一个消费循环（可接受）。
- **确定性脑**：本轮不引入模型不确定性，先把传输/归一化/replay 这套地基测稳，真实 LLM 留下一轮。
