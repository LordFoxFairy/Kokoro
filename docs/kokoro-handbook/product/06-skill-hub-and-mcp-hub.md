# Skill Hub 与 MCP Hub 产品手册

> 状态：2026-10-04。当前规则以 [当前 PRD](09-v2-prd.md) FR-10/11 和现 Platform/BFF/Agent 的三面与机器契约为准。
> 以下 Hub/Launcher 描述保留发现入口和长期市场视图，不定义共享 registry、新服务或本轮市场化范围。
> 当前 Platform 目标首批为 Skills/MCP 两个域；物理 cutover 未验前仍如实记录 kokoro-capability。
> 目录可见、个人安装/启用、连接授权、选中 refs、运行时加载分别显示；不把浏览器选中冒已安装/已连接/已执行。

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

执行费用遵循 [07 正式积分规则](07-pricing-credit-plans.md) 与 ADR-033；不由 Hub/Web 自行定价，不用历史 featureKey 固定价冒当前实际用量结算。

## 验收与长期方向

T-K02–K07/T-A02 覆盖发布、个人安装、选择、真实加载、MCP 连接和撤权；完整步骤及现状态在 [唯一测试台账](../../test-cases.md)。
Launcher 网格/市场上架/审核与专业 Studio 的旧设想不是新增本轮任务；目录存在不证明连接或运行链完成。
