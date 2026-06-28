# 数据存储技术方案

## 总原则

```text
MySQL:
  核心管理、配置、权限、账务、强一致状态。

Mongo:
  session/event/job/artifact/context/result 等产物型和文档型数据，长期真源。

Redis:
  run queue、raw event stream、live fanout、session/run lease、短期去重、限流辅助。

Object Storage:
  大文件和导出文件。

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

## Mongo 数据

适合：

```text
session message history / agent run state / checkpoint / job result /
artifact metadata / music·video·image·code 产物上下文 / 大 JSON 配置快照
```

原因：文档结构变化快；产物 metadata 类型复杂；job 状态可能含 provider 原始 payload；会话和事件天然是文档流。

## Redis 数据

```text
适合：run queue、raw event stream、session live bus、SSE live tail、短期锁和限流。
不适合：长期历史真源、积分余额、支付状态、用户权限。
```

Redis 是传输不是数据库，长期历史必须落 Mongo 或 MySQL。

## Object Storage

```text
适合：音频 / 视频 / 图片 / 压缩包 / 导出结果 / 大型日志附件。
数据库只保存 object key、metadata、hash、size、mime、owner 和权限。
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
