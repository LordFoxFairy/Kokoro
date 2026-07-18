# Kokoro 支付充值（top-up）整体闭环 — PRD / 设计定案

状态：2026-07-17 打磨期定案（落地中）。与积分策略 PRD（`2026-07-17-credit-pricing-strategy.md`）配套。
适用：kokoro-payment（订单/网关/到账）/ kokoro-credit（钱包）/ kokoro-web（购买 UI）/ closure-up（dev 编排）。

---

## 0. 目标：用户自助购买积分的整体闭环

`浏览套餐 → 下单 → 支付 → 到账（恰一次）→ 余额 → 对话消费 → 查余额/流水`。与**后台管理员手动充值/重置**（credit admin，应急/纠偏/测试）并存互不冲突：两者最终都落 credit 钱包，只是触发源不同（用户支付 vs 运营手动）。

---

## 1. 现状（研究结论：闭环在代码里已存在，仅 3 处缺口）

payment 已有完整：Plan/Order/Subscription/PaymentEvent/Provider/Refund 模型 + 状态机（`pending→confirming→paid→refunded`，confirming=outbox 意图态 + sweeper 重放不双发）；webhook 验签/重放幂等/状态机驱动；provider 抽象（stripe/alipay/wechat/**mock**，mock 恒挂）；**payment→credit 到账已 wired 且恰一次**（`confirmOrder → grantPurchaseCredits → credit /accounts/ensure + /grant`，幂等键 `order:<id>`）；退款反向（`order-refund:<id>` → credit /spend）；web 购买 UI（pricing-panel 套餐卡 + Buy）+ BFF（/api/billing/plans、/checkout）已挂在 settings「订阅」页。

**缺口（本轮补齐）**：
- **G1 hosted checkout**：`startCheckout` 恒 501（缺「创建 checkout 会话/URL」的 provider 能力）——happy path 的唯一落点。
- **G2 dev 无套餐**：closure-up 不 seed plans，目录空。
- **G3 payment 未起 + web 未配**：closure-up 不 boot payment（4241，DB 已迁），web `KOKORO_PAYMENT_BASE_URL` 注释掉 → web 诚实「支付暂未开通」。

## 2. 定价（积分包目录，高利润 + 量折扣）

毛利在**消费侧 ≥4× token 加价**实现（见积分 PRD）；积分包按 **¥0.01/积分** 售卖，**大包给量折扣**（小幅让利换更大预付、降支付笔数成本）。dev seed 档：

| key | 名称 | 积分(creditMicros) | 定价(amountMinor, 分) | 每积分 | 折扣 |
|---|---|---|---|---|---|
| pack-100 | 入门包 | 100 (1_000_000) | ¥1.00 (100) | ¥0.0100 | — |
| pack-500 | 标准包 | 500 (5_000_000) | ¥4.50 (450) | ¥0.0090 | 10% |
| pack-1000 | 超值包 | 1000 (10_000_000) | ¥8.50 (850) | ¥0.0085 | 15% |
| pack-3000 | 尊享包 | 3000 (30_000_000) | ¥24.00 (2400) | ¥0.0080 | 20% |

`billingInterval=once`（一次性积分包）。订阅（month/year）用 Subscription 通道，本轮不 seed（挂点）。金额锚定：createOrder 校验 client 金额=plan 金额（防少付拿全额），已存在。

## 3. dev 支付形态（mock provider，闭环可跑；真网关挂点）

真 hosted checkout（Stripe/支付宝/微信 托管收银台 + 各自 webhook）留挂点。dev 用 **mock provider** 打通同形闭环（切真网关时流程不变，只换 startCheckout 造 URL 的 provider 与 webhook 验签）：

1. **G1**：`startCheckout(plan, team, site)` mock 档 → 建 order（pending）→ 返回 `checkoutUrl = <web>/billing/pay/<orderId>`（dev 模拟收银台）。
2. **web 模拟收银台** `/billing/pay/[orderId]`：显示订单（套餐/金额/积分）+「确认支付（DEV 模拟）」→ POST `/api/billing/mock-pay {orderId}`。
3. **web BFF** `/api/billing/mock-pay`：用 dev mock webhook secret 签名 `{eventId, eventType:payment_succeeded, data:{orderId}}` → POST payment 公开 webhook `/payments/webhooks/mock` → 验签幂等 → `confirmOrder` → **到账**（走既有恰一次 grant）。
4. 回跳 web billing → 刷新余额/流水（含 topup 分录）。

真网关档：startCheckout 返回真网关收银台 URL；用户在网关页支付；网关回调真 webhook（provider 验签）→ 同 confirmOrder。web BFF 不持任何 secret（mock secret 仅 dev）。

## 4. 幂等 / 对账 / 退款（已存在，本轮沿用）

- **到账恰一次**：webhook 重放由 `payment_events [provider,eventId]` 唯一键挡；grant 幂等键 `order:<id>`；order 只在 `pending/confirming→paid` 跃迁 grant，重复 confirm 早退。
- **崩溃恢复**：confirming outbox + sweeper 重放（同幂等键不双发）。
- **退款**：webhook refund_succeeded → reverseCredits（credit /spend，键 `order-refund:<id>`）→ order→refunded。
- **对账**：admin 面 orders/events/refunds 列表 + events replay。

## 5. 落地任务（本轮）

- [x] 研究（payment 全景 + 缺口）
- [~] 本 PRD 定案
- [ ] closure-up：boot payment(4241) + enable mock provider + seed 积分包 plans + seed mock provider 行 + web KOKORO_PAYMENT_BASE_URL/mock secret（补 G2/G3）
- [ ] payment：`startCheckout` mock 档实现（建 order + 返回 web 模拟收银台 URL）（补 G1）
- [ ] web：`/billing/pay/[orderId]` 模拟收银台 + `/api/billing/mock-pay` BFF（签发 mock webhook 驱动到账）
- [ ] 整体闭环全链验收（浏览套餐→下单→支付→到账→余额→对话→扣减→流水）
- 挂点（不实现）：真网关 hosted checkout（Stripe/支付宝/微信 session 创建）、订阅周期计费 UI、发票/税、web 支付成功页打磨。

## 6. 边界：admin 手动 vs 用户支付

- **admin 手动**（credit `/admin/credits/grant|reset`，已落地）：运营应急/纠偏/测试，无支付、留审计分录。
- **用户支付**（payment checkout→webhook→confirm→grant，本轮补齐 dev 闭环）：用户自助，reason=subscription/topup，绑订单可对账。
- 二者独立触发、同落 credit 钱包，互不干扰。

台账与 `docs/task.md` 及会话 task 列表同步。
