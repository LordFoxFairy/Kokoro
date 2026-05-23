# Claude Code 官网 / 文档 UI 调研笔记

> 调研对象：Claude Code 的公开 web 触点（不是 CLI 本体）。  
> 调研日期：2026-05-20  
> 调研方式：WebFetch HTML/Markdown 内容抽取（无浏览器截图）。

## 1. URL 列表

| URL | 命中状态 | 类型 |
|---|---|---|
| https://www.anthropic.com/claude-code | 301 → https://claude.com/product/claude-code | 产品营销页 |
| https://claude.com/product/claude-code | 200 | 产品营销页（最终落地） |
| https://docs.claude.com/en/docs/claude-code/overview | 301 → https://code.claude.com/docs/en/overview | 文档 overview |
| https://code.claude.com/docs/en/overview | 200 | 文档站（落地） |
| https://code.claude.com/docs/en/quickstart | 200 | 文档子页 |
| https://www.anthropic.com | 200 | 母品牌主站（参照调性） |
| https://claude.com | 200 | 产品品牌主站（参照调性） |

要点：
- Claude Code 已经从 anthropic.com 域名分裂出来，落到 `claude.com/product/...`（营销）+ `code.claude.com/docs/...`（文档）两个独立子产品域。
- 文档站从 `docs.claude.com/en/docs/claude-code/*` 又被 301 到 `code.claude.com/docs/en/*`，说明 Claude Code 已经被升级为顶级产品，有自己的文档子域。这是品牌策略信号，不是单纯视觉，但和导航 IA 设计相关。

## 2. 布局速写

### 2.1 营销页（claude.com/product/claude-code）
标准 modern SaaS 单页：

```
┌──────────────────────────────────────────────┐
│  Top navbar: logo · 产品下拉 · pricing · CTA │
├──────────────────────────────────────────────┤
│                                              │
│   HERO                                       │
│   H1: "Built for developers"                 │
│   sub: 强调 "在你自己的代码库里直接工作"      │
│   [Get Claude Code] (主 CTA)                 │
│   渠道按钮组: Desktop · VS Code · JetBrains │
│              · Web · Slack                   │
│   视觉锚: 桌面应用截图（不是终端 mock）       │
│                                              │
├──────────────────────────────────────────────┤
│   Surface tabs: Desktop / Terminal /         │
│   IDE / Web · iOS / Slack                    │
│   切 tab 换大截图                            │
├──────────────────────────────────────────────┤
│   能力分组（文字 + 截图配图）：               │
│   - onboarding / 探索代码库                  │
│   - issue triage                             │
│   - 多文件 refactor                          │
│   - agentic search                           │
├──────────────────────────────────────────────┤
│   一行终端安装命令 code block:                │
│   `curl -fsSL https://claude.ai/install.sh   │
│    | bash`                                   │
├──────────────────────────────────────────────┤
│   Pricing cards: Free · Pro · Max            │
├──────────────────────────────────────────────┤
│   Social proof: Ramp · Intercom · Notion     │
│   客户 logo + 引述卡片                       │
├──────────────────────────────────────────────┤
│   FAQ                                        │
├──────────────────────────────────────────────┤
│   Footer: 6 列链接（Products / Features /    │
│   Models / Solutions / Platform / Resources /│
│   Company / Help）+ 语言选择 + 社交          │
└──────────────────────────────────────────────┘
```

### 2.2 文档页（code.claude.com/docs/en/*）
强烈 Mintlify 平台特征（依据：MDX `<Tabs>` / `<Tab>` / `<AccordionGroup>` / `<Accordion>` / `<CardGroup>` / `<Card>` / `<Info>` / `<Note>` / `<Tip>`，代码块属性 `theme={null}`，`/en/` 语言前缀，根 `llms.txt`）。Mintlify 典型布局：

```
┌──────────────────────────────────────────────────────────┐
│ Top navbar:                                              │
│   logo · 站点切换（API/Code）· search (Cmd+K) · GitHub  │
├──────┬───────────────────────────────────────┬───────────┤
│      │                                       │           │
│ 左   │       主内容                           │  右 TOC   │
│ 目录 │                                       │ on-page   │
│      │   H1 + 描述 blockquote                 │ headings  │
│ 树   │                                       │           │
│ 状   │   <Tabs> 横向 tab 切换                 │           │
│      │   ├ <Tab> 内嵌代码块 (copy btn,        │           │
│ 分组 │   │   语言标签)                        │           │
│      │   └ <Info>/<Note>/<Tip> 横条 callout   │           │
│      │                                       │           │
│      │   <AccordionGroup> 折叠组               │           │
│      │   <CardGroup cols={2}> "下一步" 卡片网格│           │
│      │                                       │           │
│      │   表格（"I want to..." / Best option） │           │
│      │                                       │           │
│      │   prev / next + "Was this helpful?"   │           │
└──────┴───────────────────────────────────────┴───────────┘
```

## 3. 设计 tokens 印象

> 注：未直接读取 CSS 变量，下列是 WebFetch 提供的语义描述 + Anthropic 品牌系统已知信息推断，置信度中。

| token | 印象 |
|---|---|
| 主背景 | 大面积白 / 接近 `#FAFAF7` 米白；偶有 cream/beige 分段（Anthropic 母站调性） |
| 主文字 | 接近黑（charcoal） |
| 品牌主色 | Anthropic 著名的"Anthropic orange / clay" 约 `#CC785C` / `#D97757`（橘陶色），按钮、链接 hover、accent 用 |
| 二级色 | 中灰系做次级 chrome（边框、辅助文字） |
| 圆角 | 中等圆角，按钮 pill / 大圆角；卡片 8–12px 体感 |
| 字体 | 全站 sans（geometric 现代感），代码 mono；headline 偏 large 但不"editorial 大字报"，对比 anthropic.com 母站会更技术克制 |
| 间距 | 偏松，section 与 section 之间留白大；docs 主列宽度有节制，阅读舒适 |
| 阴影 | 几乎不用强阴影；卡片靠边框 / 背景色块切分 |
| 装饰 | 极少（无 gradient blob、无 3D），主要靠截图本身做视觉锚 |

## 4. 关键组件清单

### 4.1 营销页
- **Surface Tabs（最大亮点）**：一个横向 tab 组，把 "Desktop / Terminal / IDE / Web · iOS / Slack" 平铺，点 tab 换大截图。把"我们到处都能跑"的卖点视觉化。
- **Channel button group**：Hero 下面一排小按钮 `Desktop / VS Code / JetBrains / Web / Slack`，相当于多入口分发器，不是单一 CTA。
- **Install code block**：一行 `curl | bash` 终端代码片段卡片（带 mono 字体、深色或浅色块），直接放在 hero 附近，引诱"复制粘贴上手"。
- **Feature block = 文字段落 + 大截图**：不是图标卡片网格，而是 alternating layout（左文右图 / 左图右文）。每段一个具体场景（onboarding / triage / refactor）。
- **Pricing cards**：3 列横向，Free / Pro / Max。
- **Logo wall + 引述卡片**：Ramp、Intercom、Notion 等客户 logo 灰度排开，下面是带客户头像/公司 logo 的简短证言。

### 4.2 文档站（Mintlify 风格）
- **左目录树**：分组 + 嵌套，激活项高亮（应是品牌橘色或下划线）。
- **顶部搜索**：Mintlify 默认 Cmd+K 大搜索框，含 AI 搜索（Claude 自己做的话基本肯定开）。
- **`<Tabs>` 组件**：横向 tab，例如 "Native Install / Homebrew / WinGet"，文档侧反复用。营销页 Surface Tabs 是它的"高配版"。
- **嵌套 Tabs**：Tab 里还可以放 Tab（Terminal Tab 里再装 Native/Homebrew/WinGet）。
- **代码块**：单语言代码块标 `bash` / `powershell` / `batch` / `text`，自带 copy 按钮、语言标签。`theme={null}` 暗示支持每个代码块覆盖主题，文档站做了主题切换（dark/light）。
- **Callouts**：`<Info>` / `<Note>` / `<Tip>` 三种横条 admonition，左侧色条 + 图标。
- **`<AccordionGroup>` + `<Accordion icon=...>`**：折叠组件，每个 accordion 带一个 FontAwesome 图标（`wand-magic-sparkles`、`hammer`、`code-branch`、`plug`、`sliders`、`users`、`terminal`、`clock`、`globe`）。这是 Mintlify 把 FontAwesome 集进了 props 的标志。
- **`<CardGroup cols={2}>` + `<Card icon href>`**：页脚做"下一步去哪"的 2 列卡片网格，每张卡 = 图标 + 标题 + 简述 + 链接。
- **表格**：紧凑、用于"我要 X / 最佳路径"的对照表。

## 5. Kokoro 可借鉴 3–5 条

1. **Surface Tabs 卖"哪里都能用"** —— Kokoro 如果要同时讲 chat + Canvas + 长任务 + 移动，可以照搬 hero 下方的横向 tab 切大截图模式，比"4 列特性卡片"信息密度高、视觉锚强。Gemini 在 anatomy.md 里走的也是大截图主导，Claude Code 这套是更"自营销"的演法。
2. **Mintlify 风格组件库（Tabs / AccordionGroup / CardGroup / Callouts）** —— Kokoro 文档/帮助中心如果要建，直接对齐这套 MDX 组件，避免重新造 UI primitive，且和"开发者品味"对齐。
3. **左目录 + 主内容 + 右 on-page TOC 三栏文档布局** —— 这是开发者文档的事实标准，Kokoro 帮助中心可以照搬，比 Gemini 帮助页的"FAQ 折叠列表"更适合长文档。
4. **`curl | bash` 风格的"一行复制即上手" code block** —— 即便 Kokoro 不是 CLI，也可以提炼一个"最短上手命令 / 链接"卡片，放在 hero 下方，给"我懂技术，给我接入方式"的用户一个快速入口。
5. **顶级 Cmd+K 全局搜索** —— Claude Code 文档站把搜索放在 navbar 中央，Kokoro web app 里"搜历史会话 / 搜 Canvas / 搜文档"也应该是顶级入口而不是塞进侧栏。

## 6. Kokoro 应避开 2–3 条

1. **不要照搬"截图主导"的营销页节奏** —— Claude Code 营销页几乎每段都靠一张大产品截图撑住。Kokoro 还在早期，没那么多打磨好的截图，硬学只会显得空。先用文字 + 抽象插画过渡。
2. **不要落进 Anthropic 品牌橘的舒适区** —— `#CC785C` 是 Anthropic 强标识，Kokoro 直接抄会被读作"Claude 套壳"。要走暖色就选自己的色相，并且只在 accent 用，不要把它当主背景。
3. **不要无脑用 6 列 footer** —— Claude Code 的 footer 信息量是因为它是大公司多产品 hub。Kokoro 单产品阶段做这么宽的 footer 会显得空架子，3 列足够。

## 7. 数据来源置信度

| 维度 | 置信度 | 备注 |
|---|---|---|
| 文档站布局/组件 | **高** | MDX 源直接抽到，Mintlify 平台特征明确（`<Tabs>`、`<AccordionGroup>`、`<CardGroup>`、`theme={null}`、`/en/`、`llms.txt`） |
| 营销页结构（hero / tabs / pricing / footer） | 中–高 | 通过 WebFetch 总结，没有原始 DOM 截图，但段落级 IA 描述一致 |
| 颜色 token 精确值 | 中 | 没读 CSS，"Anthropic orange ≈ #CC785C / #D97757" 是公开品牌系统推断；具体 hex 需用 Playwright 看 computed style 校正 |
| 字体精确名 | 中 | 只能定到"sans-serif geometric + monospace"，具体字体（Anthropic 用 Styrene / Tiempos 系列母品牌，Claude Code 产品域是否沿用未直接验证）需要 DevTools 看 `font-family` 校正 |
| 圆角 / 阴影 / 间距数值 | 低 | 全是体感描述，未量化。后续若要复刻应用 Playwright 截图 + DevTools 量取 |
| 母品牌（anthropic.com）调性 | 中 | WebFetch 第二轮拿回的是 HTML/navigation 多于视觉描述，引述里描述较稳但偏概念 |

## 8. 给主控的一句话

> Claude Code 官网最值得 Kokoro 学的一件事：**用一组横向 Surface Tabs 在 hero 之后立刻把"产品在不同入口长什么样"用大截图轮播出来**，比四列特性卡片更直接、信息密度更高，且天然能复用到文档站的 MDX `<Tabs>` 组件。
