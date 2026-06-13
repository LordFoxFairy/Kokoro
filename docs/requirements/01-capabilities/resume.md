---
status: 🟡 草稿
layer: capabilities
owner: claude
updated: 2026-06-14
refs:
  - test:web-refresh-reattach
  - test:web-sse-transient-reconnect
  - test:sse-resume-last-event-id
  - test:resume-cursor-guard
  - test:seq-dedup
---

# 能力 · 中断恢复

> 一句话:流式中刷新或瞬断,不丢、不重、不卡——重连续传补完。

## 需求

- **R1 瞬断自动重连**:SSE 瞬断时浏览器按规范带 `Last-Event-ID` 自动重连,**增量**续传;到达的事件按 `event_id` 幂等去重,不重复渲染。
- **R2 刷新 reattach**:页面刷新后,对在途 run **必须**重新订阅(新 EventSource,无 header → 全量重放 + 去重),把半截答案补完,而非卡死或丢失。
- **R3 续点守卫**:`Last-Event-ID` 仅传输游标格式(`^\d+(-\d+)?$`)放行;畸形/缺失 → 全量重放 + `eventId` 去重兜底,**绝不静默空流**。
- **R4 幂等**:`(run_id, seq)`(session)+ `eventId`(web)双重去重,重连/重放收敛到同一 thread。
- **R5 重连可辨**:重连进行中 UI **必须**给出可辨提示(turn 级「重连中…」),让用户区分「在重连」与「卡死」。

## 验收

- [ ] 流式中刷新 → reattach 续传补完(`test:web-refresh-reattach`)
- [ ] 瞬断 → Last-Event-ID 增量 + 去重(`test:web-sse-transient-reconnect` / `test:sse-resume-last-event-id`)
- [ ] 畸形续点 → 全量 fallback 不空流(`test:resume-cursor-guard`)
- [ ] 重放同 run 不产重复(`test:seq-dedup`)

## 不做 / 边界

- XTRIM 裁剪导致续点失效的空流检测 = 目标态补强(item 4),见 [stream 架构 §4](../../superpowers/specs/2026-06-11-stream-event-architecture-spec.md)。

## 引用

- 流程:[interrupt-resume](../02-flows/interrupt-resume.md)
- 契约:[session-replay-and-resume](../../protocol/session-replay-and-resume.md)
