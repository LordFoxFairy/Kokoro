"""Web, BFF and Python Agent checks with surface-specific semantics."""

from __future__ import annotations

import re

from .ten_repository_standard import (
    REQUIRED_AGENT_LAYERS,
    ROOT,
    Failure,
    add,
    contract_source_files,
    package_manifest,
    read_text,
    source_files,
)


def check_web(failures: list[Failure]) -> None:
    repository_name = "kokoro"
    repository = ROOT / repository_name
    manifest = package_manifest(repository)
    dependencies = {
        **(
            manifest.get("dependencies", {})
            if isinstance(manifest.get("dependencies"), dict)
            else {}
        ),
        **(
            manifest.get("devDependencies", {})
            if isinstance(manifest.get("devDependencies"), dict)
            else {}
        ),
    }
    for dependency in ("@ag-ui/core", "ai", "@ai-sdk/react"):
        if dependency not in dependencies:
            add(
                failures,
                repository_name,
                "agui-ui-adapter",
                f"package.json must pin {dependency!r} for the AG-UI -> UIMessage adapter",
            )

    source_entries = source_files(repository)
    source_text = "\n".join(
        read_text(path) for path in source_entries if path.suffix in {".ts", ".tsx"}
    )
    if "AgUiChatTransport" not in source_text:
        add(
            failures,
            repository_name,
            "agui-ui-adapter",
            "src must provide the in-repository AgUiChatTransport",
        )
    if re.search(r"\bSessionEvent\b", source_text):
        add(
            failures,
            repository_name,
            "single-agent-protocol",
            "src still references legacy SessionEvent instead of the sole AG-UI network protocol",
        )
    if re.search(
        r"KOKORO_(?:IAM|AGENT|SYSTEM|MODEL|BILLING|CAPABILITY|STORAGE)_", source_text
    ):
        add(
            failures,
            repository_name,
            "web-bff-boundary",
            "Web source references a downstream owner directly instead of the BFF",
        )

    for path in source_entries:
        if path.suffix.lower() != ".css":
            continue
        relative = path.relative_to(repository).as_posix()
        text = read_text(path)
        important_count = len(re.findall(r"!important\b", text))
        if important_count:
            add(
                failures,
                repository_name,
                "css-specificity",
                f"{relative} contains {important_count} !important declarations without an exemption registry",
            )
        if (
            re.search(r"outline\s*:\s*(?:none|0)\b", text, re.IGNORECASE)
            and ":focus-visible" not in text
        ):
            add(
                failures,
                repository_name,
                "accessibility",
                f"{relative} removes outline without a focus-visible replacement",
            )


def check_bff(failures: list[Failure]) -> None:
    repository_name = "kokoro-bff"
    repository = ROOT / repository_name
    expected_openapi = repository / "contract" / "openapi" / "v1" / "openapi.yaml"
    if not expected_openapi.is_file():
        add(
            failures,
            repository_name,
            "public-contract",
            "public Product API must be canonical at contract/openapi/v1/openapi.yaml",
        )
    for path in source_files(repository):
        if path.suffix not in {".ts", ".tsx"}:
            continue
        text = read_text(path)
        relative = path.relative_to(repository).as_posix()
        if re.search(r"\bMockBffStore\b", text):
            add(
                failures,
                repository_name,
                "production-doubles",
                f"{relative} contains MockBffStore in production source",
            )
        if re.search(
            r"generic[-_ ]owner|owner[-_ ]proxy|proxyOwner", text, re.IGNORECASE
        ):
            add(
                failures,
                repository_name,
                "explicit-owner-adapters",
                f"{relative} contains a generic owner proxy instead of a narrow owner adapter",
            )

    schema = read_text(repository / "database" / "schema.sql").lower()
    if schema and not ("agui" in schema and "cursor" in schema):
        add(
            failures,
            repository_name,
            "durable-agui-projection",
            "database/schema.sql must define the durable AG-UI projection and public cursor",
        )


def check_agent(failures: list[Failure]) -> None:
    repository_name = "kokoro-agent"
    repository = ROOT / repository_name
    package_root = repository / "src" / "kokoro_agent"
    for layer in REQUIRED_AGENT_LAYERS:
        if not (package_root / layer).is_dir():
            add(
                failures,
                repository_name,
                "layered-topology",
                f"src/kokoro_agent/{layer}/ is missing",
            )

    pyproject = read_text(repository / "pyproject.toml")
    if not re.search(
        r"\[tool\.pyright\][\s\S]*?typeCheckingMode\s*=\s*[\"']strict[\"']", pyproject
    ):
        add(
            failures,
            repository_name,
            "python-strictness",
            "Pyright strict mode is missing",
        )
    for tool in ("pyright", "pytest", "ruff"):
        if not re.search(rf"[\"']{tool}(?:[=>~!<]|[\"'])", pyproject, re.IGNORECASE):
            add(
                failures,
                repository_name,
                "python-tooling",
                f"pyproject.toml does not declare {tool}",
            )
    if not (repository / "uv.lock").is_file():
        add(failures, repository_name, "python-tooling", "uv.lock is missing")
    if not contract_source_files(repository):
        add(
            failures,
            repository_name,
            "contract-owner",
            "Agent run/control/event boundary has no machine contract under contract/",
        )

    forbidden_domain_import = re.compile(
        r"(?:from|import)\s+kokoro_agent\.(?:application|infrastructure|interfaces)\b"
    )
    for path in source_files(repository):
        if path.suffix != ".py":
            continue
        relative = path.relative_to(repository).as_posix()
        text = read_text(path)
        line_count = len(text.splitlines())
        if not relative.startswith("src/kokoro_agent/generated/") and line_count > 800:
            add(
                failures,
                repository_name,
                "file-granularity",
                f"{relative} exceeds 800 lines",
            )
        if re.search(
            r"^\s*#\s*(?:pyright|mypy):.*(?:false|ignore)",
            text,
            re.MULTILINE | re.IGNORECASE,
        ):
            add(
                failures,
                repository_name,
                "python-strictness",
                f"{relative} has a file-wide type suppression",
            )
        if relative.startswith(
            "src/kokoro_agent/domain/"
        ) and forbidden_domain_import.search(text):
            add(
                failures,
                repository_name,
                "dependency-direction",
                f"{relative} imports outside Domain",
            )
        if re.search(
            r"\b(?:NoSkillsClient|InMemory\w*Repository|Fake\w*|Fixture\w*)\b", text
        ):
            add(
                failures,
                repository_name,
                "production-doubles",
                f"{relative} contains a production test double",
            )
        if re.search(r"\b[a-z0-9_]+_at_unix_seconds\b", text, re.IGNORECASE):
            add(
                failures,
                repository_name,
                "utc-time",
                f"{relative} models a database fact as Unix seconds",
            )

    schema = read_text(repository / "database" / "schema.sql").lower()
    if schema:
        for marker in ("tenant_id", "timestamptz(3)", "outbox", "tool"):
            if marker not in schema:
                add(
                    failures,
                    repository_name,
                    "agent-durability",
                    f"database/schema.sql lacks required durability marker {marker!r}",
                )
