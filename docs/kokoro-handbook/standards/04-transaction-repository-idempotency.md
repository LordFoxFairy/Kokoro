# 事务、Repository 与幂等基础规范

状态：正式规范，2026-08-21

## 1. Repository 的职责

Repository 是领域或应用层需要的持久化抽象，不是通用 CRUD 工具箱。

```text
Domain/Application contract
        ↓
Infrastructure repository implementation
        ↓
MySQL driver / query builder
```

规则：

- Repository 按聚合、业务查询或用例定义，不按每张表机械生成。
- 对外暴露业务语义方法，例如 `findActiveIdentity`、`reserveCredit`，而不是只暴露 `findById/update`。
- 查询模型和写模型有明显差异时，可以使用独立 Query Repository；不强行让一个 Repository 承担所有读写。
- Repository 不负责 HTTP、RPC、权限策略编排或跨模块事务。
- Infrastructure 可以使用 ORM/query builder，但 domain 不依赖 ORM 类型。

## 2. 事务边界

- 一个 Application command 默认对应一个本地事务。
- 事务边界由用例决定，不由 Repository 随意开启嵌套事务。
- 一个事务只覆盖同一 owner 的本地数据库写入和必要的领域不变量。
- 外部 RPC、支付 provider、文件存储和消息发送不放在数据库事务内部等待完成。
- 跨子仓库操作不伪装成本地事务；先定义命令幂等、状态机和补偿语义，再决定是否需要异步协调。
- 读取后写入时使用约束、条件 UPDATE 或 version 检查保护竞态，不依赖应用内单线程假设。

## 3. 并发控制

优先级：

1. 数据库唯一约束解决重复创建。
2. 单条条件写解决余额、额度和状态抢占。
3. `generation`/`version` 实现乐观锁。
4. 只有明确需要时才使用 `SELECT ... FOR UPDATE`。

示例：

```sql
UPDATE credit_account
SET held_micros = held_micros + $1,
    generation = generation + 1,
    updated_at = now()
WHERE account_id = $2
  AND balance_micros - held_micros >= $1
  AND generation = $3;
```

应用必须检查 affected rows，而不是只判断 SQL 是否执行成功。

## 4. 幂等

以下命令必须有明确幂等策略：

- 支付 provider webhook
- 注册/登录确认
- 积分 reserve/commit/release
- 权益发放和兑换
- 文件上传完成确认
- 跨仓 RPC command

幂等优先采用：

- 数据库唯一 `command_id` / `provider_event_id`
- request digest 防止同一 id 重放不同 payload
- 状态机终态检查
- 条件更新

Redis 可以参与幂等，但只能作为快速路径：使用 `SET NX EX` 做短期抢占、重复请求合并、重试风暴抑制或分布式锁。禁止用进程内 Map、单机锁或 Redis 短期 key 作为唯一业务幂等真源；最终幂等必须由 MySQL 唯一键/持久化 command receipt、Mongo 唯一索引或持久化状态机证明。

推荐双层流程：

```text
请求进入
  -> Redis SET NX EX（快速发现 in-flight / 抑制并发，可失败后继续走持久化路径）
  -> owner 数据库事务插入 command_id/provider_event_id 唯一记录
  -> 同一事务完成业务状态变更并保存结果
  -> Redis 可缓存结果或 in-flight 状态，不作为最终事实
```

Redis key 过期、淘汰、故障切换或重复执行时，数据库唯一约束和状态机必须仍能安全返回同一结果。支付 webhook、credit hold/capture/release、权益发放、上传完成和跨仓 command 不得只依赖 Redis。

这里的“Redis 故障后走数据库”只适用于 Redis 是幂等快速路径的同步用例，不适用于 Redis 本身就是运行链路依赖的服务。若 Session/Agent 的队列、live bus 或 lease 依赖 Redis，Redis 故障时不得假装继续执行：应暂停新执行、返回明确的 dependency unavailable，或把命令写入持久化 inbox/outbox 后等待恢复。

任何服务都必须在设计卡中声明 Redis 依赖级别：

```text
optional：Redis 只做缓存/快速去重，故障可直接走 owner 数据库
degraded：核心状态可继续写库，但实时流、异步执行或部分功能暂停
required：Redis 是当前执行链路必需依赖，故障时 fail closed，不绕过伪造成功
```

## 5. Domain、Application、Infrastructure 分工

### Domain

- 维护业务状态和不变量
- 提供有业务语义的行为
- 不访问数据库和网络

### Application

- 解析 command/query
- 组织授权、事务和 Repository 调用
- 调用 Domain 行为
- 处理跨聚合、跨服务的应用流程

### Infrastructure

- 实现 Repository
- 负责 SQL、连接、事务适配和外部 provider
- 将数据库行映射成 Domain/Application 所需模型

### Interfaces

- 解析协议输入
- 做边界 schema 校验
- 调用 Application use case
- 将内部结果转换为外部响应
