## 2026-11-12 Task B 正式接管：先保成果、再补最小缺口

用户明确将Task B移交本会话主控 `/root`。本节是当前入口，以下历史记录保留各自时间／基线；不重开已交付Task A、不因旧待验表重新实现功能。唯一执行清单是[Root TODO](../../../todo.md)，原功能范围见[Task B交接](../../handoffs/2026-10-30-task-b-capabilities-account.md)。

| 项 | 当前事实／下一动作 | 负责人／写区 |
| --- | --- | --- |
| 原PR与组合 | Root#67原477562a4、App#49 d6dd3cd0、BFF#17 1e6765b3、Capability#12 e068fcaa；主控先合入Rootmain1092d99b，保原14提交／468行记录和12个已验gitlink，不直接激活旧指针。App/BFF有明显主线分叉，须按功能保双方成果 | 主控唯一Git／Root台账／资源；不强推或删除旧worktree |
| Capability已包含成果 | Root pin24094960与#12 e068fcaa源码树相同，后者仅多merge提交；MCP新授权、API隔离和Skills旧“待提交”叙述不能当当前缺功能 | api_perf_audit先只读核验；不重造owner |
| App/BFF承接门 | 原App独有37提交包含MCP/API、账户、Skills和契约；原29.3有201 ops而现28.35有215 ops，另同名operation/schema有实质差异。不得整份旧generated/pin激活；先承接无新契约依赖的API／JSON创建后精确详情，后续由BFF统一发行再生成 | composer_ui_audit只读盘点完成；主控后继集成，不恢复已删除首页预热 |
| Storage#2 | add2da6的fresh成对升级未在现main231bb663承接；现FINAL后继脚本导入旧target常量，不能机械换hash。沿原bootstrap冻结旧工具／旧canonical，核后继parent并补定向PG | app_merge_gate只读盘点完成；原PR保留，主控另交精确写区，不做正常DDL |
| R-07首片 | check仍先generate并改写生成文件。沿现脚本生成到自有临时目录、比较完整集合和字节，显式generate继续写；失败保持原输入并回收自有临时目录。无wire、数据模型或业务运行变化 | api_perf_audit单writer：package／现normalizer与直接contract check／相关测试；已沿原#12推送c040dda8；主控8例／真实check／类型与scope lint/format通过，803输入SHA/mtime/mode不变、四输入冻结核等，独审CLEAR；仅工具片源码已验待合并，不冒全PR验收；候选推进触发Agent发布pin精确配对缺口，Root暂保原12个已验gitlink，不放宽门禁，与B-01消费者窗口一并切换 |
| R-14后继 | singleton client永久origin DNS pin限制合法独立操作轮换。只把pin约束到一次有界OAuth操作，保同操作漂移拒绝／公网验证／实际IP连接／Host／SNI／取消；不清共享Map处理并发 | 局部技术设计／2生产factory＋3测试已验，原#12提交573a8f00；主控17例、types/scope lint-format、五输入核等和独审通过。writer63例仅相关unit，非真实Provider／PG／全默认；源码收口、组合待配对，不改协议／Schema |
| B-01／B-02 | 先固定消费版本／实际加载源；只补新授权刷新删除、冲突／撤权／迟到／秘密边界。已有Docker执行／清理／刷新收据复用，不跑新模型凑证据 | owner→BFF→App按依赖；原PR内交付 |
| 其余功能域 | Skills作者版本／安装使用、账户／Team／Share／模型积分与对应Admin按现收据盘点，仅实现当前缺口；视觉／多语言／性能／文档随片收尾 | composer_ui_audit先只读；主控验收和写区裁决 |

交付：各仓沿原PR，本地受影响风险和相应owner门通过后正常合main、Root固定精确组合并清本轮分支。不部署、不清卷，不引入内部OAuth、重复认证／缓存／SDK或无用层。真实支付继续关闭、完整云E2B沿已接受边界暂存；外部供应商权限缺口只约束对应末端，不伪造成功、不暂停独立工作。2026-11-12用户已明确要求设置Goal，机器目标现active；按唯一TODO及本节持续推进，不以局部通过完成整体目标，不自行暂停。

## 2026-10-29 Custom API 任务隔离主路径已正常生效，整体 Goal 继续

### 2026-10-29 后继：连接器菜单顺序已正常修正

App `fcf395bd00a5778c22e258133ddc299a60fd9f73` 在同一PR46继续交付。Manus首页中文浅色1280×720实测向上仍是“列表→添加→管理”；原记录的向上逆序有误，现共享组件删除方向监听/反转，菜单上下展开都保持列表优先。两份运行源严格核90c07f4前像后HMR，当前3310已生效。实际向上/向下键盘首项与Escape、管理/添加返回原会话及API选择1、390px本地不溢出均已验；参考/实现首页同视口、会话前后截图和DOM测量在ignored `var/dev/connector-menu-parity-20261029/`。参考窄屏未取得，目录数量/类型不同，完整视觉不冒一比一。

主方lint/typecheck/build/diff通过；定向26通过。完整default359文件6894通过，另1个HTTP套件因漏传Redis测试配置失败/2项未运行，补现有受管Redis与独立随机origin/session后原文件8通过；未重跑整套Playwright，保留原失败日志。独审无确定新增缺陷。正常代码及证据已验，未合并main。

- [x] 连接器菜单向上反序及键盘首焦点子项关闭；旧2026-10-28逆序记录仅保留为历史，已被本次实测替代。
- [ ] “＋”资源完整链继续OPEN。本轮Manus实测含Google Drive、OneDrive、Figma、使用技能、最近任务、资料库、本地文件；本地只有真实技能选择，其余无Composer handler/附件发送契约。下一片按已记录Library→BFF任务引用→Agent只读附件链推进，不用项目上传或导航冒充完成。
- [ ] Custom API多项冲突/撤权/取消正常负控、真实E2B、整体加载/其他展示、Skills/首页/项目与计费核对仍按原计划；已验成功主链不重复，Goal ACTIVE。

已批准方案正常生效：Platform `44fcc5da599b4a5cec3077e41aaef4375fe4add2`、IAM `b9a63c533ab95b70a07693190d64bd09791a125b`、Agent HTTP/Worker `c6c8073a31cd2feb2725d0fd70505e9b5140be0a`、BFF `853ca9a5d8da3500b0c37543c72198a520e46225`、App `fcf395bd00a5778c22e258133ddc299a60fd9f73`。BFF 固定 Agent HTTP8.10，App 固定 Public28.17。MCP 原链保持；本次无新 Schema、DDL、历史回填或 Share 暴露。各 owner 沿原 PR 交付，未合并 main，不称完整产品上线结束。

本轮真实主路径：管理页创建无真实凭据的 `QA Task Sandbox 20261029` → 输入菜单独立选择一个 API（两个 MCP 均关闭）→ 创建任务 → Describe/Acquire 实际 HTTP200 → Run 独立 Docker 执行 Python → 环境标记存在、公开 python.org 返回200、工具退出0 → 两次模型调用完成 → Run终态 → 容器已删除、持久清理记录 completed → 硬刷新恢复 API选择1。safe refs、dispatch、journal和公开事件未出现本轮标记值；这不是任意编码/网络/文件外泄的绝对保证。新建配置及 QA 会话保留，不删除旧样本。

成功前第一次模型网关返回用户并发超限，Run失败及未知用量原样保留；随后显式再生成成功，没有伪造成功或将未知费用补零。成功轮两条模型用量均 normalized、已收到财务确认，但分类仍 partial；本片不宣称缓存成本和整套账本最终核对完成。

浏览器继续暴露的 execute 详情缺项已修：Agent 原白名单仅 State 文件/MCP。现在冻结全部 peer 的 Docker/E2B资格并排除人工改写，再精确比对同 Run typed call/result、activity和持久journal，复用既有2048/4096字节脱敏预览；不新建API、不重跑模型、不改旧历史。正常页面刷新→展开处理过程→点击原成功动作，实际命令、HTTP200与退出码0均可见；本次空详情子项关闭。文件/产物秘密边界、其它工具展示和完整Manus视觉/交互仍按原计划开放。

主方最终验证：Agent默认3336通过/934资源marker未选，Ruff格式/lint、Pyright、contract、wheel/sdist通过；独立真实PostgreSQL RunDisplay28通过（含execute、错Run、journal不匹配、原文件无关journal预算），仅自有测试库已回收。Docker删除非零旧缺陷修正为同daemon确认不存在才幂等成功，否则保留持久重试；负控先3失败→68定向通过，真实Docker已不存在场景通过，独审无新增确定缺陷。前置App6896、BFF2306/3条件跳过＋真实PG10、IAM完整verify1554及Platform2920/1既存超时的证据绑定原owner提交，未将跳过或超时称通过。

激活踩坑与修复：匿名探测Agent `/readyz`返回401被误判，首次回滚又因同检查停止，导致Worker/BFF短暂未启动。已按原cwd/argv/env恢复全部服务并确认一致；修正为使用既有服务身份检查就绪，回滚逐个恢复全部已停止owner。重新配对激活、两次后继精确源码加载均通过；未降低认证、重置卷或改凭据。IAM先整合正常6238371已部署的direct身份链再上线，避免候选547回退既有认证。

本地ignored证据位于 `var/dev/custom-api-runtime-20261028/`：`api-selection-restored-20261029.png`、`api-execute-details-20261029.png`、`manus-connector-menu-20261029.png`；activation目录保留成功/失败/恢复及权威回读收据。Manus参考为已有项目菜单，本地为QA会话菜单，视口和页面不同，只支持交互事实与差异定位，不宣称像素一致。菜单顺序/密度、加载中间态、“＋”资源和全局性能目标未关闭。

- [x] Custom API配置保存、独立选择、safe refs冻结、真实Describe/Acquire、隔离脚本执行、终态清理和刷新恢复。
- [x] execute成功动作只读输入输出详情，正常页面已回读。
- [x] 保留已部署IAM认证链，修复激活检查及Docker清理失败误结案。
- [ ] 多配置冲突/撤权/取消的正常整链负控；现有代码与隔离证据不冒充全部产品实测。
- [ ] 完整Manus菜单与“＋”资源、其它Agent展示/加载、Skills/首页/项目及剩余整体目标；沿本唯一计划继续，Goal ACTIVE。

## 2026-10-29 Custom API 隔离执行基础片已提交，产品链仍 OPEN

固定组合候选：Platform44fcc5da599b4a5cec3077e41aaef4375fe4add2（PR12）、IAM547b05c9d49743c86c30f40c514082106135bebe（draft PR5）、Agent49f188d1aac915b6cd213adf17b59587785cd8b4（PR46）。均已非递归fetch核对main/原PR分支后提交推送；无强推、合并、DDL、正常服务重启或真实凭据调用。

主控最终证据：IAM完整verify/default1535通过；Agent停写后default3251通过/931资源marker未选、focused164通过/8未选，Ruff/格式/type/contract/正规生成/lock/wheel/sdist通过。真实Docker两次fresh acquire＋原值脱敏＋未选下次不继承通过，专属限额容器已清理；E2B仍仅SDK替身。Platform真实本机HTTP与材料边界46通过，IAM/PG在该测试中是替身；初始owner全门2920/1超时及单文件24通过记录保留，不改称全绿。最终日志为本机/tmp/kokoro-custom-api-*，不提交日志/密钥/机器状态。

下一完整业务切片明确为Agent Run safe refs/受信隔离装配→BFF原dispatch冻结/恢复→App真实API选择→正常整链＋Manus同状态对照。当前没有修改正常页面的API开关，因此不宣称用户已经看到效果；不重复做本基础片，不把工程通过当作MCP产品闭环。其余Goal与“＋”资源缺口保持原状态。

## 2026-10-28 自定义 API 任务隔离沙箱（用户已批准，实施中）

用户明确选择“采用任务隔离沙箱方案”。不做通用 HTTP 代理，不把 API profile 伪装成 MCP Connection，不切普通会话到宿主 shell。

- Platform（实际 `apps/kokoro-capability`）唯一拥有说明及加密环境变量；复用当前 schema/加密/read transaction，新增独立运行 RPC：安全描述与每次 execute 的短期材料读取。请求为多 profile 的精确 ID/version，绑定 request/工具调用、受信 tenant/actor/subject/run/session。重复 profile、重复或运行时保留 env 名直接拒绝，不静默覆盖；只读不生成新的密钥库或配置副本。
- IAM 复用现授权策略/在线 proof 校验，只增加固定 Platform operation artifact 的正式消费及生成常量；未知操作保持拒绝，不旁路服务/成员/执行资格。
- Agent 使用真正隔离 Docker/E2B backend。每次 execute 在线重验并取值，resume 重新获取；凭据只在短生命周期 runtime/子进程环境，不放 prompt、command、冻结 dispatch 或全局 os.environ，不写 .env。输出在返回模型/journal/trace 前脱敏；文件读取/产物路径亦需处理。对模型任意脚本不承诺防止编码外泄，这是用户已知的保障边界。
- App/BFF 仅传 safe profile refs，BFF 冻结在原 dispatch；本轮选择、刷新恢复、清空/新会话保持已批准语义。MCP 与 API 在菜单复用展示组件，真实身份与执行链分开。多项同名 env 冲突明确失败，不人为限制成单项。
- 无新表/列/DDL。先 owner machine contract＋最小实现→固定 artifact/消费者→正常配对激活→真实同会话调用及刷新。未接好前不显示假可执行开关，不启用宿主执行。回退旧程序/功能暴露，保留已有配置和历史。

写区：主方唯一 Git/集成 writer；只读 reviewer 核 IAM 授权与 Agent 沙箱边界。当前阶段未激活、未读取真实密钥、未执行模型。完成证据必须覆盖跨账号、撤销/版本漂移、取消/迟到结果清理、多项冲突、输出脱敏及真实沙箱成功，单测不等于整链完成。

- [x] 用户方案批准，现有 owner/执行缺口核实。
- [x] Platform 运行契约与读取/复核源码、敏感材料生命周期及真实本机HTTP验证；固定44fcc5d已推PR12。真实IAM/PG整链另列，不冒充本项已验。
- [x] IAM 固定操作artifact消费及原在线权限策略；547b05c已推draft PR5，主方完整verify通过。
- [x] Agent Docker/E2B单次环境adapter及固定Platform客户端候选；真实Docker成功/原值脱敏/不继承已验，E2B仅SDK替身。
- [x] Agent Run safe refs冻结、fresh lease绑定、Describe说明装配与隔离backend统一选择/回收；fbdfd22已交付，正常环境整链另验。
- [x] BFF safe refs选择冻结/会话恢复，853ca9a固定正式Agent8.10并发布Public28.17；独立真实PG已验。
- [x] App正式消费、独立MCP/API会话恢复与统一菜单，90c07f48已交付；正常页面效果另验。
- [ ] 正常环境端到端及 PR 精确交付；“＋”资源链继续保留独立 OPEN。

### 2026-10-29 续接边界（不重做已验片）

Platform44fcc5d已推PR12；IAM547b05c已推draft PR5。后继按依赖继续：Agent仅在选中API时由受信Feature选择已配置Docker/E2B，ordinary general仍state；build/static recipe/backend_for必须共用同一派生结果。沙箱必须使用Run级目录，不能继续共享namespace:session_id的可写workspace；同Run恢复走既有sandbox CAS。Describe说明/env名称是用户配置数据，不是系统authority，Acquire原值不进入prompt/recipe/checkpoint。

BFF不新增Platform调用或表：现本人CustomAPI读已返回profile_id/state_version；在原message-create-input→agent-dispatch→HTTP-wire冻结selected_custom_api_profiles，沿既有outbox JSON和composer-selection原normal用户dispatch恢复。Agent正式safe-ref契约先交付，BFF再固定消费；然后App统一菜单。不得只添加开关或用profile ID冒充MCP connection ID。完整端到端、文件/产物秘密边界、正常配对激活仍未验。

### 本轮实际进展（候选，未启用正常页面）

Platform 已实现独立 Describe/Acquire 运行 RPC、严格 JSON/protobuf 边界、默认关闭 surface、当前本人多 profile 精确版本读取、返回前二次执行授权/材料复核及取消/序列化后清零；无 Schema 改动。独立 owner artifact v1.0.0 已正规生成，旧主 descriptor 与历史固定父未改，只在其编译闭包排除新独立 proto。IAM547b05c已消费固定新操作；Agent固定client候选及BFF/App发送消费继续，不称整链完成。

主方复验：相关 46 例通过（含真实本机 HTTP JSON/protobuf；IAM/持久层明确替身），typecheck/full lint/build/format/schema/contract通过。owner unit/contract/architecture 合计 2920 通过、1 个既有重型子进程负控因并发 ETIMEDOUT；保持断言/超时不变，原文件单独复跑 24 通过。并发阶段统计不冒充最终整套全绿，完整真实 IAM/PG 链及消费者尚待。

Agent 已实现 Docker/E2B 每次 execute 的 environment provider、并发局部 SecretStr 快照、无值 argv 注入、有限原文输出脱敏、共享绝对预算和取消线程归属；默认 provider=None 不变。主方重跑 sandbox/profile 114 通过、8 按原 marker 未选，六文件 Ruff/类型检查通过。真实 Docker 使用既有镜像、独立临时容器、无网络/0.25 CPU/64MiB/32 PIDs：两次 acquire+执行+原值脱敏通过，下一次无配置执行无 env 继承，容器已清理。未执行模型或外部 API，E2B 仅 SDK 接线测试；factory/Run/契约尚未接 provider，文件/产物处理及完整执行联动仍需后续验收。

踩坑记录：①只封 PATH/代理不足，NODE_/OPENSSL_/SSLKEYLOGFILE 会改变 TLS/运行边界，现两端拒绝；②protobuf 会折叠重复 singular，须解码前检查原始 tag，已加真实 HTTP 负控；③Docker CLI 不能继承整个 worker env，也不能遗漏现 context，现只接显式 HOME/Docker 配置；④provider 复用可变 SecretStr 会让在途脱敏漏旧值，现每次复制快照。原文脱敏不宣称防任意编码/网络/文件外传。

下一步：提交固定 owner artifact → IAM 编译期操作目录消费 → Agent 当前 Run/lease 绑定 provider及隔离 backend装配 → BFF/App safe refs冻结/恢复/菜单 → 配对激活后实际 API 调用和页面对照。“＋”资源仍独立 OPEN，Goal 保持 ACTIVE。

## 2026-10-28 MCP 输入菜单／已发送选择：正常页面已生效，资源入口仍 OPEN

本次不是仅改候选：BFF `b1233d90403bd69e32998ccc8f71236213c28964` 已提交并推送原 PR17；App `fc57840150c4fba3fde7c0fd830f0585cc2176c4` 已推原PR46，消费正式 Public28.16 artifact，SHA256 `82485c2b7be17ad04f56d3656a58b42ea8d308c9dc22db5807a09ab706418a77`。先部署兼容 App reader（14份精确前像核验源），再仅重载 BFF53714；Agent／worker／App进程不变，无DDL、历史回填、连接或模型执行。私有 snapshot 只投影最新普通用户消息的精确冻结选择，不与账号已添加列表或工具调用次数混同。

正常3310原 conv6530：刷新 DeepWiki ON／Context7 OFF，未发送手动清空后刷新恢复原已发送1项；管理→关闭保留会话和选中；新建任务0项，再重开原会话1项。向上菜单为管理→添加→连接列表，200px容器最小高度取代列表硬撑120px；键盘 Return聚焦管理，Escape回触发器。截图和激活前像在 physicalRoot ignored `var/dev/mcp-selection-continuity-20261028/`。本轮参考1280×720、本地最初665×767／最终758×767，故只证明实际顺序／行为修复，不冒称同视口完整像素等价。

独审发现并已修两条竞态：新发送冻结选择时退休旧候选（迟到目录不覆盖新空选）；每个恢复候选独立目录scope（跨会话不沿用过期可用性）。7条恢复行为、连接器合计26、engine相关509、完整contract443通过；Node22完整typecheck、ESLint、build通过。完整default：356文件6875通过，1个stored-session套件因缺少KOKORO_TEST_REDIS_URL而失败／2例跳过；补入既有受管Redis，用随机origin＋session UUID隔离键重跑原HTTP套件8通过，未删断言或跳过失败。architecture50通过；未重跑整套Playwright，测试通过不替代上述真实页面验收。

仍未完成：自定义API选择／执行链（当前仅MCP Connection真实可执行）；「＋」本地文件／资料库／最近任务与外部来源。只读已确认发送契约、冻结dispatch、Agent RunInput均没有附件引用；Storage也没有授予Agent读取个人文件权限。后续按既有Library存储＋BFF运行绑定读取＋Agent只读附件mount设计，不新造存储，不把按钮导航或假选中当成模型已读。整体连接器及Goal继续ACTIVE，未标全部完成。

## 2026-10-28 分享链接误报失效与打开即发布（局部正常修复）

用户给出的原分享链接 GET 实际200，正式响应为 `{data,meta}`；Web页却用裸snapshot parser，catch又把协议/网络错误全当404，误称撤销/删除。现按既有Public28.15严格解析envelope，只将404归不可用，其他失败中性单句，不新增重试卡、不放宽私有过程字段、不新建分享。正常3310原链接刷新已显示真实问答、只读且无输入框。

Manus实测当前任务分享面板：打开不发布，私有/公开选项，400px面板/16px圆角/32px操作。Kokoro已将open与创建分离，显式“立即分享”才POST；关闭保留本实例已知链接，撤销仍二次确认。调整标题、权限说明、图标/操作层级及窄屏边界，删除重复CSS声明，不虚构协作或未经读取的“仅自己”状态。现BFF接口没有按会话GET分享metadata；刷新后权限状态读取及完整权限管理仍OPEN，此次不冒称Manus全等价。

先RED确认有效envelope被拒与错误误分类、打开即创建；最终3文件48行为回归通过，含创建中关闭、切会话后旧回执、复制/撤销及公开拒绝私有字段。受影响ESLint、完整typecheck、diff通过；未跑完整default/build/整套E2E，独审无确定P0–P2。以App b131894d为源码基线，6份运行源严格核HEAD前像/备份后HMR，无重启/DDL/分享创建或撤销。真实浏览器原分享恢复、打开面板、Escape回焦已验；复制/撤销只走行为回归，未改变用户现有公开范围。原始参考/截图/逐文件SHA和回退保physicalRoot ignored `var/dev/mcp-selection-continuity-20261028/share-fix/`。代码未提交，旧语音切片与BFF选择恢复候选保留；整体Goal ACTIVE。

## 2026-10-28 用户截图：重复过程披露已修复并正常刷新验证

App `b131894d602b883e51197e64c0af3512019515f8` 已推原PR46，未合并。用户新图明确指出“处理过程”内又套“工具调用3次”；主方纠正先前仅修计数的不足。有效整轮sections且唯一无正文活动passage由外层独占披露，内层direct保持原force-mounted行和身份，不写展开偏好；多段真实正文/live/无final证明不改。混合摘要另恢复准备次数，覆盖所有活动而非仅3调用。

正常3310仅3源核bc29a119前像后HMR，无重启/DDL/历史改写；原conv6530展开及刷新重开均只有一个“处理过程”标题，11原活动/4失败与独立final保持，Return收起正确。旧2消息全行摘要不变。原图、Manus参考、展开和刷新截图、3源回退归physicalRoot ignored single-process-disclosure-20261028。

实际RED：摘要4失败，重复披露1失败；修后focused50、170文件UI/core3436、lint/typecheck/build/diff通过；独审无确定P0–P2。全default/contract/architecture/整套Playwright未重跑，移动端390/coarse未验，不冒称整站等价完成。关闭本次重复披露和摘要漏计缺陷；历史自然语言action_title/公开阶段正文不造，新任务语义及其余Goal保留。

### 当前切片：已发送 MCP 选择恢复（用户已确认，2026-10-28）

Manus 实测未发送开关 ON→刷新 OFF，提示下条消息生效；已加载公开前端表明会话 state/本人 user 事件为恢复基线，temporary override 只作用于草稿。证据在 physicalRoot ignored `var/dev/mcp-selection-continuity-20261028/`，不冒充后端源码或已发送行为实测。用户随后明确确认：按会话恢复已发送选择，未发送改动不保存，新会话不继承，停用/失效项不自动启用。

设计：BFF 是已发送消息事实 owner；在既有私有 snapshot 投影 `composer_selection {source_message_id, selected_mcp_connection_ids}`。同一个读事务，取最新普通 user Message（非 regeneration_input），再精确绑定同 tenant/owner/subject/Run/Message 的冻结 dispatch。没有来源或不匹配则省略，不回退更老非空项、不从 tool trace 推断。既有省略与 [] 都代表该次未带 MCP，因此恢复 [] 而非继承；不改变 POST digest/重试/执行授权。新字段不进 Share，不公开 payload。无新表、列、偏好服务或浏览器持久缓存；回退恢复旧 reader，历史不写。

唯一 writer：主方先 BFF，正式 commit/digest 后 App；两只读子代理负责事实与独审，不并行改共享入口。

- [x] 参考行为、当前 owner 存写/读缺口与用户规则确认。
- [x] BFF Public28.16 私有字段、精确父契约保护、snapshot 有界读取；最新空、再生成、缺失/坏来源、跨主体/项目与真实隔离PG已验，b1233d9正常生效。
- [x] App 固定正式artifact；按主体/会话恢复，保护晚回执／手选／新发送及unknown原body/key，重新核验当前可用性；不增加加载／异常面板。
- [x] 正常配对激活、原会话刷新／重开／未发送清空／管理返回／新会话浏览器验收；无历史写入。已发送空选、停用／跨账号用隔离行为验证，不冒称修改过正常配置。PR与其余差异见最新记录，整体Goal未关闭。

### 2026-10-28 补充：输入框菜单与管理面板的能力不一致（重新打开，非仅数量口径）

用户再次截图后，主方实测 Manus 同一会话的连接器菜单→管理→11231 详情：11231 在菜单可开关，详情为“编辑自定义 API”。因此本地管理4个 API而输入框仅2个 MCP Connection，不应被解释为所有功能均正确的过滤；现 `use-composer-connections.ts` 只读 `listMcpConnections/getMcpConnector`，确定漏接自定义 API 候选。API 执行链是否已有完整支持由只读 owner 审核，未验证前不添加假可执行开关、不将 profile ID 冒充 connection ID。

本地管理11项=4API+7未撤销MCP（2可用、5pending）；后台另18revoked历史。此会话已发送DeepWiki1项、当前选择0是另一独立连续性缺陷。四个数量分开记录，前述“1个”不代表账号总数。

Manus 当前实测菜单向上展开时，容器及操作区均 column-reverse，管理/添加位于上方；本地固定列表→底部添加/管理，方向错误。参考容器 min200/max400px、行36px、圆角12px；本地把min120px放在列表，2行撑出空白。参考自身有最小高度，后续不以盲删全部留白代替测量对齐。参考还有内置与可连接目录项；不复制虚构provider或将不可用项自动启用。

- [x] 同会话参考菜单/管理/API详情、计算样式与本地源码核对；原截图归 physicalRoot ignored mcp-selection-continuity-20261028。
- [ ] App菜单补齐正式自定义API候选与统一身份/名称/图标映射；先确认后端选择和执行契约，不仅补外观。
- [ ] App菜单按实际弹出方向调整操作顺序、滚动与容器高度；核窄屏、键盘和焦点。
- [ ] BFF/Agent/Platform核API选择→发送冻结→授权执行→会话恢复链；跨owner设计沿现边界，不建第二套偏好事实。
- [ ] 实测菜单选择、管理返回、发送、刷新、清空、新会话与失效项；与上面的MCP恢复共同验收，整体连接器仍OPEN。

此次仅核验和更新有效计划，没有改变正常应用代码、开关、配置、凭据或执行模型。先前基础CRUD阶段完成不等于连接器执行/选择整项完成。

### 2026-10-28 补充：加号资源入口错误复用技能菜单（OPEN）

用户新图本地加号展开只有“技能”。实测当前 Manus 相同会话加号菜单包含：本地文件、创作、资料库、最近的任务、使用技能、Google Drive、OneDrive、Figma；这是加号菜单，不与此前观察的斜杠命令菜单混同。只观察，没有上传、授权或执行。

源码定位：App `app-frame-composer.tsx` 在 resources OR skills 能力可见时挂载 `ComposerSkillsMenu`；该组件 root 硬编码唯一技能行，将加号和 slash 都接进同一技能根菜单，且 available 依赖 skills。不是本次加载失败或账号少了文件，而是资源入口尚未实现。Skill picker 本身应复用，但不能代替资源菜单容器。资源功能与 skills 权限应独立。

- [x] 正常页面复现、参考加号实测、源码根因定位；截图存 physicalRoot ignored mcp-selection-continuity-20261028/{manus-plus-menu,local-plus-menu}.png。
- [ ] App按已观察的资源菜单/技能子菜单分责，保留独立组件及回焦；不让通用资源依赖 skills 准入。
- [ ] 逐入口核现有owner能力，补本地文件/资料库/任务上下文的真实选择→发送→Agent使用；外部来源未接通不制作假按钮，不凭项目上传已实现声称会话附件可用。
- [ ] 核加号/斜杠不同菜单、悬停/点击子菜单、键盘、窄屏碰撞、选中项与取消/刷新恢复；最终附正常页面对照。

关联前一项API菜单缺口：只读owner审查已确认现Agent手写运行源无Custom API执行路径，RunRequest仅MCP IDs；BFF CustomApiConnectClient.execute实际为CRUD五分支。故API菜单不只是前端列表漏接，执行与授权契约仍待设计实现。此处无业务代码修改，不把记录算修复完成。

## 2026-10-28 语音输入误启演示文本（局部已修，真实语音仍待验）

正常3310点击麦克风、没有说话，约840ms后自动写入“请帮我整理今天的工作重点”。根因：AppFrameComposer 把非production环境视为preview。改为只接受显式preview；正常开发会话沿真实SpeechRecognition路径，不再自动合成演示转写。没有新增服务、契约、存储或权限。

新增真实组件层行为回归：development+preview=false不得改变原草稿/自动提交；显式preview仍可演示。先RED（固定句污染草稿）后focused4文件112通过，受影响ESLint、完整typecheck及diff通过。未跑全default/build/E2E，不冒真实麦克风/转写已验。

以App b131894d为基线，仅1份运行源逐字前像核对后HMR；前像及SHA回执归physicalRoot ignored mcp-selection-continuity-20261028/voice-*。本轮复现插入的演示文字已清除，原空草稿恢复，未发送消息或录音。真实语音权限、浏览器支持、可见状态和Manus录音交互仍OPEN；源码/测试未提交。

## 2026-10-28 旧会话最终答复只读证明已正常激活（局部闭环）

交付组合：App `bc29a119e5eef1a0100e72ff55345360d09d6397`／BFF `38b942742574bccb12d58546301ee0c7cf4014c3`／Agent HTTP `b80d68337c6643992cc2920aa18c70d9cc783488`，均已推原 PR（App46/BFF17/Agent46），未合并、不提升Root gitlink。正式契约 AgentHTTP8.9 → BFFPublic28.15 → App精确消费；原生终态有界只读证明由BFF自有消息parts/revision绑定，只影响视图，不伪写历史final或公开阶段正文。

按用户批准范围 reader-first 加载10份App运行源→BFF→AgentHTTP；前后核无在途Run/dispatch。nullable列已current，未重复DDL；执行worker与App进程不变。首次prepare因运行目录INDEX.md落后而安全退出、零激活；确认仅文档差异后排除非运行Markdown，全部实际运行源前像严格相等才激活。前像、归档、回退程序/环境及新日志留physicalRoot ignored `var/dev/native-final-20261028/activation/`，凭据不入Git。

正常3310原conv6530实测：刷新默认只见“处理过程”收起入口及独立最终答复；展开保留11项活动及4项真实失败，失败ask_wiki_question仍能打开详情；关闭动效结束回同一活动，Return可收起；再次刷新仍保持独立答复。旧2条BFF消息全行SHA前后完全相同，未回填。参考、前/后、展开及刷新截图归同ignored证据目录。AgentHTTP当前观察43次200，无ERROR/Traceback；BFFready200，日志无错误，但未配置请求日志，不能据此声称所有后端接口无错。

实际验证：App完整默认355文件/6855测试、build、lint/typecheck、contract443、architecture50通过；开发者文档check全过（52测试、193操作）。初次全默认缺Redis/既有Radix错误保留，未删断言；配置现有受管Redis随机独立fixture后全默认重跑通过并只清自有键。BFF默认2290通过/3资源跳过，新增focused108、契约1325、architecture36、真实PG19及lint/types/build通过；Agent默认3156通过/931未选择、真实PG26及Ruff/Pyright/lock/build通过。所有pass范围各自限定，不冒全仓/上线验收。

剩余OPEN：展开仍是8项准备+3项调用且摘要仅写3次，操作语义/分组与Manus未完全对齐；旧记录缺公开阶段正文与action_title，禁止伪造补齐。Manus参考为另一种工具任务，仅证明层级节奏，不证明同MCP像素一致；移动端、本次真实在途网络取消、Swarm与其余整体Goal继续OPEN。此次关闭“旧成功轮缺final绑定导致无法整轮收起”的具体缺陷，不宣称全部Manus展示或整体产品完成。

## 2026-10-28 动作详情关闭回焦已正常修复（局部）

App `1166047a` 已推原 Draft PR46，未合并；正常两源与提交逐字一致，Root gitlink未提升。

根因：依赖打开时的 ambient focus／最后一个 Canvas opener，pointer 打开和主区域 DOM 替换后会落 WebArea 或跳到同名其它动作。ToolCallRow 提供 exact activity identity；ContextPanel 在退出后重新解析当前 shell 内同一可见动作，不选择 hidden/inert/disabled／Canvas 自身；原动作已隐藏时落 composer/sidebar，不回到无关旧按钮。文件/产物原回焦路径保留。无 API、数据模型或历史修改。

正常3310两份源码核基线后备份/HMR：新 conv3eb 动作和旧 conv6530 的失败 ask_wiki_question 均关闭后回同一 activity，Return 可重新打开该条，原失败状态及最终文字不变。五个回归场景包含 pointer、切换、节点替换、隐藏及旧无关焦点；独审先发现后者，已实际 RED 后修复。旧手写 A/B fixture 补实际行 identity，原 focus 断言保持。原始证据及回退在Root ignored `display-rework/activity-focus-20261028/`。最终相关5文件112项通过、lint/typecheck与diff检查通过；未重跑全默认/build/全E2E。此项不关闭旧MCP整轮语义、阶段正文、真实网络取消或整体Manus对齐。

### 当前旧会话验收仍未通过（同轮复核）

最新用户严重差异反馈已再次实屏核对（非修复）：正常 App1166047a 仍是“工具调用3次”展开11项；Manus参考是整轮披露、真实公开阶段正文、相邻动作组和独立答复。当前旧记录8条准备与3条调用同权平铺；源码process-summary删除混合组的准备计数，导致摘要与展开的覆盖范围不一致。assistantIdentity已有DOM但CSS明确隐藏；这与参考的回答身份标识不同。缺阶段正文/action_title及final binding仍是事实缺口，不能拿CSS变更解决。原图已归physical Root ignored display-rework/severe-mismatch-20261028；仅结构参考，非同一MCP任务。当前验收保持未通过，不改失败、不补旧正文、不宣称新任务成功等于旧样本修复。

正常 conv6530 与 Manus 指定参考再次以1280×720归档：旧会话仍为11条平铺技术记录，缺原始 action_title／公开阶段正文及已发布 final binding；新任务通过不代替此项。独审确认前端 completedTurnSections 正确拒绝缺绑定旧记录，能力description不能冒调用目的。未采纳再次更换“执行记录”等标签作为结构闭环，未伪造历史内容；正式owner旁读final证明仍待设计审查，现有全thread扫描审计脚本不进入产品HTTP。Canvas精确回焦已单独关闭。

性能独立只读排查发现：BFF projector 对所有active conversation的consumer默认每秒轮询，page exhausted仍active；正常日志快照15671 business GET200／980秒。日志未含path/source，尚未证实全部来自projector。后继已按request_id前缀核因并完成BFF10fe197正常局部修复：20个闲置终态会话，独立60秒窗projector GET200由960降至40（-95.83%）；消费者仍active、晚到事件继续读取、新提交唤醒。证据见physical Root ignored agui-idle-20261028，完整验证归BFF CURRENT。这不关闭当前展示问题。

## 2026-10-28 整轮展示首次正常配对生效（局部闭环，旧 MCP 仍 OPEN）

正常运行组合已切换到 App e7b93c7e、BFF 15cc9e1、Agent 2e61b85／DeepAgents 0.6.7。BFF具名final演进先check确认update_required，apply=updated（50ms）后check=current（40ms）；仅nullable列及canonical约束，无旧历史回填或列删除。原BFF、worker、HTTP优雅退出前后核Agent未终态与BFF待派发均0，原代码/env保留；reader-first启动正常健康。App882份src与提交归档逐字一致。Admin3320已无监听，不在本次切换范围，没有为此重启或修改其它owner。

真实新任务conv_3eb91a9b（仅只读ls，不读文件内容/外网/写入/派生）已正常完成：展开为公开进展正文→具名目录动作，收起只保留最终答复，硬刷新和再次展开仍一致；详情显示真实ls、路径/和原输出。Agent/BFF各自只读核final派生身份一致，parts revision42为87字节正文→单活动→54字节final，final恰1次，正文与owner逐字相等。2模型attempt均sealed，unknown0；input15603/output76，completeness=partial，未冒完整账本验收。此次为真实模型调用，非组件模拟。

仍OPEN：旧conv6530缺原始进展/最终标识，不能据新任务通过宣称已修；新MCP多步与Swarm正常模型整链尚未验；Canvas关闭回焦仍落WebArea；Agent HTTP正常日志短窗口出现大量business GET200，未定位来源，不宣称接口性能达标。原始对照、35份App前像、私有配置、schema回执和正常截图仅保physicalRoot ignored `display-rework/whole-turn-normal-20261028/`。独立候选默认3151通过／930资源marker未选，安装打包及静态验证通过；新增Swarm接线已提交2e61b85并推原Agent Draft PR46。完整Goal ACTIVE，未合并、未更新Root gitlink。

## 2026-10-28 最新实屏反馈：展示不合格，当前优先闭合此项

当前交付判断：**OPEN，不以结果可读、标题字段接通或工程通过代替展示验收。** 本轮从正常 App383486b3 重看原会话，并实际展开 Manus 准备阶段、点击行动和技术详情。两端同为1280×720；参考为Webdev任务，不冒充相同DeepWiki/MCP任务。

### 2026-10-28 展示读取恢复已实际修复，整轮结构继续OPEN

交付App `e7b93c7e`，原Draft PR46已推送未合并；正常仅13源HMR。

- [x] 正常3310运行目录已由监听进程核实；13份目标源码与候选HEAD基线逐字相同后备份/HMR，不覆盖别人的差异。
- [x] useRunDisplay已有facts的终态补读被卸载取消后，解除spent占用；重入共享一次读取，晚回执不覆盖新事实，原HTTP失败不自动循环。
- [x] 主行/Canvas统一MCP“调用已结束”，不把旧completed当业务成功；原四项失败与原件保持。
- [x] 新增先红后绿，扩大UI3251、最终相关104、lint/types/build/posttypes通过；同会话成功/失败详情切换已正常实看。
- [ ] 正常在途取消网络的浏览器故障注入、Canvas关闭回焦（当前落WebArea）、整轮过程/阶段层级及旧final绑定仍未闭环。

证据在physical Root ignored `display-rework/display-read-recovery-20261028/`；无新模型调用、业务写入或DDL。此项不替代用户要求的结构性对齐。

### 当前优先级纠正：整轮过程层缺失（用户指定参考，2026-10-28）

本次重新读取用户原先指定的 `https://manus.im/app/xR2wFOL9238kc7A9Z4CFik`，不是继续仅用网站开发任务推断。实际 1280×720 操作证据归 physical Root ignored `display-rework/manus-exact-task-hierarchy/`。

- [x] 初始“工作了 58s”收起，仅最终回答显示；点击后展开真实阶段正文和操作组；再次收起隐藏此前过程，最终回答仍在。
- [x] 整轮展开后，“浏览了 4 个网页”可以独立展开具体操作；公开恢复说明位于该组之后。这是“整轮过程 → 相邻动作组”的两层语义，不是按 discover/describe 切出的“工具准备”分类层。
- [x] 当前 App a0e7d740 的 `AssistantTurn` 直接平铺全部 `segments`，仅 `SegmentProcess` 有相邻活动组折叠；**缺少整轮过程与最终答复的上层阅读结构**。此前标签、间距、Markdown 修复均未承接此问题，整体展示仍不合格。
- [x] 双端只读核验：App `SessionMessage.textState` 仅表示完整性；Agent `MessageCompletedPayload` 对每次模型回合均发 segment/content，含有工具的中间回合；RunCompleted 只有终态/token_usage，BFF 当前投影没有最终答复 segment 引用。因此现有字段不足以精确区分阶段正文和最终答复。
- [ ] 下一最小跨仓切片：Agent owner 在真实结束路径明确最终答复与公开过程的边界，持久化后沿既有 HTTP/AG-UI/replay/snapshot 传递；BFF只保序投影，Web复用 Run/ordered parts 呈现整轮披露及独立最终答复。先更新受影响 owner 的正式设计/契约，再实现消费者；不在前端用最后一段、工具名或文本完整性冒充 final，不新增网络协议。
- [ ] Web主方写区：`AssistantTurn` 提取专用小组件；相邻动作组维持 `SegmentProcess`，不新增工具分类折叠，老记录无最终边界时保持可读且不伪造迁移。由现有参考确定结构，不再把字号/标签调整列为此结构项的完成证据。
- [ ] 保持在途文字/操作交错、真实失败/取消和待用户决策可见；无真实耗时不编造“工作了 xx 秒”。不从历史空段补造说明，也不通过默认隐藏失败来冒成功。
- [ ] 验收整轮收起/展开与内部组独立、键盘/焦点、刷新、进行中→结束、失败/取消、部分历史读取及同次详情；以正常页面与该参考截图复核，不用测试数宣称视觉完成。

参考采集轮没有修改产品源码或发送新任务。随后 Agent 候选 `b802f9b778fd686e80774adcdd72758325fb0b9b` 已推送原 Draft PR46（未合并）：成功终态的明确 final identity，真实原生图输出与同 Run 持久公开正文双证，原 terminal 事务固定，HTTP8.8 可选公开引用；旧记录不回填。纯文本/多步/空 final、实际 SDK HITL 新 graph 恢复/return_direct/checkpoint 无新流已核；真实 PostgreSQL 的绑定/replay/取消/回滚定向 12 项通过。BFF 与 App 读者、整轮折叠和正常页面仍未接通，**此项未闭环**。

BFF后继15cc9e1已提交推送原Draft PR17：固定Agent8.8、Public28.14；原事务持久化final与parts revision，snapshot/list/page和原RUN_FINISHED透传，隔离真实PG18及fresh/具名演进通过。停写串行lint/types/build、contract1325、architecture36、default2287通过（3原资源跳过）。App正在消费正式pin并已实现whole-turn候选：公共revision合并、分页引用绑定、完整正文后分层；原文字/活动顺序与独立final不变，旧缺字段不猜最后一段。未正常激活；用户旧conv6530没有显式final事实，不能以新模型候选冒称旧会话已对齐。独审发现的 retired Message/out-of-head 及第二终态身份漂移已加回滚负控。工程门本轮曾与主方重复 build 共享 dist 发生模块缺失；最终门禁必须停写后串行，不能将该并发结果冒称通过。仍不关闭此展示项。

最新独立推进（2026-10-28）：App `ed272244`修复既有侧栏系统测试真实菜单路径；18个受影响真实Next操作通过，原业务断言保留，独审无确定P0–P2。停写该提交后，显式受管Redis的完整默认355文件／6844测试全部通过，exit0、208.40秒；这是独立完整复验，早先18失败/缺环境结果与诊断日志保留。日志归ignored `app-final-default-configured.log`。Agent `20e82a6`只提交三项Swarm缺口设计记录，已推送原Draft；无生产补丁/SDK改动。

旧会话final证据纠正：owner只读审计已核实旧Run完整63个root checkpoint单链与唯一正常终止tip、冻结recipe/7版本/75源摘要匹配，锁定SDK原生DeltaChannel只读恢复24条messages；终止AI与同Run唯一公开assistant.completed正文/身份精确一致。不是内容丢失或末文本猜测。报告metadata归ignored `legacy-final-owner-audit.json`；主方审阅并独立运行 `legacy-proof-readonly.py`，exit0，63 checkpoint／24 messages／75源摘要／唯一公开身份对应全部复现，结果归 `legacy-proof-main.json`。连接强制repeatable-read/read-only，8 MiB／15秒预算，未写DB、未构建执行图/调用模型工具。现有32-locator展示预算不足容纳该历史；后续审查另发现SDK PostgreSQL delta快速路径先按整个thread读取metadata，再筛parent链，因此当前一次性证据脚本不得直接移入HTTP或当作生产有界reader。不得静默扩大预算、不修改旧terminal payload或直接UPDATE BFF final列；该列与event receipt／parts revision绑定。正常新Run候选继续与旧记录展示缺口分开，原会话UI仍OPEN。

App最新文档交付 `15499125` 已推送原Draft PR46，记录ed272244完整默认复验；生产源码保持ed272244，不合并、不提升Root组合。

App后继交付：`a97ec91b` 已提交推送原Draft PR46，fetch后相对main142 ahead/0 behind、相对topic1 ahead/0 behind再推送；不合并、不更新Root gitlink。最终相关138、contract442、architecture50、lint/types/build、preview3933桌面/移动E2E120通过（零重试）；全默认6824通过/18旧菜单定位失败/2测试Redis缺失未运行，保留exit1。补显式受管Redis后的两条stored-session已实际通过；菜单修后R183仍超时，扩大运行明确中断130，后续只跑单例定位，不冒整个复跑通过。菜单测试WIP不夹带该提交。

本轮后续证据：App lint/typecheck、正式契约442项通过，实际组件夹具已验整轮收起/展开、过程文字与活动交叉、最终正文始终独立及键盘收起。原始证据归 physical Root ignored `var/dev/mcp-prepare-receipt-20261027/display-rework/bff-final-answer-20261028/`，明确是候选组件，不是正常产品或真实模型任务验收。全默认串行复跑仍进行；已出现旧侧栏 Move 行内 button locator 超时。只读复核 HEAD 与当前 rail/system 测试均无 diff，HEAD 已改为 More→Move 子菜单，旧基线日志也复现；仅此类型已归因，不扩大为全部失败既存。未修改/删除这些测试或断言。正常激活授权待答，旧 conv6530 缺显式 final 的真实性证明仍 OPEN；不得用新任务或夹具通过关闭它。

Swarm 独立缺口已定位（只读最小复现29 PASS/1 FAIL，未改Agent候选）：bare Swarm compile未装四投影，pump读取不存在的tool_calls；直接peer正文位于原生subgraphs而非root.messages；锁定DeepAgents0.6.6 filesystem结果处理重建Command丢graph/goto。单进程假设探针同时承接peer投影与原Command路由后原正控通过，只证明方向，不是生产补丁。后续须在既有owner内记录最窄版本约束兼容落点，再实现异构peer、task边界、往返/HITL/replay及取消负控；不修改venv、不跳过失败、不将末条AI视作final。普通Agent已有候选证据不覆盖Swarm，上线仍OPEN。



新增真实 Swarm handoff 正控暴露既存缺口：外层官方图没有 peer tool/subagent 投影，读取 tool_calls 即失败，早于 final 判定。保留 RED，不 skip/xfail，不伪称全仓通过；修复范围独立落在 Swarm 官方 subgraphs 接线。它不抢占已实证的普通单 Agent 展示主线。当前没有运行切换、模型调用、正常数据修改或数据库 DDL。

### 当前证据及问题

- [x] 同尺寸参考/实现/新native标题截图及observations.json已归档：physical Root ignored `var/dev/mcp-prepare-receipt-20261027/display-rework/manus-recheck-20261028/comparison-latest/`。
- [x] Manus准备行实际为“检查当前会话的连接器配置”，点击后右侧显示终端命令；“读取项目运行时配置”与Webdev技术参数也分层。公开正文穿插在相邻动作组之间。
- [x] 正常旧conv6530仍为8条发现/说明＋3条调用。摘要3次与11条展开不是计数错误，但技术记录主导阅读，用户动作说明缺失；这是未完成项，不是字号已修即可关闭。
- [x] 实测本地动作行14px/20px、28px高；参考叶文本14px/20px。先前747对1280的断点差异不再作为像素结论。当前基线对齐、hover与长标题处理仍有待核差异。
- [x] 只读源码核对：主Agent三个MCP入口均接ActionDisplayMiddleware；模型副本字段required，公开activity字段optional。BFF未发现MCP专属丢字段。新native标题成功不证明新MCP三入口已真实验收；旧记录未持久标题不由前端补造。

### 同日用户再次否决后的实证纠偏

- 当前展示仍不合格。本次同1280×720实际展开/收起Manus阶段组，确认公开阶段说明始终留在主线，动作组可混合工具与文件；技术操作放右侧。这是Webdev参考，不冒同类DeepWiki参考。
- 新增只读证据排除“已有公开正文被BFF折叠吞掉”的猜测：旧conv6530的12个assistant.completed中前11段UTF-8长度为0、最后156字节；新conv0df的4段中前三段为0、最后158字节。每段身份、长度和SHA与BFF ordered text parts逐项相等；没有读取私有推理/原模型响应，没有新模型调用或业务写入。
- 因此旧记录的流水账体验不仅是CSS；原公开记录没有阶段文字且没有action_title。前端补译函数名或从工具说明推断目的不会修好事实来源。自然动作标题已经成功的新Run也不代表旧记录完成对齐。
- 当前待办收敛：先审Agent对复杂任务/真正阶段变化/失败后调整的公开进展表达（短单步任务不强制旁白、不每工具播报）；同时旧记录保持真实操作+对象、原顺序与可定位失败，技术参数留详情。仅改标签/字号不关闭展示项，不重新引入“工具准备/失败数量”嵌套。
- 本轮为实际调查与证据归档，产品源码与正常运行均未改；无新增测试绿色冒充视觉验收。证据physical Root ignored `var/dev/mcp-prepare-receipt-20261027/display-rework/manus-recheck-20261028/public-text-audit/` 的两端截图与lengths-and-hashes.json。

### 2026-10-28 历史操作修补已生效；读恢复独立待修，不替代展示闭环

- App `1e940a7c37006bb3caa8db0e413c27540820cc10`：旧MCP行恢复操作+exact对象，九语言简化重复MCP类别，原action_title最高优先、11项顺序及4项失败不变；没有再生成历史意图。正常11源HMR、859源核同，无进程重启。
- 真实conv6530刷新后显示新fallback；同名ask_wiki_question失败项仍failed/无详情、成功项仍completed/原完整结果，未串记录。conv0df新三标题在1280与747继续原文显示。原截图归档 `display-rework/legacy-action-verbs/`。关闭Canvas本次AX焦点落到WebArea，未冒称真实焦点恢复已通过。
- 先RED1/20、UI160文件3209通过；lint/types/build/posttypes通过。首扩大UI仅一条中文旧locator失败，更新为同操作文字后原完整Canvas接线断言仍在。独审无新增确定运行问题。全默认/contract/architecture/全E2E未重跑，18系统driver旧缺口保持；这不是整体视觉完成。
- 已核实既有Agent general prompt自58728a5即含多步公开阶段说明，活跃worker源码同SHA；不再把“加阶段提示词”列成待实现，也不强迫一句话小任务每工具旁白。
- **独立读恢复缺陷（保留待修，不作为展示对齐的前置条件）：** 多tab HMR后，旧conv主区整屏“会话列表加载失败/unauthenticated”，实际侧栏已读取200；显式重试后“BFF user admission failed”，随后精确snapshot GET429。正常刷新最终恢复，本次没有修其根因。正常log白名单已存hmr-http-statuses.json，早期401来源尚未判定。
- 根因定位：AppFrameConversationErrorSurface误用rail.listError；snapshot reader未保Retry-After/接可信401恢复，hydrate将读错误压成machine.error；重试UI先切别的会话或newConversation再打开目标，非exact读取且可能额外GET/清选择。待沿既有owner添加原目标只读恢复，401复用可信准入、429遵守冷却、403/缺失不混同；删fallback绕行与原始机器错误大面板，保未授权边界、草稿/URL/未知提交，不改IAM额度。

### 最新复核：停止用标签修补代替信息结构（2026-10-28）

正常 App1e940a7c，Manus既有Webdev参考与本地旧/新MCP会话均1280×720。实际再次展开/收起参考过程、打开本地同次成功调用详情；截图在physical Root ignored `display-rework/manus-recheck-20261028/rejection-review/`。本轮仅观察和只读审计，未执行模型、改产品源码或重启服务。

| 差异 | 已核实事实 | 闭合条件／下一写区 |
| --- | --- | --- |
| 主线缺少阶段说明 | Manus真实正文穿插动作组；本地两个MCP Run原公开段为空，不是前端吞字。已有prompt含进展规则，暂未证明SDK或provider抑制正文 | Agent只核真实请求/公开输出路径；不得再堆相同prompt、补造旧正文或强制每工具旁白 |
| 展开后技术记录同权 | ProcessActivityRows原样逐项；8准备与3调用同层同权。新Run已有自然action_title，旧Run没有 | 用现主行/详情层次解决，不盲加“主要/全部”筛选或恢复被否决的工具准备二级折叠；先取得同类MCP参考或标明产品取舍，保持全部历史可查 |
| 摘要口径易误解 | “3次”准确计执行调用而非11条活动总数；源码主动省略混合组准备计数。参考也有命令数与展开工具行数不同 | 不当计数算法bug改成11次调用，不凭该数量宣称已对齐 |
| 详情Markdown阅读已局部修复 | App a0e7d740复用现MarkdownMessage的text-only资源策略；原conv6530正常成功/失败切换、正文到底、原文披露点击/Enter已验 | 截图与859源哈希归`display-rework/tool-result-markdown/`；不冒同类Manus MCP一比一，宽表格/手机浏览器仍待 |

后继已实修上述结果阅读：仅3源HMR，无进程重启/模型执行/业务写入；focused101通过，扩大UI+i18n3239通过/1项目弹窗退休超时，相关与该原用例独立69通过；lint/types/build/post-types通过。不将复跑冒全量绿，整条展示待办仍未完成。读恢复缺陷仍保留，但不再将其提升成用户本轮展示反馈的唯一推进方向。两只读角色分别核UI投影与Agent公开文字来源；主方独占文档、实现和运行激活。

### 下一步：按业务展示闭合，不再绕到无关测试修复

1. [x] 本次真实新MCP discover→describe→call：三条具体公开行动和对象在首次/完成Agent事件、BFF activity与orderedparts逐项相等；正常终态和刷新保留，原详情命中同次工具。仅关闭此真实旅程，不保证所有模型输出质量；未用工具能力说明、函数名翻译、相邻正文或输出补造标题。
2. [ ] 明确旧历史缺说明的阅读方式：保留真实顺序、每次失败和exact详情，不机械恢复已被否决的二级“工具准备/失败数量”，也不假定新producer会修复旧历史。参考的正文/主行动/技术详情层次是验收目标，未观察到的MCP行为明确标为产品决定。
3. [ ] 完成同尺寸主线/详情、收起/展开、首次进入/刷新、长标题/路径、窄屏和键盘对照，逐差异关闭；全局展示通过前不将此项标完成。

### 本轮实现与验收（2026-10-28 后继）

- App `30ba1edb30a7571cccd9464d6f8d980e56936851` 已推送原Draft分支，正常3310仅2份源码HMR，859源核同：公开行动标题单行视觉省略，完整名称/title/精确详情保留；无标题文件路径继续完整换行；图标居中、hover只文字强调，focus/coarse触达不变。
- 新conv_0df86ab4：实际3次MCP动作，“查看可用的DeepWiki查询工具”→“读取…参数说明”→“查看langchain-ai/langgraph的文档目录”；正常run.completed、5模型attempt全部sealed、unknown0。三个owner公开视图标题相等，刷新后同会话/同答复/同标题。Billing admission/hold读回13积分captured，usage仍partial；未将此缩写回读称完整结算receipt/journal审计。
- 实屏1280与747两视口、同次详情、关闭回原按钮焦点、键盘折叠保答复已验；正常computed row28、font14/20、center、nowrap/ellipsis、透明背景。747无横向溢出；390/coarse实机本轮未测，不冒全响应式完成。
- 新样式回归先RED(normal非nowrap)，相关53、扩大3915、lint/types/build/posttypes通过。独审无确定新增问题；未重跑全默认/全E2E，18个过时侧栏系统驱动尚待处理。原分支main已非递归fetch，提交前基线138 ahead/0 behind，未覆盖他人更新；未合并或改Root gitlink。
- [ ] 新发现的独立连续性问题：完成会话刷新后composer连接器1→0；当前明确RAM选择，message-create仅本次intent，snapshot无会话默认字段。后续明确会话偏好或浏览器草稿的持久边界并核当前可用性，不从旧tool trace提升为新执行选择；不阻塞已验三步标题。

证据：physical Root ignored `display-rework/action-row-rhythm/`（源码/验证/回退）与 `manus-recheck-20261028/new-mcp-action/`（运行/终态/刷新/窄端截图及白名单owner回读）。本轮有真实新模型/只读外部工具调用，未修改连接配置或创建文件；不延续上一轮“无模型调用”的描述。

### 已完成窄切片与独立后续

- [x] Agent ba6c5a5重复结果投影：原结果完整阅读，旧活动/失败/技术详情保留。
- [x] App736633b8可见反馈读取减载已正常生效；并非所有429闭环。
- [x] App383486b3列表429有界恢复已提交推送、正常HMR，859源码核同；本轮正常导航清单已显示。真实隔离Next/Chromium＋fake BFF验证429→200，保草稿/URL/登录次数；不是向正常IAM注入429验收。
- [ ] 18个旧Next侧栏用例已只读定位为旧独立按钮未适配ellipsis/portal菜单；保原业务断言，后续独立修驱动，不用其数量占用当前展示优先级。
- [x] 原生同活动文件/目录详情、同次新ls标题、MCP完整结果已验，不重复执行模型充数。

完整Goal保持ACTIVE；最新调查未增加模型执行或修改产品源码。此前30ba与新MCP验收属于上一切片，不能把其结果扩大为展示完成；未宣称PR合并。

## 2026-10-28 最新展示游标纠正（覆盖旧“先接能力说明”顺序）

**同日后继：动作说明生产候选，非正常环境交付。** 已有新 Run conv689 刷新前后公开正文→工具→正文顺序逐字一致，仍有 edit_file 被泛化为“工具调用”的缺口；刷新首屏还出现“正在加载工作区”，保留 OPEN。Agent 新 `tools/action_display.py` 沿 SDK 同一次调用增加公开行动元数据，未接 factory/emitter、未改网络契约、未激活。复核暴露两项 P2（模型 schema 未扩展却剥离、HITL 改参后错误重绑原标题），均先建立真实失败再修复；现资格冻结在审批前原消息 checkpoint，执行按同 Run／call／参数核对，审批编辑不沿用旧标题。定向 33 项（含真实 SDK 新实例恢复、并发 stream、checkpoint序列化及实际 OpenAI wire）通过，ruff/targeted pyright通过；不冒称模型或产品验收。下一项只推进此生产源→原持久 activity→BFF/App reader-first及真实页面对照，不另开无关修复。


- [x] 实际对照 Manus 可读行动行→工具详情；核实 App 拼接式展示与 Agent 缺少逐调用公开行动说明。
- [ ] 在已有真实新 Run 核验阶段正文与相邻活动的原始顺序及重开恢复。
- [ ] 在原 owner 内确定行动说明的产生、exact call 绑定及缺省规则，再实施；能力说明只放详情，不当行动目的。
- [ ] 真实同视口验证主线/详情、展开/收起、失败、窄屏；未通过不得关闭 Agent 展示。

结果阅读已修不等于本项完成；8.6 候选保留但不再作为主要展示差异的解决依据。完整证据与边界见 CURRENT 首节。本轮研究没有运行模型或变更产品/运行环境。

## PROJECT-1 当前执行补充（2026-10-27；以下原历史保留）

<a id="project-1-full-scope"></a>

**2026-10-27 本轮正常最终快照。** App6907583／BFFa819855 Public28.5／Agentfc8b0f0 HTTP8.2；App826／BFF916正式源码核同，原env/deps/lock保持。Reader先于producer的动作对象链仍有效：Run804f356e实际文件读取＋DeepWiki发现／描述／调用，四项对象首条／返回／compact／parts一致、旧history不回填、刷新零重复，10attempt／20积分全sealed/captured；合此前五QA共33／73，原40冻结不改，cache仍partial。当前Root只关闭下列本次切片，全产品与AUTH-1仍OPEN，Draft不合。

| 本次切片／owner | 结论与真实验收 | 保护与后继 |
| --- | --- | --- |
| 侧栏Session／App | 隐藏四44px占176px→单44px，mobile标题83.8→215.8；desktop284px行静置动作0。390短菜单224px＋子菜单122px实际无越界，9语种保完整目标aria | 局部组件／CSS，不改Sidebar全局primitive；原move/archive/delete unknown链保持 |
| 项目同一菜单／App | 真右键、Shift+F10、ellipsis共用固定／编辑／查看／显示更少／删除；Manus与本地实际110×188／12圆角／36行／14字／16图标。652 View关闭Sheet、Show less折叠任务、取消编辑／删除零写 | 删除红沿Kokoro原语义token，与参考存在轻微色差，不作全像素声明；代码只共享真实责任组件 |
| 个人pin／BFF＋App | 正式c195合同109a／28.5／194、完整28.4 inverse保持；正常a819复用canonical错误。授权后仅新关联表PK＋两索引，DDL原32表row/xmin保持；旧程序兼容／新程序ready200 | 自然幂等PUT无命令receipt；全局actor偏好不按路由清空，unknown只显式精确GET，权限／Project可见／parent锁／删除事务清理保持 |
| pin真实闭环／Root | QA R258键盘固定→1row→刷新同row/xmin／Pinned→取消→刷新普通区及空表恢复，键盘跨区回同Project。真实PGpin／evolution含BRIN负控全0，库94→94 | 正常其余31表不变；AGUI stream正常poll/lease更新单独报告，未冒全库零写，无新模型/资金 |
| 连续Dialog旅程／Root＋App | 旧源真实RED两轮；B编辑取消→首次A删除，最终690正常连续两轮正确确认并取消。根因activeId hydration在同地址错误退休已消费handoff | 仅去非地址activeId依赖，保完整URL／Project／actor/generation／ABA／unknown原key/body与202；真实scoped engine回归承接注入单engine盲区 |
| 最终门／Root | UI/core/engine/features/薄桥3512、contract392、architecture50；lint/typegen/types/build/posttypes0；原79输入完整Docs50及188公开op/54HTML/18637链接0。BFF完整2053/3旧skip、contract1205；AM11／error12后继相关门0 | 所有阶段绑定停写SHA与正式提交；完整App默认旧Next失败未重刷仍OPEN，Draft不合。不是全产品验收或所有接口100ms |

**下一动作与保留差异。** 本次用户标题留白／项目菜单两项已闭合，截图与Manus计算样式／真实回读及红绿保ignored sidebar-project-menu-20261027。既有T02追加ProjectConversations实际短暂可见loading／骨架，不冒称全站已无加载；其余Project网站／网页资源／定时过滤／ACL和原完整目标继续，仍复用此计划。独立Provider/OAuth事实缺口不扩散阻塞其它CRUD；不将本次五项菜单等同完整七组项目能力。

**执行教训。** 有opacity不等于不占flex宽；完整实际操作往返不由测试数量替代。pin canonical错误和前置admission需真实响应验证而非手造DTO。scope可见性管新请求发起，actor＋flight管已发结算；旧分页continuation在refresh时退休，焦点移动按当前actor/route/visible target核验。不自动重放未知PUT，不渲染失败空Pinned／重试面板。精确具名generator／natural PUT清单要承接真实新增项，不因此削弱白名单；原失败和修正SHA留档。BFF日志停止前预检、并行使用正式Git输入、保他人WIP和远端main，仍为当前执行约束。

本机Codex App只读取证被工具明确拒绝，未绕过；官方介绍页仅一般产品参考，不能冒充当前动作行的精确像素基线。继续采用用户最新Codex方向与已归档Manus真实分组规范，不等待这项参考权限而停工。普通执行／账本／取消／授权语义保持，新显示对象不自动变成文件访问或分享授权。

**2026-10-27 最新正常与UI闭环快照（覆盖后面阶段记录，完整项目仍开放）：** 正常App `00974e0`／818非MD源码逐字核同，BFF `b2b9eb1`／Public28.3、Agent `38c294d`／HTTP8.1、Platform `6fdeae0`不变。真实MCP→文件交付／55字节SHA→读回／重开，以及独立Project默认Skills版本1继承／真实两文件读取已验；五QA Run共23attempt／53积分封口，新冻结0，原40不动，cache仍partial。当前38c真实3次自动压缩核capsule／原生事件／精确输入checkpoint／祖先；未把旧hard-kill证据冒作本次重演。

单一live进度、中性44×44成果卡、空href转文本、按真实Run归属均正常生效。四项Project共同上下文／dialogs已单实例接回会话，保一Composer、完整URL、Canvas原预览／DOM与同URL unknown原key/body；普通Skills／预览读取不再闪generic加载重试卡，真实内容及关闭重开仍验。实际Root往返另抓到activeId不变导致设置菜单拒开；已按完整pathname/query/hash退休既有命令／呈现与旧origin回调，保跨Project显式handoff，正常两轮Root→原Task→设置成功；不再把阶段测试通过算整条旅程。最终163文件3444相关PASS、lint/types/build/posttypes0；原完整默认两次6147／1仍有Next OIDC/request-hook缺口，AUTH-1／全App合并门未闭，Draft PR不合。

**Project子队列下一动作（服从[当前Goal顺序](#goal-progress-current)）：** 已有四项共享组件读／取消／URL／Canvas／响应式切片关闭；后继七组Project能力承接原设计，不重跑已验付费链。Project scoped定时列表沿原D0先补BFF owner过滤与正式契约，参数承接已有create的ID/slug、内部解析canonical Project，App使用已准入canonical ID；空本人Project与无权／墓碑分开，Scheduler I/O前后核权限、原5秒生命周期与取消不放宽。App复用原EditorDialog而非全局hash editor hook，仅先替换Project根页原卡，不擅自扩Task栏。对应owner文档／正式artifact先过门；网站／网页资源／RSS／Webhook／Beta／ACL仍独立OPEN，不开flag暴露preview数据。完整无感加载／后台报错与精确Manus对照也未凭这两处提示修复勾完。

**2026-10-27 项目完整范围校正（七组能力，整体仍开放）：** 用户新截图不是单独的 Skills 卡，而是整个项目上下文面板。已并行核对 App `ea04903`、BFF `1177715`、Platform `8cfead6` 的相关实现及正式契约，并只读观察 Manus 项目 `NB6rBWho5ecJHdsbQpZ8kw` 的网站选择器、触发任务类型、定时表单和事件来源。未创建、保存、授权或发送参考任务，参考原草稿保持。菜单截图／操作记录留在 ignored `var/dev/project-full-scope-20261027/`；本次调查不是实现交付，不新增完成勾选。

| 能力 | 当前事实及缺口 | 下一动作／关闭条件 |
| --- | --- | --- |
| 指令 | 已有项目范围 PATCH／GET／历史及未知提交恢复证据；不是新增后端空白。 | 保留已验写入恢复；补完整面板同态对照及新任务继承证据。 |
| 连接器／MCP | 真实 Manus 项目入口是“推荐连接器”：跨目录搜索／复选／取消／保存，已连接成员默认启用且各自可关闭；不是定义发布。本轮前runtime-manifest缺connectors键、源码只跳全局设置；现已正式启用独立推荐集合与选择器。原publication仍是定义pin，与推荐分离，不自动连接或授权。 | BFF正式推荐CAS／自然幂等PUT与App选择器已正常激活，已验持久化、取消、默认匹配和手动取消优先。新Run实际承接Connection，后继MCP发现／描述／调用、同会话产物／下载及终态恢复已真实成功；原503留历史。继续四类详情／内外入口同态验收与展示后继，不以此替整个MCP模块完成。 |
| 文件和资源 | 文件上传、扫描、metadata、原生下载、删除恢复已有真实证据；截图还含网页资源与“搜索网络”，该旅程尚未完成。 | 文件已验环节不重做；核实网页资源来源、选入／移除、刷新及任务实际读取。 |
| 技能 | 已有项目专属安装／列表／详情／启停／更新／移除，以及默认选择 GET／PUT；不是仍跳全局设置的旧占位。 | 版本1安装／启用／默认保存刷新、首发继承与同Run实际两文件读取已验；继续其余完整项目内CRUD及同态UI，不把此单条旅程当全部Skills完成。 |
| 网站 | 当前项目网站内容来自 `previewWebsites`，关联仅组件本地 state，尚非正式持久化。Manus 实际“添加网站至当前项目”为已有网站搜索／选择器，不是截图即可推定要另造托管平台。 | 确定既有用户网站实体与项目关联契约，再过受影响设计门；列表／添加／移除／刷新须走真实 owner。禁止打开 flag 暴露演示数据充数。 |
| 触发任务 | Manus 实测三入口：定时任务、触发任务、高级自动化 Beta；事件来源含 RSS／Webhook 等。现有ScheduledTasks已有新建project_id、时间计划及CRUD；本轮只读确认list/current公开契约尚无项目过滤，URL参数只决定新建归属，不过滤账户列表。项目卡仅跳转，没有完整嵌入列表／编辑；事件订阅与高级自动化正式契约仍缺。 | 先复用现有定时任务业务切片，核列表分页／项目过滤后接项目入口；事件／高级能力由现有业务 owner 明确触发、授权、投递、取消契约后实施，不以 cron 代替事件。 |
| 分享和权限 | 当前项目分享仅私有 URL／复制，没有成员／邀请／角色／撤销授权契约；会话分享 scope=project 不是 Project ACL。 | 项目 owner 定义实际协作范围与权限后实施；用访问者真实读取／编辑／撤销验收，不以复制 URL 代替。 |

**2026-10-27 前半段历史：正常激活／首次失败旅程快照：** 用户确认的范围已执行：BFF `21c6447` 已推送并正常加载；Project仅新增推荐集合／独立版本两列，配置采用CAS＋自然幂等PUT，无新增receipt／journal／outbox。System仅新建并暴露 `workspace.connectors`，manifest实际只多该启用键，网站／触发任务仍隐藏；原凭据和工具授权不改。App `dc7941d` 已正常加载，815非MD源码核同；后继 `18c1861` 两文件按Manus实际computed style补30%黑色＋4px模糊并正常配对。Root在冻结字节上完成App完整6113通过／0失败、lint／types／build及post-build types全0；后继视觉12通过／lint／types0；BFF默认2020通过／3原资源跳过、contract1191通过及隔离PG7通过。独审发现的可选Server误筛和pending关闭丢焦点已修，误用另一个Connection协议提出的status风险明确撤回，没有为失真替身新增状态。

真实正常R258：选择后取消未保存；保存MCP＋Custom API→权威回读／重开，只有本人可用MCP被默认选入；手动取消为[]后保存新推荐仍保持[]；刷新新草稿重新默认选入MCP。正常Project版本1→2→3，推荐事实实际持久化；同1138×767的选择器560×590／16px圆角、18/600标题、528×36行与Manus测量一致，参考／实现截图已归档。首次发送实际新建Project会话，BFF launch确实承接本人Connection，URL／Project／终态／重开恢复已验；但发现工具步骤得到 `MCP_CURRENT_READ_FAILED`，没有成功读取外部文档，**不能关闭执行链或整个MCP／PROJECT-1**。正常日志已定位GetConnection200约15ms、GetConnector200约10ms、随后ListMcpServerDeclarations503约3018ms；这是声明发现子链，不是App漏传，也不证明远端DeepWiki不可达。继续定位该跳的DoH／逐RPC预算／协议握手，不重发原Run、不扩大授权、不拿UI保存成功当工具成功。

正常加列前后，原Project／Conversation／Message／命令receipt／dispatch事实、xmin／ctid核同；在线 `bff_agui_stream` 操作态有变化，故不声称全库零写。原始证据、两次WIP门失败、错误推断撤回及最终冻结门均保留在 ignored `var/dev/project-mcp-recommendations-20261027/`。完整E2E／全产品<100ms与七组项目能力仍开放；PR仍Draft，不称已合并。

**本轮前进判定与证据：** 上轮是范围／源码调查进展，本轮真实点击已改变实施选择：推荐配置与 definition pin 分开。已取同页 DOM／计算样式，560px 选择器、18/600 标题、36px 操作按钮；正常本地 manifest HTTP200 与项目截图证明三个入口当前隐藏，不误判为已具备实现。证据 `var/dev/project-full-scope-20261027/connector-recommendations-observation.json`、`manus-project-connector-recommendations.png`、`local-project-flags.json`、`local-project-current.png`。BFF 设计 writer 仅既有三面文档候选，Root 独占浏览器／任务板／Git；另一只读调查转入隔离 ignored 的 Next writer 诊断，不碰正常服务。

**下一定时切片已完成最小D0（待当前display配对后实施，不重新调查）：** BFF现GET增加可选唯一project_id，缺省保持全账户原列表；在同tenant／subject的owner SQL先过滤再做Scheduler current读取，并在前后两snapshot核Project可访问，空项目与无权／已删项目分开。无分页／新表／新调度框架。App走既有 `/api/scheduled-tasks` 同源adapter（非Hub catchall），沿现真实EditorDialog和mutation pending身份，项目局部list／scoped hook隔离路由／主体／Project、传AbortSignal，慢admission到EOF共用期限；不在客户端静默过滤误返任务。保账号路径／身份头／原五秒owner生命周期，覆盖A/B/个人隔离、读中删除、取消／迟到、重复query、unknown原请求、390与键盘。正式契约从已冻Public28.3后继演进；网站／RSS／Webhook／高级Beta／ACL不混入此片，flag仍由Root在真实链验过后单独激活。

**推进顺序与防遗漏：** 项目推荐MCP／同会话产物／默认Skills实际读取子链已成功；当前先按新反馈收口成果Run归属与Project会话共同上下文，再推进项目定时列表过滤／嵌入；已验工具发现／类别不重做，Next旧风险独立保留不拖四能力UI；其余独立的参考／契约澄清并行，不等一个外部 Provider。网站、事件／高级自动化、Project ACL 涉及缺失实体／契约，先提交必要设计结论再改数据与传输边界。每组分别记录“入口可用、写入持久化、任务执行、同态 UI”，七组均满足各自适用条件才关闭 PROJECT-1；本轮资源／删除收据只关闭对应动作。


# 最新目标与 TODO：面向上线的正式产品闭环

<a id="release-readiness-20261021"></a>

### 2026-11-01 Task B 功能分工领取

2026-11-01 用户进一步明确核心目标为简历/求职：以可通过腾讯云演示地址访问、能完成真实任务、本人能解释的产品成果安排优先级；产品页展示功能结果，面试再说明技术。Task B 范围不取消。个人演示部署与同事公用实例分离，代码沿已验证 Root 精确组合更新，数据库/对象存储/会话/OIDC/密钥/域名单独配置。先准备手动版本化部署、健康检查与回退，再按实际需要接自动发布；不修改同事既有 CI/CD。当前仅方案及部署差距核查，未接入腾讯云；现有 Phase1 Compose 的 mock/preview 默认与旧目录不能作为全功能正式演示直接发布。

负责人：协作者 B（会话 01a11b32-a116-7083-acac-501aa5514c48）。范围以用户本次 Task B 为准，替代此前 Web/Backend 分层及本会话不改 Skills/MCP 的旧边界；复用本节有效目标，不另立产品事实源。A 保留统一发送、Run 控制、会话及产物展示；B 负责能力配置、资格/版本/授权、专属执行材料及账户协作的完整切片。

基线：Root main 3a3b6b91faf4540a2499915698f2abbdb525ba85 已从远端核实；首次实施先核各 owner 当前 main、已有 diff、真实进程来源。旧本地首页功能分支完整保留，不以旧运行源推断当前 main 缺能力。正常预览不因盘点重启。提交、PR、集成绑定实际门禁与精确 owner artifact，不把历史局部证据升级为本轮验收。

| ID | 功能 | 当前领取状态 | 验收范围 |
| --- | --- | --- | --- |
| B-01 | MCP/连接器 | 进行中：当前生产消费链盘点 | 四种创建→详情/编辑/图标/删除→刷新；目录分页；OAuth/Connection/Enable 分离及失败恢复；普通页/管理页/Composer 同身份 |
| B-02 | Custom API | 进行中：执行与秘密边界盘点 | 多配置、隔离 Run、跨账号/撤权/漂移、迟到/取消、文件产物秘密边界；真实 Docker/E2B 分开报告 |
| B-03 | Skills 目录与安装 | 依赖 B-01/B-02 | 精确版本/目录详情/安装启停/刷新一致 |
| B-04 | Skills 创作与发布 | 依赖 B-03 | 来源/扫描/版本/审核/角色/未知结果恢复 |
| B-05 | 任务能力与外部授权 | 随 B-01/B-02 | safe refs、Describe/Acquire、真实工具调用；与 A 统一发送/展示配对 |
| B-06 | 登录与身份 | 出现可复现 P0 优先插入 | OIDC 回跳/刷新/注销/过期/多标签/撤权及故障分类 |
| B-07 | 账户设置 | 待后继核验 | 读改存/刷新重登/CAS/取消/窄屏 |
| B-08 | 知识记忆 | 待核现有 owner/范围 | 下次 Run 生效/停用/清理/隔离，不另造服务 |
| B-09 | 团队角色 | 待后继核验 | IAM 权威分页/邀请/角色/撤权/迟到 |
| B-10 | 分享协作 | 待后继核验 | 分享 metadata 权威回读/显式发布/撤销/权限矩阵 |
| B-11 | 模型管理 | 随真实任务 | 选择到精确执行修订/健康/价格/后台回读 |
| B-12 | 积分结算 | 随真实任务 | 同 attempt 预占/结算/释放/未知恢复/余额账本一致 |
| B-13 | /manage | 随功能 | 现有管理壳中完成对应 CRUD/权限/审计及用户端回读 |
| B-14 | 视觉/性能 | 随功能 | Manus 同态对照、窄屏/键盘/回焦、冷/热 p50/p95；未观察不称一致 |
| B-15 | 说明/PR | 随功能 | 页面/接口/数据/实际门禁/限制/精确 artifact 与 A 停写互审 |

首批只读任务：B-01-AUDIT 查 App→BFF→Capability/IAM 当前真实链及最小缺口；B-02-AUDIT 查 Agent Custom API 多配置/取消/输出与文件产物秘密边界，列已有测试与未证风险。主控独占计划/基线/Git/资源；审查员不改源码、服务或正常数据。实现文件集待源码证据后明确，未授跨仓并行写入。

#### B-01-SESSION-READ：Provider 独立读 401 恢复

- owner/writer：App MCP hooks；主控独占实现及 Git。基线 App 4860c37d，工作树 clean，相关三份原测试72 PASS。
- 现有来源：Provider 目录筛选/续页、详情和关系全扫描各自 catch 未报告 typed HTTP401；同目录精确 Connection reader 已向 ProductReadRecheck 注入原 subject/generation/signal。BFF/同源维持正式401，恢复资格属于 AppGate，不能由业务 reader 伪造。
- 设计：仅当前未退休且未取消的正式 HTTP401 携捕获的 actor/generation/signal报告；403/依赖/parse/network 不触发。关系扫描只分享活跃flight，将原 signal 暴露给订阅者，旧主体/代退休不报告。重入仍由现有单次再准入预算与代际重新GET驱动，不重放写命令。
- 写区：src/ui/mcp/use-mcp-provider-directory.ts、use-mcp-provider-detail.ts、use-mcp-provider-relations.ts；tests/ui/mcp-provider-readmission.test.tsx（这三个Provider reader的会话过期/退休风险，放现有UI测试而非新通用auth套件）；相邻INDEX与当前事实仅准确记录。无新接口/Schema/状态持久化/owner，原三面设计仍适用。
- 验证：先用合法typed401写失败行为用例；覆盖目录筛选/续页、独立详情、关系尾页；403/503/parse/network负控、跨主体/代际/abort/已卸载迟到、重新准入GET恢复；原相关72例与Session再准入/配置保存/Composer回归，lint/typecheck。浏览器正常过期验收另证，不能将hook替身称真实IAM。


B-01-SESSION-READ 候选实际结果：新28行为回归先4项正确RED、最终6文件257PASS，独审无确定P0–P2。contract445/architecture50通过，完整lint0；扩大MCP/API885PASS/3原视觉夹具失败，单跑同失败，保持断言。typecheck新测试声明已修，仅余HEAD既有A展示onReconnect/legacySteps错误；未改其写区。已提交/推送 App6a4f591d，复用 draft PR49；正常IAM过期与整体B-01未关闭。

本机正常3314只读浏览器验证：真实OIDC登录→首页插件→管理连接器→设置面板完成初读，MCP列表HTTP200，但Custom API列表HTTP503。该运行源仍是旧home代码，缺当前ProductReadRecheckContext，未将候选三hook单独复制激活。此证据证明导航/登录和实际错误，不称全部连接器可用。Capability固定44fcc5d的focused65通过；Provider CRUD真实PG1通过，Custom API HTTP边界5通过（IAM/持久层替身）。扩大个人MCP真实PG8通过/3失败/1原skip：OAuth刷新后的Prepare/Enable被“private MCP connection policy changed”挡住，正只读定因，不删断言。

#### B-01-CREATE-DETAIL：API/JSON 完成回读

App唯一writer task_b_mcp_audit；基线6a4f591d（B01过期修复已推PR49）。三设计前缀已先写；允许现 connector-command、custom-api-create-flow、mcp-json-import-flow、use-connector-creation-form、两form、connector-command-context、mcp-create-dialog、mcp-projection-read及同功能局部组件/CSS、相关测试/i18n/INDEX/CURRENT。仅安全locator的UI完成投影；无wire/Schema/正常源/A展示写区。单JSON直接详情，多项明确选择；取消迟到/换主体/新代/完成失败重试/秘密清除要保。主控独占Git、冻结后独审与工程/真实界面门；不把替身当owner旅程。

冻结候选新增17行为回归，主控6文件130通过，独审无确定P0–P2。契约444通过/1既有生成器子进程5秒超时，原文件单跑23通过；保原门禁不扩大超时。完整lint通过，build编译成功但被既有A onReconnect类型错误阻断；App015862bb已推原PR49，不合main。Capability真实PG工具fixture对齐原授权名后11通过，SSE子项另配置自有空库1通过并清理，原policy/revocation负控10通过；d5708828已推原PR12，生产policy校验未改，原失败完整保留。

#### B-01-READ-RECOVERY：可见局部错误与权威空态

创建详情提交后由同App writer接续。范围：mcp-projection-read、mcp-provider-catalog-dialog、use-custom-api-projection、use-mcp-projection（仅原GET attempt/settlement）及必要内聚局部组件/CSS、对应既有gallery/read测试、i18n/INDEX/CURRENT；无wire/owner/Schema/A展示变化，不另建错误中心。读取失败目前只sr-only，旧confirmed空状态还会掩盖刷新错误。保留已知卡片，但全空/无匹配必须由当前相关读取共同确认；内联错误和GET重试按失败reader分流，不刷新健康部分、不重放写命令。保持401现有再准入归属、同主体/代际/取消边界和显式尾页/循环恢复。新按钮需真实同步pending围栏防重击，禁setTimeout假解锁；API故障不污染非all目录分类。先业务RED，再恢复、部分失败/已知卡片、旧确认空、迟到/重击/循环边界；主控冻结后独审与浏览器/窄屏验收。

交付状态：Root 最终八文件90项通过，完整ESLint通过，独审原焦点P2关闭；受保护重试失败回焦且用户移焦不抢回。浏览器测试独有缓存避免已证Vite优化缓存争用，原一次挂载失败保留而未假定根因。App b3dcbe44 已推原PR49；390/1280静态生产CSS和隔离hydrated Chromium只作组件证据。正常3314未激活，既有A类型/build错误仍OPEN，不称B-01已完成。

#### B-06-READ-RECOVER：已确认断线的显式恢复入口

只读追溯确认旧合并34295b54/736239c7部分落地：status组件移除onReconnect/按钮，但现AppFrame仍正确连接engine.reconnect；另测试引用未落地的legacySteps，当前正式projection已采用安全activity单轨。Root将前者视为B06/B14必要恢复，唯一App writer task_b_read_recovery。仅status-surfaces组件恢复unavailable的显式重连（暂时reconnecting保持sr-only），新增就近UI风险回归及原projections测试迁移；保持原顺序/拼接/tool身份断言，以typed safe activity顺序及状态更新承接失效legacy字段断言，不恢复raw旧renderer。现engine snapshot-first/active身份/零重发POST测试完整保留并复跑。禁止改engine、Run/control、wire、线程renderer、A其它展示；Root负责独审、lint/types/build与正常配对，完成此窄修不代表整个B06已验完。

交付状态：App aa3fbbdb 已推原PR49，冻结后Root完整engine加相关core/UI23文件517项通过，writer另25文件542项通过，独审无确定P0–P2；完整lint/typecheck/build均通过，先前类型/build阻断为已修历史事实。正常身份旅程尚未完成。

#### B-15-NORMAL-PAIR：保正常源的正式配对准备

正常3314仍为旧Web/BFF组合，不能直接换候选Web：存在MCP availability、模型目录、Skill publish/版本/删除及A display/parts/feedback等具体协议差异。原BFF8395有4个RSS/Billing提交与批准853分叉（4/84），merge-tree已证27处内容/重命名冲突；其正常库还含RSS历史表，必须保留。先将正在从canonical checkout加载的8395冻结为同版本独立运行归档，避免后继BFF实现/整合影响运行中的源；这是运行发行物，不创建新Git worktree。准备writer task_b_api_postgres仅写`.local-run/task-b-bff-normal-8395`与本机证据，用固定commit源、冻结lock独立依赖，保全必要生成物hash；不启动服务/数据库、不改原repo/index/ref/正常配置。Root核验后独占原env/端口的优雅切换及恢复。

升级前置已只读定位：P44正规installer识别当前74d5父并只扩展，仍需新版IAM执行凭据配对。BFF853需修message-parts canonical精确向后投影，并补dispatch双nullable列正式演进；当前normal还有RSS历史，不为达目标删表/列。迁移须在隔离库验证数据保持、失败回滚/幂等，备份/恢复演练后才动正常库；现阶段未升级Schema。各未就绪末端不阻其它独立功能。

#### B-15-BFF-EVOLUTION：正式升级入口修复

Root已将正常BFF55838从physical checkout优雅切至精确8395独立归档，launcher39043；全790源blob一致、归一业务配置相等、正常原OIDC session与MCP/API三GET200。P27085/Web62806未动，未执行DDL。原feat/home-workspace-completion四独有提交保留；physical现新分支feat/task-b-owner-closure起自批准853。

唯一BFF实现writer task_b_safe_file_tools，仅正式schema脚本/对应测试/package scripts、INDEX/CURRENT与三面设计必要前缀。第一修message-parts parser：沿现canonical regen/final定义做精确父投影与当前catalog识别，保原exact parent/CHECK，不改历史parts/regen/final语义；第二补既有dispatch.execution_project_ref与execution_context_retired_at两nullable列的具名正规check/apply演进，严格允许已知旧/current shape，不接受未知/部分漂移。无canonical新表/列、wire/owner pin/运行时业务变化，无兼容读写层或第二schema事实源。先实际RED与设计，隔离PG数据保持/幂等/取消/回滚/错误shape验收；不得运行正常库、服务或Git mutation。Root负责独审、资源执行/备份恢复与后续整合。8395RSS/Billing分叉只读分析由task_b_api_postgres进行，禁止并行写BFF；整合/正式配对未完成，不称新版Web已激活。

本片交付：BFF b3289f4a 已推原draft PR17，独审无确定P0–P2。Root默认2306 PASS/3原SKIP、contract1327 PASS、正式build；两个独占PG文件12测试通过（7 pure/5 PG case），全输入前后hash相等，原13文件冻结hash经独审和Root复算一致。独占两库保留供后续演进验证，未正常DDL。真实SQL权限矩阵/并发apply与正常备份恢复尚未验，不冒产品升级完成。

#### B-15-BFF-INTEGRATE：保留正常 RSS 的正式整合

Root以b3289f4a（批准853+已验升级工具）为主体，与正常源8395b44作显式双父整合，保留四笔旧独有提交历史。唯一BFF writer task_b_safe_file_tools；Root独占merge/index/ref/提交/PR。writer只解决本次实际内容冲突、已自动合并的相关语义、相邻设计/测试/正式生成物，不变更当前owner pins或删减A的Run/display/feedback/regeneration/项目能力。旧Public20 RSS与批准历史Public20不同，不按版本号盲串证明；整合为单一canonical Public29.0，完整保留批准199操作，补既有运行记录与RSS分支，固定精确父摘要及明确有限整合delta，保旧历史oracle不重签。RSS必填trigger_kind的breaking由新major表达；消费者须待正式owner提交后固定更新，不在当前正常Web上伪造兼容层。

Billing沿批准23ff的11正式SDK和原identity export，旧初始化更强的body/未知/取消/首末准入保障收敛至唯一现PUT；下载沿批准/download及现项目资源接口，承接旧独有有界/取消保障，不恢复重复/content别名。RSS两表、三表增量、receipt schema_version3及calendar历史身份保留；canonical仅合并两父已拥有事实，不新增别的服务或表。正常替换前仍须正式旧RSS父→最终演进、真实数据保持与备份恢复。沿原生成器重生受最终lock影响的manifest，保批准vendor/pins；不手改generated或丢旧测试换绿。设计先行、实际RED/受影响回归、冻结独审及全门由Root收口。旧8395归档继续运行，无正常Schema/配置/资源修改授权给worker。

正常库升级前备份恢复演练已实际通过：固定原生pg_dump/pg_restore18.4导出BFF owner一致性只读快照，在新建的本次专属临时库恢复，32张表的行数和全行SHA256多重集逐一相等（备份117725bytes）。正常库无DDL/业务写入，未把副本恢复回正常库；该快照不是后继升级时的最终恢复点，正式Schema演进与正常激活仍待验。专属副本保留用于最终旧RSS父→整合canonical演练；私有库身份/备份不进入Git。

BFF整合已正式提交/推送7e4ab1cee8f8d45a34902176cd15a10f3c4b22cb至原draft PR17，双父b328/8395保留，Root停写默认2756PASS/3原SKIP/0fail，独审无确定P0–P2。克隆库八正式入口各check/apply/check/apply均成功且逐步原32表旧值摘要保持，含原RSS任务/poll/seen；与34表fresh canonical首次raw比对仅3个旧CHECK括号差异失败，保原记录，后继仅此3对在PG原生重parse后精确相同，其他catalog exact且已独审。正常库未升级。固定消费者和正常业务旅程仍待，不把已推代码冒正常源。

#### B-14-MANIFEST-DEADLINE：当前展示读取的有限等待

正常旧源只读巡检已证17设置Tab DOM可打开，但全局networkidle等待被持续pending的runtime-manifest拖住；当前重测manifest173ms返回缺配置503，不能把历史pending唯一归因于它。候选App同一hook代码事实仍是fetch/response.json没有client总期限，AbortError统一忽略；这可用不合作fetch/body的确定性测试复现无限loading，独立于服务端15秒预算。唯一App writer task_b_api_postgres，基线aa3fbbdb。仅use-runtime-manifest、就近原hook/行为测试及INDEX/CURRENT/三设计必要前缀；无BFF/public/owner/wire/manifest值/导航权限/Run/正常源修改。

采用一个20秒绝对client读取预算覆盖fetch与body；超期归source:error、清retrying、退休并abort本次读取，沿现PRODUCT默认，不冒preview/live。离页/模式切换/新attempt取消保持静默，旧迟到结果不能覆盖新scope或重新应用主题。只手动GET重试，不加自动重试/独立错误中心。保持已有current空导航/locale/theme allowlist/preview/身份边界。先真实业务RED：永不完成fetch、headers后body卡住、非合作迟到、截止与成功竞争、cleanup/新attempt、主动错误AbortError与取消区别；再原风险回归、冻结独审与相关工程门。这个修复不能声称消除当前缺System配置的503或历史pending唯一根因。

Manifest修复App8f607e87已提交/推送原draft PR49，独审/Root相关57PASS、正式contract/architecture/lint/types/build与preview E2E120PASS。完整默认仍红，6个Redis环境组正确复验130PASS；OIDC97项被编译就绪前置阻断，单独亦失败。5个纯UI候选/HEAD均22FAIL361PASS，另3项视觉既有差异保留，未降门。正常源未切。

#### B-01-DETAIL-READ-RECOVERY：创建交接后的 exact 详情恢复

独审定位当前API、private MCP及Provider exact详情GET失败仅sr-only，profile缺失使表单锁定；createdDetail/createdApiDetail还禁用列表reader，不能借目录重试。唯一App writer task_b_api_postgres基线8f607e87，先修这组三详情再做正式29消费者配对。复用现McpReadFeedback/detailRetry/readScope与owner+window+locator围栏，只重发失败详情GET、同步pending防双击、失败回焦且用户移焦不抢，保401现ProductReadRecheck/代际/取消/迟到及未知命令；绝不重放创建/保存/Prepare。写区仅原projection、三详情hooks/dialogs、局部反馈必要接线及就近既有测试/INDEX/CURRENT/三设计，禁止engine/Run/正常源/Git/pin。原Provider四个sr-only/no-retry过时断言按现行为迁移且保其独有风险；icon Save旧关闭假设改为exact详情回读/显式关闭，保命令一次及icon不取消。真实RED后focused验证，最终与消费者配对合并做一次完整相关门，不为每个小步骤重复全套预览。

详情交付阶段：7生产/5测试路径已冻结并独审通过，Root相关6文件211PASS；成功后的旧错误反馈清退原本已实现，审查误读已撤回，仅补既有行为断言，不记录为新修复。尚未正常激活。

后继App cbef49c9仅测试/说明已推原PR49，Root两UI文件303PASS、scoped ESLint/完整tsc通过，桌面/手机preview E2E120PASS；77生产/生成与629冻结仍同。原full default红/OIDC97未验继续保留。Root实际候选精确GET补证断开后的server registered、connector revoked/enabled=false且二者200/ID相同，配置保留已非仅源码推断。App只读可达片已完成并提交/推送6cdbb090e1070240cc62d0e81521027cc222d2cc至原PR49：三过滤窄例外保delete优先及撤销版本屏障，immutable readonly intent、所有命令callback与UI均拒，Composer/项目/Run资格不改，不做全列表N+1/猜provider命名。7真实RED后修复，状态文案另3RED后修正，Root最终原三文件160PASS、scope lint/build通过；原逻辑与状态小差分独审通过。隔离真实IAM浏览器桌面/刷新/390px窄屏三旅程成功，exact connector/server读取200，MCP零写、关闭回焦；开发态详情6–8秒不是性能达标，global connections/icon末端503保留。正常3314未切换，正式Reauthorize消费者等ownerartifact。

Platform三文档设计门已独审APPROVE，原墓碑/receipt顺序P2已通过六处精确句修关闭：fresh身份与原安全绑定先查原receipt，completed Reauthorize/Prepare跨后继Delete保原安全ACK，unknown/expired沿原状态；首次/重入实际业务才current/墓碑/CAS。Root授权唯一Platform writer task_b_api_postgres按已核精确路径清单实施current绑定、新身份纯本地命令、材料换绑、配置墓碑、正式v2 artifact/canonical schema及精确父evolution。仅本owner，排除IAM/A/正常资源/Git；真实PG与最终资源操作由Root冻结后执行。旧永久身份/refs、原撤权/PKCE/refresh/Runtime、历史wire oracle不弱化；消费者待owner固定提交后再接。

Root已用官方generateCanonicalDdl/readCanonicalCatalogAndSlotDigest在带marker的自有临时库事务安装与slot1读数，真实fresh target718dfff8e357405f6ce24323a64e6cc1bf1749f7804ba447cc68923e29c51f65；主动回滚并确认owner schema不存在，正常源未动。三输入冻结与私有receipt保留，Platform以此接正式canonical target和精确父迁移，尚未完成整片PG业务/迁移验收。当前纯内存新增两旅程通过不是实际PG。

后继真实迁移已跑：首轮原schema套件28PASS/3FAIL，定位SQL replacement把正则`$'`当替换元字符破坏旧父DDL；原helper改callback后，固定v2输入的原旧父迁移1PASS。两慢项定向复验rollback通过、drift仍30秒超时；固定368原父同项也超时，不冒全套绿色。新current精确父5组真实PG（exact/zero/multiple/wrong-owner/wrong-material）全PASS，成功保旧列值/永久撤销，坏绑定全事务拒绝且catalog/数据保持。完整新业务v3的private integration实际17PASS/12FAIL：窄read transaction遗漏新历史receipt reader绑定导致12项DependencyUnavailableError；已交唯一writer补正式composition。独审另抓普通connection GET/List未拒旧代/墓碑、Header active上限误计revoked历史、reauthorize原安全绑定无boundary读三处P2，沿原责任面最小修复后再冻结补验。源码尚未提交、BFF/App正式重连尚未接线；正常3314/服务/库未动，Goal仍active。

最终v4已关闭上述四处缺陷：Root冻结65非MD的完整private PG29PASS、personal PG11PASS/1原SSE-driver条件SKIP、四文件unit/contract/architecture124PASS；5迁移组的4schema输入保持承接，独立有限复审APPROVE，正式lint/type/build/format通过。原strict checker同一正例在精确368父与v3均15秒ETIMEDOUT，保原完整门红，不冒性能无损或全仓通过。Platform正式提交`2cf63945feecd49f5b79c3532bbd7cbc5b70a3f8`并推原远端codex/connector-icon-staging/GitHub Draft12，70精确路径，无main合并。Root核1093全部非MD输入等值该commit，774官方build产物已备隔离候选。BFF以clean7e4接正式v2 vendor及browser-private新操作，Public29/200与SQL原字节不变；89非MD冻结2220e3ea独审通过，Root独立artifact构建0、原三文件91PASS，正式contract1560PASS/architecture37PASS，默认门仍在原冻结一轮。App已实施原UI/命令，跨仓固定依赖等正式BFF提交后更新。

Root已激活隔离Platform2cf：退休自有旧候选进程组、同RR快照原生pg_dump、官方canonical d0→718、25表全部旧列值hash一致、新候选readyz200。只动本候选库/进程，正常3314保持；备份恢复未另验，不冒normal或跨owner原子升级。进程中断/所有权及最终handoff原子点经限定独审修正后执行。真实回执见本机测试验收B01-platform-2cf-paired-upgrade.json；新的App重连UI与真实浏览器旅程仍待完成。

BFF正式固定并推送`e3b5fb759ee89523918ac06ebf3a738b4df4e346`至原Draft17，94精确路径；89非MD冻结不变，5MD仅42行当前前缀、历史后缀逐字保留。默认2762PASS/3原SKIP/0FAIL，Public29原105条lint warnings保留；Root独立artifact全部1102非MD与正式commit相同，ready200。新后端配旧App6cdb真实IAM exact两读200/断开只读可达/零MCP写，6.934秒不冒100ms达标。App唯一writer接正式private profile、现generator及同源adapter窄路由，不造通用代理；新授权页面旅程待验，正常3314未切。

限域候选真实浏览器后继：API新建/取消/修改/刷新/删除成功，私有HTTP MCP公开服务实际声明/Prepare后已连接，改名及刷新保持。管理断开后个人connector已revoked，App三处过滤令保存配置无再打开入口，真实列表已空；断开后private server精确GET尚未实测，源码显示owner仍保其配置。不能仅解除过滤后冒重连，旧Prepare/OAuth/permanent revocation边界需owner先收敛，保旧凭据/执行refs不复活。Root裁定保单URL单配置体验：Platform currentConnectorId持久绑定、双CAS/receipt的纯本地新授权命令，建立新connector/newconnection，旧永久身份不翻回active；仅本人personal_remove允许，安全/管理员撤权不统一恢复。唯一Platform writer task_b_api_postgres先只写三设计文档，未授权Schema/wire/源码实施。配置删除保永久安全记录，配置材料沿原正式删除，不新增AEAD空编码；墓碑、partial unique、迁移唯一绑定与OAuth AAD重封须文档门独审。

#### B-15-CONTROL-PLANE-PAIR：先交付真实 MCP/API 控制面

旧Platform缺新版MCP必须availability字段，不能把新版App硬接旧服务或新增猜测fallback。复用已固定IAM b9a63c53、Platform36805356、BFF7e4ab1ce独立无Git元数据构建产物；原正常进程/端口/配置/任务继续保留。Root唯一资源操作者，本地独占单库三owner schema：IAM/P在normal只读RR快照data-only备份，各旧parent官方installer先建立canonical，恢复真实副本数据后各当前官方入口升级；IAM17→19、P21→25，原列全行值摘要均同，BFF fresh34空任务/outbox。data-only保canonical CHECK语法树，不篡改owner SQL或历史catalog oracle。新库身份/OID/marker、私密dump与逐阶段回执仅留本地；不是跨owner原子快照或正常升级。

真实既有operator密码登录和官方新native OAuth client注册/回读已通过，IAM/P/BFF独立候选ready200。沿受管Redis逻辑DB9：IAM独有prefix、App origin hash；当前P只PING，BFF仅PING/publish、无subscribe且fresh无AGUI，不启动Agent，不把限域判断推广到未来AGUI隔离。候选与normal同127主机，Cookie不按端口隔离，必须独立浏览器context。加密/fingerprint私密副本保原密文配对，BFF→P两purpose与P→IAM execution服务身份独立新生成；无Storage/邮件/Provider OAuth/Agent/Billing/E2B末端不冒完成。

正式消费者已固定提交App629ac5db3715546dacb484c0bf8ef0482e021c92，推原draft PR49：固定7e4原blob与digest，12 public generator正规生成，5独立contract不换源；保两父historical oracle的完整字节/操作proof，不导入SQL。既有calendar/RSS/runs沿正常1f700功能承接，AppSurface只必要薄桥，排除A engine/Run/display/control。139路径独审通过，contract479/architecture50、lint/types/build通过；Root相关详情211/Public29 232通过。默认首轮6973PASS/48FAIL/181SKIP保留；补双Redis变量后6文件130PASS，OIDC97仍被/app compile readiness阻断，正在仅补有限观测、不延长预算。16相关UI失败唯一App writer task_b_read_review仅两测试文件迁移，保缓存/主体/代际/清稿/不重放等断言，不改生产；OIDC诊断唯一writer task_b_safe_file_tools仅原系统测试文件。

Root已建立629ac5db精确无Git archive并offline frozen安装、1545输入摘要不变；仅退休旧候选Web进程组，正常3314不动。复用候选真实IAM登录的独立context，MCP设置打开成功，scheduled-tasks真实GET200且空列表完成，RSS表单可打开，无自动化写入。首轮列表截图仅loading并非成功证据，后继已等待完成。开发环境小样本页旅程约2秒/5秒，非100ms达标或生产p50/p95；Storage/System/models/billing/skills等503末端仍明确未就绪。

#### B-02-PG：Custom API 真实数据旅程

Capability 唯一 writer task_b_api_postgres，基线 d5708828；仅本功能 integration 测试/必要 fixture/INDEX，不动生产、wire、Schema、lock、Root/Git或正常资源。复用自有 PostgreSQL fixture 与 canonical installer，从真实 profile 管理服务进入精确版本 Describe/Acquire，核同名 env 冲突、跨主体/tenant、版本轮换/删除、取消和最终材料复核；IAM authorize 明确替身，不称真实 IAM。Root 独占实际资源执行/清理与 Git。此为补当前实证缺口，已有实现不伪造 RED，不把直接 SQL seed 当管理链成功。

交付状态：真实管理命令、加密和独占PG最终四组通过（9.06秒），独审无确定P0–P2；此前BigInt序列化测试错误以官方toJson修正，未删断言或冒产品RED。Capability 36805356 已推原PR12。IAM admission仍明确替身，尚非真实HTTP/Agent全链。

#### B-02-FILE-TOOLS：受保护文件工具恢复

Agent 唯一 writer task_b_safe_file_tools，基线2139674。先沿现FileEgress guard/aguard恢复Docker ls/glob/grep：rootfd/nofollow有界枚举、原名/路径先检查、完整文件bytes先检查后literal匹配，单次fresh Acquire与共享期限/取消归属保持；名称/遍历/结果预算及二进制/空pattern行为先在三设计收敛。写区仅FileEgress/Docker/对应测试与必要INDEX/CURRENT/设计前缀，无新依赖、wire、Schema、正常资源或Git。E2B公开list先buffer且无响应上限、commands.run强制login shell，不能直接套用为安全方案；真实E2B和公开直exec的PID/开始未知清理设计继续OPEN，不能据Docker收口B02。Root接手冻结独审与真实Docker验收。

交付状态：Docker工具8文件冻结，独审无确定P0–P2；Root相邻122通过/15原marker未选，真实Docker2.201秒通过，含13次fresh Acquire、安全列举/有限glob/literal grep、完整原字节与非匹配原名拒绝及撤权，自有容器已回收。完整默认3378通过/934资源marker未选（397.73秒），未运行项不冒资源成功；最终fullRuff393/类型/lock/contract及wheel/sdist通过，Agent bfd1e9c已推原PR46。E2B公开direct exec虽有tag选择，但未知启动与迟到启动竞态、parser前预算及显式依赖决策仍待，不能据Docker关闭B-02。

#### B-02-FILE-EGRESS：Custom API 原值文件出口

Agent writer 负责 sandbox 的 fresh 授权与完整 bytes 检查；主控独占 Git/Root/正常资源。基线 c43fc3f，固定 Platform44fcc5d 与 DeepAgents0.6.7。Agent 三设计已先补，范围及同步/异步/取消/预算/TOCTOU/无持久化边界见其 2026-11-01 前缀。允许 execution_environment.py、Docker/E2B/archive、内聚 sandbox/file_egress.py、对应 tests/support 与测试/INDEX/当前事实；禁止 HTTP、Run/control、事件/产物展示、Owner wire、lock、正常进程。Root 接收后独审及真实 Docker 复验。grep/文件名/真实 E2B 未证不得声称整个 B-02 已关闭。

阶段证据：focused108通过/6按资源marker未选，类型/Ruff/contract与sdist/wheel通过。真实Docker用本地明确授权替身验证容器资源限制、同Run绑定、fresh撤权/恢复、整文件与二进制原值拒绝、干净原字节、无环境继承及自有容器清理，1.726秒；不是正常IAM/真实E2B或对象存储全链。完整默认3354通过/1失败/934未选，唯一HTTP进程3秒冷启动时限失败，原两信号单跑2通过；保留原失败不扩大超时。独审发现E2B stream idle逐片重置导致总体deadline可能近翻倍（P2），已先RED后改公开SDK限时URL+HTTPX async整体传输期限并复审无新增确定P0–P2；并发QueueHandler日志原址净化通过，OS DNS executor不可强杀的清退越期限制如实保留。最终focused115通过/6资源未选，停写481份输入无漂移、full Ruff393/pyright0/build通过；完整3359通过/3 HTTP配置启动3秒时限失败/934未选，原3项单跑全过，不改门禁。Agent2139674已推原PR46，未合main/正常激活。



更新：2026-10-23（America/New_York；沿用户重新整理的目标实施）。**本节是唯一有效目标和 TODO；历史任务顺序及“模型／工具／积分全面暂停”不再作为新计划的默认约束。** 当前已进入实施；用户已明确授权受限真实模型、工具及积分验收，验收后集中 PR merge。实施包含真实模型、低风险工具和实际用量积分结算验收；真钱支付后置。本轮统一承接全部已提出需求，Skills/MCP纳入同一交付目标，不设旧任务、交付债或另一个收尾周期。历史记录仅保留证据。

## 2026-10-24 执行纠偏：先闭合真实 Agent 主链

### 2026-10-24 本轮实际推进：交付运行配置与真实产物子链

本轮后继实际证据：原生 ToolNode write_file→deliver 在实际默认 StateBackend、真实PG journal/checkpoint与Storage上成功，新连接恢复文件及原结果，同call重放没有新Storage I/O；normal资料库GET200真实空列表，未造正常产物。ADR-033确认采购依据是既有业务要求，不是额外门槛，但独立工具面继续推进。正常新建本人 QA DeepWiki MCP（无凭据，仅公开只读验收），owner prepare已成功且原Connection ready；App错误拒绝工具描述换行，使Prepare/详情502，已在原schema三处局部修复并正常HMR，原详情GET200，只读恢复未重发Create/Prepare，352focused及Node22 lint/types通过。进一步真实Agent→正常Platform检验：GetConnection成功、GetConnector得到PLATFORM_UNIMPLEMENTED，实际surfaces缺mcp-connector与mcp-authorization；尚未远端tools/call，两独占Agent库回收、库存94保持。下一动作先用实际已运行4c3853b配齐这两部署面，保留未激活8ff图标候选，不能直接重启到其Schema。原报价／10积分不改，未把这项内部接线缺口推给用户答价。原502/UNIMPLEMENTED、回归、修复后截图与具名下一动作均在ignored agent-delivery-normal-20261024；本轮无push/PR/merge。

App局部修复已本地提交 `f0740f3`，未夹带原导航诊断WIP；正常单文件与提交逐字相同，Agent/BFF/Billing原行/xmin核同；Storage原9094回执及业务实体核同，另新增20条正常Platform的skill_package/get_package_reference回执，未把包引用读取误称全库零写。刷新后原卡片及详情均已连接/GET200；后续整页刷新网络窗有truncated，只证明可见持久状态与已捕获成功GET，不作全窗零写证据；此前短窗一次GET且未重发Create/Prepare的证据完整。自建QA连接保留供下一次真实调用核验，无远端tools/call、付费模型或积分动作，未改其它连接器。

已定位并补齐正常 worker 原缺失的 Storage URL／对象来源／独立 kokoro-agent secret。先使用既有可信 Run scope 做只读正式 v3 身份核验，再确认无活跃 Run，仅优雅替换本方 worker；新有效配置只增三项、原工具选择只新增 deliver。其余八监听及四 owner 原行/xmin核同，派发仍 false，未改旧预占或费率。最新进程仍以 ignored/private agent-chain-normal-20261024/processes-after.private.json 为权威，旧 activation 的 worker PID 不再复用。

复用现有 Root 产物 smoke，以当前 Agent 源码／冻结独立编译的 Storage 运行真实 claimed Run → journal → Storage → MinIO/ClamAV → Artifact → 原字节下载 → Chat/outbox/终态。重复发布、失效 lease、扫描拒绝及跨 scope/tenant 拒绝通过；自有DB94→94、Redis原键保持、自有对象和临时bucket清理，正常进程和源码保持。模型／Billing未参与，不能代替正常付费 Run、模型驱动工具、浏览器产物显示或整体 Agent 闭环。首次私有副本 /var 路径与入口 canonical URL 不同未监听，失败保留并清理，副本 resolve 后按原断言通过，非产品故障／未放宽门禁。证据仅留 ignored agent-delivery-normal-20261024，Agent RUNBOOK 已记录缺配置仍ready这一坑。网关计价业务事实仍待答复，后续仍固定新会话→模型→工具→产物→恢复→积分流水，不转回图标／导航。

Agent记录与运行手册已本地提交 `4bfb5cc`；文档之外运行输入未变，原composition／deliver定向17项通过，配对后四owner原行/xmin再次核同，三个readiness均200；不替整体付费旅程或上线结论。


用户再次指出整体Agent迟迟未结束。执行问题是支线切换与当前事实分散：图标／项目／布局局部交付没有取代真实执行／资金／产物验收。立即以既有16项TODO的AGENT-1／CHAT-1／CREDIT-1为唯一当前执行切片；图标内部实现冻结，不把图片上传或像素修饰列成Agent主链前置，也不新增计划中心。

本轮开始时只读核验：实际Agent HTTP／worker为正常源码efa770c（执行源码b71e972），不是physical旧9a2679f；正常BFF 5a303f2的实际进程KOKORO_AGENT_ENABLED仍false。原模型证据execution=completed，input6366／output15／total6381明确上报，但cache_read／cache_write未上报；原financial ACK已经记录，不能将ACK本身等同capture完成。正常主链并非只缺样式：现冻结价含缓存差价，原attempt仍需有来源的准确结算；不得改旧快照、猜cache=0或重新派发原调用。工具／产物／正常完整旅程和集中交付亦未完。

下一执行只沿这条链处理当前网关有效计价／同次用量证据、原pending资金恢复和新调用可结算条件，再以受限新Run完成终态→刷新恢复→低风险工具／产物→积分流水回读。历史pending不能一概变成所有新Run的前置；若缺供应商来源则具体列明，不停在无限取证。已有正式receipt／预算／single-dispatch优先复用，不重写已验内核。本次核验未发模型／工具／资金命令，完整目标仍active；原始只读收据在ignored var/dev/agent-chain-focus-20261024。


当前实际推进（2026-10-24）：Agent 已提交 `8cc975e0850ebc990c436d3f2cff544c9424cbda`／HTTP7.3，只在六元组精确 ACK 为 pending_reconciliation 时输出 `model_settlement_pending`／retryable=false，原异常与资金边界保持。419非MD输入提交后核同、owner完整门／安装包／原SDK-HTTP-PG均验，正常进程未重载。BFF消费者已正规生成并补公开23.1及既有非空库具名CHECK升级；独占PG完整51项通过、库库存94→94，正文／snapshot／replay／重开连接／重复终态／事务回滚保持。BFF已提交 `b0f201e99c2ae3fa213942c5a909f47b06640a02`：782非MD输入七门0、原contract／schema完整父证明和架构read-only双helper负控保持，默认3项既有资源SKIP如实保留，最终PG51全过且库存94→94。App已提交 `5bc5096ac567fe3c46bdda881e09ffb7aa482db1`，固定此Git blob正规生成七消费者；新profile／唯一footer／正文／九语言145项通过。停写1152输入下contract306／architecture50／默认4877 PASS及lint/types/build/Docs均0；初lint命中旧git-ignored Playwright压缩报告，整体归档而非删规则后同命令0。浏览器零重试111 PASS／1既有mobile Settings焦点失败，trace保留，不勾整体UI／合并门。本次未重现原auth EOF，不冒称根因修好。正常BFF 32表263行已完整备份并实际独占恢复、具名CHECK升级／回退与正文/xmin核同；库存94→94，正常库／进程未改。旧canonical data-only恢复碰到历史deletion_member表缺席而停止，后改完整实际owner恢复、保留历史表并只核新CHECK目标，未删数据或放宽保护。本次切换已承接上述备份和恢复演练；一旦新码实际入库，回退应关闭派发／退producer并保留可消费新旧码的App/BFF与扩展CHECK，不把旧闭集客户端重新上线，也不改历史码以迁就降级。原调用／正常库／余额未改，不冒正常整链已完成；旧pending问题只限定其结算，不作为图标或所有新Run前置。

正常配对已完成（2026-10-24，本轮实测）：先对照当前进程与13份App目标源码基线，备份原字节并保留1239份非目标tracked；App不重启精确HMR。实际正常BFF具名CHECK已原子升级，32表263行及xmin保持；随后仅重启BFF和Agent HTTP／worker，均已就绪，Agent匿名readiness仍401，其它七监听、原环境及原Agent 23表／usage data核同。原会话正常打开／刷新无需重登，原URL与正文保留；990可用／10冻结保持。原generic历史不重写，新pending码只对正式具名事件显示，不冒新真实Run已经验过。源码基线Agent8cc975e／BFFb0f201e／App5bc5096；正常记录见ignored/private `var/dev/agent-chain-normal-20261024/processes-after.private.json`，后续只使用这个最新进程记录，不复用旧activation PID。相邻owner CURRENT已分别本地文档提交adcbd37／674fed3／949f51c，三个冻结非MD输入419／782／1152仍核同；未push/PR/merge或升Root gitlink。

仍未完成：正常派发维持false，实际网关计价依据和同次补证尚缺，原OpenRouter公开费率来源不证明当前转接网关实际成本，价格／原预占不改、不伪造cache=0；此前已异步询问该业务事实。同时保留移动端焦点缺陷：现有失败trace显示桌面恢复后焦点未满足，约0.7秒后发生整文档/app重载，前2ms有Fast Refresh rebuilding；这不足以断言只有UI handoff或只有HMR单一根因。下一步沿该既有UI-1缺陷核实重载来源，原断言与失败不删；不以单项重跑变绿称根因修复。正常冷启动仍见工作区占位，亦未冒称加载无感。

踩坑如实保留：本轮切换脚本在任何正常写入前被libpq不接受schema URI参数、遗漏terminal outbox状态、UUID路径拼接及第一次替换未命中拦住；已改成独立只读预检、精确归一化连接参数、核真实六态与UUID文本后再切换。它们是操作脚本错误，不归为产品修复或成功证据；实际切换、复查与浏览器读回均已独立核验。

## 1. 新目标

### 本次目标更新与执行游标（2026-10-23）

**本轮执行增量**：正常Admin已快进 `d221b18`，修复服务端准入身份被丢弃、壳从空身份重读造成菜单渐进出现。正常首文档5→11个菜单，模型页导航/刷新1项与另一标签App原会话恢复通过，无第二次登录；47文件361项及完整工程门通过、只读独审通过，原配置/九监听PID保持。此前App `7f2b9c5` 同主体核验保留内容修复继续有效。冷读数据空态、App占位及原始身份文案仍未关闭；原10积分pending、真实结算/工具产物仍待，未集中PR/merge。现Billing技术上支持未来totals-only费率，但须先核当前网关有效计价依据，不能删缓存价伪装成本或改原冻结事实。详见[当前事实首节](../../CURRENT.md)。原16项范围保持。

**最新执行游标（覆盖下列历史阶段的未激活／零调用描述）**：正常App `623eae8` 已包含短地址登录及侧栏首屏偏好修复，展开300/300、收起52/52、手机0/0正常实测；剩余占位差异仍待。正常策略/费率及一次真实模型返回保持，缓存量缺失的原预占仍pending。Agent最新本地 `b71e972` 承接 `c92dbea` 响应编号持久化，修复cost说明误作计量类别与完整SSE缺usage丢编号；默认2621 PASS、SDK/HTTP376 PASS、隔离PG图12 PASS及其余工程/包门通过。正常Agent已保数据配对b71e972：23表185行原列/xmin保持，HTTP/worker与浏览器回读通过，990可用/10冻结不变；原attempt无编号，现网关补查尚无可用证据，不补零或改冻结价。**下一步核实同次调用补证并接金融恢复，再真实结算和有限工具/产物；原16项不增加、不勾整链，不重开Skills/MCP循环。** 详细证据见[当前事实首节](../../CURRENT.md)。有限真实验收授权保持；未集中PR/merge。

**最新AUTH-1进度**：Admin `e35df21` 已清除旧独立登录页面，将控制台壳移到正式准入后，修正返回Product和恢复生命周期；正常后台读取及完整本仓门通过，未PR/merge。首次热更异常及正常多标签登录仍不冒称关闭。具体证据与下一步见[当前事实](../../CURRENT.md#admin-session-boundary-20261023)，本16项TODO不新增、不缩小。

**MODEL-1 已推进到正常真实解析（2026-10-23）**：用户确认现提供方由OpenRouter转接，后继按其精确 `openai/gpt-5.6-luna`／canonical `openai/gpt-5.6-luna-20260709`公开价配置，不再索要可公开查询的费率。实际公开目录200／468项，普通输入／输出每百万token USD0.20／1.20，缓存读／写0.02／0.25；严格大于272000输入的覆盖价已核，现4096context不触达。保7/5倍率与整attempt最终一次ceil，费用到积分仍是单独显式平台policy，不从目录凭空推导。App在线指南提交 `52baa59`，完整Docs check通过（45测试、5例、54HTML／17942内部链接，原大chunk警告保留）；价格来源不是已发布计价或已扣分证明。

System `49a5f8e5e2797ec2d1a6fcf8c5f398184821bf33` 修复健康过期无生产者的根因：原resolve按需复用有界metadata GET，provider／密文快照与health generation CAS、全局fence，公开发现GET仍零写，fresh down不被旧probe覆盖；无新服务／表／wire，不放宽freshness。真实RED503→200、37定向／完整owner263 PASS／0SKIP、fresh33断言23表及独审Approved。正常仅本方System已备份并ff／重载，配置字节和其余8监听身份保持、readyz200；无需DDL。正常当前租户Agent正式client resolve→精确revision／digest→受控Key领取→重复解析通过；旧2026-10-21观察generation1自动恢复到2/global8→9，重复零健康写，Key不回显。此为真实System／供应商metadata链，**模型生成、工具与usage扣分仍0，计价发布与完整正常Agent链未验，未PR合并，不勾整项**。原失败与本地收据留ignored `var/dev/product-real-chain-20261023`。

**正常数据与Billing已配对（2026-10-23）**：Agent canonical绑定 `bfff8df`、Billing绑定 `1fac9de`，两owner在同一事务内以RESTRICT重建，未动其他owner或Redis。冻结备份、原始恢复、canonical＋原数据恢复、故意失败回滚均经隔离实测，临时库94→94；正常Agent23表141行／Billing35表7行逐行哈希保持，余额1000。Billing正常已重载、readyz200，精确catalog为35表493列212约束102索引且差异0；原私有配置及其他8监听身份保持。正常浏览器刷新后显示可用1000、冻结0、积分到账+1000。首轮操作在DDL前因dump恢复重解析CHECK形式而被严格检查拦下，Billing自动恢复；改用原提交canonical基线后重新演练与独审通过，未放宽比对。另修复操作脚本停机后异常未进入恢复保护的问题；原失败保留。证据在ignored `var/dev/product-real-chain-20261023/owner-cutover-v2`。本轮未发模型／工具请求或新增扣分，未PR／merge，不勾整项。

### AUTH-1／CREDIT-1：内部认证纠偏（2026-10-23）

IAM `2f881d0`／SDK0.17与Billing `c158270`已替换该跳机器OAuth，原业务wire/Schema/Run/预算语义不变；完整门、真实PG/source-dist及实际receiver配对通过，正常未统一切换、未PR/merge。用户允许重构而非叠补丁：余下Agent→Platform→IAM两跳保留现在线权限来源，仅替换机器身份并删除兑换/缓存/内省和旧配置；不把后继barrier/claim扩成此片前置，不假称它已完成。原ADR已澄清，16项TODO不增不减。证据与未完成项见[CURRENT认证纠偏](../../CURRENT.md#auth-realignment-20261023)。

**立即下一步**：Platform `4c3853b1062a9e22c9be6c059720a092805cb63f` 已完成 Agent→Platform 接收端专用服务身份和独立 auth profile，MCP principal v2 正式绑定 service/key；原 BFF 六用途、System global OAuth、业务 wire 保持。完整静态/契约/格式/build均0，174文件2661 PASS/500资源SKIP；相关隔离PG/生产装配52 PASS/4既存旅程SKIP、真实文件→Nest HTTP31 PASS，实际compiled ingress/admission→IAM Nest/PG/Redis验证4次正式当前权限且零OAuth/JWT内省，撤权/轮换/错tenant/错binding/取消拒绝保持；912输入冻结无漂移、两次资源库存94→94、独审无确定P0–P2。正常未切换、未PR/merge。Agent 消费者现已提交 `d20f608b6e217dea93f51ebd5880d84a567b32fc`，固定该profile并删除OAuth exchange/cache/旧配置，原Connect/Run proof/总deadline保持；完整默认2579 PASS／853 marker未选、类型/格式/lint/contract/build及208份安装源码核同通过，旧build混入退休模块的安装失败已clean重建纠正，418输入无漂移、独审无确证P0–P2。实际隔离Agent→compiled Platform→IAM组合现已通过14项检查、8次当前权限调用且零OAuth交换/内省，轮换/撤权/错tenant/摘要/超时恢复覆盖；数据库94→94、自有Redis键0。Agent lease与BFF绑定仍为具名fixture，Storage只验readiness，未发模型/工具/积分，不冒正常整链。正常IAM6238371/Platform4c3853b/Billingc158270/BFF5a303f2及Agent HTTP/worker d20f608现已配对运行，五HTTP readyz200、worker初始化完成/持续存活且检查无错误；App/Admin/System/Storage未动，原7条BFF entry与既有凭据保留。受管Agent schema只读核验通过，原失效连接修正；原3个terminal Run保留，启动前后无nonterminal/模型attempt，BFF派发仍false。后台刷新及1条真实业务模型读取通过，临时空态/加载与完整多标签登录仍待。两份旧owner精确源码/离线lock依赖回滚准备完成，本轮六仓fetch无未承接远端main提交。下一步发布精确计价、受限开放并验正常模型/低风险工具/产物/整数结算，再完成旧scope/client正式退役；不重新设计权限源或展开Skills/MCP页面循环。原16项TODO不变，真钱支付不做，不能把接收端完成当整链完成。

**本次刷新：唯一目标仍为正式产品整链闭环，状态进行中；下面16项TODO是唯一执行清单。** 登录、业务模型配置、会话Agent优先，页面／API对齐和其余既定需求在同一轮交付。真实模型、低风险工具和整数积分验收已授权；真钱支付不做。旧Skills目标标题、历史暂停语句、重复盘点或新增示例业务均不改变此范围。

**当前执行点：System正常解析已恢复，继续正常执行配对、计价发布与真实整链验收。Agent `bfff8df05112a88e04645d10c398982ae3946518` 已本地接完原finalhook预算授权、唯一派发、同流usage／实际归属与金融ACK，不再列为待装配。Worker ec53a01有界公平恢复、abd1186c独立关联／逐事件ACK、aedba7b内部金融consumer及189c8ac／Billing1fac9de历史sealed均复用，不重做。** BFF `5a303f2`／internal1.3仍为正式消费者基线；下一步沿正常登录→业务模型选择→真实供应商→低风险工具／产物→实际Billing整数结算及回读推进，不新增用户token回程／服务或金融seal屏障。

本次新增证据：418输入完整八门0、默认2588 PASS／853 marker未选，184真实PG／323 SDK及金融HTTP、36隔离四方恢复检查及209份安装包源码核同通过，独审Approved。原生图十向量含JSON/SSE、原生工具两轮和取消，但财务ACK为具名fixture；实际四方仍只QA预算释放，不冒正常真实模型用量扣分已验。首次失败及原时限偶发明确保留，详情见[CURRENT首节](../../CURRENT.md)。

| 当前推进顺序 | 最新状态与可验收出口 |
| --- | --- |
| 1. 同一次执行的积分结算 | **Billing、BFF及Agent金融消费者、持久ACK／崩溃恢复、Worker及首次唯一派发／同流用量装配均已本地验；正常真实供应商与实际整数扣分仍待。** BFF `5a303f2`／internal1.3固定Billing23ff719／exp10，778输入七门0、contract1008／默认1694 PASS（3原资源SKIP）、真实PG1及隔离实际四方30检查通过。原key恢复、miss和冲突无资金变化；Agent abd1186c已接逐事件持久ACK／关联与恢复：410输入八门0、153真实PG／36隔离组合检查及205份包源码核同；实际仅确认未派发的QA预算释放，不授新派发许可，不冒实际模型扣分已验。Agent `aedba7b`／BFF1.3金融消费405输入八门0、33隔离组合检查已验；Agent189c8ac／HTTP7.2历史读取和Billing1fac9de固定消费已验；原bytes／独立head完整性保持，不新增金融ACK屏障。 |
| 2. Agent正式执行链 | **装配与原生SDK／PG已本地验，正常整链待验**。bfff8df已接唯一派发→同流usage封口→金融ACK，未知拦后续模型／工具，原生图十向量含两轮write_todos和取消；财务端具名fixture，不替代真实供应商／Billing计价验收。 |
| 3. 正常用户与后台完整旅程 | **待真实验收**。正常登录／续期→业务模型选择→首发与流式→低风险工具→产物→刷新恢复→余额／流水／后台回读，覆盖取消、重复回执及未知结果。 |
| 4. App差异与统一交付 | **仍在同一轮**。按Manus实测完成原TODO中的会话／首页／项目／设置及在线Docs；本地审查和验收通过后集中PR merge、Root精确组合并核正常生效，不等待CI、不绕保护。 |


**唯一目标：按 Manus 实测完成正常登录 → 本业务模型选择 → 会话 Agent → 低风险工具 → 产物及历史恢复 → 实际用量整数积分结算，并完成对应后台管理；随后在同一轮完成首页、项目及下面全部既定 TODO，自己验收后集中 PR merge、精确组合并让正常环境生效。** 不新增另一轮“旧任务收尾”，不以局部接口／测试／已合PR代替整链完成。

**主线顺序不变：登录 → 业务模型配置 → 会话 Agent 完整链路 → 工具／产物 → 真实用量整数结算。** App 页面、交互与可观察 API 差异贯穿实测和验收；Skills/MCP 复用已有成果，当前旅程依赖或明确缺陷才补齐，不再作为主线前置验收关卡。真钱支付不做，不新增团队或示例业务，不全局放开无限执行。

当前进度：正常无感账户初始化和后台非现金充值子旅程已验；模型精确配置／候选列表及App／Admin消费者已验；IAM／Billing／BFF具名Run预算与Agent正式预算消费者78dfda5已验，同admission结算应用796bfce、正式HTTP deab94e及BFF结算消费者ebe7ca5已验。**BFF恢复5a303f2、Agent消费者aedba7b及持久金融恢复abd1186c已本地交付；Worker有界恢复ec53a01也已交付；现在接原finalhook预算授权／唯一派发、同流真实usage及认证归属映射，最后验正常用户和后台整链。** 既有阶段源码与真实／fixture证据分别见CURRENT首节，不再把已验预算入口或结算应用列为待重做；未勾AGENT-1／CREDIT-1整项。

AUTH-1当前候选：App e48adb5已提交登录／refresh的可信issuer sid连续性，原生验签、原用户／tenant、单次交换、双CAS和失败清理保持；最终1143输入无漂移，完整App十阶段0、4773 PASS／0SKIP（单worker完整test）、108 preview零重试及Docs全门通过，四MCP WIP原样恢复、独审Approved。正常未激活；旧无sid cookie不兼容，不清业务数据。此次只闭合登录子片，不因此增加Agent所需token或额外用户授权旅程，整项AUTH-1与正常产品验收仍按原完成条件。

IAM预算授权当前候选：67a3c0e已本地提交，internal／SDK0.16替换旧用户token body／Session前置，复用现签名proof／强制BFF Run及当前成员资格；496输入无漂移、九门0、1505默认PASS／0SKIP、31真实HTTP／PG／Redis及1 clean包仓外consumer通过，独审Approved。原件／包SHA与失败／恢复证据见CURRENT首节；SDK仅说明修正16ee2eb已交付；Billing d65d709固定该clean包，exp8／交付commit干净树五阶段全0／378输入无漂移，verify1786 PASS／561默认SKIP、真实PG228／source-dist10／fresh Prisma／生成检查通过，actual Agent＋Billing＋IAM隔离22检查通过。BFF0082b5c已固定Billing d345025／exp8，内部1.1，769输入无漂移／七门0／actual四方25检查通过；正常未激活；Agent消费者78dfda5及结算应用796bfce已本地验收，Agent结算消费／持久恢复、worker装配与真实整链仍待，不勾整项CREDIT-1／AGENT-1，不新建App授权旅程。

**认证最新裁决**：Run不需要用户token；执行使用内部服务身份与可信用户／租户／Run绑定。未实施的App额外Billing grant＋BFF回App取token提议撤回，不作为执行前置。App sid连续性是登录修复，不等于Run权限、消费grant或任务必须随浏览器登录过期。后继复用现IAM／BFF／Agent正式执行证据，保当前权限核验、具体消费意图绑定和预算事务；机器token本身不授权任意用户扣款。历史“App消费grant”实现游标不再直接实施。

**本次续行要求（2026-10-22，更新）**：不改范围，不重做已验proof和预算入口。Agent正式预算HTTP消费者与持久化授权已在78dfda5本地提交；399输入无漂移，完整八门0、默认2460 PASS、仓外锁定hash离线安装和200份runtime源码包审计通过，另有7真实PG／29隔离四方检查。首完整独立inventory漏4资产的47FAIL已按原exact oracle补齐，失败保留，不放宽门禁。Billing结算必经Credit跨有效期余量修复已在e558728本地提交：17专项、239真实PG、source/dist10及完整owner门通过，379输入无漂移；不复活过期额度，也不以原语修复冒实际用量结算完成。**立即下一步：Billing结算应用796bfce／正式HTTP deab94e及BFF消费者ebe7ca5已验，接Agent固定结算消费者／逐事件ACK与持久恢复 → Agent worker共享proof／预算装配 → 原唯一派发 → 同SDK流usage封口及seal后崩溃恢复 → 正常页面及后台整链验收。** 最后才解除当前finalhook拒绝，避免制造只预占但执行／收费未闭合的正常路径。验证覆盖关闭浏览器／用户token过期不阻断已授权Run、跨租户冒用拒绝、重复／晚到响应不重复派发或扣分，以及取消、未知用量和恢复；不增加用户可见授权步骤。模型、低风险工具与积分按限定范围真实验收，真钱支付不做；随后完成本轮其余16项，集中PR merge及正常生效。

执行游标（对应原 TODO，不增加平行清单）：

1. **CREDIT-1 已完成的子旅程**：App切片已保存并配对正常服务，当前租户正式后台非现金充值→严格回执→余额／流水回读及两页刷新通过。正常仅一笔POST201；原命令重放的资金幂等另有真实隔离PG证据，不冒称正常页面已经故障注入。此子旅程不另列为剩余任务。
2. **AGENT-1／MODEL-1／CREDIT-1（当前执行点）**：正式计价管理、policy2整数预算、rate2精确System修订绑定及BFF/App/Admin三消费者已本地提交和验收，不再为此重开盘点。预算方案已替代额外供应商成本上界保证，unknown／超预算仍保留资金和证据、pending并停止同Run后续派发。Agent可信prepared、Billing固定消费者及首次预算预占业务及正式预算HTTP均已本地交付（f61a5d2，POST原held回执、GET本人当前四态）；当前接可信用户／Run消费关联及正式Admission API消费者→唯一派发→真实usage封口→一次整数结算，沿现owner、原幂等／租约／取消和single-dispatch，不新增服务或兼容层。IAM67a3c0e已原位完成具名Run授权／SDK0.16及完整工程、真实HTTP31与clean仓外consumer门；Billing d65d709已固定clean SDK0.16并从已验证prepared事实重算原model-admit:1摘要；完整门、真实PG228、source/dist10及actual Agent＋Billing＋IAM隔离22检查通过，未产生真实usage/capture。BFF0082b5c已完成独立Agent内部预算通路、原提交者来源和exp8消费者；完整七门及实际四方25检查证实无receipt退休拒绝、原receipt退休后恢复且唯一预占，未运行真实模型／工具／usage。Agent短时proof供应商现已在bd287d5交付（390输入无漂移／默认2419 PASS、真实原生signer/JWKS与PG的四方27检查通过）；正式预算响应消费及pending恢复已在78dfda5完成本地源码验收，完整八门／2460默认PASS／仓外安装／7真实PG／29隔离四方检查通过；结算应用796bfce／正式HTTP deab94e及BFF结算消费者ebe7ca5已验；后继接Agent固定结算消费者及持久恢复，再接worker装配→原single-dispatch→同流usage封口及持久恢复。BFF由自身持久提交事实派生消费主体，不冒用IAM／Scheduler凭据，不改变公共AG-UI，不新增App回程broker／服务／token-exchange。普通Run assertion／管理员发放权不等于消费许可；内部服务身份、当前用户权限与该次具体消费意图分别核验。正常计价配置和源契约配对激活仍待，不能用QA价／quantity=1或纯函数冒实际收费。
3. **AUTH-1／CHAT-1／AGENT-1／UI-1／API-1**：由我走正常登录、选模型、首发／流式交互、低风险工具、产物、刷新恢复和扣分完整旅程；按 Manus 实测修页面、交互与API差异，不让用户反复代测。
4. **其余原 TODO／DOCS-1／RELEASE-1**：完成同一清单的首页、项目等既定需求；同步 App 在线文档，自审和完整验收后集中 PR merge，Root 只 pin 已合精确SHA，核实正常环境生效。不等 CI，不绕强制保护。

本次新增证据：BFF `5a303f2003fabeb50376c7f7e1f66f0d163adebb` 本地干净提交，固定Billing23ff719／exp10的十一操作，internal1.3 raw SHA256 `4de1a6c7564f3a994d879cfc93588021c5ef4aeebbcc89959fa574d5b6f16d39`。778输入冻结无漂移、完整七门0，contract1008／architecture36／默认1694 PASS及3原资源SKIP，39定向／真实PG1／隔离实际四方30检查通过，独审Approved。仅新增recover，原十操作与create proof／settle保持、Public原字节和旧内部整图保护通过，无SQL／依赖／兼容层。真实BFF/Billing/PG在Agent和IAM验收进程关闭后仍恢复原ACK，原key／miss／冲突十表含xmin不变；只QA100发放／10预占，无真实usage或capture，Chat源seed／签名JWKS fixture边界明确。库94→94、自有IAM键清理，13仓fetch成功／main无新增，正常配置资金服务保持。后继Agent金融关联／持久ACK和正式历史sealed读取及唯一派发／真实用量仍待；不重开已验组件，不勾整项完成。

目标工具只允许修改状态，旧 objective 标题暂不能原位改写；此前替换请求被“存在未完成目标”限制拒绝。本次更新现有执行目标与 TODO，不重复创建目标、不为换标题虚报 complete；目标保持 active，本节及下面唯一16项 TODO 是实际执行依据。详细阶段证据统一维护在 `docs/CURRENT.md`，历史暂停要求不重新生效。

让 Kokoro 的**正常登录 → 新建任务／进入会话 → 选择本业务模型 → Agent 执行与交互 → 产物呈现／持久化／恢复 → 对应积分与历史**成为一致、可验收的产品旅程；先打通会话，再对齐首页与项目，持续按 Manus 的实际页面、交互和可观察 API 校正。在线文档归 App 维护，随同实际发布版本对外可读；内部工程资料单独受控发布。

- **Manus复刻是实现与验收基准，不是泛泛参考。** 每个功能先实测对应Manus页面和动作，读取当次浏览器可观察的API请求／响应，再按明确证据实现；覆盖布局、CSS、组件层级、菜单／弹窗、切换／滚动／焦点、路由、空态／错误和恢复。品牌与已确认业务差异单独记录，不自行换设计。
- **API设计必须先看Manus实际接口。** 记录方法／路径、查询和请求体、返回字段／类型／可空性、分页、状态码、错误、动作先后与可观察的幂等／恢复语义；对照Kokoro正式契约逐项实现并验收。不先按旧代码自行设计，再宣称对齐；需要改契约时在现owner内同步重构消费者，删除被替代入口，不叠加兼容旁路。
- 可观察的产品／API行为与内部实现区分：Kokoro仍遵循已批准的owner、受信身份与协议边界；未观察到的Manus行为标“未核实”，不猜后端数据库、锁、私有鉴权或计费算法。具体差异有证据、有理由、有记录，不冒称完全一致。
- 使用现架构与 owner：Web 同源 adapter → BFF → 实际 owner／Agent；协议／Schema 各有唯一事实源，正式生成消费者一起更新。不复制一套 Manus 风格旁路服务。
- “组件通过”“代码候选”“正常已加载”“用户完整旅程通过”“PR 已合并”是不同状态，逐项记录；不再合并成一句“全部闭环”。
- 团队新能力、真钱支付不列入本轮实现。保留既有团队权限，不把团队／租户与项目混为同一事实。

## 2. 本轮执行边界与事实快照

- 本轮已启动主链实施。正式验收纳入真实模型请求、验收数据上的低风险工具执行及对应真实用量扣积分，不再只靠模拟链路。先核后台模型配置、当前租户／身份、计价和余额；设有限请求量与运行上限，不开无限循环／自动重试。外发、删除、发布等额外副作用按具体动作授权，不因工具链验收一并放开。供应商模型调用费用与用户真钱充值支付分开，真钱支付仍不做。
- 真实验收使用明确标记的当前租户验收会话／数据，记录 run、精确模型修订、真实用量、结算ID与积分流水；测试充值有正式权限／审计，不修改计价来伪造扣费成功。用量先保精度，在约定结算边界统一取整；取整方向、倍率与最小扣分以正式计价规则为准，列为实施前核定项，不凭参考产品猜测。
- 本次不全局开启所有业务执行开关；代码实现、受限真实验收和正式开放分别记录。
- 本轮已有成果已集中交付：IAM PR4、Platform PR11、System PR1、BFF PR16、Admin PR4、App PR45均已merge main；本Root提交聚合六个已合精确SHA（见CURRENT交付表），不再把已发布候选列作待PR。正常代码配对证据保持；真实Agent／用量结算及全16项尚未完成。
- IAM原已部署登录并发修复已在身份候选9a6a01c承接并随PR4合入main aeb3f32；八门1522 PASS及真实Session/OAuth19 PASS证据保持，正常已加载。它是代码承接与交付问题，不是让用户重新取token。
- 真实外部Next→BFF→IAM/PG/Redis→Platform/PG已由主方独立复跑：18请求、五组PASS，三类身份、tenant/project隔离、伪造头、撤销及精确绑定/CAS/replay/tombstone通过。自有库94→94、Redis自有键0→0、进程退出；不外推Storage/工具执行。旧startup失败收据保留，当前入口不再标未接通。
- App 最新交付候选 `cac62fe` 完整七门通过：248文件4709测试PASS／0SKIP、默认build／构建后types通过；交付输入冻结无漂移。前一 `b1dd711` 基线另有108项preview浏览器回归，本次未重跑整站Playwright。旧Next夹具失败收据保留，已确认的测试loader传播问题有回归承接；不把未复现的原JSON EOF故障称已定位根因。正常App现已加载 `cac62fe`，IAM／Platform正式配对已完成；完整正常产品旅程仍待验。
- 两 owner 正常库38表备份恢复已核逐行保持；原 owner canonical＋全部备份 data 的演进演练通过，目标41表且新增表为空。正常库现已按同一正式入口完成演进／重载，最新冻结备份亦恢复核对通过，原38表逐行精确保持、新3表为空。直接恢复 deparse 后的 CHECK SQL触发严格 catalog 拒绝等原失败日志保留，未放宽 owner 校验。
- 最新已落盘同步收据显示 Root＋12子仓非递归 fetch 全部成功，13个远端 main 均无新增；这只代表已抓取远端，不代表本地候选已合 main 或正常服务已更新。
- 原五个草稿PR均复用更新并merge，IAM新PR4亦已merge；本Root提交提升六owner精确gitlink，公开门户退役Root旧78文件、只在App维护。GitHub CI实际因账户付款/额度未启动，不记绿色；按用户授权不等待、不绕保护。

### 本轮主链实施证据（2026-10-21）

- 已实测 Manus 首条消息、产品模式菜单、实际网络输入输出及会话刷新恢复；脱敏证据维护在 App `docs/manus-reference-audit-v2.md`，原始材料保持本地 ignored。
- App 候选已修复新建空草稿错误读取归档、普通聊天首发模型选择缺失、目录分页／失败恢复／主体退休；主方复跑5文件179 PASS，typecheck通过。未正常加载、未完整浏览器验收，不标正式生效。
- 已复用原有私有模型配置，经 System 正式 HTTP 命令创建提供方与共享模型修订、发布并绑定当前租户 chat 默认路由；未重复索取或回显 API Key。后台页面已回读一条真实业务模型。当前验收修订使用4096输入上下文／256输出上限作为保守执行限额，不宣称供应商模型能力上限；该配置操作没有发出模型／工具请求或积分写入。随后正式 OpenAI SDK 单次限额探针成功，真实用量19 tokens；它只证明上游连通，不是产品Agent run或积分结算证据。整链仍待验收。
- 发布初次因执行边界未填写被正式409拒绝；保留草稿，以CAS补齐限额后发布成功。未绕过校验或直接写库。
- 管理页刷新复现返回 `/app`，已定位：服务端active-only准入先拒绝待续期会话，原浏览器续期组件尚未挂载。Admin候选改同URL无业务数据恢复壳，复用原生CSRF续期并重新核验管理员，正在独立审查／补负控；未正常加载，不以一次成功访问宣布修好。
- 积分零账户初始化已核实 Billing 存在正式幂等PUT；BFF候选已固定正式发布物，新增显式初始化PUT，GET保持只读；主方完整契约门发现治理元数据遗漏，独立审查发现非canonical路径绕过必需JSON，均已修并复核，正在最终完整门。App消费和真实当前租户旅程尚待，不用假0遮蔽失败。

### 当前主链推进（2026-10-22）

- **CREDIT-1 BFF与后台消费者已本地停写提交，App正式同源通路及正常充值／用户回读已验。** BFF `c48a9bca07a2bb48fb5db46272ff71aab90e14ce` Public22.4／183，完整七门通过及最终契约912 PASS；真实编译BFF→Billing／独立PG资金效果通过，IAM／session为夹具。Admin `c162f7edfee33ee0e9c20cc1db74443c3d20668c` 固定42消费，真实Ant确认流程及8个hook负控，完整303 PASS／0 SKIP、155冻结输入无漂移；旧grant入口及独占死分支退役，不添加兼容转换。已修畸形错误导致清原意图和身份退休漏取消／漏分支P2。App 9b9ec34已补齐两个具名路径并完成4721测试及108预览回归；四端正常配对后，当前租户1000非现金充值及用户余额／单笔流水刷新回读通过。尚未push／PR／merge；下一步Agent资金链，不以充值通过称CREDIT-1整项完成。
- **CREDIT-1正式非现金发放owner已验，接BFF/Admin及AGENT-1资金链。** Billing本地提交 `90929ef316470f2e9de9eda05d5510761637bd6e`：唯一正式POST、现账本／审计／双身份幂等，无DDL／支付或余额旁路；跨effective_at重复入账P1先真实PG RED后用一次DB时点修复。新8项真实资金旅程、相关Credit真实133 PASS／0SKIP和source/dist8 PASS／0SKIP；完整verify1628 PASS／509资源SKIP，341输入无漂移、fresh Prisma/HTTP生成drift通过，临时库94→94。独审无剩余确定P0–P2；旧治理map退休键已由正式26操作及集合相等承接，原失败日志保留。后继接BFF当前管理员／tenant收款主体资格、后台表单，再完成Agent授权→唯一dispatch→实际usage封口→整数结算。未push/PR/merge，Root不提前pin，正常租户尚未充值／扣分，owner验收不是整项完成。
- **当前执行切入点：Agent资金授权与usage封口，而非追加MCP验收。** 源码核实 Agent main9a267／候选c2c7cf9均在prepare后固定拒绝无Billing consumer；正常Billing Nest只挂Credit/Commerce。候选现受控取钥不需重发BFF HTTP、System6.0两操作对当前6.1等价；主方本次focused191 PASS、lock/Ruff通过。取钥候选可复用，不重写；逐attempt授权、唯一dispatch、实际usage2封口及Billing实际结算仍待接通，保护不得删除。
- CREDIT-1计价内核修复已本地提交Billing `b4dda148767f31df12d1d679cbeb2a1237d7c16a`：整attempt汇总、精确倍率／换算后只ceil一次整积分，再×1m记账；新策略attempt-credit-ceil-v2拒旧micro-ceil执行，不改历史。主方最终334输入无漂移，完整verify全0（1580 PASS／501资源SKIP），相关真实PG38 PASS／0SKIP、临时库94→94，compiled六边界通过。独审P2测试保护退化已修。没有正常充值/扣分/模型或工具请求，未PR/merge，Root不pin未发布提交；本slice不是CREDIT-1或AGENT-1整项完成。

- 集中PR与当前门已收口：六仓main和Root精确组合见CURRENT交付表。Platform当前d8c4410完整十门926输入无漂移，默认2615 PASS／500资源SKIP、真实639 PASS／9 SKIP；App后续仅Docs增量，44文档测试、301契约及构建/链接通过。旧Root门户逐项核迁后删除，唯一公开维护位置为App。此前一次严格checker子进程超时保留，未改断言/timeout，不冒根因已修。

- MODEL-1提供方刷新／选择链已正常浏览器收口：System `845cf46`→BFF `e461d51`→App `cac62fe`→Admin `1f9021a`按同一精确发行物配对。主方App七门4709 PASS／0SKIP、Admin七门274 PASS，1240／149输入无漂移；独审无剩余确定P0–P2。实际页面4次上游GET全部200／28唯一候选，搜索、刷新保搜索和已确认行、修订下拉选择及取消无保存均通过，原发布修订仍1条，零业务mutation。期间Product原生续期POST200且仍在模型页；不据此称多标签登录竞态全部完成。旧错误标签不再参与验收，新正常标签已自助打开；原网络窗口完整，截图及脱敏收据留ignored。App初次新fixture可选signal类型错误保留，唯一测试形状修正后新冻结完整重验；没有放宽tsconfig、断言或真实预算。本次未重跑整站Playwright，不称Agent真实执行、价格／能力自动识别或完整积分结算已闭环。
- 上游模型发现BFF `e461d51`／Public22.3/182已主方独立全门并正常加载：911契约、1590默认PASS／3原资源SKIP、36架构PASS，780冻结输入无漂移，独审非200 decode后deadline/abort缺口已补真实回归。新接口只供管理员、System独立管理credential与可信上下文，旧181项完整字节保持；Admin/App单pin已配对并完成正常按钮实测，见首条。交付前非递归fetch Root及实际子仓／交付对象库全部成功，远端main无新增；不做无关分支清理。
- 当前租户积分无感初始化已正常浏览器验收：两条只读缺账户404→正式幂等PUT200→summary/ledger200，同一账户、可用／冻结0、空流水，未造免费余额。根因是已合Billing `158579f`未重载，旧进程缺PUT；新源码首次启动又命中过时node_modules Fastify5.12.1／5.12.4类不一致。仅原lock离线frozen依赖重建＋Prisma原生成后正常ready，原Schema／环境不变。充值、真实用量扣减与后台资金管理尚待，不能据本次0余额页面称积分整链完成。
- 正常配对已实际执行：新冻结备份经隔离恢复逐行相等后，IAM原生具名check/apply/check与Platform原installer通过，38→41表、旧38表指纹保持、新表为空；IAM `9a6a01c`／Platform `d8c4410`与App `b1dd711`源码FF配对，沿原配置重载ready。原管理员浏览器刷新 `/manage/models` 身份与业务模型仍在，无新登录／权限改变。此证据不代替多标签自然过期、Agent执行或积分结算。
- MODEL-1补充：提供方模型发现与本地目录刷新是两件事。上游支持模型列表时，由System使用已保存的密钥读取并向后台返回候选，选择后复用现有共享模型／业务组合流程；刷新不自动覆盖已发布修订、默认项、执行限额或计价，密钥不下发浏览器。上游未返回的能力／价格不据模型名称猜测。System正式上游候选获取已实现并正常加载，设计／API／数据边界已落现owner文档，不新建表／服务。BFF沿原管理员模型管理GET新增窄消费，Admin显式获取／刷新和原始模型名选择均已实现，正常配对及完整验收见本节首条；不外推为Agent执行链已验。
- System `845cf46`／6.1已本地提交并正常加载：主方完整`pnpm verify`exit0、255测试与fresh-schema33断言通过，215输入无漂移、测试数据库前后相等。v1真实DNS拒绝保留；v2部署侧精确主机许可已独审／负控及真实验收，正常owner经已有密文领取后GET上游返回28候选、原模型存在、no-store且不回Key，未推理／工具／扣费。Schema和其他环境值不变，仅为当前提供方添加精确主机许可；BFF／App／Admin已配对并完成正常按钮读取／刷新／候选选择验收，见本节首条。
- BFF `efe0ed8`：积分显式幂等初始化已提交，七门全部exit0（默认1578 PASS／3原资源SKIP；契约909 PASS），独立审查P2已修；正常服务已载入同SHA，环境配置和canonical Schema保持。尚未发PR／merge。
- Admin `0c3e390`：同URL原生续期恢复、真实me的200／403／401／503边界和正确跨basePath导航已提交，独立审查通过，30文件261测试、lint／types／contract及默认build通过。首次build因候选node_modules外链超出Turbopack root失败；仅在候选离线frozen安装解决，产品源码冻结无漂移。正常服务已加载；真实浏览器刷新仍在`/manage/models`并回读业务模型，但该次没有证明access已过期，多标签／自然过期旅程仍待。
- App `b1dd711`：无感积分初始化、模型首发选择与目录失败恢复、空草稿归档、公开Skill入口／个人删除／MCP重连候选已统一本地提交。主方完整七门exit0，246文件4693测试PASS／0SKIP，默认构建与构建后types通过；独立preview桌面／移动Playwright108 PASS，零自动重试。1237输入经完整门保持，E2E仅Next自动dev类型引用变化，经原typegen恢复；提交前只补三份文档，原runtime／contract／test／lock字节不变。原缺Redis、一次并发JSON500和依赖外链构建失败保留，未复现的500不记根因已修；已修真实Next多preload传播与有界脱敏探针。正常App未加载，未push／PR merge，不把preview门冒正常租户和Agent闭环。
- 最新Agent源码的真实System resolve→受控credential领取已验，未回显Key；但正式模型hook仍包含“Billing未发布”的无条件授权失败占位器。接下来在既有Agent model-call状态机和Billing Metering内兑现usage2 Admission／实际证据结算，不删除该门直接放流量，不以SDK连通探针或手工扣分冒充Agent闭环。整数扣分在同attempt全部真实用量聚合和冻结倍率后统一ceil为整积分，再换算账本micros；7/5保持正式配置。
- 已确认Agent HTTP／worker与Storage、Billing正常进程存在，后续复用并按精确版本配对，不重复启动基础设施。所有13仓非递归fetch成功；各子仓remote main均已包含于当前候选基线，Root另有已合历史文档／gitlink更新待最终集中集成，不覆盖现WIP。

## 3. TODO：当前 Goal 进度与剩余顺序

<a id="goal-progress-current"></a>

### 2026-10-28 当前增量与执行游标

**2026-10-28 最新正常与当前游标（覆盖下方旧阶段，Goal ACTIVE）。** App `01a1ce337926dda33f28d826a1742ebcea078c2f`／BFF `51e049df72c1fb2fe82b9114135c2fdc1a3450d9`／Platform `94e574c68d6c972078b661fa7d917dab90c71042`／Agent `fc8b0f09f3cfd96211b33d863d5e629bbed13e46`。App reader-first后仅重载本方BFF，实际旧进程exit0→ready200；七其它listener与worker、原env/lock/Schema/旧业务事实不变。Root精确pins与正常源配对；当前其它新WIP不纳入正常完成。

**③取消状态切片正常已闭。** 旧取消Run3fe3实际Agent cancelled，原BFF持久Message四值映为failed、无failure profile，造成实时parts缺口／刷新generic失败。现私有ChatMessageRead以既有同owner durable `bff_skill_usage_run_terminal`，精确tenant/session/run/actor/dispatch assistant绑定，在原RR一次有界batch投影`terminal_status:cancelled`；无新表/列/状态中心/数据回填。Root正常只读旧Run，snapshot200确有cancelled，UI一处“已停止”，原generic与parts缺口均消失，四既有成功marker、完整项目URL、空草稿与可输入保持；没有重跑模型/工具/付费。真实后继Run＋GC的隔离PG仍保取消，不把易回收AGUI帧当永久终态。原Stop404失败历史不改。

App真实RUN_FINISHED/ERROR／exact私有快照区分取消和失败，保实际正文/未读事实；202 pending及本地意图不伪造取消。unknown显式“再次停止”复原K/body，无自动重复POST；还补实抓的停止读取旧RR与同run同cursor后继ACK竞态，exact thread lineage拒迟到，原input/draft不被替换。236/237等阶段数量不作完整产品证明；最终source 69paths/1449输入，独立相关4689/contract427/arch50与lint/typegen/types/build/posttypes八门0，Root237重跑，旧private/policy/Auth/锁等保护及正规12gen已核。BFF15paths/944输入R2 format/lint/types/build/focused119/arch36/真实PG14全0，Root20＋独立freshPG14重跑；R1完整contract1315/default2183通过及3旧skip，只按两窄差分承接，不声称R1 hash就是R2。完整App default/Next旧风险与全产品合并门仍未闭，四PR仍Draft。

**真实Auth证据，不扩大修复。** App18cbd1仅追加真实Redis RP cookie/CAS＋业务GET latch回归，Root117重跑：refreshing/旧generation正确拒401，新generation恢复200，tombstone仍拒；BFF内容明确double，不冒完整issuer/浏览器登录。未改认证生产源，不能据机制倒填原两自然401根因。原Back静壳保留页现实际已恢复可输入、SSR serverAdmitted=true，Root没有为此次观察reload/导航，不再把旧disabled状态称当前阻塞；恢复原因仍未证。

**2026-10-28 用户再次否决后的实测复核：展示仍不合格，优先修 MCP 阅读语义，不以轻量 loading 改动代替。** 当前 conv6530 展开仍是发现／说明／调用共11条内部活动，原摘要3次只计执行调用，并非算错11条；Manus混合组摘要本来也不计全部底层活动，因此不能凭数量差异重写分组。已实际打开成功MCP详情：当前统一pre展示转义JSON、text与structured_content重复，主行仍原selector；两端动作文字均14px/20px，主要缺陷是信息组织，不是字号。

- [x] 只读对照与数据源核查：参考实际阶段正文→混合操作摘要→可读动作→按类型查看结果；MCP owner仅持name/description/schema，没有逐调用目的或title；说明存在同Run discover/describe journal，当前RunDisplay未提供独立说明字段。原生edit_file/ls/glob/grep/execute也缺专用展示码，不能把edit冒充write。
- [ ] 下一完整切片：Agent按同Run、connection＋selector提供有来源的工具能力说明（不冒本次目的），经正式BFF契约供App消费；未知／冲突缺省，不从当前目录回填旧Run。主层保真实阶段正文与动作对象；详情区分可读结果和技术请求，原始信息仍可查。沿原owner与私有权限，无新业务owner或表。
- [ ] 同一旧MCP会话＋新真实Run验证：具体工具与来源、受控输入输出、失败不伪装成功、刷新不丢顺序；再验窄屏和正常轻量live标记。原文缺失的历史不能靠前端生成说明假装修复。当前参考为建站／浏览任务，没有同类DeepWiki示例；本轮747×767与1280×720仅作结构研究，不称像素一致。
- 本轮只做实测、只读源码审计与更新原执行游标，未改产品代码／重启服务／执行模型／更改历史。截图和测量在原ignored display-rework中，Goal ACTIVE，完整展示不得勾选。

**2026-10-28 MCP结果阅读已正常修补，动作语义与整体展示仍OPEN。** App a1cdb82b已推原Draft并精确HMR到3310，原BFFfb9dc4df／Agent HTTP4f8a8d24与Worker894e605均未动。Goal保持ACTIVE，不把本片称Manus一比一或产品上线完成。

- 原会话成功动作3492字符JSON同时平铺text和structured_content。现真实工具目标为标题，结果按原换行只显示一次；原始输入/输出仍在键盘可开的技术详情，未知/截断JSON不修补，失败与缺证不伪造。独立组件持有展示，不新增请求、契约、数据或工具执行。
- 正常747×767验收：原read_wiki_structure正文与原text逐字一致、无重复/横溢出/可执行链接；Enter展开原始详情，切原失败ask_wiki_question保持失败且披露关闭，刷新相同URL再开仍正确。Manus1280×720命令结果重新采集，仅作为层级参考，非同类MCP像素证明。HMR使原详情关闭，验收显式重开；不把此动作说成无感保留全部UI状态。
- Node22停写相关333、contract439、architecture50及lint/typecheck/build/post-build types通过；完整default为6764 PASS／18 FAIL／2 skipped，**不是全绿**。2项因测试Redis参数缺失，按原隔离origin/UUID补参数后该8项完整文件通过；18项为既有rail Move/rename/delete浏览器定位超时，其中R183在未修改父086d8c07已复现，其余17尚未逐项独立归因。没有删断言、放宽超时或改旧失败；完整test:e2e未另跑。Root拓扑检查当前FAIL仅因Agent checkout52cc与保留gitlink894不同，这是未配对owner候选，不为消除检查改错组合版本。本轮不扩入旧rail流程，不合并PR。
- Agent 52cccd6的HTTP8.6工具能力说明已推候选：同Run精确连接/selector成功describe、完整原文冲突拒取、1024bytes与原权限/状态保护；owner默认3039与真实隔离PG24通过。BFF/App正式消费与正常reader仍待，故Root**不更新该Agent gitlink**，不把能力说明冒成本次动作目的。
- 后续依原目标：先接通真实说明的消费者并改善动作语义，再补原生edit/命令/技能上下文和活跃标记；历史无公开阶段文字不补造。详情本片证据归ignored `display-rework/mcp-result-reader/`，来源审查与真实截图归原study；重复准备信息、语义缺口及rail未决项继续OPEN。

**2026-10-28 阶段正文擦除根因已修，真实文字/工具交错与刷新通过；展示整体仍OPEN。** Agent 58728a公开阶段指引＋894e605文本完成帧修复已推原Draft分支；正常仅Worker切至894e605，HTTP reader仍4f8a8d24，App086d8c07／BFFfb9dc4df不变。没有新Schema、契约或依赖，不重写原会话，Goal继续ACTIVE。

- 真实根因：初次新任务的公开delta已有“我会创建包含登录、会话恢复和连接器三项的简短检查单，随后重新读取核对。”，但后续assistant.completed为空，把正文擦除。SDK text projection终值与assembled AIMessage.text并不等价；现保持并发drain，await同一text projection权威终值，不使用拼接兜底覆盖修订。旧完整AIMessage回归本来存在，先前遗漏流式块路径的判断已纠正。
- 验证：真实SDK dispatch mixed先RED，修后包含修订/tool-only、原取消与空段；默认3016 PASS/920按marker未选，类型/格式/lint/contract/build通过。仅default测试，不冒真实PG或任意投影调度全覆盖。两次Worker替换均无非终态Run、旧进程实际exit0，依赖/Schema及其它进程保持。
- 正常新conv689的第一轮创建/回读/交付成功，但模型没有中间正文，不作阶段成功证据。随后明确要求公开说明的真实Run2275：四段说明与读取/修改/复读/交付四次操作交错持久化，终态完成；刷新同URL保留原顺序。更新后300B检查单实际预览含三项和追加测试说明；未核本轮账单金额，不宣称零费用或计费全链已验。
- 下一片已明确：原生修改动作仍泛化“工具调用”且无详情；普通首帧“正在整理回答”和“继续处理中…”需统一为单一轻量活跃标记，保排队/取消/重连/HITL事实；文件Markdown预览当前纯文本，与Manus渲染预览仍不同。不得用本片通过关闭整个Agent展示。不同任务同1280×720截图仅支持层级比较，不冒像素一比一。其余MCP/Skills/Home/Projects未决项沿原计划继续，不重开已验CRUD。
- 证据：ignored `display-rework/public-stage/text-completion/browser-verification.md`、真实事件回读、修前/刷新后与文件预览截图；不把私有会话产物进Git。

**2026-10-28 Manus重新实测与动作详情接线推进，展示验收仍OPEN。** 正常App现086d8c07（含227de135私有详情与0d5aaf45单层操作段），BFF fb9dc4df／Public28.12、Agent4f8a8d24／HTTP8.5；Platform94e保持。未重跑原模型/工具、不回填历史，不把以下局部修复称完整Goal完成。

- 参考新证据：Manus网站任务同一正文段后混合命令、文件与其它动作，摘要“已运行1个命令·编辑了1个文件”，点击分别打开终端/文件；原Computer Use另证明失败说明仍存在。因此撤销旧“只合并相邻同类”的假设，改为真实公开文字之间单层相邻活动段，不跨文字重组、不嵌套重复准备与失败计数。未观察同一DeepWiki/MCP参考，不冒一比一已验。
- 正常原conv6530保持11原活动及4原失败，摘要工具调用3次；名称、repo/question与文件路径只取本Run原事实。已修浏览器发现的第二缺陷：AnswerActionBoundary曾误传MainSurface、未传持有Canvas的AppFrameShell，导致详情只有泛化标签。现原成功动作有原输入/输出与截断标记，切换失败动作保原repo/英文question并明确输出未提供，关闭回到原失败按钮；无数据/权限改变。
- 验证：0d5阶段独立UI/core/engine3822、contract/architecture及lint/build/types通过；本次接线完整AppFrame行为RED→GREEN，相关314与lint/build/types通过，最后强化完整session/Run URL断言focused1/lint通过。两次fixture错误、真实失败和最终日志均存ignored display-rework。最终正常856非MD源码同086d8c07，原进程/env/依赖保持。没有全默认/E2E本片通过声明。
- 尚未关闭：历史普通调用没有自然语言目的字段；禁止用当前工具目录或新生成文字补造。下一片核实并完善Agent真实公开阶段文字与同响应文字/工具事件顺序，复用现TEXT_MESSAGE，不增展示协议。当前参考1280×720与本地窄窗747×767非同视口，精确视觉、窄屏详情呈现及新Run端到端仍待验。Auth限流等旧余项保持OPEN。
- 证据：ignored `var/dev/mcp-prepare-receipt-20261027/display-rework/` 下manus-current-mixed-passage.png、local-action-input-output.png、local-action-failed-exact-input.png及action-shell-browser-verification.md；外部内容不进入Git。

**2026-10-28 用户否决当前工具展示：不合格，展示验收重新打开。** 此裁决覆盖下方“工具展示闭环/可勾”的旧阶段判断；工具名/失败事实与模型目录局部修复保留，但不是产品展示完成。当前优先回到同一conv6530的Agent过程展示，不先绕去其他模块收集通过数。

- 已重新实测Manus既有会话：折叠入口是简洁过程/耗时；展开后真实中间文字→具名动作组→中间文字交错，相邻同类浏览动作按4/1分组，点击动作打开右侧具体浏览历史和URL。28px高/14px字/20px行高/无边框透明行，非“类别标签串＋统一完成图标”列表。参考只证明Computer Use行为，不冒已观察MCP详情；原截图/DOM测量存ignored `var/dev/mcp-prepare-receipt-20261027/display-rework/`。
- 重做范围：顶层不拼工具类别；正文保真实时间顺序，按新观察以正文之间的相邻活动为一段（可混合类别），不跨文字合并；工具行表达动作＋对象，技能名/文件path/MCP连接器与工具身份来自原Run可信事实；点击展示受控详情/结果，最终回答保持独立。历史缺字段不伪造，不能用当前连接器名称或自动生成中间文字回填旧Run。
- 待核实/实施：Agent安全投影目前主动缩窄arguments/result/连接器label，先明确可公开action摘要与owner契约，再落组件；BFF与Web不猜补数据。已有功能性状态修复不回滚，但当前UI/交互须按同视口真实参考再次验收，未经完成不得再写“展示闭环”。

**2026-10-28 模型目录读取切片正常已验，Goal仍ACTIVE。** App `8474d08fef30acab35f78012fdbe5e12fdfd9ae7` 取代下方工具展示阶段的bae416；BFF d629／Agent f31／Platform94e不变。本批9路径，正常仅3运行源码更新、855非MD源码逐字同正式commit，原进程/env/依赖保持；无Schema、认证政策、业务命令或额外模型执行。只关闭本切片，不把整个AUTH/产品标完成。

- 根因与修复：目录以前跟随engine重取，非Composer广场也发GET，失败后无前台恢复。现目录按可信Product subject/generation隔离，模型选择仍归engine；同scope好数据跨页面复用，非Composer/隐藏/未准入不读。错误仅在真实前台唤醒或重入时单flight恢复，429遵守Retry-After，不自循环；401交现有ProductReadRecheck，换主体/退休拒迟到结果。审查发现同主体旧代菜单闭包可新写，增加committed authority阻止旧回调，保已确认选择。
- 真实浏览器：同一QA项目→广场从旧2次模型GET降为0；健康往返0次GET且返回第一帧模型可见。激活期间自然发生model429（Retry-After60），重入在81.972秒后仅1次GET200、60.589ms恢复，不刷新整页。冷打开恰1次GET200、80.059ms；这些是单次实测，不称全站p95或全接口<100ms。原conv6530具体MCP工具名、4失败与正文仍保留，未重跑原任务。
- 剩余真实错误：激活曾同时捕获项目/会话/连接器等429，另有401与原auth/session409。IAM当前公开策略为同OAuth client+operation共享100次/60秒，普通BFF请求逐次fresh admission，多标签共同竞争；本片未改政策、未缓存鉴权或提高限额，AUTH整体仍OPEN。模型自动恢复后项目/会话列表仍需原有显式重试才恢复；广场6个旧QA无图标404另记，不能掩盖成空态或称全页无错。
- 最终验证：独审修复旧回调2RED，writer8文件596通过；Root私有隔离1486输入精确冻结，related4787、contract437、architecture50及lint/typegen/types/build/posttypes全通过。Root首次related的1FAIL/4786PASS保留：首发模型测试缺可信boundary，补正式准入fixture，保原首发model断言，不放宽生产鉴权。完整default/Next Chromium fixture及远端CI/合并未运行，不冒通过。正常证据ignored `var/dev/mcp-prepare-receipt-20261027/model-catalog-recovery/` 的browser-before、activation-rate-limit、normal-browser-proof、app-model-activation及原工具/项目截图。

**当前后续游标：** 先收敛共享准入限流与项目/会话失败恢复，继续③异常/多标签，然后②Skills创作与④首页/项目剩余能力；复用原计划和Draft PR，①②③④均不整体打勾。

**历史工具事实修复已实读；用户已否决展示，产品验收OPEN。** 最新正常App `bae41632fd9da66c474635e551eddc6db2387eba`／BFF `d629653cbf5799a44db55a947321a6ec152b7dcd`（Public28.11.0）／Agent `f31b60be27dd9b4dfddd7a1c3579b19e40db150d`（HTTP8.4.0）／Platform `94e574c68d6c972078b661fa7d917dab90c71042`。App855与Agent215非MD源码逐字核同正式commit；BFF971输入/1018编译文件的不可变归档启动，旧worker/HTTP/BFF逐个真实exit0后reader先于producer重载，原env/依赖保持；Admin3320此前离线且未动，不冒全系统健康。本批后继无Schema变化，不回填原Run、Message、ledger/id/digest或计费。

**用户当前旧MCP截图已用同一旧会话核验，不靠重跑生成好看的记录。** conv6530／Run cab07的11活动原顺序保留：3发现＋5描述＋3真实调用；相邻准备折叠为2/4/2，三次调用在外单列真实`read_wiki_structure`／`ask_wiki_question`。只用该Run原typed AI/ToolMessage、native journal与opaque safeactivity精确绑定的证据；4项已证明失败纠正旧all-green，未证明的未知工具名仍不猜，不借当前目录补旧历史。3旧describe错误仅允许原recipe文件SHA f4f1（正式历史2aaf67e）对应完整内建常量＋typed同ID内容匹配，不用任意远端错误串推断。bounded tool_facts经过Agent8.4→BFF28.11正式snapshot/generator→App同Run overlay；既有活动/source/order/终态不改，无新轮模型/工具/业务写命令。

**冷重开和窄屏已真实复核。** 原父折叠的手动展开意图持久化后，冷刷新只有UI恢复open却没触发详情读取，造成旧通用名/全绿直到再点一次；App bae416在同组件对已手动展开且有活动时仅排一个可取消微任务，等父reader activate，保closed/live默认与429/503不自动重读。实际冷刷新不再二次开关，恰一次display GET200／180.14ms；原页另一次200／190.673ms。不称全站<100ms。390×844实测scrollWidth390、工具名换行且右边界在内，恢复原metrics；桌面完整正文、名称、状态、四操作栏均可见。首次真实display429遵守Retry-After60，没有轮询刷请求；原用户页URL/空草稿可输入保留。独立Project保留页曾读到BFF user admission failed，显式原重试入口恢复项目及空草稿，但模型目录读取仍失败，归AUTH/加载剩余项，不能称全页无错。冷窗有原生auth/session POST，不把它说成零POST；无模型/业务命令。

**回答操作与账本承接，不重复付费验收。** 原ee22真实提交＋d38e真实再生成已完成：保原human ID、新Run/assistant，旧答案仍在、仅1份用户输入；复制marker及空剪贴板恢复、赞持久刷新→踩互斥→清除回读0。两Run各10attempt全部captured，共45积分；本批最终只读核对与激活前完全一致，原4active冻结40积分及xmin/指纹不变，不补扣、不重算。原取消“已停止”与先前成功marker承接。

**真实缺陷和踩坑已记。** stdlib host伪造未出现header为空键导致严格GET400/BFF503，2677只保真实存在性，显式空仍拒，Root真实HTTP/JWKS/Auth176通过。安全前缀regex曾把ask_wiki_question中的sk_误当密钥，f31与消费者以token边界修复，真实密钥前缀仍拒；HTTP8.4字节未改变，不同源码SHA如实锁定。旧Skill真实名和声明路径已恢复，但其旧read_file原journal不存在，工具operand仍未知，不从声明路径造参数或用当前revision补历史。只send_message给已结束Agent不会重启实施，需followup_task并查实际状态/写区；后续避免隐形停工。初隔离cwd错误与/tmp JWKS父目录guard拒保原红，改自有安全隔离目录而非放宽断言；移动截图首次capture尺度裁剪不作产品缺陷，改显式CSS clip保存真实原图。

**资格范围和后续游标。** Agent R1独立2963通过/914资源项未选，真实PG与f31窄修Root60、最终package0；BFF R1 contract1322/default2242＋3原skip，R2六文件73及Root44、归档build0，R1不冒最终R2全量；App2c隔离相关4758/contract437与八门0，bae416两路径Root42/build/posttypes0、其余1484输入无漂移。完整App default/Next fixture、远端CI/合并未宣称完成。当前新图的MCP活动展示切片可勾，完整①/②/③/④不整体打勾：继续AUTH admission/模型目录/后台接口真实错误、③异常/多标签与工具真实详情，随后②完整Skills创作与④首页/Project网站/事件/ACL等；外部OAuth只限制对应动作，全站<100ms与Manus精确像素仍OPEN。实际截图、回执与最终source/ledger证明归ignored `var/dev/mcp-prepare-receipt-20261027/answer-actions/`：normal-history-ui-proof、normal-final-pair-proof、mcp-restored-desktop-compact/mobile-compact及full-order-restored-desktop。复用原Draft PR，不新建任务中心或伪称全产品上线。

**证据/踩坑。** 本地ignored `var/dev/mcp-prepare-receipt-20261027/cancelled-terminal-read/`：formal/app-formal、runtime准备/激活、normal-proof、normal-stopped-restored.png、Root真实PG及native旧metadata证据。旧Skill“记录技能”菜单→fresh Composer预填/聚焦已正常零业务写验收，原草稿清回，但只是prompt入口，不冒屏幕录制或完整AI生成导入闭环。最初ledger-only取消方案独审抓到GC退化，已改复用原durable事实；Root首freshPG URL少schema被明确拒绝，重建自有库修正，原红与零subcase保留；R1 SELECT *／格式失败仅修两处并保差分资格。原CURRENT29和计划32/2未交接WIP严格保持。

### 2026-10-27 剩余进度对齐

以当前 active Goal 的四项顺序为准；正常App6bdf5a0／BFF7f5c522／Platformf29428f6／Agentfc8b0f0（本轮Root组合见精确gitlink）。下面区分已验子项与整项剩余，不以历史阶段的“待实施”覆盖最新验收，也不把单条成功链或测试数量当整项完成。不按已知不足的证据给百分比，不新增任务中心。

| Goal 顺序 | 原 TODO 归属 | 已完成／正常生效的子项 | 整项状态与剩余 |
| --- | --- | --- | --- |
| ① MCP／连接器 | SKILLS-MCP-1 的 MCP 部分 | 四路基础创建／对应详情编辑／QA删除刷新及密钥／Header／图标／HTTP定义发布已收敛正常证据；API删除负事实、URL图标取消、旧Prepare unknown下独立备注保存／刷新／恢复及面板分离、API外框和剩余图标／帮助／密钥细节已正常验；真实调用／项目推荐／同会话恢复保持 | **本轮可执行工程切片已闭合，整项外部授权仍单列。** 原completed回执查询、旧unknown具名fence→结束等待、新key／fresh CAS独立重连、确定失败及刷新历史已正常实测；旧回执不改，不把failed泛码当负ACK。详情历史挂载／短屏可达及配置分离已修。真实Provider/OAuth/Admin有凭据末端依对应配置，不虚构成功，也不再阻塞Skills。 |
| ② Skills | SKILLS-MCP-1 的 Skills 部分 | 真实导入／下载、启停、版本／更新恢复及获准移除重添已验；S09依赖闭包与当前tuple、真实发布方／GH来源、固定版本私有GitHub导入及安装刷新、S11清理读取消／S12来源读取和可见正文门控已有正常证据，原八成功不重做 | **实施中，不把已闭动作重开。** 当前Appb7f1e1a／BFF31ce61d；原GitHub selected未知已沿同key恢复201、私有发布与安装200，两个owner receipt终态，真实正文可读。Project exact包读取Platform94e574c正式候选、未激活，BFF完整消费者推进；创作／录制、Project详情UI及剩余权限／失败／unknown矩阵仍OPEN，org／missing等未观察实体不冒正常实测。 |
| ③ 创建任务与 Agent 主链 | AUTH-1、MODEL-1、CHAT-1、AGENT-1、CREDIT-1、PREF-1 | 正常新任务及项目归属／URL恢复已有证据；模型→真实MCP／Skills／文件→交付→终态→重开→实际积分已验，六QA共33attempt／73积分；真实自动压缩3次有checkpoint／capsule证据 | **实施中，核心成功链正常生效。** 剩运行中发送／队列／打断／停止恢复、异常／取消与多标签／会话导航完整矩阵及原AUTH-1默认测试缺口。原四笔40冻结按原事实保留，cache缺项仍partial；不反复付费重跑成功链，不改旧账充数。 |
| ④ 首页、项目及其余产品能力 | HOME-1、PROJECT-1、SCHEDULE-1、PERSONAL-1、NOTIFY-1 | 本轮标题留白、项目五项共享菜单、真实固定／取消刷新、跨项目编辑取消→删除确认已闭合；指令／MCP／资源／Skills四项共享上下文、Root↔Task往返已有正常证据 | **实施中。** 首页各场景完整创建旅程；项目网页资源／网站持久化、项目定时过滤与嵌入、事件／高级自动化、分享／ACL及排序／分区完整矩阵；个性化／知识导入和通知按原条件核验。不能把复制URL、preview数据或几个入口当这些能力完成。 |
| 贯穿四项 | UI-1、API-1、DOCS-1、RELEASE-1 | 当前相关源码／契约／Docs生成与局部工程门、Manus菜单计算样式／截图和正常版本聚合已验；原PR已更新 | **实施中／待合并。** 全站无感读取仍有T02 ProjectConversations可见loading／骨架；精确视觉色差、冷读／后台错误和完整登录回归保留。原PR仍Draft，未完成项不因push或局部绿而勾完；全部接口<100ms及全像素一致尚未成立。 |

**下一执行游标：** 继续②Skills Project exact installation详情／包下载完整切片：Platform94e574c正式产物已交，BFF沿Project访问前后复核与准确qualifier接Public28.8/private下载，再由App消费正式artifact复用reader；正常新RPC尚未激活，不把个人包权限借给项目。GitHub固定版本原提交、安装与刷新正文已闭；源删除灰卡读取消、S12来源读取、项目可见正文门控均承接，不重做原八写链／付费调用。随后创作／录制与其余矩阵，再③交互异常和④首页／项目；Auth／429与外部OAuth只限制对应动作，不暂停独立工作。

**本轮并行写区／实进度（2026-10-27）：** MCP正常App13fdfa1／BFF394ae559／Platformf29428f6已配对；原K1 CAS1 GET409→显式结束等待零写→fresh双读／K2 CAS4一次POST412具名拒绝→刷新双历史只GET，owner旧行SHA／xmin保持、新terminal attempt1／版本5／无Connection凭据，真实功能切片已收口。Root截图另发现历史外挂挤hero，已在同组件原scroll body修正，652／390键盘及配置独立读／取消正常验；不以fixture图代正常图，原完整RED保留。App最终四路径Root八门0／1434输入无漂移，CSS／commands／journal／wire零变；PlatformPG28／0skip和BFF八门承接，默认R352 timeout及Next/Auth根因仍独立OPEN。Root独占Git／正常资源，原CURRENT29及计划32增／2删WIP保留。②Skills现S09直接／传递闭包＋当前七字段tuple已闭，原八成功承接。App361896a仅去发布说明两句内部术语，Root42focused／lint／非增量types0及正常读／取消零非GET；文案片当时完整八门绑定13f；后继App2aaf六路径已Root完整八门0／4821相关／1434无漂移及正常共享reader受控延迟1px／真正文恢复／390无横溢，最终短窗4GET零写。overview无条纹截图与个人reader仅源／隔离资格分开；不冒全站loading已清。继续S10–S13，publisher BFF7f5／Public28.6与App6bdf reader-first已正常配对，5条current IAM user found且卡片／详情同Owner1231；Root八门0／1435输入无漂移，正常652／390无溢；新Manus对照确认GitHub链接／Star-Fork仍待补，不重做已验八成功；有凭据Provider/OAuth缺口不再拖住独立产品工作。完整上线、全Goal与合并门未假勾。

**Skills安装／项目来源本轮收口：** d524的灰卡fresh读取／原确认取消、来源搜索／字段恢复／短屏与Abort证据保持；后继App4e可见会话才读parts正常验，b7仅两JSX展示修正。BFF31已恢复原GitHub selected提交，201→owner私有发布200→安装200，原body/key相等，两个owner receipt终态；硬刷新固定提交来源和真实正文均可读。Project包读取Platform94e正式源码候选及BFF五路径非wire准备不等于正常启用，完整消费者继续。Root当前正常Appb7／BFF31／Platformf294与正式源候选分列，原Auth409／429、推荐0→1、创作录制及其余矩阵保持OPEN。

**Skills本轮增量（2026-10-27）：** App92e1836／BFFd040 reader-first正常配对，Public28.7正规生成；发现512与选中包128限额分离，原字节／安全预算不变。真实同仓库preview200／252完整路径，固定2574e293…／marketing/skills/content-creation仅本地选择、待确认导入；完整短窗一次只读POST，390短屏页脚可达。Root App八门0／1436输入与BFF八门0／939输入无漂移，默认142文件去重完整覆盖的运行口径明确，原Next/Auth与R352缺口不清零。获准0b42 QA系列在7f5阶段一次DELETE200／版本1→2／目录刷新不存在；e80历史安装停用且source_deleted，未额外卸载。原八成功保持，S10实际导入／创作录制、S11清理入口／后台草稿及S12差额继续；详见CURRENT最新快照。

**状态与证据规则：** 沿用待核实／待实施／实施中／待验收／待合并／正常生效；正常生效的子项不等于整项完成。每次关闭补根因、改动、正式SHA、实际旅程／回读及剩余差异；不以隐藏失败、伪造数据、删断言或重复盘点替代实施。详细证据仍在本页最新快照和CURRENT，不复制完整历史。

以下是原16项完整验收范围，不是实时进度表；当前状态以上面的Goal进度为准。已验子项承接原证据，未满足整项关闭条件仍保留，不重新列为零进度。全部需求属于本轮统一交付；功能可按依赖顺序实施，但不把Skills/MCP或其他未完成项留给另一个收尾目标。跨面工作先分独立写区，契约 owner 先交付，再接消费者；不同时重写所有模块。

| ID／顺序 | TODO 与本轮范围 | Owner／依赖 | 完成条件 |
| --- | --- | --- | --- |
| RELEASE-1／统一交付 | 全部本轮需求按依赖实现并集中交付，不设旧批次交付债或独立盘点阶段。 | Root集成；各业务owner。 | 本轮各项真实旅程及相关验证、审查通过；PR合并、Root精确组合、正常环境回读与在线文档一致。任何未完成项明确留在本轮，不以主链局部通过宣布整轮完成。 |
| AUTH-1／P0 | 第一方登录、续期、退出、多标签及过期／错误恢复的完整产品旅程。 | IAM 身份；App 产品会话／登录 UI；BFF 可信准入。 | 用户从品牌登录页回原目标；已登录切页面不反复 OAuth；退出、刷新、双标签、token到期恢复均实测。技术回调／长参数／裸错误不作为停留页面；Admin 复用 Product 登录，不另开一轮 OAuth。保留 state／PKCE／nonce／CSRF 和有效性／权限检查。 |
| MODEL-1／会话依赖 | 提供方配置地址和密钥后，可显式刷新上游模型候选列表并选择导入共享模型；业务独立组合、可用列表、默认项与可选别名，聊天选择器只拿聊天业务模型。 | System model-catalog；BFF 当前租户投影；App chooser；Agent 精确解析。 | 配置→发布→该业务 model list→用户选择／默认→服务端核验→冻结精确修订贯通；未填别名显示原名，provider Key只在服务端。不同业务可选不同能力／模型池，不把业务锁死到一个provider；按实际业务能力筛选，不预建尚未提出的业务类型或功能。 |
| CHAT-1／P0主线 | 会话创建、首条消息、任务标识／顶部地址、路由和历史恢复。 | BFF Conversation/Message；App 导航、composer、消息列表。 | 新建任务不误建项目、不跳错归属；URL与标题／选中态对应唯一会话；按 Manus 实测定具体路由，不在本记录猜路径。发送一次、刷新、返回／前进、切任务、草稿／焦点／滚动恢复不丢失、不重复。 |
| AGENT-1／会话主线 | 正式 Agent 请求到终态：流式文本、可公开的思考摘要／执行状态、工具请求／审批／进度／结果、交互输入、停止／恢复／失败重试、产物。 | Agent Run/checkpoint/tool journal；BFF durable AG-UI；App UIMessage 与子渲染组件；Storage 产物。 | 同一次 run 的事件、消息、工具和产物关联准确；重连／回放不重复执行；文本／代码／文件／图片等按正式产物类型预览、下载并刷新可恢复；真实事件驱动状态，不伪造 thinking 或工具成功。以受限真实模型和低风险工具完成正式链路验收；模拟只用于异常回归，不替代真实完成证据。 |
| CREDIT-1／上线阻断 | 用户无感积分初始化；当前租户充值、余额／用量／不可变流水、后台管理，最终接实际用量扣减。 | Billing 唯一余额／账本／计价结算；IAM 权限；System配置；Agent用量证据；BFF/App/Admin。 | 正常用户不见“尚未开通积分账户”；空余额与读取失败分开，不用假0遮错。后台充值有权限／审计／幂等，实际用量聚合后在结算点统一整数取整，分片／重试／重复回执不多扣；取消／未知结果按真实结算状态恢复。真钱支付不做，不以手工扣分代替计量链。 |
| UI-1／贯穿上述主线 | 无感读取、点击切换闪动、技能“新增”弹窗、设置页与项目技能选择；账户卡片、身份下拉菜单及响应式布局。 | App 各功能组件／读取 hook；必要时 BFF 投影。 | 冷读立即显示稳定壳，已有内容在同主体刷新时保留；不以“正在加载”／空白整页／大骨架替换内容，不误报空态；切账号清退旧数据，迟到响应不覆盖新选择；失败可恢复、保存／未知提交状态不隐藏。技能入口按冷开／再开／慢请求／失败／键盘／窄屏复现验收；账户名称、头像、积分分项、身份选中态按 Manus 实测校正，不伪造免费额度／每日刷新规则；普通用户不直接看到内部来源／状态／校验码、技术引用或无用途的连接器ID，后台排障事实保留。 |
| PREF-1／会话交互 | 运行中发送：添加队列、发送不中断、打断并发送，连同用户聊天偏好。 | BFF 消息／原子命令；Agent run控制；App设置／composer。 | 先核已有支持再补缺；每个可选项确实改变运行行为，跨刷新保持。队列、取消与下一次派发事实可恢复，不用一个 Redis 锁假定所有消息／登录／token刷新都已解决；不显示只能选但无后端行为的选项。 |
| HOME-1／会话之后 | 首页完整布局和输入框下简报／网站／设计／游戏／更多等场景入口。 | App展示／表单；System站点能力配置；BFF任务事实；Agent执行。 | 每个入口进入、切换、退出、参数／附件、草稿、创建请求及新会话回填均对照实际 Manus；不是只放同名按钮。无正式生成能力不造结果；连续缩放、桌面／窄屏、菜单和弹窗状态有对照证据。 |
| PROJECT-1／随后 | 项目概览／会话／指令／资源／技能；侧栏更多、置顶／取消置顶、排序、分区及新建任务归属。 | BFF Project/Conversation 与个人导航偏好；App项目组件；相关owner读取。 | 先核旧能力是否未合／未加载，而非凭截图直接判回退；逐动作核真实API和持久化。pin／排序／分区刷新与重登保持，项目与会话不混，项目不当作组织／团队；按 Manus 实测确定菜单和 URL。 |
| SKILLS-MCP-1／本轮完整能力 | Skills个人／项目列表、身份权限、导入／发布／版本历史／恢复／删除、后台管理；MCP配置、授权／续期／重连、发现与Agent真实调用。 | IAM身份；Platform控制面；BFF；App/Admin；Agent执行。 | 用户入口→真实API→持久化→刷新→失败恢复贯通；精确版本、权限隔离、删除语义及幂等有效；技能选择弹窗无闪动，连接器已记录的图标上传等差异在本轮解决；MCP按受限真实工具验收，不以discovery或组件测试替代执行。复用已验结果，只补缺口，不重复重写。 |
| SCHEDULE-1／既有遗留 | 自动化日历 `/app/scheduled?tab=calendar` 的页面与操作闭环，先与同事已交付能力核对。 | BFF ScheduledTask／既有 Scheduler 边界；App 日历；实现前明确写区。 | 月／周／日视图及已有筛选、时区／跨日、创建／编辑／停用／删除与刷新回读按实际已支持动作验收；空态与错误不混淆。未交接前不改同事自动化代码，纯日历操作不启动任务；执行旅程复用已验 Agent 边界。 |
| PERSONAL-1／功能缺口 | 个性化与知识／从其他AI导入记忆的真实流程。 | BFF 个人资料／知识现owner；App个性化组件；Agent上下文消费。 | 入口→输入／导入→校验／预览→确认→持久化→编辑／删除→新会话实际采用已批准内容闭环；不再显示“导入尚未接通”死流程。涉及模型处理时限定为用户提供的验收内容，不自动采集其他账号或外部私有数据。 |
| NOTIFY-1／功能缺口 | 浏览器通知、声音提醒和产品更新选项。 | App通知权限／呈现与用户设置；既有任务事件owner。 | 允许／拒绝、前后台、已完成不重复提醒、声音开关可验证；明确仅当前页面与真正后台推送的支持边界。无产品订阅服务不展示可操作却无效的订阅开关；不擅建通知服务。 |
| DOCS-1／随功能交付并纳入上线 | Manus式在线 Docs：指南、搜索、导航、示例、API Reference、错误和排障；公开与内部完整说明。 | App `developer-docs/` 公开门户／`docs/` 内部资料；各 API owner 唯一 canonical。 | 以真实可访问的在线URL验收，不以源码目录／静态截图代替上线；公开搜不到内部凭据／管理协议，内部站点有访问控制。固定发布契约生成字段与例子，文档调用可复现，桌面／窄屏和部署路由无坏链；站点域名／发布位置待对齐，不杜撰在线地址。 |
| API-1／每个切片共同条件 | 逐页面动作的 Manus API 对照：请求／响应／错误／状态／幂等与恢复。 | 当前业务 owner 主持；BFF 公共契约；App Docs 发布。 | 维护一份精简差异表：实测动作、脱敏I/O、Kokoro canonical、明确差异、实现与验收状态。必要契约改变同一切片原子更新／退役旧入口，不堆 alias／双读／临时兼容层；不声称未观察的私有API等价。 |

## 4. 需要对齐的产品／工程理解

### 4.1 登录与 token

“正常环境已有登录修复未进入新候选”说的是 Git 分支遗漏承接，**不是业务请求设计成反复走回调**。正常登录后，浏览器持有受保护的 Product 会话，Web/BFF消费受信 token；普通会话／设置读取不应重启登录。内部用户身份仍需校验有效期、当前权限／租户和撤销，不能只看“有没有token”。

OAuth/OIDC 回调可以是首次登录的内部协议步骤，不应成为给用户的技术页面或重复操作。是否进一步收敛第一方登录路径／会话职责，在 AUTH-1 先画现有实际链并核框架支持，再作最小重构；不在没有证据时新增另一套密码／token／认证协议，也不把第三方 MCP OAuth 和产品登录混成一种页面。

用户说的会话串行／Redis锁，针对 Agent 同一会话的运行协调；它与 OAuth 登录交易、浏览器 cookie 覆盖、token续期的并发不是同一个锁域。

### 4.2 模型组合，不是每个业务重复保存一套 provider

需求澄清：用户此前提到“后续可能还有音乐”只是解释不同业务需要不同模型配置的例子，不是音乐功能需求；不将它列为任务、排除项或预留实现。

目标关系为：**provider（协议／地址／服务端Key） → 共享模型配置／精确修订 → 各业务可用组合＋默认项＋可选别名 → 业务 model list → 用户选择 → 服务端核验和执行快照**。同一模型可被多个业务引用，同一业务也可引用多个 provider 的模型；各个已存在的业务按需获取自己的列表和能力约束。租户来自当前受信站点／登录上下文，不让业务表单手填租户绕隔离。

### 4.2.1 已确认的最小积分执行语义（2026-10-22）

后台配置价格和单次整数积分预算；Billing在调用前以预算预占，用真实usage和冻结价格统一一次整积分ceil结算。预算不是供应商成本保证，不再等待旧R252额外保证合同。已确认未派发才可无actual释放；completed/failed/cancelled有已验证actual均按实际结算并释放余量；unknown或actual超预算进入pending_reconciliation，保留预占及原证据，停止同Run新派发，不补0、不夹金额、不自动补差扣款或重发模型，TTL/取消也不是释放依据。Agent不计算价格或持有账本；资金/价格仍在Billing，技术目录和共享业务组合仍在System。现仅pure决策已实现，后继正式consumer、事务与恢复须以真实验收证明，不能以此宣称模型/扣分已开放。

### 4.3 System 的边界

System 保存站点／业务能力配置、模型目录／路由及适当的可发布场景配置；它不是所有业务表的归宿。首页组件与临时表单归 App；会话／项目／用户导航与业务任务事实归 BFF；执行状态／工具／交互／checkpoint归 Agent；积分账本归 Billing；文件／产物归 Storage；身份／团队归 IAM。是否需要场景配置表由真实后台维护／发布／数据需求决定，不为几个固定按钮先建通用CMS。

### 4.4 无感不等于隐藏事实

移除面向用户的技术等待文案、闪白与整页重置；保留可访问性忙碌语义、稳定占位、必要的按钮防重、明确失败恢复。读取、保存、未知提交、Agent运行进度是不同状态；不把保存失败、未到账、工具失败或未知结果静默当成功。跨主体不能为了“丝滑”继续显示前账号的私有内容。

## 5. 明确暂不做与开工门

- 暂不做：团队新增功能、真钱支付、全新认证协议、通用网关／规则引擎／CMS、无收益的全仓兼容清理。已有团队成员／权限与原始数据保持，截图中“团队”与“项目”问题分别登记，不互相替代。
- 用户截图先当正常页面观察证据，不当当前候选代码已加载的证明；实现前核实际 source／commit、API与状态，再对照同视口 Manus，禁止凭记忆猜CSS。
- 新需求先完成本次讨论排序；每个业务切片再落必要设计／契约／Schema后实施，允许必要重构与补表，不空建目录／空层／服务。
- 本地验证按风险选最低充分层级：规则／错误用定向测试，真实I/O用owner隔离集成，浏览器覆盖主旅程；只在停写交付基线跑完整相关门，别对每个按钮反复全仓测试。
- 交付后集中 push／复用PR／merge，不等CI，不绕强制保护；更新前先非递归fetch，保留同事贡献／未交接WIP。Root最后pin已发布精确组合，正常加载自验后再称可上线；只清理确已合并且无人使用的自有分支。
- **本次整理完成的判断**：新目标、任务顺序、owner、验收、排除项和当前阻断已记录；不把“整理完成”写成“产品上线完成”。

---

# 历史计划与证据（以下不决定本轮目标或优先级）

## 2026-10-21 最新授权：接手连接器，一次收尾

本段覆盖下方旧“连接器不接管”。本轮仅完成既有 Skills 与 MCP／连接器遗留，自动化不接管，模型调用／实际工具执行／扣费暂停。

- Skills：App 删除页面与 BFF 公开身份矩阵并行，Platform AppBinding 固定交付后消费；保留原明确 CAS／publication／receipt 与对象范围，不重做已验历史／恢复／后台旅程。
- MCP：先核远端与未提交写区；已确认三个现有 UI 文件的四处门禁堵住 prepare_failed／unknown 后显式重连，按原服务 Reconnect 收敛，unknown 原 Prepare 不清除、不当成功、不自动重发。唯一 connector writer `connectors_takeover`，与 Skills UI 写区隔离，公共 adapter／契约仍各一 writer。
- 验收：复用现有包发布、真实隔离续期和 discovery-only 证据；补受影响页面、键盘／窄屏／失败恢复，不新增测试平台。App 两写区同时冻结后主方集中验证一次；配置闭环不靠启用 tools/call、模型或扣费。
- 交付：已开发／已验收／已合并／正常生效分开记；逐 owner 集中既有 PR，先 fetch 整合远端，不等 CI、不绕强制保护，最后 Root gitlink 与分支清理。不另开下一轮功能。

## 2026-10-21 Skills 收口实施更新

本轮用户已确认既定删除、公开身份矩阵与后台剩余验收；不再将其列为待设计答复。Platform（skills_delete_audit）与 IAM（skills_identity_audit）各一个 writer；主方维护 BFF/App/Admin 和串行集成。删除采用现有 Skill 全系列 deleted 终态，保留精确安装/资产引用与审计，禁止新读取/安装/执行；公开列表身份由 IAM 正式生产，App 精确技能范围仍归 Platform。完成 owner 契约后固定生成消费者，先隔离真实集成，再正常页面验收；复用既有四个 draft PR 集中交付。连接器业务不改，模型/工具执行/扣费暂停。下面历史待答复段不覆盖本次批准。

## 2026-10-21 Skills 历史读链已正常配对并实测

**实施约束**：用户页面和可见能力以Manus实测为准，只补本批缺口；复用现有组件、接口和owner，不增加额外产品概念、服务或兼容层，必要的权限／版本／幂等保护留在后端。

**后台空草稿补验（最新）**：已获本次精确确认并在正常页面丢弃该样本，fresh详情及owner只读确认discarded／revision1／state_version2／aborted、零publication与安装；原空草稿删除待确认已解除。13仓重新非递归fetch全0，候选无behind，Root保留4ahead/4behind及WIP。无服务重启、权限／积分／执行开关变更；剩余完整目标和写区／身份／删除边界仍保留。

**当前验收更新**：App264225c完整七门exit0（239文件4547PASS/0SKIP、1073输入无漂移），仅正常App配对重载；真实同样本查询期间卡保留／单击后精确修订3与Storage正文／Escape回焦均通过，原配置及其他六监听不变。MCP10月19日正常包上传扫描发布读回已有证据，本轮复核原provider仍版本2停用，不重复造样本；当前四端隔离HTTP续期正负旅程各1PASS/0SKIP，验证generic412、scope收缩、claim/CAS、原回执及invalid_grant后的显式Reconnect恢复；资源逐项回原、3321输入零漂移。实际负控又确认Custom详情unknown后重连入口P1，现四处门禁待局部配对，连接器写区归属已提请协调；正常OAuth浏览器续期仍未验。完整目标、未裁决的删除／公开三身份边界、后台剩余负控、MCP runtime及集中PR/merge全部保留；暂停执行不变。详见CURRENT顶部，旧阶段描述不覆盖最新事实。

**历史恢复最新进展（2026-10-21）**：Platform 已提交 `97b27b3056f3024fe1c0509072349e1b274efac4`：复用原 GetSkillPackageDownload/CreateSkillVersion，补本人明确 personal 停用/撤回原包资格及 validated 撤回基版的新空 draft；隔离、跨主体、未知来源和安装资格不放宽。实际3RED后修复、定向81PASS，完整10阶段exit0（2598PASS/453资源SKIP），8冻结输入无漂移；真实自有PG2PASS/0SKIP，库存94→94、旧Skill/publication逐行不变。独审无确定P0–P2；没有新API/表/服务或正常切换。BFF已提交 `4a10f8b043cb44b4bd2d8f8a689bde8191db10ce`，固定同一owner实现、21份vendor原字节保持；完整七门exit0（877契约、36架构、1529PASS/3原资源SKIP），719非文档输入无漂移、独审无确定阻断。App候选 `94d3687e06083c88d921d048e81e40dc9a5fe303` 已接原ZIP/恢复确认/新UID发布，完整七门exit0（239文件4545PASS/0SKIP、1073输入无漂移），独审及隔离Next/CUA通过；正常原包写旅程已配对自验：458字节原ZIP摘要与新上传/clean扫描/校验一致，新UID修订3、旧1/2和原停用安装不变；刷新/390窄屏通过。后台核心写旅程及目录投影已正常实测，旧v1保持、发布fence匹配；删除、公开身份、后台草稿丢弃/负控与MCP仍未闭环；模型/工具/扣费继续暂停，未push/PR/merge，Root不提前pin。

本轮增量：App `49ddf7f` 已在正常环境加载，当前指针与停用／撤回／隔离分开展示。实际原样本 current v2 显示“当前版本＋已撤回”，旧 v1 不继承该标记，正文切换与 Escape 回焦仍正常；612×766／390×844无横溢，完整动作网络窗仅GET、无截断，历史与 publication 与上轮完全一致。新增回归先3FAIL后19项通过，停写后完整七门均0（237文件4519PASS／0SKIP），1069非文档输入无漂移；受管Redis PONG／119→119，未单独重跑全站Playwright。仅重载App，其他六监听不变；没有业务命令、模型、工具或积分写入。Platform 已提交 `3fc971edbd99e0c0fe7d8a30a3ebf872f57f5b3c`：两 Publish 的明确 publication 条件进入原摘要与v2回执，成功重放优先，新执行同事务确认／CAS／回滚；无新服务／表／API。最终完整10阶段均0（168文件2573PASS、442资源SKIP不计通过），39冻结源码／artifact输入无漂移、正规再生成无drift；真实隔离PG发布／导入61PASS／0SKIP，临时库余量0。首次3业务RED、首全套15旧fixture／原HTTP负控次序FAIL保留，配对后重跑；原独立历史interpreter、raw向量和完整父图保护不放宽。独审无确定阻断；HTTP6.3与旧publication原字节保持，MCP只更新import闭包descriptor及bytes/hash，不动连接器业务。正常仍是旧owner，尚未push／PR／merge。BFF现已提交c707f5c7a5f7328f7b405967dd6d069df4166713：Public22/176两发布必填确认快照、固定3fc Native artifact，摘要匹配8条owner向量，Admin snapshot冲突412／false而普通in-progress仍409／true；完整七门exit0（contract862PASS、architecture36PASS、default1514PASS／3原资源SKIP），719非文档输入无漂移，独审无阻断。四相关仓非递归fetch成功、远端main仍是候选祖先；无新服务／表、无正常切换／push／PR／merge。Admin owner已提交e95aba22d6ffc59a2c5979db39418b9a67f2822f：GetAdminSkill既有详情tag2显式空／真实pointer/version，撤回停用隔离保留、断链与跨tenant/series拒绝；沿原确认profile1.1完整父逆证，无新API/服务/表，取消与P2028均RED后修复。最终完整10阶段均0（2581PASS／451资源SKIP），22输入门内无漂移，真实隔离PG9PASS／0SKIP且自有临时库余量0，独审无阻断。正常未加载、未push／PR／merge。BFF已提交 `be5cc6f91145d46ea504420b29b16ff16c981f28`：沿既有Admin详情保留data并增加明确publication，固定e95 Native artifact；完整七门exit0（contract874PASS、architecture36PASS、default1526PASS／3原资源SKIP），719非文档输入无漂移，独审无确定阻断，远端main仍是祖先。真实二进制Connect peer验证不是owner数据库／IAM／正常页面整链；正常服务未切换、未push／PR／merge。App已提交 `83ff930ef75431814ebdccde071ae1c81cff0fb0`：固定该BFF/Public22原件、六SDK正规重出，已有系列确认前读历史并冻结，失败不猜null，未知结果／重试不改body/key；新系列明确null。最终七门exit0（contract297、architecture50、237文件4524PASS／0SKIP），1069输入无漂移，独审问题均实际RED后修复并批准。隔离Next／CUA验证503恢复、关闭重开后原请求、612／390窄屏及Escape；浏览器之后仅aria-busy收紧open/admitted，最终回归承接。自有preview已清理；未单独跑整站Playwright，不是正常owner整链或完整Manus像素验收。13仓fetch成功，保Root4ahead/4behind与WIP、未盲pull；正常服务未切换、未push／PR／merge。Admin已提交 `d7403b1583b1b35adf67020b0beeeb24a2394a76`：固定Public22/176原件、仍39消费，详情required publication和官方publish配对；确认冻结原Skill／publication，ACK不推造新快照，未知刷新沿原body/key。最终七门exit0（26文件224PASS／0SKIP），134输入无漂移，独审无确定阻断。正常四端现已以Platform e95aba2／BFF be5cc6f／App83ff930／Admin d7403b1配对重载，保留回滚源码及原配置，Schema／依赖不变，App旧next-env字节保留，其他监听和BFF Agent disabled不变，四源冻结复核无漂移。正常后台经同一Product会话读取目录及withdrawn v2详情200，加载完成、发布按钮禁用且无新OAuth；CDP正文不可取，未声称读到精确publication内容，不以UI或受控组件冒完整写生命周期。下一步继续正式替换／恢复新UID与后台完整旅程，再处理删除／公开身份矩阵／MCP；模型／工具／扣费暂停，未push／PR／merge，Root不提前pin未发布候选。恢复新UID旅程、删除、公开身份矩阵、后台和MCP等完整目标仍保留，模型／工具／扣费暂停。

正常源码已按 Platform `efe1ed1` → BFF `d28f7db` → App `e9bc2a3` 配对重载；各候选再次非递归 fetch，远端 main 均为候选祖先。保留旧 SHA、私有配置／进程快照及回滚源码；App 原 `next-env.d.ts` 字节保留，配置指纹和其余四个服务监听身份不变。没有 Schema、账号、权限或执行开关变更；BFF Agent 仍 disabled。预检最初将格式脚本路径变化误当依赖变化，确认仅 BFF format:check 增加两条已验路径后收窄精确校验；两次预检失败均发生在停止服务之前。

真实浏览器已走本人管理菜单→历史 GET 200→current v2 精确目录／正文 200→旧 v1 两文件及附属文档 200→切回 v2→刷新重开。刷新前后历史／publication 完全相同，原 v1 安装仍停用；390×844 实际 history dialog 374×828、x8/y8，页面无横向溢出。这是正常 App/BFF/Platform/Storage 数据读链，不再只是 HTTP 夹具UI；不代表写生命周期、完整公开身份或后台旅程已完成。初次历史读取短窗无截断；整页刷新宽窗截断，保留其边界，不声称完整网络零写；可见额外 POST 为正常 auth/session，未发业务命令。

本次发现并保留两项下一步：历史 current v2 的 publication 已撤回，UI 尚缺撤回状态标识；现发布仅锁新 draft 与提交时 publication，仍缺用户确认时的 current/version fence。沿现 PublishSkill 增补明确 publication precondition，纳入原摘要／幂等绑定，先回放成功 receipt 再核新执行前置条件；冲突不自动刷新期待值重发。复用新 UID→独立上传／扫描／校验／发布，不复用旧 Storage scope、不升级安装、不借恢复绕过 quarantine。不新增服务或表；正式契约设计与实现仍待交付。

本地收据与截图仅留 ignored `var/dev/skills-publisher-acceptance-20261021/history-normal-*`，重载收据为 `personal-history-normal-activation.json`。模型、工具执行与扣费仍暂停；同事自动化／连接器不接管。尚未 push／PR／merge，Root 不提前 pin 未发布候选，完整目标 active。下方“正常未激活”等仅保留本次配对之前的阶段事实。

## 2026-10-21 Skills 历史链当前实施切片

**当前已验证源**：Platform 分支 `codex/skills-personal-history`，本地提交 `efe1ed1a3f81e87df1edded53e6e796d20edea55`（未推送／未建PR）。HTTP6.3本人系列历史已实现并独审；真实HTTP＋隔离PG23PASS/0SKIP；默认套件167文件2563PASS、435资源用例SKIP（不记通过）。类型/lint/契约生成及publication/Schema/Prisma validate/格式/构建均0，冻结21输入不变，生成物无diff。首两轮失败完整保留，实际通过证据在本地 ignored `var/dev/skills-publisher-acceptance-20261021/personal-history-final3`；不把旧raw字节归一化来放宽既有保护。

**当前消费者切片**：在现有 managed BFF 工作树 `codex/skills-normal-pairing`／`192396d` 上接 Public21.2.0/176 和固定 Platform6.3，保留现模型配置字段，不回退主线旧契约。历史GET、当前主体、查询闭集、严格嵌套／原始JSON、精确current和末页cursor已接；定向46项及两次生成漂移检查通过。现已提交 `d28f7db8b84deb7305fd4212c1469347c0e63e2f`（未push/PR/merge）；完整七门exit0：contract857PASS、architecture36PASS、default1509PASS/3原资源SKIP，23输入无漂移。首次3处随新增文件／固定版本未配对断言已更正并完整重跑，原失败保留；未运行BFF实际PG/Redis或正常App页面，不称整链交付。BFF只读独审发现的165重复归一与重复原始键已修复，原父证明不放宽。接下来核对正常App/BFF/Platform配对并做历史读链真实回读；随后复用现新版本上传链实现替换与恢复新UID并补publication确认fence。App Skills指南已同步候选范围与删除观察，页面尚未激活，不以owner门通过称产品闭环。正常服务／数据库／执行开关不变；Root不提前pin未发布子仓提交。 App现固定该BFF原始snapshot并正规重出六现有窄生成器，history独立弹窗及managed精确包路径已接，非最新current／分页快照／迟到正文／重复JSON键／信号被忽略后的取消均有定向回归；App现已提交 `e9bc2a3be1c6cc2d67d6a64e142c7ce2172f3374`（未push/PR/merge）：完整七门297契约/50架构/4515默认测试全通过；仅随后两个CSS间距调整，再经相关15项、完整webpack构建和post-types全0。实际Next/CUA的同参考视口及390窄屏、精确选版／文件切换／同文件重选／Escape／聚焦Enter均通过，明确为HTTP夹具UI；未正常激活，不把组件通过视作整链完成。自有预览进程和临时源码副本已清理。

登录／退出阻断已在正常环境验证；长地址及 pending 体验保留后续项，不继续扩大认证改造。当前主控独占 BFF 消费者写区，Platform 历史 owner 已停写提交，继续固定消费者接线、历史预览、替换与恢复新版本。三设计结论见 Platform 现有 TECHNICAL_DESIGN/API_CONTRACT/DATA_MODEL 的“个人系列历史”段。恢复不得直接复制旧 Storage scope 或更改旧 UID，仍缺用户所见 publication fence；Manus参考样本已获当场确认并删除：DeleteSkill200/{}，旧GetSkill404/not_found；历史入口消失，物理包清理未证明。

只读身份审计已确认公开 API Key/standard Open App/trusted client 三身份 producer 与 BFF 准入未完成，现 Product fresh-human 读取不等于该矩阵完成。IAM 新边界先走既有设计门，不去除内部 guard、不借机器身份冒充人类。本轮不触碰自动化／连接器写区、正常数据库和服务，不启模型、工具执行或扣费；完整 goal 与原积分／Agent／首页等遗留均保留。

## 2026-10-21 最新执行目标与遗留需求总表

本节是当前跟进入口，覆盖下方历史排期与状态；历史段落只作当时证据，不把旧“待PR／暂停／已完成”自动视作现在的事实。仍使用本计划及 `docs/CURRENT.md`，不新增任务中心。

**最新执行目标（2026-10-21 用户再次确认）**：彻底收敛登录、积分、Agent 正式流程与首页／新建任务／会话的 Manus 对齐；允许必要的重构／重写，但按完整业务切片逐轮交付，不同时扩散所有模块、不新增无必要服务或兼容分支。当前先完成登录阻断及新登录验收；文档放 App 仓库持续维护，验收审查后集中逐仓 PR merge，不等 CI、不绕强制保护。模型调用、工具执行与扣费仍暂停，真钱支付后置。

| 当前顺序 | 闭环范围 | 明确完成条件 |
| --- | --- | --- |
| 1：登录收口 | 正式 IAM client/resource scope 配对、失效本地 operator 配置恢复、Product 页面与会话 | 正常新登录返回原目标；错误／过期／重复回调回干净产品结果；较新登录、旧会话和续期不被破坏；API 保失败语义。用户已明确授权备份后恢复本地 OAuth 管理资格和仅重载 IAM；不改密码、平台角色、其他账号或积分。 |
| 2：积分业务链 | 无感初始化、当前租户充值／余额／不可变流水、后台维护、正式实际用量结算 | 复用既有 Billing／IAM／System／Agent owner；按现 model list／精确配置计价，聚合使用量后在结算点统一整数取整，重试／分片／重复回执不多扣；取消／失败／未知结果正确释放或保 pending。隔离验收与正常真实消费分开，执行暂停期间不称已验证正常扣费，不用手工扣分或假用量替代。 |
| 3：Agent 与会话主路径 | 正式配置解析／准入／派发／AG-UI 流／恢复／取消与用户反馈 | 单一协议、受信 tenant 与精确模型／技能版本；发送、停止、断线回放、刷新历史、错误恢复不丢消息／草稿、不重复提交，不把开发配置错误当普通用户操作错误。先完成配置和隔离链，正常模型／工具执行另按最新授权放行。 |
| 4：首页与新建任务 | Manus 同视口截图、DOM／样式、实际 API 输入输出与完整动作对照 | 首页场景入口、新任务／会话创建与路由回填、编辑区、菜单／弹窗／快捷入口、空态／错误／返回／窄屏连续缩放逐项自验；组件按职责拆分，不只修用户截图、不造成功状态。 |
| 5：既有遗留与集中交付 | Skills 公开身份矩阵／历史／替换／删除／后台、MCP、App 公开／内部文档 | 保留原完成条件，先核同事写区并复用正式能力。各 owner 本地验收与审查→集中 PR merge→Root 精确发布组合→正常加载与回读；未完成或未执行项明确保留，不能把一次登录修复称全目标完成。 |

**既有目标完整保留**：Skills `/v1/skill.list`、owner/BFF/App/Admin 正式旅程、MCP 生命周期、模型管理候选及其余原需求均不关闭。账户／积分和首页／会话为本次最新优先要求；不以重构授权覆盖他人未交接代码、扩大自动化／连接器写区或重置正常数据。

**本次跟进核验（2026-10-21）**：GitHub 只读回查 App PR42/43、Billing PR2、Platform PR10、Root PR59/60 均为 `MERGED`；System PR1 仍为 `OPEN/DRAFT`，远端 head `dafbc66`。下表五个模型／账户候选提交经本地复核仍一致；App 在 `1a13f2e` 上另有本地已安装技能作者显示修复及定向测试，尚未提交，不能再将该工作树记为 clean。IAM 财务授权工作树有未提交改动，保留原 writer，不计作已交付。此处核的是 PR 与源码状态，不以它替代运行加载和页面验收，也不代表本次重新拉取了所有远端分支。

**立即下一步**：同Session并发续接及原生退出中文产品页均已正常加载、验收。继续收口登录长签名地址与pending预算恢复，再按既定顺序进入积分；Skills身份矩阵/历史替换删除/后台与MCP全范围继续保留。只做必要修改，保原生state/PKCE/nonce与退出确认、不自动写重试、不接管同事写区。

**本次续接定位与修补（2026-10-21）**：正常App76326e5已补原生HTML失败产品恢复，API保失败status；固定phase/status诊断明确同issuer Session并发原生400 invalid_grant。IAM独立候选1c4209b保原where锁后目标/id/userId/token与到期／撤销，移除普通属性的隐式整行CAS；真实PG屏障由[400,200]变双200，独立签名query／PKCE兑换／nonce通过。IAM完整verify119文件1517PASS，真实三文件19PASS／0SKIP、511输入无漂移；App完整七门及236文件4501PASS／0SKIP、1062非文档输入无漂移，独审无确定阻断。正常仅再重载本方IAM，复制原配置字节，原main不改、其他服务和执行开关不变；真实双密码两笔均返回产品，一边历史正文、一边技能设置可读。原用户隐藏标签仅确认原路由，不冒正文已验；本轮CDP一窗截断，不冒完整网络证据。接下来收敛英文原生退出页与长签名地址／pending预算恢复，再进入积分。全部目标仍active，本批无push／PR／merge。

**退出页本轮闭环（2026-10-21）**：App43278e5保留原生issuer确认授权链，仅将合格native HTML确认发行投影为固定中文页；无hint、vendor HTML解析、新服务/持久状态或Origin:null例外。独审发现并实际RED修复重复failed参数的Page/Proxy分歧。最终完整七门均0、236文件4504PASS/0SKIP、1064非文档输入无漂移；首轮4503PASS/1FAIL缓存预期与Next开发覆盖事实保留，协议no-store不放宽，独立构建后五份生产文档no-store/no-cookie及状态通过。正常仅App重载，正式菜单→中文页→刷新→Tab/Enter→1次canonical-Origin确认POST/303→密码重登→历史正文实读，失败重复query无form；390×844无横溢/44px按钮、精确截图与视口恢复均完成。13仓fetch/prune全成功/main无变化，无push/PR/merge。模型、工具与扣费暂停，自动化/连接器不接管；长签名地址和pending预算恢复仍OPEN，不把此UI修复记为完整目标完成。

**最新交付补记（2026-10-21）**：App PR44已合f9d45e5（独立个人技能版本管理／作者），BFF PR15已合feae0c0（个人／项目并集），Root PR61已合2e008595，组合两个精确gitlink并升级既有API Docs到Public19.0.1。门户159公开接口／344schema、6网站私有接口排除，完整43测试／5fixture示例／来源／确定性生成／架构／构建／链接通过，真实桌面1280与窄屏390自验搜索、菜单、锚点、关闭恢复和无页面横向溢出；模板外露／正则语义／表格溢出缺陷均有修复及独审。App无observer配对完整门：main4434PASS、候选4451PASS，生产输入无漂移，新增5行仅失败诊断；保留早先JSON500未归因，不称已修复。已合topic仅在无新增提交后清理。该批交付时正常服务尚未切到新组合；现已按本页最新正常配对记录更新，PR、fixture或文档仍不替代实际整链验收。

账户／积分及MC-02仍按本节优先级推进；本批不夹带它们尚未交付的候选，不改同事自动化／连接器。Skills历史／替换／删除、Admin及外部身份仍保留；模型、工具、扣积分运行开关未因本批改变，真钱支付后置。页面→API→持久化／状态→刷新→失败恢复由Agent自验，普通打开／刷新不再交用户代测。

**正常配对已落地（2026-10-21）**：为避免回退已在正常环境使用的模型配置，隔离BFF以本地模型候选为基线承接已合Skills并集并合入main，提交 `192396d29678e7977fce9c4ab837b249aaf1af93`／Public21.1.1／175操作，raw SHA256 `eff6676131081b20ba36fd4be243075c568ebd27358662a9c09fe3216b097848`。App `ee1d4a7e69e5dce45d1df8092039a8209dfd9336`、Admin `04662c4a9f568305ad6feae26bf282857deea7ff` 正式固定同一原件；六既有窄生成器正规重出，Admin39消费／155递归引用及security不变，旧vendor退休，历史证明仅构建／测试使用，无运行时兼容。三端相关完整七门均0：BFF854 contract／36 architecture／1507 PASS+3既有资源SKIP（事前固定单并发），App296 contract／50 architecture／234文件4469 PASS／0SKIP，Admin25文件217 PASS／0SKIP；各自非文档冻结输入711／1058／133逐项保持，独立审查通过。

已按当前目标及主线 ancestry、冻结字节、原source/进程启动身份检查，正常三端仅fast-forward并原配置重载；未改Schema／数据库／登录／权限／积分或启用模型／工具。正常App仅有Next自动生成的dev route类型导入单行差异，未提交、未当业务修改。实际Product页面自验列表→详情／真实Owner→正文→更新表单→取消回搜索焦点及刷新：列表／详情／self-managed GET均200，原样本始终revision1、installed=true、enabled=false、source active，正式管理source／series精确相同；390正文无页面横向溢出。首次长网络窗已截断，只作局部证据；随后完整短窗4个GET／0 Skills写请求，未再发布样本或执行技能。原2份隔离环境失败保留：双物理React图确认后仅重配本方依赖链接，385定向通过；缺测试Redis配置的4467 PASS／2SKIP+suite FAIL，复用既有受管实例后7项真实Next及最终完整门通过。未删断言、增skip或放宽超时，不把本轮通过当旧偶发JSON500根因修复。

Root及12子仓重新非递归fetch/prune均0；12个主目录main与origin/main均0/0且无新HEAD，Root原4ahead/4behind及混合改动保护，不盲pull覆盖。本批仍未push／PR／merge，不把三个本地模型组合提交算作主线已交付，也不改Root为未发布gitlink。正常Admin页面及公开skill.list正式身份／权限矩阵、历史／替换／删除和后续MCP仍待闭环；普通Product读取不能替代这些验收。账户／积分及MC-02既定优先级不变；FG2只读核定可由主方沿已批准设计认领，先冻结既有26路径并修配两处旧contract inventory/version oracle，再按原owner门推进，不另造开户或资金旁路。

**参考写旅程与文档补记**：用户批准后已实测 Manus 个人纯文档样本替换／历史恢复：Upload200→历史2项→Restore200→历史3项，新 current UID 独立于两个旧 UID，旧版本保留，选当前回读原正文；未执行／分享／删除。Root API对照及 App `6ebf078` 的 Skills指南同步记录，不把后台quarantine恢复或撤回冒成版本恢复／删除。FG2独立复核原候选515文件无漂移，定向93PASS／6FAIL；除了两旧contract oracle，入口全程budget4负控仍RED，另发现正规machine null字段被拒、原始身份头歧义及正式resource scope配对缺口。FG2本轮未改源码或正常授权／资金，不用其局部测试称积分整链完成。

**文档位置更新**：按用户要求，完整产品文档站归 App 仓库，复用门户并覆盖用户手册／开发者 API／内部工程说明；公开与内部发布隔离，契约事实源仍归各 owner。实施／维护及迁移验收见本计划 Wave 5；本轮只完成可行性和边界记录，目录尚未迁移，不另建任务中心。

### 当前执行顺序与交付条件

执行顺序以上方五步表为唯一依据；同步、复用和验收贯穿各步，不另设相冲突的排期。

- [x] 登录 scope 配对及产品失败页：已加载 App `acd28c6`，SSO 与真实密码登录已验；该批尚未集中 PR。
- [ ] 登录并发及体验：原生隔离、同Session续接、中文退出确认已正常加载；最新App完整4504PASS、IAM完整1517PASS/真实19PASS，双密码、正式退出/重登及历史回读通过。长签名地址及pending预算恢复仍待，完整登录体验不提前勾完成。
- [ ] 账户／积分与模型依赖：承接已合初始化；完成当前租户无感展示、充值、余额／流水、后台，以及 Billing 统一整数实际用量结算。现模型候选继续后台页面验收；正常执行暂停，不以隔离 fixture 冒称真实扣费成功。
- [ ] Agent 正式主路径：首页／聊天按上表第 3、4 步推进，保受信上下文、精确版本、AG-UI／UIMessage、恢复与取消；先复现再修，组件按职责拆分。
- [ ] Skills／MCP 原遗留：三类公开身份 producer、历史／替换／恢复／删除语义、后台完整旅程仍待闭环。旧 `PersonalSkillsRead` 当前无生产调用，不把其按最大 revision 选项误当正式安装列表回退；正式列表保精确安装版本。历史安装撤回受 current publication CAS 限制，先确定动作语义，不静默改为撤回最新版本。
- [ ] 集中交付：各 owner 本地相关门与审查、页面→API→状态→刷新／失败恢复证据齐备后集中 PR merge；随后 Root 精确 gitlink、正常源码配对及关键回读。PR、本地候选、Root pin 和运行版本分别核对，不等 CI，不绕强制保护。

主方只维护已确认写区；自动化／连接器由同事负责，未交接不写。仅清理已合、无新增提交且无人使用的自有分支；不丢弃他人修改。模型调用、工具执行与扣费暂停，真钱支付不做。项目布局保留后置，不能因为聊天局部通过记作项目已全部完成。

Manus 是可观察的产品交互及 API 输入输出参考，不把截图中的套餐金额、赠送额度或未观察的内部取整算法当成 Kokoro 已批准计费规则。每项继续记录 owner、下一步、依赖／阻塞和验收证据；本次只是需求与执行记录更新，不代表实现、运行放行或发布。

### Skills／MCP 已交付事实与未完成项

| 工作项 | 当前状态与证据 | 下一步／完成条件 | owner 与写区 |
| --- | --- | --- | --- |
| Skills 本地 ZIP 导入 | **owner与Root已合、正常主路径已验**。Platform [PR #10](https://github.com/LordFoxFairy/kokoro-capability/pull/10) 合并 `c9862466267e6545c0b7f191357e9b8182dcca89`。修复既有获取来源持久化及 Platform Connect内部Finalize/Get 投影缺失（owner测试证明）；浏览器JSON不直接暴露该字段，只证明原严格BFF消费与正常主路径成功；原未知结果经只读查询恢复，新纯文档包 Begin201→Complete200→Finalize200，精确参考文件可读。 | Root PR60已pin该已合SHA；保留两份验收样本及证据，清理另按产品恢复能力处理；不增加兼容分支、Schema 或重复上传。 | Platform `modules/skills` 与既有导入事务；Root 只集成。 |
| Skills 公开 v1 合同与身份语义 | **并集已随PR15合入、Root61已pin，正常21.1.1组合已加载**；完整Manus身份语义待配对。当前Product人类路径有定向/owner-peer证据；API Key、普通OAuth自身Open App、trusted client对象范围尚无等价整链证明。完整精确项目安装优先（包括停用），个人独有保留，保持独立分页、1000上限及前后项目授权。 | 按已确认规则完成现聚合并集与受影响契约/回归，验收后交付并正常配对，不改变精确版本或执行授权；在 IAM/BFF 既有能力上核对三类身份映射、项目参数与对象范围；未批准的新身份边界先明确裁决，不把 human Product 准入冒成三模式均完成。沿唯一机器契约补消费者与真实权限负控，不新增公共网关或旧协议入口。 | IAM 身份/授权；BFF Product API；Platform 数据事实。 |
| Skills App/Admin 完整旅程 | **个人发布入口／作者已随App PR44合入，正常ee1d4a7已加载；全旅程未完成**。正常旧切片的版本2发布→撤回证据保留；新组合重新完成列表／详情／正文／正式更新表单读取、取消回焦与刷新，原版本1仍安装且停用，实际GET与精确source/series绑定。App最终4469 PASS／0SKIP，原偶发Next JSON500未归因，不声称修复。Admin固定契约217PASS不等于正常后台全旅程。 | 按[实测规格](../../MANUS_API_ALIGNMENT.md)继续核历史／恢复、替换与移除语义及管理员旅程／权限负控；现无正式series历史接口，旧name/scope接口与管理员隔离restore不复用冒充；不以撤回改名冒删除，不用旧安装虚构新版本。保留偶发Next开发态500和原失败证据，不凭单次重测称已修；复核本切片交付条件后集中交付，不因未确认根因改写登录业务。未修改断言或放宽门禁，定向通过不替代完整门。后台工具拦截不绕行，参考样本删除另确认。既有PG71／peer HTTP17仅对应其隔离证据。 | App 技能子组件、Admin Skills 子组件；BFF/Platform 原操作。 |
| Skills 安装详情作者 | **已随App PR44发布并在正常新组合复验**。详情按精确安装的publisher_profile展示Owner，缺失不猜个人名，官方来源保留品牌。 | 正常612×766菜单／作者及390×766详情／更新表单已读；这不是整页Manus一比一或完整发布／删除旅程证明，不再将20e本地修复误记为未发布。 | App 现详情组件及定向测试；无API/Schema变更。 |
| MCP/Connectors 全生命周期 | **已交付的读取/可用性/受管包和隔离 OAuth 证据保留；远程 OAuth/stdio 正常完整生命周期仍未证实**。ZIP 包不是所有 MCP 连接方式的替代。 | Skills 之后先同步同事的最新成果与写区；复用已有能力，逐项核连接、授权、发现、续期/重连、停用、撤销及未知结果恢复。实际执行证据与控制面证据分列；未交接前不改同事模块。 | Platform/MCP、Agent runtime、BFF/App；自动化和连接器当前由同事负责写入。 |
| 组合发布、手册与清理 | **分批交付，不宣称全部 PR 完成**。已合项、仅本地候选、正常加载分别核验。 | 各 owner 本地验收/审查→集中 push/PR/merge→Root 精确 pin→正常加载/关键回读；不等 CI，不绕强制保护。只删除已合且无新提交/无在用工作的分支，保留未交接改动。功能手册注明已支持/未支持/未验与已批准差异。 | Root 集成；各业务 owner 保有唯一写入边界。 |

### 账户、积分及其他既有需求明细：未完成，不丢单

| 原需求 | 当前状态 | 后续最小闭环与验收 |
| --- | --- | --- |
| MC-02 模型管理、BFF/System 配对 | **本地候选待正常页面验收及交付**。System `550d654`、Agent `c2c7cf9`、BFF `f3da7d5`、Admin `4c8ec04`、App `1a13f2e` 均有本地提交；System [PR #1](https://github.com/LordFoxFairy/kokoro-system/pull/1) 仍为旧 Draft，未包含全部最新候选。 | 保留共享 provider/模型配置、各业务组合/默认项/可选别名、原模型名、精确修订与当前租户；Admin 直接写入 API Key 且不回显，System 现模块加密保存，Agent 按正式绑定领取。完成表单、保存/发布/切换、失败/未知恢复及实际页面后集中交付，不恢复手填密钥文件/handle的旧入口。 |
| 账户布局、身份菜单、切换闪动 | **闪动修复仅本地已验，整页仍有差异**。App `1a13f2e` 已有鼠标/键盘切换与冻结测试证据，尚未发本批 PR。Manus 用户名/头像、个人身份菜单、姓名行和积分卡已观察。 | 按现组件去除多余标题和占位布局，统一用户名/头像，核姓名保存语义、身份菜单与响应式；保留同主体草稿、CAS、未知结果恢复与跨主体清退。个人身份菜单不实现成重复 OAuth 登录；未观察的团队创建/多租户切换不造成功状态。 |
| T07 当前租户积分与后台管理 | **Billing 初始化已合，用户链仍未闭环**。Billing [PR #2](https://github.com/LordFoxFairy/kokoro-billing/pull/2) 合并 `158579f8`；IAM 财务授权候选仍未提交；Agent仍缺正式消费许可接续，Billing运行入口未装配Admission，旧计价仍收caller金额并限quantity=1；usage2证据到冻结费率/结算的正式链待接。当前租户充值、实际用量非零扣减及正常管理页面尚无完成证据。 | 复用内部初始化，让用户无感；当前租户充值/余额/不可变流水、实际用量预占→结算/释放及后台维护走正式 owner API。明确计费单元、取整算法、失败/取消/重试口径；聚合实际用量后由 Billing 结算时统一整数取整，不按流式分片或重复回执各扣一次。价格取正式配置，业务模型由 model list/default 解析；不用手工扣分或假用量替代。参考 Manus 产品，不引入 sub2api 代码/依赖，真钱支付后置。 |
| T00/T01/T05 聊天主路径与技能选择 | **不可用反馈有本地修复，整体导航/阅读与消息技能入口待验**。 | 保留历史/草稿/焦点、滚动和前进后退状态，局部刷新不清空整页；未知提交不自动补发。技能选择使用正式安装引用与精确版本，沿 AG-UI/UIMessage 和现引擎，不另建协议或全局框架。参考 Manus 与 Vercel 的职责划分，先复现再修。 |
| T02/T03/T04 项目工作区 | **局部交付，不是全部完成**。概览/会话布局、历史“最近/全部”语义、资源生命周期与 preview/live 可达性尚待逐项验收。 | 聊天稳定后对照项目概览/会话、指令/资源/技能、任务归属/移动和历史；390/768/1280及连续缩放验证。正式入口不使用演示数据或仅组件内模拟保存；沿现有 owner API，不扩网站托管服务。 |
| T13 首页场景入口 | **按钮和部分组件存在，完整行为待验**。 | 制作简报/网站/设计/游戏/更多的进入、切换、退出、模板/素材、草稿与真实请求逐项对照；无正式生成/发布能力明确标缺口，不只按截图判完成。 |
| T06/T10/T12 其他页面与同事写区 | **已有主线成果保留，未覆盖状态待核**。资料库新版已由 App42交付；同事设置 App43已合 `859f415`，不是“还没PR”。知识/记忆导入剩余状态、插件分类切换、自动化日历及周期旅程仍需对应证据。 | 自动化日历/列表/时区/一次性耗尽与 Agent 调度 MCP 需求，以及插件/连接器分类/详情/恢复先交给现 writer核验；本方只同步、记录、集成已交付成果，不重复做。资料库/个性化只修当前复现差异，不搬回整棵旧UI。 |
| 本批兼容代码审查与遗留 worktree | **需随交付持续审查**，不做全仓机械删码。 | 检查本批实际 diff 中旧协议 alias、双读双写、无依据 fallback、重复 DTO/实现和无用代码；有效业务规则、负控与预览用途保留。旧候选按归属/基线核对，确认已承接后再清理。 |

### 执行与验收约束

- 最新状态以本计划首节为准：App44／BFF15／Root61已合；正常三端已按192396d／ee1d4a7／04662c4本地组合配对并自验Product读取。该模型组合尚未集中PR，Admin与公开身份完整旅程继续保留；不把旧观察器、正在跑baseline或未配对字样当当前状态。

- 新增明确交付要求：按“页面动作→实际Manus API输入输出→Kokoro唯一契约→正常状态/持久化/刷新/失败恢复”逐项校正；由Agent完成整链自验，不让用户持续代测。API Docs纳入下方既有Wave5：可搜索的指南＋从固定owner OpenAPI生成的Reference；公开文档与网站私有RPC观察分开，已支持/候选/未验明确标识，不复制第二份机器schema或新建文档任务中心。

- 最新main集成证据：App独立切片基于859f415，相关108、生成/lint/types/build与预览2 PASS；完整两轮4450 PASS／1 FAIL，pending refresh JSON500仍未归因，未捕获受监视manifest空读取。不以原诊断4468 PASS替代当前门，不扩大登录重构、不把App失败扩散到独立BFF聚合交付。原正常模型候选/同事改动不混入独立Skills分支。

- 最新进展补记：上述作者修复的1122份冻结输入在正常源码与隔离验证目录逐文件一致；只有定向217项，不冒称重跑完整App测试。生命周期PG使用自建隔离库，结束后库库存恢复；正常数据、技能开关、模型／工具执行与积分均未改变。个人发布入口及新版本发布／撤回已按上表补齐；三身份、正式历史／恢复与管理员旅程仍未完成，不被局部修复冲销。
- 2026-10-21 Skills续验已补停用→刷新→仍安装且不启用→正文可读及390×766卡框对照；不是公开API／全角色验收。三身份缺口已由IAM当前源码确认，Device缺正式producer；沿现owner的设计确认待答，未先改权限或扩大写区。完整目标保持未完成，下一步只推进不依赖未决设计的现有旅程与受影响验收。
- 当前顺序按本节最新五步表。Skills／MCP 原条件不丢失；登录先收口，再按用户最新要求推进积分与首页／会话。所有执行／扣费继续暂停，不同时扩大写区。
- 同步记录区分 `origin/main`、本地候选、Root pin、运行源码四种状态。本轮 Root+12 子仓非递归 fetch均成功；Platform主目录随后快进到PR10合并SHA。Root和其他候选保留已有未提交/未发布工作，不盲pull或覆盖。
- 本次 Skills owner 格式/lint/types/契约/artifact/schema/build全部exit0；完整测试2562 PASS/432资源SKIP，明确真实PostgreSQL30 PASS/0SKIP；跳过不是通过。正常浏览器已验原结果只读恢复、新包导入及精确文件读取，未执行技能、模型或积分写入。
- 测试按变更风险选最低充分层级；修复补独有回归，交付跑受影响owner必要门，不因测试数量制造无效重复。截图/原始网络/机器配置只留ignored，Git仅含脱敏规格与验证结论。
- 当前运行 Agent guard 仍 disabled；这是真实运行状态，不以历史暂停文字替代用户最新授权，也不因本表规划自动放行执行。真钱支付仍不做。最终验收逐项说明实际完成、未执行、阻塞和后继owner。

## 2026-10-20 依赖收口：复用已合并的账户初始化

用户授权接手同事 Billing PR #2 后已完成冲突处理、本地完整相关门及真实PG/source-dist验收，通过原PR合并为 `158579f8`；Root PR #59仅组合该精确gitlink，已合为 `85c3b579`。不重复实现账户创建；当前唯一 `/v1`，没有兼容路由或额外服务。用户不感知开户是已确认产品语义，BFF/App配对和Manus实际请求/响应对照仍是后续切片；本次未重载正常运行、充值或执行收费，不能把owner合入等同于用户链闭环。详见CURRENT的验证与遗留范围。

## 2026-10-20 当前优先：内部积分正式链与无感加载

用户明确后台是配置/账户/流水/充值的管理维护面，扣减仅指模型/工具实际消耗自动计费，不新增手工扣分。真钱支付继续后置，不触碰其他开发者自动化/连接器；页面实测后集中PR/merge、不等CI，仍保本地门与GitHub强制保护。

依赖顺序：主方唯一writer先在隔离IAM落实已批准FG2（当前财务actor与同tenant target分别验证、短时授权和审计）→Billing正式赠送/查询与原幂等账本→固定owner artifact接BFF/Admin后台→沿ADR-033实际用量预占/结算/释放、余额及流水回读。现有1000赠送属于旧tenant，不用它充当前验收；不直接改库/伪造usage/负grant。实际用量不明保pending，不默认免费或扣固定次数价。

本轮页面修复范围为模型和积分：去除突兀可见“正在加载”，首读骨架与真实空态区分、刷新保原数据、保取消/权限/错误和无障碍busy。只读已确认模型首屏空表闪动；App /manage rewrite和Admin basePath一致，尚无确定产品路由故障，IAB旧错误标签不算产品404。后台浏览器仍待普通目标恢复，不能以源码/接口代替；并行角色仅只读审计，主方写入/Git串行。复用现计划与owner三面，不新增任务中心或服务。

## 2026-10-20 积分验收预检：历史赠送不等于当前账户到账

用户明确扣费指内部积分，真实支付/真钱充值后置。只读找到10月16日既有1000积分“联调测试”赠送及原命令重放余额不变收据；但收据tenant与当前正常BFF受信tenant不一致。当前验证在发出owner HTTP前即按身份绑定拒绝，未拿旧subject拼新tenant，未跨owner SQL查询、重放赠送或改余额。

随后从现有正常Product聊天页的“用量与计费”入口实际读取当前会话：余额和积分历史均显示“尚未开通积分账户”。这是当前页面事实，不冒wire抓包或整个账本验收；原始截图仅ignored current-credits-not-opened.png。当前Billing main `3f5e0dacc25c1e24d87cbe0c59337d3b909466de` 的正常module只装本人两GET、Catalog和probes，CreditService grant内部能力不等于已开放正式管理员赠送/扣减接口；不能用目标契约、历史receipt或直接改库称本轮充值完成。当前1000积分到账与端到端扣减仍未证实，正式写入口是后继缺口，不在预检中扩实现。

本轮没有充值/扣减/真实支付/模型或工具调用，没有动其他开发者自动化/连接器。模型管理原后台页仍待正确标签交接，不用本次不同Product积分页面代替后台模型表单验收，集中PR/merge条件不变。

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

### Wave 5：App 完整产品文档站（用户最新要求，2026-10-21）

**归属与定位**：文档放入 `apps/kokoro-app/developer-docs/`，复用现有 VitePress 门户，作为独立文档包维护，不在 Next.js 内重写一套 renderer。它是完整产品说明站，不仅是 API 目录；Manus 是可实测的能力、交互和文档结构参考，Kokoro 实现事实及 owner 契约仍是说明依据。

**当前事实**：Root PR61 已合，Root 现有门户固定 BFF Public19.0.1，包含159公开操作／344schema，排除6项 browser-private；43项测试、fixture示例、来源／确定性生成／构建／链接和桌面／窄屏交互已验。尚未迁入 App，完整用户手册和内部文档发布边界也尚未实现；不把本计划当迁移完成。下述目标替代此前“在 Root 新建门户”的位置安排。

| 阅读面 | 内容与维护边界 |
| --- | --- |
| 用户手册 | 首页、聊天、项目、资料库、知识／记忆、Skills、插件／连接器、自动化、账户／积分及后台的真实入口、完整操作旅程、状态与错误恢复；未完成能力明确标注。按既定模块优先级补齐，不为写文档扩建业务功能。 |
| 开发者文档 | 快速开始、认证、概念、使用指南、可搜索 API 参考、输入输出／错误／分页／幂等及可执行示例。字段说明从 BFF 固定 commit+digest 的公开 contract 生成，不复制第二份可编辑 schema。 |
| 内部工程文档 | 现有 owner／调用链、配置与部署、调试／故障排查、验收及维护入口；引用各 owner 的 canonical 设计／契约，不把 owner 手册整套复制为另一事实源。私有接口只进入单独内部发布输入。 |

**发布隔离**：公开和内部内容分开构建、产物、静态资源及搜索索引；内部入口受真实访问控制保护，不用隐藏导航代替权限。继续保留公开 catalog 白名单和私有接口／敏感信息阻断，不为内部展示放宽公开 generator 的边界。HAR、截图、token和正常数据留ignored；只提交脱敏规格和文档。

**迁移与验收**：先在隔离 App topic 搬迁现有包并修正读取固定 artifact 的路径／构建命令／来源校验，保留已有门禁及来源证明；随后配对 Root 删除旧门户并更新链接和精确 gitlink，只留一个维护位置，无旧路径 fallback。迁移验收包含来源固定、确定性生成、示例、构建、链接、搜索／锚点／键盘／窄屏，以及公开产物中没有内部页面、索引和资源。普通说明按页维护布局／操作→API→持久化／状态→刷新→失败恢复对照；Agent 自行验收，不把测试交给用户。

**本轮实施事实**：App候选已从远端Root main2e008595迁入78文件，修正固定BFF路径并配对Public22，原generator／policy／lock／43项测试保持；门户完整check与App七门均0（239文件4547PASS／0SKIP、1118输入无漂移），实际桌面搜索精确API／字段及390菜单／无横溢通过。Escape关闭后的BODY焦点未当作回焦通过；Root旧目录／链接与gitlink配对删除、内部发布访问控制、完整产品手册仍未完成，未PR／merge。没有新增业务owner、网关、依赖或文档服务；具体收据见CURRENT及ignored app-docs-migration-20261021。

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


### 2026-10-28 本轮落地：旧会话 final 只读证明候选（展示未闭环）

- [x] 回核用户已批准的 final 列激活：正常check=current，保留后续BFF/App更新，不重复DDL/历史回填。
- [x] Agent主写 bounded checkpoint_final_answer；原factory精确源码已核，真实旧Run读取得到原final身份（48.89ms），无图执行/模型/业务写入。
- [x] 原生unit与隔离真实PG证明只读、不跨Run、输入预算、格式v4限制与public正文比对；独审P2已按RED→GREEN收敛，自有DB回收。
- [ ] Agent正式RunDisplay可选最终身份契约及既有5秒/输入预算接线；当前helper未接HTTP，不声称发行。
- [ ] BFF校验本人的准确Run/Message/parts与revision，返回只读adjunct；不UPDATE历史final列。
- [ ] App正式final优先，旧成功Run仅据本次有效adjunct复用整轮披露；不混入durable final merge、不补造旧阶段文字。正常conv6530对照/刷新/详情验收后再关闭此展示子项。

写区为Agent新增helper/两份测试及既有TECHNICAL_DESIGN，消费者尚未修改；现有Goal与唯一计划继续，不创建并行任务中心。

### 2026-10-29 真实 Custom API 取消与错误提示闭环记录

- [x] 复用 QA API Boundary 当前版本，实际创建 Run 并确认 Agent DB 中 `sandbox_id`、Docker backend、`execute/started`。
- [x] 通过正常 Run control 入口停止；确认 control receipt `persisted → applied`、Run `cancelled`、cleanup `completed`，并在同一 Docker context 查询容器不存在。
- [x] 修复 Agent Custom API transport 对 Platform Connect 结构化错误的丢失：配置状态冲突/不存在与 owner 不可用分别进入 typed client error；不解析错误文案、不保留上游异常上下文。
- [x] 为现有公共错误闭集保兼容：配置错误在 `assembly_failed` 非重试外壳中传递，Web 改为中性提示并刷新实测；没有新增跨仓枚举、没有改 BFF Message CHECK。
- [ ] 若产品需要把“API 配置无效”作为独立公开 RunErrorCode，另开 Agent→BFF→App schema-evolution 切片：先更新历史父图与生成物，再升级 BFF 持久 CHECK，最后重载消费者；本轮不把这项未做的契约扩展冒称完成。

本片证据：Agent `c43fc3f`（最终工作树相对既有 `c6c8073` 仅含 Custom API typed transport/failure handling 与回归测试）、App `c222b2e4`；浏览器和私有权威回读位于 ignored `var/dev/custom-api-boundary-20261029/`。默认 App 359 文件/6894 测试继续复现原有缺失 `KOKORO_TEST_REDIS_URL` 的 1 个 stored-session 套件（2 skip），本片未删断言或把该环境缺口称绿。


### 2026-11-02 新授权完整浏览器旅程及 App 正式交付

App `fe0bb6967b2962a9d5e9b88160c60d0a74bd912d` 已提交并推原 Draft PR49（34精确路径），正式配 BFF `e3b5fb759ee89523918ac06ebf3a738b4df4e346` / Platform `2cf63945feecd49f5b79c3532bbd7cbc5b70a3f8`，未合 main。独审限定 APPROVE；writer 相关8文件744PASS，Root固定artifact原3文件314PASS，lint/type/build通过；原完整contract的4个超时及全默认门历史红保留，不冒全仓绿色。治理测试原19入口列举补齐后26PASS，原18入口及顺序不改。

真实 IAM 独立 Chromium context 已验证断开配置→创建全新授权→owner提交200但浏览器故意丢响应→原key/body/双CAS重放→同一新connector→重新GET权威详情→显式点击Connect→真实DeepWiki Prepare200。没有自动Prepare，也未执行收费模型/Run/工具调用。刷新、390px窄屏、关闭回焦3项通过，后继读取均200且零MCP写，真实状态“已连接”。前两次验收脚本分别误以为成功后详情不关闭、已连接overview应显示URL，断言错误及截图原样保留；修正后的回读脚本通过，不把脚本失败写成产品成功。综合证据 `B01-reauthorization-real-journey-final.json`、桌面与窄屏截图均在本机测试结果目录。

固定no.git App artifact的1551个跟踪输入已逐字核正式fe0；仅Next dev自动将next-env.d.ts路由类型引用改为.next/dev，其余源码一致。原浏览器验证后只CURRENT结果段及原架构测试变更，产品代码未变。元数据 `B01-App-fe0-formal-artifact.json` 明示派生差异。正常3314/原库/其它项目进程未动；隔离候选仍60256，不能称用户正常页面已激活最新版。候选projection用途凭据与mcp-connection surface补齐后connections真实200；Storage末端尚503，下一片仅核正式Storage图标owner固定版本与最小运行配置，Task B仍进行中。


#### B-01-ICON-ENDPOINT：正式Storage接通与图标最终隐私响应

App后继 `075e75fd7de21e6e77dff89fecd32156fbf3bbe2` 已推原Draft49，保持P2cf/BFFe3和Public29；只给原Proxy exact binary GET集合加入无query、小写UUID的MCP图标路径，防Next覆盖route的no-referrer。8回归先1FAIL/7PASS，最终原Proxy/图标adapter真实HTTP/安全头3文件130PASS、scope ESLint和完整typecheck通过；独审限定APPROVE。未重跑原完整contract/default/build/E2E，不冒原全仓门消失。

固定正式Storage4a990617（315源码完全等值，Prisma官方生成、584 tsc产物），同一候选库官方安装独立kokoro_storage九表5.766秒，邻居326 catalog entries前后等值。既有PG/Redis/MinIO/ClamAV在线，使用本次独立versioning/ObjectLock且无默认retention桶、独立Storage service secrets；只补候选P两个Storage键、BFF一个object origin、Web既有development-only精确loopback upload origin。正常3314/原库和其它项目服务均未动；生产CSP不改。

真实IAM主路径已证版本PUT200、ClamAV Complete200、ready intent回读200、icon-only PATCH200、fresh server/刷新卡片自然同源图片200；后继原图bytes SHA/no-store/no-referrer/nosniff通过，另新draft取消200只释放新intent，server版本/原绑定保持，零server PATCH，390px通过（补验20.483秒，不是p50/p95）。先前CSP阻断、旧保存browser state失效、脚本未捕获waiter、no-store完整值误断言与实际最终Proxy隐私缺陷均保留原失败，分别恢复/修复后验证，不冒第一轮绿色。

候选当前Web075e/P2cf/BFFe3/Storage4a990/IAMb9；A/runtime-artifact-current.json的1551跟踪输入与075e匹配，仅Next dev自动route类型引用派生；最新持有进程/组合见本机F/candidate-runtime-boundaries-icons.json。证据B01-icons-real-journey-final.json与icon-bound-desktop/narrow.png在本机E测试验收。B01/TaskB未整体关闭；下一步只读收敛普通Provider目录与/manage同身份最小链及已有surface/凭据purpose，不重开全仓盘点，不让未就绪外部OAuth末端阻塞独立功能。


#### B-13-ADMIN-ENTRY：读取资格与会话代际

真实候选确认当前真人非平台管理员：Product admin-access200/false，普通Provider目录200真实空态，管理403与匿名401均正确，零业务写；初次直接读取早于Shell恢复的401保留。原Admin gitlink已登记但本机目录空，当前HTTPS/SSH身份不可读；未开启无消费方的admin机器通道、未提升角色、不重建假后台。此未就绪末端不阻塞其它独立用户功能。

同源读取发现侧栏原useEffect([])仅挂载一次，现App局部修复等可信准入、按subject/generation/preview退休管理投影、严格positive本人/内部manage路径及typed401原recheck。8项先RED；最终原两文件118PASS、独审限定APPROVE，真实候选普通账号菜单/回焦/390px通过。受影响ESLint/完整types结果与源码SHA随本片收据绑定；未重跑全仓门或后台正例，不关闭B01/B13/TaskB。下一独立切片为Custom API现有配置管理真实CRUD，不触发Agent/外部API执行。

App局部正式提交 78337ee4bcbd1ebdf3460d22052db056a1dae653 已推原Draft49，非main；最终原两文件118PASS、scope ESLint/完整非增量types均0。候选1551跟踪输入逐字绑定78337，仅Next自动route类型引用为派生；BFFe3/P2cf/Storage4a990/IAMb9与正常3314保持。


#### B-02-API-MANAGEMENT：当前正式候选配置 CRUD 实测

Web78337/BFFe3/P2cf固定组合，真实IAM独立Chromium，创建唯一自有QA profile后UI exact详情GET200，编辑只PATCH一次后fresh列表与浏览器exact GET保持新CAS；取消草稿零写/原CAS不变，reload后权威列表及密钥空白保持，显式删除后fresh terminal列表不见本次ID。全程仅本次POST/PATCH/DELETE各一次、无违界请求，非秘密TASK_B_BASE_URL按write-only规则不回显；QA已删除。五个旅程通过，开发环境完整操作共9503ms，非p50/p95或单操作延迟。未执行第三方API/Agent/收费模型/E2B，不以配置管理当运行闭环。证据B02-custom-api-management-real-journey.json与桌面图在本机E测试验收。B02整项仍OPEN。


#### B-02-E2B-FILESYSTEM：无进程受保护目录能力实施

Agent固定bfd1e9c；原公开files.list无预算并不排除其正式底层。已核SDK2.30 Filesystem.Stat/ListDir是unary protobuf且不启动进程；采用官方生成Request/Response编解码与现有HTTPX整体deadline/先限响应再parse，固定两只读operation，使用公开envd origin/sandbox_headers，不接SDK私有pool/登录shell或新依赖。沿原FileEgress一次fresh Acquire/inspect、全遍历原名、完整文件bytes、glob/literal grep和预算；普通无provider不变。不新增Schema、Run/HTTP/owner wire或服务。

唯一Agent writer task_b_safe_file_tools先更新现技术设计/API/当前事实与相邻INDEX的必要前缀，然后在sandbox/e2b_backend.py、file_egress.py与最多一个内聚metadata adapter实现；复用三原测试文件，真实RED后focused/Ruff/types/contract。Root独占Git/运行资源/独审/真实云箱。现Stat/ListDir/download是path-based，不能冒Docker原子dirfd或已解决E2B execute取消；真实模板mode/symlink含义须按官方源码/实际云箱核，未知failclosed。响应额外每RPC256KiB/总2MiB及有限请求数，原1024entries/128files/32KiB名字/64深度与8/16MiB内容预算保持。云钥当前候选/已登记运行env未找到，未断言全机没有；纯SDK替身/本地HTTP不当云箱。

### B-06：已确认本地退出通知（2026-11-02）

App 基线 78337，Root 唯一写入 product-auth-client、原 client/settings 测试及 auth INDEX/CURRENT；正式 ACK 删除原 hint，复用 storage 退役/重核，无 wire 变化。定向 RED 4 fail/1 pass，完整四文件初门 307 pass/1 fixture fail；正向 503 fixture 补正式 status 后，仅重跑已变原用例与 client，保留原断言。独审限定通过。真实候选旧卡片由 1 变 0；issuer 确认、自动登录/刷新竞争仍未验收，B-06 不关单。Root 继续最小交付与 Agent E2B 文件工具，不重演已过 CRUD。

### B-02：E2B Filesystem 源码交付（2026-11-02）

Agent bd82a7a1d5831c8f313140c893f1b95dda3e1095 已将 ls/glob/grep 接正式 Stat/ListDir 与有界 HTTPX；不新增依赖或 wire，Docker 原 dirfd 保持，运行配方闭集已消费新模块。独审有限通过；Root 当前四文件 130 pass/1 原 marker 未选（14.10s），冻结 Pyright/Ruff/format/contract 通过。真实云箱/正式授权、path-based 竞态及 execute 远端取消仍 OPEN，本片不关闭 B-02。App 本地退出通知修复 a51939c 已推 PR49；正式源1551文件候选60256一致，正常3314未切换。后继继续 B-01 四种创建→详情实际旅程，不重复已通过的 Custom API CRUD。


### B-03 / B-04：个人技能包主链与终结拒绝（2026-11-02）

复用原 Skills UI、BFF catalog/projection、Platform source/installation/catalog 与正式 Storage，候选仅补现有 workload purpose/surface，不创建新 owner、假目录或管理员权限。真实普通 OIDC 用户使用明确自有根 SKILL.md 包，已验上传、真实扫描、finalize 自动安装、fresh 权威回读/刷新；UI停用/启用保持同一来源和revision，文件树/预览及真正下载ZIP SHA与原上传相同，390宽无横溢。取消卸载零DELETE；显式卸载后owner无有效安装、刷新移除；真实目录Add重新安装，同一来源/revision的owner回读、目录Added刷新及Settings回读均通过。正向上传至刷新10709ms只是单旅程，不是p50/p95。

测试初包错误采用Storage独立fixture的子目录根形状，不符合本产品入口根SKILL.md要求，正式拒绝保持；发现真实错误分类缺陷：持久IMPORT_PACKAGE_INVALID后原校验错误被映成Internal/BFF503。Platform 2ad5c9e72ce32bd7b7e8f97a6918e066fa0ad399只在持久reject成功后转已有LocalSkillImportError(import_package_rejected)，复用FailedPrecondition→BFF412→Web rejected；持久失败/取消/未知不伪装终结，不新增wire/Schema或放宽根校验。RED13/1→service14通过，Root相关service/RPC63通过；scope format/lint、完整typecheck及官方候选build通过，冻结两文件独审有限通过。已推原Draft12，未合main。真实不合格包在新源实际412/拒绝，owner GET终结码与UI查询恢复/重选通过。

候选当前App a51939c / P2ad5 / BFFe3 / Storage4a990 / IAMb9；1120正式P输入无漂移、774编译输出，替换仅本次自有P进程并保原artifact/配置回滚，正常3314未动。正向导入/启停/下载证据绑定原P2cf，后继重装回读/错误分支绑定P2ad5；不拼成一次全版本全门。浏览器验收器对关闭详情、嵌入目录、搜索入口和目录刷新视图的错误假设原失败均保留；未以修改生产或重复未知写消红。E/技术方案与联调/B03-personal-skill-runtime-delivery.json汇总七份实际记录；下载handle已从公开报告脱敏。

保留唯一自有QA技能供B04作者/版本旅程，其余无 他人 数据清理。B03项目精确选择、更多搜索/分页与B04作者/版本/审核权限矩阵仍OPEN；B01外部Provider/Admin、B02真实执行、B06发行者恢复及B07–15原完整范围不因本片关闭。Root组合gitlink未集成，历史完整门失败继续保留；下一步沿已有本人版本替换、撤回与恢复入口交付，不重新全仓盘点。


#### B-04：作者第2版发布与用户显式安装升级（2026-11-02）

当前固定App a519/P2ad5/BFFe3/Storage4a990/IAMb9真实普通用户旅程：作者managed/history读取后创建第2版、真实包上传/扫描校验/发布成功；原已安装版本保持第1版，未隐式升级。后继安装更新先取消零命令，再单次显式POST200；同一安装fresh读第2版、刷新保持且更新入口移除，文件预览与UI真正下载ZIP SHA均绑定第2版上传包。两份当前记录B04-personal-revision-two-published-real.json、B04-personal-explicit-version-upgrade-real.json在本机测试验收目录。未改生产源码、未重复发布、未撤回/恢复/删除，B04全项与Root组合继续OPEN；正常3314仍未切此候选。


#### B-07：设备错误可见与 GET 恢复（2026-11-02）

App7fc8a6e6已提交推原Draft49：首次/分页失败从仅sr-only改现共享Alert可见提示，保原部分列表、GET重试与未知DELETE核对围栏，不改wire/Schema。RED2失败/5通过；组件及原hook19通过，scopeESLint、完整非增量tsc通过，冻结两文件独审无确定P0–P2。1551跟踪输入候选已逐字绑定新提交，仅Next自动route类型派生；真实登录UI注入一次读503，1280/390错误可见无横溢、Enter重试真实GET200，零账户写。原完整门缺口保持，正常3314未切换，B07不整体关闭。

#### B-04：撤回、历史内容恢复与新版本安装（2026-11-02）

当前App7fc8/P2ad5/BFFe3/Storage4a990本人真实UI：取消撤回零写，显式撤回v2一次200、owner/status与history publication同证；fresh撤回后CAS从历史v1包新建并发布v3，取消恢复未创建版本。新v3不移动原v2安装，后继显式更新原安装至v3一次200。原旅程额外刷新后GET遇真实429/session_rate_limited，保留失败，不重放生命周期命令；后继独立fresh读同一v3 active、文件预览及UI下载SHA与原v1相同，零生命周期写，仅下载句柄POST。不能合成原单次全绿。

当前自有QA task-b-qa-8e4ecca4的source为skill:5740b195-ea97-42e2-877e-cc7659aeb19f/revision3，同一installation enabled/installed true。B04-personal-version-lifecycle-delivery.json分别链接原429与后继readback证据；历史与已安装pin不是同一事实。英文恢复3条文案当前fallback中文，正补现有locale；管理员/跨租户权限、分享/删除/审核等仍OPEN，未冒全B04或TaskB关闭。


#### B-10：会话分享当前状态只读链（2026-11-02，实施中）

已核当前App/BFF只支持POST创建与DELETE撤销，打开/刷新无精确metadata读取；已分享列表没有share_id，不能替代或再POST冒读。BFF沿原conversation/project owner事实新增同资源GET：合法会话data.share nullable，active字段仅share_id/created_at/expires_at；原权限统一404，故障不冒null。现budget/signal单SELECT/LEFT JOIN，不写receipt/outbox/过期清理、无Schema或新owner/授权。允许一个具名build/test-only有限逆证明承接additive GET，原Public29 bytes与ordered200摘要保持。

BFF e3b5基线由task_b_api_postgres唯一writer实施原port/query/service/route/OpenAPI/相关测试及必要文档；Root唯一Git/集成/运行资源。owner交付验证并固定提交后App才更新精确artifact与ShareButton只读打开/刷新回读，保零发布、显式create/revoke与身份代际。E技术方案与联调/B10-session-share-read-closure.md记录已核生产/消费链与实际验收边界。未交付/未验，不因计划写入关闭B10。

#### B-04：恢复弹窗语言已交付（2026-11-02）

App6b8988611f2581f0f86e52cf57bedf2b452c009f已推原Draft49，补8个现有非中文locale各3个历史恢复键；不改生命周期、中文或安装版本。原resolver定向29通过，精确ESLint及writer完整非增量typecheck通过；候选1551正式输入逐字核对，真实英文历史恢复弹窗/390宽无横溢，取消零hub写，不创建v4。B04-history-restore-locale-delivery.json与-language-browser.json保存范围；原429旅程不改写为通过。当前Web60256绑定6b898861，正常3314仍未切换，B04全范围保持OPEN。


#### B-10：会话分享状态回读子链交付（2026-11-02）

BFF2e737cad9649460dc477fc7d96ba593783fef619已推原Draft17；沿原owner提供GET，Public29.1/201有限逆证保原29与ordered200，正式机械投影固定canonicalSHA。188相关、37架构、9最终契约及Node22独立正式构建通过；真实PG/Redis单选4.11秒通过，明确IAM admission替身。原过期fixture约束失败保留，仅修本人造数。

Appa0a97845ac2f5aee73fd73f374f38f36f0f8a1d4已推原Draft49。独立投影消费/原client与同源adapter、打开/重开/focus只读、命令后权威GET、身份/代际/范围退休接齐。审查修复旧复制跨窗口/新分享影响及Copied效果被无关重渲染触发的抢焦，原RED保留；145相关初门之后，最终48分享组件、ESLint/非增量tsc通过，v3独审有限批准。

正式候选App1557输入/BFF1141输入与1082编译输出绑定上述提交。真实OIDC同一无私密QA会话/原分享：刷新恢复、9次只读零写、受控503→真实200重试、键盘/390宽通过；另一标签撤销后重开权威null，显式后继分享/撤销、匿名页面不可用通过。公开页实际HTTP200呈不可用，不冒页面404；新QA会话为明确owner-table测试准备，不冒UI创建或真实Run。原首次创建验收器CDP取body失败与全局alert断言失败均保留，只核同资源/修精确弹窗oracle，不重放未知命令。最后通过现有owner API软删本人QA，metadata404/列表无该项；保原Skills v3不动。

暖打开5样本中位230.25ms/观察95th870.55ms，首次本次页面至链接3666ms；Next dev小样本，不冒稳定生产分位或100ms达标。E/技术方案与联调/B10-session-share-runtime-delivery.json给逐项范围。当前组合F/candidate-runtime-boundaries-session-share.json；正常3314、main与Root混合gitlink未集成。B10项目/Skills分享ACL及全TaskB仍OPEN，后继回到B01/B02未闭末端与A的当前运行配对，不重复已过分享CRUD。

#### B-11/B-12：正式运行与结算配对（2026-11-02，进行中）

候选复用原同一应用数据库，新增正式Agent/System/Billing各自schema，未新起实例/应用库/角色。按BFF正式pin加载System845cf46b、Billing23ff7199及IAMb9a63c53；独立用途凭据、Agent proof/JWKS、Docker与模型路由已配对。真实管理入口创建合成QA费率/政策及非现金100积分，随后通过正式IAM CAS恢复普通用户，后继App回读platform_admin=false。该费率不是生产供应商报价，不冒真实付费充值。

真实App发送→BFF→Agent→本地Qwen暴露两项确定缺口：LiteLLM尾帧形状原观察器漏usage；合法unsupported-profile/known-totals证据被旧数据库CHECK拒绝，seal回滚后只能保存unknown终态。Agent773cb1e/c1bb1ab分别保守兼容可信尾帧及严格冗余text、修canonical CHECK；不补cache/reasoning零、不丢未知分类、不回填旧attempt。Root保留原失败及一次误载旧PYTHONPATH记录，原4笔未知结算预占共40 QA积分未人工释放/改账。候选单一CHECK已按canonical修复，四份evidence/ACK字节前后完全不变；没有重跑fresh installer或修改正常3314。启动预期CHECK指纹遗漏由安装测试RED复现后精确同步，比较器不放宽。

当前已验：观察器相关157通过；真实PG预算/证据22通过；完整安装/漂移拒绝加预算55通过；Ruff/format、完整Pyright、contract与wheel/sdist通过。完整默认本次3437通过/3时限失败/942未选，首次3416通过/7时限失败后相关10定向通过，不能合成单次全绿。资源门888通过/5失败/34环境错误：包括未配MinIO、明确disposable显示库及admin URL缺口和原native并发/时间断言；原日志保留，未关闭该门。上述3项时限失败的相关7项后继定向通过，仍不合成单次全绿。

Agent b467b5c 已推原Draft46并加载精确源码/独立venv。真实普通账户新Run实际完成：2050输入/5输出/2055总tokens、partial且supported；同attempt按合成QA费率capture3/release7，用户账本-3，余额available57/held40。本人页面显示最终TASK_B_LOCAL_OK，刷新仍在，parts GET200且零业务POST。原首次snapshot404/session_not_found与后继只读恢复200分别保留，不冒一次无竞态全绿。ordered消息content=null沿正式parts读取，不把正文空指针当模型失败。新结果不改变原4笔40积分待核对。

本机E技术方案与联调/B02-B12-current-real-run-pairing.json链接分离证据；全TaskB、B02真实Custom API与E2B末端、正常3314/Root/main组合仍OPEN。下一步单个自有QA Custom API从实际Composer选择到正式Describe/Acquire和Docker执行，不重演已过CRUD。


#### B-02：正式 Custom API Docker、隔离与取消（2026-11-02）

Agentb467候选真实普通UI保存/Composer选择，消息POST202只传profile_id+expected_state_version，正式Describe/Acquire到Docker execute exit0，动作详情刷新后能读真实输入与TASK_B_API_PRESENT；容器终态清理completed且已不存在。第一次配置故障为worker PATH漏/usr/local/bin，Describe成功但模型调用前assembly失败，修候选启动配置而非改业务；原失败保留。后继新配置的另一个Run实际输出TASK_B_ISOLATION_OK，原变量缺失/本次变量存在，workspace不同；小模型转入无关ask_user_question后单次UI取消202，页面Stopped、Agent真终态与清理completed分别确认，未把202直接当完成。

两Run分别3次真实模型调用，按合成费率capture10/release20、capture12/release18；当前available35/held40，原4笔未知预占不改。第一个模型最终答非所问，第二个转等待，两者不冒正常完整回复旅程全绿。本机literal canary在本人Run/dispatch/message/tool journal及native checkpoints、四份运行日志未检出；该单检查不证明任意编码/网络/文件外泄安全。本人API名称CAS从v1到v2后，原会话历史pin v1保留，当前Composer旧pin清空零业务写；取消删除零DELETE，后继显式删两QA配置各200、fresh GET404、列表空，保留别人MCP与Skills。

E技术方案与联调/B02-current-formal-docker-execution.json分开链接原观察器与后继只读/取消事实；首次创建/确认按钮定位错误保留，不以重放未知命令修绿。完整E2B、多配置/跨账号/撤权与全TaskB仍OPEN；正常3314/Root/main未集成。


#### B-01 / B-14：API 文案与图标弹窗回焦（2026-11-02）

App f6b26d77 补Custom API详情与共享图标弹窗中英文，中文原文/命令/密钥只写行为不变；113相关、精确lint与非增量类型通过，主方新增英文2项复跑通过，独审限定通过。实际英文1280/390弹窗文案和无横溢通过，同时稳定观察发现取消回焦落BODY/错误INPUT。1ac805bb最小补原Upload/draft回焦围栏，原取消/Escape先2 RED、原组件24通过，主方4相关通过/20未选，精确lint/非增量类型和两文件冻结独审通过。真实候选1280/390取消均回Upload、零业务写；原标题oracle与last()重绑定错误独立保留，不冒产品故障。

两提交已推原Draft49，候选1557输入绑定1ac805bb（仅Next派生类型引用例外），正常3314/main未切。纯局部片未重跑全仓门，既有全门失败与其余Task B范围保留。E技术方案与联调/B01-api-locale-and-icon-focus-delivery.json给有限范围。后继补普通Provider个人连接名称/说明编辑入口：合同已有，复用原exact GET、CAS与management恢复，不改Provider目录字段、不新owner或wire。


#### B-01：Provider 个人连接编辑与当前文案交付（2026-11-02）

App2b98f632已推原Draft49，复用已有update_connector/CAS和原Editor：普通Provider详情显式编辑个人名称/说明，fresh exact GET后才可保存，失败可见GET重试；不改共享目录字段。相关156、主方11定向、scope ESLint/非增量tsc及冻结独审通过。真实普通IAM用户一次UI PATCH200后原CDP取body观察器失败，未重放写；后继fresh GET确认v2改名/清空说明、目录不变，刷新一致，取消零写/原卡片回焦、390px/Escape通过。初次未等准入401与正确等待后200分别保留。本人fixture disabled/unavailable，只验metadata、不冒可执行能力。

候选追加原mcp_admin专用服务凭据/表面，P/BFF精确源码不改；IAM原生CAS短暂QA角色仅供正规本人Provider准备/清理，个人UI操作前已恢复普通角色。本人两连接已撤销，Provider正规删除fresh404，角色恢复false/v8；没有待恢复权限、不冒管理GUI成功。App e928ecd3补详情管理文案中英，中文逐字保持，命令不变；105相关初门、修正测试查询类型后新用例和Root各1通过，scope lint/非增量tsc及独审通过。候选1557输入绑定e928ecd3，正常3314/main未切、Root混合gitlink未集成。E技术方案与联调/B01-provider-personal-metadata-delivery.md分离实际证据。后继修目录成功后无刷新入口与团队翻页失败无首页恢复入口；B01/TaskB保持OPEN。


#### B-01 / B-09：只读恢复与正式角色权限契约（2026-11-02）

App9f3d9503补团队incompleteRead的原GET-only恢复按钮；35相关、Root2定向、scope lint/非增量tsc和冻结独审通过，已推原Draft49。App4ebcb870补目录成功态刷新，广场/弹窗均复用原GET；无筛选更新shell首页，有筛选保query/category从首页替换，保卡片/禁旧更多/按实际失败cursor重试。87相关、Root7定向、scope lint/非增量tsc及7路径独审通过，已推；候选1557输入绑定4eb，真实只读刷新/390验收进行中。正常3314/main未动。

真实团队读members200/roles502，原生错误bff_bad_response，不能仅当超时或以更宽string绕过。已核IAM正式内置角色含delete_series，BFF内部IAM reader已更新（先前认为它缺失为只读截断误判，已纠正），但BFF Public TeamRole.skill与App旧SDK/runtime闭集未同步。采用owner正规29.2追加该已存在动作、严格有限逆恢复29.1再沿原29/双父proof，原201inventory/历史oracle不改；不另建Team投影。BFF提交固定后App才更新唯一完整snapshot、12原生成入口provenance与正规输出，原schema只增正式action，unknown action仍严格拒绝。Root唯一Git/运行集成，BFF唯一writer task_b_read_review、App后继唯一writer task_b_safe_file_tools；不改数据库、权限授予或新owner。该契约片及真实团队回读未完成前B09不关闭。


#### B-09：真实团队角色502与翻页恢复闭环（2026-11-02）

BFF8ae73fde已推原Draft17（local feat/task-b-owner-closure，remote原head codex/noncash-credit-funding，未另建PR），Public29.2仅补IAM正式delete_series，严格完整inverse承接29.1/29与原双父；201inventory/SQL/旧oracle不变。11契约+11Team读及Root11、正式build/type/lint/format/semantic201通过；原Project regex负控在精确2e基线复现失败保留。候选1142源/1082正式编译已核，新独立源码沿原配置启动ready200。

App59edbe91已推原Draft49，唯一fullsource固定8ae、12原recipe和原share投影正规消费；runtime schema仅增该正式动作，未知仍502。79Team/493完整契约/50架构/13recipe、scope lint/非增量tsc与66路径独审、Root5定向通过。首轮7失败是新test-only helper说明缺原drift分类词，仅修说明，旧负控/hash不动；最终全契约通过。1559候选源精确绑定59ed。

真实普通IAM团队成员/角色/邀请均200，原roles502消失。只读注入真实成员页cursor+匹配400（未造成员行/写owner）后原行保留，显式无cursor首页GET826ms恢复，零业务写，390px无横溢。E技术方案与联调/B09-team-role-and-cursor-runtime-delivery.json汇总范围；不能据此关闭完整B09/TaskB。目录刷新真实8读/1280/390及观察器原失败分离见B01-provider-refresh-delivery.json。正常3314/main/Root混合gitlink未集成；下一步继续B01/B13现有管理入口真实闭环与未闭末端，未重复全仓门。


#### B-03 / B-14：项目技能精确安装、默认选择与可见读取恢复（2026-11-02）

App227a6ac4已推原Draft49，普通初读/搜索/分页失败不再隐藏提示，复用原GET-only reload；保旧卡片禁写、pending原key恢复及准入围栏。3 RED到presentation8通过，相关hook15通过/33未选，Root5通过/3未选，scope lint/非增量tsc0，有限独审通过。三路径冻结含原INDEX说明，候选1559源绑定227a。未重复全仓门，正常3314/main/Root未切。

真实QA项目只创建一次，既有本人Skill安装为独立项目安装，精确source_ref/revision3；一次POST安装200和一次PUT默认200，刷新后原installation_id保持。原生GET为data数组、revision字符串；首观察器错认结构保留，后继只读明确核准。SKILL.md真实文件渲染，实际ZIP266B（SKILL.md215B）下载成功；关闭未保存默认草稿零写，注入一次网络读失败后可见错误，GET重读864ms恢复，390px无横溢，后继零写验证通过。下载为正式POST签发；首观察器把此显式动作计入全局零写的假失败保留，未重放下载。

启动缺口为候选System站点不存在导致manifest404，沿原system-admin启动身份/native site+policy+config+application+feature exposure补齐，未改IAM角色/DB直写/前端绕过；保存true但未expose仍false的原生保护实际保持。入口出现后才能验项目Skill。E技术方案与联调/B03-project-skill-exact-runtime-delivery.json区分配置、命令、只读与原观察器；项目resources503及真正Run加载不冒通过，完整B03/TaskB仍OPEN。

#### B-09 / B-10：真实双账号团队与真实任务分享（2026-11-03）

App a9aa4a59 已推原 Draft49，按 IAM 正式 create/resend 与 cancel 的不同动作分别控制邀请按钮，不改变角色或服务契约。两项 RED 到原 TeamPanel34/权限4 通过，Root2定向、scope lint/非增量类型及停写独审通过；候选1559源精确绑定。普通用户通过实际现有本地SMTP收到邀请与验证邮件，原生注册、邮箱验证、接受邀请及OIDC成功，双方回读相同成员。不是互联网邮箱投递。成员无邀请管理权限；升admin后可读邀请，再降member，同一产品会话立即403，刷新管理按钮消失。取消移除零DELETE，显式移除本人QA成员200后原会话团队读403；重新邀请、重发保持同ID、撤销后接受页404。QA成员/待处理邀请已清理，无临时admin待恢复，验证过的测试账号保留。E/技术方案与联调/B09-two-account-invitation-and-role-runtime-delivery.json含最终清理，不再沿用中途“成员待移除”状态。

实际Agent任务会话分享打开零发布，显式创建200、复制一致、刷新回读原链接，匿名正式snapshot200且无execution_head/私有工具过程/parts。首次peer旧session401被观察器误判为非预期，原记录保留，不重放创建；后继原生重新准入同一主体，私有metadata404，公开链接200。取消撤销零DELETE，显式撤销一次200，fresh metadata为null、原匿名链接404，发布fixture已清理。E/技术方案与联调/B10-owned-real-session-share-runtime-delivery.json分离证据。Skill分享仍缺既有DELETE的Web消费，正沿正式29.2 ACK/原creator边界补确认与未知恢复，不造匿名权限；项目分享/完整跨租户矩阵与全TaskB仍OPEN。

#### B-05：项目默认技能实际 Run，明确加载与模型使用的差别（2026-11-03）

普通UI发送仅project_ref、未传selected_skill_source_refs，BFF message/outbox与Agent request精确冻结同一项目默认source。前两次独立新任务在模型装配前model_unavailable/0模型attempt，源于原生60s健康鲜度；第二次真实probe/CAS后冷页面准备使resolving已65.717s，原失败保留。第三次将真实probe/CAS置于页面准备后，POST202，native durable Ready的source/revision字符串3/完整/.skills/…/SKILL.md一致，真实包已校验加载。

本地小模型实际read_file只传SKILL.md，读取根路径 /SKILL.md 失败（错误原文以证据为准），完整技能路径从未尝试；随后多次无关web_fetch，终态internal_error。不能冒精确路径路由故障，不加不安全fallback，不称模型真实阅读成功。六次attempt均sealed，五次completed/normalized/partial、一条unknown/unresolved，存在financial ACK时间不等于已核最终账。后继只读确认已终态，未发cancel；balance上下文401不改写为成功。E/技术方案与联调/B05-project-default-skill-real-run-delivery.json逐条链接原证据。B05成功正文使用、长期健康上报、最终结算及完整TaskB保持OPEN；先交付已明确的Skill分享撤销consumer，避免重复模型试跑消耗。


#### B-10：Skill 原分享链接撤销消费与真实空 DELETE 修复（2026-11-03）

App14020f88接正式29.2 creator-only DELETE，详情只管理当前主体显式Create ACK，缓存复制前Resolve，取消零写、pending禁重；未知仅GET原ID，不自动复制或重发。主体/资源/窗口退休拒迟到结果，硬刷新须显式分享取得本人ACK，不造listing。70相关、Root11、scope lint/非增量类型和11路径有限独审通过并推原Draft49。真实创建201、精确v3摘要、匿名仍须登录、取消回焦/390宽通过，但首次实际DELETE400保留，原链接未替换。

官方NextRequestAdapter实测将无framing、零字节DELETE包装为非null空流；原GET式body对象检查误拒，并非已证浏览器自动CL0。24c9638a最小四路径仅使revoke走既有download的10秒/abort受限读取：CL缺省或规范0、禁TE，必须真EOF零字节后才向owner转发且不带body/framing，GET仍严拒。27 focused与Root9、scope lint/非增量类型、冻结独审通过，已推原Draft49并精确升级1559候选源。

原share_id先GET200，再由显式管理动作取得同creator/source同ID的active ACK，单次确认DELETE200、严格ACK UI显示停止、fresh GET404、原登录分享页不可用，publicationCleanupRequired=false；没有用新链接替代原链接来冒成功。390宽左右16/374无横溢。E/技术方案与联调/B10-skill-share-owned-revoke-runtime-delivery.json链接原失败和后继同链接验收。当前候选Web60256=24c9638a/BFF60259=8ae73fde，正常3314/main/Root混合gitlink未切。完整B10项目/跨租户矩阵、全仓未闭门与全TaskB仍OPEN；后继继续普通账户设置而非重复分享流程。

#### B-07 / B-11：默认模型目录随登录身份退休（2026-11-03）

App70208355已推原Draft49，原ProjectReadBoundary传入现chat preference；缺正式身份不请求，preview/admitted/subject/generation变即清退旧目录、取消原signal/计时器、退休旧Select portal，迟到响应/旧选项回调不能写。原设备级草稿、localStorage与保存失败重试保持，不新造账户owner。SET25先7FAIL/6PASS，修后13PASS；Root3/164未选、scope lint/完整非增量types、四路径冻结独审通过。候选1559源精确绑定，正常3314/main未切。

实际普通浏览器目录200/一模型，精确selector保存、刷新仍在，390px无横溢，原headless本机偏好已恢复，零服务端业务写。首单次错误注入未观察到预期503/错误提示的harness失败原样保留，不推断产品缺陷；后继有界持续依赖故障实际503及可见错误，显式GET重试真实200/约253.5ms，原abort分别记录。该单样本不是稳定分位或100ms达标；身份退役是组件负控，不冒真实双账号该设置验收。E/技术方案与联调/B07-B11-model-identity-runtime-delivery.json分离证据。下一步只读逐笔核对原4条unknown QA预占，不改账、不重跑模型；完整TaskB active。

#### B-12：原四笔与技能 Run 六笔实际核账（2026-11-03）

有界只读分别核Agent/Billing repeatable-read快照，不冒跨库原子一致：原四笔v2–v5各10仍pending_reconciliation/active hold，cap/release均0，无usage_event/settlement；原evidence与ACK完全不变，无合法后继usage，不能重送旧ACK冒已知或直接释放。后继项目Skill v3唯一Run六个不同call_id（各attempt_ordinal=1，不冒六次重试）前五笔normalized/known_nonzero/partial，owner实际capture3/4/4/4/4共19、release7/6/6/6/6共31；末笔unknown/incomplete_response保留10。身份/证据digest/ACK金额及正式usage/settlement refs逐笔对齐，未补缓存零或重算费率。

当前同一QA账户权威available6/held50，held50=原四40+末笔10，不是又扣50。真实普通浏览器Credits余额6/50、summary/ledger均200，完整ledger13条且next_cursor=null，五个已结算usage_event各精确对应唯一-3/-4/-4/-4/-4 journal；390px无溢、零业务写。首次harness误把fetch Response.status当函数的失败保留，修观察器后仅重读，未改产品代码或重放命令。E/技术方案与联调/B12-current-credit-ui-read-delivery.json链接两份逐笔报告与实际UI证据。所有费率/积分为既有合成QA，不冒支付或生产报价；五条unknown处置/真实政策及全TaskB仍OPEN。后继继续B08个人知识/记忆的真实owner与设置闭环，不重复模型试跑。

#### B-08：个人知识真实CRUD与后继Run材料接线（2026-11-03，实施中）

App702/BFF8ae现资料四字段、个人知识CRUD和usage事实都归BFF本人表；Agent长期记忆另走可信namespace/PgStore，Mori是Music，不能误起服务。真实普通UI自有知识同ID创建201/rev1、更新200/rev2、刷新保持、取消编辑/删除零写、删除204/fresh404，usage前后一致，390无溢、fixture已清理；报告B08-owned-knowledge-crud-runtime-delivery.json。初次只读Add探针误用标签，其false lookup不是按钮disabled，后继实际Add操作已证。当前UI“任务应用待接通”仍真实。

已证缺口：BFF launch/Agent strict RunRequest没有个人材料slot，保存不代表后继Run使用。两owner D0及Root实施裁定在E/技术方案与联调/B08-*-material-context-d0.md和B08-root-material-context-decisions.md。Agent b467原分支由task_b_safe_file_tools唯一writer先发布8.11 optional个人材料/旧omission fence兼容、可信human actor/tenant绑定、实际模型装配、原窗口/计数器预算拒绝与private trace门；BFF task_b_api_postgres等待owner固定提交后再正规SDK消费/原消息事务单SQL快照。Root唯一Git/服务/配置/计划writer，task_b_read_review有限设计独审。无新增知识表/服务、不挪trace/content/Skill/project字段、不静默截断，不放大原1MiB，超界须明确失败/无无限假queued。新Run含regen读新设置，同key/outbox重投原冻结；scheduler等其它admission面后继独立OPEN。原SDK压缩不保证巨型system可压，run_token_budget不是上下文帽，Langfuse原始prompt callback不能忽略。尚未实现/固定或真实新Run验收，不冒完成；QA余额6/冻结50，实施阶段零模型/改账/充值。

App d98abda1已推原Draft49并精确升级候选1559输入，仅7行隐藏知识编辑/删除弹窗遗留的上一笔Saved，列表成功与当前unknown/conflict/error恢复保留；原面板8通过、scope lint/非增量types0、三路径停写独审通过，未加镜像测试或为显示改动再重演CRUD。B08-knowledge-dialog-feedback-delivery.json给范围。Agent8.11仍独立实施，BFF未提前消费。D0独审P2自动LangSmith/Debug内容回调旁路已通知writer；真实actor.opaque_ref可绑定个人owner。BFF首次413本已有not_admitted→failed/RUN_ERROR，先unknown的sticky恢复安全围栏保留。完整HTTP body即payload.launch，身份走header，可在原queued前按正式SDK实际序列化字节和owner1MiB metadata拒界，拟正规personal_context_too_large/413；App原pending保body/key、不自动发送，不能冒已恢复editable draft。

Agent B08 30ce29a6、BFF 1e6765b3与App 38d2f6cd已提交推送原Draft46/17/49，候选Agent60261/worker、BFF60259、Web60256按精确已提交源升级并健康；正常3314/Root/main未切。Agent v2离线wheel+sdist重建成功，231生产模块及530源输入字节核一致。BFF v2独审APPROVE，63相关/37架构/201语义、18SDK生成与lint/build/types通过；Root同实例独占临时PG库真实B08两旅程及failure CHECK evolution一旅程通过，fixture库已删除；候选原库正式check→apply→check=current，1145源/1084编译产物核一致。App 77路径独审APPROVE，13原生成链、190受影响契约、67 UI/原请求恢复、50架构及scope lint/非增量types通过；1560候选源输入核一致，A发送状态未改。真实普通UI创建一条知识/开启→新消息202→正确本人材料被冻结→Agent context_window_exceeded→普通原会话刷新200正确显示超限、零自动重发；原瞬时排队观察不冒持久界面故障。网关local-qwen显式num_ctx4096，System对应context4096/maxout512，完整提示超限在模型计费准入前拒绝；该Run原生Billing admission=0，不能称知识已参与模型回答或on/off成功。20非现金QA测试积分经正式BFF发放，native IAM临时管理员8→9→10立即撤回；当前26available/50held，原unknown50未改，测试知识已删、usage恢复false/rev2。首次全表facts隔离不足、Agent probe漏Bearer及只读定位器歧义等原失败保留，未重放业务写。B08-real-material-run-read-audit.json、B08-app-final-independent-review.md等在E/技术方案与联调。模型容量适配、成功on/off、动态/scheduler及全TaskB仍OPEN，知识待接提示未提前移除。


#### B-08 / B-11：模型窗口与首发偏好更正（2026-11-03）

共享 LiteLLM local-qwen 配置实际 num_ctx4096，候选 System 曾误登记为16384；独立直接Ollama 16K/no-thinking模型另建，未改变共享网关。此前完整工具请求 UNKNOWN 不足以证明模型不会使用知识。Agent 最终边界重复注入 b636879e 缺乏依据，已用849f668撤回并推原Draft46，39项相关测试通过；Root旧gitlink尚待正规组合验证，不冒已同步或已合main。Root Draft67已改正模型能力与Admin“仓库不存在”的过度结论；当前访问Repository not found只能证明现身份不可读。

v24真实Run在装配阶段 model_unavailable，原生模型attempt=0，requested_model_label=null；原fixture已清理。定位到Web首次异步准入后丢失已有模型偏好，新增真实engine首发回归先红，最小3行修复后84相关通过，定向lint/完整非增量tsc通过。仅测试选项undefined与strict类型冲突已修，不改运行contract。Web60256此时是38d2f6cd加该单文件未提交overlay，哈希已登记；v25首条真实UI发送已包含独立16K raw label，模型最终回答与on/off仍待确认。未重演全部工程门，正常3314/main不切，不称完整B08/B11完成。

候选Billing曾经合成QA充值单位误用造成超额余额，不能沿用前文26available/50held等旧快照；不得为“修绿”直改账本或处理原未知冻结。当前独立16K费率与50积分单attempt上限仅为合成QA测试政策，非生产报价/支付。后继须逐笔以当前正式账本核对。


v25后继终态：首条请求已正确带独立16K label，Agent同值冻结，原生一次模型attempt为observed，usage execution_outcome=completed / normalized / known_nonzero / partial，financial ACK已回。Run后续internal_error，不是上游零attempt或知识成功回答；开启/关闭对照仍未通过，关闭腿未发送。页面观察169.635秒不冒模型纯耗时。自有知识删除/usage恢复均确认，cleanupRequired=false，无待恢复权限；未重放原message。BFF余额从19999985000000降至19999973000000 micros，原70积分冻结保持；12积分为合成QA消费，既存超额发放未直改。后继定位当前已完成模型调用后的Run收口异常，避免继续盲换模型或重复充值。

v25 typed checkpoint确认MODEL_BUDGET_UNAVAILABLE；Agent局部修复将3个固定财务unavailable映射dependency_unavailable/false，已确认pending ACK仍独立，不新增重放。client默认5→10秒仍单发送/有界取消。4项先红后绿，4相关文件184通过/4原marker未选，Ruff及显式Python3.12 Pyright通过；App首发偏好84相关通过。8个源/测试路径停写限定独审APPROVE，无确定P0–P2，完整owner门未重演。

候选单文件App overlay及两个Agent生产文件overlay均记精确SHA，不能冒称已提交组合。v26真实首发仍正确direct16K，唯一模型attempt observed且usage completed/normalized/known_nonzero/partial；Run失败原因为MODEL_SETTLEMENT_UNAVAILABLE，财务ACK稍后恢复。BFF当前无显式timeout配置，实际默认5秒，不是此前误认为的实际10秒；延长Agent期限未解决该末端，未发送关闭腿或重复模型。cleanupRequired=false，自有知识删除/usage恢复；保留原失败receipt，下一步沿该结算原identity与owner链定位，并推进独立功能，不再盲发v27。完整B08/TaskB保持OPEN。

两片已分别提交推送原分支：App f078d98d、Agent cfd1fccc（包含849f668撤回），工作区干净。正常3314未切；候选运行仍按上述overlay取证，不能把提交动作冒成全候选源码一致性验证。仅用v26已经ACK的原event/原幂等key，通过正式BFF重读同一结算回执212.4ms、captured，Agent原sealed evidence/ACK逐字未变；没有新reserve/provider/model，不把该单次无模型负载样本冒p50/p95或首结算性能修复。

System原LiteLLM标签经fresh版本7与已发布4K revision核对后，正式CAS PUT200恢复实际context4096的旧精确revision；版本8，原visible/default/priority保留，独立direct16K与共享网关未变。旧错误16K快照及合成QA费率历史不改写，后继不能继续使用错误窗口宣称成功。实际Admin权限、13条兼容边、全owner门及完整TaskB仍未闭，不合main。

#### B-14：设置竖栏方向键与窄屏布局配对（2026-11-03）

真实桌面column但aria-orientation固定horizontal，↓不切换，新E2E先红。原rail ResizeObserver/reveal回报实际CSS方向给同一Tabs root；不加断点、第二套导航或手写方向键。桌面↓/↑、390px→/←、回桌面焦点与选择E2E6.1秒通过，原更多菜单/深页可见项/缩放/侧栏回焦旅程11.6秒通过。候选三生产文件按HEAD字节核对后覆盖，仍为登记SHA的开发overlay，不冒整体源码精确组合；正常3314未切。

最终原设置组件167通过69.76秒，定向ESLint/完整非增量tsc通过，六路径停写只读审查APPROVE，无确定P0–P2。首跑165过/2失败及隔离复跑1过/1失败是旧模型测试在目录ready前点击disabled；仅等待enabled后全文件通过，未放宽断言/时限。浏览器旧auth观察失败、嵌套tablist观察器及私有setup重复Playwright安装原失败保留；原生/login刷新、定位实际nav、同一安装后验证通过，未改认证代码。完整owner门/视觉同态对照与全TaskB仍OPEN，后继继续账户头像与正式owner支持边界核实，不再发送模型任务来刷成功。
#### B-07：原 IAM 头像信息的账户页消费（2026-11-03）

App2286cce8 已推原功能分支，沿 IAM 已有 `profile`/`picture` 及原同源资料读补可选 HTTPS 头像；无新 owner、上传、图片代理或持久化。保持原 subject/代际退休，匿名/no-referrer，坏 URL 或图片失败回落首字母，不损姓名资料。定向回归先红2/75，修复后三文件100项通过，scope lint/完整非增量tsc通过，九路径有限独审APPROVE。后台浏览器原生资料200（本人QA无图片）和明确fixture图片加载/失败、390px无横溢分别记录，零账户写入；不冒真实用户图片或上传验收。E/技术方案与联调/B07-account-picture-delivery.json 绑定原始测试、独审和四文件候选overlay。正常3314/main不切，完整B07及TaskB、既存B08结算末端和组合门禁继续OPEN；已通过不变验证不重复。


#### B-15：日常3314切换当前App与保数据BFF/System（2026-11-03）

日常3314已从旧归档切至App2286cce8当前checkout开发源，保原正常IAM登录、用户/租户、BFF数据库、Redis与上游地址；不是切换到隔离QA环境。后台Playwright通过正常原生准入后，完成本人测试账户姓名保存→权威回读→刷新保持→未保存离开不写→原名恢复的真实旅程，两次PATCH200，cleanupRequired=false。17个设置入口面板可见，390px无横溢；只证明导航/布局，不称所有页面服务可用。导航暖缓存5样本的p50/p95约120–170/172–201ms，包含自动化观察，不是冷启动、数据就绪或100ms目标通过。

正式BFF5cb4a293完成独立正常快照恢复演练，8个原生演进check/必要apply/check均成功；随后原旧BFF优雅drain、最后一致备份、原同一kokoro_bff schema执行已验演进。32→34表，全部32张原表旧列逐表行数/排序行值摘要升级前后相同。原Project/偏好/知识/RSS/幂等与5条scheduled outbox均纳入保护，未换库/钥匙或删旧行。旧runtime与两份备份保留，自有演练临时库已精确识别、无连接后清理。新55838健康/就绪均200，Agent保持false。

按BFF正式System6.1 pin使用845cf46b，不误用物理1460820 HEAD；全新正常System以同一正常BFF数据库的独立kokoro_system schema、独立Redis namespace启动。正式空owner installer23表，原BFF列catalog摘要前后相同；BFF服务token沿原正常值配对，不复制QA数据/模型/价格或更换IAM身份。正式System API以本地部署operator创建kokoro产品、127.0.0.1站点、active状态及中英manifest policy，未变浏览器账户权限。

当前日常同源实读：账户资料、项目、project-pins、模型目录、zh-CN/en-US runtime-manifest均200，hub业务写0。模型目录接通不等于已配置真实可执行模型；无新模型/预占/充值。MCP connections与skill-installations仍明确503 dependency_unavailable，须保原Platform密钥/数据升级和补正规purpose凭据/Storage；不能放宽decoder或用候选库伪装成功。正常Platform仍旧fa5，Root/main未合，Admin与历史契约组合缺口、B08结算末端及全TaskB仍OPEN。原生浏览器凭据/备份/进程只留ignored；有限证据汇总B15-normal-preserving-runtime-delivery.json。

#### B-15：日常IAM/Platform保数据升级与真实API配置闭环（2026-11-03）

正常IAM49689升级正式b9a63c53/API0.18；原生具名演进前完成一致快照副本演练、停旧服务最后备份，原17表旧列逐表数量及有序数据摘要不变、目标19表。正常Platform61931升级正式2ad5c9e7；SQL dump/restore首演练catalog不等保留为失败；改用旧owner canonical安装与原data-only快照恢复后精确74d5父、原生apply至718d，原25表旧列数据不变。三份自有演练库按归属/无连接核实清理，正常备份保留；未改父hash或执行任意修复DDL。

Platform与IAM直接执行身份正规文件配对，BFF catalog/projection分别限定purpose；Storage63372保持4ab2原对象桶/数据库/Redis，仅追加正常Platform身份后原生重启。MCP原密钥材料逐字保持，两个旧硬链接密钥文件复制为独立0600文件以满足当前原生读取约束，未轮换密钥。正常六服务ready200，账户/项目/pins/MCP连接/Skills安装/models/中英manifest同源全200，取代上一里程碑MCP/Skills503状态；模型目录为空和Agent禁用均未掩盖。

后台Playwright在正常原生账户完成独立Custom API创建201→权威回读200→编辑200→刷新保持→未保存取消零PATCH→删除200→同ID回读404，响应不含写入密钥，自有配置cleanupRequired=false。E/技术方案与联调/B15-normal-capability-account-pairing-delivery.json绑定原始回执SHA。不是原生Computer Use或外部服务真实执行证据。其余MCP三种配置/Skills导入正在接续，Storage4a990 approved父catalog与正常实际不匹配，Prisma diff0不能代替原生指纹，尚未升级。正常历史多库未收敛同库，完整B01/B02/B03及全Task B/组合门/main仍OPEN。

#### B-01：正常四种创建入口配置保存与清理（2026-11-03）

正常3314完成Custom API创建/编辑/刷新/取消/删除（上节）；自定义MCP创建201→同ID详情200→编辑200→刷新保持→删除200/404。JSON导入与URL添加首次命令已保存，Playwright直接读取响应正文失败，原失败记录保留；各按正式connectors列表中唯一本人测试名找回同server/connector ID，真实页面打开详情、同ID删除200并回读404，未再次POST或用新配置替代原请求。全部自有配置已清理。E/技术方案与联调/B01-normal-four-creation-configuration-delivery.json逐份绑定原始失败、权威回读及恢复证据。

本片仅配置保存与管理，不触发Prepare/Connect/Enable或外部服务，不冒称四种创建的真实连接/OAuth完成；stdio、图标/存储精确升级、Provider各末端与全B01继续OPEN。原生登录可重新完成并准入，独立脚本的初始语言/会话观察问题不直接归因为产品缺陷。技能原生上传/安装真实旅程接续中，不机械重跑已通过且输入未变的测试。

正常技能上传首条导入begin201，但UI未知、权威GET仍upload_pending。已确认日常Web旧启动环境缺少既有KOKORO_WEB_LOCAL_UPLOAD_ORIGIN；正常Web保同App/认证/数据补精确loopback Storage origin后原生重启。原桶versioning Enabled；GetBucketCors404、尝试最小本地PUT/版本ACK策略被provider NotImplemented501拒绝，未成功修改桶CORS、未改对象数据。CSP漏配已确认，CORS是否另阻实际上传仍以新输入的真实请求为准，不能仅凭预检下结论。首条pending测试意图及其24小时期限保留，不伪报安装或清理完成；修正启动配置后的新独立包旅程接续并私密保存原body/key。

#### B-03：正常技能原生包导入、刷新与清理通过（2026-11-03）

正常Web补既有精确本地上传origin后，新独立QA包从原生UI选择ZIP→begin201→真实对象PUT/版本ACK→complete200→finalize200→安装后刷新仍见，随后本人技能源DELETE200、本人账号安装DELETE200，正式同ID回读installed=false且刷新卡片消失。E/技术方案与联调/B03-normal-owned-skill-import-delivery.json绑定原失败/配置切换/新真实旅程与两类清理；不把删除源当移除账号安装。桶CORS API501未改配置，后继实际成功证明它不是当前本地旅程阻塞，首次CORS诊断不冒最终根因。App未生产改码，next-env启动派生单行已精确恢复。

成功新包的来源/安装清理完成；首条旧CSP输入产生的upload_pending意图仍保留24小时到期和cleanupRequired=true，不假冒同一意图恢复，也不通过DB清理或新上传覆盖原失败。完整版本/权限/项目/Agent使用与B03/B04及全目标继续OPEN。

#### B-03：正常技能启停、文件树与精确下载闭环（2026-11-03）

正常3314同App2286cce8、原生账户与正常服务组合，以新的本人双文件包完成真实UI导入安装，停用与启用各原生命令200，分别刷新保持；详情读取SKILL.md及references/check.md正文，下载当前安装包200，下载ZIP与上传ZIP的SHA256逐字一致。随后来源删除200、账号安装移除200，同ID权威回读installed=false，刷新卡片消失，本次包cleanupRequired=false。E/技术方案与联调/B03-normal-skill-lifecycle-delivery.json绑定原始两份回执；首份验收器将文件显示名当完整accessible name导致超时，保留原失败，仅修验收器并恢复同一安装，不重新上传或修改产品源码。

本片证明正常账号安装的启停、读取及精确包下载，不冒充项目选择、真正Run加载、版本更新、跨主体权限或管理后台完成。原先CSP失败的独立旧导入意图仍单独待到期。Storage父catalog调查不阻塞本片：同PG按4ab2官方空库installer建立的本人隔离库，与正常库原生读取的388条catalog定义完全一致；两者仍不等于脚本批准的父指纹，未放宽批准值或升级正常库，隔离库已按归属清理。全Task B继续OPEN。

#### B-03/B-14：正常项目精确技能与读取失败反馈（2026-11-03）

正常 System 通过已有 API 为原站点/产品配置 project.skills 暴露；普通 manifest 实读与项目入口已确认，不改浏览器角色或绕过准入。本人同一 QA 包先账号安装，再创建项目的独立安装，默认选择经权威回读/刷新保持；精确正文预览、下载原 ZIP SHA256 一致。随后清默认、移除项目安装、项目删除202并原生读回逻辑 released、移除本人来源和账号安装均通过。本次 cleanupRequired=false 仅指原生逻辑清理，不声称物理存储对象删除；原先独立 CSP pending 意图不在本次清理内。

真实首次 package 429 及另一次诊断503暴露了空白 reader。App7bac5ae6 已推原功能分支：无已确认正文时显示现有错误提示，仅绑定有效时显式 GET 重试；权限退休不恢复旧内容，不重放写命令。完整详情88项、定向lint/完整非增量types/diff通过，限定独审无确定P0–P2；缺失的指定审查技能未调用，按局部迭代未重跑完整 owner 门，不声明可合并。最终正常预览下载成功未再命中失败，不能作为正常错误重试证据；底层429/503仍未定因。原验收器失败均保留，恢复同一项目/安装而非新建覆盖。证据 E/技术方案与联调/B03-normal-project-skill-and-reader-delivery.json 绑定实际回执、源码及日志SHA。未执行Run；版本/权限/Admin、真实外部连接与全Task B/组合门/main继续OPEN。

本次 Root 仅更新已推送并正常加载的 App7bac5ae6 精确 gitlink；拓扑检查仍退出1，错误仅为原 kokoro-admin 未独立初始化、origin/HEAD不符三项，未冒称完整组合通过或合 main。

#### B-01/B-05：正常 HTTPS MCP 准备、刷新与草稿交接（2026-11-03）

正常3314原生创建本人 DeepWiki HTTPS 配置201，Prepare200，权威GET为ready/available、有独立Connection和实际三个selector（ask_wiki_question/read_wiki_contents/read_wiki_structure）。刷新后首次“试用一下”禁用并非连接保存失败：正常System尚无mcp导航，App按现规则不给Composer连接器回调。通过既有System API向原站点/产品/应用增加workspace.connectors暴露及mcp导航配置，保原project.skills及账户角色；没有前端绕过或运行代码改动。恢复同一配置后刷新按钮可用，显式试用进入新草稿、正文含该连接器名、选择器同名项checked；执行写请求0。随后原生删除200、同ID404，cleanupRequired=false。官方端点依据 https://docs.devin.ai/work-with-devin/deepwiki-mcp ，实际selector以回执为准。

先前本地HTTP本人fixture的初始化/三类目录发现、Prepare200和connection回读也真实成功，但现安全投影严格HTTPS，保持unavailable且不出现可执行试用；不为验收放宽协议。首条浏览器create响应正文读取失败保留，经本人唯一名称及原server/connector权威回读恢复，没有第二次创建；该HTTP配置已删除并404，自有fixture已关闭。E/技术方案与联调/B01-normal-https-prepare-and-draft-delivery.json逐份绑定原失败/配置与成功回执。此片只关闭声明的HTTPS准备/刷新/草稿交接，不当成真实Run工具调用、OAuth矩阵、结算、完整视觉/性能或全Task B完成；其他末端继续OPEN。

#### B-04：正常个人版本完整生命周期与历史读取修复（2026-11-03）

正常3314本人样本完成v1导入安装→v2新包上传/扫描/校验/发布→取消升级零写→同一安装显式更新v2及刷新/精确正文/原ZIP摘要一致。发布不隐式升级安装。随后取消撤回零写、显式撤回v2、历史v1精确正文读取；取消恢复零写，原v1 ZIP经既有链发布成新UID/v3，原安装保持v2。显式更新同一安装到v3后，刷新正文与ZIP均与原v1一致；原生系列删除、安装移除及权威installed=false通过，测试样本cleanupRequired=false，不声称物理对象删除。首份验收器对重复关闭按钮和更新按钮完整无障碍名称误定位保留；后续恢复同一系列/安装，未重发成功发布或升级。

App a857542a64b6d878e5aeab92b081194a1ff478e9修复历史关闭/重新准入/同主体generation换代时旧列表、正文、分页/恢复入口复现，迟到结果退休；原未知Restore意图及原body/key/CAS保留。可见版本号与真实完整日期已在正常桌面/390核对，窄窗374宽、scrollWidth=clientWidth=372；截图正文仍加载，未冒已加载正文视觉对照。新增回归先3FAIL，最终history+restore16PASS，Root同范围独立复验16PASS，scoped ESLint/完整非增量tsc/diff0；停写四文件限定独审无确定P0–P2，缺失hix-code-review未冒调用。E/技术方案与联调/B04-normal-version-lifecycle-and-history-read-delivery.json绑定七份原始回执与四源码SHA。无接口/Schema/依赖/模型变化，未重复无关全owner门，不声明完整需求可合并；Root只配对已推精确App版本。跨主体/租户、Admin、真实Run加载、其余B项及全组合/main继续OPEN。

本次新App gitlink的Root拓扑复验仍仅原Admin未独立初始化、origin不匹配及HEAD/gitlink不符三项，退出1；不据局部功能修复合main。

#### B-04 / B-06 / B-09：正常私有技能作者与同团队成员权限（2026-11-03）

正常3314通过团队页邀请、现有本地SMTP邮箱验证、原生注册/登录和接受邀请建立本人QA普通成员，双方回读同一member身份。作者独立私有技能导入安装后，另一账号的managed详情、历史、包及作者安装读取均404；创建新版、撤回、删除系列及安装owner-only来源均403，作者原active状态与state_version不变。分享仍遵循现owner规则，不扩大publication audience：匿名401；成员Resolve、summary、下载及撤销均404，页面显示不可用，作者原链接仍有效。作者显式撤销200后fresh GET404。以上13个负控未暴露本人QA正文标记，不冒跨租户或管理员矩阵。

作者原生撤回200后安装保留且source_status=withdrawn；本人managed下载资格与字节200，SHA256与原ZIP一致，成员同路径404。随后本人系列删除、安装移除、权威installed=false/managed404通过；测试成员通过正常团队页移除200，原Product会话立即403，原邀请不再pending。保留已注册测试账号，未授予admin或修改用户账号权限、模型、账本。最初QA ZIP错误地多包一层目录，被原生IMPORT_PACKAGE_INVALID拒绝；原rejected意图保留至2026-11-04T10:19:14.743Z，不称物理清除。已知拒绝后换用根目录SKILL.md的新包，原输入与回执均保留；分享响应正文观测失败及清理脚本语言定位失败分别保存，未伪称产品故障或丢弃原写事实。

本片无生产代码/契约/Schema变动。独立只读审计未发现确定新越权问题；现有权限与主体退休定向回归20通过、96因名称筛选跳过，不作为完整测试通过。正常真实证据E/技术方案与联调/B04-normal-private-permission-runtime-delivery.json绑定10份原始回执SHA、明确API/页面范围与清理边界；hix-code-review仍缺失，未声称调用。App保持a857542a，完整作者/管理员/跨租户、真实Run及其余Task B与组合合并门继续OPEN。

#### B-07：设置草稿隔离与日期语言（2026-11-03）

App27b17f12c325022cfd0f9b77eab53fccf6f5598d已推原Draft49。个性化旧回调此前可取到新准入会话并修改/保存新草稿或读取新冲突；增加发起scope核对，换主体/准入代后的旧update/persist/retry/chooseServer/saveDraft均退休，原CAS及未知结果显式恢复保持。新回归4FAIL/2PASS后修复；数据管理三类日期原来无视产品语言，沿现locale格式化，原ISO时间和列表读取不变，新回归1FAIL/5PASS后修复。

停写五路径独审无确定P0–P2，主方四套67PASS、定向ESLint/完整非增量tsc/diff通过。正常3314当前源码的日期展示以明确只读列表fixture验证中文/英文及390px无横溢；不冒原生分享/归档CRUD或Manus对照。第二轮逐路径记录仅原生POST /api/auth/session，业务写零；第一轮计数未分类而失败的原回执保留。正常个性化当前null，双标签CAS验收器在首写前退出，零PUT/零数据修改，未将其算通过。

E/技术方案与联调/B07-settings-identity-locale-delivery.json绑定源码、命令、原始回执和范围；同目录自包含HTML提供真实显示截图。无契约/Schema/依赖变动，不重演无关完整owner门。hix-code-review不可用，未声称调用；完整B07/Task B及组合合并仍OPEN。

#### B-01：正常存储图标升级与页面实测（2026-11-03）

官方4ab2f23干净父库原生bootstrap真实RED：完整目录为1d60而原脚本只接受历史bdf6。正常库与同源码官方新建库388项定义完全一致，不归因于正常结构漂移。Storage add2da6ca379be686127da31d64e38843fc10a70保留历史bdf6→94839，新增固定父新建→原三条enum ALTER→独立新版新建全部定义一致的1d60→0f480精确配对；未知、部分目录及双向错误目标仍拒绝，canonical/fingerprint/事务/安装锁/取消围栏不变。独立只读审无确定P0–P2；正常执行脚本的未知COMMIT记录问题已修为调用前unknown、成功后committed，不把丢ACK写成零修改。

定向真实PG三项及单元五项通过，四项名称过滤；完整类型、相关lint、四路径格式和diff通过。完整bootstrap首轮7FAIL涉及fixture连接与CREATE/DROP超时，首因未归因、原日志保留，未重跑无关全仓或冒完整owner门。当前只读库存仍见4个storage_schema前缀库，未证明全部归本次失败，保留待核，不盲删；本次新建fresh资格两库和真实备份恢复演练库均有亲建清理回执。hix-code-review仍不可用，未冒调用。

正常Storage owner先全量私有pg_dump并恢复到独立库，原数据SHA一致，正式expand前后九表全量数据及xmin摘要一致，重放already-current；再对正常库重新备份、亲建旧服务优雅退出、正式expand与相同数据/xmin核对通过。正常63372已从冻结add2da6源码启动ready，原数据库/对象bucket/扫描器/credential配置保留。此为Storage运行源更新，不冒完整Root所有gitlink与运行源一致。

正常3314本人QA完成从设备上传PNG→扫描/可用预览→保存MCP配置→刷新卡片自然图片加载→详情及390宽度无横溢。单次上传到预览8561ms、整段25167ms，不称p50/p95或100ms达标；Playwright headless自动化不是Computer Use，也不是Manus视觉对照。随后同一新建配置原生删除200、fresh列表无该server；原生对象生命周期清理不等于物理字节删除。只保存配置，未连接示例端点，不冒真实MCP调用/OAuth完成。E/技术方案与联调/B01-normal-icons-storage-delivery.json及自包含HTML绑定真实回执、截图和精确source。Storage功能分支已推；组合及完整Task B仍OPEN。

### 2026-11-03 B-03 / B-06：两类恢复功能交付

正常B06真实双标签复现退出后原页丢为/app。App5b7d0fd6保tab-local白名单导航hint，原GET-only确认和签RP流程不改，失败页不提前固定跳首页；正常退出→issuer确认→另一标签私有内容退休/资料401→显式重登完整path/query/hash恢复/资料200→另一标签再准入通过。存储不可用失败恢复回退/app，自然过期/多设备仍OPEN。

Appd6dd3cd0修设置与独立技能广场的可见错误/明确重试，保原查询/分类/cursor/身份退休与安装写命令。正常两入口浏览器注入目录503→可见Alert→同body真实owner200通过，390px及设置提示框父内边界通过；原误判共用组件导致首轮广场漏修的RED保留，现两个入口均验。原CSS仅width:auto防w-full加margin裁切。Auth75、设置选中8（18未选）、广场原文件12项通过，scope lint/最终全tsc通过，停写限定独审无确定P0–P2；非完整owner门，缺hix-code-review未冒调用。

App两提交已推原Draft49并核精确remote head；Root仅更新App gitlink与本计划。正常3314加载本App源码，其他owner组合/原Admin拓扑/全门仍未完整配对，不冒main或完整Task B。故障为明确浏览器fixture、非自然owner事故；单样本恢复设置1855ms/广场2036ms及退休约5秒，不冒分位或100ms。E/技术方案与联调/B03-B06-settings-recovery-delivery.json绑定原始范围；完整目标继续active。


### 2026-11-12 Task B App候选与真实配置首片

- App原#49已并入accepted main，候选a0512901保双方历史和现Public28.35；完整lint／非增量TS／build／22正规生成检查通过，rail最终295 PASS。完整默认6753 PASS/2 FAIL后，仅修旧calendar与可见错误两处oracle，原两文件48 PASS；未重跑全默认，不拼接成全绿。
- Root ae480fb9固定App候选并从真实已提交blobs重算inventory，拓扑／15 edges 0 violations／原checkpoint通过。正常3310受控切换；隔离依赖复用曾误改正常workspace链接造成Build Error，已恢复并改独立offline frozen安装，正常浏览器确认恢复；持久数据未改。
- 主控native真实API创建201→fresh exact详情→刷新保持；JSON双导入201→明确选择B→fresh Connector/Server200→取消未保存编辑→刷新原值通过。只保存配置，未连接/Prepare/执行或声称供应商成功，秘密未回显。3项唯一命名测试配置待删除确认，原Context7未改；原始脱敏metadata／截图／receipt保本地ignored。
- 本片真实观察：bootstrap空models被误投影ready-empty，MCP English详情/配置/JSON编辑有硬编码中文与局部缺译。composer_ui_audit仅在隔离App最小修正，复用现字典/测试，不动auth、机器契约/正常源；主控停写后验收。BFF原#17收敛和Agent精确消费者四字段配对并行，Goal保持active。


### 2026-11-12 B-T1a正式消费者配对与受控恢复

Agent281bde49（PR #48）仅4行顶层Platform pin／常量／断言配对Capability573a8f00（原#12），四Proto、generated、独立历史发行锚不变。主控正常3.14.3复验四contract文件129 PASS／contract-check，四SHA与隔离archive fixture核等；正规generator／Ruff／Pyright／wheel安装smoke通过，初次3.11 TypedDict收集失败保留。managed worktree工具两次未返回且未生成目录，独立验证用ignored源码archive，不掩称managed工作树成功。

52 Run均终态、Agent dispatch与BFF相关pending0后，主控SIGTERM原HTTP／Worker／Platform，应用已验补丁并恢复正式入口；两owner health／ready200、Worker消费，原持久数据和两笔未知财务恢复记录保持。staged Root精确gitlink与按76真实Git blobs重算93引用的inventory已通过拓扑／15边0违例／原checkpoint。首轮未stage导致gitlink不一致失败保留，随后补齐真实gitlink通过；未弱化规则。源码／本地候选组合通过不冒PR已合、供应商授权或整个Task B完成。App局部多语言片16路径停写／独审CLEAR，主控验收中；BFF认证metadata按owner发行单独推进。


### 2026-11-12 B-01明确重新授权最小续做裁决

复用原#17 e3b5fb7已批准边界与Capability573a8f00正式ReauthorizePersonalMcpServer，无新owner／Schema／认证。BFF现MCP native管理入口显式POST承接source_connector_id及server/connector双CAS、冻结原key/body/digest；Capability唯一生成全新pending/disabled身份，旧身份永久无效，不自动Prepare/OAuth或补连接资格。历史ACK允许按原命令重放，不在重放前插current GET；ACK后由App fresh exact读新Server/Connector决定当前投影，失败仅重读，身份／窗口退休与迟到结果不handoff。

BFF独立MCP writer api_perf_audit仅承接旧具体hunks，并用当前owner精确commit/provenance正规生成；四Proto／67 artifacts已核与旧候选相同，当前新增serviceCredentialSources使provenance摘要必须按当前真实字节配对，独立publication旧pin保留。Public Chat／Share、Schema、package-lock及共有文档仍由Chat writer／主控持有。MCP private code-first artifact与App正式固定消费者顺序交付，不制造第二SDK或公开传输协议。正常资源不动；两writer停写后由主控统一build／contract与真实最小边界验收再入原BFF#17／App#49。


### 2026-11-12 Native UI／清理与已验Agent PR出口

App8208882d四文件443 PASS／build、后继34c51204七字典十默认key与原测试117 PASS／build／独审／输入核等；真实English详情/JSON安全错误/取消回焦/390px与最终French320默认表单内收通过（288px容器与scrollWidth相等）。实际French先复现回退与English占位才修，不把key存在当正确翻译。未全站／全部locale视觉QA；最终观察网络缓冲eviction保留，不把留存零mutations冒完整零写证据。

用户明确批准后，仅删除本轮API与JSON A/B三唯一配置，三DELETE200，硬刷新仅余原Context7，未改它；恢复en与视口，原收据／截图留ignored。Agent#48正常merge mainb7867212，树核等281bde49，topic本地远程均清；4个CI红annotation明确账户账单/额度未启动，未绕保护。Root db28020c精确配对Agent main／App34c51204／Capability573a8f00，131真实blobs／150引用重算，拓扑／15边0违例／原checkpoint通过。

BFF3007c16仅本地metadata已验未push，后继Share GET19路径停写待真实PG、MCP独立writer进行；原PR17最终保历史集成后统一发行消费者。Skills只读核验已证多数原功能和真实旅程在现源码祖先，剩余现三入口一致性、后台/管理员撤权与跨tenant边界，复用真实Skill运行，不把旧待领取或旧候选独有提交机械扩成新Task B范围。Goal active，主控继续收口独立已验片而非只汇报。


### 2026-11-12 BFF联合实测与原PR历史收口

主控0a2c98ae联合候选337相关PASS／0SKIP、build/types/lint／216semantic／两正规check与114输入核等；独立Share/MCP/Team/退役补口审查CLEAR。真实ChatModule/Nest＋独立PG7 PASS（IAM准入double、无Redis），含Project owner单独变化404／恢复200、GET事实和receipt值/xmin不变。首次URL漏schema、次轮deleted seed漏deleted_at失败均保留，只改接线/fixture，所有3个自有库DROP。未跑全默认／新模型／真实Provider，不以数量冒Task B完成。

原BFF#17普通merge旧1e6765b3到已验0a2，82冲突及自动混入260路径由两只读owner分组审查、主控具名路径逐组处理；保当前完整Schema/Execution/verified spool/native credit与已移植Share/MCP/enum，删除旧层/重复186行MCP测试/未发行29.3及旧vendor/CLI/RSS旁路，B08意图另保留。最终609b0e93有双方历史且完整源树等已验0a2，快进推送原#17，无force/no新BFF PR，仍Draft。App composer_ui_audit正从固定0a2正规消费两profile；正常服务未抢切。Storage原#2由api_perf_audit独立非runtime工具片推进，base maina8edebf8树等231bb663，fresh→FINAL资格不得凭猜hash或改成功断言收口。Goal active、唯一TODO持续推进。


### 2026-11-12 App消费交付与Storage实证纠偏

App原#49已提交推送ebc36617：固定BFF0a2两profile，主控23生成检查、60文件1216 PASS／build；独审发现3真实缺口（tenant暂缺下原未知命令保留、provider_key与server身份一致、Shared SDK path.id生成）修后主控185 PASS／types／SDK check／build，110路径冻结核等，两独审CLEAR。未重跑完整默认或模型、不拼全门绿色；正常源仍34c51204／BFF05a1074，下一步受控配对只补native缺口。

Storage旧fresh1d60→0f480说法经当前真实PG完整目录推导未复现：0f91535 fresh实际94839，精确删除3 enum定义为legacy bdf6；既有FINAL DDL到809d并与独立993aede定义全等，既有workspace DDL到13a347并与独立当前f8145定义全等。四owner search_path均一致，public反解仅schema前缀差异；无旧0f480全定义收据，不据mock hash添加兼容。撤回未提交假设补丁，生产工具/canonical保持。

原6例先4 PASS/2 FAIL仅因历史FINAL测试误读当前Schema及遗漏workspace_output；固定同发布工具/helper/993aede与测试URL GUC后主控真实6 PASS，原行/no-op/ArtifactsStore断言不弱化，格式／ESLint／types／独审CLEAR，2输入SHA核等。三注册probe库和fixture自有库均回收，正常库/卷未改。47bf19d两文件修复；原#2普通保add2历史集成31a7c89，完整树核等已验47bf19d，沿原PR交付，不带未证实兼容。早期探测主控输错摘要与后继未复现假设的失败保留，不归咎生产实现。Goal持续active，唯一TODO已纠偏。


### 2026-11-12 受控消费者组合与真实native补验

Storage原#2正常合main7155093c（树等31a7c89/47bf19d），仅两test/doc差异；本轮local/remote topic已清，其他旧工作树保留。CI annotation明确账户账单／额度导致任务未启动，未绕保护。

52 Run全终态／相关pending0后，只SIGTERM本方BFF/App，正常源码切609b0e93/ebc36617、原配置启动，health/页面200、原生会话刷新恢复。真实浏览器Share打开只GET200、未创建公开链接；自建无密钥MCP QA Disconnect→显式reauthorize200→不同connector pending/disabled/version1→exact Connector与Server GET200→硬刷新保持未连接，完整操作阶段trace仅1个reauthorize POST，无自动Prepare/OAuth/enable，Context7未改。刷新后再取旧response body已evict，保留实际早先ACK/状态/完整阶段trace，不冒重取得body。新1项测试配置待用户单项删除确认；原3项批准删除此前已完成，不能挪用其授权。

当前staged精确组合由326真实已提交Git blobs更新398引用，拓扑／15边0违例／原checkpoint通过；初次遗漏inventory owner版本更新而FAIL，按实际28.37纠偏后通过，未改规则。Skills现本人structured-report安装详情/真实SKILL.md读取200及返回已验，但当前账号Project为空，不冒广场/Project/作者history三入口全验，也不为验收复制旧账号数据。Goal仍active，完整Task B/原Draft PR出口未完，下一步仍只补当前TODO缺失。


### 2026-11-12 B-02最低补证、Skills多语言与B-08实施

主控复用现测试，只补Custom API材料资格/秘密边界：Capability573真实PG4 PASS（执行准入double、fixture随机库回收）；Agentb786在Python3.14.3三小文件＋Factory接缝107 PASS（model/sandbox doubles，178原实验/弃用warnings保留）；BFF609已构建隔离checkout单文件7 PASS。源码核对Acquire只作调用局部SecretStr、metadata-only prompt/recipe、先脱敏再截断与原文件/产物guard，未发现具体新明文出口；不新增每载体重复套件，不冒真实IAM撤权、任意编码外发DLP、全存量扫描或云E2B。

App正常英文Skills两radio回退中文、日期固定zh已修，5source/test路径：仅en补2已有key（另外8语言齐备）、formatter显式locale及两调用、现组件回归。writer7 RED→主控41 PASS/types/build与5SHA核等，独审CLEAR；原#49提交844fbbcb/0c6078e3，正常HMR后native英文/320px文本完整、Third-party整词换行、documentWidth320、日期November12，恢复视口。不称全站九语QA。

B08不换当前Agent8.17已发行pin；三设计实施门本地1d9ab9e，唯一writer app_merge_gate在隔离BFF推进同owner快照→原Chat outbox→私有材料。无profile/usage省略，关闭保revision，原key/regen原输入；consumer按canonical补闭集/knowledge条件/ID唯一性，不另造schema。主控Agent当前两相关文件21 PASS，待writer停写后独立真实PG；正常BFF609保持。

Admin原正常3320监听缺失，主控校原9bed/私有配置与Product origin一致后恢复正式Next dev；无代码/角色/凭据/Schema变更。匿名直入/Web入口307，当前浏览器/manage回/app且无管理菜单，只作当前用户拒绝边界，正管理员/撤权/跨tenant未验。原三QA已清；新增1MCP QA待单项删除确认，Goal仍active。


### 2026-11-12 B-08源码、真实PG与受控激活

原#17已推143ade1，现三设计门1d9ab9e。最终12输入manifest SHA1509e05272cc2c25eb65f2e9e3dbe180a099b678aa0441a96b9f9351abe328ef；主控68 related/types/正规Agent check，writer build/lint通过，两独审CLEAR。当前Agent固定7bfb/8.17原artifact不换；个人子图闭集/usage条件/ID唯一性从owner生成，不加平行schema。Agent当前owner两文件21 PASS，未改源码。

真实PG初轮前三旅程PASS，第4因fixture漏abort和缺current stream头FAIL；未改生产，仅同PG文件接真实SELECT完成后abort及合法活动头。修后5PASS，再同旅程末尾增加合法小snapshot interrupt正控，最终5PASS，原read故障/取消/1MiB/101项完整Message/outbox/cancel零effects断言保持。三自有库均DROP，正常DB/Redis不变；生产11输入持续原SHA，未重跑68/build去刷绿。

正常52终态/相关pending0后仅BFF受控SIGTERM并以原env源码143恢复health200，App0c不动、原两未知财务记录保留。Root232真实blobs/290引用配对，staged拓扑/15边0违例/原checkpointPASS。正常Profile当前只读，未改资料/知识、未发模型；native设置→新消息生效/恢复与公开产品指南仍继续，不关闭B08或整体Goal。


### 2026-11-12 B08产品分层说明与native验证开始

App原#49 c044c337：product/settings/personalization.md及原导航/index/availability/一致性/INDEX六路径，另仅现knowledgeUseHint九语言与直接测试，去掉公共过时Englishfallback。主控18冻结输入：47 related/types/阅读路线具名1/正规参考生成与门户build/62页20513内链/Appbuild全部通过，独审CLEAR；原大chunk/API changelog MD012/mts lint ignored不冒全门。正常AppHMR至c044，Knowledge当前英文提示正确；未改开关/知识。当前Profile四字段原值均空，已由正常UI onBlur保存75字符临时功能marker并显示Saved（非个人信息/秘密），单次新消息实际作用仍进行中，之后正常UI恢复原四字段。不以此Saved替代Run成功。

Appc044/BFF143精确组合staged85真实blobs/93引用重算，拓扑/15边0违例/原checkpointPASS。管理员正式read命令当前仅做预检：原manager authority env无native Session cookie路径，因此未启动CLI/未改权/未重置凭据；不拿历史不同管理员身份/tenant收据冒当前通过。整体Goal继续active。


### 2026-11-12 B-08正常native闭环与原值恢复

绑定Root21e833c4（Appc044/BFF143）精确干净已提交组合：UI Profile75字符临时指令onBlur Saved；新消息只含简短问候请求，不含marker。正常配置模型实际1次调用，AI SDK显示TASKB_PERSONAL_APPLIED问候，原资料清空恢复Saved/revision2后硬刷新仍恢复同一条原答复。仅此次新风险1模型调用，不重做旧Skill/MCP/Docker成功旅程。

权威normal BFF/Agent各自只读连接验证私有personal_context完全相同/owner相等、UserMessage不含marker/trace无原材料，双Message完成/Run terminal，model attempt observed/granted、financial ACK存在；53终态/pending0，旧两未知财务候选保持。原native提交network collector当时未观察到事件，明确无HTTP数量/状态断言；刷新重新启用Network后有203事件，未掩盖前段缺口。此前真实PG/owner规则风险组合独立承接知识开关/删除/跨actor/重放/regen，未为每分支重复真实模型。B08当前手工范围验收待原PR整体出口，自动记忆/外部导入仅既有支持范围说明，不扩大目标。

Appbf8ef938/BFFabbfd78只更新CURRENT，代码与已验c044/143逐路径相同；正常checkout同源，无需因纯文档再重启/刷测试。产品指南/9语知识提示、Portal62页20513链接已验。Goal active，后继B01/B13现有Admin→托管stdio实旅程与剩余域；本地新会话留作收据、1MCP QA删除待单项确认，原配置/未知WIP不动。

### 2026-11-12 PERF-02 最小收口

BFF原#17已推 `9cc717135255b639b66933ac58e48e813d696a86`：GET入口一次完整原生Session＋current_membership，原六跳变两跳；后续只验本request真实expiresAt/绝对预算/断连，不跨请求缓存。本人tenant/active Project SQL不变，PUT三次准入及写后撤权/unknown保持，无wire/Schema/依赖变化。主控四输入SHA核等、51 focused PASS/0 SKIP、完整types/diff-check，writer最终build/scoped lint/格式通过，独审CLEAR。证据依赖为真实localhost HTTP peer，不冒真实IAM/p95。

正常源同原配置受控切至9cc，前后53 Run均终态/待投递0，旧两未知财务记录保持。首次探测误用/health得404，正式/healthz复核另记录，不当服务故障或隐藏首probe。无PG/模型/全默认重跑。Root仅更新此BFF gitlink及232真实已提交blobs/290引用；拓扑 PASS、兼容 15 edges/0 violations、原 checkpoint PASS。原3QA先前已DELETE200＋刷新验，不重复删除；新增1QA单独待确认。Goal保持active，B01/B13及原表剩余项继续，未完成全TaskB或合原Draft PR。

### 2026-11-12 B13正常准入与下一片最小设计门

主控沿现IAM正式管理CLI（仅独立进程显式manager配置）和现owned开发账号新建原生Session，先正式read原false/version0，再CAS grant true/v1；正常Admin同源/manage成功，Models四目录200，Provider/托管包页可读。随后CAS恢复false/v2，两个operation_id对应IAM审计成功且old/new状态版本核等；仅新Session退出和自有0600 Cookie删除，原浏览器刷新/manage→/app、普通会话继续有效。未改正常服务配置/密码/tenant，未造Cookie或SQL角色。初始Web /iam/sign-in/email JSON405、退出非空body400均保留；正式CSRF表单与空body恢复成功。不是整个Admin CRUD通过。

真实新缺口已定位：users强制site却请求已不存在/api/user360，teams仍旧通用ResourceTable，壳层sites/manifests固定空。不是缺少待创建站点；不能用site=tenant或个人余额接口假装管理员任意用户读取。下一片按既有owner成员目录替换死入口，仍保未交付的更广后台需求，不标B13完整闭环。

Skills正常浏览器只读：同structured-report安装、作者current history、广场package均source_ref/revision1相同，SKILL.md目录及正文核等；GET及只读List/Get RPC无生命周期写。当前作者只有v1/账号无Project，旧版恢复和Project现行关联未运行；原收据/祖先按差额承接，不重复模型。封面404如实记录，未把不存在图片当包读取失败。Root3389/Appbf8/BFF9cc源码未变；临时授权/截图/原始收据仅ignored。Goal active，新增托管stdio QA准备/启用的动作确认待用户回答，不阻塞独立修复。

**B13成员目录切片设计门（主控裁决）**：IAM拥有当前tenant成员/角色事实，BFF现有 `/v1/admin/identity/members` 仍是唯一投影，Admin沿现adapter与已固定strict成员client读取，无新owner/协议/Schema/数据库/认证层。`/users` 和 `/teams` 以明确的当前租户成员/角色目录替换死site/manifest入口，共用一个有实际两调用方的业务组件；使用既有分页/cursor、刷新、401/403退休与断连/迟到隔离，过滤只声明当前页，不冒全局搜索。不修改AppShell的其它未承接模块；不造站点，不借本人账户读他人余额。删除两页旧独占user360/action/退款/停用假入口及无消费者的专属类型（仍有其它消费者则保留待对应切片）。保留积分现正式入口，不增充值/写权限。完整任意用户360及原后台尚缺的跨owner操作仍列OPEN，不以本只读片替代。最低验证：当前成员分页/空/失败重试/退休/迟到风险组件＋原成员client及本owner所需types/lint/build/contract；正常native管理员实读并复核撤权，不跑模型/全后端。Admin三面当前文档先更新此边界，再实施，独立writer与主控验收/原PR出口分开。

### 2026-11-12 B07双标签主旅程补验

Root3389/Appbf8/BFF9cc不改源码。正常浏览器两个同主体设置页：B初始GET revision2，A实际PUT expected_revision2成功200；B同expected2保存409，原B草稿保留。显式Reload显示权威A，再Use server profile，硬刷新仍A。随后按最新revision3将原四个空字段恢复PUT200，原标签硬刷新确认四空；另独立新原生Session走正式CSRF表单登录，profile GET200/revision4全空，再仅退出新Session并删除自有Cookie。没有模型/工具/资金/知识开关调用，也没有版本回滚；当前工作浏览器Session未退出。

三个写入阶段request/response事件完整无truncated/hasMore；首A GET未捕获、后续旧response body lookup已evict均记录，不能声称全程trace完整；A outgoing expected2和B GET2、UI冲突/权威选择/刷新与新登录GET是独立实际证据。只补关闭B07此缺口，B06、Project ACL、后台完整CRUD及整个TaskB不因此完成。截图/收据仅ignored，不重跑默认/模型或旧已验分支。

### 2026-11-12 B06接线定位/B13具名实施

主控新建独立原生Session经正式CSRF登录与本人auth读成功，随后 `/api/account/sessions?limit=25` 实际503 `account_sessions_unavailable`，尚未撤销任何会话。只读定位normal BFF未设置既有 `KOKORO_BFF_IAM_ACCOUNT_SESSIONS_SERVICE_CREDENTIAL_FILE`，IAM亦缺 `IAM_BFF_ACCOUNT_SESSION_CREDENTIAL_FILE`，普通登录专用user_context凭据不能当该生命周期profile复用；未因此改协议/加OAuth/token/SDK。自有本次Session已正式退出、自有Cookie删除，原工作Session不变。下一步只核登记的专用文件/正式格式，再由主控纯配置配对、按空闲受控重启并补两个真实缺口。

B13成员目录设计门已记同一有效计划。唯一writer api_perf_audit复用现干净Admin checkout，先由主控停止自己启动的3320，再从已fetch main08365f3（merge树等原normal9bed）建本轮codex/task-b-admin-directory；候选验收前不重开服务。写区仅users/teams、一个两消费方成员组件、直接测试、现中英词典和三短文档；无新owner/wire/Schema/认证层，较广后台CRUD/任意User360仍OPEN。受管隔离创建请求仍待工具响应，句柄仅留本地持续核验，未宣称结束/未重复创建；复用已有checkout继续实质推进，普通App/BFF/其它owner不变。

### 2026-11-12 B06真实接线闭环与Admin候选发行

只补normal IAM/BFF原已支持account_sessions专用路径，当前正常tenant精确配对、独立随机profile、0600文件，原.env私有备份；无源码/协议/Schema/SQL模型/认证层变化。主控空闲检查后受控重启两owner，healthz均200。正常浏览器当前Session列表200，精确核QA新Session身份/创建时间后，仅该目标DELETE200，fresh列表200目标消失，原当前和原另一Session都保留；被撤会话自己的auth读false、受保护profile401。此为正常IAM/BFF真实链，不是HTTP替身。

另一个自建QA Session仅fixture缩短自身expires_at到8秒，正式auth先true且返回的真实expiresAt精确相符；墙钟过期后auth=false/profile401，不先logout/不改全局TTL/原Session，不冒七天浸泡或浏览器自动倒计时已验。两个测试Session均经正式退出与自有Cookie清理。前后53 Run终态/pending0，旧两财务未知保持；不调用新模型/资金/全默认。原503与首次临时登录残留已清理，完整收据只留ignored。

Admin目录候选10bc264已沿自有PR7推送（此前Admin PR已合闭，实际新需求才建），writer完整lint/contract/355测试/build/post-types，主控九SHA/相关35测试/独审CLEAR，当前待正常native中英/窄屏与撤权。Root只配新Admin gitlink；inventory无该Admin repository_path描述项，本次0引用/0blob变化，不能冒重算其它owner。本轮Root拓扑PASS、15边0违例、原checkpoint PASS；整个TaskB/后台广义CRUD仍OPEN，Goal active。

### 2026-11-12 B11/B12既有Run只读补证

未增加模型/工具调用或财务写入。主控按现canonical schema，对B08既有Run在BFF、Agent、Billing各owner独立只读查询，无跨owner SQL。唯一dispatch/attempt/admission及原会话核等；actor/payer、attempt/call/ordinal和调用三摘要、模型精确revision/digest与冻结报价均匹配。Agent actual=verified，最新evidence/ACK/admission引用核等；ACK/admission/hold=captured，usage/settlement=settled，单条usage debit与capture金额、每个funding allocation及预留=capture+release守恒核等。

首次摘要仅因psycopg UUID与string比较方式产生admission_matches=false，原始身份其实相等；统一两侧类型后全部关系核等，初次私有摘要保留，无生产修复/重新计价或重跑模型。该证据只证明此前B08真实Run及其历史冻结报价，不把当前活动政策、旧两未知预占、所有Run或Admin政策管理顺带标完成。完整查询和无秘密摘要均只留ignored，唯一TODO已补此差额。

### 2026-11-12 B13窄屏首轮FAIL与最小标题修复

Admin10bc264正常native验证当前tenant3成员、正式GET200、两入口一致、本页筛选1→清空3、中英/UTC均通过；390px documentWidth390、表内310/920横滚正确，但截图标题/说明被默认PageHeader同一行ellipsis截为Curre...，故首轮视觉FAIL保留，不以DOM全文或宽度通过冒验收。

后继Admin4241c2f只改组件标题结构与原两个公开语义断言：正式pageHeaderRender=false、语义h1和独立自然换行说明，不改读取/状态机/文案/表格。主控两SHA/11 focused、独审CLEAR；writer相关lint/types/build/post-types通过，不重复355/后端/模型。原临时role已恢复false/version4、新Session/cookie已清、原浏览器回/app；再由主控停自启Admin修候选。新源正常390最终复验仍待，原PR7保持Draft。

Root仅固定该Admin新gitlink，owner传输/契约/生成物与09e1完全相同，沿此前合同门证据，不重跑不变输入；本轮只补新gitlink拓扑。Goal active，全部TaskB及后台更广合同需求仍OPEN。

### 2026-11-12 B13目录读取片最终native验收

绑定Root5d9a1760/Admin4241c2f正常源码（后继e7f2f79仅README，九源码/设计输入冻结核等）。正式当前tenant成员GET200/3项、Users/Teams同事实、当前页筛选和清空、中英UTC均已实测；首轮10bc390标题/说明单行截断FAIL保留。最终4241在390px中英h1/说明自然完整换行，标题与说明client/scroll均310、documentWidth390，表格仅内部横滚；保截图对照，不冒全站/全部语言Manus等同。

当前role撤销后原挂载目录刷新实际403，私有成员行立即清退；显式重核回/app，原工作会话仍可用。最后临时platform_admin恢复false/v6，三次临时窗口共六CAS成功audit old/new版本核等，新Session全部正式退出/自有Cookie清除，locale=en及viewport恢复。无业务写/新模型/资金操作；正常Admin已恢复3320，原核心owner和数据保持。

主控最终两SHA/11 focused/独审CLEAR，writer最终相关lint/types/build/post-types；前序九SHA/主控35与writer355等按阶段保留，不拼成最终全量测试全绿。原PR7保持Draft；只读成员目录此片关闭，广义User360、其它后台管理/政策与TaskB原剩余项仍OPEN。Root只配DocOnly后继gitlink；传输输入与已验09e1相同，沿原合同门，补本轮拓扑，不重复模型/PG/默认。Goal持续active。

### 2026-11-12 PERF-03发行及下一native隔离旅程

BFF原PR17已推aad81e7，4生产路径/2原测试完成模型目录一次共同deadline与本方取消，删除本GET无用幂等Map。主控六SHA停写核等、同两文件34 PASS/0 SKIP、完整types；独审原六文件CLEAR，主控另补零预算503缺x-request-id的真实RED/最小header修复并复核，余四SHA不变。writer最终build/scoped lint通过；测试原文件基线也有format告警，只新段格式通过，不冒整文件格式绿。无contract/Schema/依赖/新认证/cache/retry变化。

正常BFF在空闲检查后同原配置受控切aad，healthz200，前后53Run终态/pending0，旧两财务未知保持。Root按232个真实已提交BFF blobs重算290引用，本轮暂存组合拓扑PASS、兼容15边/0违例、原checkpoint PASS；均为本组合实际结果，不用旧门冒新组合。原正常模型读/浏览器菜单仅补必要回读，无新模型或资金操作。

当前另有私有native模型/计价隔离driver正在接线：真实IAM/App/Admin/BFF/System/Billing，正常tenant/配置不动；只允许独立源码/输出/临时数据库及精确localhost开发态fixture接缝，尚未启动或验证，不冒已闭环。stdio echo包已在本地由锁定SDK生成声明并经Agent/Platform两owner结构验证，未创建Provider/上传/发布/启动进程，等待原动作确认。Project ACL产品边界同样待用户选择；这些局部前置不暂停整个Goal。

### 2026-11-12 native目录与icon观察核验

Root0b725116/BFFaad正常认证目录GET200、两现有模型选项/Default原选中态和Esc回焦已验；network189事件未截断，未发任务/模型或资金操作。精确组合拓扑PASS、兼容15边0违例、原checkpoint PASS已提交推送原#67，BFF原#17描述同步；两PR继续Draft、整体TaskB未完。

icon观察由api_perf_audit只读链路核验、主控当前native采样：同一Context7服务详情200/无icon绑定，独立media404；本挂载只发1次media请求，打开详情不重读，首字母C及Connected保持，列表200。正式owner已定义optional绑定缺失404，App已有no retry/fallback，无新缺陷或必要代码。旧布尔样本缺exact URL不能倒填根因，当前404body被CDP回收故不称全trace。只关闭该观察，不扩缓存/协议/服务。原三QA配置已删除；后来新reauthorization配置不在三项授权内，仍待原单项确认。

B09主动leave源码已具备，缺真实主动退出而非管理员移除证据。正常Product固定tenant/最后owner保护，不让原账号退出；现隔离主机primary/secondary是同用户，不能伪造第二成员。后继复用真实IAM/App/BFF隔离组织与正式邀请一个QA member/两个自然Session，预期退出窗口logout后401、另一Session当前资格403；不强锁退出窗口403或新写生产实现。

### 2026-11-12 B13有限原范围与当前隔离接线

主控复核原交接B13（功能表）及有效计划B13条目，composer_ui_audit只读交叉核验：必交为具名Skills审核、Provider/MCP/API/模型、用户团队权限、积分计价/流水和对应操作审计；任意User360、全局画像/退款、跨owner统一日志平台并非原文具体旅程。唯一TODO将笼统“广义User360未完”改成这些有限原范围，不借此取消真实权限/审计或Custom API管理的owner设计缺口。已验非现金发放与同Run账本不重复。

后台native模型/计价接线首run仅source阶段FAIL：Admin archive不跟踪Next生成的next-env.d.ts，而旧隔离helper要求其存在。未启动DB/服务、cleanup PASS；私有driver补标准两reference bootstrap及原helper输入检查，不改生产源。后继冻结Root2d1a074f/六owner提交并审查exact localhost三处test-only fixture diff：第二轮System安装遇macOS Unix socket临时路径过长，cleanup PASS；短路径修正后第三轮iam_native报告SmokeError、cleanup PASS；源码定位现凭据根落在已注册短tmp，却仍传旧run-directory，推断是归属guard不匹配，后继待实际证实。现仅修注册短tmp与既有helper凭据根的接线，不放宽生产/auth校验；尚无浏览器写旅程成功证据。仅回收已终态B-T1a独立验证venv，保源/补丁/收据；正常venv/数据/进程不动，实际释放量不据逻辑214MiB推断。原managed worktree工具确认返回超时，Git只见既有Admin checkout；不重启创建操作。

### 2026-11-12 Billing readiness接线与当前活动政策

第四隔离run正常构建/IAM/System已走通，Billing真实/readyz持续200却等待超时，outcome FAIL/cleanup PASS。主控比对Billing canonical/controller/生成ReadyResponse：正式Root helper仍要求早已退役的data.module，故不是Billing/PG不健康。api_perf_audit仅删此旧期望，现原测试用独立canonical body替代复制被测READY；真实RED两项→本文件41 PASS/0 SKIP，主控同41/两SHA/格式检查复验。status=ready/PG=ok/绝对期限/停止等原行为不变；既有sys.path后import E402保留，不冒全lint/全Root门绿。仅修Root test接线，Billing生产源码/协议不改；新冻结组合后再补同一次缺失native后台旅程，不重跑模型/资金。

另主控对正常Billing以单owner只读repeatable-read/DB时钟补证：当前活动rate v3、policy v2，均与latest一致且非未来；rate计数/profile配对、已验模型exact revision/digest当前覆盖与币种一致。选择按正式owner先tenant revision后过滤model，不把latest或历史冻结快照当今天政策；仅此时点/该模型，不冒全部模型、后台发布或新费用。原价/资金/历史快照保持，当前报告时间规范化UTC。

### 2026-11-12 native后台阶段证据及容量恢复

绑定Rootdf295dac/精确六owner的第六run：真实IAM/System/Billing/BFF/App/Admin启动，匿名Admin API401、正式/login303；CUA独立localhost原生账号实际登录进入工作台，无Bearer/假Cookie。访问/manage/models首次编译时Turbopack SST出现ENOSPC、owned_service_exited，尚无模型/标签/费率/政策业务写。本轮outcome FAIL；自动回收最终receipt同受ENOSPC影响，不能称自动cleanup PASS。

主控查全注册pgroup已无进程，先仅删其生成.next释放空间，再沿具名资源marker/原helper回收同一测试库与Redis/origin键；库回收前九业务表（model definition/revision/label、费率/政策、账户/hold/journal、Agent outbox）均0。自有shorttmp/source/deps、账号/密钥文件回收，原生测试Cookie清除/页关，人工cleanup PASS独立留证。正常BFF随后发现旧进程exit1/无监听，旧log不足证根因；仅同aad/原配置恢复，healthz/readyz200。原工作台native刷新auth/session及models均200/189事件无截断，原会话保持，无新模型/资金动作；正常App200。未清正常数据、卷或他人资源。

私有driver后继只增加容量控制：已锁Next16.2.6支持的dev磁盘缓存关闭，仍Turbopack；两private config独立记录原blob/补丁摘要，不混IAM三test-only接缝。启动要求2GiB/运行保底1GiB，低于则正常退出回收；错误记录失败不阻断finally。静态准备通过，未重跑；随后只回收原TaskA已终态私有qualification的两node_modules与一.next叶，保源码/收据/manifest；主控核七门终态、基线为当前App祖先、无活跃argv/正常依赖链接。allocated约2.35GiB因APFS共享实际仅增143MiB，现Data约1.38GiB仍低于2GiB预算，不拿逻辑大小冒实得、不继续无界扫描或删除正常输出。Goal持续active，完整后台写旅程和原TaskB其余具名残项仍OPEN；原PR不合main/不部署。

### 2026-11-12 侧栏既有key缺译修复派工

正常English截图的“新建任务/电脑/创作/自动化/任务/收起项目”等由App现t(key)直接产生，8个key仅中文源存在，非中文overlay缺席；不是这些标签来自System中文manifest，也未见第二LocaleProvider。composer_ui_audit单writer仅八非中文词典/两原测试及必要i18n INDEX，按所有9个上线语言补既有key，先RED再GREEN；不改中文源、key、Provider、导航资格、协议或CSS。主控管Git/验收/唯一台账。当前资源不足大隔离，只做focused/相关lint/非增量TS，不跑build/完整默认/资源，未冒已修/可合并。

live与private fallback出现Agent/Library的差别来自现manifest featureFlags/navigation与既有fallback，不据截图认定版本或System发布错误。manifest hook取navigator.language而非Settings当前locale是另一具名事实，当前未留实际navigation响应正文，后继定向核验语言切换影响，不混本片改动或假修正常配置。Goal持续active。

### 2026-11-13 当前阶段收口与下一差额

Goal实查active，整体Task B保持OPEN。App原#49新增00334cbe（基线bf8ef938，16路径含当前文档）：侧栏32个既有key九语言自有译文，补118缺译/7占位；拖动ARIA仅现有t向hook传必需label，两个真实caller承接，不改排序/权限/焦点/迟到逻辑、用户标题或locale框架。主控最终160 focused、相关ESLint、完整非增量TS、正常工作区production build通过，15输入前后SHA核等、独审CLEAR。最新真实French项目标题/空态正确并恢复English；实际目标视口1000×716/document1000，工具临时390 override未应用，不称本阶段新390验收。原15-key阶段窄屏证据仍单列，未重跑完整默认或模型/资金。

B13第七次隔离run0eb09c8e843ee281ba2f37f4绑定Root58215eca/已提交六owner（Appbf8，不混后继侧栏提交）。六owner真实启动/native登录通过；definition201、r1草稿201后publish409。确定原因是旧测试recipe空bounds，但System正式publish要求完整；Admin“可空”未解释发布要求且详情只读，登记明确后续UI补口，不放宽owner约束。保原409，主控同一run显式创建r2(8192/1024)201→发布200；label201→两次CAS200别名修改/恢复原null/default revision不变；rate/policy各201，硬刷新与正式GET完整配置/精确r2 digest核等。两条计价命令由主控显式触发原body/key HTTP replay，data回执完全一致；不是浏览器ACK丢失验收。

原driver只支持恰一个revision，其终态FAIL/exact_owned_browser_creations_required原样保留，cleanup PASS、credential log check PASS。独立补充verifier只核实录10命令、两个revision精确状态/两publish状态/CAS、fresh reads、原replay及五表零资金/Run，主控执行PASS；新增补充收据不覆盖原FAIL、不冒整个B13闭环。浏览器正式退出回landing，独占临时库/Redis/pgroup/源码输出由原helper回收；不可变配置随具名临时库清理不是产品retire/delete能力。正常账号/报价/资金/路由未动，无Provider/model请求。

后续只做已发现差额：B13草稿发布提示/可修正路径；原具名Skills审核、MCP/API管理、团队邀请/角色/审计等TODO仍OPEN，不扩User360/统一审计框架。共享移动侧栏primitive与manifest设置语言输入另列观察；不以有限词条齐备冒全站翻译完成。沿原PR，不部署、不提前合整PR。主控只短停自己的App3310用于build，同配置已恢复；本轮无源码/依赖副本新复制，原B13副本创建早于新备份规则，后继不得复用旧复制配方新建。

正常Agent Worker恢复补记：只读预检53 Run全终态、dispatch pending0（claimed53为历史）。Worker此前缺席，Agent.env.local本身缺BFF模型准入map；沿已登记launch_worker.py从BFF purpose凭据文件精确匹配当前tenant/caller/surface，进程内复用原secret/System角色并移除HTTP-only字段，不新增凭据或改生产配置。正式AppConfig/签名/Platform文件通过，主控启动原正式worker入口并观察到consuming日志；登记实际PID/exec及九个正常listener。此为消费就绪，不冒本轮新模型端到端成功，未提交新Run；旧财务未知项保持原正式恢复边界。

### 2026-11-13 B13 草稿修正接线设计门（当前实施）

- 事实/owner：System49a5已有updateModelRevisionDraft；System拥有草稿/发布不可变性与版本校验。BFFaad/Admin e7当前只承接create/publish，导致空bounds合法草稿没有产品内修正入口，真实409已留证。
- 选定位置：BFF扩现有model-configuration窄adapter，发布具名PATCH /v1/admin/model-revisions/{revision_id}（required idempotency-key+If-Match、现platform-admin准入/system:write），只透传owner已有草稿更新；Admin复用现ConfigurationFlow与revision表单，编辑仅草稿，model_id/revision不可修改；提交显式CAS，unknown保原body/key/version，退休/取消/迟到沿原流程。发布前缺bounds给就地解释，不改变System的最终执行边界，不用自动复制新revision代替修正。
- 契约：仅BFF兼容增量并提交固定owner blob给Admin正规消费；System及数据库不改，App原public子集pin暂不无意义升级，机器治理核兼容。保持Admin同源→BFF→System、内部服务身份+可信actor，不新增Cookie/OAuth/token/SDK/缓存。文档只改本次TECHNICAL_DESIGN/API_CONTRACT/current，Root单写台账。
- 删除/恢复/验收：没有legacy双路，不建通用编辑框架或第二草稿store；缺权限/过时版本/未知结果与已发布拒绝承接原控制。最低充分证据为现BFF实际Nest/loopback-owner传输与closed schema/权限/CAS/取消负控，Admin实际表单编辑/发布前反馈与原命令恢复；源码停写后主控focused/types/build+相关contract，真实owner草稿修正→发布补缺旅程另记，不重跑模型/支付/全部B13。

### 2026-11-13 B13 草稿修正候选验收/交付

原计划设计门落实：BFF原#17/396897b8固定Public28.38/217，System仍49a/既有845契约pin，只正规生成已有PATCH，源头草稿/不可变性/权限不变。现BFF现窄adapter+精确admin前缀/UUID/服务准入承接required key/CAS、closed非空partial、null/省略及同id草稿ACK。主控正常工作区build与五相关文件190 PASS/0SKIP；writer全lint/types/generator/semantic通过，独审CLEAR。原整contract1400PASS/2FAIL保留，准确修复原delete_series的16项exact enum与feedback负控误删无关Share项后两文件44 PASS；主控190已包含，但未拼成重跑全contract绿。

Admin原#7/df7883d固定该BFF原字节、46消费项并退役旧唯一无依赖vendor。复用原表单编辑当前草稿，冻结id/version及不可修改model_id/revision；新读只提示重开不自动rebase，合法空bounds草稿仍可保存，发布前缺bounds有原页反馈。原journal写入读回后onPrepared只退休matching编辑器，unknown显式原命令恢复，不清key/body/CAS或算成功；取消/卸载代际阻止异步validation和迟到接管。主控最终全47文件363 PASS/0SKIP、全lint/非增量types/两正式contract/build/post-types通过，停写18输入独审CLEAR，后继只有验收文案及纠正旧版本注释。

App原#49/c1444ee0仅同源桥精准开放此PATCH，原64KiB/body/key/CAS/Origin/Cookie/signal保持；主控56 focused/build、writer scopedlint/完整types通过，Public28.37子集及原生成链不盲升级。Root固定三仓精确HEAD，inventory核413真实committed blobs/507引用，拓扑/15边0违例/原checkpoint通过。三仓已推原PR，未merge main/部署。原B13第七次两revision/rate/policy真实旅程仍只证明旧组合，不借它代替本片新路径。

运行恢复先只读：53 Run全终态，Agent dispatch/BFF launch/steer/scheduled待办0，原两财务未知项保持；只替换主控自己的BFF进程，healthz/readyz200。App/Admin只短停用于各一次正常工作区build后同配置恢复，未复制源码/依赖、未动PG/Redis/卷/其它owner。App dev生成next-env路径diff单列未提交。下一检查点是隔离native真实“同一草稿PATCH补齐→publish→刷新”，不重复模型/费率/支付；新fixture须遵当前轻量源码/依赖规则，历史复制配方不复用。B09正式invite/accept/leave已定位，缺隔离双身份接线，不扩Project ACL或用logout401冒成员403。

### 2026-11-13 B13/B14 下一独立写区

主控验收与唯一Git/台账；sidebar_i18n_finish仅Admin修订表单与共用上游选择两组件复用现zh/en词典和真实LocaleProvider；实际Shell已有locale却固定Ant zhCN，一行按同一locale选择官方enUS/zhCN并补原hydration行为测试，不增加Provider或逐组件覆盖，不改业务/协议/框架；pricing_fixture_review只更新既有ignored native driver四文件为draft-correction与当前轻量复制/锁定安装规则，不启动资源。主控随后绑定三仓新提交/Root精确组合，单次补native同草稿修正/发布；不把另建r2或mock当该证据。

### 2026-11-13 B14/新native接线交接事实

Admin原#7后继87c228c只修两实际模型组件60个zh/en词条、现App上下文的发布确认，以及Shell现单一ConfigProvider跟随同一locale选择官方enUS/zhCN。用户模型名/协议、onPrepared/代际/CAS/null及目录不rebase保持；不加新Provider/解析层或逐组件重复覆盖。主控九输入冻结：全47文件367 PASS/0SKIP、完整lint、正常工作区build及构建后非增量types通过、独审CLEAR；原SSR/hydration/链接/监听回收覆盖保留。其它Models/Admin自定义旧文案未扩译，本片不冒全后台本地化/视觉完成。

Root配对Admin87c228c；BFF396897b8/Appc1444ee0及机器契约不变，拓扑/15边0违例/原checkpoint通过，未重复后端全门。主控同配置恢复Admin，正常数据/角色/资金未改。

新native driver仅ignored四文件静态准备并由主控纯检查/四SHA复验通过；draft-correction只同一r1创建→PATCH补齐(原CAS1)→publish(CAS2)→fresh版本3，原PATCH显式历史回执重放后仍须鲜读published3，不重复label/费率/模型/资金。新source复制遵rsync相同预检/实参、固定排除清单/提交blob核等，无旧依赖/cache复制；实际fixturepatch门批准后才按各owner engines/锁安装（Next22，其它24），8GiB启动预算/运行保底1GiB，拒复用run-id时不碰历史目录。正常pnpm/Corepack只读缓存可复用，不另备缓存。主控仅一次最小旧driver四源码备份69,265bytes，未带依赖；旧runs原失败/收据保持。尚未把静态检查当source复制、安装或native成功；下一步在新Root精确SHA上由主控启动并审实际patch。


### 2026-11-13 B13 native 执行检查点

主控独占资源/浏览器，pricing_fixture_review只读复审安装参数，sidebar_i18n_finish只读准备B09双身份接线。首新规则run c551e366f081e23dc7844615源码/私有patch门通过，锁安装请求下载超时FAIL，cleanup PASS；无业务/DB/浏览器动作。后继只调锁定pnpm下载请求预算600000ms/并发4，保锁、版本和engine。新run dc4d634d3525c1b6171576a7绑定Root2303d74c，4137源码与三IAM test/两Next resource patch由主控实际核验批准，安装进行中。只补同一r1 PATCH→publish→fresh及原PATCH回执/当前态分离，不重复计价/模型旅程；Goal active，整Task B及原PR仍OPEN。


后继实测：dc4d634d3525c1b6171576a7六owner锁安装/构建/启动通过，真实native登录成功；/manage/models首次编译触发Next16.2.6已确认Google /l/font?kit=...&skey=... 无扩展URL解析缺陷（官方issue99114/fix100158），不是业务API/TLS失败。实际截图/主控browser-failure-receipt保留；正式Sign out后abort，原driver FAIL/cleanup PASS。只实施Admin同族/字重真实官方local字体+许可的局部修复，不改依赖/认证/模型，focused及真实Next build后配新Root再补同草稿。该环境失败不扩为整个Goal blocked。

局部font修复已沿Admin原#7推送`3a521aba`：原三族/字重local真实官方资产779316bytes、OFL/固定来源SHA，主控12focused/非增量types/scopedlint/真实Turbopack build/posttypes/独审通过；15提交输入核等，normal同配置恢复。后继仅复用现pnpm store按锁copy安装（prefer-offline、无复制依赖/cache或prune/reset；cleanup只run），免重复下载，不换runtime或锁版本。新Root配对后补同草稿旅程，未冒已通过。B09三命令隔离接线已纯准备/静态核验，未邀成员/改角色或跑真实旅程。


### 2026-11-13 B13 同草稿缺失native收据收口

主控run9634eda90cfe493517b5394b绑定Root89de6a62/Admin3a521aba精确组合。唯一definition201与r1空bounds201；缺bounds发布仅本页英文反馈、观察代理无publish请求；同ID PATCH仅context8192/output1024、原key/CAS1→200/version2，再显式publish CAS2→200/version3，浏览器硬刷新详情同ID/摘要/限额且Published/无Edit。原PATCH显式重放历史ACK2不变、独立fresh仍published3。owner读回/七Billing资金/计价表与BFF dispatch均0/正式logout/cleanup/credential-log-check PASS。完整receipt与截图保ignored，前c551下载超时和dc4字体编译FAIL均保留；不拼历史r2/计价或mock。English表单/确认/Ant文案本次实际通过，非全Admin翻译/视觉完成。

本子项关闭，整体B13/Task B/原PR仍OPEN/Draft；Goal实查active。下一个为B09双身份正式邀请/CSRF接受/本人UI leave与独立Session403，三命令test协议纯准备/语法与schema检查已交主控，未实际邀请/授成员/跑服务。继续既有owner，无新认证/SDK/框架，不重跑模型/资金或已验B06/B07。
