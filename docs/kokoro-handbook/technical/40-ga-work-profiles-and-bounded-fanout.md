# 40. GA Agent 协作与有界后台任务

状态：当前协作专项，2026-08-27。

本页服从 [42 GA 核心架构](42-ga-core-architecture.md)。GA 只有一个 DeepAgents 运行底座；
协作分成两种，不再引入第三套任务运行时。

## 1. 两种协作语义

| 需求 | 原生落点 | 用户回复归属 |
|---|---|---|
| Agent 幕后调用专业能力 | DeepAgents native `subagents` | 发起 Agent 统一回复 |
| 专业 Agent 接手同一会话 | official `langgraph-swarm` | 当前 Swarm peer 回复 |

单 Agent 足够时直接运行，不为了假设中的未来场景拆角色。Swarm 不做批处理，native subagent
也不改变用户会话控制权。

## 2. Feature 声明

```text
music      -> [music]
chat       -> [general]
music_chat -> [general, music] + general <-> music handoff
```

Feature 是静态业务组装声明；它确定 Agent、入口和允许的 handoff。Session、Browser、Run 输入
不能临时添加 Agent、边、工具、Skill、MCP 或并发参数。

## 3. 有界后台任务

当一个 Feature 确实需要对多个独立项进行后台处理时，由主 Agent 使用 DeepAgents native
subagent，并在 GA RunLedger 中记录父 Run 下的私有 WorkItem：

```text
输入规范化/去重
  -> parent RunLedger 记录 WorkItem（稳定 item_id）
  -> DeepAgents native subagent 执行
  -> 结果按 item_id 写回 parent ledger
  -> 主 Agent 汇总并回复
```

`WorkItem` 不是 child Session、child Run、独立 checkpoint 或浏览器对象；它不改变计费单位和
终态归属。上限、取消、重试和迟到结果都由 parent RunLedger 收口，DeepAgents 仍拥有实际 loop
和 native state。

## 4. 扩展规则

- 新增独立产品能力：新 Agent + 最小 Feature。
- 新增组合能力：Feature 复用已有 Agent，必要时声明官方 handoff。
- 新增后台协作者：在 Agent 的 `subagents` 声明中加入 native subagent。
- 只有在需要确定性的跨节点步骤时，才直接使用 LangGraph 官方原语；它不是 GA 自有 runtime，
  也不改变 Feature/Agent/Run 三个公开词汇。

## 5. 目录落点

```text
agents/       完整 Agent 声明
features/     Feature 组装声明
agent_factory.py  DeepAgents 唯一构造入口
swarm.py      official Swarm 最薄接线
execution/    Run、WorkItem、HITL、effect、终态
worker/       Redis、lease、recovery、readiness
```

禁止新增 `Feature 组合`、`compiler/`、`runtime/`、`framework/`、`ports/`、child Session 或第二
scheduler。
