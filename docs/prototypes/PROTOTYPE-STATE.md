# Kokoro 原型设计状态 · variant-a-mi-mu 高保真原型

> 原型/设计阶段文档，最后更新 2026-05-24。记录高保真 HTML 原型的视觉铁律、信息架构与文件地图，作为产品视觉与交互方向的设计参考。
> 范围：本文件是**原型设计阶段**状态，非当前工程状态。三仓生产系统的当前进度见根目录 `claude-progress.md`、任务见 `tasks/todo.md`。

## 1. 这是什么
**Kokoro（こころ）** = 一个「慢一点、和它一起把想法做出来」的暖色 AI 创作产品。
当前产物是一套**高保真静态原型 / 设计稿**（vanilla HTML + CSS + 极少 JS），用来定产品形态与视觉，不是生产代码。

- 原型目录：`docs/prototypes/variant-a-mi-mu/`（**53 个 .html + 10 个 css/**）。
- 本地预览：在该目录下 `python3 -m http.server 8753`，浏览器开 `http://localhost:8753/<page>.html`。
- 每页可单文件直接打开（ADR-007）；页面专属样式写**页内 `<style>`**（BEM 前缀），共享样式在 `css/`。

## 2. 视觉铁律（违反即错）
- 风格：**米 + 木 + 纸感**。bg `#FAF7F2`、surface `#FFFFFF`、accent 木色 `#8B6F47`、accent-soft `#EBE0CF`、text `#2B2520`；暖色补充 `#FBF6EC #F3EAD6 #E7CBA0 #C8A26B #7A8B6B(绿) #B36B5A`。全部走 `css/tokens.css` 的 CSS 变量。
- 标题用衬线 `var(--font-serif)`，数字/Key/代码用 `var(--font-mono)`。
- **绝对禁止：cyan/青色、dark mode、glassmorphism 毛玻璃、霓虹。** play键/进度/选中环/开关一律木色或暖绿。
- 交互尽量纯 CSS（`<details>/<summary>`、`radio:checked + label`、`:hover` flyout），minimal JS。

## 3. 核心概念模型（重要，别推翻）
- **功能组件 = 通用生成器**（muapi Image Studio 那种）：身份大标题 + 模式 tab + 模型下拉 + 参数 + 「生成」。共 7 个：图片 / 视频 / 数字人 / 音频 / 设计 / 文档 / 站点。
- **应用场景 = 案例**：组件 + 预设参数的具体例子（探店海报、给妈妈讲 AI 课件…）。归「案例」（`templates.html`），不是独立组件。营销 = 跨组件的场景，也在案例里。
- **积分**：普通用户消耗「积分」（不是「次」）。全站额度文案已是积分。
- **角色**：普通用户**看不到** 模型/Key 配置；只有**管理员**在 `admin-models.html` 配模型、填 Key、设每模型「N 积分/次」。**管理员启用的模型 = 用户创作页模型下拉里能选到的**（两者绑定）。
- 两态流程：空组件页（生成器）→「生成」→ 产物页 `canvas-*-result.html`。

## 4. 信息架构（侧边栏，全站一致，见 `css/sidebar-creative.css`）
参照 pollo.ai 的单列分组（暖色化），**不是两个并列板块**：
```
新对话 / 搜索(→search.html)
创作   🖼图片 🎬视频 🗣数字人 🎵音频 ✨设计 📝文档 🌐站点   ← 组件，:hover 右侧弹出子能力 flyout
进阶   🤖智能体 🔀工作流                                   ← 占位页（用户说后续再定，别深做）
发现   📚案例 🧩Skill Hub 🔌MCP Hub
─────  👥团队 🗂库·收藏
最近 … / user-row(→settings.html)
```
- 组件 flyout 的子能力（如 图片：文生图/图生图/局部改图/扩图/高清放大/抠图去背）都**指向该组件页**；组件页用 `.fn-modes` 的模式 tab 承载这些模式（`css/function-tool.css`，通用 `radio:checked + label` 激活，支持任意模式数）。

## 5. 关键文件地图
**应用首页/对话**：`index.html`（登录后首页：问候 + 输入框 + 首页 showcase[7 组件代表案例，CSS radio-tab] + 模板 chips）、`chat.html`。
**7 个组件页（muapi 式生成器）**：`canvas-image / canvas-video / canvas-lipsync / canvas-audio / canvas-design / canvas-courseware / canvas-landing`.html。
**产物页**：`canvas-*-result.html`（含 `canvas-audio-result.html`、写信=`canvas-result.html`）。左 chat + 右 canvas-pane。
**案例库**：`templates.html`（案例墙，卡片链到各 *-result）。
**Skill/MCP/Teams**：`skill-hub.html`、`mcp-hub.html`（暖色市场卡，`css/hub.css`）、`teams.html`（**群聊式**，两种群：讨论群[纯人] / 智能体小队[我+多 agent 协作]，房间栏 CSS radio 切换）。
**进阶占位**：`agents.html`、`workflows.html`（轻量概览，刻意不深做）。
**公开漏斗**：`marketing.html`（落地页）、`login.html`（登录/注册）、`pricing.html`（订阅 3 档：免费/Plus¥39/团队¥99）。
**设置/管理员**：`settings.html`（账户·订阅[积分+升级→pricing] / 个性化 / 数据；**已移除**「AI 模型与 Key」段——那是管理员的事）；`admin-models.html`（**管理员专属**模型管理表格，5 组 42 模型，每行 模型/供应商/Key/积分/状态开关；不在普通侧栏，按 URL 进）。
**设计系统页**：`components.html`、`interactions.html`、`gallery.html`（与案例略重叠）。
**CSS**：`tokens / base / components / patterns / utilities`（共享基座）+ `sidebar-creative`（创作侧栏 + flyout）+ `function-tool`（组件生成器：模式 tab/模型下拉/数量段控）+ `hub`（Skill/MCP Hub 卡）+ `studio-nav`（旧折叠侧栏，部分页仍引但已被 sidebar-creative 取代）+ `attach-menu`（「+」下拉）。

## 6. 操作约定（坑）
- **HTML 多为 `chmod 444` 只读**：脚本批量改前要 `chmod u+w`，改完 `chmod 444` 复原。Edit 工具前需先 Read。
- **浏览器缓存激进**：预览验证时对 `<link>` 加 `?v=Date.now()` 破 CSS 缓存；HTML 导航加 `?v=N`。**文件内容是事实，截图可能陈旧**。
- 跨页机械改动（侧栏/文案）用 **python 正则脚本**最稳；新页面创建可派 subagent（独立文件不冲突），同一文件只允许一个 writer。
- 全站改完务必跑：死链检查（`grep href=...html` 比对文件存在）+ 关键页 `curl` 200 + `git status` 确认没动已跟踪文件（原型全在 untracked `docs/`）。

## 7. 参考（只读，**绝不修改**）
- `../pollo.ai`、`../Open-Generative-AI`（同级目录，thefoxfairy/ 下）。Open-GenAI：ImageStudio=t2i/i2i、VideoStudio=t2v/i2v/v2v；muapi 顶栏 = 一排功能组件。
- 仿设计前先亲自打开/读透参考再动手（踩过 3 次坑）；大改先做对 1 个锚再铺量。

## 8. 已知未做 / 取舍（不是 bug）
- **响应式/移动端**：未做，全桌面布局（ADR-007 桌面优先）。要做是单独大工程（50+ 页重排），需专门一轮。
- **智能体 / 工作流**：刻意只占位（用户要后续再定）。
- **旧场景生成页**（canvas-poster/deck/mindmap/website/app/chart、canvas.html 等）：已从侧栏移除引用、不在主流程；仍存在、无死链，其成品经 案例 / *-result 呈现。
- 小技术债：`index.html` 的创作侧栏用页内 `<style>`（其余用共享 `sidebar-creative.css`，两份）；`gallery.html` 与案例库略重叠；侧栏「案例」vs 页面标题「案例库」措辞。
- 所有交互是**视觉占位**（toggle/模型下拉/生成 不带真实逻辑）。

## 9. 相关文档
`docs/task.md`（跨会话任务）、`docs/lessons/`（操作教训）、`docs/decisions/`（ADR）、`docs/product/`（产品形态，含 canvas-types）。
