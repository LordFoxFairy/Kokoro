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
- 检查并就绪依赖（Python: `poetry install`；TS: `pnpm install` 或 `npm install`）。
- **LSP 健全性预检：** 触发本地 LSP 工具（如 `ruff` / `pyright` / `tsc --noEmit`），确保当前工作区无存量语法与类型阻塞。
- 运行基础健全性测试（Smoke Test）确保当前主线没有损坏。
- **限制：** 同一时间只能聚焦一个未完成的细分功能，在当前功能通过“边界测试门槛”之前，不得声明完成。

### 2. 计划模式与 Superpower Skill 对接
任何非 trivial 任务（3步以上或涉及架构决策），必须先进入计划模式，且**必须严格配合以下 Superpower Skill（超级技能）动作集**执行，严禁自由发挥：
- **[Skill: Context-Scan] 扫描上下文：** 在计划前，必须通过工具阅读依赖的 exports、直接调用者和共享工具（Rule 8: Read before write）。禁止盲目猜测接口定义。
- **[Skill: Spec-Drafting] 制定确定性计划：** 将高度具象、细化到函数级的步骤写入 `tasks/todo.md`（包含可勾选条目与预期的边界条件断言），经用户确认后方可编码。
- **[Skill: Pivot-On-Failure] 失败即时熔断：** 如果执行或测试中出现非预期错误，**必须立刻停止（STOP）**。启动该 Skill 重新扫描上下文，推翻并更新 `tasks/todo.md` 计划，严禁盲目重试。
- **[Skill: Subagent-Isolation] 子智能体隔离：** 积极利用子智能体去跑调研、探索和探索性实验，保持主上下文（Main Context）干净。每个子智能体只分配单一聚焦任务。

### 3. 自我改进循环 (Self-Improvement Loop)
- 在收到用户的任何纠错、反馈后：必须立刻将该错误模式更新至 `tasks/lessons.md`。
- 为自己写出“防御性规则”以防止再次犯错。在后续任务中，先阅读 `lessons.md` 规避历史陷阱。

---

## 🐍 Python Pydantic & 📘 TypeScript Zod 核心防线与契约对齐

在进行全面优化或全托管运行（/goal）时，涉及跨语言、前后端、网络 I/O、存储层的核心数据实体流转，必须遵循以下硬核 Schema 铁律：

### 1. Python Pydantic V2 终极铁律
- **严格实例化（Strict Mode）：** 新建或优化外部不可信数据源（API/Websocket/DB）的 Pydantic 模型时，必须启用严格模式：`BaseModel(model_config={"strict": True})`。防止将乱序字符串隐式转换成基本类型。
- **防止多余数据污染（Extra Fields）：** 必须显式声明如何处理未知字段。除了松散的代理转发外，默认一律设为丢弃或抛错：`model_config={"extra": "forbid"}` 或 `"ignore"`。
- **空值安全防御：** 严禁使用 `Optional[T] = None` 去隐式吞掉本该必填的字段。必须区分 `field: T | None`（字段必填，值允许为 None）与 `field: T | None = None`（字段可选）的边界意义。
- **联动字段校验：** 涉及复杂关联业务逻辑时，必须编写 `@model_validator(mode="after")` 进行多字段交叉逻辑强断言。

### 2. TypeScript Zod 终极铁律
- **彻底防范未定义字段（Strip / Strict）：** 外部载荷进入系统前，必须通过 Zod Schema 解析。核心对象必须显式加 `.strict()`（严格抛错）或 `.strip()`（绝对过滤额外未知字段），拦截非预期属性注入。
- **严格消灭 `any` 级联污染：** Zod 校验输出结果严禁声明或赋予为 `any` 变量。必须使用 `z.infer<typeof schema>` 获取强类型推导结果。
- **空值韧性转换：** 对于可有可无的值，利用 `.nullable()` 和 `.optional()` 分开防御。凡是面对不安全输入，一律采用 `.preprocess()` 或 `.catch()` 设置确定性的兜底 fallback，严禁因为一行属性脏数据让整个进程死掉（Crash）。
- **同步/异步转化安全：** 分清 `.parse()` 与 `.parseAsync()`。在 Zod 涉及异步细化转换（如通过真实异步 DB 校验唯一性）时，必须异步执行，切忌阻塞单线程事件循环。

### 3. 双端契约与零硬编码（Contract Alignment）
- 如果系统涉及 Python 后端与 TS 前端/微服务的联调：**接口的模型定义不准双向手动维护。** 必须编写或使用脚本（如 `openapi-typescript` 或脚本生成器）直接根据 Python FastAPI/Pydantic 的 OpenAPI Schema 生成前端 Zod 规范与强类型，保持单源真理（Single Source of Truth）。

---

## 🐍 Python & 📘 TypeScript 通用编码规范

### 1. 极简至上与外科手术式修改
- **最少代码解决问题：** 拒绝任何投机性、面向未来的冗余代码。不为单一使用场景设计复杂的抽象。
- **精准修改（Surgical Changes）：** 只触碰必须修改的代码，清理你自己的战场。严禁“顺手”重构或美化邻近无关的代码、注释或格式。
- **因袭传统（Match Style）：** 严格匹配 codebase 现有的编码风格和设计模式。若认为现有惯例有害，须显式提出，严禁私自搞分支风格。
- **模型仅用于主观决策：** 仅在分类、草稿、总结、提取等需要主观判断的场景使用大模型能力；路由、重试、确定性转换等一律用 Python/TS 代码本身解决（能用代码解答的，绝不用模型）。

### 2. 运行时 LSP 守卫
- **Python 专属：** 必须保持 `pyright`（或 `mypy . --strict`）以及 `ruff check` 运行全绿、无任何 Warning。异常必须分级捕获，使用标准 `logging`（严禁直接 `print`）。异步任务强制使用 `asyncio.timeout()` 锁死最长挂起时间。
- **TypeScript 专属：** 必须保持本地 `typescript-language-server` 检查无错，或手动运行 `tsc --noEmit` 100% 通过。

---

## 🧪 双栈边界测试验证马具 (Boundary Testing Spec)

你不能仅凭“看起来通过了”来宣告胜利。必须编写具备高度抗破坏能力的测试，且覆盖以下全套边界条件：

### 1. 极端边界条件矩阵 (Boundary Test Matrix)
针对 TS 和 Python 的所有输入输出，测试用例必须显式包含：
- **Schema 崩塌测试：** 故意向 Pydantic / Zod 投喂不合法的 JSON、缺失核心必填项、注入恶意多余字段、传递非法格式字符串（如错误格式的 UUID / Email）。
- **空值与零值：** `None` / `null` / `undefined`, 空字符串 `""`, 空列表/数组 `[]`, 空字典/对象 `{}`。
- **数值边界：** `0`, `-1`, 极大数（安全整数 `Number.MAX_SAFE_INTEGER`）, 极小浮点数, 正负无穷大 `float('inf')` / `Infinity`, 以及非数字 `float('NaN')` / `NaN`。
- **集合与序列边界：** 单元素集合、重复元素集合、极大超长序列、稀疏数组。
- **时间与时区边界：** 跨时区计算（UTC 切换）、闰年（2月29日）、夏令时（DST）切换点、过去/未来极端时间戳（如 `0` 戳、2038年问题）。
- **并发与幂等：** 涉及状态变更、网络请求或数据库写入的接口，必须编写“连续调用2次/多次”的幂等性边界测试。

### 2. 测试架构规范
- **Python 测试：** 统一使用 `pytest` 作为标准测试框架。充分利用 `@pytest.mark.parametrize` 进行矩阵式边界测试。外部依赖必须使用 `pytest-mock` 进行行为模拟。
- **TypeScript 测试：** 统一使用 `vitest` 或 `jest`（根据项目现存框架匹配）。充分利用 `test.each` 或 `it.each` 传递边界矩阵。外部 API、DOM 或浏览器全局变量必须被充分 Mock（如使用 `msw` 或内置 `vi.mock`）。
- **意图验证：** 测试必须编码验证“为什么这个行为重要”（验证业务逻辑意图），而不仅仅是“它的输出是什么”。如果业务逻辑变了测试却无法失败，说明测试是无效的。

### 3. 完成门槛与彻底放行 (Definition of Done)
只有在满足以下自动化结果，且结果被明确持久化记录后，该任务状态才可切换为完成（DoD）：
- **LSP & Linter 双重全绿：** 运行对应的 LSP 工具（`pyright`/`ruff`/`tsc`）以及 Linter（`eslint`/`black`）无任何报错和警告。
- `pytest` 或 `vitest/jest` 测试用例 100% 通过（必须包含**Schema崩溃验证**和极端的边界测试）。
- 测试覆盖率（Coverage）未发生下滑，核心业务逻辑的行覆盖率和分支覆盖率必须达到 **95%** 以上。
- 自问检查：“如果是一个 Staff Engineer（首席工程师）来审查，他会批准这段代码吗？”

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