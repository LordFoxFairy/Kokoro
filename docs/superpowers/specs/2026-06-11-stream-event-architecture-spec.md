# Stream / SSE / Event 架构规格 — 目标态(100 分定义)

> 定位:这份规格定义 kokoro 三仓 stream/SSE/event 子系统的**无妥协理想态**——所有不变量、契约、边界、分层、门禁的目标形态。它是**验收基线**:任何 stream 改动以它为准。
> 方法:**理想态为北极星,实现分期**(零行为风险先落,破坏性项分期 + TDD/e2e)。
> 来源:2026-06-11 全链探查(envelope 组装 / cursor 三义 / seq / 续订 / redis-memory / reducer / 三仓契约),逐条 grep + 真实 e2e 实证。

---

## 1. 架构与边界

三层,只通过 redis stream + SSE 协议耦合,各自独立部署。契约单源 = `contract/events.yaml`。

| 层 | 职责 | 禁止依赖 |
|---|---|---|
| **agent** (Python) | 执行 agent(deepagents),产出**原始执行事件**(13 kind,snake_case wire,带 per-run 单调 `seq` + `segment_id`),写 redis run-events stream | 不知道 session/web;domain 不依赖框架/ORM |
| **session** (TS) | 消费原始事件 → 归一化成 AGUI envelope(去重、补归属、透传 seq、稳定 id) → 写 per-session replay stream → SSE fan-out + Last-Event-ID 续订 | 不执行 agent(只编排);不渲染 |
| **web** (React) | 消费 SSE → strict 解析 → reducer 折叠成有序 thread → 渲染 | 纯消费;不产生事件(用户输入是本地 run) |

数据流:`agent ──redis run-events──▶ session ──redis replay + SSE──▶ web`。

四层 DDD(三仓统一):`domain`(纯实体/契约,无框架) / `application`(编排,依赖抽象 Protocol/interface) / `infrastructure`(redis/sse/model 实现) / `interfaces`(worker/http/React)。上层只依赖抽象,实现由 infrastructure 注入(依赖倒置)。

---

## 2. 标识符体系(理想态:三个 "cursor" 消成一个)

### 现状三义(债)
1. **域 cursor** `run_x:NNNN`(`normalize.ts` 生成,per-run,web 反解 seq)
2. **run-events transport cursor**(agent→session,redis stream id / memory counter)
3. **replay transport cursor**(session→web,= SSE id)

三个都叫 cursor,职责不同 —— `http.ts` 得专门写注释防混淆。

### 目标态
| 标识符 | 定义 | 职责 | 不变量 |
|---|---|---|---|
| **seq** | 一等整数,agent 产生、session 透传、web 直读 | **唯一的领域排序源** | per-run **非递减**:进入排序的领域事件(message/tool/thinking/subagent/run.*)严格递增;`run.started` 合成的 `session.created`+`run.created` 共享其 seq(不参与排序);跨 run 在同一 SSE 流内可重置——reducer 只 per-run 比较 |
| **stream_id** (= transport cursor) | redis stream id `ms-seq` / memory 20-pad counter | SSE `id:` + Last-Event-ID 续点 + redis xread lastId | per-stream 全局单调(replay 流内,跨 run 不重置——可作续点) |
| **segment_id** | agent 侧分配,统一标识一段输出 | 替代 `message_ref↔message_id↔messageId` 三段映射 | 一段输出全程同一 id,session 不重映射 |
| **event_id** | session 生成,全局唯一 | web `seenEventIds` 幂等去重键 | 全局唯一 |

### 关键简化:删除域 cursor
seq 升格一等后,web 不再需要从 `run_x:NNNN` 反解顺序,SSE id 已改用 transport cursor —— **域 cursor 在 envelope 里几乎无职责**。目标态删除 `envelope.cursor`,seq 成为唯一领域排序源。三个 "cursor" 直接消掉一个,命名歧义根除。(分期 P2,需 R2 过渡期结束。)

---

## 3. 事件契约

13 kind × 三视角(agent-out / agui-out / render),snake_case wire ↔ camelCase render。

- **单源**:`contract/events.yaml` 声明 13 kind + 各视角 payload 字段 + 命名映射 + transport 常量 + status。
- **门禁**:`contract/verify.py` 结构化解析 6 镜像 + 2 stream-port,逐视角断言 kind 集 + payload 字段集 + transport 常量一致,漂移即非零退出。(已就位,注入实证。)
- **目标态补**:events.yaml 加 `envelope` 段(声明 seq/event_id/stream_id/timestamp 等共享字段)+ verify 校验 envelope 字段(P1);phase-2 确定性 generator 翻源 + `git diff --exit-code`(P4,YAGNI 触发)。

---

## 4. 传输与续订

- **SSE 三行**:`id:` = transport cursor(全局单调续点) / `event:` = kind / `data:` = envelope JSON。
- **续订**:浏览器按 SSE 规范回传 `Last-Event-ID`(=上次 transport cursor) → `resumeCursor` 守卫(仅传输游标格式 `^\d+(-\d+)?$` 放行)→ `subscribe(fromCursor)` 增量续传;畸形/缺失 → 全量重放 + `eventId` 去重兜底(绝不静默空流)。
- **两种重连**:① 瞬断自动重连(同 EventSource,浏览器带 Last-Event-ID,**增量**);② 刷新 reattach(新 EventSource,无 header,**全量 + 去重**)。
- **backend**:memory(单进程,counter)/ redis(多副本,xread BLOCK)。replay per-session 单流(多 run 共流)。
- 已就位(刚修)。**目标态补**:SSE loopback gate 加"per-runId 分组 seq 严格单调"断言(P1)。

---

## 5. 错误与边界不变量

| 不变量 | 机制 |
|---|---|
| **strict 拒收** | 所有跨进程载荷过 zod/pydantic `.strict()`/`extra=forbid`,缺字段/多余键/未知 kind 抛,绝不污染 replay |
| **畸形 fallback** | 畸形 Last-Event-ID → 全量;无数字 cursor → seq=0(过渡期);单条解析失败 → skip-and-continue(不撕整流) |
| **幂等** | `eventId` 去重(web)+ `(run_id, seq)` 去重(session),重连/replay 收敛 |
| **空流防御** | 续点失效(将来 XTRIM 裁剪)→ 检测并回退全量 |
| **终态** | `run.completed`/`run.failed` 关流;`status` 收紧为 enum(`completed`/`cancelled`/`timeout`),web 放宽 `z.literal` 避免新终态 strict-parse 成 null |

---

## 6. DDD 分层与目录

三仓 4 层(已基本就位)。目标态:
- **命名一致性**:agent `events.py` → `agent_event.py`(对齐 session `agent-event.ts`/`session-event.ts` 单数命名)。
- **子目录规则**:同前缀 ≥3 文件设 concern 子目录;<3 文件扁平化。
- **零质量债**:无 `cast`/`# type: ignore`/`if TYPE_CHECKING`/deferred import/跨模块私有穿透;循环依赖结构性断开(leaf 导入/DI/Protocol)。
- **极简注释**:只写 WHY ≤1 行;无标识符复述/历史辩解/装饰线。
- **职责大小**:文件 >~500 行或 God Object 按行为拆窄协作者。

---

## 7. 质量门禁矩阵(每条不变量可证)

| 不变量 | 类型/schema 层 | 测试层 | CI 门禁层 |
|---|---|---|---|
| seq per-run 单调 | `z.number().int().nonnegative()` | normalize/reducer test | SSE gate per-run 断言 |
| 契约不漂移 | zod/pydantic `.strict()` | — | `verify.py`(CI) |
| transport 常量一致 | — | — | `verify.py` |
| 续订增量正确 | `resumeCursor` 正则 | http.test 3 cycle + resumeCursor 5 | SSE e2e |
| eventId 幂等 | — | reducer test | — |
| envelope 结构 | strict envelopeFields | normalize/http test | verify.py(P1 后) |
| 无质量债 | — | — | tsc/pyright/ruff(CI) |

"100 分" = 这张表**满格 + 全绿**,每个格子可跑命令复现。

---

## 8. 北极星 → 现状 → 分期路线

**现状已达**:契约单源 + verify 门禁(kind/payload/**transport/envelope**)、seq 一等字段(step8)、Last-Event-ID 续订 + resumeCursor 守卫、**SSE gate per-run seq 断言**、**run.completed status 终态 enum**(生产严格/消费宽容)、`agent_event.py` 命名一致。**✅ P1 全部完成。**

**Gap 分期**(每项独立 spec→plan→TDD→门禁绿→commit):

| 期 | 项 | 风险 | 前置 |
|---|---|---|---|
| **✅ P1** 已完成 | ① SSE gate per-run seq 断言 ② events.yaml envelope 段 + verify 校验 ③ agent `events.py`→`agent_event.py` ④ status enum(session 严格 + web 宽容;agent Python 类型留待 cancel/timeout 逻辑) | 低 | — |
| **P2** 破坏性,TDD+e2e | 删域 cursor(`envelope.cursor` + web `parseCursorSeq` + normalize `cursorSeq`),seq 唯一排序源 | 中 | R2 过渡期结束(确认无旧无-seq replay 残留,或清 db) |
| **P3** 破坏性,最后 | `message_ref`→`segment_id` 折叠(agent+session+web) | 中高 | 跨三仓契约改 + 全 e2e |
| **P4** YAGNI 触发 | contract phase-2 generator 翻源 + `git diff --exit-code` | — | 契约改动频率证明值得 |

**纪律**:不再"任务驱动打地鼠"。每个分期项先对照本规格列影响面(尤其契约两端原子性、手构 fixture 连锁),再 TDD 落地。发现问题集中在设计阶段。

---

## 9. 验收审计(已执行 2026-06-11)

全仓质量审计(stream-quality-audit workflow,59 agents,35 文件,每条 ISSUES 经对抗复核去误报):**0 blocker**(正确性扎实)、2 major、29 minor。

**已修(本轮)**:
- session-event.ts 删不必要的 `as SessionEvent` cast(major,实证 no-op 加宽)。
- agent-event.ts 过期注释 `events.py`→`agent_event.py`。
- comment-noise(~20 处多行 WHY → ≤1 行)+ transport/simulator 边界 cast 消除(批量清理)。

**设计债 backlog(分期,每项独立 spec→TDD,不打地鼠)**:
| 债 | 内容 | 性质 |
|---|---|---|
| **D1** (= step10/P3) | run_agent `ref_for_segment_body`/`ref_for_segment_activity` 字节级重复 → 折叠成显式 `Segmenter` | 破坏性,TDD |
| **D2** | normalize.ts `envelope(payload: Record<string,unknown>)` 丢 per-kind 类型 → 判别联合 per-kind payload 恢复编译期保护(出站 strict zod 已兜运行期,非 blocker) | 类型强化 |
| **D3** | web state-schema `z.union` → `z.discriminatedUnion("kind")`(更快+更好错误),保 disk 序列化兼容 | zod 最佳实践 |
| **D4** | subagent_registry env JSON 手工 TypeGuard → pydantic strict 模型(extra=forbid),对齐 §5 strict 拒收 | 一致性 |
| **D5** | use-conversation.ts(557 行)God Object → 按职责拆(composer 高度/会话 store/重连/模式) | 拆分 |

**判为 defensible(非债,保留 + WHY)**:run_agent deepagents `pyright:ignore`(SDK 不可约类型边界,带 WHY)、application import 纯无状态 infra helper(实际倒置成本低)、transport DOM `MessageEvent.data` 边界(已改 typeof 守卫)。
