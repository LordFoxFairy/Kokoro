# Kokoro Root 文档索引

这是 Root `docs/` 的最小导航入口，面向贡献者、主控 Agent 和并行 worker。Root 文档只拥有跨仓治理、架构决策、仓库拓扑、部署编排与质量门禁；业务 API、数据库 Schema、生成代码和实现细节必须留在事实 owner 子仓。

## 必读顺序

1. [`CURRENT.md`](CURRENT.md)：当前有效文档白名单、实施主线和已确认边界。
2. [`task.md`](task.md)：当前唯一任务状态表、依赖顺序、owner 与阶段门。
3. [`progress.md`](progress.md)：当前 commit、命令输出、审查结论和风险的追加证据账。
4. [`CODEBASE_MAP.md`](CODEBASE_MAP.md)：九个 active repository 的 owner、目录、运行链路和派工上下文。
5. [`ARCHITECTURE_STANDARD.md`](ARCHITECTURE_STANDARD.md)：中文工程标准、分层、类型、SQL、API、Web、测试和 Agent 执行协议。
6. [`REPOSITORY_STATUS.md`](REPOSITORY_STATUS.md)：仓库映射、事实归属、归档状态和最近可用证据；HEAD、分支和 clean 状态必须以审计命令的当前输出为准。
7. [`kokoro-handbook/README.md`](kokoro-handbook/README.md)：稳定的跨仓产品与技术手册。

## 按任务查找

| 任务 | 入口 |
| --- | --- |
| 了解活动仓边界 | [`CODEBASE_MAP.md`](CODEBASE_MAP.md)、[`REPOSITORY_STATUS.md`](REPOSITORY_STATUS.md) |
| 初始化/验证 Submodule 组合 | [`REPOSITORY_STATUS.md`](REPOSITORY_STATUS.md)、[ADR-032](kokoro-handbook/decisions/ADR-032-root-submodule-composition-and-repository-identity.md)、[`../scripts/verify-repository-topology.py`](../scripts/verify-repository-topology.py) |
| 修改架构或跨仓规则 | [`ARCHITECTURE_STANDARD.md`](ARCHITECTURE_STANDARD.md)、[`kokoro-handbook/technical/`](kokoro-handbook/technical/) |
| 设计/修改 API | 先定位事实 owner，再阅读该仓 `contract/README.md` 与 `docs/API_CONTRACT.md`；Root 不复制契约 |
| 设计/修改 SQL | 先定位事实 owner，再阅读该仓 `database/schema.sql` 与 `docs/DATA_MODEL.md`；Root 不复制 Schema |
| 执行质量门禁 | [`../scripts/INDEX.md`](../scripts/INDEX.md) 与各 owner README/ACCEPTANCE；旧全仓 runner 已暂停，System 隔离 smoke 不是全仓门 |
| 查看已验证事实 | [`reports/`](reports/)；报告必须包含 commit、命令、结果和时间 |
| 给 Agent 派工 | [`CODEBASE_MAP.md`](CODEBASE_MAP.md) + [`ARCHITECTURE_STANDARD.md`](ARCHITECTURE_STANDARD.md) 第 11 节 |
| 跟踪后端闭环 | [`task.md`](task.md)、[`progress.md`](progress.md)、[批准设计](superpowers/specs/2026-09-20-kokoro-backend-closure-design.md)、[当前 Wave 1A 计划](superpowers/plans/2026-09-22-wave-1a-iam-session-admission.md)、[已验收 Wave 0B 计划](superpowers/plans/2026-09-21-wave-0b-hard-link-closure.md)、[已验收 Wave 0A 计划](superpowers/plans/2026-09-21-wave-0a-governance-and-contract-gates.md) |

## 文档层级

```text
当前事实与入口  -> CURRENT.md / CODEBASE_MAP.md / REPOSITORY_STATUS.md
长期规则与决策  -> ARCHITECTURE_STANDARD.md / kokoro-handbook/
任务与进度      -> task.md / progress.md
实施计划        -> superpowers/plans/
短期派工        -> handoffs/
验证证据        -> reports/
历史与研究      -> product/、prototypes/、research/、brainstorm/
```

历史、研究和过程文件不能覆盖当前规范；实现尚未完成的目标架构必须明确标记为缺口，不能把设计文档当作运行证据。新增跨仓规则先沉淀到 Root 手册，再由各 owner 子仓落到自己的 contract、Schema、代码、测试和 CI。
