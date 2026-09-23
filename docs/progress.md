# Kokoro 后端闭环进度证据账

本文件只追加已执行事实，任务状态以 [`task.md`](task.md) 为准，目标设计以 [`superpowers/specs/2026-09-20-kokoro-backend-closure-design.md`](superpowers/specs/2026-09-20-kokoro-backend-closure-design.md) 为准。没有命令输出、commit 或冻结 SHA 的事项不得写成完成。

阅读入口：当前执行记录见本文末尾的 **W1B 启动**；能力边界与下一步见 [`task.md`](task.md) 第1节及 Wave1B 执行卡。此前日期的通过数只证明对应提交，不代表最新工作树或整体系统已完成。

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

- Root只读完成5R实施前盘点：现有Capability runner884行/test408行，原focused26/26通过；Capability7f89a267 clean。已批准一个同目录runtime与INDEX更新（精确4文件），承接进程/资源/readiness生命周期，保留原8case及已验收行为。5R在Task10代码审查通过且writer停写后可串行推进，不依赖Scheduler回调DNS；Task11仍要求两项真实CLI全绿。这是独立修复的调度调整，不放宽Task10或edge验收门。尚未派工或修改5R源码。

## 2026-09-22 — W0B-10代码审查放行，运行验收保留

- 原writer Fix3已停写，Root冻结七文件SHA-256；原独立astra reviewer SPEC/QUALITY PASS，0/0/0。真实loopback slow status/header/HTTP1.0 body分别3.00/3.01/3.00s自行Timeout，HTTP1.0取消立即退出；late registration、正常/异常出口均无timer/socket/线程残留。HTTP职责移动无旧定义或兼容re-export。
- Root在控制基线9e0fd859及相同七文件上独立复跑：双focused48/48（8.27s）、全pytest480/480（38.45s）、6文件Ruff format/check、4源码compile、diff-check全部通过；AST文件/函数门通过，冻结hash7/7匹配；w0b-capability checkpoint PASS。
- Root真实精确CLI仍exit1：本机hostname仅192.168.1.4，loopback前置检查先于所有资源创建。PG自有smoke库/Redis harness为空；未扩大listener，不修改DNS/hosts，不激活双向edge。此切片保存已审查实现，但W0B-10状态只到“待集成验证”，不是已验收；Agent仍明确stub，Goal保持active。
- 下一切片按已批准调度为独立W0B-5R，由新的Root smoke负责人单独写入四文件；Task10代码保持冻结，Task11仍等待两个真实CLI通过。Root继续拥有所有Git与最终质量放行。

- W0B-10代码提交`cfaacbb50ec00180dbc34a44ed96096d1c53332c`已推送main；七个源码/测试/INDEX文件与独立审查冻结字节一致，Root仅剩两处计划中的子仓gitlink差异。未将代码提交冒作真实运行验收。
- 派发W0B-5R：`w0b5r_capability_smoke_writer`（gpt-5.6-sol/high）独占Capability runner/runtime/pytest及scripts/INDEX四文件；Root保留控制账与Git。基线为上述Root提交，Task10所有源码冻结；新的同源故障修复先RED，真实8case、资源回收、独立审查和主控复跑之后提交。

- 提交后Root治理诊断：topology exit1精确为BFF/Scheduler两个checkout领先冻结gitlink；ten-repository-standard exit1仍为112 violations/1 unverified，无门禁放宽。Task10提交未改变owner/inventory，w0b-capability仍为2 active/14 broken/1 illegal；后续Task11才提升组合。

- Root另行执行live只读分支审计（Task5R写入期间快照）：主仓+11个submodule共12仓，本地分支与远端heads均只有main，12/12 HEAD与live origin/main一致；11子仓全部clean。Root当前差异仅本轮工具/控制变更及两处尚待Task11提升的gitlink，故不宣称整个工作树已clean。审计不fetch、不删除分支、不操作worker索引。

## 2026-09-22 — W0B-5R主控复验与新隔离前置

- Root冻结四文件后独立focused34/34、全Root488/488（41.30s）、Ruff/compile3/3/diff通过；真实Capability/BFF CLI exit0、8case，随后自有PG/Redis/进程/临时资源均已回收。BFF与Capability子仓仍clean。
- Root另查到Capability `src/main.ts:190`硬编码listen 0.0.0.0：runner访问127不等于owner只监听127。此前“owner进程loopback”描述不准确；本次功能8case通过也不满足该隔离验收。自有进程已结束，暂停继续执行该真实CLI；新增W0B-2B owner监听配置切片，先做三文档/代码/测试只读审计，再由Root决定最小配置变更。
- 5R独立sol reviewer另复现一个Important：prefix存在非ownership key但无marker时仍可SET claim，cleanup会删除预存key。Root接受并准备原writer Fix1；这是四文件范围内问题，不靠随机ID碰撞概率豁免。Root定位Task10 harness同源路径，登记独立W0B-10R，只修该残留，不重复已验收deadline工作。
- Task5R未验收/未提交；Task10只完成代码审查保存，仍待DNS条件及10R补验；Task11新增两项前置，继续不激活edge。Goal active，本轮已有owner7R2、Task10代码提交及故障验证进展，不宣称整体完成。

- 5R最终fresh review为SPEC/QUALITY fail0/1/1：除markerless预存prefix被删除外，partial-header清理虽无线程残留，仍打印预期BrokenPipe teardown traceback。Root退回原writer Fix1：前置exact-prefix inventory fail-closed、仅收敛owned shutdown的预期socket错误且保留异常错误可见；原四文件，不动Task10/child。真实CLI因Task2B前置暂停，先完成故障代码审查；Root派sol只读owner监听审计并行提供三文档/最小配置建议，尚未授权child写入。

## 2026-09-22 — W0B-5R Fix1代码放行

- 原writer完成markerless prefix/未知SCAN前置拒绝与只抑制owned teardown预期socket错误；原独立reviewer定向SPEC/QUALITY PASS，0/0/0，内存探针证明预存key无SET/UNLINK，12-client loopback stderr=0/handler=0，非预期RuntimeError仍可见。
- Root对冻结4文件独立复跑focused37/37（1.59s）、全Root491/491（43.70s）、3文件Ruff format/check及diff通过，前轮compile后未改变Python语法结构；提交前再编译冻结源码。未再运行真实CLI或启动旧wildcard owner，PG/Redis未触碰。代码先保存，5R仍“待集成验证”，2B后更新owner pin/显式loopback并重跑真实8case才验收。
- 尺寸核对纠正：runner/runtime满足≤800/≤100；测试中既有midflight cleanup用例仍为105行，早先“全部函数≤100”不准确。Root登记临时例外：owner Root，保留该既有行为基线避免与故障修复混拆，截止2026-09-23或5R实际运行验收前（取先）；5R更新owner pin的同一次测试改动须提取fixture setup并关闭例外，不影响其现有断言。
- 2B只读owner审计已完成。Root选择源码默认127.0.0.1、Docker部署显式0.0.0.0，配置KOKORO_CAPABILITY_HOST/listenHost仅两个精确literal，空白/hostname等拒绝；实际OS绑定地址须验证，API/Schema不变。整体设计由Root固定，尚未授权child实现；先串行完成10R的Root小修复。

- 5R代码提交`1f628dd2b2b1393d42730fa989a72154bce5bdd3`已推送main，未标记runtime验收；Root现串行派fresh `w0b10r_scheduler_prefix_writer`（gpt-6-astra/high）做Task10原ownership后续定向修复，精确runtime/主pytest两文件，HTTP/deadline/owner均不动。按既有fix-loop升级判断，不重开已关闭deadline工作。Root保留控制/Git；2B仍只读资源审计/设计，尚无child writer。

## 2026-09-22 — W0B-10R通过 / W0B-2B文档门

- 10R fresh astra writer只改runtime三行及两个内存回归；原reviewerSPEC/QUALITY PASS 0/0/0，6个独立内存测试通过。Root对同一冻结两文件复跑50/50 focused（8.19s）、全Root493/493（45.02s）、Ruff/diff通过；提交前compile与hash复核。无共享资源操作，Task10原11case仍留DNS前置，不冒称运行闭环。
- Root完成并提交Capability三文档设计门：owner commit `e956c62a4212d7b691f3678310a46fdd172f3b5b`已推送main；设计明确当前硬编码wildcard尚未改、目标源码默认loopback/部署显式wildcard。文件为 `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-capability/docs/TECHNICAL_DESIGN.md`、`/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-capability/docs/API_CONTRACT.md`、`/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/apps/kokoro-capability/docs/DATA_MODEL.md`；DATA旧“当前基线”澄清为历史里程碑。
- Node24静态文档门实测：三文件Prettier write均unchanged/check通过；`pnpm exec tsx scripts/check-contract.ts`通过，combined digest仍536dca2989…；`REQUIRE_REAL_INTEGRATION=0 pnpm schema:check`通过（Prisma既有无FK索引提示保留，不是实时数据库证明）。contract/canonical schema共23个tracked blob SHA-256全部与7f89a267一致。三面无未决owner/API/SQL决定；真实fresh install、监听与完整owner门留实现阶段。
- 资源审计确认owner完整suite在显式独占PG URL、Redis URL及REQUIRE_REAL_INTEGRATION=1下目标0skip；Redis仅PING无flush。另发现release-image既有check→apply顺序在fresh DB错误，单列2BV沿同owner两文件独立commit，不能把旧workflow当fresh-install证据。

- Root串行派发2B实现负责人 `w0b2b_capability_listener_writer`（gpt-5.6-sol/high），基线为已推送三文档提交`e956c62a4212d7b691f3678310a46fdd172f3b5b`，child clean。精确15既有文件；Root保留Git和跨仓控制。先无socket RED，再仅loopback实测；明确独占随机PG库、Redis只PING、full suite目标0skip。2BV顺序修复和Root pin/105行fixture收尾分别后置，未一并授予修改权。

## 2026-09-22 — 按用户要求加速代码推进

- 收敛为同owner完整实现窗口，减少只为过程记账的提交与重复全盘评审；保留冻结版本上的真实功能/隔离验收。用户明确未上线按clean-slate，删除被替代旧路径/协议/alias/fallback，不维护兼容双轨。
- 原2BV两文件顺序修复并入正在执行的2B（仍原15文件），已通知writer，不另停一轮派工/提交；Root验收包含apply→persisted check实际证明。此前“另行提交2BV”安排由本决定替代。
- 并行准备下一BFF Storage代码清理的只读检查，不让Scheduler本机DNS限制阻止独立代码工作。Root先核对Task12/14既定契约/文件范围，之后同BFF窗口处理三文档和删除死链；最终同一次组合更新pins/fan-out，避免多次无收益升级。尚未放宽任何edge激活门或修改网络边界。

- 2B原15文件独立SPEC/QUALITY通过（0/0/0，15hash与23机器blob一致，定向36测试）；Root fresh apply/schema/format/lint/typecheck通过，但标准并行全门实测852 passed/1 failed/0 skipped：MCP real-P2034探针在预期rollback观察点前触发冲突。Root新库已精确回收；整体owner未放行。继续同owner窗口排查并修复两个receipt integration suite的资源隔离，保留真实并行与精确断言，不用重跑或串行化掩盖。

- BFF只读预检完成，基线`5ea4440941ed65c424fffb0ae834e67b2ae93e74` clean：真实死链、test-double假200与机器契约缺503均已定位。Root批准原13+7清理文件并扩`src/contracts/account.ts`共21文件；按未上线clean-slate删除不可达Library200及孤儿类型，不把未来设计伪装当前契约。三文档/机器门先于runtime，合成单次owner交付；W1/W2五项授权/scope/分页条件已写入任务验收栏，后续以最终BFF release绑定。预检报告Redis端口56380更正为实际共享6379/8；尚未派BFF写入。
- 本次Root控制文档验证：本地Markdown链接PASS，handbook/checkpoint测试14 passed；当前topology exit1，精确三项为BFF/Capability/Scheduler checkout领先旧gitlink，待最终组合接收。

## 2026-09-22 — Capability 监听与并行验收隔离闭环，接力 BFF

- Capability交付`9c88d0d934387b590bc74dae0179a587292e0253`：19文件；唯一typed listener配置、默认127.0.0.1/显式Docker 0.0.0.0、release先apply后check；两个Serializable探针suite转为各自成功创建的随机canonical DB，内部真实竞争和原精确断言保留。新增fixture纳入标准format gate；无API/schema/dependency/lockfile变更，23机器blob一致。
- 原listener审查及fixture增量最终均SPEC/QUALITY 0/0/0。Root独立fresh apply→persisted schema、format/lint/typecheck、标准并行`pnpm test` 75 files/853 passed/0 failed/0 skipped、contract/artifact/Prisma/build/production smoke全部PASS；compiled address断言IPv4/127.0.0.1。最后一行format清单补充仅复跑实际format门，原18文件hash保持；未重复不变全门。
- Root新库`w0b_cap2b_root_bcb19dd76cb4`关闭后0连接、精确DROP并确认不存在；receipt/recovery两suite fixture数据库余量0。前一次852/1失败记录保留，不改写历史。未运行Docker候选或Root最终双smoke，不把owner验收冒充组合验收。
- BFF下一窗口交给同仓预检负责人，Root批准22文件（在原21外补`contract/README.md`的未上线corrective-baseline说明，保持上线后breaking政策），先三文档/机器契约门，再删除运行链、mock200与孤儿类型；五个W1/W2前置已绑定任务栏，提交后再补最终BFF SHA。Root仍独占Git/组合文件，子仓单writer。

- Root已完成5R最后小切片：Capability runner锁定已发布9c88d0d并覆盖继承wildcard HOST；2个RED后GREEN，旧105行fixture提取后所有函数≤100、两个文件≤800。定向39/全Root495通过，Ruff通过，独立luna SPEC/QUALITY 0/0/0。BFF仍在写入，暂不跑最终8case或冻结其新pin。
- Root组合接收与edge激活分开记账：后续可把已验收子仓SHA/digest与真实broken原因一次更新，使组合可复现；Scheduler DNS条件尚不满足时保留2 active/14 broken/1 illegal，不冒称4/12/1，也不让这一环境条件阻断独立代码清理。

## 2026-09-22 — BFF Storage删除已发布，最终双smoke真实通过

- BFF `c5e9b3cc8eb134ff72e37f56ac1f95ebec4f42e7` 已审查/推送main，22文件精确范围。Root独立复验format/lint/typecheck/build、contract21、architecture25、unit199、schema4、fresh PG+Redis integration35，0失败/0跳过；独立SPEC/QUALITY 0/0/0。OpenAPI digest为`173354c68ea8e7c606df8213c0a7605d510c46bb2dcc298245daff3c944df946`；schema/依赖/vendor/generated不变。Redocly无2xx warning如实保留，未保留假success契约。Root新库`w0b_bff14_root_9d67d5bf327d`0连接后精确回收。
- W0B-13的五项前置正式绑定上述BFF同一commit：Storage default-deny caller×operation×scope、Capability scope mapping、Agent trusted Run/ExecutionIdentity mapping、BFF W1 IAM admission、Library per-kind/composite pagination。这里只完成交接，不冒称这些能力已实现。
- 最终Capability9c88d0d/BFFc5e9b3c真实smoke **8/8 PASS**，DB、Redis前缀、进程组、临时文件全部回收；最终Scheduler975dee59/BFFc5e9b3c严格原CLI **11/11 PASS**，同样全部本次资源回收。当前hostname解析包含127.0.0.1，未改hosts/resolver、未扩大listener或CIDR。早前DNS失败记录保留；本次通过结束该环境阻碍。
- 因最终双smoke已通过，执行原Task11两edge激活，不再停在前述partial-only方案；其余12 broken与唯一非法旁路保持不变。更新三gitlink、62个既有commit tuple、Scheduler generator/Node/Go及完整生成链证据、Storage明确503原因；BFF vendor来源仍7f89a267/92bf9e7，不伪造新生成。Root候选topology PASS，激活前495测试通过，激活后待冻结复验；静态审计仍112 violations/1 unverified。W0B-11/15/16待最终独立组合审查，不提前宣称全项目闭环。

- 最终激活候选复验：`verify-contract-checkpoint.py --expected .../w0b-exit.json` PASS（精确4 active /12 broken /1 illegal）；Root完整测试495 passed、Ruff与diff检查通过；topology PASS。两条新Scheduler edge的generator/Node/Go版本断言亦独立执行PASS。下一步是绑定这一冻结候选的独立SPEC/QUALITY组合审查与提交后main-only审计。


## 2026-09-22 — W0B 最终组合双审通过，进入提交后审计

- 独立 SPEC `w0b_final_spec_reviewer` 与 QUALITY `w0b_final_quality_reviewer`（均 gpt-5.6-sol/high）绑定 Root 基线 `818bb300483f4f7b483fb02bd7f66624320e7b7d` 的冻结 9 文件 + 3 gitlink，均 PASS、Critical/Important/Minor `0/0/0`。
- QUALITY 独立核验 144 引用实例 / 96 唯一 commit-blob tuple、16 条 owner contract digest 均一致，三子仓 live main 与 HEAD 相等；定向 154 tests、Ruff、topology 与 w0b-exit 通过。真实资源门由 Root 既有最终双 smoke 提供，不重复宣称 reviewer 运行了真实 smoke。
- Root 收尾更正 Task6 的历史前置：它依赖当时 Task5 Capability smoke，不倒置依赖后来 Task10R/Scheduler；Task11 的最终双 smoke 门保持不变。这是计划文字纠错，不改变实现、edge 状态或验收门。
- W0B-11/15/16 进入待集成验证；尚不预先证明 Root 已推送、全仓工作树 clean 或 main-only live audit。下一步按精确 12 路径提交集成、推送，再执行审计。


## 2026-09-22 — W0B 已验收：主仓集成与 12 仓 live 审计闭环

- Root 集成提交 `96d238bae1e23cbbfda66ea631e7e40c1176ef3b`（`fix(integration): close Scheduler BFF edges and remove Storage dead path`）已推送。精确 9 普通文件 + 3 gitlink，无任务外变更；Task6 文字纠错及 4 控制文档收尾已由原 SPEC reviewer 增量复审，仍 `0/0/0`，其余 5 文件 + 3 gitlink 字节未变。
- Root 提交前最后复验：`python3 -m pytest scripts/tests -q` → **495 passed / 0 failed / 0 skipped, 47.39s**；本次 4 Python 文件 `python3 -m ruff check`、`python3 -m ruff format --check`、`git diff --check` 与本地 Markdown 链接检查均 exit0。
- 在上述已推送 SHA 上实跑：`python3 scripts/verify-main-only.py` → **PASS，Root + 11 submodules**；全部本地分支与 origin live heads 只有 `main`，工作树均 clean。另对 12 仓逐一执行 `git rev-parse HEAD`、`git rev-parse origin/main`、`git ls-remote origin refs/heads/main`，三个 SHA 全部相等。
- 同一提交上 `python3 scripts/verify-repository-topology.py` → PASS；`python3 scripts/verify-contract-checkpoint.py --expected verification/contracts/checkpoints/w0b-exit.json` → PASS，精确 **4 active / 12 broken / 1 illegal**。只激活两条 Scheduler 边；Storage 与真实 Agent 边均未冒进激活。
- 最终真实 smoke 命令使用 owned 临时 pnpm→corepack wrapper、现有 PG/Redis 实例与独占数据库/精确 prefix：
  - `python3 scripts/e2e/run_capability_bff_smoke.py --postgres-admin-url 'postgresql://nako@127.0.0.1:5432/postgres?options=-csearch_path%3Dpublic' --redis-url redis://127.0.0.1:6379 --bff-node-bin /Users/nako/.nvm/versions/node/v22.22.2/bin --capability-node-bin /Users/nako/.nvm/versions/node/v24.20.0/bin` → exit0，8/8。
  - `python3 scripts/e2e/run_scheduler_bff_smoke.py --postgres-admin-url 'postgresql://nako@127.0.0.1:5432/postgres?options=-csearch_path%3Dpublic' --redis-url redis://127.0.0.1:6379/7 --bff-node-bin /Users/nako/.nvm/versions/node/v22.22.2/bin --go-bin /opt/homebrew/bin/go` → exit0，11/11；Agent 为明确的 receipt stub。
  - 两门绑定最终 BFF `c5e9b3c…`、Capability `9c88d0d…`、Scheduler `975dee59…`；全部自有资源已回收，没有修改 hosts/resolver 或放宽 loopback 边界。集成仅绑定已验证字节，不重复运行不变 owner 全门。
- W0B-11/15/16 标记已验收。后续 owner：W1 IAM → BFF → kokoro-app；其后按批准设计推进 Storage、Platform、Agent、System，Billing 最后。112 条静态违规、1 项 System TypeScript 未验证、12 broken 与 1 illegal 仍是实际差距；镜像/全仓 E2E/SLO 未执行，不声称全项目完成。
- 全局 Goal 的 Wave 0–7 目标未完成。本次工具查询仍返回旧 `blocked` 状态；原 DNS 阻碍已通过真实 CLI 消除，当前接口仅支持 complete/blocked/paused，无 resume 操作，因此未创建替代 Goal、未缩小目标或误标 complete。任务执行进度以本账与 task.md 为准。


## 2026-09-22 — 继续整体闭环，启动 Wave 1

- 用户要求继续，核心聊天和 AG-UI/工具交互按真实可运行体验验收，不以 owner 单测替代浏览器端到端结果。
- Goal 工具重新查询为 `active`，原整体 Wave0–7 目标继续沿用；不重建 Goal、不缩小完成定义。Root `136e12d7…` 工作树 clean。
- 先进行三条明确责任的只读预检：IAM owner、Web 聊天/同源边界、主控 BFF admission；任务卡见 task.md §6。通过后由 Root 冻结精确计划，IAM owner 先发布，BFF/Web 顺序消费；Billing 仍最后。

- 用户异步确认默认个人私有、显式分享。已写入批准设计 §1.1，要求列表/详情/搜索/AG-UI/审批/附件与产物逐边界授权；当前仅确认需求，尚未声称现有代码满足。

- W1-P1/P2只读盘点结束；Root自跑IAM标准 `PATH=/Users/nako/.nvm/versions/node/v24.20.0/bin:$PATH corepack pnpm test` →80 files/682 passed、13.77s，0fail/0skip。未运行真实IAM资源门。
- Web真实现状不是文档中的Auth.js/OIDC，而是旧magic-link/session HTTP +AES-GCM cookie；仍直连IAM。AG-UI入口已有，浏览器测试主要fixture，输入附件和编辑/重新生成缺失，reconnect状态未完整上抛。已将核心可运行验收矩阵写入task §7，避免用静态UI假装聊天闭环。
- Root独立确认BA1.7.3 introspection查询当前client/session，却未校验session.userId与user存在；无FK下现hasMembership只查member行。W1A必须增加最小current-facts查询及孤儿/错绑定负例；不扩大成新身份系统或新增表。
- 当前执行计划切至Wave1A，发布user-only/no-body session admission与生成SDK；IAM SDK engines保持Node24，未来BFF从固定OpenAPI生成Node22client。暂不处理63operation授权/ADR005execution，不声称W1完成。

- Wave1A 控制文档复验：Root handbook/topology 回归14 passed，topology PASS，Markdown本地链接与git diff --check通过。IAM三文档门已交原负责人续任，Root保留所有Git操作；本记录不代表运行实现完成。

- 控制计划已提交并推送 `96a283db`；其上 Root 全量 `python3 -m pytest scripts/tests -q` →495 passed/0 failed/0 skipped，47.07s。
- W1后续边界复核：BFF Chat已有owner predicate，但Project的list/find/update与Redis缓存key仅tenant维度，ScheduledTask列表也仅tenant；这些不是本次IAM identity endpoint能解决的权限，必须进入BFF资源授权切片，同tenant他人负例通过前不宣布默认私有闭环。Web session adapter已有Bearer转发，BFF当前仍只使用service secret+自报tenant/user headers；W1B需移除这条身份来源，并保留独立的Scheduler服务回调与显式只读share边界。

- W1A三文档门通过：IAM TECHNICAL_DESIGN/API_CONTRACT/DATA_MODEL明确无body/query、user-only scope、只读RepeatableRead当前事实、无FK孤儿拒绝和Node24 SDK边界；Root核对BFF relay方向、普通header不扩展黑名单。Agent在基线35d868a4验证contract:check/prisma:validate通过，contract:breaking为0 error/400既有warning；仅三文档变化。Root已续派同负责人进入TDD实现，运行能力尚未验收。

- W1A首次冻结41文件，Root独立复验format/lint/typecheck/contract+breaking/sdk/schema/build全部通过；标准82 files/701 passed（4.87s）、真实integration28 files/170 passed（25.70s），自有资源清理通过。独立审查0 Critical/1 Important/0 Minor：Guard/parser错误发生在Controller header前，缺no-store。已回派同负责人修复并增加错误header回归；未提交或发布IAM。consumer仍需clean候选提交后实跑，不绕过provenance门。

- no-store修复首轮后Root真实HTTP探针发现相同缺口在框架接受的大小写/尾斜杠路径仍存在（401，cache header为null）；canonical路径已为401/no-store。已回派通过Express本身路由匹配统一前置策略，补变体400/401/413测试，不更改全局路由语义；探针私有DB/prefix已回收。

- W1A实现已精确提交IAM `54d0d5f923c82e6145c71c6e9ea6eb571cc6713c`（43文件，未推送）。提交前最终冻结hash与提交内容一致，独立SPEC/QUALITY0/0/0；Root完整format/lint/typecheck/contract+breaking/sdk/prisma/build均通过，82 files/701标准测试（5.03s）、28 files/174真实integration（29.16s），no-store含路由变体全部覆盖。现在在clean候选提交运行仓外consumer，尚未宣布发布。

- clean候选 `54d0d5f…` 的 `pnpm test:consumer` 已实跑2文件/2项通过（10.75s），包括仓外安装、编译和新method真实调用。Root接收owner交付后仅更正4份owner文档，形成文档release `30f7dbffa8bac3dc9b3a5a163babc3722384051a`；runtime/contract/test/SDK/lockfile字节不变，正在该release再核验consumer provenance。

- IAM release `30f7dbffa8bac3dc9b3a5a163babc3722384051a` 的clean工作树consumer复验2文件/2项通过（11.19s）；仅文档相对54d0d5f发生变化，SDK/runtime/contract/test字节未变。Root现在提升IAM gitlink与3个commit-blob tuple，不修改任何edge状态或其它owner artifact。

- Root组合门：topology PASS、w0b-exit精确4active/12broken/1illegal PASS，495 tests通过（42.55s）；static112violations/1unverified保持原事实。Markdown检查发现IAM技术文档两条既有Root手册相对路径失效，已在仅2行docs提交`259a66e6a569889c030734f380e99685d8b9e21c`修复，运行代码/contract/SDK与54d0d5f保持一致；最终组合改锁此文档release，不扩大业务范围。

- 最终组合只读审查（gpt-6-astra/high）SPEC PASS、QUALITY Approved，Critical/Important/Minor=0/0/0；最终IAM259a66e gitlink、3个tuple、provenance及默认私有/BFF-Web未完成边界一致。新pin上Root全量495 passed（42.27s），checkpoint PASS；最终release仓外consumer2/2（11.25s），IAM HEAD=origin/main=live main且clean。资源基线仍为保留原2数据库、testkeys0。本轮没有运行真实BFF/IAM/Web浏览器组合或发布镜像，不以本片替代后续验收。
- W1A-2代码与验证已就绪；Root最终提交和发布后main-only/clean审计随后执行，完成前保持待集成验证。整体Goal继续active，下一owner为BFF（IAM admission、权限/私有资源边界），其后Web；Billing最后。

## 2026-09-22 — W1A 最终验收

- IAM代码 `54d0d5f923c82e6145c71c6e9ea6eb571cc6713c`；最终发布 `259a66e6a569889c030734f380e99685d8b9e21c`（后两提交只改文档）。Root集成 `a7585a97a2bf34eff33f2d20af3a46779aca1884` 已推送；仅1个gitlink、3个IAM证据tuple前移，所有edge状态保持原值。
- 已发布Root提交上：`python3 scripts/verify-main-only.py` → PASS，Root+11子仓均clean且本地/远程只有main；额外逐仓核对HEAD=origin/main=live main，12/12相等。`verify-repository-topology.py` 与 `verify-contract-checkpoint.py --expected verification/contracts/checkpoints/w0b-exit.json` 均PASS，4active/12broken/1illegal。
- 最终新pin Root回归：`python3 -m pytest scripts/tests -q` →495 passed/0 failed/0 skipped（42.27s）。IAM full静态/生成/构建门、701标准、174真实integration、最终release仓外consumer2均通过；完整实际命令与各次结果见本节之前记录及IAM CURRENT。独立任务审查与最终组合审查均0/0/0。
- 静态全仓治理依旧112 violations/1 unverified（System TypeScript）；旧400条breaking warning保留，没有放宽门禁。真实BFF/IAM/Web浏览器E2E、模型provider、全仓镜像/SLO未验收；W1A不代表W1或完整聊天闭环。
- W1A-1/2已验收；Goal工具确认active，整体Wave0–7未完成。后续owner为BFF，再Web；个人私有/显式分享、同tenant不同用户负例仍是后续资源授权硬要求，Billing最后。
- 本计划scratch只保存过渡日志/报告；验收事实已固化到本账、task与owner CURRENT，收尾后删除本计划专属scratch，不触碰其他计划或预存数据库。

## 2026-09-22 — W1B 启动

- Root沿用active Goal，接续BFF而非重做W1A。BFF基线c5e9b3c上执行Node22.22.2 `corepack pnpm test`：199 passed、0 failed、0 skipped，5.43s；未执行改后验收。
- `w1b_privacy_reviewer`（sol/high）只读交付；Root核对Run control漏Conversation owner gate、ScheduledTask稳定ID漏subject、Project无owner与tenant缓存/slug，以及project_ref关系缺口。已纳入同一W1B计划Task2；没有把IAM会话有效等同资源权限。
- Root冻结新auth目录、Node22 generated IAM0.2.0、三个显式服务例外及连续私有资源切片。当前仅授权BFF三文档门；尚未修改runtime/schema，未提升gitlink或激活edge。

- W1B控制计划已提交并推送Root `818f714841e83e5ea6ace630f7254f239c72255a`；Root handbook/topology回归14 passed，topology和本地Markdown链接通过。BFF负责人三文档停写交付后，Root完整审阅diff（仅三文档）、复跑 `corepack pnpm contract:check`（21 passed，63 operations、两旧generated drift通过，Library既有1 warning）及`schema:check`（4 passed）；文档门通过。
- 已续派同一BFF负责人进入Task1 TDD实现，仍只写计划精确文件集；Root独占Git。预存IAM两数据库仍保留，Redis8 PONG；本门未创建/清理基础设施。Task2私有SQL/Run control尚未实施，边界不得提前宣称闭环。
- Root另在未改动的`src/http/routes/scheduler.ts`及对应dist上执行纯函数探针：同tenant、不同user、同path/key生成的ScheduledTask ID完全相同，确认Task2碰撞缺陷（无DB/网络操作）。资源授权必须先于receipt且事务内重验的补充已提交并推送`91908b3b`，不是修复完成证据。

- W1B Task1负责人已停写交付：64文件，BFF HEAD仍c5e9b3c，未操作Git；owner报告222标准/35真实integration及contract24/architecture26/schema4通过。Root已核对精确文件范围、vendor owner blob一致、schema/lock未改，冻结hash；进入独立SPEC/QUALITY审查与Root重跑，尚未提交或提升gitlink。
- Root在该64文件冻结工作树独立执行Node22.22.2 `corepack pnpm format:check/lint/typecheck/contract:check/test:architecture/schema:check/test/build`，全部exit0；contract24、architecture26、schema4、标准222（5.44s），0失败/跳过。真实新库`bff_w1b_root_c15823ee2894`先apply-schema再`test:integration`，35 passed（14.25s）；自有库已删除、所有预存库保留、Redis8前后key完全一致。独立审查尚未放行，以上不代表Task1已验收或整体私有资源已闭环。
- Root额外loopback探针发现当前测试未覆盖的契约偏差：严格合法IAM 429响应省略可选`Retry-After`时，BFF映射为503而不是既定429；`assert.equal(actual.status,429)`真实失败。临时HTTP server已关闭，无数据库操作；已交独立审查汇总，Task1保持未放行。
- 用户进一步明确“目的是开发、写代码”，避免深陷运维。主控已收敛当前计划：只修本片明确行为/契约缺陷，后续直接推进资源权限与聊天代码；IAM监听硬化、部署/镜像/SLO后置，开发联调复用现有真实HTTP fixture并准确标注证据等级；不在每个小片重复全仓审计。该调整不取消权限负例、事务正确性和测试资源隔离。
- 用户要求明确能力边界并用task/progress整体把控；主控复用现有两份文档，在task首页补当前开发关键路径和九个owner的负责/不负责边界，没有另建任务中心。开发优先裁决及首轮审查状态已随Root `a541254f` 推送。独立审查最终为0 Critical/2 Important/0 Minor，准入429映射与header/body总预算已批量续派同一负责人，仅3个代码/测试文件加报告；Task2仍待本片冻结提交。
- W1B-1代码已由Root精确提交BFF `a898c90fe2b5447178a76fb04b0fedf9fa98e0d5`（64文件、提交字节等于冻结hash，提交后clean）。429保持稳定状态、合法Retry-After才转发及header/body总预算两项已修复；独立增量复核均ADDRESSED、无新缺陷，SPEC Compliant/QUALITY Approved。
- 最终代码上Root执行`corepack pnpm format:check`、`lint`、`typecheck`、`test`、`build`均exit0；标准 **227 passed/0 failed/0 skipped（5.43s）**。独占空库`bff_w1b_root_51dcbc524d9f`先`db:apply-schema`再`test:integration`：**35 passed/0 failed/0 skipped（12.02s）**；自有库已删除、预存数据库保留、Redis8无增删。contract24/architecture26/schema4此前独立通过；fix仅3文件，contract/generated/schema/lock字节未变，标准测试亦覆盖相应断言，未重复生成。
- Task1代码切片验收，Root gitlink仍锁c5e9b3c、IAM edge尚未激活；真实跨仓联调留Task3，不声称整套登录或个人私有已闭环。现续派同一BFF owner按Task2实现Project/ScheduledTask与Chat关联/Run control私有权限；主控维护边界与复核，不抢写子仓。
- Task2负责人确认不需修改`test/doubles/`，严格保持批准文件集，已开始Project owner/schema/查询及真实HTTP负例代码；当前工作树仍在变化，未提前验收。Root并行只读预检发现System smoke旧tenant-header负例需改为“manifest忽略恶意header、绑定server tenant”，普通模型查询使用两个固定身份token；不恢复旧身份入口兼容测试。
- W1B-3P已验收只读报告：IAM现有`createInternalHttpApplicationFixture`已提供真实PKCE用户token、Nest loopback HTTP、独占数据库/Redis前缀与close；session HTTP integration已有sign-out后旧token拒绝证据。后续仅需薄的IAM test-owned CLI供Root驱动真实BFF联调，不需先改部署入口。未新增测试服务、未执行组合测试、不将预检写成edge激活证据。
- 2026-09-23 W1B-2交接检查：原BFF写入代理在额度中断后结束，工作树保留33个已跟踪修改+1新文件，HEAD仍a898c90，未提交；Root与BFF gitlink尚未更新。Root在该未冻结工作树执行Node22`corepack pnpm typecheck`通过、`corepack pnpm test` **231/231通过**、`corepack pnpm schema:check` **4/4通过**，`git diff --check`通过。这些只证明当前快照的静态与标准测试，不是Task2验收。
- 同一快照Root新建独占空库`bff_w1b_root_5daeb1ad3ef4`，`db:apply-schema`通过；真实PG/Redis `test:integration` **35/36通过、1失败**：`test/scheduler-dispatch-receipt.integration.mjs:306`仍以旧位置参数调用`ScheduledTaskService.create`，新具名scope传入后在`scheduled-task-repository.ts::requireLineage`读取`undefined.trim`。自有库已删除、既有库保留、Redis8 key前后相同。Root批准仅将该旧fixture调用改为`{tenantId,subjectId}`，并继续核验真实同tenant/跨tenant负例；任务仍进行中，不宣称个人私有完成。
- 现阶段真实问题是开发切片尚未收尾和一处测试调用漂移，而非数据库或部署故障。Web旧IAM直连、BFF→IAM真实跨仓联调、Storage/Agent完整聊天与Billing仍按后续Wave推进；支付最后。
- 2026-09-23 W1B-2由Root接续唯一BFF写入：旧Scheduler receipt fixture改为具名owner scope后，独占空库真实integration **36/36**。Root以新断言复现ScheduledTask通过项目slug创建时落库`project_id=slug`（35/36 RED），事务锁内解析同owner Project canonical ID后恢复 **36/36**；同租户和跨租户私有访问拒绝不增事实、receipt或outbox。未借此改动IAM/Web等下游。
- 独立只读审查在冻结前指出Share二次读取撤销竞态仍可返回200元数据、跨租户Project/ScheduledTask详情/变更缺测试。Root先加Share竞态RED（200≠404），再改`listMessages:null`为`404 share_not_found`；补跨租户detail/patch和前后事实断言。审查员复核两项均关闭、无新阻断，未写文件/共享状态。
- BFF `6238599667110fbfbc2d5ef3a9d53731f2623cfe` 已精确提交35文件并推送main，提交后子仓clean。Root Node22最终执行`corepack pnpm format:check`、`check`（lint/typecheck、generated漂移、OpenAPI lint/semantic、contract **25/25**、标准 **231/231**、build）、`schema:check` **4/4**及`git diff --check`，全部exit0。新独占空库`bff_w1b_root_e6739d29a8df`的`db:apply-schema`和真实PG/Redis `test:integration` **37/37**通过，库已删除、预存库完整、Redis8 keys前后相同。该证据只验收BFF owner代码切片；Root gitlink和跨仓真实IAM↔BFF组合仍分别待本轮提交及W1B-3验证。
- Root `5d98df4d0e1ceffd4c2cb18c9a8818cb0bff6f75` 已将BFF gitlink前移至`6238599…`并推送main；Root `python3 -m pytest scripts/tests -q` **495/495**通过，提交后`verify-repository-topology.py` exit0，Root/BFF工作树clean。`verify-ten-repository-standard.py --format json`仍为**130 violations/1 unverified**，其中BFF 28项包含vendor owner契约误按本仓公共契约检查及现有TS严格度差距；这不是本次owner功能门全绿，列为后续治理，不转移当前开发关键路径。真实IAM↔BFF组合、Web同源会话和完整聊天执行链尚未验证。
- 2026-09-23 W1B-3A IAM test-owned联调入口已提交并推送IAM main `b2ad9dd6906b73f275b96d570dad66eae86e97e9`，仅新增本仓fixture host与聚焦integration test；没有生产IAM API/schema改动。Root用Node24、独立IAM PG/Redis环境重跑**3/3**（真实PKCE/Nest HTTP，Member失效403、signout401、reset/stop/EOF/启动中TERM清理）；typecheck/format/lint exit0，前后所有预存数据库与Redis8 key完整、新增残留均零。独立只读审查发现的启动中TERM清理竞态和缺乏清理断言两项已修复复核无新阻断。此为IAM测试入口验收，不等于BFF消费已联通；Root gitlink尚待组合任务同步。
- 2026-09-23 W1B-3B Root真实IAM→BFF runner已冻结，两文件由同一Agent写入，未操作Git。Root独立执行聚焦pytest **8/8**、全Root scripts pytest **499/499**、真实Node22当前源码build+BFF HTTP→Node24 IAM Nest/PKCE fixture **7/7**；验证恶意旧header不能改变SQL owner、缺Bearer、登出后同key重放、reset新身份不可读原资源、当前Member失效、IAM失联及凭据不入日志。IAM库2→2、对应Redis键0→0，BFF自有DB/进程0残留。独立审查初轮P1/P2协议半行阻塞、发布SHA绑定、失败清理和稳定错误码已修复复核无新增阻断。当前Root IAM gitlink尚未提交，实跑显式使用`--allow-unpublished-iam-gitlink`；不能据此激活EDGE-BFF-IAM，须提交后无过渡参数复跑并完成inventory/checkpoint及旧smoke回归。
- W1B-3B已由Root `1d1c4df85fd7b7d39a8465d9746ac2be59b5ba4d`精确提交推送main：IAM gitlink前移`b2ad9dd…`，BFF仍`623859…`，inventory中106个BFF/3个IAM commit-blob引用按当前SHA/digest机械更新，所有16条edge的状态、协议和版本未改。发布提交后Root在**不带过渡参数**下重跑真实IAM↔BFF **7/7**，两个子仓SHA/clean/Root gitlink一致，BFF DB/进程零残留、IAM库2→2/Redis键0→0；`w0b-exit`精确checkpoint PASS、Root topology PASS。EDGE-BFF-IAM仍标broken，因Capability/Scheduler/System旧smoke准入回归与正式edge证据尚待处理，不把真实联调和库存门混同。
- W1B-3C未提交冻结快照：共享严格IAM wire stub仅供旧owner smoke，不冒充真实IAM；Capability与Scheduler旧用户路径改Bearer，BFF release锁`623859…`，原8/11 case一个不删，Scheduler callback专用服务凭据不变。Root独立聚焦pytest **110/110**、全Root scripts pytest **524/524**、ruff check和diff-check通过；真实Capability **8/8**、Scheduler **11/11**，各自独占DB/Redis/进程/临时文件清理通过。独立只读审查初轮2个P2（DNS多地址歧义、stub启动失败socket泄漏）经同一writer TDD修复，复核无新P1/P2。System旧smoke与正式IAM edge仍待后续片，不提前写作全仓闭环。
- W1B-3C已由Root `0295fbdda439a4008cb114c8d726cf893694fc4b`精确提交并推送main，`w0b-exit` checkpoint及topology均PASS，Root工作树提交后clean。W1B-3D在该共享stub上修正System旧smoke的Root/apps路径、BFF models A/B Bearer、server-only manifest身份语义，并保留System/Agent跨租户与发布配置断言；Root独立聚焦pytest **23/23**、全scripts **525/525**、ruff check、真实System/BFF/Agent HTTP smoke PASS，System c0a76a3/BFF 6238599/Agent 741c928均SHA/clean/index gitlink一致，自有DB/Redis/临时文件残留0。独立审查的当前index gitlink门P2已修复复核无新阻断；尚待Root精确提交，不代表BFF-System generated edge激活。
- W1B-3D已由Root `9fa6d2cd68d06dbd9dc235da520ba4c15089b1e1`精确提交并推送main，Root/System/BFF/Agent代码与索引清洁；System smoke的成功不激活BFF-System handwritten edge。W1B-3E现在仅处理BFF→IAM事实边：IAM0.2.0 owner contract与BFF generated client、真实IAM→BFF 7/7及原owner 8/11/System回归已齐，仍须在Root inventory新增精确当前checkpoint与版本/证据绑定，未运行的新门不提前记PASS。
- W1B-3E提交前冻结候选：inventory只将`EDGE-BFF-IAM` broken→active，IAM `b2ad9dd…` 0.2.0 owner contract与BFF原`259a66e…` vendor字节相同；31个BFF commit-blob evidence、`@hey-api/openapi-ts@0.99.0`和Node22.22.2两个版本断言均通过。新`w1b-iam.json`精确**5 active/11 broken/1 illegal** checkpoint PASS，其他15条edge语义零变化，历史w0b-exit未改；Root聚焦compatibility/checkpoint **81/81**、全scripts **526/526**、topology PASS。静态全仓另实测9仓/130 violations/0 unverified（exit1），如实保留。独立SPEC/QUALITY均0个P1/P2且复核全部证据；尚待提交后main-only/clean与最终报告。
- W1B-3E已由Root `7b6e486b630a40ff825736299ef02720cbfbef6a`精确提交推送main；发布提交上`verify-main-only.py` PASS：Root和11个子仓均clean且本地/远程仅main，Root HEAD=origin/main。`verify-repository-topology.py` PASS、`verify-contract-checkpoint.py --expected verification/contracts/checkpoints/w1b-iam.json` PASS，精确5 active/11 broken/1 illegal。W1B-3 IAM→BFF组合切片正式验收；Web同源登录、Storage、Platform、Agent聊天执行、System generated edge与Billing仍在后续Wave，不以本切片宣称整体Goal完成。当前开发关键路径转W1C Web，支付最后。
- 2026-09-23 W1C-P两份独立只读预检（Web auth消费面、IAM OIDC owner）完成，均未改文件、Git或启动服务。冻结输入：Root `ab0dcda481910c8689937364bd7bae7d961bea3d`，Web `ce4e466c960c4b40a87a7be38b5a56f265f7a12f`，BFF `6238599667110fbfbc2d5ef3a9d53731f2623cfe`，IAM `b2ad9dd6906b73f275b96d570dad66eae86e97e9`。已证实IAM `/iam` Code+S256、精确allowlist、原生issuer cookie与HTTP consumer测试存在；BFF仅`/v1`已有Bearer admission、`/iam`未接线；Web仍用旧IAM magic-link/team-session直连，session以外多个BFF代理缺Bearer而只送旧identity headers。IAM自身测试不等于Web→BFF→IAM组合通过。Root创建Wave1C owner-first计划，BFF协议relay先于Web RP；此刻只完成预检/计划，未宣称W1C代码或测试通过。Auth.js与Next16兼容、OAuth `resource`/scope在authorize/token/refresh三段传递必须在Web实施时实测，不作推断。
- W1C计划只读审查初轮3 P1/2 P2并修复核心：IAM OAuth client/resource/redirect tuple与真实交互矩阵、issuer/Product cookie隔离、Web→BFF全edge不得因登录中继激活；复核又修正生产`__Secure-` cookie、合法logout确认Path、准入前/上游后socket证据边界，以及issuer URL与callback URI区分。独立IAM只读预检发现未验证redirect分支当前指向IAM未开放的`/iam/error`；记录owner负例，不开放BFF通配。Root `git diff --check`、`python3 -m pytest scripts/tests -q` **526 passed + 4 subtests**、`verify-repository-topology.py` PASS，均在仅Root文档变化的当前快照运行；不是W1C代码门。
- W1C-1 BFF三文档设计门当前工作树已写入：`apps/kokoro-bff/docs/TECHNICAL_DESIGN.md`、`docs/API_CONTRACT.md`、`docs/DATA_MODEL.md`；固定IAM b2ad allowlist commit blob SHA-256 `f63dacfa8a7bcec3c56efb8ffb762a3f8bd82bb380eff40a1462db1e77d61ead`、Better Auth snapshot `b2eac1919e16fdc30a40bee0f3c4300b641bd8f674214aea7731bf10299559e1`，均经Root独立`git show | shasum -a 256`比对。设计明确BFF独立`/iam`服务例外、固定路径/方法、原生OAuth/cookie/Location及无新SQL事实，Web消费BFF自身只读policy artifact而非复制IAM schema。独立审查首轮1 P1/2 P2（Web交互页签名query、429/logout安全headers、机器policy发布证据）均由同一writer修正，增量复核0新P1/P2；BFF `git diff --check` PASS。当前仍是**未提交设计门**，未改BFF源码/contract/schema，未运行BFF contract/schema/真实HTTP，不把文档写成relay可用。
- Root W1C控制计划、任务卡与证据账已以 `b89de955` 精确提交并推送main；该提交不包含仍在BFF工作树中的设计/实现，不是BFF release。W1C-2 Web可行性第二轮只读研究核验维护者固定`next-auth@4.24.15` tag对Next16/React19 peer范围及Route Handler异步API，但Web当前无next-auth/Redis依赖，安装/build/E2E均未执行。关键待测：Auth.js v4 browser sign-in query可覆盖固定authorize参数、默认callback未保证resource进入token request；Web需受限token hook与真实wire断言authorize/token/refresh各恰一个`resource`，以及server-only Basic、Web Redis CAS/tombstone、HttpOnly加密Product Session与公开session字段隔离。计划已补这一门，不能把依赖peer匹配当运行闭环。
- 用户提示Docker已启动后Root只读探测：`docker info`显示daemon 28.5.1、7个已存在容器但**0个运行**；`docker ps`为空。宿主机现有`postgres`监听127.0.0.1/[::1]:5432且`pg_isready`接受连接、现有`redis-server`监听127.0.0.1/[::1]:6379且`redis-cli ping`为PONG；没有启动/停止/重建容器或基础设施。开发组合按用户最新裁决采用单实例/单库/单应用账号，owner仍按schema/表及代码边界隔离；本轮W1C继续写代码，不为角色/部署另开任务。当前IAM test fixture既有临时DB/Redis前缀为隔离验收，已清理且零新增残留。
- 2026-09-23 W1C-1 BFF relay代码已由BFF唯一writer提交并推送main `55b9150d44ad65f8e6e62e5242d2fa9f95576eab`，子仓clean；Root独立Node22复跑`format:check`、`lint`、`typecheck`、`contract:check`、`test`、`schema:check`、`test:architecture`、`build`全部exit0，独立代码复审0个新增P1/P2。真实IAM基础HTTP1/1不覆盖首次成功Code+PKCE，因此BFF gitlink/库存尚未提升，也不宣称完整协议或Web登录闭环。
- W1C-1G Root跨仓固定blob校验三脚本经独立审查0 P1/P2、聚焦`14 passed`、Root全量`540 passed, 4 subtests passed`、Ruff检查/格式检查及`git diff --check`通过；Root精确提交并推送`070b0589f49aad97c07731a930fb68e495af258a`。真实CLI因尚未提升BFF gitlink且IAM test fixture写入中，当前预期红；待两个owner release后按固定gitlink复跑。IAM W1C-1F仅测试fixture四文件由唯一writer实施中，Node24真实首次流与资源清理尚未验收。
- IAM W1C-1F fixture 经两轮独立复审修复HTTPS校验、EOF/错误命令/启动失败清理及并发测试误报，最终P1/P2=0/0；Root独立在现有PG/Redis运行新Web OIDC host **5/5**、旧admission host独立**3/3**，Node24 format/lint/typecheck均通过，`iam_web_oidc_*`与`iam_hardening_*`测试库及本fixture Redis prefix检查为0残留。IAM精确四测试文件提交并推送main `f0bb18e6fee8f4b1ee9a1c2d9e7aa2eb4621e614`，无生产API/schema/contract变化。
- Root另试跑 IAM 全量`test:integration`结果为**175通过/4失败**：3项旧admission host测试使用全局`iam_hardening_*`集合，与并行suite互扰；`fresh-install`在当前本机role/Prisma组合报P1010。Root只清理本次产生的3个精确临时`iam_hardening_*`库，预存业务库与Redis未动；不以这次全量红冒充全门通过，也不为运维配置扩围。新fixture聚焦和旧host隔离门真实通过，完整IAM integration仍列待诊断。
- BFF W1C-1 SHA-only来源重pin由唯一writer在IAM新提交后完成：IAM allowlist与Better Auth snapshot固定blob digest不变；BFF仅六文件各替换旧IAM commit为`f0bb18e6…`，派生JSON，Root独立Node22 `contract:check` **25/25**、标准`test` **248/248**与diff-check通过。BFF精确提交并推送main `804a5832c066ce60dde9f4592856ac40ce20f402`；Root尚待提升两gitlink、重算库存证据并做真实OAuth正向链，不能把pin更新当组合成功。
- Root `4d2c149b6cfdd1bc08e8340926b4652ec9ea049e` 已精确提升IAM `f0bb18e6…` 与BFF `804a5832…` 两gitlink，并机械重算inventory中140个commit引用与16个变化的blob digest，16条edge语义/版本均不改；三个旧smoke pin及两个测试同步，独立审查0 P1/P2。发布后`verify-iam-relay-policy.py`、`verify-contract-checkpoint.py --expected w1b-iam.json`、topology均PASS；Root全量`540 passed, 4 subtests passed`、聚焦组合`187 passed`。Web子仓仍是三文档未提交，未暂存进Root release。
- 在上述新pin上，Root串行实跑真实IAM准入→BFF **7/7**（BFF/IAM SHA/clean/gitlink一致，自有资源0残留）、Capability→BFF **8/8**（自有库/Redis前缀/进程均清理）、Scheduler→BFF **11/11**（Go1.26.8、Redis DB7隔离、自有资源清理）、System/BFF/Agent真实HTTP组合 **PASS**（inference未执行、自有资源清理）。这四条证明旧owner能力未被relay提交破坏，**不证明首次OAuth Code+PKCE或Web同源登录**。首次调用Capability smoke误传`node`文件而非toolchain目录、Scheduler smoke误传非DB7 Redis URL、System smoke误传node文件而非目录，均在资源创建前失败；按脚本要求重跑后PASS，不归因数据库并发。
- 用户再次确认开发应用使用一个PostgreSQL数据库/一套账号。此前“串行以避免并发占用数据库”表述不准确：串行只为减少当前测试fixture全局集合断言的互扰，不是应用连接限制；正式应用可以并发访问同库。Root将单库+owner独立schema/连接URL写入AGENTS、SQL手册、架构标准及治理测试，明确部分现有installer仍锁`public`/整库空白，代码适配W1C-DB未完成前不声称单库应用真运行；测试临时库不是长期应用库，也不引入新role/运维拓扑。
- Web W1C-2三文档门经独立审查修复4个P2、1个P3及单开发库目标与Root规范不一致P2，最终复审0个P1/P2；Root修正最后一处旧措辞，Web仅三文档精确提交并推送main `62da3f856efdb207ea662010382ad14a965009a0`，无源码/lockfile/contract或资源操作。BFF `804a5832…`、IAM `f0bb18e6…`、policy blob digest由审查复核。三文档门通过**只允许进入源码**，Auth.js、Product Session、/iam同源入口及浏览器组合均未实现。
- W1C-1H真OAuth联调脚本正在由Root唯一脚本writer实现（另有只读Web源码范围盘点），尚未运行完整正向链。脚本审查提前发现IAM test-owned首次流fixture把OIDC退出URI写为根路径，与BFF固定relay仅允许`/auth/sign-in`回跳不一致。IAM仅改3个测试文件、生产契约/Schema/API未动，提交并推送main `c9a277213ade41b9225ab0f158b89092d1869a83`；Root独立重跑聚焦5/5，自有数据库与Redis资源清理。BFF仅6个来源pin文件更新到IAM c9，allowlist/snapshot digest保持不变，提交推送`1fae01e309aed26439ae5f172a70551621107222`；Root独立Node22 contract25/25、标准248/248。Web三文档只更正最新BFF/IAM来源及policy digest，提交推送`38683a5c2a46af3e9d604b5d7219a864684d5ad1`；Web源码仍未实施。
- 当前Root候选仅提升上述3个gitlink、精确库存commit/blob证据与5个旧smoke常量，以及CURRENT/task/progress；16条edge状态不变，仍是**5 active/11 broken/1 illegal**。`804a583…`旧四条真实smoke只属历史release，不为`1fae01e…`代签；新pin上的relay来源CLI、旧smoke与首次Code+S256真HTTP待Root发布后实跑。IAM全量integration既有并发fixture互扰与本机P1010仍待代码/fixture诊断，不能用测试串行描述成应用数据库并发问题。单开发库owner-schema适配W1C-DB亦未完成。下一步先完成Root固定来源发布，再验收W1C-1H、Web代码及真实浏览器链；不触碰支付和部署扩展。
- Root来源候选经独立只读审查0 P1/P2：库存191个commit+blob digest均匹配精确gitlink；本轮149个commit SHA引用、2个实际blob digest前移，16条edge语义/状态不变。`verify-contract-checkpoint.py --expected .../w1b-iam.json`、topology、暂存区diff-check及全Root scripts **545 passed、10 subtests passed**；Root精确提交推送 `a5ca0afc4eff8e98259273aadf5d055dec6920d4`，发布后`verify-iam-relay-policy.py`/checkpoint/topology均PASS。未跟踪W1C-1H两脚本仍属另一个未验收切片，故此时不宣称Root全工作树clean/main-only门已过。
- `1fae01e…`新pin真实回归由Root串行复跑：IAM admission→BFF **7/7**、Capability→BFF **8/8**、Scheduler→BFF **11/11**、System/BFF/Agent HTTP **PASS**；每条固定source SHA/gitlink一致，自有PG/Redis/进程/临时文件均清理，System inference仍未执行。三条旧owner链使用明确标记的IAM wire stub，不能替代真实IAM。此次无需再用旧`804a…`证据代签。
- W1C-1H候选runner在相同固定IAM/BFF commit真HTTP已验证discovery、sign-in、首次authorize、select-tenant、consent、Code+S256 token、userinfo、get-session均200且issuer session存在；带`id_token_hint`的`end-session` **401 `invalid_token`**，无hint对照 **400 `invalid_request`**。runner保持非零FAIL，不将部分成功冒称完整OAuth闭环；本轮IAM fixture DB、BFF临时DB、IAM Redis前缀均0残留。因果定位：test-owned host声明公网HTTPS issuer但没有Web同源JWKS回环，IAM既有consumer测试通过精确fetch映射解决同一测试边界。已派IAM唯一writer W1C-1I只修test-owned host；BFF无hint浏览器navigation metadata另列1J审查，不在Root runner隐藏绕过。Web W1C-2A独立唯一writer已启动固定policy只读GET同源入口，Auth.js/完整Web登录仍未实现。
- W1C-1I IAM test-owned host按owner-first只改2个测试文件：仅精确本fixture public issuer `/jwks` 的内部fetch映射到自身Nest loopback，stop/EOF/SIGTERM/失败恢复全局fetch，其他URL沿原fetch；生产API/schema/contract字节不变。Root独立Node24实跑真实首次OAuth签发→带hint logout聚焦**5/5**，format/lint/typecheck及自有DB/Redis 0残留；独立审查0 P1/P2，非阻断P3为子进程内global fetch恢复不可直接从父进程断言。IAM精确提交推送main `b838853a81ff34bd0f7a079ccc75ba6abd61d1ec`。BFF六文件只机械重pin IAM commit，allowlist/snapshot真实blob digest均不变；Root独立Node22 contract**25/25**、标准**248/248**，提交推送BFF main `cd1c2600ea2a6e0716b07628822a49653964675a`，新policy digest `457909cd8c6ce77d59ca4cb929f22b439ebf00154256381a0cc3d6a32c2e8fb2`。
- Root W1C-1H runner独立审查发现**2 P1/2 P2**：tenant/scope/ID token绑定、动态凭据日志扫描及shutdown窗口、logout state/Set-Cookie、revoke后实际失效尚未充分断言。新唯一Root脚本writer正在修复，仅限两未跟踪脚本；旧401仍是已记录真实红，不能因为IAM单仓5/5就标组合PASS。新IAM/BFF两gitlink及140处inventory来源与5个旧smoke常量已进入Root候选，精确checkpoint/topology在暂存索引上PASS，16条edge状态不变；新pin真HTTP与Root发布尚待完成。Web唯一writer获准对三份已有设计文档只做新SHA/digest机械re-pin，其余Auth.js/浏览器链未实现。
- Root新IAM/BFF来源候选经独立复审修正两处过度陈述后0 P1/P2：191项commit/blob从暂存gitlink精确读取，140处commit引用与2处blob digest变化，16 edge状态不变。`83022b65fafadc1fa5f741f6680dd0293d4af385`精确提交推送；发布后relay policy CLI与w1b-iam checkpoint PASS。Root在BFF `cd1c260…`/IAM `b838853…`新pin重跑真HTTP IAM准入**7/7**、Capability**8/8**、Scheduler**11/11**、System/BFF/Agent组合**PASS**，全部自有资源清理，System inference依旧未执行。历史`1fae01e…`不再代签当前pin。
- W1C-1H第一轮审查修复后，Root独立在固定新pin实跑首次未预同意OAuth **13 case PASS**：Code+S256、tenant/consent、token/userinfo、revoke后同refresh token `400 invalid_grant`、带hint原生JSON logout与旧session失效，自有资源0；Root scripts全量**558 passed/37 subtests**。但第二轮独立复审发现**2 P1/2 P2**：真实首次签名sign-in续接未走、异常上游header可能进runner stdout、部分JSON Content-Type未验、primary失败会被cleanup失败覆盖。原13-case结果只算阶段证据，W1C-1H尚未验收；新唯一脚本writer正TDD修复，不把HTML confirmation分支单测冒称真HTTP通过。
- Web W1C-2A首轮实现的固定BFF policy snapshot与commit blob digest一致；Root独立Node22 `pnpm check`全门exit0，Next build包含动态`/iam/[...path]`。独立审查1 P1/3 P2：Host/Origin需绑定server-only固定Web origin、Location原始编码路径、真实Next路由alias证据、API文档当前/目标语句。唯一Web writer正修，当前工作树未提交；Web Auth.js、POST交互/CSRF、Product Session与真实Browser→Web→BFF→IAM仍未完成。
- W1C-1H第二轮四项审查问题经唯一脚本writer TDD修复；独立只读复审 **0 P1/0 P2**、聚焦 **23 passed/52 subtests**。Root亲自用固定IAM `b838853a…`/BFF `cd1c2600…`与精确gitlink运行首次无session OAuth 真HTTP **15/15**：原生authorize→签名sign-in→continue→tenant→consent→Code+S256/token/userinfo→revoke后 refresh `400 invalid_grant`→带hint原生JSON logout→旧cookie session=false；自有PG/Redis资源0，异常header仅输出分类/布尔/数量。Root全scripts **563 passed/56 subtests**、py_compile与diff-check通过。两脚本尚未提交；无hint HTML退出确认只单测未真HTTP，留1J；Web同源与浏览器E2E仍未完成。
- W1C-1H Root两脚本与三份台账精确提交并推送main `bb60a6a466c73940ce7e1f19d7efcb0742571dea`；发布后`verify-iam-relay-policy.py`、`verify-contract-checkpoint.py --expected .../w1b-iam.json`、topology均PASS，Root HEAD=origin/main。15/15真HTTP证据仅覆盖IAM→BFF，不用作Web登录替代。
- W1C-2A Web GET中继经两轮审查修复可信固定origin、raw Location、无Content-Length/chunked请求体与Next真实HTTP测试隔离，最终独立增量审查 **0 P1/0 P2**；Root独立Node22 `pnpm check` **1259 tests + contract52 + architecture29 + lint/typecheck/build PASS**、Playwright **6/6**，真实Next system测试含chunked请求本地400且零BFF。BFF固定`cd1c260…:contract/iam-relay-policy.json`与Web snapshot SHA-256均为`457909cd8c6ce77d59ca4cb929f22b439ebf00154256381a0cc3d6a32c2e8fb2`，字节`cmp=0`。Web精确23文件提交并推送main `85b4bad25769efcca8f417e0232fdaa6c485bf01`，本仓clean且本地/远程仅main；Root本次候选提升gitlink/库存9处commit-blob并独立逐项核验，16条edge状态不变，Root全scripts 563/563与policy/checkpoint/topology PASS，独立库存审查无来源/状态问题。三页`/auth/*`当前未安装而会404，旧Web IAM直连仍存在，不宣称登录闭环。
- W1C-2A Root精确gitlink/9处库存来源与三台账提交并推送main `6f7b31c29f019f1306e6ebd03b7ccca725c729b3`；发布后`verify-main-only.py`确认Root+11子仓本地/远程均仅main、全工作树clean，Root HEAD=origin/main。topology、relay policy、w1b-iam checkpoint均PASS；真实兼容门仍按现状FAIL，精确 **5 active/11 broken/1 illegal**，未借Web GET中继激活Product edge或抹去IAM直连非法边。下一步W1C-2B实现Auth.js与同源交互/CSRF/Product Session并删旧直连，再做Web→BFF→IAM真实组合；支付最后。
- 用户要求加速并行；Root在基线`85e06c533c4141cea1aba28cca6b18c5e0ae9131`/全仓clean上同时启动Web W1C-2B-1唯一写入和BFF W1C-1J只读审查。两者仓库/文件/资源无重叠：Web只推进POST/CSRF与交互页的可运行切片，BFF只判断无hint退出是否确需owner修改；Root负责SQL单库阻断点只读盘点、任务卡、审查和提交。任何worker结论未经验收不计完成；当前浏览器登录、单库应用组合及其余11条broken边均未宣称闭环。
- W1C-1J BFF只读审查已完成：Better Auth在无hint且非导航时返回400，BFF/Web已转发`Accept`但不信浏览器可伪造`sec-fetch-*`。主路径由Web server-only `id_token_hint`完成，Root IAM→BFF真HTTP15/15已证实；无hint HTML确认留可选独立验收，不阻断2B/3，当前不改BFF。审查员因此切换为W1C-DB-BFF唯一writer，与Web 2B-1分仓并行；Root继续保留两仓Git/index/最终验证，BFF先完成三文档门再实施。Web当前无Redis依赖而2B-1要求跨实例一次性CSRF，Root只批准Web server-only精确`redis@5.12.1`、独立`KOKORO_WEB_REDIS_URL`和定点架构测试更新，不扩入Auth.js/Product Session或运维专项；真实验证待writer交付。
- Root并行只读盘点单库目标：Agent `src/kokoro_agent/infrastructure/{postgres,schema}.py`已默认`kokoro_agent`独立schema并只查该namespace；Scheduler `internal/adapters/postgres/bootstrap.go`按`current_schema()`查空表，可在显式owner search_path下复用，但其URL/启动是否强制固定schema仍待针对性验收。IAM `src/database/postgres-url.ts`与`scripts/apply-schema.ts`锁`public`并检查整个数据库；Capability `scripts/canonical-schema-state.ts`、Storage `scripts/apply-schema.ts`、Billing `scripts/canonical-schema.ts`锁`public`（Billing支付最后），System `scripts/apply-schema.ts`锁`public`；BFF旧installer亦锁`public`，现由唯一writer先改。以上只是代码扫描，不冒充统一单库真运行；后续各owner按依赖逐仓实施，不派多人并写同仓或扩成生产角色/部署项目。
- W1C-DB-BFF唯一writer按文档门完成29文件owner-schema实现，独立只读复审首轮1 P1/4 P2均已修正，最终0 P1/0 P2。Root在冻结工作树以Node22独立执行`pnpm format:check`、`pnpm check`（标准 **253/253**、contract **25/25**、architecture **27/27**、lint/typecheck/build）、带真实admin URL的`pnpm schema:check` **6/6无skip**，全部exit0；另用自建独占临时库先`db:apply-schema`再`test:integration` **37/37**，删除自有库，Redis DB8 **0→0**。canonical SQL/OpenAPI/package/lock字节未改；BFF `06a478403c92eeede0c54ed1f53022f0ff60d79e`已精确提交并推送main、子仓clean。Root gitlink/库存尚未集成，本片不代表IAM/System等owner已可同库运行；full persisted catalog drift仍待独立切片。
- Web W1C-2B-1首轮26文件候选的独立只读审查为**1 P1/2 P2/1 P3**：真实IAM continue 200 JSON被无JS表单直接展示、中间sign-in非200可能回传原始敏感body/cookie、两处Redis测试按可复用端口SCAN删除且cleanup无有限截止，CSRF digest未显式绑定POST。唯一Web writer已按TDD修复轮接手；Root未提交/放行Web，Node22与真实Next证据须在修复后独立重跑。CI/env/lock的server-only Redis必要扩围已写回W1C-2B-1任务卡。
- 为在Web修复期间保持独立并行，Root另派W1C-DB-IAM只读设计审查，定位IAM Prisma/fresh installer的`public`与整库空白假设；当前仅审查，未授权IAM源码写入，不建多role/多应用库。
- Web W1C-2B-1 27文件审查修复与302回归完成：原1 P1/2 P2均由独立只读复审确认关闭，剩余P3也以真实Next 302+多issuer Set-Cookie/恶意Location负例覆盖。Root在最终树用Node22独立`pnpm check`：contract **52/52**、architecture **32/32**、标准 **1297/1297**，lint/typecheck/build PASS；`pnpm test:e2e` **6/6**，Redis DB9 **0→0**。Root清理本次Playwright生成目录并恢复测试改写的`next-env.d.ts`，仅保留27文件业务变更；Web `d619f2c06951cb2decdb1eeac48547e3bcf40361`精确提交推送main、子仓clean。此切片只实现sign-in交互/一次性CSRF与安全续接，未实现Auth.js/Product Session、旧IAM直连删除或完整浏览器登录，Root gitlink/库存与真Web→BFF→IAM尚待集成。
- Root BFF新schema跨仓runner由独立脚本writer完成候选：五条runner仅BFF数据库URL改`schema=kokoro_bff`并清旧public options/PGOPTIONS，IAM session直接SQL改指`kokoro_bff`；其他owner URL不改。Root独立聚焦pytest **151 passed/56 subtests**、Ruff/py_compile/diff-check PASS。BFF固定SHA常量已改`06a4784…`但当前Root gitlink仍旧，真实五链待Root组合发布后复验，候选不能冒称release。
- IAM W1C-DB-IAM只读盘点定位17 Prisma model无owner schema、URL/PrismaPg/raw SQL与installer锁public/整库、readiness仅`SELECT 1`，提出同库coexist、IAM非空拒绝、DDL rollback、缺表ready四项真实门；未操作资源。随后唯一IAM文档writer仅改三设计文档，Root审查当前/目标边界和diff-check后提交推送IAM `d415ddbe565ec6c09e432945624e72c4b86d7a78` main，子仓当时clean；API wire不变。该SHA只是设计门，不证明实现；IAM唯一源码writer已按Root批准文件集进入TDD，Root gitlink尚未提升。
- IAM W1C-DB-IAM-C 38文件实现经独立只读审查首轮0 P0/P1、3 P2（pg_catalog顺序、测试资源cleanup、设计文档候选态）全部定点修正复核0 P0/P1/P2。Root独立Node24 `prisma:validate`、`pnpm verify` **704/704**与全format/lint/typecheck/contract/breaking/build通过，`VITEST_MAX_WORKERS=1 pnpm test:integration`真实PG/Redis **183/183**；自有`iam_*`库和Redis DB1均 **0→0**。默认并行integration的旧admission host全局临时库数量断言会与其他fixture竞态，此处串行不代表应用数据库不能并发；未改该旧fixture。IAM `6bc9b190c359b8109238626ff689ce9839e858b5`已精确提交推送main、子仓clean；Root gitlink仍待集成。
- Root另在一个自建独占临时PostgreSQL库、同一账号中先后真实运行BFF `db:apply-schema`与IAM `db:apply-schema`，最终`kokoro_bff` **16** 表、`kokoro_iam` **17** 表、`public` **0** 业务表、两owner物理FK **0**，两installer共存PASS且自有库已删除。首次用带Prisma专用`schema` query参数的URL直接调用`psql`被libpq拒绝，未触碰目标库；改用不带schema的同库观察URL后PASS。这是schema组合证据，不替代双服务真实HTTP/最终Root发布。
- BFF仅机械re-pin IAM `6bc9b19…` 来源commit，IAM allowlist与Better Auth snapshot blob digest保持`f63dacfa…`/`b2eac191…`；BFF policy JSON新digest为`ba1e63083b4b2ed0f3eb42308e632bc502cb4f07fcb99a2ea04586f7faa123ad`。Root独立Node22 `format:check`、`check`（contract **25/25**、标准 **253/253**、lint/typecheck/build）及真实admin URL的`schema:check` **6/6无skip**，BFF `a4dbc3339448c7ee8763b0f82d1c0ae4c213bf87`六文件精确提交推送main。Web snapshot与Root库存尚未向新来源提升，不能把owner提交直接当跨仓release。
- Web W1C-2B-2 首轮11文件候选经只读审查发现**1 P1**：issuer session cookie固定`Path=/iam`，浏览器在`/auth/select-tenant|consent`页面不会发送，模拟BFF未验session掩盖了真实断点。Root否决扩大issuer Path或Redis敏感cookie桥，批准Web-owned外层`/auth/*`精确GET安全跳转到静态`/iam/interactions/*`，由内层GET/POST自然接收原issuer cookie，CSRF绑定实际内层path；需真Next静态优先与遵守Cookie Path的CookieJar联测。唯一Web writer正修，候选未提交，不宣称Tenant/Consent或完整RP已闭环。
- 用户要求加速并行；Root保持Web唯一写入、另派独立Web审查与Root runner复审，同时只读调查下一片Auth.js RP。Web W1C-2B-2 初轮1 P1（issuer cookie `Path=/iam`）由静态内层route+Path-aware CookieJar修复；终审发现2 P2（删除cookie后CSRF绑定、Next自动HEAD/OPTIONS扩张），同一writer按真实Next RED→GREEN定点修复，最终独立复审 **0 P0/P1/P2**。Root独立Node22 `pnpm check`：contract **52/52**、architecture **32/32**、标准 **1320/1320**、lint/typecheck/build通过，`pnpm test:e2e` **6/6**；Root清理本次Playwright输出并恢复生成的`next-env.d.ts`。Web 17文件精确提交并推送main `14e23e602a5631009584d84f58871e51d32b821c`，子仓clean。BFF `a4dbc33…` policy与Web snapshot原字节digest同为`ba1e63083b4b2ed0f3eb42308e632bc502cb4f07fcb99a2ea04586f7faa123ad`。Web测试的BFF是严格HTTP fixture，真实IAM签名、Auth.js RP及Product Session仍未完成；最终callback保持受控503。
- Root跨仓BFF-schema runner独立审查当前候选 **0 P0/P1/P2**。Root自检发现 session runner曾将带`?schema=kokoro_bff`的应用URL传给`psql`，已改为原始无schema URL供libpq观测、BFF环境专用schema URL；新回归门防止混用。五runner及窄helper聚焦 **152 passed/56 subtests**、Ruff/diff-check通过；`consumer-inventory.json`的BFF 137项、IAM 3项、Web 9项来源现从各自已发布commit blob重算。Root gitlink/库存/脚本尚未提交，五条真实跨仓smoke及发布后main-only仍待复验；不把owner或fixture结果写成组合完成。
- Root组合提交 `20112fcbfa9f9d2f662ad70db33fa5a16ec83f30` 已将Web `14e23e6…`、BFF `a4dbc33…`、IAM `6bc9b19…`三个gitlink、149项库存commit-blob来源、BFF owner-schema五runner/窄helper/测试与CURRENT/task台账集成到main本地，尚未推送时运行固定来源policy、`w1b-iam` checkpoint与topology均PASS（9 runtime）。首次全Root pytest **568通过/1失败**：重写CURRENT时删掉治理测试要求的明确短语；补第一短语后仍缺`verification/`/精确治理短语而再次**568/1**，仅修文档说明，不放宽测试。最终 `test_repository_topology.py` **7/7**，全Root `scripts/tests` **569 passed/56 subtests passed**，`git diff --check`通过。原始兼容CLI按设计exit1，仅11个declared broken加1非法Web→IAM，无额外来源漂移；真实五链、main-only与最终推送仍待下步，不以这些静态门代签。
- 发布Root `a12c00b5822bb3346c1344267f3182add2b6c8c0` 后，`verify-main-only.py`确认Root+11个子仓本地/远端均仅main且clean；`verify-iam-relay-policy.py`、`w1b-iam`精确checkpoint、topology均PASS。固定新pin真实IAM准入→BFF **7/7**、首次OIDC Code+S256→BFF **15/15**、Capability→BFF **8/8**、System/BFF/Agent HTTP组合 **PASS**，各自BFF/IAM/其他owner commit=Root gitlink、资源清理报告零残留；Capability/Scheduler/System旧owner smoke的IAM身份仍为标注的固定wire stub，System未执行provider inference。Web真实Next fixture不等于三服务浏览器登录，当前callback仍503。
- 新pin Scheduler→BFF首次真实smoke红，Root用自有临时目录诊断为 `scheduler_bff_smoke_cases.py` 两条直接`psql` outbox查询仍默认public，BFF新schema为`kokoro_bff`；只将这两条SQL显式限定owner schema并加定点回归，不改Scheduler/应用DB配置。聚焦pytest **59/59**、Ruff通过；随后有一次无细节FAIL，诊断运行与再次正常CLI均 **11/11 PASS**，Go1.26.8/BFF `a4dbc33…`，自有DB/Redis/进程/临时文件报告已清。该一次不稳定已如实保留，未归因应用并发；无需扩到运维。改后Root全量`python3 -m pytest -q scripts/tests` **570 passed/56 subtests passed**，`git diff --check`通过；本定点修复尚待单独提交发布，发布后再核main-only/topology/门禁。
- Root定点修复已精确提交推送main `ba2e29019379fbc93aec093509953caec8cc5ee4`。发布后`verify-main-only.py` **12/12仓PASS**且本地/远端仅main/clean，policy、`w1b-iam` checkpoint、topology（9 runtime）均PASS；Scheduler真实smoke在最终提交上 **11/11 PASS**，确认自有资源清理。全仓静态治理`verify-ten-repository-standard.py --format json`仍exit1：**9仓/130 violations/0 unverified**，真实债务不假称清零。当前Web旧IAM直连非法边、11条broken与Auth.js/Product Session/全AG-UI/真实Agent与Storage能力仍属后续开发；Billing最后。
- W1C-2C 下一片由Web与IAM两名只读Agent并行核对，未改任何子仓/资源。IAM固定issuer=`<Web origin>/iam`、callback=`/api/auth/callback/kokoro-iam`、postlogout=`/auth/sign-in`，client为`user_delegated`/`client_secret_basic`/Code+S256，scope含`iam:session-authorization.verify`，resource=`https://kokoro.dev/resources/iam-internal`；真实token wire为Basic+form+唯一resource，userinfo仅GET Bearer且无issuer cookie。Web `next-auth`尚未安装；当前v4.24.15候选虽有Next16/React19 peer，但其authorization URL可能被浏览器query覆盖resource/scope/redirect_uri，自定义`token.request`仅返回TokenSet会跳过完整callback检查；下一代码片必须严格剥离外来参数并通过验证型`client.callback`完成state/nonce/ID token及受限exchangeBody，真实wire和一次性replay负例是放行门。建议放置在Web独立RP route/provider/transaction/backchannel文件，不塞旧`auth.ts`或browser `/iam` catch-all；Redis只存短TTL state摘要不存code/token/PII。Product Session未完成前RP不得生成可用session或泄露token，仍以受控未开通结束。此处是实施方案与待验约束，不是代码/真实Web三服务链完成证据。
- W1C-2C Web唯一writer在已通过三文档门的22文件范围内完成RP-only源码与真实Next+BFF严格fixture。独立审查先后发现EdDSA缺pin、chunked clone挂起、backchannel无绝对deadline/限额、取消未传播、预先abort永待等P1/P2，均经定点RED→GREEN后复审为 **0 P0/P1/P2**；最终冻结manifest `23976523744012a51ee76e2d336f1f799867406c90cbf02f0859d8ad87f583eb`。Root独立Node22 `pnpm check`：contract **52/52**、architecture **32/32**、标准 **1339/1339**，lint/typecheck/Next build均PASS；`pnpm test:e2e` **6/6**，清理Root自有Playwright产物并恢复生成的`next-env.d.ts`。Web `c71aa3f5130ae52c7f76356ac38bdabaf551d4e9`已精确22文件提交推送main、子仓clean。RP固定issuer/资源、验证型`openid-client` callback、EdDSA ID token、Redis state一次消费、server-only token Basic/userinfo Bearer/JWKS经BFF且5秒/1MiB/取消边界已在严格fixture实测；验证成功也只报受控 `503 product_session_unavailable`、无新可用session。fixture不是真实IAM签名组合，旧IAM直连、Product Session、refresh/logout、AG-UI仍待后续；不宣称登录闭环。
- W1C-2C Root将Web新gitlink和库存9处commit-blob来源同步到暂存区，BFF/IAM与16条edge语义不改。Root独立 `verify-iam-relay-policy.py`、`verify-contract-checkpoint.py --expected verification/contracts/checkpoints/w1b-iam.json`、`verify-repository-topology.py` 均PASS（9 runtime）；全 `python3 -m pytest -q scripts/tests` **570 passed / 56 subtests passed**。第一次在未暂存gitlink时checkpoint按已提交树仍读旧SHA而FAIL，精确暂存后PASS；不是业务回归。Root真实HTTPS Web→BFF→IAM测试由只读审查明确需要新增隔离Web入口，目前尚未执行；Root组合提交/发布后仍需main-only复验。下一任务W1C-2D按现有IAM/BFF隔离fixture增加真实签名Web回调，不扩成运维专项。
