# 可观测性

本文定义全链路标识、结构化日志、tracing、指标、异常治理队列和告警。安全边界见 [09-security-permissions](09-security-permissions.md)，存储边界见 [06-data-storage](06-data-storage.md)。

## 链路标识

每个请求、run 和 job 贯穿统一标识，日志和指标都必须能按这些维度聚合：

```text
requestId        单次入口请求。
sessionId        聊天会话。
runId            一次 agent 执行。
jobId            一次能力任务（长耗时生成等）。
siteId           站点隔离边界。
workspaceId      协作边界。
userId           身份。
provider         模型 provider。
modelBindingId   模型绑定。
creditHoldId     扣费前冻结。
paymentOrderId   支付订单。
```

`eventId` 只用于事件幂等去重，不是排序游标也不是链路标识；排序真源见 [07-service-communication](07-service-communication.md)。

## 结构化日志

```text
格式      JSON，带上述链路标识维度。
脱敏      不输出 provider secret、明文 token、用户完整支付 payload。
prompt    大段 prompt 默认不进普通日志，除非用户授权或已脱敏。
分级      provider raw response 分级存储，不进普通业务日志。
```

## Tracing

按 `requestId` 把一次入口请求的全链路聚合：

```text
web request
site resolve（SiteContext）
auth/user ensure
credit quote/hold
model resolve
provider call
artifact write
credit capture/release
```

run 链路（session 关联 agent）按 `sessionId + runId` 串联，跨 Redis run queue 和 raw event stream。

## 指标

按维度切分（`siteId / capabilityKey / modelLabel / provider / workspaceId / plan / route`）：

```text
质量    run latency、provider latency、job success/failure rate、retry rate。
成本    token/cost usage、provider cost、failed job cost、free quota cost、refund amount。
账务    credit hold leak、credit ledger 不平。
支付    payment event failure。
实时    SSE disconnect、session reconnect。
转化    site conversion（signup / first generation / payment）。
```

## 异常治理队列

运营必须可见、可重试、幂等、有人工操作审计、有用户可解释状态：

```text
payment_webhook_failed
credit_capture_failed
job_succeeded_but_capture_failed
provider_charged_but_job_failed
artifact_upload_failed
sitemap_generation_failed
site_domain_verification_failed
```

每条异常按状态机推进，重试走幂等 key，不靠单进程定时器承载关键状态。

## 告警

```text
P0
  payment event 处理失败。
  credit ledger 不平。
  provider 全部 down。
  session event 持久化失败。
  agent run 大量失败。

P1
  某站点转化异常。
  provider 成本异常。
  free quota 被刷。
```
