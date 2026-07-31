# Kokoro 当前任务状态

> 主 Agent 维护；Subagent 只读。最后更新：2026-07-31。
> 本文件只保存当前 campaign、事实、阻塞与下一步。历史过程从 Git 记录或 dated handoff 查询，不在这里累积。

## 1. 当前目标

在不改变 GA graph/checkpoint/terminal/handoff 核心语义的前提下，把 Root、Platform、Session、Web 与 Agent 的整体
架构和真实代码收敛为可发布的 redeem-first 多 Site AI 产品平台：

- 每个 Site 是独立 Web 项目、品牌、账户、artifact、部署和回滚单元；
- 共享 Platform/Session/Agent 后端，但所有业务请求按可信 Site/workload/actor 隔离；
- 卡密与未来支付统一进入 Fulfillment，再签发 SubscriptionTerms/EntitlementGrant/CreditGrant；
- 一个全局模型目录，产品通过 ModelOption 与 SiteRelease 自由组合；
- Chat 与专业 Studio 共享 Media/Artifact/Credit spine，但保持不同产品体验；
- Saved Memory、conversation history/search 与 Agent runtime context 保持三个 owner；
- 四个 `kokoro-*` 永久是独立子仓，Root 只做 contract/Infra/compatibility/BOM/pin authority。

整体事实源：

1. `docs/CURRENT.md`
2. `docs/CODEBASE_MAP.md`
3. `docs/kokoro-handbook/technical/24-federated-product-platform-architecture.md`
4. 与任务直接相关的 accepted ADR

`technical/15` 与 `technical/20` 是历史稿，不得恢复 Root V2、Session V2、MySQL、Platform 零新增或旧
Generation/Job 架构。

## 2. 不变量

- 不存在 Root V2、Session V2 或第二套根/会话系统；`v2` 只用于明确 protocol/schema family。
- 不创建顶层 Generation 服务、通用 Job 服务或新 `kokoro-generation` 子仓。
- 图片/音乐/视频归 Platform Media；Artifact 独立拥有产物；Agent 只通过窄工具调用。
- Platform 同 bounded context 使用本地 application interface + `PlatformUnitOfWork`，禁止 self-RPC。
- 跨仓只走 HTTP/SSE/Connect/durable transport，不导入兄弟仓源码、不共享进程对象、不跨库写表。
- Session 不是 Hub runtime consumer；Agent 是 Hub runtime consumer。
- GA 只消费 opaque non-empty `namespace`，不得新增 Site/User/Owner/Workspace 第二身份轴。
- 每个外部 Site 一个独立 Web 项目；共享账户未来通过标准 OAuth/OIDC linking，不默认跨站共享。
- Payment feature-off；当前 launch 只要求 card-code redemption 与同一 Fulfillment/Credit 链。
- 默认本地 Infra 只保留 PostgreSQL、MongoDB、Redis、MinIO 四个容器；不得常驻测试/业务容器。

## 3. 当前工作树

Canonical worktree：

```text
/Users/nako/.config/superpowers/worktrees/Kokoro/feat/lordfoxfairy/wave-0-foundation
```

Root branch：`feat/lordfoxfairy/wave-0-foundation`。

四个子仓当前都超前于 Root 已提交 gitlink；在独立 CI、跨仓兼容、真实基础设施和 rollback evidence 完成前，不做
原子 pin promotion、不打 BOM tag。

Web 中以下是既有未提交生成物/本地制品，必须保留，不能由无关任务提交：

```text
packages/session-client/src/generated/control.ts
packages/site-app-kit/dist/
packages/site-scaffold/dist/
```

## 4. 已收敛事实

### Agent

- 当前候选 HEAD：`4ea5df6`。
- Tool catalog supervisor ingress、delivery/web-fetch hardening 已完成。
- 旧的 Agent 直连 Mongo Saved Memory 工具已从生产移除。
- Agent 全量验证此前为 115/115，ruff 与 pyright 通过。
- 本 campaign 不修改 Agent 核心 graph/checkpoint/terminal/handoff。

### Web Saved Memory

- Saved Memory 基线 commit：`23afbb4`；Web 当前候选 HEAD：`4923b4c`。
- owner snapshot、space-version floor、scope remount、async request generation、cursor recovery 和
  import/export state projection 已完成独立复审。
- Memory 52/52；Site BFF 60/60；typecheck/lint/diff-check 通过；未启动 Docker。
- 该切片只是 dormant Web consumer，不能证明 Platform Memory 已可对外发布。

### Session context policy

- `standard|temporary` 已进入 Session create contract、receipt/digest/snapshot/list/event，并在创建后不可变。
- branch/edit/regenerate/fork/activate 继承 Session policy；普通列表排除 temporary，精确授权 snapshot 仍可读。
- Session M0 当前候选 `b2954ba` 已通过独立终审：真实 migrator、FORCE RLS、不可变 trigger、普通列表抑制与精确
  授权读取成立；全量 469/469，真实 PostgreSQL verifier 通过。
- 这只完成 Session-local policy，不是完整 Temporary Chat。policy 尚未进入 Platform Admission/source suppression；Web
  的创建入口、badge 与临时本地恢复策略正在实现，因此全链继续 NO-PASS。

### Root architecture

- `docs/kokoro-handbook/technical/24-federated-product-platform-architecture.md`、ADR-016 与 PRD-00 v1.1 已通过四轮独立
  架构终审；Product/Surface 唯一 owner、完整 SurfaceInventory、Web material/toolchain、五阶段 build supply chain、
  JCS/DSSE/OCI/SLSA、旧事实源与真实 activation 状态均已收敛。
- 旧 `technical/20` 已降级为历史基线；handbook README、CURRENT、CLAUDE 路由正在同步。
- Root boundary registry 的精确 provider matching 已修复；Hub runtime 真实 consumer 只有 Agent，不是 Session。

### Web Temporary Chat

- 当前候选 commit：`4923b4c`；Web 创建时显式提交 `standard|temporary` 并核对 receipt/snapshot owner fact。
- Temporary UI、持续 badge、普通 rail/search 抑制、draft/command/upload recovery 禁止与 scope remount 已实现；Web 全仓
  typecheck/lint/599 tests/production build 由实现 agent 验证，正在独立终审。
- 这仍只是 Web M1 + Session M0。Platform Admission、Saved Memory/past-chat/source/retention 抑制未完成前，完整
  Temporary Chat 继续 NO-PASS。

## 5. 正在进行

### Platform Saved Memory owner data plane

当前候选 commit：`0679e85`。独立 spec review 已 NO-PASS，正在修复；继续 dormant。

目标：完成 M0 personal owner data plane，但继续 dormant。

必须满足：

- remember/correct/forget/reset 只由 `MemoryAuthorityService` 产生 transition；
- SQL 只负责真实 workload/OID/RLS、owner facts、锁、CAS、receipt 和已验证 transition 的持久化；
- forget 只撤销目标 entry，reset 才推进整个 space generation；
- list/detail/history/restore 全部数据库侧防止忘记/重置后的 plaintext 复活；
- public command fingerprint 使用注入的 keyed provider + key revision；
- prepare receipt、expected state digest 与 commit CAS 绑定，不能绕过 domain service；
- 没有权威 per-Site Memory activation projection、production classifier 或 keyring 时 fail closed；
- 使用现有 PostgreSQL 的唯一临时 DB 验证并删除，不新建容器。

已确认的阻断包括：prepare/commit 可伪造 transition、JSONB `null` 与时间格式不兼容、成功 command replay 被前置
read/KMS/classifier 破坏、revoked/purged detail 只存在于 fake、真实 PostgreSQL ACL/routine/隔离证据缺失、decoder 非
closed shape。上述问题全部修复并复审前，不得把该 commit 纳入候选 pin。

### Web Release Composition

当前 scaffold 只有 `SiteProductId = "memory"`，存在 `memoryEnabled` 特判，而 Chat/Account/Media 总是打包后再
`notFound()`。这不适合大量独立套皮 Site。

目标：Platform release candidate 签发 `WebBuildIntent`，Web 从受信、版本化、封闭的 `WebCompositionUnit` 目录编译
`CompiledWebManifest`，再构建独立 Site artifact；最终 SiteRelease 绑定 intent、compiled-manifest digest、artifact digest
与业务 revisions。Web unit 只拥有 package/route/nav/BFF/bootstrap 等物理映射，不拥有 Product、Entitlement、Policy 或
Journey。未启用 surface 在 artifact 和 Platform authorization 中都物理缺席。不得引入任意动态代码、shell、URL/npm
spec 或 `if (productEnabled)` 扩散。

## 6. 后续顺序

1. 修复 Platform Memory Task 5 的全部独立审查 blocker，再走 spec、code-quality、主控真实 PG 与全仓复验。
2. 完成 Web Temporary Chat M1 独立终审；Session context-policy M0 已终审通过，不再重复做 migration 工作。
3. Root 先发布 ProductSurfaceCatalog、SurfaceInventory、WebBuildIntent、MaterialBundle、BuildToolchain、CompiledManifest
   与 provenance profile contracts/corpus；不得先写一个自有字符串表的 Web compiler。
4. Platform Product Catalog 发布唯一 catalog revision；Site 的单一 SurfaceInventory、Commerce、Model 与 Memory
   全部迁到同一 ref/digest。
5. Web 在 shadow mode 发布 WebCompositionRegistryRevision/compiler，由完整 SurfaceInventory 派生 units，删除 Memory
   特判与 always-included 产品。
6. 建立 controller → trusted compiler → credential-free build sandbox → separate inspector sandbox → attestor 的构建
   控制面、release material/package/OCI provenance 和真实 Next artifact inspection。
7. Platform Site owner 完成 WebBuildIntent/MaterialBundle、candidate evidence、SiteRelease、ProductContext、activation/
   drain/rollback 集成，并以两个完全独立 Site 验证。
8. Session/Platform Admission 完成 Temporary Chat retention/source/search/Saved Memory 抑制；再实现可解释 conversation
   search。任何 Agent MemoryPort 变更先与用户对齐。
9. Platform 增加权威 SiteRelease Memory activation projection；完成 purge/import/export worker 与 Data Rights 后才挂
   public route。
10. 审计并收口 ModelOption、LiteLLM adapter、Redeem/Fulfillment/Credit 三 bucket 与 payment-off negative inventory。
11. 完成 Media image vertical 的真实 Gateway/Trust/Credit/Artifact/worker 链，再复用到 Music/Video。
12. 建立 Workspace/Project、Trust、Notification、Support、Data Rights 的最小 core-launch bounded contexts 与旅程。
13. 对 Web/Session 超大 controller/composition 文件按责任拆分，建立 Root toolchain BOM；Session 是否迁 pnpm 单独决策。
14. 四仓完整 CI、真实 Infra、两个独立 Site 浏览器 E2E、安全/故障/恢复、clean clone、BOM、rollback rehearsal。

## 7. 当前阻塞

- Root GitHub Actions 缺少用户侧 `KOKORO_SUBMODULE_TOKEN`（对四个私有子仓只读 Contents）。不代用户签发凭据；
  Root remote CI 未绿前不创建 BOM tag。
- Payment provider 凭据不在当前 launch scope；保持 feature-off，不用 fake payment 替代真实集成。
- 任何需要改变 Agent 核心 graph/checkpoint/terminal/handoff 或正式加入 MemoryPort 的工作，必须先与用户对齐。

## 8. 完成定义

“整体 OK”不是测试数量或文档数量。必须同时满足：

- owner、边界、状态机和失败恢复正确；
- Site/Subject/workload/namespace 隔离无 fail-open；
- 启用产品业务旅程完整，未启用产品五层关闭；
- 真实 PostgreSQL/MongoDB/Redis/MinIO 与跨仓协议证据通过；
- Web 浏览器行为、Admin 运维、可观测、数据权利、维护与回滚可用；
- 子仓独立发布 + Root 原子组合经过 clean clone 和 rollback rehearsal；
- 文档、contracts、generated clients、deployment inventory 与代码事实一致。
