# 数据存储技术方案

> **阶段 1 当前裁决（2026-09-01）**：Web/BFF/Agent 三仓只使用 PostgreSQL + Redis。
> PostgreSQL 是唯一持久化真源，Redis 负责队列、事件流、租约、唤醒和短期缓存；不新增
> MySQL 或 MongoDB。本文下方的 MySQL/Mongo 分层是历史方案，不作为阶段 1 新代码、Compose
> 或部署配置依据。当前边界以 [storage-baseline-v1](../../../contract/spec/storage-baseline-v1.md) 为准。

## 总原则

```text
MySQL:
  核心管理、配置、权限、账务、强一致状态。

Mongo:
  Session/Agent 运行态文档（message projection、checkpoint、memory 等），长期真源；
  不承载 Storage 的 Asset/Artifact 生命周期。

Redis:
  run queue、raw event stream、live fanout、session/run lease、短期去重、限流辅助。

Object Storage:
  通过 S3-compatible 协议承载大文件和导出文件；Storage v1 默认使用 Docker MinIO，
  AWS S3、Ceph RGW 等只替换 endpoint/profile。e2b 云档的 workspace 收敛归档仍见 ADR-009。

PostgreSQL:
  当前方案不引入。SQLite 不作为 V1 runtime 存储策略。
```

## MySQL 数据

适合：

```text
site / user / workspace/team / model registry / provider account /
credit ledger / payment order / subscription / pricing rule / admin config
```

原因：唯一约束清晰、事务强、审计好做、后台查询稳定、账务一致性要求高。

## Mongo 数据（Session/Agent owner）

适合：

```text
session message history / agent run state / checkpoint / memory / runtime document
```

原因：运行态文档结构变化快，会话事件和 checkpoint 天然是文档流。Job、Asset、Artifact
的最终业务事实仍由各自 owner 管理，不因 payload 是 JSON 就迁入 Mongo。

## Redis 数据

```text
适合：run queue、raw event stream、session live bus、SSE live tail、短期锁和限流。
不适合：长期历史真源、积分余额、支付状态、用户权限。
```

Redis 是传输不是数据库，长期历史必须落 Mongo 或 MySQL。

## Object Storage

```text
适合：音频 / 视频 / 图片 / 压缩包 / 导出结果 / 大型日志附件。
Storage 的 MySQL 只保存 object identity、metadata、hash、size、mime、owner、scan 和生命周期；
bytes 只进入 S3-compatible ObjectStore。业务代码不直接依赖 Mongo、S3 SDK 或 bucket/key。
```

## siteId 策略

所有业务数据默认带 `siteId` 或能通过上级对象追溯 `siteId`。

```text
必须直接带 siteId：
  User、Team/Workspace、CreditAccount、LedgerEntry、UsageRecord、
  PaymentOrder、Subscription、Project、Job、Artifact。

可平台复用（靠 SiteModelPolicy 控制可见性）：
  ProviderAccount、ModelBinding。
```

## 数据一致性

```text
强一致链路：
  payment event -> order/subscription -> credit grant
  credit hold -> job execution -> commit/release
  user/team permission -> run authorization

最终一致链路：
  provider callback -> job status -> artifact metadata -> web refresh
  agent event -> session normalization -> SSE
  analytics event -> dashboard
```

## 禁止

```text
不把账务放 Mongo。
不把长期事件历史只放 Redis。
不引入 PostgreSQL。
不让业务模块直接读写其它模块的 MySQL 表。
```

相关：[ADR-005 MySQL 与 Mongo 数据边界](../decisions/ADR-005-mysql-and-mongo.md)、[deployment](08-deployment.md)。
