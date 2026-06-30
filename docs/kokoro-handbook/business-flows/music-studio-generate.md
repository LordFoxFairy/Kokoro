# Music Studio Generate 链路

## 目标

跑一次长耗时音乐生成 job：排队 -> 预估冻结积分 -> 解析模型 ->
调 provider（Suno）-> 异步轮询/webhook -> 成功落产物并按实际用量结算；
失败则释放冻结。全程 site scoped、幂等、不超扣。

## 参与模块

```text
kokoro-session / agent         通过 capability 发起 job，不拥有 job/credit 事实。
kokoro-credit                  quote / hold / capture / release，写 ledger 和 usage。
kokoro-model                   resolve 站点授权的生成模型。
provider (Suno)                实际生成，异步回调。
kokoro-artifact                落 Job / JobStep / Artifact / Asset。
```

## 前置条件

```text
SiteContext 已解析（siteId, appKey, surface=music.studio）。
User + workspace 已存在；CreditAccount 已 ensure。
EntitlementGrant 允许 music.studio.generate；PricingRule 覆盖该 capabilityKey。
SiteModelPolicy 授权了生成模型。
```

## 主流程

```text
0. 入口
   General Chat 通过 general.music.generate capability 进入；
   Music Studio 通过 studio.music.generate capability 进入。

1. 建 Job
   Job(siteId, appKey, surface, capabilityKey=music.studio.generate,
       workspaceId, userId, status=queued, idempotencyKey, requestId)。

2. Quote
   POST /credit/quote 入: siteId, workspaceId, capabilityKey, modelLabel/plan, quantity
   检查 entitlement，匹配 PricingRule，返回 estimateMicros。无副作用。

3. Hold
   POST /credit/hold 入: siteId, accountId, amountMicros, idempotencyKey, expiresAt
   按 bucket 优先级冻结，避免长任务成功后余额不足。UsageRecord status=held。

4. Resolve 模型
   POST /models/resolve(siteId, appKey, surface, capabilityKey) -> modelBindingId。

5. 执行
   Job status=running，写 JobStep(provider=suno, modelBindingId, startedAt)。
   调 provider (Suno) 提交生成请求。

6. 异步轮询/webhook
   provider 异步回调或轮询拿结果；JobStep finishedAt。

7. 成功落产物
   Job status=succeeded。
   建 Artifact(siteId, workspaceId, artifactType=audio, sourceJobId, visibility=private)
   + Asset(storageKey, mimeType, sizeBytes, checksum)。

8. Capture
   POST /credit/capture 入: siteId, holdId, actualAmountMicros, idempotencyKey
   按实际用量扣 bucket，写 CreditLedgerEntry（负数）+ UsageRecord status=settled，hold=captured。
```

## 异常流程

```text
余额不足          step 3 hold 失败 -> 402，提示充值。
模型不可用         step 4 resolve 503 -> release hold，job failed。
provider 失败/超时   生成失败或回调超时 -> Job status=failed，
                  POST /credit/release(siteId, holdId, idempotencyKey)，
                  UsageRecord status=failed。
用户取消          Job status=canceled -> release hold。
hold 超时         hold 到 expiresAt 自动过期释放。
重复提交          同 idempotencyKey 重放，hold/capture 幂等返回，不重复扣。
```

## 数据变化

```text
Job               status queued -> running -> succeeded / failed / canceled。
JobStep           新增（provider, modelBindingId, startedAt, finishedAt）。
Artifact          成功时新增（artifactType=audio, sourceJobId）。
Asset             成功时新增（storageKey, checksum）。
CreditHold        active -> captured（成功）/ released / expired（失败）。
CreditLedgerEntry capture 写负数。
CreditBucket      capture 减 remainingMicros。
UsageRecord       quoted -> held -> settled / failed。
```

## 幂等和一致性

```text
jobId             长任务关联键；subagent/工具 usage 归并到主 jobId。
idempotencyKey    hold / capture / release 幂等，唯一约束兜底，重放不重复扣。
holdId            冻结与结算/释放关联。
事务              capture 在 DB 事务内完成 bucket 扣减 + ledger 写入。
最终一致          provider callback -> job status -> artifact -> web 刷新。
强一致            credit hold -> job execution -> capture/release。
```

## 用户可见结果

```text
进行中    job 排队/生成中状态可见。
成功      音乐产物可播放/下载，余额按实际用量减少，usage 可见。
失败      额度自动恢复，无扣费，可重试。
余额不足   402，引导充值/升级。
```

## 验收标准

```text
同 idempotencyKey 重试 N 次，余额只变一次。
job 失败/取消/超时后 hold 完全释放，不留悬挂冻结。
capture 后 ledger 与 bucket 余额账平。
music job 无法写入 video workspace。
artifact 保留 siteId，可追溯到 sourceJobId。
```

## 相关

```text
General Chat 入口  ./general-chat-to-music-entry.md
Agent 编排路线  ../technical/13-agent-business-orchestration-roadmap.md
扣费闭底  ./credit-reserve-commit-refund.md
模型解析  ./model-resolution.md
产物生命周期  ./artifact-job-result.md
模块     ../modules/kokoro-credit.md
```
