# 能力(Capability) × Studio × Chat 架构 — 技术方案

状态：草案待评审
日期：2026-07-24
缘起：产品愿景是"AI 产品工厂（Chat + 专业 Studio）"，但 Studio 与媒体能力=0。
用户定向：**优先 Music Studio + Image Studio，能过快速，且做好后反哺 Chat 当二级子功能。**
关键：**"反哺 chat"从架构上强制了一个统一抽象**——能力不能焊死在 Studio 里。

> 论据只来自我们自己的约束（design soul：能力放对层 / 扩张=加配置 / chat 复用专业能力 / 不自建媒体模型）。

---

## 0. 核心原则：**能力是原子，Studio 与 Chat 是它的两个界面**

一句话定架构：
- **Capability（能力）** = 可被调用的一个"产品能做 X"的原子单位（对话、生成音乐、生成图片、代码…）。
- **Studio** = 某能力之上的**专业工作台界面**（参数/预览/版本/队列/批量/导出）。付费、可增长。
- **Chat** = agent 把**同一个能力**当**工具**调用的低门槛界面。

**同一份能力，两个界面。建一次，surface 两次。** 这就是"Studio 反哺 Chat"的机制——
Studio 依赖的能力**本就在 Chat 可调用**，不是再实现一遍。焊死在 Studio 里则永远反哺不了。

---

## 1. 能力模型（Capability）

一个能力声明：
- **调用契约**：入参 schema（如 image：prompt/尺寸/风格/张数）→ 出参（artifact/message）。
- **执行模式**：`sync-stream`（LLM 对话，流式）| **`async-job`（媒体生成，耗时秒~分）**。
- **provider**：谁执行——LLM=litellm 网关；**媒体=外部 provider（Suno/Replicate/fal/OpenAI-images…），我方不自建模型**。
- **featureKey（计费）**：如何计量/定价（music / image 各自费率；接 credit hold/settle）。
- **产出**：message（chat 内联）| **artifact（媒体产物，进产物库）**。
- **权益 gating**：哪些 Plan 可用 / 什么档（免费=基础、订阅=高级模型/更快/更低倍率——接 §权益层）。

> 加一种能力（video/code/tts）= 声明一条 = provider 适配 + featureKey + 参数 schema，**不改 job/计费/产物/界面机器**。

---

## 2. 媒体能力 = 异步 job + 外部 provider（这也是"能快"的原因）

**能过快，因为我方不训练/不托管媒体模型——只做集成**：
- **provider 适配层**（类比 litellm 之于 LLM，但 job 形态）：把 Suno/Replicate/fal 等的 API 归一化成统一"媒体 job"。
  凭据同模型 key，走加密/env 注入（provider key 需你提供，架构可先用一个 provider/mock 跑通）。
- **job 生命周期**：enqueue → hold 积分 → 调 provider → poll/webhook → 结果 → settle 积分 → 落 artifact → SSE 通知。
- **复用现有机器**：credit hold/settle、artifact 库、SSE、Redis 队列、namespace 隔离——**全都现成**。
  真正的新件只有：**provider 适配 + job 编排 + 两个界面**。

---

## 3. 两个界面：反哺的机制

**能力层（job）被两个入口共用**：
- **Chat（二级子功能）**：agent 把能力当**工具**调——"生成一张猫的图" → agent 调 image 工具 → job → 产物卡回到对话。
  低门槛、语言驱动。这就是"反哺"：Studio 建好的能力，Chat 立刻能用。
- **Studio（主打付费）**：专业工作台 UI，参数表/实时预览/多版本/队列/批量/导出，驱动**同一个 job**。
  主界面不是聊天，是控制面。

**落位待定（§6 决策）**：job 层需要 agent 工具**和** Studio 后端都能调 → 是共享的"能力 job 服务"（非 agent 私有）。

---

## 4. Studio 即配置（扩张=加配置不是加代码）

一个 Studio = `{能力 ref, 参数 schema, UI 布局模板, featureKey, 产物类型}`。
- **Music Studio** = music 能力 + 音乐参数（时长/风格/歌词/人声）+ 音频产物 + 音乐 featureKey。
- **Image Studio** = image 能力 + 图片参数（尺寸/风格/张数/参考图）+ 图片产物 + 图片 featureKey。
- **后续 Video/Code Studio** = 新 provider + 新配置，**复用 job/计费/产物/界面骨架**。
这就是"产品工厂"：新垂类 = 共享能力机器之上加一份配置。

---

## 5. 分层落位（映射现有仓）

- **provider 适配 + 凭据**：归模型/provider 域（kokoro-model 扩出"媒体 provider"，或平行新模块）。凭据同 model key 口径。
- **能力 job 编排**：新"能力 job"层（enqueue/hold/provider/settle/artifact/notify）——agent 工具与 Studio 后端共调。
- **Chat 工具**：kokoro-agent 加媒体工具（wrap job）。
- **Studio UI**：kokoro-web/apps/user 加 studio 路由/工作台（暖纸感设计系统）。
- **产物**：现有 artifact 库（按 studio/project 归类，接 §组织纵深）。
- **计费**：credit hold/settle + 媒体 featureKey；卡密/订阅/包三渠道供给积分。

---

## 6. 待你确认的架构决策（我已定倾向，供纠偏）

1. **能力 job 层落位**：独立"能力 job 服务"（agent 工具 + Studio 后端共调）——倾向此，避免 Studio 被迫走 agent run。
   次选：Studio 也走 headless agent run（复用最彻底但耦合 agent）。
2. **provider 归属**：媒体 provider 收进 kokoro-model 的 provider/凭据体系（一个 provider 就是一个 provider），还是平行新模块。
3. **反哺时序**：先把能力 job + Studio 做好 → 再在 chat 挂工具（反哺）。即 **Studio 先行、Chat 工具随后**。

---

## 7. 执行序（提案，先对齐再动）

1. 能力 job 层骨架（enqueue/hold/provider/settle/artifact/notify）+ 一个真 provider（或 mock）跑通。
2. **Image Studio**（图片最快：单次调用、产物直观）→ 参数表/预览/版本/导出。
3. **Music Studio**（音频：时长/风格/歌词/人声）。
4. 两个能力**挂进 Chat 工具**（反哺，二级子功能）。
5. featureKey 计费接入（图片/音乐费率）+ 卡密/订阅/包供给。
6. 产物库按 studio/project 归类（依赖组织纵深 workspace/project）。

> 依赖：媒体 provider key（同"真模型 key"，你提供即真；架构先用单 provider/mock 验证）。
