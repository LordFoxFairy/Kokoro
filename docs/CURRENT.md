# Root 当前组合

状态日期：2026-09-25。Root 是 Git superproject，精确组合以当前提交的 gitlink、`.gitmodules` 与
[`verification/contracts/consumer-inventory.json`](../verification/contracts/consumer-inventory.json) 为准。
业务源码、canonical Schema 和可编辑契约仍由各子仓 owner 维护。实施任务见 [`task.md`](task.md)，
已执行命令与失败记录见 [`progress.md`](progress.md)。

| 子仓 | 当前固定提交 |
| --- | --- |
| `apps/kokoro-app` | `63aca94f93095722425340a0a95985e8796a5b33` |
| `apps/kokoro-bff` | `d6dc8a0ea5a3fee7a4f54f01fefdeff0e28892e7` |
| `apps/kokoro-agent` | `520ec181a101298b4f336aad273ce003b2735955` |
| `apps/kokoro-iam` | `ac94f152daffa2293801ea4f56f98b3ae59452d7` |
| `apps/kokoro-system` | `c0a76a3a7614bf46ea6e665e523f24261862436f` |
| `apps/kokoro-storage` | `38be74ef7fb0b1ddd687c67434d898f8628068fb` |
| `apps/kokoro-scheduler` | `975dee59616a1e0eda609aa69283401344900d83` |
| `apps/kokoro-capability` | `9c88d0d934387b590bc74dae0179a587292e0253` |
| `apps/kokoro-billing` | `63e0ab6e61b397f23f7ab71f5d6dc9df3d6de0fa` |
| `apps/kokoro-mori` | `ca76c2e12861a2e4a6af3049f6df8c34b417c158` |
| `libs/kokoro-web-shared` | `0c4e87ace01340aaa07bc57935f1d98b8e77af14` |

`kokoro-app` 是本轮唯一正式前端；Mori 不在本轮业务改造内。正式能力仓当前仍是
`kokoro-capability`，尚未完成向 `kokoro-platform` 的原子切换。各子仓自行持有测试；Root 的
`scripts/tests/` 只覆盖 Root 治理脚本，不是业务单元测试总目录。
子仓的 tests 不迁入 Root；业务回归仍在各自 owner 仓执行。
`verification/` 保存跨仓来源库存与验收检查点，不承载子仓业务测试代码。

## 当前进行中的固定租户切片

Root 当前精确 pin IAM `ac94f15`、BFF `d6dc8a0`、Web `63aca94`。IAM 已发布固定租户、收件人限定 invitation context 与正式邮件 URL，BFF 已发布 policy `2.1.0` 的 sign-up 和三条独立动态 invitation relay；BFF 本仓 `pnpm format:check && pnpm check` 为 291 passed、1 skipped、0 failed，build 通过。Root 真 IAM→BFF HTTP 和 Web 独立 invitation interaction 尚未完成，故不声称邮件点击或用户页面闭环。原有 Team Product API 三读/六写仍在当前 BFF；此前固定旧 SHA 的真实 PostgreSQL/Redis/HTTP Team mutation smoke 是历史证据，不冒充新组合验收。2026-09-25 只读检查 3310 无监听进程；本轮不启动用户常驻预览，也没有可见“连接中／整页重试”中转。

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
  Chromium 尚未发送 Chat、验证实时 AG-UI/断线恢复，真实模型 provider 仍未执行。3310 仍仅运行 Web，
  没有常驻 RP/IAM/BFF，不能将隔离测试当作用户当前 HTTP 页面已登录。
- Web `067d7ea` 已修正真实 BFF AG-UI 终帧/工具错误字段的严格解析，并只对 Chat events SSE 采用首部连接 deadline + 可续空闲 deadline；Web 当前 Node22 单仓 `pnpm check` contract56、architecture32、unit1408、lint/typecheck/build PASS，独立只读审查0 P0/P1/P2。Root 已以此精确 SHA 真 Chromium 跑通 IAM登录→DOM首发→真实Agent worker→AG-UI助手DOM→刷新一用户一助手；随后测试自有 TLS proxy 将首次 SSE 截在一个完整帧后，浏览器携该帧 `Last-Event-ID` 重连、恢复助手DOM并保持刷新后一对消息，BFF五帧 cursor 唯一，测试自有资源清零。此证明固定 fixture 的浏览器 Chat/断线恢复，不代表3310常驻IAM/BFF、真实模型 provider、跨用户私有矩阵或全产品完成。
- Web `9e2eb73` 在同一 `/login` 路由不变的前提下，进一步删除九语种 54 条不再使用的连接中、整页重试和旧 handoff 文案；Node22 `pnpm check` contract56、architecture32、unit1408、lint/typecheck/build PASS。Root 固定该 Web gitlink 再跑真 HTTPS Chromium 登录/Chat/一次断线恢复 `status=PASS`，测试自有 PG/Redis/进程剩余 0。当前 3310 的 `/login` 仍是空 body 503，说明旧错误页没有复活，但该 Web-only 进程仍不是完整 IAM 可用入口。
- 本地 PostgreSQL/Redis 复用一套实例与应用凭据，数据 owner 各自使用 schema/连接边界；
  Root 不要求此阶段拆分多个数据库角色，不允许跨 owner SQL。Storage owner schema 已有独立验证，
  但 Storage 用户文件链尚未与 Web/BFF/Agent 闭环。

## 仍未完成

1. R2c 已在固定隔离组合中证明 Chromium/DOM 首消息→BFF→Agent worker→实时 AG-UI 与一次受控断线恢复；仍需
   Web 对 BFF public contract 的全量 generated 消费、单一 AG-UI 网络协议门、默认个人私有/显式分享/跨 tenant
   负例以及真实 provider 验收。固定 fixture 不等于用户当前 3310 已具备完整可见登录入口。
2. Team Product 的 Web→BFF→IAM 同源 HTTP 读链已通过隔离组合；仍需 Chromium DOM、邀请邮件入口与写操作的浏览器端到端验收。
3. Storage/Platform/System/Scheduler 各自 owner 的能力调用、契约与数据闭环；Billing 最后。
4. 当前 inventory 的 11 条 broken edge 与 1 条非法 Web→IAM 旁路，不能因为局部 smoke 通过而标绿。

当前可执行门：`python3 scripts/verify-repository-topology.py`、
`python3 scripts/verify-contract-checkpoint.py --expected verification/contracts/checkpoints/w1b-iam.json`、
`python3 scripts/verify-iam-relay-policy.py`、`python3 scripts/verify-main-only.py` 和
`python3 -m pytest scripts/tests`。旧 `verify-ten-repository-full.sh` 与
`run_stage2_owner_health.py` 的共享状态编排已暂停；它们不是当前全仓验收证据。
