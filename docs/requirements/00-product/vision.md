---
status: 🟡 草稿
layer: product
owner: claude
updated: 2026-06-14
refs:
  - ADR-001
  - ADR-004
---

# 产品定位与北极星

> 一句话:这篇钉住「Kokoro 是什么、为谁、用什么指标衡量成功」,作为下游所有需求的前提。不复制 product/ 愿景细节,只取需求相关前提。

## 定位

**Kokoro(こころ)= 一个有人格的通用 AI agent,主战场是把「想法」变成可分享的产物,气质柔、温、内观。**

需求前提(从中派生能力/流程要求):
- **agent,不是单轮问答**:产品的内核是一个**会规划、会用工具、会派子代理**的执行体。UI 必须如实呈现它的「活动」——计划、工具、子代理、思考(见 [01-capabilities/agent-activity.md](../01-capabilities/agent-activity.md))。
- **慢一点、一起做**:强调过程可见、可中断、可续接,而非一次性吐结果。流式连续性与中断恢复是一等需求(见 [streaming](../01-capabilities/streaming.md) / [resume](../01-capabilities/resume.md))。
- **产物可分享**:北极星指向「产出物的传播」,而非停留时长。

## 北极星

**WAS = 周活跃产物分享数**(链 [ADR-004](../../decisions/ADR-004-north-star-metric.md))。

对需求的约束:
- 任何能力以「是否帮用户更快产出**可分享的产物**」为优先级标尺。
- 当前真实系统尚未落地「产物(canvas)」层(见 [scope-and-boundary](./scope-and-boundary.md)),北极星目前由**基础对话/agent 执行质量**间接支撑;产物分享是已规划方向。

## 引用

- 人格定调:[ADR-001](../../decisions/ADR-001-product-personality.md) · [docs/product/02-personality/](../../product/02-personality/)
- 北极星定义:[ADR-004](../../decisions/ADR-004-north-star-metric.md)
- 愿景全文(参考,不继承):[docs/product/00-overview/vision.md](../../product/00-overview/vision.md)
