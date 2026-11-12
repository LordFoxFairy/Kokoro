# Agent 真实主链路：复用可插拔后端的接线收口

状态：既有接口内实施方案；首片实现与运行状态以TODO为准，不宣称整体成功旅程。2026-11-12。
基线 Root `07241f03`，Agent `a9021318`，BFF `7c503f08`，App `026a7d12`。
本轮总目标与后续 AG-UI／首页阶段只维护在[唯一 TODO](../../../todo.md)。

## 1. 要交付什么

让普通任务不选择 Custom API 也能使用受信配置指定的沙箱，通过真实模型执行一条通用任务：读取已选 Skill、调用已选 MCP、执行脚本生成真实文件、交付 Storage FINAL，并在原工作台看到结果和刷新恢复。

**不重新设计沙箱。** 本仓已有 DeepAgents `BackendProtocol`、`Backend` 类型、connector registry 与官方 agent 装配。本片只修普通任务的后端选择与 Custom API 条件耦合。后端是否可插拔不是新需求；Docker只是首个本地实测提供者，不是新增统一执行框架。

“通用”表示生产逻辑不按任务文案、技能名、模型答案或测试标记分支；不是本片自动适配所有语言依赖、第三方沙箱控制面或任意包脚本。

## 2. 已核实的差距，不以旧证据冒当前闭环

| 事实 | 当前代码／影响 |
| --- | --- |
| 普通 Agent 默认 `state` | `agents/general.py` 继承 `agents/definition.py`；普通 Chat 在 `execution/custom_api_selection.py` 中才因 API 选择切到隔离后端 |
| 后端接口本来已经可插拔 | `sandbox/backend.py` 的 `_CONNECTORS` 包含 state/local_shell/docker/e2b/custom；返回 DeepAgents `BackendProtocol`，不能另建一套 factory/protocol |
| 仅改 backend 默认值不充分 | Docker 的资源／只读 root／日志限制仍受 `environment_provider is not None` 控制；`native_script` 还检查 `custom_api_selected` |
| 配方与恢复已有正确保障 | `assembly_recipe_bytes/fingerprint` 已存 backend descriptor；Factory在沙箱装配前由原repository核完整request／当前lease并比较，配置不兼容明确失败；首片保留这个行为，不新增透明迁移 |
| 文件有两种来源 | `execute.output_path` 捕获私有 scratch 的过程版本后清 scratch；`deliver(path)` 读取普通 workspace；二者不天然是同一文件 |
| 正常开发验收尚未建立 | 现存 Agent HTTP 私有持久配置仍在，不等于凭据全丢；Worker 的 System／BFF／模型预算配置需要按现字段合齐。旧进程登记不代表正在运行 |

## 3. 方案选择

- **推荐：修现有插拔接线。** 受信 Worker 配置选择普通 Chat backend；复用原 connector、SDK loop、租约、profile、Storage 交付与事件链。改动限 Agent 配置／装配／相关实际耦合处。
- 不采用重写执行平台：不建 SandboxManager、通用工具注册中心、第二 runner、内部 OAuth/token/SDK 或新事件总线；现接口已具备扩展点。

使用已有 `Backend` 类型和 registry，不再声明一套 provider 枚举。 普通Chat选择使用`KOKORO_AGENT_CHAT_BACKEND`／YAML `sandbox.chat_backend`；缺省不覆盖受信Feature声明，显式配置由现SandboxSettings验证真实参数，禁止host local_shell。Factory只在一处生成effective Feature，供build和cleanup共用，原catalog保持不变。新增普通 Chat 配置时遵守本仓 config.py／config_file.py／example 唯一映射，不改浏览器 Run body。普通产品任务不因此获得宿主 `local_shell`。已有 custom 扩展点保留；不支持某项授权环境的后端明确失败，不假设所有插件自动具备 Custom API 安全能力。

## 4. 后端选择、冻结与恢复

1. HTTP 不解析 Worker 私有配置；选择只发生在现 Worker bootstrap／Factory。
2. 普通 Chat采用受信配置；Custom API只叠加原授权环境及已有后端约束，不再是普通沙箱的唯一启用开关。
3. 原 `freeze_or_verify_static_recipe` 在 Acquire／沙箱装配前校验完整request、tenant、当前lease与配方。保原顺序，不新增读取接口／表／状态机。
4. 同配置重启仍承接原Run/checkpoint/journal。改默认backend、镜像或其他完整配方字段不兼容时明确失败，不启动另一后端继续旧Run；通过处理在途Run和新请求使用新配置，不承诺跨配置透明恢复。
5. 同一effective Feature用于permissions／tools／profile／backend／cleanup；不在各层重复推测backend，不为策略模式另建抽象层。

不新增 System／BFF／Agent 公开 HTTP／Redis字段、数据库表／列、RunRepository方法或共享DTO。现BackendProtocol＋registry就是扩展边界，不另外发明接入协议。

## 5. 沙箱与工具行为

- 沿已有 connector 注册／生命周期。Docker 的任务隔离、资源和日志限制不再依赖“是否有 Custom API secret”；使用现有受信限制，不另外发明容量策略。
- 保原 workspace、run/thread/lease 所有权、执行期限、输出预算、unknown-outcome journal、取消与清理；配置缺失或后端不可用明确报错，不退成假成功。
- 有 Custom API 时仍执行原 fresh Acquire／FileEgress；不把通用后端选择变成绕过授权的路径。
- Skill 沿 owner 批准引用→exact 包摘要→现 TypedSkillBackend／SkillsMiddleware 读取；MCP 沿现选中 connection→声明／授权→Acquire→官方 SDK→journal。不得自报身份或读取 owner 数据库。
- `/.skills/` 是虚拟文件路由，不是容器挂载。首片实测文档型 Skill／参考资料，由模型在普通 workspace 编写脚本；不宣称运行的是包内不可变原脚本，不为此搭 RO 挂载平台。

## 6. 产物的精确范围

首条任务明确使用 **普通 execute→真实 workspace 文件→现 deliver→Storage CLEAN／FINAL**，下载内容与该实际文件按字节／摘要核等。

现 scratch 过程捕获仍保留、独立验证解耦后的普通任务可用；不把过程版本伪装成上述 FINAL 的来源。要求“指定过程版本直接成为同字节 FINAL”时，应另沿现不可变版本事实和正式 Storage API裁决，而非从同名可变路径猜关联。本片不修改 deliver 公开工具 schema、不偷偷把 scratch 写回 workspace。

已经存在的过程文件／Canvas版本与 FINAL 两条能力都要在总 Goal 验收中列清，不以首条 FINAL 旅程代替所有版本来源验收。

## 7. 正常本地运行与真实依赖

主控先恢复持久运行配置，不复用测试临时库／模型 fixture 作为日常站点。保留现有模型路由，不造余额或每次 bootstrap；原先优先复用账号，本轮用户已明确全权授权本地账号准备，允许一次专用持久开发账号与最低成员接入，积分只走Billing原事务／流水并如实标明operator操作；不去掉 Billing 许可来做“免费聊天”。保原各 owner 受管配置，单库迁移不是本片前置。

启动 Worker 前核现 owner 运行配置、待处理任务和队列归属，防止盲目消费旧 durable 任务；只操作本轮已登记进程／容器。缺少真实模型或可用 MCP 时给出明确缺口，不把 fixture冒外部供应商验收。MCP优先复用已批准连接；本地协议服务只证明实际协议调用，不冒某个外部账号已接通，也不放宽默认 egress／SSRF边界。

最小旅程使用 Python 标准库生成一份报告，显式不选择 Custom API。仅核工具事实、结果结构／字节和状态，不要求模型逐字回答或强制 prompt中的某个固定执行顺序。

## 8. 写区与协作

| owner | 允许候选写区 | 保持不变 |
| --- | --- | --- |
| Agent | 现 config／Worker bootstrap／Factory／runtime_profile_plan／sandbox已有实现及同职责测试／三设计受影响段 | 公开 launch、Tool Journal owner、SQL canonical、SDK loop与checkpoint、MCP控制面 |
| Root | 持久开发运行的私有配置／进程记录、原入口实际旅程、精确组合、TODO／本方案／CURRENT | 不建第二应用 runtime或可编辑业务contract中心 |
| BFF／Storage／Capability | 本片正式消费者验收，默认不改源码／合同 | Task B 原 PR、分支、管理UI、Schema和控制面 |

原 Skill/MCP／Storage client 不建替身 production实现。发现合同确需增量先回本设计门，不把消费者未知字段静默放宽。

后继 App AG-UI与首页只进入各自切片：现 live client丢 chunks／历史slot用SDK的差异已确认；优先用现SDK reader形成唯一正文装配，不换 useChat 控制面、不泄原始思考／私有工具参数。首页按单一 Composer、任务优先、能力按需展开方向另做可视设计，不在 Agent 片修改全局布局。

Task B App #49 的 client.ts Share实际hunk与conversation-thread props存在；候选 openEvents／mapper／reader和首页文件已定向核，前者必须保留Share hunk，后者当前无文件diff。不以同名文件或缺patch声称零冲突；实施及集成前重核。

## 9. 最低充分验收

1. 现配置／profile定向回归：普通 Chat无API选择也能用已配backend；不可用明确失败。状态后端和已有Custom API路径不被破坏。
2. 冻结／恢复：原同配置Run重启恢复、不重做已完成MCP／交付；变backend默认／镜像的旧Run按原语义明确不兼容、不得执行，保当前lease约束。
3. 实际 Docker／隔离 PG／Redis：inspect核资源、只读root、日志限制实际生效，执行成功／超时／取消后的自有资源正确回收；不只断言命令行。
4. Agent本仓相关 Ruff／Pyright／contract／默认测试／build；不因Agent变更重跑所有子仓。
5. 冻结停写源码后，一条正常浏览器任务实测：原生登录→真实模型→Skill实际读取→MCP实际调用→普通沙箱真实文件→Storage CLEAN／FINAL→现AG-UI结果展示→刷新一致。保存模型提供方／MCP真实性边界，不输出凭据／私有工具payload。
6. 过程版本单独核事实与原内容，未证明与FINAL同源则明确区分；不把本片勾成全部Goal完成。

## 10. 收口与退路

停止新沙箱任务、处理在途Run；不重绑历史backend或增加跨配置透明迁移，不清历史对象、数据库、Redis或卷，不启宿主兜底。提交只沿各仓自有PR，Root后配精确子提交；按授权正常合main与清本topic，不动Task B、不部署。

实现后更新Agent技术／配置文档，以及公开产品指南中执行环境、文件与结果的真实能力说明；API参考只在 owner canonical确有变化时正规生成，不把内部配置写入公开客户端步骤。

## 11. 参考与证据口径

- [DeepAgents Backends](https://docs.langchain.com/oss/python/deepagents/backends)：现成可插拔后端与路径路由；项目仍以锁定 deepagents 0.6.7 的实际接口为准，不顺手升级。
- [DeepAgents Sandboxes](https://docs.langchain.com/oss/python/deepagents/sandboxes)：隔离后端提供文件工具与 execute；不等于配置一个镜像就已完成本仓装配。
- [AG-UI events](https://docs.ag-ui.com/concepts/events)、[AI SDK readUIMessageStream](https://ai-sdk.dev/docs/reference/ai-sdk-ui/read-ui-message-stream)：后继App片复用原有事件和SDK reader，不为新展示新增第二网络协议。
- [Manus quickstart](https://manus.im/docs/introduction/quickstart)：首页借鉴目标→上下文→执行→成果的任务路径。仅官方公开说明，未做登录态DOM／截图测量，不冒一比一视觉证据。

本方案初审时仅只读核源码／当前包／PR实际hunk与公开官方资料。后继已开展正常运行恢复、登录与首条任务，具体通过／失败以[TODO](../../../todo.md)与[CURRENT](../../CURRENT.md)的当前记录为准；尚无真实模型／沙箱首片通过。多agents只读分工：agent_runtime_closure、agui_closure_design、workbench_home_design；主控负责实际写入和验收。

## 12. G1真实运行发现的准入补口（本轮实施门）

现正常任务证明两个独立失败：供应商SSE error被误归internal_error；严格422 insufficient_credit未持久化拒绝且同attempt并发可能重复reserve。本节为现owner内修复，不新增沙箱设计／公开合同或数据模型；其余首片方案不扩。

- 供应商流：只新增锁定SDK基类APIError的精确type分类为既有model_unavailable/false，原status/validation子类不变；不得因此重试、补零或释放未知usage。
- 先修单次准入：begin_authorization的newly_requested赢家才发原reserve／proof；已有requested_unknown仅用现正式recover，404或失联继续unknown；已有granted不再联系owner。改现窄Protocol暴露已有recover，不新增RPC。
- 再接明确拒绝：仅首次reserve的完整有效422 insufficient_credit产生model层typed denial；不把409／503／坏ACK／recover404当永久拒绝。原活跃Run/lease锁内核exact pending/ref/digest及未dispatch，同事务写现denied授权、首条not_dispatched sealed usage2 evidence/head和Run completeness；原Schema已有此状态，无新列／状态。失败或失租整笔回滚，不产生零usage或financial ACK。
- 两步必须一起成立：否则另一个同attempt reserve的晚到grant可能被错误排除financial recovery。历史已封存unknown不凭日志／当前0行回填denied。
- 私有写区：Agent model/budget、call_models、call_artifacts、call_evidence，clients/model_budget，既有PostgresModelCallRepository/evidence与execution/failures；不写BFF／Billing资金、不改SDK loop／Schema／generated。纯transport分类先独立收口。
- 最低验证：现invoke/client用例；复用原真实PG budget_authorizer fixture证明单reserve、recover miss、并发、取消／失租、denial原子封口与重复稳定；保原financial unknown负控。只用本片独有证据，不重新跑所有子仓。

该门经agent_runtime_closure只读审计并由主控收敛；主控唯一writer和验收。当前实施／验证状态仍以[TODO](../../../todo.md)为准。

## 13. G3：实时正文与终态展示的最小收敛

正常模型/真实 Skill、MCP、Docker、Storage 旅程已产生实际产物；这不把当前 Web live 的手工拼字升级为“已经 AI SDK 单轨”。本片沿现 AG-UI transport，不新增 owner、网络协议、提交入口或 Schema。

- **唯一正文装配**：保留 decoder/mapper 的同一 frame；将已有 `uiMessageChunks` 接入现 SDK reader。engine 继续拥有命令、opaque cursor、重连和取消；reducer 只采用 SDK 产生的绝对文本快照，删除原实时正文追加，不保留第二条文字累计路径。
- **顺序与恢复**：同一 stream generation 内串行消费异步 SDK 快照，前序正文完成后再投影 terminal。重连从中段进入时用已确认 prefix 初始化同一文本 slot；history 的 bounded journal 保留可重放原输入，而不是只存缺前缀的快照。owner revision/watermark baseline 到达后，以同一 SDK 装配规则重放严格更新部分，保留当前409、取消、隐藏和 scope 退休保障。
- **生命周期**：close/hydrate/scope/dispose 同时退休 reader；迟到结果不写新线程。SDK EOF 不推断 Run 终态、不自己推进 cursor；原 transport dedupe/replay 不移到第二个 `useChat` transport。
- **真实展示缺口**：已观察到旧 `assembly_failed` Run 在成功 Regenerate 后仍显示 `Skill Loading`。复用现 `runTerminalsById`，将 exact Run 终态传到对应 process/Skill row；未完成 activity 在已知终态下显示中性“Run 已结束”，不伪造 Skill Ready/Failed，不用非 live 或超时推断结束。保留旧失败正文与新成功交付。`model_access_denied` 现同时承接余额与权限拒绝，文案覆盖两者，不另加 wire。
- **写区**：现 `client`/mapper/文本 reader、`execution-adapter`/`machine`、内部 projection/reducer；终态展示限现 conversation/assistant/process/Skill rows 与 i18n。保留 Task B Share 与 failure-code 的实际 hunk；不整体覆盖同名文件。
- **最低验证**：复用现 transport、parts reader/machine 和 UI 测试，覆盖重复 cursor、中段 prefix、迟到 baseline、terminal 紧随最后 delta、scope/dispose 迟到结果和不同 Run 终态隔离。正常浏览器复用本次真实历史与产物验展示/刷新，不再为同一后端风险重跑模型或全套资源验收。
