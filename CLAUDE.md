# CLAUDE.md — TS & Python 双栈 Harness Engineering 铁律规范

本文件定义的规则适用于该项目中的每一项任务。
我们的核心导向是：**拒绝表面开发速度，追求极端边界的正确性、代码的极简高内聚与跨会话的连续性。**

---

## 🔄 闭环工作流与状态管理 (Workflow & State)

### 1. 初始化与固定工作循环
每轮会话（Session）开始时，你必须按以下顺序执行初始化，严禁跳过：
- 运行 `pwd` 确认处于正确的仓库根目录（区分前后端或 Mono/Poly-repo 目录）。
- 读取 `claude-progress.md` 恢复上一次的上下文、当前状态与未完工任务。
- 读取 `tasks/todo.md` 或 `feature_list.json` 查看当前功能的定义与要求。
- 检查并就绪依赖（Python: `poetry install` 或 `uv sync`；TS: `pnpm install`）。
- **LSP 健全性预检：** 触发本地 LSP 工具（如 `ruff` / `pyright` / `tsc --noEmit`），确保当前工作区无存量语法与类型阻塞。
- 运行基础健全性测试（Smoke Test）确保当前主线没有损坏。
- **限制：** 同一时间只能聚焦一个未完成的细分功能，在当前功能通过“边界测试门槛”之前，不得声明完成。

### 2. 计划模式与 Superpower Skill 对接
任何非 trivial 任务（3步以上或涉及架构决策），必须先进入计划模式，且**必须严格配合以下 Superpower Skill（超级技能）动作集**执行，严禁自由发挥：
- **[Skill: Context-Scan] 扫描上下文：** 在计划前，必须通过工具阅读依赖的 exports、直接调用者和共享工具。禁止盲目猜测接口定义。
- **[Skill: Spec-Drafting] 制定确定性计划：** 将高度具象、细化到函数级的步骤写入 `tasks/todo.md`（包含可勾选条目与预期的边界条件断言），经用户确认后方可编码。
- **[Skill: Pivot-On-Failure] 失败即时熔断：** 如果执行或测试中出现非预期错误，**必须立刻停止（STOP）**。启动该 Skill 重新扫描上下文，推翻并更新 `tasks/todo.md` 计划，严禁盲目重试。
- **[Skill: Subagent-Isolation] 子智能体隔离：** 积极利用子智能体去跑调研、探索和探索性实验，保持主上下文（Main Context）干净。每个子智能体只分配单一聚焦任务。

### 3. 自我改进循环 (Self-Improvement Loop)
- 在收到用户的任何纠错、反馈后：必须立刻将该错误模式更新至 `tasks/lessons.md`。
- 为自己写出“防御性规则”以防止再次犯错。在后续任务中，先阅读 `lessons.md` 规避历史陷阱。

---

## 🐍 Python (Pythonic & DDD) 极致重构防线

当你受命优化、重构或在此仓库中编写 Python 代码时，必须无条件锁死以下铁律。你拥有最高改写与重写权，严禁缝补、严禁保留遗留兼容代码！

### 1. Pydantic V2 终极硬核契约
- **严格实例化（Strict Mode）：** 处理外部不可信数据源（API/Websocket/DB/JSON）时，必须启用严格模式：`BaseModel(model_config={"strict": True})`。防止乱序字符串隐式转换。
- **绝不接受多余污染：** 默认一律设为禁止未知字段：`model_config={"extra": "forbid"}`。最大可能不使用 `object`、`Any` 或原始 `dict` 兜底，流转实体必须全面 Pydantic 模型化。
- **空值安全防御：** 严禁使用 `Optional[T] = None` 隐式吞掉必填项。严格区分 `field: T | None`（字段必填，值可为 None）与 `field: T | None = None`（字段可选）的边界语义。
- **交叉校验：** 涉及复杂关联业务逻辑时，必须编写 `@model_validator(mode="after")` 进行多字段交叉逻辑强断言。

### 2. 领域驱动设计 (DDD) 与架构做减法
- **分层纯净度：** - `domain/`（领域层）：纯业务逻辑与 Pydantic 核心实体。**绝对禁止**依赖 FastAPI 框架或 SQLAlchemy/Tortoise 等 ORM 基础设施细节。
  - 上层（Domain/Application）只能依赖抽象（通过 Python `typing.Protocol` 定义的接口契约），具体实现由基础设施层注入（依赖倒置原则）。
- **极致做减法：** 拒绝任何投机性、面向未来的冗余代码。不为单一使用场景设计复杂的抽象。拒绝 Java/TS 仪式（如无意义的 Builder/Manager 镜像设计），移除复杂无用的过度设计，追求最小闭环。

### 3. 拒绝遮掩：每改完一个文件，立刻执行「自检三问」
每修改完或重构完一个 Python 文件，必须立刻调用 Bash 工具运行实证，并在心里和输出中明确对标以下三问，禁止遗留任何技术债：
- **① 真解还是遮掩？** 函数内临时导入（deferred import）、`# type: ignore`、`cast()`、`if TYPE_CHECKING:` 块、跨模块私有属性穿透（`other._x`）**一律视为技术遮掩，全面禁止**。循环依赖必须**结构性断开**（采用 leaf 导入路径、依赖注入、标准 `Protocol` 依赖倒置、或者 lazy `__getattr__` 包初始化）。
- **② 跑了实证没有？** 必须在 Bash 终端中运行并贴出真实输出：`uv run python -c "import aura"` + `uv run mypy <该文件>` + 相关测试。禁止“看起来对”或“应该没问题”。
- **③ 是最佳写法吗？** 有更优解立刻更换，最大化利用 Python 3.10+ 标准库（`contextlib`, `functools`, `enum`, `ABC`），绝不为省事留次优。

### 4. Python 单文件「完成标准」 (Definition of Done)
每个 `.py` 文件在被你宣告完成前，必须**一次性对标并满足全部**以下条目，不准分批修补：
- **导入规范：** 零 `if TYPE_CHECKING`；零函数内 deferred import（唯一例外：`try/except ImportError` 可选 SDK 守卫，且带 1 行 WHY 注释）；无循环依赖。
- **类型纯净：** 零 `# type: ignore`、零 `cast`；无 `Any`/`object` 兜底（唯有 JSON 入参/`**kwargs`/协程机制等真实边界可留，须能合理解释）。`NotRequired` vs `X|None` 按语义正确（键总在用 `|None`）。
- **封装与边界：** 零跨模块私有穿透（禁止使用 `_` 开头的私有属性/方法），对外一律通过公开访问器、抽象接口或注入解决。
- **死代码清理：** 100% 清除未被引用的函数、类、变量、参数、多余分支及无用 import。
- **极简注释：** 注释只写 WHY（为什么这么做），字数 ≤ 1 行；严禁标识符复述、历史辩解或装饰线；module docstring ≤ 1 行。
- **职责大小：** 文件 >~500 行或单类多职责（God Object）时，标记并按行为保持拆分为窄协作者。
- **行为保持与验证：** 重构过程不得改变原有的核心业务行为、不能篡改原本测试断言的真实意图。`ruff` + `mypy <文件>` + 相关测试 + `import aura` 全绿并贴出输出。

### 5. 极端边界测试验证马具 (Boundary Testing Spec)
统一使用 `pytest` 作为标准测试框架。针对重构重写后的所有输入输出，必须通过 `@pytest.mark.parametrize` 显式包含以下极端边界矩阵，压测其抗破坏能力：
- **Schema 崩溃测试：** 故意投喂非法 JSON、缺失必填项、注入恶意未知字段、传递错误格式字符串（不合法的 Email/UUID），验证 Pydantic 的拦截表现。
- **空值与零值：** `None`、空字符串 `""`、空列表 `[]`、空字典 `{}`。
- **数值边界：** `0`, `-1`, 极大数, 极小浮点数, 正负无穷大 `float('inf')` 以及 `float('NaN')`。
- **并发与幂等：** 涉及状态变更、DB 写入的接口，必须编写“连续调用2次/多次”的幂等性边界测试。
- **覆盖率底线：** 核心业务逻辑的行覆盖率和分支覆盖率必须达到 **95%** 以上，且整体覆盖率未发生下滑。
- **全仓覆盖（/goal）：** 做"全仓质量"时，枚举 `git ls-files '*.py'` 全部文件，逐个对标 rule 7 出 `PASS/ISSUES` 清单，ISSUES 修复后复验，确保无遗漏、可证明。不许"看到哪改哪"。

### 6. Pydantic 与 TypedDict 混合编排规范
- **输入与防守边界**：凡是接收外部、第三方字典数据时，允许用 `TypedDict` 声明字典结构，但**必须立刻使用 Pydantic `TypeAdapter` 进行运行时洗净**。
- **配置与元数据嵌套**：允许在 Pydantic 模型的局部复杂多变字段（如 `metadata`, `options`）中使用 `TypedDict` 以保持底层的字典原生态灵活性，同时享受 Pydantic 的下钻校验。
---

## 📘 TypeScript Zod 核心防线与契约对齐

### 1. TypeScript Zod 终极铁律
- **彻底防范未定义字段（Strip / Strict）：** 外部载荷进入系统前，必须通过 Zod Schema 解析。核心对象必须显式加 `.strict()`（严格抛错）或 `.strip()`（绝对过滤额外未知字段），拦截非预期属性注入。
- **严格消灭 `any` 级联污染：** Zod 校验输出结果严禁声明或赋予为 `any` 变量。必须使用 `z.infer<typeof schema>` 获取强类型推导结果。
- **空值韧性转换：** 对于可有可无的值，利用 `.nullable()` 和 `.optional()` 分开防御。凡是面对不安全输入，一律采用 `.preprocess()` 或 `.catch()` 设置确定性的兜底 fallback，严禁因为一行属性脏数据让整个进程死掉（Crash）。
- **同步/异步转化安全：** 分清 `.parse()` 与 `.parseAsync()`。在 Zod 涉及异步细化转换（如通过真实异步 DB 校验唯一性）时，必须异步执行，切忌阻塞单线程事件循环。

### 2. 双端契约与零硬编码（Contract Alignment）
- 如果系统涉及 Python 后端与 TS 前端/微服务的联调：**接口的模型定义不准双向手动维护。** 必须编写或使用脚本（如 `openapi-typescript` 或脚本生成器）直接根据 Python FastAPI/Pydantic 的 OpenAPI Schema 生成前端 Zod 规范与强类型，保持单源真理（Single Source of Truth）。

---

## 📐 TypeScript 通用编码规范

### 1. 精准修改与因袭传统
- **最少代码解决问题：** 拒绝任何投机性、面向未来的冗余代码。不为单一使用场景设计复杂的抽象。
- **精准修改（Surgical Changes）：** 只触碰必须修改的代码，清理你自己的战场。严禁“顺手”重构或美化邻近无关的代码、注释或格式。
- **因袭传统（Match Style）：** 严格匹配 codebase 现有的编码风格和设计模式。若认为现有惯例有害，须显式提出，严禁私自搞分支风格。
- **模型仅用于主观决策：** 仅在分类、草稿、总结、提取等需要主观判断的场景使用大模型能力；路由、重试、确定性转换等一律用 TS 代码本身解决（能用代码解答的，绝不用模型）。

### 2. TS 运行时 LSP 守卫
- **TypeScript 专属：** 必须保持本地 `typescript-language-server` 检查无错，或手动运行 `tsc --noEmit` 100% 通过。
- **TS 测试架构规范：** 统一使用 `vitest` 或 `jest`（根据项目现存框架匹配）。充分利用 `test.each` 或 `it.each` 传递边界矩阵。外部 API、DOM 或浏览器全局变量必须被充分 Mock（如使用 `msw` 或内置 `vi.mock`）。

---

## 🛑 显性失败、预算与交接门槛 (Constraints & Handoff)

### 1. 显性失败（Fail Loud）
- “已完成”是错误的，如果期间有任何步骤或 LSP 警告被隐式跳过。
- “测试通过”是错误的，如果任何一个测试被隐式 `skip`。
- 宁可暴露出不确定性并停下来提问，也绝不隐藏、妥协或粉饰太平。

### 2. Token 预算硬约束
- 单次 Task 预算：4,000 tokens。单次 Session 预算：30,000 tokens。
- 当接近预算水位线时，立刻主动进行总结、清理上下文并刷新（Fresh Start）。严禁保持沉默并超支运行。

### 3. 结束与会话交接
在会话结束或长任务需中断前，你必须：
- 更新 `claude-progress.md` 和 `tasks/todo.md`：明确记录“已完成什么”、“当前卡在什么边界条件”、“下一步需要运行哪个测试验证”。
- 确保当前工作区运行 `git status` 没有任何未跟踪的、零散的残留垃圾文件（全部纳入 `.gitignore` 或删除）。

