# 测试与工程门禁规范

状态：当前补充，2026-09-04。命令与目录分别见 [TS](08-typescript-backend-engineering.md)、[Python](09-python-backend-engineering.md)、[SQL](03-sql-and-postgresql.md)。

## 1. 按风险选择证据

| 变更                   | 必需证据                                                                |
| ---------------------- | ----------------------------------------------------------------------- |
| 纯规则、状态、授权判断 | 单元与非法分支测试                                                      |
| Repository/SQL         | 真实 PostgreSQL、tenant、Row 映射、提交/回滚测试                        |
| Schema                 | 空库安装、catalog drift、无外键、选定约束/索引测试；V1 不做历史迁移兼容 |
| API/RPC/事件           | 机器契约、生成 drift、成功/错误/权限/未知字段/序列化与消费者测试        |
| 模块和依赖             | AST import/公开边界检查及违规样本测试                                   |
| 幂等和并发             | 多独立 client 的重复、竞争、未知提交与恢复测试                          |
| Redis/provider         | 真实依赖集成和故障注入；固定响应替身只说明本方分支                      |
| 启动和退出             | 构建/安装后的真实进程 smoke、health/ready、信号与资源回收               |

只有存在对应能力时才建立对应套件；不为无数据库服务生成空 SQL 测试。测试层级被聚合或单独执行必须写明，unit 通过不代表 integration 已跑。

## 2. 隔离与真实性

- 单元测试不依赖外部服务；集成使用真实对应基础设施。
- 复用本地已存在的 PostgreSQL/Redis 实例，每个 run/worker 独立数据库/schema/key prefix，只清理自身资源。
- 生产不包含 Fake/Fixture/InMemory；使用语言手册规定的测试目录。
- 重构前固定保留行为基线，批准改变的行为写新契约断言。clean-slate 删除旧实现，不保留双轨，但不跳过行为验证。
- 不缩小 tsconfig/test glob、不大量 skip、不以 echo/true 代替检查制造绿色。

## 3. 可执行门禁

每仓 CI 执行格式、lint、类型、unit、相关 integration/contract/architecture、build/package 和 smoke；数据 owner 额外执行 schema 安装与 drift。
检查器必须有有效/违规样本，测试其误报和漏报。根级正则扫描只作预检，不证明语义、性能、权限或运行可靠性。

报告记录当前 commit、环境/依赖版本、命令、退出码、通过/失败/跳过数量和未运行原因；Agent 自评分和历史报告不替代当前输出。
涉及容量、延迟、SLO 时必须另有代表性负载与观测证据，而不是用代码风格或测试数量推导“生产级”。
