---
artifact: architecture-child-spec
specId: WAVE-2A-COMMERCE-REDEEM-CREDIT
version: "1.0"
created: 2026-07-28
status: internally-approved
scope: catalog-fulfillment-redeem-subscription-entitlement-credit
accountableArchitectureRole: Commerce Platform Architect
engineeringOwner: team:commerce-core-engineering
qaOwner: team:commerce-quality
mandatoryReviewers: [Product, Finance, Risk, Security, Legal, Support, Platform, Session, QA]
implementationAuthorized: true
gaRuntimeSemanticChangeAuthorized: false
supersedesImplementationShape: [mutable-three-bucket-credit-authority, payment-service-direct-credit-grant, mutable-plan-as-purchase-snapshot, zero-value-payment-for-redemption]
---

# Wave 2A：Commerce、Redeem 与 Credit 技术设计

## 1. 决策摘要

Wave 2A 交付可直接上线的 `redeem_only` acquisition 闭环，不接真实支付，不创建假订单，也不把卡密兑换实现成
Payment 的特殊分支。系统采用成熟 Commerce 分层：Catalog 定义“卖什么”，Acquisition 记录“如何取得”，
Fulfillment 统一“签发什么”，Subscription/Entitlement/Credit 表达“现在拥有什么”，Usage/Journal 记录“如何
消耗”。

本方案冻结以下不可退让的决定：

1. Payment、Redemption、AdminGrant、ProgramWindow 是互不伪装的 acquisition fact。
2. 所有 acquisition 在 `FulfillmentTransaction` 后共用同一后半链。
3. Wave 2A 的新用户 acquisition 只有 `redeem_only`；Payment 八个显式 surface 全部 fail closed。
4. Platform Commerce Core 与 Identity/Site/Policy 处于同一 Platform 产品、同一 PostgreSQL 18 truth、同一
   `PlatformUnitOfWork`，bounded context 之间调用本地 application port，不走 self-RPC。
5. Catalog version、Program version、Offering version、Plan version 发布后不可修改。
6. Credit 权威模型是 `CreditGrant + append-only CreditJournal + CreditHold/HoldAllocation`；daily、period、
   permanent 只是用户读模型。
7. Code 明文只允许出现在批准的一次性加密交付路径；数据库、日志、事件、Admin 和 Support 永不保存或展示。
8. 所有 command 使用 Site/Caller 鉴权、same-key-same-payload 幂等、固定锁序、事务 Outbox 和可重建 receipt。
9. 所有撤销是来源级追加事实；已兑换 Code 永不恢复为可用，历史 Journal Entry 永不改写。
10. GA 不参与 Catalog、Redeem、Subscription、Credit、Admission 或计费；Wave 2A/3 不改变 GA 已有
    `run.request`/`run.cancel` wire 或业务语义，GA 不接收、解析或消费任何新增 grant/credit/auth handle。

## 2. 目标、范围与上线定义

### 2.1 Wave 2A 目标

- 用户在独立 Site 中注册后，可兑换合法 Code，原子取得套餐周期、权益和积分。
- 用户能看到当前套餐、到期时间、不自动续费说明、三桶余额、预留、消费和来源 receipt。
- 第二张相同 Plan Code 可按冻结策略可靠延长；不同 Plan 不被 handler 隐式覆盖。
- 网络丢包、进程崩溃、并发请求、重复任务和重复事件不会多 claim Code 或多签 Grant。
- Operator 可安全生成、导出、启用、暂停、撤销和替换卡密，并能处理 reconciliation。
- Session Admission 只通过 Platform Prepare/Finalize/Release/Reconcile 管理同一执行根预算；Usage producer、rating、
  settlement 与其端到端认证属于 Wave 5A Gateway/Capability，不由 Session 实现。
- `redeem_only` Site 的 Web、BFF、Platform API、worker 和 secret dependency 均不会产生 Payment Provider IO。

### 2.2 非目标

- 不连接 Stripe、Alipay、WeChat 或其他真实 Provider。
- 不实现 Checkout、法币 Refund、Dispute、Tax、Invoice delivery 或 Revenue recognition。
- 不支持跨 Site Credit、Credit 转让、提现或法币余额。
- 不支持不同 Plan 的隐式 upgrade/downgrade。
- 不支持一次 ExecutionRoot 跨多个 credit unit 或 liability merchant。
- 不保留旧 `grant/reset/spend/creditBack` 生产入口或 mutable 三桶兼容层。
- 不修改 GA graph、checkpoint、handoff、terminal 或 tool 核心语义。

## 3. 运行时边界与模块结构

### 3.1 Platform 内部形态

Commerce 是 `kokoro-platform` 内的模块化核心，不拆成新的子仓，也不让每个业务模块独立部署。所有同库对象通过
application port 和 Unit of Work 协作：

```text
modules/{catalog,commerce,redeem,credit,policy,admin}
application/{unit-of-work,projections}
interfaces/{public-http,control-rpc,workers}
infrastructure/{postgres,redis,object-store,secrets}
```

Domain/application code不得依赖 HTTP、Connect、Prisma、Redis 或对象存储 SDK。接口层先校验输入，再构造不可变
command；repository 只接受已解析的值对象和明确的 `RequestSecurityContext`。

### 3.2 远程边界

- Site Web BFF → Platform 普通兑换/账户查询：OpenAPI HTTP/JSON。
- Platform Admin Web → Platform privileged command：ConnectRPC/Protobuf。
- Session → Platform：Connect Prepare/Finalize/Release/Reconcile，不直写 Credit 表、不计算费用、不生产 Usage。
- Outbox relay → notification/analytics：版本化事件；consumer 不成为交易提交条件。
- Platform 不通过 HTTP 调自己的 Catalog、Credit、Redeem 或 Subscription 模块。
- GA 不调用 Commerce API，也不消费新增 authorization handle；Session 在 Platform receipt 成功后仍按既有字节级
  `run.request`/`run.cancel` contract dispatch，Platform 负责授权生命周期，Wave 5A producer/Rating 负责结算。

### 3.3 数据真源

PostgreSQL 18 保存全部业务 truth、审计和 checkpoint；Redis 仅做限速/challenge/cache；对象存储仅放一次性加密
artifact；Secret Manager 保存 HMAC/envelope key，数据库只保存 key version/ref。

## 4. 请求安全上下文与所有权

Commerce 不定义第二套 caller envelope，逐字段继承 Wave 1 canonical `RequestSecurityContext`。只有 Platform
边界 verifier/interceptor 能在验证 workload credential 后构造该对象；BFF、browser、Connect message、header 或
request body 只能提供 routing hint，不能“生成”可信 Site、actor 或 BillingAccount 身份：

```text
RequestSecurityContext {
  trustedProductContext {
    SiteProjectBinding / WorkloadIdentityBinding
    siteId / siteReleaseId / environment / region / audience
    allowedOperations / siteSecurityEpoch / bindingEpoch / issuedAt / expiresAt
  }
  actorPrincipal      // AnonymousPrincipal | UserPrincipal | OperatorPrincipal | WorkloadPrincipal
  delegatedGrant?     // 仅允许 Wave 1 定义的 operation/resource/audience-bound delegated grant
  audience / environment / region / issuedAt / expiresAt
  correlationId
  requestId
}
```

`trustedProductContext` 必须由已验证 workload identity、`SiteProjectBinding`、`WorkloadIdentityBinding`、deployment /
release 与 audience 交换得到；`actorPrincipal` 必须来自有效 AuthSession、Operator session 或 workload identity。
所有 issuer、audience、subject、expiry、Site/environment/region、session/security/restriction/binding epoch 在入口和
effect point 校验。`x-kokoro-principal`、`x-kokoro-site-id`、Host、body `siteId/billingAccountId/callerKind/scopes`、
caller-level shared secret 与上游 `verified=true` 均不是 authority；不允许 default Site/global/wildcard fallback。

### 4.1 Effect-point authorization

- repository 查询不能仅凭资源 ID；每个 effect 查询均从 `trustedProductContext.siteId` 注入 Site 条件，或先在同一
  事务锁定并验证所属 Site。
- 用户兑换要求 `actorPrincipal.kind=user`，其 Site 与 AuthSession 匹配；BillingAccount 由同事务内有效
  Membership/ownership binding 解析并锁定，不能接受 caller 提交的 owner；同时要求 CSRF 与已发布 SiteRelease。
- Admin command 要求 `OperatorPrincipal + typed SiteScope|GlobalScope|BreakGlassScope`；三者是互斥的 canonical
  scope variant，`BreakGlassScope` 不是 `GlobalScope` 的别名或超集。每个 scope 都冻结并在入口与 effect point 重验
  environment、region、device binding、operator session/security epoch、scope epoch、issuedAt/expiry 和允许的
  operation/resource；Site operator 或 breakglass operator 都不能通过 body/header/default fallback 升级为 global，
  stale epoch、换设备、跨 environment/region 或 audience 不匹配一律 fail closed。
- Worker 使用 audience/operation-bound `WorkloadPrincipal`；只有被 operation 明确要求时才接受同 subject/resource/
  audience/expiry 的 `delegatedGrant`，无用户 Cookie、无 wildcard Site fallback。
- Site、BillingAccount、Program、Batch、Code、Plan 和 legal Merchant 的关联在写入前与锁内各校验一次。
- 读取别站资源统一返回不泄漏 existence 的错误；日志只记录安全 correlation ref。

### 4.2 CallerOperationPolicy

每个 command 注册 actor kind、trusted product operation、audience、Site scope、auth strength、step-up、
maker-checker 和 dry-run policy；未注册默认拒绝，路由层与 application effect gate 双重校验。BillingAccount
membership、live Site/Release/Restriction 与全部相关 epoch 在拿锁后再验，不能把入口通过视为 effect 授权。

## 5. Catalog 与不可变商业快照

### 5.1 对象关系

```text
Product/ProductVersion + Plan/PlanVersion
→ Offering/OfferingVersion → FulfillmentProgramVersion
→ EntitlementTemplateVersion[] + CreditProgramVersion[]
→ SiteOfferingAssignment/AssortmentRevision → SiteRelease
```

- `Product`、`Plan`、`Offering` 是稳定 identity。
- 所有 Version 使用 `draft → validating → ready → published`；published 后只读。
- `ProductVersion.kind` 是 `free | credit_pack | subscription | bundle` discriminated union。
- `PlanVersion` 冻结周期、renewal modes、term/stack/change、grace/dunning 和 allowance 模板引用。
- `OfferingVersion` 冻结可取得组合；Wave 2A 不要求 Price，但保留未来 Payment source 的可选引用槽位。
- `FulfillmentProgramVersion` 冻结 `FulfillmentOutputPlan`，按 Product kind 声明 term、Subscription、Entitlement、
  Credit 的 required/optional/forbidden 输出及其 versioned template ref；不从兑换时的“当前 Plan”推导。
- Catalog 全局复用；SiteRelease 只通过 assignment 选择展示、排序、文案和资格，不复制 Catalog 行。

`FulfillmentOutputPlan` 是可验证 discriminated union：`subscription|bundle` 必须声明 stable Subscription、term 和
相应 Entitlement/Credit 输出；`credit_pack` 禁止 Subscription/term 且只允许声明的 CreditGrant；ProgramWindow
只能 materialize 其 `CreditProgramVersion` 窗口输出，禁止顺带创建 Subscription/Entitlement。publish/compile 阶段
拒绝 required template 缺失、forbidden template 出现或 Product/Plan/Offering/Fulfillment snapshot 不一致。

每个 plan output 必须冻结不可复用的 `outputLineId`、plan 内 `ordinal`、`cardinality`、`templateRevision`、output kind
与 required/optional/forbidden disposition；`outputLineId` 在一个 `FulfillmentProgramVersion` 内唯一，ordinal 连续且
冻结，禁止仅凭 output kind/template 去重。实际输出 identity 由 `(sourceType, sourceId, purpose, cycleKey,
fulfillmentProgramVersion, outputLineId, occurrence)` 确定，数据库 unique；`occurrence` 必须落在 cardinality 范围内。
执行成功前按 line identity 比较 expected 与 actual multiset：required 数量完全相等、optional 不超上限、forbidden
为零，且每项 template revision 相同；任何缺失、额外、重复或 revision 漂移均使整个 UoW 回滚。

### 5.2 Redeem-only SalesPolicyRevision

`SalesPolicyRevision` 冻结 Site、`acquisitionMode=redeem_only`、legal Merchant、允许的 Redeem Program versions；
Payment Provider account 集合为空且 routing policy 为 null。

SiteRelease compile 必须证明：Program 属于允许集合；Product/Plan/Fulfillment/Credit unit 兼容；Program 的
`liabilityMerchantAccountId` 与 SalesPolicy 相同；不存在 Payment Provider assignment；Code 生效窗不超越
Program/Plan policy。live suspension、Restriction 和 kill switch 可覆盖已发布 release。

## 6. FulfillmentTransaction：共享签发脊柱

### 6.1 AcquisitionSource

```text
PaymentAcquisition       // Wave 2A 不可创建
RedemptionAcquisition    // Wave 2A 用户 acquisition
AdminGrantAcquisition    // 受批准的修复/运营签发
ProgramWindowAcquisition // daily/period/free/welcome materialization
```

`RedemptionAcquisition` 冻结 redemption、program version、batch、code fingerprint、Site、BillingAccount、Product/
Plan/Fulfillment revisions、liability Merchant、term policy 和 approval ref。它不得引用 Order、Payment、Price、
Invoice 或 Refund。

### 6.2 Fulfillment identity 与原子性

`FulfillmentTransaction` 冻结 source type/id、purpose、cycle key、BillingAccount、Product/Plan/Offering/Fulfillment
versions、`FulfillmentOutputPlan` digest、status 和 result digest。

唯一键为 `(sourceType, sourceId, purpose, cycleKey)`。一个成功 transaction 在同一 PlatformUnitOfWork 中严格执行
该 frozen output plan，既不能少写 required output，也不能多写 forbidden output：

1. 对声明 Subscription 的 plan 创建或定位 stable `SubscriptionActiveSlot` 与 Subscription；否则证明无该输出。
2. 对声明 term 的 plan 创建 source-specific `SubscriptionTermAllocation`；否则证明无该输出。
3. 仅签发计划列出的 immutable `EntitlementGrant`。
4. 仅 materialize 计划列出的 initial `CreditGrant`；daily/period 后续窗口使用 ProgramWindow source。
5. 对每个 Credit output 创建 balanced CreditJournal issuance transaction。
6. 以 canonical line identity/order 写 expected/actual multiset digest，并验证 required/optional/forbidden exact set；
   receipt、audit、idempotency result 和 outbox 保存相同 output-set digest。

任一写入失败，整笔回滚。`pending/running` 只用于 durable workflow 外壳；用户可见 Grant issuance 仍单事务
提交，不能出现半套权益。Payment、Redemption、AdminGrant 与 ProgramWindow 共用 identity/UoW/receipt/reversal
mechanics，不表示它们必须创建相同输出集合。

### 6.3 Fulfillment 状态

```text
pending → running → succeeded
                  → failed → running
succeeded → reversing → reversed
                     → reconciliation_required
```

重复 source 恢复原 transaction/result；不同 payload 命中同 business identity 时进入 conflict，不合并来源。

## 7. Subscription、Entitlement 与 Allowance

### 7.1 Subscription

`Subscription` 只保存稳定 BillingAccount、serviceScope、Plan identity、current binding 和 aggregate version。
每个周期事实由 `FulfillmentCycle` 和 `SubscriptionTermAllocation` 保存完整 version/source lineage。

- `SubscriptionActiveSlot(billingAccountId, serviceScope, activeSubscriptionId, expectedVersion)` 使用普通 stable unique
  `(billingAccountId, serviceScope)`；创建、切换、到期/撤销清槽均在 Fulfillment/Reversal UoW 内以 expectedVersion
  CAS。数据库不使用依赖 `now()` 的 time-dependent partial unique 来表达“当前 effective”。
- active slot 至多指向一个 base Subscription；effective term 仍由 immutable allocation/reversal/time projection 计算，
  slot 只是并发所有权栅栏，不篡改历史。
- Code fixed-term 创建 `SubscriptionBillingBinding(authority=none)`，绝不自动续费。
- 相同 Plan 第二张卡默认使用 `extend_from_max(now,currentPeriodEnd)`。
- `new_subscription`、`extend_from_max`、`reject_if_active` 必须由 Program version 冻结。
- 不同 Plan 默认拒绝且不 claim Code；未来必须走独立 ChangePlan workflow。
- `credit_pack` 不创建 Subscription，只签 CreditGrant。
- 取消、到期和撤销不删 allocation；effective term 由 allocation、reversal 与时钟投影。

### 7.2 EntitlementGrant

EntitlementGrant 保存 feature/capability key、source、effective/expiry、limits、scope、grant terms 和 revision。
issuance 不可变；撤销追加 `EntitlementRevocationFact`。Admission 只解析当前有效 grant，不能把 Plan 或价格交给
GA，也不能以 Web feature flag 替代 Entitlement。

### 7.3 Allowance 与三桶

`CreditProgramVersion` 定义 amount、unit、calendar zone、window anchor、rollover、expiry、scope 和 burn priority。
PlanVersion/FulfillmentProgramVersion 只引用它，不保存 mutable allowance。

- `daily`：访问或 Admission 时按唯一 `(program,subject,windowKey)` 惰性创建窗口 CreditGrant。
- `period`：按 Subscription term/冻结周期创建 CreditGrant。
- `permanent`：credit pack、welcome 或 Admin source 签发无 expiresAt 的 CreditGrant。
- daily/period/permanent 是 `uxBucketClass`，不是数据库扣减 authority。
- read API 不直接“重置余额”；它可以请求幂等 window materialization，再读取 projection。
- rollover 默认为 none；任何 rollover 都必须是新 Program version 的明确规则。

## 8. Redeem Program、Batch 与 Code 安全

### 8.1 版本与可用性

内容与 live 状态分离：

```text
RedeemProgramVersion + RedeemProgramAvailability(epoch)
RedeemBatch          + RedeemBatchAvailability(epoch)
RedeemCode
RedemptionAttempt
Redemption
```

Program version 冻结 Site eligibility、subject eligibility、Product/Plan/Fulfillment、legal liability、term policy、
duration、stack limit、max expiry、兑换次数和生效窗。Availability 行保存 status、monotonic epoch、reason、actor。

### 8.2 Code format 与存储

- Secret 使用 CSPRNG，随机熵至少 128 bit。
- 用户格式包含 public format/key selector、至少 96-bit 随机且不可枚举的 opaque lookup selector、secret 和覆盖
  全部 public fields+secret 的 typo checksum；规范化不降低 secret entropy。
- 数据库只存 `HMAC(keyVersion, domainSeparator || normalizedSecret)`、短安全 fingerprint 和 format metadata。
- domain separator 至少绑定 environment、Site、Program 和 Batch。
- `(environment, siteId, lookupSelector)` 建唯一 locator index，只返回 immutable Program/Batch refs；拿到 refs 后才按
  public key selector 计算上述最终 HMAC 并常量时间比较。每个 format version 的 locator/HMAC candidate 上限冻结为
  `MAX_CODE_LOOKUP_CANDIDATES<=2`（仅当前/受控轮换 key）；超限、碰撞或 selector 与 checksum/key version 不一致均
  fail closed，禁止扫描 Program、Batch、Code 或历史 keyring。
- HMAC key rotation 保留所有 active inventory 所需旧 version，直到 retention/revocation 完成。
- Code 原文禁止进入数据库、普通 CSV、日志、trace、metrics label、analytics、event、error、Admin、Support。

### 8.3 Batch lifecycle

```text
ProgramVersion: draft → validating → ready → published
ProgramAvailability: inactive → active ↔ suspended → retired
Batch: draft → generated → exported
BatchAvailability: inactive → active ↔ suspended
                   active/suspended → compromised | revoked | expired
Code: available → redeemed | revoked | expired
```

Batch `exhausted` 是 projection，不与 Availability 竞争。suspend/compromise/revoke 只阻止未兑换 Code；已完成
Redemption 只能由单独的 source reversal 或 campaign 处理。

### 8.4 一次性加密导出

`BatchExportArtifact` 是唯一允许短暂包含明文的载体。隔离生成进程直接用 recipient public key/KMS envelope
加密后上传；数据库只存 encrypted blob ref、cipher/hash/ETag/size、recipient key fingerprint、专用 data-key ref、
TTL、intentionId 和 audit metadata。plaintext 不落临时盘、swap、core dump 或备份。

生成器为每一行冻结 `(batchId, outputLineOrdinal, lookupSelector, codeHmac, formatVersion, keyVersion)` 的 canonical
inventory entry digest，并构造 ordered Merkle/root commitment。加密 artifact 内的 manifest 携带同一 ordered line
commitment；生成器以受信 workload identity/attestation 签署 `BatchExportCommitment(batchId, intentionId, lineCount,
inventoryRoot, encryptedArtifactHash, ETag, size, generatorVersion, keyVersions)`。Batch inventory、commitment 与 artifact
ready metadata 必须在一次 CAS/UoW 中满足 count/root/hash/ETag/size 完全一致；缺行、多行、重复 ordinal、root 不同、
签名/attestation 不可信或 artifact 被替换均禁止 exported/activate。commitment 只含 HMAC/locator 安全字段及密文摘要，
不得包含 secret/plaintext derivative。

- 生成需要 maker-checker；生成者、批准者和领取者身份分离。
- `SecretDeliveryClaim` 以 CAS 绑定 artifact、recipient key fingerprint、single-use token hash、expiry 和唯一
  `SecretDeliverySession`；领取者先签署 server nonce 证明持有 recipient private key，KMS recipient 则验证等价的
  workload/attestation grant，证明失败不返回任何 byte。
- `SecretDeliverySession` 状态为 `claimed → streaming → delivered | unknown | expired`，只允许一个 active stream；
  它冻结 artifact ETag/hash/size、recipient proof digest、`nextOffset` 和 revision。每个 Range 必须从已提交
  `nextOffset` 开始并以 CAS 推进，响应与 receipt 带相同 ETag；并发、回退、跳段、换 recipient/设备、换 ETag 或
  第二次从 byte 0 开始均拒绝。同一 session 只可从 durable `nextOffset` 单调恢复，不能 restart 或创建第二 claim。
- 全量 bytes 发送后必须以 final hash/size/recipient ack 做一次 CAS 才进入 delivered；token/claim replay 只返回
  delivered receipt，不再返回密文。连接结果无法证明时进入 `unknown` 并自动 suspend Batch，不猜 delivered。
- delivered/expired/unknown disposal 销毁 artifact 专用 data key/key version 与所有 wrapped-key copies，删除对象的
  所有 versions、multipart parts、replicas/cache copies，并写不可变、可对账的 `SecretDeliveryGcReceipt`。该 key
  material 不进入数据库备份。Batch activation 的充要交付门是：同一 commitment 的 delivery session 为
  `delivered`、recipient ack 与 final hash/size 已 CAS、`BatchExportCommitment` 验证成功、crypto-shred receipt 和
  object-version GC receipt 全部存在；任一 evidence 缺失都不得 activate。
- `expired` 或 `unknown` 永远不是 activation evidence：必须 suspend，完成 disposal 后转 revoke/terminal review；禁止
  通过重领、重建明文、人工改状态或仅补 GC receipt 激活。只有上述完整 `delivered` 路径可以进入 active。
- HMAC inventory 已写但 artifact 丢失/损坏时，Batch 永不 activate，只能 revoke 并生成新 Batch。
- object 上传成功但 DB ready 失败时，按 intentionId/tag GC orphan。
- 无法证明交付结果时状态为 `unknown`，自动 suspend Batch，禁止重建同一批明文。

## 9. Redeem 命令与原子流程

### 9.1 Public API

Public OpenAPI 固定为 preview、confirm、按幂等键恢复、receipt、account products、credit summary、grant detail 和
usage detail 八类资源；所有用户资源从 security context 取 owner，不接受 body/query 覆盖 BillingAccount。

Preview 不 claim、不 reserve；它返回冻结 revisions、term preview、Credit expiry、条款、短 TTL preview token 和
digest。Confirm 必须重新校验所有 live 状态，最终 receipt 以 commit 时结果为准。

### 9.2 Confirm 流程

```text
validate schema/canonical security context/CSRF
→ normalize code, verify checksum, resolve bounded opaque locator
→ derive at most MAX_CODE_LOOKUP_CANDIDATES final HMAC candidates by key selector + located Program/Batch
→ enforce distributed Site/account/IP/device/program/batch velocity
→ evaluate Risk/Restriction; dependency failure = fail closed
→ begin PlatformUnitOfWork
→ atomically claim/lock command identity and compare canonical request digest
→ same identity + different digest fails before any Code/business lock or effect
→ lock ProgramAvailability → BatchAvailability → Code
→ lock BillingAccount → Subscription → TermAllocation scope
→ lock CreditAccount → eligible CreditGrant → relevant HoldAllocation
→ recheck SalesPolicy, epochs, Code, eligibility, Risk epoch, stacking
→ CAS Code available→redeemed
→ create immutable Redemption
→ execute unique FulfillmentTransaction and journal issuance
→ write receipt, audit, command result and outbox; finalize the claimed idempotency record
→ commit
```

用户失败统一为 `REDEEM_NOT_ACCEPTED` 或 `REDEEM_TEMPORARILY_UNAVAILABLE`，不暴露不存在、跨站、已兑换、
撤销或过期。合法 receipt 可以显示其本人 Code 的 safe fingerprint。

### 9.3 Review

需人工审核时只创建 `RedemptionAttempt` 和 `RiskCase`，不 claim 或预留 Code。批准产生 single-use
`RedeemApprovalGrant`，绑定 attempt、request digest、decision、RestrictionEpoch、actor 和 expiry。恢复兑换时仍
运行完整校验和 UoW；Code 已被使用则安全失败。

## 10. 幂等、锁序与一致性

### 10.1 Same-key-same-payload

`IdempotencyRecord` 保存 Site/actor/command scope、key、command version、canonical request digest、
`executing|succeeded|failed_retryable|failed_final` 和 result ref。

Digest 至少包含 environment、Site、resolved BillingAccount、actor subject、operation、Program/Batch/Fulfillment
versions、opaque lookup selector digest、Code HMAC/fingerprint、term policy、relevant security/restriction epochs 和
schema version。原始 code/token 不进入 digest/log。相同 key/digest 返回相同结果；相同 key/不同 digest 返回
`IDEMPOTENCY_CONFLICT`。
Idempotency 行与业务结果在同一事务提交，禁止只依赖 Redis TTL。

每个 effectful Commerce command 在拿任何业务锁之前，以 unique `(environment,siteId,actorSubject,operation,key)`
执行 `INSERT ... ON CONFLICT`/等价原子 claim 并锁定 command identity。新记录冻结 digest；已存在同 digest 的
`executing` 等待/恢复同一 execution，terminal 返回原 receipt；已存在不同 digest 立即
`IDEMPOTENCY_CONFLICT`，且此时尚未读取或锁定 Code、Account、Subscription、Credit 等业务 authority。所有
serialization/deadlock retry 复用同一 identity/digest；所有 mutation 都遵循该前置 fence，禁止先拿业务锁再补
IdempotencyRecord。事务末尾才把 result ref、terminal status 与 outbox identity 写回该已锁定记录；回滚后仍由同一
identity 安全重试，不产生第二 execution。

### 10.2 固定锁 DAG

全体 Commerce mutation 在完成上述 command-identity fence 后共用业务锁 DAG：

```text
ProgramAvailability
→ BatchAvailability
→ Code
→ BillingAccount
→ Subscription(serviceScope)
→ SubscriptionTermAllocation
→ CreditAccount
→ CreditGrant(burn order)
→ CreditHold
→ HoldAllocation
```

不涉及的节点跳过，但顺序不能反转。Idempotency identity 始终先于该 DAG；result/outbox 只在业务事实完成后写入，
它们不是可反转的业务锁节点。Availability update 对 Program/Batch 取排他锁；Redeem 取 share/share/update。
停用命令 commit/返回后不得出现新成功 Redemption。serialization/deadlock retry 必须复用原 key/digest。

### 10.3 PostgreSQL 约束

- 普通 unique `(billingAccountId, serviceScope)` 约束 `SubscriptionActiveSlot`，slot 的 create/swap/clear 与
  Fulfillment/Reversal 使用 aggregate expectedVersion/CAS；禁止基于 `now()` 的 time-dependent partial unique。
- unique 保证 source-specific Fulfillment、TermAllocation、Grant、Window materialization 和 Journal transaction。
- amount 使用 bigint/decimal integer micros，不使用 float。
- 时间统一 timestamptz，业务 calendar zone 由 versioned policy 保存。
- 所有 aggregate 使用 version/CAS；读模型使用 checkpoint，不将 cache 值回写 authority。

## 11. Credit Journal 与余额守恒

### 11.1 权威对象

```text
CreditAccount(BillingAccount, unit, liabilityMerchantAccountId)
CreditGrant(sourceRef, originalAmount, effectiveAt, expiresAt, priority, scope)
CreditJournalTransaction / CreditJournalEntry
CreditHold / HoldAllocation
AuthorizationSegment / RatedUsage
BalanceProjection
```

Journal account type：

```text
grant_issuance_source
customer_available
customer_reserved
customer_consumed
expired
revoked
adjustment
recovery_exposure
```

每个 JournalTransaction 在同 credit unit 下 signed entries 之和为 0。Entry 只追加；纠错使用引用原交易的完整
reversal 加 correction。Projection 可从 Grant/Journal/HoldAllocation 重建，差异进入 reconciliation，不能改
Journal 来迎合 projection。

### 11.2 Burn policy

固定顺序：

```text
expiresAt ASC NULLS LAST
→ burnPriority ASC
→ issuedAt ASC
→ grantId ASC
```

Reserve 按此顺序锁定 Grant 并创建 exact HoldAllocation。不得从聚合三桶直接减数字，也不得在 release 时按当前
余额猜测来源。

### 11.3 Root Hold 与 AuthorizationSegment

```text
ExecutionBudgetRoot
  ├─ one CreditHold → exact HoldAllocation[] → original CreditGrant[]
  └─ root BudgetAllocationRevision
       └─ child BudgetAllocationRevision[]
            ├─ AuthorizationSegment[]
            └─ EffectBudgetCommit[] → AttemptUsageEvidence[] → AllocationSettlementReceipt
```

- 一个 `ExecutionRoot + liabilityAccount` 至多一个 `ExecutionBudgetRoot`/root CreditHold；V1 一个 root 只允许一个
  CreditAccount、credit unit 和 liability。Chat Run、未来 Gateway/Capability/Job allocation 共用该 root；Direct
  Studio 是新的 ExecutionRoot，才创建独立 Hold。
- `ExecutionBudgetRoot` 冻结 Site、BillingAccount、liability、root Hold、RatingPolicy、reserved ceiling 和 revision。
  `BudgetAllocationRevision` 冻结 parent/root、audience、purpose、ceiling、dimension envelope、allocationEpoch、
  expectedVersion，以及 stock `unassignedStock/activeChildReservedStock/committedStock` 与 cumulative flow
  `capturedCumulative/returnedToParentCumulative`；stock 是当前可支配状态，cumulative 只记录该 allocation 的历史
  terminal 去向，二者不得混作可再次分配余额。
- Platform Credit/Admission 是 allocation 唯一 owner。child 由 Platform 以同一事务/CAS 从 parent `unassigned`
  切出；consumer 不能自行扩容、reparent、换 audience/liability 或创建第二份 root Hold。Wave 2A/3 不把 allocation
  handle 加入 GA wire；GA-facing producer/consumer integration 在 Wave 5A 完成。
- 每个 allocation 在每个 durable revision 必须满足 node-local conservation：

```text
ceiling = unassignedStock
        + activeChildReservedStock
        + committedStock
        + capturedCumulative
        + returnedToParentCumulative
all terms >= 0
activeChildReservedStock = SUM(ceilings of direct active child allocations)
```

parent 接收 child return 时，在同一 UoW 将 child 冻结为 immutable terminal revision、从 parent
`activeChildReservedStock` 减去 child ceiling 并向 parent `unassignedStock` 加入 returned amount；terminal child 自此
不再属于 parent active-child set。`returnedToParentCumulative` 只用于 child 的 node-local history，绝不能在 root/tree
余额中再次求和。tree-wide conservation 只递归展开当前 active allocation tree 一次：

```text
rootCeiling = SUM(each active allocation's unassignedStock + committedStock)
            + treeCapturedCumulative
            + releasedBackToRootHoldCumulative
```

父节点的 `activeChildReservedStock` 只用于 node-local invariant，tree-wide 展开时由 active child 的 stock 取代，
禁止同时计数；`treeCapturedCumulative` 和
`releasedBackToRootHoldCumulative` 由 Journal/settlement receipt 去重汇总，内部 child return 不属于 root release。
terminal revision 的 ceiling、flows、terminal receipt digest 和 parent-applied revision 永久冻结；相同 return receipt
只能返回原结果，不得重复增加 parent stock。

- allocation 不能跨 Site、BillingAccount、ExecutionRoot、RatingPolicy 或 liability 复用；resize/revoke 后旧
  allocationEpoch 不能创建新 effect。`EffectBudgetCommit` 在外部 effect 前冻结 logical effect、request digest、
  maximum credit 和 operation key；unknown 保持 committed/reconciling，不能 return/reuse。
- child 只有在所有 descendants terminal、所有 committed/unknown effect 已 settled 或明确关闭、consumer lease 与
  old epoch 已 fence 后才能原子 terminal CAS 并创建 `AllocationReturnReceipt`；receipt durable 后 parent 才增加
  `unassignedStock`。worker crash、browser disconnect、lease expiry 或“未看到结果”都不是 return 证据。

### 11.4 CreditHold、AuthorizationSegment 与 Effect 状态分离

Root `CreditHold` 只表达整个 ExecutionBudgetRoot 的预留 envelope 与最终归还，不含 segment `rating_pending`，也不在
第一次 dispatch 时把整个 Hold 切成 committed：

```text
open(reservedEnvelope) → closing → settled(capturedAmount, releasedAmount)
open(no committed segment/effect) → released | expired
open | closing → reconciliation_required → closing | settled
```

- Prepare Admission 创建/复用 root Hold 的 `open` envelope，并创建一个 `reserved` AuthorizationSegment；只有从未
  产生 committed segment/effect 的 root 与未 committed segment slice 可因短 TTL 自动 release。
- dispatch 前 Finalize 只 CAS 当前 AuthorizationSegment slice `reserved→committed`，并以唯一 segment/effect identity
  将相同 amount 从 allocation `unassignedStock` 移至 `committedStock`；root Hold 保持 `open`，后续合法 Segment 仍可
  从剩余 stock 授权。commit receipt 丢失返回同一 receipt，不重新 commit 或 dispatch。
- committed segment/effect slice 不得由普通 sweeper 释放；其 outcome unknown 使该 slice 与 root 进入
  `reconciliation_required`，但不得把其他未相关 slice 猜作 committed/settled。
- Platform capture 将 Wave 5A producer 提交并经 Rating 验证的 Usage 从 reserved 转 customer_consumed，并释放剩余
  allocation；Wave 2A Session 不生产 Usage、不计算 rating、不宣称 settlement E2E。
- release 按原 Grant 当前状态进入 available、expired 或 revoked，绝不复活过期/撤销额度。
- actual cost 超 ceiling 只能截断/停止或经重新授权创建新 Segment，禁止负余额和静默透支。

`AuthorizationSegment` 单独管理一次可关闭的执行区间：

```text
reserved → committed → rating_pending → settled
committed | rating_pending → reconciliation_required → settled
```

每个 Segment 绑定 root/allocation/manifest/rating snapshot/hold 与 fence epoch。Session 只调用 Platform
Prepare/Finalize/Release/Reconcile；Finalize 后仍以既有 `run.request` dispatch。Attempt terminal 后由 Wave 5A
Gateway/Capability 在 effect-local transaction 写 `AttemptUsageEvidence + outbox`，Platform Rating 幂等创建
`AllocationSettlementReceipt`。terminal Attempt 缺 evidence 不是零费用，而是 reconciliation_required。

## 12. 来源级撤销、补发与纠错

```text
RevokeRedemption
→ RedemptionRevocationFact
→ FulfillmentReversalTransaction(source=redemption)
  → reverse unused SubscriptionTermAllocation
  → EntitlementRevocationFact
  → CreditRevocationFact + balanced Journal reversal
  → committed/unknown exposure → RecoveryCase
→ optional ReplacementCodeIssuance or AdminGrant
```

- 已兑换 Code 永不回到 available。
- 只撤销目标 source 的未使用 term、Entitlement 和 Credit，不借用其他 source 补账。
- 已消费 amount 不制造负 available；进入 RecoveryCase，按批准 policy 形成 recovery/correction facts。
- 误绑不转移 owner；撤销后给正确 owner 新 Code 或 AdminGrant。
- replacement 引用原 Redemption/Revocation，maker-checker，使用同一 SecretDelivery 协议。
- 外部售卡方退款只保存受控 external reference，不创建 Platform Refund 或伪造资金处理。

Compromised Batch 使用 `RedemptionRevocationCampaign`：planned → approved → running → completed/
partially_completed/failed/canceled。Campaign 冻结 scope/policy，以 RedemptionId 幂等推进 durable cursor，允许
pause/resume；每个 reversal 是独立 `PlatformUnitOfWork`，将 reversal fact、目标 source 输出反转、Journal、receipt、
audit、idempotency 与 outbox 原子提交，不用一个大事务批量删 Grant。

## 13. Transactional Outbox、Projection 与 Reconciliation

### 13.1 Outbox

业务事实与 `OutboxMessage` 在同一 UoW 写入。message 冻结 `producerId/eventId/topic/schemaVersion/aggregateId/
aggregateSequence/digestAlgorithmVersion/payloadDigest/envelopeDigest/payload/occurredAt`。schema 必须为每个版本指定
唯一 canonical bytes：Protobuf 使用冻结 schema 的 deterministic serialization（例如 `SHA256_PROTOBUF_V1`），JSON
只能使用 RFC 8785 JCS（例如 `SHA256_JCS_V1`）；禁止依赖语言 map 顺序、数据库 JSON rendering 或未版本化 stringify。
`payloadDigest` 哈希 canonical payload bytes；`envelopeDigest` 哈希 domain separator、digest algorithm/version、
producerId、eventId、topic、schemaVersion、aggregateId、aggregateSequence、occurredAt canonical value 与
payloadDigest，因而 topic/schema/producer/aggregate/sequence 任何变化都会改变 identity evidence。数据库 unique
`(producerId,eventId)`；同 identity + 同 envelopeDigest 恢复原 message，同 identity + 不同 digest 立即 quarantine
并 page Platform Commerce owner，禁止覆盖或 publish。

relay 使用 claim/lease、attempt、nextAttemptAt 与 durable publisher checkpoint；broker ack 后才推进 checkpoint，
超 attempt/window 进入 DLQ。consumer 必须先按声明的算法/version 重建并验证 payload/envelope digest，再在处理 effect
的同一事务写 `ConsumerInbox(producerId,eventId,envelopeDigest,digestAlgorithmVersion,processedAt,resultRef)`，unique
`(producerId,eventId)`；重复同 digest 返回原结果，不同 digest 或不可识别算法/schema 直接 quarantine，
不得仅以内存/Redis 去重。producer outbox/DLQ/replay owner 是 Platform Commerce on-call；每个 consumer team 拥有其
inbox/checkpoint/quarantine 与 deadline，Reconciliation 只通过 typed replay/skip-after-approval command 推进。
Outbox 卡住不回滚已成功兑换，Account receipt 可直接从 authority 读取。

### 13.2 投影

- `RedemptionReceiptProjection`：Redemption → Fulfillment → term/Entitlement/Credit refs。
- `AccountProductProjection`：current subscription、renewal authority、next change、effective grants。
- `BalanceProjection`：available/reserved/cost_pending/settled/expired/reversed，按 UX bucket/source 聚合。
- 投影带 source checkpoint、asOf 和 freshness；落后时 UI 显示 pending，不猜成功或失败。

### 13.3 Reconciliation jobs

- Journal balance 与 CreditGrant original/remaining 守恒。
- Hold 状态与 allocation/capture/release 合计守恒。
- Fulfillment succeeded 与完整 term/Entitlement/Credit/result digest 一致。
- redeemed Code 必有唯一 Redemption；Redemption 必有唯一 Fulfillment。
- ProgramWindow acquisition、Grant 和 Journal transaction 一一对应。
- Batch inventory count/hash、delivery artifact、GC receipt 和 activation evidence 一致。

Reconciler 仅生成 Case 或调用 typed repair/reversal/correction command；不得直接 update authority table。

## 14. Admin 与 Support 操作面

### 14.1 专用工作流

必须提供专用页面/命令，不用通用 CRUD 表格替代：

- Catalog/Plan/Offering/Fulfillment revision diff、validate、publish。
- Redeem Program、Batch generate、export、activate、suspend、compromise、revoke。
- Redemption timeline、pending review、source reversal、replacement。
- Grant provenance、Journal transaction、Hold allocation、Usage trace、reconciliation case。
- Campaign dry-run、审批、pause/resume、逐项结果和 partial failure。

### 14.2 高风险控制

Program publish、Batch export/activate、mass reversal、AdminGrant、Journal correction 要求：step-up auth、
reason、expectedVersion、canonical parameter digest、maker-checker、执行 receipt。maker/checker/executor 不能是同一
operator。成功 effect 的 immutable Audit 与业务 effect 在同一 `PlatformUnitOfWork` 提交。入口拒绝或业务 UoW
回滚时，使用独立 fail-closed `RejectedCommandAttemptReceipt` append transaction，冻结 command identity/digest、
actor/product context refs、decision/error class 与 correlation（不含 Code/secret）；该 receipt 无法持久化时 privileged
command 不执行或不返回可重试成功语义并触发 Security on-call。不得声称 rolled-back 事务中的 audit 可以保留。

### 14.3 Support 边界

Support 只能查询 safe fingerprint/correlation ref，并调用 typed reverse/replace/correct/reconcile command。
禁止直接修改 Code status、Subscription end、Grant、Journal、Hold、BalanceProjection 或 GA state。所有结果返回
authoritative receipt 和 Case owner/deadline。

## 15. Payment 八个显式 surface 关闭契约

Wave 2A 将未来 Payment 保留为架构边界，但不开放任何 acquisition 能力。八个 surface 必须同时关闭：

1. `Offering/Assortment`：无可购买 Price/checkout assignment。
2. `SiteRelease/SalesPolicy`：`acquisitionMode=redeem_only`，Provider account 集合为空。
3. `Web UI`：不渲染购买/付款入口，不用支付失败跳转兑换。
4. `BFF route`：checkout/payment/refund mutation 不注册或稳定返回 `ACQUISITION_CHANNEL_DISABLED`。
5. `Platform command admission`：即使绕过 Web 也 fail closed，Order/Attempt 为零。
6. `Worker/provider adapter`：不装配 outbound Provider client，不消费 Payment attempt task。
7. `Secret/config bootstrap`：不要求 Provider credential；若误配也不会自动启用。
8. `Admin`：不发布 Payment manifest/resource/action/page；`/admin/payments/*`（含 stats、grant-plan、plan restore、
   provider upsert/delete、event replay）不注册或稳定 fail closed，Operator/breakglass 也不能绕过。

clean-cut inventory 和 negative route/config tests 必须显式覆盖现有 `/orders/checkout`、`/orders/:id/confirm`、
`/orders/:id/refund`、`/payment-events/record`、`/payments/webhooks/:provider`、`/admin/payments/*`，以及
`DATABASE_URL_PAYMENT`、`KOKORO_PAYMENT_BASE_URL`、`KOKORO_PAYMENT_PORT`、`KOKORO_INTERNAL_SECRET_PAYMENT`、
`KOKORO_PAYMENT_MOCK_WEBHOOK_SECRET`、`KOKORO_PAYMENT_ENABLED_PROVIDERS`、confirm-sweeper 与 provider credential
variables。redeem-only deployment 不注册相关 service/worker/ingress，不把“secret 未设置”当唯一关闭证据。

Redemption 产生的 Subscription/Entitlement/Credit 与未来 Payment 结果相同，但 acquisition receipt 不同。Wave 2B
只能新增 Merchant/Provider/Quote/Order/Checkout/Attempt/ProviderFact/Payment/Refund 前半链，并调用现有
FulfillmentTransaction；禁止复制 Grant、Account success page 或 Subscription issuance。

## 16. Crash 与恢复矩阵

| Crash point | Committed fact | 恢复行为 | 禁止行为 |
|---|---|---|---|
| HMAC inventory 前 | 无 | 删除临时内存/对象 | 产生 Batch count |
| inventory 后、artifact ready 前 | inactive Batch | GC orphan，revoke Batch | activate/rebuild plaintext |
| encrypted upload 后、DB ready 前 | object only | intentionId GC | 普通 bucket 保留 |
| claim 后、download receipt 前 | claim | 同 claim TTL 内恢复；unknown suspend | 新 claim/再导出 |
| Redeem UoW commit 前 | 无 Redemption | 整体 rollback，Code available | 独立补 Grant |
| Redeem commit 后、HTTP 前 | 完整 Redemption | same key 查询原 receipt | claim 第二张 Code |
| Outbox publish 前 | 完整业务事实+outbox | relay 重试 | 回滚已发权益 |
| Hold reserve 后、Finalize 前 | reserved | TTL release 或同 identity finalize | dispatch without commit |
| Finalize commit 后、dispatch ack 前 | committed | 查 receipt/dispatch dedupe/reconcile | TTL release/duplicate run |
| Usage known、rating commit 前 | evidence | 幂等 rating/settle | 猜 cost 或丢 evidence |
| outcome unknown | committed exposure | reconciliation_required | 自动释放或复用额度 |
| reversal 部分步骤前 | reversal intent | source idempotent resume | 改历史 Grant/Journal |

所有恢复动作有 owner、deadline、attempt count、alert 和 terminal receipt。

## 17. Clean replacement 与切换

项目未上线，Wave 2A 使用一次性 clean replacement，不背负错误内部兼容：

固定旧行为 corpus 只用于证明删除范围；在 PostgreSQL 以 TDD 建立统一 schema/UoW 全链，再切换 Session
Admission 与 Web Account/Redeem。随后删除旧 MySQL Credit/Payment schema、跨服务 credit grant client、mutable
bucket authority、direct grant/reset/spend、welcome env、namespace→team billing 映射和旧 sweeper。fixture/seed 只走
versioned Program/Fulfillment/Grant command；clean install、双 Site seed、rebuild/reconcile 通过后才删除旧测试。

若实施时发现真实需要保留的数据，立即停止 clean cut，另立数据迁移规格；本方案不默许双写或长期双库。

## 18. 测试策略与发布门

### 18.1 Domain/property tests

覆盖状态机 terminal 不回退；任意 Grant/Hold/reversal 序列 Journal 平衡、available 非负、projection replay 一致；
burn order deterministic；任意 term stacking 顺序不丢 duration、不超 max expiry。

### 18.2 PostgreSQL integration/concurrency

覆盖同 Code 并发单赢家、同 Plan 双 Code term 串行叠加、suspend 线性化、same-key-same-payload、各事务故障点
全回滚，以及 Finalize/capture/release/sweeper/reconciler 竞争只有一个合法终态。

### 18.3 Security tests

覆盖跨 Site/伪造 header/global scope/service audience 拒绝；匿名试码、CSRF 缺失、Risk/velocity down、stale epoch
fail closed；全 surface 明文扫描零命中；claim replay、recipient 变化、TTL、tamper 和 orphan 安全失败/GC。

### 18.4 E2E journeys

覆盖 preview→redeem→receipt→Account、lost response、same Plan stacking、Plan mismatch、reversal/replacement、Chat
Admission prepare→finalize→release/reconcile、双 Site Web 隔离，以及 stale checkout 在八个 surface 均无 Payment
fact/IO。Wave 2A 仅用 owner contract fixture 验证 Platform rating/settlement 接口与守恒；真实 Usage producer、
rating→settlement/unknown 端到端测试是 Wave 5A exit gate，不能由本 Wave 的 Session E2E 冒充。

### 18.5 上线 No-Go

出现以下任一项禁止发布：Journal 不平衡、Code 明文泄漏、跨 Site 读取/写入、claim 与 Fulfillment 非原子、
committed Hold 被 TTL 释放、无来源 Grant、direct balance mutation、Payment route/provider IO 可达、reconciler
直接修表、Admin 高风险命令无 maker-checker、clean install 或 projection rebuild 失败。

## 19. 成熟模式映射、SLO 与最终约束

本设计采用成熟项目的边界思想而非复制其数据模型：Stripe 的 Payment/Fulfillment 与幂等分离、Medusa 的
workflow/compensation 和 store-credit transaction linkage、Lago 的 wallet funding-consumption traceability。
Kokoro 的差异是 Code acquisition、Site 隔离、一次性 secret delivery、来源级 term/Grant reversal 和执行预算
树；这些差异通过明确 fact、约束和 Journal 表达，不通过万能 status 或 metadata JSON 手搓例外。

SLO：合法兑换成功率 ≥99.9%；lost-response 恢复率 100%；重复 Redemption/Grant、claim 后不完整 Fulfillment、committed Hold 误释放、redeem-only Provider IO 均为 0。
低基数 metrics 覆盖 UoW、幂等、reconciliation、outbox 和 secret GC；Code/HMAC/fingerprint/email/account 不作 label，每个 Case 有 owner、deadline 和 paging threshold。

Wave 2A 已通过内部评审，`implementationAuthorized=true`。实施计划按 Platform schema/UoW、
Catalog/Fulfillment、Code generation/export、Redeem、Subscription/Entitlement/Allowance、Credit/Admission、
Outbox/Reconciliation、Admin/Support、Payment 八面关闭、Web Account/Redeem 与 migration/certification 切片展开。
任何实现不得改变 acquisition 分离、同 UoW 原子性、Credit authority、Site/caller 鉴权或 Payment 八面关闭。
`gaRuntimeSemanticChangeAuthorized=false` 持续生效；如果实现需要修改 `kokoro-agent`、GA wire 或其业务语义，必须停止并单独评审。

## 20. Internal review record

- 2026-07-28：两轮内部架构评审通过，16 项阻断全部关闭。终审确认 idempotency claim/lock 先于
  业务锁、output line identity 与 batch activation commitment 不可歧义、allocation stock/cumulative 与
  root Hold/AuthorizationSegment slice 不重复计数、canonical envelope digest 可验证、
  `SiteScope|GlobalScope|BreakGlassScope` 互斥且 effect-point fail closed，以及 Site authority、Payment Admin 八面关闭与
  GA 零变更边界全部闭合。
- 用户已授权非 GA 实现；`implementationAuthorized=true`。`gaRuntimeSemanticChangeAuthorized=false`
  保持不变，实施不得修改 GA 代码、wire 或业务语义。
