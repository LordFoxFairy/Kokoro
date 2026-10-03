# Kokoro 产品手册

> 项目状态：研发与系统验收推进中；未验功能不标完成
> 起草时间：2026-05-20
> 维护方式：每个主题一个子目录、多个聚焦的小 md，方便后续逐节复查与修订
> 本文件 = 总索引


## 当前入口（2026-10-03）

研发以用户已确认的 [核心流程](03-product-form/core-flows.md#当前研发验收基线2026-10-03)、[会话/项目/任务导航](04-architecture/navigation.md)、[Home](06-screens/home.md) 与 [聊天](06-screens/chat.md) 当前基线为准。Root [task](../task.md)/[progress](../progress.md)/[测试台账](../test-cases.md) 分别维护派工、实际证据和完整70组验收；本手册不建立第二计划中心。

2026-05的增长、视觉与模式正文仍为历史草稿/当时决策，不得覆盖后续用户确认、当前owner三设计或机器契约。ChatGPT/Manus交互是本轮对齐参照，成熟组件优先，不以历史竞品评价或ASCII布局替代现浏览器验证。并行按真实依赖拆分，而不是让PRD/系统QA/业务CRUD等待整个Agent完工。

---

## 导览

| 章节 | 内容 | 当前状态 |
|---|---|---|
| [00-overview](./00-overview/) | 一页纸、愿景、定位、术语表 | 🟡 部分填充 |
| [01-strategy](./01-strategy/) | 目标用户、价值主张、差异化、增长引擎、商业模式 | 🟡 部分填充 |
| [02-personality](./02-personality/) | 人格定调、Voice & Tone、视觉语言、品牌资产 | 🟢 主体已定（[ADR-001](../decisions/ADR-001-product-personality.md)） |
| [03-product-form](./03-product-form/) | 产品形态、核心流程、功能地图、Canvas 主打类型 | 🟡 形态已定，细节待填 |
| [04-architecture](./04-architecture/) | IA、导航、模式、记忆与上下文、权限层级、三主仓运行时链路 | 🟡 框架已定 |
| [05-design-system](./05-design-system/) | tokens、组件、动效、交互模式 | 🔴 待填（待人格视觉细化） |
| [06-screens](./06-screens/) | 首屏、对话、Canvas、分享、模板、库、设置 | 🔴 待填（待 IA 锁定） |
| [07-growth](./07-growth/) | 引擎拆解、分享一等公民、模板市场、病毒循环、指标 | 🟢 框架已定 |
| [08-extensibility](./08-extensibility/) | Skills、命令、插件、MCP | 🟡 框架已定（重度参考 Claude Code） |
| [09-safety](./09-safety/) | 权限模型、隐私、护栏、熔断器 | 🟡 框架已定（重度参考 Claude Code） |
| [99-references](./99-references/) | 内外部参考文档索引 | 🟡 维护中 |

---

## 状态标记规范

每个文件顶部 frontmatter 须含 `status` 字段：

- 🟢 **已定**（locked）— ADR 锁定或用户已拍板，改动需新 ADR
- 🟡 **草稿**（draft）— Claude 已起草，等用户审阅修订
- 🔴 **待你拍板**（pending-user）— 内容空或只有问题清单，需用户输入

---

## 决策记录（ADR）

重要决策记到 [`../decisions/`](../decisions/)，本手册章节通过链接引用回去。

- [ADR-001 · 产品人格定位：「心」路线](../decisions/ADR-001-product-personality.md)
- [ADR-002 · 目标用户：T0 = 内容创作者 + 新手创业者](../decisions/ADR-002-target-users.md)
- [ADR-003 · Mode 模型：信任档位（Plan / Default / Auto）](../decisions/ADR-003-mode-model.md)
- [ADR-004 · 北极星指标：WAS（周活跃产物分享数）](../decisions/ADR-004-north-star-metric.md)
- [ADR-005 · 商业模式：freemium + 创作者 Pro](../decisions/ADR-005-business-model.md)
- [ADR-006 · 主色板：A（米+木）](../decisions/ADR-006-color-palette.md)
- [ADR-007 · 原型 = 设计 spec；生产另起真栈（Next.js + shadcn + Tailwind 4）](../decisions/ADR-007-prototype-and-production-stack.md)

---

## 关联调研

- [Gemini anatomy](../research/gemini/anatomy.md) — UI 主轴参考
- [CoWork notes](../research/cowork/notes.md) — agent 形态参考
- [Claude Code 深度学习 ×4](../research/claude-code/learnings/) — 扩展机制 / agent 原语 / 安全模型
- [Manus notes](../research/manus/notes.md) — 视觉产物 + 营销策略参考
- [ChatGPT notes](../research/chatgpt/notes.md) — 历史调研；当前按用户偏好对齐清晰会话交互
- [截图索引 16 张](../research/SCREENSHOTS.md)

---

## 阅读顺序建议

第一次过手册：`00-overview` → `02-personality` → `07-growth` → `03-product-form` → 其余按需。

修订单个章节：直接进对应子目录，每个文件可独立改。

---

## 关键决策状态

✅ **已锁（5 条）**：
1. 产品人格「心」路线 → [ADR-001](../decisions/ADR-001-product-personality.md)
2. 目标用户 T0 = 内容创作者 + 新手创业者 → [ADR-002](../decisions/ADR-002-target-users.md)
3. 首发 Canvas chip = 海报 / 落地页 / 课件 / 写一封信 / 想法可视化 / 更多（5 产物 + 兜底）→ [canvas-types.md](./03-product-form/canvas-types.md)
4. Mode 模型 = 信任档位（不做顶部 tab）→ [ADR-003](../decisions/ADR-003-mode-model.md)
5. 北极星 = WAS（周活跃产物分享数）→ [ADR-004](../decisions/ADR-004-north-star-metric.md)
6. 商业模式 = freemium + 创作者 Pro → [ADR-005](../decisions/ADR-005-business-model.md)

🟡 **等用户给输入**（不是决策，是只有你能写的内容）：
- [00-overview/vision.md](./00-overview/vision.md) — 产品愿景（创始人手笔）
- [02-personality/brand-assets.md](./02-personality/brand-assets.md) — logo / favicon / OG 模板等设计资产

🟢 **本轮全部锁定**。下一阶段重点：
- 在 `docs/prototypes/variant-a-mi-mu/` 基础上做组件级 / 交互细节打磨
- vision.md / brand-assets.md 等待你给输入的章节
