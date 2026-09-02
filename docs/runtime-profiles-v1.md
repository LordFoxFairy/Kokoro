# Kokoro Runtime Profiles v1

本文件是 Root 对“最小启动、Model 独立、LiteLLM 可选、Agent 可选”的运行约定。子仓库只维护
自己的进程与实现，Root 只维护 profile、契约和部署组合，不复制子仓库代码。

## 组件边界

| 组件 | 是否默认启动 | 职责 | 不负责 |
|---|---:|---|---|
| `kokoro-model` | 按业务链路 | 模型目录、revision、policy、route resolve | 不生成模型、不探活/拉起 LiteLLM |
| LiteLLM | 否 | 外部 OpenAI-compatible provider gateway | 不拥有 Kokoro model catalog、Credit 或 Agent 状态 |
| `kokoro-agent-http` | 否 | BFF 调用的 durable run admission/control/replay ingress | 不执行 worker loop |
| `kokoro-agent` | 否 | Redis ingress 后的实际 Agent loop、恢复和事件事实 | 不提供 Web-facing API |

Agent 的完整执行 profile 必须同时包含 HTTP ingress 和 worker；只启动其中一个都不是完整闭环。
Agent 关闭时，BFF 仍可启动和就绪，Chat/调度执行路由返回 `agent_not_configured`，不会静默切换
到 mock 或让 Web 长时间等待。

## Profile

### local-fast

适合前端开发和布局验收：

```dotenv
KOKORO_BFF_MODE=mock
KOKORO_AGENT_ENABLED=0
KOKORO_LITELLM_ENABLED=0
```

启动 Web、BFF、PostgreSQL、Redis；不启动 Agent、Model、LiteLLM。Model 需要验收时独立用
`pnpm dev` 启动，不改变 Web+BFF 的最小启动时间。

### local-full

适合真实 Agent admission/worker 联调：

```dotenv
KOKORO_BFF_MODE=live
KOKORO_AGENT_ENABLED=1
KOKORO_AGENT_BASE_URL=http://kokoro-agent-http:4401
KOKORO_LITELLM_ENABLED=0
```

然后执行：

```bash
docker compose --env-file deploy/.env.phase1.local \
  -f deploy/docker-compose.phase1.yml --profile agent up --build
```

如果 Model resolve 返回 `transport=litellm`，再给 Agent 注入：

```dotenv
KOKORO_LITELLM_ENABLED=1
KOKORO_LITELLM_BASE_URL=https://HOST/v1
KOKORO_LITELLM_API_KEY=TOKEN
```

LiteLLM 仍由外部部署提供，不加入 `kokoro-model` 或 `kokoro-agent` 镜像。

### production

线上使用独立生产镜像或 Cloudflare 直连 Web，配置策略保持一致：

- 不需要 Agent 执行时，`KOKORO_AGENT_ENABLED=0`，只部署 Web+BFF 与必需的 PostgreSQL/Redis。
- 需要执行时，部署 `kokoro-agent-http` 和 `kokoro-agent`，并将 BFF 的
  `KOKORO_AGENT_BASE_URL` 指向 HTTP ingress。
- Model 作为独立 owner 部署；LiteLLM 只有在实际选择 `litellm` route 时才部署和配置。
- Web 只通过 BFF 同源 API 访问，浏览器不接触 Model、LiteLLM、Agent 数据库或 Redis。

每个环境的域名仍由 `KOKORO_DOMAIN` 注入：本地默认 `dev.kokoro.localhost`，线上替换为实际
`HOST`。域名只用于服务端站点绑定、`Forwarded` 和租户上下文，不依赖浏览器自带的 `X-Domain`。

## 验证

```bash
KOKORO_ENV_FILE=.env.phase1.example docker compose \
  --env-file deploy/.env.phase1.example \
  -f deploy/docker-compose.phase1.yml config --quiet

KOKORO_ENV_FILE=.env.phase1.example docker compose \
  --env-file deploy/.env.phase1.example --profile agent \
  -f deploy/docker-compose.phase1.yml config --quiet
```

Root machine-readable 对应项见 [`contract/goal2-cross-repository-contract-v1.json`](../contract/goal2-cross-repository-contract-v1.json)。
