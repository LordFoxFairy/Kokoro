---
status: 🟡 草稿
updated: 2026-05-20
---

# 核心流程

> 三条主用户路径。其他次要 flow 在 [06-screens/](../06-screens/) 各页文档展开。

---

## Flow 1 · 一句话造产物（首屏 → Canvas → 分享）

```
用户进首屏
  └─ 看到引导语 + 输入框 + 几个产出物 chip（"做小红书海报""做策划案"...）
     └─ 用户输入一句话 + 选 chip 或纯文本
        └─ Kokoro 在 Canvas 里实时生成
           └─ 用户可继续追问 / 调整 / 重做
              └─ 用户点"分享"
                 └─ 生成 share link + OG 图（带印记）
                    └─ 分享出去
```

**关键体验点**：
- 首屏 → Canvas 之间没有任何中间步骤
- Canvas 生成过程**可见**，能让用户感觉"在做" 而不是"在等"
- 分享按钮位置显眼（一等公民）

---

## Flow 2 · 持续对话深化（Chat → 多轮 → Canvas 累积）

```
用户进对话
  └─ 多轮对话讨论想法
     └─ Kokoro 提议 "要不要把这个落到 Canvas 上"
        └─ 用户同意 → Canvas 出现
           └─ 来回多次（chat → canvas → chat → canvas）
              └─ 完成 / 暂停 / 分享
```

**关键体验点**：
- Chat 和 Canvas 之间的"过渡"要顺
- 不要强迫用户提前决定"要 Canvas 还是只 chat"

---

## Flow 3 · 用模板（模板库 → 一键起飞）

```
用户进模板库（或被首屏推荐）
  └─ 浏览 / 搜索模板
     └─ 选定一个
        └─ 一键复制到我的 Canvas
           └─ 用 Kokoro 帮我"按这个风格做一份"
              └─ Kokoro 在 Canvas 里调整为用户场景
                 └─ 用户微调 / 分享 / 自己再转模板
```

**关键体验点**：
- 模板不是静态文件，是"半成品 + AI 适配"
- 用户改完可以一键转模板回馈社区

---

## 共享子流程

### A. 触发 Plan mode

任何用户输入涉及**多步骤 / 风险 / 不确定**时，Kokoro 自动进入 Plan mode：

```
用户输入
  └─ Kokoro 判断"这个需要规划"
     └─ 进 Plan mode：生成 plan preview
        └─ 用户 Approve / Refine / Cancel
           └─ Approve → 执行
              Refine → 用户调整 plan，再 Approve
              Cancel → 回到 chat
```

参考：[04-architecture/modes.md](../04-architecture/modes.md) + [Claude Code learnings/03-agentic-primitives.md](../../research/claude-code/learnings/03-agentic-primitives.md)

### B. 危险操作熔断

任何"不可逆 / 影响他人 / 跨账号"的操作：

```
Kokoro 准备执行
  └─ circuit breaker 触发
     └─ 弹 modal："你要 ___，我做完就回不去了。确认？"
        └─ 用户 Confirm / Cancel
```

参考：[09-safety/circuit-breakers.md](../09-safety/circuit-breakers.md)

---

## 反例（不要这样做）

- ❌ 首屏需要选择"我要 chat 还是 Canvas"——增加心智成本
- ❌ 分享按钮藏在三级菜单——违反一等公民
- ❌ 模板需要付费才能用——破坏增长引擎
- ❌ Plan mode 必须手动开——应自动进入

## 待答题

- [ ] Flow 1 的"产出物 chip"个数：3 / 5 / 7？（决定首屏布局）
- [ ] Flow 2 的"chat → canvas 过渡"用什么触发？（用户主动 / Kokoro 提议 / 自动判断）
- [ ] 是否允许"未登录"试用？（影响 funnel 顶部宽度）

## 关联

- [shape.md](./shape.md)
- [feature-map.md](./feature-map.md)
- [04-architecture/](../04-architecture/)
- [06-screens/home.md](../06-screens/home.md)
