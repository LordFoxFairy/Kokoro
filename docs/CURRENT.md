## BFF-CHAT-PAGING1：源码已提交，真实owner门通过（2026-10-01）

BFF main `88c54dbc1a67beba13c7bc159b7cb42cbb202ada`，Root唯一精准7路径提交；生产仅1行mixed-direction keyset修复。
原四候选doc495行完整保留，提交只含本片四前缀（40行）与source/test，不发布retry草案。414其他tracked文件保护，最终独立7hash review0/0/0；初评CURRENT过期阶段P1已按实测更新。public3.0机器contract/DDL/generated/scope/FIFO/retry不变，Web无需重发相同机器artifact。

Root实际RED：unit11pass/1fail；真实PG HTTP0pass/1fail明确漏tie_b/tie_c。GREEN unit12/12与Chat PG/Redis9/9；完整format/lint/typecheck/build、contract193/193、architecture27/27通过。第一次full547pass/1既定schema skip保留；fresh full提供同现PG实例/role自有fixture，548/548零skip，完整owner integration48/48（13.95s）exit0。静态可见集合时间ties/跨边界/limit1、2/末cursor与Project/tenant/subject/deleted/orphan均验，不冒称跨页更新snapshot一致性。

两Root自有临时DB正常回收，schema治理测试自身临时库亦finally回收；Redis未flush，3310仍PID65590。日志 `/tmp/kokoro-bff-chat-paging1-{red-unit,red-pg,green-unit,green-pg,full,full-real}.log`；manifest `/tmp/kokoro-bff-chat-paging1-final-manifest.json`记录working候选与committed7路径分别hash，draft不混发布。187条BFF committed来源已刷新，inventory仍3active/13broken；Root已精确暂存gitlink后执行checkpoint/topology，均PASS/exit0。完整 `python3 -m pytest scripts/tests` 当前实际1103通过/3跳过（125.84s）；3项明确需Agent .venv，用该Python独立补验3通过/52 subtests，不能把先前95项报告当当前完整Root门。fresh全仓标准审计仍FAIL：137项、0未核，按owner持续推进，不放宽门禁或称全部完成。日志 `/tmp/kokoro-bff-chat-paging1-root-{checkpoint,topology,governance,native}.log` 与 `...-root-standard.json`。

PG/Redis真实，IAM/Agent/Storage等外部HTTP仍测试double；未跑真实外部存储/provider/浏览器，不宣称全产品完成。ChatGPT回复区方案待确认；同会话terminal-gated FIFO、Agent4/原user retry、direct inbox语义及所有九owner/Wave0–7继续原目标，Billing最后。当前BFF/Agent/Billing仍有候选doc、Rootuv.lock任务外修改受保护，不称全仓clean。

## PLATFORM-IAM07-PIN：源码已提交，整体授权组合仍待验（2026-10-01）

Platform physical apps/kokoro-capability main `a77ad403095ae6314485e13298b7afa175932c8b`、13文件、clean；Root唯一提交，最终独立13hash/274保护终审0/0/0。正式IAM0.7来自clean e3c035b9的sdk:pack，archive3d9abf77/96entries；旧0.6包删除、manifest/lock只6+/6-IAM file pin，没有其他依赖升级。完整内外provenance/archive/package/dependency/lock三section/default importer门及28真实CLI用例；生产src/Prisma/Platform v5.0.1契约274hash冻结，两个现IAM method兼容，新增Skill authorization方法未消费。

Root fresh R3离线门 actual0：frozen offline install、format/lint/typecheck/checker、contract lint/read-check、execution artifact/cutover、Prisma/schema/test/build；102files pass/19skip、1224tests pass/243既定设施skip（6.96s）。日志 `/tmp/kokoro-platform-iam07-root-full-gates-r3.log`，最终manifest `/tmp/kokoro-platform-iam07-final-manifest-r3.json`。保留旧pin4fail7pass、Root wrong-section checker0、四section/default importer4fail24pass→GREEN、R2两个regex lint错误及未进入tests；Root独立原negative现exit1。没有ignore/放宽门、没有依据旧full绿误认返修通过。

这关闭的是SDK消费者来源漂移，不是live IAM/Product激活、同会话执行FIFO或整产品完成。没有真实IAM/PG/Redis/Storage/provider/浏览器，243设施用例未验；db:apply-schema未跑（Schema冻结），受管3310 PID65590未动。Agent/BFF/Billing候选docs/Rootuv.lock保护。Root刷新9条既有Platform committed来源并新增4项SDK证据（当前共13条），inventory继续3active/13broken，不把组件绿升级成实际能力。Root首轮集成未先暂存新gitlink，checkpoint/topology1、治理1fail/94pass（50.37s），历史日志 `/tmp/kokoro-platform-iam07-root-{checkpoint,topology,governance}.log` 保留；精确5路径暂存后两CLI fresh PASS/0，相关治理pytest95/95（50.94s）exit0，日志 `/tmp/kokoro-platform-iam07-root-{checkpoint-final,topology-final,governance-final}.log`；独立5路径审查0/0/0，不改snapshot/门槛。后继BFF direct会话列表与Project归属隔离/Agent4 terminal-gated FIFO继续依赖正式owner切片；retention与ChatGPT风格待回复，不缩小九owner/Wave0–7目标。

## PLATFORM-IAM07-PIN：进入正式消费者切片（2026-10-01）

上一goal turn为progress：Web34dc40c/Root865ba1fd已提交，提交后checkpoint/topology0；实际用户会话清单恢复，聊天重复与失败/重试交互仍未完成。整体goal不变。

当前Platform physical apps/kokoro-capability main6519ae9 clean，IAM e3c035b9 clean。Root正式Node24.20.0/pnpm12.3.4 sdk:pack exit0，0.7archive SHA256 `3d9abf77393944592d2fa32f5f67fe2aeda32cfc6995f7a021a414c7aecd4439`、96entries；内provenance contract/generator config/lock三个hash与owner committed blobs一致；IAM仍clean。Platform旧SDK checker0+15相关文件115/115基线0，日志 `/tmp/kokoro-platform-iam07-{owner-pack,baseline}.log`。src/Prisma/contract274文件冻结 `/tmp/kokoro-platform-iam07-protected-baseline.json`。

platform_iam07_owner(gpt-5.6-sol)当前只授权四docs门，Root管理Git/全部实际验收，未半切pin/runtime。并行只读bff_chat_role_owner交付terminal-gated FIFO方案：现Agent durable completed/cancelled/failed outbox足够，不需新terminal协议；BFF必须拆enqueue与release/expected registration、2xx不能释放下一turn，Agent仍加session防御fence。尚未源码实施或真实组合验证。retention与ChatGPT样式确认待回复，不靠该等待停止独立可执行工作；不重启3310，不触共享PG/Redis/provider。

## WEB-PROJECT-FLOW：源码提交与实际清单恢复（2026-10-01）

Web main `34dc40c0f92fb440dc241643b491cdc3e61f9f1c`，18文件、clean；Root sole commit，独立最终18hash审查0/0/0。BFF required string|null正式消费、null唯一终页、view显式映射、preview/fixtures同shape；项目loading/error优先，不改API/SQL/用户数据/模型。Root实际完整check contract219/architecture50/tests2064/163files/lint/typecheck/build exit0；preview Playwright14pass/4既定skip（13.7s），后置typecheck0，34117退出。

保留全部失败证据：最初9fail/113pass；第一fullcontract1/218（旧合法fixtures缺cursor）；R2–R4fulltest2fail/2062pass、定点3pass但整文件2/70，最终定位同文件共享ListClient in-flight。仅恢复用例使用独立稳定ListClient与finally恢复spy、没有timeout/retry/reset或放宽原snapshot/URL断言。最后整文件72/72和freshfull2064通过；日志 `/tmp/kokoro-web-project-flow-*.log`、冻结 `/tmp/kokoro-web-project-flow-final-manifest.json`。

受管3310 PID65590/parent65119未重启，四个独立职责窄patch通过旧hash门，原failure46文件未半切；backup/manifest `/tmp/kokoro-web-project-runtime-{backup,sync.json}`。Root真实tab6侧栏展开已显示会话清单，不再误报加载失败；截图 `/tmp/kokoro-web-project-flow-user-page.jpg` 仍明确显示重复user及旧失败/重试反馈，未称用户整体交互已修。没有收费provider/PG/Redis清理。

Root只刷新49个Web committed来源，inventory仍3active/13broken；Agent/BFF/Billing候选docs及Root uv.lock保护。总goal保持active，137研发规则缺口不因本片清零。下一关键链为同会话执行串行/正式原user retry与队列UX；用户明确喜欢ChatGPT风格，已提出中性色正文/紧凑操作栏/就近低干扰失败反馈，异步风格确认待回复。不能靠隐藏错误、过滤历史user或再生一次新消息来假闭环。Root实际集成复验：当前 w1e-iam07-bff-pin checkpoint PASS/0、topology PASS/0；治理 pytest 95/95（44.61s）。首轮 missing path、随后误选历史 platform-code-release 的4/12快照失败均保留，不修改快照或3/13状态。实际日志 `/tmp/kokoro-web-project-flow-root-{checkpoint-final,topology,tests}.log`；组合命令因历史checkpoint失败退出1，pytest本身95通过，最终正确checkpoint单独退出0。

### 执行串行审计：尚未实现目标队列（只读，2026-10-01）

已核Web machine.ts481–512运行中分支实际普通createMessage，而注释声称转steer；MachinePhase无queued。BFF当前dispatch FIFO仅等待HTTP admission回执（Agent outbox delivery），不是Run terminal；Agent现Schema只有per-Run lease/generation，未有session-active唯一约束。Redis通知不是现有会话锁。因此“同会话上一轮结束后下一轮执行”是明确目标，不是当前已验事实。

后继最高能力切片：BFF持久用户轮FIFO/terminal释放，Agent防御session active fence（沿retry4既有scope方案），Web后续turn queued与run.steer分离。真实PG/Redis验证A/B同会话只有A执行、A各终态B恰一次释放，跨会话A/X可并行；浏览器刷新/停止/重复点击不重复原user或Run。没有双扣款观测证据，不冒称已双扣，也不使用Redis锁/组件mock代替组合验收。

## WEB-PROJECT-FLOW：用户实际交互故障优先（2026-10-01）

| 项 | 当前任务卡 |
|---|---|
| 目标/Owner | 修复当前项目会话加载与状态投影，Web负责严格wire消费/界面状态，BFF仍唯一Conversation/Message owner；Root实际浏览器、验证、Git负责人。 |
| 基线/范围 | Web main e17c039 clean；Root main1f20be65。当前3310/tab6项目会话URL复现，不修改原用户数据。web_failure_wire_review只读cursor与项目状态审计；bff_chat_role_owner只读其他Chat/Project wire差异；bff_failure_contract_review并行只读Platform IAM0.7来源，未授权任何源码写入。 |
| 已复现 | 点击侧栏“重试加载”，GET /api/session/sessions?project_ref=...返回HTTP200、sessions=[]、next_cursor=null；Web sessionListSchema只允许optional string，合法响应进入catch/error。正文projectConversation提前return welcome又忽略loading/error，显示错误空态。不是Redis并发或CSS根因。 |
| 放置/选案 | 优先扩现src/contract/chat.ts、rail hook、现project workspace与相邻tests；淘汰代理临时删null、宽松unknown/fallback及新store。精确required/nullable须先核固定BFF committed spec；三设计文档收敛后tests RED再源码。 |
| 依赖/数据 | Browser→Web同源→BFF不变，无新SQL/owner/队列/角色；同会话用户轮串行，Redis协调但不替代DB幂等与执行身份。任务、项目、会话保持独立。 |
| 验证/交付 | 主树实际RED/GREEN、完整Web门、独立fixture与用户tab刷新/项目列表/已有会话回读；用户页未见正常前不称完成。冻结manifest、独立review、Root精准提交；运行副本仅经旧hash验证的完整职责切片更新，其他已发布failure合同不半切。 |

## 2026-10-01 下一owner Agent4：设计门具体缺口已定位，未授权重写

Web consumer/source片e17c039已由Root b1e53f91精确集成；提交后checkpoint/topology均PASS（`/tmp/kokoro-web-public3-postcommit-{checkpoint,topology}.log`），全goal保持active，137规则失败/真实整体能力待验未清零。

只读Agent审计已交6项实施前约束建议：retryable失败前profile freeze、scope latest/active与terminal协调时点、tenant/subject scope身份、native saver同事务写入+exact checkpoint、所有入口scope-first与generation/head fence、原Human与工具副作用边界。Root已读取当前三设计/Current的候选字段、native/retention边界，并核BFF TECH49–50/100–101明确复用原user、仅新assistant/run/outbox；未据审计报告宣称现代码已实现，后续逐项核源码。

Root锁死两条既有目标：retry绝不新建原user消息；四阶段只是实现切片，Agent4 artifact必须等全owner实现与真实PG/Redis/HTTP门通过再发布，不能先发布required字段而执行器仍旧。Agent四dirty候选doc与BFF/Billing/uv.lock仍原样保护。

Agent DATA_MODEL78–83/Current15明确retention释放未裁决会阻断完整文档门，不能用永久跳过purge假闭环。已异步向用户确认删除会话是否取消执行并清理执行记录/检查点（账本不含对话内容），这是研发契约/隐私生命周期，不是运维角色部署。尚未授权新DELETE API/旧数据兼容/共享数据清理；下一阶段先收敛已批准设计的具体约束与该生命周期决定。

## 2026-10-01 WEB-BFF-PUBLIC3 源码消费已验收；整产品仍未完成

Web main `e17c039c7e3a629e9815026206d08bcbcb4381bd`（16文件、clean），Root唯一提交；BFF public3精确committed blob与两角色消费已对齐，旧public2 pin删除，无fallback/alias。Root独立整份parsed spec只差version/role、owner bytes equality、Team15再生零字节变化；safe failure12tuple/guard/全部operation不变。Agent4/BFF3.1 retry未发布，不提前开放terminal mutation。

Root真实RED35通过/12失败→完整`pnpm check` exit0（contract219/architecture50/tests2055、41.02s、lint/typecheck/build）；完整preview Playwright14通过/4项目跳过、14.1s；后置typegen/typecheck exit0且next-env生成变化自动恢复，34117退出。两次冻结16hash独立终审0/0/0。日志 `/tmp/kokoro-web-public3-{red,check,e2e,final-typecheck}.log`，final manifest `/tmp/kokoro-web-public3-final-manifest.json`。

Root刷新Web48条evidence及Browser→Web owner contract共49个committed来源，inventory仍3active/13broken。首轮刷新脚本错误预期47而实际48，断言中断docs更新；随后checkpoint实际FAIL因遗漏Browser→Web owner旧gitlink，topology PASS；原log `/tmp/kokoro-web-public3-root-checkpoint.log`保留，现补齐owner commit/digest后重验，不放宽门。

这里关闭的是消费者source漂移，不是整条用户能力。未热切3310、改schema/用户数据或调用收费模型；用户输入内框和真实IAM→BFF→System→Agent→能力/Storage→Billing组合仍须验。Root本轮全仓标准仍137失败/0unverified；main-only实跑FAIL仅因候选及受保护BFF/Agent/Billing/uv.lock dirty，各head/local/remote仍main，不宣称clean。Root最终精确五路径集成checkpoint/topology均PASS，相关治理pytest95/95（47.15s），日志 `/tmp/kokoro-web-public3-root-{checkpoint-final,topology-final,governance}.log`；下一owner Agent4只读设计门已派 bff_chat_role_owner，代码写入未授权。继续按依赖闭环真实consumer与能力，不深挖部署运维。

## 2026-10-01 WEB-BFF-PUBLIC3 正式消费对齐进行中

上一goal turn是progress（Web9c428bf/BFF293dfe7/Root55dd9fa真实提交），本goal仍是九owner/Wave0–7研发+整体真实端到端，不缩小为单仓静态门。Root确认Web9c428bf clean、BFF原四份retry候选495行及Agent/Billing/uv.lock未动；沿同task卡续派Web sole writer及独立只读contract审查，Git/验证/运行由Root管理。

Root已独立核对BFF293dfe7 committed public3原字节digest acd92ed2fa3e84032e824e1462d67a007c4a94a7e79b7bda8fd5a66f9d51cd3b；旧spec仅version与role更新后整份parsed deepEqual PASS，operations/12tuple/presence guards不变。旧Web基线完整pnpm contract218/19files exit0，日志 `/tmp/kokoro-web-public3-baseline-contract.log`。Team15基线hash `/tmp/kokoro-web-public3-baseline.json`，owner blob `/tmp/kokoro-bff-public3-owner.yaml`。

三设计/contract README门已由Root读审；Team仅digest校验、failure version/provenance与Rootblob核commit边界已要求窄修。现授权七tests-only RED，尚未授权generator/snapshot；不新目录/依赖、不热切3310，不以pin或preview冒充真实产品/积分完成。全仓137失败及3active/13broken保留，下一阶段必须有实际RED再GREEN证据。

## 2026-10-01 研发闭环当前事实：Web/BFF两片已提交，整体未完成

用户重申边界：研发负责实现、契约/SQL、测试/build与真实端到端；部署运维配置后移，不把独立roles/GRANT/集群配置前置。
九owner总验收表在同一 `docs/task.md`，不新建第二任务中心。源码组件green ≠ 服务激活 ≠ 整产品完成。

- Web main `9c428bf8cfdbdafae1d0cc0c3ed807fa8defa591`（5文件、clean）：普通Markdown UL/OL marker在Thread scope恢复，literal GFM task-list排除免CSS Module哈希；Root真实RED→GREEN，最后完整Playwright14通过/4项目分工跳过（14.3s），完整check contract218/architecture50/tests2054（45.55s）/lint/typecheck/build exit0。真实390x620 overflow、wheel脱离/公开smooth回尾、tail不遮挡、48rem轴/两轮三gap；Root查看3PNG。独立终审0/0/0。日志 `/tmp/kokoro-long-thread-final-e2e-ol.log`、`/tmp/kokoro-long-thread-check-ol.log`；R2/R3/R4测试语义失败与GFM UL/OL RED日志保留，不通过删断言/加timeout掩盖。
- 受管3310仅本片6行CSS及属性排除窄sync，其余字节保存；backup/hash `/tmp/kokoro-long-thread-runtime-sync.json`，PID65590、首页HTTP200，34117测试退出，不改PG/Redis/user rows。用户tab6当前读取仍CDP超时，输入内框与实际整会话未验；既有failure源码没有半切激活。
- BFF main `293dfe7638e5dea0df2bee6dfdd8483b53fc9df6`（11路径自有片）：public3.0 pre-release同/v1 corrective两角色声明，SQL/domain/public/OpenAPI一致、failureguard/query/mapper/operation/pins不变。Root public真实RED35/2→提交后37/37；realPGschema6/2→8/8/0skip；完整check546通过/1动态schema跳过（PG另跑0skip）、format/lint/typecheck/contract/build exit0，独立终审0/0/0。日志 `/tmp/kokoro-bff-role2-{red-openapi,red-schema,green-schema,check,format-child}.log`。仅Root随机临时库，原应用DB不变，旧CHECK不被installer更新；source发布不代表3310激活。
- BFF原4doc retry候选495新增行保留（3.1目标对齐），通过commit-only快照选择性暂存，没有把未实现retry草案混入发布。Agent/Billing docs与Root uv.lock保护。Web仍exact public2 pin，下一片先精确repin已发布BFF public3，再做fresh真实组合；Agent4/BFF3.1原user retry尚未实现。
- 三仓只读来源盘点校正：Platform v5.0.1、BFF五项Personal API及Web同源/UI**源码已有**，不能再据旧inventory否认；开放项是当前真实三仓组合激活和Platform IAM0.6→owner0.7精确pin。库存reason已校正，状态仍3active/13broken，未假造Run或改门槛。
- Root当前默认全仓静态门**137规则失败/0未验证**（Agent5、Web12、BFF31、Billing33、Platform12、IAM30、Scheduler3、Storage11；System该门无失败），日志 `/tmp/kokoro-long-role2-root-standard.log`。这是代码目录/职责、TS严格性、API版本/owner标注与wire泄漏等研发缺口，不是运维；BFF test:architecture27/27并不等于Root标准31项通过。相关治理pytest95/95（73.93s）；最终精确6路径暂存的两gitlink/inventory组合checkpoint与topology均PASS/exit0，日志 `/tmp/kokoro-long-role2-final-checkpoint.log`、`/tmp/kokoro-long-role2-final-topology.log`。全仓137失败仍保留，未把这两片或库存一致性当成九仓研发完成。

Root集成复验：精确5路径暂存后checkpoint/topology PASS/0；相关治理pytest95/95（47.31s），日志 `/tmp/kokoro-composer-action1-root-governance.log`。3310公共首页HTTP200、原PID65590，34117测试服务退出；用户当前聊天像素/内框仍未验，3active/13broken不变。

## 2026-10-01 WEB-COMPOSER-ACTION1：实际操作行修复与渲染回归已验

Web main `42df17b8e3cd01d58c929cd83de1e2bc0b93e630`（6文件、clean）；唯一Root提交，writer agent_failure_cursor_owner，独立终审web_failure_wire_review P0/P1/P2=0/0/0。VoiceActions引用不存在CSS Module类导致宽屏发送组左靠，旧coarse reset又撤销auto；组内视觉归controls module，父级仅稳定slot定位，删除死/重复规则及coarse reset。无新组件体系、依赖、API、SQL或其他子仓改动。

Root独占34117真实preview填写/提交与PNG：桌面640右缘偏移386.8125px RED，触屏640偏移372.421875px RED；最终完整Playwright **13通过/3项目分工跳过（11.3s）**，desktop10宽度390–1280、Pixel7 390/640右缘<=1px，原轴线/overflow不放宽。Root已查看桌面全页/blur/Tab focus/三行与触屏640图片，操作组右靠。Node22/pnpm11 fresh完整check **contract218/architecture49/全test2053（40.79s）/lint/typecheck/build exit0**；日志 `/tmp/kokoro-composer-action1-{red,touch-red,final-e2e}.log`、`/tmp/kokoro-composer-action1-root-final-check.log`。首次check的257error/2773warning来自本轮generated HTML trace bundle；报告移出仓到/tmp后fresh全门通过，不加ignore/改门槛；原失败log保留。

Root仅把3个UI源码通过旧hash精确检查后同步受管3310，备份/manifest `/tmp/kokoro-composer-action1-runtime-{backup,sync.json}`；PID65590保持，34117测试服务已退出，无PG/Redis/共享数据操作。未混入46文件failure切片，未半切contract。用户IAB tab6再截图35s超时kernel reset；这不是UI根因。独立fixture textarea实测border0/shadow none、blur/focus/multiline未出现内框，但**用户当前输入内方框与整体对话视觉仍未验，不宣称用户问题全解决或整产品完成**。当前截图请求仍待回复。

库存刷新43条原Web来源至精确commit/blob，并加4个UI证据；仍3active/13broken。BFF只读后继P1：删除无producer的system角色是breaking，现version政策与同/v1 3.0候选冲突；fresh installer不会更改已有CHECK。尚未源码授权，避免分散UI关键路径。BFF/Agent/Billing docs及Root uv.lock保护。

Root集成门：精确暂存5路径后checkpoint/topology均PASS/0，相关治理pytest95/95（46.76s）；没有放宽broken状态、清理共享数据或包含其他子仓/uv.lock。

## 2026-10-01 Web失败消费源码已提交，用户视觉问题仍未验

Web main `8a2d771e5ed106f93473ac3d1b5efb793b9b32ab`，46文件自洽切片、clean；固定public2唯一tuple/profile严格消费、Agent/dispatch隔离与string seq、snapshot/live/Share安全投影，移除raw详情/terminal重发，只保留未receipt同key/body恢复；另修两条旧submission晚到污染新submission竞态。最终manifest2837a89046+9全部Root复核，13项有效guard mutation真实AssertionError并恢复；两个独立源码复审最后0/0/0。

Root Node22/pnpm11 fresh `pnpm check` contract218/architecture49/lint/typecheck/test2052/build exit0；最后仅新增same-session catch case，Root专属lint0+fulltest2053 exit0（43.76s）。不可删除的失败证据：该最后测试首次2fail/2051pass，均IAM /login内部csrf_status；原file隔离64/64、随后同源码full2053均通过，未加重试/timeout/预热或放宽断言，精确偶发原因尚未确定（不是已修复声明）。日志 `/tmp/kokoro-web-failure3-green-root-{check-r3,final-test,final-iam-isolated,final-test-r2}.log`。

Root库存仅刷新Web精确来源/digest与已验局部事实，仍3active/13broken；public角色漂移、正式retry与整产品组合继续留红。原3310运行副本未加载此46文件切片；Composer方框/全对话视觉仍最高用户未验项，不以这次source提交冒充可见UI修复。Root仅3台账/库存/gitlink集成，其他子仓候选与uv.lock保护。

## 2026-10-01 当前用户视觉问题：未闭合

输入内方框与整体对话布局仍以用户实际页面为准。Root与独立只读CSS审查确认：active thread覆盖到48rem、textarea源中border/shadow归零；受管3310对应Globals/Composer/primitive/AppFrame源码逐字节一致。Root初步704/768判断忽略了外层cascade，已公开更正，未据此改代码。IAB6截图/DOM/CDP均focus超时，已有tab13navigation超时，未新增重复标签；native Codex surface被明确禁止后即停止。当前截图请求待用户答复。源码/功能门不是视觉验收，禁止报告方框已修复、布局与ChatGPT对齐或整体闭环。

已有Web失败消费候选另行收尾：两项负例盲点与未读ref/注释已修正；追加真实旧submission晚到污染新submission竞态，RED2→GREEN68，身份绑定修正保留原key/body与late cancel。最终source门/manifest/独立复审待Root，用户视觉任务不由此清零。

## WEB-PUBLIC-ROLE-AUDIT 已核事实（2026-10-01）

只读固定BFF ccb8e144/Web daaf45b：SQL/schema/public读声明允许system，但唯一message INSERT只写user/assistant，其他writer仅更新assistant；Agent contract也只有两角色，无system产品producer/生命周期。Web只收两角色且其投影else会把system误当assistant，故不得为清门盲放宽parser。独立结论P0=0/P1=1/P2=0，具体证据见task后继卡；未查询运行DB，不能宣称没有历史/manual行。当前failure源片不扩角色。

Root后继方向：先由BFF owner删除没有实现职责的system声明，按现breaking政策发布SQL/types/public合同一致切片，再由Web精确repin，关闭角色漂移；如发现真实通知职责则先明确该通知owner/producer/Share安全语义，不暴露Agent内部system prompt。不在Root直接改子仓schema，不静默删除/改写运行数据。该P1继续使整体Web↔BFF edge待闭，failure局部green不等于完整public消费。

## WEB-FAILURE3-GREEN 已授权的必要边界补充（2026-09-30）

R4身份与unused清理独立已通过；审查提出的fail.showDetail测试引用冲突已归入GREEN迁移授权：原11tests不再要求字节冻结，必须保留行为/负断言，原tr(showDetail)改为无Collapsible DOM断言，不能保留孤儿key迁就测试。该P1不是新增设计阻塞，源码与测试在一个自洽切片闭合。

Root采纳只读审查的恢复capability：EngineSnapshot新增唯一只读 `canRetryPendingSubmission:boolean`，由现pendingSubmission+同session+合法error恢复态计算，不暴露body；AppFrame传给ConversationThread必填同名prop、Share显式false。Owner terminal与post-receipt SSE error均false，未receipt transport/credit恢复才true；不以runError=null盲目提供noop恢复，不新增endpoint/重试command。新增授权现tests/ui/app-frame.smoke.test.tsx只加post-receipt error无retry与未receipt能力接线回归；engine现tests在改源前toMatchObject验证true/false能力（不import未来类型，不靠类型错误RED），Conversation tests显式传能力。MainSurface/Shell只转conversationProps无需改。

追加devharness仅现src/dev/preview-transport.ts+tests/dev/preview-transport.test.ts：unknown !fail须在title/message.user/history等任何副作用前拒绝，不留下半轮；合法code从唯一generated/schema选择false profile，不建码表。原Thread raw detail相关state/ref/callback/props/effect依赖及CSS孤儿清理纳入删除责任，但errorCard几何ref如仍用于failureItem保留。四docs窄更新明确实现候选与未验组合。Root已读当前本仓Next use-client官方文档，无新Next API/依赖，三设计文档现方案可直接沿用。

## WEB-FAILURE3-GREEN 当前推进（2026-09-30）

R4测试身份/清洁已复验，Root126fail/194pass（真实行为RED、0collection）、lint/typecheck通过、engine/UI恢复各2通过。精确源码任务与追加恢复capability放在 `docs/task.md` 顶部同一任务卡，不复制成第二计划。唯一Web writer已获phase3+4源码授权；本轮不切换运行组，不将即将实施代码当成完成证据。独立wire审查 `/root/web_failure_wire_review` 已启动，模型gpt-5.6-sol，只读published owner/方案，冻结后再审candidate；工程审查bff_failure_contract_review，Root主树验收与sole Git。

## GOAL 续推：WEB-FAILURE3-RUNTIME-RED R4 → 正式源码消费（2026-09-30）

上一turn为progress：Web daaf45b两文件真实源码修复、Root 3d3589e9组合提交，UI131/131、architecture49/49、typecheck/build与提交后checkpoint/topology PASS。内方框和整体视觉仍开放，未以局部green缩小全goal。

当前Root main3d3589e9/Web maindaaf45b；Web原11测试候选及其他子仓docs/Root uv.lock保护。唯一writer agent_failure_cursor_owner，审查 bff_failure_contract_review只读，Root sole Git与主树验收。R4仅tests/engine/event-reducer.test.ts统一tool/dispatch/machine的run_id=run_1，及tests/ui/conversation-failure.test.tsx删除失效unused消息参数和对应调用值（不加lintignore或void掩盖）。不改断言/测试集合/producer/源码；交新9hash/2protected，真实8文件RED、typecheck及精确2未receipt恢复。独立清零且Root复验后，进入既有TECH phase3+4同一类型闭合切片；源码授权另发，当前仍无源码写权。

## WEB-COMPOSER-RHYTHM2 源码已验，视觉仍开放（2026-09-30）

Root组合验收：首次未暂存gitlink时checkpoint/topology均exit1（来源新SHA与旧index不一致，日志保留），精确暂存上述5路径后两CLI fresh PASS/0；日志 `/tmp/kokoro-web-composer-rhythm2-root-staged-{checkpoint,topology}.json`，不放宽门禁。

Web main `daaf45b132e30fe5bff3ee9a3234363b5be3d12d` 两文件窄片已提交：max960 active form padding由1.7/.85/.3修为.7/.85/.6，删除重复顶部留白；不改内框、焦点、宽度、controls或消息状态。独立终审P0/P1/P2=0/0/0，Root同树UI131/131、architecture49/49、owned test lint、typecheck、build实际exit0，日志 `/tmp/kokoro-web-composer-rhythm2-root-{result.json,typecheck.log}`；不冒称全lint通过（冻结failure test既有unused warning）或完整test/E2E通过。

Root核runtime原CSS精确等于daaf45b父commit，后仅同步该文件到原3310受管副本，hash513b1f4a；没有重启/新服务/provider/数据操作。源码热同步不是当前画面证据。CUA tab6焦点读取31秒超时；当前输入方框、整个对话视觉和真实浏览器E2E仍未验，截图请求待答。以下任务仍开放，不把此padding切片宣称整体布局闭环。

failure R3仅测试仍冻结：Root9/9hash、8files126失败/194通过、0collection（1.77s），日志 `/tmp/kokoro-web-runtime-red-root-r3.log`；独立审查仍有dispatch tool run-1与terminal run_1不一致的1P1，source GREEN未放行。原11候选hash保留，其他子仓候选/Root uv.lock保护。

## 用户优先：WEB-COMPOSER-RHYTHM2（2026-09-30）

用户再次指出输入方框与整体对话布局，Root切回UI关键路径，不继续让failure测试返修占据可见验收。当前Root main c8d71517/Web main3c4e739；原runtime候选11路径冻结，唯一writer先收尾一个dispatch测试身份修正，然后交接同仓局部UI切片。所有其他仓未提交变更、Root uv.lock保护。

| 任务卡 | WEB-COMPOSER-RHYTHM2 |
| --- | --- |
| owner/writer/review | Web AppFrame响应式Composer外壳；agent_failure_cursor_owner唯一writer，Root主树复验；原failure审查只读并行 |
| 当前事实/职责 | src/ui/composer/composer.module.css为编辑器本体；AppFrame max960规则以更高特异度把active form padding改成1.7rem .85rem .3rem，覆盖coarse≤640组件0.7rem；不改消息/契约/交互 |
| 局部范围 | 仅src/components/blocks/app-frame/app-frame-main.module.css及tests/ui/app-frame.smoke.test.tsx；扩展现文件，不创建目录/组件/协议，不把重设计塞入本片 |
| 方案与粒度 | 改现max960 form padding为紧凑0.7rem .85rem .6rem并更新过时注释；不追加更高特异度补丁，不改宽度/底部safe-area/焦点/多行增高/controls |
| 依赖/数据/删除 | 仅现shell CSS；无schema/API/generated/SQL变化；删除过量上留白与错误参考注释，不删除键盘focus保障 |
| 验证 | TDD先锁原1.7rem失败、再同测试绿色；Composer/AppFrame相关unit、architecture/lint/typecheck；完整test目前含冻结failure RED如实保留，不清门；浏览器当前读取超时，未视觉验收 |
| 排除/交付 | 不改Composer/primitive/Thread/消息样式/原11候选/子仓docs/依赖/运行副本/服务/Git；Root sole commit。内方框根因仍未确定，当前截图请求待答，不将padding修复冒称方框修复 |

新鲜UI证据：CUA inventory返回当前tab6，getTab实际Emulation.setFocusEmulationEnabled超时31.36s；未新建tab、未重启/绕过。受管3310 PID65590存在，源码五文件（Composer CSS/TSX、AppFrame CSS、Thread TSX、Textarea primitive）与主树逐字节相同，排除这些文件未同步这一假设；不证明浏览器CSS实际生效。当前回归仍优先真实画面。

## 当前goal：runtime RED已Root真实复现，R2仅测试返修（2026-09-30）

Root mainc8d71517/Web main3c4e739；新九候选R1 hash9/9及原两contractRED保护复核。Root Node22 fresh typecheck0，定点8文件114失败/190通过，0collectionerror，日志 `/tmp/kokoro-web-runtime-red-root-final-{result.json,red.log}`；40188已终态消费。未receipt初始筛选3项通过含2恢复+1双发guard，不称全engine通过。

独立R1发现Share精确copy、dispatch工具/历史run、profile快照阻断、generic原user retry四P1测试缺口；Root补creditRejected为admission失败的边界裁决，保留其三独立动作与冻结意图恢复，不与owner terminal混淆。R2只同九tests返修，生产/生成/docs/Git/服务无worker授权，源码GREEN尚未放行。机器切片已验不等于runtime/UI/全产品完成。以下为历史门记录。

## 当前goal：Web机器切片3c4e739已提交，runtime门继续（2026-09-30）

Root基线main8a3940fe，Web main `3c4e7394ce5219906530d5077a3ae163c2b1c0fc`。Root已精确提交18 pin/generator/provenance/docs路径，两runtime RED未纳入；新鲜完整结果为artifact46/49architecture/lint/typecheck/build通过、fulltest26失败/1928通过，失败仅两冻结runtime文件。日志 `/tmp/kokoro-web-pin-release-root-result.json`，两generatorcheck及owner原blob/Team15逐hash也通过，独立release0/0/0。不能据此声明运行时失败消费或产品闭环完成。

库存38Webrefs/6来源hash已更新，新增2单源artifact证据；3active/13broken不变。后继runtime RED仅9既有tests，见task；生产/source GREEN另授。当前UI只读审查确认coarse≤640输入外层1.7rem覆盖内部0.7rem的几何冲突P1，实际方框/全布局仍须当前页面证据，不在本次机器切片改CSS。未热同步3310、未启动服务或访问模型/PG/Redis/积分；其他仓候选及uv.lock保留。

Root主工作树相关治理88/88（47.00s）及current checkpoint/topology CLI已新鲜actual0；日志 `/tmp/kokoro-web-pin-root-{governance.log,checkpoint.json,topology.json}`。runtime下一RED基线8test files228/228通过，唯一writer仅授9tests、生产零授写。全Root tests/完整标准/组合/browser本轮未执行，不把来源检查通过包装成产品全部闭环。

Root组合main已提交56ee865a，提交后checkpoint/topology再验PASS；本轮终态句柄均已消费，无残留验证进程。下一9tests首轮107失败/197通过但12类型错误，仍草稿、未通过RED门，writer返修真实typed入口中；原两contractRED仍冻结，Root不称当前变化树全量通过。机器切片、runtime消费与UI验收是三个不同状态。

## 当前用户优先：输入框与对话布局尚未视觉验收（2026-09-30）

Root main `8a3940fe`、Web main `399f863`；当前18机器候选+两runtime RED未提交，生产聊天UI未新修改。现有IAB tab6读取实际焦点命令超时31秒，当前页面画面缺证据；只读负责人核级联/布局，不重启服务或重复添加CSS补丁。历史图片、源码断言均不作为用户当前方框的已修证明。

机器候选Root最终实测artifact46/46、architecture49/49与lint/typecheck/build通过；完整测试26失败/1928通过，runtime消费者仍未实现。日志 `/tmp/kokoro-web-failure3-pin-generator-root-final-quality-result.json`。当前输入框/整体视觉、运行时consumer、完整浏览器E2E仍开放；保护其他仓候选及uv.lock。以下为历史阶段记录，以本段及当前task为准。

## 当前续推：Web failure consumer 设计与真实 RED，UI 未闭（2026-09-30）

基线 Root main `d88ca38b7bff200875e7535e4378232f741f70fc`、Web main `399f863277f6b62e42772042bc940c62f33dc724`、BFF已发布 `ccb8e144` public2.0；Web机器pin仍1.0。本片只产生Web四docs候选和两个现contract测试，不改任何生产源码、生成物、运行副本、服务、数据库、provider或积分。

Root先跑两目标40/40和四相关70/70保留行为基线；再在主树复现最终RED：两文件126项=26目标失败/100通过、0collection/import error，actual exit1。12合法Message与12合法Agent RUN_ERROR被现strict schema拒绝，合法dispatch string seq/source_owner也被拒；旧failureless Agent RUN_ERROR却被接受。这些是当前consumer真实缺口，不是已修成果。日志 `/tmp/kokoro-web-failure3-root-{contract-baseline,behavior-baseline,red-r2}.log`。负例绿可能只是旧schema同因拒绝，不能宣称各守卫已经证明；GREEN后须mutation。

唯一Web writer agent_failure_cursor_owner、只读契约/测试审查 bff_failure_contract_review；Root重跑并实核冻结hash。四docs741c2182/4a9b3a52/720cde07/4f87fc92，两个tests2fbb79a7/14ce463e；设计R1 dispatch身份/code/message漏项和测试R1旧正例冲突已窄修，最终各0/0/0。严格区分Agent安全三键与BFF opaque dispatch，不Number化BIGINT，不展示raw异常，不把terminal重发user冒充正式retry。public system role现consumer drift仍开放。下一pin/generator阶段尚未授权，正式retry仍等Agent4/BFF2.1及生命周期门。

当前UI复核没有发现所谓48/44宽度缺陷：active AppFrame更高特异度会覆盖组件默认44rem；禁止凭局部CSS误判而再加补丁。输入方框根因与真实桌面/窄屏视觉仍未验。原tab6一次读取实际焦点命令31秒超时，未新开tab或换工具绕过，当前截图请求仍待答。既有bounding-box Playwright本片未运行；不以contract RED或历史1846测试代替用户可见页面验收。

整产品/Wave0–7未完成，历史完整标准137FAIL不清零；Agent/BFF/Billing docs候选与Root uv.lock保护。Web六文件保留为未提交下一实现切片，Root本片只记录任务/进度，不更新gitlink、不发布半套协议。

## 当前UI：短线程滚动源码切片已验，输入内框仍开放（2026-09-30）

Web main `399f863277f6b62e42772042bc940c62f33dc724` 精确四文件已提交、clean。已删仅两项/只量末项的 compact 判断；现在只在 settled、非重连/HITL/详情展开，所有实际项（含成果/失败）的跨度与双层 padding 真正 fit 时清 native spacer。ResizeObserver+rAF 合并、无反向跳尾，卸载清理。Composer/CSS/消息/契约/SQL未改。

Root 最终源码/测试哈希复核，HEAD 原生产配最终测试 RED5失败/37通过；最终完整 `pnpm check` actual0：contract109、architecture49、1846全量（45.14s）、lint/typecheck/build。独立最终0/0/0，HITL用例P2已窄修并mutation RED。证据 `/tmp/kokoro-web-compact-geometry-root-red.log`、`/tmp/kokoro-web-compact-geometry-root-final-check.log`。Root 相关治理测试18/18（20.65s）actual0，日志 `/tmp/kokoro-web-compact-geometry-root-governance.log`；仅在核原aacd baseline后同步原3310单个Thread文件，无重启/provider/数据操作；源码同步不等于视觉验收。

当前用户输入框方框仍未定位，fresh桌面/窄屏视觉与完整Playwright未验。IAB tab6焦点读取超时；native Codex app读取被工具限制后停止，未绕过。已请求当前截图标框。不得声明整个对话体验、登录或产品E2E完成。Agent/BFF四docs候选、Billing五docs与Root uv.lock继续保护；正式retry仍有lifecycle前置，全goal active。

原生retry R4实际PG spike11/11（含两native HITL）通过，自有fixture已回收、cleanup_errors=[]；证据 `/tmp/kokoro-retry-native-pg-spike-r4-result.json`。仅证明native库实验，不证明生产Run/lease/HTTP/provider/browser。双方R2新契约/SQL缺陷已闭，retention/activation未决，无源码授权。

## 当前输入框与对话布局：源码局部修复，视觉未验（2026-09-30）

Web main `13b881d242b59d23e18c0b0cd4f5fcb266cb3d60`，四文件切片已提交、工作树clean。已删除AppFrame首Item正负margin补丁，恢复content统一1.75rem gap；viewport继续拥有顶部留白。原测试锁定错误首轮几何，已改为禁止首Item补丁。独立冻结审查0/0/0；Root显式Node22.22.2/pnpm11.25完整check exit0：contract109、architecture49、全量1836（41.01s）、lint/typecheck/build。日志 `/tmp/kokoro-web-uniform-turn-gap-root-node22-check.log`。首次误用Node24的自有检查已精确终止并消费143，不计通过；worker任务外导航首次超时保留，随后两次70/70。

Root只同步原3310受管副本单个CSS，更新前确认其bytes等于8205基线，更新后确认等于已审源码；无重启、模型调用或数据修改。当前IAB inventory成功、tab6绑定仍实际20秒超时；已请求fresh完整截图标出内框。**输入方框、完整桌面/窄屏视觉和滚动仍未验收，完整Playwright未执行**；compact两项限定/末项几何启发式的另一P1保留，不再以源码测试冒充页面通过。

后端retry的Agent/BFF各四docs已freeze待审，没有新源码或机器契约发布，不算本次UI成果。Root保护这些候选、Billing五docs与uv.lock；全goal继续active，整仓/产品E2E未完成。

## BFF-AGENT-FAILURE3：owner源码已提交，组合待闭环（2026-09-30）

Root组合提交 `8ed71e9e211c1e6ca1504aaa67df18a122b11545` 后，strict IAM relay、指定current checkpoint与topology三CLI实际PASS/exit0，均已完成且无待消费进程。日志 `/tmp/kokoro-bff-failure3-root-final-{iam-relay,checkpoint,topology}.json`。原提交前HEAD/index差异exit1保留作阶段证据，未改门。Root全量1103passed/3skip结果仍绑定同一源码/来源；Billing五docs与Root uv.lock继续保留。整个goal仍active，Web消费与正式原user重试是下一条关键链。

BFF main `ccb8e144d72e35d90f9edc23f8b3ed0c82fde98d`，clean，Root精确33路径（32现文件+旧HTTPvendor删除，Git显示32changes含rename）提交。
Agent HTTP3.0/provenance exact2与17 deterministic生成、strict10false/2true、Message两列完整CHECK、同TX失败事实与safe snapshot/list/Share/标准RUN_ERROR闭环；无旧七码fallback/HTTP双vendor。独立契约/SQL及四docsmetadata最终0/0/0，schema-extra约束与Share/GC两个测试盲点本片已修而非延期。

Root Node22/pnpm11.25最终format与完整check exit0：contract193/193，主545pass/0fail/1schema-fixture skip，lint/typecheck/build；在自有随机DB、复用同PG/Redis/role且原子claim Redis15，fresh canonical install、动态schema7/7、architecture27/27、全部七integration47/47（14.08s），0skip。实际旧RUN_ERROR GC后snapshot/list/有效Share保留同safe profile已执行，当前active Share撤销拒绝也核；上游服务/模型仍double，不称真实owner/provider/browserE2E。

证据 `/tmp/kokoro-bff-failure3-root-final-{format,full-check}.log`、`/tmp/kokoro-bff-failure3-root-real-acceptance-r2{.log,-result.json}`。run f1db3932a3edbe3f195580f1 source/tests前后hash稳定、DB残留false/fixture增量[]/Redis15keys0/cleanup[]，独立残留probe也0；Root仅最后四docsmetadata改动，其他28entries仍c12ced8d冻结bytes，release manifest `/tmp/kokoro-bff-failure3-root-final-release-manifest.sha256`。

Root来源库存184个BFFcommit refs/10 digest更新，新增3固定Agent3来源证据，public owner2.0，但Web仍public1；edge仍3active/13broken、不转绿。指定current checkpoint与topology已经实际exit0。strict IAM relay提交前暂exit1仅Root HEAD/index新gitlink不同，需Root提交后原门重验；main-only列出的所有本地/远端branch都是main，但整门exit1因Root/Billing未提交变更，保护Billing五docs/uv.lock，不称整体clean。

完整工程标准门仍FAIL137（BFF31），未放宽；Root完整治理tests1103passed/3skip、119.19s、exit0，日志 `/tmp/kokoro-bff-failure3-root-governance-tests.log`。Web consumer2、正式原user重试、fresh输入框视觉、运行组协调/真实E2E与其余Wave0–7仍开放，Payment最后。3310未重启/无半套热切，provider/积分未操作。

## WEB-EMPTY-FAILED-TURN：源码与运行副本同步，视觉未验（2026-09-30）

Root 本轮相关治理测试47/47（40.73s）实际通过；指定w1e-iam07-bff-pin checkpoint与topology CLI均exit0，strict IAM relay仍exit1，准确原因为BFF工作树候选dirty，未清理候选/放宽门。完整Root测试、完整标准门、Playwright与fresh输入框视觉本轮未执行。日志 `/tmp/kokoro-web-empty-failed-turn-root-{governance.log,checkpoint.json,topology.json,relay.json}`。

Web main `8205fa003d5ea269741df359d4d6881dd0f1e0f8` 精确四文件提交、clean；仅把严格终态空assistant与原失败反馈归同原MessageScrollerItem，保留article/run/message事实、普通/credit动作、详情与query hook，无CSS负margin/隐藏/去重。Root Node22完整check实际0：contract109、architecture49、1836tests（40.87s）、lint/type/build；独立四hash审查0/0/0，Root HEAD组件RED2失败/30通过→恢复候选GREEN。日志 `/tmp/kokoro-web-empty-failed-turn-root-{red,check}.log`。

仅原3310受管副本一个ConversationThread文件核f958baseline后逐字节同步，无重启/新进程/provider/积分/数据库操作。当前浏览器tab6焦点与selected13截图实际超时；fresh页面间距/输入框方框仍未验，已请求截图，不宣称整体UI完成。库存38Web commit引用更新、0contract digest变化；BFF R3纯REDRoot70pass/38fail/33infra skip，契约1P1旧testvendor路径与SQL1P2空白code负例已派R4，不授GREEN。Billing五docs与Root uv.lock保留。

## WEB-FAILURE-FEEDBACK-FLAT：源码通过，当前内框与视觉未验（2026-09-30）

Root本轮治理：指定当前 `w1e-iam07-bff-pin.json` checkpoint与topology实际0；相关Root治理tests88/88（47.08s）通过。误选历史platform-code-release checkpoint首次exit1（历史4active不同于当前3active），已保留原日志并改用既定当前checkpoint，未修改任何门。strict IAM relay仍exit1，原因BFF四docs候选dirty，未stash/放宽或冒称全组合绿。日志 `/tmp/kokoro-web-failure-feedback-root-{topology,checkpoint-current,relay}.json` 与 `-governance.log`；本轮完整Root/全标准/Playwright未运行。

Web main `f9587ac9a008c7183b875e096be504fb5c0b69ef` 四文件精确提交、clean。Thread失败反馈由固定48rem圆角阴影卡改为内容宽度透明无外卡反馈；保留shadcn Alert/标题/详情/动作与全部Message事实，未改Composer。Root显式Node22完整check实际exit0：contract109、architecture49、全量1825（41.43s）、lint/typecheck/build；独立冻结审查0/0/0；主控HEAD CSS复现RED1失败/20通过，恢复候选GREEN21/21，日志 `/tmp/kokoro-web-failure-feedback-root-{check,red,target-green}.log`。

仅精确核HEAD baseline后同步受管3310原进程的Thread CSS，未重启/模型/计费/数据库操作。本轮CUA user tab6两种正式绑定均焦点超时，无fresh截图；输入框用户所见方框仍未定位，桌面/窄屏视觉与全Playwright未运行，不称整体对话体验完成。库存38个Webcommit引用更新，0个digest变化；BFF R2四docs契约/SQL独立复审均0/0/0，仅文档门不代表实现；Billing/uv.lock保留不提交。

## WEB-CHAT-CURRENT-FEEDBACK 源码门通过，视觉待验（2026-09-30）

Root组合CLI实际结果：topology=0、指定checkpoint=0；strict IAM relay=1，准确原因是保留的BFF四docs候选使child worktree dirty，未stash/回滚候选或放宽门禁。三日志 `/tmp/kokoro-web-chat-current-feedback-root-{relay,topology,checkpoint}.json`。本轮未跑全Root治理测试、全标准门或完整Playwright；Web纯门通过不代表这些门通过。

Web main `5b77798be7a407c3f0a82d47841f1e141021de02` 四文件精确提交、clean；删除11行按message ID后缀施加全用户正负margin/translate的错误规则，保留AppFrame首项几何、消息/重复事实、Composer和失败卡。Node22主控完整 `pnpm check` actual0：contract109、architecture49、全量1823（39.18s）、lint/typecheck/build；独立4hash审查0/0/0。Prettier四文件及HEAD基线均FAIL既有格式，不宣称全部格式门绿。日志 `/tmp/kokoro-web-chat-current-feedback-root-check.log`。

仅受管3310 PID65590目标Thread CSS逐bytes同步，无重启/模型/积分/数据库操作。本轮IAB含原user tab6的读取/截图均超时，fresh desktop/mobile视觉、当前输入框与失败卡观感尚未验收；已请求用户刷新并提供当前图。历史65e输入框矩阵不代替本轮证明。来源库存38个Web引用指向新commit、0digest变化，3active/13broken不变；BFF四docs候选仍有独立3P1/2P2未放行，Billing五docs与uv.lock保留。目标仍active，不称整体ChatGPT/Manus体验完成。

## Web 输入框与空成果项当前组合（2026-09-30）

Root五项冻结来源下relay/checkpoint/topology三个CLI实测PASS/exit0。topology首次在gitlink暂存前exit1（checkout与旧记录不一致），精确暂存后原门通过；未修改门禁。日志 `/tmp/kokoro-web-visual-current-root-{relay,checkpoint,topology-final}.log`。本轮未运行全Root治理测试、完整Playwright或标准全门；历史结果不作本轮重跑。

Web main `65e328755774080fc37a4d12d2b9f9b2e21a22bf` 七文件已精确提交、clean。Root最终Node22 check109/49/1822（37.72s）/lint/type/build actual0，独立R3 0/0/0；真实触屏失焦/聚焦、默认桌面、390px、多行和高对比通过局部修复验收。继承primitive内shadow与forced透明outline被系统着色两种内框均修；成果null不留wrapper。消息全文逐项exact不变，重复user/历史failed仍未闭，不称完整ChatGPT/Manus体验。自有runtime仅两源码同步，无重启/模型/数据改写，override恢复。完整Playwright、本轮全Root1103与全标准门未执行；后继BFF失败持久化/同user retry继续，支付最后。日志 `/tmp/kokoro-web-visual-current-root-r3-check.log`、矩阵 `/tmp/kokoro-web-visual-current-real-matrix-r2.json`。Root保护Billing五docs与uv.lock，来源库存仍3active/13broken。

下面bef68与f3be切片保留为历史验收，Web来源现由65e3287后继；Agent/BFF来源未改变。

## 本轮Composer焦点与Agent粒度切片已验收（2026-09-30）

Web main `bef68a0386a902bbe4747c5795d8222d1d91fa51` 4文件精确提交、clean：内框保持移除，shell深border/3pxhalo双圈改为单2px环，forced-colors系统色outline保留键盘指示。Root显式Node22最终check109/37/1800（44.86s）/lint/type/build actual0、独立0/0/0；日志 `/tmp/kokoro-web-single-focus-root-r2-final-check.log`。真实IAB鼠标/Tab/blur、390px/1280px与forced-colors均检查，默认媒体/viewport恢复、article全文严格相等；现3310仅同步自有单CSS，无重启/模型/数据变更。截图 `/tmp/kokoro-composer-single-focus-desktop.jpg`、矩阵 `/tmp/kokoro-composer-single-focus-real-matrix.json`。重复user及视口切换后通用failed卡仍真实可见，精确失败/同user重试与深链仍开放，不以CSS遮盖。

Agent main `f3be3b97dd67df69ed3c6cb88c59f3bc2db97703` 15文件精确提交、clean；完整分类与唯一proof metadata/comparator按职责搬移，无alias/兼容层/机器SQL变化。Root fresh252Ruff/Pyright0/generator/checker/1520pass6既有skip174deselect/build actual0，真实PG/Redis/HTTP22pass无skip，fixture残留0/cleanup[]，System/model为double；日志 `/tmp/kokoro-agent-granularity-root-{final-gates.log,real-acceptance.log,real-acceptance-result.json}`。标准实际FAIL137/0，仅移除本片新增2项，无新项；不称全工程标准清零。BFF vendor/runtime仍原2.0，后继按strict3.0持久failure/public breaking/Web协调推进。Root更新68来源指针，3active/13broken不变；Root冻结六项来源后完整治理测试实测1103passed/3既有skip/455subtests（122.91s，exit0），日志`/tmp/kokoro-single-focus-agent-granularity-root-tests.log`；Root集成commit `4133174cfc5e356acb4cabb9d0c67340f1e82197` 后relay/topology/指定checkpoint actual PASS/exit0，session46296已消费；三JSON `/tmp/kokoro-single-focus-agent-granularity-root-{relay,topology,checkpoint}.json`，Billing五docs与Root uv.lock保留，完整目标仍active。

# 历史切片与组合记录

以下为当时的来源、失败和验收证据，保留用于追溯，不作为当前来源或授写指令。当前组合及未完成项以本文件顶部本轮记录和 task 顶部为准。

## AGENT-FAILURE-3.0 与 Run 首事件已完成 owner 验收（2026-09-30）

Root 来源集成 commit `e2ef2866fd9a3de9b1b1ae2cef107bb9282d8fdc` 后，正式 IAM relay、repository topology、
指定 `w1e-iam07-bff-pin` checkpoint 均 actual PASS/exit0，session62704 已消费；
证据 `/tmp/kokoro-agent3-root-{relay,topology,checkpoint}-final.json`。只提交本片5项，
Agent/BFF/Web子仓clean；Billing五docs与Root uv.lock仍未提交，不称全体clean。本段仅追加验收记录。

Agent main `da056b0103cced10188cdc1f5baef841d8333889` 已由 Root 按冻结 29 文件精确提交、子仓 clean。
独立最终 review P0/P1/P2=0/0/0、29/29 hash 吻合；Root fresh 完整离线门 actual exit0：
Ruff251/Pyright0/generator/contract/lock/frozen sync、1518 passed/6既有skip/174deselect/364warnings（58.74s）、wheel/sdist。
日志 `/tmp/kokoro-agent-evidence-cursor-root-final-gates.log`。
Root 完整真实 PG/Redis/HTTP owner acceptance 22 passed/100warnings/7.31s、exit0、无跳过，
包含安全失败 true/false、index0 terminal replay、tenant/fence；System/model 为 test doubles，不是外部推理 E2E。
自有 fixture 数据库和 Redis15 残留均0/cleanup_errors[]，不触活跃 DB10/共享schema。
证据 `/tmp/kokoro-agent-evidence-cursor-root-real-acceptance-all{.log,-result.json}`。
旧 after_seq0 漏 index0 及此前 driver 解析失败记录为历史，未伪造 START、重排索引或放宽断言。

Root 仅更新当前 Agent owner/source 指针与 commit blob 摘要；BFF 的实际 2.0 vendor/generated 不改写成3.0，
库存维持3active/13broken。BFF 精确失败持久化及公开契约、Web严格消费、受管服务协调发布仍未完成；
现3310组仍原Agent58b/BFF15e组合，没有热加载半套契约。Billing五docs与Root uv.lock保留。
后续在清除本片新增两项粒度问题后进入 BFF 文档门及严格消费，不以 owner acceptance 代替整个产品闭环。

Root 冻结来源后完整 `python3 -m pytest -q scripts/tests` 实测1103 passed/3既有skip/455 subtests，
123.78s exit0，日志 `/tmp/kokoro-agent3-root-final-tests.log`；先前变化中定点131pass只作历史，未用作最终放行。
Root fresh全仓标准门 actual FAIL：139 violations/0 unverified，比既有137新增Agent
`execution/events.py`806行与`execution_proof_contract.py`804行两项800行粒度违例。
因此本片仅行为/契约来源验收，不宣称整个Agent工程标准清零。先按变化原因清这两项再BFF发布；
不得压空行、挤tuple或豁免阈值冒充修复，独立只读后继设计审查已派发。
原标准输出 `/tmp/kokoro-agent3-root-standard-first.log`（text），首次摘要读取误当JSON保留为调用错误；
显式JSON格式复验 `/tmp/kokoro-agent3-root-standard.json`。Billing/Root uv.lock未暂存。

本轮再验正式 IAB：聚焦 textarea border0/box-shadow none/透明outline；composer x282/768px，无横向溢出。
原问题重复提问仍真实可见，不隐藏数据冒充布局修好；截图 `/tmp/kokoro-chat-layout-current-verified.jpg`。
只读追踪确认当前终态“重试”调用普通createMessage新key，BFF创建第二user/assistant/run；不是CSS重复。
目标采用BFF正式同user重试command，复用原user、冻结输入/选项，只创建新assistant/run/outbox；
先完成failure profile再明确server retryable=true准入，不让Web猜失败文案。未知POST结果恢复继续原key，
与终态重试分开；原重复数据不隐藏、删除或合并，不建立兼容分支。命令路径与机器契约由BFF文档门确定。

## WEB-READING-AXIS-ALLWIDTH 已验收（2026-09-30）

Web main `30545c55625fb257ac17ce2199e8fa1000f3ecae` 已由Root按五文件精确提交，子仓clean；只改现AppFrame阅读轨、两测试及两文档。Root独立Node22完整check实际exit0（contract109/architecture37/1800 tests/lint/typecheck/build），日志 `/tmp/kokoro-web-reading-axis-root-final-check.log`，独立最终审查0/0/0及5/5冻结hash核对。

正式3310原生IAB十宽度/侧栏真实矩阵全过：390/640漂移0.40625px，其余641/700/767/768/800/960/961/1280均0、无横向溢出；800/960收起，961/1280展开。焦点内框仍透明、圆角shell可键盘定位，全文数组未变。只同步自有runtime一个CSS、不重启、不调用模型或计费；窗口/侧栏恢复原状。截图 `/tmp/kokoro-web-reading-axis-desktop-final.jpg`、`/tmp/kokoro-web-reading-axis-mobile-final.jpg`，数据 `/tmp/kokoro-web-reading-axis-real-matrix-final.json`。

保留两类真实失败：首候选纯1800pass但960px漂移54px，追加RED后修form的48rem上限；返修worker完整首跑既有HTTP5s超时1799/1800，隔离3/3与完整重跑1800、Root独立全门均通过。没有放宽断言或timeout。新增Preview Playwright几何源码未执行，不冒称自动浏览器全套PASS。重复user、空/失败状态、sidebar列表加载错误及query-only深链仍开放；本片不是所有能力闭环。

Root本片38个Web来源指针与34个commit blob路径重新核对，digest没有变化，现有broken依赖不改绿。Root相关三文件治理测试54pass（39.18s，`/tmp/kokoro-web-reading-axis-root-integration-tests.log`）。Root集成commit `2b9d6379` 后，strict IAM relay、repository topology、指定w1e-iam07-bff-pin checkpoint三门均actual PASS/exit0，session32068已消费；证据 `/tmp/kokoro-web-reading-axis-root-{relay,topology,checkpoint}.json`。独立Root最终0/0/0；本段为验收记录补充，代码/gitlink/库存未再变。task/progress保留未完成后端与Agent/Billing/uv.lock在途状态。

## 历史用户页面复验（Web 7c2b4d7，已由30545c55后继）

以下为修复前Web `7c2b4d700c8a4399fae68012c1db7423d790abd7` 的历史证据：当时重新操作正式3310原生IAB，而非只检查源码。桌面 textarea 为透明 outline、无内层 box-shadow；form/content 同 x282、768px。390px 窄屏 form x16/358px、content x15.59/358.81px，无横向溢出。Shift+Enter 保留两行并增高至51px，没有提交消息；清空测试草稿、恢复默认窗口，原 article 全文数组严格不变。截图 `/tmp/kokoro-chat-layout-current-desktop.jpg`、`/tmp/kokoro-chat-layout-current-mobile.jpg`；新 Node22 定点 Composer/AppFrame/architecture **164 passed / 6 files / 7.22s / exit0**，日志 `/tmp/kokoro-chat-layout-current-tests.log`。本轮未重跑完整 build/Playwright，也未调用模型或充值。

仍可见重复提问与历史空失败轮次；不是以 CSS 隐藏或去重解决的布局事实。深链、重试身份及精确安全失败的 Agent→BFF→Web 持久消费仍待闭环，不称完整产品完成。Agent cursor 已由唯一 writer 实现并冻结、独立审查0/0/0；Root纯门1518pass与build已过，真实PG/Redis/HTTP复验尚未执行成功，未发布切换当前受管2.0组合。

## WEB-COMPOSER-VISUAL-ALIGN 已验收（2026-09-30）

Web main `7c2b4d700c8a4399fae68012c1db7423d790abd7` 六文件已提交；Root本片已固定该gitlink与38个consumer证据指针，原契约摘要无变化。内部直角框移除、键盘token焦点在圆角shell、thread与composer统一48rem、手机viewport不误用桌面32px。Root Node22.22.2 `pnpm check` exit0（contract109/architecture37/全量1800/lint/typecheck/build）；日志 `/tmp/kokoro-web-composer-align-root-node22-check.log`。独立只读返修后0/0/0；单独prettier六文件检查FAIL、未全仓格式化，不称全格式门通过。

真实 IAB：桌面两轴x282/w768，390px content x15.59/w358.81与form x16/w358、无横向溢出，欢迎/线程聚焦均无可见内框；多行38→100→38，Shift+Enter不提交，Tab可达。owned runtime仅两CSS同步并核对旧baseline，无重启/新模型调用。原消息全文数组在恢复原conversation并reload后与修前严格相等。截图 `/tmp/kokoro-composer-desktop-after.jpg`、`/tmp/kokoro-composer-mobile-after.jpg`、`/tmp/kokoro-composer-welcome-after.jpg`。

新发现同pathname query-only导航漏接，new conversation后URL可能被stale eviction清空；显式goto+reload已重新恢复原conversation，非owner删除或丢数据。原Web负责人已只读定位，后继需deferred snapshot RED与严格失败清理断言，暂未授写。重复user/空failed assistant、完整failure契约与整个Wave0–7仍未闭环；未隐藏消息冒充布局完成。Agent cursor docs/tests已冻结RED，源码未授写。保留任务外Agent/Billing/Root uv.lock变更。

# Root 历史组合（已由文件顶部当前组合后继）

**Agent当时来源（2026-09-30）：** 已验收提交 `da056b0103cced10188cdc1f5baef841d8333889`，完整22例真实owner HTTP acceptance与Root1518纯门均通过，详见顶部。此前safe failure两例因Run初始cursor漏index0失败的记录为历史；Run-only -1修复保留Chat0、索引与fence。BFF/Web未切新版，运行组仍2.0，重复提问语义未完成。

**BFF已验收组合（Root `7c13378e3e752b72c170cfdf3629cca743db5b81`，Web新片另见下段）：** BFF `15e07fa44670bc13705ce3f6f700e73afcb72ccc` 已验收、clean并集成。Root提交后strict relay/checkpoint/topology均独立exit0；完整 `scripts/tests` **1103 passed / 3 native依赖skip / 455 subtests**，108.74秒。新全仓标准门实际exit1，仍137违例/0 unverified；main-only实际exit1，主仓和11子仓本地/远端均只有main，但Billing五docs候选及任务外Root `uv.lock` 未提交，不称全体clean。此前BFF pure506pass1skip、fresh install/target8/full47真实owner integration通过及fixture失败历史保留；来源库存仍3active/13broken。


**Web当时owner验收（2026-09-30）：** `5058ae2c400dd8be1964bba5df03fd7ce5b52133` 已由Root精确提交八文件，子仓clean。独立最终review0/0/0、8/8冻结hash一致；Root显式Node22.22.2完整 `pnpm check` exit0：contract109、architecture37、lint/typecheck、162文件1799tests、build；隔离3387 Web治理Playwright11pass/1既定mobile rail skip（8.3s），不是真实IAM/模型E2E。首Root check误用Node24，保留原日志而不当Node22验收；worker首typecheck与非pending pause RED缺陷已严格修复。仅恢复owner snapshot绝对尾failed assistant且无active_run/未决pause的通用failed/error=null，不自动重跑、无新contract/SQL/兼容层。Root组合库存38个Web来源指针重钉，34路径raw digest原bytes，3active/13broken不变；Root集成`1e7b721b7b725166570da844ec8b3fee0e7b634f`后strict relay/checkpoint/topology分别actual0；完整Root1103pass/3native依赖skip/455subtests（119.07s），均实际终止。


**本轮原生窄闭环：** Root只将自有受管Web复制处hydration.ts从经bytes确认的840更新为accepted5058，其他服务/权限/登录/配置/进程不变。原IABtab3焦点超时，新同browser3 tab5正常/app同会话；真实失败generic提示与retry在reload后保持。一次手动retry得到真实中文追问回答和END标记，Stop消失，terminal reload前后3article全文数组一致。新发现刷新后同追问用户泡泡exact count2；retry当前按新turn提交的持久语义仍须BFF/Web只读审查，不称完整retry产品PASS。精确failure合同、流式中途reload、全部能力/计费仍未闭环。Agent四文档冻结已通过独立0/0/0及Root逐hash/SQL原bytes核对；当前2.0 checker实际exit0、四tests baseline101pass，仅作为现态证据。原owner已获四tests-only RED，机器/source仍2.0/runtime58，未发布3.0。

**当前运行与原生浏览器：** 唯一受管组session29394/launcher65119已正常启动3310，workspace `/Users/nako/WebstormProjects/github/thefoxfairy/kokoro-local-login-xm_q35q2`，启动时加载固定Web840/BFF15e/Agent58b/Systemc0a来源（Web后继仅hydration受管copy更新见上文），用户指定gpt-5.6-luna私有profile；空Skills、Storage未配置。新原生IAB tab3走正式 `/login`，账号提交通过。经用户明确同意首次权限，原签名过期后重新进入同范围新签名并完成consent/callback，已实际回到 `/app`。原生UI首消息得到30条建议及END标记，终态Stop消失；刷新前后回答全文453个JS字符口径（string.length）一致、article唯一。这仅证明新登录/真实回答/终态刷新子门，未捕获流式中途刷新，历史terminal DOM失败不改为PASS。同会话追问实际失败：曾显示“空间配置有误”/Agent run failed，后续状态观察中失败卡与重试入口消失，仅留下用户消息；续问及失败持久展示门FAIL。同期System日志有unknown与resolve error，但未取得同Run身份关联，不能确认本次根因。原生IAB访问正式同源snapshot被浏览器ERR_BLOCKED_BY_CLIENT拒绝，未换通道绕过。全部能力、正式积分链仍未闭环。下文较早运行停止/候选记录为历史，不是当前派工。

**历史候选复验（BFF activeRun，Root604dc12f）：** 12文件冻结hash核对，独立最终源码审查0/0/0、无infra聚焦20pass；Root Node22 format/lint/typecheck/contract191/architecture27/test506pass1skip/build全部exit0，日志`/tmp/kokoro-bff-active-run-root-final-gates.log`。真实自有PG首次GREEN尝试为7pass/1fail/0skip（`/tmp/kokoro-bff-active-run-real-pg-green.log`）：newer-run终态因fixture只有consumer registration、缺正常ChatTurn assistant/dispatch绑定而触发`AGUI_ASSISTANT_BINDING_MISSING`。未放宽生产guard，原owner仅修fixture和CURRENT；自有库/新增库0、Redis新增0/baseline保留。仍未验收/提交BFF、未启动3310、未通过浏览器全文门。Billing只读核查确认新Metering当前按功能quantity=1定价，无成本倍率规则；1.4与9.4基准待用户确认，未写配置或执行账务。

**本轮后置更新（Root代码9e77ac17）：** checkpoint/topology分别实际exit0；使用用户指定私有profile，一次真实免费库存GET成功、未调用推理。BFF tests-only已冻结，Root复用现PG/Redis在唯一自有临时库执行真实RED：3pass/5fail/0skip、2.31s，均缺active_run或缺非法marker拒绝；自有库0、Redis新增0/baseline保留，日志`/tmp/kokoro-bff-active-run-real-pg-red.log`，原owner已获GREEN源码授权。Billing五docs修订独立0/0/0，但IAM任意target能力未发布，源码/入账仍阻塞。用户要求的当前线程每10分钟检查并推进heartbeat `kokoro-10` 已创建ACTIVE并回读；静默无变化、实质进展/失败/偏差/决策通知。3310仍未重启，完整goal未闭环。

## 本轮最新：开发入口稳定性与竞品交互对齐（2026-09-30）

Root `6fdcba6e` 基线的三文件生命周期切片已由原writer停写、独立复审0/0/0、Root主树完整纯门 **1103 passed / 3 native依赖skip / 455 subtests**（114.87s，session2944 exit0已消费）后验收。日志 `/tmp/kokoro-provider-lifecycle-final-root-tests.log`；Ruff check/format/diff均exit0。外部周期库存的预期传输/格式失败只写System `unknown`，继续原两ownership续租、health CAS与严格status/observed_at/provider/generation回执；不伪造healthy，不退出独立IAM/Web。下一正常60s周期可恢复healthy。配置/代码、owned进程、ownership、CAS/回执错误仍fatal，启动两个preflight和Ollama严格不变，无后台保活/自动重试/付费健康推理。

首候选1102pass仍被独立审查1P1拒绝：回执只验证provider/generation，接受了与unknown命令不一致的healthy。追加RED16场景后补齐真实System回执绑定，最终聚焦58pass/114subtests；原FAIL和首候选日志保留。三文件最终hash已Root核对；这里仅证明工具代码/测试，不证明真实周期故障恢复、已重启3310或完整浏览器Chat成功。**3310仍未重新启动，真实Chat terminal DOM门仍FAIL。**

官方ChatGPT Projects、Manus Projects/Connectors及Scheduled Tasks参照和Kokoro验收取舍已进入既有 `docs/task.md` 顶部：会话/项目/调度定义/Run身份分离、默认个人私有显式分享、真实文件与结果；不另建UI/计划中心。BFF四文档修复独立0/0/0通过，原2P1/1P2关闭，仅恢复既有v1 running的同RR snapshot方案已放行测试RED阶段；OpenAPI原字节、不改enum/消费者契约，源码与真PG/浏览器尚未验收。Billing五文档修订候选已停写，200command ACK/1Credit=1e6micros/reason贯穿已统一，IAM任意target能力明确owner-first阻塞；未充值、未计费E2E，文档待复审。

状态日期：2026-09-30。这里只记录历史组合和已验证边界；执行任务见 [task.md](task.md)，逐轮证据及失败历史见 [progress.md](progress.md)。旧 CURRENT 时间线保存在 Git `51bd4a2f40aab98b253329c0a5e9d110b7e77211`，不是并列的当前方案。

## 当时锁定的历史组合

下表与当时 Root 集成提交的 gitlink 一致，不代表正在修改的子仓工作树或常驻预览的加载版本。Root 是 Git superproject，`.gitmodules` 的 branch 只是提示，精确发布来源由 gitlink 与 owner artifact digest 锁定。

| 路径 | 固定 commit |
| --- | --- |
| `apps/kokoro-agent` | `58b59cf7cdc4132042d25460b4928d71a66ae7ec` |
| `apps/kokoro-app` | `30545c55625fb257ac17ce2199e8fa1000f3ecae` |
| `apps/kokoro-bff` | `15e07fa44670bc13705ce3f6f700e73afcb72ccc` |
| `apps/kokoro-billing` | `63e0ab6e61b397f23f7ab71f5d6dc9df3d6de0fa` |
| `apps/kokoro-capability` | `6519ae9a7dba63586474d2860f6725d3165b701e` |
| `apps/kokoro-iam` | `e3c035b99cf9479ac8357c7d38147f1541dcbcac` |
| `apps/kokoro-mori` | `ca76c2e12861a2e4a6af3049f6df8c34b417c158` |
| `apps/kokoro-scheduler` | `975dee59616a1e0eda609aa69283401344900d83` |
| `apps/kokoro-storage` | `16a6c1ce95832df6dc839e0d50e957405c5c7005` |
| `apps/kokoro-system` | `c0a76a3a7614bf46ea6e665e523f24261862436f` |
| `libs/kokoro-web-shared` | `0c4e87ace01340aaa07bc57935f1d98b8e77af14` |

`apps/kokoro-app` 是本轮唯一正式前端；Mori 不参与本轮业务重构。当前物理名称仍为 `apps/kokoro-capability`，业务目标为 Platform，重命名/cutover 未完成；不使用 `apps/kokoro/` alias。模型目录归 System，不新建 kokoro-model。

**历史用户链证据（当前组另见下文）：** 3310曾唯一有序切换到用户指定外部`gpt-5.6-luna`；正规IAM登录→app原生发送202→正式System resolveModel success→标准Agent真实可见回复。独立首轮捕获流式前缀并途中刷新，但terminal严格组合断言E_FLOW，原失败保留。同一会话后验GET两份完整snapshot稳定、DOM全文一致、原生logout成功；不能以后验改称首轮全通过，途中刷新的瞬态断言仍待定位。右侧IAB操作被平台URL policy拒绝，未绕过，独立Chromium不是右侧IAB已验。

**历史运行更新（已被当前29394组替代）：** Root ee22bacd原受管session92720/launcher39290/Web39688已exit1且3310无监听，workspace`kokoro-local-login-he2cz0xc`保留。固定安全日志明确实际失败分支`stage=provider`，即模型库存观测失败导致整组清理；并非已经证明真实推理失败或具体HTTP状态。该组实际曾加载Web752/BFF677、emptySkills/Storage未装配。后继须隔离模型库存观测与独立IAM/Web生命周期，不放宽ownership/CAS或伪造healthy，不盲目重复重启。

**历史真实Chat失败验收：** 新独立产品Chromium第二轮已越过真实login/UI202/非空prefix途中reload/RUN_FINISHED、owner completed、Stop detached、两份正式terminal snapshot全文/ID/run/status/watermark比较；FAIL精确为`terminal_dom_full_content`，最后owner有效、Stop0/user1/markdown-message2。这两DOM parts不等同重复Message；已纯当前源码对照复现：BFF snapshot缺active_run时无法认领同run前缀，补合法active_run则一段。真实轮reload瞬间shape未捕获；后继BFF同RR projection文档门进行，不加Web猜测或盲拼START。证据`/var/folders/gn/wbk8wfbd047_wvwkwtyn331r0000gn/T/kokoro-gpt56-await-proof.h4b1tsvz`，非右侧IAB。原首轮及历史E_FLOW失败保留，无完整E2E PASS。

**真实Product安装当前：** Root `c3fa42710334bf1b9dc00f9be0f8b6a21a647e78` 原入口`run_bff_skill_draft_sandbox_smoke.py --product-installation`已真实exit0/PASS（session78975），日志`/tmp/kokoro-product-installation-real-surface.log`。固定IAMe3c/BFF677/Platform6519/Storage16a6，复用现PG/Redis/MinIO/ClamAV，五public操作、same-key历史ACK→GET当前、false筛选/opaque两页、移除/稳定ID重装、撤权五方法在owner前拒绝均通过；两不同已发布Skill、39receipt/2publish事件，resources clean。此前native依赖缺失与Root误开legacy surface的真实FAIL保留。此为后端组合，不是浏览器安装UI、同租户第二用户或标准worker非空Skill模型验证；Agent关闭仅结构证据，不冒充Run数据库观测。

## 最新验收边界

| 能力 | 当前证据 | 尚未证明 |
| --- | --- | --- |
| 非空 typed Skill Source | Root `4aef9d1c` 正常原文件入口真实 IAM/BFF/Platform/Storage/Agent/PG/Redis/MinIO/ClamAV，exit0/PASS；安装、原字节、native metadata、只读、停用拒读/重新启用、旧 lease 拒读、IAM 执行撤权均通过；receipt31→34/outbox2；resources clean、Redis15=0。日志 `/tmp/kokoro-source-window-real-composition.log` | 标准 worker＋真实模型的非空 Skill 运行、个人 Product 安装 UI、正式激活。native name 与 opaque 目录不匹配警告仍开放 |
| 普通 Chat/作品 | 历史固定组合已验真实 Chromium 登录、标准 worker、durable AG-UI、live Delivery、刷新、Canvas 下载、GC/410 恢复与个人私有性；历史 `5b1b9a5e` 还验真实 System→已有 Ollama→worker→Storage 作品链，精确来源/边界见 progress | 历史普通 Chat 或空选择模型结果不替代当前非空 Skill 模型运行，也不证明所有产品能力 |
| 个人 Skill 安装 | Platform runtime `d93e8a59` 已独立审查0缺陷＋RootNode24全门1185pass/243依赖skip＋真实ownedPG安装事务27/27（含ACKlost/CAS），自有库已回收。旧v5机器候选发现List has_more与唯一Proto optional next_cursor矛盾，已在6519ae9以5.0.1纠正，Root全门1196pass/243skip与独立0缺陷；仍inactive | owner runtime、机器wire、BFF固定消费者、Web纯门与真实后端五API组合已验；浏览器安装、正式激活、非空Skill模型运行仍待验，不是全产品可用 |
| 最近3310留证（现已停止） | 原受管session53033/launcher30171：IAM30877/System31271/Agent HTTP31307/worker31309/BFF31346/Web31351。精确Web14a54b4/BFF67755d16/Systemc0a76a3a/Agent58b59cf7；用户指定gpt-5.6-luna，经私有profile正式System路由/标准Agent。首轮正常登录和UI消息202、非空流式prefix/中途刷新、可见真实回复；同一会话后验两条完整owner内容及ID750ms稳定、DOM全文一致、原生logout/session=false。证据`/tmp/kokoro-gpt56-ui.CsnuNA`（首轮FAIL）和`/tmp/kokoro-gpt56-diag.hVEygz`（只读诊断PASS）。 | 首轮严格terminal E_FLOW未存当时shape/hash，历史具体子断言不可后验臆定；不能称首轮E2E PASS。Root新增正式快照全文/身份/watermark证据门仅纯测试通过，真实模型门尚未重跑。右侧IAB未验，Skills空选择/Storage未配置/完整产品未闭环。 |

Root Source-only 高请求量测试在 Run/lease 前主线程等待现 IAM60秒窗口；默认模式不等待，SIGTERM可中断。没有改生产限流、权限、凭据或 Redis 计数；这是测试资源礼让，不是应用重试/fallback。

## 用户指定真实外部模型

用户选择 `gpt-5.6-luna`，指定HTTPS接口真实 `/chat/completions` 已200、返回该ID及非空回复，
结果 `/tmp/kokoro-gpt56-luna-probe.json`（0600、无key/body）。Root现组合工具支持显式私有profile，
七源码/测试文件独立0缺陷、Root87tests/36subtests与Ruff通过；不改System/Agent owner API或原Ollama guard。
历史3310外部profile经正式System→标准Agent→UI已产生真实回复；最新受管组另见上文，完整首轮E2E仍FAIL，后验持久态/DOM一致不改写历史失败。旧7399及其六直接子进程已全部退出、session65687已回收，首启动因3310临时bind占用exit1，等原guard释放后再成功启动，无kill-all/端口guard放宽。

## 当前优先级与正在推进

- Platform 原负责人：runtime已验收提交d93e8a59；已提交6519ae9未激活v5候选5.0.1 wire矛盾纠正，唯一Proto/Schema/runtime源码冻结，无兼容字段/双轨。
- BFF消费者67755d16已独立0缺陷与Root Node22全门验收提交；五本人安装路由固定Platform6519/5.0.1，读projection/写catalog分离，默认新增测试已纳入，413/504真实状态契约。真实IAM→BFF→Platform安装组合已PASS；Web安装浏览器仍待验。
- Web原负责人：个人安装consumer已提交752aff9d，29文件独立0/0/0、Root contract109/architecture37/lint/typecheck/test1773/build通过；五client/严格同源adapter/UI未知同key/currentGET/分页取消已验纯门。真实后端组合已PASS；新3310启动时加载本片后退出，浏览器安装仍待验。完整Project typed全集及任务关联仍后继切片。
- Root主线：gpt-5.6-luna正式链真实回复已见，首轮中途刷新严格断言失败待精确定位；已完成的Web/BFF候选统一提交并加载，旧session53033/14183已退出，旧92720已退出；当前29394唯一受管组已加载BFF15e07fa4，并按顶部记录做原生IAB验证。继续按owner推进非空Skill/安装Web、Project真实全集及全产品闭环，不把直接provider probe/后验快照冒充完整E2E。

同仓单writer；worker不自行启动共享PG/Redis或重置数据。子仓 CURRENT 中“候选待Root”属于交付时快照，Root已验收状态以本表和绑定commit的task/progress为准；在owner下一代码切片同步文档，不因纯文案制造另一轮依赖升级。

## 未闭环清单

1. 当前个人安装machine→owner runtime→BFF真实后端组合已验；Web浏览器安装、Platform原子命名/激活cutover仍开放。
2. 非空Skill真实worker/模型、MCP执行与其他Agent能力；不以Source helper读取替代真实运行。
3. Browser signed PUT/CORS：已探测本地MinIO返回501；HTTP Source GET/PUT或预览Playwright不替代浏览器发布门。Storage orphan retirement/quarantine 等生命周期仍开放。
4. System 部分 installer 仍锁 public/整库空白；同库owner schema组合边界须继续修正。Team DOM/邀请邮件/写操作、Scheduler调用/恢复与其他Product surface均须按owner闭环。
5. 最近全仓标准门137项违规（旧136非当前），来源库存16边/13 declared broken；这些是仍开放队列，不因局部PASS改绿。完整goal仍active，Billing最后。
6. BFF d654a1bc已完成IAMe3来源重钉，16SDK与owner inputs原bytes，policy语义不变；Root3bdf27db已集成；提交后relay实际FAIL（BFF四文档候选仍dirty），前一组合命令尾部git status掩盖前面退出码，原PASS描述已纠正；预提交HEAD/index不一致FAIL也保留。checkpoint/topology须独立记录，不以整段shell末尾exit0推定。Web仍更旧a4/0.6 relay消费者，后继原字节消费未完成，不把BFF provenance PASS当Web闭环。
7. 工作树任务外Root `uv.lock` 变化保留不暂存；不称全体clean。本轮实际main-only核对主仓+11子仓本地/远端全仅main、当时11子仓clean；当前BFF文档候选和Web修复在途，整体gate因Root在途改动及任务外uv.lock FAIL，后者保留，不称全体clean，不新建分支/PR。

## 验证和归属

- 最新Root `a0b95a31`发布组合：独立checkpoint/topology实际exit0；完整`scripts/tests` **1094 passed / 3 native依赖skip / 409 subtests**，100.52s（session75632 exit0已消费），日志`/tmp/kokoro-web-billing-root-full-tests.log`。严格IAMrelay门仍FAIL：BFF候选四文档dirty；不以Root纯门PASS将该门改绿、不称整体clean或收费已完成。Web840完整owner门1784/162无skip已独立验收；受管3310仍未重新启动。

- Root当前`c3fa4271`组合checkpoint/topology PASS；同handle91663全量`scripts/tests` **1090 passed/3 native依赖skip/395 subtests**，117.49s，exit0已消费，日志`/tmp/kokoro-product-final-root-tests.log`。Product selector独立0/0/0、聚焦86/98subtests，原入口真实owned组合PASS；3个native skip不以Agentvenv真实组合覆盖为本runtime全绿。全仓标准门最近仍FAIL137/0 unverified，不更改门禁清零。
- Root `4aef9d1c` 提交后的topology9runtime/checkpoint通过。新增候选仍须独立验收和最终集成复验。
- 子仓的 tests 不迁入 Root；`scripts/tests/` 只覆盖 Root 治理脚本（含Root自有组合driver边界），业务unit/integration/contract/build仍在owner仓。`verification/` 保存跨仓来源库存与检查点，不复制业务测试。
- 本地应用使用一个PG数据库/一套credential、独立owner schema和共享Redis namespace；测试临时库用于运行隔离，不是多应用角色/部署方案。禁止跨owner业务SQL。

当前可执行门：

```bash
python3 scripts/verify-repository-topology.py
python3 scripts/verify-contract-checkpoint.py --expected verification/contracts/checkpoints/w1e-iam07-bff-pin.json
python3 scripts/verify-iam-relay-policy.py
python3 scripts/verify-main-only.py
python3 -m pytest scripts/tests
```

旧 `verify-ten-repository-full.sh` 与 `run_stage2_owner_health.py` 的共享状态编排暂停，不能当作全仓验收；完整单仓门、真实模型和浏览器门按task依赖逐片执行。

## 正式积分流程最新核对（2026-09-30）

用户已授权当前测试帐号后台积分入账；尚未执行，不称已充值。Web“本次由 Kokoro 承担费用，不消耗点数”是 taskTitle 条件下的静态 Badge，未消费计费 owner 决策，九语言对收费说法矛盾；删除片已提交Web840fa7e0、独立0/0/0、Root重跑完整1784tests/162files、contract109/architecture37/lint/typecheck/build PASS；未启动预览/未真实浏览器验收，placeholder亦已中性。Billing `63e0ab6` 已有32表 canonical 与新 CreditService 的事务组件，但生产主入口仍旧 pg/旧表，新 grant/operator入口与 Run准入/结算未接，CURRENT明确M3/M4前不可部署。Web余额 DTO 与BFF public契约及标准402 error code消费也有缺口，不能以移除Badge宣布账务闭环。支付渠道仍最后；积分正式赠送、reserve/capture/release 和余额/流水按owner后续逐片验收。

## WEB-BILLING-TRUTH 集成证据

Web `840fa7e0ff9c4d241daca0c297b120f34821018e`：16现文件已冻结hash核验、独立0/0/0与Root Node22主树完整门后提交。Root日志 `/tmp/kokoro-web-billing-truth-root-gates.log`；162文件1784通过（含worker未跑的8个integration命名文件119项，无skip），contract109/architecture37/lint/typecheck/build/diff PASS。这里的测试名称integration不据此冒充真实Billing/provider组合；未充值、未Run扣费/浏览器验收。Root后继只更新Web gitlink/来源库存/blob digest与driver固定SHA，不改任何业务或放宽门。BFF active文档独立2P1/1P2（版本策略、非法stream矩阵、永久失败测试允许集）尚未通过，未授权源码；Billing新正式admin grant五文档门进行中。

### a0b95a31 后置门事实修正

Root已集成Web840fa7e0；relay门实际FAIL `apps/kokoro-bff: child worktree is dirty`，由尚未通过独立审查的BFF四文档候选触发。首前置shell尾部git status曾掩盖门exit1，Root读取原JSON后已纠正全部本轮relay PASS断言。原失败日志保留，严格门不放宽，也不回滚/覆盖worker候选。Web1784/162完整owner测试/构建为独立已实跑exit0，和Rootdirty gate分别记录。Root随后各门独立执行，不再以shell最后命令冒充前面门通过。
