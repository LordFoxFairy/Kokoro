from __future__ import annotations

import copy
import gzip
import importlib.util
import json
import shutil
import subprocess
import tarfile
from base64 import b64encode
from dataclasses import dataclass
from hashlib import sha256, sha512
from io import BytesIO
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


@dataclass
class ReplaceRefFixture:
    inventory: InventoryFixture
    original_commit: str
    original_blob: bytes


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


def test_default_topology_baseline_declares_16_edges_and_no_violation() -> None:
    module_path = ROOT / "scripts/governance/contract_inventory.py"
    spec = importlib.util.spec_from_file_location("contract_inventory", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert module.EXPECTED_EDGE_IDS == frozenset(
        {
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
        }
    )
    assert module.EXPECTED_VIOLATION_IDS == frozenset()


def test_scheduler_event_edges_pin_scheduler_owned_contract() -> None:
    inventory = json.loads(
        (ROOT / "verification/contracts/consumer-inventory.json").read_text()
    )
    edges = {edge["id"]: edge for edge in inventory["edges"]}
    scheduler_owner = edges["EDGE-BFF-SCHEDULER"]["owner"]
    # The live inventory can advance its pin; the compatibility verifier still
    # checks the exact gitlink, blob digest and version for all three edges.
    assert scheduler_owner["name"] == "kokoro-scheduler"
    assert scheduler_owner["repository_path"] == "apps/kokoro-scheduler"
    assert scheduler_owner["contract_path"] == "contract/openapi/v1/openapi.yaml"
    assert edges["EDGE-SCHEDULER-BFF"]["owner"] == scheduler_owner
    assert edges["EDGE-SCHEDULER-AGENT"]["owner"] == scheduler_owner
    assert "apps/kokoro-bff" in {
        reference["repository_path"]
        for reference in edges["EDGE-SCHEDULER-BFF"]["evidence"]
    }
    assert "apps/kokoro-agent" in {
        reference["repository_path"]
        for reference in edges["EDGE-SCHEDULER-AGENT"]["evidence"]
    }


@pytest.fixture()
def fixture(tmp_path: Path) -> InventoryFixture:
    root = tmp_path / "root"
    root.mkdir()
    run(root, "git", "init")
    run(root, "git", "config", "user.email", "tests@kokoro.local")
    run(root, "git", "config", "user.name", "Kokoro Tests")
    owner_contract = b'{"openapi":"3.1.0","info":{"version":"1.0.0"}}\n'
    owner_go_mod = b"module example.com/owner\n\ngo 1.26.8\n"
    consumer_source = b'export const ownerVersion = "v1";\n'
    consumer_node_version = b"22.22.2\n"
    consumer_package = (
        b'{"version":"7.16.0","metadata":{"undici":"7.16.0"},'
        b'"dependencies":{"undici":"7.16.0","openapi-typescript":"7.10.1"},'
        b'"devDependencies":{"openapi-typescript":"7.10.1",'
        b'"undici":"7.16.0"}}\n'
    )
    owner_sha = commit_child(
        root,
        "owner",
        {"contract/openapi.json": owner_contract, "go.mod": owner_go_mod},
    )
    consumer_sha = commit_child(
        root,
        "consumer",
        {
            "src/client.ts": consumer_source,
            ".node-version": consumer_node_version,
            "package.json": consumer_package,
            "config/versions.json": consumer_package,
        },
    )
    run(
        root,
        "git",
        "update-index",
        "--add",
        "--cacheinfo",
        "160000",
        owner_sha,
        "apps/owner",
    )
    run(
        root,
        "git",
        "update-index",
        "--add",
        "--cacheinfo",
        "160000",
        consumer_sha,
        "apps/consumer",
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
        "edges": [
            {
                "id": "EDGE-CONSUMER-OWNER",
                "caller": "consumer",
                "owner": {
                    "name": "owner",
                    "repository_path": "apps/owner",
                    "repository_commit": owner_sha,
                    "contract_version": "1.0.0",
                    "contract_path": "contract/openapi.json",
                    "contract_sha256": sha256(owner_contract).hexdigest(),
                },
                "protocol": "http-openapi",
                "code_generator_version": "openapi-typescript@7.10.1",
                "runtime_package_version": "undici@7.16.0",
                "state": "active",
                "reason": "Generated client calls the owner v1 contract.",
                "evidence": [
                    {
                        "repository_path": "apps/consumer",
                        "repository_commit": consumer_sha,
                        "path": "src/client.ts",
                        "sha256": sha256(consumer_source).hexdigest(),
                    }
                ],
                "version_assertions": [
                    {
                        "field": "code_generator_version",
                        "declared_value": "openapi-typescript@7.10.1",
                        "package_name": "openapi-typescript",
                        "version": "7.10.1",
                        "manifest_kind": "npm-package-json",
                        "repository_path": "apps/consumer",
                        "repository_commit": consumer_sha,
                        "path": "package.json",
                        "sha256": sha256(consumer_package).hexdigest(),
                        "json_checks": [
                            {
                                "pointer": "/devDependencies/openapi-typescript",
                                "expected": "7.10.1",
                            }
                        ],
                    },
                    {
                        "field": "runtime_package_version",
                        "declared_value": "undici@7.16.0",
                        "package_name": "undici",
                        "version": "7.16.0",
                        "manifest_kind": "npm-package-json",
                        "repository_path": "apps/consumer",
                        "repository_commit": consumer_sha,
                        "path": "package.json",
                        "sha256": sha256(consumer_package).hexdigest(),
                        "json_checks": [
                            {
                                "pointer": "/dependencies/undici",
                                "expected": "7.16.0",
                            }
                        ],
                    },
                ],
            }
        ],
        "violations": [],
    }
    inventory_fixture = InventoryFixture(module, root, manifest_path, data)
    inventory_fixture.write()
    return inventory_fixture


def use_plain_node_runtime(fixture: InventoryFixture) -> dict[str, object]:
    edge = fixture.data["edges"][0]
    consumer_commit = edge["evidence"][0]["repository_commit"]
    assertion = {
        "field": "runtime_package_version",
        "declared_value": "node@22.22.2",
        "package_name": "node",
        "version": "22.22.2",
        "manifest_kind": "plain-version-file",
        "repository_path": "apps/consumer",
        "repository_commit": consumer_commit,
        "path": ".node-version",
        "sha256": sha256(b"22.22.2\n").hexdigest(),
    }
    edge["runtime_package_version"] = "node@22.22.2"
    edge["version_assertions"][1] = assertion
    return assertion


def use_event_producer_runtime(fixture: InventoryFixture) -> dict[str, object]:
    edge = fixture.data["edges"][0]
    edge["protocol"] = "http-event"
    owner = edge["owner"]
    assertion = {
        "declared_value": "go@1.26.8",
        "package_name": "go",
        "version": "1.26.8",
        "manifest_kind": "go-mod",
        "repository_path": owner["repository_path"],
        "repository_commit": owner["repository_commit"],
        "path": "go.mod",
        "sha256": sha256(b"module example.com/owner\n\ngo 1.26.8\n").hexdigest(),
    }
    edge["producer_runtime_assertion"] = assertion
    return assertion


@pytest.fixture()
def replace_ref_fixture(fixture: InventoryFixture) -> ReplaceRefFixture:
    owner = fixture.data["edges"][0]["owner"]
    original_commit = owner["repository_commit"]
    original_blob = b'{"openapi":"3.1.0","info":{"version":"1.0.0"}}\n'
    replacement_blob = b'{"openapi":"replaced"}\n'
    repository = fixture.root / "apps/owner"
    (repository / "contract/openapi.json").write_bytes(replacement_blob)
    run(repository, "git", "add", "contract/openapi.json")
    run(repository, "git", "commit", "-m", "test: add replacement contract")
    replacement_commit = run(repository, "git", "rev-parse", "HEAD")
    run(repository, "git", "replace", original_commit, replacement_commit)

    replaced = subprocess.run(
        ["git", "show", "--end-of-options", f"{original_commit}:contract/openapi.json"],
        cwd=repository,
        capture_output=True,
        check=True,
    ).stdout
    assert replaced == replacement_blob
    return ReplaceRefFixture(fixture, original_commit, original_blob)


def test_matching_gitlink_blobs_and_active_edge_return_no_errors(fixture) -> None:
    assert fixture.module.verify_inventory(fixture.root, fixture.manifest_path) == []


def test_git_blob_ignores_local_replace_refs(
    replace_ref_fixture: ReplaceRefFixture,
) -> None:
    fixture = replace_ref_fixture.inventory
    assert (
        fixture.module.git_blob(
            fixture.root,
            "apps/owner",
            replace_ref_fixture.original_commit,
            "contract/openapi.json",
        )
        == replace_ref_fixture.original_blob
    )


def test_verify_inventory_ignores_local_replace_refs(
    replace_ref_fixture: ReplaceRefFixture,
) -> None:
    assert replace_ref_fixture.inventory.verify() == []


def test_owner_commit_drift_is_reported(fixture) -> None:
    fixture.data["edges"][0]["owner"]["repository_commit"] = "0" * 40
    fixture.write()
    errors = fixture.verify()
    assert any("owner gitlink" in error for error in errors)
    assert not any("missing commit blob" in error for error in errors)


def test_commit_option_injection_is_rejected_without_file_side_effect(fixture) -> None:
    side_effect = fixture.root / "git-show-side-effect"
    injected_output = Path(f"{side_effect}:blob")
    fixture.data["edges"][0]["owner"]["repository_commit"] = f"--output={side_effect}"
    fixture.data["edges"][0]["owner"]["contract_path"] = "blob"

    errors = fixture.verify()
    with pytest.raises(
        ValueError, match="canonical 40 or 64 character hexadecimal OID"
    ):
        fixture.module.git_blob(
            fixture.root, "apps/owner", f"--output={side_effect}", "blob"
        )

    assert any(
        "canonical 40 or 64 character hexadecimal OID" in error for error in errors
    )
    assert not injected_output.exists()


def test_uninitialized_child_checkout_is_reported_as_stable_error(fixture) -> None:
    shutil.rmtree(fixture.root / "apps/owner")

    errors = fixture.verify()

    assert any("child repository checkout is unavailable" in error for error in errors)


def test_missing_root_git_index_is_reported_as_stable_error(fixture) -> None:
    errors = fixture.module.verify_inventory(
        fixture.root / "missing-root", fixture.manifest_path
    )

    assert any("Root git index is unavailable" in error for error in errors)


@pytest.mark.parametrize("length", [40, 64])
def test_canonical_object_id_accepts_sha1_and_sha256_lengths(
    fixture, length: int
) -> None:
    object_id = "a" * length
    assert fixture.module._canonical_object_id(object_id) == object_id


def test_invalid_utf8_inventory_is_reported_as_stable_error(fixture) -> None:
    fixture.manifest_path.write_bytes(b"\xff")

    assert fixture.module.verify_inventory(fixture.root, fixture.manifest_path) == [
        "inventory: inventory must be UTF-8 JSON"
    ]


@pytest.mark.parametrize(
    ("assertion_index", "repository_name"),
    [(0, "invalid-generator"), (1, "invalid-runtime")],
)
def test_invalid_utf8_version_evidence_is_reported_without_traceback(
    fixture, assertion_index: int, repository_name: str
) -> None:
    invalid_blob = b"\xff"
    repository_commit = commit_child(
        fixture.root, repository_name, {"package.json": invalid_blob}
    )
    run(
        fixture.root,
        "git",
        "update-index",
        "--add",
        "--cacheinfo",
        "160000",
        repository_commit,
        f"apps/{repository_name}",
    )
    assertion = fixture.data["edges"][0]["version_assertions"][assertion_index]
    assertion["repository_path"] = f"apps/{repository_name}"
    assertion["repository_commit"] = repository_commit
    assertion["sha256"] = sha256(invalid_blob).hexdigest()

    errors = fixture.verify()

    assert any("version evidence must be UTF-8 JSON" in error for error in errors)


def test_plain_version_file_accepts_exact_node_semver(fixture) -> None:
    use_plain_node_runtime(fixture)

    assert fixture.verify() == []


def test_plain_version_file_reads_commit_blob_not_dirty_worktree(fixture) -> None:
    use_plain_node_runtime(fixture)
    (fixture.root / "apps/consumer/.node-version").write_text("999.0.0\n")

    assert fixture.verify() == []


def test_plain_version_file_ignores_local_replace_refs(fixture) -> None:
    use_plain_node_runtime(fixture)
    edge = fixture.data["edges"][0]
    original_commit = edge["evidence"][0]["repository_commit"]
    repository = fixture.root / "apps/consumer"
    (repository / ".node-version").write_text("999.0.0\n")
    run(repository, "git", "add", ".node-version")
    run(repository, "git", "commit", "-m", "test: replacement node version")
    replacement_commit = run(repository, "git", "rev-parse", "HEAD")
    run(repository, "git", "replace", original_commit, replacement_commit)

    assert fixture.verify() == []


def test_plain_version_file_requires_canonical_filename(fixture) -> None:
    assertion = use_plain_node_runtime(fixture)
    assertion["path"] = "config/.node-version"

    assert any("path must be .node-version" in error for error in fixture.verify())


@pytest.mark.parametrize("content", [b">=22.22.2\n", b"22.x\n", b"v22.22.2\n"])
def test_plain_version_file_rejects_ranges_and_noncanonical_versions(
    fixture, content: bytes
) -> None:
    assertion = use_plain_node_runtime(fixture)
    repository_commit = commit_child(
        fixture.root, "node-runtime", {".node-version": content}
    )
    run(
        fixture.root,
        "git",
        "update-index",
        "--add",
        "--cacheinfo",
        "160000",
        repository_commit,
        "apps/node-runtime",
    )
    assertion.update(
        repository_path="apps/node-runtime",
        repository_commit=repository_commit,
        sha256=sha256(content).hexdigest(),
    )

    assert any("exact semantic version" in error for error in fixture.verify())


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("declared_value", "node@22.22.3"),
        ("package_name", "deno"),
        ("version", "22.22.3"),
    ],
)
def test_plain_version_file_rejects_wrong_declaration_package_or_version(
    fixture, key: str, value: str
) -> None:
    assertion = use_plain_node_runtime(fixture)
    assertion[key] = value

    assert fixture.verify()


def test_plain_version_file_rejects_invalid_utf8(fixture) -> None:
    assertion = use_plain_node_runtime(fixture)
    invalid_blob = b"\xff"
    repository_commit = commit_child(
        fixture.root, "invalid-node-runtime", {".node-version": invalid_blob}
    )
    run(
        fixture.root,
        "git",
        "update-index",
        "--add",
        "--cacheinfo",
        "160000",
        repository_commit,
        "apps/invalid-node-runtime",
    )
    assertion.update(
        repository_path="apps/invalid-node-runtime",
        repository_commit=repository_commit,
        sha256=sha256(invalid_blob).hexdigest(),
    )

    assert any(
        "plain version evidence must be UTF-8" in error for error in fixture.verify()
    )


def test_plain_version_file_rejects_mismatched_gitlink(fixture) -> None:
    assertion = use_plain_node_runtime(fixture)
    assertion["repository_commit"] = fixture.data["edges"][0]["owner"][
        "repository_commit"
    ]

    assert any("evidence gitlink" in error for error in fixture.verify())


def test_go_mod_accepts_exact_go_directive_for_event_producer(fixture) -> None:
    use_event_producer_runtime(fixture)

    assert fixture.verify() == []


def test_go_mod_reads_commit_blob_not_dirty_worktree(fixture) -> None:
    use_event_producer_runtime(fixture)
    (fixture.root / "apps/owner/go.mod").write_text(
        "module example.com/owner\n\ngo 9.9.9\n"
    )

    assert fixture.verify() == []


def test_go_mod_requires_canonical_path(fixture) -> None:
    assertion = use_event_producer_runtime(fixture)
    assertion["path"] = "config/go.mod"

    assert any("path must be go.mod" in error for error in fixture.verify())


@pytest.mark.parametrize(
    "content",
    [
        b"module example.com/owner\n\ngo >=1.26.8\n",
        b"module example.com/owner\n\ntoolchain go1.26.8\n",
        b"module example.com/owner\n\ngo 1.26.8\ngo 1.26.8\n",
    ],
)
def test_go_mod_rejects_range_toolchain_substitute_and_duplicate_directive(
    fixture, content: bytes
) -> None:
    assertion = use_event_producer_runtime(fixture)
    repository_commit = commit_child(fixture.root, "go-runtime", {"go.mod": content})
    run(
        fixture.root,
        "git",
        "update-index",
        "--add",
        "--cacheinfo",
        "160000",
        repository_commit,
        "apps/go-runtime",
    )
    edge = fixture.data["edges"][0]
    edge["owner"]["repository_path"] = "apps/go-runtime"
    edge["owner"]["repository_commit"] = repository_commit
    edge["owner"]["contract_path"] = "go.mod"
    edge["owner"]["contract_sha256"] = sha256(content).hexdigest()
    assertion.update(
        repository_path="apps/go-runtime",
        repository_commit=repository_commit,
        sha256=sha256(content).hexdigest(),
    )

    assert any(
        "exactly one canonical go directive" in error for error in fixture.verify()
    )


@pytest.mark.parametrize(
    "hidden_directive",
    [
        b"go\t1.25.0\n",
        b"\tgo 1.25.0\n",
        b"  go\t1.25.0\n",
    ],
)
def test_go_mod_rejects_duplicate_directive_with_noncanonical_whitespace(
    fixture, hidden_directive: bytes
) -> None:
    assertion = use_event_producer_runtime(fixture)
    content = b"module example.com/owner\n\ngo 1.26.8\n" + hidden_directive
    repository_commit = commit_child(
        fixture.root, "duplicate-go-runtime", {"go.mod": content}
    )
    run(
        fixture.root,
        "git",
        "update-index",
        "--add",
        "--cacheinfo",
        "160000",
        repository_commit,
        "apps/duplicate-go-runtime",
    )
    edge = fixture.data["edges"][0]
    edge["owner"].update(
        repository_path="apps/duplicate-go-runtime",
        repository_commit=repository_commit,
        contract_path="go.mod",
        contract_sha256=sha256(content).hexdigest(),
    )
    assertion.update(
        repository_path="apps/duplicate-go-runtime",
        repository_commit=repository_commit,
        sha256=sha256(content).hexdigest(),
    )

    assert any(
        "exactly one canonical go directive" in error for error in fixture.verify()
    )


def test_producer_runtime_rejects_incompatible_npm_manifest_without_exception(
    fixture,
) -> None:
    assertion = use_event_producer_runtime(fixture)
    edge = fixture.data["edges"][0]
    assertion.update(
        manifest_kind="npm-package-json",
        path="contract/openapi.json",
        sha256=edge["owner"]["contract_sha256"],
        json_checks=[{"pointer": "/dependencies/go", "expected": "1.26.8"}],
    )

    errors = fixture.verify()

    assert any(
        "manifest_kind 'npm-package-json' is not allowed for producer_runtime_version"
        in error
        for error in errors
    )


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("declared_value", "go@1.26.7"),
        ("package_name", "golang"),
        ("version", "1.26.7"),
    ],
)
def test_go_mod_rejects_wrong_declaration_package_or_version(
    fixture, key: str, value: str
) -> None:
    assertion = use_event_producer_runtime(fixture)
    assertion[key] = value

    assert fixture.verify()


def test_go_mod_rejects_invalid_utf8(fixture) -> None:
    assertion = use_event_producer_runtime(fixture)
    invalid_blob = b"\xff"
    repository_commit = commit_child(
        fixture.root, "invalid-go-runtime", {"go.mod": invalid_blob}
    )
    run(
        fixture.root,
        "git",
        "update-index",
        "--add",
        "--cacheinfo",
        "160000",
        repository_commit,
        "apps/invalid-go-runtime",
    )
    edge = fixture.data["edges"][0]
    edge["owner"]["repository_path"] = "apps/invalid-go-runtime"
    edge["owner"]["repository_commit"] = repository_commit
    edge["owner"]["contract_path"] = "go.mod"
    edge["owner"]["contract_sha256"] = sha256(invalid_blob).hexdigest()
    assertion.update(
        repository_path="apps/invalid-go-runtime",
        repository_commit=repository_commit,
        sha256=sha256(invalid_blob).hexdigest(),
    )

    assert any("go.mod evidence must be UTF-8" in error for error in fixture.verify())


def test_http_event_requires_producer_runtime_assertion(fixture) -> None:
    fixture.data["edges"][0]["protocol"] = "http-event"

    assert any(
        "missing producer_runtime_assertion" in error for error in fixture.verify()
    )


def test_non_event_rejects_producer_runtime_assertion(fixture) -> None:
    use_event_producer_runtime(fixture)
    fixture.data["edges"][0]["protocol"] = "http-openapi"

    assert any(
        "producer_runtime_assertion is only valid" in error
        for error in fixture.verify()
    )


def test_event_producer_assertion_must_match_contract_owner(fixture) -> None:
    assertion = use_event_producer_runtime(fixture)
    assertion["repository_path"] = "apps/consumer"
    assertion["repository_commit"] = fixture.data["edges"][0]["evidence"][0][
        "repository_commit"
    ]

    assert any("must match contract owner" in error for error in fixture.verify())


def test_producer_assertion_cannot_replace_consumer_runtime_assertion(fixture) -> None:
    use_event_producer_runtime(fixture)
    edge = fixture.data["edges"][0]
    edge["version_assertions"] = [edge["version_assertions"][0]]

    assert any(
        "missing version assertion for runtime_package_version" in error
        for error in fixture.verify()
    )


def test_contract_digest_uses_commit_blob_not_dirty_worktree(fixture) -> None:
    (fixture.root / "apps/owner/contract/openapi.json").write_text("dirty")
    assert fixture.verify() == []


@pytest.mark.parametrize("state", ["active", "broken"])
def test_openapi_owner_version_must_match_frozen_contract_info(fixture, state) -> None:
    edge = fixture.data["edges"][0]
    edge["state"] = state
    edge["owner"]["contract_version"] = "0.9.0"

    assert any(
        "contract_version '0.9.0' != OpenAPI info.version '1.0.0'" in error
        for error in fixture.verify()
    )


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        (b'{"openapi":"3.1.0","info":{"version":"1.0.0"}}', "1.0.0"),
        (
            b"openapi: 3.1.0\ninfo:\n  title: Example\n  version: '2.0.0'\npaths: {}\n",
            "2.0.0",
        ),
    ],
)
def test_openapi_info_version_reads_json_and_canonical_yaml(
    fixture, source, expected
) -> None:
    assert fixture.module._openapi_info_version(source) == expected


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
    fixture.data["violations"] = [
        {
            "id": "EDGE-ILLEGAL",
            "caller": "web",
            "target": "iam",
            "reason": "Web bypasses BFF.",
            "evidence": fixture.data["edges"][0]["evidence"],
        }
    ]
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


def test_unavailable_npm_blob_does_not_misclassify_valid_json_checks(fixture) -> None:
    assertion = fixture.data["edges"][0]["version_assertions"][1]
    assertion["path"] = "missing/package.json"

    errors = fixture.verify()

    assert any("missing commit blob" in error for error in errors)
    assert not any("json_checks must be a non-empty list" in error for error in errors)
    assert not any("version evidence must be UTF-8 JSON" in error for error in errors)


@pytest.mark.parametrize("checks", [[], {}])
@pytest.mark.parametrize("missing_blob", [False, True])
def test_invalid_npm_json_checks_are_rejected_even_with_unavailable_blob(
    fixture, checks: object, missing_blob: bool
) -> None:
    assertion = fixture.data["edges"][0]["version_assertions"][1]
    assertion["json_checks"] = checks
    if missing_blob:
        assertion["path"] = "missing/package.json"

    errors = fixture.verify()

    assert any("json_checks must be a non-empty list" in error for error in errors)
    assert any("missing commit blob" in error for error in errors) is missing_blob


def test_unrelated_json_pointer_cannot_prove_package_version(fixture) -> None:
    assertion = fixture.data["edges"][0]["version_assertions"][1]
    assertion["json_checks"] = [{"pointer": "/metadata/undici", "expected": "7.16.0"}]

    assert any("canonical npm pointer" in error for error in fixture.verify())


@pytest.mark.parametrize(
    ("assertion_index", "pointer", "expected"),
    [
        (0, "/dependencies/openapi-typescript", "7.10.1"),
        (1, "/devDependencies/undici", "7.16.0"),
    ],
)
def test_wrong_npm_dependency_section_is_rejected(
    fixture, assertion_index: int, pointer: str, expected: str
) -> None:
    assertion = fixture.data["edges"][0]["version_assertions"][assertion_index]
    assertion["json_checks"] = [{"pointer": pointer, "expected": expected}]

    assert any("canonical npm pointer" in error for error in fixture.verify())


def test_non_package_json_version_evidence_is_rejected(fixture) -> None:
    assertion = fixture.data["edges"][0]["version_assertions"][1]
    assertion["path"] = "config/versions.json"

    assert any(
        "evidence basename must be package.json" in error for error in fixture.verify()
    )


def test_unknown_version_manifest_kind_is_rejected(fixture) -> None:
    fixture.data["edges"][0]["version_assertions"][1]["manifest_kind"] = "generic-json"

    assert any("unknown manifest_kind" in error for error in fixture.verify())


def test_scoped_package_name_uses_rfc6901_escaping(fixture) -> None:
    assert (
        fixture.module._npm_package_pointer("runtime_package_version", "@scope/package")
        == "/dependencies/@scope~1package"
    )


def test_wrong_assertion_package_name_is_rejected(fixture) -> None:
    fixture.data["edges"][0]["version_assertions"][1]["package_name"] = "fake-runtime"

    assert any("package_name" in error for error in fixture.verify())


def test_duplicate_version_assertion_field_is_rejected(fixture) -> None:
    assertions = fixture.data["edges"][0]["version_assertions"]
    assertions.append(copy.deepcopy(assertions[1]))

    assert any("duplicate version assertion" in error for error in fixture.verify())


@pytest.mark.parametrize(
    ("declared_value", "package_name", "version"),
    [
        ("@scope/package@1.2.3", "@scope/package", "1.2.3"),
        ("node:http@22", "node:http", "22"),
        ("go:net/http@1.26.8", "go:net/http", "1.26.8"),
    ],
)
def test_declared_package_version_splits_on_last_at_sign(
    fixture, declared_value: str, package_name: str, version: str
) -> None:
    assert fixture.module._split_package_version(declared_value) == (
        package_name,
        version,
    )


def test_multi_package_version_requires_a_packages_array(fixture) -> None:
    with pytest.raises(ValueError, match="packages array"):
        fixture.module._split_package_version("next@16.2.6+ai@7.0.92")


def test_browser_same_origin_generator_exemption_does_not_require_assertion(
    fixture,
) -> None:
    edge = fixture.data["edges"][0]
    edge["id"] = "EDGE-BROWSER-WEB"
    edge["protocol"] = "same-origin-http"
    edge["code_generator_version"] = "not-applicable:same-origin-route"
    edge["version_assertions"] = [edge["version_assertions"][1]]
    fixture.module.EXPECTED_EDGE_IDS = frozenset({"EDGE-BROWSER-WEB"})

    assert fixture.verify() == []


def test_generator_exemption_is_rejected_for_other_edges(fixture) -> None:
    edge = fixture.data["edges"][0]
    edge["code_generator_version"] = "not-applicable:same-origin-route"
    edge["version_assertions"] = [edge["version_assertions"][1]]

    assert any("generator exemption" in error for error in fixture.verify())


def test_http_event_cannot_use_generator_exemption(fixture) -> None:
    edge = fixture.data["edges"][0]
    edge["code_generator_version"] = "not-applicable:same-origin-route"
    edge["version_assertions"] = [edge["version_assertions"][1]]
    use_event_producer_runtime(fixture)

    assert any("generator exemption" in error for error in fixture.verify())


_SYSTEM_CONTRACT = "contract/openapi/system.openapi.json"
_SYSTEM_PROVENANCE = "contract/provenance.json"
_SYSTEM_CLIENT = "src/kokoro_agent/clients/system.py"
_SYSTEM_OPERATIONS = (
    "POST /v1/system/model-catalog/resolve",
    "POST /v1/system/model-catalog/credentials/read",
)
_AGENT_SYSTEM_LOCK = b"""version = 1
revision = 3
requires-python = ">=3.11"

[[package]]
name = "httpx"
version = "0.28.1"
source = { registry = "https://pypi.org/simple" }

[[package]]
name = "kokoro-agent"
version = "2.0.0"
source = { editable = "." }
dependencies = [{ name = "httpx" }]
"""


def use_handwritten_agent_system(
    fixture: InventoryFixture,
    *,
    lock: bytes = _AGENT_SYSTEM_LOCK,
    lock_path: str = "uv.lock",
    owner_repo: str = "kokoro-system",
    contract_path: str = _SYSTEM_CONTRACT,
    receipt_change: str | None = None,
) -> dict[str, object]:
    def json_bytes(document: object) -> bytes:
        return (json.dumps(document) + "\n").encode()

    contract = json_bytes(
        {
            "openapi": "3.1.0",
            "info": {"title": "System", "version": "6.1.0"},
            "paths": {
                operation.split(" ", 1)[1]: {"post": {"responses": {"200": {}}}}
                for operation in _SYSTEM_OPERATIONS
            },
        }
    )
    contract_digest = sha256(contract).hexdigest()
    owner_sources = {
        "scripts/generate-system-openapi.ts": b"export {};\n",
        "src/modules/model-catalog/schemas/resolve.schema.ts": b"export const resolve = {};\n",
    }
    source_digests = {
        path: sha256(content).hexdigest() for path, content in owner_sources.items()
    }
    if receipt_change == "source_blob":
        source_digests[next(iter(source_digests))] = "0" * 64
    elif receipt_change == "missing_source_blob":
        owner_sources.pop(next(iter(source_digests)))
    owner_provenance = json_bytes(
        {
            "authority": "runtime Zod HTTP schemas",
            "version": 2,
            "openapi": {
                "file": contract_path.removeprefix("contract/"),
                "sha256": contract_digest,
                "source": "runtime Zod",
                "sourceSha256": source_digests,
            },
        }
    )
    owner_sha = commit_child(
        fixture.root,
        owner_repo,
        {
            contract_path: contract,
            _SYSTEM_PROVENANCE: owner_provenance,
            **owner_sources,
        },
    )
    receipt = {
        "owner": "kokoro-system",
        "contract": contract_path,
        "version": "6.1.0",
        "source_commit": owner_sha,
        "sha256": contract_digest,
        "provenance": {
            "path": _SYSTEM_PROVENANCE,
            "sha256": sha256(owner_provenance).hexdigest(),
        },
        "source_sha256": dict(source_digests),
        "operations": list(_SYSTEM_OPERATIONS),
    }
    if receipt_change == "owner_pin":
        receipt["source_commit"] = "0" * 40
    elif receipt_change == "contract_version":
        receipt["version"] = "6.0.0"
    elif receipt_change == "contract_digest":
        receipt["sha256"] = "0" * 64
    elif receipt_change == "operation":
        receipt["operations"][1] = "GET /v1/system/model-catalog/catalog"
    elif receipt_change == "source_map":
        receipt["source_sha256"].pop(next(iter(source_digests)))
    elif receipt_change == "owner_provenance":
        receipt["provenance"]["sha256"] = "0" * 64
    agent_provenance = json_bytes({"consumer_dependencies": [receipt]})
    if receipt_change == "malformed_json":
        agent_provenance = b'{"consumer_dependencies": [\n'
    elif receipt_change == "nonfinite_json":
        agent_provenance = b'{"version": NaN, ' + agent_provenance[1:]
    agent_files = {
        _SYSTEM_CLIENT: b"from httpx import AsyncClient\n",
        _SYSTEM_PROVENANCE: agent_provenance,
        lock_path: lock,
    }
    agent_sha = commit_child(fixture.root, "kokoro-agent", agent_files)
    for name, commit in ((owner_repo, owner_sha), ("kokoro-agent", agent_sha)):
        run(
            fixture.root,
            "git",
            "update-index",
            "--add",
            "--cacheinfo",
            "160000",
            commit,
            f"apps/{name}",
        )

    def agent_reference(path: str) -> dict[str, str]:
        return {
            "repository_path": "apps/kokoro-agent",
            "repository_commit": agent_sha,
            "path": path,
            "sha256": sha256(agent_files[path]).hexdigest(),
        }

    edge = fixture.data["edges"][0]
    edge.update(
        id="EDGE-AGENT-SYSTEM",
        caller="Agent",
        owner={
            "name": "kokoro-system",
            "repository_path": f"apps/{owner_repo}",
            "repository_commit": owner_sha,
            "contract_version": "6.1.0",
            "contract_path": contract_path,
            "contract_sha256": contract_digest,
        },
        code_generator_version="not-applicable:handwritten-agent-system-http",
        runtime_package_version="httpx@0.28.1",
        reason="The handwritten client consumes two pinned System operations.",
        evidence=[agent_reference(path) for path in agent_files],
        version_assertions=[
            {
                "field": "runtime_package_version",
                "declared_value": "httpx@0.28.1",
                "package_name": "httpx",
                "version": "0.28.1",
                "manifest_kind": "uv-lock",
                **agent_reference(lock_path),
            }
        ],
    )
    fixture.module.EXPECTED_EDGE_IDS = frozenset({"EDGE-AGENT-SYSTEM"})
    return edge


def test_handwritten_agent_system_accepts_pinned_receipt_and_direct_uv_runtime(
    fixture,
) -> None:
    use_handwritten_agent_system(fixture)

    assert fixture.verify() == []


@pytest.mark.parametrize(
    "scope",
    ["edge", "caller", "protocol", "owner_name", "owner_repository", "contract_path"],
)
def test_handwritten_agent_system_generator_exemption_is_edge_local(
    fixture, scope: str
) -> None:
    edge = use_handwritten_agent_system(
        fixture,
        owner_repo="other-system" if scope == "owner_repository" else "kokoro-system",
        contract_path="contract/openapi/other.openapi.json"
        if scope == "contract_path"
        else _SYSTEM_CONTRACT,
    )
    if scope == "edge":
        edge["id"] = "EDGE-AGENT-CAPABILITY"
        fixture.module.EXPECTED_EDGE_IDS = frozenset({edge["id"]})
    elif scope == "caller":
        edge["caller"] = "BFF"
    elif scope == "protocol":
        edge["protocol"] = "same-origin-http"
    elif scope == "owner_name":
        edge["owner"]["name"] = "other-system"

    assert any("generator exemption" in error for error in fixture.verify())


@pytest.mark.parametrize(
    "lock",
    [
        pytest.param(
            _AGENT_SYSTEM_LOCK.replace(
                b'dependencies = [{ name = "httpx" }]',
                b'dependencies = [{ name = "adapter" }]\n\n[[package]]\n'
                b'name = "adapter"\nversion = "1.0.0"\n'
                b'source = { registry = "https://pypi.org/simple" }\n'
                b'dependencies = [{ name = "httpx" }]',
            ),
            id="transitive-only",
        ),
        pytest.param(
            _AGENT_SYSTEM_LOCK.replace(
                b'dependencies = [{ name = "httpx" }]',
                b'dependencies = [{ name = "httpx" }, "not-a-package-record"]',
            ),
            id="malformed-direct-dependency-record",
        ),
        pytest.param(
            _AGENT_SYSTEM_LOCK.replace(b'version = "0.28.1"', b'version = "0.29.0"'),
            id="different-runtime-version",
        ),
        pytest.param(
            _AGENT_SYSTEM_LOCK + b'\n[[package]]\nname = "httpx"\nversion = "0.28.2"\n'
            b'source = { registry = "https://pypi.org/simple" }\n',
            id="ambiguous-runtime",
        ),
        pytest.param(
            _AGENT_SYSTEM_LOCK.replace(
                b'version = "0.28.1"',
                b"""version = "0.28.1"\nresolution-markers = ["python_version < '3.0'"]""",
            ),
            id="runtime-is-only-conditionally-resolved",
        ),
        pytest.param(
            _AGENT_SYSTEM_LOCK.replace(b"version = 1", b"version = 2", 1),
            id="unsupported-lock-format",
        ),
        pytest.param(
            _AGENT_SYSTEM_LOCK.replace(b'editable = "."', b'editable = "./other"'),
            id="no-editable-root",
        ),
        pytest.param(
            _AGENT_SYSTEM_LOCK.replace(
                b'registry = "https://pypi.org/simple"', b'directory = "vendor/httpx"'
            ),
            id="non-registry-runtime",
        ),
    ],
)
def test_handwritten_agent_system_rejects_unpinned_uv_runtime(
    fixture, lock: bytes
) -> None:
    use_handwritten_agent_system(fixture, lock=lock)

    assert any("uv.lock" in error for error in fixture.verify())


def test_handwritten_agent_system_requires_agent_root_uv_lock_path(fixture) -> None:
    use_handwritten_agent_system(fixture, lock_path="fixtures/uv.lock")

    assert any("uv.lock" in error for error in fixture.verify())


@pytest.mark.parametrize(
    "receipt_change",
    [
        "owner_pin",
        "contract_version",
        "contract_digest",
        "operation",
        "owner_provenance",
        "source_map",
        "source_blob",
        "missing_source_blob",
        "malformed_json",
        "nonfinite_json",
    ],
)
def test_handwritten_agent_system_rejects_wrong_consumer_receipt(
    fixture, receipt_change: str
) -> None:
    use_handwritten_agent_system(fixture, receipt_change=receipt_change)

    errors = fixture.verify()
    assert len(errors) == 1 and "System consumer receipt" in errors[0], errors
    assert "evidence sha256" not in errors[0]


def use_generated_agent_connect(
    fixture: InventoryFixture, *, drift: str | None = None, platform: bool = False
) -> None:
    def json_bytes(value: object) -> bytes:
        return (json.dumps(value) + "\n").encode()

    owner_name = "kokoro-capability" if platform else "kokoro-storage"
    owner_repo = f"apps/{owner_name}"
    wire_package = "kokoro.platform.v1" if platform else "kokoro.storage.v3"
    edge_id = "EDGE-AGENT-CAPABILITY" if platform else "EDGE-AGENT-STORAGE"
    agent_repo = "apps/kokoro-agent"
    generator = "^0.11.1" if drift == "floating_generator" else "0.11.1"
    common = "kokoro/common/v1/common.proto"
    wire = (
        "kokoro/platform/v1/platform_runtime.proto"
        if platform
        else "kokoro/storage/v3/storage.proto"
    )
    mcp = "kokoro/platform/v1/mcp_runtime.proto"
    custom = "kokoro/platform/v1/custom_api_runtime.proto"
    base_inputs = (common, wire, mcp) if platform else (common, wire)
    owner_proto = "contract/proto/"
    vendor = "contract/platform/v1/" if platform else "contract/storage/v3/"
    pin_path = vendor + "provenance.json"
    vendor_provenance = vendor + "owner-provenance.json"
    owner_provenance = "contract/provenance.json"
    owner_files = {
        owner_proto + common: b'syntax = "proto3";\npackage kokoro.common.v1;\n',
        owner_proto + wire: f'syntax = "proto3";\npackage {wire_package};\n'.encode(),
    }
    if platform:
        owner_files[owner_proto + mcp] = b"// exact MCP protocol\n"
        owner_files[owner_proto + custom] = b"// exact Custom API protocol\n"
    combined = sha256(b"".join(owner_files.values())).hexdigest()
    owner_files[owner_provenance] = json_bytes(
        {
            "authority": "local contract/proto",
            "source": "contract/proto",
            "files": list(base_inputs),
            "combinedSha256": combined,
        }
    )
    owner_sha = commit_child(fixture.root, owner_name, owner_files)
    agent_files = {
        vendor + "proto/" + source: owner_files[owner_proto + source]
        for source in ((*base_inputs, custom) if platform else base_inputs)
    }
    if drift == "owner_vendor":
        # Keep the Agent pin and evidence self-consistent with the wrong bytes.
        agent_files[vendor + "proto/" + (custom if platform else wire)] += (
            b"// stale consumer copy\n"
        )
    codegen = {
        "python": "3.11",
        "buf_bin": "^1.73.0" if drift == "floating_toolchain" else "1.73.0",
        "protoc_gen_py": "0.1.1",
        "protoc_gen_connectrpc": generator,
        "connectrpc_parameter": "io=async",
    }

    def source_pin(source: str) -> dict[str, str]:
        path = vendor + "proto/" + source
        return {
            "owner_path": owner_proto + source,
            "path": path,
            "sha256": sha256(agent_files[path]).hexdigest(),
        }

    if platform:
        config_path = vendor + "codegen.json"
        agent_files[config_path] = json_bytes(
            {
                **{key: codegen[key] for key in codegen if key != "python"},
                "version": "v1",
                "inputs": ["proto/" + source for source in (*base_inputs, custom)],
            }
        )
        special = {
            "custom_api_runtime": {"sources": [source_pin(custom)]},
            "generation_inputs": [
                {
                    "path": config_path,
                    "sha256": sha256(agent_files[config_path]).hexdigest(),
                }
            ],
        }
    else:
        agent_files[vendor_provenance] = owner_files[owner_provenance]
        special = {
            "owner_provenance": {
                "path": vendor_provenance,
                "sha256": sha256(agent_files[vendor_provenance]).hexdigest(),
                "combined_sha256": combined,
            }
        }
    agent_files[pin_path] = json_bytes(
        {
            "owner": "kokoro-platform" if platform else "kokoro-storage",
            "owner_repository": owner_repo,
            "owner_commit": owner_sha,
            "sources": [source_pin(source) for source in base_inputs],
            "codegen": codegen,
            **special,
            "runtime": {"connectrpc": "0.12.1", "protobuf_py": ">=0.3.0,<0.4.0"},
        }
    )
    direct = "wrapper" if drift == "transitive_only" else "connectrpc"
    agent_files["uv.lock"] = f'''version = 1
revision = 3
requires-python = ">=3.11"

[[package]]
name = "connectrpc"
version = "0.12.1"
source = {{ registry = "https://pypi.org/simple" }}

[[package]]
name = "wrapper"
version = "1.0.0"
source = {{ registry = "https://pypi.org/simple" }}
dependencies = [{{ name = "connectrpc" }}]

[[package]]
name = "kokoro-agent"
version = "2.0.0"
source = {{ editable = "." }}
dependencies = [{{ name = "{direct}" }}]
'''.encode()
    agent_files["src/kokoro_agent/clients/storage_transport.py"] = (
        b"from kokoro_agent.generated.kokoro.storage.v3.storage_connect "
        b"import StorageServiceClient\n"
    )
    agent_sha = commit_child(fixture.root, "kokoro-agent", agent_files)
    for repo, commit in ((owner_repo, owner_sha), (agent_repo, agent_sha)):
        run(
            fixture.root,
            "git",
            "update-index",
            "--add",
            "--cacheinfo",
            "160000",
            commit,
            repo,
        )

    def reference(repo: str, path: str) -> dict[str, str]:
        files, commit = (
            (owner_files, owner_sha) if repo == owner_repo else (agent_files, agent_sha)
        )
        return {
            "repository_path": repo,
            "repository_commit": commit,
            "path": path,
            "sha256": sha256(files[path]).hexdigest(),
        }

    edge = fixture.data["edges"][0]
    edge.update(
        id=edge_id,
        caller="Agent",
        owner={
            "name": owner_name,
            "repository_path": owner_repo,
            "repository_commit": owner_sha,
            "contract_version": wire_package,
            "contract_path": owner_proto + wire,
            "contract_sha256": sha256(owner_files[owner_proto + wire]).hexdigest(),
        },
        protocol="connect-proto",
        code_generator_version=f"protoc-gen-connectrpc@{generator}",
        runtime_package_version="connectrpc@0.12.1",
        reason="Generated Agent client consumes the pinned Connect contract.",
        evidence=[
            *(reference(owner_repo, path) for path in owner_files),
            *(reference(agent_repo, path) for path in agent_files),
        ],
        version_assertions=[
            {
                "field": "code_generator_version",
                "declared_value": f"protoc-gen-connectrpc@{generator}",
                "package_name": "protoc-gen-connectrpc",
                "version": generator,
                "manifest_kind": "agent-connect-codegen",
                **reference(agent_repo, pin_path),
            },
            {
                "field": "runtime_package_version",
                "declared_value": "connectrpc@0.12.1",
                "package_name": "connectrpc",
                "version": "0.12.1",
                "manifest_kind": "uv-lock",
                **reference(agent_repo, "uv.lock"),
            },
        ],
    )
    fixture.module.EXPECTED_EDGE_IDS = frozenset({edge_id})


def test_generated_agent_storage_accepts_exact_owner_and_direct_uv_runtime(
    fixture: InventoryFixture,
) -> None:
    use_generated_agent_connect(fixture)

    assert fixture.verify() == []


@pytest.mark.parametrize(
    ("drift", "diagnostic"),
    [
        ("owner_vendor", "vendor"),
        ("transitive_only", "direct runtime"),
        ("floating_generator", "exact semantic version"),
    ],
)
def test_generated_agent_storage_rejects_unpaired_inputs(
    fixture: InventoryFixture, drift: str, diagnostic: str
) -> None:
    use_generated_agent_connect(fixture, drift=drift)

    errors = fixture.verify()
    assert any(diagnostic in error.lower() for error in errors), errors
    assert all("evidence sha256" not in error for error in errors)


@pytest.mark.parametrize("drift", [None, "owner_vendor", "floating_toolchain"])
def test_generated_agent_platform_checks_all_current_vendor_inputs(
    fixture: InventoryFixture,
    drift: str | None,
) -> None:
    use_generated_agent_connect(fixture, drift=drift, platform=True)

    errors = fixture.verify()
    if drift is None:
        assert not errors
    elif drift == "owner_vendor":
        assert any(
            "vendor differs from owner" in error and "custom_api_runtime.proto" in error
            for error in errors
        ), errors
        assert all("evidence sha256" not in error for error in errors)
    else:
        assert any("exact semantic version" in error for error in errors), errors


def use_capability_iam_sdk_archive(
    fixture: InventoryFixture,
    *,
    drift: str | None = None,
) -> dict[str, object]:
    def json_bytes(value: object) -> bytes:
        return (json.dumps(value) + "\n").encode()

    def pack(members: list[tuple[str, bytes]]) -> bytes:
        with BytesIO() as buffer:
            with tarfile.open(fileobj=buffer, mode="w") as archive:
                for name, body in members:
                    entry = tarfile.TarInfo(name)
                    entry.size = len(body)
                    archive.addfile(entry, BytesIO(body))
            return gzip.compress(buffer.getvalue(), mtime=0)

    package = "@kokoro/iam-client"
    version = "^0.21.0" if drift == "version_range" else "0.21.0"
    generator = "@hey-api/openapi-ts"
    generator_version = "0.99.0"
    archive_path = f"vendor/iam/kokoro-iam-client-{version}.tgz"
    provenance_path = "vendor/iam/provenance.json"
    contract_path = (
        "contract/openapi/other.internal.v1.json"
        if drift == "owner_contract_path"
        else "contract/openapi/iam.internal.v1.json"
    )
    sdk_manifest_path = "sdk/package.json"
    config_path = "sdk/openapi-ts.config.ts"
    iam_name = "other-iam" if drift == "owner_repository" else "kokoro-iam"
    iam_repo = f"apps/{iam_name}"
    capability_repo = "apps/kokoro-capability"
    zod_sri = "sha512-" + b64encode(sha512(b"owner zod archive").digest()).decode()
    owner = {
        "package.json": json_bytes(
            {"name": "kokoro-iam", "packageManager": "pnpm@12.3.4"}
        ),
        ".node-version": b"24.20.0\n",
        "pnpm-lock.yaml": f"""lockfileVersion: '9.0'
importers:
  sdk:
    dependencies:
      zod:
        specifier: 4.5.4
        version: 4.5.4
    devDependencies:
      '@hey-api/openapi-ts':
        specifier: 0.99.0
        version: 0.99.0(typescript@6.0.3)

packages:
  zod@4.5.4:
    resolution: {{integrity: {zod_sri}}}

snapshots:
  zod@4.5.4: {{}}
""".encode(),
        contract_path: json_bytes({"openapi": "3.1.0", "info": {"version": version}}),
        config_path: b'export const input = "../contract/openapi/iam.internal.v1.json";\n',
        sdk_manifest_path: json_bytes(
            {
                "name": package,
                "version": version,
                "engines": {"node": ">=24 <25"},
                "main": "./dist/index.js",
                "types": "./dist/index.d.ts",
                "exports": {
                    ".": {"types": "./dist/index.d.ts", "import": "./dist/index.js"}
                },
                "dependencies": {"zod": "4.5.4"},
                "devDependencies": {generator: generator_version},
            }
        ),
    }
    owner_sha = commit_child(fixture.root, iam_name, owner)
    contract_digest = sha256(owner[contract_path]).hexdigest()
    provenance = {
        "schema_version": 1,
        "package": {"name": package, "version": version},
        "source": {"commit": owner_sha, "dirty": False},
        "contract": {"path": contract_path, "sha256": contract_digest},
        "generator": {
            "package": generator,
            "version": generator_version,
            "config_sha256": sha256(owner[config_path]).hexdigest(),
        },
        "lockfile_sha256": sha256(owner["pnpm-lock.yaml"]).hexdigest(),
        "runtime": {"node": "v24.20.0", "pnpm": "12.3.4"},
    }
    members = [
        ("package/package.json", owner[sdk_manifest_path]),
        ("package/dist/index.js", b"export {};\n"),
        ("package/dist/provenance.json", json_bytes(provenance)),
    ]
    official_archive = pack(members)
    fixture.module.IAM_SDK_RELEASE_ARCHIVES = {
        (owner_sha, version): sha256(official_archive).hexdigest()
    }

    if drift == "matching_wrong_contract":
        provenance["contract"]["sha256"] = "0" * 64
    elif drift == "matching_wrong_owner_config":
        provenance["generator"]["config_sha256"] = "0" * 64
    elif drift == "matching_wrong_owner_lock":
        provenance["lockfile_sha256"] = "0" * 64
    provenance_bytes = json_bytes(provenance)
    members[-1] = ("package/dist/provenance.json", provenance_bytes)
    if drift == "duplicate_member":
        members.append(members[-1])
    elif drift == "repacked_entrypoint":
        members[1] = ("package/dist/index.js", b"export const repacked = true;\n")
    archive_bytes = pack(members)
    if drift == "damaged_deflate":
        archive_bytes = archive_bytes[:10] + b"\xff" + archive_bytes[11:]
    integrity_bytes = b"other archive" if drift == "wrong_sri" else archive_bytes
    sri = "sha512-" + b64encode(sha512(integrity_bytes).digest()).decode()
    file_specifier = f"file:{archive_path}"
    archive_key = f"{package}@{file_specifier}"
    snapshot_key = "unrelated@1.0.0" if drift == "wrong_snapshot" else archive_key
    consumer_zod_sri = (
        "sha512-" + b64encode(sha512(b"untrusted zod archive").digest()).decode()
        if drift == "wrong_zod_sri"
        else zod_sri
    )
    lock = f"""lockfileVersion: '9.0'

importers:
  .:
    dependencies:
      '{package}':
        specifier: {file_specifier}
        version: {file_specifier}

packages:
  '{archive_key}':
    resolution: {{integrity: {sri}, tarball: {file_specifier}}}
    version: {version}
    engines: {{node: '>=24 <25'}}
  zod@4.5.4:
    resolution: {{integrity: {consumer_zod_sri}}}

snapshots:
  '{snapshot_key}':
    dependencies:
      zod: 4.5.4
  zod@4.5.4: {{}}
""".encode()
    if drift == "optional_importer":
        lock = lock.replace(
            b"\npackages:\n",
            f"    optionalDependencies:\n      '{package}':\n"
            f"        specifier: file:vendor/replacement.tgz\n"
            f"        version: file:vendor/replacement.tgz\n\npackages:\n".encode(),
            1,
        )
    elif drift == "optional_snapshot":
        lock = lock.replace(
            b"      zod: 4.5.4\n  zod@4.5.4: {}",
            b"      zod: 4.5.4\n    optionalDependencies:\n      zod: 9.0.0\n  zod@4.5.4: {}",
        )
    consumer = {
        "package.json": json_bytes(
            {
                "name": "kokoro-capability",
                "dependencies": {package: file_specifier},
                **(
                    {"devDependencies": {generator: generator_version}}
                    if drift == "consumer_generator"
                    else {}
                ),
                **(
                    {"optionalDependencies": {package: "file:vendor/replacement.tgz"}}
                    if drift == "optional_manifest"
                    else {}
                ),
            }
        ),
        "pnpm-lock.yaml": lock,
        archive_path: archive_bytes,
        provenance_path: provenance_bytes,
        "src/infrastructure/iam/execution-authorization-verifier.ts": b'import "@kokoro/iam-client";\n',
        "scripts/check-iam-sdk-artifact.ts": b"export {};\n",
    }
    consumer_sha = commit_child(fixture.root, "kokoro-capability", consumer)
    for repo, commit in ((iam_repo, owner_sha), (capability_repo, consumer_sha)):
        run(
            fixture.root,
            "git",
            "update-index",
            "--add",
            "--cacheinfo",
            "160000",
            commit,
            repo,
        )

    def reference(repo: str, path: str) -> dict[str, str]:
        files, commit = (
            (owner, owner_sha) if repo == iam_repo else (consumer, consumer_sha)
        )
        return {
            "repository_path": repo,
            "repository_commit": commit,
            "path": path,
            "sha256": sha256(files[path]).hexdigest(),
        }

    edge = fixture.data["edges"][0]
    edge.update(
        id="EDGE-CAPABILITY-IAM",
        caller="Capability",
        owner={
            "name": "kokoro-iam",
            "repository_path": iam_repo,
            "repository_commit": owner_sha,
            "contract_version": version,
            "contract_path": contract_path,
            "contract_sha256": contract_digest,
        },
        code_generator_version=f"{generator}@{generator_version}",
        runtime_package_version=f"{package}@{version}",
        reason="Capability consumes the pinned IAM SDK archive.",
        evidence=[reference(capability_repo, path) for path in consumer],
        version_assertions=[
            {
                "field": "code_generator_version",
                "declared_value": f"{generator}@{generator_version}",
                "package_name": generator,
                "version": generator_version,
                "manifest_kind": "npm-package-json",
                "json_checks": [
                    {
                        "pointer": "/devDependencies/@hey-api~1openapi-ts",
                        "expected": generator_version,
                    }
                ],
                **(
                    reference(capability_repo, "package.json")
                    if drift == "consumer_generator"
                    else reference(iam_repo, sdk_manifest_path)
                ),
            },
            {
                "field": "runtime_package_version",
                "declared_value": f"{package}@{version}",
                "package_name": package,
                "version": version,
                "manifest_kind": "npm-file-archive",
                **reference(capability_repo, "package.json"),
            },
        ],
    )
    fixture.module.EXPECTED_EDGE_IDS = frozenset({"EDGE-CAPABILITY-IAM"})
    return edge


def test_capability_iam_sdk_archive_accepts_exact_owner_and_file_lock(fixture) -> None:
    use_capability_iam_sdk_archive(fixture)

    assert fixture.verify() == []


@pytest.mark.parametrize(
    "scope",
    ["edge", "caller", "protocol", "owner", "owner_repository", "owner_contract_path"],
)
def test_capability_iam_sdk_archive_assertion_is_edge_local(
    fixture, scope: str
) -> None:
    edge = use_capability_iam_sdk_archive(fixture, drift=scope)
    if scope == "edge":
        edge["id"] = "EDGE-BFF-IAM"
        fixture.module.EXPECTED_EDGE_IDS = frozenset({edge["id"]})
    elif scope == "caller":
        edge["caller"] = "BFF"
    elif scope == "protocol":
        edge["protocol"] = "same-origin-http"
    elif scope == "owner":
        edge["owner"]["name"] = "other-iam"

    assert any("archive" in error.lower() for error in fixture.verify())


@pytest.mark.parametrize(
    ("drift", "diagnostic"),
    [
        ("matching_wrong_contract", "provenance"),
        ("matching_wrong_owner_config", "provenance"),
        ("matching_wrong_owner_lock", "provenance"),
        ("consumer_generator", "generator"),
        ("wrong_sri", "lock"),
        ("wrong_snapshot", "lock"),
        ("wrong_zod_sri", "lock"),
        ("optional_importer", "lock"),
        ("optional_snapshot", "lock"),
        ("optional_manifest", "outside runtime"),
        ("duplicate_member", "archive"),
        ("damaged_deflate", "archive"),
        ("version_range", "archive"),
    ],
)
def test_capability_iam_sdk_archive_rejects_inconsistent_git_evidence(
    fixture, drift: str, diagnostic: str
) -> None:
    use_capability_iam_sdk_archive(fixture, drift=drift)

    errors = fixture.verify()
    assert any(diagnostic in error.lower() for error in errors), errors
    assert all("evidence sha256" not in error for error in errors)


def test_capability_iam_sdk_archive_rejects_repacked_js_with_genuine_provenance(
    fixture,
) -> None:
    use_capability_iam_sdk_archive(fixture, drift="repacked_entrypoint")

    errors = fixture.verify()
    assert len(errors) == 1 and any(
        diagnostic in errors[0]
        for diagnostic in ("published IAM archive digest", "clean IAM archive")
    ), errors


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
    fixture.data["violations"] = [
        {
            "id": "EDGE-UNAPPROVED",
            "caller": "web",
            "target": "iam",
            "reason": "Unapproved bypass.",
            "evidence": fixture.data["edges"][0]["evidence"],
        }
    ]
    assert any("unexpected violation ids" in error for error in fixture.verify())


def test_path_escape_is_rejected(fixture) -> None:
    owner = fixture.data["edges"][0]["owner"]
    fixture.data["edges"][0]["owner"] = dict(owner, contract_path="../secret")
    assert any("safe relative path" in error for error in fixture.verify())
