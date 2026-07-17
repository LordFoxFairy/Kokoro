# Kokoro 积分（credit）定价与利润策略 — PRD / 设计定案

状态：2026-07-17 打磨期定案（落地中）。落地稳定后迁 `docs/kokoro-handbook/`。
适用：kokoro-credit（钱包权威）/ kokoro-session（计量出站）/ kokoro-admin-web（运营）/ kokoro-web（用户面）。
原则：吸收参考项目（hix general_agent）的抽象思路，论据落回 Kokoro 现有 credit 架构与「要赚钱、高利润、合理」的目标。

---

## 0. 目标与非目标

**目标**：一个**高利润、可审计、可调**的积分体系。用户充值/被发放积分 → 对话按模型 token 消费积分 → 房方（平台）在真成本之上稳定加价获利。本地管理平台可手动充值/重置积分做测试。

**非目标（本轮挂点，后续做）**：真实支付集成（充值购买）；订阅套餐 / 每日免费额度的自动周期发放；媒体（图/视频）计费。均在本 PRD 留出形状与挂点，不实现。

---

## 1. 现状事实（Kokoro credit 架构，落地论据）

- **钱包=kokoro-credit**：账户按 `(siteId, ownerKind, ownerId)` 定位；对话计费恒 `ownerKind:"team", ownerId:namespace`（namespace=JWT sub=个人 team cuid）。
- **计量=kokoro-session**：`applyBillingOnAccept` 建 hold、`settleRunBilling` 结算；shadow 档**仍真实扣减**，只是余额不足不拒绝。
- **定价规则**：`priceLine` 按 `(featureKey, labelKey?, unit)` 命中，缺 labelKey 回落 `(featureKey, null, unit)`；`charge = amountMicros × tokenQuantity`。**天然支持分模型（per-labelKey）计价**。
- **hold**：估价 `priceUsage(est 1000 in/1000 out) × 1.20` buffer，min 1 micro；`settle`：实际 `in×inRule + out×outRule`，clamp 到 hold，`captureHold` 落账（reason=model_call）。
- **读**：session `/billing/summary`（balance_micros/held_micros）、`/billing/ledger`（entries，delta_micros 带符号）。
- **发放**：`/admin/credits/grant {ownerKind, ownerId, amountMicros, reason}`；**只增量、无 set-to-value 重置**。

参考项目对照（只吸收思想）：credit 有 USD 锚点（1 credit=$0.006）+ 加价倍率（1.3/1.5/2×，但零散硬编码、真成本被埋、无套餐/充值）。**其自评短板正是我们要超越的**：加价应「单一可配置系数」、真成本与加价分离可审计、钱包侧（套餐/充值）它没有——那正是我们的地盘。

---

## 2. 积分单位与货币锚点（定案）

- **内部记账仍用 micros**（整数、精确，承载分数级 token 计价）。
- **用户面单位=积分（credit）**，定义 **1 积分 = 10,000 micros**。用户只见整数积分。
- **售价锚点：1 积分 ≈ ¥0.01（1 分）**，即 100 积分 = ¥1。等价 1 micro = ¥0.000001。锚点把「用户售价」与「供应商真成本」解耦——换供应商/调成本不动积分对用户的价值。
- 换算单一真源常量 `MICROS_PER_CREDIT = 10_000`（credit 与消费侧共享），前端/运营/后端都据此显示与录入。

---

## 3. 利润模型（可审计——对参考的关键改进）

**核心公式**：`用户售价(micros/token) = 供应商真成本(micros/token) × 加价系数(margin)`。

- **加价系数单一、显式、可配**：不再像参考那样把加价埋进费率表 / 零散硬编码。每条定价规则的 `amountMicros` 即最终售价，其推导（`raw × margin`）在**定价表**登记，使有效毛利可审计（见 §7 定价表）。
- **默认加价 ≥ 4×（文本核心）**：文本 token 真成本极低，高倍率对用户仍便宜、对房方毛利厚。媒体/工具（后续）单列更高倍率（参考媒体用 2×，我们文本核心可更高）。
- **分模型档**：靠 per-labelKey 定价规则实现——内置默认（claude-code 门面）低档、未来 premium（opus 级）高档（更高真成本 × 可更高 margin）。
- **长上下文加价（挂点）**：可选，超阈值 token 提高档位费率（参考的 TieredModelRate 思路），本轮不实现，定价表预留列。

## 4. 计费机制（house-favor 利润原语）

- **按模型调用**：`Σ(tokens × per-token 售价)`。
- **向上取整到整积分**：settle 落账按 `MICROS_PER_CREDIT` 边界 `ceil`——碎屑归房。（吸收参考的 `ceil()` 原语。）
- **最小消费保底**：每次 run 最小 1 积分，杜绝零收入调用。
- **hold buffer 20%**（沿用），**clamp 到 hold**（沿用），失败媒体不退（媒体上线时启用，挂点）。
- 约束：`charge = min(hold, max(MIN_CHARGE, ceilToCredit(actual)))`——取整/保底不得超 hold（hold 估价含 20% buffer，足以覆盖）。

## 5. 钱包操作

- **发放 grant（+delta）**：沿用 `/admin/credits/grant`。
- **重置 reset（set-to-value）**：**新增**——把余额设到目标值（测试/运营纠偏用）。实现=读现额→算差额→落一条 `manual_adjustment` 调整分录（可正可负），杜绝直接改余额不留痕。
- **消费 spend**：hold/settle（沿用）。
- **读**：summary/ledger（沿用）。

## 6. 套餐 / 免费额度 / 支付（挂点，本轮不实现）

- **免费额度**：每日 N 积分免费额（每日封顶周期发放）——钱包侧周期 grant 钩子，设计形状、后续实现。
- **套餐订阅**：按档月度发放积分——同上。
- **支付充值**：kokoro-payment 已在（PAY-1）；充值成功→credit grant。本轮只留挂点：admin 手动充值即「充值成功→grant」的人工版，支付接入后替换触发源。

## 7. 定价表（内置默认档，dev 落地值；真成本待供应商价目表填齐）

| featureKey | labelKey | unit | 真成本(micros/token) | margin | 售价 amountMicros | 说明 |
|---|---|---|---|---|---|---|
| chat | (default) | input_token | 待填 | ≥4× | **40** | 内置默认门面输入 |
| chat | (default) | output_token | 待填 | ≥4× | **120** | 内置默认门面输出 |

- 典型短对话（~500 in + 500 out）≈ (500×40 + 500×120)/10000 = 8 积分 ≈ ¥0.08，取整/保底后不低于 1 积分。
- 真成本列需从供应商价目表录入以让毛利可审计（数据维护任务，非本轮阻塞）；本轮售价为清晰加价后的合理 dev 值。
- 内置定价的**定义归属**：与「内置模型目录归 kokoro-model seed:builtin」同构——内置定价应最终归 kokoro-credit 的 seed:builtin 单一真源（本轮先在 closure-up 种，PRD 记为收敛点）。

## 8. 强制策略

- **shadow（dev 默认）**：真扣减，余额不足不拒。
- **enforce（生产）**：不足→402，**软降级**（挡付费模型调用，文本/免费能力继续）——参考的 soft-degrade 思路，媒体/套餐上线时完善。

---

## 9. 落地任务台账（本轮）

- [x] 研究（参考 + Kokoro 架构）
- [x] 本 PRD 定案
- [x] credit：MICROS_PER_CREDIT 单位（domain/amount）+ reset（§5，set-to-value 带符号分录）
- [ ] credit：加价定价（§7，closure-up 种高加价档）
- [ ] admin-web：手动充值 grant + 重置 reset（§5）
- [ ] web 用户面：积分余额/流水/消费展示（§2 换算）
- [ ] 全链 e2e 验收（签→发放/重置→对话→扣减→核对余额+流水）
- **挂点（本轮不实现）**：
  - **向上取整/碎屑归房（§4）**：`ceilToCreditMicros` 已落 domain/amount 并单测，但**启用需先把整套 credit 测试夹具从亚积分 micro-pricing（如 in=2/out=6）升到积分尺度**，否则 settle 对亚积分实额取整会撞 hold clamp、破坏 quota「buffer 释放不双算」语义。留作专注一轮（连夹具重标定）。当前 settle 按实额 clamp，毛利由 §3 加价（≥4×）承载——加价才是利润主引擎，取整是碎屑级次要杠杆。
  - 支付充值、套餐/免费额度周期发放、媒体计费、长上下文加价、内置定价迁 kokoro-credit seed:builtin

以上勾销状态与本仓 `docs/task.md` 及会话 task 列表同步。
