# Kokoro 任务状态（跨会话）

> 主 agent 维护；子 agent 只读。会话开始读一次。

## 进行中：Canvas 全量产物矩阵 buildout（2026-05-23 起）

用户拍板：**全量产物矩阵**，且 **Open-Generative-AI 的所有 studio 也要各做一个 Kokoro 页面展示**。
"少了太多了" = ①产物类型太少 ②现有页不够丰满 ③缺整块功能区深度 ④动效/活着的感觉不足 ⑤Open-GenAI 全功能搬过来。

### 执行约束（务必遵守）
- 每个新 canvas 页**自包含**：复用共享 shell（`sidebar`/`chat-view`/`canvas-toolbar`/`canvas-controls`/`chip`/`btn`，来自 `css/components.css`），**类型专属样式写进页内 `<style>` 块**（BEM，`.canvas-<type>__*`）。**不准改 `css/*.css`**——这样多个子 agent 可并行、互不冲突，也保持单文件可开（ADR-007）。
- 视觉铁律：米+木+纸感（bg #FAF7F2 / surface #FFF / accent #8B6F47 / soft #EBE0CF）。**严禁** dark/cyan/glassmorphism（Open-GenAI 是深色+cyan，只吸收产品模式与交互流程，不吸收视觉）。
- 模板基底：`canvas-video.html`（最新，分镜型 + 页内 style 范式）、`canvas-courseware.html`（缩略条+大图）、`canvas-poster.html`（hero+候选+controls）。
- Open-GenAI / pollo.ai 仓库**只读**。pollo.ai 是空壳，无源码。

### 矩阵与状态

| 类型 | 映射参考 | 文件 | 状态 |
|---|---|---|---|
| 小红书海报 | ImageStudio（排版向） | canvas-poster.html | ✅ 已有 |
| 一页落地页 | — / Manus | canvas-landing.html | ✅ 已有 |
| 学习课件 | Open-Poe / ImageStudio history | canvas-courseware.html | ✅ 已有 |
| 写一封信（信件/文档） | — | canvas.html | ✅ 已有 |
| 想法可视化 | Vibe-Workflow node builder | canvas-mindmap.html | ✅ 已有 |
| **短片/视频（分镜）** | **VideoStudio / CinemaStudio** | **canvas-video.html** | ✅ 本轮新建（模板锚） |
| 会说话的照片 / 对口型 | LipSyncStudio | canvas-lipsync.html | ✅ 已建并复查 |
| 演示稿 / Pitch Deck | DeckVibe / Manus slides | canvas-deck.html | ✅ 已建并复查 |
| AI 图像 / 绘画（多模型文生图） | ImageStudio（纯生成向，区别于海报排版） | canvas-image.html | ✅ 已建并复查 |
| 营销物料组 | MarketingStudio | canvas-marketing.html | ✅ 已建并复查 |
| 设计稿 / 品牌视觉 | DesignAgentStudio / Open-AI-Design-Agent | canvas-design.html | ✅ 已建并复查 |
| 小应用 / 小工具 | AppsStudio | canvas-app.html | ✅ 已建并复查 |
| 数据图表 / 看板 | 产物矩阵 | canvas-chart.html | ✅ 已建并复查 |
| 多页网站 | 产物矩阵（区别于一页落地页） | canvas-website.html | ✅ 已建并复查 |
| 封面图（公众号/视频封面） | poster 变体 | — | ❌ 并入 poster/image（避免冗余，不单独做） |

**dev 向 studio —— ❌ 用户拍板：三个都不做**：
- AgentStudio / McpCliStudio / WorkflowStudio 全部不做独立 canvas（与"消费者、反 dev"定位 ADR-002 冲突）。已定，不再讨论。

### 配套
- [x] `gallery.html` 全产物菜单页 ✅ —— 14 张卡（视觉创作6/文档表达4/站点工具4），href 全对（Playwright 实测）；首页"更多…"chip 已接通 → gallery.html
- [x] 动效与"活着" ✅ —— mindmap 节点补成**真 :hover**（已验证 fill #FFF→#FBF6EC + 阴影）；视频页流光+播放呼吸；既有 8 个 @keyframes + reduced-motion 守卫
- [x] 最终复查 ✅ —— 27 页全 HTTP 200 + favicon×1 + 5 css link 齐；新 9 页 + gallery 全部达标
- [x] 可达性 ✅ —— 全产物经 gallery 入口可达（首页"更多…"→gallery）；首页 5 chip 直达各 canvas

### 仍可深化（非本轮"产物矩阵"范围，建议下轮，已与用户口径一致：保持节奏不硬塞）
- 功能区（模板市场 / 库 / 分享 / 设置）页已存在且可加载，内容可再加厚（真实数据流、空/载/错态矩阵）
- 大文件 components.css(50KB)/patterns.css(59KB) 可按模块 @import 拆小（已采纳"拆文件"偏好；新类型已全部 page-local，未来不再塞 monolith）

## ✅ 本轮交付（全部已建并逐页 Playwright 复查）
新增 9 个 canvas 产物页：video / lipsync / deck / image / marketing / design / app / chart / website；
+ gallery 全产物菜单；产物总数 14 类。Open-GenAI 全消费向 studio 已映射，dev 工具(Agent/McpCli/Workflow)按用户拍板弃。

## 第二批 · 交互 + pollo.ai/muapi 功能补充（用户：主要要他们的功能，风格保持米+木）
- [x] 聊天框"+"附件下拉 ✅：CSS-only `<details>`（向上弹，6 项+分隔线），新模块 `css/attach-menu.css`，铺到 20 页；Playwright 实测弹出 + "+"转"×" + 暖色无 cyan。
- [🟡] 左侧栏「工作室」常驻导航（A 方案）：14 产物 2 列网格 + 当前页高亮，新模块 `css/studio-nav.css`。**17 页已加并实测**（canvas-video 短片高亮、窄侧栏不溢出）；**7 页**（chat/canvas/templates/templates-detail/first-time/chat-error/chat-limit，因 模板库 href 不一致被漏）补加中，顺修它们 模板库→templates.html 的旧 bug。目标 24 页。
- ⚠ 维护注意：studio-nav 的 14 项 grid **硬编码在每页**（无 JS/include）；以后加新 studio（如 effects/restyle）要一次性同步所有页的 grid（14→N）+ gallery。
- 节奏：effects/restyle 等 studio-nav 24 页齐了再建（克隆最新范式）；建完做一次 grid 14→16 + gallery 同步。
- 联网研究（pollo.ai + muapi 托管版）缺口，按 ROI：
  1. [🔴] `canvas-effects.html` — **AI 温情特效模板墙**（pollo 招牌）：精选 8–12 个温情向特效卡（拥抱/牵手/老照片复活/全家福动起来），避开猎奇 explode/melt；选特效→传照片→生成短视频播放器。**最高 ROI**。
  2. [🔴] `canvas-restyle.html` — 一键换风格/重绘（吉卜力/插画/手绘/水彩）+ 原图↔结果对比滑块。
  3. [🔴可选] 多图参考一致性（锁同角色跨图）——倾向并入 `canvas-image` 的"参考图槽"，非独立页。
- ❌ 不做：Cinema 镜头参数（太专业超消费级）/ Virtual Try-On（电商垂直）/ Workflow 节点编排（开发者向，与"左对话右canvas"骨架冲突）。
- 节奏：等 attach 下拉铺完复查 → 派 effects + restyle（克隆已含 attach 下拉的 canvas-video 范式，保证新页也有"+"菜单）。

## 第三批 · 功能 vs 模板库 重构（用户纠正：我之前理解错了）
**关键认知**（用户拍板「工具态改造」）：
- **功能(功能组件)** = 少数通用生成器工具：输入 + 模型选择 + 参数 chips + 生成 + 结果区。空态 = 图标+大标题+副文案+就绪的生成器（不是灰盒占位）。参数差异：Image 有「数量1-4」、Video 有「时长/首尾帧」。
- **模板库** = 具体场景模板 = 通用功能 + 预填参数（模型+任务+prompt）+ 营销/教学外壳；卡片墙，点卡片带预设跳进对应功能。
- **我之前的错**：14 个"工作室"做成了**填好的场景故事（案例）**，更像模板库内容，不是通用功能组件。
- **方向 = 工具态改造**：保留 14 个入口，但每页从"填好的故事"改成"通用功能工具的空/就绪态"；具体场景移进模板库。
- 新模块 `css/function-tool.css`（`.canvas-stage--tool` / `.fn-tool__*`）。
- 参考：muapi `/studio/video`·`/studio/image`、pollo `/`·`/video-effects`（只吸收结构，深色cyan视觉不要）。

**布局纠正（用户第二次纠正，关键）**：功能页 = **输入+参数在左侧 composer**（fn-params 参数行 + input-pill），**右侧 canvas 是「产物」**——未生成=就绪空态（fn-empty：图标+标题+"会在这里显影"+虚线框）+ fn-presets 模板卡。**绝不**把输入表单放右侧产物区（我之前错在这）。`function-tool.css` 已按此重写（`.fn-params`/`.canvas-stage--fn`/`.fn-empty`/`.fn-preset`）。

**布局再纠正（用户第三次：直接看 muapi/pollo 的 img/video studio 设计）**：功能页 = **单列生成器**（不是左右分栏！）。参照 muapi Studio：左 sidebar（studio nav）+ 右 main 单列 = 居中身份(图标+两行大标题"开始创作/X工作室"+副) → 中部"从模板开始"starters → **底部全宽生成栏**（行1：上传图标 + 描述输入；行2：模型/比例/时长 chips + 生成按钮）。`function-tool.css` 已重写为 `.fn-studio`/`.fn-bar`/`.fn-starter`。

**再两条对齐（用户）**：
- **产物 = 结果态会出现**：工作室空态→点生成/选模板→**产物 canvas 出现**（=之前做的富画布：分镜/海报/课件/图表…）。已把 13 个富画布备份成 `*-result.html` 作结果态，不删；生成/模板将来接到它们。两态：空 studio → 生成 → 产物 canvas。
- **功能不混场景**：功能页**只放功能**（生成器），不嵌模板/场景卡（已从 fn-studio 删掉 starters）。场景/案例归**模板库**，功能↔场景一对一但分开展示（避免相互影响、便于维护）。

进度：
- [x] 锚样板 `canvas-video.html` = 干净单列生成器（图标+开始创作/X工作室+副 → 底部生成栏，无场景卡），Playwright 验证通过，截图 `screenshots/40-canvas-video-studio.png`。
- 待用户点头 → 用此版铺其余 13（每页替换整个 `<main>` 为 fn-studio，customize 图标/标题/上传/参数/starters；保留各页 sidebar 高亮）。
- 注：前两轮铺设子 agent 均已 STOP；部分页被改坏，重铺整 main 会覆盖修正。
- 教训：连续 3 次设计没理解到位（输入放右→分栏→才到单列）。根因=没先深入看参考站就动手。已记 lesson。
- [ ] 其余 13 工作室页 → 各自工具态（参数按功能取舍）。
- [ ] 模板库 `templates.html` 充实：把场景做成卡片墙（点击带预设进功能）。
- [ ] effects/restyle（pollo 招牌）此前规划——重新评估：很可能就是"模板库里的特效卡"，未必是独立功能页。

## ✅ 第三批完成：14 个页全部 = 单列功能生成器空态（file-grep 验证 1×fn-studio+1×fn-bar、0 残留、标题对）。富画布已备份 `*-result.html` 作结果态。
## ✅ 第四批完成：侧边栏「应用功能」1 列可滚列表（14 项）+ 下方「案例库」入口；`studio-nav.css` grid→flex 单列+overflow；全站标签 工作室→应用功能、模板库→案例库（含 *-result）。已 Playwright 验证。
## 待续：① 案例库页(templates.html)充实成案例墙(用 *-result 富画布,功能↔案例一对一) ② 生成/模板 接到结果态 ③ 小尾巴：studio-nav aria-label 仍"工作室"、个别注释提"模板库"、recent 被挤(可后调)

## 第四批 · 侧边栏改造（用户：工作室→应用功能 1 列；下加案例库）—— 等 rollout 完再做（避免同文件冲突）
- 左侧「工作室」**改名「应用功能」**，从 2 列网格 → **1 列竖排列表**（14 项，可往下滚动）。改 `css/studio-nav.css`（grid→单列 + 列表项样式 + 滚动）+ 全站 sidebar 标签。
- 「应用功能」**下面加「案例库」**入口（= 场景案例库，和功能一对一、分开陈列）；倾向把现「模板库」并/改成「案例库」，案例 = 之前备份的 `*-result.html` 富画布。
- 影响全站 ~24 页 sidebar → 待 main rollout（a9055/ab5a/a48b）完成复查后，专开一轮 subagent 改 sidebar，避免与 rollout 撞同一批文件。

## 已完成（本会话前段）
- 首页导航修复（模板库/库·收藏 链接与高亮）、首屏 chip 接通各 canvas 类型
- 想法地图画板比例修复（板随地图横向比例，内容占比 36%→60%）
- 全站 favicon（favicon.svg + 17 页引入）
- 写一封信补进 canvas-types.md（表+理由）+ README 同步
