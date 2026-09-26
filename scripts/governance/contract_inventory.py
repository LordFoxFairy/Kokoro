from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path, PurePosixPath
from typing import Any

PROTOCOLS = frozenset(
    {"same-origin-http", "http-openapi", "connect-proto", "http-event"}
)
STATES = frozenset({"active", "broken"})
EXPECTED_EDGE_IDS = frozenset(
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
EXPECTED_VIOLATION_IDS = frozenset()
OBJECT_ID_PATTERN = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})")
EXACT_SEMVER_PATTERN = re.compile(
    r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)"
)
VERSION_MANIFEST_KINDS = {
    "code_generator_version": frozenset({"npm-package-json"}),
    "runtime_package_version": frozenset({"npm-package-json", "plain-version-file"}),
    "producer_runtime_version": frozenset({"go-mod"}),
}


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def safe_relative_path(value: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or ".." in path.parts:
        raise ValueError(f"not a safe relative path: {value}")
    return path


def _canonical_object_id(value: str) -> str:
    if OBJECT_ID_PATTERN.fullmatch(value) is None:
        raise ValueError(
            "repository_commit must be a canonical 40 or 64 character hexadecimal OID"
        )
    return value


def gitlink_sha(root: Path, repository_path: str) -> str:
    path = safe_relative_path(repository_path).as_posix()
    try:
        result = subprocess.run(
            ["git", "ls-files", "--stage", "--", path],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError:
        raise ValueError("Root git index is unavailable") from None
    fields = result.stdout.split()
    if result.returncode or len(fields) < 2 or fields[0] != "160000":
        raise ValueError(f"{path}: not a Root gitlink")
    return fields[1]


def git_blob(
    root: Path, repository_path: str, commit: str, relative_path: str
) -> bytes:
    repository = root / safe_relative_path(repository_path)
    commit = _canonical_object_id(commit)
    relative = safe_relative_path(relative_path).as_posix()
    try:
        result = subprocess.run(
            [
                "git",
                "--no-replace-objects",
                "show",
                "--end-of-options",
                f"{commit}:{relative}",
            ],
            cwd=repository,
            capture_output=True,
            check=False,
        )
    except OSError:
        raise ValueError(
            f"{repository_path}: child repository checkout is unavailable"
        ) from None
    if result.returncode:
        raise ValueError(f"{repository_path}@{commit}:{relative}: missing commit blob")
    return result.stdout


def load_inventory(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raise ValueError("inventory must be UTF-8 JSON") from None
    value = json.loads(text)
    if not isinstance(value, dict):
        raise ValueError("inventory must be an object")
    if value.get("schema_version") != 1:
        raise ValueError("schema_version must equal 1")
    for field in ("edges", "violations"):
        if not isinstance(value.get(field), list):
            raise ValueError(f"{field} must be a list")
    return value


def _openapi_info_version(blob: bytes) -> str:
    try:
        source = blob.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise ValueError("OpenAPI contract must be UTF-8") from None
    if source.lstrip().startswith("{"):
        try:
            document = json.loads(source)
        except json.JSONDecodeError:
            raise ValueError("OpenAPI contract is invalid JSON") from None
        if not isinstance(document, dict) or not isinstance(document.get("info"), dict):
            raise ValueError("OpenAPI contract has no info object")
        version = document["info"].get("version")
    else:
        # Root governance uses only stdlib. Fail closed for YAML metadata shapes
        # outside the canonical top-level info / indented version form.
        in_info = False
        version = None
        for line in source.splitlines():
            if line == "info:":
                in_info = True
                continue
            if not in_info:
                continue
            if line and not line[0].isspace() and not line.startswith("#"):
                break
            match = re.fullmatch(
                r"  version:\s*['\"]?([^'\"#\s]+)['\"]?\s*(?:#.*)?", line
            )
            if match is not None:
                version = match.group(1)
                break
    if not isinstance(version, str) or not version:
        raise ValueError("OpenAPI contract has no canonical info.version")
    return version


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
        repository_commit = _canonical_object_id(repository_commit)
        actual_gitlink = gitlink_sha(root, repository_path)
        if actual_gitlink != repository_commit:
            errors.append(
                f"{label}: evidence gitlink {actual_gitlink} != {repository_commit}"
            )
            return None
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


def _split_package_version(declared_value: str) -> tuple[str, str]:
    package_name, separator, version = declared_value.rpartition("@")
    if not separator or not package_name or not version:
        raise ValueError(
            f"declared version must use package_name@version: {declared_value!r}"
        )
    package_name_without_scope_marker = package_name.removeprefix("@")
    if "@" in package_name_without_scope_marker:
        raise ValueError("multiple package declarations require a packages array")
    return package_name, version


def _npm_package_pointer(field: str, package_name: str) -> str:
    sections = {
        "runtime_package_version": "dependencies",
        "code_generator_version": "devDependencies",
    }
    try:
        section = sections[field]
    except KeyError:
        raise ValueError(f"unknown npm version field: {field}") from None
    escaped_package_name = package_name.replace("~", "~0").replace("/", "~1")
    return f"/{section}/{escaped_package_name}"


def _verify_declared_package_version(
    label: str,
    declared_value: str,
    package_name: str,
    version: str,
    errors: list[str],
) -> None:
    try:
        declared_package_name, declared_version = _split_package_version(declared_value)
    except ValueError as error:
        errors.append(f"{label}: {error}")
    else:
        if package_name != declared_package_name:
            errors.append(
                f"{label}: package_name {package_name!r} != {declared_package_name!r}"
            )
        if version != declared_version:
            errors.append(f"{label}: version {version!r} != {declared_version!r}")
    if f"{package_name}@{version}" != declared_value:
        errors.append(
            f"{label}: package_name/version do not compose declared_value "
            f"{declared_value!r}"
        )


def _verify_npm_assertion(
    label: str,
    field: str,
    assertion: dict[str, Any],
    package_name: str,
    version: str,
    blob: bytes | None,
    errors: list[str],
) -> None:
    evidence_path = _text(assertion, "path", label, errors)
    if evidence_path and PurePosixPath(evidence_path).name != "package.json":
        errors.append(f"{label}: evidence basename must be package.json")
    checks = assertion.get("json_checks")
    if blob is None or not isinstance(checks, list) or not checks:
        errors.append(f"{label}: json_checks must be a non-empty list")
        return
    try:
        document = json.loads(blob)
    except (UnicodeDecodeError, json.JSONDecodeError):
        errors.append(f"{label}: version evidence must be UTF-8 JSON")
        return
    canonical_pointer = _npm_package_pointer(field, package_name)
    has_package_version_evidence = False
    for check_index, check in enumerate(checks):
        check_label = f"{label}.json_checks[{check_index}]"
        if not isinstance(check, dict):
            errors.append(f"{check_label}: must be an object")
            continue
        pointer = _text(check, "pointer", check_label, errors)
        expected = check.get("expected")
        if pointer != canonical_pointer:
            errors.append(
                f"{check_label}: pointer {pointer!r} != canonical npm pointer "
                f"{canonical_pointer!r}"
            )
            continue
        try:
            actual = _json_pointer(document, pointer)
        except ValueError as error:
            errors.append(f"{check_label}: {error}")
            continue
        if actual != expected:
            errors.append(f"{check_label}: {actual!r} != {expected!r}")
        elif expected == version:
            has_package_version_evidence = True
    if not has_package_version_evidence:
        errors.append(
            f"{label}: json_checks must include package/version evidence for "
            f"{package_name}@{version}"
        )


def _verify_plain_version_assertion(
    label: str,
    assertion: dict[str, Any],
    package_name: str,
    version: str,
    blob: bytes | None,
    errors: list[str],
) -> None:
    evidence_path = _text(assertion, "path", label, errors)
    if evidence_path and evidence_path != ".node-version":
        errors.append(f"{label}: path must be .node-version")
    if package_name != "node":
        errors.append(f"{label}: plain-version-file package_name must be 'node'")
    if EXACT_SEMVER_PATTERN.fullmatch(version) is None:
        errors.append(f"{label}: version must be an exact semantic version")
    if blob is None:
        return
    try:
        text = blob.decode("utf-8")
    except UnicodeDecodeError:
        errors.append(f"{label}: plain version evidence must be UTF-8")
        return
    content = text.removesuffix("\n")
    if (
        text not in {content, f"{content}\n"}
        or "\n" in content
        or EXACT_SEMVER_PATTERN.fullmatch(content) is None
    ):
        errors.append(
            f"{label}: plain version evidence must be one exact semantic version"
        )
    elif content != version:
        errors.append(f"{label}: plain version evidence {content!r} != {version!r}")


def _verify_go_mod_assertion(
    label: str,
    assertion: dict[str, Any],
    package_name: str,
    version: str,
    blob: bytes | None,
    errors: list[str],
) -> None:
    evidence_path = _text(assertion, "path", label, errors)
    if evidence_path and evidence_path != "go.mod":
        errors.append(f"{label}: path must be go.mod")
    if package_name != "go":
        errors.append(f"{label}: go-mod package_name must be 'go'")
    if EXACT_SEMVER_PATTERN.fullmatch(version) is None:
        errors.append(f"{label}: version must be an exact semantic version")
    if blob is None:
        return
    try:
        text = blob.decode("utf-8")
    except UnicodeDecodeError:
        errors.append(f"{label}: go.mod evidence must be UTF-8")
        return
    directives = [
        line for line in text.splitlines() if re.match(r"^[^\S\r\n]*go[^\S\r\n]+", line)
    ]
    if len(directives) != 1:
        errors.append(
            f"{label}: go.mod must contain exactly one canonical go directive"
        )
        return
    match = re.fullmatch(rf"go ({EXACT_SEMVER_PATTERN.pattern})", directives[0])
    if match is None:
        errors.append(
            f"{label}: go.mod must contain exactly one canonical go directive"
        )
    elif match.group(1) != version:
        errors.append(f"{label}: go.mod version {match.group(1)!r} != {version!r}")


def _verify_version_assertion(
    root: Path,
    label: str,
    assertion: dict[str, Any],
    field: str,
    errors: list[str],
) -> None:
    declared_value = _text(assertion, "declared_value", label, errors)
    package_name = _text(assertion, "package_name", label, errors)
    version = _text(assertion, "version", label, errors)
    manifest_kind = _text(assertion, "manifest_kind", label, errors)
    _verify_declared_package_version(
        label, declared_value, package_name, version, errors
    )
    blob = _verify_blob_reference(root, label, assertion, errors)
    known_manifest_kinds = set().union(*VERSION_MANIFEST_KINDS.values())
    if manifest_kind not in known_manifest_kinds:
        errors.append(f"{label}: unknown manifest_kind {manifest_kind!r}")
        return
    if manifest_kind not in VERSION_MANIFEST_KINDS.get(field, frozenset()):
        errors.append(
            f"{label}: manifest_kind {manifest_kind!r} is not allowed for {field}"
        )
        return
    if manifest_kind == "npm-package-json":
        _verify_npm_assertion(
            label, field, assertion, package_name, version, blob, errors
        )
    elif manifest_kind == "plain-version-file":
        _verify_plain_version_assertion(
            label, assertion, package_name, version, blob, errors
        )
    elif manifest_kind == "go-mod":
        _verify_go_mod_assertion(label, assertion, package_name, version, blob, errors)


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
    generator_exempt = (
        edge_id == "EDGE-BROWSER-WEB"
        and edge.get("protocol") == "same-origin-http"
        and generator == "not-applicable:same-origin-route"
    )
    if isinstance(generator, str) and generator.startswith("not-applicable:"):
        if not generator_exempt:
            errors.append(f"{edge_id}: generator exemption is not allowed")
    else:
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
        if field in asserted:
            errors.append(f"{label}: duplicate version assertion for {field}")
            continue
        asserted.add(field)
        declared_value = raw_assertion.get("declared_value")
        if declared_value != edge.get(field):
            errors.append(
                f"{label}: declared version {declared_value!r} != {edge.get(field)!r}"
            )
        _verify_version_assertion(root, label, raw_assertion, field, errors)
    for field in sorted(required - asserted):
        errors.append(f"{edge_id}: missing version assertion for {field}")


def _verify_producer_runtime_assertion(
    root: Path,
    edge_id: str,
    edge: dict[str, Any],
    errors: list[str],
) -> None:
    assertion = edge.get("producer_runtime_assertion")
    if edge.get("protocol") != "http-event":
        if assertion is not None:
            errors.append(
                f"{edge_id}: producer_runtime_assertion is only valid for http-event"
            )
        return
    if not isinstance(assertion, dict):
        errors.append(f"{edge_id}: missing producer_runtime_assertion")
        return
    label = f"{edge_id}: producer_runtime_assertion"
    owner = edge.get("owner")
    if isinstance(owner, dict) and (
        assertion.get("repository_path") != owner.get("repository_path")
        or assertion.get("repository_commit") != owner.get("repository_commit")
    ):
        errors.append(f"{label}: repository must match contract owner")
    _verify_version_assertion(
        root,
        label,
        assertion,
        "producer_runtime_version",
        errors,
    )


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
            owner_values = {
                field: _text(raw_owner, field, f"{edge_id}: owner", errors)
                for field in (
                    "name",
                    "repository_path",
                    "repository_commit",
                    "contract_version",
                    "contract_path",
                    "contract_sha256",
                )
            }
            repository_path = owner_values["repository_path"]
            repository_commit = owner_values["repository_commit"]
            contract_path = owner_values["contract_path"]
            contract_digest = owner_values["contract_sha256"]
            if all(
                (repository_path, repository_commit, contract_path, contract_digest)
            ):
                try:
                    repository_commit = _canonical_object_id(repository_commit)
                    actual_gitlink = gitlink_sha(root, repository_path)
                    if actual_gitlink != repository_commit:
                        errors.append(
                            f"{edge_id}: owner gitlink {actual_gitlink} != "
                            f"{repository_commit}"
                        )
                    else:
                        blob = git_blob(
                            root,
                            repository_path,
                            repository_commit,
                            contract_path,
                        )
                        actual_digest = sha256_bytes(blob)
                        if actual_digest != contract_digest:
                            errors.append(
                                f"{edge_id}: contract_sha256 {actual_digest} != "
                                f"{contract_digest}"
                            )
                        if raw_edge.get("protocol") in {"http-openapi", "http-event"}:
                            try:
                                openapi_version = _openapi_info_version(blob)
                            except ValueError as error:
                                errors.append(f"{edge_id}: owner {error}")
                            else:
                                if owner_values["contract_version"] != openapi_version:
                                    errors.append(
                                        f"{edge_id}: owner contract_version "
                                        f"{owner_values['contract_version']!r} != "
                                        f"OpenAPI info.version {openapi_version!r}"
                                    )
                except ValueError as error:
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
            _verify_producer_runtime_assertion(root, edge_id, raw_edge, errors)
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
        errors.append(f"{violation_id}: illegal edge: {raw_violation.get('reason')}")
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
