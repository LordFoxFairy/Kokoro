---
status: 🟡 草稿
layer: flows
owner: claude
updated: 2026-06-14
refs:
  - test:web-new-chat
  - test:web-switch-conversation
  - test:web-delete-conversation
  - test:web-auto-title
  - test:web-localstorage-persistence
---

# 流程 · 多会话 新建 / 切换 / 删除 / 持久

> 主路径:用户并行管理多个对话,本地持久,刷新恢复。

## 前置

- web 已加载(SSR 水合完成)。

## 验收

**M1 新建**
- Given 任意状态
- When 用户点新建对话
- Then 出现空会话并选中;旧会话状态不受影响(`test:web-new-chat`)

**M2 切换隔离**
- Given ≥2 个会话,其一有在途 run
- When 切换会话
- Then 各会话 thread/在途状态独立,不串(`test:web-switch-conversation`)

**M3 删除**
- Given 选中一个会话
- When 删除
- Then 从列表移除;选中态合理回退;持久化同步(`test:web-delete-conversation`)

**M4 自动标题**
- Given 新会话发出首条消息
- When 首条落定
- Then 生成简短标题(`test:web-auto-title`)

**M5 持久 + 降级**
- Given 会话列表与 thread 已写 localStorage
- When 刷新 / 注入脏数据
- Then 正常恢复;脏数据降级保留可用项,不崩溃(`test:web-localstorage-persistence`)

## 边界

- 侧栏折叠/拖拽改宽 = 交互细节(`test:web-rail-collapse-resize`,测试总目录标 🔴);跨设备同步未规划。

## 引用

- 能力:[conversation](../01-capabilities/conversation.md)
