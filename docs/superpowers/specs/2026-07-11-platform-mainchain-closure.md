# Platform × 主链完整闭环技术方案（v1 定案稿）

状态：定案执行稿（用户已授权自主推进；发现与 handbook 冲突时停下列冲突）
日期：2026-07-11
上级：`docs/kokoro-handbook/technical/20-kokoro-v1-technical-plan.md`、`18-capability-namespace-auth-sandbox-artifacts.md`
事实底图：platform 域内环（user/site/model/credit/payment/platform-kit/admin 双后台）已自洽可跑有测试；主链（web/session/agent）对 platform 真实源码零调用。

## 0. 一句话

> platform 内环已成形，闭环缺的是**外环三条线**：①终端身份签发链（web 登录 → user 认证 → opaque-namespace JWT → session 验签）；②运行时模型与计费链（model resolve → litellm 网关 → credit hold/capture）；③一键编排与跨栈 e2e。本方案只接线，不重造任何一环。

## 1. 铁边界（继承，不重议）

- GA/agent 只消费**不透明 namespace**（`RunRequest.context.namespace`），身份语义在上游解析。session 已禁 `user:/team:/site:` 等前缀——保持。
- session 消费端契约不动：HS256 Bearer JWT，`namespace = payload.sub`。闭环=给它接上真签发方，不是改它。
- 模型/provider/凭据/注册归 kokoro-model + kokoro-litellm；agent 不存 provider 凭据（litellm 网关档只持网关地址与网关 key）。
- 扩张=加配置不是加代码：新 provider/新价格/新站点都必须只是 platform 数据/配置变更。

## 2. 目标链路（两条主线）

### 2.1 身份签发链（断点最硬，先做）

```text
浏览器 → kokoro-web(登录 UX,next-auth 认证得 externalUserId)
      → kokoro-user POST /auth/sessions（新增,服务间调用,platform-kit callService 口径）
         入参: {site_id, external_user_id, email?}   出参: {token, namespace, user, team}
         行为: resolve-or-create user + personal team → 签发 HS256 JWT
               sub = teamId(ULID,天然不透明,个人=personal team) / exp / iss=kokoro-user / site_id claim
      → web 把 token 下发浏览器（httpOnly cookie）,前端调 session 全部带 Bearer
      → session 现有 auth.ts 验签零改动（共享 KOKORO_AUTH_JWT_SECRET）
      → agent 现有 namespace 隔离零改动
```

定案理由：
- **签发权威=kokoro-user**（身份数据在它手里，token 生命周期与账号生命周期同源治理）；web 不自己签，避免双权威。V1 HS256 共享 secret（session 现状即此），升级 RS256/JWKS 留作后续硬化块，不阻塞闭环。
- **namespace=teamId**：对齐 handbook「teams/个人=namespace 实例」——个人即 personal team，切团队=换 namespace 重新签发，session/agent 无需任何团队概念。
- admin 双后台（oidc/magic-link）是运营者身份，与终端用户签发**两套并行**，互不复用。

### 2.2 运行时模型与计费链

```text
run 受理(session start-message):
  1. model 选择子照旧过 model_policy
  2. (新增) 调 kokoro-model GET /model-bindings/resolve?label=<选择子>&site_id=…
     → {transport: litellm|direct, gateway_model_name, pricing_ref}
  3. (新增) 调 kokoro-credit POST /holds {account: namespace, amount: quote(pricing, est), idempotency_key: run_id}
     余额不足 → 402 credit_insufficient（新错误码,web 可导购）
  4. RuntimeConfig.model = {provider: "litellm", name: gateway_model_name}（契约已有形状,不加字段）
run 执行(agent): model factory 的 litellm 档 = OpenAI 兼容客户端 → KOKORO_LITELLM_BASE_URL + 网关 key
run 收口(session relay 终态):
  run.completed{token_usage} → POST /holds/:id/capture {amount: settle(pricing, usage), idempotency_key: run_id}
  run.failed / cancel        → POST /holds/:id/release
```

定案理由：
- 计费收口放 **session**（run 生命周期唯一 owner，token_usage 已全链路贯通到 run.completed）；agent 零计费概念。
- hold→capture 而非 postpaid：多租户云端先守「不透支」，估算冗余系数配置化。
- pricing 真源在 credit（已有 pricing 面）；session 不算钱，只传 usage。
- credit/model 不可达时 **fail-closed 可配**（`KOKORO_BILLING_MODE=enforce|shadow|off`）：shadow=全链调用但不拒绝（灰度实测），off=纯开发。默认 dev=off、e2e=enforce。

## 3. 分块与验收（执行序）

| 块 | 内容 | 仓 | 验收 |
|---|---|---|---|
| **P1 签发链** | user 新增 auth/sessions 签发端点（含 resolve-or-create、personal team、HS256、TTL/时钟容差；服务间鉴权用 platform-kit 现有 service token 口径） | kokoro-user | user 测试套全绿+新端点单测；手动 curl 签发 → session /sessions 200 |
| **P2 web 接线** | web 登录（next-auth,V1 邮件 magic-link 对齐 admin-web 形态）→ 调 P1 换 token → cookie → 全部 session 调用带 Bearer；host→site 解析 V1 单站点缺省常量 | kokoro-web | Playwright 主路径:登录→发消息→SSE 有流;⚠️ web 仓有外部会话在建 shell,**开工前必须与其分区或串行,不并发写** |
| **P3 模型网关链** | agent model factory litellm 档（OpenAI 兼容,env 网关地址/key）；kokoro-litellm 配置从 example 落地一份 dev 真配 | kokoro-agent, kokoro-litellm | agent 单测（假 OpenAI 端点）+ 本地 litellm 起真网关 smoke |
| **P4 计费链** | session 接 model resolve + hold/capture/release（billing mode 三档,幂等键=run_id）；402 错误码进契约 | contract, kokoro-session | session 双后端测试;资金安全负向:capture 幂等重放、失败必 release、shadow 不拒绝 |
| **P5 编排+e2e** | 根 compose 收编 mysql+platform 5 服务+litellm+mongo/redis/minio；e2e 新段 E2E-40:真 user 签发 token 全链跑 run → credit ledger hold/capture 断言 | 主仓 | `docker compose up` 一键起环;e2e-v21-gate 全绿+E2E-40 |

依赖：P1→P2、P1→P4（account=namespace）、P3→P4（capture 需真 usage）、P5 收口。P2 与 P3/P4 可并行（不同仓）。

## 4. 契约增量（单源,随块落地）

- P4: http.yaml 错误码 `credit_insufficient`（402）；session 内部对 platform 的出站调用**不进 contract/**（服务间 API 权威在各 platform 模块的 zod schema,经 openapi/手工镜像消费——不做双源）。
- RunRequest/RuntimeConfig **零改动**（provider=litellm 复用现有 model 形状）——D9 前缀不变量不受影响。

## 5. 不做（本闭环外,记档不丢）

platform 内环遗留（payment provider config/webhook 验签/Subscription 写路径/hold 过期回收任务/ModelLabel.defaultBinding 消费）→ 独立硬化块,不阻塞闭环;RS256/JWKS 轮换、团队切换 UX、多站点真解析、kokoro-i18n 复活 → 后续;swarm/组织级配额 → P2。

## 6. 风险与回滚

- secret 共享面扩大（user+session 双持）：部署以同一 secret 注入,轮换=双写窗口;泄露即全域,故 P1 落地即禁 secret 进日志/错误（platform-kit envelope 已有掩码习惯,补测试）。
- e2e 既有 `sign_token` 夹具保留（gate 自签仍是合法部署形态——secret 相同即等价）,E2E-40 增量走真签发,两轨并存不迁移。
- 计费链任何一步不可达:enforce 档拒绝受理（402/503）,绝不"先跑后补账"。
