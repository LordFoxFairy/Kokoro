# Billing 成熟方案对标与复用决策

状态：方案依据，2026-08-22。

## 1. 对标结论

| 项目 | 直接观察到的成熟能力 | Kokoro 采用方式 | 不直接引入的部分 |
|---|---|---|---|
| OpenMeter | CloudEvents usage ingestion、meters、entitlements、grant priority、expiration、balance、notifications、LLM cost tracking | 采用事件模型、grant priority/expiration、entitlement 与 usage 分离 | 不直接引入其 Go + PostgreSQL + ClickHouse + Kafka 全套基础设施 |
| Lago | billing engine、credit transactions、prepaid credits、subscription、metering/billing/payment 分层、grant priority | 采用 credit transaction、grant lot、消费分配、支付与 billing 分层 | 不复制其 Ruby/Rails + PostgreSQL + ClickHouse 实现 |
| LiteLLM | provider/model/user/team/key 预算维度、Redis 多实例 spend sync、DB spend logs、预算窗口和 token/cost tracking | LiteLLM 继续承担模型 provider cost normalization；Billing 可接收 diagnostics | 不把 LiteLLM Redis counter 当钱包账本，不复制其 proxy budget code，也不让 token/cost 决定 GA 用户按次价格 |

根仓已有的 `PRD-03`、`PRD-04` 和 `2026-08-13-kokoro-canonical-data-model-design.md` 是本项目更高优先级的
本地权威设计证据：它们进一步把 `Entitlement/Credit` 与 `Payment` 分成两个 bounded context，用
`Acquisition/Fulfillment`、`PaymentSettlement`、`PaymentReversal` 和 outbox 连接，而不是设计一个万能 Billing
账务模块。本次方案已按该成熟边界修正。

## 2. 复用原则

### 2.1 不复制模型 provider 成本计算

Model/LiteLLM 已经接触 provider、model、token usage 和 provider-specific cost。Billing 不重新维护
每个 LLM provider 的 token price 表；这类数据可作为稳定的 provider-cost diagnostic event：

```json
{
  "eventId": "provider-request-id",
  "tenantId": "tenant_1",
  "accountId": "credit_account_1",
  "featureKey": "llm.chat",
  "modelBindingId": "model_1",
  "inputTokens": "120",
  "outputTokens": "40",
  "amountMicros": "17",
  "currency": "USD",
  "occurredAt": "2026-08-22T12:00:00.000Z",
  "metadata": {"provider":"openai"}
}
```

`amountMicros` 由 Model/LiteLLM cost adapter 计算并作为成本分析输入；它不再是 Feature-first GA 的用户扣费输入。
GA target 的 user price 在 provider accepted `ModelInvocation` 上由 Billing 固定 `invocation_micros`，并以
`billing_ref + hold_ref + invocation_id` 结算；Billing 仍负责 hold、settlement、credit allocation、ledger 和对账。
这样既不重造 provider pricing wheel，也不把 provider token 成本误写为产品计费单位。

### 2.2 采用 grant lot，而不是单一总余额

OpenMeter 和 Lago 的成熟模型都把授予额度作为可追踪的来源，而不是只有一个 `balance`：

```text
paid purchase grant   priority=20  expires_at=NULL
subscription grant    priority=30  expires_at=period_end
promotional grant     priority=10  expires_at=campaign_end
manual adjustment     priority=50  expires_at=NULL
```

消费顺序：先过期时间最近，再 priority，再创建时间；每次消费写 allocation。余额只是 projection，
grant/consumption allocation/ledger 才是可解释事实。

### 2.3 采用事件 Inbox/Outbox

Provider webhook 和 usage event 都先按外部 event id 唯一落库，再异步处理。支付成功、权益授予、credit grant
入账不依赖一次跨服务 HTTP 调用完成。重试只重放同一 event/idempotency key。

### 2.4 Redis 只做同步加速

LiteLLM 的多实例 budget sync 说明 Redis 适合做窗口内快速同步，但其公开 issue 也暴露了 counter
重建、索引和 stale cache 风险。Kokoro 使用 Redis 做 fast-path/lease/rate coordination；MySQL 的
credit ledger、grant allocation、usage event 和 idempotency record 才是最终事实。

## 3. 为什么不直接部署 OpenMeter/Lago

当前 Kokoro 的基础设施约束是 MySQL + Redis，且需要接入现有 IAM/Site/Model/Agent/Session contract。
OpenMeter 的公开架构是 PostgreSQL、ClickHouse、Kafka；Lago 的成熟部署也围绕 PostgreSQL、ClickHouse
和异步 billing pipeline。直接引入会增加第三套数据事实和基础设施，而不是减少自研复杂度。

因此当前决策是：

1. 采用它们已经验证的 domain model、事件语义、credit-grant/entitlement API 形状；
2. 继续使用 Kokoro 的 Node.js 22 + TypeScript + MySQL 8.4 + Redis 7 技术底座；
3. 把 LiteLLM 作为 provider cost adapter；
4. 将来达到高吞吐时，再把 usage event sink 替换为 OpenMeter/ClickHouse，而不改变 Billing command
   contract 和 credit ledger contract。

### 3.1 高吞吐演进触发器

这里不预设一个脱离业务的拍脑袋 QPS 阈值，而使用可观测信号触发架构演进：

- usage event 写入开始持续争用 Billing transaction pool，影响 checkout/hold/settle P99；
- usage 原始事件保留和分析查询开始与 MySQL 账务查询争用 IO；
- 需要按分钟级窗口做大规模聚合、重算或多维分析，而不是单账户账务结算；
- usage ingestion 需要独立水平扩展、回放和削峰，且不能扩大 MySQL 账务事务边界。

触发后只替换 `UsageEvent` 的 ingestion/aggregation adapter：采用 CloudEvents-compatible envelope、独立
事件 sink 和聚合存储；`CreditGrant`、`HoldAllocation`、`CreditJournal`、command receipt 以及 Billing
对外 command/query contract 保持不变。OpenMeter 的架构正是将高吞吐 usage 与 transactional state
分离，这个演进方向优先于在 Billing 内自建第二套分析模型。

## 5. Kokoro 最终复用裁决

- **仓库层**：一个 `kokoro-billing` 子仓库，统一版本、CI、migration、contract 与运行手册。
- **领域层**：Payment 与 Entitlement/Credit 两个 bounded context，各自 repository、表前缀、transaction matrix。
- **数据层**：MySQL 8.4 + Redis；不引入 PostgreSQL/ClickHouse/Kafka 作为当前首发强依赖。
- **模型层**：用 `CreditGrant + HoldAllocation + CreditJournal` 替换单一 mutable balance authority。
- **支付层**：保留 ProviderFact/Settlement/Reversal 的 append-only evidence，Payment 不直接写 Credit。
- **计量层**：LiteLLM/Model 负责 provider cost normalization，Billing 负责 authorization/settlement。
- **Provider 层**：不自行重写 Stripe/Alipay/WeChat 协议；迁移 `kokoro-payment` 已验证的 adapter/registry，
  Billing 只负责把 provider event 接入 inbox 和 settlement/reversal 状态机。

## 6. 证据来源

- [OpenMeter repository](https://github.com/openmeterio/openmeter)
- [OpenMeter architecture: usage pipeline separated from transactional state](https://github.com/openmeterio/openmeter/blob/main/docs/architecture.md)
- [OpenMeter releases: credits, grants, priority, expiration, LLM cost](https://github.com/openmeterio/openmeter/releases)
- [Lago billing/metering/payment separation](https://github.com/getlago/lago/wiki/Anatomy-of-a-B2B-payment)
- [Lago wallet model](https://github.com/getlago/lago-api/blob/main/app/models/wallet.rb)
- [Lago wallet API](https://github.com/getlago/lago-php-client)
- [LiteLLM provider budget and Redis synchronization](https://github.com/BerriAI/litellm/blob/main/docs/proxy/provider_budget_routing.md)
- [LiteLLM spend tracking index incident](https://github.com/BerriAI/litellm/issues/35766)
