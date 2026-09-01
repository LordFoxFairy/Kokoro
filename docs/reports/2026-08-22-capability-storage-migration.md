# Capability / Storage 子仓迁移记录

日期：2026-08-22

已建立 `kokoro-capability` 与 `kokoro-storage` 的唯一入口、模块目录、MySQL schema、Redis owner inventory、Root contract mirror/provenance、architecture/unit/integration/contract/smoke test。Storage 现已由 `src/main.ts` 装配 MySQL-backed application、S3-compatible ObjectStore 和 Redis fail-closed runtime，并提供 Connect RPC。

存储分层决策修正：Storage v1 不依赖 MongoDB。MySQL 保存 upload/asset/artifact/scan 的结构化状态、scan outcome、report identity 和最终幂等；S3-compatible ObjectStore 保存原始 bytes；Redis 只做运行时门禁。Session/Agent 继续各自拥有 Mongo runtime 文档，不能直接写 Storage collection 或 bucket。

- 本轮只闭环 `kokoro-capability` 与 `kokoro-storage`；Hub、Agent、Session 的实现不在本轮改动范围。它们保留既有兼容期限记录，后续由各自负责人迁移。
- Redis：两个 runtime 在启动时连接并 PING；异常直接 fail closed。
- IAM、Model、Credit：本轮只通过 Root public contract 消费，不改其实现。

验证证据：`kokoro-capability pnpm verify` 通过；`kokoro-storage pnpm verify` 通过（40 tests）；MinIO S3 smoke 通过；MySQL/Redis/MinIO infrastructure smoke 通过；Storage production source 不含 Mongo client/config，Root contract manifest 仍由生成检查守护。

当前范围外迁移项：Hub、Agent、Session 的旧 writer/reader 由各自负责人按既有兼容期限处理。本轮不改变这些子仓库。
