# 工具结果审核暂停（result_review）设计（2026-07-03）

> 状态：✅ 已实现并验证（agent 217 / session 128 / web 171 全门禁绿 + 跨栈 e2e 25 项含审批→执行→审核串联）。
> 施工中追加的两个实现决定：①投影侧 raw returned 对审核工具抑制，裁决后由 supervisor 直发（approve 也带 responded 标记的原结果——raw 结果绝不先于裁决上 wire）；②pause_id 含 kind 维度（同一工具先审批后审核两次暂停不碰撞）。

> 用户需求：两类通用拦截——①工具前人确认（已存在=HIL 审批，approve/edit/reject）；
> ②工具后结果审核：工具执行完、结果回流模型前，停下让用户审核。本文实现 ②。
> 法源延续 handbook 12 号：不自造暂停系统，复用 langgraph 原生 interrupt + 既有 pending_pauses 全链。

## 契约（已落，8cd3c6f）

- `awaiting_kind` += `result_review`；`tool.awaiting_approval.payload.result?`（该 kind 局部可选，生成器新增 `"字段?"` 局部可选标记）；`Permissions.review_tools`；`PendingPause.result?`。
- `tool.returned.result` 保持严格必填不受影响。

## agent

1. **ToolResultReviewMiddleware**（tools/middleware.py 新类，与 ToolPolicyMiddleware 并列）：
   - 命中 `review_tools` 的工具：`handler()` 执行后 `langgraph interrupt({"kokoro_result_review": {tool_id, name, args, result, is_error}})`。
   - **双执行防护**：resume 后节点从头重跑 → 结果先落持久缓存（RunStateStore 扩 `put_tool_result/get_tool_result`，键=run_id+tool_id；sqlite 表 tool_results / mongo 集合），重入命中缓存跳过 handler。
   - 决策应用：approve→原结果；respond{response}→人工替换结果文本；reject{reason}→ToolMessage("[result rejected by user] …", status=error 不用，用普通文本让模型可换路)。
   - resume 值形状与 HIL 对齐：list[decision dict]，中间件按 tool_id 取己项。
   - ask_user ∉ review_tools（build 时校验）；同一工具可同时在 approval+review（先批参→执行→审结果，缓存保证串联不双跑）。
2. **approvals.py**：interrupt 解析成判别联合——HIL 形状(`action_requests/review_configs`) vs review 形状(`kokoro_result_review`)。**V1 约束（fail-loud）**：同帧不混两种形状、review 每帧单 interrupt。
   - review awaiting payload：kind=result_review、result=缓存结果、allowed=[approve, respond, reject]、editable=False、segment=last AIMessage id、pending_tool_ids=review 帧集合。
   - align/validate：review 帧接受 approve/respond/reject（respond=替换结果，不再绑 ask_user——按 pause 类型分支校验）；resume→`Command(resume=[decision dicts])`（非 HIL 的 {"decisions": …} 包装）。
   - resolution_payloads 不适用于 review（工具已执行，最终 tool.returned 由重入后的正常 projection 发出，内容=裁决后结果；respond 替换的 provenance V1 不打标，注记）。
3. supervisor/run_agent：pending/awaiting 调用点传 approval+review 两组名字；`_review_tool_names(request)`。
4. 事件时间线：tool.invoked → tool.awaiting_approval(result_review, 带 result) → [resume] → tool.returned(裁决后内容)。RunEmitter 的 segment 继承机制自动保证三者同段。

## session

- start-message 默认 Permissions 加 `review_tools`（env `KOKORO_REVIEW_TOOLS` csv，默认空）。
- control 校验："respond 仅 ask_user" 放宽为 "respond 仅 kind∈{ask_user, result_review}"；其余（decision∈allowed/tool_id 匹配/decision_id 幂等）不变。
- relay 投影：pause 透传 `result?`；snapshot 原样带出。

## web

- kind=result_review → 结果审核卡（ui/hitl 第三张卡）：展示 result + 采纳 / 替换（文本框→respond）/ 拒绝；staging/decision_id 机制复用。
- hydration/reducer：awaiting step 透传 result。

## 验证

- agent：middleware 双执行防护（缓存命中不重跑 handler）、审批+审核串联、respond 替换/reject 废弃、混帧 fail-loud 反例。
- e2e：LocalFake write_file 同时配 approval+review（session env KOKORO_REVIEW_TOOLS=write_file）→ 批参数 → 审结果（respond 替换）→ 终态；刷新恢复审核卡。
- 真栈走查审核卡一次。

## 明示不做（V1）

同帧混合 approval/review、多 review interrupt 并行、respond 替换的 provenance 标记、结果编辑的结构化 UI。
