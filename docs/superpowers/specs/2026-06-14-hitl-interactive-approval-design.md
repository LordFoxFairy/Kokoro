# HITL 交互式确认设计 — 工具调用暂停→确认→恢复

> 定位:把 HITL 从「确定性拦截」升级为真·human-in-the-loop——被门控的工具调用时**暂停**,前端弹出**批准/拒绝**,用户决定后**恢复**(approve 跑真工具 / reject 回拒绝)。
> 用户拍板:进交互式确认,自主全面完成。

## 架构:in-tool 阻塞(避开 checkpointer/resume 重编排)

不用 LangGraph `interrupt_on`+checkpointer(那需要 worker 暂停 run + 后续 resume 再编排,run 生命周期变多段)。改用 **in-tool 阻塞**:被门控工具的协程内 **await control 流的决定**,run 保持单条 astream(工具内挂起),无需 checkpointer、无需 worker resume 编排。

```
工具被调用 → translator emit tool.invoked + tool.awaiting_approval（on_tool_start）
          → 工具协程阻塞读 kokoro:run:<id>:control（带超时）
web 显示批准/拒绝 → POST /runs/:id/control?decision=approve → session 写 control 流
          → 工具协程收到决定 → approve: 跑真工具 / reject: 回「用户拒绝」
          → on_tool_end → tool.returned（真实结果 或 拒绝语）
```

- 单工具同时至多一个待批(agent 顺序执行),control 消息无需 tool_call_id 匹配。
- 超时(默认 90s 无决定)→ 回退 reject,避免永久挂起(且 astream 120s 总超时兜底)。
- **降级**:无 control_port(单元测试/未接入)时回退到确定性 deny(现有行为),互不破坏。

## 契约(走 codegen SOP)

events.yaml 加 1 个 kind `tool.awaiting_approval`:
- agent_out / agui_out payload: `[segment_id, tool_id, name, args]`;render: `tool-awaiting-approval` `[segmentId, toolId, name, args]`。
- `generate.py` 重生成 5 镜像;verify 自动纳入。结果(approve/reject)复用现有 `tool.returned`(reject 时 is_error 视情)。

## 分层

1. **契约**:events.yaml + generate + verify。
2. **agent**:`infrastructure/control.py`(读 control 流首条决定,超时回退)+ `permission.py` 交互式 gate(emit awaiting 由 translator 据 blocked 集做;工具协程阻塞)+ `run_agent`/worker 透传 `control_port`。
3. **session**:control 流常量 + `POST /sessions/:id/runs/:rid/control?decision=` → `streamPort.publish(controlStream(runId), {decision})`。
4. **web**:transport/reducer 处理 `tool-awaiting-approval`→工具 status `awaiting`;tool-call-row 批准/拒绝按钮 → `POST control`;transport 加 sendControl。

## 验收（✅ 全部达成）

- [x] 契约新 kind 全 5 镜像生成 + verify + generate --check 绿（14 kinds）。
- [x] agent:control 可用时被门控工具阻塞待批;approve 跑真工具、reject 回拒绝、超时回退;无 control 时确定性 deny(回归不破)。157 pytest（含 test_control）。
- [x] session:POST control 写流;agent 工具读到。82 bun test。
- [x] web:awaiting 渲染批准/拒绝;点击 POST control。240 vitest。
- [x] 三仓门禁绿 + **真实 LLM e2e 实证**:plan 模式真模型调 fetch_url → tool.invoked + tool.awaiting_approval（run 暂停）→ POST approve → tool.returned 真实 HTML `<title>Example Domain</title>` + run.completed（模型答出标题）;reject 对照 → tool.returned「用户拒绝」+ 模型适应。暂停→approve 真跑 / reject 真拒，双向端到端证实。

## 边界
- 单 worker 顺序:一个 run 待批时该 worker 阻塞(单用户/demo 可接受;多并发 worker 各自独立)。
- 本轮覆盖**注入工具**(fetch_url/runtime-agent)的交互式审批;deepagents **内部工具**(write_file 等)见下方 follow-up。

## Follow-up:deepagents 内部工具的交互式审批（机制已探明，执行就绪）

**结论(2026-06-14 决定)**:内部工具暂维持**确定性门控**(plan `fs_permissions` 只读已落地+真机验);**交互式**审批列为专注的下一件——它走的是与注入工具**不同的机制**(LangGraph 中断,非 in-tool 阻塞),需重构核心 run 循环,intricate 且 fake model 无法触发(只能真机验),价值/风险比不宜在长会话尾部仓促做。

**已用真机探针探明的确切机制**(可直接据此实现):
- `create_deep_agent(interrupt_on={"write_file": True, "edit_file": True}, checkpointer=InMemorySaver())` + astream 配 `config={"configurable": {"thread_id": run_id}}`。
- 命中 interrupt_on 工具时 astream **正常结束**(不抛、暂停在工具**之前**,无 on_tool_start);
  `await agent.aget_state(config)` → `state.interrupts[0].value["action_requests"]` = `[{"name","args","description"}]`(待批工具名+参数);`state.next` 非空表暂停。
- 恢复:`agent.astream_events(Command(resume={"decisions": [{"type": "approve"|"reject"}]}), ...)` 续跑;approve → 工具真执行(on_tool_end「Updated file …」),reject → 中间件告知模型被拒。

**实现设计**(单条逻辑 run、多段 astream):
1. **seq 连续**:把 drive_agent_events 的 `nxt`/`_Segmenter` 抽成可跨段共享(或提取 `_EventMapper`),run.started/completed 只首尾各一次,run.failed 任段异常即发。
2. **resume 循环**(run_agent):`while True: astream 段 → aget_state 取中断 → 有则 emit tool.invoked(synth_id)+tool.awaiting_approval(synth_id) 据 action_requests → await control 决定 → emit tool.returned(synth_id, 已批准/已拒绝) → Command(resume) 续 → 无中断则 break → run.completed`。
3. **事件表征**(避开 id 阻抗,选其一):① 2 行(awaiting 行 + resume 真执行行,简单稳健,略冗余);② 1 行(suppress resume 的 tool.invoked + 按工具名 remap tool.returned 到 synth_id,干净但需名匹配)。
4. **模式语义**:plan 写操作保持硬 deny(只读规划);default 写操作 → interrupt_on(交互审批);auto 放行。
5. 验收:真实 LLM e2e——default 写文件→awaiting→approve 真写/reject 真拒。
