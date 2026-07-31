# 22. 能力中台 kokoro-hub 与内部通信定案

> 历史实现册。当前 Hub owner/consumer/transport 以 `24-federated-product-platform-architecture.md` 和 Root boundary
> registry 为准：Hub 属于 Platform，只有 Agent 是 runtime consumer，跨仓使用 ConnectRPC/mTLS；本文中的 tRPC、
> Session consumer、Agent 直读 Hub 数据库或旧 commit 绿灯结论均已失效。

状态：正式册（HUB-1/2/3/4 代码已提交；HUB 链经 HUB-CONSIST 收口（hub 9710400/session dfd1280/agent 2e30fe0/gate 560d70c，e2e 全绿）；跨仓运行证据已补齐（ROUND4-EVIDENCE 证据①AGENT-MCP E2E-33 铁证 d4cf07e、证据②WEB-3 浏览器实走）；仅 HUB-4 灰度未做）
收编自：`docs/superpowers/specs/2026-07-11-capability-hub-and-polish.md` §1-§3（该文已转历史入口；§4 web 打磨不属本册）
上级：[20-kokoro-v1-technical-plan](20-kokoro-v1-technical-plan.md)、[21-platform-mainchain-closure](21-platform-mainchain-closure.md)

## 0. 一句话

> skill/MCP 的**管理写面**归 platform 域模块 **kokoro-hub**（注册/上传/审核/版本/启停/配额/运营位）；agent 只留装配热路径直读。内部通信**不换 tRPC**（证据定案），以 contracts 共享包 + 修四个实锤洞达成同等收益。

## 1. kokoro-hub 边界（长期规则）

**落位**：platform workspace 内模块（与 user/credit 平级），复用 platform-kit（envelope/健康检查/启动器/admin manifest）与部署编排/CI；后期若独立拆走，模块边界已备。

**归 hub（TS，管理写面）**：

- skills 上传/GitHub 导入（preview→confirm）、审核状态机、版本历史（Mongo revisions 附表，S3 zip 永存=回滚零成本）。
- per-user/官方启停 API、namespace 配额、运营位（排序/置顶/分类）。
- **MCP server 注册表**（per-namespace，凭据只存 secret-ref 不落明文）。
- 池查询 API：session `pool.ts` 与 agent `hub.list_pool` 双语言双实现的收敛终点，单实现消除漂移。

**留 agent（Python，装配热路径）**：

- resolve_cards/read_body 双路/物化/graph state 账本/GC 自愈/MCP 三恒定工具与懒连接。
- agent 直读 Mongo+S3（hub 写、agent 读，读写分离同库）；**每 run 跨服务 RPC 是可用性耦合，禁止**。

**契约单源**：storage.yaml 生成 pydantic+zod 双镜像；generate.py 第三输出位 `kokoro-hub/src/contract`；校验常量（名称正则/大小/配额）入 spec 数据化，双语言同源。

**双层守门**：hub 写面校验（入库守门）+ agent 装配防御校验并存，不算重复——信任边界各自校验是本仓既有法则。

## 2. 分期状态

| 期 | 内容 | 状态 |
|---|---|---|
| HUB-1 | 脚手架 + skills 读写面迁移（seed 改调 hub）+ 启停/配额 API + storage 镜像输出 | **已落地** |
| HUB-2 | 上传/GitHub 导入 preview→confirm + 版本历史 | **已落地** |
| HUB-3 | MCP 注册表 + admin manifest 接入 | **已落地(8baaf95)** |
| HUB-4 | 审核三态/运营位 已落地(f0f3c62)；灰度(canary)属运营部署动作，未做 | **代码已落地；灰度未做** |

## 3. 内部通信：不换 tRPC（证据定案）

全域切换 tRPC 的实锤反对证据：

1. admin 中台核心机制 = manifest 声明 REST 路由 → 网关白名单代理 + RBAC + 审计 + 审批；tRPC procedure 无法被 manifest 声明式代理，切换=重写整个 admin 网关。
2. per-module OpenAPI 是 Python 侧（agent/litellm）消费的唯一通路。
3. 跨语言边界一律 HTTP+schema，tRPC 只适用于单仓内前端↔BFF——与 web→session→agent 现状同构。

**达成同等收益（类型端到端、减漂移、减通信）的定案**：

- **P-A contracts 共享包**：各模块经 `@kokoro/<mod>` 导出 interfaces schemas，消费方 import 代替手写镜像（实锤漂移案例：credit 的 activeSchema、payment 的 ensureAccountResponseSchema 均为手抄）。编译期即漂移信号，零运行时改动。
- **P-B 修四洞**：①payment→credit 裸 fetch 归队 callService（补 principal/internalSecret/错误信封）；②requestId 头统一为 x-kokoro-request-id 单名；③internal-secret 入站守门件已落（/admin 前缀,env 配置后 401）——**纠偏(2026-07-11)**：这不等于内部信任面闭合，default-internal 全路由策略/per-caller 分级凭据/生产 fail-closed 属 Wave 1 TRUST-ROUTES；**已落地(platform 150aa25/f9802f1/c4b89a1，e2e 凭据强制档绿)**，内部信任面已闭合；④payment↔credit 补 outbox/重试驱动（防 confirmOrder 中途崩溃订单悬挂）。
- **P-C 减通信**：credit 改账热路径 site/user active 双查加短 TTL 缓存；主链 delta 事件读模型压缩记档为独立块。
- tRPC 保留给 kokoro-web 自己的 BFF 层（单仓内）若后续需要——不强推。

## 4. 主链修缮清单（M-1~M-7 代码已提交；M-1 后半「model 可用性收敛 platform 单源」已落地=MODEL-SOURCE，platform 3b4c743）

- M-1 model 允许集三处漂移 + resolveModel undefined 时 hold 缺 modelBindingId 仍放行：enforce 档下无绑定应拒绝；model 可用性收敛 platform 单源，profile.allowed 降级为展示过滤。**已落地（MODEL-SOURCE，platform 3b4c743）**。
- M-2 store→relay 依赖反转（SessionEventDraft 下沉 store 或 contract）。
- M-3 workspace key `{namespace}:{sessionId}` 约定进 contract/spec（原为三处注释级硬编码）。
- M-4 billing client 手写镜像：P-A 落地后 session 消费 contracts 包或加跨仓契约测试。
- M-5 INDEX.md 覆盖补齐：session relay/store/http、agent contract/execution/worker、web core/engine。
- M-6 事件回放 O(N) delta 与 snapshot 双份传输（读模型压缩，独立大块）。**已落地（M6-SNAPSHOT，裁决 B 变体：属主 snapshot 省 messages、/shared 必携；契约 9f33734/session 13b6f6f/web 87f422f/gate a38ac30）**。

## 5. 不做

- 全域 tRPC 化（§3 证据）。
- skills 装配路径跨服务化。
- admin-web 硬编码页面重构（HUB-3 管理面接入时随 manifest 元数据一并解）。
