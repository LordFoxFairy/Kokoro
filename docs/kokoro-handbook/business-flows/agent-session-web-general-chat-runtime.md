# Agent / Session / Web 通用聊天运行链路

状态：当前三仓目标链路，2026-08-22。详细 owner 见
[36 GA 总体方案](../technical/36-ga-final-agent-technical-plan.md)，Root/legacy contract 切换见
[38 GA 公共运行契约](../technical/38-ga-public-runtime-contract.md)，HITL 见
[12 Agent HITL](../technical/12-agent-hitl-tool-interception.md)。

## 职责

```text
Web
  选择 App/Feature、提交输入/附件/可选模型标签、渲染 Session snapshot/SSE/HITL。

Session
  验证产品入口与权限；保存 feature_key、消息/run 投影和 SSE；投递最小受信 command。

GA
  一次性 normalizer、ledger claim、FeatureCatalog、DeepAgents、官方 Swarm、
  checkpoint/HITL/effect、Skill runtime 与 private execution evidence。
```

Web 和 Session 都不构建 `RuntimeConfig`，不选择 Agent、Tool、Skill、MCP、member、graph、provider 或 sandbox。

## 主流程

1. Web 在 App 内选择 Feature，提交消息、opaque AssetRef 与可选模型标签。
2. Session/BFF 校验 tenant、App、Feature、权限与产品计费资格；Session 创建或复用固定 `feature_key` 与 immutable tenant + subject；每次 Launch 重新受理 actor 对该 tenant + subject 的代表关系，并原子检查 active Run。
3. 若没有 active Run 或前一 Run 已 terminal，Session 落消息、分配新 `run_id`，向 GA 投递 Root `LaunchRunRequest`；其中没有 preset/capability selector 业务语义。
4. 若已有 `running` Run，普通文本返回 `run_active`，不落 Session 消息、不投递 Root command；只有当前 native interrupt 的 matching HITL/cancel 才投递 `ApplyControlRequest(same run_id)`。
5. GA ingress 一次性规范化 Launch 为 canonical `RunRequest` 并 durable claim；control 只由该 claim 在当前 native interrupt boundary 幂等应用。
6. GA 以 `feature_key` 取得内置 Feature；单 Agent 直接由 DeepAgents 执行，需要 peer 接手时由官方
   Swarm 初始化 `active_agent`，后续 Run 从原生 checkpoint 恢复当前 peer。
7. `AgentFactory` 将 Feature 声明转换为 DeepAgents 参数并 invoke/resume；后台隔离工作使用 DeepAgents
   native subagent。GA 不创建 WorkflowCompiler、CompiledGraph、RuntimeContext 或自有 graph/state。
8. GA 先将安全 ProductEvent 写入 `chat_events`，再发布 Redis live；Session 查询/replay 这些事实并投影 reply owner 的消息、活动、HITL、初始 Job/Artifact card 与 terminal，再 SSE 给 Web。GA CreateJob effect 只写 `StudioJobLinked(JobRef)`；Session 以 JobRef 读取 Studio snapshot 并消费/replay StudioJobEvent 刷新同一张 card。GA 不订阅 Job 状态。
9. HITL decision/reject/cancel 经 Session 授权后作为同一 `run_id` 的 control 送回 GA，按同一 Feature 与原生
   checkpoint 恢复或终态；Browser 断线不影响 GA recovery。

## 一致性与恢复

```text
message idempotency       Session admission
run claim / lease         GA ledger
checkpoint concurrency    GA runtime_namespace:thread_id gate
external effect replay    GA effect identity
product event replay      GA chat_events durable facts + Session query/replay projection
model billing             provider-accepted invocation_id + subject-bound Billing usage receipt
```

Session 有 `running` run 时后续普通输入返回 `run_active`，不创建第二个 Launch、并发 graph 或 checkpoint writer；awaiting interrupt 的 matching HITL/cancel 保留同一 `run_id`。
只有 terminal 后的下一条普通用户消息才创建新的 `run_id`；它仍读取同一个 `thread_id=session_id` checkpoint。worker
restart/reclaim 从 ledger 中同一 canonical RunRequest 恢复；Session relay/browser 离线时不阻塞执行。

## 动态能力与产物

- default Skill 由 GA direct catalog 提供；user/session Skill 仅经 `find_skills/load_skill` -> Capability path -> Storage
  content 进入 GA workbench。
- Studio Job、Asset、Artifact 均经 public contract；GA S3Workspace 是可选 sandbox adapter，不替代 Artifact。
- provider 接受的模型调用按 `invocation_id` 计费；GA usage receipt 带 `ExecutionIdentity.subject` 的最小 `billing_subject` 与可选 `billing_ref`，Billing 自己定位 payer；RuntimeNamespace 不参与扣费。token 不作为产品计费单位。

## 验收

```text
Browser payload 与 Session record 不携带 Agent/runtime recipe。
GA default-only run 在 CA/Storage 未请求或暂不可用时仍可启动。
terminal 后续聊才创建新 run_id；active `running` 文本返回 `run_active`，matching HITL/cancel 才控制原 run_id，二者都没有第二份 active_agent 或 graph state；只有 Swarm 使用 active_agent。
Session 投影可刷新和 SSE replay；GA checkpoint 可独立恢复，且 ProductEvent 不含 WorkItem/task 控制、raw thinking/tool/subagent/sandbox payload。
Chat/Music/Image/Video/Code/Creative 共用同一三仓运行链路。
```
