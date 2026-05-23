---
status: 🟡 维护中
updated: 2026-05-20
---

# 参考索引

> 内外部参考的快速导航。内部链接帮你 1 跳到位，外部链接附 1 句价值说明。
> 链接失效或新增条目随手补——这页是工作台，不是档案。

---

## 内部 · 决策记录（ADR）

- [ADR-001 · 产品人格定位：「心」路线](../../decisions/ADR-001-product-personality.md) — 锁定 Kokoro 走柔/温/内观；后续所有设计都以此为前提

---

## 内部 · 调研

### 主轴
- [research/gemini/anatomy.md](../../research/gemini/anatomy.md) — UI 主轴参考，左导航 + 中央胶囊输入框 + Canvas 右抽屉
- [research/SCREENSHOTS.md](../../research/SCREENSHOTS.md) — 16 张截图索引（含登录/未登录、产品/营销页区分）

### 次轴
- [research/cowork/notes.md](../../research/cowork/notes.md) — agent 形态参考，Plan-then-Approve 模型
- [research/manus/notes.md](../../research/manus/notes.md) — 视觉产物 + 营销策略参考；首页"产出物 chip"重要灵感来源
- [research/claude-code/notes.md](../../research/claude-code/notes.md) — Claude Code 总体调研
- [research/claude-code/learnings/01-philosophy.md](../../research/claude-code/learnings/01-philosophy.md) — Claude Code 设计哲学
- [research/claude-code/learnings/02-extensibility.md](../../research/claude-code/learnings/02-extensibility.md) — 扩展机制（Skills / Slash / MCP）
- [research/claude-code/learnings/03-agentic-primitives.md](../../research/claude-code/learnings/03-agentic-primitives.md) — Agent 原语（Tasks / Subagents / Hooks）
- [research/claude-code/learnings/04-safety-and-surfaces.md](../../research/claude-code/learnings/04-safety-and-surfaces.md) — 安全模型 + Surface 抽象
- [research/chatgpt/notes.md](../../research/chatgpt/notes.md) — ChatGPT 调研（多作反面参考：着陆页过弱、能力 grid 不分主次）
- [research/gemini/anatomy.md](../../research/gemini/anatomy.md) — Gemini 解剖（详细 UI 拆解）

---

## 内部 · 产品手册（按章节）

### 00 · 总览
- [README · 产品手册总索引](../README.md) — 导览 + 状态标记规范 + 阅读顺序
- [00-overview/one-pager.md](../00-overview/one-pager.md) — 一页纸
- [00-overview/vision.md](../00-overview/vision.md) — 愿景
- [00-overview/positioning.md](../00-overview/positioning.md) — 定位
- [00-overview/glossary.md](../00-overview/glossary.md) — 术语表

### 01 · 策略
- [01-strategy/target-users.md](../01-strategy/target-users.md) — 目标用户（T0/T1 分层）
- [01-strategy/value-proposition.md](../01-strategy/value-proposition.md) — 价值主张
- [01-strategy/differentiation.md](../01-strategy/differentiation.md) — 差异化三支柱（气质 / 产物即广告 / 通用底盘 + 钩子叙事）
- [01-strategy/growth-engine.md](../01-strategy/growth-engine.md) — 增长引擎高层说明
- [01-strategy/business-model.md](../01-strategy/business-model.md) — 商业模式三档候选

### 02 · 人格
- [02-personality/core.md](../02-personality/core.md) — 「心」人格内核
- [02-personality/voice-and-tone.md](../02-personality/voice-and-tone.md) — 文案口气
- [02-personality/visual-language.md](../02-personality/visual-language.md) — 视觉语言宪法 + 产物印记定义
- [02-personality/brand-assets.md](../02-personality/brand-assets.md) — 品牌资产清单

### 03 · 产品形态
- [03-product-form/shape.md](../03-product-form/shape.md) — 形态总论
- [03-product-form/core-flows.md](../03-product-form/core-flows.md) — 核心流程
- [03-product-form/feature-map.md](../03-product-form/feature-map.md) — 功能地图
- [03-product-form/canvas-types.md](../03-product-form/canvas-types.md) — 5 个首发 Canvas 类型候选

### 04 · 架构
- [04-architecture/ia.md](../04-architecture/ia.md) — 信息架构
- [04-architecture/navigation.md](../04-architecture/navigation.md) — 导航

### 05 · 设计系统
- [05-design-system/](../05-design-system/) — 待填（依赖人格视觉细化）

### 06 · 屏幕
- [06-screens/home.md](../06-screens/home.md) — 首屏
- [06-screens/](../06-screens/) — 其余待填

### 07 · 增长（本章节自身）
- [07-growth/engine-overview.md](../07-growth/engine-overview.md) — 双循环节点级拆解
- [07-growth/sharing-first-class.md](../07-growth/sharing-first-class.md) — 分享一等公民产品形态
- [07-growth/templates-market.md](../07-growth/templates-market.md) — 模板市场
- [07-growth/viral-loops.md](../07-growth/viral-loops.md) — K-factor 量化模型
- [07-growth/metrics.md](../07-growth/metrics.md) — 增长指标体系

### 08 · 可扩展性
- [08-extensibility/](../08-extensibility/) — 待填（重度参考 Claude Code）

### 09 · 安全
- [09-safety/](../09-safety/) — 待填（重度参考 Claude Code）

---

## 外部 · 竞品产品页 / 营销页

| 链接 | 价值 |
|---|---|
| https://gemini.google.com | Gemini 主入口，左导航 + 中央胶囊输入 + 右 Canvas 抽屉的标准型 |
| https://manus.im | 首页"产出物 chip"模式的代表；feature 页"Hero→痛点→对比表→三步→FAQ"模板可借鉴 |
| https://manus.im/playbook | Manus Playbook 模板生态层，Kokoro 模板市场的直接参考 |
| https://chatgpt.com | 未登录态着陆页风格（极简 composer + 全 sidebar 暴露）；多作反面参考 |
| https://chatgpt.com/overview | ChatGPT 营销页能力 grid 平铺，Canvas 不被特别突出 |
| https://claude.com/product/claude-code | Claude Code 产品页，Surface Tabs 设计的关键参考 |
| https://claude.com/product/cowork | Claude Cowork 产品页，Plan-then-Approve agent 形态 |
| https://anthropic.com/product/claude-cowork | 同上的 anthropic.com 域版本，对比观察品牌一致性 |
| https://code.claude.com/docs/en/overview | Claude Code 官方文档（Mintlify 三栏布局参考） |
| https://www.canva.com | 模板生态成熟样本（反面：Kokoro 不做手动设计） |
| https://www.notion.so/templates | Notion 模板市场（反面：Kokoro 模板要"留坑给 AI"，不是预填内容） |
| https://v0.dev | 视觉产出 + 强人格 + dev 向（差异化对照） |
| https://lovable.dev | 同上类型，对照"夸张人格"路线为什么不适用 Kokoro |

---

## 外部 · 设计灵感与体系

| 链接 | 价值 |
|---|---|
| https://m3.material.io | Material 3 设计系统；token 体系、动效曲线、组件分层的工业参考 |
| https://developer.apple.com/design/human-interface-guidelines | Apple HIG；克制、可达性、平台一致性的标杆 |
| https://www.anthropic.com/brand | Anthropic 品牌资产；琥珀色 + 几何 sans 的暖调克制风 |
| https://things.com | Things（Mac/iOS）；"克制但有温度"工具的代表，ADR-001 气质参考点 |
| https://www.notion.so | Notion；柔色 + 信息密度高的另一个气质方向 |
| https://cron.com | Cron（已被 Notion 收购）；圆角 + 暖调 + 极简的设计语言参考 |
| https://linear.app | Linear；纯专业极简（Kokoro 不走这条但要对照） |
| https://refactoringui.com | Refactoring UI；微观间距 / 字号 / 阴影实操参考 |

---

## 外部 · 开源代码参考

### Open-Generative-AI
- URL：https://github.com/LordFoxFairy/Open-Generative-AI（本地：/Users/nako/WebstormProjects/github/thefoxfairy/Open-Generative-AI/）
- 是什么：开源的 AI 媒体生成 studio（图 / 视频 / Lip Sync / Cinema），Next.js 15 + React 19 + Tailwind 4 + Electron，monorepo workspaces
- 给 Kokoro 的参考价值：
  1. 产品模式 — image/video 生成 UI 流程（prompt + model picker + aspect ratio + result + history），已部分继承到 `docs/prototypes/variant-a-mi-mu/canvas-poster.html`
  2. 架构模式 — monorepo 4 sub-package、Electron 多平台封装、Muapi 客户端，未来 Kokoro MVP 启动时可作工程参考
  3. ApiKey 管理 — 本地 localStorage 存 key、polling 出图、history sidebar 模式，已继承到 settings.html "AI 模型与 Key" 段 + components.html `gen-history` / `model-picker` specimen
- **不继承**：dark + cyan + glassmorphism 视觉语言，与 ADR-006 米+木+纸感 冲突；所有借鉴过来的产品模式视觉都重做

---

## 外部 · AI 产品 / 增长观察

| 链接 | 价值 |
|---|---|
| https://www.lennysnewsletter.com | Lenny's Newsletter；产品 + 增长高密度信号源 |
| https://every.to/p1 | Every（P1）；AI 产品深度评论 |
| https://stratechery.com | Stratechery；AI / 平台战略长文 |
| https://www.notboring.co | Not Boring；增长 / 商业模型分析 |
| https://www.firstround.com/review | First Round Review；早期阶段产品 + 招聘 + 创始人手册 |
| https://www.reforge.com/blog | Reforge；增长方法论 + K-factor / 留存 / 漏斗教科书级文章 |
| https://andrewchen.com | Andrew Chen；增长经典（"Law of Shitty Clickthroughs"等） |
| https://www.lennyrachitsky.com | 同 Lenny's Newsletter 作者博客 |
| https://newsletter.pragmaticengineer.com | Pragmatic Engineer；工程视角的 AI 产品观察 |

---

## 外部 · 报告 / 数据集

| 链接 | 价值 |
|---|---|
| https://www.a16z.com/ai | a16z AI 产品分类与 Top 50 报告（半年更新一次） |
| https://www.appliedai.tools | Applied AI Tools；按场景分类的 AI 工具目录 |
| https://theresanaiforthat.com | There's An AI For That；全网 AI 产品索引（量大但噪声高） |

---

## 维护规则

- 新增条目随手补；不写就忘
- 链接失效不删除——加 `(404, 2026-MM-DD)` 标记，保留作为历史
- 外部链接尽量保留 1 句价值说明，方便后来人不点开也能判断要不要看
- 内部链接按章节分组，跟着 [README.md](../README.md) 的导览表保持一致
