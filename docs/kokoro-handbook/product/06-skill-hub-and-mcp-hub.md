# Skill Hub 与 MCP Hub 产品手册

> **状态：历史 V1 Capability Hub 产品视图。**本文的统一 registry、Skill 版本、grant 与 MCP 启用态模型不定义
> 当前 GA runtime。目标以 [33 GA-first SkillRuntime](../technical/33-ga-first-skill-runtime-architecture.md)、
> [36 GA 整体 Agent 技术方案](../technical/36-ga-final-agent-technical-plan.md) 与
> [ADR-022 动态 Capability 重验](../decisions/ADR-022-run-execution-attestation-and-dynamic-capability-resolution.md)
> 为准：GA 默认 Skill 自己闭环，CA 仅拥有用户/session Skill logical path、visibility 与 CRUD，动态 Skill 只经
> `find_skills/load_skill` 进入 GA workbench；不引入 Session Skill binding、全量 grant 或 Skill 版本产品平台。

> 2026-07-07 修订：产品上可以继续呈现 Skill Hub / MCP Hub 两个分区，但服务边界不拆
> 两套 registry。能力控制面采用一个 capability hub，内部按 kind 区分 skill / mcp /
> subagent，共享 namespace 归属、启用态、版本、审核、配额和 grant 骨架。

## 定位

Skill Hub 和 MCP Hub 是两个能力市场。

```text
Skill   可复用能力包：固化的提示、流程、工具组合，开箱即用。
MCP     外部工具/资源接入：让 Agent 连到第三方系统、数据源、API。
```

General Agent 可以调用 skill，也可以调用 MCP。两者都是 Agent 的能力来源，不是独立产品入口。

## 功能 Launcher

功能不靠线性侧栏堆。所有功能模块以「功能」Launcher 注册表网格呈现。

```text
侧栏       保持精简（如 最近 / 项目 / 功能 三项），不随功能数膨胀。
功能 Launcher  注册表驱动的网格，Skills、MCP、video、image、code 等都是其中的模块。
新增模块   = 注册表里加一条配置，不是侧栏加一行。
```

这保证模块越加越多时，侧栏不被挤爆，发现路径统一。

## Skill Hub

```text
Skill 是什么
  一个可复用能力包。封装提示、参数、工具调用、输出格式。

用户任务
  浏览 skill、启用 skill、在对话或 Studio 中使用 skill、查看运行结果。

呈现
  Launcher 网格里的一个模块；进入后是 skill 列表和详情。
```

## MCP Hub

```text
MCP 是什么
  外部工具/资源接入点。让 Agent 连接第三方系统并读写资源。

用户任务
  浏览可接入的 MCP、连接/授权、在对话中让 Agent 使用、管理连接。

呈现
  Launcher 网格里的一个模块；进入后是连接列表和接入向导。
```

## 与 Agent 的关系

```text
General Agent 可以：
  调用 skill。
  调用 MCP。
  组合 skill + MCP 完成任务。

General Agent 不可以：
  绕过 siteId 访问其它站点的 skill / MCP。
  直接扣积分（扣费走 credit 闭环）。
```

Agent 编排见 [../technical/03-agent-architecture.md](../technical/03-agent-architecture.md)。

## 权限和可见性

按 siteId 和 entitlement 控制。

```text
siteId        哪些 skill / MCP 在当前站点可见。
entitlement   套餐决定可用哪些、并发多少、是否可接入自定义 MCP。
workspace     团队内的连接和授权按 workspace 隔离。
```

跨站不共享 skill 启用状态和 MCP 连接。

## 计费

skill 和 MCP 的使用按 featureKey 扣费，走 credit 闭环。

```text
skill.<name>.run
mcp.<server>.call
```

定价由 credit 决定，model 只给成本参考。详见 [07-pricing-credit-plans](07-pricing-credit-plans.md) 和 [../business-flows/credit-reserve-commit-refund.md](../business-flows/credit-reserve-commit-refund.md)。

## 设计红线

```text
不把每个 skill / MCP 都塞成一行侧栏导航。
不让 skill / MCP 跨站默认可见。
不让 Agent 绕过 credit 直接调用计费能力。
不把 MCP 连接凭据按全局而非 siteId/workspace 存储。
```

## 后续任务

```text
P0  功能 Launcher 注册表结构。
    skill / MCP 模块条目和详情页。
    skill.* / mcp.* featureKey 定义。
P1  自定义 MCP 接入向导和授权管理。
    skill 市场和启用状态按 site 隔离。
```
