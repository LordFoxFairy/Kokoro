# Task A 当前进度、问题与 C-1～C-4 闭环技术方案

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 先完成 G0 / C-1～C-4 的认证切换、旧实现删除和真实验证，再进入 A-01/A-02，随后 A-07；保留 A-03～A-16 的完整产品责任，不以清理完成代替 Task A 产品闭环。

**Architecture:** IAM 唯一拥有人类 session、active tenant 与权限；App 同源适配 → BFF Nest feature → owner API/RPC。Nest `AppModule` 是唯一运行时组合根；旧 raw server/runtime、dispatcher 和无边界 aggregate 在消费者迁移后删除。有效的事务、幂等、取消、恢复、lease/outbox 语义必须承接，不机械删除 Repository 或新增空层。

**Tech Stack:** 现有 TypeScript/NestJS/pnpm、PostgreSQL/Redis、owner generated clients、Python Root 治理；各仓 Node/Python/Go 版本以其 manifest/lockfile 为准。

**当前检查点：** G1/T‑05、T‑17、T‑11、T‑15 正式原生旅程及 G3 已验。I‑15 在组合 `6db2028d` 的同一隔离 PG、同一角色下分八 schema，八 owner 同时 readiness 通过并全部回收。已发布契约 15 active／0 declared broken／0 illegal。严格结构审计保留 exit 1（408 FAIL／0 未验证）；相较 388 旧基线，20 项是 IAM 原件同字节消费者副本的重复报告，无新增未处置。Task A 产品项按 A‑01/A‑02、再 A‑07 推进，A‑13 setup 保留、仅真实支付除外。最新证据和待办见[唯一执行清单](../../../todo.md)。

## A‑07 Project Todo：设计门与分工（2026-11-04）

A‑01/A‑02 已在 Root `33cc1485` 交付。沿原 handoff 的完整 A‑07：Project Overview 手动待办，创建、改名、三态切换、删除、owner 排序及刷新；后续使用真实 CRUD 去重登记 A/B 两组任务，不把已清理夹具称实际登记。原 BFF 有单独的项目 Task 表及 GET；Run Todo 仍是执行进度，两者不联动。保留现 Project 权限、GET shape/排序及 id/slug；新增只针对 canonical 项目 ID 的写操作。不使用 AG‑UI、Agent、Scheduler 或新 IAM 机制。

**选择与失败恢复。** 单独加版本列会要求复活非空库演进；直接拿现有毫秒时钟作版本有同毫秒及 ABA 问题。选择有效写入严格推进现任务时间戳、从完整资源投影生成强 revision，零 DDL；现有成功回执表同事务记录不含标题的 ACK。先锁当前 active 父 Project，再判原 key/版本及目标 Task；删除 Project 同锁清理任务，拒绝不再拥有者重放。App 同源同 key 同输入显式重试，明确 412 保草稿并只读刷新，不用新版本自动覆盖。

| 顺序 | 唯一写入面 | 进入／退出证据 |
| --- | --- | --- |
| D0 / BFF 契约 | 主控：BFF 三设计与唯一 OpenAPI，配套契约基线；App 仅设计 | [BFF 技术设计](../../../apps/kokoro-bff/docs/TECHNICAL_DESIGN.md)／[API](../../../apps/kokoro-bff/docs/API_CONTRACT.md)／[数据](../../../apps/kokoro-bff/docs/DATA_MODEL.md)，[App 设计](../../../apps/kokoro-app/docs/TECHNICAL_DESIGN.md)／[同源 API](../../../apps/kokoro-app/docs/API_CONTRACT.md)。定合同再接消费者。 |
| D1 / BFF | Projects 真路由／唯一 task store／父项目删除事务，另一写区做真实 PG 用例 | 现旧行可读写；原 key 一行、异指纹 409；并发同版本唯一胜者、ABA 后旧版本拒绝、错主体／父墓碑不能读写或重放；不跑邻 owner。通过后仅 BFF #18 推精确 SHA。 |
| D2 / App | Project Overview 独立视图、具名 adapter 与固定来源生成；不改 Chat/Run | 独立逻辑可按冻结 D0 开始，生成只使用已交付 BFF Git blob。真原生浏览器项目创建待办→刷新→编辑/三态→第二标签旧版本拒绝且保草稿→删除→刷新。复用既有登录证据，不重跑 A‑01/T‑15。 |
| 集成／登记 | 主控串行原 PR、Root gitlink 和唯一 TODO | 只给已验证且已推子仓精确配对；正式 CRUD 登记前核实际本地 owner／项目及已有项，避免重复。临时资源仅回收自己创建的；不合并、不部署。 |

**原生验收（2026-11-05）。** 冻结 IAM `b6a9745`、BFF `846821ae`、App `85752044`，收据 `2f5123a6b6d7297ba1a0e2cb` 通过，真 PG/Redis 资源回收。保留三处独有浏览器缺陷的失败证据：`454ca7fe6fb4b81f2320065a` 指针被拦；`d4bf6f021c5c70841ad68d81` 核对步骤提前触发 PATCH；`fa3914223b8ba70a6a56f8ab` 真实 DELETE 已 204 但 UI 误当不确定。现明确滚动避让范围、核对取消原生默认动作、DELETE 接收零字节而拒绝正文、在浏览器以受信 204 ACK 判定成功；不改 BFF/IAM 或放宽条件写。正式 A/B 登记独立于此自动回收的夹具。

## A‑03 运行中投递：区分排队、打断和原 Run 补充（2026-11-05）

**先闭环现役 FIFO。** 运行中发送继续经过原 Message POST，进入 owner FIFO；与首发共用原请求记录，只允许一条未确认写，不打断当前 Run。已知 202 按精确原用户消息 ID 对账；丢回执时刷新不自动发，用户显式按原键、原 body 重试。Run 的进度、暂停交互、终态及恢复与提交错误分开。不改 Public 28.20、存储格式、服务鉴权或 owner。

**打断并发送的边界。** BFF Chat owner 先过契约门：在既有 Message POST 加严格可选目标 Run，普通发送的字节和旧摘要保持。按现 Project → Conversation → stream 锁序，已准入 owner 同键回原三 ID；仅新键确认指定 Run 为同会话当前已启动且未终态。新消息、后继 Run 和旧 Run 的现有取消 outbox 同事务；错目标/已被其它命令认领返回冲突且零写，不创建缺失会话，不改数据库。沿原 FIFO 和真实终态放行，接纳不等于取消成功，旧 Run 自然结束不冒称已取消。BFF 先交测试和固定版本，再由 App 正规生成消费者。默认不插队，不引入偏好存储。

**打断后继的原生收据。** IAM `b6a9745`、BFF `2cf1c14`、Agent `18efa2e`、App `35967026`，Chromium 收据 `e7d8150a022eb8ab81adaee4`（SHA‑256 `040bc411540f3fd520c6f33b59f5b0105e2f9550ed85188d37a339792aa77124`）。真 BFF cancel outbox / Agent HTTP / 真 Worker / PG / Redis：后继 admission 先于旧终态但实际派发晚于终态，旧 Run 真实取消，后继完成和刷新回读各保持唯一。首轮 `d7b09df5851331af3f49c06c` 未进入第二 POST，私有两层代理开启既有 SSE 转发后通过。未使用外部模型，隔离资源已回收。自然终态先于晚控制的真 PG/Redis owner 回归保持原终态、无再发布；不等同 Chromium 全链复测。

**发送但不中断的边界。** 不复用普通发送来伪造「已注入」。BFF 同事务保存一条归原 Run 的用户消息和可重放投递，不新建 Run 或助手占位；现 launch/cancel outbox 各 Run 唯一，不塞多条 steer。Agent 复用现控制/信箱，但必须区分接纳、实际在指定 Run 注入和未注入；信箱写失败不冒成功，不终止健康 Run，不自动转排队。待 owner 设计明确定下最小投递记录、原键回执、实际注入证据和存量 schema 变更方式后再实现；不恢复旧校验或临时双 POST。三种路径独立验收，保留原 IME/多行、审批、停止/继续、草稿和阅读位置。

---

## 收口执行规则（2026-11-04）

- **现行契约和职责优先，不继承旧形状。** 以现行用户行为、owner 边界、契约和有效设计裁决为准；旧代码是调查材料，不是设计依据。已批准退役且消费者归零的入口、dispatcher、兼容层和纯转发抽象直接删除，不留 alias、fallback 或无调用壳。仍需保留的生产行为放在现役 owner；若发现真实消费者或有效兼容义务，列出调用方及退出条件，不以“以前这样写”保留。
- **每个风险只在最低充分层级验证一次。** 机械接线和死代码删除只检查现役入口、引用和受影响的编译/定向行为；只有变更实际触及认证、授权、取消或事务边界时，才选对应回归。已有证据按提交、受影响路径和场景核对；只因 SHA 变化、旧脚本存在或测试数量多不加跑。不保留只验证旧目录、旧类名或私有调用顺序的断言；合并或删除前说明独有风险由何处承接。
- **先收口 T‑11，再对冻结组合跑 C‑4。** 先盘点真实消费者和未覆盖的行为差异，复用适用的阶段证据，只补实际缺口；不继续扩写 smoke。C‑4 对最终精确组合做一次约定的正式验收；失败先分环境、业务与证据漂移，修复后定向复跑受影响项，组合变更影响正式结论时才重验对应门。环境失败记为未执行到业务断言，不算代码回归，也不算通过。A‑01/A‑02/A‑07 保持门控；各仓沿自己的 PR，不合并 main、不部署。

## 当前执行摘要（2026-11-04，本地提交）

- **恢复后本地交付**：Root `237be60c` 将最后一个现役旧 workload fixture 切到原生凭据，落盘字节与既有候选一致；主控定向 5 项、Ruff 与 diff 检查通过，当前版本真实存储未跑。IAM `b6a9745` 退役 producer：59 路径与原冻结候选逐字节一致，正式固定基线 breaking 门及正式树 contract/SDK 生成校验通过；clean commit 打包的 0.21.0 经独立核验版本、commit、契约及锁文件摘要，归档 SHA-256 `458da2ba96daa7784f0cd296b92fc0e428232e49119c0ca25485788ffc1dcad9`。`test/consumer/iam-client.consumer.test.ts` 在干净提交上用独立安装、编译及真实 IAM/PG/Redis 通过，隔离资源库存恢复；不冒称发布或 Root 精确配对完成。以 Root `edf8c020`、IAM `b6a9745`、Capability `bf4aa07` 真验 named IAM 的 execution peer，再 dry-run ingress；初次仅私有工具链绑定到旧 IAM 目录导致 fixture 启动失败，切到已冻结的 0.21 工具链后通过，隔离 PG/Redis 和凭据回收均通过。未运行真实 Storage。Capability `749b159` 已本地提交 R336 的唯一现役测试文件，保留原场景并以真实 ACK/PUT 绑定 CAS 和版本；Prettier/ESLint/TypeScript 通过，R336 真实用例未运行。
- **6 小时执行目标（不是完成承诺）**：只指机器 Goal C‑1.3～C‑4。主控负责受管实例恢复后的 T‑11 真实收口、配对和验收；Capability owner 保持原 draft PR13；只读远端核对实际分支为 PR13 `f515e22`、其 base PR12 `2ad5c9e`，与本地 `bf4aa07` 仍分叉。冻结前在隔离区保留两边提交解决实际冲突，不整树择一。对象存储恢复写能力、确认旧空桶回收后，先补存储独有风险和现役接线，再冻结精确组合并执行 C‑4 一次；环境未恢复或定向回归失败即时汇报，不扩大范围。A‑01/A‑02/A‑07 不计入本时窗。

- **BFF 原 PR #18 分支本地提交**：`09f44fe` fix(runtime): bound Nest shutdown and drain AG-UI transports；`50b2f09` fix(mcp): restore projection authorization and request cancellation；`820f5bc` fix(skills): wire public list project and app owners；`329f9a1` test(knowledge): exercise account module with real storage；`170064b` test(bff): migrate billing and projection checks off raw listeners；`8de48c6` test(mcp): include projection admission in default checks；`79d3d10` fix(health): preserve readiness unavailable response；`325e777` fix(skills): return not found for retired reads；`91038f6` 迁移 admission 定向验证；`5a38c39` 删除无消费者的旧 route wrapper；`3ab4357` 修正 Model Admission 总请求头上限；`93336a1` 修正 Scheduler 顶层创建回执前置检查。
- **验证范围**：Skills 的真实 factory 回归 503 已转绿；定向 Skills/相邻用例、T‑17/MCP 定向门、Billing/Platform 测试和 Personal Knowledge 独立真实 PG/Redis 均通过。 `/readyz` 503/HealthResponse 已在真实 HealthModule HTTP 复验。 退役 Skills GET 的 404 与零 owner 转发已定向复验。 T‑17 真进程的正常退出、端口冲突、真实 PG 锁下 30/31 秒期限及回收均有收据。前轮真主进程验证 16 KiB proof 穿过 parser 后得到缺 Run 的 404、超字段返回 400、超总请求头返回 431；受控 Billing HTTP 的合法流程另验 201。重新实测 30.002 秒 HTTP EOF、31.033 秒退出 1。Scheduler R73/R74 的非法/不可见请求零回执、同键重放/撤权、outbox 失败回滚已在独立 PG/Redis 上通过，资源已回收。以上不是完整 C‑4，也不把受控 IAM/Platform 对端当实际跨仓链路。
- **本轮 BFF 本地提交**：`837ecde` 恢复 Mori SSE 路由透传 `Last-Event-ID`，同一 HTTP 测试验证续流不重复、重复字段拒绝且不发给非 SSE 请求；`2643bd5` 接回既有 Agent setup handler，真实 Nest 验证 400/503、受控对端 200 和信任边界；`e54249a` 修复 R237 Project instruction 和嵌套 Scheduler 创建在认领或重放回执前核对 Project 可见性；`b4c9bbb` 将 Account profile/session/Team 写测试迁到真实 Nest 模块，保留原场景与断言。
- **本轮主控验证**：Mori/Agent setup/transport 等相关门通过（受控 HTTP 对端，不是 owner E2E）；R237 和相邻 Scheduler 定向真实 PG/Redis 通过，含合法原 ACK、墓碑后拒重放、不可见零写和行锁复判；隔离资源清理完成。Account 三份真实 Nest HTTP 定向通过（IAM 为受控对端）。未运行本轮全量门，不以阶段通过替代完整验收。
- **Scheduler 任务项**：`c6b8085` 在 PATCH/retry 认领或重放回执前核对当前归属，保留父 Project 墓碑规则。后继 `80c68ac` 收口 DELETE：真实 PG/Redis 旧基线复现错归属写回执；新代码中错主体/租户、缺行和非同 key 均不写，合法原 ACK 精确重放，异指纹 409；回执丢失时只凭同 tenant/task/subject/key 的已提交 outbox 经原事务恢复。outbox 不证明 HTTP 指纹，不覆盖异常历史终态；旧 owner 锁与事务不改。
- **前轮 raw 消费迁移**：BFF `1e25efc` Billing/Model、`cde1232` MCP、`881d4c7` Chat/IAM relay、`c55d82a` Archived Tasks、`071098c` Skills 已迁到实际 owner 模块。原场景按组对照、定向通过；Archived Tasks 原版和候选均用隔离真 PG/Redis 保持原四个场景（含行锁），资源已回收。
- **IAM 消费退出前置**：Capability `6ae34a8` 用 HTTP 边界零调用哨兵取代旧 SDK spy。IAM 退役补丁仍是私有候选：隔离真实 PG/Redis 证明已持久化的旧 client/resource/scope 行在旧版仍可换 token（200），候选拒绝 `400 invalid_scope` 且不签 token；常规 OAuth、native session、独立 E2 的同 token/proof 成员撤销复判通过。测试资源已回收；没有改 IAM 工作树、发行或升级 SDK。
- **前轮 owner 测试迁移**：Projects、Library、Chat/Message、Admission、Agent Control 已按组迁移并复验；移除重复 mock 时保留真实模块的准入、关闭期和 owner 零调用断言。Business Store `aaa3add` 与 Chat/AG‑UI `b499ddb` 移除宽工厂与 raw 接线，隔离 PG/Redis 前后全文件题名一致、零跳过；Message Parts 与上传回执恢复也用真实 PG 验收（上传对端为受控 Storage）。
- **404 契约**：`3f4c595` 把唯一 Express transport 移到 HTTP 层，仅在 Nest 最终未匹配的 `/v1` 请求上输出既有 `bff_route_not_found`，不路由、不做准入或 owner I/O。真实 AppModule 复现旧 Nest 错误形态差异并复验四条文档明确的退役路由、未知 owner/Session 路径、正常 health 和非 Product 404。已匹配 feature、System/Skills 既有 503 与 `/browser/v1` 不纳入此修复。
- **BFF raw 退场（本地）**：`ef64012` 删除旧 bootstrap、dispatcher、宽 Postgres 聚合、旧探针/路由映射和六份 mock 夹具，移除 format 中已删文件输入；原 21 路径候选均已收口。退役 MCP 写和 Chat 依赖故障在真 Nest 验证无 owner 旁路；Project 指令历史和嵌套任务字段在真实 PG/Redis 验证。干净构建无旧产物，声明式格式、lint、267 项受影响检查及 Business Store 整文件 181 项通过，无失败或跳过。Scheduler receipt/dispatch 另用真实资源对照前后通过。未用这些阶段结果替代各仓完整门禁。
- **边界补证**：`9bba83f` 保留最终未匹配的 `/browser/v1` 原 404 形态，不运行准入、权限或 owner；`133b72a` 用真 Nest relay 连接真 IAM owner，sign-in、会话与 sign-out 对照通过。真实 BFF 进程 `8bcdd2e` 恢复 Protobuf BOM/CRLF 字节保真，旧版 502 → 新版 200，plain/拒绝对照不变、两进程退出 0，资源已回收；IAM/Platform 为受控对端，非浏览器组合。
- **BFF Chat 与 Skill Share（本地）**：`38d0200` 删除可选 Chat provider 和不可达分支；现役鉴权、AG‑UI 回放与派发不变。隔离真实 PG/Redis 的 Chat Facts、AG‑UI HTTP、Business Store、Message Parts 通过。首次 Chat Facts 的 5 ms 租约在 SQL 往返内过期；测试改为按 tenant/id/fence 显式推进同一租约过期，原重领、旧 fence、跨租户和结算断言保留并复跑。默认套件另发现 Skill Share 读已删启动文件，`a0a9830` 换成真实 Nest HTTP 验证：假 Origin 403/零 owner 调用，可信 Origin 201/精确分享 URL；整文件通过。精确 BFF `a0a9830` 在保留 Git 历史的隔离 checkout 通过 build/format/lint/typecheck 与默认入口（2409 通过、0 失败、2 个 PostgreSQL 条件跳过，本次未执行这两项）。早期 archive 门另因缺 Git 历史失败；复验没有删断言。
- **Capability 原生 Storage ingress（本地）**：`db98f67` 对应私有 Root runner 实测：真实 IAM 独立 E2 服务凭据预检后，真实 Capability/Storage 用签名 PUT、原 Complete/Finalize 重放和纯 Get，校验缺失、错用途和撤销且产品控制面零 IAM 请求。首次因私有 Storage 源码归档缺编译产物、在 readiness 前失败，确认自有桶为空后回收该桶和单一测试库；构建锁定 Storage 后重试 4/4、无跳过，PG 清单、IAM Redis 命名空间和 Storage 资源恢复。仅验 opt-in `ingress_clean`，本轮未重跑默认 clean/eicar/ack_lost。
- **Sandbox 原生接线实测（阶段）**：真实 IAM/BFF/Capability/Storage 暴露 System 旧兜底抢占 Skills，`POST /v1/skills/drafts` 错回 `503 platform_operation_not_available`；BFF `7c661ad` 按 owner 约束兜底，不调整 Nest 注册顺序。完整 AppModule 回归先失败后通过，保留原 owner 兜底、退役读 404 和零转发。真实复跑六个 default-off 均 `503 skill_dependency_unavailable`、零 Platform 请求；启用后原草稿 201、同键 201 重放、异输入 409、初始 GET 200。
- **包验证与发布（阶段）**：Capability 旧 smoke 在构造 Publish digest 时遗漏 `expectedPublication`，负控未发 RPC。 `85fc3bb` 只修测试请求：首发显式 absent，发布后新 key 使用独立系列 CAS 和 Skill ACK，并断言具名 `publish_state_invalid`。冻结版本真实通过原签名上传、感染/坏 ZIP、恢复、验证和发布/重放，持久化计数与非草稿 GET 412 保持。运行进程、桶、PG/Redis 清单均已恢复。
- **Sandbox 默认全链路（真实私有组合）**：R357 现役 stable-series GetSkill 与个人列表替代旧 BFF GET；旧入口实测终端 404、零转发，直连 Capability 保留身份负控。旧 ZIP 缺 SKILL.md frontmatter 造成 CLEAN 后 Validate 412；当前 fixture 的实际 owner 校验通过，验证和重放都校验 SKILL.md 精确摘要。Public Publish 传显式 publication CAS，与 Skill 版本分别校验；回执、唯一事件、精确库存通过。真 IAM 同 Cookie 登出后九个请求均 401，Platform 连接与请求计数均无增量。资源已回收。默认路径通过不代表 Root runner/精确 pin 落地。
- **Product Installation 可选模式（真实私有组合）**：独立开启 product surface，沿同一活跃 Cookie 对两个真实发布系列跑原安装、重放、列表分页、包正文、移除/重装；包正文与实际上传且通过 Validate 摘要绑定的 SKILL.md 全字节匹配。撤权后原六操作 401，代理 TCP/HTTP 计数均无增量；PG/Redis/桶和进程均回收。
- **Personal Skill Lifecycle 可选模式（真实私有组合）**：使用 BFF `f56caea`、IAM `5436f4f`、Capability `85fc3bb`、Storage `4a99061` 复跑默认、Product 及 Lifecycle：真实版本创建/重放/冲突、精确安装修订、无包新版本、撤回重放与终态拒绝、既有安装的来源撤回可见；验了原库存增量、回执和唯一撤回事件。撤权后两写均在 BFF 准入拒绝，零 Platform 调用。PG/Redis 清单恢复、桶删除、全部自有进程和代理退出。此证据绑定旧 BFF 精确基线，尚未用 `f0107a7` 重跑。
- **撤权传输纠偏（本地）**：真实撤权 package GET 已拒绝，但缺 `x-request-id`；BFF `f56caea` 在准入前挂同请求 ID，不改 401/no-store 或零 owner。旧版现有回归复现空头、定向复验 78 项通过；默认 Sandbox 真跑收口。
- **可选本地登录与 IAM 测试 fixture（本地提交）**：Root `fff4c9d6` 将 MCP-only、Skills+Storage、Admin 可选启动器切到同一个命名原生 host，落盘源码与三次真实 Chromium 隔离诊断所用字节一致，主控重跑定向 75 项通过。IAM `5436f4f` 原命名 host 16 项通过；`9bd7a8c` 仅追加 Agent 的 JWKS/BFF 绑定测试接线，19 项 preflight、类型/格式/lint 和实际 Agent 链通过。退役 producer 的旧四项真实证据覆盖旧行拒绝、默认 OIDC、既有原生 Cookie/direct 凭据、E2 撤权；不含后继同租户三用途和 Agent 组合。退役与 Agent patch 可独立组合且静态检查通过，退役未提交。
- **MCP 浏览器准入（BFF 本地提交 `f0107a7`）**：真实 App 将匿名 MCP 请求的 BFF 非契约错误体转换成 502。改用现有错误 envelope；真 Nest 先红后绿，保留无 Cookie 和无效 Cookie 的 401、请求相关性、no-store 与拒绝时零 Platform 调用。定向回归、build/lint 通过；真实 Chromium 的 MCP-only 复跑从匿名 401 进入原生表单登录 303，再到同源认证 MCP 200。Skills+Storage 与 Admin 分别通过：Skills 读取当前本人列表 200/空页/无下一页，Admin 进入管理入口并读本人身份。Skills 两次私有探针先因旧查询字段、再因旧响应字段失败，按 App 现役契约修正后复跑，未改产品代码。三种模式的 launcher 均退出 0，自有资源已回收。仅为隔离精确候选诊断，正式源码门仍拒绝旧 gitlink；没有把测试时退出的进程当常驻可测环境。
- **组合边界**：BFF 本地 `f0107a7`、Capability 本地 `bf4aa07`（继 `85fc3bb` 后只改工作流）、IAM 本地 `9bd7a8c`、Agent 候选 `47ca431`。Root gitlinks 未变，私有运行按实际完整 SHA 和文件摘要核验，没有放宽正式门。正式拓扑和契约兼容仍红，C‑4 全量门未运行；未推送、未 merge main、未部署。
- **Agent 与唯一 Root runner（真实私有组合／本地提交）**：原 runner 用同一个原生 Cookie 发一次 BFF Message；真实 Agent pending 与 BFF outbox 精确 `admitted` 后才认领租约。真实 IAM/BFF/Agent/Capability/Storage 与 PG、Redis、S3 验过 SKILL.md 原始字节、原生元数据、只读、安装禁用/恢复、旧租约拒绝、成员撤权，三条 setup 回执且最终库存一致。首次私有归档缺 Prisma client、Mac 临时路径过长，均在业务前失败并回收；补正规生成物及短临时目录后通过。Root `d6ffb89c` 收口原入口，删已无消费的旧 READY/OAuth 凭据工厂。最终提交同字节私有复跑默认、Product、Lifecycle 通过，保留重装精确身份、完整重放和撤权零转发；PG、Redis、桶及进程已回收。Agent 也以最终提交同字节和 IAM `9bd7a8c` 精确本地候选复跑通过；原发布门仍须在正式 gitlink 组合下验证。主控在正式树重跑相关 505 项，零跳过。
- **当前 ingress 验证（真实失败，候选未提交）**：Root `c03be384`／IAM `9bd7a8c`／BFF `f0107a7`／Capability `85fc3bb`／Storage `4a99061` 的私有组合通过原生 peer 预检与 dry-run；真实 Capability 建隔离库遇本机 `ENOSPC`，四个业务断言未执行。IAM 正常退出、自有数据库已精确回收，Capability 未建成的库不存在；Storage manifest 确认进程停且零 socket，空测试桶仍因对象存储 `SlowDownWrite` 保留。候选已补显式 owner env 文件参数，定向与 ingress/default 两个 CLI dry-run 通过；默认 clean/eicar/ack_lost 本轮未真跑。
- **Capability／IAM 后继**：Capability `ef2d919` 本地提交候选镜像的原生 IAM execution 文件及独立 Storage 凭据接线，真实配置加载旧红新绿，不改触发、健康探测或发布步骤；未运行 CI 或部署，runner 实际凭据仍待配置。R336 单文件私有候选已静态验，真实回归未跑。IAM 退役 `0.21.0` 私有候选正规生成，旧产物保持不变；相邻版本只删除旧 introspection POST 及专用 Basic scheme，保留 37 项。五个受影响的集成文件已用真实隔离 PG/Redis 完整通过（144 项，无跳过），资源清单一致；恢复轮在同一冻结候选用正式 `pnpm contract:breaking` 对固定基线通过（exit 0，保留历史告警），相邻版本仍只有经批准的 introspection 删除。未提交退役、未打包发布；以上是此前私有候选状态；当前 Root 原生接线和 IAM 退役均已本地提交，安装与最终组合验收另列。
- **工作流与消费者补证**：Capability `bf4aa07` 在 CI 与 release verify 同步替换旧 global bearer 输入，改为 owner 文件路径与精确凭据 ID。实际 smoke 在请求前复现旧红新绿并通过权限、身份、用途负控；未运行真实 CI，runner 变量仍须由 owner 配对。现有消费者 pin 未改：BFF 0.20 契约/生成及策略、Capability 0.18 SDK/E2、Billing 0.17 SDK/授权各自定向通过。BFF `f0107a7` 的原 Nest relay 用真实 IAM 0.21 私有候选复验登录、会话状态和登出，PG/Redis 清单与 owner 凭据均清理；不是新 SDK 已安装或发布。
- **Project 原生门与旧手工入口退役**：Root `eee26f5a` 加入原生写入、PG owner 和撤权零写，`ba4668ea` 在同一 minimal 模式加入跨身份列表/直读隔离、IAM 停机 503 与原事实不变，退役历史 BFF session Bearer CLI（明确非零并指向现入口），保留共享 NDJSON、ready、源码核验、合法 OAuth 和 Admin 仍使用的 helper。新增 runner 同字节在 BFF `f0107a7`、IAM `9bd7a8c` 的真实 HTTP/PG/Redis 通过，资源已回收；未重跑正式 App/Chromium。Root `ba0f5d90` 让纯 observer 测试独立于 Agent venv；受影响的 502 项 Python 3.13 测试通过，无跳过。Admin 旧手工入口未改，也不作当前原生验收。
- **恢复与 T‑11 收据**：原 Docker Desktop 优雅停止超时后使用官方强制停止并启动，保留原 Docker 镜像、MinIO 容器及 `/data` 卷；在已登记的空桶中实际版本化 PUT、读回、精确删除，再删桶并确认 404。复用原 ClamAV，未清卷、重建或创建常驻服务。Root `eadf960d`／IAM `b6a9745`／BFF `f0107a7`／Capability `749b159`／Storage `4a99061` 的真实 `ingress_clean` 原四例、默认 `eicar` 与 `ack_lost`、R336 单场景通过；PG/Redis、对象版本、桶、进程及凭据回收通过。未另跑重叠的默认 `clean`。后续只在最终组合补 PR12 新的 Schema、MCP 和确有差异的业务，不重跑这些相同正控。
- **C‑4 正在执行**：主控按仓串行验收；IAM `b6a9745` 正式 `pnpm verify` 和真实全量集成均 exit 0，停写及 PG/Redis 清单一致；安装包独立消费另已有同 SHA 证据。Capability `1b5116c` 在隔离 worktree 保留 Task A `749b159` 与原 PR12 `2ad5c9e` 两个父提交；合成 provenance 先失败后用现有唯一三源码索引修复，两具名检查通过且生成前后摘要相同。Capability 首次全量中格式、lint、正式合同/Schema/typecheck 均通过；默认测试 4 个 `spawnSync` 超时。限并发同输入补验 3 个原负控通过，唯一仍超时的正控与正式 `contract:check` 重复，隔离诊断验证该进程 15.165 秒通过（非验收）。`6e6ba9b` 删除仅在临时树重复同一 checker 的正控（现役 `contract:check` 承接），保原负控与 15 秒限制；三条 R345 进一步锁定实际 `feature publication` / `complete HTTP inverse` 诊断。按 Vitest 2 的进程上限重跑正式 gate，再跑受影响的真实 Schema 与 MCP。Agent 原 PR46 最新 `cfd1fcc` 与本地 `47ca431` 已隔离整合为 `33545a4`，保留两侧。`6e6ba9b` 正式 `verify`/build exit 0；条件资源用例不记作默认通过。独立真 PG 的 Schema installer、MCP private/personal、Custom API 四文件通过；项目发布测试旧 fixture 缺新 `currentConnectorId`，15 例在造数前失败。`5e607fd` 仅补该 fixture 的指针后原 15 例全过，另补原 opt-in 真实 SSE 单场景及 fresh schema；每批资源清单恢复。已将本地原 PR13 分支快进至该 SHA，未推送。Agent `33545a4` 格式、lint、pyright、契约和构建通过；默认首跑其余用例通过、JWKS 全组因 `/private/tmp` 祖先可写而失败。移动同 SHA 到权限合格的 worktree 后，仅复验 JWKS 文件通过（77 项），未放宽权限门。真实全组首跑失败；下列定向证据不替代全组合。BFF/App 终态兼容和 Root 精确组合仍待，未更新 Root gitlinks。

- **C‑4 精确组合发现的真实不兼容（T‑09，OPEN）**：原 Agent PR46 新 8.11 终态 `context_window_exceeded` 为非重试；合成 `33545a4` 后真实 Agent 已可能发出该枚举。主控用现 BFF `f0107a7` 实测当前生成解析器返回 `null`，正常投影会拒绝该事件；BFF domain/public OpenAPI/PG 约束与 App 现用生成 tuple 同样只接受旧集合。不是可忽略的可选请求字段或纯 pin 漂移。组合冻结前由 owner 正规配对 Agent 发布原件 → BFF 生成消费与同一 canonical 约束/公开契约 → App 固定产物和非重试展示，并用一个聚焦终态链证明传输、持久与展示；不靠旧别名、吞错或额外生成第二份事实源。未改 BFF/App，独立 owner 门继续；原 PR46 不覆盖其远端新增提交。

- **Agent C‑4 定向纠偏**：补真实 PG/独占空 Redis 前置，原 HTTP acceptance、Run Display 和 Platform transport 68 项通过；真实归档 5 项和 Docker→S3 单例通过，独占桶、容器及 PG/Redis 清单复位。Docker 测试只清本轮已确认创建的精确桶与对象（`0fc0b42`）；初次全组遗留的 25 个流按实际测试前缀、事件时间、前置空库和精确键逐项回收，无清库。`af1188e` 仅让两个故障注入满足 canonical CHECK，保持 reader 拒绝和 terminal 回滚，两个具名用例通过。原剩余三项在合成与原 PR46 `cfd1fcc` 第一父同条件真实 PG 均失败。`494a278` 仅将 R35 共用夹具对齐现 builder 的第四参数；原 `bridge_r35` 组真实 PG 18 项通过，保留重复投递、健康心跳和拒入负控。`bb47ae8` 将旧终态读取测试固定为 `b80d683` 已审历史配方，保留真 PG、同 Run、原正文、只读/字节预算、坏格式拒绝及显式终态优先的原断言，原单例通过。现役 factory 的真实 v3/SSE 诊断在无上下文和合成上下文两例都产出正常答复，但即使在私有诊断临时接纳其摘要，历史 checkpoint 形状校验仍拒绝（无 `__pregel_tasks` 通道）；新 Run 走已有的显式终态绑定，不扩大历史读门、不改生产、不跳过原测试。两批定向 PG/Redis 均已回收。最终门先发现先前 Docker 测试的 S3 错误元数据为可选字段；`40effb2` 只改为类型安全读取，仍严格要求桶前后均为 404，完整 Pyright 通过。主控在 `40effb2` 停写树跑正式格式、lint、类型、合同、默认测试及 wheel/sdist，均 exit 0。真实集成/acceptance 首轮 908 通过，只有 26 个 Display 因一次性数据库命名不符合专用隔离守卫而未执行；同 SHA 改用专用独立库仅补该文件，26 项全通过（无跳过）。真实 HTTP/Redis、PG 与 Docker→MinIO 都有最终候选证据，PG、Redis、Docker 和 S3 清单恢复；仅按已确认键回收本轮 Redis 遗留，不清库。本地 `codex/task-a-c1-agent` 候选已快进至该提交，未推送或改 Root gitlink；跨仓组合另验。

- **Root C‑4 独立验证**：Root `8c71a7c4` 以锁定 pytest 跑 `scripts/tests`，exit 0（2129 通过、4 跳过）；`verify-repository-topology.py` exit 1，只有 BFF、Agent、IAM、Capability 当前 checkout 与旧 gitlinks 不同。结构审计 exit 1；`9a55df34` 按已批准的 BFF Node 24 对齐 profile 和前台启动器，消除 7 条 Node 22 误报，未放松源码门。受影响的 launcher/native runner 及治理测试文件均通过。更正后审计仍报 381 项、2 个工具链未验证；对旧 gitlink 精确快照用同审计规则比较静态项：349 项原样、BFF 两个旧 bootstrap 超长项消失，唯一新增是 Capability `mcp.ports.ts` 超 800 行（原 PR12 已 802，整合后 805），不归为本次新建的抽象或 Schema 故障。31 项有效 TS 配置告警未进入静态差分。独立核实 BFF `message-parts-read` 告警是现役历史数据有界恢复，不是遗留生产入口；公开 YAML 的解析告警在旧、新 BFF 同一 Git blob 复现，不能当契约损坏。审计保留 FAIL，不批量修改历史问题、不将差分冒充最终组合通过。
- **T‑15 启动前置**：`9a55df34` 让唯一前台 fixture 复用正式 native runner 版本：IAM/BFF 24.20.0，App/Admin 22.23.4；真实版本门及定向 RED→GREEN 通过，尚未启动服务。当前默认 HTTP/`--chat` 仍用已无 App 路由的 OAuth 探针，也未接 native 服务用途文件；不能当原生同步环境。最终配对后先用原正式浏览器 runner 验收并回收；需要共享前台时，只选现有 native MCP-only 或 Skills+Storage（Admin 显式）模式、按实际支持旅程交接，不占日常入口、不混 Chat/Billing，不宣称同库应用拓扑已验收。仍待最终 Git 配对及真实启动。

- **BFF C‑4 基线补验**：在独立构建区用 Node 24.20.0 / pnpm 11.25.0 对 `f0107a7` 跑正式门。lint、typecheck、合同生成/静态/语义和 build 通过；正式 `check` exit 1，合同套件唯一失败是启动器 `umask 077` 将试图制造的 0644 负控文件变成 0600。用正确的权限条件仅复跑原具名负控通过；没有改权限规则或测试。随后正式 `pnpm test` 通过，2 个 PG 条件用例未运行；仅在 `45a2989` 的自有隔离库补这两项，证实 fresh 安装/回滚和 Project tombstone/index，资源清单恢复。另 `format:check` 原只有 `mcp-personal.ts` 一处换行，原 PR18 本地 `45a2989` 按原格式器修正，TypeScript 规范化语法与注释逐字相同，完整格式清单通过。BFF/App 新终态候选及最终真实组合尚未运行。
- **T‑11 后 C‑4 前置验证**：BFF `32357c0` 独立干净 checkout、Node 24.20.0/pnpm 11.25.0、`umask 022`、不注入真实资源，正式 `pnpm test` exit 0；两条 PG 条件测试未执行，不以早期同 Schema 证据冒称本次通过。BFF 合同、canonical SQL 与生成物对 `45a2989` 原字节不变；Agent 8.11 原件/来源摘要及 BFF Public28.18 与 App 唯一快照重新核对。
- **Root 精确组合前置红项**：在 `e42fccb9` 实测拓扑，仅 BFF/Agent/IAM/Capability 四个 checkout 与旧 gitlinks 不符。结构审计 exit 1，381 违规与 Billing/System 两个未验证工具链同 Node 对齐基线逐条无新增；不降格门禁。合同兼容 CLI exit 1：13 条声明破损边、284 条 evidence gitlink 和 16 条 owner gitlink 差额，未看到其它错误类别；IAM relay CLI 当前先拒 IAM gitlink，既有 Root 校验器固定 2.1.0，而现役 BFF policy 为 3.0.0。最终固定后必须按实际 commit blobs 复核 evidence/provenance，不机械换 SHA、不冒称已绿。正式浏览器与原生前台均未启动。
- **C‑4 独立来源与工具链补证**：现 BFF `32357c0`、App `197f1102` 的各自 relay 生成检查 exit 0；以 commit blob 核 v3.0 固定来源和祖先关系、IAM allowlist/Better Auth/错误常量同字节、五条认证及三条 invitation。IAM `b6a9745` 相对原 0.20 只有版本和退役内省及其 Basic scheme 差额；不等于旧 2.1 Root CLI 或现运行环境通过。inventory 的历史 blob 全部可校验，但对当前候选有 18 个不同路径不存在，含两条 Scheduler 边共用的旧 vendor。现 Scheduler `cfb2502`、原 owner anchor 与 BFF 当前 vendor 同字节，BFF 正式 Scheduler 合同门通过；最终按真实证据重取，不机械改旧清单。独立 Billing/System checkout 复用锁中相同完整性摘要的 TypeScript 6.0.3 执行原有效配置规则；两个未验证项有了实证：System 此组无违规，Billing 七项原配置差额。未安装依赖、改两仓或把原 aggregate 审计冒称通过。

- **T‑11 G0 全量处置复核**：按 G0 [原清单 §10.5](../specs/2026-10-30-task-a-cleanup-inventory.md) 对 BFF `45a2989` 的 23 项逐项核对：15 项保留具名边界、1 项旧 BffBusinessStore 已删除、4 项并入余差、3 项部分拆分。旧运行入口、全局 locator 和旧 IAM producer 的移除证据不变；旧 import 归零不代表每项按原 disposition 履约。未见后继有效裁决豁免这些处置。
  - **并入首批（三项）**：`stable-id-generator`、`project-execution-binding-reader`、`submitted-agent-run-reader` 仅移动接口。按原 G0 删除独立接口和纯转发：StableId 沿唯一现役算法，保相同 SHA-256 输入、前缀与截断；两个 reader 沿现 AgentRuns 注入、原 Pool/SQL、当前授权与历史恢复各自的语义。主控已在精确 `45a2989` 真 PG/独占 Redis 补 **R146**（绑定授权、撤权及取消）、**R189**（Chat 原 ID 重放、冲突零写）、**Submitted Run**（历史恢复及越界拒绝）、**ScheduledTask outbox**（事务、租约与重启同 ID）四条基线，全部通过无跳过；资源清单恢复。这是归并前行为基线，不是新 provider 验收。此段记归并前基线。新 Goal 下 StableId `f7d1e69` 已完成本地归并：源码 lint、构建、相关定向门及 R189/ScheduledTask outbox/固定时钟真库回归通过，资源清单复位；两个 reader 已在 `76f2d04` 归并：新 Nest 工厂使用原 Pool，SQL、取消和 API 保持；生产注入图、真实 R146/R148/Submitted Run 均通过，资源清单恢复。
  - **其余一项并入**：`335dbe3` 从既有唯一 PG 实现推导类型，删除重复接口，Account token 与实现方法体不变。真实 R257 读写、并发 CAS、COMMIT 结果未知和锁等待取消通过，资源清单恢复。
  - **三项部分拆分**：Chat 已分公开 Share 和 AG‑UI，但 RunDisplay 仍借宽 Chat 依赖；Projects 有具名 Skill 选择入口但底层仍绑整套 ProjectService，MCP 同样持有全量服务；ScheduledTask 已有独立 read/outbox/receipt，callback 仍借 mutation service 读 `findRecord`。按消费者真实需要分别收窄，不拆数据库池或事务，不扩新功能。其余四项与首批不同写区，未授权实施；完成前 T‑11 处置和 C‑4 最终组合继续 OPEN。

- **ScheduledTask 已完成本地拆分 `368e65e`**：旧宽接口及公开 repo token 删除；读取 snapshots、用户 mutation 和 callback lookup 各接自己的窄能力，outbox 与 receipt 保持现边界，沿同一 PG 实例。删仅测试调用的旧 list SQL，原跨 tenant/owner 负控改走生产 snapshots；在线 SQL、事务、调用顺序和 HTTP 契约未改。构建、lint、目标文件格式、Nest/HTTP 相关定向门通过；真实权威读取、DELETE 回执、callback cadence revision、终态通过。outbox 首轮合并夹具运行受共享测试库的全局 claim 干扰，保留失败记录；单独空库只补该例通过，无跳过，资源清单恢复。最终 C‑4 不把上述阶段证据当冻结组合通过。
- **Chat / RunDisplay 子切片已本地提交 `c005e27`**：真实 Nest 图先因缺窄读取 provider 失败，接线后通过。Chat owner finder 和 AgentRuns 终态读取复用原 Pool；删 Chat 终态转发，不改 SQL、准入复判顺序、绝对期限或响应。构建、lint、相关文件格式、定向 Nest/HTTP 与取消回归通过；隔离 PG exact final 场景明确执行并通过（复用 Redis 资源并校验清单），其他 parts 场景按范围排除。该提交只完成 RunDisplay，未推送。
- **AG‑UI process/head 子切片已本地提交 `2ef307e`**：新窄 provider 的真实 Nest 装配先红后绿。原 process RR/权限及 SQL 保持；Chat snapshot 用原 client 同时读 Message、Delivery、process/head 和 watermark；AgentRuns 不再注入宽 Chat，移除不可达的旧控制转发。构建、lint、变更文件格式、定向 HTTP/装配通过；隔离真实 PG/Redis 的 R124 快照及分页、R57 ACK 与拒绝、R237 的 process 底层授权通过，资源清单恢复。该提交不含 Chat 本地宽聚合。
- **Chat 拆分本地完成 `fb3cfa4`**：去掉旧 Repository、Service、token 和无消费的转发；Chat 私有读写只共用原 PG store，Archive、Shared list、Feedback、Move 各接原有实现。新装配先红后绿；构建、lint、相关格式、定向 HTTP/映射通过。隔离真 PG/Redis 的 SET47 归档、SET21 私有 Share、R146/R237 Move、R43 SSE、R124 RR 快照通过；独占空 PG 的 Feedback 四场景通过。初次定向有两个迁接线夹具失败（缺拒绝 finder、在收尾后检查 signal），只修夹具后通过。原 SQL、Move scope/hash、同一 RR 与公开契约不变；资源清单恢复，未推送。
- **Projects lookup、Pin、Task 子切片**：`d0724ec` 将查归属的消费者接到唯一单方法 lookup，原 tenant、owner、未删除和 ID/slug 查询原样；装配、HTTP、隔离真 PG/Redis 的 R237、R73、R189 通过。`a6ce80e` 让 Pin 和 Project Task 分别绑定现有实现，保 Pin 事务及 Task 两段 owner fence；定向装配、HTTP、真实 PG Pin 分页/同键无副作用/删除竞争、R237 Task 的 ID/slug 精确读取、隐藏父级和读中墓碑通过。原静态断言仍锁旧 tasks 调用名，替换为实际装配和真实路由证据。两批资源清单恢复，均未推送。
- **Projects 拆分本地完成**：`c781a8f` 让 Recommendations 与 Skill Selection 脱离宽服务，原 CAS、绝对期限、Skill 回执与 Project 行锁保持；真实 PG CAS、取消、Skill 重放/回滚与锁中墓碑、定向 MCP/Skill HTTP 通过。`32357c0` 删除旧宽接口、Service 和 token；具名 Project 读写、Rename、Delete/Status，Resource/Installation 共用单方法 lookup。构建、lint、格式、装配、定向 HTTP 与真 PG/Redis 的 R237/R241/R279/R280/R73/R278 通过。首轮 R278 因测试仍依赖 Scheduled 传递挂载 Project 路由而 404；仅给该双 owner 夹具显式接回 ProjectsModule，保原断言复验通过。隔离资源恢复，契约/Schema 不变，未推送。
- **T‑11 本地关闭**：四项归并、三项拆分及旧生产入口退役已验；C‑4 的 T‑09、各仓最终门、精确 gitlinks、正式端到端和同步环境未关闭。

- **原 PR 与组合交付前置（只读核验）**：GitHub PR 与远端 refs 均核对：Root #66、BFF #18、App #50、Agent #46、IAM #6、Capability #13 仍为各自 OPEN draft，原 PR head 均在当前候选历史内；Cap #13 的 base 保持原 PR #12（`2ad5c9e`），不改成直接指 main。Agent 本地候选分支名不同于原 PR #46 远端 head：后者实际为 `codex/agent-run-lifecycle`（`cfd1fccc`），不得把本地名当远端推送目标或新开 PR。未推送、未改跟踪关系；交付前按各仓实际 head/base 再做非递归核验。
- **固定产物顺序（无依赖环）**：Agent `40effb2` 反向固定的 BFF internal v1.3.0 与现 BFF 同字节；T‑09 只配对 BFF public failure，不需要先升级 Agent 的 BFF internal 产物。各独立 owner 可本地冻结；按 T‑11 → Agent 原件 → BFF public/domain/SQL → App 唯一 public 快照推进。App 有 12 个现有生成/校验入口固定同一快照摘要，使用原入口同步，不建第二份快照。各仓通过验收并在自己的原 PR 可达后，Root 才更新精确 gitlinks、验正式组合；不先钉已知不兼容中间态。

### T‑09 精确终态配对：最小方案（已确认）

- **事实与边界**：BFF `f0107a7` 原解析器对 Agent 8.11 新终态返回 `null`；App `197f1102` 实测拒绝新 tuple、仍接受旧 `token_budget_exceeded`。保留原 PR46 两侧提交，不用旧 Agent 临时遮住不兼容，也不把新码降格为旧码。Agent 是终态事实 owner，BFF 是消息/公开投影 owner，App 是生成契约的消费者。只承接 `context_window_exceeded` / `retryable: false`，不接入 `personal_context` 或任何 A 功能。
- **写区与顺序**：Agent PR46 工程门通过后固定现有 OpenAPI 与 provenance；BFF PR18 用原生成器固定该原件，既有 domain/公开失败 tuple 与唯一 `database/schema.sql` 保同一闭集。用原 `db:apply-schema` 在本轮隔离空 schema 验证，不改正常非空库、不恢复旧迁移 CLI。App PR50 只从已提交 BFF 公开 YAML 原样更新唯一快照和现有生成器，补独立非重试文案，不新增 SDK、alias、fallback 或第二个契约。
- **已验证的生成器差额**：已固定 Agent `40effb2` 原样 OpenAPI/provenance，HTTP SHA `ad34ba2c…` 与生成 Failure 模型来源一致；8.11→8.10 仅逆版本、新失败码、可选 `personal_context`、`POST /v1/runs` 的 1 MiB body 上限标记，可恢复原 8.10 字节；可重试闭集不变。私有目录用原 Hey API 配置/版本真实生成：现 BFF Custom API 的 Zod 改写会吃掉后续 `personal_context`。应收窄既有改写而非损坏 owner 生成物；当前 Scheduled saved projector 实测拒绝带该字段的输入，而新 owner schema 会接受并保留它。需显式保持 BFF 的原拒绝与出站字段，不接 A 功能、不调现请求限额。未改 BFF/App 合同或生产接线。
- **持久化负控已实测**：在 BFF `32357c0` 的私有副本给原 `test/agui-projection.integration.mjs` 失败参数表仅追加新 tuple，以 Node 24 编译后定向跑单例。真实隔离 PG/Redis 的现行投影提交报 `23514 / ck_bff_message_agent_failure`，测试退出 1（1 失败、0 跳过）；PG/Redis 库存恢复，主工作树 BFF 干净。该输入已归一化，证据不覆盖 raw wire、回放成功或正式跨仓端到端。
- **真实 owner HTTP 回放与旧消费者对照**：以 Agent `40effb2` 私有副本的原 HTTP acceptance 为骨架，只将一条诊断用例改用 `PersonalContextWindowExceeded`。首次因私有源码未绑定 editable distribution，在业务断言前失败；离线安装匹配的 editable 后，同一用例在隔离 PG/Redis 上通过，真实 HTTP 返回、持久终态与 Redis wire 保持精确 tuple，资源清单恢复。该 fixture 注入 typed error，未走 Worker 自然触发。将真实 HTTP 回放页交给 BFF `32357c0` 已构建解析器：外层 page 和前一状态事件合法，`mapAgentEvent` 拒绝新终态；同页只换旧 `token_budget_exceeded` 的对照映射通过。未改任一 owner 生产源码。
- **Agent 真实 Worker 补证**：在 `40effb2` 私有源码仅挂诊断，直连原 acceptance HTTP server 提交合成超窗输入并返回 202。真实 Redis `RunSupervisor.serve` 读取同一 PG pending 和执行身份，经真实 `AgentFactory.build` 自然触发，未注入异常。PG 回放、Redis 终态及 HTTP 200 回放均只有一个 `context_window_exceeded / retryable: false`，无未 ACK 请求，模型供应商/资金授权零调用，公开回放不泄露材料。定向 1 通过；服务与隔离 PG/Redis 清单恢复。仅 Agent owner 诊断，不经 BFF、不开通产品 `personal_context`，不代替正式跨仓。
- **Root relay 精确前置复现**：私有 Root 以已提交 HEAD/index gitlinks 绑定干净 IAM `b6a9745` 和 BFF `32357c0`。未改原校验器，`verify-iam-relay-policy.py --root <isolated-root>` 实际 exit 1，具体为真实 3.0 policy TS literal 解析，不是 gitlink 差额。IAM 0.21 的 allowlist/snapshot 摘要相同，重绑发布来源会改 `iamOwnerCommit`、`iamOpenapiVersion`、`iamOpenapiSha256`；实测 App `197f1102` 接收原快照、拒绝只变三项的候选。本轮只改 Root 校验器：保留旧 2.1 严格检查；3.0 分别证明 IAM/BFF 发布锚、当前精确 pin、唯一已批准退役差额，另校验 BFF 路由/传输矩阵与 App 生成器锁、vendor 和生成物。私有 Root 精确锁定真实 IAM `b6a9745`、BFF `32357c0`、App `197f1102` 后 CLI exit 0；正式工作树旧 gitlink 仍 exit 1。定向 42 项通过，包含保留合同漂移、非祖先、传输和 App 生成漂移负控。未改 owner 产物或降低门禁。
- **Root 合同清单预检**：以私有 `GIT_INDEX_FILE` 绑定当前实际各 owner checkout，按 Git blob 重取清单，不把不兼容旧 consumer artifact 标成当前 owner。原 `w1e-iam07-bff-pin` checkpoint exit 0；兼容性 CLI exit 1，仅 13 条既定 broken，3 active、0 illegal、无其余来源错误。原 Scheduler 测试对私有 3.0 清单因硬钉历史 1.0 先红；改断言三条 Scheduler 边统一使用同一具名 owner 合同，历史清单与 3.0 候选通过；实际 commit/digest/version 仍由原 CLI 校验。治理补丁已在 Root 本地提交 `3a02058a`，兼容性与 checkpoint 两套实际 93 项通过。未改正式清单、历史 checkpoint 或 gitlinks；最终 BFF/App 替换后重取相关证据，保留仍未验的运行时差额。
- **独立来源差额**：当前 Storage `4a99061` 与 Capability v3 vendor 原件同字节；BFF 与 Agent v3 vendor 同为较早原件。比较 Git blob 去注释后的 proto 内容，差异仅 Storage 新增 `UPLOAD_PURPOSE_CONNECTOR_ICON = 5`，并非另一套 RPC。该静态证据不提升历史 broken 边，也不替代当前业务操作 smoke。
- **正式候选与 owner 交付**：BFF `d166a51` 和 App `e726cd61` 已推各自原 PR。BFF 格式与完整 `check` 通过，两个默认 PG skip 已分开真库补齐；新终态在真实 PG/Redis 的持久、快照、回放和资源回收通过。App 从已提交的唯一 Public 28.19 同字节生成，完整 `pnpm check` 通过；保留正文、不显示重发。IAM/Capability/Agent 原 PR head 已与已验候选精确配对。
- **已确认验收顺序**：只接入新终态、不启用 `personal_context`、保持原路由与 PR。BFF 已修正，再复用原用例验证持久/回放/快照，由 App 现役入口验证同一公开 tuple 与非重试提示。只在适当层级保留非法 `retryable: true` 的拒绝证据。按 owner 串行验收后才能冻结 Root gitlinks，继续原 PR，不推未验组合，不 merge main、不部署。

## 历史执行摘要（2026-11-03，G1已验；开始 T-17）

- **目标/状态**：原C-1.3～C-4完整目标保留，认证D0通过；IAM唯一Session权威、BFF入口认证、内部服务身份及owner业务授权分离。普通内部业务不携浏览器Cookie、登录Session引用或伪OAuth claims。账号会话生命周期的明确认证例外见§3.6。
- **已交付**：IAM `1fc3875952a9840aa1a8d15124b9be0eaf91c5f2` / PR6、BFF `8cb6169cf1d15d54c3a3bacad9ea622695642228` / PR18、App `197f110294e9b373d5c4aa0836b3d80f48e3a833` / PR50，Admin `95c504d1bfdcf1038ebadb85d8493c18828b51f7` / PR5不变；四仓在G1验收时源码clean，远端原PR head已精确核对；当前T17测试候选不提前pin。Root4e603743已精确配对并完成原正式五旅程；inspection真实生产/消费及组合负控现已通过，G1按当前冻结组合收口。internal/SDK0.20与BFF状态1.0/relay3.0正式产物字节保持，不新建SDK/flag/fallback。
- **历史I45主方验证（非当前owner HEAD）**：IAM9ea5b4c交付源码完整verify126文件/1690PASS、全部真实integration48文件/482PASS/0SKIP；537输入与DB inventory保持，四文件暂存SHA逐字匹配门禁，双审CLEAR。I-45基线的clean consumer2/provenance仍为正式不变artifact证据，不把它冒成新源码consumer重跑。实际IAM＋raw BFF HTTP relay1PASS/0SKIP，退出/删除Cookie/旧Cookie匿名全部通过，source/DB保持且清理通过；不是生产Nest/browser G1。
- **当前验证/已交付**：Root4e603743的I57原两文件已独审、主方完整2142PASS/3SKIP/531subtests/Node/Ruff并推原PR66；正式原五旅程随后5/5通过，严格broker收据、源/Node精确、共享Admin验证、cleanup/quiescent/凭据扫描通过。真实anonymous后canonical sign-in/私有canary退休已由新原旅程验证，聚焦诊断仍只作诊断。原07c失败及较早Adminbuild失败保留，当前run无命令失败；不把SSL stderr计数作为未证因果。
- **I56当前实证**：三仓及Root候选冻结/交叉CLEAR；IAM完整1695/126、真实482/48与提交后clean consumer2通过，537输入/DB保持；BFF完整format/check0（contract1347/default2370PASS＋2条件SKIP），当前真实PG423/0SKIP含schema15补证、1085输入/DB保持并回收；App458contract/50architecture/6399default、0SKIP及工程门/构建后types0，1504 tracked inputs保持。真实HTTPS删除3条均Secure并保留3条、原真实IAM/raw BFF relay1通过且全回收；不是Nest/browser G1。Root完整2135PASS/3SKIP/531subtests、Node/Ruff与855受保护输入保持，后续仅三tracking docs同步与gitlinks交付。
- **账户实际消费已补证**：BFF8cb6169与IAM1fc3875，源码绑定fresh build/1214 dist字节保持；真实生产Nest→IAM完成18行为检查，profile实际peer＋actor且无Cookie/Origin，账户实际独立peer＋Cookie/Origin且无actor（1次profile/10次账户调用）。包括伪actor覆盖、三Session opaque分页、自撤409/撤他200、立即expired tombstone、冻结旧Cookie匿名/401invalid、应用删除后401required及A/seed存活。source/DB保持、credential scan/回收通过；原首轮失败为harness误传legacy request-id，按既有原生协议改标准x-request-id后保原断言通过。不是App/Admin/browser五旅程、单库应用或T17证明。
- **G1收口**：既有正式五旅程、账户实际消费和分层零越权/未知结果证据，加上真实Native Create→Begin→signed PUT版本ACK→Complete CLEAN→Validate→Publish→同subject Install及原BFF四GET全部通过。错Origin/服务身份拒绝、伪身份头不覆盖真实Session、独立purpose服务密钥失配与实际IAM中断均维持typed拒绝；源码/dist/DB清单及凭据扫描保持，两个自有S3版本和全部自有资源已回收。主方与独审确认无额外未决G1项；不将原四GET单独等同全门。
- **剩余TODO**：T-17完整生命周期→T-11遗留清理→C-4最终门、精确组合与同步环境；不重做已验G1。每仓沿原PR，不merge main、不部署；A-01/A-02/A-07保持GATED。

## 0. 当前结论与唯一入口

**Task A 尚未闭环；G1 / T-05已闭合当前冻结组合范围。** 原正式五旅程、账户真实Nest→IAM消费、真实包producer/原BFF四GET和独有组合负控共同满足G1，源码及收据经主方与独审复核。G2/G3仍OPEN；下一步是 T‑11 遗留删除及 C‑4 最终组合/常驻环境，不把阶段验收换算全产品完成。

根目录 [todo.md](../../../todo.md) 是唯一执行清单；本方案维护技术裁决、原任务 ID 和证据。按用户要求每小时做一次只读进度对齐：完成/证据、进行中负责人、阻塞偏差、下一检查点及 Goal/TODO 待纠偏；不借定时汇总新增实现或并发改清单。`docs/task.md`、`docs/CURRENT.md` 只保留摘要与链接。

规范来源：
- [原 Task A 完整任务表](../../handoffs/2026-10-30-task-a-workspace-execution.md)；[原清理执行顺序](2026-10-30-task-a-cleanup-refactor-execution.md)。
- [清理设计](../specs/2026-10-30-task-a-cleanup-refactor-design.md)、[逐项 disposition 与测试矩阵](../specs/2026-10-30-task-a-cleanup-inventory.md)。
- [ADR-036：Nest 收敛](../../kokoro-handbook/decisions/ADR-036-bff-nestjs-convergence.md)、[ADR-035：内部 direct credential](../../kokoro-handbook/decisions/ADR-035-direct-internal-service-authentication.md)。
- [当前实施证据](../evidence/2026-10-31-task-a-c1-cleanup-implementation.md)、[历史 native 收据](../evidence/2026-10-31-task-a-c1-3-native-receipt.md)、[历史问题台账](../evidence/2026-10-31-task-a-issue-register.md)。

### 0.1 当前组合与未提交范围

执行目录：`/Users/nako/.codex/worktrees/task-a-c1-cleanup/Kokoro`；Root 分支 `codex/task-a-c1-cleanup`。不要把原 checkout 的 `main` 当成本轮执行树，也不要把 HEAD 当作包含未提交候选。

| 仓 / 范围 | 已提交基线 | 当前候选与证据层级 |
| --- | --- | --- |
| Root | `4e60374353a565e6e11592a34274c5564388c766` / 原draft PR66；当前仅进度docs | I57原两文件独审/完整治理2142/3SKIP/531subtests及Node/Ruff通过后交付；正式原5随后5/5通过、严格broker验证、四owner clean/gitlink精确、共享Admin/cleanup/scan通过并全回收。新进度仅三tracking docs，不改已验代码/四gitlinks；Agent拓扑差异归T16/C4；inspection真实组合与完整G1已复核通过 |
| App | `197f110294e9b373d5c4aa0836b3d80f48e3a833` / 原draft PR50 | I56唯一生产config一行及六原测试/二docs已交付clean；Root最终完整458contract/50architecture/6399default、0SKIP，全部工程门及post-build types0；1504 tracked source保持，五env模板另外核HEAD原字节。Root4e603743原正式五旅程已通过；完整G1当前冻结组合已收口 |
| Admin | `95c504d1bfdcf1038ebadb85d8493c18828b51f7`，原PR5分支 `codex/admin-credit-funding` | 共享安全Session消费已推原draft PR5，远端head精确95c504d。Root最终完整348PASS/0SKIP及contract/lint/typegen/types/build/posttypes全部0，179输入保持；随后只修一行API文档时态并独审CLEAR、diff-check通过。本仓clean，Root4e603743精确配对的正式shared_admin已通过；完整G1当前冻结组合已收口 |
| BFF | `8cb6169cf1d15d54c3a3bacad9ea622695642228` / 原draft PR18 | I56唯一生产config一行及五原测试/二docs已交付clean；完整format/check0、contract1347/default2370PASS＋2条件SKIP；当前真实PG423/0SKIP含schema15补证，实际IAM relay1及HTTPS删除Secure3→保留3，source1085/DB保持并回收。状态1.0/relay3.0字节不变，不代Nest生命周期/inspection owner/G1 |
| IAM | `1fc3875952a9840aa1a8d15124b9be0eaf91c5f2` / 原draft PR6 | I56删一行NODE_ENV覆盖、官方issuer URL默认；Root完整1695/126、全部真实482/48及本commit clean consumer2通过，537输入/DB保持；真实HTTPS删除Cookie3条Secure保留3、原IAM/BFF relay1通过。internal/SDK0.20正式产物不变，正式原五旅程及后继完整G1证据已通过 |
| Agent | Root pin `c761fad3dba2b56cd7fe4da7683a9ac2f208243f`；本地 `47ca431` | c761候选lock/frozen sync/格式/lint/types/contract/generated/default3336/build/installed wheel已主方验；47ca431仅修display旧integration oracle并删两过时参数，真实全文件26通过。未推送/未更新pin，不算C-4最终全资源/组合门 |
| Capability（物理路径仍为 kokoro-capability） | `f515e22596357e2dd6c05cfa47a1c2f54b99f202` | receiver-only源码及真实PG已验，独立draft PR13依赖PR12；远端基线2ad5c9e未集成且PR冲突，保留原已验组合不覆盖新增提交，最终合并门OPEN |
| 其他组合成员 | 当前 Root gitlinks | 仅按受影响边界纳入验证；本轮未启动、未刷新全套运行健康状态 |

当前消费者只接受下列已提交候选原件；Root不建第二契约中心，不把此表视作新组合已验：

| Owner commit / 原件 | 版本 | SHA256 |
| --- | --- | --- |
| IAM `896405d146c4ff96f5f39d5c2ce1bc788d46c2c7` / `contract/openapi/iam.internal.v1.json` | internal / SDK 0.20.0 | `61cf99b4fe836deafedb9f59d9fa2ea3446ce172f4069944f7facb14e816c7ca` |
| BFF `34c9f997a4d86f33be2f815c43cd155ed338fe86` / `contract/openapi/browser/v1/auth-session.json` | 1.0.0 | `a7b5876632f6ad91b9fc162c9abcf48b36b2677a3b15a6a497d3305aeaea81ba` |
| BFF同commit / `contract/iam-relay-policy.json` | 3.0.0 | `c88bab0bd1d5529573eee318e50ac2dd41349a03fc84e8b7284416af700a0ebe` |

### 0.2 进度与验证事实

| 阶段 | 已有成果 | 当前结论 / 缺口 |
| --- | --- | --- |
| G0 | ADR-036的Nest/DI/feature决定保留；原native artifact/hash只证明历史准入 | 认证D0三面主方复核通过，依已有ADR与用户“标准后端推翻重来”要求进入owner实施；不声称用户另行接受过候选，不用旧artifact/测试放行消费者 |
| C-1.1 / C-1.2 | BFF schema-evolution 旧入口、App hash/legacy 展示分支、Agent legacy_failed 推断等已删除；保留 canonical localDraft / journal / replay | 已提交切片；最终零消费者复核及 App/BFF/Agent 完整门待 C-4 |
| C-1.3 | 历史native四旅程与Capability receiver片已验；IAM标准认证0.20和BFF六合同检查点已沿原PR交付 | Root4e603743精确组合原正式五旅程与账户18已通过；当前普通业务/账户认证分离已实测。inspection真实producer/原四GET及组合负控已通过，G1当前冻结组合VERIFIED |
| C-2 | Nest 生产图已移除 LegacyRoutes；named feature 路由接管；generic configured-owner proxy tail 已删除 | raw server/runtime 与测试消费者仍存；生产 Nest shutdown 语义待核；入口隔离候选不等于删除完成 |
| C-3 | BffBusinessStore / BffApplicationServices / PostgresBffRepositories 旧 aggregate 已清理多片；global ports 仅留 idempotency contract | raw composition / owner-resource 聚合工厂和 feature disposition 仍待最终审计，不以类名删除代替边界证明 |
| C-4 | App e1be/BFF4d6/IAM1ee8/Capabilityf515各有对应工程门；Root治理/真实限定链路有证据 | Agent全门、最新base整合、全受影响真实I/O及最终组合E2E/常驻同步环境未齐；678skip不算通过 |

证据严格分层：
- **已提交旧基线**：BFF `228e3d6` 默认测试 2298 total / 2296 pass / 2 skip / 0 fail；该时默认入口未纳入两套 Nest 架构测试。IAM `a1457be` verify 为 120 files / 1561 pass / build PASS。Root 上次 topology PASS，治理 1846 pass / 3 skip / 502 subtests。这些不是当前 dirty tree 全绿证明。
- **App 历史T-07基线9ba，Root复验结果（最新基线见§0.1）**：Node 22.23.4；contract 48 files / 452 pass、architecture 50 pass、完整 test 354 files / 6373 pass / 0 skip；typecheck/lint/build/diff-check 通过。旧基线50个契约失败已收敛，Root完整check exit0且56路径前后SHA一致；已提交4260f698、集成origin/main空树merge为9ba65343并推送App draft PR #50。Root当时已pin；该历史阶段真实四旅程仍待，最新正式4/4见§0.1。
- **BFF 历史173e026切片，Root复验结果（最新基线见§0.1）**：Node24.20.0下format/check exit0；contract1344pass，默认2343pass/0fail/2skip，lint/types/build通过。两项原数据库条件skip另补整文件真实PG schema15pass/0skip，覆盖共存/回滚与R237。原architecture73/focused123为辅助证据；未完成完整业务integration/当前native链路，字面依赖扫描不称完整AST图。
- **Root runner历史阶段（不是最新验收结论）**：最初close函数缺失1pass/2fail，后续独审发现五项清理/收据缺陷，均已在T-13修复并以Root60定向/IAM真实62及成功/失败退出验证。现Root六文件T-14配套候选另有154定向、完整治理1879pass/3skip/506subtests；真实Capability receiver后续已验（f515，见§0.1）；该历史阶段完整四浏览器旅程仍未验，最新正式4/4见§0.1。
- **历史真实链路**：旧组合有 IAM 集成 12 pass、IAM→BFF 7 case、HTTPS native smoke 4 case。保留其对应 SHA/范围；不外推到当前 Nest/候选组合，也不将历史 OIDC 验证作为目标 native 链路。

---

### 0.3 测试价值审计与处置（I-36，2026-11-02）

范围：IAM `cc3fbaf1`，两路只读 Agent 分别抽查 integration/consumer 与 unit/architecture/smoke，Root 复核具体源码并抽查 contract。没有完成全部 484/1651 用例价值审计，不设置数量削减目标。下面复用 T-05/T-09，不新增任务中心。

| 处置 | 当前证据与独有风险 | 状态 / 下一动作 |
| --- | --- | --- |
| 重写 SDK consumer 旧凭据 | `test/fixtures/sdk-consumer/src/real-consumer.ts` 用 tenant OAuth 调 Billing；现 `billing-authorization-http.test.ts` 明确该凭据应 401。打包、外部安装/编译/真实调用仍有独有价值 | VERIFIED（此测试切片）：b2f28d4 修旧凭据，2cb9864 修独立 SDK 回归后主方完整 consumer 2 PASS；其余 I-36 处置不据此关闭 |
| 合并 SMTP 正例 | 两个邀请正例原本重复收件人/subject/path，第二例独有 origin/唯一query ID/PG状态 | VERIFIED（1d82fa2）：独有断言已并入真实HTTP正例并绑定响应invitation ID，删除直接调用重复例；拒收/pending、注册验证、magic-link、TLS原例保持。主方原SMTP整文件真实通过 |
| 替换 Skills 源码顺序断言 | 全文件indexOf可能因-1假通过且不绑定路由 | VERIFIED（1d82fa2）：删除弱位置比较；保重复key/JSON/权限/413，补原始非法UTF8字节400/no-store/request ID。正常成功也不写audit，新增计数断言无独有价值已删除；最终Skills真实16通过，不宣称证明service未调用或具体解析分支 |
| 删除 Audit 机械清单/重复字符串检查 | 精确query/maintenance文件清单锁布局，tenant源码包含不证明隔离，原HTTP宽松schema会剥未知字段 | VERIFIED（本片1d82fa2）：删两文件清单与tenant字符串检查，保Nest/schedule边界；真实两页strict schema+exact IDs/tenant/sentinel/keyset承接wire。details/resultSlot两条原弱检查暂保留，不把wire脱敏说成SQL最小读取保证，不新增未有设计要求的DB读取门 |
| 强化 contract 结构断言 | `session-authorization.openapi.test.ts` 等 stringify 后 contains 字段名，不证明类型、必填或所在位置 | VERIFIED（1d9bd95）：四处改结构断言，properties/required按集合，保closed/type/nullable与绑定，去掉重复request-id contains。既有SwaggerParser仅本地dereference，容许等价$ref；主方6文件39通过，内存等价变换4通过/22名称过滤，不复制整Schema/日期regex或新增框架 |
| 复核转发用例/重复 fixture 与命名 | native unit 的部分纯 mock 转发重复，guard 装配重复；MCP 的 “native signed user token” 实为 OAuth，kernel “every” 实仅六入口 | VERIFIED（1d9bd95，本片）：删Skills/publisher两项纯mock转发，由原真实guard→事务复读矩阵承接，主方native15通过；保Account/MCP政策。纠正OAuth/代表性入口标题。guard重复fixture保留，不因风格新增通用框架 |
| 保留真正跨层证据 | native guard 后撤权→事务复读零写；provider refresh 竞态；profile CAS/审计回滚；真实 socket 断连与已提交未知结果；unit 的确定性时窗 | RETAIN：不同入口/层级有独有风险，非按同名判重复；mock 提交不描述成真实数据库提交 |

本次抽样已识别项已完成保留/合并/删除/重写处置，实际删改有风险承接、双审与主方定向验证。I-36仅此有界发现集闭合；全部484/1651用例价值未逐项审计，两条Audit敏感列源码弱检查仍明确保留，不宣称无冗余或整体Task A完成。

## 1. 已知问题全量表（本次 Task A 审计范围）

这里只把本次可核验的问题标为当前事实；历史或任务外问题保留归属，未核验不等于无问题。

| ID | 问题 / 当前证据 | 处理与关闭条件 | TODO |
| --- | --- | --- | --- |
| I-01 | 原精确源码/dirty/gitlink阻断已解决：Root1e6精确App e1be/BFF4d6/IAMe6，Capability f515另已pin | 已验组合source门保持；后续IAM fixture或base整合新候选必须重新停写/提交/精确pin，不绕过门禁 | T-04/T-13/T-05/T-09 |
| I-02 | MCP denied icon mutation 曾在拒绝后调用 Platform | `228e3d6` 已补 manage admission，focused42与基线 full已证；最终组合继续保护零副作用 | T-02（已验证切片） |
| I-03 | Skill installation Chat invalid-owner error 曾被 fixture 缺失掩盖 | `228e3d6` 补最小 receipt seam，focused24与基线 full已证；保持 typed error，不放宽断言 | T-03（已验证切片） |
| I-04 | BFF原32文件格式warnings已机械修复；Root完整格式门通过 | 重跑确切清单，仅处理本任务受影响文件；不做无关全仓格式化；门未绿前 C-4 保持 OPEN | T-06 |
| I-05 | App Public28.18 pin/generator/历史逆证已正规修复并经Root完整门，已提交独立draft PR | 原问题已按T-07切片关闭：原件/旧父链独审、Root完整门与精确集成已验；后继组合继续保护，不手改快照或历史hash | T-07 |
| I-06 | IAM SDK drift | `a1457be` 已正规生成并 verify；更改消费者后仍核 fixed artifact，不引入手写第二契约 | T-08（已验证切片） |
| I-07 | 全部 owner 的受影响全门、真实 I/O、当前 E2E 收据未齐 | 按停写组合串行验收，逐项记录 fail/skip；不把 health/static/fixture 当产品闭环 | T-09/T-15/T-16 |
| I-08 | A 任务产品缺口尚在，容易被清理完成误标关闭 | A-01/A-02/A-07 保持门控；A-03～A-16 保留完整 backlog；不新增本轮产品代码 | T-10 |
| I-09 | raw server/runtime、composition 与无边界聚合迁移 | 本地 BFF `ef64012` / `38d0200` 已删除 raw、dispatcher、宽 PG 聚合和 Chat 可选 provider；保留具名 owner、可执行 HTTP 与真存储风险。跨仓旧 IAM 消费退出和最终门仍待，不以历史静态计数代替验证。 | T-11 |
| I-10 | 默认 test/check 曾遗漏 Nest 架构门 | 候选已在 test 与 test:architecture 各接两套 Nest suites 一次；主方复验默认入口；静态扫描不冒充完整依赖图 | T-12 |
| I-11 | smoke teardown 吞 process/proxy 异常，缺 IAM 前后 inventory；失败日志在临时目录退出时消失 | 所有自有资源尽力回收、失败可见、未停进程不删依赖；增加脱敏 stage/cleanup 收据和泄漏负控；红测保留至真实修复 | T-13 |
| I-12 | Capability `global_register` 原用 IAM workload introspection且曾被TODO遗漏；f515接收方切片已替换并验证 | policy caller为kokoro-system；System当前未见实际producer，已验范围仅direct credential receiver。最新base整合归T-09，无需求不新增System注册功能 | T-14 |
| I-13 | 原真实AppModule compile→close探针closeCount0/externalIo0复现接线缺口；两文件修复后主方88相关测试/格式/lint/types/build通过。再用受管真实PG/Redis验证正常空闲连接：production hook在fallback前均1→0，禁用hook负控均1→1，能检出原故障 | 资源hook子项已验，不等于完整生命周期。锁定Nest12吞hook rejection；完整init/readiness、HTTP/SSE、worker、故障/挂起、硬期限与信号退出码仍OPEN，完成后才删raw shutdown | T-17 |
| I-14 | 新旧计划/问题台账/日期混用，App旧失败、G0待批准、资源缺失等曾覆盖当前态 | 本计划唯一当前台账；旧文件加历史/导航标记；候选/已提交/Root复验分列，状态变化再同步摘要 | T-01 |
| I-15 | 单数据库 owner schema 组合、Redis namespace、自有 fixture 回收尚无当前共同证据 | fixture 临时库只是隔离，不证明应用单库组合；逐 owner 核 installer/URL/schema，禁止跨 owner SQL/共享 reset | T-04/T-09/T-15 |
| I-16 | Agent最终资源/组合门与全局规范审计未齐；候选复核发现display资源测试仍要求已删文本失败推断 | c761静态/default3336通过但排除integration；主方原legacy真实RED assert1==2，47ca431一文件改现行事实并删两过时参数，真实全文件26/双审通过。原历史224不当当前计数；最终全资源/组合与治理核对仍在C-4，不冒全仓无问题 | T-09/T-16 |
| I-17 | 原runner遗漏必需的Web Redis输入已修复并提交，实际无cookie注入冷登录已通过 | 此配置不是退休项；隔离注入/归属/回收与冷登录证据已验。后续永久四旅程保留该回归，不以默认preview替代 | T-04/T-13/T-05 |
| I-18 | 原BFF engines与pin/生成链/CI/Docker存在Node24/22漂移；173e026已统一并通过Root当前完整静态门 | 保留两轮RED与真实修复证据；七条正规生成/双检及当前完整门通过，106generated不变；未实跑CI/Docker，不以配置对齐冒称容器验收 | T-18 |
| I-19 | 原Nest启动失败已解决：BFF4d6修复五处DI可见性，Root535最小native成功；完整关闭矩阵仍缺证 | 已加真实生产容器compile/关键token单实例回归；后续验证drain/SSE/worker/PG/Redis，不重复领取旧启动修复 | T-17 |
| I-20 | 本计划曾要求同App正向双tenant切换，但App/BFF/IAM当前三面设计与G0都明确固定Product tenant；属于台账错误 | 已按有效裁决纠正T-05；用异tenant会话拒绝/固定域恢复验证隔离，禁止删BFF授权门或新增TaskB切换器 | T-01/T-05 |
| I-21 | 真实冷登录原表单303后session/projects401，App缺固定tenant set-active，fixture预设会话曾掩盖 | App e1be及Root旧组合已完成真实冷登录/退出HTTP验证；此原缺陷闭合，不等于当前完整四旅程通过 | T-05 |
| I-22 | LocalPlatformRuntime先生成单projection文件，随后聚合多surface凭据以同名O_EXCL创建，真实文件装配抛FileExistsError | Root候选已改独立聚合文件名，真实临时目录RED→GREEN并保持0600/回收；独审及Root154定向通过，已随c08c提交并配对f515；此文件装配缺陷闭合，同步环境仍待T-15 | T-14/T-15 |
| I-23 | Capability现部分R317/R336 opt-in测试、显式package smoke与release workflow有旧OAuth/CAS/publication配置欠账 | T14 receiver切片保持已验。2026-11-03只读确认当前smoke-storage-package仍为显式package脚本但不入default/verify/integration，Publish缺required expectedPublication且依赖预存skill；旧Root runner另锁过期pins/OAuth env。R336仅有SYSTEM_INPUT_FILE才运行，缺当前CAS/sourceVersionId/frontmatter，未启用不算通过。T05用当前owner Native真实fixture供原BFF四GET，不以私有fixture冒原入口已修；原有效入口修复/退休随T09/C4按风险承接，不删断言清绿 | T-09/T-14/T-16 |
| I-24 | 已修复退出两层缺陷：显式POST body与owner JSON媒体类型/空对象规范化 | App e1be完整门6407/0skip及Root真实退出200、cookie清除、项目/旧cookie均401；I-24在此HTTP范围闭合，完整T-05仍OPEN | T-05 |
| I-25 | Capability原PR12基线由44fcc前进至2ad5c9e，4提交/73路径含契约和Schema；本Task A PR13与其存在实际合并冲突 | 保留双方提交，不force、不整树择一；在独立集成区审边界/冲突后重新完整门和真实receiver，再更新精确Root组合。当前仅已验f515候选 | T-09/T-16 |
| I-26 | Root dd447正式四旅程cold_login已303并到/app，但账户入口不可见而超时；诊断14次HMR WebSocket Upgrade均404，代理缺101双向转发 | 已交付实现与原断言保持；Root aec5775a/run2a960804正式4/4通过，本项在真实旅程范围闭合。对应RED/修复/组件门与历史失败见实施证据，不重复领取 | T-05/T-13 |
| I-27 | Root50ac正式旅程已过cold_login UI/profile，进入异tenant旅程后profileBarrier的route.fetch在TLS握手前失败；Playwright Node请求不继承Chromium域名/443映射，私有同请求loopback诊断200 | 已交付实现与原断言保持；Root aec5775a/run2a960804正式4/4通过，本项在真实旅程范围闭合。对应RED/修复/组件门与历史失败见实施证据，不重复领取 | T-05 |
| I-28 | bad205正式异tenant旅程已取得真实profile barrier，但driver错误要求projects401；实际session401/native_session_required、projects403/product_tenant_forbidden，符合固定tenant隔离实现 | 已交付实现与原断言保持；Root aec5775a/run2a960804正式4/4通过，本项在真实旅程范围闭合。对应RED/修复/组件门与历史失败见实施证据，不重复领取 | T-05 |
| I-29 | 历史BFF4d6生产缺native配置时回退Bearer；目标应仅当前标准浏览器准入 | VERIFIED（当前消费者处置）：BFF8cb唯一AuthenticationModule→官方get-session→独立service+actor；App197/Admin95无RP mirror/refresh链，Capabilityf515本路径不换workload token。独立源码复核未见旧SessionRef/OwnerSessionAuth/第一方client-credentials生产消费；公共skill.list/IAM独立OAuth/API Key/OpenApp/第三方MCP OAuth合法保留。IAM遗留PlatformWorkload producer仍装配、不是已删除或合法公共OAuth，零目标消费者后的删除明确归T11 | T-05/T-11 |
| I-30 | 原BFF漏生成native operation且自写response，已由f81f271正规生成24 operations并删除重复schema，unknown error fail-closed | 本片已闭合：双审、Root完整门1345contract/2350default（2skip）；现固定原件不升级。I-29后继artifact再正式固定/生成，I-30不代表授权闭环 | T-05 |
| I-31 | G1负控仍须完整映射；BFF默认入口已由I-30补齐。IAM1d9bd95已有真实专用admission无效服务凭据401及guard先于人类读取证据，不因通用矩阵缺参数再造重复例 | 285dfcb两测试切片已双审/主方验：真实host14含同Cookie重复sign-out/expired tombstone/另一SID用户不变，guard58含专用admission依赖故障typed503，后者不冒HTTP/controller零调用。BFF b6d98f8生产ProjectMutationMiddleware/client真实loopback失败关闭与成功控制已双审、主方native整文件6通过。当前独立补证完成；新owner合同消费后的组合负控仍随I-29/G1，非此局部测试代证 | T-05/T-12 |
| I-32 | cc405正式run在focusProbe等待session超时；锁定Playwright默认启用focus emulation，抑制bringToFront真实事件。私有禁用两页override后trusted事件/session401与前三旅程顺序走通 | 已交付实现与原断言保持；Root aec5775a/run2a960804正式4/4通过，本项在真实旅程范围闭合。对应RED/修复/组件门与历史失败见实施证据，不重复领取 | T-05 |
| I-33 | 同请求首次/me429→App503已证，场景累计负载触及既有共享配额；Root c142c49c仅在独立场景边界尊重窗口 | Root2005治理/3skip与双审；aec5775a正式4/4通过，本编排缺陷闭合。未抬配额/缓存/重试，不冒产品容量证明 | T-05 |
| I-34 | App最终鲜验原catch成null误判401，已由fdbb49f1删除吞错，依赖不可用沿503且无资料泄漏 | 本局部缺陷已闭合：先3项真实loopback RED，Root App完整6411/0skip、contract452/architecture50/lint/types/build，1494输入稳定且双审CLEAR；当前aec5775a正式4/4已通过，整体G1另验 | T-05/T-12 |

| I-35 | IAM 完整 integration 原 15 失败：schema digest 非 id 主键、Session 物理删除旧预期、CLI 资源身份缺口 | 已修旧 oracle 并保留数据保全/撤销断言；CLI 仅显式采用同管理连接实际 role，不改产品/权限。主方原整套 48 文件 / 484 PASS，无 skip；纳入本地 cc3fbaf1，不代表消费者或 G1 完成 | T-05/T-09 |
| I-36 | 测试价值抽样发现 SDK Billing 旧成功路径、SMTP 重复正例、源码位置/文件清单耦合与弱契约断言 | §0.3 有界发现集已处置：consumer、1d82fa2首批及1d9bd95结构/转发/命名均双审、主方定向通过；保留项注明风险，不宣称全部套件无冗余，不按数量减测，不冒I-38批准或全产品完成 | T-05/T-09 |
| I-37 | SDK 在新增双认证 scheme 后把 bearerToken 同时填入 Cookie，OAuth 请求误入 native 并 503 | 局部已验：2cb9864 仅 transport/既有 SDK 测试；HTTP Bearer-only scheme callback，Basic/默认/调用覆盖保持，generated/guard/contract不改。双审CLEAR，主方verify默认1654/consumer2 PASS且542输入未变；未推送，不决定I-38 | T-05/T-09 |
| I-38 | 用户已否决请求内Session引用，要求按后端标准推翻重做 | 引用candidate/提案已撤销，旧A/B等待结束；认证D0已按§3.6收口，IAM先交付、BFF/App/Admin消费在做。旧逐业务Cookie、假claims和兼容principal不是目标，不重设批准阻断 | T-01/T-05 |
| I-39 | IAM最终规格审发现Team损坏Tenant状态、重复issuer Cookie、既存OpenApp scope读取三项漏承接 | VERIFIED（IAM896405d）：7实际RED后最小修复，独审复核CLEAR；Root最终verify1673、全部真实481与clean consumer2通过，source/DB inventory保持。无新认证副本/role扫描，不以测试数量代替这些具体风险 | T-05/T-09 |
| I-40 | BFF安全状态候选遗漏error.message必填，query/default生成存在第二事实源，契约测试锁oneOf/属性顺序 | VERIFIED（六合同检查点34c9f99）：补唯一source的strict错误/请求schema，parser与generator共用；改结构/集合断言。主方以HEAD802＋六文件独立快照重跑focused/generator/工程门，原PR18已推。运行时与consumer闭合仍归T-05，不扩张此证据 | T-05/T-12 |
| I-41 | Root标准认证编排首轮独审发现browser模式只验authenticated布尔（漏strict身份/expiry/匿名私有canary），匿名UI退休继承30秒而弱化原3秒；当前文档另有旧D0/发行状态矛盾 | VERIFIED（Root编排切片）：文档已复核纠偏；7实际RED后补共享strict状态oracle及3秒总退休deadline，独审修后CLEAR。主方最终205定向＋7文档测试通过，Ruff/node/diff及三输入SHA保持；未实跑新browser组合，首轮Root2065只作返修前辅助证据 | T-01/T-05/T-12 |
| I-42 | App旧mock迁移脚本过宽匹配测试外层，typecheck已检出；实际影响为29文件 | VERIFIED（测试修复切片）：从精确HEAD恢复后窄迁移，原风险断言与suite/hooks保留；治理及两旧HTTP fixture已承接，最终Root完整check6388/0SKIP与contract452/architecture50、lint/types/build通过，1505输入保持。不是新组合browser通过 | T-05/T-12 |
| I-43 | BFF规格复核发现MCP末验、Profile/Team typed服务错误及Skill真实client风险漏承接；另有旧Origin fixture | VERIFIED（返修切片）：独审CLEAR，Root修后完整format/check通过（contract1347、default2352/2条件SKIP），1086输入保持。后继I-48/I-49改变基线，最终真实资源及全门仍待；不将此前纯门代替最终BFF交付 | T-05/T-12 |
| I-44 | Admin同owner新SSR恢复被去重；首修又有旧background检查拒绝回调清空刚恢复身份的竞态 | VERIFIED（Admin认证消费组件）：两轮真实RED后633d88仅hook＋两测试，旧check先退休，修后独审CLEAR。Root最新完整47文件/348PASS/0SKIP、contract/lint/Nexttypegen/types/build/posttypes全部0，179输入保持；不当真实共享Admin/browser或Task A闭合 | T-05/T-12 |
| I-45 | 官方User的管理员bool与IAM具名管理事实完整性存在分歧：true＋负version时core成员门允许、管理policy拒绝；BFF现global-admin gate仍可放行 | VERIFIED（IAM4463c50增量）：只证明BFF gate差异，不冒下游写成功或旧native回归；官方after成功get-session单次User窄读，复用validator且version私有，未扩core角色门。Root最终verify1687、全部真实481/0SKIP、clean commit consumer2/精确provenance与双审通过，537输入及DB inventory保持；原PR6已推，无Schema/API shape改变，不代表新组合/G1 | T-01/T-05/T-12 |
| I-46 | App多Cookie合并、迟到RSC覆盖新身份数据、歧义Cookie抛500及SSR首帧/预hydrate失效缺口 | VERIFIED（App消费组件）：实际RED后窄修、限定独审CLEAR；fde7565候选Root完整6388/0SKIP及contract452/architecture50/lint/types/build/posttypes通过，1505输入保持。其后只有四份owner文档变化；未新增登录流程/SessionID/协议，新组合browser仍待 | T-05/T-12 |
| I-47 | BFF core tenant/read只按status接受429/403，错typed tuple可误判限流或人类失权 | VERIFIED（质量返修切片）：strict schema与exact tuple，原Retry-After及框架分支保持，独审CLEAR；Root完整format/check1347contract/2352default通过（2资源条件SKIP另由schema15补证），1086输入保持。后继I-48/I-49新基线须复验 | T-05/T-12 |
| I-48 | BFF原单URL两具名DB guard互斥，默认2SKIP与独立资源入口未被纯门承接 | VERIFIED（PG范围）/OWNER_COMBINATION_PENDING：Root最终10组423PASS/0SKIP，含原15 integration suite、6独立PG及schema15；source1087/DBinventory保持、cleanup通过。此前240/101与349/9失败保留并有因果窄修；不累计重复批次数。inspection单fixture wire8PASS/19坏输入关闭不冒真实IAM/Platform；后继真实relay、账户消费及inspection owner producer/组合已补证通过；不改或冒称完整应用单库拓扑 | T-05/T-09 |
| I-49 | 真实资源门检出的既有Message/Task/Project入口保障缺口与旧fixture/oracle漂移 | VERIFIED（组件＋真实PG＋工程门）：唯一Message handler、移除外围receipt、同lifetime/UNKNOWN保持已真实复验；Task exact PROJECT_NOT_FOUND→404经原receipt、Project单尾斜杠400、RR同页＋下一鲜读null及AGUI正例省略非法null均已Root整批423/0SKIP通过。三过时源码锁退休/AST有效违规样本与JS resolver fixture返修保独有风险。Root最终format/check全0，contract1347/default2369PASS＋2条件SKIP（schema15另补）；真实IAM/浏览器G1另验，不新增A功能或Schema | T-05/T-11/T-12 |
| I-50 | App完整复验检出unknown告警后Escape未关dialog，尚未执行retained Task导航 | VERIFIED（App局部缺陷）：受控窗口实证DOM已解锁而Radix旧闭包仍captured saving=true；仅两文件用现有committed layout/ref同步四guard。原32项保持，先RED1/1→GREEN2，Root独立原文件34PASS及冻结链通过；最终完整6390/0SKIP、452contract/50architecture/lint/types/build全0、1505输入保持。已随bfb749c3推原PR50，新组合另验 | T-05/T-09 |
| I-51 | 共享Admin未被runner启动；fixture无真实管理员，Node同origin不继承Chromium映射 | VERIFIED（编排/fixture组件）/G1_PENDING：Root标准Node CONNECT＋CA五类正负控保持Host/SNI且全回收；原host新增旅程真实RED后整文件15PASS，I-51基线verify1687/全48 integration suite482PASS。Root原三文件组件232＋文档7＝239PASS，browser模式拒绝未配对IAM豁免，产品源码/Schema不改。源码停写，未提交配对或实跑共享Admin浏览器，不当G1通过 | T-05/T-15 |
| I-52 | 真实IAM/BFF relay退出失败；IAM零字节POST被物化为有body，偏离锁定框架Node adapter | VERIFIED（认证HTTP组件）：原unit实际RED2→相关13PASS；Root当前完整verify1690、全部真实482/0SKIP及真实IAM/BFF relay1PASS。保原无body请求，退出200/issuer Cookie删除/同旧Cookie安全状态严格匿名，source/DB保持且清理通过；最小四文件含I-51已推9ea5b4c原PR6。无媒体/CSRF/Schema放宽，不外推Nest/browser G1 | T-05/T-09 |
| I-53 | I-52测试给原生sign-out新增了未获合同支持的no-store断言，真实复验停在该断言 | VERIFIED（测试约束纠偏）：Generic native合同保留owner缓存头，safe status及具名邮件/邀请操作才强制no-store。仅撤主方误加的raw sign-out缓存断言；exact200/删除Cookie/noJWT及旧Cookie fresh safe严格匿名/no-store/noJWT逐字保留，独审CLEAR、实际真实relay1PASS/0SKIP且回收。未为测试绿改生产政策，原RED保留，不称原生产退化 | T-05/T-09 |
| I-54 | 新精确组合G1停在Admin隔离build阶段；编译成功后的进程组库存-信号竞态令EPERM被立即判失败 | VERIFIED（helper组件＋正式run Admin阶段）：正式四源码/Node/production BFF已通过、0旅程，清理/scan通过。原helper独立真实build复现编译成功后EPERM，原HEAD另观察库存true→ProcessLookupError。两文件最小修复仅复用原15/5秒库存预算；原用例实际4FAIL/1PASS→45整文件PASS，持续存在/库存失败仍报错，独审CLEAR。Root原helper实际隔离Next build已PASS/全回收，最终Root治理2105PASS/3SKIP、531subtests及Ruff全0，851输入保持；已推78105bb6，正式重跑已过Admin构建/启动，后续I55另收口；不改产品/认证/90秒期限 | T-05/T-13 |
| I-55 | 新G1已进入tenant_rejection_recovery，retired旧oracle强制私有账户card继续可见，与可信403的数据空壳路径不符 | VERIFIED（oracle组件及后继正式五旅程）：Root78105bb6正式run已过Admin编译/启动和先行冷登录/共享Admin步骤，整体收据仍0完成、在driver214失败且全回收。只读核当前App可信403为forbidden/checking而非anonymous，booting分支卸载私有Runtime。Root私有诊断保留原失败断言，真实DOM为仍在/app、非/login、账户card/旧邮箱/subject/姓名字段均0；真实composer非空draft原字节在403时不变，同Session恢复fixed并reload后原draft可见且字节不变。故只纠正Root原oracle，保3秒总预算、无私有泄漏、非匿名/不注销及迟到结果不复活；不改App产品或以空draft冒保留。原9语义及/error、/app无公共壳两项均实际RED后修复，Root最终完整治理2116PASS/3SKIP、531subtests及Node/Ruff全0、851输入保持，243原整文件及独审CLEAR；当时正式5旅程未通过，后继Root4e603743原正式5/5已验，TLS噪音未证与此因果 | T-05/T-13 |
| I-56 | HTTPS原生Cookie安全模式跨层不一致 | VERIFIED（组件及正式浏览器主路径）/G1整体OPEN：三仓及Root候选冻结/交叉CLEAR；IAM完整1695/真实482/clean consumer2、BFF完整工程及真实PG423、App完整6399、Root治理2135/3SKIP均有停写证据。实际HTTPS删除已从非Secure3→过滤0纠正为Secure3→保留3，原真实relay1通过且source/DB保持/全回收。三owner已推原PR，Root4e603743精确配对后原正式五旅程5/5通过；不放宽安全过滤/精确401，后继inspection及组合负控亦通过，完整G1按当前冻结组合收口 | T-01/T-05/T-09 |
| I-57 | 独立撤销focus跨document证据及匿名最终跳转oracle | VERIFIED（原正式5）：Root4e603743原五旅程5/5，严格原broker和四源/Node精确，cleanup/scan通过；真实anonymous canonical sign-in/私有canary及trusted ACK已通过整批。原P2清理预算实际RED后修复，同3秒/strict响应/I55/五旅程/401/175秒/60秒保持。此前07c超时、聚焦不完整/更早Adminbuild失败均保留；最新run无命令失败，不伪称旧Admin失败根因已查清 | T-05/T-09 |

---

## 2. Goal 与原 Task A 对齐

### 2.1 机器 Goal 与阶段目标

旧 Goal 已由用户清除；主窗口按最新请求和根目录 todo.md 新建并核验机器 Goal 为 **active**，范围仍是 C-1.3～C-4，A-01/A-02/A-07 保持门控。不以阶段通过提前 complete。

| 阶段目标 | 状态 | 可核验的完成条件 |
| --- | --- | --- |
| G0 设计门 | 认证D0设计面主方复核通过；Nest/owner决定保留 | IAM0.20及BFF安全状态/relay候选机器合同已沿原PR交付；消费者及新组合另验，不以设计门或旧artifact代替G1 |
| G-DOC 当前方案与追踪 | VERIFIED（文档基线） | 初始17问题/17TODO及A-01～A-16已独审；执行中新发现T-18同步登记，状态持续更新；不算产品完成 |
| G1 C-1.3 认证切换 | VERIFIED（当前冻结组合） | 正式五旅程、账户消费、真实包producer/原四GET及组合负控通过；当前旧认证零目标消费者与T14 receiver处置已核，主方及独审确认；未来组合变更按影响回归 |
| G2 C-2/C-3 清理 | VERIFIED | T‑17、旧入口退役、四项归并和 ScheduledTask、Chat、Projects 三项拆分验收；已纳入 C‑4 精确组合。 |
| G3 C-4 与同步端到端 | VERIFIED（前置门） | 已发布契约和组合通过；原生浏览器收据复用，I‑15 同库八 owner 联合 readiness 已实证并回收；严格结构历史红项照实保留，无新增未处置。不是全产品验收。 |
| G-A 产品后续 | OPEN | A‑01/A‑02 先推进，之后 A‑07；其他 A 任务按原范围领取。 |

### 2.2 A-01～A-16，不缩小原任务

| 原任务 | 功能 | 本轮定位 / 后继验收 |
| --- | --- | --- |
| A-01 | 会话创建与恢复 | GATED；先 localDraft→owner create/retry→URL/刷新/前后退/多标签/迟到响应 |
| A-02 | Agent过程与详情展示 | GATED；唯一AG-UI/RunDisplay，live/终态/历史一致，真实详情不补造 |
| A-03 | 输入框与运行控制 | 后续backlog；IME、队列、审批、停止/继续、重连与一次意图一次执行 |
| A-04 | 执行正确性与恢复 | 后续backlog；worker/lease/checkpoint/journal/outbox恢复不重复副作用 |
| A-05 | 长上下文压缩 | 后续backlog；当前长会话/工具/取消/恢复，私有capsule不进入公开面 |
| A-06 | 项目概览与上下文 | 后续backlog；指令/pin/资源/Skill引用、菜单、删除释放与回读 |
| A-07 | Project Todo | GATED，A-01/A-02之后；BFF项目任务CRUD/权限/CAS/幂等→generated client→App，不把Run Todo改名 |
| A-08 | 附件与上下文引用 | 后续backlog；选择→发送→Run资格→真实内容→刷新恢复 |
| A-09 | 资料库 | 后续backlog；上传/扫描/分页/下载/删除/来源回跳 |
| A-10 | 文件/产物/Canvas | 后续backlog；正确Run/版本/权限、完整内容、窄屏与键盘 |
| A-11 | 首页与创建场景 | 后续backlog；只交付真实支持入口，Manus同状态对照 |
| A-12 | 自动化 | 后续backlog，先核原writer；CRUD/时区/DST/到点执行/重投结果闭环 |
| A-13 | Agent与外部聊天应用 | 后续backlog；已有能力真实owner/callback/过期状态，不增加未裁决能力 |
| A-14 | 语音输入 | 后续backlog；真实麦克风/转写/拒绝/取消，不用演示文本 |
| A-15 | 体验与性能 | 随产品切片验收；响应式/回焦/真实延迟，不藏加载或伪造成功 |
| A-16 | 文档、PR、合并与运行配对 | 随片交付；Root/App/BFF/IAM/Capability各自draft PR，旧冻结组合已精确配对；当前候选 gitlink、最终验收/运行配对仍待；未merge或上线 |

Task B 继续拥有能力配置/授权/安装、账户协作等业务；Task A 使用其固定契约与真实资格。`global_register` 属原 C-1.3 已批准清理依赖，不借此接管整个 Task B。

---

## 3. 技术方案与逻辑闭环

### 3.1 C-1.3：撤销前行为/证据基线（新设计以§3.6为准）

以下保留原阶段链路与验证语境，不作为用户推翻后的目标实现依据；有效业务隔离/权限/事务保障仍须承接，不照搬认证材料传递。

```text
Browser → App same-origin adapter → BFF native admission → IAM fresh session/tenant/membership
                                  → named feature → owner API/RPC → owner facts
                                  ← canonical result / receipt ←
Browser ← App UI 与刷新后的同一事实
```

- IAM拥有cookie/session/active tenant/revocation；App只转发allowlist cookie、Origin、request-id与取消；BFF冻结可信身份，body自报身份不参与授权。原生认证协议不强套业务API命名。
- 四旅程按既有固定Product tenant裁决验收：真实冷登录→固定域session/业务读取；由IAM合法测试通道使会话进入异tenant→当前App/BFF立即拒绝且不读写外域，返回固定tenant后恢复；App登出→旧cookie失效；独立撤销session/membership→已开页面下一次请求拒绝。跨标签迟到响应不串身份。不是同App跨tenant正向产品切换，不新建已删除的Team selector。
- T-05测试协议纠偏（2026-11-02真实RED＋owner源码/数据设计确认）：原生退出将Session到期并撤销派生凭据，保留expired tombstone；不能以物理row消失作为退出条件。私有inspect保留exists=物理row，并加unexpired=该exact row的expiresAt>now；退出应为exists=true/unexpired=false及原生get-session null、BFF旧cookie401。独立fixture exact-session删除为exists=false/unexpired=false；仅撤fixed membership时B session仍exists/unexpired=true、member=false且业务拒绝。owner active_tenant按物理row记录，不因到期伪改none。此变更限测试协议与oracle，不修改生产撤销语义。
- App当前native投影没有tenant标记；同subject切tenant后的页面与在途请求退休是待验证风险，不据源码直接认定正确或新增一套身份协议。IAM `verify`不含真实integration；App默认Playwright开启session preview，另设真实配置旅程后才能引用为认证证据。
- 负控：匿名、错Origin、伪造tenant/subject、失效/错surface服务身份、重复登出、撤权后旧请求、IAM不可用；拒绝时零越权owner写入，未知结果不补成功。
- `run_web_native_session_smoke.py`的**默认模式仍只是三服务最小HTTP smoke**：fixture给现成native cookie→`/api/auth/session`→`/api/session/projects`→fixture直接IAM signout后401，加日志检查共4case。不是浏览器登录，不覆盖tenant切换、App登出、独立revocation或全部owner。 显式`--browser-journeys`已在d309加入永久四旅程，dd447加入脱敏失败位置；最早cold_login失败见I-26，当前正式运行已进入第四旅程并由I-33续接；不把模式已实现当验收通过。
- `global_register`：先核真实producer与接收方写区。Capability复用既有direct service credential校验与无tenant/caller/surface规则，承接注册授权/幂等/取消，再删除该surface的OAuth分支及专用消费配置；第三方MCP OAuth、IAM公共OAuth与Billing资金授权保持。调用方待证不新增无需求服务。
- T-14盘点补充：Capability当前RPC接收方真实可写，但冻结v9 manifest仍inactive/routable=false，注册profile身份段还是operator_machine。认证切换需owner单一当前auth profile明确替代旧身份语义并校验provenance，不修改冻结v9或借机激活它；三面设计已审；实现已以f515提交并完成Root完整门及真实接收方验证，派生auth-source索引/原policy与schema单一事实源已纳入；最新base整合仍须重新验证。System当前src/scripts/contract未见producer，仅receiver与测试client存在，证据称接收方切换，不称System业务链完成。
- T-14局部取消风险：已提交44fcc5d的register handler/service未传caller boundary，PrismaMcpTransaction.runGlobal使用无caller取消的transaction request。现冻结候选已传递既有boundary，并补授权后/provider等待中取消→零入库的回归并承接现有boundary；其余MCP业务不顺手重写。direct credential没有TTL字段，不凭空增加过期机制；测试覆盖旧OAuth拒绝与文件删除/轮换即时失效。
- 本片不新增数据模型、第二认证协议、token镜像或Root可编辑contract；需要变更wire/schema时先由owner补相应设计面和机器契约，再串行交给消费者。

### 3.2 C-2：从入口隔离走到真正删除

1. 已提交173e026承接原11文件候选，Root已确认该子集只去掉`main.ts` raw re-export/两处type倒依赖、迁6个测试import并补默认门；不把它写成最终删除。
2. 先核Nest生命周期：`src/main.ts`、`src/common/database/database.module.ts`及现Redis/worker provider。用真实`TestingModule`/应用关闭验证停止接收、worker drain、SSE取消、超时上界、池与监听释放；不新增第二bootstrap或万能Lifecycle总管。
   BFF4d6已加入真实生产AppModule的`TestingModule.compile()`与关键token单实例回归；该启动/装配证据不替代实际应用shutdown、drain与资源释放行为。
   2026-11-02只读复核（BFF4d6，非运行验收）：当前main未启锁定Nest adapter的return503OnClosing；worker只接onApplicationShutdown，处于HTTP dispose之后；数据库owner仅普通close无Nest hook，pool.end失败可能阻止Redis关闭；旧signal31秒上界只被raw测试消费。先在生产Nest上复现关闭准入/SSE/worker失败与卡住/PG-Redis释放，保留旧风险保障；不因本静态发现提前实施G1后的清理或新增万能lifecycle总管。
   2026-11-02后继只读核对已确认锁定Nest源码实际顺序为destroy→beforeShutdown→adapter dispose→applicationShutdown；当前四worker的stop在最后阶段，DatabaseModule工厂产物只有普通close、无Nest hook，且pool.end失败会跳过Redis关闭。旧`test/lifecycle.test.ts`的HTTP/worker drain、恰一次close及SIGINT/SIGTERM/失败/永不完成期限用例仍测raw或旧signal handler，不能作为生产Nest证据；现Nest compile测试不替代listen/close。G1后首片直接用真实AppModule/listener与窄provider override复现drain→Pool/Redis释放，不新建通用harness；活动SSE取消另有独有缺口，不声称raw已覆盖。
   **T17 活动AG-UI传输退役设计门（五源码候选已验，未提交；不含完整T17）：**
   - `AGUI_RUNTIME` 仍是唯一feature owner；匹配events路由后、首次await前跟踪匿名HTTP handler的实际settlement，覆盖准入、授权预读、consumer-register和SSE，不增加身份、SessionRef、票据或持久事实。Native route可直接组合既有authenticateBrowserRequest/writeSessionCookies，在物理verify返回后先核signal再写合法Cookie；授权helper以现options中的标准可选signal逐await检查，SSE必须传入，其他caller/预算不伪造或扩写。
   - 复用原生AbortController/AbortSignal及现Message route的caller接线方式；IAM客户端已支持signal，不改认证。单客户端断连只退役本handler，不取消同session其他客户端、shared wait/replay；runtime停机才全退役。
   - 现runtime factory实例的`onModuleDestroy`先封闭新登记并广播transport-only退役，再等已登记handler真实finally；此阶段早于worker的beforeShutdown，不依赖跨module顺序，不新增全局LifecycleManager。
   - 各await前后检查取消，退役后不新发register/replay/status或晚写响应；已开始的授权查询、注册事务或shared replay/status等待物理工作完成，不以Promise.race先返回冒称settle，也不关闭共享pool来取消单请求。
   - shared ledger wait保持tenant/session合并；单waiter取消不撤其他waiter，最后waiter离开或runtime关闭才清自有timer。shared replay不绑定单客户端signal。writer背压可由传输signal唤醒并清监听。
   - 保留原10秒admission阶段预算及stream容量/frame/byte/duration预算；停机硬期限仍归唯一进程owner。挂住PG必须如实进入硬期限/异常出口，不伪称已回收。
   - 只退役传输、监听、等待和connection lease；不cancel Run，不造terminal/frame/cursor，不改consumer持久语义，恢复仍用原ledger与Last-Event-ID。目标写区限定现runtime、chat-events-native、events stream、writer、chat-authorization的标准signal检查及原三测试；新传输/Schema/SDK/锁均不需要。
   验收分别承接：实际Nest listener下的前连接(admission/register)与在途物理读取两阶段、同session多客户端隔离、writer背压；零越权/未授权projection、原cursor恢复与lease恰次释放保留。依旧先原测试RED→主方复现→最小source，不将测试替身称真实IAM/PG。
   **有限失败切片（原五hook候选已验，未提交；主进程后继未验）：** Nest12会记录并吞有限hook异常，app.close resolve不是成功退出证据。只在现feature hook按原顺序尝试所有独立stop，有限失败不跳过后续stop；将原始cause替换为稳定安全类别，并在所属hook设置单调非零进程退出状态。数据库正常/幂等/失败尽力close不重做，只补Nest hook失败状态承接。原Nest测试先用真实AppModule重现同步抛错/拒绝、原始canary不泄露、余下worker和Pool/Redis恰次清理；测试收回临时进程状态，不给default suite遗留exitCode。挂起、真实main信号/初始化竞态及30/31秒owner仍是后继，不以本有限失败slice冒完整退出保障；不新增全局manager、重试或并行化既有有序stop。
   **T17唯一进程owner目标（尚未实现）：** Root已用真实`node dist/main.js`、自有fresh BFF schema及受管PG/Redis复现正常SIGINT/SIGTERM的既定出口差异：health/ready均200，但返回-2/-15而非0；只说明正常退出策略差异，不冒清理失败。private `kokoro-t17-main-entry-signal-red-xyo6o_51/result.json`记录source/dist保持、资源全回收/DB清单保持。后继只在现main建立一个薄`startBffApplication`，由真实bootstrap直接调用，同一函数负责init/listen、信号与一次memoized公开app.close；删除无生产消费者的旧fake ShutdownServer信号入口，不与enableShutdownHooks双注册，不新增文件/全局manager。
   - 第一终止请求即启动referenced 31秒硬期限，30秒仅通过现HTTP server公开能力强制收口连接；重复信号在整个终止期忽略，挂起到deadline固定安全诊断/exit1，不冒已drain或提前关仍被I/O使用的Pool。生产30/31秒保持；同一函数允许测试显式短预算，不加env测试flag。
   - 明确跟踪当前init/listen真实Promise，终止等待其settle后才close；初始化结束后若已要求关闭就不再listen。after-create启动失败走同一关闭出口；有限失败非零latch不被成功分支写回0。只使用Nest公开API，保留feature stop/DB末期释放边界，不复制另一套runtime。
   - 原lifecycle fake `{shutdown}` child测试迁真实AppModule/实际Nest listener并调用同一生产owner，覆盖正常/重复信号、代表有限失败、worker/Pool/Redis挂起及启动失败；不将缺新函数的收集错误当行为RED。Root已有真实文件入口RED，后续须同资源fixture复跑实际main及31秒保障，不能只由导出helper测试自证bootstrap接线。原raw行为测试等T11有效风险全部承接后才删。
3. 依据原provider图按feature迁移测试消费者到Nest入口/override provider。每个批次明确旧测试风险→新测试位置：身份、错误、body/SSE、取消、幂等、并发、恢复一项不丢。通用helper只承载启动关闭，不暴露global business store。
   **2026-11-03当前T11只读核量（未实施）：** 三个历史aggregate class定义、LegacyRoutes实现及GracefulShutdown均已删除，不重复计作待删。实际剩余为bootstrap两文件及`createPostgresBffOwnerResources`宽factory。T17完整收口后，先迁原`personal-knowledge.integration.mjs`单文件到Account owner Nest，再按原owner迁archived-tasks、scheduler-dispatch-receipt、business-store、chat-facts、agui-http六文件的53处HTTP相关factory调用；不是53个新测试，不另建harness。另三纯PG文件的49处仍在最低充分repository层显式装配，不抬成HTTP。剩余mockBusiness HTTP fixture和三个直接composition消费者按feature后继迁移，合法Repository/Port保留。部分名字含native的旧测试只是node server/handler，不冒真实Nest证据。
   IAM旧PlatformWorkload退休还须同步AuthModule/guard/setup、canonical内省operation和正规SDK生成及原fixture，不是只删Controller/Service；保合法通用OAuth等能力，固定历史snapshot/拒绝测试不追字符串清零。Root现`run_web_chat_gc_chromium_smoke.py`的旧class调用归T09/I23已知脚本漂移；raw唯一protobuf text编码初始化须在删除前明确原有效契约的Nest承接位置，不静默丢失副作用。
4. 最后扫描生产、test、scripts、package默认入口，零消费者后删除`src/bootstrap/server.ts`、`src/bootstrap/runtime.ts`、旧dispatcher/相关helpers。不要把旧文件搬到test目录永久保留另一套运行时。
5. 编译、contract、真实I/O及新图行为共同验收；源码字面扫描仅辅助，不靠名字改动或注释匹配证明边界。

### 3.3 C-3：Repository / Service / Port 按真实职责处置

复用原[完整disposition](../specs/2026-10-30-task-a-cleanup-inventory.md)和[provider census](../evidence/2026-10-31-task-a-c3-provider-census.md)，逐项更新结论，不另建一套DTO/层。

| 当前对象 | 目标处置 | 保留风险与验收 |
| --- | --- | --- |
| `createBffComposition` / `BffRuntimeStore` / raw dispatch | 消费者迁移后删除 | 不能只删旧class后改名保留aggregate |
| `createPostgresBffOwnerResources`及9套integration消费者 | 审计聚合职责，改为显式feature/test资源装配后消除无边界locator | 不靠工厂改名完成；每个pool/notify/receipt调用归到实际owner |
| Chat/Projects/ScheduledTask/AG-UI/Idempotency等复杂Repository | 保留必要feature-local持久化边界 | 事务、锁/CAS、lease/outbox、ledger/replay、复杂查询真实存在 |
| 仅转发一次的Service/Port、简单CRUD重复层 | 并入当前feature provider或删除 | 保留授权/错误/取消策略，不因“一实现”删除真实边界 |
| 全局idempotency contract | 审核为有真实跨feature语义的共享契约或迁到合适位置 | 不按目录名机械清零，不再塞其他业务能力 |

删除闭环为：**列消费者→确认替代事实→迁移风险测试→切生产与测试引用→删除旧项→零引用/编译/行为复验**。缺替代事实时保持OPEN，不造空实现或删断言换绿色。

### 3.4 C-4：契约、默认门与运行资源

- App Public28.18 原件来自BFF `091cd5022cf517d243a6390b933f9dded7e3b4a9`，SHA256 `35a86f91e44beb1aeb6b17eca41d3bfdc79f11a43633662113a1778b4fab6082`。增量只有profile GET/response schema/version，原199操作顺序保持，新版200。候选使用原生成器与严格全文28.18→28.17逆证，旧父hash、private/policy快照不动。
- BFF默认入口纳入现有两套Nest架构测试；删除实现耦合/失效测试前证明风险已由当前行为测试承接。格式失败是门失败，不降格“非阻断历史”。
- Node必须匹配owner engines。App候选门用22.23.4，runner候选已更新App为22.23.4、BFF/IAM24.20.0；BFF七条生成链/CI/Docker已对齐24.20.0并通过Root完整门。收据另分期望与实际版本，失败阶段不伪造已验证版本。
- 复用受管PostgreSQL/Redis。前序只读连接/PING成功仅证明可连接；不证明当前完整配置、Schema、身份与业务就绪。凭据只在私有配置，不写文档/参数日志/收据。
- 应用目标是一实例、一数据库、一套应用credential、每owner独立schema；测试临时库只是隔离。核installer/URL对schema的支持，禁止跨owner表访问或reset共享DB/Redis。
- T-13资源归属补充设计：现native IAM fixture只随机分配资源，Root全局前后差集会误归属并发测试。复用IAM fixture现有`resourceId/resourceOwnerToken`、Redis NX marker和named DB机制，允许`bff-session-admission-host`在固定webOrigin下传入两环境字段；旧Web host行为保持。Root只核该run精确DB/prefix与匹配owner marker，不删除未知身份资源。写区限`test/fixtures/bff-session-admission-host.ts`、`test/fixtures/internal-http-application.ts`及现有host integration测试；无公开API/Schema/业务变更，真实I/O由Root验收。补充批准`test/unit/bff-session-admission-host-resources.test.ts`仅覆盖无资源非法env的子进程fail-fast/脱敏；真实named资源/碰撞/中断仍由integration验证。
- 复用现有runner/资源helper补清理，不新建通用编排平台。全部进程/proxy/reader/自有DB/Redis均尝试关闭且汇总失败；未quiescent时保留其依赖资源并报告。收据保存source SHA、stage、结果、资源清理状态，去掉cookie、secret与敏感payload；失败也留脱敏索引。

### 3.5 分层端到端与同步测试交付

| 层级 | 依赖 / 验收 | 结论边界 |
| --- | --- | --- |
| L0 静态/契约 | owner完整命令、生成物、架构图 | 不证明进程运行 |
| L1 隔离最小native | 复用PG/Redis → IAM fixture → BFF → App；真实同源HTTP | 只证明所测session/projects/signout检查，不替代四旅程 |
| L2 C-1.3完整旅程 | 同一冻结组合的真实App浏览器固定域登录/异tenant拒绝与恢复/登出/撤权与负控；Capability接收方独立真实fixture | 形成当前认证闭环；不扩为全产品验收 |
| L3 受影响业务组合 | 按具体旅程增加System/Capability/Storage/Billing/Scheduler/Agent worker等实际依赖，Admin/Mori仅有受影响路径时加入 | health与业务结果分别记录；不为“全部启动”盲开服务，不假定每个owner都支持匿名readyz |
| L4 用户同步测试 | Root交付已验证源码组合、无秘密的访问入口/可测范围、私有日志索引、启动/停止归属、已知缺口 | 临时smoke已退出的进程不算常驻可测环境；本轮尚未交付该状态 |

启动顺序由实际调用依赖和owner README决定，先提供方后消费者；关闭反向且只停止本任务拥有的进程。已有用户预览与共享基础设施不重启。同步环境的保留/清理策略在后续运行阶段明确，不把PID/凭据写进版本文档。

---

### 3.6 认证标准重设计：I-38 引用方案已否决，认证 D0 已通过

**当前裁决。** 用户已明确否决“请求内Session引用”，要求按后端标准推翻重来；旧A/B问题结束，不继续请求委托信任批准，也不自动恢复“每个IAM业务操作再验Cookie”的旧设计。此前把自定义会话证明贯穿业务接口并靠测试/内部审查证明其合理性的做法已撤回。源码只用于辨识消费者、迁移成本和必须承接的业务行为，不作为目标设计依据。

#### 已执行的撤销，不是整体认证已闭环

- IAM基线`285dfcb`：12个本轮引用candidate文件已逐路径恢复HEAD，包含源码、生成源/OpenAPI/profile/SDK和仅服务该candidate的测试；引用header/分流/repository入口零残留。六份IAM/BFF owner I-38设计前缀已删除，改为明确撤销通知；I29历史后缀原字节保留，但不再是新设计的放行依据。
- BFF`b6d98f8`、App`fdbb49f`的源码本轮未重写；既存Cookie搬运、空Bearer/假claims/wrapper风险仍是待替换对象，不因为撤销candidate而视为正确。Agent与其他任务、原Root gitlink均未改。
- I-37 SDK Bearer只供Bearer scheme、I-36有价值测试清理及原业务权限/事务保障保留。撤销后IAM完整`pnpm verify`exit0、125文件/1652通过；旧引用候选16/1656仅为已撤输入的历史工程证据，不作新架构正确性证明。BFF/App源码保持时不无意义重跑全门。

撤销最终收据：三个子仓当前只有Markdown diff，source/generated/test均与各自HEAD一致；六owner历史后缀原字节保持。额外发现BFF ignored dist仍含早先引用构建物，确认候选工作树无Node消费者后按HEAD源码重建，build exit0；源码与IAM/BFF实际构建输出的引用header/helper扫描均零残留。Root/子仓diff-check与97个本地链接通过。新§3.6经独立标准复核，限文档一致性通过，不代表新认证G0或实现验收。

#### 标准依据与项目取舍分开

| 依据 | 可据此确定的边界 | 不从中推导的结论 |
| --- | --- | --- |
| [RFC10017 §6.1 / §7.1](https://www.rfc-editor.org/rfc/rfc10017.html)（2026-08正式BCP） | OAuth-BFF是机密客户端、服务端保管token并向资源服务使用access token；同源第一方也可使用普通服务端Session | 不是所有同源应用都必须OAuth；也不是任意自创引用协议都叫标准BFF |
| [OIDC Core](https://openid.net/specs/openid-connect-core-1_0.html)、[RFC9700](https://www.rfc-editor.org/rfc/rfc9700.html) | 选用OIDC时采用标准Code/PKCE与客户端/回调/issuer/audience校验，令牌不当作任意服务身份 | ID token、JWKS可用或未到TTL不等于会话当前未撤销 |
| [Better Auth原生Session](https://better-auth.com/docs/concepts/session-management)、[Server API](https://better-auth.com/docs/concepts/api) | 框架拥有登录/HttpOnly Cookie/Session生命周期；IAM进程内调用自己的官方API，不复制框架算法 | 不为适配旧App模型造空access、generation或60秒有效期；需要在线撤销语义时不信任cookie cache的旧允许结果 |
| [Nest认证/授权分离](https://docs.nestjs.com/security/authorization)与本仓TS/API手册 | 入口认证建立可信principal；Guard/handler/业务policy分别承担职责，业务逻辑不处理浏览器凭据 | 教程不是安装新认证包/权限中心的许可；也不要求每表一层或通用SDK |
| 现有效ADR-034/035 | Product/Admin共享登录；内部接收方验证专用服务身份，BFF建立可信用户上下文；IAM拥有权限事实 | 内部机器零OAuth不等于禁止人类OIDC登录；服务凭据也不自动授予管理员/资金/任意用户权限 |

#### 重设计的确定边界

1. **浏览器认证**是唯一处理Cookie/登录Session的边界。App只做同源UI/adapter，不伪造Session claims；Product/Admin共享同一登录，不各建一套认证。框架Session cookie本身与自创跨服务Session引用不同。
2. **业务入口**通过框架认证结果建立真实用户上下文（subject、可信tenant及请求关联），而不是`user_delegated`伪scope、占位client/session、空Bearer等兼容形状。失败/依赖故障区分；浏览器自报body/header身份不参与authority。
3. **服务身份**由接收owner验证独立caller/surface/tenant凭据与允许的调用边界；网络内网或自报user_id不是认证。采用入口Session路线时，跨owner承接受信入口派生的actor/subject/tenant，这是需明确约束的项目委托；采用完整OAuth-BFF路线时，资源服务器须消费并验证标准用户access token，不是只信gateway身份头。两者不能混称。任何路线均不另造Session引用/票据/自签证明或共享认证SDK；具体owner合同在G0中固定。
4. **业务授权**由IAM鲜读User/tenant/member/role/operator事实，各数据owner检查自身资源、状态和写入权限；普通业务不接Cookie/浏览器Session ID，不每个方法再跑登录流程。登录Session检查留在认证边界，业务事务保当前成员/权限、CAS/last-owner/审计等真正不变量。
5. **资源ID不混淆**：账户设备/会话管理的目标session_id、Chat/Run的conversation/execution session_id仍是原业务资源；不按字符串全删。它们不承担通用登录凭据职责。
6. **执行/资金**继续独立Run/proof/lease/预算授权，不因网页登录重做删除。第三方MCP OAuth、合法公共API Key/OpenApp、owner生成client及真实SDK消费者保留，不为包名或测试数量机械删减。

#### 两条有官方依据的接入路线（内部委托为项目设计）与工程建议

- **框架原生服务端Session、统一入口认证**：IAM仍唯一会话权威，使用其官方认证能力；认证后业务只处理受信用户上下文/原policy，无业务Cookie/Session proof。认证边缘拟固定在Nest BFF（App仅薄adapter，IAM持有框架实例/Session事实）；每个受保护请求按IAM当前会话鲜验，必要私有交付前重验，关闭/跳过允许结果缓存。普通业务下游不接登录Session；撤销后的下一请求在边缘拒绝，撤销前已认证的在途请求不承诺跨owner全局原子终止，成员/权限变化仍在原业务事务复核。本项目已确认同源Product/Admin、固定tenant，尚未有必须另建RP会话/refresh存储的需求；因此推荐从这条边界完成设计，而不是沿旧native-admission/业务Cookie代码补洞。这是需求驱动的工程建议，非框架强制或旧代码投入理由。
- **完整标准OAuth/OIDC-BFF**：若明确需要独立登录安全域、联邦IdP或独立资源服务器访问，则定义唯一RP/session owner，按Code+PKCE/服务端token/资源服务器access token完整设计；不恢复旧Auth.js generation/handoff实现，不把“只用OIDC登录＋内部委托”混称完整OAuth-BFF。必须定义撤销时效：资源服务器可按[RFC7662](https://www.rfc-editor.org/rfc/rfc7662.html)用直接客户端凭据在线检查**人类access token**的active，AS将其绑定当前grant/session及资格，且不缓存允许结果；不需要先mint机器token。这可实现撤销提交后下一次资源请求拒绝，但绑定/新鲜度是项目契约，并非OAuth自动保证。[Back-Channel Logout](https://openid.net/specs/openid-connect-backchannel-1_0.html)另负责RP会话退休，不以TTL或异步通知空口保证即时拒绝。

两条路线都不包含已否决的Session引用，也不把旧“逐业务Cookie验证”当选项。当前先固定认证owner、唯一入口、撤销时效和服务/用户上下文边界的完整设计；新协议/owner/数据影响通过G0前，不先写新运行时代码或发行契约。若采用第二路线，修订受影响ADR/数据设计并说明新会话/令牌存储的必要性，不能偷偷叠一层。

#### 本轮收敛的技术方案候选（D0，尚非实现完成）

采用上面的**原生服务端Session＋入口认证**路线，沿用ADR-035已确定的接收方服务认证与可信BFF上下文；不因内部机器不走OAuth而再造一种用户票据。完整OAuth/OIDC-BFF保留为不同需求下的独立方案，不混入当前实现。下列HTTP字段是项目受信网关契约，不是RFC规定的跨服务用户凭据。

```text
浏览器 ──HttpOnly Cookie / CSRF──> App同源薄适配 ──> BFF认证边缘
                                                    │
                                      IAM Better Auth官方get-session
                                                    │ 真实用户
                                                    ▼
                           BFF业务用例 ──独立服务身份＋用户上下文──> owner
                                                                     │
                                                         当前权限＋资源＋事务
```

| 设计面 | 固定候选与职责 | 明确不做 |
| --- | --- | --- |
| IAM框架认证 | 锁定Better Auth 1.7.3原生`GET /iam/get-session`，消费已有upstream snapshot；业务入口检查使用官方`disableCookieCache=true&disableRefresh=true`。认证client立即安全挑选真实User/active tenant/expiry，原始token不越过认证adapter | 不建新的admission成功协议，不手改upstream snapshot，不补假client/scope/Session ID |
| 真实用户投影 | IAM的`platformAdmin`使用正式additionalFields输出配置、仍禁止客户端输入；这是全局原生User输出增量（含注册/防枚举），BFF现strict注册消费者须按正式生成形状窄pick承接并回归邀请注册，不只改get-session。供UI及BFF既有global-admin gate使用，非浏览器自报权限；私有version完整性由IAM官方认证投影检查。BFF普通业务principal只有真实userId/tenantId，具体action/资源当前policy仍由IAM及相应owner判断 | 不默认补false、空access、generation0、固定60秒TTL；不把UI管理员位当业务授权 |
| BFF装配 | 一个AuthenticationModule显式导出同一个认证provider；现会先终止响应的feature middleware直接调用该provider，Controller/Guard复用，不新设全局允许缓存 | 不把provider藏AccountModule、不加@Global/locator/broker，不误以为全局Guard覆盖middleware |
| IAM业务（17项BFF第一方调用模式） | 独立服务Bearer、固定`kokoro-bff/bff_user_context/tenant`凭据记录；仅成功认证该caller/用途后接受单值`x-kokoro-actor-id`，subject=actor。浏览器身份头丢弃，tenant不能覆盖凭据；内部生成client只传这些业务metadata | BFF该业务模式不带Cookie、Origin、登录Session引用/ID、用户Bearer；失败不fallback OAuth/native，无万能共享SDK |
| 当前业务授权 | IAM在原事务读取真实User、active Tenant、Member及本操作所需role/action/operator。Product成员门复用现`checkAuthorization tenant/read`的受信actor分支，只查核心成员事实，不附带扫描所有动态角色；具体业务原policy不放宽 | 不因服务凭据正确跳过成员/资源/last-owner/CAS/审计；不把普通成员门扩大为全角色完整性门 |
| 单一浏览器状态 | BFF拥有`GET /browser/v1/auth/session`机器契约；200的strict `data`为匿名`{authenticated:false}`或真实`{authenticated:true,subject,tenant_id,expires_at}`（RFC3339）；request ID只在响应header，不新加JSON meta。资格403、依赖/坏响应503，no-store。公开`/v1/me`三字段不变 | 无token、Session引用、generation、内部Session ID；App只正规生成消费，不能再手写近似decoder |
| 续期与RSC | 状态GET的普通`refresh`查询默认true，HTTP Route Handler完整传递框架多条Set-Cookie；RSC显式false，BFF转换官方双true，不rolling。业务入口一律不rolling。失效Cookie/过期Session清理仍可能写，RSC不能声称已回写浏览器；不透传`set-auth-jwt` | 不逗号合并Cookie、不把RSC当可写Cookie边界，不新增第二状态接口；不把无rolling说成绝对零写 |
| App/Admin | 普通同源业务adapter一次BFF请求，不再`me→业务→me`。App初始只读观察注入完整安全状态；Admin同源`/manage`消费同一登录与状态，不再独立csrf/refresh/store | 不制造Session claims，不新加RP/session/token存储，不改管理业务功能 |
| 浏览器寿命 | 保留真实UI epoch/AbortSignal/ABA/pagehide与跨标签无秘密失效通知；它只退休迟到结果，不进入认证wire。401只恢复允许的读，unknown写不自动重放 | 不把subject相同当同一Session，不宣称外部撤销可瞬时清除无推送的全部旧展示 |

**信任边界必须说清：**受信BFF负责断言它刚认证的actor，IAM负责当前业务许可。若BFF的该用途服务凭据及运行时失陷，就可能在其固定tenant内冒充actor；这是ADR-035的受信入口模型，不是用户密码学证明，更不通过换名为“上下文”消除这一风险。凭据按receiver/purpose分隔、严格peer/route/tenant允许边界；仅持通用服务凭据不进入这些操作。若要求IAM独立验证每个用户的委托凭据，应整体采用标准OAuth用户access token路线，而不是再塞Session引用。

**operation与调用模式不可混淆：**17项是本次BFF第一方模式的迁移面，不是把整个IAM operation改为全局direct-only。当前正式SDK仓外consumer的`tenant.checkAuthorization(tenant/read)`是合法machine OAuth成功正控（真实token/HTTP，allowed=true）；Team/Skills/MCP/OpenApp也存在不要求Product client的有效OAuth权限路径。它们继续按正式client/scope/Session/permission合同工作，不能因为新BFF不用OAuth就批量删security、JWT verifier或shared当前事实helper；第一方新模式失败仍不回退到这些独立模式。真正Product绑定的AccountProfile/Publisher与目标App注册client约束分别处置。非19目标中的APIKey管理三操作仍保现有效Product OAuth合同，本片不冒其控制面已闭环；Product配置必须按消费者处置，而非按名字全删。后继owner必须逐operation声明身份模式与负控，避免让旧fixture决定目标或把有效协议当冗余测试删除。

**会话管理属于认证生命周期，而非普通业务：**账户会话list/revoke两项由IAM具名认证adapter校验原生Cookie，保持IAM对caller Session/current、当前设备删除保护、锁排序、target撤销/tombstone/审计的真实责任；不把当前Session引用送进普通业务接口。其业务资源session_id保留。保留现`/internal/v1/account/sessions`与`/{session_id}`路径；由AuthModule具名AccountSessionGuard先校独立`kokoro-bff/account_sessions/tenant`接收方凭据，再校exact Origin与官方get-session双true，不接actor头/外部caller sid/人类Bearer。Browser→BFF写入CSRF与IAM精确Origin/歧义header拒绝均保留；正式AND认证合同先发行，再由BFF具名认证adapter固定消费，不让通用SDK自动携Cookie。cursor继续绑定真实actor/tenant/current Session与keyset，移除伪OAuth client绑定，正式cursor v2；旧v1明确400从首屏重读，不误报401、不恢复旧OAuth配置或fallback。**删除前稿的all-active＋BFF current投影＋额外分页补读**：清理认证搬运不要求转移会话资源owner或弱化其事务保障。第一方BFF的17项业务调用采用服务身份＋actor，认证生命周期使用框架Cookie，两者不混合fallback。Invitation等真实认证交互、独立OAuth/API Key、Chat/Run资源ID同样不在机械删除范围。

**账户专属OAuth scope处置（2026-11-03收口）：**两账户API改peer＋Cookie后，专属scope扩展/seal管理命令及AccountProfile对该pair的假前置退休；新登记输入不再接受该pair。已存client读取与已发行access/refresh、旧登记默认scope仍保原完整wire/原序及当前有效OAuth权限复核，退休pair只是无权标签，绝不通过新账户准入。不清历史DB、不偷偷filter或改grant，不因账户清理破坏Profile/APIKey等独立OAuth；确有持久/claim读取消费者的精确标签集合按事实保留，不作认证fallback或通用legacy框架。

**撤销时效：**每个受保护请求入口重新检查IAM Session；撤销提交后的下一次检查拒绝。已在途业务不承诺和IAM登录Session行跨owner全局原子排序；当前成员/管理员/业务资源变化仍在原owner事务和必要发送/派发前复核。保留真正的取消、unknown、receipt和原key/body恢复，删除的是旧证明材料，不是这些行为。

#### 落地顺序与最小验收（沿用T-01/T-05，不新增任务中心）

**I-49原入口保留保障的有界恢复**：真实资源门揭示的已存在路由缺陷只按原API/owner恢复，不开展A-01/A-12产品。Schedule仅修collection POST匹配与GET读取边界；Chat/Move提前拒绝补原`x-request-id`契约。Message的唯一持久提交/重放事实归现ChatTurn/outbox：先核当前Project/Conversation，再按digest返回原三ID，同事务提交Message/dispatch/AG-UI。native Message入口不得另claim/replay通用receipt或在准备、解析、提交间重置预算；未知COMMIT继续用原key/body恢复、不新增失败回执、不自动重放。后续只在该完整业务切片删除外围ticket并传递既有lifetime，保现Skills、权限、取消及canonical事务，不搬全局dispatcher、不新增Schema/协议。现有调用链经writer与独立reviewer核验，Root已授权I-49 Part2八个关联源文件及三个原测试：移动唯一Message handler、清native及raw/Nest调用的外围ticket/无用参数，并沿既有service/selection port/PG prepare与commit贯穿lifetime；不改Schema、公开协议、Project端口或全局idempotency。pg排队只退休等待者并回收晚lease，Project只读晚结果只退休，不冒物理取消；认证/body不扩成统一HTTP SLO。不能复制两套Message映射或遗留无意义兼容参数；真实R211/R215/R237/R190与独立默认回归证明，而非改断言清绿。

**I-52原生空body传输对齐（既定C-1.3，不用旧caller规避owner偏差）：**Root真实IAM＋BFF relay已过登录/固定tenant/安全状态，退出断言实际失败，原候选source/DB inventory保持且全清理。锁定Better Auth1.7.3的sign-out body为optional；上游better-call/node对零Content-Length返回null body，而当前IAM ingress对所有非GET/HEAD注入Uint8Array(0)。Root实跑锁定parser证明无body可接受、注入空body触发415。只在原auth handler对零字节保留无body语义，仍读取/限界原raw bytes，不伪造{}、不放开媒体类型、不改非空payload/CSRF/allowlist/取消；原auth-handler单元真实HTTP先RED再窄修。原BFF relay测试保无body请求并加强为200＋Cookie清除＋同旧Cookie安全状态匿名，退休含401的弱成功枚举，不改业务API或新增协议。Root再串行真实relay、IAM完整门/全资源与相关BFF门；旧绿色不覆盖这一原生传输缺口。

**I-53测试新增约束纠偏（同一C-1.3，不由测试倒逼无依据生产改动）：**I-52真实复验确认退出200和issuer Cookie删除，随后raw sign-out的no-store断言失败；production与fixture均经同一IAM HTTP setup，Better Auth sign-out不保证该头。核对BFF现API原生relay段明确保留owner cache header，只有safe session及具名邮件/邀请操作强制no-store；主方给该原生退出测试额外增加no-store没有充分现行合同依据。撤回仅此一条新增断言，不改生产代码、cache policy、referrer-policy、IAM或fixture，不新增缺头/可缓存值测试来创造本轮新要求。保留原无body请求、exact200、issuer Cookie空值及Max-Age=0、noJWT，以及同旧Cookie下一次safe读取200/strict匿名/no-store/noJWT，故不放宽真正退出与撤销风险。此纠偏不是把生产失败冒通过，原RED和判定依据保留；Root继续真正跨仓复验。

**I-54原生编排owned-process清理竞态（同一T-05/T-13）：**当前四仓精确组合正式G1已过source/node及生产BFF启动，但Admin阶段0旅程失败；源码、清理及凭据边界未失败。Root无资源复现原Admin隔离构建：Next编译/类型实际成功，仅原run_native_command后置进程组清理报EPERM，finally随后重试清理成功；该重试是否再次发信号未记录，不断言zombie或仅自然消失。原helper已正确保留leader退出后的子进程库存，但EPERM后二次库存仍短暂有组即失败，未使用现有quiescence预算。只在既有capability_bff_smoke_runtime的stop_owned_process承接该竞态：在当前phase原15/5秒内轮询真实库存，只有组确实消失才成功；持续EPERM/存活/库存读取失败仍报错并保留依赖，不以leader退出或EPERM当完成，不延长build期限、不盲重试信号。原capability测试先证明短暂EPERM→后消失的RED，保持续拒绝/仍存活的负控；Root原helper真实隔离build和正式G1再验。无System helper、产品、认证或Schema扩修。

**I-55原生资格拒绝的真实UI oracle（同一T-05，不提前A功能）：**正式新G1已推进至异tenant资格拒绝，原retired以“私有账户card必须可见且disabled”绑定旧实现。当前有效设计只要求可信403不伪装匿名、不注销仍有效Session、退休私有读写/旧数据并保canonical草稿/未知命令；不要求私有modal继续挂载。Root私有真实诊断保留原断言并先经真实composer写非空草稿：403后仍/app且无登录表单，card/旧邮箱/subject/姓名字段均消失，草稿原字节未变；通过既有fixture恢复同Session固定tenant并reload后原草稿实际恢复，非空字节仍相同。只在原driver/原Python测试使oracle允许“旧数据已退休的disabled空card”或“私有card已卸载”，两者都要留在/app产品路由并确认真实公共壳可见，保全局旧身份无泄漏、非/login、3秒总预算及迟到profile释放后仍不复活；/error或/app白屏不能因私有card不存在就通过，不能只删可见断言放行。补会被旧实现击中的回归与仍泄露/误到登录/超预算负控，Root再正式5旅程验证；未知命令原key/body由既有对应案例承接，不用这次普通draft证明其全链。无需App/IAM/BFF/Admin产品、Schema、认证协议或新状态页变动。TLS handshake噪音另作未裁因事实，不借此关闭TLS校验。

**I-56 Cookie安全模式收敛设计门（同一C-1.3，不改身份/业务边界）：**真实浏览器及真实owner/client探针共同证明：已撤销的会话并未误放行，失败源于HTTPS测试/开发配置把不带Secure的删除Cookie交给严格HTTPS过滤，随后旧Cookie仍在而业务正确返回session_invalid。不能靠放宽此过滤、Cookie改名/补签或把两种401都算成功掩盖传输不一致。

- **Owner/目标**：IAM仍唯一Cookie owner；移除`createBetterAuth`对`useSecureCookies`的NODE_ENV覆盖，复用锁定Better Auth按已配置`IAM_ISSUER_URL`/baseURL选择Secure和`__Secure-`名称的官方默认。生产schema已强制issuer/Web HTTPS，生产名称/属性不变；有效HTTP开发保持plain，HTTPS开发/测试正确使用Secure。Path/HttpOnly/SameSite和Cookie内容不变，无第二SDK或新配置flag。
- **消费者**：BFF/App既有relay config从可信canonical public origin的HTTPS选Secure模式，同时保留`NODE_ENV=production`的原Secure安全floor，不能把production+HTTP从Secure降为plain；不新增跨field校验或混合协议支持承诺。BFF safeCookies现HTTPS过滤原样保留，不给删除Cookie开不安全例外。当前Root fixture的issuer明确为同webOrigin＋`/iam`，production两者均HTTPS；mixed-scheme非生产配置可解析不等于已支持的原生组合。
- **Root/删除项**：原native receipt按其已验证web origin只接对应合法模式：HTTP/plain、HTTPS/`__Secure-`；不无条件宽收两名前缀。BrowserBroker、driver、Admin现有精确合法名/opaque Cookie承接不新增解析器。删除环境变量导致的HTTPS plain假设；旧开发HTTPS plain Cookie需仅清旧Cookie后重新登录，不清草稿或业务数据，不加旧名fallback，不操作用户现有浏览器/正常服务。
- **合同/数据**：不新增Schema、Session引用、DTO、票据、路径或依赖。现relay3.0/状态1.0及IAM snapshot已含合法协议形状，预计artifact字节不变，必须正规生成检查证明；若实际变动由owner先发行再固定消费者，不手改vendor/摘要、不强行保持版本。只同步受影响owner的技术/API文档，无数据变化不建空模型文档。
- **验证/写区**：owner先交必要设计文档，Root复核后才授权源。IAM原factory/原配置测试与确有plain硬编码的原host/SMTP案例；BFF原runtime config及policy/transport/native client/真实relay案例；App原iam-relay-config及原模式/登录案例；Root原native receipt/原测试。先用框架真实Cookie名/属性及HTTP/HTTPS非生产/production floor获得RED，不锁内部配置字段字符串，不机械扩17项矩阵。Root串行完整owner门、实际Cookie删除/rolling传输、SDK/相关真实资源与精确新组合5旅程；账户两API真实BFF消费和inspection owner继续列缺，A停写。

**I-51共享Admin真实验收接缝（仅既定T-05 fixture/编排，不改产品认证）：**当前runner只起IAM/BFF/App；App已有`/manage`重写，可直接接同源Admin，不新建业务路由。新增Admin源码/Node精确预检、隔离Next启动与清理；仍复用现PG/Redis/TLS代理及一个浏览器会话，不改App/Admin/BFF产品admission、Schema或发布依赖。现browser用户不是platformAdmin；IAM现成`manage-platform-admin.ts`与model-routing fixture已提供真实管理者Session、0600私有Cookie、CAS、鲜读和同事务audit模式。只给原bff-session-admission host增加固定当前fixture用户的grant/revoke/inspect窄命令，禁任意userId/直接改资格SQL/新测试服务；CLI未知不自动重试，失败与输出脱敏，私有文件/manager随自有fixture回收。命令有限输出为`kind=browser_platform_admin`、原command、真实enabled/version/succeeded_audits，不含Session/Cookie/新token。先原host integration实际RED再fixture实现，Root串行真实资源复验。

Admin Node需回读canonical同源`/api/admin-access`；Chromium的host映射不覆盖Node，不能改产品Origin或放开localhost掩盖。只验证并复用Node22既有`--use-env-proxy`与`NODE_EXTRA_CA_CERTS`：自有loopback HTTP CONNECT仅允许本run唯一canonical host:443，隧道到原自有TLS代理的随机端口，Host/SNI/证书校验和产品fetch保持，不禁TLS校验、不猴补fetch、不继承外部proxy。先私有真实Node fetch＋正确/错误authority与CA负控证明，再定具体Root写区。顺序为同一真实登录→Admin准入/安全状态→CLI仅撤管理员→Admin私有UI与当前me拒绝、Product会话/成员仍有效→原撤成员旅程；全部源码停写且精确gitlink后才能称G1通过。Root候选写区仅原native runner、Chromium driver与原测试；若隔离Next通用helper确需变更，先报精确路径/兼容影响，不自建第二编排框架。

- [x] 撤销I-38引用candidate，核实源码/生成物/构建输出零残留；保留SDK I-37与I-36有效风险覆盖。
- [x] 三路只读盘点完成：IAM原生实际形状/官方双true、BFF全部59调用文件/隐藏Bearer链、App36源码消费者与Admin共享登录接缝；计数只表达迁移面。
- [x] **D0三面候选文档**：IAM、BFF、App/Admin各自唯一writer完成技术/API/数据文档；交叉审查收敛17普通业务＋2账户认证生命周期、rolling/RSC，并补raw Session relay关闭与全局User输出消费者。此勾仅指文档候选交付。
- [x] **认证D0设计门复核（2026-11-03）**：主方核ADR-034共享登录、ADR-035直接服务认证＋BFF可信用户上下文与用户标准后端重做要求，三面/删除项/失败语义完整且无新增认证owner、票据或持久模型。无需重复索取已有决定；准许IAM owner先完成合同与实现，不声称用户另行批准候选，也不提前放行消费者/G1。
- [x] **IAM owner先行**：896405d / internal与SDK 0.20沿原PR6交付；服务认证/用户上下文/业务policy分离，退役native-admission profile/模块及第一方伪OAuth分支，保合法独立OAuth。Root完整verify、真实481、clean consumer2及双审通过；具体范围见§0.1/I-39，不代表消费者/G1。
- [ ] **BFF消费**：固定owner commit/artifact后迁AuthenticationModule、唯一认证client及所有私有业务参数链，删除optional native/Bearer fallback、OwnerSessionAuth、空token与丢native的wrapper；发行独立browser-private状态contract。先核一条真实完整链，再扩大，不逐文件堆测试。
- [ ] **App/Admin消费**：正规生成状态契约，删假claims/旧nextauth catchall/重复me/csrf-refresh外壳，保UIepoch和unknown写恢复。公开协议及第三方OAuth不动。
- [ ] **主方冻结复验**：冷登录/深链、共享Admin、CSRF、rolling多Cookie、独立撤Session、撤成员/管理员、异tenant/伪造身份/错service用途、依赖503、私有迟到响应、CAS/last-owner/audit回滚与unknown零自动重放；检查普通owner业务wire不含浏览器Cookie/Session引用。更新既有测试，只有独有风险才新增。
- [ ] **回到清理闭环**：G1完成后T-17真实Nest关闭与资源释放→T-11剩余raw/dispatcher/Repository-Service-Port disposition→C-4精确组合全门与同步E2E；每仓各自PR，不merge main，不部署。A-01/A-02/A-07继续GATED。

本轮三个具名writer分别交付IAM三面、BFF三面、App/Admin六面后停写，完成只读交叉复核；后续源码调查又核到operation全局direct-only会误删合法OAuth，IAM/BFF候选已限定为第一方调用模式；已批准T-17前置关闭缺陷另由具名writer按下方有界写区先RED推进，不涉及新认证；主方唯一写Root计划/状态。此前文档阶段主方复验Root/四子仓diff-check及19份Markdown新增本地链接，新认证源码/契约/生成物零新diff；后续有界T-17仅改资源client与原Nest测试。发现的raw relay与注册strict decoder问题已纳入实施/回归清单，运行时仍待修；未启动业务服务、重复跑业务全门、提交/推送或更新gitlink；新增driver回归只使用自身loopback协议peer，不使用共享Redis。后续fresh BFF build与无外部I/O的生产DI关闭探针先RED，再按T-17前置例外完成下方两文件修复与主方相关复验；不算业务全门或新认证验收。主方已按既定授权收口认证D0并交IAM owner实施，不再用文档自设“待用户批准”停工或询问旧A/B；Goal仍active，D0通过不等于G1/消费者或C-4通过。

#### 替换清单、状态及验收

| 范围 | 标准重做要求 | 当前状态 |
| --- | --- | --- |
| App/Admin | 删除假claims/60秒TTL/旧RP形状，收敛`/me→business→/me`；错误不伪装401，共享登录/未知写入与UI退休保持 | App6388完整候选门已验、机械交付预检返修中；Admin348完整门通过并推95c504d至原PR5，新共享browser未验 |
| BFF | 消除optional native/legacy Bearer fallback/空token；wrapper/action/publisher/OpenApp/AdminTeam/Billing全消费者使用唯一真实principal | IAM0.20消费与pure门已阶段验过，当前I-49 Message既有保障窄修中，真实资源/新组合仍待 |
| IAM | 分开认证、服务身份、权限业务；删第一方业务的Cookie/Session及伪OAuth耦合；保合法独立OAuth与原业务保障 | 4463c50/0.20已推原PR6，Root完整与真实门通过；新组合另验 |
| 原生认证合同与SDK | 唯一owner生成源；退役旧native-admission生成物；IAM官方get-session仅认证client消费，browser raw relay关闭并只读安全状态 | IAM0.20已发行至候选PR；BFF34c9f99状态1.0/relay3.0机器合同已推，App/Admin固定消费中，尚未实测新browser整链 |
| 认证G0 | 受影响三面与必要ADR差异先收口，再固定合同/消费者；Nest/feature/数据owner决定保留 | D0及当前冻结组合G1已通过，不重复请求既有决定 |

验证按行为风险而非旧实现：真实冷登录/深链、Admin共享登录、CSRF、退出与独立会话撤销、会员/管理员资格变化、同主体切tenant/会话的迟到私有响应、错caller/surface/tenant/自报身份拒绝、IAM故障与取消；认证边界之后的跨owner业务wire无Cookie/登录Session引用（Browser→入口仍自动带Cookie），原CAS/审计回滚/未知提交不自动重放；用真实HTTP secret-canary核旧浏览器get-session路径不再返回框架raw body，IAM认证client仍正常。变更后的新测试以新owner合同和行为为oracle，不拿旧测试数量/内部CLEAR覆盖设计问题。

T-01负责标准方案/G0；T-05负责认证完整切片；G1后仍T-17/T-11清理、最终T-09/T-15/T-16全量与组合验证，A-01/A-02/A-07保持停写。原完整Goal不缩减；机器Goal已核实为active；旧等待条件已结束，不再请求旧委托选择。

## 4. 执行顺序、并行写区与检查点

保持用户指定次序：**先C-1.3，再C-2/C-3，最后C-4全量验收，再A任务**。允许独立只读调查和已冻结候选审查并行；不以并行之名提前开展后继业务写入。前置例外为本任务候选门禁所需的T-06机械格式修复、T-18已复现的Node运行/生成工具链修复，以及真实native运行复现的T-17最小启动/关闭缺陷；它们不等待G1，避免验证依赖成环，也不授权提前批量迁移raw消费者。

### Chunk 1：当前方案与既有候选接收

- [x] T-01：Root完成本文/摘要/历史入口整理，独审、文档验证通过；冻结的是本轮方案，不是业务已验组合。
- [x] T-06/T-07/T-12/T-18既有候选接收：Root完成冻结复核/静态完整门及BFF真实schema补测，子仓独立draft PR与Root精确gitlink已交付；仅闭合原切片，不替代新候选和最终组合门。
- [x] T-04/T-13：原runner/source/Redis注入与清理修复完成；真实失败退出和Root535最小成功退出均cleanup PASS，只关闭此smoke范围。
- [x] T-17前置子项：BFF4d6五DI修复、真实容器回归及Root535最小native通过；完整生命周期子项仍开放，不据此放行raw删除。

### Chunk 2：先关闭C-1.3

- [x] T-05：原正式五旅程、账户真实消费、inspection完整生产链/原BFF四GET及组合负控共同满足G1，owner/request/receipt与最终HTTP/UI状态已复核；主方及独审确认，不把单一smoke或四GET当全门。
- [x] T-14接收方切片：producer盘点、三面设计、receiver-only实现与取消负控已交付f515；Root独审、完整门/真实接收方及Root六文件精确配对完成。最新PR12基线整合另属T-09，未据此关闭G1/G3。
- [x] Root与独审已复查当前旧RP/SessionRef/第一方workload OAuth目标消费者为零，合法独立OAuth/API Key/OpenApp/MCP OAuth保留；IAM仍装配的PlatformWorkload producer归T11退休。G1完整证据已满足，进入下一chunk，不冒所有遗留server已删。

### Chunk 3：C-2/C-3最终清理

- [x] T-17：BFF `09f44fe` 真进程 SIGINT/SIGTERM、端口冲突、PG 锁下 30/31 秒期限及回收已有证据。
- [x] T-11：现役 feature 接线和测试迁移完成；当前 BFF 生产图无可达旧 raw/聚合。
- [x] T-11：退役旧认证 producer 与目标消费者，按当前组合定向验证并回收；精确组合的正式门见 C‑4。
- [ ] T-06复验：前置格式门已处理；本批新触及文件若再有格式失败，只作机械修正并复验无行为改动。

**本轮收口盘点（只读，BFF `f0107a7`）**：生产入口为 `main.ts → AppModule`，未发现仍可达的旧 raw runtime、LegacyRoutes 或宽聚合；旧批次迁移/调用点数字不再作为新增工作量。现役 System/Skills 的 503 是公开的拒绝行为，不调用旧 runtime 或 owner；不为迁移重复验，也不靠旧文件名判断去留。Root 旧 Chat GC Chromium 脚本引用已删的 `PostgresBffRepositories`，无现役调用者，已随专属驱动和分支在 `8a172454` 删除。现役 BFF 真 PG 覆盖删帧/墓碑/游标/快照，Web 覆盖 `event_cursor_expired` 后重新取快照和按新水位续流；旧的两件产物和 Chromium 真链只保留历史证据，不声称本轮复验，也不恢复宽聚合。定向 Root 回归与 Ruff 通过。此盘点不代替 IAM producer 退役或 C‑4。

### Chunk 4：C-4整体验收与A门交接

- [x] T-09/T-16：受影响 owner 门和真实 I/O 按范围验证，各沿原 PR；Root 拓扑/来源通过，结构基线逐项复核没有新增规则问题，13 条声明破损边和 2 个工具链未验证仍记录。
- [x] T-15：正式原生 5/5 并回收；保留的同步实例实测登录、项目读取、共享 Admin，启停和范围交本机说明。此隔离实例不是全 owner 单库、全产品或正式部署。
- [x] G1/G2/G3 已满足清理退出条件；交接 A‑01/A‑02，之后 A‑07，不把清理 Goal 完成计为产品完成。

### 并行职责

| 角色 | 唯一写区 / 范围 | 排除 / 交接 |
| --- | --- | --- |
| Root主控 | 本计划、task/CURRENT/evidence；Git index/提交/组合/进程资源/最终验收；Root runner按本轮明确派工 | 不同时修改worker写区；受影响owner完整门由主窗口串行执行 |
| App/Admin原writer `app_standard_consumer`（已停写） | App bfb749c3/原PR50、Admin95c504d/原PR5已交付且clean；I-50两文件/45路径机械空白全部已Root复验 | 无当前写区，不为G1预写A功能；后继源码问题先证因再单独授权 |
| BFF writer `bff_standard_runtime`（已停写） | I-49 Message/Task/Project与原测试有界修复已交接；Root真实423/0SKIP通过并接管最终全门，owner四文档由Root单独同步 | 无当前写区；不擅自修新失败、改Schema/契约/依赖或Git，真实IAM relay另由Root执行 |
| Root端到端 writer `root_standard_adapter_review` | 仅原native runner、Chromium driver与原Python测试，按I51扩共享Admin与标准Node CONNECT/CA自有transport，保原strict四旅程/3秒/清理 | 不动共用proxy/helper/产品源码/Git；不启动真实owner/浏览器/PG/Redis，完成后停写交Root复核 |
| 独立reviewer | 各片停写后只读核规格/质量/证据；已实现该片的writer不自充独立复审 | 与当前具名写区分离，不实现、不提交，不把worker退出码或局部门当Root完整验收 |
| IAM I51 writer `root_standard_adapter_review/frame_route_read`；Capability后继owner | IAM仅原bff-session-admission host与原integration，固定fixture User的管理CLI grant/revoke/inspect；Root真实RED已跑后授权源实现 | 不改生产src/Schema/契约/依赖，不Git/真实资源/全门；Capability仍待既定C4整合，不新增并行contract writer |

历史交接（已由§3.6用户否决与标准重设计覆盖）：IAM 285dfcb与Agent 47ca431均本地停写、未推送；I-36已识别处置和Agent本次候选复核完成。Root独占任务表/Git/资源。I-38未裁决前不实施会话引用、不发行native2或启动BFF新契约消费；I-31重复登出与专用admission依赖错误分类已由285dfcb补证；BFF b6d98f8已在现测试接当前生产ProjectMutationMiddleware与真实client/loopback的网络失败负控，无新增compat/raw消费者或通用harness。所有writer/验收均结束，当前等待I-38裁决。I-33原四旅程不重复调试，T-17/T-11后继仍门控。

---

## 5. TODO 台账（后续持续更新）

状态：`OPEN`未做；`IN_PROGRESS`已开工尚未闭环，不代表当前有运行worker（实时执行另见当前交接）；`REVIEW_PENDING`候选已有证据、待主方复验；`VERIFIED`仅该切片已验；`WAITING`依赖未满足；`GATED`后继停写。未运行、skip和设计通过都不记为功能完成。

| ID | 事项 / owner | 状态 | 依赖、下一动作与完成证据 |
| --- | --- | --- | --- |
| T-01 | 方案/问题/Goal/TODO统一；Root | VERIFIED（认证D0设计门） | I-38已撤；§3.6与owner三面经交叉及主方复核，17＋2/原生状态/删除项与ADR-034/035一致，无新增票据/owner/数据。IAM已交付、BFF/App/Admin消费实施；本表持续更新，不虚构用户另批候选；Goal active |
| T-02 | MCP denied icon零owner副作用；BFF | VERIFIED | `228e3d6`、focused42、旧基线full；最终组合继续回归 |
| T-03 | invalid-owner typed error；BFF | VERIFIED | `228e3d6`、focused24、旧基线full |
| T-04 | 资源/Node/source/schema preflight；Root | VERIFIED（当前原生组合前置） | aec5775a正式run三owner clean/gitlink配对、实际Node符合；隔离fixture正常建立/回收。不外推所有owner schema或常驻运行；后继新候选重新配对 |
| T-05 | 认证完整切片与真实旅程；Root+IAM/BFF/App/Admin | VERIFIED（G1当前冻结组合） | Root4e603743正式原5/5、真实账户消费、inspection完整Native生产链与原BFF四GET、代表组合负控全部通过；源码/dist/DB清单、strict broker、cleanup/scan保持，主方/独审复核无漂移。I-23旧显式smoke/R336及IAM遗留producer仍按T09/T11/C4承接，不冒已删除或全Task A完成 |
| T-06 | BFF格式门；BFF | VERIFIED（候选） | Root format exit0，AST/注释等价32/32；独审确认原11候选byte不变、1068tracked符合冻结；后续改动再复验 |
| T-07 | App Public28.18消费修复；App/Root | VERIFIED（消费切片） | App fdbb49f1主方完整contract452/architecture50/default6411、0skip及lint/types/build；当前正式native4/4。I-29后继owner版本另按影响固定消费，不将此项当全产品验收 |
| T-08 | IAM SDK与verify；IAM | VERIFIED（1ee8已验切片，非I-29候选） | IAM1ee8d156 / 原PR6已推送；Root verify121files/1566pass/build，真实两host66pass/0skip；Root d309已接收新pin，不代表跨仓native端到端 |
| T-09 | Root/各受影响 owner 最终串行门；Root | WAITING_FINAL（终态配对待确认） | T‑11 已本地收口。IAM、Capability、Agent 有各自候选证据；BFF `32357c0` 正式默认门通过，两项 PG 条件用例未运行。Agent 8.11→BFF→App、Root 来源校验与精确组合 E2E 未收口。Capability `5e607fd` 相对已验候选的静态差额已补：Node 24.20.0/pnpm 11.25.0 执行 `pnpm typecheck`、变更 fixture Prettier 与两份变更测试 ESLint 均 exit 0，不重跑真实 15 项。 |
| T-10 | A-01/A-02/A-07及其余A backlog；Root | GATED | G1/G2/G3全部闭合；原16任务责任和优先级保持 |
| T-11 | raw/global/剩余 Repository-Service-Port 与旧认证 producer；BFF/IAM，Capability 消费配合 | VERIFIED_LOCAL | 旧生产入口/producer 归零，真实 ingress、eicar、ack_lost、R336 已通过。`45a2989` 首批四条真实行为基线通过；StableId `f7d1e69`、两个 reader `76f2d04`、Personalization `335dbe3` 均本地归并并定向验收；ScheduledTask `368e65e`、Chat `fb3cfa4`、Projects `32357c0` 已拆分；C‑4 组合另验。 |
| T-12 | Nest默认架构门与入口隔离；BFF/Root | VERIFIED（切片） | 173e026；Root第三轮format/check exit0、contract1344/default2343pass+2skip/build通过；两资源skip另真实PG15pass/0skip；此项只覆盖Nest架构默认门，native默认测试遗漏归T-05/I-31；raw最终删除仍属T-11 |
| T-13 | native smoke清理与脱敏证据；Root | VERIFIED（隔离smoke/browser清理） | 既有成功/失败回收证据保留；aec5775a正式4/4收据cleanup PASS/quiescent/无保留文件、credential scan PASS。不替代生产Nest生命周期或常驻同步环境 |
| T-14 | global_register direct credential；Capability/Root | VERIFIED（接收方切片） | Capability f515e225 / 独立draft PR13，Root最终format/lint/verify/Prisma/build全0（3051pass/678skip）；真实receiver1pass，Root配套六文件154定向/1879治理。原PR12新增基线导致PR13冲突，后继整合归T-09，不能合并或称全组合完成 |
| T-15 | 当前组合同步 E2E 可用性；Root | PRECHECKED（未启动） | `9a55df34` 对齐 launcher 版本；正式 runner 选项和 Admin 已安装运行时预检通过，实际 source 检查 IAM/BFF 被旧 gitlink 拒绝。前台 MCP+Admin 选项缺 PG 键，仅在进程内显式从现本机 admin URL 映射后通过。旧 HTTP/Chat 不是原生入口；最终配对后跑正式旅程，再交接现役 native 前台入口、支持范围、日志索引与回收归属。 |
| T-16 | Agent 与原 C-1 删除项最终复核；Agent/Root | VERIFIED_OWNER（组合待验） | `40effb2` 已通过最终工程门、真实集成/acceptance（Display 隔离命名差额同 SHA 补验），本地候选已快进；交付目标是原 PR46 远端 `codex/agent-run-lifecycle`，精确组合及全局规范核对仍归 T‑09。 |
| T-17 | Nest 启动、shutdown/drain/pool；BFF | VERIFIED_LOCAL_COMMIT `09f44fe` | 实际 SIGINT/SIGTERM=0、端口冲突=1、真实 PG 锁下 30.002 秒 HTTP EOF 与 31.030 秒 exit 1，资源回收；未推送或更新 Root pin。 |
| T-18 | BFF Node24运行/生成工具链一致；BFF/Root | VERIFIED（切片） | 173e026；21路径独审/1068tracked hash匹配；Root第三轮format/check exit0，106generated与原43路径保持，7正规生成/双检通过；两轮RED保留，CI/Docker未实跑不称通过 |

---

### 5.1 下一检查点与工期口径（2026-11-03）

#### 历史检查点（2026-11-03，不作为当前排程）

G1/T05已按完整证据链及源码复核收口，Root a612915a仅三份tracking docs已推原PR66；原正式五旅程、账户消费与包producer/原四GET不重跑。T17首片主方RED→最小AgentDispatch早期hook修复→冻结相关门GREEN及独审CLEAR；真实listener、在途HTTP/worker双释放顺序和DB末期回收已验，候选未提交/pin，不当完整T17。四feature正常drain均已按独有主方RED→最小hook前移→冻结相关门GREEN并独审CLEAR；累计6原文件未提交/pin，不是完整T17。`t17_sse_admission_read` 已只读确认锁定Nest原生return503OnClosing可在worker等待期间拒新请求，force-close不替代优雅SSE。关闭拒入主方已RED→原生return503OnClosing→冻结相关门GREEN，生产与测试复用main唯一options，不是测试专用假绿，未用force-close。SSE五源码已主方准确RED→最小实现→冻结相关门GREEN并独立规格/质量CLEAR，15文件候选未提交/pin；当前writer `t17_signal_failure_read` 的原Nest测试已被Root实际复验有限失败准确RED：原78保护PASS，新增5场景+父FAIL/0SKIP，无fixture/cleanup失败；private `kokoro-t17-finite-primary-red-d7nrju4e/result.json`。新增场景独审CLEAR；旧DB失败例已最小finally归还process状态，原断言/真实close及其他测试保持，Root再验84中78保护PASS/6准确RED/0SKIP，private `kokoro-t17-finite-compat-primary-red-rvc9n900/result.json`。owner设计先写回后实施原五hook最小候选，现已停写并由Root冻结format/lint/typecheck/build、原84保护/故障及121相关worker回归GREEN/0SKIP，1085输入保持，独立规格/质量CLEAR，private `kokoro-t17-finite-primary-green-flae_5uw/result.json`。DB close原字节、main/SSE控制语义及其他保护文件保持；累计16原文件候选未提交/pin，不冒实际main退出码或真实资源门；进程失败/挂起/初始化竞态与31秒出口只读盘点已完成，仍未实施，不以native enableShutdownHooks或旧fake shutdown用例冒已验。Root独占台账/Git/真实资源及后续source批准。有限失败独立清理/安全分类/非零状态切片亦已Root冻结GREEN并独审CLEAR；完整T17尚有挂起、启动失败/竞态、真实main signal/deadline出口及真实资源/SSE回归，T11待风险承接后删除；其后T09/T16/T15最终门与同步环境，A继续停写。

C阶段尚有5个未闭环执行包（T-17/T-11/T-09/T-16/T-15）；T-10另保留原A-01～A-16产品责任，不是同级相加或全部从零开发。未按实际剩余量核准整体完成日期，不用测试数量换算百分比。

**执行中断与恢复纠偏：**前一实施回合因模型容量错误结束为failed，机器Goal进入blocked的更新时间与该失败结束时间一致，失败窗口未见显式assistant blocked工具调用，但日志没有状态转移actor字段，不臆断具体调用者；G1实证已取得而收口台账尚未写回。随后三次只读heartbeat没有后台实施worker，不是业务依赖或用户待决事项阻塞。本次用户明确恢复active，主方get_goal已确认；保留原完整目标，不新建/缩减Goal。此次恢复先落G1/T05与TODO，再推进T17，定时汇总不替代实施或串行交接。

#### G1已验范围与证据边界（2026-11-03收口）

- **已有证据不重铺**：正式原五旅程承接匿名、退出、Session/member/admin撤权、旧Cookie与迟到私有响应；账户18承接伪actor和实际业务/账户wire隔离。IAM当前真实482项中的current-facts、account-sessions与host用例承接伪tenant/不存在actor、撤销事务、重复退出及锁等待取消零写；App/Admin原状态机承接未知结果不补成功/不自动重放。独立只读复核核对相关测试与各owner当前完整门字节相符；这些证据分层保留，不机械复制17操作或把doubles冒真实组合。
- **组合接缝已补证**：当前真实BFF→IAM的错Origin/错Web service envelope拒绝、独立purpose服务密钥失配及实际IAM进程中断均按当前安全状态合同返回typed拒绝，不误匿名、不补成功；恢复密钥后真实正控再次成功。零owner工作仍由原middleware计数负控承接，不虚称本次额外观察过零调用。
- **inspection已取得真实消费证据**：复用受管版本化S3与ClamAV，当前Capability f515/Storage4a99061真实Nest、PG/Redis与BFF8cb/IAM1fc配对，完成Native生产全链和原BFF四GET/0SKIP。独立已知ZIP正文与UTF-8字节原样比对；两S3版本逐exact key/version回收且全新tenant前缀证空，进程静止及自有DB/namespace/私有工作目录回收。六owner生产输入、Root冻结代码与dist清单经独审保持；未新增基础设施/Schema/SDK或改owner协议，不冒旧显式smoke/R336、Agent执行proof或全产品通过。
- **最小producer裁决**：使用当前正式Capability Native Connect Create→Begin→signed PUT version ACK→Complete CLEAN→Validate→Publish（含required publication precondition）→同subject Install；expected正文来自独立已知ZIP，随后执行BFF原四GET consumer。当前proto与BFF固定artifact源摘要相同，无SDK/生成升级。旧storage smoke缺Publish必需precondition且依赖预存skill，不整段执行旧脚本或顺带跑无关矩阵。
- **资源与写区**：Root唯一资源/Git/验收owner；具名worker只写私有一次性harness，不改产品/Schema/认证协议。复用真实IAM generic fixture同时生成当前bffUserContext与executionProof配置，个人包路径不伪称已验Agent执行授权；只使用本run自有临时DB/schema、namespace与全新fixture tenant的S3前缀。S3在任何Storage操作前证明该精确tenant斜杠前缀完整分页为空，记录生成的exact key/version，进程静止后逐版本回收并验证为空；不得清空共享桶或删除预存对象。准备脚本/资源就绪不记成G1通过。

#### 历史过程记录（以下时态不作为当前待办）

以下保留此前探针、首轮失败及返修因果；其中“当时/本轮/当前”均指各条发生时的基线。IAM0.19、BFF497900、待IAM发行或等待App/Admin开写等状态已被§0的896405d/0.20、BFF34c9f99与当前消费者写区覆盖。

**独立证据补充（当时未越过认证G0）：**上一目标回合执行真实受管PG/Redis正负控，补得正常空闲资源hook关闭及自有资源回收证据，归类为progress，而非等待或全任务完成。本轮复核私有receipt与source冻结，并将结论写回I-13/T-17及摘要；原Goal保持active，设计实施依据是已有明确用户要求与有效ADR，不将自动继续消息虚构为新的用户批准。

- 主方fresh BFF build exit0，随后生产`AppModule`容器关闭探针实际RED（closeCount0/externalIo0/期望1、exit1）。现`DatabaseModule`/`PostgresBffDatabase`无关闭hook，原lifecycle测试仅raw；Nest12按模块浅→深shutdown并`allSettled`记录吞掉hook失败，最小hook不证明worker失败/资源失败/退出状态已闭环。完整T-17继续OPEN，不临时塞AppModule早关pool或新增另一套shutdown。现按§4已批准的T-17前置例外实施有界资源owner修复：唯一writer `bff_standard_consumer` 仅写`src/infrastructure/postgres/client.ts`与原`test/nest-runtime-architecture.test.ts`，先test-only RED→主方复验→再授权source；只补正常hook、关闭Promise幂等、失败仍尽力清理和安全失败类别。此有界切片最终已停写：Root先复跑RED（5旧PASS/4新FAIL），作者补Pool-only/Redis-only/both旧source RED后实现；初版87PASS后quality发现锁redis5.12.1的QUIT失败会先置isOpen=false，故未放行。实际RedisClient＋自有RESP peer回归再获RED（close拒绝/open=false/ready=true/peer未闭），改用官方公开close后GREEN，零QUIT/真实driver状态归零/peer关闭。Root最终两文件格式、lint、typecheck、fresh build及architecture/Nest/原raw lifecycle共88PASS/0SKIP，冻结两文件SHA前后保持；spec/quality复审限范围无阻断。该loopback不冒真实Redis集成。随后真实资源hook验证见下项；worker失败/挂起、HTTP/SSE、硬期限及信号退出码仍OPEN；该阶段未放行新认证，后续设计门收口见本节当前立即动作。
- **真实资源hook子项补证（2026-11-03，Root执行）：**复用受管PostgreSQL/Redis，沿既有OwnedResources创建并回收本run临时数据库；真实生产AppModule/Database factory仅替换配置，实际连接Pool与Redis。独立Node进程分别做缺hook负控与production hook正控：双方连接先各1；负控在显式close/fallback前仍各1并如期失败；正控在同一观测点均降为0，Pool ended/count0、Redis end/open=false/ready=false，重复close成功。故不是由finally或强制DROP制造通过。全部自有进程组先确认静止，再清依赖，cleanup/verify_clean通过；观察连接已关闭，Redis零key写入，无新基础设施或共享数据重置，两source SHA保持。首轮private fixture把数值Redis CLIENT ID传给仅接字符串的命令而失败，修String转换后正负控通过；原失败及清理结果保留，不归因生产代码。此probe未init模块/启动HTTP/安装业务schema或运行worker，只证明正常空闲真实资源的hook，不关闭完整T-17/G1/C-4，也不提供同步E2E环境。脚本/脱敏receipt仅留本机private tmp，不入Git。
- 主方复跑别名感知AST census确认§I-09数字；无现成Nest listener fixture；3个纯PG suite的49调用保持最低充分测试层级，不为迁factory把全部测试抬成HTTP。main静态闭包506个value文件中不达raw server/runtime/owner aggregate，当前literal dynamic import/require为0；这是静态证据，不冒全运行时覆盖。
- IAM正常生成源当前仍强依赖旧native：`generate-contracts.ts`导入response schema、附加native security、强读v1 hash并产v2；IAM `generate-sdk.ts:104–122`与BFF `generate-iam-http-client.mjs:167–172`均强找旧response marker，BFF config还include旧operation。退休必须同片改生成源再正规生成，不只删JSON或手修generated。固定breaking baseline `75dea5e6`／oasdiff`v1.28.0`不重置；当前IAM internal/SDK0.19，BFF实际pin`497900ab`/0.18，不伪称已消费0.19。
- 新认证实现/发行尚未验收：主方已复核D0，保上述真实独立OAuth调用语义、第一方service分支零fallback、账户认证生命周期与生成链处置，现由IAM先正式contract/实现→消费者。不新增A功能，不合并main或部署。


**当时立即动作**：按用户否决撤销引用方案已完成；§3.6与IAM/BFF/App/Admin三面候选已交叉收敛，主方确认已有ADR及用户要求覆盖原生认证边缘/受信BFF上下文，认证D0收口，进入IAM正式合同/回归RED/实现；未新增用户待决项。范围和删除项不由旧代码决定，停止旧A/B及文档自设等待。依owner合同→完整消费者→G1→T-17/T-11→C-4推进，A停写。

当时执行分工：IAM896405d已交付后停止写入；`bff_standard_runtime`为BFF唯一writer（8028651基线＋三面交接），固定IAM0.20并实施单AuthenticationModule/普通service+actor/具名账户生命周期与browser-private code-first合同。其只读角色仅核接缝，不重开设计或全面盘点。Root唯一任务表/Git/资源/最终门负责人；App/Admin等BFF稳定正式browser-private artifact后开写。Root gitlink尚保持旧已验组合，不将仅IAM升级的混合组合标通过。

IAM最终owner候选第一轮完整门：121路径冻结清单由Root逐项SHA核验，随后主方Node24.20.0完整`pnpm verify`exit0（格式/lint/types/contract drift/固定breaking/SDK/default125文件1665PASS/build），551输入前后保持；私有冻结/日志不入Git。全部真实integration已终态：48文件47PASS/1FAIL、477PASS/1FAIL，551输入及DB inventory保持。唯一资源RED为platform-admin-management旧断言要求官方User不返回platformAdmin，与本D0显式returned:true不符；交回作者精确承接真实bool，保version私有/input:false/manager权限。独立quality限范围CLEAR；spec发现I-39三项，Root已核源码成立，现交回IAM唯一writer先RED修复再重新冻结，不因verify绿色提交/发行或切BFF/App。consumer/pack仍尚待。 现`iam_standard_contract`已取得I-39对应7项实际focused RED（4 Team损坏状态、2重复Cookie、1既存OpenApp读取），仅在现边界最小修；真实Cookie顺序/零写及旧OpenApp原scope序回归由Root后续执行。SDK pack本身要求clean committed tree，故正确顺序是最终verify/全integration/复审通过→Root显式提交→同clean commit真实pack/install/consumer→push，不造dirty开关或重置基线。 后继已完成：124路径最终freeze双审通过，Root第二完整verify126文件1673PASS、全部真实integration48文件481PASS/0SKIP，552输入及DB inventory保持。Root只按清单显式提交896405d（Git将3组删除/新增折叠为rename，清单仍精确124路径），同clean commit consumer2PASS；另正式sdk:pack并核commit/contract/lock/generator provenance与归档digest一致。非递归fetch无新增待整合后已推原draft PR6并核head精确896；PR说明保留原文补本片证据。未merge main、未部署、未更新Root gitlink。

本轮并行切片：`root_native_fixture_adapter`仅写Root现native runner与其现测试，承接IAM host已确认的两独立purpose凭据文件（USER_CONTEXT与ACCOUNT_SESSIONS），已停写。Root亲自复跑原整文件166PASS/0SKIP、diff-check及两SHA保持，独审本片CLEAR；拒旧字段/缺失或越run文件/同物理文件复用，两secret都登记脱敏，删除旧ADMISSION env。未改Chromium/浏览器状态/四旅程oracle或原RP env，未启动真实runner/资源，未提交；它只是fixture接缝，不是新链路通过。IAM唯一writer继续实现；只读SDK/账户早审发现actor metadata丢失、DELETE query闭集及锁等待取消风险已返修推进，另核无actor合法OAuth不应被普通Origin误拒；未冻结，不作最终CLEAR。完整owner/组合验证仍待停写基线。

IAM正式交付前远端预检：Root显式非递归fetch main与原PR分支，本地285dfcb对main28ahead/0behind、对原PR6ahead/0behind，无新增远端提交待整合；只更新远端ref，未切分支/改index/merge或推送。最终提交/推送前仍复核，不把此事实当本地候选已发行。

IAM首个冻结资源实测：作者停写后Root按新四入口实际跑受管PG/Redis（bff-owner-current-facts、account-sessions、account-profile、host）；551输入前后不变，42例中39PASS/3FAIL、两文件PASS/两文件FAIL。RED分别为missing User的MCP旧200/false oracle（当前正式身份拒绝403），以及两条合法OAuth Profile并发测试仍以旧账户OAuth入口触发撤销（401/屏障未入）。已交回作者按新AND账户入口承接原顺序/Session锁保障，不放宽生产或删有效并发风险；另补真实锁等待abort零写回归。原RED不作通过。作者按正式合同修MCP身份oracle、用新AND账户入口承接两条合法OAuth Profile顺序保障、精简普通BFF读的旧登录setup；补真实PG确认锁阻塞→HTTP abort→实际server signal→放锁→原repo结束→target/access/refresh/successAudit零写，以及旧含pair默认/refresh仍可合法Profile/APIKey但账户OAuth拒绝的正负例。第二冻结点Root同四文件实跑44PASS/0SKIP、71.87秒，551输入前后相同，独立数据库inventory相同；账户取消/query及回归oracle独审限范围CLEAR。此结论只覆盖四资源核心，不是完整owner/G1；0.20正规生成drift、全门/全部integration与consumer仍待，未发行/固定消费者。

BFF完整门首轮保留失败：contract1344PASS/1FAIL，默认test/build尚未执行；Root私有wrapper把umask077传给子进程，令现安全负控请求的0644 fixture实为0600，导致“应拒不安全文件”未触发。相同原文件/原断言单独对照：077为17PASS/1FAIL，正常022为18PASS/0FAIL；未改production/test或降低校验。将子进程恢复正常022（日志仍0600）后从完整check重跑，exit0、contract1345PASS/default2359PASS+2条件SKIP、lint/typecheck/build通过，输入前后保持。两条件skip随后原schema整文件真实PG15PASS/0SKIP，数据库inventory前后相同，不将原skip改称默认通过。两资源文件已本地提交8028651，未推/未更新Root gitlink，完整T-17仍OPEN。首轮额外手动Prettier遗漏本仓no-semi/160选项也已按真实脚本纠正并通过，原失败日志保留。

IAM首轮focused行为RED已实际取得：原`bff-user-context`单元入口6 FAIL，复现合法service＋actor仍被旧guard拒绝、Cookie误入旧native路径、重复actor边界及普通业务facts仍查登录Session。同一入口随后6PASS，仅证明guard＋核心facts初步实现，非完整owner或真实I/O；writer在上述有界写区继续17业务消费者→账户生命周期→正常生成链，并承接只读review指出的服务失败零fallback/缺核心事实/歧义actor负控，原RED保留。

**I-31覆盖核准基线（IAM1d9bd95；后继两处已由285dfcb补证）**：`native-owner-current-facts.test.ts:906–969`已覆盖真实专用admission未知服务凭据与human401分流；`internal-auth.guard.test.ts:179–239,1149–1173`已覆盖服务拒绝先于人类读取。撤回“未知凭据接线缺失”的初步判断。这两处原缺口已在285dfcb补证；不增未知credential重复例，不重跑既有四旅程。IAM native真实矩阵另已承接非合作getSession期限、limiter拒绝零写、断连及准入后当前事实变化；已提交写超时明确是unknown503，不伪称回滚。BFF专用native网络故障的feature接线已由b6d98f8承接（真实loopback、生产middleware与client，IAM响应/持久化端口仍替身），不冒Nest启动或PG验证。

**历史 I-29 首版接收检查点（2026-11-02，当时候选未提交；当前见 §0.3）**：IAM首次55文件停写清单hash `c4a505dc3a5bb86dced0be78302a71166c86cdcc500c2c1b56c5f0bdabb4a90c`；主方确认native1原件hash不变。真实native新suite 11PASS/13.38s，完整verify 124files/1613PASS/exit0；两次541输入无漂移。随后完整真实integration为43files pass/5fail、464pass/15fail/421.62s，输入仍不变，归I-35。通过范围不覆盖失败项，不作owner发行依据。

双审发现两项D0内缺口，统一归I-29不重建问题中心：resendTenantInvitation实际接受native但正规生成操作清单与新真实矩阵遗漏；native请求未真正接同一入口期限/HTTP断连，非协作依赖可能超预算且迟到抛500。唯一writer已获窄返修：resend正规生成/正负控；原lifetime＋具名native ingress/窄interceptor/guard/service共享预算，admission原504、business取消/unknown503，OAuth及服务身份不改，不承诺撤销已提交业务。主方所有测试已终态后才交还写区；后继重新冻结、双审、完整门和真实I/O，BFF仍待正式owner artifact。

I-35诊断续证：在私有临时`git archive 5fffe60`源码快照复用未变依赖/Prisma生成物，原3个CLI真实测试3FAIL；最小私有类别诊断见底层P1010→FAILED_TO_GET_SESSION，未保存原始凭据/异常payload。受管测试admin URL未显式user，父进程有默认USER但CLI按设计只用显式env，造成身份漂移。仅从同一管理连接读取current_user并将其私有地明确到测试URL，原基线/原断言3PASS、46非选、15.56s。快照已清理，不修改全局配置/CLI、不新增账号或扩大child env。验收wrapper后续固定此资源身份；3份旧oracle修订仍待主方真实GREEN，完整15失败记录保留至整套重验。

**历史首版返修时的进度重盘点 / 工期边界（不作为实时 worker 状态）**：

- **暂停问题**：机器Goal为active；上轮验收进程确已结束，当前IAM实现正在运行。Goal状态、worker运行、测试服务存活是三个不同事实。现无待用户批准事项；具体桌面暂停原因没有调度日志证据，不能归因于权限或环境。主控须在每次阶段交付同步当前writer、下一动作和依赖，避免把“有计划”写成“正在执行”。
- **历史候选交付预测（首版候选现已交付，进入返修，不作剩余倒计时）**：本次记录时刻`2026-11-02T03:24-05:00`；IAM writer在本轮报告候选实现/定向检查尚需约45～70分钟，低置信度、仅本轮时点预测；不含真实PG、独审、全门、提交/固定artifact、BFF消费或整个A。已报native2/guard/current-facts/Team定向结果仅为阶段证据，尚有原测试actor断言待承接，不写VERIFIED。
- **剩余关键路径**：IAM owner及正式artifact → BFF共享认证/生成消费 → Skills、Account/Team/Admin/Billing、MCP实际链与负控 → I-31/G1 → T-17生命周期 → T-11旧实现删除 → T-09/T-16最终组合 → T-15同步环境 → 原A产品项。依赖契约和共享文件保持单writer；消费者清单与原A只读核量可以并行。
- **当前Goal完成定义**：G1认证生产切换、G2生命周期/删除、G3冻结组合验证和同步环境全部达到退出条件；这是C前置Goal，不是原A01～16产品完成。11/18的VERIFIED是切片状态，不计算为Task A完成率。
- **当前运行环境**：正式4/4收据再次读取确认passed，cleanup/quiescent通过且无保留文件；没有据此交付常驻同步E2E。当前文档盘点不启动服务，后继T-15独立交付入口/支持旅程/健康与回收归属。

**本轮I-30实施写区（BFF唯一writer）**：固定IAM497900/0.18原件不升级；include新增verifyNativeSession（23→24 operation），使用generated native响应与既有ApiErrorResponse闭集，删除重复手写schema/arbitrary code fallback。仅openapi-ts.iam.config.ts、必要的既有generator精确保真normalizer、正规src/generated/iam-http生成物、依赖manifest、session-admission.client.ts、两份相关测试与package.json；16生成文件allowlist/双生成/owner digest不变。对owner closed object和RFC3339 offset语义补最低充分回归，native suite纳入默认入口。无Schema/lockfile/业务授权改动。已由f81f271交付，主方format/check全0，contract1345/default2350pass+2skip；1068输入无漂移，双审CLEAR。I-29后继owner artifact升级仍须重新固定/生成，不将此版本永久冻结。

**I-29历史静态发现（后续 owner 实现见 §0.3）**：当前BFF native client从permissions字符串推platformAdmin，而IAM原生permissions来自organizationRole，不等于User.platformAdmin事实；此项不能以I-30生成替换冒关闭。与Skills/MCP/publisher/OpenApp的原user-delegated资格一起由IAM owner明确当前事实与native决定，先更新相应设计/机器契约再消费。withSkillActionAdmission丢失verifyNative也须迁移；公共skill.list身份和服务身份不误删。

**历史 I-29 独立设计复核：当时 owner 三面 D0 通过、实现待交付；当前见 §0.3**。建议 native profile 2.0 删除无有效业务消费者的permissions、增加required platform_admin（当前User.platformAdmin事实，版本合法性留owner内，不增加无消费者wire）；旧1.0原件只读保留，新版正式生成/固定后原子切换，无兼容fallback。当前admission本身已核active tenant，缺口是业务事务helper/Team list未复核，以及Team Members/Roles/Invitations把Session/native proof丢失；必须承接exact Session/User/active tenant/current member，不只加四operation guard。角色政策按原owner承接：Skills/MCP检查角色完整性，Account/普通publisher不暗加全局角色门。现native admission的异tenant→BFF403既有语义保持。新增消费清单包括app-skill-bindings二次Bearer、skill-admin/installations regex enrich、managed-personal-skills/publisher、Billing成员分页/末端复核。IAM5fffe60/BFF105024d已明确这些写区/资格/错误/事务与零DDL并通过规格/质量双审，后继可实施；设计通过不冒实现完成。native2唯一必要新增native_session_service_unauthenticated（owner401→BFF既有503），human失效401保持，未归属401为503；原native1不改，不增加SLO/部署门。公共skill.list/第三方OAuth/服务资金与执行身份保持；事务内复读不承诺跨owner全局撤权原子性。

**I-33历史定位实验（已运行，结果见下）**：仅在隔离Web代理转发精确GET /api/account/profile时设置单个随机x-kokoro-request-id，以其入站hash→响应hash桥接App的两次/v1/me与业务profile请求；只留状态/错误类别/计时/hash，不留body/cookie。已读源码确认header用于关联而非身份，原driver、限流和预算不变。IAM native admission按caller/credential/operation共享100/60s bucket的静态事实已确认；仍需同请求证据判断本失败与429的关系。当时在BFF停写并精确配对后运行；后继同请求因果与窗口对照见下。

**I-33已取得因果与私有对照**：Root75f6e1ce/BFFf81的run7890d310同profile请求hash匹配首次/me429 session_rate_limited（2ms）→App503（11ms），业务profile未调用；cleanup PASS。单变量私有driver在旧context.close后、创建独立撤权A/B前等60,001ms，run3dbb48c3完整4/4、0次429、五次profile200、cleanup PASS。仅证明测试场景累计负载跨窗口后可通过；不称正式收据/产品容量验收。正规写区限Root driver及既有native测试；保持175秒总预算、3秒/4.5秒退休、同fixture的A/B、无重试与原断言。Node计时只要求完整60秒，sleep请求含1ms余量；不足剩余预算提前拒绝，不扩大watchdog。上述正规调度现已交付并通过主方停写门，aec5775a正式4/4通过；本段保留当时设计，不再指示重复运行。

**I-34局部修复写区**：App account-profile.ts、现有account-profile-admission.integration.test.ts及相邻server/INDEX.md精确条目。既有final null/身份改变/过期401和同主体200覆盖复用；补真实loopback最终429/503/断连→503、无资料泄漏。无owner/Schema/wire变化，先RED再删除局部catch。与Root编排writer路径独立；完整门和真实资源仍由Root串行。

**已交付I-32：当时检查点与写区**：cc405正式run6cb4509024b133f193c0ddc7在focusProbe172等待session响应超时，cleanup PASS。Playwright1.62.1源码默认Emulation.setFocusEmulationEnabled=true；主控私有副本仅在focusProbe起始对page/peer关闭该override，ecfbb0f5659e34406c291314实证trusted事件＋401，继而完成异tenant退休/恢复与UI退出全段，第四旅程新context登录账户入口超时。该副本不是正式4/4验收，不修改旧收据0/4。当时限定driver＋native测试两路径实现此focus纠偏，保全部原事件/预算/退休断言，不靠synthetic dispatchEvent；该修复已精确提交并复跑，后继第四旅程失败由I-33承接。

**I-31最小负控证据映射（只读审计，未新增运行结果）**：

| 风险 | 可复用当前测试与基线 | 缺口 / 后继 |
| --- | --- | --- |
| 匿名 | App e1be product-bff/session-proxy；IAM1ee8 native-session-admission unit，分别已有6407/1566默认门 | 旧cookie拒绝及当前UI另以正式旅程为准 |
| 错Origin | App native-sign-in route零relay调用；IAM native unit；BFF4d6 native-session-admission真实loopback零IAM调用 | BFF f81f271已纳默认入口，Root2350pass覆盖该native文件；后继新增风险仍单独补证 |
| 伪造tenant/subject与零写 | App session-proxy丢弃伪造身份；BFF user-admission已有零receipt/route oracle | BFF相关fixture仍Bearer/raw，I29时承接到native生产准入；body自报身份单独核，不外推header测试 |
| 失效/错surface服务凭据 | IAM direct-service-authenticator现有rotation/malformed/unknown矩阵 | 参数当前只Billing/execution，无session_admission；沿现矩阵与host补该purpose真实接线 |
| 重复登出 | IAM真实host长旅程仅一次sign-out | 私有重复revoke命令不是重复登出；沿原logout补重复请求/终态/旧cookie保持拒绝，状态按owner契约 |
| 撤权旧请求 | IAM1ee8两host66pass覆盖tombstone/旧cookie/SID重放；BFF旧replay零额外route | native化承接现幂等回放拒绝风险；UI/跨标签迟到独有证据归正式旅程 |
| IAM不可用 | App mock BFF unavailable；BFF旧Bearer/缺配置fail-closed | native配置齐全但IAM连接失败/超时仍待BFF现loopback补503/有限时间/无重试/零业务调用，不关共享服务 |

矩阵不新增任务中心或自动生成重复测试；I-29/I-30/31都在G1前收口，G2生命周期/旧实现删除保持后继。

**I-28已复现与最小纠偏**：bad205正式run c2e12b5a失败于异tenant双401断言；私有40e265df实证session401/native_session_required、projects403/product_tenant_forbidden。只读沿IAM→BFF→App证实该403正确；其他exact session删除/成员撤销仍401，退出匿名仍200/false。唯一writer仅driver/native runner/现native测试，先补typed code/status拒绝负控，再同步三处精确oracle；不改产品、不允许泛化401|403。I-27传输修复已过主方108定向及正式真实profile barrier，该完整旅程仍待I-28后重验。

**G1额外收口，不能只看浏览器5/5**：I-29当前旧Bearer生产消费已复核为零，当前合同消费者已配对；后继owner新版仍按契约正规生成。§5.1已完成分层负控映射，仅补缺少的真实组合接缝。IAM PlatformWorkloadController仍装配而目标消费者为零，明确归T11退休，不伪称已删除或合法公共OAuth；fixed-Web原生guard仍用IAM_PRODUCT_WEB_CLIENT_ID，与App短期sign-in/CSRF交互状态均合法保留，不按字符串误删。Capability f515 receiver-only已验足够此切片，最新base整合仍归G3。后继T-17/T-11不提前实施。

**历史运行检查点（已由I-33续接）**：I-26修复已提交50ac142b并完成Root完整门；正式run8160b600已越过cold_login UI/profile而在tenant_rejection_recovery失败，整体收据仍0/4（失败路径不输出部分成功计数）。I-27主控私有诊断确认原fetch“TLS建立前连接断开”、upstream_status=null，同一真实请求经自有loopback/原Host/cookie返回200；不是认证失败。以下第1项实现已交付，第2项重验发现的新阻断由I-27承接。

**I-27最小写区与验证**：只修改既有Chromium driver和native runner测试文件；将config传入profileBarrier，route.fetch显式指向`https://127.0.0.1:<owned port>/api/account/profile`，保留原request.allHeaders及固定原origin Host、4500ms/maxRetries0并禁redirect；现有App profile GET适配器自身拒绝上游Set-Cookie且成功响应不返回Set-Cookie；本driver不建立新的cookie投影。保原真实response/status/subject与fulfill，不绕过owner或造成功。主方已获得实际RED/同请求200对照，接收最小行为回归后实现、独审、停写门、精确提交再正式复跑。

1. **已交付设计／Root／T-05＋I-26**：在既有共享smoke代理增加仅Web实例启用、精确`GET /_next/webpack-hmr`的Upgrade路径；固定自有Next上游，严格握手/101双向转发、有限连接/空闲/总时长预算和断开回收。不支持任意CONNECT或动态目标，不记录frame/cookie；普通HTTP/SSE、body上限与默认smoke行为不变。先查现有可复用实现，再在现有代理测试补握手/双向/EOF/关闭/禁用负控RED，随后实现与独审；不关闭React debug channel或增加登录等待掩盖问题。
2. **主控验证／T-05**：代理定向及Root相关完整门→停写提交→正式四旅程原断言重跑。保持自然签发cookie、精确owner绑定与凭据私有管道；若HMR已通而UI仍不就绪，继续定位实际挂载原因，不先关闭I-26或G1。写区限定共享代理、其现有测试及native runner必要的显式启用接线；无App/IAM生产、Schema、依赖或lockfile变更。
   **组合依赖边界**：G1按当前已冻结、已验证的Capability f515组合判断认证门，不等待最新base整合；I-25/T-09整合在最终G3前完成，新组合重跑受影响G1回归。这样不形成G1等待T-09、T-09又等待G1的循环。
3. **G1→T-17/T-11／BFF**：生命周期真实释放通过后，按feature迁移原消费者并删除raw/aggregate；不提前删除测试或创建第二套运行时。
4. **T-09/T-16/T-15／Root与owner**：保留双方更新整合Capability publication冲突，完成Agent及受影响owner最终门、组合E2E和可同步环境。每仓独立PR，未完成前不合main。
5. **原A产品阶段**：G1～G3通过后才进入A-01/A-02→A-07；其余原A任务继续保留。当前原16项没有逐项剩余工作量与已配对端到端验收，故尚无可信完整完成日期；不把“未验收”解释为全部从零实现。下次估时须标明范围、基线、依赖、实际剩余量和置信度，而不是滚动重复3～7日。

**本次I-29消费者核量（不是全A总工期）**：基于BFF105024d实际Nest生产调用链的只读盘点，原先owner+BFF合计1.5～3人日低估了隐蔽消费者和认证测试迁移。修正为BFF本片约**5～10工程人日，中低置信度**；以熟悉本仓的工程师有效投入衡量，不是Agent墙钟承诺，也不除以Agent数换日历天。

| I-29 BFF工作包 | 剩余工程人日 | 核量依据 |
| --- | --- | --- |
| 固定artifact/共享认证底座 | 1～2 | 正规生成、必需native接口/显式proof、严格解析与服务401分类、wrapper/shared double |
| Skills实际消费者 | 1.5～3 | action/import、publisher enrich/specification、download/share末验、App binding第二Bearer |
| Account/Team/Admin/Billing | 1～2 | 共享Team client、全部成员分页、Billing末验及typed错误 |
| MCP消费者 | 0.5～1 | 现闭集helper/DI及原公共OAuth/service-only负控 |
| 本片集成/审查/返修 | 1～2 | 真Nest HTTP/实际IAM配对、零副作用/末验、完整相关门 |

前提为IAM正式artifact满足D0且可运行、既有资源可用，无新增owner/Schema/协议裁决。该量包含本片认证fixture迁移，**不包含**IAM剩余、其他owner的I-31、T-17、T-11剩余raw全删、Capability整合、Agent全门、G3环境或A01～16；后续T-11核量须扣除本片已迁测试。首条wrapper＋publisher＋Billing分页真实链闭合后据实收窄，而不是每轮重新启动“5～10天”倒计时。

**历史容量预算（I-30/I-33交付前的工程判断，非当前剩余）**：当时替代未纳入 I-29～31/I-33 的旧5～12人日，仅估C前置阶段而非整个Task A。现I-30/I-33已交付、I-29设计已通过；下表保留估算基准，不把已关闭工作继续计为剩余，也不重新滚动倒计时。当前剩余以T-05中的I-29/I-31、T-17/T-11、T-09/T-16/T-15为准，首批IAM实现后据实际工作量再更新。

| 当时C阶段工作包 | 当时估计工程人日 | 退出条件 |
| --- | --- | --- |
| I-33定位/最小修复/正式四旅程 | 0.5～2 | 同请求因果证据、回归、原断言四旅程完整通过 |
| I-29 owner授权适配与生产回退删除 | 1.5～3 | 先IAM设计/artifact，再BFF消费；有效权限承接且旧浏览器入口零消费者 |
| I-30受控native生成消费 | 0.5～1 | 正规生成/重复schema删除/contract保护/默认入口纳入 |
| I-31 native负控补证 | 1～2 | 风险→case→SHA→结果→零副作用映射齐全，不重复已足够的测试 |
| T-17真实生命周期 | 1～2 | shutdown/drain/SSE/worker/PG/Redis释放与失败边界 |
| T-11 raw/无边界聚合删除 | 2～4 | 按feature迁消费者、风险承接、旧项删除、零引用及行为复验 |
| T-09/T-16/T-15集成与同步环境 | 2～4 | 保留双方更新整合、最终owner/组合门、可同步环境及回收说明 |
| **当时C阶段合计（非当前剩余）** | **约9～18人日** | G1/G2/G3均达到退出条件才关闭当前Goal |

前提：持续有效投入、既有资源可用、I-33属局部问题、没有新增owner/Schema裁决。I-29～31共享部分BFF写区，G1→生命周期→删除→最终组合有串行依赖；不能除以Agent数得到日历天数。复用已验成果，不把历史未验项目都算作重做。其中I-33根因与IAM授权D0现已明确；首批IAM实现/消费者及raw迁移有实绩后，再按实际剩余消费者重估，不是每次会话重新倒计时。

**完整A的估时缺口（原16项未缩减）**：

| 原A范围 | 当前可确定的剩余类型 | 还需核量 |
| --- | --- | --- |
| A-07 / A-08 | 明确缺Project Todo写操作、附件发送/Run绑定/读取资格 | 设计、契约和消费者具体改动；不拿Run Todo/导航代替 |
| A-01/02 | 已有实现且有明确语义/展示待修边界，不是仅缺测试 | localDraft/retry/retire、导航/多标签/迟到；RunDisplay分组/身份/历史/回焦的当前case与实际缺陷量 |
| A-04/05/09/10/14 | 已有实现或历史子链，当前恢复/压缩/资料库/产物/语音完整验收未齐 | 当前commit的实现—case—收据映射；未验不等于全量重写，也不承诺无代码修复 |
| A-06 | 项目上下文已有部分成果，菜单/排序/删除释放等支持面未核量 | 逐动作实际差距，不按页面名称计算完成 |
| A-03/11/12/13 | 当前支持面和剩余量未逐项核实；A-12需原writer交接，A-13对应外部末端有条件依赖 | 输入控制、实际支持场景、自动化DST/重投/结果、外部账号callback/过期；不将末端条件扩大为全A阻塞 |
| A-15 / A-16 | 体验缺陷未按页面量化；已有多仓draft PR，仍须随片验收/配对 | 缺陷与性能基线、交付成本；当前不merge main、不发布 |

完整A当前没有有依据的总日期。本次已完成原16项文档证据分类，A-07另窄核canonical OpenAPI仅listProjectTasks及repository列表读；A-08原handoff明确缺选择→发送→Run绑定/读取资格。没有任何完整A行因本次盘点新增标完成。上述分类不是全产品源码审计；原 **0.5～1工程人日只读盘点预算** 尚须补支持动作/缺陷量及当前case映射才能给全A总范围，可与C实施并行，不提前写A功能。

本次Goal保持active，未创建重叠目标或将任何未验条目标complete。后续交接注明“主控下一动作”，不将worker等待当作需要用户再次发送“继续”。

## 6. 验证与风险控制

### 本轮文档交付

- `git diff --check`；本轮改动Markdown的本地链接检查。
- 独立review核“当前/历史、候选/Root验证、C/A边界、问题→TODO→关闭证据”一致。
- 本轮只核现有提交/收据并更新文档，未运行业务测试或启动服务；旧1pass/2fail属于初始文档轮历史，不作为本轮结果。文档轮不重跑全部业务门、不安装Schema。

### 后续执行与最终验收

命令在对应owner目录执行，先核manifest/CI，不假定每仓同脚本：

| 范围 | 命令 / 证据 |
| --- | --- |
| BFF | `pnpm format:check`、`pnpm lint`、`pnpm typecheck`、`pnpm test:architecture`、`pnpm contract:check`、`pnpm test`、`pnpm build`；默认脚本已覆盖的步骤避免无意义重复；真实PG/Redis条件测试另列 |
| App | `pnpm check`（contract、architecture、lint、typecheck、test、build）；真实浏览器使用关闭preview的native模式，默认preview E2E不替代认证验收 |
| IAM | `pnpm sdk:check`、`pnpm verify`与相关真实native/profile/撤权integration；核verify覆盖后不重复等价全门 |
| Agent | `uv lock --check`、`uv sync --frozen`、`uv run ruff format --check .`、`uv run ruff check .`、`uv run pyright`、`uv run pytest`、`uv build`，资源marker按真实依赖补跑 |
| Capability及实际受影响owner | 读取各自AGENTS/README/manifest，执行格式/lint/types/contract/test/build及本次真实I/O；未触及的owner不无端重写 |
| Root | `78105bb683047861d13a508340469d97a97b0432` / 原draft PR66；当前I55原driver/test待交付 | 四仓精确pin保持。I54原helper实际Next build、Root完整2105/3SKIP/531subtests与Ruff已验并推；正式重跑已进入tenant_rejection_recovery，但旧card可见oracle失败，整体0完成且全回收。I55真实DOM/非空draft同Session恢复诊断已验，原oracle已窄修，Root最终2116/3SKIP/531subtests、Node/Ruff及独审CLEAR；五文件追加交付后正式5旅程另验；Agent未pin/C4 OPEN |
| 真实链路 | 精确source/clean preflight、owner health/readiness、认证与业务负控、持久事实回读、取消/重试/恢复、全部自有资源回收 |

暂停入口 `verify-ten-repository-full.sh` / `run_stage2_owner_health.py` 不作完成证明；System smoke只证明自己的链路。

回滚使用原切片/精确gitlink与前一已验组合；不覆盖其他人未交接修改。凭据/共享数据不回滚或重置。仅在原有风险被承接或需求正式废止后删除测试；不删失败断言、加timeout、改历史hash或恢复fallback来通过门禁。用户本轮明确授权按仓各自PR交付，未完成前不merge到main；候选可提交/推送并维护draft PR，Root只更新已推送子仓精确gitlink。发布部署不在本轮范围。

## 7. Goal / TODO 后续更新规则

1. **触发时机**：新问题、写区/依赖变化、切片停写、测试结果变化、提交/pin变化、阶段验收时更新。纯对话无状态变化不制造新计划或重复全量运行。
2. **每条TODO记录**：原ID、owner、状态、依赖、精确基线/候选manifest、命令与exit/pass/fail/skip、未运行范围、下一动作。发现问题先登记再修，不让代码走在方案前面。
3. **唯一writer**：Root更新本表及阶段Goal；worker交接文件/结果/风险，reviewer只读核验。`task.md`/`CURRENT.md`同步简报，证据文件追加本次事实，旧证据不改写成当前成功。
4. **主方完成判定**：worker报告→独审→停写后的Root相关门→真实受影响旅程→精确组合。少任一必要层，只标REVIEW_PENDING/OPEN，不标VERIFIED整体。
5. **机器Goal**：每次阶段交接用`get_goal`核验；当前目标未完成时保留active。只在用户明确要求暂停时设paused；同一外部阻塞连续至少三个goal turns且无可推进工作才按工具规则blocked；G1/G2/G3全部达到才complete。不要为了更新文案虚假complete或重复create_goal。
6. **下一轮默认动作**：正式四旅程已通过，I-26/I-27/I-28/I-30/I-32/I-33/I-34不重复实施；先按已通过D0实施I-29 owner→消费者并补I-31/G1负控。T-14接收方不重复实施。G1闭合后T-17完整生命周期→T-11删除→T-09/T-16最终组合门→T-15同步环境；A功能继续门控。

### 历史暂停后续接检查点（已被下方 active 状态更新）

用户已明确继续。工具Goal记录仍显示paused；继续请求已撤销此前暂停指令，本轮不伪造状态切换，也不创建重叠Goal。阶段目标仍G1/G2/G3 OPEN，A门保持。

T-13五项修复已获规格/质量双审，六路径hash停写匹配；Root相关60pass/31subtests、完整治理1876pass/3skip/502subtests（exit0）。IAM真实两个host文件62pass/0skip，完整verify121files/1566pass/build通过，已推送e6a01cf与本仓draft PR #6。App/BFF原已验候选保持。三精确gitlink暂存后topology PASS；暂存前因旧pin的三项预期mismatch保留为阶段记录。当前等待Root提交后实际最小native，不把宿主测试或临时数据库隔离视为应用单库组合/浏览器四旅程。

### 历史阶段：首次真实 native 失败与当时下一动作

Root已提交/推送b2f9a59c，精确pin App9ba65343/BFF173e026/IAMe6a01cf。两次最小native在source clean/gitlink、Node、BFF build/schema及IAM host之后，于BFF startup失败，completed_checks=0；两次cleanup passed/quiescent=true、无保留workdir。诊断复现定位UnknownExportException：ChatModule导出CHAT_TURN_SERVICE，但该token由AgentDispatchModule拥有。此为T-17允许的前置启动修复，不等待G1，不扩展为raw消费者批量迁移。Skills/Projects导出与ProjectAccess/Billing数据库导入为只读同类候选，尚未逐个实测。

下一步由BFF唯一writer核对真实owner/module可见性，补实际Nest容器compile/启动回归（不只源码字符串断言），最小修复后Root完整门与精确pin再跑native。最小HTTP仍不替代四浏览器旅程；T-13清理仅在本次失败路径有实测证据，成功路径待后续。G1/G2/G3继续OPEN。

### 历史阶段：T-17 前置实现写区与接收过程

BFF唯一writer `bff_node24_generation`，基线173e026；限定chat.module、skills.module、projects.module、project-access.module、billing.module五个现有生产文件及现有nest-runtime-architecture测试。先真实生产AppModule容器compile RED，逐项纠正owner/module可见性；仅替换测试配置与外部资源，保留真实DI图/factory，不auto-mock缺失token、不重复provider、不global Database。新增文件/默认门接线需求先报告；生产写区外的新阻断先报告。worker不做Git/真实服务/完整门，停写双审后Root串行全门与native。T-14由独立只读角色完善owner局部设计，与BFF不重叠。

T-17范围补充：真实生产AppModule compile已依次复现五个RED（Chat/Projects/Skills非法导出，ProjectAccess缺BFF_DATABASE，Billing缺BFF_POOL），五处修复后compile GREEN。扩architecture出现72pass/2fail，系旧nest-feature-architecture两断言强制引用已删除的非法re-export；批准只将两断言核对迁至真实provider owner/模块导入，既有行为/路由断言保留，由真实DI及单实例回归承接风险。写区最终5生产+2既有测试，不改package/依赖；尚待停写双审与Root全门，不据worker GREEN称已可启动。

T-17前置候选已通过独立规格/质量审阅及Root冻结hash复核。Root完整format/check exit0：contract1344pass、default2344pass/0fail/2原资源skip、lint/types/build通过；不是全真实I/O。BFF实现4d6d17b沿原PR18交付，下一步精确Root pin后真实native。T-14 owner三面设计独立推进，只改三文档，不并行写生产。

### 已验阶段：Root535e7071 最小链路及当时T-14文档门

BFF4d6d17b / IAMe6a01cf / App9ba65343的exact SHA、clean、Root gitlink及实际Node均通过。诊断包装只在失败时捕获内存脱敏信息，不替换成功路径行为；本次生产BFF启动、App同源session/projects、fixture直接IAM signout后401及日志扫描共4checks PASS，cleanup PASS/quiescent，无保留workdir。仅最小HTTP，未覆盖真实登录/切tenant/App登出/独立撤权；不把process组退出当完整Nest drain/池优雅关闭证明。

T-14三面门已Root复核：复用policy/schema，当前auth-source摘要派生索引绑定接收分流，旧contract-only combined/冻结v9/既有BFF-Agent pin不动；caller取消保证不扩大到COMMIT已发后的原子零写，不宣称补全历史R328。仅三owner文档dirty，后继代码待独立writer按门实施。

### T-05验收纠偏与T-14实施写区

只读证据：App TECHNICAL_DESIGN §固定部署tenant（约3203–3228）明确删除Team selector与/api/team/switch；IAM设计约850–872允许第二tenant membership用于负例；BFF设计约3626–3634及user-admission.ts固定tenant不符即403；本轮G0设计spec约409仍固定Product tenant。因此纠正的是本计划“正向切双tenant”错误，不变更已批边界、不缩减当前隔离/撤权要求。新跨tenant产品能力不属于本清理片。

T-14 Capability唯一writer按三面门实施；Root已在44fcc5d建立codex/task-a-c1-capability，Node24.20.0/pnpm11.25 frozen install成功且lock不变。批准额外现unit/mcp-p3b的register取消负控及现skill-admin-admission测试迁至有效单用途准入oracle；任何业务/冻结协议扩区继续先报告。另Root独立writer仅处理三旧配置消费者及对应低层测试：不再要求/注入resource-server配置、不再生成其文件；IAM公开OAuth fixture协议及Root收到的secret保护保持。两写区互不重叠，完整门/真实服务/Git只由Root执行。

### T-05真实冷登录RED与Root消费者候选

Root使用现精确组合和全新Chromium context实测/login表单，不向浏览器注入fixture cookie。浏览器登录凭据仅从当前自有IAM fixture的get-session与公开测试密码在内存取得，走stdin，不留凭据日志；诊断收据仅状态。结果：form_present=true、signin303、session401、projects401。该诊断独立于原最小HTTP4checks，后者仍PASS且该run最终cleanup PASS/quiescent、无保留文件；不能拿原4PASS覆盖浏览器RED。App单writer按现固定Product语义准备修复，尚未源码验收。

Root三旧resource配置消费者候选6文件已停写并独审CLEAR；Root实际定向154pass/141subtests，源冻结在本地manifest。顺带同文件真实O_EXCL同名冲突已先RED后修复，未mock文件装配过门；IAM公共OAuth fixture接收字段/secret保护保持。Capability仍实现中，Root不先宣称该组合已可运行。

T-05 App修复局部门已确认：现sign-in路由内sign-in/email→新issuer cookie合并→原生set-active→现admittedNativeSession最终准入，才303进入产品。tenant沿现BFF/IAM credential opaque词法（1..255且无空白/控制字符），绝不新增UUID限制/浏览器选择。坏配置在凭据发送前拒绝；上游全序列共用一个有界deadline/取消信号，不每步重置预算。签入后续失败退休本次flow/CSRF、不发新issuer cookie、不清除请求既存issuer cookie、不自动重发密码/额外signout；新未交付session由现IAM TTL回收。成功按每cookie名称最后合法值发送，删除项不带入后继Cookie header。限现route、native-sign-in测试、env例和TECHNICAL_DESIGN/CURRENT；新helper/其他写区须报告。独立App writer，Root保留真实浏览器RED；最终完整门和浏览器GREEN由Root完成。

### T-05冷登录候选Root完整门与精确交付

App727cd674fd45487d3d9becc685701546623865b1：Root Node22.23.4/pnpm11.25.0完整pnpm check exit0，contract452、architecture50、full354files/6401pass/0skip、lint/types/build通过；1494tracked输入前后hash一致，独审CLEAR。仅五明确路径提交并沿原draft PR50推送，本次Root提交精确pin；未合main。浏览器冷登录GREEN/完整四旅程待验，不沿用原fixture4checks替代。

Capability71路径另获Root独立只读审查CLEAR及hash核验，完整format/lint/verify/Prisma/build按序运行中；终态以实际exit为准，不以worker123替代。

### 历史验收推进：冷登录GREEN、T14全门RED与后继设计

Root4fdb2ede精确App727/BFF4d6/IAMe6 source/clean/gitlink通过。全新Chromium context未注入cookie，真实表单303、session200、projects200；独立冷登录诊断与原最小HTTP4checks均PASS，cleanup PASS/quiescent/无保留资源。仅关闭I-21冷登录缺陷，不关闭T-05四旅程。

Capability首次Root完整门format/lint/Prisma validate/build均0，verify退出1：3049pass/678skip/2fail。两项为本次旧OAuth删除/有效Agent错用途导致的旧oracle：preflight期待泄露ENOENT但现execution reader抛sanitized错误；generated-client期待Code16但应为有效credential错surface的Code7。只授权两现测试精确承接typed失败、无监听/零写，保留RED，生产不因此改宽。待重新冻结后Root真实receiver及完整门。

I-24退出局部修复授权App唯一writer：现iam route、现真实transport测试（必要时原route测试）及CURRENT；先loopback真实RED，再按已批准空体POST补明确零长度Uint8Array，不放宽transport或新建helper。当前冷登录源码已提交，不在验收中重写。

T-05余下旅程的后继最小设计：沿现IAM native host增加test-only浏览器fixture、session绑定slot和有限switch/revoke命令；cookie从浏览器自然签发只在私有pipe/内存交接，owner验签并核本fixture同user、非seed exact session后才绑定；Root不SQL IAM。另建同一user合法第二tenant membership验证固定Product拒绝及真实重登恢复；App UI退出须核exact session消失；独立A/B浏览器分别验exact session撤销仅影响A、membership撤销时B session仍存在但准入拒绝。保持原最小smoke模式，新driver/模式显式扩四旅程；先停Chromium再Web/BFF/IAM，保现精确资源回收。具体写区限IAM native host/其integration、Root native runner/新Chromium driver/现runner测试。此处为当时设计记录；其中“退出session消失”已被§3.1的expired tombstone oracle替代。host与driver后续均已交付，当前结果见§0与T-05，不使用本历史交接状态驱动执行。

### I-24主方静态门与T14真实接收方GREEN

App1d54eedd4d67482c789ae3f7dd60807302732b24三文件退出修复已独审并经Root完整check exit0（contract452/architecture50/full6403/0skip、lint/types/build；1494hash保持），沿原PR50交付。本次Root仅更新App精确pin；真实sign-out及旧cookie重放另验，T-05仍OPEN。

Capability72路径修正canonical ownership断言后，Root真实HTTP→production receiver→隔离PG组1pass；13项为本次-t未选择，不计本组覆盖。System成功/自然重放/冲突/disabled不复活、BFF/Agent/未知凭据拒绝、文件删除后撤销、ownerTenantId/ownerUserId均null、零receipt/outbox/IAM请求均过；数据库inventory前后相同，Redis仅connect/ping/quit无key写入。不是System producer链。最终完整owner门再次串行运行中，尚不提前标全绿。

T14实际交付：Capability f515e225，PR13 OPEN/draft，base为原PR12候选分支；GitHub实际mergeable=CONFLICTING，明确不合并。Root配套六文件hash保持，再跑154定向/141subtests通过（前轮完整治理1879/3skip/506同源码）；本次Root提交精确pin f515并配对退休配置删除。I-25记录最新基线集成，不借旧已验组合否认他人四个新提交。

I-25只读集成调查已完成：共同基线44fcc；9重叠中5处文本冲突为provenance与四份设计/current文档，另checker/product-mcp.rpc/mcp.ports/architecture需语义复核。更重要的是远端mcp-private-server-v2-contract.ts从冻结父重建整份provenance，会拒绝/生成时删除T14认证索引；后继必须保v2精确contract发行及认证索引独立严格校验，并补生成保留/只读不写负控，不能重签父快照或删除索引。新Schema的global currentConnectorId=NULL需真实T14重验；B01 private/personal、fresh/父升级/回滚/代际撤权及Custom API真PG均随新组合重验。新B01消费者发布/正常Schema激活归其owner，不在本片擅自实现Task B；当前f515证据不继承到新合并树。本轮只读调查未合并、写对象或修改base分支。

App媒体类型修复e1be73e08bb1bd4c9c554c9e319f6b079006fdb5已Root独审与完整check exit0：contract452/architecture50/full6407/0skip、lint/types/build，1494输入hash不变。仅三文件沿PR50交付；本次Root精确pin后再次验真实App sign-out/旧cookie重放。I-24在真实GREEN前仍OPEN。

### I-24真实退出最终GREEN（Root1e6组合）

同一新Chromium未注入cookie，真实表单303、session200且authenticated=true、projects200；浏览器实际调用App sign-out返回200，session200且authenticated=false、issuer session cookie数量0，projects401，内存旧cookie独立HTTP重放401。原最小smoke4checks与cleanup passed/quiescent/无保留文件均过，原RED和匿名状态错误oracle留证。无cookie时session接口既有契约为200/false，不是401；修正临时driver为精确false+cookie0+业务401+旧cookie401，未放宽生产或删负控。仅关闭I-24及冷登录HTTP缺陷；本次不是Settings按钮点击，也未运行异tenant恢复/独立撤权完整四旅程。
