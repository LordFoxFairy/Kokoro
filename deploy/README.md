# Kokoro 阶段 1 部署

阶段 1 的部署闭环只有三个子仓库；Agent 执行面是可选 profile：

```text
kokoro Web → kokoro-bff/modules/chat → kokoro-agent HTTP ingress → worker
                                      ├─ PostgreSQL：持久化真源
                                      └─ Redis：stream / queue / lease / wakeup / cache
```

Web 不连接数据库，BFF 不直连 Agent 的数据库或 Redis。Chat 不再拆成独立 Session/Chat 服务，Gateway
也不在部署路径中。

## 组件选择

阶段 1 只启动两个 stateful 基础设施：

- **PostgreSQL 17**：Agent checkpoint、RunLedger、Chat execution facts，以及后续各业务 owner 自己的 SQL schema。
- **Redis 7**：worker stream、队列、租约、心跳、wakeup、短缓存和限流；Redis 丢失后从 PostgreSQL 恢复，不能作为长期真源。

不启动 MySQL、MongoDB、独立 Session 或 Gateway。MinIO、LiteLLM、Agent 也不属于 Web+BFF 最小启动的必需依赖；对象存储和模型 provider
以后按业务能力以独立 endpoint/secret 接入。

阶段 2 的正式业务仓库不由 Root Compose 拼装。它们各自维护 PostgreSQL/Redis adapter、迁移、Docker 和 CI，
由 BFF 按 Root contract 接入：`kokoro-iam`、`kokoro-system`、`kokoro-model`、`kokoro-billing`、
`kokoro-capability`、`kokoro-storage`、`kokoro-scheduler`。Root 的 Phase 1 Compose 只启动 Web、BFF、Agent
和本地 PostgreSQL/Redis，不复制这些业务仓的实现或数据库 schema。

## 一键起栈

前置：Docker Compose v2、`curl`。Root 不 vendoring 任何独立子仓源码；从全新 Root checkout
开始时，先用下面的 additive bootstrap 准备同目录的正式仓库：

```bash
bash deploy/clone-active-repositories.sh
```

它只会 clone 缺失的正式仓库，并校验现有目录的 Git root 与 `origin`；不会 reset、删除或覆盖本地改动。
`kokoro-agent` 使用 Root 已声明的 gitlink 初始化，其他正式仓库保持独立 Git 仓库。

```bash
cp deploy/.env.phase1.example deploy/.env.phase1.local
# 编辑 deploy/.env.phase1.local，至少替换 CHANGE_ME_postgres_password 和 CHANGE_ME_bff_shared_secret
bash deploy/provision-phase1.sh deploy/.env.phase1.local
```

默认启动内容（fast profile）：

- `postgres`：本地 5432，卷 `kokoro-phase1-postgres`
- `redis`：本地 6379，卷 `kokoro-phase1-redis`
- `kokoro-bff`：4300，`KOKORO_BFF_MODE=mock`
- `kokoro-app`：3000，阶段 1 preview auth

完整执行 profile（显式开启）额外启动：

- `kokoro-agent-http`：4401，BFF 唯一 Agent 业务入口
- `kokoro-agent`：Redis worker，执行实际 Agent loop

```bash
# Web+BFF 最小启动，不启动 Agent
docker compose --env-file deploy/.env.phase1.local -p kokoro-phase1 \
  -f deploy/docker-compose.phase1.yml up --build

# Web+BFF + Agent 完整执行
# 同时把 KOKORO_BFF_MODE=live、KOKORO_AGENT_ENABLED=1、
# KOKORO_AGENT_BASE_URL=http://kokoro-agent-http:4401 写入 env 文件。
# provision-phase1.sh 会在 live 模式启动应用前自动执行 BFF schema migration。
docker compose --env-file deploy/.env.phase1.local -p kokoro-phase1 \
  -f deploy/docker-compose.phase1.yml --profile agent up --build
```

本地访问：

```text
http://dev.kokoro.localhost:3000/
http://127.0.0.1:4300/healthz
```

停止：

```bash
docker compose --env-file deploy/.env.phase1.local -p kokoro-phase1 \
  -f deploy/docker-compose.phase1.yml down
```

## 生产配置

生产复制同一模板为 `deploy/.env.phase1.prod`，不改变量结构，只填生产值。生产可以把
`KOKORO_AGENT_DATABASE_URL` 和 `KOKORO_REDIS_URL` 指向托管 PostgreSQL/Redis；这时可从
`deploy/docker-compose.phase1.yml` 移除对应本地 stateful service，但应用契约不变。

生产按需选择两个维度：

1. **Agent**：不需要执行任务时保持 `KOKORO_AGENT_ENABLED=0`，只部署 Web+BFF；需要执行时
   同时部署 `kokoro-agent-http` 与 `kokoro-agent`，并设置 `KOKORO_AGENT_ENABLED=1` 和
   `KOKORO_AGENT_BASE_URL`。
2. **LiteLLM**：它是外部 OpenAI-compatible gateway，不属于 `kokoro-model` 或
   `kokoro-agent` 必需进程。只有选择 Model 的 `litellm` transport 时，才在 Agent 环境设置
   `KOKORO_LITELLM_ENABLED=1`、`KOKORO_LITELLM_BASE_URL` 和 `KOKORO_LITELLM_API_KEY`；
   直接使用 OpenAI-compatible 或 Anthropic 时保持关闭。

`kokoro-model` 始终可以独立启动并提供目录/解析；它不会探活、调用或拉起 LiteLLM。Model
目录中 `transport=litellm` 只是路由元数据，是否可执行由部署的 Agent/provider profile 决定。

`KOKORO_DOMAIN` 是当前站点域名，例如 `kokoro.miaokit.cloud`。它只由服务端读取，用于标准
`Forwarded` 和跨服务上下文；浏览器不携带自定义 `X-Domain` 作为信任依据。

生产 Web、BFF、Agent 分别使用各自仓库的生产 Dockerfile：

```bash
docker build -t ghcr.io/LordFoxFairy/kokoro-app:TAG ./kokoro
docker build -t ghcr.io/LordFoxFairy/kokoro-bff:TAG ./kokoro-bff
docker build -t ghcr.io/LordFoxFairy/kokoro-agent:TAG ./kokoro-agent
```

正式发布由各子仓自己的 GitHub tag workflow 触发；普通 push 不发布镜像。Cloudflare 直连 Web 时只
替换 Web deployment target，BFF/Agent 仍按内部 service endpoint 和同一份 v1 contract 对接。

## 契约与门禁

每个子仓独立闭环，不通过共享源码、共享数据库或跨仓 import：

```bash
(cd kokoro-agent && uv run ruff check . && uv run pyright && uv run pytest)
(cd kokoro-bff && pnpm check)
(cd kokoro && pnpm check)
```

根仓只维护 `contract/` 的版本化 API/AIP 索引、[storage-baseline-v1](../contract/spec/storage-baseline-v1.md)
和验收文档。跨仓联调交换 contract fixture、兼容性结果和发布元数据。

## 已移除的历史入口

旧的双 Compose 编排、旧 k8s manifests、旧全栈 provisioning、旧 workspace 配置，以及依赖
MySQL/Mongo/Session/Platform 的验证脚本已从本机活动工作区和本机归档目录清除；GitHub 历史仓库
仍以 archived 状态保留提交历史。它们不是开发、CI 或生产入口。

后续接入阶段 2 业务仓时，必须由各自仓库完成 PostgreSQL adapter、Redis adapter、迁移、测试和 Docker/CI 闭环，
再接入新的业务 BFF contract；不要把旧组件重新接回阶段 1。
