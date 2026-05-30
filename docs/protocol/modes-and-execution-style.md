---
status: 🟢 accepted
version: 1.0.0
producer: kokoro-session
consumers:
  - kokoro-web
  - kokoro-agent
backward-compatibility: New execution styles may be added additively; existing style names and semantics are stable in v1.
---

# Modes & Execution Style

> 把“产品层的信任档位”和“本次执行风格”拆开，避免一个词同时背两种语义。

## Two layers

### 1. Product mode / trust mode

这是用户对 Kokoro 的**授权节奏**，对应权限与审批频率。

初期约束：
- phase 1 UI 可以只显默认档位
- 后续可扩展为 `plan` / `default` / `auto`

### 2. Execution style

这是本次 run 的**表现风格**，决定用户会看到多少中间态。

v1 只定义两档：
- `fast`
- `thinking`

## `fast`

- 更短路径
- 少展示中间态
- 只保留必要的 streaming / tool summary / completion 信号
- 适合“我就想快点有个可用初版”

## `thinking`

- 允许更丰富的进度摘要
- 允许出现 `thinking.summary` 一类事件
- 适合复杂任务、需要 plan / refine 的场景
- 暴露的是**可给用户看的摘要**，不是原始 chain-of-thought

## Rules

- execution style 由 `run.mode.selected` 事件显式记录
- `fast` 与 `thinking` 共享同一聊天壳，不分裂成两个页面
- execution style 不等于权限模式：`thinking` 不自动意味着更高权限
- phase 1 允许只有轻量 UI 呈现，不要求完整 reasoning 可视化系统
