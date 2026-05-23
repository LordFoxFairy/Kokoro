# 调研截图索引

> 抓取时间：2026-05-20
> 视口：1440 × 900
> 工具：Playwright（除 Gemini 登录后两张由用户直接提供）

---

## Gemini（主轴参考）

| 文件 | 来源 | 说明 |
|---|---|---|
| `gemini/screenshots/01-loggedin-home.png` | 用户提供 | **登录后**默认态：左导航 + 中央大字问候 + 胶囊输入框 |
| `gemini/screenshots/02-loggedin-canvas.png` | 用户提供 | **登录后**Canvas 态：左导航变窄 + 中央对话 + 右侧文档面板 |
| `gemini/screenshots/03-loggedout-landing.png` | Playwright | **未登录**着陆页，与登录后差异巨大（仅作对照） |

**保真度**：登录后两张最高，未登录页与产品 UI 关联弱。

---

## CoWork（Claude Cowork by Anthropic）

| 文件 | 来源 URL | 说明 |
|---|---|---|
| `cowork/screenshots/01-product-viewport.png` | claude.com/product/cowork | claude.com 域产品页 hero |
| `cowork/screenshots/02-product-fullpage.png` | 同上 | 全页（含 feature / FAQ / footer） |
| `cowork/screenshots/03-anthropic-product-viewport.png` | anthropic.com/product/claude-cowork | anthropic.com 域产品页 hero |
| `cowork/screenshots/04-anthropic-product-fullpage.png` | 同上 | 全页 |

**保真度**：营销页中等。**真实产品 UI（三栏 + Plan-then-Approve + Artifacts pane）需登录态**，本次未抓到，详见 `cowork/notes.md` 的"未验"章节。

---

## Claude Code

| 文件 | 来源 URL | 说明 |
|---|---|---|
| `claude-code/screenshots/01-product-viewport.png` | claude.com/product/claude-code | 营销页 hero（Surface Tabs 关键证据） |
| `claude-code/screenshots/02-product-fullpage.png` | 同上 | 全页 |
| `claude-code/screenshots/03-docs-mintlify.png` | code.claude.com/docs/en/overview | Mintlify 文档站三栏布局（左目录 + 主内容 + 右 TOC） |

**保真度**：营销页 + 文档站直接来自官方页面，高保真。

---

## Manus

| 文件 | 来源 URL | 说明 |
|---|---|---|
| `manus/screenshots/01-home-viewport.png` | manus.im | 首页 hero（产出物 chip 关键证据） |
| `manus/screenshots/02-home-fullpage.png` | 同上 | 全页（含 feature / pricing / 三步流程） |

**保真度**：营销页中等。**Agent 工作台真实 UI** 仍需登录或视频演示，本次未抓到。

---

## ChatGPT

| 文件 | 来源 URL | 说明 |
|---|---|---|
| `chatgpt/screenshots/01-chatgpt-home-viewport.png` | chatgpt.com | 未登录着陆页（含 composer 单胶囊输入） |
| `chatgpt/screenshots/02-chatgpt-home-fullpage.png` | 同上 | 全页 |
| `chatgpt/screenshots/03-overview-viewport.png` | chatgpt.com/zh-Hans-CN/overview | 产品介绍页（能力网格平铺） |
| `chatgpt/screenshots/04-overview-fullpage.png` | 同上 | 全页 |

**保真度**：未登录态 + 营销页。**登录后真实产品（Canvas / GPTs / Projects）** 需账号，本次未抓到。

---

## 全局保真度提醒

1. **登录后真实产品 UI** 是最高价值参考，但本次只有 Gemini 拿到（用户直接提供）
2. **营销页 / 落地页**和真实产品的视觉差异普遍较大，特别是 Gemini / ChatGPT 这类把营销做得非常重的产品
3. **Anthropic 系**（Claude Code / CoWork）营销页与产品页的视觉语言比较接近，可参考度高
4. **Manus** 已被 Meta 收购，处品牌过渡期，色板/字体可能近期变动
