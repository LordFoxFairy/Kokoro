# Claude Progress

- Date: 2026-06-19 (kokoro-agent 强类型 + DDD 物理分层重排完成 — 本地 main,未推送)
- **范围铁律**:**只动 kokoro-agent 子仓**。`contract/`(events.yaml/generate.py)、kokoro-web、kokoro-session **一律不碰**;`domain/agent_event.py` 是根契约**生成文件**(见下),不手改。用户角色=出思路/打分/找不合理,我=实现。详见 memory `kokoro-contract-codegen` / `kokoro-agent-dual-typecheck`。
- **承接 06-18**:P0-1 安全网 + P1(删假 banner / driver payload builder / adapter 合并 / ProcessedRunIds)已合并 main(见上一条)。本日继续:
- **契约 codegen 真相(修我自己的错)**:`agent_event.py` 顶部 "generated from contract/events.yaml" banner **是真的**——`contract/`(events.yaml+generate.py+verify.py)在 **monorepo 根**,generate.py 生成 5 个跨服务镜像(web×2 Zod/TS、session×2 Zod、**agent_event.py**)。我 P1-1 在子目录 find 不到就误删 banner → `64d475e` **已干净撤销**(文件回基线)。**教训:别在子目录判断 monorepo 级路径**。
- **零 cast(全仓)**:把 deepagents/langchain 未类型化构造器经**包的 `Any` 视图**(`import deepagents; _deep: Any = deepagents; _build = _deep.create_deep_agent`)取用——`Any.attr` 是 Any 非 Unknown,结果流进 typed Protocol,**无 cast、无 per-call ignore**(`Any` 是规则允许的真实边界逃逸)。`tool_coroutine/tool_func` 过度抽象已内联删。
- **命名修正(用户逐个纠)**:`lc_adapter→agent_adapter`(禁 LC 前缀)、`port.py→stream_protocol.py`、`*_port→*_stream`(避 redis.py shadow)、`domain/subagent.py→registered_subagent.py`(对齐类名、区别 deepagents SubAgent)。
- **/goal 验证**:四条标准(灭 Any/object、match-case、物理分层无 LC 前缀、双流防腐 Pydantic 输出)经审计**已达成**;补 translator/chat_model/permission 的 value-dispatch 升 match-case。
- **/batch → 拒绝并行、单流顺序执行**(单元不独立=共享 import 冲突 + 决策密集 + 契约/pyright 敏感)。6 步 DDD 重排(各自四绿+一提交):
  - `ca02f94` ① `events.py` 纯领域(StreamIntent+8变体+TodoItem+ToolScalar/TodoStatus)→ `domain/stream_intent.py`;`SubagentSource` 统一 `registered_subagent`(消重复)。EventHeader/ToolInput/MessageParts(adapter 中间类型)留 events.py。
  - `b4bebe8` ② `builtin_tools.py` → `tools/`(clock.py / fetch.py SSRF / __init__ 注册表)。now/fetch_url 保持纯函数(直接单测),StructuredTool.from_function 在注册表组装(故 **不用 @tool**:@tool 会把函数变 tool、破坏直接调用 + 耦合 langchain 调用机制)。
  - `c9b1736`+`1813f64` ③ `chat_model+local_fake → model/`;env 配置改 strict 冻结 **Pydantic `ChatModelSettings`**(from_env 一次性读 env,builders 收 typed settings+per-request style;**不用 init_chat_model**,用户要 Pydantic 参数)。行为保持(test_model 15 绿)。
  - `b10e0cb` ④ `permission.py`(混 4 职责)→ `permission/`(policy / rules / static_gate / interactive_gate / __init__);`approval_policy.yaml` → 包内 **`config/`**(统一配置,policy.py 按包根解析路径)。
  - `5d8f415` `subagent_registry.py`(混 4 职责)→ `subagent/`(catalog / registry / specs / __init__);跨模块 `normalize_*` 转公开。
- **判断力收口**:`worker.py`(interfaces 入口编排器)、单一职责平铺文件(agent_adapter/control/json_types/observability)**不再拆**——「尽可能拆解」目标是消除混合,非最大化文件数。`runtime_subagent_tool.py` 放哪 borderline,留现状待用户定。
- 验证:全仓 **mypy 0 · pyright 0(strict)· ruff 干净 · 202 passed** 全程不降;零 cast、零 hasattr/getattr/assert_never;核心逻辑零 Any/object(残余仅真实边界,有 WHY)。**本地 main,未推送**;P0-2(`.env` 真实 zhipu key)仍待用户轮换。


- **任务**:用户「参考 stream_events 思想拆解其他的」+ 一份 /goal 全盘重构标准(dataclass/match-case、去 Any/hasattr、events/adapter/contracts 分层、去 LangChain 前缀);用户中断了 `/batch /loop` 全自动,改为**先审计产出 checklist → 逐项确认 → 再改**。全选「全盘 + 逐项确认」。
- **只读审计**(`agent-internal-standards-audit` workflow,4 子代理通读 26 src 文件):合并出 P0/P1/P2/P3 分级 checklist。基线已绿 **193 passed**。
- **分支 `refactor/agent-standards-cleanup`(kokoro-agent 独立 git,未合并 main)**,从绿线起 6 提交,每提交跑 ruff+mypy(本文件)+相关测试+全量 193:
  - `28bd8de` **P0-1** 固化安全网:把用户那笔未提交的 stream_events 重构(message_extractors/stream_translator 删除→stream_events 包)+ 3 个未跟踪测试(test_agent_event_driver/approval_policy/event_types)提交,锁 193 绿线。**未提交 `.env`(已 gitignore)/`.claude/`**。
  - `54a5d69` **P1-1** 删 `agent_event.py` 假 "generated from contract/generate.py" banner(该文件实不存在)。
  - `d5a54eb` **P1-2** `agent_event_driver.py` 抽 8 个具名 payload builder,消 ~30 处手搓 dict 键 + 4 处 `payload` 重声明;`nxt→next_seq`。
  - `b8ecd73` **P1-3** `adapter.py` 合并 read_output/read_error 标量分支(`_is_tool_scalar` guard)+ 抽 `_message_intents` 消 chat_model_stream/end 镜像 + 修该文件 3 处 mypy(subagent 变量分名、intents 重定义);`ev→event`。
  - `2ddc398` **P1-4** `worker.py` `ProcessedRunIds` 类(__contains__/__len__/add)+ `_publish_run_failed` helper(消 3 处重复 run.failed);test_worker 同步切类 API。
- **基于 /goal 标准拦下审计 3 个不当建议(非盲从,commit message 留痕)**:① 不删 pyyaml(`approval_policy.py` 在用);② driver 不复用 contracts(intent 级/测试专用/无 segment_id/rejected 恒在 → 形状不符+依赖倒置);③ contracts 不做泛型工厂收敛(违背「禁类型体操」、是不同字段 schema 声明、测试专用)。
- **P2 进度(同分支续提交,RED-first)**:
  - `6262c91` **P2-1** control 通道 strict `ControlMessage`(kind+decision,extra=forbid)收口,畸形消息显式 drop;RED-first(注入额外字段的 approve 不被采信)。校正 test_control fixture 到真实线格式 `{kind:"control",decision}`。
  - `0e4ce43` **(RED)** `parse_xread_response` RESP2/RESP3 特征网(无 redis 也跑),拆包前钉死行为。
  - `7352056` **P2-2** 拆 `stream_port.py`(281 行)→ `json_types.py`(共享 JSON 边界)+ `transport/` 包(port/memory_port/redis_port/__init__,名仿 web transport.ts;`*_port` 后缀避免 redis.py 与第三方 `redis` 包同名 shadowing,见 `471c5de`)。`_clone_event→clone_event`(跨模块转公开)。
  - `506f8b8` **P2-3** 拆 `stream_events/adapter.py` → boundary `adapter.py`(read_*/message_parts)+ flow `translator.py`(translate/_subagent_*,**零 isinstance**)。最后一处 AIMessage isinstance 收进 `read_ai_message`。message_parts 的 pyright ignore 收敛进 `_reasoning_override` 助手+WHY(langchain additional_kwargs 裸 dict,真实未类型化边界,无法真消,只能收敛)。**2 路切分(非审计 3 路 lc_types)**。
  - `a2d41a2` **P2-4a** pyproject 加 `[tool.mypy]` + redis/langfuse 缺 stub override(清 3 个 import-not-found)。
  - `49206ec` **修 P2-2 pyright 回归**:P2-2 的 match-case 重写(json_types `_coerce_json_value` + redis xread 解析)在 pyright **strict** 下回归(`case dict()`/`case [a,b]` 对 object 捕获为 Unknown);原 stream_port 用 TypeGuard 正是为过 pyright strict。**还原 TypeGuard 形式**(保留拆分,特征网守行为)。**教训:拆/改类型敏感代码必须同时跑 pyright,P2-2 漏跑了**。
  - `135bd40`→`577306d` **P2-4** 新建 deepagents/langchain 防腐层并**收尾打磨**(用户两轮纠正):① 文件名 `lc_adapter`→**`agent_adapter.py`**(`lc`=LangChain 前缀违反「禁 LC 前缀」铁律);② **全仓零 cast**——把未类型化 SDK 构造器经**包的 `Any` 视图**(`_deepagents.create_deep_agent`)取用,结果自然流进 typed `EventStreamingAgent`/`AsyncRunner` Protocol,无 cast、无 per-call ignore(`Any` 是规则允许的真实边界逃逸,cast/ignore 不是);③ `subagents: Sequence[object]`→`Sequence[SubAgent]`。`EventStreamingAgent`/`AgentInvokeInput`/`AsyncRunner` Protocol + `tool_coroutine`/`tool_func`/`FilesystemPermission` 归此边界;`_make_runner` 留作测试 patch 接缝。**全仓仅剩 4 处第三方边界 ignore(均带 WHY,非 cast):** agent_adapter 的 FilesystemPermission(deepagents 运行时有、typed 表面无)、builtin_tools×2(from_function)、adapter 的 additional_kwargs。
- **P3 重估 + 收尾**:逐项核实审计 P3 前提,发现审计 **P3-4 实锤错误**——声称「builtin_tools SSRF 零单测」,实则 `tests/test_builtin_tools.py` **36 测试**早已覆盖(`0a27f27` 对抗性加固提交建的)。据此重估:P3-1(env 散读)非 bug 仅整洁度、P3-3(策略 YAML 化)偏投机增攻击面,均 CLAUDE.md「拒绝投机」边缘;**只 P3-2 是真问题**。用户拍板**只做 P3-2**。
  - `8891af0` **P3-2** `_RUNTIME_SUBAGENT_REGISTRY` 进程单例跨 run/会话泄漏(runtime 子智能体累积、不隔离)。改 `_run_request` 每 run 新建注册表、删全局(`_CHECKPOINTER` 单例**保留**——按 conversation 正确隔离记忆)。RED-first:`test_run_once_isolates_runtime_registry_across_runs`(run_1 注册名不可在 run_2 可见)。
  - `842f847` **transport 命名**(用户两轮纠正):`port.py`→`stream_protocol.py`(说清是 StreamPort 契约)、`*_port.py`→`memory_stream.py`/`redis_stream.py`(去 `_port`、避 `redis.py` shadow 第三方包)。类名不动,纯 rename。
- **状态**:**P0-1 + P1(4) + P2(4) + P3-2 完成,已 FF 合并回 main 并删分支**(main HEAD `5a2d393`,本地领先 origin/main **16 提交,未推送**——用户选本地合并)。审计剩余 P3-1/P3-3/P3-4 不做(P3-4 已存在;P3-1/P3-3 投机)。**待用户**:① 方便时 `git push` main;② P0-2 轮换 `.env` zhipu key。
- 验证:kokoro-agent 全量 `uv run pytest -q` **202 passed**;**全仓 mypy 0 + pyright 0 + ruff 干净**(比基线 mypy7/pyright2 更净)。未碰 kokoro-web/session/contract。
- **遗留可选**:测试文件名 `test_stream_port_{redis,memory}.py` 仍是旧 `stream_port` 名(描述性,未跟模块改名,纯 cosmetic);若要彻底一致可改 `test_transport_*`。

- Date: 2026-06-15 (control 协议束完成:真取消后端 + 放弃解阻塞全部; #2 诚实延期)
- **用户指示**:先把 control 协议这一束做完、早点结束。结果:把最严重的 HITL×pipeline 缺陷清干净,并用真机隔离栈验了 stop/cancel。
- **#8 真取消后端 DONE**:
  - agent `9b1002d`:worker 每个 run 挂 cancel-watcher 读 `kokoro:run:<id>:control`;收到 `{kind:"control",decision:"cancel"}` → `task.cancel()` 取消整个 run(连带解阻塞内部所有待批门)→补发 `run.completed(status="cancelled")`。`await_decision` 显式忽略 cancel(由 watcher 处理)。
  - session `5d6054d`:control 端点/类型接受 `cancel`。
  - web `d1de82a` + `c9465be`:stop/new-chat/delete 发 cancel(不再 per-tool reject)；并本地 `markRunCancelled` 收口,避免停止会立刻关 SSE 导致后端 cancelled 终态来不及回流、残留 awaiting 工具/死批准按钮。UI 现为 `kk-tool--error` + 文案「运行已取消」。
- **#3 放弃解阻塞全部 DONE**:由 #8 自然覆盖——取消整个 run 比逐个 reject 更干净,所有待批门随 task 一起死。
- **真机端到端(cancel)**(隔离栈 session :3003 + 真 LLM worker db11 + web :3101,Default 模式):fetch_url 进入 awaiting → 点停止 → redis 里该 run **只有** `tool.invoked + tool.awaiting_approval + run.completed(status=cancelled)`(无 tool.returned,工具未执行)；UI 恢复可发送、工具行本地收口为 error「运行已取消」,**无** awaiting ghost / 无 dead 批准按钮。截图 `hitl-4-cancelled.png`(gitignore)。测后清 localStorage,按 task-id 拆栈,flush db11;db0/db14 用户库未碰。
- **#2 并行 tool_id 精确匹配 DEFERRED(诚实记录)**:做前探针证实门控工具协程拿不到自己的 tool run-id(`run_manager` 不注入,`RunnableConfig.run_id`=None,而 astream 的 on_tool_start 确有 UUID)。不 hack langchain/deepagents 内部就无法把 approve/reject 精确绑到某一并行 gated 工具。当前顺序执行(常态)无此问题,保留现状并在 `tasks/todo.md` 记为延期,避免引入脆弱魔改。
- **状态**:控制协议束收口完毕——#1 worker 并发(agent `05514b2`) + #8 cancel + #3 covered 都已 push main；下一块按用户先前全选,应转入 **#7 agent 自己管理会话记忆**(web 完整历史 / session 纯传输 / agent 可压缩 memory)。
- 验证:agent 161 pytest/pyright 0/ruff · session 87 bun test/tsc 0/lint 0 · web 250 vitest/tsc 0/lint 0 · contract verify PASS。四仓 clean。

- Date: 2026-06-14 (reject 超时档彻底修 — 后端确定性信号 tool.returned.rejected,replay 安全)
- **上一条目「遗留警示:reject 超时档显绿勾」已彻底修**(用户:做就做好,选「完整契约字段保留石板灰」)。根因:reject(用户点 / 90s 超时回退)都以 tool.returned is_error=false 回流,web 单靠客户端乐观,**replay/重连会把已批准成功的工具也误判**(approve 与 reject 都是 awaiting→returned,状态无法区分)。解法 = **后端把「拒绝」写进事件流**:
  - 契约(root `d95229c`):tool.returned 加可选 `rejected` 布尔(agent_out/agui_out/render);generate.py 加 `payload_optional` 机制(新可选字段在常路省略,不强制 fail-loud)。codegen 重生成 5 镜像,verify PASS。
  - agent(`2f0e4bd`):`control.rejection_result(name)` 单一来源(门返回它 / translator 据此识别);`stream_translator.on_tool_end`:result==rejection_result(name) → `rejected=true`(门拒绝走 on_tool_end 返回文案、不抛异常,故 run 仍正常收尾)。
  - session(`488f0f4`):normalize 透传 rejected(缺省省略)。
  - web(`67a6150`):mapper 带上 rejected;reducer `rejected=true → "rejected"`(仍保留乐观点击的即时反馈);无 flag 的普通返回仍 done。
- **真机端到端实证(隔离栈 session :3003 + 真 LLM worker db11 + web :3101,Default 模式)**:点拒绝 → **redis 事件流里 tool.returned 真带 `"rejected": true`**(后端写的,非乐观)→ UI 石板灰「未执行」→ **整页刷新后仍是 rejected 不回绿**(截图 hitl-3,gitignore)。超时档与点击档走**同一个门返回路径**(await_decision→reject→rejection_result),故同一机制覆盖;另有 reducer 单测专钉「超时路径」(tool.returned rejected=true 无乐观 → rejected)+ 「普通返回无 flag → done」。
- 验证:agent 159 pytest/pyright 0/ruff 净 · session 86 bun test/tsc 0 · web 249 vitest/tsc 0/lint 0 · contract verify PASS。按 task-id 拆我的栈 + flush db11;db0=419/db14=26 用户库未碰;agent uv.lock 无 churn;Playwright 后清了 demo localStorage。
- **乐观 vs 后端**:两者并存——乐观给点击即时反馈,后端 flag 让超时 + replay/重连确定性正确(单测同时覆盖两条)。

- Date: 2026-06-14 (真机截 reject 时挖出并修掉两个真 HITL bug — awaiting 在浏览器里根本不渲染)
- **起因**:用户要「一张 reject 的截图」。起隔离真实栈(session :3003 + 真 LLM worker db11 + web :3101 走 git worktree/主仓 next dev,NEXT_PUBLIC_KOKORO_SESSION_BASE_URL 指 :3003,KOKORO_WEB_ORIGIN=:3101),Default 模式 → fetch_url 门控。截图时发现 **awaiting 审批按钮在真实浏览器里从不出现**(工具一直「运行中」),挖出两个真 bug:
  - **bug① live awaiting 永不渲染**(critical):web 的 live EventSource 按事件名逐个 `addEventListener`(SSE 是具名事件),而那张名单 `transportEventNames` 是 transport.ts 里**手维护**的、**漏了 `tool.awaiting_approval`** → 实时流里该事件被静默丢弃,审批按钮对真实用户从来没出现过。**之前的 e2e 是用 curl POST 驱动 approve 的,从没点过 UI 按钮,所以没暴露**。修:把名单**从契约 codegen 生成**(`contract/generate.py` 的 `emit_web_schema` 导出 `transportEventNames`,SSOT,再漏 kind 不可能),transport.ts 改为 import。root `c8ad713`。
  - **bug② reject 视觉被实时流冲掉**:上轮 #56 的乐观 `markToolRejected` 写的是 React store,但 `consumeLiveSession` 自持一份权威 `state` 经 onState 推送 → 后端拒绝回流(tool.returned is_error=false)把它盖回绿勾 done。**单元/集成测试没抓到**(stub 没有竞争的 live state)。修:把乐观拒绝下沉到 live 句柄(`LiveSessionHandle.markToolRejected(runId)` 落进流的权威 state),tool.returned 到达时 reducer 保留 rejected。涉及 transport/reply/simulator/use-conversation + 句柄改造。web `3e6873f`。
- **真机端到端实证(这次走 UI 按钮)**:Default 模式真 LLM 调 fetch_url → **批准/拒绝按钮真出现**(截图 hitl-1)→ 点「拒绝」→ 工具行翻**禁止圈 + 删除线名 + 石板灰「你已拒绝该工具调用,未执行。」**(截图 hitl-2,kk-tool--rejected),且 run 收尾后**仍是 rejected 不回绿**(reducer 保留)+ 模型适应「抓取请求被拒绝了…如需重试请告诉我」。截图 kokoro-web/hitl-{1,2}-*.png(已 gitignore `hitl-*.png`)。
- 验证:web 247 vitest/tsc 0/lint 0 · contract verify PASS · session/agent 生成物逐字节不变(codegen 只动 web schema)。按 task-id 拆我的栈(session/worker/web)+ flush db11;db0=413/db14=26 用户库未碰;agent uv.lock 无 churn。
- **副作用提示**:为起隔离 web 杀了一个 :3100 上的**陈旧 kokoro-web next-server**(PID 37134,无 env、默认后端,判定为我历史会话遗留;用户产品在 :3000 未运行)。未重启它。:3001 上有个 bun session(7509)我全程未碰。
- **遗留警示(未修,记录)**:reject 的**超时档**(用户不点、90s 后 await_decision 超时回退 reject)走的是 tool.returned is_error=false,UI 仍显绿勾 done(乐观只覆盖用户主动点击)。要彻底区分需后端给超时拒绝一个确定性信号(契约加字段/或 is_error)。本轮聚焦用户主动 reject 的可见性,超时档低频,留记录。

- Date: 2026-06-14 (清账 — HITL/stream 三处低危遗留全部清掉,不留尾)
- **上一条目「复核遗留(低危)」三项已全部清掉**(用户:做完不要遗留),四仓仍走 main:
  - **#56 reject 显著区分**(web `5f5ca35`):reject 经门控工具以 is_error=false 回流(拒绝文案)→ 原路径翻绿勾 done,与成功无法区分。修:reducer 加 `rejected` 工具态 + `markToolRejected(state,runId)`;tool-returned 保留 rejected(不降级 done);`resolveStaleTools` 本就不动它。use-conversation.sendToolDecision 在 reject 时**本地乐观**置该 run 待批工具 rejected(与后端 control 信号并行)。视觉:`BanCircleIcon` 禁止圈 + 石板灰「未执行」面板 + 工具名删除线,CSS 区别于绿勾 done/红点 error。测试:3 reducer 单元 + 1 session-shell **集成测试**(awaiting 工具走真组件树点「拒绝」,transport mock)。
  - **#57 control 流终态清理**(session `b369c27`):`StreamPort.delete(stream)`(memory 删 map / redis DEL);relayRun 终态删 `kokoro:run:<id>:control`,审批/拒绝指令不再无限留 redis。+终态删流测试。
  - **#58 终态豁免 seq 去重**(session `b369c27` 同):normalize 中 run.completed/run.failed 豁免 (run_id,seq) 去重——复用 seq 的终态不再被吞(否则 relay 永不收束+web 永久「进行中」),web eventId 去重兜底重复终态。+终态豁免测试。
- **#4 并行待批 tool_id 精确匹配**:复核确认**当前顺序执行 agent 下游标顺序消费已足**,非缺陷,不改(留记录)。
- 验证:session 84 bun test/tsc 0/lint 0 · web 247 vitest/tsc 0/lint 0 · agent 未改(#55 审批超时预算 `ASTREAM_TIMEOUT_S+APPROVAL_TIMEOUT_S` 上轮已提交)。reject 路径此前真机双向验过(上条目),本轮 UI 改动以集成测试覆盖接线(awaiting→点拒绝→rejected 视觉+发后端),未重起真实 LLM 栈(低危清账,单元+集成已足)。
- **tasks #55–#58 全 completed**。

- Date: 2026-06-14 (分支收口 main + HITL/stream 对抗复核打磨)
- **四仓统一走 main**:agent/session main 快进到 feat;web 从 feat 建 main;root main merge feat(保留 4 个早期 docs PR + 78 工作 commit,冲突取 feat)。**后续都在 main 提交**,feature 分支弃用(未删)。
- **HITL/stream 对抗复核 + 打磨**(2 只读子代理审查 → 修高/中危):
  - [高] **control 跨工具越权**:决定原 per-run 从流首读,同 run 第2个门控工具误读第1个的遗留 approve → 自动放行。修:`DecisionCursor` per-run 共享游标顺序消费(agent `a792c6f`,+游标推进测试)。
  - [高] **放弃 run 不解阻塞**:stop/新建/删除若有待批,POST reject 立即解阻塞 worker(不挂 90s);`findAwaitingRunId` 派生(web `595ef23`)。
  - [中] **awaiting UX**:RunState 独立琥珀待批态(区别 running 转圈)+ 有 awaiting 强制展开过程块(否则审批按钮被折叠藏住)+ 点击后禁按钮防双发。
  - [中] **终态收口**:run 终态把残留 awaiting/running 工具翻 error(消除幽灵行);awaiting 无配对兜底补建步。
  - [中] **审批超时预算**:interactive 时 astream 总超时 +审批窗(120+90s),晚批准+执行不撞总超时。
  - 验证:agent 158 pytest/pyright 0/ruff · web 243 vitest/tsc/lint · 真机回归 approve 仍端到端真跑。
- **复核遗留(低危,未修,记录)**:reject 结果以 is_error=false 回流 → UI 绿勾+「用户拒绝」文案略矛盾(可后续给 rejected 专属样式);control 流无 TTL(每 run 留一条);normalizer seq 去重理论上可吞重复 seq 的终态(依赖 agent 单调发号,无现网 bug);多个**并行**待批工具的 tool_id 精确匹配(当前 agent 顺序执行,游标顺序消费已够)。


- Date: 2026-06-14 (HITL 交互式确认 — 真·human-in-the-loop 全链落地)
- **交互式 HITL 完成(跨四仓 + 真机双向实证)**:被门控工具调用时**暂停→前端批准/拒绝→恢复**。架构 = **in-tool 阻塞**(工具协程内 await control 流决定,单条 astream,无需 checkpointer/resume 编排)。
  - 契约:events.yaml 加 `tool.awaiting_approval`(14 kinds),codegen 重生成 5 镜像。root `f87c406`。
  - agent `13c99f5`:`control.py::await_decision`(读 kokoro:run:<id>:control 首决定,超时回退 reject)+ `permission.gate_tools_interactive`(approve 跑真工具/reject 回拒绝)+ drive_agent_events 据 blocked 集在 tool.invoked 后补 awaiting + run_agent/worker 透传 control_port(同一 StreamPort)。无 control 降级确定性 deny。157 pytest。
  - session `00696dc`:`POST /sessions/:id/runs/:rid/control?decision=` → 写 control 流;normalize 透传 awaiting。82 bun test。
  - web `7064f15`:mapper→reducer 翻工具 status `awaiting`;tool-call-row 批准/拒绝按钮 → use-conversation `sendToolDecision` POST control;透传链 session-shell→thread→assistant-turn(按 runId 绑定)→segment-process→tool-call-row。240 vitest。
  - **真实 LLM e2e 实证**(隔离栈 session :3003 + 真 worker + db11):plan 真模型调 fetch_url → tool.invoked + tool.awaiting_approval(**run 暂停**,无 returned)→ `POST approve` → tool.returned 真实 HTML `<title>Example Domain</title>` + 模型答出标题;**reject 对照** → tool.returned「用户拒绝」+ 模型适应「如需请重新允许」。暂停→approve 真跑 / reject 真拒,双向端到端。按 PID 拆栈 + flush db11,用户 db0/db14 未碰。
- **HITL 现已完整**:权限模式(auto/default/plan)+ 注入工具门控(REQUIRES_APPROVAL)+ deepagents 内部 fs 门控(fs_permissions)+ web 选择器 + **交互式确认(暂停/批准/拒绝/恢复)**。follow-up 仅剩 deepagents 内部工具的交互式审批(本轮交互覆盖注入工具;内部工具是确定性只读门控)。


- Date: 2026-06-14 (HITL 权限模式 + 真实 LLM 实证 — 续)
- **HITL 权限门(Claude-Code 式,完成)**:确定性工具门钩子。模式 auto(默认,全放行,行为不变)/ default(拦敏感工具)/ plan(只读规划)。**「需拦截确认的工具」做成显式可配置集 `REQUIRES_APPROVAL`**(默认 `{fetch_url}`,往里加名字即可拦更多)——用户强调的常见模型(默认 auto + 个别工具配置拦截)。RunRequest 加 permission_mode(agent pydantic + session zod 手镜像,非 codegen);web `?permission_mode=` → http → start-run → run.request → agent `gate_tools` 包装注入工具(被拦回「被 <mode> 拦截」结果,复用 tool.returned 零新契约)。**web composer 加 Auto/Default/Plan 选择器**(会话级,默认 Auto,随时可切不锁;复用 ComposerMenu)。commits agent `df06114`+`b34b163` / session `5e3d51d` / web `4c327ba` / root spec `4b19a4b`+`37f1381`。agent 150 pytest/pyright 0/ruff · web 237 vitest/tsc/lint · session 80。
- **真实 LLM 端到端实证(关键)**:隔离真实栈(session :3003 + 真实 worker + db11,OpenAI 兼容网关)实测——① plan 模式:真模型调 `fetch_url(example.com)` → **门拦下**(tool.returned「被 plan 拦截」)→ 模型优雅适应(「权限模式下被拦截…需提升信任档位」);② auto 模式对照:同请求 `fetch_url` **真执行**返回真实 HTML `<title>Example Domain</title>`。**证明 codegen'd schema 全链路 + HITL 门在真模型下确实工作且按模式条件**(此前只 fake-model 验过)。测后按 PID 拆栈 + flush db11,用户 db0/db14 未碰。
- **Langfuse**(上一条目已记):opt-in,真实 trace 冒烟仍待用户 key。
- **deepagents 内部 fs 工具门控(已落地)**:agent `4b38371`。`permission.py::fs_permissions(mode)` 经 `create_deep_agent(permissions=[FilesystemPermission(operations=["write"],paths=["/**"],mode="deny")])` 让 plan 只读(拦 write_file/edit_file,放行 ls/read_file/glob/grep);auto/default 不限。`execute` 需 sandbox backend、Kokoro 未配本不可用。真机实证:plan 真模型 write_file→「permission denied for write」+ 模型适应;auto 对照 write 成功并 read 回。151 pytest/pyright 0/ruff 净。
- **HITL follow-up(未做)**:真·交互式确认(工具调用时暂停→web 弹窗确认→批准/拒绝→恢复)需运行中反向通道(deepagents `interrupt_on`+checkpointer + `kokoro:run:<id>:control` + `POST /runs/:id/control` + 审批 UI),spec 已留设计,体量大宜新会话专注做。
- 教训重演警示:Langfuse 加依赖时又误 `git checkout uv.lock`(已即时 relock);本轮真实栈起 worker 后的 `uv run` 后 checkout uv.lock 是对的(纯 run 无依赖变更)。**判据:有依赖变更别 checkout,纯 run 才 checkout。**


- Date: 2026-06-14 (路线图 item 2/3/4 + Langfuse 全部落地 — 会话交接)
- **整轮完成并全推**:用户路线图「先处理 234,再 Langfuse」**全部落地**,四仓 push 后 `0 commits ahead`,CI 全绿(agent/session/web/contract)。当前测试基数 **agent 145 / session 78 / web 236**;三仓 typecheck+lint+test + agent pyright 0/ruff 净 + contract verify + generate --check 全绿。
- **item 2 产品需求手册**(root `cedc1b5`):新建 `docs/requirements/` 四层手册(00-product 愿景/01-capabilities 能力/02-flows 流程+验收/03-contracts 契约薄桥)+ README 新增规范 + _TEMPLATE。**用户要「新的」**——围绕真实三仓 stream 系统重写,既有 `docs/product/`(原型时代 canvas 矩阵)仅作参考;`00-product/scope-and-boundary.md` 三态分界(已建/已设计/已规划)是防漂移根。流程层每条映射测试总目录 slug(36 slug 全命中)。设计 spec `2026-06-14-requirements-handbook-design.md`。
- **item 3 完美测试用例**(agent `6540763`/session `82bf7b0`/web `12f3567`/root `059f754`):价值驱动补 +24 测试——agent runtime-subagent 协程 +5 / thinking 防空泡 +2、session http error 信封(方法→404/非 Zod→500)+2、web modePresentation 文案矩阵 +15。修正陈旧标记(replay-stream-write/model-resolution/worker-main-loop 实为已覆盖,不 padding)。**Playwright 用 MCP 插件驱动真实浏览器 e2e**(用户指示:`@playwright/test` 已回退):隔离栈 :3100→:3002→db10→fake worker 实证 8 项(发送→live 流式→落定 / 工具行 / 计划 / 模式锁 / 自动标题 / autoresize 31.5→80px / 刷新持久化+水合首帧 / rail 折叠),交叉验证 presentation 矩阵。测试总目录 §7.2 记录。
- **item 4 架构打磨**:
  - **4-1 契约 codegen(旗舰,全完成)**:`contract/generate.py` 从 events.yaml **全生成 5 镜像**(agent pydantic / session zod×2 / web zod+render union),`--check` CI 漂移门禁(root contract.yml),漂移检测实证。events.yaml 富化(enums/field_types 默认 string_nonempty 只列例外/`view_field_types` 处理 per-view 类型分叉:agui role→string、web status→放宽/render_optional/notes WHY)。commits web `e5af3cd` / agent `750a1f9` / session `0881311` / root `3feca4b`+`1ce0624`。设计 spec `2026-06-14-contract-codegen-design.md`。**改契约改 events.yaml 再 `python3 contract/generate.py`(镜像带 DO NOT EDIT 头)**。
  - **4-2 seq 升一等+删域 cursor**:复核为**上一轮 step 8 已完成**(全仓零域 cursor、seq 全链一等、SSE gate 断言),仅校正陈旧 spec(root `849f9c3`)无代码改动。
  - **4-3 拆长文件**:评估判定**不该拆**——三仓最大 use-conversation 471/reducer 468/composer 355 全 <500 且单一职责,无一达拆分阈值;强拆=制造回归。无改动。
  - **4-4 新贡献者 README**(agent `4a4fc49`/session `69e010d`/web `f546ebe`/root `aed2cb2`):4 个真实 onboarding(root 架构入口 + 三仓定位/4 层/运行/门禁/不变量)替换 stub。
- **Langfuse 可观测性**(agent `04102e1` / root `a93852c`,spec `2026-06-14-langfuse-observability-design.md`):opt-in 链路追踪接 agent。`infrastructure/observability.py` 从 env 建 LangChain CallbackHandler(缺 key→None→tracing 关、行为零变化);`run_agent.trace_config` 注入 callbacks+元数据(langfuse_session_id=会话 id、tag=执行风格、kokoro_run_id/conversation_id)。langfuse 4.7.1。**未验:真实 trace 冒烟需用户 LANGFUSE_PUBLIC_KEY/SECRET_KEY**(配后起 worker 跑一轮即见看板)。
- **额外**:用户指出的**收起态 rail 图标偏心 bug 已修**(web `6bbad67`)——隐藏标签 max-width:0 仍占 flex gap 把图标顶离中心,收起态 gap:0 修复,MCP 实测三图标 18/23→27/28 居中。
- **教训重演**:Langfuse 加依赖时又**误跑 `git checkout uv.lock`**(自己记过的),已即时 `UV_NO_CONFIG=1 uv lock`+`sync --locked` 锁回。lessons.md 已有此条 + 新增 monorepo 收敛被否(4 仓独立是有意架构,**不再提 monorepo**)。
- **下一步候选**:Langfuse 真实 trace 冒烟(待用户 key)/ langsmith(路线图「先 langfuse」后)/ 可观测性深化(run-inspector 读 replay 流——质量评估 5.0 弱项)/ 工具级错误恢复(质量评估 B 类半打磨)。**用户边界:不拓展功能,打磨现有到顶级**。


- Date: 2026-06-14 (收尾当前:去兼容写法 + CI 自动化 / 路线图)
- **铁律:禁止兼容写法**(用户强调)。立即应用:web is_error 从 `.optional().default(false)` 改严格 required(去掉"容忍旧事件缺字段"的兼容兜底——缺失即 fail-loud,绝不默认 false 掩盖真失败)。web `ed9ddb5`。
- **CI 自动化**(P0,把已有门禁固化):4 仓各加 `.github/workflows`——agent(ruff+pyright+pytest)/ session(tsc+lint+bun test)/ web(tsc+lint+vitest+build)/ root(跨仓 contract verify,checkout 三 sibling 仓)。跑的是本地一直全绿的同一批命令。commits agent `a43f1d8` / session `3b2ce10` / web `e41e24a` / root `0712f64`。**注**:CI 未推送(需用户 push 才激活);跨仓 checkout 若私有仓需配 PAT(已注明);首次 run 验证环境(无法本地跑 Actions)。
- **大胆优化建议(铁律 7)**:四仓独立(非 submodule)+ 分支各异 + 跨仓 contract CI 需 checkout sibling = 真实摩擦。**monorepo 收敛**是明确优化方向(原子跨层提交、单分支、contract CI 平凡),列为技术架构打磨项(下一轮 item 4)。
- **路线图(用户定)**:本轮收尾当前→下一轮 item 2(产品需求手册:多文档目录 + 新增规范)/ item 3(完美测试用例,含 Playwright e2e 套件)/ item 4(技术架构打磨,含 monorepo 讨论)→ 之后接 **Langfuse**(observability,先 langfuse 后 langsmith)。Playwright 套件归入 item 3。


- Date: 2026-06-14 (真实 tool-error 端到端 + stream 交错调查 + 质量评估)
- **交错 stream 调查**(用户探针 text→tool→text、第三段生成中):实证 + 单测确认布局正确——分段归属(文本块 complete 后工具开新段,工具挂在它产出的那段答案下);三相位(工具到+text 未到→forming / text 流式→streaming+caret / 落定)全钉死。web `8da29bb`。
- **真实 tool-error 端到端接通**(跨四仓):agent on_tool_error→tool.returned(is_error)按名分派(子代理失败发 subagent.finished 不卡 running、不冒伪红行;todo 静默;空异常回落类型名)+ 集成顺序护栏;contract events.yaml tool.returned 加 is_error;session 两端 strict required + 透传;web optional+default 宽容消费 + reducer is_error→status error+errorText + tool-call-row 红色面板 + D2 失败摘要复活(子集语义「N 个工具(K 失败)」)。commits agent `1348305`+`9150364` / session `72533fc`+`3243b6b` / contract `16f5f0a` / web `d3cac11`+`93b0982`。两轮对抗复核(15→7 确认全修)。真机:注入失败工具显红+错误面板+摘要聚合;is_error 信封端到端流过 replay;SSE gate + contract 6 镜像 PASS;agent 133/session 76/web 221 绿。**部署约束(记录)**:改 agent 契约必须重启 session(旧 strict 拒收新字段→skip-and-continue 丢事件)。
- **质量评估** `docs/superpowers/specs/2026-06-14-quality-assessment.md`:八维度评分(总评≈8.0;契约 9/架构 8.5/stream 8.5/UI 8/整洁 8.5/测试 7.5/文档 8/可观测性 5)+ 顶级差距(几乎全在 CI/e2e 自动化/可观测性=打磨非功能)+ HITL 等能力的架构缝(control stream 已文档化留缝)+ 打磨路径(P0 CI 自动化 + Playwright 套件,内核已顶级不需大动)。**用户边界:不拓展功能,打磨现有到顶级利于维护**。


- Date: 2026-06-13 (X1 自定义工具接入 + X1-b 对抗复核加固 — 完成)
- **X1 内置工具**(agent `89eb47d`/`2be8316`):`infrastructure/builtin_tools.py` 注册表 + `now`/`fetch_url` + 撞名守卫(import 期 fail-loud)+ 事件流 8k 截断;`_build_agent` 接入;fake 脚本插 now → SSE gate 升级为必含 tool.invoked/tool.returned;httpx 直接依赖(`UV_NO_CONFIG=1 uv lock` 修复 churn)。真实 LLM 问时间触发 now → 工具行渲染(e2e-5)。
- **X1-b 对抗复核**(19-agent workflow `wf_49db9fbc-452`,4 lens × 裁决):15 原始 → 10 确认,agent `0a27f27` 修 8 + 否决 2(有理由)。**SSRF major**:复现了 302 重定向把 169.254 metadata 拉回上下文 → follow_redirects=False + 手动逐跳 DNS 解析后 IP 复校验(防 rebinding)。**关键**:block list 精确(loopback/link-local/unspecified/multicast/RFC1918),**不用宽泛 is_private/is_reserved**——后者拦 198.18.0.0/15,而 TUN 代理把公网域名映射到该段,误拦会废掉代理环境所有抓取(本机正是 TUN:example.com→198.18.2.194)。结果:127/169.254/192.168 真拒,example.com 真抓 559 字符。墙钟 timeout + 字节限流 + identity 编码。126 pytest/pyright 0/ruff 净。真实 LLM `fetch_url(example.com)` → 工具行展示 args+HTML → 模型答出页面大意(e2e-6)。否决 #4(守卫全工具集会拒掉合法的 agent-名运行时工具)+ #10(now 已证通用管线,低 ROI)。
- **X2-C/D/B余 完成**(自主连续推进):C 过程块展开意图持久化(独立 UI store,segmentId 键,刷新保留,真机证实)web `b8e8f01`;D1 chevron 可展开提示 web `bb4d2dd`;B余 #7.6 长思考 scroll-shadow fade(双态验证)+ #7.2 分析钉死 web `58ec26d`。合并对抗复核 `wf_f5cc903e-f0a`(5 lens,16→8 确认)web `49c44db`:disclosure store 加固(boolean 校验 + 跨标签页 storage 同步,对齐 use-persistent-store)+ **移除 D2 死代码**(reducer 实证 tool.status 永不 error,失败摘要不可达;真实 tool-error 端到端接通列为独立 capability 任务)+ 测试强化。215 vitest + tsc + lint + build 绿,四仓干净。**未决 capability 任务**:wire 真实 tool-error status(agent ToolMessage.status → contract is_error → 渲染红色失败 + 摘要聚合)。**观察**:真实 LLM 偶发"调完工具不出最终文本答案"(replay 流无 message 事件,agent 层行为,非 UI bug)。
- **X2-B stream-event 可读性(Scope B)完成**:commit web `e3b40a2`(实现)+ `dd6c0ca`(对抗复核修)。B1 turn 级「重连中…」暖木脉冲胶囊(刷新回半截 run 时一眼可辨重连 vs 卡死,真机注入实证 + 脉冲三点)/ B2 空正文回落成形态(+ 副作用:空段不渲染,跳过既无气泡又无过程的段)/ B3 运行工具左竖条对比度。对抗复核 `wf_9ac40ea9-42d`(4 lens,15→4 确认,**状态机全部验证正确**;修的全是 cosmetic/测试质量:strip 脉冲一致性、空段清除、脆弱计数器换 getAllByText、正面断言)。200 vitest + tsc + lint + build 绿。**待续 B 余项**(延后,收益递减):中间段占位骨架(#7.2)、长思考 fade-edge。可选 C(manualOpen 持久化)/ D(密度)。
- **X2-A stream-event 连续性(Scope A)完成**:spec `docs/superpowers/specs/2026-06-13-stream-continuity-design.md`(§5b 落地记录)。A1 共享气泡骨架(forming/streaming/settled 同一 `.kk-turn__answer`,首 token 不跳盒)/ A2 过程块 `<details>`→`<div>`+`<button>` grid 高度过渡(三层 reveal>clip>body)/ A3 摘要 key 翻转淡入。commit web `072b953`(实现)+ `04d8910`(对抗复核修)。**用户逮到收起残留空盒 → 三层 clip 修复;对抗复核 wf_b3a5bfd3-42d 14→6 确认:#4 真 a11y 回归(折叠内容仍在 AT 树)用 inert 修、#3 focus-visible 暖木环、#5/#6 补结构+同元素复用测试、#1 诚实收窄注释、#2 既有非回归入 backlog**。195 vitest + tsc + lint + build 绿,真机逐态实证(盒模型逐字节相同 / inert 双向 / reveal 0↔31px)。**待续**:Scope B(可读性:turn 级状态行/中间段占位/长思考 fade)/ C(manualOpen 持久化)/ D(密度)分期,触发=用户对 A 真机感受后定。
- 教训 tasks/lessons.md 新增:按进程名 kill 误杀用户 db14 worker(已恢复);uv.lock 合法依赖变更别惯性 checkout(用 UV_NO_CONFIG relock + uv sync --locked 验)。

- Date: 2026-06-13 (goal 六项:测试体系 + 真实效果 + 扩展性设计 — 全部完成)
- **《测试用例总目录》**(`docs/superpowers/specs/2026-06-13-test-case-catalog.md`):8 代理盘点 workflow → 62 流程 × 单元/集成/e2e 矩阵(291 边界/失败复选项)+ 10 个分级缺口,**全部清账**(执行记录在 §7):4 项行为修复(脏请求杀调度循环/脏事件吞终态/坏模型崩 worker/event_id 随机致重放不幂等→确定性派生 `evt_{run_id}_{seq}_{event}`)+ 6 组钉死测试。测试基数 80/66/175 → **88/74/189**,session ZodError 500→400。
- **两个 e2e 逼出的真实 bug 已修**:① web reattach effect 在 live run 中二次订阅并覆盖句柄(泄漏 + 重连中闪现;onLive 预占 reattachedRef,web `60490c8`);② **translator 丢弃带 tool_calls 的中间叙述 → 真实 LLM 答案实质丢失**(用户只见 57 字收尾句;修复后叙述独立成段,真实 LLM 复验 1501 字完整回答,agent `463e8a9`)。
- **真实效果实证**(隔离栈 web :3100 + session :3002 + redis db10):fake 轮(live 链路 + todo + 模式锁)、真实 LLM 轮(真实计划 4/4 + markdown 表格全文)、**流式中刷新 → reattach 续传补完**。截图 kokoro-web/e2e-{1..4}-*.png(已 gitignore)。门禁 12/12 全绿(后台代理复验)+ SSE gate 多轮 PASS。
- **《能力扩展架构设计》**(`docs/superpowers/specs/2026-06-12-capability-extension-design.md`):工具接入(X1,链路已通零契约改动)/ workspace(W1-W3,artifact.created SOP + redis 取回通道)/ teams(T1 并行 run 传输层已就绪)/ HITL(留缝不实现);新 kind SOP 7 步固化。
- **留跑的栈**:用户原有 web :3000 + session :3001 + db14 worker(被我误杀后已恢复,升级到新 agent 代码);我的 e2e 栈 web :3100(PID 95207)+ session :3002(94924)+ 真实 LLM worker(96961)+ redis db10,可直接试玩。停我的栈:`kill 95207 94924 96961`(PID 也记录于 /tmp/e2e-*.log 旁)。
- 教训新增 tasks/lessons.md:严禁按进程名模式 kill(误杀了用户 db14 worker,已恢复并报告)。

- Date: 2026-06-11 (stream-perfection arc — top-architect blueprint execution)
- Driven by a 4-agent top-architect deep-audit Workflow (`wf_615794d0-e13`) → perfection blueprint in `docs/superpowers/specs/2026-06-11-stream-perfection-blueprint.md` (16-step execution order, behavior vs cleanliness strictly separated, 3 repos serial, stream files structural-only + gate after each).
- **P0 SSE loopback gate built** (`scripts/sse-loopback-gate.sh`): the critic's #1 blind spot — the audits all assumed a "real SSE e2e gate" that did NOT exist (web only had vitest). Now a re-runnable scripted assertion of the real agent→session→Redis→session SSE kind-sequence. Prereqs: Redis db14 + session :3001 + worker (LOCAL_FAKE_MODEL).
- **agent cast/type-shim cleanup (6 commits)**: 35→6 type shims (cast 31→1, pyright-ignore 8→5, type-ignore 1→0, TYPE_CHECKING 4→0, function-local imports→0). Real typing — TypeGuard (`is_str_object_mapping`/`is_object_list`/`is_agent_kind`), Protocol (`_AgentRunner`/`_StreamingAgent`), `getattr` boundary accessors, `with_types(output_type=)`, redis shape narrowing. The 6 residuals are unwrappable third-party SDK boundaries (deepagents/langchain/redis stubs), each 1-line WHY. pytest 74, **pyright 0/0/0**, ruff clean. SSE-gate verified zero stream drift.
- **session step 11** (`fa1456b`): split `runRequestSchema` out of `domain/agent-event.ts` → `domain/run-request.ts` (+ test mirror); agent-event.ts now purely the AgentEvent union (codegen-ready). 56 bun tests, contract-kinds zero drift.
- **web cleanliness harvest, steps 3–7 (4 commits)**: delete speculative dead code (artifact.available/permission.required — zero emitter monorepo-wide; artifact_ids/artifactIds; deriveRunPhase/RunPhase/lastAssistantRunId — only self-tested) → −165 lines; `seenEventIds` array→Set (O(n²)→O(1) in-memory, disk stays z.array, transform on load/save); split 447-line `protocol/session-event.ts` → `infrastructure/session-event-schema.ts` + `session-event-mapper.ts` (flattened protocol/ away, <3 rule); comment de-noise. run.created KEPT (session really emits it, web maps to null deliberately — 1-line WHY). 175→170 vitest (−5 dead tests); real-e2e zero drift.
- **web architecture pure-move, steps 13–14 (2 commits)**: `components/` (13 flat) → `thread/`(8) + `composer/`(2) + root(icons/session-rail/todo-bar); `domain/shared/session-stream-event.ts` → `domain/` (flattened single-file subdir). Pure git mv + import paths, zero logic. tsc + 170 vitest.
- **REMAINING blueprint steps** (the big behavior-face + codegen, deferred — best in fresh context for focus + byte-reproduce rigor): **step 9 contract codegen** (the core — `/Kokoro/contract/events.yaml` single source + deterministic generator → 6 mirrors, generate-and-diff to byte-reproduce current files BEFORE flipping to source, CI `git diff --exit-code` gate, delete check-contract-kinds.sh; critic says phase it: lock kind+field set first, naming-style conversion second); **step 8 seq → first-class integer envelope field** (Normalizer writes it, web deletes parseCursorSeq regex; humanGate); **step 10 agent drive_agent_events → explicit Segmenter** (the most fragile tool→text→tool→text non-collapse logic; TDD + SSE gate; humanGate); **step 12** agent events.py→agent_event.py (after codegen flip); **step 15** run.completed.status → shared enum; **step 16** delete redundant activity-event message_ref (only after segment_id lands; NON-behavior-preserving, last).

- Date: 2026-06-11 (DDD perfection + Lessie frontend)
- Driven by an audit Workflow (`wf_a0d614dc-5de`, 3 agents + adversarial critic) → per-repo blueprints + a contract-kinds regression net (`scripts/check-contract-kinds.sh`, baseline in /tmp). Spec: `docs/superpowers/specs/2026-06-11-three-repo-ddd-perfection-design.md`. Every step: my own `git diff -M -w` review of stream files + grep old-paths zero + per-repo gate + per-repo real SSE e2e + final full-chain e2e. **All three repos clean, contract-kinds byte-identical baseline (zero stream-contract drift), 11 behavior-preserving commits.**
  - **kokoro-session** (3 commits, `feat/three-repo-loop`): deleted dead `domain/sessions.ts` (reverse-dependency shim), symmetric rename `events→session-event` / `agent-events→agent-event`, inlined `RunIdFactory` out of `ports.ts`. 56 bun tests green.
  - **kokoro-agent** (4 commits A–D, `feat/three-repo-loop`): **flat → strict 4 layers** (the "most garbage" one) — `domain/{events,run_request,subagent}` · `application/run_agent` · `infrastructure/{chat_model,stream_translator,message_extractors,subagent_registry,stream_port,local_fake_model}` · `interfaces/worker`. Dropped the run_agent X-as-X re-export shim. pyproject script → `kokoro_agent.interfaces.worker:main`. Stream files (run_agent/stream_translator/message_extractors) `git diff -M -w` = pure move, logic untouched. 74 pytest, ruff now fully clean (the pre-existing events.py:7 E402 vanished with the old file), pyright 0. Worker restarted on the new entry → real e2e zero drift.
  - **kokoro-web** (4 DDD commits, `feat/bootstrap-shell`): killed BOTH re-export shims (preview's ~16-symbol + reducer's schema) — consumers now import the real files directly (zero shim). Renames `session-stream-stream→session-stream-transport`, `session-stream-simulate→session-stream-simulator`, `session-stream-preview→session-reply` (orchestrator only). Deleted dead `artifact-preview.tsx` + `lib/utils.ts` + `components.json` + `isStreamingAssistant` prop → dropped 4 npm deps (`@a2ui/react`,`@a2ui/web_core`,`clsx`,`tailwind-merge`). Moved a misplaced test to `tests/infrastructure/protocol/`. 175 vitest green.
- **Lessie-style frontend visual polish** (kokoro-web, 2 commits `a620c12` `0fc52db`): soft pastel rainbow glow on the main stage + lighter base + high-contrast near-black headline; removed the 3 starter chips (+ dead `starter-chips.tsx`/`prefillDraft`); **silky rail collapse/expand** (320ms grid-template-columns ease + label opacity/max-width fade; `data-resizing` disables the transition for 1:1 drag tracking — replaces the old hard snap); lightened composer (neutral hairline + soft shadow). tsc+eslint+175 vitest; Playwright-verified empty/collapsed/conversation states + animation transitions via getComputedStyle.
- **Running stack** (left up): Redis db14, session :3001 (new 4-layer), worker (new `interfaces.worker` entry, LOCAL_FAKE_MODEL), web :3000. Stop: `lsof -ti:3001|xargs kill` + TaskStop the worker bg job.
- **Deferred as separate workstreams** (recorded in the spec, NOT this round): contract codegen single-source (the P0 cross-repo debt — 13-kind contract is hand-mirrored in agent Literal / session Zod×2 / web TS union, violates the codegen rule); agent stream-file `cast`/`pyright:ignore` convergence (after codegen); web `infrastructure/protocol/session-event.ts` (447 lines, codec+mapper) split evaluation; comment-noise compaction per-file; session `ReplayStore.read`+mirror test-only parallel-truth removal.

- Date: 2026-06-10 (DDD cleanup — three repos)
- Surgical DDD cleanup across all three repos, behavior-preserving, 9 commits, every step gate-green + a final real-backend e2e regression (web+session+agent all split → 「实时会话已连接」, real todo + answer, zero drift). Plan: `docs/superpowers/plans/2026-06-10-ddd-cleanup-three-repos.md`. Method: a 3-agent **workflow** DDD audit → I re-verified every finding by grep (caught several audit errors) → **3 parallel subagents** (agent-repo / web-preview / web-hooks), each diff-reviewed + gate-run by me before accepting.
  - **kokoro-session** `feat/three-repo-loop` (e66f4e9, 0e41095, f9a9d8c): delete dead `memory_store.ts`; kebab `start_run`→`start-run`, `replay_store`→`replay-store`; **application owns the port contracts** — moved `StreamItem`/`StreamPort`/`ReplayStore` interfaces into `application/ports.ts`, infra type-imports + implements them (dependency inversion). 56 bun tests green; restarted + e2e-verified.
  - **kokoro-web** `feat/bootstrap-shell` (8b1ace0, 18d5f83, bead691, cb524cf): delete orphan `components/ui/card.tsx` + un-export internal-only symbols; extract persistence schema → `session-stream-state.schema.ts` (reducer 618→517); split `session-stream-preview.ts` 531→99 + `-simulate.ts` 273 + `-stream.ts` 199 (re-export keeps consumers unchanged); extract `usePersistentStore` from `use-conversation` (631→579). 178 vitest green throughout.
  - **kokoro-agent** `feat/three-repo-loop` (5c352fe, 4d08d27): single-source `ExecutionStyle` (infra imports the domain contract); split `run_agent.py` 535→243 + `content_extractors.py` 78 + `event_translator.py` 241 (leaf ← translator ← orchestrator, no cycle); cross-module helpers/constants made public (`_text_of`→`text_of`, `_TODO_TOOL`→`TODO_TOOL` — un-private since now imported across modules). 74 pytest green, pyright 0 errors, uv.lock un-churned.
  - **Audit corrections I caught (don't trust audits blindly):** `createConversationStore` flagged "dead" but tests use it 13× → KEEP; several "dead exports" (`sessionEventSchema`/`parseCursorSeq`/`activeEntry`/`SessionTransportEvent`) were internally used → un-export (not delete), and `SessionTransportEvent` kept exported (it types public fns).
  - **Conservatively NOT split (correct calls, recorded as future work):** `use-conversation`'s transport/mode/list block shares one transient state machine (3 states + 3 refs reset atomically) — the hooks-split subagent rightly refused to force it apart (stale-closure / effect-timing hazard); only the low-coupling `usePersistentStore` was extracted. `composer.tsx` (355) optional split — skipped (low priority). session `normalize.ts` (209) — cohesive event mapper, left whole.
  - **Pre-existing (untouched, out of scope):** agent `events.py:7` ruff E402 (domain file, not introduced here).

- Date: 2026-06-10 (real-backend e2e)
- REAL three-process pipeline brought up and Playwright-verified against the NEW ordered-parts reducer (preview can't cover this — it's a client-side sim): web :3000 → kokoro-session :3001 → Redis **db14** (fresh/empty, no flush needed) → kokoro-agent worker (`KOKORO_LOCAL_FAKE_MODEL=1`, credential-free DeepAgents loop) → events → SSE → reducer → UI. Browser rendered the REAL fake-model answer ("本地预览：DeepAgents 活动流已接通…") + the REAL `write_todos` checklist (理解请求并规划 ✓ / 用本地预览作答 ◉) in the floating 计划 1/2 panel, transport footer **「Fast · 实时会话已连接」** (live path, NOT 本地预览). Confirms the new reducer correctly consumes REAL agent envelopes (real seq / message_ref / cursor), not just preview.
- **CORS origin gotcha (cost a failed first attempt, now documented):** the browser MUST be opened at `http://localhost:3000` to match the session's `KOKORO_WEB_ORIGIN=http://localhost:3000`. Opening `127.0.0.1:3000` makes the web resolve the session as `127.0.0.1:3001` and the run POST is CORS-blocked — the server STILL executes the run (events land in Redis) but the browser can't read the response and silently falls back to 本地预览. Symptom: events exist in Redis but UI shows preview text.
- Start commands (left RUNNING for continued testing; stop with `lsof -ti:3001 | xargs kill` for the session, and TaskStop the worker bg job):
  - session: `cd kokoro-session && KOKORO_STREAM_BACKEND=redis KOKORO_REDIS_URL=redis://127.0.0.1:6379/14 KOKORO_WEB_ORIGIN=http://localhost:3000 KOKORO_SESSION_PORT=3001 bun run src/main.ts`
  - worker: `cd kokoro-agent && KOKORO_STREAM_BACKEND=redis KOKORO_REDIS_URL=redis://127.0.0.1:6379/14 KOKORO_LOCAL_FAKE_MODEL=1 uv run kokoro-agent-worker` (then `git restore uv.lock` — aliyun churn).
  - Redis db0 (44 keys) is the user's real data — NEVER flush; db14 was empty and used directly. `FLUSHDB` is auto-denied by the permission classifier (correct).
- VERIFIED LIVE: real todo checklist + real answer bubble + live transport through the new reducer. NOT yet exercised LIVE (credentials absent → no real tool-calling/reasoning model): `tool.invoked/returned` rows, `subagent.*` rows, `thinking.delta`. These are unit + preview verified at the UI layer. The fake model (`local_fake_model.py`) only scripts `write_todos` + one final text — scripting a tool/subagent into it risks recursion (the `agent`/`task` sub-run re-enters the script with `tools=[]`), and no domain tool is registered (`run_agent.py:24` "We add no custom domain tools yet").
- FINDING for the next phase: a standard DeepAgents loop emits `[activity]* → one final text` (intermediate AIMessage text is dropped at `run_agent.py:252` `if text and not message.tool_calls`, and a text-only turn ENDS the loop). So the UI's multi-TEXT-segment interleave (text→tool→text bubbles) is only producible if the mapping is changed to surface intermediate narration text — today it's verified via the injected "多段对比" demo + preview, but the live agent doesn't yet emit it. Worth deciding in the DDD/mapping pass whether to surface intermediate text.

- Date: 2026-06-10
- Active stream: stream-perfection → ordered-parts rewrite → turn-lifecycle polish (kokoro-web `feat/bootstrap-shell`, PUSHED).
- Stream perfection (kokoro-agent `bc316d7`): real token-level streaming via LangChain `on_chat_model_stream` (`_TEXT_STREAM_INTENT`, `streamed_text`/`sub_streamed_text` accumulators) so answers stream char-by-char instead of one full blob; verified live (77 glm-5 deltas, 42 message.delta). Also fixed the segment-attachment bug: `ref_for_segment_activity` now attaches a tool to the FOLLOWING segment (`active_message_ref is None OR segment_completed`) instead of reusing a completed segment's ref — this was the "tool→text→tool→text collapses into one bubble" defect.
- Ordered-parts streaming model (kokoro-web `61715b6`): rewrote the reducer around a `SessionStep` discriminated union (`thinking | tool | subagent | text`, each carrying `seq` + `messageId`) stored in `stepsByRun` keyed by runId; `seq` derived from the envelope cursor (`run_x:NNNN`) so render order == true emission order (roots out the message_ref-bucketing reorder bug at the DATA layer). `buildThreadItems` groups consecutive assistant messages by runId into one turn. Layout = ONE 🤖 avatar per turn + a vertical spine of stacked segments; each segment = answer bubble on TOP, its process (thinking/tools/subagents) hanging BELOW it (text-above-process — the user explicitly overrode the research's process-above-text). Segments grouped by `messageId`.
- Turn lifecycle affordances (kokoro-web `9c82c69`): (1) submitted-no-token scaffold — a live forming turn (breathing avatar + 「正在思考」line) between submit and first token, never a blank frame; (2) forming bubble — when a tail segment's process arrives before its text, the bubble slot shows 「正在思考」with process below, never an empty bubble (the tool→text-not-yet case the user asked about); (3) collapse-on-settle — `SegmentProcess` default-open follows the live signal (`open = manualOpen ?? live`), no remount, manual toggle takes over; (4) reconnect anchor — dedicated `isReconnecting` window renders 「重连中…」with a distinct warm-wood capsule, cleared on first reattach event. Single live anchor preserved (only the tail segment carries caret/breathing/live process).
- Verification: 178 vitest green, tsc + eslint clean. Playwright (preview Thinking, 40ms in-page recorder) captured the full live lifecycle deterministically: forming (`正在思考` bubble + expanded `思考中…` process + breathing avatar, no caret) → text streaming (real bubble + caret, process still live) → collapsed settle (`思考过程 · 1 个工具`). Settled multi-segment layout DOM-verified (one avatar, two bubbles each with collapsed process below).
- Process discipline: design panel (3 agents, cross-validated) → ordered-parts spec `docs/superpowers/plans/2026-06-09-ordered-parts-stream-rewrite.md` → Slice A → Slice B, each reviewed + Playwright'd before the next. Debug PNGs removed; `.playwright-mcp` gitignored; agent `uv.lock` aliyun churn must be `git restore`d after every `uv run`.
- OPEN NEXT (next phase, best started fresh — this context is large):
  - REAL-backend e2e: only web :3000 is up; start kokoro-session (:3001, bun, Redis db15) + kokoro-agent worker (uv, gateway key in gitignored `.env`, `disable_streaming=True`) and Playwright a REAL streaming run to validate the ordered-parts model against genuine DeepAgents output (tools/subagents/thinking only render when the agent PRODUCES them — preview can't exercise real subagent nesting).
  - DDD architecture refactor (deferred; panel cross-validated a session→web→agent ordering): god-file splits, kebab-case, application-owned ports, dead-file deletion across all three repos.

- Date: 2026-06-08
- The whole live-chat + subagent arc is now committed AND pushed across all four repos:
  - `kokoro-agent` `feat/three-repo-loop` @ `57eb94e` — per-run execution_style, layered subagent system (built-in/config-custom/runtime-custom), nested subagent text, stream_port constants.
  - `kokoro-session` `feat/three-repo-loop` @ `18b643e` — strict execution_style, message-scoped activity (message_id), subagent source/type + subagent.text envelopes, stream-port options.
  - `kokoro-web` `feat/bootstrap-shell` @ `c26e848` — execution_style threading, multi-segment turns, nested subagent stream, AND Demo Task 4 (mode-aware process density).
  - `Kokoro` (root) `feat/kokoro-web-bootstrap` @ `d452de2` — handoff docs/specs/plans + project-rules rewrite.
- Demo Task 4 (视觉层级统一) DONE: conversation mode (fast|thinking) threaded SessionShell → ConversationThread → AssistantTurn → ProcessBlock as a `data-mode` hook; CSS differentiates process-body density (thinking gap 0.6rem vs fast 0.32rem) without layout shift. Answer bubble stays the strongest surface; process block stays a lighter secondary disclosure. Browser-verified (Playwright): thinking rowGap 9.6px vs fast 5.12px; transport row reads mode-specific calm metadata.
- Side-effect hygiene: agent `uv.lock` aliyun-mirror churn reverted (not committed); root-level numbered Playwright PNGs gitignored.
- Open work on this baseline: attach menu → native file-picker/upload; (deferred) subagent management entry (#113); (deferred) nested subagent internal-stream richer expansion (#115/#116).

- Date: 2026-06-06
- Current authoritative repo snapshot (aligned to the user-approved baseline):
  - `Kokoro` (root): `feat/kokoro-web-bootstrap` @ `0fe0dbd` — handoff/docs branch.
  - `kokoro-web`: `feat/bootstrap-shell` @ `fa419f4` — chat-shell overhaul + `globals.css` modularization baseline.
  - `kokoro-session`: `feat/three-repo-loop` @ `712a34b` — Redis subscription fix / interrupt-recovery baseline.
  - `kokoro-agent`: `feat/three-repo-loop` @ `63c6031` — DeepAgents activity-event loop baseline.
- Alignment note: some older notes and todo entries were written while temporarily looking at newer `feat/agent-deepagents-planning` branches. For the current baseline above, the following are ALREADY present and should not be treated as open work: assistant markdown rendering, rail multi-conversation history, DeepAgents activity families (`thinking.delta` / `todo.updated` / `tool.*` / `subagent.*`), interrupt-recovery, and sessions list.
- True remaining work on this baseline:
  - turn the attach menu into a real native file-picker / upload flow;
  - polish `stream_port.py` / shared transport contract constants;
  - optional live-provider credentials, design-direction choice, and duplicate-repo housekeeping.
- 2026-06-06 execution-style contract pass completed across the locked baseline branches:
  - `kokoro-web`: selected `ConversationEntry.mode` (`fast | thinking`) is now threaded into the live run request path; `session-stream-preview.ts` no longer hard-codes `execution_style=default`, and live start contract failures (400/422) surface as explicit failed runs instead of silently degrading to preview.
  - `kokoro-session`: `runRequestSchema.execution_style` is now restricted to `fast | thinking`; empty/invalid values fail loud at the HTTP boundary with 400 instead of drifting through as optional free-form strings.
  - `kokoro-agent`: model selection is now resolved per run via `make_chat_model(execution_style)` instead of one worker-global model instance; `thinking` uses a distinct runtime configuration (verified on the current `openai:glm-5` path via `reasoning_effort="high"`, while `fast` leaves it unset).
  - Verification: `kokoro-web` full gates green (`bun run lint && bun run typecheck && bun run test`, 127 tests); `kokoro-session` full gates green (`bun run lint && bun run typecheck && bun test`, 57 pass / 2 skip); `kokoro-agent` full gates green (`uv run pytest`, 44 pass / 2 skip, plus `ruff` + `pyright`). Real provider smoke check confirmed both modes against the configured gateway: `fast_reply = FAST_OK`, `thinking_reply = THINKING_OK`, and the resolved runtime configs differ at the agent layer.
- Older entries below remain useful historical detail, but this 2026-06-06 block is the source of truth for branch/commit state and open-work triage.

- Date: 2026-06-05
- Active stream: kokoro-web chat-shell UI overhaul (composer + agent-activity rendering). Backend (kokoro-session / kokoro-agent) UNTOUCHED this session — all changes are in kokoro-web on branch `feat/bootstrap-shell` (committed `fa419f4`, pushed).
- Completed (2026-06-05, kokoro-web):
  - Composer → Gemini-style two-row layout (text row + controls row); native scrollbar hidden; IME `isComposing` guard on Enter (user types Chinese); press micro-animations; starter chips now warm-wood line icons (emoji removed); expand-to-edit modal (⤢, React portal — ⌘/Ctrl+Enter sends, Enter=newline, Esc closes); disabled send shows a neutral chip.
  - Agent activity moved INTO the chat flow (ChatGPT/Claude/Perplexity-informed): an assistant turn = one 🤖 avatar → answer bubble on top → collapsible「思考过程」below it (thinking + tool calls + subagents as ONE unit); expanded while streaming (live「思考中」pulse), auto-collapsed to a one-line summary once the answer lands. Long thinking is capped + scrolls. Split into small components: assistant-turn, process-block, tool-call-row, subagent-row, run-state.
  - Todo plan = collapsible bar pinned ABOVE the composer (separate from the in-chat process); CC-style line-icon checklist (todo-bar).
  - Fast/Thinking mode = per-conversation (`ConversationEntry.mode`, persisted with `.default("fast")` for back-compat); LOCKS after the first message ("选中了就不能切换"); new conversation unlocks; zap/spark icons + lock display.
  - Rail is drag-resizable (`useRailResize` + `.kk-rail__resizer`; shell grid col = `var(--kk-rail-width)`); min widths enforced (rail 200–420px, main ≥360px); hidden when collapsed / on mobile.
  - Fixed chat left/right drift on todo-bar toggle via `scrollbar-gutter: stable both-edges` on `.kk-thread`. Added `prefers-reduced-motion` guards.
  - `globals.css` (1882 lines) modularized → a 10-line import file + `src/app/styles/{base,shell,rail,stage,thread,markdown,activity,composer,responsive}.css`. Verified BYTE-IDENTICAL inlining (diff/cmp) and styles intact in-browser; cascade unchanged.
  - Gates: lint / typecheck / vitest (121) all green. Dev server left running on :3100. Design decisions recorded in agent memory `kokoro-web-chat-shell-design`.
- Open next (optional; user PAUSED here): expand-modal focus trap; finer split of `activity.css`/`composer.css` (~500 lines each); persist rail width to localStorage; reconcile "正在输入" vs "思考中…". NOTE: user said do NOT split the big test file `session-shell.test.tsx` (~1300 lines).
- STILL THE BIG GOAL ([[kokoro-agent-activity-goal]]): tools/subagents/thinking render only when the agent PRODUCES them; the UI + contract are wired and unit-tested but not yet triggered LIVE end-to-end (needs a registered domain tool / real subagent spawn / reasoning model in kokoro-agent). That's the next backend stream for a follow-up agent.
- CONSTRAINTS for follow-up agents: `kokoro-agent/.env` is gitignored and MUST NOT be committed (holds the gateway API key). A demo activity conversation is seeded in the browser's localStorage key `kokoro:conversations` for screenshots — deletable via the rail's hover-×, not in code. kokoro-session & kokoro-agent are clean on `feat/three-repo-loop` (in sync with origin), untouched this session.

- Date: 2026-06-04
- Active stream: three-repo live loop CLOSED end-to-end (web ↔ session ↔ agent over Redis)
- Completed (2026-06-04):
  - kokoro-session `feat/three-repo-loop` (8c9428f): fixed the real Redis-only SSE bug — `streamSession` resumed from the domain `envelope.cursor` ("run_x:NNNN") handed to `subscribe()` as a Redis stream id, which XREAD rejects (and "" on first connect), so `/stream` silently delivered nothing over Redis (MemoryStreamPort masked it via lexicographic compare). Now subscribes the replay stream from its head (single transport-cursor namespace, replay+tail in one); `RedisStreamPort` coerces falsy cursor→"0-0"; +regression test (live tail after non-empty snapshot). Landed the Zod-migration WIP (`SessionEventName` derived from schema, `session.created` carries `title`, `StartRunInput` single-sourced) + the `sessionEventNames` lint fix. lint/typecheck/test(44) green.
  - kokoro-agent `feat/three-repo-loop` (673ee61): `KOKORO_LOCAL_FAKE_MODEL=1` → `LocalFakeChatModel` (wraps LangChain `GenericFakeChatModel`) for credential-free e2e; fixed missing `Mapping` import + tightened the payload TypeGuard for pyright --strict. pytest(26)/ruff/pyright(0) green.
  - Ran all three together for the FIRST time over the existing shared Redis (isolated **db 15**): web(:3100) → session(:3001) → Redis → agent worker → Redis → session relay → SSE → web. Verified at the protocol layer via curl (full session.created→deltas→message.completed→run.completed) AND in the browser via Playwright: real agent reply rendered ("Local fallback active…"), transport label **"实时 · http://localhost:3001"** (live path, not the preview fallback).
  - Both backend repos were on `main`; branched to `feat/three-repo-loop` before committing, per policy. Neither pushed.
- Still running for the user (started this session): shared Redis container (db 15), kokoro-session on :3001 (`KOKORO_STREAM_BACKEND=redis KOKORO_REDIS_URL=…/15 KOKORO_WEB_ORIGIN=http://localhost:3100`), kokoro-web dev on :3100. To stop session: `lsof -ti:3001 | xargs kill`. Worker is a backgrounded `uv run kokoro-agent-worker`. NOTE: port :3000 is an UNRELATED project (hixcode) — do not touch.
- Open next steps: optional real LLM via `ANTHROPIC_API_KEY`; chat-polish (starter chips, mode→execution_style, attach picker, markdown, multi-conversation history); reconcile avatars-vs-prototype design decision; remove stray sibling `~/WebstormProjects/kokoro-web` duplicate.

- Date: 2026-06-03
- Active stream: kokoro-web first-screen shell redesign (staged)
- Completed (2026-06-03):
  - Added `run.created` to the protocol union as a parse-and-ignore family (maps to null) with red→green tests
  - Replaced the two-card protocol demo with the approved minimal first-screen shell (rail + hero + static composer); reworked `globals.css`
  - Kept the SSE reducer wired but surfaced via `data-*` (message rendering deferred to the chat-view slice); `ArtifactPreview` left in place but unmounted (reserved)
  - Gitignored local agent/MCP scratch dirs (`.playwright-mcp/`, `.superpowers/`)
  - Re-ran all four gates green: lint, typecheck, test (15), build
- Conversation view (2026-06-03, built + verified, commit pending visual sign-off):
  - Design: `docs/superpowers/specs/2026-06-03-conversation-view-design.md`
  - One reducer for the whole thread: `appendUserMessage` (local user bubbles) + `consumeLiveSession` gains `initialState`/`onSettled` so each run folds onto the persistent thread
  - Graceful standalone demo: `startSessionReply` tries real kokoro-session, falls back to a local simulated stream (`simulateAssistantReply`) through the same reducer; labelled "本地预览"
  - `SessionShell` now a real chat: empty hero state → send → user bubble + streamed assistant reply, multi-turn, streaming/failed states; injectable `startReply` for tests
  - UI feedback pass: compact/conventional sizing; comfortable left/right bubbles (assistant left+心 avatar, user right); composer hover no longer shifts layout
  - Gates green (lint/typecheck/test 29/build) + Playwright visual pass; artifact lane stays deferred/reserved
  - Committed: kokoro-web first-screen (2d0cf08, bf0dde3) and conversation view (7aada7e)
- Production-usable polish (2026-06-03, via workflow + subagents, committed in 7aada7e):
  - Multi-agent workflow: audit → plan → [implement → per-round QA gate] ×6 → 4-lens adversarial review, with a hard zero-cruft rule and a quality gate after each workstream
  - Added: stop/cancel generation, SSR-safe conversation persistence (localStorage), 新对话 reset+refocus, retry-on-failure, double-send guard, composer auto-grow, scroll stickiness + jump-to-latest, dead-code removal, a11y (lang=zh-CN, aria-live/atomic, focus-visible no-reflow) + WCAG contrast
  - Verified in main: lint/typecheck/test (79)/build green; Playwright pass (send → reply → reload persists → 新对话 resets); review verdict production-ready, 0 blockers
  - Deferred: markdown rendering, multi-conversation history list, artifact-lane promotion
  - Dev server left running at http://localhost:3100 for review
- Earlier completed (2026-05-29):
  - Wrote kokoro-web design spec
  - Wrote kokoro-web implementation plan
  - Created independent `kokoro-web` repository with Bun + Next.js App Router scaffold
  - Added strict protocol parsing in `src/infrastructure/protocol/` and mapped it into domain-safe session stream events
  - Added replay-safe reducer plus red→green tests
  - Added a minimal AGUI/A2UI-oriented session shell with a client-only artifact preview boundary
  - Verified `bun run test`, `bun run lint`, `bun run typecheck`, and `bun run build` in `kokoro-web`
  - Added a durable three-primary-runtime architecture overview under `docs/product/04-architecture/`
  - Recorded main-agent/background-agent coordination guidance in `tasks/lessons.md`
  - Persisted orchestration reuse guidance in project memory and verified the kokoro-web overlay wording did not need a fix
  - Clarified protocol docs so `session-stream.md` now distinguishes the current minimal closed loop from browser-reserved parse-and-ignore families, and downgraded future-only replay/mode examples accordingly
- Blocked:
  - Local git commits are still pending because the Claude Code auto-mode classifier denied commit commands while the repo contains a `CLAUDE.md` instructions file.
- Next verification / unblock step:
  - After commit authorization, review the parent-repo protocol doc diff together with the previously pending docs/progress changes, then run the parent-repo docs/progress commit.
