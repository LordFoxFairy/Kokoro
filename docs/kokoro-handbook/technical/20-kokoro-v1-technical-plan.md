# Kokoro V1 最终技术方案（定稿）

状态：正式方案，**取代 `19` 作为 V1 事实源**；`19` 降级为扩展附录（背景、风险细节、P2 蓝图）。
日期：2026-07-10
范围：kokoro-web / kokoro-session / kokoro-agent；platform V1 零新增。

> **2026-08-22 边界更新 / 状态修正：本文是 V1 已交付事实的历史记录，不是当前 GA 演进的 Agent 事实源。**
> 它继续约束 namespace、HITL、终态、交付等已验证行为；但其中涉及会话能力快照、
> `RuntimeConfig`、preset 与 Agent 入口的 D1/D2/D3/D6 均已由
> [ADR-015](../decisions/ADR-015-agent-state-and-feature-context.md)、
> [33 Skill runtime](33-ga-first-skill-runtime-architecture.md) 和
> [34 GA Runtime](34-ga-agent-runtime-architecture.md) 取代。
>
> 尤其，本文历史段落中出现的 `session.agent`、会话 `CapabilitySnapshot`、
> Session-built `RuntimeConfig` 都**不得用于新实现**：`DeepAgentState`
> 是 DeepAgent Feature 的唯一 Agent 会话执行状态；swarm 使用 official `SwarmState.active_agent` 记录 peer handoff；Session 只保留产品 Feature 上下文，不持有 Agent、图或能力配置。

## 0. 本文与 19 的关系

`19` 是打磨过程的全记录，含多轮已被推翻的设计（registry 四层、binding store、principal 表、独立 selection 服务、stage 状态机、内容寻址 workspace）。**本文只保留经代码核实或已落地验证的最终结论**；冲突时以本文为准。

判据只有一条：每个设计要么已跑到 `typecheck + test + lint` 三绿，要么直接建立在核实过的代码事实上。纸面自洽不算数。

## 1. 一句话架构

> 沙盒文件系统是能力面，wire 上只走 names，run ledger 里的请求就是不可变绑定，交付物按内容 hash 冻结。

五层压缩成一张表：

| 层 | V1 形态 | 状态 |
|---|---|---|
| 身份 | `namespace = JWT sub`（opaque 主体 id），session 持久化 + 全链路反查；缺 secret 启动即拒 | **已落地三绿** |
| 能力 | skills/MCP：会话快照+skill 单工具+MCP 三工具+注册表(McpServerDoc) | V1 行为不变量已落地；当前 target：GA 直接读取默认 Skill，动态项经 `find_skills/load_skill` 使用 GA catalog 与 CA path；CA/Storage 只作来源辅助；technical/22 仅作历史取证。 |
| 执行 | 单 `general` agent + deepagents task 子代理 + 现有 HITL 回路 | **已跑通（e2e 门禁）** |
| 交付 | `deliver` 单工具：读字节 → sha256 → `deliveries/<ns>/<hash>` → delivery.created → session 读模型+下载端点+web 成果卡 | 已落地(E2E-31) |
| 编排（业务 agent） | **preset 配置包**（见 D6）；swarm 中途 handoff 已落地 | session 首条锁已落;agent 侧目录化 preset **已落地(AGENT-PRESET，agent f4e7b6b/web bf3973b)**;swarm handoff **已落地(SWARM-QUOTA，agent 7cfa48e)** |

## 2. 已落地的事实（三绿，不要重做）

worktree：`kokoro-session/.gitwarp/worktrees/agent/session-namespace-auth-persistence`（未 commit）。

1. **namespace 事实源化**：auth 产出 `{ownerId, namespace}`（均 = `payload.sub`）；`session.namespace` 落库（存量 `?? owner_id` backfill）；relay / snapshot / file read / RunRequest 全部 `session_id → session.namespace` 反查；`RunRecord.namespace` 冗余存储供恢复扫描校验；forbidden-prefix（`user:` 等）token 拒收；public snapshot 不暴露 namespace。
2. **fail-closed auth**：`resolveAuthMode` —— 缺 `KOKORO_AUTH_JWT_SECRET` 默认拒绝启动；单机 dev 必须显式 `KOKORO_ALLOW_INSECURE_LOCAL_AUTH=true` 才允许直通。
3. 验证：`npm run typecheck` / `npm test`（195 passed / 16 files）/ `npm run lint` 全绿。

**身份定案**：V1 不建 principal 表、session 不调 platform。`sub` 就是主体 id；未来 team 由 platform 在自己的 id 空间签发主体 id 放进 `sub`，namespace 语义不变、无数据迁移。

## 3. 核心设计（每条附代码依据）

### D1 绑定即请求（杀掉 binding store）

代码事实：agent run ledger 的 `try_claim` 是"`request_json` + lease + owner **单次原子 upsert**"（`kokoro-agent/storage/mongo.py`），resume/recover 用原 request 重建同 scope（`worker/supervisor.py`）。

结论：**持久化的 RunRequest 就是本 run 的不可变 capability binding**。

- session 在受理瞬间把 `skills` 与 `mcp_servers` 写进 RunRequest —— **来源已升级为 session 级快照**（specs：会话创建时定死,run 只是复制,不回查池）。
- steer / HITL resume / crash recover 复用同一 request（既有行为），天然"不重解析"。
- 终态后的新消息 = 新 run = 新快照。能力变化只在 run 边界生效。
- **不建** CapabilityResolver、RunCapabilityBinding 表、binding store。

### D2 skill：沙盒挂载 + `find_skill`（杀掉 registry 四层）

> **本节已被取代（2026-07-10）**：skills 现行方案见 `docs/superpowers/specs/2026-07-10-skills-design.md`（v2.1）——要点：Mongo 元数据+S3 包体的 hub、**会话级快照（卡片全量+内容锁）**、清单常驻+`skill(name)` 单工具（find_skill 已废）、hash 增量物化。本节正文保留为演进历史，**勿照此实现**；specs 认可后回灌本节。

代码事实：skill 已有"上传进 backend `/.skills/<name>/` 前缀"的供给机制（`skills/provision.py`）；现在的问题只是它接到了 `create_deep_agent(skills=)`，导致 skill 集变化会动 system prompt。

**定案（2026-07-10 二次修订：存储按多租户，行为按 Claude Code——用户明确"参考 CC，不用自己乱设计"）**：

- **存储真源 = Mongo**（多租户必然；此前"启动扫描进内存"是单机 CLI 形态的错误移植）。`skills` 集合：`{scope: official|<namespace>, name, description, files, content_hash, updated_at, deleted_at}`，(scope,name) 唯一索引；同名时 namespace 覆盖 official。**写入即生效（下一 run），不再重启**。官方包：部署目录只是 seed 输入，启动 upsert 进 Mongo（content_hash 不变则不写）。进程内 LRU 按 content_hash 缓存（内容寻址永不失效）。
- **发现 = 清单常驻（CC 本源，无检索）**：装配期按本 run names 查 Mongo 拿 name+description，组装"可用技能"段落进 system prompt——模型恒见清单，发现=阅读。**没有 find 工具、没有 query、没有向量**：不存在"想不起来查/关键词不匹配/召回差"这些问题。
- **调用 = `skill(name)` 单工具（CC 的 Skill 同款）**：校验 name ∈ 本 run 授权集 → Mongo 取包（LRU）→ SKILL.md 正文直返；含非 .md 资产的包**此刻**按需整包幂等上传沙盒 `/.skills/<name>/` 供 execute。未授权/不存在 → error 文本 fail-closed。
- **前缀（D9 增补）**：同池且内容未变 → system prompt 字节恒定；技能池/内容变更 → **下一 run 一次性换轨**（显式低频，与 swarm 移交同级的合法触发；CC 同款代价：装新技能=新前缀）。
- 授权快照（RunRequest.runtime.skills names，run 内不可变）、沙盒残留非权限、子代理同池、state 档资产降级——均保留。
- V1 范围：agent 侧真源化+seed+清单+单工具；session 池查询与用户上传接口 = 紧随的写面块（存储模型已按多用户建好）。
- 内置核心 skill 恒挂；其余按启用挂载——"内置一部分、其余 find"即渐进披露。
- **选择模式定案（池自动注入，用户不勾选）**：skill 池是**账户/部署级**管理面（新增/update/启停，settings 级低频操作），每次 run **自动快照整个可用池**挂载，agent 靠 `find_skill` 按需自取——用户从不逐消息选择。三层分离：池（可随时变，生效于下一 run）→ run 快照（不可变）→ 使用（agent 运行时判断）。渐进披露的意义就是让"不选"成为可能；让用户勾选 = 把系统的智能负担转嫁给用户。wire `skills` 字段降级为**程序化例外口**（preset 强制注入 / API 精确控制 / 测试），不做大众输入框交互；缺省（不发）= 全池，即现实现语义，代码零改动。MCP 同理：enabled servers 是账户/部署状态，非逐消息勾选。
- **不建** `skill_registry` / `principal_skill_state` 数据库。用户上传 skill、启用状态持久化 = P1.5（届时加一张最小 state 表即可，挂载机制不变）。
- **简化代价（主动标注）**：binding 的不可变是 **names 级**、非内容级——skill 库是进程级部署快照，部署更新后 crash-resume 的旧 run 按旧 names 解析到新内容。V1 以"部署=不可变单元"为界可接受（官方 skill 随部署版本走）；用户上传 skill（P1.5）落地时必须补内容锁（content_hash/read_ref），届时此简化失效。

### D3 MCP：wire 只传 names，secret 不出 agent 侧（最小修法）

代码事实：现在 `RunRequest.runtime.mcp` 携带完整 `McpServer` 对象含明文 `headers`（`contract/spec/control.yaml`；`mcp/servers.py` 直传）——secret 进了 wire 和 request ledger，真实卫生洞。

V1 定案（最小、不建服务）：

- contract 变更：`RuntimeConfig.mcp: McpServer[]` → `mcp_servers: string[]`（names only），旧字段直接删、不做兼容层（无存量生产依赖）。
- MCP server 完整配置（transport/url/headers）移到 **agent 侧部署配置**（env/yaml，按 server name 索引）。agent 收到 names → 查本地配置 → 连接。
- secret 只存在于 agent 部署配置；RunRequest / ledger / events 全链路无明文凭据（负向测试）。
- **工具面定案（2026-07-10 修正，用户指出前缀缓存问题后）**：动态注册（`load_mcp_tools` 展开进工具列表）**V1 即删除**，换稳定 adapter `mcp_list_tools / mcp_describe_tool / mcp_call` 三个恒定工具（与 `find_skill` 同构）。原因：tools 块位于 API 前缀最前，动态注册下**远端 server 的 schema/顺序漂移（不受我们控制）会打穿同会话全部缓存**——历史越长损失越大，等效每次新会话。server/tool/schema 全部降为工具返回的数据：数据变不动前缀。此前"标注为已知不一致、P1.5 再修"是低估，不留账。
- secret-ref / gateway 服务 = P2。

**与 skill 池模型的同构与差异（定案）**：MCP 同样走"池自动注入、不逐消息勾选"，但池的性质不同——skill 是静态文本（躺着零成本、可海量），MCP 是**活的外部连接**（有凭据、有副作用、天然少量）。因此：

- 入池动词不同：skill = "添加/启停"；MCP = **"连接/断开"**（显式授权动作，ChatGPT connectors 同款心智）。连接后自动可用。
- 故障语义分裂：未知 server 名 = 配置错误 fail-loud（已实现）；**server 运行时不可达 = 外部常态**，P1.5 起降级为"该 server 本次不可用 + 显式事件"，不杀整个 run（V1 现状全 fail-closed，部署静态+个位数 server 可承受，已知脆点）。
- 终态统一：skill 用 `find_skill`+文件读、MCP 用 `mcp_list/describe/call`——都是"恒定小工具面 + 惰性发现"，池再大 prompt 不膨胀。V1 动态注册是池小时期的过渡。

### D4 deliver：hash 键冻结（一次 hash、一次上传、零额外机器）

需求（用户定案）：纯 agent 驱动、单工具、产出即固化不可变。

代码事实：归档是 session 级 path-key 覆盖写（`{namespace}:{session_id}/{path}`），无 run 边界、全仓无任何 hash —— 所以"复用归档快照"不成立（已证伪），"复制到只读目录"在 S3 上也没有只读语义。

定案：**只对交付物做内容寻址**（不动 workspace）：

```text
deliver(path, title, note?)                     # agent 可见的唯一交付工具
  1. 经 backend 读文件字节（本地/docker 已有读路径）
  2. sha256(字节) = content_hash
  3. 上传 deliveries/<namespace>/<content_hash>  # 同内容同 key=幂等；异内容异 key=永不覆盖
  4. 发 delivery.created 事件：{run_id, path, title, mime, size, content_hash}
```

- 不可变性由 key 构造保证；**不需要 quiesce**——工具读到哪份字节就 hash/上传哪份字节，记录与冻结内容构造上一致；agent 在自认为写完时调用，语义自洽。
- session 投影读模型：按 `(namespace, content_hash)` upsert，`session_id/run_id/path/title` 为元数据——天然支持未来"作品统一归库"（用户级），V1 先给 session 级 list + download（session 代理从 deliveries key 取回）。
- 存储沿用 workspace 的 ADR-009 配置模式：s3 / 本地目录双实现，dev 无 S3 也能跑。
- V1 单文件；多文件产物先 zip 再 deliver。用户 promote/demote 不做，agent 是唯一定稿者。
- 远程沙箱（E2B/Daytona）的 pull 读路径是 WP-2 依赖；V1 dev 用 local/docker backend 即闭环。

### D5 动态性（一张表说完）

> **口径升级（2026-07-10 specs）**：能力快照从 run 级上收为 **session 级**（会话创建定死,含内容锁）——表中"新 run 重新快照"应读作"从 session 快照复制"；池演进只作用于新会话/fork。

| 入口 | 新 run？ | 能力重新快照？ |
|---|---|---|
| 无 active run 发消息 | 是 | 是（受理瞬间） |
| active run 中发消息 | 否（steer） | 否 |
| HITL approve/reject | 否（resume） | 否 |
| crash / lease recover | 否 | 否（复用 ledger request） |
| 终态后 retry / 新消息 | 是 | 是 |
| active run 中改设置 | 否 | 否；下一 run 生效，立即生效=显式 cancel 再开 |

### D6 业务 agent：历史 V1 方案（已由 ADR-015 / 34 取代）

> **不要按本节实施。**它记录了当时把 `session.agent` 当作场景锁的 V1 做法；这会与
> 当前 Feature 的 native outer state（DeepAgent 时 `DeepAgentState`，swarm 时 official `SwarmState.active_agent`）形成两份 Agent 状态。当前设计以 `feature_key -> Feature`
> 完成首次 bootstrap，以 checkpoint 的 `active_agent` 完成后续续聊与 swarm handoff；详见
> [34 GA Runtime](34-ga-agent-runtime-architecture.md) §1–§4。

旧设计（19 的 C 层 / AgentProfile / StageSpec）错在**把业务编排当成缺失的运行时层去发明**：阶段枚举是拍脑袋的瀑布流，还要新建 deepagents 没有的状态机引擎。定案推翻它：

> **业务 agent 不是层，是一份 preset：prompt（岗位 SOP）× 挂载集（能力 names）× 策略（HITL/交付规则）。流程是知识，写在文档里给模型执行；代码只强制四个状态机。**

三个轴全有代码雏形，不发明新机制：

- **prompt 轴**：`prompts/` 目录 + `PromptLibrary`；`entry`（StartMessageBody 已有字段）按名选具名 .md 并联动 skills——就是 preset 入口的胚胎，正名补全即可。**同时删掉 wire 内联 system_prompt / subagent prompt 覆盖层**（客户端供给系统提示词 = 安全洞 + 破坏前缀稳定），只留 entry 具名选择。
- **挂载轴**：`RuntimeConfig`（skills / mcp_servers / subagents names）即挂载点；preset 声明默认挂载集，用户选择在其上叠加。
- **策略轴**：`interrupt_on`（HITL 工具拦截）、review_tools、deliver 约定，per-preset 配置。

**软流程归文档，硬约束归状态机**：垂类工作流（理解 brief → 方案 → 生成候选 → 用户确认 → 定稿交付）写进该 preset 的 `agent.md` SOP + 分阶段 skill 文件，靠评测迭代；代码级强制只有四个——run 生命周期（已有）、HITL 拦截（已有）、`deliver`（D4）、计费 job 状态机（platform 侧，quote/hold/commit）。

**形态与切换**：

- preset = 一个目录（`agent.md` + 清单：挂载 names、interrupt_on、交付约定）。**新增业务 agent = 加目录，零运行时改动。**
- **切换两层模型（2026-07-10 定案：场景 + 功能）**：
  - **场景层（入口，wire 字段）**：`session.agent` 首条消息定死并持久化——进 studio 的会话生来就是该 agent 当主。后续消息带不同 agent → 400 拒绝（堵现状 wire 洞）：**字段层永不换**。
  - **功能层（会话内，swarm 机制，P2 落地）**：swarm graph 挂全部 agents（各带自己的 prompt+tools）；用户消息让当前 agent **自己判断**该不该调 handoff 工具移交主导权（模型驱动、不强制，与"该不该调 find_skill"同一种智能）；`active_agent` 落 checkpoint、共享消息历史，session/wire 不参与切换。
  - 换 agent 的合法通道有且只有这两个：开新会话（换场景）或 swarm 移交（换功能）；没有"改字段"这种第三通道。
- 旧 `namespace/profile.ts` 子系统重构并入 preset/部署配置（它本就是"实例=租户"旧世界残留）。
- **V1 只落 `general` 一个产品 preset，聚焦通用底座。**"加目录 = 加 agent"用测试 fixture preset 验证，不新增产品面 agent。后续垂类 agent = 再加一个配置包（自己的 prompt/tools/skills 按配置），入口直连使用；agent 间协作走 swarm（P2）。垂类细节（含入口形态）等启动时再写。

### D7 一致性加固（小项，有代码依据）

- **epoch fencing**：lease 只有 owner 字符串覆盖，代码注释自认裂脑双跑窗（`supervisor.py`）。写操作带单调 epoch，旧 epoch 拒写。
- `completeMessageSegment` "读全量再覆写"两步非原子 → 改单次 `$push`+`$set`。
- snapshot 1000 条静默截断 → 显式 `truncated` 失败面。
- `run.steer` contract 已有、web HTTP 未暴露 → 接通。

### D9 前缀缓存不变量（动态性设计的硬约束）

一次 API 调用的前缀 = tools schema → system prompt → 历史 messages；任何"动态"设计先过这张表：

| 前缀段 | 变化源 | 保证 |
|---|---|---|
| tools schema | registry/toolbox/skill 工具 | 恒定集合+固定合流顺序（A/B 逐字节测试钉死） |
| 〃 | MCP | 稳定 `mcp_*` 三工具（D3 定案）；server/tool/schema 是数据不是 schema |
| 〃 | task 工具的子代理枚举 | catalog/profile 均部署级；变化以部署为界 |
| system prompt | agent（配置包）名 → 静态 .md + 技能清单段（会话快照卡片渲染） | **会话内前缀字节恒定是结构保证**（能力全量随 session 创建快照+内容锁，改字段=400；池演进只作用于新会话/fork）；唯一会话内换轨 = swarm 移交（P2，显式低频一次性） |
| 历史 messages | 新消息/steer/工具结果 | **append-only**：steer 追加不插入、runtime note 请求级不落 checkpoint |
| model/thinking | 用户主动切换 | 该模型下重新积累，用户行为非设计洞 |

法则：**能力/配置的变化只允许表现为"工具返回的数据变化"或"append 的新消息"，绝不允许表现为前缀段的字节变化**（换 preset 除外）。

### D8 命名法则（wire 字段 / 工具 / 函数）

V1 无存量兼容负担，是改名的唯一零成本窗口；块2 动契约时命名一次到位，不留"以后再改"。

法则（新命名一律先过法则 0，再过五条，不逐个讨论）：

0. **先继承生态惯例，不自造**：LangChain/LangGraph/deepagents、Anthropic/OpenAI SDK、REST 有现成名字就用现成的。
1. **调用方视角**：字段说"是什么"，不泄漏实现或 UI 状态。
2. **一个概念一个词，全链路同名**：web→session→agent→文档同一个名。
3. **无装饰词**：`selected_` / `current_` / `_info` / `_data` 不携带信息即删。
4. **模型可见工具名 = 普通英语动词/生态惯例名**（`skill` / `deliver`），禁 DevOps 黑话。
5. **缩写只用行业通用**（id / mcp / url），不自造。

当前 V1 的命名证据（不作为目标目录名）：`KokoroAgentState → DeepAgentState → AgentState`、`thread_id`、`run`、checkpoint/store/middleware。目标按 Feature 使用原生 `DeepAgentState` 或官方 `SwarmState`；见 ADR-015/ADR-020。

定案改名（块2 执行，旧名全仓清零不留别名）：

| 现名 | 定案 | 理由 |
|---|---|---|
| `StartMessageBody` / `startMessage` | `MessageCreateParams` / `createMessage` | 法则 0：Anthropic/OpenAI SDK 对 POST messages 的同款命名 |
| `selected_model` | `model` | UI 状态词泄漏 |
| `entry` | `agent` | 就是"用哪个 agent"；内部机制名 preset 不上 wire |
| `RuntimeConfig.mcp` | `mcp_servers` | 装的是 server names |
| 新增能力字段 | `skills` / `mcp_servers` | 与 RuntimeConfig 同名，全链路不换名 |
| `provision_skills` | `mount_skills`（块3） | 贴 D2 挂载心智 |

保留的好名（不为改而改）：`idempotency_key`、`content`、`thinking`、`namespace`、`RunScope`、`RuntimeConfig`、`ensure/claim/put/get` 系、`try_claim/renew/reclaim_expired`、`skill`、`deliver`。

## 4. 明确砍掉的（防止复活）

| 被砍设计 | 砍它的理由 |
|---|---|
| registry 四层（skill_registry/CapabilityResolver/binding store/selection 服务） | binding=ledger request 已原子存在；skill 面=沙盒挂载；V1 无用户上传 |
| platform `principal` 表 | `sub` 即主体 id，opaque 语义已满足；team 到来时换签发不换轴 |
| 独立 artifact keyspace 之外的冻结机器（复制副本、quiesce、内容寻址 workspace） | hash-key 一条就够；其余是为不用 hash-key 打的补丁 |
| C 层 / AgentProfile / StageSpec 状态机 | 编排不是运行时层，是 preset 配置包（D6）；软流程归 SOP 文档，硬约束只四个状态机 |
| swarm 中途 handoff（V1） | 入口选 preset 已覆盖 studio 场景；langgraph-swarm 未依赖；对等交接 = P2 锦上添花 |
| wire 内联 system_prompt / subagent prompt 覆盖 | 客户端供给系统提示词 = 安全洞 + 破坏前缀稳定；只留 entry 具名选择 |
| ~~MCP 稳定 adapter 推迟~~（已撤销） | D9 前缀审计后**提前至 V1 并已完成**（见块3b）——远端漂移打穿缓存,不可休眠 |
| 用户 promote/demote 产物 | agent 唯一定稿已闭环；读模型天然可后加人工覆盖 |

## 5. 落地顺序（每块验收 = typecheck + test + lint 三绿 + 该块断言）

```text
块1  [已完成] namespace 事实源化 + fail-closed auth（195 tests 绿）
块2  [已完成] contract 与命名一次到位（D3+D8），并超额完成 wire 全面 names 化：
     MessageCreateParams（+skills/mcp_servers、model、agent）、RuntimeConfig
     （mcp_servers/subagents 全 names、删 system_prompt 内联与 swarm_members）、
     agent 侧 KOKORO_MCP_CONFIG（headers 值 ${ENV} 占位，凭据不进 yaml/wire/ledger）
     已验：agent 410 pytest+ruff+pyright / session 195+tc+lint / web 214+tc+lint 三仓三绿；
     负向测试（wire 注入 system_prompt/McpServer 对象/内联 subagent/swarm_members 全拒）；
     generate --check 14 镜像零漂移；旧名 grep 零残留。e2e-v21-gate 已同步（需 docker 环境跑）
块3  [已完成→已被 specs v2 取代] find_skill/read_skill 渐进披露（该实现后由
     skills spec v2 演进为 skill 单工具+清单常驻+Mongo/S3 hub，见 specs）（挂载=逻辑授权，去 skills=/装配期物化/
     initial_files；资产按需单包幂等供给；工具恒挂）
     已验：agent 413 pytest+ruff+pyright 三绿；断言达成——skill 池 A/B 切换工具面
     逐字节相同（prompt 本就不含 skill 信息）；未授权包 find 不可见/read fail-closed；
     纯文档包零物化；资产包整包幂等供给；state 档显式降级。e2e E2E-29 改为
     "装配期零物化"反向断言（需 docker 环境跑）
块3b [已完成] MCP 稳定工具面（D9 驱动，从 P1.5 提前）：删动态注册，换恒定
     mcp_list_tools/mcp_describe_tool/mcp_call（懒连接+run 内缓存，与 find_skill 同构）
     已验：agent 417 pytest（含 FastMCP live e2e）+ruff+pyright 三绿；断言达成——
     server 集 A/B/空 切换工具面逐字节相同；装配期零连接（run 不被挂掉的 server
     拖死）；运行时不可达降级 error 文本；未知名装配期 fail-loud
块4  [已完成] agent 配置包化：session.agent 持久化（首条定死，后续不同值 400 fail-loud，
     同 session 前缀结构保证）；profile 子系统重构为部署配置；机制用测试 fixture 验证
     断言：同 session 第二条消息换 agent 被 400 拒；新增 agent 配置包 = 仅加目录+配置，
     零运行时代码改动（fixture 证明）；general 与 fixture 的 system prompt 各自稳定
块5  [已完成] deliver 端到端（agent 工具 → 事件 → session 读模型 → web list/download）
     断言：deliver 后改/删源文件，下载内容不变；同内容重复 deliver 同记录
块6  一致性加固（D7 四项）+ WP-2 远程沙箱（Daytona + pull 读路径）
块7  web 底座（auth/settings/能力池管理面[启停/新增，非逐消息勾选]/成果面板）
```

P1.5（V1 全绿后）：用户上传 skill、启用状态表、用户可选 MCP + 稳定 `mcp_*` adapter。
P2：swarm / 业务 agent / stage、secret-ref 服务、workspace 版本化（若真需要）。

## 6. 不做清单（V1）

- 不在 agent runtime 解释 namespace 业务含义；不引入第二身份轴；不拼 `user:<id>`。
- 不把 skill 全文或 MCP schema 塞 system prompt；不因能力变化动稳定前缀。
- 不热插 active run 的能力集。
- 不把沙盒残留当权限事实源。
- 不建本文 §4 已砍的任何一项。
- 不在正式 docs/code 写外部参考路径、分支、逐字文案。
