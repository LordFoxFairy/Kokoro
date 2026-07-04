# Claude Progress

- Date: 2026-07-04 (R-artifact 设计定稿——决策完备待"继续")
- docs/superpowers/specs/2026-07-04-artifact-face-design.md：核心难点定案（agent/session 跨进程，backend FS 对 session 不可达 → **双面分工：backend FS 服务模型、共享 ArtifactStore 服务人**）；四层设计（agent 端口+content_and_artifact 类型化元数据通道拒路径嗅探 / 契约 artifact 对象替换 string 占位+产物 HTTP 端点 / session 直连同后端出字节 / web 按 MIME 渲染播放器）；验证锚=正弦波本地工具真产物场景 G；64MB 上限 fail-loud；版本/hub 检索/清理明确出界。
- 用户裁定已入 memory："继续"=全程自主收口，执行期零决策残留。

- Date: 2026-07-04 (系统总方案 v2——三仓全栈，music/video 北极星)
- **docs/superpowers/specs/2026-07-04-system-master-plan-v2.md**：三仓四面总览、全栈十词法典、成品体系（本体论+对偶性+三元+新类型手册）、能力矩阵、13 条法则汇编、路线图重排——**R-artifact 升首位**（media 成品产出非文本，产物面=music/video 硬前置：content_and_artifact→artifact_ref→session 产物端点→web MIME 预览）→R-hub（含 profile.subagents 纯工人表）→music 落地→retention→外部件。v1 agent 方案标记取代。
- 下一单默认：R-artifact（等拍板）。

- Date: 2026-07-04 (深度思考单：成品/子代理二元论 + 能力束流动定稿)
- **本体论法典**：docs/superpowers/specs/2026-07-04-product-vs-subagent-ontology.md——四维对立表、**对偶性定律**（成品被选中=主位/未选中=降格子代理，声明束两用、代码配方只在主位）、成品三元（资产 prompts/ + bundle 在 session 入口表 + 配方 orchestration/<type>.py）、music 两条落地路（数据型近零改动/代码型纯增量+届时契约分派键）、细节边界清单（守卫两态/记忆两态/纯工人 profile.subagents 缺口留 hub 批次）。
- **对偶性断裂实锤修复**（agent 406e614）：wire_subagents 主 index 优先→KOKORO_TOOLS 注册表兜底→未知 fail-loud；修复前 general 主位挂带专属工具的降格成品必炸。
- 验证：agent 335 + pyright 0 + ruff + e2e PASS。

- Date: 2026-07-04 (用户三连批→整体形状定案：prompts 资产域 + 类型化配方)
- **定案形状**：类型的两个家——资产在 prompts/<type>.md（general/web-researcher 已归位，prompt 文本出现在 .py 即红灯）、配方在 orchestration/<type>.py（general.py 现在；music 届时纯增量+契约加分派键）；agents/ 镜像目录撤销（第三个家=死结构）。
- **工具用法彻底出 system prompt**：指引全文并进各工具 description（LangChain 经工具 schema 交模型），_SECTIONS/render_tool_guidance/guidance.py 全删；context.py=纯两段组合（人格+skills）。SteeringMiddleware 归 tools/middleware.py（运行时中间件之家）。
- real-model 场景 F 时序脆弱修复（受理即插话，不与末轮竞速）。
- 验证：agent 335 + pyright 0 + ruff；e2e PASS；real-model 26 项 PASS（含 F 复绿）。lessons 记"三连改被批不带思考"。

- Date: 2026-07-04 (用户批 context.py 囤工具文案→指引随本体)
- **工具指引文案归位**：ToolGuidance{requires,text} 随各工具模块（tools/*.GUIDANCE），context.py 只留拼装序——加/删工具不再触碰拼装点；防漂移钉子（各 GUIDANCE 必含自身工具名）。lessons 记"配套件二犯"。
- 验证：agent 335 + pyright 0 + ruff + e2e PASS（行为保持，纯归置）。

- Date: 2026-07-04 (用户质疑"入口好奇怪"→entry 域减肥 + 工具自述上 wire)
- **entry 域名不副实收口**：AgentEntry.name/description 零消费者（入口表在 session，入口=数据）→删 entry.py，agents/ 只留 GENERAL_PERSONA 人格资产；docstring/handbook 同步诚实化。
- **审批卡数据源接通（用户点拨"tool 不是有 desc 吗"）**：AssembledAgent{graph, tool_descriptions} 装配产物携 describe_tool → awaiting 载荷 description=工具自述（查不到发空串），deepagents 英文模板永不上 wire；web 审批卡自述优先、中文兜底。
- **web 仓发现他人进行中的改动（未动）**：package.json(+antd)、layout.tsx(+antd css)、未跟踪 tests/app/admin-i18n-workbench.test.tsx（引用缺失模块→web tsc 现红）——i18n 工作现场，等归属会话收口。
- 验证：agent 335 + pyright 0 + ruff；web 173（排除他人红文件）+ session 152；e2e + chaos PASS。

- Date: 2026-07-04 (R2 steering 全链落地 + 投影泄漏真缺陷修复 + HITL 卡文案法则)
- **steering（运行中插话）四层全通**：契约 run.steer 帧（幂等键=message_id）→ ledger 信箱（keep-first、未认领 run 安全丢弃防毒化 try_claim）→ SteeringMiddleware.abefore_model 模型轮前排空注入（稳定 id、只挂主链）→ session 活跃 run 的 POST 从 409 改"落库+转 steer"（确定性 msg_steer_{idem} 双端幂等）→ web 输入恒可用（草稿非空=发送插话/空=停止）。
- **走查抓出真缺陷**：注入的 HumanMessage 经 before_model 节点混进 v3 消息投影→冒充 assistant 正文上 wire。修法：正文通道只认 node=="model" 投影项，其余抽干防回压（test_steering 真图钉死）。
- **HITL 卡设计缺陷（用户批评）**：英文 interrupt 模板+裸 JSON 当文案→法则"wire 只带数据，展示文案归 web(zh)"：问答卡渲染 args.question、ask_user 行隐藏 JSON、审批卡固定中文文案。language 轴（用户语言偏好随账户）待 auth/用户设置，现阶段文案全中文即正解。
- 验证：agent 334 + session 152 + web 173 + 双 tsc/lint；e2e（含 steer 幂等断言）+ chaos；real-model 26 项双跑 PASS（场景 F：真模型运行中插话，产出以"转向确认"开头）；Playwright 全流程走查 3 截图（插话发送/卡片修复/正文无泄漏）。
- 待办小尾巴：steer 投递失败仅 console.error（无 UI toast，P1）；context-layer-notes 已记前缀缓存追记（动态 skills 尾部化方向）。

- Date: 2026-07-04 (R1 子代理执行面收口——用户拍板"先完成")
- **子代理工具事件通道**：契约新增 subagent.tool.invoked/returned（raw 18 / browser 19 kind）；投影路由改造（子代理内工具含其自有 todo 走新通道，不再覆盖主 todo 面板；嵌套 task 不双发；截断语义同 tool.returned）；session 透传 + web 穷尽接收。
- **general-purpose 守卫旁路收口**：orchestration 传同名 spec 覆盖内生 GP（tools/model 继承主 agent），守卫链齐挂；可达性政策不变。真图差分测试钉死（唯一守卫挂 GP、终态账本熔断出自 GP 子图内）。
- 用户即时批评已落实：注释禁排期黑话（V1/P1 词汇重写为约束陈述，lessons 入册）。
- 验证：agent 326 tests + pyright 0 + ruff；session 151 + web 171 + tsc；e2e 30 项 + chaos 双场景；**real-model 25 项 PASS**（场景 A 新增两断言：子代理内 web_search 成对事件 + subagent_id 归属，真模型实证）。

- Date: 2026-07-04 (命名归一 + 总体方案成文)
- **词汇法典归一**：三个"state"撞名收口——`run/state.py`→顶级 `state.py`（KokoroAgentState+RunScope，删空壳 run/ 包）；`storage/run_state.py`→`storage/ledger.py`（RunStateStore→RunLedger、Sqlite/MongoLedger、make_ledger、LedgerSettings）；env KOKORO_LEDGER_BACKEND/DB。用户裁定：**初期不留兼容层**（迁移闸写了又删，直接删旧换新）——入法则。
- **总方案成文**：docs/superpowers/specs/2026-07-04-agent-master-plan.md（PRD+技术方案+词汇法典+八条设计法则汇编+R1~R5 拓展路线：R1 子代理执行面收口→R2 steering+context middleware→R3 hub 分发→R4 retention→R5 外部件）。
- handbook modules/kokoro-agent.md 旧目录树（run/request.py 一代）同步真实现（子代理执行，待复核）。
- 验证：agent 321 tests + pyright 0 + ruff；e2e 30 项 + chaos 双场景 PASS（重命名后全量复跑）。

- Date: 2026-07-04 (存量裁剪——用户拍板：该移除的移除)
- **timeout 死枚举移除**：run_completed_status 收窄为 [completed, cancelled]（零生产者实证后直接删，不建墙钟超时生产者）；contract generate+check 全镜像同步，agent 参数化测试同步收窄。
- **定时任务提案作废**：后续走 MCP 机制（外挂 server 提供调度工具），不在 agent 内写死；scheduled-runs-design.md 已删。连带"前置改参 normalizer 挂点"失去首用例，继续搁置。

- Date: 2026-07-04 (深挖回答"还有什么缺陷"——四实锤全修 + hub v3 单轴归一)
- **namespace 单轴归一（用户两次纠正）**：个人=personal namespace 实例，无 user 层级/user_id；跨空间=grant；lessons 立"身份轴唯一性"防漂移规则。McpServer.headers 契约补齐（个人 MCP 凭据最小可用，四仓 CI 绿）。
- **结构批评修复**：agents/ 每成品一子包（general/persona.md）+ orchestration 真门面；AgentProduct→AgentEntry/GENERAL_ENTRY（入口词汇对齐 session）。
- **四实锤缺陷（本轮深挖，全修全钉）**：①多段用量少报→store 跨段累计真源（c54e77d）②崩溃重拾复制消息→稳定 message_id 幂等重放（同前）③子代理内审批 fail-loud→嵌套帧回退（合成稳定 id+task 段归属+占位 returned，f5b15e6）④审核政策委派旁路→review middleware 下发子代理链（7dd280d）。
- 验证：agent 322 tests + pyright 0；e2e/chaos 多轮 PASS。设计存量（未做，等拍板/外部件）：子代理工具事件通道（可见性 P2）、steering/retention 两提案、hub 数据模型、e2b、response_format、artifact 生产者、context middleware 化。（timeout 枚举已移除；定时任务改走 MCP，提案作废——见最新条目）

- Date: 2026-07-04 (心脏重构完成 — orchestration/agents/context/State 四合一，agent 7d3fbef)
- **State 轴迁移**：RunScope+KokoroAgentState（DeepAgentState 扩展）替代 context_schema 轴（实证生产零消费者后整体删除）；scope 随 input 进图/落 checkpoint/续段不重供（test_run_scope_state 真图钉死）；"context"一词让位上下文工程层。
- **四层分域**：agents/（general 成品）+ orchestration/（assemble 主配方+context 拼装点，只收领域设置——架构法测试抓住 AppConfig 越权后按域拆参）+ worker/ 瘦身 104 行 + execution/ 不变。
- 验证：agent 314 tests + verify-all --real 四套件全 PASS（e2e/chaos/trace/真模型 23 场景）。
- 设计稿：2026-07-04-heart-restructure-design.md（含 state-vs-context 裁决记录与 middleware 化升级路径）。
- 待办（用户新题，讨论中）：skills/MCP hub 整体设计（参照 Manus/CC）、入口切换的上下文语义（同 session 换 entry 时 prompt 更换 vs 追加）、agent 产物放置与 langchain 构造结合。

- Date: 2026-07-04 (守卫下发 + 三提案齐备 — 自主窗口收官)
- **守卫下发**（e916ed5）：TerminalGuard/TokenBudget 逐个下发进 catalog+wire 子代理的独立 middleware 链（不下发=task 委派旁路预算，真旁路回归钉死）；residual：deepagents 内生 general-purpose 仅 allow 档可达且不带闸（handbook 注记）。
- **三份提案待批**：steering（信箱+before_model 注入）、scheduled-runs（session 触发+幂等键）、storage retention（分层 TTL 全默认关）。
- 窗口终态认证：verify-all 三套件 PASS + 真实流式抓取冒烟 PASS；agent 313 tests；四仓 CI 绿。

- Date: 2026-07-04 (对抗复审三实锤全修 — agent 9c8de9b)
- 复审子代理（对抗性，限时收口）交付 3 条已确认真 bug，全部自行复核后修复+回归钉死：
- **①【高】跨 worker resume/cancel 竞态**（收养机制引入）：三层闸（resume 复检/执行入口闸/TerminalGuardMiddleware 轮粒度熔断）；cancel 语义定案=轮边界尽力而为+终态单胜者；竞态回归测试（renew 即终态→绝不 spawn）。
- **②【中】_control 泄漏**：done-callback pop + 公开观测面 control_listeners。
- **③【中】web_fetch OOM 面**：流式读取边读边封顶（5MB 响应实测只读 1MB 断流）。
- 门禁：agent 312 + e2e + chaos 双场景全绿；handbook cancel 语义入册。
- steering 设计稿（信箱+before_model 注入）已备提案待批。

- Date: 2026-07-04 (自主时段二：五单连发全绿)
- **token 预算熔断**（861bb08）：RunStateStore.add_tokens（sqlite UPSERT RETURNING/mongo $inc/fake，矩阵 24）+ TokenBudgetMiddleware（awrap_model_call 累计 usage_metadata，超限 TokenBudgetExceeded→run.failed）；跨 HITL 段不清零（store 背书，rebuild 测试钉死）；KOKORO_RUN_TOKEN_BUDGET 默认 0=关（预算数值属政策，用户裁定 agent 执法+namespace 政策位）。
- **web-researcher 内建**（0361710）：用户裁定"实现但默认关"——KOKORO_BUILTIN_SUBAGENTS 点名启用；catalog_subagents 装配点解析工具实例，声明工具缺任一整个不挂（不设空壳）；deny 声明集只含真挂载者。
- **subagent.thinking.delta**（四仓 2a964a3/881a0bb/7bb0504/0389ca5）：子代理 reasoning 不再弃置；契约 16/17 kind。
- **system prompt 行为工程**（b9185d7）：一行空壳 → 人格+条件工具指引（只提真挂载工具）+skills 三段组合；**真模型实证：不提工具名，模型自发 save_memory（key=ui-dark-mode-preference，内容自主泛化）**。
- 门禁：agent 309 + e2e ×5 轮 + 真模型微场景；全推送。对抗复审子代理已催收（15 分钟限时）。

- Date: 2026-07-04 (自主时段末段：流式工具输出四仓收口 + token 熔断开工)
- **tool.output.delta 全链落地**（契约 15/16 kind；agent a7a59f6 / session 02e1531 / web a5e681a / 父 5464d17）：投影层 output_deltas 不再 drain 弃置——发射进 wire（预算=TOOL_RESULT_MAX_CHARS 累计截停防刷屏），session 透传自动，web 穷尽分支 no-op（渲染留 canvas 期）。行为测试：增量序列在 invoked/returned 之间 + 预算截停；四仓门禁+e2e 绿。
- **在飞：token 预算熔断**——已实证 ModelResponse.result=list[BaseMessage]（usage_metadata 累计点）+ awrap_model_call 熔断口。关键设计已定：**预算必须跨 HITL 段**（resume 重建 middleware 清零计数）→ 累计落 RunStateStore（add_tokens 方法，同 tool_results 模式，sqlite/mongo/fake 三实现）；政策=agent env 默认（KOKORO_RUN_TOKEN_BUDGET）+ 未来 profile 覆盖位。下一步：storage 方法 TDD → TokenBudgetMiddleware → 装配 → 行为测试（超限→run.failed(TokenBudgetExceeded)）。
- 对抗复审子代理仍在跑（supervisor/storage/events/web_fetch 高危区），结果待验证并入。
- 用户裁定记录：token 熔断=agent 执法+namespace 政策；聚焦 agent 子仓。

- Date: 2026-07-04 (自主时段后半：入口级 skills + MCP wire 可读性 + 定时任务设计稿)
- **入口级技能包**（session 43e4e80）：AgentSpec.skills——选中入口时在 namespace 常挂之上追加（同路径去重保序）；动态 skills P1a 落地，P1b（消息级选择子）待产品面。session 151 tests。
- **MCP 结果 wire 可读性**（agent 186b333）：content blocks（list[{type,...}]）经 TypeAdapter 洗净后文本拼接上 wire（非文本块记 omitted 注记），不再是 Python repr。
- **定时任务设计稿**：docs/superpowers/specs/2026-07-04-scheduled-runs-design.md（提案待批）——触发器归 session（幂等键=schedule_id+fire_time）、创建归 agent 工具（前置改参首用例=既有 HITL edit）、409 跳过不排队。
- 门禁：agent 294 + session 151 + e2e PASS；全推送。

- Date: 2026-07-04 (自主时段：三真缺陷修复 + 深度体检报告)
- **①暂停 run 永久卡死（严重）**：认领 worker 崩溃后 control 流无人监听，resume 石沉大海。修：RunStateStore.list_paused（sqlite/mongo/fake 三实现+行为矩阵）+ 心跳收养 control 监听（consumer group 去重）。证：scripts/chaos-verify.py 6/6（SIGKILL A→B 收养→续走到终态）。agent dcf3fdc。
- **②wire 子代理 tools/model 静默丢弃**：wire_subagents 现按名解析实例（未知名 fail-loud）+ model 工厂实例化，缺省继承。agent 41d3773。
- **③失控无熔断**：KOKORO_RECURSION_LIMIT（默认 100）→ GraphRecursionError → run.failed。agent 5a4e886。
- **④sandbox 后端可选**：profile.backend（state|local_shell）；real-model-verify 全程 local_shell + 场景 E execute 审批→真 shell 回流，23/23。session bf14a8d。
- **⑤契约减法**：RuntimeContext 八个投机字段（user_id/site_id/workspace_id/project_id/recent_messages/summary/memory_scope/feature_flags）全链无产无消→移除，四仓镜像重生成全绿。
- **深度体检报告**：docs/superpowers/specs/2026-07-04-agent-deep-review.md——可插拔矩阵（仅 sandbox 闭集等 e2b、observability 单实现不抽象）、context 审计、动态 skills 分层答案（agent 已动态，缺产品面选择子，安全底线=只开放选择不开放定义）、memory 工具 vs CC 文件型辨析、下一段需求清单。
- 门禁：agent 293 + session 148 + contract 20 + e2e ×3 + real-model 23/23 + chaos 6/6，全推送。

- Date: 2026-07-03 (统一入口表 — general 一等入口，用户裁定)
- session resolve 重构（a698b43）：listEntries 单表 = 内建 general（人格缺省→agent 内置）∪ profile.agents（可覆盖 general）；缺省 entry ≡ entry=general；general 恒不作委派下属；下属无人格=结构破裂 fail-loud（替换 ?? "" 遮掩）。wire 零改动。
- 验证：session 146 tests（+5 入口表矩阵）+ tsc；跨栈 e2e PASS。studio 选择器（P1）枚举 listEntries 即可。

- Date: 2026-07-03 (Langfuse trace 点亮 — "等凭证"挂账清零)
- 自托管 Langfuse v3（compose 项目 kokoro-langfuse，web :3310，headless init 预置 pk/sk-lf-kokoro-local；redis/postgres/clickhouse/minio 全不占宿主端口）。用户 .env 已配三元组，trace 即开即用（UI dev@kokoro.local）。
- **scripts/trace-verify.py 7/7 PASS**：LocalFake HITL 双暂停全流程 → Langfuse API 断言 3 段 trace 同 kokoro_run_id + 同 sessionId 归组——HITL trace 连续性达成（连续性=可归组的多段，非单条长链）。
- 途中修正：session RunStatus 词汇是 active|terminal（我误猜 completed）；snapshot 以 active_run 缺席判终态。
- **业务编排状态答复**：V1 完备（通用主 agent + namespace 预设入口 + 委派三档 + 五面挂载全活）；swarm P2 后置。
- 剩余挂账仅：e2b 部署、canvas 产品面、tavily/zhipu key、music/platform、前置改参 normalizer（等首个真实用例）。

- Date: 2026-07-03 (skills 子系统实证 + 修活 — 最后一个未验证挂载面清零)
- **实证抓到真缺陷**：deepagents 原生 skills 渐进披露依赖模型 read_file 宿主路径，state 虚拟 backend 下读不到 SKILL.md（探针：源路径进 prompt 但清单 "No skills available yet"）——skills 子系统在默认部署形态下整个是死的。
- **V1 修法（全文注入）**：mounts.py 改 render_skills_prompt（lock sha256 fail-closed + ≤32k 上限 + 去重保序 + 全文渲染 ## Skills 段），worker 拼进 system_prompt；build_agent 移除死参数 skills=/memory=。升级路径（沙箱供给→回归渐进披露）已入 handbook 注记。
- 验证：单测 7 项矩阵 + 真图 system prompt 行为断言；**real-model-verify 场景 D：glm-5 遵循 namespace 挂载 skill 的标记约定，19/19 PASS**；跨栈 e2e PASS；agent 287 pytest + pyright 0。
- 五大挂载面（tools/mcp/subagents/memory/skills）至此全部四层验证（单测→e2e→真模型→真 UI 或 SSE）。

- Date: 2026-07-03 (web_search 真调用点亮 — searxng 自托管，零 key)
- 本地 docker 起 searxng（kokoro-searxng, :8888, --restart unless-stopped，settings 开 json format）；用户 .env 已配 KOKORO_WEB_SEARCH_PROVIDER=searxng + _URL——web_search 即开即用。
- scripts/real-model-verify.py 增场景 C（searxng 可达才跑，否则 SKIP）：**16/16 PASS**——glm-5 真模型经 provider 注册表调 web_search（tool.invoked/returned 非错误）+ 原 thinking/subagent 场景回归。
- 至此三 provider 中开放标准路径（searxng）全链实证；tavily/zhipu 适配器留解析级测试，等 key/资源包。registry 疑问澄清：web/memory 工具实例带装配政策不入常量表，registry 只登记名字（ASSEMBLY_TOOL_NAMES）。

- Date: 2026-07-03 (web 底层工具 + 三次分层纠正定型)
- **web_fetch/web_search**（agent 9bbfeda→56ab411）：fetch 恒挂载（httpx+bs4，SSRF 防御：DNS 解析后拒非公网/重定向逐跳复检/15s/1MB/24k；KOKORO_WEB_FETCH_ALLOW_PRIVATE=1 供 fake-IP 代理本机——用户机器实证 example.com 解析进 198.18.0.0/15）；search 配置即挂载（无 provider 不挂空壳），工具层零 vendor（inspect 执法测试），适配器注册表 tools/web_search_providers.py（tavily/searxng/zhipu 平权；用户 coding key 无 zhipu 资源包 429/1113 故默认不挂）。
- **用户三连纠正定型**（tasks/lessons.md"底层工具三问"）：①租户政策不进工具体（memory 改 make_memory_tools(scope) 装配注入）②vendor 不进工具层（web_search 通用化）③配套件归 tools/ 不占一级目录。内建子代理原则同定：只收带真实工具的真能力，researcher 空壳已删，真栈委派走 namespace 预设（12/12 PASS）。
- streams/protocol.py 语义打磨（d555d81）：五方法契约语义写进接口（consumer-group 分摊/ack-收养/至少一次/cursor 不透明）。
- 门禁：agent 285 pytest + pyright 0 + ruff；跨栈 e2e PASS；真抓取 PASS；CI 全绿。
- 用户 .env 已配好：KOKORO_OPENAI_REASONING=1 + 流式恢复 + ALLOW_PRIVATE=1（本机 thinking/web_fetch 即开即用）。
- **真栈浏览器全家桶走查 ✅**（glm-5 + 本地四件套）：①thinking 真渲染（"处理过程"折叠条含真实推理文本）②save_memory 工具行 + 终答 ③**新会话** search_memory 命中上会话存的深色模式偏好（跨会话长期记忆 UI 级实证）④web_fetch 抓 example.com 并正确摘要；console 零错误。截图 walkthrough-{1,2,3}-*.png（playwright 输出目录）。途中实证：浏览器必须走 http://localhost:3000（session CORS 默认源），127.0.0.1 会被拦——属预期行为非 bug。

- Date: 2026-07-03 (清零轮完成 — **✅ C 记忆 store + 全部已知妥协/盲区清零**)
- **C 长期记忆**（agent 2e03e72/55eab21/47b35c9）：make_memory_store 三后端与 checkpoint 对齐（memory=InMemoryStore / sqlite=AsyncSqliteStore(<path>.store 独立文件防撞) / mongo=官方 langgraph-store-mongodb，集合 kokoro_agent_memory）；save_memory/search_memory 恒挂载核心工具，store 前缀 (RunContext.namespace, "memories")——真图测试：跨 run 可读 + 双租户隔离 + 错误上 wire + schema 边界矩阵。
- **截断显性化**（四仓 "Make wire truncation explicit"）：契约 tool.returned 增 per-kind 可选 "truncated?"（缺席=完整，true=4000 护栏截断）；clip_result 返回 (text, bool)；awaiting 帧仅展示裁剪无 truncated 位。14 镜像重生成，golden/agent/session/web 门禁全绿。
- **豁免清剿**（agent 04f1400）：3 文件 5 规则 → 2 文件 2 规则。结构性消灭：build_agent 去泛型（唯一 schema=RunContext，YAGNI，StateLike/reportPrivateImportUsage 整个消失+双分支合一）；test_context_injection 改 StructuredTool 直构（@tool 重载含 Unknown）；mcp_live 用 TypeAdapter 洗净 content blocks。幸存 2 处（deepagents 未解 ResponseT / BaseTool.ainvoke 裸 dict）锁进 tests/test_boundary_pragmas.py allowlist——新增豁免必改测试=显式评审；type:ignore 行内标记全仓为零同测执法。
- **真栈盲区压实**（agent 9585431 + 父 29fce91）：实证 GLM 原始 wire 有 reasoning_content(1541 chars) 而 ChatOpenAI 明文拒收（上游 API scope）→ KOKORO_OPENAI_REASONING=1 切 ChatDeepSeek（官方抽取，对 GLM 实证出 reasoning 块）。scripts/real-model-verify.py（glm-5 真栈）：**12/12 PASS**——thinking.delta 全链 + subagent.started/finished/text（researcher, built-in）+ token_usage。途中抓到 provider 内容过滤 400（错误码 1301）被正确 fail-loud 成 run.failed 带原文——管线行为正确，换话题即过。
- **设计决策入册**（handbook 11 号新注记）：review void-on-terminal 法则 / wire 截断法则 / namespace profile JSON=V1 配置真源+升级路径 / 豁免 allowlist 政策 / 记忆 store 归属。
- 门禁：agent 257 pytest + pyright 0 + ruff + 边界 allowlist；session 141 + tsc；web tsc + lint；contract golden 20 + check 14 镜像；跨栈 e2e PASS ×3 轮；真模型 12/12。
- **剩余=全部等外部条件（非缺陷）**：e2b 池（等部署）、Langfuse（等凭证）、canvas/artifact_ref 生产者（P1 产品面）、前置改参 normalizer（等首个真实工具用例）、music/platform（用户令后置）。
- 计划文档：docs/superpowers/plans/2026-07-03-zero-debt-closeout.md（7 task 全勾）。

- Date: 2026-07-03 (agent 自身完善 A+B 完成 — RuntimeContext 注入 + subagent_create 执法)
- **A RuntimeContext 注入图运行时**（agent f5312bb）：create_deep_agent(context_schema=RunContext) + 每 run context 值经 astream_events(context=) 全链透传（invoke/resume 双路径）；工具/middleware 经 get_runtime/ToolRuntime.context 读 namespace/session/run 身份（真图行为测试固化）。泛型坑记录：deepagents ContextT bound=StateLike（langgraph.typing 未 re-export，最窄文件级豁免沿 build_agent 先例）；Optional 掺未 bound 泛型解不动→拆分支绑定。
- **B subagent_create 执法**（agent 9a3cef1）：deny=仅声明集（catalog+wire 预设）可被 task 委派，general-purpose 临时创建 fail-closed 且错误携声明集；ask=task 进 interrupt_on 走现有审批卡（pending 识别集同步含 task）；allow=放行。行为矩阵测试全覆盖。
- 门禁：agent 227 pytest + pyright 0 + ruff；跨栈 e2e 回归 PASS；已推送 CI。
- **余项 C**：memory store 接线（create_deep_agent(store=)，先实证 langgraph sqlite/mongo store 可用性，namespace 前缀隔离）——spec 2026-07-03-agent-self-completion-design.md 已载。
- Date: 2026-07-03 (收尾清账完成 — 系统进入稳定待命态)
- 用户定调：编排=通用组装+拓展位，已达终态不再加建。收尾三件全清：① resume 续段不再重复宣告 run.started（agent 6ff2012，emitter.at_start）；② result_review 终态收口文案修正"工具已执行"（web f859345）；③ 真栈浏览器走查 review 卡全流程 PASS（问答卡答复→审批卡批准→审核卡展示真实结果→替换文本提交→write_file 显"已人工答复"→终文，console 零错误，截图在 scratchpad）。handbook 11 号补 namespace profile/entry 实现注记。
- **当前态**：四仓 main 全绿全推送，CI 绿；已知缺陷清零；agent 先行余项全部在等外部条件（真实工具用例/部署/凭证）。等待用户输入：web/产品规划（canvas、studio surface）或 platform 接入（music job 链）。
- Date: 2026-07-03 (agent 先行①②完成 — MCP live + PEL 死信收养)
- **MCP live 集成测试**（agent 01bee20）：进程内 FastMCP(streamable-http, stateless) fixture 服务器 × langchain-mcp-adapters 真 HTTP 往返——白名单过滤/mcp__ 重命名/真调用（返回标准 content blocks）/不可达 fail-closed，全部实证且离线进 CI。pyright 收口沿 build_agent.py 先例（文件级最窄豁免，BaseTool.ainvoke 泛型未参数化属第三方边界）。
- **PEL 死信收养**（agent 3c00387）：redis subscribe 空转间隙 XAUTOCLAIM 收养 idle 超阈值（默认 60s，可配）的未 ack 条目——崩溃消费者的 PEL 不再永久悬挂；下游幂等去重吸收重放。集成测试：A 读未 ack"崩溃"→ B 按 50ms 阈值收养。
- 门禁：agent 233 pytest + pyright 0 + ruff；跨栈 e2e 回归 PASS；CI 绿。
- agent 先行余项：前置改参 normalizer（等首个真实工具用例）、e2b 实例池（等部署）、Langfuse HITL trace 连续性（等凭证）。
- Date: 2026-07-03 (push + CI 首跑全绿 + 真模型冒烟 — **✅ 地基钉死**)
- 四仓 main 全部 push（agent 39cce02 / session a9ec14e / web d452370 / 父 8cf102e）；GitHub CI 四仓 success（父仓跨仓契约门禁对真远端 main 首跑即绿）。途中修复：web CI 旧 bun 工作流换 npm 四门禁；mac 生成的 package-lock 缺 linux rolldown binding（npm/cli#4828）→ 清库重生成。
- 真模型冒烟（智谱 glm-5 经 openai 兼容端）：全链 PASS，token_usage {6091/58} agent→session→SSE 贯通（LocalFake 盲区①验掉）。冒烟揭示并已修：v2.1 后模型档位归 session model_policy，agent 的 KOKORO_MODEL env 已死 → README/.env.example/LocalFake 文案同步（39cce02）。thinking 通道（需 reasoning 模型）与 subagent 事件真栈仍未验。
- **agent 先行路线（用户定：agent 独立推进，web 等产品规划）**：① MCP live 集成测试（本地 FastMCP streamable-http fixture 服务器 + LocalFake 脚本调 mcp__ 工具，离线可跑）；② PEL 悬挂清理（XAUTOCLAIM）；③ 前置改参 normalizer 挂点（等首个真实用例如定时工具）；④ e2b 实例池（等部署需要）。
- 操作教训：shell cwd 会被 harness 重置——rm -rf 类命令必须绝对路径+同命令内 pwd 验证（本次 rm 落在 Python 仓无害，纯侥幸）。

- Date: 2026-07-03 (namespace profile + 具名 agent 入口 — **✅ 编排最小闭环落地**)
- 三层所有权定案：namespace 拥有 skills/mcp/agent 预设/模型策略/permissions；session 拥有 sandbox 工作区(thread checkpoint 天然隔离+延续)/消息史/暂停点；run 拿 RuntimeConfig 快照。
- 实现（spec: 2026-07-03-namespace-profile-and-entry-design.md）：契约 +RuntimeConfig.system_prompt?/+body.entry?（2ab6b10）；agent 一行消费 entry 人格（273c47e）+ control 流终态 NOGROUP 竞态修复（346bb32）；session src/namespace/{profile,resolve}.ts（strict schema + JSON loader fail-fast + 解析矩阵），start-message 硬编码默认档物理迁入 resolver，context.namespace 改租户级（KOKORO_NAMESPACE），解析先于任何落库（a9ec14e）。
- 语义：entry=X → X 人格作主 agent、其余预设仍可委派；缺省 → 通用 agent + 全预设为下属。ask_user_question 改名与 result_review 均已全链。
- 验证：agent 230 pytest+pyright 0+ruff；session 141（含 12 项 namespace 矩阵+双租户隔离断言）；跨栈 e2e 30 项 PASS（entry wire 断言直读 redis 请求流 + cancel 收束补覆盖）。
- 待办：真栈浏览器过一遍 review 卡与 entry（可选）；push+CI 首跑仍是最大空洞；e2b 实例池/DB 配置源/web entry UI 后续。

- Date: 2026-07-03 (工具结果审核暂停 result_review — **✅ 四层全链完成**)
- 用户定义两类通用拦截：工具前人确认（=已有 HIL 审批，edit 即"确认并改参"）+ **工具后结果审核（新做）**；明确不做"重定向到其他工具"。
- 实现（spec: 2026-07-03-result-review-pause-design.md）：契约 awaiting_kind+result?/Permissions.review_tools/PendingPause.result?（生成器新增 "字段?" 局部可选标记；http.yaml 的 enums 副本要与 events/control 同步——这次踩到）；agent ToolResultReviewMiddleware（langgraph 原生 interrupt + RunStateStore tool_results keep-first 缓存防 resume 双跑）+ 投影 raw returned 抑制 + supervisor 裁决直发（approve/respond 带 responded、reject 带 rejected）+ 混帧 fail-loud；session respond 放宽至 result_review + pause 透传 result + KOKORO_REVIEW_TOOLS 部署配置 + **pause_id 加 kind 维度**（审批→审核双暂停碰撞，e2e 抓获）；web review-card 第三卡（采纳/替换/拒绝，171 tests）。
- 门禁：agent 217+pyright 0+ruff @ 50948e2；session 128 @ f27fcd8；web 171+build @ 07851a6；契约 @ 2dcb82d；跨栈 e2e 25 项 PASS（含串联双暂停实证缓存防双跑）。
- 待办残留：names.py 解散提议（并入 registry + mcp_tool_name 归 mcp/）等用户点头；review 卡真栈浏览器走查未做（wire+组件测试已覆盖）；middleware 前置改参与 artifact_ref 后置加工仍是 P1。

- Date: 2026-07-03 深夜 (合入 main + 真栈浏览器走查 — **✅ 全部完成**)
- **四仓 squash 合入 main**：parent 2bc8d50 / agent 6b992c0 / session 75a9025→d3c84fd / web ab119ac→f836a99；main 上全门禁 + 跨栈 e2e (23/23) 复验绿。rewrite/v2 分支保留未删。
- **真栈浏览器走查**（agent LocalFake hitl + session:3101 redis db13+mongo + web:3002 Playwright）主路径全通：发消息→ask_user 问答卡（选项+自由输入+取消）→respond→write_file 审批卡（仅 批准/拒绝，respond/edit 正确隐藏）→批准→最终文本→composer 恢复；暂停中刷新 snapshot 水合后卡片直接可操作。
- **走查抓获并修复 2 个真 bug**：① Mongo messages 按 created_at+随机 id 排序，同毫秒 user/assistant 对顺序随机 → 店内单调 ordinal（session d3c84fd，行为套件回归双后端）；② agent resume 后 tool.invoked/returned 的 segment 兜底漂移致 web 工具行重复 → reducer 工具步按 tool_id 归并（web f836a99，segment 漂移免疫回归测试）。修复后真栈复走全部正确。
- **注意**：用户本机 3000/3001 有其自启的旧代码 dev 服务未动；e2e/走查容器与进程均已清理；截图存 scratchpad。
- **待用户**：agent 侧 segment 漂移的根治（invoked/returned 应继承 awaiting 的 AIMessage segment——web 已免疫，agent 修复属锦上添花）记为后续小项。

- Date: 2026-07-03 (/goal 三仓彻底重写 v2 + handbook 对齐 v2.1 — **✅ 全链完成，四仓 rewrite/v2 分支待合入**)
- **v2 重写**：contract/ 重建为 spec 四部立法（events/control/streams/http）+ 确定性生成器 + check.py 字节门禁（verify.py 正则解析器/agent_wire 双 master/docs/protocol 手写规范全部退役）；三仓按蓝图推倒重建（agent 执行链路布局+TTL 租约+claim-before-emit、session contract/relay/store/transport/http 五模块+DB-first、web contract/core/engine/ui+显式状态机）。
- **用户中途纠偏（关键）**：① 必须以 docs/kokoro-handbook（ADR-004/11/12/03/modules）为法——v2 撞了禁止项（conversationId/permissionMode）、错杀了 handbook P0 脚手架；② 业务编排=通用 Agent 层级调度专业能力（job 工具/subagent/skill/MCP），Studio=专业 agent 作主 agent，swarm 降 P2；③ 禁 workflow/team 模式（三线并行撞 session limit 全灭），改主控直施 + 单 subagent 串行。教训均入 memory。
- **v2.1 对齐**：RunRequest→{run_id,thread_id,input,runtime(RuntimeConfig),context(RuntimeContext 含 namespace),trace}；事件词汇 message.*，raw 14/browser 15（session 合成 session.created/run.created 带真实元数据）；独立 control 流；session 恢复 pending_pauses 校验（自有投影非第二真理源）+ 五集合 + snapshot 端点 + 准入/幂等；agent 回归 handbook 布局 + ToolPolicyMiddleware（真实行为）+ skills mount(lock 校验 fail-closed) + MCP(langchain-mcp-adapters, live smoke 单列) + namespace 隔离（checkpoint thread_id 前缀）+ respond↔ask_user 双向 fail-loud；web snapshot-first 水合 + 双 HITL 卡（approval-card/ask-user-card）+ decision_id 幂等。
- **跨栈 e2e（scripts/e2e-v21-gate.py，真 redis+mongo）23/23 绿**，途中抓获并修复 3 个真跨栈缺陷：wire 上 optional None 被序列化成 null 被 zod .optional() 拒收（agent emit exclude_none + 回归测试）；session 默认审批集缺 write_file；LocalFake hitl 脚本无接线开关（KOKORO_LOCAL_FAKE_SCRIPT=hitl）。
- **门禁终值**：contract golden 20 + 14 mirrors 字节稳定；agent 208 pytest(redis/mongo 实跑)+pyright 0+ruff @ 83f40d0；session 127+tsc+eslint @ 2d54a73；web 166+tsc+eslint+build @ 8ec9932；父仓 @ 5fae9c6（含 handbook 三处实现注记反哺）。
- **待用户**：① 四仓 rewrite/v2 合入 main 的方式（merge/squash/PR）与旧数据清库确认（新 schema 与旧 Mongo 事件史不互通，已按"清库重来"实施）；② 后续单列：swarm P2、music 垂类 job 工具（编排参考实现）、MCP live smoke、真浏览器联调走查。
- 注意：docker 容器 kokoro-e2e-redis/mongo 已停；handbook 里用户未提交的 3 处文档地图链接已随 docs 提交一并入库。

- Date: 2026-06-20 (用户驱动 DDD 审查闭环 — **✅ 4 PR 全合入 main + 三仓 main 同步**)
- **承上(/goal 深度重构后续)**。用户从 `agent_builder.py` 观察「多个相似 class+函数混在一起、本质 dataclass」切入,引出系统性 DDD 审查:依赖方向(domain←application←infra←interfaces)+ 文件内职责混杂 + 框架类型钻进签名 + God object。
- **PR#20 agent 端口上移 application(`36e3700`)**:`agent_builder`(infra)此前既定义 application 消费的强类型 port(`EventStreamingAgent`/`AgentInvokeInput`)又混 builder 构造,致 application/agent_factory+run_agent 反向 import infra 取 port(违 DIP)。新建 `application/agent_ports.py` 承载 port;infra 只留框架接线+builder+内部契约 `AsyncRunner`(仅 infra runtime_subagent 消费,正确留 infra)。
- **PR#21 JsonObject 下沉 domain(`8c151bd`)**:同类——`infrastructure/json_types` 混基础类型 `JsonObject`(dict[str,JsonValue])+洗净逻辑,application/request_admission 反向 import 取类型。类型下沉 `domain/json_payload.py`(最内层单一来源),infra 只留 validate/clone。
- **PR#19 H3 worker 级集成测试(`d9a166f`)**:补 H3(control 断连不伪造 reject)唯一覆盖缺口——serve 真实路径+gated fetch_url+control 流 subscribe 立即耗尽 → 断言 `run.completed{cancelled}`+无伪造 reject。
- **深层语义审查(4 个并行只读 agent,一仓/层一个)**:agent application=PASS(framework 类型均 ACL 边界豁免);agent domain+infra=PASS(domain 纯净;translator 190/redis_stream 164 行核实为单一职责必要体量,非 God object);session=1 low → **PR#11 修**;web=1 med → **用户定保持**。
- **PR#11 session start-run 拆分(`2cb8590`)**:`start-run.ts`(112行)混 4 链路 → 拆 stream-names/send-run-control/relay-run/start-run,importer 直指新文件无 barrel。typecheck/lint/109 test。
- **判断保持(非债,经核实)**:web `transport.ts` I/O 实现在 application 层(med)——它同时导出端口契约类型(被 reply.ts 当端口)+I/O 实现,整体迁 infra 反造 application→infra 反向依赖,干净拆需 DI 管线;**用户选保持**(与 agent 仓 application 务实编排具体 infra 的先例一致,反过度设计),审查在案。大量 application→infra 编排调用(make_chat_model 等)同理判定务实折中,不报。
- **验证**:每 PR 过各自类型门+全量测试(agent mypy 59/pyright 0/252 pytest;session typecheck/lint/109;零遮掩)。三仓 main 同步:agent `8c151bd`、session `2cb8590`、web `dc947d3`。**结论:三仓 DDD 分层健康**——domain 纯净、依赖内向、无 God object,剩余为已评估可接受的务实折中。

- Date: 2026-06-20 (/goal 三仓深度架构重构 — **✅ 8 重构 PR 全合入 main + 组合态 + 跨栈 e2e 全验证**)
- **目标**(用户 /goal,自主无交互):三仓能力闭环 + 极高质量(DDD/职责单一/无 God 文件)+ 架构梳理 + 禁遗留兼容/敢重构 + 多方案择优。
- **方法**:3 个只读架构审计 agent(一仓一个,通读全源)→ ~30 findings + topRefactors → 8 个文件互不重叠重构 worker(并行 worktree)→ 逐仓组合态验证 → 合入 main → 跨栈 e2e。
- **kokoro-agent(4 PR,#15-#18 → `2381450`)**:H1 `drive_agent_events` 143 行 God 函数拆 TextAccumulator+SubagentRouter;**H3 正确性 bug 修复**(control 流终止抛 `ControlChannelClosed` 不再伪造 reject 回灌模型,TDD);H2 control.py 三层拆分(ControlMessage→domain、rejection_result→application、IO 留 infra);M1 **worker.py 222→31 行**(抽 RequestAdmission+RunSupervisor);M2 终态事件下沉 application 工厂(消手搓 seq);M3 不可变 SubagentCatalog 值对象(消每事件重建+三处校验重复);M5 adapter 203 行按读取目标拆 header/tool_input/message;L1 SYSTEM_PROMPT 外置。组合态 mypy 57+pyright 0+**251 pytest**+ruff+零遮掩。
- **kokoro-session(1 PR,#10 → `0f1af00`)**:R1 删 ReplayStore.read+mirror 死抽象(多进程语义破裂、零调用);R2 StreamProtocol 端口删 readAll/close(零调用);R3 HTTP query 入参 Zod 化+统一路由风格;R4 抽 sse-endpoint.ts;R5 MemoryStream lastIndex 续读消 O(n²)。typecheck+lint+**109 test**。
- **kokoro-web(3 PR → `dc947d3`)**:F1 reducer 616 行拆 types/state-mutations/thread-projection(applySessionEvent 14 if→switch+穷尽守卫,公开 API 不变零 importer 改动);F7+F8 抽 useTransportSession 收敛在途句柄+消 4 处重复复位+5 裸 ref 透传+eslint-disable;F2 composer 拆 expand-dialog/mode-options;G1-G3 悬空能力(附件/语音/搜索)改 disabled 消误导;F11 Zod 双参。typecheck+lint+**255 test**。
- **验证**:逐仓门 + 三仓组合态(本地合分支跑门)+ **跨栈 e2e 复验**(agent→Redis→session→SSE 八类事件按序全跑通,深度重构后 live loop 未破)。
- **多方案择优的 deferred(有理由,非回避)**:control schema codegen——三仓 schema **当前实证一致**(approve/reject/cancel+args?),full codegen 把 3 字段、§H 故意手定的 schema 塞进 event-shaped 生成器+动三仓生成物,收益<风险、不成比例,记为后续(真要做按 contract codegen 单源);web 显示 timeout/cancelled(契约 ripple,见前);#2 tool_id 精确匹配(langchain 限制)。

- Date: 2026-06-20 (HITL 收尾:超时设计修复 + 审批可编辑工具参数 — **✅ 4 PR 全合入 main + 跨栈 e2e 复验**)
- **承上(/batch 收尾后续)**。先做 1-2-3(e2e/§H/DDD):跨栈 e2e 复验大重构后 live loop 八类事件按序全跑通(脚本 `/tmp/kokoro-e2e.sh`,LocalFake 免密);DDD 剩余 survey 发现已基本达标(死文件零、ports 已在 application 层、kebab-case web 已合规、session 3 个点分测试名改 kebab=PR#8);§H 多项过时已反向修正(#7/#9/#5 已完成)。
- **用户两条 HITL 指令**:① 审批超时设计错误→移除;② HITL 暂停时 tool 参数可编辑。
- **#4 超时修复(agent #12 `cd8598a` 前)**:`drive_agent_events` 的 `asyncio.timeout(120)` 包住整个 astream(含审批等待),用户审批超 120s 被误杀成 run.failed。移除该 wall-clock(HITL 须无限等用户,放弃靠 cancel;fetch 工具级截止保留);`TimeoutError`→显式 `run.completed{status:"timeout"}` 不混同 reject。TDD,全量 241。web UI 区分 timeout 因 generated domain 丢 status、属契约后续(真超时已极罕见)。
- **#10 审批可编辑工具参数(agent #13 / session #9 / web #11)**:control 协议(手定非 codegen)加可选 `args`——approve 整体替换工具参数。agent `ControlMessage.args`+`await_decision` 返回完整消息+gate approve 用编辑参数执行(向后兼容);session `controlEventSchema.args`+`?args=<json>` 端点透传(非法→400);web 待批参数 `<pre>`→可编辑 `<textarea>`,approve 解析草稿沿 onToolDecision→sendToolDecision→sendRunControl 回传(非法 JSON 本地拦+提示)。三仓各自 TDD(241/108/257),跨栈 e2e 复验 loop 未破。
- **web 可编辑 UI 撤回(web #12 → main `2b03a28`)**:用户定——统一 JSON textarea 对所有工具不合适,默认简单只读审批,**后续按 tool 定制 UI**。撤回 web#11(回只读),**保留 agent#13+session#9 协议地基**(control args 通道 dormant 待 per-tool UI 调用)。
- **状态**:本会话 5 PR 合入 main(agent `cd8598a`/session `daec14a`/web `2b03a28`),三仓本地 main FF 同步,0 open PR,无孤儿进程。**判断暂缓**(顺应用户「keep simple」):① web 显示 timeout/cancelled(需 contract `run.completed` render 加 status 重生成——cancelled 现有本地 path、timeout 罕见,契约 ripple 暂不值);② #6 plan 模式语义(含 read-only vs 交互审批的产品决策,不擅自定)。两者记为 follow-up。

- Date: 2026-06-19 (三仓 /batch 全面打磨 agent/web/session — **✅ 16 PR 全部合入 main + 真实 main 验证全绿**)
- **承上**。用户 `/batch`「全面打磨 kokoro-agent web sessions,严守 DDD+语言特性+顶级优雅」+ ultracode。只读审计 workflow(36 个 Explore agent,逐文件对标三仓 CLAUDE.md)产出 27+8+7 条真实发现 → critic 去重 → **16 个主题化、文件互不重叠工作单元**,每单元独立 worktree 后台 worker(实现→code-review→测试/双类型门→TDD 硬化→PR)。
- **关键操作坑(已记 memory `kokoro-batch-worktree-orchestration`)**:① 跨仓隔离须协调端自建 worktree(`Agent isolation` 只对 CWD 所在仓);② 后台 agent CWD=kokoro-web 会加载其 scope CLAUDE.md 致空跑,prompt 须中和;③ web 未提交 HITL WIP 先提交 checkpoint(`f864e8f`)+ 推 `hitl-wip-base` 作 PR base(不直推 main)。
- **16 PR(全部门绿 + code-review)**:agent `#6-#11`(base main)、session `#4-#7`(base main)、web `#4-#9`(base `hitl-wip-base`,已 squash 合入,组合 tsc/eslint/255 vitest 绿)。
- **顶级 follow-up**:#1 真零遮掩(mypy 配 `python_executable=.venv/bin/python` 让其对 venv 解析 → 删 agent_builder `type:ignore`,顺带 yaml override;并入 #11);#2 cancel 功能完整(interactive_gate 遇 cancel 抛 `CancelledError` 让 run 级取消独占终止,TDD;并入 #9)。**#3 单列后续**:todo-bar 稳定 id 需动 `contract/events.yaml` 三仓重生成 + reducer(收益小于风险,暂缓)。
- **组合态本地实证(纯本地分支,未推 main)**:agent 6 PR 零冲突 → mypy+pyright 双绿 + 240 pytest + src 零遮掩;session 4 PR → SE-1/SE-3 `http.ts` 冲突=1 行 import 取并集(已验证),typecheck/lint 绿 + 106 test。
- **✅ 已合入 main(用户明确授权后执行)+ 真实 origin/main 验证全绿**:
  - **agent**:6 PR squash 合入(`6c51ba6..d3950d2`)→ origin/main 实证 mypy+pyright 双绿 + **240 pytest** + src **零遮掩**。
  - **session**:4 PR 合入(`3b975aa..962983b`)→ SE-1/SE-3 `http.ts` 冲突由我本地 merge-main 解并集 + push 后合 → origin/main 实证 typecheck+lint + **106 test**。
  - **web**:`hitl-wip-base`(HITL 快照 `f864e8f` + WB-1..6)经 PR#10 `--merge` 合入(`4eb8627..95b3670`)→ origin/main 实证 tsc+eslint + **255 test**;`hitl-wip-base` 分支已删。**注意:main 现含用户"进行中"的 HITL 快照**(测试全绿、有集成覆盖),用户可在 main 上继续 HITL。
  - **功能层验证(超单测/类型门)**:web `next build` 生产构建成功(SSR/静态页 4/4);session 启动冒烟绑 `:3199`+连 Redis(PONG)、脏端口 `not_a_number` 运行时回退 `:3001`(SE-2 Zod `.catch` 真生效);agent import 冒烟 + worker 测试覆盖。
  - **跨栈 e2e 复验(2026-06-20)**:agent(LocalFake)→Redis db15→session(:3001)→SSE,curl 驱动真实 DeepAgents run,八类事件按序全到(session.created→run.created→todo.updated→tool.invoked→tool.returned→message.delta→message.completed→run.completed)——大重构后 live loop 未破。脚本 `/tmp/kokoro-e2e.sh`。顺带反向修正 §H 过时项:#9 有界已完成、#7 记忆已接线(thread_id=conversation_id+InMemorySaver)、#5 control POST 失败已处理。
  - **遗留**:#3(todo-bar 稳定 id,需 `contract/events.yaml` 三仓重生成 + reducer)**判定不做**——跨三仓契约波及大、收益仅一个可能不显现的 React key reconciliation 边角,风险>收益,单列独立后续;P0-2 轮换 `.env` zhipu key(沿用);用户本地各仓 `git pull` 同步 main。

- Date: 2026-06-19 (kokoro-agent worker.py + agent_builder.py 打磨 — **已推送 origin/main** `9b9e951..6c51ba6`)
- 用户「继续打磨 worker.py 和 agent_builder.py」。串行亲自,ruff/mypy0/pyright strict 0/202 passed,redis 实跑。提交 `6c51ba6`。
- **worker.py**:抽 `_admit_request`(parse → 非法发 run.failed → 去重 → 登记)消除 `_handle_request`(顺序路径)与 `serve`(并发+cancel 路径)的重复准入逻辑,去重单一出处;ProcessedRunIds docstring 压 1 行。
- **agent_builder.py**:`AsyncRunner.ainvoke` 参数 `input`→`payload`(避免遮蔽内置);`-> object` 补 WHY(runner 结果是进程内不透明对象,调用方按需收窄);Any-view 注释专业化。
- **刻意未改并标注(非 timid)**:`_run_with_cancel` 取消时补发的 `run.completed{status:cancelled}` 用 `seq=0`(破坏单调性),但 `agent_event.py` 契约规定 session 端归一化排序、agent seq 仅建议值,故大概率无害;正确赋 last_seq+1 需 worker 跟踪 driver 计数器(跨 driver/worker)且触 session 契约(越界),已留给用户确认 session 排序方式后再做。
- **状态**:`9b9e951..6c51ba6` 已 push origin/main,同步,工作区仅 `.claude/`。**待用户**:① 确认 session 是否按 seq 排序(定夺 cancelled seq 改动);② P0-2 轮换 `.env` zhipu key。

- Date: 2026-06-19 (kokoro-agent 全仓审计 + 注释专业化 + 硬质量改 — **已推送 origin/main** `78a3a1a..9b9e951`)
- **承接上一条**。本会话续做全仓「每模块位置 + 代码质量」审计与打磨。**串行亲自**(并行 worktree 在紧耦合类型脊柱上不成立:共享文件冲突 + 各自 commit/PR 无法独立合并)。每步 ruff/mypy0/pyright strict 0/202 passed,redis 实跑。
- **用户两条关键反馈(已记 memory `kokoro-style-comments-and-no-compromise`):** ① 注释「非专业」——口语/江湖气/说教(如 constants.py docstring 写「勿往此堆」立规矩);② 「为怕动代码而故意兼容,不应该妥协」。据此:注释去口语保 WHY、该硬改的硬改。
- **`tool_names.py` 归属(用户三次质疑,逐次纠正自己):** 先答「移进 tools/」→ **实证推翻**(`import tools.<子模块>` 会触发 `tools/__init__` 连带加载 langchain+httpx;`import tool_names` 零重依赖)→ 结论「零依赖中立叶子,留原地」;用户最终要 `constants.py` 约定 → `git mv` 成 `infrastructure/constants.py`(`5689923`),保留零依赖性质 + 限定 docstring。
- **审计方式**:3 个只读 Explore/general 子代理通读 45 文件(分层/质量、注释专业度/妥协代码),我逐条**过滤 sonnet 噪音**——驳回约 20 条 textbook/判断错误并留痕:`@tool`(BaseTool vs StructuredTool 脊柱,实测更差)、interactive_gate「infra→application 违反分层」(搞反了,Clean 架构依赖指向内核,验证了 StreamProtocol 上移)、anthropic 双分支合并(实测 `ChatAnthropic` 拒绝 `api_key=None`)、删 static_gate sync(是返回拦截文案的真实现非桩)、去 fetch 字节封顶(会废解压炸弹防护)、settings 加 provider↔key 交叉校验(破坏 env-key 回退)、各处加缓存(非热路径)、注释改英文(项目要中文)、constants 杂物抽屉(私有常量就近放原则不变)。
- **真改落地(`c293805` + `9b9e951`):**
  - `c293805` control.py 补 module docstring(全仓唯一缺)+ await_decision reject 兜底 WHY;policy.py 删冗余 `_StringList` 双重校验。
  - `9b9e951` **硬质量**:`settings.provider` `str`→`Literal["openai","anthropic"]`(`_split_model_spec` 显式 return 收窄无 cast、配置期 fail-fast、删死 `case _`,测试恢复原样);`agent_factory` 内联 2 个单次薄包装;`run_agent` 删单用中间变量;`adapter` 3 段重复 match/case → `_str_or_empty` 助手(15→5 行);`redis_stream.subscribe` 删重复二次 `clone_event`;`chat_model` anthropic 分支补 WHY(实测必要)。**注释专业化**:~15 处去口语("废掉/饿死/不死/撞名/绝不让/裸 dict/拍平/就该/杜绝")为干练书面语,保留中文 + WHY。净 -30 行。
- **状态**:3 提交**已 push origin/main**(`78a3a1a..9b9e951`),`main...origin/main` 同步,工作区仅 `.claude/`。严守 kokoro-agent only。**待用户**:P0-2 轮换 `.env` zhipu key。

- Date: 2026-06-19 (kokoro-agent DDD 严格分层 + 工具/事件打磨 — **已推送 origin/main** `c1d8241..78a3a1a`)
- **承接上一条**。本会话 `/goal`→`/batch` 顶级打磨,议题:① 工具没用 langchain idiom(`@tool`/BaseTool);② 自定义 event「留位置」;③ DDD 每层严格职责分区(用户反复强调「严格分明/方便维护/舒坦」);④ 常量归属。**串行逐模块**(未开并行 worktree)。
- **判断力收口(非盲从,均实证/留痕):**
  - **`@tool` 驳回**:实测 `@tool` 静态返回 `BaseTool`(运行时才是 StructuredTool),且装饰器本身 pyright `partially unknown`。整条工具链钉死 `StructuredTool`(权限门 `static_gate`/`interactive_gate` **重包**工具、读 `.func/.coroutine/.args_schema`)。改 `@tool` 要降级脊柱或逐个 `cast`——用 2 条解释清楚的 ignore 换一堆 cast,**是退步**。保留 `from_function`。
  - **`event_payloads` 返回 dict 非偷懒**:`AgentEvent.payload` 在生成契约里就是 `dict[str,JsonValue]`。实测 TypedDict **类型不兼容**(mypy+pyright 都拒),Pydantic 是**热路径(每 token delta)仪式**。类型安全由「强类型 domain 输入 + `tests/stream_contracts.py` 镜像断言」兜住。
  - **全仓 DDD 审计**(Explore 子代理通读 45 文件)裁决:domain 用 pydantic = **铁律要求**(`agent_event.py` 生成契约 / `RunRequest` 外部输入校验边界),**非违例**;Composition Root(`agent_factory`/`run_agent`)直依 langchain 具体类 = 组装层职责,藏成抽象是投机仪式,**驳回**;全局 `constants.py` = junk-drawer **反模式**(`_REDIS_FIELD` 这类私有细节就近私有放,只有跨子系统共享身份才抽小模块如 `tool_names.py`)。
- **提交(每个 ruff/mypy0/pyright strict 0/202 passed 全绿,redis 实跑 PONG):**
  - `907480d`+`2e0be2a` *(上轮 /goal)* `_Contract` 基类 DRY(17→1)、抽 `event_payloads.py`(SRP)。
  - `810d692` `stream_events` 拆 SRP:leaf `tool_names.py`(共享工具名身份单一真理源,`RESERVED_TOOL_NAMES` 改为派生、杀 `write_todos`/`task`/`agent` 重复字面量)+ `events.py`→`parsed_event.py`(只留 LangChain ACL DTO)+ `TOOL_RESULT_MAX_CHARS` 下沉 translator;测试镜像 `contracts.py`→`tests/stream_contracts.py`(出生产 API);`runtime_subagent` 去假 sync 桩→纯异步。
  - `1b56587` 抽 `RunEmitter`(消 driver ~15 处事件构造样板 + 「新增 event」5 步配方 docstring);driver/event_payloads **直依 `domain.stream_intent`**(不再经 infra 洗白)。
  - `78a3a1a` **`StreamProtocol`/`StreamItem` 上移 `application/event_stream.py`**(真·无框架抽象,infra 反向依赖它实现→依赖倒置方向正了;`EventStreamingAgent`/`AsyncRunner` 留 infra=langchain 形状的适配契约);`port`/`control_port`→**`bus`/`control_bus`**(避 `stream:str` 名参 + `control_stream()` 函数撞名,用户否决 "port" 黑话)；interactive_gate 也去假 sync 桩。
- **分层结果**:domain 纯语义 / application 编排+无框架抽象(含 `event_stream`/`run_emitter`/`event_payloads`)/ infrastructure 仅适配器与细节 / interfaces 进程入口。
- **状态**:5 提交**已 push origin/main**(`c1d8241..78a3a1a`),`main...origin/main` 同步,工作区仅 `.claude/` untracked。**严守 kokoro-agent only**(未碰 contract//web/session;`agent_event.py` 生成契约未动)。**待用户**:P0-2 轮换 `.env` zhipu key(仍未做)。

- Date: 2026-06-19 (kokoro-agent 全面打磨 + 命名重排 — **已推送 origin/main** `6bc7c51..c1d8241`)
- **承接上一条**(强类型+DDD分层 16提交本地未推)。本会话续做:先把 `runtime_subagent_tool.py` 移入 `tools/runtime_subagent.py`(`6bc7c51`,与 clock/fetch 同级),再用 `/batch` 触发但**改串行逐模块**(用户选「串行·我逐模块」——单元共享类型骨架不独立、pyright/contract 敏感),把全仓 12 模块逐个打磨,**每模块独立 commit + ruff/mypy/pyright strict/全量 pytest 全绿**。redis 本机在跑(PONG),**redis 集成测试真实执行非 skip**。
- **类型反模式消除(object/Any→class):**
  - `9ce93fc` `json_types.py` 手写 object TypeGuard 阶梯(`_is_object_dict/_coerce_json_value`)→ Pydantic `TypeAdapter`(规则§6),统一到 `pydantic.JsonValue`(消除与 driver/agent_event 的重复定义)。47→19 行。ValidationError 是 ValueError 子类,raises 契约不变。
  - `39926bb` `local_fake.py` 3 处 `Any` 全清:LangChain override 的 `bind_tools/_generate` 用 `object` 逆变加宽(LSP 安全),删 `_ToolLike` 别名。
  - `3121d9b` `redis_stream.py` 移除规则§4 违规的 `if TYPE_CHECKING`+函数内 deferred import(redis 是**硬依赖**,无 try/except 豁免理由),`from redis.asyncio import Redis, from_url` 提顶层。
- **三组改名(用户逐个纠,均机械 rename + 全绿):**
  - `48f2be7` `RedisStreamPort/MemoryStreamPort`→`RedisStream/MemoryStream`(实现不带 port/protocol 后缀)。
  - `9727678` `StreamPort`→`StreamProtocol`(它确是 Protocol,与文件名 stream_protocol.py 对齐)、`make_stream_port`→`make_stream`。
  - `1b9641b` `agent_adapter.py`→`agent_builder.py`(里面全是 `make_deep_agent/make_subagent_runner` 构造函数,「构造」非「运行」;run_agent.py 才跑循环)。用户反对「adapter/第三方SDK」黑话,采纳 builder。
- **全仓中文注释**:WHY-only、≤1 行、技术术语(deepagents/langchain/RESP3/RFC1918 等)保留英文;补齐所有模块 + 5 个包根 `__init__` docstring。
- **刻意保留的合法边界(均补中文 WHY):** redis RESP2/3 线格式、LangChain StreamEvent、deepagents runner 结果 三处 `object`+TypeGuard 解析(非 JSON、Pydantic 不适用、折叠会触发 pyright Unknown);`agent_builder` 的 Any-package-view + 唯一 1 处 `type: ignore`(FilesystemPermission 存根缺口);`AsyncRunner.ainvoke->object`(诚实,不强行收紧)。`domain/agent_event.py` **整文件未动**(根仓 contract/events.yaml 生成,禁改)。
- **验证**:全仓 **ruff 干净 · mypy 0 · pyright 0(strict)· 202 passed**(redis 集成真跑)。**严守 kokoro-agent only**,未碰 contract//web/session。
- **状态**:本会话 16 提交**已 push origin/main**(`6bc7c51..c1d8241`),工作区仅 `.claude/` untracked。**待用户**:P0-2 轮换 `.env` 真实 zhipu key(仍未做)。

- Date: 2026-06-19 (kokoro-agent 强类型 + DDD 物理分层重排完成 — 本地 main,未推送)
- **范围铁律**:**只动 kokoro-agent 子仓**。`contract/`(events.yaml/generate.py)、kokoro-web、kokoro-session **一律不碰**;`domain/agent_event.py` 是根契约**生成文件**(见下),不手改。用户角色=出思路/打分/找不合理,我=实现。详见 memory `kokoro-contract-codegen` / `kokoro-agent-dual-typecheck`。
- **承接 06-18**:P0-1 安全网 + P1(删假 banner / driver payload builder / adapter 合并 / ProcessedRunIds)已合并 main(见上一条)。本日继续:
- **契约 codegen 真相(修我自己的错)**:`agent_event.py` 顶部 "generated from contract/events.yaml" banner **是真的**——`contract/`(events.yaml+generate.py+verify.py)在 **monorepo 根**,generate.py 生成 5 个跨服务镜像(web×2 Zod/TS、session×2 Zod、**agent_event.py**)。我 P1-1 在子目录 find 不到就误删 banner → `64d475e` **已干净撤销**(文件回基线)。**教训:别在子目录判断 monorepo 级路径**。
- **零 cast(全仓)**:把 deepagents/langchain 未类型化构造器经**包的 `Any` 视图**(`import deepagents; _deep: Any = deepagents; _build = _deep.create_deep_agent`)取用——`Any.attr` 是 Any 非 Unknown,结果流进 typed Protocol,**无 cast、无 per-call ignore**(`Any` 是规则允许的真实边界逃逸)。`tool_coroutine/tool_func` 过度抽象已内联删。
- **命名修正(用户逐个纠)**:`lc_adapter→agent_adapter`(禁 LC 前缀)、`port.py→stream_protocol.py`、`*_port→*_stream`(避 redis.py shadow)、`domain/subagent.py→registered_subagent.py`(对齐类名、区别 deepagents SubAgent)。
- **/goal 验证**:四条标准(灭 Any/object、match-case、物理分层无 LC 前缀、双流防腐 Pydantic 输出)经审计**已达成**;补 translator/chat_model/permission 的 value-dispatch 升 match-case。
- **/batch → 拒绝并行、单流顺序执行**(单元不独立=共享 import 冲突 + 决策密集 + 契约/pyright 敏感)。6 步 DDD 重排(各自四绿+一提交):
  - `ca02f94` ① `events.py` 纯领域(StreamIntent+8变体+TodoItem+ToolScalar/TodoStatus)→ `domain/stream_intent.py`;`SubagentSource` 统一 `registered_subagent`(消重复)。EventHeader/ToolInput/MessageParts(adapter 中间类型)留 events.py。
  - `b4bebe8` ② `builtin_tools.py` → `tools/`(clock.py / fetch.py SSRF / __init__ 注册表)。now/fetch_url 保持纯函数(直接单测),StructuredTool.from_function 在注册表组装(故 **不用 @tool**:@tool 会把函数变 tool、破坏直接调用 + 耦合 langchain 调用机制)。
  - `c9b1736`+`1813f64` ③ `chat_model+local_fake → model/`;env 配置改 strict 冻结 **Pydantic `ChatModelSettings`**(from_env 一次性读 env,builders 收 typed settings+per-request style;**不用 init_chat_model**,用户要 Pydantic 参数)。行为保持(test_model 15 绿)。
  - `b10e0cb` ④ `permission.py`(混 4 职责)→ `permission/`(policy / rules / static_gate / interactive_gate / __init__);`approval_policy.yaml` → 包内 **`config/`**(统一配置,policy.py 按包根解析路径)。
  - `5d8f415` `subagent_registry.py`(混 4 职责)→ `subagent/`(catalog / registry / specs / __init__);跨模块 `normalize_*` 转公开。
- **判断力收口**:`worker.py`(interfaces 入口编排器)、单一职责平铺文件(agent_adapter/control/json_types/observability)**不再拆**——「尽可能拆解」目标是消除混合,非最大化文件数。`runtime_subagent_tool.py` 放哪 borderline,留现状待用户定。
- 验证:全仓 **mypy 0 · pyright 0(strict)· ruff 干净 · 202 passed** 全程不降;零 cast、零 hasattr/getattr/assert_never;核心逻辑零 Any/object(残余仅真实边界,有 WHY)。**本地 main,未推送**;P0-2(`.env` 真实 zhipu key)仍待用户轮换。


- **任务**:用户「参考 stream_events 思想拆解其他的」+ 一份 /goal 全盘重构标准(dataclass/match-case、去 Any/hasattr、events/adapter/contracts 分层、去 LangChain 前缀);用户中断了 `/batch /loop` 全自动,改为**先审计产出 checklist → 逐项确认 → 再改**。全选「全盘 + 逐项确认」。
- **只读审计**(`agent-internal-standards-audit` workflow,4 子代理通读 26 src 文件):合并出 P0/P1/P2/P3 分级 checklist。基线已绿 **193 passed**。
- **分支 `refactor/agent-standards-cleanup`(kokoro-agent 独立 git,未合并 main)**,从绿线起 6 提交,每提交跑 ruff+mypy(本文件)+相关测试+全量 193:
  - `28bd8de` **P0-1** 固化安全网:把用户那笔未提交的 stream_events 重构(message_extractors/stream_translator 删除→stream_events 包)+ 3 个未跟踪测试(test_agent_event_driver/approval_policy/event_types)提交,锁 193 绿线。**未提交 `.env`(已 gitignore)/`.claude/`**。
  - `54a5d69` **P1-1** 删 `agent_event.py` 假 "generated from contract/generate.py" banner(该文件实不存在)。
  - `d5a54eb` **P1-2** `agent_event_driver.py` 抽 8 个具名 payload builder,消 ~30 处手搓 dict 键 + 4 处 `payload` 重声明;`nxt→next_seq`。
  - `b8ecd73` **P1-3** `adapter.py` 合并 read_output/read_error 标量分支(`_is_tool_scalar` guard)+ 抽 `_message_intents` 消 chat_model_stream/end 镜像 + 修该文件 3 处 mypy(subagent 变量分名、intents 重定义);`ev→event`。
  - `2ddc398` **P1-4** `worker.py` `ProcessedRunIds` 类(__contains__/__len__/add)+ `_publish_run_failed` helper(消 3 处重复 run.failed);test_worker 同步切类 API。
- **基于 /goal 标准拦下审计 3 个不当建议(非盲从,commit message 留痕)**:① 不删 pyyaml(`approval_policy.py` 在用);② driver 不复用 contracts(intent 级/测试专用/无 segment_id/rejected 恒在 → 形状不符+依赖倒置);③ contracts 不做泛型工厂收敛(违背「禁类型体操」、是不同字段 schema 声明、测试专用)。
- **P2 进度(同分支续提交,RED-first)**:
  - `6262c91` **P2-1** control 通道 strict `ControlMessage`(kind+decision,extra=forbid)收口,畸形消息显式 drop;RED-first(注入额外字段的 approve 不被采信)。校正 test_control fixture 到真实线格式 `{kind:"control",decision}`。
  - `0e4ce43` **(RED)** `parse_xread_response` RESP2/RESP3 特征网(无 redis 也跑),拆包前钉死行为。
  - `7352056` **P2-2** 拆 `stream_port.py`(281 行)→ `json_types.py`(共享 JSON 边界)+ `transport/` 包(port/memory_port/redis_port/__init__,名仿 web transport.ts;`*_port` 后缀避免 redis.py 与第三方 `redis` 包同名 shadowing,见 `471c5de`)。`_clone_event→clone_event`(跨模块转公开)。
  - `506f8b8` **P2-3** 拆 `stream_events/adapter.py` → boundary `adapter.py`(read_*/message_parts)+ flow `translator.py`(translate/_subagent_*,**零 isinstance**)。最后一处 AIMessage isinstance 收进 `read_ai_message`。message_parts 的 pyright ignore 收敛进 `_reasoning_override` 助手+WHY(langchain additional_kwargs 裸 dict,真实未类型化边界,无法真消,只能收敛)。**2 路切分(非审计 3 路 lc_types)**。
  - `a2d41a2` **P2-4a** pyproject 加 `[tool.mypy]` + redis/langfuse 缺 stub override(清 3 个 import-not-found)。
  - `49206ec` **修 P2-2 pyright 回归**:P2-2 的 match-case 重写(json_types `_coerce_json_value` + redis xread 解析)在 pyright **strict** 下回归(`case dict()`/`case [a,b]` 对 object 捕获为 Unknown);原 stream_port 用 TypeGuard 正是为过 pyright strict。**还原 TypeGuard 形式**(保留拆分,特征网守行为)。**教训:拆/改类型敏感代码必须同时跑 pyright,P2-2 漏跑了**。
  - `135bd40`→`577306d` **P2-4** 新建 deepagents/langchain 防腐层并**收尾打磨**(用户两轮纠正):① 文件名 `lc_adapter`→**`agent_adapter.py`**(`lc`=LangChain 前缀违反「禁 LC 前缀」铁律);② **全仓零 cast**——把未类型化 SDK 构造器经**包的 `Any` 视图**(`_deepagents.create_deep_agent`)取用,结果自然流进 typed `EventStreamingAgent`/`AsyncRunner` Protocol,无 cast、无 per-call ignore(`Any` 是规则允许的真实边界逃逸,cast/ignore 不是);③ `subagents: Sequence[object]`→`Sequence[SubAgent]`。`EventStreamingAgent`/`AgentInvokeInput`/`AsyncRunner` Protocol + `tool_coroutine`/`tool_func`/`FilesystemPermission` 归此边界;`_make_runner` 留作测试 patch 接缝。**全仓仅剩 4 处第三方边界 ignore(均带 WHY,非 cast):** agent_adapter 的 FilesystemPermission(deepagents 运行时有、typed 表面无)、builtin_tools×2(from_function)、adapter 的 additional_kwargs。
- **P3 重估 + 收尾**:逐项核实审计 P3 前提,发现审计 **P3-4 实锤错误**——声称「builtin_tools SSRF 零单测」,实则 `tests/test_builtin_tools.py` **36 测试**早已覆盖(`0a27f27` 对抗性加固提交建的)。据此重估:P3-1(env 散读)非 bug 仅整洁度、P3-3(策略 YAML 化)偏投机增攻击面,均 CLAUDE.md「拒绝投机」边缘;**只 P3-2 是真问题**。用户拍板**只做 P3-2**。
  - `8891af0` **P3-2** `_RUNTIME_SUBAGENT_REGISTRY` 进程单例跨 run/会话泄漏(runtime 子智能体累积、不隔离)。改 `_run_request` 每 run 新建注册表、删全局(`_CHECKPOINTER` 单例**保留**——按 conversation 正确隔离记忆)。RED-first:`test_run_once_isolates_runtime_registry_across_runs`(run_1 注册名不可在 run_2 可见)。
  - `842f847` **transport 命名**(用户两轮纠正):`port.py`→`stream_protocol.py`(说清是 StreamPort 契约)、`*_port.py`→`memory_stream.py`/`redis_stream.py`(去 `_port`、避 `redis.py` shadow 第三方包)。类名不动,纯 rename。
- **状态**:**P0-1 + P1(4) + P2(4) + P3-2 完成,已 FF 合并回 main 并删分支**(main HEAD `5a2d393`,本地领先 origin/main **16 提交,未推送**——用户选本地合并)。审计剩余 P3-1/P3-3/P3-4 不做(P3-4 已存在;P3-1/P3-3 投机)。**待用户**:① 方便时 `git push` main;② P0-2 轮换 `.env` zhipu key。
- 验证:kokoro-agent 全量 `uv run pytest -q` **202 passed**;**全仓 mypy 0 + pyright 0 + ruff 干净**(比基线 mypy7/pyright2 更净)。未碰 kokoro-web/session/contract。
- **遗留可选**:测试文件名 `test_stream_port_{redis,memory}.py` 仍是旧 `stream_port` 名(描述性,未跟模块改名,纯 cosmetic);若要彻底一致可改 `test_transport_*`。

- Date: 2026-06-15 (control 协议束完成:真取消后端 + 放弃解阻塞全部; #2 诚实延期)
- **用户指示**:先把 control 协议这一束做完、早点结束。结果:把最严重的 HITL×pipeline 缺陷清干净,并用真机隔离栈验了 stop/cancel。
- **#8 真取消后端 DONE**:
  - agent `9b1002d`:worker 每个 run 挂 cancel-watcher 读 `kokoro:run:<id>:control`;收到 `{kind:"control",decision:"cancel"}` → `task.cancel()` 取消整个 run(连带解阻塞内部所有待批门)→补发 `run.completed(status="cancelled")`。`await_decision` 显式忽略 cancel(由 watcher 处理)。
  - session `5d6054d`:control 端点/类型接受 `cancel`。
  - web `d1de82a` + `c9465be`:stop/new-chat/delete 发 cancel(不再 per-tool reject)；并本地 `markRunCancelled` 收口,避免停止会立刻关 SSE 导致后端 cancelled 终态来不及回流、残留 awaiting 工具/死批准按钮。UI 现为 `kk-tool--error` + 文案「运行已取消」。
- **#3 放弃解阻塞全部 DONE**:由 #8 自然覆盖——取消整个 run 比逐个 reject 更干净,所有待批门随 task 一起死。
- **真机端到端(cancel)**(隔离栈 session :3003 + 真 LLM worker db11 + web :3101,Default 模式):fetch_url 进入 awaiting → 点停止 → redis 里该 run **只有** `tool.invoked + tool.awaiting_approval + run.completed(status=cancelled)`(无 tool.returned,工具未执行)；UI 恢复可发送、工具行本地收口为 error「运行已取消」,**无** awaiting ghost / 无 dead 批准按钮。截图 `hitl-4-cancelled.png`(gitignore)。测后清 localStorage,按 task-id 拆栈,flush db11;db0/db14 用户库未碰。
- **#2 并行 tool_id 精确匹配 DEFERRED(诚实记录)**:做前探针证实门控工具协程拿不到自己的 tool run-id(`run_manager` 不注入,`RunnableConfig.run_id`=None,而 astream 的 on_tool_start 确有 UUID)。不 hack langchain/deepagents 内部就无法把 approve/reject 精确绑到某一并行 gated 工具。当前顺序执行(常态)无此问题,保留现状并在 `tasks/todo.md` 记为延期,避免引入脆弱魔改。
- **状态**:控制协议束收口完毕——#1 worker 并发(agent `05514b2`) + #8 cancel + #3 covered 都已 push main；下一块按用户先前全选,应转入 **#7 agent 自己管理会话记忆**(web 完整历史 / session 纯传输 / agent 可压缩 memory)。
- 验证:agent 161 pytest/pyright 0/ruff · session 87 bun test/tsc 0/lint 0 · web 250 vitest/tsc 0/lint 0 · contract verify PASS。四仓 clean。

- Date: 2026-06-14 (reject 超时档彻底修 — 后端确定性信号 tool.returned.rejected,replay 安全)
- **上一条目「遗留警示:reject 超时档显绿勾」已彻底修**(用户:做就做好,选「完整契约字段保留石板灰」)。根因:reject(用户点 / 90s 超时回退)都以 tool.returned is_error=false 回流,web 单靠客户端乐观,**replay/重连会把已批准成功的工具也误判**(approve 与 reject 都是 awaiting→returned,状态无法区分)。解法 = **后端把「拒绝」写进事件流**:
  - 契约(root `d95229c`):tool.returned 加可选 `rejected` 布尔(agent_out/agui_out/render);generate.py 加 `payload_optional` 机制(新可选字段在常路省略,不强制 fail-loud)。codegen 重生成 5 镜像,verify PASS。
  - agent(`2f0e4bd`):`control.rejection_result(name)` 单一来源(门返回它 / translator 据此识别);`stream_translator.on_tool_end`:result==rejection_result(name) → `rejected=true`(门拒绝走 on_tool_end 返回文案、不抛异常,故 run 仍正常收尾)。
  - session(`488f0f4`):normalize 透传 rejected(缺省省略)。
  - web(`67a6150`):mapper 带上 rejected;reducer `rejected=true → "rejected"`(仍保留乐观点击的即时反馈);无 flag 的普通返回仍 done。
- **真机端到端实证(隔离栈 session :3003 + 真 LLM worker db11 + web :3101,Default 模式)**:点拒绝 → **redis 事件流里 tool.returned 真带 `"rejected": true`**(后端写的,非乐观)→ UI 石板灰「未执行」→ **整页刷新后仍是 rejected 不回绿**(截图 hitl-3,gitignore)。超时档与点击档走**同一个门返回路径**(await_decision→reject→rejection_result),故同一机制覆盖;另有 reducer 单测专钉「超时路径」(tool.returned rejected=true 无乐观 → rejected)+ 「普通返回无 flag → done」。
- 验证:agent 159 pytest/pyright 0/ruff 净 · session 86 bun test/tsc 0 · web 249 vitest/tsc 0/lint 0 · contract verify PASS。按 task-id 拆我的栈 + flush db11;db0=419/db14=26 用户库未碰;agent uv.lock 无 churn;Playwright 后清了 demo localStorage。
- **乐观 vs 后端**:两者并存——乐观给点击即时反馈,后端 flag 让超时 + replay/重连确定性正确(单测同时覆盖两条)。

- Date: 2026-06-14 (真机截 reject 时挖出并修掉两个真 HITL bug — awaiting 在浏览器里根本不渲染)
- **起因**:用户要「一张 reject 的截图」。起隔离真实栈(session :3003 + 真 LLM worker db11 + web :3101 走 git worktree/主仓 next dev,NEXT_PUBLIC_KOKORO_SESSION_BASE_URL 指 :3003,KOKORO_WEB_ORIGIN=:3101),Default 模式 → fetch_url 门控。截图时发现 **awaiting 审批按钮在真实浏览器里从不出现**(工具一直「运行中」),挖出两个真 bug:
  - **bug① live awaiting 永不渲染**(critical):web 的 live EventSource 按事件名逐个 `addEventListener`(SSE 是具名事件),而那张名单 `transportEventNames` 是 transport.ts 里**手维护**的、**漏了 `tool.awaiting_approval`** → 实时流里该事件被静默丢弃,审批按钮对真实用户从来没出现过。**之前的 e2e 是用 curl POST 驱动 approve 的,从没点过 UI 按钮,所以没暴露**。修:把名单**从契约 codegen 生成**(`contract/generate.py` 的 `emit_web_schema` 导出 `transportEventNames`,SSOT,再漏 kind 不可能),transport.ts 改为 import。root `c8ad713`。
  - **bug② reject 视觉被实时流冲掉**:上轮 #56 的乐观 `markToolRejected` 写的是 React store,但 `consumeLiveSession` 自持一份权威 `state` 经 onState 推送 → 后端拒绝回流(tool.returned is_error=false)把它盖回绿勾 done。**单元/集成测试没抓到**(stub 没有竞争的 live state)。修:把乐观拒绝下沉到 live 句柄(`LiveSessionHandle.markToolRejected(runId)` 落进流的权威 state),tool.returned 到达时 reducer 保留 rejected。涉及 transport/reply/simulator/use-conversation + 句柄改造。web `3e6873f`。
- **真机端到端实证(这次走 UI 按钮)**:Default 模式真 LLM 调 fetch_url → **批准/拒绝按钮真出现**(截图 hitl-1)→ 点「拒绝」→ 工具行翻**禁止圈 + 删除线名 + 石板灰「你已拒绝该工具调用,未执行。」**(截图 hitl-2,kk-tool--rejected),且 run 收尾后**仍是 rejected 不回绿**(reducer 保留)+ 模型适应「抓取请求被拒绝了…如需重试请告诉我」。截图 kokoro-web/hitl-{1,2}-*.png(已 gitignore `hitl-*.png`)。
- 验证:web 247 vitest/tsc 0/lint 0 · contract verify PASS · session/agent 生成物逐字节不变(codegen 只动 web schema)。按 task-id 拆我的栈(session/worker/web)+ flush db11;db0=413/db14=26 用户库未碰;agent uv.lock 无 churn。
- **副作用提示**:为起隔离 web 杀了一个 :3100 上的**陈旧 kokoro-web next-server**(PID 37134,无 env、默认后端,判定为我历史会话遗留;用户产品在 :3000 未运行)。未重启它。:3001 上有个 bun session(7509)我全程未碰。
- **遗留警示(未修,记录)**:reject 的**超时档**(用户不点、90s 后 await_decision 超时回退 reject)走的是 tool.returned is_error=false,UI 仍显绿勾 done(乐观只覆盖用户主动点击)。要彻底区分需后端给超时拒绝一个确定性信号(契约加字段/或 is_error)。本轮聚焦用户主动 reject 的可见性,超时档低频,留记录。

- Date: 2026-06-14 (清账 — HITL/stream 三处低危遗留全部清掉,不留尾)
- **上一条目「复核遗留(低危)」三项已全部清掉**(用户:做完不要遗留),四仓仍走 main:
  - **#56 reject 显著区分**(web `5f5ca35`):reject 经门控工具以 is_error=false 回流(拒绝文案)→ 原路径翻绿勾 done,与成功无法区分。修:reducer 加 `rejected` 工具态 + `markToolRejected(state,runId)`;tool-returned 保留 rejected(不降级 done);`resolveStaleTools` 本就不动它。use-conversation.sendToolDecision 在 reject 时**本地乐观**置该 run 待批工具 rejected(与后端 control 信号并行)。视觉:`BanCircleIcon` 禁止圈 + 石板灰「未执行」面板 + 工具名删除线,CSS 区别于绿勾 done/红点 error。测试:3 reducer 单元 + 1 session-shell **集成测试**(awaiting 工具走真组件树点「拒绝」,transport mock)。
  - **#57 control 流终态清理**(session `b369c27`):`StreamPort.delete(stream)`(memory 删 map / redis DEL);relayRun 终态删 `kokoro:run:<id>:control`,审批/拒绝指令不再无限留 redis。+终态删流测试。
  - **#58 终态豁免 seq 去重**(session `b369c27` 同):normalize 中 run.completed/run.failed 豁免 (run_id,seq) 去重——复用 seq 的终态不再被吞(否则 relay 永不收束+web 永久「进行中」),web eventId 去重兜底重复终态。+终态豁免测试。
- **#4 并行待批 tool_id 精确匹配**:复核确认**当前顺序执行 agent 下游标顺序消费已足**,非缺陷,不改(留记录)。
- 验证:session 84 bun test/tsc 0/lint 0 · web 247 vitest/tsc 0/lint 0 · agent 未改(#55 审批超时预算 `ASTREAM_TIMEOUT_S+APPROVAL_TIMEOUT_S` 上轮已提交)。reject 路径此前真机双向验过(上条目),本轮 UI 改动以集成测试覆盖接线(awaiting→点拒绝→rejected 视觉+发后端),未重起真实 LLM 栈(低危清账,单元+集成已足)。
- **tasks #55–#58 全 completed**。

- Date: 2026-06-14 (分支收口 main + HITL/stream 对抗复核打磨)
- **四仓统一走 main**:agent/session main 快进到 feat;web 从 feat 建 main;root main merge feat(保留 4 个早期 docs PR + 78 工作 commit,冲突取 feat)。**后续都在 main 提交**,feature 分支弃用(未删)。
- **HITL/stream 对抗复核 + 打磨**(2 只读子代理审查 → 修高/中危):
  - [高] **control 跨工具越权**:决定原 per-run 从流首读,同 run 第2个门控工具误读第1个的遗留 approve → 自动放行。修:`DecisionCursor` per-run 共享游标顺序消费(agent `a792c6f`,+游标推进测试)。
  - [高] **放弃 run 不解阻塞**:stop/新建/删除若有待批,POST reject 立即解阻塞 worker(不挂 90s);`findAwaitingRunId` 派生(web `595ef23`)。
  - [中] **awaiting UX**:RunState 独立琥珀待批态(区别 running 转圈)+ 有 awaiting 强制展开过程块(否则审批按钮被折叠藏住)+ 点击后禁按钮防双发。
  - [中] **终态收口**:run 终态把残留 awaiting/running 工具翻 error(消除幽灵行);awaiting 无配对兜底补建步。
  - [中] **审批超时预算**:interactive 时 astream 总超时 +审批窗(120+90s),晚批准+执行不撞总超时。
  - 验证:agent 158 pytest/pyright 0/ruff · web 243 vitest/tsc/lint · 真机回归 approve 仍端到端真跑。
- **复核遗留(低危,未修,记录)**:reject 结果以 is_error=false 回流 → UI 绿勾+「用户拒绝」文案略矛盾(可后续给 rejected 专属样式);control 流无 TTL(每 run 留一条);normalizer seq 去重理论上可吞重复 seq 的终态(依赖 agent 单调发号,无现网 bug);多个**并行**待批工具的 tool_id 精确匹配(当前 agent 顺序执行,游标顺序消费已够)。


- Date: 2026-06-14 (HITL 交互式确认 — 真·human-in-the-loop 全链落地)
- **交互式 HITL 完成(跨四仓 + 真机双向实证)**:被门控工具调用时**暂停→前端批准/拒绝→恢复**。架构 = **in-tool 阻塞**(工具协程内 await control 流决定,单条 astream,无需 checkpointer/resume 编排)。
  - 契约:events.yaml 加 `tool.awaiting_approval`(14 kinds),codegen 重生成 5 镜像。root `f87c406`。
  - agent `13c99f5`:`control.py::await_decision`(读 kokoro:run:<id>:control 首决定,超时回退 reject)+ `permission.gate_tools_interactive`(approve 跑真工具/reject 回拒绝)+ drive_agent_events 据 blocked 集在 tool.invoked 后补 awaiting + run_agent/worker 透传 control_port(同一 StreamPort)。无 control 降级确定性 deny。157 pytest。
  - session `00696dc`:`POST /sessions/:id/runs/:rid/control?decision=` → 写 control 流;normalize 透传 awaiting。82 bun test。
  - web `7064f15`:mapper→reducer 翻工具 status `awaiting`;tool-call-row 批准/拒绝按钮 → use-conversation `sendToolDecision` POST control;透传链 session-shell→thread→assistant-turn(按 runId 绑定)→segment-process→tool-call-row。240 vitest。
  - **真实 LLM e2e 实证**(隔离栈 session :3003 + 真 worker + db11):plan 真模型调 fetch_url → tool.invoked + tool.awaiting_approval(**run 暂停**,无 returned)→ `POST approve` → tool.returned 真实 HTML `<title>Example Domain</title>` + 模型答出标题;**reject 对照** → tool.returned「用户拒绝」+ 模型适应「如需请重新允许」。暂停→approve 真跑 / reject 真拒,双向端到端。按 PID 拆栈 + flush db11,用户 db0/db14 未碰。
- **HITL 现已完整**:权限模式(auto/default/plan)+ 注入工具门控(REQUIRES_APPROVAL)+ deepagents 内部 fs 门控(fs_permissions)+ web 选择器 + **交互式确认(暂停/批准/拒绝/恢复)**。follow-up 仅剩 deepagents 内部工具的交互式审批(本轮交互覆盖注入工具;内部工具是确定性只读门控)。


- Date: 2026-06-14 (HITL 权限模式 + 真实 LLM 实证 — 续)
- **HITL 权限门(Claude-Code 式,完成)**:确定性工具门钩子。模式 auto(默认,全放行,行为不变)/ default(拦敏感工具)/ plan(只读规划)。**「需拦截确认的工具」做成显式可配置集 `REQUIRES_APPROVAL`**(默认 `{fetch_url}`,往里加名字即可拦更多)——用户强调的常见模型(默认 auto + 个别工具配置拦截)。RunRequest 加 permission_mode(agent pydantic + session zod 手镜像,非 codegen);web `?permission_mode=` → http → start-run → run.request → agent `gate_tools` 包装注入工具(被拦回「被 <mode> 拦截」结果,复用 tool.returned 零新契约)。**web composer 加 Auto/Default/Plan 选择器**(会话级,默认 Auto,随时可切不锁;复用 ComposerMenu)。commits agent `df06114`+`b34b163` / session `5e3d51d` / web `4c327ba` / root spec `4b19a4b`+`37f1381`。agent 150 pytest/pyright 0/ruff · web 237 vitest/tsc/lint · session 80。
- **真实 LLM 端到端实证(关键)**:隔离真实栈(session :3003 + 真实 worker + db11,OpenAI 兼容网关)实测——① plan 模式:真模型调 `fetch_url(example.com)` → **门拦下**(tool.returned「被 plan 拦截」)→ 模型优雅适应(「权限模式下被拦截…需提升信任档位」);② auto 模式对照:同请求 `fetch_url` **真执行**返回真实 HTML `<title>Example Domain</title>`。**证明 codegen'd schema 全链路 + HITL 门在真模型下确实工作且按模式条件**(此前只 fake-model 验过)。测后按 PID 拆栈 + flush db11,用户 db0/db14 未碰。
- **Langfuse**(上一条目已记):opt-in,真实 trace 冒烟仍待用户 key。
- **deepagents 内部 fs 工具门控(已落地)**:agent `4b38371`。`permission.py::fs_permissions(mode)` 经 `create_deep_agent(permissions=[FilesystemPermission(operations=["write"],paths=["/**"],mode="deny")])` 让 plan 只读(拦 write_file/edit_file,放行 ls/read_file/glob/grep);auto/default 不限。`execute` 需 sandbox backend、Kokoro 未配本不可用。真机实证:plan 真模型 write_file→「permission denied for write」+ 模型适应;auto 对照 write 成功并 read 回。151 pytest/pyright 0/ruff 净。
- **HITL follow-up(未做)**:真·交互式确认(工具调用时暂停→web 弹窗确认→批准/拒绝→恢复)需运行中反向通道(deepagents `interrupt_on`+checkpointer + `kokoro:run:<id>:control` + `POST /runs/:id/control` + 审批 UI),spec 已留设计,体量大宜新会话专注做。
- 教训重演警示:Langfuse 加依赖时又误 `git checkout uv.lock`(已即时 relock);本轮真实栈起 worker 后的 `uv run` 后 checkout uv.lock 是对的(纯 run 无依赖变更)。**判据:有依赖变更别 checkout,纯 run 才 checkout。**


- Date: 2026-06-14 (路线图 item 2/3/4 + Langfuse 全部落地 — 会话交接)
- **整轮完成并全推**:用户路线图「先处理 234,再 Langfuse」**全部落地**,四仓 push 后 `0 commits ahead`,CI 全绿(agent/session/web/contract)。当前测试基数 **agent 145 / session 78 / web 236**;三仓 typecheck+lint+test + agent pyright 0/ruff 净 + contract verify + generate --check 全绿。
- **item 2 产品需求手册**(root `cedc1b5`):新建 `docs/requirements/` 四层手册(00-product 愿景/01-capabilities 能力/02-flows 流程+验收/03-contracts 契约薄桥)+ README 新增规范 + _TEMPLATE。**用户要「新的」**——围绕真实三仓 stream 系统重写,既有 `docs/product/`(原型时代 canvas 矩阵)仅作参考;`00-product/scope-and-boundary.md` 三态分界(已建/已设计/已规划)是防漂移根。流程层每条映射测试总目录 slug(36 slug 全命中)。设计 spec `2026-06-14-requirements-handbook-design.md`。
- **item 3 完美测试用例**(agent `6540763`/session `82bf7b0`/web `12f3567`/root `059f754`):价值驱动补 +24 测试——agent runtime-subagent 协程 +5 / thinking 防空泡 +2、session http error 信封(方法→404/非 Zod→500)+2、web modePresentation 文案矩阵 +15。修正陈旧标记(replay-stream-write/model-resolution/worker-main-loop 实为已覆盖,不 padding)。**Playwright 用 MCP 插件驱动真实浏览器 e2e**(用户指示:`@playwright/test` 已回退):隔离栈 :3100→:3002→db10→fake worker 实证 8 项(发送→live 流式→落定 / 工具行 / 计划 / 模式锁 / 自动标题 / autoresize 31.5→80px / 刷新持久化+水合首帧 / rail 折叠),交叉验证 presentation 矩阵。测试总目录 §7.2 记录。
- **item 4 架构打磨**:
  - **4-1 契约 codegen(旗舰,全完成)**:`contract/generate.py` 从 events.yaml **全生成 5 镜像**(agent pydantic / session zod×2 / web zod+render union),`--check` CI 漂移门禁(root contract.yml),漂移检测实证。events.yaml 富化(enums/field_types 默认 string_nonempty 只列例外/`view_field_types` 处理 per-view 类型分叉:agui role→string、web status→放宽/render_optional/notes WHY)。commits web `e5af3cd` / agent `750a1f9` / session `0881311` / root `3feca4b`+`1ce0624`。设计 spec `2026-06-14-contract-codegen-design.md`。**改契约改 events.yaml 再 `python3 contract/generate.py`(镜像带 DO NOT EDIT 头)**。
  - **4-2 seq 升一等+删域 cursor**:复核为**上一轮 step 8 已完成**(全仓零域 cursor、seq 全链一等、SSE gate 断言),仅校正陈旧 spec(root `849f9c3`)无代码改动。
  - **4-3 拆长文件**:评估判定**不该拆**——三仓最大 use-conversation 471/reducer 468/composer 355 全 <500 且单一职责,无一达拆分阈值;强拆=制造回归。无改动。
  - **4-4 新贡献者 README**(agent `4a4fc49`/session `69e010d`/web `f546ebe`/root `aed2cb2`):4 个真实 onboarding(root 架构入口 + 三仓定位/4 层/运行/门禁/不变量)替换 stub。
- **Langfuse 可观测性**(agent `04102e1` / root `a93852c`,spec `2026-06-14-langfuse-observability-design.md`):opt-in 链路追踪接 agent。`infrastructure/observability.py` 从 env 建 LangChain CallbackHandler(缺 key→None→tracing 关、行为零变化);`run_agent.trace_config` 注入 callbacks+元数据(langfuse_session_id=会话 id、tag=执行风格、kokoro_run_id/conversation_id)。langfuse 4.7.1。**未验:真实 trace 冒烟需用户 LANGFUSE_PUBLIC_KEY/SECRET_KEY**(配后起 worker 跑一轮即见看板)。
- **额外**:用户指出的**收起态 rail 图标偏心 bug 已修**(web `6bbad67`)——隐藏标签 max-width:0 仍占 flex gap 把图标顶离中心,收起态 gap:0 修复,MCP 实测三图标 18/23→27/28 居中。
- **教训重演**:Langfuse 加依赖时又**误跑 `git checkout uv.lock`**(自己记过的),已即时 `UV_NO_CONFIG=1 uv lock`+`sync --locked` 锁回。lessons.md 已有此条 + 新增 monorepo 收敛被否(4 仓独立是有意架构,**不再提 monorepo**)。
- **下一步候选**:Langfuse 真实 trace 冒烟(待用户 key)/ langsmith(路线图「先 langfuse」后)/ 可观测性深化(run-inspector 读 replay 流——质量评估 5.0 弱项)/ 工具级错误恢复(质量评估 B 类半打磨)。**用户边界:不拓展功能,打磨现有到顶级**。


- Date: 2026-06-14 (收尾当前:去兼容写法 + CI 自动化 / 路线图)
- **铁律:禁止兼容写法**(用户强调)。立即应用:web is_error 从 `.optional().default(false)` 改严格 required(去掉"容忍旧事件缺字段"的兼容兜底——缺失即 fail-loud,绝不默认 false 掩盖真失败)。web `ed9ddb5`。
- **CI 自动化**(P0,把已有门禁固化):4 仓各加 `.github/workflows`——agent(ruff+pyright+pytest)/ session(tsc+lint+bun test)/ web(tsc+lint+vitest+build)/ root(跨仓 contract verify,checkout 三 sibling 仓)。跑的是本地一直全绿的同一批命令。commits agent `a43f1d8` / session `3b2ce10` / web `e41e24a` / root `0712f64`。**注**:CI 未推送(需用户 push 才激活);跨仓 checkout 若私有仓需配 PAT(已注明);首次 run 验证环境(无法本地跑 Actions)。
- **大胆优化建议(铁律 7)**:四仓独立(非 submodule)+ 分支各异 + 跨仓 contract CI 需 checkout sibling = 真实摩擦。**monorepo 收敛**是明确优化方向(原子跨层提交、单分支、contract CI 平凡),列为技术架构打磨项(下一轮 item 4)。
- **路线图(用户定)**:本轮收尾当前→下一轮 item 2(产品需求手册:多文档目录 + 新增规范)/ item 3(完美测试用例,含 Playwright e2e 套件)/ item 4(技术架构打磨,含 monorepo 讨论)→ 之后接 **Langfuse**(observability,先 langfuse 后 langsmith)。Playwright 套件归入 item 3。


- Date: 2026-06-14 (真实 tool-error 端到端 + stream 交错调查 + 质量评估)
- **交错 stream 调查**(用户探针 text→tool→text、第三段生成中):实证 + 单测确认布局正确——分段归属(文本块 complete 后工具开新段,工具挂在它产出的那段答案下);三相位(工具到+text 未到→forming / text 流式→streaming+caret / 落定)全钉死。web `8da29bb`。
- **真实 tool-error 端到端接通**(跨四仓):agent on_tool_error→tool.returned(is_error)按名分派(子代理失败发 subagent.finished 不卡 running、不冒伪红行;todo 静默;空异常回落类型名)+ 集成顺序护栏;contract events.yaml tool.returned 加 is_error;session 两端 strict required + 透传;web optional+default 宽容消费 + reducer is_error→status error+errorText + tool-call-row 红色面板 + D2 失败摘要复活(子集语义「N 个工具(K 失败)」)。commits agent `1348305`+`9150364` / session `72533fc`+`3243b6b` / contract `16f5f0a` / web `d3cac11`+`93b0982`。两轮对抗复核(15→7 确认全修)。真机:注入失败工具显红+错误面板+摘要聚合;is_error 信封端到端流过 replay;SSE gate + contract 6 镜像 PASS;agent 133/session 76/web 221 绿。**部署约束(记录)**:改 agent 契约必须重启 session(旧 strict 拒收新字段→skip-and-continue 丢事件)。
- **质量评估** `docs/superpowers/specs/2026-06-14-quality-assessment.md`:八维度评分(总评≈8.0;契约 9/架构 8.5/stream 8.5/UI 8/整洁 8.5/测试 7.5/文档 8/可观测性 5)+ 顶级差距(几乎全在 CI/e2e 自动化/可观测性=打磨非功能)+ HITL 等能力的架构缝(control stream 已文档化留缝)+ 打磨路径(P0 CI 自动化 + Playwright 套件,内核已顶级不需大动)。**用户边界:不拓展功能,打磨现有到顶级利于维护**。


- Date: 2026-06-13 (X1 自定义工具接入 + X1-b 对抗复核加固 — 完成)
- **X1 内置工具**(agent `89eb47d`/`2be8316`):`infrastructure/builtin_tools.py` 注册表 + `now`/`fetch_url` + 撞名守卫(import 期 fail-loud)+ 事件流 8k 截断;`_build_agent` 接入;fake 脚本插 now → SSE gate 升级为必含 tool.invoked/tool.returned;httpx 直接依赖(`UV_NO_CONFIG=1 uv lock` 修复 churn)。真实 LLM 问时间触发 now → 工具行渲染(e2e-5)。
- **X1-b 对抗复核**(19-agent workflow `wf_49db9fbc-452`,4 lens × 裁决):15 原始 → 10 确认,agent `0a27f27` 修 8 + 否决 2(有理由)。**SSRF major**:复现了 302 重定向把 169.254 metadata 拉回上下文 → follow_redirects=False + 手动逐跳 DNS 解析后 IP 复校验(防 rebinding)。**关键**:block list 精确(loopback/link-local/unspecified/multicast/RFC1918),**不用宽泛 is_private/is_reserved**——后者拦 198.18.0.0/15,而 TUN 代理把公网域名映射到该段,误拦会废掉代理环境所有抓取(本机正是 TUN:example.com→198.18.2.194)。结果:127/169.254/192.168 真拒,example.com 真抓 559 字符。墙钟 timeout + 字节限流 + identity 编码。126 pytest/pyright 0/ruff 净。真实 LLM `fetch_url(example.com)` → 工具行展示 args+HTML → 模型答出页面大意(e2e-6)。否决 #4(守卫全工具集会拒掉合法的 agent-名运行时工具)+ #10(now 已证通用管线,低 ROI)。
- **X2-C/D/B余 完成**(自主连续推进):C 过程块展开意图持久化(独立 UI store,segmentId 键,刷新保留,真机证实)web `b8e8f01`;D1 chevron 可展开提示 web `bb4d2dd`;B余 #7.6 长思考 scroll-shadow fade(双态验证)+ #7.2 分析钉死 web `58ec26d`。合并对抗复核 `wf_f5cc903e-f0a`(5 lens,16→8 确认)web `49c44db`:disclosure store 加固(boolean 校验 + 跨标签页 storage 同步,对齐 use-persistent-store)+ **移除 D2 死代码**(reducer 实证 tool.status 永不 error,失败摘要不可达;真实 tool-error 端到端接通列为独立 capability 任务)+ 测试强化。215 vitest + tsc + lint + build 绿,四仓干净。**未决 capability 任务**:wire 真实 tool-error status(agent ToolMessage.status → contract is_error → 渲染红色失败 + 摘要聚合)。**观察**:真实 LLM 偶发"调完工具不出最终文本答案"(replay 流无 message 事件,agent 层行为,非 UI bug)。
- **X2-B stream-event 可读性(Scope B)完成**:commit web `e3b40a2`(实现)+ `dd6c0ca`(对抗复核修)。B1 turn 级「重连中…」暖木脉冲胶囊(刷新回半截 run 时一眼可辨重连 vs 卡死,真机注入实证 + 脉冲三点)/ B2 空正文回落成形态(+ 副作用:空段不渲染,跳过既无气泡又无过程的段)/ B3 运行工具左竖条对比度。对抗复核 `wf_9ac40ea9-42d`(4 lens,15→4 确认,**状态机全部验证正确**;修的全是 cosmetic/测试质量:strip 脉冲一致性、空段清除、脆弱计数器换 getAllByText、正面断言)。200 vitest + tsc + lint + build 绿。**待续 B 余项**(延后,收益递减):中间段占位骨架(#7.2)、长思考 fade-edge。可选 C(manualOpen 持久化)/ D(密度)。
- **X2-A stream-event 连续性(Scope A)完成**:spec `docs/superpowers/specs/2026-06-13-stream-continuity-design.md`(§5b 落地记录)。A1 共享气泡骨架(forming/streaming/settled 同一 `.kk-turn__answer`,首 token 不跳盒)/ A2 过程块 `<details>`→`<div>`+`<button>` grid 高度过渡(三层 reveal>clip>body)/ A3 摘要 key 翻转淡入。commit web `072b953`(实现)+ `04d8910`(对抗复核修)。**用户逮到收起残留空盒 → 三层 clip 修复;对抗复核 wf_b3a5bfd3-42d 14→6 确认:#4 真 a11y 回归(折叠内容仍在 AT 树)用 inert 修、#3 focus-visible 暖木环、#5/#6 补结构+同元素复用测试、#1 诚实收窄注释、#2 既有非回归入 backlog**。195 vitest + tsc + lint + build 绿,真机逐态实证(盒模型逐字节相同 / inert 双向 / reveal 0↔31px)。**待续**:Scope B(可读性:turn 级状态行/中间段占位/长思考 fade)/ C(manualOpen 持久化)/ D(密度)分期,触发=用户对 A 真机感受后定。
- 教训 tasks/lessons.md 新增:按进程名 kill 误杀用户 db14 worker(已恢复);uv.lock 合法依赖变更别惯性 checkout(用 UV_NO_CONFIG relock + uv sync --locked 验)。

- Date: 2026-06-13 (goal 六项:测试体系 + 真实效果 + 扩展性设计 — 全部完成)
- **《测试用例总目录》**(`docs/superpowers/specs/2026-06-13-test-case-catalog.md`):8 代理盘点 workflow → 62 流程 × 单元/集成/e2e 矩阵(291 边界/失败复选项)+ 10 个分级缺口,**全部清账**(执行记录在 §7):4 项行为修复(脏请求杀调度循环/脏事件吞终态/坏模型崩 worker/event_id 随机致重放不幂等→确定性派生 `evt_{run_id}_{seq}_{event}`)+ 6 组钉死测试。测试基数 80/66/175 → **88/74/189**,session ZodError 500→400。
- **两个 e2e 逼出的真实 bug 已修**:① web reattach effect 在 live run 中二次订阅并覆盖句柄(泄漏 + 重连中闪现;onLive 预占 reattachedRef,web `60490c8`);② **translator 丢弃带 tool_calls 的中间叙述 → 真实 LLM 答案实质丢失**(用户只见 57 字收尾句;修复后叙述独立成段,真实 LLM 复验 1501 字完整回答,agent `463e8a9`)。
- **真实效果实证**(隔离栈 web :3100 + session :3002 + redis db10):fake 轮(live 链路 + todo + 模式锁)、真实 LLM 轮(真实计划 4/4 + markdown 表格全文)、**流式中刷新 → reattach 续传补完**。截图 kokoro-web/e2e-{1..4}-*.png(已 gitignore)。门禁 12/12 全绿(后台代理复验)+ SSE gate 多轮 PASS。
- **《能力扩展架构设计》**(`docs/superpowers/specs/2026-06-12-capability-extension-design.md`):工具接入(X1,链路已通零契约改动)/ workspace(W1-W3,artifact.created SOP + redis 取回通道)/ teams(T1 并行 run 传输层已就绪)/ HITL(留缝不实现);新 kind SOP 7 步固化。
- **留跑的栈**:用户原有 web :3000 + session :3001 + db14 worker(被我误杀后已恢复,升级到新 agent 代码);我的 e2e 栈 web :3100(PID 95207)+ session :3002(94924)+ 真实 LLM worker(96961)+ redis db10,可直接试玩。停我的栈:`kill 95207 94924 96961`(PID 也记录于 /tmp/e2e-*.log 旁)。
- 教训新增 tasks/lessons.md:严禁按进程名模式 kill(误杀了用户 db14 worker,已恢复并报告)。

- Date: 2026-06-11 (stream-perfection arc — top-architect blueprint execution)
- Driven by a 4-agent top-architect deep-audit Workflow (`wf_615794d0-e13`) → perfection blueprint in `docs/superpowers/specs/2026-06-11-stream-perfection-blueprint.md` (16-step execution order, behavior vs cleanliness strictly separated, 3 repos serial, stream files structural-only + gate after each).
- **P0 SSE loopback gate built** (`scripts/sse-loopback-gate.sh`): the critic's #1 blind spot — the audits all assumed a "real SSE e2e gate" that did NOT exist (web only had vitest). Now a re-runnable scripted assertion of the real agent→session→Redis→session SSE kind-sequence. Prereqs: Redis db14 + session :3001 + worker (LOCAL_FAKE_MODEL).
- **agent cast/type-shim cleanup (6 commits)**: 35→6 type shims (cast 31→1, pyright-ignore 8→5, type-ignore 1→0, TYPE_CHECKING 4→0, function-local imports→0). Real typing — TypeGuard (`is_str_object_mapping`/`is_object_list`/`is_agent_kind`), Protocol (`_AgentRunner`/`_StreamingAgent`), `getattr` boundary accessors, `with_types(output_type=)`, redis shape narrowing. The 6 residuals are unwrappable third-party SDK boundaries (deepagents/langchain/redis stubs), each 1-line WHY. pytest 74, **pyright 0/0/0**, ruff clean. SSE-gate verified zero stream drift.
- **session step 11** (`fa1456b`): split `runRequestSchema` out of `domain/agent-event.ts` → `domain/run-request.ts` (+ test mirror); agent-event.ts now purely the AgentEvent union (codegen-ready). 56 bun tests, contract-kinds zero drift.
- **web cleanliness harvest, steps 3–7 (4 commits)**: delete speculative dead code (artifact.available/permission.required — zero emitter monorepo-wide; artifact_ids/artifactIds; deriveRunPhase/RunPhase/lastAssistantRunId — only self-tested) → −165 lines; `seenEventIds` array→Set (O(n²)→O(1) in-memory, disk stays z.array, transform on load/save); split 447-line `protocol/session-event.ts` → `infrastructure/session-event-schema.ts` + `session-event-mapper.ts` (flattened protocol/ away, <3 rule); comment de-noise. run.created KEPT (session really emits it, web maps to null deliberately — 1-line WHY). 175→170 vitest (−5 dead tests); real-e2e zero drift.
- **web architecture pure-move, steps 13–14 (2 commits)**: `components/` (13 flat) → `thread/`(8) + `composer/`(2) + root(icons/session-rail/todo-bar); `domain/shared/session-stream-event.ts` → `domain/` (flattened single-file subdir). Pure git mv + import paths, zero logic. tsc + 170 vitest.
- **REMAINING blueprint steps** (the big behavior-face + codegen, deferred — best in fresh context for focus + byte-reproduce rigor): **step 9 contract codegen** (the core — `/Kokoro/contract/events.yaml` single source + deterministic generator → 6 mirrors, generate-and-diff to byte-reproduce current files BEFORE flipping to source, CI `git diff --exit-code` gate, delete check-contract-kinds.sh; critic says phase it: lock kind+field set first, naming-style conversion second); **step 8 seq → first-class integer envelope field** (Normalizer writes it, web deletes parseCursorSeq regex; humanGate); **step 10 agent drive_agent_events → explicit Segmenter** (the most fragile tool→text→tool→text non-collapse logic; TDD + SSE gate; humanGate); **step 12** agent events.py→agent_event.py (after codegen flip); **step 15** run.completed.status → shared enum; **step 16** delete redundant activity-event message_ref (only after segment_id lands; NON-behavior-preserving, last).

- Date: 2026-06-11 (DDD perfection + Lessie frontend)
- Driven by an audit Workflow (`wf_a0d614dc-5de`, 3 agents + adversarial critic) → per-repo blueprints + a contract-kinds regression net (`scripts/check-contract-kinds.sh`, baseline in /tmp). Spec: `docs/superpowers/specs/2026-06-11-three-repo-ddd-perfection-design.md`. Every step: my own `git diff -M -w` review of stream files + grep old-paths zero + per-repo gate + per-repo real SSE e2e + final full-chain e2e. **All three repos clean, contract-kinds byte-identical baseline (zero stream-contract drift), 11 behavior-preserving commits.**
  - **kokoro-session** (3 commits, `feat/three-repo-loop`): deleted dead `domain/sessions.ts` (reverse-dependency shim), symmetric rename `events→session-event` / `agent-events→agent-event`, inlined `RunIdFactory` out of `ports.ts`. 56 bun tests green.
  - **kokoro-agent** (4 commits A–D, `feat/three-repo-loop`): **flat → strict 4 layers** (the "most garbage" one) — `domain/{events,run_request,subagent}` · `application/run_agent` · `infrastructure/{chat_model,stream_translator,message_extractors,subagent_registry,stream_port,local_fake_model}` · `interfaces/worker`. Dropped the run_agent X-as-X re-export shim. pyproject script → `kokoro_agent.interfaces.worker:main`. Stream files (run_agent/stream_translator/message_extractors) `git diff -M -w` = pure move, logic untouched. 74 pytest, ruff now fully clean (the pre-existing events.py:7 E402 vanished with the old file), pyright 0. Worker restarted on the new entry → real e2e zero drift.
  - **kokoro-web** (4 DDD commits, `feat/bootstrap-shell`): killed BOTH re-export shims (preview's ~16-symbol + reducer's schema) — consumers now import the real files directly (zero shim). Renames `session-stream-stream→session-stream-transport`, `session-stream-simulate→session-stream-simulator`, `session-stream-preview→session-reply` (orchestrator only). Deleted dead `artifact-preview.tsx` + `lib/utils.ts` + `components.json` + `isStreamingAssistant` prop → dropped 4 npm deps (`@a2ui/react`,`@a2ui/web_core`,`clsx`,`tailwind-merge`). Moved a misplaced test to `tests/infrastructure/protocol/`. 175 vitest green.
- **Lessie-style frontend visual polish** (kokoro-web, 2 commits `a620c12` `0fc52db`): soft pastel rainbow glow on the main stage + lighter base + high-contrast near-black headline; removed the 3 starter chips (+ dead `starter-chips.tsx`/`prefillDraft`); **silky rail collapse/expand** (320ms grid-template-columns ease + label opacity/max-width fade; `data-resizing` disables the transition for 1:1 drag tracking — replaces the old hard snap); lightened composer (neutral hairline + soft shadow). tsc+eslint+175 vitest; Playwright-verified empty/collapsed/conversation states + animation transitions via getComputedStyle.
- **Running stack** (left up): Redis db14, session :3001 (new 4-layer), worker (new `interfaces.worker` entry, LOCAL_FAKE_MODEL), web :3000. Stop: `lsof -ti:3001|xargs kill` + TaskStop the worker bg job.
- **Deferred as separate workstreams** (recorded in the spec, NOT this round): contract codegen single-source (the P0 cross-repo debt — 13-kind contract is hand-mirrored in agent Literal / session Zod×2 / web TS union, violates the codegen rule); agent stream-file `cast`/`pyright:ignore` convergence (after codegen); web `infrastructure/protocol/session-event.ts` (447 lines, codec+mapper) split evaluation; comment-noise compaction per-file; session `ReplayStore.read`+mirror test-only parallel-truth removal.

- Date: 2026-06-10 (DDD cleanup — three repos)
- Surgical DDD cleanup across all three repos, behavior-preserving, 9 commits, every step gate-green + a final real-backend e2e regression (web+session+agent all split → 「实时会话已连接」, real todo + answer, zero drift). Plan: `docs/superpowers/plans/2026-06-10-ddd-cleanup-three-repos.md`. Method: a 3-agent **workflow** DDD audit → I re-verified every finding by grep (caught several audit errors) → **3 parallel subagents** (agent-repo / web-preview / web-hooks), each diff-reviewed + gate-run by me before accepting.
  - **kokoro-session** `feat/three-repo-loop` (e66f4e9, 0e41095, f9a9d8c): delete dead `memory_store.ts`; kebab `start_run`→`start-run`, `replay_store`→`replay-store`; **application owns the port contracts** — moved `StreamItem`/`StreamPort`/`ReplayStore` interfaces into `application/ports.ts`, infra type-imports + implements them (dependency inversion). 56 bun tests green; restarted + e2e-verified.
  - **kokoro-web** `feat/bootstrap-shell` (8b1ace0, 18d5f83, bead691, cb524cf): delete orphan `components/ui/card.tsx` + un-export internal-only symbols; extract persistence schema → `session-stream-state.schema.ts` (reducer 618→517); split `session-stream-preview.ts` 531→99 + `-simulate.ts` 273 + `-stream.ts` 199 (re-export keeps consumers unchanged); extract `usePersistentStore` from `use-conversation` (631→579). 178 vitest green throughout.
  - **kokoro-agent** `feat/three-repo-loop` (5c352fe, 4d08d27): single-source `ExecutionStyle` (infra imports the domain contract); split `run_agent.py` 535→243 + `content_extractors.py` 78 + `event_translator.py` 241 (leaf ← translator ← orchestrator, no cycle); cross-module helpers/constants made public (`_text_of`→`text_of`, `_TODO_TOOL`→`TODO_TOOL` — un-private since now imported across modules). 74 pytest green, pyright 0 errors, uv.lock un-churned.
  - **Audit corrections I caught (don't trust audits blindly):** `createConversationStore` flagged "dead" but tests use it 13× → KEEP; several "dead exports" (`sessionEventSchema`/`parseCursorSeq`/`activeEntry`/`SessionTransportEvent`) were internally used → un-export (not delete), and `SessionTransportEvent` kept exported (it types public fns).
  - **Conservatively NOT split (correct calls, recorded as future work):** `use-conversation`'s transport/mode/list block shares one transient state machine (3 states + 3 refs reset atomically) — the hooks-split subagent rightly refused to force it apart (stale-closure / effect-timing hazard); only the low-coupling `usePersistentStore` was extracted. `composer.tsx` (355) optional split — skipped (low priority). session `normalize.ts` (209) — cohesive event mapper, left whole.
  - **Pre-existing (untouched, out of scope):** agent `events.py:7` ruff E402 (domain file, not introduced here).

- Date: 2026-06-10 (real-backend e2e)
- REAL three-process pipeline brought up and Playwright-verified against the NEW ordered-parts reducer (preview can't cover this — it's a client-side sim): web :3000 → kokoro-session :3001 → Redis **db14** (fresh/empty, no flush needed) → kokoro-agent worker (`KOKORO_LOCAL_FAKE_MODEL=1`, credential-free DeepAgents loop) → events → SSE → reducer → UI. Browser rendered the REAL fake-model answer ("本地预览：DeepAgents 活动流已接通…") + the REAL `write_todos` checklist (理解请求并规划 ✓ / 用本地预览作答 ◉) in the floating 计划 1/2 panel, transport footer **「Fast · 实时会话已连接」** (live path, NOT 本地预览). Confirms the new reducer correctly consumes REAL agent envelopes (real seq / message_ref / cursor), not just preview.
- **CORS origin gotcha (cost a failed first attempt, now documented):** the browser MUST be opened at `http://localhost:3000` to match the session's `KOKORO_WEB_ORIGIN=http://localhost:3000`. Opening `127.0.0.1:3000` makes the web resolve the session as `127.0.0.1:3001` and the run POST is CORS-blocked — the server STILL executes the run (events land in Redis) but the browser can't read the response and silently falls back to 本地预览. Symptom: events exist in Redis but UI shows preview text.
- Start commands (left RUNNING for continued testing; stop with `lsof -ti:3001 | xargs kill` for the session, and TaskStop the worker bg job):
  - session: `cd kokoro-session && KOKORO_STREAM_BACKEND=redis KOKORO_REDIS_URL=redis://127.0.0.1:6379/14 KOKORO_WEB_ORIGIN=http://localhost:3000 KOKORO_SESSION_PORT=3001 bun run src/main.ts`
  - worker: `cd kokoro-agent && KOKORO_STREAM_BACKEND=redis KOKORO_REDIS_URL=redis://127.0.0.1:6379/14 KOKORO_LOCAL_FAKE_MODEL=1 uv run kokoro-agent-worker` (then `git restore uv.lock` — aliyun churn).
  - Redis db0 (44 keys) is the user's real data — NEVER flush; db14 was empty and used directly. `FLUSHDB` is auto-denied by the permission classifier (correct).
- VERIFIED LIVE: real todo checklist + real answer bubble + live transport through the new reducer. NOT yet exercised LIVE (credentials absent → no real tool-calling/reasoning model): `tool.invoked/returned` rows, `subagent.*` rows, `thinking.delta`. These are unit + preview verified at the UI layer. The fake model (`local_fake_model.py`) only scripts `write_todos` + one final text — scripting a tool/subagent into it risks recursion (the `agent`/`task` sub-run re-enters the script with `tools=[]`), and no domain tool is registered (`run_agent.py:24` "We add no custom domain tools yet").
- FINDING for the next phase: a standard DeepAgents loop emits `[activity]* → one final text` (intermediate AIMessage text is dropped at `run_agent.py:252` `if text and not message.tool_calls`, and a text-only turn ENDS the loop). So the UI's multi-TEXT-segment interleave (text→tool→text bubbles) is only producible if the mapping is changed to surface intermediate narration text — today it's verified via the injected "多段对比" demo + preview, but the live agent doesn't yet emit it. Worth deciding in the DDD/mapping pass whether to surface intermediate text.

- Date: 2026-06-10
- Active stream: stream-perfection → ordered-parts rewrite → turn-lifecycle polish (kokoro-web `feat/bootstrap-shell`, PUSHED).
- Stream perfection (kokoro-agent `bc316d7`): real token-level streaming via LangChain `on_chat_model_stream` (`_TEXT_STREAM_INTENT`, `streamed_text`/`sub_streamed_text` accumulators) so answers stream char-by-char instead of one full blob; verified live (77 glm-5 deltas, 42 message.delta). Also fixed the segment-attachment bug: `ref_for_segment_activity` now attaches a tool to the FOLLOWING segment (`active_message_ref is None OR segment_completed`) instead of reusing a completed segment's ref — this was the "tool→text→tool→text collapses into one bubble" defect.
- Ordered-parts streaming model (kokoro-web `61715b6`): rewrote the reducer around a `SessionStep` discriminated union (`thinking | tool | subagent | text`, each carrying `seq` + `messageId`) stored in `stepsByRun` keyed by runId; `seq` derived from the envelope cursor (`run_x:NNNN`) so render order == true emission order (roots out the message_ref-bucketing reorder bug at the DATA layer). `buildThreadItems` groups consecutive assistant messages by runId into one turn. Layout = ONE 🤖 avatar per turn + a vertical spine of stacked segments; each segment = answer bubble on TOP, its process (thinking/tools/subagents) hanging BELOW it (text-above-process — the user explicitly overrode the research's process-above-text). Segments grouped by `messageId`.
- Turn lifecycle affordances (kokoro-web `9c82c69`): (1) submitted-no-token scaffold — a live forming turn (breathing avatar + 「正在思考」line) between submit and first token, never a blank frame; (2) forming bubble — when a tail segment's process arrives before its text, the bubble slot shows 「正在思考」with process below, never an empty bubble (the tool→text-not-yet case the user asked about); (3) collapse-on-settle — `SegmentProcess` default-open follows the live signal (`open = manualOpen ?? live`), no remount, manual toggle takes over; (4) reconnect anchor — dedicated `isReconnecting` window renders 「重连中…」with a distinct warm-wood capsule, cleared on first reattach event. Single live anchor preserved (only the tail segment carries caret/breathing/live process).
- Verification: 178 vitest green, tsc + eslint clean. Playwright (preview Thinking, 40ms in-page recorder) captured the full live lifecycle deterministically: forming (`正在思考` bubble + expanded `思考中…` process + breathing avatar, no caret) → text streaming (real bubble + caret, process still live) → collapsed settle (`思考过程 · 1 个工具`). Settled multi-segment layout DOM-verified (one avatar, two bubbles each with collapsed process below).
- Process discipline: design panel (3 agents, cross-validated) → ordered-parts spec `docs/superpowers/plans/2026-06-09-ordered-parts-stream-rewrite.md` → Slice A → Slice B, each reviewed + Playwright'd before the next. Debug PNGs removed; `.playwright-mcp` gitignored; agent `uv.lock` aliyun churn must be `git restore`d after every `uv run`.
- OPEN NEXT (next phase, best started fresh — this context is large):
  - REAL-backend e2e: only web :3000 is up; start kokoro-session (:3001, bun, Redis db15) + kokoro-agent worker (uv, gateway key in gitignored `.env`, `disable_streaming=True`) and Playwright a REAL streaming run to validate the ordered-parts model against genuine DeepAgents output (tools/subagents/thinking only render when the agent PRODUCES them — preview can't exercise real subagent nesting).
  - DDD architecture refactor (deferred; panel cross-validated a session→web→agent ordering): god-file splits, kebab-case, application-owned ports, dead-file deletion across all three repos.

- Date: 2026-06-08
- The whole live-chat + subagent arc is now committed AND pushed across all four repos:
  - `kokoro-agent` `feat/three-repo-loop` @ `57eb94e` — per-run execution_style, layered subagent system (built-in/config-custom/runtime-custom), nested subagent text, stream_port constants.
  - `kokoro-session` `feat/three-repo-loop` @ `18b643e` — strict execution_style, message-scoped activity (message_id), subagent source/type + subagent.text envelopes, stream-port options.
  - `kokoro-web` `feat/bootstrap-shell` @ `c26e848` — execution_style threading, multi-segment turns, nested subagent stream, AND Demo Task 4 (mode-aware process density).
  - `Kokoro` (root) `feat/kokoro-web-bootstrap` @ `d452de2` — handoff docs/specs/plans + project-rules rewrite.
- Demo Task 4 (视觉层级统一) DONE: conversation mode (fast|thinking) threaded SessionShell → ConversationThread → AssistantTurn → ProcessBlock as a `data-mode` hook; CSS differentiates process-body density (thinking gap 0.6rem vs fast 0.32rem) without layout shift. Answer bubble stays the strongest surface; process block stays a lighter secondary disclosure. Browser-verified (Playwright): thinking rowGap 9.6px vs fast 5.12px; transport row reads mode-specific calm metadata.
- Side-effect hygiene: agent `uv.lock` aliyun-mirror churn reverted (not committed); root-level numbered Playwright PNGs gitignored.
- Open work on this baseline: attach menu → native file-picker/upload; (deferred) subagent management entry (#113); (deferred) nested subagent internal-stream richer expansion (#115/#116).

- Date: 2026-06-06
- Current authoritative repo snapshot (aligned to the user-approved baseline):
  - `Kokoro` (root): `feat/kokoro-web-bootstrap` @ `0fe0dbd` — handoff/docs branch.
  - `kokoro-web`: `feat/bootstrap-shell` @ `fa419f4` — chat-shell overhaul + `globals.css` modularization baseline.
  - `kokoro-session`: `feat/three-repo-loop` @ `712a34b` — Redis subscription fix / interrupt-recovery baseline.
  - `kokoro-agent`: `feat/three-repo-loop` @ `63c6031` — DeepAgents activity-event loop baseline.
- Alignment note: some older notes and todo entries were written while temporarily looking at newer `feat/agent-deepagents-planning` branches. For the current baseline above, the following are ALREADY present and should not be treated as open work: assistant markdown rendering, rail multi-conversation history, DeepAgents activity families (`thinking.delta` / `todo.updated` / `tool.*` / `subagent.*`), interrupt-recovery, and sessions list.
- True remaining work on this baseline:
  - turn the attach menu into a real native file-picker / upload flow;
  - polish `stream_port.py` / shared transport contract constants;
  - optional live-provider credentials, design-direction choice, and duplicate-repo housekeeping.
- 2026-06-06 execution-style contract pass completed across the locked baseline branches:
  - `kokoro-web`: selected `ConversationEntry.mode` (`fast | thinking`) is now threaded into the live run request path; `session-stream-preview.ts` no longer hard-codes `execution_style=default`, and live start contract failures (400/422) surface as explicit failed runs instead of silently degrading to preview.
  - `kokoro-session`: `runRequestSchema.execution_style` is now restricted to `fast | thinking`; empty/invalid values fail loud at the HTTP boundary with 400 instead of drifting through as optional free-form strings.
  - `kokoro-agent`: model selection is now resolved per run via `make_chat_model(execution_style)` instead of one worker-global model instance; `thinking` uses a distinct runtime configuration (verified on the current `openai:glm-5` path via `reasoning_effort="high"`, while `fast` leaves it unset).
  - Verification: `kokoro-web` full gates green (`bun run lint && bun run typecheck && bun run test`, 127 tests); `kokoro-session` full gates green (`bun run lint && bun run typecheck && bun test`, 57 pass / 2 skip); `kokoro-agent` full gates green (`uv run pytest`, 44 pass / 2 skip, plus `ruff` + `pyright`). Real provider smoke check confirmed both modes against the configured gateway: `fast_reply = FAST_OK`, `thinking_reply = THINKING_OK`, and the resolved runtime configs differ at the agent layer.
- Older entries below remain useful historical detail, but this 2026-06-06 block is the source of truth for branch/commit state and open-work triage.

- Date: 2026-06-05
- Active stream: kokoro-web chat-shell UI overhaul (composer + agent-activity rendering). Backend (kokoro-session / kokoro-agent) UNTOUCHED this session — all changes are in kokoro-web on branch `feat/bootstrap-shell` (committed `fa419f4`, pushed).
- Completed (2026-06-05, kokoro-web):
  - Composer → Gemini-style two-row layout (text row + controls row); native scrollbar hidden; IME `isComposing` guard on Enter (user types Chinese); press micro-animations; starter chips now warm-wood line icons (emoji removed); expand-to-edit modal (⤢, React portal — ⌘/Ctrl+Enter sends, Enter=newline, Esc closes); disabled send shows a neutral chip.
  - Agent activity moved INTO the chat flow (ChatGPT/Claude/Perplexity-informed): an assistant turn = one 🤖 avatar → answer bubble on top → collapsible「思考过程」below it (thinking + tool calls + subagents as ONE unit); expanded while streaming (live「思考中」pulse), auto-collapsed to a one-line summary once the answer lands. Long thinking is capped + scrolls. Split into small components: assistant-turn, process-block, tool-call-row, subagent-row, run-state.
  - Todo plan = collapsible bar pinned ABOVE the composer (separate from the in-chat process); CC-style line-icon checklist (todo-bar).
  - Fast/Thinking mode = per-conversation (`ConversationEntry.mode`, persisted with `.default("fast")` for back-compat); LOCKS after the first message ("选中了就不能切换"); new conversation unlocks; zap/spark icons + lock display.
  - Rail is drag-resizable (`useRailResize` + `.kk-rail__resizer`; shell grid col = `var(--kk-rail-width)`); min widths enforced (rail 200–420px, main ≥360px); hidden when collapsed / on mobile.
  - Fixed chat left/right drift on todo-bar toggle via `scrollbar-gutter: stable both-edges` on `.kk-thread`. Added `prefers-reduced-motion` guards.
  - `globals.css` (1882 lines) modularized → a 10-line import file + `src/app/styles/{base,shell,rail,stage,thread,markdown,activity,composer,responsive}.css`. Verified BYTE-IDENTICAL inlining (diff/cmp) and styles intact in-browser; cascade unchanged.
  - Gates: lint / typecheck / vitest (121) all green. Dev server left running on :3100. Design decisions recorded in agent memory `kokoro-web-chat-shell-design`.
- Open next (optional; user PAUSED here): expand-modal focus trap; finer split of `activity.css`/`composer.css` (~500 lines each); persist rail width to localStorage; reconcile "正在输入" vs "思考中…". NOTE: user said do NOT split the big test file `session-shell.test.tsx` (~1300 lines).
- STILL THE BIG GOAL ([[kokoro-agent-activity-goal]]): tools/subagents/thinking render only when the agent PRODUCES them; the UI + contract are wired and unit-tested but not yet triggered LIVE end-to-end (needs a registered domain tool / real subagent spawn / reasoning model in kokoro-agent). That's the next backend stream for a follow-up agent.
- CONSTRAINTS for follow-up agents: `kokoro-agent/.env` is gitignored and MUST NOT be committed (holds the gateway API key). A demo activity conversation is seeded in the browser's localStorage key `kokoro:conversations` for screenshots — deletable via the rail's hover-×, not in code. kokoro-session & kokoro-agent are clean on `feat/three-repo-loop` (in sync with origin), untouched this session.

- Date: 2026-06-04
- Active stream: three-repo live loop CLOSED end-to-end (web ↔ session ↔ agent over Redis)
- Completed (2026-06-04):
  - kokoro-session `feat/three-repo-loop` (8c9428f): fixed the real Redis-only SSE bug — `streamSession` resumed from the domain `envelope.cursor` ("run_x:NNNN") handed to `subscribe()` as a Redis stream id, which XREAD rejects (and "" on first connect), so `/stream` silently delivered nothing over Redis (MemoryStreamPort masked it via lexicographic compare). Now subscribes the replay stream from its head (single transport-cursor namespace, replay+tail in one); `RedisStreamPort` coerces falsy cursor→"0-0"; +regression test (live tail after non-empty snapshot). Landed the Zod-migration WIP (`SessionEventName` derived from schema, `session.created` carries `title`, `StartRunInput` single-sourced) + the `sessionEventNames` lint fix. lint/typecheck/test(44) green.
  - kokoro-agent `feat/three-repo-loop` (673ee61): `KOKORO_LOCAL_FAKE_MODEL=1` → `LocalFakeChatModel` (wraps LangChain `GenericFakeChatModel`) for credential-free e2e; fixed missing `Mapping` import + tightened the payload TypeGuard for pyright --strict. pytest(26)/ruff/pyright(0) green.
  - Ran all three together for the FIRST time over the existing shared Redis (isolated **db 15**): web(:3100) → session(:3001) → Redis → agent worker → Redis → session relay → SSE → web. Verified at the protocol layer via curl (full session.created→deltas→message.completed→run.completed) AND in the browser via Playwright: real agent reply rendered ("Local fallback active…"), transport label **"实时 · http://localhost:3001"** (live path, not the preview fallback).
  - Both backend repos were on `main`; branched to `feat/three-repo-loop` before committing, per policy. Neither pushed.
- Still running for the user (started this session): shared Redis container (db 15), kokoro-session on :3001 (`KOKORO_STREAM_BACKEND=redis KOKORO_REDIS_URL=…/15 KOKORO_WEB_ORIGIN=http://localhost:3100`), kokoro-web dev on :3100. To stop session: `lsof -ti:3001 | xargs kill`. Worker is a backgrounded `uv run kokoro-agent-worker`. NOTE: port :3000 is an UNRELATED project (hixcode) — do not touch.
- Open next steps: optional real LLM via `ANTHROPIC_API_KEY`; chat-polish (starter chips, mode→execution_style, attach picker, markdown, multi-conversation history); reconcile avatars-vs-prototype design decision; remove stray sibling `~/WebstormProjects/kokoro-web` duplicate.

- Date: 2026-06-03
- Active stream: kokoro-web first-screen shell redesign (staged)
- Completed (2026-06-03):
  - Added `run.created` to the protocol union as a parse-and-ignore family (maps to null) with red→green tests
  - Replaced the two-card protocol demo with the approved minimal first-screen shell (rail + hero + static composer); reworked `globals.css`
  - Kept the SSE reducer wired but surfaced via `data-*` (message rendering deferred to the chat-view slice); `ArtifactPreview` left in place but unmounted (reserved)
  - Gitignored local agent/MCP scratch dirs (`.playwright-mcp/`, `.superpowers/`)
  - Re-ran all four gates green: lint, typecheck, test (15), build
- Conversation view (2026-06-03, built + verified, commit pending visual sign-off):
  - Design: `docs/superpowers/specs/2026-06-03-conversation-view-design.md`
  - One reducer for the whole thread: `appendUserMessage` (local user bubbles) + `consumeLiveSession` gains `initialState`/`onSettled` so each run folds onto the persistent thread
  - Graceful standalone demo: `startSessionReply` tries real kokoro-session, falls back to a local simulated stream (`simulateAssistantReply`) through the same reducer; labelled "本地预览"
  - `SessionShell` now a real chat: empty hero state → send → user bubble + streamed assistant reply, multi-turn, streaming/failed states; injectable `startReply` for tests
  - UI feedback pass: compact/conventional sizing; comfortable left/right bubbles (assistant left+心 avatar, user right); composer hover no longer shifts layout
  - Gates green (lint/typecheck/test 29/build) + Playwright visual pass; artifact lane stays deferred/reserved
  - Committed: kokoro-web first-screen (2d0cf08, bf0dde3) and conversation view (7aada7e)
- Production-usable polish (2026-06-03, via workflow + subagents, committed in 7aada7e):
  - Multi-agent workflow: audit → plan → [implement → per-round QA gate] ×6 → 4-lens adversarial review, with a hard zero-cruft rule and a quality gate after each workstream
  - Added: stop/cancel generation, SSR-safe conversation persistence (localStorage), 新对话 reset+refocus, retry-on-failure, double-send guard, composer auto-grow, scroll stickiness + jump-to-latest, dead-code removal, a11y (lang=zh-CN, aria-live/atomic, focus-visible no-reflow) + WCAG contrast
  - Verified in main: lint/typecheck/test (79)/build green; Playwright pass (send → reply → reload persists → 新对话 resets); review verdict production-ready, 0 blockers
  - Deferred: markdown rendering, multi-conversation history list, artifact-lane promotion
  - Dev server left running at http://localhost:3100 for review
- Earlier completed (2026-05-29):
  - Wrote kokoro-web design spec
  - Wrote kokoro-web implementation plan
  - Created independent `kokoro-web` repository with Bun + Next.js App Router scaffold
  - Added strict protocol parsing in `src/infrastructure/protocol/` and mapped it into domain-safe session stream events
  - Added replay-safe reducer plus red→green tests
  - Added a minimal AGUI/A2UI-oriented session shell with a client-only artifact preview boundary
  - Verified `bun run test`, `bun run lint`, `bun run typecheck`, and `bun run build` in `kokoro-web`
  - Added a durable three-primary-runtime architecture overview under `docs/product/04-architecture/`
  - Recorded main-agent/background-agent coordination guidance in `tasks/lessons.md`
  - Persisted orchestration reuse guidance in project memory and verified the kokoro-web overlay wording did not need a fix
  - Clarified protocol docs so `session-stream.md` now distinguishes the current minimal closed loop from browser-reserved parse-and-ignore families, and downgraded future-only replay/mode examples accordingly
- Blocked:
  - Local git commits are still pending because the Claude Code auto-mode classifier denied commit commands while the repo contains a `CLAUDE.md` instructions file.
- Next verification / unblock step:
  - After commit authorization, review the parent-repo protocol doc diff together with the previously pending docs/progress changes, then run the parent-repo docs/progress commit.
