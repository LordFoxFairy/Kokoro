# 交接:技术方案打磨复盘 + WP-0 落地 + 给下一个 code agent 的审核

状态:2026-07-09。用途:给下一个 code agent **审核思考**,不是执行派工。
先读本文的"一句话现状"和"元教训",再按需读 `19`。

## 0. 一句话现状

runtime/capability 主线方案(`docs/kokoro-handbook/technical/19-current-runtime-capability-review-plan.md`)已被打磨得很详尽,**但其中绝大部分是纸面自洽、未经任何运行验证**。唯一真正落地、跑到 `typecheck + test + lint` 三绿的是 **WP-0 namespace 地基**(在 kokoro-session gitwarp worktree,未 commit)。审核时务必区分"三绿的事实"与"纸面的方案"。

## 0.1 这一场经过(背景叙事)

- **起点**:在 `19` 主线上继续打磨 runtime/capability 技术方案。
- **过程**:上一轮 agent 连续多轮做文档层打磨——补 principal 独立轴、业务 agent 编排层(C 层)、stage 契约、swarm、12 步一致性契约、8 项决策、三个断头(Selection 层 / artifact 读接口 / run.steer)修补。中途被用户多次纠正:prompt 是 `prompts/` 目录里的静态 .md(不是运行时拼)、agent 切换用 langgraph-swarm handoff(不是走新 run)、`submit_artifact` 命名反人类(改 `deliver`)、多次警告"过度设计 / 绕远"。
- **转折**:用户始终"总感觉有问题"。上一轮 agent 最终认清根因——**纸面方案会无限自洽地膨胀,自己一直在用"更周全"冒充"更成立"**;几版"最佳方案"前两版一证伪即塌。于是从纸面转落地。
- **落地第一步**:review 那份未提交的 namespace worktree → 跑测试当场发现 `AU-2` fail(run record 缺 namespace)→ 接手补完 → `typecheck + test + lint` 三绿。这是整场唯一有运行证据的成果。

## 1. 元教训(最重要,先读)

已记 `docs/lesson.md`:**纸面方案会无限自洽地膨胀,"更周全"不等于"更成立"。** 上一轮 agent(即本文作者)连续十几轮文档打磨,每轮都能宣告"闭环 / 零开放项 / 最佳方案",但:

- 几版"最佳方案"(registry 四层 → deliver 薄标记复用一个**不存在的** run 快照 → 内容寻址脊椎)前两版一证伪就塌。
- 用户始终"总感觉有问题",直到落地跑第一块才产出真结果。
- 实测:看 diff 觉得好但 `AU-2` 跑出 fail;`test 191 绿`但 `tsc` 还红。

→ **给你的第一条建议:不要再堆文档。方案主干已够清晰,继续纸面打磨是自欺。你的审核方式应是"证伪 + 落地跑绿",不是顺着 `19` 夸它周全。**

## 2. 已落地的事实(WP-0 namespace,三绿)

worktree:`kokoro-session/.gitwarp/worktrees/agent/session-namespace-auth-persistence`(分支同名,**未 commit**)。

- namespace 从实例级(`KOKORO_NAMESPACE` 进程常量)改为 **session 持久化 + 全链路反查**:auth 产出 namespace、`session.namespace` 落库、relay/snapshot/file-read/RunRequest 全部按 `session_id → session.namespace` 反查。
- namespace = `payload.sub`(= ownerId);forbidden-prefix 拒绝 `user:/team:/site:` 等前缀作 namespace;public snapshot(`SessionMeta`)不暴露 namespace;存量文档 `namespace ?? owner_id` backfill。
- 本文作者接手补完的:原作者给"run record 也带 namespace"写了断言但实现没跟上(`AU-2` fail),补了 `RunRecord.namespace` + `putRun` 传值 + mongo `toRunRecord` 透传 + 5 处测试 fixture。
- 验证:`npm run typecheck` / `npm test`(191 passed)/ `npm run lint` **三绿**。

审核点:这块是真的,但**未 commit**;要不要 commit/收编是个待定决定。`namespace = sub(ownerId)` 是 V1 务实简化(见 §4)。

## 3. 还是纸面的(`19` 里写得像定案,但都没落地,按"待证伪"对待)

- **能力线**:`19` 早期写了 registry 四层(`skill_registry` / `CapabilityResolver` / binding store),**这版已弃**。改方向为"skill = 沙盒文件 + 内置 `find_skill` 发现,不建 registry"(Claude Code 式渐进披露)——但**没落地、没验证**。MCP 是服务连接不是文件,不适用沙盒模型,单独走稳定 adapter。
- **产物 deliver**:命名从 `submit_artifact` 改 `deliver`。形态仍未定:"独立 content-hash keyspace 冻结" vs "薄标记复用 run 快照"(**已被证伪**:run 快照不存在,归档是 session 级覆盖写)vs 最土的"复制到只读目录"。**没定、没验证。**
- **C 层 / stage 契约 / swarm / 专属 agent**:全是 P2 蓝图,V1 不做,别照 `19` §3.2/§3.3 字面实现。
- 8 项决策(§3.5)、12 步一致性契约(§3.6):除 WP-0 外都是纸面。

## 4. 证伪抓到的真洞(读真实代码确认,待落地)

- **local-user fail-fast 缺失**:生产忘配 `authSecret` 时,`kokoro-session` auth 直通模式让任何人串所有人数据。高危、改动小 —— 建议下一块落地。
- **epoch/fencing 缺失**:`kokoro-agent` supervisor 里 lease 过期原 worker 复活会双跑,代码注释自认审计缺口。
- **platform principal 不存在**:principalId 语义/表在 platform 零实现。V1 务实结论 = namespace 直接用平台给的主体 id(现为 sub),**不建独立 principal 表**(`19` 早期"必须独立表"已放宽为务实版)。
- **归档 session 级覆盖写**:对象键 `{namespace}:{session_id}/{path}`,无 run 边界、无 content_hash —— 是 deliver 不可变问题的根子。

## 5. 给你的审核思考清单

1. 别顺着 `19` 夸周全 —— 它大部分是纸面。用证伪视角:从零落地会卡哪、边界能不能被打破。
2. deliver 到底要多简?**先质疑"内容寻址脊椎"是不是过度设计**,V1 是否"复制到只读目录"就够。用最小实现验证,别照文档建重的。
3. 能力线 "skill = 沙盒文件 + find_skill" 方向对不对?落地一小段验证,别建 registry。
4. WP-0 三绿 worktree 要不要 commit/收编?`namespace = sub` 的务实简化能不能接受?
5. 下一块落地建议:local-user fail-fast(同区、高危、小改)。
6. 始终:一块块落地跑到 `typecheck + test + lint` 全绿,别回头堆方案。

## 6. 读什么(按顺序,不要递归全量 docs)

1. 本文
2. **`docs/kokoro-handbook/technical/20-kokoro-v1-technical-plan.md`(2026-07-10 定稿,V1 唯一事实源,取代 19)**
3. `docs/lesson.md`(元教训)
4. `docs/CODEBASE_MAP.md`
5. `19` / 前序 polish handoff 只作历史附录,冲突以 20 为准

## 7. 后记(2026-07-10)

本文 §3-§5 提出的开放问题已在 `20` 全部定案:binding=ledger request、skill=沙盒挂载+find_skill、
MCP=names+agent 侧配置、deliver=hash 键冻结。第二块落地也已完成:fail-closed auth
(`resolveAuthMode`,新增 4 测试,全量 195 绿)。落地顺序见 `20` §5。
