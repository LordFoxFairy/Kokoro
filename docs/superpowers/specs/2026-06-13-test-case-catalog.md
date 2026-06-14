# Kokoro 测试用例总目录 — 全流程 × 单元/集成/e2e

> 定位:三仓(kokoro-agent / kokoro-session / kokoro-web)**全部交互流程与业务流程**的测试用例总账。每条流程列:主路径、边界用例、失败路径用例、现有覆盖(精确到测试文件)、缺口。它是「测试完成度」的验收基线:任何新流程/新事件 kind 落地时,在此登记用例并指向真实测试。
> 来源:2026-06-13 八代理盘点 workflow(62 流程、36 测试资产文件,逐断言核对)+ 综合矩阵。覆盖判定:✅ covered = 主路径与关键边界皆有断言;🟡 partial = 仅主路径;🔴 gap = 无断言。
> 现状:盘点时 37 covered / 21 partial / 4 gap;**§7 全部 10 个缺口已于 2026-06-13 清账**(4 项行为修复 + 6 组钉死测试,见 §7 执行记录)。

---

## 1. 测试金字塔现状

单元层最厚实且边界质量高：agent 约 80 例（13-kind 契约往返、流式/非流式/子代理路由、分段语义、schema 崩溃矩阵）、session 约 66 例（normalize 全 kind 映射、(run_id,seq) 幂等、resumeCursor 守卫）、web 的 schema/reducer/组件测试边界矩阵充分（it.each 非法形状×13、eventId 去重、seq 交错保序）。集成层以 kokoro-web 的 session-shell.test.tsx（56 例整壳集成）和三仓的 http/start-run/transport/worker 测试为骨干，happy path 与状态机边界覆盖良好，但「失败路径集成」系统性缺位——调度循环吃脏请求即整体死亡、relay 遇脏事件终态丢失、POST 失败降级触发层、模型解析崩溃无 run.failed、重启/多副本幂等，这五处跨进程静默失败全部无断言。e2e 层仅两件手工门禁资产：scripts/sse-loopback-gate.sh（真实 agent→Redis→session→SSE 链路 4 断言，含 seq 单调与 5 kind 在场）和 contract/verify.py（三仓契约字段集静态锁定 7 检查），无 Playwright 套件、无 CI 接入（.github/ 不存在，根 package.json 无聚合入口），两个门禁全靠手工记得跑——金字塔形状健康（宽单元/中集成/窄 e2e），但顶端两块门禁悬空未自动化，且中层的失败注入测试是整体最大空洞。

**三层基数**:agent **140** pytest · session **78** bun test · web **236** vitest · 跨仓门禁 2(contract/verify.py 七检查 + scripts/sse-loopback-gate.sh 四断言)。沿革:盘点 80/66/175 → §7 补缺 88/74/189 → tool-error 轮 133/76/221 → **item 3 补强(2026-06-14)140/78/236**(见 §7.2)。CI 接入已补:四仓各 `.github/workflows`(全绿);e2e 真实效果由 Playwright MCP 插件驱动真实浏览器验证(见 §7.2),非 committed 套件。

---

## 2. 覆盖矩阵总览

| # | 流程 | 仓 | 单元 | 集成 | e2e/门禁 | 判定 |
|---|---|---|---|---|---|---|
| 1 | 发送消息（Enter/点击发送） (web-send-message) | kokoro-web | — | tests/interfaces/session-stream/session-shell.test.tsx（发送入log/空白拦截/4000可发/4001拦截 | — | ✅ covered |
| 2 | 停止生成 (web-stop-reply) | kokoro-web | — | session-shell.test.tsx [stop]×6（close恰1次/null句柄/同步settle/气泡不擦除/控件互斥）+ simulator. | — | 🟡 partial |
| 3 | 失败重试 (web-retry-failed) | kokoro-web | — | session-shell.test.tsx [重试]×3（复用同句/气泡不重复/连点只一次）+ [conversation]失败alert；reducer.t | — | ✅ covered |
| 4 | 双发防抖（同步在途守卫） (web-double-submit-guard) | kokoro-web | — | session-shell.test.tsx「两次同步Enter仅发起一次」「连点重试只发起一次」（显式针对isStreaming异步读旧值） | — | ✅ covered |
| 5 | IME输入（合成期Enter不发送） (web-ime-composition) | kokoro-web | — | session-shell.test.tsx IME合成期Enter不发送+合成结束正常发送恰1次 | — | 🟡 partial |
| 6 | Composer放大编辑面板 (web-composer-expand) | kokoro-web | — | session-shell.test.tsx 放大dialog与内联镜像同一草稿、Esc收起内容保留 | — | 🟡 partial |
| 7 | 输入长度上限（双重把关） (web-input-max-length) | kokoro-web | — | session-shell.test.tsx 恰4000可发/4001发起前拦截草稿留存/textarea maxLength=4000与守卫同上限 | — | ✅ covered |
| 8 | 输入框自适应高度 (web-composer-autoresize) | kokoro-web | — | session-shell.test.tsx jsdom scrollHeight=0不抛错且height被赋值（仅退化路径，真实贴合行为jsdom不可测） | — | 🟡 partial |
| 9 | 新建对话 (web-new-chat) | kokoro-web | tests/application/conversation-store.test.ts addConversation前置并激活 | session-shell.test.tsx [新对话]×2（hero回归/落盘messages=[]/在途流close恰1次防串流） | — | ✅ covered |
| 10 | 多对话切换 (web-switch-conversation) | kokoro-web | conversation-store.test.ts selectConversation未知id为no-op/模式按会话独立/sortedConversati | session-shell.test.tsx [sessions]两会话切换各自消息互不串 | — | 🟡 partial |
| 11 | 删除对话 (web-delete-conversation) | kokoro-web | conversation-store.test.ts removeConversation重激活剩余首个/删最后自动新空会话 | session-shell.test.tsx 删会话/删唯一会话回空首屏旧标题消失 | — | ✅ covered |
| 12 | 会话自动标题 (web-auto-title) | kokoro-web | conversation-store.test.ts 首条用户消息为题/超长截断≤25含…/空会话「新对话」 | — | — | 🟡 partial |
| 13 | 侧栏折叠与拖拽改宽 (web-rail-collapse-resize) | kokoro-web | — | — | — | 🔴 gap |
| 14 | Fast/Thinking模式选择与锁定 (web-mode-select-lock) | kokoro-web | conversation-store.test.ts 默认fast/首条消息后锁定/按会话独立/旧落盘补默认 | session-shell.test.tsx [mode lock]×3（锁定只读态/新对话恢复/thinking透传startReply）+ transpor | — | ✅ covered |
| 15 | Todo计划条 (web-todo-bar) | kokoro-web | tests/interfaces/session-stream/todo-bar.test.tsx ×3（空DOM/三态+计数/折叠展开） | reducer.test.ts todo整表替换+新用户轮清空；session-shell.test.tsx todo钉输入框上方（log外） | sse-loopback-gate.sh 断言2含todo.updated（链路在场性） | ✅ covered |
| 16 | 过程块折叠/展开 (web-process-disclosure) | kokoro-web | tests/interfaces/session-stream/thread/segment-process.test.tsx ×4（live默认开/落定自动收 | session-shell.test.tsx Fast落定摘要「处理过程」 | — | ✅ covered |
| 17 | 页面刷新中断恢复（reattach续传） (web-refresh-reattach) | kokoro-web | — | session-shell.test.tsx [reattach]×3（带pendingInput挂载即续传补完/「重连中…」锚点区分/无pendingInpu | — | 🟡 partial |
| 18 | SSE瞬断自动重连（幂等去重） (web-sse-transient-reconnect) | kokoro-web | — | transport.test.ts onerror调onError一次且流保持打开；reducer.test.ts eventId去重不二次累积/seq有序插入 | — | ✅ covered |
| 19 | 后端缺席本地预览降级 (web-preview-fallback) | kokoro-web | — | simulator.test.ts ×10（确定性/fast与thinking事件集/CJK与latin分块/onSettled恰1次/close防泄漏）；但r | — | 🟡 partial |
| 20 | localStorage持久化与脏数据降级 (web-localstorage-persistence) | kokoro-web | tests/application/session-stream/state-schema.test.ts ×4（step判别联合/未知kind/缺判别/分支s | session-shell.test.tsx [持久化]×4（恢复/损坏JSON降级/schema非法降级/发送即落盘）+ conversation-store | — | ✅ covered |
| 21 | 滚动吸附跟随与回到最新 (web-scroll-follow) | kokoro-web | — | session-shell.test.tsx [滚动]×4（上滑不拽视图+浮按钮/贴底跟随/点按钮滚底自隐/发送滚底）+ reducer.test.ts com | — | ✅ covered |
| 22 | Markdown渲染与XSS防线 (web-markdown-rendering) | kokoro-web | — | session-shell.test.tsx [markdown]×3（富元素/用户消息纯文本不解析记号/<img onerror>不渲染真实元素） | — | ✅ covered |
| 23 | 多段segment交错渲染 (web-segment-interleaving) | kokoro-web | tests/interfaces/session-stream/thread/assistant-turn.test.tsx ×10（caret唯一性/单头像多 | reducer.test.ts按seq交错APPEND/buildThreadItems归并/仅过程轮不塌空 + session-shell.test.tsx  | — | ✅ covered |
| 24 | 工具调用行展示 (web-tool-call-display) | kokoro-web | tests/interfaces/session-stream/thread/tool-call-row.test.tsx ×6（running/done/er | reducer.test.ts invoked→returned就地翻done不重排 | — | ✅ covered |
| 25 | 子智能体行展示与结论流式 (web-subagent-display) | kokoro-web | tests/interfaces/session-stream/thread/subagent-row.test.tsx ×9（三source标签/runnin | reducer.test.ts started→finished翻done+text-completed写output + transport.test.ts三 | — | ✅ covered |
| 26 | SSR水合首帧与历史恢复 (web-hydration-first-frame) | kokoro-web | — | session-shell.test.tsx 空首屏最小元素集/恢复历史隐藏hero/判脏落hero（jsdom仅客户端渲染，无SSR双帧一致性断言） | — | 🟡 partial |
| 27 | SSE载荷严格解析与畸形隔离 (web-transport-strict-parse) | kokoro-web | — | tests/infrastructure/transport-event.test.ts ×6（映射对齐/seq透传/cancelled容忍/run.creat | contract/verify.py 检查4/5（schema字段集与render视图契约锁定） | ✅ covered |
| 28 | 传输标签与模式提示 (web-presentation-status) | kokoro-web | — | session-shell.test.tsx 仅间接触及（失败模式化文案/Fast落定摘要），mode-presentation六态×两模式文案矩阵无直接测试 | — | 🟡 partial |
| 29 | Composer弹出菜单交互 (web-composer-menus) | kokoro-web | — | session-shell.test.tsx 经模式菜单选Thinking（间接走通menuitemradio选中收起） | — | 🟡 partial |
| 30 | 占位控件（上传/语音/搜索） (web-placeholder-controls) | kokoro-web | — | session-shell.test.tsx composer五控件可见性（附加内容/语音输入按钮在场）；占位无业务行为可断言，属已知缺口非bug | — | 🟡 partial |
| 31 | POST开run（异步派发到请求流） (http-start-run) | kokoro-session | tests/run-request.test.ts ×6（strict拒多余键/缺input/枚举外style） | tests/http.test.ts POST 200含run_前缀runId + tests/start-run.test.ts conversation_i | scripts/sse-loopback-gate.sh 断言1（真实链路POST必回run_id） | 🟡 partial |
| 32 | SSE全量回放（历史+实时） (sse-full-replay) | kokoro-session | — | tests/http.test.ts SSE回放归一化事件/content-type/id-event-data三行结构/非空快照续订实时追加（回归测试）/id | sse-loopback-gate.sh 断言2（5个event kind全集逐个grep） | ✅ covered |
| 33 | Last-Event-ID增量续订 (sse-resume-last-event-id) | kokoro-session | tests/resume-cursor.test.ts格式判定 + tests/stream-port.memory.test.ts subscribe(fro | tests/http.test.ts transport cursor增量续传跳过已交付（session.created不重发） + stream-port.r | — | ✅ covered |
| 34 | resumeCursor守卫与畸形值fallback (resume-cursor-guard) | kokoro-session | tests/resume-cursor.test.ts ×5（memory游标/redis id/域cursor拒/数组拒/undefined与空串拒） | tests/http.test.ts 非法cursor忽略退全量绝不静默空流 | — | ✅ covered |
| 35 | 后台调度：消费run请求流并派relay (relay-dispatch-loop) | kokoro-session | — | —（start-run.test.ts只测relayRun，main.ts的dispatchRelays循环零直接测试） | sse-loopback-gate.sh隐式覆盖happy path（真实服务调度成功才有SSE输出） | 🔴 gap |
| 36 | 单run中继：归一化→append→终态收束 (relay-run-terminal-close) | kokoro-session | — | tests/start-run.test.ts relayRun归一化顺序/在run.completed处停止+重复(run_id,seq)幂等/run.fai | sse-loopback-gate.sh主链路（终态落流才能通过） | ✅ covered |
| 37 | 13种agent kind归一化为AGUI信封 (normalize-13-kinds) | kokoro-session | tests/normalize.test.ts ×21（全kind映射/信封字段齐全/seq透传/schema崩溃×5）+ tests/agent-event. | — | contract/verify.py检查1-3（三仓kind集与payload字段名集锁定）+ gate 5 kind实链在场 | ✅ covered |
| 38 | (run_id,seq)去重幂等 (seq-dedup) | kokoro-session | tests/normalize.test.ts 同(run_id,seq)二次投喂输出空数组 | tests/start-run.test.ts relayRun重复run.started只产出一次 | —（进程内幂等已钉死；重启/多副本失效见gap） | ✅ covered |
| 39 | 合成session.created+run.created (synthetic-session-run-created) | kokoro-session | tests/normalize.test.ts 首条合成对共享seq且event_id互异/第二次run.started不重发session.created | tests/start-run.test.ts replay顺序首两条为合成对 | sse-loopback-gate.sh断言4显式排除合成对再验严格递增 | ✅ covered |
| 40 | replay流写入与本地镜像 (replay-stream-write) | kokoro-session | — | tests/start-run.test.ts经relayRun间接验证replay流内容与顺序 | gate主链经replay流出SSE | 🟡 partial |
| 41 | StreamPort双后端差异 (backend-memory-vs-redis) | kokoro-session | tests/stream-port.memory.test.ts ×7（保序/cursor互异/fromCursor排除/实时/流隔离/cursorWidth） | tests/stream-port.redis.test.ts ×3（真实Redis，不可达skip） | contract/verify.py检查6（CURSOR_WIDTH/REDIS_FIELD/BLOCK_MS双端常量锁定）+ gate redis实链 | ✅ covered |
| 42 | 多订阅者/多副本fan-out广播 (multi-replica-fanout) | kokoro-session | — | —（无多订阅者广播断言，更无多副本重复relay/event_id分歧断言） | — | 🔴 gap |
| 43 | CORS放通与OPTIONS预检 (cors-preflight) | kokoro-session | — | — | — | 🔴 gap |
| 44 | 脏事件严格拒收（无skip-and-continue） (strict-reject-no-skip) | kokoro-session | tests/normalize.test.ts 仅断言ingest对畸形/未知kind抛ZodError | —（relay级行为契约——脏事件后终态丢失/run悬挂——零断言） | — | 🟡 partial |
| 45 | HTTP路由兜底与统一错误处理 (http-routing-error-envelope) | kokoro-session | — | tests/http.test.ts 仅未知路由404；缺url 400/405落404/500信封/SSE中途异常静默断流均无断言 | — | 🟡 partial |
| 46 | Worker主循环：收run请求发布事件流 (worker-main-loop) | kokoro-agent | — | tests/test_worker.py ×5（畸形请求不崩循环/重复run_id幂等/execution_style传参，经run_once共享_handle | sse-loopback-gate.sh真实worker常驻消费 | 🟡 partial |
| 47 | run_once批量排空模式 (worker-run-once) | kokoro-agent | — | tests/test_worker.py run_once端到端（MemoryStreamPort+真实DeepAgents+fake model注入）+ pr | — | ✅ covered |
| 48 | run生命周期与seq单调分配 (run-lifecycle) | kokoro-agent | tests/test_run_agent.py 空流started→completed seq=[1,2]/seq从1严格递增无重复/异常→run.failed | test_worker.py首尾run.started/run.completed且seq连续无空洞 | sse-loopback-gate.sh断言3/4（seq非递减+排除合成对严格递增） | ✅ covered |
| 49 | token流式：text.delta累积→completed (text-stream-flow) | kokoro-agent | tests/test_run_agent.py 每块独立delta非累积/末尾恰一条全文completed/同segment_id/空块静默/tool_call | — | gate断言2含message.completed | ✅ covered |
| 50 | 非流式fallback：delta+completed成对 (text-nonstream-flow) | kokoro-agent | tests/test_run_agent.py text.delta与text.completed同ref同text（成对形态）+ tests/test_mod | — | — | ✅ covered |
| 51 | 推理流：thinking.delta产出 (thinking-delta-flow) | kokoro-agent | tests/test_run_agent.py stream路径与end路径reasoning_content均先thinking.delta再text | — | — | 🟡 partial |
| 52 | 通用工具tool.invoked/returned (tool-event-flow) | kokoro-agent | tests/test_run_agent.py start/end映射/run_id作tool_id配对/result提取AIMessage文本/工具与后续文本 | — | — | ✅ covered |
| 53 | write_todos→todo.updated映射 (todo-flow) | kokoro-agent | tests/test_run_agent.py on_tool_start映射todo.updated携带列表/on_tool_end静默不重发 | test_worker.py事件流中todo.updated在场 | gate断言2 todo.updated实链在场 | ✅ covered |
| 54 | task工具子代理started/finished与source (subagent-task-flow) | kokoro-agent | tests/test_run_agent.py task映射started/finished+source=built-in与config-custom + t | — | — | ✅ covered |
| 55 | runtime-custom子代理即席注册执行 (subagent-runtime-flow) | kokoro-agent | tests/test_run_agent.py agent工具映射source=runtime-custom + tests/test_runtime_suba | —（agent_runtime协程执行路径：同名复用/嵌套ainvoke/空输出回''/sync抛RuntimeError均无断言） | — | 🟡 partial |
| 56 | 子代理文本路由delta/completed (subagent-text-routing) | kokoro-agent | tests/test_run_agent.py 嵌套流路由（lc_agent_name命中→subagent.text.*，主线只剩最终总结）流式逐块delta | — | — | ✅ covered |
| 57 | _Segmenter分段：tool→text→tool不塌缩 (segmenter-flow) | kokoro-agent | tests/test_run_agent.py 同段共享segment_id/落定后新段seg_0002/工具1→文本1→工具2→文本2两段不塌缩/流式段完成新 | — | — | ✅ covered |
| 58 | 模型解析：execution_style+provider分发 (model-resolution-flow) | kokoro-agent | tests/test_model.py ×5（默认构造/自定义spec/thinking设reasoning_effort=high/fake flag/非法p | test_worker.py monkeypatch验证style传参 | — | 🟡 partial |
| 59 | LOCAL_FAKE_MODEL离线确定性路径 (local-fake-model-flow) | kokoro-agent | tests/test_model.py fake flag返回LocalFakeChatModel | tests/test_worker.py 经flag走make_chat_model完整事件流且text.completed含『本地预览』 | sse-loopback-gate.sh全链以fake model跑真实DeepAgents循环 | ✅ covered |
| 60 | config-custom子代理env加载 (config-custom-subagent-loading) | kokoro-agent | tests/test_subagents.py ×15（坏JSON/未知字段/非字符串/缺字段/空白/strip/撞名抛/materialize合并） | — | — | ✅ covered |
| 61 | StreamPort传输层memory vs redis契约 (stream-port-transport) | kokoro-agent | tests/test_stream_port_memory.py ×6（保序/cursor唯一单调/from_cursor跳过/阻塞唤醒非忙等/cursor_w | tests/test_stream_port_redis.py ×3（真实Redis不可达skip） | contract/verify.py检查6双端常量 + gate redis实链 | ✅ covered |
| 62 | 异常→run.failed边界（及边界外区域） (failure-run-failed-boundary) | kokoro-agent | tests/test_run_agent.py 流内异常→run.failed含error_kind/message且绝不发run.completed | —（边界外三区：make_chat_model/_build_agent/publish失败崩worker无终态，零断言；120s超时路径无直接断言） | — | 🟡 partial |

## 3. kokoro-web 交互流程用例(30)

### ✅ 发送消息（Enter/点击发送） `web-send-message`

**触发**:用户在 composer 输入文本后按 Enter（非 Shift、非 IME）或点击发送键提交表单

**主路径**:
1. handleKeyDown 拦截 Enter 或 handleSubmit preventDefault 后调 submit(draft)
1. submit 对 content trim 并通过守卫（非空/非流式/非在途/未超长），置 requestInFlightRef=true
1. 若 store 为 null（首次交互）即时 addConversation 创建首个会话并承接 pendingMode
1. appendUserMessage 以本地 id 注入用户消息（runId=自身 id，清空 todos，runStatus 复位 idle）
1. withActiveThread 写回活跃会话并刷新标题/updatedAt；清空 draft、重置 textarea 高度并 focus
1. beginReply：关旧句柄、setIsStreaming(true)、scrollToLatest、调 startReply（sessionId=会话 id，executionStyle=mode）
1. startSessionReply POST /sessions/{id}/runs 成功后开 SSE，事件经严格解析折进 reducer，onState 持续写回 liveStore
1. onLive 标记 pendingInput（可重连）；onSettled 复位 in-flight/isStreaming、清 pendingInput、focus composer

**边界用例**:
- [ ] 纯空白输入 trim 后为空直接 return
- [ ] 恰好 4000 字符可发送，4001 被拦截
- [ ] Shift+Enter 只换行不发送
- [ ] 流式中（isStreaming）submit 被守卫拦截
- [ ] 首次交互（无 store）与已有会话两条创建路径
- [ ] 时间戳只在用户动作里取 Date.now()，不在 render（防 SSR 注水抖动）

**失败路径用例**:
- [ ] POST 失败/网络不可用 → 静默降级本地预览模拟（见 web-preview-fallback）
- [ ] run.failed 事件 → runStatus=failed，浮出重试条（见 web-retry-failed）
- [ ] 组件卸载时 effect cleanup 关闭在途句柄

**现有覆盖**:集成:tests/interfaces/session-stream/session-shell.test.tsx（发送入log/空白拦截/4000可发/4001拦截/双发守卫/焦点回归）+ tests/application/session-stream/transport.test.ts（POST+SSE折叠全链、executionStyle透传）

**代码定位**:`kokoro-web/src/interfaces/session-stream/hooks/use-conversation.ts:279-319` · `kokoro-web/src/interfaces/session-stream/hooks/use-conversation.ts:236-277` · `kokoro-web/src/interfaces/session-stream/hooks/use-conversation.ts:434-442` · `kokoro-web/src/interfaces/session-stream/components/composer/composer.tsx:179-194` · `kokoro-web/src/application/session-stream/reply.ts:30-79` · `kokoro-web/src/application/session-stream/transport.ts:148-179`

### 🟡 停止生成 `web-stop-reply`

**触发**:流式中发送键变为停止键，用户点击「停止生成」

**主路径**:
1. Composer 在 isStreaming 时渲染 stop 按钮（替换 submit 键）
1. stopReply 关闭 replyHandle（live：解绑监听+close EventSource；preview：cancelled=true 并 clearTimeout）
1. 复位 requestInFlightRef/isStreaming/isReconnecting，transportState 回 idle
1. setActivePending(undefined) 清除在途标记——刷新后不再自动重连这一轮

**边界用例**:
- [ ] 停止后线程保留半截内容，runStatus 维持上一个值（非 failed，不出重试条）
- [ ] POST 仍在 pending 时 stop：reply.ts 的 closed=true 保证之后既不接管 live 也不降级 preview
- [ ] 停止后立即重发：beginReply 内先 close 旧句柄，双保险

**失败路径用例**:
- [ ] live 链路 stop 只关前端 SSE，后端 run 继续跑完；因 pendingInput 已清，该轮剩余内容永久丢失

**现有覆盖**:集成:session-shell.test.tsx [stop]×6（close恰1次/null句柄/同步settle/气泡不擦除/控件互斥）+ simulator.test.ts handle.close防泄漏

**代码定位**:`kokoro-web/src/interfaces/session-stream/hooks/use-conversation.ts:345-354` · `kokoro-web/src/interfaces/session-stream/components/composer/composer.tsx:261-279` · `kokoro-web/src/application/session-stream/simulator.ts:257-265` · `kokoro-web/src/application/session-stream/transport.ts:110-115` · `kokoro-web/src/application/session-stream/reply.ts:60-78`

### ✅ 失败重试 `web-retry-failed`

**触发**:run.failed 事件落定后线程底部出现 role=alert 错误条，用户点「重试」

**主路径**:
1. reducer 收到 run-failed → runStatus='failed'
1. hasFailed = runStatus==='failed' && !isStreaming，ConversationThread 渲染错误条+重试按钮
1. retry() 守卫（非流式/非在途/lastInputRef 非空/store 存在）后置 in-flight
1. resetThread 把 runStatus 复位 idle（不重复注入用户消息）
1. beginReply 用 lastInputRef.current 重发同一句，走与 submit 完全相同的链路

**边界用例**:
- [ ] lastInputRef 在 submit/retry/reattach 三处维护，用户无需重新打字
- [ ] 重试沿用同一会话 sessionId，replay 流不混淆
- [ ] presentation 在 failed 态显示「这轮未完成」标签（failed 优先于 transportState）

**失败路径用例**:
- [ ] 再次失败回到 failed 态可无限重试
- [ ] 刷新后 lastInputRef 丢失（仅内存），但 hasFailed 仍渲染——点重试守卫 !lastInputRef 直接 return，按钮看似无响应（潜在 UX 缺口）

**现有覆盖**:集成:session-shell.test.tsx [重试]×3（复用同句/气泡不重复/连点只一次）+ [conversation]失败alert；reducer.test.ts run.failed置failed+终态去重

**代码定位**:`kokoro-web/src/interfaces/session-stream/hooks/use-conversation.ts:321-338` · `kokoro-web/src/interfaces/session-stream/hooks/use-conversation.ts:224` · `kokoro-web/src/interfaces/session-stream/components/thread/conversation-thread.tsx:89-100` · `kokoro-web/src/application/session-stream/reducer.ts:438-440`

### ✅ 双发防抖（同步在途守卫） `web-double-submit-guard`

**触发**:用户快速连按 Enter/连点发送，或 Enter 与表单 submit 同帧触发

**主路径**:
1. submit 第一道读 isStreaming（异步 UI 态），第二道读 requestInFlightRef（同步 ref）
1. 首次 submit 同步置 requestInFlightRef=true，同帧第二次 submit 读到 true 直接 return
1. onSettled / stopReply / startNewChat / selectConversation / deleteConversation(活跃项) / reattach settle 处复位 ref

**边界用例**:
- [ ] isStreaming 是 setState 异步态，两次同步 submit 都读到旧值——ref 是真正的防线
- [ ] retry 与 submit 共用同一 ref，互斥

**失败路径用例**:
- [ ] 若 onSettled 因传输 bug 永不回调，ref 卡 true 锁死发送——可通过 stop/新建/切换会话解锁

**现有覆盖**:集成:session-shell.test.tsx「两次同步Enter仅发起一次」「连点重试只发起一次」（显式针对isStreaming异步读旧值）

**代码定位**:`kokoro-web/src/interfaces/session-stream/hooks/use-conversation.ts:135-137` · `kokoro-web/src/interfaces/session-stream/hooks/use-conversation.ts:283-292` · `kokoro-web/src/interfaces/session-stream/hooks/use-conversation.ts:266-273`

### 🟡 IME 输入（拼音选词 Enter 不发送） `web-ime-composition`

**触发**:用户用中文/日文输入法在合成期按 Enter 确认候选词

**主路径**:
1. handleKeyDown 检查 event.nativeEvent.isComposing
1. 合成期 Enter 不 preventDefault、不 submit——Enter 只确认候选词
1. 合成结束后的 Enter 正常发送

**边界用例**:
- [ ] 放大编辑面板的 ⌘/Ctrl+Enter 同样检查 isComposing
- [ ] Shift+Enter 与 IME Enter 两条豁免互不干扰

**失败路径用例**:
- [ ] Safari 旧版 compositionend 后立刻 keydown 的 isComposing 兼容性差异（未做 keyCode 229 兜底）

**现有覆盖**:集成:session-shell.test.tsx IME合成期Enter不发送+合成结束正常发送恰1次

**代码定位**:`kokoro-web/src/interfaces/session-stream/hooks/use-conversation.ts:434-440` · `kokoro-web/src/interfaces/session-stream/components/composer/composer.tsx:161-175`

### 🟡 Composer 放大编辑面板 `web-composer-expand`

**触发**:用户点击输入框右上角的「放大编辑」按钮

**主路径**:
1. setExpanded(true)，createPortal 渲染全屏 backdrop+对话面板（role=dialog aria-modal）到 body
1. effect 聚焦大编辑框并 setSelectionRange 把光标移到末尾
1. 面板 textarea 与内联输入共享同一 draft（受控双向同步）
1. 面板内 Enter 换行；⌘/Ctrl+Enter requestSubmit 发送；Esc 或点遮罩空白处或收起键关闭
1. submitFromExpand 复用 onSubmit 后收起面板，closeExpand 把焦点还给内联输入框

**边界用例**:
- [ ] 流式中 expand 入口隐藏（输入框 disabled 时一并不可达）
- [ ] 面板发送键同样受 canSend 约束；maxLength=4000 同样生效
- [ ] 点击面板内部不冒泡关闭（event.target===currentTarget 判定）

**失败路径用例**:
- [ ] 面板打开期间若流式开始（如 reattach effect 触发），expanded 不会自动关闭，但内联输入已 disabled——状态轻微不一致

**现有覆盖**:集成:session-shell.test.tsx 放大dialog与内联镜像同一草稿、Esc收起内容保留

**代码定位**:`kokoro-web/src/interfaces/session-stream/components/composer/composer.tsx:130-175` · `kokoro-web/src/interfaces/session-stream/components/composer/composer.tsx:196-206` · `kokoro-web/src/interfaces/session-stream/components/composer/composer.tsx:291-352`

### ✅ 输入长度上限（双重把关） `web-input-max-length`

**触发**:用户输入/粘贴超长文本或程序化注入超长 draft

**主路径**:
1. textarea maxLength={MAX_INPUT_LENGTH}(4000) 在浏览器层硬截断键入与粘贴
1. submit 内第二道：content.length > MAX_INPUT_LENGTH 时直接 return 不发起网络/模拟
1. 放大编辑面板的 textarea 同样挂 maxLength

**边界用例**:
- [ ] 恰好 4000 可发；4001 被拦
- [ ] trim 后才比较长度（前后空白不计入有效内容但计入 textarea 截断）
- [ ] 测试可绕过 DOM 直接 setDraft 注入超长——第二道守卫兜底

**失败路径用例**:
- [ ] 超限被静默拦截，无任何用户可见提示（无计数器/无错误文案）

**现有覆盖**:集成:session-shell.test.tsx 恰4000可发/4001发起前拦截草稿留存/textarea maxLength=4000与守卫同上限

**代码定位**:`kokoro-web/src/interfaces/session-stream/components/composer/composer-input.ts:1-8` · `kokoro-web/src/interfaces/session-stream/components/composer/composer.tsx:186` · `kokoro-web/src/interfaces/session-stream/components/composer/composer.tsx:327` · `kokoro-web/src/interfaces/session-stream/hooks/use-conversation.ts:283-289`

### 🟡 输入框自适应高度 `web-composer-autoresize`

**触发**:用户在内联输入框键入/删除多行文本

**主路径**:
1. onChange 里调 resizeComposer：height 先归零 'auto' 再贴合 scrollHeight
1. CSS max-height 提供硬顶，超出后内部滚动
1. submit 成功后把 height 重置为 'auto' 收回单行

**边界用例**:
- [ ] jsdom 下 scrollHeight 恒 0 不抛错（测试兼容）
- [ ] 放大编辑面板不走 autoresize（固定大区域）

**现有覆盖**:集成:session-shell.test.tsx jsdom scrollHeight=0不抛错且height被赋值（仅退化路径，真实贴合行为jsdom不可测）

**代码定位**:`kokoro-web/src/interfaces/session-stream/components/composer/composer-input.ts:4-8` · `kokoro-web/src/interfaces/session-stream/components/composer/composer.tsx:188-191` · `kokoro-web/src/interfaces/session-stream/hooks/use-conversation.ts:310-314`

### ✅ 新建对话 `web-new-chat`

**触发**:用户点击 rail 上的「新对话」按钮

**主路径**:
1. startNewChat 先 close 在途回复句柄，复位 requestInFlightRef 与 reattachedRef
1. createLocalId('conv') 生成新会话 id，addConversation 把空会话置于列表最前并设为活跃
1. 清空 draft、isStreaming、isReconnecting，transportState 回 idle，focus composer
1. liveStore 变更触发落盘 effect 写 localStorage

**边界用例**:
- [ ] 流式中点新建会中止旧流（旧事件不会折进新会话）
- [ ] 新会话标题为「新对话」，模式默认 fast——注意 startNewChat 不传 pendingMode（与首条消息创建路径不同）
- [ ] store 为 null 时基于 persistedStore 兜底创建

**失败路径用例**:
- [ ] 无（纯本地操作）；旧会话若有 pendingInput，因 reattachedRef 重置，切回时仍可续传

**现有覆盖**:单元:tests/application/conversation-store.test.ts addConversation前置并激活;集成:session-shell.test.tsx [新对话]×2（hero回归/落盘messages=[]/在途流close恰1次防串流）

**代码定位**:`kokoro-web/src/interfaces/session-stream/hooks/use-conversation.ts:356-370` · `kokoro-web/src/application/conversation-store.ts:101-112` · `kokoro-web/src/interfaces/session-stream/components/session-rail.tsx:47-54` · `kokoro-web/src/application/session-stream/simulator.ts:17-27`

### 🟡 多对话切换 `web-switch-conversation`

**触发**:用户点击 rail 历史会话列表中的某一项

**主路径**:
1. selectConversation 先 close 在途句柄并复位 in-flight，防旧流折进新会话
1. reattachedRef 置 null：允许切到（含切回）有在途 run 的会话时重新续传
1. selectConversationOp 纯函数改 activeId（id 不存在则原样返回）
1. 清空 draft 与全部瞬态（isStreaming/isReconnecting/transportState），focus composer
1. 若目标会话有 pendingInput，重连 effect 随 pendingConvId 变化自动触发 reattach

**边界用例**:
- [ ] 切到不存在的 id：store 不变（防御）
- [ ] 列表按 updatedAt 倒序渲染（sortedConversations），active 项高亮 aria-current
- [ ] 切换会丢弃当前未发送的 draft（不随会话保存）

**失败路径用例**:
- [ ] 流式中切走：本轮 live 流被 close；若已标 pendingInput，切回时通过 reattach 续传，否则丢失

**现有覆盖**:单元:conversation-store.test.ts selectConversation未知id为no-op/模式按会话独立/sortedConversations降序;集成:session-shell.test.tsx [sessions]两会话切换各自消息互不串

**缺口(rank 9)**:integration 级断言：流式中切换会话时旧流句柄被 close 且旧流事件不折进新会话；切回带 pendingInput 会话可再续传

**代码定位**:`kokoro-web/src/interfaces/session-stream/hooks/use-conversation.ts:372-391` · `kokoro-web/src/application/conversation-store.ts:150-156` · `kokoro-web/src/application/conversation-store.ts:175-179` · `kokoro-web/src/interfaces/session-stream/components/session-rail.tsx:64-95`

### ✅ 删除对话 `web-delete-conversation`

**触发**:用户点击 rail 会话项右侧的 × 按钮

**主路径**:
1. deleteConversation 判断被删 id 是否活跃项：是则先 close 在途句柄并清瞬态
1. removeConversation 过滤该会话；删空则用 fallbackId 自动起一个新的空会话
1. 删的是活跃项时激活 remaining[0]（数组序，非时间序）
1. liveStore 变更落盘

**边界用例**:
- [ ] 删除非活跃项不打断当前流式
- [ ] 删除最后一个会话 → 自动新空会话（永远有活跃会话）
- [ ] remaining[0] 是插入序首个而非 updatedAt 最新——与 rail 展示序可能不一致

**失败路径用例**:
- [ ] 无确认对话框，误删不可恢复（localStorage 即时被覆盖）

**现有覆盖**:单元:conversation-store.test.ts removeConversation重激活剩余首个/删最后自动新空会话;集成:session-shell.test.tsx 删会话/删唯一会话回空首屏旧标题消失

**代码定位**:`kokoro-web/src/interfaces/session-stream/hooks/use-conversation.ts:393-414` · `kokoro-web/src/application/conversation-store.ts:159-172` · `kokoro-web/src/interfaces/session-stream/components/session-rail.tsx:84-91`

### 🟡 会话自动标题 `web-auto-title`

**触发**:每次线程更新（withActiveThread）时重算标题

**主路径**:
1. conversationTitle 找首条 role=user 的消息，trim 后作为标题
1. 超过 24 字符 slice(0,24) 加 …；无用户消息时回退「新对话」
1. withActiveThread 在每次写回线程时同步刷新 title 与 updatedAt

**边界用例**:
- [ ] 恰好 24 字不加省略号，25 字截断
- [ ] 全空白首条消息 trim 后为空 → 保持「新对话」（实际不可达，submit 已拦空白）
- [ ] slice 按 UTF-16 码元截断，emoji/代理对可能截半个字符

**现有覆盖**:单元:conversation-store.test.ts 首条用户消息为题/超长截断≤25含…/空会话「新对话」

**代码定位**:`kokoro-web/src/application/conversation-store.ts:34-45` · `kokoro-web/src/application/conversation-store.ts:79-97`

### 🔴 侧栏折叠与拖拽改宽 `web-rail-collapse-resize`

**触发**:用户点击折叠按钮，或在 rail/main 之间的分隔条上按下并拖动

**主路径**:
1. 折叠：setRailCollapsed 翻转，shell 打 data-rail-collapsed，CSS 切换窄列；收起态分隔条不渲染
1. 拖宽：onResizeStart 量取 shell getBoundingClientRect，setIsResizing(true) 关掉列宽过渡
1. pointermove 把 clientX-rect.left 经 clampRail 钳制（RAIL_MIN=200，RAIL_MAX=420，MAIN_MIN=360）后 setWidth
1. 拖拽期间 body 锁 col-resize 光标并禁选；pointerup 解绑监听并恢复
1. 宽度经 CSS 变量 --kk-rail-width 应用到布局

**边界用例**:
- [ ] 容器极窄使 max<min 时以 RAIL_MIN 兜底，绝不返回负数/反转区间
- [ ] 折叠态不可拖（分隔条不存在）
- [ ] 宽度与折叠态都不持久化，刷新回默认 248px/展开

**失败路径用例**:
- [ ] pointerup 发生在窗口外仍由 window 级监听捕获并清理

**缺口(rank 10)**:全层级零测试：折叠切换、clampRail 钳制边界、拖拽监听清理

**代码定位**:`kokoro-web/src/interfaces/session-stream/session-shell.tsx:34-38` · `kokoro-web/src/interfaces/session-stream/session-shell.tsx:93-95` · `kokoro-web/src/interfaces/session-stream/session-shell.tsx:107-116` · `kokoro-web/src/interfaces/session-stream/hooks/use-rail-resize.ts:9-57` · `kokoro-web/src/interfaces/session-stream/components/session-rail.tsx:36-44`

### ✅ Fast/Thinking 模式选择与锁定 `web-mode-select-lock`

**触发**:用户在 composer 的模式下拉菜单中选择 Fast 或 Thinking

**主路径**:
1. ComposerMenu 单选（menuitemradio+勾选）触发 onModeChange
1. setMode：无会话时落 pendingMode（空首屏选好），有会话时 setActiveMode 写入活跃会话
1. 首条消息创建首个会话时 addConversation(null,id,now,pendingMode) 承接空首屏选的模式
1. 开聊后 isActiveModeLocked（messages.length>0）→ modeLocked，菜单换成 disabled 锁定按钮（带 LockIcon 与 title 提示）
1. 发起回复时 executionStyle=mode 作为 POST 的 execution_style query 传给 kokoro-session；预览模拟也按模式产事件（thinking 前置思考/工具/todo）
1. presentation 按模式给出差异化 transportLabel/modeHint 文案

**边界用例**:
- [ ] 锁定后 setMode 直接 return（防御，即使 UI 已 disabled）
- [ ] 每会话独立持模式；旧版落盘无 mode 字段 zod default 补 fast
- [ ] startNewChat 创建的新会话固定 fast，不承接当前 pendingMode（与首条消息路径不对称）
- [ ] 无会话时 activeMode 回退 fast

**现有覆盖**:单元:conversation-store.test.ts 默认fast/首条消息后锁定/按会话独立/旧落盘补默认;集成:session-shell.test.tsx [mode lock]×3（锁定只读态/新对话恢复/thinking透传startReply）+ transport.test.ts executionStyle进URL + simulator.test.ts fast/thinking事件差异

**代码定位**:`kokoro-web/src/interfaces/session-stream/hooks/use-conversation.ts:131` · `kokoro-web/src/interfaces/session-stream/hooks/use-conversation.ts:225-233` · `kokoro-web/src/interfaces/session-stream/hooks/use-conversation.ts:416-432` · `kokoro-web/src/application/conversation-store.ts:115-135` · `kokoro-web/src/interfaces/session-stream/components/composer/composer.tsx:222-251` · `kokoro-web/src/application/session-stream/transport.ts:154`

### ✅ Todo 计划条（钉在输入框上方） `web-todo-bar`

**触发**:todo.updated 事件到达后 thread.todos 非空

**主路径**:
1. reducer 收 todo-updated 整表替换 state.todos（每次携带完整清单）
1. TodoBar 渲染「计划 doneCount/total」标题 + 三态图标列表（completed/in_progress/pending）
1. 用户点 toggle 折叠/展开列表（aria-expanded 同步）

**边界用例**:
- [ ] todos 为空不渲染（不留空壳）；水合前（mounted=false）不渲染
- [ ] appendUserMessage 在新一轮提交时清空 todos
- [ ] 折叠态仅组件内存，刷新/切会话重置为展开
- [ ] 列表 key 用 index+content，重复内容项可接受

**现有覆盖**:单元:tests/interfaces/session-stream/todo-bar.test.tsx ×3（空DOM/三态+计数/折叠展开）;集成:reducer.test.ts todo整表替换+新用户轮清空；session-shell.test.tsx todo钉输入框上方（log外）;e2e:sse-loopback-gate.sh 断言2含todo.updated（链路在场性）

**代码定位**:`kokoro-web/src/interfaces/session-stream/components/todo-bar.tsx:30-79` · `kokoro-web/src/application/session-stream/reducer.ts:371-374` · `kokoro-web/src/application/session-stream/reducer.ts:457` · `kokoro-web/src/interfaces/session-stream/session-shell.tsx:151`

### ✅ 过程块折叠/展开（思考·工具·子智能体披露） `web-process-disclosure`

**触发**:段内有 thinking/tools/subagents 活动时渲染 <details> 过程块；用户点 summary 切换

**主路径**:
1. SegmentProcess 以 open = manualOpen ?? live 受控：尾段流式默认展开实时看
1. 落定（live=false）自动收起为一行摘要「思考过程 · N 个工具 · M 个子智能体」（零维度省略）
1. 用户手动 toggle 后 manualOpen 接管，不再随 live 翻转对抗用户
1. onToggle 仅当 details.open ≠ 本帧受控 open 时记为手动（区分 React 受控下发与用户操作）
1. live 时 summary 显示「思考中…」+ 脉冲动画

**边界用例**:
- [ ] 全空过程（无思考/工具/子智能体）不渲染
- [ ] fast 模式 verb 改「处理」，避免「直接作答」与「思考」自相矛盾
- [ ] 不靠 remount/翻 key，保留 details 自身滚动状态

**现有覆盖**:单元:tests/interfaces/session-stream/thread/segment-process.test.tsx ×4（live默认开/落定自动收起/手动意图两向保持）;集成:session-shell.test.tsx Fast落定摘要「处理过程」

**代码定位**:`kokoro-web/src/interfaces/session-stream/components/thread/segment-process.tsx:34-106`

### 🟡 页面刷新中断恢复（reattach 续传在途 run） `web-refresh-reattach`

**触发**:live run 在途时（pendingInput 已落盘）用户刷新/关闭后重新打开页面

**主路径**:
1. POST 成功时 onLive 回调 setActivePending(content)，pendingInput 随会话 store 落盘
1. 刷新后 usePersistentStore 恢复种子，pendingConvId 检出活跃会话的在途标记
1. 重连 effect（每 pending 会话只触发一次，reattachedRef 守卫）设 isStreaming+isReconnecting+transportState=live
1. thread 在途轮渲染「重连中…」锚点（data-anchor=reconnecting），区别于普通「正在思考…」
1. reattach 不发新 POST，直接重订阅 /sessions/{id}/stream；服务端 replay 从流首回放
1. 已收过的事件按 eventId 被 reducer 去重，剩余事件续上；首批事件一到即清 isReconnecting
1. run.completed/run.failed 到达 → settle：清 isStreaming/in-flight/pendingInput

**边界用例**:
- [ ] REATTACH_TIMEOUT_MS=90s 无终态则 close+settle，避免永久卡 streaming
- [ ] preview 降级链路不触发 onLive，绝不把本地模拟误标为可重连
- [ ] 手动 stop 清 pendingInput，刷新后不再自动重连
- [ ] 切走再切回该会话：reattachedRef 在 select/new chat 时重置，可再次续传
- [ ] effect 依赖故意只含 pendingConvId/reattach，防流式增量重跑 effect 误清兜底计时器

**失败路径用例**:
- [ ] 后端已无该 session/已停：SSE 空挂 90s 后放弃续传
- [ ] 兜底超时触发后 runStatus 维持原值（不会标 failed），线程停在半截

**现有覆盖**:集成:session-shell.test.tsx [reattach]×3（带pendingInput挂载即续传补完/「重连中…」锚点区分/无pendingInput不触发）

**缺口(rank 5)**:integration 级断言：90s 兜底超时退出 streaming、手动 stop 清 pendingInput 后不再重连、preview 降级不写 pendingInput

**代码定位**:`kokoro-web/src/interfaces/session-stream/hooks/use-conversation.ts:105-106` · `kokoro-web/src/interfaces/session-stream/hooks/use-conversation.ts:160-213` · `kokoro-web/src/interfaces/session-stream/hooks/use-conversation.ts:259-265` · `kokoro-web/src/application/session-stream/transport.ts:181-194` · `kokoro-web/src/application/conversation-store.ts:138-148` · `kokoro-web/src/interfaces/session-stream/components/thread/assistant-turn.tsx:70-92`

### ✅ SSE 瞬断自动重连（Last-Event-ID + 幂等去重） `web-sse-transient-reconnect`

**触发**:SSE 连接瞬时中断（网络抖动/代理重置）触发 EventSource onerror

**主路径**:
1. onerror 只回调 args.onError（可选），不 close、不撕毁 reducer 状态
1. 浏览器原生 EventSource 自动重连并携带 Last-Event-ID 请求头
1. 服务端按游标续发/replay；重复事件进 applySessionEvent 时被 seenEventIds O(1) 去重
1. message.completed 以全量 content 覆盖累计 delta，半句内容收敛
1. run.completed/run.failed 到达后 close 流并 onSettled

**边界用例**:
- [ ] 乱序事件由 insertOrdered 按 seq 稳定插入（同 seq 追加在既有之后）
- [ ] 重复 message-delta/tool 事件全部幂等
- [ ] EventSource 不存在的环境（SSR/旧浏览器）返回 no-op 句柄

**失败路径用例**:
- [ ] 后端进程彻底死亡：EventSource 无限重试，前端无退避上限——只能靠用户 stop 或 reattach 场景的 90s 兜底
- [ ] 重连后若服务端不支持 replay 且无 Last-Event-ID 续发，中间事件永久丢失（completed 全量覆盖可部分自愈文本）

**现有覆盖**:集成:transport.test.ts onerror调onError一次且流保持打开；reducer.test.ts eventId去重不二次累积/seq有序插入/completed全量覆盖半句

**代码定位**:`kokoro-web/src/application/session-stream/transport.ts:101-146` · `kokoro-web/src/application/session-stream/transport.ts:140-143` · `kokoro-web/src/application/session-stream/reducer.ts:223-233` · `kokoro-web/src/application/session-stream/reducer.ts:267-289` · `kokoro-web/src/application/session-stream/reducer.ts:169-182`

### 🟡 后端缺席本地预览降级 `web-preview-fallback`

**触发**:POST /sessions/{id}/runs 抛错（网络不可达或非 2xx）

**主路径**:
1. startSessionReply 的 async IIFE catch 后调 fallbackToPreview
1. simulateAssistantReply 用 buildSimulatedReplyEvents 产出与真实流同形的有序 domain 事件（含单调 seq）
1. thinking 模式额外前置：思考 delta 流 + 示例工具 invoked/returned + todo 整表
1. 事件按 stepMs 节拍（thinking 90ms / fast 40ms）+ chunkPauseMs 标点微停顿折进同一 reducer
1. 首个增量同步出现（streaming 态即时可见），run-completed 收尾后 onSettled('preview')
1. transportState=preview，标签显示「{Mode} · 本地预览」

**边界用例**:
- [ ] POST pending 期间用户已 stop（closed=true）→ 不再降级也不接管
- [ ] preview 不触发 onLive → 不写 pendingInput → 刷新后不会误重连本地模拟
- [ ] chunkText：CJK 1-3 字一吐、latin 整词带尾随空白；纯字符串无随机无时钟
- [ ] createLocalId 优先 randomUUID，回退自增计数（防 SSR 注水抖动）

**失败路径用例**:
- [ ] onState 首帧前 transportState 被设为 preview（onState 回调里 prev!=='live' 即 preview），随后 POST 成功才翻 live——存在标签短暂闪烁窗口

**现有覆盖**:集成:simulator.test.ts ×10（确定性/fast与thinking事件集/CJK与latin分块/onSettled恰1次/close防泄漏）；但reply.ts的POST失败→降级触发路径未被任何测试执行

**缺口(rank 6)**:integration 级断言：reply.ts 的 POST 失败→fallbackToPreview 触发路径与 closed-before-settle 竞态（simulator 本体已厚测，但降级决策层零执行）

**代码定位**:`kokoro-web/src/application/session-stream/reply.ts:30-79` · `kokoro-web/src/application/session-stream/simulator.ts:107-198` · `kokoro-web/src/application/session-stream/simulator.ts:219-266` · `kokoro-web/src/application/session-stream/simulator.ts:39-94` · `kokoro-web/src/interfaces/session-stream/hooks/use-conversation.ts:253-258`

### ✅ localStorage 持久化与脏数据降级 `web-localstorage-persistence`

**触发**:liveStore 任何变更（落盘）；页面加载/水合（恢复）；脏数据出现（降级）

**主路径**:
1. 落盘 effect：liveStore 非 null 时 serializeConversationStore（每线程 Set→string[]）后 JSON.stringify 写 key kokoro:conversations
1. 恢复：usePersistentStore 经 useSyncExternalStore 读取，SSR 快照恒 null
1. readPersistedStore 按原始字符串缓存稳定引用（防 React 判快照恒变抛无限循环）
1. JSON.parse try/catch → parseStoredConversationStore zod .strict() 校验 → 失败一律 null 降级空首屏
1. 旧版兼容：缺 mode/runId/todos/stepsByRun/subagentType/source 用 .default() 补，不判脏
1. liveStore 一旦出现即盖过 persistedStore 种子（store = liveStore ?? persistedStore）

**边界用例**:
- [ ] seenEventIds 落盘为 string[]，解析时 transform 回 Set
- [ ] 多余未知字段（strict）/枚举越界/类型错 → 整库判脏丢弃（不做部分恢复）
- [ ] storage 事件仅跨标签页触发重读；同标签页由 React 状态驱动
- [ ] 种子本就来自存储，liveStore 为 null 时不回写（避免无意义写）

**失败路径用例**:
- [ ] 损坏 JSON → cachedSeed=null，空首屏，不崩溃
- [ ] localStorage.setItem 配额满会抛 QuotaExceededError，落盘 effect 未捕获（潜在未处理异常）
- [ ] 整库判脏时用户全部历史静默消失（无提示）

**现有覆盖**:单元:tests/application/session-stream/state-schema.test.ts ×4（step判别联合/未知kind/缺判别/分支strict）;集成:session-shell.test.tsx [持久化]×4（恢复/损坏JSON降级/schema非法降级/发送即落盘）+ conversation-store.test.ts序列化往返 + reducer.test.ts非法形状it.each×13与旧版补默认

**代码定位**:`kokoro-web/src/interfaces/session-stream/hooks/use-persistent-store.ts:9-63` · `kokoro-web/src/interfaces/session-stream/hooks/use-conversation.ts:113-123` · `kokoro-web/src/interfaces/session-stream/hooks/use-conversation.ts:149-158` · `kokoro-web/src/application/conversation-store.ts:181-217` · `kokoro-web/src/application/session-stream/state-schema.ts:73-110`

### ✅ 滚动吸附跟随与「回到最新」 `web-scroll-follow`

**触发**:流式新内容到达时的自动跟随；用户上滑阅读历史；点击「回到最新」

**主路径**:
1. onScroll 实时判定 isNearBottom（距底 <64px 阈值，含余量防子像素抖动）
1. 贴底时 messages/isStreaming/activityVersion 任一变化 → scrollToLatest（threadEndRef.scrollIntoView block:end）
1. 用户上滑离底 → isNearBottom=false，停止跟随；hasMessages && !isNearBottom 时浮出「回到最新」按钮
1. 点按钮 scrollToLatest 并把贴底态置回 true 恢复跟随
1. submit/retry 时经 scrollToLatestRef seam 主动贴底（ref 打破 useConversation 与 useAutoScroll 的环依赖）

**边界用例**:
- [ ] 过程块静默生长（messages 引用不变）由 computeActivityVersion（思考字数+工具/子智能体计数+输出长度的单调派生数）驱动跟随
- [ ] 贴底态从 ref 读取，不列入 effect 依赖（防循环）
- [ ] jsdom 无布局环境 scrollIntoView 抛错被吞，不影响状态流转

**现有覆盖**:集成:session-shell.test.tsx [滚动]×4（上滑不拽视图+浮按钮/贴底跟随/点按钮滚底自隐/发送滚底）+ reducer.test.ts computeActivityVersion单调且纯派生

**代码定位**:`kokoro-web/src/interfaces/session-stream/hooks/use-auto-scroll.ts:7-71` · `kokoro-web/src/interfaces/session-stream/session-shell.tsx:40-45` · `kokoro-web/src/interfaces/session-stream/session-shell.tsx:72-85` · `kokoro-web/src/interfaces/session-stream/session-shell.tsx:139-148` · `kokoro-web/src/application/session-stream/reducer.ts:58-76`

### ✅ Markdown 渲染（助手/子智能体）与 XSS 防线 `web-markdown-rendering`

**触发**:assistant 消息正文或 subagent output 渲染

**主路径**:
1. MarkdownMessage 用 react-markdown + remark-gfm 构建 React 元素树
1. 不启用 rehype-raw：内嵌原始 HTML（<script>/<img onerror>）被当文本而非可执行节点，从根上防 XSS
1. 所有链接强制 target=_blank + rel=noopener noreferrer nofollow
1. 用户消息走 MessageBubble 的纯文本 <p>，绝不解析用户键入的 markdown 记号

**边界用例**:
- [ ] GFM：表格/任务列表/删除线/自动链接
- [ ] 流式中半截 markdown（未闭合代码块/表格）逐帧重解析，落定后由 completed 全量覆盖收敛
- [ ] subagent output 同样走 MarkdownMessage（同一防线）

**现有覆盖**:集成:session-shell.test.tsx [markdown]×3（富元素/用户消息纯文本不解析记号/<img onerror>不渲染真实元素）

**代码定位**:`kokoro-web/src/interfaces/session-stream/components/thread/markdown-message.tsx:1-31` · `kokoro-web/src/interfaces/session-stream/components/thread/message-bubble.tsx:18-25` · `kokoro-web/src/interfaces/session-stream/components/thread/subagent-row.tsx:66-81`

### ✅ 多段 segment 交错渲染（assistant turn 组装） `web-segment-interleaving`

**触发**:一个 run 内 thinking/tool/subagent/text 事件按 seq 交错到达

**主路径**:
1. reducer 把每类事件按 seq insertOrdered 进 stepsByRun[runId]（append-only 有序步骤列表）
1. buildThreadItems：用户消息单独成项；连续同 runId 的 assistant 消息归并为一个 assistant-turn
1. 仅有过程、尚无文本的 run（首 token 未到）也作为无文本 turn 渲染
1. AssistantTurn 的 groupSegments 按 segmentId 首现序分段：每段聚合自己的思考/工具/子智能体，正文从 messagesById 取
1. 每段渲染为「答案气泡在上 + 过程块挂下面」依次堆叠，共用一个头像与竖脊
1. 尾段 live：正文已到显示内联光标；正文未到显示 FormingBubble「正在思考/整理回答」；提交后整轮无任何 step 时由 ConversationThread/AssistantTurn 渲染 scaffold 轮，绝不留空帧

**边界用例**:
- [ ] legacy 落盘只回放了 messages：withRestoredTextSteps 为缺 text step 的段合成步骤，刷新后答案仍渲染
- [ ] tool.returned 无配对 invoked（部分 replay）：仍以 done 态记录，不丢事件
- [ ] 同 seq 事件稳定追加在既有之后（保持到达序）
- [ ] message-delta 首个增量确定 role/runId，后续只追加正文；completed 全量覆盖防半句残留

**失败路径用例**:
- [ ] subagent-finished/text 事件早于 started（无配对）时 updateRunStep 找不到目标直接丢弃

**现有覆盖**:单元:tests/interfaces/session-stream/thread/assistant-turn.test.tsx ×10（caret唯一性/单头像多段/scaffold不空帧/段内答案上过程下）;集成:reducer.test.ts按seq交错APPEND/buildThreadItems归并/仅过程轮不塌空 + session-shell.test.tsx [activity]两segment工具归属DOM顺序compareDocumentPosition

**代码定位**:`kokoro-web/src/application/session-stream/reducer.ts:108-157` · `kokoro-web/src/application/session-stream/reducer.ts:89-106` · `kokoro-web/src/application/session-stream/reducer.ts:240-289` · `kokoro-web/src/interfaces/session-stream/components/thread/assistant-turn.tsx:36-66` · `kokoro-web/src/interfaces/session-stream/components/thread/assistant-turn.tsx:98-161` · `kokoro-web/src/interfaces/session-stream/components/thread/conversation-thread.tsx:36-87`

### ✅ 工具调用行展示（running/done/error） `web-tool-call-display`

**触发**:tool.invoked / tool.returned 事件渲染为段内工具行

**主路径**:
1. tool-invoked → status=running，行内 spinner
1. tool-returned → updateRunStep 就地翻 done 并带 result（保持原 seq 位置不重排）
1. 有 args/result/error 时渲染 <details>（running/failed 默认 open）；无任何细节退化为不可点击静态行（避免死切换）
1. args 经 JSON.stringify(args,null,2) 紧凑预览；循环引用等序列化失败降级为键名列表

**边界用例**:
- [ ] error 态保持展开并显示 errorText（兜底文案「工具调用失败」）
- [ ] 当前事件链路无产生 status=error 的路径（schema/落盘支持，传输映射未覆盖）——error 仅可能来自持久化恢复
- [ ] 空 args（无键）不渲染参数块

**失败路径用例**:
- [ ] 运行中且无入参：展开块显示「运行中」脉冲而非塌空

**现有覆盖**:单元:tests/interfaces/session-stream/thread/tool-call-row.test.tsx ×6（running/done/error默认open/无细节无死切换）;集成:reducer.test.ts invoked→returned就地翻done不重排

**代码定位**:`kokoro-web/src/interfaces/session-stream/components/thread/tool-call-row.tsx:7-74` · `kokoro-web/src/application/session-stream/reducer.ts:321-369` · `kokoro-web/src/application/session-stream/state-schema.ts:14-23`

### ✅ 子智能体行展示与结论流式 `web-subagent-display`

**触发**:subagent.started/finished/text.delta/text.completed 事件

**主路径**:
1. subagent-started → running 状态行（机器人图标+名称+来源胶囊「内置/配置自定义/运行时自定义 · type」+spinner）
1. running 即默认展开：结论未到显示「运行中」脉冲，不塌空行
1. subagent-text-delta 续写 output；subagent-text-completed 全量覆盖
1. subagent-finished 翻 done；落定有 output 时为可展开 <details>（output 走 MarkdownMessage），无 output 退化静态行
1. description 常驻行内可见

**边界用例**:
- [ ] 三种 source 标签映射（built-in/config-custom/runtime-custom）
- [ ] 落定且无结论 → 静态行无死切换
- [ ] 旧落盘缺 subagentType/source 由 zod default 补

**失败路径用例**:
- [ ] finished/text 事件无配对 started 时被 updateRunStep 静默丢弃

**现有覆盖**:单元:tests/interfaces/session-stream/thread/subagent-row.test.tsx ×9（三source标签/running默认open/无output无死切换）;集成:reducer.test.ts started→finished翻done+text-completed写output + transport.test.ts三事件折叠

**代码定位**:`kokoro-web/src/interfaces/session-stream/components/thread/subagent-row.tsx:35-85` · `kokoro-web/src/application/session-stream/reducer.ts:376-432` · `kokoro-web/src/application/session-stream/state-schema.ts:25-35`

### 🟡 SSR 水合首帧与历史恢复（无闪跳） `web-hydration-first-frame`

**触发**:页面首次加载/刷新

**主路径**:
1. SSR 与客户端首帧 useHydrated=false：rail 与 composer 立即就位，主区渲染 aria-hidden 空 stage
1. useSyncExternalStore 双保险：useHydrated 与 usePersistentStore 的 server 快照都恒定（false/null），首帧与服务端一致，无 hydration mismatch
1. 水合后 mounted=true：persistedStore 种子出现 → 有历史则渲染 ConversationThread，无则 hero 空首屏「今天想做什么？」
1. TodoBar 同样 mounted 后才渲染

**边界用例**:
- [ ] 持久化快照按 raw 字符串缓存稳定引用，防 React 无限循环告警
- [ ] Date.now 只在用户动作里调用，绝不进 render

**失败路径用例**:
- [ ] 种子判脏（zod 失败）→ 等价于无历史，落到 hero 空首屏

**现有覆盖**:集成:session-shell.test.tsx 空首屏最小元素集/恢复历史隐藏hero/判脏落hero（jsdom仅客户端渲染，无SSR双帧一致性断言）

**代码定位**:`kokoro-web/src/interfaces/session-stream/hooks/use-hydrated.ts:1-11` · `kokoro-web/src/interfaces/session-stream/session-shell.tsx:31-32` · `kokoro-web/src/interfaces/session-stream/session-shell.tsx:118-137` · `kokoro-web/src/interfaces/session-stream/hooks/use-persistent-store.ts:12-44` · `kokoro-web/src/app/page.tsx:1-5`

### ✅ SSE 载荷严格解析与畸形事件隔离 `web-transport-strict-parse`

**触发**:SSE 上任一 named event（14 种事件名全集）到达

**主路径**:
1. decodeStreamMessage：校验 MessageEvent 且 data 为 string → JSON.parse
1. parseTransportEvent：zod union，envelope .strict()（event/event_id/seq/session_id/conversation_id/run_id/timestamp 全必填），各 payload 逐 arm .strict()
1. toSessionStreamEvent 投影成 domain 事件（snake→camel，seq 透传为唯一排序源）
1. run.created 解析以拒畸形但投影 null（web 不消费）
1. 任何解析失败/未知事件返回 null 被吞——单条畸形事件绝不中断整条流

**边界用例**:
- [ ] seq 必须非负整数；timestamp 必须 ISO datetime
- [ ] run.completed 的 status 故意放宽到任意非空字符串（新终态不卡死客户端）
- [ ] payload 含未知字段即拒收（注入防线）

**失败路径用例**:
- [ ] 被拒收的事件等同丢失：若是 message-delta 可由 completed 全量覆盖自愈；若是 run.completed 被拒则流不会落定（依赖 stop/兜底）

**现有覆盖**:集成:tests/infrastructure/transport-event.test.ts ×6（映射对齐/seq透传/cancelled容忍/run.created→null/缺title抛/顶层strict）+ transport.test.ts畸形信封拒收流不崩后续恢复;e2e:contract/verify.py 检查4/5（schema字段集与render视图契约锁定）

**代码定位**:`kokoro-web/src/application/session-stream/transport.ts:12-27` · `kokoro-web/src/application/session-stream/transport.ts:76-88` · `kokoro-web/src/infrastructure/transport-event-schema.ts:4-228` · `kokoro-web/src/infrastructure/transport-event-mapper.ts:16-133` · `kokoro-web/src/domain/session-stream-event.ts:11-157`

### 🟡 传输标签与模式提示（composer 下常驻状态行） `web-presentation-status`

**触发**:transportState（idle/connecting/preview/live）、hasFailed、isStreaming、hasMessages 任一变化

**主路径**:
1. useConversation 算 presentation = modePresentation(mode, hasFailed?'failed':transportState, isStreaming, hasMessages)
1. failed 最优先：「{Mode} · 这轮未完成」+ 模式化失败提示
1. idle 区分有无消息：「等你发出首条消息」vs「已准备继续」
1. preview：「本地预览」；live：「实时会话已连接」，hint 随 isStreaming 在进行/落定文案间切换
1. Composer 底部 <p class=kk-shell__transport> 常驻保留高度，标签延后出现不挤动输入框

**边界用例**:
- [ ] Fast/Thinking 两套完整文案矩阵（idle/connecting/preview/live/settled/failed 六态）
- [ ] transportLabel 同时镜像到 shell 的 data-transport-label 供 CSS/测试钩取

**现有覆盖**:集成:session-shell.test.tsx 仅间接触及（失败模式化文案/Fast落定摘要），mode-presentation六态×两模式文案矩阵无直接测试

**代码定位**:`kokoro-web/src/interfaces/session-stream/hooks/mode-presentation.ts:13-88` · `kokoro-web/src/interfaces/session-stream/hooks/use-conversation.ts:224-233` · `kokoro-web/src/interfaces/session-stream/components/composer/composer.tsx:284-289` · `kokoro-web/src/interfaces/session-stream/session-shell.tsx:91-92`

### 🟡 Composer 弹出菜单交互（附加/模式菜单通用机制） `web-composer-menus`

**触发**:用户点击 + 附加键或模式键打开浮层菜单

**主路径**:
1. ComposerMenu 受控 open，trigger 带 aria-haspopup/aria-expanded/aria-controls
1. open 时挂全局 pointerdown（点击菜单外关闭）与 keydown Escape 监听
1. 单选形态（selectedKey 提供，如 Fast/Thinking）渲染 menuitemradio+勾选；分组形态（sections，如附加菜单）渲染分组标签+分割线
1. 选中任一项后 onSelect 并立即收起

**边界用例**:
- [ ] 菜单为绝对定位浮层，不改 composer 盒模型
- [ ] align=start/end 控制锚定方向

**现有覆盖**:集成:session-shell.test.tsx 经模式菜单选Thinking（间接走通menuitemradio选中收起）

**代码定位**:`kokoro-web/src/interfaces/session-stream/components/composer/composer-menu.tsx:32-133` · `kokoro-web/src/interfaces/session-stream/components/composer/composer.tsx:210-251`

### 🟡 占位控件（附加上传/语音/搜索） `web-placeholder-controls`

**触发**:用户点击 + 菜单内的上传图片/上传文件/拍照，或麦克风键，或 rail 的搜索（⌘K）

**主路径**:
1. 附加菜单三项可选中，onSelect 为空操作（注释：上传链路接后端前为占位）
1. 麦克风按钮渲染但无 onClick handler
1. rail 搜索按钮显示 ⌘K 快捷键提示但无 handler、无全局键绑定

**边界用例**:
- [ ] 菜单本身的开闭/无障碍行为是完整的，仅业务动作缺位

**失败路径用例**:
- [ ] 用户点击后无任何反馈（已知占位状态，测试时应作为已知缺口而非 bug）

**现有覆盖**:集成:session-shell.test.tsx composer五控件可见性（附加内容/语音输入按钮在场）；占位无业务行为可断言，属已知缺口非bug

**代码定位**:`kokoro-web/src/interfaces/session-stream/components/composer/composer.tsx:33-72` · `kokoro-web/src/interfaces/session-stream/components/composer/composer.tsx:213-219` · `kokoro-web/src/interfaces/session-stream/components/composer/composer.tsx:253-259` · `kokoro-web/src/interfaces/session-stream/components/session-rail.tsx:56-62`

## 4. kokoro-session 业务流程用例(15)

### 🟡 POST 开 run(异步派发到请求流) `http-start-run`

**触发**:HTTP POST /sessions/{sessionId}/runs?input=...&conversation_id=...&execution_style=...(参数全在 query string,无 JSON body)

**主路径**:
1. applyBrowserHeaders 设置 CORS 头
1. sessionIdFromPath 从路径解析 sessionId(必须恰好 sessions/{id}/runs 三段)
1. 从 query 读 input,空/缺失即 400
1. startRun: defaultRunId 生成 run_(uuid 前 16 位);conversationId 缺省回退为 sessionId
1. runRequestSchema.parse 严格校验出站请求(strict,拒空 input/多余键/非法 execution_style)
1. streamPort.publish 写入 kokoro:runs:requests 请求流(不同步调 agent)
1. 返回 200 JSON { runId }

**边界用例**:
- [ ] input='' 空串是 falsy → 走 400 分支
- [ ] conversation_id 缺省 → 等于 sessionId
- [ ] execution_style 仅接受 fast|thinking;undefined 时该键整体不出现(strict 下不能传 undefined 键)
- [ ] 路径段数 ≠3 或首段非 sessions → 404
- [ ] POST 不读取 request body,只认 query 参数

**失败路径用例**:
- [ ] missing input → 400 {error:'missing input'}
- [ ] execution_style 非法值 → runRequestSchema.parse 抛 ZodError → buildServer 顶层 catch → 500(不是 400,无专门校验响应)
- [ ] redis backend 下 publish 连接失败 → 抛错 → 500

**现有覆盖**:单元:tests/run-request.test.ts ×6（strict拒多余键/缺input/枚举外style）;集成:tests/http.test.ts POST 200含run_前缀runId + tests/start-run.test.ts conversation_id缺省=session_id/空串style显式抛/runId互异;e2e:scripts/sse-loopback-gate.sh 断言1（真实链路POST必回run_id）

**缺口(rank 7)**:integration 级断言：HTTP 层错误响应契约——缺/空 input→400、非法 execution_style 当前落 500（ZodError 穿透）

**代码定位**:`kokoro-session/src/interfaces/http.ts:73-98` · `kokoro-session/src/application/start-run.ts:33-54` · `kokoro-session/src/domain/run-request.ts:4-13`

### ✅ SSE /stream 全量回放(历史+实时) `sse-full-replay`

**触发**:HTTP GET /sessions/{sessionId}/stream,无 Last-Event-ID 或其值被守卫拒绝

**主路径**:
1. writeHead 200 text/event-stream + no-cache + keep-alive
1. replayStream(sessionId) 得到流名 kokoro:session:{id}:replay
1. resumeCursor(undefined) → undefined → 从流首订阅
1. streamPort.subscribe 先吐全部历史条目,再阻塞等待实时新条目(memory 用 waiter 唤醒,redis 用 XREAD BLOCK)
1. 每条出站前 parseSessionEvent 严格自检(防脏事件出门)
1. toSseChunk: id=transport cursor,event=域事件名,data=完整 SessionEvent JSON(含 seq 供 web 定序)
1. req 'close' 置 aborted → 下次迭代 break → res.end()

**边界用例**:
- [ ] 空 session 流:不发任何 chunk,连接挂住等首个事件
- [ ] 历史与实时无缝拼接,无显式分界事件
- [ ] SSE 连接不因某 run 终态关闭 —— session 级流持续存活等待后续 run
- [ ] memory backend 下 subscribe 是死循环,只有客户端断开才退出

**失败路径用例**:
- [ ] replay 流中混入不合 schema 的事件 → parseSessionEvent 抛 → handle catch 发现 headersSent → 直接 res.end(),SSE 静默中断
- [ ] 客户端断开 → aborted break;redis 端 finally 归还(disconnect)duplicate 连接,不泄漏
- [ ] redis 条目缺 data 字段 → decodeFields 返回 null → parseSessionEvent 抛 → 同上中断

**现有覆盖**:集成:tests/http.test.ts SSE回放归一化事件/content-type/id-event-data三行结构/非空快照续订实时追加（回归测试）/id用transport cursor非域cursor;e2e:sse-loopback-gate.sh 断言2（5个event kind全集逐个grep）

**代码定位**:`kokoro-session/src/interfaces/http.ts:122-146` · `kokoro-session/src/infrastructure/sse.ts:5-11` · `kokoro-session/src/infrastructure/replay-store.ts:8-10`

### ✅ Last-Event-ID 增量续订 `sse-resume-last-event-id`

**触发**:GET /sessions/{id}/stream 携带 Last-Event-ID 头(浏览器 EventSource 重连自动带上次 SSE id)

**主路径**:
1. 读 req.headers['last-event-id']
1. resumeCursor 正则 /^\d+(-\d+)?$/ 判定是否传输层游标(memory 纯数字 / redis ms-seq)
1. 合法 → 作为 fromCursor 传入 subscribe
1. memory: 字符串比较 item.cursor > fromCursor(20 位零填充保证字典序=数值序),严格排除续点本身
1. redis: XREAD BLOCK 从 lastId 起(XREAD 语义天然 exclusive),只投续点之后条目
1. 后续与全量回放同路径(parseSessionEvent + toSseChunk)

**边界用例**:
- [ ] 续点恰为流尾 → 无历史输出,直接挂实时
- [ ] memory cursor 为 20 位零填充计数(CURSOR_WIDTH=20),redis 为 ms-seq,两格式都过正则
- [ ] backend 切换(memory↔redis)后旧 cursor 格式仍匹配正则但语义错位:memory 收到 'ms-seq' 字符串比较结果不可预期
- [ ] '0' 与 '0-0' 都合法,等价于从头读

**失败路径用例**:
- [ ] 头类型为 string[](理论分支)→ typeof 非 string → 退全量
- [ ] redis 流将来被 XTRIM 裁剪 → 续点之前条目静默丢失(代码注释明示未处理,需加裁剪检测回退全量)

**现有覆盖**:单元:tests/resume-cursor.test.ts格式判定 + tests/stream-port.memory.test.ts subscribe(fromCursor)严格排除续点;集成:tests/http.test.ts transport cursor增量续传跳过已交付（session.created不重发） + stream-port.redis.test.ts fromCursor之后续传

**代码定位**:`kokoro-session/src/interfaces/http.ts:115-118` · `kokoro-session/src/interfaces/http.ts:135-144` · `kokoro-session/src/infrastructure/stream-port.ts:34-53` · `kokoro-session/src/infrastructure/stream-port.ts:113-139`

### ✅ resumeCursor 守卫与畸形值 fallback `resume-cursor-guard`

**触发**:任意带 Last-Event-ID 的 /stream 请求

**主路径**:
1. 非 string(undefined/string[])→ 返回 undefined
1. string 但不匹配 /^\d+(-\d+)?$/(域 cursor 如 evt_xxx、空串、'1-2-3'、含字母)→ 返回 undefined
1. undefined → streamSession 从流首全量重放
1. 匹配 → 原样作为传输层续点

**边界用例**:
- [ ] 空串 ''、'abc'、'evt_123'、'1-2-3'、'-1'、' 1 ' 全部拒 → 全量
- [ ] '0'、'0-0'、超长数字串均放行
- [ ] 设计意图:升级过渡期旧域 cursor 不产生静默空流,宁可全量重复

**失败路径用例**:
- [ ] fallback 全量必然重复投递历史事件 → 依赖 web 端 reducer 按 eventId 去重兜底(代码注释明确此契约)

**现有覆盖**:单元:tests/resume-cursor.test.ts ×5（memory游标/redis id/域cursor拒/数组拒/undefined与空串拒）;集成:tests/http.test.ts 非法cursor忽略退全量绝不静默空流

**代码定位**:`kokoro-session/src/interfaces/http.ts:113-118`

### 🔴 后台调度:消费 run 请求流并派 relay `relay-dispatch-loop`

**触发**:进程启动(main)后常驻;每条 kokoro:runs:requests 新条目触发一次

**主路径**:
1. main() 构造 streamPort + replayStore,启动 dispatchRelays(不 await)
1. subscribe(REQUESTS_STREAM) 无 fromCursor → 从流首消费(含历史)
1. 每条 runRequestSchema.parse 严格校验
1. 为该 run new Normalizer(binding={session_id,conversation_id,run_id}, clock={newEventId,now})
1. void relayRun(...) 异步起中继,catch 仅 console.error('relay failed'),调度循环继续

**边界用例**:
- [ ] 多 run relay 并行互不阻塞
- [ ] 进程重启:requests 流历史全部重放 → 每个历史 run 重新起 relay;新 Normalizer 的 seenSeqs 为空 → 同一 run 事件会被再次 append 进 replay 流(replay 重复,靠 web 去重?event_id 是新生成的,web eventId 去重对此失效,只能靠 (run_id,seq))
- [ ] 无 consumer group:多副本部署时每个副本都消费同一 requests 流 → 同一 run 被 N 份 relay,replay N 倍写入

**失败路径用例**:
- [ ] 某条 request 不合 schema → parse 抛 → 整个 dispatchRelays 循环 crash(main.ts:46 catch 仅打日志)→ 此后所有新 run 永不被调度,服务静默半死(致命级)
- [ ] 单 run relay 失败只影响该 run,其它 run 不受波及

**现有覆盖**:集成:—（start-run.test.ts只测relayRun，main.ts的dispatchRelays循环零直接测试）;e2e:sse-loopback-gate.sh隐式覆盖happy path（真实服务调度成功才有SSE输出）

**缺口(rank 1)**:integration 级断言：requests 流中单条畸形 run.request 不杀死整个调度循环（或显式钉死当前 crash 行为为契约）

**代码定位**:`kokoro-session/src/main.ts:15-40` · `kokoro-session/src/main.ts:42-54` · `kokoro-session/src/application/start-run.ts:11`

### ✅ 单 run 中继:消费→归一化→append→终态收束 `relay-run-terminal-close`

**触发**:dispatchRelays 为每个 run.request 启动一条 relayRun

**主路径**:
1. subscribe(kokoro:run:{runId}:events) 从流首消费 agent 原始事件
1. normalizer.ingest 归一化为 0..2 条 SessionEvent
1. envelopes 非空 → replayStore.append(sessionId, envelopes)
1. envelopes 含 run.completed 或 run.failed → return 收束订阅(redis 侧 generator finally disconnect 归还连接)

**边界用例**:
- [ ] 空流/agent 迟迟不回:挂等不崩,但也无超时机制 → run 卡死时 relay 永久占用
- [ ] 重复 seq → ingest 返回 [] → 跳过 append,不触发终态判断
- [ ] 终态事件之后流内残余事件不再被消费
- [ ] 终态判断基于归一化输出(some event === run.completed|run.failed),非原始 kind

**失败路径用例**:
- [ ] ingest 抛(脏事件)→ relayRun reject → 仅日志,该 run 后续事件全部丢失,终态不会进 replay → web 端该 run 永远停在进行中(无 skip-and-continue,详见 strict-reject 流程)
- [ ] append 中途失败 → 多条 envelope 部分已 publish,replay 流与本地 mirror 不一致

**现有覆盖**:集成:tests/start-run.test.ts relayRun归一化顺序/在run.completed处停止+重复(run_id,seq)幂等/run.failed终止;e2e:sse-loopback-gate.sh主链路（终态落流才能通过）

**代码定位**:`kokoro-session/src/application/start-run.ts:66-77` · `kokoro-session/src/application/start-run.ts:13-15` · `kokoro-session/src/main.ts:30-38`

### ✅ 13 种 agent kind 逐个归一化为 AGUI 信封 `normalize-13-kinds`

**触发**:relayRun 每收到一条原始 agent 事件调用 normalizer.ingest(raw)

**主路径**:
1. 入站 agentEventSchema.parse:discriminatedUnion(kind) + 每 arm .strict(),13 kind 各绑专属 payload schema
1. run.started(payload 必须为空对象)→ 首次额外合成 session.created,恒产 run.created → 1 进 2 出(首次)或 1 进 1 出
1. thinking.delta {segment_id,text} → thinking.delta {segment_id,delta}(text 改名 delta)
1. text.delta → message.delta {segment_id,delta,role:'assistant'}(改名+注入 role)
1. text.completed → message.completed {segment_id,role:'assistant',content}(text→content)
1. tool.invoked → tool.invoked {segment_id,tool_id,name,args} 同形透传
1. tool.returned → tool.returned {segment_id,tool_id,name,result} 同形透传
1. todo.updated → todo.updated {todos:[{content,status∈pending|in_progress|completed}]} 同形
1. subagent.started → 同名 {segment_id,subagent_id,name,description,subagent_type,source∈built-in|config-custom|runtime-custom}
1. subagent.finished / subagent.text.delta / subagent.text.completed → 同名同形透传
1. run.completed {status∈completed|cancelled|timeout} → run.completed {run_id(取 binding),status}
1. run.failed {error_kind,message} → run.failed {run_id(取 binding),error_kind,message}
1. 每条信封注入 event_id(clock.newEventId)/session_id/conversation_id/run_id(全取 binding)/timestamp(clock.now ISO)并透传原事件 seq
1. 出站每条再过 parseSessionEvent 严格自检后才返回

**边界用例**:
- [ ] 原始事件自带的 run_id 字段只参与校验非空,映射时被忽略 —— payload 的 run_id 一律来自 binding,事件 run_id 与 binding 不一致也不报错(身份混淆隐患)
- [ ] text/delta/result/description/message 允许空串;args 任意 record;todos 允许空数组
- [ ] seq 必须 int ≥0;0 合法
- [ ] run.started 合成的两条信封共享同一 seq,event_id 各异
- [ ] clock 可注入 → 测试确定性

**失败路径用例**:
- [ ] 缺字段/多余键/非法枚举(status、source、todo status)/segment_id 空串 → 入站抛 ZodError
- [ ] 出站自检失败(理论上仅代码 bug)→ 抛错终止 relay

**现有覆盖**:单元:tests/normalize.test.ts ×21（全kind映射/信封字段齐全/seq透传/schema崩溃×5）+ tests/agent-event.test.ts ×10;e2e:contract/verify.py检查1-3（三仓kind集与payload字段名集锁定）+ gate 5 kind实链在场

**代码定位**:`kokoro-session/src/application/normalize.ts:28-42` · `kokoro-session/src/application/normalize.ts:44-172` · `kokoro-session/src/application/normalize.ts:178-191` · `kokoro-session/src/domain/agent-event.ts:87-111` · `kokoro-session/src/domain/session-event.ts:151-178`

### ✅ (run_id, seq) 去重幂等 `seq-dedup`

**触发**:同一 run 的事件被重复投递(agent 重发/流重放)

**主路径**:
1. Normalizer 实例 per-run(dispatch 每条 request 新建),内部 seenSeqs: Set<number>
1. ingest 先查 seenSeqs.has(seq) → 命中返回 [](relayRun 不 append)
1. 未命中 → add(seq) 后再映射

**边界用例**:
- [ ] seq=0 正常去重
- [ ] 同 seq 不同内容:首条胜出,后到的被静默吞掉
- [ ] 去重发生在 schema 校验之后:重复 seq 的脏事件仍会先抛错——不,parse 在前,脏事件先抛;合法重复才被吞
- [ ] 去重状态在内存:进程重启/多副本下失效,replay 流可能重复(下游需按 (run_id,seq) 兜底)

**失败路径用例**:
- [ ] 进程重启后 dispatch 重放 requests 流 → 新 Normalizer seenSeqs 为空 → 历史 run 事件二次 append 进 replay

**现有覆盖**:单元:tests/normalize.test.ts 同(run_id,seq)二次投喂输出空数组;集成:tests/start-run.test.ts relayRun重复run.started只产出一次;e2e:—（进程内幂等已钉死；重启/多副本失效见gap）

**代码定位**:`kokoro-session/src/application/normalize.ts:21` · `kokoro-session/src/application/normalize.ts:32-36` · `kokoro-session/src/main.ts:21-28`

### ✅ 合成事件:session.created + run.created `synthetic-session-run-created`

**触发**:run 的首条 run.started agent 事件

**主路径**:
1. sessionCreated flag(per-Normalizer)为 false → 合成 session.created {session_id,conversation_id,owner_id:'kokoro-agent',title}并置 true
1. title = conversationId || sessionId(conversationId 空串时回退)
1. 恒合成 run.created {run_id}
1. 两条信封透传 run.started 的同一 seq

**边界用例**:
- [ ] flag 是 per-Normalizer = per-run:同 session 的第二个 run 用新 Normalizer → 每个 run 都会再发一条 session.created,web 端必须幂等处理
- [ ] 同 run 内第二条 run.started(不同 seq)只产 run.created 不再产 session.created
- [ ] 同 run 内重复 seq 的 run.started 被 seq 去重整条吞掉

**失败路径用例**:
- [ ] run.started payload 非空对象({}之外任何键)→ strict 拒收抛错

**现有覆盖**:单元:tests/normalize.test.ts 首条合成对共享seq且event_id互异/第二次run.started不重发session.created;集成:tests/start-run.test.ts replay顺序首两条为合成对;e2e:sse-loopback-gate.sh断言4显式排除合成对再验严格递增

**代码定位**:`kokoro-session/src/application/normalize.ts:20` · `kokoro-session/src/application/normalize.ts:46-63` · `kokoro-session/src/application/normalize.ts:174-176`

### 🟡 replay 流写入与本地镜像 `replay-stream-write`

**触发**:relayRun 调用 replayStore.append(sessionId, envelopes)

**主路径**:
1. 流名 kokoro:session:{sessionId}:replay
1. 逐条 await streamPort.publish(每条事件一个流条目,cursor 即后续 SSE 的 Last-Event-ID 续点)
1. 同步 push 进进程内 mirror Map(为 read() 提供同步快照语义)
1. read(sessionId) 返回 mirror 浅拷贝(当前仅测试调用;HTTP 层直接 subscribe 流,不走 read)

**边界用例**:
- [ ] 逐条 publish 非原子:一批 envelope 中途失败 → 流中留下半批
- [ ] mirror 只反映本进程 append 过的事件:多副本/重启后 read() 与流内容不一致(HTTP 路径不受影响)
- [ ] memoryReplayStore() 便捷构造仅测试/单进程用

**失败路径用例**:
- [ ] publish 抛(redis 断连)→ append reject → relayRun 终止,该 run 中继死亡
- [ ] mirror 无上限增长:长寿进程内存随事件量线性膨胀

**现有覆盖**:集成:tests/start-run.test.ts经relayRun间接验证replay流内容与顺序;e2e:gate主链经replay流出SSE

**代码定位**:`kokoro-session/src/infrastructure/replay-store.ts:8-10` · `kokoro-session/src/infrastructure/replay-store.ts:14-37`

### ✅ StreamPort 双后端:memory vs redis 差异 `backend-memory-vs-redis`

**触发**:进程启动时 makeStreamPort() 按 KOKORO_STREAM_BACKEND 选择(默认 memory;redis 时读 KOKORO_REDIS_URL,默认 redis://127.0.0.1:6379)

**主路径**:
1. memory publish:自增 counter 零填充 20 位作 cursor,push 数组,唤醒该流全部 waiter
1. memory subscribe:扫数组吐 cursor > lastCursor 的条目,无新条目则挂 waiter promise;死循环,仅消费方 break 退出
1. redis publish:ensureConnected 后 XADD stream * data <JSON>,cursor=条目 id(ms-seq)
1. redis readAll:XRANGE - +,decodeFields 找 data 字段 JSON.parse
1. redis subscribe:duplicate() 独占连接(BLOCK XREAD 霸占连接防互饿),fromCursor||'0-0' 起,XREAD BLOCK 1000ms 轮询,finally disconnect
1. redis ping():lazyConnect 下显式 connect+ping 判活(测试 skip 探测用)

**边界用例**:
- [ ] CURSOR_WIDTH=20 / REDIS_FIELD='data' / BLOCK 1000ms 是与 Python 侧共享的 transport contract(contract/events.yaml constants),不可漂移
- [ ] memory cursor 字典序=数值序仅在 20 位内成立(2^53 级事件量内安全)
- [ ] redis fromCursor 空串 falsy → 回退 '0-0' 全量;XREAD exclusive 语义保证不重发续点本身
- [ ] memory close() 只 wakeAll 不终止订阅循环:醒来发现无新条目又挂回去 → 订阅者挂死(测试需靠 break)
- [ ] ioredis error 事件被吞(on error noop),依赖调用路径抛错显性失败;maxRetriesPerRequest:1 快速失败

**失败路径用例**:
- [ ] redis 不可达:publish/readAll/subscribe 的 connect 抛 → 上游 500 或 relay 死亡
- [ ] decodeFields 条目缺 data 字段/值 undefined → 返回 null → 下游 zod parse 抛
- [ ] data 字段非法 JSON → JSON.parse 直接抛(无 catch)
- [ ] XADD 返回空 id → 显式 throw 'redis xadd returned no id'

**现有覆盖**:单元:tests/stream-port.memory.test.ts ×7（保序/cursor互异/fromCursor排除/实时/流隔离/cursorWidth）;集成:tests/stream-port.redis.test.ts ×3（真实Redis，不可达skip）;e2e:contract/verify.py检查6（CURSOR_WIDTH/REDIS_FIELD/BLOCK_MS双端常量锁定）+ gate redis实链

**代码定位**:`kokoro-session/src/infrastructure/stream-port.ts:5-8` · `kokoro-session/src/infrastructure/stream-port.ts:11-78` · `kokoro-session/src/infrastructure/stream-port.ts:81-159` · `kokoro-session/src/infrastructure/stream-port.ts:162-170`

### 🔴 多订阅者/多副本 fan-out 广播 `multi-replica-fanout`

**触发**:同一流被多个消费者 subscribe(多 SSE 客户端;多 session 副本)

**主路径**:
1. subscribe 无 consumer group 概念:每个订阅者维护独立 lastCursor/lastId → 广播语义,人人收全量
1. replay 流:N 个 SSE 客户端各自独立续点互不影响;redis 下每订阅 duplicate 一条专属连接
1. redis backend 跨进程:副本 A 的 relay 写 replay,副本 B 的 SSE 订阅同名流即时可见 → web 可连任意副本

**边界用例**:
- [ ] memory backend 下无跨进程能力:多副本各自为政,SSE 只能看到本副本 relay 的事件
- [ ] requests 流同样是广播:多副本都跑 dispatchRelays → 同一 run.request 被每个副本各起一条 relay → replay 流 N 倍重复写入;且各副本 Normalizer 生成不同 event_id → web 按 eventId 去重失效,只能靠 (run_id,seq)+事件名去重(当前架构的最大多副本风险)
- [ ] redis subscribe BLOCK 1000ms 空转轮询:大量空闲 SSE 连接 = 大量阻塞连接 + 周期性唤醒

**失败路径用例**:
- [ ] 某订阅者消费慢不影响他人(无背压共享),但 memory 数组/redis 流无限增长无裁剪
- [ ] 副本间时钟差使重复信封 timestamp 不一致,下游若按时间排序会抖动

**现有覆盖**:集成:—（无多订阅者广播断言，更无多副本重复relay/event_id分歧断言）

**缺口(rank 4)**:integration 级断言：进程重启/多副本重放 requests 流后 replay 出现同 (run_id,seq) 不同 event_id 的重复信封，且 web reducer 缺 (runId,seq) 兜底去重

**代码定位**:`kokoro-session/src/infrastructure/stream-port.ts:34-53` · `kokoro-session/src/infrastructure/stream-port.ts:113-139` · `kokoro-session/src/main.ts:19` · `kokoro-session/src/interfaces/http.ts:141`

### 🔴 CORS 放通与 OPTIONS 预检 `cors-preflight`

**触发**:任意 HTTP 请求(每请求前置);浏览器跨源时先发 OPTIONS

**主路径**:
1. allowlist = {KOKORO_WEB_ORIGIN ?? http://127.0.0.1:3000, http://localhost:3000}
1. 请求带 origin 且命中 allowlist → 回 access-control-allow-origin: <该 origin> + vary: origin
1. 无条件回 allow-methods: GET,POST,OPTIONS 与 allow-headers: content-type
1. OPTIONS → 204 空响应直接返回

**边界用例**:
- [ ] 无 origin 头(同源/curl/服务间调用)→ 不回 allow-origin,请求照常处理
- [ ] 非 allowlist origin:服务端不拒绝、照常执行业务并返回数据,只是不回 allow-origin 由浏览器侧拦截 —— 非浏览器客户端不受任何限制(开发态设计)
- [ ] EventSource 跨源依赖 GET + allow-origin;SSE 无自定义头所以 allow-headers 仅 content-type 够用

**失败路径用例**:
- [ ] KOKORO_WEB_ORIGIN 配错(如带尾斜杠)→ 精确匹配失败 → 浏览器侧 CORS 报错,服务端无感知

**缺口(rank 8)**:integration 级断言：allowlist 命中回显 allow-origin+vary、非 allowlist 不回头但业务照常、OPTIONS→204

**代码定位**:`kokoro-session/src/interfaces/http.ts:9-23` · `kokoro-session/src/interfaces/http.ts:58-62`

### 🟡 未知 kind / 脏事件严格拒收(注意:无 skip-and-continue) `strict-reject-no-skip`

**触发**:agent 事件流出现未知 kind、缺字段、多余键、非法枚举值的条目

**主路径**:
1. agentEventSchema 为 13-kind discriminatedUnion,每 arm 顶层与 payload 双重 .strict()
1. 未知 kind → 判别失败抛 ZodError;已知 kind 但 payload 脏 → 该 arm strict 抛
1. ingest 不捕获 → relayRun for-await 抛 → promise reject
1. main.ts 派发处 catch 仅 console.error('relay failed', run_id) → 该 run 中继永久终止

**边界用例**:
- [ ] 已 append 进 replay 的事件保留;脏事件之后的合法事件(包括终态)全部丢失 → web 端该 run 卡在进行中,无超时无补偿
- [ ] 调度循环本身不受单 run 脏事件影响(隔离在 relayRun promise 内)
- [ ] 对比:requests 流的脏条目在 dispatchRelays 循环内直接 parse → 抛错杀死整个调度循环(见 relay-dispatch-loop),两处隔离级别不一致

**失败路径用例**:
- [ ] 重要事实:当前代码不存在'解析失败跳过该条继续消费'的行为 —— 任务假设的 skip-and-continue 未实现;单条脏事件 = 整条 run 中继死亡。若契约要求 skip-and-continue,这是缺口,值得加测试钉死期望行为
- [ ] 测试现状:tests/normalize.test.ts:195-380 只断言 ingest 抛错,无 relay 级 skip 断言

**现有覆盖**:单元:tests/normalize.test.ts 仅断言ingest对畸形/未知kind抛ZodError;集成:—（relay级行为契约——脏事件后终态丢失/run悬挂——零断言）

**缺口(rank 2)**:integration 级断言：relay 消费中途遇脏 agent 事件后的终态契约（当前单条脏事件=该 run 中继永久死亡、终态永不落 replay）

**代码定位**:`kokoro-session/src/domain/agent-event.ts:87-111` · `kokoro-session/src/application/normalize.ts:30` · `kokoro-session/src/application/start-run.ts:68-69` · `kokoro-session/src/main.ts:36-38`

### 🟡 HTTP 路由兜底与统一错误处理 `http-routing-error-envelope`

**触发**:任意不匹配已知路由的请求,或 handler 内未捕获异常

**主路径**:
1. req.url 缺失 → 400 'missing url'
1. 路径非 /sessions/{id}/runs(POST) 且非 /sessions/{id}/stream(GET) → 404 'not found'
1. handle 任何未捕获异常 → buildServer 顶层 catch:headersSent 为 false → 500 + error.message;已发头(SSE 中途)→ 直接 res.end()

**边界用例**:
- [ ] 方法不匹配(GET 打 runs / POST 打 stream)→ 落到 404,而非 405
- [ ] sessionId 为空段(/sessions//runs)→ segments.filter(Boolean) 后段数不足 → 404
- [ ] URL 以 http://127.0.0.1 为 base 解析,只取 pathname+query,host 无关

**失败路径用例**:
- [ ] 500 响应体直接暴露 error.message(含 ZodError 详情)→ 信息泄露面,开发态可接受
- [ ] SSE 中途异常被静默吞为正常断流,客户端只能靠 EventSource 自动重连恢复

**现有覆盖**:集成:tests/http.test.ts 仅未知路由404；缺url 400/405落404/500信封/SSE中途异常静默断流均无断言

**代码定位**:`kokoro-session/src/interfaces/http.ts:38-49` · `kokoro-session/src/interfaces/http.ts:64-68` · `kokoro-session/src/interfaces/http.ts:30-36` · `kokoro-session/src/interfaces/http.ts:109-110`

## 5. kokoro-agent 业务流程用例(17)

### 🟡 Worker 主循环:收 run 请求并发布事件流 `worker-main-loop`

**触发**:进程启动 `kokoro_agent.interfaces.worker:main`,持续订阅 redis/memory 流 kokoro:runs:requests

**主路径**:
1. main() 配置 logging、load_dotenv() 载入 .env、make_stream_port() 按 KOKORO_STREAM_BACKEND 建端口
1. _serve 以 processed=set() 初始化,port.subscribe(REQUESTS_STREAM) 无限迭代(from_cursor=None,从流起点 0-0 开始读)
1. 每条 raw dict 进 _handle_request:RunRequest.model_validate(strict+extra=forbid)校验
1. run_id 已在 processed 集合则跳过(进程内幂等);否则加入集合
1. make_chat_model(request.execution_style) 按请求解析模型(每请求解析,fast/thinking 无需重启)
1. async for event in run_agent(request, model):逐个 port.publish 到 kokoro:run:{run_id}:events

**边界用例**:
- [ ] 同一 run_id 的重复请求第二次到达被静默跳过(processed 为进程内存,重启即清空)
- [ ] worker 重启后 subscribe 从 0-0 重放历史请求 → 所有旧 run 会被重新执行一遍(processed 空)
- [ ] malformed 请求(缺字段/多余字段/类型错)只 warn 不中断主循环
- [ ] 事件流命名 kokoro:run:{run_id}:events 由 events_stream() 拼接,run_id 含冒号等字符不转义

**失败路径用例**:
- [ ] ValidationError → 丢弃该请求,LOGGER.warning,继续循环(worker.py:30-34)
- [ ] make_chat_model 抛 ValueError(坏 KOKORO_MODEL/未知 provider)发生在 run_agent 之外 → 异常穿透 _serve,整个 worker 崩溃,且该 run 不会收到任何 run.failed 事件
- [ ] port.publish 失败(redis 断连)同样不在 run.failed 边界内 → worker 崩溃,事件流半截

**现有覆盖**:集成:tests/test_worker.py ×5（畸形请求不崩循环/重复run_id幂等/execution_style传参，经run_once共享_handle_request）;e2e:sse-loopback-gate.sh真实worker常驻消费

**代码定位**:`kokoro-agent/src/kokoro_agent/interfaces/worker.py:17` · `kokoro-agent/src/kokoro_agent/interfaces/worker.py:20-21` · `kokoro-agent/src/kokoro_agent/interfaces/worker.py:24-44` · `kokoro-agent/src/kokoro_agent/interfaces/worker.py:59-71`

### ✅ run_once 批量排空模式 `worker-run-once`

**触发**:测试/一次性调用 run_once(port, processed, model?)

**主路径**:
1. port.read_all(REQUESTS_STREAM) 一次性取全部待处理请求
1. 逐条走与主循环相同的 _handle_request(校验→去重→执行→发布)
1. 可注入 model 参数绕过 make_chat_model(测试用 fake model 注入点)

**边界用例**:
- [ ] 幂等性依赖调用方持有的 processed 集合:同一集合重复调用 run_once,已跑过的 run_id 不重跑
- [ ] read_all 是快照式,处理期间新到的请求不会被这一轮看到

**失败路径用例**:
- [ ] 单条请求执行抛异常会中断整批(无 per-item try),后续请求不处理

**现有覆盖**:集成:tests/test_worker.py run_once端到端（MemoryStreamPort+真实DeepAgents+fake model注入）+ processed集合幂等

**代码定位**:`kokoro-agent/src/kokoro_agent/interfaces/worker.py:47-56`

### ✅ run 生命周期与 seq 单调分配 `run-lifecycle`

**触发**:run_agent(req, model) 被 worker 调用

**主路径**:
1. _build_agent:new RuntimeSubagentRegistry → create_deep_agent(model, tools=[agent 运行时子代理工具], system_prompt, subagents=built-in+config-custom)
1. agent.astream_events({messages:[user input]}, version='v2') 产生原始事件流
1. drive_agent_events 先 yield run.started(seq=1, payload={})
1. 在 asyncio.timeout(120s) 内迭代原始事件,translate_stream_event 纯映射为 (kind,payload) intents,按 13-kind 契约展开发出,每个事件 seq=nxt() 递增
1. 迭代正常结束 → yield run.completed(payload={status:'completed'})
1. 任意异常 → 单个 run.failed(payload={error_kind:类型名, message:str(error)}),绝不 re-raise

**边界用例**:
- [ ] seq 从 1 开始(run.started=1),对所有 kind 全局单调,run.failed 也占用 nxt() 保持连续
- [ ] ASTREAM_TIMEOUT_S=120 覆盖整个流迭代而非单 token:慢但持续产出的长 run 也会在 120s 被掐断为 run.failed(TimeoutError)
- [ ] run.started 在 try 之外发出:即使第一个原始事件就抛错,消费者也已先看到 run.started
- [ ] AgentEvent 模型 strict+extra=forbid,只填 kind/run_id/seq/payload,event_id/cursor/timestamp 留给 kokoro-session

**失败路径用例**:
- [ ] 模型 API 错误/网络错误/translate 抛错 → run.failed,error_kind 为异常类名
- [ ] 120s 超时 → run.failed error_kind='TimeoutError'
- [ ] _build_agent 阶段抛错(如 KOKORO_CUSTOM_SUBAGENTS 坏 JSON)发生在 drive_agent_events 之前 → 不产生 run.failed,异常上抛崩 worker

**现有覆盖**:单元:tests/test_run_agent.py 空流started→completed seq=[1,2]/seq从1严格递增无重复/异常→run.failed绝不发completed;集成:test_worker.py首尾run.started/run.completed且seq连续无空洞;e2e:sse-loopback-gate.sh断言3/4（seq非递减+排除合成对严格递增）

**代码定位**:`kokoro-agent/src/kokoro_agent/application/run_agent.py:30` · `kokoro-agent/src/kokoro_agent/application/run_agent.py:40-54` · `kokoro-agent/src/kokoro_agent/application/run_agent.py:84-113` · `kokoro-agent/src/kokoro_agent/application/run_agent.py:226-235` · `kokoro-agent/src/kokoro_agent/application/run_agent.py:238-250` · `kokoro-agent/src/kokoro_agent/domain/agent_event.py:7-60`

### ✅ token 流式文本:text.delta 累积 → text.completed `text-stream-flow`

**触发**:模型支持流式时的 on_chat_model_stream / on_chat_model_end 事件

**主路径**:
1. on_chat_model_stream:chunk 是 AIMessageChunk 且非纯 tool-call chunk → text_of(content) 非空时产出 TEXT_STREAM_INTENT('text.stream')
1. run_agent 把每片 TEXT_STREAM_INTENT 发为 text.delta(segment_id=segment.current()),并把 text 累积进 streamed_text
1. on_chat_model_end:输出是 AIMessage、text 非空且无 tool_calls → 产出 TEXT_INTENT('text')
1. run_agent 收到 TEXT_INTENT 且 streamed_text 不为 None → 只发 text.completed(text=累积值,不重发 delta),重置 streamed_text=None,segment.complete()

**边界用例**:
- [ ] text.completed 的 text 用本地累积的 streamed_text,而非模型 end 消息的全文 — 两者不一致时以累积为准
- [ ] is_tool_call_only_chunk:只带 tool_call_chunks 无文本的 chunk 完全静默,工具参数碎片不漏进 text
- [ ] list 型 content 只提取 {type:'text'} 块,thinking/tool 块被丢弃(text_of)
- [ ] 中间轮次(带 tool_calls 的模型回复)即使有文本也不产生 TEXT_INTENT → 不形成用户可见消息

**失败路径用例**:
- [ ] 若模型流式产出但 on_chat_model_end 缺失(异常中断),streamed_text 永不结算 → 只有 delta 无 completed,随后 run.failed

**现有覆盖**:单元:tests/test_run_agent.py 每块独立delta非累积/末尾恰一条全文completed/同segment_id/空块静默/tool_call_chunks静默不泄漏;e2e:gate断言2含message.completed

**代码定位**:`kokoro-agent/src/kokoro_agent/infrastructure/stream_translator.py:33-36` · `kokoro-agent/src/kokoro_agent/infrastructure/stream_translator.py:142-161` · `kokoro-agent/src/kokoro_agent/application/run_agent.py:118-140` · `kokoro-agent/src/kokoro_agent/application/run_agent.py:176-186` · `kokoro-agent/src/kokoro_agent/infrastructure/message_extractors.py:98-100`

### ✅ 非流式 fallback:delta+completed 成对发出 `text-nonstream-flow`

**触发**:KOKORO_DISABLE_STREAMING=1 或模型不产生 stream chunk(streamed_text 仍为 None 时收到 TEXT_INTENT)

**主路径**:
1. chat_model 构造时把 disable_streaming=True 传给 ChatOpenAI/ChatAnthropic
1. 无 on_chat_model_stream 事件,只有 on_chat_model_end → TEXT_INTENT
1. run_agent 检查 streamed_text is None → 同一 body({segment_id, text=全文})连续发 text.delta 和 text.completed 两个事件,然后 segment.complete()

**边界用例**:
- [ ] 下游消费者必须容忍'单 delta 携带全文 + completed 重复同文'的成对形态
- [ ] streamed_text 用 None vs '' 区分'从未流过'与'流过空串':空串 chunk 不会产出 intent(text 非空才 append),None 哨兵决定走哪条路径

**失败路径用例**:
- [ ] 无独立失败路径;依附 run-lifecycle 的异常边界

**现有覆盖**:单元:tests/test_run_agent.py text.delta与text.completed同ref同text（成对形态）+ tests/test_model.py disable_streaming=True传参

**代码定位**:`kokoro-agent/src/kokoro_agent/infrastructure/chat_model.py:41` · `kokoro-agent/src/kokoro_agent/infrastructure/chat_model.py:51` · `kokoro-agent/src/kokoro_agent/infrastructure/chat_model.py:65` · `kokoro-agent/src/kokoro_agent/application/run_agent.py:99-101` · `kokoro-agent/src/kokoro_agent/application/run_agent.py:187-190`

### 🟡 推理流:thinking.delta 产出 `thinking-delta-flow`

**触发**:reasoning 模型在 stream chunk 或 end 消息中携带推理内容

**主路径**:
1. reasoning_of 先读 additional_kwargs.reasoning_content(字符串),否则收集 content 列表里 type∈{thinking,reasoning} 块的 块[kind] 或 text 字段
1. on_chat_model_stream 与 on_chat_model_end 均可能产出 ('thinking.delta', {text}) intent
1. run_agent 发 thinking.delta(segment_id=segment.current())

**边界用例**:
- [ ] 无 thinking.completed:推理只有 delta,end 消息的 reasoning 会再发一次(stream 时可能与累积 delta 重复——end 路径不检查是否已流过)
- [ ] 普通非 reasoning 模型 reasoning_of 返回 '' → thinking 事件完全不出现
- [ ] thinking.delta 不调用 segment.complete() → 不会切段

**失败路径用例**:
- [ ] 无独立失败路径

**现有覆盖**:单元:tests/test_run_agent.py stream路径与end路径reasoning_content均先thinking.delta再text

**代码定位**:`kokoro-agent/src/kokoro_agent/infrastructure/message_extractors.py:58-81` · `kokoro-agent/src/kokoro_agent/infrastructure/stream_translator.py:146-147` · `kokoro-agent/src/kokoro_agent/infrastructure/stream_translator.py:154-156` · `kokoro-agent/src/kokoro_agent/application/run_agent.py:191-197`

### ✅ 通用工具调用:tool.invoked / tool.returned `tool-event-flow`

**触发**:astream_events 的 on_tool_start / on_tool_end,工具名不属于 write_todos/task/agent

**主路径**:
1. on_tool_start → ('tool.invoked', {tool_id=langchain run_id, name, args=dict(input)})
1. on_tool_end → ('tool.returned', {tool_id, name, result=result_text(output)})
1. run_agent 给两者注入 segment_id=segment.current() 后发出

**边界用例**:
- [ ] tool_id 取 langchain 事件的 run_id,invoked/returned 通过同一 tool_id 配对
- [ ] result_text 兜底链:output.content 字符串直取 → 非字符串 str() → output 为 None 得 ''
- [ ] args 非 mapping 时 as_mapping 兜底为 {} 不崩
- [ ] 工具事件会打开新 segment(若上一段已 complete),但自身不 complete → 后续文本与该工具同段

**失败路径用例**:
- [ ] 工具内部抛异常由 DeepAgents/LangGraph 处理;若异常逃逸到流层则触发 run.failed

**现有覆盖**:单元:tests/test_run_agent.py start/end映射/run_id作tool_id配对/result提取AIMessage文本/工具与后续文本段归属

**代码定位**:`kokoro-agent/src/kokoro_agent/infrastructure/stream_translator.py:69-70` · `kokoro-agent/src/kokoro_agent/infrastructure/stream_translator.py:102-103` · `kokoro-agent/src/kokoro_agent/infrastructure/stream_translator.py:135-141` · `kokoro-agent/src/kokoro_agent/application/run_agent.py:198-218` · `kokoro-agent/src/kokoro_agent/infrastructure/message_extractors.py:84-91`

### ✅ write_todos → todo.updated 映射 `todo-flow`

**触发**:模型调用 DeepAgents 内置 write_todos 工具

**主路径**:
1. on_tool_start 且 name=='write_todos' → ('todo.updated', {todos: input.todos})
1. on_tool_end 且 name=='write_todos' → 显式 return,不再发(清单已在 start 发过)
1. run_agent 对 todo.updated 走 else-分支按原 payload 发出 — 不注入 segment_id(契约:payload 只有 todos)

**边界用例**:
- [ ] todos 非 list 时兜底为 [](isinstance 检查)
- [ ] todos 条目内容({content,status})不在 agent 侧校验,strict 校验留给 kokoro-session Zod 边界
- [ ] 每次 write_todos 都是全量替换式的 todo.updated,无增量 diff

**失败路径用例**:
- [ ] 无独立失败路径;畸形 todos 项原样透传给下游

**现有覆盖**:单元:tests/test_run_agent.py on_tool_start映射todo.updated携带列表/on_tool_end静默不重发;集成:test_worker.py事件流中todo.updated在场;e2e:gate断言2 todo.updated实链在场

**代码定位**:`kokoro-agent/src/kokoro_agent/infrastructure/stream_translator.py:28` · `kokoro-agent/src/kokoro_agent/infrastructure/stream_translator.py:71-73` · `kokoro-agent/src/kokoro_agent/infrastructure/stream_translator.py:105-106` · `kokoro-agent/src/kokoro_agent/application/run_agent.py:219-225` · `kokoro-agent/src/kokoro_agent/domain/agent_event.py:38`

### ✅ task 工具子代理(built-in/config-custom):started/finished 与 source 解析 `subagent-task-flow`

**触发**:模型调用 DeepAgents 内置 task 工具委派已注册子代理

**主路径**:
1. _build_agent 用 materialize_runtime_subagents 把 built-in(researcher)+ config-custom(env)注册进 create_deep_agent 的 subagents
1. on_tool_start name=='task' → subagent.started {subagent_id=tool run_id, name=subagent_type, description, subagent_type, source=subagent_source_for(subagent_type)}
1. run_agent 注入 segment_id,并记录 active_subagent=(subagent_id, name) 用于后续文本路由
1. on_tool_end name=='task' → subagent.finished(同 source 解析),run_agent 清空 active_subagent

**边界用例**:
- [ ] source 解析顺序:built-in → config-custom(每次调用重读 os.environ)→ runtime registry;查不到默认 'runtime-custom'
- [ ] translate 层调用 subagent_source_for 时不传 runtime_registry → 运行时注册的名字靠默认 fallback 恰好得到 'runtime-custom'
- [ ] subagent_type 缺失/空 → 兜底字符串 'subagent'(其 source 解析为 runtime-custom)
- [ ] active_subagent 是单槽:不支持并行 task,嵌套/并发 task 的文本路由会串

**失败路径用例**:
- [ ] task 指定不存在的 subagent_type → DeepAgents 工具层报错,结果以工具错误或 run.failed 形态出现
- [ ] mid-run 修改 KOKORO_CUSTOM_SUBAGENTS 环境变量会让 started 与 finished 的 source 解析不一致

**现有覆盖**:单元:tests/test_run_agent.py task映射started/finished+source=built-in与config-custom + tests/test_subagents.py subagent_source_for解析×2

**代码定位**:`kokoro-agent/src/kokoro_agent/infrastructure/stream_translator.py:29` · `kokoro-agent/src/kokoro_agent/infrastructure/stream_translator.py:74-87` · `kokoro-agent/src/kokoro_agent/infrastructure/stream_translator.py:107-120` · `kokoro-agent/src/kokoro_agent/infrastructure/subagent_registry.py:127-135` · `kokoro-agent/src/kokoro_agent/application/run_agent.py:204-211`

### 🟡 runtime-custom 子代理:agent 工具即席注册并执行 `subagent-runtime-flow`

**触发**:模型调用自定义 StructuredTool 'agent'(name/description/system_prompt/task 四参)

**主路径**:
1. on_tool_start name=='agent' → subagent.started {name=args.name, subagent_type=args.name, source='runtime-custom'}
1. agent_runtime 协程:registry.get(name) 命中复用,否则 registry.register(strip 后非空校验+查重)
1. create_agent(model, system_prompt, tools=[], name) 建嵌套 runner,ainvoke 执行 task
1. 从结果 messages 倒序找首个有文本的 AIMessage,rstrip 后作为工具返回字符串(找不到返回 '')
1. on_tool_end name=='agent' → subagent.finished(source='runtime-custom')

**边界用例**:
- [ ] registry 每个 run 新建(_build_agent 内):runtime 注册不跨 run 持久;同 run 内同名第二次调用复用首个 spec(传入的新 system_prompt 被忽略)
- [ ] 与 built-in 名冲突('researcher')或同 run 重名 → register 抛 ValueError
- [ ] name/description/system_prompt/task 由 Pydantic args_schema(min_length=1)前置拦截空串
- [ ] 同步调用路径 agent_runtime_sync 直接 raise RuntimeError('requires async execution')

**失败路径用例**:
- [ ] register ValueError / runner.ainvoke 异常 → 由 langchain 工具层捕获或上抛;上抛则 run.failed
- [ ] 嵌套 runner 无文本输出 → 工具返回空串,主 agent 拿到空结果继续

**现有覆盖**:单元:tests/test_run_agent.py agent工具映射source=runtime-custom + tests/test_runtime_subagent_protocol.py register/get/同名抛ValueError + test_subagents.py撞built-in名抛;集成:—（agent_runtime协程执行路径：同名复用/嵌套ainvoke/空输出回''/sync抛RuntimeError均无断言）

**代码定位**:`kokoro-agent/src/kokoro_agent/infrastructure/stream_translator.py:30` · `kokoro-agent/src/kokoro_agent/infrastructure/stream_translator.py:43-47` · `kokoro-agent/src/kokoro_agent/infrastructure/stream_translator.py:88-101` · `kokoro-agent/src/kokoro_agent/infrastructure/stream_translator.py:121-134` · `kokoro-agent/src/kokoro_agent/infrastructure/stream_translator.py:164-224` · `kokoro-agent/src/kokoro_agent/infrastructure/subagent_registry.py:29-54`

### ✅ 子代理文本路由:subagent.text.delta / subagent.text.completed `subagent-text-routing`

**触发**:active_subagent 存在期间到达的模型文本事件,且事件 metadata.lc_agent_name == 子代理名

**主路径**:
1. routed_subagent:active_subagent 非空且 ev.metadata.lc_agent_name 等于其 name → 返回 subagent_id,否则 None
1. TEXT_STREAM_INTENT 命中路由 → subagent.text.delta {segment_id, subagent_id, text},累积进 sub_streamed_text
1. TEXT_INTENT 命中路由且 sub_streamed_text 非 None → 仅 subagent.text.completed(text=累积),重置哨兵
1. TEXT_INTENT 命中路由且从未流过 → 同 body 连发 subagent.text.delta + subagent.text.completed(非流式 fallback 对)

**边界用例**:
- [ ] lc_agent_name 不匹配的子图文本(如 DeepAgents 内部节点)落回主线 text.* 家族
- [ ] subagent.text.completed 后不调用 segment.complete() → 子代理文本不切段,父级后续文本共用该段
- [ ] sub_streamed_text 与 streamed_text 各自独立哨兵,父/子文本互不污染
- [ ] subagent.finished 时若 sub_streamed_text 未结算(无 end 事件)会残留到下一个子代理

**失败路径用例**:
- [ ] create_agent 未注入 lc_agent_name metadata 时,子代理文本全部误归主线 text.delta

**现有覆盖**:单元:tests/test_run_agent.py 嵌套流路由（lc_agent_name命中→subagent.text.*，主线只剩最终总结）流式逐块delta+一条completed含subagent_id、父线程无text.completed

**代码定位**:`kokoro-agent/src/kokoro_agent/application/run_agent.py:98-111` · `kokoro-agent/src/kokoro_agent/application/run_agent.py:120-133` · `kokoro-agent/src/kokoro_agent/application/run_agent.py:142-175`

### ✅ _Segmenter 分段语义:tool→text→tool 不塌缩 `segmenter-flow`

**触发**:drive_agent_events 内所有携带 segment_id 的事件调用 segment.current()

**主路径**:
1. current():无活跃段或上一段已 complete → counter+1,生成 '{run_id}:seg_{counter:04d}' 新段;否则返回现段
1. 只有主线 text.completed(两条路径)调用 segment.complete()
1. tool.invoked/tool.returned/thinking.delta/subagent.* 取 current() 但从不 complete → 与随后的文本同段
1. text.completed 之后的下一个 tool/text 事件触发新段 → tool→text→tool→text 产出 seg_0001、seg_0002 两段而非合并一段

**边界用例**:
- [ ] 段 id 全局唯一(run_id 前缀+计数),由 agent 分配,session 原样透传
- [ ] counter 是 :04d 最小宽度,>9999 自动变宽不截断
- [ ] subagent.text.completed 不结段是有意行为还是遗漏值得用测试钉死(与主线 text.completed 行为不对称)
- [ ] 一个 run 内纯思考无文本 → 段开了永不 complete,只有一个段

**失败路径用例**:
- [ ] 无独立失败路径(纯内存计数)

**现有覆盖**:单元:tests/test_run_agent.py 同段共享segment_id/落定后新段seg_0002/工具1→文本1→工具2→文本2两段不塌缩/流式段完成新ref

**代码定位**:`kokoro-agent/src/kokoro_agent/application/run_agent.py:62-81` · `kokoro-agent/src/kokoro_agent/application/run_agent.py:185` · `kokoro-agent/src/kokoro_agent/application/run_agent.py:190` · `kokoro-agent/src/kokoro_agent/application/run_agent.py:204`

### 🟡 模型解析:execution_style fast/thinking + provider 分发 `model-resolution-flow`

**触发**:_handle_request 每请求调用 make_chat_model(execution_style)

**主路径**:
1. KOKORO_LOCAL_FAKE_MODEL=='1' 时直接短路返回本地假模型(忽略一切 provider 配置)
1. resolve_execution_config:style 非 'thinking' 一律折叠为 'fast';KOKORO_MODEL(默认 anthropic:claude-sonnet-4-6)按 'provider:model' partition 拆分
1. provider=='openai' → ChatOpenAI(reasoning_effort='high' 当 thinking,否则 None;OPENAI_API_KEY/OPENAI_BASE_URL)
1. provider=='anthropic' → ChatAnthropic(effort='high' 当 thinking;ANTHROPIC_API_KEY 有无走两个构造分支;ANTHROPIC_BASE_URL)
1. KOKORO_DISABLE_STREAMING=='1' → disable_streaming=True 传入构造器

**边界用例**:
- [ ] RunRequest.execution_style 是 Literal['fast','thinking'] 且 strict — 非法值在 worker 校验层就被丢;resolve 内的折叠只对直接调用方生效
- [ ] KOKORO_MODEL 形如 'anthropic:'、':model'、'plainstring' 均判非法
- [ ] fast 与 thinking 唯一差异是 effort/reasoning_effort 参数,模型名相同
- [ ] API key 缺失不在构造时报错(Anthropic 走无 key 分支),失败延迟到首次模型调用 → 那时落入 run.failed

**失败路径用例**:
- [ ] _split_model_spec 抛 ValueError('Invalid KOKORO_MODEL spec')
- [ ] 未知 provider 抛 ValueError('Unsupported model provider') — 两者均在 run.failed 边界之外,直接崩 worker

**现有覆盖**:单元:tests/test_model.py ×5（默认构造/自定义spec/thinking设reasoning_effort=high/fake flag/非法provider显性抛）;集成:test_worker.py monkeypatch验证style传参

**代码定位**:`kokoro-agent/src/kokoro_agent/infrastructure/chat_model.py:14-15` · `kokoro-agent/src/kokoro_agent/infrastructure/chat_model.py:26-42` · `kokoro-agent/src/kokoro_agent/infrastructure/chat_model.py:45-89` · `kokoro-agent/src/kokoro_agent/domain/run_request.py:7-20`

### ✅ LOCAL_FAKE_MODEL 离线确定性路径 `local-fake-model-flow`

**触发**:环境变量 KOKORO_LOCAL_FAKE_MODEL=1

**主路径**:
1. make_chat_model 返回 LocalFakeChatModel,真实 DeepAgents 循环照常运行(假模型支持 bind_tools)
1. 固定两幕脚本:第一轮回 write_todos tool_call(2 条 todo:completed+in_progress),第二轮回固定中文最终答案
1. 产生的事件序列:run.started → todo.updated → text.delta/text.completed(本地预览文案) → run.completed
1. _generate 检测输入无 AIMessage(新 run 首轮)→ cursor 重置为 0,长生命周期 worker 复用同一实例可跨 run 重放脚本
1. 脚本耗尽后的额外轮次返回空 AIMessage 终止循环

**边界用例**:
- [ ] bind_tools 接受并忽略(脚本固定),返回 with_types 包装
- [ ] 同步 _generate + langchain 的 astream 兜底意味着流式形态依赖 langchain 行为(单 chunk 或仅 end)→ 两种都应落到 delta+completed,值得契约测试钉死
- [ ] 并发 run 共享一个实例时 _cursor 有竞态(单 worker 串行处理下不触发)

**失败路径用例**:
- [ ] 无外部依赖,基本不会失败;脚本与 DeepAgents 版本行为耦合(write_todos 参数 schema 变更会崩)

**现有覆盖**:单元:tests/test_model.py fake flag返回LocalFakeChatModel;集成:tests/test_worker.py 经flag走make_chat_model完整事件流且text.completed含『本地预览』;e2e:sse-loopback-gate.sh全链以fake model跑真实DeepAgents循环

**代码定位**:`kokoro-agent/src/kokoro_agent/infrastructure/chat_model.py:80-81` · `kokoro-agent/src/kokoro_agent/infrastructure/local_fake_model.py:15-39` · `kokoro-agent/src/kokoro_agent/infrastructure/local_fake_model.py:42-88`

### ✅ config-custom 子代理:KOKORO_CUSTOM_SUBAGENTS env 加载 `config-custom-subagent-loading`

**触发**:_build_agent → materialize_runtime_subagents → load_custom_subagents_from_env(每 run 重读)

**主路径**:
1. 读 KOKORO_CUSTOM_SUBAGENTS 环境变量;空/未设 → 返回 []
1. json.loads + TypeAdapter(list[_CustomSubagentPayload]).validate_python:strict、extra=forbid、strip_whitespace+min_length=1 三字段(name/description/system_prompt)
1. 逐条查重:撞 built-in 名或列表内重名 → raise ValueError(fail-loud)
1. 合法条目转 RegisteredSubagent(source='config-custom'),与 built-in、runtime registry 一起 materialize 为 DeepAgents SubAgent dict(同一 model,tools=[])

**边界用例**:
- [ ] 纯空白字符串字段被 strip 后 min_length=1 拦截
- [ ] 未知键、非字符串值(strict)、非 list 顶层结构均拒收
- [ ] subagent_source_for 每次事件都重读 env:run 中途改 env 会导致 source 标注漂移

**失败路径用例**:
- [ ] 坏 JSON → json.JSONDecodeError;schema 违例 → ValidationError;重名 → ValueError — 三者都发生在 _build_agent 阶段(run.failed 边界外),直接崩 worker 且无事件落流

**现有覆盖**:单元:tests/test_subagents.py ×15（坏JSON/未知字段/非字符串/缺字段/空白/strip/撞名抛/materialize合并）

**代码定位**:`kokoro-agent/src/kokoro_agent/infrastructure/subagent_registry.py:13-26` · `kokoro-agent/src/kokoro_agent/infrastructure/subagent_registry.py:57-67` · `kokoro-agent/src/kokoro_agent/infrastructure/subagent_registry.py:70-94` · `kokoro-agent/src/kokoro_agent/infrastructure/subagent_registry.py:97-124` · `kokoro-agent/src/kokoro_agent/application/run_agent.py:52`

### ✅ StreamPort 传输层:memory vs redis 契约 `stream-port-transport`

**触发**:make_stream_port() 按 KOKORO_STREAM_BACKEND(默认 memory)构造;worker publish/subscribe 全经此口

**主路径**:
1. 协议:publish 保序、cursor 单调可比较;StreamItem={cursor, event dict}
1. MemoryStreamPort:cursor 为 zfill(20) 单调整数(字典序==插入序),subscribe 用 asyncio.Event 阻塞而非忙等,from_cursor 按字典序跳过 <=
1. RedisStreamPort:XADD 单字段 data 存 JSON(ensure_ascii=False),entry id 即 cursor;read_all 用 XRANGE - +;subscribe 用 XREAD BLOCK 1000ms 从 last(默认 '0-0')循环
1. 传输常量是 Python/TS 共享契约:_REDIS_FIELD='data'、_BLOCK_MS=1000、_CURSOR_WIDTH=20

**边界用例**:
- [ ] memory 后端单进程,无法桥接 TS session — worker 真实部署必须 redis,默认 memory 是个静默陷阱
- [ ] cursor 宽度 20 可在测试中收窄做契约对照
- [ ] redis entry 缺 data 字段 → event 兜底 {};bytes/str 双形态统一 _decode
- [ ] subscribe from_cursor=None:memory 从头吐全部,redis 从 '0-0' 全量重放 — 重启重放语义由此而来

**失败路径用例**:
- [ ] 未知 backend 值 → make_stream_port raise ValueError
- [ ] redis 连接失败/JSON 解析失败异常上抛(无内部重试),崩掉调用方
- [ ] redis xread 永久空响应时 subscribe 死循环 continue(预期行为,靠 BLOCK 节流)

**现有覆盖**:单元:tests/test_stream_port_memory.py ×6（保序/cursor唯一单调/from_cursor跳过/阻塞唤醒非忙等/cursor_width）;集成:tests/test_stream_port_redis.py ×3（真实Redis不可达skip）;e2e:contract/verify.py检查6双端常量 + gate redis实链

**代码定位**:`kokoro-agent/src/kokoro_agent/infrastructure/stream_port.py:12-14` · `kokoro-agent/src/kokoro_agent/infrastructure/stream_port.py:23-45` · `kokoro-agent/src/kokoro_agent/infrastructure/stream_port.py:48-101` · `kokoro-agent/src/kokoro_agent/infrastructure/stream_port.py:107-158` · `kokoro-agent/src/kokoro_agent/infrastructure/stream_port.py:161-169`

### 🟡 异常→run.failed 边界(及边界外区域) `failure-run-failed-boundary`

**触发**:drive_agent_events 迭代期间任意异常

**主路径**:
1. try 块包裹 asyncio.timeout(120) + 整个原始事件迭代与 intent 展开
1. except Exception(BLE001 有意宽捕)→ 发单个 run.failed {error_kind: 异常类名, message: str(error)},seq 延续单调
1. 异常永不 re-raise,worker 主循环继续服务后续请求

**边界用例**:
- [ ] run.failed 之后不会再有 run.completed(generator 直接结束)
- [ ] 覆盖范围仅限模型流迭代:make_chat_model、_build_agent(含 env 子代理加载)、port.publish 三处异常都在边界之外 → 崩 worker 且流上无终止事件,下游会看到悬挂的 run
- [ ] KeyboardInterrupt/SystemExit 等 BaseException 不被捕获(Exception 级)

**失败路径用例**:
- [ ] TimeoutError(120s)、模型 4xx/5xx、translate 内 KeyError 等全部归一为 run.failed
- [ ] publish run.failed 本身失败 → 异常逃逸,流上既无 completed 也无 failed

**现有覆盖**:单元:tests/test_run_agent.py 流内异常→run.failed含error_kind/message且绝不发run.completed;集成:—（边界外三区：make_chat_model/_build_agent/publish失败崩worker无终态，零断言；120s超时路径无直接断言）

**缺口(rank 3)**:integration 级断言：run.failed 边界外异常（make_chat_model/_build_agent/坏 KOKORO_CUSTOM_SUBAGENTS）应产出 run.failed 而非崩 worker 留悬挂 run

**代码定位**:`kokoro-agent/src/kokoro_agent/application/run_agent.py:30` · `kokoro-agent/src/kokoro_agent/application/run_agent.py:114-115` · `kokoro-agent/src/kokoro_agent/application/run_agent.py:229-235` · `kokoro-agent/src/kokoro_agent/interfaces/worker.py:42-44`

## 6. e2e / 门禁资产清单

### `scripts/sse-loopback-gate.sh`(e2e)

- 断言1: POST /sessions/$SID/runs?conversation_id=$SID&input=ping&execution_style=fast 必须返回非空 run_id(runId 或 run_id 字段),否则 FAIL exit 1
- 断言2: curl -sN --max-time 4 $SESSION/sessions/$SID/stream 的 SSE 流必须包含全部 5 个 event kind: session.created / run.created / todo.updated / message.completed / run.completed(逐个 grep -qx,缺一即 FAIL)
- 断言3: 解析每条 data: JSON 的 seq 与 run_id,按 run 分组断言 seq 非递减(seq 是一等 envelope 字段)
- 断言4: 排除 session.created/run.created(两条由 run.started 合成、共享同一 seq)后,剩余事件 seq 必须严格递增
- 判级: e2e + gate-script 双属性——走真实 agent→session→Redis→session SSE 主链路的脚本化门禁,自述'取代手工 Playwright e2e,任何 stream-pipeline 改动后必跑'
- 前置条件: Redis db14 + kokoro-session 监听 :3001(KOKORO_STREAM_BACKEND=redis KOKORO_REDIS_URL=redis://127.0.0.1:6379/14 bun run src/main.ts)+ kokoro-agent worker(同 env + KOKORO_LOCAL_FAKE_MODEL=1 uv run kokoro-agent-worker);可用 KOKORO_SESSION_URL 覆盖默认 http://127.0.0.1:3001;依赖 curl + python3;无 CI 接入,手工执行

### `contract/verify.py`(gate-script)

- 检查1: kokoro-agent/src/kokoro_agent/domain/agent_event.py 的 AgentKind Literal kind 集 + docstring 表格的 per-kind payload 字段名集 == events.yaml agent_out 视图
- 检查2: kokoro-session/src/domain/agent-event.ts 的 Zod discriminated union(按 kind)各 arm payload 键集 == agent_out 视图
- 检查3: kokoro-session/src/domain/session-event.ts 的 Zod union(按 event)== agui_out 视图(含 agui_only 节点)
- 检查4: kokoro-web/src/infrastructure/transport-event-schema.ts 各 arm == agui_out+web 容忍字段(agui_out_web_extra),且 envelope enum 的 event 集 == agui_out(web) 全集
- 检查5: kokoro-web/src/domain/session-stream-event.ts render union(camelCase,剔除 6 个 envelope 字段)== render 视图(render.absent 的 kind 必须缺席)
- 检查6: transport 常量 CURSOR_WIDTH/REDIS_FIELD/BLOCK_MS 在 kokoro-session stream-port.ts 与 kokoro-agent stream_port.py 双端字面量 == yaml transport 节
- 检查7: envelope 字段——session session-event.ts 的 envelopeFields 键集 == yaml envelope.agui_out;web eventEnvelopeSchema == agui_out+event
- 判级: 纯 gate-script,确定性、model-free、纯静态正则/括号配平解析,任何 missing/extra/drift 即非零退出 + 精确报告(文件/kind/字段);phase 1 只锁 kind 集与字段名集,字段类型/必选性是 phase 2 TODO
- 前置条件: 仅 python3 + PyYAML,零服务依赖(无 redis/端口/env);运行方式 python3 contract/verify.py;yaml 注释自述应入 CI 但 .github/ 不存在,目前手工跑;它已取代被删除的 scripts/check-contract-kinds.sh(其'三仓 kind 集 byte-identical'前提为假)

### `kokoro-session/tests/stream-port.redis.test.ts`(integration)

- RedisStreamPort publish/readAll 往返且 cursor 单调递增互异
- subscribe(fromCursor) 从给定 cursor 之后恢复(跳过更早事件)
- 允许自定义 block 轮询间隔
- 前置条件: KOKORO_REDIS_URL(默认 redis://127.0.0.1:6379)可 ping 通;探测失败时整组 test.skip 干净跳过不 fail——即 bun test 的 '57 pass / 2-3 skip' 来源

### `kokoro-agent/tests/test_stream_port_redis.py`(integration)

- RedisStreamPort publish 后 read_all 保序
- subscribe(from_cursor) 跳过 cursor 之前的条目
- 允许自定义 block_ms
- 前置条件: pytest.importorskip('redis.asyncio') + KOKORO_REDIS_URL(默认 redis://127.0.0.1:6379/0)0.5s 超时 ping 探测,不可达即 skip——pytest 输出里的 skip 来源

### `.playwright-mcp`(e2e)

- 结论: 全仓无 Playwright e2e 配置——无 playwright.config.*、无 e2e/ 目录、kokoro-web/package.json 无 @playwright/test 依赖(测试栈仅 vitest+jsdom+testing-library)
- 此目录(及 kokoro-web/.playwright-mcp)仅是 Playwright MCP 浏览器工具的手工会话产物: console-*.log / page-*.yml,时间跨度 2026-05-30 至 2026-06-07;根目录另有 01~29 编号 PNG 手工截图
- claude-progress.md 明确记载: 此前 audits 假设的 'real SSE e2e gate' 并不存在(web 只有 vitest),Playwright 验证全部是会话内手工跑,sse-loopback-gate.sh 即为补此盲区而建的可重跑替代
- tasks/todo.md 仍有一条未完成项: '[ ] REAL-backend e2e: 起 session(:3001, Redis db15)+ agent worker(gateway .env)后 Playwright 一次真实 DeepAgents 流式 run'——属计划中,未脚本化

### `package.json`(gate-script)

- 根 package.json scripts 仅 build: tsc,没有 test/e2e/gate 任何聚合入口;根目录与三个子仓均无 Makefile;.github/ 不存在即零 CI——两个跨仓门禁(sse-loopback-gate.sh / verify.py)均未被任何自动化调用
- 各子仓也均无 scripts/ 目录;子仓门禁为各自 package.json/pyproject 内的 lint/typecheck/test: web=eslint+tsc+vitest run, session=eslint+tsc+bun test, agent=uv run pytest(asyncio_mode=auto)+ruff+pyright strict

## 7. 缺口分级与补齐计划

排序按真实风险:跨进程静默失败/数据丢失/幂等失守 > 续订边界 > HTTP 契约 > 纯渲染。

**✅ 执行记录(2026-06-13,全部清账)**:
| rank | 处置 | commit |
|---|---|---|
| 1 | dispatchRelays 抽至 application + safeParse skip(脏请求不杀循环),TDD + 真实 redis 注入实证 | session `69db1c0`+`ca20e21` |
| 2 | relayRun 单条脏事件 skip-and-continue(终态必落 replay),TDD | session `47987d3` |
| 3 | worker 模型解析入 run.failed 边界(worker 存活)+ 5 形态坏 spec parametrize,真实栈 SSE 实证 | agent `9d84e66` |
| 4 | event_id 确定性派生 `evt_{run_id}_{seq}_{event}`(重放/多副本幂等),删 newEventId 注入缝 | session `0408b86` |
| 5 | 90s 兜底退出流式 / 停止后不重连 / preview 轮零在途标记,3 用例 | web `60490c8` |
| 6 | reply.ts 降级决策层 3 用例(变异检验证非空洞) | web `60490c8` |
| 7+8 | HTTP 边界 + CORS 契约 5 用例;ZodError 穿透 500 → 400 修复 | session `c9d69d3` |
| 9 | 切换会话防串流 + 切回续传用例;**逼出并修复真实 bug:reattach effect 在 live run 中二次订阅并覆盖句柄(泄漏)** | web `60490c8` |
| 10 | use-rail-resize 钳制矩阵 + 监听清理,7 用例 | web `60490c8` |

**追加(真实 LLM e2e 逼出的核心缺陷)**:translator 丢弃带 tool_calls 的中间叙述 → 用户只见 57 字收尾句、答案实质丢失。修复为叙述独立成段浮出(多段交错 UI 即为此而建),TDD 2 用例 + 真实 LLM 复验 1501 字完整回答。agent `463e8a9`。

| rank | 流程 | 缺什么 | 风险 | 补齐动作 |
|---|---|---|---|---|
| 1 | `relay-dispatch-loop` | integration 级断言：requests 流中单条畸形 run.request 不杀死整个调度循环（或显式钉死当前 crash 行为为契约） | 一条脏请求即让 dispatchRelays 整循环 crash，此后所有新 run 永不被调度，服务静默半死——跨进程静默失败的最高危单点 | 把 /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-session/src/main.ts:21-40 的 dispatchRelays 抽为可注入 streamPort/replayStore 的导出函数，新建 kokoro-session/tests/dispatch-relays.test.ts：memory port 上先 publish 一条畸形 request（多余键），再 publish 合法 run.request，断言①循环不退出②合法 run 的 replay 流仍产出 session.created…run.completed（需先实现 per-条目 try/catch skip，用测试钉死该契约） |
| 2 | `strict-reject-no-skip` | integration 级断言：relay 消费中途遇脏 agent 事件后的终态契约（当前单条脏事件=该 run 中继永久死亡、终态永不落 replay） | 脏事件之后的 run.completed 全部丢失，web 端该轮永远卡「进行中」无超时无补偿——跨进程数据丢失+静默失败 | kokoro-session/tests/start-run.test.ts 新增用例：向 kokoro:run:{id}:events 依次 publish run.started→未知 kind 脏事件→text.completed→run.completed，await relayRun，断言期望行为——若契约为 skip-and-continue 则断言 message.completed/run.completed 仍落 replay；若保留 fail-fast 则断言 relayRun reject 且 replay 恰止于脏事件前并补发 run.failed 兜底信封（需实现） |
| 3 | `failure-run-failed-boundary` | integration 级断言：run.failed 边界外异常（make_chat_model/_build_agent/坏 KOKORO_CUSTOM_SUBAGENTS）应产出 run.failed 而非崩 worker 留悬挂 run | 坏 KOKORO_MODEL 或坏子代理配置时 worker 崩且事件流上无任何终态，session relay 与 web 看到永远悬挂的 run——跨进程静默失败 | kokoro-agent/tests/test_worker.py 新增：monkeypatch make_chat_model 抛 ValueError 后调 run_once，断言 kokoro:run:{run_id}:events 流以 run.failed（error_kind='ValueError'）收尾且循环存活（需把模型解析/_build_agent 挪入 run_agent.py:226-235 的 run.failed 边界内）；parametrize KOKORO_MODEL='plainstring'/'anthropic:'/':model' 三种畸形 spec |
| 4 | `multi-replica-fanout` | integration 级断言：进程重启/多副本重放 requests 流后 replay 出现同 (run_id,seq) 不同 event_id 的重复信封，且 web reducer 缺 (runId,seq) 兜底去重 | 重启或多副本下新 Normalizer 生成全新 event_id，web 按 eventId 去重彻底失效→历史消息双写——跨进程幂等契约失守（权重最高类） | kokoro-session/tests/start-run.test.ts：对同一 run 事件流用两个新 Normalizer 各跑一次 relayRun，断言 replay 出现重复 (run_id,seq) 且 event_id 互异（钉死现状暴露风险）；kokoro-web/tests/application/session-stream/reducer.test.ts：投喂两条同 (runId,seq) 同 kind 不同 eventId 的 message-delta，断言内容不双倍累积（钉死需实现的 (runId,seq) 兜底去重契约） |
| 5 | `web-refresh-reattach` | integration 级断言：90s 兜底超时退出 streaming、手动 stop 清 pendingInput 后不再重连、preview 降级不写 pendingInput | 续订（resume）边界失守会让用户刷新后永久卡 streaming，或对本地模拟发起幽灵重连——跨进程续订边界 | kokoro-web/tests/interfaces/session-stream/session-shell.test.tsx [reattach] 增三例：①reattach 桩不发终态，vi.advanceTimersByTime(90_000) 断言退出流式且 composer 恢复可用；②点「停止生成」后重挂载断言 reattach 调用数组为空；③POST 失败走 preview 完成一轮后重挂载断言不触发 reattach |
| 6 | `web-preview-fallback` | integration 级断言：reply.ts 的 POST 失败→fallbackToPreview 触发路径与 closed-before-settle 竞态（simulator 本体已厚测，但降级决策层零执行） | 降级是静默路径，回归（如降级轮误触发 onLive）会把本地模拟标成可重连，刷新后发起幽灵 SSE——静默失败 | 新建 kokoro-web/tests/application/session-stream/reply.test.ts：stub fetch reject 调 startSessionReply（fake timers），断言①onState 快照出现回声 assistant 且终态 runStatus=completed②onSettled('preview') 恰一次③onLive 从未被调；再测发起后同步 close()：runAllTimers 后零新增快照 |
| 7 | `http-start-run` | integration 级断言：HTTP 层错误响应契约——缺/空 input→400、非法 execution_style 当前落 500（ZodError 穿透） | 非法入参落 500 泛化错误使客户端无法区分可重试性，且该跨进程接口契约漂移时无人察觉 | kokoro-session/tests/http.test.ts 增三例：①POST /sessions/s1/runs 无 input 断言 400+{error:'missing input'}②execution_style=bogus 断言响应码（钉死 500 现状或改为 400 后更新断言）③GET 打 /runs 路径断言 404 |
| 8 | `cors-preflight` | integration 级断言：allowlist 命中回显 allow-origin+vary、非 allowlist 不回头但业务照常、OPTIONS→204 | KOKORO_WEB_ORIGIN 配错（如带尾斜杠）时浏览器全量拦截而服务端无感知，前后端联调静默失败 | kokoro-session/tests/http.test.ts 增：①带 origin: http://localhost:3000 的 GET 断言 access-control-allow-origin 回显且 vary: origin②OPTIONS 任意路径断言 204 空体③origin: http://evil.example 断言无 allow-origin 头但响应体正常 |
| 9 | `web-switch-conversation` | integration 级断言：流式中切换会话时旧流句柄被 close 且旧流事件不折进新会话；切回带 pendingInput 会话可再续传 | 防串流失守=旧 run 的 SSE 事件写入错误会话（跨会话数据串写），新建对话已有此断言但切换路径没有 | kokoro-web/tests/interfaces/session-stream/session-shell.test.tsx [sessions] 增：流式中（startReply 桩句柄未 settle）点击另一会话，断言①句柄 close 恰 1 次②目标会话 log 不含旧流内容③切回原会话时 reattach 被触发（reattachedRef 重置语义） |
| 10 | `web-rail-collapse-resize` | 全层级零测试：折叠切换、clampRail 钳制边界、拖拽监听清理 | 纯渲染交互，最坏情况是布局瑕疵（负宽/反转区间），风险最低但目前完全裸奔 | 新建 kokoro-web/tests/interfaces/session-stream/use-rail-resize.test.tsx：clampRail 参数化矩阵（200 下限/420 上限/容器极窄 max<min 时回 RAIL_MIN 绝不返负）+ session-shell 折叠态 data-rail-collapsed 下分隔条不渲染 |

---

## 7.2 item 3 补强执行记录(2026-06-14)

§7 的 10 个最高危缺口已于 2026-06-13 清账。本轮(item 3「完美测试用例」)按**价值驱动、拒绝覆盖率表演**补强剩余真实工作面:补可测的逻辑缺口、修正陈旧标记、用真实浏览器 e2e 覆盖 jsdom 测不了的部分。

**Phase A — 逻辑 partial 补测(+9)**
| 流程 | 补什么 | 文件 |
|---|---|---|
| `subagent-runtime-flow` (#55) | StructuredTool 协程本体此前零断言:新名注册+文本提取 / 同名复用既有 spec(不用调用参数,断言 runner 用已注册 prompt)/ 空输出回 '' / 无 AIMessage 回 '' / sync func 抛 RuntimeError | agent `test_runtime_subagent_protocol.py` +5 |
| `thinking-delta-flow` (#51) | 防空泡不变量:空 reasoning_content 不发 thinking.delta;有 reasoning 无正文不发空 text.stream | agent `test_run_agent.py` +2 |
| `http-routing-error-envelope` (#45) | 错误方法落 404 契约(POST /stream、DELETE /runs);非 Zod 内部错(publish 抛)落 500+message 信封 | session `http.test.ts` +2 |

**Phase B — 交互 partial 补测(+15)**
| 流程 | 补什么 | 文件 |
|---|---|---|
| `web-presentation-status` (#28) | modePresentation 纯展示映射此前零直接测试:六态(failed/idle/connecting/preview/live)× Fast/Thinking × 流式与否的文案矩阵全覆盖 | web `mode-presentation.test.ts` +15 |

**陈旧标记修正(不为旧标记 padding)**
- `replay-stream-write` (#40):start-run.test.ts 已 `replayStore.read()` 直接断言精确写入(102/127/162/188 行),partial 标记陈旧 → 实为 covered。
- `model-resolution-flow` (#58):默认/自定义/thinking effort/fake/非法 + 畸形 ×5 已充分 → 实为 covered。
- `worker-main-loop` (#46):run_once 批量排空已覆盖(#47 ✅);main_loop 是 `while True` 无限 glue,不写 flaky 测试。

**Phase C — Playwright MCP 真实浏览器 e2e**(覆盖 jsdom 测不了的真实渲染/交互;用 MCP 插件驱动,非 committed 套件)
隔离栈 web :3100 → session :3002 → redis db10 → fake worker,逐项实证:
- 发送 → **live 流式**(transport「实时会话已连接」)→ 落定;过程块「处理过程·2 个工具」+ 工具行 `now` + 计划 1/2;首条后模式锁「Fast(本轮已锁定)」;会话入侧栏 + 自动标题。
- **autoresize**:textarea 31.5px→80px(真实换行布局,jsdom 不可测)。
- **刷新持久化 + SSR 水合首帧**:reload 后无 hero、thread 从 localStorage 复原。
- **rail 折叠**:data-rail-collapsed=true + 分隔条不渲染(#13)。
- **交叉验证**:真实 UI 的 transport label(idle+!msg→「等你发出首条消息」/ live→「实时会话已连接」/ idle+msg→「已准备继续」)与 Phase B 的 modePresentation 单测矩阵逐条吻合。
- 纪律:测后清 demo localStorage;全程未碰用户 :3000/:3001/db0/db14。

**基数**:agent 133→**140** · session 76→**78** · web 221→**236**;三仓 typecheck/lint/test + agent pyright/ruff 全绿。

---

## 8. 运行手册

| 层 | 命令 | 前置 |
|---|---|---|
| agent 单元 | `cd kokoro-agent && uv run pytest`(完跑 `git checkout uv.lock`) | uv |
| agent 类型 | `uv run pyright` + `uv run ruff check` | — |
| session 单元/集成 | `cd kokoro-session && bun test && bun run typecheck` | bun |
| web 单元/集成 | `cd kokoro-web && bun run test && bun run typecheck && bun run lint` | bun |
| 契约门禁 | `python3 contract/verify.py` | — |
| SSE 回环门禁 | `scripts/sse-loopback-gate.sh` | redis + 隔离 db + session :3002 + worker(LOCAL_FAKE_MODEL) |
| 真实 LLM 冒烟 | 全栈拉起(web/session/worker,.env 网关凭据)+ Playwright 主路径 | .env、隔离 redis db、空闲端口 |

**e2e 隔离纪律**:用户在跑的 `:3001`(session)/`:3000`(web)与 redis **db0(真实数据,永不 flush)** 一律不碰;e2e 用 `:3002`/`:3100` + 空 redis db(10+)。
