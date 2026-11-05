from __future__ import annotations

import base64
import gzip
import hashlib
import io
import json
import re
import subprocess
import tarfile
import tomllib
import zlib
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
    "runtime_package_version": frozenset(
        {"npm-package-json", "plain-version-file", "uv-lock", "npm-file-archive"}
    ),
    "producer_runtime_version": frozenset({"go-mod"}),
}


AGENT_SYSTEM_EDGE = "EDGE-AGENT-SYSTEM"
AGENT_STORAGE_EDGE = "EDGE-AGENT-STORAGE"
AGENT_STORAGE_PIN = "contract/storage/v3/provenance.json"
AGENT_STORAGE_VENDOR = "contract/storage/v3"
STORAGE_REPOSITORY = "apps/kokoro-storage"
STORAGE_PROTO = "kokoro/storage/v3/storage.proto"
AGENT_SYSTEM_GENERATOR = "not-applicable:handwritten-agent-system-http"
AGENT_REPOSITORY = "apps/kokoro-agent"
SYSTEM_REPOSITORY = "apps/kokoro-system"
SYSTEM_OPENAPI = "contract/openapi/system.openapi.json"
CONTRACT_PROVENANCE = "contract/provenance.json"
SYSTEM_CLIENT = "src/kokoro_agent/clients/system.py"
CAPABILITY_IAM_EDGE = "EDGE-CAPABILITY-IAM"
CAPABILITY_REPOSITORY = "apps/kokoro-capability"
IAM_REPOSITORY = "apps/kokoro-iam"
IAM_OPENAPI = "contract/openapi/iam.internal.v1.json"
IAM_SDK_PACKAGE = "@kokoro/iam-client"
IAM_SDK_GENERATOR = "@hey-api/openapi-ts"
IAM_SDK_MANIFEST = "sdk/package.json"
# IAM does not store tarballs in the source tree. Anchor the independently
# packed clean-owner release here, not in the consuming repo's lock/evidence.
IAM_SDK_RELEASE_ARCHIVES = {
    (
        "b6a9745b340149808afb1aae357574d0aa7bbad3",
        "0.21.0",
    ): "458da2ba96daa7784f0cd296b92fc0e428232e49119c0ca25485788ffc1dcad9",
}
IAM_SDK_VERIFIER = "src/infrastructure/iam/execution-authorization-verifier.ts"
SYSTEM_OPERATIONS = (
    "POST /v1/system/model-catalog/resolve",
    "POST /v1/system/model-catalog/credentials/read",
)


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
    if not isinstance(checks, list) or not checks:
        errors.append(f"{label}: json_checks must be a non-empty list")
        return
    if blob is None:
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


def _verify_agent_uv_lock(
    label: str, package_name: str, version: str, blob: bytes, errors: list[str]
) -> None:
    try:
        lock = tomllib.loads(blob.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError):
        errors.append(f"{label}: uv.lock must be valid UTF-8 TOML")
        return
    packages = lock.get("package")
    if (
        type(lock.get("version")) is not int
        or lock["version"] != 1
        or not isinstance(packages, list)
        or any(not isinstance(package, dict) for package in packages)
    ):
        errors.append(f"{label}: uv.lock must contain version 1 package records")
        return
    projects = [
        package for package in packages if package.get("name") == "kokoro-agent"
    ]
    if (
        len(projects) != 1
        or projects[0].get("source") != {"editable": "."}
        or "resolution-markers" in projects[0]
    ):
        errors.append(
            f"{label}: uv.lock must have one unconditional editable kokoro-agent root"
        )
        return
    dependencies = projects[0].get("dependencies")
    if (
        not isinstance(dependencies, list)
        or any(
            not isinstance(dependency, dict)
            or not isinstance(dependency.get("name"), str)
            or not dependency["name"].strip()
            for dependency in dependencies
        )
        or [
            dependency
            for dependency in dependencies
            if dependency["name"] == package_name
        ]
        != [{"name": package_name}]
    ):
        errors.append(
            f"{label}: uv.lock must have one direct runtime {package_name} dependency"
        )
    matches = [package for package in packages if package.get("name") == package_name]
    source = matches[0].get("source") if len(matches) == 1 else None
    if (
        EXACT_SEMVER_PATTERN.fullmatch(version) is None
        or len(matches) != 1
        or matches[0].get("version") != version
        or "resolution-markers" in matches[0]
        or not isinstance(source, dict)
        or set(source) != {"registry"}
        or not isinstance(source["registry"], str)
        or not source["registry"].strip()
    ):
        errors.append(
            f"{label}: uv.lock must resolve one registry {package_name} at {version!r}"
        )


def _strict_json_blob(blob: bytes) -> Any:
    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON field")
            result[key] = value
        return result

    def invalid_constant(value: str) -> Any:
        raise ValueError(f"invalid JSON constant: {value}")

    return json.loads(
        blob.decode("utf-8"), object_pairs_hook=unique, parse_constant=invalid_constant
    )


def _verify_agent_storage_codegen(
    root: Path,
    label: str,
    edge: dict[str, Any],
    assertion: dict[str, Any],
    errors: list[str],
) -> None:
    version = _text(assertion, "version", label, errors)
    if EXACT_SEMVER_PATTERN.fullmatch(version) is None:
        errors.append(f"{label}: generator must be an exact semantic version")
        return
    _verify_declared_package_version(
        label,
        _text(assertion, "declared_value", label, errors),
        "protoc-gen-connectrpc",
        version,
        errors,
    )
    blob = _verify_blob_reference(root, label, assertion, errors)
    if blob is None:
        return
    try:
        pin = _strict_json_blob(blob)
        owner_commit = edge["owner"]["repository_commit"]
        if not isinstance(pin, dict) or (
            pin.get("owner"),
            pin.get("owner_repository"),
            pin.get("owner_commit"),
        ) != ("kokoro-storage", STORAGE_REPOSITORY, owner_commit):
            raise ValueError("Agent Storage receipt owner pin differs")
        agent_commit = assertion["repository_commit"]
        provenance = git_blob(
            root, STORAGE_REPOSITORY, owner_commit, CONTRACT_PROVENANCE
        )
        inputs = ("kokoro/common/v1/common.proto", STORAGE_PROTO)
        sources = []
        combined = hashlib.sha256()
        for source in inputs:
            owner_path = f"contract/proto/{source}"
            vendor = f"{AGENT_STORAGE_VENDOR}/proto/{source}"
            owner_bytes = git_blob(root, STORAGE_REPOSITORY, owner_commit, owner_path)
            if owner_bytes != git_blob(root, AGENT_REPOSITORY, agent_commit, vendor):
                raise ValueError(f"Agent Storage vendor differs from owner: {source}")
            combined.update(owner_bytes)
            sources.append(
                {
                    "owner_path": owner_path,
                    "path": vendor,
                    "sha256": sha256_bytes(owner_bytes),
                }
            )
        provenance_path = f"{AGENT_STORAGE_VENDOR}/owner-provenance.json"
        if provenance != git_blob(
            root, AGENT_REPOSITORY, agent_commit, provenance_path
        ):
            raise ValueError("Agent Storage vendor provenance differs from owner")
        provenance_data = _strict_json_blob(provenance)
        if (
            not isinstance(provenance_data, dict)
            or provenance_data.get("files") != list(inputs)
            or provenance_data.get("combinedSha256") != combined.hexdigest()
            or pin.get("sources") != sources
            or pin.get("owner_provenance")
            != {
                "path": provenance_path,
                "sha256": sha256_bytes(provenance),
                "combined_sha256": combined.hexdigest(),
            }
        ):
            raise ValueError("Agent Storage source or provenance digest differs")
        if (
            _json_pointer(pin, "/codegen/protoc_gen_connectrpc") != version
            or _json_pointer(pin, "/codegen/connectrpc_parameter") != "io=async"
            or f"connectrpc@{_json_pointer(pin, '/runtime/connectrpc')}"
            != edge["runtime_package_version"]
        ):
            raise ValueError(
                "Agent Storage generation or runtime version differs from receipt"
            )
    except (KeyError, TypeError, ValueError) as error:
        errors.append(f"{label}: {error}")


def _verify_agent_system_receipt(
    root: Path, edge: dict[str, Any], errors: list[str]
) -> None:
    label = f"{AGENT_SYSTEM_EDGE}: System consumer receipt"
    evidence = edge.get("evidence")
    try:
        required = {}
        for path in (SYSTEM_CLIENT, CONTRACT_PROVENANCE):
            references = (
                [
                    ref
                    for ref in evidence
                    if isinstance(ref, dict)
                    and ref.get("repository_path") == AGENT_REPOSITORY
                    and ref.get("path") == path
                ]
                if isinstance(evidence, list)
                else []
            )
            if len(references) != 1:
                raise ValueError(f"requires one pinned Agent {path} reference")
            blob = _verify_blob_reference(root, label, references[0], errors)
            if not blob or not blob.strip():
                raise ValueError(f"missing Agent {path} blob")
            required[path] = blob

        owner = edge["owner"]
        commit = owner["repository_commit"]
        provenance = git_blob(root, SYSTEM_REPOSITORY, commit, CONTRACT_PROVENANCE)
        producer = _json_pointer(_strict_json_blob(provenance), "/openapi")
        sources = _json_pointer(producer, "/sourceSha256")
        if (
            producer.get("file") != "openapi/system.openapi.json"
            or producer.get("sha256") != owner["contract_sha256"]
            or not isinstance(sources, dict)
            or not sources
        ):
            raise ValueError("System owner provenance differs from the pinned OpenAPI")
        for path, digest in sources.items():
            if sha256_bytes(git_blob(root, SYSTEM_REPOSITORY, commit, path)) != digest:
                raise ValueError(f"System source digest differs at {path}")
        openapi = _strict_json_blob(
            git_blob(root, SYSTEM_REPOSITORY, commit, SYSTEM_OPENAPI)
        )
        for operation in SYSTEM_OPERATIONS:
            method, path = operation.split(" ", 1)
            operations = _json_pointer(openapi, "/paths")
            if not isinstance(operations.get(path, {}).get(method.lower()), dict):
                raise ValueError(f"System OpenAPI lacks {operation}")
        dependencies = _json_pointer(
            _strict_json_blob(required[CONTRACT_PROVENANCE]), "/consumer_dependencies"
        )
        if not isinstance(dependencies, list):
            raise ValueError("Agent consumer_dependencies must be a list")
        matches = [
            dependency
            for dependency in dependencies
            if isinstance(dependency, dict)
            and dependency.get("owner") == "kokoro-system"
        ]
        expected = {
            "owner": "kokoro-system",
            "contract": SYSTEM_OPENAPI,
            "version": owner["contract_version"],
            "source_commit": commit,
            "sha256": owner["contract_sha256"],
            "provenance": {
                "path": CONTRACT_PROVENANCE,
                "sha256": sha256_bytes(provenance),
            },
            "source_sha256": sources,
            "operations": list(SYSTEM_OPERATIONS),
        }
        if matches != [expected]:
            raise ValueError(
                "Agent receipt differs from the pinned System owner or operations"
            )
    except (AttributeError, KeyError, TypeError, ValueError) as error:
        errors.append(f"{label}: {error}")


def _iam_sdk_archive_members(blob: bytes) -> dict[str, bytes]:
    limit = 4 * 1024 * 1024
    with gzip.GzipFile(fileobj=io.BytesIO(blob)) as archive:
        tar = archive.read(limit + 1)
    if len(tar) > limit:
        raise ValueError("archive expands beyond the SDK size limit")
    required = {
        "package/package.json",
        "package/dist/provenance.json",
        "package/dist/index.js",
    }
    seen = set()
    result = {}
    with tarfile.open(fileobj=io.BytesIO(tar), mode="r:") as archive:
        for member in archive:
            name = member.name
            if (
                not member.isfile()
                or not name.startswith("package/")
                or "\\" in name
                or safe_relative_path(name).as_posix() != name
                or name in seen
            ):
                raise ValueError("archive has an unsafe or duplicate member")
            seen.add(name)
            if name in required:
                content = archive.extractfile(member)
                if content is None or member.size == 0 or member.size > 128 * 1024:
                    raise ValueError(f"archive member is missing or invalid: {name}")
                with content:
                    result[name] = content.read()
    if set(result) != required:
        raise ValueError("archive lacks its SDK entrypoint, manifest, or provenance")
    return result


def _verify_pnpm_file_lock(
    lock: bytes,
    owner_lock: bytes,
    archive_path: str,
    version: str,
    integrity: str,
    dependencies: dict,
) -> None:
    from scripts.governance.contract_checks import (
        _yaml_block_mapping,
        _yaml_mapping_entries,
    )

    def document(text: str) -> dict:
        root = _yaml_mapping_entries(text)
        if root["lockfileVersion"] != ("'9.0'", ""):
            raise ValueError("expected pnpm lockfile version 9")
        return root

    def packages(root: dict, section: str) -> dict:
        value, body = root[section]
        # pnpm emits unquoted scalar package keys such as accepts@2.0.0;
        # normalize only those canonical keys at the section's key indent.
        body = re.sub(
            r"(?m)^  ([A-Za-z0-9_][A-Za-z0-9._/@+()~-]*)(?=:[ \t]*(?:$| ))",
            lambda match: f"  '{match.group(1)}'",
            body,
        )
        return _yaml_block_mapping((value, body))

    try:
        root = document(lock.decode("utf-8"))
        imports = _yaml_block_mapping(root["importers"])
        importer = _yaml_block_mapping(imports["."])
        for other in ("devDependencies", "optionalDependencies", "peerDependencies"):
            if other in importer and IAM_SDK_PACKAGE in _yaml_block_mapping(
                importer[other]
            ):
                raise ValueError(
                    "archive is also selected outside the runtime importer"
                )
        deps = _yaml_block_mapping(importer["dependencies"])
        selected = _yaml_block_mapping(deps[IAM_SDK_PACKAGE])
        reference = f"file:{archive_path}"
        if selected != {"specifier": (reference, ""), "version": (reference, "")}:
            raise ValueError("default runtime importer selects a different archive")
        key = f"{IAM_SDK_PACKAGE}@{reference}"
        installed_packages = packages(root, "packages")
        installed_snapshots = packages(root, "snapshots")
        package = _yaml_block_mapping(installed_packages[key])
        expected = f"{{integrity: {integrity}, tarball: {reference}}}"
        if package.get("resolution") != (expected, "") or package.get("version") != (
            version,
            "",
        ):
            raise ValueError("archive resolution, integrity, or version differs")
        snapshot = installed_snapshots[key]
        if not dependencies:
            if snapshot != ("{}", ""):
                raise ValueError("expected an empty archive snapshot")
            return
        snapshot = _yaml_block_mapping(snapshot)
        if set(snapshot) != {"dependencies"}:
            raise ValueError("archive snapshot has extra dependency selections")
        locked = _yaml_block_mapping(snapshot["dependencies"])
        if locked != {name: (value, "") for name, value in dependencies.items()}:
            raise ValueError("archive snapshot dependencies differ")
        # IAM's pnpm bootstrap document precedes the actual project graph.
        owner_docs = [
            part
            for part in re.split(r"(?m)^---[ \t]*$", owner_lock.decode("utf-8"))
            if part.strip()
        ]
        if not 1 <= len(owner_docs) <= 2:
            raise ValueError("unexpected IAM lock document layout")
        owner = document(owner_docs[-1])
        producer_packages = packages(owner, "packages")
        producer_snapshots = packages(owner, "snapshots")
        for name, value in dependencies.items():
            dependency = f"{name}@{value}"
            if (
                not isinstance(value, str)
                or EXACT_SEMVER_PATTERN.fullmatch(value) is None
                or installed_packages[dependency] != producer_packages[dependency]
                or installed_snapshots[dependency] != producer_snapshots[dependency]
            ):
                raise ValueError(
                    f"archive dependency {name} resolves differently from IAM"
                )
    except (AttributeError, KeyError, TypeError, ValueError) as error:
        raise ValueError(f"pnpm lock: {error}") from error


def _verify_capability_iam_archive(
    root: Path, edge: dict[str, Any], assertion: dict[str, Any], errors: list[str]
) -> None:
    label = f"{CAPABILITY_IAM_EDGE}: IAM SDK archive"
    owner = edge["owner"]
    try:
        version = assertion.get("version")
        if (
            not isinstance(version, str)
            or EXACT_SEMVER_PATTERN.fullmatch(version) is None
        ):
            raise ValueError("archive version must be exact semantic version")
        if version != owner["contract_version"]:
            raise ValueError("archive version differs from the IAM owner contract")
        archive_path = f"vendor/iam/kokoro-iam-client-{version}.tgz"
        paths = (
            archive_path,
            "vendor/iam/provenance.json",
            "pnpm-lock.yaml",
            IAM_SDK_VERIFIER,
        )
        evidence = edge.get("evidence")
        blobs = {}
        for path in paths:
            matches = (
                [
                    ref
                    for ref in evidence
                    if isinstance(ref, dict)
                    and ref.get("repository_path") == CAPABILITY_REPOSITORY
                    and ref.get("path") == path
                    and ref.get("repository_commit")
                    == assertion.get("repository_commit")
                ]
                if isinstance(evidence, list)
                else []
            )
            if len(matches) != 1:
                raise ValueError(f"requires one pinned Capability {path} reference")
            blob = _verify_blob_reference(root, label, matches[0], errors)
            if not blob:
                raise ValueError(f"missing Capability {path} blob")
            blobs[path] = blob

        consumer = _verify_blob_reference(root, label, assertion, errors)
        if not consumer:
            raise ValueError("missing Capability package.json")
        consumer_manifest = _strict_json_blob(consumer)
        if (
            _json_pointer(consumer_manifest, "/dependencies/@kokoro~1iam-client")
            != f"file:{archive_path}"
        ):
            raise ValueError(
                "Capability runtime dependency does not select the archive"
            )
        for other in ("devDependencies", "optionalDependencies", "peerDependencies"):
            if IAM_SDK_PACKAGE in consumer_manifest.get(other, {}):
                raise ValueError(
                    "Capability manifest also selects the archive outside runtime dependencies"
                )

        commit = owner["repository_commit"]

        def owner_blob(path: str) -> bytes:
            return git_blob(root, IAM_REPOSITORY, commit, path)

        packed = _iam_sdk_archive_members(blobs[archive_path])
        owner_sdk = _strict_json_blob(owner_blob(IAM_SDK_MANIFEST))
        if (
            _strict_json_blob(packed["package/package.json"]) != owner_sdk
            or owner_sdk.get("name") != IAM_SDK_PACKAGE
            or owner_sdk.get("version") != version
        ):
            raise ValueError("archive manifest differs from the IAM SDK owner")
        if (
            packed["package/dist/provenance.json"]
            != blobs["vendor/iam/provenance.json"]
        ):
            raise ValueError("archive embedded provenance differs from the sidecar")
        owner_generator = _json_pointer(
            owner_sdk, "/devDependencies/@hey-api~1openapi-ts"
        )
        pnpm = _json_pointer(
            _strict_json_blob(owner_blob("package.json")), "/packageManager"
        )
        if not isinstance(pnpm, str) or not pnpm.startswith("pnpm@"):
            raise ValueError("archive provenance requires an IAM pnpm pin")
        expected = {
            "schema_version": 1,
            "package": {"name": IAM_SDK_PACKAGE, "version": version},
            "source": {"commit": commit, "dirty": False},
            "contract": {"path": IAM_OPENAPI, "sha256": owner["contract_sha256"]},
            "generator": {
                "package": IAM_SDK_GENERATOR,
                "version": owner_generator,
                "config_sha256": sha256_bytes(owner_blob("sdk/openapi-ts.config.ts")),
            },
            "lockfile_sha256": sha256_bytes(owner_blob("pnpm-lock.yaml")),
            "runtime": {
                "node": "v" + owner_blob(".node-version").decode("utf-8").strip(),
                "pnpm": pnpm.removeprefix("pnpm@"),
            },
        }
        provenance = _strict_json_blob(blobs["vendor/iam/provenance.json"])
        if provenance != expected or provenance["source"]["dirty"] is not False:
            raise ValueError("archive provenance differs from the exact IAM source")
        if (
            edge.get("code_generator_version")
            != f"{IAM_SDK_GENERATOR}@{owner_generator}"
        ):
            raise ValueError(
                "archive generator differs from the declared IAM generator"
            )
        integrity = "sha512-" + base64.b64encode(
            hashlib.sha512(blobs[archive_path]).digest()
        ).decode("ascii")
        _verify_pnpm_file_lock(
            blobs["pnpm-lock.yaml"],
            owner_blob("pnpm-lock.yaml"),
            archive_path,
            version,
            integrity,
            owner_sdk.get("dependencies", {}),
        )
        if sha256_bytes(blobs[archive_path]) != IAM_SDK_RELEASE_ARCHIVES.get(
            (commit, version)
        ):
            raise ValueError(
                "digest does not match the independently verified clean IAM archive"
            )
    except (
        AttributeError,
        EOFError,
        KeyError,
        OSError,
        tarfile.TarError,
        zlib.error,
        TypeError,
        ValueError,
    ) as error:
        errors.append(f"{label}: {error}")


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
    elif manifest_kind == "uv-lock" and blob is not None:
        _verify_agent_uv_lock(label, package_name, version, blob, errors)


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
    owner = edge.get("owner")
    capability_iam = (
        edge_id == CAPABILITY_IAM_EDGE
        and edge.get("caller") == "Capability"
        and edge.get("protocol") == "http-openapi"
        and isinstance(owner, dict)
        and owner.get("name") == "kokoro-iam"
        and owner.get("repository_path") == IAM_REPOSITORY
        and owner.get("contract_path") == IAM_OPENAPI
    )
    if edge_id == CAPABILITY_IAM_EDGE and not capability_iam:
        errors.append(
            f"{edge_id}: archive assertion requires the scoped Capability IAM edge"
        )
    agent_system = (
        edge_id == AGENT_SYSTEM_EDGE
        and edge.get("caller") == "Agent"
        and edge.get("protocol") == "http-openapi"
        and isinstance(owner, dict)
        and owner.get("name") == "kokoro-system"
        and owner.get("repository_path") == SYSTEM_REPOSITORY
        and owner.get("contract_path") == SYSTEM_OPENAPI
        and generator == AGENT_SYSTEM_GENERATOR
    )
    agent_storage = (
        edge_id == AGENT_STORAGE_EDGE
        and edge.get("caller") == "Agent"
        and edge.get("protocol") == "connect-proto"
        and isinstance(owner, dict)
        and owner.get("name") == "kokoro-storage"
        and owner.get("repository_path") == STORAGE_REPOSITORY
        and owner.get("contract_path") == f"contract/proto/{STORAGE_PROTO}"
        and owner.get("contract_version") == "kokoro.storage.v3"
    )
    if edge_id == AGENT_STORAGE_EDGE and not agent_storage:
        errors.append(f"{edge_id}: assertion requires the scoped Agent Storage v3 edge")
    browser_exempt = (
        edge_id == "EDGE-BROWSER-WEB"
        and edge.get("protocol") == "same-origin-http"
        and generator == "not-applicable:same-origin-route"
    )
    if isinstance(generator, str) and generator.startswith("not-applicable:"):
        if not (agent_system or browser_exempt):
            errors.append(f"{edge_id}: generator exemption is not allowed")
    else:
        required.add("code_generator_version")
    if edge_id == AGENT_SYSTEM_EDGE and not agent_system:
        errors.append(
            f"{edge_id}: requires the scoped Agent System generator exemption"
        )
    if agent_system:
        _verify_agent_system_receipt(root, edge, errors)
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
        manifest_kind = raw_assertion.get("manifest_kind")
        if agent_system and (
            field != "runtime_package_version"
            or manifest_kind != "uv-lock"
            or raw_assertion.get("repository_path") != AGENT_REPOSITORY
            or raw_assertion.get("path") != "uv.lock"
            or raw_assertion.get("package_name") != "httpx"
        ):
            errors.append(
                f"{label}: requires Agent uv.lock and direct httpx runtime evidence"
            )
            continue
        if agent_storage:
            expected_kind, expected_path, expected_package = (
                ("agent-storage-codegen", AGENT_STORAGE_PIN, "protoc-gen-connectrpc")
                if field == "code_generator_version"
                else ("uv-lock", "uv.lock", "connectrpc")
            )
            if (
                manifest_kind != expected_kind
                or raw_assertion.get("repository_path") != AGENT_REPOSITORY
                or raw_assertion.get("path") != expected_path
                or raw_assertion.get("package_name") != expected_package
            ):
                errors.append(
                    f"{label}: requires Agent {expected_path} and {expected_package}"
                )
                continue
            if field == "code_generator_version":
                _verify_agent_storage_codegen(root, label, edge, raw_assertion, errors)
                continue
        elif manifest_kind == "agent-storage-codegen":
            errors.append(
                f"{label}: codegen assertion is only allowed for {AGENT_STORAGE_EDGE}"
            )
            continue
        if not (agent_system or agent_storage) and manifest_kind == "uv-lock":
            errors.append(
                f"{label}: uv.lock assertion is only allowed for {AGENT_SYSTEM_EDGE} or {AGENT_STORAGE_EDGE}"
            )
            continue
        if capability_iam:
            if field == "runtime_package_version":
                if (
                    manifest_kind != "npm-file-archive"
                    or raw_assertion.get("repository_path") != CAPABILITY_REPOSITORY
                    or raw_assertion.get("path") != "package.json"
                    or raw_assertion.get("package_name") != IAM_SDK_PACKAGE
                    or raw_assertion.get("declared_value")
                    != f"{IAM_SDK_PACKAGE}@{raw_assertion.get('version')}"
                ):
                    errors.append(
                        f"{label}: requires the pinned Capability IAM SDK archive"
                    )
                    continue
                _verify_capability_iam_archive(root, edge, raw_assertion, errors)
                continue
            if (
                manifest_kind != "npm-package-json"
                or raw_assertion.get("repository_path") != IAM_REPOSITORY
                or raw_assertion.get("repository_commit")
                != owner.get("repository_commit")
                or raw_assertion.get("path") != IAM_SDK_MANIFEST
                or raw_assertion.get("package_name") != IAM_SDK_GENERATOR
            ):
                errors.append(
                    f"{label}: generator must be pinned to the IAM owner SDK manifest"
                )
                continue
        elif manifest_kind == "npm-file-archive":
            errors.append(
                f"{label}: archive assertion is only allowed for {CAPABILITY_IAM_EDGE}"
            )
            continue
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
