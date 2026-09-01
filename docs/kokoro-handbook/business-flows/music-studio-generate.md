# Music Studio Generate 链路

状态：当前 Feature-first Music 产品链路，2026-08-22。产品/编排总图见
[37 App、Feature 与 Studio 架构](../technical/37-product-experience-agent-studio-architecture.md)；GA 执行、状态和
S3Workspace 边界见 [36 GA 整体 Agent 技术方案](../technical/36-ga-final-agent-technical-plan.md)；Root command
与安全事件边界见 [38 公共运行契约](../technical/38-ga-public-runtime-contract.md)。

## 产品语义：一个 Music App，两种正确入口

```text
Music App
  A. 自然语言创作 Feature
     -> FEATURE_KEY_MUSIC_CREATE FeatureKey
     -> GA Feature(FEATURE_KEY_MUSIC_CREATE -> music)
     -> Studio CreateJob / QueryJob

  B. 专业参数控制
     -> Studio direct CreateJob / QueryJob
     -> 同一 Studio Job / Artifact lifecycle
```

入口 A 是“帮我做一首轻快广告歌”一类需要理解、建议、歌词/风格协作和持续对话的 Agent Feature。入口 B 是专业用户
已给出完整参数时的确定控制动作；它不绕经 GA，也不创建一个只为提交表单的 Session Agent 选择。二者共享 Music App、
Studio Job 与 Storage Artifact，却不共享两套 provider、计费或产物事实。

`music_maker` 是 GA 内置 `Agent`，不是 Session 字段、浏览器 selector 或独立服务。一个 AI Music 站点仅需：

```text
System:  Music App + enabled AppFeatureExposure(FEATURE_KEY_MUSIC_CREATE)
GA:      Feature(FEATURE_KEY_MUSIC_CREATE -> music)
Studio:  supported CreateJob/QueryJob command + Music Job lifecycle
Storage: Asset/Artifact lifecycle
```

无需新建 Music worker、Music Session service、Music graph service 或“音乐编排层”。

## A. Agent Feature 主链

```text
1. Browser 进入 music.example.com 或 App launcher，选择“创作歌曲”这一产品 Feature。
2. Entry/Session 校验 host、tenant、AppFeatureExposure、权限与计费资格，取得可信 global FeatureKey；
   创建或读取 Session(feature_key)，并落用户消息与 run admission。
3. Session 投递最小 LaunchRunRequest(run_id, session_id, ExecutionIdentity, feature_key, input, opaque AssetRef...)；GA 在 ingress 派生内部 RuntimeNamespace。
4. GA normalizer 使用 session_id 作为 DeepAgents thread；RunLedger durable claim 后，从本地 FeatureCatalog 取得
   FEATURE_KEY_MUSIC_CREATE 的 `music` Agent。
5. 同一 Session 首次 bootstrap DeepAgents native state；后续消息以同一 native checkpoint 继续。没有
   active_agent、Agent name、RuntimeConfig、Skill/MCP snapshot 或图配置写入 Session。
6. music_maker 使用 GA default Skill；需要用户/Session Skill 时才经 find_skills/load_skill 按需加载到
   GA workbench。Capability 负责 logical path/CRUD，Storage 负责已扫描内容；普通编辑不改写已加载 mount。
7. 需要生成时，GA 以该 CreateJob effect 的稳定 id 和 operation-bound RunExecutionAttestation 调用 Studio CreateJob；
   Studio 选择 provider、维护 Job/Project/状态机，并返回 opaque JobRef。
8. GA 写 initial `StudioJobLinked(JobRef)` ProductEvent；Session 随后以 JobRef 读 Studio snapshot 并消费/replay安全 StudioJobEvent 更新 Job/Artifact card。Run 已 terminal、GA/Browser 断线时也不重开 Run；Job event 绝不写 assistant 文本。
9. Studio 通过 Storage 的公开 Artifact lifecycle 完成用户可见音频/歌词/封面；GA sandbox 文件与 S3Workspace
   不作为交付 Artifact，也不泄漏 bucket/object key。
```

```text
Music Feature
  feature_key: FEATURE_KEY_MUSIC_CREATE  # 文档符号；实际值为 System 分配的 opaque key
  entry/members: music_maker
  agents: [music]
  entry_agent: music
```

它是单 Agent 的最快垂类组装。歌词研究、素材准备等隔离工作优先使用 DeepAgents `task`；只有多个平等专员需要
直接接管同一用户对话，才由另一份已发布且兼容的 Swarm Feature（或新的 FeatureKey/new Session）表达。任何既有 Run
不会临时改成 Swarm、把 Music Agent 写入 Session，或拼接新图。

## B. Studio direct control 主链

```text
专业表单 -> Studio CreateJob(validated parameters, feature policy)
          -> provider submission / callback / polling
          -> Job terminal
          -> Storage CreateUpload -> CompleteUpload -> CreateArtifact -> FinalizeArtifact
          -> Studio UI 的 Job/Artifact read model
```

Studio 直接控制不要求一条 GA Run。用户需要“为什么这样写、替我改歌词、基于上一版继续创作”时，可以从 Studio 打开
`FEATURE_KEY_MUSIC_CREATE` Agent Feature 的新 Session；该新 thread 从 Music Feature entry bootstrap，不挪用旧 Session 的
DeepAgents native state、workbench 或动态 Skill。

## 与 General Chat 的组合

```text
General Chat Feature(FEATURE_KEY_GENERAL_ASSIST)
  -> General Assistant 在 Chat Feature 中使用 DeepAgents native subagent / 创建 Studio Job
  -> Studio Job / Artifact card 回到 General Chat Session

Music Studio Feature(FEATURE_KEY_MUSIC_CREATE)
  -> 新 Music Session + music_maker single Feature
```

General Chat 可以组合音乐能力，但不把原 Chat thread 改成 Music Agent，也不把 Music Studio 的专业权限、模型策略或
Project 状态混入原对话。用户打开 Music App 才开始另一个 Feature Session。

## 计费、恢复与失败

| 事实 | owner | 语义 |
|---|---|---|
| Agent reasoning | GA -> Billing usage fact | 每个 provider-accepted `ModelInvocation` 按 `invocation_id` 计一次；token 仅成本/预算诊断。 |
| Music generation Job | Studio/Credit | Job 自己的 quote -> hold -> capture/release；provider callback/retry 不归 GA 伪造。Feature 静态选择 `detached` 或 `request_cancel`：后者只是 GA 向 Studio 的一次幂等取消请求。 |
| 音频/歌词/封面 | Storage | 仅完成 canonical Asset/Artifact lifecycle 后才可展示/交付。 |
| sandbox/workbench persistence | GA | `S3Workspace` 是 MinIO-first 的 `WorkbenchPersistence` S3 adapter；`durable_required` mount 必须 commit 后才成功，且永不等同 Artifact owner。V1 `S3Archiver` archive failure 只是不影响本地写/Artifact 的旁路诊断。 |

Feature `cost_policy` 明确 reasoning 与 Job 是否 `included`、`separate` 或 `zero-rated`，用 invocation/job 的独立幂等
identity 防止双扣。GA 的 ledger/checkpoint 可在 Browser、Session relay 或 Capability client 离线时恢复 default-only
run；dynamic Skill/Asset/Studio source 在每次 operation boundary 由 owner 重新校验。

## 验收

```text
Music App 只通过 App/Feature admission 选择对应的 `FEATURE_KEY_MUSIC_CREATE`；Browser payload 不含 Agent、member、graph、Skill/MCP 或 provider 配方。
FEATURE_KEY_MUSIC_CREATE 首次/恢复均使用同一 `music` Agent 与同一 Session 的 DeepAgents native checkpoint。
专业参数表单直达 Studio Job；自然语言入口通过 GA CreateJob；两条链只有一套 Studio Job/Storage Artifact lifecycle。
ProductEvent/SSE 与 Studio Job snapshot/event 只含安全 Job/Artifact/assistant/terminal 信息，不含 raw thinking、tool 参数、provider secret、sandbox/object path；Job event 在 Run terminal 后只能更新 card。
GA reasoning invocation 与 Studio Job 结算均可重放且不双扣；`detached`/`request_cancel` 行为可恢复且不复活 Run；`ephemeral_ok` core 不因没有 S3Workspace 阻塞，`durable_required` Feature 由 workbench readiness/`workbench_unavailable` 收束，且 V1 S3Archiver archive failure 不影响 Artifact finalization。
```
