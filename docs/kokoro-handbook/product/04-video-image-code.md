# Video / Image / Code Studio 产品手册

## 定位

Video、Image、Code 是继 Music 之后的专业 Studio。三者共用 [02-studio-products](02-studio-products.md) 定义的 Project/Job/Artifact/Version 结构，差异在创作对象、参数面、模型 transport 和计费 featureKey。

```text
Image Studio   文生图、图生图、批量变体、放大、改图。
Video Studio   文生视频、图生视频、镜头编排、放大、导出。
Code Studio    用 agent 执行代码任务，输出 patch / 文件 / 运行结果。
```

Image/Video 偏生成型 provider；Code 偏 agent 执行。

## 用户任务

```text
Image
  一句话生图、参考图改图、批量风格变体、放大、抠图。

Video
  一句话生短视频、图生视频、镜头/分镜编排、放大、导出。

Code
  描述需求 -> agent 规划 -> 生成或修改文件 -> 运行 -> 返回结果。
```

## 页面结构

Image / Video 沿用 Studio 通用布局：

```text
左侧   项目/历史/版本列表。
中间   当前产物预览（图/视频/分镜）、生成状态。
右侧   参数、模型、尺寸/时长、批量数、导出、成本预估。
底部   prompt/composer 或生成控制条。
```

Code Studio 以执行为中心：

```text
左侧   project / 任务列表 / 文件树。
中间   diff / 代码 / 运行输出 / agent 活动流。
右侧   模型、运行环境、成本预估。
底部   任务指令输入。
```

## 两种入口

General Chat 入口：

```text
用户说「给我一张赛博朋克海报」
  -> 通用 Agent 生成简化参数
  -> 创建 image job
  -> 返回 artifact card
  -> 可进入 Image Studio 精修
```

独立站点入口：

```text
image.example.com -> SiteContext(site_image) -> Image Studio 首页
video.example.com -> SiteContext(site_video) -> Video Studio 首页
code.example.com  -> SiteContext(site_code)  -> Code Studio 首页
```

## 核心对象

```text
ImageProject / ImageJob / ImageArtifact / ImageVersion
  ImageJob       generate/edit/variation/upscale。
  ImageArtifact  图片文件、prompt、参数 metadata。

VideoProject / VideoJob / VideoArtifact / VideoVersion
  VideoJob       generate/img2video/upscale/export。
  VideoArtifact  视频文件、分镜、prompt、参数 metadata。

CodeProject / CodeJob / CodeArtifact / CodeVersion
  CodeJob        run/edit/test。
  CodeArtifact   patch、文件、运行日志、结果摘要。
```

## 计费

featureKey：

```text
general.image.generate
studio.image.generate
studio.image.edit
studio.image.upscale

general.video.generate
studio.video.generate
studio.video.upscale
studio.video.export

general.code.run
studio.code.run
studio.code.test
```

扣费链路：

```text
quote -> hold -> provider/agent job -> commit/release -> usage record -> artifact
```

长耗时 job 的 hold 一致性见 [../business-flows/credit-reserve-commit-refund.md](../business-flows/credit-reserve-commit-refund.md)。model 不定价，credit 决定扣多少。

## 模型

模型由 `kokoro-model` 管理。transport 视 provider 而定：

```text
Image   featureKey image，transportKind direct 或 litellm（视 provider）。
Video   featureKey video，transportKind direct 或 litellm（视 provider）。
Code    featureKey code，主要由 agent 执行，模型走文本 provider。
```

Image/Video provider 若有原生 SDK 走 direct adapter；若 LiteLLM 已覆盖则走 litellm。Code 偏 agent 执行，编排见 [../technical/03-agent-architecture.md](../technical/03-agent-architecture.md)。

## 风险

```text
不要把 provider 的全部参数直接暴露给新手。
不要让 General Chat 和 Studio 使用同一个 UI。
不要让模型价格写死在 model 模块。
不要跳过 credit hold 直接调用 provider 或执行 agent job。
Code Studio 的执行必须落在 sandbox，不直接碰宿主环境。
```

## P0 验收

```text
能从独立 site 创建 image/video/code job。
能从 General Chat 创建简化 job。
能保存 artifact。
能按 featureKey 扣费。
能展示 job 进度和失败退款。
Code job 在 sandbox 内执行且结果可回放。
```
