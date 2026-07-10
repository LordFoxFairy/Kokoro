# Kokoro Agent 系统统一模型（顶层，统领各专题 spec）

状态：待审。本文是"整个 agent"的统一思考；四份专题 spec（skills / mcp / deliver / agent-preset）是它的展开，冲突时以本文裁。
日期：2026-07-10

## 0. 三个概念，其余皆推论

```text
池(Pool)      平台维度能力资产：agent 配置包 / skills / MCP servers。随时可管理演进。
   │ 创建会话瞬间 → 不可变快照（skills 含内容锁 content_hash）
会话(Session) 池的冻结快照 + append-only 历史 + 一个沙箱。
   │ 每次推进
运行(Run)     消费快照、追加历史、操作沙箱、可交付成果的一步；全部输入原子入账,重放幂等。
```

## 1. 设计决策与推论表（多数由模型必然导出;标注★的是产品决策而非逻辑推论）

| 关切 | 推论 |
|---|---|
| 前缀缓存 | 快照不可变 + 历史 append-only ⟹ 会话内 tools/system/技能内容字节恒定,零换轨（结构保证） |
| 动态性 | 池变只作用于新会话；fork = 新快照 × 复制历史 ⟹ 会话内零热变化,无死局 |
| 隔离 | 池按 scope（official/namespace）；会话按 namespace；沙箱按 session |
| 恢复 | run 输入=快照引用,已入账 ⟹ crash 重放不需要重新决定任何事 |
| agent 切换★ | 场景=选快照（新会话,session.agent 定死,改字段 400）；功能=历史里的工具调用（swarm,P2）——均不碰快照（功能层是产品决策） |
| 成果 | 沙箱=可变草稿；deliver=按内容 hash 冻结出会话生命周期,独立留存 |
| hub | 池的 CRUD 面（Mongo 元数据+正文快照,S3 包体权威源）；**V1 例外：agent 配置包是部署目录资产**（hash 照算入快照,hub 化待用户自定义 agent） |
| 长期记忆 | namespace 级第三轴（跨会话 store,已有 memory tools） |
| model/thinking | **run 级参数,故意不进快照**：用户需即时切换；换模型=换缓存空间,不破坏同模型恒定 |
| subagents | 快照的一部分（agent 配置包声明 + 内置 catalog） |

## 2. 全景生命线

```text
平台态: 官方 seed / 用户上传·GitHub 导入·启停(独立偏好表,required 不可关) → 池
创建:   agent 选择 + 池全量快照(names+hashes) + pinned(输入框强调) → session 持久,定死
每 run: 读快照 → ledger 原子入账 → 装配:
          prompt   = agent 的 .md + 技能清单段(pinned 置顶)   ← 快照,恒定
          工具面   = 注册表/底座/skill 工具/mcp_* 三件套       ← 恒定集合与顺序
          沙箱     = backend ready(local/docker/e2b) + 技能 hash 增量物化(账本在
                     graph state,跨 worker 一致;目录缺失自愈;GC;只读加固)
        → 模型循环(文件/execute/skill(name)/mcp_*/memory/HITL 审批)
        → 事件流 → deliver(内容 hash 冻结) → 终态
延续:   steer/HITL resume=同 run;新消息=新 run(同快照);crash=重放幂等
变化:   池演进 → 新会话 / fork(复制历史+新快照);swarm 移交=P2 的历史内工具调用
终局:   会话可归档;成果独立于会话留存(内容寻址,永不漂移)
```

## 3. 咬合缝清单（已逐缝闭合;审核后补第 8 缝并修第 1 缝）

1. session 创建取池：session 直读共享 Mongo 池集合;**文档 schema 进 `contract/spec/storage.yaml` 生成 zod+pydantic 双镜像**（单源法则,不手写两份）。
2. 快照 → run：RunRequest 携带 names+hashes,ledger 原子入账即 run 级绑定（无独立 binding store）。
3. 沙箱生命周期：per-session 语义,e2b per-run 重连;销毁重建由物化自愈覆盖。
4. pinned：不收窄授权,只做清单置顶强调。
5. memory：第三轴,不进池/快照,namespace 隔离（现状已对）。
6. model/thinking：run 级,见推论表。
7. subagent：来源=配置包声明+catalog,随快照恒定。
8. 快照的完整字段（审核补缝）：`agent + agent_hash + skills 卡片全量[(name,hash,description)] + pinned_skills + mcp_servers`——清单渲染零查询;内容锁真源=S3 内容寻址 zip（Mongo 是当前版缓存,旧版走 S3 取回）。

## 4. 专题 spec 索引（本文的展开）

- skills：`2026-07-10-skills-design.md`（v2）
- MCP：`2026-07-10-mcp-design.md`
- 成果：`2026-07-10-deliver-design.md`
- agent 配置包与编排：`2026-07-10-agent-preset-design.md`（v2，阶段即技能）
- HITL 通用化：`2026-07-10-hitl-design.md`（HumanRequest 单原语）
- Python 实现美学：`2026-07-10-python-style.md`

## 5. 实施主序（认可后执行）

```text
块A hub(池的读写: Mongo+S3+seed+校验+CAS) + contract storage.yaml(池文档双镜像)
    + deliver 存储配置 schema 定案(与 workspace 配置同文件加节)      — agent 仓+contract
块B session 快照(agent+agent_hash / skills 卡片全量 / pinned_skills / mcp 定死+400,
    含 session 查池读面)                                            — session 仓+contract
块C 装配链(快照卡片渲染清单 + hash 增量物化[graph state 账本] + skill 工具双路取文) — agent 仓
块D deliver(冻结成果+读模型+下载;配置已在块A 定)                     — agent+session
块E 用户写面(上传/导入/启停/配额/管理面) + fork                      — 逐块
P2  swarm 功能层切换 / secret-ref / stage 蓝图
```
