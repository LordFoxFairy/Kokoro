# Model Resolution 链路

## 目标

为一次能力调用解析出实际可用的 ModelBinding：按站点策略 allowlist + 优先级 + fallbackGroup 选模型，并检查 provider 健康。纯查询、无副作用。模型价格不在此决定（由 credit PricingRule 负责）。

## 参与模块

```text
kokoro-model                   ProviderAccount / ModelBinding（平台复用）+ SiteModelPolicy（站点可见性）。
kokoro-site                    提供 SiteContext（siteId/appKey/surface）。
kokoro-agent / session         发起 resolve，拿到 modelBindingId 后执行。
```

## 前置条件

```text
SiteContext 已解析（siteId, appKey, surface 确定）。
SiteModelPolicy 已为该站配置 allow 的模型。
ProviderAccount / ModelBinding 已在平台层配置。
```

## 主流程

```text
1. Resolve
   POST /models/resolve 入: siteId, appKey, surface, capabilityKey, modelLabel(可选)。

2. 匹配 SiteModelPolicy
   按 siteId + appKey + surface + capabilityKey + modelLabel 找 allow 项；
   未指定 modelLabel 用 defaultForCapability。
   站点只能用 allowlist 内模型，不能绕过。

3. 优先级 + fallback
   按 priority 取首选 ModelBinding；首选不可用时在同 fallbackGroup 内降级。

4. 健康检查
   检查所选 ModelBinding 的 ProviderAccount healthStatus；
   不健康则在 fallbackGroup 内继续降级，但不得跳出站点 allowlist。

5. 返回
   modelBindingId（+ transportKind / gatewayModelName 供执行）。
```

## 异常流程

```text
未授权            请求的模型不在 SiteModelPolicy allowlist -> 403。
全部不可用         allowlist 内模型与 fallbackGroup 全不健康 -> 503。
fallback 越界禁止   provider 健康影响降级顺序，但绝不调用站点未授权模型。
缺 siteId         拒绝解析（不从 host 猜站点，P9）。
```

## 数据变化

```text
无写入。纯读 SiteModelPolicy / ModelBinding / ProviderAccount。
```

## 幂等和一致性

```text
requestId        追踪关联。
无副作用          可重试，不产生状态。
最终一致          ProviderAccount.healthStatus 可能短暂滞后，影响 fallback 选择但不破坏 allowlist。
边界             价格不在此解析（credit PricingRule 负责）；fallback 必须带 siteId。
```

## 用户可见结果

```text
正常      请求落到该站授权的模型，用户无感。
未授权     该能力不可用（403），引导升级或换能力。
全不可用   暂时不可用（503），可重试或稍后再来。
```

## 验收标准

```text
SiteModelPolicy 未授权的模型无法 resolve（403）。
fallback 不会跳出站点 allowlist。
provider 不健康时按 fallbackGroup 正确降级。
music 站看不到只给 video 站开的模型。
解析无副作用，可重复调用。
```

## 相关

```text
编排     ../decisions/ADR-004-agent-orchestration.md
模块     ../modules/kokoro-agent.md
扣费     ./credit-reserve-commit-refund.md（resolve 后 quote/hold）
```
