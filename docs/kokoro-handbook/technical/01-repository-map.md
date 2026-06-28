# 仓库地图

## 主仓 Kokoro

定位：产品、架构、跨仓契约、handbook、ADR、原型和治理入口。

Owns:

- `docs/kokoro-handbook`
- `contract/events.yaml` 及生成脚本
- 跨仓架构报告、ADR、业务链路
- 子仓版本治理和 CODEBASE_MAP

Does not own:

- runtime 服务实现
- 子仓内部实现细节
- 平台业务服务的运行时代码

## kokoro-web

定位：用户界面和浏览器端会话投影。

Owns:

- Next.js 页面、组件、样式、交互
- SiteContext 注入和用户可见状态
- session snapshot 加载
- SSE 消费、事件严格解析、本地 reducer
- 本地缓存和刷新体验

Does not own:

- session 生命周期真源
- Mongo/Redis 写入
- agent 执行、工具、checkpoint
- billing、credit、payment、model pricing

## kokoro-session

定位：会话域服务和浏览器会话契约拥有者。

Owns:

- sessions / messages / runs / session_events
- 同 session 单 active run admission
- session snapshot API
- browser-facing session events
- agent raw event relay 和归一化
- Mongo 持久化、Redis live fanout、SSE

Does not own:

- LLM 执行和工具调用
- agent checkpoint/memory 内部结构
- Web 组件渲染
- 积分扣减、支付、模型价格决策

## kokoro-agent

定位：Agent 执行 runtime。

Owns:

- LangChain/LangGraph/DeepAgents 编排
- model runtime 选择后的执行
- tools、subagents、middleware、HITL
- sandbox runtime: local / E2B / custom
- agent checkpoint、memory、tool state
- raw execution events

Does not own:

- 浏览器会话事件契约
- session messages 历史
- Web replay
- credit ledger 和支付
- SiteContext 最终鉴权

## kokoro-platform

定位：平台核心业务域集合，由对应模块 agent 继续补齐。

Owns:

- site / user / workspace / project
- model registry / model policy
- credit / payment
- admin permissions / audit
- MySQL 结构化核心业务数据

Does not own:

- Agent 执行细节
- session event replay
- Web 本地渲染

## 根仓拓扑建议

V1 推荐承认主仓是治理型顶级仓库：子仓可以作为受控 submodule/gitlink 管理版本，但 CI 和文档必须一致。不能同时出现"文档说非 submodule、Git 实际是 submodule、CI 又 checkout sibling main"的混合状态。

后续实现前先选定：

1. 治理型 submodule 根仓：根仓提交锁定每个子仓 commit，CI 按 gitlink 版本验证。
2. 纯 docs/protocol 根仓：移除 gitlink，子仓通过 `repos.yaml` 或 `docs/CODEBASE_MAP.md` 标注。

如果目标是"看着是一个顶级代码仓库"，推荐第 1 种。子模块当前状态和差异见 [migration-checklist](../operations/migration-checklist.md) 与本仓 `.gitmodules`。
