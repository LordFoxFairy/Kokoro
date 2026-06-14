# 能力扩展架构设计 — 工具接入 / Workspace / Teams / HITL

> 定位:在 stream/SSE/event 子系统已达 [架构规格](2026-06-11-stream-event-architecture-spec.md) 满分基线的前提下,定义**后续能力如何长出来**——每个能力挂在哪个现有缝上、要新开什么缝、分期与验收。
> 方法:理想态为北极星,实现分期;**优先复用已有挂点,新概念最少化**;任何新事件 kind 一律走契约 SOP(§6),不开旁路。
> 来源:2026-06-12 deepagents SDK 源码级调研(`.venv/.../deepagents/graph.py:217-237`)+ 三仓挂点逐文件核对(调研结论经抽查修正:`execution_style` 实际已在 `worker.py:42` per-run 解析)。

---

## 1. 冻结不变量(扩展不得破坏)

任何新能力接入后,以下不变量必须原样成立(由现有门禁矩阵守护):

1. **契约单源**:新 kind/新字段只在 `contract/events.yaml` 声明,6 镜像由 `contract/verify.py` 拦漂移。
2. **标识符体系**:`seq`(领域排序)/ `stream_id`(续点)/ `segment_id`(段引用)/ `event_id`(去重)职责不变;新事件进排序就分配 seq,属段就带 segment_id。
3. **strict 生产 / 宽容消费**:跨进程载荷生产端 `.strict()`/`extra=forbid`,web 消费端对新枚举值宽容降级。
4. **层间只经 redis stream + SSE 耦合**;domain 不依赖框架。

---

## 2. 现状扩展点地图

| 能力 | 挂点现状 | 位置 | 难度 |
|---|---|---|---|
| 自定义域工具 | ✅ 已有缝,事件链路零改动 | `run_agent.py` `tools=[...]`;未知工具名自动translate 成 `tool.invoked/returned` | 低 |
| 子代理(已三层) | ✅ 完整 | `subagent_registry.py`:built-in / env `KOKORO_CUSTOM_SUBAGENTS` / runtime tool | — |
| middleware | ✅ 已有缝(未用) | `create_deep_agent(middleware=[...])` | 中 |
| 新事件 kind | ✅ SOP 化(§6) | events.yaml + 6 镜像 + verify | 中 |
| workspace 文件 | ⚠️ 半成品 | deepagents 虚拟 fs 工具已内置(StateBackend);envelope 预留 `workspace_id/created_by/initial_mode`(web 宽容可选);**无暴露通道** | 中→高 |
| teams 并行 run | ⚠️ 传输层已支持 | per-session 单 replay 流多 run + per-run seq(P2/P3 已实证);**缺 UI 并行呈现 + 编排** | 中→高 |
| HITL/中断 | ❌ 无跨进程缝 | `interrupt_on` 只在 agent 进程内;无反向 control 通道 | 高 |
| 用户/多租户 | ❌ 无 | `normalize.ts:54` `owner_id` 硬编码 | 高(YAGNI) |

deepagents 侧可用而未用的面(源码实证):`backend=`(StateBackend 默认 / FilesystemBackend 真实盘 / StoreBackend 持久化)、`middleware=`、`interrupt_on=`、`AsyncSubAgent`、`skills=` / `memory=` / `permissions=`。

---

## 3. 能力一:自定义域工具接入(分期 X1,低风险先行)

**结论:这是最便宜的能力——整条事件链路已为它铺好,加一个工具 = 写一个函数 + 注册,契约零改动。**

- `stream_translator.py` 对非 `write_todos/task/agent` 的任何工具自动产 `tool.invoked`(args)/`tool.returned`(str 化 result);session/web 全链已渲染 tool row。
- **注册模式**:镜像 `subagent_registry` 的三层——
  1. built-in:`infrastructure/tools/`(有 IO)+ `domain/tools/`(纯函数),`BUILT_IN_TOOLS` 清单;
  2. config-custom:`KOKORO_CUSTOM_TOOLS` 暂不做(自定义工具需要代码体,env 装不下;触发条件 = 出现"仅声明即可用"的工具类,如 HTTP 调用模板)。
- **接入点**:`run_agent._build_agent` 的 `tools=[build_runtime_custom_subagent_tool(...), *BUILT_IN_TOOLS]`。
- **边界**:工具名不得撞 deepagents 内置(`write_todos/ls/read_file/write_file/edit_file/glob/grep/execute/task`)——注册时断言;长 result 截断策略(>8KB 截断 + 提示,防 redis 单条事件膨胀)。
- **验收**:注册一个真实工具(首选 `fetch_url` 或 `now`)→ pytest 边界(撞名拒收/截断)→ SSE gate 看到 `tool.invoked→tool.returned` → web Playwright 截图 tool row。

## 4. 能力二:Workspace(文件/工件)

历史上 `artifact.available` 因**无发射端**被按 YAGNI 删除——这次先把发射端做出来,事件随后。

- **W1(会话内工件,中)**:agent 已能用虚拟 fs(`write_file` 等,StateBackend)。run 终态时枚举虚拟 fs,对每个产物发新 kind **`artifact.created`**(payload:`segment_id, path, mime, size, preview`,preview 为前 N 字节;走 §6 SOP)。web 在 turn 下渲染工件卡片。**小内容走事件流,原则:事件只载元数据 + 短预览。**
- **W2(取回通道,中)**:大文件不进事件流。session 加 `GET /sessions/:id/files/:path`;实现要点:agent 把工件全文随 `artifact.created` 同步写 redis(`kokoro:session:<id>:artifact:<path>`,带 TTL),session 端点直读 redis——**不打通 agent 进程内 state 的实时访问**(state 随 run 结束消亡,redis 是两进程已有的唯一耦合点,不新增 RPC)。
- **W3(持久 workspace,高,YAGNI 触发)**:`backend=` 换 StoreBackend/FilesystemBackend,跨 run 共享文件;`workspace_id` 字段从预留转正(session.created 透传,web 已宽容)。触发条件:用户明确要"接着上次的文件继续"。

## 5. 能力三:Teams(多 agent 协作)

- **T1(并行 run,中)**:传输与数据层**已就绪**——同 session 多 run 并行 POST `/runs`,replay 单流多 run、per-run seq、web `stepsByRun` 按 runId 分组折叠,全部 P2/P3 实证过。缺的只是:① web UI 并行 turn 呈现(两个 turn 同时 streaming 的布局/锚点);② 并发幂等 e2e(两 run 交错事件,reducer 不串台)。**先补 ② 的测试再做 ① 的 UI。**
- **T2(结构化协作,高,远期)**:agent 间共享 todos/邮箱、协调者分派。依赖 T1 + 新 kind(`team.message` 类)+ 编排者(session 层或独立 conductor)。触发条件:单 agent + 子代理(已有三层)不够用的真实场景出现。**在 deepagents 已提供 `task` 子代理的前提下,绝大多数"多人协作"场景应优先用子代理表达**——teams 是子代理不可达(跨模型/跨进程/长生命周期)时的升级,不是默认。

## 6. 新增事件 kind 的标准作业程序(SOP)

把"扩展"变成例行公事——任何新 kind 按此 checklist,**顺序固定,verify 不绿不前进**:

1. `contract/events.yaml`:声明 kind 的 `agent_out / agui_out / render` 三视角 payload。
2. agent `domain/agent_event.py`:`AgentKind` Literal + 文档表;产出点(translator 或 run_agent)分配 seq/segment_id。
3. session `domain/agent-event.ts`:zod 判别联合新 arm(strict)。
4. session `application/normalize.ts`:新 case → `envelope(...)`(泛型保证 payload 编译期对齐)。
5. web `infrastructure/transport-event-schema.ts` + `transport-event-mapper.ts`:schema arm + mapper case(snake→camel)。
6. web `domain/session-stream-event.ts` + reducer/渲染:域 arm + 折叠 + UI。
7. 门禁:`python3 contract/verify.py` PASS → 三仓单元(每层 strict 注入测试)→ `scripts/sse-loopback-gate.sh`(真实 redis 链路看到新 kind)。

**消费端兼容**:web 对未知 kind 的策略是 strict-parse 失败 skip-and-continue(不撕整流)——新 kind 可以先落后端、web 晚一步升级,顺序天然安全。

## 7. HITL / 反向控制(远期,只留缝不实现)

当前唯一反向通道是 `POST /runs`。HITL 需要 run 进行中的 web→agent 信令(批准/拒绝/补充输入):

- **预留设计**:per-run control stream(`kokoro:run:<id>:control`,redis),agent worker 在 `astream_events` 循环间隙非阻塞 xread;session 加 `POST /runs/:id/control`。配合 deepagents `interrupt_on=` + checkpointer 恢复。
- **不现在做的理由**:无 checkpointer 时 interrupt 即丢 run;引入 checkpointer 牵动 backend 选型(应与 W3 一起决策)。触发条件:出现需要用户确认的危险工具(如 `execute`)。

## 8. 不做什么(YAGNI 边界)

- **用户认证/多租户**:`owner_id` 维持硬编码,直到有第二个真实用户。
- **通用插件系统/动态 schema**:契约必须静态可验证,拒绝运行时注册 kind。
- **contract phase-2 generator**:维持原触发条件(契约改动频率证明值得)——若 X1/W1 连续落地导致 events.yaml 高频改动,即触发。

## 9. 分期路线

| 期 | 内容 | 前置 | 验收 |
|---|---|---|---|
| **X1** 自定义工具 | 注册表 + 1 个真实工具 | 无 | pytest 边界 + SSE gate 出 tool.* + Playwright 截图 |
| **T1a** 并发幂等测试 | 双 run 交错 e2e(reducer 不串台) | 无 | session/web 测试 + gate 双 run 断言 |
| **W1** artifact.created | §6 SOP 全程 | X1(发射端经验) | verify PASS + gate 出新 kind + web 工件卡片 |
| **W2** 文件取回端点 | redis artifact 镜像 + GET 端点 | W1 | http.test + e2e curl |
| **T1b** 并行 turn UI | 双 streaming 布局 | T1a | Playwright 双流截图 |
| **W3/T2/HITL** | 持久 workspace / 结构化 teams / 控制通道 | 真实需求触发 | — |
