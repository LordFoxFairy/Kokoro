# 恢复等待中的 run

只有当 public projection 显示 pending interaction，并且应用已经收集全部 required decision 后，才发送 resume。

`RunControlRequest` 的 `run.resume` body 要有非空 `decisions` array。decision object 是 interaction-specific：保留 public event 或 session projection 提供的标识，不猜测内部 tool reference。

已验证的 TypeScript 示例会先从长连接中增量读取 `kokoro.interaction.awaiting_approval`，再提交 approval，最后用上一个完整 frame 的 cursor 重连：

<<< ../../examples/typescript/run-lifecycle.ts{ts}

重试同一 decision set 时复用原 idempotency key。改变 decision 就是新的逻辑 command，应生成新 key，并先确认 run 仍接受输入。
