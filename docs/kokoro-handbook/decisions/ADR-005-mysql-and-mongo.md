# ADR-005 MySQL + Mongo 数据边界，不引入 PostgreSQL

状态：已采纳。

## 背景

平台同时有强一致账务/配置数据和大量非结构化产物/事件/上下文数据。需要明确各类数据落在哪个存储，避免账务进文档库、长期历史只进缓存等错误。

## 决策

```text
MySQL  核心管理、配置、权限、账务、强一致状态。共用一个 database=kokoro，
       每个子仓拥有自己的 Prisma schema/migration/表名前缀。
Mongo  session messages/events、agent checkpoint/memory、job result、artifact metadata、
       创作上下文和大 JSON 等文档型与产物型数据的长期真源。
Redis  run queue、raw event stream、live fanout、session/run lease、短期去重，不作长期真源。
对象存储 音频/视频/图片/导出包等大文件；DB 只存 key/metadata/hash/size/mime/owner。
PostgreSQL  当前不引入；SQLite 不作为 V1 runtime 存储策略。
```

## 理由

```text
账务需要唯一约束、强事务、稳定后台查询和审计 -> MySQL。
产物 metadata、事件流、provider 原始 payload 结构多变 -> Mongo。
实时短期流量天然适合 Redis，但保留时长不可靠，不能当真源。
单库 database + 子仓 schema：后续拆库只改部署拓扑，不改领域边界。
不引入 PG 是为了降低运维栈复杂度，MySQL+Mongo+Redis 已覆盖当前需求。
```

## 约束

```text
不把账务放 Mongo，不把余额放 Redis，不把长期事件历史只放 Redis。
不让业务模块直接读写其它模块的 MySQL 表（跨模块走 API）。
不新增 kokoro-contracts，不使用 ports 目录命名。
跨存储一致性通过明确业务事务、outbox 或补偿机制处理。
```

## 替代方案（已否决）

```text
全 PostgreSQL          需新增运维栈，文档型产物在 MySQL/Mongo 已能覆盖。
全 Mongo               账务一致性和审计能力不足。
每子仓独立 database     早期增加运维和事务复杂度，用 schema 隔离即可。
```

## 影响

数据分层和一致性链路见 [data-storage](../technical/06-data-storage.md)；多 Pod 红线（无 InMemory 关键状态、余额不进 Redis）见 [deployment](../technical/08-deployment.md)。

相关：[ADR-003 credit ledger](ADR-003-credit-ledger.md)。
