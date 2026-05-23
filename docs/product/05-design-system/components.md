---
status: 🟡 草稿
updated: 2026-05-20
---

# 核心组件清单

> 本文件 = MVP 范围内必备的组件、每个组件的关键状态、参考竞品、以及 Kokoro 的差异点。
> 视觉细节走 [tokens.md](./tokens.md)，动效走 [motion.md](./motion.md)，交互模式走 [patterns.md](./patterns.md)。

## 摘要

- 列出 12 个 MVP 必备组件。
- 每个组件四列：用途 / 关键状态 / 参考竞品 / Kokoro 差异点。
- 复杂组件追加 ASCII 示意。
- **差异点的统一原则**：暖底 + 大圆角 + copy 有温度 + 不用冷蓝 / spinner / 强阴影。

---

## 组件总表

| # | 组件 | 优先级 | 主要出现位置 |
|---|---|---|---|
| 1 | Sidebar item | P0 | 左导航 |
| 2 | Input pill（主输入框） | P0 | Chat 区底部居中 |
| 3 | Model switcher chip | P0 | Input pill 内右 |
| 4 | Send button | P0 | Input pill 内右末 |
| 5 | Chat bubble | P0 | Chat 区消息流 |
| 6 | Canvas card | P0 | Chat 区内 Canvas 触发卡 |
| 7 | Template card | P0 | 模板库 / 首屏 chip |
| 8 | Share button | P0 | Chat 区文档卡片 / 产物分享页（**不再**挂在 Canvas 顶栏） |
| 9 | OG image | P0 | 产物分享落地页 |
| 10 | Empty state | P0 | 各页空态 |
| 11 | Loading pulse | P0 | 所有等待场景 |
| 12 | Error toast | P0 | 全局错误 |

---

## 1. Sidebar item

| 维度 | 内容 |
|---|---|
| 用途 | 左导航中的可点击行：新对话 / 搜索 / 模板库 / 最近对话项 等 |
| 关键状态 | default / hover / active（当前选中）/ disabled / pressed |
| 参考竞品 | Gemini（淡蓝填充激活）、Claude（极简灰底）、Notion（灰填充） |
| Kokoro 差异点 | active 用 **accent-soft 暖填充**（A 米褐 / C 浅苔），不用冷蓝；图标用 1.5px 描边线性图标但**略软的端点（round cap）**；hover 时**仅背景轻微变暖**，不变色不放大 |

```
 ┌────────────────────────────┐
 │  🎨  模板库                  │   ← active：accent-soft 填充 + radius-sm
 └────────────────────────────┘
    icon 16px  text 13-14px
    高度 ~40px，左右 padding 12px
```

---

## 2. Input pill（主输入框）

| 维度 | 内容 |
|---|---|
| 用途 | 用户输入入口，所有对话起点 |
| 关键状态 | empty（占位） / focus / typing / disabled / submitting |
| 参考竞品 | Gemini 胶囊（高 ~60px）、ChatGPT 圆角矩形、Claude 简单 box |
| Kokoro 差异点 | **胶囊形（radius-lg 24px）+ 高 60px**；focus 时**只加 1px 暖边框**不加发光；placeholder 是**句子不是命令**："把想说的告诉我。" 而非 "Type here"；左附件按钮、右模型切换、右末发送按钮 |

```
 ┌──────────────────────────────────────────────────────────────┐
 │  ＋   把想说的告诉我。                       [小心 ▾]  [ ➤ ]  │
 └──────────────────────────────────────────────────────────────┘
   附件   placeholder/text                       model    send
   34px                                          chip     34px
```

- 内边距：左右 20px，上下 14px
- 不允许发送时（empty / submitting）：send button 用 `text-tertiary` 灰色，可见但点不动

---

## 3. Model switcher chip

| 维度 | 内容 |
|---|---|
| 用途 | 切换底层模型 / 模式（如"小心"细节模式 vs "速回"快速模式） |
| 关键状态 | default / hover / open（下拉打开） / disabled |
| 参考竞品 | Gemini "Flash ▾" pill、ChatGPT 模型选择下拉 |
| Kokoro 差异点 | chip **不用模型代号**（"GPT-4o" / "Claude 3.5"）而用 **气质化别名**（"细想" / "速回" / "细心"）；选项下拉**带一句话解释**："适合需要慢一点细想的事"；chip 本体小巧（高 28px，radius-sm） |

```
 [ 细想 ▾ ]   ← 默认  
 ┌─────────────────────────────┐
 │ ✓ 细想                       │
 │   适合慢慢想清楚的事           │
 │   速回                       │
 │   聊一句，快回                 │
 └─────────────────────────────┘
```

---

## 4. Send button

| 维度 | 内容 |
|---|---|
| 用途 | 提交输入 |
| 关键状态 | idle（无内容，灰）/ ready（有内容，accent）/ submitting（pulse 动画）/ disabled |
| 参考竞品 | Gemini 圆形深色填充、ChatGPT 黑色箭头按钮 |
| Kokoro 差异点 | **圆形 34px**（不是方形）；icon 用 **arrow-up 而非 paper-plane**（轻一点）；submitting 时不转圈，**用 pulse 节奏脉动**（见 [motion.md](./motion.md)）；ready 状态 accent 填充但**不发光不放大** |

---

## 5. Chat bubble

| 维度 | 内容 |
|---|---|
| 用途 | 显示消息（用户 / Kokoro） |
| 关键状态 | sending / sent / streaming（Kokoro 生成中）/ done / error |
| 参考竞品 | ChatGPT / Claude / WhatsApp / WeChat（用户右对齐 + 助手左对齐）；Gemini（用户居中，异类） |
| Kokoro 差异点 | **用户气泡右对齐 + 暖灰底（surface-hover）+ 不对称圆角（右下角小、其余大）**，走业界标准 IM 范式（零认知摩擦）；**Kokoro 回复无气泡，纯文本左对齐**，更像"在跟你说话"而非"系统回复"——这是真正的差异化；streaming 时**光标用呼吸节奏**而非闪烁；段落间距宽松（24px）。决策见 [ADR-008](../../decisions/ADR-008-chat-alignment.md) |

```
                            ┌──────────────────────┐
                            │  把这个写成一封信。     │  ← 用户气泡：右对齐
                            └──────────────────────┘

 好。先问你两件事，我才知道写给谁。            ← Kokoro：无气泡纯文本
 1. 收信人是？
 2. 想让对方读完有什么感觉？
```

---

## 6. Canvas card

| 维度 | 内容 |
|---|---|
| 用途 | Chat 区内表示"已生成 / 正在生成 Canvas 产物"的卡片 |
| 关键状态 | generating / done / error / archived |
| 参考竞品 | Gemini 文档卡片（淡灰边、左 emoji 标题）、ChatGPT artifact 卡 |
| Kokoro 差异点 | **大圆角 radius-md (16px)**；左侧不用 emoji 用 **小图标**（更克制）；generating 时**右上角有节奏脉动点**而非进度条；标题下一行有 **Kokoro 自己起的一句话副标**（"一封写给老朋友的信"），比文件名更有温度；done 后整张卡可点击展开 Canvas |

```
 ┌──────────────────────────────────────────┐
 │  📄  一封写给老朋友的信                       │
 │      Letter · 312 字 · 刚刚                  │
 │                                           │
 │      [ 打开 ]   [ 分享 ]                      │
 └──────────────────────────────────────────┘
   radius 16px， border 1px， shadow-sm
```

---

## 7. Template card

| 维度 | 内容 |
|---|---|
| 用途 | 模板库 / 首屏 chip 区的可点击模板入口 |
| 关键状态 | default / hover / pressed / used（已用过有标记） |
| 参考竞品 | Notion 模板（带 preview 图）、Manus chip（圆角 chip + 文字）、ChatGPT example prompt 卡 |
| Kokoro 差异点 | **不用预览缩略图**（避免堆砌信息），只用**一句话描述 + 小图标**；hover 时**整卡轻微暖化**（背景从 surface → accent-soft，不放大不抖动）；首屏只显示 5 个最高优先级 chip（见 [canvas-types.md](../03-product-form/canvas-types.md)） |

```
 ┌─────────────────┐  ┌─────────────────┐
 │ 📝              │  │ 🎨              │
 │ 写一封信         │  │ 做一张海报       │
 │ 想说但不知怎么说  │  │ 朋友圈用的那种    │
 └─────────────────┘  └─────────────────┘
   radius-md，padding 20px
```

---

## 8. Share button

| 维度 | 内容 |
|---|---|
| 用途 | 把 Canvas 产物分享出去（关键增长入口） |
| 关键状态 | default / hover / copying / copied / error |
| 参考竞品 | Notion 分享、Figma 分享、Manus 分享按钮 |
| Kokoro 差异点 | **不藏在「更多」菜单**，作为 chat 区"文档卡片"按钮行的一等公民（"打开 / 分享 / 再调一下"）；Canvas 顶栏**不再重复**挂分享按钮（顶栏只留收起 / 自动保存 / 关闭，详见 [06-screens/canvas.md](../06-screens/canvas.md#关键组件)）；点击展开的弹层包含：链接复制 / 下载图片 / 下载 PDF / 直接发到主流平台；**复制成功的反馈不弹 toast**，按钮文字短暂变成 "复好了 ✓" 再回弹 |

---

## 9. OG image

| 维度 | 内容 |
|---|---|
| 用途 | Canvas 产物分享到社交平台时自动生成的预览图（核心增长资产，见 [07-growth/sharing-first-class.md](../07-growth/sharing-first-class.md)） |
| 关键状态 | 模板版（无内容预览）/ 实例版（含产物缩略） |
| 参考竞品 | Notion OG（页面标题 + Notion logo）、GitHub OG（repo 信息卡）、Vercel OG |
| Kokoro 差异点 | **底色用 bg / bg-subtle**（暖米或苔米），**不用纯白**；左上角 Kokoro 签名 + 右下角 "by Kokoro · 你的产物"；中央**只放产物标题 + 一句副标**，不放预览缩略图（避免信息过密）；字体用品牌 serif/手写点缀 |

```
 ┌─────────────────────────────────────────┐
 │ Kokoro                                   │
 │                                          │
 │     一封写给老朋友的信                     │
 │     有些话，想了三年才写出来               │
 │                                          │
 │                          by Kokoro       │
 └─────────────────────────────────────────┘
   1200 × 630，暖米底，serif 标题
```

---

## 10. Empty state

| 维度 | 内容 |
|---|---|
| 用途 | 列表 / 页面 / Canvas 为空时的占位（最近列表空、模板库空、库为空等） |
| 关键状态 | first-time（从未用过） / cleared（用完都删了）/ filtered（筛选无结果） |
| 参考竞品 | Notion（小插画 + 引导）、Linear（一句话 + CTA）、Apple Notes（极简） |
| Kokoro 差异点 | **不用插画 / 占位图**，只用文字（参考 ADR-001）；first-time 时是**邀请式引导**："这里会装下你做过的东西。先聊一句？"；cleared 时是**陪伴式**："清空了，挺好。"；filtered 时是**承担式**："这里没找到。换个词试试？"；copy 严格走 [voice-and-tone.md](../02-personality/voice-and-tone.md) |

---

## 11. Loading pulse

| 维度 | 内容 |
|---|---|
| 用途 | 所有等待场景（streaming、文件上传、Canvas 生成、网络请求） |
| 关键状态 | start / running / settling（即将结束） |
| 参考竞品 | Gemini（"思考中..."文字 + 渐变）、Claude（点点点）、ChatGPT（光标闪烁） |
| Kokoro 差异点 | **完全不用 spinner / 旋转 / 进度条**；用**呼吸节奏的圆点**（直径 6-8px，1800ms 周期，opacity 0.3 → 1 → 0.3）；如需多个点表示阶段，则**依次接力呼吸**而非同步；可配文字提示走 voice-and-tone（"在想……" / "正在整理……"） |

```
 在想……   ●            ← 单点呼吸（streaming）
 在想……   ● ● ●         ← 三点接力（多阶段）
```

---

## 12. Error toast

| 维度 | 内容 |
|---|---|
| 用途 | 全局非阻塞错误提示（网络断、保存失败、限流等） |
| 关键状态 | enter（入场） / visible / dismissing（出场） / persistent（需用户主动关） |
| 参考竞品 | Linear toast（顶部，简洁）、Notion toast（底部，带 undo）、Apple notification |
| Kokoro 差异点 | **底部居中浮起**，不弹顶；**配色用 danger 暖陶土**而非正红；**默认含 undo / 重试入口**而非只显示"失败"；copy 严格走"承担 + 路径"模式（"没保存上。要不要再试一次？"）；自动消失时长 4s，hover 暂停 |

```
 ┌─────────────────────────────────────────┐
 │ ⚠  没保存上。要不要再试一次？  [ 重试 ]  ✕ │
 └─────────────────────────────────────────┘
   暖陶土底，radius-md，shadow-md
```

---

## 待你拍板

- [ ] Model switcher chip 用气质化别名（"细想 / 速回"）还是技术化（"Pro / Standard"）？前者更心路线，后者更工程师友好
- [x] Chat bubble 对齐方式 → 已定：用户右 / 助手无气泡左。见 [ADR-008](../../decisions/ADR-008-chat-alignment.md)
- [ ] Template card 要不要预览缩略图？现在写的是"不要"，但模板库密度可能不够
- [ ] OG image 是否在 MVP 就做？做的话需要 server-side rendering 基建
- [ ] Loading pulse 用单点还是多点？多点接力更好看但实现复杂

## 关联

- [tokens.md](./tokens.md) — 组件用的色 / 圆角 / 字号
- [motion.md](./motion.md) — 状态切换的动效
- [patterns.md](./patterns.md) — 组件组合成的交互模式
- [voice-and-tone.md](../02-personality/voice-and-tone.md) — 组件内 copy 的语气
- [ia.md](../04-architecture/ia.md) — 组件出现位置
