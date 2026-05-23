---
status: 🟡 草稿
updated: 2026-05-20
---

# Kokoro · 一页纸

## 一句话

**Kokoro 是一个有人格的通用 AI agent，主战场是把"想法"变成可分享的视觉产物。**

## 三段话

- **它是什么**：Kokoro 是一个 chat + Canvas + agent 的 web 产品，定位"通用助理"。但它不假装中性——它叫"心"，气质柔、温、内观，每一份产出物都带这种气质的印记
- **它解决什么**：你脑里有一个想法（一份策划、一张海报、一份课件、一篇分析、一个原型），想快速把它做出来并发给人看。Kokoro 帮你想清楚、做出来、并让产出物"自带 Kokoro 印记"地传播
- **它怎么赢**：**Canvas 产物自带气质 → 分享出去一眼可识别 → 看到的人来用**。这是 Kokoro 的核心增长玩法（详见 [07-growth](../07-growth/)）

## 四个支柱

1. **通用 agent**（包容多种任务，参考 CoWork / Manus / Claude Code）
2. **Canvas 视觉产物**（主战场是视觉化 Manus / v0 风格的产出）
3. **「心」人格**（[ADR-001](../../decisions/ADR-001-product-personality.md) · 柔、温、内观）
4. **分享是一等公民**（产品出生就带 share link / 模板 / 嵌入）

## 五个反面（明确不是什么）

- **不是 Cursor**——不为编程而生
- **不是 ChatGPT 通用 chat 类目克隆**——通用是底盘不是叙事
- **不是 Lovable / v0**——目标人群更广，不限 dev
- **不是 NotebookLM**——不为知识提取/总结而生（虽然可以做）
- **不是夸张个性 AI**（如 Pi、Replika）——温柔克制，不卖萌

## 主要 tradeoff（写在最上面，避免后续反复扯）

- **目标市场可能集中在中文 / 东亚**，欧美吃不开（[ADR-001 tradeoff 节](../../decisions/ADR-001-product-personality.md)）
- **通用 agent 反增长**，对外叙事必须靠"3-5 个钩子 use case"克服（[01-strategy/differentiation.md](../01-strategy/differentiation.md)）
- **气质一致性**要求高，所有文案 / 视觉 / 动效都要服务"心"路线，没有半路改调子的余地

## 下一个 milestone

把 5 个关键问题答完（见 [README.md](../README.md) 末尾），然后进入设计 token 与第一版原型。
