# Kokoro Runtime Profiles v1

2026-09-08：System 合入分支采用 ADR-031 的单一 HTTP 模型目录/解析边界。
Root 只编排启动与验收；完整 System 状态见其 CURRENT/IMPLEMENTATION_PLAN，本文件不是运行通过证据。

## 组件边界

| 组件 | 启用条件 | 职责 |
|---|---|---|
| kokoro-system | 站点配置/模型目录或 Agent 执行需要时 | Sites、Workspaces、Products、Runtime Manifest、Model Catalog；不推理 |
| LiteLLM | 标准 Agent worker 执行时 | 外部网关；不拥有 System catalog、Billing ledger 或 Agent Run |
| kokoro-agent-http | BFF 提交/控制/读取执行时 | durable ingress，不执行 worker loop |
| kokoro-agent | 执行 profile | worker、恢复、运行事实；模型先经 System resolve |

旧 kokoro-model 不再作为独立运行依赖；checkout/remote 保留为历史源，不归档或删除。
System 的 model-catalog 不持有 provider 明文凭据，不拉起或探活 LiteLLM。

## local-fast：不执行模型

从各仓源码启动 Web/BFF；BFF 使用 live 模式及其独立 PostgreSQL 数据库、Redis 连接，
`KOKORO_AGENT_ENABLED=0`。本地只复用一套 PostgreSQL/Redis，不启动第二套容器。
需要站点或模型目录页面时另外源码启动 System；未配置 owner 不冒充 mock 成功。

## local-full：执行链路

1. 按 System README 从 fresh owner 数据库启动 `pnpm dev`，配置三种独立服务凭据。
2. BFF 设置 `KOKORO_SYSTEM_BASE_URL`、`KOKORO_INTERNAL_SECRET_BFF`；后者对应 System 的 BFF token。
3. Agent worker 设置以下配置，凭据仅放在被忽略的本地环境文件或 secret manager：

```dotenv
KOKORO_SYSTEM_BASE_URL=http://HOST:4240
KOKORO_INTERNAL_SECRET_AGENT=TOKEN
KOKORO_LITELLM_ENABLED=1
KOKORO_LITELLM_BASE_URL=https://HOST/v1
KOKORO_LITELLM_API_KEY=TOKEN
```

Agent token 对应 System 的 `KOKORO_SYSTEM_AGENT_SERVICE_TOKEN`，不复用 BFF/admin token。
System 返回的 opaque label/路由不包含 endpoint/key；缺少路由或凭据时失败关闭，没有本地默认模型选择。
完整执行同时启动 Agent HTTP ingress 和 worker；BFF 设置 `KOKORO_AGENT_ENABLED=1` 及 Agent ingress URL。
每个 owner 只访问自己的数据库；Redis System=2、BFF=8、Agent=9；原 Model DB3 保持空置。

## 生产与候选验证

System、BFF、Agent 使用各仓生产镜像；LiteLLM 由外部部署提供，不加入其镜像。
Root Phase1 compose 不新增 System/Model 容器，也不代表完整业务链已验收；容器只用于候选 smoke，开发仍从源码运行。
浏览器只访问 Web 同源 adapter，经 BFF 到 owner；不直连 System、LiteLLM 或数据库。

跨仓 System smoke（需各仓依赖已按 frozen lock 安装）：

```bash
python3 scripts/e2e/run_system_owner_smoke.py \
  --postgres postgresql://HOST/postgres --redis redis://HOST:6379/2 \
  --node24-bin /ABSOLUTE/NODE24/bin --node22-bin /ABSOLUTE/NODE22/bin
```

脚本创建随机独立数据库，仅清理本次登记资源与 System 专属缓存前缀；不 FLUSHDB、不重启共享服务。
验证 BFF manifest/catalog 和 Agent 实际 HTTP resolve/模型映射，不执行 provider 推理，不能称作真实推理验收。
历史全仓/owner-health runner 的危险实现已移除，原入口非零退出且不访问基础设施；Root 后续重建全仓隔离编排，不用它取代本轮 System 验收。
