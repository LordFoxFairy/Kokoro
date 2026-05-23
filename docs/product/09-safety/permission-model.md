---
status: 🟡 草稿
updated: 2026-05-20
---

# 权限模型（实现层）

> [04-architecture/permissions.md](../04-architecture/) 讲架构上"为什么要分层"；本文讲实现上"每一层长什么样、默认值、用户在哪改"。
> 主要素材来自 [Claude Code 学习笔记 04 · 安全与多端](../../research/claude-code/learnings/04-safety-and-surfaces.md)。
> 对应人格章节：心路线下的拒绝/打扰必须服务"温柔但不甩锅"，参见 [voice-and-tone.md](../02-personality/voice-and-tone.md)。

---

## 一句话

Kokoro 是通用 agent，会替用户跑工具、改 Canvas、调外部服务，所以权限不是一个开关，而是**三层防御**：

1. **Permission rules**（每个动作三态：deny / ask / allow）—— 谁能干什么
2. **Permission modes**（4 档：plan / ask / acceptEdits / auto）—— 打扰频率
3. **沙箱**（受限运行环境）—— OS 级兜底，模型说错话也不出事

三层独立，下一层兜上一层的漏。

---

## 第 1 层 · Permission rules

### 工具按敏感度分 tier

| Tier | 工具示例 | 默认行为 |
|---|---|---|
| 只读 | 读 Canvas、搜索 Library、Web 搜索 | 永不询问 |
| 写 Canvas | 改用户当前的 Canvas、新建草稿层 | 默认 ask（acceptEdits 模式后免审） |
| 调外部 | WebFetch、第三方 MCP server、给 Slack 发消息 | 必须 ask；首次 allow 后该域名/server 持续放行 |
| 危险 | 删除已发布模板、撤销公开分享、跨设备同步覆盖 | 永不进入"自动允许"，见 [circuit-breakers.md](./circuit-breakers.md) |

### 规则三态

- **deny**：直接拒绝，模型被告知"这件事我不能做"，主控继续别的事
- **ask**：弹询问 UI，用户点允许 / 拒绝 / 永久允许
- **allow**：跳过询问直接做

匹配顺序 **deny → ask → allow**，先匹配先决。这点照抄 Claude Code，对治"用户写了 allow，但还是希望某些 case 走 ask"的常见诉求。

### 最小规则示例（用户视角）

```yaml
# 用户设置里看到的样子（实际可视化为 UI，YAML 仅为内部示意）
permissions:
  deny:
    - WebFetch(domain:*.banking.example)   # 永远不要去银行类站点
    - Delete(/share/public/*)              # 已公开的分享链接不许删
  ask:
    - WebFetch(*)                          # 抓网默认弹审批
    - MCP(slack)                           # 第三方 server 默认问一次
  allow:
    - Canvas.edit(self)                    # 自己的 Canvas 自动改
    - Read(*)                              # 自己的 Library 自由读
```

### 一条规则的生效域

| 域 | 例 | 持续 |
|---|---|---|
| 一次（this turn） | 这次回答里允许跑这个 MCP 调用 | 当前轮次 |
| 一次会话（this session） | 本对话内不再问 | 至本会话结束 |
| 永久（always for this site / this Canvas） | 把规则写进用户 settings | 永久 |

询问 UI 的三选项就是上面三档，**默认是"一次会话"**（不要默认永久，那等于偷偷扩权）。

---

## 第 2 层 · Permission modes

Mode = 全局的"打扰频率档位"，决定上面这些 ask 规则现在算不算数。

### 4 档（建议初版只做这 4 档，不抄 CC 的 6 档）

| Mode | 自动允许的范围 | 还会问的范围 | 适用场景 |
|---|---|---|---|
| **Plan**（plan） | 只读 + 写"草稿层"，不动 Canvas 主稿 | 任何会落到主稿、外部服务、文件系统的事 | 探索/不确定要不要做时 |
| **Ask**（默认） | 只读 | 写 Canvas、外部调用、危险操作都要问 | 第一次用 Kokoro / 敏感任务 |
| **Accept edits** | 只读 + 写当前 Canvas 主稿 + 写草稿层 | 外部调用、危险操作仍要问 | 日常创作，"我相信它改 Canvas" |
| **Auto** | 几乎全自动（仅熔断器还会问） | 仅 [circuit-breakers.md](./circuit-breakers.md) 列的 protected paths | 长任务后台跑，事后审 |

> 不做 `bypassPermissions`。Kokoro 是消费级产品，没人需要"全跳"——这是 Claude Code 给"在隔离 VM 里跑的开发者"的口子，在 Kokoro 场景下只是脚枪。

### 用户改 mode 的入口

- **主要入口**：输入框底部一个 mode 指示器（参考 Claude Code 的 Shift+Tab 指示器），点开切档
- **快捷键**：`Cmd/Ctrl + .` 循环切下一档（不学 Shift+Tab，那个组合在 Web 里冲突太多）
- **不要**藏到设置页里——藏起来等于让用户审批疲劳到瞎按"永久允许"

### Mode 切换的可见性

- 当前 mode 始终可见在输入框旁
- 切换时输入框下方出现一行轻量提示，例如"现在我会先给方案，不动 Canvas"（plan）/ "改 Canvas 我不再问你"（acceptEdits）—— 用心路线措辞，避免"已切换至 X 模式"这种系统腔
- mode 切换不打断当前任务，但下一次工具调用就生效

### 默认值

| 用户类型 | 默认 mode |
|---|---|
| 新用户首次进入 | **Ask** |
| 老用户上次离开时是 X | 沿用 X |
| 一次会话里手动改过 | 当次到底 |
| 任务跨越 Auto 但触发了熔断器 | 自动回退到 Ask，并在 UI 里说明原因 |

---

## 第 3 层 · 进程 / 数据沙箱

Mode 控制"问不问"，沙箱控制"问错了答错了也出不了事"。

### Kokoro 当前的沙箱边界（v1）

| 边界 | 实现 |
|---|---|
| Canvas 文件系统 | 每个用户有命名空间，模型只能读写当前会话的 Canvas，不能跨 Canvas 写 |
| 工具网络出口 | WebFetch 走 Kokoro 代理，强制域名校验 + UA 标记 |
| MCP server 进程 | 第三方 stdio MCP 跑在 worker 里，只能访问声明过的 scope |
| 第三方 OAuth token | 凭证只在调用瞬间从加密存储取出，不进对话上下文 |

### 未来（v2+）要补的

- 长任务跑在 ephemeral VM（参考 Claude Code Web 的"每 session fresh VM"）
- "Computer use"类工具（自动操控屏幕）必须默认关闭，开启时强制 isolated session

### 沙箱与 mode 的关系

正交。沙箱不会因为切到 Auto 就放松；它兜的是"模型决策失误"，不兜"用户授权扩大"。这层独立于 permission，是最后一道闸。

---

## 典型用户旅程

### 旅程 A · 新用户第一次让 Kokoro 帮做一份 Canvas

1. 默认 Ask mode，输入框底部显示"问我"指示器
2. 用户说"帮我做一份周报模板"
3. 模型说"我打算这样做……（结构）"——这步只读 + 想，不算敏感，不弹审批
4. 模型要开始写 Canvas——按规则是 ask，弹询问条："要把这份写到当前 Canvas 吗？（这次 / 本对话不再问 / 永久允许）"
5. 用户点"本对话不再问"
6. 模型连续写完几个章节，每个章节不再弹（已 allow）

### 旅程 B · 用户切到 Plan mode 让它先想

1. 用户切 Plan
2. 输入框下方提示"现在我会先给方案，不动 Canvas"
3. 模型生成 plan 文本 + 草稿层预览
4. 弹审批面板（4 选 1，参考 Claude Code）：
   - 接受方案并开始改 Canvas（自动切 Accept edits）
   - 接受方案但逐条审（保持 Ask）
   - 改方案后再来
   - 继续 plan
5. 用户选哪个，就切到哪个 mode

### 旅程 C · 长任务用户切 Auto 然后回来

1. 用户切 Auto，让 Kokoro 后台调研 + 整理
2. 跑到一半模型要调 Slack MCP——这是外部调用，按规则即使在 Auto 也只对 allowlist 域名放行
3. Slack 不在 allowlist → 触发 protected path 弹框（参考 circuit-breakers），自动回退到 Ask
4. 用户回来看到一条挂起询问 + 已经完成的工作量

---

## 默认值汇总

| 项 | 默认 |
|---|---|
| Permission mode | Ask |
| 询问对话框默认勾选 | "本对话不再问" |
| 外部域名首次访问 | ask |
| 第三方 MCP server 首次启用 | ask + 显式"添加到 allowlist"按钮 |
| 危险操作（见熔断器清单） | 永远 ask，与 mode 无关 |
| 用户主动撤回授权 | 设置页 → 权限审计 → 一键撤销 |

---

## 待拍板

- [ ] mode 是否给企业版加一档 `Locked`（管理员锁死，用户不能切到 Auto）
- [ ] 询问 UI 是浮层、行内还是 sidesheet？倾向行内（不打断 Canvas）
- [ ] 是否允许用户写自定义 deny/allow 规则（advanced），还是只暴露开关
- [ ] 跨设备 mode 是否同步（手机切 Auto 时桌面也变？）—— 倾向不同步，设备独立

---

## 关联

- [04-architecture/permissions.md](../04-architecture/) — 架构层（这边讲实现）
- [privacy.md](./privacy.md) — 数据维度的授权
- [content-guardrails.md](./content-guardrails.md) — 模型自己拒绝的那一层
- [circuit-breakers.md](./circuit-breakers.md) — 永远不进入 auto 的危险动作清单
- [02-personality/voice-and-tone.md](../02-personality/voice-and-tone.md) — 询问 / 拒绝措辞
- 调研：[claude-code/learnings/04-safety-and-surfaces.md](../../research/claude-code/learnings/04-safety-and-surfaces.md)、[claude-code/learnings/03-agentic-primitives.md](../../research/claude-code/learnings/03-agentic-primitives.md)
