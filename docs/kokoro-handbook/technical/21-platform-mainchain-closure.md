# 21. Platform × 主链闭环（现状事实）

状态：正式册（P1-P5 已全部落地，本文描述当前有效事实与边界规则）
收编自：`docs/superpowers/specs/2026-07-11-platform-mainchain-closure.md`（该文已转历史入口）
上级：[20-kokoro-v1-technical-plan](20-kokoro-v1-technical-plan.md)、[18-capability-namespace-auth-sandbox-artifacts](18-capability-namespace-auth-sandbox-artifacts.md)

## 0. 一句话

> platform 内环（user/site/model/credit/payment/platform-kit/admin 双后台）与主链（web/session/agent）已通过三条外环线闭合：①终端身份签发链；②运行时模型与计费链；③一键编排与跨栈 e2e（E2E-40）。闭环只接线，不重造任何一环。

## 1. 铁边界（长期有效）

- GA/agent 只消费**不透明 namespace**（`RunRequest.context.namespace`），身份语义在上游解析；session 禁 `user:/team:/site:` 等前缀。
- session 消费端契约：HS256 Bearer JWT，`namespace = payload.sub`。签发方接入未改动该契约。
- 模型/provider/凭据/注册归 kokoro-model + kokoro-litellm；agent 不存 provider 凭据（litellm 网关档只持网关地址与网关 key）。
- 扩张=加配置不是加代码：新 provider/新价格/新站点只是 platform 数据/配置变更。
- agent 零计费概念；计费收口在 session（run 生命周期唯一 owner）。

## 2. 身份签发链（已落地）

```text
浏览器 → kokoro-web（登录 UX，next-auth 邮件 magic-link，得 externalUserId）
      → kokoro-user POST /auth/sessions（服务间调用，platform-kit callService 口径）
         入参: {site_id, external_user_id, email?}   出参: {token, namespace, user, team}
         行为: resolve-or-create user + personal team → 签发 HS256 JWT
               sub = teamId（ULID，天然不透明，个人=personal team）/ exp / iss=kokoro-user / site_id claim
      → web 把 token 经 httpOnly cookie 下发，前端调 session 全部带 Bearer
      → session auth.ts 验签零改动（共享 KOKORO_AUTH_JWT_SECRET）
      → agent namespace 隔离零改动
```

规则与事实：

- **签发权威=kokoro-user**：身份数据与 token 生命周期同源治理；web 不自己签，避免双权威。
- **namespace=teamId**：个人即 personal team，切团队=换 namespace 重新签发；session/agent 无团队概念。
- V1 使用 HS256 共享 secret（与 session 现状一致）；RS256/JWKS 轮换属后续硬化块。
- admin 双后台（oidc/magic-link）是运营者身份，与终端用户签发**两套并行**，互不复用。
- host→site 解析 V1 为单站点缺省常量。
- secret 不进日志/错误输出（platform-kit envelope 掩码，有测试覆盖）。

## 3. 运行时模型与计费链（已落地）

```text
run 受理（session start-message）:
  1. model 选择子过 model_policy
  2. 调 kokoro-model GET /model-bindings/resolve?label=<选择子>&site_id=…
     → {transport: litellm|direct, gateway_model_name, pricing_ref}
  3. 调 kokoro-credit POST /holds {account: namespace, amount: quote(pricing, est), idempotency_key: run_id}
     余额不足 → 402 credit_insufficient（契约错误码，web 可导购）
  4. RuntimeConfig.model = {provider: "litellm", name: gateway_model_name}（复用既有 model 形状，未加字段）
run 执行（agent）: model factory 的 litellm 档 = OpenAI 兼容客户端 → KOKORO_LITELLM_BASE_URL + 网关 key
run 收口（session relay 终态）:
  run.completed{token_usage} → POST /holds/:id/capture {amount: settle(pricing, usage), idempotency_key: run_id}
  run.failed / cancel        → POST /holds/:id/release
```

规则与事实：

- **hold→capture 而非 postpaid**：多租户云端先守「不透支」，估算冗余系数配置化。
- pricing 真源在 credit；session 不算钱，只传 usage。
- `KOKORO_BILLING_MODE=enforce|shadow|off`：shadow=全链调用但不拒绝；off=纯开发。默认 dev=off、e2e=enforce。
- enforce 档下计费链任何一步不可达即拒绝受理（402/503），绝不「先跑后补账」。
- 幂等键=run_id：capture 幂等重放、失败必 release、shadow 不拒绝，均有资金安全负向测试覆盖。

## 4. 契约面

- http.yaml 错误码 `credit_insufficient`（402）已进 contract。
- session 对 platform 的出站调用**不进 contract/**：服务间 API 权威在各 platform 模块的 zod schema，经 openapi/镜像消费，不做双源。
- RunRequest/RuntimeConfig **零改动**（provider=litellm 复用现有 model 形状），D9 前缀不变量不受影响。

## 5. 编排与 E2E-40 断言面（已落地）

- 根 compose 收编 mysql + platform 5 服务 + litellm + mongo/redis/minio，`docker compose up` 一键起环。
- e2e 新段 **E2E-40**：真 kokoro-user 签发 token 全链跑 run → credit ledger hold/capture 断言；e2e-v21-gate 全绿。
- e2e 既有 `sign_token` 自签夹具保留（secret 相同即等价的合法部署形态），与 E2E-40 真签发**两轨并存**，不迁移。

## 6. 闭环外遗留（记档，不属本册范围）

platform 内环遗留（payment provider config/webhook 验签/Subscription 写路径/hold 过期回收任务/ModelLabel.defaultBinding 消费）→ 独立硬化块；RS256/JWKS 轮换、团队切换 UX、多站点真解析、kokoro-i18n 复活 → 后续；swarm/组织级配额 → P2。

## 7. 已知风险

- secret 共享面（user+session 双持）：部署以同一 secret 注入，轮换=双写窗口；泄露即全域。
