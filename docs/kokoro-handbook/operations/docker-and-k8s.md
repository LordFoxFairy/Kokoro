# Docker 与 Kubernetes

## 范围

本文约束所有 Kokoro 服务的本地 Docker Compose 编排与 K8s 生产部署形态。目标：从 Docker Compose 切到 K8s 不改业务代码，每个服务独立扩容，无进程内关键状态。

## 部署目标

所有核心服务都要支持：

- Docker 本地启动。
- Kubernetes 多副本。
- 稳定服务名（不写 Pod IP、不写 localhost）。
- 无进程内关键状态。
- `/healthz`。
- 可独立扩容。

## 服务清单

```text
kokoro-web      Next.js，公网入口。
kokoro-session  Bun/TS，内部或公网 API，提供 SSE。
kokoro-agent    Python worker，内部服务或 worker deployment。
kokoro-site     Fastify/TS，内部服务。
kokoro-user     Fastify/TS，内部服务。
kokoro-model    Fastify/TS，内部服务。
kokoro-credit   Fastify/TS，内部服务。
kokoro-payment  Fastify/TS，内部服务和 webhook endpoint。
kokoro-litellm  外部/独立 LiteLLM proxy。
```

## 基础设施

```text
MySQL           平台核心管理和账务。
Mongo           session、agent state、job、artifact。
Redis           live stream、队列、广播、限流。
Object Storage  文件产物。
```

当前不引入 PostgreSQL，避免数据库组合过重。存储边界见 [../technical/06-data-storage](../technical/06-data-storage.md)。

## 稳定服务名与端口

代码和配置不写死 Pod IP，内部调用不写 `localhost`。

```text
http://kokoro-site:4201
http://kokoro-user:4211
http://kokoro-model:4221
http://kokoro-credit:4231
http://kokoro-payment:4241
http://kokoro-session:3001
http://kokoro-web:3000
```

K8s 同 namespace 使用同样短名。跨 namespace 由部署层覆盖为完整 DNS：

```text
http://kokoro-user.kokoro-platform.svc.cluster.local:4211
```

统一 base URL 环境变量（业务代码只读 base URL，不判断自己跑在 Docker 还是 K8s）：

```text
KOKORO_SITE_BASE_URL
KOKORO_USER_BASE_URL
KOKORO_MODEL_BASE_URL
KOKORO_CREDIT_BASE_URL
KOKORO_PAYMENT_BASE_URL
```

## Docker Compose（本地编排）

基础设施由根 `docker-compose.yml` 提供，平台服务由覆盖文件提供：

```bash
docker compose -f docker-compose.yml -f deploy/docker-compose.services.yml up --build
```

启动：`mysql` / `kokoro-site` / `kokoro-user` / `kokoro-model` / `kokoro-credit` / `kokoro-payment`。

第一阶段镜像使用 workspace 依赖和 `tsx` 入口，和当前 TS 源码结构一致。后续压缩镜像体积再切 `tsc` build + `node dist`，但不牺牲子仓自治和 package exports 清晰度。

session / agent / web 的本地启动见 [local-development](local-development.md)。

## Kubernetes（生产）

`deploy/k8s/platform-services.example.yaml` 是部署样例，不是生产机密文件。生产 Secret、Ingress、HPA、镜像 tag 和资源限额由环境仓或 GitOps 仓维护。

默认形态（每个平台服务 replicas=2 + ClusterIP）：

```text
Deployment/kokoro-site     replicas=2    Service/kokoro-site     ClusterIP
Deployment/kokoro-user     replicas=2    Service/kokoro-user     ClusterIP
Deployment/kokoro-model    replicas=2    Service/kokoro-model    ClusterIP
Deployment/kokoro-credit   replicas=2    Service/kokoro-credit   ClusterIP
Deployment/kokoro-payment  replicas=2    Service/kokoro-payment  ClusterIP
```

K8s 原则：

- 内部服务用 ClusterIP，默认不暴露公网。
- 公网入口放在 `kokoro-web` / admin / API gateway / ingress 层。
- payment webhook 可以单独 ingress（与主入口隔离，便于按 provider 限流和审计）。
- agent worker 可以按队列深度扩容（worker deployment，不是请求型服务）。
- credit / payment 关键写操作必须幂等。
- session SSE 要考虑 sticky 或通过 DB + live bus 解耦，不依赖单 Pod 内存保持连接状态。

每个 Pod 必须：

- 监听 `0.0.0.0`。
- 暴露 `/healthz`，供 readiness/liveness probe 使用。
- 优雅关闭：先停止接收请求，再关闭 Prisma/DB 连接。

## 数据库

第一阶段使用一个 MySQL database：`kokoro`。

```text
DATABASE_URL_SITE
DATABASE_URL_USER
DATABASE_URL_MODEL
DATABASE_URL_CREDIT
DATABASE_URL_PAYMENT
```

四个 env 可指向同一个库，也可在部署层拆库。拆库不改变模块领域边界。表结构仍由各自 Prisma migration 管理。生产不使用 root 账号，每个模块用受限数据库账号。

## 多 Pod 红线

```text
不用 InMemory 存关键业务状态。
不把积分余额放进 Redis。
不把 payment event 处理状态放进进程内存。
不让 agent run 只存在单进程。
不让 session 历史依赖 Redis 保留时长。
不在服务间调用里写 localhost。
不把支付网关、LiteLLM、Strapi 这类成熟系统从 0 复制一遍。
```

数据一致性依赖 MySQL 事务、唯一索引和幂等 key；需要异步任务时用队列 + 数据库状态机，不用单进程定时器承载关键状态。

## 质量门禁

修改部署或子仓公共能力后至少运行：

```bash
pnpm run test:platform
pnpm typecheck
pnpm test
pnpm lint
docker compose -f docker-compose.yml -f deploy/docker-compose.services.yml config
```

涉及 Prisma schema、repository 或 HTTP API 时继续运行：

```bash
pnpm test:integration
```

完整测试分层见 [testing-checklist](testing-checklist.md)。
