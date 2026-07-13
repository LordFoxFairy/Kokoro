# 23. Platform 运营台（现状事实）

状态：正式册（均为 kokoro-platform 已落地并有代码/子仓 docs 支撑的当前有效事实；§6 内部信任面已随 Wave 1 TRUST-ROUTES 闭合）
事实源：`kokoro-platform` 子仓代码与 `kokoro-platform/docs`（只读取证）
上级：[02-platform-architecture](02-platform-architecture.md)、[21-platform-mainchain-closure](21-platform-mainchain-closure.md)、[09-security-permissions](09-security-permissions.md)

## 0. 一句话

> platform 运营台是"网关声明式代理 + operator 身份 + 三维 RBAC + maker-checker 审批 + DB 审计"五件套：admin 网关只按各模块 manifest 声明的路由做白名单代理，不硬编码业务页面；危险变更走双人审批，全部动作落库审计；operator 身份与终端用户身份两套并行、互不复用。扩张=模块加一份 manifest，网关零改代码。

## 1. operator 身份与双认证

运营者身份有两个入口，与终端用户签发链（见 [21](21-platform-mainchain-closure.md) §2）完全分离：

- **admin 网关侧**（`kokoro-platform-admin`）：三种认证模式，缺省 `oidc`。
  - `oidc`：标准 OIDC 登录换 operator 身份。
  - `proxy`：反向代理注入 `x-kokoro-operator` + 校验 `x-kokoro-proxy-secret`，用于前置网关已鉴权的部署。
  - `dev`：本地开发直通。
- **admin-web BFF 侧**（`kokoro-admin-web`）：NextAuth Nodemailer magic-link；`signIn` 仅放行 active 运营账号。

两套 operator 认证是运营者接入网关的不同形态，与终端用户的 magic-link 签发无任何复用关系。

## 2. 三维 RBAC

operator 权限模型（`kokoro-platform-admin/src/rbac.ts` 的 `Operator{roleKey, permissions, scopeSites}`）按三个维度求交：

1. **角色**：`roleKey` 映射到角色的权限集合。
2. **资源.动作**：权限用 glob 表达（如 `credit.grant`、`credit.*`），逐条动作匹配。
3. **租户站点**：`scopeSites` 限定该 operator 只能操作授权 `siteId` 集合内的资源。

三维同时满足才放行；任一维不匹配即拒绝并落审计。

## 3. maker-checker 审批

危险变更走"发起—复核"双人流程（`kokoro-platform-admin/src/approval.ts`）：

- 状态机：`pending → approved → executed / failed`，或 `pending → rejected`。
- **禁自审**：复核者不得等于发起者。
- **至多一次执行**：复核用原子占用抢占，杜绝并发双执行。
- **触发范围**（网关 `needsApproval`）：全部危险 mutation，外加金额型 mutation 超过阈值（按 `amountMicros`）。

低危读操作与阈值内动作直接执行，不进审批队列。

## 4. manifest 网关代理

admin 网关的核心机制是**声明式代理**，不为每个模块写死页面或路由：

- 每个平台模块暴露一份 admin **manifest**（schema 见 platform-kit 的 manifest 定义），声明它开放给运营台的资源与动作。
- 网关拉取各模块 manifest（模块表含 user/site/model/credit/payment/hub，hub 走 `/hub/admin/manifest`），据此做**路由白名单代理**并防 SSRF（只代理 manifest 声明的资源路由）。
- action 必须存在于 manifest 才允许 `prepareAction`；未声明的动作一律拒绝。

这就是"扩张=加配置不加代码"在运营台的落点：新模块接入运营台=补一份 manifest，网关不改。这也是 [22](22-capability-hub.md) §3 判定"内部通信不换 tRPC"的关键理由——tRPC procedure 无法被 manifest 声明式代理。

## 5. DB 审计

operator 每次动作都落库（`kokoro-platform-admin/src/audit.ts` 的 `PrismaAuditSink` → `audit_logs` 表）：

- 执行成功、执行失败、以及**准备阶段被拒绝**都写审计，不只记成功。
- 审计与 RBAC/审批同层：谁、在哪个 site、对什么资源做了什么动作、结果如何，均可回溯。

## 6. 内部信任面（TRUST-ROUTES 已落地）

内部服务面守门已由 Wave 1 TRUST-ROUTES 闭合（platform 150aa25/f9802f1/c4b89a1，e2e 凭据强制档绿；见 [specs/2026-07-12-wave1-trust-routes.md](../../superpowers/specs/2026-07-12-wave1-trust-routes.md)）：

- **default-internal 全路由策略**：全服务路由默认内部，public 需显式声明。
- **per-caller 分级凭据**：public / runtime-internal / web-bff / admin 四级独立凭据，取代原单一共享 secret。
- **生产 fail-closed**：生产缺凭据启动失败，不再是原 fail-open 过渡态（未配 secret 直通并只告警一次）。
- 历史现状（留档）：原守门件只护 `/admin` 前缀且共享单 secret 空值直通；hub 路由曾完全无鉴权、namespace/scope 来自请求——已由 TRUST-ROUTES + HUB-AUTHZ 纠正。

即：能触达端口≠能调路由的强不变量，已随 TRUST-ROUTES 合流成立，内部信任面已闭合。

## 7. webhook 面

provider webhook 是运营台之外的 **public 等级** 入口（见 [21](21-platform-mainchain-closure.md) §6，PAY-1 已落地）：

- 路由 `POST /payments/webhooks/:provider`（`kokoro-payment`），不在 `/admin` 前缀下，不受 internal-secret guard，对外可达。
- 安全靠 **provider 签名另验**：独立 context 保留原始请求体做验签；验签密钥缺失时 fail-closed；`(provider, eventId)` 幂等入库防重放。
- stripe/alipay/wechat 的真实验签**已落地**（PAY-2，platform ac3376f+00bdcff：三驱动真验签+Subscription+refund）；provider 沙箱真跑通留运营配置后，非代码欠账。

## 8. hold 回收

credit 预留额度（hold）的过期回收已落地（`kokoro-credit`，[21](21-platform-mainchain-closure.md) §6）：

- hold 落库带 `expiresAt = now + TTL`。
- **定时回收**：进程内 sweeper 周期扫描（`setInterval`，周期由 env 配置，缺省 300s），原子把过期 active hold 转 expired。
- **手动回收**：`POST /credit/holds/sweep` 供运维触发。
- 当前无 outbox；hold→capture 的一致性靠 run_id 幂等键（见 [21](21-platform-mainchain-closure.md) §3），payment↔credit 的 outbox 补强属后续块。

## 9. 多租户 siteId 化与身份边界

平台业务隔离以 **siteId** 为轴：

- 6 个模块的 Prisma schema（site/user/payment/credit/admin/model）均带 `siteId` 列。
- 请求上下文经 `x-kokoro-site-id` 注入，写路径 `requireSite` 强校验。
- operator 的 `scopeSites` 也建立在 siteId 之上（见 §2）。

**siteId × namespace 边界**（长期铁规，见 [17](17-namespace-runtime-isolation.md)）：`siteId` 是平台业务隔离边界，只在 platform 域出现；`namespace` 是 GA/runtime 唯一隔离键，只在 session/agent/hub 运行时侧出现。二者不互相替代，platform 不把 namespace 当业务轴，runtime 不接收 siteId 作第二身份轴。
</content>
</invoke>
