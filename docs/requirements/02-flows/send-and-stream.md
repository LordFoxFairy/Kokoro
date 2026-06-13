---
status: 🟡 草稿
layer: flows
owner: claude
updated: 2026-06-14
refs:
  - test:web-send-message
  - test:web-segment-interleaving
  - test:text-stream-flow
  - test:segmenter-flow
  - test:run-lifecycle
---

# 流程 · 发送 → 流式作答 → 落定

> 主路径:用户提交 → agent 执行 → 事件流 → 边生成边渲染 → 落定。

## 前置

- 三仓在跑(web ↔ session ↔ agent),或本地预览降级(见 [degrade-and-reject](./degrade-and-reject.md))。
- 一个已选中会话。

## 验收

**S1 提交**
- Given 一个非空 composer 输入
- When 用户按 Enter / 点发送
- Then 出现用户气泡;进入流式态;在途时再次提交被守卫挡(`test:web-send-message`)

**S2 run 生命周期与排序**
- Given 提交触发一个 run
- When agent 产出事件
- Then session 合成 `session.created`+`run.created`(共享 seq);后续领域事件 per-run `seq` 严格递增;web 按 seq 排序渲染(`test:run-lifecycle` / `test:synthetic-session-run-created`)

**S3 文本流式**
- Given 模型流式产出
- When `text.delta` 持续到达
- Then 文本累积渲染 + caret;`text.completed` 落定;非流式模型 delta+completed 成对(`test:text-stream-flow`)

**S4 多段交错**
- Given agent 产出 `text → tool → text` 序列
- When 第三段仍在生成
- Then 分段不塌缩:工具行挂在其产出的答案段下;首 token 不跳盒(forming→streaming→settled 同骨架)(`test:web-segment-interleaving` / `test:segmenter-flow`)

**S5 落定**
- Given run 结束
- When `run.completed` 到达
- Then 流关闭;最终 thread 稳定;caret 消失

## 边界

- 工具失败分支 → [tool-run](./tool-run.md);中途刷新 → [interrupt-resume](./interrupt-resume.md)。

## 引用

- 能力:[conversation](../01-capabilities/conversation.md) · [streaming](../01-capabilities/streaming.md) · [agent-activity](../01-capabilities/agent-activity.md)
- 契约:[session-stream](../../protocol/session-stream.md)
