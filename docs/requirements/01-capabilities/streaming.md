---
status: 🟡 草稿
layer: capabilities
owner: claude
updated: 2026-06-14
refs:
  - test:web-segment-interleaving
  - test:text-stream-flow
  - test:segmenter-flow
  - test:web-scroll-follow
  - test:thinking-delta-flow
---

# 能力 · 流式呈现

> 一句话:作答边生成边显示,连续不跳;文本/工具/文本交错时分段归属正确。「慢一点、一起做」的核心兑现。

## 需求

- **R1 token 流式**:文本以 `text.delta` 累积、`text.completed` 落定;非流式模型回退时 delta+completed 成对发出,行为对齐。
- **R2 分段不塌缩**:`tool → text → tool → text` 序列**必须**保持分段,不得塌缩成一段。工具挂在它所产出的那段答案之下(文本块 complete 后,下一个工具开新段)。
- **R3 三相位连续**:同一段答案经历 forming(工具已到、文本未到 → 成形占位)→ streaming(文本流式 + caret)→ settled(落定),且**首 token 不跳盒**(forming/streaming/settled 共享同一气泡骨架)。
- **R4 排序唯一源**:渲染顺序**只**由 `seq` 决定(per-run 非递减),不得依赖到达顺序或反解游标。
- **R5 滚动吸附**:流式中视图吸附跟随最新;用户上滚后出现「回到最新」,不强拽。
- **R6 思考流**:Thinking 风格下 `thinking.delta` 可流式呈现于过程块。

## 验收

- [ ] 多段交错渲染归属正确,工具在其答案段下(`test:web-segment-interleaving` / `test:segmenter-flow`)
- [ ] text.delta 累积 → completed 落定;非流式成对(`test:text-stream-flow`)
- [ ] forming→streaming→settled 首 token 不跳盒(`test:web-segment-interleaving` 覆盖布局)
- [ ] 吸附跟随 + 回到最新(`test:web-scroll-follow`)
- [ ] thinking.delta 呈现(`test:thinking-delta-flow`)

## 不做 / 边界

- 续传/重连后的去重收敛 → 见 [resume](./resume.md)。
- seq 升格为一等字段、删除域 cursor = 架构目标态(item 4),见 [stream 架构 §2](../../superpowers/specs/2026-06-11-stream-event-architecture-spec.md)。

## 引用

- 流程:[send-and-stream](../02-flows/send-and-stream.md)
- 设计:[multi-segment-assistant-stream](../../superpowers/specs/2026-06-06-multi-segment-assistant-stream-design.md) · [stream-continuity](../../superpowers/specs/2026-06-13-stream-continuity-design.md)
