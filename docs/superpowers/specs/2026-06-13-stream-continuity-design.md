# Stream 连续性设计 — 让流式 turn 从「机械替换」变「生命生长」(Scope A)

> 定位:在现有 ordered-parts/turn=run/process-below-text 结构(全部保留、不推翻)之上,只攻**转场质感**——首 token、过程展开/收起、live→settled 三处硬切,改为同一活体的连续形变。
> 范围:用户选定 Scope A(连续性优先)。改动面 = `assistant-turn.tsx` + `segment-process.tsx` + `activity.css`,**不碰 reducer / state-schema / store / use-conversation**。可读性(B)/持久化(C)/密度(D)列入 backlog 分期。
> 验收:三处转场无跳变(Playwright 真机录帧 + getComputedStyle);现有 session-shell/segment-process 测试零回归;`prefers-reduced-motion` 下退化为瞬切且仍可用。
> 来源:2026-06-13 UI 现状深度调研(33 文件,reducer→component→CSS 全链)+ 研究列出的 10 个粗糙点中归属 A 的 #7.1 / #7.5 / #7.8。

---

## 1. 不变量(设计不得破坏)

1. **结构锁**:一 turn 一头像一竖脊;每段答案气泡在上、过程在下;ordered-parts 按 seq 真实时序;collapse-on-settle 的 `open = manualOpen ?? live` 语义不变。
2. **测试钩子锁**:forming 态仍含文本「正在思考」;重连态仍含「重连中…」+ `data-anchor="reconnecting"`;过程摘要 settled 文案仍含「处理过程」/工具计数;`.kk-caret` 仍在尾段有正文时出现。
3. **a11y 锁**:过程块可键盘展开/收起,`aria-expanded` 反映状态;减少动态偏好下无强制动画。
4. **零行为改**:渲染哪些步骤、折叠分组、消息归属一概不动——只改「同一内容如何转场呈现」。

---

## 2. A1 — 共享气泡骨架(首 token 不跳变)

### 现状(债)
`assistant-turn.tsx` 在尾段二选一渲染:`<FormingBubble>`(`.kk-msg__bubble--forming`,inline-flex、浅灰混合底、小圆角)**或** `<div class="kk-turn__answer"><Markdown/></div>`(块级、实底 surface、大圆角)。首 token 到达 = React 卸载前者挂载后者 → 盒模型/底色/圆角全变,肉眼跳变。

### 目标态
尾部 live 段**恒渲染同一个气泡盒** `.kk-turn__answer`,新增 `data-state`:
| data-state | 触发 | 盒内内容 |
|---|---|---|
| `forming` | `liveSegment && !message`(过程先到、正文未到) | 脉冲点 + 标签(「正在思考」/ 重连时「重连中…」) |
| `streaming` | `liveSegment && message.content.length > 0` | Markdown 正文 + `.kk-caret` |
| `settled` | 非 live 或已落定 | Markdown 正文 |

- **盒子三态视觉一致**:底色/圆角/内距/最小高度由 `.kk-turn__answer` 统一定义,`data-state` 只切换**内容层**。
- **内容交叉淡变**:盒内放两层——`.kk-turn__answer-forming`(脉冲+标签)与 `.kk-turn__answer-body`(Markdown),按 data-state 用 opacity 过渡互替(forming 淡出、body 淡入),首 token 时脉冲在原位被文字接替,而非元素跳换。
- **重连锚点迁移**:`data-anchor="reconnecting"` 从旧 forming 元素移到 `.kk-turn__answer[data-state="forming"]` 上,样式钩子不变。
- 非尾段/历史段:`data-state="settled"`,与今天等价。

### 技术注意
- `FormingBubble` 组件不再独立成盒,降级为 forming 内容层(脉冲+标签)。
- 早期段(非 live、过程齐但无文本)今天塌成纯过程块——A 不处理(属 B 的「中间段占位」),保持现状。

---

## 3. A2 — 过程块呼吸(展开/收起高度过渡)

### 现状(债)
`segment-process.tsx` 用 `<details open={open}>`+`<summary>`,React 受控 `open = manualOpen ?? live`。浏览器对 `<details>` 内容是 `display:none` 硬切,无高度过渡;仅 chevron 有 150ms transform。live→settled 收起时内容「啪」消失。

### 目标态
保留受控语义,换可动画的盒:
- `<details>/<summary>` → `<div class="kk-process" data-open>`+`<button class="kk-process__summary" aria-expanded aria-controls>`。
- body 包一层高度动画器:`.kk-process__reveal { display:grid; grid-template-rows:0fr; transition:grid-template-rows 200ms ease } [data-open] .kk-process__reveal { grid-template-rows:1fr }`,内层 `.kk-process__body { overflow:hidden; min-height:0 }`。
- 受控 `open` 仍来自 `manualOpen ?? live`;点击 summary `onClick` 翻转 `manualOpen`(替代原 `onToggle`)。
- `prefers-reduced-motion: reduce`:`transition:none`,grid 立即到位(瞬切,功能不变)。

### a11y
`<button aria-expanded={open} aria-controls="proc-{segmentId}">` + body `id="proc-{segmentId}"`;键盘 Enter/Space 翻转。语义不弱于原 `<details>`。

---

## 4. A3 — live→settled 摘要交叉淡变

### 现状(债)
summary 在 live(火花 +「思考中…」+ 三点脉冲)与 settled(火花 +「处理过程 · N 工具 · M 子智能体」)间瞬切文本与点缀。

### 目标态
- 摘要标签包 opacity 过渡:`.kk-process__title { transition:opacity 160ms ease }`;live↔settled 文案切换时短暂淡变而非硬跳。
- `.kk-process__live` 三点脉冲在转 settled 时 opacity→0 淡出(150ms),不瞬隐。
- 文案内容逻辑不变(仍由 live 布尔决定),只加过渡。

---

## 5. 验证矩阵

| 项 | 手段 |
|---|---|
| A1 盒子三态底色/圆角/内距一致 | Playwright getComputedStyle 三态对比 background/border-radius/padding 恒等 |
| A1 首 token 不换元素 | 同一 `.kk-turn__answer` 节点引用跨 forming→streaming 存活(非卸载重挂) |
| A1 测试钩子保全 | 现有 session-shell.test.tsx forming/reconnecting/caret 断言零改动通过 |
| A2 高度过渡 | Playwright 录 open 切换帧 + 断言 `.kk-process__reveal` transition 生效;reduced-motion 下 transition:none |
| A2 a11y | button aria-expanded 随 open 翻转;键盘可操作 |
| A3 摘要淡变 | live→settled 时 `.kk-process__title` opacity 过渡存在 |
| 全局 | tsc 0 + 全 vitest 绿 + `:3100` 真机走一轮真实 LLM 流式录三处转场 |

---

## 5b. 落地记录(2026-06-13,✅ 完成)

A1/A2/A3 全部实现 + 真机验证 + 对抗复核加固:
- **实现** commit `072b953`:A1 共享盒(forming/streaming/settled 同一 `.kk-turn__answer`,data-state 切内容)/ A2 `<details>`→受控 `<div>`+`<button>` + grid `0fr↔1fr` 三层 reveal>clip>body / A3 标题 key 翻转淡入。
- **真机实证**:forming↔settled 盒模型逐字节相同(bg/radius/padding);展开 reveal=31px、收起=0px、过渡 0.22s。
- **用户逮到的 bug**:单层 grid 收起残留 31px 空盒 → 修成三层(clip 纯裁剪层)。
- **对抗复核** workflow `wf_b3a5bfd3-42d`(5 lens,14→6 确认),commit `04d8910` 修:
  - #4(真 a11y 回归):折叠内容仍在无障碍树 → `inert={!open}`(AT 隐藏 + 不可聚焦,不设 display:none 故动画仍可动)。真机验证 inert 双向 + reveal 0↔31px。
  - #3:展开按钮缺暖木 focus-visible 环(details→button 丢的)→ 补 inset box-shadow,验证 `rgb(139,111,71)`。
  - #5/#6:补 reveal>clip>body 结构断言 + A1 同元素复用身份测试(证明段内 forming→streaming 不 remount)+ data-state 三态断言。
  - #1(降级 cosmetic):scaffold→首段确是 remount → 诚实收窄注释(段内成立,scaffold 边界窄路径同尺寸 opacity 重淡入无跳动)。
  - #2(既有非回归):空 content message 空窗 → backlog(改最小,不在本 commit 顺手改)。
- 195 vitest + tsc + lint + 生产 build 全绿。

---

## 6. backlog(本轮不做,分期)

- **B 可读性**:turn 级状态微行(重连/分步在途随时可读)、中间段占位骨架、运行工具更强活动信号、长思考 fade-edge。
- **C 持久化**:`manualOpen` 落 store(随会话快照存)。
- **D 密度**:工具/子代理一致展开模型、多工具失败摘要聚合。
触发:A 落地真机验收后,按你对"还差哪口气"的反馈决定下一期。
