# `kokoro-system` 业务边界设计卡

## 定位

`kokoro-system` 是 site、workspace、runtime manifest、配置发布和策略的事实 owner。每个 site 的
域名和运行时配置属于独立 site 语义，不在 Web 仓库复制一份业务实现。

## 数据与依赖边界

- PostgreSQL 是唯一事实存储，Redis 只缓存 manifest。
- IAM 负责 Tenant、身份和权限 admission；System 在自己的 Site/Host 记录中校验受信 tenant_id + Host。
- System 不拥有 Chat、Project、Billing、Model、Capability、Storage 或 Agent 状态。

## 契约与验收

`/system/runtime-manifest` 与 `/system/*` 使用 snake_case HTTP contract；health/readiness 不等同于
业务授权。必须验证 host→System Site binding、tenant 隔离、BFF service auth、空配置 manifest 和 request id。
