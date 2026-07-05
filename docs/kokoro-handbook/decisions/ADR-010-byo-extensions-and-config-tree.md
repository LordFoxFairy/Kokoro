# ADR-010 BYO 扩展点与统一配置树

## 状态

Accepted（2026-07-05；custom backend + agent 配置树 + examples 族已落地并验证）

## 背景

两个并发的痛点：

1. **custom backend 是占位**：ADR-006 列了 `custom` 策略但无实施路径。企业/私有云要插入
   自己的沙箱只能改本仓源码。
2. **配置散**：agent 有 40+ 平铺 env、两个独立 yaml、一个 JSON 字符串 env
   （custom subagents）；`WebToolSettings` 一类 env 组各自为政。没有一个"照着抄"的单一
   参考面，部署配置全靠翻代码。

## 决策一：BYO 扩展点约定（custom backend 首个实施）

自带代码扩展统一走 **`pkg.module:attribute` 引用 + importlib 加载 + 契约校验 fail-loud**：

- 使用方 pip 安装自己的包，配置 `KOKORO_CUSTOM_BACKEND=my_pkg.sandbox:make_backend`
  （可选 `KOKORO_CUSTOM_BACKEND_CONFIG=xx.yaml` 自由参数，原样透传、工厂自校验）。
- 工厂契约：`def make_backend(ctx: CustomBackendContext) -> BackendProtocol`；
  ctx 携带 `run_id / workspace / workspace_root / prior_sandbox_id / config`。
- **统一生命周期面**：所有沙箱产物（docker/e2b/custom）以 `sandbox_id` 属性声明
  自己可绑定——编排层单点 keep-first 落 ledger，HITL resume 经 `prior_sandbox_id`
  重连而非新建。custom 产物不带该属性即不绑定（无状态沙箱合法）。
- 坏引用/坏产物在装配期爆炸（模块不存在、attr 缺失、不可调用、缺核心 backend 方法），
  绝不静默降级。

### 分派采用注册表（Strategy）

`make_backend_for_run` 不再 if 链：五档各一个 connector 进
`_CONNECTORS: dict[Backend, SandboxConnector]`，生命周期绑定收敛为分派器内单点。
加新档 = 写 connector + 注册一行；`test_connectors_cover_backend_enum` 守卫
"枚举加值忘注册"在测试期爆炸。

## 决策二：统一配置树（KOKORO_AGENT_CONFIG）

单一 yaml 按域分组（model / stream / mongo / checkpoint / ledger / sandbox /
web_tools / subagents / limits / retention），机制为**摊平叠加**：

- yaml 树按 `config_file.py` 的映射表摊平成"虚拟 env 底座"，真实 env 原样叠加——
  解析逻辑单源不变，优先级 **env > yaml > 内置默认** 自然成立，存量部署零破坏。
- 映射表即配置 schema：未知键 fail-loud；**凭据键故意不在表内**（api key/secret
  写进 yaml 即报错），强制 env/secret 注入。
- `KOKORO_WORKSPACE_CONFIG`（ADR-009）保持独立文件：它是 session/agent 双侧共读的
  跨服务契约，并入单侧配置树会造成双源。agent 配置树以 `workspace_config:` 键指向它。

### 参考模板族（config/examples/）

每种部署形态一份可直接照抄的 example：`agent.example.full.yaml`（全域注释版）、
`workspace.example.{local,s3}.yaml`、`namespaces.example.{local,docker,e2b,custom}.yaml`、
`custom-backend.example.yaml`。namespaces 文件同时接受 yaml/JSON
（yaml 为 JSON 超集，session loader 统一 yaml 解析）。
`test_config_file.py` 加载 example 防文档漂移。

## 范围外

- session 侧同构配置树：session env 仅 ~10 个，现阶段 yaml 收益低；namespaces/workspace
  两个 yaml 已覆盖其可变面。需要时按同一摊平机制对称实施。
- 插件市场/entry-points 发现机制：无场景不做；`module:attr` 显式引用已满足企业自带。

## 强制规则

- 凭据永不进任何配置文件；映射表不得添加凭据键。
- 加配置项三件套缺一不可：Settings 字段 + 映射表一行 + example 一行。
- custom 工厂的产物必须过核心方法鸭子校验；扩展面（execute 等）缺失属工厂作者责任。
- BYO 代码运行在 agent worker 进程内：部署方对其供应链安全负责（与自装依赖同责任面）。
