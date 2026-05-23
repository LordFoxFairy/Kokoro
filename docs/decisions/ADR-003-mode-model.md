# ADR-003 · Mode 模型：信任档位（Plan / Default / Auto）

- **日期**：2026-05-21
- **状态**：accepted
- **决策者**：Claude（用户全权授权代决）
- **关联**：[ADR-001](./ADR-001-product-personality.md)、[04-architecture/modes.md](../product/04-architecture/modes.md)、[09-safety/permission-model.md](../product/09-safety/permission-model.md)

---

## 决策

**不做顶部 Chat / Canvas / Agent 三态 tab**。Mode 表达"对 Kokoro 的信任档位"，借鉴 Claude Code permission mode 哲学。Chat / Canvas / Agent 任务类型保持**隐式自动触发**。

### MVP 3 档（对外叙事）

| Mode | 含义 | 行为 |
|---|---|---|
| **Plan** | 研究态 — "先告诉我你想怎么做" | 仅 read；任何"改 Canvas / 调工具 / 跑外部请求"前必须先给 plan 等用户批 |
| **Default**（默认） | "改之前问我一下" | 关键动作前弹简明确认 |
| **Auto** | 放手态 — "你来吧，我看着" | 不弹确认，每动作有 timeline + 一键回滚 |

实现细节由 [09-safety/permission-model.md](../product/09-safety/permission-model.md) 承载（4 档实现 → 对外收敛 3 档叙事，对内可细分）。

### MVP 优先

只做 `Default` 一档对外，Plan / Auto 后续加。架构必须从一开始支持三档切换，不破坏向后兼容。

---

## 理由

1. **A 候选（全隐式）的优点 C 全保留**：任务类型仍隐式自动触发，用户无须预选场景
2. **"控制感"挪到正确维度**：AI agent 时代真正稀缺的不是"切换任务类型"而是"信任程度"。A 没解决，B（顶部 tab）解错了题
3. **与心路线天然契合**：心路线的核心是"克制、内观、节奏感"。Mode 表达"节奏"刚好对位
4. **与 [09-safety/permission-model](../product/09-safety/permission-model.md) 共享语义**：UI 层 Mode 切换 = Agent 权限层策略切换，少一个概念

---

## 否决项

| 候选 | 否决理由 |
|---|---|
| **B 顶部三态 tab**（CoWork 风格） | 强迫预选违反心路线；三件事经常混着发生，硬切会断裂 |
| **A 全隐式**（Gemini 风格） | 老手没控制感；任务结束前难预知"它要跑多久 / 要不要批准" |

---

## Tradeoff

- 用户需学一次"Mode"概念（用文案缓解，可能不叫"模式"叫"节奏" / "信任档"）
- Plan 易被误解为"不能用 Canvas" → 文案需对齐："Plan 模式下 Kokoro 会先给你看草稿再动手"

---

## 后续待定（不阻塞 lock）

- Mode 中文名（"模式" / "节奏" / "信任档"）：等首版 copy 评审定
- 切换入口位置（输入框右下角 vs sidebar 底部 vs 顶栏右上）：等原型出来定
- MVP 真的只做 Default 还是出 Plan 做研究态：倾向只做 Default

---

## 后果

- [04-architecture/ia.md](../product/04-architecture/ia.md) / [navigation.md](../product/04-architecture/navigation.md) 不需要给顶部留 mode tab 空间
- [05-design-system/components.md](../product/05-design-system/components.md) 的输入框组件需要预留 mode 指示器位置
- [09-safety/permission-model.md](../product/09-safety/permission-model.md) 与 [04-architecture/modes.md](../product/04-architecture/modes.md) 必须严格语义一致
