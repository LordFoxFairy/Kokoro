# kokoro-agent 架构与技术方案对齐审计

日期：2026-08-22
范围：`kokoro-agent` 代码、运行时契约、sandbox workspace/S3 配置、Agent 技术文档。
非范围：Compose/Kubernetes、Storage/Capability 子仓部署实施、浏览器或业务产品面改造。

> **归档边界。**本报告只记录当日 V1 源码的 owner、目录和验证事实；它不是 GA 的目标实现规格，也不证明
> `FeatureAssembly`、native `DeepAgentState`、official `SwarmState`、GA-first SkillRuntime 或 公共运行契约 已迁入代码。
> 当前目标统一以 [36 GA 整体方案](../kokoro-handbook/technical/36-ga-final-agent-technical-plan.md)、
> [38 公共运行契约](../kokoro-handbook/technical/38-ga-public-runtime-contract.md) 和
> [ADR-020](../kokoro-handbook/decisions/ADR-020-native-framework-compatibility-and-swarm-adapter.md) 为准。

## 1. 结论

Agent 的正确架构不是“等外部 client 的业务服务”，而是一个可独立闭合的执行运行时：

```text
RunRequest + RuntimeConfig + Agent runtime state
  -> worker claim / assembly / execution / HITL / terminal claim
  -> raw event
```

浏览器、Desktop、CLI 和 Session 是请求/消费方，不是 Agent core 的运行前提。没有 client 时，
worker 不会收到新 request；已有 run 的恢复和终态仍由 Agent 自己的 ledger、checkpoint、
control/event 流完成。

`S3Workspace` 已定性为 GA 管理的**可选 sandbox workspace adapter**：当前 S3 profile 接 MinIO 的
S3-compatible API，默认部署 profile 仍为 local workspace；未来以配置切到 AWS S3、Ceph RGW、R2 或其他 S3-compatible provider。
它不等于 Storage 的 Artifact/Asset writer，也不应把 S3 的可用性变成 core execution 的前提。

## 2. 当前代码事实

| 执行责任 | 实现证据 | 结论 |
|---|---|---|
| 进程入口、请求消费、lease/recovery | `worker/main.py`、`worker/supervisor.py` | Agent 自己拥有 runtime 调度，不依赖浏览器 client。 |
| 本次 run 装配 | `agents/`、`agents/assembly/` | 将 RunRequest 的 model、permissions、capability grants、sandbox 组装为可调用图。 |
| 调用、HITL、终态和 raw events | `execution/{build_agent,run_agent,events,approvals}.py` | 执行闭环位于 Agent，不由 Session/Client 承担。 |
| 执行状态 | `state.py`、`storage/{ledger,checkpoints,memory_store,mongo}.py` | Agent 是自己的 run/checkpoint/memory/raw-event owner；不写 Chat/Session 业务事实。 |
| 可授权能力 | `tools/`、`skills/`、`mcp/`、`subagents/`、`sandbox/` | 五个 sibling package 是 capability runtime 的当前物理形态。 |
| Sandbox workspace | `sandbox/{backend,archive,docker_backend}.py` | `state` 与本地 workspace 不要求 S3；`local_shell/docker + S3Workspace` 才增加归档装饰器。 |
| S3 provider 选择 | `sandbox/archive.py:S3Workspace` | 只含 `endpoint/bucket/region/force_path_style`，通过 boto3 的 S3 API 接入，不耦合 MinIO SDK。 |

## 3. 文档对齐结果

| 原问题 | 已完成的对齐 |
|---|---|
| `09-agent`、`26`、`27` 把 `run/capabilities/providers/persistence` 写成未存在的强制物理目录 | 改为语义分组；明确实际目录是 `agents/execution/state.py/{tools,skills,mcp,subagents,sandbox}/model/storage`，不做目录大搬家。 |
| 文档没有明确 Agent core 与外部 client 的关系 | `09-agent` 增加核心闭环、执行硬依赖/可选能力分类、owner 和禁止依赖。 |
| Storage 文档把所有 Agent 的 S3 使用都等同于 Artifact 业务写入 | `29` 增加 §9.0，区分可选 sandbox workspace 归档与必须走 Storage contract 的 Artifact。 |
| 把 CA 写成全部 Skill 的主控 | `09`、Agent 专项 §6 与 `29` §9 改为 GA-first：默认 Skill 直接绑定；GA `find_skill` 向量发现 GA catalog 与 CA user/session path；CA/Storage 仅提供路径、管理和 bytes 辅助，命中后由 GA 加载并 append-only 注入 run binding。 |
| S3Workspace 的 MinIO 当前配置与未来 provider 切换缺少统一口径 | `09`、`26`、`27`、`29` 全部确定为 S3-compatible adapter；MinIO 是当前 S3 profile，默认 profile 是 local workspace。 |
| `modules/kokoro-agent` 混有已不存在的 `assets/` 目录和历史 V1 结构 | 重写为 11 节当前执行设计：真实目录、生命周期、数据 owner、依赖/失败语义、S3 边界、current/target 迁移表与验收矩阵。 |
| `03/11/12/20` 的历史细节可能被当作当前 Agent 目录或 Storage/Capability owner | 在每篇开头加入作用域与冲突裁决：保留 V1 交互/HITL 行为价值，当前 source tree、owner 与迁移规则回到 `09 + module + 29`。 |
| Agent 文档地图仍把历史 `19/03` 当作当前入口 | `13-agent-docs-map` 改为按 `CURRENT -> 09 -> module -> 20 -> 29 -> 12 -> 27` 的权威层级阅读，并给出冲突裁决。 |
| 当前白名单漏掉 Agent/Storage 的新权威入口 | `docs/CURRENT.md` 更新日期并加入 `29` 与 `09`。 |

## 4. 设计 100 分审计

设计评分只评价方案是否完整、可审阅、可证明；不把未迁移的 legacy writer 或未运行的真实
依赖 integration 错写成实现完成。

| 评分维度 | 分值 | 文档证据 | 结论 |
|---|---:|---|---|
| 运行时职责与不负责项 | 20 | `09-agent` 的“定位/核心闭环/数据 owner”与专项方案 §1 | 完整。 |
| 数据 owner 与唯一 writer | 15 | 专项方案 §3、§6 的 lifecycle 和 owner/current-target 表 | 完整；legacy writer 明列迁移门禁。 |
| 复杂度选择 | 15 | `09-agent`“架构等级”、专项方案 §4 | 完整；执行 pipeline，不套 DDD 目录模板。 |
| 目录可读性 | 15 | 专项方案 §4 的真实 source tree | 完整；移除已不存在的 `assets/` 目录叙述。 |
| 依赖可执行性 | 15 | `09-agent`“依赖规则与可自动化门禁”、`test_architecture.py` | 完整；worker 方向、config 单点、product-service 禁止项可检查。 |
| 公开契约 | 10 | 专项方案 §2、generated contract gate | 完整；输入、控制、输出与禁止泄漏对象明确。 |
| 测试映射与迁移证据 | 10 | 专项方案 §10-11、`verify-backend-design.py` | 完整；静态/契约/真实依赖证据分层，迁移完成条件明确。 |
| **合计** | **100** | 设计卡、专项方案、文档地图、验证器 | **设计文档 100/100**。 |

实现完成度单独保留 P1/P2 迁移项，不能和上表的设计完成度混写。

## 5. 自动化保护与验证

新增/收紧的测试：

- `tests/test_architecture.py`
  - execution core 不得反向 import `worker`；替换了此前只检查不存在 `run/` 目录的空洞断言。
  - Agent 不得 import `kokoro_session`、`kokoro_web`、`kokoro_storage`、`kokoro_capability`、
    `kokoro_chat`、`kokoro_iam`、`kokoro_payment`、`kokoro_credit` 等 product-service package。
- `tests/test_workspace_archive.py`
  - 保留无 S3 配置时使用本地 backend 的断言。
  - 增加 `force_path_style=false` 的非 MinIO S3-compatible endpoint 配置断言。
- 清理测试文件的 import/unused-import 问题，使静态门禁重新全绿。

本轮实际验证：

```text
cd kokoro-agent
uv run ruff check .
# All checks passed

uv run pyright
# 0 errors, 0 warnings

uv run pytest tests/test_architecture.py tests/test_boundary_pragmas.py \
  tests/test_contract_gate.py tests/test_workspace_archive.py -q
# 75 passed, 5 skipped

python3 scripts/verify-backend-design.py
# backend design manifest: 10 repositories, 0 errors
```

该 verifier 现额外校验 Agent 设计卡的架构等级、闭环、owner、S3、目录、依赖、契约、
证据和迁移门禁段落，以及专项方案的 11 个设计章节、历史文档的 authority-routing 标记和
相关相对链接；同时比对专项方案列出的 runtime source tree 是否真实存在，避免 100 分只
停留在 manifest 数字。

`5 skipped` 是没有可达 MinIO 时的真实 S3 round-trip 组；配置和本地 fallback 组仍已执行。
完整 `uv run pytest -q` 已启动并确认集成前置缺失时按设计 fail-loud：首个 E2E 在
`redis://127.0.0.1:6379/0` 被拒绝连接，Mongo fixture 的清理也因此等待。它不构成
Agent core 代码失败的证据，但当前环境也没有提供全量 Redis/Mongo/MinIO integration 的绿色证据。

## 6. 剩余设计门禁

| 优先级 | 项目 | 完成判据 |
|---|---|---|
| P1 | GA-first SkillRuntime 切换 | GA 直接绑定默认 Skill；以 `find_skills/load_skill` 聚合自身 catalog 与 CA user/session path；候选用 opaque `candidate_ref`，成功后写 GA thread workbench `.kokoro/skills.lock`。删除 worker legacy Hub 直读和启动期 seed/upsert；CA/Storage 故障不阻止只依赖默认 Skill 的 core run。 |
| P1 | 真实依赖集成验证 | 提供 Redis、Mongo、MinIO 后，全量 Agent suite 通过；覆盖 lease/recovery/HITL、MCP snapshot、workspace S3 archive 与 delivery。 |
| P2 | S3 credential/provider profile | 现有 access-key/secret-key 已覆盖 MinIO 与静态 S3 凭据；引入 AWS IRSA/STS、SSE、私有 CA 或 provider capability 时，只扩展 sandbox adapter/config profile，并增加真实 provider contract test。 |
| P2 | architecture test 深度 | 当前 import test 保护 Python 包耦合；后续可加 AST/network port inventory，防止以 HTTP/SDK 形式绕过 product-service package import 门禁。 |

这些门禁不要求 Compose/Kubernetes 调整，也不改变“Agent core 自闭环、外部能力可选”的设计结论。
