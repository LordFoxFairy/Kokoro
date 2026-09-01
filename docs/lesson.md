# 操作教训

只记操作级教训（场景 / 我做错的 / 下次怎么避免）。用户档案归 memory 系统。

## "我信任你"≠方案认可；方案必须成文可审后才有认可可言

- 场景：skills 重设计时用户说"参考 CC 我信任你/加油"，我当成放行直接开工——但 Mongo 存储模型、seed 链路、store 接口、测试形态他全没见过，第一次见就是代码，连环炸雷（内存 fake、fixture 天书、"太蠢了"）。用户："你根本没好好规划技术方案就开始写代码了，我也没有认可。"且这发生在他立下 align-before-execute 铁规的当天。
- 我做错的：把口头方向授权当成了对技术方案的认可；"对齐单"只写了行为层，存储/加载/测试这些真正的技术方案没成文。
- 下次怎么避免：动手门槛 = 一份**成文的、含数据模型/链路/边角语义/测试策略的 spec**（放 docs/superpowers/specs/）+ 用户对该文档的明确 OK。口头鼓励、方向性同意都不算。

## 动态性设计必须先过前缀缓存审计，"已知不一致"不许休眠

- 场景：MCP 用动态注册（load_mcp_tools 展开进工具面），我明知它与 per-run 选择冲突，标注为"已知不一致，V1 休眠，P1.5 修"。用户指出："设计动态的时候没考虑前缀缓存，无脑替换相当于每次都是新会话。"
- 我做错的：两层。① 低估：动态注册的变化源是**远端 server**（schema/顺序漂移不受我们控制），tools 块在 API 前缀最前，一漂移同会话全部缓存失效——不是"休眠风险"是"命门交给外部"。② 把设计错误当技术债标注留账，而不是当场修。
- 下次怎么避免：任何"动态"设计先过 handbook `20` D9 前缀不变量表——变化只允许表现为"工具返回的数据"或"append 的消息"，绝不允许是前缀段字节变化；发现前缀污染源，改设计而不是标注。

## 别拿通用 LLM 架构直觉套 kokoro 的 agent 运行机制

- 场景：打磨 `docs/kokoro-handbook/technical/19-...` 的 C 层（业务 agent 编排）时，我直接写"每个业务 agent 自定义 system prompt""切 profile 走新 run"。
- 我做错的：凭通用 agent 架构直觉 + 文档"应然"下笔，没先核 kokoro-agent 实际的 prompt 组织和 agent 切换机制，被用户连续纠正两次——(1) prompt 是 `kokoro-agent/src/kokoro_agent/prompts/` 专门目录的**静态 .md**、通用统一（`general.md`），业务差异靠 subagent/skill/tool + 阶段策略，**不是运行时拼 prompt**；(2) agent 间切换是 **langgraph-swarm handoff**（同 graph/checkpoint 对等移交主导权），**不是走新 run**。
- 下次怎么避免：写 agent 运行机制类结论（prompt 装配 / agent 切换 / 委派 / checkpoint）前，先派只读探子核 kokoro-agent 实际代码（`prompts/`、`agents/`、swarm/handoff 现状、`uv.lock` 依赖），**事实优先于直觉和文档应然**。

## 用户口头举例垂类 ≠ 允许把垂类细节写进正式文档

- 场景：讨论业务 agent 编排时，用户多次拿 music studio 举例；我顺势把 quick/advanced 双模（Suno 式入口形态）写进了 handbook `20` 正式方案。用户纠正："music 还没开始，暂时不写，聚焦通用和 agent 底座，你跑偏了。"
- 我做错的：把讨论中的垂类举例当成了给垂类写正式设计的许可。举例是帮助对齐抽象机制的，不是启动垂类。
- 下次怎么避免：正式文档只写通用机制 + "垂类 = 再加一个配置包"的抽象结论；任何垂类专属细节（入口形态、双模、阶段流程）等该垂类明确启动再写。

## 纸面方案会无限膨胀，只有落地才收敛（贯穿一整场的元教训）

- 场景：runtime/capability 技术方案，我连续十几轮在文档层打磨（加层、定案、全链路走查、派证伪 agent），每轮宣告"闭环 / 零开放项 / 最佳方案"，用户始终"总感觉有问题"。
- 我做错的：纸面方案能无限自洽地长大，我用"更周全"冒充"更成立"。几版"最佳方案"（registry 四层 → deliver 薄标记复用一个**不存在的** run 快照 → 内容寻址脊椎）前两版一证伪就塌；第三版可能又是我爱"优雅统一抽象"的过度设计。纸面推演给不出"真的 ok"这个答案。
- 下次怎么避免：方案主干清晰后就**转落地**——挑最小垂直切片真跑到 **typecheck + test + lint 全绿**，用运行证伪文档。实测教训：看 diff 觉得好但 `AU-2` 跑出 fail；`test 191 绿`但 `tsc` 还红；vitest 运行时不严格校验、typecheck 才抓到 fixture 漏字段。**落地一块的真绿，胜过纸面十轮的自洽。** 用户"总感觉有问题"的解药是落地，不是再审方案。

## 前端多视图改动：逐个走查每个视图/状态，别抽样几个就宣称完成

- 场景：整页设置中心 8-tab 重构，我只在浏览器验证了 account/skills/team/mcp 几个 tab 就宣告"完成、内容嵌入成功"。用户批评："能不能细心点，还有好多都是加载报错的。"
- 我做错的：前端有多个视图/tab/状态时**抽样验证几个当全体 OK**，且只在 happy path（登录态新）验证，没覆盖异常场景。实测根因是**会话过期后所有 tab API 401 满屏"加载失败"**——一个我从没走查的状态。
- 下次怎么避免：前端有 N 个视图/tab/状态，**逐个走查全部 N 个**（截图或 evaluate 遍历断言 ok/内容/返回入口），不抽样；验证覆盖**异常态**（会话过期/加载失败/空态），不只 happy path。对照 CLAUDE §5：宣称完成前，每个状态实际看到什么（loading/empty/error/success）都要过一遍。

## 改了实现只跑"定向测试"就宣称完成——全量套件里躺着我自己的回归

- 场景：整数扣费(ceil/min-1)改完，我跑了 credit 单测 164 绿就收工；dev 面板写完跑了 tsc+定向测试就提交。
  后来跑全量才发现：web 3 红（2 条是我引入：面板残留硬编码中文、i18n 覆盖率被我加的新键压破 95% 闸），
  platform 集成层 11 红（9 条是我的整数扣费回归——我只更了单测夹具，集成夹具还在断言 9600/2200 的小数额）。
- 我做错的：把"定向测试绿"当成"没破坏别的"。定向测试只覆盖我盯着的那几个文件，跨层护栏（i18n 完整性、
  硬编码文案闸、契约形状、集成夹具）恰恰在我没看的地方。更糟的是**整个集成层压根没被跑过**
  （pnpm -r test 只含单测；集成需 DATABASE_URL_* 没人接线），所以回归能安静躺很久。
- 下次怎么避免：**动了实现（非纯文档）就跑该仓全量套件**，别只跑定向；跨仓改动把相关仓全量都跑一遍。
  报绿前查两件事：① 有没有 skipped——静默 skip 会把"没跑"伪装成"跑过了"（本轮 session 8 条、agent 10 条
  因写死的 minio 密码整组静默跳，S3 链路真覆盖为零）；② 有没有**根本没被纳入 CI/默认命令的测试层**
  （本轮 platform 569 条集成从没跑过）。缺入口就补入口，别绕过。

---

# 历史教训归档

以下由 `tasks/lessons.md` 与 `kokoro-agent/tasks/lessons.md` 归并而来（原三处并存易漏读，现此文件为唯一权威）。
条目按原样保留，时间戳即当时记录日期。

## 主线（2026-05-28 → 07-06，原 tasks/lessons.md）

- 2026-05-28: Do not collapse Kokoro frontend, session/backend, and agent into a monorepo by default. The user requires each major system to be planned as an independent repository.
- 2026-05-29: For frontend engineering in Kokoro, proactively lean on relevant superpower skills plus frontend/design skills where they fit.
- 2026-06-02: Keep the main agent aligned with the user-facing conversation while background agents handle bounded execution, dispatch, and exploration. Defensive rule: restate the user goal in the main thread before delegating, give each background agent a narrow scope, and return synthesized progress/decisions instead of raw executor chatter.
- 2026-06-03: Verify UI at realistic SCALE, not the short happy path. A fixed-height chat shell looked fine with 1 message but broke with many (page scrolled, rail/composer pushed) — caught by the user, not me. Root cause: a CSS grid item defaults to min-height:auto and grows to its content, defeating a child's internal overflow; fix = grid-template-rows: minmax(0,1fr) on the grid + min-height:0 on the scrolling item's ancestors. Defensive rules: (a) before claiming a layout is done, test with enough content to overflow and confirm via JS that the PAGE is not scrollable while the intended container IS (document.scrollHeight==clientHeight; container.scrollHeight>clientHeight); (b) treat layout as one spatial SYSTEM — thread, composer, and rail must share alignment (a single --content-width token), avatars top-aligned, balanced bubble widths — don't build pieces in isolation; (c) reactive one-off CSS patches without visual+scaled verification waste the user's patience — make the holistic fix and screenshot it.
- 2026-06-03: For kokoro-web UI, default to compact, conventional chat sizing — NOT oversized. The 06-02 "larger Gemini card / huge headline" spec was over-scaled; the user wants normal app proportions. Defensive rules: (a) keep hero/headline ≈2–2.5rem, rail avatars ≈2rem, composer/body text ≈0.95rem; (b) chat threads must use a comfortable two-sided bubble layout — assistant left (bubble + avatar), user right (tinted bubble) — not borderless full-width prose; (c) NEVER let hover/focus change an element's box size (padding/width) inside a shared row — it reflows neighbors and feels like jitter; change only color/shadow/opacity on hover.
- 2026-06-04: A pluggable transport with a memory adapter for tests will HIDE bugs that only exist in the real adapter. The three-repo loop passed every unit test (44/79/26) yet had never actually streamed over Redis — because the session SSE conflated two cursor namespaces: it resumed `subscribe()` from the domain `envelope.cursor` (a "run_x:NNNN" string) as if it were a Redis stream id, and passed "" on first connect. Redis XREAD rejects both as invalid ids → `/stream` silently delivered nothing. MemoryStreamPort's lexicographic `cursor > lastCursor` compare happened to accept both, so tests stayed green. Fix: subscribe the replay stream from its head (one transport-cursor namespace; replay+tail in a single subscribe) and coerce falsy cursor→"0-0"; regression test asserts live events tail after a NON-EMPTY snapshot (the path tests never exercised). Defensive rules: (a) before claiming a cross-process loop works, run ALL processes together against the REAL transport (Redis) early — green unit tests on a memory adapter prove nothing about the wire; (b) never conflate a domain sequence cursor with a transport stream id, even when both are called "cursor" — they are different namespaces; (c) the discriminating test for "real vs simulated/fallback" must be visible in the artifact (here: the fake-model's "Local fallback active…" reply + a "实时" transport label distinguished the live path from the preview fallback).
- 2026-06-04: New CSS in globals.css rendered as unstyled text in the browser even though the rules were on disk and lint/typecheck/test/build were green. Root cause: TWO `next dev` servers (ports 3100 + 3200) were running from the SAME repo, sharing one `.next` dir, and Turbopack served a STALE compiled CSS chunk (had the old `.kk-shell__hero`, missing the new `.kk-starter`) — a plain dev-server restart did NOT fix it because the new server reused the poisoned cache. Fix: kill ALL dev servers on the repo, `rm -rf .next`, start exactly ONE. Defensive rules: (a) jsdom tests never apply CSS — to verify styling you MUST check the rendered page (computed style / served stylesheet text), not the file on disk; (b) never run two dev servers from one repo — they corrupt the shared `.next`; (c) when served output disagrees with source, suspect a stale build cache and bust `.next` rather than re-debugging the source.
- 2026-06-06: 当用户要求“先对齐状态 / 看遗留任务”时，先区分**当前选定基线分支上的真实状态**与**曾经在别的分支/文档里记录过的更晚状态**。防御规则：先用 `branch --contains <milestone-commit>`、代码 grep、当前分支 HEAD 三者交叉验证，再更新 `claude-progress.md` / `tasks/todo.md`；不要把别的分支上的 later work 直接当成当前基线已完成，也不要把当前分支已包含的里程碑继续误记成未完成。
- 2026-06-06: 做前端演示打磨、交互细节与模式差异化时，如果条件允许，优先用 Playwright 做浏览器级实时调试与可视验证，而不只依赖单测或静态代码判断。防御规则：涉及“看起来舒服不舒服”“模式差异是否可感知”“交互是否顺手”这类问题时，把 Playwright 当作主验证手段之一，并在交接里写清实际看到的行为。
- 2026-06-10: DDD 架构审查绝不能只看"无循环依赖/依赖方向对"就判 clean——必须检查是否真有 `domain/application/infrastructure/interfaces` **分层目录**且文件各归其位。kokoro-agent 把 `events`/`run_agent`/`event_translator`/`content_extractors`/`subagents`/`worker` 6 个文件平铺在包根、只有 `infrastructure/` 一层，而 session/web 都是规范四层；我却接受了 workflow 审计的"agent layering generally clean"（它只验了依赖方向没看目录），还以为 agent 的 DDD 整理做完了，被用户当面指出"agent 架构最垃圾、没有严格 DDD"。防御规则：(a) DDD verdict 必须对标"分层目录 + 文件归位"，平铺包根=不合格，依赖再干净也不算 DDD；(b) 子代理/审计给的 clean/minor 要自己 `find src -name '*.py'` 对比同项目其它 repo 的分层结构交叉核验，绝不直接采信；(c) "DDD 整理" = 建立四层 + 文件归位 + 依赖倒置，god-file 拆分只是其中一步，不能拆完文件就宣称 DDD 完成。
- 2026-06-11: 文件名前缀重复 = 缺子目录的信号；类型遮掩(cast/ignore)不能借口"边界"放过。两宗都被用户当面骂"问题严重/根本没优化"。(1) kokoro-web `application/` 里 `session-stream-reducer/-transport/-simulator/-state.schema` 四个文件同前缀平铺——同前缀重复 N 次就该是 `session-stream/` 子目录 + 去前缀文件名(`session-stream/{reducer,transport,simulator,state-schema}`)，我却只做了"改名去丑词"的浅层优化没建子模块目录。(2) agent stream 文件 30+ `cast`/`# pyright: ignore`，我借 critic 的"langchain 无类型边界、留到 codegen 后"放过——但用户洁癖明令禁 cast：必须用 `TypeAdapter`/`Protocol`/窄类型 wrapper 在边界一次性洗净，把 `Any` 收敛在单个适配函数里而非散落 30 处 cast。防御规则：(a) 同目录出现 ≥3 个同前缀文件，立即评估抽 concern 子目录 + 去前缀，别平铺；(b) cast/type-ignore 默认是债不是边界，先问"能不能用 TypeAdapter/Protocol/泛型洗净"，只有证明确属第三方未类型化 SDK 且无法包装时才以单处 1 行 WHY 保留；(c) "优化/DDD 完成"的判据是用户看着目录和类型舒服，不是测试绿——浅层改名 ≠ 架构优化。

## 2026-06-13 按进程名 kill 误杀用户长跑进程
- 场景:e2e 收尾换 worker 时用 `pgrep -f kokoro-agent-worker | xargs kill`,把用户上一会话留跑的 db14 worker 一并杀掉(暴露于陈旧后台任务的 exit 144 通知)。
- 我做错的:按名字模式杀进程,而同一二进制有用户进程在共存。
- 下次怎么避免:自己起的进程必须记 PID、按 PID 杀;任何 pgrep/pkill 模式匹配前先 `pgrep -lf` 人工核对每一条;杀完立即恢复并向用户如实报告。

## 2026-06-13 uv.lock:合法依赖变更被惯性 checkout 撤销 + aliyun churn 根治
- 场景:`uv add httpx` 后按惯例 `git checkout uv.lock`,把合法 lock 变更也撤了,pyproject/lock 漂移(`uv sync --locked` 失败),且首次提交漏掉 lock。
- 我做错的:把"撤销 aliyun churn"惯性应用到真正的依赖变更上;提交前没跑 `uv sync --locked` 验一致性。
- 下次怎么避免:依赖变更后用 `UV_NO_CONFIG=1 uv lock` 重锁——绕开本地 aliyun 镜像配置,产出官方源最小 diff,可直接提交;任何 pyproject 依赖改动的提交前必跑 `UV_NO_CONFIG=1 uv sync --locked`(本地镜像配置下裸跑 --locked 会因 index 不匹配误报)。日常 `uv run` 后的 checkout 惯例仅适用于无依赖变更场景。

## monorepo 收敛提案被否（2026-06-14）
- 场景：item 4 架构打磨，我把"4 独立仓 → monorepo 收敛"作为大胆优化建议提出。
- 我做错的：把跨仓 contract CI 的摩擦当成"该合并"的论据。用户明确否决——"本来就是四个独立子仓库，为什么放一个大仓"。4 仓拆分是**有意的架构**（独立可部署：agent Python worker / session TS server / web Next.js，各自 runtime、各自 remote、各自 CI）。
- 下次怎么避免：**不再提 monorepo 收敛**。跨仓契约的"双向维护"摩擦用 **codegen 单源生成**解决（generator 在 root，生成进 4 仓镜像），而非合并仓库。架构打磨一律在 4 仓结构内做。

## 2026-06-15 大文件/循环依赖/边界类型收口不够细
- 场景：用户指出 agent `run_agent.py` 问题很大，并质疑为何审批工具会自动超时、为何还靠 `_str_field` 从松散 payload 里抠字段；同时指出我在 Python/TS 都容易把文件写大，导致循环 import 压力和职责混杂。
- 我做错的：把多个 concern（审批语义、事件翻译、segment 归并、配置拼装、memory 接线）堆进同一文件里；为了先跑通链路接受了 `Mapping[str, object]` 边界，再用 `_str_field` 这类 helper 在下游兜底；文件粒度过粗让依赖边界模糊，后续一加功能就推高循环依赖风险。
- 下次怎么避免：1) 新行为先找最小宿主文件，单文件同时承担 >2 个 concern 时优先拆；2) 边界类型问题尽量在上游一次性收紧（TypedDict/Protocol/适配器），不要让下游靠 `_str_field`/`cast` 连续兜底；3) 任何需要把“取消/审批/记忆/流式翻译”同时改进同一文件时，先停下来按 concern 拆 helper/子模块，再继续加功能；4) Python/TS 都把“避免循环依赖”当设计目标，不等 import 爆了再补救。

## 2026-07-03 底层工具的分层三连（namespace→vendor→目录）
- 场景：实现 memory/web 底层工具时，先后把租户 scope 读取、zhipu vendor 代码、一级目录 search/ 混进了工具层。
- 我做错的：把"政策/vendor/归置"当成实现细节随手就近放，没有先过"这属于哪一层"的关。
- 下次怎么避免：底层工具 = 通用原语，铁律三问——①体内有没有租户/环境政策？（应装配注入）②体内有没有 vendor 词汇？（应适配器外置，注册表选择）③文件归置是否与所属域同处？（工具的配套件放 tools/ 下，不占一级目录）。写完先自查再交。

## 2026-07-04 i18n 设计不能只停在 translator
- 场景：设计 `kokoro-i18n` 时先实现了 locale/key/catalog/translator，但用户指出技术方案详细设计必须说明并覆盖“翻译会用到的位置”，本质是文本 key 在展示边界被替换成文案。
- 我做错的：只证明 key 能被翻译，没有把 `labelKey` 这类实际 translation slot 建模，也没有给 admin/module manifest 的嵌套位置提供明确替换 API。
- 下次怎么避免：i18n 设计必须同时回答三件事：① key 的格式与词典；② key 出现在哪些结构位置（labelKey/titleKey/descriptionKey 等）；③ 在哪个边界把 key 解析成展示字段并保留可审计原 key。测试必须覆盖真实位置，而不是只测孤立 `translate(key)`。

## 2026-07-04 身份轴漂移（hub v2 发明 user 层级）
- 场景：设计 skills/MCP hub 用户维度时提出"platform→namespace→user→entry"四级 + user_id 回归契约。
- 我做错的：违背自己档案里的既定法律（namespace 模型：teams/个人=namespace 实例）——给系统开了第二条身份轴。
- 下次怎么避免：任何涉及"谁的空间/谁的资产/谁的记忆"的设计，先复述单轴法则（个人=personal namespace）；出现"user 级/组织级/项目级"字样时一律先问能否表示为 namespace 实例+跨空间 grant。

## 2026-07-04 初期项目不写迁移兼容层
- 场景：ledger 重命名时给旧 env 拼写（KOKORO_RUN_STATE_*）加了 fail-loud 迁移闸 + 迁移测试。
- 我做错的：把"生产系统改名要留迁移路径"的惯性带进了初期项目——用户裁定：直接删除重新来，避免初期就遗留兼容代码。
- 下次怎么避免：本项目未上生产前，重命名/重构一律删旧换新，不写垫片、不写迁移错误提示、不留双拼写；"兼容"二字出现时先问一句"现在有真实的旧消费者吗"，没有就不写。

## 2026-07-04 代码注释不写排期黑话
- 场景：web reducer 穷尽分支注释写成"V1 不渲染；子代理详情视图（P1）再消费"，用户指出注释要专业。
- 我做错的：把 roadmap 词汇（V1/P1/再消费）当注释——那是对评审者说话，不是对下一个读者说约束。
- 下次怎么避免：注释只陈述代码本身承载不了的约束（这里是"穷尽 switch 须显式接收、无消费视图不参与归约"）；出现版本号/优先级/排期词即重写。

## 2026-07-04 展示文案不走 wire（用户批 HITL 卡英文模板+裸 JSON）
- 场景：ask_user 卡把 deepagents 的英文 interrupt 模板（description）当问题文案渲染，还平铺入参 JSON；用户批"没看懂"并点出语言应随用户。
- 我做错的：把执行侧调试语料直接当 UI 文案；数据（args.question）反而没有语义化呈现。
- 下次怎么避免：法则"wire 只带数据，展示文案归 web（zh）"；任何 wire 字段上屏前先问"这是数据还是执行侧调试语料"；模板英文出现在 UI 即红灯。

## 2026-07-04 工具配套件二犯：指引文案囤在拼装点（用户批 context.py）
- 场景：四个工具的行为指引文案硬编码在 orchestration/context.py 的 _SECTIONS 表里，用户问"工具的信息为什么不放工具那里"。
- 我做错的：与 2026-07-03"分层三连"同族——把工具的配套件（prompt 指引）当拼装细节就近堆在消费点，加工具要改拼装点（散弹手术）。
- 下次怎么避免：工具的一切配套件（名字/指引/自述/schema）随本体文件；拼装点只持有"排序与组合"这一个关切。自查问句："删掉这个工具时，要改几个文件？"答案必须是 1。

## 2026-07-04 三连改被批"不带思考"（context 指引→工具指引→编排结构）
- 场景：用户连续纠正同一族问题（指引进 system prompt、SteeringMiddleware 归属、编排无类型结构），我每次只做最小局部反应，被批"深度思考而不是根本不带思考的"。
- 我做错的：把每条批评当孤立缺陷贴补丁，没有停下来从第一性原理推整体形状，导致用户被迫逐个纠正、结构反复震荡。
- 下次怎么避免：同一区域收到第二条批评时强制停手，先推导完整设计（这块系统的本质构成是什么、每样东西的唯一归属地在哪、扩展时哪些是增量）再动；答卷先给"整体形状+为什么"，再给改动。本次定案：类型的两个家=prompts/ 资产 + orchestration/<type>.py 配方，第三个镜像目录即死结构；prompt 文本出现在 .py 里即红灯。

## 2026-07-04 对偶性检验句入册（成品/子代理二元论）
- 场景：用户要求深度思考内部 subagent 与顶层成品的区别与设计；推导出对偶性定律并实锤修复 wire_subagents 解析断裂。
- 收获（非错误，防漂移）：任何成品设计必须过问"降格为子代理时还能工作吗"；成品三元各归其家（资产 prompts/、bundle 归 session/hub 数据、配方 orchestration/<type>.py）；通用域出现类型词汇即红灯。

## 2026-07-05 契约镜像漏批（web CI 红）
- 场景：web 挑拣提交组件文件时把 generate 产出的 src/contract 镜像留在工作区，本地 tsc 绿（工作区有新镜像）、CI 红（checkout 旧镜像），并连带父仓 byte-diff 门禁红。
- 我做错的：绕开 git add -A（因他人现场）改挑拣提交后，没有把"镜像与消费代码同批"当硬规则。
- 下次怎么避免：contract generate 之后，各仓 src/contract 的改动永远属于当前批次；挑拣提交前跑 `git status src/contract` 自查；本地绿≠CI 绿，挑拣模式下以"CI 视角文件集"过一遍。

## 2026-07-05 platform i18n 预览放错仓
- 场景：为验证 i18n 管理界面，把 admin i18n preview 放进 `kokoro-platform/src`，再挪到 `kokoro-platform/tools`，用户指出 platform 主仓和 tools 都不该承载 web/admin UI。
- 我做错的：把"平台 i18n 能力验证"和"web/admin 页面承载"混成一块；子仓库边界被临时预览服务污染。
- 下次怎么避免：platform 只放领域能力、catalog、registry、manifest 聚合和测试；任何 web/admin UI 与 HTTP route 必须在承载子仓一体化实现。宁可没有预览，也不要在 platform 增加 `src/*preview` 或 `tools/*preview`。

## 2026-07-05 git add -A 三犯（web 仓 i18n 现场两度被打包）
- 场景：web 仓提交三次误用 add -A 把 i18n 会话的进行中文件带进提交（4b2b3a2、ad0fb95）。
- 我做错的：知道规则（挑拣提交）但肌肉记忆在多仓切换时带偏；且未在提交前跑 git status 自查。
- 下次怎么避免：**web 仓永久禁 add -A**——一律 `git add <显式文件列表>`；任何仓提交前先 `git status --short` 扫一眼陌生文件；共享工作区（他人会话活跃）视为雷区。

## 2026-07-05 刷新丢历史的根修（事件溯源闭环）
- 场景：用户报"刷新后只剩输入的"；根因=wire 无 user 消息事件，线程被迫 snapshot 直投+续传混合体，过程步在夹缝里丢。
- 收获：**事件史必须是线程的唯一完整真源**——补 message.user 合成事件后水合=全量回放（折叠幂等），三坨机械（snapshot 消息投影/hydratedStreaming 占位/空失败气泡）随之整体消失。混合真源=bug 温床。

## 2026-07-05 验证脚本进程泄漏 = 假绿制造机（本轮最大教训）
- 场景：chaos S3 四项 FAIL 排查发现 session-2/session-b 全部 EADDRINUSE——历次运行泄漏的 tsx 僵尸占着端口，"验证"实际打在旧代码进程上（S1/S2 假绿、S3 假败）；且 `proc.kill()` 只杀 npm/uv 包装层，混沌注入 SIGKILL 等于没发生。
- 我做错的：subprocess 直接 Popen+kill/terminate，从未管进程组；跑完也没检查端口归还。
- 下次怎么避免：**验证脚本一律走 scripts/procutil.py**（start_new_session + killpg + ensure_port_free fail-loud）；新增常驻服务的脚本先想清楚"谁负责杀掉整棵进程树"；跑完 lsof 验端口归还。

## 2026-07-05 终判提前 return = 吞失败（Fail Loud 违规）
- 场景：chaos-verify 的 `if FAILURES: return 1` 写在 S3 场景之前，S3 四项 FAIL 后仍打 PASS、exit 0。
- 下次怎么避免：多场景验证脚本的 FAILURES 终判只允许出现在**全部场景之后**一处；每加新场景检查终判位置。

## 2026-07-05 走查 locator 惨案：非 exact 匹配点中删除按钮
- 场景：`getByRole('button', {name: '标题'})` 同时命中"删除会话 标题"按钮，我把两个会话删光，然后花半小时排查"列表崩塌"这个不存在的产品 bug。
- 下次怎么避免：走查里按可见文本定位一律 `exact: true`；破坏性按钮（×/删除）与标题同名时优先用 aria 精确名；出现"诡异丢数据"先怀疑自己的 locator。

## 2026-07-05 目录残渣与词义过载让用户"看不懂"
- 场景：用户点名 agents/ + orchestration/ 看不懂。排查：agents/ 是重构后没删的空壳（本地残渣）；orchestration 一词做的是装配、而项目里该词已被 swarm 概念占用——同词两义。
- 我做错的：搬走内容没删旧目录；起名时没检查词汇在本项目的既有占用（测试都叫 test_assembly 了目录还叫 orchestration）。
- 下次怎么避免：重构收尾 `git status` + `find` 双查空目录残渣；起顶层域名前先 grep 该词在 handbook/memory 的既有含义，一词一义。

## 2026-07-05 结构设计连续三次被批的元教训
- 场景：agents/orchestration → assembly → 包层 → 工厂，同一层连改四轮才对齐用户心智（一类型一 py 的 Factory、政策即类属性、杂烩按域归位）。
- 我做错的：每轮只修用户点名的表象（删空壳/改名/包化），没有一次性追问或推演"这层的终态形状"；parts.py 这类"共享杂物桶"每轮都残留。
- 下次怎么避免：动结构前先写出"这层的终态目录树+每文件一句话职责"自审——出现"parts/utils/common"命名即警报；用户批评一次=심智模型偏差信号，先重建对方的完整心智（factory？plugin？）再动手，别挤牙膏。

## 2026-07-05 深度自审的两类漏想（用户"很多细节没想明白"点醒）
- 场景：自审挖出①入口对偶性缺口（entry 作下属丢 skills）②docker+s3 静默组合缺陷（归档只挂 local_shell 分支）。
- 我做错的：加正交维度（文件面×执行沙箱）时只验证了各自主路径，没扫组合矩阵；加"入口既是主又是下属"的对偶结构时没逐字段核对两形态的能力面等价。
- 下次怎么避免：正交配置维度落地时列组合矩阵逐格问"这格行为是什么"（静默降级=缺陷）；对偶/降格结构逐字段核对能力面守恒。

## 2026-07-05 "同一关切两套机制"是结构性没想明白的标志（资产源 vs workspace）
- 场景：用户点破 skills 挂载与 s3/minio 文件面"应该统一"——workspace 有 type 判别 yaml（local/s3），资产却只有本地目录 env，还留了条"多 pod 自行分发资产"的运维红线。
- 我做错的：给资产做机制时没有横向扫一遍"系统里还有谁在回答'文件从哪来'"；把一致性难题写成部署红线交给运维，而不是消掉它。
- 下次怎么避免：新机制落地前先问"这个关切在系统里已有的答案是什么"，同关切必须同抽象；写"部署红线/运维须知"时警觉——红线常常是设计债的遮羞布，先想能不能用一档配置消掉。

## 2026-07-05 100 行独木函数：内联表达式堆叠让用户三处看不懂
- 场景：general.py create() 把四路工具来源、两条中间件链、人格三级 or 链、审核悖论校验全部内联，用户连问三处看不懂（or 链 / ask_user 校验 / web_tools 是啥）。
- 我做错的：只顾行为正确，把"每步是什么"编码在注释而非结构里；web_tools 这种与 kokoro-web 撞名的词没有就地消歧。
- 下次怎么避免：装配类函数按"一步一具名模块/函数"拆，主干读起来是目录页；被问"这是什么"的名字=命名债，要么改名要么就地一行注释消歧（web=互联网，非 kokoro-web）。

## 2026-07-05 被质疑就钟摆：从"修复机制"直接摆到"全删机制"
- 场景：用户连环质疑 thread TTL（"什么玩意/1w 个就 g 了/缺这点磁盘吗"），我把质疑当裁决，未经讨论就开始全仓拆除；被叫停："不是我说不需要你就真不需要了，你应该和我讨论。"
- 我做错的：把用户的困惑/不满当成了删除指令；没有先给出"这机制解决什么、我的立场、可选项"三件套就动手做破坏性变更。
- 下次怎么避免：质疑≠裁决。破坏性结构变更（删机制/删表/删配置面）必须先摆立场和选项、拿到明确裁决；执行中途被连环质疑时停下来对齐，而不是边挨骂边换方案。

## 2026-07-06 git add -u 吞掉新文件：本地全绿、CI 必红
- 场景：新建 src/relay/delete-session.ts 后用 git add -u 提交，未跟踪新文件被漏掉；本地测试因文件在盘全绿，CI typecheck 直接 Cannot find module。
- 下次怎么避免：提交前 git status --short 里出现 `??` 行必须逐个显式处置（add 或说明不提交）；新建文件的提交永远显式列文件名，git add -u 只配纯修改场景。

## kokoro-agent 侧（2026-06-24，原 kokoro-agent/tasks/lessons.md）

## L1 (2026-06-24)：v3 重写里别照搬 v2 的防御脚手架

**场景**：把 ACL 从 astream_events v2 迁到 v3 typed projections 时，我把 awaiting.py 的
`_is_object_mapping`/`_last_ai_message`、invoke/supervisor 的 `TypeGuard`+`getattr(snapshot,...)`
手刨 interrupt payload 的写法，从 v2 直接搬了过来。

**我做错的**：在 langchain 1.0+ v3、框架已锁定（永不更换）的前提下，本该直接吃框架的 typed 结构，
却把所有 interrupt/snapshot 值收成 `object` 再用 isinstance/TypeGuard 手动收窄——这是 v2 时代
（流是裸 dict）才需要的防御，在 v3 里纯属冗余噪音。用户明确反问"为什么有这些存在"。

**下次怎么避免**：迁移到强类型框架 API 时，先查框架提供的 typed 结构再写代码，别凭惯性套旧防御：
- HITL interrupt：`langchain.agents.middleware.human_in_the_loop` 有 `HITLRequest`/`ActionRequest`/
  `ReviewConfig`/`Decision` 全套 TypedDict；`langgraph.types.Interrupt`(`.value`,`.id`)、
  `StateSnapshot.interrupts: tuple[Interrupt,...]`(顶层直接有，别去 tasks[].interrupts 手刨)、
  `StateSnapshot.values: dict[str,Any]`。
- 框架值确实是 `Any` 的边界（如 langgraph 图 state values），收窄**一次**就够，别造 TypeGuard 塔。
- **唯一仍需结构校验的**：不可信的**模型工具输出**（如 write_todos 的 todos 来自 LLM），那是真·外部
  载荷洗净（项目铁律），与"框架 typed 值上套防御"是两回事，别混为一谈。

**区分原则**：框架产出的 typed 值 → 直接用其类型；外部/模型产出的不可信载荷 → Pydantic/校验洗净。

## L2 (2026-06-24)：别把自己能推理的判断题甩回给用户猜

**场景**：typed-payload 打磨，多 lens 评审后我用 AskUserQuestion 让用户在 wash_args 保留/回退、
source 收窄、interrupt 一致性三项上拍板。用户回"我又带你猜""能不能别问我"。

**我做错的**：把"≥3 轮交互评审"误解成"每轮都让用户做决定"。这三项都有充分工程依据
（goal 意图 + 代码事实 + 既定约束）可自决，却 offload 成开放选择题让用户猜。

**下次怎么避免**：交互评审 = 我出**带依据的结论**供用户复核/否决，不是把开放题推回去。
能用"代码事实 + 既定约束 + goal 意图"推出的取舍，自己定并讲清理由；只有真属于产品/业务方向、
我无依据可循的才问。问之前先自检：我是真没依据，还是在偷懒回避思考？

## L3 (2026-06-24)：设计文档放 docs/superpowers/，不放 tasks/、不 commit

**场景**：写分通道 spec，先往 `docs/superpowers/specs/` 写（被 gitignore），又自作主张移到 `tasks/`
并 commit。用户怒："你又不是看不到"——`docs/superpowers/specs/` 里**本就躺着 v3 那批 spec/plan**。

**我做错的**：(1) 没先 `ls docs/superpowers/specs/` 看兄弟文件就乱放；(2) 看到 docs/ 被 ignore，
就擅自改去 tasks/ 还 commit——既破坏约定（tasks/ 只放 todo.md/lessons.md），又把本该本地的
设计文档塞进版本库。

**下次怎么避免**：本仓设计产物的家 = **`docs/superpowers/specs/`（spec）、`docs/superpowers/plans/`（plan）**，
gitignore、**本地工作文档、不 commit**。写前先 `ls` 看既有兄弟、就地放进去。`tasks/` 仅
`todo.md`/`lessons.md`。看到目录被 ignore，是"别 commit"的信号，不是"换地方"的信号。绝不为了让它
被 track 而搬家。

## L4 (2026-06-24)：AgentEvent 信封是唯一 JSON 边界，别在它前面再撒校验

**场景**：tool_call_start 的 args 我加了 `wash_args`/`as_json_args` 在 transformer 里逐键/整盘
validate JSON。用户连呼"为什么要丢弃""多此一举""毫无意义"。

**我做错的**：`AgentEvent` 信封本身就是 `model_config(strict=True)` + `data: dict[str, JsonValue]`，
`model_validate` 时**已经把整个 data（含 args）校验过一遍 JSON 安全**。我在它前面又 validate 一次
args，纯属重复；而且"逐键 try/except 丢弃"还会静默吞掉键，把本来能跑的 args 搞得不一致。这是
[[L1]] 同一个病的又一次发作——在框架/模型产出的结构化数据上撒手搓校验。

**下次怎么避免**：**单一 strict 边界原则**——对外只有 `AgentEvent.model_validate` 这一道 JSON 关；
它前面的投影层只管把框架/模型给的数据**原样透传**，类型如实标（langchain 给 `dict[str, object]`
就标 `dict[str, object]`，别强转 `JsonValue` 逼出"转换/洗净"代码）。模型生成的 tool args 必是 JSON，
真出现非 JSON 让信封那一关报错即可，不在前面静默丢。

**补（2026-06-24，用户进一步纠正）**：连 `custom_event` 的 `_wash` 也删了——同理，custom 载荷也被
信封校验，wash 多余；`get_stream_writer` 业务遥测本就该是 JSON，非 JSON 让信封报错即可。`_ev` 这种
偷懒缩写也改成标准名 `_make_event`。**原则贯彻到底：投影层零 wash，全部原样透传，类型如实。**

## L5 (2026-06-24)：wire 是 canonical 就该自洽对称，别把 consumer 细节倒灌进 wire

**场景**：分通道设计里我让 reasoning 通道"只发 delta 不发 final"，而 text 通道发 delta+final。
理由是"web 现有 thinking reducer 是纯续写"。用户质疑："langchain 本身这么干吗？不一致后续排查困难吗？"

**我做错的**：把**消费端（web P4）的当前实现细节**倒灌进了**对外 canonical wire** 的设计，造成两通道
不对称。langchain 的 `.text`/`.reasoning` projection 本就对称；wire 是单一真理源，就该自洽。不对称 =
后续"为何 text 有终态帧 reasoning 没有"翻半天。

**下次怎么避免**：wire/契约设计只对**自身一致性 + 上游（框架）语义**负责，**不为下游消费者的当前实现
打折**。下游不支持就 P4 改下游（reasoning final 当 replace，与 text 一致），而非把 wire 改残。
对称的东西就对称建模。

## L6 (2026-08-30)：先区分全局基础设施配置与仓库架构文档

**场景**：用户说要把开发配置记在全局，并让 Cloudflare、服务器、GitHub 配合部署；我先改了仓库文档，用户随后纠正为 Cloudflare Tunnel/服务器配置。

**我做错的**：把“全局配置”误解成仓库内的产品/运维文档，没有先确认目标是本机全局工具链与远程部署链路。

**下次怎么避免**：先按三方边界拆解：GitHub 管源码与 CI，服务器跑 Docker Compose，Cloudflare Tunnel 做入口；凭据只进 SSH key、GitHub Secrets 或服务器 Secret，不写入文档。
