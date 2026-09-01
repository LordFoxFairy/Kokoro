# ADR-013 V1 使用 MySQL + Mongo，不引入 PostgreSQL

状态：已废弃（2026-09-01）

> **已废弃（2026-09-01）**：本文是旧 MySQL + Mongo 迁移阶段的历史决策，不是当前运行时规范。正式业务子仓库统一采用 PostgreSQL + Redis，当前决策见 [ADR-028](ADR-028-postgresql-redis-runtime-baseline.md)。请勿依据本文新增数据库、服务、环境变量或部署入口。

## 决策

V1 最终运行时只保留：

```text
MySQL      结构化业务事实：IAM、Model、Credit、Payment、Capability、Chat 元数据
MongoDB    Session/Agent checkpoint、事件、运行时文档、向量与非结构化上下文
Redis      队列、live stream、短租约、幂等快速路径；不作业务幂等最终真源
Object     大文件、artifact bytes；数据库只存 metadata/key/hash/size/mime/owner
```

不把 PostgreSQL 加入 V1 基础设施。现有 Root PostgreSQL baseline、`langgraph-checkpoint-postgres`
和 PostgreSQL 设计文档标记为迁移期实验/历史方案，不得继续扩展新的业务表或运行入口。

## 理由

1. 当前部署、环境变量、迁移命令和已实现平台域已经是 MySQL + Mongo + Redis；新增 PostgreSQL 会形成第四类持久化依赖。
2. Credit、Payment、IAM 的核心需求是 InnoDB 的事务、唯一约束、行锁、审计和稳定后台查询，MySQL 已足够。
3. Session、Agent checkpoint、原始事件、向量和大 JSON 已经天然属于 MongoDB，不需要用 PostgreSQL JSONB 复制一套文档存储。
4. 当前没有必须依赖 PostgreSQL 专属能力的业务查询、扩展或地理/分析场景；复杂查询能力不是引入数据库的充分理由。
5. 早期系统的总复杂度由数据库种类、迁移链路、备份、连接池和本地开发门槛共同决定；少维护一个数据库比理论功能冗余更有价值。

## 约束

- MySQL 必须使用 InnoDB；余额、支付、权限、订阅和幂等状态只在 MySQL 事务中修改。
- Redis 可以使用 `SET NX EX` 做短 TTL 抢占、请求合并和重试风暴抑制；业务幂等最终由 MySQL 唯一键/状态记录或 Mongo 唯一索引证明。
- Redis 故障策略按服务声明：IAM/Credit/Payment 的持久状态不能因 Redis 快速路径不可用而丢失；Session/Agent 的 queue/live bus/lease 把 Redis 视为运行时硬依赖，Redis 不可用时这些核心运行服务不可服务，必须暂停新执行并返回明确依赖故障，不绕过 Redis 假装成功。
- Mongo 向量索引只服务文档/语义检索；不得把 Credit、Payment、IAM 主事实放 Mongo。
- 一个事实只能有一个 owner 和一个 runtime writer；跨存储流程使用 outbox、幂等命令和补偿状态机。
- Agent checkpoint 优先迁移到 MongoDB checkpointer；迁移完成前，旧 PostgreSQL checkpoint 只能作为兼容运行时，不能作为新业务设计依据。
- 后续如需 PostgreSQL，必须提交新的 ADR，证明 MySQL/Mongo 无法满足明确的业务不变量或查询，并包含新增运维、迁移、备份和测试成本。

## Redis 故障边界

```text
IAM：Redis 是认证运行时硬依赖；Redis 不可用时认证、刷新、授权和受保护业务入口 fail closed，MySQL 仍保存身份事实
Session / Agent live execution：Redis 为 required；Redis 不可用时核心运行服务不可服务，停止新 run，不绕过 Redis
SSE / live fanout：Redis 不可用时连接失败或显示恢复中，不伪造实时成功
验证码 / 限流 / 短期去重：Redis 不可用时按产品策略 fail closed 或暂时关闭该能力
```

生产环境的 Redis 不采用单机裸实例：至少使用托管高可用、Sentinel 或 Cluster，并配置持久化、故障切换和恢复演练。单机 Redis 只用于本地开发和测试。

## 被取代的决策

- ADR-005 的 MySQL + Mongo 决策继续有效；本 ADR 将其提升为 V1 最终存储边界。
- ADR-012 及 24/25/27 中的 PostgreSQL SQL-first 目标降级为迁移期试验，后续应按本 ADR 修正文档和实现计划。
