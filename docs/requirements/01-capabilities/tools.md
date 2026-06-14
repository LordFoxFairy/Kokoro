---
status: 🟡 草稿
layer: capabilities
owner: claude
updated: 2026-06-14
refs:
  - test:tool-event-flow
  - test:web-tool-call-display
  - test:subagent-runtime-flow
---

# 能力 · 工具接入

> 一句话:agent 可调用内置/配置工具去取外部信息或执行动作,调用与结果如实成事件流呈现。

## 需求

- **R1 工具事件**:每次工具调用**必须**产 `tool.invoked`(含 args)+ `tool.returned`(含 result + `is_error`)成对事件,经契约流到 web 渲染(见 [agent-activity](./agent-activity.md))。
- **R2 内置工具**:已建 `now`(当前时间)、`fetch_url`(抓取 URL)。`fetch_url` **必须**带 SSRF 防护:阻断 loopback/link-local/unspecified/multicast/RFC1918,跟随重定向时逐跳 DNS 解析后 IP 复校验(防 rebinding),墙钟超时 + 字节上限。
- **R3 撞名守卫**:工具注册名与保留名/彼此撞名**必须**在导入期 fail-loud,不得静默覆盖。
- **R4 结果截断**:超长结果按上限截断后入事件流(避免污染上下文/传输)。
- **R5 错误呈现**:工具失败 → `is_error: true` + result 为错误文本(空异常回落类型名)→ web 显红失败行。子代理工具失败发 `subagent.finished` 不留卡死行。
- **R6 接入 SOP**:新工具按[扩展架构 spec](../../superpowers/specs/2026-06-12-capability-extension-design.md) 的 7 步新 kind SOP 接入,零契约破坏。

## 验收

- [ ] tool.invoked/returned 成对,args/result 正确(`test:tool-event-flow`)
- [ ] web 工具行三态(含 error 红)(`test:web-tool-call-display`)
- [ ] runtime-custom 子代理即席注册并执行(`test:subagent-runtime-flow`)
- [ ] SSRF:内网/元数据地址真拒,公网域名真抓(参 `kokoro-agent/tests/test_builtin_tools.py`)

## 不做 / 边界

- 工具执行前**确认/暂停**(HITL)= 🔲 未实现 → [extension-points](./extension-points.md)。
- MCP 工具接入 = 🟡 已设计(`docs/product/08-extensibility/mcp.md`),真实仓未落地。

## 引用

- 扩展架构:[capability-extension-design](../../superpowers/specs/2026-06-12-capability-extension-design.md)
- 实现:`kokoro-agent/src/kokoro_agent/infrastructure/builtin_tools.py`
