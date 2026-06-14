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
- deepagents 内部工具(write_file 等)的交互式审批同理可扩(本轮先覆盖注入工具 fetch_url/runtime-agent;fs 的确定性只读门控已落地)。
