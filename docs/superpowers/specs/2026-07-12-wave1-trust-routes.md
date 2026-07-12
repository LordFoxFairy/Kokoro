# Wave 1 · TRUST-ROUTES 子 spec(获批纲领 D2 的 platform 落地)

状态:执行稿(上级=2026-07-11 总设计稿 D2/§6 Wave1-1,已获批)
owner:单 worker(kokoro-platform,子仓 worktree 分支 wave1/trust-routes)

## 目标

platform 全服务 default-internal:每条路由声明唯一访问等级,per-caller 凭据,生产缺凭据启动失败。
交付后不变量:①能触达端口≠能调路由;②runtime 凭据调不动 admin 路由;③共享空 secret 静默直通不复存在。

## 等级与凭据(D2 原文照抄)

```text
public            health、公开站点元数据、provider webhook(另验 provider 签名)
runtime-internal  session/agent 等运行时服务
web-bff           终端 web BFF
admin             platform-admin(仍叠加 operator RBAC)
```
- 调用方带 `x-kokoro-service: <caller>` + `x-kokoro-internal-secret: <该 caller 的 secret>`。
- 每 caller 独立 secret:env `KOKORO_INTERNAL_SECRET_<CALLER>`(如 _SESSION/_WEB_BFF/_ADMIN/_HUB/_PAYMENT/_CREDIT);服务端按路由等级 allowlist 校验 (caller∈等级允许集) ∧ (secret 匹配该 caller)。
- 测试构造器显式 `insecureLocal: true` 才直通;`NODE_ENV=production`(或 KOKORO_ENV=production)下任一所需凭据缺失 → 启动 fail-fast。dev 未配=直通+启动时告警一次(过渡态,与现状兼容)。

## 落点

1. platform-kit:`route-access.ts`——`declareRouteAccess(app, matcher, level)` + 入站校验钩子(替换/包裹现 internal-secret-guard;guard 保留为实现细节)。`callService` 增 caller 参数(签名兼容:老用法=legacy 单 secret,标记 deprecated 注释)。
2. 全模块路由矩阵显式声明(site/user/model/credit/payment/hub 每条路由标等级;OpenAPI 文档路由生产默认 internal):
   - public:各 /healthz、site 公开元数据(若有)、payment /payments/webhooks/:provider(另有 provider 验签)。
   - runtime-internal:credit usage hold/settle/release、model resolve、hub runtime pool(现 /hub/skills/pool——HUB-AUTHZ 会再细分,本项先归 runtime-internal)。
   - web-bff:user /auth/magic-links*、hub self-service(暂全关=空集,HUB-AUTHZ 开);user /auth/sessions 收编 internal(纲领 §5.1:不再任意签发 oracle;e2e/closure-up 用 runtime 凭据调)。
   - admin:各 /admin/**。
3. 调用方接线:credit→site/user、payment→credit、admin 网关→模块、(session/web 的 env 名先定死进 .env.example,session 侧实改属 AUTH-P0/R 波,但 gate/closure-up 必须本项内配好让 e2e 全绿)。
4. 主仓 closure-up/e2e gate 同步:注入各 caller secret env(dev 假值),session billing client 需带 caller 头——**session 仓最小改动**:billing/client.ts 出站带 `x-kokoro-service: session` + env secret(此为跨仓例外,准许;user 签发调用同)。gate 的 user 直调(签发/E2E-40 种子)改带 runtime 凭据。

## 验收

- platform 全模块 unit+integration 只增不减;新负向矩阵:无头 401/错 caller 401/对 caller 错 secret 401/runtime 凭据打 admin 403/production 缺凭据启动失败(spawn 断言退出码)。
- 主仓 `python3 scripts/e2e-v21-gate.py` 全绿(secret 全配下跑通=纲领 §8.2-2 场景)。
- 不做:JWT 化服务凭据/轮换自动化(SEC-2);Hub 三面细分(HUB-AUTHZ)。
