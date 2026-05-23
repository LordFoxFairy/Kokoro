---
status: 🟡 草稿
updated: 2026-05-20
---

# 权限层级总览（架构层）

> 本文件是 **架构视角**：Kokoro 的权限分几层、各层管什么、用户从哪个入口接触。
> **实现视角**（每层具体规则、deny / ask / allow 语义、UI 弹框形态）见 [09-safety/permission-model.md](../09-safety/permission-model.md)。
> 两文互链，不重复内容。

---

## 一句话模型

Kokoro 的权限有**三层**，从外向里：

```
┌─────────────────────────────────────────────────────┐
│ 1. UI 权限    "用户能进哪些区域"                     │
│    (Who can see what)                               │
├─────────────────────────────────────────────────────┤
│ 2. 数据权限   "哪些操作能读 / 写哪些资源"            │
│    (Who can do what to data)                        │
├─────────────────────────────────────────────────────┤
│ 3. Agent 权限 "Kokoro 自己能调哪些工具"              │
│    (What Kokoro is allowed to do on behalf of user) │
└─────────────────────────────────────────────────────┘
```

层与层正交（一个动作可能同时穿过三层）。用户在每一层有不同的入口与心智。

---

## 第 1 层 · UI 权限（区域可见性）

**回答**："这个用户能不能看到 / 进入这个界面区域？"

**典型例子**：

| 场景 | 决策 |
|---|---|
| 未登录用户访问主页 | 看落地页，看不到 Sidebar |
| 普通用户访问"团队管理"页 | 跳转或隐藏入口 |
| 免费用户访问"模板高级筛选" | 入口可见但点击提示升级（不是隐藏） |
| 被分享 Canvas 链接的访客 | 只看 Canvas 内容，看不到 Sidebar |

**控制粒度**：路由 / 区段 / 按钮可见性。

**用户心智**：用户**不需要意识到这一层的存在**。"看不见就是没有"是 UI 权限的默认体感。

**设计原则**：
- 不要靠"按钮变灰 + 弹框升级提示"砸用户（违反心路线）
- 高级功能：入口轻量保留，点击时柔和说明（参考 [voice-and-tone.md](../02-personality/voice-and-tone.md) 的"限制"场景）
- 完全无权访问的区域：直接隐藏入口，避免引起好奇

---

## 第 2 层 · 数据权限（资源读写）

**回答**："对这个具体资源（对话 / Canvas / 模板 / 设置），这个用户能做什么？"

**操作分类**（参考 Claude Code 的 tier 化思路）：

| Tier | 操作 | 默认 |
|---|---|---|
| **只读** | 浏览自己的对话 / Canvas / 设置 | 不需要二次确认 |
| **写自己的** | 改自己的 Canvas / 删自己的对话 / 改自己的指令 | 不需要二次确认（除"删除"类） |
| **不可逆操作** | 永久删除、清空记忆、删账号 | 必须二次确认 |
| **写他人的 / 共享资源** | 在共享 Canvas 协作、改团队模板 | 视协作角色（owner / editor / viewer） |
| **跨账号 / 跨数据源** | 把私有内容发布为公共模板、把 Canvas 导出到第三方 | 必须显式批准 + 落审计日志 |

**最小示例**：

```yaml
# 资源：用户 A 的 Canvas "毕业海报"
permissions:
  user_A (owner):         [read, write, delete, share]
  user_B (invited editor): [read, write]
  访客（带分享链接）:       [read]
  搜索引擎（OG image）:    [read meta only]
```

**用户心智**：
- 用户**应该意识到**自己在"分享 / 公开"。这一层的关键 UX 是**让用户清楚自己刚做的操作影响了多少范围**
- 心路线注脚："已分享"的提示要平静且明确，不要"分享成功！🎉"

---

## 第 3 层 · Agent 权限（Kokoro 自己能做什么）

**这是 AI 时代独有的一层**——传统软件不需要。

**回答**："Kokoro 在帮我做事时，能调哪些工具 / 改哪些东西 / 访问哪些外部资源——不需要先问我？"

**典型工具类别**（参考 Claude Code 的 tier 化默认）：

| 类别 | 例子 | 默认策略 |
|---|---|---|
| 内省 / 阅读 | 读历史对话、读当前 Canvas、读用户指令 | 永不询问 |
| 改 Canvas | 编辑当前 Canvas 内容 | 视 [Mode](./modes.md) 决定（Default 询问 / Auto 不问） |
| 外部读取 | Web 搜索、抓取 URL、读用户授权的云盘 | 第一次询问，之后记住域名 |
| 外部写入 / 副作用 | 发邮件、发推、导出到他方平台、付费动作 | **每次询问** |
| 危险操作 | 永久删除对话 / Canvas、清空记忆、解除集成 | **每次询问**（即使 Auto mode） |

**与 Mode 的关系**：
- 如果选 [modes.md](./modes.md) 候选 C，Mode 就是 Agent 权限的"档位切换器"
- `Plan` → Agent 权限严格收紧（只读）
- `Default` → 大部分写操作要询问
- `Auto` → 大部分写操作不问，但**危险操作仍弹框**（circuit breaker，参考 Claude Code 的 `rm -rf /` 永远 prompt）

**用户可见入口**：
- 设置页 → "Kokoro 可以做什么" 区
- 每次 Kokoro 调工具时输入框上方一行极淡提示（不打断对话主流）
- 弹审批时：明确说做什么（"我想访问你的 Google Drive 找那份策划")，说为什么需要，给"只这次 / 总是允许 / 拒绝"三选项

**最小示例**：

```yaml
# 用户 A 的 Agent 权限策略
agent_permissions:
  read_my_canvases:        always_allow
  read_my_history:         always_allow
  edit_canvas:             ask_each_time  # 取决于 Mode
  web_search:              always_allow
  fetch_url(*.notion.so):  always_allow   # 用户某次"总是允许"过
  fetch_url(*):            ask_each_time
  google_drive:            disconnected   # 未授权集成
  send_email:              ask_each_time
  delete_canvas:           ask_each_time  # 即使 Auto mode
```

**心路线注脚**：审批弹框文案要像朋友请示，不像系统警告：
- ✅ "我想去翻一下你 Notion 里的旧策划，可以吗？"
- ❌ "Permission required: access third-party service [notion.com]"

---

## 三层的交叉示例

**场景**：用户 B（被邀请进 Canvas "毕业海报"的协作者）让 Kokoro 把这份 Canvas 导出到 Google Drive。

| 层 | 检查 | 结果 |
|---|---|---|
| 1. UI 权限 | B 能进这个 Canvas 页面吗？ | 能（被邀） |
| 2. 数据权限 | B 能读 Canvas 内容？能触发"导出"操作？ | 读：能（editor 角色）；导出：取决于 owner 设置 |
| 3. Agent 权限 | Kokoro 现在能调 Google Drive 工具吗？ | 取决于 B（不是 owner A）授权过没有 |

三层都通过才能执行。任何一层卡住，给出对应该层的解释。

---

## 设计原则（贯穿三层）

1. **可见 > 隐式**：用户应能在设置里看清三层各自的状态，不要藏
2. **可撤销 > 阻止**：能撤回的操作让用户做了再后悔（参考 Claude Code 的 Esc Esc 撤回 + checkpoints）
3. **解释 > 弹框**：被卡住时，告诉用户"为什么"和"怎么解"，不要只说 "denied"
4. **询问要稀疏**：宁可第一次问详细一点，不要每次都问。"总是允许"的回忆要可信
5. **心路线语气**：参考 [voice-and-tone.md](../02-personality/voice-and-tone.md) 的"限制/不能做"场景

---

## 待你拍板

- [ ] MVP 是否三层全做？倾向：第 1 层 + 第 3 层做，第 2 层先做"个人 / 已分享 / 公开"三态，团队协作权限矩阵留到 v2
- [ ] Agent 权限的存储粒度：按工具粗粒度（如 `web_search`），还是按 tool + 参数（如 `fetch_url(*.notion.so)`）？倾向**两层都支持**，初期只暴露粗粒度给用户
- [ ] 是否做"审计日志"页面给用户看 Kokoro 做过的事？倾向**做**，对应心路线"内观"叙事，且配合 Auto mode 必不可少
- [ ] "总是允许"的存储位置：用户级 vs session 级？倾向**用户级**，但敏感工具（导出 / 发邮件）强制 session 级失效

---

## 关联

- [ia.md](./ia.md) — 信息架构（哪些区域属于第 1 层 UI 权限）
- [navigation.md](./navigation.md) — Sidebar 各入口的可见性策略
- [modes.md](./modes.md) — Mode 与 Agent 权限的对应
- [memory-and-context.md](./memory-and-context.md) — 持久层 3b "AI 自学"属于数据权限的子域
- [09-safety/permission-model.md](../09-safety/permission-model.md) — **实现层**：具体规则、deny/ask/allow 语义、弹框形态、protected paths
- [02-personality/voice-and-tone.md](../02-personality/voice-and-tone.md) — 审批 / 拒绝 文案的语气
- [research/claude-code/learnings/04-safety-and-surfaces.md](../../research/claude-code/learnings/04-safety-and-surfaces.md) — 灵感来源（tier 化默认、circuit breaker、protected paths）
