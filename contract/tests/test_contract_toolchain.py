import json
import tomllib
from pathlib import Path

import yaml


ROOT = Path(__file__).parents[2]


def test_consumer_registry_rejects_duplicate_names() -> None:
    def reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            assert key not in result, f"duplicate consumer registry key: {key}"
            result[key] = value
        return result

    json.loads(
        (ROOT / "contract/consumers.yaml").read_text(),
        object_pairs_hook=reject_duplicate_keys,
    )


def test_contract_toolchain_is_exactly_pinned() -> None:
    package = json.loads((ROOT / "package.json").read_text())
    assert package["packageManager"] == "pnpm@11.2.2"
    assert package["engines"] == {"node": ">=22 <25"}
    assert package["devDependencies"] == {
        "@bufbuild/buf": "1.72.0",
        "@bufbuild/protoc-gen-es": "2.14.0",
        "@redocly/cli": "2.46.1",
    }
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())
    assert project["project"]["requires-python"] == ">=3.11,<3.14"
    assert project["project"]["dependencies"] == [
        "grpcio-tools==1.76.0",
        "protobuf==6.33.6",
        "PyYAML==6.0.3",
    ]
    assert yaml.safe_load((ROOT / "contract/buf.yaml").read_text()) == {
        "version": "v2",
            "modules": [{"path": "proto", "excludes": ["proto/kokoro/credit"]}],
        "lint": {"use": ["STANDARD"]},
        "breaking": {
            "use": ["FILE"],
            "except": ["FIELD_SAME_ONEOF"],
        },
    }


def test_contract_toolchain_commands_are_local_and_fail_closed() -> None:
    package = json.loads((ROOT / "package.json").read_text())
    assert package["scripts"] == {
        "contract:format": "buf format --diff --exit-code contract",
        "contract:lint": "buf lint contract",
        "contract:render": "uv run python scripts/contract/render_slice_a.py --manifest contract/slice-a-contract-manifest.yaml --write",
        "contract:check": "uv run python scripts/contract/render_slice_a.py --manifest contract/slice-a-contract-manifest.yaml --check",
    }
    assert (ROOT / ".node-version").read_text() == "22\n"
    workspace = yaml.safe_load((ROOT / "pnpm-workspace.yaml").read_text())
    assert workspace == {
        "allowBuilds": {"@bufbuild/buf": True},
        "minimumReleaseAgeExclude": [
            "@bufbuild/protobuf@2.14.0",
            "@bufbuild/protoc-gen-es@2.14.0",
            "@bufbuild/protoplugin@2.14.0",
        ],
    }


def test_contract_ci_runs_the_frozen_source_only_gate() -> None:
    workflow = (ROOT / ".github/workflows/contract.yml").read_text()
    assert "python3 contract/check.py" not in workflow
    assert "kokoro-session" not in workflow
    assert "fetch-depth: 0" in workflow
    for command in (
        "pnpm install --frozen-lockfile",
        "uv sync --frozen --group dev",
        "cmp docs/superpowers/specs/2026-08-14-slice-a-contract-manifest.yaml contract/slice-a-contract-manifest.yaml",
        "uv run --frozen python scripts/contract/render_slice_a.py --manifest contract/slice-a-contract-manifest.yaml --check",
        "pnpm exec buf format --diff --exit-code contract/proto",
        "pnpm exec buf lint contract",
        "pnpm exec buf breaking contract --against contract/breaking/slice-a-v1.binpb",
        "pnpm exec redocly lint contract/openapi/slice-a-web-v1.yaml",
        "uv run --frozen pytest contract/tests scripts/contract/tests -q",
    ):
        assert command in workflow


def test_database_roadmap_checks_consumers_from_detached_contract_toolchain() -> None:
    roadmap = (
        ROOT / "docs/superpowers/plans/2026-08-14-slice-a-root-database-contracts-plan.md"
    ).read_text()
    assert 'git worktree add --detach "$CONTRACT_WORKTREE" "$ROOT_CONTRACT_COMMIT"' in roadmap
    assert '"root-e2e":"$ROOT_CURRENT"' in roadmap
    assert '--source-root "$CONTRACT_WORKTREE"' in roadmap
    assert '(cd "$CONTRACT_WORKTREE" && pnpm install --frozen-lockfile && uv sync --frozen --group dev)' in roadmap

    web_roadmap = (
        ROOT / "docs/superpowers/plans/2026-08-14-slice-a-web-e2e-promotion-plan.md"
    ).read_text()
    assert '--source-root "$(git rev-parse --show-toplevel)"' not in web_roadmap
    assert web_roadmap.count('git worktree add --detach "$CONTRACT_WORKTREE" "$ROOT_CONTRACT_COMMIT"') >= 3
    assert web_roadmap.count('--source-root "$CONTRACT_WORKTREE"') >= 3
    assert '--consumer root-e2e --repo "$ROOT_CURRENT" --check' in web_roadmap
    assert 'candidate Root and promoted gitlinks are output targets only' in web_roadmap
    assert web_roadmap.count('test "$ROOT_CONTRACT_COMMIT" = "$(git log -1 --format=%H -- contract)"') >= 3
    assert "Replace the floating sibling-`main` checkouts" not in web_roadmap
    assert "submodules: recursive" in web_roadmap
    assert "KOKORO_SUBMODULE_TOKEN" in web_roadmap
    barrier = (
        ROOT / "docs/superpowers/plans/2026-08-14-slice-a-contract-manifest-barrier-roadmap.md"
    ).read_text()
    master = (
        ROOT / "docs/superpowers/plans/2026-08-14-sql-backed-chat-slice-a-master-plan.md"
    ).read_text()
    rule = "Every child write generation runs from a detached exact contract-source worktree"
    assert rule in barrier
    assert rule in master
