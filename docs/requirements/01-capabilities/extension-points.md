---
status: 🔴 待用户拍板
layer: capabilities
owner: claude
updated: 2026-06-14
refs:
  - ADR-009
---

# 能力 · 扩展位(留缝,未建)

> 一句话:这篇登记**已留架构缝、尚未实现**的能力,防止它们被误当已建。每项注明缝在哪、缺什么。来源 [能力扩展架构 spec](../../superpowers/specs/2026-06-12-capability-extension-design.md)。

## 🔲 工具接入(X 系,部分已建)

- **现状**:链路已通,`now`/`fetch_url` 已建(见 [tools](./tools.md))。
- **缝**:7 步新 kind SOP 固化;更多工具按 SOP 增量,零契约破坏。
- **缺**:具体工具集(搜索/代码执行/文件等)按需。

## 🔲 workspace(产物工作区)

- **缝**:`artifact.created` 事件 SOP + redis 取回通道(设计在案)。
- **缺**:产物实体模型、存储、产物页 UI(canvas 矩阵仅原型)。
- **依赖**:北极星「产物分享」的真实落点 → 见 [vision](../00-product/vision.md)。

## 🔲 teams(多代理协作)

- **缝**:并行 run 传输层已就绪(session fan-out 支持多订阅者)。
- **缺**:团队/角色模型、并行 run 编排、协作 UI。

## 🔲 HITL(工具执行前 暂停 / 确认 / 恢复)

- **缝**:control stream 已在 stream 架构文档**留缝**(双向通道,web→session→agent 的控制信令)。
- **缺**:控制事件契约、agent 侧暂停点、web 侧确认 UI、恢复语义。
- **关联**:这是 [trust-modes](../00-product/trust-modes.md) 的 Plan/Default/Auto 完整语义所**依赖**的底座;当前 Mode 只落地 Fast/Thinking 执行风格,确认/暂停未实现。

## 推进规则

任一项从 🔲→🟡→✅:先在 [scope-and-boundary](../00-product/scope-and-boundary.md) 升态,补对应能力/流程文档,链到新契约 + 测试 slug。

## 引用

- 扩展架构:[capability-extension-design](../../superpowers/specs/2026-06-12-capability-extension-design.md)
- 仓边界:[ADR-009](../../decisions/ADR-009-repository-boundaries-and-ownership.md)
