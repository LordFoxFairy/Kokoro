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

- **Plan**:**交互审批**——执行,但敏感工具(外部网络 fetch、子代理 task 等)调用时**暂停等用户批准**(approve/reject/cancel),逐个放行。**不是只读、不是「只规划不执行」**(语义 2026-06-20 定）。
- **Default**:正常执行,敏感集(requires_approval)同样走暂停审批,Plan 在其上再加严(plan_only_blocked_tools)。
- **Auto**:充分自主,不拦。

> ⚠️ 执行风格 Fast/Thinking 是另一维(见下)。**信任档位的 HITL 工具审批已落地**:control 协议(approve/reject/cancel)+ 交互门控 `gate_tools_interactive` + web 审批 UI。**FS 写暂不可审批化**(deepagents 文件系统中间件仅 allow/deny、无 ask),故 Plan 下 FS 写放行;若需 FS 写也审批属后续(须把写工具纳入可门控集）。

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

- Plan/Default 的**工具暂停/批准/取消** = HITL,**已建**(control 协议 + 交互门控 + web 审批 UI,2026-06-20);中断恢复见会话流(replay/resume）。Auto 不拦。

## 引用

- Mode 决策:[ADR-003](../../decisions/ADR-003-mode-model.md)
- 模式与执行风格契约:[docs/protocol/modes-and-execution-style.md](../../protocol/modes-and-execution-style.md)
