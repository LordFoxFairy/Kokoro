# 套餐、积分和商业模型

## 定位

Kokoro 的商业模型由 plan、offer、credit、entitlement 共同构成。payment 负责卖什么，credit 负责到账什么、怎么消耗。

## 核心概念

```text
Plan            套餐模板或站点套餐。
Offer           某站点实际售卖的商品组合。
Subscription    周期订阅。
Top-up Package  增量积分包。
Credit Account  用户或团队的积分账户。
Entitlement     权益，如可用功能、额度、折扣、并发数。
Usage Record    一次能力使用记录。
```

credit 侧的对象和账本权威见 [../modules/kokoro-credit.md](../modules/kokoro-credit.md)。

## 套餐类型

```text
Free                  低额度试用，主要用于激活。
General Pro           通用聊天和轻量能力。
Music Pro             Music Studio 专属。
Video Pro             Video Studio 专属。
Creator Bundle        多 Studio 组合。
Enterprise / White-label  独立站点、团队、账单和管理。
```

## 计费原则

```text
模型不决定最终价格。
Agent 不直接扣费。
Payment 不直接写 credit ledger。
Credit 是唯一余额和账本权威。
不同站点默认独立套餐和积分。
跨站通用积分必须显式作为产品能力设计。
```

## 扣费闭环

```text
1. 用户发起任务。
2. agent/session 向 credit 请求 quote。
3. credit 创建 hold。
4. agent/provider 执行。
5. 成功 commit hold，写 ledger 和 usage。
6. 失败 release hold。
7. 实际成本偏差通过补差或退款修正。
```

完整链路见 [../business-flows/credit-reserve-commit-refund.md](../business-flows/credit-reserve-commit-refund.md)。

## 价格组合

一个 capability 的价格可以由多层决定：

```text
siteId
featureKey
surface general/studio/api
model label / model binding
plan tier
discount policy
provider cost
campaign
```

## 后续后台

后台需要支持：

```text
套餐管理、站点 offer、积分包、pricing rule、
entitlement、手动调整、usage 审计、provider 成本和毛利。
```

## 风险

最容易乱的是把价格、模型、套餐、扣费写在同一个地方。正确分工：

```text
model     能用哪些模型，给成本参考，不定价。
payment   卖什么商品，不写 ledger。
credit    到账什么权益，使用时扣多少。
agent     执行任务，不改余额。
```
