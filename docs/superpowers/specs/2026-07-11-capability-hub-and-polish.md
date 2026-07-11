# 能力中台(kokoro-hub) × 全域打磨方案(v1 定案稿)

状态:定案执行稿(五路侦察证据支撑;与用户"内部走 trpc"意向的分歧见 §2,依证据给出替代定案)
日期:2026-07-11
上级:`20-kokoro-v1-technical-plan.md`、`2026-07-11-platform-mainchain-closure.md`、skills/mcp 两 spec

## 0. 一句话

> skill/MCP 的**管理写面**从 agent 仓出走,进 platform 域新模块 **kokoro-hub**(注册/上传/审核/版本/启停/配额/运营位);agent 只留装配热路径直读。内部通信**不换 tRPC**,以 contracts 共享包 + 修四个实锤洞达成同等收益。web 按"三栏工作台 + 语义 token + 四卡精细化"打磨。

## 1. kokoro-hub 能力中台(新模块,platform workspace 内)

**为什么现在建**:写面今天只有部署 seed 一个调用方,但上传/审核/版本/灰度/运营位/MCP 注册每一项都会长大;admin 网关是 manifest 声明即接入的扩张模型(加配置不加代码),管理面挂进去零成本;session `pool.ts` 与 agent `hub.list_pool` 双语言同语义双实现是现存漂移痛点,收进 hub 单实现消除。

**为什么在 platform workspace 而非独立顶层仓**:复用 platform-kit(envelope/健康检查/启动器/admin manifest)、部署编排与 CI;与 user/credit 平级即是"中台子仓库"的正确落位;后期真要独立拆走,模块边界已备。

**边界切法**(侦察 capability-hub 路线结论,照单):
- **归 hub(TS)**:skills 上传/GitHub 导入(preview→confirm)、审核状态机、版本历史(Mongo 覆盖 upsert 改为 revisions 附表,S3 zip 本就永存=回滚零成本)、per-user/官方启停 API、namespace 配额、运营位(排序/置顶/分类)、**MCP server 注册表**(per-namespace,凭据只存 secret-ref 不落明文)、池查询 API(session 双实现的收敛终点)。
- **留 agent(Python)**:装配热路径全部——resolve_cards/read_body 双路/物化/graph state 账本/GC 自愈/MCP 三恒定工具与懒连接。agent 直读 Mongo+S3(hub 写、agent 读,读写分离同库);每 run 跨服务 RPC 是可用性耦合,禁止。
- **契约单源**:storage.yaml 已生成 pydantic+zod 双镜像;generate.py 增第三输出位(kokoro-hub/src/contract),校验常量(名称正则/大小/配额)入 spec 数据化,双语言同源。
- **双层守门**:hub 写面校验(入库守门)+ agent 装配防御校验并存,不算重复——信任边界各自校验是本仓既有法则。

**分期**:HUB-1 脚手架+skills 读写面迁移(seed 改调 hub / 或 hub 起后 seed 双轨过渡)+启停/配额 API;HUB-2 上传导入 preview→confirm+版本历史;HUB-3 MCP 注册表+admin manifest 接入;HUB-4 审核/运营位/灰度(配置表驱动,参考"配置即灰度"思想)。

## 2. 内部通信:不换 tRPC(证据定案),改修四洞 + contracts 共享包

用户意向"内部服务走 trpc 减少通信"。侦察实锤反对全域切换:
1. admin 中台核心机制 = manifest 声明 REST 路由 → 网关白名单代理 + RBAC + 审计 + 审批;tRPC procedure 无法被 manifest 声明式代理,切换=重写整个 admin 网关。
2. per-module OpenAPI 是 Python 侧(agent/litellm)未来消费的唯一通路。
3. 参考生态同样只在"单仓内前端↔BFF"用 tRPC,跨语言边界一律 HTTP+schema——与我们 web→session→agent 现状同构。

**达成用户真实目标(类型端到端、减少漂移与通信)的替代定案**:
- **P-A contracts 共享包**:各模块经 `@kokoro/<mod>` 导出 interfaces schemas,消费方 import 代替手写镜像(实锤:credit 的 activeSchema、payment 的 ensureAccountResponseSchema 都是手抄)。编译期即漂移信号,零运行时改动。
- **P-B 修四洞**:①payment→credit 裸 fetch 归队 callService(补 principal/internalSecret/错误信封);②requestId 头分裂统一(x-kokoro-request-id 单名,链路追踪修通);③**internal-secret 只发不验→服务端强制校验**(中台化前必须,否则触达端口即可绕 RBAC 打 /admin 路由);④payment↔credit 补 outbox/重试驱动(confirmOrder 中途崩溃订单悬挂),或合并 billing 上下文——V1 先 outbox。
- **P-C 减通信**:credit 改账热路径的 site/user active 双查加短 TTL 缓存;(主链)delta 事件不落库只 live 转发+completed 帧落库、snapshot/回放双份传输去其一——记档为主链读模型压缩块,不混本轮。
- tRPC 保留给:kokoro-web 自己的 BFF 层(单仓内)若后续需要——不强推。

## 3. 主链修缮清单(侦察 mainchain 实锤,按危害排序)

- M-1 model 允许集三处漂移 + resolveModel undefined 时 hold 缺 modelBindingId 仍放行(计价维度缺失):enforce 档下无绑定应拒绝;model 可用性收敛 platform 单源,profile.allowed 降级为展示过滤。
- M-2 store→relay 依赖反转(SessionEventDraft 应下沉 store/或 contract)。
- M-3 workspace key `{namespace}:{sessionId}` 约定进 contract/spec(现为三处注释级硬编码,改格式即静默失联)。
- M-4 billing client 手写镜像:P-A 落地后 session 消费 contracts 包或加跨仓契约测试。
- M-5 INDEX.md 覆盖:session relay/store/http、agent contract/execution/worker、web core/engine 补齐(边界事实从文件头注释升格为地图)。
- M-6 事件回放 O(N) delta 与 snapshot 双份传输(读模型压缩,大项独立块)。

## 4. web 打磨方向(对标 manus/lessie/hix 的抽象吸收,不照抄)

- **IA=三栏工作台**:折叠式单列侧栏 + 事件序穿插的会话流 + 可拖拽/全屏 **Canvas 工作区**(事件总线开合,产物点击即入 Canvas 非弹窗;开合带会话级记忆)。
- **四卡精细化**:工具胶囊 pill(状态→语义色,loading 流光,点击入 Canvas);计划链卡(逐项状态/可折叠);审批卡=动态表单(schema 驱动,与 HITL kind=input 契约天然对齐——我们已有 input_schema 上 wire,领先参考);交付物文件卡(骨架占位→实体卡,下载/二次加工)。
- **语义 design tokens**:全色走 `--k-*` 语义变量(text 四级/bg 多层/语义色三梯度),组件零裸色值;暗色换色相非反色;登录闸的 antd 缺省蓝即首个偿还对象。
- **流式工程**:块构建对象引用稳定化+memo 可见帧比较;离底暂停贴底恢复;刷新续流已有(水合+续流双链)。
- 分期:WEB-1 tokens+登录闸对齐+pill/计划卡打磨(现有卡升级);WEB-2 Canvas 面板+产物卡(接 snapshot.deliveries+下载端点,即块D-ux);WEB-3 动态表单审批卡(kind=input)。

## 5. 执行序(本轮启动)

| 块 | 内容 | 仓 |
|---|---|---|
| HUB-1 | kokoro-hub 脚手架+skills 管理 API(启停/配额/软删/官方位)+storage 镜像输出 | platform, contract |
| P-B | 四洞修复(secret 验证/裸 fetch/requestId/outbox) | platform |
| WEB-1 | tokens+登录闸+卡片打磨 | web(分支) |
| M-2/M-3 | 依赖反转下沉+workspace key 进契约 | session, contract |

HUB-2/3/4、WEB-2/3、M-1/4/5/6、P-C 记档为后续块,不丢。

## 6. 不做

全域 tRPC 化(§2 证据);skills 装配路径跨服务化;admin-web 硬编码页面重构(HUB-3 管理面接入时随 manifest 元数据一并解,先记档);参考材料任何路径不入正式文档(笔记只在 tmp/)。
