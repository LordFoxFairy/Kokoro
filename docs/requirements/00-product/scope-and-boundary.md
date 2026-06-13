---
status: 🟡 草稿
layer: product
owner: claude
updated: 2026-06-14
refs:
  - ADR-007
  - ADR-009
---

# 范围与边界 — 已建 / 已设计 / 已规划

> 一句话:这篇是整本手册防漂移的根。明确区分**真实造出来的**、**只画了原型的**、**留了缝还没做的**。任何下游需求不得把「已设计」当「已建」描述。

## 为什么需要这篇

`docs/product/` 把产品描述成「canvas 生成器矩阵」(图片/视频/数字人/音频/设计/文档/站点 7 个生成器 + 产物页),那是**原型时代的设计**(`docs/prototypes/variant-a-mi-mu/` 的静态 HTML)。但真实三仓代码里**没有任何 canvas/generator**——造出来的是**对话 + agent 活动流**的基础骨架。手册必须如实分界。

## 三态分界

### ✅ 已建(真实在跑,有代码 + 测试 + CI)

三仓 stream 聊天系统:

- **kokoro-web**(Next.js):聊天壳 + agent 活动流渲染。组件面:对话线程(assistant-turn / message-bubble / markdown-message)、工具调用行(running/done/error)、子代理行、todo 计划条、过程块(思考/工具/子代理披露)、composer、多会话 session-rail。
- **kokoro-session**(TS):SSE/replay 归属者。归一化 13 kind → AGUI 信封、去重、Last-Event-ID 续订、memory/redis 双后端 fan-out。
- **kokoro-agent**(Python):deepagents worker。产 13 kind 原始执行事件、seq 单调、segment 分段、内置工具(`now` / `fetch_url`,带撞名守卫 + SSRF 防护)、子代理(built-in/config-custom/runtime-custom)。
- **跨仓契约**:`contract/events.yaml` 单源 + `verify.py` 门禁(6 镜像)。四仓 CI 全绿。

能力清单见 [01-capabilities/](../01-capabilities/);验收见 [02-flows/](../02-flows/)。

### 🟡 已设计(有原型/spec,真实仓未落地)

- **canvas 产物矩阵**:7 类生成器 + 产物页(`docs/product/03-product-form/` + `docs/prototypes/`)。**仅静态原型**(ADR-007:原型=设计 spec,生产另起真栈)。真实仓**无**。
- **产物分享 / 模板市场 / 增长引擎**:`docs/product/07-growth/`,设计框架已定,未实现。
- **设计系统落地**:`docs/product/05-design-system/` tokens/组件(🔴 待填),web 实际用的是自有 `activity.css` 暖木风,未对齐原型 design system。

### 🔲 已规划(留了架构缝,未实现)

来源:[能力扩展架构 spec](../../superpowers/specs/2026-06-12-capability-extension-design.md)。

- **工具接入(X 系)**:链路已通(`fetch_url`/`now` 已建),更多工具按 SOP 接入 → 见 [tools](../01-capabilities/tools.md)。
- **workspace**:artifact.created SOP + redis 取回通道(设计在案,未建)。
- **teams**:并行 run 传输层已就绪,多代理协作未建。
- **HITL(工具执行前暂停/确认/恢复)**:control stream 已在文档留缝,**未实现**。见 [extension-points](../01-capabilities/extension-points.md)。

详见 [extension-points.md](../01-capabilities/extension-points.md)。

## 边界规则

- 描述需求时必须标注三态;**不得**把 🟡/🔲 写成 ✅。
- 新能力从 🔲→🟡→✅ 推进时,同步更新本表 + 对应能力/流程文档状态。

## 引用

- 原型=spec 决策:[ADR-007](../../decisions/ADR-007-prototype-and-production-stack.md)
- 仓边界与归属:[ADR-009](../../decisions/ADR-009-repository-boundaries-and-ownership.md) · [docs/product/04-architecture/repository-boundaries.md](../../product/04-architecture/repository-boundaries.md)
- 扩展架构:[capability-extension-design](../../superpowers/specs/2026-06-12-capability-extension-design.md)
