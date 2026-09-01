# Studio 产品手册

状态：当前 Feature-first 产品定义，2026-08-22。产品入口与 GA/Studio owner 边界以
[37 App、Feature 与 Studio 架构](../technical/37-product-experience-agent-studio-architecture.md) 为准。

## 定位

Studio 是 Kokoro 统一入口中的专业 App surface。它不是 General Chat 的子页面；两者复用 Feature、Agent、Capability 与 Session 基建，但提供不同的任务界面。

## Studio 的共同结构

每个 Studio 都包含：

```text
Project             一个可持续编辑的创作空间。
Job                 一次生成、处理、转换、渲染或导出的任务。
Artifact            任务产物，如音频、视频、图片、代码、文档。
Version             产物的版本和变体。
Prompt / Parameters 用户意图和专业参数。
Timeline / History  操作历史和任务状态。
Export              下载、发布、分享或转到其它工具。
```

> 统一入口、App/Feature、GA Agent 组合、Job、Artifact 与计费的统一模型见
> [37 Kokoro 统一入口、App 与 Agent 产品架构](../technical/37-product-experience-agent-studio-architecture.md)。

## Studio 与 General Chat 的区别

```text
General Chat   对话优先，能力自动选择。
Studio         对象优先，流程和参数清晰。
```

Studio 不是一组聊天提示词。它给专业用户提供：

```text
参数控制、预览、版本管理、批量生成、
历史回滚、导出格式、成本估算、任务队列。
```

## Studio 入口

入口来自三类：

```text
独立域名 / 深链接
  music.example.com 预选 Music App 后进入 Music Studio。

Kokoro App launcher
  zeze.work/apps/music。

General Chat 升级
  Chat Feature 生成的 Job/Artifact 进入 Studio 精修。
```

## Studio 计费

Studio 和 General Chat 可调用同一 Studio Job kind 或模型能力，但产品入口和计费策略可不同。用户看到的
`music.generate`、`music.extend` 等是 capability/Job display name；真正进入 GA 的是 Entry 受信签发的 global
`FeatureKey`，它不是可读 slug、模型名或浏览器可写参数：

```text
Chat Feature -> FEATURE_KEY_GENERAL_ASSIST FeatureKey -> GA lead -> Studio CreateJob(music.generate)
Music App    -> FEATURE_KEY_MUSIC_CREATE FeatureKey  -> GA music_maker -> Studio CreateJob(music.generate)
Studio form  -> direct Studio CreateJob(music.generate)
```

当 GA Feature 创建 Job 时，GA 以稳定 `effect_id` 调用 Studio 并取得 JobRef；然后只发安全 `StudioJobLinked(JobRef)`。
Session 的聊天卡片以该 JobRef 读取 Studio snapshot/event，Studio 仍拥有 provider 与 Job 状态机，即使 parent Run 已 terminal。
专业 Studio 表单不创建 GA Run，而是使用同一个 Studio Job view/status contract。两条入口共享同一个 Studio Job 与 Storage Artifact lifecycle，
不共享或复制 Agent 配置、checkpoint、provider state。

支持：

```text
General Chat 简化定价。
Studio 专业功能更精细扣费。
单独套餐只包含某个 Studio。
多 Studio 组合套餐。
```

定价由 credit 决定，model 只给成本参考，不定价。详见 [07-pricing-credit-plans](07-pricing-credit-plans.md)。

## Studio 的共用技术底座

```text
kokoro-web      Studio UI、参数表单、预览、任务状态、Artifact 展示。
kokoro-session  Agent Feature 的消息/产品事件投影与 SSE；不拥有 Studio Job。
kokoro-agent    Workflow 内的自然语言 Agent、Skill/Tool 调用与 Studio public command；不拥有 provider/Job。
Studio           Project、Job、provider submission/callback 与专业控制面。
kokoro-storage   Upload、Asset、Artifact、scan、retention 与 ObjectStore port。
Billing/Credit   Agent ModelInvocation 和 Studio Job 各自的幂等结算事实。
```

存储边界见 [29 Storage/ObjectStore](../technical/29-capability-storage-runtime-architecture.md)。

## 首批 Studio

```text
P0  Music Studio    见 03-music-studio。
P1  Image Studio    见 04-video-image-code。
    Video Studio    见 04-video-image-code。
P2  Code Studio     见 04-video-image-code。
    Workflow Studio
```

## 验收标准

```text
Studio 可以独立站点使用。
Studio 可以从 General Chat 进入。
自然语言 Feature 与专业表单共享一套 Studio Job/Storage Artifact lifecycle。
Studio 产物能进入统一 Artifact library，且 GA sandbox/S3Workspace 不冒充用户产物。
Studio Job 与 Agent reasoning 分别按其幂等 identity 结算，不双扣。
```
