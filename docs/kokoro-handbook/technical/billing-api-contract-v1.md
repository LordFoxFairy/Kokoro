# Billing API v1 索引

Billing 的唯一机器可读 wire contract 位于：

[`/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/kokoro-billing/contract/openapi/v1/openapi.yaml`](../../../kokoro-billing/contract/openapi/v1/openapi.yaml)

实现说明位于：

[`kokoro-billing/docs/API_CONTRACT.md`](../../../kokoro-billing/docs/API_CONTRACT.md)

本文件不再复制 endpoint、schema 或错误码，避免 Root handbook 与 Billing 子仓库产生第二份契约。
跨仓调用方只能以 owner 的 canonical v1 OpenAPI 和 Root 的跨仓 manifest 为准；旧的无版本 route、
旧的 `site_id` header、旧的 MySQL/Mongo 迁移资料只作为历史审阅材料，不属于运行时契约。
