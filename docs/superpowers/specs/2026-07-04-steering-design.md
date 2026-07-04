# Steering（运行中插话）预研设计（2026-07-04，提案待批）

> 状态：机制已想透、未实施。CC 的"跑着的时候还能说话"对标件；当前活跃 run 撞 409（V1 故意）。

## 机制（agent 侧，全部现有件组合）

- **插话信箱**：RunStateStore 增 `add_steer(run_id, message_id, content)` / `drain_steers(run_id)`
  （keep-first 幂等，同 tool_results 模式；跨 worker 崩溃收养天然生效）。
- **SteeringMiddleware.abefore_model**：每次模型调用前 drain 信箱，非空则把插话作为
  HumanMessage 追加进本轮 messages——**模型轮粒度**的协作式转向，不打断图、不丢状态。
- 注入同时发既有 `message.*` 事件面向 web 渲染？不——插话本身由 session 落库为用户消息
  （见下），agent 只负责"下一模型轮可见"。
- HITL 暂停中的插话：现有 resume 已支持带内容的 respond；暂停态信箱同样在 resume 后
  首个模型轮生效——零特例。

## 契约与 session（产品面，待用户拍板后另单实施）

- control 增 `run.steer {message_id, content}`（decision_id 幂等同款）；或 POST messages
  在活跃 run 时语义从 409 改为"落库+转 steer"——**推荐后者**（用户无感，消息史自然）。
- web 输入框在 run 活跃时不再置灰。

## 边界与不做

- 插话不中断当前工具执行（工具原子性）；只影响后续模型轮。
- 不做"撤回已插话"；不做多条插话合并语义（按序全部注入）。

## 验收（届时）

- 单测：信箱幂等/顺序/跨段；middleware 注入时机矩阵。
- 跨栈：活跃 run 中 POST → 下一模型轮响应转向；HITL 暂停中插话 → resume 后生效。
- 真模型：长任务中途改需求，产出反映转向。
