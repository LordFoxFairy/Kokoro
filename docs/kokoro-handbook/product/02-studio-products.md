# Studio 产品手册

## 定位

Studio 是 Kokoro 的专业创作工作台。它不是 General Chat 的子页面，而是与 General Chat 同级的产品入口。

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
独立站点
  music.example.com 直接进入 Music Studio。

主站应用入口
  zeze.work/apps/music。

General Chat 升级
  对话中生成的 artifact 进入 Studio 精修。
```

## Studio 计费

Studio 和 General Chat 可调用相同底层模型，但使用不同 featureKey：

```text
general.music.generate
studio.music.generate
studio.music.extend
studio.music.export
studio.video.generate
studio.video.upscale
```

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
kokoro-web      Studio UI、参数表单、预览、任务状态、artifact 展示。
kokoro-session  实时任务流、历史回放、状态同步。
kokoro-agent    编排专业 Agent、工具、模型和 provider。
kokoro-platform site/user/model/credit/payment。
Mongo           job result、artifact metadata、创作上下文、大 JSON 状态。
Object Storage  音频、视频、图片、导出文件。
```

存储边界见 [../technical/06-data-storage.md](../technical/06-data-storage.md)。

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
Studio 产物能进入统一 artifact library。
Studio 任务能进入 job 状态机。
Studio 扣费通过 credit reserve/commit/refund。
```
