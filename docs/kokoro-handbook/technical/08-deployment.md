# 部署

> **阶段 1 当前裁决（2026-09-01）**：只部署 `kokoro` Web、`kokoro-bff` 和 `kokoro-agent` 三仓
> 闭环；Chat 属于 BFF 模块，不使用 Gateway 或独立 Session/Chat 仓库。运行时存储只采用
> PostgreSQL + Redis。本文下方的旧服务清单和 MySQL/Mongo Compose 仅保留为历史物理记录，
> 不得作为新部署模板；当前基线以 [storage-baseline-v1](../../../contract/spec/storage-baseline-v1.md)
> 与 `kokoro/docs/deployment.md` 为准。

> **状态：历史 V1 deployment 记录。**本文的三仓 runtime 引用、Session/Agent 共读 workspace、旧 service
> base URL 与资产 source 只保留现有物理基线。当前 target 的部署边界以
> [operations Docker/Kubernetes](../operations/docker-and-k8s.md) 与
> [36 GA 整体 Agent 技术方案](36-ga-final-agent-technical-plan.md) §9 为准：Compose/Kubernetes 只接入
> endpoint/secret/volume/sandbox/S3Workspace/readiness，GA catalog 才拥有 Feature/Agent，
> Session 不读取 GA workspace 或从部署配置获得 Agent/Skill/graph。

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
kokoro-session  Node/TS，内部或公网 API，提供 SSE。
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
MySQL          平台核心管理和账务；各 owner 的结构化元数据与生命周期事实。
Mongo          Session/Agent 运行态文档（checkpoint、memory、消息/事件 projection）。
Redis          run queue、raw event stream、live fanout、短租约、限流（传输非长期库）。
S3-compatible  Storage 的 Blob/Asset/Artifact bytes；默认部署为 Docker MinIO。
```

存储边界细则见 [06-data-storage](06-data-storage.md)。Redis 只承载传输与短期锁，恢复以各 owner 的 Mongo/MySQL 真相为准。
`kokoro-storage` 的 bytes 不进入 Mongo，而是通过统一 S3-compatible adapter 访问 MinIO、AWS S3 或 Ceph RGW。
Workspace 文件面的三档部署（单节点本地默认 / 共享卷 / e2b+对象存储）见 [ADR-009](../decisions/ADR-009-workspace-storage.md) 与 [operations/docker-and-k8s](../operations/docker-and-k8s.md)。

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
NEXT_PUBLIC_SESSION_BASE_URL          web 浏览器端访问 session 的入口（缺失即 fail-loud）。
KOKORO_WEB_ORIGIN                     session CORS 白名单（web 的浏览器 origin）；不配则
                                      浏览器跨源请求全拒（缺省仅 http://localhost:3000）。
KOKORO_AUTH_JWT_SECRET                session 鉴权（M2-P1）：未配置=直通模式（开发零配置）；
                                      配置后全路由强制 Bearer JWT（HS256，owner=sub）+ 属主裁权。
                                      web 侧 token 暂由 localStorage kokoro.auth.token 注入
                                      （platform 登录体系接入前的部署方通道）。
KOKORO_STREAM_BACKEND                 实时流后端选择。
KOKORO_REDIS_URL                      run queue / event stream / live fanout / lock。
KOKORO_MESSAGE_STORE_BACKEND          session 消息存储后端。
KOKORO_MESSAGE_STORE_MONGO_URL        session 消息 Mongo 连接。
KOKORO_MONGO_URL / KOKORO_MONGO_DB    agent 存储（checkpoint / ledger / 长期记忆）统一后端，唯一 mongo。
KOKORO_REDIS_URL（agent 复用上行）     agent 实时流传输，唯一 redis。
```

Workspace 与沙箱（ADR-009；全部可选，缺省=单节点 local 零配置）：

```text
KOKORO_WORKSPACE_ROOT                 local 档工作区根（默认 ./kokoro_workspace）。
KOKORO_WORKSPACE_CONFIG               存储形态 yaml（type: local|s3），session/agent 双侧共读。
KOKORO_WORKSPACE_S3_ACCESS_KEY/_SECRET_KEY   s3 档凭据（不进 yaml）。
KOKORO_DOCKER_IMAGE / KOKORO_DOCKER_TTL      docker 执行隔离档：镜像（选 docker 必填）/容器存活期。
KOKORO_E2B_API_KEY / _TEMPLATE / _TIMEOUT    e2b 云沙箱档（选 e2b 时 api_key 必填）。
KOKORO_CUSTOM_BACKEND / _CONFIG              BYO 自带沙箱（ADR-010）：pkg.module:factory + 自由参数 yaml。
```

资产源（ADR-011；缺省=env 目录档，零配置可用）：

```text
KOKORO_SKILLS_DIR / KOKORO_PERSONAS_DIR      local 档资产目录（不配 ASSETS_CONFIG 时生效）。
KOKORO_ASSETS_CONFIG                         资产源 yaml（type: local|s3）；配置后目录 env 失效。
KOKORO_ASSETS_S3_ACCESS_KEY/_SECRET_KEY      s3 档凭据（不进 yaml）。
```

统一配置树（ADR-010）：`KOKORO_AGENT_CONFIG` 指向按域分组的单一 yaml，优先级
**env > yaml > 内置默认**，凭据 env-only（写进 yaml fail-loud）。全部可用键与各部署
形态的照抄模板见仓根 `config/examples/`。

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
