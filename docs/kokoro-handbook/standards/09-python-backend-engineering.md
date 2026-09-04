# Python 后端成熟工程规范

状态：正式规范，2026-09-04。

适用范围：Kokoro Python Agent、worker、HTTP/RPC 服务、异步执行与 provider integration。本文采用 Python
生态原生实践，不复制 TypeScript/Java 文件树，也不以教科书 DDD 目录代替真实边界。

阅读路径：1–5 节看工具链、package 与命名；6–10 节查类型和 I/O；11–16 节用于时间、测试、依赖与重构评审。

## 1. 核心决策

Kokoro Python 后端采用：

```text
PyPA src layout
+ 业务能力包直接位于应用 package
+ 普通 module/service/repository/schema 命名
+ Pydantic 负责不可信边界
+ dataclass/普通 class 负责内部数据与行为
+ typing.Protocol 只表达确有价值的最小依赖
+ psycopg 3 + database/schema.sql
+ 显式 async、资源生命周期、取消和恢复
```

明确不采用：

```text
额外的 modules/ 包装层
全仓 domain/application/infrastructure/interfaces 四层
ports/、adapters/、postgres/、redis/ 作为默认业务目录
一函数一文件或一 class 一文件
全局 services/、repositories/、models/ 垃圾桶
BaseRepository、service locator、import-time client singleton
TypedDict/cast 冒充运行时校验
```

Python 的 package 本身已经提供命名空间；`typing.Protocol` 是语言特性，不对应一个 `ports/` 文件夹。

## 2. 技术基线

| 能力             | Kokoro 默认                    | 落地规则                                               |
| ---------------- | ------------------------------ | ------------------------------------------------------ |
| Runtime          | 仓库声明的受支持 Python minor  | `.python-version`、CI、镜像一致并跟进安全 patch        |
| Package manager  | uv 稳定版                      | `pyproject.toml` + 单一 `uv.lock`，CI 使用 frozen sync |
| Format/lint      | Ruff                           | `ruff format --check` 与 `ruff check` 都是门禁         |
| Type checker     | Pyright strict                 | 一个主检查器；不并行维护互相冲突的 mypy 规则           |
| Boundary model   | Pydantic v2                    | HTTP/RPC JSON、provider payload 和序列化边界           |
| Settings         | pydantic-settings              | 唯一配置入口，启动时校验                               |
| Internal value   | dataclass                      | 默认 `frozen=True, slots=True, kw_only=True`           |
| Dependency shape | `typing.Protocol` / `Callable` | 由消费方定义，只有测试/替换/隔离有价值时创建           |
| Database         | PostgreSQL + psycopg 3         | SQL-first、显式 transaction、typed row mapping         |
| HTTP client      | HTTPX                          | 共享 client、timeout、limits、cancellation、错误归一   |
| Redis            | redis-py                       | 缓存/lease/stream；不成为持久事实源                    |
| Test             | pytest                         | unit/integration/contract/architecture/smoke 分层      |

SQLAlchemy 2 是成熟 ORM，但不是 Agent 的默认依赖。只有整个业务能力从 identity map、unit of work 和关系映射
明显获益时，才经项目级 ADR 同步修订手册与门禁后引入；子仓不单方面更改 SQL-first 基线，同一写路径不维护两套实现。

### 2.1 版本、构建和检查配置

每次进入子仓重构前核验 Python 官方支持周期、uv、Ruff、Pyright、Pydantic、psycopg 和框架兼容矩阵；
精确版本写入锁文件与本仓工具链配置，并记录核验日期，不在通用手册固定所有 SDK patch。
应用仓 `requires-python`、`.python-version`、Pyright、Ruff、CI 和镜像必须一致。以下片段以 **Python 3.14** 为例，
实际仓库先验证框架支持，未通过时记录受支持版本及升级条件，而不是关闭检查。

```toml
[tool.pyright]
include = ["src", "tests"]
pythonVersion = "3.14"
typeCheckingMode = "strict"

[tool.ruff]
target-version = "py314"
line-length = 100

[tool.ruff.lint]
select = ["E4", "E7", "E9", "F", "I", "UP", "B", "ASYNC"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "--import-mode=importlib --strict-config --strict-markers"
markers = [
  "integration: requires real external dependencies",
  "contract: verifies wire contracts",
  "smoke: verifies installed entrypoints",
]
```

- `uv lock --check` 检查 manifest 与 lock 一致；`uv sync --frozen` 使用已固定 lock，不能单独证明 lock 仍匹配 manifest。
- 工具依赖归入 dev/test dependency groups；CI 使用显式 group/extra，不靠开发者机器的隐式全局包。
- 包发布/部署执行 `uv build`，再在隔离环境安装 wheel 并 smoke；不通过 `sys.path` 补丁掩盖 src-layout 打包遗漏。
- 新工具版本验证 release notes、依赖树和真实检查命令；构建工具、镜像与 Actions 同样固定版本/digest/SHA。

## 3. 仓库级目录

### 3.1 Agent/worker 默认结构

```text
pyproject.toml
uv.lock
database/
  schema.sql
src/
  kokoro_agent/
    __init__.py
    settings.py                  # Pydantic Settings 唯一入口
    bootstrap.py                 # composition root 与资源生命周期
    worker.py                    # worker 进程薄入口
    cli.py                       # CLI 薄入口

    runs/                        # Run、checkpoint、lease、恢复
    execution/                   # Agent 执行引擎
    approvals/                   # HITL/interrupt/resume 业务能力
    agents/                      # Agent 定义与组装
    tools/                       # 工具发现、调用与权限边界
    skills/                      # Skill runtime
    mcp/                         # MCP runtime
    sandbox/                     # sandbox 生命周期
    artifacts/                   # Storage client 与 artifact 映射

    protocol/                    # 仅本仓拥有的稳定跨进程 envelope
    generated/                   # 有生成物时创建，只读
tests/
  unit/
  integration/
  contract/
  architecture/
  smoke/
  fixtures/
  doubles/
```

上树是 Agent 能力地图，不是通用 Python 服务必建树；新服务只创建实际拥有的 package 和入口。

规则：

- 不增加 `src/kokoro_agent/modules/`；`kokoro_agent` 已是应用 namespace。
- 不用宽泛 `capabilities/` 把 skills、MCP、tools、artifacts 混在一起；这些是不同生命周期。
- 一个 Settings、Pool、Cache 或 telemetry 文件足够时，使用 `settings.py`、`database.py`、`cache.py`、
  `telemetry.py`；只有同类代码真的增长后才展开同名 package。
- `bootstrap.py` 只创建资源并装配业务对象，不包含 Run 状态机、权限或 SQL。
- `protocol/` 只保存稳定跨进程消息；模块自己的 event 优先放回模块。

### 3.2 多进程入口

同仓确实存在 HTTP、worker、CLI 等多个进程时：

```text
src/kokoro_agent/
  entrypoints/
    http.py
    worker.py
    cli.py
  runtime/
    create_runtime.py
    close_runtime.py
  runs/
  execution/
  approvals/
  ...
```

单一 worker 不预建 `entrypoints/` 和 `runtime/` 两层。入口只处理参数、signal、资源创建/关闭和退出码。

## 4. 业务包的成熟形态

### 4.1 小型能力：Python 允许聚合

```text
runs/
  __init__.py
  models.py                     # dataclass、Enum、业务结果
  schemas.py                    # Pydantic 边界模型；有外部边界时创建
  service.py                    # 高度内聚的 create/get/cancel 操作
  repository.py                 # 当前唯一 psycopg 数据访问；需要持久化时创建
  events.py                     # 该能力拥有的 event；需要时创建
```

`service.py` 在 `runs/` 上下文中是清晰的；问题是根级 `src/services/`，不是所有名为 `service.py` 的模块。
简单 CRUD/状态读取不机械拆成 `create_run.py`、`get_run.py`、`list_run.py` 四个十几行文件。

### 4.2 能力增长：优先按子业务聚合

```text
runs/
  __init__.py
  models.py
  service.py
  repository.py
  recovery/
    __init__.py
    service.py
    repository.py
    schemas.py
```

先寻找共同变化的子能力，不把 `services/repositories/schemas` 当成每包默认三层。只有多个同类对象确实共享职责和生命周期，
才使用复数集合 package；不要新建只放一个文件的目录。所有手写 package 使用 `__init__.py`，有意使用 namespace package 需说明理由。
本手册统一仓根 `tests/`，不再同时推广 package 内另一套 tests 目录。

### 4.3 Agent 执行链路

```text
execution/
  engine.py
  dispatch.py
  run_loop.py
  recovery.py
  checkpoints.py
  leases.py
```

LangGraph/DeepAgents 可以是 execution engine 的实现框架；真正的边界是：其 State/Graph/SDK 类型不能泄漏到
Run 持久事实、公开 protocol、数据库 Row 或其他业务包。不要为了叫“adapter”把核心运行时拆到难以理解的远端目录。

### 4.4 按职责而不是技术品牌命名

当业务使用 Redis 时：

```text
runs/checkpoint_cache.py
execution/lease.py
execution/event_stream.py
```

而不是：

```text
runs/redis/
execution/redis/
infrastructure/redis/
```

当业务使用 PostgreSQL 时，SQL 默认在 `repository.py` 或 `repositories/`；不因数据库已确定而重复建立
`postgres/`。只有同一职责确实存在多个数据库实现，或 PostgreSQL 子系统本身包含 CDC/outbox/projection 等
多文件边界时，技术目录才有信息价值。

## 5. 文件、package 与符号命名

| 对象              | 规则                | 示例                                    |
| ----------------- | ------------------- | --------------------------------------- |
| package/module    | `snake_case`        | `scheduled_tasks/`, `run_repository.py` |
| class             | `PascalCase`        | `RunService`, `RunRepository`           |
| function/variable | `snake_case`        | `create_run`, `tenant_id`               |
| constant          | `UPPER_SNAKE_CASE`  | `MAX_BATCH_SIZE`                        |
| private           | 单前导下划线        | `_to_run()`                             |
| test              | `test_<subject>.py` | `test_run_service.py`                   |

允许在清晰 package 中使用 `service.py`、`repository.py`、`models.py`、`schemas.py`。避免全局或无上下文的：

```text
utils.py
common.py
helpers.py
manager.py
base.py
factory.py
processor.py
```

如果确实是 factory/processor，文件名要带业务对象，例如 `agent_factory.py`、`artifact_processor.py`。

`__init__.py` 只定义窄公开面，不执行连接、注册、读取环境变量或其他 import-time side effect。禁止大量 star export。

## 6. `TypedDict`、Pydantic、dataclass、class、Protocol

“尽量强类型”不是所有对象都用 Pydantic。

| 工具         | 正确用途                                                             | 常见误用                             |
| ------------ | -------------------------------------------------------------------- | ------------------------------------ |
| `TypedDict`  | 必须保留 dict 语义的内部 shape、psycopg `dict_row`、第三方 stub      | 外部输入校验、状态机、运行时不变量   |
| Pydantic     | HTTP/RPC JSON、设置、provider payload、runtime parsing/serialization | 所有内部临时对象、数据库实体         |
| dataclass    | 内部值、用例输入/结果、不可变 record                                 | 未校验网络 JSON                      |
| 普通 class   | Service、状态机、资源生命周期、封装可变行为                          | 只有字段的数据袋                     |
| `Protocol`   | Store/Client/Clock 等可替换依赖的最小 shape                          | 每个 class 的镜像接口、全局 ports 包 |
| Enum/StrEnum | 稳定有限状态或 wire 值                                               | 一次性分支和开放字符串               |

### 6.1 `TypedDict`

```python
from datetime import datetime
from typing import TypedDict
from uuid import UUID


class RunRow(TypedDict):
    id: UUID
    tenant_id: UUID
    created_at: datetime
```

它只影响静态检查，运行时仍是普通 dict。规则：

- 网络输入先经 Pydantic/parser；不能 `cast(RunRow, payload)` 假装已经验证。
- 精确使用 `Required`/`NotRequired`；不为省事把整个类型设为 `total=False`。
- Row 类型留在 Repository 内部，不贯穿整个业务链路。psycopg 将 PostgreSQL UUID 映射为 `UUID`，不是自动变成 str。
- `dict_row` 的注解不执行字段校验；采用 typed row factory 或显式 parser 校验并映射，不能直接把任意 dict 赋成 TypedDict。

### 6.2 Pydantic

```python
from pydantic import BaseModel, ConfigDict, Field


class CreateRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prompt: str = Field(min_length=1, max_length=100_000)
```

- 自有 API 默认 `extra="forbid"`；第三方协议为前向兼容可局部 `extra="ignore"`。
- 是否 strict 按输入介质和字段决定；环境变量天然是字符串，不机械把 Settings 全部设为 strict。
- Pydantic validation error 在接口层映射，不传入业务包。
- Request/Response model 不直接作为数据库 Row 或状态对象。

### 6.3 dataclass 与行为 class

默认内部不可变数据：

```python
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True, kw_only=True)
class Run:
    id: str
    tenant_id: str
    created_at: datetime
```

- 简单不变量可在 `__post_init__` 校验。
- 复杂状态迁移使用普通 class，通过方法保护状态。
- 不写无意义 getter/setter；Python 属性已经是 API。
- 集合使用 `default_factory`；时间必须 timezone-aware。
- 不为每个字符串创建“DDD Value Object” class。

### 6.4 Protocol 与 Callable

依赖 shape 由消费方定义：

```python
# src/kokoro_agent/runs/service.py
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from kokoro_agent.runs.models import Run


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateRun:
    tenant_id: str


class RunRecords(Protocol):
    async def insert(self, run: Run) -> None: ...


async def create_run(
    input_: CreateRun,
    *,
    records: RunRecords,
    new_id: Callable[[], str],
    clock: Callable[[], datetime],
) -> Run:
    run = Run(id=new_id(), tenant_id=input_.tenant_id, created_at=clock())
    await records.insert(run)
    return run
```

上例仅展示依赖注入，`Run` 引用第 6.3 节模型；真实 CreateRun 的参数、身份授权、幂等和生命周期由 Agent 契约规定。

- 单方法函数依赖优先 `Callable`；多个稳定方法才使用 Protocol。
- 具体类无需继承 Protocol。
- 同语义的内部类型共享，不为 DTO/Command/Model/Row 五个名字复制字段；边界有转换语义才分开。
- 不暴露 psycopg connection、Redis client 或 HTTPX Response。
- 不创建 `IRunRepository`、`BaseRepository`、`ports/`。

## 7. Service 与 Repository

### 7.1 Service

Service/function 负责：业务授权、状态转换、事务边界、依赖调用顺序、幂等、重试判断与结果组装。

选择：

- 纯计算或单个简单用例：普通函数。
- 一组共享依赖的内聚用例：`RunService` class。
- 有生命周期/状态的对象：普通 class。
- 不为 DI 而把所有函数包装成 class。

### 7.2 Repository

Repository 是该能力的数据访问组件，不是 ORM 的同义词。默认 `runs/repository.py` 可以直接包含当前唯一
psycopg 实现；无需再配一套 `ports/run_repository.py` 和 `postgres/run_repository.py`。

它负责：

- 参数化 SQL 与 typed Row；
- tenant predicate；
- Row -> dataclass/business model；
- affected row 和数据库错误归一；
- 在传入 transaction 上执行锁与写入。

业务 Service 定义“为什么以及何时写”，Repository 定义“如何读写”。复杂只读 projection 可以用
`queries.py`/`queries/`，KV/checkpoint 才使用 `store` 命名。

## 8. psycopg、事务与异步

- Pool 在 `bootstrap.py`/runtime 创建并在 shutdown 关闭；不在每个请求/任务中新建连接池。
- 每个 request/job 获取独立 connection/transaction；不跨并发 task 共享 cursor。
- psycopg 值参数使用 `%s` 或 `%(name)s`，identifier 使用白名单/`psycopg.sql.Identifier`。
- 一个业务操作使用同一 connection；transaction client 不泄漏到 HTTP/worker 入口。
- 事务内不做外部网络调用；可靠事件的 outbox row 与业务事实同事务写，提交后派发，普通 commit 后回调不保证不丢。
- blocking SDK 不直接运行在 event loop；选择 async client 或明确 thread offload 与取消语义。
- `asyncio.TaskGroup` 优先用于结构化并发；后台 fire-and-forget task 必须登记、观测并在 shutdown drain/cancel。
- `asyncio.CancelledError` 是 BaseException 分支；不要用 `except BaseException` 或裸 except 吞掉。必要清理在 finally，随后传播取消。
- `TaskGroup` 中一个非取消异常会取消兄弟任务；明确部分成功和补偿。thread offload 被取消不等于底层线程已停止，副作用仍需幂等。
- psycopg AsyncConnectionPool 显式 `open()/wait()` 后就绪；设置 pool 上限、等待超时、statement/lock/idle transaction timeout，
  借还连接使用 context manager。事务后再释放；失效连接不回池，连接预算按最大实例数计算。
- Service 若需要多 Repository 事务，注入模块专用 `in_transaction(work)`，回调获得同连接绑定的数据访问能力；连接不逃逸回调。
- 40001/40P01 仅有限重试整个可重试事务；提交结果未知先按操作身份恢复，不把异常当作“肯定没有写入”。
- HTTPX 的 connect/read/write/pool timeout 之外，长链路需总体 deadline（如 `asyncio.timeout`）；限制响应字节数、重定向与并发。
- redis-py 使用进程级 async client，显式 aclose；区分命令、订阅和阻塞消费连接，设置 pool/command/reconnect 上限。
  Pub/Sub 可丢、Streams 需 ACK/reclaim/幂等；未知写入结果不盲重试，租约过期后的旧持有者须被持久化条件写拒绝。

## 9. 配置与 `.env.*`

### 9.1 统一策略

```text
development: .env -> .env.local -> shell/IDE environment（最高）
test:        .env.test -> .env.test.local -> pytest environment（最高）
production:  只读真实 environment / secret manager，不加载仓库 env 文件
```

- `.env.example`、`.env.test.example` 提交无 secret 示例。
- `.env`、`.env.local`、`.env.test`、`.env.test.local` 默认忽略。
- pytest 不加载开发 `.env.local`，避免本机状态污染。
- 不同时使用 pydantic-settings、python-dotenv、pytest plugin 三套隐式加载。

### 9.2 唯一 Settings 入口

```python
# src/kokoro_agent/settings.py
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        extra="ignore",
        case_sensitive=True,
        frozen=True,
    )

    environment: Literal["development", "test", "production"] = Field(
        validation_alias="KOKORO_AGENT_ENVIRONMENT"
    )
    database_url: SecretStr = Field(validation_alias="KOKORO_AGENT_DATABASE_URL")
    redis_url: SecretStr | None = Field(default=None, validation_alias="KOKORO_AGENT_REDIS_URL")

    def __init__(self, *, env_files: tuple[str, ...] = ()) -> None:
        super().__init__(_env_file=env_files or None)


def load_settings(env_files: tuple[str, ...] = ()) -> Settings:
    return Settings(env_files=env_files)
```

入口开发模式传 `(".env", ".env.local")`，测试传 `(".env.test", ".env.test.local")`，生产传空元组；
运行模式来自明确入口参数而不是通过默认加载开发文件猜测。大写环境变量通过 validation_alias 显式映射，避免
case-sensitive + 小写字段意外要求小写环境变量。实际 environment 优先于 dotenv，必须用隔离测试验证。

显式构造函数把装载参数限制为 env_files，Pyright 按真实入口签名检查；必填字段仍由 Pydantic 在启动时校验。
启动时加载一次并注入，不使用全局 `lru_cache` 把测试环境永久缓存；除 settings/入口装载外，业务代码不读取 `os.environ`。
Settings 的 `extra="ignore"` 只用于共享环境，不影响自有 API 的 `extra="forbid"`。URL 协议、允许主机和空值另行校验，
`SecretStr` 仅降低误打印风险，不是加密存储；仅在连接创建处调用 `get_secret_value()`。

## 10. HTTP/RPC/provider 边界

- HTTP 使用 `router.py`/`api.py` 和 `schemas.py`；入口只解析协议、trusted context、调用 Service、映射错误。
- Generated Proto/Pydantic/provider SDK 类型在 adapter/client 中终止，不传入核心状态和数据库。
- HTTPX client 进程级复用，明确 connect/read/write/pool timeout、limits、redirect 和 response size。
- provider 错误先归一成稳定内部错误；日志可以保留脱敏 cause，协议响应不泄漏原文和 secret。
- 每个调用传播 request ID、trace context、deadline 和 cancellation。
- 每条 API/消息定义唯一机器事实源方向，生成物只读；不得同时手改 Proto/OpenAPI/Pydantic 三份同字段模型。
- 全局异常处理只公开白名单业务错误；验证、认证、权限、冲突、超时和未知异常分别映射。请求/响应、错误及事件均有 contract test。

## 11. 时间、Enum 与错误

- 瞬时点使用 timezone-aware `datetime`，进入业务边界归一化到 `timezone.utc`。
- 纯日期使用 `date`；本地周期调度保存 IANA timezone，不把本地时间伪装成 UTC。
- 测试注入 clock，不全局 monkey-patch `datetime.now()`。
- 稳定状态使用 `StrEnum`/Enum 或 discriminated union；不要散落魔法字符串。
- 业务失败使用稳定异常类型或 Result；禁止捕获所有异常后返回 `None`/`False`。
- `raise ... from error` 保留因果链；外层统一脱敏映射。

## 12. import 与副作用

- 使用绝对 package import，包内很小范围可用清晰相对 import；全仓统一。
- 禁止 wildcard import、循环 import 补丁和 import-time service registration。
- `if TYPE_CHECKING` 仅解决真实 runtime dependency，不作为循环依赖常规方案。
- `cast`、`Any`、`# type: ignore` 必须局部、注明第三方缺口和移除条件。
- 模块导入不得创建数据库/Redis/HTTP client、启动线程、读取 secret 或发网络请求。
- 业务包通过 owner 的窄公开面协作，不从另一包导入其 Repository/Row；bootstrap 可以导入实现做装配。
- 文件约 400 行或函数约 60 行触发职责复核；超过 800/100 行默认拆分或登记有 owner、理由和到期日的例外。
  行数不自动决定新建 package；生成物按可再生条件豁免。

## 13. 测试与门禁

```bash
uv lock --check
uv sync --frozen
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest
uv build
```

测试层次：

| 层次         | 内容                                                  |
| ------------ | ----------------------------------------------------- |
| unit         | 纯 service、policy、状态机、parser                    |
| integration  | 真实 PostgreSQL、Redis、HTTP adapter/provider sandbox |
| contract     | JSON/Proto/event schema 与 producer/consumer          |
| architecture | import、env、Any、framework/Row 泄漏、旧目录          |
| smoke        | 真实入口、health/ready、graceful shutdown             |

- Python 测试目录统一 `tests/`，不使用 TS 的 `test/`。
- Fake/Fixture/InMemory 放 `tests/fixtures/`、`tests/doubles/`。
- pytest fixture 管资源生命周期，不共享可变全局 singleton。
- async test 使用与生产一致的 event loop 模型；不得靠 sleep 猜时序。
- 并发、取消、重复消息、checkpoint 恢复、事务回滚和 tenant 隔离必须有失败路径测试。
- 每个 run/worker 使用独立测试数据库/schema、Redis key prefix；复用已有实例，禁止清理其他套件的数据。
- 每个实例启动校验配置、schema 与关键依赖后才 ready。收到退出信号先停止接单/变为 not-ready，在截止时间内 drain/cancel，
  再逆序关闭 HTTP/Redis/Pool。重启通过持久化状态恢复，不依赖 finally 一定运行。
- 结构化日志与 trace 记录 operation/request_id/result/duration，异常边界统一脱敏；不输出 prompt、token、SecretStr 明文或 SQL 参数。

## 14. 架构门禁

CI 阻断：

1. 顶层 `domain/application/infrastructure/interfaces/ports/adapters/modules` 重新成为重复层；
2. handler、graph node 或 worker consumer 中散落 SQL；
3. 业务事实依赖 HTTPX Response、psycopg Row、Redis client 或 generated wire model；
4. `os.environ`/dotenv 出现在 Settings/entrypoint 之外；
5. import-time singleton 和网络副作用；
6. 裸 `dict[str, Any]` 贯穿业务、宽泛 cast/type ignore、file-wide suppression；
7. 每个包机械创建 `postgres/`、`redis/` 或空目录；
8. `BaseRepository`、service locator、万能 manager/utils/common；
9. 同一能力保留旧新两套实现、fallback 或 compatibility alias；
10. 缺失 Ruff、Pyright、pytest、schema 和真实集成验证。

## 15. 创建文件/package 前的设计门

Agent 新建文件/package 或调整职责边界前列出以下设计；既定方案引用即可，已有文件内局部修复只说明 owner 与验证：

```text
业务 owner 与 package 名
现有相邻文件和框架约定
新对象的职责与公开 API
为何新建文件/package，而不是扩展现有内聚 module
同步/异步模型与资源生命周期
Pydantic/TypedDict/dataclass/class/Protocol 的选择理由
SQL、事务、cache、provider、protocol 影响
至少两个放置方案及淘汰理由
验证命令和失败路径
```

新顶层 package、跨 package 公共抽象、进程入口或 framework boundary 必须有技术设计/ADR。禁止从模板批量生成
空 package；禁止看到 PostgreSQL/Redis 就创建同名业务目录。

## 16. 重构顺序

1. 盘点入口、Run/Agent/Tool/Skill/MCP/Approval owner、协议、表和资源生命周期；
2. 先完成 AGENTS 的技术方案/API/数据文档门，画出 package/import；补保留行为基线和目标契约测试，不先机械搬文件；
3. 在不可信边界加入 Pydantic/parser，消除贯穿链路的 `Any`；
4. 把业务行为收敛到 service/明确函数，把 psycopg、cache、HTTP client 放回 owner package；
5. 仅在多实现或高价值单元测试需要时提取 Protocol；
6. 删除旧层、重复 Repository、fallback、compat 和 import-time singleton；
7. 执行 Ruff、Pyright、unit、integration、contract、schema、smoke；
8. 一个 commit 只处理一个可验证能力切片。

## 17. 参考依据

- [PyPA: src layout vs flat layout](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/)
- [Python typing: TypedDict](https://typing.python.org/en/latest/spec/typeddict.html)
- [Python typing: Protocol](https://typing.python.org/en/latest/spec/protocol.html)
- [Pydantic models](https://docs.pydantic.dev/latest/concepts/models/)
- [Pydantic settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [Ruff](https://docs.astral.sh/ruff/)
- [Pyright configuration](https://microsoft.github.io/pyright/#/configuration)
- [psycopg 3 transactions](https://www.psycopg.org/psycopg3/docs/basic/transactions.html)
- [HTTPX advanced clients](https://www.python-httpx.org/advanced/clients/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [PEP 8](https://peps.python.org/pep-0008/)

这些资料用于建立 Python-native 基线；Google 指南提供可读性、异常、命名和 import 的企业经验，PyPA/官方类型规范/Pydantic
决定工具语义。目录仍由业务能力和当前代码事实决定，不复制某一框架脚手架。国内团队经验参照 SQL 手册中的 Alibaba 指南，
不把 Java/MySQL 的细则强行套进 Python。

- [Python 官方版本支持](https://devguide.python.org/versions/)
- [uv locking and syncing](https://docs.astral.sh/uv/concepts/projects/sync/)
- [psycopg typed row factories](https://www.psycopg.org/psycopg3/docs/advanced/rows.html)
- [asyncio task cancellation / TaskGroup](https://docs.python.org/3/library/asyncio-task.html)
