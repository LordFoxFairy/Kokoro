from __future__ import annotations

import ast
import json
import re
import tomllib
from pathlib import Path

import pytest

from scripts.governance.handbook_examples import (
    ROOT,
    STANDARDS,
    code_blocks,
    extract_examples,
)


def test_examples_extract_from_the_current_manuals(tmp_path: Path) -> None:
    paths = extract_examples(tmp_path)
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
    for path in paths:
        if path.suffix == ".py":
            ast.parse(path.read_text())
        elif path.suffix == ".json":
            json.loads(path.read_text())
        elif path.suffix == ".toml":
            tomllib.loads(path.read_text())
    with pytest.raises(ValueError, match="empty"):
        extract_examples(tmp_path)


def test_sql_example_does_not_imply_every_table_needs_status_or_constraints() -> None:
    sql = (STANDARDS / "03-sql-and-postgresql.md").read_text()
    schema = code_blocks(sql, "sql")[0]
    for forbidden in (
        "status",
        "version",
        "CHECK",
        "UNIQUE",
        "REFERENCES",
        "FOREIGN KEY",
    ):
        assert forbidden not in schema
    assert "deleted_at TIMESTAMPTZ(3) NULL" in schema
    assert re.search(r"\| `status`\s*\| \*\*默认不加\*\*", sql)
    assert "字符而非字节" in sql


def test_canonical_manuals_have_sources_and_balanced_code_fences() -> None:
    for name in (
        "03-sql-and-postgresql.md",
        "08-typescript-backend-engineering.md",
        "09-python-backend-engineering.md",
    ):
        text = (STANDARDS / name).read_text()
        assert len(re.findall(r"^```", text, re.MULTILINE)) % 2 == 0
        assert re.search(
            r"^## 17\. (?:参考依据|真实来源与核验记录)$", text, re.MULTILINE
        )
        assert "https://" in text
    agents = (ROOT / "AGENTS.md").read_text()
    assert not code_blocks(agents, "ts")
    assert not code_blocks(agents, "python")
    assert not code_blocks(agents, "sql")


def test_local_ci_database_identity_and_owner_isolation_are_not_conflated() -> None:
    agents = (ROOT / "AGENTS.md").read_text()
    architecture = (ROOT / "docs/ARCHITECTURE_STANDARD.md").read_text()
    sql = (ROOT / "docs/kokoro-handbook/standards/03-sql-and-postgresql.md").read_text()
    decision = (
        "本地与 CI 复用一个 PostgreSQL 实例和一套应用 role/credential；每个数据 owner 仍使用"
        "独立 database/schema 与独立连接 URL。代码、Schema、查询、事务和测试继续禁止跨 owner "
        "SQL/JOIN、表引用、ORM model 与 canonical schema 共享。每 owner 独立 production role、"
        "GRANT/REVOKE、数据库 mTLS 和 NetworkPolicy 属于部署阶段，不是当前闭环门禁。"
    )
    for content in (agents, architecture, sql):
        assert decision in content
        assert "SQL-first" in content
        assert "ORM-first" in content
        assert "canonical schema" in content
        assert (
            "每个数据 owner 使用独立 PostgreSQL database/schema 和凭据" not in content
        )
        assert "每个服务使用独立 database/schema 和独立凭据" not in content


def test_architecture_has_the_complete_approved_protocol_matrix() -> None:
    architecture = (ROOT / "docs/ARCHITECTURE_STANDARD.md").read_text()
    agents = (ROOT / "AGENTS.md").read_text()
    table_rows = [
        "| " + " | ".join(cell.strip() for cell in line.strip("|").split("|")) + " |"
        for line in architecture.splitlines()
        if line.startswith("|")
    ]
    rows = (
        "| Browser → Web | same-origin HTTP | Web | Cookie、CSRF、浏览器状态。 |",
        "| Web → BFF | HTTP/OpenAPI；AG-UI/SSE | BFF | Public Product API 与 durable event projection。 |",
        "| BFF → IAM | HTTP/OpenAPI generated client | IAM | OAuth/OIDC/Better Auth 保持原生 HTTP 语义。 |",
        "| BFF/Agent → System | HTTP/OpenAPI generated client | System | 不因统一偏好重写当前稳定 HTTP。 |",
        "| BFF/Agent → Platform | ConnectRPC/Proto | Platform | Skills/MCP typed command/query。 |",
        "| BFF/Agent/Platform → Storage | ConnectRPC/Proto v2 | Storage | Asset、Artifact、Upload、Package reference。 |",
        "| BFF → Agent | HTTP/OpenAPI generated client | Agent | Run dispatch/control 与可恢复 event paging。 |",
        "| BFF → Scheduler | HTTP/OpenAPI generated client | Scheduler | Schedule command/query。 |",
        "| Scheduler → BFF/Agent | HTTP event protocol | Scheduler | Durable retry、receipt、duplicate delivery。 |",
        "| BFF → Billing | HTTP/OpenAPI generated client | Billing | Checkout、payment resource 与 provider webhook。 |",
    )
    assert "| Caller → Owner | 唯一目标协议 | 契约 owner | 说明 |" in table_rows
    for row in rows:
        assert table_rows.count(row) == 1
    assert "BFF → IAM/System/Agent/Scheduler/Billing" not in architecture
    assert "Root 只做 catalog 和治理" in architecture
    assert "Root 不建立跨仓可编辑 contract 中心" in agents
    assert "不共享 ORM schema、SQL、业务 DTO" in agents
    assert "固定版本、commit 和 digest 的 generated client/artifact" in agents


def test_architecture_locks_capability_current_identity_and_atomic_cutover() -> None:
    architecture = re.sub(
        r"\s+", " ", (ROOT / "docs/ARCHITECTURE_STANDARD.md").read_text()
    )
    decision = (
        "当前物理身份仍是 `kokoro-capability`。只有 remote、path、package、service、env、Proto、"
        "数据库、Redis 和 consumer 在 Wave 3 同一窗口完成切换并通过 owner 完整门禁与跨仓 "
        "integration/smoke 后，才改称 `kokoro-platform`；切换前的 Root 路径、运行身份和当前状态"
        "不得提前使用目标名称，也不保留兼容 alias。"
    )
    assert decision in architecture


def test_architecture_allows_exactly_one_sql_first_or_orm_first_schema() -> None:
    architecture = (ROOT / "docs/ARCHITECTURE_STANDARD.md").read_text()
    assert (
        "每个数据 owner 维护一份唯一 canonical schema；SQL-first 使用 "
        "`database/schema.sql`，ORM-first 使用技术方案批准的唯一 ORM schema。"
        in architecture
    )
    assert "每个数据 owner 维护唯一 `database/schema.sql`" not in architecture
