# Cowork（Claude Cowork）调研笔记

调研时间：2026-05-20
受众：Kokoro 项目设计/产品决策参考

---

## 身份判断

**选定：Claude Cowork（Anthropic 官方产品）**

- 全称：Claude Cowork，由 Anthropic 发布
- 定位：把 Claude Code 的 agentic 能力带到桌面，面向**非编码**的知识工作（研究、分析、运营、法务、财务）
- 关键时间线：2026-01-12 以 research preview 形式登陆 macOS（Max 订阅）→ 2026-02-10 加入 Windows → 2026-04-09 全 GA，覆盖 Pro / Max / Team / Enterprise 所有付费档
- 官方页面：
  - https://www.anthropic.com/product/claude-cowork
  - https://claude.com/product/cowork
  - https://support.claude.com/en/articles/13345190-get-started-with-claude-cowork
- 与 Claude Code 的关系：同源能力（agentic + 计划/审批 + 工具调用），形态从终端转到桌面 app；官方原话 "Cowork: Claude Code power for knowledge work"

**依据**
1. anthropic.com 和 claude.com 双域名都有官方产品页，URL 路径就是 `/product/cowork` / `/product/claude-cowork`，不是任何第三方
2. CNBC、Tom's Guide、DataCamp 等独立媒体在 2026-01 至 2026-04 间持续报道，与官方时间线完全吻合
3. 用户表述"Claude Code 系列的产品"与官方定位"Claude Code power for knowledge work"一致

**其他候选排除理由**
- `coworker.ai` / Coworker AI：独立公司，融资 $13M（Triatomic Capital 领投），产品形态是企业 SaaS（连 Salesforce/Slack/Jira 的 agent 平台），与 Claude/Anthropic 无关
- Flowith `Canvas Cowork`：第三方 skill，依附 Claude Code/Codex 输出，不是独立产品
- `CoWork OS` / `OpenCoworkAI/open-cowork`：开源 desktop agent 框架，命名借势，非 Anthropic 出品
- Microsoft `Copilot Cowork`：MS 与 Anthropic 合作产物，但姓 Copilot，不是 Claude 系列
- Anthropic 培训站 `anthropic.skilljar.com/introduction-to-claude-cowork`：印证官方产品身份

**置信度：高（0.95）。** 用户口中的 "Claude Code 系列产品" 与官方"Claude Code power for knowledge work"几乎逐词对应，候选里只有 Claude Cowork 能同时满足"Anthropic 官方"+"Claude Code 同源"两个条件。

---

## URL 列表

| 类型 | URL | 用途 |
|---|---|---|
| 产品官页（anthropic.com） | https://www.anthropic.com/product/claude-cowork | 产品定位 + FAQ |
| 产品官页（claude.com） | https://claude.com/product/cowork | hero + 功能截图 + CTA |
| 帮助中心：入门 | https://support.claude.com/en/articles/13345190-get-started-with-claude-cowork | UI 名词、模式切换、调度 |
| 帮助中心：电脑使用 | https://support.claude.com/en/articles/14128542-let-claude-use-your-computer-in-cowork | 权限模式 |
| 企业版博客 | https://claude.com/blog/cowork-for-enterprise（2026-04-08） | 企业插件、部署 |
| 调度功能博客 | https://claude.com/blog/dispatch-and-computer-use（2026-03-23） | scheduled tasks |
| 培训课程 | https://anthropic.skilljar.com/introduction-to-claude-cowork | 官方课程 |
| 独立教程（截图较多） | https://www.datacamp.com/tutorial/claude-cowork-tutorial | 三栏布局、权限弹窗、Artifacts pane |
| 媒体试用 | https://www.tomsguide.com/ai/i-tested-claude-cowork-anthropics-new-ai-feels-more-like-a-coworker-than-a-chatbot | 体验口径 |

---

## 布局速写

### 桌面 app 顶层（Claude Desktop 内）
- **顶部标签栏**：`Chat` / `Cowork` / `Code` 三态切换，Cowork 是其中一种 mode，不是独立 app
- 切到 Cowork 后整个工作区切换为 agent 形态

### Cowork 工作区（三栏式）
```
┌─────────────┬──────────────────────────┬───────────────────┐
│ 左侧 sidebar│  中央对话/输入区          │  右侧任务进度面板 │
│             │                           │                   │
│ • Settings  │  [对话历史 / 计划预览]    │  Step 1  ✓        │
│ • Connectors│                           │  Step 2  …running │
│ • Scheduled │  ┌────────────────────┐   │  Step 3  pending  │
│   (任务列表)│  │ 输入框              │   │                   │
│             │  │ ☐ Work in a Folder │   │  Artifacts pane   │
│             │  └────────────────────┘   │  (click 预览)     │
└─────────────┴──────────────────────────┴───────────────────┘
```

### 关键交互流
1. 输入目标 → 勾选 "Work in a Folder" → 弹**权限 modal**（read / edit / delete + One-time / Always Allow）
2. Claude 生成 **plan preview** → 用户 Approve / Refine / Redirect（"Review Claude's approach, then let it run"）
3. 执行中：右侧 panel **逐步勾掉 step**，Artifacts pane 实时累积产物
4. 遇到破坏性动作（如删除）→ 二次**审批 gate**，附"30+ duplicate files"这种数字摘要
5. 完成 → 文件落回用户指定 folder

### 调度任务（/schedule）
- 侧栏 `Scheduled` 入口或斜杠命令触发
- 人话 cadence：`every weekday at 8am`、`first Monday of the month`
- 后台跑，结果写盘

### 权限模式（全局）
- `Ask before acting`（默认）
- `Act without asking`
- 入口：Settings > Cowork（含全局 instructions 的 Edit/Save）

---

## 设计 tokens 印象（基于官页 + 媒体截图描述）

> 注：anthropic.com 与 claude.com 官页本身视觉简洁，**未在 HTML 里暴露具体色值/字号**，以下为基于公开素材的设计语言推断，强度比 token 表低。

| 维度 | 印象 | 置信度 |
|---|---|---|
| 主色 | 中性底（米白 / 接近 Anthropic 一贯的 off-white #F5F4EE 系），强调色克制；插画/截图里能看到蓝、绿（数据可视化用） | 中 |
| 文字 | sans-serif，标题/正文权重清晰分层；无明显衬线 | 中 |
| 圆角 | 微圆，非 pill 非 0；按钮和卡片都偏 subtle | 中（来自组件描述） |
| 间距 | section 之间生成式留白，组件内紧凑；典型 Anthropic 编辑式节奏 | 高 |
| 视觉语言 | clean + modern + 偏文档/数据感（文件树、CSV 元数据、Draft 文档预览常出现） | 高 |
| 图像 | 极少抽象插画，更多产品截图 / 数据 dashboard / 文件树 mockup | 高 |

**hero 文案锚定调性**
- "Delegate to Claude, delight in the result"（claude.com）
- "From delegation to deliverables"（anthropic.com）
- "Spend less time finding, formatting, and fixing"
- "Unlike Chat, Cowork lets Claude complete work on its own."

调性=**克制、可信、办公友好**，不卖萌不炫技，强调"交付完成"。

---

## 关键组件清单

按官页 + 帮助文档归并：

1. **Mode 切换 Tab**：Chat / Cowork / Code 顶部三态
2. **Plan preview card**：列出 Claude 的步骤计划，带 Approve / Refine
3. **权限 Modal**：read / edit / delete 三选项，One-time vs Always Allow
4. **Folder 选择 + "Work in a Folder" checkbox**：与输入框并排
5. **右侧 Task Progress Panel**：实时 step ticker，✓/…/pending 三态
6. **Artifacts Pane**：点击文件项可在右侧 inline 预览，不离开界面
7. **Approval Gate**：破坏性动作前的二次确认，附"做了什么/找到了什么"摘要
8. **Scheduled Tasks 列表**：cadence 自然语言展示
9. **MCP Connectors 区**：左侧 settings 入口，列 Google Drive / Gmail / DocuSign / FactSet 等
10. **Permission Mode 二选一开关**：Ask before acting / Act without asking
11. **Global Instructions 编辑区**：Settings > Cowork 下的 Edit/Save 文本块
12. **Tasks 列表 + ⋮ 菜单**：trash icon 批量删除
13. **Plugins**（企业）：跨域插件（financial / engineering / HR 等）

---

## Kokoro 可借鉴（3-5 条）

1. **三态模式切换 Tab**作为顶部一级导航
   Cowork 用 `Chat / Cowork / Code` 把"对话 / agent 任务 / 终端编码"三种交互范式作为同级选择，而不是塞进二级菜单。Kokoro 如果同时有"对话"和"任务式产出"两种形态，可以照搬这种**顶部模式切换**而不是 sidebar，降低用户认知负担。

2. **"任务进度面板"独立于对话流**
   把 step-by-step 的进度从对话气泡里拆出去，放右侧常驻 panel，✓/running/pending 三态可视。对话区只承载意图与结果，**过程透明但不噪音**。Kokoro 做 agent 形态时极推荐这一拆分。

3. **Plan-then-Approve 模式作为默认**
   Cowork 的 `Ask before acting` 是 GA 默认值，破坏性动作还要二次审批 + 摘要（"找到 30+ 重复文件"）。这套**人在环路 + 数字摘要**比"原地操作"更让用户敢放权。Kokoro 若涉及任何修改用户数据的能力，应抄这套两段式 gate。

4. **Artifacts Pane 内嵌预览**
   Claude 处理的所有文件以"产物"形式在右侧累积，点击即预览，不跳出。对 Kokoro 来说，这是一个比"附件列表"更高级的范式——**产物即一等公民**，对话只是产物的索引。

5. **自然语言 cadence 的 schedule UI**
   `every weekday at 8am` 这类输入比 cron / 日历控件门槛低得多。Kokoro 任何"定时/重复"功能可以直接抄这个交互（背后用 LLM 解析即可）。

---

## Kokoro 应避开（2-3 条）

1. **不要把 Cowork 的"克制中性 + 文档感"直接照搬**
   Anthropic 的视觉是企业可信任品牌策略的产物（off-white + sans + 数据截图），换个产品形态会显得寡淡。Kokoro 若想要识别度，需要自己的强调色/排版个性，不要无脑 clone 米白底 + 极简。

2. **不要在主界面塞 4+ 列**
   Cowork 已经是"左 sidebar + 中央 + 右 panel"三栏，桌面 13" 下其实已偏挤。Kokoro 若想做 web 端，三栏要慎重，**优先两栏 + 抽屉式右 panel**，否则移动响应式直接崩。

3. **不要省略权限/审批的视觉重量**
   Cowork 的权限 modal、Always Allow 选项、删除二次确认是**功能正确但 UI 容易做轻**的地方。如果 Kokoro 走 agent 路线，必须给"授权"和"危险动作"专门的视觉层级（颜色、字号、按钮 hierarchy 都要区分），不要做成普通 confirm 弹窗。

---

## 数据来源置信度

| 维度 | 置信度 | 说明 |
|---|---|---|
| 产品身份 | 0.95 | 双官域 + 多家独立媒体一致 |
| 时间线 / 可用性 / 价位 | 0.9 | 官方博客与媒体口径一致 |
| 顶部三态 Tab + 三栏布局 | 0.85 | DataCamp 教程明确描述，官页截图佐证 |
| Plan-Approve / 权限 Modal | 0.9 | Anthropic 帮助文档直接给了 UI 名词 |
| 调度 / Artifacts Pane | 0.8 | DataCamp + Anthropic 博客 |
| **设计 tokens（色值/字号/圆角具体数值）** | **0.5** | 官页 HTML 未暴露 token，结论是基于素材印象 + Anthropic 既有品牌一致性推断，**不要拿来当像素级标准** |
| 企业插件 / Connectors | 0.85 | 官博明确列举（Google Drive / Gmail / DocuSign / FactSet） |

**总评**：身份与交互骨架可信度高，**视觉 token 级别需要看真实截图/Figma 才能确认**。如果 Kokoro 要做更细的视觉对标，建议直接安装 Claude Desktop 体验 Cowork mode 一次。
