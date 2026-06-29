# Model Resolution 链路

## 目标

为一次能力调用解析出实际可用的 ModelBinding：按 featureKey(+labelKey, transportKind)过滤 active binding，排除 provider 不可用者，按 priority 升序返回有序候选。纯查询、无副作用。模型价格不在此决定(由 credit PricingRule 负责)。

## 实现状态

```text
已实现   GET /model-bindings/resolve；按 featureKey + active 过滤，
         排除 provider status≠active 或 healthStatus=down，priority asc 排序返回候选。
规划     SiteModelPolicy / 站点 allowlist / 站点可见性、quotaClass、
         provider fallbackGroup 降级、健康检查与 logs。当前无任何 siteId 维度。
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

## 主流程

```text
1. Resolve
   GET /model-bindings/resolve 入: featureKey, labelKey?, transportKind?。

2. 过滤候选(单次查询)
   ModelBinding.status = active
   AND ModelBinding.featureKey = featureKey
   AND (transportKind 给定时) ModelBinding.transportKind = transportKind
   AND providerAccount.status = active
   AND providerAccount.healthStatus != down  (允许 unknown / healthy / degraded)。

3. labelKey 后置过滤(可选)
   给定 labelKey 时，仅保留 labelKeys 包含该 labelKey 的 binding。

4. 排序返回
   orderBy priority asc, createdAt asc，返回全部命中的 ModelBinding 候选数组
   (含 transportKind / gatewayModelName 供执行)。不在本层做 fallback 链选取。
```

## 异常流程

```text
无可用候选        过滤后为空 -> 返回空数组，由上游决定降级/报错。
缺 featureKey     resolve 必须带 featureKey(必填)。
provider down     该 provider 的 binding 直接排除(degraded 仍参与)。
站点越权拦截      当前无 SiteModelPolicy / allowlist(规划)，本层不做站点鉴权。
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
                 站点可见性(SiteModelPolicy)未实现，候选不按 site 隔离(规划)。
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
(规划)SiteModelPolicy 落地后未授权模型不可 resolve。
```

## 相关

```text
编排     ../decisions/ADR-004-agent-orchestration.md
模块     ../modules/kokoro-model.md
扣费     ./credit-reserve-commit-refund.md(resolve 后 quote/hold)
```
