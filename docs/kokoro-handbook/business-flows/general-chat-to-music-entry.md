# General Chat 到 Music Entry 链路

本文描述 `kokoro-web`、`kokoro-session`、`kokoro-agent` 如何把通用对话中的
音乐意图转成可追踪的 Music job。Music job、credit、model、artifact 的内部
规则仍以对应模块文档为准。

## 目标

用户在 General Chat 里用自然语言提出音乐创作请求，系统创建轻量
`general.music.generate` job，返回可播放/可进入 Music Studio 的结果卡片。

## 参与模块

```text
kokoro-web
  提交用户消息，渲染 assistant 回复、music job card、artifact card、进入 Studio。

kokoro-session
  保存 session messages/runs/events，构建 AgentRunInput，把 job/artifact refs
  放入 session event 和 snapshot 投影。

kokoro-agent
  识别 music intent，生成 MusicBrief，调用 general.music.generate capability。

music/job/artifact 服务
  拥有 MusicJob、MusicProject、Artifact、Asset 和 provider 结果。

credit/model
  quote/hold/capture/release 与模型解析。
```

## 前置条件

```text
SiteContext 已解析。
用户有 general.music.generate entitlement。
session 构建的 AgentRunInput.capabilities 包含 general.music.generate。
approvalPolicy 允许或要求确认该 capability。
credit/model/artifact 服务可用。
```

## 主流程

1. 用户在 General Chat 输入音乐请求。
2. Web 调用 `POST /sessions/:sessionId/messages`。
3. Session 写 user message、assistant placeholder、run。
4. Session 构建 `AgentRunInput`，其中包含 `general.music.generate` capability。
5. Agent 根据用户请求生成 `MusicBrief`。
6. 如果 policy 要求确认，Agent 发出 HITL approval。
7. 用户确认后，Agent 调用 `general.music.generate` capability tool。
8. Capability adapter 调用 music/job 服务。
9. music/job 服务执行 quote -> hold -> model resolve -> provider submit。
10. Session 通过 agent event 展示 tool/job queued 状态。
11. Provider 完成后，music/job 服务写 artifact/asset。
12. Agent 收到 capability result，输出 assistant summary。
13. Session 写 `message.completed` 到 messages，并写 session_events。
14. Web 渲染 music job card、artifact card 和进入 Music Studio action。

## MusicBrief

```text
MusicBrief
  prompt
  language?
  lyrics?
  styleTags[]
  mood?
  tempo?
  vocalMode?
  durationHint?
  negativePrompt?
```

Agent 只负责生成 brief。provider 原始参数由 music service 适配，不暴露给
General Chat。

## 数据变化

```text
kokoro_session.messages
  user message
  assistant final message

kokoro_session.runs
  general chat run

kokoro_session.session_events
  tool/job activity、message completed、run terminal

music jobs
  general.music.generate job

artifact/assets
  audio artifact、preview、metadata

credit
  hold / capture / release / usage record
```

## 幂等和一致性

```text
message idempotencyKey
  防止重复创建 chat run。

capability invocation idempotencyKey
  防止重复创建 music job 和重复扣费。

jobId
  关联 provider callback、artifact、usage。

artifactId
  Web 跳转 Studio 和播放预览的引用。
```

Session 不直接轮询 provider。job 进度进入 session 的方式可以是：

```text
agent 等待 capability result 后输出最终消息。
或 music/job 服务后续通过 session-facing job update adapter 写入活动事件。
```

P2 先允许“job card + 后续刷新查 job 状态”，不要求所有 provider 进度都走
agent token stream。

## 异常流程

```text
未授权
  capability 不进入 AgentRunInput，agent 不可调用。

余额不足
  hold 失败，assistant 返回充值/升级提示，不创建 provider job。

provider 失败或超时
  job failed，hold release，Web 显示失败可重试。

用户取消
  cancel run 或 cancel job，释放 hold。

重复提交
  session idempotencyKey 与 capability idempotencyKey 双重收敛。
```

## 用户可见结果

```text
生成中：assistant 活动流展示 music job queued/running。
成功：出现音乐 artifact card，可播放、下载、进入 Music Studio。
失败：显示失败原因和重试入口，余额不减少。
```

## 验收标准

```text
General Chat 能触发 general.music.generate。
AgentRunInput 未授权时不包含该 capability。
MusicBrief 不包含 provider 专有参数。
重复消息不会创建多个 job。
provider 失败会 release hold。
刷新后 snapshot 能恢复 assistant message 和 music job card。
Web 不直接调用 provider 或 artifact DB。
Agent 不直接写 credit ledger、music job、artifact。
```

## 相关文档

```text
技术路线  ../technical/13-agent-business-orchestration-roadmap.md
Music 产品  ../product/03-music-studio.md
Music job  ./music-studio-generate.md
Agent handoff  ./agent-handoff.md
P0 runtime  ../technical/12-agent-session-web-p0-implementation-design.md
```
