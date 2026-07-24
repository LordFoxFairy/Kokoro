# 通用引擎架构：一个本质，surface + 模型 是唯一变量 — 技术方案

状态：草案待评审（v3，收敛到"共同本质"）
日期：2026-07-24
用户定向：优先 Music/Image Studio、能过快、反哺 Chat；**先把通用的基本能力打通**。

> 论据只来自我们自己的约束（design soul：智能给 agent / 能力放对层 / 扩张=加配置 / chat 复用能力 / 不自建媒体模型）。

---

## 0. 共同本质：**只有一台通用引擎**

Chat、Music Studio、Image Studio、以后 Video/Code——**不是不同的东西，是同一台引擎的不同配置**。

**本质（一条链）：**
```
用户意图 → GA 编排能力 → 能力调用 kokoro-model 里的模型（任意厂商/任意模态）
        → 产出 artifact → credit 计量 → namespace 隔离
```

**全局只有两个变量：**
1. **surface**：Chat（语言表意、GA 自选） vs Studio（参数直给、专业控制面）。**只差意图表达 + 产出呈现。**
2. **模型**：调 kokoro-model 里的哪个——LLM / 音乐模型 / 图片模型 / 视频模型。**都是一个"模型"，平级。**

其余（GA、能力抽象、credit、artifact、namespace）**恒定不变**。

> 推论：**根本没有"做一个 Music Studio / Image Studio"这种事**——只有"给通用引擎加一份配置（surface 布局 + 指定模型 + featureKey）"。
> 产品工厂是字面的：**工厂=这台引擎；产品=配置。** 所以要打磨的是**引擎的通用基本能力**，不是某个 studio。

---

## 1. 三个统一（把"不同的东西"收成"同一本质的实例"）

| 维度 | 唯一抽象 | 实例（只是配置/数据） |
|---|---|---|
| **执行** | **GA（一个运行时）** | chat run / studio run 全跑它；GA run 本身就是 job |
| **模型** | **kokoro-model（一个注册表，所有厂商所有模态）** | GPT/Claude(LLM) · Suno(音乐) · 某(图片/视频) 全平级 |
| **能力** | **Capability（GA 可调用）** | tools · skills · MCP · subagents · **调某模型（含媒体）** |
| **货币** | **credit（一种）** | 对话/音乐/图片 按 featureKey 计，同一 hold/settle |
| **产物** | **artifact（一个库）** | 文本/音频/图片/视频 同一库，按 studio/project 归类 |
| **surface** | **通用 Chat / 通用 Studio 框架** | Music/Image = 两份 Studio 配置 |
| **商业** | **Plan（一个抽象）** | 免费/积分包/订阅（见货币化 spec） |

**kokoro-model 是所有模型的家**（你的定调）：一个音乐模型就是一个模型，和 LLM 走同一套 label/binding/provider/凭据/网关。
媒体不是"另接一个 provider 网关"，是**kokoro-model 多一种模态的模型**；能力调它、GA 编排它，与调 LLM 同构。

---

## 2. Studio 通用：一份配置，不是一套代码

通用 Studio 框架 = 读配置渲染控制面 + 组装一次 GA run：
```
{ surface布局: 左参数/右预览/下版本, 参数schema: {…}, 调用: 指定 kokoro-model 的某模型 + featureKey, 产物类型: … }
```
- **Image Studio** = 图片模型 + 图片参数(尺寸/风格/张数/参考图) + 图片 featureKey。
- **Music Studio** = 音乐模型 + 音乐参数(时长/风格/歌词/人声) + 音乐 featureKey。
- **加 Video/Code = 再加一份配置 + kokoro-model 里注册对应模型**，框架/GA/credit/artifact **零改动**。

Chat 是另一个通用 surface：对话 → GA 自主从能力池选（含媒体能力）→ 产物卡回对话。**反哺=自动**（同一 GA、同一能力池、同一 kokoro-model）。

---

## 3. 落位（全是现有层扩展，**无新服务、无平行 job**）

- **模型（含媒体）**：kokoro-model 注册所有模态模型 + provider/凭据（同 model key 口径）；网关调用（litellm 之于 LLM，媒体同理经网关/adapter）。
- **能力挂载**：hub 按 namespace（与 skills/MCP 同装配路径）。
- **执行/job/流式/durable/HITL**：kokoro-agent GA（现成，GA run 即 job）。
- **计费**：credit hold/settle + featureKey。**产物**：artifact 库。**供给**：卡密/订阅/包。
- **surface**：kokoro-web 通用 Chat + 通用 Studio 框架。

---

## 4. 执行序：**先打通通用基本能力，studio 才是配置**（你的定调）

1. **kokoro-model 收全模态**：模型注册表容纳"媒体模型"（音乐/图片），与 LLM 同构（label/binding/provider/凭据/网关调用）。
2. **能力调模型的通用链打通**：GA 能力池加"调某模型（含媒体）"这类能力，经 hub 挂载；run 按 featureKey 计费；产出落 artifact。**这条通用链打通=引擎成。**
3. **通用 Studio 框架**：读配置→控制面→组装 GA run→预览/版本/导出。
4. **Image Studio / Music Studio = 各一份配置**（图片先，最直观最快）。
5. **反哺自动**：能力已在池，chat 里 GA 自选即用。
6. 产物按 studio/project 归类（依赖组织纵深 workspace/project）。

> 依赖：媒体模型的 provider key（同"真模型 key"，你提供即真；先用单模型/mock 验证通用链）。

---

## 5. 待你确认（v3 收敛后几乎不剩）

1. **能力调媒体模型的形态**：GA 内置能力（provider 适配在 model 网关侧，GA 只"调 kokoro-model 的某模型"）——倾向此，最贴"共同本质"。
2. 其余（GA/Studio/模型/credit/artifact 统一 + 反哺自动 + 无新服务）**已随"共同本质"定死，不再是问题**。
