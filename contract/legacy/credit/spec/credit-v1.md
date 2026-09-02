# Credit v1 contract boundary

状态：`kokoro-billing` 内部 Credit bounded context 的 v1 契约。

Root-owned source：`contract/legacy/credit/proto/kokoro/credit/v1/credit.proto`。

Credit contract 独立于 Slice-A descriptor，使用 `contract/legacy/credit/buf.credit.yaml` 构建和校验；Slice-A 的
`contract/buf.yaml` 明确排除 Credit module，避免跨生命周期把 Credit 误当作 Slice-A 内部协议。

契约声明账户 ensure、grant、spend、refund、quote、pricing rule、usage record、原子 `SettleUsage` 与 `CreateHold`、`CaptureHold`、`ReleaseHold`。金额使用十进制字符串 `micros`；每个副作用 command 携带 `command_id`、`request_id` 和 `idempotency_key`。服务端必须保证同一幂等 key 只产生一次状态转移；`SettleUsage` 的正向路径必须在一个 PostgreSQL 事务内完成 capture、ledger 和 usage。

Root consumer closure：`contract/legacy/credit/consumers.json`。HTTP adapter 与未来 RPC adapter 复用同一 command model；数据库 writer 只存在于 `kokoro-billing` 内部 Credit bounded context。
