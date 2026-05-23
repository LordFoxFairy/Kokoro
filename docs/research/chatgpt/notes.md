# ChatGPT 设计语言调研（未登录态）

> 数据来源：Playwright 抓取 + 全页截图 + computed style 取值，2026-05-20。所有数值来自未登录态着陆页与营销页 DOM；登录后界面（含 Canvas、GPTs、Projects 实操态）本次未抓取。
> 角色定位：Kokoro 的 **次轴参考**（主轴是 Gemini）。重点对比"chatgpt.com 着陆页输入框"与"Gemini home 胶囊输入框"两种风格的取舍。

---

## 1. URL 列表

| URL | 状态 | 抓取方式 |
|---|---|---|
| https://chatgpt.com/ | 200，渲染完整未登录态 | Playwright，已截图 `chatgpt-landing.png` |
| https://openai.com/chatgpt/overview/ | 自动 301 → `chatgpt.com/zh-Hans-CN/overview/` | Playwright，已截图 `chatgpt-overview.png` |
| https://help.openai.com/en/ | 200 | Playwright，已截图 `chatgpt-help.png` |
| WebFetch 通道 | 全部 403（Cloudflare WAF） | 改用 Playwright |

截图保存在 `.playwright-mcp/`（mcp 默认目录），未拷进本目录以保持仓库轻量。

---

## 2. 布局速写

### 2.1 chatgpt.com 未登录态着陆页

```
┌──────────────┬─────────────────────────────────────────────┐
│  Sidebar     │  Header:  [ChatGPT ▾]      [登录] [免费注册]  │
│  (~260px)    │                                              │
│              │                                              │
│  + 新聊天     │                                              │
│  ⌕ 搜索聊天   │           今天有什么计划？  (h1, 24px, 400)    │
│  □ 图片       │                                              │
│              │  ┌─────────────────────────────────────────┐ │
│  …           │  │ + │ 有问题，尽管问            🎙 语音    │ │
│              │  └─────────────────────────────────────────┘ │
│  套餐/设置    │   "向 AI 聊天机器人 ChatGPT 发送消息即表示…"   │
│  [登录]       │                                              │
└──────────────┴─────────────────────────────────────────────┘
```

- 未登录已展示**完整 sidebar**（新聊天 / 搜索聊天 / 图片入口 / 套餐 / 设置 / 帮助 / 登录卡），不是空壳
- 主区中央**单胶囊 composer**，左侧 `+` 弹菜单（添加照片 / 网页搜索 / 深度研究[需登录] / 思考时间更长[需登录] / 创建图片[需登录]），右侧"开始听写"和"语音"
- 主标题极克制：`今天有什么计划？`，24px 400 weight，与 Gemini 大字问候完全相反
- 没有 prompt suggestion chip。"探索 / Sora / GPTs / Projects" 等入口在着陆页不暴露，藏在登录后

### 2.2 openai.com/chatgpt/overview 营销页

```
┌──────────────────────────────────────────────────────┐
│  Logo + [简介 功能▾ 学习▾ Codex 商业 定价 下载] [登录][注册]
├──────────────────────────────────────────────────────┤
│  ChatGPT                                              │
│  获取答案，寻找灵感，提升效率。   ← h1 56.8px / 500     │
│  全新的 GPT-5.2，为专业工作、编码和长时运行的智能体…    │
│  [ 开始使用 → ]  [ 详细了解 GPT-5.2 → ]                │
│                                                       │
│  ─── 旋转 prompt chip 三列瀑布（24 条示例 prompt）─── │
│                                                       │
│  ┌ 大幅 feature 块（左文右大图）×4 ┐                  │
│  │ "陪你写作、构思、修改并发现新想法"                  │
│  │ "总结会议内容，获取全新启发，提高工作效率。"        │
│  │ "生成并调试代码，实现重复工作的自动化…"             │
│  │ "探索新知，培养爱好，破解难题。"                    │
│  └────────────────────────────────┘                  │
│                                                       │
│  ── "探索 ChatGPT 的更多功能" 网格 ──                  │
│   随心输入或语音 / 搜索网页 / 协作完成写作与编程(Canvas)│
│   分析数据并创建图表 / 讨论图片 / 智能体 / 创作图像     │
│   / Apple 携手 ChatGPT                                │
│                                                       │
│  ── 价格 4 列：免费 / Go $8 / Plus $20 / Pro $200 ──   │
│                                                       │
│  Footer: OpenAI © 2015-2026  社交图标  语言切换         │
└──────────────────────────────────────────────────────┘
```

- 营销页 hero 极简：**纯白底 + 大字 serif-ish sans + 一个深色 pill CTA**，没有 hero illustration
- prompt chip 三列瀑布**自动滚动**（DOM 中同一组 chip 重复三份，CSS 动画轮播），是 hero 下方最强视觉
- feature 块为"短大字标题 + 一张产品 mock 图"的左右交替排版，**没有图标**
- 子产品（**Canvas / Sora / DALL·E / 智能体 / Apple 集成**）**全部塞在同一个 grid**，等权重并列，不分主次

### 2.3 help.openai.com 帮助中心

```
┌──────────────────────────────────────────────────────┐
│  OpenAI logo                                  [Login] │
│                                                       │
│  ┌─────────  Search for articles…  ─────────────────┐ │
│                                                       │
│  3 列卡片网格，每张卡：icon + 标题 + 一句话描述         │
│   Account / API / ChatGPT / ChatGPT Ads /             │
│   ChatGPT Atlas / Business / Enterprise & Edu /       │
│   Codex / Open Models / Privacy / Secure sign in /SSO │
│                                                       │
│  Footer: ChatGPT · API · Service Status · Cookies     │
│  右下浮动 "Open chat" 气泡                             │
└──────────────────────────────────────────────────────┘
```

- 标准 Intercom 模板，**没用 OpenAI 自己的设计系统**（卡片直角、字体 fallback 到 system，与 chatgpt.com / openai.com 不一致）
- 唯一统一项是 OpenAI Sans 字体族（body font-family 仍是 OpenAI Sans）

---

## 3. 设计 tokens 印象

### 3.1 色板（实测值）

| token | 值 | 用途 |
|---|---|---|
| `--bg` | `#FFFFFF` | 主背景，全场景纯白 |
| `--surface-1` | `#F3F3F3` | sidebar 浅灰 |
| `--surface-2` | `#ECECEC` | hover / 二级面板 |
| `--ink-strong` | `#0D0D0D` | 正文 / 主按钮底色 |
| `--ink-mid` | `#5D5D5D` | 副文本 |
| `--ink-weak` | `#8F8F8F` | placeholder / 三级文本 |
| `--border-faint` | `rgba(13,13,13,0.05)` | 极淡描边 |

**没有蓝色，没有品牌强彩色。** OpenAI 在产品 UI 里贯彻**单色（near-black on white）**。营销页插画里出现的暖橙/粉/紫渐变是装饰图素，不是 token。

### 3.2 字体

| 场景 | font-family | size / weight |
|---|---|---|
| chatgpt.com app | system stack（`ui-sans-serif, -apple-system, "system-ui"…`） | h1 24px / 400 |
| openai.com marketing | **OpenAI Sans**, sans-serif | h1 56.8px / 500，letter-spacing −1.7px，line-height ≈ 1.01 |
| openai.com h3 | OpenAI Sans | 28.6px / 500 |
| help center | OpenAI Sans / system fallback | h1 ≈ 22-28px |

**App 内不用品牌字体**（OpenAI Sans 只在营销页登场），降低运行时字体加载成本，也让产品看起来"无品牌、像工具"。

### 3.3 圆角

- 营销页 CTA pill：`border-radius: 8388608px`（= 完全胶囊）
- 卡片 / feature 块：`16px`
- 中等控件：`10px`
- 小标签：`6-8px`
- 帮助中心卡片：`0px`（Intercom 模板）

### 3.4 间距与栅格

- 营销页 hero 内容垂直 padding 极大（h1 上下约各 96–120px），整页约 10470px 滚动
- prompt chip 三列等宽，间距 16px，chip 本身高约 44px
- 营销页主断点 ≈ 1200px，没用窄栏（Gemini 居中窄栏）

---

## 4. 关键组件

### 4.1 App 着陆 Composer（chatgpt.com）

- 单胶囊容器，浅灰底（`#F3F3F3`），完全圆角
- 左 `+` icon：弹出**菜单**（添加照片 / 网页搜索 / 深度研究 / 思考时间更长 / 创建图片）
  - 未登录态用"登录"链接占位需登录的能力（清晰告知"这功能要登录"，不点击直接 throw）
- 中间 contenteditable，placeholder `有问题，尽管问`
- 右侧两枚按钮："开始听写"麦克风 + "语音"按钮（与听写分离，语音是实时对话模式）
- 没有 send 按钮（输入后才出现）

### 4.2 Sidebar（chatgpt.com 未登录）

- 折叠按钮（顶部）
- 操作项：新聊天 / 搜索聊天 / 图片
- 推广卡："查看套餐和定价" + 设置 + 帮助
- 底部登录卡：标题 `获取为你量身定制的回复` + 描述 + 主按钮"登录"
- 全部走浅灰 surface，没有强分割线

### 4.3 营销 Prompt Chip 三列瀑布

- DOM 里每列 chip 渲染 3 次（动画拼接技巧），三列方向交错滚动
- 每个 chip 都是 `<a href="/?prompt=…">`，点了直接带 prompt 跳进 chat
- 视觉：白底卡 + 极淡阴影 + 16px 圆角 + 一行截断
- **巧妙**：营销页用这块替代了"产品 mock 截图"的常规位置，直接表达"它能做什么"

### 4.4 营销 Feature Grid（Canvas / Sora 等并列卡）

- 8 个能力一视同仁排在 grid 里，**Canvas 不被特别突出**
- Canvas 卡：标题"协作完成写作与编程"+ 描述"借助画布功能，你能够与 ChatGPT 合作，一起完成编辑和修订等项目。" + "了解更多"链接 + 一张柔粉/橙渐变背景的工具栏 mock 图
- Sora（视频）、DALL·E（图像）、智能体等都用类似 mock 图占位，没用真实 UI 截图

### 4.5 价格表（4 列）

- 免费 / Go $8 / Plus $20 / Pro $200，等宽 4 列
- 每列：标题 + 一句话定位 + 勾选列表 + 价格 + 主 CTA pill
- 不强行高亮"推荐套餐"，靠用户自己挑（OpenAI 风格：克制）

---

## 5. Kokoro 可借鉴（3-5 条）

1. **App 内用 system font，营销页用品牌字体**：降低产品页加载成本，又让 marketing 端有辨识度。Kokoro 完全可以照这套（产品端 ui-sans-serif，落地页用一款字重高对比的几何 sans）。
2. **Composer `+` 按钮收纳能力 + 用"登录"标记未授权项**：比 disabled state 友好。Kokoro 的 Canvas / 深度研究等高级能力如果未登录可见，应当让用户清楚"要登录才能用"，而不是灰掉。
3. **极简色板 + 单一灰阶**：OpenAI 全场景没有品牌色蓝/紫强干扰，连 CTA 都是黑底白字。Kokoro 如果想做"工具感强、不像玩具"的 AI 对话，可以借这种 monochrome 立场，把彩色留给 Canvas 内的内容本身（代码高亮、文档块）。
4. **营销 hero 用"自动滚动 prompt chip 瀑布"代替产品截图**：传达"它能做什么"比"它长什么样"对 LLM 产品更有说服力，截图会过期，prompt 不会。
5. **能力 grid 平铺、不分主次**：Canvas 不被特别强调，与 Sora、图像、智能体并列。Kokoro 介绍 Canvas 时也可以放进"能力网格"，避免把 Canvas 包装成核心卖点（Canvas 本质是工作面，不是产品）。

## 6. Kokoro 应避开（2-3 条）

1. **着陆页主标题过弱**：`今天有什么计划？` 24px / 400 在白底上几乎和正文一样重，未登录新用户少了一个"这是个什么产品"的锚定。Gemini 的大字问候在这点上更友好，Kokoro 应该走 Gemini 路线而非 ChatGPT 路线。
2. **帮助中心和产品 UI 完全脱节**：Intercom 直角卡 + 默认配色，破坏品牌一致性。Kokoro 即便用第三方帮助中心，至少应把字体/色板/圆角对齐过去。
3. **未登录态 sidebar 太满**：ChatGPT 把"新聊天 / 搜索 / 图片 / 套餐 / 设置 / 帮助 / 登录卡"全暴露给游客，对首访者认知负担偏高。Kokoro 在未登录态可以更克制，把"图片 / 套餐 / 设置"这种功能项藏到登录后。

---

## 7. 数据来源置信度

| 项 | 置信度 | 备注 |
|---|---|---|
| 未登录着陆页布局与 composer | 高 | DOM 完整渲染，computed style 取值 |
| 营销页 token（字体/字号/色板） | 高 | computed style 直接读，h1 字体确认为 OpenAI Sans |
| 帮助中心模板 | 高 | 三页都已截屏存档 |
| **登录后界面（含 Canvas 实操、GPTs、Projects、Sora 入口在 sidebar 的位置等）** | **未观测** | 本会话无 OpenAI 凭据，营销页 mock 图只是宣传素材，不能当真实 UI 用 |
| 移动端 / 小屏断点 | 未观测 | 仅在 1200×691 视口抓取 |
| 暗色主题 | 未观测 | 未触发深色模式（OpenAI 产品里通过用户设置切换，未登录态不显式提供入口） |

如果后续要补充 Canvas 实操的真实 UI（编辑面板布局、工具栏、版本对比交互），需要登录态截屏或第三方录屏作为补料。
