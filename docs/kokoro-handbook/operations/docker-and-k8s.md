# Docker 与 Kubernetes

状态：**历史 deployment plane 参考**，2026-08-22。当前 Root 只提供
[`deploy/docker-compose.phase1.yml`](../../../deploy/docker-compose.phase1.yml) 的 Web/BFF/Agent + PostgreSQL/Redis
入口；旧 k8s manifests 和全栈 Compose 已从当前工作区移除并仅保留在 Git 历史。本文保留服务发现、endpoint、secret、volume、sandbox
adapter、资源与 readiness/drain；它不定义产品 Feature、GA Agent、Skill、graph 或 Session 状态。GA 的目标编排以
[36 GA 整体 Agent 技术方案](../technical/36-ga-final-agent-technical-plan.md) 和
[37 App、Feature 与 Studio 架构](../technical/37-product-experience-agent-studio-architecture.md) 为准。

## 范围

当前部署入口只约束阶段 1 三仓；阶段 2 业务仓的 Docker/Kubernetes 形态由各自仓库和部署环境维护，Root
不再拼装业务服务或发布 Kubernetes manifests。

## 配置边界：三层不互相越权

| 层 | 由谁写入 | 可以配置 | 明确不可以配置 |
|---|---|---|---|
| deployment config | Compose/Kubernetes/env/secret/GitOps | service DNS、PostgreSQL/Redis、model/provider handle、sandbox profile、S3Workspace endpoint/bucket、CA/Storage public client、观测与资源/ready/drain。 | Workflow、Agent、member/edge/mode、Skill runtime、prompt、Session Agent。 |
| GA catalog | GA control plane / normal deployment rollout | `FeatureKey -> Workflow`、Agent、default Skill、Tool/Model/HITL/sandbox policy、execution ceiling。 | endpoint/secret、Pod IP、bucket key、Session selection、用户/会话 Skill CRUD。 |
| external owner config | Capability / Storage / Studio / Billing 各自 public service | user/session Skill path 与 CRUD、Asset/Artifact lifecycle、Job/provider policy、价格/余额/结算。 | GA checkpoint、workbench、Agent graph、Session runtime recipe。 |

部署变量只让 GA **连接**到已定义的 adapter；GA catalog 才决定“一个 Feature 如何组装 Agent”。例如 MinIO 的
endpoint/bucket 只启用可选 `S3Workspace`，不会让任何 Session 变成 Music Agent，也不会新增 Tool、Skill 或 member。

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
kokoro              Next.js Web，公网入口。
kokoro-bff          Web-facing BFF，Chat/业务编排、鉴权、幂等、SSE。
kokoro-agent        Python worker，Run 执行、HITL、恢复和事件投影。
kokoro-iam          Goal 2 身份、认证、授权和审计 owner。
kokoro-system       Goal 2 Site、Workspace、Runtime Manifest owner。
kokoro-model        Goal 2 Model Catalog/Provider owner。
kokoro-billing      Goal 2 Payment/Subscription/Checkout/Refund/Credit/Ledger owner。
kokoro-capability   Goal 2 Skill/MCP Connector control-plane owner。
kokoro-storage      Goal 2 ObjectStore 引用、Asset/Artifact metadata owner。
kokoro-scheduler    Goal 2 通用调度、lease、retry、misfire owner。
```

## 基础设施

```text
PostgreSQL      Agent durable facts 与阶段 2 各业务 owner 的业务事实。
Redis           Agent transport、队列、lease、wakeup、cache 和限流，不作长期真源。
Object Storage  Storage bytes/Artifact 与 GA optional S3Workspace 使用 S3-compatible 接口，owner/lifecycle 分离。
```

当前阶段不新增 MySQL/Mongo 运行时依赖。存储边界见 [../technical/06-data-storage](../technical/06-data-storage.md)。

## 稳定服务名与端口

代码和配置不写死 Pod IP，内部调用不写 `localhost`。

```text
http://kokoro-bff:4300
http://kokoro-web:3000
kokoro-agent              worker，无 HTTP service
```

Goal 2 服务名、端口和跨 namespace DNS 由各正式仓库的部署 contract 定义；Root 不在这里复制一份。

阶段 1 的统一 base URL 环境变量：

```text
KOKORO_BFF_BASE_URL
KOKORO_AGENT_DATABASE_URL
KOKORO_REDIS_URL
```

## Docker Compose（当前本地编排）

Root 当前只有阶段 1 三仓入口：

```bash
cp deploy/.env.phase1.example deploy/.env.phase1.local
bash deploy/provision-phase1.sh deploy/.env.phase1.local
```

启动：`postgres` / `redis` / `kokoro-bff` / `kokoro-agent` / `kokoro-web`。具体环境变量和停止命令见
[`deploy/README.md`](../../../deploy/README.md)。

第一阶段镜像使用 workspace 依赖和 `tsx` 入口，和当前 TS 源码结构一致。后续压缩镜像体积再切 `tsc` build + `node dist`，但不牺牲子仓自治和 package exports 清晰度。

session / agent / web 的本地启动见 [local-development](local-development.md)。

## Kubernetes（生产）

Root 不再发布 Kubernetes manifests；旧 `deploy/k8s/` 已移至 Root 外归档。阶段 2 正式业务仓的 Secret、Ingress、
HPA、镜像 tag、资源限额和 rollout 由各 owner 仓库及部署/GitOps 环境维护。

当前 Root 的 Kubernetes 默认形态：

```text
Root Phase 1：由部署环境提供 Web/BFF/Agent workload 与 PostgreSQL/Redis；Root 不生成 k8s 资源。
Goal 2 owners：各自仓库提供 workload/image/config contract，由目标环境组合和发布。
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

## GA Sandbox Workspace：仅部署注入，不参与产品编排

Compose/Kubernetes 只为 GA 提供 sandbox backend、可选 `S3Workspace` adapter、secret handle 和资源限额；它们
不决定 Workflow、Agent、成员、mode、Skill、图或 Session 行为。Session 从不挂载、直读或清理
GA workspace；用户可见文件统一由 Storage Artifact lifecycle 交付。

```text
GA thread workspace root = {RuntimeNamespace}:{session_id}
GA task workspace root   = {RuntimeNamespace}:{session_id}:{task_id}
Session                  = messages / SSE / Artifact reference only
```

```text
本地开发 / Docker Compose：
  agent 容器使用 local/state workspace；若 local_shell/docker sandbox 需要文件卷，只挂给 agent 与 sandbox runner。
  session/web 不挂 workspace volume。

Kubernetes 多 Pod：
  `ephemeral_ok` Feature 可用 local sandbox；需要跨 pod/sandbox 恢复的 `durable_required` Feature
  必须由 GA WorkbenchPersistence 选择持久本地卷或 MinIO-first S3Workspace，并在 mount commit 后才 ready。
  当前 V1 `S3Archiver` 只是 best-effort archive，不提供 target recovery；不以 Session/Agent 共享 RWX PVC 作为 Agent 运行语义。

Docker / E2B sandbox：
  runner 只接收该 thread 或 task 的 GA workspace；task workbench 与 parent thread workbench 隔离。
  container/e2b handle 归 GA RunLedger；HITL resume 由 GA 恢复。
```

`S3Workspace` 使用 MinIO-first 的 S3-compatible 配置：`endpoint`、`bucket`、`region`、`force_path_style`。
AWS S3、Ceph RGW、R2 等 provider 通过部署配置切换；provider 私有扩展留在 sandbox/ObjectStore adapter。
归档失败不改变本地 sandbox write 的结果，也不伪装为 Storage Artifact 失败。

目标配置样例是 [`deploy/ga-workbench.example.yaml`](../../../deploy/ga-workbench.example.yaml)：旧
`storage.yaml` / `storage.s3.yaml` 已随历史 Compose 一起归档。GA-only `workspace_prefix` 与 `credential_handle`
仍由部署环境注入；工作负载凭据只可访问该 prefix，Storage Artifact 的 bucket/prefix、扫描和 retention 不随此配置产生权限。

## 资产面（skills/personas，ADR-011）

```text
单节点 / 单机 docker：
  默认档零配置：KOKORO_SKILLS_DIR / KOKORO_PERSONAS_DIR 指向本地目录（或镜像内置）。

多 Pod：
  GA 默认 Skill/persona 资源可随镜像或由 S3-compatible deployment asset source 提供；改默认资源后按普通 GA
  deployment 滚动更新。user/session 动态 Skill 不走这个 assets source，仍由 GA `find_skills/load_skill` 经
  Capability/Storage public contract 获取。
```

## 数据库

阶段 1 使用 PostgreSQL database；阶段 2 各 owner 维护自己的 PostgreSQL schema。

```text
KOKORO_AGENT_DATABASE_URL
DATABASE_URL_<OWNER>
```

各 owner 可在部署层拆库。拆库不改变模块领域边界。表结构由各自 migration 管理；生产不使用超级用户，每个模块用受限数据库账号。

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

数据一致性依赖 PostgreSQL 事务、唯一索引和幂等 key；需要异步任务时用队列 + 数据库状态机，不用单进程定时器承载关键状态。

## 质量门禁

修改 Root 部署入口或跨仓公共能力后至少运行：

```bash
pnpm contract:format
pnpm contract:lint
pnpm contract:check
python3 scripts/goal2/mock_cross_repository_closure.py
python3 scripts/verify-backend-design.py
python3 scripts/verify-repository-topology.py
KOKORO_ENV_FILE="$PWD/deploy/.env.phase1.example" docker compose --env-file deploy/.env.phase1.example -f deploy/docker-compose.phase1.yml config
```

涉及某个正式业务仓库时，再运行该仓库自己的 typecheck/lint/test/build 和 integration gate：

```bash
(cd kokoro-billing && pnpm check)
(cd kokoro-scheduler && go test ./...)
```

完整测试分层见 [testing-checklist](testing-checklist.md)。
