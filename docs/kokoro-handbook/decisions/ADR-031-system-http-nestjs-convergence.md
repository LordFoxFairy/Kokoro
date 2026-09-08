# ADR-031 System HTTP 与完整 NestJS 收敛

状态：已接受，待实施（2026-09-07）。本决策承接用户确认的完整 System 交付，不把单个 Site CRUD 切片当最终结果。

## 放置与范围

| 项目 | 决定 |
|---|---|
| Owner | Root 拥有跨仓协议/拓扑裁决；System 拥有本仓业务与机器契约；消费者各仓修改自己的 client |
| 当前事实 | System 7dde8e7：Node HTTP/pg/Site Connect；Model ddf1f55：HTTP+Connect/Prisma；BFF实际使用HTTP，Agent Model client未接线 |
| 目标职责 | 完整 System 的站点/域名/工作空间/产品/应用/Feature/exposure/策略/Manifest/Model控制面 |
| 位置比较 | 采用现有 Root decisions 中 ADR，而非 System 单仓 ADR 覆盖全局；字段/SQL设计仍只在 System |
| 粒度 | 本文件仅裁决跨仓协议与收敛范围；不复制各仓机器schema |
| 依赖 | owner contract先提交，consumer后更新；单仓单writer；未交接变更不触碰 |
| 数据/API | 唯一System数据库访问栈与schema；HTTP internal-owner /v1；新鲜数据库，不迁移旧开发数据 |
| 删除 | 完成cutover时删除旧Site/Model RPC、生成物、旧Model服务身份/配置/部署与协议副本；不是本次文档写入立即删除 |
| 验证 | System全门禁/fresh schema/真实PG-Redis，消费者contract/integration，Root拓扑与smoke；未测生产SLO不报通过 |

## 决策

1. System 使用 NestJS 原生业务模块与 DI，Node 24 LTS，Express adapter。
2. System 目标只提供 HTTP/OpenAPI，包括合入后的 Model Catalog。Site Connect 无仓内外部生产调用；
   BFF 已使用 HTTP。Model 文档所称 Agent RPC caller 未在当前生产源码找到，不以目标文档代替接线证据。
3. 本决策明确替代 ADR-029 中保留 kokoro.model.v1 Proto namespace/transport 的要求；保留的是 Model 业务词汇、
   model_* 数据owner边界、不可变revision、routing/resolve语义，不保留无消费者的第二协议栈。
4. 单向事实源：System运行时 Zod schema生成只读 OpenAPI；不同时手写同一形状的class DTO/OpenAPI/Proto。
   消费者使用固定version/commit/digest的owner artifact或本仓窄HTTP client，禁止共享ORM/源码。
5. 目标数据库采用 SQL-first + pg；单一 canonical database/schema.sql。Model的Prisma adapter通过独立受测切片替换，
   不保留两套生产访问路径。此决定不要求 IAM 等其他owner更换ORM。
6. 业务模块为sites、workspaces、products、runtime-manifests、model-catalog。域名/站点策略归sites；
   applications/features/exposures/presentation与现有配置发布行为归products，不新增独立releases模块。
7. 完整交付包括各资源适用的创建/读取/更新/删除或明确状态转换；不是把任意不可变资源都做通用CRUD。
   新普通配置保存后生效；现有发布版本资源的发布/退役不变量继续保留并补齐binding流程，禁止静默丢行为。
8. Model Catalog只管理定义/供应方/不可变版本/标签/选用规则/可用性与解析结果，不转发推理或拥有计费。
9. Model能力中的availability仍保持清晰语义；当前provider health投影先在providers内实现，不预建无用目录。
10. Workspace承接System内tenant/site范围的工作空间身份与生命周期，不创造第二组织、BFF Project或执行机器。
    Runtime Manifest为配置投影；没有消费者契约的执行Runtime/调度能力不在此范围。

## 安全与一致性底线

- PG为事实，Redis只缓存/协调；tenant及global operator作用域来自受信认证边界。
- 保留当前幂等receipt、事务锁、tenant隔离、generation fence、BIGINT精度保障；删除旧实现前由新测试承接。
- IAM未交付的internal AuthZ/SDK不伪造成功；身份接入只消费已明确可验证的契约。
- Model故障不能摘除Site/Workspace基础读；不得把health探测做成每个CRUD的实时provider调用。
- 不取消外部未知consumer而冒称无影响：首次正式发布前核对artifact/部署清单；发现真实consumer则纳入同一cutover。

## 候选比较

- 保留HTTP+Connect：继续两套契约与生命周期；当前没有生产consumer收益，不采用。
- 全面切换gRPC：需要改写BFF现有HTTP并新增AgentRPC依赖，缺乏当前需求，不采用。
- 统一HTTP/OpenAPI：匹配Nest与BFF现状，减少生成/传输分叉；采用，承担显式breaking review与consumer切换成本。
- Prisma-first：与IAM经验一致但System特殊锁/索引需重新适配；本次选择pg，Model adapter重写成本独立记录并验证。

## 实施顺序与完成定义

Root先冻结整体边界；System负责人先完成技术/API/数据三面及机器contract/schema，Root审查与验证后授权源码。
之后同一System writer连续推进完整功能、测试、CI、运行文档；Root在owner契约提交后串行集成消费者及拓扑变化。
内部切片用于review/commit，不需要用户逐片确认，也不改变完整交付范围。

静态盘点发现BFF对System/Model的HTTP路径缺少/v1，必须作为消费者任务闭环。Agent实际Model解析调用和旧Model服务退出
必须有真实证据；未完成即保留未完成，不用新增但未接线的client文件或历史测试冒充完整cutover。

