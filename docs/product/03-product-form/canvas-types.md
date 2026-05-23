---
status: 🟢 已定（chip 已锁；具体视觉缩略图待 prototype 落定后微调）
locked-by: ADR-002（继承目标用户结论）
updated: 2026-05-21
---

# 主打 Canvas 类型（产出物 chip）

> 🟢 **首发 chip 已锁定**：小红书风海报 / 一页落地页 / 学习课件 / **写一封信** / 想法可视化 / 更多（5 个产物 + 1 个兜底）。
> 服务 [ADR-002](../../decisions/ADR-002-target-users.md) 的 T0 用户（内容创作者 + 新手创业者）。

## 选 chip 的 4 个标准

1. **目标用户能记住**（具体 use case，不要"做内容"）
2. **视觉产出强**（不是纯文本，要能晒）
3. **分享/传播圈层广**（产物丢出去有人看）
4. **AI 现阶段能做好**（不超能力范围）

## 候选 chip 池

### 创作者 / 营销向（高 fit）

- 小红书风海报 / 笔记
- 公众号封面图
- 抖音 / B 站视频封面
- 朋友圈 / 微博图文
- 产品介绍落地页
- 营销文案 + 配图组合

### 学生 / 知识工作者向（高 fit）

- 课件 / 演示稿
- 学习笔记拼图
- 闪卡 / 复习卡
- 读书报告 / 总结
- 知识地图 / 思维结构图

### 创业者 / Solopreneur 向（高 fit）

- 落地页（一页式产品介绍）
- 投资人 pitch deck
- 产品策划案 / PRD
- 一句话产品名 / slogan 生成
- 简单原型 / wireframe

### 通用办公向（中 fit）

- 策划案 / 方案
- 周报 / 月报
- 会议纪要 → 视觉化
- 数据表 → 看板（弱）

---

## 首发组合（已锁定 🟢）

**首发 5 个产物 chip + 1 个兜底**：

| # | chip | 服务用户 | 钩子价值 | 原型示例 |
|---|---|---|---|---|
| 1 | 🎨 **小红书风海报** | 内容创作者 T0 | 视觉强、分享率最高、最适合带印记 | [`canvas-poster.html`](../../prototypes/variant-a-mi-mu/canvas-poster.html) |
| 2 | 📊 **一页落地页** | 新手创业者 T0 | 创业者真痛点；产物本身就能拉新 | [`canvas-landing.html`](../../prototypes/variant-a-mi-mu/canvas-landing.html) |
| 3 | 📝 **学习课件** | 学生 T1 + 教师 / 培训师 | 拼图分享性强，B 站学习区显学 | [`canvas-courseware.html`](../../prototypes/variant-a-mi-mu/canvas-courseware.html) |
| 4 | 💌 **写一封信** | 通用 / 情感表达 | 最贴「心」人格的产物——像一封信，不像一条消息；情感场景分享天然有温度 | [`canvas.html`](../../prototypes/variant-a-mi-mu/canvas.html)（信件 canvas，入口走 [`chat.html`](../../prototypes/variant-a-mi-mu/chat.html)） |
| 5 | 💡 **想法可视化**（思维结构图） | 通用 | 跟"心 = 内观"暗合；是 Kokoro 独有钩子 | [`canvas-mindmap.html`](../../prototypes/variant-a-mi-mu/canvas-mindmap.html) |
| 6 | ✨ **更多……** | 兜底 | 避免局限感；点开展示全部产物类型 | （兜底入口，无独立 canvas） |

**为什么是这 5 个产物**（见 [ADR-002](../../decisions/ADR-002-target-users.md)）：
- 1, 2 直击 T0 内容创作者 + 新手创业者
- 3 给 T1 学生 + 教师扩散圈
- 4 **写一封信**是「心」人格的代言产物：别的产品把它做成"一条消息"，Kokoro 做成"一封信"——克制、有温度，是人格落到产物上的锚点
- 5 通用钩子，独有定位（其他产品没人这么命名）
- 6 兜底，避免认知超载也避免局限感

**MVP 后再迭代的 chip 候选**（不进首发）：
- 公众号封面、朋友圈图文、视频封面、闪卡、读书报告、pitch deck、PRD、营销文案+配图组合

## Manus 启示（参考）

Manus 首页用 "Create slides / Build website / Develop desktop apps / Design" 这种**产出物 chip 化**——把通用能力包装成具体记忆点。我们直接借这个 pattern，但 chip 内容服务 Kokoro 自己的 T0 用户。

## 反例

- ❌ "做内容" / "做设计" / "做产品" 这种太抽象
- ❌ "Python 代码 / React 组件" 这种 dev 向（违反目标用户）
- ❌ 一次给超过 7 个（认知超载）
- ❌ chip 自身视觉差异化弱（应每个有缩略图）

## 待你拍板

- [ ] 你最想的 chip 是哪 3 个？（最直觉的，不要纠结）
- [ ] 是否同意"5 个 + 兜底"的数量？
- [ ] 有没有特别想做但担心做不好的产物类型？

## 关联

- [01-strategy/target-users.md](../01-strategy/target-users.md)
- [02-personality/visual-language.md](../02-personality/visual-language.md)
- [Manus notes](../../research/manus/notes.md)
- [06-screens/home.md](../06-screens/home.md)
