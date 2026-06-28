# kokoro-model 技术方案

## 定位

kokoro-model 是模型配置、provider account、model binding、label、能力可见性和兜底策略的权威模块。

它回答"这个站点这个能力可以用哪些模型、优先用哪个、走什么 transport、网关名是什么"。它不放价格、不放积分、不执行生成。

实现状态：model_provider_accounts/model_bindings/model_labels 表和 ensure/list 接口已实现；SiteModelPolicy、站点化可见性、provider fallback/health 为规划。

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
  kokoro-site           消费 siteId（SiteModelPolicy 按 site 隔离可见性）。
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
model_provider_accounts
model_bindings
model_labels
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
GET  /model-bindings
```

resolve 查询路径（规划）：

```text
siteId + featureKey + labelKeys + user/team entitlement
  -> available model bindings
  -> priority / fallback
  -> transportKind
  -> gatewayModelName 或 direct adapter
```

```text
幂等  provider-accounts/ensure、model-bindings/ensure 按业务 key 幂等。
约束  litellm binding 必须有 gatewayModelName；direct binding 不强制。
```

## Admin 管理

```text
basePath  /admin/model（resources 以 manifest 为准）
resources provider accounts / model bindings / model labels / health status
          （后续 site model policies / provider fallback order / health check logs）
权限 key  model.provider.manage（细分 read/write 规划中）
操作      provider 账号增改、binding 增改、label 维护、健康状态查看。
审计      provider/binding 变更审计（规划接入统一审计）。
```

后台查询默认带 siteId，仅 platform root admin 可跨站查询。

## 业务链路

```text
model-resolve     按 site policy + featureKey + entitlement 解析可用 binding 与 fallback。
litellm-mapping   transportKind=litellm 时 gatewayModelName -> LiteLLM model_name（见 kokoro-litellm.md）。
```

## 部署

```text
服务名   kokoro-model
端口     4221
env      DATABASE_URL_MODEL, KOKORO_MODEL_PORT, KOKORO_MODEL_BASE_URL, KOKORO_SITE_BASE_URL
多 Pod   权威状态在 MySQL，可多副本。
```

## 测试

```text
集成    同 featureKey 按 site policy 返回不同 model list；fallback provider 按 priority 生效。
反例    disabled provider 不参与 resolve；litellm binding 缺 gatewayModelName 报错；
        direct binding 不强制 gatewayModelName。
```

## 风险和边界

```text
不要把价格放进 model。model 最多给成本参考和能力标签，最终扣费规则在 kokoro-credit。
ProviderAccount 可平台复用，但模型可见性必须站点化（SiteModelPolicy）。
同名模型由 provider + modelName 区分；labelKey 只用于展示聚合，运行时必须解析到具体 binding。
```

## 后续任务

```text
P0  SiteModelPolicy 建表与站点化 resolve；litellm/direct binding 约束测试。
P1  provider fallback order；provider health check 与 logs。
P2  与 credit 的成本参考对账；quotaClass 落地。
```
