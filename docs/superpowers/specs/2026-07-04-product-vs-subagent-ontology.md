# 成品与子代理二元论 + 能力束流动（2026-07-04 定稿）

用户命题：想清楚"内部 subagent 与顶层 agent 的区别、意义、定义、设计"，以及
"music 这类成品有自己的 tools，需要配置组装"。本文是推导后的法典与落地手册。

---

## 一、本体论：两种 agent，四个维度的对立

| 维度 | 顶层成品（product / entry） | 内部子代理（subagent / worker） |
|---|---|---|
| **面向谁** | 用户——"你在和谁说话"，会话的主人格 | 主 agent——"主 agent 雇的临时工" |
| **语境** | 完整会话语境：checkpoint 历史、长期记忆、HITL、steering 插话 | 无会话语境：一次 task 进出，不见历史、不继承 scope、结果以 ToolMessage 回归 |
| **生命周期** | session 级；用户可切换（人格更换+历史保留） | 单次 task 调用 |
| **身份来源** | session 入口表（数据）＋ agent 仓代码型成品（general 现在） | 内置 catalog（web-researcher）/ 配置自定义 / wire 预设 / runtime-custom |

形状相似（name/description/prompt/tools）是合并的诱惑，语义四重对立是分开的理由。
CC 同构：主 agent ≠ Task subagent types。

## 二、对偶性定律（核心洞见）

**同一个成品，被选中时是主 agent；别人被选中时，降格为该会话的可委派子代理。**

session `resolveRuntime` 已实现此投影：选中 music → music 主位；选中 general →
music 出现在 `runtime.subagents`（toSubagent 携带其 tools/model/persona）。

由此推出两条设计定律：

1. **成品定义必须声明式**（数据），因为它要能投影成两种运行形态——主位配方入参 /
   SubAgent 定义。代码型配方只在主位生效；降格态只带声明束（+守卫下发）。
2. **降格态的工具解析不受主工具面约束**（2026-07-04 已修实锤断裂）：
   `wire_subagents` 主 index 优先（复用政策实例）→ 注册表兜底（成品专属纯原语）→
   仍未知 fail-loud。修复前 general 主位挂 music 子代理必炸。

## 三、成品的三元结构与各自的家

| 构成 | 是什么 | 家 |
|---|---|---|
| **人格资产** | persona 文本 | `agent 仓 prompts/<type>.md`（prompt 文本进 .py 即红灯） |
| **能力束声明（bundle）** | tools 名集 / skills / model 偏好 / 描述 | **session 入口表（EntrySpec）就是 bundle 的形状**——入口是数据；将来归 hub 管理 |
| **配方（代码）** | 超出通用装配管线的专属编排 | `agent 仓 orchestration/<type>.py`（仅当需要时存在） |

**"配置组装"机制的真相：链路早已存在**——
`EntrySpec(bundle) → resolveRuntime → RuntimeConfig 上 wire → resolve_tools 按名解析
（KOKORO_TOOLS 注册表）→ 配方装配`。music 需要的不是新机制，是在链路各挂点上就位。

工具的三类解析域（registry.py 现状即法）：
- `KOKORO_TOOLS` 注册表：无政策纯原语（ask_user；**music 专属工具将来注册于此**）；
- `ASSEMBLY_TOOL_NAMES`：装配期注入政策的实例（memory 带 scope、web 带 SSRF/provider）；
- `DEEPAGENTS_BUILTIN_TOOLS`：框架自带（文件/execute/todo/task），保留名不可占用。

## 四、music 全链路落地手册（两条路，步骤到文件）

**路 A：数据型 music（人格+工具束即可表达——首选，agent 仓近零改动）**
1. 工具实现：`tools/music_generate.py` 等（纯原语，description 携用法）→ 注册进
   `registry.KOKORO_TOOLS`；【agent 仓唯一改动】
2. 人格与束：session/hub 的 namespace profile 加
   `agents.music = {description, system_prompt, tools: ["music_generate", ...], model?}`；
3. 完成。选中 music=主位成品；未选中=general 的可委派子代理（对偶性自动成立）。

**路 B：代码型 music（需要专属编排——届时纯增量）**
1. 路 A 全部 + `prompts/music.md`（人格资产随仓）；
2. `orchestration/music.py`：music 配方（专属 middleware/子代理拓扑/输出管线）；
3. 契约加配方分派键（spec 单源加字段，如 `runtime.recipe`），worker 按键选配方；
4. 降格态不变：对偶性只投影声明束，专属编排不进子代理位。

## 五、被深挖出的细节与边界（诚实清单）

- **守卫在对偶两态**：主位=配方挂 guards+steering+policy；降格态=subagent_guards
  下发（Terminal/Budget/review），steering 不下发（插话是用户↔主 agent 对话）。已实现。
- **记忆在对偶两态**：降格态继承主位的 memory 工具实例（同 namespace scope 注入）——
  空间隔离语义正确；子代理无独立记忆身份，属定义（无会话语境）。
- **纯工人子代理的配置位缺口**：profile.agents 兼做入口表与降格来源；"只想当工人、
  不进入口选择器"的预设没有独立字段。→ hub 数据模型批次加 `profile.subagents`
  （纯工人表），resolve 时并进 runtime.subagents 而不进 listEntries。【待 hub 批次】
- **内置 catalog 的边界**：agent 仓 catalog 只放"官方通用工人"（web-researcher 这类
  与类型无关者）；类型专属工人（music-mixer）随类型走 bundle/配方，不进全局 catalog。
- **prompt 资产两用**：prompts/<type>.md 主位作 persona；若该类型也常被委派，
  同一文本即降格态 system_prompt（session bundle 引用或复制皆可，真源在 hub 化时收敛）。

## 六、防漂移法则（lessons 同步）

1. 成品三元各归其家：资产 prompts/、bundle 在 session/hub（数据）、配方 orchestration/<type>.py。
2. 对偶性检验句：**"这个成品降格为子代理时还能工作吗？"**——任何成品设计必须过此问。
3. 类型专属件不进全局域（catalog/registry 常量表除注册外零 music 词汇）；
   通用域出现类型词汇即红灯。
