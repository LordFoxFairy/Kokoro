# Music Studio 产品手册

## 定位

Music Studio 是第一个专业 Studio，对标 Suno、Tad.ai 等 AI 音乐产品，但保持 Kokoro 的多站点、通用对话、Agent 和积分体系。

## 用户任务

```text
一句话生成歌曲
  输入主题、风格、语言、情绪，生成完整草稿。

歌词创作
  写歌词、改歌词、生成多版本。

音乐风格控制
  genre、mood、tempo、vocal、instrument、length。

续写和变体
  extend、variation、remix。

导出
  mp3/wav/stem，后续可扩展版权和商用授权。

项目管理
  保存到 project，管理版本和历史。
```

## 页面结构

```text
左侧   项目/历史/版本列表。
中间   当前作品、歌词、波形/播放器、生成状态。
右侧   参数、模型、风格、导出、成本预估。
底部   prompt/composer 或生成控制条。
```

## 两种入口

General Chat 入口：

```text
用户说「帮我做一首轻快广告歌」
  -> 通用 Agent 生成简化参数
  -> 调用 general.music.generate capability 创建 music job
  -> 返回 artifact card
  -> 可进入 Music Studio 精修
```

独立 Music 站点入口：

```text
music.example.com
  -> SiteContext(site_music)
  -> Music Studio 首页
  -> 直接创建 music project/job
```

## 核心对象

```text
MusicProject   一首或一组歌曲的创作空间。
MusicJob       generate/extend/remix/export。
MusicArtifact  音频文件、歌词、封面、metadata。
MusicVersion   同一 project 下的不同版本。
```

## 计费

featureKey：

```text
general.music.generate
studio.music.generate
studio.music.extend
studio.music.remix
studio.music.export
```

扣费链路：

```text
quote -> hold -> provider job -> commit/release -> usage record -> artifact
```

长耗时 job 的 hold 一致性见 [../business-flows/credit-reserve-commit-refund.md](../business-flows/credit-reserve-commit-refund.md)。

## 模型

模型由 `kokoro-model` 管理：

```text
featureKey      music
labelKeys       fast / quality / vocal / instrumental / pro
transportKind   direct
```

LiteLLM 不强行负责音乐 provider。音乐 provider 通常走 direct adapter。model 只描述能用哪些模型和成本参考，不定价。

## 风险

```text
不要把音乐 provider 的所有参数直接暴露给新手。
不要让 General Chat 和 Music Studio 使用同一个 UI。
不要让音乐模型价格写死在 model 模块。
不要跳过 credit hold 直接调用 provider。
不要让 agent 直接写 music job / artifact / credit ledger。
```

## P0 验收

```text
能从独立 music site 创建 job。
能从 General Chat 创建简化 music job。
能保存 artifact。
能按 featureKey 扣费。
能展示 job 进度和失败退款。
```

General Chat 到 Music 的 agent 编排入口见
[../business-flows/general-chat-to-music-entry.md](../business-flows/general-chat-to-music-entry.md)。
