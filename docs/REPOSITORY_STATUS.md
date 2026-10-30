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

## 2026-10-27 产品闭环 Draft 组合（非发布）

用户授权逐仓PR对齐。全部候选已推送，仍保Draft、未合并/部署，不以测试数字替代产品验收。App原22与Billing原7工作树变更已按依赖闭包提交，不再依赖隐形运行覆盖；未交接的Root进度文档保持原工作树，不整树覆盖。唯一逐动作入口为原闭环计划§2.1。

| Owner | 精确候选 | Draft PR |
| --- | --- | --- |
| kokoro-system | `49a5f8e5e2797ec2d1a6fcf8c5f398184821bf33` | [#2](https://github.com/LordFoxFairy/kokoro-system/pull/2) |
| kokoro-capability | `8cfead647856ef54ec851a3bebe169a3ca14d212` | [#12](https://github.com/LordFoxFairy/kokoro-capability/pull/12) |
| kokoro-billing | `b7c9858844df4c9b99e40e16bd9984b1d268b503` | [#4](https://github.com/LordFoxFairy/kokoro-billing/pull/4) |
| kokoro-agent | `d0815143f55b0879b3cbdc4a8eeb5694dece07e0` | [#46](https://github.com/LordFoxFairy/kokoro-agent/pull/46) |
| kokoro-bff | `11777152bf8fe2ae316e4c67fb355eab94e7c0b5` | [#17](https://github.com/LordFoxFairy/kokoro-bff/pull/17) |
| kokoro-admin | `d221b18d28e15ec423798416aa8abd1f71f44bf8` | [#5](https://github.com/LordFoxFairy/kokoro-admin/pull/5) |
| kokoro-app | `ea04903928ac0f5ba6f231e9f2f73215daa1a0e0` | [#46](https://github.com/LordFoxFairy/kokoro-app/pull/46) |

本轮真实闭合：Project根页独立新任务草稿与旧会话URL/锁定隔离；真实资源上传→fresh详情→原生900000B同SHA下载（该次90ms），同名本地413更正后不残留旧错误；真实Asset删除200的ACK延迟→unknown→关闭重开→404回读→同key/空body重放200且replayed=true，只移除目标并保兄弟；精确批准的QA Project删除202后返回/app、fresh侧栏不再出现。普通资源父/子面板读取无可见通用加载/错误重试面板；390px无横溢。项目逻辑删除与后台物理清理分层，不把202当物理完成。

工程证据分层：BFF默认2005PASS/3原资源SKIP、contract1176PASS及相关构建/静态/生成检查通过；Billing默认1864PASS/630资源SKIP、独立真实PG44PASS/零残留。App最终72路径组合1480相关、lint/build/types及11既有生成check通过；其前一阶段完整门6027PASS/1FAIL：Next Webpack开发fixture读取0字节react-loadable-manifest导致请求prepare阶段JSONEOF，真实trace已绑定，未靠刷绿/放宽门禁抹掉。最后仅空DELETE流API守卫增量定向/真实HTTP验证，未冒最终字节完整门全绿。所有PR保留此缺口、不合并；正常Turbopack与发布生产构建不混称这一开发系统门。

全产品目标仍开放：Project成员协作权限/执行绑定、外部Provider/OAuth事实及Skills精确分享/作者系列删除等依唯一计划继续；不拿私有URL、空目录或候选协议假代替。全接口100ms并未证明，不把单次90ms下载外推。正常旧Agent/Billing账本及原样本保持，无新付费Run/充值/费率发布。本批复用已授权topic分支；历史main-only记录不作为删除未合并分支的依据。
