# Lessons

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
