---
status: 🟢 已定（架构方向锁定；MVP 范围与命名待落地时定）
locked-by: ADR-003
updated: 2026-05-21
---

# 模式（Modes）：要不要做顶部 mode tab？

> 🟢 **已锁定**（[ADR-003](../../decisions/ADR-003-mode-model.md)）：**选 C（信任档位 Mode）**。
> 不做顶部三态 tab；Chat / Canvas / Agent 保持隐式自动触发。Mode 表达"对 Kokoro 的信任档位"——Plan / Default / Auto 三档。MVP 只做 Default。
> 切换入口位置与中文名称待原型落地时定。

> 这是 [ia.md](./ia.md) 末尾「是否需要模式切换顶部 tab？」这道题的展开。
> 决策结果会反向影响 [navigation.md](./navigation.md)（是否要给 sidebar 之外再让出顶部空间）和 [09-safety/permission-model.md](../09-safety/permission-model.md)（mode 是否承担权限语义）。

---

## 问题

Kokoro 同时承担三件事：
1. **Chat**——纯对话、问答、思考
2. **Canvas**——视觉产物（文档 / 海报 / 课件）
3. **Agent**——多步执行、调工具、跑命令

用户在这三件事之间切换的方式有三种候选。**选哪种会决定产品的第一印象**——是"一个简洁的 AI"还是"一个有模式的工作台"。

---

## 三个候选

### 候选 A · 不做 mode tab，状态隐式（Gemini 风格）

界面上没有任何"模式选择器"。用户只看到一个输入框：
- 直接说话 → Chat
- 让 Kokoro 做产物 → 自动触发 Canvas 三栏
- 让 Kokoro 跑多步 → 自动进 Agent 流（出现 plan / progress UI）

**心智**：用户无须学。"Kokoro 自己懂该用哪种形态。"

**Tradeoff**：
- ✅ 入门门槛最低；符合心路线"克制"
- ✅ 与 Claude Code 的 *"You don't have to manually add context"* 哲学一致
- ❌ 老手想强制"只 chat 不要画 Canvas"或"只 plan 不要直接动手"时没有显式入口
- ❌ Agent 任务在结束前用户难以预知"它要跑多久 / 要不要批准"

### 候选 B · 顶部三态 tab（CoWork 风格）

主区顶部一条 tab：`[Chat] [Canvas] [Agent]`，三态互斥。

**心智**：用户先选场景再开始。

**Tradeoff**：
- ✅ 用户预期明确，知道现在在哪个上下文
- ✅ 营销好讲（"我们有三种模式"）
- ❌ 强迫用户做选择，违反"心"路线的不打扰
- ❌ 三件事其实经常混着发生（聊着聊着开 Canvas，写 Canvas 时让 Agent 找资料），硬切会断裂
- ❌ 与 Sidebar 的"新对话"叙事冲突：到底是"新对话"还是"新 Canvas"？

### 候选 C · Mode = Permission Mode（Claude Code 风格）

Mode 不表达"我在做什么类型的任务"，而表达"**我允许 Kokoro 做到什么程度**"。借鉴 Claude Code 的 `default` / `acceptEdits` / `plan` 三档：

| Mode | 含义（Kokoro 化译） | 行为 |
|---|---|---|
| **Plan**（计划） | "先告诉我你想怎么做" | 只 read；任何"改 Canvas / 跑工具"前必须先给 plan 等用户批 |
| **Default**（默认） | "改之前问我一下" | 改 Canvas / 调工具 / 发送外部请求都弹审批 |
| **Auto**（自动） | "你来吧，我看着" | 不弹审批，但每个动作给可见的 timeline + 一键回滚 |

切换位置：输入框右下角小指示器（不顶部 tab），按 ⇧Tab 循环（学 Claude Code）。

**心智**：Mode 不是"我要什么"，而是"我对 Kokoro 的信任档位"。Chat / Canvas / Agent 仍然隐式自动触发。

**Tradeoff**：
- ✅ 与心路线高度契合："沉静地把权交出去，但有节奏"
- ✅ 老手可以一键切到"Auto"放手，新手默认在"Default"被 Kokoro 询问
- ✅ 与 [permissions.md](./permissions.md) 的架构直接咬合
- ✅ 任务类型保持隐式自动（A 的优点保留）
- ❌ 比 A 多一个概念，新用户需要学一次"什么是模式"
- ❌ 切到 Plan 时用户可能误以为"只能 Chat 不能 Canvas"——需要文案对齐

---

## 对照表

| 维度 | A 隐式 | B 三态 tab | C 信任档位 |
|---|---|---|---|
| 入门门槛 | 最低 | 较高 | 中 |
| 老手控制感 | 弱 | 强（但僵） | 强（且柔） |
| 心路线契合 | 高 | 低 | 最高 |
| 营销叙事 | "懂你" | "三种模式" | "你定节奏" |
| Sidebar 配合 | 顺 | 拧 | 顺 |
| 权限语义 | 隐式 | 无 | 一等公民 |
| 实现复杂度 | 低 | 中 | 中-高 |
| 与 Claude Code 哲学一致 | 部分 | 否 | 是 |

---

## Claude 推荐

**倾向候选 C（信任档位 Mode）**，理由：

1. **A 的优点 C 全保留**：Chat / Canvas / Agent 仍然隐式自动触发，用户不用预先选场景
2. **C 把"控制感"从"任务切换"挪到"信任程度"**——这恰好是 AI agent 时代真正稀缺的 UX 维度（A 没解决，B 解错了题）
3. **与心路线天然契合**：心路线的核心不是"温柔卖萌"，而是"克制、内观、节奏感"。Mode 表达"节奏"刚好对位
4. **可向后兼容**：MVP 可只做 `Default`，Plan 和 Auto 后续加，不破坏架构
5. **与 [permissions.md](./permissions.md) 共享语义**：UI 层的 mode 切换 = Agent 权限层的策略切换，少一个概念

C 的两个风险都可控：
- "比 A 多一个概念"——通过文案让"Mode"看起来不像设置（不叫"模式"，叫"节奏" / "信任"等更人格化的词，待定）
- "Plan 易被误解"——空状态文案明确说"Plan 模式下 Kokoro 会先给你看草稿再动手"

---

## 待你拍板

- [ ] **拍 A / B / C 哪一个**
- [ ] 若选 C：MVP 是否只做 `Default` 一档，先不出 Plan / Auto？
- [ ] 若选 C：Mode 在 UI 上叫什么名字（"模式" / "节奏" / "信任档" / 英文 "Mode"）？
- [ ] 若选 C：切换位置（输入框右下 vs 顶栏右上 vs sidebar 底部）？
- [ ] 若选 B：三个 tab 的中文怎么叫？（"对话 / 画布 / 任务"？）

---

## 关联

- [ia.md](./ia.md) — 待答题来源
- [navigation.md](./navigation.md) — Sidebar 是否要给顶部 tab 让位
- [permissions.md](./permissions.md) — 若选 C，Mode 与权限层共享语义
- [memory-and-context.md](./memory-and-context.md) — Mode 是否影响 context 管理（如 Plan mode 是否额外保留 plan 历史）
- [09-safety/permission-model.md](../09-safety/permission-model.md) — Permission mode 实现细节
- [Claude Code permission-modes 学习](../../research/claude-code/learnings/04-safety-and-surfaces.md) — C 候选的灵感来源
