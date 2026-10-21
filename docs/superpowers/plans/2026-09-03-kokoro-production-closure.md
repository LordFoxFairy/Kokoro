## 2026-10-20 最新执行目标与遗留需求总表

本节是当前跟进入口，覆盖下方历史排期与状态；历史段落只作当时证据，不把旧“待PR／暂停／已完成”自动视作现在的事实。仍使用本计划及 `docs/CURRENT.md`，不新增任务中心。

**当前活动目标保持完整**：闭环 Kokoro Skills 正式产品能力，完成 Manus v2 `skill.list` 对齐的 `/v1/skill.list` 契约、owner/BFF/App/Admin 接线及真实验收；随后按同一边界收敛 MCP/Connectors，逐仓 PR 后由 Root 精确 gitlink 聚合进入 main。不得以一个导入修复、组件通过或服务健康替代整个目标完成。

### 当前目标：按依赖顺序完成

| 工作项 | 当前状态与证据 | 下一步／完成条件 | owner 与写区 |
| --- | --- | --- | --- |
| Skills 本地 ZIP 导入 | **已合 owner、正常主路径已验**。Platform [PR #10](https://github.com/LordFoxFairy/kokoro-capability/pull/10) 合并 `c9862466267e6545c0b7f191357e9b8182dcca89`。修复既有获取来源持久化及 Platform Connect内部Finalize/Get 投影缺失（owner测试证明）；浏览器JSON不直接暴露该字段，只证明原严格BFF消费与正常主路径成功；原未知结果经只读查询恢复，新纯文档包 Begin201→Complete200→Finalize200，精确参考文件可读。 | Root pin 该已合 SHA；保留两份验收样本及证据，清理另按产品恢复能力处理；不增加兼容分支、Schema 或重复上传。 | Platform `modules/skills` 与既有导入事务；Root 只集成。 |
| Skills 公开 v1 合同与身份语义 | **Product 人类会话路径已有主线实现与定向验证；完整 Manus 身份语义待配对**。现有 BFF 两套定向测试82 PASS，owner/client为测试peer。官方 API Key、普通 OAuth 自身 Open App、trusted client 的对象范围尚无等价整链证据。 | 在 IAM/BFF 既有能力上核对三类身份映射、项目参数与对象范围；未批准的新身份边界先明确裁决，不把 human Product 准入冒成三模式均完成。沿唯一机器契约补消费者与真实权限负控，不新增公共网关或旧协议入口。 | IAM 身份/授权；BFF Product API；Platform 数据事实。 |
| Skills App/Admin 完整旅程 | **个人列表、预览、包文件和本地导入已实测；管理员发布与全角色矩阵待验**。后台原标签仍有浏览器工具准入问题；接口／组件证据不替代页面。 | 对照 Manus 同尺寸状态，完成官方草稿→包→发布→安装→精确版本→撤回/恢复边界；补普通用户、跨tenant及撤权负控。后台从正常产品入口恢复后实测，不绕工具拦截；产品缺陷先复现再修。 | App 技能子组件、Admin Skills 子组件；BFF/Platform 原操作。 |
| MCP/Connectors 全生命周期 | **已交付的读取/可用性/受管包和隔离 OAuth 证据保留；远程 OAuth/stdio 正常完整生命周期仍未证实**。ZIP 包不是所有 MCP 连接方式的替代。 | Skills 之后先同步同事的最新成果与写区；复用已有能力，逐项核连接、授权、发现、续期/重连、停用、撤销及未知结果恢复。实际执行证据与控制面证据分列；未交接前不改同事模块。 | Platform/MCP、Agent runtime、BFF/App；自动化和连接器当前由同事负责写入。 |
| 组合发布、手册与清理 | **分批交付，不宣称全部 PR 完成**。已合项、仅本地候选、正常加载分别核验。 | 各 owner 本地验收/审查→集中 push/PR/merge→Root 精确 pin→正常加载/关键回读；不等 CI，不绕强制保护。只删除已合且无新提交/无在用工作的分支，保留未交接改动。功能手册注明已支持/未支持/未验与已批准差异。 | Root 集成；各业务 owner 保有唯一写入边界。 |

### 必须保留的历史需求：未完成，不丢单也不并入当前 Skills 修复

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

- 先完成当前 Skills 缺口，再接 MCP；模型/账户/积分、首页/聊天、项目分别保留完整需求，不因记录齐全就同时扩大写区。用户调整优先级时只更新本节，保留原完成条件。
- 同步记录区分 `origin/main`、本地候选、Root pin、运行源码四种状态。本轮 Root+12 子仓非递归 fetch均成功；Platform主目录随后快进到PR10合并SHA。Root和其他候选保留已有未提交/未发布工作，不盲pull或覆盖。
- 本次 Skills owner 格式/lint/types/契约/artifact/schema/build全部exit0；完整测试2562 PASS/432资源SKIP，明确真实PostgreSQL30 PASS/0SKIP；跳过不是通过。正常浏览器已验原结果只读恢复、新包导入及精确文件读取，未执行技能、模型或积分写入。
- 测试按变更风险选最低充分层级；修复补独有回归，交付跑受影响owner必要门，不因测试数量制造无效重复。截图/原始网络/机器配置只留ignored，Git仅含脱敏规格与验证结论。
- 当前运行 Agent guard 仍 disabled；这是真实运行状态，不以历史暂停文字替代用户最新授权，也不因本表规划自动放行执行。真钱支付仍不做。最终验收逐项说明实际完成、未执行、阻塞和后继owner。

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
