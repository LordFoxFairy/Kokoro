# Kokoro 仓库现状与 TypeScript 工程审计报告

- 日期：2026-11-11。
- 审计工作区：`/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro`。
- Root 精确基线：`32c56199a74e61bd757d6c69ee17efcd7904d16a`。
- 目的：为统一整改提供依据；第1～7节是只读审计快照，第8～9节记录用户随后授权的实施范围与深入核验。审计本身未修改业务代码，后续修复状态以唯一TODO和交付基线为准。
- 方法：主控核仓库组合、治理脚本和证据；三名只读代理分别检查 IAM/OAuth、BFF/Admin、其余 TypeScript 仓。属于入口及关键链路审计，不是所有源码逐行安全审计。
- 当前执行状态先读[唯一TODO](../../todo.md)和[最新主线§17](#17-主线范围纠偏与最小清理)；第1～7节是原始快照，不把已修问题继续当当前故障，Mori不属于本轮后续实施范围。
- **Task B 保持其原负责人和 PR。本报告检查的是当前 Root 固定组合，不代表其未合并分支的最终状态。**

## 1. 先说结论

**有实质问题，但现有证据不支持“整个 BFF／IAM／OAuth 都严重失控，必须推倒重来”。**

优先处理的是：
1. IAM 业务准入的共享限流桶，可能让不同用户相互影响。
2. IAM 原生全设备撤销受保留 Session 行数上限影响。
3. Admin 部分导航仍连接旧后台壳，页面可见不代表业务已接通。
4. BFF 已有 PostgreSQL 幂等回执仍重复保存在无容量上限的进程 Map。
5. 原生认证与 Mori adapter 的时间／取消边界、生成检查副作用、共享源码双份和工程入口文档漂移。

其中前两项是**源码机制已确认、实际发生频率及端点行为仍待定向复现**；后台缺失接线已由当前路由和消费者证明。本轮没有证明可直接越权／提权的漏洞，也没有生产流量或线上故障证据。

**不建议：** 全仓重写、再建认证中心、把所有内部调用改 OAuth、为每个模块强加 Repository／Service／Port、按行数机械拆文件、为了审计数字归零重跑全产品测试。

## 2. 到底有多少仓库

**13 个 Git 仓库 = 1 个 Root + 12 个子仓。** 其中 11 个在 apps 下，1 个是共享库。语言按主要运行实现分类，不把测试夹具中的少量其他语言计为新仓库。

| 仓库 | 主要实现／形态 | 职责 | 本次固定提交 |
| --- | --- | --- | --- |
| Kokoro Root | Python 治理脚本、文档 | 精确组合与跨仓治理，无业务服务 | `32c56199` |
| kokoro-app | TypeScript／Next／React | 用户工作台、同源 adapter、AI SDK 视图 | `b93acbd893fbc584643c3e72b9340943653e51e7` |
| kokoro-mori | TypeScript／Next／React | 音乐产品 preview 与 adapter | `12a1060830e1239c2ccb866baeefa4546ec04bb5` |
| kokoro-bff | TypeScript／Nest | 产品 API、Chat／Project、事件持久投影 | `0895e254fc48a7ab62ede5d5433a7fc82eb6b722` |
| kokoro-iam | TypeScript／Nest／Better Auth | 原生登录、Session、身份与权限、外部 OAuth | `b6a9745b340149808afb1aae357574d0aa7bbad3` |
| kokoro-system | TypeScript／Nest | 站点、工作区、模型配置 | `49a5f8e5e2797ec2d1a6fcf8c5f398184821bf33` |
| kokoro-billing | TypeScript／Nest | 积分、用量、资金账务 | `b7c9858844df4c9b99e40e16bd9984b1d268b503` |
| kokoro-capability | TypeScript／Nest／ConnectRPC | Skills／MCP 控制面 | `24094960bad58d1b6a85a273d3bc94b0a0e0d1dc` |
| kokoro-storage | TypeScript／Nest／ConnectRPC | 上传、对象、扫描、版本与交付 | `b60931e9e4e92d596b0678cbdabd9116e898b432` |
| kokoro-admin | TypeScript／Next／Ant Design | 共享 Product 登录的独立后台前端 | `95c504d1bfdcf1038ebadb85d8493c18828b51f7` |
| kokoro-web-shared | TypeScript／私有包 | i18n、web-core、tsconfig | `0c4e87ace01340aaa07bc57935f1d98b8e77af14` |
| kokoro-agent | Python | Run、Worker、工具、恢复 | `a9021318b33f2e34e44e960a6f1632f7bb21bd15` |
| kokoro-scheduler | Go | occurrence、到点投递和重试 | `cfb2502b0ef9331f79a328ec85c254157340962c` |

因此，**TypeScript 主实现子仓共 10 个**：6 个后端（BFF、IAM、System、Billing、Capability、Storage），3 个前端（App、Mori、Admin），1 个共享包仓。Scheduler 不纳入本轮重构评估；Agent 也不展开实现审计。

固定身份以 [.gitmodules](https://github.com/LordFoxFairy/Kokoro/blob/32c56199a74e61bd757d6c69ee17efcd7904d16a/.gitmodules) 和实际 gitlink 为准。子仓 checkout 的 HEAD 与其 main 合并提交可以不同；本轮读取的是表中实际固定提交。

## 3. BFF、IAM、OAuth 应怎样理解

### 3.1 当前真实边界

```text
Browser
  → App 同源 adapter
  → BFF：校原生 Session、当前产品租户／成员资格
  → 内部 owner：专用服务身份 + 已认证 actor + 本 owner 业务授权

Admin → 同源 /manage → 复用 Product 登录与后台资格
外部应用／第三方连接 → 各自需要的 OAuth 授权链
```

- BFF 原生准入调用官方 get-session，禁 Cookie cache；普通业务准入不隐式续期。见 [SessionAdmissionTransport](https://github.com/LordFoxFairy/kokoro-bff/blob/0895e254fc48a7ab62ede5d5433a7fc82eb6b722/src/auth/session-admission.transport.ts#L4-L17)。
- 普通 BFF→IAM 业务是直接服务身份加可信 actor；IAM 明确拒绝该分支夹带 Cookie、Origin、Session-ref。见 [InternalAuthGuard](https://github.com/LordFoxFairy/kokoro-iam/blob/b6a9745b340149808afb1aae357574d0aa7bbad3/src/modules/auth/internal-access/internal-auth.guard.ts#L410-L452)。
- 本人会话管理的 Cookie／Origin 是具名例外；它管理原生 Session，不是让所有内部业务携带 Cookie。
- 已保留服务身份、用户权限、执行授权的区别；不能把浏览器自报 userId 当身份，也不需要为普通内部业务新增一套用户 OAuth token。

**因此：整改应收敛现有实现，而不是再把内部认证方向推翻一次。**

### 3.2 与官方实现的对齐判断

Better Auth 官方将 Cookie Session 和 OAuth Provider 分为不同用途：前者承接应用登录，后者供其他应用进行授权；RFC 9700 的 PKCE、重定向等要求适用于对应 OAuth 流程，不是内部每跳都必须换票的要求。参见 [Session Management](https://better-auth.com/docs/concepts/session-management)、[OAuth Provider](https://better-auth.com/docs/plugins/oauth-provider)、[RFC 9700](https://www.rfc-editor.org/rfc/rfc9700.html)。

这些在线文档用于辨别协议职责，不替代本项目锁定 Better Auth 1.7.3 的实现证据，也不据此自动升级依赖。**本轮未完成所有外部 OAuth grant 的逐端点安全审查。**

进一步澄清：OAuth client_credentials本身也是标准化的机器认证方式，见[RFC6749 §4.4](https://www.rfc-editor.org/rfc/rfc6749.html#section-4.4)，不能将“内部采用OAuth”笼统判为违反后端技术规范。**本项目已选专用服务凭据，问题是残留换票／双轨或无收益的重复步骤，而非OAuth这个协议本身。** 在线成员／资源／执行权限判断也不等同OAuth换票，删除前必须追到实际调用和授权事实。

## 4. 重点问题与最小修复方向

“优先”表示下一轮先处理的影响面，不表示已证明生产事故或严重安全漏洞。

### R-01｜优先：不同用户共享 IAM 准入限流额度

**证据：** [IAM 限流键](https://github.com/LordFoxFairy/kokoro-iam/blob/b6a9745b340149808afb1aae357574d0aa7bbad3/src/modules/auth/internal-access/internal-auth.guard.ts#L497-L505) 只有 caller、credentialId、operation，固定 100 次／60 秒，没有 actor；[BFF Session 准入](https://github.com/LordFoxFairy/kokoro-bff/blob/0895e254fc48a7ab62ede5d5433a7fc82eb6b722/src/auth/session-admission.client.ts#L110-L156) 每次均调用 authorization.check。

**影响：** 同一 BFF 凭据下所有用户竞争同一操作额度，页面并发读取也消耗它。某用户的请求可能让其他用户收到 429。源码阈值确定；实际用户量、调用放大率及是否已触发未测。

**已有保障：** Redis 原子计数、429／Retry-After 与当前成员资格鲜读仍在，不存在限流失败后放行的证据。

**最小修复：** 区分接收方总容量保护与用户公平性额度；按真实容量设定，不直接取消限流，也不增加 token 缓存。最低验证为两个 actor 共用服务凭据时不互相耗尽用户额度、总量保护仍生效。

**归属：** IAM 主改、BFF 消费回归；与 Task B 登录／账户范围交接后实施。

### R-02｜优先：历史 Session 保留量会阻断原生“撤销全部会话”

**证据：** [adapter 目标上限](https://github.com/LordFoxFairy/kokoro-iam/blob/b6a9745b340149808afb1aae357574d0aa7bbad3/src/modules/auth/better-auth/account-session-adapter.ts#L60-L72) 最多取 501 行，超过 500 即 invalid_grant；[终止入口](https://github.com/LordFoxFairy/kokoro-iam/blob/b6a9745b340149808afb1aae357574d0aa7bbad3/src/modules/auth/better-auth/account-session-adapter.ts#L146-L160) 在此之后才执行撤销；[生命周期实现](https://github.com/LordFoxFairy/kokoro-iam/blob/b6a9745b340149808afb1aae357574d0aa7bbad3/src/modules/auth/account-sessions/account-session-lifecycle.repository.ts#L47-L90) 以到期保留行，并撤销关联 token。

本机锁定版本的 Better Auth 原生 revoke-sessions→deleteUserSessions 按 userId 调用 deleteMany；当前配置未走 secondaryStorage＋preserveSessionInDatabase 的 live-only 分支。因此，**500 条已到期保留行＋1 条有效 Session** 即符合失败机制，而非一定需要 501 台在线设备。

**限制／反证：** 已有[每小时清理、24 小时 grace](https://github.com/LordFoxFairy/kokoro-iam/blob/b6a9745b340149808afb1aae357574d0aa7bbad3/src/modules/auth/cleanup/expiry-cleanup.config.ts#L3-L28)，不是永久积累；但它不保证目标始终低于 500。原生 revoke-other-sessions 过滤有效 Session 后逐条删除，不直接等同此失败路径。未查询真实用户行数，未跑端点复现。

**最小修复：** 区分已结束墓碑与有效撤销目标；保留会话锁和关联 OAuth token 失效，明确有效目标本身超过上限时的策略，不只把 500 改大。最低验证先复现“500 墓碑＋1 有效”的官方 endpoint，再检查撤销结果及子凭据。

**归属：** IAM／Task B 账户生命周期负责人。

### R-03｜优先：Admin 部分可见页面仍是未接通的旧壳

**证据链：**
- [导航和上下文](https://github.com/LordFoxFairy/kokoro-admin/blob/95c504d1bfdcf1038ebadb85d8493c18828b51f7/components/shell/app-shell.tsx#L62-L125)：仍展示 users、teams、payment、sites、approvals、audit、operators；sites／manifests 永久为空，reloadSites 只清空。
- [operators 页](https://github.com/LordFoxFairy/kokoro-admin/blob/95c504d1bfdcf1038ebadb85d8493c18828b51f7/app/%28console%29/operators/page.tsx#L1-L6) 指向旧 API；[approvals 页](https://github.com/LordFoxFairy/kokoro-admin/blob/95c504d1bfdcf1038ebadb85d8493c18828b51f7/app/%28console%29/approvals/page.tsx#L95-L122) 同样读写缺失入口。
- 当前 Admin 只有 me 与 v1/admin 两类 route handler；[Next 配置](https://github.com/LordFoxFairy/kokoro-admin/blob/95c504d1bfdcf1038ebadb85d8493c18828b51f7/next.config.ts#L13-L21) 没有为这些旧 API 提供 rewrite。
- Product 仅将 /manage 整体转发 Admin；旧请求经 Admin 路径包装后仍落在该挂载内，不会自动被 Product 其他 adapter 接住。

**影响：** users 卡在选站点，manifest 类页没有可用资源，部分端点页会请求未实现 API；存在静默空态和“看上去有功能”的误导。属于当前固定组合的接线缺口，未运行浏览器重现。

**重要区别：** UI 将已准入者映射为 permissions:['*']，不能据此断言服务端越权。[当前后台准入](https://github.com/LordFoxFairy/kokoro-admin/blob/95c504d1bfdcf1038ebadb85d8493c18828b51f7/lib/server/product-admin-admission.ts#L40-L63) 仍校 Product 平台管理员资格；模型、Skills／MCP、积分等具名链已经有实现，不能说整个后台不可用。

**最小修复：** 由产品和 Task B 列出“本期支持／暂不支持”菜单；支持项接现有 BFF／owner 并真实回读，不支持项显式标明或经裁决退役。不要恢复万能 /api/resource 代理，不另建后台数据库／Session／权限中心。

**归属：** Task B B-13，涉及 B-09／B-11／B-12；见[原交接范围](https://github.com/LordFoxFairy/Kokoro/blob/32c56199a74e61bd757d6c69ee17efcd7904d16a/docs/handoffs/2026-10-30-task-b-capabilities-account.md#L24-L33)。不由本轮审计接管。

### R-04｜次批：IAM 原生认证入口缺应用级总预算与断开传递

[原生 handler](https://github.com/LordFoxFairy/kokoro-iam/blob/b6a9745b340149808afb1aae357574d0aa7bbad3/src/modules/auth/ingress/auth.handler.ts#L39-L102) 等待读取完整 body，再构造未关联 signal 的 Request 交给 Better Auth；[body reader](https://github.com/LordFoxFairy/kokoro-iam/blob/b6a9745b340149808afb1aae357574d0aa7bbad3/src/modules/auth/ingress/auth-body.reader.ts#L4-L15) 有 64KiB 限额，未配置读取总期限。现有 internal lifetime 不覆盖该原生入口。

客户端断开／BFF 超时，不等于 IAM 后继操作会终止。raw-body 会识别实际流中止，Node／反代也可能另有限制，因此本报告不称“完全无保护、无限等待”。

**最小修复／验收：** 原生入口复用适当读取／总预算并传递断开；不对所有 OAuth／邮件流程机械套同一短时限。仅补慢 body、断开和迟到完成回归；超时后的写入保持 unknown 语义，不假称回滚。

### R-05｜产品接线前置：Mori preview adapter 与当前认证边界脱节

[Mori adapter](https://github.com/LordFoxFairy/kokoro-mori/blob/12a1060830e1239c2ccb866baeefa4546ec04bb5/src/app/api/v1/mori/%5B...path%5D/route.ts#L21-L53) 不传当前准入要求的 Origin，仍发送旧 namespace／可选环境 principal；按 loopback hostname 自动注入 fixture 默认值，没有显式生产／preview 开关。

当前 BFF 音乐路由确实进入真实用户准入，缺 Origin 会被拒，旧 namespace／principal 不会自动成为权限来源。Mori README 也明确称 preview，故这是**正式接线缺口与 fixture 隔离债务，不是已证明的生产绕权**。

同文件 [55–70 行](https://github.com/LordFoxFairy/kokoro-mori/blob/12a1060830e1239c2ccb866baeefa4546ec04bb5/src/app/api/v1/mori/%5B...path%5D/route.ts#L55-L70) 全量缓冲请求体、fetch 未传 signal／总预算，另有资源边界缺口；上游 BFF 限额不解决 Mori 已接收的字节。

**最小修复：** Mori owner 单独接现有 Product 原生准入，fixture 显式隔离；补 body 上限、请求取消和普通／媒体流各自适合的期限。保留 Range、幂等键和原字节，避免短超时截断正常音频。不新建 Mori 身份服务。

### R-06｜次批：共享包仍有两套可编辑同名源码

[App 依赖](https://github.com/LordFoxFairy/kokoro-app/blob/b93acbd893fbc584643c3e72b9340943653e51e7/package.json#L77-L78) 指向本仓 workspace；[Mori 依赖](https://github.com/LordFoxFairy/kokoro-mori/blob/12a1060830e1239c2ccb866baeefa4546ec04bb5/package.json#L19-L27) 指向 web-shared。App 本身[约定第二产品接入后迁共享仓](https://github.com/LordFoxFairy/kokoro-app/blob/b93acbd893fbc584643c3e72b9340943653e51e7/packages/README.md#L76-L87)，当前尚未完整收敛。

本轮对 web-core／i18n 源码比对，**当前字节相同**；问题是未来改动存在两个 writer，不是已发现内容不一致。允许的本地 file bridge 本身也不是违规。

**最小修复：** 先确认唯一源码 owner 和包交付方式，再逐个切消费者、锁版本并验证公共入口，最后删副本；不建设通用“全栈共享层”。

### R-07｜次批：名为 contract:check 的命令会写生成物

[Capability scripts](https://github.com/LordFoxFairy/kokoro-capability/blob/24094960bad58d1b6a85a273d3bc94b0a0e0d1dc/package.json#L18-L20) 与 [Storage scripts](https://github.com/LordFoxFairy/kokoro-storage/blob/b60931e9e4e92d596b0678cbdabd9116e898b432/package.json#L19-L21) 都先调用 generate；normalizer 也明确写回文件。

**已证事实：** check 入口有写副作用。**待验证风险：** 它可能先修复待检查的漂移，使检查结论与输入状态不一致；本轮没有执行它或证明某次漂移已被掩盖，也不称生成器本身错误。

**最小修复：** generate 保留显式写入；check 在隔离输出生成并按字节比较，或等价地保证漂移必失败、不改输入。仅补“已漂移输入失败／干净输入通过／检查不写输入”的命令行为验证。Capability 先交其现 owner。

### R-08｜低成本先修：权威入口文档与现代码矛盾

- [BFF AGENTS 第35行](https://github.com/LordFoxFairy/kokoro-bff/blob/0895e254fc48a7ab62ede5d5433a7fc82eb6b722/AGENTS.md#L33-L36) 仍写 IAM 0.7／用户 Bearer。
- [IAM AGENTS](https://github.com/LordFoxFairy/kokoro-iam/blob/b6a9745b340149808afb1aae357574d0aa7bbad3/AGENTS.md#L15-L24) 仍有 Web／Auth.js 持 Product Session 的旧说明。
- [App README](https://github.com/LordFoxFairy/kokoro-app/blob/b93acbd893fbc584643c3e72b9340943653e51e7/README.md#L65-L74) 仍说 AI SDK 适配未实现，另有过时 pnpm／E2E 状态。
- [Billing AGENTS](https://github.com/LordFoxFairy/kokoro-billing/blob/b7c9858844df4c9b99e40e16bd9984b1d268b503/AGENTS.md#L7-L11) 仍将当前入口称作旧全局分层。
- [Root 组合表](https://github.com/LordFoxFairy/Kokoro/blob/32c56199a74e61bd757d6c69ee17efcd7904d16a/docs/REPOSITORY_STATUS.md#L5-L21) 漏 Admin，保留旧候选和 main-only 叙述；实际拓扑检查已识别 12 子仓。

**影响：** 人和 agent 按这些入口继续改，会重复设计已删除的认证、误报未交付、用错工具链。这是实际维护问题，非排版偏好。

**最小修复：** 只改现役首读页的当前事实，指向唯一技术总览／owner 契约；历史收据明确历史化，不批量重写证据。各仓 owner 维护自己的入口，内部工程资料不搬入公开产品／API 门户。

### R-09｜先校准工具：治理扫描结果不等于真实缺陷清单

本轮只读运行旧 ten-repository-standard：
- 输出 FAIL，414 条原始规则记录，0 项工具未核验。
- 它[实际配置仅 9 个子仓](https://github.com/LordFoxFairy/Kokoro/blob/32c56199a74e61bd757d6c69ee17efcd7904d16a/scripts/governance/ten_repository_standard.py#L99-L190)，未纳入 Mori、Admin、web-shared。
- [路径规则](https://github.com/LordFoxFairy/Kokoro/blob/32c56199a74e61bd757d6c69ee17efcd7904d16a/scripts/governance/contract_checks.py#L359-L394) 把 vendored Better Auth 原生路径和 browser-private 路径按普通业务 /v1 处理，不能直接据此改认证协议。
- Billing YAML 解析报“不支持某种 YAML 内容”，随后报“无 owner OpenAPI”，但仓内已有 canonical 文件；这是预检解析能力与诊断级联问题，不能据此说业务没有合同。
- 行数／兼容标记等词法命中还需查真实职责、生成状态和消费者。

**结论：414 不是 414 个安全漏洞，也不是下一轮 414 个必须逐条编码的任务。** 脚本原始 FAIL 如实保留；其中的有效工程欠账也不能全部当误报抹掉。

**最小修复：** 补真实覆盖清单、区分 owner／vendor／native 协议，用违规和合法样本校准；工具解释不了的输入报未核验而非推导业务缺失。不通过全量忽略列表刷绿，也不为数字归零机械重构。

### R-10｜可顺带：确认无消费者的旧 Admin 配置

[旧 env 模块](https://github.com/LordFoxFairy/kokoro-admin/blob/95c504d1bfdcf1038ebadb85d8493c18828b51f7/lib/env.ts#L3-L23) 还定义独立认证／数据库／邮件／旧网关配置。当前搜索仅其配套测试消费，生产走现 server/config 与 Product 准入。

这是旧方案残留，不代表当前后台真的又启动第二套登录或连业务库。实施前再核动态入口，随后连同只保护已废止需求的测试删除；不恢复这些旧配置。

### R-11｜可顺带：Mori 依赖声明需要小幅对齐

[Mori package](https://github.com/LordFoxFairy/kokoro-mori/blob/12a1060830e1239c2ccb866baeefa4546ec04bb5/package.json#L28-L38) 的 Node 类型仍是20代、运行要求22，且一个构建插件使用浮动 latest；lock 当前固定具体版本。

只固定已锁定兼容版本、对齐 Node 类型。**本轮未查依赖漏洞库，未发现／证明 CVE，不据版本号断言不安全。** TS target／额外 strict flags 差异作为后续兼容评估，不先强开导致全仓机械改造。

### R-12｜优先小修：BFF 持久回执重复驻留无界 Map

[mutationTicket](https://github.com/LordFoxFairy/kokoro-bff/blob/0895e254fc48a7ab62ede5d5433a7fc82eb6b722/src/application/idempotency.ts#L24-L37) 在提供 persistent repository 时只读 PostgreSQL；[commitReceipt](https://github.com/LordFoxFairy/kokoro-bff/blob/0895e254fc48a7ab62ede5d5433a7fc82eb6b722/src/application/idempotency.ts#L56-L64) 写持久回执成功后仍将完整响应 structuredClone 到 Map，没有容量／TTL。

这不是测试专用路径：[LibraryMiddleware](https://github.com/LordFoxFairy/kokoro-bff/blob/0895e254fc48a7ab62ede5d5433a7fc82eb6b722/src/modules/account/library.middleware.ts#L16-L24) 持有长期 Map，并与数据库回执同时传给现役上传链；[provider 装配](https://github.com/LordFoxFairy/kokoro-bff/blob/0895e254fc48a7ab62ede5d5433a7fc82eb6b722/src/modules/account/account.module.ts#L33-L36) 确实提供 PostgreSQL repository。

**影响：** 不同幂等键的已完成回执持续保留，持久分支又不读取这份副本，存在确定的冗余内存增长机制；未测实际增长曲线，不直接称已发生 OOM。

**最小修复／验收：** 持久提交成功后不再写进程副本；保留仍有用途的纯 Map 路径。仅补 persistent 成功不增长 Map、PG replay／冲突和纯 Map 正控，复用个人上传回归；不新建缓存层。实施前核 BFF Task B 当前分支是否已承接此逻辑。

## 5. 各仓应如何定性

| 范围 | 当前判断 | 后续边界 |
| --- | --- | --- |
| BFF | 普通内部认证方向正确；共享准入额度、冗余回执 Map、文档漂移需改进 | 不恢复 legacy dispatcher／内部 OAuth／通用代理 |
| IAM | 身份与生命周期有实际保障；限流、撤销上限、原生取消需定向修补 | 小范围修补，保撤权及审计，不先重写 OAuth |
| Admin | 真正突出的功能接线债务；部分旧页仍露出 | 交 Task B 按支持功能闭环，不擅删其在建 UI |
| Mori | 明示 preview，正式准入与资源边界未收敛 | 与产品主链分开实施，不冒已可正式使用 |
| App／web-shared | 已交付主链不重开；共享包双 writer、入口文档需统一 | 先统一 owner，再删副本 |
| Capability／Storage | 本轮明确发现生成检查写副作用 | 各 owner 修命令，不借机重命名／迁库 |
| System／Billing | 本次入口抽样未确认新的越权或跨 owner SQL 问题；有文档／配置基线债务 | 不把“未确认”写成全仓无问题，不顺带重做资金／模型系统 |
| Root | 实际组合可识别；旧组合表和治理预检需校准 | 文档／工具修正，不新建业务管理层 |

本轮未确认新的跨 owner SQL 事实；也未对所有查询、所有事务与所有 OAuth grant 作穷尽审查。后台管理验收、外部真实账号和已暂存事项继续按原 owner 范围，不作为重开 Task A 的理由。

## 6. 建议整改顺序与闭环条件

这是**待统一排期的候选队列，不是另一份活动 TODO 或对 Task B 的重新派工**；用户确认进入实施后，再串行写入唯一 todo。

| 批次 | 候选工作 | 最低充分闭环 |
| --- | --- | --- |
| 1：先降误导 | R-08／R-09 文档和扫描边界；R-10／R-11 小清理 | 来源与链接检查、治理合法／违规样本；无消费者证明；相关类型验证，不跑业务全链 |
| 2：先补实际风险 | R-01／R-02／R-04 IAM；R-12 BFF 小修，写区隔离、公共 guard 单 writer | 先复现共享桶／墓碑阈值；原生慢 body／断开；必要的 IAM 隔离集成；BFF 幂等与受影响消费回归 |
| 并行交接 | R-03 Admin 交 Task B，R-05 Mori 交产品 owner | 每个实际支持管理动作页面→API→owner→回读；Mori 正式登录、媒体取消／Range；不重复整仓验收 |
| 3：有收益再收敛 | R-06 共享包、R-07 只读 check | 消费者公共入口与固定版本检查；漂移必须失败且检查不写输入 |

实施纪律：
- 开始前核 Task B 当前源码／PR，已经修复的候选直接注销，不重复劳动。
- 不按本报告的问题编号拆一堆空层、计划、服务；一个完整行为切片对应其原 owner 的 PR。
- 改动不影响认证／数据时，不新增相应端到端套件；复用现有覆盖，只补独有风险。
- 删除旧代码之前查消费者和已废止需求；不为消除失败删仍有效的断言。
- 业务、契约、Schema 有变化才扩相应验证；全仓测试数量不作为闭环标准。
- 各仓独立 PR，子仓交付后 Root 固定精确组合；合入和分支清理按该次授权执行，不碰 Task B，不部署。

## 7. 审计阶段实际检查与未执行项（进入修复前）

| 项目 | 结果／口径 |
| --- | --- |
| Root／12 子仓 status、HEAD 与 gitlink | 调查开始全部 clean，精确配对；只有本报告为本轮新增文档 |
| 仓库计数 | .gitmodules／gitlink／manifest 交叉核对：12 子仓，其中10个 TypeScript 主实现 |
| repository-topology | 本轮 PASS；其 runtime_module_count=9 是业务组合口径，不是 Git 子仓总数 |
| contract-compatibility | 本轮 PASS：15 edges／0 violations；只说明固定消费证据兼容，不等于产品全功能通过 |
| ten-repository-standard | 本轮 FAIL：414 原始规则记录／0 unverified；含范围缺口与已核实的误报，不冒称通过 |
| PR 元数据 | 只读核对 Root #67、App #49、BFF #17、Capability #12／#13 仍 OPEN；不操作其分支／合并 |
| 官方资料 | 本轮查询 Better Auth Session／OAuth Provider 和 RFC9700，限定用于协议职责对照 |
| 业务测试／浏览器／真实 PG／Redis／流量测试／依赖漏洞扫描 | 本轮未运行；源码推导、历史证据与实际运行结果分开记录 |
| 文件与链接检查 | 37 个固定源码链接的 Git 对象／文件及行范围核对 PASS；本报告 whitespace／diff 检查 PASS；只读报告复核无必须修改项；不重跑已交付 Task A 全量 |

**下一步决策只需明确先做哪一批，以及与 Task B 的写权交接；不需要再次设计一整套认证架构。**

## 8. 后续执行（2026-11-11）

用户已要求进一步修复，不再停留在审计；本节复用上述结论作为本轮范围，状态仅在Root唯一TODO更新。

| 负责人／写区 | 本轮目标 | 验收与排除 |
| --- | --- | --- |
| BFF writer：现幂等实现、现个人上传测试 | 修R-12，持久回执不再写无消费者Map副本 | 上传真实接线先RED后GREEN，保PG回放／冲突及纯Map；不改Task B重叠的原幂等测试／package／契约 |
| Admin writer：旧env及其专属测试、无调用包装 | 清R-10 | 全消费者搜索与相关原生准入／页面生命周期／类型构建；不改现server/config、后台菜单或业务接线 |
| 主控：BFF AGENTS、Root组合入口／报告／TODO | 修确定的旧规则误导 | 当前Session／内部服务身份／第三方OAuth区别清楚，链接与文档检查；不改业务认证协议 |
| 认证审计负责人：只读跨owner实际caller与本地日志 | 核是否有可达内部机器换票残留 | 分类为普通内部／第三方／业务权限／死代码；日志仅脱敏错误码与源码时间，历史不冒当前 |

Git基线：Root从fetch后main32c56199，BFF从main887633c、Admin从mainb6e37fa建立本轮codex/auth-maintenance-cleanup分支；两个子仓main树分别与审计源提交相同。完整分页确认BFF上述源码与上传测试未被Task B PR17改动；不据前100文件推断无冲突。

本轮不改Schema／公开API／认证机制，不引入服务、缓存、SDK或新的Repository层。IAM限流／批量撤销与后台功能是独立行为切片，先核对Task B当前实现和写权；本轮可独立清理继续推进，不把局部冲突扩大为全局停工。后继交付仅报告实际完成范围，不把这批删除说成12项全部修复。

本批实施结果：BFF R-12与AGENTS纠偏已提交 `00a9ebeea3f82b10c7edd1729770209e3b666111`，经[PR #20](https://github.com/LordFoxFairy/kokoro-bff/pull/20)合main；Admin R-10已提交 `9bed3d2af168a7cf8d55de4fac6a7c9369394e10`，经[PR #6](https://github.com/LordFoxFairy/kokoro-admin/pull/6)合main。主控分别复验定向14／64例、lint／类型／build，另直接验证纯Map commit／快照／回放／冲突；两个独立只读审查CLEAR。HTTP／Connect使用协议夹具，未称真实PG／Storage集成，也未重跑无关全产品套件。Root固定这两个精确源码提交、按290项引用读取232个实际Git blobs；拓扑、15条契约边／0违例及原checkpoint通过。未改其它owner pins，剩余候选未伪装完成。

## 9. 深入核验：哪些OAuth保留，哪些旧表面待删

只读追踪当前非generated生产代码的实际caller，未发现BFF、Billing、Capability、System、Storage或Agent主动以client_credentials向IAM换机器票据。此结论限定于已查调用链，不推断当前进程已启动这些提交。

| 实际链路 | 读取证据 | 结论 |
| --- | --- | --- |
| BFF→IAM普通业务 | 上述InternalAuthGuard的bff_user_context分支 | 服务凭据＋可信actor，不是用户OAuth透传 |
| BFF／Agent→Capability | [本地Ingress授权](https://github.com/LordFoxFairy/kokoro-capability/blob/24094960bad58d1b6a85a273d3bc94b0a0e0d1dc/src/infrastructure/auth/platform-ingress-authorizer.ts#L28-L44) | bearerCredential经本地校验，明确service_credential；Bearer名称不代表OAuth |
| BFF／Agent→System | [AccessGuard](https://github.com/LordFoxFairy/kokoro-system/blob/49a5f8e5e2797ec2d1a6fcf8c5f398184821bf33/src/access/access.guard.ts#L73-L95) | 按service校专用secret |
| caller→Storage | [WorkloadVerifier](https://github.com/LordFoxFairy/kokoro-storage/blob/b60931e9e4e92d596b0678cbdabd9116e898b432/src/common/auth/workload-verifier.service.ts#L24-L45) | 直接服务凭据与用途校验 |
| BFF→Billing | [PersonalAuth的机器分支](https://github.com/LordFoxFairy/kokoro-billing/blob/b7c9858844df4c9b99e40e16bd9984b1d268b503/src/infrastructure/auth/billing-auth.ts#L249-L282) | 直接service token／internal secret，不先换票 |
| Capability→IAM执行授权 | [Execution verifier](https://github.com/LordFoxFairy/kokoro-capability/blob/24094960bad58d1b6a85a273d3bc94b0a0e0d1dc/src/infrastructure/iam/execution-authorization-verifier.ts#L77-L112) | 服务凭据＋execution proof＋当前业务权限，保留 |
| Billing→IAM资金授权 | [Billing authorization client](https://github.com/LordFoxFairy/kokoro-billing/blob/b7c9858844df4c9b99e40e16bd9984b1d268b503/src/modules/metering/iam-billing-authorization.client.ts#L85-L118) | 核payer／Run／lease／digest的业务授权，保留 |
| IAM对外部用户token内省 | [进程内introspection](https://github.com/LordFoxFairy/kokoro-iam/blob/b6a9745b340149808afb1aae357574d0aa7bbad3/src/modules/auth/internal-access/token-introspection.service.ts#L30-L48) | 资源服务器直接凭据认证，不先mint机器token；有真实消费者，保留在线失效检查 |

另外必须保留：IAM对外OAuth/OIDC发行、第三方MCP Code／PKCE／refresh、User API Key／OpenApp、Billing当前独立用户Bearer模式。它们各有生产caller，不能借“内部不走OAuth”整删。

**新增后继删除候选（不伪称已修）：**
- BFF旧Admin允许表仍列jwks／token／userinfo／revoke，但当前relay五条原生交互先拒这些旧路径；是不可达的过时表面，非活内部换票。该policy文件与Task B PR17重叠，留给对应writer，不在本轮抢写。
- Billing旧createBillingAuth总factory仅被其单测消费，生产已改具名Personal／Catalog factories；由Billing owner核验后删除旧factory及专属测试，保留同文件现役用户JWT分支。不据此整删JWKS verifier。
- 显式拒绝退役OAuth配置的代码属于防误配置约束，不是兼容fallback，不因出现旧名字就删除。

**日志口径：** ignored日志目录按mtime最近的8份尾部只提取时间／错误码／显式source SHA；最新记录止于2026-10-20，存在历史EADDRINUSE但无可绑定本轮的source SHA。本轮不将其当当前OAuth故障或当前进程存活证据，也不据此重启他人服务。当前直接取得的失败证据是R-12真实上传回归和Admin旧生成类型缺失；两者分别通过最小源码修补、归档旧缓存并正规生成解决，详细结果写入TODO。

## 10. IAM后继修复设计门（2026-11-11）

用户已同意继续修复。基线Root main95736aec、IAM main86f2ed7（与原已验b6a9745b代码树相同），本轮分支codex/iam-maintenance。IAM当前无open PR；已有独立Task B功能和PR不操作。一个IAM writer独占源码／测试／owner说明；主控管理唯一TODO、资源、Git和最终验收，两名reviewer仅只读。

### R-01：普通业务限流的最小纠偏

只修改已完成bff_user_context服务认证、actor／tenant校验后的普通owner分支：以caller、credential、可信tenant、actor、operation的无歧义元组为桶，100次／60秒不变。**该分支原所有用户共用的凭据总桶不再保留，多个actor的合计准入量会提高**；不凭空另设N倍全局额度、缓存或配置系统。资金／执行机器分支、OAuth／APIKey、账户生命周期、原生入口既有保护不变。

本轮进一步核到官方get-session仍按受信源IP＋路径执行框架默认100/60；BFF的汇聚连接可能共享该桶。因此本片只能证明普通业务公平额度隔离，不能称整条登录入口再无跨用户共享阈值。原生边缘总量策略另按真实拓扑与容量处理，不能关掉全部原生限流或随意调高数字来刷绿。

验证只补可信actor A耗尽后B仍可用、同actor保持限流、非法服务／重复actor不消耗、Redis故障失败关闭；复用已有真实原子计数证据，不引入新表或网络协议。

### R-02：批量撤销按页，不按任意总行数拒绝

保留原官方adapter与原where，仅Session删除支路改为同一个既有事务内的keyset分页：id升序、每页最多500、原谓词与游标显式AND；每页先按同序集合锁，再按原谓词＋本页ID鲜读复核。不能用offset，也不能按页独立commit。处理全部匹配行，包括已结束墓碑的Access／Refresh子凭据及rotation replay清除；仅把较晚有效期批量降到冻结cutoff，不延长旧墓碑。

删除的保护是任意500总目标上限及成百上千次逐行SQL，不是事务、当前谓词、子凭据撤销或失败回滚。所有页仍共用原5秒事务预算；过大批次／争用超时明确失败并回滚，不把超时当成功。update／rotation的原500保护和CAS本轮不改。无Schema／API字段／新state owner。

最低真实验收：500墓碑＋1有效且墓碑仍有未撤子token、501有效、OR谓词不扩大目标、第二页失败全回滚；复用既有撤销／rotation竞争回归。仅使用本轮隔离PG数据库／Redis前缀，不触已有数据。

### R-04：传输有界与副作用取消必须分开

当前Better Auth／Prisma handler不保证合作取消；仅加signal或Promise.race不代表数据库／邮件停止。原生入口须保持原字节、官方协议错误／Cookie／redirect／429和已派发结果unknown语义，不套internal envelope，不自动重试。

已确认Node适配器setResponse返回不代表流EOF，清理应绑定response finish／close／error。读取阶段必须实际停止未完成输入，且超时／断开不再启动handler；派发后的晚Response不能写Cookie或redirect，未消费body应取消，晚拒绝必须被观察。预算及具体实现由本轮主控与writer收敛后开写，不直接复用硬编码5秒的authorization业务lifetime，不建设另一套认证框架。

本轮已收敛的HTTP预算：读取5秒、总响应30秒，读取成功立即退役读取timer；总timer保留到真正finish／close。邮件既有连接5秒／问候5秒／socket10秒留在此窗口内，总HTTP期限小于默认45秒shutdown。它们是入口资源策略，不是性能SLO或数据库硬取消保证。超时未发headers时返回no-store原生503空body并关闭连接；已发headers时只断开。受信mount参数允许现有HTTP测试注入短预算，不新增环境变量／业务字段；所有迟到错误与Response取消失败仍被观察，不重复响应。不建立新的全局pending registry，非合作的下游操作与容量问题按真实边界保留。

### 精确交付：区分服务运行提交与不变SDK发行来源

Root现归档校验将Capability消费的独立已验SDK构建source.commit硬绑当前IAM runtime gitlink。私有服务修复即便SDK／机器契约完全不变，也会要求重打包并改Task B消费者；这是需修的组合校验耦合，不通过改造消费者或伪写provenance绕过。

本轮Root治理writer仅修该局部校验及现有真实Git fixture回归：runtime owner／evidence仍逐字匹配Root gitlink；SDK继续使用既有侧车的已独立验发行source（必须规范SHA、在原发行allowlist且是runtime提交祖先），原tgz摘要、SRI／lock、干净来源、内嵌侧车相等与版本检查全保留。新增证明发行与runtime的整个sdk Git子树、canonical合同原字节一致；已记录generator／lock／runtime参数仍严格比对。任一SDK源／合同漂移、未知发行、重打包JS或不相容lock必须失败。不新增allowlist条目、不改Capability／Task B、不只凭版本号判兼容。该薄片先用私有代码提交推进但SDK不变的合法组合复现RED，再验合法／违规样本，主控最终复验。

## 11. 远程PR收尾复核（2026-11-11）

用户指出远程PR仍多后，主控逐13仓读取OPEN并非递归fetch精确main／head／base，共8个OPEN，全部仍为Draft。**此前“本轮已收尾”只覆盖当轮自有PR，不应被理解为整个组合的所有子仓均已合main。当前确有Task A自己的未收口项，也有Root正在使用的未合候选。**

| PR | 当前head／base | 已确认归属与处置 |
| --- | --- | --- |
| [Root #67](https://github.com/LordFoxFairy/Kokoro/pull/67) | 477562a4／main | Task B组合；保留其负责人，非本轮可擅自close |
| [App #49](https://github.com/LordFoxFairy/kokoro-app/pull/49) | d6dd3cd0／main | Task B连接器／Skills／账户功能，保留 |
| [BFF #17](https://github.com/LordFoxFairy/kokoro-bff/pull/17) | 1e6765b3／main | Task B业务与合同，保留 |
| [Storage #2](https://github.com/LordFoxFairy/kokoro-storage/pull/2) | add2da6c／main | Root #67明确配对的Task B图标Schema独立修复；patch未等价进main，保留 |
| [Capability #12](https://github.com/LordFoxFairy/kokoro-capability/pull/12) | 2ad5c9e7／main | Skills／MCP上游候选，#13依赖它；按其owner验收交付 |
| [Capability #13](https://github.com/LordFoxFairy/kokoro-capability/pull/13) | 24094960／#12分支 | **我们的Task A实质遗留**；当前Root正固定它，未合main，不能归给Task B |
| [System #2](https://github.com/LordFoxFairy/kokoro-system/pull/2) | 49a5f8e5／main | 盘点时未合；现已正常merge `0a4e7932`，精确Root pin保持且main可达，原候选远程分支已清理 |
| [Billing #4](https://github.com/LordFoxFairy/kokoro-billing/pull/4) | b7c98588／main | 盘点时未合；现已正常merge `43a60920`，精确Root pin保持且main可达，原候选远程分支已清理 |

8个head均未成为各自main祖先；Storage #2与Capability #13另做patch等价核验，均未被main等价承接。因此本次未找到可为了减少数量而直接close的已完成空PR。远端mergeable／UNSTABLE不等于完整本地验收结论，也不自动构成必须等待CI的理由；不绕强制保护。

### 我们的#13依赖复核与最终收口

#13已通过merge提交1b5116c包含收口前#12 head2ad5c9e7；原PR描述“最新base尚未集成”已过时，本次已修正。初次将**上游#12仍未入main**判断为#13必须等待的前置条件，后来复核确认该判断过度约束，以下保留差分事实并更正出口。合并前#13相对#12有11个独有提交（10个非merge），87文件／1796增1478删；独有非merge patch均未等价进入main。相对main则包含37提交、398文件；现在直接retarget会把#12约378文件一并带入，既不独立，也违反不接管Task B的边界。

正确出口有两种：按原base完成叠层交付，或等待#12由其owner交付main后再处理剩余差分。前者不要求先合Task B到main，但会推进其接收分支，须明确边界。用户已选择前者：只将我们的#13按原目标合入，不合Task B到main。没有直接close、强行retarget或独立重写。

用户提出PR问题时，在手IAM13文件与Root治理2文件已停写、未提交，主控先完成上述历史候选的收尾。随后只验收原在手候选：首次默认检查发现一条绑定Math.min源码字面的过时oracle；保留AST唯一writer及unit／真实PG单调到期保障，退役该字面断言后完成验收，未继续扩展新功能。执行状态只维护唯一TODO。

### 已实际收口的两个独立owner PR

System #2与Billing #4此前保留Draft的直接原因，是2026-10-27对齐时的“不请求自动合并”旧检查点，不是已证明技术上不可合。按用户后续逐仓PR交付授权及本次收尾要求，主控重核远端main／head、独立owner范围与当前输入，修正PR说明、转ready并以精确head经正常merge API合入；未admin／force／绕保护，未部署或改运行配置。两个main合并树与Root原已验源码树完全相等。

复用证据而非重复测试：System196个交付输入逐项与49a5f8e Git blobs全等，历史定向／owner／fresh schema收据仍精确绑定，当前独立代码复核CLEAR；Billing419个基线＋7个最终输入共426个逐项与b7c98588全等，历史default1864 PASS／630 SKIP、真实PG44、零残留与源码独审绑定核实，主控另复核最终两文档。此处没有将历史结果写作本轮重跑。远端失败check的job均0个step，annotations明确账户账单导致未启动；CI未通过，不以UNSTABLE冒称技术保护阻塞，也不绕强制规则。

上述两个owner收口时剩6个OPEN：Root67／App49／BFF17／Storage2／Capability12与我们的Capability13。这是中间快照；后续#13实际合并见下，剩5个属于Task B或其显式配对依赖，不由我们操作。

### 在手IAM候选亦已验收交付

IAM14路径最终源码 `cee88df4770ce52d42798a9ed2cb66b3b6262c5d` 经[原PR #7](https://github.com/LordFoxFairy/kokoro-iam/pull/7)正常合main（merge9f260bb6）。主控完成格式、lint、类型、合同生成／固定baseline breaking、SDK检查；默认初次1630通过／1条旧源码oracle失败，移除该实现耦合而保留架构／行为保护后最终1631通过、build通过。真实隔离PG／Redis3文件24通过，PG库存102→102；不将官方auth.api＋真实PG写作浏览器整链。完整停写输入和独审已绑定，未改Schema／wire／依赖或SDK源。

Root治理153项及Ruff主控复验通过；新实际IAM pin对应的4条来源引用按3个真实Git blobs核实，当前拓扑、15条契约边／0违例及原checkpoint通过。既有SDK的独立发行锚仍为原b6a9745b／0.21，不重打包或改Task B；新增校验证明其SDK整树和合同与当前runtime相同。原生源IP容量、已派发的非合作副作用unknown及极大撤销集合5秒事务边界仍明示，不称全部问题解决。Root最终集成与自有分支清理随本次PR和主控回执确认。

### 用户确认后的Capability #13最终回执

2026-11-11T09:45:59Z，主控将我们自己的[#13](https://github.com/LordFoxFairy/kokoro-capability/pull/13)转ready，以精确head `24094960bad58d1b6a85a273d3bc94b0a0e0d1dc` 通过正常merge合入原base `codex/connector-icon-staging`，merge为 `e068fcaaeb0c40e1119ce88760f568a94bf0859c`。用户明确授权该接收分支前进；没有操作#12的ready／合并／描述／清理，#12仍OPEN／Draft，Capability main仍为adbcc78a。没有force／admin／绕保护、没有部署。

主控fetch后核验：源24094960为接收分支祖先，merge树与源树完全相等，Root仍固定该已验源；自有远程分支删除前tip精确匹配24094960，删除后prune，本地无该同名分支。保留其他owner的分支和工作树。此为叠层交付完成，不是Capability main交付完成；后者归#12原owner。

补验严格限定缺口：当前源SDK checker／typecheck及8文件129项定向通过；另补本地HTTP peer 5项通过，明确不是实际IAM。私有精确源归档1118个tracked文件逐项与Git blobs全等，正式build／八owner真实PG同库schema和Redis readiness通过；仅证明装配，不扩大为完整产品mutation／当前全owner门。历史完整3051／678 SKIP不冒称当前重跑。合并无新源码，不重复全产品旅程。

至此我们的历史PR已收口；剩余Root #67、App #49、BFF #17、Storage #2、Capability #12均保留原owner。Root #72亦已正常合main（66da9997）并清理本轮分支，本次只通过独立Root文档PR更正TODO／当前事实／技术总览和本报告，不改gitlink或业务代码。


## 12. 十轮定向维护审查

日期：2026-11-11（America/New_York）。

### 策略与完成口径

用户要求继续梳理并启动十轮扫描。本轮把“十轮”定义为十个不同风险面，三名只读代理并行检查第1～9轮，主控完成第10轮、交叉复核和去重；不是把全仓测试或同一关键词搜索重复十遍。每轮检查代表性入口与实际消费者，**不是全源码逐行审计，也不证明没有其他缺陷**。

冻结基线为Root `7274322c0775f386c5f7784365bfbc95bd3ee804`，12个子仓均干净且与其gitlink精确匹配。已修R-01／R-02／R-04／R-10／R-12不重新报新增；旧问题的剩余范围仍按原记录区分。

只读获取Task B五个PR的完整文件清单：Root #67（11路径）、App #49（287）、BFF #17（598）、Capability #12（398）、Storage #2（4）。这是写区碰撞提示，不代表这些文件的当前代码已被Task B修复；未改其PR、分支或工作树。Scheduler继续不展开重构审查。未启动业务服务、浏览器或外部供应商连接，未安装依赖、重跑全套或删除测试；本次交付仅更新Root报告、当前入口和唯一TODO。

### 十轮结果

| 轮次／负责人 | 代表性检查入口 | 结论 |
| --- | --- | --- |
| 1／认证代理 | IAM原生handler/lifetime、BFF Session准入、InternalAuthGuard、AccountSessionGuard／撤销adapter | 抽样无新增；直接服务身份与可信actor、原生会话管理具名例外均保留。已修项不重报，源IP共享额度等已知边界未消失 |
| 2／认证代理 | BFF ProjectsModule→mutation middleware→PG mutation store／receipt repository；ScheduledTask命令lineage | 新增R-13：项目业务与完成回执分开提交 |
| 3／认证代理 | Admin console准入、具名adapter、NAV／旧页面与route inventory | 原R-03后台接线债务仍在，不新增；有效模型／Skills／MCP／积分adapter保留，不能说整个后台失效 |
| 4／后端代理 | System模块／维护服务，Billing Nest图与三个worker脚本 | 无新增；Billing旧pg services有真实脚本消费者，不能整树删。Billing入口文档漂移归R-08 |
| 5／后端代理 | Storage RPC／身份与purpose；Capability package／icon client与装配 | 无新增；不同资源purpose和服务身份有独有权限价值。生成检查副作用归R-07，不重复计数 |
| 6／后端代理 | System／Billing关闭路径、Storage lifecycle、Capability registry／HTTP/SSE／OAuth client | 新增R-14；其余活动集合有settle／finally清理，不凭Map存在判泄漏 |
| 7／Web-Agent代理 | AgUiChatTransport→readUIMessageStream→machine、draft、final reference、Agent scoped replay | 抽样无新增；实际使用锁定AI SDK，不建第二网络协议，不重开已交付Task A能力；未重跑浏览器／Worker旅程 |
| 8／Web-Agent代理 | App scripts／Vitest发现配置，composer／CSS质量门，历史contract parent与Agent字符串断言 | 新增R-15；只保留窄去重建议，不把实现耦合测试全部判无用 |
| 9／Web-Agent代理 | Mori／shared／App packages消费者、README与manifest | 原R-05／R-06／R-08／R-11再确认，无新增编号；双份源码当前相同不等于没有双writer债务，也不是已发生漂移 |
| 10／主控 | 三份结论交叉复核、真实调用与写区核对、Root组合／main-only治理入口、最小失败探针 | 新增R-16；合并重复命中，保留正常保障；共四个新增确认机制，不是四起已发生事故 |

### R-13｜优先修：项目业务成功与幂等完成回执不原子

**当前证据（BFF `00a9ebee`）：** `src/modules/projects/project-mutation.middleware.ts:83–106` claim后调用正式业务；`src/http/routes/project-mutation-native.ts:46–47,54–62`先create／instruction后reply。`src/infrastructure/postgres/project-store.ts:119–124`为单条自动提交，`:149–160`在新增revision后显式COMMIT。之后`src/http/response.ts:28–33`才写完成回执；`src/application/idempotency.ts:56–61`失败会尝试release pending，返回503。`src/infrastructure/postgres/idempotency-repository.ts:23–38,41–53,84–89`的claim／完成／释放均为独立操作，未完成pending还可在60秒后重取。

**触发／影响：** 业务成功但完成回执失败且release成功，或进程在两次提交间退出。原key可能重做已完成指令；create可能从原成功变成slug409，instruction会多写revision，中间有新指令时旧key重试可覆盖新值。tenant／owner、唯一约束、fingerprint和完成回执CAS仍存在；它们不消除此提交窗口。

**主控最小探针：** 调用现真实route/helper，以内存business／receipt doubles注入一次完成回执失败，依次发原key旧指令、新key新指令、原key重试，实得状态`503 → 200 → 200`、业务调用3次、最终恢复旧指令。仅证明当前调用／恢复分支，**不称真实PG集成或生产事故**；实际SQL提交边界另由上述源码确认。

**最小修复：** 优先仅收敛Project mutation的同owner提交边界，让业务与完成回执在同一PG事务落地，或以已有可恢复命令事实承接；保留claim、fingerprint、当前权限、slug与错误语义。单独保留pending只会延后重做窗口。不建新服务／全局框架，也不借此重写所有通用幂等消费者。实施前在现owner技术设计记清事务与恢复边界。

**最低验收：** 隔离PG在回执写入点注入失败，确认业务与回执整事务无部分提交；若首笔已回滚，重试可首次成功创建项目／revision，不强求未提交的原ID。另对已成功提交，或提交ACK未知但结果已持久化的场景，同key只回放原project／结果，不新增revision、不覆盖后续新指令。复用现定向接线，不新增全产品门。

**归属／碰撞：** BFF主改、主控验收；上述项目／receipt文件不在#17文件清单。`src/http/request.ts`有重叠但不需改。不等同已修R-12的Map驻留问题。

### R-14｜交原owner：MCP OAuth DNS pin跨独立授权长期驻留

**当前证据（Capability `24094960`）：** `src/modules/mcp/mcp.module.ts:338–368`只创建一次HTTP client并给单例OAuth port使用；`src/infrastructure/clients/mcp/mcp-oauth-http-client.ts:54,182–191`以origin永久保存首次完整地址集合，以后集合变化即拒绝。`src/infrastructure/clients/mcp/standard-product-oauth.ts:30–32,46–49,141–166,181–198`的discovery／begin／complete／refresh共用它；普通个人授权RPC及refresh服务为真实消费者。

**触发／影响：** 首次解析后AS／CDN合法公网地址轮换或增减，后续独立授权、refresh因旧集合被拒，直到原DNS集合恢复或client重建。没有外部AS实测或线上发生证据。主控仅用注入DNS的白盒pin探针确认：同实例拒合法公网A→B，新实例接受B；没有网络连接。

**最小修复／验收：** 明确pin绑定的一次授权操作／有界上下文；新授权和独立refresh可重新建立通过公网检查的绑定。同一上下文变更、私网、取消仍拒，实际连接IP、Host／SNI和预算保留。不直接删除SSRF保护、不引入通用缓存层。现有HTTP client用例承接这些差异即可，无需全产品E2E。

**归属／碰撞：** Capability原owner；缺陷文件本身不在#12清单，但composition与OAuth调用链重叠，故只列交接，不由本轮修改Task B写区。不重复原R项。

### R-15｜交原owner：Web聚合门重复执行同批测试

**当前证据（App `b93acbd8`）：** `package.json:19`的contract在generator checks后运行contract Vitest；`:26`单跑architecture；`:31`默认test不带过滤；`:33`的check顺次调用三者。`vitest.config.ts:11–18`没有排除前两组，锁定Vitest本地默认发现模式也包含它们，因此执行一次`pnpm check`会再执行同一批contract／architecture测试。

**影响与最小修复：** 确认重复工作，未测总耗时，不用测试数量推导收益。聚合门保留所有generator drift检查，让Vitest一次覆盖原文件集即可；独立focused入口继续保留。不删断言、不缩glob、不增加套件。最低验收是发现文件集与generator清单不减少，再跑调整后的一次聚合门。

**归属／碰撞：** App原owner，package.json在#49写区，本轮只交接。不等同R-07“检查会写生成物”。composer forced-colors重复子断言仅作低优先窄去重建议；其普通焦点、系统色和forced-color-adjust保护仍有独有价值。landing文件数／行数门及历史parent helper尚未完成风险承接证明，不整组删除。

### R-16｜低成本先纠偏：一次性main-only工具被当成通用组合门

**当前证据（Root `7274322c`）：** `scripts/verify-main-only.py:55–60`要求每个子仓当前分支为main，且所有远端只能有main。`README.md:34`和`docs/REPOSITORY_STATUS.md:42`仍把它列为复现入口。正常submodule checkout可以detached在精确gitlink；其他人的正常topic分支也不应构成我们清理失败或删除理由。

**主控最小探针：** 向原main函数注入干净detached＋仅一个main本地分支＋正常他人远端topic的合法fixture，原工具返回FAIL，分别报“checked out branch is not main”和“origin branches…expected only main”。这是合成语义反例，不是本轮执行全仓远端扫描；实际Capability当前也以合法精确pin detached。拓扑检查已承接组合身份，不通过换错gitlink或删他人分支刷绿。

**最小修复／验收：** 从现役通用清理／复现入口退役该一次性“全远端只留main”要求，复用精确拓扑与自有分支收尾回执；如保留专用工具须明确限定自有范围。不要再建万能扫描框架。保留旧ADR历史验收事实，不改写过去PASS。定向合法／违规fixture和相关链接检查足够，不重跑产品旅程。

**归属／碰撞：** Root主控；脚本与当前README／组合入口不在Root #67写区。本项是原R-09治理误报的新增具体反例，不重复计算旧414条原始记录。

### 后续推进顺序与停止条件

1. 先处理非重叠的R-13正确性问题及R-16工具误导；每项只围绕上述最小写区和独有风险，不扩成全仓重写。
2. R-14／R-15列明证据交原owner，未拿到独立写权不改Task B；其余既有维护债务不假装已完成，也不重复立项。
3. 本轮十个风险面已有可追溯结论，停止继续机械扫描。后续修复只回归受影响风险；新证据改变判断时更新原条目，不再启动重复十轮。

状态仅维护[唯一TODO](../../todo.md)；本次扫描完成不等于上述修复完成，也不重开已交付Task A。未改业务源码／gitlink／Schema／依赖、未部署、未操作他人PR。


## 13. R-13／R-16最小修复执行（2026-11-11）

用户确认只闭环R-13、R-16，沿自己的PR合main并清理，Task B不动。基线Root0643c551、BFF main c358e403（树与原pin00a9ebee相同）。BFF唯一writer负责Project局部实现和独占PG回归；主控负责Root、资源、验收和Git；另两名只读代理分别复核事务与退役范围。

R-13采用现BFF owner内本地PG事务，不增Schema／token／第二套receipt adapter：外层保留claim及pending语义，业务事务先锁并重读receipt，匹配pending才执行业务与完成回执；已完成同fingerprint只回放，异fingerprint冲突，缺行不得补造成功。锁覆盖业务，60秒接管无法越过；失败整事务回滚，COMMIT ACK未知不删除持久终态，不盲重做。成功仅在提交后发送，现准入／owner／slug／错误语义不退化。项目store与现receipt repository复用同client，不复制通用claim SQL或重写其他消费者。

R-16删除一次性main-only脚本及当前复现命令，改正ADR现行分支说明但保留历史PASS。现有拓扑入口承接精确pin身份，定向合法／错pin反例保护该边界，不新建通用扫描器。历史CODEBASE_MAP／旧计划中的原始记录不批量改写。

写区已对照Task B最新完整文件清单：BFF旧business-store集成、通用idempotency测试、owner技术设计等重叠文件不写；新项目PG回归使用独占临时库，沿现Project fixture组织，不新建共享服务。Root此报告记录已批准的局部事务决定，不另造重复技术方案。R-14／R-15继续原owner交接，未授权扩入本轮。

上述为实施前裁决；实际停写验收与交付结果如下。


### 停写验收与交付回执

- **R-13交付：** BFF精确源码`a3e190623183d56f95960d8b6feb89a84fda1ece`经自有[PR #21](https://github.com/LordFoxFairy/kokoro-bff/pull/21)正常merge main（58222407a64c66b57069f05ae618050d58a7b063）；合并树与已验源全等。自有本地／远程分支已删，checkout回到Root精确源。生产只改Project store、native handler和receipt repository的queryable构造类型；Schema、wire、依赖及通用receipt行为不变。
- **真实RED保留：** 首轮独占PG触发器令完成receipt失败，create后仍残留1个project、instruction仍为older，正确复现缺陷而非测试装配失败。修复后主控独立真实PG回归9通过／0失败／0跳过，覆盖业务／revision回滚、同key原结果、HTTP成功响应丢失、真实COMMIT已执行后注入确认异常、同／异fingerprint过期claim及行锁阻挡reclaim。fixture只起测试HTTP、复用正式provider factory／middleware；IAM准入为明确替身，非完整Nest或真实IAM浏览器链。
- **主控相关门：** build、lint、typecheck及五文件格式通过；现有idempotency、native admission、Nest feature、user admission和BFF五文件78通过／0失败／0跳过。未重复全默认或完整产品旅程，不冒称其它历史门已全绿。独立事务与最终fixture审查CLEAR。
- **新增失败与修正：** 主控首次扩大focused为77通过／1失败：旧revoked-session fixture只mock create且禁止PG，与新事务边界未接线。没有生产回退、删断言或缩小用例；仅在该case局部mock原有withReceipt并沿同receipt对象保存，最终78通过。该文件与Task B名单重叠，但主控核过其实际三个diff区只涉credential／Share／末尾Admin，该case及helper不在其中；本轮所有原断言／helper和Task B实际改动均未改。BFF #17仍OPEN／Draft、head保持1e6765b3。
- **资源：** 本轮所有PG临时库由fixture独立创建／注销；主控数据库库存102→102，本轮前缀库剩余0，未重置共享PG／Redis、未启动产品服务。真实集成重跑命令为`KOKORO_TEST_POSTGRES_ADMIN_URL=... node --import tsx --test --test-concurrency=1 test/project-mutation-receipt.integration.mjs`（在BFF运行，先正规build）；不修改Task B重叠的package入口。
- **R-16验收：** 删除旧脚本、四处当前入口／政策说明已纠正，历史ADR §4.1验收事实保留；其中两条既存失效CURRENT锚点已核原Git内容并固定到4addb02c历史快照，不把过去PASS移作当前证明。旧checker合法fixture RED被保留为失败证据；现拓扑8项及Ruff通过。新增两项用真实本地Git＋bare origin证明detached与他人topic合法，错SHA仍FAIL，不访问远端或删除他人分支。独立退役审查CLEAR。
- **Root组合：** 290项BFF来源引用按232个真实提交blob重算，不机械替换摘要；当前拓扑PASS、15条契约边／0违例、原checkpoint PASS。Root本次自有PR承载R-16、精确gitlink、inventory和台账，不接管Task B；最终合main／分支清理随对应Git回执确认。

只闭环R-13／R-16。R-14／R-15及既有其它维护项未借本轮勾掉；未部署，未将未运行CI记通过。


## 14. 剩余问题盘点与最小维护批次

日期：2026-11-11（America/New_York）。起点Root `f0efcb879b35ae852261372692cd743158b7758b`，不重复十轮扫描。对既有R-01～R-16按已提交事实去重：已闭环R-01／R-02／R-04／R-10／R-12／R-13／R-16共7项；仍有遗留R-03／R-05／R-06／R-07／R-08／R-09／R-11／R-14／R-15共9项，其中R-08已部分完成。这是维护问题范围，不是九起已发生事故。

此外，§9的BFF旧Admin允许表、Billing旧总factory是两条旧代码清理候选，不再包装成新增编号；容量策略、非合作副作用语义及用户暂存外部验收分别保留，不混算故障数。唯一执行状态已整理为[当前TODO](../../todo.md)，旧重复完成记录由Git历史和本报告承接，不再占据当前队列。

本轮只处理三片：R-08的App／Billing文档余项；无生产caller的Billing总factory及只保护退役模式的分支／类型；R-11的Mori工具依赖分片。Billing生产Personal／Catalog及真实JWT/JWKS、operator保障不变；有效旧测试迁现役入口或复用已有保护，不以减少数量为目标。Mori仅固定已锁plugin-react6.1.1和Node22类型22.20.1，不改运行依赖、Node要求或pnpm11.2.2。App仅改两篇工程README，不迁共享包、不改业务／依赖。

三owner均从fetch后的main树开始，原Root pins与main树相同：Billing43a60920（原pinb7c98588）、Mori12a10608、Appe3ece750（原pinb93acbd8）。App #49全分页287路径不含两篇README；Billing无他人现役PR写区，Mori亦未操作他人PR。Root与各仓Git／PR由主控串行，三名聚焦代理各自写区隔离，独立只读审查再核最终候选。

上段为起始盘点与执行范围；停写验收与实际交付结果如下。R-03／R-06／R-14／R-15及重叠部分均不借本轮勾掉，R-05正式业务准入不混进开发类型对齐。


### 本批停写验收与结余

- **既存WIP保护：** 原仓App登录失败页的完整文件／基线／二进制补丁私有归档保留；尚无本轮已核恢复或交接完成的证据，TODO继续列待核实，不因压缩历史删除该义务，也不直接覆盖当前main或他人修改。
- **盘点结余：** R-08已列文档余项收口，故编号问题变为8闭环／8仍有遗留；遗留为R-03／R-05／R-06／R-07／R-09／R-11／R-14／R-15。R-11仅Mori完成，App类型余项仍在，不能整体关闭。Billing旧总factory候选另已清理，BFF旧Admin允许表候选继续交原owner，不增新编号凑数。四项产品验收暂存及容量／取消策略边界仍单列。
- **App文档交付：** [#54](https://github.com/LordFoxFairy/kokoro-app/pull/54)正常合main，源码`7182873fced2a58f0dd3bd052f492f10aef266e4`，merge`1e6b1aa5bf7d482f699f8ac0eded5c4faf362152`。仅README及packages README；主控15本地相对链接、manifest／lock／真实SDK／Playwright入口事实检查通过，独审CLEAR。没有业务／门户构建／浏览器重跑，不把preview入口存在当真实owner旅程通过。Task B #49完整287路径不含两文档。
- **Billing清理交付：** [#5](https://github.com/LordFoxFairy/kokoro-billing/pull/5)正常合main，源码`afbfd790c28939cf0e85c0db0b40b737271ee450`，merge`ecdea64b380705c9d5728ce9a62823b6be9c3594`。仅旧aggregate factory、专属helpers和3个无consumer类型删除；从createBillingPersonalAuth到文件末尾的现役Personal／Catalog实现与基线逐字相同，JWKS verifier未改。有效EdDSA／tenant／R73真实JWT与签名断言迁现役factory，旧header／admin／白名单退役模式或已被现identity／operator HTTP承接的测试退役，并将三个错factor负控交现役入口。不按数量删保障。
- **Billing验证：** worker基线7文件290通过，迁移后且删除前288通过，删除后288通过。主控对冻结输入独立格式、lint、类型、build及同7文件288通过／0跳过。worker首轮lint41项生成类型未解析，正规prisma:generate／typecheck／build后消失，失败证据保留，未修改那些非任务业务。无Schema／机器合同／依赖变更，不跑真实PG或全默认，未称全产品门绿。
- **Mori依赖分片：** [#2](https://github.com/LordFoxFairy/kokoro-mori/pull/2)正常合main，源码`d363816e58d3e96fadcc75021d89d789c20916e8`，merge`5de3a79084a89d596ea252368b695ed3e4558baa`。仅manifest／lock两文件，插件latest固定到旧lock6.1.1，Node类型20.19.43对齐22.20.1，undici6.21.0保持。主控限定转换后全lock与基线逐字相等，除了这两声明、Node类型版本／integrity及关联peer key，没有任何运行resolver／SRI变化；未升级Next／React／Vite／pnpm。
- **Mori验证：** Node22.23.4／pnpm11.2.2按owner要求，worker frozen安装接受，主控完整pnpm check的lint／types／86文件706测试／build通过；jsdom HTMLMediaElement.play未实现提示保留，不称媒体实机验收。未改R-05正式认证接线或共享包迁移。
- **交付控制：** 独立只读审查三片CLEAR；主控核冻结10个路径hash与最终源码一致。三owner自有分支删除前均核精确tip，main包含源且merge树等于已验源；保留Root精确源码pins，不机械换merge SHA。不操作他人PR、分支或worktree，不启业务服务／DB，不部署、不以远端CI代本地证据。

Root本次PR仅承接App／Billing／Mori三精确gitlink、95项来源引用（按87个真实提交blob重新核摘要）和报告／CURRENT／唯一TODO；Mori没有既有contract边，不为此新建空契约。实际组合／链接与最终main清理由本次Root PR和主控Git回执确认。


## 15. R-07 Storage分片与R-09治理校准

日期：2026-11-11（America/New_York）。起点Root `ff0e36dfea6e77b55ef21fb2ee4352830a48799a`。Storage从已合main `635b18f83151a8a2dd28fa982ab8db4fa5c6ebea`开始：与原Root pin b60931e9仅差两行已经交付的架构测试，整个生产src树相同，保留main更新而非回退。Task B Root #67和Storage #2的最新全分页文件范围已核，不触及其业务／Schema／扩展脚本；主控与两writer分区，Git／台账只由主控处理。

R-07只修Storage，不改Capability：保留原正式Buf template和显式generate；只读check用本地固定CLI的output前缀生成到唯一临时目录，复用同normalizer，对完整相对文件集合与Buffer字节比对，缺失／多余／漂移失败，symlink不穿出目录，成功／异常finally回收。HTTP原--check与现语义／RPC／provenance检查保留；不改proto、运行代码、Schema或依赖。回归使用隔离fixture，不为测试损坏正常工作区生成物。

R-09只修三个已证机制：profiles真实覆盖12子仓（含libs/shared实际路径、Admin真实源码目录），web／源码library按固定职责验质量入口，不给无DB／传输owner造空Schema或契约／发布模板；保留已经存在的BetterAuth精确pin／provenance例外，以正式owner路径／visibility识别native／browser-private，不全放过vendor或/v2；保留受限YAML解析器，不新增依赖或自建完整parser，确实unsupported进入阻断unverified并停止“缺owner契约”级联，可识别的无效JSON／结构和真正缺文件仍失败。现TS工具安装unknown语义不借机更改。

只补这些命令／分类器的合法、违规、未知反例，再运行静态诊断观察残余FAIL，不把原414条词法记录当编码任务或零违规目标。Storage只跑相关契约／脚本静态验证，Root只跑相关治理测试；不启动业务服务、浏览器、PG／Redis／S3／Scanner或全产品套件。

### 阶段证据与必要纠偏

- Storage自有[#4](https://github.com/LordFoxFairy/kokoro-storage/pull/4)已正常合main，源码`231bb6632c9962d18ce48c6e998384fb76497d06`，merge`a8edebf83f9b1df9e428c2c8ce35b5ce812f5046`；合并树与已验源相等，自有本地／远程topic已删，checkout保留精确源码pin。主控独立7项真实命令回归、typecheck、focused ESLint／格式、正式contract:check通过，321个tracked／新增输入验证前后摘要不变，独审CLEAR。旧正式check对漂移仍退出0的RED保留。早期fixture触发pnpm自动安装及macOS长TMPDIR引起tsx IPC错误属环境失败；最终fixture显式禁安装并用短路径，不将环境失败称缺陷RED。远端CI显示FAIL，日志接口返回log not found；未冒称远端通过，未重推／绕保护。
- R-09首轮独审发现YAML非字符串版本被误判unsupported；补JSON／YAML等价反例修正后，主控341项fixture通过，真实静态诊断随后仍FAIL：12仓、552条结构规则记录、4项unverified（BFF／Billing的受限YAML解析，shared两个未安装TS工具）。它证明覆盖／诊断已变化，**不证明原生／snapshot归属已收口**：当前合法browser-private、历史IAM／Scheduler导入与Mori adapter仍误判。沿同写区补已有manifest／owner Git blob的可追溯来源分类，不豁免裸vendor、篡改或未知来源，也不把552条记录变为552个TODO。
- 精确Storage组合首次拓扑PASS，但兼容／checkpoint FAIL：Agent原固定Storage发布receipt仍指向b60931e9，被强制要求等于当前Storage运行源码，即使proto与provenance完全相同。最小纠偏沿已采用的“不可变发布锚与私有runtime解耦”：仅Storage允许精确祖先发布锚，逐字核当前／发布的全部生成输入和owner provenance，原消费副本／生成器／运行依赖负控保留；Platform不变，不为内部check脚本变更重发Agent相同机器契约。主控记录此局部治理决定，再由独立写区补反例、停写验收。

### R-09最终停写验收

主控独立治理fixture 372通过；现有真实CLI smoke另单独执行并采同一次child输出，故不是把deselected项称通过。八文件Ruff／format及diff检查通过，独立归属复审CLEAR。最终实际诊断仍exit1／FAIL：12仓、294条结构记录、4项unverified；所针对的http-versioning、snapshot-provenance、contract-owner误报记录为0。原552／4候选保留，第二次实际诊断只因首轮发现未收口归属问题而补，不通过反复改基线／删规则刷绿。

4项未验证为BFF与Billing canonical YAML超出受限解析器能力，以及shared两个package未安装TypeScript工具；前两项默认阻断，后两项沿原可选工具语义。没有替换parser、安装shared依赖或将缺证据记PASS。294条记录包含84条文件粒度词法提示与63条operation治理记录等，需结合owner事实筛选，**不是294个已确认缺陷或本轮待修数量**。导入契约只证明所固定发布来源（含历史snapshot），不证明当前消费活跃；Mori同源版本合法也不补造缺失metadata。原R-09的覆盖／归属／诊断机制按此有界范围完成，其余维护项继续唯一TODO，不借工具校准宣布整个产品全绿。

### 精确组合与本批交付范围

Storage发布锚回归先复现private runtime变更误拒的RED；冻结后writer完整兼容性151通过，主控独立9项新增行为／负控与11项checkpoint回归通过，相关Ruff／format通过。发布OID、祖先、COMMON／STORAGE proto、owner provenance逐字一致仍是硬门，改源、未知／非canonical／非祖先发布均失败；Platform／IAM原分支未改，Agent receipt字节及消费者commit不动。随后主控实际拓扑PASS、15条契约边／0违例、原Task A checkpoint PASS。Storage15项来源引用按9个真实提交Git blobs重核，没有机械换摘要。

最终编号为9项有界收口／7项遗留（5待处理、R-07与R-11部分完成）。R-07只交Storage，R-09只修Root分类／诊断；原产品暂存、App既存WIP保护／交接及Task B重叠项原样保留。Root本PR承接上述代码、精确Storage gitlink和唯一TODO／文档，不操作他人PR、分支、worktree，不部署。未重跑全产品／业务服务／真实基础设施，也不把远端CI记为本地通过。

## 16. R-05 Mori同源adapter修复

日期：2026-11-11。用户授权继续R-05，沿自有PR合main并清分支，不动Task B。Root基线7edca39a，Mori从main 5de3a790开始，与原pind363816e树相同；已核Mori没有他人OPEN PR。复用原R-05范围与Mori技术／API设计，不另建计划中心。唯一源码writer负责现route.ts与route.test.ts；另一writer只负责7份旧Cookie机器契约、相关契约断言与工程文档；主控独占Root台账／Git／资源验收，第三名代理只读审查。

### 最小设计与验收边界

Mori不成为身份owner，只消费Product在同一公开origin已建立的IAM原生会话。配置只接现Product三项KOKORO_BFF_BASE_URL、KOKORO_INTERNAL_SECRET_WEB_BFF、KOKORO_WEB_ORIGIN；先核入站同源，再向BFF固定Origin及服务凭据，Cookie限定原生6名，忽略其他Cookie并拒歧义，旧kokoro_session不再有效。删除namespace、可选principal及根据loopback注入的全部默认，不新增fixture模式或独立OAuth／token／SDK。fixture仅测试harness显式配置同一通道；禁跟随重定向，保多Set-Cookie及追踪。Mori七份当前已声明旧session的契约只更正认证scheme，不动业务字段或owner。

普通命令body上限1MiB／读取5秒；仅既有音频PUT creative-source-uploads/{ref}/content保UI 50MiB／读取120秒，随后回执30秒。普通API从入口到响应完30秒；媒体／SSE首头30秒，之后仅pending upstream read空闲60秒，不以播放器背压当卡死、不用普通短总期限截正常流。原字节、Range／If-Range、Last-Event-ID和幂等键保持，取消传上游并清reader／timer／listener，不自动重试未知写结果。数值为本次本地传输保护，不冒代表性SLO测试。

现Mori没有独立登录／session路由，Product return_to尚未支持任意Mori路由；本片不复制完整登录系统或改App／IAM。BFF当前Music映射缺媒体、上传等Mori preview seam；不接管该业务owner、不声称独立站冷登录／真实播放或音乐产品全功能已通。验收只补当前adapter失败反例与原生凭据／有界传输；主控一次相关owner check、实际socket到现BFF入口的局部接线（IAM准入与Music owner明确替身），不重复Task A全产品或真实PG／Redis／音频provider验证。设计门先落Mori TECHNICAL_DESIGN／API_CONTRACT相关段后再开生产修改。

上述是实施前决定，停写后的实际结果与交付另补。

### 停写验收与交付

- **Mori交付：** 自有[#3](https://github.com/LordFoxFairy/kokoro-mori/pull/3)正常合main，已验源码`3a4400e3dd9ed9530f06309c718e0e0e3f46520f`，merge`6d98924ebbfb3ae707901b6ed812f6503ff17173`；合并树与已验源一致，自有本地／远程topic已清理，Root锁精确源码而非浮动main。18路径只含现adapter／回归、认证契约与必要文档，无依赖／Schema／owner改动，远端未见CI运行，不将它说成通过。
- **有意义的RED与局部修正：** 先复现旧代码缺Origin、1MiB+1仍放行，以及7份旧session契约。独审指出写入响应若伪装audio/SSE会逃逸普通总预算，限定仅GET长流；主控按锁定Next源码核实其内部URL来自fetchHostname／port，公开Host／Origin正常也可能不同，故不拿内部URL作身份，未信任x-forwarded-host。两处先补行为RED后修正，保坏Host／Origin原负控。冻结route30通过、契约三文件13通过；不为缩数量删保障，不新增框架／配置层。
- **主控一次owner门：** Node22.23.4／pnpm11.2.2的`pnpm --config.verify-deps-before-run=false check`通过：lint／类型、87文件739测试／0失败／0跳过、production build。270个tracked／新增输入摘要前后不变，冻结源码／契约与交付逐字相同。之后主控只补CURRENT真实验收与RUNBOOK亲建测试进程措辞，未重跑无关全门。独立18路径实现审查CLEAR，当前链接／diff检查通过。
- **实际HTTP接线：** 用亲建独占端口启动生产Next（Node22）和现BFF Music入口（Node24）本地HTTP peer；IAM admission及Music owner明确替身。通过公开Host／Origin与内部Next URL分离的成功读取、原生Cookie筛选、多Set-Cookie；同会话第二次准入撤权401，准入累计2次／Music owner仅1次，跨源与旧Cookie在Mori层拒绝、不增加准入。未运行真实IAM浏览器登录或Music供应商／媒体链。测试Next、BFF与owner socket均已关闭，未动正常服务、PG／Redis／卷或他人资源。
- **真实首轮失败保留：** 主控HTTP首测403，诊断显示mori_origin_rejected且BFF零准入。用同机最小HTTP回显定位Node24 fetch未发送指定Host（实际为内部127.0.0.1），而http.request正确传公开Host；仅改验收脚本后同旅程PASS，未放宽生产Host校验。首FAIL、诊断及最终PASS私有证据均保留，不将该夹具失败冒生产缺陷。

R-05按原报告的adapter欠账范围收口，编号变为10收口／6遗留（4待处理、R-07／R-11部分完成）。Mori独立冷登录／Product挂载和Music owner上传／媒体等未接能力另列产品暂存，不借修代理冒音乐产品交付；其余Task B重叠项及App既存WIP交接仍保持。Root只更新精确Mori gitlink和现报告／CURRENT／唯一TODO，原inventory无Mori引用，不新造空活跃契约边；主控实际拓扑PASS、15条契约边／0违例、原Task A checkpoint PASS；Root自有PR承接该精确组合。

## 17. 主线范围纠偏与最小清理

日期：2026-11-11，基线Root9957b41d。用户明确重点是主工作台、BFF、IAM/OAuth及旧代码，不是Mori独立音乐产品。本轮停止Mori后续，产品待办退出唯一TODO；旧合并保留历史，不擅自回滚main，也不将其计作主线交付。原16编号排除范围外R-05后，主线15项为9收口／6遗留。以下只处理既有问题，不启动新一轮全仓扫描或认证重写。

**独立写区与基线：** App main1e6b1aa5、BFF main58222407、IAM main9f260bb6，三者树分别等于原Root pins7182873f／a3e19062／cee88df4。每仓从非递归fetch后的main建自有codex/product-auth-cleanup；三聚焦writer隔离，主控独占Root、验收与Git。Task B App #49的package实际hunk是contract新增generator，未改check或Node类型，lock／vitest配置不在其清单；BFF #17的同policy实际hunk是三条账务business准入，不碰admitBrowserService尾部旧表。按实际区块保留对方改动，不操作其PR或分支。

- **BFF旧代码：** kind:iam唯一生产caller先经过现原生／邀请闭集，旧Admin四项/jwks、/oauth2/token、/oauth2/userinfo、/oauth2/revoke没有可达消费者。仅browser-service-credential.policy.ts尾部改拒绝，在既有iam-protocol-relay-policy测试承接；保web-bff、Admin business及凭据校验。IAM自身对外端点／OAuth、BFF native relay、机器合同、生成物与Schema均不改。
- **App R-11／R-15：** 仅package／lock及两条CI的验证步骤；App共享CURRENT与Task B有多处实际hunk，保持原文，由Root台账和本PR承接记录。Node类型对齐本组合既有22.20.1，pnpm／运行依赖保持；聚合check使用锁定pnpm原生正则sequential执行现全部contract:check:*，再lint／types／default test一次／build。独立contract、test:architecture、test入口及glob保持，现22项generated checks不减，Task B未来新增同模式检查自然承接。不新增runner、测试框架或删除断言；先在亲建最小fixture证明命令集合／重复次数／失败传播，最终主控只跑一次调整后的owner聚合门。
- **IAM文档：** README当前0.20尚待consumer的叙述与canonical／SDK0.21及BFF正式pin不符，更新README和contract README当前段。introspection／Product client配置有真实调用，仍是必填：它们服务保留OAuth／资源授权分支，不表示普通Browser／BFF主链需OAuth换票。不删除这些配置、不改运行代码，不用文档变更重跑IAM全业务测试；历史版本／验收标题保留。

本轮无新owner、Schema、API、SDK、token或缓存层；局部清理复用既有决定，无另建ADR／计划／准入表。亲建fixture不启动正常业务服务或共享资源，Mori／Task B／App既存WIP保护范围不动。以上是实施与最少验收边界，实际停写结果另补。

### 停写验收与交付

- **BFF旧允许表：** 自有[#22](https://github.com/LordFoxFairy/kokoro-bff/pull/22)正常合main；源码`22943ec3efa3709b130e89d24f15b1d0fbc072e5`、merge`545b1fd3b57b32ea68b4bdbe8c13b44233bf53ab`，合并树等于已验源。生产仅1行，现有test增加2个聚焦case／63行，原测试块完整保留。先正规build旧行为RED1失败／1通过，再修复GREEN11通过；主控独立build／lint／类型及policy／transport／native session／user admission四文件44通过／0跳过，1134输入摘要无漂移，独审CLEAR。初次默认formatter噪声已撤回，使用正式no-semi／160参数检查，不因格式扩大源码改动。published relay、generated、SDK、依赖与Schema不变；不重跑无关全默认／真实PG／Redis／浏览器。
- **IAM文档：** 自有[#8](https://github.com/LordFoxFairy/kokoro-iam/pull/8)正常合main；源码`40cda8e32347b72b3932b496a5fe85c824e03136`、merge`421f36fe92cfaeff6e41c4cb0cc416f699cb0453`，合并树等于已验源。仅两文档，主控22本地链接、canonical／SDK／BFFconsumer版本和固定摘要事实、冻结hash／diff通过；没有运行源码或配置删除，不以此重跑IAM业务门。真实introspection／Product client配置及外部OAuth保留，普通BFF业务不新增换票。
- **App R-11／R-15：** 自有[#55](https://github.com/LordFoxFairy/kokoro-app/pull/55)正常合main；源码`906f9c01bb77ced651637198a665a7465e0df016`、merge`c6131dde7a1653584a9a6391440dcbb83a58a75a`。最终仅package／lock／ci.yml／release-image.yml四路径；Task B共享CURRENT完全未改，记录归Root。主控独立把新lock的Node版本／SRI／specifier逆归一后与基线逐字相等，1200包图其它字段与运行resolver守恒，undici6.21不动；manifest只改types及check两键，两个workflow精确转换之外全字节相同，Cloudflare无此重复未动。
- **编排与实际门：** 锁定pnpm原生命令在亲建fixture实跑：原Vitest3次→新1次，22项生成检查各1次；检查exit23时后续lint／test／build不进入，fixture已回收。主控冻结输入一次Node22.23.4／pnpm11.25完整check通过：22项生成检查、lint／类型、363文件6519测试／0失败／0跳过、production build，日志只一次Vitest启动，1558输入摘要前后不变；独审4路径CLEAR。不删测试断言或缩发现范围，不用数量推断收益；未单独跑Playwright／全产品，也未创建tag、运行release或部署。
- **安装失败边界：** lock更新初次workspace-root保护拒绝，随后显式-w；offline frozen因供应链元数据缓存不全失败，并非类型或业务失败。保留原供应链策略，在线frozen29.3秒通过，实际Node类型22.20.1；registry额外deprecated元数据噪声已去除，原caret声明风格保留、lock精确固定。不禁策略、不借机刷新运行依赖，所有原失败保留。

三个子仓自有本地／远程topic清理前均核精确tip、源为main祖先及合并树相等，checkout保留已验精确源。主线15项现为11收口／4遗留（R-03／R-06／R-14待原owner，R-07部分完成），旧BFF候选另已清理，不新增编号凑数。Task B PR和分支未操作，既存App WIP及产品暂存原样保留；Mori不计本轮进度。Root387项来源按320个真实提交Git blobs重新核摘要，原发行锚／consumer机器字节不机械换新；本次Root PR只承接精确组合与现台账。
