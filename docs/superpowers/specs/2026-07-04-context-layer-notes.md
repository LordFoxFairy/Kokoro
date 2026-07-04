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
