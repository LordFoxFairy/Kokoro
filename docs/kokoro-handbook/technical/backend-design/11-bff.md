# `kokoro-bff` 业务边界设计卡

## 定位

`kokoro-bff` 是 Web v1 的业务承接层，不是透明网关。它拥有 Project、ScheduledTask、Chat 的 Web
投影与幂等回执，并通过正式 owner contract 调用 IAM、System、Model、Billing、Capability、Storage、
Scheduler 和 Agent。

## 数据与依赖边界

- BFF 自己的业务事实只写 PostgreSQL，Redis 只做缓存与快速协调。
- BFF 不读取任何子仓库数据库，也不把浏览器的 tenant、host 或 bearer 直接转发给 owner。
- Chat 属于 BFF 的业务模块；Agent 只拥有 Run、执行、事件和恢复事实。
- ScheduledTask 定义属于 BFF；Scheduler 只拥有通用 ScheduleJob、lease、retry、misfire 和 dispatch。

## 契约与验收

外部 HTTP 固定 `{data, meta.request_id}` / `{error, meta.request_id}`，snake_case；owner 调用必须带
可信服务身份、Forwarded host、tenant context、request id 和幂等键。验收覆盖单仓测试、PostgreSQL+
Redis 集成、owner projection、Scheduler 重启恢复和 occurrence replay。
