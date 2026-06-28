# 部署

本文定义全系统的服务清单、基础设施、本地 Compose、Kubernetes 多副本形态、环境变量和多 Pod 红线。运行时三仓内部架构见 [03-agent-architecture](03-agent-architecture.md)、[04-session-architecture](04-session-architecture.md)、[05-web-architecture](05-web-architecture.md)；平台子仓约定见 [02-platform-architecture](02-platform-architecture.md)。

## 部署目标

所有核心服务都要支持：

```text
Docker 本地启动。
Kubernetes 多副本。
稳定服务名。
无进程内关键状态。
/healthz readiness/liveness probe。
可独立扩容。
优雅关闭。
```

## 服务清单

```text
kokoro-web      Next.js，公网入口。
kokoro-session  Bun/TS，内部或公网 API，提供 SSE。
kokoro-agent    Python worker，worker deployment，按队列扩容。
kokoro-site     Fastify/TS，内部服务。
kokoro-user     Fastify/TS，内部服务。
kokoro-model    Fastify/TS，内部服务。
kokoro-credit   Fastify/TS，内部服务。
kokoro-payment  Fastify/TS，内部服务 + 支付 webhook endpoint。
kokoro-litellm  外部/独立 LiteLLM proxy（不改源码）。
```

## 基础设施

```text
MySQL          平台核心管理和账务（单 database: kokoro）。
Mongo          session、agent state、job、artifact 的长期真源。
Redis          run queue、raw event stream、live fanout、短租约、限流（传输非长期库）。
对象存储        文件产物。
```

存储边界细则见 [06-data-storage](06-data-storage.md)。Redis 只承载传输与短期锁，恢复以 Mongo 和 MySQL 为准。

## Docker Compose（本地）

本地基础设施由根 `docker-compose.yml` 提供 MySQL；平台服务由覆盖文件提供：

```bash
docker compose -f docker-compose.yml -f deploy/docker-compose.services.yml up --build
```

会启动 `mysql` + `kokoro-site/user/model/credit/payment`。运行时三仓（web/session/agent）和 Mongo/Redis 视调试目标按需启动。本地调试顺序：

```text
platform healthz
session health
agent fake model
web simulator
真实 provider
```

## Kubernetes（多副本）

```text
内部平台服务         ClusterIP，replicas>=2，默认不暴露公网。
kokoro-web           公网入口，走 Ingress。
kokoro-session       提供 SSE；多副本时 sticky 或通过 Mongo + Redis live bus 解耦。
kokoro-agent         worker deployment，按 run queue 深度扩容。
payment webhook      可单独 Ingress，与普通公网入口隔离。
```

跨 namespace 时 base url 由部署层覆盖为完整 Service DNS。生产 Secret、Ingress、HPA、镜像 tag、资源限额由环境仓或 GitOps 维护，不进样例文件。

## 环境变量

平台 base url（业务代码禁止写死 localhost）：

```text
KOKORO_SITE_BASE_URL
KOKORO_USER_BASE_URL
KOKORO_MODEL_BASE_URL
KOKORO_CREDIT_BASE_URL
KOKORO_PAYMENT_BASE_URL
```

每个平台子仓另带自身配置：

```text
DATABASE_URL_<NAME>      （SITE/USER/MODEL/CREDIT/PAYMENT，可同库可拆库）
KOKORO_<NAME>_PORT
KOKORO_<NAME>_BASE_URL
```

运行时：

```text
NEXT_PUBLIC_KOKORO_SESSION_BASE_URL   web 浏览器端访问 session 的入口。
KOKORO_STREAM_BACKEND                 实时流后端选择。
KOKORO_REDIS_URL                      run queue / event stream / live fanout / lock。
KOKORO_MESSAGE_STORE_BACKEND          session 消息存储后端。
KOKORO_MESSAGE_STORE_MONGO_URL        session 消息 Mongo 连接。
KOKORO_AGENT_RUN_STATE_BACKEND        agent run 状态后端。
```

端口固定：site:4201 / user:4211 / model:4221 / credit:4231 / payment:4241。其余端口以各子仓 `.env.example` 为准，缺失待补，不编造。

## 多 Pod 红线

```text
不用 InMemory 存关键业务状态（run、锁、余额、幂等、payment event 处理状态）。
不把积分余额放进 Redis；账务只在 MySQL。
credit/payment 关键写操作必须幂等（唯一索引 + 幂等 key）。
不让 agent run 只存在单进程；run 状态可被任一 worker 恢复。
不让 session 历史依赖 Redis 保留时长；长期真源在 Mongo。
所有服务监听 0.0.0.0，暴露 /healthz。
关闭进程时先停止接收请求，再关闭 DB/Redis 连接（优雅关闭）。
```
