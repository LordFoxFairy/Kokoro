# Kokoro 需求手册

> 维护方式:四层(产品 / 能力 / 流程 / 契约),每层一个子目录、多个聚焦小 md,逐节可独立复查修订。
> 本文件 = 总索引。新增文档照 [§ 新增规范](#新增规范) 走。
> 起草:2026-06-14 · 状态:🟡 草稿(围绕真实三仓 stream 系统重写)

---

## 这份手册是什么

**工程可验证的真实 PRD**:系统**必须做什么** + **如何验收**。

它和 `docs/product/` 的分工:
- `docs/product/` 谈**产品愿景与设计语言**(原型时代,部分已过时,保留作设计参考)。
- `docs/requirements/`(本手册)谈**真实在跑的三仓 stream 系统的需求与验收**,围绕实际造出来的产品,链回 product/ 但不继承其过时内容。

> ⚠️ **事实基线**:本手册描述的产品 = **三仓 stream 聊天系统**(kokoro-web 聊天壳 + agent 活动流 + session SSE/replay)。`docs/product/` 里的「canvas 生成器矩阵」是**原型设计,尚未在真实仓落地**——见 [00-product/scope-and-boundary.md](./00-product/scope-and-boundary.md) 的三态分界。

## 导览

| 层 | 目录 | 内容 | 读者 |
|---|---|---|---|
| **00 产品层** | [00-product/](./00-product/) | 为什么做 / 给谁 / 做成什么样 / 信任档位 | 产品 + 工程共读 |
| **01 能力层** | [01-capabilities/](./01-capabilities/) | 系统必须能做什么(会话 / 活动流 / 流式 / 恢复 / 工具 / 扩展位) | 工程 |
| **02 流程层** | [02-flows/](./02-flows/) | 端到端业务流程 + Given/When/Then 验收 | 工程 + QA |
| **03 契约层** | [03-contracts/](./03-contracts/) | 需求 → protocol / spec / 测试的映射索引(薄桥) | 工程 |

## 阅读顺序建议

- **第一次过手册**:`00-product/vision` → `scope-and-boundary` → `01-capabilities/conversation` → `02-flows/send-and-stream` → 其余按需。
- **接手某个能力**:直接进 `01-capabilities/<域>.md`,顺 `refs` 跳到流程层验收 + 契约层实现。
- **加新需求**:见下方新增规范。

---

## 状态约定

每个 doc frontmatter 的 `status`:
- 🟢 **已定**(locked)— ADR 锁定或用户拍板,改动需新 ADR
- 🟡 **草稿**(draft)— 已起草,等审阅修订
- 🔴 **待用户拍板**(pending-user)— 只有问题清单,需用户输入

## 新增规范

「以后新增的文档都在这里如何加」:

1. **判断归层**:产品前提 → `00-product/`;静态能力域 → `01-capabilities/`;端到端流程 → `02-flows/`;契约映射 → `03-contracts/`。
2. **复制模板**:从 [`_TEMPLATE.md`](./_TEMPLATE.md) 起,填 frontmatter(`status / layer / owner / updated / refs`)。
3. **注册索引**:在对应层 README(或本总索引)的表里加一行。
4. **流程层强约束**:`02-flows/` 的每篇**必须**在 `refs` 写 ≥1 个 `test:<slug>`(指向[测试总目录](../superpowers/specs/2026-06-13-test-case-catalog.md));暂无对应测试 → 状态标 🔴 并入 item 3 缺口清单。
5. **不重写契约**:涉及契约/实现细节,链到 `docs/protocol/` 或 `docs/superpowers/specs/`,**不复制内容**(杜绝双向维护漂移)。

---

## 关联文档

- 决策记录 [`docs/decisions/`](../decisions/)(ADR ×9)— 需求层引用为权威
- 跨仓协议 [`docs/protocol/`](../protocol/)— 契约层指向
- 工程设计 spec [`docs/superpowers/specs/`](../superpowers/specs/)— 实现真相
  - [stream 架构规格](../superpowers/specs/2026-06-11-stream-event-architecture-spec.md)— 目标态北极星
  - [测试总目录](../superpowers/specs/2026-06-13-test-case-catalog.md)— 62 流程验收锚点
  - [能力扩展架构](../superpowers/specs/2026-06-12-capability-extension-design.md)— workspace/teams/HITL 留缝
- 产品愿景/设计 [`docs/product/`](../product/)— 参考,不继承
