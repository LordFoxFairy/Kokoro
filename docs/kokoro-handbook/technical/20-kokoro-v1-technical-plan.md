# Kokoro V1 最终技术方案（定稿）

状态：正式方案，**取代 `19` 作为 V1 事实源**；`19` 降级为扩展附录（背景、风险细节、P2 蓝图）。
日期：2026-07-10
范围：kokoro-web / kokoro-session / kokoro-agent；platform V1 零新增。

## 0. 本文与 19 的关系

`19` 是打磨过程的全记录，含多轮已被推翻的设计（registry 四层、binding store、principal 表、独立 selection 服务、stage 状态机、内容寻址 workspace）。**本文只保留经代码核实或已落地验证的最终结论**；冲突时以本文为准。

判据只有一条：每个设计要么已跑到 `typecheck + test + lint` 三绿，要么直接建立在核实过的代码事实上。纸面自洽不算数。

## 1. 一句话架构

> 沙盒文件系统是能力面，wire 上只走 names，run ledger 里的请求就是不可变绑定，交付物按内容 hash 冻结。

五层压缩成一张表：

| 层 | V1 形态 | 状态 |
|---|---|---|
| 身份 | `namespace = JWT sub`（opaque 主体 id），session 持久化 + 全链路反查；缺 secret 启动即拒 | **已落地三绿** |
| 能力 | skill = 沙盒挂载的文件包 + 内置 `find_skill`；MCP = agent 侧部署配置，wire 只传 server names | 待落地 |
| 执行 | 单 `general` agent + deepagents task 子代理 + 现有 HITL 回路 | **已跑通（e2e 门禁）** |
| 交付 | `deliver` 单工具：读字节 → sha256 → 传 `deliveries/<ns>/<hash>` → marker 事件 → session 读模型 | 待落地 |
| 编排（业务 agent） | **preset 配置包**（见 D6）：prompt（岗位 SOP .md）× 挂载集（RuntimeConfig names）× 策略（HITL/交付）。入口在 run 受理时选 preset；swarm 中途 handoff = P2 | 待落地（`entry` 机制已是雏形） |

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

- session 在受理瞬间把本 run 的 `skills`（names）与 `mcp_servers`（names）快照进 RunRequest —— 之后用户改设置不影响本 run。
- steer / HITL resume / crash recover 复用同一 request（既有行为），天然"不重解析"。
- 终态后的新消息 = 新 run = 新快照。能力变化只在 run 边界生效。
- **不建** CapabilityResolver、RunCapabilityBinding 表、binding store。

### D2 skill：沙盒挂载 + `find_skill`（杀掉 registry 四层）

代码事实：skill 已有"上传进 backend `/.skills/<name>/` 前缀"的供给机制（`skills/provision.py`）；现在的问题只是它接到了 `create_deep_agent(skills=)`，导致 skill 集变化会动 system prompt。

V1 设计：

- skill 包 = 目录（`SKILL.md` frontmatter: name/description + 辅助文件）。官方 skill 随部署提供（目录或对象存储，沿用现有 `content_source` 扫描）。
- run 装配时，把 request 里 names 对应的包挂载到 `/.skills/<name>/`；**不再传 `skills=`**，system prompt 与 tool schema 恒定。
- 新增一个内置工具：`find_skill(query)` —— 返回**本 run request names 范围内**的 skill 短卡片（name/description/入口路径）。正文用现有文件读工具按需读。
- **沙盒残留不是权限**：`find_skill` 按当前 run 的 names 过滤，不是裸扫磁盘；上一 run 挂过、本 run 未启用的包不可见。
- session 文件列示与归档排除 `/.skills/**`（不进用户 workspace 视图）。
- 内置核心 skill 恒挂；其余按启用挂载——"内置一部分、其余 find"即渐进披露。
- **不建** `skill_registry` / `principal_skill_state` 数据库。用户上传 skill、启用状态持久化 = P1.5（届时加一张最小 state 表即可，挂载机制不变）。

### D3 MCP：wire 只传 names，secret 不出 agent 侧（最小修法）

代码事实：现在 `RunRequest.runtime.mcp` 携带完整 `McpServer` 对象含明文 `headers`（`contract/spec/control.yaml`；`mcp/servers.py` 直传）——secret 进了 wire 和 request ledger，真实卫生洞。

V1 定案（最小、不建服务）：

- contract 变更：`RuntimeConfig.mcp: McpServer[]` → `mcp_servers: string[]`（names only），旧字段直接删、不做兼容层（无存量生产依赖）。
- MCP server 完整配置（transport/url/headers）移到 **agent 侧部署配置**（env/yaml，按 server name 索引）。agent 收到 names → 查本地配置 → 连接。
- secret 只存在于 agent 部署配置；RunRequest / ledger / events 全链路无明文凭据（负向测试）。
- 工具注册沿用现有 `load_mcp_tools` 动态展开——**V1 server 集是部署静态的，schema 稳定，不构成 prefix 问题**。`mcp_list/describe/call` 稳定 adapter 推迟到 P1.5（用户可选 MCP 时才需要）。
- secret-ref / gateway 服务 = P2。

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

| 入口 | 新 run？ | 能力重新快照？ |
|---|---|---|
| 无 active run 发消息 | 是 | 是（受理瞬间） |
| active run 中发消息 | 否（steer） | 否 |
| HITL approve/reject | 否（resume） | 否 |
| crash / lease recover | 否 | 否（复用 ledger request） |
| 终态后 retry / 新消息 | 是 | 是 |
| active run 中改设置 | 否 | 否；下一 run 生效，立即生效=显式 cancel 再开 |

### D6 业务 agent = preset（编排定案，取代旧 C 层设计）

旧设计（19 的 C 层 / AgentProfile / StageSpec）错在**把业务编排当成缺失的运行时层去发明**：阶段枚举是拍脑袋的瀑布流，还要新建 deepagents 没有的状态机引擎。定案推翻它：

> **业务 agent 不是层，是一份 preset：prompt（岗位 SOP）× 挂载集（能力 names）× 策略（HITL/交付规则）。流程是知识，写在文档里给模型执行；代码只强制四个状态机。**

三个轴全有代码雏形，不发明新机制：

- **prompt 轴**：`prompts/` 目录 + `PromptLibrary`；`entry`（StartMessageBody 已有字段）按名选具名 .md 并联动 skills——就是 preset 入口的胚胎，正名补全即可。**同时删掉 wire 内联 system_prompt / subagent prompt 覆盖层**（客户端供给系统提示词 = 安全洞 + 破坏前缀稳定），只留 entry 具名选择。
- **挂载轴**：`RuntimeConfig`（skills / mcp_servers / subagents names）即挂载点；preset 声明默认挂载集，用户选择在其上叠加。
- **策略轴**：`interrupt_on`（HITL 工具拦截）、review_tools、deliver 约定，per-preset 配置。

**软流程归文档，硬约束归状态机**：垂类工作流（理解 brief → 方案 → 生成候选 → 用户确认 → 定稿交付）写进该 preset 的 `agent.md` SOP + 分阶段 skill 文件，靠评测迭代；代码级强制只有四个——run 生命周期（已有）、HITL 拦截（已有）、`deliver`（D4）、计费 job 状态机（platform 侧，quote/hold/commit）。

**形态与切换**：

- preset = 一个目录（`agent.md` + 清单：挂载 names、interrupt_on、交付约定）。**新增业务 agent = 加目录，零运行时改动。**
- 进 studio = 入口选 preset（run 受理时定，前缀各自稳定）；swarm 中途对等交接 = P2 锦上添花，不是业务 agent 成立的前提。
- 旧 `namespace/profile.ts` 子系统重构并入 preset/部署配置（它本就是"实例=租户"旧世界残留）。
- **V1 只落 `general` 一个产品 preset，聚焦通用底座。**"加目录 = 加 agent"用测试 fixture preset 验证，不新增产品面 agent。后续垂类 agent = 再加一个配置包（自己的 prompt/tools/skills 按配置），入口直连使用；agent 间协作走 swarm（P2）。垂类细节（含入口形态）等启动时再写。

### D7 一致性加固（小项，有代码依据）

- **epoch fencing**：lease 只有 owner 字符串覆盖，代码注释自认裂脑双跑窗（`supervisor.py`）。写操作带单调 epoch，旧 epoch 拒写。
- `completeMessageSegment` "读全量再覆写"两步非原子 → 改单次 `$push`+`$set`。
- snapshot 1000 条静默截断 → 显式 `truncated` 失败面。
- `run.steer` contract 已有、web HTTP 未暴露 → 接通。

### D8 命名法则（wire 字段 / 工具 / 函数）

V1 无存量兼容负担，是改名的唯一零成本窗口；块2 动契约时命名一次到位，不留"以后再改"。

法则（新命名一律先过法则 0，再过五条，不逐个讨论）：

0. **先继承生态惯例，不自造**：LangChain/LangGraph/deepagents、Anthropic/OpenAI SDK、REST 有现成名字就用现成的。
1. **调用方视角**：字段说"是什么"，不泄漏实现或 UI 状态。
2. **一个概念一个词，全链路同名**：web→session→agent→文档同一个名。
3. **无装饰词**：`selected_` / `current_` / `_info` / `_data` 不携带信息即删。
4. **模型可见工具名 = 普通英语动词**（`find_skill` / `deliver`），禁 DevOps 黑话。
5. **缩写只用行业通用**（id / mcp / url），不自造。

已循规范的正面样板（核实过，别动）：`KokoroAgentState → DeepAgentState → AgentState`（框架官方继承链，deepagents 推荐扩展方式）、`thread_id`（langgraph 同名）、`run`（OpenAI Assistants 同概念）、checkpoint/store/middleware（框架词）。

定案改名（块2 执行，旧名全仓清零不留别名）：

| 现名 | 定案 | 理由 |
|---|---|---|
| `StartMessageBody` / `startMessage` | `MessageCreateParams` / `createMessage` | 法则 0：Anthropic/OpenAI SDK 对 POST messages 的同款命名 |
| `selected_model` | `model` | UI 状态词泄漏 |
| `entry` | `agent` | 就是"用哪个 agent"；内部机制名 preset 不上 wire |
| `RuntimeConfig.mcp` | `mcp_servers` | 装的是 server names |
| 新增能力字段 | `skills` / `mcp_servers` | 与 RuntimeConfig 同名，全链路不换名 |
| `provision_skills` | `mount_skills`（块3） | 贴 D2 挂载心智 |

保留的好名（不为改而改）：`idempotency_key`、`content`、`thinking`、`namespace`、`RunScope`、`RuntimeConfig`、`ensure/claim/put/get` 系、`try_claim/renew/reclaim_expired`、`find_skill`、`deliver`。

## 4. 明确砍掉的（防止复活）

| 被砍设计 | 砍它的理由 |
|---|---|
| registry 四层（skill_registry/CapabilityResolver/binding store/selection 服务） | binding=ledger request 已原子存在；skill 面=沙盒挂载；V1 无用户上传 |
| platform `principal` 表 | `sub` 即主体 id，opaque 语义已满足；team 到来时换签发不换轴 |
| 独立 artifact keyspace 之外的冻结机器（复制副本、quiesce、内容寻址 workspace） | hash-key 一条就够；其余是为不用 hash-key 打的补丁 |
| C 层 / AgentProfile / StageSpec 状态机 | 编排不是运行时层，是 preset 配置包（D6）；软流程归 SOP 文档，硬约束只四个状态机 |
| swarm 中途 handoff（V1） | 入口选 preset 已覆盖 studio 场景；langgraph-swarm 未依赖；对等交接 = P2 锦上添花 |
| wire 内联 system_prompt / subagent prompt 覆盖 | 客户端供给系统提示词 = 安全洞 + 破坏前缀稳定；只留 entry 具名选择 |
| MCP 稳定 adapter（V1） | server 集部署静态时无收益；用户可选 MCP（P1.5）时再上 |
| 用户 promote/demote 产物 | agent 唯一定稿已闭环；读模型天然可后加人工覆盖 |

## 5. 落地顺序（每块验收 = typecheck + test + lint 三绿 + 该块断言）

```text
块1  [已完成] namespace 事实源化 + fail-closed auth（195 tests 绿）
块2  contract 与命名一次到位（D3+D8）：MessageCreateParams（原 StartMessageBody，
     +skills/mcp_servers、selected_model→model、entry→agent）、
     RuntimeConfig.mcp→mcp_servers、agent 侧 MCP 配置
     断言：request ledger 无明文 headers（负向测试）；names 受理快照生效；
     旧字段名全仓 grep 零残留
块3  skill 挂载 + find_skill（去 skills=）
     断言：skill 集 A/B 切换 system prompt diff 为空；未启用包 find 不可见
块4  preset 化：profile 子系统重构为 preset/部署配置、entry 正名选 preset、
     删 wire 内联 prompt/subagent 覆盖；机制用测试 fixture preset 验证
     断言：wire 注入 system_prompt 被拒（负向测试）；新增 preset = 仅加目录+配置，
     零运行时代码改动（fixture 证明）；general 与 fixture 的 system prompt 各自稳定
块5  deliver 端到端（agent 工具 → 事件 → session 读模型 → web list/download）
     断言：deliver 后改/删源文件，下载内容不变；同内容重复 deliver 同记录
块6  一致性加固（D7 四项）+ WP-2 远程沙箱（Daytona + pull 读路径）
块7  web 底座（auth/settings/capabilities 选择 UI/成果面板）
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
