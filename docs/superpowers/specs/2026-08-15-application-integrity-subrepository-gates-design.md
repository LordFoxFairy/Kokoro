---
artifact: architecture-decision-spec
version: "1.2"
created: 2026-08-15
status: frozen
scope: kokoro-application-integrity-and-promotion-gates
---

# Kokoro 应用完整性与子仓晋级门禁

## 0. 裁定与证据

本文自 2026-08-15 起生效，是 PostgreSQL 完整性归属、独立 Git 子仓、clean replace、子仓闭环、RPC 联调和系统 E2E 的覆盖性裁定。规则优先级为：当前用户裁决 > 本文 > 2026-08-13 两份架构规范 > 当前实现。旧规范中未冲突的 owner 边界、事务归属、跨仓 Protobuf RPC 和仓内直接调用原则继续有效。

冻结输入：

| 输入 | SHA-256 |
|---|---|
| `/private/tmp/kokoro-postgres-no-fk-audit.md` | `0860df403aeb30a044cc2c3c7058378668db7a3b42c317b5a94df9bebe088373` |
| `/private/tmp/kokoro-prisma-alibaba-schema-audit.md` | `3d990dc040dacaf64261f76e078937edf965d317a8765a1a695cc2938a4376ad` |

本文件是规则冻结，不是测试报告；本文预置的测试任务当前全部为 `NOT_STARTED`，不声明任何实现已通过。

## 1. 对旧规范的覆盖

| 旧规范冲突 | 本文裁定 |
|---|---|
| Canonical data model §0.1 的 forward migration、增量 FK 模型 | 未发布产品执行 clean replace，只从空库安装新 baseline |
| §2.2 的稳定关系 FK、composite FK、constraint trigger | 关系由 owner application service、UoW、lock/CAS、UNIQUE 和审计闭环 |
| §2.3 的 `ON DELETE RESTRICT/CASCADE` 与旧删除口径 | 数据库零级联；可删除 aggregate 使用统一软删除协议 |
| 各逐表 FK 描述、§12 FK catalog 完成条件、§13 Root 全 FK CI | 改为零 FK catalog、owner integrity audit、权限和并发门禁 |
| 单一 `kokoro_app` 全表可写 | 改为每个服务独立 logical database、migrator role 与 runtime role；Root 不持有服务 DDL authority |
| SQL-first 规范以 FK/trigger 为前置权威 | 应用完整性为权威，数据库只保留本文 SQL 白名单 |
| Root canonical baseline、`99-cross-capability-relations.sql`、child scalar + Root physical FK | 每个独立服务仓拥有自己的数据库和 migration；删除跨 owner 物理关系，跨仓只走冻结 RPC 与不可变快照/显式 claim |
| Root 集中保存全部服务 Proto、生成产物和测试 | 服务提供方拥有自己的 RPC Proto/生成配置；consumer 拥有真实 pair 测试；用户/Admin Web 各自拥有浏览器 E2E |
| legacy adapter、旧 Session 业务术语、旧 DTO 和 feature flag 旧路径 | clean replace 不保留旧运行路径或兼容层 |
| 先整条 E2E 再提升 | 改为子仓报告 `APPROVE` -> RPC pair 报告 `APPROVE` -> 系统 E2E 报告 `APPROVE` |

机器契约已经正式冻结的部分继续受现有 manifest/descriptor 约束；本文不借 clean replace 重开已冻结 wire number。

## 2. SQL 能力边界

业务 schema 仅允许：

1. 单表主键 `PRIMARY KEY`。
2. 业务唯一和幂等唯一 `UNIQUE` / unique index；并发仲裁不能只靠应用预查。
3. 只读取当前行、无跨表查询、无时序副作用的 simple `CHECK`。
4. 为已证明查询模式服务的普通 index。

业务 schema 必须保持：零 `FOREIGN KEY`、零数据库 cascade、零关系 trigger、零业务状态 trigger。禁止用 PL/pgSQL、可查询函数、物化视图刷新或另一种跨表 constraint 复刻上述能力。删除只为旧 FK candidate key 服务的冗余组合 UNIQUE；replay identity、顺序号、receipt、inbox/outbox 和内容摘要等不可复用 identity 继续全历史唯一。

Schema/catalog 测试必须从 fresh PostgreSQL 校验精确表、列、PK、UNIQUE、CHECK、index、trigger 和 privilege 集合；SQL 文本匹配不能代替 catalog 证据。

## 3. Owner 应用完整性

每个写命令由唯一 owner application service 执行，标准顺序为：

1. 校验 typed command、actor、tenant scope、command ID 与 canonical request digest。
2. 跨 owner 事实先通过 generated RPC 取得 authority generation、不可变 revision/digest 或 durable claim；不在本地事务中直接查询其他 owner 表。
3. 开启 owner UoW，按文档化的全局固定顺序 `SELECT ... FOR UPDATE` 锁 aggregate root 与竞争行。
4. claim command receipt；同 ID 同 digest 精确重放，同 ID 异 digest 返回 typed conflict。
5. 校验本 owner 关系、active/deleted 状态和状态迁移；普通 query-then-write 不构成并发保护。
6. 使用 generation/CAS predicate、业务 UNIQUE 和 exact affected-row assertion 写入；业务事实、receipt、outbox 在同一事务提交。
7. 把唯一冲突、stale generation、deleted parent、scope mismatch 和 dependency unavailable 映射为稳定 typed error，不泄露 SQL 错误。

跨 owner 边必须在 RPC 设计时明确属于不可变快照还是 live binding。不可变快照保存 authority ID、revision 与 digest，后续删除不改写历史；live binding 必须使用 owner-issued generation/claim 与幂等释放/撤销协议，使 delete-vs-create 竞争有唯一胜者。一次 RPC 预检查不能充当并发证明。每个 owner 提供只读 readiness/integrity audit，发现 orphan、scope drift、非法状态或 claim 漂移即 fail closed；审计不得静默修数据。

DB role 只阻止越权写入，不做 actor、tenant、状态机或业务授权判断。

## 4. 生命周期与软删除

所有可删除 aggregate root 及需要独立恢复语义的 owner-local entity 统一包含：

```text
deleted_at timestamptz NULL
deleted_by uuid NULL
delete_reason text NULL
```

活动行三列均为空；删除命令设置三列并递增 generation，恢复命令清空三列并再次递增 generation。普通业务 query 和 mutation 固定排除 `deleted_at IS NOT NULL`；管理/审计接口必须显式请求 `include_deleted`。可复用自然键使用 `WHERE deleted_at IS NULL` 的 partial unique；安全、账务、顺序、replay identity 不得因软删而复用。

数据库不级联删除。owner UoW 显式处理 aggregate 内部可变成员；普通读取始终从 active root 进入，历史 child 不得绕过 root 单独暴露。跨 owner 删除/恢复由对应 RPC pair 的 claim/generation 协议处理。

Append-only fact、ledger、receipt、outbox/inbox、运行证据、checkpoint、lease、审计事实和 vendor-owned 表不套软删除模板；它们使用终态、ACK、retention、冷存或受控物理清理协议，生产业务接口不得提供任意 hard delete。

## 5. 独立 Git 与数据库所有权

1. Site、IAM、Model、Capability、Agent、Chat、Storage、Entitlement/Credit、Payment、User Web 和 Admin Web 分别存放在独立 Git repository；各仓自己拥有 source、migration、RPC provider contract、生成配置、业务/管理接口、测试、报告、CI 和 dev entry。
2. 每个后端服务连接自己的 PostgreSQL logical database，拥有独立 bootstrap/migrator role 与 runtime role；本地可以共用一个 PostgreSQL 18 instance，但禁止共享业务表、跨库 SQL 或把另一个 owner 的 migration 放进本仓。
3. runtime role 无 DDL 权限；migrator 凭据不下发给服务进程。诊断只使用该仓自己的只读审计入口；系统验收所需 SQL evidence 使用各仓显式提供的受限只读 test credential。
4. `Kokoro` Root 退化为 meta repository，只管理文档化规范、独立仓 pin/release manifest 和最终原子提升，不保存任何服务的业务 DDL、ORM schema、业务实现、生成 RPC consumer、测试 schema/validator 或测试实现。Root 只核对各仓公开 `verify` 命令和已验收报告摘要，不重新托管测试。
5. 每个 provider 仓拥有自己的完整 Proto package、Buf baseline、server 生成配置和兼容测试；使用 Google 标准 wire types，禁止另建集中业务协议仓。每个 consumer 仓固定 provider descriptor commit/digest，拥有生成 client 和真实 pair 测试。
6. 报告字段与证据要求由本文档化，各仓在本仓保存自己的 report schema、validator、catalog、evidence 和 CI；禁止另建集中 quality/test repository。Root 只比较各仓声明的报告格式 revision/hash 和验收摘要。
7. “独立 Git”必须同时满足独立 object database、独立 remote、独立 CI、独立版本以及可单独 clone/build/test；从 `kokoro-platform` 或 `kokoro-session` 建立的 branch/worktree 只算提取 candidate，不算独立仓。Root 最终只用 gitlink 固定独立 remote commit，禁止路径复制、同仓 branch 或未提交目录冒充子仓。

## 6. Clean replace 与 Proto 首次冻结

实现从不同 identity 的空 PostgreSQL/Redis/state/fixture 建立新基线，不设计旧数据迁移、双写、回填、shadow schema、legacy adapter、旧 DTO 转换或旧路径开关。旧实现只可作为行为证据，不可继续成为运行 authority。

某一服务目标 Proto 由服务提供方仓拥有。在首次正式冻结报告之前允许一次协调的 breaking baseline 重建，但必须在 provider cut 中更新机器 manifest、descriptor 和 server 产物，并由所有 consumer 仓分别更新生成 client、固定 provider contract commit/digest、通过 source/generated byte parity。首次冻结报告 `APPROVE` 后 provider 严格执行 Buf breaking；字段号和枚举号不复用，不随意破坏 RPC。已经冻结的 Proto 不因本文获得第二次 breaking 机会。

## 7. 仓内架构与闭环

有复杂领域规则的仓采用标准 DDD 四层：`interfaces -> application -> domain`，`infrastructure` 实现 application/domain ports；domain 不依赖框架、ORM、RPC 或 infrastructure。IAM 使用完整四层和清晰的 aggregate/entity/value object 归属；Agent 保留适合执行引擎的现有模块风格，但遵守同一依赖方向。轻量仓可以省略没有内容的目录，不能省略 owner、UoW、typed boundary 与测试责任，也不为所有子仓机械制造同一空目录树。

每个子仓必须在仓内同时闭环：本仓数据库 baseline/migrations、领域与 application service、业务面、管理面、repository、DB roles、provider RPC、readiness/integrity audit、单元/真实数据库/contract/admin 测试、正式报告、CI 和 dev entry。本地验证直接使用本仓 dev 进程与本仓 fresh PostgreSQL logical database；当前阶段不以 Docker 作为通过条件。

多个无共享写面的子仓可以并行推进。依赖尚未完成时只允许仓内 port contract test double；并行不改变晋级条件，双方各自 `APPROVE` 后才能开始真实 RPC pair。

## 8. 测试与报告状态机

每个 owner 写实现前先冻结 test catalog 和正式报告骨架，全部 case 初始为 `NOT_STARTED`。测试结果只允许 `NOT_STARTED/RUNNING/PASS/FAIL/BLOCKED`；category 和 overall status 从 required case 机械汇总，不接受人工覆盖。研发晋级阶段使用独立字段：`CATALOG_FROZEN -> RED_RECORDED -> IMPLEMENTING -> EXECUTING -> REPORT_REVIEW -> APPROVE`。RED 必须证明测试因缺少目标行为而失败；失败或证据缺失不得进入下一阶段。只有独立正式报告的 `APPROVE` 具有晋级效力。

每条 case 的通用必填项是：stable ID、category/overall status、requirement/source、owner、依赖、candidate commit/tree/provider-contract SHA 与 clean state、OS/runtime/PostgreSQL 和数据库 identity、local+UTC 起止时间与 duration、精确命令/exit code、预期/实际、逐项结果、warning、correlation IDs、证据路径及每个文件 SHA-256、独立 reviewer 结论。每仓本地 validator 必须实现相同的 execution-layer 矩阵，inventory 作者不得降级：仓内数据库测试强制 command/process log、SQL/catalog before/after；使用 Redis 的测试再强制 Redis before/after；RPC pair 强制 RPC/network trace、双方 service/process log 和 SQL/Redis 事实；浏览器测试强制每个标记步骤的 screenshot、Playwright trace、video、HAR/network，并同时保留对应 RPC、SQL、Redis 和服务日志。Aggregate suite 数量不能代替逐 ID 证据。

## 9. 子仓任务目录

推荐依赖顺序是 Site、IAM、Model、Capability、Agent、Chat、Storage、Entitlement/Credit、Payment、Web user/admin；可按 §7 并行实现独立仓内 cut。

| Stable ID | 冻结验收面 | 初始状态 |
|---|---|---|
| `SITE-D-SQL-CLEAN-001`, `SITE-N-SQL-CLEAN-001`, `SITE-A-SQL-CLEAN-001` | Site/Domain 软删、active unique、race、业务/管理面 | `NOT_STARTED` |
| `IAM-D-SQL-CLEAN-001`, `IAM-N-SQL-CLEAN-001`, `IAM-A-SQL-CLEAN-001` | IAM aggregate、授权映射、无 trigger 状态机、管理审计 | `NOT_STARTED` |
| `MODEL-D-SQL-CLEAN-001`, `MODEL-N-SQL-CLEAN-001`, `MODEL-A-SQL-CLEAN-001` | catalog/revision/routing CAS 与管理面 | `NOT_STARTED` |
| `CAP-D-SQL-CLEAN-001`, `CAP-N-SQL-CLEAN-001`, `CAP-A-SQL-CLEAN-001` | snapshot/receipt exactly-once 与管理诊断 | `NOT_STARTED` |
| `AGENT-D-SQL-CLEAN-001`, `AGENT-N-SQL-CLEAN-001`, `AGENT-A-SQL-CLEAN-001` | run/evidence/ACK/effect/usage 与原 trigger 行为替代 | `NOT_STARTED` |
| `CHAT-D-SQL-CLEAN-001`, `CHAT-N-SQL-CLEAN-001`, `CHAT-A-SQL-CLEAN-001` | Conversation、launch、stream/HITL、删除恢复与审计 | `NOT_STARTED` |
| `STORAGE-D-SQL-CLEAN-001`, `STORAGE-N-SQL-CLEAN-001`, `STORAGE-A-SQL-CLEAN-001` | Blob/Asset/Artifact、retention、管理诊断 | `NOT_STARTED` |
| `ENT-D-SQL-CLEAN-001`, `ENT-N-SQL-CLEAN-001`, `ENT-A-SQL-CLEAN-001` | Entitlement/Fulfillment/Credit owner 闭环 | `NOT_STARTED` |
| `WEB-U-CLEAN-001`, `WEB-A-CLEAN-001` | User Web 与 Admin Web 各自 generated clients、业务、测试和报告 | `NOT_STARTED` |

Credit 还必须逐项冻结：

| ID | 验收阈值 | 状态 |
|---|---|---|
| `CR-SQL-001` | exact catalog、零 FK/cascade、source/generated parity | `NOT_STARTED` |
| `CR-TENANT-001` | direct site lineage、跨租户写零残留 | `NOT_STARTED` |
| `CR-IDEM-001` | 同 digest 精确重放、异 digest durable conflict | `NOT_STARTED` |
| `CR-RACE-001` | quota/delete/hold/capture/release/pricing lock/CAS | `NOT_STARTED` |
| `CR-LIFE-001` | Account/Pricing 恢复；Ledger/Hold/Usage 无 hard delete | `NOT_STARTED` |
| `CR-ADMIN-001`, `CR-GATE-001` | 管理面、fresh DB 全套与独立报告 | `NOT_STARTED` |

Payment 还必须逐项冻结：

| ID | 验收阈值 | 状态 |
|---|---|---|
| `PAY-SQL-001`, `PAY-SNAPSHOT-001` | exact catalog；购买 revision/digest 永久冻结 | `NOT_STARTED` |
| `PAY-IDEM-001`, `PAY-SUB-001` | checkout/grant/webhook/cycle exactly-once 与 identity 不漂移 | `NOT_STARTED` |
| `PAY-RI-001`, `PAY-RACE-001` | 缺失/删除/跨租户零残留；claim/generation/outbox race | `NOT_STARTED` |
| `PAY-LIFE-001`, `PAY-ADMIN-001`, `PAY-GATE-001` | Provider/Plan 生命周期、管理面和独立报告 | `NOT_STARTED` |

## 10. RPC pair 晋级

只有两侧 owner 报告均 `APPROVE`、provider Proto 已冻结且 consumer 已从固定 descriptor 生成 client，consumer 仓才创建 pair cut。每对使用 generated client、真实进程、双方独立数据库和 consumer 仓的正式独立报告，覆盖正向、拒绝、重放、并发、deleted parent、authn/authz、timeout、lost response 与 restart；provider 仓同时维护服务端契约一致性测试。禁止 mock、direct handler、共享 SQL join 或 admin SQL 代替。

| Consumer owner | Pair | 范围 | 初始状态 |
|---|---|---|---|
| IAM | `PAIR-R-SITE-IAM-001` | Site active/deleted authority、domain resolve | `NOT_STARTED` |
| Chat | `PAIR-R-IAM-CHAT-001` | Authorize、tenant actor | `NOT_STARTED` |
| Agent | `PAIR-R-MODEL-AGENT-001`, `PAIR-R-CAP-AGENT-001` | immutable revision/snapshot/digest | `NOT_STARTED` |
| Agent | `PAIR-R-STORAGE-AGENT-001` | Agent artifact/blob authority 与 retention | `NOT_STARTED` |
| Chat | `PAIR-R-STORAGE-CHAT-001` | Chat artifact/blob authority 与 retention | `NOT_STARTED` |
| Agent | `PAIR-R-ENT-AGENT-001` | usage authorization/settlement/reversal | `NOT_STARTED` |
| Chat | `PAIR-R-AGENT-CHAT-001` | Launch/Evidence/Ack/Control、terminal/restart | `NOT_STARTED` |
| Payment | `RPC-PC-001`, `RPC-PC-002`, `RPC-PC-003`, `RPC-PC-004` | Payment -> Entitlement/Credit exactly-once、重试/重启、provenance、真实进程证据 | `NOT_STARTED` |
| User Web | `PAIR-R-WEBU-BACKEND-001` | IAM session、Chat snapshot/stream、用户命令 | `NOT_STARTED` |
| Admin Web | `PAIR-R-WEBA-BACKEND-001` | IAM admin session、各 owner 管理命令 | `NOT_STARTED` |

每个 pair 必须单独 `APPROVE`；一对通过不能替代另一对报告。

## 11. 两轮 fresh Chromium E2E

所有所需 pair `APPROVE` 后，User Web 仓拥有完整用户浏览器链，Admin Web 仓拥有完整后台管理浏览器链；两个仓分别使用依赖仓公开 dev entry 启动真实 Site/IAM/Model/Capability/Agent/Chat/Storage/Entitlement/Credit/Payment，走 production adapters、generated clients、各仓独立数据库和真实 Chromium。冻结任务当前为：

| Owner | ID | 范围 | 初始状态 |
|---|---|---|---|
| User Web | `CHAIN-B-USER-001`, `E2E-BILLING-001` | 完整用户链与 checkout/webhook/settlement/usage/refund | `NOT_STARTED` |
| User Web | `E2E-REPLAY-U-001`, `E2E-TENANT-U-001` | 用户双击/乱序/restart/concurrency 与双 Site/Org 隔离 | `NOT_STARTED` |
| User Web | `E2E-FRESH-U-001`, `E2E-EVIDENCE-U-001` | 用户链两套 fresh identity 重跑及逐步证据 | `NOT_STARTED` |
| Admin Web | `CHAIN-B-ADMIN-001`, `CHAIN-B-DELETE-RESTART-001`, `E2E-ADMIN-001` | 后台 create/update/delete/restore/audit、跨 owner race/restart/reload | `NOT_STARTED` |
| Admin Web | `E2E-REPLAY-A-001`, `E2E-TENANT-A-001` | 管理命令重放/乱序/concurrency 与双 Site/Org 隔离 | `NOT_STARTED` |
| Admin Web | `E2E-FRESH-A-001`, `E2E-EVIDENCE-A-001` | 后台链两套 fresh identity 重跑及逐步证据 | `NOT_STARTED` |

完整冻结清单必须在两套不同 PostgreSQL、Redis、state、secret 和 fixture identity 上各执行一次，各仓 candidate commit/tree 与 provider-contract SHA 完全相同。每一步保存 local+UTC 时间、截图、Playwright trace/video/HAR、RPC/network、只读 SQL/Redis、服务日志和 SHA-256。两轮均 PASS、parity/cleanup/evidence-ledger 均 PASS 且最终报告独立 `APPROVE`，才可宣布系统晋级。

## 12. Test double 边界与最终门禁

Test double 仅用于单仓 port contract test，不能计入真实 RPC、跨仓集成、系统联调或 E2E。以下任一成立即禁止晋级：Root 集中保存服务 DDL/业务测试；某服务仓依赖另一个仓的业务表；存在 FK/cascade/关系或业务 trigger；runtime role 可跨 owner 写；依赖普通预查保证并发；软删字段/默认过滤/恢复不完整；预填 PASS；缺少 RED、fresh DB、逐 ID 证据或独立报告；使用 mock/direct handler/shared SQL 冒充 RPC；保留旧 adapter/DTO/双写路径；只跑一轮或非真实 Chromium。

最终 Definition of Done 是：每个独立 Git owner 仓的业务面、管理面、数据库/repository/readiness/integrity audit、测试、报告和 CI 独立 `APPROVE`；每个 consumer 仓的 generated RPC pair 独立 `APPROVE`；User Web 与 Admin Web 各自两轮 fresh 真实浏览器链最终独立 `APPROVE`；Root 最后只提升已验收的独立仓 pins 和 release manifest。在此之前整体状态保持未晋级。
