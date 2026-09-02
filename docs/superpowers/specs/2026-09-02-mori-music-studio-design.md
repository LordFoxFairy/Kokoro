# Mori Music Studio 设计基线

> 状态：draft，等待产品确认
> 日期：2026-09-02
> 品牌：Mori
> 产品仓库：`kokoro-mori`
> 共享仓库：`kokoro-web-shared`

## 1. 目标与边界

Mori 是 Kokoro 体系中的专业音乐创作产品。它不是在通用 Kokoro 页面上增加一个
`music` 模式，而是拥有独立的信息架构、品牌视觉、音乐对象模型和发布生命周期的
兄弟产品。

第一阶段只打磨一个稳定闭环：

```text
描述想法 → 生成候选 → 对比试听 → 选定版本 → 编辑/导出 → 回到项目继续创作
```

本设计阶段锁定页面结构、对象关系、共享边界和 API 原则；不在 UI 中绑定任何单一
供应商，不把 Suno/Tad 的私有字段泄漏为公开业务契约，也不在未确认 API 前开始大规模
实现。

## 2. 参考结论

### 2.1 借鉴 Suno 的能力骨架

- 左侧稳定导航，核心入口集中在 Create、Studio、Library。
- Simple/Advanced 两档创作入口，先让一句话生成成立，再渐进展开专业控制。
- 生成结果以候选作品为中心，而不是一条不可追溯的聊天消息。
- 播放器、队列、版本操作贯穿工作区。
- 作品详情支持歌词、标签、分享、下载和版本管理。

### 2.2 吸收 Tad 的专业控制

- Smart/Custom 双模式。
- Reference、Remix、Edit 等后续创作动作。
- Lyrics/Instrumental、Style、Voice、Duration、Advanced Settings。
- Genre、Vibe、Instrument、Scene、Rhythm 等可组合标签。

### 2.3 采用 Lessie 的浅色质感

- 默认浅色，不采用深色音乐软件常见的黑底方案。
- 大面积温暖留白，渐变只用于背景氛围、重点按钮和波形状态。
- 白色内容卡片、弱边框、轻阴影、低密度视觉噪声。
- 衬线字体只用于品牌、欢迎语和空状态；编辑器、标签、数据使用无衬线字体。

参考的是能力组织和视觉原则，不复制页面代码、品牌素材或逐字文案。

## 3. 核心信息架构

### 3.1 组织原则

采用 **Project-first + Creation lifecycle**：用户始终围绕一个项目积累草稿、生成任务、
候选、版本、歌词、音频引用、stem 和导出物；复杂工具只在相关项目上下文中出现。

### 3.2 全局导航

```text
Mori
├── Create       新建创作，默认入口
├── Projects     项目列表，按最近活动排序
└── Library      作品、音频、歌词和导出物

项目上下文内
├── Overview     项目摘要、候选和最近版本
├── Generate     生成配置与任务队列
├── Studio       已有版本的编辑工作区
├── Stems        分轨与音频资产
└── Export       导出与分享
```

`Studio` 不作为进入产品时的空白独立页面。只有存在项目和版本后才进入 Studio，
避免自动创建空项目造成初始化失败，也让 Studio 成为真实对象的编辑上下文。

### 3.3 页面职责

| 页面 | 用户问题 | 主要内容 |
|---|---|---|
| Create | 我现在想做什么？ | Smart/Custom 创作卡、参考音频、最近项目 |
| Projects | 我在做哪些作品？ | 项目卡、状态、最近版本、继续创作 |
| Project Overview | 这个项目现在到哪了？ | Song Plan、生成历史、候选、当前版本 |
| Generate | 我如何控制下一次生成？ | Prompt、Lyrics、Style、Reference、Voice、Duration |
| Studio | 我如何继续打磨这一版？ | 波形、段落、歌词、版本、分轨、编辑动作 |
| Library | 我如何找到可复用的资产？ | 作品、版本、音频、歌词、导出物、过滤器 |
```

### 3.4 URL 规则

```text
/create
/projects
/projects/{project_ref}
/projects/{project_ref}/generate
/projects/{project_ref}/studio/{version_ref}
/library
```

所有 `project_ref`、`version_ref` 都是 opaque reference。前端 URL 不承载 tenant、site
或内部 runtime namespace。

## 4. 工作台布局

```text
┌──────────────┬──────────────────────────────┬────────────────┐
│ Mori Rail    │ Create Canvas                │ Queue /        │
│              │                              │ Inspector      │
│ Create       │ Prompt / Lyrics              │                │
│ Projects     │ Reference / Style           │ Generation     │
│ Library      │ Smart / Custom              │ Candidates     │
│              │                              │ Version info   │
├──────────────┴──────────────────────────────┴────────────────┤
│ Persistent Player · waveform · transport · current version    │
└────────────────────────────────────────────────────────────────┘
```

### 4.1 左侧 Rail

- 品牌标识和 `New creation`。
- 仅放 3 个一级产品入口，避免把每个能力都变成导航项。
- 项目内显示上下文导航，而不是把 Stems、Export 等提升到全局。
- 小屏幕转为顶部菜单 + 底部播放器抽屉。

### 4.2 中央 Create Canvas

- Smart 模式：一句话描述即可生成。
- Custom 模式：显示专业字段，但保留默认值和渐进展开。
- 生成前明确展示预计耗时、消耗和当前模式。
- 一次提交产生一个 generation job，可返回多个 candidate。

### 4.3 右侧 Queue / Inspector

- 生成中：任务状态、进度阶段、取消、重试。
- 生成完成：候选列表、A/B 试听、收藏、设为当前版本、继续 Remix/Edit。
- 选中版本：标题、歌词、标签、来源引用、版本历史和导出动作。

### 4.4 底部 Persistent Player

- 当前播放版本、封面、波形、播放进度、音量和队列。
- 试听候选时保留生成上下文，不跳离当前页面。
- 播放器状态只属于浏览器 UI；作品和版本状态由服务端资源确认。

## 5. 创作流程

### 5.1 Smart

```text
输入一句话 → 生成 Song Plan 预览 → 用户确认/调整 → 提交 generation
```

Song Plan 是 Mori 的差异化中间对象，包含结构、情绪、速度、乐器、演唱方式和歌词
意图。它让一句话输入与专业编辑之间有可见的中间层，便于解释、修改和复用。

### 5.2 Custom

```text
Lyrics / Instrumental
Style + tags
Reference audio
Voice
Duration
Advanced settings
→ 生成候选
```

复杂字段采用 progressive disclosure。首屏只展示 Prompt、歌词/纯音乐切换、Style 和
生成按钮；Reference、Voice、Duration、Advanced 在需要时展开。

### 5.3 候选到版本

- generation 是一次请求的生命周期对象。
- candidate 是本次请求返回的可比较结果。
- version 是项目中可引用、可编辑、可导出的不可变音频快照。
- 用户执行 `Set current version` 后，项目获得新的 current version ref；旧版本仍可回溯。

## 6. 视觉系统初稿

### 6.1 基础 token

```text
background       #FBFAF8   温暖米白
surface          #FFFFFF   内容卡片
foreground       #25252A   主文字
muted            #77747B   次文字
border           #EAE7E3   弱边框
lavender         #EDE9FE   紫色氛围
peach            #FDE7DA   桃色氛围
mint             #E7F6EF   绿色氛围
primary          #6D5CE7   主操作
primary-soft     #F0EDFF   主操作浅底
success          #3D9B72
warning          #C58A32
error            #C95555
```

### 6.2 使用规则

- 页面背景使用 `background`，渐变作为低对比度 atmosphere layer，不干扰文字和表单。
- 卡片不堆叠玻璃效果；优先白底、弱边框和单层阴影。
- 主按钮可以使用 lavender → peach 的细渐变，但文字对比度必须满足可读性。
- 波形使用低饱和紫/桃渐变，播放进度使用实色提高识别度。
- 动效用于生成状态、波形和面板过渡，不用于装饰性持续闪烁。
- 默认 `color-scheme: light`；深色主题保留为未来可选 preset，不进入第一阶段验收。

## 7. 复用与拆分边界

### 7.1 从现有 Kokoro 保留并提取

| 资产 | 去向 | 处理方式 |
|---|---|---|
| `@kokoro/i18n` | `kokoro-web-shared` | 直接迁移，产品注入自己的词典 |
| `@kokoro/web-core` | `kokoro-web-shared` | 保留纯类型和资源/动作状态 |
| `@kokoro/tsconfig` | `kokoro-web-shared` | 保留工程基线 |
| shadcn/Radix primitive | `web-ui` | 只抽无业务基础组件 |
| Rail、Composer、ContextPanel 思路 | `web-blocks` | 改为 props/adapter 驱动，不抽 Mori 布局事实 |
| query、SSE、错误映射 | `web-data` | 只抽浏览器安全的契约和适配器 |
| runtime manifest 类型 | `web-runtime` | 只抽公开投影类型和主题协议 |

### 7.2 留在 `kokoro-mori`

- Mori 品牌、Logo、SEO、文案和浅色渐变 preset。
- 音乐 Project、Song Plan、Generation、Candidate、Version、Stem、Export 对象。
- Create/Studio/Library 页面组合方式。
- 音乐领域组件、音频播放器、波形、歌词编辑器和供应商无关的音乐交互。

### 7.3 明确不迁移

- 通用 Kokoro 的业务导航和非音乐页面。
- 当前聊天线程作为产品主对象的假设。
- 产品专属文案、素材、页面 CSS 和旧业务 API。
- Suno/Tad 的登录状态、内部接口、私有 token、反向工程字段或供应商分支。

## 8. API 契约草案

API 契约仍遵守现有 Kokoro 规则：浏览器只请求同源 `/api/*`，通过 BFF 进入业务 owner；
外部字段使用 `snake_case`；成功响应为 `{data, meta}`；错误响应为 `{error, meta}`；
每次响应包含可追踪的 `request_id`；写操作使用 `Idempotency-Key`；事件流使用 SSE 和
`Last-Event-ID`；前端不直连供应商。

### 8.1 初始资源

```text
Project
SongPlan
Generation
Candidate
Version
Asset
Export
```

### 8.2 初始端点方向

```text
POST /api/v1/projects
GET  /api/v1/projects
GET  /api/v1/projects/{project_ref}

POST /api/v1/projects/{project_ref}/song-plans
POST /api/v1/projects/{project_ref}/generations       → 202
GET  /api/v1/generations/{generation_ref}
GET  /api/v1/generations/{generation_ref}/events      → SSE
POST /api/v1/generations/{generation_ref}/cancel

GET  /api/v1/projects/{project_ref}/candidates
POST /api/v1/candidates/{candidate_ref}/promote       → version
POST /api/v1/versions/{version_ref}/remix
POST /api/v1/versions/{version_ref}/exports           → 202
GET  /api/v1/library
```

端点名称和字段在 UI/IA 确认后进入独立 API contract 文档。供应商 adapter 只在后端实现：

```text
Mori Web → same-origin BFF → Music owner → Provider adapter → Suno/Tad/other provider
```

公开契约只表达 Mori 的业务对象，不暴露供应商名称、供应商任务 id 或供应商状态枚举。

## 9. 错误与异步状态

Generation 状态统一为：

```text
queued → preparing → generating → post_processing → succeeded
                                      ├→ failed
                                      ├→ cancelled
                                      └→ expired
```

要求：

- 创建任务立即返回稳定 `request_id` 和 `generation_ref`。
- SSE 可从 `Last-Event-ID` 续传；断线后先回放再接收新事件。
- 同一 `Idempotency-Key` 重试返回同一个 generation receipt。
- 失败必须返回可见错误码、request id、是否可重试和 credit 处理结果。
- 取消只改变 Mori 任务状态；供应商取消由 adapter 尝试执行并记录结果。
- provider 不可用时，UI 呈现能力级错误，不把供应商错误文案泄漏给用户。

## 10. 第一阶段验收标准

- 默认打开即为浅色主题，任何主要流程不依赖深色背景。
- 用户能从 Create 在一个页面完成 Smart 生成配置和任务提交。
- 用户能在不离开当前页面的情况下比较至少两个候选并试听。
- 用户能把 candidate 提升为不可变 version，并继续进入 Studio。
- Studio 只在已有 project/version 上下文中打开。
- Projects 与 Library 能区分项目、候选、版本和导出物。
- 共享 package 与 Mori 产品代码没有反向依赖。
- 前端不包含 Suno/Tad 专属分支、token 或私有接口地址。
- API 契约具备 request id、幂等、异步状态和 SSE 回放语义。

## 11. 后续推进顺序

```text
本设计稿 → 你确认页面/视觉方向
         → 输出页面清单、状态矩阵和线框
         → 你确认 UI/IA
         → 输出完整 API contract
         → 你确认 API
         → 创建 kokoro-web-shared
         → 创建 kokoro-mori
         → 先做本地 preview fixture，再接真实 provider adapter
```

当前推荐先锁定三件事：

1. `Project-first` 是否作为 Mori 的唯一主对象模型；
2. Create 页面采用 Smart 默认、Custom 渐进展开；
3. 浅色米白 + lavender/peach/mint 渐变作为默认品牌视觉。

