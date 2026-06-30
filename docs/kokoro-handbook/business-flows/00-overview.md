# 业务链路总览

本目录描述用户可感知或系统关键的完整链路，从入口到数据变化。每条链路统一写：目标、参与模块、前置条件、主流程、异常流程、数据变化、幂等和一致性、用户可见结果、验收标准。

## 链路清单

```text
site-resolution               host -> SiteContext，所有请求的第一步。
user-register-login           注册登录，落 User/ExternalIdentity/personal workspace。
general-chat                  通用对话扣费链路（quote/hold/model/provider/capture）。
agent-session-web-general-chat-runtime  三仓内部通用聊天运行链路。
general-chat-to-music-entry   General Chat 触发 music job 并进入 Music Studio。
agent-handoff                 General Agent 编排专业 Agent / 工具，subagent usage 归并。
session-lifecycle             conversation 创建/活跃/存档/删除与 siteId 绑定。
credit-reserve-commit-refund  扣费闭环底座，被所有计费链路复用。
payment-to-credit             支付成功 -> grant 权益和积分。
model-resolution              按 SiteModelPolicy 解析可用 model binding 与 fallback。
music-studio-generate         长耗时 job 的生成、轮询、结算、产物。
artifact-job-result           产物生命周期：创建/编辑/发布/查询/删除/导出。
```

## 贯穿全链路的纽带

```text
siteId           第一隔离边界，所有业务读写的第一过滤条件。
requestId        全链路追踪和日志关联。
idempotencyKey   防重复扣费/下单/发放/处理 webhook。
jobId            长耗时任务关联，subagent usage 归并到主 jobId。
holdId           冻结与结算/释放的关联。
```

## 一致性分级

```text
强一致（必须事务/幂等）：
  payment event -> order/subscription -> credit grant
  credit hold -> job execution -> commit/release
  user/team permission -> run authorization

最终一致：
  provider callback -> job status -> artifact metadata -> web refresh
  agent event -> session normalization -> SSE
  analytics event -> dashboard
```
