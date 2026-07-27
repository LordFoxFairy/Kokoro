---
artifact: product-requirements-document
prdId: PRD-A6
version: "1.0"
created: 2026-07-25
status: internal-review-active
scope: cli-desktop-ide-install-auth-device-task-continuation-target-offline-update-support
accountableProductRole: Agent Product Lead
mandatoryCosigners: [Identity, Client Platform, Execution Runtime, Session, Developer Workspace, Security, Accessibility, Support, SRE, QA]
engineeringOwner: team:client-platform
qaOwner: team:client-quality
supportOperationsOwner: team:client-operations
namedOwnerAssignmentStatus: assigned-team-responsibility-ids
implementationAuthorized: false
gaRuntimeSemanticChangeAuthorized: false
---

# PRD-A6：Client Access Plane — CLI、Desktop 与 IDE

## 1. Overview

Kokoro 需要提供 Claude Code 类 CLI、Desktop 与 IDE 入口，让用户在本地开发环境、桌面和 Web 之间继续同一
Task，而不是复制第二套 Agent、账户、Session 或 Credit 系统。现有 Client Access 技术设计已经冻结 OAuth、
public client、attach/fork/new run 和 ExecutionTarget 边界；本文补齐用户旅程、状态、恢复、指标、Admin/Support
和发布范围。

### Users and jobs

| Actor | Job |
|---|---|
| Developer | 安全安装客户端、登录当前 Site、绑定仓库，在 IDE/CLI 中继续同一任务 |
| General user | 在 Desktop 与 Web 间切换，不丢 Session、HITL、Artifact 或费用状态 |
| Security-conscious user | 看清设备、scope、target permission，随时撤销且确认生效 |
| Site operator | 控制允许的 client/release/protocol/feature，不泄露另一 Site 产品关系 |
| Support/SRE | 用安全 bundle 和 correlation refs 诊断登录、兼容、连接、target 与 unknown action |

## 2. Goals、metrics and non-goals

### Goals

1. 用户无需粘贴 token/secret，即可在 system browser 或 device flow 完成 Site-bound 登录。
2. `attach`、`fork`、`new_run` 三种意图在 UI、账务、lineage 和恢复上完全可区分。
3. 本地文件、命令、浏览器与 Git effect 默认 deny，按 action/resource/time 授权并产生 receipt。
4. 客户端升级、协议兼容、device revoke、offline/degraded 和 Support 形成完整闭环。
5. Web、CLI、Desktop、IDE 复用同一 Platform/Session/Task/GA/Job/Artifact/Credit runtime。

### Launch metrics

| Metric | Target |
|---|---:|
| OAuth/device-flow 成功后 token/Code/secret 泄漏 | 0 |
| attach 误创建 Run/Hold/effect | 0 |
| fork 复用旧 Hold、GA checkpoint 或 Target grant | 0 |
| cross-Site token/device/cache/task/target 授权成功 | 0 |
| revoke 后新 API/SSE/target effect 超 SLO 仍成功 | 0 |
| unknown local action 被自动重放 | 0 |
| compatible active client attach 成功率 | ≥ 99.9% |
| update-required 用户保留/导出 draft 成功率 | 100% |

### Non-goals

- 不定义新的 Agent runtime、模型路由、Credit 或 Session 真源。
- 不暴露 GA checkpoint、namespace mapping、Provider、内部 RPC 或 workload credential。
- 不承诺离线运行云端 Agent；offline 只允许安全读缓存和保存本地 draft。
- 不在本 PRD 开放第三方扩展继承主客户端 token。
- 不授权修改 GA graph、assembly、prompt、tool、Skill/MCP、HITL、cancel、terminal 或 checkpoint。

## 3. Product model and ownership

| Product object | User meaning | Authority |
|---|---|---|
| PublicClientDefinitionRevision | 官方 client kind、publisher、redirect 与 protocol 范围 | Client Platform |
| ClientReleaseAttestation | 某 binary/package 可被信任和支持 | Supply-chain/Client Platform |
| DeviceRegistration | 当前 Site 下一个可查看、撤销的设备安装 | Identity/Device Registry |
| OAuthGrantRevision | 当前 Site、device、audience 和 scope 的授权 | Site Identity |
| ClientFeatureManifestRevision | 此 SiteRelease 对该 client 真正开放的功能 | Site Fleet/Client Access API |
| WorkspaceBindingRevision | Project 与本地 root/target 的显式绑定 | Developer Workspace/Execution Runtime |
| ClientTaskIntent | attach/fork/new_run 的用户意图与幂等身份 | 对应 command owner |
| TargetActionIntent/Receipt | 被批准和实际执行的本地动作 | Execution Runtime/local connector |

Client Access API 是 public edge façade，不拥有上述领域真源。客户端不得保存 Site workload secret、raw namespace、
Provider secret、repository credential 或可复用高风险 approval。

## 4. Canonical journeys

### CLIENT-01 — Install、verify and update

用户从 Site 官方入口取得签名 client，验证 publisher/channel，完成首次启动；若版本低于 security minimum，客户端
阻止新 effect，保留安全导出 draft、诊断与签名升级路径。rollback/downgrade attack 必须拒绝。

### CLIENT-02 — Authenticate and register device

有浏览器时使用 Authorization Code + PKCE；headless 使用 Device Authorization。用户在授权页看到准确 Site、client、
device、scope 和 expiry。成功后注册 device；取消、expiry、slow_down、state mismatch 可安全重启，不记录 code/token。

### CLIENT-03 — Bind project and local target

用户选择 Project、本地 root/repository 和 permission profile。客户端先展示 ignore/symlink/secret 风险；server 只保存
opaque root identity 与必要 metadata。root、remote、worktree、device key 或 membership 变化产生新 revision 并失效旧 grant。

### CLIENT-04 — Attach an existing task

用户从 recent tasks 或安全 deep link 选择 active/paused/recoverable Task；客户端加载 Session snapshot、TaskView 和当前
interaction，然后 attach。它不新建 Run/Hold、不重放 effect、不改变 workspace binding。

### CLIENT-05 — Fork from a point

用户明确选择 Message/Task point、预览继承上下文和新费用边界，再创建新 branch/session 与 execution root。保留 parent
lineage，但不复制 GA checkpoint、旧 Hold、target permission 或 uncertain effect。

### CLIENT-06 — Start a new run

用户提交新 intent，使用当前 Site/Profile/Plan/permission 重新 Quote/Admission。unknown/failed 旧 Run 不能被 UI 伪装成
retry；相同外部 effect lineage 未收口时 Admission 阻止可能重复执行。

### CLIENT-07 — Approve and observe local action

用户看到 exact action、argv/operation、resource/path、cwd、network、duration 和 risk，选择一次、会话内或拒绝。effect point
重新校验 target/revision/path/symlink/worktree/epoch；connector durable receipt 后才 ack。断线查询同 identity。

### CLIENT-08 — Offline、reconnect and multi-device

offline 可看带 freshness 的低敏 summary/diff 和编辑加密 draft，不 flush command queue。reconnect 先刷新 OAuth、manifest、
target revision，再加载 snapshot+SSE。另一设备已批准的 HITL/permission 不自动扩权当前设备。

### CLIENT-09 — Revoke、logout and recover

用户可撤销当前 session、device 或所有设备。epoch 在 SLO 内终止 refresh/API/SSE 和新 target effect；已提交 unknown effect
进入 reconciliation，不宣称 cancel。Support 只能通过 action-bound verification 和安全 bundle 协助。

## 5. User-visible states and recovery

| State | Explanation | Allowed recovery |
|---|---|---|
| signed_out / authorization_pending | 未授权或等待 browser/device flow | login、cancel、restart same flow |
| device_registered / restricted / revoked | 设备可用、受 policy 限制或已撤销 | step-up、inspect policy、re-register、Support |
| current / update_recommended / update_required / revoked_release | client 版本状态 | signed update、export draft；required/revoked 禁新 effect |
| target_unbound / ready / permission_required / stale_binding | 本地工作空间与权限状态 | bind、inspect、request exact permission、rebind |
| connected / reconnecting / offline | transport 状态 | wait、reauth、save draft；不 replay effect |
| attached / waiting_interaction / terminal_view | 当前 Task/Run 可继续或仅查看 | respond、detach、explicit fork/new run |
| action_pending / running / unknown / reconciled | 本地 effect 生命周期 | approve/cancel-before-effect、query same identity、wait/Support |
| incompatible / feature_disabled | protocol 或 Site 未开放 | signed update、use supported surface；不 fallback internal API |

任何 error/partial/unknown 必须绑定 RecoveryActionCatalog。`action_unknown` 只能 `wait_and_refresh`、query/reconcile 或
Support；不得提供普通 retry。

## 6. Functional requirements

### Identity and client trust

- public client 不含 client secret；PKCE S256、state、nonce、exact redirect 与 Site issuer/audience 强制。
- token 存 OS credential store/受限 helper；禁止 repo、env、shell rc、日志、analytics 与 crash dump。
- ClientReleaseAttestation 绑定 digest、signature、SBOM/provenance、protocol 和 revocation；marketplace 状态不单独可信。
- Site A 的 token、device、grant、cache、deep link、Task 或 Target 在 Site B 统一 secrecy-preserving deny。

### Task and session

- feature discovery 只读取签名 manifest，不猜 server version，不因 unknown field 降级到内部 endpoint。
- attach/fork/new_run 使用独立 typed command、idempotency digest 和 user-visible confirmation。
- Session snapshot 是长期页面 projection；SSE 仅 incremental/bounded replay。客户端不请求 GA checkpoint。

### Local target

- action schema 有限且版本化；不接收任意 remote code envelope。
- shell/command 冻结 argv、cwd、env allowlist、timeout、output、network/sandbox；secret 使用短期 non-persistable lease。
- path traversal、symlink、mount、nested repo、worktree 与 ownership 在 effect point 重验。
- connector 仅 outbound authenticated channel，默认不开放本地公网 listener。

### Offline、privacy and accessibility

- 离线缓存按 Site/subject generation/client profile 加密分区；logout/Site switch/revoke 按 policy 清除。
- telemetry 不含 path、repo URL、prompt、diff、command/output、token；Support bundle 用户 review、字段/大小 manifest、短期 delivery grant。
- CLI 提供 screen-reader-safe 文本、稳定 exit code、非颜色唯一提示；Desktop/IDE 满足 keyboard/focus/zoom/reduced-motion；device flow 不依赖二维码作为唯一方法。

## 7. Admin and support

Admin 提供 typed workflow 管理 client definition、release attestation、minimum version、revocation campaign、feature manifest、
device/target restriction 与 incident。高风险 publish/revoke 使用 expectedVersion、reason、step-up、maker-checker 和 audit；
不能直接改 device/token/session/target 表。

Support Case 可安全关联 Site、client/release、device、OAuth request、Task/Session、target/action receipt 与 correlationId，但默认
mask 本地 path、repo、prompt、diff、command/output。Support 不索要 token/code，不远程扩大 permission，不通过“重装/重试”
掩盖 unknown effect。

## 8. Edge cases and failure policy

| Case | Required behavior |
|---|---|
| browser login completed but client response lost | query same OAuth/device identity；不要求粘贴 token |
| device code expired/slow_down | typed expiry/backoff；新 flow 新 identity |
| user switches Site with same email/repo | clear selection/cache partition；重新 Site authorization |
| client revoked while Task running | stop new effect；Task 继续由 owner runtime 收口，可从受支持 client attach |
| connector crashes after local effect | persist/query same action receipt；unknown no retry |
| workspace root or worktree changed | stale_binding；new revision and authorization |
| two devices answer same HITL | owner CAS 接受一个；另一端显示 already resolved |
| protocol adds security-required field | incompatible fail closed；signed update path |
| offline draft conflicts | explicit compare/merge/new intent；不自动提交 |
| deep link points wrong Site/Task | secrecy-preserving deny；不自动切 Site |

## 9. Acceptance criteria

### AC-CLIENT-01 — Site isolation

```gherkin
Given one installation has separate grants for two Sites
When any token, device, cache, task cursor or target grant is crossed
Then authorization rejects without revealing resource existence
And local state remains partitioned
```

### AC-CLIENT-02 — Public client authentication

```gherkin
Given the package is fully inspectable
When a user signs in through browser or device flow
Then no embedded client or Site workload secret is required
And codes and tokens never enter shell history, logs or analytics
```

### AC-CLIENT-03 — Attach has no effect

```gherkin
Given a Run continues while another device attaches
When Session snapshot and bounded replay are loaded
Then the same Task and Run are shown
And no Run, Hold, Provider call, target action or terminal is created
```

### AC-CLIENT-04 — Fork creates new authority

```gherkin
Given the user forks from an earlier point
When the fork is admitted
Then lineage is preserved but execution root, Hold and authorizations are new
And no GA checkpoint, uncertain effect or target grant is copied
```

### AC-CLIENT-05 — Unknown action cannot replay

```gherkin
Given a local action may have executed before disconnect
When any client reconnects
Then the same action identity is queried and reconciled
And no queue, retry, fork or new run silently executes it again
```

### AC-CLIENT-06 — Exact permission

```gherkin
Given an approval covers one target revision, action and resource set
When path, symlink, worktree, command, network need or revision changes
Then effect is denied until a new current approval exists
```

### AC-CLIENT-07 — Revocation closes channels

```gherkin
Given refresh, SSE and connector channels are active
When the device or grant epoch is revoked
Then refresh, API, SSE and new target effects stop within SLO
And submitted uncertain effects remain truthful and reconcile
```

### AC-CLIENT-08 — Compatibility fails closed

```gherkin
Given a client lacks a required security field or trusted release
When it loads the feature manifest or submits a command
Then new effects are blocked with a signed update path
And no internal endpoint fallback occurs
```

### AC-CLIENT-09 — Offline is draft-only

```gherkin
Given the client is offline
When the user edits a draft and local files change
Then no server or local effect is queued for automatic execution
And reconnect requires current auth, manifest, binding and explicit submit
```

### AC-CLIENT-10 — Support cannot expand access

```gherkin
Given a user opens a client support case
When diagnostics are collected
Then the user reviews a redacted bounded bundle with expiring delivery grant
And Support receives no token, secret, raw path or reusable target permission
```

## 10. Verification and release gates

- OAuth/device：PKCE/state/nonce/redirect、poll backoff、refresh replay、Site audience、logout/revoke。
- supply chain：signature/digest/SBOM/provenance、rollback attack、minimum version、revoked release。
- client security：credential store、deep link、IPC/plugin isolation、cache partition、telemetry/crash redaction。
- target：path/symlink/worktree/argv/env/network/sandbox、permission race、disconnect/unknown、receipt idempotency。
- product：attach/fork/new run、multi-device HITL、offline draft、Site switch、a11y、Support recovery。
- operations：reconnect storm、device fleet revoke、update campaign、signed manifest outage、kill switch。

No-Go：embedded secret；粘贴 token 登录；跨 Site grant/cache；直连 GA/Provider；public `ga.*` scope；客户端读取
namespace/checkpoint；offline effect auto-flush；attach 创建 Run；fork 复用 Hold/target grant；任意 remote code；
未签更新、unknown required field 或 revoked release 被静默忽略。

## 11. Dependencies and risks

| Dependency/Risk | Mitigation |
|---|---|
| Identity OAuth/device flow 与 Device Registry | PRD-01 与 Client Access contract 联合认证 |
| Session snapshot/SSE 仍未达到目标 | Client release blocked，不能用客户端缓存掩盖 |
| ExecutionTarget/local connector 权限复杂 | PRD-A2 owner + effect-point negative/chaos suite |
| IDE/OS credential store 差异 | per-platform adapter qualification，不自行降级明文存储 |
| 客户端成为第二套 runtime | architecture test 禁止 GA/Provider/internal RPC dependency |
| 支持旧 client 造成安全字段忽略 | protocol range + minimum security release + expiry campaign |

## 12. Related documents and approval boundary

- [Client Access architecture](2026-07-25-client-access-plane-developer-client-design.md)
- [PRD-01 Identity](2026-07-25-prd-01-site-identity-and-account-security.md)
- [PRD-05 Chat](2026-07-25-prd-05-chat-conversation-run-and-interaction.md)
- [PRD-A2 Target/Device/Permission](2026-07-25-prd-a2-target-device-permission-and-interaction.md)
- [PRD-A3 Developer Workspace](2026-07-25-prd-a3-developer-workspace-context-and-multidevice.md)
- [Session production transport](2026-07-25-session-http-sse-production-transport-design.md)

本文批准不授权实现，也不授权 GA runtime 变化。任何为客户端暴露 GA control/checkpoint、改变 namespace、tool、
Handoff、cancel、terminal、event order 或 checkpoint schema 的提案必须停止并与用户专项对齐。
