# Kokoro 后端整体闭环与 Platform 原子切换设计

状态：已批准设计草案，2026-09-20。本文记录 Root、`kokoro-app` 与八个后端 owner 的目标边界；Mori 等其他前端不在本轮范围。实现前必须再形成逐切片计划。

## 1. 目标与当前裁决

本轮目标是把现存子仓从“各自具备部分能力”收敛为一套可以从 `kokoro-app` 走到所有 owner、由机器契约和真实数据门禁证明的组合系统。

确定事项：

1. 只处理 `apps/kokoro-app`；`apps/kokoro-mori` 与其他前端不参与本轮业务改造。
2. Browser 只经 Web same-origin adapter 访问 BFF；Web 不直连内部 owner。
3. BFF 是唯一 public Product API 与 durable AG-UI projection owner。
4. 同步内部协议按语义选择：Platform/Storage 使用 ConnectRPC + Proto；IAM/System/Agent/Scheduler/Billing 保留 owner HTTP/OpenAPI。
5. 异步调度、outbox 投递、支付 webhook 使用版本化 HTTP event protocol，不用同步 RPC 冒充 durable delivery。
6. Billing 最后处理；在 Billing runtime 与唯一首发契约对齐前，不扩大新 consumer。
7. 本地和 CI 共用一个 PostgreSQL 实例、一个应用角色与一套凭据；每个 owner 仍使用独立 database 或 schema。独立 production role、GRANT/REVOKE、mTLS 和 NetworkPolicy 属于部署阶段，不是本轮闭环门禁。
8. 每个事实只有一个 owner 和 writer；服务只通过版本化 contract 访问其他 owner，不共享 ORM schema、SQL、业务 DTO 或源码。

### 1.1 聊天与文件默认可见性（2026-09-22 用户确认）

聊天与文件默认个人私有，只有显式分享/授权才开放。同一 tenant 是必要隔离范围，不是成员互相访问所有数据的授权。

- Conversation/Message、历史列表/详情/搜索、AG-UI replay/live、附件与产物均执行 tenant + 资源 owner/显式授权检查；隐藏 UI 不替代服务端检查。
- 放进 Project 不自动变成整个 tenant 可见；只有该 Project 的显式有效访问授权才可授予相应资源访问，具体继承范围在 owner 契约中固定。
- 分享只授予声明的资源与动作；只读分享不授予继续聊天、取消 Run、审批工具或读取未分享文件的权利。
- 取消、HITL 审批与恢复必须绑定可信 actor、Run/thread 及对应操作权限；不得只凭 session ID、cursor、share token 或 tenant 相同放行。
- 验收必须有“同 tenant 不同用户”和“跨 tenant”两组负例，覆盖列表到事件/附件下载，且不泄漏不可见资源的存在性。
- 当前实现可能仅有 tenant predicate；本决定是待落实的完成标准，不把它写成当前已完成能力。

## 2. `kokoro-capability` 当前状态

当前尚未正式成为 Platform：

- GitHub remote 仍是 `LordFoxFairy/kokoro-capability`；
- Root submodule 仍是 `apps/kokoro-capability`；
- npm package 仍是 `@kokoro/capability`；
- service/log/env 仍使用 `kokoro-capability`、`KOKORO_CAPABILITY_*`；
- canonical Proto 仍是 `kokoro.capability.v1`；
- BFF、Agent 和 Storage 仍含 Capability 名称或旧消费路径；
- `kokoro.platform.v1` 当前只存在于目标设计和 execution-operation artifacts，尚不是唯一运行契约。

因此当前事实必须继续写成 Capability；只有第 8 节的原子 cutover 全部完成并验证后，才可在 Root 拓扑和状态文档中写成正式 Platform。

## 3. 目标运行拓扑

```text
Browser
  -> kokoro-app same-origin adapter
    -> kokoro-bff HTTP/OpenAPI + AG-UI/SSE
      -> kokoro-iam HTTP/OpenAPI generated client
      -> kokoro-system HTTP/OpenAPI generated client
      -> kokoro-platform ConnectRPC/Proto generated client
      -> kokoro-storage ConnectRPC/Proto generated client
      -> kokoro-agent HTTP/OpenAPI generated client
      -> kokoro-scheduler HTTP/OpenAPI generated client
      -> kokoro-billing HTTP/OpenAPI generated client

kokoro-agent
  -> kokoro-system HTTP/OpenAPI generated client
  -> kokoro-platform ConnectRPC/Proto generated client
  -> kokoro-storage ConnectRPC/Proto generated client

kokoro-platform
  -> kokoro-storage ConnectRPC/Proto generated client
  -> kokoro-iam workload/execution authorization HTTP client

kokoro-scheduler
  -> versioned HTTP webhook -> BFF or Agent
```

AG-UI 只存在于 Web/BFF 网络边界。Agent 发布 execution event/page/control contract，BFF 持久化投影、cursor、replay 和浏览器事件。

## 4. 协议矩阵

| Caller → Owner | 唯一目标协议 | 契约 owner | 说明 |
| --- | --- | --- | --- |
| Browser → Web | same-origin HTTP | Web | Cookie、CSRF、浏览器状态。 |
| Web → BFF | HTTP/OpenAPI；AG-UI/SSE | BFF | Public Product API 与 durable event projection。 |
| BFF → IAM | HTTP/OpenAPI generated client | IAM | OAuth/OIDC/Better Auth 保持原生 HTTP 语义。 |
| BFF/Agent → System | HTTP/OpenAPI generated client | System | 不因统一偏好重写当前稳定 HTTP。 |
| BFF/Agent → Platform | ConnectRPC/Proto | Platform | Skills/MCP typed command/query。 |
| BFF/Agent/Platform → Storage | ConnectRPC/Proto v2 | Storage | Asset、Artifact、Upload、Package reference。 |
| BFF → Agent | HTTP/OpenAPI generated client | Agent | Run dispatch/control 与可恢复 event paging。 |
| BFF → Scheduler | HTTP/OpenAPI generated client | Scheduler | Schedule command/query。 |
| Scheduler → BFF/Agent | HTTP event protocol | Scheduler | Durable retry、receipt、duplicate delivery。 |
| BFF → Billing | HTTP/OpenAPI generated client | Billing | Checkout、payment resource 与 provider webhook。 |

同一个 operation 只能存在一个 canonical transport。短期迁移测试可以同时装配 old/new client，但 release commit 不保留双读、双写、fallback、alias 或两个公开 contract。

## 5. Contract 统一规则

### 5.1 Owner 事实源

- BFF public API：design-first OpenAPI。
- IAM/System/Agent/Scheduler/Billing：各 owner 的唯一 OpenAPI。
- Platform/Storage：各 owner 的唯一 Proto。
- Root 只维护 catalog、组合 gitlink、consumer pin 和兼容性验证，不复制可编辑契约。

### 5.2 生成链

Proto owner 必须固定：

```text
buf format check
buf lint
buf build
buf breaking --against approved baseline
buf generate
生成物 drift check
```

HTTP owner 必须固定：

```text
OpenAPI parse/lint
owner metadata check
breaking baseline
client generation
生成物 drift check
runtime parity test
```

Consumer pin 至少包含：

```text
owner repository
owner commit
contract version
contract digest
code generator version
runtime package version
```

Generated 类型只存在于 client/handler adapter；业务模块使用本仓内部对象。错误在 owner transport 边界映射为稳定 wire code，消费者再映射为本地错误。

### 5.3 通用调用上下文

每条内部调用根据语义携带并验证：

- caller service identity；
- request ID 与 trace context；
- tenant、actor、subject 的受信引用；
- permission 或 authorization decision reference；
- command idempotency key/digest；
- deadline 与取消；
- contract version/digest。

只有契约明确声明为安全重试的 unary/query 才自动有限重试。写操作依赖 owner PostgreSQL receipt/outbox，而不是依赖 RPC transport 猜测幂等性。

## 6. SQL 与数据闭环

### 6.1 开发与 CI 数据库模型

- 共用一个 PostgreSQL 实例；
- 共用一个应用 role/credential；
- 每个 owner 使用独立 database 或 schema 与独立连接 URL；
- Root 测试为每个 worker 分配独立临时 database/schema 名；
- 不以数据库 role 隔离作为当前验收项。

代码和测试仍必须阻止：

- 跨 owner SQL/JOIN；
- 引用别仓表名；
- 共享 Prisma/ORM model；
- 共享 canonical schema；
- BFF 读取 owner 数据库；
- Agent 复制 Platform/Storage/IAM 业务事实。

### 6.2 每个数据 owner 的完成门

每仓必须有且只有一个 canonical schema，并证明：

1. fresh install 到空数据库成功；
2. catalog 与 canonical schema 完整一致，包括 table、column、type、nullability、default、constraint、index；
3. 0 物理跨 owner FK；
4. tenant-owned query/write 均带 tenant predicate；
5. command receipt 包含 tenant、operation、key、request digest、state、lease/fence、result/error、created/updated/expiry；
6. 业务写、receipt 和 outbox 在同一事务；
7. 网络/provider 调用不在数据库事务内；
8. outbox claim、retry、duplicate delivery、crash/restart 和 commit-unknown 有真实测试；
9. 每类事实声明 retention、GC、legal/audit exception；
10. Redis 丢失不丢 durable truth。

SQL-first owner 使用 `database/schema.sql`；ORM-first owner 使用批准的唯一 `prisma/schema.prisma`。生成 SQL/client 只读，不成为第二事实源。

## 7. 必须偿还的现存技术债务

### 7.1 当前硬断链

- BFF 使用 Capability 已废止 `/bff/*` 路径，owner 实际 projection 为 `/v1/*`；
- BFF 使用 Storage 已删除 `/internal/bff/library`；
- Platform/Capability 固定 Storage Proto v1，而 Storage owner 已是 v2；
- BFF 使用 Scheduler `jobs`，owner contract 使用 `schedules`；
- Scheduler callback header 与 occurrence 时间格式不一致；
- Web 仍直接调用 IAM；
- BFF 尚无完整 IAM admission。

这些边界按 owner-contract-first 顺序逐条原子替换，并在同一切片删除旧调用。

### 7.2 数据 owner 冲突

Conversation、Message、Project、Share、ScheduledTask 属于 BFF。Agent 只拥有 Run、Checkpoint、Lease、Tool Journal、execution event、HITL/Approval 和 Evidence。

Agent 当前 Chat session/message/event/memory 表必须逐项分类：

- execution source/event/evidence 留在 Agent；
- Product Conversation/Message 投影写入 BFF；
- BFF reconciliation 与 replay 稳定后删除 Agent 的重复产品事实；
- 不保留双 owner 或长期同步副本。

### 7.3 结构债务

本轮必须处理：

- BFF 手写 owner URL/JSON client；
- Web 历史未使用 Proto；
- IAM admission 与 Platform workload authorization 缺口；
- BFF receipt/fallback/retention；
- BFF、Agent、IAM exact schema drift；
- Storage consumer 未激活；
- Root 跨仓 compatibility/integration runner 缺失；
- `kokoro-capability` 与目标 Platform 的双重身份。

下列工作后置到部署/规模化阶段：

- 每 owner 独立数据库 role；
- service mesh、数据库 mTLS、NetworkPolicy；
- 私有 BSR；
- 多区域与自动扩缩容；
- migration 历史链；
- 全量灾备演练。

## 8. Capability → Platform 原子切换

### 8.1 最终身份

切换完成后唯一身份为：

```text
GitHub repository: LordFoxFairy/kokoro-platform
Root path:         apps/kokoro-platform
npm package:       @kokoro/platform
service:           kokoro-platform
environment:       KOKORO_PLATFORM_*
Proto package:     kokoro.platform.v1
business domains:  skills, mcp
```

`capability` 仍可作为普通业务词汇描述 Agent capability，但不再作为仓库、服务、Proto package、环境变量前缀或 owner 名。

Storage 的 `capability_package` 是资产用途枚举，表达“能力包”而不是旧服务身份；只有语义确实是该资产类型时保留。

### 8.2 Cutover 顺序

1. 冻结 Capability 当前 descriptor、数据库 schema、Redis namespace、消费者和运行配置清单。
2. 完成 IAM execution/workload authorization contract。
3. 在当前仓建立唯一 `kokoro.platform.v1` Proto、生成物和 runtime handler。
4. 将内部 package/service/log/env/config 命名切换为 Platform。
5. 将 Storage consumer 升级为 owner v2 artifact。
6. 更新 Agent 与 BFF generated client/facade，并验证所有 operation。
7. 更新数据库名、Redis namespace、service identity 与 deployment manifest。
8. 删除 `kokoro.capability.v1` Proto、旧生成物、旧 HTTP projection、旧 token/env 和旧测试 fixture。
9. 运行 owner 完整门禁和跨仓 integration/smoke。
10. 将 GitHub remote 改名为 `kokoro-platform`。
11. Root 将 submodule 从 `apps/kokoro-capability` 原子替换为 `apps/kokoro-platform`，更新 `.gitmodules`、治理 profile、拓扑测试和文档。
12. 验证 fresh recursive clone、remote SHA、main-only、clean worktree 后推送 Root。

切换失败时回滚整个组合 gitlink；不通过兼容 alias 让旧新身份同时运行。

## 9. 分阶段闭环顺序

### Wave 0：权威设计与自动门禁

- 同步 Root AGENTS、架构标准、SQL 标准和 owner 状态；
- 固定调用矩阵、contract owner、SQL owner 与 consumer inventory；
- 建立 contract digest、runtime parity 和 cross-repo compatibility runner；
- 修复 Capability、Storage、Scheduler 的当前硬断链。

### Wave 1：IAM → BFF → Web

- 完成 IAM execution/workload authorization；
- BFF 接入 IAM generated client 和 admission；
- Web 的 IAM 调用收回 same-origin BFF adapter；
- 删除 Web 历史 Proto、直连配置与重复身份解析；
- 验证 session、tenant、actor、subject、permission、CSRF 和越权失败。

### Wave 2：Storage v2

- 固定 Storage Proto v2 与 consumer artifact；
- 切 Platform、Agent、BFF；
- 完成 scope/action authorization、artifact receipt、expiry/GC；
- 验证真实 PostgreSQL、ObjectStore、scan provider；
- 删除 v1 snapshot 与旧 HTTP 调用。

### Wave 3：Platform 原子切换

按第 8 节完成 runtime、consumer、remote 与 Root submodule 一次性切换。

### Wave 4：BFF、Agent、Scheduler

- BFF 完成 tenant-aware receipt、transactional outbox、AG-UI、retention，删除 Map fallback；
- BFF/Agent 清除 Chat owner 重叠；
- Agent 完成 execution lifecycle、exact drift、retention、worker recovery；
- Scheduler 对齐 schedule/callback contract，完成 occurrence、retry、retention、metrics；
- 三仓完成真实 PostgreSQL/Redis restart/duplicate/concurrency 测试。

### Wave 5：System

- 保留 HTTP/OpenAPI；
- BFF/Agent 改用固定 generated client；
- 接 IAM caller identity；
- 完成 TypeScript、contract、schema 和模块隔离门禁。

### Wave 6：Billing

Billing 最后执行：

- 选择唯一首发 `/v1` 契约，消除当前 v1/v2 双态；
- 完成 Prisma writer、worker、provider adapter 和 reconciliation；
- 修复现有 schema/runtime integration failures；
- provider 网络调用保持事务外，并对 unknown outcome 恢复；
- 完成 payment、subscription、refund、credit、ledger、metering、outbox、retention；
- 切换 BFF generated client，删除旧 runtime/contract；
- 使用 provider sandbox 验证重复 webhook、退款、结算和对账。

### Wave 7：Root 组合验收

固定所有 gitlink 与 artifact digest，执行：

```text
kokoro-app -> BFF -> IAM/System/Platform/Storage/Agent/Scheduler/Billing
```

覆盖 happy path、权限失败、跨 tenant、重复请求、并发、timeout、取消、有限重试、outbox 重投、worker crash/restart、AG-UI reconnect/replay、ObjectStore/provider sandbox、backup/restore 和 graceful shutdown。

## 10. 每仓完成定义

一个 owner 只有同时满足下列条件才标记闭环：

- `TECHNICAL_DESIGN`、`API_CONTRACT`、`DATA_MODEL` 与代码一致；
- 唯一 canonical contract/schema；
- 所有 consumer 固定 artifact；
- 旧路径、旧 DTO、旧 schema、alias、fallback 和双轨实现已删除；
- lint、format、typecheck、unit、integration、contract、architecture、build 全绿；
- fresh schema、catalog drift、真实基础设施 smoke 全绿；
- timeout、取消、幂等、并发、恢复、tenant 和权限测试全绿；
- 当前 commit、命令、测试数量、风险和运行证据写入 `docs/CURRENT.md`；
- owner commit 先推送，Root 再提升 gitlink。

“目录已整理”“契约文件存在”或静态 Root audit 通过都不等于闭环。

## 11. Root 最终完成定义

Root 完成必须证明：

1. Root 与全部 submodule 只有 `main`、工作树 clean、`HEAD == origin/main`；
2. `.gitmodules` 使用远端仓名，正式路径为 `apps/kokoro-platform`；
3. 每条调用边都有唯一 owner contract、consumer pin 和组合测试；
4. 每个数据 owner 的 fresh schema、exact drift、事务、outbox、retention 已验证；
5. Web 不直连内部 owner；BFF 不读 owner 数据库；Agent 不复制 Platform/Storage 事实；
6. Billing 位于最后一波并完成 sandbox/reconciliation；
7. Root contract/integration/e2e/smoke runner 不清理共享基础设施，使用独立临时 database/schema 与 namespace；
8. release manifest 固定 Root commit、子仓 SHA、contract digest、SDK version、image digest 和验证结果。

只有以上全部满足，才使用“整体闭环”表述。
