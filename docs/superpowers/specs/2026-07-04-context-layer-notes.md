# Context 层讨论纪要（2026-07-04，未实施——用户令先讨论清楚）

## 用户裁定
1. "context" 一词 = **上下文工程层**（模型每轮可见面的拼接构造），不是身份 DI。
   现 run/context.py 的 RunContext（langgraph runtime context 身份注入）撞词，实施时让位改名。
2. 该层必须**深入配合 deepagents**：优先组合原生件（MemoryMiddleware / SummarizationMiddleware /
   SkillsMiddleware / state backend / middleware 钩子 / dynamic system prompt），不自造平行拼接管线。
3. 命名方向：用户偏好 **State 系**（贴近 langchain AgentState / DeepAgentState 家族）。
   注意张力待设计时讲透：RunStateStore（租约存储）已占名；身份"不可变注入"与 state
   "可持久/可改写"是两条轴，若并轨需向用户呈现利弊后定。

## 实施前置调研清单（届时先做）
- 盘 deepagents 全部可组合面：state_schema 扩展、before_model/wrap_model_call、
  MemoryMiddleware 的 sources/backend 工厂、SkillsMiddleware 渐进披露、动态 system_prompt 支持。
- 现散装拼接点收编评估：worker/main.py build() 的 persona+guidance+skills 三段。
- 注入点预留：steering 信箱、（开放项）记忆构造期预取 vs 模型自取。

## 时机
挂 steering 单元之前（steering 需要干净注入点，顺序天然）。

## 追记（2026-07-04，用户提示：动态 skills/MCP 与前缀缓存）

同一 session 内 skills 开关 / MCP 变更是常态。当前 skills 走 system prompt 全文注入、
工具面随 MCP 变化——两者都改写 prompt 头部/工具块 → **provider 前缀缓存整段失效**，
长会话下每次切换都为全量历史重新付费。

方向（不改变 V1 正解，进化路径）：
1. **易变内容尾部化**：动态到达的 skill 内容按时间序注入消息流尾部（CC 渐进披露同构：
   skill 经工具调用加载，内容以 tool result 落在历史尾），历史前缀不动 → 缓存保住。
   steering 信箱已是同一形状（HumanMessage 尾部追加），skills 动态开启可复用该管道。
2. **稳定段前置**：system prompt 排布恒定段（persona/工具指引）在前、易变段在后，
   配合 provider 分段缓存断点（Anthropic cache_control）减少半程失效。
3. **工具面变更（MCP 增删）无解层**：工具定义属 prompt 前缀，变更必失效——
   政策上鼓励 entry 级工具集稳定，MCP 中途挂载为显式用户动作（成本可解释）。
