---
status: 🟢 已定
updated: 2026-05-28
locked-by: ADR-009
---

# 仓库边界（Repository Boundaries）

> 这份文档回答：Kokoro 四仓里，每个仓到底该放什么，不该放什么。

---

## 一句话

Kokoro 不是一个大仓库，而是**4 个独立 Git 仓库**通过协议协作：

- `Kokoro`：定义产品、原型和协议
- `kokoro-web`：呈现聊天壳与 AGUI 渲染
- `kokoro-session`：承接会话、SSE、Redis replay / resume、权限决策
- `kokoro-agent`：执行任务并发出标准化事件

---

## 每个仓的职责

### 1. `Kokoro`

**负责：**
- 产品文档
- ADR
- IA / screen spec / mode / permission 设计
- 静态 HTML / CSS 原型
- 跨仓协议文档

**不负责：**
- 前端运行时代码
- 会话 API
- Redis 实现
- Agent 执行逻辑

### 2. `kokoro-web`

**负责：**
- Bun + Next.js 前端
- 聊天入口页 / 对话页 / Canvas 壳
- AGUI / A2UI 渲染器接入
- SSE client、断线恢复 UI、replay 呈现

**不负责：**
- Redis stream 管理
- Agent 工具调用
- 权限最终裁决

### 3. `kokoro-session`

**负责：**
- conversation / session / run 生命周期
- AGUI + SSE 输出
- Redis replay / resume
- mode / permission decision envelope
- 面向 `kokoro-web` 的会话接口

**不负责：**
- 前端 DOM / 组件渲染
- DeepAgents 任务编排细节

### 4. `kokoro-agent`

**负责：**
- Python + DeepAgents
- 规划 / 执行 / 工具编排
- thinking / fast 执行风格下的标准化事件产出
- 面向 `kokoro-session` 的 agent 事件输出

**不负责：**
- 直接维护前端会话状态
- 直接暴露给浏览器的 SSE

---

## 允许的依赖方向

```text
Kokoro docs/protocols
  -> implemented by kokoro-web / kokoro-session / kokoro-agent

kokoro-web
  -> talks to kokoro-session over HTTP/SSE only

kokoro-session
  -> talks to kokoro-agent through Redis-backed event contracts only

kokoro-agent
  -> emits normalized events, never reaches directly into frontend state
```

核心原则：**只有协议向下流动，源码不跨仓流动。**

---

## 禁止的耦合方式

### 禁止 1：跨仓源码 import

**错误例子：**
- `kokoro-web` 直接 import `kokoro-session` 的内部 TypeScript 类型
- `kokoro-session` 直接 import `kokoro-agent` 的 Python 事件定义生成物

**原因：**
这样会把独立仓重新绑回 Monorepo 心智，版本演进会互相拖死。

### 禁止 2：前端直连 agent

**错误例子：**
- 浏览器直接订阅 `kokoro-agent` 输出
- 前端把长任务游标、resume cursor、tool 状态直接绑在 agent 进程语义上

**原因：**
会话恢复、权限中断、replay、审计都属于 `kokoro-session`，不是浏览器该背的复杂度。

### 禁止 3：把原型仓当运行时脚手架

**错误例子：**
- 在 `Kokoro` 里继续堆 Next.js 页面
- 在 `Kokoro` 里写 SSE demo server 并逐渐演化成生产入口

**原因：**
会破坏 [ADR-007](../../decisions/ADR-007-prototype-and-production-stack.md) 的决策：原型是 spec，不是 MVP 代码。

---

## 变更管理规则

### 协议怎么改

1. 先在 `Kokoro` 写文档改动
2. 明确版本、状态、producer / consumer
3. 再分别到 `kokoro-web` / `kokoro-session` / `kokoro-agent` 实现
4. 如果有 breaking change，先补 migration note，再落代码

### 原型怎么影响运行时

- 原型负责锁体验和边界
- 运行时仓负责翻译成真实工程
- 不允许把原型 HTML/CSS 直接复制进生产当最终结构

---

## 当前阶段的最小共识

第一阶段只需要让系统围绕**直接聊天页**收拢：

- `Kokoro`：把 home / chat / canvas 的体验、协议、原型锁清
- `kokoro-web`：先实现聊天入口页壳
- `kokoro-session`：先实现最小 session / SSE / replay 骨架
- `kokoro-agent`：先实现最小 DeepAgents 入口与事件输出骨架

后面的支付、积分、订阅、模型管理、桌面端，不属于这轮主干。
