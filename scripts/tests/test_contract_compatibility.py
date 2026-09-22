from __future__ import annotations

import copy
import importlib.util
import json
import shutil
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


def test_default_topology_baseline_declares_16_edges_and_violation() -> None:
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
    assert module.EXPECTED_VIOLATION_IDS == frozenset({"EDGE-WEB-IAM-DIRECT"})


def test_scheduler_event_edges_pin_scheduler_owned_contract() -> None:
    inventory = json.loads(
        (ROOT / "verification/contracts/consumer-inventory.json").read_text()
    )
    edges = {edge["id"]: edge for edge in inventory["edges"]}
    scheduler_owner = {
        "name": "kokoro-scheduler",
        "repository_path": "apps/kokoro-scheduler",
        "repository_commit": "92bf9e7e6724c591bab4b7fa27f08d694b59a67e",
        "contract_version": "1.0.0",
        "contract_path": "contract/openapi/v1/openapi.yaml",
        "contract_sha256": (
            "6ec2f6d5d71efa60b92bba1eb2dd0c81b7439734e2bc4450caa221e952e24183"
        ),
    }

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
    owner_contract = b'{"openapi":"3.1.0"}\n'
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
                    "contract_version": "v1",
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
    original_blob = b'{"openapi":"3.1.0"}\n'
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
