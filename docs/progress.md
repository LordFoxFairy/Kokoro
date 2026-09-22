# Kokoro 后端闭环进度证据账

本文件只追加已执行事实，任务状态以 [`task.md`](task.md) 为准，目标设计以 [`superpowers/specs/2026-09-20-kokoro-backend-closure-design.md`](superpowers/specs/2026-09-20-kokoro-backend-closure-design.md) 为准。没有命令输出、commit 或冻结 SHA 的事项不得写成完成。

## 2026-09-21 — W0A-0 启动

### Goal

Codex Goal 已建立并保持 `active`：按已批准的 Kokoro 后端整体闭环设计维护统一任务与进度台账；Root 主控审查，子 Agent 逐仓实施 Wave 0–7；Billing 最后处理。

### 冻结基线

- Root：`1bc74ae536d8a2da48f76045da95c2d5c2877750`
- 分支：Root 与已初始化子仓均以 `main` 为唯一工作分支；当前组合由 `.gitmodules` 和 gitlink SHA 定义。
- 工作树：开始本切片前 `git status --short --branch` 输出 `## main...origin/main`，无未提交变更。
- 已批准设计：`docs/superpowers/specs/2026-09-20-kokoro-backend-closure-design.md`

### 已确认决策

1. 仅 `apps/kokoro-app` 是本轮前端；Mori 与其他前端不改。
2. Web → BFF 使用 HTTP/OpenAPI + AG-UI/SSE；Platform/Storage 使用 ConnectRPC/Proto；IAM/System/Agent/Scheduler/Billing 使用 owner HTTP/OpenAPI。
3. 本地与 CI 使用一个 PostgreSQL 实例和一套应用 role/credential；每个数据 owner 仍使用独立 database/schema，禁止跨 owner SQL、ORM 或 Schema 共享。
4. 当前正式身份仍是 `kokoro-capability`；只有 Wave 3 原子切换全部完成后才写成 `kokoro-platform`。
5. Billing 位于 Wave 6，在身份、存储、Platform、执行链和 System 闭环之后处理。

### 当前审计事实

- Root 默认测试最近基线：`python3 -m pytest scripts/tests -q` 为 `322 passed`。
- Root 全仓静态治理仍为红：`verify-ten-repository-standard.py --format json` 报告 `110 violations, 1 unverified`；该结果是改造队列，不是成功证据。
- 已确认硬断链：BFF → Capability `/bff/*`、BFF → Storage `/internal/bff/library`、Capability → Storage Proto v1、BFF ↔ Scheduler `jobs/schedules` 与 callback header/time format。
- 已确认身份缺口：Web 仍直连 IAM，BFF admission 尚未完整闭环。

### 当前动作

- W0A-0：建立 `docs/task.md`、`docs/progress.md` 与 Wave 0A 实施计划。
- 下一步：Root 验证并提交 W0A-0；随后按计划派发 W0A-1，Root 只做审查与集成。

### 尚未形成的完成证据

- 本节创建时尚未执行变更后的 Root 门禁，W0A-0 仍为“进行中”。
- 尚未修改任何 owner 代码、contract 或 Schema。
- 尚未完成 Capability → Platform cutover，也未启动 Billing 实施。

## 2026-09-21 — W0A-0 验收

- 交付文件：`docs/task.md`、`docs/progress.md`、`docs/INDEX.md`、`docs/CURRENT.md`、`docs/superpowers/plans/2026-09-21-wave-0a-governance-and-contract-gates.md`。
- 计划审查经历三轮实质修正：补齐 16-edge/非法旁路矩阵、commit-blob pin、generator/runtime 版本绑定、topology ID 基线和全部负向测试；最终只读审查为 `Blocking 0 / Important 0 / Minor 0`。
- `python3 scripts/verify-repository-topology.py`：exit 0，`status=PASS`，9 个 runtime owner 与 2 个非 runtime submodule 均匹配 gitlink/remote/main。
- `python3 -m pytest scripts/tests -q`：exit 0，`322 passed in 3.24s`。
- Markdown 相对链接检查：exit 0，`PASS`。
- `git diff --check`：exit 0，无空白错误。
- 本切片只建立治理控制面，没有修改任何子仓代码、contract、Schema 或 gitlink；W0A-1 仍为下一项待派工任务。

## 2026-09-21 — W0A-1 派工

- 写入 Agent：`w0a1_governance_writer`（`gpt-5.6-sol`，high）。
- 基线：Root `1cc8b85591401de062f2b80771894e696b31b3c9`，`main` 与 `origin/main` 对齐且工作树 clean。
- 获准文件：`AGENTS.md`、`docs/ARCHITECTURE_STANDARD.md`、`docs/kokoro-handbook/standards/03-sql-and-postgresql.md`、`docs/CURRENT.md`、`scripts/tests/test_engineering_handbooks.py`。
- Root 保留 `docs/task.md`、`docs/progress.md`、Git index、commit、push、规格审查、质量审查和集成验证；子 Agent 不提交。

## 2026-09-21 — W0A-1 验收

- 实现 Agent：`w0a1_governance_writer`；基线 `1cc8b85591401de062f2b80771894e696b31b3c9`。
- TDD RED：`python3 -m pytest scripts/tests/test_engineering_handbooks.py -q` 为 `1 failed, 3 passed`；Fix Round 1 新门先为 `3 failed, 4 passed`。
- 任务审查首轮发现 canonical schema、Agent→System 协议边和测试强度 3 个 Important；Fix Round 1 后 SPEC `✅`、QUALITY `✅`，Critical/Important/Minor=`0/0/0`。
- Root 精确提交：`14ee7146`（`docs(architecture): align database and protocol authority`），仅包含五个获准文件。
- 提交后 `python3 scripts/verify-repository-topology.py`：exit 0，`status=PASS`，`runtime_module_count=9`。
- 提交后 `python3 -m pytest scripts/tests -q`：exit 0，`326 passed in 3.22s`。
- `git show --check --stat --oneline HEAD` 与 `git diff --check`：exit 0。
- 已锁定：共享 local/CI PostgreSQL role、独立 owner database/schema、SQL-first/ORM-first 唯一 schema、完整协议矩阵、Capability 当前身份和 Wave 3 Platform 原子切换条件。

## 2026-09-21 — W0A-2 派工

- 写入 Agent：`w0a2_contract_verifier_writer`（`gpt-5.6-sol`，high）。
- 基线：Root `73b373db73b4df572d8ce7557032bdd10efb21f5`，`main` 与 `origin/main` 对齐且工作树 clean。
- 获准文件：`scripts/governance/contract_inventory.py`、`scripts/verify-contract-compatibility.py`、`scripts/tests/test_contract_compatibility.py`。
- Root 保留真实 inventory、任务/进度账、Git index、commit、push、审查与集成验证；本任务只实现 verifier 与隔离 fixture。

## 2026-09-21 — W0A-2 验收

- 实现 Agent：`w0a2_contract_verifier_writer`；独立审查 Agent：`w0a2_contract_verifier_reviewer`；基线 `73b373db73b4df572d8ce7557032bdd10efb21f5`。
- 初审为 SPEC `✅`、QUALITY `❌`，发现 3 个 Important：Git option injection、缺失 child checkout 的不稳定异常、version assertion 可由无关 JSON pointer 伪造。
- Fix Round 1 关闭 option injection；复审继续发现 2 个 Important：version evidence 的无效 UTF-8 仍抛异常、任意 JSON 父路径仍可伪造依赖 pin。
- Fix Round 2 将 version evidence 收敛到 fail-closed `npm-package-json`：canonical `package.json`、runtime=`dependencies`、generator=`devDependencies`、RFC 6901 package identity 与冻结 blob version 同时绑定；无效 UTF-8 返回稳定错误。
- 最终独立复审：SPEC `✅`、QUALITY `✅`，Critical/Important/Minor=`0/0/0`。
- Root 精确提交：`ba51947e`（`test(contracts): verify frozen owner and consumer pins`），只包含三个获准文件：`scripts/governance/contract_inventory.py`、`scripts/verify-contract-compatibility.py`、`scripts/tests/test_contract_compatibility.py`。
- 提交后 `python3 scripts/verify-repository-topology.py`：exit 0，`status=PASS`，`runtime_module_count=9`。
- 提交后 `python3 -m pytest scripts/tests/test_contract_compatibility.py -q`：exit 0，`38 passed in 11.79s`。
- 提交后 `python3 -m pytest scripts/tests -q`：exit 0，`364 passed in 15.11s`。
- `git show --check --stat --oneline HEAD` 与 `git diff --check`：exit 0。
- 真实 `consumer-inventory.json` 尚未建立；默认 compatibility CLI 在 W0A-3 前保持“inventory 缺失”的稳定红门。

## 2026-09-21 — W0A-3 派工

- 写入 Agent：`w0a3_inventory_writer`（`gpt-5.6-sol`，high）。
- 基线：Root `311a1391a6752961e61a6c5236527bc58f9196ec`，`main` 与 `origin/main` 对齐且工作树 clean。
- 获准文件：`verification/contracts/consumer-inventory.json`、`verification/contracts/README.md`、`scripts/INDEX.md`。
- Root 保留任务/进度账、Git index、commit、push、审查与集成验证；子 Agent 必须从 Root gitlink 与 child commit blob 计算证据，不读取脏工作树作为冻结事实。

## 2026-09-21 — W0A-3 验收

- 实现 Agent：`w0a3_inventory_writer`；独立审查 Agent：`w0a3_inventory_reviewer`；基线 `311a1391a6752961e61a6c5236527bc58f9196ec`。
- 冻结 `verification/contracts/consumer-inventory.json`：16 条批准 edge（1 active、15 broken）与 1 条 `EDGE-WEB-IAM-DIRECT` 非法旁路；owner、evidence 与唯一 active version assertion 均绑定 Root gitlink 和 child commit blob digest。
- hardened npm assertion 固定 `manifest_kind=npm-package-json`、`package_name=next`、`version=16.2.6` 与 `/dependencies/next`；15 条 broken edge 不伪造 version assertion。
- 独立审查：SPEC `✅`、QUALITY `✅`，Critical/Important/Minor=`0/0/0`，逐项核对 edge、owner tuple、protocol、state、版本、reason 与 evidence。
- Root 精确提交：`95afb3c3`（`test(contracts): freeze complete consumer inventory`），只包含 `verification/contracts/consumer-inventory.json`、`verification/contracts/README.md`、`scripts/INDEX.md`。
- 提交后 `python3 scripts/verify-repository-topology.py`：exit 0，`status=PASS`，`runtime_module_count=9`。
- 提交后 `python3 -m pytest scripts/tests/test_contract_compatibility.py -q`：exit 0，`38 passed in 11.80s`。
- 提交后真实 compatibility CLI：预期 exit 1；错误精确为 15 条 `declared broken` + 1 条 `illegal edge`，schema/gitlink/digest/evidence/version 漂移为 0。
- 提交后 `python3 -m pytest scripts/tests -q`：exit 0，`364 passed in 15.04s`；`git show --check` 与 `git diff --check`：exit 0。

## 2026-09-21 — W0A-4 双审启动

- 冻结审查 SHA：Root `ff5f91191ad33f39f80272df546af34d1b691e0e`；该 SHA 已推送，`main` 与 `origin/main` 对齐。
- 规格审查 Agent：`w0a_final_spec_reviewer`；质量审查 Agent：`w0a_final_quality_reviewer`；两者只读、独立、绑定同一 SHA。
- Root 保留最终门禁、任务/进度账、提交、推送和 W0B 放行决定。

## 2026-09-21 — W0A-4 最终验收

- 初始双审绑定 `ff5f91191ad33f39f80272df546af34d1b691e0e`，各发现 1 个 Important：Scheduler outbound event 的 canonical contract owner 错绑 receiver；Git `replace` refs 可改变声明 OID 的读取结果。
- 规格修复提交 `68a53463`（`fix(governance): bind scheduler event contract owner`）：架构矩阵恢复 contract owner 列；两条 Scheduler event edge 绑定 Scheduler canonical OpenAPI；BFF/Agent 保留 receiver evidence；计划、README 与回归同步。
- 质量修复提交 `d0f012a1`（`fix(contracts): ignore local Git replace objects`）：使用 `git --no-replace-objects show --end-of-options`，helper 与完整 verifier 都有 replace-ref 回归。
- 最终冻结 SHA：`d0f012a1ef7a5b4914b4b631122482d5f121ca01`。独立规格审查 SPEC `✅`；独立质量审查 QUALITY `✅`；两者 Critical/Important/Minor 均为 `0/0/0`，绑定同一 SHA。
- `python3 scripts/verify-repository-topology.py`：exit 0，`status=PASS`，`runtime_module_count=9`。
- `python3 -m pytest scripts/tests -q`：exit 0，`367 passed in 15.66s`。
- `python3 scripts/verify-ten-repository-standard.py --format json`：exit 1，`9 repositories / 110 violations / 1 unverified`；这是后续 owner 改造队列，不冒充通过。
- `python3 scripts/verify-contract-compatibility.py --inventory verification/contracts/consumer-inventory.json`：预期 exit 1，`16 edges / 1 violation`；错误仅为 15 条 `declared broken` 与 1 条 `illegal edge`，其他漂移为 0。
- `git diff --check`：exit 0。Wave 0A 治理基线、机器门和冻结 inventory 已闭环；下一阶段进入 W0B owner-first 硬断链修复。
- W0B compatibility 红队列：`EDGE-WEB-BFF`、`EDGE-BFF-IAM`、`EDGE-BFF-SYSTEM`、`EDGE-BFF-CAPABILITY`、`EDGE-BFF-STORAGE`、`EDGE-BFF-AGENT`、`EDGE-BFF-SCHEDULER`、`EDGE-BFF-BILLING`、`EDGE-AGENT-SYSTEM`、`EDGE-AGENT-CAPABILITY`、`EDGE-AGENT-STORAGE`、`EDGE-CAPABILITY-STORAGE`、`EDGE-CAPABILITY-IAM`、`EDGE-SCHEDULER-BFF`、`EDGE-SCHEDULER-AGENT` 与 `EDGE-WEB-IAM-DIRECT`。

## 2026-09-21 — W0B-0 计划冻结与控制面切换

### 基线与范围

- Root 起始 SHA：`bfa054f3cafe0e340a8e04d567bf923dbe03ee4e`；开始时 `main == origin/main`、工作树 clean。
- 当前实施计划：`docs/superpowers/plans/2026-09-21-wave-0b-hard-link-closure.md`，480 行，最终审查 SHA-256 `3481acfb6ac1d0431fd349c4f0a23a27948f94dee609a9b215e4644d9fd097be`。
- 本切片只修改 Root 计划、任务表、进度账和文档索引；没有修改子仓、gitlink、contract、Schema 或运行代码。

### 子 Agent 审计与裁决

- Capability/BFF 只读审计确认 W0B 使用当前 Capability HTTP 四个 `/v1/*` projection，而不是恢复旧 Capability RPC；BFF 旧 `/bff/*` 与 `q/query` 已漂移。计划裁决 public API 只接受 canonical `query`，`q` 返回 400；Wave 3 再原子切到 Platform ConnectRPC。
- Scheduler 只读审计确认 owner `/schedules/{name}`、`X-Kokoro-Scheduler-Schedule`、RFC3339/RFC3339Nano、opaque idempotency key 与 retry status 已一致；BFF 的 `/jobs`、旧 header/time/error 已漂移。计划把 BFF receiver 的 generated/Node 作为 consumer evidence，把 Scheduler `go.mod` 作为独立 producer evidence。
- Storage consumers 只读审计确认 BFF 废止 HTTP、Agent 缺 adapter、Capability 仍固定 Storage v1，且 caller×operation×scope 授权依赖 Wave 1。W0B 只删除死 HTTP；三条 Storage edge 留给 W2，不伪造激活。
- W0B 退出状态冻结为：active `EDGE-BROWSER-WEB`、`EDGE-BFF-CAPABILITY`、`EDGE-BFF-SCHEDULER`、`EDGE-SCHEDULER-BFF`；12 条明确 broken；非法旁路仍仅 `EDGE-WEB-IAM-DIRECT`。

### 计划审查

- 架构审查经历 owner/consumer 语义、Storage 范围和 Browser generator 豁免修正；最终 `SPEC ✅`，Blocking/Important/Minor=`0/0/0`，绑定计划 digest `3481acfb…fd097be`。
- 执行审查经历 repository writer 拆卡、真实 smoke、精确工具链、vendor provenance/generator、逐 edge checkpoint、精确文件集与 tenant 语义修正；最终 `EXECUTION ✅`，Blocking/Important/Minor=`0/0/0`，绑定同一 digest。
- 计划最终拆为 W0B-0..16：Root 主控保留架构、任务账、Git index、集成和最终验收；子 Agent 逐 owner 串行实施；两个真实 smoke 各自独立成 Root 任务。

### 实测工具链

```text
BFF Node: v22.22.2
Capability Node: v24.20.0
BFF/Capability pnpm via Corepack: 11.25.0
BFF/Capability TypeScript: 5.9.3
Scheduler: go1.26.8 / GOTOOLCHAIN=auto
Root Ruff: 0.15.2
```

### 下一步

W0B-1 由 Root governance 子 Agent 实现 consumer/producer manifest 解析和三个逐 edge checkpoint；Root 主控随后独立审查、复跑门禁、精确提交并推送。W0B 尚未改变任何业务 edge 状态，真实 compatibility 基线仍是 1 active / 15 broken / 1 illegal。

### W0B-0 Root 验收命令

- `python3 scripts/verify-repository-topology.py`：exit 0，`status=PASS`，9 个正式 runtime、2 个非 runtime submodule 均匹配。
- `python3 -m pytest scripts/tests -q`：exit 0，`367 passed in 16.60s`。
- `git diff --check`：exit 0，无空白错误。
- W0B-0 达到计划冻结门；业务实现、gitlink 提升和 edge 激活仍全部未开始。

## 2026-09-21 — W0B-1 consumer/producer 与 checkpoint 机器门验收

- 写入 Agent：`w0b1_governance_writer`；基线 Root `bf16916dbed17e585f08cd3bf2a0c4ebd29b0036`；共享 checkout 未由 worker 暂存、提交或推送。
- TDD 初始 RED：focused pytest 在新模块缺失时 collection exit 2；首版 GREEN 后 fresh review 又用独立 fixture 复现 2 个真实缺口：非 canonical whitespace 的重复 Go directive 可绕过、错误 producer manifest kind 会触发未捕获 `ValueError`/CLI traceback。
- Fix Round 1 RED：`5 failed, 75 passed`；覆盖三类隐藏 whitespace 重复 directive、verifier 异常和两个 CLI traceback。修复后 field×manifest 使用 fail-closed 允许矩阵，W0B producer 只允许 `go-mod`；Go directive 同时识别空格/tab/前导空白并要求唯一 canonical `go X.Y.Z`。
- 三份 checkpoint fixture 现逐项固定完整 active/broken/illegal ID 集，不以数量替代身份验证；checkpoint CLI 只接受声明的 broken/illegal outcome，任何其他 compatibility drift 都失败。
- 最终独立复审：SPEC `✅`、Blocking/Important/Minor=`0/0/0`；QUALITY `✅`、Critical/Important/Minor=`0/0/0`。
- Root 复跑：focused `80 passed in 29.20s`；全量 `406 passed in 32.08s`；Ruff format/check、`py_compile`、`w0b-start` checkpoint、topology 与 `git diff --check` 全部 exit 0。
- Root 精确提交并推送：`dc05459a`（`test(contracts): verify consumer and producer runtimes`），仅包含任务卡 10 个文件；`verification/contracts/consumer-inventory.json`、gitlink、子仓和业务 edge 状态未改变。
- 当前 compatibility 基线仍是 `w0b-start`：1 active / 15 broken / 1 illegal。下一任务为 W0B-2，只读验证 Capability owner release。

## 2026-09-21 — W0B-2 只读审计与 W0B-2A owner 修复派工

- 只读验证 Agent：`w0b2_capability_owner_verifier`；Root 基线 `60cd4a79e2a2ecff11d8d7961d486ff92fec947c`；Capability frozen release `e576d38dd103c2fda4d6389385b3f04f82ddfc20`。
- 冻结 release 的 Node `24.20.0`、pnpm `11.25.0`、TypeScript `5.9.3` 可复现；format/lint/typecheck/contract/build 均 exit 0；focused `11 passed`；full `650 passed / 177 skipped / 0 failed`；Root、child 与 live remote 均 clean、main-only、SHA 对齐。
- Owner artifact `1.0.0` 的 direct SHA-256 为 `c24f5b42bd9f92f5f149e93fc455b55ae3a451e2d30ca08ef899088d717af8f4`，combined provenance 为 `6eb170d12bd046aa70b2a1b8aa775c6303e46ffc997cb4193f77fc230072d3b5`；但验证发现四类实质漂移，故未把 W0B-2 冒充验收：runtime/docs/test 仍接受未发布的 `q` alias；runtime 未执行 `query/tags/provider_key` 的声明上限；三份当前设计文档误称 inactive Platform artifact 未实现；错误 envelope 缺少 Root 标准要求的 `retryable`。
- Root 裁决为独立 owner-local W0B-2A：OpenAPI 提升到 `2.0.0`，只保留 canonical `query`，按 Unicode code point 执行参数边界，request ID 只保留响应 header，错误 retry 语义由 Capability 固定；无 Prisma/schema/data-owner 变化。
- 写入 Agent：`w0b2a_capability_owner_writer`（`gpt-5.6-sol`，high）；精确任务卡位于 ignored SDD workspace 的 `task-2a-capability-owner-repair.md`。Root 保留 Git index、commit、push、Root gitlink、consumer inventory、双审和最终复跑；W0B-3 在新 owner release 验收前不启动。

## 2026-09-21 — W0B-2A owner release 与 W0B-2B Root repin

- Capability owner repair 经两轮 TDD 修正后由独立 SPEC/QUALITY reviewer 对最终 21 文件 diff 复审，结论均为 `0 blocking/critical, 0 important, 0 minor`。
- 新 owner release 已精确提交并推送到 Capability `main`：`7f89a267d745cbb9870f52d6edb23dec1a3c469b`（`fix(http): publish canonical Capability projection contract`）；local、`origin/main` 与 live remote 一致，remote 只保留 `main`。
- OpenAPI `2.0.0` direct digest 为 `e0b7c4b57ac030efb73878b51da2a3595ec0172bce0608a88ea925b57a69761a`，combined provenance 为 `536dca2989a5a9b7e06f1bcd15ef8eb25876ef4184345b077407555457e45c4b`。契约固定四个 GET、canonical `query`、Unicode code point 参数上限、header-only request ID、`retryable` 错误语义与 typed dependency failure；Prisma/schema、Proto、generated、package/lock 和 Platform artifact 未改变。
- Root fresh pre-commit verification 使用 Node `24.20.0`：format/lint/typecheck/contract/platform-artifact/schema/build 全部 exit 0；focused `35 passed`；full `663 passed / 177 skipped / 0 failed`；范围与禁止变更检查通过。独立 post-commit release 复验与 Root 集成验证仍在执行，因此任务状态保持“待集成验证”。
- W0B-2B inventory writer 仅更新 `verification/contracts/consumer-inventory.json`：9 个 Capability tuple pin 到新 SHA，并从新 commit blob 重算两个实际变化的 controller digest；未改变任何 edge state/protocol/reason/version/runtime assertion。Root 主控负责 gitlink、权威计划、当前状态与最终 checkpoint。

## 2026-09-21 — W0B-2 验收完成

- 独立只读 Agent `w0b2_release_reverify` 在已推送 commit 上复跑全部 Capability 门：format/lint/typecheck/contract/platform-artifact/schema/build 全部 exit 0；focused `26 passed`、direct-digest `9 passed`、full `663 passed / 177 skipped / 0 failed`；确认 21 文件范围、四路由、OpenAPI `2.0.0`、digest、无 schema/Proto/generated/package/lock 漂移，结论 PASS。
- Root 集成提交 `3d2fa8a11acc7ffe18c87875c4131ecc011a46bd`（`fix(integration): pin Capability HTTP owner release`）已推送；它只提升 Capability gitlink、刷新全部 Capability fan-out tuple/digest，并同步 CURRENT、W0B 权威计划与控制账。
- Root 在该 commit 上复跑 topology、main-only、`w0b-start` exact checkpoint、全量 governance tests 与 diff check：全部 exit 0，`406 passed`；Root、全部子仓与 live remote 均 clean、只保留 `main`。当前 compatibility 基线仍诚实保持 1 active / 15 broken / 1 illegal。
- `verify-ten-repository-standard.py --format json` 继续报告既有 `110 violations / 1 unverified`，与 W0B-2 owner contract repair 无关，未被弱化或冒充通过。W0B-2 已验收，下一任务是 W0B-3：冻结 BFF Capability 设计与 owner artifact。

## 2026-09-21 — W0B-3 已派工

- Root 已完成新建文件/目录前放置裁决，精确任务卡位于 ignored SDD workspace 的 `task-3-bff-capability-design.md`。本切片只允许 BFF 的 9 个 contract/config/docs/test 文件，不改 runtime、package/lock、public OpenAPI 或数据库 schema。
- 写入 Agent `w0b3_bff_capability_designer`（`gpt-5.6-sol`，high）负责 RED→GREEN：从 Capability commit blob 冻结 OpenAPI `2.0.0`、dependency provenance 与生成配置，并让 TECHNICAL_DESIGN/API_CONTRACT/DATA_MODEL/CURRENT 对齐 HTTP-only consumer 目标。
- Root 主控保留规格审查、质量审查、BFF Git index、commit/push、Root gitlink 与最终验证；W0B-4 在 W0B-3 双审和 owner artifact 验收前不启动。

## 2026-09-21 — W0B-3 验收完成，W0B-4 已派工

- W0B-3 初审发现并修复两处真实 owner 语义偏差：Capability response correlation header 必须是 `x-kokoro-request-id`；Skills cursor 含 subject scope，而 MCP cursor 只绑定 tenant/operation/provider filter，BFF 不自造 MCP subject binding。修正后 SPEC/QUALITY 均为 `0/0/0`。
- BFF 提交 `8a66158f4ec19f09d995bc92917b117fc1d2ab89`（`docs(bff): freeze Capability projection consumer design`）已推送，local、`origin/main` 与 live remote 一致且 remote main-only。它精确包含 9 个允许文件；vendored blob 与 Capability owner commit byte-for-byte 一致。
- Root 在该 commit 上使用 Node `22.22.2` 复跑 lint/typecheck/build、focused `28 passed`、contract `16 passed`、full `160 passed`、owner blob compare 与 diff check，全部通过；generator config 另由质量 reviewer 在隔离环境实际生成两次，16 文件 byte-identical。
- Root gitlink 按 W0B 计划暂不提升：BFF W0B-4/W0B-5 完成后由 W0B-6 一次刷新全部 fan-out 并激活 edge。当前 checkout 前移不等于 Root 已集成。
- W0B-4 任务卡位于 ignored SDD workspace 的 `task-4-bff-capability-consumer.md`，续派同一 Agent 实现 generated client/facade/四路由切换。为避免实现后 CURRENT 与三文档门失真，计划范围补入四份现有设计文档；无新目录 owner、无数据库/schema 变化。

## 2026-09-21 — W0B-4 验收完成，W0B-5 已派工

- BFF Capability consumer 经两轮 TDD 修正和完整双审收敛。最终 SPEC 与 QUALITY 均为 `0/0/0`；旧问题（稳定错误码、strict response、cursor、非四 GET fail-closed、generated allow-list、public cursor schema、generated suppression 与文档当前态）全部关闭。
- BFF 提交 `2ed792586e89c035155938078d9b07f33af95abd`（`fix(bff): align Capability projection client with owner v1 routes`）已推送；local、`origin/main` 与 live remote 一致，remote 只保留 `main`，工作树 clean。提交精确包含任务卡 36 文件。
- Node `22.22.2` / pnpm `11.25.0` 下，Root pre-commit 与 post-commit 均复跑 generation/contract/focused/full/build：16 个 generated 文件连续两次 byte-identical，contract `19 passed`，focused `69 passed`，full `173 passed`，build 通过；integration `30 skipped / 0 failed`，原因是该门需要显式测试数据库与 Redis 环境。
- Root 独立核对 owner commit blob、vendor digest `e0b7c4b57ac030efb73878b51da2a3595ec0172bce0608a88ea925b57a69761a`、manifest config/lock/generated digests、无 TypeScript/ESLint suppression、无 legacy `/bff/*`/搜索 alias、无 schema/config/operation baseline 漂移，全部通过。
- Root gitlink仍按计划不提升：W0B-5 必须先用真实 Capability/BFF 进程、独占数据库、Redis namespace 与端口完成八个 case，W0B-6 才一次刷新 BFF fan-out 并激活 `EDGE-BFF-CAPABILITY`。当前 compatibility 仍保持 1 active / 15 broken / 1 illegal。
- 本机预检已确认 Node `22.22.2`、Node `24.20.0`、`psql`、`redis-cli` 可用；`postgresql://localhost/postgres` 以当前用户连通，`redis://127.0.0.1:6379` 返回 `PONG`。W0B-5 任务卡固定只写 Root smoke runner、其测试与 `scripts/INDEX.md`，不改子仓、gitlink、inventory 或控制文档。
- W0B-5 派工后的 Root runtime/contract 交叉核对发现计划把“缺 BFF auth”误写为 401；live BFF 强制配置 shared secret，当前实现与 public OpenAPI 都固定为 `403 service_auth_failed`，401 在配置完成的 live 运行态不可达。Root 已把该 smoke case 更正为 403，禁止 worker 为迎合旧文字伪造运行态。

## 2026-09-21 — W0B-5 验收完成，W0B-6 已派工

- 写入 Agent `w0b5_capability_bff_smoke_writer` 完成 Root 隔离 smoke；独立可靠性审查 `w0b5_smoke_reliability_reviewer` 最终 QUALITY `✅`，Critical/Important/Minor=`0/0/0`。Root 精确提交并推送 `97c98bf95dc270d605ffa46817ef9b1850405c67`（`test(e2e): add isolated Capability BFF smoke`），仅包含 runner、测试与 `scripts/INDEX.md`。
- Runner 强制 BFF Node `22.22.2` 与 Capability Node `24.20.0`，创建本次唯一拥有的两个 PostgreSQL database、Redis prefix、loopback ports 与 process groups；真实 BFF HTTP surface 的 8 个 case 全部通过，其中缺 BFF auth 为 canonical `403 service_auth_failed`。
- Root 独立复验：focused `26 passed`；Ruff format/check、`py_compile` 全部 exit 0；Root full tests `432 passed in 30.18s`；真实 CLI 两次均输出 `status=PASS,cases=8`。故障注入测试经真实 `run_smoke(..., fault_injection=...)` 证明 mid-flight 失败仍按逆序清理。
- 真实 CLI 后残留探针：PostgreSQL `w0b_cap_%` database=`0`，Redis `kokoro:w0b:capability:*` key=`0`，BFF/Capability `dist/main.js` process=`0`，临时目录=`0`。owner 日志证据固定唯一 `trace_id` 与精确 `/v1/skills` operation；W0B-4 unit 继续负责 literal query forwarding 断言。
- W0B-6 由 `w0b6_capability_integration_writer` 独占 Root 四个集成文件：提升 `apps/kokoro-bff` gitlink 到已推送 `2ed792586e89c035155938078d9b07f33af95abd`，刷新全部 BFF fan-out commit-blob evidence，并只激活 `EDGE-BFF-CAPABILITY`。Root 主控保留 Git index、commit/push、交叉审查与冻结 SHA 独立复验。

## 2026-09-21 — W0B-6 写入完成，待独立审查

- 唯一写入 Agent `w0b6_capability_integration_writer` 基于 Root `274dee1b1640e5e4fa189fb735e230383dba780c` 完成四文件集成切片；未操作 Git index、未提交、未推送。`apps/kokoro-bff` checkout 与已推送 `origin/main` 均为 `2ed792586e89c035155938078d9b07f33af95abd`；`apps/kokoro-capability` 保持 `7f89a267d745cbb9870f52d6edb23dec1a3c469b`。
- `consumer-inventory.json` 已从 frozen BFF commit blob 重算全部 BFF fan-out tuple/digest；`EDGE-BFF-CAPABILITY` 唯一从 broken 切为 active，owner 固定 Capability HTTP OpenAPI `2.0.0` / `e0b7c4b…61a`，consumer evidence 固定 dependency manifest、vendor、generator config/script、16 个 generated 文件、facade、行为测试、`package.json`、`pnpm-lock.yaml` 与 `.node-version`。生成器 assertion 为 `@hey-api/openapi-ts@0.99.0`，运行时 assertion 为 Node `22.22.2`。
- 因 Root 主控保留真实 Git index，本 Agent 使用 Root index 的临时副本，仅把 BFF gitlink设为 prospective release进行机器验证；真实 index 始终未改。`w0b-capability` checkpoint exit 0；raw compatibility按预期 exit 1，精确为 14 条 `declared broken` + 1 条 `illegal edge`，其他漂移为 0；prospective topology exit 0，`runtime_module_count=9`。
- Root full governance tests 在仅对 Root cwd 使用 prospective index 的 Git wrapper 下为 `432 passed in 35.26s`。首次把 `GIT_INDEX_FILE` 全局传给 pytest 会污染测试创建的临时 Git 仓并产生 fixture setup errors；该次结果已废弃，修正为 cwd-scoped wrapper后全量通过，临时 index/wrapper均已删除。
- `verify-ten-repository-standard.py --format json` 按真实债务 exit 1：`9 repositories / 109 violations / 1 unverified`；这是既有 owner 改造队列，不是 W0B-6 通过门，也未放宽规则。
- 真实 Capability↔BFF smoke exit 0：`status=PASS`、`cases=8`，release 精确为 BFF `2ed7925…` / Capability `7f89a267…`；PostgreSQL、Redis、process group 与临时日志清理均由 runner 报告完成。
- 当前状态为“待审查”：Root 主控仍需 fresh cross-repository review、真实暂存四个精确路径后以普通 index 重跑门禁、提交并推送；本条不构成验收或冻结 SHA。

## 2026-09-21 — W0B-6 独立审查与 Root 集成验收

- Fresh cross-repository reviewer 对 Root `274dee1b…` 加四文件 prospective diff 完成独立复审：SPEC `✅`、QUALITY `✅`，Critical/Important/Minor 均为 `0/0/0`。审查独立核验全部 95 个 inventory commit-blob digest、45 个 BFF tuple、35 个唯一 BFF path、25 个 active request-edge BFF evidence，非目标 edge 语义漂移为 0。
- Root 精确暂存 `apps/kokoro-bff`、`verification/contracts/consumer-inventory.json`、`docs/task.md`、`docs/progress.md`，普通 index 下复跑 topology exit 0（9 runtime）、`w0b-capability` checkpoint exit 0、全量 governance tests `432 passed in 29.12s`、`git diff --cached --check` exit 0。
- Raw compatibility 保持诚实红门：预期 exit 1，精确 14 条 `declared broken` + 1 条 `illegal edge`，无 schema/gitlink/digest/evidence/version drift；状态精确为 2 active / 14 broken / 1 illegal。
- Root 再次执行真实 smoke：exit 0，`status=PASS,cases=8`，release 精确为 BFF `2ed7925…` / Capability `7f89a267…`。独立残留探针确认 PostgreSQL database=`0`、Redis key=`0`、owner process=`0`、临时目录=`0`。
- `verify-ten-repository-standard.py --format json` 仍按真实债务 exit 1：`9 repositories / 109 violations / 1 unverified`；相较上一基线少 1 条仅因 BFF Root gitlink已提升，不影响后续 owner debt队列。
- BFF 与 Capability 的 local/origin/live remote均只保留 `main`，child工作树 clean；本切片满足 W0B-6 激活条件。下一步在本集成 commit推送并确认 Root clean后，进入 W0B-7 Scheduler owner只读 release验证。

## 2026-09-21 — W0B-6 冻结完成，W0B-7 已派工

- Root 集成提交 `2ef5aa689ecaaf137168dcd68a9dd4ae8185c6c4`（`fix(integration): activate BFF Capability projection edge`）已推送；`main == origin/main`、Root工作树 clean。提交精确包含 BFF gitlink、consumer inventory与两份控制账。
- 提交后 Root 再次复验：topology exit 0、`w0b-capability` checkpoint exit 0、全量 governance tests `432 passed in 28.94s`、真实 smoke `PASS / 8 cases`；独立残留探针仍为 PostgreSQL `0`、Redis `0`、process `0`、temp dir `0`。
- W0B-7 只读 Agent `w0b7_scheduler_owner_auditor` 绑定 Scheduler `17c2de3e68ed75dbf3fa495643f6ad280e3c7112`，核对 contract/docs/schema/runtime语义与完整 Go门禁。审计不改文件、不操作 Git index、不写共享 PostgreSQL/Redis；若发现任何 drift，先报告并拆出 owner repair任务，不直接进入 BFF Scheduler设计。

## 2026-09-21 — W0B-7 发现 owner contract drift，W0B-7R 已派工

- 只读审计确认 Scheduler Git/provenance正确：HEAD、Root gitlink、`origin/main`与live remote均为 `17c2de3e68ed75dbf3fa495643f6ad280e3c7112`，local/remote只保留`main`；OpenAPI commit-blob SHA-256为`49be4429f9b1f4e86582c95aff770f6835629d3ea4ad80408bf65d0c64e598c3`，version `1.0.0`。
- Go `1.26.8`下，contract-check、gofmt、vet、test、race、build与diff-check全部exit 0；独立统计`120 pass / 9 skip / 0 fail`。9个skip来自未配置的7个PostgreSQL integration、1个source-process smoke与1个Redis integration，本次只读审计未访问共享基础设施。
- W0B-7保持未验收：runtime/docs已有`409 schedule_already_exists`与`404 schedule_not_found`，但canonical OpenAPI只把`error.code`声明为无约束string，breaking policy与contract/handler tests也未保护两项稳定机器码；删除或改名时现有contract-check仍会误绿。另缺RFC3339Nano小数秒与复杂opaque idempotency key逐字传递证据。
- 其余owner语义已核对一致：`/schedules/{name}`、tenant/schedule headers、408/425/429/5xx retry、四类PostgreSQL事实、无外键、transaction/outbox/claim expiry/recovery与Redis仅协调均无drift。
- W0B-7R由单一Scheduler writer以TDD修复，限定7个contract/test文件，不改runtime、SQL schema、路径、header、owner或contract major；owner commit推送和fresh contract复审完成前不得启动W0B-8。


## 2026-09-21 — W0B-7R 修复审查第 1 轮

- 原7文件交付的机器错误码、manifest、Nano样本和handler映射通过审查；独立 reviewer 以真实 HTTP 证明合法 U+00A0 边界 key 被 handler/application 的两次 `TrimSpace` 改写，可能使不同 key 共用 durable receipt。SPEC/QUALITY 各有1项 Important，W0B-7R继续进行中。
- Root 对旧7文件交付已做额外真实验证：独占临时数据库 + Redis DB 7 下 `go test -race -count=1 -json ./...` 为 `134 pass / 0 skip / 0 fail`（包含7 PostgreSQL、1 Redis与1真实进程重启smoke）；schema fresh install得到4表，二次安装正确拒绝，contract/vet/build/module verify/gofmt通过。该结果仅证明旧覆盖集，不消除审查发现的新回归缺口。
- 首次空库验证受本机role的 `search_path=kokoro, pg_catalog` 影响而正确拒绝系统目录；第二次在本次独占连接URL显式指定 `search_path=public` 后通过。未更改全局role设置；两个本次临时数据库均已删除，Redis测试key无残留。
- 范围已限定扩展为10文件：原7文件加 `internal/transport/http/handler.go`、`internal/application/commands.go`、`test/integration/postgres_test.go`。目标为原始HTTP field value与持久化幂等身份一致，不改其他身份处理、schema或依赖。Writer续任，先RED证明两层缺陷，再修复与独立复审；禁止以已有绿色测试放行。


## 2026-09-21 — W0B-7R 验收，W0B-7I owner release 集成

- Fix Round 1 以真实 HTTP 与独占 PostgreSQL 测试分别复现两个 trim 缺陷，再仅删除 handler/application 两处 `IdempotencyKey` 改写。两种 key 分别保存 receipt，同 key replay 与异 digest conflict 均保持。原 reviewer 复审结论 ADDRESSED，最终 SPEC/QUALITY 均 `0/0/0`。
- Scheduler 已精确提交并推送 `92bf9e7e6724c591bab4b7fa27f08d694b59a67e`（`fix(scheduler): protect stable control error and idempotency contracts`），10 个批准文件，工作树 clean，live remote 仅 main。OpenAPI `1.0.0` digest=`6ec2f6d5d71efa60b92bba1eb2dd0c81b7439734e2bc4450caa221e952e24183`，policy digest=`57b9c2739bcee031f4750fc01dce7607f8fceff5ceea9fc86c938370a0d75d34`；manifest 两项匹配。
- Root 在冻结 diff 与提交后的上述 SHA 各执行独占 PostgreSQL + Redis DB 7 的 `go test -race -count=1 -json ./...`：均 `135 pass / 0 fail / 0 skip`；包含8项 PostgreSQL integration、1项 Redis integration、1项真实 source-process restart smoke。提交后 contract-check、vet、build 均 exit 0；修改前的 fresh install/4表/非空拒绝门通过，schema 未变。
- Root 建立的修复测试库与提交后测试库已逐个精确删除；未改变共享role、重启数据库或清空Redis。Worker 自报的1项Redis skip已由Root真实门禁补齐，不再作为此 owner release 的缺失证据。
- W0B-7I 只集成已推送 owner：Root 单一 writer 更新 Scheduler gitlink、全部8个 inventory tuple与commit-blob digest、固定owner测试pin、CURRENT、当前计划与控制账；不激活任何新edge。BFF Scheduler设计仍等待Root集成门通过。

## 2026-09-21 — W0B-7I 写入完成，待独立审查

- 唯一写入 Agent `w0b7i_scheduler_integration_writer` 基于 Root `73036f75f035570cf83f0ab5ea4a9d16a0c6c9a9` 完成七文件 prospective 集成切片；Scheduler checkout 为已推送 `92bf9e7e6724c591bab4b7fa27f08d694b59a67e`。Worker 没有操作 Git index、提交或推送。
- TDD 聚焦红绿证据：先只更新 inventory 的 Scheduler pin，`test_scheduler_event_edges_pin_scheduler_owned_contract` 如预期 `1 failed`（旧 SHA/digest 冻结断言命中）；再仅更新该测试的 owner SHA/digest 后为 `1 passed`。随后整个 `scripts/tests/test_contract_compatibility.py` 为 `73 passed in 17.54s`。
- 使用 `git -C apps/kokoro-scheduler --no-replace-objects show --end-of-options <SHA>:<path>` 对全部 8 个 Scheduler owner/evidence tuple 重算 SHA-256：4 个 OpenAPI tuple 均为 `6ec2f6d5…24183`，2 个 `client.go` tuple 仍为 `e5fb3901‣69e`，2 个 `go.mod` tuple 仍为 `289cf9e8‣4a1`；8 个全部与 commit blob 一致。JSON 语义对比确认除这些 Scheduler pin/digest 外其余字段不变，状态仍为 `2 active / 14 broken / 1 illegal`。
- `git diff --check` 对精确七文件范围 exit 0；当前计划、固定 owner 测试与 inventory 已无旧 Scheduler SHA/digest。CURRENT 已切换到 W0B 当前态，并保留 Root 词法 parser 限制、非法 Web→IAM、真实全仓 runner/镜像/SLO 未验收等未完成事实。
- 真实 Root index 仍由主控保留且 Scheduler gitlink 尚未暂存，因此本 Agent 未构造 prospective index，也未运行最终 checkpoint/topology/全量 Root tests。这些门禁须由 Root 主控精确暂存七个文件后以普通 index 执行；本条不构成 Root 集成验收或冻结 SHA。

## 2026-09-21 — W0B-7 / W0B-7I Root 集成验收

- Root 主控接收七文件交付，独立审查 Agent `w0b7i_integration_reviewer`（`gpt-5.6-sol` / high）对冻结 diff 给出 SPEC/QUALITY PASS，Critical/Important/Minor = `0/0/0`；当前 index 与交付差异完全一致。
- 主控独立核对全部8个 Scheduler commit-blob tuple，digest 8/8匹配；除目标 pin 外 JSON 语义漂移为0。Scheduler release 为 `92bf9e7e6724c591bab4b7fa27f08d694b59a67e`；Root 基线 `73036f75f035570cf83f0ab5ea4a9d16a0c6c9a9`，集成 SHA 以本条所在 commit 为准。
- 精确暂存后真实 index 门禁：`python3 scripts/verify-repository-topology.py` PASS；`python3 scripts/verify-contract-checkpoint.py --expected verification/contracts/checkpoints/w0b-capability.json` PASS；`python3 -m pytest scripts/tests -q` 为 `432 passed in 41.00s`；`git diff --cached --check` exit0。
- Raw compatibility exit1，恰好14条 declared-broken + 1条 illegal，无新增 drift；ten-repository-standard exit1，`109 violations / 1 unverified`。Scheduler双向 edge尚未激活，W0B-8..11继续负责BFF设计、实现和真实进程验收。
- 本切片不改Schema、不访问或清理共享数据，不重复运行未改变的Capability smoke。全仓E2E、镜像与SLO仍未验收；Goal保持active。

## 2026-09-21 — W0B-7I 冻结证据与 W0B-8 派发

- Root集成commit `7c9e7abfbf8a4af36d7f039ec93f863dfc66b63f` 已推送origin/main；提交后 topology/checkpoint再次PASS，Root tests `432 passed in 34.56s`。`python3 scripts/verify-main-only.py` exit0：Root + 11个submodule全部clean，local/remote仅main。此证据绑定该commit，不代表后续写入中的工作树仍clean。
- W0B-8负责人 `w0b8_bff_scheduler_designer`（`gpt-6-astra` / high）只写当前计划Task8精确9个BFF文件：vendor、dependency manifest、generator config、技术/API/数据/CURRENT四文档、contract-governance/architecture两测试。BFF基线main `2ed792586e89c035155938078d9b07f33af95abd`，工作树干净且live远端一致。Root保留Git index/commit/push、控制账和最终放行。
- 本步仅设计与不可变artifact，不改runtime、public contract、package/lock或schema，不激活edge。Root已核验Node22.22.2、pnpm11.25.0、TS5.9.3；后续worker执行治理RED/GREEN、build与contract门，Root重新验收。
- 设计风险核对项：现有receipt的过期pending claim会替换fingerprint，不能直接当作同key不同digest恒409的证据；要求设计明确opaque identity、Nano精度、semantic digest、重启/response-unknown窗口及后续最小实现范围。任何所需范围扩展先回报主控，不悄悄改Schema或放宽门禁。

## 2026-09-21 — W0B-8 设计/artifact 验收，W0B-9 范围收敛

- BFF设计release `94a143cc545d74c2d3f518e3cafcc7f0eca0b450`（`docs(bff): freeze Scheduler owner contracts`）已推送main，live远端一致、子仓clean；精确9文件，无runtime/schema/package/lock/public OpenAPI变更。原始owner vendor与Scheduler `92bf9e7e…` blob字节一致；manifest/config/lock摘要已由Root独立核对。
- Writer `w0b8_bff_scheduler_designer`（gpt-6-astra/high）；独立审查 `w0b8_bff_scheduler_design_reviewer`（gpt-5.6-sol/high）。首轮发现验收层级误把Agent stub作为真实Agent证据，以及canonical JSON数字键序列化验收遗漏；fix1全部解决，最终SPEC/QUALITY `0/0/0`，后续Task9精确范围补充亦通过审查。
- Root在最终diff与提交后SHA分别复验：build exit0；contract-governance+architecture `34 pass / 0 fail / 0 skip`；contract:check `20 pass / 0 fail / 0 skip`及生成漂移/lint/semantic通过；schema:check `4 pass / 0 fail / 0 skip`；config prettier、diff-check通过。各测试集合有重叠，不相加为独立用例总数。
- 三文档门通过：`/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/docs/TECHNICAL_DESIGN.md`、`/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/docs/API_CONTRACT.md`、`/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/docs/DATA_MODEL.md`。设计无剩余阻断；实现、fresh install/真实PG与smoke仍待9/10，真实Agent admission/冲突/重启唯一事实属于W4。
- 当前计划Task9已加入专用receipt port/repository、现有pool装配、稳定Agent occurrence identity、独立identity算法/单测/PG测试和四文档状态同步。保留原Schema/通用public mutation实现，不新增owner/进程；generation、control与webhook边界仍沿既定方案。
- Root暂不提升BFF gitlink：按计划待W0B-9实现、W0B-10 smoke后由W0B-11统一提升并刷新全部fan-out。当前Root checkpoint仍对已冻结组合PASS（2 active/14 broken/1 illegal）；topology实际exit1，仅`kokoro-bff: checkout HEAD differs from recorded gitlink`。不把这个有记录的待集成状态写成全仓clean或拓扑通过。
- 本设计切片按Task8未运行完整runtime test、真实integration或db:apply-schema，也未重复Root全量tests；实际Root432项通过的最近冻结证据仍绑定`7c9e7abf…`。Goal保持active，下一步W0B-9。

## 2026-09-21 — W0B-9 实现派发

- 设计writer已停写；实现交接给 `w0b9_bff_scheduler_writer`（gpt-5.6-sol/high），BFF基线 `94a143cc545d74c2d3f518e3cafcc7f0eca0b450`，精确范围以当前计划Task9为准。Root继续独占Git index/commit/push与最终验证。
- Root复用现有PG/Redis，只新建本任务独占空库 `kokoro_bff_test_w0b9_742c50e086d4a950`；显式public search_path，未改共享role，Redis复用DB8且禁止flush。该库由Root在worker停写及独立验证后精确清理。
- Worker先RED后实现identity/generation/control/receipt/receiver，执行完整BFF门；Root随后独立审查及用另一独占库复验。当前仍在实施，不构成runtime或Scheduler双向edge验收。

### W0B-9 并行 Root 预审：后续 smoke release pin

- Root只读核对发现既有 `run_capability_bff_smoke.py` 对BFF精确锁定 `2ed7925…` 并在HEAD不同立即停止；这是有效保护，不应在consumer升级后绕过。W0B-11提升BFF时需同步推进该runner的固定输入并保留不匹配拒绝；W0B-15再次提升BFF时同步两条runner的输入。新增Scheduler runner仍由W0B-10负责，当前未派工/未写入。
- 该维护项属于Root组合pin，不改变consumer契约、Schema或edge状态；Root将把精确文件集与回归验证写入相应任务卡，避免到最后执行双smoke才发现旧pin阻挡。

## 2026-09-21 — W0B-9 待审查 / W0B-9V 基线 fixture 修复

- W0B-9 writer已停写：44文件交付，聚焦unit50/50、聚焦PG4/4、全量unit185/185；全量integration30/32，保留两条真实失败，不宣称全门通过。
- Root将未修改的BFF基线94a143c导出到独立临时源码、独立新库 `kokoro_bff_test_w0b9_base_a2c2d1c006e7`，相同两份AG-UI suite实际20 pass/2 fail/0 skip，确认不是靠Task9变更才产生的失败。
- 根因：AG-UI HTTP fixture在旧Run终态后直接追加Run2 source，没有先调用现有consumer admission注册expectedRun；projection fixture调用deleteConversation缺少第4个requestId。Root只在临时基线候选中修复，22/22连续三轮通过；进一步把admission放到发布Run2 events之前，避免新竞态。没有放宽原frame/replay/tenant/delete断言，也未改runtime。
- W0B-9V仅允许 `test/agui-http.integration.mjs`、`test/agui-projection.integration.mjs`，writer `w0b9v_agui_fixture_writer`（gpt-5.6-luna/medium）负责将已定位修正应用到实际子仓；Root保留index/commit/push并把此小切片独立提交。Task9原writer仍停写，避免同仓双writer。

## 2026-09-21 — W0B-9 独立验证与首轮审查退回

- Root使用另一独占PG库 `kokoro_bff_test_w0b9_root_332e93eff4b496` 复验实际44文件与两项fixture修复：format/lint/typecheck/contract/build/schema均exit0；unit185/185、integration32/32、contract20/20、schema4/4，均0skip。fresh install通过，非空重复apply按设计exit1。集合有重叠，不汇总为独立测试数量。
- 独立审查 `w0b9_scheduler_implementation_reviewer`（gpt-6-astra/high）发现6项P2、1项P3：特殊JSON键被generated parser删除、锁等待消耗lease、Agent预算超过lease、响应hard cap读完才检查、非有限数字变500、恢复验收缺失、0000–0099年误判。Root源码核对并接纳；绿色测试不替代缺失场景与正确性。
- Root真实PG锁等待探针：等待62007ms后claim返回成功但lease剩余-2003.661ms，确认生产逻辑缺陷；只使用Root独占库，自有探针行已删除。修复必须使用锁后实际数据库时间，并覆盖预算、CAS和恢复，不靠放宽测试。
- W0B-9退回“进行中”，原writer续任集中修复，Root保持审查/控制账/最终验证；9V已独立审查无发现。Scheduler edge仍未激活，Goal继续active。

## 2026-09-21 — W0B-9V 独立验收与提交

- 仅两个AG-UI fixture修复已独立提交并推送BFF main：`fd75dc92dbf0401a6d21cbdab13fe723dd6ccfe0`，live远端SHA一致。6行新增/1行删除，不修改生产逻辑、原断言或跳过测试。
- writer `w0b9v_agui_fixture_writer`（gpt-5.6-luna/medium）交付后停写；独立审查 `w0b9_scheduler_implementation_reviewer` 无发现。Root在独立94a143c基线源码+修复上提交前22/22、提交后逐文件校对commit blob后22/22，均0fail/0skip。
- 使用显式两路径提交；Root比较提交前后Task9暂存diff字节完全一致，44文件未混入9V。Task9新基线是fd75dc9，原44文件待修复/审查，子仓工作树仍不clean。
- Fix Round1派发原实现负责人；七项缺陷及验收要求在当前计划固化。Root gitlink仍留待W0B-11提升，不借fixture提交提前宣称Scheduler集成完成。

- 本轮控制账Root复验：checkpoint `w0b-capability` PASS；Root tests `432 passed in 34.83s`；topology exit1且仅BFF checkout/gitlink待W0B-11集成不一致；diff检查通过。既有109 violations/1 unverified是前次静态审计证据，本次未重测，不写成已清零。
- 9V独占基线数据库和临时源码已精确删除，RED/GREEN日志保留；Task9 writer库和Root独立复验库仍保留用于本轮修复。未清理共享数据库/Redis。

## 2026-09-22 — W0B-9 Fix Round 1 交付与复验

- 原writer已停写，基线BFF `fd75dc92dbf0401a6d21cbdab13fe723dd6ccfe0`；修复原44路径内14文件，生成物/Schema/config/9V fixture均无额外变动。Root再次精确暂存44文件并冻结diff，未提交。
- Root在自有独占PG库独立复跑：format/lint/typecheck/build均exit0；contract20/20、unit193/193、integration34/34、schema4/4，均0fail/0skip。新增PG+BFF HTTP+Agent stub覆盖finalize失败、receiver重建、原snapshot恢复与stale prepare零I/O，不冒称真实Agent事实。
- 只读astra审查员已续派复审七项及修复回归，当前状态“待审查”。Root另检查DB返回/COMMIT延迟是否被lease预算扣除；在结论确认前不放行，Scheduler edge维持原状态。

- Fix1复审仅余1项P2：预算采样后至repository返回的传输/COMMIT延迟被遗漏。Root真实PG注入6500ms确认延迟，返回预算59996ms、真实剩余53489.512ms，扣5000ms reserve仍超出。astra独立内存探针亦证实过期后仍发Agent请求。原writer续派Fix2，只改本地预算观测与两条接纳路径测试；其余原发现已关闭。

## 2026-09-22 — W0B-9 最终验收与冻结

- BFF实现release `5ea4440941ed65c424fffb0ae834e67b2ae93e74`（`fix(bff): align Scheduler control and event contracts`）已推送main，live远端一致、子仓clean。Root精确提交已审查44文件；9V独立commit `fd75dc9…` 未混入本切片。
- writer `w0b9_bff_scheduler_writer`（gpt-5.6-sol/high），审查 `w0b9_scheduler_implementation_reviewer`（gpt-6-astra/high）。两轮修复后最终SPEC/QUALITY PASS、剩余发现0；预算query前单调观测随claim/prepare传递，覆盖DB/COMMIT/route返回耗时。审查员独立执行两条延迟负例2/2通过。
- Root提交前与提交后各独立执行完整门禁：format/lint/typecheck/build均exit0；contract20/20、unit195/195、integration35/35、schema4/4，全部0fail/0skip。提交后重新创建Root独占空库，fresh install通过，非空重复apply按设计exit1。Schema、runtime config、package lock无本切片变化。
- Root对同一6500ms COMMIT确认延迟故障重验：最终Agent预算48489ms、DB剩余53488.601ms，约5000ms settlement reserve完整保留；只操作Root独占库，自有探针行已清理。
- 三文档实现状态已随release冻结：`/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/docs/TECHNICAL_DESIGN.md`、`/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/docs/API_CONTRACT.md`、`/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-bff/docs/DATA_MODEL.md`。owner artifact仍固定Scheduler `92bf9e7e…`，BFF generated control/webhook边界与immutable receipt/snapshot真实PG恢复已验收。
- Task9两个PG库现均已精确删除，连同之前清理的9V baseline库，共三个自有库无遗留；fixture env已移除，worker/reviewer均停写。未启停或清空共享PG/Redis。
- 下一项W0B-10：真实Scheduler+BFF进程smoke，Agent只用明确标记的receipt stub；W0B-11再提升Root gitlink、刷新全fan-out与Capability smoke pin并激活双向edge。当前Root仍固定旧BFF组合，`2 active / 14 broken / 1 illegal`保持不变；真实Agent admission归W4，全局Goal保持active，不宣称整体闭环。

- 本轮Root收尾实测：checkpoint `w0b-capability` PASS；Root tests `432 passed in 24.18s`；topology exit1仅BFF checkout与冻结gitlink不一致。静态规范审计现为 **112 violations / 1 unverified**，不是之前109：新增3条全部来自Task8引入的Scheduler原始vendor中 `/internal/scheduler/v1/schedules/{name}` 及pause/resume路径，被当前通用v1规则再次计入BFF。与前次109逐项对比无其他新增/消失；不删除vendor、不放宽规则或隐去红门，后续Root治理收敛owner/vendor归属与路径规则。

## 2026-09-22 — W0B-10 真实进程 smoke 派发

- 上一Goal回合属于progress：W0B-9完成子仓实现、审查、真实验证与提交；本回合重新核对Root `07f2420c…`、BFF `5ea4440…`、Scheduler `92bf9e7e…`，两子仓clean且live远端一致。Root唯一已有差异是按计划尚未提升的BFF gitlink。
- 负责人 `w0b10_scheduler_bff_smoke_writer`（gpt-5.6-sol/high）只写runner、runner自身pytest、scripts/INDEX三个文件。Root保留控制账、Git操作和独立验收；不得改owner、contract、Schema、inventory或gitlink。
- 创建前放置表已加入当前计划Task10。Root发现Scheduler原生Redis lease使用tenant/occurrence摘要固定前缀而非可配置namespace；方案使用nonce tenant与独占DB证明归属、登记精确key并在进程停止后清理，禁止全前缀清除，也不通过禁用Redis缩小验收。
- 本阶段验证真实Scheduler控制/派发→BFF receipt恢复；Agent只用明确stub。尚未运行新runner，不提前激活edge，Goal保持active。

- W0B-10 worker已完成pytest RED（runner缺失导致预期collection ImportError、exit2）并写初稿；1128行触发Python职责复核。Root批准同目录增加唯一 `scripts/e2e/scheduler_bff_smoke_runtime.py`，拆出自有资源/进程生命周期与HTTP测试设施，runner保留11case/CLI/证据编排；测试文件不扩散。不靠压缩代码过行数门，也不新建common框架。Task10精确范围由3文件调整为4文件，Ruff/py_compile同步覆盖runtime。

## 2026-09-22 — W0B-10 partial handoff / W0B-7R2 派发

- Task10 writer已明确停写，四文件成果保留未提交；报告确认其进程、私有数据库及owned Redis keys已清理。首轮focused20/20及随后定向RED/GREEN只属于阶段证据，最终完整门禁仍待执行。曾输出11case PASS的诊断含私有409 receipt注入，因此不作为owner/Task10验收。
- Root在独立新库、真实Scheduler HTTP上观察首次create 200、同tenant/name新key create 500 `scheduler_command_failed`。该探针误把首次成功期待为201，故命令exit1；保存的JSON由Root另行断言状态序列200/500，不把失败命令冒称通过。探针自有进程/数据库/临时文件已清理。只读owner auditor确认23505导致事务aborted，后续receipt写入25P02；此前135项全绿缺少此场景。
- W0B-7R2归Scheduler现有PostgreSQL command adapter，三文档与canonical schema已明确可replay冲突语义；仅允许adapter及PG integration测试两个现有文件。实现Agent `w0b7r2_scheduler_conflict_writer`（gpt-5.6-sol/high），Root负责Git、独立审查和真实HTTP复验。没有schema/contract变更；Task10先等待本切片，整体Goal仍active。

- W0B-7R2派工控制账Root复验：已接收Root测试（显式排除尚未交付Task10测试）432 passed in 25.45s；`w0b-capability` checkpoint PASS；diff检查通过。Root独立查询确认Task10数据库及其应用进程均无遗留。未运行Task10最终门禁，不计入本次432项。

- W0B-7R2 writer已停写交付：仅adapter与PG测试两文件，真实RED复现25P02，full/race各139 pass/0 fail/0 skip（含子测试）；重放使用新RequestID仍保留原receipt，并发两键收敛。Root已冻结文件digest、确认Schema/contract/module未变及BFF原vendor逐字一致，独立审查与另库全门/真实HTTP复验正在进行，尚未提交owner。

## 2026-09-22 — W0B-7R2 owner 验收 / W0B-10 恢复

- Scheduler新release `975dee59616a1e0eda609aa69283401344900d83` 已精确提交并推送main，live远端一致、子仓clean、远端仅main。两文件137新增/8删除；无Schema、OpenAPI、manifest或依赖变化。
- 独立reviewer `w0b7r2_scheduler_conflict_reviewer`（gpt-5.6-sol/high）对冻结diff给出SPEC/QUALITY PASS，Critical/Important/Minor=0/0/0。Root提交前独立库普通/race各139 pass/0 fail/0 skip；提交后race再次139/0/0，contract-check、gofmt、vet、build与提交前mod verify通过。
- Root真实HTTP新库/新进程复验提交前后均得到200→409→重启后409，第二receipt保留原request ID及完整body；数据库精确1个Schedule/2个receipt，Redis DB7启用。每次探针自动清理自有库/进程/临时文件；writer与Root两个额外测试库现也已精确删除、fixture env移除。
- BFF原vendor、Scheduler92bf9e7发布artifact与新runtime的canonical OpenAPI字节完全一致，digest仍为6ec2f6d5…183。保留真实历史artifact provenance，不伪造重新生成记录；Root Task11将pin新runtime并重算所有Scheduler证据，更新pin回归。
- W0B-10原writer恢复，仅在原四文件内更新Scheduler runtime SHA、移除私有409 receipt注入及known-risk分支，以真实同名新key创建自然产生409，完成11case与完整生命周期门。当前尚未验收Task10或激活Scheduler双向edge；Root gitlink与inventory留Task11一次集成，Goal保持active。

- Root接受owner后的组合门：checkpoint仍为w0b-capability PASS；已接收Root tests（显式排除未交付Task10测试）432 passed in 33.11s。topology exit1精确为BFF与Scheduler两个checkout领先旧gitlink，留Task11集成。只读预检新组合：BFF45、Scheduler8个现有tuple路径在各新release均存在，10处BFF摘要需要更新、无缺失路径。

- Task10恢复后的writer报告真实自然409与私库/receipt断言11case已通过，尚待Root独立审查。Ruff后runner878/runtime789行，Root按Python尺寸/职责门批准同目录唯一新增 `scheduler_bff_smoke_cases.py`（现精确5文件）：cases承载行为/SQL观察，runner保留CLI/总生命周期，runtime保留资源/进程/HTTP。不塞满runtime、不压缩代码或登记永久行数豁免；修改后重新冻结审查和真实CLI。

## 2026-09-22 — W0B-10 冻结待审查

- writer最终停写，精确五文件：runner302、cases641、runtime789行及pytest/INDEX；自然owner409→BFF PUT、三项control的Scheduler schedule/receipt断言、负例Agent计数均已补齐；没有诊断伪造receipt/预期500/known-risk成功分支。
- Root冻结五文件SHA-256后独立执行focused24/24、Ruff format/check、三源码py_compile、全量Root456/456、真实Scheduler/BFF/PG/Redis十一case CLI，均通过。runtime SHA固定Scheduler975dee596…与BFF5ea444094…；输出明确Agent只为receipt stub，未验证真实Agent。自有fixture清理通过。
- fresh reviewer `w0b10_scheduler_bff_smoke_reviewer`（gpt-6-astra/high）正在独立检查失败路径、资源所有权、线程生命周期和replay证明强度；Root不以绿色正常路径替代审查，任务保持待审查、未提交，双向edge未激活。

## 2026-09-22 — W0B-10 首轮审查退回

- 独立astra reviewer以纯内存与自有loopback探针复现4 Important：CREATE/SET已生效但确认丢失后丢弃ownership、partial-body HTTP handler在context退出后仍alive、同task新run_id二次Agent调用被case误判PASS、go1.26.80/devel被子串版本检查放行。另有2个超100行函数（191/211）为Minor。reviewer所有探针连接/线程/临时目录已清理。
- Root接受上述缺口并退回原writer Fix Round1，精确五文件不扩张；每项先补RED后修复，保持实际11case/严格cleanup/owner边界。456全绿和真实11case正常路径不替代故障验收。
- 同源CREATE资源登记缺陷也存在已验收Capability runner（只读定位），新增W0B-5R两文件修复切片，排在Task10完成后、Task11激活前。它同时前移原本Task11负责的Capability smoke BFF pin以便真实8case验证；不改业务owner/contract或提前激活edge。Goal继续active，本回合已有Scheduler owner修复进展，不标记全局blocked。

- W0B-5R只读预检补充：Root对Capability现有readiness fixture发出自有loopback partial-header，context返回后实测1个owned handler仍alive；关闭自有socket并join后0残留。该同源HTTP生命周期缺陷一并列入5R原两文件范围；没有修改Capability runner或共享基础设施。

## 2026-09-22 — W0B-10 Fix1交付与网络边界复核

- writer已停写：RED17 failed/26 passed，报告最终focused45/45、Ruff/compile、十一case真实CLI通过；源码函数均≤100行，文件均<800。Root冻结Fix1 delta后续派原reviewer定向复审，尚未验收。
- Root发现writer另加未先申请的RFC1918 callback listener，以适应本机DNS变化；当前Root独立查询主机名仅解析192.168.1.4及link-local IPv6，原loopback条件已不成立。Scheduler出站/32 allowlist不等于listener入站peer限制；现实现缺少peer限制，Root未运行该新非loopbackCLI。已向用户询问是否允许仅本机peer的临时内网绑定，或保持loopback；在明确新边界前保留原隔离约束，不把worker扩大网络面的PASS作为接受证据。
- Root仍继续不触及非loopback面的focused/全pytest/静态门，以及reviewer对I1–I4/M1的内存/loopback故障复验；Goal保持active，非停止全部推进。

- Fix1 Root非扩面验证：focused45/45、全pytest477/477、Ruff/compile通过。独立复审关闭I1/I3/I4/M1，仅剩2 Important：慢速上游body绕过idle timeout使server_close无界join；RFC1918自动绑定且无入站peer限制。reviewer的6秒慢速body/peer模拟探针已全部清理。
- Root派原writer Fix2：为全部proxy upstream I/O设置总期限/取消并有界join；撤回未经批准的RFC1918自动扩面，保留loopback/fail-closed并提前检查DNS。用户尚未答复网络边界问题，Root按既有批准约束推进，不等待回复才修其余质量缺口，不修改共享hosts/DNS。真实CLI若仍因本机DNS失败，应如实交付环境限制，Task10不冒称已验收。

## 2026-09-22 — W0B-10 Fix2复验 / Fix3定向派发

- Root在冻结Fix2源码上实测focused47/47、全pytest479/479（42.85s）、Ruff format/check、compile与diff通过。真实CLI exit1，前置DNS检查发现主机名仅解析192.168.1.4；未创建run资源，自有Scheduler/BFF smoke数据库为零。保留原loopback边界，用户网络选项尚待答复。
- 独立reviewer确认F2关闭、慢速body约3.1s自行Timeout，但未完成headers每100ms滴入1byte时4.3s仍未结束，保留F1一个Important（0/1/0）。手动取消后所有探针资源已回收。Root接受该问题，原writer进入Fix3，不以479项全绿替代失败路径证据。
- 当前runtime774/test798行。Root先完成放置门，批准同目录HTTP fixture模块及对应HTTP测试文件，精确范围由5变7：按HTTP职责搬迁，原定义和旧import删除；不创建共享框架或兼容alias。实现覆盖request/status/headers/body的主动总期限取消，处理HTTP/1.0 socket转移并回收timer；其他owner/contract/network边界不变。Task10尚未提交或验收，Goal active。
