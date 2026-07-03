# Agent 自身完善：RuntimeContext 注入 / subagent_create 执法 / memory store（2026-07-03）

> 用户定调：聚焦三仓，agent 重点完善自身，web 冻结，music/platform 后置。
> 缺口对照 handbook V1（technical/11+12、modules/kokoro-agent）坐实；create_deep_agent
> 原生支持 context_schema 与 store（已实证签名）。

## A. RuntimeContext 注入图运行时（11 号明文）

- run/context.py 的 RunContext（namespace/session_id/run_id/thread_id）作 `context_schema`；
  build_agent 增 `context_schema` 参数，main 传入。
- 每 run 的 context 值在 invoke/resume 时随调用注入（langgraph v1 的 runtime context：
  invoke/stream 的 `context=` kwarg；需实证 astream_events 是否透传，不透传则走
  `config` 或 durability 等替代——**先实证再定**）。
- 消费面：工具/middleware 经 `ToolCallRequest.runtime.context` 读取（现 ToolPolicyMiddleware
  的 _runtime 已有该字段位）；这是将来"前置改参按用户时区"的基座。
- 验收：middleware 单测断言拦截时能读到 namespace/session_id；e2e 不回归。

## B. subagent_create 策略执法（12 号：deny|ask|allow，默认 deny）

- **deny**：ToolPolicyMiddleware 拦 `task` 调用——请求的 subagent 类型不在 catalog 声明集
  （含 deepagents 默认 general-purpose）→ fail-closed 错误结果，模型可感知换路。
- **ask**：`task` 加入 interrupt_on（委派参数走现有审批卡，零新 UI）。
- **allow**：放行任意（含 general-purpose 临时委派）。
- 声明集 = catalog.definitions() + wire subagents 名单；策略源 = runtime.permissions.subagent_create。
- 验收：三档行为矩阵 + deny 下声明内子代理仍可用 + e2e 不回归。

## C. 长期记忆 store 接线（模块文档 Owns memory；kokoro_agent_memory{namespace,...}）✅

- `create_deep_agent(store=...)`：InMemoryStore（测试）/持久后端按 checkpoint backend 对齐
 （sqlite/mongo 的 langgraph store 可用性**先实证**，不可用则 V1 只接 InMemory + 注记）。
- namespace 隔离：store 命名空间前缀 = RunContext.namespace（跨租户不可见断言）。
- 验收：跨 run 同 session 记忆可读、双 namespace 隔离。

## 顺序与纪律

A → B → C 串行，各自门禁全绿即提交推送；e2e 每步回归；handbook 实现注记随做随补。
web/session 零改动（wire 已有全部所需字段）。
