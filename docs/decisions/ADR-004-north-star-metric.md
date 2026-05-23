# ADR-004 · 北极星指标：WAS（周活跃产物分享数）

- **日期**：2026-05-21
- **状态**：accepted
- **决策者**：Claude（用户全权授权代决）
- **关联**：[ADR-001](./ADR-001-product-personality.md)、[07-growth/metrics.md](../product/07-growth/metrics.md)、[01-strategy/growth-engine.md](../product/01-strategy/growth-engine.md)

---

## 决策

**北极星 = WAS（Weekly Active Shared products）**
**定义 = 当周被分享出去的产物总数**

反作弊规则（强制）：

- 同 IP / 同设备 / 短时间内重复分享同一产物 → 算 1 次
- 链接被自动爬取（非真人点击）→ 不算入下游指标
- 详细规则见 [07-growth/sharing-first-class.md](../product/07-growth/sharing-first-class.md) 与 [09-safety/circuit-breakers.md](../product/09-safety/circuit-breakers.md)

---

## 理由

1. **核心命题直接对位**：Kokoro 的命题是"产物即广告"，北极星必须直接刻画
2. **三压一**：WAS 同时压住——
   - 产物质量（不好用没人完成）
   - 产品价值（对用户有意义才会做）
   - 传播力（分享触发率）
3. **候选对比**：
   | 候选 | 否决理由 |
   |---|---|
   | B. WNT（周新增可复用模板数） | 滞后（要等"被复用 3 次"才计入）+ 早期数太小 |
   | C. WAP（周活产物完成数） | 不差异化，任何 AI 产品都看 |
   | D. MAC（月活创作者数） | 太通用，不体现 Kokoro 独有命题 |

---

## 季度目标（仅参考，等真数据校准）

| 季度 | WAS 目标 |
|---|---|
| Q1 上线 | 500 / 周 |
| Q2 | 5,000 / 周 |
| Q3 | 30,000 / 周 |
| Q4 | 100,000 / 周 |

数字粗糙，看真实曲线再校准。

---

## Tradeoff

- **不直接等于收入**：早期阶段可接受；增长引擎转通后再考虑商业指标
- **易被自分享刷**：靠反作弊规则兜底；同时把"印记保留率"列入健康指标（如果都被改私有 / 被去印记，WAS 数字膨胀但产品价值打折）

---

## 输入 / 健康 / 警戒指标

完整看板见 [07-growth/metrics.md](../product/07-growth/metrics.md)。关键依赖项：

- **输入**：DAU、新用户首产物完成率、分享触发率、分享落地→新用户率、模板复用率
- **健康**：留存 D1 / D7、印记保留率（> 80%）、产物完成率
- **警戒**：分享被举报率、模板被删比例、自分享比例

---

## 后果

- 所有重大产品决策需要至少一个"WAS 贡献分析"
- 必须实现 [07-growth/metrics.md](../product/07-growth/metrics.md) 列的 11 个埋点事件
- "印记可弱化但不可去除"决策需保持（详见 [ADR-005](./ADR-005-business-model.md) Pro 边界）
