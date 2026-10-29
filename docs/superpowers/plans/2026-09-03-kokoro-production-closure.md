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
- [ ] Agent Run safe refs冻结、fresh lease绑定、Describe说明装配与隔离backend统一选择/回收；不得把当前独立adapter冒充已接Run。
- [ ] BFF/App 选择冻结、会话恢复与统一菜单。
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
