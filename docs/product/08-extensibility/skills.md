---
status: 🟡 草稿
updated: 2026-05-20
---

# Skills

> Skills = Kokoro 的「行为模板」。一个 skill 就是一段我可以被触发去做的预设工作流。
> 设计灵感直接来自 Claude Code——他们把 slash commands 合并进了 skills，证明这两件事在产品上就是同一件事：**一段可命名、带描述、能被手动也能被自动触发的预设文本**。

---

## 0. 一句话

写一个 skill = 写一份 markdown，告诉我什么时候该用它、用的时候该怎么做。

放进 skills 目录我就看到了，能在 `/` 菜单里被你手动调，也能在你描述任务时被我自动想起来。

---

## 1. 为什么是 Skills 而不是「命令系统」

Claude Code 走过弯路：早期 `.claude/commands/*.md` 和 `.claude/skills/*/SKILL.md` 是两套并列机制，一套是用户手动 `/cmd`，一套是 LLM 自动触发。最近他们把命令合并进了 skills，理由是「两套语法在做同一件事，宁可破坏向后兼容也要收敛」。

Kokoro 一上来就只做一个抽象。**Skills 是 Kokoro 唯一的「可命名、可触发的预设行为单元」**。

- 想手动叫我做什么 → 写 skill，用 `/` 触发
- 想让我在合适场景主动想起做什么 → 写 skill，描述写好让我能匹配
- 想分享给别人 → 也是 skill，因为本来就只有一种东西

不再有「命令 vs skill」、「模板 vs 预设」的纠结。

---

## 2. Anatomy

一个 skill 是一个文件夹（最简情况就一个 `SKILL.md`）：

```
my-skill/
├── SKILL.md           # 必需，主入口
├── reference.md       # 可选，按需加载的详细资料
├── examples/          # 可选，示例 Canvas / 示例对话
└── assets/            # 可选，需要的图、字、模板片段
```

`SKILL.md` 自身保持精简（建议 ≤ 200 行），重资料拆到附属文件。这样我加载时只把主文件吞进 context，需要细节再去看附件。

### Frontmatter 字段

```yaml
---
name: 海报排版
description: 用户想做一张海报、传单、Banner 时用我。我会给出版面方案再落到 Canvas。
trigger:
  manual: /poster
  auto:
    - 帮我做一张海报
    - 设计一个 banner
canvas-type: poster        # 可选，限定到某种 Canvas
tone: warm                 # 可选，覆盖默认 voice
allowed-tools: [Canvas.Edit, Web.Search]  # 可选，白名单
version: 1
---
```

关键字段说明：

| 字段 | 作用 |
|---|---|
| `name` | 显示名，菜单里能看到 |
| `description` | **最重要**。我用它判断该不该自动触发。写得清楚 = 触发得准 |
| `trigger.manual` | 用户输入的命令字 |
| `trigger.auto` | 自动触发的语义示例（可省，留空 = 不自动触发） |
| `canvas-type` | 这个 skill 只在某种 Canvas 上才出现 |
| `tone` | 临时覆盖语气（如 `serious` / `playful` / `warm`） |
| `allowed-tools` | 这个 skill 跑起来能用哪些工具，超出就要二次确认 |
| `version` | 版本号，社区分享时区分 |

### 正文

正文就是一段 markdown 写给我看的说明书。我建议结构：

```markdown
# 海报排版

## 什么时候用我
当用户想做单页静态视觉物（海报、Banner、传单、活动卡片）时。

## 我会做什么
1. 先问清主图情绪、用途场景、主标语
2. 给 3 个版面方向（满版图、留白排版、几何拼贴）
3. 用户选一个之后落到 Canvas，主色用心人格暖调

## 我不做什么
- 不做多页（多页转给「文档排版」skill）
- 不做动效海报（v2 再说）

## 心人格备忘
不要一上来就生成。先确认情绪和用途。错一稿成本比多问一句高。
```

---

## 3. 最小例子

用户想给自己写一个「日记结构化」skill。文件 `~/.kokoro/skills/journal/SKILL.md`：

```markdown
---
name: 整理日记
description: 用户输入一段散乱日记或语音转写，希望整理成有结构的回顾。
trigger:
  manual: /journal
  auto:
    - 帮我整理今天的日记
    - 把这段碎碎念整理一下
---

# 整理日记

把用户输入按 **「今天发生了什么 / 我感觉到了什么 / 我想记下的一句话」** 三段重写。
保留原话里有温度的细节，不要把"今天有点累"改成"今日感受疲惫"。
不评判，不建议，不安慰。只整理。
```

把这个文件放好之后：

- 用户输 `/journal` → 我激活这个 skill
- 用户说「帮我整理今天的日记」→ 我也激活
- 用户说「我今天写了点东西，看看？」→ 我可能激活（看 description 匹配度）

---

## 4. Skill 的来源

| 来源 | 例子 | 安装方式 |
|---|---|---|
| **内置** | 海报排版 / 文档结构化 / 课件大纲 / 整理碎念 | 跟 Kokoro 一起出厂 |
| **用户自创** | 「整理日记」「写每周复盘」 | 在 skills 库点「新建」或直接放文件 |
| **社区分享**（v2+）| 别人写的「读论文 + 出脑图」 | 模板市场点「装上」 |

内置 skill 用户也能看到源文件，可以 fork 改成自己的。

---

## 5. Skill 跟 Template 的区别

经常会混。说清楚：

| | Skill | Template |
|---|---|---|
| **是什么** | 行为模板，描述「我该怎么做这件事」 | 产物模板，描述「成品长什么样」 |
| **触发** | 通过 `/cmd` 或语义匹配 | 在「新建 Canvas」时被选中作为起点 |
| **产出** | 一段对话 + 一个 Canvas | 一个 Canvas 文件 |
| **核心** | prompt + 步骤指令 | 已经填好结构的 Canvas |
| **类比** | "请按这个流程做" | "复制这份给我做基底" |

举例：「OKR 海报」是 template（已经排好版的 Canvas 半成品）；「帮我做一张 OKR 海报」是 skill（指挥我去问需求、出方案、落 Canvas 的流程）。

一个 skill 内部可以**引用**一个 template 作为起点，但它们是两种东西。

---

## 6. 触发机制详解

每个 skill 有两个触发入口：

### 手动触发：`/`

用户在输入框打 `/`，弹出补全菜单，按 description 排序。选中 skill 后：
- 如果 skill 有参数（`{{topic}}` 之类的占位符），让用户填
- 没参数就直接进 skill 主体

### 自动触发：语义匹配

我会在你说话时，把当前消息和所有可用 skill 的 description 对一遍。匹配到了：
- **高置信**（明显匹配）→ 静默激活，但在我的回复底部告诉你「我用了 /poster 这个 skill」
- **低置信**（可能匹配）→ 先问你「我觉得这事像是想做海报，要不要走 /poster 的流程？」

可以在设置里关掉自动触发，或针对某个 skill 单独关。

### 谁能调

| 配置 | 用户能 `/` 调 | 我能自动调 |
|---|---|---|
| 默认 | ✅ | ✅ |
| `trigger.auto` 留空 | ✅ | ❌ |
| `trigger.manual` 留空 | ❌ | ✅ |
| 都留空 | 这个 skill 没意义，会报错 |

---

## 7. 存放层级（precedence：高 → 低）

| 层 | 路径示意 | 谁能写 |
|---|---|---|
| 当前对话 | session-local | 我临时生成的 ad-hoc skill |
| 项目级 | `<workspace>/.kokoro/skills/` | 当前工作区有效 |
| 用户级 | `~/.kokoro/skills/` | 你自己 |
| 团队级（v2+） | 团队空间 | 团队 admin |
| 官方 | 内置 | Kokoro 团队 |

同名时高层覆盖低层，但低层依然能在管理界面看到（标"被覆盖"）。

---

## 8. v1 / v2 范围

### v1（MVP+）

- 内置 5-8 个 skills（覆盖首发主打 Canvas 类型）
- 用户可以 `/` 手动触发
- 用户可以自创 skill（界面化新建，frontmatter 字段以表单形式呈现）
- **不开放**社区分享 / 安装第三方 skill

### v2

- 自动触发（语义匹配）
- 社区市场（浏览 / 安装 / 评分）
- skill 内引用 template
- skill 内调用 plugin / MCP 工具（联动 plugins.md / mcp.md）

> ⚠️ **待你拍板**：`feature-map.md` 把 Skills 系统标在 v1，但 v1 的范围是「只能手动 + 不开放社区」还是「连自动触发也包含」？影响**通用 agent**叙事的完整性——只手动调的 skill 偏「快捷指令」，加上自动触发才是真正的「agent 行为系统」。

---

## 9. 设计纪律

每个 skill 加进 Kokoro 前过一遍：

1. **description 能让我准确判断要不要用吗？**——这是 skill 触发质量的命根
2. **它描述的是「怎么做」还是「成品长什么样」？**——后者属于 template，不属于 skill
3. **没有它，用户直接说自然语言会少做到什么？**——如果答不出，这个 skill 不该存在
4. **它的语气和心人格冲突吗？**——内置 skill 必须服务心人格；用户自创不强制

---

## 关联

- [commands.md](./commands.md) — 命令 = skill 的手动触发面
- [plugins.md](./plugins.md) — plugin = 带代码的扩展，skill = 带 prompt 的扩展
- [mcp.md](./mcp.md) — skill 内可调用 MCP 工具（v2+）
- [../03-product-form/feature-map.md](../03-product-form/feature-map.md) — Skills 优先级
- [../../research/claude-code/learnings/02-extensibility.md](../../research/claude-code/learnings/02-extensibility.md) — 借鉴来源
