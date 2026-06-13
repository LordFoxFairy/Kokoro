---
status: 🟡 草稿
layer: flows
owner: claude
updated: 2026-06-14
refs:
  - test:tool-event-flow
  - test:web-tool-call-display
  - test:subagent-task-flow
  - test:todo-flow
---

# 流程 · 工具调用 → 渲染 → 错误

> 主路径:agent 调工具/派子代理,调用与结果如实成行,失败显红。

## 前置

- 一个会触发工具/子代理的请求(如「查一下时间」→ `now`,「抓取某页」→ `fetch_url`,复杂任务 → `task` 子代理)。

## 验收

**T1 工具成对事件**
- Given agent 决定调用工具
- When 执行
- Then 产 `tool.invoked`(含 args)+ `tool.returned`(含 result + `is_error`)成对;web 渲染工具行 running→done(`test:tool-event-flow` / `test:web-tool-call-display`)

**T2 工具失败**
- Given 工具抛错
- When agent 走 on_tool_error
- Then `tool.returned` 带 `is_error: true` + result 为错误文本(空异常回落类型名);web 工具行显红 + 错误面板;段摘要聚合「N 个工具(K 失败)」(`test:web-tool-call-display`)

**T3 子代理**
- Given `task` 工具派子代理
- When 子代理执行
- Then 子代理行展示 + 来源解析(built-in/config-custom/runtime-custom);结论流式;失败发 `subagent.finished` 不留卡死行(`test:subagent-task-flow`)

**T4 todo 联动**
- Given agent 调 `write_todos`
- When `todo.updated` 到达
- Then 计划条逐项状态更新(`test:todo-flow`)

## 边界

- 工具执行前的**确认/暂停**(HITL)= 🔲 未实现,见 [extension-points](../01-capabilities/extension-points.md)。

## 引用

- 能力:[tools](../01-capabilities/tools.md) · [agent-activity](../01-capabilities/agent-activity.md)
