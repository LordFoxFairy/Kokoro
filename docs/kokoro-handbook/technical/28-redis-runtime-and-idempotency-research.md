# Redis 运行时依赖、队列与幂等技术调研

状态：技术调研结论，2026-08-22

本文件只讨论研发架构：Redis 在 Kokoro 中是不是硬依赖、Lua/Streams 如何使用、Redis 故障时服务如何表现，以及幂等最终应该落在哪里。它不是完整的生产运维手册。

## 1. 当前代码证据

Kokoro 当前已经把 Redis 放在运行时主链路，而不是只当缓存：

```text
kokoro-web -> kokoro-session -> Redis -> kokoro-agent
                         Redis live bus / queue / lease
```

现有证据：

- `kokoro-session/README.md`：生产使用真实 Redis，内存替身只用于测试；
- `kokoro-session/src/transport/redis`：Session 的传输实现；
- `kokoro-session/tests/transport-redis.test.ts`：Redis transport 集成测试；
- `kokoro-agent` 的 worker、streams、execution 依赖运行时控制和事件通道；
- `docker-compose.infra.yml`：Redis 是全局基础设施，而不是某个接口的可选缓存。
- 旧 `kokoro-user` 的 `magic-link-rate-limiter` 单元测试目前规定 Redis 异常时 fail open；这与生产安全目标不一致，迁移时必须改为安全入口 fail closed。

因此，Session/Agent 的最终方案不能写成“Redis 故障后绕过 Redis 继续执行”。这会把运行时依赖描述错。

## 2. 官方技术事实

### 2.1 Lua/Functions

Redis 官方保证 Lua script 在 Redis 内部原子执行；脚本可以跨多个 key 做条件读写。但脚本执行期间会阻塞其他 Redis 客户端，不能写长脚本。Redis 7+ 可以使用 Functions 管理服务端函数；普通 `EVAL` 脚本缓存可能在重启或故障切换后丢失，客户端必须能重新加载。[Redis Lua Scripting](https://redis.io/docs/latest/develop/programmability/eval-intro/)、[Redis Functions](https://redis.io/docs/latest/develop/programmability/functions-intro/)

结论：Lua 适合 `claim/renew/complete/deduplicate`，不适合承载长业务流程，也不能把 Redis 写入和 MySQL 写入变成一个原子事务。

### 2.2 Streams

Redis Streams 提供 append-only entry、consumer group、ACK、pending entries 和未确认消息重新认领；适合命令队列和 worker 协调。实时通知仍可以用 Pub/Sub，但关键任务不能只依赖 Pub/Sub，因为断线后没有历史重放。[Redis Streams](https://redis.io/docs/latest/develop/data-types/streams/)

结论：

```text
Agent command / control / work queue：Redis Streams + consumer group
SSE live fanout / 非关键通知：Pub/Sub 或独立 live stream
```

### 2.3 持久化与 HA

Redis 支持 RDB、AOF、RDB+AOF 和无持久化；主从复制默认异步。Sentinel 提供监控、通知、自动故障转移和主节点发现，但官方明确提示异步复制在故障时仍存在已确认写入丢失窗口。[Redis Persistence](https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/)、[Redis Replication](https://redis.io/docs/latest/operate/oss_and_stack/management/replication/)、[Redis Sentinel](https://redis.io/docs/latest/operate/oss_and_stack/management/sentinel/)

结论：单机 Redis 适合本地开发；生产至少使用托管高可用、Sentinel 或 Cluster。HA 解决可用性和故障切换，不自动把 Redis 变成跨数据库事务真源。

### 2.4 成熟 Redis 队列实现

[BullMQ](https://github.com/taskforcesh/bullmq) 的实现采用 Redis 队列、job id 去重、锁 TTL、锁续期、完成/失败状态、重试和事件 Streams。其核心语义是 worker 可能因锁过期或故障产生重复处理，因此业务 handler 仍需要幂等；队列解决投递和协调，不替业务副作用提供 exactly-once。

## 3. Kokoro 最终技术方案

### 3.1 Redis 依赖等级

```text
Session / Agent：required
  Redis 是 queue、control、live bus、lease 的运行时硬依赖。
  Redis 不可用时核心运行服务不可服务，不接收新 Run，不使用内存替代。

IAM / Payment / Credit：按进程部署决定
  如果该进程的请求 admission 或异步协调依赖 Redis，Redis 故障时同样返回 503。
  只有明确独立部署且 Redis 只是快速路径时，才允许继续走 MySQL。

Web SSE / live fanout：required for live behavior
  Redis 故障时断开、返回恢复中或 503，不伪造实时成功。
```

### 3.1.1 IAM 的特殊边界

IAM 不等于 Session/Agent，但 Kokoro 的运行时规范要求 Redis 作为统一基础设施硬依赖。IAM 的
持久身份事实仍然在 MySQL；Redis 负责 IAM 运行时安全和多实例协调，因此 IAM 不能在 Redis
不可用时绕过 Redis 继续接受业务请求：

```text
JWT/JWKS 验签：进程内完成，但 IAM readiness 仍要求 Redis available
Identity/Organization/Role：MySQL required，Redis required for runtime admission
Refresh token 轮换/撤销：MySQL 记录最终事实，Redis 负责热状态和撤销传播
登录/魔法链接限流：Redis Lua/Functions required
Nonce/重放防护：Redis required，VerificationToken 最终记录仍在 MySQL
Command idempotency：Redis 快速 claim，MySQL CommandReceipt 最终收敛
Authorization request coordination：Redis required，授权事实仍由 MySQL 查询
```

这意味着 Redis 故障时：

- IAM 的所有公开业务入口均返回 `503 dependency_unavailable` 或 fail closed；
- IAM 不关闭限流、不跳过 nonce/replay 检查、不把 Redis 替换为进程内 Map；
- 已签发且仍在有效期内的 access token 是否继续可用，由下游消费者自己的本地验签策略决定，
  不代表 IAM 服务仍然可用；
- MySQL 仍保存最终身份事实，Redis 恢复后由持久记录和重放流程重建短期运行状态；
- Session/Agent 仍然整体不可服务，因为它们的运行时 queue/live bus/lease 直接依赖 Redis。

不能为了“全站可用”把 Redis 故障时的登录限流关闭，也不能在撤销状态未知时继续放行任何 IAM
管理或授权请求。

### 3.2 生产数据流

```text
Web command
  -> Session ingress
  -> Redis Stream: agent.commands
  -> Agent consumer group
  -> Redis Stream: agent.events
  -> Session relay/projection
  -> MongoDB durable session/event state
  -> SSE live fanout
```

```text
MySQL：IAM、Payment、Credit、结构化业务事实
MongoDB：Session/Agent durable document、checkpoint、event history、vector/context
Redis：运行时队列、控制、lease、短期状态和实时传输
```

Redis 是运行时传输和协调层；Mongo/MySQL 是恢复和业务事实层。

### 3.3 Lua 函数边界

只允许短小、可审计的 Redis Function/Lua：

```text
claim_command(stream, command_id, consumer, lease_until)
renew_lease(run_id, fencing_token, lease_until)
claim_idempotency(scope, idempotency_key, request_hash, ttl)
complete_idempotency(scope, idempotency_key, result_digest, result_ref)
```

禁止：

- Lua 调用外部 HTTP、MySQL 或 Mongo；
- 在脚本中循环大量 key；
- 用 TTL 代替业务终态；
- 只依赖 Redis key 判断 Payment/Credit 是否已经成功；
- 把长时间 Agent 执行塞进 Redis 脚本。

### 3.4 幂等分层

```text
Redis Lua：快速 claim / in-flight / lease / 重试风暴抑制
MySQL：Payment/Credit/IAM command receipt、唯一业务键、状态机
MongoDB：Session/Agent event seq、checkpoint version、文档唯一键
```

Redis 发生故障时，Session/Agent 停止服务；Redis 恢复后，持久化状态负责恢复和防重复，不能依靠“绕过 Redis 直接执行”解决故障。

## 4. 故障矩阵

| 故障 | Session | Agent | MySQL 业务 API | 恢复动作 |
|---|---|---|---|---|
| Redis 连接断开 | 503/恢复中 | 停止消费和新 Run | 若进程依赖 Redis 则 503 | Redis 恢复、重新发现主节点、恢复 consumer/lease |
| Redis 主节点宕机 | 暂停新请求 | 暂停消费 | 不伪造成功 | Sentinel/托管服务提升副本 |
| Redis failover 后丢短期 key | 依持久状态恢复 | 重新 claim | 由 MySQL/Mongo 防重复 | 重建 Redis ephemeral state |
| Redis Streams backlog | 限制 admission | 扩容 consumer 或降载 | 不影响已提交业务事实 | 监控 pending、重试和 DLQ |
| Redis 内存达到上限 | fail closed，不继续写关键 stream | 停止新任务 | 不把 Redis 当可写缓存硬撑 | 容量治理、trim、迁移和恢复 |

## 5. 最终决策

1. Redis 在 Session/Agent 和 IAM 中都是运行时硬依赖；Redis 挂掉时这些服务不可服务。
2. 生产不使用单机裸 Redis；使用托管 HA、Sentinel 或 Cluster。
3. 关键任务使用 Streams + consumer group；Pub/Sub 只做非持久化实时广播。
4. Lua/Functions 只做短小原子协调，不承载外部事务。
5. Redis 幂等可以作为运行时 claim，但 Payment/Credit/IAM 的最终幂等必须落 MySQL；Session/Agent 的恢复事实落 MongoDB。
6. “Redis 故障后直接绕过 Redis 访问 MySQL”只适用于明确标注 Redis 为 optional 的独立进程，不适用于 Kokoro Session/Agent 主链路。
7. IAM 不属于 Redis optional 进程；IAM 的 `readyz`、请求 admission 和安全入口都必须验证 Redis。

## 6. 参考实现检查清单

```text
[ ] Redis client 支持 Sentinel/托管 endpoint 的重连和主节点发现
[ ] Session/Agent readiness 反映 Redis 是否可用
[ ] Redis 断开时新 Run 明确返回 dependency unavailable
[ ] Streams 使用 consumer group、ACK、pending reclaim 和重试上限
[ ] 关键 command 有 request hash 和 fencing token
[ ] Lua/Functions 有脚本版本、加载和故障切换后的 reload 机制
[ ] MySQL/Mongo 有最终状态和恢复查询
[ ] Redis 故障、failover、AOF 恢复、积压和重复消费都有集成测试
```
