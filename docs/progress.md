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
