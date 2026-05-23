# ADR-002 · 目标用户：T0 = 内容创作者 + 新手创业者

- **日期**：2026-05-21
- **状态**：accepted
- **决策者**：Claude（用户全权授权代决）
- **关联**：[ADR-001](./ADR-001-product-personality.md)、[01-strategy/target-users.md](../product/01-strategy/target-users.md)、[03-product-form/canvas-types.md](../product/03-product-form/canvas-types.md)

---

## 决策

| 层级 | 用户群 |
|---|---|
| **T0**（首发，对外叙事服务） | 内容创作者（小红书 / B 站 / 公众号 / 短视频） + 新手创业者 / Solopreneur |
| **T1**（扩散后接入） | 学生 / 设计学生 |
| **T2**（长期） | 营销 / 产品经理 / 教育者 |

---

## 理由

1. **气质契合**：两类用户都吃温柔治愈调性，与 ADR-001「心」路线高度契合
2. **产物诉求强**：海报 / 落地页 / 提案 / 笔记 / 课件——主战场是视觉产物
3. **分享是工作的一部分**：他们的成果默认要发出去，与增长引擎"产物即广告"循环天然咬合
4. **早期口碑能力强**：自带传播渠道（小红书 / B 站 / 朋友圈 / 创业者社群）
5. **圈层够广但不失焦**：两个圈互补但不打架；比"知识工作者"具体，比"创业者"开阔

---

## 否决项

| 候选 | 否决理由 |
|---|---|
| 开发者 | 与 Cursor / Lovable / Replit 红海冲突，且开发者不是 Kokoro 气质 fit |
| 企业用户 | 早期没渠道，回报周期长，企业版叙事破坏个人产品节奏 |
| "知识工作者" 模糊画像 | 太宽，等同没定位；CoWork 已占该位 |
| 学生（设为 T1 而非 T0） | 付费力弱，作为扩散圈而非首发圈 |

---

## Tradeoff（必须告知）

- **付费意愿一般** → 必须用 freemium 撑住（见 [ADR-005](./ADR-005-business-model.md)）
- **对"AI 生成的真实性"敏感**（特别是内容创作者）→ 后续产品需提供"由 Kokoro 协助"的署名透明机制
- **欧美市场弱**（继承 ADR-001 tradeoff）→ 一线市场集中中文 / 东亚

---

## 后果

- [03-product-form/canvas-types.md](../product/03-product-form/canvas-types.md) 的 5 个产出物 chip 必须服务这两类用户
- [02-personality/voice-and-tone.md](../product/02-personality/voice-and-tone.md) 已服务这两类（克制 + 有温度）—— 不动
- **首发增长渠道**：小红书、B 站学习区、设计师圈、独立产品 / 创业圈、Solopreneur 社群
- 商业模式必须 freemium 撑住 → 关联 ADR-005
