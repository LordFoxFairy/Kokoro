# Namespace Profile 与具名 Agent 入口（2026-07-03）

> 状态：✅ 已实现并验证。agent 230 / session 141 全门禁绿；跨栈 e2e 30 项 PASS
>（含 entry 人格上 wire、其余预设为下属、租户 namespace、unknown_entry 400、cancel 收束）。
> 施工补获：supervisor 终态清理删 control 流与监听任务的 NOGROUP 竞态噪音已按"终态后=干净收束"修复。

> 一石二鸟：多租户资源模型（namespace 拥有 skills/mcp/subagent 预设/模型策略）+ 编排最小闭环
>（具名 AgentSpec 既可被通用 agent 委派、也可独立作主 agent 入口）。
> 法源：handbook ADR-004（Capabilities 由 session/上游生成，agent 只消费不扩权）、
> modules/kokoro-agent.md（RunContext.namespace）、memory: kokoro-agent-namespace-model / swarm-orchestration。

## 所有权三层（定案）

```
namespace  拥有 skills 安装态 / MCP 连接 / subagent 预设(AgentSpec) / 模型策略 / permissions 覆盖
session    拥有 sandbox 工作区(state backend 经 {namespace}:{session} checkpoint 已天然隔离+延续) / 消息史 / 暂停点
run        拿到 RuntimeConfig = profile 资源 ∩ 本次选择 的快照（wire 契约不变原则）
```

## 契约变更（最小两处）

- `control.yaml` RuntimeConfig + `system_prompt?`（专业 agent 作主 agent 的已解析人格；缺省=agent 内置 SYSTEM_PROMPT）
- `http.yaml` startMessageBody + `entry?`（profile.agents 里的具名预设；未知名 → 400 unknown_entry）

## session（大头，新能力域 src/namespace/）

- `profile.ts`：NamespaceProfile Zod strict schema + 文件 loader（`KOKORO_NAMESPACES_FILE` JSON；
  缺省无文件 → 内置 default namespace = 现行为）。形状：
  `{ namespaces: { <name>: { model_policy: {default, allowed?}, skills: SkillMount[], mcp: McpServer[],
     agents: { <name>: {description, system_prompt, tools?, model?} }, permissions?: {approval_tools, review_tools, subagent_create, filesystem} } } }`
- `resolve.ts`：(profile, namespace, body.entry?, body.selected_model?) → RuntimeConfig + RuntimeContext。
  规则：entry 缺省 → 主 agent=通用（无 system_prompt 上 wire），subagents=全部预设；
  entry=X → system_prompt=X 的人格 + model=X.model||policy.default + subagents=其余预设；
  selected_model 不在 policy.allowed（若声明）→ 400 model_not_allowed；
  permissions 覆盖缺省则用内置默认（含 KOKORO_REVIEW_TOOLS 兜底，保持现部署行为）。
- 归属：本实例 namespace 由 `KOKORO_NAMESPACE` env 决定（默认 "local"）；sessions 集合记 namespace，
  runs 记 entry。**不开 body.namespace 口子**（无鉴权环境的伪多租户，等上游身份系统）。
- start-message 的硬编码 defaultRuntime 迁入 resolve（物理删除，禁双源）。

## agent（一行级）

- `worker/main.py`：`system_prompt=runtime.system_prompt or SYSTEM_PROMPT`。其余零改动
 （skills/mcp/subagents 装配与授权边界已就绪）。

## 验证

- session：loader 边界矩阵（缺文件默认/脏 schema fail-loud/未知 entry 400/model_not_allowed/
  双 namespace 的 skills+mcp+agents 互不可见——resolver 级隔离断言）
- agent：system_prompt 覆盖装配单测
- 跨栈 e2e：profile 文件含具名预设（researcher 型 fake），POST entry 指定 → run.request wire 上
  system_prompt/subagents 断言（读请求流）→ LocalFake 全链跑通；缺省 entry 行为不变（现有 25 项不动）

## 明示不做（V1）

body.namespace / DB 配置源（loader 已留接口）/ skills-mcp 的 Hub 管理面 / e2b 实例池 /
entry 的 web UI（surface 路由属 studio 时代）/ swarm 对等交接（P2）。
