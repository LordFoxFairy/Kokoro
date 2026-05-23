# Manus 设计语言调研笔记

> 目的：为 Kokoro（类 Gemini 的对话 + Canvas 应用）横向对比 Manus 的产品形态与设计语言。
> 数据来源：仅 WebFetch 抓取的服务端渲染文本（HTML→markdown）。**未拿到截图、未跑浏览器渲染**，色值/字体/圆角档位多为文字推断，请以"印象级"对待。

---

## 1. URL 列表（实际拉取到的）

成功：

- `https://manus.im` —— 首页
- `https://manus.im/pricing` —— 仅拿到 title 和导航壳，无真实定价卡内容
- `https://manus.im/blog` —— 博客卡片网格
- `https://manus.im/playbook` —— 模板/工作流目录
- `https://manus.im/features/webapp` —— "AI Website Builder" 详情页
- `https://manus.im/features/wide-research` —— "Wide Research" 多 agent 并行
- `https://manus.im/features/manus-browser-operator` —— 浏览器接管 agent

404（站点已重组）：

- `/features`、`/use-cases`、`/usecases`、`/tools/ai-slides`、`/feature/ai-slides`、`/feature/browser-operator`

旁注：底部版权显示"copyright belongs to Meta as of 2026"，页面多处出现"Manus is now part of Meta"，结合此次调研日期 2026-05-20 判断 Manus 已被 Meta 收购，站点正处于品牌过渡期。

---

## 2. 布局速写

### 2.1 首页

```
┌──────────────────────────────────────────────────────────────┐
│  Manus    Features  Solutions  Resources    Events Pricing   │
│  (logo)                                     Sign in  Sign up │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│                   "What can I do for you?"                   │
│                                                              │
│            ┌──────────────────────────────────────┐          │
│            │  [input 区 / 提示词框，推测]         │          │
│            └──────────────────────────────────────┘          │
│                                                              │
│      [Create slides] [Build website] [Develop desktop        │
│       apps] [Design]   More ▾                                │
│                                                              │
│                   "Less structure, more intelligence."       │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│  Footer: Product · Resources · Community · Compare ·         │
│          Download · Business · Company                       │
│  Social: LinkedIn · X · YouTube · Instagram · TikTok         │
└──────────────────────────────────────────────────────────────┘
```

首页核心是"中央一个意图框 + 一排意图分类 chip"，类似 ChatGPT/Gemini 首页的输入主导式布局，但 chip 的标签是**任务产出物**（slides / website / desktop apps / design），不是话题分类。

### 2.2 Feature 详情页（以 wide-research / browser-operator / webapp 为代表）

```
┌──────────────────────────────────────────────────────────────┐
│ Header (含 Install / Get started CTA)                        │
├──────────────────────────────────────────────────────────────┤
│ Hero：一句强对比 headline + 一个主 CTA                       │
│   e.g. "Most AI tools fail at scale. Manus doesn't."         │
├──────────────────────────────────────────────────────────────┤
│ 问题陈述段：「The context overload problem」                 │
├──────────────────────────────────────────────────────────────┤
│ 差异化段：「What makes X different」+ 对比表                 │
│   ┌──────┬─────────┬────────────┬────────┐                  │
│   │ 维度 │ Manual  │ Std. AI    │ Manus  │                  │
│   ├──────┼─────────┼────────────┼────────┤                  │
│   │ 速度 │ ...     │ ...        │ ...    │                  │
│   └──────┴─────────┴────────────┴────────┘                  │
├──────────────────────────────────────────────────────────────┤
│ How it works：3 步流程图                                     │
│   [1 Prompt] → [2 Build] → [3 Launch & Grow]                 │
├──────────────────────────────────────────────────────────────┤
│ 真实用例 + 视频回放链接                                      │
├──────────────────────────────────────────────────────────────┤
│ FAQ（可折叠）                                                │
├──────────────────────────────────────────────────────────────┤
│ Footer（40+ 链接，分多列）                                    │
└──────────────────────────────────────────────────────────────┘
```

模式高度一致：**Hook headline → 痛点 → 对比表 → 三步流程 → 用例 → FAQ**。Manus 的所有 feature 页都套这个模板。

### 2.3 Playbook（模板库）

7 个分类的网格列表：Picks / Business / Creative / Sales & Marketing / Education / Personal Productivity / Other。每个分类下挂 N 个"模板"卡片（e.g. pitch deck generator / influencer finder / interior design assistant）。本质是带分类导航的工具/prompt 商店。

---

## 3. 设计 tokens 印象（**低置信，未见截图**）

| 维度 | 印象 | 依据 |
|---|---|---|
| 主色 | 白/浅灰主导，黑文字 | 博客页文字描述"predominantly white/light backgrounds, dark text" |
| 强调色 | 不显眼，可能仅在分类徽章 / 主 CTA 上着色 | 博客描述"accent colors appear in category badges and thumbnails" |
| 字体族 | 现代 sans-serif，无 serif | 博客描述"clean, modern sans-serif typeface" |
| 圆角档位 | 推测中等（卡片软圆角，按钮 pill 或 6-8px） | 未拿到 CSS，纯推断，**不要照搬** |
| 间距感 | 偏宽松、白底为主 | "minimalist presentation, focusing attention on content" |
| 信息密度 | 营销页中等，组件页未见 | — |

**这一节如果要做颜色 / 字体的硬决策，必须重新跑一次带浏览器渲染的抓取或人工截图。**

---

## 4. 关键组件（按实际看到的）

均为营销页组件，**未见登录后产品内的真实 agent UI 截图**：

- **中央意图输入框 + 意图 chip 行**（首页）—— 类 Gemini 首页，但 chip 表达"我要做什么类产出"，不是"聊什么话题"。
- **产品对比表**（feature 页通用）—— 三列：手工 / 普通 AI / Manus，按维度逐行打钩。
- **三步流程图**（Prompt → Build → Launch；Connect → Grant Access → Autonomous Action）—— 几乎每个 feature 页都有，构成 Manus 的"动作叙事"模板。
- **集成图标网格**（webapp 页：LLM / Stripe / Database / Maps / Voice-to-Text 等图标墙）。
- **视频回放链接**（browser-operator 页用 inline video 演示用例）。
- **FAQ 折叠组**。
- **博客卡片**（缩略图 + 分类标签 + 日期 + 标题）。
- **Playbook 模板分类网格**（带 Picks / Business / Creative 等 tab 分类）。

未确认（拉不到截图）：聊天气泡、agent 状态卡、工作流可视化、任务列表、文件浏览器、终端 pane、Canvas 工件区。

---

## 5. Kokoro 可借鉴 3-5 条

1. **首页用"产出物 chip"组织意图入口**：Manus 把"Create slides / Build website / Develop desktop apps / Design"当做一级入口，比"Code / Search / Image"这种能力分类更贴近用户脑中的任务表征。Kokoro 的 Canvas 产物（文档 / 网页 / 图 / 幻灯片）可以照搬这个表达。
2. **Feature 页统一模板**：Hero → 痛点 → 对比表 → 三步流程 → 用例 → FAQ。叙事一致让产品的"宣称能力"和"实际工作流"对得上号。
3. **多 agent 并行的可视化叙事**（Wide Research）：把"每个子 agent 自己有 VM + 工具 + 网络"这种系统设计，做成对用户可见的产品差异化，而不是埋在技术博客里。Kokoro 如果上 sub-agent，正面 sell 它。
4. **Playbook 作为模板生态层**：在主对话/Canvas 之上挂一层"模板商店"，按工种切分类（业务 / 创意 / 销售 / 教育 / 生活），降低冷启动门槛。Gemini 没把这层做得很重，Kokoro 可以补。
5. **视频回放替代静态截图**：browser-operator 页大量用 inline 视频演示真实跑流程。对 agent 类产品比截图说服力强，因为 agent 的价值是"过程"。

## 6. Kokoro 应避开 2-3 条

1. **首页 slogan 太抽象**："Less structure, more intelligence." 一眼看不出产品做什么，得靠下方 chip 救场。Kokoro 的首屏一句话最好直接说"做什么"，别玩概念。
2. **Feature 页全是文字 + 对比表，零真实 UI 截图**：调研全程没拉到一张 agent 实际工作的截图，对买家心智极不友好——"你说自己强，给我看看"。Kokoro 必须把 Canvas / 对话流的真实截图放在 fold 之上。
3. **导航分类太多且模糊**（Features / Solutions / Resources / Events / Business / Pricing + 大量 footer 列）：典型大公司站点信息过载。Kokoro 早期阶段顶导保持 3-4 项即可。

---

## 7. 数据来源置信度

| 项 | 置信度 | 依据 |
|---|---|---|
| URL 列表 / 导航结构 | 高 | WebFetch 直接拉到的 href |
| 首页 hero 文案 / chip 标签 | 高 | 抓到了 "What can I do for you?" / "Less structure, more intelligence." / 四个 chip 标签的原文 |
| Feature 页叙事模板（Hero/对比表/三步） | 高 | 三个独立 feature 页（webapp / wide-research / browser-operator）模式一致 |
| Playbook 分类 | 高 | 直接列出 7 个分类名 |
| 颜色 / 字体 / 圆角 / 间距 | **低** | 仅靠博客页一句"white background, dark text, sans-serif"的转述推断，未见任何 CSS 值、未渲染、未截图 |
| 登录后产品 UI（侧边栏 / 聊天 / Canvas / 任务卡） | **低 / 缺失** | 完全没拿到，营销页未嵌入 product screenshot |
| Manus 已属于 Meta 的事实 | 中 | 多处页面文本与 footer 版权提到，但未交叉验证公开新闻 |

如果 Kokoro 团队要做颜色 / 字体的具体决策，建议补一轮：① 人工截首页 + 1 个 feature 页 + 登录后界面（如果可注册）；② 用浏览器渲染抓 computed style。
