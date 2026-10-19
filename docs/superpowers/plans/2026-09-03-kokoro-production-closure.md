## 2026-10-19 既定 MCP availability 消费配对集成

原字段13被旧BFF decoder拒绝的故障已按既定边界修复。BFF [PR #11](https://github.com/LordFoxFairy/kokoro-bff/pull/11) 已合入 `f6ae19cb8aeebc1fe4744bbefaae986843d93172`，App [PR #39](https://github.com/LordFoxFairy/kokoro-app/pull/39) 已合入 `0a0bf9b0a414405684d0d6ffb2cdfbb26c341a5c`；各merge tree与已验head精确相等。Root仅更新这两个gitlink，Platform仍4a4e4c4，其余owner与公共契约不动；不重新实现已合协调器。CI按用户要求不等待，不把未运行/失败称通过。

BFF最终七门0，contract847/architecture36、default1492 PASS/3原资源SKIP；App完整七门0，contract288/architecture50、default4240 PASS/0SKIP，原完整桌面/手机Playwright38 PASS、0retry/原timeout。只增加3条App独有风险回归，原8测试断言经精确逆证保留；先前Prepare fixture失败已按显式owner字段配对并全门重跑。实际App client→BFF HTTP/Native SDK五态及历史/拒绝链通过，IAM/Native owner/同源桥受控，不能冒正常整链。真实Chromium四组件1280/390、Server和Connector字段独立、多连接、键盘及零自动动作通过。Admin25操作仅Skills/Provider/包，不消费个人对象，无Admin改动。

本次是已批准消费者修复与组合交付，不是新增功能轮。正常源/配置/服务/数据库/登录/权限/积分保持，模型、实际工具和扣费继续暂停；未切换正常运行。正常IAM/Platform完整产品链、Manus逐态对照/手册、其他既有知识/记忆等未交付mixed与聊天/项目细节仍未完成。Manus现有tab本次仅AX可读、隐藏视口宽0未获新图，不冒像素一致；本轮Root876输入与12gitlink停写无漂移，拓扑PASS、完整pytest1845 PASS/3原资源SKIP、diff check0；首拓扑失败仅私有克隆origin仍是本地路径，按canonical .gitmodules同步私有remote后重跑，不改检查器或生产源；首pytest1844 PASS/1 FAIL仅因fresh私有Storage未装AWS SDK，package/lock与原owner核等后只读复用既有依赖、未在链接上执行pnpm，完整门重跑。原静态标准239告警/7未验及旧consumer inventory CLI失败不纳入扩修，不冒全仓通过。原始日志仅ignored var/dev/app-mcp-availability-20261019及mcp-availability-integration-20261019。

# Kokoro 九个运行仓生产级工程闭环总实施计划

## 2026-10-19 本轮收口决定

本轮只合并既有交付和必要契约配对，受影响九个owner已通过正式PR合入，精确SHA/验证/未验范围见[当前事实](../../CURRENT.md)。Root最后提升精确gitlink并验拓扑/治理；CI等待由用户豁免，不等于跳过本地门。模型、真实工具和扣费暂停，正常运行/数据库不切换。知识/记忆/资料库其余mixed、MCP availability整链、全站视觉与聊天项目留待下一轮，不继续扩大。原长期目标尚有这些缺口，不将本轮PR收口写成全产品闭环。

> 日期：2026-09-03  
> 状态：执行中  
> 总目标：以可执行门禁而不是口号，完成 Root 与九个正式运行仓库的架构、契约、SQL、代码、文档、交互和发布闭环。Root 是治理主仓，不计入运行仓。

## 1. 范围与完成定义

正式仓库固定为：

1. `kokoro`：Web 产品界面与同源 HTTP adapter；
2. `kokoro-bff`：公开 Product API、Conversation、Message、Share、Project、ScheduledTask 与 durable AG-UI projection；
3. `kokoro-agent`：Run、checkpoint、lease、tool journal、执行事件、HITL 与 evidence；
4. `kokoro-iam`；
5. `kokoro-system`；
6. `kokoro-billing`；
7. `kokoro-capability`；
8. `kokoro-storage`；
9. `kokoro-scheduler`。

Model 目录与路由事实已收敛到 `kokoro-system` 的 `model-catalog` 模块；旧 `kokoro-model` checkout 仅作历史来源，不是活动运行仓。`kokoro-capability` 是当前物理仓，目标 clean-slate 重命名为 `kokoro-platform`（Skills/MCP），尚未完成仓库 cutover；本计划的当前九仓清单仍用物理名称。

完成必须同时满足：

- 九个运行仓职责、依赖方向、机器契约、SQL owner 和 Redis/PostgreSQL 隔离可由脚本验证；
- Agent 三项 P0、BFF 的真实持久化与 AG-UI 投影、Web 的唯一协议链路均有真实故障恢复测试；
- 每仓代码、Schema、contract、测试、CI、文档在同一提交切片中收敛；
- 主工作区重新执行九个运行仓质量门禁、真实 PostgreSQL/Redis 集成、浏览器交互和候选镜像 smoke；
- 最终报告只引用本轮产生的命令输出和 evidence，不继承历史“100 分”结论。

## 2. 固定架构裁决

```text
Browser
  -> kokoro same-origin adapters
  -> kokoro-bff public Product API
  -> IAM/System(model-catalog)/Billing/Capability/Storage owner APIs
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

- [x] 历史切片：将 `AGENTS.md` 从七仓规则升级；当前规范以九个运行仓为准；
- [ ] 增加代码粒度、React/CSS、文档、公开 API、AG-UI/Vercel 与本地基础设施规则；
- [ ] 将历史七仓静态/全量验证器收敛为九个运行仓验证器（静态审计器已覆盖九仓；隔离全量编排仍待 Wave 0 Task 3）；
- [x] 历史切片：建立文档矩阵和 contract provenance 门禁；当前覆盖与违规由九仓标准审计复核；
- [ ] 更新 `docs/CURRENT.md`、`docs/CODEBASE_MAP.md`、`scripts/INDEX.md`。

### Wave 1：文档与契约事实源

- [ ] 每仓补齐 `INDEX.md`、`docs/INDEX.md`、`docs/CURRENT.md`、`docs/TECHNICAL_DESIGN.md`、`docs/API_CONTRACT.md`、`docs/DATA_MODEL.md`、`docs/SECURITY.md`、`docs/RELIABILITY.md`、`docs/ACCEPTANCE.md`、`docs/SLO.md`、`docs/RUNBOOK.md`；
- [ ] 每个实际拥有机器契约的仓库补齐 `contract/README.md`，写明 owner、visibility、版本、生成命令、breaking policy 和 provenance；
- [ ] 将 BFF 公开 OpenAPI 收敛到 `kokoro-bff/contract/openapi/v1/openapi.yaml`；
- [ ] 为 Agent 自有 ingress/event/control 边界建立本仓机器契约，不复制 Capability、Storage 或 BFF 模型；
- [ ] 对九个运行仓运行文档 lint、链接、契约 lint、breaking 与示例验证。

每个仓库只分配一个写入 Agent；IAM/System（含已收敛的 Model `model-catalog` 工作）/Billing/Capability/Storage/Scheduler 的独立调查可并行，同仓仍只有一个 writer；Web/BFF/Agent 在其 P0 设计定稿后再写。

### Wave 2：Agent 正确性与 Python 业务能力收敛

- [ ] 在 `kokoro-agent/database/schema.sql` 建立唯一 canonical schema；删除 runtime DDL 和 epoch 时间事实；
- [ ] admission 事务原子写入 Run aggregate 与 outbox，再由 dispatcher 投递 Redis，消除“先 claim 后落库”丢 Run 路径；
- [ ] 所有 Run、control、evidence、checkpoint、memory 查询显式携带受信 `tenant_id`；
- [ ] 引入 `generation + owner + lease_token` fencing，旧 worker 不能提交状态；
- [ ] tool journal 先以唯一 effect identity 竞争写入，只有 winner 执行副作用；
- [ ] 保留超大 repository/supervisor 的现有正确行为与测试基线，再按 `runs/`、`execution/`、`approvals/` 等 Python 原生业务能力包拆分；每个手写文件只有一个主要变化原因，只有实际复杂度需要时才增加文件或子包，不默认套四层目录；
- [ ] 接入真实 Capability/Storage clients，移除生产 fixture 与 `NoSkillsClient`；
- [ ] 用真实 PostgreSQL/Redis 覆盖 trim、TTL、worker crash、lease expiry、duplicate delivery、resume 与跨租户测试。

### Wave 3：BFF Product API 与持久化

- [ ] 移除 live composition 中的 `MockBffStore` 和通用 owner proxy；
- [ ] 为 IAM/System（含 `model-catalog`）/Billing/Capability/Storage/Agent/Scheduler 建立显式窄 adapter；
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

- [ ] 运行 Root 九个运行仓结构门禁；
- [ ] 五个 TypeScript 业务 owner 仓（IAM、System、Billing、Capability、Storage）分别运行 `pnpm lint && pnpm typecheck && pnpm test && pnpm build && pnpm db:apply-schema`；
- [ ] BFF/Web 分别运行本仓完整门禁和浏览器 E2E；
- [ ] Agent 运行 Pyright strict、pytest、真实 PostgreSQL/Redis fault/recovery tests；
- [ ] Scheduler 运行 format、vet、test、race、build 与真实 Redis integration；
- [ ] 在全新 database 上安装每仓 schema，检查外键、时间类型、约束命名、tenant predicate 和索引；
- [ ] 构建候选镜像并执行 health/ready/smoke、漏洞扫描、SBOM/provenance/signature 门禁；
- [ ] 生成本轮 evidence 和未完成项清单，按仓提交并记录 commit。

## 4. 提交策略

- Root、九个活动子仓分别使用 `codex/production-closure-*` 分支；既有分支和未提交变更先审计、交接，不机械重建；
- 每个提交只完成一个可独立验证的纵向切片；
- 先固定保留行为的测试基线与已批准的契约断言；按自洽业务切片提交实现、对应测试、契约及必要文档/CI，不按架构层或逐文件机械排序；
- BFF 现有 `docs/api/v1/agui-chat.md` 未提交修改视为协作者工作，不覆盖、不回滚；
- worker 的退出码不作为完成证据，主工作区必须重跑该仓验证。

## 5. 风险控制

- 文档规范先进入审计模式，再逐仓修复；在全仓补齐之前不得把失败门禁误报为回归；
- Agent P0 与 BFF/Web 协议变更禁止并行写同一 contract，先由 owner 提交再更新消费者；
- 共享 PostgreSQL/Redis 由 Root orchestration 复用，执行前探测并禁止重复启动；
- 任何“100 分”“顶级标准”结论都必须附当前 commit、命令、时间和 evidence 路径。

## 6. 独立后续门与当前验收边界

以下门按依赖顺序分别设计、实施、验证，不因本计划改为九仓而标记完成。旧 Wave/Task ID 与尚未闭环的业务、契约及验证任务继续保留。

1. **Root 规范收敛切片（静态已验，运行组合未验）**：按 [`2026-09-15-kokoro-root-governance-convergence.md`](2026-09-15-kokoro-root-governance-convergence.md) 校准当前九仓入口与本任务表；`32a7d5cb` 主工作树执行 Root tests 89 PASS、拓扑 PASS、标准审计九仓 244 既有违规/新增 0。只报告本切片事实，不宣称运行组合通过。
2. **九仓 gitlink 与路径 cutover**：另立拓扑设计和 ADR，明确当前只有 Agent 是 Root gitlink、Web 在 `kokoro/` 独立 checkout；目标 `apps/`、九仓固定 SHA、remote 与部署入口需一次闭环。旧 Model checkout 保留历史；Capability→Platform 由独立仓库切换处理。
3. **隔离全仓编排**：替换仍暂停的 `scripts/verify-ten-repository-full.sh` 和旧 owner-health 入口，使用隔离数据库、缓存前缀与输出目录，在主工作树重跑真实九仓门禁和跨仓 smoke；脚本名称的历史“ten”不代表已验十仓。
4. **逐仓 main 与发布收尾**：在各 owner 所有待保留提交、未提交修改及组合验证交接后，逐仓审查、集成和清理分支，再以固定 commit/镜像 digest/证据推进候选发布；Root 本轮文档更新不执行 checkout、删除分支或发布。
