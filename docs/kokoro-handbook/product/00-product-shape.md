# 产品形态

## 一句话

Kokoro 是一个多站点 AI 产品工厂：用户在通用对话里完成轻量任务，或进入专业 Studio 完成音乐、视频、图片、代码等垂直创作。底层复用同一套账号、站点、模型、积分、支付、会话、Agent 能力。

## 产品层级

```text
入口站点
  首页、营销页、SEO 页、登录注册、价格页。

General Chat
  通用 AI 对话，支持调用能力、工具、skill、MCP、专业 agent。

Studio
  面向特定创作任务的专业工作台，如 music studio、video studio。

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

## 为什么分开

General Chat 和 Studio 是同级产品入口，不是侧栏里一个小功能和一个大功能的关系。

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

每个站点都可以是一个独立 AI 产品。siteId 是第一业务隔离边界。

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
数据按 siteId 隔离。
专业 Studio 能独立增长。
General Chat 能调用专业能力。
```
