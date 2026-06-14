# HITL 权限模式设计 — Claude-Code 式工具门钩子

> 定位:把 [trust-modes](../../docs/requirements/00-product/trust-modes.md) 的信任档位从「叙事」落成**真行为**——按权限模式在工具执行前放行/拦截。参考 Claude Code 的 permission mode。
> 用户拍板:参考 Claude Code,auto mode + 其它模式,**弄一个钩子,保持简单**。
> 边界:本轮做**确定性门**(allow/deny by mode),不做交互式「暂停→问用户→恢复」(那需要运行中反向通道,列为 follow-up)。

## 权限模式(随 RunRequest,默认 auto = 现状)

| 模式 | 语义 | 放行 | 拦截 |
|---|---|---|---|
| `auto` | 全自动(= CC bypassPermissions),**默认** | 全部工具 | — |
| `default` | 拦外部副作用 | now / write_todos / task / runtime-agent | fetch_url |
| `plan` | 只读规划(= CC plan mode) | now / write_todos | fetch_url / task / runtime-agent |

> 默认 `auto`:不传即现有行为,零破坏。

## 需拦截确认的工具 = 显式可配置集（用户强调的常见模型）

更常见的用法不是靠 mode 一刀切，而是**默认 auto 全自动，但把个别敏感工具设为「需拦截确认」**。
因此 `permission.py` 用显式集 `REQUIRES_APPROVAL`（默认 `{fetch_url}`）承载「哪些工具要拦」——
要拦更多工具往里加名字即可。`blocked_tools(mode)`:auto 不拦 / default 拦 `REQUIRES_APPROVAL` /
plan 在此基础上再拦执行类(`agent` 子代理)只读规划。

> 注:本轮「拦截」是**确定性拦下并回拦截结果**(模型据此调整);真·交互式「暂停→人确认→恢复」
> 见下方 follow-up（需反向通道）。

## 钩子(本轮实现范围)

`infrastructure/permission.py`:`PermissionMode` 枚举 + `tool_allowed(mode, tool_name) -> bool` 策略 +
`gate_tools(tools, mode)` 把**Kokoro 注入的工具**(BUILT_IN_TOOLS = now/fetch_url + runtime-agent)
包成「执行前查策略」的 StructuredTool:被拦则返回 `「<tool> 被 <mode> 模式拦截:需更高权限档位」`
(模型看到该结果后调整;复用现有 `tool.returned`,**零新契约 kind**)。

`_build_agent(model, permission_mode)` 应用 gate;`run_agent` 传 `req.permission_mode`。

## 契约

`RunRequest` 加 `permission_mode: "auto"|"default"|"plan" = "auto"`(agent `run_request.py` pydantic +
session `run-request.ts` zod **手镜像**,与既有 `execution_style` 同模式;RunRequest 不在 events.yaml
codegen 范围)。session `http.ts` 读 `?permission_mode=` query → `start-run` 透传到 run.request 事件。

## 落地范围 vs follow-up

**已落地**:
- Kokoro 注入工具(fetch_url / runtime-agent)按模式 deny;契约 + session 透传 + agent 测试。
- web composer Auto/Default/Plan 选择器(会话级,默认 Auto)。
- **✅ deepagents 内部文件系统工具门控**:`fs_permissions(mode)` 经 `create_deep_agent(permissions=)`,
  plan 只读(`deny write` → 拦 write_file/edit_file,放行 ls/read_file/glob/grep);auto/default 不限。
  真机实证:plan 真模型写文件被拒(`permission denied for write`)、auto 写成功并读回。
  (`execute` 需 sandbox backend,Kokoro 未配 → 本就不可用,无需门控。)

**follow-up(更完整 HITL,需反向通道)**:
- **交互式 ask**(真·human-in-loop:暂停→web 确认→恢复):deepagents `interrupt_on=` + `checkpointer`
  + per-run control stream(`kokoro:run:<id>:control`)+ session `POST /runs/:id/control` + web 审批 UI。
  这是反向通道,工作量大,独立实现。

## 验收

- [ ] auto:所有工具照常执行(全套测试不变)。
- [ ] plan/default:对应工具被拦,返回拦截结果;模型流不崩。
- [ ] permission_mode 经 RunRequest 端到端透传(http query → agent gate)。
- [ ] 默认 auto:不传即零行为变化。
- [ ] agent pytest/pyright/ruff + session test/typecheck 绿。
