# `kokoro-scheduler` 业务边界设计卡

## 定位

`kokoro-scheduler` 是 Go 编写的通用调度执行器，负责 ScheduleJob 注册、时间触发、lease、retry、
misfire 和带 occurrence 的内部 dispatch。

## 数据与依赖边界

- Scheduler 不拥有用户 ScheduledTask 定义，不读取 BFF、Billing 或其他仓库数据库。
- BFF 是任务定义和业务状态 owner；目标业务 owner 负责 command receipt 和业务事实。
- 每次 dispatch 固定携带 job name、UTC occurrence、request id 和幂等键，重试复用 occurrence。

## 契约与验收

内部 API 使用稳定的 service token 与 scheduler headers。验收覆盖注册/替换/删除、lease/retry、
重复 occurrence、目标不可用和重启后的 BFF registration replay。
