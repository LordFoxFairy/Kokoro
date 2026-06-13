---
status: 🟡 草稿
layer: product
owner: claude
updated: 2026-06-14
refs:
  - ADR-003
  - test:web-mode-select-lock
---

# 信任档位(Mode)

> 一句话:Mode 表达「对 Kokoro 的信任档位」,不是任务类型 tab。这篇钉住面向用户的模式语义与对需求的约束。

## 决策前提(链 [ADR-003](../../decisions/ADR-003-mode-model.md))

**不做 Chat / Canvas / Agent 顶部三态 tab**。任务类型隐式自动触发。Mode 借鉴 Claude Code permission mode 哲学,表达信任档位:

- **Plan**:只规划、不执行,用户审阅后放行。
- **Default**:正常执行,关键动作可能确认。
- **Auto**:充分自主,少打断。

> ⚠️ 三档是**对外叙事 / 已设计**;真实系统当前落地的是 **Fast / Thinking 执行风格**两档(见下)。信任档位的完整 Plan/Default/Auto 行为(尤其确认/暂停)依赖 [HITL 扩展位](../01-capabilities/extension-points.md),**未实现**。

## 已建:执行风格两档(Fast / Thinking)

真实系统暴露并锁定的是**执行风格**,映射到模型解析:
- **Fast**:快速直答风格。
- **Thinking**:带推理流(thinking.delta)的深思风格。
- 选择后在会话内**锁定**(锁定后不可中途改),composer 下常驻提示当前档位。

需求约束:
- 模式选择**不得**暴露 provider/模型名(用户零配置心智,见 [users-and-jobs](./users-and-jobs.md))。
- 锁定语义必须在 UI 明确(已锁 → 禁用切换)。

验收:`test:web-mode-select-lock`(测试总目录)。

## 边界

- Plan/Default/Auto 的**确认/暂停/恢复**语义 = HITL,属 🔲 已规划,见 [extension-points](../01-capabilities/extension-points.md)。本篇不描述其为已建。

## 引用

- Mode 决策:[ADR-003](../../decisions/ADR-003-mode-model.md)
- 模式与执行风格契约:[docs/protocol/modes-and-execution-style.md](../../protocol/modes-and-execution-style.md)
