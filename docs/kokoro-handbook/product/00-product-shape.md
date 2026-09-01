# 产品形态

状态：当前 Feature-first 产品轮廓，2026-08-22。产品入口、Feature、GA Workflow 与 Studio 的 owner 以
[37 App、Feature 与 Studio 架构](../technical/37-product-experience-agent-studio-architecture.md) 为准；用户可见交付与质量/成本回归
以 [41 Feature 结果契约](../technical/41-feature-outcome-contracts-and-quality-gates.md) 为准。

## 一句话

Kokoro 是一个统一入口的 AI 产品工厂：用户从同一个 Kokoro Entry 进入 Chat、Music、Image、Video、Code 等 App；独立域名只预选默认 App 与品牌。每个智能 Feature 由一个或多个 Agent 组成，底层复用同一套账号、站点、模型、积分、支付、会话、GA、Studio 与产物能力。

## 产品层级

```text
Kokoro Entry
  统一 App launcher、深链接、登录注册、价格与可信 tenant/site context。

App
  Chat、Music、Image、Video、Code、Creative 等产品入口；独立域名只是默认 App。

Feature
  一个用户可开始的智能功能；System 的 FeatureDefinition 定义输入、用户可见交付、失败/更新状态和 cost policy，
  GA 再以同一 FeatureKey 的 Workflow 声明一个或多个 Agent 的协作。产品契约不保存 Agent/图，GA Workflow 也不复制 UI/价格。

Studio
  面向特定创作任务的专业工作台，如 Music Studio、Video Studio；它拥有 Project/Job/provider，
  并通过 canonical ArtifactRef 集成 Storage 产物。

Artifact Library
  用户生成产物库，按站点、workspace、project、类型组织。

Admin Console
  平台、站点、模型、用户、积分、支付、运营和风控管理。
```

## 两类体验

### General Chat

低门槛入口，让用户直接用自然语言表达需求。

```text
不需要先理解专业参数。
能自动调用 music/video/image/code 等能力。
输出是文字、工具结果、任务进度或产物卡片。
适合轻量创作、咨询、整理、转换、解释、探索。
```

详见 [01-general-chat](01-general-chat.md)。

### Studio

专业垂直产品，提供完整控制面。

```text
有明确对象和工作流。
有参数、预览、版本、历史、队列、导出。
复用 General Chat 的对话能力，但主界面不是聊天。
适合高频、专业、可付费的创作任务。
```

详见 [02-studio-products](02-studio-products.md)。

> 统一入口、App/Feature、单 Agent/多 Agent、Studio Job 与计费的总体模型见
> [37 Kokoro 统一入口、App 与 Agent 产品架构](../technical/37-product-experience-agent-studio-architecture.md)。

## 为什么分开

General Chat 和 Studio 是统一 Kokoro Entry 下的不同 App/Feature surface，不是侧栏里一个小功能和一个大功能的关系。

```text
General Chat   以语言为入口，强调低成本开始。
Studio         以专业对象为入口，强调控制、效率和可复用产物。
```

两者共享：

```text
账号体系、workspace/team/project、模型能力、Agent 能力、
积分/套餐、artifact/job、admin/observability。
```

两者隔离：

```text
页面 IA、任务参数、产物编辑体验、计费 featureKey、SEO 和营销定位。
```

## 多站点形态

每个站点都可以是独立品牌或默认 App 的 AI 产品入口；可信 tenant/site context 是业务隔离边界。

```text
zeze.work            通用 AI 工作台。
music.example.com    音乐 AI 产品。
video.example.com    视频 AI 产品。
image.example.com    图片 AI 产品。
code.example.com     代码 Agent 产品。
brand-a.example.com  白标客户 A。
```

站点独立，平台复用。同邮箱跨站默认是不同用户。详见 [05-teams-workspaces-projects](05-teams-workspaces-projects.md) 和 [08-multi-site-seo-growth](08-multi-site-seo-growth.md)。

## 产品边界

不做：

```text
把所有功能堆进一个侧边栏。
把 Studio 当成普通聊天插件。
把同邮箱跨站默认合并成同一用户。
把不同站点的积分默认打通。
把模型选择、价格、套餐、扣费混成一个模块。
```

要做：

```text
入口清晰。
能力复用。
数据按可信 tenant/site context 隔离。
专业 Studio 能独立增长。
General Chat 能调用专业能力。
```
