# ADR-030：IAM 重构的协议、数据与运行边界

- 日期：2026-09-04。
- 状态：主控采纳，作为 IAM 分片实施的设计约束；不代表目标实现或最终验收已完成。
- 范围：`kokoro-iam` 既有认证、授权、Magic Link 投递；其他子仓仅记录依赖，不在本轮改动。
- 输入：IAM-01 候选文档、源码 `23a0b65e0e361d474d9afed491379df45a36f574`、SQL/API 独立审查。
- 执行记录：[IAM 任务板](../../superpowers/plans/2026-09-04-iam-engineering-alignment.md)。

## 1. 目录与运行拓扑

采用 [TS 手册](../standards/08-typescript-backend-engineering.md) 的模块优先规则。当前认证、登录建档、session、
权限读取和审计追加共同参与登录事务，先归入 `modules/auth`，按真实的 Magic Link、session 等子能力展开。
不预建 OAuth、Passkey、组织/角色管理模块；不用 Root 四层模板、技术品牌目录或通用 command executor。
登录组织选择是 Service 业务规则，Repository 只提供候选读取与同事务写入，不把选择政策藏入 SQL 的 LIMIT 1。

保留单进程、HTTP 4211/RPC 4212、三个 HTTP 读取路径和六个 RPC；Fastify 切换采用两个实例、共享唯一 runtime，
不把换框架与合并端口绑定。Pool、Redis、JWT、Service、worker 各只创建一次；两个实例分别监听，共同处理部分
启动失败、draining 和关闭。只有两个 listener 均就绪才启动投递，退出先停新 claim 再排空请求与在途投递。

依据：[Fastify Server](https://fastify.dev/docs/latest/Reference/Server/)、
[Connect server plugins](https://connectrpc.com/docs/node/server-plugins/#fastify)。双实例选择是本项目工程判断。

## 2. SQL 身份与模型

- 本表主键统一 `id`；引用字段保留 `tenant_id`、`principal_id`、`organization_id` 等业务名。
- `iam_tenant.id` 保留现有 opaque `TEXT`，引用 `tenant_id` 同为 `TEXT`。这是保留既有跨仓身份的具名例外；
  不额外创建 tenant UUID、映射表或兼容列。其他现有资源 ID 仍为 UUID。
- 删除没有生产读写的 `iam_identity` 及其专用索引；保留有建档写入的 user、只读授权依赖的 role/permission/grant。
- 默认值但无读写/比较的 generation、恒空审计 payload、重复邮箱字段等按逐字段证据精简，不能只看表名删表。
- principal/organization 已有 deleted 语义，改用 `deleted_at` 与停用/暂停状态分离；tenant/user/role 当前无恢复用例，
  不机械加列。关系与凭据采用撤销或保留期清理，不补造删除/恢复 API。
- 每个 UNIQUE/CHECK/索引保留业务或查询证据；保留严格唯一不变量的数据库保护，移除无用查询索引。
- 无外键、空库 canonical schema 安装、catalog drift 与并发关系验证沿用 [SQL 手册](../standards/03-sql-and-postgresql.md)。

## 3. 登录、会话与授权

- 有效身份投影同时约束 tenant、organization、principal、membership、session 及同租户关系；JWT scope 与权威
  session 一致，权限从当前事实读取。无效身份为 Unauthenticated，依赖故障不伪装权限拒绝。
- 登录先区分不存在的 contact 与已经存在但失效的身份。只有真正新邮箱建档，不通过重新注册绕过停用。
- 一个有效组织候选直接选择，包括唯一 team；多个候选且仅一个 personal 时选择 personal；其余明确返回
  FailedPrecondition，不随机挑选，不新增组织切换 API。
- 保留 logout 单 session 与已有 refresh rotation 语义；全 family 撤销、OAuth、Passkey 和组织管理另立需求。
- 父有效性读取与关系创建在固定锁顺序中重验；`FOR SHARE` 可与父状态更新互斥，不能用 `FOR KEY SHARE`
  假装阻止非 key 字段更新。未知提交、回滚失败和连接损坏保留原因并销毁不确定连接。

依据：[PostgreSQL 行锁](https://www.postgresql.org/docs/current/explicit-locking.html#LOCKING-ROWS)、
[node-postgres 事务](https://node-postgres.com/features/transactions)、[连接释放](https://node-postgres.com/apis/pool)。

## 4. API 输入与安全重放

- 保留 Proto message/field 编号；静态 RPC 校验在 Proto 及实际验证执行链落地，不复制一套 RPC Zod 字段。
- request ID 只解析一次，适合响应 header，日志、handler 与 ErrorDetail 共用；非法输入返回稳定错误。
- 调用方 request_digest 为有界输入，不视为已证明的请求摘要。服务端额外计算版本化、无歧义的 HMAC 绑定：
  operation、权威 tenant、客户端摘要和有效业务输入；refresh/logout 包含凭据定位出的 session 身份。
  request ID/trace/deadline 不参与业务绑定。同 identity 换 payload 在解密重放前冲突，不强迫消费者新增参数。
- 敏感结果采用版本化 AEAD 快照，AAD 绑定 tenant、operation、command、服务端绑定及格式版本；记录 key ID，
  密钥通过受控配置提供，绑定与加密密钥用途隔离。轮换保留重放窗口所需旧 key，不做明文回退。
- 重放返回原 token 字节，不重新签发、不延长有效期、不把旧 principal 快照当当前授权；会话/父资源已经失效时
  不释放可用凭据快照。窗口过期为 FailedPrecondition，完整性损坏为 Internal，已识别依赖故障为 Unavailable。
- Refresh 重放检查结果 successor 及其父资源，输入旧 session 已 rotated 本身不阻止合法重放；Logout 成功
  receipt 按窗口重放，不对已经 revoked 的目标套用认证凭据释放检查。
- 结果重放与命令去重分开：认证结果窗口不超过原 access token 到期；RequestMagicLink 不超过 link 到期；
  logout 结果最多 24 小时。去重 tombstone 至少保留 24 小时，期间结果失效不重新执行命令。
- V1 仅安装新 schema；旧 receipt 不支持兼容解密或不可信绑定重放。本轮不自动清理任何已有数据库。

## 5. 保留与操作边界

- 读取先检查有效期限，不依赖清理已经执行。过期敏感快照可清除，去重身份留到其窗口结束。
- 原 refresh session/digest 保留至 refresh 到期后至少 24 小时；link/outbox 清理须等待终态与有关重放窗口结束。
- 清理使用有界批次、固定时钟和索引，跳过有效引用/仍在处理的记录，真实数据库测试证明边界；不自动清空业务库。
- principal/organization 的 deleted_at 只落实现有删除含义，未新增恢复产品；不自动硬删身份或审计历史。
  审计/身份的不可逆清理要求显式批准的保留策略与 cutoff，禁止把工程默认值说成法定保存期限。
- key 故障与密文损坏有界分类处置，不无限 provider retry，也不清掉失败证据后假装成功。

### 5.1 Magic Link 投递的密钥与终态证据

投递 token 与命令 receipt 是不同生命周期。第 4 节的 keyring/key ID 要求针对 receipt，不隐式要求把
当前单 key 投递升级成通用密钥平台。S3 保留投递现有配置与 outbox 结构，采用**停签发、旧 key 排空、再换 key**：

- 缺失或长度不符的 key 在启动、claim 前失败；已加载的错误 32-byte key、密文/tag/AAD 损坏统一归为
  `delivery_decryption_failed`，当前格式没有 key ID，不能凭错误文本区分“旧 key 缺失”和“密文损坏”。
- Repository 返回有类型的加密 claim，不在已提交 claim 的映射中解密。Processor 先判断取消、expiry 与次数，
  再解密、调用 provider；解密、provider、状态持久化分别处理错误。解密故障只在现有次数/有效期内有限重试，
  不向 provider 发送、不重新签发 token、不记录密码材料；过期或次数用尽转入终态。
- 保留现有 terminal CHECK：`delivered/failed` 清除 token ciphertext/IV/tag，保留 delivery 身份、次数、
  时间、受限错误码和已有 provider ref。删除短期凭据与删除失败证据是两件事；本片不删除 outbox 行，也不
  提前 GC。此前技术方案中“不自动丢弃加密材料”需收敛为“有效重试期保留，终态按既有约束清凭据并保留元数据”。
- `delivered` 只表示 provider 已接受并返回契约 receipt，不保证邮件送达收件箱；`failed` 表示 IAM 停止尝试，
  不证明外部 provider 从未接受。provider 已接受后的 SQL 故障不重标成 `provider_unknown`，不覆盖已提交终态。
- 换 key 前在维护窗口阻断所有实例的新签发入口，并确认在途签发已经结束；旧实例内的 worker 继续用旧 key
  排空 pending/processing，包含 lease 恢复及过期终止。确认没有旧 key 活跃密文与在途投递后停止全部旧实例，
  再以新 key 启动并恢复入口。仅等待 link TTL 不等于排空；本片不新增管理 API、热重载或第二种 worker 进程。
  不承诺不停签发的混合 key 滚动发布；确有该要求时再提出独立 delivery key ID/keyring 设计与原子 enqueue 变更。
- provider 调用始终使用同一持久化 delivery ID。真实 PG 加本地幂等 provider fixture 验证 IAM 的重试/fencing
  行为；真实供应方的接受去重、响应丢失、并发和保留窗口仍需供应方 sandbox 证据，两者分别记录。

该决定来自对现有 claim/processor/SQL 约束的复核，属于 IAM 的最小闭环取舍，不是通用加密系统标准。
S3 实现前须同步本仓技术/API/数据及 RUNBOOK 的相应表述，并以失败断言证明上述边界。

## 6. 放行方式

三面文档先按本决策对齐，主控审查设计后逐片放行。每片写入前明确对机器 contract/schema 的影响；没有这类
变化的首片可以在现有机器源上修复已确认行为，不要求先做与首片无关的主键/框架替换。
涉及机器源的切片先修源与验证断言，再对齐实现；以同一自洽 commit 交付。方案通过和实现通过分开记录。

IAM 单仓验收不冒充 BFF 已接入：当前缺失的 BFF IAM consumer、Web cookie 集成、逐 workload tenant grant 属于
后续子仓/跨仓切片。本轮用真实 IAM 客户端契约测试证明 owner 行为，并明确记录消费者缺口。
