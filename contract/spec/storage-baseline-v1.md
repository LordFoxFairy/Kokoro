# Kokoro 阶段 1 存储基线 v1

状态：阶段 1 架构决策（2026-09-01）。本文件是 Web、BFF、Agent 三仓闭环的存储约束；
历史 MySQL/Mongo 设计文档不再作为阶段 1 新代码的依据。

## 决策

阶段 1 只保留两类运行时基础设施：

1. **PostgreSQL**：唯一持久化真源。
2. **Redis**：实时传输、队列、租约、短期缓存和唤醒协调。

不再新增 MySQL 或 MongoDB 运行时依赖。已有旧实现按仓库逐步迁移，迁移期间不得继续扩展
旧客户端、旧 schema、旧 compose 服务或新的 `KOKORO_MONGO_*` / MySQL 配置。

## 所有权

| 数据 | PostgreSQL | Redis |
| --- | --- | --- |
| Chat session/message/run/event 索引 | 权威记录、查询和恢复依据 | SSE/live stream、短期 fan-out |
| Agent run/control/HITL/outbox | Run、control、工具效果、恢复和幂等的持久状态 | run stream、消费组、lease heartbeat、唤醒 |
| Project、Billing、Scheduler、Model、IAM 业务事实 | 各自 schema/table 的权威记录 | rate limit、锁、缓存、任务触发提示 |
| 大文件/导出物 | 只保存元数据、hash、引用和生命周期 | 不保存大对象；仅传递事件/通知 |

Redis 丢失后必须能由 PostgreSQL 恢复业务状态；PostgreSQL 不可用时不能把 Redis 当作持久
成功。任何需要跨进程、跨 pod 的状态必须先写 PostgreSQL，再发布 Redis 事件，并以 outbox/
消费回执保证恢复。

## 三仓边界

- `kokoro` Web 不连接 PostgreSQL 或 Redis，只调用同源 Web route。
- `kokoro-bff` 通过业务 ports 使用 PostgreSQL/Redis adapter；Mock 模式可以使用内存 fixture，
  但不能伪装成已持久化。
- `kokoro-agent` 通过 PostgreSQL adapter 持久化 durable run state，通过 Redis adapter 处理
  streams、outbox wakeup、lease 和 control 投递；Agent 不暴露浏览器 HTTP ingress。
- BFF 不直接访问 Agent Redis；BFF → Agent 只使用冻结的内部 adapter/HTTP 或消息契约。
- 三仓不复制彼此源码，不共享 `file:`、`workspace:` 或 git submodule 依赖。

## 配置规范

```dotenv
DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/DB
KOKORO_REDIS_URL=redis://HOST:6379/DB
```

服务可用的环境变量应使用本仓库的明确前缀（例如 Agent 的 `KOKORO_AGENT_DATABASE_URL`），
但语义必须落到 PostgreSQL/Redis。禁止使用浏览器传入的 `X-Domain`、tenant 或 site 字段
选择数据库；部署域名只由服务端 `KOKORO_DOMAIN` 转换成标准 `Forwarded` 上下文。

## 迁移验收

- `grep`/架构测试确认生产依赖、Docker Compose、启动脚本不再新增 MySQL/Mongo。
- PostgreSQL migration 在空库可重复执行，所有 owner 表按 namespace/user/project 隔离。
- Redis stream 消费、lease 失效、outbox repair、control resume 在 PostgreSQL 重启/Redis
  重启后仍可恢复，不把缓存命中当成成功。
- 三仓各自运行 lint/typecheck/test/build；真实基础设施门禁使用 PostgreSQL + Redis，Mock 门禁
  保持零外部依赖。
