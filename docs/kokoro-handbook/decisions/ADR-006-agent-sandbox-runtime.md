# ADR-006 Agent Sandbox Runtime

## 状态

Proposed for V1 implementation

## 背景

Agent 需要执行工具、代码、文件操作、MCP、子代理和未来的创作任务。
不同部署环境对隔离要求不同：

- 本地开发需要低成本、可调试。
- 生产环境需要隔离文件系统、网络和进程。
- 某些任务需要云 sandbox，例如 E2B。
- 企业部署可能要求自有 sandbox provider。

如果把 sandbox 写死在 agent 工具里，后续会很难替换；
如果一开始做过度抽象，也会拖慢 V1。

## 决策

V1 将 DeepAgents backend/storage 与执行 sandbox 分开建模。
Kokoro 不定义一套平行 sandbox framework，而是把策略编译到
DeepAgents backend、filesystem permissions、middleware、wrapped tools
和 sandbox adapter。

| 维度 | 策略 | 用途 | 默认 |
| --- | --- | --- | --- |
| storageBackend | `state` | 普通推理、受控工具编排、安全默认 | 生产默认 |
| storageBackend | `store` | 持久化文件视图、skills、memory | 可配置 |
| storageBackend | `custom` | 私有云、自研 DeepAgents backend | 可配置 |
| executionSandbox | `none` | 无命令/代码执行能力 | 生产默认 |
| executionSandbox | `local_shell` | 本地开发、受控测试 | 开发默认 |
| executionSandbox | `e2b` | 远程隔离执行代码或文件任务 | 可配置 |
| executionSandbox | `custom` | 企业隔离执行环境 | 可配置 |

Agent application 层只依赖明确接口，不使用 `ports/` 目录命名。
具体实现放在 agent infrastructure 下，例如 backend mapper、permission
compiler、sandbox adapter、capability tool wrapper。

## 能力边界

Storage backend 必须支持：

- DeepAgents 文件视图。
- skill 文件和按需资料加载。
- memory/store namespace。
- checkpoint 需要时的持久化协作。

Execution sandbox 必须支持：

- 创建隔离 workspace。
- 写入输入文件或上下文。
- 执行命令或代码。
- 读取结果文件。
- 限制超时、网络、文件系统和资源。
- 清理 workspace。
- 返回结构化执行结果。

V1 不要求 backend/sandbox 承担：

- 积分扣减
- 用户权限最终决策
- session message 写入
- Web 可见事件格式化

## 和 LangChain/LangGraph 的关系

LangChain/LangGraph/DeepAgents 负责 agent 编排、tool calling、middleware、
checkpoint、HITL、skills、subagents 和 backend 文件视图：

- tool 调用前由 `interrupt_on`、filesystem permissions、backend hook 或
  wrapped tool 决定是否需要用户确认。
- custom/MCP/capability tools 通过 tool wrapper 和 `interrupt_on` 治理。
- filesystem tools 通过 DeepAgents filesystem permissions 治理。
- 命令/代码执行通过 execution sandbox adapter 隔离。
- tool 结果回到 LangChain/LangGraph，再由 agent event adapter 发 raw event。
- checkpoint/memory 存 agent 自己的执行上下文，不进入 session messages。

## 影响

正向影响：

- 本地开发可用 local_shell，生产默认不把本地 shell 当安全边界。
- 生产可切 E2B 或 custom backend；其它官方 backend 后续按需扩展。
- Agent 工具不会和某个 sandbox SDK 深度耦合。
- 未来可为 code、data、browser、MCP 分别配置 sandbox policy。

代价：

- 每个远程 backend 都需要集成测试和安全审计。
- sandbox/custom 需要额外密钥、网络和成本治理。
- 本地 sandbox 不能被误认为生产安全边界。

## 强制规则

- `local_shell` 只能作为开发默认和明确受控测试策略。
- 生产高风险工具必须配置 execution sandbox 或 HITL。
- 缺 provider 依赖时必须 fail loud。
- backend/sandbox 结果不能直接写 session messages。
- 结果必须回到 agent -> session 链路。
- agent 不因 sandbox 成功而直接扣积分。
