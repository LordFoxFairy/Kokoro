# Variant A · 米 + 木

Kokoro 视觉原型，A 套色板（暖中性 / 低饱和 / 亲近）。

## 是什么

低保真但视觉真实的静态 HTML 原型，用来验证「心」路线在 A 套色板下的实际观感。
**不是生产代码**——纯 HTML/CSS + 极少 vanilla JS，无构建工具、无 webfont CDN。

## 文件

### 页面

| 文件 | 对应规格 |
|---|---|
| `index.html`           | 首屏（Home） · `docs/product/06-screens/home.md` |
| `chat.html`            | 对话视图 · `docs/product/06-screens/chat.md` |
| `canvas.html`          | Chat + Canvas 三栏 · `docs/product/06-screens/canvas.md` |
| `share.html`           | 分享公开页（含 sticky CTA） · `docs/product/06-screens/share.md` |
| `templates.html`       | 模板库浏览 · `docs/product/06-screens/templates.md` |
| `settings.html`        | 设置 / 个性化（memory 三层） · `docs/product/06-screens/settings.md` |
| `chat-error.html`      | 对话错误态变体（Canvas 失败 + 心人格 copy） |
| `chat-limit.html`      | 对话额度到达变体（暖色 inline 提示） |
| `components.html`      | 组件库 specimen 集 |
| `interactions.html`    | 9 个交互 pattern 故事卡 |

### 样式（v0.3 物理拆分）

| 文件 | 内容 |
|---|---|
| `css/tokens.css`     | CSS 自定义属性（color / type / space / motion / radius / shadow） |
| `css/base.css`       | Reset + layout (.app / .sidebar / .main / .topbar / .stage / .split) |
| `css/components.css` | 原子 & 分子组件（BEM only，无 legacy alias） |
| `css/patterns.css`   | 模式（chat / canvas / share / templates / settings / gallery） |
| `css/utilities.css`  | utility classes + scrollbar + reduced-motion |
| `styles.css`         | manifest，仅 `@import` 上述 5 个文件（向后兼容） |

新页面应直接 link 5 个 css 文件而非 `styles.css`。

### 验证

| 截图 | 用途 |
|---|---|
| `screenshots/01-home.png` 到 `08-mode-switcher-open.png` | 8 张基线，验证 CSS 拆分零回归 |
| `screenshots/09-templates.png`                | 模板库 full page |
| `screenshots/10-settings-personalization.png` | 设置 · 个性化 + 数据 full page |
| `screenshots/11-share-sticky-cta.png`         | Share + sticky CTA |
| `screenshots/12-chat-error.png`               | 对话错误态 |
| `screenshots/13-chat-limit.png`               | 对话额度到达 |

## 怎么打开

由于 5-file CSS 使用相对路径，建议起 HTTP server 而非 `file://`：

```bash
cd docs/prototypes/variant-a-mi-mu
python3 -m http.server 8765
# 访问 http://localhost:8765/index.html
```

也可双击单个 HTML（多数浏览器支持本地相对路径 CSS）。

## 设计取舍

- **色板**：A 套 `tokens.md` 原值，主色 `--color-bg #FAF7F2`，accent `--color-accent #8B6F47`
- **字体**：system stack（PingFang SC / Songti SC / Kaiti SC），离线可用
- **圆角**：主输入框、主按钮 24px；卡片 16px；chip 999px（pill）
- **动效**：仅做 loading pulse 与 streaming cursor，遵守 `motion.md` 的「呼吸不旋转」
- **copy**：严格走 `voice-and-tone.md`，全部真实草稿文案，无 placeholder
- **BEM**：第三轮起所有 class 都已规范化（`.message--user` 而非 `.bubble-user`）

## v0.3 还债 + 新增（2026-05-21）

- ✅ `styles.css` 2300 行物理拆分为 5 个文件
- ✅ Legacy class alias（`.bubble-user` / `.brand-mark` / `.sidebar-item` 等）全部清掉
- ✅ 新增 `templates.html`（含 8 张真实 SVG 模板缩略图）
- ✅ 新增 `settings.html`（个性化两区视觉重量明显分隔）
- ✅ Share 加 sticky CTA bar
- ✅ Chat error / limit 两个状态变体
- ✅ 补缺组件：`.avatar` / `.badge` / `.inline-link` / `.btn--danger` / `.btn.is-loading` / `.input-pill.is-disabled` / `.save-state` / `.message--error` / `.limit-notice`
- ✅ Canvas 顶栏加自动保存指示

## 还没做

- 暗色主题（待 visual-language.md 拍板）
- 库 · 收藏页（library.html）
- 模板复用 modal 流程（点"用这个" → 输入场景 → 进 Canvas）
- 分享弹层 / 复制反馈交互
- OG 图模板（需 server-side 渲染）
