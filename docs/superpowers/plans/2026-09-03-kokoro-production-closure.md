# Kokoro 十仓生产级工程闭环总实施计划

> 日期：2026-09-03  
> 状态：执行中  
> 总目标：以可执行门禁而不是口号，完成 Root 与十个正式仓库的架构、契约、SQL、代码、文档、交互和发布闭环。

## 1. 范围与完成定义

正式仓库固定为：

1. `kokoro`：Web 产品界面与同源 HTTP adapter；
2. `kokoro-bff`：公开 Product API、Conversation、Message、Share、Project、ScheduledTask 与 durable AG-UI projection；
3. `kokoro-agent`：Run、checkpoint、lease、tool journal、执行事件、HITL 与 evidence；
4. `kokoro-iam`；
5. `kokoro-system`；
6. `kokoro-model`；
7. `kokoro-billing`；
8. `kokoro-capability`；
9. `kokoro-storage`；
10. `kokoro-scheduler`。

完成必须同时满足：

- 十仓职责、依赖方向、机器契约、SQL owner 和 Redis/PostgreSQL 隔离可由脚本验证；
- Agent 三项 P0、BFF 的真实持久化与 AG-UI 投影、Web 的唯一协议链路均有真实故障恢复测试；
- 每仓代码、Schema、contract、测试、CI、文档在同一提交切片中收敛；
- 主工作区重新执行十仓质量门禁、真实 PostgreSQL/Redis 集成、浏览器交互和候选镜像 smoke；
- 最终报告只引用本轮产生的命令输出和 evidence，不继承历史“100 分”结论。

## 2. 固定架构裁决

```text
Browser
  -> kokoro same-origin adapters
  -> kokoro-bff public Product API
  -> IAM/System/Model/Billing/Capability/Storage owner APIs
  -> Agent run ingress/control/events
  -> Scheduler generic schedule/lease/dispatch
```

- 浏览器不直连业务 owner、Agent、数据库或 Redis。
- AG-UI 是 Web 与 BFF 之间唯一 Agent 网络事件协议；Vercel AI SDK 的 `UIMessage` 只作为 Web 内部视图模型。
- BFF 不读取 Agent 数据库；Agent 不拥有 Conversation、Project 或 ScheduledTask 产品事实。
- PostgreSQL 保存事实；Redis 只承担 cache、stream、queue、lease、限流和协调。
- 本地只复用一个 PostgreSQL 和一个 Redis；应用从源码启动，业务镜像只用于候选发布验证。
- V1 clean-slate：无 migration 链、无兼容层、无双读双写、无生产 Fake/InMemory、正式 SQL 无外键。

## 3. 并行执行波次

### Wave 0：Root 治理基线

详细计划：[`2026-09-03-governance-documentation-baseline.md`](2026-09-03-governance-documentation-baseline.md)

- [x] 将 `AGENTS.md` 从七仓规则升级为十仓长期中文控制手册；
- [ ] 增加代码粒度、React/CSS、文档、公开 API、AG-UI/Vercel 与本地基础设施规则；
- [ ] 将七仓静态/全量验证器升级为十仓验证器；
- [ ] 建立十仓文档矩阵和 contract provenance 门禁；
- [ ] 更新 `docs/CURRENT.md`、`docs/CODEBASE_MAP.md`、`scripts/INDEX.md`。

### Wave 1：文档与契约事实源

- [ ] 每仓补齐 `INDEX.md`、`docs/INDEX.md`、`docs/CURRENT.md`、`docs/TECHNICAL_DESIGN.md`、`docs/API_CONTRACT.md`、`docs/DATA_MODEL.md`、`docs/SECURITY.md`、`docs/RELIABILITY.md`、`docs/ACCEPTANCE.md`、`docs/SLO.md`、`docs/RUNBOOK.md`；
- [ ] 每个实际拥有机器契约的仓库补齐 `contract/README.md`，写明 owner、visibility、版本、生成命令、breaking policy 和 provenance；
- [ ] 将 BFF 公开 OpenAPI 收敛到 `kokoro-bff/contract/openapi/v1/openapi.yaml`；
- [ ] 为 Agent 自有 ingress/event/control 边界建立本仓机器契约，不复制 Capability、Storage 或 BFF 模型；
- [ ] 对十仓运行文档 lint、链接、契约 lint、breaking 与示例验证。

每个仓库只分配一个写入 Agent；IAM/System/Model/Billing/Capability/Storage/Scheduler 可并行，Web/BFF/Agent 在其 P0 设计定稿后再写。

### Wave 2：Agent 正确性与 DDD 收敛

- [ ] 在 `kokoro-agent/database/schema.sql` 建立唯一 canonical schema；删除 runtime DDL 和 epoch 时间事实；
- [ ] admission 事务原子写入 Run aggregate 与 outbox，再由 dispatcher 投递 Redis，消除“先 claim 后落库”丢 Run 路径；
- [ ] 所有 Run、control、evidence、checkpoint、memory 查询显式携带受信 `tenant_id`；
- [ ] 引入 `generation + owner + lease_token` fencing，旧 worker 不能提交状态；
- [ ] tool journal 先以唯一 effect identity 竞争写入，只有 winner 执行副作用；
- [ ] 将超大 repository/supervisor 拆入 Domain/Application/Infrastructure/Interfaces；
- [ ] 接入真实 Capability/Storage clients，移除生产 fixture 与 `NoSkillsClient`；
- [ ] 用真实 PostgreSQL/Redis 覆盖 trim、TTL、worker crash、lease expiry、duplicate delivery、resume 与跨租户测试。

### Wave 3：BFF Product API 与持久化

- [ ] 移除 live composition 中的 `MockBffStore` 和通用 owner proxy；
- [ ] 为 IAM/System/Model/Billing/Capability/Storage/Agent/Scheduler 建立显式窄 adapter；
- [ ] Project、Conversation、Message、Share、ScheduledTask 使用真实 PostgreSQL repository；
- [ ] ScheduledTask 采用 IANA timezone + local rule + UTC occurrence，事务写 task 与 outbox；
- [ ] 幂等 digest 覆盖 method、canonical path、query、selected headers 与 canonical body，并具备并发 fencing；
- [ ] 建立 durable AG-UI projection ledger、唯一 public cursor、断线恢复和 cursor GC 策略；
- [ ] OpenAPI 与运行时路由、错误、权限、幂等和事件生命周期双向测试。

### Wave 4：Web 交互、CSS 与协议统一

- [ ] 删除 legacy `SessionEvent` 双读和 runtime fallback，只消费 AG-UI；
- [ ] 实现仓内 `AgUiChatTransport`，映射为 Vercel AI SDK `UIMessage`，网络层不增加第二套 Vercel stream；
- [ ] 明确 `idle/submitting/queued/streaming/awaiting_approval/resuming/cancelling/reconnecting/completed/failed` 状态机；
- [ ] optimistic echo 通过 receipt/event reconciliation 收敛，使用 generation guard 防止旧流覆盖新状态；
- [ ] 拆分超过预算的 React 与 CSS modules，保持现有安静、克制、专业工作台视觉方向；
- [ ] 统一 token、focus、reduced-motion、keyboard、IME、mobile、错误和 reconnect 体验；
- [ ] 建立 Playwright、axe、视觉回归、响应式和 bundle budget 门禁；
- [ ] 禁止 Web 直连 IAM，收窄 catch-all same-origin adapters，并加入 timeout、body limit、CSRF/CSP 与安全响应头。

### Wave 5：Developer API 文档门户

- [ ] 在 Root 新建 `developer-docs/`，Root 只拥有门户编排、指南和版本 catalog；
- [ ] `developer-docs/catalog/contracts.yaml` 固定各 owner contract artifact 的版本、来源 commit 和 digest；
- [ ] 从 BFF 公开 OpenAPI 自动生成 Reference，不复制可编辑 schema；
- [ ] 编写 quickstart、auth、concepts、guides、AG-UI、webhook、errors、pagination、idempotency、rate limit、retry、security、versioning、changelog；
- [ ] 提供可执行 TypeScript、Python 和 cURL 示例；
- [ ] CI 校验链接、示例、构建、contract provenance，并阻止内部 API/secret 进入公开门户。

### Wave 6：主工作区最终闭环

- [ ] 运行 Root 十仓结构门禁；
- [ ] 六个 TypeScript owner 仓运行 `pnpm lint && pnpm typecheck && pnpm test && pnpm build && pnpm db:apply-schema`；
- [ ] BFF/Web 分别运行本仓完整门禁和浏览器 E2E；
- [ ] Agent 运行 Pyright strict、pytest、真实 PostgreSQL/Redis fault/recovery tests；
- [ ] Scheduler 运行 format、vet、test、race、build 与真实 Redis integration；
- [ ] 在全新 database 上安装每仓 schema，检查外键、时间类型、约束命名、tenant predicate 和索引；
- [ ] 构建候选镜像并执行 health/ready/smoke、漏洞扫描、SBOM/provenance/signature 门禁；
- [ ] 生成本轮 evidence 和未完成项清单，按仓提交并记录 commit。

## 4. 提交策略

- Root、十个子仓分别创建 `codex/production-closure-*` 分支；
- 每个提交只完成一个可独立验证的纵向切片；
- 推荐顺序：`contract/test -> domain/application -> infrastructure/interfaces -> docs/CI`；
- BFF 现有 `docs/api/v1/agui-chat.md` 未提交修改视为协作者工作，不覆盖、不回滚；
- worker 的退出码不作为完成证据，主工作区必须重跑该仓验证。

## 5. 风险控制

- 文档规范先进入审计模式，再逐仓修复；在全仓补齐之前不得把失败门禁误报为回归；
- Agent P0 与 BFF/Web 协议变更禁止并行写同一 contract，先由 owner 提交再更新消费者；
- 共享 PostgreSQL/Redis 由 Root orchestration 复用，执行前探测并禁止重复启动；
- 任何“100 分”“顶级标准”结论都必须附当前 commit、命令、时间和 evidence 路径。
