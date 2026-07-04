# kokoro-agent 深度体检报告（2026-07-04，自主时段产出）

> 命题（用户）：模块是否可插拔（如 sandbox）、context 构造是否透彻、用户传递 skills 的动态性、
> 以及从整条链路出发的其他问题。本报告全部结论有实证（探针/测试/真栈），非纸面推演。

## 0. 先回答悬着的问题：memory 为什么是"工具"，CC 有吗

**CC 没有 save_memory 工具**——CC 的记忆是文件型：harness 把记忆目录说明注入 system prompt，
模型用通用 Write/Edit 写记忆文件。deepagents 原生 memory 同型（AGENTS.md + edit_file）。

我们不走文件型、走 store+工具型（langmem 模式），是架构处境不同，不是偏好：

| | CC（本机单用户） | kokoro（服务端多租户多 pod） |
|---|---|---|
| 记忆载体 | 本机文件系统，天然持久 | sandbox 是易失虚拟 FS（state）/未来 e2b——文件型记忆随会话死 |
| 隔离 | 无需隔离 | namespace 租户墙必须结构性成立 |
| 多副本 | 单进程 | 多 pod 共享 → 需要 mongo/sqlite store |

工具型还把写记忆收窄成一个受审计的原语（比"放开宿主文件写"小得多的攻击面）。
若未来 sandbox 供给落地、记忆文件可随沙箱持久，可再评估文件型并轨——记 P2 观察项。

## 1. 模块可插拔矩阵（逐个盘）

| 模块 | 端口/工厂 | 现有实现 | 换新成本 | 判定 |
|---|---|---|---|---|
| 事件传输 | `StreamProtocol`（5 方法，cursor 不透明） | redis / memory | 新实现类+工厂分支 | ✅ 干净端口 |
| run 状态 | `RunStateStore` Protocol | sqlite / mongo / fake | 同上，行为矩阵 23 项复用 | ✅ |
| checkpoint | langgraph `BaseCheckpointSaver` 工厂 | memory / sqlite / mongo | 官方 saver 即插 | ✅ 借框架端口 |
| 记忆 store | langgraph `BaseStore` 工厂（随 checkpoint 对齐） | InMemory / sqlite / 官方 mongo | 官方 store 即插 | ✅ |
| **sandbox** | `make_backend(kind, settings)` 闭集工厂 | state / local_shell；e2b/custom fail-loud | 加分支+Settings 字段 | ⚠️ 可插但闭集——**e2b 是下一个真实现**，届时应引入 `(namespace, session_id)` 键的实例池；不预先抽象（YAGNI） |
| 模型 | `make_chat_model` 工厂 | openai / anthropic / deepseek 包装 / local fake | 契约 provider 枚举+分支 | ✅ 枚举收口是故意的（wire 词汇） |
| search provider | `SearchProvider` 协议+注册表 | tavily / searxng / zhipu | 注册表加类 | ✅ 用户裁定后的形态 |
| skills | lock 校验+全文注入（backend 无关） | 文件挂载 | 沙箱供给后回归渐进披露 | ✅ 有升级路径注记 |
| subagents | catalog（内建空）+ wire 预设 | namespace 预设 | profile 加条目 | ✅ |
| 可观测 | `trace_config`（langfuse 专用） | langfuse v3 自托管 | 换厂=改此文件 | ⚠️ 未端口化——只有一家真实现，不为单场景开抽象；OTel 化记 P2 |
| HITL/审核 | interrupt_on + 两个通用 middleware | — | — | ✅ 机制通用 |

结论：**除 sandbox（等 e2b）与可观测（单实现不抽象）外，全部达到"换实现不动业务层"。**

## 2. context 构造审计（发现两处真问题，已当场处置）

**RunContext（图运行时注入）最小集是对的**：namespace/session_id/run_id/thread_id——
不可变身份，不进 checkpoint，工具/middleware 经 `get_runtime` 读。身份混进 state 才是反模式。

**实锤①（已修，41d3773）**：wire `SubagentDef.tools/model` 被 agent 静默丢弃——namespace 给预设
声明工具/模型会无声失效（最坏失效方式）。已改为：tools 按名解析为已挂载实例（未知名 fail-loud）、
model 经工厂实例化，缺省继承主 agent。回归测试钉死。

**实锤②（待清理，下一单）**：契约 `RuntimeContext` 的 `user_id/site_id/workspace_id/project_id/
recent_messages/summary` 六字段**全链无人产、无人读**（session 不填、agent 不消费）——投机字段。
会话连续性由 thread checkpoint 承担，`recent_messages/summary` 属误设计；四个组织字段等真实
auth/平台接入时再进契约。按"拒绝投机"应从契约移除（四仓机械重生成）。
`user_id` 的真实需求（记忆按人细分）到来时：store 前缀元组加一层即可，工具零改动。

## 3. 动态 skills（用户问：如果用户传递的 skills 是动态的）

分层答案：**agent 侧已经是动态的**——skills 是 per-run `RuntimeConfig.skills`（每次 build 重新
lock 校验+渲染），今天换内容换 lock 下一 run 即生效。**静态的是产品面**：目前唯一来源是
namespace profile（租户级常挂）。要"用户级/消息级动态"缺的是 session 入口，路径已清晰：

- P1a：entry 预设加 `skills` 字段（不同专业入口挂不同技能包）——resolve 合并即可；
- P1b：POST messages 加 `skills` 选择子（按名引用 namespace 已注册技能，不许任意路径——
  lock 与路径必须仍由管理面声明，用户只做选择，否则技能注入=提示注入攻击面）；
- 安全底线：动态性只开放"选择"，不开放"定义"。

## 4. 本时段抓到并修掉的问题（全部有验证产物）

1. **暂停 run 永久卡死**（严重可用性缺陷）：认领 worker 崩溃后无人监听其 control 流，
   用户 resume 石沉大海。修：心跳周期收养暂停 run 的 control 监听（consumer group 天然去重）。
   证：单测 + `scripts/chaos-verify.py` 6/6（SIGKILL A → B 收养 → resume 续走到终态）。
2. **wire 子代理 tools/model 静默丢弃**：见 §2 实锤①。
3. **失控无熔断**：无限工具循环会烧钱到天荒地老。修：`KOKORO_RECURSION_LIMIT`（默认 100）
   → GraphRecursionError → run.failed fail-loud。证：循环模型行为测试。
4. **sandbox 后端不可选**：session resolve 写死 state。修：`profile.backend`（state|local_shell）。
   证：real-model-verify 全程 local_shell + 场景 E（execute 审批 → 真 shell 输出回流，23/23）。

## 5a. agent 本体"还没做"的能力账本（2026-07-04 下午复盘补充）

逐项与 CC/生产级 agent runtime 对照后的诚实清单（已实证核对，非猜测）：

| 能力 | 现状 | 判定 |
|---|---|---|
| 流式工具输出 | **✅ 已做**（tool.output.delta，预算截停防刷屏；web 渲染留 canvas 期） | agent a7a59f6 |
| 运行中追加消息（steering） | 活跃 run 撞 409（V1 故意）；CC 支持 mid-run 注入 | P1 产品决策 —— langgraph 侧可用 interrupt+resume 注入实现 |
| 多模态输入（图片附件） | 契约已减法移除（无产无消）；模型面 glm-5V/claude 可接 | 真需求出现时：契约+session 上传面+HumanMessage content blocks，一次做完 |
| 结构化输出（response_format） | create_deep_agent 原生支持，未暴露到 wire | P2 —— music/platform job 链的前置件 |
| worker 优雅停机（SIGTERM drain） | 现靠 TTL 租约重拾兜底（已混沌验证），rollout 会有 ≤TTL 延迟尖峰 | P2 —— 停止消费+限时等活跃 run |
| MCP 工具表缓存 | 每 run 全量 HTTP 拉取 | P2 —— TTL 缓存（注意工具漂移语义） |
| 子代理 thinking 事件 | **✅ 已做**（subagent.thinking.delta 全链） | agent 2a964a3 |
| 模型瞬态重试 | **非缺口**：openai/anthropic SDK 默认 2 次重试已生效 | 已核对 |
| 长会话上下文摘要 | **非缺口**：deepagents 主/子代理路径均默认挂 summarization middleware | 已核对 |
| attachments/content_ref 静默丢弃 | **已处置**：契约减法（无产无消） | 3c83d16 |

## 5. 下一段需求清单（按优先级，等你拍板顺序）

1. **契约减法**：移除 §2 六个死字段（机械，半小时级）。
2. **e2b sandbox**：`make_backend` 加真实现 + `(namespace, session_id)` 实例池 + skill 文件
   随沙箱供给（顺带回归 deepagents 渐进披露）。等部署环境。
3. **动态 skills 产品面**：entry.skills + 消息级选择子（§3 路径）。
4. **定时任务**：session 侧触发器 + 首个前置改参 normalizer 用例（按用户时区改参）。
5. **多用户**：auth → user_id 真消费（记忆前缀细分、owner 校验）。
6. **swarm 对等交接**（P2，用户已后置）；**可观测 OTel 化**（P2）。

## 验证汇总（本时段）

agent 293 pytest + pyright 0 + ruff；storage 行为矩阵 23（sqlite+mongo）；跨栈 e2e ×3 轮 PASS；
real-model-verify 23/23（新增 execute/local_shell）；chaos-verify 6/6（新增）；全部已推送。

## 状态追记（2026-07-04 自主时段二）

- ✅ token 预算熔断（store 背书跨 HITL 段；KOKORO_RUN_TOKEN_BUDGET，默认关闭=政策不擅代）——agent 861bb08
- ✅ web-researcher 真内建（用户裁定：实现但默认关；KOKORO_BUILTIN_SUBAGENTS 点名启用 + 工具缺任一整个不挂）——agent 0361710
- ✅ system prompt 行为工程（人格+按挂载工具的条件指引+skills 三段组合；真模型实证：未提工具名即自发 save_memory 且 key 规范）——agent b9185d7
- 剩余 P1/P2：steering 机制预研、response_format、存储保留策略、MCP 缓存、e2b（外部）。
