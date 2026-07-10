# Kokoro 业务 agent 配置包与编排 v2（待审）

状态：草案 v2（业务编排表达力重设计），未获认可
日期：2026-07-10
上级：`2026-07-10-agent-system-model.md`（统一模型：本文是"池中 agent 资产 + 快照中 agent 维度"的展开）

## 0. 一句话

> 业务 agent = 一个结构化配置包（人格 + 能力声明 + **私有阶段技能**）；编排深度由"阶段即技能"承接——零新机制，阶段细节渐进披露；硬约束仍只有四个状态机。

## 1. 配置包结构（编排表达力的载体）

```text
agents/music/
  agent.md              # 人格 + 总工作方式（短：只写"怎么想"，一句"工作流程见岗位技能"）
  manifest.yaml         # 能力与策略声明（知识与权限分离：能不能用在这，何时用在 SOP）
    tools: [...]        #   工具白名单
    skills: [...]       #   追加的公共技能（用户池之外恒挂的）
    mcp_servers: [...]  #   需要的外部连接
    subagents: [...]    #   可委派下属（内置 catalog 名）
    approval_tools: []  #   本岗位需人工审批的工具（并入 interrupt_on）
    deliver:            #   交付约定（expects: mime/命名提示，写给 SOP 与校验用）
    model:              #   模型偏好（可选）
  skills/               # 私有阶段技能（不进用户池，随包走，hash 随包锁）
    understanding-brief.md
    producing-drafts.md
    review-and-deliver.md
```

### 阶段即技能（本 v2 的核心）

- 多阶段工作流不是状态机、也不是塞长 prompt——是**该 agent 的私有技能包**：干到哪个阶段，模型读哪份阶段 SOP（`skill(name)` 同一机制、同一清单注入）。
- 清单分区注入 system prompt：**「岗位流程」区（私有阶段技能，置顶）** + 「可用技能」区（会话快照的用户池）+ pinned 强调。
- 主 prompt 恒短；阶段深度不膨胀上下文（渐进披露）；阶段内容可独立打磨评测。
- required（官方强制技能）恒注入；pinned 只影响排序——三者互不冲突。

## 2. 池与快照中的位置（统一模型对齐）

- agent 配置包是**池的一种资产（V1 例外：不入 Mongo/S3,是部署目录资产）**；存储演进方向=与 skills 同链路入 hub（用户自定义 agent 时启用，非 V1）。
- 会话创建时 `session.agent + agent_hash` 定死（改字段 400）；**agent_hash 在部署扫描时用与 skills 同一套 `content_hash_of` 对整包（agent.md+manifest+私有 skills）计算**——进行中的会话不受包升级影响（与 skills 内容锁同法则;V1 包在部署态,同 hash 校验即可,旧版取回依赖部署不回滚——例外已标注,hub 化后自然消除）。
- fork/新会话拿新版包。私有阶段技能随包 hash 一起锁定与物化。

## 3. 切换（已定案，此处收口）

- 场景层：会话在哪创建就是哪个 agent（首条定死+400）。
- 功能层：swarm handoff = P2，历史里的一次工具调用，不碰快照。
- 合法通道仅此两条，无"改字段"。

## 4. 装配（Python 侧的优雅落点）

```text
AgentBundle（frozen dataclass）: prompt / manifest / private_skills(cards+hashes)
  ← BundleLoader: 目录(或未来 hub) → 校验(manifest schema 严格) → bundle
装配管线消费 bundle：
  prompt   = bundle.prompt + 清单段(岗位流程区 + 用户池区)
  toolset  = 注册表(bundle.manifest.tools) + 底座 + skill 工具 + mcp_*
  interrupt_on ⊕ bundle.manifest.approval_tools
  delegates = catalog ∩ bundle.manifest.subagents
```

实现须遵守《Python 实现美学约定》（同日 spec）：manifest 用 pydantic 严格模型；分派用 match/策略表；注册用装饰器注册表；bundle 全 frozen。

## 5. 验收断言

- 新增业务 agent = 仅新增一个包目录（fixture agent 证明零运行时代码改动）。
- fixture agent 的私有阶段技能出现在其会话清单「岗位流程」区，且**不出现**在 general 会话中。
- 同 session 改 agent 字段 → 400；agent 包升级不影响进行中会话（hash 锁断言）。
- general 与 fixture 各自 system prompt 两次装配字节相同。

## 6. 不做

- StageSpec/状态机（阶段是知识不是 schema）；swarm 实现（P2）；用户自定义 agent 包（待 hub 化）；任何垂类实例落库。
