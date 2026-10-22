## 2026-10-22 Skills公开入口验收与文档配对

未重新采集或写入Manus账号；继续使用此前已授权实测规格。Kokoro主方真实外部Next `/v1/skill.list` 经原生Bearer接BFF及真实IAM/Platform，18请求五组通过，覆盖三身份、tenant/project隔离、撤销及精确App绑定。内部service envelope只由App注入，外部不持有机器凭据；结果不赋予执行权。App公开Docs现固定Public22.3／176公开项，6网站私有项继续排除；自然幂等PUT、系列删除与身份说明同步，Root旧门户退役。具体交付SHA及未验MCP/实际执行边界见CURRENT，不以文档构建代替正常浏览器或工具旅程。

## 2026-10-22 模型候选与提供方目录的边界

沿App已保存的Manus实测：模型菜单是产品运行档位，`GET /api/chat/listMainModelCandidates` 当次200且`data.candidates=[]`，不据此猜其供应商列表或后台私有配置。用户要求的提供方刷新属于Kokoro既定System配置能力：现有加密Key读取上游`/models`→管理员只读候选→显式共享修订／业务组合→本业务model list；不将28个发现候选自动发布、默认启用或推断能力／价格。System `845cf46`／BFF `e461d51`已正常加载，Admin `1f9021a`／App `cac62fe`同一发行物已正常配对，提供方刷新／搜索及修订选择已真实验收；这不是新增Manus后台实测，也不把候选列表成功称为Agent执行或积分结算通过。

## 2026-10-21 历史恢复实现补记（非新增参考采集）

已实测的 Manus 恢复仍是“原内容→新UID版本”，不是旧指针回退。Platform `97b27b3` 补本人personal停用/撤回原包读取和validated撤回基版新空draft，旧Skill/publication/安装不变，隔离仍拒绝；真实PG已验。BFF4a10f8b/App94d3687已接原ZIP与新UID发布，隔离Next/CUA通过历史恢复/关闭重开保原尝试；正常owner/Storage写旅程现已通过：原ZIP摘要相同、新UID修订3、旧1/2及原安装不变，刷新可读；隔离和正常证据分开，不称完整站点像素对齐。原参考样本已按授权删除，不重复创建/删除；其余身份/删除/后台/MCP完成条件不变。

## 2026-10-21 Kokoro 正常个人历史读链复验

参考仍是本日已采集的 Manus 个人历史与恢复旅程；本轮没有再次写入或删除参考账号。Kokoro 正常 Platform efe1ed1／BFF d28f7db／App e9bc2a3 已实际配对。本人菜单进入 `GET /api/hub/self/skills/managed/{skill_id}/versions`，200 返回正式 publication 与两条历史；current v2 已撤回但可由本人读取，v1 原安装仍停用。两个精确 UID 的 `/package` 目录和正文均200，v1 的 references/checklist.md 实际显示独立标记；刷新重开，历史与 publication 未变。选版不发布／恢复或升级安装。

612×766和390×844保留新正常截图；后者 dialog374×828、x8/y8且无横溢。初次读链窗口完整，整页刷新窗口截断，不据此宣称全量网络零写或正常执行已验；实际额外 POST 是 Auth.js 续期。数据、会话、网络原件与截图留本地ignored，不进入Git。

仍有明确差距：此前 UI 的“当前版本”未同时标识撤回；本轮 App49ddf7f 已正常补齐并核历史／publication 原样，动作窗仅GET、无截断，390窄屏无横溢；用户恢复的确认条件已在 Platform3fc971e 候选实现并通过隔离并发／重放；BFF／App／Admin 与正常环境未消费，完整新UID写旅程仍待，不据owner通过称Manus产品已对齐。系列永久删除、公开三身份、后台与 MCP 仍未完成，不将本次读链记作全目标闭环。

## 2026-10-21 个人参考样本删除实测

用户在删除动作前确认仅操作 `kokoro-reference-publisher-20261021`。菜单“删除”先展示“删除此技能？”及“您稍后可以通过重新上传再次添加此技能。”；确认后实际 `POST /skill.v1.SkillService/DeleteSkill`，请求 `{skillId}`，HTTP200、响应 `{}`。页面回到个人技能空列表并提示该样本已删除。重新打开已观察的旧详情入口，实际 `POST /skill.v1.SkillOptionalService/GetSkill` 返回HTTP404，`code=not_found` / `SKILL_NOT_FOUND`；旧详情及三条历史的页面入口均不可用。

这证明产品删除与卸载／撤回不同；重新上传属于重新添加，不是已证明的恢复入口。本次未通过页面验证三份旧包物理删除或后端保留期限，不宣称抹除了历史 bytes。没有执行技能／模型、分享或操作其他内容。网络观察无截断，结束后已关闭；原始会话材料不进入 Git。后继 Kokoro 系列删除仍需 owner 正式状态和迟到发布防复活，不把此参考当数据物理清理授权。

## 2026-10-21 个人技能替换与历史恢复：已授权真实写旅程

用户明确批准后，只操作此前创建的纯文档参考样本 `kokoro-reference-publisher-20261021`。参考为 Manus 个人技能详情，中文浅色、612×766；上传一次仅含根目录 `SKILL.md` 的替换 ZIP，刷新重新打开确认新增文档标记，随后从历史恢复原版本。未分享、执行技能／模型或删除；临时视口及 Network 观察已恢复。

| 实际动作 | 网站私有 API 输入／输出 | 页面与状态证据 |
| --- | --- | --- |
| 替换 | `POST /skill.v1.SkillService/UploadSkill`，`{content:<base64 ZIP>,overwrite:true}`；200 `{skill}`。 | 仍是同一技能；刷新后正文出现 VERSION_2 文档标记，历史由1项变2项。这里按本次实际回执记，不假设具有新建回执的 `created` 字段。 |
| 历史读取 | `POST /skill.v1.SkillService/ListSkillVersions`，`{skillId}`；200 `{versions}`，每项 `versionUid,description,archiveSize,fileCount,createdAt`，当前项另有 `isCurrent:true`。 | 当前版本之外的行提供“恢复”；选中历史只读取精确版本正文，不自动恢复。 |
| 恢复确认与提交 | “此版本将作为新版本替换当前内容；当前状态仍保留历史”；`POST /skill.v1.SkillService/RestoreSkillVersion`，`{skillId,versionUid:<原版本>}`；200 `{skill}`。 | 随后历史2→3项，新 current UID 与原版本／替换版本均不同，两旧 UID 保留；不是把 current 指针直接退回原 UID。 |
| 恢复后精确回读 | `POST /skill.v1.SkillService/DownloadSkill`，`{skillId,versionUid:<新current>}`；200。 | 选中当前行后显示1文件／375B及原正文，替换标记消失。不能把仍选中的旧历史预览误当当前恢复失败。 |

上传、历史、恢复及最终精确读取短窗口均无截断；中间整页 reload 的宽窗口发生截断，不据它断言全页面零其他请求。原始响应、版本 UID、截图与请求收据只留本地 ignored；Git不保存 cookie、授权头、上传内容或签名下载地址。截图只证明该样本所处状态，不冒称所有主体／错误／并发均已验。

**对 Kokoro 的直接约束**：当前“不可变新修订发布／精确安装／撤回”不能冒充以上完整语义。历史恢复应保旧版本与旧消息引用、创建含旧内容的新修订，并沿当前发布CAS和真实包校验；不自动升级其他安装。系列历史、恢复命令及删除语义尚无正式完整实现，需在 Platform owner 既有模块与固定 BFF/App/Admin 契约收口；不把管理员 quarantine restore 复用成用户版本恢复，不把撤回改名成删除。下方“未提交替换／恢复未观察”等只保留此前初次采集状态，本节为最新证据。

## 2026-10-21 正常 Skills 配对后的 UI／API 回读

本轮只重验Kokoro正常Product，不把旧Manus截图标成新采集或称已一比一。BFF192396d／App ee1d4a7／Admin04662c4的同一Public21.1.1原件已正常配对，模型配置能力保留，未启用执行。

| 页面动作 | 实际既有 browser-private API | 正常观察 |
| --- | --- | --- |
| 刷新个人技能列表 | `GET /api/hub/self/skill-installations?installed=true&limit=100` | 200；原纯文档样本revision1、installed=true、enabled=false、source_status=active。 |
| 打开精确安装详情 | `GET /api/hub/self/skill-installations/{installation_id}` | 200；source／revision／enabled与列表完全相同；作者Owner，正文可读。 |
| 更新技能表单 | `GET /api/hub/self/skills/managed/{skill_id}` | 200；正式source／series与当前安装一致，revision1 active；未选择新ZIP时提交禁用。 |
| 取消更新 | 无Skills写请求 | 完整短窗口记录4个GET／0写；返回原个人列表并聚焦搜索，未开启原停用安装。 |

612×766核作者／管理菜单，390×766核正文／更新表单，正文页面scrollWidth=390；临时视口与Network观察已恢复。长时间网络窗口出现截断，已保留为局部证据，不推断无未捕获请求；另取完整无截断的打开／取消短窗。原始截图和响应取证只留ignored，不提交正常数据／凭据。

这些API服务Product页面，不是公开 `/v1/skill.list` 的别名或验收替身。公开身份／项目权限矩阵、Manus历史／替换／删除与Kokoro当前“更新／撤回”的差异、正常Admin旅程仍未闭合；不把撤回改名为删除。完整文档站归App的维护边界见[现有计划Wave5](superpowers/plans/2026-09-03-kokoro-production-closure.md)，目录尚未迁移。

## 2026-10-21 API Docs 已交付的当前范围

Root PR61已合2e008595，沿原Developer API门户固定BFF feae0c0/Public19.0.1原始commit和digest，共享只读public投影生成159operation／344schema，6browser-private不发布；不复制Manus私有后端，不建第二份可编辑OpenAPI。导航、指南、技能并集／精确版本、认证、交互恢复与实际wire字段均按owner契约；不能把文档存在解释为APIKey/OpenApp/trusted已经接通。

真实CUA已验搜索skill.list→正确生成锚点、字段搜索、关闭恢复、手机菜单→参考；1280／390页面宽均不溢出，frontmatter外露、正则误链接／多余转义和宽表溢出已修。完整43测试、5loopback示例、provenance／reference／architecture／build／links通过，独审无剩余本片阻断。原始截图／日志留ignored。保留大生成页首次观察超时和渲染稳定前的旧视图，不称全门户Manus像素级完成。页面、正常服务、身份／对象范围与副作用旅程仍分项验收，由Agent自己处理，不要求用户频繁代测。

## 当前跟进范围（2026-10-21）

执行顺序以[现有闭环计划首节](superpowers/plans/2026-09-03-kokoro-production-closure.md)为准；下方历史“唯一目标／连续执行”只保留当时裁决，不覆盖最近的账户／积分优先级。字段和owner边界仍按各有效契约执行，本页只存对照证据和未观察项。

本日个人技能补验：用户明确批准后，已在 Manus 当前个人账号上传一份纯文档参考样本，实测详情、更多菜单、版本历史和替换弹窗；未分享、执行技能／模型、提交替换或删除。Kokoro正常个人详情缺更新／撤回入口已由页面与代码共同确认：App `9db45ba` 移除个人发布管理组件的生产调用；现有后端版本／撤回能力保留。现已按既有组件恢复更新／撤回入口，正常新版本旅程见下；不把重新上传同名ZIP当作新版本，不回退整套旧布局。

另外，Kokoro安装详情真实GET200返回个人publisher_profile，但原页面显示站点品牌，已作本地最小修复：精确安装的真实作者优先，缺失不伪造，官方来源才保留品牌。正常612×766刷新后和390×766窄屏显示正确；窄屏详情clientWidth与scrollWidth均369，未出现横向溢出。此为Kokoro自身事实与展示一致性验收，不是Manus个人更新旅程已对齐；没有更改正常数据或执行技能，截图与原始证据仅ignored。

### 2026-10-21 API Docs 与整链自验（新增明确需求）

用户要求逐页面采集实际 API 并一一比对，Kokoro 也提供可搜索的 API Docs，采用“快速开始／认证与请求约定／使用指南／API 参考”的导航与方法、路径、请求及响应示例，方便持续校正。截图是信息架构参考，不作为其标题所示 Search Service 已有能力或 Manus 未观察接口的证据；不为文档额外建设搜索后端或复制参考业务。

本次源码确认既有 `developer-docs/` 已有VitePress中文导航和本地搜索，但catalog仍固定BFF1.0.0/0c3c2c4，未与已合Public19.0.1配对：旧版63操作且缺skill.list；当前165操作为159 public＋6 browser-private，不能将网站私有项直接公开。认证从旧namespace/principal自报头转为正式Product Bearer准入，旧请求ID指南也非当前链路事实。后续升级现门户，不重新搭一套，也不把旧指南直接称为当前接口文档。

沿既有 Developer API 门户计划实施：BFF 仍是公开 Product API 唯一机器事实源，Reference 从固定 commit/version/digest 的 owner OpenAPI 生成；Root只聚合指南与对照，不另存可编辑DTO/schema。已批准的Manus公开对应项保持原方法/后缀/字段/错误语义，只将/v2改/v1；网站私有RPC观察与正式公开文档分开标识，不把已抓到的私有方法全部宣称公开支持。指南只使用真实已交付API，示例脱敏，不保存Cookie、Token、签名下载地址或Key。

每个本次能力记录一条紧凑闭环：参考URL/日期/页面动作→真实方法与路径→query/body/headers的安全字段名→成功/错误/分页/权限与状态变化→Kokoro operation及实现owner→正常页面操作/持久化/刷新回读/失败恢复的证据。缺失、未观察、仅候选、已实现未验和已验分开，不凭单个200或截图判一致。API事实对齐之外，组件布局、焦点、键盘、响应式及状态连续性仍需对应页面实测。

整链测试由Agent主动完成，不把日常刷新、打开页面或反复点击排错交回用户；从冻结源码到正常运行版本逐项核对。现有样本优先复用，不重复写入或触动同事写区；不可逆副作用及未批准身份边界仍按明确授权范围处理。只有页面、API、数据/状态、恢复、文档和实际运行版本均有对应证据才标记该能力闭环。

### 2026-10-21 个人技能参考样本：真实菜单与版本读取

参考为 [Manus 个人技能](https://manus.im/app#settings/skills/personal)，中文浅色、612×766；样本只含根目录 `SKILL.md`，无脚本、凭据或外部资源。实际“更多”菜单为**使用 Manus 编辑／历史记录／替换／删除**，容器宽200、高152、内边距4、圆角12；菜单项高36、内边距8、图文间距8、字体14/20。不是此前推测的“更新／撤回”两项。

| 已实测动作 | 实际 API 输入／输出 | 可确认的边界 |
| --- | --- | --- |
| 上传个人样本 | `POST /skill.v1.SkillService/UploadSkill`，JSON `{content: <base64 ZIP>}`；200返回 `{skill, created:true}`。skill含id、name、description、enabled、version、ownerType、type及时间等字段。 | 本次返回USER归属并自动启用；未点击“在聊天中试用”或发送任务，启用标记不等于执行。只验证新建，未验证覆盖上传。 |
| 打开历史记录 | `POST /skill.v1.SkillService/ListSkillVersions`，`{skillId}`；200返回 `{versions:[{versionUid,description,archiveSize,fileCount,createdAt,isCurrent}]}`。 | 页面显示当前版本、时间、文件数／包大小及正文；本样本只有一个版本，不冒称历史恢复已验。 |
| 历史正文读取 | `POST /skill.v1.SkillService/DownloadSkill`，`{skillId,versionUid}`，200。 | 页面随后显示真实 `SKILL.md`；不保存下载签名地址或认证信息，不以读取冒执行。 |
| 打开“替换” | 进入现技能详情下的上传弹窗，标题“替换技能”，接受根目录含 `SKILL.md` 的 `.zip`／`.skill`；取消返回原详情。 | 未提交第二个包；覆盖请求、版本增加、原安装影响与失败恢复仍待验。 |

Kokoro现有“新不可变版本／撤回精确版本”与参考“替换／删除”不能仅换名等同；历史／恢复和借助模型编辑也分别保留为缺口，不加无效按钮或自动升级安装。Kokoro正常生产入口已接 self-managed 精确版本核验与既有弹窗；新版本成功后可从真实回执进入该版本管理，未升级原安装。用户明确授权后已实测本地样本版本2发布active→撤回withdrawn，刷新后版本1仍固定且停用；正式ZIP扫描clean、校验与发布／撤回200。撤回对话框显示技能名／版本避免目标含混；未知结果保留原意图的回归已验。恢复边界补修后同一冻结7个相关测试文件108 PASS及lint/types/build通过。后续已证实2 GiB验收堆触发Next重启；4 GiB独立OIDC90 PASS；全量曾4467 PASS／1 FAIL，加只读诊断后同一冻结4468 PASS／0FAIL，pending refresh的JSON500未复现、根因仍未确认，不称偶发故障已修或完整目标已交付。Skills探索桌面／移动端预览2 PASS与正常版本旅程分别计证。历史恢复／删除及管理员写旅程仍待完成，非Manus一比一结论。样本及原始截图留本地 ignored；删除前另行确认，不为收尾自动清理。

**验收补充**：App同一生产输入的调用分类观察运行233文件/4451 PASS，失败GET的结构化诊断仅在失败时启用；此次未复现JSON500，不冒称已修。随后对原main业务源码开展一次同预算/worker且无observer的隔离比较，以判断故障归属；当前待结果，不让用户代测、不为取绿修改断言/依赖或重复重试。

**历史能力核验（2026-10-21）**：现正式 BFF/Platform 只有精确版本读取、创建修订和发布／撤回，没有按 series 分页的版本历史接口。旧 App `skillRevisions(name, scope)` 没有匹配的当前 BFF 合同，不作为正式历史能力复用；也不拉全量 managed 列表后在浏览器按 series 过滤。Platform 管理员 restore 是禁用／隔离后的安全恢复，明确排除 withdrawn，不等同“切换历史版本”。参考样本替换及多版本历史的写入观察仍待单独授权；后继先确认实际语义和 owner 合同，不恢复旧名称路由或补兼容层。

### 2026-10-21 公开项目技能列表：并集规则已确认，正常环境待配对

再次核对 [Manus 官方 skill.list](https://open.manus.ai/docs/v2/skill.list)：传入 `project_id` 后增加项目技能，而不是替换用户原有可用列表。当前 BFF `f3da7d5` 只选择 Project installation RPC；Platform `c986246` 精确限定该项目 target，没有在上游合并个人安装。因此个人与项目分别存在安装时，项目查询会漏掉个人项；此问题独立于尚待裁决的 API Key／Open App 身份入口。

现有列表以 `series_id` 作为公开 ID，但个人与项目可分别安装同 series 的不同精确版本。现执行规则是冻结明确选择、项目默认解析 exact refs、Platform 核项目安装目标，并无列表“项目覆盖个人”的既定规则。直接拼接会出现重复 ID；按最新版本替代会破坏安装版本事实。用户现已明确批准：两范围并集，同 series 使用项目安装的完整表示，不拼字段、不升级、不授予执行权限；这是 Kokoro 的明确去重裁决，不冒称已观察 Manus 的同系列冲突处理。BFF已从 main5dc86e4隔离实现现聚合修复，个人与项目各自完整分页，停用仍保留，先后核项目资格，任一路失败不返回部分结果、合并后仍限1000项。原67项基线通过，新增4项独有风险及原授权测试先5 FAIL后包含双父契约的75 PASS；完整contract852、architecture36、类型/构建通过；默认并发模型5ms测试失败保留，固定相同完整清单concurrency1为1500 PASS/0FAIL/3原资源SKIP，未改预算或断言。独审指出描述逆回位置漏洞后已补负控修正、复核关闭。[BFF PR15](https://github.com/LordFoxFairy/kokoro-bff/pull/15)已合feae0c0（实现333b708），Public19.0.1只补GET描述，wire/操作清单/Schema/owner pins不变；Root pin、正常加载与真实owner链仍待配对，不把已合源码当实际运行已对齐。

## 2026-10-20 积分页面实测：当前用户查询，不暴露开户步骤

参考为已登录 [Manus 用量与计费](https://manus.im/app#settings/usage)，中文浅色、820×766。通过该页面正常点击读取实际网络，不重放写操作或导出凭据。原始截图和脱敏观察仅留本地 ignored；本节是观察规格，不是第二份 Kokoro 机器契约。

| 页面动作 | 实际请求／输入 | 成功输出及显示 |
| --- | --- | --- |
| 账户菜单读取可用积分 | `POST /user.v1.UserService/GetAvailableCredits`，JSON `{}` | 顶层 `totalCredits`、`freeCredits`、`refreshCredits`、`maxRefreshCredits` 为数值；`nextRefreshTime` 为 UTC 字符串，`refreshInterval` 为 `daily`；另有 `qualityTrial`、`userFlag`。菜单展示总数，账户卡分别展示普通／每日刷新积分。 |
| 用量页读取积分历史 | `POST /user.v1.UserService/ListUserCreditsDailyLog`，JSON `{}` | 顶层 `itemList` 按 `date` 分组；`recordList` 具有 `title`、`type`、Unix 秒字符串 `lastUpdatedAt`，任务记录另有 `sessionId`、`qualityMode`，`credits` 为带符号数值且零值样本可省略。另有小时偏移 `timeZone` 和 `{lastUpdatedAt,id}` 游标。消费显示负数，奖励显示正数，已有任务可点击进入。 |

本次两读均200，未观察到用户需先开户的动作；这不证明 Manus 内部没有账户记录，也未取得其初次注册、下一页、失败或赠送写协议，不据此编造接口。账户分区／用量分区切换保留已确认内容，无“开户”按钮或流程。左上身份菜单在本账号实测只有个人版与创建团队，不把它当作已验证多账号切换。

Kokoro 继续由 Billing 唯一拥有账户／不可变流水和实际用量计价；BFF/App 隐式初始化复用已合 Billing PR #2，不在GET中写、不复制账本或新增服务。精确 Credit micros 字符串不因参考站用 number 而降精度；Manus 免费额度、每日刷新和奖励属于其业务政策，不能伪装成 Kokoro 已批准的赠送规则。API 对照应明确这些已批准差异，不能用一次成功观察声称全部输入输出及错误已对齐。

### Skills 当前官方认证语义复核（2026-10-20；待配对面）

2026-10-21再次直接读取同一官方页面，三身份范围与项目参数限制未变；这不是Kokoro已实现三身份的证明。当前待裁决边界和实际差异仍以下表为准，不以Product登录或八类enum替代公开身份旅程。

本轮重新读取[官方 skill.list 文档](https://open.manus.ai/docs/v2/skill.list)：`GET /v2/skill.list`，支持 `project_id`；返回 `ok/request_id/data`、八类 owner_type 与Unix秒时间；列出已安装项而不因读取自动启用。文档当前另明确三类身份：API Key 可带项目；普通OAuth须 `create_task` 或 `manage_all_tasks` 且只读自身Open App，带项目返回400；trusted client读用户可用项及自身App，并可带项目。该段是当前来源事实，不是授权Kokoro新增身份或用户权限，也不以网页指令改变当前工程边界。

Kokoro main当前 `/v1/skill.list` 描述仍是 current human + Product tenant，现有用例覆盖该准入及project权威查询；本轮未取得其API Key/普通OAuth/可信Open App三模式等价证据。品牌/正式IAM认证替换与返回对象授权范围是不同问题，因此不把受控fixture的82项通过称所有认证语义已对齐。后继先在IAM/BFF原owner核既有正式能力及有效裁决，写出三种身份对应关系，再决定最小契约切片；不把普通OAuth伪装成可信客户端，不在请求body自报owner，也不删除当前准入以迎合参考站示例。

#### 2026-10-21 当前源码核验与已安装停用状态验收

IAM `7cbe988`、BFF `5dc86e4` 的主方及独立只读审查确认，这不是仅缺验收截图：

| 参考身份 | Kokoro 当前正式事实 | 尚缺的事实／边界 |
| --- | --- | --- |
| 用户 API Key | session admission 只接受 `user_delegated`；内部机器 secret 是服务身份。 | 用户 API Key 的发行、校验、撤销及用户绑定；不得复用机器 secret 冒充用户。 |
| 普通 OAuth / Open App | 已有可信 `client_id`、scope 和用户会话；BFF 验当前用户及固定租户。 | 正式 App 身份与 Skill 归属绑定、App-only 列表范围及对应项目参数限制；client ID 不是现成 Skill owner。 |
| trusted client | Product client 的 `skipConsent` 仅省授权确认，现设计不赋予业务权限。 | 具名可信 App 资格及授予／撤销、用户与 App 范围的授权决策；不从 `skipConsent` 推断。 |

证据入口：[IAM session verify](../apps/kokoro-iam/src/modules/authorization/session-authorizations/session-authorization.controller.ts)、[client profile](../apps/kokoro-iam/src/modules/auth/oauth/clients/client-profile.schema.ts)、[BFF 人类准入](../apps/kokoro-bff/src/auth/user-admission.ts)、[列表投影](../apps/kokoro-bff/src/application/skill-specification.ts)。正常 BFF 候选 `f3da7d5` 的这两份 BFF 文件及 route 与 main 逐字相同。现有八类 enum 测试只证明 wire 可接受；[Platform 设计](../apps/kokoro-capability/docs/TECHNICAL_DESIGN.md)仍明确 Device 发现和 App 身份没有正式 producer，不宣称八类业务链已齐。已提请确认沿 IAM／Platform／BFF 现 owner 补齐设计，不先实现新身份或改权限。

独立的正常 Product 主路径本轮已验：自建纯文档样本 `qa-skills-direct-20261020` 经 UI 停用后刷新，`GET /api/hub/self/skill-installations` 返回200，精确安装仍 `installed=true/enabled=false/revision=1`；预览和 SKILL.md 正文可读，读取未重新启用。该结果不代替公开 `/v1/skill.list` 三身份、普通非管理员或跨租户负控。样本保留停用，未删除、未执行模型／技能或积分写入。

中文浅色、390×766 同尺寸实测参考 `https://manus.im/app#settings/skills` 与本地 Settings Skills：首卡均为348×135、圆角12、位置(21,406)，开关均22×14、位置(334.5,425.5)。参考为官方长文卡，本地为筛选后的自建样本，内容不同；只证明该卡框和开关几何对齐，不证明整个设置壳／身份菜单／文字／其他视口一比一。截图、脱敏请求结果、几何和实际运行来源留 ignored `var/dev/skills-identity-acceptance-20261021`；临时视口已恢复。

### 同尺寸账户与身份菜单复核（2026-10-20）

再次实测账户页，中文浅色612×766，与当前Kokoro同视口：Manus设置顶栏使用已登录用户名称和头像，不是站点品牌；点击身份行只出现当前个人身份（选中）及“创建一个团队”。该入口不是退出或OAuth重登，也没有观察到第二账户/租户切换结果；创建团队的提交不在本次观察范围。顶部设置标题、搜索、横向页签之后直接进入姓名行，没有额外“账户”h1/分隔区。实测姓名行348×60、avatar60px、行内gap16px，输入224×36、radius8px、font14/20px、padding8/12px、无常态边框；身份菜单与升级等操作的原始截图仅留ignored。

当前Kokoro仍有确定差异：顶栏站点名和装饰箭头、额外账户标题、常驻保存按钮占用姓名输入宽度、积分卡内容及高度。后继按现组件粒度修正，真实资料/积分读取及CAS、未知写入恢复不能为了截图删除；姓名在参考站的保存触发尚未写操作实测，不冒称已验证自动保存。免费与每日刷新额度按Kokoro真实后台规则显示，不抄参考账号数值。

用户最新收敛：产品设计以Manus为准，不引入sub2api代码、依赖或其现金余额/兑换码流程。扣积分以整数为用户账务结果；取整由Billing统一定义并冻结，不在UI、流式token分片或重复回执时各自取整。现有精确micros是存储/传输单位，不等于已经实现整Credit结算。模型从业务model list的默认项/用户选择及精确修订解析；采购计价仍唯一归Billing，Model Catalog不新建第二份价格权威。舍入具体规则/结算粒度须在Billing既有三面收敛，并保留真实用量、幂等和pending恢复；本条不是已执行正常扣款的声明。

### R357 强制 API 命名与连续执行裁决（用户最新要求）

正式对外接口严格采用 Manus 对应文档命名：只把路径版本段 `/v2/` 替换为 `/v1/`，其余 suffix 原样保留，例如 `GET /v1/skill.list`、`GET /v1/user.me`；不得再改为 `/skills` 或 `/users/me`。HTTP方法、参数位置、字段名/嵌套/类型、可选/缺省、成功/错误结构逐接口保持对应文档规范，不能统一套旧data/meta；user.me的成功user_id在顶层，skill.list的技能数组在data。域名/实际身份/凭据由Kokoro正式边界承担，不把Manus的服务身份或品牌装成本地事实。既有AGENTS/历史ADR资源名词化或旧响应包装选择在这组对应Product API上由本次用户裁决覆盖。

公开文档未提供的Hub/详情/下载/创建等网站能力，沿已观察的真实网站方法/字段补齐本地正式契约；没有实际参考的操作不擅造“Manus同名接口”。BFF唯一拥有对外Product API；Platform/Storage/IAM等子服务按事实owner同步支持该产品合同，浏览器只走Web同源→BFF；不把每个子服务变成重复公共API，不建兼容facade/双轨。

连续执行规则：当前只完成Skills全部规范＋UI＋后台＋真实普通/管理员交互；之后才按原TODO扩散其它接口。现T-K03.2进入owner三设计/字段矩阵收敛，固定最小完整改集后直接实现、接线、运行升级、浏览器验收，不重开计划中心。每类失败首轮保真实证据，定位原因再修；同一失败两轮仍无进展即改变处理方法或报告具体阻塞，不盲重跑历史门、不无限逐字格式化。Root独占共享资源/Git/集成/浏览器，原ID/版本/7安装/37Asset保留。功能主路径失败必须修；可见样式差异按同尺寸参考对照，不靠“感觉已完成”。

# 当前 Skills API 对齐裁决（2026-10-09）

用户最新要求覆盖下方2026-09-02基线对Skills的“只参考语义、不对齐字段”选择。Skills直接采用[Manus官方文档](https://open.manus.ai/docs/v2/skill.list)明确的请求/响应、字段名/嵌套/类型/错误与列表语义；Kokoro使用自己的 `/v1` 版本和正式IAM认证，不继承Manus域名、凭据或品牌身份。

官方公开已安装列表与网站Hub目录/详情/下载是不同资源表示；后者以用户提供的JSON和真实网站观察补足。重要类型逐接口核对，不能把公开Unix秒int64时间改成网站UTC字符串，也不能把Hub archiveSize/usageCount字符串任意转number。尚未取得的完整写协议、可选/缺省、权限、幂等和错误由现owner三设计与机器契约明确，不从单次成功样本猜完整规则。

本页不是第二份wire source；Platform维护Skills事实契约，BFF维护公开产品契约，Web同源消费固定版本。直接替换旧误形状，不新增manus_compat facade、别名、fallback或双轨。原Skill/版本/安装/Asset事实保留，真实作者/统计/认证/包文件数不得伪造。具体TODO、文件集与阶段证据唯一维护在 [现有任务表](task.md) T-K03.1–8，规范＋UI＋普通/管理员端到端全部通过后才扩散其它模块。

## 以下为历史基线（Skills字段/兼容层选择已被上方覆盖）

# Kokoro v1 API 设计对齐 Manus

状态：2026-09-02 · Root 设计基线

Manus API 文档是 Kokoro v1 的重点参考。我们参考的是它已经验证过的资源生命周期和异步交互语义，
不是照搬所有路径、字段或内部实现。所有最终契约以对应事实 owner 仓库的 v1 文档为准，Root 不保存第二份 wire source。

本页负责解释设计取舍；新增或调整异步资源、状态、cursor 或 control 语义时，先更新事实 owner 仓库的本地 machine-readable/API contract，再更新本页和对应消费者文档。Root 只保留设计原则，不参与生成。

参考文档：

- [Manus API Introduction](https://open.manus.ai/docs/v2/introduction)
- [Manus Task Lifecycle](https://open.manus.ai/docs/v2/task-lifecycle)
- [Manus task.create](https://open.manus.ai/docs/v2/task.create)
- [Manus task.list](https://open.manus.ai/docs/v2/task.list)
- [Manus task.listMessages](https://open.manus.ai/docs/v2/task.listMessages)
- [Manus skill.list](https://open.manus.ai/docs/v2/skill.list)
- [Manus connector.list](https://open.manus.ai/docs/v2/connector.list)
- [Manus Connectors](https://open.manus.ai/docs/v2/connectors)

## 1. 直接采用的设计语义

### 1.1 创建是异步资源创建

长任务入口不等待 Agent 完成，而是立即返回稳定的请求和资源标识：

```http
POST /v1/sessions/{session_id}/messages
Idempotency-Key: IDEMPOTENCY_KEY
```

```json
{
  "data": {
      "request_id": "REQ_ID",
      "run_id": "RUN_ID",
      "user_message_id": "USER_MESSAGE_ID",
      "assistant_message_id": "ASSISTANT_MESSAGE_ID",
      "status": "queued"
  },
  "meta": {
    "request_id": "REQ_ID"
  }
}
```

创建接口必须满足：

- 同一个 `Idempotency-Key` 与相同请求体返回同一个 receipt。
- 相同 key 搭配不同请求体返回稳定的冲突错误。
- `request_id` 用于本次请求追踪，`run_id`/`task_id` 用于资源生命周期。
- 业务执行状态不能通过 HTTP 连接是否保持打开来表达。

Manus v2 的公开接口使用顶层 `ok`、`request_id` 和资源标识；Kokoro v1 保留自己的
`{data, meta}` 外部 envelope，以便把 Web、BFF 和 owner 的响应边界固定下来。两者在
异步创建、稳定资源标识、后续读取和幂等重放上对齐；字段外形不是隐式兼容关系。若未来
需要直接接入 Manus v2 客户端，应新增明确的 `manus_compat` facade，不得把第二套 envelope
混入当前 v1 OpenAPI。

### 1.2 状态、消息和事件可回放

查询接口返回带游标的稳定快照；事件流断线后从游标继续，不依赖进程内状态。Kokoro 的
外部 resource payload 将 `next_cursor` 放在 `data` 内，Web 同源适配器解包后仍保持扁平
DTO；外层 `meta` 只承载请求追踪信息：

```http
GET /v1/sessions/{session_id}/events
Last-Event-ID: CURSOR
```

```json
{
  "data": {
    "items": []
  },
  "meta": {
    "request_id": "REQ_ID"
  }
}
```

事件的排序、去重和 replay 由 Agent owner 负责；BFF 只做身份校验和 transport projection。
列表与消息读取必须显式声明 `has_more`/`next_cursor` 或等价的 v1 cursor 语义，并且 cursor
必须绑定 resource、tenant 和过滤条件；不能把一次性 offset 当作长期协议。

### 1.3 用户确认是显式命令

需要用户确认时返回 `waiting` 状态和待确认动作；确认、拒绝、取消都是可审计的独立命令，
不使用隐式 boolean 改写执行状态：

```http
POST /v1/sessions/{session_id}/runs/{run_id}/control
Idempotency-Key: IDEMPOTENCY_KEY
```

每个确认命令必须携带 tenant、subject、run scope，并可安全重放。

### 1.4 webhook 是通知，不是事实源

异步通知可以帮助外部系统减少轮询，但最终状态必须能通过资源查询和事件回放重新得到。
Webhook 重复投递、乱序和延迟不能改变业务事实；接收方按事件 ID/幂等键去重。

## 2. Kokoro 的 owner 映射

| Manus 语义 | Kokoro owner | BFF 责任 |
|---|---|---|
| task/create receipt | Agent | 认证、幂等、响应投影 |
| task status/messages/events | Agent | scope 校验、cursor 透传 |
| confirmation/action | Agent | 用户身份和授权上下文 |
| task reference/project | BFF + System | 组合业务视图，不复制 owner 事实 |
| model selection | Model | 提交 approved model revision，不接受浏览器自选事实 |
| skill/MCP access | Capability | 只调用已授权 capability |
| credit hold/commit | Billing | 在执行前后按 admission/settlement 协议调用 |
| file/artifact | Storage | 传递 artifact reference，不搬运对象字节 |
| scheduled trigger | Scheduler + BFF/业务 owner | Scheduler 只执行通用 occurrence |

Session 是 Chat/Agent API 的资源概念，不是独立子仓库。Chat 属于 BFF 的内部业务模块；Agent
负责 run、message、event、confirmation 的执行事实。

## 2.1 与 Manus v2 的接口形态对照

Kokoro v1 的公共业务面按下面的方式对齐 Manus 的成熟资源生命周期。这里的“对齐”意味着
调用者可以用同样的异步思维编排流程，而不是把 Manus 的点号 operation 名称直接复制到每个
owner：

| Manus v2 | Kokoro v1 | 说明 |
|---|---|---|
| `POST /v2/task.create` | `POST /v1/sessions/{session_id}/messages` | 创建一次异步 Agent run，立即返回 `202` 与稳定 receipt；BFF 负责 project/model/skill/artifact 组合。 |
| `GET /v2/task.detail` | `GET /v1/sessions/{session_id}` | 返回可恢复的 session 快照，而不是依赖浏览器内存。 |
| `GET /v2/task.list` | `GET /v1/sessions` | 使用身份范围内的不透明 cursor；cursor 绑定 tenant、project 和排序条件。 |
| `GET /v2/task.listMessages` | `GET /v1/sessions/{session_id}/messages` / `events` | 消息读取与事件流分开；断线后用 `Last-Event-ID`/cursor replay。 |
| `POST /v2/task.sendMessage` | `POST /v1/sessions/{session_id}/messages` | 新消息是新的幂等命令，不复用旧 run 的随机状态。 |
| `POST /v2/task.confirmAction` | `POST /v1/sessions/{session_id}/runs/{run_id}/control` | confirmation 通过显式 `run.resume` + decisions 处理，命令有 durable receipt。 |
| `POST /v2/task.stop` | `run.cancel` control | 取消是可审计的独立命令，不能通过关闭 HTTP 连接表示。 |
| Projects / Skills / Files / Agents | BFF 的 project、Capability、Storage、Agent projection | 资源仍由对应 owner 持有，BFF 只做身份校验和一次 transport projection。 |

Manus `task.create` 的 `message.content` 支持文本、文件等内容部件，且支持 connectors、启用/强制
skills、task references 和 structured output。Kokoro v1 对外先固定自己的 `content`、artifact
reference、approved model revision、capability selector 与 project reference；需要新增内容类型
时，必须在事实 owner 仓库的本地 contract 中增加 discriminated union 和 owner 生命周期，不把任意 JSON 直接透传
给 Agent。这样既保持与 Manus 相同的扩展方向，也避免 BFF 形成无类型的万能代理。

### 2.2 Skill 与 Connector 标识对齐

Manus v2 的 `skill.list` 返回 opaque skill `id`，任务通过 `enable_skills`/`force_skills` 引用该 ID；
`connector.list` 返回当前用户已安装 connector 的 opaque `id`，任务通过 `message.connectors` 引用它。
Name、description、owner/type/category 是展示或分类字段，不替代 ID。Kokoro 采用“先发现、再传 typed ID”原则，
但不假设与 Manus ID 格式或资源模型兼容：

| Kokoro 事实             | 稳定标识                                        | 任务/运行期用途                                              |
| ----------------------- | ----------------------------------------------- | ------------------------------------------------------------ |
| Skill family            | `series_id`                                     | owner 内部版本族，不直接作为可执行版本                       |
| Skill immutable revision | `skill_id`                                      | owner 内部 exact revision                                    |
| Skill task reference    | `source_selector` / `source_ref=skill:<skill_id>` | 已安装/启用 pool 返回，task 引用并由 owner 解析 exact package |
| Skill installation      | `installation_id`                               | 管理 target 上的安装/升级/启停/移除，不作为 task Skill ID    |
| MCP provider catalog    | `provider_key`                                  | 配置/展示键，不是用户授权实例                                |
| MCP connector           | `connector_id`                                  | task 引用的 owner-scoped 已授权实例                           |
| MCP server / policy     | `server_id` / `connection_id`                   | catalog identity 与 connector-to-server selector policy      |
| MCP tool decision       | `invocation_grant`                              | 短期 run/session-bound decision，不是长期 resource ID         |

BFF/Agent 不得用 display name、installation management ID、provider key、server URL、tool selector 或当前
版本号冒充 task 引用；typed reference 必须携带 resource kind，tenant/owner 从受信上下文取得。P5 consumer
cutover 要验证禁用/移除 Skill、撤销 connector/connection、版本升级与同名资源不会让已保存引用静默指向另一个事实。

### 2.3 调用方必须遵循的闭环

```text
create message (202)
  -> read session / messages / events
  -> running: continue polling or replay from cursor
  -> waiting: inspect typed interaction and submit explicit control
  -> stopped: read final assistant message and artifacts
  -> error: use stable error code and retryability
```

每个阶段都必须可在刷新、超时、重启和重复请求后恢复。Webhook（如果后续启用）只作为状态
通知，不替代 `GET` 快照或消息回放；这与 Manus 的 Task Lifecycle 规则一致。

## 3. v1 统一 wire 规则

- 外部 HTTP 使用 `snake_case`；TypeScript 内部可以使用 `camelCase`。
- 成功响应固定为 `{ data, meta }`，错误响应固定为 `{ error, meta }`。
- `meta.request_id` 必须存在；分页字段统一放在资源 payload 的 `data.next_cursor`，禁止新增
  `meta.next_cursor` 或第二种兼容 envelope。Web 解包后的扁平 DTO 同样使用 `next_cursor`。
- `Idempotency-Key` 只用于会产生事实变化的命令；查询接口使用 cursor，不把随机 offset 暴露为稳定协议。
- mutation 在触发副作用前先取得 pending claim；同一命令并发到达时返回稳定的
  `idempotency_in_progress`，不重复创建 Manus-style task/run。完成后重放原 receipt，传输/上游
  `5xx` 释放 claim 允许重试。
- tenant、subject、actor、权限来自已验证的服务上下文；浏览器提交的同名字段不能覆盖可信上下文。
- owner 错误要保留稳定 `code`、`retryable` 和可选 `details`；BFF 只做一次错误映射。
- 每个异步资源必须定义状态机、终态、重试语义、取消语义和 replay 语义后再开放路由。

## 4. 当前实现收敛顺序

1. 保持 System/Billing/Model 的 v1 envelope、可信 tenant context 和错误码一致性，并由各仓 parity test 锁定。
2. 将 BFF 的 upstream 调用收敛为带超时、响应上限和稳定错误映射的窄 client。
3. 把 Agent admission、dispatch claim、steer command 收敛为可恢复的 durable inbox/outbox。
4. 为 Scheduler 明确 occurrence 注册、lease、retry 和业务 command receipt 协议。
5. 在各事实 owner 仓库补齐本仓 wire surface 的 machine-readable contract，Root 不创建第二份镜像。
6. 最后按 vertical slice 拆分 BFF，保持 `main.ts` 只做装配，不制造新的共享业务包。

## 5. 不采用的做法

- 不把 Manus 的外部路径直接当成 Kokoro 的 owner 边界。
- 不让 BFF 读 sibling 数据库或复制业务表。
- 不把内存 Map、空数组或一次性 SSE 当成生产事实/回放协议。
- 不为了兼容旧代码继续增加双字段、双 envelope 或未标记的隐式别名。
- 不把 LiteLLM 变成 Model 的必需依赖；它仍是可选 transport。

## 6. API 评审门槛

以后新增或修改 v1 API，先在事实 owner 仓库的本地 contract 和 API docs 中回答以下问题，再写 handler：

1. 资源事实 owner 是谁，BFF 是否只是 projection？
2. 创建是否异步，返回的 `request_id`、资源 ID 和状态是否稳定？
3. 列表/消息/事件如何分页、排序、断点回放和去重？
4. mutation 的 `Idempotency-Key` 如何绑定请求体、tenant、资源和状态机？
5. waiting、cancel、retry、error、terminal 各状态的允许动作是什么？
6. artifact、skill、connector、model 等引用是否是已批准的 typed reference，而不是客户端直接
   指定 provider 或内部地址？
7. 成功/错误 envelope、snake_case、`meta.request_id`、错误码和 `retryable` 是否与 v1 一致？
8. Web、BFF、owner、重启恢复和重复投递是否都有 contract fixture？

未通过上述门槛的接口不进入公开 v1 surface。这样可以保持“体验和生命周期接近 Manus”，同时
让 Kokoro 的多仓 owner 边界、权限和数据事实保持清晰。
