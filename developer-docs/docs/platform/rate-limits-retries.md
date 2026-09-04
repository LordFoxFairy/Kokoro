# 速率限制与重试

## 当前 contract 事实

当前 v1 canonical OpenAPI **没有发布** numeric quota，也没有 `429` response 或 `Retry-After` header schema。以下重试表是客户端策略建议，不是服务端已经承诺的字段契约；不要把观测到的流量阈值写成公开 quota。

## 客户端策略建议

| 情况 | 建议 |
| --- | --- |
| 安全 read 收到暂时性的 `5xx` | 在整体 timeout 内使用指数 backoff 和 jitter，限制次数。 |
| mutation 的响应不确定 | 用相同 idempotency key 重试完全相同的请求。 |
| 收到 `idempotency_in_progress` | 有界等待后重试原 command。 |
| 收到 `idempotency_conflict` | 停止重试，修正 key 与请求绑定。 |
| 将来 contract 明确发布 `429` | 先按生成 reference 的字段和 header 处理；当前页面不预设 `Retry-After`。 |
| validation、auth 或 not-found 类 `4xx` | 修正请求或权限，不做无限循环。 |

传播原始调用方的取消信号，限制总 elapsed time。不要用不同 idempotency key 并行重试同一个逻辑 command，否则可能重复 admission。若 BFF owner 增加正式 quota、header 或 retry contract，应先更新 artifact、catalog digest 和 generated reference。
