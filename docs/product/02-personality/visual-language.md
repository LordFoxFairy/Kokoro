---
status: 🟡 草稿
updated: 2026-05-20
---

# 视觉语言总纲

> 本文件 = 视觉的"宪法"。具体 token / 组件 / 动效见 [05-design-system/](../05-design-system/)。

---

## 总原则

视觉应让人感到：

1. **干净但不冷**——留白足够，但留白里有温度
2. **柔和但不软**——圆角、缓动、暖色，但不松散
3. **有印记但不张扬**——产物一眼可识别是 Kokoro，但不靠 logo 砸脸

---

## 色板方向

> 具体 token 见 [05-design-system/tokens.md](../05-design-system/tokens.md)。本文件描述方向。

### 主色调候选（待选 1）

| 方向 | 关键词 | 风险 |
|---|---|---|
| **A. 米 + 木** | 暖中性、低饱和、亲近 | 略显寡淡 |
| **B. 浅粉 + 莫兰迪** | 柔、女性偏好高 | 性别标签风险 |
| **C. 苔绿 + 米** | 自然、平静、独特 | 不主流 |
| **D. 浅琥珀 + 米白** | 温暖、有活力 | 跟 Anthropic 橘陶撞 |

**Claude 倾向 A 或 C**——最契合"心 = 内观"且无性别标签。

### 必须 not

- ❌ Gemini 冷蓝（已被占）
- ❌ 纯白纯黑高对比（违反"柔"）
- ❌ 任何荧光 / neon 色
- ❌ 渐变靓丽（v0 / Lovable 那种，违反"克制"）

---

## 字体方向

- **正文**：现代 sans-serif（候选 Inter / Geist / PingFang / Noto Sans CJK）
  - 西文与中文都需要好看
  - 不要 Helvetica / Arial 这种通用感太强的
- **标题 / 品牌**：略带暖意的 sans 或一抹 serif 点缀
  - 候选：Söhne / Bricolage Grotesque / Source Han Serif（中）
- **手写点缀**（克制使用）：用于品牌名 / 引导语 / 空状态友好提示
  - 候选：Kalam / Caveat / 中文手写字体

---

## 形状语言

- **圆角档位**：
  - 大（24px）—— 主输入框、主卡片、主按钮 pill
  - 中（12-16px）—— 内嵌卡片、模板缩略图
  - 小（6-8px）—— chip、tag、标签
  - 0px —— 极少用（仅文字 underline 或分割）
- **比例**：偏圆润，避免锐利直角

---

## 留白与节奏

- 默认间距以 **8px 网格** 为基准
- 主区域内边距宽松（≥40px）
- 卡片之间留白可见
- 避免信息密集，**愿意为留白牺牲信息密度**

---

## 阴影与质感

- 阴影**极淡**（参考 Gemini）：`0 1px 6px rgba(0,0,0,0.04)` 量级
- 不用 hard shadow / drop shadow / 强 depth
- 不用 glassmorphism / blur 背景
- 不用 gradient 主背景（除了**极淡的环境色变化**）

---

## 动效语言

- **缓动**：所有交互动画用 `ease-out` / 自然 cubic-bezier
- **时长**：常规过渡 200-300ms，关键状态 400-500ms
- 不弹 / 不 spring / 不 overshoot
- Loading 用**节奏脉动 / 渐变**而非 spinner（pulse / breath 节奏）

---

## 产物印记（核心增长资产）

每个 Canvas 产物默认要带：

1. **底色 / 字体**——心路线的视觉骨架
2. **角标 / 署名**——克制小，但可识别
3. **分享尾巴**——分享链接落地页带 Kokoro 气质
4. **OG 图模板**——产物分享到社交媒体时的预览图自带印记

详见 [07-growth/sharing-first-class.md](../07-growth/sharing-first-class.md)。

---

## 待你拍板

- [ ] 主色调（A / B / C / D 中选一，或你心里有别的）
- [ ] 是否需要个 logo / 视觉吉祥物？（参考 Anthropic 的星状物、Mistral 的灯笼）
- [ ] 中文优先还是中英平等优先？
- [ ] 暗色主题：MVP 要不要？

## 关联

- [core.md](./core.md)
- [05-design-system/tokens.md](../05-design-system/tokens.md)
- [05-design-system/components.md](../05-design-system/components.md)
- [05-design-system/motion.md](../05-design-system/motion.md)
