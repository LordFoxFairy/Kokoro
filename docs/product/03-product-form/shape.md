---
status: 🟡 草稿
updated: 2026-05-20
---

# 产品形态

## 一句话

**Kokoro 是 Web 优先（PWA-ready）的对话 + Canvas + 通用 agent。**

## 形态层次

```
┌─────────────────────────────────────────────────┐
│  Surface（呈现层）                                 │
│  - Web（首发）                                     │
│  - Desktop wrapper（中期，Electron / Tauri）        │
│  - Mobile（长期，可能先做 PWA 再做 native）         │
├─────────────────────────────────────────────────┤
│  UI（交互层）                                       │
│  - 三栏布局：Sidebar + Chat + Canvas               │
│  - 输入 → AI 回应 → Canvas 实时生成               │
│  - 分享 / 模板 一等公民                            │
├─────────────────────────────────────────────────┤
│  Agent（能力层）                                    │
│  - 通用对话                                        │
│  - 工具调用（搜索 / 文件 / 数据）                    │
│  - Plan mode（计划-审批-执行）                      │
│  - Skills（用户自定义扩展）                         │
├─────────────────────────────────────────────────┤
│  Model（推理层）                                    │
│  - LLM 提供方 unclear（待选）                       │
│  - 多模型路由可能（不同任务路由不同 model）          │
└─────────────────────────────────────────────────┘
```

## 平台优先级（待你确认）

| 平台 | MVP | 中期 | 长期 |
|---|---|---|---|
| Web | ✅ 首发 | 持续 | 持续 |
| PWA | ✅（基础） | 增强 | 增强 |
| Desktop | — | ✅ wrapper | native? |
| Mobile | — | PWA 兜底 | ✅ native |
| 桌面终端 / CLI | — | — | 可选 |
| IDE 插件 | — | — | 不做 |

## 形态决策点（与竞品对比）

| 决策 | Kokoro | 参考 |
|---|---|---|
| Web vs Desktop | **Web 首发** | Manus / ChatGPT / Gemini |
| 单一窗口 vs 多窗口 | 单窗口（三栏） | Gemini / Manus |
| Chat 是入口还是平等 mode | **Chat 是入口，Canvas 是引擎** | 与 Gemini 不同（Gemini 平等） |
| Agent 显式 / 隐式 | **可见的 plan 流**（参考 CoWork） | CoWork / Claude Code |
| 工具调用展示 | 默认折叠摘要，可展开 | Claude Code / CoWork |

## 必须不是的形态

- ❌ CLI-first（违反目标用户，他们不开终端）
- ❌ IDE 插件（这是 Cursor 红海）
- ❌ 浏览器扩展（不能承载 Canvas）
- ❌ 微信小程序首发（容量 + 体验不够）

## 待你拍板

- [ ] **平台优先级**：是否同意"Web 首发 → PWA → Desktop wrapper"路线？
- [ ] **MVP 是否包含 mobile（PWA）**？还是 desktop only？
- [ ] **是否做 native app**（长期）？
- [ ] **模型策略**：单一模型（一家供应商）还是多模型路由？这影响商业 / 工程复杂度

## 关联

- [04-architecture/ia.md](../04-architecture/ia.md)
- [04-architecture/modes.md](../04-architecture/modes.md)
- [core-flows.md](./core-flows.md)
