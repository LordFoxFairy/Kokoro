# Kokoro Wave 0A Governance and Contract Gates Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立无歧义的 Root 治理基线和可机器验证的全调用矩阵 contract pin/digest/inventory，为 W0B 逐条修复断链提供可复现的红门。

**Architecture:** Root 只保存跨仓组合元数据和校验器，不复制 owner 的可编辑 contract。机器清单绑定 owner gitlink、canonical contract blob、contract version、generator/runtime version，以及来自冻结 repository commit blob 的运行证据；所有当前断链和非法旁路都显式报错，不提供跳过参数。

**Tech Stack:** Python 3.13、pytest、Git submodules、JSON manifest、SHA-256、Markdown。

## Global Constraints

- 本计划只修改 Root 治理、验证脚本和只读组合清单；不修改任何子仓运行代码、contract 或 Schema。
- 当前身份必须写作 `kokoro-capability`；`kokoro-platform` 只表示 Wave 3 目标态。
- 本地/CI 共用一个 PostgreSQL 实例和一套应用 role/credential；每个 owner 使用独立 database/schema。
- Root 不维护可编辑 OpenAPI/Proto 副本，不共享 ORM schema、SQL、业务 DTO 或 generated client。
- 一个任务只有一个写入 Agent；Root 不抢写已派出的文件，并负责独立审查、验证、精确提交和推送。
- 所有任务状态同步到 `docs/task.md`；实际 commit、命令和审查证据只追加到 `docs/progress.md`。
- Compatibility CLI 在任一 `broken` edge、非法旁路、SHA/digest/evidence 漂移时 exit 1；没有 allow/ignore 参数。

---

## File map

| 文件                                                      | 单一职责                                                      |
| --------------------------------------------------------- | ------------------------------------------------------------- |
| `AGENTS.md`                                               | 跨仓 owner、执行流程和本地/CI 数据库裁决。                    |
| `docs/ARCHITECTURE_STANDARD.md`                           | 当前协议矩阵、数据隔离与 Platform 目标态。                    |
| `docs/kokoro-handbook/standards/03-sql-and-postgresql.md` | PostgreSQL/SQL 唯一规范；区分逻辑 owner 隔离与部署凭据隔离。  |
| `docs/CURRENT.md`                                         | 当前组合事实、正在执行的 Wave 与诚实门禁结果。                |
| `verification/contracts/consumer-inventory.json`          | 全批准调用矩阵和非法旁路的机器清单；不含 contract 内容副本。  |
| `verification/contracts/README.md`                        | 清单字段、状态语义、更新流程和运行命令。                      |
| `scripts/governance/contract_inventory.py`                | 可导入的 manifest/git-blob 校验逻辑。                         |
| `scripts/verify-contract-compatibility.py`                | 稳定 CLI 入口。                                               |
| `scripts/tests/test_contract_compatibility.py`            | git blob、schema、pin、digest、evidence、状态和旁路负向测试。 |
| `scripts/INDEX.md`                                        | 暴露新的 Root compatibility 门。                              |
| `docs/task.md`                                            | 当前任务状态、依赖和 owner。                                  |
| `docs/progress.md`                                        | 冻结 SHA、命令输出、审查和风险的追加证据。                    |

## Task 1: Align governance decisions

**Files:**

- Modify: `AGENTS.md`
- Modify: `docs/ARCHITECTURE_STANDARD.md`
- Modify: `docs/kokoro-handbook/standards/03-sql-and-postgresql.md`
- Modify: `docs/CURRENT.md`
- Test: `scripts/tests/test_engineering_handbooks.py`

**Interfaces:**

- Consumes: `docs/superpowers/specs/2026-09-20-kokoro-backend-closure-design.md` 第 1、3、4、6、8 节。
- Produces: 后续任务读取的唯一数据库部署裁决和协议矩阵；不产生运行时 API。

- [ ] **Step 1: 写入失败的治理断言**

在 `scripts/tests/test_engineering_handbooks.py` 使用该文件已导入的 `ROOT`，新增以下测试；不要添加不存在的 pytest fixture：

```python
def test_local_ci_database_identity_and_owner_isolation_are_not_conflated() -> None:
    agents = (ROOT / "AGENTS.md").read_text()
    architecture = (ROOT / "docs/ARCHITECTURE_STANDARD.md").read_text()
    sql = (ROOT / "docs/kokoro-handbook/standards/03-sql-and-postgresql.md").read_text()
    for content in (agents, architecture, sql):
        assert "一个 PostgreSQL 实例" in content
        assert "一套应用 role/credential" in content
        assert "独立 database/schema" in content
        assert "跨 owner SQL" in content
    assert "部署阶段" in agents
    assert "kokoro-capability" in architecture
    assert "kokoro-platform" in architecture
```

- [ ] **Step 2: 运行测试并确认旧表述失败**

Run: `python3 -m pytest scripts/tests/test_engineering_handbooks.py -q`

Expected: 新测试因现有“每 owner 独立凭据”表述失败；既有测试结果保持可见。

- [ ] **Step 3: 最小化修改三份权威规则**

三份文件统一使用以下裁决，不保留冲突句：

```text
本地与 CI 复用一个 PostgreSQL 实例和一套应用 role/credential；每个数据 owner 仍使用独立 database/schema 与独立连接 URL。代码、Schema、查询、事务和测试继续禁止跨 owner SQL/JOIN、表引用、ORM model 与 canonical schema 共享。每 owner 独立 production role、GRANT/REVOKE、数据库 mTLS 和 NetworkPolicy 属于部署阶段，不是当前闭环门禁。
```

`docs/ARCHITECTURE_STANDARD.md` 同步唯一协议矩阵：

```text
Browser→Web: same-origin HTTP
Web→BFF: HTTP/OpenAPI + AG-UI/SSE
BFF→IAM/System/Agent/Scheduler/Billing: owner HTTP/OpenAPI generated client
BFF/Agent→Platform: ConnectRPC/Proto
BFF/Agent/Platform→Storage: ConnectRPC/Proto v2
Scheduler→BFF/Agent: versioned HTTP event protocol
```

同时写明：当前物理身份是 `kokoro-capability`；只有 remote/path/package/service/env/Proto/数据库/Redis/consumer 在 Wave 3 同一窗口完成切换并通过门禁后，才改称 `kokoro-platform`。

- [ ] **Step 4: 更新 CURRENT 的当前执行事实**

链接 `task.md`、`progress.md`、批准设计和本计划；记录 W0A 正在执行，不把 compatibility 红门或 110 项静态违规写成通过。

- [ ] **Step 5: 运行治理测试**

```bash
python3 -m pytest scripts/tests/test_engineering_handbooks.py -q
python3 scripts/verify-repository-topology.py
```

Expected: 两条命令 exit 0；子 Agent 在任务报告中记录实际通过数，由 Task 4 统一追加到 `docs/progress.md`。

- [ ] **Step 6: 子 Agent 交付，Root 审查后精确提交**

```bash
git add AGENTS.md docs/ARCHITECTURE_STANDARD.md \
  docs/kokoro-handbook/standards/03-sql-and-postgresql.md \
  docs/CURRENT.md scripts/tests/test_engineering_handbooks.py
git commit -m "docs(architecture): align database and protocol authority"
```

## Task 2: Implement the git-blob compatibility verifier

**Files:**

- Create: `scripts/governance/contract_inventory.py`
- Create: `scripts/verify-contract-compatibility.py`
- Create: `scripts/tests/test_contract_compatibility.py`

**Interfaces:**

- Consumes: Root git index、submodule commit blobs 和 schema version 1 JSON。
- Produces: `verify_inventory(root: Path, inventory_path: Path) -> list[str]`；返回排序错误列表。CLI 成功输出 JSON `{"status":"PASS","edge_count":16,"violation_count":0}`，失败输出 `status=FAIL` 与 `errors` 并 exit 1。

- [ ] **Step 1: 写 git blob 与 manifest 失败测试**

测试通过 `importlib.util.spec_from_file_location` 导入 `scripts/governance/contract_inventory.py`。在 `tmp_path` 创建 Root、`apps/owner`、`apps/consumer` 三个 Git 仓；每仓设置本地 user、提交固定 contract/evidence，再用下方 helper 中的字面 `git update-index --add --cacheinfo` 调用把 child commit 登记为 Root gitlink。

测试 helper 使用以下完整结构；`run` 对非零退出码使用 `check=True`，因此 fixture 创建失败不会伪装成断言失败：

```python
import copy
import importlib.util
import json
import subprocess
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from types import ModuleType

import pytest

from scripts.governance.handbook_examples import ROOT


@dataclass
class InventoryFixture:
    module: ModuleType
    root: Path
    manifest_path: Path
    data: dict[str, object]

    def write(self) -> None:
        self.manifest_path.write_text(json.dumps(self.data, indent=2) + "\n")

    def verify(self) -> list[str]:
        self.write()
        return self.module.verify_inventory(self.root, self.manifest_path)


def run(cwd: Path, *args: str) -> str:
    return subprocess.run(
        args, cwd=cwd, text=True, capture_output=True, check=True
    ).stdout.strip()


def commit_child(root: Path, name: str, files: dict[str, bytes]) -> str:
    repository = root / "apps" / name
    repository.mkdir(parents=True)
    run(repository, "git", "init")
    run(repository, "git", "config", "user.email", "tests@kokoro.local")
    run(repository, "git", "config", "user.name", "Kokoro Tests")
    for relative, content in files.items():
        path = repository / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    run(repository, "git", "add", *files)
    run(repository, "git", "commit", "-m", f"test: add {name} fixture")
    return run(repository, "git", "rev-parse", "HEAD")


@pytest.fixture()
def fixture(tmp_path: Path) -> InventoryFixture:
    root = tmp_path / "root"
    root.mkdir()
    run(root, "git", "init")
    run(root, "git", "config", "user.email", "tests@kokoro.local")
    run(root, "git", "config", "user.name", "Kokoro Tests")
    owner_contract = b'{"openapi":"3.1.0"}\n'
    consumer_source = b'export const ownerVersion = "v1";\n'
    consumer_package = (
        b'{"dependencies":{"undici":"7.16.0"},'
        b'"devDependencies":{"openapi-typescript":"7.10.1"}}\n'
    )
    owner_sha = commit_child(
        root, "owner", {"contract/openapi.json": owner_contract}
    )
    consumer_sha = commit_child(
        root,
        "consumer",
        {"src/client.ts": consumer_source, "package.json": consumer_package},
    )
    run(
        root, "git", "update-index", "--add", "--cacheinfo",
        "160000", owner_sha, "apps/owner",
    )
    run(
        root, "git", "update-index", "--add", "--cacheinfo",
        "160000", consumer_sha, "apps/consumer",
    )
    module_path = ROOT / "scripts/governance/contract_inventory.py"
    spec = importlib.util.spec_from_file_location("contract_inventory", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.EXPECTED_EDGE_IDS = frozenset({"EDGE-CONSUMER-OWNER"})
    module.EXPECTED_VIOLATION_IDS = frozenset()
    manifest_path = root / "inventory.json"
    data = {
        "schema_version": 1,
        "edges": [{
            "id": "EDGE-CONSUMER-OWNER",
            "caller": "consumer",
            "owner": {
                "name": "owner",
                "repository_path": "apps/owner",
                "repository_commit": owner_sha,
                "contract_version": "v1",
                "contract_path": "contract/openapi.json",
                "contract_sha256": sha256(owner_contract).hexdigest(),
            },
            "protocol": "http-openapi",
            "code_generator_version": "openapi-typescript@7.10.1",
            "runtime_package_version": "undici@7.16.0",
            "state": "active",
            "reason": "Generated client calls the owner v1 contract.",
            "evidence": [{
                "repository_path": "apps/consumer",
                "repository_commit": consumer_sha,
                "path": "src/client.ts",
                "sha256": sha256(consumer_source).hexdigest(),
            }],
            "version_assertions": [
                {
                    "field": "code_generator_version",
                    "declared_value": "openapi-typescript@7.10.1",
                    "repository_path": "apps/consumer",
                    "repository_commit": consumer_sha,
                    "path": "package.json",
                    "sha256": sha256(consumer_package).hexdigest(),
                    "json_checks": [{
                        "pointer": "/devDependencies/openapi-typescript",
                        "expected": "7.10.1",
                    }],
                },
                {
                    "field": "runtime_package_version",
                    "declared_value": "undici@7.16.0",
                    "repository_path": "apps/consumer",
                    "repository_commit": consumer_sha,
                    "path": "package.json",
                    "sha256": sha256(consumer_package).hexdigest(),
                    "json_checks": [{
                        "pointer": "/dependencies/undici",
                        "expected": "7.16.0",
                    }],
                },
            ],
        }],
        "violations": [],
    }
    fixture = InventoryFixture(module, root, manifest_path, data)
    fixture.write()
    return fixture
```

新增并实现以下测试；每个 mutation 后把 JSON 写入 fixture manifest，再调用 `verify_inventory`：

```python
def test_matching_gitlink_blobs_and_active_edge_return_no_errors(fixture) -> None:
    assert fixture.module.verify_inventory(fixture.root, fixture.manifest_path) == []


def test_owner_commit_drift_is_reported(fixture) -> None:
    fixture.data["edges"][0]["owner"]["repository_commit"] = "0" * 40
    fixture.write()
    assert any("owner gitlink" in error for error in fixture.verify())


def test_contract_digest_uses_commit_blob_not_dirty_worktree(fixture) -> None:
    (fixture.root / "apps/owner/contract/openapi.json").write_text("dirty")
    assert fixture.verify() == []


def test_contract_digest_drift_is_reported(fixture) -> None:
    fixture.data["edges"][0]["owner"]["contract_sha256"] = "0" * 64
    fixture.write()
    assert any("contract_sha256" in error for error in fixture.verify())


def test_evidence_digest_drift_is_reported(fixture) -> None:
    fixture.data["edges"][0]["evidence"][0]["sha256"] = "0" * 64
    fixture.write()
    assert any("evidence sha256" in error for error in fixture.verify())


def test_broken_edge_and_illegal_bypass_are_reported(fixture) -> None:
    fixture.data["edges"][0]["state"] = "broken"
    fixture.data["violations"] = [{
        "id": "EDGE-ILLEGAL",
        "caller": "web",
        "target": "iam",
        "reason": "Web bypasses BFF.",
        "evidence": fixture.data["edges"][0]["evidence"],
    }]
    fixture.write()
    errors = fixture.verify()
    assert any("declared broken" in error for error in errors)
    assert any("illegal edge" in error for error in errors)


def test_duplicate_id_is_rejected(fixture) -> None:
    fixture.data["edges"].append(copy.deepcopy(fixture.data["edges"][0]))
    assert any("duplicate id" in error for error in fixture.verify())


@pytest.mark.parametrize(("field", "value"), [("protocol", "grpc"), ("state", "ready")])
def test_unknown_enum_is_rejected(fixture, field: str, value: str) -> None:
    fixture.data["edges"][0][field] = value
    assert any(field in error for error in fixture.verify())


def test_unmanaged_active_edge_is_rejected(fixture) -> None:
    fixture.data["edges"][0]["code_generator_version"] = "unmanaged"
    assert any("unmanaged" in error for error in fixture.verify())


def test_version_value_must_match_frozen_package_json(fixture) -> None:
    checks = fixture.data["edges"][0]["version_assertions"][1]["json_checks"]
    checks[0]["expected"] = "9.0.0"
    assert any("'7.16.0' != '9.0.0'" in error for error in fixture.verify())


def test_top_level_version_pin_must_match_assertion_declared_value(fixture) -> None:
    fixture.data["edges"][0]["runtime_package_version"] = "undici@999.0.0"
    assert any("declared version" in error for error in fixture.verify())


def test_required_topology_ids_cannot_be_removed(fixture) -> None:
    fixture.module.EXPECTED_EDGE_IDS = frozenset({"EDGE-CONSUMER-OWNER"})
    fixture.data["edges"] = []
    assert any("missing edge ids" in error for error in fixture.verify())


def test_required_violation_id_cannot_be_removed(fixture) -> None:
    fixture.module.EXPECTED_VIOLATION_IDS = frozenset({"EDGE-REQUIRED"})
    assert any("missing violation ids" in error for error in fixture.verify())


def test_unapproved_violation_id_is_rejected(fixture) -> None:
    fixture.data["violations"] = [{
        "id": "EDGE-UNAPPROVED",
        "caller": "web",
        "target": "iam",
        "reason": "Unapproved bypass.",
        "evidence": fixture.data["edges"][0]["evidence"],
    }]
    assert any("unexpected violation ids" in error for error in fixture.verify())


def test_path_escape_is_rejected(fixture) -> None:
    owner = fixture.data["edges"][0]["owner"]
    fixture.data["edges"][0]["owner"] = dict(owner, contract_path="../secret")
    assert any("safe relative path" in error for error in fixture.verify())
```

- [ ] **Step 2: 运行测试并确认模块尚不存在**

Run: `python3 -m pytest scripts/tests/test_contract_compatibility.py -q`

Expected: collection/import 失败，因为实现模块尚未创建。

- [ ] **Step 3: 实现 schema 与 commit-blob 校验器**

`contract_inventory.py` 使用以下完整最小实现；仅错误文案可在不改变测试 fragment 的前提下整理：

```python
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path, PurePosixPath
from typing import Any

PROTOCOLS = frozenset({"same-origin-http", "http-openapi", "connect-proto", "http-event"})
STATES = frozenset({"active", "broken"})
EXPECTED_EDGE_IDS = frozenset({
    "EDGE-BROWSER-WEB",
    "EDGE-WEB-BFF",
    "EDGE-BFF-IAM",
    "EDGE-BFF-SYSTEM",
    "EDGE-BFF-CAPABILITY",
    "EDGE-BFF-STORAGE",
    "EDGE-BFF-AGENT",
    "EDGE-BFF-SCHEDULER",
    "EDGE-BFF-BILLING",
    "EDGE-AGENT-SYSTEM",
    "EDGE-AGENT-CAPABILITY",
    "EDGE-AGENT-STORAGE",
    "EDGE-CAPABILITY-STORAGE",
    "EDGE-CAPABILITY-IAM",
    "EDGE-SCHEDULER-BFF",
    "EDGE-SCHEDULER-AGENT",
})
EXPECTED_VIOLATION_IDS = frozenset({"EDGE-WEB-IAM-DIRECT"})


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def safe_relative_path(value: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or ".." in path.parts:
        raise ValueError(f"not a safe relative path: {value}")
    return path


def gitlink_sha(root: Path, repository_path: str) -> str:
    path = safe_relative_path(repository_path).as_posix()
    result = subprocess.run(
        ["git", "ls-files", "--stage", "--", path],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    fields = result.stdout.split()
    if result.returncode or len(fields) < 2 or fields[0] != "160000":
        raise ValueError(f"{path}: not a Root gitlink")
    return fields[1]


def git_blob(root: Path, repository_path: str, commit: str, relative_path: str) -> bytes:
    repository = root / safe_relative_path(repository_path)
    relative = safe_relative_path(relative_path).as_posix()
    result = subprocess.run(
        ["git", "show", f"{commit}:{relative}"],
        cwd=repository,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        raise ValueError(f"{repository_path}@{commit}:{relative}: missing commit blob")
    return result.stdout


def load_inventory(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError("inventory must be an object")
    if value.get("schema_version") != 1:
        raise ValueError("schema_version must equal 1")
    for field in ("edges", "violations"):
        if not isinstance(value.get(field), list):
            raise ValueError(f"{field} must be a list")
    return value


def _text(record: dict[str, Any], field: str, label: str, errors: list[str]) -> str:
    value = record.get(field)
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{label}: {field} must be non-empty text")
        return ""
    return value


def _verify_blob_reference(
    root: Path,
    label: str,
    reference: dict[str, Any],
    errors: list[str],
) -> bytes | None:
    repository_path = _text(reference, "repository_path", label, errors)
    repository_commit = _text(reference, "repository_commit", label, errors)
    relative_path = _text(reference, "path", label, errors)
    digest = _text(reference, "sha256", label, errors)
    if not all((repository_path, repository_commit, relative_path, digest)):
        return None
    try:
        actual_gitlink = gitlink_sha(root, repository_path)
        if actual_gitlink != repository_commit:
            errors.append(
                f"{label}: evidence gitlink {actual_gitlink} != {repository_commit}"
            )
        blob = git_blob(root, repository_path, repository_commit, relative_path)
    except ValueError as error:
        errors.append(f"{label}: {error}")
        return None
    actual_digest = sha256_bytes(blob)
    if actual_digest != digest:
        errors.append(f"{label}: evidence sha256 {actual_digest} != {digest}")
    return blob


def _json_pointer(value: Any, pointer: str) -> Any:
    if not pointer.startswith("/"):
        raise ValueError(f"invalid JSON pointer: {pointer}")
    current = value
    for raw_part in pointer.removeprefix("/").split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if not isinstance(current, dict) or part not in current:
            raise ValueError(f"missing JSON pointer: {pointer}")
        current = current[part]
    return current


def _verify_version_assertions(
    root: Path,
    edge_id: str,
    edge: dict[str, Any],
    errors: list[str],
) -> None:
    assertions = edge.get("version_assertions")
    if not isinstance(assertions, list):
        errors.append(f"{edge_id}: version_assertions must be a list")
        return
    required = {"runtime_package_version"}
    generator = edge.get("code_generator_version")
    if isinstance(generator, str) and not generator.startswith("not-applicable:"):
        required.add("code_generator_version")
    asserted: set[str] = set()
    for index, raw_assertion in enumerate(assertions):
        label = f"{edge_id}: version_assertions[{index}]"
        if not isinstance(raw_assertion, dict):
            errors.append(f"{label}: must be an object")
            continue
        field = _text(raw_assertion, "field", label, errors)
        if field not in {"code_generator_version", "runtime_package_version"}:
            errors.append(f"{label}: unknown version field {field}")
            continue
        asserted.add(field)
        declared_value = _text(raw_assertion, "declared_value", label, errors)
        if declared_value != edge.get(field):
            errors.append(
                f"{label}: declared version {declared_value!r} != {edge.get(field)!r}"
            )
        blob = _verify_blob_reference(root, label, raw_assertion, errors)
        checks = raw_assertion.get("json_checks")
        if blob is None or not isinstance(checks, list) or not checks:
            errors.append(f"{label}: json_checks must be a non-empty list")
            continue
        try:
            document = json.loads(blob)
        except json.JSONDecodeError:
            errors.append(f"{label}: version evidence must be JSON")
            continue
        for check_index, check in enumerate(checks):
            check_label = f"{label}.json_checks[{check_index}]"
            if not isinstance(check, dict):
                errors.append(f"{check_label}: must be an object")
                continue
            pointer = _text(check, "pointer", check_label, errors)
            expected = check.get("expected")
            try:
                actual = _json_pointer(document, pointer)
            except ValueError as error:
                errors.append(f"{check_label}: {error}")
                continue
            if actual != expected:
                errors.append(f"{check_label}: {actual!r} != {expected!r}")
    for field in sorted(required - asserted):
        errors.append(f"{edge_id}: missing version assertion for {field}")


def verify_inventory(root: Path, inventory_path: Path) -> list[str]:
    try:
        inventory = load_inventory(inventory_path)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        return [f"inventory: {error}"]
    errors: list[str] = []
    identifiers: set[str] = set()
    for index, raw_edge in enumerate(inventory["edges"]):
        label = f"edges[{index}]"
        if not isinstance(raw_edge, dict):
            errors.append(f"{label}: must be an object")
            continue
        edge_id = _text(raw_edge, "id", label, errors) or label
        if edge_id in identifiers:
            errors.append(f"{edge_id}: duplicate id")
        identifiers.add(edge_id)
        for field in (
            "caller",
            "protocol",
            "code_generator_version",
            "runtime_package_version",
            "state",
            "reason",
        ):
            _text(raw_edge, field, edge_id, errors)
        if raw_edge.get("protocol") not in PROTOCOLS:
            errors.append(f"{edge_id}: unknown protocol {raw_edge.get('protocol')}")
        state = raw_edge.get("state")
        if state not in STATES:
            errors.append(f"{edge_id}: unknown state {state}")
        if state == "active" and (
            raw_edge.get("code_generator_version") == "unmanaged"
            or raw_edge.get("runtime_package_version") == "unmanaged"
        ):
            errors.append(f"{edge_id}: active edge cannot be unmanaged")
        raw_owner = raw_edge.get("owner")
        if not isinstance(raw_owner, dict):
            errors.append(f"{edge_id}: owner must be an object")
        else:
            for field in (
                "name",
                "repository_path",
                "repository_commit",
                "contract_version",
                "contract_path",
                "contract_sha256",
            ):
                _text(raw_owner, field, f"{edge_id}: owner", errors)
            try:
                repository_path = str(raw_owner["repository_path"])
                repository_commit = str(raw_owner["repository_commit"])
                actual_gitlink = gitlink_sha(root, repository_path)
                if actual_gitlink != repository_commit:
                    errors.append(
                        f"{edge_id}: owner gitlink {actual_gitlink} != {repository_commit}"
                    )
                blob = git_blob(
                    root,
                    repository_path,
                    repository_commit,
                    str(raw_owner["contract_path"]),
                )
                actual_digest = sha256_bytes(blob)
                if actual_digest != raw_owner["contract_sha256"]:
                    errors.append(
                        f"{edge_id}: contract_sha256 {actual_digest} != "
                        f"{raw_owner['contract_sha256']}"
                    )
            except (KeyError, ValueError) as error:
                errors.append(f"{edge_id}: owner {error}")
        evidence = raw_edge.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            errors.append(f"{edge_id}: evidence must be a non-empty list")
        else:
            for evidence_index, raw_reference in enumerate(evidence):
                reference_label = f"{edge_id}: evidence[{evidence_index}]"
                if not isinstance(raw_reference, dict):
                    errors.append(f"{reference_label}: must be an object")
                    continue
                _verify_blob_reference(root, reference_label, raw_reference, errors)
        if state == "active":
            _verify_version_assertions(root, edge_id, raw_edge, errors)
        if state == "broken":
            errors.append(f"{edge_id}: declared broken: {raw_edge.get('reason')}")
    for index, raw_violation in enumerate(inventory["violations"]):
        label = f"violations[{index}]"
        if not isinstance(raw_violation, dict):
            errors.append(f"{label}: must be an object")
            continue
        violation_id = _text(raw_violation, "id", label, errors) or label
        if violation_id in identifiers:
            errors.append(f"{violation_id}: duplicate id")
        identifiers.add(violation_id)
        for field in ("caller", "target", "reason"):
            _text(raw_violation, field, violation_id, errors)
        evidence = raw_violation.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            errors.append(f"{violation_id}: evidence must be a non-empty list")
        else:
            for evidence_index, raw_reference in enumerate(evidence):
                reference_label = f"{violation_id}: evidence[{evidence_index}]"
                if not isinstance(raw_reference, dict):
                    errors.append(f"{reference_label}: must be an object")
                    continue
                _verify_blob_reference(root, reference_label, raw_reference, errors)
        errors.append(
            f"{violation_id}: illegal edge: {raw_violation.get('reason')}"
        )
    actual_edge_ids = {
        edge["id"]
        for edge in inventory["edges"]
        if isinstance(edge, dict) and isinstance(edge.get("id"), str)
    }
    actual_violation_ids = {
        violation["id"]
        for violation in inventory["violations"]
        if isinstance(violation, dict) and isinstance(violation.get("id"), str)
    }
    missing_edges = sorted(EXPECTED_EDGE_IDS - actual_edge_ids)
    unexpected_edges = sorted(actual_edge_ids - EXPECTED_EDGE_IDS)
    missing_violations = sorted(EXPECTED_VIOLATION_IDS - actual_violation_ids)
    unexpected_violations = sorted(actual_violation_ids - EXPECTED_VIOLATION_IDS)
    if missing_edges:
        errors.append(f"inventory: missing edge ids: {missing_edges}")
    if unexpected_edges:
        errors.append(f"inventory: unexpected edge ids: {unexpected_edges}")
    if missing_violations:
        errors.append(f"inventory: missing violation ids: {missing_violations}")
    if unexpected_violations:
        errors.append(f"inventory: unexpected violation ids: {unexpected_violations}")
    return sorted(set(errors))
```

该实现只从 Root index 和 child commit blob 取证；工作树脏文件不会改变结果。错误是数据，不通过 traceback 代替稳定诊断。

- [ ] **Step 4: 实现薄 CLI**

`scripts/verify-contract-compatibility.py` 使用以下完整入口；不得增加 refresh、write、allow、ignore 或 exclude 参数：

```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.governance.contract_inventory import load_inventory, verify_inventory


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify frozen owner/consumer contract pins.")
    parser.add_argument(
        "--inventory",
        type=Path,
        default=ROOT / "verification/contracts/consumer-inventory.json",
    )
    args = parser.parse_args(argv)
    inventory_path = args.inventory
    if not inventory_path.is_absolute():
        inventory_path = ROOT / inventory_path
    errors = verify_inventory(ROOT, inventory_path)
    try:
        inventory = load_inventory(inventory_path)
        edge_count = len(inventory["edges"])
        violation_count = len(inventory["violations"])
    except (OSError, json.JSONDecodeError, ValueError, TypeError):
        edge_count = 0
        violation_count = 0
    payload: dict[str, object] = {
        "status": "FAIL" if errors else "PASS",
        "edge_count": edge_count,
        "violation_count": violation_count,
    }
    if errors:
        payload["errors"] = errors
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: 运行聚焦测试**

```bash
python3 -m pytest scripts/tests/test_contract_compatibility.py -q
python3 -m pytest scripts/tests/test_repository_topology.py scripts/tests/test_contract_compatibility.py -q
```

Expected: 两条命令 exit 0，所有新测试通过。

- [ ] **Step 6: Root 审查后精确提交**

```bash
git add scripts/governance/contract_inventory.py \
  scripts/verify-contract-compatibility.py \
  scripts/tests/test_contract_compatibility.py
git commit -m "test(contracts): verify frozen owner and consumer pins"
```

## Task 3: Freeze the complete current call inventory

**Files:**

- Create: `verification/contracts/consumer-inventory.json`
- Create: `verification/contracts/README.md`
- Modify: `scripts/INDEX.md`

**Interfaces:**

- Consumes: Task 2 schema/verifier；Root 当前 gitlinks；下表给出的全部 owner artifact 与 evidence 路径。
- Produces: 16 条批准 topology edge、1 条非法 Web→IAM 旁路及其精确冻结证据。

- [ ] **Step 1: 写入 owner artifact 常量**

清单中重复使用以下精确 owner tuple；digest 必须来自表内对应 repository 中 `git show` 读取的指定 commit/path blob bytes，不从工作树读取：

| Owner          | repository path          | commit                                     | contract version        | contract path                                                  | SHA-256                                                            |
| -------------- | ------------------------ | ------------------------------------------ | ----------------------- | -------------------------------------------------------------- | ------------------------------------------------------------------ |
| Web            | `apps/kokoro-app`        | `ce4e466c960c4b40a87a7be38b5a56f265f7a12f` | `browser-private-0.1.0` | `contract/README.md`                                           | `651f270aab0e3451ac4cd6a68f490024c3e907751571940bda6f817224b6821f` |
| BFF            | `apps/kokoro-bff`        | `f117a00a9c12649a762c975622da81ad8e3c59ec` | `1.0.0`                 | `contract/openapi/v1/openapi.yaml`                             | `af2b1cfd350b139527a8ce2579764d32412c9d3f43927d1eb86e9ebd6030127f` |
| IAM            | `apps/kokoro-iam`        | `35d868a410c06731362bd1e8bcc3e602d01875f8` | `0.1.0`                 | `contract/openapi/iam.internal.v1.json`                        | `b76903a274c708910a791b47beefbeb9094a3a38269e07112c084aecce7d2579` |
| System         | `apps/kokoro-system`     | `c0a76a3a7614bf46ea6e665e523f24261862436f` | `2.0.0`                 | `contract/openapi/system.openapi.json`                         | `f9ea76f107e1ea0fc19df20ee7c59032c0fbac66e640e9a16a1b770ab27c1f37` |
| Agent          | `apps/kokoro-agent`      | `741c928dfc11313a25064a905d77d4ad371f5534` | `1.1.0`                 | `contract/openapi/v1/openapi.json`                             | `20e679c5e46ec3fee0b1e002b2b37bdbcae21b1bee5616bd8013bd62d4d7e71f` |
| Capability RPC | `apps/kokoro-capability` | `e576d38dd103c2fda4d6389385b3f04f82ddfc20` | `kokoro.capability.v1`  | `contract/proto/kokoro/capability/v1/capability_runtime.proto` | `830b5b6cbc1409ce8a8cb87dace688fd76e4f07d17c18c8cadedb4ec725a66a5` |
| Storage        | `apps/kokoro-storage`    | `f80917e98a1cd1fe196ce10b0aba6f8f67fdf205` | `kokoro.storage.v2`     | `contract/proto/kokoro/storage/v2/storage.proto`               | `e6a599c447d19f9d97b097751156ef8e84f2ce34ffe38c67f4f83dcdc22a4def` |
| Scheduler      | `apps/kokoro-scheduler`  | `17c2de3e68ed75dbf3fa495643f6ad280e3c7112` | `1.0.0`                 | `contract/openapi/v1/openapi.yaml`                             | `49be4429f9b1f4e86582c95aff770f6835629d3ea4ad80408bf65d0c64e598c3` |
| Billing v1     | `apps/kokoro-billing`    | `63e0ab6e61b397f23f7ab71f5d6dc9df3d6de0fa` | `1.0.0`                 | `contract/openapi/v1/openapi.yaml`                             | `58fbe4fea083ba12e0db23f49e995b96500d01af0013febf40eba3093510ef63` |

- [ ] **Step 2: 写入完整 16-edge matrix**

每个 evidence object 的 `repository_commit` 使用对应 Root gitlink。运行以下字面脚本计算全部 evidence blob SHA-256，并把输出值逐项复制到对应 JSON；脚本不读取工作树内容：

```python
import hashlib
import subprocess

evidence = [
    ("apps/kokoro-app", "ce4e466c960c4b40a87a7be38b5a56f265f7a12f", "contract/README.md"),
    ("apps/kokoro-app", "ce4e466c960c4b40a87a7be38b5a56f265f7a12f", "src/app/api/session/[...path]/route.ts"),
    ("apps/kokoro-app", "ce4e466c960c4b40a87a7be38b5a56f265f7a12f", "src/engine/agui-chat-transport.ts"),
    ("apps/kokoro-app", "ce4e466c960c4b40a87a7be38b5a56f265f7a12f", "src/lib/server/auth.ts"),
    ("apps/kokoro-app", "ce4e466c960c4b40a87a7be38b5a56f265f7a12f", "package.json"),
    ("apps/kokoro-bff", "f117a00a9c12649a762c975622da81ad8e3c59ec", "src/config/runtime.ts"),
    ("apps/kokoro-bff", "f117a00a9c12649a762c975622da81ad8e3c59ec", "src/http/request.ts"),
    ("apps/kokoro-bff", "f117a00a9c12649a762c975622da81ad8e3c59ec", "src/http/routes/owner.ts"),
    ("apps/kokoro-bff", "f117a00a9c12649a762c975622da81ad8e3c59ec", "src/upstream.ts"),
    ("apps/kokoro-bff", "f117a00a9c12649a762c975622da81ad8e3c59ec", "contract/README.md"),
    ("apps/kokoro-bff", "f117a00a9c12649a762c975622da81ad8e3c59ec", "src/infrastructure/clients/agent/launch.ts"),
    ("apps/kokoro-bff", "f117a00a9c12649a762c975622da81ad8e3c59ec", "src/infrastructure/clients/agent/projector-source.ts"),
    ("apps/kokoro-bff", "f117a00a9c12649a762c975622da81ad8e3c59ec", "src/infrastructure/clients/scheduler/outbox-delivery.ts"),
    ("apps/kokoro-bff", "f117a00a9c12649a762c975622da81ad8e3c59ec", "src/http/routes/scheduler.ts"),
    ("apps/kokoro-bff", "f117a00a9c12649a762c975622da81ad8e3c59ec", "package.json"),
    ("apps/kokoro-billing", "63e0ab6e61b397f23f7ab71f5d6dc9df3d6de0fa", "docs/CURRENT.md"),
    ("apps/kokoro-agent", "741c928dfc11313a25064a905d77d4ad371f5534", "src/kokoro_agent/clients/system.py"),
    ("apps/kokoro-agent", "741c928dfc11313a25064a905d77d4ad371f5534", "src/kokoro_agent/worker/main.py"),
    ("apps/kokoro-agent", "741c928dfc11313a25064a905d77d4ad371f5534", "contract/provenance.json"),
    ("apps/kokoro-agent", "741c928dfc11313a25064a905d77d4ad371f5534", "src/kokoro_agent/clients/skills.py"),
    ("apps/kokoro-agent", "741c928dfc11313a25064a905d77d4ad371f5534", "src/kokoro_agent/clients/mcp.py"),
    ("apps/kokoro-agent", "741c928dfc11313a25064a905d77d4ad371f5534", "src/kokoro_agent/worker/dependencies.py"),
    ("apps/kokoro-agent", "741c928dfc11313a25064a905d77d4ad371f5534", "src/kokoro_agent/clients/storage.py"),
    ("apps/kokoro-agent", "741c928dfc11313a25064a905d77d4ad371f5534", "contract/openapi/v1/openapi.json"),
    ("apps/kokoro-agent", "741c928dfc11313a25064a905d77d4ad371f5534", "uv.lock"),
    ("apps/kokoro-capability", "e576d38dd103c2fda4d6389385b3f04f82ddfc20", "src/modules/skills/source/skill-projection.controller.ts"),
    ("apps/kokoro-capability", "e576d38dd103c2fda4d6389385b3f04f82ddfc20", "src/modules/mcp/server/mcp-server-projection.controller.ts"),
    ("apps/kokoro-capability", "e576d38dd103c2fda4d6389385b3f04f82ddfc20", "src/modules/skills/storage-package.client.ts"),
    ("apps/kokoro-capability", "e576d38dd103c2fda4d6389385b3f04f82ddfc20", "src/generated/proto/kokoro/storage/v1/storage_pb.ts"),
    ("apps/kokoro-capability", "e576d38dd103c2fda4d6389385b3f04f82ddfc20", "package.json"),
    ("apps/kokoro-capability", "e576d38dd103c2fda4d6389385b3f04f82ddfc20", "src/infrastructure/clients/iam/http-attestation.ts"),
    ("apps/kokoro-capability", "e576d38dd103c2fda4d6389385b3f04f82ddfc20", "src/modules/skills/skills.module.ts"),
    ("apps/kokoro-iam", "35d868a410c06731362bd1e8bcc3e602d01875f8", "docs/CURRENT.md"),
    ("apps/kokoro-storage", "f80917e98a1cd1fe196ce10b0aba6f8f67fdf205", "contract/openapi.json"),
    ("apps/kokoro-storage", "f80917e98a1cd1fe196ce10b0aba6f8f67fdf205", "contract/proto/kokoro/storage/v2/storage.proto"),
    ("apps/kokoro-scheduler", "17c2de3e68ed75dbf3fa495643f6ad280e3c7112", "contract/openapi/v1/openapi.yaml"),
    ("apps/kokoro-scheduler", "17c2de3e68ed75dbf3fa495643f6ad280e3c7112", "internal/adapters/httpclient/client.go"),
    ("apps/kokoro-scheduler", "17c2de3e68ed75dbf3fa495643f6ad280e3c7112", "go.mod"),
]
for repository, commit, path in evidence:
    blob = subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=repository,
        capture_output=True,
        check=True,
    ).stdout
    print(repository, commit, path, hashlib.sha256(blob).hexdigest())
```

`caller → target` 记录运行时调用方向，`contract owner` 记录 canonical schema 的唯一 owner；二者不得视为同义。普通 request/response edge 通常由 target 拥有 contract，但 outbound event protocol 由 producer 拥有。`EDGE-SCHEDULER-BFF` 与 `EDGE-SCHEDULER-AGENT` 因而都使用 Step 1 的 Scheduler canonical OpenAPI tuple：`apps/kokoro-scheduler`、`17c2de3e68ed75dbf3fa495643f6ad280e3c7112`、`1.0.0`、`contract/openapi/v1/openapi.yaml`、`49be4429f9b1f4e86582c95aff770f6835629d3ea4ad80408bf65d0c64e598c3`；BFF/Agent 仍是 target 与 consumer evidence。

| id                        | caller → target / protocol           | contract owner | state  | generator / runtime                                                                                                                          | evidence path（均为相对各自 repository）                                                                                                                            | 精确 reason                                                                                             |
| ------------------------- | ------------------------------------ | -------------- | ------ | -------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| `EDGE-BROWSER-WEB`        | Browser→Web / `same-origin-http`     | Web            | active | `not-applicable:same-origin-route` / `next@16.2.6`                                                                                           | Web `contract/README.md`; `src/app/api/session/[...path]/route.ts`; `package.json`                                                                                  | Browser 只进入 Web same-origin routes。                                                                 |
| `EDGE-WEB-BFF`            | Web→BFF / `http-openapi`             | BFF            | broken | `unmanaged` / `next@16.2.6+@ag-ui/core@0.0.59+ai@7.0.92`                                                                                     | Web `src/app/api/session/[...path]/route.ts`; `src/engine/agui-chat-transport.ts`; `package.json`                                                                   | Runtime path exists but Web has no BFF artifact commit/digest pin or generated client.                  |
| `EDGE-BFF-IAM`            | BFF→IAM / `http-openapi`             | IAM            | broken | `unmanaged` / `unmanaged`                                                                                                                    | BFF `src/config/runtime.ts`; `src/http/request.ts`                                                                                                                  | BFF has no IAM upstream or admission client and trusts Web headers/shared secret only.                  |
| `EDGE-BFF-SYSTEM`         | BFF→System / `http-openapi`          | System         | broken | `unmanaged` / `node:http@22`                                                                                                                 | BFF `src/http/routes/owner.ts`; `src/upstream.ts`; `contract/README.md`; `package.json`                                                                             | Calls are handwritten and the recorded System commit pin is stale.                                      |
| `EDGE-BFF-CAPABILITY`     | BFF→Capability / `connect-proto`     | Capability     | broken | `unmanaged` / `unmanaged`                                                                                                                    | BFF `src/http/routes/owner.ts`; Capability `src/modules/skills/source/skill-projection.controller.ts`; `src/modules/mcp/server/mcp-server-projection.controller.ts` | BFF calls removed `/bff/*` HTTP paths and has no Connect client.                                        |
| `EDGE-BFF-STORAGE`        | BFF→Storage / `connect-proto`        | Storage        | broken | `unmanaged` / `unmanaged`                                                                                                                    | BFF `src/http/routes/owner.ts`; Storage `contract/openapi.json`; `contract/proto/kokoro/storage/v2/storage.proto`                                                   | BFF calls deleted `/internal/bff/library` and has no Storage v2 Connect client.                         |
| `EDGE-BFF-AGENT`          | BFF→Agent / `http-openapi`           | Agent          | broken | `unmanaged` / `node:http@22`                                                                                                                 | BFF `src/infrastructure/clients/agent/launch.ts`; `src/infrastructure/clients/agent/projector-source.ts`; `contract/README.md`; `package.json`                      | Runtime calls are handwritten and the recorded Agent commit pin is stale.                               |
| `EDGE-BFF-SCHEDULER`      | BFF→Scheduler / `http-openapi`       | Scheduler      | broken | `unmanaged` / `node:http@22`                                                                                                                 | BFF `src/infrastructure/clients/scheduler/outbox-delivery.ts`; `package.json`; Scheduler `contract/openapi/v1/openapi.yaml`                                         | BFF sends `/jobs/{name}` while owner contract exposes `/schedules/{name}`.                              |
| `EDGE-BFF-BILLING`        | BFF→Billing / `http-openapi`         | Billing        | broken | `unmanaged` / `node:http@22`                                                                                                                 | BFF `src/http/routes/owner.ts`; `package.json`; Billing `docs/CURRENT.md`                                                                                           | BFF consumes v1 while Billing v2 is target-only and no unique release artifact/generated client exists. |
| `EDGE-AGENT-SYSTEM`       | Agent→System / `http-openapi`        | System         | broken | `unmanaged` / `httpx@0.28.1`                                                                                                                 | Agent `src/kokoro_agent/clients/system.py`; `src/kokoro_agent/worker/main.py`; `contract/provenance.json`; `uv.lock`                                                | Runtime works through handwritten HTTP and the recorded System commit pin is stale.                     |
| `EDGE-AGENT-CAPABILITY`   | Agent→Capability / `connect-proto`   | Capability     | broken | `unmanaged` / `unmanaged`                                                                                                                    | Agent `src/kokoro_agent/clients/skills.py`; `src/kokoro_agent/clients/mcp.py`; `src/kokoro_agent/worker/dependencies.py`; `src/kokoro_agent/worker/main.py`         | Only optional interfaces exist; no production Connect adapter is assembled.                             |
| `EDGE-AGENT-STORAGE`      | Agent→Storage / `connect-proto`      | Storage        | broken | `unmanaged` / `unmanaged`                                                                                                                    | Agent `src/kokoro_agent/clients/storage.py`; `src/kokoro_agent/worker/dependencies.py`; `src/kokoro_agent/worker/main.py`                                           | Only a Protocol exists; no Storage v2 adapter/generated client is assembled.                            |
| `EDGE-CAPABILITY-STORAGE` | Capability→Storage / `connect-proto` | Storage        | broken | `@bufbuild/buf@1.72.0+@bufbuild/protoc-gen-es@2.14.0` / `@bufbuild/protobuf@2.14.0+@connectrpc/connect@2.2.0+@connectrpc/connect-node@2.2.0` | Capability `src/modules/skills/storage-package.client.ts`; `src/generated/proto/kokoro/storage/v1/storage_pb.ts`; `package.json`                                    | Consumer is generated from `kokoro.storage.v1` while owner canonical contract is v2.                    |
| `EDGE-CAPABILITY-IAM`     | Capability→IAM / `http-openapi`      | IAM            | broken | `unmanaged` / `node:fetch@24`                                                                                                                | Capability `src/infrastructure/clients/iam/http-attestation.ts`; `src/modules/skills/skills.module.ts`; IAM `docs/CURRENT.md`                                       | Capability expects a handwritten attestation endpoint that IAM runtime/OpenAPI does not expose.         |
| `EDGE-SCHEDULER-BFF`      | Scheduler→BFF / `http-event`         | Scheduler      | broken | `unmanaged` / `go:net/http@1.26.8+node:http@22`                                                                                              | Scheduler `internal/adapters/httpclient/client.go`; `go.mod`; BFF `src/http/routes/scheduler.ts`; `package.json`                                                    | Scheduler emits schedule header/RFC3339Nano while BFF expects job header/compact timestamp.             |
| `EDGE-SCHEDULER-AGENT`    | Scheduler→Agent / `http-event`       | Scheduler      | broken | `unmanaged` / `go:net/http@1.26.8`                                                                                                           | Scheduler `internal/adapters/httpclient/client.go`; `go.mod`; Agent `contract/openapi/v1/openapi.json`                                                              | Scheduler can emit webhooks but Agent has no scheduler callback operation or header handling.           |

第一条 active edge 必须按以下完整 JSON 写入；其余 15 条复用同一字段结构并使用上表字面值，不得省略 `evidence`：

```json
{
  "id": "EDGE-BROWSER-WEB",
  "caller": "Browser",
  "owner": {
    "name": "kokoro-app",
    "repository_path": "apps/kokoro-app",
    "repository_commit": "ce4e466c960c4b40a87a7be38b5a56f265f7a12f",
    "contract_version": "browser-private-0.1.0",
    "contract_path": "contract/README.md",
    "contract_sha256": "651f270aab0e3451ac4cd6a68f490024c3e907751571940bda6f817224b6821f"
  },
  "protocol": "same-origin-http",
  "code_generator_version": "not-applicable:same-origin-route",
  "runtime_package_version": "next@16.2.6",
  "state": "active",
  "reason": "Browser enters only Web same-origin routes.",
  "evidence": [
    {
      "repository_path": "apps/kokoro-app",
      "repository_commit": "ce4e466c960c4b40a87a7be38b5a56f265f7a12f",
      "path": "contract/README.md",
      "sha256": "651f270aab0e3451ac4cd6a68f490024c3e907751571940bda6f817224b6821f"
    },
    {
      "repository_path": "apps/kokoro-app",
      "repository_commit": "ce4e466c960c4b40a87a7be38b5a56f265f7a12f",
      "path": "src/app/api/session/[...path]/route.ts",
      "sha256": "87cb54ab3fc1d309c67d8786e0b27fc7dab3f291277a63a623b774f1a247b8da"
    },
    {
      "repository_path": "apps/kokoro-app",
      "repository_commit": "ce4e466c960c4b40a87a7be38b5a56f265f7a12f",
      "path": "package.json",
      "sha256": "09a2bf989ec1e2e834682428a45aa68b909a6e80abf06df9010059d8f950e348"
    }
  ],
  "version_assertions": [
    {
      "field": "runtime_package_version",
      "declared_value": "next@16.2.6",
      "repository_path": "apps/kokoro-app",
      "repository_commit": "ce4e466c960c4b40a87a7be38b5a56f265f7a12f",
      "path": "package.json",
      "sha256": "09a2bf989ec1e2e834682428a45aa68b909a6e80abf06df9010059d8f950e348",
      "json_checks": [{ "pointer": "/dependencies/next", "expected": "16.2.6" }]
    }
  ]
}
```

- [ ] **Step 3: 写入非法旁路**

`violations` 只包含 `EDGE-WEB-IAM-DIRECT`，evidence 固定为 Web `src/lib/server/auth.ts`，reason 固定为：`Web directly calls IAM and bypasses the required Web -> BFF -> IAM boundary.`。该记录必须始终令 CLI 失败。Wave 1 删除旁路时，必须在同一受审切片同时删除 manifest 记录、把 `EXPECTED_VIOLATION_IDS` 改为空集合并加入“旧 ID 不再接受”的测试；单独删 manifest 行仍由 topology baseline 报错。

- [ ] **Step 4: 文档化字段与变更协议**

`verification/contracts/README.md` 明确：owner/evidence digest 都来自 commit blob；`unmanaged` 只能用于 broken edge；owner-first 提交并推送后才能更新 pin；任一 edge 只有 contract、runtime、generated client、evidence 和 tests 同时满足时才改为 active。`scripts/INDEX.md` 增加命令与 exit code。

- [ ] **Step 5: 运行真实红门与单测**

```bash
python3 -m pytest scripts/tests/test_contract_compatibility.py -q
python3 scripts/verify-contract-compatibility.py --inventory verification/contracts/consumer-inventory.json
```

Expected: pytest exit 0；CLI exit 1，错误集合精确包含 15 条 `declared broken` 与 1 条 `illegal edge`，且没有 schema、gitlink、contract digest 或 evidence digest 漂移。

- [ ] **Step 6: Root 审查后精确提交**

```bash
git add verification/contracts/consumer-inventory.json \
  verification/contracts/README.md scripts/INDEX.md
git commit -m "test(contracts): freeze complete consumer inventory"
```

## Task 4: Review, integrate, and freeze Wave 0A evidence

**Files:**

- Modify: `docs/task.md`
- Modify: `docs/progress.md`
- Modify: `docs/INDEX.md`

**Interfaces:**

- Consumes: Task 1–3 commits、审查报告和当前门禁输出。
- Produces: W0A 冻结证据；W0B 直接消费的 15 个 broken edge 与非法旁路队列。

- [ ] **Step 1: 规格审查**

只读审查 Agent 检查数据库裁决、协议矩阵、Capability 当前态、16-edge 完整性、Web→IAM 旁路、owner/evidence commit-blob pin、generator/runtime 字段和不复制 contract。Blocking/Important/Minor 均为 0 才进入质量审查。

- [ ] **Step 2: 质量审查**

第二名只读审查 Agent 检查路径穿越防护、稳定错误、fixture 隔离、脏子仓不能影响摘要、重复 id/enum/unmanaged-active/digest/gitlink 负例。审查绑定同一 Root SHA；有变更则重新审查。

- [ ] **Step 3: Root 在冻结 SHA 上复跑完整门禁**

```bash
python3 scripts/verify-repository-topology.py
python3 -m pytest scripts/tests -q
python3 scripts/verify-ten-repository-standard.py --format json
python3 scripts/verify-contract-compatibility.py --inventory verification/contracts/consumer-inventory.json
git diff --check
```

Expected: topology exit 0；pytest 全绿；ten-repository 的真实 violation/unverified 数原样记录；compatibility CLI 只因 15 个 broken edge 和 1 个非法旁路 exit 1；diff check exit 0。

- [ ] **Step 4: 更新任务与证据账**

将 W0A-0 至 W0A-4 的实际状态写入 `docs/task.md`；只有已提交、双审和 Root 复验的任务可标 `已验收`。在 `docs/progress.md` 追加 commit、命令实际输出、两轮审查结论和 W0B 红门列表，不改写启动记录。

- [ ] **Step 5: 更新索引并提交收口文档**

`docs/INDEX.md` 链接 task、progress、批准设计和本计划：

```bash
git add docs/task.md docs/progress.md docs/INDEX.md
git commit -m "docs(governance): freeze wave 0a evidence"
```

- [ ] **Step 6: 推送并进入 W0B**

```bash
git push origin main
git status --short --branch
```

Expected: push 成功；状态只显示 `## main...origin/main`。随后为 W0B 的 owner-first 修复拆分独立计划，不在本计划扩大实现范围。
