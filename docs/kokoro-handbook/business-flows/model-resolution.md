# Model Resolution 链路

> **状态：历史 V1 ModelBinding resolver 流程。**本文的 `featureKey` 查询和 Session/Agent 取得 binding 的实现记录
> 不定义目标 GA runtime。当前模型选择以 [36 GA 整体 Agent 技术方案](../technical/36-ga-final-agent-technical-plan.md)
> §5.3、§8.2 和 [38 公共运行契约](../technical/38-ga-public-runtime-contract.md) §5.3 为准：Session 只可传可选
> `requested_model_label` 用户意图；GA 用 Workflow 的静态 model policy 选择 adapter，并由每次
> `ModelInvocation`/`attempt_id` 的 accepted/reconcile 事实驱动 Billing。provider 配方、binding、secret 和 fallback
> 不进入 Session、RunRequest 或 checkpoint。

## 历史 V1 目标

为一次能力调用解析出实际可用的 ModelBinding：按 featureKey(+labelKey, transportKind)过滤 active binding，排除 provider 不可用者，按 priority 升序返回有序候选。纯查询、无副作用。模型价格不在此决定(由 credit PricingRule 负责)。

## 历史 V1 实现状态

```text
已实现   GET /model-bindings/resolve；按 featureKey + active 过滤，
         排除 provider status≠active 或 healthStatus=down，priority asc 排序返回候选。
已实现   tenant policy 作为受信 tenant_id + label 的可见性过滤。
规划     quotaClass、provider fallbackGroup 降级、健康检查与 logs。
```

## 参与模块

```text
kokoro-model                   ProviderAccount / ModelBinding / ModelLabel(平台层)。
kokoro-agent / session         发起 resolve，拿到候选 binding 后执行。
```

## 前置条件

```text
ProviderAccount / ModelBinding 已在平台层配置且 status=active。
PricingRule 由 credit 侧另行配置(与 resolve 解耦)。
```

## 历史主流程

```text
1. Resolve
   GET /model-bindings/resolve 入: featureKey, labelKey?, transportKind?。

2. 过滤候选(单次查询)
   ModelBinding.status = active
   AND ModelBinding.featureKey = featureKey
   AND (transportKind 给定时) ModelBinding.transportKind = transportKind
   AND providerAccount.status = active
   AND providerAccount.healthStatus != down  (允许 unknown / healthy / degraded)。

3. labelKey 后置过滤(可选；tenant policy 先过滤 hidden label)
   给定 labelKey 时，仅保留 labelKeys 包含该 labelKey 的 binding。

4. 排序返回
   orderBy priority asc, createdAt asc，返回全部命中的 ModelBinding 候选数组
   (含 transportKind / gatewayModelName 供执行)。不在本层做 fallback 链选取。
```

## 当前执行级契约

当前跨服务模型解析以 `kokoro-model/docs/API_CONTRACT.md` 与 Root Protobuf
`contract/proto/kokoro/model/v1/model_catalog.proto` 为准：

```text
RPC ResolveModel(request_id, tenant_id, label) -> 单个已发布且可用的解析结果
HTTP target POST /resolve -> 本地/适配器等价入口
无匹配 -> NotFound / model.route_not_found
```

本页后续的候选数组、旧 GET 路径和旧 ModelBinding 流程仅保留为迁移历史，不得作为新调用方契约。

## 历史异常流程

```text
无可用候选        过滤后为空 -> 返回空数组，由上游决定降级/报错。
缺 featureKey     resolve 必须带 featureKey(必填)。
provider down     该 provider 的 binding 直接排除(degraded 仍参与)。
tenant 越权拦截  tenant_id 来自受信请求上下文；hidden policy 的 label 不进入候选。
```

## 数据变化

```text
无写入。纯读 ModelBinding / ProviderAccount。
```

## 幂等和一致性

```text
无副作用          可重试，不产生状态。
最终一致          providerAccount.healthStatus 可能短暂滞后，影响候选集但不破坏正确性。
边界             价格不在此解析(credit PricingRule 负责)；
                 tenant 可见性由 model_routing_policy 控制；无 tenant context 的管理预览不得作为 runtime 结果。
```

## 用户可见结果

```text
正常      返回该 featureKey 下按优先级排序的可用模型候选。
无候选     该能力暂不可用，由上游引导换能力或稍后再来。
```

## 验收标准

```text
status≠active 的 binding 不出现在候选中。
provider status≠active 或 healthStatus=down 的 binding 被排除。
transportKind / labelKey 给定时按之过滤。
候选按 priority asc(再 createdAt asc)有序。
解析无副作用，可重复调用。
tenant policy hidden 的 label 不可 resolve。
```

## 相关

```text
编排     ../decisions/ADR-004-agent-orchestration.md
模块     ../modules/kokoro-model.md
扣费     ./credit-reserve-commit-refund.md(resolve 后 quote/hold)
```
