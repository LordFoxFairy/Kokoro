# Tenant、Site 与跨仓请求上下文规范

状态：当前有效，全局规范，2026-09-02。

本文是 Root 对 `tenant_id`、`site_id`、Host 和跨仓上下文的唯一解释。各正式子仓库的 `API_CONTRACT`/API docs
必须与本文一致；历史文档中的 `iam_site`、`site_site`、`iam_tenant_site_binding`、双隔离键和 IAM Host lookup
均不再执行。

## 1. 四个概念

| 概念 | owner | 含义 | 跨仓可否作为隔离键 |
|---|---|---|---|
| `tenant_id` | IAM 产生/管理；各业务仓使用 | 租户的 opaque external identifier，所有业务数据的唯一隔离键 | 是，唯一隔离键 |
| `site_id` | System | System 内部 Site 资源的 UUID，用于 Site、Workspace、Policy 的本仓关系 | 否 |
| `host` | System | 请求进入的 Host/Forwarded host，用于解析本仓 Site | 否 |
| `organization_id` | IAM | Tenant 内组织、成员与权限的作用域 | 否 |

`site_id` 从不替代 `tenant_id`，也不进入 Billing、Model、Capability、Storage、Scheduler 的跨仓数据主键。
业务 payload 不重复接收客户端提供的 `tenant_id`；它只能来自受信服务上下文。

## 2. 所有权矩阵

| 仓库 | 负责 | 不负责 |
|---|---|---|
| `kokoro-iam` | Tenant、User/Principal、Identity、Organization、Membership、Role/Permission、Authentication、OAuth、Passkey、Audit、ExecutionIdentity | Site、Host、Runtime Manifest、业务配置 |
| `kokoro-system` | Site、Site Host/Domain binding、Workspace、SitePolicy、Product/App configuration、Runtime Manifest、release | IAM 登录凭据、权限事实、Model Provider 调用 |
| `kokoro-model` | Model Catalog、Provider、Availability、公开模型能力契约 | 实际模型 client 与调用执行 |
| `kokoro-billing` | Payment、Subscription、Checkout、Refund、Credit、Hold/Commit/Refund、Ledger | Scheduler 通用调度、模型和能力事实 |
| `kokoro-capability` | Skill、MCP/Connector、Catalog、安装、启停、版本、权限契约 | Agent 执行实现、BFF 复制能力实现 |
| `kokoro-storage` | File、Upload、Artifact、Object、Download、生命周期 | 其他业务数据库读取 |
| `kokoro-scheduler` | 通用 ScheduleJob、Trigger、Lease、Concurrency、Retry/Backoff、Pause/Resume、Misfire、ExecutionReceipt | Billing/Credit 业务逻辑，业务数据库连接 |

Connector 在 Kokoro 中是 MCP 的接入/管理表达，不另建 Connector 业务仓库；MCP 的 Catalog、安装和权限由
`kokoro-capability` 管理。Agent 只消费公开 capability/model contract，负责执行。

## 3. Site 解析与请求流

```text
Browser Host
  → BFF 取得原始 Host，并完成会话/IAM admission
  → BFF 生成受信 tenant_id + ExecutionIdentity/permissions
  → System 用自己的 Site Host 表校验 tenant_id + host
  → BFF/System 将 TenantRequestContext 传给业务 owner
  → 各 owner 只按 tenant_id 隔离自己的数据
```

System 可以保存 `system_site(site_id, tenant_id, ...)` 与 `system_site_domain(site_id, host, ...)`；这是 System
内部关系，不向 IAM 复制。IAM 数据库不读取 System，System 数据库不读取 IAM；跨仓只走 API/RPC/事件契约，不建跨仓关系约束。

Host 不产生租户身份，客户端 header 也不产生租户身份。Host 是 System 的站点选择输入，最终必须与受信
`tenant_id` 的本仓 Site 绑定一致；未知、禁用或不一致时在业务数据读取前失败。

## 4. 标准上下文

```text
TenantRequestContext {
  tenant_id: string
  actor_id: string | null
  organization_id: string | null
  permissions: string[]
  request_id: string
}
```

服务间使用标准 `Forwarded` 和受信服务上下文；不使用 `X-Domain` 作为身份依据，不允许业务仓从 query/body
选择隔离键。所有响应使用统一 envelope 和 `request_id`；写操作使用 `Idempotency-Key`；列表使用 cursor pagination。

## 5. 设计不变量

1. 只有 IAM 产生和证明身份/权限，System 不保存登录凭据。
2. 只有 System 拥有 Site/Host binding，IAM 不创建 Site 表或 Site binding 表。
3. 其他业务仓只接收可信 `tenant_id`，不接收或推导 `site_id` 作为隔离轴。
4. Billing 内部包含 Credit；不拆出独立 Credit 业务仓库。
5. Scheduler 是 Go 通用基础设施，不连接 Billing/Credit 或其他业务数据库。
6. 任何新增类似 Skills/MCP 的能力先进入 Capability module；只有独立数据 owner、发布节奏、故障域和 API 契约
   同时成立时才评估新仓库。
7. Root `contract/` 是跨仓 wire authority；每个子仓 API docs 是本仓实现和测试 authority。
