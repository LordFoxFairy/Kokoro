# Kokoro 当前任务状态

> 主 Agent 维护；Subagent 只读。最后更新：2026-08-02。
> 本文件只保存当前 campaign、已验证事实、阻塞与下一步；历史过程以 Git 和 dated handoff 为准。

## 1. 当前目标

把 Root、Platform、Session、Web 与 Agent 收敛为可发布的 redeem-first 多 Site AI 产品平台：

- 每个 Site 是独立 Web 项目、品牌、账户、artifact、部署和回滚单元；
- Platform、Session、Agent 后端复用，但所有请求由受信 Site/workload/actor 上下文隔离；
- 卡密与未来支付统一进入 Fulfillment，再签发 SubscriptionTerms、EntitlementGrant 与 CreditGrant；
- 全局 Model Catalog 只维护一份底层模型，产品通过 ModelOption 与 SiteRelease 组合 Chat、Image、Music、Video 的模型路由；
- General Chat 与 Studio 共享 Platform Media、Artifact、Credit spine，但保持独立产品体验；
- Saved Memory、conversation history/search 与 Agent runtime context 分属三个 owner；
- 四个 `kokoro-*` 永久保持独立仓库、CI、artifact、deploy 与 release；Root 只拥有 contract、Infra、compatibility、BOM 与 pin promotion。

当前事实源：

1. `docs/CURRENT.md`
2. `docs/CODEBASE_MAP.md`
3. `docs/kokoro-handbook/technical/24-federated-product-platform-architecture.md`
4. `docs/kokoro-handbook/decisions/ADR-016-web-release-composition.md`
5. 本文件列出的已终审 commit

## 2. 不变量

- 不存在 Root V2、Session V2 或第二套根/会话系统；`v2` 只表示特定 protocol/schema family。
- 不创建顶层 Generation、通用 Job 或 `kokoro-generation` 子仓。图片/音乐/视频归 Platform Media；Artifact 独立拥有产物。
- Agent 只处理 Agent 业务和窄工具端口；不得未经用户确认修改 graph、checkpoint、terminal、handoff 核心语义。
- Platform 同 bounded context 使用本地 application interface 与 Unit of Work，禁止 self-RPC；跨仓只走 HTTP/SSE/Connect/durable transport。
- 每个外部 Site 是独立 Web 项目；共享账户只通过标准 OAuth/OIDC linking，不默认跨站共享。
- Payment feature-off；当前 launch 只要求 card-code redemption 复用未来支付的 Fulfillment/Credit 链。
- 浏览器展示协议由 Session 投影；AG-UI 不替代 durable evidence、branch、HITL、billing、checkpoint 或 owner receipt。
- 默认本地 Infra 只保留 PostgreSQL、MongoDB、Redis、MinIO；不得常驻测试或业务容器。

## 3. 当前工作树

Canonical worktree：

```text
/Users/nako/.config/superpowers/worktrees/Kokoro/feat/lordfoxfairy/wave-0-foundation
```

Root branch：`feat/lordfoxfairy/wave-0-foundation`。

当前候选：

| Repository | Candidate | 状态 |
|---|---:|---|
| Root contract baseline | `b2d0916` | strict AG-UI governance 已提交；本任务状态文档单独前移，不提升 gitlinks |
| Agent | `4ea5df6` | 本 campaign 未改核心语义 |
| Platform | `534be3a` | old Site publication handler fail closed；Candidate Authority 未实现 |
| Session | `8c22f85` | Browser v3 基线；AG-UI runtime M0 正在实现 |
| Web | `a8fb515` | owner/terminal projection 已终审；保留既有 generated/dist dirt |

Web 既有未提交本地制品必须保留，不能由无关任务提交：

```text
packages/session-client/src/generated/control.ts
packages/site-app-kit/dist/
packages/site-scaffold/dist/
```

## 4. 已独立终审 PASS

### Root SiteRelease publication authority

Commit chain：`a52ccc3` → `d918080` → `f90069a` → `11a98db`。

- Root trust anchors 独立于 corpus，签名算法固定 Ed25519，certification、revocation 与六类 owner-read receipt 权限分离；
- begin 与 immediate-before-CAS 两份 authority snapshot 绑定 Site/environment、六个 owner live head、时效 lease 与 active-pointer CAS；
- first activation 与 existing activation 的 release ref/current/expected generation 构成封闭状态分区；
- 59 个负向向量和 7 个 blocked activation snapshot 均由 checker 内独立 JCS digest 冻结，不能复制凑数或同错误码替换；
- 终审 P0/P1/P2 为 0；50/50 主测试、13/13 pointer/signature 专项和 package gate 通过。

这只证明 Root contract/publication authority。Platform Candidate Authority 与 active-pointer runtime 仍未实现，不能宣称 SiteRelease 已上线。

### Root strict AG-UI presentation profile

Commit chain：`18555c7` → `43c73b2` → `1d108bd` → `b2d0916`。

- exact `@ag-ui/core@0.0.57`、npm integrity、TypeScript compatibility 与官方 `EventSchemas/EventType` 进入可执行门禁；
- 第一阶段只允许 RUN、TEXT、ACTIVITY_SNAPSHOT 与注册 CUSTOM；RAW、state/messages snapshot、native tool、reasoning/thinking/step/chunk 族全部 fail closed；
- Session 是 durable projection owner；Agent/Python 与 stock `@ag-ui/client` 不参与 browser transport；
- 每个 persisted row 保存完整 closed projection payload 与 JCS digest，并一对一生成保留 SSE `id/event` 的 frame；
- run resume 与 parent lineage 分离；TEXT END 后不得重开旧 presentation message id；resume 创建新 segment id；
- cursor decoded claims、source、row、run/message binding 与 segment identity 在 Session scope 内全局去重；
- deterministic corpus、checker、typecheck、18/18 对抗测试与 Root CI 接线终审 P0/P1/P2 为 0。

该 profile 仍为 `contract-only`。Session provider、Web consumer、兼容性场景与 release evidence 完成前不得激活。

### Web Chat owner/terminal projection

Commit chain：`2e8c742` → `95d5241` → `7c05e70` → `ddff038` → `fd08fe4` → `a8fb515`。

- Run/Launch 双向绑定、pending half 私有、terminal non-revival 与 command selector authority 已收口；
- live message 导致的 branch authority stale 只能由完整 owner snapshot 修复，合法 branch switch 不会无限 repair；
- Session/Branch owner 使用 version + semantic fingerprint；同版本只能幂等，高版本不能改写 immutable identity；
- branch root write-once，Session updatedAt 单调；非法新 Session snapshot 不会清除旧 scope；
- terminal Run/Launch pair 在 snapshot/live 两条路径均不可重绑，authority ledger 有 4096 上限并超限 fail closed；
- 最终终审 P0/P1/P2 为 0；chat-surface 53/53、chat-app 62/62、typecheck/lint 通过。

### 其他稳定基线

- Agent tool catalog ingress、delivery 25 MiB/TOCTOU 与 web-fetch private/CGNAT 防护已完成；本轮不改 Agent 核心语义。
- Session Browser v3 已具备 scope-bound encrypted cursor、Last-Event-ID 冲突检查、durable +1、snapshot repair、bounded SSE、revocation 与 draining。
- Platform identity/authz/model/hub/artifact/admin kernel 与 card-code/Fulfillment 基础较强；公开激活与完整 worker/recovery 仍按下节处理。

## 5. 正在进行

### Session AG-UI runtime M0

只在 `kokoro-session` 建立 dormant provider 基础：exact official dependency、strict normalized source port、run/message segment state machine、完整 row payload/digest、PostgreSQL append/CAS/RLS repository 与真实验证。不得直接让 Agent 输出 browser protocol，不改变现有 active Browser v3 stream；完成独立终审后再接 current Session owner facts。

Root prelaunch contract 已要求每个 durable payload 原子携带完整 `bindingAuthorityDelta`，并把 Session source
`projectionVersion` 收紧为 positive uint64 十进制字符串。Session 子仓仍须同步生成镜像、持久化与
admission/projector。公开 binding 已完成浏览器安全硬切：Agent 的 internal run/message/parent 路由只能留在 Session
私有映射权威，snapshot、delta、persisted payload 与 SSE 全部禁止携带；三类走私攻击和私有父子映射冲突均 fail closed。
Agent `sourceEventRef` 同样只留在 candidate/private provenance；Session 公开 `sourceEventId` 使用独立 opaque
`presentation.event:` identity，二者相等、泄露、重复、跨 Session 与覆盖缺失均拒绝，Web 不负责派生。
Root generator 的 domain-separated HMAC 仅用于 deterministic test fixture，不进入 runtime contract/frame；旧
`sessionId:epoch:seq` 明文组合已禁止，runtime 仍只要求 Session owner-assigned opaque ref。
`kokoro.run.replace.v1.value` 已硬切为 positive uint64 string `ownerVersion`，旧 integer `projectionVersion` 禁止。
Root 合同通过不代表 provider 已激活。

### Web AG-UI consumer M0

只在 `kokoro-web` 建立 dormant strict decoder/adapter：保留自有 bounded SSE parser、验证 outer profile/source/cursor 与 official event，再映射到现有 `useExternalStoreRuntime` owner reducer。不得使用 stock `@ag-ui/client` 或 `useAgUiRuntime`，不得在 Session provider/compatibility evidence 完成前切 active controller。

Web 必须只应用 Session owner-authored 的完整 binding replacement，从真实 sequence-zero 空 snapshot 逐帧建立
binding authority；不得预载未来 binding、按 CUSTOM 名称推断、发逐事件修复请求或自行拼 patch。

### Platform Candidate Authority implementation audit

正在按真实代码梳理 ProductCatalog、SurfaceInventory、WebBuildIntent、MaterialBundle、Candidate、Certification、SiteRelease、active-pointer CAS 与六个 owner live receipt 的实现 DAG。Platform `534be3a` 的旧 publish handler 已明确 `Unimplemented`；当前不得恢复旧 handler 或用 self-RPC 拼装。

## 6. 尚未闭环的产品能力

- Platform ProductCatalog/SurfaceInventory/SiteRelease Candidate Authority 与真实 activation/rollback；
- Commerce、Model、Hub、Auth、Memory 对 exact active SiteRelease revision 的运行时绑定；
- card-code redeem → Fulfillment → Subscription/Entitlement/CreditGrant，以及 daily/periodic/permanent bucket 的 hold/settle/release/reconcile/expiry workers；
- Image-first Media 的 Gateway/Trust/Credit/Artifact/worker 全链，随后复用到 Music/Video；
- Saved Memory activation、classifier、keyring、retention/import/export/purge/Data Rights；
- conversation search、workspace/project、notification、support 与完整 telemetry；
- 标准 Admin operator product的全量 control plane，而非直接写业务数据库；
- 两个独立 Site 的浏览器 E2E、故障恢复、clean clone、BOM、rollback rehearsal。

所以当前整体仍不是 launch-ready；已 PASS 的是关键 owner/contract/Web projection 基础，不是全部 Platform 模块。

## 7. 下一步顺序

1. 完成 Session/Web AG-UI M0，双独立复审后建立真实 Session provider → Web consumer compatibility scenario。
2. 设计并实施 Session presentation projector 对现有 owner facts/Agent durable-output consumer 的接线；每个 frame 必须先持久化，禁止临时 fan-out。
3. 实现 Platform Product/Surface/SiteRelease Candidate Authority 与 active-pointer CAS，再将旧 handler 的 fail-closed 替换为新 authority。
4. 把 Commerce、Model、Hub、Auth、Memory 全部绑定同一 active release ref/digest，完成两个独立 Site 的启用/禁用验证。
5. 闭环 card-code/Fulfillment/Credit 三 bucket，再做 Image Media vertical；Music/Video 只复用已验证 spine。
6. 激活 Saved Memory 与 Data Rights；任何 Agent MemoryPort 或核心 graph/handoff 改动先通知用户。
7. 四仓独立 CI、跨仓 runtime compatibility、真实 Infra、clean clone、原子 pin promotion、BOM 与 rollback rehearsal。

## 8. 当前阻塞

- Root GitHub Actions 缺用户侧 `KOKORO_SUBMODULE_TOKEN`，不能代用户签发；Root remote CI 未绿前不创建 BOM tag。
- Payment provider 凭据不在当前 launch scope；保持 feature-off，不以 fake payment 冒充真实集成。
- Node 本地主控为 22，仓库声明 Node >=24；实现 agent 已使用 Node 24 复验关键 Web 门禁，Root CI 也固定 Node 24。

## 9. 完成定义

“整体 OK”必须同时满足：

- owner、边界、状态机、失败恢复与不可逆终态正确；
- Site/Subject/workload/namespace 隔离无 fail-open；
- 启用产品旅程完整，未启用产品在构建、路由、授权、模型与计费五层都关闭；
- PostgreSQL/MongoDB/Redis/MinIO 与跨仓协议有真实运行证据；
- Web 浏览器行为、Admin 运维、可观测、数据权利、维护和回滚可用；
- 四个子仓独立发布，Root 原子组合经过 clean clone 与 rollback rehearsal；
- 文档、contract、generated client、deployment inventory、BOM 与代码事实完全一致。
