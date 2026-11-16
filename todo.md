# Kokoro · 已批准范围交付与条件暂存

更新：2026-11-16（America/New_York）。仅维护下一动作、进入条件和完成边界；详细完成过程由固定 Git 历史保留。

## 本轮已验：BFF IAM 账户资料／会话传输收口

用户批准的窄保行为重构。只合并两账户客户端真实重复的fetch／绝对预算／取消／响应头与字节上限／reader回收机制，认证、schema与业务错误仍留各客户端。现iam-http-transport为NodeHTTP及不同使用边界，本轮不迁其它消费者；新窄共享函数不读凭据／身份／环境，不建SDK、Base类、port或通用框架。

保资料10秒上限、服务＋actor无Cookie、严格raw JSON及generated response缺失补回；会话5秒上限、专用凭据＋原Cookie／Origin、原generated JSON解析、缺response分类及raw Retry-After不变；initial取消／过期零I/O、非合作fetch／reader迟到回收和原错误元组保持。实现agent独占两client＋一个窄transport文件，测试agent仅既有client测试必要补缺，审查agent只读差异，主控独占docs／TODO／Git及最终验收。契约／generated／Schema／依赖、其它客户端和Mori不动。

- [x] 单一窄函数收口重复传输；认证／schema／业务错误各留原client。资料10秒／strict raw／response补回及会话5秒／Cookie-Origin／原decoder保持；候选profile取消检查位移已修回race结算后、finally前，会话不加额外完成校验。
- [x] 原client基线主控61 PASS，测试agent只补两项原实现特征后63 PASS；主控停写5输入验收四client／HTTP文件79 PASS、architecture 111 PASS，lint／types／build／相关正式格式／diff通过，独立修正后审查CLEAR。无私有微任务矩阵，不把原63绿冒窗口证明；未跑模型／真实IAM／PG／全默认／契约生成／部署或重启业务服务。
- [x] TODO／CURRENT／导航及独立审查已完成；BFF [#30](https://github.com/LordFoxFairy/kokoro-bff/pull/30)已合main `3002d271f0602dd525d861a522bbc296a3a9947f`，树与验收核等，BFF本轮topic已清。Root精确配对gitlink，按233真实blobs重算291处inventory引用，内容摘要全保持；拓扑／兼容性15 edges、0 violations／原checkpoint均PASS。随Root本片正常PR交付，Root合并与本轮topic清理以最终Git回执为准，不预写未来SHA。

## 本轮已验：Web Hub 处理器与分发收口

用户批准按现有能力拆分，不改API／业务语义。现MCP、Custom API及六个Skills具名处理器进入既有lib/server目录，实际共用的projection错误／请求约束与下载头／流校验各保一处；路由只保原顺序／条件分发及Next runtime／dynamic／HTTP exports。原末端包含多种闭集响应的BFF转发整体进入hub-bff-proxy，不改其self剥离、managed URL特判或增通用registry／nullable-handler框架；不把它声称为新业务owner。

保权限／Cookie／Origin／owner选择、原path／body／key／CAS／header、取消／各自期限、错误shape／状态／request-id／Retry-After／EOF清理及分发优先级；不为统一外观修改原差异。主控唯一route／共享helper／fallback／台账／Git writer；两个agent分别独占MCP＋Custom API及六Skills处理器；第三agent只读核保行为。依赖、契约、数据、UI和Mori不动。

- [x] 八个具名处理器迁移并集成，路由仅原顺序分发；原末端BFF多profile整体迁移，projection／下载共用规则各保一处。18函数体／15声明、dispatch prefix／precedence／末端body／Next导出核等；清除误导的旧信封总注释，无新业务层。
- [x] 主控停写12源码输入验收：现相关5文件333 PASS、architecture 50 PASS，lint／Next typegen＋非增量types／production build及diff通过；输入SHA保持，独立行为审查CLEAR。原测试／断言未改，不跑模型／全默认／无关契约生成／浏览器／真实PG／部署，loopback fixture不冒真实owner E2E；自己Web已恢复HTTP200，其它服务不动。
- [x] TODO／CURRENT／导航已同步；App [#70](https://github.com/LordFoxFairy/kokoro-app/pull/70)已合main `db21d3a42160d25c671a7f5d64cfc6641ac3eef6`，树与停写验收核等，App本轮topic已清。Root精确配对gitlink与89个真实blobs／97处引用（1处摘要变化），拓扑／兼容性15 edges、0 violations／原checkpoint均PASS；随Root本片正常PR交付，Root合并与本轮topic清理以最终回执为准，不预写未来SHA。

## 本轮已验：App 未消费 @ai-sdk/react 退役

用户批准的窄依赖清理。tracked源码／脚本／测试无@ai-sdk/react引用，仅manifest／release-age例外及历史ADR提及；实际消息流由ai的readUIMessageStream与ChatTransport／UIMessage类型承担，保留ai及其现有版本／消息流／AG-UI／恢复行为。只删除该直接依赖与对应release-age例外，用pnpm正规重算锁与回收独占依赖；不手改lock、不升级其它依赖、不改App源码／测试、契约或Mori。Root仅联动check_web：删除强制安装未消费React hooks包的旧要求，保留ai／@ag-ui/core与原传输／边界规则，补3个最小正反例。

- [x] 核实际引用并删除未消费直接依赖；pnpm正规裁剪目标和独占5包，并移除react／mcp两条过期release-age例外。冻结安装通过，其余1121 packages／1122 snapshots内容、版本／integrity及ai依赖图不变，i18n和安全策略保留。
- [x] 现消息流4文件93 PASS、lint／Next typegen＋非增量types／production build通过；1344源码／测试输入逐SHA核等，独立配置复核CLEAR。不重跑全默认／浏览器／模型或无关契约生成，不冒性能提速。自己的Web已恢复HTTP200，其它服务、数据和资金不动。
- [x] TODO／CURRENT已同步、独立两面复核CLEAR；App [#69](https://github.com/LordFoxFairy/kokoro-app/pull/69)已合main `45091453c0413961c2e77b462dfb44bed102ebca`且树与验收核等、App本轮topic已清。Root旧依赖要求最小3例RED→GREEN，实际ai／core及所有原传输检查保留；精确gitlink与89个Git blobs／97处引用核等，拓扑／兼容性15 edges、0 violations／原checkpoint均PASS。随Root本片PR交付，Root合并／本轮topic清理以最终Git回执为准，不预写未来SHA。

## 本轮已验：BFF Projects／Skills 下载装配收口

用户批准的单仓重构；不重开Task A／Task B已完成范围或8项条件项。复用现ExactSkillDownloadService与owner客户端，将Module内具体来源解析移到具名factory（platform下Project／Skill各一文件），两处owner下载响应采用现skill-product-response内同一纯mapper；Module仅保原token／inject并引用factory。没有新SDK／Base类／空port／通用代理层，不改契约、Schema、生成物、依赖或认证边界；Mori不动。

保行为：缺配置仍null、对象origin优先级不变；Project同tenant／subject前后鲜验与owner projectRef校验保留；managed/share资格、exact revision、wire／timestamp校验、signal／绝对deadline与既有错误映射原样。两Module和factory／mapper由实现agent唯一写入；审查agent只读核行为，主控独占台账／Git／最终验收。

- [x] 沿既有目录收口两个具名source factory，两处来源下载共用现response mapper；删除Module内重复业务闭包，不改原下载Service。
- [x] 4项装配特征迁移前通过原Nest provider，最终5项已纳入默认入口；主控停写7源码输入核等，相关下载5文件45 PASS、既有architecture 111 PASS，lint／types／build／新文件format及diff通过。未跑无关全默认／契约生成／真实PG／浏览器／模型／部署，loopback夹具不冒跨owner实测。
- [x] 独立行为审查CLEAR，TODO／CURRENT已同步；BFF [#29](https://github.com/LordFoxFairy/kokoro-bff/pull/29)已合main `d29dd8b5d2c42406abe4ac306d1f3dc1150c7699`且合并树与验收树相等、BFF本轮topic已清理。Root精确配对gitlink，按233个实际Git blobs重算291处inventory引用（18处摘要变化）；拓扑／兼容性15 edges、0 violations／原checkpoint均PASS。本清单随Root本片正常PR交付，Root合并与本轮topic清理以最终Git回执为准，不预写未来SHA。

## 本轮已验：共享依赖核实与 App 重复配置收口

本轮由用户新批准，不重开已完成业务Goal。两只读agent按精确依赖核实：shared三包均有受保护消费者（包括范围外Mori及shared自身extends），不存在本轮可直接删除的闲置shared包；不把App/Admin未用冒全局无用。shared和Mori不改、不运行、不切分支；不借旧i18n名或其它App配置差异扩大修复。

最小设计：只将App本地packages/tsconfig编译基线合入App根tsconfig，退休本地同名包及manifest／lock／workspace／Docker接线；保留所有有效严格选项、文件集合、pnpm安全设置和正式i18n版本／SRI／registry。无新依赖、发行、业务层或契约。主控唯一Root文档／Git／资源writer；App配置writer独占这组紧密相关文件，审查agent只读。

- [x] 确认实际消费者与冻结修改前tsc --showConfig；不删除shared的真实依赖。
- [x] App有效配置合回单一根入口，删除本地重复package，正规更新lock与Docker输入。
- [x] 配置／文件集严格核等：官方完整showConfig前后相等（35选项／1234文件），1127包／1128 snapshots除本地link与空importer外不变，i18n和安全设置不变；冻结安装、lint、Next typegen／非增量types、architecture 50项、production build通过。离线metadata缺口及不支持CLI参数保留，最终沿原registry正规生成／冻结安装通过；不重跑无关业务／浏览器E2E、不冒Docker镜像已验。
- [x] 独立复核CLEAR，更新TODO／CURRENT；App [#68](https://github.com/LordFoxFairy/kokoro-app/pull/68)已合main `c3e2a82918879310007cc71139add8c8cdf5e8cd`，合并树与停写验收树相等，本轮App topic已清理。Root仅配对App gitlink及按89个真实Git blobs重算97处inventory引用（6处摘要变化）；拓扑／兼容性（15 edges、0 violations）／既定checkpoint通过。Root随本PR交付，合并及本轮topic清理以最终Git回执为准，不预写未来merge SHA。

## 正式交付结论

- **已批准范围正式交付，不再自动选择下一项任务。** Task A／Task B、两笔无预占恢复残留、R-06、核心链质量修复、H-01 metadata及单一真实只读MCP四步均已交付。
- **Task A 范围不包含 Mori。** 本处仓库口径为Root＋11个相关子仓：App、BFF、Agent、IAM、System、Billing、Capability、Storage、Scheduler、Admin、Web shared；这是业务／支撑范围，不是`.gitmodules`的全部登记。Mori属于其他App，不计入Task A任务、验收、PR或本地清理范围，也不改其代码或仓库结构。Web shared是包源码／发行仓，不是另一个业务App；当前明确由App正式消费的是i18n，不将其它未复用包算作已交付收益。
- 剩余 **8 项条件性遗留／可选增强** 见下表；本轮已补齐一个真实只读MCP调用／展示／刷新／撤权拒绝；其他条件和Provider专有授权不自动扩项。它们不是 8 个新故障，也不因暂存而视作已经完成。
- A-15 已定位生产启动成本，唯一候选净收益不足已撤销；不重复该试验，不为保持推进而扫描已交付代码或新增设计、缓存、测试矩阵。
- H-01 只交付本人草稿 metadata 编辑与 fresh 读回。**cover／discard／AI 仍排除**；不从旧代码或 API 的存在推导新增产品承诺。

## 最终收尾与 Goal 边界

机器Goal已在[Root #108](https://github.com/LordFoxFairy/Kokoro/pull/108)合main `eac123f6e79bb01d296591f1497b94a064fd67d7`并完成最终Git核对后标记complete；本次窄配置清理不重开已完成业务Goal，不开启新功能目标。**下方8项条件不属于本Goal未完成工作**；不将其伪标验收通过，也不保留一个自动持续扫描的active目标。

- [x] 自有PR核对：正式收尾核对时，Task A范围内Root及11个相关子仓作者LordFoxFairy的OPEN PR均0；最近Root #104／#105／#106／#107及App #67均MERGED→main。只核元数据，未操作他人PR。
- [x] 本地基线核对：Task A范围内12仓工作区干净、每仓1个checkout、实际本地branch refs均仅main、11个gitlink与checkout核等。System继续固定detached pin，不为整理擅动组合；Mori不计入本项，也不因其Root登记而进行任何清理。
- [x] A-14及其它条件项单独暂存，本轮不准备语音页面、不申请麦克风、不采集录音／口述原文；只有用户重新明确启动才继续。
- [x] 仅本次Root文档收尾沿正常PR交付；不重新跑业务／全量测试，不启动服务／浏览器，不动资金、权限、归档refs、私有配置或证据。主控合并后核main及只清本轮topic，Goal状态以机器最终结果为准。

## 本轮已验：一个真实只读 MCP 末端

范围仅实际工具调用→结果展示→硬刷新恢复→正式撤权后新调用拒绝。优先本地现成服务，不拿mock／fixture当真实，不新增SDK／认证层，不扩其它Provider、Skills、渠道或运维。主控独占资源／Git／台账与验收；两只读agent分别核已有服务候选及执行／撤权接线。

- [x] 正式目录确认原Context7可用并保持不动。本机无可直接接入的现成HTTP MCP；不关闭Agent strict egress来接loopback。独立QA连接使用真实公开DeepWiki／Streamable HTTP，无新SDK、账号授权或权限放宽。
- [x] 正常浏览器“Try it”预选QA连接并显式发送唯一成功任务；真实gpt-6.1-sol调用，mcp_list_tools／describe之后恰1次mcp_call(read_wiki_structure)成功，3956B结果及UI三条文档主题核等，不以声明发现冒调用。
- [x] 同一Run的durable FINAL／UI硬刷新前后正文及hash一致，刷新新POST0；后置owner读确认原tool journal未变化。
- [x] 仅QA Connector正式DELETE撤权；全新key／新Run收到202后，由Agent owner检查拒绝并终结为assembly_failed／retryable=false，UI可见；模型attempt0、MCP journal0、Billing admission0，不把旧回执重放或余额拒绝当撤权证明。QA server随后正式删除／fresh404，原Context7完整投影核等，临时会话logout200。
- [x] 本轮未确认生产缺陷，业务源码／子仓版本／gitlink保持，不制造补丁。仅Root验收记录与TODO沿PR交付，文档检查和独立验收后由主控核main与本轮topic清理。

本轮正常执行实扣13积分（现有21→8），4个新hold均结清；未充值／赠送，历史held30不动。首负控helper误把key放入正文导致invalid_message400，未产生Run；仅修私有helper后以正确header提交一次有效负控。原FAIL与正常子步骤分开保留，不重复成功任务、不扩大验证矩阵。

## 本轮收口：执行清单与交付事实一致

本轮唯一写区为 Root `todo.md`、`docs/CURRENT.md`。主控负责编辑、验证与 Git；两只读 agent 分别核遗留进入条件及精确交付记录，不检查业务源码或重跑旧旅程。

- [x] 仅核现有8项遗留和H-01排除边界，区分外部条件、产品决定与已完成事项。
- [x] 登记 Root #104／#105 和 App #67 的实际合并出口，删除旧 worktree／分支仍待清理的陈旧提示；不把归档引用当活跃工作。
- [x] 已完成长过程改为下方固定 Git 历史入口，保留原失败与证据，不制造第二套台账。
- [x] 文档diff／8个本地链接与锚点／2个固定历史对象检查通过；直接相关Root治理测试8 PASS，独立复核CLEAR。本轮沿Root文档PR交付，不扩大验证范围。

## 条件性遗留（本轮不自动开工）

| 项目／状态 | owner | 下一动作与完成边界 |
| --- | --- | --- |
| Provider专有授权末端／条件暂存（本轮单一只读MCP已验） | Capability＋目标Provider | 本轮DeepWiki实际调用／展示／刷新／Kokoro连接撤权拒绝已验。未使用的OAuth、续期和其它Provider授权仍在相应真实账号条件下验；不将公开无鉴权服务冒其证明，不重跑已验控制面 |
| A-13外部渠道／条件暂存 | 渠道owner | Telegram/LINE/Slack按实际使用的渠道，账号授权齐备后补收发/撤权；本地协议证据不冒供应商实测 |
| A-14本人语音／条件暂存，本轮不启动 | App＋用户 | 用户后续重新确认时间，再验主动口述→手动编辑→显式发送；当前不准备页面／麦克风，不保留录音或口述原文 |
| 完整E2B生命周期／可选运行环境 | Agent＋环境owner | 确认实际采用云或完整自托管后补创建/重连/独立回收；官方envd Docker已有证据保留，不当完整云验收也不重复跑 |
| A-15后续性能优化／production单边界试验已验 | App＋BFF | 真实owner production启动成本已定位，唯一Skills候选净收益不足已撤销；不把诊断当提速，不自动扩试其它页面／认证／缓存 |
| IAM共享源IP额度／非合作取消语义／容量边界 | IAM及对应写入owner | 有代表负载再核容量；不随意抬限流，不将HTTP取消等同事务硬回滚，不为已验功能再造组合矩阵 |
| 远端CI账单／额度／运维事项 | GitHub账户管理员 | 处理Actions账户条件后让正常CI运行；既存“未启动”不改写绿色、不绕分支保护、不重复push等CI |
| Provider专用长期审计／可选增强 | Capability＋Admin | 只有明确产品需求后立项；当前状态/receipt不称长期审计，现IAM/CustomAPI审计不重做 |

**保持关闭／不纳入本轮**：真实支付未接入，不部署；Mori属于其他App，完全不纳入Task A。

非合作取消的已知边界保留：HTTP 取消不等于下游事务硬回滚；不为此扩建取消框架或声称任意下游均可回滚。
两笔无预占恢复残留已审计关闭，旧 usage unknown／空 ACK 原事实保留，不伪造零用量。
历史 30 积分资金事项另案保留，不与这两笔无 admission 候选混算，不自动扩查、追加或回收资金。

## 最近交付与证据入口

| 交付 | 已观察到的出口与范围 |
| --- | --- |
| 单一真实只读MCP四步 | [Root #107](https://github.com/LordFoxFairy/Kokoro/pull/107) → `363daf1f6731e252f67a59244dc73d86e7c53fc8`。真实调用、UI、硬刷新与撤权后新Run拒绝已验；QA配置已删、原Context7未改。其它Provider授权不扩称完成 |
| H-01 本人草稿 metadata | [App #67](https://github.com/LordFoxFairy/kokoro-app/pull/67) → `a516cfcb991a080baaf51fef1c070ff57854db0c`；[Root #105](https://github.com/LordFoxFairy/Kokoro/pull/105) → `3c66f1739f8fff950acd630fd5b78d6238e97d10`。精确 gitlink、保存／读回／刷新及中法语窄屏已验；不扩封面／discard／AI。开发角色临时QA权限已还原，不修改默认成员权限。原失败与子步骤边界见 CURRENT |
| 历史源码／旧 worktree 收拢 | [Root #104](https://github.com/LordFoxFairy/Kokoro/pull/104) → `5a6c895cec76f0278a7488605604c1229c024418`；[逐项报告](docs/reports/2026-11-15-historical-work-reconciliation.md)。旧 checkout 已退役，源码通过 Git 归档保留；不整批恢复旧代码 |
| 真实浏览器核心链 | [Root #103](https://github.com/LordFoxFairy/Kokoro/pull/103) → `138201388931a8fa3198c9298eb7f9cf341e1c02`。当前组合任务→工具→产物下载→刷新恢复已验；资金授权、原失败和未验边界仍由原收据承接，不重复执行 |
| Task A／Task B 已批准范围 | [Root #67](https://github.com/LordFoxFairy/Kokoro/pull/67)；[系统总览](docs/kokoro-handbook/technical/00-system-overview.md)、[Task B 原功能交接](docs/handoffs/2026-10-30-task-b-capabilities-account.md)保留范围，不据旧 OPEN 文字重新开工 |
| 两笔无预占恢复残留 | [Root #93](https://github.com/LordFoxFairy/Kokoro/pull/93)；[报告§7](docs/reports/2026-11-14-historical-financial-unknown-readonly.md#7-2026-11-15-实际闭环与交付收据)。防迟到与独立审计关闭，不改资金、不造零用量 |
| R-06 GitHub 单一发行 | shared #2／App #64／[Root #94](https://github.com/LordFoxFairy/Kokoro/pull/94)；`@lordfoxfairy/i18n@0.1.0`，无 CNB 活接线；[方案](docs/superpowers/plans/2026-11-15-r06-i18n-publication.md) |
| A-15／后续代码质量批次 | [已交付详细记录（固定基线）](https://github.com/LordFoxFairy/Kokoro/blob/3c66f1739f8fff950acd630fd5b78d6238e97d10/todo.md)、[报告](docs/reports/2026-11-11-typescript-auth-admin-audit.md)保留实际收益、撤销试验、失败、具名验证和各仓出口；诊断不冒提速 |

[CURRENT](docs/CURRENT.md)维护时间序列；旧段仅代表记录当时，当前交付和清理结论以上述后继事实为准。[更早完整清单](https://github.com/LordFoxFairy/Kokoro/blob/8f68f9a3eb6d67b9f35c5e49e1f40d1955f7a07a/todo.md)继续保留，不复制历史为新待办。

## 本地保留与清理边界

- 上轮最终回执已核 Root／App 同步 main、工作区干净、本轮远近 topic 清理及精确 gitlink；不从“PR已合并”单独推导整个机器无遗留。
- 七个旧 worktree 与已核过时分支名已清理，不再列作占用待交接。源码 archive refs、私有配置、ignored 证据保留；它们不是活跃分支或待合 PR。
- 历史源码恢复入口见专项报告，不删 archive refs、不做 GC／历史重写、不把旧树整批合回 main。
- Task A中的System固定detached pin不等于脏仓，不为整理擅自切换或更新gitlink。Mori为范围外App，不操作其代码、分支、gitlink、配置或仓库结构。
- 不删除 ignored 运行配置、验证收据、数据库／数据卷、聊天记录或归属未明的工作；本轮不操作业务服务、模型、权限、资金或部署。
