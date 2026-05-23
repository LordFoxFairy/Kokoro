# ADR-006 · 主色板：A（米 + 木）

- **日期**：2026-05-21
- **状态**：accepted
- **决策者**：用户拍板（看完 A / C 双路 HTML 原型后）
- **关联**：[ADR-001](./ADR-001-product-personality.md)、[05-design-system/tokens.md](../product/05-design-system/tokens.md)、[02-personality/visual-language.md](../product/02-personality/visual-language.md)

---

## 决策

主色板选 **A · 米 + 木**。

### 锁定 tokens（基础层，色值来自 variant A 原型）

| Token | 值 | 用途 |
|---|---|---|
| `--color-bg` | `#FAF7F2` | 主背景（米） |
| `--color-surface` | `#FFFFFF` | 卡片 / 浮层 surface |
| `--color-bg-subtle` | TBD（基于 `#EBE0CF` 减饱和） | 强调淡填充（如选中态） |
| `--color-accent` | `#8B6F47` | 木色 accent（按钮 / 边框点缀） |
| `--color-accent-soft` | `#EBE0CF` | 软木色（hover / 微强调） |
| `--color-text-primary` | `#2B2520` | 暖深棕（非纯黑） |
| `--color-text-secondary` | TBD（基于主色降阶） | 辅助文字 / 占位符 |
| `--color-border` | TBD（基于 `#EBE0CF` 降饱和） | 极淡边线 |

### "纸感"系统（继承原型）

A 套不只是色值，是一整套"纸"的视觉语言：

- 顶沿暖一档边色（页面顶部一条不易察觉的色变化）
- 不对称圆角 `6/6/4/4`（卡片左上右上 6px、左下右下 4px——像翻页）
- 左 margin 暖 hairline（细一条暖灰线，像纸的装订）
- SVG turbulence noise overlay（极淡 noise 让米色不是色块而是"纸"）

这些细节是 A 套的灵魂，**不可在打磨时被简化掉**。

---

## 理由

1. **用户直接体感**："variant-a-mi-mu 舒服一点"（看完 A / C 双路实景后）
2. **气质契合**：米 + 木的"纸 / 木"双重意象，比苔绿+米更直接对位心人格的"内观 / 温度"
3. **辨识度足**：暖深棕文字（非纯黑）+ 木色 accent 在中文 AI 产品里几乎无重复
4. **风险可控**：C 套的自然意象更小众，可能在 T0 用户（创作者 / 创业者）里偏弱

---

## 否决项

| 候选 | 否决理由 |
|---|---|
| **C 苔绿 + 米** | 美但不如 A 直接；自然意象偏小众，对 T0 受众抓力弱 |
| **B 浅粉 + 莫兰迪** | （此前已在 visual-language.md 否决）性别标签风险 |
| **D 浅琥珀 + 米白** | （此前已否决）跟 Anthropic 橘陶撞 |

C 套原型 `docs/prototypes/variant-c-koke-mi/` 保留为历史参考，不删除。

---

## Tradeoff（必须告知）

- **暖调可能让"专业感"打折**：参考 Notion / Things 的范式，靠组件克制和字体层级承载专业感，色板不背锅
- **暗色主题挑战**：A 套深色版本需要重新设计（暖深褐 + 木色调亮），不能简单"反色"
- **打印 / 截图分享场景**：纸感细节（noise / hairline）在低分辨率截图里会丢失，需要 fallback

---

## 后续待办

- [ ] 把 tokens.md 中 C 套 section 移到"历史候选"附录区（保留信息，不再当主项）
- [ ] design review：补全 TBD 的 `--color-bg-subtle` `--color-text-secondary` `--color-border` 精确值
- [ ] 暗色主题方案（v1.x 评估，MVP 先 light only）
- [ ] 把"纸感系统"写成独立 `05-design-system/paper-system.md` 文件，作为视觉灵魂资产

---

## 后果

- 所有后续视觉决策以 A 套为前提
- 第二轮打磨在 `docs/prototypes/variant-a-mi-mu/` 上 in-place 推进
- 不再为 C 套投入精力
- 上面"纸感系统"成为视觉 spec 的一等公民
