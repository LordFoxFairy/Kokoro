# Wave 1B BFF Admission and Private Resources Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** BFF 只接受 IAM 在线验证的用户身份，并把本仓 Project、ScheduledTask 与 Chat 关联访问收敛为默认个人私有；不把 session admission 当作业务 RBAC 或完整聊天闭环。

**Architecture:** 保留现有 Node HTTP 组合根与 SQL-first 事实，不在身份接入时重写框架。BFF 从 IAM 固定 OpenAPI 生成 Node22 client；服务身份与用户身份分开验证。用户资源由 BFF 自有 owner predicate 保护，Public Share、站点启动清单、Scheduler callback 是三个显式且相互独立的服务边界。

**Tech Stack:** Node22.22.2、pnpm11.25.0、TypeScript5.9.3、@hey-api/openapi-ts0.99.0、Zod4.5.4、当前 pg/redis lockfile；不安装 Node24-only IAM SDK，不升级依赖。

## Global Constraints

- 批准设计：`docs/superpowers/specs/2026-09-20-kokoro-backend-closure-design.md`，尤其 §1.1；Root AGENTS、SQL03、TS08、API05 为权威。
- Browser → Web same-origin adapter → BFF → owner；Web OIDC/CSRF 是下一子仓，不在 BFF 留 header 身份 fallback。
- 默认个人私有；同 tenant 不同用户和跨 tenant 都必须有服务端负例。显式只读分享不授予 Run control、HITL、事件流或未分享文件访问。
- 只用 main；一个子仓一个 writer；Root 独占 Git index/commit/push。owner 发布后才更新 consumer/gitlink。不得覆盖任务外变更。
- 本地共用 PostgreSQL/Redis 实例和 role；测试使用新随机数据库及专属 key/prefix，禁止清理预存数据库或共享 Redis。
- IAM owner 固定 `259a66e6a569889c030734f380e99685d8b9e21c`，OpenAPI0.2.0，`contract/openapi/iam.internal.v1.json`，SHA256 `f7a3ea2e5ae7ade82ae1a6756a2f560d3129ca1b2977c6b0905633a284bd3aab`。
- W0B 当前4 active /12 broken /1 illegal 不因生成client自动变绿；W1B必须明确真实owner与fixture证据。Billing最后、Platform原子改名不提前。
- 用户最新裁决（2026-09-22）：当前以开发为目的，优先功能代码、针对性测试和最小真实联调；运维加固、部署、镜像、SLO与重复全仓审计后置，不作为本片功能开发的额外前置。保留身份/资源权限、数据一致性及自有测试资源隔离，不扩大为基础设施治理项目。

## 基线、放置与文档门

Root基线 `c89816378bd6f5275980527eea863da52ad84d80`；BFF `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff`，main `c5e9b3cc8eb134ff72e37f56ac1f95ebec4f42e7`、clean。Root已执行 `PATH=/Users/nako/.nvm/versions/node/v22.22.2/bin:$PATH corepack pnpm test`：199 passed、0 failed、0 skipped（5.43s）。此基线不是改后验收。

| 项 | 裁决 |
| --- | --- |
| Owner | IAM拥有身份/session/member事实；BFF拥有入口准入、Project/ScheduledTask/Chat资源检查。BFF唯一writer由Root逐阶段续派。 |
| 当前事实 | `src/http/request.ts::authorize`只读secret+自报namespace/principal；`bootstrap/server.ts`有manifest虚拟用户fallback；Project无owner列且缓存仅tenant；ScheduledTask已有owner列但public查询/写入尚未全用它。Chat已有多处owner predicate，不重写其durable ledger。 |
| 目标职责 | `src/auth/`只负责在线准入client、传输预算和HTTP身份建立，无DB/业务权限/通用IAM SDK；私有资源规则修改现有所属service/repository。 |
| 目录方案 | 比较①新增`infrastructure/clients/iam`再分散到application/http；②`src/auth/`共置新准入能力。采用②，避免继续扩张历史机械四层；既有业务目录暂不批量迁移。generated保留`src/generated/iam-http`，与已有生成物同一治理方式。 |
| 粒度 | client、transport、types、HTTP admission有独立变化原因；不另造Auth数据库、Repository port、Command bus或模块容器。manifest抽到现有http/routes下一份文件，避免伪造用户或新增泛用服务代理。 |
| 依赖 | auth仅依赖config、IAM generated及domain RequestContext；bootstrap接线，业务service不依赖HTTP/JWT。token只发IAM，不保存或传入其他owner。 |
| 数据/API | Task1无schema变化；Task2新Project owner及查询索引/slug scope，SQL-first fresh install，不做迁移/旧数据回填。public auth声明修正，固定63个path/method/operationId，不重置baseline掩盖变化。 |
| 删除项 | 删除header身份authorize与manifest假user fallback；Task2删除tenant-only用户查询和Project列表缓存，不保留旧缓存读取/双scope/兼容API。 |
| 验证 | BFF format/lint/typecheck/contract/architecture/schema/test/build；真实PG/Redis integration与fresh install；Root重跑、独立审查、组合smoke后才提升gitlink。 |

子仓实现前，由指定owner只改以下三份设计文件，Root复核后再续派runtime：

- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/docs/TECHNICAL_DESIGN.md`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/docs/API_CONTRACT.md`
- `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/docs/DATA_MODEL.md`

三文档明确当前态/本片目标，删除“由Web还是BFF执行IAM尚未决定”等过期决策；BFF依旧Node HTTP/SQL-first，不宣称已迁入Nest。Owner报告列出基线SHA、三文档绝对路径、未决项及`contract:check`/`schema:check`实际输出。本阶段禁止runtime/contract/schema写入；设计通过后按下面切片串行授权。

## 固定边界与失败语义

1. 普通用户 `/v1/*`：先校验`web-bff`服务secret，再读取唯一Bearer凭据，调用IAM admission。缺失/错误service为403 `service_auth_failed`；缺失/格式错误Bearer为401 `session_authentication_required`。旧namespace/principal、body tenant/user、Host和forwarded身份均不参与用户身份建立，也不转发IAM。
2. IAM调用严格为`POST /internal/v1/session-authorizations/verify`、无body/query，只有Bearer、JSON Accept及受控`x-request-id`。redirect禁用、零自动重试、无allow缓存；整个header/body读取受timeout与byte cap约束，并响应客户端断开。最大预算使用现有upstream配置与5s/1MiB硬上限的较小值，不通过测试开关绕过生产预算。
3. 只接受strict generated response，`allowed`必须为true且tenant/user/session/client均非空；错误也按owner schema解析，检查响应no-store与合法request-id。200才建立`RequestContext.identity={namespace:tenant_id,userId:user_id}`。不自行解码JWT取得authority，不复制IAM当前事实。
4. IAM401→401 `session_invalid`；403/404/409→403 `session_forbidden`；429→429 `session_rate_limited`（合法Retry-After秒数1..86400才转发）；transport/timeout/其他status/错误shape或header→503 `iam_admission_unavailable`。响应保持BFF当前canonical ErrorEnvelope和no-store，消息不复制IAM原文。所有拒绝发生在body业务解析、receipt、SQL、outbox、SSE与owner socket之前。
5. `GET /healthz`与`GET /readyz`保持probe。`GET /v1/shared/{shareId}`仅服务secret+有效share capability，不能走用户路由。`GET /v1/system/runtime-manifest`显式仅服务secret+服务器配置tenant/domain，不再制造`runtime-manifest` userId；只发tenant及service身份给System，保持原projection校验。两者OpenAPI覆盖顶层用户Bearer security，不是IAM故障时降级路径。
6. `/internal/bff/scheduled-tasks/dispatch`保持独立Scheduler token、事件identity与持久receipt/CAS；不得因为新IAM准入接受Web用户token，亦不得把浏览器用户带入该回调例外。
7. 单次用户请求/SSE建连及重连都重新admit；既有已建立SSE受现有有界connection duration控制，本片不声称实现跨连接即时撤销。IAM缺配置时用户入口503且production readiness不宣称就绪；probe/share/site-bootstrap的独立边界不被伪装成用户登录。
8. `x-kokoro-permission`保持产品operation的动作标识；本片不凭session admission结果合成63种IAM权限。BFF私有事实由owner predicate授权，其他owner继续执行自身契约检查，尚未接线的surface保持原fail-closed。

### Task 1: 接入 generated IAM admission 并删除自报身份入口

**Files — BFF仓内精确范围：**
- Create: `src/auth/session-admission.client.ts`、`src/auth/session-admission.transport.ts`、`src/auth/session-admission.types.ts`、`src/auth/user-admission.ts`、`src/http/routes/runtime-manifest.ts`。
- Create: `openapi-ts.iam.config.ts`、`scripts/generate-iam-http-client.mjs`、`contract/dependencies/iam-http.json`、`contract/vendor/kokoro-iam/259a66e6a569889c030734f380e99685d8b9e21c/iam.internal.v1.json`。
- Generate only: `src/generated/iam-http/`（生成器产物清单与每文件digest写入manifest；严格allowlist与两次生成drift检查，禁止手改）。
- Modify: `src/bootstrap/runtime.ts`、`src/bootstrap/server.ts`、`src/config/runtime.ts`、`src/http/request.ts`、`src/http/routes/owner.ts`、`src/http/response.ts`（只为受控Retry-After header）。
- Modify: `package.json`、`.env.local.example`、`contract/openapi/v1/openapi.yaml`、`contract/README.md`、`AGENTS.md`、`README.md`、`INDEX.md`、`docs/INDEX.md`、`docs/CURRENT.md`、上述三文档、`docs/SECURITY.md`、`docs/ACCEPTANCE.md`、`docs/RUNBOOK.md`。
- Create tests: `test/iam-admission-client.test.ts`、`test/user-admission.test.ts`、`test/doubles/session-admission.ts`。
- Update existing fixtures/assertions only: `test/doubles/server.ts`、`test/bff.test.ts`、`test/config.test.ts`、`test/lifecycle.test.ts`、`test/source-start.test.mjs`、`test/contract-governance.test.mjs`、`test/contract/openapi-contract.test.mjs`、`test/architecture.test.ts`、`test/mori.test.ts`、`test/music.test.ts`、`test/scheduler.test.ts`、`test/agent-control-adapter.test.ts`、`test/business-store.integration.mjs`、`test/chat-facts.integration.mjs`、`test/agui-http.integration.mjs`、`test/scheduler-dispatch-receipt.integration.mjs`。
- Exclude: `database/schema.sql`、lockfile、其它generated、IAM/Web/Root代码。需要越界先向Root报告文件和理由。

**Interfaces:**
```ts
// src/auth/session-admission.types.ts；不携带Bearer到业务context
export type SessionAdmissionInput = Readonly<{ token: string; requestId: string; signal: AbortSignal }>
export type SessionAdmissionResult =
  | { ok: true; identity: { namespace: string; userId: string } }
  | { ok: false; status: 401 | 403 | 429 | 503; code: string; retryAfter?: string }
export type SessionAdmission = { verify(input: SessionAdmissionInput): Promise<SessionAdmissionResult> }
```
`SessionAdmissionClient`实现该窄接口；composition显式test seam `sessionAdmission?: SessionAdmission`，生产默认真实client。`config.iamBaseUrl: string | null`从`KOKORO_IAM_BASE_URL`解析，只接收无userinfo/query/hash的HTTP(S) origin；未配置不允许业务。HTTP建立context由`authorizeUserRequest`统一负责，service检查在调用client之前。测试double只从固定token→身份映射取值，不读取legacy identity header，不提供环境变量测试 bypass。

- [ ] **Step 1: 文档门与机器契约先行。** 三文档通过后复制固定commit blob为vendor并校验digest；配置生成入口只暴露`verifySessionAuthorization`操作及其引用schema，不复制另一套手写wire DTO。scope过滤必须可重复由完整vendor派生；Node22生成兼容修正只允许写在生成脚本中，严格匹配次数并纳入负例。保留已接受Capability/Scheduler artifact字节与版本。
- [ ] **Step 2: 写失败用例并实跑red。** client用loopback HTTP owner fixture验证：POST/no-body/唯一Bearer、strict success、false/空字段/extra字段、错误status/envelope/no-store/request-id、redirect、超过cap、慢header/慢body、取消、零重试。server用显式admission spy验证service/Bearer拒绝不触发业务、IAM identity覆盖恶意header、撤销后同key不replay、断开取消，以及三类服务例外互不授权。
```ts
assert.equal(captured.method, "POST")
assert.equal(captured.url, "/internal/v1/session-authorizations/verify")
assert.equal(captured.body.length, 0)
assert.equal(captured.headers["x-kokoro-namespace"], undefined)
assert.equal(captured.headers["x-kokoro-principal-id"], undefined)
assert.equal(result.ok, true)
if (result.ok) assert.deepEqual(result.identity, { namespace: "tenant-a", userId: "user-a" })
assert.equal(ownerCallsAfterDeniedAdmission, 0)
assert.equal(receiptCallsAfterDeniedAdmission, 0)
```
Run: `corepack pnpm build && node --test test/iam-admission-client.test.ts test/user-admission.test.ts`；新实现前必须至少有一项行为失败，不以语法/import错误作唯一red证据。
- [ ] **Step 3: 实现单一准入链。** 删除`authorize`旧身份构造；先service→Bearer→在线verify→context，后才mutation/body/routes。request.aborted和response提前close取消本次IAM IO，正常request body end不得误取消；清理listener/timer/reader，失败不泄漏Bearer。manifest走显式服务handler，删除owner.ts重复分支与fake principal，不泛化代理。
- [ ] **Step 4: 同步public contract和测试接线。** 顶层security为serviceHeader+internalSecret+userBearer，删除namespace/principalId security schemes；share/manifest显式service-only override；所有受保护operation发布401/403/429/503，path/method/operationId不变。记录未上线clean-slate auth修正，不声称backward compatible。旧fixtures改为token映射，测试仍验证原业务断言；默认composition必须真实client，不允许旧tests通过隐式allow。
- [ ] **Step 5: Owner全门和停写交付。** `format:check`纳入新手写/生成文件；`contract:check`纳入IAM drift，provenance固定Node/pnpm/generator/lockfile。执行format/lint/typecheck/contract/architecture/schema/test/build与真实integration。先自有空库apply，再集成；回报计数、资源清理及剩余私有资源问题。Root独立SPEC/QUALITY审查与重跑后精确提交`feat(bff): admit users through pinned IAM session contract`，不提前提升Root gitlink或声明私有资源完成。

### Task 2: 关闭同 tenant 私有 Project / ScheduledTask 与关联访问缺口

**Files（在Task1冻结提交上续派同一BFF owner）：**
- Modify: `database/schema.sql`、`src/application/project-service.ts`、`src/application/scheduled-task-service.ts`、`src/application/ports/project-repository.ts`、`src/application/ports/scheduled-task-repository.ts`、`src/infrastructure/postgres/project-repository.ts`、`src/infrastructure/postgres/scheduled-task-repository.ts`、`src/infrastructure/postgres/client.ts`、`src/infrastructure/postgres/chat-repository.ts`、`src/infrastructure/postgres/agent-dispatch-outbox-repository.ts`、`src/application/chat/message-create-input.ts`、`src/http/routes/live-bff.ts`、`src/http/routes/chat.ts`、`src/http/routes/agent.ts`、`src/http/routes/scheduler.ts`、`src/bootstrap/server.ts`。
- Create: `src/http/routes/chat-authorization.ts`，Chat HTTP范围校验与现有ChatService授权调用；比较放auth/与现有routes/，采用后者，业务资源规则不进入IAM准入目录。返回结构化判定供server在通用mutation receipt之前执行，不包含SQL、Agent调用或新ACL。
- Test: `test/business-store.integration.mjs`、`test/scheduled-outbox.integration.mjs`、`test/chat-facts.integration.mjs`、`test/agui-http.integration.mjs`、`test/agent-control-adapter.test.ts`、`test/chat-input.test.ts`、`test/schema-governance.test.mjs`、`test/architecture.test.ts`、`test/scheduler.test.ts`及必要的既有`test/doubles/`对应fixture（实施前列出具体文件）。
- Docs: 三文档、`docs/SECURITY.md`、`docs/CURRENT.md`、`docs/ACCEPTANCE.md`、`docs/RUNBOOK.md`、`contract/openapi/v1/openapi.yaml`（仅说明私有语义与scope约束）。
- Exclude: IAM/Web/Root、lockfile、已生成IAM/Capability/Scheduler artifacts。需要越界先报告，不自行扩展。

**Interfaces / 固定行为：** 用户范围使用具名`{ tenantId, subjectId }`入参，不再添加易混淆同类型位置参数。Project新增不可由body指定的`owner_id TEXT NOT NULL`，创建取可信subject；所有列表/详情/slug/修改/skills/revisions/tasks均tenant+owner。slug唯一域改为tenant+owner+slug，不泄漏同tenant他人的slug；按真实列表排序加tenant+owner索引。Project子事实通过本仓父Project predicate/锁保护，不复制owner列。删除非必要的Project Redis列表cache及invalidate分支，避免新身份下读旧tenant缓存；Redis其它职责不动。

ScheduledTask用户list/detail/update/delete/retry均tenant+owner；create所引用Project必须属于同一tenant/subject，在写task+outbox的同一事务验证并锁定。服务回调的`findRecord`以明确内部语义保留tenant/task→stored owner读取，不能被用户route调用；body不能指定执行owner。Chat/Message关联Project的创建与后续project_ref访问不能借他人Project绕过私有边界；现有Conversation owner/Share锁与AG-UI predicate继续生效。Project没有显式授权API/表，当前只允许owner；不伪造团队共享或新建泛用ACL，现有显式只读Conversation Share保持可用。

补充P0（只读审查、Root核对源码）：`scheduledTaskId`稳定材料必须包含tenant+可信subject+path+key；create replay和outbox lookup不能跨owner命中。Run control目前直接落到Agent adapter而未检查Conversation；必须在业务receipt replay与Agent IO之前检查tenant+subject+Conversation，并覆盖cancel/resume/steer，不能只依赖Agent替BFF授权。Chat query `scope`只允许省略/空/direct（与现有mock定义一致），其它值400，不作为tenant来源；body/query同时提供不同project_ref返回400。非空Conversation.project_ref必须匹配同tenant/owner的Project；隐私读取、message事务与control均fail-closed，不把外部字符串当共享授权。

所有按既有资源寻址的用户mutation都先做资源gate再进入通用receipt：`chat-authorization.ts`负责Conversation；既有`live-bff.ts`提供Project/ScheduledTask的窄HTTP授权入口，server在receipt之前调用。mutation repository仍在事务/写入predicate中重验，避免预检后TOCTOU；不能只靠HTTP预检，也不能通过旧receipt跳过已删除/不可见资源。新建Project无既有资源预检；新建ScheduledTask的非空Project引用先检查且在写事务锁内再次验证。该接线使用Task2既有文件范围，不新增授权框架。

契约细节：现有`ScopeQuery`同时被私有Chat与Public Share引用；拆出私有Chat的direct/空过滤参数，保留Share的tenant窄化过滤语义，不能全局收窄同一component误伤分享。ScheduledTask稳定ID使用无歧义的序列化材料（例如JSON数组），避免将opaque tenant/subject/key用可出现在值中的分隔符拼接。

- [ ] **Step 1: 真实PG red矩阵。** 同tenant A/B及跨tenant C：A创建私有Project/ScheduledTask/Conversation；B/C的list不出现、detail/mutation/control/events均与缺失相同；B可创建同名slug的自己的Project。记录调用前后事实/outbox/receipt数量，拒绝不产生业务副作用。
```js
assert.equal(otherUserDetail.status, 404)
assert.equal(otherUserScheduledPatch.status, 404)
assert.deepEqual(otherUserProjectList.data.projects, [])
assert.equal(ownerProjectAfterDeniedWrite.instruction, ownerProjectBeforeDeniedWrite.instruction)
assert.equal(outboxCountAfterDeniedWrite, outboxCountBeforeDeniedWrite)
```
- [ ] **Step 2: Schema与数据访问切片。** fresh schema增加Project owner和对应唯一/查询索引；将用户scope沿route/service/repository完整传递；关系写入锁内检查，无跨owner SQL。安装非空DB必须拒绝，不自动迁移或为旧seed提供默认owner。更新fixture显式owner，不降低负例。
- [ ] **Step 3: 分享与内部执行回归。** 显式Share只读可访问且revoke/expire/tombstone后拒绝；持有share不可control/HITL/events。Scheduler专用callback仍从受信事件与已存task owner产生内部调用，跨身份/重复/重启receipt测试保留。已知未完成Storage/files继续503而非假200。
- [ ] **Step 4: 完整门、独立审查与Root复验。** 同Task1全门，补索引/列catalog断言和fresh install。Root在最终冻结diff上验证，再精确提交`fix(bff): enforce personal ownership for product resources`。记录真实通过数，不用fixture称完整IAM/Agent/Storage组合。

### Task 3: Root 组合验收与发布交接

**Owner:** Root主控；BFF writer停写后进入。Root后续精确任务卡列出smoke变更与证据tuple，不授权子仓writer修改Root。

- [ ] 回收两个切片SPEC/QUALITY结论，Root在冻结BFF SHA重跑完整owner门。核对IAMvendor源commit/digest、SQL owner/无FK、用户/服务例外、旧身份入口全部删除。
- [ ] 更新现有Capability↔BFF与Scheduler↔BFF隔离smoke的认证fixture，使其使用明确token→admission fixture映射；System smoke同步。fixture必须标注非真实IAM，不能因此激活BFF→IAM edge。保持原8/11case及资源生命周期负例，不用删case通过。
- [ ] 按已经发布的IAM/BFF原生接口建立独立真实IAM↔BFF验收任务：当前有效会话、撤销/成员删除、同tenant身份冒用、IAM失联fail-closed、无敏感token日志；Root发布前要有真实证据，否则BFF→IAM继续broken并明确剩余项。该harness须先独立放置/隔离设计，不从Root直接读写业务数据库。
- [ ] 开发联调优先复用IAM已有loopback Nest HTTP fixture及真实PG/Redis业务，明确标注真实HTTP integration，不冒称`src/main.ts`双进程或部署验收。IAM源码入口监听配置、发布进程硬化留到部署阶段，不因该运维项打断BFF→Web功能推进；也不为此扩大监听范围或放宽测试资源隔离。
- [ ] 子仓push后再提升Root gitlink与全部BFF fan-out evidence；按实测证据决定edge状态，生成器/Node/provenance与consumer digest一致。在组合发布时集中执行一次Root topology、exact checkpoint及相关Root回归，不在每个功能小片重复全仓审计；全仓standard/远端分支/部署门后置统一收尾，既有失败如实保留。
- [ ] 更新同一task/progress/CURRENT，不复制任务中心；W1后续Web OIDC/CSRF与execution authorization仍由既定owner接续，完整Goal继续active。计划scratch仅在本计划全部验收且证据固化后删除。

## 本片不宣称的能力

Web仍未切换OIDC/same-origin登录；已有SSE未实现即时跨连接撤销；IAM session admission不是63个业务权限判定；Project ACL/Storage文件分享尚未有运行契约；真实Agent聊天、附件、编辑/重生成、Provider及全仓镜像/SLO仍按W2–W7闭环。每个缺口继续绑定owner，不以文档、生成物或历史PASS替代运行结果。
