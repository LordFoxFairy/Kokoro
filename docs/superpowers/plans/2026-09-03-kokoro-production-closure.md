## 2026-10-20 聊天未就绪反馈：本次局部修复

用户最新要求在模型、真实工具和扣费保持暂停的前提下优化聊天体验。本次只修已复现的 `agent_not_configured` 提交前依赖状态：独立紧凑中性反馈组件，保留历史与编辑区，只有现有恢复能力允许时展示“重试原请求”，不自动发送。真实 run.failed、未知提交、402、原 key/body 恢复、AG-UI、BFF 和项目业务不变；不接管其他开发者的自动化/连接器。

正常 3310 已先复现旧红色整行错误，再实测新状态卡、历史保留、草稿可编辑和键盘到达恢复按钮；BFF 前置 guard 仍 disabled，未派发模型/工具/资金。实际截图视口568×766，不将此称为全尺寸或 Manus/ChatGPT 一比一验收。新增两项现有 suite 回归，定向214项通过；隔离完整233文件4446PASS/0skip、contract295/architecture50、lint/types/webpack build/posttypes全部通过，只读复核Approved。全测后仅整理两新增测试并加强新按钮标签断言，最终53项与lint重跑通过；其余1118输入hash不变，活动与隔离源码核等。App局部提交 `de5ffe5c0cae2aaf0a79b33bb09d49698d6c9671` 已在原正常源码目录由HMR加载，工作树clean；截图与运行收据仅保留ignored。

本批仍不报告整体目标或PR完成。MC-02后台表单的原标签仍是浏览器内部错误页，工具准入拦截未解除；未换标签/浏览器/底层通道绕行，正常后台页面验收仍待原标签恢复。以下MC-02范围和历史结果继续有效，聊天只放行本段明确局部切片。

## 2026-10-20 MC-02 当前执行目标：配置页面闭环后集中 PR merge

用户最新授权继续 BFF 接线、后台模型配置表单和页面验收，完成后集中 PR/merge；模型调用、真实工具执行和扣费继续暂停，其他开发者的自动化/连接器明确排除。沿已确认 System6 `550d654` / Agent `c2c7cf9`，不新增 owner、服务、System6既定表之外的数据表或通用配置框架。

1. **BFF（主方唯一writer）**：固定System6，独立model-management机器token，无通用token回退；IAM实时platformAdmin、tenant/actor保持。补既有资源provider/definition/feature列表，provider只写Key创建及脱敏创建查回，definition/revision创建、CAS发布、label创建/别名及默认修订修改共10具名操作；保原routing四操作，public21.1新增至175，不扩删除/恢复/health/草稿修改/密钥读取代理。
2. **Admin/App（主方顺序写）**：先消费固定BFF artifact，再按连接、模型修订、业务组合拆现Ant组件，薄same-origin adapter闭集配对。Key仅当前内存，恢复记录只存原key/主体/tenant/阶段/确认provider ID；未知provider创建刷新后只查，404仍未知，不换key重建；无手填tenant/handle，无自动重试。
3. **验收/交付**：定向RED→GREEN、owner相关完整门、真实IAM→BFF→System配置链、浏览器主路径/键盘/窄屏及失败恢复；正常配对前按既有备份/恢复/最小owner schema流程，不启模型或资金。独审/主方复验后才集中push、复用原PR、同步main/gitlink及清理自有已合topic；不动他人PR/分支。

### 当前检查点

- **源码已交付本地提交**：System6 `550d654`、Agent `c2c7cf9`；新BFF `f3da7d5`、Admin `4c8ec04`、App `0efd68f`。BFF Public21.1/175的10具名管理操作及同源消费已闭合，原key/CAS、当前管理员/tenant、Key只写及未知只查保持；配置表单分连接、共享修订、业务组合，不扩删除/health/执行。均未push本批，Root gitlink不指向未发布组合。
- **验证**：BFF格式/lint/types/contract850、architecture36、默认1503 PASS/3原资源SKIP和build；Admin固定契约/lint/types、217 PASS/0skip、独占webpack build/post-types；App七生成/contract295、architecture50、lint/types、完整4444 PASS/0skip、webpack build/post-types。独审Approved，修复缺省ACK绑定、截止后误成功、Next零字节POST流、超期provider只读恢复、外部目录重试及原修订详情回归。保留首次fixture/缺Redis/Turbopack外链root失败，不改旧oracle、测试skip/timeout或依赖。
- **真实链**：固定交付BFF提交的IAM→BFF→System6/PG配置创建、原key查回、发布、业务组合/别名清空、catalog、CAS/重放/冲突/非法session通过；自有DB94→94、IAM测试key0→0，进程已清。不是浏览器表单或正常执行验收。
- **正常配对已完成**：先备份恢复和事务回滚负控，再停四个原进程、冻结备份/实际恢复复演；同一PG client提交前核新表完整canonical、其余catalog及22表旧行指纹，唯一补System6 credential表。独立model-management机器凭据/私有加密材料已按既定方案配对；四服务由上述精确已验源码重载，System/BFF ready200，provider/definition/feature三目录200，未登录Admin新路径401。23表及旧行复验不变，新表空，原模型目录无provider/definition；现有1个正式feature不伪造。Agent disabled、retention hold，未改用户登录/权限/积分或启模型/工具/资金。正常App仅有Next自动生成route import差异，不作为源码提交。
- **仍待完成**：原后台标签处于浏览器内部错误页；用户要求自行恢复后再次从原标签获取，工具仍按URL安全策略拒绝。未换标签/浏览器/原始CDP或终端页面读取绕行；正常浏览器表单主路径、键盘/窄屏/视觉与本轮E2E尚未验，不用组件/接口成功替代。页面验收未完成，因此本批尚未集中push、更新Draft1或PR merge；不报告整个需求/上位目标完成。
- **Root交付核查**：主方重新执行相关隔离助手单测66 PASS/4 subtests、Python compile与diff检查，Root三文件只读独审Approved；五个候选HEAD均含origin/main且behind=0（System/Agent/BFF/Admin/App分别ahead8/2/3/3/3），App仅运行时Next route import差异。GitHub六仓当前仅System原Draft1，其余无open PR，本轮未push/新建/合并；System Draft1已关联当前任务，后续复用而非另开。原错误标签inventory仍是data内部错误页，没有重试被拒读取或更换通道。
- **同步与范围**：Root及12子仓最新fetch/prune全部0，远端main无新变化；自动化/连接器及他人PR/分支未动。只保留必要运行服务，自有隔离库/前缀已清，正常私有配置和回滚材料保留ignored。后续仍同一目标，不扩首页/聊天或新增框架。

## 2026-10-20 MC-02：密钥底座与 Agent 已隔离交付，后台旅程待接

已按用户明确批准的 System 现模块方案实现，无新服务／依赖。System6 `550d65498822d8d2e629199482de4f6990b62708` 在原model-catalog加密保存只写Key、独立HMAC脱敏receipt／永久创建身份、原主体脱敏查回、当前业务路由与精确修订Agent-only领取；原PG事务、CAS及恢复保护保留。完整owner门225 PASS／0SKIP，fresh33断言／23表canonical、格式/lint/type/build/contract均通过。独审Approved；55非model/probe递归表示除获准Feature身份枚举外保持，22来源Git原件核等。生成classification遗漏已正规重出并重跑最终全门；artifact `10ff7ee82ca7405dcab473f3fd80e620aa6c4e0bc92e64111797144ce0fa4061`、provenance `ed2e312bc5bc3022111797771190e57133818af83c0bb7ad2024a615a4e033c5`。

Agent `c2c7cf98138b9b6002e6033635ed952cea1501ab` 固定上述System6，复用原连接池受控领取，原默认label缺省不变，逐项绑定响应且要求no-store／有界／无重试；删除旧本地Key文件parser和配置入口，无双读。完整默认2405 PASS／773资源marker未选，frozen锁／Ruff／Pyright／contract／wheel-sdist及仓外安装合同通过；194运行Python与wheel逐字同源，原usage1／usage2／sealed历史／SQL／资金runtime不改。原PG+本地协议受影响两文件331 PASS，自有库清理库存核等；旧文件测试随已删除loader退役、当下独有风险由owner文件／密文与当前严格消费承接，原资金零发送／取消断言未削弱。

独立实际System6 HTTP／PG→当前Agent客户端隔离链通过：默认与显式选择领取、撤权／跨tenant拒绝、provider／receipt无明文；真实监听模型tripwire请求0。自有DB及Redis namespace已清、子进程关闭，未重启或修改正常服务／配置／库。Root及12子仓fetch/prune全0，remote main均无新变化，所有primary仍等于origin/main；不接管他人自动化／连接器，不覆盖其工作。

仅上述两组件本地提交，尚未push／更新原Draft1／merge，Root gitlink不指向未发布组合。正常System5/Public21／Web/Admin仍原源及PID，Key方案不因隔离通过自动部署。下一步仍为原需求：BFF窄模型管理接线→App/Admin连接Key输入／修订发布／业务引用别名／当前tenant可见默认→页面与未知结果恢复验收；无手填tenant或handle回退、不加网关或万能配置框架。当前浏览器目标仍有内部错误页交接，未转通道绕开工具URL策略；正常完整页面旅程待普通UI恢复后验。本节优先于下方历史候选／等待记录，不宣称整个模型管理或总目标闭环。模型、真实工具和扣费继续暂停。

## 2026-10-20 MC-02A 正常配对执行结果

- **已完成**：System5／Public21 与 App/Admin 精确提交配对；真实备份恢复、冻结复演、同 client 提交前完整 catalog／22表行指纹验证、回滚及错误 CHECK 负控。只按现 canonical 替换零行旧 revision／可空别名，无旁路兼容，无新增服务或表。四服务按原配置重载，System/BFF ready200，四个模型 owner GET200；正常模型目录仍空，BFF403／401准入拒绝与原契约一致。
- **未完成**：正常 Admin/Product 浏览器完整写旅程。内部错误页 URL 策略拒绝获取后未绕行；待用户普通界面打开目标本地页再验。不把预览E2E或隔离链称为正常写验收。
- **边界保持**：Agent disabled，模型／工具执行／扣费暂停，登录／权限／积分／机器配置不变，自动化与连接器排除。System/Admin 正常源码停机前、四仓启动前与各 Popen 紧前均核精确已验 HEAD；无盲重试或重复进程。
- **交付后续**：Key 保存／精确受控领取设计仍待独立裁决，提供方／模型创建发布管理仍缺；本批未 push／新PR／merge，Root gitlink不指向未发布提交。先闭合该需求与真实页面，再集中逐仓PR及Root组合，不扩展首页聊天写区。

### MC-02 后继完整配置旅程：实际缺口与依赖

四个固定提交／正式 artifact 审计确认：现产品管理闭集仅三个GET和租户routing PUT，System已有global label新建／别名及默认修订更新并未投影到后台。待现 MC-02 密钥及窄管理身份边界裁决后，按一个完整需求而非按钮分PR配对：

1. System先交直接Key创建／脱敏恢复与受控领取的正式契约和固定artifact；普通现有label／definition／revision发布复用原owner事务、CAS、幂等，不重写目录服务。
2. BFF一次性消费本旅程必要的业务／provider／definition读取、模型修订创建发布、业务label创建／别名及默认引用更新，并保留现tenant routing。global写使用接收方核验的窄模型管理身份，不借web-bff改名system-admin或将权限扩大到站点／产品其他管理域。
3. App/Admin按连接输入、模型修订编辑、业务绑定三个职责拆局部组件，沿用现页面／资格／请求取消和受限恢复；含Key创建的内存／脱敏恢复与普通routing恢复语义分开，不为复用强建万能表单或命令引擎。
4. 以同一共享修订配置两业务、别名省略／清空、默认及可见性、刷新回读、CAS／未知结果与错主体拒绝完成真实隔离链与页面验收；正常模型／工具执行／扣费仍不放行。零模型的正常200空页不是这条写旅程的正控。

本节是对已批准产品需求的缺口／实施依赖梳理，不宣称未决密钥候选已通过设计门。本轮只有只读审计及Root当前计划更新；未执行global写或扩展首页／聊天、自动化／连接器。

## 2026-10-20 MC-02A：共享业务模型跨仓验收与消费者收口

用户已确认共享配置、业务分别组合。System `b7fe78e`（5.0.0）、BFF `513b18e`（Public21/165）、Agent `10dc60f`、Admin `6aa68f0`、App `56f2bfe` 均为本地已验提交；未 push/新建或合并本批 PR。System 原 Draft1 继续复用；Root gitlink暂不指向未发布组合。模型/工具执行/扣费暂停，其他开发者自动化与连接器不动。

主方已独立重跑 BFF 七门全0（contract849、architecture36、默认1498 PASS/3原资源SKIP），独审无确定P0–P2；原20→19证明逐字保留，21→20可精确还原，162项其余递归契约保持。Agent System4→5 resolve＋3递归引用相等，20来源/Git原件固定；176定向、最终默认2399 PASS/773未选、frozen/Ruff/Pyright/contract/build及安装发行物检查通过。首轮退出/启动时限失败原留，不宣称已经修复原信号测试时限脆弱性，不改超时或skip。

Admin 同共享修订可供多业务引用，别名为空按当前路由override/default显示request_model；已修策略分页未完成却猜default名称P2，两分支真实组件RED→GREEN。主方独占副本127输入相等、完整七门全0、默认208 PASS/0SKIP；活动.next未覆盖。冗余自有构建取消记exit143，不冒通过。

Root正式隔离真IAM→BFF→System/PG主路径通过：业务chat筛选列表、slash稳定key与真实provider、无别名原request_model、精确revision、管理目录、CAS/原命令重放/冲突及非法session拒绝；自有数据库清理前后94=94、IAM测试key0=0，无正常数据或进程切换。Root原相关测试51 PASS。此链不含模型/工具调用、Admin浏览器写旅程或正常环境切换。

App Public21消费者已提交 `56f2bfee465b63711d4b38e270381a95844b4a92`；最终收口关闭两个真实P2：raw业务label贯通菜单→message→BFF→Agent→System，不再拼provider前缀；Chat列表固定feature_key=chat且拒非chat响应。偏好只用v2，旧key保留但不读/拆/迁移，未知提交冻结body/key原样。完整owner七生成、contract295、architecture50、lint/types/build、233文件4442PASS/0SKIP及既有桌面/手机预览E2E108PASS，无新增retry/skip；主方另在1116输入逐字同源副本验735合同/受影响engine/UI/偏好/loopbackHTTP、architecture50、七生成与lint/types/build全0。47路径/1116输入停写hash及原BFF Git blob核等、最终独审Approved。E2E专属端口/进程已退出，Redis前后88keys及摘要相同；这是受控预览浏览器与隔离owner链分别提供的证据，不冒正常执行或完整Manus像素对齐。前轮OIDC/Radix阶段失败保留，未扩修这些模块。

Root及12子仓再次fetch/prune全0，远端main本轮无新提交；五个受影响候选仓均已本地提交且clean。Root现有4项范围仍待整批交付：App既有main gitlink、两份有效进度文档和本次正式隔离smoke；未直接提交main、未push本批或改他人分支。

Key保存/领取及提供方/模型新增发布表单仍是后续缺口；共享业务语义的确认不自动放行前述独立密钥设计候选。正常System/BFF仍System4组合，不热重载半套契约或隐式改库。

## 2026-10-20 MC-02A 当前交付：System 已验，消费者待配对

用户已明确批准“共享模型配置，业务分别组合”，不是维持业务各复制修订。System在原模块实现无feature共享revision、业务label/routing引用与tenant覆盖、nullable展示别名默认原request_model、实际有效catalog身份、空绑定拒绝全局扫描；无新表、服务或依赖。已本地提交 `b7fe78e25e3c569ae0e1cb9b42cddab02074ca07`，5.0.0 artifact `a83b37269e9e4fa7fb5310a1836975e20ab9eaee965a66c83e35bb1ca1b9e5df`，provenance `97b20e57f66010ba456fac59fe1dd62d90c17325c82d3da80be455ea9d3cf747`。

主会话有效RED→GREEN后最终完整verify全0：contract20、16files214PASS／0SKIP、fresh33／22表catalog精确、format/lint/type/build；共享业务生命周期与tenant隔离真实HTTP/PG通过，库inventory前后相等。独审无确定P0–P2，55非model操作及递归表示保持；只加现合同1／HTTP1用例，原风险fixture定向升级。首轮README摘要与三处fixture错配失败诊断保留，最终通过不抹去失败。

后继按owner精确提交配对BFF Public、业务models列表真实provider投影、Agent固定消费及App/Admin可空别名／共享修订选择，不改他人自动化／连接器。正常组合仍为System4，尚未重载／DDL／push／新PR／merge；Key保存／领取继续是待确认候选，不由共享业务确认自动放行。模型、工具执行、扣费持续暂停。

## 2026-10-20 模型需求澄清记录：业务配置优先于密钥底座

用户明确模型模块服务于“各业务取得自己的模型配置／组合／列表”，provider 统一配置，别名允许、默认原模型名。此答复不是对 MC-02 存储／读取方案的直接批准。前面候选保持设计状态，先完成以下最小语义核对，不按 Key 管理单独宣告模型能力闭环：

1. Provider 一份连接／账户配置供多个模型复用，不是一模型新建一次提供方。
2. 模型目录／精确修订描述实际模型及执行配置；按现 feature/label/tenant routing 承接业务可用集合、默认选择和稳定配置引用。
3. 业务入口按受信 tenant 与其业务上下文取得对应模型列表／默认项；运行方受控解析执行配置，前端不获取 Key，不在各业务复制 provider 配置或硬编码另一份模型列表。
4. 别名为可选展示／业务命名，未设置默认原模型名；不能替代 request_model、作为唯一资源身份或改写历史精确引用。

已读当前 System definition/provider/revision/label/catalog/resolve 的 schema、controller、service/repository 及 canonical SQL，并核 Agent resolve：已有 feature 投影基础，但 revision 绑定 feature、label_key 全局唯一、display_name 必填。须核现结构能否直接承接跨业务复用与默认别名，不把“有过滤参数”等同于完整业务入口授权／交付；只对实际缺口改边界，不先建模型组合平台。Root＋12子仓本轮重新 fetch 均成功且 HEAD 与远端 main 相等，无对方新分支接收；本批特性提交尚未 push/merge。

## 2026-10-20 MC-02 设计门与默认租户核验

已有 App → IAM → BFF 的登录准入自动传递受信租户，后台模型表单不新增 tenant 配置。System 提供方／模型修订保持全局目录，租户路由单独隔离，不按用户输入、Site 或 Project 猜 tenant。此事实已按当前 controller/repository/canonical SQL 复核，不以先前聊天承诺代替源码。

本新增需求的设计候选位于既有 System TECHNICAL_DESIGN/API_CONTRACT/DATA_MODEL 的 MC-02 顶部和 IMPLEMENTATION_PLAN，不在 Root 复制 DTO/Schema。明确：System 原模块受保护凭据存储＋窄模型管理身份＋Agent 内部读取，创建连接与密文同事务，普通投影及未知结果恢复不存 Key，删除 Agent 旧文件解析。新增边界已交用户确认、独立只读审查中；同账户轮换及精确读取／未知查回语义收敛后才实施，不能把候选文档称作已批准机器契约或已完成密钥链。

下一步顺序：收敛上述设计门 → System 原生契约／持久事实 → Agent/BFF 精确消费者 → App/Admin 表单及整链验收 → 本批集中 PR/merge。首页／聊天继续后置；不触对方自动化／连接器，不运行模型、实际工具或扣费。当前未修改正常环境或新建远端 PR。

## 2026-10-20 用户补充：模型连接必须可直接配置地址和 API Key

用户指出正常模型页只读且要求手填 `secret_handle_ref` 不满足产品用途。本批目标改为**完整模型连接配置**：新增连接时直接填写 API base URL、API Key（不假定供应商都使用sk-前缀）、请求模型名；可管理模型修订／发布与路由切换。已有目录／路由页属于已验基础，不再把它当完整模型管理能力或整体完成条件。先完成必要三面设计门和正式API，再实现真实表单，不放演示保存或仅隐藏限制说明。

拟沿现有owner最小收敛：System `model-catalog` 管连接元数据与受保护凭据存储，BFF核正式平台管理员并通过独立窄机器身份管理，Admin是同一Product会话下的输入界面，Agent仅按受控内部契约取得对应凭据；不让BFF写Agent本机文件、不把MCP密钥仓变成公共Secret模块，不新增网关或独立Secret服务。此项取代现部署文件手工配对的产品目标；System旧“只存handle、管理员手工配置Agent文件”是当前实现，不作为新表单已接线的证明。具体credential加密、读取授权、版本／轮换、失败／未知恢复及旧文件退出须在owner三面文档与机器契约先收敛后落码。

秘密只写入服务端受保护存储，不回显原Key、不进URL／日志／浏览器持久记录；配置持久化和修订发布都不调用模型、不发送健康探测或计费请求。更换地址／协议／供应商账户仍创建新连接与精确修订，不让历史运行套用新地址。同账户Key轮换如何绑定当前credential版本须随正式执行消费核对，不靠名称／handle推断账户。

本批尚未建新的远端PR、未push本批提交；System原PR1保持Draft。新要求完成相关验证后再统一PR/merge，不先合只读页冒称完整。自动化／连接器仍不碰，首页／聊天仍在后；模型、实际工具执行、扣费继续暂停。用户允许备份后必要范围清空重建，不实施旧数据兼容或为清空而全库重置。

## 2026-10-20 当前执行批：BFF 正常配对 → System 管理消费 → 首页／聊天

用户已确认此顺序；本方排除自动化与插件／连接器写区，模型、实际工具执行、扣费继续暂停。既有设计不重开方案评审，不新增服务、网关、数据 owner 或计划中心。 用户追加确认clean-slate：不为旧字段、旧协议或旧数据建立兼容读写／fallback；如当前契约确需重建，可在备份和核清影响后清空该必要范围重建，不扩大成全库重置。已兼容当前结构且无额外兼容代码的数据直接保留；历史终态记录不作为新执行authority，也不回填猜测快照。

| 切片 | writer／基线 | 写区与删除项 | 验收／当前状态 |
| --- | --- | --- | --- |
| BFF 正常配对 | 主会话；BFF14 `5dc86e4`／IAM `7cbe988` | 本地受限机器配置、BFF owner 两个已合 nullable 字段；不回填旧 trace，不删旧表或历史行 | 已备份、全32表恢复演练及 canonical 必需列形状核对；冻结后定向补两列并快进正常源码，BFF/IAM ready200；正常403/404、IAM正式reader缺绑定返回null；32表原行hash完全保留；浏览器刷新保持登录并回读历史。正向执行仅已有隔离证据，正常执行仍暂停。 |
| System4 与 BFF 配对 | BFF独立 writer；System Draft1 `dafbc66`／BFF main `5dc86e4` | 只换System4固定artifact、严格revision投影及公开major；保留现四操作闭集，不扩大成provider/revision写入口；删除旧transport/gateway投影，不加兼容union。BFF三面文档先收敛。 | 受影响contract与model routing测试；完整相关交付门；非模型消费者无协议变化。System正常旧行先只读盘点；非空旧修订不猜地址／改digest。 |
| 后台模型页正式接线 | 主会话；Admin `f2fac30`／App `859f415` | 独立标签／修订只读详情与路由策略编辑组件；替换models legacy ResourceTable及仅模型旧表单；现有Product会话、正式四操作、同一幂等键和CAS。App只改模型精确allowlist及CAS头，Admin只改模型校验／错误／页，保留Skills/MCP原行为。 | 无模型创建发布UI承诺；未知结果不盲发新key；读回／冲突／同主体恢复与跨主体清退，真实adapter链，正常只读目录；模型执行仍暂停。 |

依赖：BFF发布新Public artifact后由主会话配对App/Admin固定consumer，System原Draft复用不重复PR。Root最后按实际交付SHA更新gitlinks；已合版本与正常加载分开记录。资源重载及Git提交、push、PR/merge由主会话串行负责。每个owner一个完整需求PR，集中验收后推送；不因CI付款故障重复push，不把未跑CI写成通过。

## 2026-10-20 后续 TODO：已合批次之外的缺口

本节是下一轮讨论与开工入口；后续在本节更新状态，不另建任务中心。范围是盘点，不构成业务实现、配置激活或执行链放行。最初盘点只读核对记录与源码；随后用户截图触发 T00 当前页面只读实测，已区分确定缺陷与仍待复现项，下列“待复现”不计作已确认缺陷。下方旧时间段仅是历史，已经关闭的事项不重复开工。

### 已关闭，不重复做

- [x] 超长恢复草稿明确反馈，发送边界保持原有 4000 上限。
- [x] 同一页面生命周期内跨 direct/project 切换，保留未回执提交的原 key/body；不自动新建请求。
- [x] 窄屏长输入框不再遮挡项目历史尾行。
- [x] 私有项目链接移除公开访问承诺、假邮箱和未实现邀请。
- [x] App PR #41 / Root PR #57 已合并；本批分支、临时工作区和失效引用已清理，正常服务与原混合工作保留。

交付基线：Root `2de896ce4b5f40718160b253a9b82348431bba16`、App `e189954af6e27116d024b66a75069b8de2c7ab8e`。清理后存在可用于下一轮的干净 main 副本；原占用目录仍有受保护的历史未提交改动，不把它冒称全树 clean。

### 本方漏交付优先收口（T11）

> 下列为发现时的历史状态，不是当前未交付结论。当前 App42 已合并并加载正常3310；正式收据见本节下方及 CURRENT 首节。上面的 e189954 基线也是本批开始前的历史基线。

- [x] **T11 提取并交付原资料库／侧栏修复**：用户判断属实，准确状态不是只有“另一个未 merge 的分支”，而是本方修复仍在原 `apps/kokoro-app` 的 `codex/local-ui-verification` 工作树作为未提交与未跟踪文件保存，既未形成完整交付 commit，也未入 main。10 月 17 日资料库和侧栏记录当时均明确“源码未提交”；正常服务后续切到干净 main，保留 mixed 却遗漏提取该部分，因此相对之前已实测画面倒退。之前“当前文件等 main，所以只是未做”的推断不完整，已纠正。
- **代码仍在**：Library header、独立 artifacts reader 为未跟踪新文件；surface/model/sections/CSS 为本地修改。新版默认产物、个人文件移到查看选项、移除顶层 Tabs 的实现仍可见，main 没有新 header／reader。侧栏三文件仍有缩小菜单／定位、修正项目行多余分隔阴影、统一图标文字起点与 Portal 回焦的未提交修改；不能把用户当前截图都当新需求重新实现。
- **最小后继**：先按既有已验修复、对应测试、文案、返回路由及消费者契约梳理完整依赖闭集；从干净最新 main 提取本方增量，不复制整个 mixed、不碰对方设置分支、不覆盖主线认证／Skills/MCP／聊天修复。先复用旧截图与冻结证据定位差异，再做受影响定向回归和正常页面同态验收；所需 owner 相关交付门通过后集中 PR／merge，Root 最后 pin。重启不是提取／合并的替代方案。
- 本次只有只读源码／历史核查、ignored 源文件与窄补丁留存、当前 TODO 纠偏；尚未迁移代码、切换服务、提交或创建 PR。窄补丁只用于保全，不宣称九个路径就是可直接合并的完整切片。模型、实际工具执行与扣费暂停不变。

### 2026-10-20 T11 正式交付收据及其余保留工作

T11历史段描述的是发现时状态，现已由 App42 合并 `d4b61f9` 承接；正常3310也已fast-forward并真实读取新版，不能再解释为只重启旧代码。知识草稿重新准入与preview组合有回归，完整4316测试/42浏览器旅程和独审通过。BFF13、Scheduler2、Admin3、Mori1已合；Root58最后配对。已合范围不重做，详见CURRENT首节。

其余真正独有的旧提交分列，不混为已完成：
- Library上传deadline `6a443b2`、选后才显示Upload/长文件名 `1b35a7a`、rail重新clamp `4871c2e`：保全候选，尚未完成最新主线复现/提取/验收；下轮局部守卫，不恢复整棵旧UI。
- 项目资源scope/取消/迟到退休 `bf2bee9` 与旧worker/Chromium smoke：聊天/项目后置；旧Skills/Admin callback/trace兼容和浮动旧pins不恢复。
- System4原 `7f479f6` 已发System1 Draft，owner完整verify通过，但BFF Public19/Admin公开投影及正常旧数据未配对。当前System pin仍1460820，不以清分支为由强合破坏性契约。
- BFF `d623f76`/`16da6f0` 独有可信执行绑定producer已从最新main定向承接并合BFF14 `5dc86e4`；Public19/所有当前owner pins/System3/Scheduler旧命令路径保持，schema3不读旧trace当authority。完整contract848/default1496 PASS＋3原资源SKIP、真实隔离PG33 PASS及独审通过；正常字段/outbox/机器配置尚未激活，暂停执行不解除。
- 原混合与detached的39棵worktree均有HEAD、tracked/index及untracked本地恢复快照。清理必须先核恢复与当前写入，另一个开发分支继续排除；不再声称所有本地改动均已合入。

### 外部新增交付仅跟踪，避免误判为运行回滚

- [ ] **T09 对方设置新增交付（仅跟踪）**：远端 `feat/settings-assets-pages` 的 `ed92864` 是原设置 PR #38（head `cc8e040`）合并后新增的提交，尚未进 main，当前没有后续 open PR。新增内容包含账户积分正式读取与设置内页；分支自身记录完整测试／手机项目场景仍有失败，不把“开发已提交”直接算整体验收完成。用户随后明确对方 PR／分支不由本会话处理：本项只记依赖，不接收、改动、代建 PR 或合并，不列为本方开工前置。对方正常发布后再按当前 main 同步；本方 App #41／Root #57 已合事实不变，不直接切换正常运行目录到落后功能分支，也不盲目替换源码或先重启。
- **运行版本核查**：3310 运行进程 的 cwd 是既有独立正常源码副本，HEAD 与远端 main 均为 `e189954`；账户卡与资料库的页面、子件、CSS 字节均等 main，不是误跑原 mixed 主目录。原进程确实未为新增设置提交重启，但因为新提交根本未接入，单纯重启不会升级。
- **资料库纠偏**：只比较 main／对方设置分支，只能证明当前进程与主线一致，不能证明本方此前修复已交付。用户随后指出个人文件页及侧栏截图后，已实际定位原工作区保留的未提交资料库／侧栏修复，见 T11；当前展示相对当时已验页面确有倒退，不再笼统归为“尚未做过整页对齐”。

### 协作同步约定

按用户要求，每轮开工、交接及PR合并前检查Root和全部12子仓远端main；逐仓非递归拉取，只快进，保护现有写区，不自动合入他人的未合分支或覆盖重叠diff。Root精确gitlink随后随本轮正式PR配对，源码最新、组合已验和正常服务已加载分别记录。2026-10-20本次13仓均已与远端main对齐，App43也同步至正常App源码副本；未重启后端或放行实际执行。

### 2026-10-20 双人分工建议（待双方确认，未代为派工）

本次仅整理交接边界。刚只读核实：对方App PR43已于2026-10-20合入main `859f41593da6b70cbba4c64df1a2ad3480b841a6`；其settings分支675b69c已被main完整包含（ahead0/behind1），不是仍有未交付增量。下方T09的ed92864/未发PR是历史，已由此纠正；未修改、代合或接收对方分支。当前Root组合仍pin已验App d4b61f9，正常3310是否加载43本次未检查，不将远端合并冒成运行已更新。

推荐按变化边界，而非把项目／自动化／插件／连接器四块同时全交给一人：

| 负责人建议 | 首批完整需求 | 顺序／边界 |
| --- | --- | --- |
| 本会话 | BFF正常环境配对、System Draft及管理消费接线；首页与聊天主路径；项目主框架／任务往返 | 先收本方既有尾项，再首页／聊天，随后项目主框架。Frame／Composer／导航／会话scope与项目会话紧耦合，暂不两人同时改；不接管对方已合设置源码。 |
| 另一开发者 | 自动化完整旅程；插件目录＋连接器管理／详情完整旅程 | 先自动化：日历／列表、周期、CRUD和同态回读；再插件／连接器作为一个MCP业务域，统一目录、详情、授权／连接／状态与恢复。可端到端修改对应App和既有BFF ScheduledTask或Platform业务，不限于CSS；变更公共机器契约／Schema前协调唯一writer。 |
| 后续明确交接 | 尚未开工的完整切片，例如连接器详情／恢复，或主框架稳定后的项目资源／技能面板 | 本会话先完当前批，再按余量接手。先交接基线SHA、组件写区、已实现／未验／阻塞及测试命令；原writer停写后新writer接手，不在原有写入中抢改。 |

App现有建议写区：自动化为 `src/features/scheduled-tasks/`；插件／连接器为 `src/ui/mcp/` 及对应surface；本会话首页为 `kokoro-welcome*`，会话为thread/composer/frame。项目文件现仍在 `src/features/app/`，不为分工机械建新框架或一口气改目录。公共入口、globals、i18n、API契约、canonical schema、lockfile、Root组合与共享运行进程每批约定一个writer，其余方给明确需求后由该writer集成；正常服务重载不并发操作。

每人一次推进一个完整需求PR；从同步main的新分支开工，不向旧settings分支续叠多个模块。验收包括同视口Manus观察、真实入口／回读／错误恢复及本slice充分测试，末尾集中PR/merge/运行配对。不为分工新增服务、不重做已合能力，不启模型／实际工具／扣费；这只是建议，不代表已给另一个会话发送任务或取得其写区承诺。

### 2026-10-20 补充确认：自动化日历、首页场景与整体能力

用户确认前述剩余项都要完成，并明确加入 `/app/scheduled?tab=calendar` 与 `/app` 的制作简报／建立网站／设计／制作游戏／更多。项目能力只有局部交付，不将已合 PR、入口存在或隔离测试当作全部项目功能已完成。本段是范围和验收清单，不是新增业务方案、接口或本次已完成声明。

| TODO | 当前事实／待核 | 最小闭环与验收 | owner／写区 |
| --- | --- | --- | --- |
| T12 自动化完整旅程 | App已有独立calendar/content/editor/model与daily/weekly/monthly/once模型；现calendar按任务nextRun归日，并非完整未来周期展开。是否应展开重复事件须Manus同态实测，不先新增日历预测器。已有周期代码和历史隔离验证不等于当前正常完整旅程。 | 对照Manus实测日历／列表切换、月份／今天、任务详情与编辑、新建／修改／暂停／恢复／删除及刷新回读；核每周多星期、每月多日期、一次性日期、IANA时区／跨日／夏令时、next和耗尽状态、取消和失败恢复。Scheduler保持通用时间调度，BFF拥有用户任务；Agent定时MCP管理工具核相同权限、幂等和规则，不绕成另一套定时器。正常任务继续暂停，实际到点派发／工具／模型执行验收单独保持未验。 | App现features/scheduled-tasks组件；BFF ScheduledTask及正式Scheduler／Agent消费者，受影响owner各自闭环。 |
| T13 首页场景入口 | 当前已有四场景及creation intent组件，截图按钮存在不证明完整场景。More内容、场景选择后的真实行为、模板／素材来源、退出和草稿保留仍需逐项同态观察；不据标题猜其绑定某个skill或connector。 | 对照Manus实测按钮字体／图标／间距与响应式、hover／focus、More菜单、各场景进入／切换／退出、模板与输入区联动、附件／素材选择、草稿／焦点／返回刷新；核场景选择交给现有会话路径的真实请求与精确能力引用。仅凭UI不推断后端API或专用生成服务；无正式后端的发布／托管等能力明确列缺口，不造成功卡片或演示保存。实际生成、工具、扣费暂停期间不计为执行闭环。 | App KokoroWelcome／DirectWelcomeContent／CreationWorkflowSurface／Composer与现Frame；所需API依现owner正式契约。 |

推进顺序收敛为：本批BFF正常配对与System Draft尾项 → 自动化／首页两独立面核查与分批交付 → 聊天主路径 → 项目工作区。前两UI面可并行只读核查；共享契约、schema、公共入口和计划保持唯一writer，不为了并行机械拆PR。旧上传／缩放局部守卫随对应旅程先复现再提取。

项目T02/T03/T04及资源上传scope/取消/迟到退休仍保留，逐项验项目概览、指令、资源、技能精确版本、任务归属／移动、历史与导航／响应式；未实现、已实现未验、已验三类分别记。不扩大成新网站托管服务，不重写既有调度／聊天引擎。全部模块沿现功能手册补齐“页面→正式API→持久化或状态→刷新回读→失败恢复”的证据；模型、实际工具执行、扣费和他人分支边界不变。

### 下一轮优先：聊天主路径 → 项目工作区

| TODO | 当前证据／状态 | 最小工作与完成条件 | owner／组件 |
| --- | --- | --- | --- |
| T00 已暂停服务的失败语义与布局 | **本次已实际复现**。正常 BFF 进程显式 agent_enabled=false；提交准入将停用与未配置合为 agent_not_configured，前端统一文案却引导检查连接／重试。现窄列动作区为 column＋align-items:center，空 errorBody 仍产生 16px gap，重试居中且可点击。 | 优先修提交不可用说明与恢复动作：配置／停用类错误不冒成临时可重试；提示与动作在阅读列内成组左对齐，移除空占位，窄列只换行不居中漂移。暂停原因的展示必须基于正式可信事实，不在前端硬编码所有 unavailable 都等于暂停；若需新增可用性事实再走 owner 契约门。保留原输入和消息，不隐藏真实错误，不启 Agent 验收。 | App ConversationThread／局部失败反馈子件／thread 样式；BFF 准入错误现状只读，不为本项新增服务。 |
| T01 聊天导航与阅读状态 | **一般导航仍待复现／补验**。四项局部修复不等于完整导航、刷新、滚动矩阵通过；不预判当前仍闪动或串草稿。 | 对照最新 Manus 同态页面及既有 Vercel 职责参考，实测 direct→项目概览→项目会话、前进后退、刷新、长历史、输入焦点和上翻阅读。只修复现问题；局部加载不清空整页，迟到响应不串会话，未知提交不自动补发。刷新后的未确认提交恢复语义先核现有正式链，不默认新增持久化 store。 | App Frame／scope reader／ConversationThread／MessageScroller／Composer；沿用 engine 与 AG-UI。 |
| T02 项目概览和会话布局 | **未完成整页对齐**。正常 manifest 曾未发布 workspace/project 能力，不能靠 preview 截图判正式页面完成。 | 先核正式能力投影和实际入口，再测概览／线程两态、上下文与历史区域、资源／指令／技能、长标题、局部空／错／加载态。390/768/1280 与连续缩放无溢出遮挡；截图、DOM、计算样式和实际读写结果配对，不为展示强开 flag 或虚构能力。 | App KokoroProjectWorkspace／ProjectIdentity／ProjectConversations／上下文子件；投影缺口按 BFF owner 核实。 |
| T03 项目历史分页 | **代码事实已确认，产品语义待定**。ProjectConversations 当前只接列表，没有 hasMore/loadMore；标题为“最近”，因此不直接认定应无限加载。 | 先确定“最近首页＋全部入口”还是“本区继续加载”；确需更多时接既有 reader/controller。跨项目游标隔离、不漏项不重复，加载失败只影响列表；没有必要就不新增后端 API。 | App 项目历史 reader／ProjectConversations，沿已有 BFF 分页契约。 |
| T04 preview 与正式能力边界 | **代码缺口已确认，可达性待验**。项目网站选择仍读 previewWebsites，部分编辑只存组件 state；尚未证明正常 live 暴露该路径。 | 沿实际 capability 判定路径；演示数据和本地模拟保存严格留在 preview，正式入口只展示真实能力和真实结果。保留合法预览用途，不借此实现网站托管／发布服务。 | App 项目 workspace model／能力投影消费／相关对话框。 |

建议下一 PR 只收上述五项中本次确有必要的修复，先收已复现 T00，再按 T01→T02，随项目上下文收 T03/T04；有现成正确行为就验收保留。每个实际修改 owner 一个完整需求 PR，内部允许多个 commit，Root 最后 pin；不是每个 TODO 或组件一个 PR。

### 后置能力，不塞进下一 PR

- [ ] **T05 消息内技能选择**：已有精确 refs 与选择 pill，但斜杠／附件菜单入口尚未完成。主路径稳定后再接真实搜索、键盘选择、移除及显式空选择；项目默认与消息冻结版本保持，不以名称拼提示词代替安装身份，不执行工具。
- [ ] **T06 其他模块剩余对齐与覆盖**：自动化、个性化、资料库、插件保留已交付成果；从已有手册逐页列出未观察／未覆盖的具体状态，再同态补验，不笼统判定整模块未完成或重做。自定义连接器图标上传仍禁用；Device／外部 caller 等全部来源正常旅程没有完整证据，公开目录与受管 ZIP 包也不能代替普通 MCP 连接场景。
- [ ] **T10 插件分类切换反馈**：用户在 `/app/plugins` 点击切换时报告异常；截图显示“开发”已选中、原列表区域呈三块长条骨架占位。证据目前是用户截图与描述，未做新浏览器复现，不断言卡死、重复请求或后端根因。后续核对分类切换是否清空整区、加载／空态尺寸是否跳变、快速切换迟到响应是否覆盖当前分类；对照 Manus 的局部更新与过渡，确认不连贯原因后只做必要修复。此为记录，不自动扩入当前实现或操作对方分支。
- [ ] **T07 实际执行及 Billing 收口**：模型、真实工具执行、扣费继续暂停，不把暂停当故障。既有 MCP OAuth／续期／包生命周期的隔离证据与正常执行证据分列。Billing 最近正常读取有缺账户 404、旧 draft #2 保留；后续先重新核事实与范围，再决定账户／计费闭环，不借本 TODO 开户、充值或改计费链。
- [ ] **T08 功能手册与历史工作归属**：随实际完成更新已有 Manus 观察记录和 Kokoro 已支持／未支持／未验说明，不声称抓齐全站 API。原混合改动及旧 worktree 按归属另行交接，不为 Git 状态好看强删、重置或混入下一需求。

### 开工与验收约束

只拆有独立变化原因的组件；保留现有 owner、AG-UI、消息引擎与唯一滚动实现，不造网关、全局状态层或机械分层。参考采样需真正开工后按页面范围执行，本次不新登录或采集站点。

测试先查现有覆盖，开发时只跑受影响规则与旅程，缺陷只补独有回归；不为文档、组件数量或每次小改重复全仓套件，不为追“少测试”删除有效保障。交付时按受影响 owner 跑必要完整门与实际页面对照，记录未验和暂停项；集中完成后再 push/PR/merge，不手动触发或等待 CI，不把 CI 未运行写成通过。

## 2026-10-19 当前局部修复交付边界

已确认先闭环当前批，不启动下一轮。App PR #41 已合 main `e189954a`；Root 本次只配对这一精确 gitlink，并记录四处已验局部修复，不修改其他 owner/配置/数据。完整4249测试与10浏览器旅程复用冻结树证据，收尾定向123 PASS；无新增测试或功能。

下一轮单独处理项目概览—历史任务—会话往返、现有分页与真实能力呈现；消息内技能选择后置。暂停模型、实际工具和扣费不变，不把参考截图或隔离 preview 冒称真实执行。当前 PR 合并后同步 main、仅清理本方已合 topic 分支，不覆盖占用工作区。

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
