# Kokoro 当前系统与工作台技术总览

核对日期：2026-11-11 UTC。本文描述 Task A 已交付的实际边界，替代旧三主仓／独立 Session 服务／临时认证引用方案。它是工程首读页，不是另一份可编辑 API、SQL 或状态机契约。

当前产品操作见 [App 文档门户](https://github.com/LordFoxFairy/kokoro-app/blob/2b2522b784492c248d3a95e6530fba9b03f562b4/developer-docs/docs/product/index.md)；批准的产品要求见 [PRD](../product/09-v2-prd.md)；当前组合及暂存项分别见 [CURRENT](../../CURRENT.md)、[TODO](../../../todo.md)。

## 1. 一条产品链，不再保留旧入口

```text
Browser
  → App 同源 adapter
  → BFF（业务入口、Conversation/Message/Project、durable AG-UI）
  → Agent HTTP / 独立 Worker（Run、lease、checkpoint、工具与恢复）
  → 各业务 owner 的正式接口

Agent / BFF 的 AG-UI 事件 → BFF 持久 ledger / cursor / replay
  → App 本地适配 → Vercel AI SDK UIMessage → 聊天与结果面板
```

网络执行事件使用 AG-UI；AI SDK 是 Web 阅读和恢复视图的工具，不是第二套传输协议。BFF 只有 Nest 原生 listener 和按业务能力装配的 Module/Provider，不恢复 `LegacyRoutesModule`、旧 bootstrap dispatcher、全局 Service/Repository locator 或机械四层。

## 2. 事实由谁维护

| Owner | 维护的事实 | 不做什么 |
| --- | --- | --- |
| App `apps/kokoro-app` | 页面、草稿、同源 adapter、AG-UI 到 UIMessage 的本地映射 | 不持第二套登录 Session，不直连内部业务 owner |
| BFF `apps/kokoro-bff` | 会话、消息、项目、定时任务业务、分享投影、提交 outbox、事件重放 | 不读其他 owner 的数据库，不拥有模型执行 loop |
| Agent `apps/kokoro-agent` | Run、lease、checkpoint、工具 journal、审批／取消／恢复、执行输出版本 | 不复制 SDK 的 loop，不拥有项目或积分账本 |
| IAM | 原生身份会话、成员与动作／资源权限 | 不把内部服务身份等同用户许可 |
| Storage | 对象、扫描、上传／下载资格、精确字节及目的释放 | 不猜 Run 路径或持有第二份项目关系 |
| Scheduler | 到点 occurrence、投递与重试 | 不直连 Agent 执行、不取代 BFF ScheduledTask |
| System / Billing / Capability | 模型配置／资金账务／Skills 与 MCP 等各自业务 | 不变为共享状态或通用权限中心 |

完整路径以 [.gitmodules](../../../.gitmodules)、[仓库组合](../../REPOSITORY_STATUS.md)为准。Admin 是独立前端工程，走同源 `/manage`，共享 Product 登录，不新增身份 owner。Mori 与共享前端库不因本轮工作台收尾改变职责。

## 3. 原生登录与内部调用

1. **IAM 唯一拥有原生登录 Cookie、数据库 Session 和续期。** App 提供同源薄 adapter，Admin 复用同一链；BFF 认证边缘使用官方 `get-session`，不维护另一套 RP Session／refresh token／Session-ref。
2. **受保护请求先取得当前身份。** 普通业务入口禁 Cookie 缓存和隐式刷新，核用户、有效期、固定产品租户与当前成员资格，然后建立可信 principal。撤销后的下一次入口检查拒绝，不宣称已准入的在途跨 owner 副作用可全局原子收回。
3. **普通 IAM 业务使用服务身份＋可信 actor。** BFF 的 actor 只取本次认证结果，不信任浏览器自报 user/tenant。接收方直接服务认证，不在内部反复 OAuth 换票；普通业务不搬运人类 Cookie、Origin、Session ID/ref/proof 或用户 Bearer。IAM 仍按当前用户／成员／具体动作和资源检查权限与审计。
4. **账户会话管理是具名例外。** 本人会话 list/revoke 同时验证专用 peer 凭据、原生 issuer Cookie 和 exact Origin，保留当前会话保护、事务及撤销语义；目标 session ID 是被管理资源，不是通用认证引用。第三方 OAuth、执行授权和资金授权各自保留正式合同。
5. **浏览器只拿安全状态。** BFF 的 session 状态投影不暴露完整 Session；续期入口和业务准入分开。依赖故障不伪装成退出登录，未知写入不自动重放。

有效决定见 [ADR-034](../decisions/ADR-034-independent-admin-web.md)、[ADR-035](../decisions/ADR-035-direct-internal-service-authentication.md)、[ADR-036](../decisions/ADR-036-bff-nestjs-convergence.md)。详细 wire 以 IAM/BFF 当前 owner 合同和生成消费为准。

## 4. 一次消息怎样走到结果

- App 提交公开选择；BFF 先处理同键重放，新请求在数据库事务外解析必要的 Storage 元数据，最终在本 owner 事务内重核关系并冻结唯一 launch、Message 与 outbox。
- 公开资源选择只带 opaque 身份；Asset、历史 Artifact 和最终答复使用各自正式来源。最终答复私有字节不复制到公开 Message、分享或诊断。
- 唯一 dispatcher 把持久提交送至 Agent；Agent 依据已保存 Run、当前 lease 与冻结输入读取资源，不凭文件名猜资格。恢复同 Run 保留原事实，不静默改用新指令或新来源。
- 工具／审批／取消和终态进入原 journal 与事件链；同会话排序、未知结果和断线恢复沿正式持久事实处理。Stop 接纳不等于执行已经结束。
- App 从正式消息、事件和结果恢复 UIMessage；迟到响应不覆盖新账号／租户／路由。草稿不是已提交 Message。

## 5. 文件、Canvas 与定时任务

**文件**：正式交付与过程输出是两类来源。Agent 持有精确 Run/version／路径／摘要与发布事实，Storage 维护 CLEAN 与精确对象，BFF 核当前本人会话／项目关系。Canvas 读指定不可变版本，不从可变沙箱路径回读猜结果；只读预览、下载和格式限制见产品指南。会话／项目删除撤可见资格与对应释放，不把逻辑拒读冒作未知对象的物理清除。

**定时任务**：Scheduler 到点回调 BFF，BFF 接入同一普通 Chat turn、outbox、dispatcher 和 AG-UI 终稿链。已接纳、排队、成功、失败和取消分别展示；Updates 由已有执行事实投影，结果链接打开真实会话，不再维持独立终稿 reader 或 Scheduler→Agent 直连。

## 6. 数据与契约维护

- Root 只锁精确 gitlink 和跨仓治理，不保存可编辑业务 DTO／ORM／API 中心。owner 发布固定 commit、版本与摘要的合同，消费者使用正规生成流程。
- PostgreSQL 是持久真源；本地应用目标为一库、同一应用凭据、每 owner 独立 schema，共享 Redis 隔离 namespace。已有环境是否完成保数据交接必须实际核验，不能仅改 URL。
- schema 安装和隔离 fresh 测试不等于允许重建已有卷；不跨 owner SQL、不清共享数据库／Redis／桶。
- 子仓默认测试属于子仓。Root `scripts/tests/` 只测治理；跨仓组合证据在 `verification/` 及已忽略的本地收据中，不复制所有单元测试再跑一遍。

## 7. 已验范围与仍保留的限制

Task A 按用户确认的开发交付口径收尾，不等于外部生产环境全部通过。Root 基线 `bdebba56` 保留精确已验子提交；IAM、Admin、Storage、Agent、BFF、App 的原 PR 已合 main。Capability #13 仍叠在其他 owner #12，上游栈保留；继承 Billing/System pins 不借本轮合入其独立工作。Task B 不由 Task A 接手。

| 验证片 | 实际结果／边界 |
| --- | --- |
| 原生登录／退出／撤权与共享 Admin | 正式组合浏览器证据已验；不扩大为全部 Admin 业务验收 |
| 附件→Agent 实读→AI SDK 展示→刷新 | 真实浏览器与独立 Worker；历史 FINAL／最终答复、Project 草稿与同 Run 恢复有对应证据 |
| 定时到点→BFF→Agent→Updates／终稿 | 真实 Scheduler、BFF 和独立 Worker；模型／System／预算为明确确定性夹具，不称供应商生成验收 |
| E2B→Storage CLEAN→Canvas 两版本／刷新 | 官方 envd 0.10.0 Docker＋锁定 SDK 真实进程／文件协议；整轮及物理容器回收通过，未验云控制面生命周期 |
| 外部账号／语音／支付 | 三个真实渠道、最终本人语音编辑发送暂存；真实支付关闭，未称通过 |

源码证据与历史失败可从[收尾基线的原计划](https://github.com/LordFoxFairy/Kokoro/blob/bdebba56a046703400845f79ae57834d4dfa4d0a/docs/superpowers/plans/2026-11-01-task-a-c1-c4-technical-plan.md)追溯；当前行动只维护 [TODO](../../../todo.md)，不把旧执行门恢复成新阻塞。当前实现与未来目标不混写。

## 8. 去哪里看细节

各子仓 `docs/TECHNICAL_DESIGN.md`、`docs/API_CONTRACT.md`、`docs/DATA_MODEL.md` 和 canonical contract/schema 负责本 owner 细节。[总体架构](../../ARCHITECTURE_STANDARD.md)和有效 ADR 管长期边界；本文不复制接口字段与整张测试表。

公开门户只发布 App `developer-docs/docs/`，产品指南与生成 API 参考分开；内部三设计、机器日志、凭据和验收原始 payload 不进入搜索索引。`/docs` 帮助链接的实际部署挂载另行核验，本轮未部署。
