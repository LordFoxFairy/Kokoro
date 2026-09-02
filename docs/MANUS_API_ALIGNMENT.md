# Kokoro v1 API 设计对齐 Manus

状态：2026-09-02 · Root 设计基线

Manus API 文档是 Kokoro v1 的重点参考。我们参考的是它已经验证过的资源生命周期和异步交互语义，
不是照搬所有路径、字段或内部实现。所有最终契约仍以 Root `contract/` 与各 owner 仓库的 v1 文档为准。

参考文档：

- [Manus Task Lifecycle](https://open.manus.ai/docs/v2/task-lifecycle)
- [Manus task.create](https://open.manus.ai/docs/v2/task.create)

## 1. 直接采用的设计语义

### 1.1 创建是异步资源创建

长任务入口不等待 Agent 完成，而是立即返回稳定的请求和资源标识：

```http
POST /v1/chat/messages
Idempotency-Key: IDEMPOTENCY_KEY
```

```json
{
  "data": {
    "request_id": "REQ_ID",
    "run_id": "RUN_ID",
    "status": "queued"
  },
  "meta": {
    "request_id": "REQ_ID"
  }
}
```

创建接口必须满足：

- 同一个 `Idempotency-Key` 与相同请求体返回同一个 receipt。
- 相同 key 搭配不同请求体返回稳定的冲突错误。
- `request_id` 用于本次请求追踪，`run_id`/`task_id` 用于资源生命周期。
- 业务执行状态不能通过 HTTP 连接是否保持打开来表达。

### 1.2 状态、消息和事件可回放

查询接口返回带游标的稳定快照；事件流断线后从游标继续，不依赖进程内状态：

```http
GET /v1/runs/RUN_ID/events?cursor=CURSOR
```

```json
{
  "data": {
    "items": []
  },
  "meta": {
    "request_id": "REQ_ID",
    "next_cursor": "CURSOR"
  }
}
```

事件的排序、去重和 replay 由 Agent owner 负责；BFF 只做身份校验和 transport projection。

### 1.3 用户确认是显式命令

需要用户确认时返回 `waiting` 状态和待确认动作；确认、拒绝、取消都是可审计的独立命令，
不使用隐式 boolean 改写执行状态：

```http
POST /v1/runs/RUN_ID/confirmations/CONFIRMATION_ID
Idempotency-Key: IDEMPOTENCY_KEY
```

每个确认命令必须携带 tenant、subject、run scope，并可安全重放。

### 1.4 webhook 是通知，不是事实源

异步通知可以帮助外部系统减少轮询，但最终状态必须能通过资源查询和事件回放重新得到。
Webhook 重复投递、乱序和延迟不能改变业务事实；接收方按事件 ID/幂等键去重。

## 2. Kokoro 的 owner 映射

| Manus 语义 | Kokoro owner | BFF 责任 |
|---|---|---|
| task/create receipt | Agent | 认证、幂等、响应投影 |
| task status/messages/events | Agent | scope 校验、cursor 透传 |
| confirmation/action | Agent | 用户身份和授权上下文 |
| task reference/project | BFF + System | 组合业务视图，不复制 owner 事实 |
| model selection | Model | 提交 approved model revision，不接受浏览器自选事实 |
| skill/MCP access | Capability | 只调用已授权 capability |
| credit hold/commit | Billing | 在执行前后按 admission/settlement 协议调用 |
| file/artifact | Storage | 传递 artifact reference，不搬运对象字节 |
| scheduled trigger | Scheduler + BFF/业务 owner | Scheduler 只执行通用 occurrence |

Session 是 Chat/Agent API 的资源概念，不是独立子仓库。Chat 属于 BFF 的内部业务模块；Agent
负责 run、message、event、confirmation 的执行事实。

## 3. v1 统一 wire 规则

- 外部 HTTP 使用 `snake_case`；TypeScript 内部可以使用 `camelCase`。
- 成功响应固定为 `{ data, meta }`，错误响应固定为 `{ error, meta }`。
- `meta.request_id` 必须存在；分页字段统一放在 `meta.next_cursor`，禁止新增第二种兼容 envelope。
- `Idempotency-Key` 只用于会产生事实变化的命令；查询接口使用 cursor，不把随机 offset 暴露为稳定协议。
- tenant、subject、actor、权限来自已验证的服务上下文；浏览器提交的同名字段不能覆盖可信上下文。
- owner 错误要保留稳定 `code`、`retryable` 和可选 `details`；BFF 只做一次错误映射。
- 每个异步资源必须定义状态机、终态、重试语义、取消语义和 replay 语义后再开放路由。

## 4. 当前实现收敛顺序

1. 先修复 System/Billing/Model 的 v1 envelope、可信 tenant context 和错误码一致性。
2. 将 BFF 的 upstream 调用收敛为带超时、响应上限和稳定错误映射的窄 client。
3. 把 Agent admission、dispatch claim、steer command 收敛为可恢复的 durable inbox/outbox。
4. 为 Scheduler 明确 occurrence 注册、lease、retry 和业务 command receipt 协议。
5. 将 Root contract 扩展为所有跨仓 wire surface 的 machine-readable authority。
6. 最后按 vertical slice 拆分 BFF，保持 `main.ts` 只做装配，不制造新的共享业务包。

## 5. 不采用的做法

- 不把 Manus 的外部路径直接当成 Kokoro 的 owner 边界。
- 不让 BFF 读 sibling 数据库或复制业务表。
- 不把内存 Map、空数组或一次性 SSE 当成生产事实/回放协议。
- 不为了兼容旧代码继续增加双字段、双 envelope 或未标记的隐式别名。
- 不把 LiteLLM 变成 Model 的必需依赖；它仍是可选 transport。
