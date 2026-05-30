# ADR-009 · 四仓拆分：Kokoro 只做 docs / prototype / protocol

- **日期**：2026-05-28
- **状态**：accepted
- **决策者**：用户拍板，Claude 起草
- **关联**：[ADR-007](./ADR-007-prototype-and-production-stack.md)、[ADR-008](./ADR-008-chat-alignment.md)、[../PROJECT-STATE.md](../PROJECT-STATE.md)、[../product/04-architecture/repository-boundaries.md](../product/04-architecture/repository-boundaries.md)

---

## 决策

Kokoro 系统按 **4 个独立 Git 仓库** 拆分，禁止 Monorepo 硬引用：

1. **`Kokoro`**：产品文档、ADR、静态原型、跨仓协议文档
2. **`kokoro-web`**：Bun + Next.js 前端，负责聊天壳、AGUI 渲染、SSE 消费
3. **`kokoro-session`**：Bun / TypeScript 会话中枢，负责会话生命周期、AGUI + SSE、Redis replay / resume、权限决策
4. **`kokoro-agent`**：Python + DeepAgents，负责规划、执行、工具编排与标准化事件产出

`Kokoro` 仓库**不承载运行时代码**。这里定义协议与体验，运行时在另外 3 个仓里实现。

---

## 所有权表

| Repo | Owns | Must not own |
|---|---|---|
| `Kokoro` | docs、ADRs、screen specs、static prototypes、protocol contracts | runtime web app、SSE transport、Redis orchestration、agent execution |
| `kokoro-web` | Next.js UI、AGUI rendering、chat shell、SSE client | Redis internals、agent execution |
| `kokoro-session` | session lifecycle、SSE stream、replay / resume、permission decisions | frontend rendering、DeepAgents workflows |
| `kokoro-agent` | planning / execution、tool orchestration、normalized agent events | web UI、SSE client transport |

---

## 关键边界

### `Kokoro` 仓库负责什么

- 锁定产品边界与体验决策
- 维护 `home / chat / canvas` 等 screen spec
- 维护静态原型（设计参考，不是 MVP 代码）
- 维护跨仓协议：事件流、回放、mode、permission envelope

### `Kokoro` 仓库明确不负责什么

- 不写前端运行时状态管理
- 不写真实 SSE server / client
- 不写 Redis stream / pubsub 逻辑
- 不写 DeepAgents 运行与工具调用代码
- 不做跨仓共享源码包

---

## 通信契约

跨仓通信只走协议，不走代码依赖：

- `kokoro-web` ↔ `kokoro-session`：HTTP + SSE（AGUI 事件流）
- `kokoro-session` ↔ `kokoro-agent`：Redis Stream / PubSub + 标准化事件 schema
- `Kokoro` ↔ 其他仓：只通过文档和协议版本对齐，不产生源码 import

---

## 理由

1. **边界更清**：聊天 UI、会话编排、agent 执行是三种不同节奏，拆仓更利于独立演进
2. **协议先行**：AGUI + SSE + Redis replay 是跨层系统，先把协议锁清比先堆代码更稳
3. **避免历史包袱**：不让原型仓慢慢长成半吊子运行时
4. **符合当前阶段**：第一版只做聊天入口壳，但架构不能堵死后面的多用户、replay、thinking / fast

---

## 否决项

| 方案 | 否决理由 |
|---|---|
| Monorepo 多包硬引用 | 会把 docs / prototype、runtime web、session、agent 混脏，边界一开始就坏掉 |
| 在 `Kokoro` 里继续堆运行时代码 | 会让 ADR-007 的“原型 = spec，生产另起真栈”失效 |
| `kokoro-web` 直连 `kokoro-agent` | 前端会被长任务、replay、权限语义拖脏，SSE / Redis 边界消失 |

---

## 后果

- `Kokoro` 成为产品与协议的**源头仓**
- 所有跨仓字段、事件、模式命名先在这里定，再到运行时仓实现
- 原型页面继续用于锁体验，不直接升格为生产代码
- 后续若新增第五仓（如 admin / billing），也必须先补仓边界 ADR
