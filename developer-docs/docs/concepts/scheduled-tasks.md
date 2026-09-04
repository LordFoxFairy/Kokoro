# 定时任务

Scheduled task 是描述重复工作的 BFF 产品资源。public model 当前包含 title、prompt、daily/weekly frequency、local time、IANA timezone、next run instant、可选 expiry、approval behavior、enabled flag 和 status。

## 时间模型

`time` 与 `timezone` 保存用户想要的本地调度意图；`next_run_at` 是客户端可以展示和监控的 RFC 3339 UTC occurrence。不要把 IANA timezone 替换为固定 UTC offset，因为夏令时会改变实际 occurrence。

## Commands

创建、更新、删除和 retry operation 的 canonical metadata 标为 `Idempotency-Key` `required`。project-scoped create 从 URL path 取得 project identity，body 不应尝试覆盖它。

public BFF scheduled resource 与内部 Scheduler 的 lease、occurrence、retry、dispatch protocol 是不同边界。门户不发布后者的数据库结构或内部 message。
