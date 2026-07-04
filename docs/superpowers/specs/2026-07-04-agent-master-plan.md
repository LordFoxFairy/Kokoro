# kokoro-agent 总体方案 v1（PRD + 技术方案 + 拓展规划）

2026-07-04 定稿。本文是 agent 子仓库的单一总纲：产品定义、当前架构、词汇法典、能力现状、拓展路线。
与 handbook 冲突时以 handbook 裁决记录为准；本文吸收了截至今日的全部用户裁定。

---

## 一、PRD——产品定义

### 定位

kokoro-agent 是 Kokoro 平台的**执行引擎**：从 wire 接收一次 run 请求（RunRequest），
装配一个"人格 + 工具 + 技能 + 政策"的 agent，流式执行，把全过程以契约事件上 wire。
多租户（namespace 单轴）、多 pod 水平扩展、模块可插拔。它不做产品面——
会话管理、用户资产、权限归 session/platform；agent 是纯消费者与执行者。

### 用户能感知的能力（V1 已交付）

| # | 能力 | 用户视角 |
|---|---|---|
| 1 | 流式对话 | 实时看到思考过程（thinking delta）、正文增量、todo 进展 |
| 2 | 工具执行 | 文件读写、shell、web fetch/search、长期记忆、外接 MCP server（含个人凭据 headers） |
| 3 | 人在环 HITL | 危险工具审批（approve/edit/reject/respond）、agent 主动提问、工具结果人工审核；子代理内的审批同样可达 |
| 4 | 委派 | 内置子代理（web-researcher，点名启用）、配置自定义、运行时 wire 预设；委派不旁路任何守卫 |
| 5 | 技能 | 入口绑定技能包，sha256 lock 校验后全文注入人格 |
| 6 | 具名入口 | general 成品人格；同 session 切换入口=人格整体更换+历史保留（每 run 装配，零特殊机制） |
| 7 | 可靠性（无感） | worker 崩溃续跑、重复请求去重、暂停 run 收养、优雅停机、用量跨段准确 |
| 8 | 治理 | token 预算熔断、递归上限、工具白名单 fail-closed、SSRF 防护、审批集政策注入 |
| 9 | 观测 | langfuse 全链 trace、run.completed 报累计真实用量 |

### 非目标（明确不做，均有裁定记录）

- **定时任务**：走 MCP 机制（外挂 scheduler server 提供工具），不进 agent。
- **user_id 身份轴**：namespace 单轴法则——个人=personal namespace 实例，跨空间=grant。
- **swarm 编排**：P2；通用 agent 层级调度已覆盖当前需要，入口切换将来收敛为 handoff 特例。
- **hub 管理面**：技能/MCP/入口的 CRUD、上传下载、审核归 platform/session；agent 只认
  `SkillMount{name,path,lock}` 与 `McpServer`。

---

## 二、技术方案——分层与词汇法典

### 分层（数据流叙事）

```
contract/          wire 单源镜像（spec 生成，禁手改）
    │
worker/            调度域：进程入口、消费循环、租约/去重/收养、HITL resume、drain
    │                主配方以 functools.partial 注入，worker 不懂装配
    ▼
orchestration/     编排域：assemble.py（每请求主配方：工具→守卫→子代理→prompt→图）
    │              context.py（模型可见面唯一拼装点：人格+条件工具指引+skills 全文）
    ▼
execution/         执行域：build_agent（图构建）、invoke_once（单段执行）、
    │              approvals（HITL 帧代数，含嵌套帧回退）、events/publish（wire 出口）
    ▼
agents/            成品域：AgentEntry 形状（name/description/persona）+ general/ 成品

横向能力件：tools/ subagents/ skills/ mcp/ sandbox/ model/
横向基础设施：storage/ streams/ state.py config.py observability.py
```

一句话背诵：**contract 进 → worker 调度 → orchestration 拼装 → execution 执行 → agents 出人格。**

### 词汇法典（2026-07-04 命名归一后）

| 词 | 唯一含义 | 落点 |
|---|---|---|
| **state** | LangGraph 图状态（messages/todos/files/scope），跨段延续 | `state.py` → `KokoroAgentState` |
| **scope** | 一次 run 的身份四元组（namespace/session/run/thread），乘在图状态上 | `state.py` → `RunScope` |
| **ledger** | 控制面账本：去重/租约/终态认领/token 计数/用量累计/keep-first 工具结果 | `storage/ledger.py` → `RunLedger`（sqlite/mongo 双实现） |
| **context** | 上下文工程（prompt 拼装、将来 steering 注入），不是图状态 | `orchestration/context.py` |
| **entry** | 可作主 agent 的封装成品，人格为身份核心，能力束按 wire 装配 | `agents/entry.py` |

env：`KOKORO_LEDGER_BACKEND` / `KOKORO_LEDGER_DB`（旧 KOKORO_RUN_STATE_* 已废弃，无兼容层——初期不留迁移代码）。

### 设计法则汇编（均有用户裁定，违反即红灯）

1. **namespace 单轴**：空间/身份一律收敛 namespace；任何"再加一条身份轴"的冲动即红灯。
2. **政策装配注入**：工具是通用底层原语（零租户/vendor 概念）；租户 scope、审批集、预算、
   provider 选择全部在 orchestration 装配时注入。
3. **config 单点消费**：env 只在 `AppConfig.from_env` 解析一次；orchestration 只收领域设置
   （AssembleDeps），不收整个 AppConfig（有架构法测试执法）。
4. **诚实挂载**：依赖不可用就整个不挂（search 无 provider 不挂、子代理缺工具不上目录），不设空壳。
5. **wire 法则**：optional=缺席省略，null 永不上 wire；契约改动只经 spec→generate→check。
6. **守卫下发**：TerminalGuard/TokenBudget/review 逐个进每条子代理 middleware 链——不下发=委派旁路。
7. **fail-loud**：未知工具名、lock 失配、非法枚举、对齐失配一律即刻抛错，绝不静默降级。
8. **初期不留兼容层**：重命名/重构直接删旧换新，不写迁移垫片。

---

## 三、能力现状与验证马具

- **单测**：321 项（含存储 28 矩阵、供给链 37、HITL/嵌套 HITL、web 工具边界、架构法测试）。
- **静态**：pyright 0（豁免走 allowlist 测试，现 3 项）+ ruff 全绿。
- **跨栈**：e2e-v21-gate 30 项、chaos-verify 11 项双场景（worker/session 崩溃）、trace-verify 7 项。
- **真模型**：real-model-verify 23 项五场景（subagent/thinking/search/skills/execute）。
- 已知验证边界：web_search 三 provider 仅 searxng 真测（tavily 无 key、zhipu 429）；
  skills 渐进披露在 state backend 读不到宿主文件（全文注入是 V1 正解），e2b 后回归。

---

## 四、拓展规划（roadmap，按时序）

### R1 子代理执行面收口【下一单，agent 侧】

- **需求**：用户能看到子代理内的工具过程（现为黑盒，只见 task 一进一出）；
  委派面无守卫漏洞。
- **技术**：①子图工具事件转发上 wire（契约 P2 可见性项，新增 kind 走 spec 单源）；
  ②deepagents 内生 general-purpose 子代理在 allow 档可达且不带闸——收口（禁用或带闸挂载）。
- **验收**：真模型场景 A 能看到子代理工具事件；general-purpose 委派路径带 TerminalGuard/预算闸的回归测试。

### R2 交互深化：steering + context middleware 化【设计稿已备】

- **需求**：run 进行中用户可插话纠偏，而不是只能干等或 cancel。
- **技术**：steering 信箱（ledger 或 stream 载体）+ before_model 注入；context 拼装
  middleware 化与之同批（插话注入是 before_model 的第一个真实消费者）；
  须实证与 deepagents Skills/Memory middleware 的 prompt 改写层叠序。
- **验收**：e2e 新场景——运行中插话，下一模型轮可见且不破坏 checkpoint 连续性。

### R3 hub 分发（主战场 session/platform，agent 近零改动）

- **需求**：技能/MCP/入口的 platform 公共库 → namespace 库 → entry 选择（单轴三级）；
  用户上传/下载/分享（grant 跨空间）。
- **agent 侧**：唯一实事=**skills 铺文件同步器对接**——修"SkillMount.path 假设本地可读"
  的部署级缺陷（多 pod/e2b 下 path 失效）；lock 机制已就绪。
- **验收**：非本机来源技能包在 worker 侧可挂载且 lock 校验通过。

### R4 运维：storage retention【提案已备，半天量】

- 分层 TTL（checkpoint/ledger/事件流），全默认关；本地 sqlite 膨胀的解法。

### R5 外部件（等依赖就绪，不排期）

- **e2b 沙箱池**：SandboxSettings 已是可插拔位；落地时连带 skills 渐进披露回归。
- **artifact_ref 生产者**：等 canvas 消费面；content_and_artifact + after-tool 登记环节。
- **response_format 上 wire**：等 job 结构化输出需求。
- **auth/成员模型**：platform 侧 namespace 成员关系；agent 契约零改动。

### 依赖关系

R1 独立可做；R2 独立可做（R1 先行更好，事件面稳定）；R3 依赖 platform 排期；
R4 独立随时可插；R5 全部等外部件。agent 侧正确性面已闭合——R1 之后，agent 仓库
进入"能力扩建跟随产品"的节奏。
