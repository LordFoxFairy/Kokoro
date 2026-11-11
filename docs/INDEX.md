# Kokoro 文档索引

[总入口](README.md)面向团队统一阅读。本页只列活动入口；业务字段、SQL 和生成制品仍由子仓 owner 维护。

## 产品与工程首读

1. [工作台使用指南](../apps/kokoro-app/developer-docs/docs/product/index.md)：开始使用、聊天与结果、项目／定时、支持范围。
2. [PRD](kokoro-handbook/product/09-v2-prd.md)：用户对象、批准需求与非目标，不当完成报告。
3. [当前技术总览](kokoro-handbook/technical/00-system-overview.md)：实际链路、原生认证、AI SDK、文件与调度。
4. [CURRENT](CURRENT.md)：当前交付事实；[Task A TODO](../todo.md)：唯一当前暂存事项。
5. [代码地图](CODEBASE_MAP.md)、[仓库组合](REPOSITORY_STATUS.md)：定位实际 owner、目录及精确组合政策。

## 按问题定位

| 问题 | 入口 |
| --- | --- |
| 架构／owner／跨仓边界 | [总体架构](ARCHITECTURE_STANDARD.md)、[长期手册](kokoro-handbook/README.md)、有效 ADR |
| API／数据变更 | 对应子仓 `contract/`、`docs/API_CONTRACT.md`、`docs/DATA_MODEL.md` 和 canonical schema；不从旧原型推字段 |
| Web 用户文档或公开 API 文档 | App [门户维护说明](../apps/kokoro-app/developer-docs/README.md)；API 参考只由固定 BFF artifact 生成 |
| 类型／SQL／事务／API／测试规范 | [工程手册](kokoro-handbook/standards/)及 Root [AGENTS](../AGENTS.md) |
| 当前验证命令 | [scripts 索引](../scripts/INDEX.md)及各 owner README/ACCEPTANCE；不因改文档启动全产品测试 |
| Task B | [独立交接入口](handoffs/2026-10-30-task-b-capabilities-account.md)，保留其负责人、原 PR 和未验状态 |
| 历史与旧验收 | [历史任务记录](task.md)、[历史证据账](progress.md)、[报告](reports/)；日期／commit／真实依赖界定范围，旧“当前”标题不覆盖最新事实 |

## 维护边界

长期决定归 `kokoro-handbook/`；临时方案只在需要时按主题读取。已被替代的 Task A 四份计划、旧 Session 产品拓扑已退役，可从 `bdebba56` 的 Git 历史追溯，不再列为实施入口。其它 owner 的需求、计划与原始证据不批量删除。

保留 [ADR-032](kokoro-handbook/decisions/ADR-032-root-submodule-composition-and-repository-identity.md)、[ADR-034](kokoro-handbook/decisions/ADR-034-independent-admin-web.md)、[ADR-035](kokoro-handbook/decisions/ADR-035-direct-internal-service-authentication.md)、[ADR-036](kokoro-handbook/decisions/ADR-036-bff-nestjs-convergence.md)等有效边界；本次只更新已被最终实现替代的说明，不新造规则中心。
