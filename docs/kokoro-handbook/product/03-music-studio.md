# Music Studio 产品手册

状态：当前 Feature-first Music App 产品定义，2026-08-22。完整 Agent/Studio 双入口与计费边界见
[Music Studio Generate 链路](../business-flows/music-studio-generate.md) 与
[37 App、Feature 与 Studio 架构](../technical/37-product-experience-agent-studio-architecture.md)。

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
  -> 创建 music job
  -> 返回 artifact card
  -> 可进入 Music Studio 精修
```

独立 Music 站点入口：

```text
music.example.com
  -> Kokoro Entry resolves trusted tenant/site context
  -> preselect Music App -> Music Studio 首页
  -> 直接创建 music project/job
```

两条入口收敛于同一个 Studio public `CreateJob/QueryJob` contract。独立 Studio 由用户直接提交专业参数，
无需经过 GA；自然语言创作入口通过 `FEATURE_KEY_MUSIC_CREATE` Feature 进入 GA 的 `music_maker` Agent，再调用相同
contract。经 GA 创建时，`music_maker` 的 stable `CreateJob effect_id` 取得 JobRef 并写 `StudioJobLinked`；Session 以 JobRef
读取 Studio snapshot/event 更新 Job/Artifact card，不在 Run terminal 后重开对话。独立 Studio 表单不创建 GA Run，直接展示同一个 Studio Job。
`music_maker` 也可以辅助歌词、prompt、素材规划和版本解释，但它不拥有 Job、provider、Credit 或音频 bytes，更不是 Session 上的 `music-copilot` 配置。

> Music App 的 `FEATURE_KEY_MUSIC_CREATE` Feature、Music Assistant、Studio Job 与 General Chat 组合见
> [37 Kokoro 统一入口、App 与 Agent 产品架构](../technical/37-product-experience-agent-studio-architecture.md)。

## 核心对象

```text
Studio Project       一首或一组歌曲的创作空间。
Studio Job           generate/extend/remix/export。
Storage Artifact     音频文件、歌词、封面与 metadata 的交付生命周期。
Studio Version       同一 project 下的不同版本和变体。
```

## 计费

产品能力名称（展示/Studio policy，不是浏览器传入的 GA `FeatureKey`）：

```text
general.music.generate
studio.music.generate
studio.music.extend
studio.music.remix
studio.music.export
```

Studio Job 扣费链路：

```text
quote -> hold -> provider job -> commit/release -> usage record -> artifact
```

自然语言 reasoning 则按 GA 的 provider-accepted `ModelInvocation` count 单独结算；两类事实以
`cost_policy` 与各自幂等 identity 防止双扣。见
[Music Studio Generate 链路](../business-flows/music-studio-generate.md)。

## 模型

模型由 `kokoro-model` 管理：

```text
job kind        music.generate / music.extend / music.remix
model label     fast / quality / vocal / instrumental / pro
transport       Studio provider adapter
```

LiteLLM 不强行负责音乐 provider。音乐 provider 通常走 direct adapter。model 只描述能用哪些模型和成本参考，不定价。

## 风险

```text
不要把音乐 provider 的所有参数直接暴露给新手。
不要让 General Chat 和 Music Studio 使用同一个 UI 或共用同一 Session/thread。
不要让音乐模型价格写死在 model 模块。
不要跳过 credit hold 直接调用 provider。
```

## P0 验收

```text
能从独立 music site 创建 job。
能从 `FEATURE_KEY_MUSIC_CREATE` Feature 创建简化 music job，并从 General Chat 的 lead Workflow 组合音乐能力。
能经 Storage Artifact lifecycle 保存和展示产物。
能分别结算 GA ModelInvocation 与 Studio Job，不按 token 或可读 feature 字符串混算。
能展示 job 进度和失败退款。
```
