# Wave 1C Web OIDC 与同源接线实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans. Each owner is implemented and reviewed separately; do not parallel-write BFF and Web.

**Goal:** Browser 经 Web 同源 `/iam`、BFF 受控 relay、IAM issuer 完成 OIDC Code+S256 PKCE 登录，Web 以自己的 Product Session 向 BFF 普通 `/v1` 请求传唯一 Bearer；旧 magic-link/team-session 直连和自报身份彻底删除。

**Architecture:** IAM 保持唯一 issuer/token/session owner；BFF 只做固定路径与方法的无用户 Bearer 协议 relay，不存登录状态、不签发 token；Web 是 Auth.js RP、Product Session 与同源 adapter owner。BFF owner contract/测试/提交先行，Web 消费冻结 BFF artifact 后实施，最后 Root 真实进程组合验证。

**Tech Stack:** IAM Better Auth 1.7.3；BFF Node 22 / TypeScript；Web Next 16.2.6、批准的 Auth.js 4.24.15 目标版本（安装前重新核对当前兼容性与 lockfile）；PostgreSQL/Redis 仅由各自 owner 复用隔离 fixture。

## Global Constraints

- Root `AGENTS.md` 与 SQL/TypeScript/API 专项手册为权威；先通过每个 owner 的 `TECHNICAL_DESIGN`、`API_CONTRACT`、`DATA_MODEL` 三文档门，再改业务源码。
- 只在 `apps/kokoro-bff` 与 `apps/kokoro-app` 写本切片，IAM 已发布 owner 协议不回退旧 alias；跨仓每次只一位 writer，Root 保留 Git index/commit/push/gitlink。
- 当前 IAM admission `0.2.0` 只校验已有 Bearer；BFF `/iam` relay 是无用户凭据的登录 bootstrap 服务例外，普通 `/v1` 仍必须在线 IAM admission。
- IAM 原生 OAuth/OIDC redirect、JSON、表单、cookie 不包装为 BFF Product envelope；BFF 不编辑、复制 IAM 的协议 schema，自己维护的是 relay 准入策略，并从单一TS policy确定性导出只读 `contract/iam-relay-policy.json` 供Web固定版本消费。浏览器到 Web 的 Product Session cookie `Path=/` 可能同时出现在 `/iam` 请求；Web/BFF 双层只转发 IAM 发布 cookie snapshot 中的精确 `kokoro-issuer.*` 与 production `__Secure-kokoro-issuer.*`，绝不转发 Auth.js/Product Session cookie、BFF service secret 或浏览器自带任意 `Authorization`。通常 issuer cookie `Path=/iam`；锁定 OAuth Provider 的 logout-confirmation cookie 使用更窄的 `Path=/iam/oauth2/end-session/confirm`，必须按精确名称/路径例外验证，不机械改写为 `/iam`。`/iam/oauth2/token` 的 Basic client authentication 只可由受信 Web server 生成，Web ingress 必须丢弃浏览器任意 Basic/Bearer；BFF 只信任已校验的 Web service 身份，不假装能凭同一 secret 区分 Basic 的原始来源。
- 默认个人私有、显式分享；Web 不把 Product Session cookie 或 Bearer 暴露给浏览器脚本、IAM issuer 或其他 owner。
- 不扩展部署/运维工作；本片只做源码、契约、真实 HTTP 与必要浏览器验收。

## 放置与依赖门

| 项 | 裁决 |
| --- | --- |
| Owner | IAM 唯一写 OAuth/Session；BFF 唯一写受控 relay；Web 唯一写 RP/Product Session/同源 adapter。 |
| 当前事实 | IAM `/iam` 原生协议与精确 allowlist 已存在；BFF 只有 `/v1` IAM admission，`/iam` 404；Web 仍直打旧 IAM magic-link/team-session、部分代理缺 Bearer。基线 SHA 见 `docs/task.md` W1C 卡。 |
| 目标职责 | BFF 在普通 `/v1` admission 前接受 Web service 身份的固定 `/iam/*` path+method，仅转发到固定 IAM origin；Web 对浏览器公开同源 `/iam/*`，Auth.js 保持 state/nonce/PKCE 与 server-only Product Session。 |
| 目录方案 | BFF 采用既有 `src/http/routes/` 的专用 `iam-protocol-relay` handler + `src/bootstrap/server.ts` 接线，不放入 `src/auth/` 用户 admission，也不建万能 upstream proxy；Web 采用既有 `src/app/` Route Handler 与 `src/lib/server/` 会话边界，不新建应用或数据库模块。 |
| 粒度 | BFF path policy、transport、bootstrap 接线分离，分别因 IAM 路由准入、HTTP 语义、安全边界变化；Web RP/session 与业务 proxy 分离，避免单文件承担登录、cookie、代理三类变化。 |
| 依赖 | Browser→Web→BFF→IAM；BFF 只依赖 IAM 发布的协议行为与固定 IAM commit/digest，Web 只依赖 BFF 发布的受控 relay/Product API；禁止 Web→IAM 直连、BFF→IAM DB、任何跨仓相对 import。 |
| 数据/API | BFF 不增 SQL/Redis 表；Web 无业务 DB，Product Session 协调只属于 Web Redis namespace；relay 是 browser-private transport policy，不新增 BFF public Product `/v1` OAuth schema。普通 `/v1` 仍按现有 IAM generated admission 验证。 |
| 删除项 | Web 旧 `/auth/magic-links`、`/bff/auth/team-sessions`、`/auth/refresh` 直连与 sealed legacy session、自报 namespace/principal、旧 team IAM wildcard；无 fallback/alias。 |
| 验证 | BFF contract/architecture/unit/integration/build + 真实 IAM HTTP；Web contract/architecture/unit/build/Playwright；Root 真实 Web→BFF→IAM 登录/刷新/退出/越权与静态 edge/main-only 门。 |

## Task 1：BFF relay 设计门与可执行路径策略

**Owner:** `apps/kokoro-bff`，唯一 writer。先更新 `docs/TECHNICAL_DESIGN.md`、`docs/API_CONTRACT.md`、`docs/DATA_MODEL.md`，说明当前/目标态、固定 path+method、服务身份、HTTP/cookie/redirect 语义、timeout/body cap、取消、错误与无数据事实；Root 审核三文档一致后才改代码。

- [ ] 锁定 IAM owner commit、`/iam` 精确 allowlist 的来源/digest 与 BFF 更窄的 Web-facing 路由集合。登录交互矩阵至少审查 discovery/JWKS、authorize/token/userinfo/revoke/end-session、`sign-in/email`、`sign-in/magic-link`/`magic-link/verify`、`get-session`、`organization/list|set-active`、`oauth2/consent|continue`；对每一路由按真实用途决定方法与是否开放，不把这份候选列表机械全开放。拒绝 `/internal/v1`、admin、dynamic client CRUD、未知/encoded alias；不能把所有 IAM vendor 路由照搬。BFF从单一运行时policy导出只读、版本化 `contract/iam-relay-policy.json`（BFF自有准入，不复制IAM schema），`contract:check` 证明deterministic drift与IAM固定provenance。
- [ ] 写 BFF relay policy 的失败测试：缺/错 service secret、任意路径或方法、编码/大小写/双斜线别名、CRLF/host/open redirect、混合 issuer/Product Session cookie、IAM down/timeout/body cap；合法 IAM redirect 到 Web `/auth/sign-in|select-tenant|consent`（带 IAM 签名的动态 authorize query）与精确注册 `/api/auth/callback/...` 必须正向保持，任意外域/未注册 Web URL 拒绝。BFF只验固定origin/path和有界、无CRLF的query，不消费、不重签IAM参数；Web以IAM原生续接校验。真实IAM HTTP必须覆盖三页带签名query。本地准入拒绝必须零 IAM socket；仅能在收到上游响应后判断的恶意 `Location`/`Set-Cookie` 允许一次 IAM I/O，但不得向 Web 输出恶意值；两类均不得写 BFF SQL/Redis。
- [ ] 实现窄 handler/transport，固定 IAM origin；只转发经校验的 issuer cookie namespace、必要协议 headers/body，不能把 BFF service secret 或 Product Session cookie 发给 IAM，不能自动跟随 redirect；只把 IAM issuer namespace 的多个 `Set-Cookie` 送浏览器，保留合法 status、`Location`、`Cache-Control`、`Content-Type`、429 `Retry-After` 与logout HTML的 `Content-Security-Policy`/`X-Content-Type-Options`/`Pragma`（均校验值）及精确 cookie Path（通常 `/iam`，logout-confirmation 仅 `/iam/oauth2/end-session/confirm`）；`Location` 仅允许固定 issuer 同源路径、批准 Web 交互页与注册 Auth.js callback/post-logout URI，拒绝任意外域或未注册内部 URL，且合法原生值不改写。剔除 hop-by-hop headers 与不可信 forwarded host。token endpoint 只接受已认证 Web service 的 Basic header；BFF 不持有 OAuth client secret，浏览器 Basic/Bearer 过滤由 Web ingress 负责并以 Web 负例证明。
- [ ] 运行 `pnpm format:check`, `pnpm lint`, `pnpm typecheck`, `pnpm contract:check`, `pnpm test`, `pnpm build` 与独立真实 HTTP IAM↔BFF relay；Root 冻结 BFF SHA/contract policy digest 并复验。

**完整真实链前置：** 现有IAM联调host只给已预consent的token，不足以证明首次OIDC。BFF本仓先以严格替身锁原生传输及真实IAM基础HTTP；Root随后先在IAM测试owner切片W1C-1F复用现有隔离fixture，开放可配置Web-origin issuer、第二个未预consent RP client与测试专用email/password，再以真实IAM HTTP对BFF relay跑Code+S256/三页签名query/tenant/consent/token/userinfo/logout/确认及429/安全header。此门未过时，W1C-1不能写“完整IAM协议已验收”；BFF不得导入IAM源码或自造OAuth fixture事实。

## Task 2：Web 同源 issuer 与 Auth.js Product Session

**Owner:** `apps/kokoro-app`，在 Task 1 BFF release 后唯一 writer。先更新 Web 三文档门，确认无持久化业务事实、Auth.js RP/Redis 协调、固定 BFF `contract/iam-relay-policy.json` 的commit/blob digest及vendor copy/consumer drift检查、CSRF/Origin 与旧路径删除列表；修改源码前读取已安装 Next 16 本地文档。

**文件放置（设计门需按当前Web源码复核后冻结）：** `src/app/api/auth/[...nextauth]/route.ts` 只挂Auth.js；`src/lib/server/oidc-provider.ts` 只处理RP/provider与受限token exchange；`src/lib/server/oidc-token.ts` 只处理server-only refresh/revoke；`src/lib/server/product-session{,-store}.ts` 分别处理请求态与Redis CAS/tombstone；`src/app/iam/[...path]/route.ts` 只转BFF固定relay；`src/app/auth/{sign-in,select-tenant,consent}/page.tsx` 处理IAM原生交互。现有`src/lib/server/auth.ts`、`session-envelope.ts`、`src/app/api/auth/{magic-link/request,callback,logout,session-state}/route.ts`及`src/app/api/team/*`必须按删除/替换清单裁决；`src/app/api/{session,hub,agents,scheduled-tasks,billing}/*`的BFF代理统一Bearer+service身份，不再自报tenant/actor。测试优先新增`tests/server/{oidc-provider,product-session-store}.test.ts`与`tests/system/{iam-relay-http,auth-browser-login}.integration.test.ts`，再更新现有proxy/architecture/UI/Playwright断言。新增依赖（Auth.js、Redis client、必要OIDC直接依赖）须固定版本/lockfile并通过供应链与兼容审查，不凭peer范围代替真实Node22门。

- [ ] 新增按 IAM 实际 OIDC + Better Auth 登录/会话/organization 交互矩阵收窄的 `/iam/*` Route Handler，经 Web→BFF service secret 转发；Web `/auth/sign-in`、`/auth/select-tenant`、`/auth/consent` 完成真实 loginPage/postLogin/consentPage 续接；只转发精确 issuer cookie，不把 Product Session cookie 或浏览器 Authorization 送 BFF/IAM；Auth.js 可信服务端 token 调用单独生成 Basic。浏览器只看到 Web origin；discovery/issuer 声明与 `IAM_ISSUER_URL` 精确一致，callback/post-logout URI 分别与 IAM client 已注册值精确一致。
- [ ] 配置 Auth.js OIDC Code+S256 PKCE、state/nonce、加密 HttpOnly Product Session cookie（仅server-only access、随机handle/generation与必要RP退出提示；当前refresh加密存Web Redis，绝不进公开session callback）、登录/tenant/consent/callback/refresh/logout；issuer cookie `Path=/iam` 与 Product Session cookie 分离。先由 IAM operator/provisioning 创建并 readback `user_delegated` client：`client_secret_basic`、`require_pkce=true`、`enable_end_session=true`、精确注册的 redirect/post-logout URI、`openid profile email offline_access iam:session-authorization.verify` scopes、绑定 internal resource；Auth.js 在 authorize/token/refresh 均发送恰好一个 `resource=https://kokoro.dev/resources/iam-internal`，以真实 IAM 断言 JWT audience 与 BFF admission 可用。Auth.js v4 的browser sign-in query可覆盖固定authorization params，Web入口必须拒绝/清除浏览器自报`resource`；默认callback不保证token request带resource，应以受限`token.request`/OIDC client `exchangeBody`和真实wire测试证明；refresh由Web server端显式token POST带唯一resource与Basic。不得以依赖peer范围或默认Auth.js行为推断已满足这些参数。
- [ ] 以 Web 自有 Redis namespace 实现 Product Session 双阶段 rotation CAS、旧 generation 拒绝与 logout tombstone；仅在 Redis value 中保存由 Web 密钥加密的当前 refresh credential，供按可信 session ID 原子撤销/取得；Redis 丢失 fail closed，不能用旧 sealed cookie 单独证明在线身份。精确状态机见下方 W1C-2F 决议。
- [ ] 所有普通 BFF `/v1` 代理统一从 server-only Product Session 取得单一 Bearer，并保留 Web service secret；删除 namespace/principal 自报 header、旧 IAM 直连配置/路由与 legacy sealed session。service-only manifest 与公开 Share 仍走各自显式边界。
- [ ] 同源 cookie mutation 缺失/错误 Origin 或 CSRF 证据一律拒绝；验证跨 tenant/同 tenant 其他用户不可见、refresh 并发/撤销、登录 callback 重放、超时及不泄密。
- [ ] 运行 Web `pnpm contract`, `pnpm test:architecture`, `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm build`, `pnpm test:e2e`；Root 冻结 Web SHA 并复验。

## W1C-2F 决议：Product Session 与 Team 切片（2026-09-23）

已发布的 Web/IAM 文档对 refresh 并发、token 存储和 logout 互相矛盾。Root 在真实 RP-only HTTPS 14/14 后，结合锁定 Better Auth 1.7.3 源码与 IAM 现有测试，裁决 V1 采用 **Web 双阶段 CAS、单次 issuer refresh、旧 generation 拒绝**，不依赖 issuer 的 30 秒 replay 窗口恢复败者。该窗口仍是 IAM 的真实协议行为，但不是 Web 正确性前提。选择是为了把跨实例竞争、响应丢失和撤销语义保持为可验证状态机；可用性上的重新登录代价明确接受，不伪称 previous-generation 恢复。

- Web cookie 为 HttpOnly 加密 Product Session，只携带随机 session ID、generation、当前 access 与必要 RP 退出提示；不以旧 cookie 的 refresh 作为撤销依据。Web Redis record 是本服务持有凭据的生命周期状态，保存 `active(g)`/`refreshing(g,reservation,deadline)`/`revoked`、固定到期和 **Web 密钥加密的当前 refresh**；key、日志、公开 session、浏览器存储均无 token。IAM 是实际 issuer grant/session 的唯一事实 owner。
- `active(g)` 原子预留为 `refreshing(g,reservation)`；仅赢家发起一次固定 Basic/resource 的 refresh，随后在 reservation、deadline、未撤销条件下原子写新加密 refresh 并提交 `active(g+1)`，才发新 cookie。败者只拒绝本请求，不撤销赢家、不触发第二次 refresh、不清其 cookie。pending、旧 generation、结果未知、Redis 故障均 fail closed；未决 reservation 到期只撤销，不回退 active。cookie 交付未知时重新登录。
- logout 凭可信解封的 session ID 原子 tombstone 当前记录并 **take 当前**加密 refresh，不要求请求 cookie generation 最新；重复 logout 不重复远端 revoke。缺失记录也建覆盖最大会话/在途窗口的 tombstone，迟到 finalize 不可复活。tombstone 成功后单次有界 revoke/end-session 并清 cookie；远端失败准确报告未确认。若 tombstone 写入结果未知，清 cookie 只能代表本浏览器清除，不能报告服务端已撤销。refresh 与 logout 并发下远端撤销结果可能不确定；锁定 Better Auth 对旧 refresh 的 revoke 会扩大到同 client/user family 且返回 400，不能称它幂等或单设备隔离。
- IAM ADR/API/TECHNICAL_DESIGN/RELIABILITY 需删去“Web 必须 previous-generation/fingerprint/jitter 恢复、单 CAS”指令，保留 issuer 30 秒 replay、真实 revoke 行为；Web 三文档同步上述唯一目标。各仓文档门完成前不写 Product Session 业务代码。
- Team 管理另走 IAM owner-first：先发布当前 tenant 的狭窄 member/invitation read、授权 scope/permission 和 machine contract，再由 BFF 固定 artifact 生成消费、发布窄 Product projection，Web 最后切换 UI/代理并删除 `/bff/*`/team-session 旧路径。待加入租户的邀请查询/接受/拒绝属于 issuer-session 路径，不借尚不存在的目标 tenant Product admission。成员资格不自动开放私人 Conversation/Project/文件。

本决议的并行面仅为不同仓的**文档收敛与只读审查**。IAM 与 Web owner 文档可以并行改写，Root 对齐后再放行 Web Product Session 源码；Team 的 IAM→BFF→Web 运行时契约仍串行发布。主控保留共享 checkout 的 Git index、commit、push 与最终验证。

## Task 3：Root 组合验收与 W1C 证据冻结

- [ ] 在独立 fixture 中运行真实 Browser/HTTP Web→BFF→IAM：首次登录、有效 Bearer、refresh rotation、logout/revoke、失效后拒绝、同租户不同人/跨租户访问拒绝；确认无 owner 数据或进程泄漏。
- [ ] 记录 Web→BFF `/iam` browser-private relay 的固定 BFF+Web commit/digest 与真实组合证据，并证明非法 Web→IAM 旁路已删除。`EDGE-WEB-BFF` 当前还覆盖 Product OpenAPI generated client 与 AG-UI consumer，**不得因登录 relay 可用而激活**；本片保留其 broken，另立 W1D 完成 Product API 全量生成消费与单一 AG-UI 协议后才运行精确 edge checkpoint。
- [ ] 子仓各自 commit/push 后 Root 提升 gitlink、更新 `docs/task.md`/`docs/progress.md`，复跑 topology、compatibility、Root tests、main-only 与 Git clean。

## 不提前宣称的能力

本计划只关闭 Wave 1C 浏览器身份接线，不代表整个 Web→BFF edge、Storage、Platform、Agent 聊天执行链、System generated consumer、Billing 或 Wave 7 组合已完成。W1D 单独关闭 Product generated consumer/AG-UI 后才可能宣布 Wave 1 完成。各 owner 的技术设计/契约/Schema 和独立验证继续按 `docs/task.md` 依赖顺序闭环。
