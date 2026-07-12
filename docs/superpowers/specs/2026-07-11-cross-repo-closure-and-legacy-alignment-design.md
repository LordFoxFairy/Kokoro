# 根仓与四子仓闭环及遗留对齐总设计

状态：待评审的项目级设计稿（2026-07-11）

## 0. 文档定位

本文定义 Kokoro 根仓、`kokoro-agent`、`kokoro-session`、`kokoro-web`、
`kokoro-platform` 的共同终态、跨仓边界、实施波次和完成证据。它是项目组合级设计，
不是一份横跨所有文件的巨型实施计划。

每个独立子项目必须按本文边界另写聚焦 spec 和实施 plan；任何子项目完成都不能缩小本文的
总目标。通常优先级仍为：当前用户指令 > `CLAUDE.md` > handbook > 本文 > 历史
specs/plans/handoffs。本文获批后，其下列“显式纠偏清单”临时覆盖被点名的过期 handbook 段落；
Wave 0 必须先把纠偏回灌 handbook/CURRENT，完成后恢复正常优先级，再生成实现 plan。

本文纠正但不直接删除以下过期结论：

- `21-platform-mainchain-closure` 中“httpOnly cookie 后浏览器直接带 Bearer”的不可执行链路。
- `three-repo-rewrite-blueprint` 中“parse 后 ACK、靠 TTL 租约覆盖崩溃”的不完整恢复模型。
- `capability-hub-and-polish` 中“internal-secret 四洞已闭合”的过度完成声明。
- `docs/task.md` 与交接档中 Round-4 仍在飞、M1-M7/HUB4 已全完成等状态漂移。

## 1. 目标与完成定义

### 1.1 总目标

打通所有子仓库，并把 `docs/task.md`、当前交接档和代码审计确认的既有遗留全部对齐到可验证、
可部署、可恢复的真实实现。

### 1.2 “打通”不是测试绿的同义词

只有同时满足以下条件，才允许宣称总目标完成：

1. 新环境可从根仓 clone，按根仓 gitlink 初始化四子仓，得到本轮验证过的精确代码。
2. 根契约单源生成的全部镜像与四仓消费代码一致，没有手写镜像或未提交生成件。
3. web 登录、会话、能力、计费和团队路径都经过已验证身份，不能靠客户端自报 namespace/owner。
4. Hub 写入的能力能够被新会话快照和 agent 装配读取，审核/启停/排序语义不漂移。
5. request、control、terminal、projection、billing 在列出的崩溃点后都能自动收敛。
6. platform 的站点、用户、模型、积分、支付和 Hub 服务在真实 internal-secret 下仍能互调。
7. P0、P1、P2 遗留逐项有代码、测试、运行证据或经用户明确取消；不能仅从台账删项。
8. handbook、CURRENT、CODEBASE_MAP、task、handoff、部署模板与当前代码事实一致。
9. 根仓全链门禁覆盖上述跨仓要求，而非只覆盖各仓 happy path。

## 2. 当前基线

### 2.1 已提交本地 HEAD

| 仓库 | HEAD | 当前事实 |
| --- | --- | --- |
| 根仓 | `39b02f2` | ahead origin 31；Round-4 后 gitlink 尚未提交 |
| agent | `2181938` | AGENT-MCP 已提交；ahead origin 17 |
| platform | `f0f3c62` | HUB-4 + AUTH-2 已提交；ahead origin 12 |
| session | `074e0c7` | M-6 已提交；生成镜像有未提交变更 |
| web | `5c937ef` | `agent/p2-auth-wiring`；WEB-3 已提交；生成镜像有未提交变更 |

### 2.2 当前在手但未实现的契约

根仓 `contract/spec/http.yaml` 已增加 `GET /sessions`、`SessionListItem`、`SessionList`，
session/web 镜像已生成且 `contract/check.py` 通过；store、route、client、rail 水合尚未实现。
该状态只能称“契约草稿完整”，不能称 SESS-LIST 已落地。

### 2.3 已证实的系统缺口

- Hub 路由没有内部鉴权，namespace/scope 直接来自请求。
- credit 启用 internal-secret 后，session billing client 不带密钥。
- Hub、session、agent 默认 Mongo DB 不同；session 池解析又忽略审核和运营排序。
- web 任意邮箱直登、token 存 localStorage；magic-link 默认把原文 token 写日志。
- credit owner 正缓存键缺少 `siteId`。
- request/control 在 durable claim/inbox 前 ACK。
- agent terminal 在事件发布前消耗终态权；关键状态帧发布失败可直接丢弃。
- session control 在 publish 前记录完成；billing settle/release 失败没有持久重试。
- 根仓未 pin Round-4 四子仓 HEAD，文档状态落后一轮。

## 3. 长期边界

以下边界在所有子项目中保持不变：

- `siteId` 是 platform 业务隔离轴；`namespace` 是 runtime 唯一隔离轴。
- `namespace` 是不透明空间 id，V1 等于已验证的 team id，不加业务前缀。
- browser 不直连 agent、Hub、credit、user 或 model；终端请求只到 web 同源 BFF。
- session 拥有会话、run、HITL、浏览器事件投影和运行计费 saga。
- agent 拥有模型/工具/子代理执行、checkpoint、memory、sandbox 和运行侧 durable inbox/outbox。
- Hub 是 skills/MCP 管理和池解析权威；agent 只按会话快照读取确定版本包体/注册表。
- MySQL 是平台业务和账务真源；Mongo 是 runtime、Hub 元数据和持久意图真源。
- Redis 是至少一次传输和 live fanout，不是完成证明或长期真源。
- payment 不写 credit ledger；agent 不计费；model 不决定最终价格。
- 根 `contract/spec/*.yaml` 是跨仓 wire/HTTP/storage 单源，生成镜像禁止手改。

## 4. 核心设计决策

### D1. 开发身份直接切换，不保留错误兼容轴

现有 dev-login 用原始邮箱作为 `external_user_id`，magic-link 使用
`email|<normalized-email>`。默认把前者视为开发数据，切换时清理，不增加双查、别名或永久兼容层。
若后续确认存在必须保留的数据，另写一次性迁移，不把兼容分支留在请求热路径。

### D2. 内部服务默认拒绝，并区分调用方等级

platform 服务采用 default-internal 路由策略，并给每条路由声明唯一访问等级：

```text
public            health、公开站点元数据、provider webhook（另验 provider 签名）
runtime-internal  session/agent 等运行时服务
web-bff           终端 web BFF
admin             platform-admin（先做 operator RBAC）
```

`x-kokoro-internal-secret` 只能证明调用方服务身份，不能替代用户/成员授权。请求同时携带
`x-kokoro-service`，各调用方使用不同 secret；路由按 allowlist 接受 caller。OpenAPI 在生产默认
internal。user 的 magic-link 申请/消费只开放给 web-bff，浏览器不能直打 user 服务。

测试构造器可以显式启用 insecure local，生产 main 缺少该进程所需 caller credential 必须启动失败。
不能继续用一个共享空 secret 静默直通，也不能让持有 runtime credential 的服务调用 admin 路由。

### D3. web BFF 持有浏览器会话，浏览器不持有 bearer

magic-link 消费成功后，web BFF 用独立的 `KOKORO_WEB_SESSION_SECRET` 把服务端返回的
`{runtime_jwt, user_id, namespace, site_id, exp}` 签名并加密为会话信封，再放入
`HttpOnly + Secure(production) + SameSite` cookie。namespace/site 只能来自 user 服务的
consume 响应，绝不接受浏览器提交，也不通过未验签 decode JWT 得出。

Wave 1 使用 BFF 服务端固定 `KOKORO_SITE_ID`；magic-link 请求体不接受浏览器 `site_id`。
`SITE-REAL` 落地后仅把固定值替换为可信 host→site resolver。`user_id` 只供 web/platform 的
团队、邀请和成员授权使用，永不进入 session/agent runtime contract。

web 的 session catch-all 代理读取信封、向 session 注入 `Authorization: Bearer`，并透传
HTTP、SSE、文件与成果流。Hub BFF 从同一可信信封取 namespace，并带 internal-secret 调 Hub。
浏览器端 client 只访问同源 `/api/session/*`、`/api/hub/*` 等 BFF 路径。

cookie 明确使用 `SameSite=Lax`、`Path=/`，max-age 不超过 JWT exp；生产强制 Secure。
会话密钥支持 current+previous 两把短轮换，写只用 current、读可用两者。mutation 代理校验同源
Origin；退出登录以同 path 立即过期 cookie。这同时解决 localStorage token 泄露和“httpOnly
cookie 无法由浏览器 JS 加 Bearer”的旧规格矛盾。

登录发起时 BFF 设置一次性 HttpOnly nonce，并把其哈希绑定到 magic-link；callback 必须匹配后才
consume，防 login CSRF。callback 立即 303 到无 token URL，响应设 `Referrer-Policy: no-referrer`；
web、反代和访问日志必须按路由删除 query/token，错误日志只留 requestId。

V1 有意限制为“发起登录与打开邮件是同一浏览器”。nonce cookie 丢失、过期或在另一设备打开时，
BFF 不消费 token，统一返回 `auth_link_unavailable`，页面只提供重新发送入口，不区分 nonce、token
或邮箱是否存在。用户在当前浏览器重新输入邮箱并申请新链接即可恢复；旧链接按原 TTL 失效。
浏览器验收必须覆盖同浏览器成功、跨设备/无 nonce 失败、重新申请成功和错误不泄漏账号存在性。

### D4. Hub API 是唯一池解析器，并拆分三类权限面

session 在首条消息创建能力快照时，以已验证 namespace 通过内部客户端调用 Hub：

```text
Hub runtime resolver(namespace) -> SkillGrant[] + versioned McpGrant[]
session persist immutable capability snapshot
agent consume snapshot -> read exact scope/name/hash and MCP records
```

session 不再直接查询 `skills/skill_state`，从而删除第二套 review/pinned/weight 语义。已有会话继续使用
不可变快照；Hub 短暂不可用只阻止新会话首次快照，不影响已存在会话继续运行。

Hub 与 agent 必须显式使用同一 Mongo URL/DB 和包体配置。部署模板与 closure/e2e 必须启动 Hub，
不得靠测试夹具把 split-brain 隐藏掉。

Hub 路由分为互不混用的三类：

- runtime resolver：只接受 session 的 runtime caller，按已验 JWT namespace 返回有效池。
- namespace self-service：只接受 web-bff；BFF 从密封信封取 `user_id/namespace`，先经 user 服务
  校验 active membership。读取允许 active member，启停/上传/删除要求 owner/admin。
- official/admin：只接受 platform-admin caller，审核、curation、official flags 和跨 namespace
  操作仍由 operator RBAC 决定。

self-service 路由不接受任意 `scope`；BFF 与 Hub 都强制 `scope=sealed namespace`。TEAM-1 未落地前，
personal team 的 owner membership 已足够授权；TEAM-1 后沿用同一 authorizer，不改 Hub 契约。

`HUB-AUTHZ` 首次开放 namespace self-service 时只开放 skill 读写和 MCP 只读；MCP register/update
必须以 `capability_registration_disabled` fail-closed。只有 `MCP-REVISION`、`MCP-SECRET`、
`HUB-CONSIST` 及 Hub→session snapshot→agent connector 跨仓 E2E 全部通过后，同一部署门才可开启
namespace MCP mutation，避免写入新 revision/secret handle 时仍有旧 names/live-doc 消费路径。

MCP 不再只快照 name。`McpGrant` 至少包含 `{scope,name,revision,config_hash}`；定义修改创建
append-only revision，旧会话继续读原 revision，新会话拿新 revision。安全状态是显式例外：当前
definition 被 disable/revoke 时，旧 grant 也 fail-closed；secret handle 轮换实时生效但不改变 URL、
transport 或 allowed tools。测试必须分别覆盖“配置版本锁定”“紧急撤销”和“secret 轮换”。

namespace self-service 注册 MCP 时禁止 `env:VAR`，只允许属于该 namespace 的 opaque secret
handle。`env:` 仅允许 admin/official 定义引用部署 allowlist 中的变量。MCP-UX 开工前必须先交付
`MCP-SECRET`：窄 secret broker、加密存储/KMS port、namespace 绑定、runtime caller 读取、全链
日志脱敏。secret 明文不进入 Hub/Mongo 文档、session 快照或 agent ledger。

self-service URL 生产只接受 HTTPS。注册和每次连接都执行 egress policy：DNS A/AAAA 全量解析，
拒绝 loopback/private/link-local/multicast/metadata 网段；禁止重定向，或逐跳重新校验；连接器防
DNS rebinding。站点可再配置域名 allowlist。localhost/http 只允许显式 test profile。

### D5. 可靠性统一使用持久意图，而非零散重试

所有跨进程副作用遵循同一模型：

```text
Mongo durable intent/inbox/outbox
        -> Redis at-least-once delivery
        -> receiver durable claim/inbox
        -> idempotent apply
        -> reconciler advances terminal state
```

合法帧只有在 durable claim/inbox 成功后才能 ACK。无法认证或无法解析出可信
`run_id/event_id/durable_seq` 的 transport 噪声，可在 durable DLQ 记录 raw hash、来源和原因后 ACK；
任何已识别 durable identity 的 critical frame 都必须先进入 inbox 或 durable quarantine，数据库不可用
时不得 ACK。live publish 可以重建，不得作为持久状态成功的前置条件。

request 的投递竞争由根 storage contract 定义的 `run_dispatches` 单文档 CAS 决定：
session 写 `pending + deadline + fence`；agent 仅能在 deadline 前把 pending 原子改为 claimed；
session 超时
只能把仍为 pending 的记录改为 expired。claimed 获胜后，session 不得宣告 dispatch_exhausted 或
释放 hold；expired 获胜后，任何晚到 Redis request 都不能启动执行。claimed run 后续由
owner/lease/heartbeat/fencing 和 `reclaim_expired` 从 request/checkpoint 接管。

`run.started` 的最小 durable outbox/receipt 属于 R1，不等待通用 terminal outbox。session 只有在
dispatch CAS 为 expired 时拥有合成 dispatch 失败终态的权力；claimed 后终态权归 agent。

每个 critical durable event 使用独立于 live/UI `index` 的 per-run 连续 `durable_seq`，从 1 开始；
terminal 携带 `terminal_seq`。agent durable outbox 只发布尚未证明 persisted 的最小 seq，前一个
event 经 session receipt 确认后才允许发布下一个。session 分别维护
`highest_persisted_durable_seq` 与 `highest_projected_durable_seq`：前者只在连续
durable slot 已由 accepted inbox 或 quarantine 占据时推进；后者只允许 CAS 应用
`current + 1`，并在该事件的业务投影或显式 no-op 成功后推进。normal terminal 分配时以 CAS
设置 `terminal_fence_seq`，allocator 从此禁止再分配更大 seq。finalize 要求 persisted watermark
至少到 fence、projected watermark 恰好到 fence。live frame 不占 durable_seq，因此可丢的
token/update 不会制造伪缺口。

已识别 identity 但 schema/version/payload 不可应用的 critical frame 进入 durable quarantine，
receipt 状态为 `rejected`，不得伪装成正常事件已 persisted；quarantine 自身仍占据该 durable
slot。该 seq 由 session 的 contract-failure reconciler 原子投影为
`run.failed contract_incompatible` 并成为 terminal_seq；这是 session 除
dispatch expire 外唯一可取得 terminal 权的异常。agent 查询到 rejected 后停止执行并消费该
NACK。基础 envelope、
quarantine receipt 与 contract-failure 形状必须跨滚动升级窗口向后兼容；无法识别基础 envelope 的
帧只进 DLQ，不能关联或推进任何 run。

contract failure N 把权威 `terminal_fence_seq` 原子收窄为 `min(existing, N)`。agent 同步 fence、
停止分配/执行，把本地已排队的 `seq > N` 原子改为 superseded，并在 ledger 留 compact range/hash
后删除 payload，永不发布。session 把已乱序持久化或随后到达的 `seq > N` inbox/receipt 标为
superseded，永不投影；persisted watermark 可高于 fence，但 projected watermark 必须停在 N。
manifest 暴露 fence 与 superseded range，使双方可在 N 的 NACK consumed 后忽略整个后缀。

receipt 使用 producer manifest 与两阶段回收。session 暴露仅供 agent runtime caller 的
per-event GET、幂等 POST consume 和 per-run manifest；manifest 至少保存三个连续 watermark：
persisted/projected/consumed，以及 terminal_fence_seq、superseded range 与 producer_closed。
agent 在发
consume 前先把本地 outbox 原子改为 `consume_requested`，POST 成功或 manifest 证明
`seq <= highest_consumed` 后才硬删除。consume 必须按 seq 顺序推进并校验 event_id/hash。

session 可在 terminal 已投影且 finalized 后删 event stream/payload，但 receipt manifest 在
agent 确认 terminal fence event/NACK 已 consumed、suffix 已 compact、无可发布 outbox，并发送
幂等 `producer_close` 前不得 GC。close 发出前 agent 先持久化 `producer_close_requested`；
session 成功后才设 producer_closed。
close 前的 404 是 `receipt_state_lost`，agent 不得删 outbox，并必须告警；close 请求后的
404/410 表示已关闭，可安全收口。
这样 consume/close 响应丢失和 agent 长期离线都不会把状态变成不可判定。

control 同理：agent inbox 持久化后把 `persisted`、checkpoint 后把 `applied` 作为 critical event；
session receipt store 驱动 control 状态，pending scanner 负责重启续办。Redis XADD、流存在或
live publish 都不能成为 outbox 清理条件；control receipt 也遵守相同 query/consume 回收协议。

### D6. 外部工具副作用采用 unknown-outcome 语义

“唯一副作用”只承诺 Kokoro 自有 Mongo/MySQL 状态和支持稳定 idempotency key 的下游。外部 MCP/
tool 写操作在“远端成功、checkpoint 未提交”窗口无法证明恰好一次。

执行前以稳定 tool_call_id 写 effect journal=`started`，成功结果写 `completed`。takeover 命中
completed 直接复用；命中 started 但无结果时不得自动重放，进入 `unknown_outcome` HITL，提示用户/
operator 核对后选择视为成功、补录结果或显式重试。支持幂等键的下游继续自动收敛。

### D7. 不造通用工作流框架

持久状态嵌入现有 run/ledger 文档，使用单文档 CAS 和已有幂等键；只在确有独立生命周期时增加
窄 collection。V1 不引入 Kafka、Temporal 或跨库分布式事务。

### D8. 同仓并行只通过独立 worktree

根契约变更串行；同一子仓多个写面必须在子仓内使用独立 worktree。主工作树的用户修改和
`.gitwarp/` 不得被清理、移动或纳入提交。每个 worker 完成后由主控在目标合流分支重跑验证。

## 5. 目标数据流

### 5.1 登录与 runtime 请求

```text
browser -> web /api/auth/magic-link/request
        -> BFF adds trusted site + web-bff credential -> user -> SMTP
browser -> web callback(token)
        -> BFF credential -> user consume
        -> {JWT(sub=teamId, iss, site_id, exp), user_id, namespace}
        -> web seals {JWT, user_id, namespace, site_id, exp} into httpOnly cookie
browser -> web /api/session/*
        -> BFF injects Bearer -> session verifies sig/iss/site_id/sub
browser -> web /api/hub/*
        -> BFF uses sealed namespace + internal secret -> Hub
```

`/auth/sessions` 仅供受保护的内部/测试迁移调用，不能再成为任意身份签发 oracle。

### 5.2 会话与执行

```text
session persist run + CAS dispatch(pending, deadline, fence)
  -> Redis run.request
  -> agent CAS dispatch pending->claimed, durable lease, then ACK
  -> execute/checkpoint
  -> critical event/terminal outbox(durable_seq, strict head-of-line)
  -> Redis event stream
  -> session advances persisted watermark, then projects only next seq through fence
  -> agent records consume_requested, consumes receipt, then clears local outbox
  -> after terminal consumed: producer_close -> receipt manifest GC
  -> SSE/live + snapshot replay
```

dispatch CAS claimed 后进入 confirmed；重发相同 `run_id/fence` 不得二次执行。
agent 在 ACK 后执行中崩溃时，lease 到期由存活 worker fencing 接管，并从原 request/checkpoint 续跑。
`run.started` 作为 R1 的首个 critical outbox frame；session 持久后可供 receipt endpoint 查询，
它仍不进入 browser projection。

### 5.3 HITL control

`decision_id` 必须进入 control wire。session 先存 command outbox，再发布；agent 先存 inbox 后 ACK，
以 `decision_id + interrupt fingerprint` 保证只应用一次。session 不得把“已记录”误当成“已发布/已应用”。
agent 必须把 `run.control.receipt{decision_id,status}` 作为 internal-only critical event，分别回传
`persisted` 与 `applied`；重启 scanner 继续所有非 applied command。session 持久 receipt 后，
agent 经内部 receipt query/consume 握手清理自己的 event outbox。control stream 只有在 terminal
连续性门通过且 command/receipt 均收口后才能删除。

### 5.4 终态与计费

agent 终态先原子选定 payload 和稳定 index/event_id/durable_seq/terminal_fence，再由 outbox 发布。session
append 后，内部 receipt endpoint 对该 event_id 返回 persisted；agent 完成 consume 或 manifest
证明前保留本地记录。session 收到 terminal 后，先按 durable_seq 逐个投影；persisted/projected
分别满足 `>= terminal_fence` 与 `== terminal_fence` 才推进，fence 后缀永不投影：

```text
projection: terminal_recorded -> projected -> finalized
billing:    held -> settle_pending|release_pending -> settled|released
```

业务终态不等于 saga 已完成。reconciler 必须扫描未 finalized 的 terminal run，直到 projection、active
slot、pause/message、billing 全部收敛。credit TTL sweeper 只是最后保险，不是成功证明。
event stream 可在 terminal 连续投影且 projection finalized 后由 session 删除；receipt manifest
保留到 producer_close。agent 的 terminal outbox 与 superseded suffix 无论 relay 是否仍在，
都可通过 receipt query/consume/manifest 清理；close 握手完成后 session 才能回收 manifest。

## 6. 项目分解与依赖波次

### Wave 0：状态封存与事实台账

交付：

- session/web 生成镜像提交。
- 根仓一次提交契约源、生成 README 和四个新 gitlink。
- `DOC-AUTHORITY`：先修 handbook 21、20/22 状态、CURRENT 指针中被本文点名的错误，消除事实源
  优先级冲突，再允许生成 Wave 1 子 spec/plan。
- `ROUND4-EVIDENCE`：补 AGENT-MCP 真注册表 e2e 和 WEB-3 真 MCP elicitation Playwright；两项通过后
  才把 Round-4 从“代码已提交、证据待补”改为已收口。
- Round-5 标为失败且零 lane 落地，保留 SESS-LIST 契约草稿的真实状态。
- 全量刷新 `docs/task.md` 事实描述，把代码审计发现的新 P0（trust、Hub split-brain、durability、
  cache）纳入，并逐条校正已完成/未完成状态。
- 关闭已完成的 storage.yaml 运营字段项，修正 Hub README/Mongo 注释中的“待收编”，删除已被
  生成单源取代的手写 mirror/TODO。
- 确认所有本地提交可被目标远端获取后，才允许发布根 gitlink。

Wave 0 不改变运行行为，但它是所有 worktree 和后续合流的共同基线。

### Wave 1：安全与能力基础

拆成八个有显式依赖的子项目：

1. `TRUST-ROUTES`：platform default-internal 访问等级、per-caller credential、调用方接线、
   生产 fail-closed 与完整路由矩阵。
2. `CREDIT-CACHE`：owner cache 改 `(siteId, ownerKind, ownerId)`，独立负向测试。
3. `AUTH-P0`：服务端可信 site、SMTP、magic-link web 流、密封 cookie、session BFF、JWT
   iss/site 校验、user principal、nonce、callback/日志脱敏。
4. `HUB-AUTHZ`：runtime/self-service/admin 三权限面、membership authorizer、scope 强制；
   namespace MCP mutation 初始保持 fail-closed。
5. `MCP-REVISION`：先串行冻结根契约中的 append-only config revision、McpGrant
   revision/hash、旧会话锁定与实时撤销。
6. `MCP-SECRET`：namespace opaque secret handle、secret broker、SSRF/egress connector、
   日志脱敏；通过后仍保持 namespace MCP mutation 关闭。
7. `HUB-CONSIST`：消费已冻结的 versioned McpGrant，完成同库部署、session HttpSkillPool、
   skills/MCP 快照统一；跨仓 MCP E2E 通过后才开启 namespace mutation。
8. `MODEL-SOURCE`：session `profile.allowed` 降为展示过滤，platform resolve 成为可用性权威。

`TRUST-ROUTES` 先冻结内部调用契约；其后 AUTH 与 Hub 可跨仓并行。Hub 链内部顺序固定为
`HUB-AUTHZ -> MCP-REVISION contract -> MCP-SECRET -> HUB-CONSIST`，根契约由主控串行修改。
Wave 1 负向测试必须证明 HUB-CONSIST 跨仓门前 MCP 写入始终返回 503，开门后仍拒绝 env ref、
私网/metadata、DNS rebinding、redirect 和跨 namespace handle。每个子项目同时修改并验证自身需要的
closure-up、compose、K8s、CI 和环境模板，不能把可运行性推迟到 Wave 6。任何用户态产品 API
都必须等待 AUTH/TRUST 的负向测试通过。

### Wave 2：runtime 与 billing 可靠性

按以下顺序拆 spec/plan：

1. `R0` 故障注入护栏：先写当前必红测试，不改行为。
2. `R1` 共享 run_dispatch CAS、deadline/fence、agent durable claim 后 ACK、最小
   `run.started` outbox、durable_seq 与 receipt manifest/query/consume/close contract；保留
   lease/heartbeat/fencing/checkpoint takeover。
3. `R2` control outbox/inbox，`decision_id` 进入根契约，pending scanner 与
   internal-only `run.control.receipt` 的 persisted/applied 闭环。
4. `R3` tool effect journal；unknown-outcome 不自动重放，支持 idempotency key 才自动收敛。
5. `R4` agent critical event/terminal outbox，严格 head-of-line、first-terminal fence、
   consume_requested 与 close 握手。
6. `R5` session persisted/projected 双水位、superseded suffix、quarantine/NACK、
   projection/finalization reconciler。
7. `R6` billing hold journal，解决 hold 成功但 handle 未落库与 enqueue failure。
8. `R7` billing settle/release durable compensation、告警和 hold 临期策略。

R4 与 R5 可跨 agent/session 并行；R5/R6 都改 session run schema，必须串行合流。

### Wave 3：用户可感 P0

1. `SESS-LIST`：owner 隔离分页、复合 cursor、软删过滤；web rail 服务端水合，本地只保留 UI 偏好。
2. `WEB-BILLING`：credit 窄读 summary/ledger；session 从 auth namespace 派生账户并代理；余额、流水、
   402 专用说明与价格/联系入口。真实购买在 PAY-2，P0 不放假充值按钮。
3. `WEB-SKILLS`：认证 BFF、池列表、required lock、启停、配额、上传 preview/confirm、版本/审核状态、
   pinned 接线。

三项必须各自形成后端、BFF/client、UI、真实浏览器验收的完整竖切，不接受“只交 API”或“只交 UI”。

### Wave 4：既有 P1 遗留

逐项保持在总目标内：

- `TEAM-1`：使用密封信封中的 user principal 完成邀请、消费、成员权限、active membership、
  团队换签和 web 团队切换；user principal 永不下传 runtime。
- `MCP-UX`：依赖 Wave 1 的 MCP-SECRET + MCP-REVISION；连接向导、启停、enabled pool
  自动进入新会话快照。
- `MODEL-UX`：平台模型候选、web 选择、M1 单源收口。
- `AGENT-PRESET`：目录即配置的 preset、session 首条锁、agent 选择 UX。
- `ARTIFACT-LIB`：按 namespace/content_hash 的跨会话作品库。
- `PAY-2`：真实 provider 验签、Subscription 写路径、refund provider 回链、价格页购买流。
- `SITE-REAL`：host→site、域名验证、品牌注入，删除单站点常量依赖。
- `OBS-1`：session/agent metrics/tracing、卡死与计费补偿告警。
- `SEC-2`：RS256/JWKS、magic-link Redis 限频、service credential/secret broker 轮换硬化。
- `SHARE-1`：有权限、可撤销的会话只读分享。

每项独立 spec/plan；支付、站点、团队、观测不得混进一个 lane。

### Wave 5：P2 与产品质量遗留

- `CONV-UX`：会话重命名。
- `HITL-NOTIFY`：待批通知。
- `ERROR-UX`：run.failed 分类文案与恢复引导。
- `WEB-THEME`：暗色模式。
- `WEB-MOBILE`：移动端主路径。
- `ADMIN-MANIFEST`：admin-web manifest 元数据驱动页面。
- `I18N-REVIVE`：admin-web i18n 与 `kokoro-i18n` 恢复。
- `SESSION-FLAKE`：session 并发时序根治。
- `M6-SNAPSHOT`：snapshot.messages 双份传输另一半。
- `SWARM-QUOTA`：swarm 与组织级配额。

以上每项分别形成单一 owner 的子 spec/plan，不以“P2 尾巴”合并派工。

### Wave 6：文档、部署与发布收口

- 新增 technical/23 platform 运营台事实册。
- 将 web 三栏/Canvas/四卡收编正式册。
- 对 Wave 0 已纠偏的 handbook 再做全册事实审计，更新 09/15 等剩余状态。
- 更新 CURRENT、docs README、00 指针、CODEBASE_MAP（含 Hub）、modules/platform README。
- 修复 contract README 事件数量硬编码。
- 审计各 Wave 已随功能提交的 closure-up、compose、K8s、CI，补跨栈发布总门禁。
- 清理 tmp/closure 中间物，但不得删除用户仍在使用的 `.gitwarp/`。

## 7. 错误与恢复语义

| 场景 | 对外语义 | 持久状态 |
| --- | --- | --- |
| 未登录/坏 cookie/JWT | 401；清 cookie 后回登录 | 不创建 run/session |
| magic-link 无 nonce/跨设备/过期 | 400 auth_link_unavailable | 不消费 token；允许重申请 |
| 访问其它 namespace 的资源 id | 404，防枚举 | 不访问目标数据 |
| 当前 namespace 内角色不足 | 403 | 不执行写操作 |
| Hub 不可达（新会话） | 503 capability_unavailable | 不创建半快照 |
| credit 受理不可达 | 503 billing_unavailable | 不创建 run；active slot 必须清理 |
| 余额不足 | 402 credit_insufficient | 不发布 request |
| Redis request publish 暂时失败 | 202 dispatch_pending | intent pending，后台重试 |
| dispatch expire CAS 获胜 | run.failed dispatch_exhausted | release pending 后终态 |
| 超时检查发现 dispatch 已 claimed | 继续 active，不报发送失败 | lease/fencing 接管 |
| control 已持久但未发布 | 202 control pending | outbox pending 自动重发 |
| critical publish 失败 | agent outbox pending 自动补发 | 固定 event_id/durable_seq |
| schema mismatch | run.failed contract_incompatible | quarantine/NACK |
| live publish 失败 | snapshot/replay 仍完整 | 不回滚 projection |
| settle/release 失败 | run 可向用户终态，但 billing pending 告警重试 | 不静默过期 |

计费受理返回 503/402 时，HTTP 返回前必须清 active slot；若清理本身失败，持久 admission cleanup
intent 由 reconciler 完成，但对外仍是同一个拒绝结果。dispatch intent 使用可配置
`KOKORO_DISPATCH_MAX_AGE_MS`（默认 15 分钟）；只有 pending→expired CAS 获胜才产生一次
`dispatch_exhausted` 并进入 billing release。若 agent 已把同一 fence claim，超时方不能再写失败
终态；旧 Redis request 在 expired tombstone 后到达也必须被 agent 丢弃。

control POST 返回 `{ok, decision_id, status}`，status 为 `pending|persisted|applied|failed`。
新增同属主 GET receipt 端点按 decision_id 返回状态；形状校验、stale pause、权限失败在创建 outbox
前同步返回 4xx。publish 故障仍返回 pending receipt，web 可查询或等待状态事件，不得误报 applied。

禁止把 secret、magic-link token、JWT、MCP 凭据、原始 provider payload 写日志或错误响应。

## 8. 验证体系

### 8.1 每个子仓

- agent：pytest、pyright、ruff；Mongo ledger 与 Redis consumer 故障矩阵。
- session：unit/integration、typecheck、lint；Mongo 双后端语义和 reconciler 重启测试。
- web：unit、typecheck、lint、build；真实浏览器覆盖登录、SSE、列表、计费、能力、团队。
- platform：各 workspace unit/integration/typecheck/lint；MySQL/Mongo/MinIO 真件。
- contract：生成检查、镜像漂移、golden、事件/端点计数动态生成。

### 8.2 跨仓强制场景

1. magic-link 真 SMTP fixture → cookie → session BFF → 发消息 → SSE 终态；跨设备/无 nonce
   统一失败且在当前浏览器重申请后成功。
2. per-caller credential 启用下 model resolve、hold、settle 全链成功；缺/错 caller 或越级路由全拒绝。
3. Hub 上传/审核/启停 → 新 session snapshot → agent 精确 hash 读取；rejected 永不执行。
4. site A 暖缓存后，site B 同 owner id 仍重新校验并拒绝串站。
5. request/control/terminal/billing 每个故障注入点重启后自动收敛。
6. SESS-LIST 换浏览器仍可见；跨 owner 不可枚举。
7. 402 UI、技能上传/启停、团队换签均走真实后端，不使用 mock 完成验收。
8. 根仓 `verify-all`、closure-up、compose/K8s smoke 在新 clone 上通过。
9. Hub 注册/禁用/覆盖 MCP → 新会话快照 → agent 三工具面调用真实 MCP server。
10. WEB-3 `kind=input` 通过真实 MCP elicitation 在浏览器完成 submit/reject 与重问。
11. 浏览器伪造 site/namespace/scope/user_id 均被拒；BFF 固定 site，
    self-service 强制本 namespace。
12. member 可读池但不能上传/启停，owner/admin 可管理；web-bff 不能调用 official/admin 路由。
13. MCP mutation 在安全门前返回 503；开门后仍拒绝 env ref、私网/metadata、DNS
    rebinding/redirect，secret handle 不跨 namespace。
14. MCP 定义改版时旧会话锁原 revision，新会话取新 revision；disable/revoke 对旧会话立即生效。
15. MCP-SECRET 已部署但 HUB-CONSIST 未通过时 mutation 仍为 503；通过跨仓 E2E 后才开门。

### 8.3 可靠性故障矩阵最低集

- request 读出后 claim 前、claim 后 ACK 前、XADD 后 dispatch 状态落库前。
- deadline 前后 pending→claimed 与 pending→expired 并发；expired 旧请求永不执行，claimed 不被误释放。
- agent ACK 后执行中崩溃、checkpoint 前后崩溃、lease 被新 worker takeover。
- control outbox 落库前后、agent inbox 后 apply 前、checkpoint 后 applied 标记前、
  pending scanner 重启。
- terminal intent 后 publish 前、publish 后 receipt 前、Redis 流丢失后 producer 重发。
- 中间 critical durable_seq 丢失而 terminal 先到时不得 finalize；补齐后只 finalize 一次。
- seq N append 后 project 前崩溃、N+1 已持久时，恢复后仍只按 N、N+1 顺序投影。
- 可信 durable identity 但 schema/version 畸形时先 quarantine 再 ACK，以 contract_incompatible
  唯一收口；无可信 identity 的噪声只进 DLQ，不推进 run。
- terminal M 已在本地排队或乱序持久化后 seq N 被 rejected 时，fence 收窄到 N，双方将
  `seq > N` 标为 superseded；只投影到 N，并能完成 receipt/producer-close GC。
- session append 后 receipt 丢失，agent 重发相同 event_id 且 projection 只执行一次。
- receipt query/consume 响应分别丢失时两端幂等重试；consume 响应丢失后 agent 离线超过普通
  run retention，恢复时仍由 manifest highest_consumed 确认并清理。
- producer_close 响应丢失时重试安全；close 前 manifest 404 必须告警且不得静默删 outbox。
- session finalized/relay 关闭且双端重启后，agent 仍从 receipt manifest 清理 outbox。
- session event append 后 project 前、terminal mark 与 active clear 之间。
- 外部写工具远端成功但 checkpoint 前崩溃时进入 unknown_outcome，不自动产生第二次调用。
- hold 成功后 handle 落库前、enqueue 永久失败、settle/release 响应前后。

每个场景都必须断言最终业务状态、唯一副作用、余额和可观察告警，不能只断言进程没崩。

## 9. 迁移与回滚

- MySQL 迁移只允许 additive/expand-contract；共享 `_prisma_migrations` 禁止 `migrate dev/reset`。
- Mongo 新字段先读侧 backfill，再逐步强制；关键 saga 字段必须有显式初始值。
- auth 切换默认清理 dev identity 数据；生产数据迁移需单独审批和 dry-run。
- 新 BFF、Hub reader、durable dispatcher 以环境开关分阶段启用，但开关只用于迁移，稳定后删除旧路。
- 回滚不能恢复任意邮箱直登、空 internal-secret 生产直通或未审核 skill 执行。

## 10. 并行与合流纪律

- 根契约、根 gitlink、task/handoff 由主控串行修改。
- platform 的 trust、auth、Hub、credit cache 如并发，必须各自 worktree；合流后跑 platform 全量。
- session 的 auth/Hub reader 与 runtime/billing saga 不能在同一工作树并写 store/main；
  按 Wave 先后合流。
- agent 的 request/control 与 terminal outbox 可在契约冻结后分 worktree，但最终由同一
  ledger 行为矩阵审查。
- web 在 `agent/p2-auth-wiring` 基线上工作；BFF 先落，产品页面随后分区，合流后统一 Playwright。
- worker 的测试数字不是完成证据；主控在合流分支和根仓重新验证。

## 11. 项目完成审计

最终关闭目标前，主控按 `docs/task.md` 每一条 P0/P1/P2/DOC 项建立证据表：实现 commit、权威测试、
运行截图/HTTP 证据、文档状态。任何一项证据缺失、仅有间接 e2e、或被 feature flag 永久关闭，
都保持未完成。

本文获批后先只生成并执行 Wave 0 implementation plan；`DOC-AUTHORITY` 与共同基线门通过后，
再为 Wave 1 的独立单元逐份生成 spec/plan。后续 Wave 同样在前置门通过后依次设计和执行，
不允许重新退回“一个 workflow 五个大 lane”的派工方式。
