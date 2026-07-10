# kokoro-agent Python 实现美学约定（待审）

状态：草案；认可后并入 kokoro-agent 仓 docs 作为实现纪律
日期：2026-07-10
原则一句话：**让结构讲话——类型即文档、模式即意图，注释只讲为什么。**

## 1. 值与边界

- 值对象一律 `@dataclass(frozen=True, slots=True)`（RunScope/Toolset/AgentBundle 同族）。
- 边界数据一律 pydantic v2 严格模型（`strict/frozen/extra="forbid"`），外部输入经 `TypeAdapter` 一次洗净；嵌套模型显式 strict。
- 常量域用 `Literal` / `StrEnum`，拒绝裸字符串比较散落。

## 2. 分派与组合

- 多分支语义分派用 `match/case`（事件 kind、resume decision、backend 种类），拒绝 if/elif 链。
- 开放集合分派用 **策略表 dict**（`AGENT_FACTORIES` 既有惯例），新增项=加表项。
- 注册面用**装饰器注册表**（`@register_tool("deliver")` 式），注册即声明，杜绝手工同步清单。
- 组合优于继承：Template Method 只保留装配管线一处；其余用 Protocol 端口 + 注入。

## 3. 资源与惰性

- 生命周期资源一律 `@asynccontextmanager`（make_ledger/make_skill_store 同族），worker 顶层单点 `async with` 编排。
- 惰性派生用 `functools.cached_property`；纯函数缓存用 `lru_cache`（禁用于携带可变依赖的方法）。
- per-run 上下文捕获用**闭包工厂**（make_skill_tool/make_memory_tools 同族），不造带状态小类。

## 4. 端口与依赖方向

- 跨层依赖只经 `Protocol`（结构化满足，不强制继承）；实现不 import 消费方。
- 单实现也先立 Protocol 的唯一豁免：纯内部私有件。
- `deps` 聚合（AssembleDeps）只收领域设置，不收全局 config（单点消费法则，既有）。

## 5. 小语法糖清单（用即加分，滥用即扣分）

- `dict.fromkeys(xs)` 去重保序；`itertools.chain`/解包合流；海象 `:=` 限单行判取；
- f-string 一律；`pathlib` 一律（禁 os.path）；`Annotated` 收约束进类型；
- 解构赋值/星号解包表达"取谁弃谁"；生成器表达式优先于临时 list。

## 6. 反模式黑名单

裸 `dict[str, Any]` 过边界；函数内 import 绕环（TYPE_CHECKING 仅限纯类型）；`cast`/inline ignore（文件级 pragma 需登记 allowlist，既有测试执法）；布尔位置参数（一律关键字）；注释复述代码。
