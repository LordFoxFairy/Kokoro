# 平台架构

本文定义 `kokoro-platform` 子仓集合的架构、内部约定和红线。平台是业务核心域（site/user/model/credit/payment）的集合，不是运行时三仓。运行时执行链路见 [03-agent-architecture](03-agent-architecture.md)、[04-session-architecture](04-session-architecture.md)、[05-web-architecture](05-web-architecture.md)。

## 定位

`kokoro-platform` 是管理仓库，不是一个大业务服务。它负责子仓注册、部署样例、统一约定、质量门禁和文档；具体业务权威落在各子仓自己。

```text
kokoro-site          站点、域名、应用开关、策略、品牌、SEO；SiteContext 解析权威。
kokoro-user          用户、团队、成员、角色、邀请、服务账号、审计。
kokoro-model         provider account、model binding、model label、可见性和兜底。
kokoro-credit        积分账户、冻结、账本、usage、pricing rule、权益和扣费。
kokoro-payment       plan、order、subscription、payment event、refund。
kokoro-litellm       LiteLLM 网关配置和部署接入（external gateway，非业务权威）。
kokoro-platform-kit  response、amount、admin manifest schema、HTTP server 等无业务状态工具。
```

模块级技术方案见 [modules/kokoro-platform](../modules/kokoro-platform.md) 及各子仓模块文档。

## 子仓统一四层

每个业务子仓内部都按同一分层组织，便于跨子仓审查：

```text
src/domain          实体、值对象、领域错误、repository interface。
src/application     用例编排，只依赖 domain。
src/infrastructure  Prisma、第三方 SDK、provider adapter。
src/interfaces      HTTP、admin manifest、未来 worker/RPC adapter。
src/config          env schema 和配置解析。
```

## 单库多 schema

第一阶段使用一个 MySQL database：`kokoro`。每个子仓拥有自己的 Prisma schema、migration 和表名前缀，互不读写对方表：

```text
site_*     kokoro-site
user_*     kokoro-user
model_*    kokoro-model
credit_*   kokoro-credit
payment_*  kokoro-payment
```

每个子仓配置独立 `DATABASE_URL_<NAME>`，可以指向同一个库，也可以在未来部署层拆成不同库。拆库只是部署拓扑变化，不改变领域边界。

存储边界（MySQL 账务、Mongo 产物、Redis 传输）见 [06-data-storage](06-data-storage.md)。

## 稳定服务名和端口

代码和配置不写死 Pod IP，也不把内部服务调用写成 `localhost`。Docker Compose 和 Kubernetes 都使用稳定服务名：

```text
http://kokoro-site:4201
http://kokoro-user:4211
http://kokoro-model:4221
http://kokoro-credit:4231
http://kokoro-payment:4241
```

跨 namespace 时由部署层覆盖为完整 DNS（如 `http://kokoro-user.kokoro-platform.svc.cluster.local:4211`）。业务代码只读取 base url，不判断自己运行在 Docker 还是 Kubernetes：

```text
KOKORO_SITE_BASE_URL
KOKORO_USER_BASE_URL
KOKORO_MODEL_BASE_URL
KOKORO_CREDIT_BASE_URL
KOKORO_PAYMENT_BASE_URL
```

## SiteContext

入口层（web/admin/gateway）通过 `kokoro-site` 把 host 解析为站点上下文，再把 `siteId` 注入下游：

```text
host -> siteId/siteKey/appKey/surface/defaultLocale/timezone
入口解析 SiteContext -> 注入 siteId -> 下游 user/model/credit/payment 只消费 siteId
```

业务子仓只消费 `siteId`，不自己解析 host。`siteId` 是所有业务表和查询的第一隔离边界。详见 [09-security-permissions](09-security-permissions.md)。

## Admin 统一壳子

每个子仓声明 admin manifest + 管理 API + permission key + resource/action，`kokoro-web/admin` 统一渲染壳子：导航、列表、表单、详情、审计页；复杂模块允许自定义页面 adapter。

```text
admin manifest    资源、字段、动作声明（schema 由 kokoro-platform-kit 提供）。
permission key    按模块划分：site.* / user.* / credit.* / payment.* 等。
resource/action   后台对资源可执行的操作（read/write/adjust/...）。
```

后台查询默认带 `siteId`，仅 platform root admin 可跨站查询。

## kokoro-platform-kit

无业务状态的基础工具包，禁止成为隐藏业务模块：

```text
可以拥有  admin manifest schema、统一 HTTP response/error、startHttpServer helper、
          amount/credit micros 解析、request id helper、SiteContext 类型与 header parse/serialize。
禁止拥有  业务 service、Prisma client、数据库 schema、领域逻辑、业务常量大全。
依赖方向  子仓 -> kit 允许；kit -> 子仓禁止。
验收      每个导出都不查库、不调业务服务、不持业务状态、不决定业务策略。
```

## 与运行时三仓的边界

平台不在 SSE 实时链路上。`kokoro-session` 和 `kokoro-agent` 只通过稳定服务名的 HTTP API 调用平台能力（如解析 SiteContext、quote/hold/capture 积分、取模型 binding），不直接读平台表，平台也不参与 run 事件流。

```text
session/agent -> HTTP -> site/user/model/credit/payment
平台不订阅 Redis run queue，不写 session_events，不推 SSE。
```

服务间调用契约见 [07-service-communication](07-service-communication.md)。

## 红线

```text
不建 kokoro-contracts。
不使用 ports 目录命名。
不跨子仓直接读写对方表。
不把业务逻辑塞进 kokoro-platform 或 kokoro-platform-kit。
不修改 LiteLLM 源码（kokoro-litellm 只做接入目录）。
价格在 credit、卖什么在 payment、模型能力在 model、身份在 user、站点事实在 site。
```
