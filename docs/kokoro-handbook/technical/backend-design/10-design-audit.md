# 后端逐仓库设计审计

状态：设计审计，2026-08-21

本表审计“设计是否完整”，不把尚未迁移的实现伪装成完成。每个设计卡的目标分为 100/100；当前实现状态另列。

## 设计完整度

| 对象 | 设计卡 | 设计状态 | 当前实现证据 | 当前差距 |
|---|---|---:|---|---|
| Root | [00-root](00-root.md) | 100/100 | `contract/`、`database/`、`deploy/`、`scripts/`、`docs/` 已存在 | 还需吸收 legacy platform registry/composition |
| IAM | [01-iam](01-iam.md) | 100/100 | `database/schema/20-iam.sql`、IAM contract consumer | site/user 旧入口尚未完全合并 |
| Model | [02-model](02-model.md) | 100/100 | `database/schema/60-model.mysql.sql`、旧 model 模块、model contract | 旧模块仍有跨服务配置依赖 |
| Credit（迁移历史） | [03-credit](03-credit.md) | 100/100 | 旧 `kokoro-credit` 的边界与迁移来源 | 业务 owner 已由 `kokoro-billing` 接管；旧 writer 仍按迁移计划收口 |
| Payment（迁移历史） | [04-payment](04-payment.md) | 100/100 | 旧 `kokoro-payment` 的边界与迁移来源 | 业务 owner 已由 `kokoro-billing` 接管；旧 writer 仍按迁移计划收口 |
| Billing | [05-billing](05-billing.md) | 100/100 | `kokoro-billing` 已具备 Payment + Entitlement/Credit bounded contexts、MySQL 29 migrations、Redis coordination、OpenAPI、unit/integration/container evidence | 仍需按 cutover runbook 停止旧 writer 并完成跨仓 consumer 切换 |
| Capability | [05-capability](05-capability.md) | 100/100 | `kokoro-capability` v1 schema、public clients、MCP/Connector/Skill contract、Docker/Compose、architecture/contract/smoke evidence | v1 子仓库实现已闭环；后续仅由 GA/Agent owner 完成 dynamic source consumer 与旧 Hub 读面迁移 |
| Storage | [06-storage](06-storage.md) | 100/100 | `kokoro-storage` S3-compatible owner/schema、MinIO smoke、reconciliation | 继续按 Storage public contract 被 Capability/GA 消费，不暴露 bucket/object key |
| Session | [08-session](08-session.md) | 100/100 | `src/{relay,store,transport,http}`、大量恢复/SSE 测试 | 收敛为唯一产品 Session admission/message/projection/control owner，删除旧 Chat 双写/consumer |
| Chat 独立分仓（历史） | [07-chat](07-chat.md) | 不进入目标清单 | SQL-first `chat_*` 方案与 V1 generated consumer | 不新增 `kokoro-chat` runtime；迁移期仅作为 Root contract/database 考古 |

| Agent | [09-agent](09-agent.md) | 100/100 | `worker/agents/execution/state.py/{tools,skills,mcp,subagents,sandbox}/storage/streams` 与 [专项技术方案](../../modules/kokoro-agent.md) | 保持执行管道结构；P1 迁移 legacy Hub/PackageStore 读写到 Capability/Storage public contract，并补全真实 Redis/Mongo/MinIO integration 证据 |

## 设计 100 分的判定

设计卡只有同时明确以下七项，才记 100 分：

```text
1. 业务/运行时职责和明确的不负责项
2. 数据 owner 与唯一 writer
3. 适用的 L0/L1/L2 或运行管道模型
4. 目标目录和目录存在理由
5. 入口、公开契约和跨仓调用
6. 依赖禁止项与可自动化门禁
7. 当前证据、迁移顺序和完成证据
```

## 当前禁止继续扩张的旧边界

- 不新增 `kokoro-entitlement`。
- 不向 `kokoro-platform` 增加业务能力。
- 不新增全局 `common`、`utils`、`domain/entities` 垃圾桶。
- 不让新模块直接读取旧 Platform 子仓表。
- 不把 Agent/Session 重写为业务 DDD。
- 不用目录移动代替数据 owner、契约和测试迁移。

## 完成定义

一个仓库从“设计 100/100”进入“实现完成”，必须提供：

```text
目标目录真实存在
唯一生产入口
schema/owner inventory
contract generation/check
architecture dependency tests
unit + integration tests
公开入口 smoke
旧入口删除或明确兼容期限
```
