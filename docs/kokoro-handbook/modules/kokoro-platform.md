# kokoro-platform 技术方案

## 定位

kokoro-platform 不是业务服务，而是平台子仓集合的管理仓库。它负责统一注册、部署样例、质量门禁和文档；具体业务权威落在各子仓。

子仓多为规划或部分实现：site/user/model 已有最小表和接口，credit/payment 站点化改造仍在路上。本文件按"已实现 / 规划"如实标注。

## 业务职责

owns：

```text
子仓注册与部署样例（docker compose / k8s 服务名端口）。
跨子仓统一约定（单 MySQL database、表前缀、服务名端口、env 命名）。
质量门禁（typecheck / test / lint / compose config）。
平台文档。
```

does not own：

```text
任何子仓的领域逻辑（site/user/model/credit/payment 各自权威）。
agent/session/web 运行时（属三主运行时仓库）。
LiteLLM 网关运行态（kokoro-litellm 只做接入目录）。
```

## 上游和下游

```text
平台仓不在请求链路上。它定义子仓之间的调用拓扑：

入口（web/admin/gateway）
  -> kokoro-site 解析 SiteContext
  -> 注入 siteId header
  -> 下游 user/model/credit/payment 只消费 siteId
```

子仓服务调用关系见 [07-service-communication](../technical/07-service-communication.md)。

## 核心对象

子仓清单：

```text
kokoro-site          站点、域名、应用开关、策略、品牌、SEO；SiteContext 解析权威。
kokoro-user          用户、团队、成员、角色、邀请、服务账号、审计。
kokoro-model         provider account、model binding、model label、可见性和兜底。
kokoro-credit        积分账户、冻结、账本、usage、pricing rule、权益和扣费。
kokoro-payment       plan、order、subscription、payment event、refund。
kokoro-litellm       LiteLLM 网关配置和部署接入（external gateway，非业务权威）。
kokoro-platform-kit  response、amount、admin manifest schema、HTTP server 等无业务状态工具。
```

每个业务子仓统一四层：

```text
src/domain          实体、值对象、领域错误、repository interface。
src/application     用例编排，只依赖 domain。
src/infrastructure  Prisma、第三方 SDK、provider adapter。
src/interfaces      HTTP、admin manifest、未来 worker/RPC adapter。
src/config          env schema 和配置解析。
```

## 数据模型

MySQL：

```text
早期共用一个 database：kokoro。
每个子仓拥有自己的 Prisma schema、migration 和表名前缀：
  site_*    kokoro-site
  user_*    kokoro-user（users/teams/memberships/...，前缀以子仓 schema 为准）
  model_*   kokoro-model
  credit_*  kokoro-credit
  payment_* kokoro-payment
后续拆库只是部署拓扑变化，不改变领域边界。
```

其它存储：

```text
Mongo：后续 artifact、job result、创作内容、非结构化大 JSON 状态。
Redis：实时流、队列、短租约（不作长期真源）。
PostgreSQL：当前不引入，避免三套数据库同时维护。
对象存储：后续产物存储。
外部系统：LiteLLM（gateway）、支付 provider。
```

存储边界细则见 [ADR-005 MySQL 与 Mongo 的数据边界](../decisions/ADR-005-mysql-and-mongo.md)。

## API / RPC / Events

平台仓本身不提供运行时 API。统一约定如下。

服务名 + 端口：

```text
http://kokoro-site:4201
http://kokoro-user:4211
http://kokoro-model:4221
http://kokoro-credit:4231
http://kokoro-payment:4241
```

base url env（业务代码禁止写死 localhost）：

```text
KOKORO_SITE_BASE_URL
KOKORO_USER_BASE_URL
KOKORO_MODEL_BASE_URL
KOKORO_CREDIT_BASE_URL
KOKORO_PAYMENT_BASE_URL
```

SiteContext 解析（入口层调用 kokoro-site）：

```text
host -> siteId/siteKey/appKey/surface/defaultLocale/timezone
业务子仓只消费 siteId，不自己解析 host。
```

## Admin 管理

```text
每个子仓提供 admin manifest + 管理 API + permission key + resource/action 声明。
kokoro-web/admin 统一渲染壳子：导航、列表、表单、详情、审计页。
复杂模块允许自定义页面 adapter。
admin manifest schema 由 kokoro-platform-kit 提供。
```

后台查询默认带 siteId，仅 platform root admin 可跨站查询。

## 业务链路

```text
site-resolution        入口解析 SiteContext，下游消费 siteId。
payment-to-credit      支付成功后由 payment 调 credit grant。
credit-reserve-commit  扣费闭环（见 credit）。
```

参见 [credit-reserve-commit-refund](../business-flows/credit-reserve-commit-refund.md)。

## 部署

```text
服务名   见上方稳定服务名清单。
端口     site:4201 / user:4211 / model:4221 / credit:4231 / payment:4241。
env      每个子仓自带 DATABASE_URL_<NAME> + KOKORO_<NAME>_PORT + KOKORO_<NAME>_BASE_URL，
         并按依赖引入上游 base url（多数需 KOKORO_SITE_BASE_URL）。
多 Pod   子仓权威状态在 MySQL，可多副本；不依赖进程内状态做权威。
门禁     Docker Compose 与 k8s 均用稳定服务名，compose config 必须可解析。
```

## 测试

```bash
pnpm typecheck
pnpm test
pnpm lint
docker compose -f docker-compose.yml -f deploy/docker-compose.services.yml config
```

涉及 Prisma schema、repository 或 HTTP API 时继续运行：

```bash
pnpm test:integration
```

## kokoro-platform-kit 概述

无业务状态的基础工具包。服务子仓，禁止成为隐藏业务模块。

```text
可以拥有  admin manifest schema、统一 HTTP response/error、startHttpServer helper、
          amount/credit micros 解析、request id helper、SiteContext 类型与 header parse/serialize。
禁止拥有  业务 service、Prisma client、数据库 schema、领域逻辑、远程 client 复杂实现、业务常量大全。
当前能力  src/admin/manifest-schema.ts、src/domain/amount.ts、
          src/http/responses.ts、src/http/start-server.ts。
依赖方向  子仓 -> kit 允许；kit -> 子仓禁止。
验收      每个导出都不查库、不调业务服务、不持业务状态、不决定业务策略。
```

## 风险和边界

红线：

```text
不建 kokoro-contracts。
不使用 ports 目录命名。
不跨子仓直接读写对方表。
不把业务逻辑塞进 kokoro-platform。
不把业务逻辑塞进 kokoro-platform-kit。
不修改 LiteLLM 源码。
```

边界提醒：价格在 credit、卖什么在 payment、模型能力在 model、身份在 user、站点事实在 site。任何一处越权混表都是技术债来源。详见 [ADR-001 站点边界](../decisions/ADR-001-site-boundary.md)。

## 后续任务

```text
P0  各子仓站点化改造（user/model/payment 加 siteId）；compose/k8s 服务名端口跑通。
P1  admin manifest 壳子统一接入 kokoro-web/admin；platform-kit 补 SiteContext header helper。
P2  拆库部署拓扑评估；Mongo/对象存储接入 artifact 链路。
```
