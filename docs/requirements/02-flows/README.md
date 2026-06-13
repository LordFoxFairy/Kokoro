# 流程层 — 端到端业务流程 + 验收

> 每篇描述一条**跨层端到端流程**(web↔session↔agent),用 Given/When/Then 写验收,并映射[测试总目录](../../superpowers/specs/2026-06-13-test-case-catalog.md)的 slug。

## 验收规范

- 每条流程**必须** `refs` 含 ≥1 个 `test:<slug>`。
- 验收用 Given(前置)/ When(触发)/ Then(可观察断言)三段,断言可由对应测试机械验证。
- 暂无测试覆盖的断言 → 标 🔴 并登记到 [item 3 缺口](#缺口指向-item-3)。

## 流程索引

| 流程 | 文件 | 主要能力 | 关键 slug |
|---|---|---|---|
| 发送 → 流式作答 → 落定 | [send-and-stream](./send-and-stream.md) | 会话 / 流式 / 活动流 | web-send-message · web-segment-interleaving · text-stream-flow |
| 刷新/瞬断 → 重连续传 | [interrupt-resume](./interrupt-resume.md) | 恢复 | web-refresh-reattach · sse-resume-last-event-id |
| 工具调用 → 渲染 → 错误 | [tool-run](./tool-run.md) | 工具 / 活动流 | tool-event-flow · web-tool-call-display |
| 多会话 新建/切换/删除/持久 | [multi-conversation](./multi-conversation.md) | 会话 | web-new-chat · web-localstorage-persistence |
| 降级与严格拒收 | [degrade-and-reject](./degrade-and-reject.md) | 鲁棒性 | web-preview-fallback · web-transport-strict-parse · strict-reject-no-skip |

## 缺口指向 item 3

测试总目录已标注每条用例的成熟度(✅ 已覆盖 / 🟡 部分 / 🔴 缺)。本手册流程层**引用**这些 slug,不复制用例;item 3「完美测试用例」反向消费这里映射出的 🔴/🟡 缺口去补齐。
