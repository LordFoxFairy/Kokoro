# Wave 1A — IAM User Session Admission Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. 执行按 owner 串行，Root 保留 Git index、commit、push 和最终验证。

**Goal:** 发布可由 BFF 消费、只接受可信用户令牌且在线重验当前身份事实的 IAM session admission contract；不把本片当作完整业务授权或聊天闭环。

**Architecture:** 沿用批准设计 Wave1 与用户确认的默认个人私有规则。IAM 已有 JWT verifier/introspection/Prisma/组织成员事实；在现有 Authorization 模块增加具名只读 operation，不新造 token、不共享表、不恢复旧 Web magic-link contract。BFF 后续从 owner 固定 OpenAPI 生成 Node22 client；本片 IAM SDK 保持 Node24。

**Tech Stack:** Node24.20.0 / pnpm12.3.4 / Nest12.0.1 / Better Auth1.7.3 / Prisma7.10.0 / TypeScript6.0.3 / Vitest4.1.11 / hey-api0.99.0；沿用 manifest/lockfile，不升级。

## Global Constraints

- 权威：Root AGENTS、SQL/TypeScript/API手册、批准整体设计；唯一状态表 docs/task.md，唯一证据账 docs/progress.md。
- IAM `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-iam`，main 基线 `35d868a410c06731362bd1e8bcc3e602d01875f8`，clean；Root 基线 `136e12d7f751b7b77c5a16f8a36fa1df32f97b50`。
- 用户要求只保留 main，沿用当前已授权 main 集成，不创建分支/worktree；子 Agent 不操作 Git index/commit/push。
- 独占 writer `w1_iam_owner_auditor`（gpt-5.6-sol/high，盘点后续任）；Root 独立审查、复验、精确提交。共享基础设施不 reset/flush/restart。
- PostgreSQL127.0.0.1:5432 / Redis127.0.0.1:6379，复用现有单实例；只创建并回收本次确实拥有的随机数据库和精确 Redis prefix，连接 public/UTC。
- 不改 Prisma schema、lockfile、Billing、execution proof、BFF/Web 源码，不激活任何 Root edge。
- 同 tenant 不等于已授权读取私有聊天；本 endpoint 只证明用户/会话/成员当前有效，资源 permission/visibility 仍是后续必做门。
- 根因已确认：Web 仍是旧 magic-link HTTP +密封cookie而非文档中的Auth.js/OIDC；不为保留旧路径而扩大 IAM兼容面。

## 放置与数据设计门

| 项目 | 结论 |
| --- | --- |
| Owner / writer | IAM Authorization 唯一 session admission writer；Auth 保留 OAuth/JWT/issuer事实 |
| 当前事实 | verifier + introspection + InternalAuthGuard 已存在；authorization/check仅tenant/read、audit/read且允许machine；当前User无disabled字段；682标准测试通过 |
| 目标职责/API | POST /internal/v1/session-authorizations/verify，仅用户当前身份/成员准入；不判业务资源permission |
| 目录比较 | 采用现有 authorization 下 session-authorizations：与Billing/Execution各自授权决定并列；不放auth/ingress（不是发行协议）、不另建顶级模块 |
| 粒度 | schema/controller/service/current-facts repository四个明确职责；非机械七件套，不新建连接池或空目录 |
| 依赖 | controller→service→当前IAM事实查询；复用Auth verifier/introspection与PrismaService；禁止跨owner数据、Billing repository复用或Web DTO复制 |
| 数据/API | canonical schema不变；代码优先生成OpenAPI，生成SDK只读；snapshot非永久授权，无租户自报、无准入缓存 |
| 删除项 | 不新增旧token/旧Web endpoint alias；没有被替代的已发布业务路径；旧authorization/check继续承接原tenant/audit职责，非同operation双轨 |
| 验证 | unit/contract/generated drift/architecture/build + 真实PG/RedisHTTP撤销矩阵，Root复跑；无真实服务证明不激活edge |

## 固定协议与行为

```http
POST /internal/v1/session-authorizations/verify
Authorization: Bearer <IAM user_delegated access token>
x-request-id: correlation_id
# 无 body，也无业务 query
```

```json
{"data":{"allowed":true,"tenant_id":"tenant-a","user_id":"user-a","session_id":"session-a","client_id":"web-client"}}
```

- operationId `verifySessionAuthorization`；strict response，无requestBody，不接身份字段、permission、operation或request binding。
- user_id来自已验sub；tenant_id来自已验namespaced tenant claim；session_id来自sid；client_id来自client_id。首版actor=subject=user_id，不复制可漂移的actor字段。
- 专用 `SESSION_AUTHORIZATION_SCOPE = "iam:session-authorization.verify"`，只加入 user_delegated allowlist；不放入共用TENANT_SCOPES，不授予machine/operator/resource_server。
- 同步固定 Better Auth允许scope、internal OAuthResource.allowedScopes、user client注册校验；只有真实 Code+PKCE签发/refresh通过才算可消费。既有部署资源需显式operator provisioning，不自动修改已有数据库。
- metadata：owner kokoro-iam / internal-owner / stable / permission iam:session-authorization.verify / idempotency none；响应no-store、x-request-id，错误沿用IAM稳定ApiError envelope。
- 任何body包括 `{}`、Transfer-Encoding、非零Content-Length，以及非空query：400 INVALID_ARGUMENT；不通过空schema strip掉自报身份。
- 401：无效/过期JWT、inactive introspection、缺失/过期/不属于sub的session、缺失user或disabled/missing client；403：非user profile、缺scope、membership缺失、client不再具备该profile/scope/resource；404：可信tenant不存在；409：tenant disabled；429限流；413大小；503依赖故障；500真正内部错误。
- 已安装BA introspection查询当前client和session，但只按sid查session，未证明user存在/session.userId绑定；现有hasMembership只查member行。无FK下必须补本模块current-facts查询，覆盖孤儿记录，不能用cascade happy path冒充完整性。
- 数据查询通过唯一Prisma连接，短有界只读transaction形成当前Tenant/User/Session/Member/Client/resource binding snapshot，外部网络在事务外。原guard/introspection有效保障保留，最终查询不降级为允许；失败归一503。
- token生效/过期由现有已验证schema/guard校验；允许结果是当前请求的瞬时检查，不是可缓存lease或新授权凭证。不得声称跨服务副作用与logout零窗口原子性。
- 无 User.disabled/banned 字段，不捏造此能力；真实 user deletion/orphan 必须拒绝。JWT逐token撤销不是已有能力；session/client/member撤销边界如实记录。
- 不自动重试本片SDK operation，单次检查失败即交给调用方，避免瞬时准入结果被隐式重试/缓存扩大；deadline/cancel/body cap复用现有SDK。

## Task 1 — Owner 文档门与完整实现（W1A-1）

### 精确允许文件集

IAM目录内新增：

```text
src/modules/authorization/session-authorizations/session-authorization.schema.ts
src/modules/authorization/session-authorizations/session-authorization.controller.ts
src/modules/authorization/session-authorizations/session-authorization.service.ts
src/modules/authorization/session-authorizations/session-authorization.repository.ts
test/unit/session-authorization.service.test.ts
test/contract/session-authorization.openapi.test.ts
test/integration/session-authorization-http.test.ts
```

IAM目录内修改：

```text
src/http/application.setup.ts
src/http/internal-api.openapi.ts
src/modules/auth/oauth/oauth.constants.ts
src/modules/auth/better-auth/better-auth.config.ts
src/modules/auth/oauth/clients/oauth-client.schema.ts
src/modules/auth/oauth/clients/oauth-client.service.ts
src/modules/auth/internal-access/internal-principal.types.ts
src/modules/auth/internal-access/internal-auth.guard.ts
src/modules/authorization/authorization.module.ts
scripts/generate-contracts.ts
contract/openapi/iam.internal.v1.json
contract/vendor/better-auth.v1.7.3.json
sdk/src/api/types.gen.ts
sdk/src/api/sdk.gen.ts
sdk/src/api/zod.gen.ts
sdk/src/iam-client.ts
sdk/src/iam-client.types.ts
sdk/src/index.ts
sdk/package.json
sdk/README.md
test/unit/sdk/iam-client.test.ts
test/consumer/iam-client.consumer.test.ts
test/fixtures/sdk-consumer/src/real-consumer.ts
test/unit/internal-auth.guard.test.ts
test/unit/oauth-client.service.test.ts
test/unit/token-claims.test.ts
test/contract/auth-kernel.test.ts
test/contract/internal-openapi.test.ts
test/smoke/internal-api.test.ts
test/fixtures/internal-http-application.ts
docs/TECHNICAL_DESIGN.md
docs/API_CONTRACT.md
docs/DATA_MODEL.md
docs/CURRENT.md
docs/integration/bff-iam.md
INDEX.md
contract/README.md
```

vendor snapshot仅接受现有生成器因真实scope公开面产生的确定性diff，禁止手改；其他生成文件如出现真实diff先报告Root调整范围。
SDK package仅版本0.2.0，engines保留>=24<25；internal OpenAPI升0.2.0，既有breaking baseline不重置。

**接口：** 消费已有InternalAuthGuard/PrismaService及IAM事实；产出上述唯一operation + `IamClient.verifySessionAuthorization(options?: IamCallOptions)`，无request参数，返回`IamResponse<SessionAuthorizationResponse>`。固定生成函数/response schema由operationId推导；业务层不手写一份wire DTO。

- [x] 先把TECHNICAL_DESIGN/API_CONTRACT/DATA_MODEL写为一致目标，明确当前不存在endpoint；运行既有contract/schema静态门，向Root发送绝对路径、基线、未决项和命令结果后等待文档门放行。文档门期间不写runtime。
- [x] TDD：先写新operation/guard/service/SDK/真实HTTP负例，确认旧基线404/缺少新方法使所需断言失败；非import缺失之外至少一次真正HTTP行为RED。
- [x] 最小实现：user-only Guard passage、无body/query拒绝；本模块service/current-facts repository；不新增API身份输入、不复用permission checker充当admission。
- [x] 单元与真实HTTP固定以下断言形式，fixture沿用本仓真实issuer发行token，不mock签名/DB成功：

```ts
const response = await fetch(`${fixture.baseUrl}/internal/v1/session-authorizations/verify`, {
  method: "POST", headers: { authorization: `Bearer ${userToken}` },
});
expect(response.status).toBe(200);
expect(await response.json()).toEqual({ data: {
  allowed: true, tenant_id: tenantId, user_id: userId,
  session_id: sessionId, client_id: clientId,
}});
// 同一个已签发token，在owner事实撤销后下一次请求必须拒绝。
await fixture.db.database.query('DELETE FROM iam_tenant_member WHERE organization_id = $1 AND user_id = $2', [tenantId, userId]);
expect((await verify(userToken)).status).toBe(403);
```

  还需覆盖：机器/operator、缺scope、body/query注入、伪造header不改变identity、invalidJWT/issuer/aud/expired、session删除/过期/错误user绑定、client删除/禁用/profile/scope/resource变化、user直接SQL删除遗留session/member、tenant不存在/disabled、membership移除、依赖503且不回退允许、refresh与会话撤销、no-store/request-id；数据库操作仅fixture拥有的库。
- [x] 正常generator更新OpenAPI/SDK，新增SDK方法设置retry=false；source/schema/contract/type与测试一致。
- [x] GREEN：从IAM目录，Node24.20.0 PATH，运行下一节完整命令并记录实际数量。标准测试基线682，不允许静默减少覆盖或skip绿色。
- [x] 停写交付文件清单、diff、RED/GREEN证据、资源回收与未完成项；由Root串行review/Git，不自行提交。

## Task 2 — Root 独立审查、验证与集成（W1A-2）

**Root精确文件：** gitlink apps/kokoro-iam、verification/contracts/consumer-inventory.json、相关固定pin回归 scripts/tests/test_contract_compatibility.py、本计划、docs/task.md、docs/progress.md、docs/CURRENT.md、docs/INDEX.md。其它Root脚本或edge checkpoint不改。

- [x] 审查绑定冻结IAM工作树hash与base；独立SPEC/QUALITY覆盖scope签发、身份绑定、撤销、无FK孤儿、异常与SDK生成/Node边界。需要修复时只回派IAM负责人。
- [x] Root在冻结代码重跑IAM同一完整门，确认资源清理；精确提交IAM业务+测试+文档自洽slice，push并验证live main。
- [x] Root提升IAM gitlink，将所有受影响IAM owner/evidence tuple刷新到新commit-blob/digest/version；不伪造任何未变artifact来源，不激活edge。BFF/Web仍未接线。
- [x] Root运行topology、w0b-exit精确4 active/12 broken/1 illegal、完整scripts/tests；static standard实际失败继续列明，不放宽规则。
- [x] 精确提交Root并push；main-only/clean/live-main审计；W1A完成但W1与整体Goal不完成。后续 W1B BFF admission/generated consumer、W1C Web issuer/same-origin/CSRF、W1D已批准execution authorization；每片独立设计门。

## 验证命令与资源

```bash
# cwd: /Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-iam
export PATH=/Users/nako/.nvm/versions/node/v24.20.0/bin:$PATH
corepack pnpm format:check
corepack pnpm lint
corepack pnpm typecheck
corepack pnpm contract:check
corepack pnpm contract:breaking
corepack pnpm sdk:check
corepack pnpm prisma:validate
corepack pnpm test
corepack pnpm build
IAM_TEST_ADMIN_URL=postgresql://nako@127.0.0.1:5432/postgres IAM_TEST_REDIS_URL=redis://127.0.0.1:6379 corepack pnpm test:integration
IAM_TEST_ADMIN_URL=postgresql://nako@127.0.0.1:5432/postgres IAM_TEST_REDIS_URL=redis://127.0.0.1:6379 corepack pnpm test:consumer
```

子进程需要pnpm executable时使用本任务owned临时shim调用corepack，不改全局安装。fixture必须是新随机数据库、public/UTC；fresh schema install由各isolated fixture执行并补空库canonical schema证据，保留旧schema hash相等断言。`test:consumer`包括外部临时安装，可联网；不升级依赖/lockfile。

## 主控自审

- 本片是W1必要身份前置，不宣称63 operation授权、真实聊天或Platform execution完成。
- 不阻断已完成W0B，也不重复其双smoke；Root只刷新本次IAM组合输入。
- 现有Web无Auth.js事实与IAM文档目标态明确区分；后续只能按当前issuer contract收敛，不恢复旧API。
- 无外键关系由查询与负例补偿，数据角色共用不改变owner隔离；不创建新schema或自研身份协议。

## 审查修复 Round 1

Root 接收独立审查的 no-store 缺口：Controller header 晚于 Guard/64KiB parser，错误响应缺少 no-store。允许仅扩展既有 HTTP 装配和错误 OpenAPI decorator 两文件，配置在 parser/guard 前生效的 session endpoint cache policy；保持其他 operation 行为不变。新增代表性 400/401/403/413/429/503 header 回归与所有错误响应机器契约断言；禁止手改生成文件。consumer 必须先有 Root 精确候选提交，再实跑 clean provenance 门，发布仍在所有门通过之后。

Round2：Root真实probe要求缓存策略与Express实际接受的case/trailing-slash路由语义相同；复用框架matcher，不维护第二份字符串路径判定。错误header覆盖canonical与相同operation的路径变体，不调整其他路由策略。

## 执行结果

Task1/2完成。IAM代码54d0d5f、最终docs release259a66e，Root集成a7585a97均已推送。Root复验701标准/174真实integration/2仓外consumer/495治理测试；12仓main-only/clean/live-SHA审计通过，SPEC/QUALITY均0/0/0。112静态违规与1未验证项、12broken与1illegal保留；后续BFF→Web及整体Goal仍未完成。详见docs/task.md、docs/progress.md与IAM CURRENT，不从本计划scratch重派完成任务。
