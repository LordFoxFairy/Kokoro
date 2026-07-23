# PRD：全面"真正 OK" campaign

状态：草案待评审
日期：2026-07-22
用户 /goal：除支付真网关外，一切都要能**真实测试、真正打通**，这一次做到全面 OK。
附带三件：① 列需求 PRD（本文）；② 按 CLAUDE.md 补/更新 INDEX.md 方便迭代；③ web 收拢（用户面 + 后台管理归一个 web 子仓）。

---

## 0. 本轮实测事实（PRD 的地基，全部亲验）

- **GLM key 死**：Aura `config.json` 内联的 bigmodel key，对 openai-paas / coding-paas / anthropic / coding-anthropic 四端点 × glm-4.6/4/flash/5 × Bearer/x-api-key，连纯 `GET /models` 全部 **401「身份验证失败」code 1000**。是 provider 鉴权层拒 token，**非接线问题**。Aura 能跑大概率靠其 `openrouter` provider（走 env `OPENROUTER_API_KEY`，不在文件里）。
- **模型接线本就完整**：kokoro-model 的 `claude-code` label/binding → litellm 网关 → 后端已闭环；凭据走 `secretRef=env:...`（ADR-010，明文不入库）。**换任意有效 key = 改一处网关 env**，无需改 model 库代码。
- **一批能力造好了默认 OFF**：`KOKORO_BILLING_MODE=off`（计费空转）、`KOKORO_HUB_MCP_MUTATION=off`（MCP 写面 503）、secret broker 未配即 503、真 checkout 501 + mock 生产禁用。
- **可观测缺口**：platform 6 服务全无 `/metrics`；session 无 `/healthz`；agent `/metrics` 默认关。
- **web 双栈**：admin-web = Ant Design Pro + NextAuth + Prisma 直连 DB（Next15/React18，在 kokoro-platform 内）；user web = 自定义设计 + session BFF 不碰 DB（Next16/React19，独立仓）；两者零 `@kokoro/*` 共享。

---

## 1. 范围

**IN（这轮真做真测）**
- WS1 模型凭据收口 + 全链真测（ollama 作真 stand-in；有效 key 即生产级）
- WS2 计费点亮 enforce + 全链真测（含离线/mock 充值作为唯一到账路径）
- WS3 能力开门真测（MCP 写面、secret broker）
- WS4 可观测补平（platform /metrics、session /healthz、agent metrics）
- WS5 真环境证明（compose 真机 build&up 烟测、真 S3 档、docker 沙箱默认）
- WS6 web 收拢为 monorepo（apps/user + apps/admin + packages/*）
- WS7 INDEX.md 补/更新（随各 WS 落地同步）

**OUT（明确不做）**
- 真支付托管网关（用户已砍，个人无商户、做海外，mock/离线到账够用）
- 媒体生成 music/video/图像/TTS（用户已缓，代码侧不占坑）

---

## 2. 工作流明细

### WS1 · 真模型凭据收口
- **目标**：模型链路"随时一把有效 key 即生产级"，且用真模型（非 fake）证明全链。
- **交付**：
  - dev 默认切 ollama 真模型（已具备，`KOKORO_DEV_LOCAL_FALLBACK=1` 持久化在 `.env.dev`）——保证"默认起环即真模型驱动工具"。
  - 文档化"接有效 key"路径：`CLAUDE_CODE_BASE_URL/API_KEY/MODEL` 三值注入 litellm 网关（GLM=coding-paas 端点；openrouter/openai/deepseek 同形），一处切换。
  - （可选增强，待定）admin 侧"网关后端"配置面：admin 选 provider + 填 secretRef，免手改 env。
- **验收**：全新会话 chat 真出文（非罐头）；agent 真调 read/write/execute/web 工具跑通一条多步任务（ollama 力所能及的粒度）。
- **依赖**：生产级稳定需**用户给一把有效 key**（任意 provider）。无 key 时以 ollama 交付"链路真"。

### WS2 · 计费点亮 + 充值到账真测
- **目标**：把 credit-payment 从"测试绿"变成"部署开着、真扣费、真能充"。
- **交付**：staging/dev 档 `BILLING_MODE=enforce`；确认 hold→settle→quota 真扣；mock/离线充值面在该档可用（作为砍掉真网关后的唯一到账路径）。
- **验收**：真栈 e2e——签发→清零→充值到账→对话扣费→余额/流水自洽；余额不足→402；配额超限→402。
- **依赖**：无（不需外部凭据）。

### WS3 · 能力开门真测
- **目标**：MCP 写面 + secret broker 在受控档打开并真测。
- **交付**：`KOKORO_HUB_MCP_MUTATION=on` + secret 主密钥配置档；真注册一个 MCP server + 存取一次 secret handle。
- **验收**：注册/启停/删真生效（非 503）；secret 值只进不出；agent 按 revision 快照消费。
- **依赖**：无。

### WS4 · 可观测补平
- **目标**：上线不盲跑。
- **交付**：platform 6 服务经 platform-kit 收一处补 `/metrics`；session 补 `/healthz`；agent metrics 默认档评估。
- **验收**：各服务 `/metrics` 真出 prometheus 文本、`/healthz` 200。
- **依赖**：无。

### WS5 · 真环境证明
- **目标**：把"config 校验过"升级成"真跑起来过"。
- **交付**：在用户主机 `docker compose ... build && up` 一次真烟测；真 S3 存储档跑一轮；docker 沙箱作默认 backend 真测。
- **验收**：16 服务起齐、健康检查绿、一条端到端对话跑通。
- **依赖**：需在用户主机执行（拉基础镜像）。

### WS6 · web 收拢（monorepo）
- **目标**：web 只有一个子仓，用户面 + 后台管理都在其中，共享层收敛，方便整体迭代。
- **方案（已定，见 §3 决策）**：`kokoro-web/` 升为 pnpm monorepo：
  ```
  kokoro-web/
    apps/user/     ← 现 kokoro-web 内容（Next16/R19）
    apps/admin/    ← 从 kokoro-platform 迁入的 admin-web（Next15/R18，先原样搬）
    packages/
      contract-types/  ← 跨仓契约类型单源（web 侧）
      i18n/            ← 收敛 @kokoro/i18n，两 app 共用
      ui/              ← 后续增量抽共享设计件
  ```
  - 两个**独立部署目标**（admin 仍可挂 admin 子域/内网，直连 DB + NextAuth 边界不变）。
  - `kokoro-platform` 移除 `kokoro-admin-web`（迁走非删）。
- **交付**：monorepo 骨架 + 两 app 各自可 build；共享 i18n 打通；两 app 部署单元（Dockerfile/compose 段）对齐。
- **验收**：`apps/user` 与 `apps/admin` 各自 `build` 绿；两 app 本地起得来；根 compose 两服务解析通过。
- **不做**：不把 admin 强迁到 React19/去 antd（那是后续设计统一，风险独立）；不合并成单 app（安全边界，见 §3）。
- **依赖**：无（纯结构迁移，分阶段可验证：迁移→契约调整→清理）。

### WS7 · INDEX.md 补/更新
- **目标**：按 CLAUDE.md §2 给公开入口/装配/持久化目录补局部架构地图，方便后续迭代。
- **交付**：随各 WS 落地，为改动到的公开入口目录补/更新相邻 INDEX.md（kokoro-model provider 面、hub 写面、session observability、web monorepo 各 app 根、packages/*）。
- **验收**：改动目录均有当前有效 INDEX.md，无死链。
- **依赖**：随 WS1-6 同步。

---

## 3. 决策点（我已定，待你否决）

**web 收拢用 monorepo 两部署，不合并成单 app。** 理由：admin 是 antd Pro + NextAuth + **Prisma 直连 DB** 的特权应用，用户面 web 走 session BFF **从不碰 DB**。合成单 app = admin 的 JS 打进公网用户浏览器包、admin 路由暴露公网源、DB 直连边界与公网面混同——安全上是倒退。monorepo 同时满足你要的"一个子仓 / 收拢 / 方便迭代"，又保住"admin 独立部署、可挂内网"的边界。若你坚持单 app，我再评估路由组 + 中间件强隔离的次优解。

---

## 4. 唯一外部依赖

**一把有效模型凭据**（新 GLM / OpenRouter / OpenAI / DeepSeek / Anthropic 任一，litellm 支持即可）。给了 → WS1 直接生产级；没给 → 我用 ollama 交付"全链真"，其余 WS2-7 全部不依赖它、照常真做真测。

---

## 5. 执行序与验证纪律

WS2 → WS4 → WS3 → WS1(ollama 档) → WS6 → WS5 → WS7，每块开工前发对齐单、收工贴真实验证输出（真栈 e2e，非 happy-path）。WS5 真机烟测需你在主机执行的步骤我给命令清单。

排序原则：先点亮不依赖外部凭据的（钱链/可观测/能力开门）→ 再证模型链真 → 再收 web 架构 → 最后真机总证。
