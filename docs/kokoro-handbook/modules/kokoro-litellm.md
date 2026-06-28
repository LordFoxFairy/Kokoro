# kokoro-litellm 技术方案

## 定位

kokoro-litellm 是 LiteLLM 网关的部署和配置接入目录，不是 Kokoro 自己的模型业务权威。

它在平台 registry 中是外部网关：status=external，kind=gateway。它只回答"LiteLLM 怎么部署、virtual key 怎么配、与 kokoro-model 怎么映射"。

实现状态：接入目录与映射约定为规划/外部依赖；Kokoro 侧只保存映射关系和审计状态，不持有 LiteLLM 运行态。

## 业务职责

owns：

```text
LiteLLM proxy 配置样例。
healthcheck 脚本。
docker compose 样例。
与 kokoro-model 的映射约定。
```

does not own：

```text
model catalog / model label（kokoro-model）。
provider account 业务状态（kokoro-model）。
credit ledger（kokoro-credit）。
user/team 权限（kokoro-user）。
```

## 上游和下游

```text
上游（经 LiteLLM 转发的调用方）：
  kokoro-agent / 运行时   transportKind=litellm 的模型请求走 LiteLLM proxy。

映射来源：
  kokoro-model            提供 gatewayModelName，运行时据此命中 LiteLLM model_name。

LiteLLM 不是 Kokoro 子仓权威，只作为外部 gateway 被消费。
```

## 核心对象

职责切分：

```text
LiteLLM 负责
  provider 请求代理、virtual keys、rate limit、budget guard、
  部分 spend tracking、provider retry/fallback。

Kokoro 负责
  用户/站点权限、模型可见性、套餐权益、积分扣费、审计。
```

映射约定：

```text
kokoro-model 保存
  ProviderAccount / ModelBinding / ModelLabel / featureKey / labelKeys /
  transportKind / gatewayModelName。

当 transportKind = litellm 时
  ModelBinding.gatewayModelName -> LiteLLM model_name。
```

## 数据模型

```text
MySQL / Mongo / Redis / 对象存储：kokoro-litellm 自身不持有业务数据。
  Kokoro 侧的模型映射落在 kokoro-model（model_bindings.gatewayModelName）。
外部系统：LiteLLM proxy（config yaml、virtual keys、model aliases）。
```

## API / RPC / Events

```text
kokoro-litellm 不提供 Kokoro 业务 API。
对外暴露的是 LiteLLM proxy 自身的 OpenAI 兼容端点 + healthcheck。
配置入口：LiteLLM proxy / config yaml / virtual keys / model aliases / callbacks(hooks，后续按需)。
```

## Admin 管理

```text
平台 registry 状态  status: external / kind: gateway。
无 Kokoro admin manifest（LiteLLM 自带管理面）。
Kokoro 侧管理落在 kokoro-model（binding 的 transportKind / gatewayModelName）。
权限 key  无独立权限；模型映射归 kokoro-model 权限。
```

## 业务链路

```text
litellm-mapping
  kokoro-model resolve -> transportKind=litellm
    -> gatewayModelName 命中 LiteLLM model_name
    -> LiteLLM 代理 provider 请求
    -> spend/budget 仅作护栏，最终账务回 kokoro-credit。
```

模型解析见 [kokoro-model](kokoro-model.md)；账本边界见 [kokoro-credit](kokoro-credit.md)。

## 部署

```text
服务名   kokoro-litellm（可独立部署，或作为外部服务由环境提供）
端口     待补（LiteLLM proxy 默认端口，以部署样例为准）
env      待补（LiteLLM 配置以其 config yaml / virtual keys 为准）
多 Pod   网关无 Kokoro 业务状态；spend/budget 状态在 LiteLLM 侧。
```

## 测试

```text
healthcheck  LiteLLM proxy 存活探测脚本。
集成        transportKind=litellm 的 binding 能命中 LiteLLM model_name。
门禁        compose 样例可 config 解析。
```

## 风险和边界

```text
不要修改 LiteLLM 源码，优先用 proxy / config yaml / virtual keys / model aliases / hooks。
不要把 LiteLLM 当成 Kokoro 的账本。
  spend/budget 可做护栏，最终用户积分、套餐权益和账务审计在 kokoro-credit。
```

## 后续任务

```text
P0  补部署样例端口与 env；healthcheck 脚本。
P1  LiteLLM virtual key 与 site/team 的映射策略；每 site/team budget guard。
P2  LiteLLM spend tracking 与 Kokoro usage record 对账；失败重试与 credit hold 一致性。
```
