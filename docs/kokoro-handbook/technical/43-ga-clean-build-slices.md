# 43. GA Agent 落地切片

状态：按 42/36 实施的工程顺序，2026-08-27。

这不是另一套架构。每一切片都围绕同一条链路：

```text
Feature -> Agent(s) -> AgentFactory -> DeepAgents / official Swarm -> Run
```

## 1. 代码切片

1. **Agent 定义**：建立 `agents/general.py`、`agents/music.py`。每个文件只描述一个完整
   Agent 的 prompt、固定工具、Skill/MCP 和 native subagent 声明。
2. **Feature 装配**：建立 `features/catalog.py`、`features/chat.py`、`features/music.py`。
   Feature 直接声明所选 Agent、entry 与 peer handoff，不引入第二个编排对象。
3. **Factory**：建立 `agent_factory.py`。单 Agent 直接调用 `create_deep_agent`；peer 组合直接
   调用 DeepAgents `create_deep_agent` + `langgraph_swarm.create_swarm`。包内不再保留同名
   `factory/`：构造顺序留在 `agent_factory.py`，共享服务归 `worker/services.py`，工具与守卫归
   `tools/`，prompt 渲染归 `prompts/`，native subagent 归 `agents/subagents.py`。
4. **Run 接线**：worker 通过 `feature_key` 查 Feature，调用 Factory，执行返回的 native 对象。
   Redis、RunLedger、HITL、事件和恢复留在现有 execution/worker 边界。
5. **旁路能力**：GA default Skill、Capability/MCP/Storage client、Workbench 和聊天事实按需
   接入；不把外部 owner 的数据库或 bucket 写进 Agent。

## 2. 明确不做

- 不新增 `factory/` 或自有 compiler/runtime/framework/ports 目录和图包装。
- 不继承或包装 DeepAgents 原生 state，不实现自有 router、prompt-swap 或 handoff state。
- 不把 `deps`、namespace、thread、Agent、Skill、MCP 或 graph 配方放入外部请求。
- 不为音乐能力拆 composer/arranger/reviewer；需要后台隔离任务时使用 DeepAgents native subagent。

## 3. 验收

- `music` Feature 单独运行成功；组合 Feature 可复用同一个 Music Agent。
- peer handoff 只由 official Swarm 提供，`SwarmState` 只由官方框架维护。
- 同一 Session 的 terminal 后新 Run 可继续 native checkpoint；fork 使用新 state。
- GA chat facts 与 LangChain checkpoint 分离，Redis 丢失可从 `chat_events` replay。
- 外部 Capability/Storage/Studio 缺席时，未声明外部操作的 Feature 仍可运行。

## 4. 结构闭环

- [x] 删除包内 `factory/`，所有调用方改用各职责模块；不存在兼容 re-export。
- [x] `deepagents.create_deep_agent` 只在 `agent_factory.py` 出现。
- [x] architecture verifier 同时禁止 `factory/` 和第二个 DeepAgents 构造点。
- [x] 根仓 36/42/43、Agent 设计卡、模块卡与子仓 README/architecture/technical-plan 使用同一目录树。
