> 历史过程材料（Task A已收尾）：本页保留原设计／失败／验证事实，不再作为执行入口。现行边界见[当前技术总览](../../kokoro-handbook/technical/00-system-overview.md)，后继事项见[TODO](../../../todo.md)。

# Task A G0 只读证据

日期：2026-10-31（补充复核）

## 范围

本证据只证明 Root/submodule 盘点、设计文档、路径清单、native-session contract pin 和停写边界；不证明业务功能、代码清理完成或产品验收完成。

## 基线

| 仓库 | HEAD |
|---|---|
| Root | `64dcb0cd4ef88cc74337eac8ffd828ec19b14296`（C-1 阶段集成分支；基线父为 `3a3b6b91`） |
| `apps/kokoro-app` | `73b2df451c2604a6d1e9413bf07eb383b95219e9` |
| `apps/kokoro-bff` | `17d10477f4cc2966fb5083aa88839885fcd8c9e3`（Nest 预备依赖/架构门，未迁移 runtime） |
| `apps/kokoro-agent` | `c43fc3f22c676b459dd45d74438a6ccb515e5abd` |
| `apps/kokoro-iam` | `e36aed8`（native-session artifact pin；runtime 未实现） |
| `apps/kokoro-capability` | `44fcc5da599b4a5cec3077e41aaef4375fe4add2` |
| `apps/kokoro-system` | `49a5f8e5e2797ec2d1a6fcf8c5f398184821bf33` |
| `apps/kokoro-billing` | `b7c9858844df4c9b99e40e16bd9984b1d268b503` |
| `apps/kokoro-storage` | `4a990617ffe36d739b5a3e622132c304d4d48d41` |
| `apps/kokoro-scheduler` | `cfb2502b0ef9331f79a328ec85c254157340962c` |
| `apps/kokoro-admin` | `d221b18d28e15ec423798416aa8abd1f71f44bf8` |
| `apps/kokoro-mori` | `12a1060830e1239c2ccb866baeefa4546ec04bb5` |
| `libs/kokoro-web-shared` | `0c4e87ace01340aaa07bc57935f1d98b8e77af14` |

## 实际检查

### Repository topology

```text
python3 scripts/verify-repository-topology.py
status: PASS
runtime_module_count: 9
```

Continuation recheck：同一命令再次执行仍为 `PASS / 9 / 12`，相关子仓 `git status --short` 均为空。

补充复核时 C-2 预备 BFF commit 与 IAM contract commit 已在隔离工作树形成待集成 gitlink；因此当前 `verify-repository-topology.py` 会按设计报告 `kokoro-bff: checkout HEAD differs from recorded gitlink`，直到 Root 串行更新 gitlink。该 FAIL 是集成未完成证据，不改写为通过。

### 绝对路径清单

`docs/superpowers/specs/2026-10-30-task-a-cleanup-inventory.md` 当前引用 208 个绝对路径；逐项 `Path.exists()` 检查结果：

```text
missing: 0
```

### 文档 whitespace

以下文件执行 `git diff --no-index --check /dev/null <file>`，均无 whitespace 错误：

- `docs/superpowers/specs/2026-10-30-task-a-cleanup-refactor-design.md`
- `docs/superpowers/specs/2026-10-30-task-a-cleanup-inventory.md`
- `docs/superpowers/plans/2026-10-30-task-a-cleanup-refactor-execution.md`

### 全仓规范审计

```text
python3 scripts/verify-ten-repository-standard.py --format json
status: FAIL
violation_count: 224
unverified_count: 0
```

与 Task A 直接相关的已知项：BFF 缺少 NestJS runtime/bootstrap、App/Agent/BFF/IAM 兼容标记、配置边界、文件粒度和契约治理问题。该结果被记录为当前事实，不被改写成“清理已通过”。

### 文档相对链接

4 份 G0 文档共检查 6 个相对链接，`missing: 0`。

### Native-session contract pin

G0 设计材料现在固定 IAM owner artifact：

- 文件：`apps/kokoro-iam/contract/openapi/native-session-admission.v1.json`
- version：`1.0.0`
- operation：`POST /internal/v1/native-session-admission/verify`
- SHA-256：`5cf59df4b7bd9853edfd2eabb31afc236c0ec0db371f9737706fc129484fd83f`
- Cookie cutover：目标 `Path=/`、无 `Domain`、HttpOnly、SameSite=Lax、生产 Secure；旧 `/iam` 只清理不再接受
- writer：IAM contract/SDK；BFF admission consumer；App same-origin adapter；Capability `global_register` direct-credential cleanup

该 artifact 仅固定 wire/owner/版本，尚未代表 IAM controller、BFF consumer 或 App cutover 已实现；实现仍必须按 artifact digest 成对交付与验证。

## 设计与停写边界

- 方案 B：IAM native session owner；删除 first-party Web OAuth/OIDC RP；保留第三方 OAuth、MCP provider OAuth 和 Billing 资金授权。
- `localDraft` 和 Agent frozen recipe 属于当前语义，保留；只删除已确认旧协议、旧字段、旧 source-digest 特判和历史展示补偿。
- BFF 迁移 NestJS；复杂事务/lease/CAS/outbox Repository 保留，机械组合器删除。
- G0 设计门已由独立 reviewer 于 2026-10-31 APPROVED；本轮只新增/固定 contract 与设计材料，尚未写入 IAM runtime、BFF feature、App auth 或 Schema/DDL。既有 C-1 阶段提交与 BFF Nest 预备提交均不作为 C-2/C-3/C-4 完成证据。

BFF 组合引用复核：`BffBusinessStore` 27 个引用文件、`PostgresBffRepositories` 14 个、`BffApplicationServices` 5 个、`ChatRepository` 16 个、`ProjectRepository` 10 个；先迁 provider 图再删除组合器。

## 兼容命中分类

### C-1 删除/重写候选

- App `cancelledRuns` 旧状态迁移；
- App `legacyRenderAnchor` 与旧 hash conversation URL；
- App `legacyFinalId`、inline/ordered 双读、未锚定历史顺序推导；
- Agent `legacy_failed` 与旧 source digest 特判；
- BFF schema-evolution scripts、只验证 evolution 的测试和默认脚本引用。

### 当前语义保留

- App `localDraft` canonical 未提交状态；
- Agent frozen recipe 完整性校验；
- durable replay、CAS、lease、outbox、unknown/failed/取消恢复；
- MCP `sse_compat` 和第三方 OAuth 等 Task B/外部协议边界。

该分类由源码、INDEX、package script、architecture test 和反向 import graph 共同核验，不按关键词直接批量删除。

## 权威文档

- [清理重构技术方案](../specs/2026-10-30-task-a-cleanup-refactor-design.md)
- [只读盘点清单](../specs/2026-10-30-task-a-cleanup-inventory.md)
- [清理重构执行计划](https://github.com/LordFoxFairy/Kokoro/blob/bdebba56a046703400845f79ae57834d4dfa4d0a/docs/superpowers/plans/2026-10-30-task-a-cleanup-refactor-execution.md)

## G0 checklist

- [x] Root/submodule baseline frozen
- [x] Absolute-path delete/retain/rewrite inventory
- [x] BFF NestJS gap and provider migration map
- [x] Repository/Service/Port complexity classification
- [x] Compatibility/test deletion and rewrite matrix
- [x] Login/OAuth方案 B与native-session admission design gate
- [x] C-1～C-4 stop-write boundaries
- [x] Native-session admission artifact/version/digest fixed
- [x] C-1 implementation evidence pinned separately at `docs/superpowers/evidence/2026-10-31-task-a-c1-cleanup-implementation.md`
- [x] G0 reviewer approval and user release gate (2026-10-31 reviewer APPROVED; user requested continuation)
- [ ] C-1 post-cleanup verification against current gitlink set
