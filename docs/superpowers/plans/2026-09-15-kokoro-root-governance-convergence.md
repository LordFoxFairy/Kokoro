# Kokoro Root Governance Convergence Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 使 Root 当前九仓规范入口、现状地图和有效任务计划一致，并修复两项过期手册测试，不触碰子仓或当前脏工作树。

**Architecture:** 本计划仅实施已审查的 [Root 规范收敛设计](../specs/2026-09-15-kokoro-root-governance-convergence-design.md)第 1 切片。先以 Root 治理测试固定“九仓当前态、Web 真实路径、Scheduler PostgreSQL owner、目标 apps 尚未实施”，再修正文档与现有唯一任务表；不执行 gitlink 搬迁、全仓 runner 或分支删除。

**Tech Stack:** Markdown、Python 3、pytest、Git；服务语言规范仍由 Root 三份专项手册负责。

---

## 基线、职责与文件地图

- Owner：Root `Kokoro`；规范入口与当前仓库地图由 Root 唯一写入。九个运行子仓各自是业务/contract/schema writer，均只读。
- 起始 commit：`4da98a39bf2c0502be143e6f809d0a5d381f2564`，分支 `codex/production-closure-governance`。实施前重新记录 HEAD/status；若基线变化，以实际值更新交接，不回退他人提交。
- 工作树排除：`docs/kokoro-handbook/standards/03-sql-and-postgresql.md`、Agent gitlink、`uv.lock`、`.tmp/`、`kokoro-mori-p1-arrangement-recording/` 和全部运行子仓；这些是任务外现存变化，禁止 stage、format、reset 或 checkout。
- 当前权威：`AGENTS.md` 与三份专项手册 → `docs/ARCHITECTURE_STANDARD.md` → `docs/REPOSITORY_STATUS.md`（活动仓/remote）→ `docs/CURRENT.md`（实际证据）→ `docs/CODEBASE_MAP.md`（导航）。前两级只读；不能为了让旧 map 正确而改高阶规则。
- 唯一任务表：`docs/superpowers/plans/2026-09-03-kokoro-production-closure.md`；本文件是第 1 切片的操作步骤，不建立第二份项目总任务状态。
- 在首次修改前运行 `python3 scripts/verify-ten-repository-standard.py --format json > /tmp/kokoro-standard-before-root-convergence.json`；当前预期 EXIT 1、`repository_count=9`、`violation_count=244`。另运行 `git rev-parse HEAD && git status --short` 并把实际 SHA/status 放入切片交接。before JSON 是本轮明细集合基线，不依赖历史报告的总数。

| 文件 | 本切片单一变化原因 |
|---|---|
| `scripts/tests/test_repository_topology.py` | Root 九仓/当前路径/owner 导航的正反断言 |
| `docs/CODEBASE_MAP.md` | 从当前仓库状态与已裁定架构派生的入口和存储地图 |
| `docs/REPOSITORY_STATUS.md` | 当前九仓/远端/仅 Agent gitlink 的事实索引 |
| `docs/CURRENT.md` | 当前验证范围与目标 Submodule 尚未完成的证据导航 |
| `README.md` | Root 与 Web 的五分钟路径区分及目标链接 |
| `docs/superpowers/plans/2026-09-03-kokoro-production-closure.md` | 把仍活跃的“十仓”总任务表对齐为九仓，不删历史工作 |
| `scripts/tests/test_engineering_handbooks.py` | 手册示例/来源的当前语义测试，不固定失效数量与标题 |

## Chunk 1: 当前仓库事实与导航

### Task 1: 测试先行冻结九仓与 Scheduler 数据 owner

**Files:**
- Modify: `scripts/tests/test_repository_topology.py`
- Read: `AGENTS.md`, `docs/REPOSITORY_STATUS.md`, `docs/CODEBASE_MAP.md`, `docs/ARCHITECTURE_STANDARD.md`

- [ ] **Step 1: 写两个当前事实测试**

在 `scripts/tests/test_repository_topology.py` 追加：

```python
def test_codebase_map_does_not_replace_scheduler_postgres_truth() -> None:
    root = Path(__file__).resolve().parents[2]
    map_text = (root / "docs/CODEBASE_MAP.md").read_text()
    scheduler_row = next(
        line for line in map_text.splitlines() if line.startswith("| `kokoro-scheduler` |")
    )
    assert "PostgreSQL" in scheduler_row
    assert "no business DB" not in scheduler_row


def test_current_web_path_is_not_claimed_as_an_apps_gitlink() -> None:
    root = Path(__file__).resolve().parents[2]
    status = (root / "docs/REPOSITORY_STATUS.md").read_text()
    gitmodules = (root / ".gitmodules").read_text()
    assert "| kokoro | LordFoxFairy/kokoro-app |" in status
    assert "path = kokoro-agent" in gitmodules
    assert "path = apps/kokoro" not in gitmodules
```

- [ ] **Step 2: 运行测试记录 RED/GREEN 基线**

Run: `python3 -m pytest scripts/tests/test_repository_topology.py -q`
Expected: Scheduler 测试先因旧 `no business DB` 描述 FAIL；Web 现状测试 PASS。不得改高阶 `AGENTS.md` 让旧 map 测试通过。

- [ ] **Step 3: 修正地图，不迁移路径**

把 `docs/CODEBASE_MAP.md` 的 Scheduler 存储边界改为“PostgreSQL 保存 Schedule/Occurrence/Receipt/Outbox 权威事实；Redis 仅协调 lease/通知/缓存”，明确当前九仓中只有 Agent gitlink，未来 `apps/` 属目标。检查文件工作规则中的 Stage 2 mock 与暂停 full runner 不被写成完整系统 E2E。

- [ ] **Step 4: 运行针对性测试**

Run: `python3 -m pytest scripts/tests/test_repository_topology.py -q`
Expected: 全 PASS。

- [ ] **Step 5: 提交一个当前事实切片**

```bash
git diff -- scripts/tests/test_repository_topology.py docs/CODEBASE_MAP.md
git add -- scripts/tests/test_repository_topology.py docs/CODEBASE_MAP.md
git diff --cached --check
git diff --cached --name-only
git commit -m "docs(governance): align current map with scheduler owner"
```

Staged path 必须恰好两个；Root 主 Agent 在主工作树重跑 Step 4，worker 报告不代替结果。

### Task 2: 校准 Root 当前事实入口

**Files:**
- Modify: `docs/REPOSITORY_STATUS.md`, `docs/CURRENT.md`, `README.md`, `scripts/tests/test_repository_topology.py`
- Read: `docs/CODEBASE_MAP.md`, `docs/ARCHITECTURE_STANDARD.md`

- [ ] **Step 1: 写失败的入口断言**

在 `scripts/tests/test_repository_topology.py` 增加：

```python
def test_root_current_marks_apps_and_full_gate_as_unfinished() -> None:
    root = Path(__file__).resolve().parents[2]
    current = (root / "docs/CURRENT.md").read_text()
    assert "`apps/` 尚未实施" in current
    assert "`scripts/verify-ten-repository-full.sh` 仍暂停" in current


def test_repository_status_keeps_exact_nine_current_paths() -> None:
    root = Path(__file__).resolve().parents[2]
    status = (root / "docs/REPOSITORY_STATUS.md").read_text()
    table = status.split("## 正式仓库与 GitHub 映射", 1)[1].split("## 归属裁决", 1)[0]
    rows = [line for line in table.splitlines() if line.startswith("| kokoro")]
    assert len(rows) == 9
    assert "仅 Agent 是 Root gitlink" in status
```

第一项是当前 `CURRENT.md` 实际缺失的目标态标注，是真实 RED；第二项验证已正确的事实，不制造假失败。

- [ ] **Step 2: 执行 RED 并记录具体失配**

Run: `python3 -m pytest scripts/tests/test_repository_topology.py -q`
Expected: `test_root_current_marks_apps_and_full_gate_as_unfinished` 因当前 `CURRENT.md` 没有 `apps/` 目标态标注 FAIL；九仓表测试 PASS。

- [ ] **Step 3: 只更新当前态/目标态与证据导航**

`docs/REPOSITORY_STATUS.md` 继续作为九仓和远端唯一索引，明确 `kokoro` 当前在 Root 同目录且非 gitlink；`docs/CURRENT.md` 增加精确短句“`apps/` 尚未实施”和“`scripts/verify-ten-repository-full.sh` 仍暂停”，并记录本轮可复核基线：Root 仅 Agent gitlink、full runner EXIT 2、拓扑静态 PASS、手册测试基线 82 PASS/2 FAIL、九仓标准审计 244 现有违规；目标全九仓 Submodule/组合 CI 标待验。`README.md` 五分钟入口先写当前真实目录，再链接目标规格。不要以这轮 read-only baseline 覆盖先前已验的 System owner commit 或编造新 live smoke。

- [ ] **Step 4: 运行入口测试和 diff 检查**

Run: `python3 -m pytest scripts/tests/test_repository_topology.py -q && git diff --check`
Expected: 全 PASS，diff 无空白错误。

- [ ] **Step 5: 提交导航切片**

```bash
git add -- scripts/tests/test_repository_topology.py docs/REPOSITORY_STATUS.md docs/CURRENT.md README.md
git diff --cached --name-only
git diff --cached --check
git commit -m "docs(governance): distinguish current workspace from submodule target"
```

仅 stage 本任务四个路径，不暂存任务外 SQL 手册、Gitlink 或子仓修改。

## Chunk 2: 有效计划与规范测试收尾

### Task 3: 活跃总计划从十仓收敛到九仓

**Files:**
- Modify: `docs/superpowers/plans/2026-09-03-kokoro-production-closure.md`
- Test: `scripts/tests/test_repository_topology.py`

- [ ] **Step 1: 写计划断言**

在 `scripts/tests/test_repository_topology.py` 顶部增加 `import re`，并追加：

```python
def test_active_production_plan_lists_exact_nine_runtime_repositories() -> None:
    root = Path(__file__).resolve().parents[2]
    plan = (root / "docs/superpowers/plans/2026-09-03-kokoro-production-closure.md").read_text()
    scope = plan.split("## 1. 范围与完成定义", 1)[1].split("## 2. 固定架构裁决", 1)[0]
    repositories = re.findall(r"(?m)^\d+\. `([^`]+)`", scope)
    assert repositories == [
        "kokoro", "kokoro-bff", "kokoro-agent", "kokoro-iam", "kokoro-system",
        "kokoro-billing", "kokoro-capability", "kokoro-storage", "kokoro-scheduler",
    ]
    assert "model-catalog" in plan
```

仅解析有效计划首节的编号运行仓；第十个 `kokoro-model` 使当前测试真实 FAIL，目标九仓则 PASS。

- [ ] **Step 2: 执行 RED**

Run: `python3 -m pytest scripts/tests/test_repository_topology.py -q`
Expected: 当前计划首节列 `kokoro-model` 为第十仓，新增测试 FAIL。

- [ ] **Step 3: 更新原有唯一任务表**

把计划标题/总目标/正式运行仓/调用图/Wave 0、1、3、6 的现行“十仓”描述对齐为九仓；Model 的历史工作放入 System `model-catalog` 已裁定收敛语境，Capability→Platform 明确当前物理仓与目标名。现有未完成任务不机械标完成，原有任务 ID 与验证风险保留；本切片、Gitlink cutover、隔离全仓编排与 main 收尾各自成为该总计划下明确后续门，不写“全部已验”。

- [ ] **Step 4: 运行计划测试**

Run: `python3 -m pytest scripts/tests/test_repository_topology.py -q`
Expected: 全 PASS。

- [ ] **Step 5: 提交唯一任务表更新**

```bash
git add -- scripts/tests/test_repository_topology.py docs/superpowers/plans/2026-09-03-kokoro-production-closure.md
git diff --cached --check
git diff --cached --name-only
git commit -m "docs(governance): scope active production plan to nine owners"
```

### Task 4: 修复两项失效的手册测试

**Files:**
- Modify: `scripts/tests/test_engineering_handbooks.py`
- Read only: `docs/kokoro-handbook/standards/03-sql-and-postgresql.md`, `08-typescript-backend-engineering.md`, `09-python-backend-engineering.md`, `scripts/governance/handbook_examples.py`

- [ ] **Step 1: 固定真实现行手册语义**

在 `scripts/tests/test_engineering_handbooks.py` 中把过期 `assert len(paths) == 18` 替换成：

```python
assert paths
assert len(paths) == len({path.resolve() for path in paths})
for required in (
    "typescript/tsconfig.json",
    "typescript/package.json",
    "python/src/kokoro_agent/settings.py",
    "python/src/kokoro_agent/runs/models.py",
    "python/src/kokoro_agent/runs/rows.py",
    "python/src/kokoro_agent/runs/schemas.py",
    "python/src/kokoro_agent/runs/service.py",
    "python/pyproject.toml",
    "schema.sql",
):
    assert (tmp_path / required).is_file(), required
```

保留现有对全部返回路径的 Python/JSON/TOML parse 循环、空输出目录拒绝测试。把来源章节断言替换成：

```python
assert re.search(r"^## 17\. (?:参考依据|真实来源与核验记录)$", text, re.MULTILINE)
```

继续要求 `https://`、平衡 code fence 与 Root `AGENTS.md` 不复制 TS/Python/SQL 示例；不得编辑 dirty SQL 手册让旧测试通过。当前 `extract_examples` 实际写出 11 个文件，TypeScript 手册不再含 `// src/...` 的独立可抽取 `.ts` 示例，故旧 `typescript/src/app.ts` 和 `typescript/src/modules/sites/site.ts` 是过时必需项；真正的生成物为 TypeScript 工具配置、Python 业务对象/服务/配置以及 SQL 样本。完整生成物语义比固定 18 个数更稳定；未来若重新加入可抽取 TS 示例，应在对应切片增加断言。

- [ ] **Step 2: 单测 RED/GREEN 对照**

Run before: `python3 -m pytest scripts/tests/test_engineering_handbooks.py -q`
Expected baseline: 2 FAIL；修改后同命令全 PASS。若仍失败，查具体来源/示例而不是进一步降低断言。

- [ ] **Step 3: 提交测试修正**

```bash
git add -- scripts/tests/test_engineering_handbooks.py
git diff --cached --check
git diff --cached --name-only
git commit -m "test(governance): assert current handbook evidence semantics"
```

### Task 5: Root 主工作树集成验收与交接

**Files:**
- Inspect only: 本计划允许文件、`git status --short`、标准审计 JSON
- Modify: `docs/superpowers/plans/2026-09-03-kokoro-production-closure.md` 的本切片任务状态（仅实际通过后）

- [ ] **Step 1: 在最后一个提交 HEAD 重新执行**

```bash
python3 scripts/verify-repository-topology.py
python3 -m pytest scripts/tests -q
python3 scripts/verify-ten-repository-standard.py --format json > /tmp/kokoro-standard-after-root-convergence.json
git diff --check
git status --short
```

before 命令必须在 Task 1 修改前执行，Task 5 不得覆盖它。Expected: topology PASS、`scripts/tests` 全 PASS；标准审计仍可能 EXIT 1，但须覆盖九仓。运行：

```bash
python3 - <<'PY'
import json
from collections import Counter
from pathlib import Path
before = json.loads(Path('/tmp/kokoro-standard-before-root-convergence.json').read_text())
after = json.loads(Path('/tmp/kokoro-standard-after-root-convergence.json').read_text())
keys = lambda document: {
    (item['repository'], item['rule'], item['detail'])
    for item in document['violations']
}
added = keys(after) - keys(before)
assert before['repository_count'] == after['repository_count'] == 9
assert not added, sorted(added)
print('remaining=', after['violation_count'])
print('by_repo=', dict(Counter(item['repository'] for item in after['violations'])))
PY
```

`git status` 中任务外 dirty 保留，不宣称 clean checkout。两个 JSON 都写 `/tmp` 而非 Root 仓。

- [ ] **Step 2: 只在实际达标后更新原计划状态并提交**

```bash
git add -- docs/superpowers/plans/2026-09-03-kokoro-production-closure.md
git diff --cached --check
git commit -m "docs(governance): record root convergence verification"
```

完成报告列出每个切片 SHA、主工作树实际命令、PASS/FAIL、标准审计未闭环数量、现存未提交变化和后续 owner。下一独立设计/计划是九仓 gitlink 与 `apps/` 拓扑 cutover；逐仓 main 集成与本地/远端分支清理必须在该仓所有待保留提交和未提交修改已交接后实施。

- [ ] **Step 3: 状态记录提交后在最终 HEAD 无条件复验**

```bash
git rev-parse HEAD
python3 scripts/verify-repository-topology.py
python3 -m pytest scripts/tests -q
python3 scripts/verify-ten-repository-standard.py --format json > /tmp/kokoro-standard-final-root-convergence.json
git diff --check
python3 - <<'PY'
import json
from pathlib import Path
before = json.loads(Path('/tmp/kokoro-standard-before-root-convergence.json').read_text())
final = json.loads(Path('/tmp/kokoro-standard-final-root-convergence.json').read_text())
keys = lambda document: {
    (item['repository'], item['rule'], item['detail'])
    for item in document['violations']
}
assert before['repository_count'] == final['repository_count'] == 9
assert not (keys(final) - keys(before)), sorted(keys(final) - keys(before))
print('final_violation_count=', final['violation_count'])
PY
```

Expected: 输出最终状态提交 SHA；topology 与 tests 全 PASS。标准审计因既有子仓缺口可预期 EXIT 1，但 JSON 必须可解析、覆盖九仓且相对 before 明细没有本切片新增违规；不能凭主观判断省略最终 HEAD 复验。
