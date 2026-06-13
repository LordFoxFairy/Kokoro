---
status: 🟡 草稿
layer: contracts
owner: claude
updated: 2026-06-14
refs:
  - test:normalize-13-kinds
  - test:stream-port-transport
---

# 契约层 — 需求 ↔ 契约 ↔ 测试映射索引

> 一句话:这是**薄桥**,不重写契约。把能力/流程映射到已有的 protocol 文档、工程 spec、测试 slug,让人一眼找到「这个需求的契约在哪、怎么验证」。契约本身的真相在 `docs/protocol/` 和 `docs/superpowers/specs/`,改契约改那里,这里只更新链接。

## 单源与门禁

- **契约单源**:`contract/events.yaml`(13 kind × 三视角 + 命名映射 + transport 常量 + status)。
- **门禁**:`contract/verify.py` 结构化校验 6 镜像 + 2 stream-port 一致,漂移即非零退出(`test:normalize-13-kinds`)。
- **CI**:根仓 `.github/workflows/contract.yml` checkout 三 sibling 仓跑 verify(四仓 CI 全绿)。

## 映射表

| 需求 / 流程 | 契约文档 | 工程 spec | 测试 slug |
|---|---|---|---|
| [conversation](../01-capabilities/conversation.md) | [session-stream](../../protocol/session-stream.md) | — | web-send-message · web-new-chat · web-localstorage-persistence |
| [agent-activity](../01-capabilities/agent-activity.md) | [session-stream](../../protocol/session-stream.md) | [stream 架构 §3](../../superpowers/specs/2026-06-11-stream-event-architecture-spec.md) | todo-flow · web-tool-call-display · subagent-task-flow |
| [streaming](../01-capabilities/streaming.md) | [session-stream](../../protocol/session-stream.md) | [multi-segment](../../superpowers/specs/2026-06-06-multi-segment-assistant-stream-design.md) · [stream-continuity](../../superpowers/specs/2026-06-13-stream-continuity-design.md) | text-stream-flow · segmenter-flow · web-segment-interleaving |
| [resume](../01-capabilities/resume.md) | [session-replay-and-resume](../../protocol/session-replay-and-resume.md) | [stream 架构 §4](../../superpowers/specs/2026-06-11-stream-event-architecture-spec.md) | sse-resume-last-event-id · resume-cursor-guard · seq-dedup · web-refresh-reattach |
| [tools](../01-capabilities/tools.md) | [session-stream](../../protocol/session-stream.md) | [capability-extension](../../superpowers/specs/2026-06-12-capability-extension-design.md) | tool-event-flow · subagent-runtime-flow |
| [trust-modes](../00-product/trust-modes.md) | [modes-and-execution-style](../../protocol/modes-and-execution-style.md) | — | web-mode-select-lock · model-resolution-flow |
| [degrade-and-reject](../02-flows/degrade-and-reject.md) | [safety-and-permission-envelope](../../protocol/safety-and-permission-envelope.md) | [stream 架构 §5](../../superpowers/specs/2026-06-11-stream-event-architecture-spec.md) | web-transport-strict-parse · strict-reject-no-skip · failure-run-failed-boundary |
| [extension-points](../01-capabilities/extension-points.md)(🔲) | — (control stream 留缝) | [capability-extension](../../superpowers/specs/2026-06-12-capability-extension-design.md) | — (未建) |

## 标识符与传输契约(速查)

| 标识符 | 职责 | 详情 |
|---|---|---|
| `seq` | 唯一领域排序源(per-run 非递减) | [stream 架构 §2](../../superpowers/specs/2026-06-11-stream-event-architecture-spec.md) |
| `stream_id` | 传输游标 / SSE id / 续点 | 同上 |
| `segment_id` | 一段输出统一 id | 同上 |
| `event_id` | `evt_{run_id}_{seq}_{event}` 幂等去重键 | 同上 |
| StreamPort | memory / redis 双后端 | `test:stream-port-transport` |

## 维护规则

- 改契约 → 改 `contract/events.yaml` + 对应 protocol 文档,本表只跟着更新链接,**不**复制契约内容。
- 新流程 → 在本表加一行(需求 / 契约 / spec / slug 四列齐)。
