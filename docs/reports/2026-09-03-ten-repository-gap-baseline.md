# 十仓生产级重构缺口基线

生成时间：2026-09-04T01:58:40Z  
Root：codex/production-closure-governance @ 50ce4262310b  
结构审计：**FAIL（337 项）**——这是冻结的修复队列，不是完成结论。

## 1. 范围与证据规则

正式范围固定为 Web、BFF、Agent 与七个业务 owner，共十仓。每条结论绑定
[`2026-09-03-ten-repository-gap-baseline.json`](2026-09-03-ten-repository-gap-baseline.json) 中的完整
HEAD、dirty path 和结构化诊断。
历史报告、旧“100 分”评分、worker 退出码均不作为后续完成证据。

开始时只有 kokoro-bff 存在协作者改动 docs/api/v1/agui-chat.md；本轮保留该文件，不覆盖、不回滚。

## 2. P0 正确性问题

### P0-AGENT-001：Redis 请求流可裁剪，但 PostgreSQL pending dispatch 没有独立 dispatcher 扫描恢复

- 影响：HTTP ingress 在落 pending dispatch 后直接 XADD；若消息在 worker 消费前被 maxlen 裁剪，数据库 intent 不会自动重新投递，Run 可永久停在 pending。
- 证据：kokoro-agent/src/kokoro_agent/http/ingress.py:185-207、kokoro-agent/src/kokoro_agent/streams/redis.py:139-145、kokoro-agent/src/kokoro_agent/worker/supervisor.py:223-232
- 退出条件：admission transaction 写 Run + outbox；独立 dispatcher 持续扫描未发布行；trim、进程崩溃和重复发布测试均收敛到一个 Run。

### P0-AGENT-002：Run launch 和 evidence/control 尚未把受信 tenant context 收敛为所有持久化操作的显式谓词

- 影响：POST /v1/runs 仍从 body 构造 execution_identity；evidence 只按 run_id 查询，Run schema/repository 主要依赖 run_id、session_id、namespace，缺少统一 tenant_id SQL predicate。
- 证据：kokoro-agent/src/kokoro_agent/http/server.py:146-205、kokoro-agent/src/kokoro_agent/http/ingress.py:104-118、kokoro-agent/src/kokoro_agent/http/ingress.py:260-283、kokoro-agent/src/kokoro_agent/infrastructure/schema.py:32-103
- 退出条件：tenant/actor/subject 仅来自受信 middleware/context；Run/control/evidence/checkpoint/chat/memory 全部带 tenant_id 或等价强类型 scope，并有跨租户负向测试。

### P0-AGENT-003：Worker lease 和 tool effect 缺少贯穿写路径的 generation fencing

- 影响：旧 worker 只在下一次 heartbeat 才取消；多数写操作不校验 generation/lease token。tool journal 的 INSERT 返回 winner，但 middleware 忽略返回值，竞争 loser 仍可执行副作用。
- 证据：kokoro-agent/src/kokoro_agent/worker/supervisor.py:289-310、kokoro-agent/src/kokoro_agent/infrastructure/postgres_run_repository.py:662-721、kokoro-agent/src/kokoro_agent/infrastructure/postgres_run_repository.py:908-937、kokoro-agent/src/kokoro_agent/tools/middleware.py:252-271
- 退出条件：claim 返回 generation + lease_token；所有状态/event/tool 写入验证 fencing；只有 tool journal insertion winner 调用 handler；双 worker 故障注入证明副作用至多一次。

### P0-MORI-EXPOSURE-001（条件性发布阻断）

kokoro-mori 不属于正式十仓，但 kokoro-mori/src/app/api/v1/mori/[...path]/route.ts:23-33 使用默认
shared secret、namespace 和 principal 为请求注入可信身份。它保持未部署；任何公开暴露前必须删除默认凭据和
伪造身份并接入真实 session/IAM admission。

## 3. 十仓静态缺口

| 仓库 | 规则缺口数 | 开始状态 |
|---|---:|---|
| kokoro | 100 | clean |
| kokoro-bff | 62 | dirty: docs/api/v1/agui-chat.md（保留） |
| kokoro-agent | 54 | clean |
| kokoro-iam | 10 | clean |
| kokoro-system | 22 | clean |
| kokoro-model | 32 | clean |
| kokoro-billing | 22 | clean |
| kokoro-capability | 12 | clean |
| kokoro-storage | 8 | clean |
| kokoro-scheduler | 15 | clean |

规则聚合：

| Rule | 数量 |
|---|---:|
| documentation | 86 |
| openapi-governance | 57 |
| supply-chain | 46 |
| file-granularity | 31 |
| css-specificity | 21 |
| typescript-strictness | 19 |
| python-strictness | 11 |
| contract-provenance | 7 |
| sql-naming | 7 |
| container-reproducibility | 6 |
| layered-topology | 6 |
| production-doubles | 6 |
| real-integration | 4 |
| agui-ui-adapter | 3 |
| canonical-schema | 3 |
| container | 3 |
| quality-gates | 3 |
| security-gate | 3 |
| agent-contract | 2 |
| contract-owner | 2 |
| shared-local-infrastructure | 2 |
| toolchain | 2 |
| accessibility | 1 |
| container-supply-chain | 1 |
| durable-agui-projection | 1 |
| public-contract | 1 |
| single-agent-protocol | 1 |
| source-local-runtime | 1 |
| web-bff-boundary | 1 |

完整逐项明细只保存在 JSON，避免 Markdown 复制 300 余条并形成第二事实源。

## 4. 执行优先级

1. **P0 Agent**：先写复现测试，再修 durable admission/outbox、tenant scope、generation fencing/tool winner；
2. **P1 BFF**：公开 OpenAPI、真实 PostgreSQL store、显式 owner adapters、幂等/outbox、durable AG-UI projection；
3. **P1 Web/协议**：删除 direct IAM 与 legacy SessionEvent 双读，接入 AgUiChatTransport，补安全同源 adapter；
4. **P1 SQL/类型/供应链**：canonical schema、UTC、严格类型、真实 lint/integration、镜像和 workflow 门禁；
5. **P2 文档与可维护性**：十仓文档矩阵、contract provenance、超大模块/CSS、可访问性和 Developer API 门户。

## 5. 并行边界

- 一个仓库同一时刻一个写入 Agent；七 owner 的文档/contract provenance 可以并行；
- Agent P0 由单一写入 Agent 串行完成三个测试驱动切片；
- BFF contract 先提交后，Web 才更新消费者；AG-UI 字段不由 Root 或 Web 复制定义；
- 主工作区在每个 worker 完成后重跑本仓门禁，最终才执行十仓 full verifier。

## 6. 当前门禁命令

    uv run --frozen pytest scripts/tests -q
    python3 scripts/verify-repository-topology.py
    python3 scripts/verify-ten-repository-standard.py --format json

第三条当前预期返回 1 并稳定报告 337 项；修复完成的唯一结构标准是返回 0 且
violation_count=0。
