# 后端工程规范入口（旧版已撤销）

状态：2026-09-04 已由三份专项手册替代。本文件仅保留文档导航，不再保存另一套目录、SQL 或类型规则。

- [Root 执行控制手册](../../../AGENTS.md)：owner、工作流程、文档门、验收与协作。
- [总体架构](../../ARCHITECTURE_STANDARD.md)：当前/目标仓库拓扑与业务边界。
- [SQL 手册](../standards/03-sql-and-postgresql.md)：Schema、字段、约束、事务与数据生命周期。
- [TypeScript 手册](../standards/08-typescript-backend-engineering.md)：业务模块、文件命名、Fastify、配置、类型与验证。
- [Python 手册](../standards/09-python-backend-engineering.md)：业务 package、类型、async、配置与验证。

旧版强制四层、Port 目录、五份同构类型和旧仓边界不再用于实现。Scheduler 的 Go 方案与版本由其当前技术设计和 go.mod 维护，不从旧综合规范复制。
