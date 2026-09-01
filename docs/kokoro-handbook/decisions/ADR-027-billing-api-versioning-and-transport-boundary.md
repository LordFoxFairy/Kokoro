# ADR-027：Billing API 版本与传输边界

- 状态：accepted
- 日期：2026-08-29

## Context

Manus API v2 使用显式版本前缀和 operation-style 方法，例如 `/v2/task.create`；Google API 的资源化设计强调资源名、标准方法和
稳定的资源状态；Stripe 与云厂商实践则把 API 版本、幂等请求、RequestId、Webhook 事件结构和重试语义作为独立契约治理。

Kokoro 同时有 User、Admin、Internal、Provider Webhook 四个 API surface。若把版本号放进所有 domain、repository、SQL 表，或者让
`/billing` 与 `/v1/billing` 并存，会造成两套行为、权限和账务语义。若完全依赖 Header 版本，又不利于网关路由、OpenAPI 发布和 SDK
生成。因此需要固定版本所在边界。

## Decision

### 1. 首发版本

未上线系统的第一个正式 HTTP contract 固定为 `v1`，所有业务路由使用：

```text
/v1/commerce/...
/v1/billing/...
/v1/admin/...
/v1/internal/...
/v1/webhooks/...
```

不注册无版本业务路由，不创建空 `v2`，不做 v1/v2 双写或兼容适配。

### 2. 版本只属于 transport boundary

```text
contract/openapi/v1/
src/interfaces/http/v1/
src/interfaces/admin/v1/
```

以下目录不带 API 版本：

```text
src/application/
src/domain/
src/ports/
src/adapters/
database/
```

v1 adapter 将 DTO、认证上下文、错误码和 URL 转换为稳定的 application command/query。v2 若未来出现，只能先复用相同
application/domain 能力；只有字段或语义确实破坏兼容时才新增 v2 adapter 和独立 OpenAPI 文档。

### 3. API 风格取舍

- 资源读写采用资源导向 REST：`GET /v1/commerce/orders/{orderId}`、`POST /v1/commerce/orders`；
- 不把 Manus 的 `task.create` 点号 operation 名称复制到 Kokoro 的 URL；需要原子领域动作时使用明确的 action 子资源，例如
  `/v1/internal/billing/admissions/{admissionId}/capture`；
- 异步执行使用资源状态、`operationId`/`executionId`、cursor 和 webhook，不用 HTTP 请求阻塞等待 provider；
- 所有 mutation 使用 `Idempotency-Key`；首发 HTTP JSON 使用 `snake_case`，成功响应为 `{data, meta.request_id}`，错误响应为 `{error.code, error.message, error.request_id, error.retryable, error.details}`；不额外引入 Manus 的 `ok` 字段，HTTP status 与 `data/error` 结构已表达结果；限流返回 `429` 和 `Retry-After`；
- webhook 按版本固定 payload schema，先验签入 inbox，再异步处理；事件保存其产生时的 schema version，不因以后 API 升级而重写历史事件；
- PostgreSQL 事实、状态机、ledger、outbox 和 Redis key 不按 HTTP 版本复制。

## Consequences

- 网关、OpenAPI、SDK、文档和测试可以按 `v1` 明确发布；
- 领域模型不会出现 `OrderV1`、`OrderV2`、`CreditRepositoryV2` 等版本分叉；
- 未来 v2 需要明确 breaking-change 清单和迁移期，但当前 clean-build 不提前承担兼容成本；
- 现有无版本探索路由属于非目标代码，重建目标实现时直接按 `/v1` 注册。

## References

- [Manus API v2 Introduction](https://open.manus.ai/docs/v2/)
- [Manus Task Lifecycle](https://open.manus.ai/docs/v2/task-lifecycle)
- [Google AIP-121 Resource-oriented design](https://google.aip.dev/121)
- [Google AIP-133 Create](https://google.aip.dev/133)
- [Stripe Idempotent requests](https://docs.stripe.com/api/idempotent_requests)
- [Stripe API versioning](https://docs.stripe.com/api/versioning)
