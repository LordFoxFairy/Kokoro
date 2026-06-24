# Tool-Call 状态实体模型 —— 端到端补全设计

> 2026-06-24 · 跨仓（kokoro-agent / contract / kokoro-session / kokoro-web）
> brainstorming 产出，待用户复审 → writing-plans。

## 0. 决策（TL;DR）

把"工具调用"作为**带状态的实体**端到端补全；规范状态机 = 消费端 `SessionToolCall.status` 已有的集合：

```
running ─────────────→ done
   │                    │
awaiting(pending) ──┬─→ rejected      （HITL: 用户拒绝）
                    ├─→ done           （HITL: respond 注入合成结果）
                    └─→ running→done   （HITL: approve / edit）
任意阶段异常 ───────────→ error
```

**关键决策：补全，不重建。保留现有事件溯源式 wire（`tool.invoked` / `tool.awaiting_approval` / `tool.returned`），不把三事件坍缩成单事件。** 理由见 §3。

本设计同时收口三件本质同源的事：① HITL "等待"语义（你说的 pending）；② `rejected` 死字段 → rejected 工具 **replay 不安全**；③ subagent 嵌套工具的审批/归属缺失。一个模型，三处闭环。

## 1. 背景与问题

现状（已逐文件勘察，证据见 §2）：

- **felt #1「等待用 pending 更舒服」**：agent wire 用独立事件 `tool_call_awaiting` *替身* `tool_call_start`，"等待"不是一等状态而是靠事件类型反推。
- **felt #2 `rejected` 是死字段**：`projection/transformer.py:tool_end_event` 硬编码 `"rejected": False`（注释 `HITL reject 语义后续接入`）。HITL 拒绝回流时 `tool.returned` 带 `is_error=false` → 消费端看到的是"绿勾 done"，**与成功完成不可区分**。
- **felt #3 subagent 审批不透明**：subagent 的 text/tool chunk 都带 `subagent_id`，唯独 `awaiting_approval_events` 只读**顶层**图快照（last AIMessage），子代理里待批的工具丢归属。
- **附带真 bug**：多个工具可同时 awaiting（`awaiting` 逐工具发 N 个事件），但 `RunResume.decision` 是**单数**，只能答 1 个；native `Command(resume={"decisions":[...]})` 本是 list。

## 2. 关键证据（为什么这不是臆想，也不需要重建 wire）

**消费端早已是状态实体模型**（`kokoro-web/src/application/session-stream/types.ts`）：

```ts
export type SessionToolCall = {
  // …
  status: "running" | "awaiting" | "rejected" | "done" | "error"
}
```

状态集合与本设计**完全一致**。web reducer（`state-mutations.ts`）已实现完整转移：

- `resolveOpenTools`：run 终态时把残留 `running`/`awaiting` 翻 `error`，避免永久挂起的待批行 + 无人消费的批准按钮。
- **乐观 reject**（行 79-93）：用户点「拒绝」**本地**把 `awaiting`→`rejected`，注释直言 `区别于 reject 回流的 is_error=false 绿勾`。

⇒ 这是 felt #2 的铁证：**后端不发权威 `rejected`，web 只能本地乐观置 rejected；一旦 reload/replay，乐观状态丢失，被拒绝的工具变回绿勾 done。rejected 工具 replay 不安全。**

**contract 已声明 `rejected`**（`contract/events.yaml:139, 298-299`）：`tool.returned.rejected` 可选、语义"仅 HITL 拒绝时为 true，replay 安全地区别于绿勾 done"。session Zod 也已接收。

⇒ **缺口 100% 在 agent 侧**：契约、session、web 都已为状态模型就位，唯独 agent projection 不发 `rejected:true`、不带 subagent 归属。

## 3. 设计决策：补全，不重建（为何不坍缩 wire）

考虑过把 `tool.invoked`/`awaiting_approval`/`returned` 坍缩成单一 `tool_call{status}` 事件。**否决**，理由：

1. **消费端已从事件溯源正确派生 status**——坍缩对消费端零收益。
2. **事件溯源是 replay 的根基**：分阶段（进入帧 + 终态帧）天然支持流式与重放；单事件多次发 status 反而更难保序去重。
3. **坍缩 = 四仓 churn 无净收益**，违背"极简、拒绝无谓改动"。

✅ 正解：**承认 `SessionToolCall` 为规范模型，让每一仓忠实地产出/透传完整状态集（尤其 agent 侧权威 `rejected` + subagent 归属），事件族不动。**

## 4. 规范状态机（canonical）

工具实体键 = `tool_id`（= AIMessage tool_call id，全程稳定，已验证）。

| 状态 | 进入条件 | wire 信号 |
|---|---|---|
| `running` | 工具被批准/无需审批，开始执行 | `tool.invoked` |
| `awaiting` | 被门控工具命中 interrupt | `tool.awaiting_approval` |
| `done` | 正常返回 / HITL respond 合成结果 | `tool.returned{is_error:false, rejected:false}` |
| `rejected` | HITL 用户拒绝（或审批超时回退） | `tool.returned{is_error:false, rejected:true}` |
| `error` | 工具执行异常 | `tool.returned{is_error:true}` |

子代理内的工具：上述事件附 `subagent_id`（归属其触发 call id），与 text/tool chunk 同构。

## 5. 待解机制 ⚠️ SPIKE（实现前必须先验）

**核心未知：agent 如何观测到"这个工具是被 reject 的"，从而发 `rejected:true`？**

reject 流程：`RunResume(RejectDecision)` → supervisor `_decision_dict` → `Command(resume={"decisions":[{type:reject,...}]})` → deepagents `HumanInTheLoopMiddleware` 不执行工具、注入合成结果。`invoke_once` 独立消费 stream，看到的是一条工具结果——**它怎么知道这是 reject 而非正常返回？**

候选机制（spike 逐一实证，选最 native 的）：
- **A. langgraph/deepagents 状态自带标记**：reject 后 ToolMessage / state 是否带 `status="rejected"` 或可识别 metadata？（首选——若框架原生有，直接读，零自研）
- **B. supervisor 侧关联**：supervisor 处理 reject 时已知 `tool_id` + 决策，下沉给 `invoke_once`（如经 run_state / 一个 per-run 的 rejected tool_id 集合），projection 据此置 `rejected`。（次选——跨 invoke 段关联，注意 replay/多 pod）
- **C. 合成结果内容嗅探**：从结果文本判断。（**否决**：脆弱、字符串硬编码，违背铁律）

**spike 产出**：确定机制 A 是否成立；不成立则定 B 的最小关联通道。这是本设计**最大风险点**，writing-plans 前先做。

## 6. 四仓改动面（line-precise）

### kokoro-agent
- `application/projection/transformer.py:tool_end_event` —— `rejected` 由 §5 机制派生，删死字段 `False`；`tool_start_event`/`tool_end_event` 增可选 `subagent_id` 形参。
- `application/run/consumer.py:_consume_tools` —— 把 `subagent_id` 透传进 tool 事件（现已对 message chunk 透传，tool 对齐）。
- `application/projection/awaiting.py` —— 子代理待批：从子代理 run 的快照取 action_requests + 带 `subagent_id`；当前只读顶层快照的硬伤修掉。
- `interfaces/inbound.py:RunResume` —— `decision: ResumeDecision` → `decisions: list[ToolDecision]`，每项含 `tool_id`；supervisor 按 `tool_id` 组 `Command(resume={"decisions":[...]})`。
- `interfaces/envelope.py` —— `ToolStartData`/`ToolEndData` 加 `subagent_id: NotRequired[str]`；`ToolEndData` 可选 `reject_reason`。
- subagent failed 终态：见 §7。

### contract（单源）
- `events.yaml` 的 `tool.invoked`/`awaiting_approval`/`returned` 三事件 payload 加 `subagent_id`（render_optional + agui_out_web_extra）。
- `tool.returned` 加可选 `reject_reason`。
- subagent_finished 加可选 `failed`/`error`（§7）。
- 重生成 5 镜像 + `verify.py` + `generate --check`。

### kokoro-session
- `application/normalize.ts` 的 `tool_call_*` 三 case —— 透传 `subagent_id` / `reject_reason`（机械）。

### kokoro-web
- `state-mutations.ts` —— **删乐观-only reject hack**，改消费后端权威 `rejected`（保留乐观作为即时反馈、但以后端回流为准 → replay 安全）。
- 渲染 subagent 嵌套工具的审批行（按 `subagent_id` 归属到子代理段）。
- `types.ts` 工具实体补 `reject_reason?` / `subagentId?`。

## 7. subagent 配套（同源收口，不外扩）

- **failed 终态**：子代理内部异常现冒泡成顶层 `agent_error`、丢归属。给 `subagent_finished` 加可选 `failed` + `error`，使子代理失败有主（与工具实体 `error` 终态同构）。
- **subagent_id 贯穿**：§6 已让工具事件带 subagent_id；subagent 审批因此天然归属，felt #3 闭环。
- **明确不做（YAGNI）**：per-subagent usage 拆分、单独 cancel 某个在途子代理——无产品诉求前不做。

## 8. 多工具审批 ↔ 多决策 resume

- `RunResume.decisions: list[{tool_id, decision}]`，按 `tool_id` 寻址，一次性答复同一 interrupt 内的全部待批工具。
- supervisor 组 `Command(resume={"decisions":[_decision_dict(d) for d in ...]})`（native 本就是 list）。
- 兼容：单工具时退化为单元素 list；wire 仍逐工具发 awaiting（不变）。

## 9. 测试策略（重点 replay-safety）

- **replay 安全（核心）**：reject 一个工具 → 断言 `tool.returned{rejected:true}` → 重放事件流 → 工具终态仍是 `rejected`，**不退化为绿勾 done**。这是本设计存在的根本理由，必须有红→绿测试。
- subagent HITL e2e：子代理内工具被门控 → `tool.awaiting_approval{subagent_id}` → reject → `tool.returned{subagent_id, rejected}`。
- 多工具 resume：一个 interrupt 含 2 个待批工具 → 一条 `RunResume.decisions=[approve A, reject B]` → A done / B rejected。
- subagent failed：子代理抛异常 → `subagent_finished{failed:true}`，不再吞成顶层 agent_error。
- 全门：mypy0 / pyright0 / pytest（含上述新例，零 skip）/ ruff；session `bun test`；web `vitest`；contract `verify.py` + `generate --check`。
- wire 兼容铁证：现有 tool 事件断言（不含新可选字段的旧例）保持绿。

## 10. 范围与不做

- **做**：rejected 权威化（replay 安全）、subagent_id 贯穿工具事件 + 审批归属、多工具多决策 resume、subagent failed 终态、契约/三仓透传。
- **不做（YAGNI）**：坍缩 wire 事件族（§3）；per-subagent usage 拆分；单独取消子代理；审批超时 TTL（除非产品要）。

## 11. 风险与开放问题

1. **§5 SPIKE 是前置阻断**：reject 观测机制未定，则 rejected 权威化无法落地。先验。
2. **跨仓节奏**：contract-first（events.yaml → 重生成 → 各仓），coupled PR 一起合（参 stacked-squash playbook）。
3. **依赖已删**：`.venv`/`node_modules` 当前为打包删除态，落地实现前需 `uv sync` + `pnpm/bun install` 才能跑门禁验证。
4. **多 pod / replay 下的 reject 关联**（若 §5 走 B）：rejected tool_id 集合需随 run_state 持久化，否则跨 pod/重放丢失——与既有 RunStateStore 对齐。
