# ADR-006 Agent Sandbox Runtime

## 状态

Proposed for V1 implementation

## 背景

Agent 需要执行工具、代码、文件操作、MCP、子代理和未来的创作任务。不同部署环境对隔离要求不同：

- 本地开发需要低成本、可调试。
- 生产环境需要隔离文件系统、网络和进程。
- 某些任务需要云 sandbox，例如 E2B。
- 企业部署可能要求自有 sandbox provider。

如果把 sandbox 写死在 agent 工具里，后续会很难替换；如果一开始做过度抽象，也会拖慢 V1。

## 决策

V1 将 sandbox 作为 `kokoro-agent` 的基础设施能力，提供三种策略：

| 策略 | 用途 | 默认 |
|---|---|---|
| `local` | 本地开发、受控测试、低风险工具 | 默认 |
| `e2b` | 需要远程隔离执行代码或文件任务 | 可配置 |
| `custom` | 私有云、自研 sandbox、企业隔离环境 | 可配置 |

Agent application 层只依赖 `SandboxRuntime` 这类明确接口，不使用 `ports/` 目录命名。具体实现放在 agent infrastructure 下，例如 `infrastructure/sandbox/local.py`、`e2b.py`、`custom.py`。

## 能力边界

Sandbox runtime 必须支持：

- 创建 workspace
- 写入输入文件或上下文
- 执行命令或代码
- 读取结果文件
- 限制超时、网络、文件系统和资源
- 清理 workspace
- 返回结构化执行结果

V1 不要求 sandbox 承担：

- 积分扣减
- 用户权限最终决策
- session message 写入
- Web 可见事件格式化

## 和 LangChain/LangGraph 的关系

LangChain/LangGraph 负责 agent 编排、tool calling、middleware、checkpoint 和 HITL。Sandbox 是工具执行的基础设施之一：

- tool 调用前由 permission/HITL middleware 决定是否需要用户确认。
- tool 执行时通过 sandbox runtime 隔离。
- tool 结果回到 LangChain/LangGraph，再由 agent event adapter 发 raw event。
- checkpoint/memory 存 agent 自己的执行上下文，不进入 session messages。

## 影响

正向影响：

- 本地默认可用，生产可切 E2B 或 custom。
- Agent 工具不会和某个 sandbox SDK 深度耦合。
- 未来可为 code、data、browser、MCP 分别配置 sandbox policy。

代价：

- 每个 sandbox provider 都需要集成测试和安全审计。
- E2B/custom 需要额外密钥、网络和成本治理。
- 本地 sandbox 不能被误认为生产安全边界。

## 强制规则

- `local` 只能作为开发默认和明确低风险策略。
- 生产高风险工具必须配置 sandbox policy。
- sandbox 结果不能直接写 session messages，必须回到 agent -> session 链路。
- agent 不因 sandbox 成功而直接扣积分。
