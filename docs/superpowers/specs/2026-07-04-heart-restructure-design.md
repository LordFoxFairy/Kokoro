# 心脏重构设计：orchestration / agents / context / State 四合一（2026-07-04）

> 用户四点裁定合刀：①编排要有独立子目录；②对外封装好的 agent 成品要有独立目录；
> ③"context"一词归上下文工程层，须深度配合 deepagents；④身份承载用户偏好 State 系。
> 全部机制已实证（见"实证记录"），行为保持，wire 零改动。

## 目标结构

```
src/kokoro_agent/
├── agents/                # 【成品层】封装好的对外 agent 定义
│   └── general.py         #   通用 agent 成品：身份+人格源+能力束描述
├── orchestration/         # 【编排层】RunRequest+RuntimeConfig → InvokableAgent
│   ├── assemble.py        #   主配方（收编 worker/main.build() 全部拼装 + 三个 helper）
│   └── context.py         #   上下文构造器：模型可见面的唯一拼装点（人格+指引+skills）
├── run/state.py           # RunScope（原 RunContext 改名让词）+ KokoroAgentState（State 轴）
├── worker/                # 【调度域】只剩消费/租约/收养/drain/control 监听
└── execution/             # 【运行域】不变
```

## 裁决记录：身份从 context 轴迁 State 轴

- 实证 A：生产代码 **get_runtime/context 轴零消费者**（记忆工具=闭包 scope 注入，
  middleware=构造参数 run_id）——该轴是死重。
- 实证 B：`DeepAgentState` 子类加自定义键：随 input 透传、落 checkpoint、
  续跑不重供仍保持。机制成立。
- 决定：**删除 context_schema 轴**（build_agent/protocols/invoke_once/supervisor 的
  context 参数全清）；新增 `KokoroAgentState(DeepAgentState)`，键 `scope`（纯 dict，
  checkpoint 序列化安全），供未来工具/中间件经 `ToolRuntime.state` 取环境身份。
- 法则：**图节点不得改写 scope**（回归测试钉：resume 后 scope 不变）；子代理子图
  不继承 scope——子代理所需身份一律装配注入（既有法则，记忆工具先例）。
- 命名：值对象 `RunScope`（run/state.py）；State 家族满足于 KokoroAgentState 真继承
  DeepAgentState（用户"为何不继承 AgentState"的原始直觉正式落地）。
  RunStateStore（租约存储）名不变，域不同（storage/）。

## context 构造器（V1 纯函数，middleware 化留给 steering 单元）

- `orchestration/context.py`：`compose_system_prompt(persona, mounted_tools, skill_mounts)`
  ——收编现散装三段（persona + guidance 条件段 + skills 全文），一处真源、可单测、可 dump。
- **为什么 V1 不直接 middleware 化**（实证 ModelRequest.override 可行，但）：deepagents 自身
  的 Skills/Memory middleware 也在改写 system prompt，我们的 override 层叠顺序须专门实证，
  且静态组合无运行时需求——等 steering（首个运行时注入需求）一并做层叠实验。已记升级路径。

## agents/ 成品层

- `agents/general.py`：GENERAL_AGENT 成品（name/description/persona 源）。assemble 缺省
  人格从此取；session 的 listEntries 内建 general 概念上引用此成品（session 零改动）。
- web-researcher（内建子代理）目录归属不动（subagents/catalog），成品层只收"可作主 agent
  的入口成品"；二者受众不同（入口 vs 下属）。

## 迁移清单（行为保持）

1. run/context.py → run/state.py：RunScope（含 of()/scoped_thread_id/state_key）+
   KokoroAgentState + scope dict 转换器；旧模块物理删除（禁遗留）。
2. build_agent：删 context_schema 参数，内部恒传 state_schema=KokoroAgentState。
3. protocols/invoke_once/supervisor：context 参数链全删；request 路径 payload 增
   `"scope": scope.as_state()`；resume 不重供（checkpoint 已证保持）。
4. orchestration/assemble.py：收编 build() + build_web_tools/catalog_subagents/
   wire_subagents；worker/main 瘦身为 env→deps→serve。
5. orchestration/context.py：收编 prompt 三段拼装（guidance.py 并入或被其调用）。
6. agents/general.py 成品；SYSTEM_PROMPT 归其名下。
7. 测试迁移：test_context_injection → 新行为测试（真图内工具经 ToolRuntime.state 读 scope；
   resume 后 scope 保持）；test_assembly 导入路径随迁。

## 验收

全门禁（pytest/pyright/ruff）+ 跨栈 e2e + chaos 双场景 + 真模型五场景全绿；
worker/main.py 显著瘦身；`grep context_schema` 仓内为零。
