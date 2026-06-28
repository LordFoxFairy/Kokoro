# 测试清单

## 范围

本文定义 Kokoro 的分层测试策略、各仓门禁命令，以及必须覆盖的反例矩阵和 e2e gate。目标：合并前可证明主链路不坏、计费不超扣、站点不串站。

## 测试分层

```text
单测        纯逻辑、计算、解析、bucket 选择、状态机转移。无外部依赖。
集成        repository / API / schema 行为，跨进程或带 DB/Redis/Mongo。
E2E         真实链路：web -> session -> agent -> back，含 SSE 与 HITL。
```

外部 API、DOM、provider、浏览器全局必须 mock；端到端验证用真实 Redis + Mongo，不用 memory fake 兜底。

## 各仓门禁

每仓提交前跑（命令以各仓为准）：

Agent:

```bash
cd kokoro-agent
uv run pytest
uv run pyright
uv run ruff check src tests
```

Session:

```bash
cd kokoro-session
bun test
bun run typecheck
bun run lint
```

Web:

```bash
cd kokoro-web
bun test
bun run typecheck
bun run lint
bun run build
```

平台服务（kokoro-platform）:

```bash
pnpm typecheck
pnpm test
pnpm lint
```

## schema 改动追加门禁

涉及 Prisma schema、repository 或 HTTP API 时，除上面命令外必须跑集成测试：

```bash
pnpm test:integration
```

不跑集成测试就改 schema 视为门禁未过。

## 必须覆盖的反例

这些反例不是可选项，缺一即不算覆盖：

- [ ] 幂等重试不重复扣：同 `idempotencyKey` 重放 N 次，余额只变一次。
- [ ] 余额不足：hold 必失败返回 402，不产生负余额。
- [ ] capture/release 后账平：ledger 与 bucket 余额一致，release 不留悬挂 hold。
- [ ] webhook 去重：同 provider event id 只处理一次。
- [ ] 同邮箱跨站隔离：same email / same OAuth subject 在两个 site 创建两个 user。
- [ ] siteId 过滤：site A admin 不能查询 site B 数据；artifact/order/credit 查询默认带 siteId。
- [ ] job context 不中途切站：长任务全程 siteId 不丢、不串站。
- [ ] sitemap 不跨站：只输出当前 site URL。
- [ ] 长任务失败 release hold：失败/取消/超时额度恢复，不漏扣。

站点隔离反例清单见 [../decisions/ADR-001-site-boundary](../decisions/ADR-001-site-boundary.md)；计费反例见 [../business-flows/credit-reserve-commit-refund](../business-flows/credit-reserve-commit-refund.md)。

## E2E gate

主链路端到端必须通过：

```text
sse-loopback   web 发消息 -> session 写入 -> agent 产 events -> SSE 回放 -> web 展示，
               刷新后 snapshot 恢复。
hitl-e2e       human-in-the-loop：工具审批暂停 -> 人工决策 -> resume -> 终态正确浮现。
```

E2E 用 `KOKORO_LOCAL_FAKE_MODEL=1` 跑稳定管线，必要时再接真实 provider 验证。

## 验收闭环

合并前逐项确认：

- [ ] 改动仓的门禁命令全绿（typecheck / test / lint）。
- [ ] 改动 schema/repository/API 的，`test:integration` 全绿。
- [ ] 反例矩阵中受影响项有对应测试且通过。
- [ ] 主链路 sse-loopback 与（涉及 HITL 时）hitl-e2e 通过。
- [ ] 无隐式 skip 的测试，无被忽略的类型/lint 错误。

本地起服务和分层调试见 [local-development](local-development.md)。
