# 请求 ID（Request ID）

JSON envelope 的 `meta.request_id` 用于关联一次请求。event stream 没有 JSON body，因此 `GET /v1/sessions/{id}/events` 的 `200` response 在 canonical contract 中通过 `X-Kokoro-Request-Id` header 暴露 correlation ID。

当前 public contract 没有把 request correlation ID 定义成调用方输入字段。客户端应接受服务端返回的值，不要在门户之外发明同名 request header 或把它当作幂等 key。

记录 operationId、HTTP status、latency 和返回的 request ID，便于排查；凭据、完整用户消息、tool 参数和 provider payload 默认脱敏。request ID 只是诊断标识，不是 authorization credential、resource ID 或 AG-UI replay cursor。

字段名、header 出现在哪个 operation、状态码和约束都以[生成 reference](/reference/v1/)为准。
