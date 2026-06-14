---
status: 🟡 草稿
layer: capabilities
owner: claude
updated: 2026-06-14
refs:
  - test:web-todo-bar
  - test:web-tool-call-display
  - test:web-subagent-display
  - test:web-process-disclosure
  - test:todo-flow
  - test:subagent-task-flow
---

# 能力 · agent 活动流

> 一句话:如实、可读地呈现 agent 在做什么——计划、工具、子代理、思考。这是产品内核「它是 agent 不是问答」的 UI 兑现。

## 需求

- **R1 计划(todo)**:agent 的 `write_todos` **必须**映射为可见的计划条,钉在输入框上方,逐项状态(待办/进行中 ◉/完成 ✓)随 `todo.updated` 更新。
- **R2 工具调用**:每次工具调用**必须**渲染一行,呈现三态:running / done / error。错误态显红 + 错误文本。
- **R3 子代理**:`task` 工具派出的子代理**必须**成行展示,标注来源(built-in / config-custom / runtime-custom),其结论可流式呈现。
- **R4 思考**:Thinking 风格下的推理流(`thinking.delta`)应当可呈现,且可折叠(过程块披露)。
- **R5 可读性**:活动呈现面向**非工程用户**——用自然语言摘要,不是裸 JSON/调试日志(见 [users-and-jobs](../00-product/users-and-jobs.md))。
- **R6 披露持久**:过程块(思考/工具/子代理)的展开/折叠意图按 segment 持久,刷新保留。

## 验收

- [ ] todo 条随 `todo.updated` 逐项更新(`test:web-todo-bar` / `test:todo-flow`)
- [ ] 工具行三态正确,error 显红 + 文本(`test:web-tool-call-display`)
- [ ] 子代理行 + 来源解析 + 结论流式(`test:web-subagent-display` / `test:subagent-task-flow`)
- [ ] 过程块折叠/展开 + 刷新保留意图(`test:web-process-disclosure`)

## 不做 / 边界

- 工具执行前的**暂停/确认**(HITL)= 🔲 未实现,见 [extension-points](./extension-points.md)。
- 活动流的渲染如何与文本答案分段交错 → 见 [streaming](./streaming.md)。

## 引用

- 流程:[tool-run](../02-flows/tool-run.md)
- 契约:13 kind 中的 `todo.updated` / `tool.invoked` / `tool.returned` / `subagent.*` — [stream 架构 §3](../../superpowers/specs/2026-06-11-stream-event-architecture-spec.md)
