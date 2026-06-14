---
status: 🟡 草稿
layer: capabilities
owner: claude
updated: 2026-06-14
refs:
  - test:web-send-message
  - test:web-new-chat
  - test:web-switch-conversation
  - test:web-delete-conversation
  - test:web-auto-title
  - test:web-localstorage-persistence
---

# 能力 · 会话

> 一句话:用户发起、续接、并行管理多个对话,且本地持久。

## 需求

- **R1 发起**:用户从 composer 输入提交(Enter 或点击)即开一个 run。空输入不得发出;在途时再次提交必须被同步在途守卫挡住(双发防抖)。
- **R2 多会话**:用户**必须**能新建、切换、删除会话;每个会话独立持有自己的 thread 状态与在途 run。
- **R3 持久化**:会话列表与每会话 thread **必须**在 localStorage 持久,刷新后恢复;脏数据(解析失败)必须降级而非崩溃(丢坏的、保好的)。
- **R4 自动标题**:新会话应当依首条消息生成简短标题。
- **R5 输入约束**:输入长度有上限,双重把关(UI + 提交前)。

## 验收

- [ ] 提交非空 → 出现用户气泡 + 进入流式(`test:web-send-message`)
- [ ] 空输入/在途重复提交被挡(`test:web-double-submit-guard`)
- [ ] 新建/切换/删除会话状态隔离正确(`test:web-new-chat` / `web-switch-conversation` / `web-delete-conversation`)
- [ ] 刷新后列表与 thread 恢复;注入脏 localStorage → 降级保留可用项(`test:web-localstorage-persistence`)
- [ ] 首条消息后生成标题(`test:web-auto-title`)

## 不做 / 边界

- 后端缺席时的本地预览降级 → 见 [degrade-and-reject 流程](../02-flows/degrade-and-reject.md)。
- 跨设备同步/云端会话 = 🔲 未规划,不在此。

## 引用

- 流程:[send-and-stream](../02-flows/send-and-stream.md) · [multi-conversation](../02-flows/multi-conversation.md)
