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
