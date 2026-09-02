# kokoro-iam v1 技术方案与契约

状态：目标实现基线，2026-08-27

本文是 IAM v1 的执行级技术方案。它约束 IAM 子仓库的代码、SQL、RPC/HTTP 适配器和测试；与旧的
`Organization`、`kokoro-site`、`kokoro-user` 原型描述冲突时，以当前 Root contract 的 `Organization` 语言和本文契约为准。

## 1. 定位与边界

`kokoro-iam` 是身份和访问控制 bounded context，负责把可信请求上下文解析为可验证的授权事实。

负责：

- Site/tenant 目录与生命周期
- User、service principal、external identity 和 contact
- Organization、Membership、Role、Permission、Invitation
- 登录、magic link、refresh session、撤销和重放防护
- Authorization decision、ExecutionIdentity 和安全审计
- IAM command 的幂等执行

不负责：

- Model、Credit、Payment、Subscription、Agent run、Chat message、Session product state
- GA 的 `RuntimeNamespace`、checkpoint、graph state 或恢复
- 业务方数据库表的写入
- Redis 中的最终事实、审计记录或授权策略

术语约定：

| v1 术语 | 说明 |
|---|---|
| `tenant_id` | IAM 及所有租户业务表使用的隔离键；入口从可信 SiteContext 得到 |
| `site_id` | Site 资源的内部标识；不是浏览器可自由选择的授权依据 |
| `organization_id` | Site 内承载成员、角色和权限的组织单元 |
| `principal_id` | user、service 或 operator 的统一主体标识 |
| `subject` | 被代表的个人、organization/project 或 service subject |
| `ExecutionIdentity` | IAM 签发给下游的 `{tenant_ref, actor, subject, identity_assertion_ref}` |

## 2. 技术架构

```text
HTTP / gRPC / Admin adapter
            |
      application use cases
            |
  domain policies + public ports
       /                 \\
PostgreSQL repository  Redis runtime
事实、审计、会话、       限流、nonce、重放、撤销传播、
  Organization、权限、幂等收据 session hot state、分布式协调
```

### 2.1 依赖规则

- PostgreSQL 是持久化事实源；所有 IAM 业务写入必须经过 application use case 和事务。
- Redis 7+ 是 IAM 运行时硬依赖。`readyz = postgres healthy AND redis healthy`。
- Redis 不允许以内存实现替代，也不允许 Redis 故障时关闭限流、nonce 或撤销检查。
- 新的认证、刷新、撤销、授权、管理和幂等命令在任一依赖不可用时返回 `503 dependency_unavailable`。
- access token 的本地验签属于消费者运行时优化；不能被解释成 IAM 在 Redis 故障时继续签发或刷新。
- MySQL、MongoDB 不属于 IAM v1 依赖。身份、授权、session 和审计需要事务、行锁和可追溯 PostgreSQL 事实。
- Domain 只依赖值对象、端口和策略；不得 import pg、Redis client、HTTP 或 protobuf。
- interfaces 只做协议转换和认证上下文提取；事务、授权和状态转换放 application。

## 3. 目录拓扑

```text
src/
├── modules/
│   ├── site/                 # site context、tenant lifecycle
│   ├── identity/             # principal、identity、contact
│   ├── organization/         # organization、membership、role、permission、invitation
│   ├── authentication/       # magic link、credential、session、token
│   ├── authorization/        # policy evaluation、decision、assertion
│   └── audit/                # security event append/read
├── application/              # cross-module use-case orchestration only
├── contracts/                # public DTO/port schemas, no transport client
├── infrastructure/
│   ├── postgres/             # pool、transaction、repositories、row locks
│   └── redis/                # Lua/Functions、rate limit、nonce、revocation
├── interfaces/
│   ├── http/
│   ├── rpc/
│   └── admin/
├── config/                   # env parsing and invariant checks
├── bootstrap/                # dependency graph and readiness
└── main.ts
```

禁止：全局 `utils`/`common` 业务垃圾桶、跨模块直接访问 repository、接口层直接写 SQL、业务模块
直接读取 Redis key、用 `site_id` 或 `user_id` 充当 `tenant_id`。

## 4. PostgreSQL SQL 规范

IAM schema 使用 PostgreSQL，所有表遵循全局 PostgreSQL 规范和以下 IAM 约束：

1. 每张表使用应用生成的 UUID 主键；主键只承担行定位。
2. 所有租户事实必须带 `site_id`/`tenant_id` 隔离条件；`tenant_id` 是 opaque text，内部实体 ID 默认使用 UUID。
3. 软删除统一使用 `deleted_at timestamptz null`；业务默认只读取 `deleted_at is null`，删除采用状态/时间双写。
4. 所有可变聚合有 `version bigint not null default 1`，更新使用 `where ... and version=$n` 乐观并发校验。
5. 审计字段统一为 `created_at`、`updated_at`、`created_by`、`updated_by`；系统任务使用固定 system actor。
6. 同一 owner 内可证明的引用关系使用 PostgreSQL 外键；跨仓引用只保存 opaque ID，不建立跨仓外键。
7. 可证明的业务唯一性使用 `UNIQUE` 或 partial unique index；禁止用“先查询再插入”代替数据库约束。
8. 主键索引、普通查询索引和锁扫描索引允许存在；每个索引必须对应真实查询或不变量。
9. 所有 SQL 使用 `$1, $2, ...` 参数占位符，禁止字符串拼接；事务内锁顺序和 affected rows 检查必须写入 application contract。
10. 所有时间使用 `timestamptz`；金额/计数使用整数；JSONB 只放有 schema 版本的非查询扩展字段。

### 4.1 v1 表集合

```text
site_site
iam_principal
iam_identity
iam_contact
iam_organization
iam_membership
iam_role
iam_permission
iam_role_permission
iam_membership_role
iam_magic_link
iam_auth_session
iam_command_receipt
iam_security_event
```

同一 IAM owner 内的关系使用 PostgreSQL FK；跨仓引用只保存 opaque ID，不建立跨仓 FK。关联表的
重复写入由 PostgreSQL 唯一约束、命令幂等键和事务状态机共同保护。

### 4.2 锁模型

锁桶为固定预创建行，不能在竞争事务中依赖“插入即锁”：

```sql
SELECT namespace, bucket_no
FROM iam_lock_bucket
WHERE namespace = $1 AND bucket_no = $2
FOR UPDATE;
```

锁顺序固定为 `site -> organization -> membership/role/invitation -> command`，同一 use case 不反向取锁。
PostgreSQL 适配器统一封装 `withTransaction()`、`lockBucket()` 和 `assertVersion()`；业务模块不得自行拼接
`FOR UPDATE`。

## 5. Redis 运行时契约

Key 必须带 `iam:v1:{tenant_id}:` 前缀，并通过集中 key builder 生成。禁止业务代码拼接裸 key。

| 能力 | Redis 数据 | 事实源 | 失败策略 |
|---|---|---|---|
| 登录/发码限流 | counter + TTL | SecurityEvent/认证结果 | fail closed |
| magic link nonce | hash + TTL | MagicLink 状态 | fail closed |
| token/session 撤销 | revocation marker + TTL | PostgreSQL session 状态 | fail closed |
| authorization 热缓存 | versioned decision | PostgreSQL Organization/Role/Permission | 不命中回源；Redis 故障 503 |
| command claim | Lua 原子 claim | CommandReceipt | fail closed |
| 多实例协调 | short lease | 对应 PostgreSQL 事务 | lease 失败重试/503 |

Lua/Function 必须保持原子：`claim-if-absent`、`consume-once`、`rate-limit`、`revoke-and-publish`。
Redis TTL 只用于运行时垃圾回收，不改变 PostgreSQL 的过期、撤销和审计事实。

## 6. API v1 契约

### 6.1 通用请求/响应

每个请求必须带 `x-kokoro-request-id`，内部命令还必须带 `x-kokoro-command-id` 和
`x-kokoro-tenant-id`。tenant header 只作为已认证上下文的校验输入，不能覆盖入口解析出的 tenant。

```json
{
  "data": {},
  "meta": {"request_id": "REQUEST_ID"}
}
```

```json
{
  "error": {
    "code": "permission_denied",
    "message": "stable human-readable message",
    "request_id": "REQUEST_ID",
    "retryable": false,
    "details": {}
  }
}
```

错误码固定集合：`invalid_argument`、`unauthenticated`、`permission_denied`、`not_found`、
`conflict`、`version_conflict`、`idempotency_conflict`、`rate_limited`、`dependency_unavailable`、
`internal`。message 不承载 SQL、token、email token 或内部堆栈。

### 6.2 对外能力

```text
POST /v1/auth/magic-links
POST /v1/auth/magic-links/consume
POST /v1/auth/sessions/refresh
POST /v1/auth/sessions/revoke
GET  /v1/me
GET  /v1/organizations
POST /v1/organizations
PATCH /v1/organizations/{organization_id}
POST /v1/organizations/{organization_id}/members
PATCH /v1/organizations/{organization_id}/members/{membership_id}
DELETE /v1/organizations/{organization_id}/members/{membership_id}
GET  /v1/organizations/{organization_id}/roles
POST /v1/organizations/{organization_id}/invitations
POST /v1/authorize
```

写接口要求：鉴权上下文、tenant 绑定、权限判断、锁/版本校验、事务写入、SecurityEvent 和幂等收据
必须在一个 application use case 内完成。`DELETE` 仍是软删除，重复删除返回同一幂等结果。

`POST /v1/authorize` 只返回 decision，不修改被授权资源：

```json
{
  "data": {
    "allowed": true,
    "action": "session.write",
    "resource": "session:SESSION_ID",
    "tenant_id": "TENANT",
    "subject_id": "SUBJECT_ID",
    "decision_version": 7,
    "expires_at": "2026-08-27T12:00:00Z",
    "identity_assertion_ref": "ASSERTION_REF"
  }
}
```

### 6.3 跨服务身份

IAM 输出 `ExecutionIdentity(tenant_ref, actor, subject, identity_assertion_ref)`。调用方不得提交或选择
GA `RuntimeNamespace`；它不选择或下发 GA `RuntimeNamespace`，GA 只根据可信 tenant + subject 在自身 ingress 派生内部 namespace。
assertion 必须包含 audience、issuer、issued_at、expires_at、decision_version 和 provenance，过期或
撤销传播后不得继续用于新 admission。

## 7. 关键状态与业务链路

### 7.1 认证

```text
requested -> issued -> consumed
                  \\-> superseded
issued -> expired
```

发码：解析 SiteContext -> Redis 限流 -> PostgreSQL 锁桶 -> 创建 magic link -> 写 SecurityEvent。
消费：Redis consume-once nonce -> PostgreSQL 锁定 link -> 校验 expiry/status -> 创建 session -> 发布撤销/刷新状态。

### 7.2 Organization membership

```text
invited -> accepted -> active -> suspended -> removed(soft-deleted)
             \\-> expired
```

成员变更必须校验 actor 对 organization 的管理权限、目标 principal site 一致性和 role 状态；撤销成员后清理
Redis authorization cache 并发布 revocation event。历史审计不可删除。

### 7.3 幂等与并发

```text
new command -> Redis claim -> PostgreSQL receipt lock -> execute transaction
                         \\-> existing completed result
                         \\-> same command/different digest: idempotency_conflict
```

`command_id` 通过 PostgreSQL `(site_id, command_id, command_kind)` 唯一索引保护。CommandReceipt 查询必须
使用该索引和事务锁；不能使用假设 command_id 全局唯一的 API。

## 100 分证据

本节的 100 分只表示边界、数据 owner、目录、契约、依赖和测试设计齐全；它不是实现完成标志。

## 8. 测试与完成门禁

### 8.1 代码门禁

- Domain architecture test：不依赖 Prisma/HTTP/Redis client。
- SQL lint：所有 FK、CHECK、UNIQUE 和 partial unique index 必须对应同一 owner 的不变量；禁止跨仓 FK。
- tenant-scope test：每个 repository 的 read/write/delete 都带 tenant 条件。
- soft-delete test：默认读不返回 deleted 行，重复删除不物理删除。
- lock test：PostgreSQL 使用显式 `SELECT ... FOR UPDATE`，锁顺序一致，version conflict 可重试。
- Redis test：Lua claim/consume/rate-limit/revoke 原子性，故障时无内存降级且返回 503。

### 8.2 契约门禁

- protobuf/OpenAPI 源、生成物、consumer manifest 一致。
- error code、request id、tenant binding、idempotency header 和 `ExecutionIdentity` 有 wire test。
- Organization membership revoke 后新的 read/write/control admission 全部拒绝；SSE 重连必须重新授权。
- accepted delete retry 不依赖原 actor 当前权限；显式 cancel 与 GA recovery 保持边界分离。
- Session 的 HTTP/SSE ingress 通过 IAM public authorization decision 对当前 actor 做 `read`、`write`、`control`、`delete` 四类 Session action 校验。
- Session control admission 的 actor/authorization decision 进入 Session `ControlAudit`；ControlAudit/control_audit_ref 关联既有 Run，不产生第二个 namespace 或 payer。
- project 成员撤销、SSE 关闭/重连、Session read/control 拒绝、已接受 delete retry、以及显式 cancel 与 GA offline recovery 的分层测试齐全。

### 8.3 完成定义

IAM v1 只有同时满足以下条件才标记完成：

1. `kokoro-iam` 子仓库实际存在并能 clean build；当前根仓不存在该实现，因此本设计文档不代表实现完成。
2. PostgreSQL fresh migration 与本文表集合、约束、索引和状态机规则一致。
3. Redis 是真实依赖，readyz、Lua 原子操作和 fail-closed 测试通过。
4. API/RPC 契约已生成，Web agent 可只依赖公开 DTO、错误码和状态码。
5. Organization/Identity/Auth/AuthZ/Audit 的 unit、integration、contract、architecture test 全部通过。
6. 旧 Organization、Site、User writer 和旧 contract 生成物已删除；v1 首发不保留双写。

在这些证据齐全前，设计评分只能表示文档完整度，不能表示代码或运行时闭环。
