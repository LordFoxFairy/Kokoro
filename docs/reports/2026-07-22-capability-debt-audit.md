# Kokoro 能力债务审计

状态：2026-07-22 历史审计；不定义当前 Skill/Storage owner。
方法：以当时代码/实测为准校正台账自报；结构、可观测、真模型落点、共享层均为当轮亲验。

> 2026-08-22 覆盖：文中“hub 写、agent 直读同库”仅是当时实现事实。当前设计将 GA 原生
> DeepAgents Skill 的 CRUD/direct reader 留在 GA，将 Client/租户 Skill 的管理面迁至
> Capability/Storage public contract；详见 `docs/kokoro-handbook/technical/backend-design/09-agent.md`、
> `docs/kokoro-handbook/modules/kokoro-agent.md` §6 与
> `docs/kokoro-handbook/technical/29-capability-storage-runtime-architecture.md` §9。

---

## 一句话结论

代码纪律极强：**生产路径零 TODO/FIXME，假件全部锁在 test 内**，无一处生产默认走假。
所以真正的"能力债"不是"没造"，而是**造好了但默认 OFF / 降级**——靠部署期 env 才点亮。
两个同级的上线级阻塞：**① 没有生产真模型；② 计费默认关 + 生产无充值路径**。
其余是可控的工程债与架构债。
你点名的"管理面/用户面一个 web"——现状两个独立 app、差一个大版本，但**不该合**，
真正的债是两边零共享 + 版本漂移。

---

## 零、最关键一层：造好了但默认 OFF / 降级（深扫补充）

这是"打通度"的真相——不是缺代码，是缺"点亮"。以下均为**默认部署即命中**（非误配）：

| 能力 | 开关 / 位置 | 默认态 | 后果 |
|---|---|---|---|
| **计费/计量/扣费** | `KOKORO_BILLING_MODE` `session/main.ts:66` | **off** | 默认部署不校验/不计量/不扣费，credit-payment 整链空转 |
| **生产充值下单** | 真 checkout `payment-service.ts:57` 501 + mock 生产禁用 `mock-pay/route.ts:31` 503 | **无路径** | 上线后用户无法买积分（真 provider 未接 + mock 仅 dev） |
| **登录邮件真发** | `KOKORO_AUTH_MAGIC_DELIVERY` `user/env.ts:33` | **log** | 默认只写日志哈希，不真发邮件；SMTP 已实现需显式开 |
| **MCP 写面**（注册/启停/删） | `KOKORO_HUB_MCP_MUTATION` `hub/env.ts:34` | **off→503** | 读面可用，写面默认不可用（"待跨仓一致后开门"） |
| **MCP 凭据保管** | secret 主密钥 `runtime-routes.ts:102` | **off→503** | 未配主密钥则 secret broker 不可用 |
| **agent 联网检索** | `KOKORO_WEB_SEARCH_PROVIDER` `agent/config.py:132` | **缺席** | 默认 agent 无 web_search/web_fetch（诚实缺席非假件） |
| **记忆语义检索** | `memory.py:41` | **降级** | 无向量检索，退化为子串过滤（"留待未来 embeddings 档"） |

**fail-open（失败放行而非拒绝）——生产需显式收紧：**
- `billing/service.ts:35` shadow 档：resolve/无绑定/hold 失败一律放行免费用量（enforce 档才 402/503）
- `/models` `http/server.ts:744`：模型目录不可达静默回落 profile 候选
- magic-link 限频 `magic-link-rate-limiter.ts:107`：Redis 挂了 fail-open 放行（限频被绕过）
- 内部信任边界 `internal-secret-guard.ts:25`：`x-kokoro-internal-secret` 未配则**直通 + 告警一次**（靠部署补配才强校验）

**单 agent 类型**：`agents/__init__.py` 只注册 `general`；studio 类型 / general⇄studio handoff 图未接线
（会话内**人格 swarm** 已实现，但 **agent 类型**只有 general）。

---

## 一、整体能力评估：按成熟度分层看"哪些是真的"

### A 层 — 真硬（重测 + e2e + 亲验，可信）

- **运行时可靠性脊柱**（Wave 2 R0–R7）：dispatch CAS、control outbox/inbox/receipt、
  tool effect journal、双水位 + quarantine、billing durable journal。有 chaos 门（kill agent/session
  验去重与补偿）。这是全系统最扎实的部分。
- **认证**：magic-link + BFF 密封 cookie（浏览器不持 bearer）+ RS256/JWKS + kid 轮换 + nonce 防 CSRF
  + 邮箱/IP 双维限频；生产 fail-closed。
- **能力中台 hub（历史事实）**：当时 skill 上传/审核/版本/启停、MCP 注册 + secret broker（值只进不出）、读写分离同库
  （agent 直读不跨 hub RPC）；这条 Hub 直读链已被上述 2026-08-22 迁移边界取代。
- **计费闭环（mock）**：credit micros/hold-settle、整数扣费（ceil 向上取整）、payment mock 收银台、
  幂等 grant（order:<id> 不双发）、quota 月窗。真栈 e2e 全绿。
- **沙箱**：docker backend 对真 docker 往返验证（bind mount/exec/双向文件/复用/回收）。
- **多租户隔离**：namespace 单键、siteId 业务边界、owner 隔离、跨 owner 不可枚举。
- **agent 工具面**：read/write/edit_file、execute(shell)、web_search/web_fetch、memory、
  ask_user(HITL)、task(子代理)、deliver、MCP、skills。**工具不缺，缺的是驱动它的模型。**

### B 层 — 接好了但没在真环境证明 / 靠弱替身撑

- **真模型**（最致命）：三级回落 GLM（死）→ ollama 8B（opt-in，默认关）→ fake。
  **prod 默认无模型，dev 靠一个 8B 小模型**（台账自认多步工具编排慢/偶卡）。
- **单机 compose**：`docker compose config` 16 服务全解析，但**从没在真主机 build&up 烟测**过。
- **S3 生产存储**：代码对真 minio 亲验，但 prod 默认仍是共享本地卷，S3 是 opt-in 开关。

### C 层 — 缺口/未做

- k8s manifests（块2 未做）
- 可观测：platform 6 服务**全无 /metrics**（全有 /health）；session 有 /metrics **无 /health**
- per-model 用量分解（B1d：有 UsageRecord 后端，无用户端点 + 无 modelName 映射 + 无 UI）
- 订阅周期计费 UI、发票/税
- `settleRunBilling` 的 settle_pending→settled **非原子**（ledger 幂等不双花，仅 journal 相位抖动）

### D 层 — 架构债（不影响能不能跑，影响长期维护成本）

- **web / admin-web 版本漂移 + 零共享 + i18n 三套**（详见第四节）
- 定价 seed 散在 closure-up 未收编 kokoro-credit 权威 seed（B3c）
- hub Mongo 文档 schema 未收编 contract 单源（mongo-client.ts 两处 TODO(主控)）

### 不算债（用户已决策）

- 真支付网关（个人无商户、做海外，mock 闭环够用——用户砍了）
- 媒体生成 music/video/图像（用户明确暂缓；代码侧无骨架占坑，干净）

---

## 二、能力闭环缺口（逐项"有 X 无 Y"）

| 能力 | 后端 | BFF/端点 | UI | 闭环 |
|---|---|---|---|---|
| 对话/run/HITL | ✅ | ✅ | ✅ | ✅ 真硬 |
| 积分展示/流水/低余额预警 | ✅ | ✅ | ✅ | ✅ |
| 充值（mock） | ✅ | ✅ | ✅ | ✅ |
| skill 上传/审核/启停 | ✅ | ✅ | ✅（admin + 用户 self 面） | ✅ |
| MCP 注册/secret | ✅ | ✅ | ✅ | ✅ |
| 团队自助/邀请 | ✅ | ✅ | ✅ | ✅ |
| 分享只读页 | ✅ | ✅ | ✅ | ✅ |
| 作品库跨会话聚合 | ✅ | ✅ | ✅ | ✅ |
| **按模型用量分解** | ✅ UsageRecord | ❌ 无用户端点 | ❌ | **断**（B1d） |
| **可观测指标** | 部分 | ❌ platform 无 /metrics | — | **断** |
| **真模型** | 链路在 | 网关在 | — | **断**（无有效凭据） |
| **k8s 部署单元** | — | — | — | **无**（只有 compose） |
| 订阅周期计费 | 半场 | — | ❌ UI | 断（低优先） |

---

## 三、缺陷与债务清单（分级 + 文件位置）

### P0（挡上线）

1. **无生产真模型** — `scripts/closure-up.py:167` 三级回落；GLM 全 401（bigmodel 侧拒，非接线）。
   有效 GLM/云 key 进 `kokoro-agent/.env` 即自动升级。
2. **计费默认关 + 生产无充值路径** — `KOKORO_BILLING_MODE=off` 默认空转；真 checkout 501 +
   mock 生产禁用 → 上线后用户买不了积分。想"赚钱"就必须先把这条从"测试绿"变成"部署开 + 有真下单面"。
3. **compose 未真机烟测** — `deploy/README.md` 记明需用户主机拉基础镜像 build&up。

### P1（上线前该补）

4. **可观测缺口（逐服务实测）** —
   `/metrics`：仅 session 有；agent opt-in（`KOKORO_AGENT_METRICS_PORT` 默认 None）；
   platform 全 6 业务服务 + web/admin-web **全无**。
   `/healthz`：platform 各服务 + platform-admin 有；**session 无**（仅 /metrics）；agent/web/admin-web 无。
5. **k8s manifests 缺** — hub/redis/secret/litellm + 应用层单元未补（块2）。
6. **生产 fail-open 需显式收紧** — billing enforce 档、内部 secret 强校验、限频后端硬依赖，
   都要在生产 env 显式开，否则默认放行（见第零节）。
7. **settleRunBilling 非原子** — settle_pending→settled 相位可回退（台账 Wave2 harden 记明）。

### P2（架构清理，不挡上线）

6. **web/admin-web 零共享 + 版本漂移** — Next 16/R19 vs 15/R18；i18n 三套。
7. **B1d 按模型用量分解** — UsageRecord 无用户端点 + modelBindingId→模型名映射缺。
8. **定价 seed 未收编** — chat 40/120 散在 closure-up，未迁 kokoro-credit seed:builtin（B3c）。
9. **hub Mongo schema 未收编 contract 单源** — `kokoro-hub/.../mongo-client.ts:59,92` TODO(主控)。

---

## 四、web 结构专项：不该合，但该收敛共享层

**现状（实测）：**

| | 用户面 `kokoro-web` | 管理面 `kokoro-platform/kokoro-admin-web` |
|---|---|---|
| 仓 | 独立仓 | platform 仓内 |
| 框架 | Next 16.2.6 / React 19.2.4 | Next 15.5 / React 18.3 |
| 共享 | 零 `@kokoro/*` 依赖 | 用 `@kokoro/i18n` 窄包 |
| i18n | 自造整套引擎（11 文件 + MT 管线） | 复用 `@kokoro/i18n` |

**判断：**

- **不该**塞进"一个 app、不同子目录"。管理面是运营/员工、RBAC、看全租户账单 + PII，
  按安全标准必须与公网用户 app **分源、分部署、分域名**（`admin.x` vs `app.x`，宜挂 VPN/IP 白名单）。
  合成一个 app = admin JS 打进公网用户浏览器包、admin 路由暴露公网源，一处配错两个全崩。
- **真正的债**：两边重复造轮子 + 版本漂移。web 把 `@kokoro/i18n` 已有引擎重实现一遍；
  差一个 Next/React 大版本；设计系统/api-client 各写各的；web 连 platform workspace 都不在。
- **标准解**：保持两个部署，抽 `@kokoro/ui`（设计系统）、`@kokoro/i18n`（web 切共享包）、
  `@kokoro/api-client` 共享包，两个薄 app 壳消费；对齐框架版本。

---

## 五、深刻打磨：建议动作序（不问，直接给定序）

1. **真模型收口**（解 P0-1）：要么你给一把有效 GLM/云 key（进 `.env` 即自动升级），
   要么把 kokoro-model 的 litellm 凭据管理做成加密存储 + admin 可换 provider，dev 先用 ollama 顶住。
   这一步不通，下面的体验打磨都是在弱脑子上打磨。
2. **计费点亮 + 充值面收口**（解 P0-2）：生产 env 开 `BILLING_MODE=enforce`；把 mock 下单面
   在生产可控开放（你已砍真网关，那就明确"mock/离线发放"作为唯一充值路径并让它生产可用），
   否则"赚钱"这条链是灭的。
3. **compose 真机烟测**（解 P0-3）：在你主机上 build&up 一次，把"config 过"变成"真跑起来"。
4. **可观测补平 + fail-open 收紧**（解 P1-4/6）：platform 6 服务补 /metrics（platform-kit 收一处）、
   session 补 /healthz；生产 env 显式收紧 billing/secret/限频。上线不能盲跑、不能默认放行。
5. **共享层收敛**（解 P2）：抽 `@kokoro/ui` + web 切 `@kokoro/i18n` + 对齐 Next/React 版本。
   这是"方便管理"的正解。
6. **k8s manifests**（解 P1-5）：与 compose 对齐，补 hub/redis/secret/litellm。
7. 余下 P2（B1d/B3c/hub schema/settle 原子化/MCP 写面开门）随手清，非阻塞。

排序原则：**先让脑子真、再让钱链通、再让部署真、再让运维可观测、最后收架构债**。
UI 细节打磨排在真模型之后——在 8B 小模型上打磨多步编排体验是解错题。
</content>
</invoke>
