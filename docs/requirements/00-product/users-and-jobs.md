---
status: 🟡 草稿
layer: product
owner: claude
updated: 2026-06-14
refs:
  - ADR-002
---

# 目标用户与核心 Jobs

> 一句话:谁在用、来完成什么任务。下游能力/流程的优先级由这里的 JTBD 排序。

## T0 用户(链 [ADR-002](../../decisions/ADR-002-target-users.md))

**内容创作者 + 新手创业者**。共性:有明确产出意图、缺工程/工具链能力、要快且要「能发出去」。

需求约束:
- **零配置心智**:普通用户**看不到**模型/Key/参数等工程概念(模型配置是管理员的事)。对需求的影响——面向用户的流程不得暴露 provider/模型内部;模式只暴露为「信任档位」(见 [trust-modes](./trust-modes.md))。
- **过程要可读**:非工程用户也要能看懂 agent 在干什么 → 活动流的可读性(计划/工具/子代理用自然语言摘要)是硬需求,不是工程调试视图。

## 核心 Jobs(JTBD)

| Job | 用户说法 | 对应能力 |
|---|---|---|
| J1 把一个想法交给它去做 | 「帮我做一份 X」 | [conversation](../01-capabilities/conversation.md) + [agent-activity](../01-capabilities/agent-activity.md) |
| J2 看着它做、随时插手 | 「它做到哪了 / 停一下」 | [streaming](../01-capabilities/streaming.md) + [resume](../01-capabilities/resume.md) |
| J3 让它去查/取外部信息 | 「查一下最新的…」 | [tools](../01-capabilities/tools.md) |
| J4 同时推进多件事 | 「另开一个聊聊别的」 | [conversation](../01-capabilities/conversation.md)(多会话) |
| J5(规划)拿到产物并分享 | 「导出 / 发出去」 | 扩展位:[extension-points](../01-capabilities/extension-points.md) |

## 引用

- 目标用户决策:[ADR-002](../../decisions/ADR-002-target-users.md)
- 用户/价值细节(参考):[docs/product/01-strategy/](../../product/01-strategy/)
