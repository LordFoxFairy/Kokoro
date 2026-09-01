# kokoro-storage 设计卡

状态：Capability × Storage v1 正式边界，2026-08-23。

## 定位

`kokoro-storage` 是 Blob、Upload、Asset、Scan、Artifact 生命周期 owner。它不是数据库 wrapper，也不是某个云厂商 SDK 的业务层。

## owns

```text
upload admission/completion
object key allocation
blob metadata
asset identity/visibility/scan state
artifact draft/final state
command receipt/final idempotency
short-lived upload/download reference
```

## doesNotOwn

```text
IAM identity and authorization master data
Capability Skill/MCP policy and installation
Session snapshot/event
Agent checkpoint/memory/execution event
Model/Credit/Payment
MongoDB-owned Session/Agent documents and runtime state
```

## 存储分层

```text
MySQL       upload/blob/asset/scan/artifact/command receipt final truth
Storage v1  no MongoDB dependency; report identity is `storage_scan.report_ref`
Redis       runtime admission/liveness gate; unavailable => fail closed
ObjectStore original bytes
```

原始 bytes 不进入 MySQL；scanner 结果与 report identity 在 MySQL 事务中和 asset 一起提交。Storage v1 不连接 MongoDB。

## ObjectStore

生产与默认集成 profile 使用 S3-compatible adapter：

```text
AWS S3   endpoint unset, usually virtual-hosted style
MinIO    local endpoint, usually forcePathStyle=true
Ceph RGW endpoint supplied by deployment
```

LocalObjectStore 仅显式 no-infra/unit profile。业务层不导入 provider SDK、不生成 bucket/key。v1 已公开 presigned upload/download 与单对象 PUT；multipart 需后续 Root contract 增量发布。

## 状态机

```text
Upload: pending -> completed
Scan: pending -> clean | infected | unknown
Artifact: draft -> final
```

只有 clean asset 可以返回 package/download reference；final artifact 不可修改 digest、asset 或状态。ObjectStore 有对象不等于业务上传完成。

当前完整生命周期 v1 已包含 upload/status/abort、asset、scan、artifact draft/final 和 download reference。multipart、删除策略、provider lifecycle 与批量查询明确是后续增量，不属于当前 v1。

## 证据

- Root：`contract/proto/kokoro/storage/v1/storage.proto`
- Schema：`kokoro-storage/database/schema.sql`
- API：`kokoro-storage/docs/API_CONTRACT.md`
- Owner inventory：`kokoro-storage/docs/SCHEMA_OWNER_INVENTORY.md`
- generated mirror/provenance：`kokoro-storage/scripts/check-contract.ts`
- runtime entry：`kokoro-storage/src/main.ts`

## 100 分证据

- MySQL/Redis/ObjectStore owner 矩阵与 schema 一致，Storage v1 不依赖 MongoDB。
- MinIO 通过 S3-compatible adapter 验证；LocalObjectStore 仅 no-infra。
- upload/scan/artifact 状态机、幂等和 clean gate 有 contract/unit/integration tests。
- Redis、MySQL、ObjectStore 依赖故障均按 fail-closed/dependency-unavailable 处理。
- RPC adapter 不直接写数据库，不向 caller 暴露 provider SDK、bucket 或 Redis key。
