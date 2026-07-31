# 仓库地图

> 历史局部说明。当前四子仓拓扑、Platform 模块化核心、存储与跨仓协议以 `24-federated-product-platform-architecture.md`
> 和 `docs/CODEBASE_MAP.md` 为准；本文残留的 MySQL/旧子仓描述不得指导实现。

repositoryTopology: federated-submodules-v1

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

## 已定案的根仓拓扑

Kokoro 根仓永久采用治理型 superproject：`.gitmodules` 管理四个独立子仓，根 tree 以 mode `160000`
精确锁定每个经过组合验证的 commit。该选择服务于独立构建、部署、扩缩容、发布与回滚，不是页面展示。

子仓拥有自己的 lock、CI、artifact、migration、release、rollback 和历史；根仓拥有 contract 单源、root-only
工具、统一 Infra/集成编排、兼容矩阵、BOM 和 gitlink promotion。根 CI 只初始化当前 root commit 的 pin，
不得 checkout 浮动 sibling branch。

跨仓运行时通过 HTTP/RPC、SSE 或 durable async command/event transport；禁止兄弟源码 import、共享进程内
对象或跨服务直写数据库。仓库边界不机械决定 Platform 内部进程拆分：同仓 modular core 可以为独立部署
提供 RPC adapter，无需为每个后台能力创建新 Git 仓库。

版本提升与恢复规则见 [ADR-007](../decisions/ADR-007-kokoro-platform-submodule.md) 和
[Wave 0 v2.0](../../superpowers/specs/2026-07-25-wave-0-repository-contract-foundation-design.md)。
