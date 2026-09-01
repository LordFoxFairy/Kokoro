# 33. GA Skill 能力：Capability 解析与 DeepAgents 原生读取

状态：当前 Skill 专项方案，2026-08-29。总体架构以
[42 GA 核心架构](42-ga-core-architecture.md) 和 [36 GA 技术方案](36-ga-final-agent-technical-plan.md) 为准。

## 1. 一句话

GA 不实现第二套 Skill runtime。Agent 声明 Skill 名称，Capability 解析当前 Run 可见引用，GA
把获准包体接成 DeepAgents backend 的只读逻辑路由，之后完全使用官方 SkillsMiddleware 与
`read_file` 渐进读取。

```text
Agent.skills
  -> Capability SkillClient.resolve(identity, runtime_namespace)
  -> ResolvedSkill(name, scope, content_hash)
  -> CapabilitySkillBackend (read-only, lazy package read)
  -> CompositeBackend route: /.skills/
  -> create_deep_agent(skills=["/.skills/"])
  -> DeepAgents SkillsMiddleware + read_file
```

## 2. Owner 边界

| 内容 | Owner | GA 行为 |
|---|---|---|
| Agent 需要哪些 Skill | GA Agent 声明 | 只保存稳定名称 |
| 用户/项目/session Skill CRUD、可见性与 logical path | Capability | 通过 public contract 解析名称 |
| package bytes、checksum 与对象生命周期 | Storage | 经 `SkillReader` 读取获准包体 |
| Skill metadata、渐进读取与附件访问 | DeepAgents | 官方 SkillsMiddleware / `read_file` |
| `/.skills/` route | GA | public client 到 BackendProtocol 的只读 adapter |

GA 不读取 Capability/Storage 数据库、Redis key 或 bucket，也不 seed/upsert 官方 Skill。

## 3. 包与运行路径

Skill 包沿用 DeepAgents 原生布局：

```text
<skill-name>/
├── SKILL.md
├── scripts/       可选
├── references/    可选
└── assets/        可选
```

`/.skills/` 只是 `CompositeBackend` 的逻辑路由。包体保持在 Storage public contract 后面，首次读取
时才由 `CapabilitySkillBackend` 拉取并在当前 Agent 构造实例内缓存；不会复制到 sandbox，不创建
mount ledger、物化、reconcile 或 GC 流程。

## 4. Agent 与 Feature

Agent/Feature 不携带 `ResolvedSkill`、grant、版本或 Session binding。Factory 在每次构造时解析
Agent 声明，解析结果只属于本次构造：

- 单 Agent Feature 直接传给 `create_deep_agent`；
- 多 Agent Feature 的每个 peer 按自己的声明解析，再由 official Swarm 组合；
- Skill 不增加 Agent、handoff、Tool、MCP、权限、模型或计费能力；
- Capability 解析失败时使用空 Skill 集，基础 DeepAgents 对话循环继续。

## 5. 明确不做

当前 GA 不提供：

- Skill 搜索或加载工具；
- 动态 Skill 发现/追加；
- 自定义 Skill prompt manifest；
- Skill mount receipt、Session Skill binding 或版本机制；
- 自定义 State、middleware 或读取协议来替代 DeepAgents。

未来若产品确实需要发现能力，应作为独立需求重新验证 public contract；它不改变本方案的原生读取链路。

## 6. 验收门

- `create_deep_agent` 收到 `skills=["/.skills/"]`；
- DeepAgents 官方 SkillsMiddleware 能列出 metadata，并给出原生 `read_file` 路径；
- route 只暴露 Capability 已授权 Skill，未知路径不可读，写入全部拒绝；
- 包体按需读取，同一构造实例内不重复下载；
- Skill client 不可用时基础 Agent 仍可运行；
- Skill 内容、内部路径与 package bytes 不进入 ProductEvent 或 GA 自定义 checkpoint 字段。
