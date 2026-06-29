# kokoro-model 技术方案

## 定位

kokoro-model 是模型配置、provider account、model binding、label、能力可见性和兜底策略的权威模块。

它回答"这个能力可以用哪些模型、优先用哪个、走什么 transport、网关名是什么"。它不放价格、不放积分、不执行生成。

实现状态：model_provider_accounts/model_bindings/model_labels 表和 ensure/list/resolve 接口已实现；resolve 按 featureKey(+labelKey/transportKind)过滤 active binding、排除 provider status≠active 或 healthStatus=down、priority asc 返回候选。SiteModelPolicy、站点化可见性(siteId)、provider fallback/health-check logs、quotaClass 为规划，当前无任何 site 维度。

## 业务职责

owns：

```text
ProviderAccount  provider 账号与 secret 引用。
ModelBinding     具体模型绑定（provider + modelName）。
ModelLabel       展示层聚合标签。
SiteModelPolicy  站点级可见性与优先级（规划）。
provider priority / health status。
transportKind    litellm / direct / internal 标记。
```

does not own：

```text
用户权限本身（kokoro-user）。
积分账本与价格（kokoro-credit；model 最多给成本参考）。
支付订单（kokoro-payment）。
生成产物（运行时仓库）。
LiteLLM 网关运行态（kokoro-litellm）。
```

## 上游和下游

```text
上游（调用 model）：
  kokoro-agent / 入口   resolve 可用 binding -> transportKind / gatewayModelName。
  kokoro-credit         取模型成本参考（不取价格）。

下游（model 调用）：
  当前无；站点化可见性（SiteModelPolicy 按 site 隔离）为规划。
```

## 核心对象

```text
ProviderAccount
  provider, key, label, secretRef, status, priority, transportKind, healthStatus。

ModelBinding
  providerAccountId, provider, modelName, displayName, featureKey,
  labelKeys, inputModalities, outputModalities, transportKind,
  gatewayModelName, contextWindow, priority, status。

ModelLabel
  key, displayName, description, featureKey, tier, defaultBindingId, status。

SiteModelPolicy（规划）
  siteId, featureKey, labelKey?, modelBindingId?, status, priority, quotaClass?, metadata。
```

transportKind：

```text
litellm   LLM 走 LiteLLM proxy（必须有 gatewayModelName）。
direct    music/video/image 等 provider 由 adapter 直接调用。
internal  内部或自托管服务。
```

## 数据模型

MySQL（Prisma，已实现）：

```text
model_provider_accounts   unique(provider, key)，index(status, priority)
model_bindings            unique(providerAccountId, modelName, transportKind)，
                          index(featureKey, status, priority) / (provider, modelName)
model_labels              unique(key)，index(featureKey, status)
```

规划新增：

```text
site_model_policies   按 siteId + featureKey 限定可见模型与优先级。
```

其它存储：

```text
Mongo / Redis / 对象存储：当前不使用。
外部系统：LiteLLM 网关（仅 transportKind=litellm 时按 gatewayModelName 映射）；
          provider secret 通过 secretRef 引用，不直接落明文。
```

## API / RPC / Events

已实现：

```text
GET  /healthz
POST /provider-accounts/ensure
POST /model-bindings/ensure
GET  /model-bindings              入(query): ListModelBindingsFilter   出: ModelBinding[]
GET  /model-bindings/resolve      入(query): featureKey, labelKey?, transportKind?
                                  出: ModelBinding[]（有序候选，无副作用）
```

resolve 过滤与排序（已实现，单次查询）：

```text
ModelBinding.status = active
  AND ModelBinding.featureKey = featureKey
  AND (transportKind 给定时) ModelBinding.transportKind = transportKind
  AND providerAccount.status = active
  AND providerAccount.healthStatus != down   (允许 unknown / healthy / degraded)
  -> orderBy priority asc, createdAt asc
  -> (labelKey 给定时)后置过滤 labelKeys 含该 labelKey
  -> 返回全部命中候选（含 transportKind / gatewayModelName）。
当前不做 fallbackGroup 链选取，不按 siteId 隔离（规划）。
```

```text
幂等  provider-accounts/ensure、model-bindings/ensure 按业务 key 幂等。
约束  litellm binding 必须有 gatewayModelName；direct binding 不强制。
```

## Admin 管理

```text
basePath  /admin/models（manifest resources: provider-accounts / bindings / labels）
resources provider accounts / model bindings / model labels
          （后续 site model policies / provider fallback order / health check logs）
权限 key  model.provider.manage（细分 read/write 规划中）
操作      provider 账号增改、binding 增改、label 维护、健康状态查看。
审计      provider/binding 变更审计（规划接入统一审计）。
```

（规划）后台查询带 siteId、仅 platform root admin 可跨站；当前无 site 维度。

## 业务链路

```text
model-resolve     按 featureKey(+labelKey/transportKind)解析 active binding（已实现）；
                  site policy + entitlement + fallback 为规划。
litellm-mapping   transportKind=litellm 时 gatewayModelName -> LiteLLM model_name（见 kokoro-litellm.md）。
```

## 部署

```text
服务名   kokoro-model
端口     4221
env      DATABASE_URL_MODEL, KOKORO_MODEL_PORT, KOKORO_MODEL_BASE_URL,
         KOKORO_USER_BASE_URL, KOKORO_CREDIT_BASE_URL, KOKORO_PAYMENT_BASE_URL
多 Pod   权威状态在 MySQL，可多副本。
```

## 测试

```text
集成    resolve 按 featureKey 过滤 active binding，priority asc 有序返回。
反例    disabled binding 不参与 resolve；provider status≠active 或 healthStatus=down 被排除；
        labelKey / transportKind 给定时按之过滤。
        （约束）litellm binding 缺 gatewayModelName 校验为规划项。
```

## 风险和边界

```text
不要把价格放进 model。model 最多给成本参考和能力标签，最终扣费规则在 kokoro-credit。
ProviderAccount 平台复用；模型可见性站点化（SiteModelPolicy）为规划，当前所有站点共享同一候选集。
同名模型由 provider + modelName(+ transportKind) 区分；labelKey 只用于展示聚合，运行时必须解析到具体 binding。
```

## 后续任务

```text
P0  SiteModelPolicy 建表与站点化 resolve；litellm/direct binding gatewayModelName 约束。
P1  provider fallbackGroup 降级；provider health check 与 logs。
P2  与 credit 的成本参考对账；quotaClass 落地。
```
