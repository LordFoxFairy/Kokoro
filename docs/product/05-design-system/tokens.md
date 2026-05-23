---
status: 🟢 已定（主色板锁定 A；TBD 项待 design review）
locked-by: ADR-006
updated: 2026-05-21
---

# Design Tokens

> 🟢 **主色板锁定 A · 米+木**（[ADR-006](../../decisions/ADR-006-color-palette.md)）
> 锁定的 hex 值见 ADR 与原型 `docs/prototypes/variant-a-mi-mu/styles.css`。
> C 套保留为历史候选（见下文），不再当主项。
> 部分 TBD 色值（`--color-text-secondary` / `--color-border` 等）待 design review。

## 摘要

- 主色调给出**两套并列候选**：A（米+木）和 C（苔绿+米）。你先拍其一，剩下细调由 design review 决定。
- 字号 / 圆角 / 间距 / 阴影统一一套，独立于色板。
- 8px 网格为基准，圆角四档（24 / 16 / 8 / 0），字号七档。
- 暗色主题 token 暂留空，MVP 是否做见 [visual-language.md](../02-personality/visual-language.md) 待拍板节。

---

## 色板：候选 A — 米 + 木

> 关键词：暖中性、低饱和、亲近。Notion / Things 风。
> 风险：略寡淡，accent 用得不准会"没存在感"。

| Token | Hex | 用途 |
|---|---|---|
| `--color-bg` | `#FAF7F2` | 主背景（暖米，比纯白柔，比 Gemini 冷蓝暖） |
| `--color-bg-subtle` | `#F3EEE5` | 次级背景（sidebar / Canvas 区底） |
| `--color-surface` | `#FFFFFF` | 卡片 / 输入框 / 气泡白底（不用纯白当背景，但卡片可以） |
| `--color-surface-hover` | `#F7F2EA` | hover 时的卡片底 |
| `--color-text-primary` | `#2B2520` | 主文本（暖灰深棕，不用纯黑） |
| `--color-text-secondary` | `#7A6F62` | 次文本 / 占位 / 时间戳 |
| `--color-text-tertiary` | `#B8AC9C` | 极弱信息 / disabled |
| `--color-accent` | `#8B6F47` | 木色 accent，用于激活态填充 / 主按钮 |
| `--color-accent-soft` | `#EBE0CF` | accent 的淡填充（激活态背景） |
| `--color-border` | `#E8E0D2` | 极淡边框 / 分割线 |
| `--color-border-strong` | `#D4C9B5` | 需要更明显边界时（input focus） |
| `--color-shadow` | `rgba(60, 45, 30, 0.05)` | 暖调阴影，不用黑 |

### 示意（ASCII）

```
背景  #FAF7F2 ──── sidebar #F3EEE5 ──── canvas #F3EEE5
         │
       卡片 #FFFFFF（白底卡浮在米底上 → 自然分层）
         │
       accent #8B6F47（木色主按钮 / 激活）
```

---

## 色板：候选 C — 苔绿 + 米

> 关键词：自然、平静、独特。比 A 更有辨识度。
> 风险：不主流，初见可能"小众感"重；苔绿用过头会"养生馆"。

| Token | Hex | 用途 |
|---|---|---|
| `--color-bg` | `#F7F4ED` | 主背景（米底，略偏冷一点点） |
| `--color-bg-subtle` | `#EEEAE0` | 次级背景 |
| `--color-surface` | `#FFFFFF` | 卡片白底 |
| `--color-surface-hover` | `#F2EFE6` | hover 卡片底 |
| `--color-text-primary` | `#2A2E26` | 主文本（带绿调的深灰） |
| `--color-text-secondary` | `#6E7367` | 次文本 |
| `--color-text-tertiary` | `#A8AC9F` | 极弱信息 |
| `--color-accent` | `#6B7F5C` | 苔绿 accent，主按钮 / 激活 |
| `--color-accent-soft` | `#DDE4D2` | accent 淡填充 |
| `--color-border` | `#E2DFD4` | 极淡边框 |
| `--color-border-strong` | `#CDC9BC` | 强边框（focus） |
| `--color-shadow` | `rgba(45, 50, 35, 0.05)` | 微绿调阴影 |

### 示意（ASCII）

```
背景  #F7F4ED ──── sidebar #EEEAE0 ──── canvas #EEEAE0
         │
       卡片 #FFFFFF
         │
       accent #6B7F5C（苔绿主按钮 / 激活）
```

---

## 语义色（两套候选共享）

| Token | A 候选 hex | C 候选 hex | 用途 |
|---|---|---|---|
| `--color-success` | `#7A8B6B` | `#7A8B6B` | "做好了"提示，与 accent 区分 |
| `--color-warning` | `#C8A26B` | `#B8A86B` | 限制 / 注意 |
| `--color-danger` | `#B36B5A` | `#A8705F` | 删除 / 错误，**暖陶土，不用正红** |
| `--color-info` | `--color-text-secondary` 同色 | 同左 | 中性提示，不强调 |

---

## 字号 / 行高

> 字体族见 [visual-language.md](../02-personality/visual-language.md)。这里只定字号档位。

| Token | 字号 | 行高 | 用途 |
|---|---|---|---|
| `--text-display` | 40px | 1.2 | 首屏大字问候（"今天想做什么？"） |
| `--text-h1` | 28px | 1.3 | Canvas 文档 H1 |
| `--text-h2` | 22px | 1.35 | Canvas 文档 H2 |
| `--text-h3` | 18px | 1.4 | Canvas H3 / 卡片标题 |
| `--text-body` | 15px | 1.6 | 对话正文 / 主体文本 |
| `--text-small` | 13px | 1.5 | 次信息 / sidebar item |
| `--text-micro` | 11px | 1.4 | 时间戳 / 标签 / 角标署名 |

字重统一只用三档：`400`（常规）/ `500`（中等）/ `600`（半粗）。不用 700+，避免"硬"。

---

## 圆角

| Token | 值 | 用途 |
|---|---|---|
| `--radius-lg` | 24px | 主输入框胶囊、主按钮 pill、首屏主卡片 |
| `--radius-md` | 16px | Canvas 文档卡片、模板缩略图 |
| `--radius-sm` | 8px | chip、tag、model switcher |
| `--radius-xs` | 4px | input 内嵌元素、tooltip |
| `--radius-0` | 0px | 极少用，仅文字下划线 / 分割线 |

---

## 间距（8px 网格）

| Token | 值 | 典型用途 |
|---|---|---|
| `--space-1` | 4px | icon-text 内贴 |
| `--space-2` | 8px | chip 内 padding |
| `--space-3` | 12px | sidebar item 行高内 padding |
| `--space-4` | 16px | 卡片内 padding、组件间小距 |
| `--space-5` | 24px | 卡片间距、段落间距 |
| `--space-6` | 32px | 区段间距 |
| `--space-7` | 40px | 主区域内边距下限 |
| `--space-8` | 64px | 首屏垂直留白 |

规则：除 `--space-1`，全部是 8 的倍数。

---

## 阴影

| Token | 值 | 用途 |
|---|---|---|
| `--shadow-none` | `none` | 默认无 |
| `--shadow-xs` | `0 1px 2px var(--color-shadow)` | 输入框 focus、chip hover |
| `--shadow-sm` | `0 1px 6px var(--color-shadow)` | 卡片默认浮起（参考 Gemini） |
| `--shadow-md` | `0 4px 16px var(--color-shadow)` | 弹层 / 浮窗 |
| `--shadow-lg` | `0 8px 32px var(--color-shadow)` | 模态 / 重要 dialog |

**不准用**：hard shadow（offset > 2 又无 blur）、多层堆叠阴影、`drop-shadow()` filter、glassmorphism（backdrop-blur）。

---

## 动效 token

| Token | 值 | 用途 |
|---|---|---|
| `--easing-default` | `cubic-bezier(0.25, 0.1, 0.25, 1)` | 自然 ease-out |
| `--easing-enter` | `cubic-bezier(0.16, 1, 0.3, 1)` | 入场更柔 |
| `--easing-exit` | `cubic-bezier(0.7, 0, 0.84, 0)` | 退场略快 |
| `--duration-fast` | 150ms | hover / 微交互 |
| `--duration-base` | 250ms | 常规过渡 |
| `--duration-slow` | 450ms | 关键状态切换、loading 进入 |
| `--duration-breath` | 1800ms | loading 节奏脉动一次的周期 |

明令：**禁止 spring / overshoot / bounce 缓动**，详见 [motion.md](./motion.md)。

---

## 暗色主题（MVP 范围待定）

```
--color-bg-dark:        ?  暂不定
--color-surface-dark:   ?  暂不定
```

暗色不是简单反色。等 visual-language.md "暗色主题 MVP 要不要" 拍板后再定。倾向用**暖深棕**或**深苔**做底，不用纯黑。

---

## 待你拍板

- [ ] 主色调选 **A 米+木** 还是 **C 苔绿+米**？（B 浅粉、D 浅琥珀已在 visual-language.md 被弱化）
- [ ] accent 饱和度：现在两套都偏低，看起来"够温柔"但可能"不够有印记"。要不要把 accent 再饱和 10-15%？
- [ ] 字号 display 40px 够不够大？Gemini 印象在 36-44px，Kokoro 想再克制点用 36px 还是更张扬用 44px？
- [ ] 圆角 24px 用在主按钮 + 输入框是否一致？还是按钮稍小（20px）？
- [ ] 暗色主题 MVP 做不做？做的话以"暖深棕"还是"深苔"为底？

## 关联

- [visual-language.md](../02-personality/visual-language.md) — 视觉总纲
- [components.md](./components.md) — 组件用到这些 token
- [motion.md](./motion.md) — 动效 token 的具体应用
- [research/gemini/anatomy.md](../../research/gemini/anatomy.md) — token 档位参考
