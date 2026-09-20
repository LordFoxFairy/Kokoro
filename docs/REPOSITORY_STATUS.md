# Kokoro repository composition

状态：2026-09-20。Root 是 Git superproject：它只锁定子仓的精确 gitlink、维护跨仓治理与组合验证；每个子仓独立拥有代码、依赖锁、契约、数据、测试、CI 和发布。当前 phase-one 治理收敛记录见 [repository-governance reconciliation plan](superpowers/plans/2026-09-20-repository-governance-reconciliation-and-hygiene.md)，当前组合 SHA 与实测质量队列见 [CURRENT.md](CURRENT.md)。

## 组合清单

| Root 路径 | GitHub 仓库 | 分类 | 唯一职责 |
|---|---|---|---|
| `apps/kokoro-app` | `LordFoxFairy/kokoro-app` | deployable Web | Web UI、浏览器状态、HttpOnly session、同源 adapter |
| `apps/kokoro-mori` | `LordFoxFairy/kokoro-mori` | deployable Web | Mori 音乐产品 UI |
| `apps/kokoro-bff` | `LordFoxFairy/kokoro-bff` | service | Conversation、Message、Share、Project、ScheduledTask、公开 Product API、durable AG-UI projection |
| `apps/kokoro-agent` | `LordFoxFairy/kokoro-agent` | service | Run、Checkpoint、Lease、Tool Journal、执行事件、HITL、Evidence |
| `apps/kokoro-iam` | `LordFoxFairy/kokoro-iam` | service | Tenant、Identity、Authentication、Authorization、Role、Permission、Audit |
| `apps/kokoro-system` | `LordFoxFairy/kokoro-system` | service | Site、Host、Workspace、Runtime、Policy、Model Catalog |
| `apps/kokoro-billing` | `LordFoxFairy/kokoro-billing` | service | Payment、Subscription、Checkout、Refund、Credit、Ledger、Metering |
| `apps/kokoro-capability` | `LordFoxFairy/kokoro-capability` | service | Skills 与 MCP control plane |
| `apps/kokoro-storage` | `LordFoxFairy/kokoro-storage` | service | Blob、Upload、Asset、Artifact、Scan、object lifecycle metadata |
| `apps/kokoro-scheduler` | `LordFoxFairy/kokoro-scheduler` | service | Schedule、Occurrence、Lease、Retry、Outbox、Dispatch |
| `libs/kokoro-web-shared` | `LordFoxFairy/kokoro-web-shared` | versioned library | 独立发布的共享前端包 |

`kokoro-app` 是 Web 仓的唯一 Git 标识；Root 不使用 `kokoro/` 或 `apps/kokoro/` 作为 alias。`kokoro-mori-p1-arrangement-recording` 是已移除的 Mori worktree，不是仓库或 submodule。`kokoro-model` 已合入 System model-catalog，不在组合清单中；Capability→Platform 的独立 clean-slate cutover 尚未发生。

## Git 与版本政策

1. Root 与所有子仓本地、`origin` 只保留 `main`；每个 gitlink 锁定精确、已推送的 commit。当前精确 SHA 在 [CURRENT.md](CURRENT.md#已锁定的组合) 记录。
2. `.gitmodules` 的 `branch = main` 仅作更新提示，不能替代 gitlink 发布锁。
3. 子仓先独立 commit、验证、推送；随后才更新 Root gitlink 并执行组合验证。禁止用 `git submodule update --remote` 形成浮动发布快照。
4. Root 不建立跨仓 `pnpm-workspace.yaml`、共享语言 lockfile、共享 ORM schema、可编辑 contract 副本或 sibling source import。

## 测试与文档归属

- unit、子仓 integration、contract、lint、typecheck、build、schema 与仓内 smoke 由对应 submodule 保有。
- Root `scripts/tests/` 只测试 Root 自己的拓扑与治理脚本；未来跨仓组合 contract/integration/e2e/smoke 归 `verification/`，不复制子仓测试。
- 系统拓扑、跨仓 ADR、组合版本、部署、回滚与组合验证归 Root；业务 API、SQL schema、运行手册归事实 owner 子仓。

## 验证入口与当前判定

```bash
git submodule update --init --recursive
python3 scripts/verify-repository-topology.py
python3 scripts/verify-main-only.py
python3 -m pytest scripts/tests -q
python3 scripts/verify-ten-repository-standard.py --format json
```

2026-09-20 的组合验证中，前三项分别为 `PASS`、`PASS`、`322 passed`。最后一项报告 `110` 个 owner violation 和 `1` 个 System TypeScript `unverified`，因此其 JSON status 是 `FAIL`；这是可见的逐仓收敛队列，而非组合拓扑或 main-only 失败，也不允许被表述为全仓质量完成。

完整 clone 的复现命令与远端标识规则见 [ADR-032](kokoro-handbook/decisions/ADR-032-root-submodule-composition-and-repository-identity.md)。
