# Kokoro v1 API 设计对齐 Manus

状态：2026-09-02 · Root 设计基线

Manus API 文档是 Kokoro v1 的重点参考。我们参考的是它已经验证过的资源生命周期和异步交互语义，
不是照搬所有路径、字段或内部实现。所有最终契约仍以 Root `contract/` 与各 owner 仓库的 v1 文档为准。

本页负责解释设计取舍；可供 CI、生成器和联调工具读取的冻结映射位于
[`contract/goal2-cross-repository-contract-v1.json`](../contract/goal2-cross-repository-contract-v1.json)
的 `manus_api_alignment`。两者必须同步：新增或调整异步资源、状态、cursor 或 control 语义时，
先更新 Root machine-readable contract，再更新本页和对应 owner API docs。

参考文档：

- [Manus API Introduction](https://open.manus.ai/docs/v2/introduction)
- [Manus Task Lifecycle](https://open.manus.ai/docs/v2/task-lifecycle)
- [Manus task.create](https://open.manus.ai/docs/v2/task.create)
- [Manus task.list](https://open.manus.ai/docs/v2/task.list)
- [Manus task.listMessages](https://open.manus.ai/docs/v2/task.listMessages)

## 1. 直接采用的设计语义

### 1.1 创建是异步资源创建

长任务入口不等待 Agent 完成，而是立即返回稳定的请求和资源标识：

```http
POST /v1/sessions/{session_id}/messages
Idempotency-Key: IDEMPOTENCY_KEY
```

```json
{
  "data": {
      "request_id": "REQ_ID",
      "run_id": "RUN_ID",
      "user_message_id": "USER_MESSAGE_ID",
      "assistant_message_id": "ASSISTANT_MESSAGE_ID",
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

Manus v2 的公开接口使用顶层 `ok`、`request_id` 和资源标识；Kokoro v1 保留自己的
`{data, meta}` 外部 envelope，以便把 Web、BFF 和 owner 的响应边界固定下来。两者在
异步创建、稳定资源标识、后续读取和幂等重放上对齐；字段外形不是隐式兼容关系。若未来
需要直接接入 Manus v2 客户端，应新增明确的 `manus_compat` facade，不得把第二套 envelope
混入当前 v1 OpenAPI。

### 1.2 状态、消息和事件可回放

查询接口返回带游标的稳定快照；事件流断线后从游标继续，不依赖进程内状态。Kokoro 的
外部 resource payload 将 `next_cursor` 放在 `data` 内，Web 同源适配器解包后仍保持扁平
DTO；外层 `meta` 只承载请求追踪信息：

```http
GET /v1/sessions/{session_id}/events
Last-Event-ID: CURSOR
```

```json
{
  "data": {
    "items": []
  },
  "meta": {
    "request_id": "REQ_ID"
  }
}
```

事件的排序、去重和 replay 由 Agent owner 负责；BFF 只做身份校验和 transport projection。
列表与消息读取必须显式声明 `has_more`/`next_cursor` 或等价的 v1 cursor 语义，并且 cursor
必须绑定 resource、tenant 和过滤条件；不能把一次性 offset 当作长期协议。

### 1.3 用户确认是显式命令

需要用户确认时返回 `waiting` 状态和待确认动作；确认、拒绝、取消都是可审计的独立命令，
不使用隐式 boolean 改写执行状态：

```http
POST /v1/sessions/{session_id}/runs/{run_id}/control
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

## 2.1 与 Manus v2 的接口形态对照

Kokoro v1 的公共业务面按下面的方式对齐 Manus 的成熟资源生命周期。这里的“对齐”意味着
调用者可以用同样的异步思维编排流程，而不是把 Manus 的点号 operation 名称直接复制到每个
owner：

| Manus v2 | Kokoro v1 | 说明 |
|---|---|---|
| `POST /v2/task.create` | `POST /v1/sessions/{session_id}/messages` | 创建一次异步 Agent run，立即返回 `202` 与稳定 receipt；BFF 负责 project/model/skill/artifact 组合。 |
| `GET /v2/task.detail` | `GET /v1/sessions/{session_id}` | 返回可恢复的 session 快照，而不是依赖浏览器内存。 |
| `GET /v2/task.list` | `GET /v1/sessions` | 使用身份范围内的不透明 cursor；cursor 绑定 tenant、project 和排序条件。 |
| `GET /v2/task.listMessages` | `GET /v1/sessions/{session_id}/messages` / `events` | 消息读取与事件流分开；断线后用 `Last-Event-ID`/cursor replay。 |
| `POST /v2/task.sendMessage` | `POST /v1/sessions/{session_id}/messages` | 新消息是新的幂等命令，不复用旧 run 的随机状态。 |
| `POST /v2/task.confirmAction` | `POST /v1/sessions/{session_id}/runs/{run_id}/control` | confirmation 通过显式 `run.resume` + decisions 处理，命令有 durable receipt。 |
| `POST /v2/task.stop` | `run.cancel` control | 取消是可审计的独立命令，不能通过关闭 HTTP 连接表示。 |
| Projects / Skills / Files / Agents | BFF 的 project、Capability、Storage、Agent projection | 资源仍由对应 owner 持有，BFF 只做身份校验和一次 transport projection。 |

Manus `task.create` 的 `message.content` 支持文本、文件等内容部件，且支持 connectors、启用/强制
skills、task references 和 structured output。Kokoro v1 对外先固定自己的 `content`、artifact
reference、approved model revision、capability selector 与 project reference；需要新增内容类型
时，必须在 Root contract 中增加 discriminated union 和 owner 生命周期，不把任意 JSON 直接透传
给 Agent。这样既保持与 Manus 相同的扩展方向，也避免 BFF 形成无类型的万能代理。

### 2.2 调用方必须遵循的闭环

```text
create message (202)
  -> read session / messages / events
  -> running: continue polling or replay from cursor
  -> waiting: inspect typed interaction and submit explicit control
  -> stopped: read final assistant message and artifacts
  -> error: use stable error code and retryability
```

每个阶段都必须可在刷新、超时、重启和重复请求后恢复。Webhook（如果后续启用）只作为状态
通知，不替代 `GET` 快照或消息回放；这与 Manus 的 Task Lifecycle 规则一致。

## 3. v1 统一 wire 规则

- 外部 HTTP 使用 `snake_case`；TypeScript 内部可以使用 `camelCase`。
- 成功响应固定为 `{ data, meta }`，错误响应固定为 `{ error, meta }`。
- `meta.request_id` 必须存在；分页字段统一放在资源 payload 的 `data.next_cursor`，禁止新增
  `meta.next_cursor` 或第二种兼容 envelope。Web 解包后的扁平 DTO 同样使用 `next_cursor`。
- `Idempotency-Key` 只用于会产生事实变化的命令；查询接口使用 cursor，不把随机 offset 暴露为稳定协议。
- mutation 在触发副作用前先取得 pending claim；同一命令并发到达时返回稳定的
  `idempotency_in_progress`，不重复创建 Manus-style task/run。完成后重放原 receipt，传输/上游
  `5xx` 释放 claim 允许重试。
- tenant、subject、actor、权限来自已验证的服务上下文；浏览器提交的同名字段不能覆盖可信上下文。
- owner 错误要保留稳定 `code`、`retryable` 和可选 `details`；BFF 只做一次错误映射。
- 每个异步资源必须定义状态机、终态、重试语义、取消语义和 replay 语义后再开放路由。

## 4. 当前实现收敛顺序

1. 保持 System/Billing/Model 的 v1 envelope、可信 tenant context 和错误码一致性，并由各仓 parity test 锁定。
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

## 6. API 评审门槛

以后新增或修改 v1 API，先在 Root contract 和 owner API docs 中回答以下问题，再写 handler：

1. 资源事实 owner 是谁，BFF 是否只是 projection？
2. 创建是否异步，返回的 `request_id`、资源 ID 和状态是否稳定？
3. 列表/消息/事件如何分页、排序、断点回放和去重？
4. mutation 的 `Idempotency-Key` 如何绑定请求体、tenant、资源和状态机？
5. waiting、cancel、retry、error、terminal 各状态的允许动作是什么？
6. artifact、skill、connector、model 等引用是否是已批准的 typed reference，而不是客户端直接
   指定 provider 或内部地址？
7. 成功/错误 envelope、snake_case、`meta.request_id`、错误码和 `retryable` 是否与 v1 一致？
8. Web、BFF、owner、重启恢复和重复投递是否都有 contract fixture？

未通过上述门槛的接口不进入公开 v1 surface。这样可以保持“体验和生命周期接近 Manus”，同时
让 Kokoro 的多仓 owner 边界、权限和数据事实保持清晰。
