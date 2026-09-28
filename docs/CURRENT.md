# Root 当前组合

状态日期：2026-09-28。Root 是 Git superproject，精确组合以当前提交的 gitlink、`.gitmodules` 与
[`verification/contracts/consumer-inventory.json`](../verification/contracts/consumer-inventory.json) 为准。
业务源码、canonical Schema 和可编辑契约仍由各子仓 owner 维护。实施任务见 [`task.md`](task.md)，
已执行命令与失败记录见 [`progress.md`](progress.md)。

## 当前推进边界（2026-09-28）

IAM `4d981441d154c83b63987f284e3a82a559595870` 的 0.7 owner 切片已发布，不等于整个登录及产品能力完成。固定 Web/BFF/IAM/Agent 组合曾通过隔离真 Chromium 的登录、OAuth 回跳、Product Session、私有聊天、AG-UI 与刷新；其中 System/模型为确定性 fixture，旧 3310 常驻实例没有在本轮热替换。因此“登录写完”是先前错误的完成口径，必须按具体来源与链路分别报告。

W2 当前 Storage `ef0fd7779bf434120ac1f8a58592222f534a7c45` 与 BFF `31c4803b3df0e90c031a97844f89df384ca1a35c` 已发布项目资源 ListAssets→GET；Web `a0e41a72fe4eae6a8076e5126a8daaa15eecd90a` 已发布正式 Project 创建、多文件逐项上传与 owner GET 列表。Root 在隔离真实 PostgreSQL/Redis/MinIO/ClamAV 组合验证上传、幂等重放、签名 GET 原字节、持久列表重载、cursor 分页、私有拒绝和感染拒绝，自有数据库/对象/bucket 已清理。Web 最终 Node22 全门由 Root 独立复验：contract 83/83、architecture 36/36、test 1511/1511、lint/typecheck/build PASS，独立端口 Playwright 11 pass/1 预期 skip。Root 新增的隔离 Chromium 项目资源 runner 静态/归属检查 18/18、Root 全量 `scripts/tests` 775 pass/187 subtests；**当前精确组合的真实浏览器创建/上传/刷新仍待运行**，不把后端 smoke 或 Web stub 测试冒充浏览器产品闭环。

W2 浏览器验收前发现正式 Web “新建项目”只生成 `preview-project-*`，没有调用 BFF Project 创建 API。Web owner 已修正式侧栏与欢迎页入口：BFF POST 严格回执后按 canonical id 导航，未知结果同键重试，Direct/Project 草稿分键；预览 fixture 独立保留。Root 将从用户点击开始做真实 Chromium 验收，而不是在测试中预造项目掩盖缺口。当前用户 3310 仍是旧隔离预览进程，未热替换为此提交。

## IAM 0.7 与 BFF 窄消费者历史基线（2026-09-28）

IAM main `4d981441d154c83b63987f284e3a82a559595870` 已发布 Organization Skill 12 动作、user-delegated 专用 scope、同快照具名 check、`0.7.0` OpenAPI/公开 SDK 与真实 Better Auth/PostgreSQL/HTTP 测试。Root 独立 `pnpm verify` 为 102 文件/938 测试 PASS，完整 IAM integration 在原代码候选为 37 文件/280 测试 PASS；最终旧/新 refresh+Code/consent 补测后 Root 独立聚焦 OAuth 3/3 PASS、writer 全量 integration 280/280 PASS。BFF main `815cf564fcbfda9a7d83ab8bb7364fe5fe7df4ff` 已固定 IAM 0.7 窄 Skill client，现另固定 Platform 两份 Proto 并生成 Connect wire；Root Node22 `pnpm format:check && pnpm check && pnpm schema:check` 为 319 pass/1 skip、schema 5 pass/1 skip。**这不是 IAM 或 Product 全链写完**：BFF 尚无 Skill mutation route/credential/digest，Web 仍请求旧 scope，真实 IAM→BFF→Platform 用户链未验，`EDGE-BFF-IAM` 保持 broken。3310 是先前单组临时预览，未以这些新提交热替换运行进程。

BFF 的 Product Skill 四 scope/六 mutation 文档仍只是目标评审，public mutation 运行代码和机器 OpenAPI 未发布。Platform main `ae48c894d9034016a16a4cbaa60ab80743d1aab9` 的运行代码仍是前一 `f26d147` 发布的六 catalog RPC Product context/owner gate 与 execution artifact v2/2.0.0；本次仅追加 v3 机器投影目标设计文档，未写 artifact/runtime。Root 独立 Node24 前片 `pnpm format:check && pnpm verify && pnpm build` 为 819 pass/179 skip，本片 `pnpm format:check` PASS；真 PostgreSQL/Connect 因指定隔离端口不可达仍待验。Storage Begin/Complete 与 Platform 不可变包绑定未接通，因此 Validate/Publish fail closed；BFF public mutation、Web 新 scope 与跨仓消费者亦未完成。不能把 BFF IAM 窄 client、Platform 单仓发布或 BFF generated client 列作 Product 闭环。

## W2 项目资源首片历史基线（2026-09-28）

Storage main `91a8748` 仅新增真实个人附件回环测试及测试 fixture 修复，运行代码/Proto/Schema不变；本地 HTTP MinIO 的真PG/ClamAV验证不代表 production HTTPS。BFF main `815cf56` 固定 Storage v2 Proto `094847da` 的原字节（当前 Storage Proto digest相同），新增 Project 单文件 multipart→CreateUpload→受限PUT→Complete/CLEAN Asset 纵切及持久checkpoint恢复，移除该 POST 的旧503。Root Node22全门319 pass/1 skip、contract28、schema5/1 skip。独立审查指出 Web 仍允许多文件、15秒代理短于 BFF45秒、每次新幂等键且资源列表只保留本地乐观假数据；真实BFF+Storage+ObjectStore/浏览器未跑，`EDGE-BFF-STORAGE`与`EDGE-WEB-BFF`保持broken。本片不是附件/Library/Web完整闭环。

## 3310 临时登录入口历史实测（2026-09-28）

当前 Web main `a7decb69e3f29bf6d0a1988899f107e39964af99` 修复独立 HTTPS TLS 代理下登录表单 rewrite 错误；Root 独立 Node22 `pnpm check` 为 contract 69、architecture 36、unit 1481、lint/typecheck/build PASS。Root 首次以修复前 Web `40a2095` 和当前 IAM/BFF/Agent 执行隔离真 Chromium，在 `/auth/sign-in` 500 停止，Next 将表单 rewrite 错转为 `http://` 公共 TLS 端口（`ECONNRESET`）；修复后首次运行发现 Root 浏览器脚本仍匹配旧英文“Sign in”，已按当前可见中文“欢迎回来/登录”更新脚本与断言。最终固定 Web `a7decb6`、BFF `61b8074`、IAM `4d98144`、Agent `d6fcbf2` 的真 Chromium 隔离组合 **PASS**：同一浏览器完成表单、OAuth/Product Session、DOM 首消息 202、AG-UI 五帧、一次 SSE cursor 断线恢复与刷新后一对 user/assistant；同租户其他成员私有 404，跨租户准入 403。测试自有 PostgreSQL 数据库、Redis DB7/14/15 keys 与进程剩余均为0，旧 3310 未触碰。该组合使用确定性 System/模型 fixture，不是实际模型 provider、常驻 3310 更新或全产品完成证据。

旧预览的 IAM 后端退出后，`/login` 曾 302 到返回 `iam_relay_unavailable` 503 的 `/iam/oauth2/authorize`；此前截图不证明当时的当前态。Root 仅替换已确认归属的旧 Web/BFF PID 88923/88920，使用 `scripts/dev/serve_local_login.py` 重新启动单组隔离 IAM/BFF/Web（supervisor PID 62862，IAM 62935，BFF 62984，Web 62986；另一个旧 BFF PID 81924 未触碰）。新组合的 `GET /login` 经 IAM 到 `/auth/sign-in` 200，Browser 目视邮箱/密码表单、无连接中/整页重试；同一临时账户 HTTP 实测凭据提交 → consent → `/app` 200。fixture 创建独立测试数据库/Redis 前缀，未改变正式子仓发布 commit 或 Billing/Platform 状态；当前预览是进程存活时的临时开发验收，不是生产部署或长期在线保证。

| 子仓 | 当前固定提交 |
| --- | --- |
| `apps/kokoro-app` | `a0e41a72fe4eae6a8076e5126a8daaa15eecd90a` |
| `apps/kokoro-bff` | `31c4803b3df0e90c031a97844f89df384ca1a35c` |
| `apps/kokoro-agent` | `d6fcbf2424ea6a936bb53f4dc1be95d13f78f2e0` |
| `apps/kokoro-iam` | `4d981441d154c83b63987f284e3a82a559595870` |
| `apps/kokoro-system` | `c0a76a3a7614bf46ea6e665e523f24261862436f` |
| `apps/kokoro-storage` | `ef0fd7779bf434120ac1f8a58592222f534a7c45` |
| `apps/kokoro-scheduler` | `975dee59616a1e0eda609aa69283401344900d83` |
| `apps/kokoro-capability` | `ae48c894d9034016a16a4cbaa60ab80743d1aab9` |
| `apps/kokoro-billing` | `63e0ab6e61b397f23f7ab71f5d6dc9df3d6de0fa` |
| `apps/kokoro-mori` | `ca76c2e12861a2e4a6af3049f6df8c34b417c158` |
| `libs/kokoro-web-shared` | `0c4e87ace01340aaa07bc57935f1d98b8e77af14` |

`kokoro-app` 是本轮唯一正式前端；Mori 不在本轮业务改造内。正式能力仓当前仍是
`kokoro-capability`，尚未完成向 `kokoro-platform` 的原子切换。各子仓自行持有测试；Root 的
`scripts/tests/` 只覆盖 Root 治理脚本，不是业务单元测试总目录。
子仓的 tests 不迁入 Root；业务回归仍在各自 owner 仓执行。
`verification/` 保存跨仓来源库存与验收检查点，不承载子仓业务测试代码。
Platform 已发布单一 `kokoro.platform.v1` Proto、IAM 0.6 ingress 与 `kokoro_platform` 同库 owner schema；Agent 已固定同一 Proto 的只读 vendor 输入、官方 Python Connect generated client 和 24 个 tenant operation 的 request-binding projector，并在 worker 装配租户凭据、IAM token、DB lease 证明与六个 generated Connect RPC。Agent 仍未把 typed Skill/MCP 产品声明接入此 sender；Storage 已窄放行 Platform 原 scope 干净包的 GetPackageReference，但 Platform 仍消费 v1/body tenant/裸 URL 且缺包 scope/manifest，BFF/Web 选择链与真实 IAM→Platform→Agent 三 owner 组合也未验收；不能把 transport/loopback fixture 当作能力激活。Root 库存继续校验 owner OpenAPI 的声明版本与已提交 `info.version` 一致。

## IAM 0.6 固定租户登录与 relay 历史来源

W1E IAM 0.6 历史组合：IAM main `a4c2b61` 已发布 Platform ingress 运行端点/OpenAPI/SDK；BFF main `1105553` 只把完整 IAM owner OpenAPI `0.6.0` 精确 vendor/生成来源/浏览器 policy provenance 重钉，既有 16 个 generated 文件与 browser relay 路由不变；Web main `40a2095` 当时固定 BFF policy `2.1.0` SHA-256 `8f7d4f4cb6fa0ec34d2cce8702d8882d3270a316a6cbdb2d8bdaccefb9c6b4a1`。IAM Node24 97 文件/883 unit 与 36 文件/265 真实隔离 integration、BFF Node22 292 pass/1 skip、Web Node22 1478/1478 最终全门已由 Root 独立复验；Web 首轮全量一个 OIDC refresh 真 HTTP 用例间歇失败，聚焦 38/38 与第二轮全量均通过，仍需单独稳定化。此段不代表当前 IAM/BFF gitlink；Platform 消费者和六 owner 真组合仍待执行。

以下为先前固定组合的历史验收，不是当前 IAM/BFF/Web 来源：

Web main `1fa25d2b4760dc428d3fcdf77628ba343a5bc3ff` 已发布真实 shadcn 登录表单；Root Node22 `pnpm check` exit0（contract 69、architecture 36、Vitest 1478、lint/typecheck/build），3310 临时组合已按明确文件热同步且未重启进程。全新 Chromium 实测 `/login` 302→302→200 到同一邮箱/密码表单、旧重试/连接状态 0；一次无效凭据提交后仍在表单就近报错且密码清空。下面旧三仓组合与无脚本 Route Handler 描述是此前 Root pin 的历史状态；本次仅提升 Web gitlink，不冒充 IAM 0.6/BFF 来源或 Platform 完整闭环。

W1D 历史固定 IAM `b720b6d`、BFF `c586d0b`、Web `9fc2fef`。IAM 仅为本地/测试固定 HTTP loopback 提供显式 native OAuth client，生产 web HTTPS 约束不变。`/login` 在服务端直接启动 Product OIDC，正常 302 经 BFF/IAM 到 Web 唯一签名 `/auth/sign-in` 邮箱/密码表单；没有可见“连接中”或整页重试页。表单为中文紧凑布局，遵循 Web 现有 shadcn 语义色和 Card/Input/Button 尺度；由于它同时签发 Cookie-bound 一次性 CSRF，仍由现有 script-free Route Handler 输出，不冒称直接引用 React 组件。BFF relay policy 已固定当前 IAM commit，Web 原样消费其发布字节。IAM 已发布 `platform:execute` 目录及具名 execution verifier/OpenAPI `0.5.0`/SDK，Root 独立验收 IAM 92 文件/846 单测及真实 PostgreSQL/Redis/JWKS HTTP 8/8；BFF Node22 `pnpm format:check && pnpm check` 292 项中 291 pass/1 既有 skip；Web Node22 `pnpm check` contract 69、architecture 36、Vitest 1475、lint/typecheck/build 均通过。当前三仓精确 SHA 的隔离 HTTPS Product Session S1 已实跑首登邮件→OIDC→会话→issuer logout、Team 同源 HTTP 与 Chat proxy，通过且测试自有资源清零；该 runner 使用 CookieJar/HTTP，Chromium DOM 在这一新组合仍待验。Platform ingress 身份契约、consumer 原子切换、真实 Agent signer 和六 owner 组合也仍未完成，不能将 IAM 单仓 E2 当成授权链闭环。

Root 已按进程所有权正常停止旧隔离预览并清理其自有资源，以 W1D 固定 IAM `6a55ffb`/BFF `bc45632`/Web `942d22e` 重建 3310 本地临时组合。真实 `GET /login` 经 IAM authorize 到中文签名表单为 200；Codex IAB 目视无连接/整页重试，临时账号提交到 consent 后继续进入 `/app`，页面显示工作区/输入区。当前 W1E 三仓仅更新角色权限与来源 pin，尚未重建 3310；该实例是可交互的**临时测试租户**，不是正式部署。Issuer 最终退出仍未在当前 HTTP 组合验收。后续 Chat/Storage/其他 11 条 declared broken edge 未因此闭环，Billing 仍最后。

W1D 历史组合提交 `b5738127ab98e9a2ef1cc2f4ee1d681a88e07255` 已将 IAM/BFF/Web 三 gitlink、16 edge 来源库存与 IAM `0.5.0` 验证器固定；`verify-iam-relay-policy.py`、topology、W1D checkpoint 及单独的治理验证器 36/36 均 PASS。Root 全量 `scripts/tests` 在验证器修复前为 741 passed/187 subtests；修复后全量尚待重跑，不用此前结果冒充当前提交。完整 compatibility 仍 `FAIL`：16 edges、0 illegal、11 declared broken；十仓标准门仍未通过，具体违反项以当前命令为准。

## 已验证到的边界

- Web `08ef650a` 已把两个不被当前 UI/正式 OIDC 使用的旧 magic-link browser route 实际删除；失败回调不再产出 `/login?auth=link_unavailable`。正式 Auth.js `/api/auth/callback/kokoro-iam` 保留。Root `54e18142` pin 后的隔离 HTTPS first-login smoke 再次 PASS，自有资源0；Web 隔离新目录的 Next typegen、TypeScript 和 production build PASS，未改用户 3310 共享 `.next`。旧 auth helper、Team/其他认证路径尚在，普通 IAB 3310 入口依旧未配 IAM/BFF。

- 当前固定 IAM `093b7651`、BFF `7a7f3adf`、Web `0f5aec47` 已由隔离 HTTPS Product Session runner 实测：`/login` 302 直达真实 IAM 邮箱/密码表单，无可见连接中或整页重试；新账号在未验邮件时 403，经真实 TCP SMTP 邮件中的链接由 Web→BFF→IAM GET 验证，随后以新账号/新测试 tenant 完成 OIDC、Product Session、Chat 代理与退出，自有资源剩余 0。注册与建租户由测试 setup 直连 IAM loopback；IAM host 仍预置测试 owner/tenant/client，因此这不是空库首租户开通，也不是当前仅运行 Web 的 `3310` 正式入口。Web Next typegen/build 与普通 IAB 可见 HTTPS 入口仍待单独验证。

- BFF `928ada2` 增加固定 IAM 邮箱验证 GET relay，Web `24445a1` 固定消费其 policy `1.1.0`：真 Next HTTP/Chromium fixture 验证 token query、同源 200/302、最终 `no-store`/`no-referrer`、跳转后请求不带 token Referer、Next 开发 incoming log 不输出验证 token，外域/错误方法/路径别名/重复 query 拒绝。Web Node22 本片 Root 独立聚焦测试 13/13、contract 56/56、architecture 32/32、lint、`tsc --noEmit`、全量 Vitest 1414/1414 通过；未触用户 3310 `.next`，正式 build/Next typegen、真 IAM 邮件点击与普通 IAB 可见登录仍待验证，不把 fixture 当成用户当前可用入口。
- IAM `c16a9bc` 已用真实 TCP SMTP 邮件证明新用户未验证登录拒绝、验证链接生效、持久 `emailVerified` 与后续 issuer Session；BFF `a50f987`、Web `5192ff0` 仅顺序重钉该 IAM 来源与原始 relay policy blob，路由/安全边界未变。IAM owner 全门 740/740、SMTP integration 4/4；BFF 270/1 skip、Web 1414/1414 通过。真实跨仓首次邮件点击与普通 IAB 可用入口尚待独立组合验证。
- Web `/` 是固定单租户公开首页；`/login` 已删除可见连接中/整页重试组件以及失败时共用的假登录页面，服务端启动固定 Product OIDC，
  成功后浏览器直接进入真正的 IAM `/auth/sign-in` 邮箱/密码表单；不依赖 System manifest。
  Web `a70dd24` 进一步删除 RP `signin` 失败时 303 跳回重试页的残留分支；失败返回原状态的结构化错误，不再生成失败页 Location。
  `/app` 只以 Product Session 作认证闸。仅 Web dev 在 3310 运行时，缺少常驻 BFF/IAM/RP 配置，
  `/login` 返回空 body 的 HTTP 503，不是在线登录入口；没有后端不伪造可提交的凭据表单。
- 固定上述 IAM/BFF/Web 提交运行的独占真实 HTTPS Product Session smoke 已通过：Web 同源入口、
  BFF/IAM 协议链、在线会话、Chat 列表 Bearer 代理与退出，测试自有资源剩余 0。这不是 3310 常驻
  服务的证明，也不覆盖首条消息、Agent worker、Web 重载或真实模型 provider。
- 本轮 IAM `c16a9bc`/BFF `a50f987`/Web `5192ff0` 重新执行上述真 HTTPS Product Session runner，修正 Root 对 `Cache-Control` 的过窄字面断言后 `status=passed`、自有资源剩余0；其 IAM 测试 host 预置 verified user/tenant/client，尚未证明真实邮件从 Web relay 点击到正式固定租户首次登录。
- Agent 已发布 typed `createRun`/`replaySessionEvents` 契约及空最终文本完成事件；BFF 已完成
  新会话首消息事务、assistant Message 与 AG-UI 同事务投影，并固定生成的 Agent HTTP 消费者。
  Web 已按 BFF 严格 MessageCreate 契约发送首消息。固定 BFF/Agent SHA 的 Root 真 HTTP + 独立
  CLI worker 首消息组合已通过，覆盖幂等、Agent 执行、AG-UI 与持久重载。Root R2b 进一步把真实 IAM
  Product Session、Web 同源 JSON 首发、BFF 与独立 Agent CLI worker 放在同一次隔离 HTTPS 运行：202、
  同 key 重放、改 body 409、Web 重载 snapshot 与 AG-UI 5 帧通过；测试自有 PG/Redis/进程归零。
  此处使用 Python CookieJar HTTPS 客户端，不执行真实浏览器 JavaScript；System/模型 HTTP 是严格
  确定性测试 fixture。该 R2b 证据本身不包含 Chromium/DOM 首发、跨 tenant 私有负例或真实 provider 验收。
- 固定 Web `175a6d805b69b88c1478b86164fdcbfe925f498a` 的 R2f 真 HTTPS Chromium 组合已 PASS：
  `/login` 在服务端启动 OIDC，浏览器不再请求可见 CSRF/signin 中转页，直接进入带签名 query 的 IAM
  邮箱/密码表单；同一 Chromium 原生提交凭据、选择 tenant、确认 consent，取得 Product Session
  HttpOnly/Secure/Lax cookie 与同源 session projection 并进入 `/app`。随后独立 Python CookieJar
  完成 Web/BFF/Agent worker 首消息与持久回归；自有 PostgreSQL/Redis/进程剩余0。后续 Web 文档提交
  `9794a286` 不改运行代码，Root 来源已重钉，并在该精确 SHA 复跑同一组合 `status=PASS`、资源剩余0。
  在该次验收时 Chromium 尚未发送 Chat、验证实时 AG-UI/断线恢复，真实模型 provider 仍未执行；当时 3310 仅运行 Web，
  没有常驻 RP/IAM/BFF。后续 Chat 浏览器组合与临时 HTTPS 联调入口见本文件当前状态，不以旧 HTTP 标签作登录证明。
- Web `067d7ea` 已修正真实 BFF AG-UI 终帧/工具错误字段的严格解析，并只对 Chat events SSE 采用首部连接 deadline + 可续空闲 deadline；Web 当前 Node22 单仓 `pnpm check` contract56、architecture32、unit1408、lint/typecheck/build PASS，独立只读审查0 P0/P1/P2。Root 已以此精确 SHA 真 Chromium 跑通 IAM登录→DOM首发→真实Agent worker→AG-UI助手DOM→刷新一用户一助手；随后测试自有 TLS proxy 将首次 SSE 截在一个完整帧后，浏览器携该帧 `Last-Event-ID` 重连、恢复助手DOM并保持刷新后一对消息，BFF五帧 cursor 唯一，测试自有资源清零。此证明固定 fixture 的浏览器 Chat/断线恢复，不代表3310常驻IAM/BFF、真实模型 provider、跨用户私有矩阵或全产品完成。
- Web `9e2eb73` 在同一 `/login` 路由不变的前提下，进一步删除九语种 54 条不再使用的连接中、整页重试和旧 handoff 文案；Node22 `pnpm check` contract56、architecture32、unit1408、lint/typecheck/build PASS。Root 固定该 Web gitlink 再跑真 HTTPS Chromium 登录/Chat/一次断线恢复 `status=PASS`，测试自有 PG/Redis/进程剩余 0。当时 Web-only 3310 的 `/login` 返回空 body 503；后续前台临时 HTTPS 联调入口见上文，仍不等于正式租户部署。
- 本地 PostgreSQL/Redis 复用一套实例与应用凭据，数据 owner 各自使用 schema/连接边界；
  Root 不要求此阶段拆分多个数据库角色，不允许跨 owner SQL。Storage owner schema 已有独立验证，
  但 Storage 用户文件链尚未与 Web/BFF/Agent 闭环。

## 仍未完成

1. R2c 已在固定隔离组合中证明 Chromium/DOM 首消息→BFF→Agent worker→实时 AG-UI 与一次受控断线恢复；仍需
   Web 对 BFF public contract 的全量 generated 消费、单一 AG-UI 网络协议门、默认个人私有/显式分享/跨 tenant
   负例以及真实 provider 验收。固定 fixture 不等于正式单租户常驻入口已具备完整能力。
2. Team Product 的 Web→BFF→IAM 同源 HTTP 读链已通过隔离组合；仍需 Chromium DOM、邀请邮件入口与写操作的浏览器端到端验收。
3. Storage/Platform/System/Scheduler 各自 owner 的能力调用、契约与数据闭环；Billing 最后。
4. 当前 inventory 的 13 条 broken edge 仍开放；旧 Web→IAM 非法旁路已删除并从当前 inventory 移除，不能因为局部 smoke 通过而将剩余 edge 标绿。

当前可执行门：`python3 scripts/verify-repository-topology.py`、
`python3 scripts/verify-contract-checkpoint.py --expected verification/contracts/checkpoints/w1e-iam07-bff-pin.json`、
`python3 scripts/verify-iam-relay-policy.py`、`python3 scripts/verify-main-only.py` 和
`python3 -m pytest scripts/tests`。旧 `verify-ten-repository-full.sh` 与
`run_stage2_owner_health.py` 的共享状态编排已暂停；它们不是当前全仓验收证据。
