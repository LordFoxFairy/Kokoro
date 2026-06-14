---
status: 🟡 草稿
layer: flows
owner: claude
updated: 2026-06-14
refs:
  - test:web-refresh-reattach
  - test:web-sse-transient-reconnect
  - test:sse-resume-last-event-id
  - test:resume-cursor-guard
  - test:seq-dedup
---

# 流程 · 刷新 / 瞬断 → 重连续传

> 主路径:在途 run 期间连接断了,系统补完而非丢失。

## 前置

- 一个**在途**(未落终态)的 run 正在流式。

## 验收

**R1 瞬断自动重连**
- Given SSE 连接瞬断
- When 浏览器(同 EventSource)按规范带 `Last-Event-ID` 重连
- Then 从续点**增量**续传;到达事件按 `event_id` 去重不重复渲染(`test:web-sse-transient-reconnect` / `test:sse-resume-last-event-id`)

**R2 刷新 reattach**
- Given 流式中用户刷新页面
- When 新 EventSource 无 Last-Event-ID 订阅在途 run
- Then **全量重放 + 去重**补完半截答案;UI 显「重连中…」可辨提示,不卡死、不丢失(`test:web-refresh-reattach`)

**R3 畸形续点 fallback**
- Given `Last-Event-ID` 畸形或缺失
- When 续点守卫校验(`^\d+(-\d+)?$`)
- Then 不放行增量 → 全量重放 + `eventId` 去重兜底,**绝不静默空流**(`test:resume-cursor-guard`)

**R4 幂等收敛**
- Given 同 run 被重放
- When session `(run_id, seq)` 去重 + web `eventId` 去重
- Then thread 收敛到唯一正确序列,无重复(`test:seq-dedup`)

## 边界

- XTRIM 裁剪致续点失效的空流检测 = 目标态补强(item 4)。

## 引用

- 能力:[resume](../01-capabilities/resume.md)
- 契约:[session-replay-and-resume](../../protocol/session-replay-and-resume.md) · [stream 架构 §4](../../superpowers/specs/2026-06-11-stream-event-architecture-spec.md)
