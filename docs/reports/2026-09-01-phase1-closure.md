# Kokoro 阶段 1 闭环验收证据

日期：2026-09-01

## 验收范围

本次只验收当前阶段的三个运行时子仓库：

```text
kokoro Web → kokoro-bff 的 Chat 内部业务边界 → kokoro-agent worker
                               PostgreSQL 17 + Redis 7
```

阶段 1 使用 `KOKORO_BFF_MODE=mock`。这表示 BFF 的 Web-facing Chat contract 使用确定性
fixture；它不冒充已接入持久化业务 upstream。Agent 仍以独立 worker 启动，使用 PostgreSQL
和 Redis 的生产 adapter。live BFF upstream 接线不属于本阶段的验收边界。

## 门禁结果

### Root contract

```text
pnpm contract:format       PASS
pnpm contract:lint         PASS
pnpm contract:check        PASS
uv run pytest -q           84 passed
python3 scripts/verify-backend-design.py  PASS
git diff --check           PASS
```

独立 Credit contract 也通过 `pnpm exec buf lint --config contract/buf.credit.yaml`；它不被
Slice-A renderer 当成同一生命周期的 Proto inventory。

### 三个子仓库

```text
kokoro-agent: ruff PASS, pyright PASS, 497 passed, Docker build PASS
kokoro-bff:   lint/typecheck/test/build PASS, 18 passed, Docker build PASS
kokoro:       lint/typecheck/test/build PASS, 1135 passed, first-site smoke PASS
```

## 真实 Compose 验收

使用临时端口启动 `deploy/provision-phase1.sh`，避免影响已有本地工作区：

- PostgreSQL：15434，`pg_isready` 返回 accepting connections；
- Redis：16381，`redis-cli ping` 返回 `PONG`；
- Web：13002；根路径 307 到 `/app`，跟随后返回 200；
- BFF：4300，`/healthz` 与 `/readyz` 返回 200；
- Agent：容器保持 `Up`，日志确认消费 `kokoro:runs:requests`。

HTTP 闭环断言：

1. 读取 `/v1/projects` 和 `/v1/sessions`；
2. 读取会话详情；
3. POST `/v1/sessions/{id}/messages`；
4. 使用同一个 `Idempotency-Key` 重放，响应完全一致；
5. 从 `Last-Event-ID: 0` 读取 SSE，收到 `session.created`、`run.created`、`message.user`
   和 `message.completed`，序号单调递增；
6. PostgreSQL、Redis、Web、BFF、Agent 都完成启动和健康验证。

验收完成后，Compose 容器、卷和网络均已按项目名清理；旧的 `kokoro-payment-final-it`
MySQL 孤儿容器及其卷也已清理。当前阶段运行入口不再启动 MySQL/Mongo。

## 本次修复的实际缺口

1. `PgMemoryStore` 缺少同步 `batch` 抽象方法，导致 Agent 容器启动循环；已补齐同步桥接
   并加入非抽象类回归测试。
2. Credit proto 位于独立 contract module，但 Slice-A renderer 原来把它误判为 inventory
   漂移；renderer 现在遵循 `contract/buf.yaml` 的排除目录，并保留独立 Credit lint。
3. `provision-phase1.sh` 原来把 Web 根路径的合法 307 当作失败，也会用 shell 默认端口
   检查而不是 env 文件实际发布端口；现在跟随重定向并通过 Compose 读取发布端口。

## 阶段结论

阶段 1 的 contract、三仓质量门禁、PG+Redis Compose 启动、BFF mock Chat API、SSE 重放、
幂等重放和部署脚本已形成可重复闭环。后续接入真实业务 upstream 时，必须继续沿用同一
`v1` contract，并在各自子仓先完成 PostgreSQL/Redis adapter、测试和发布门禁；不得把
MySQL/Mongo、独立 Session 或 Gateway 重新接回阶段 1。
