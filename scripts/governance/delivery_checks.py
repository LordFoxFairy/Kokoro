"""Documentation, container and software-supply-chain delivery checks."""

from __future__ import annotations

import re

from .ten_repository_standard import (
    REQUIRED_REPOSITORY_DIRECTORIES,
    REQUIRED_REPOSITORY_DOCUMENTS,
    ROOT,
    Failure,
    add,
    has_exact_relative_directory,
    has_exact_relative_file,
    read_text,
)


def check_delivery(repository_name: str, failures: list[Failure]) -> None:
    repository = ROOT / repository_name
    for relative in REQUIRED_REPOSITORY_DOCUMENTS:
        if not has_exact_relative_file(repository, relative):
            add(failures, repository_name, "documentation", f"{relative} is missing")
    for relative in REQUIRED_REPOSITORY_DIRECTORIES:
        if not has_exact_relative_directory(repository, relative):
            add(failures, repository_name, "documentation", f"{relative}/ is missing")

    dockerfile = repository / "Dockerfile"
    if not dockerfile.is_file():
        add(failures, repository_name, "container", "Dockerfile is missing")
    else:
        docker_text = read_text(dockerfile)
        build_args = dict(
            re.findall(
                r"^ARG\s+([A-Za-z_][A-Za-z0-9_]*)=([^\s]+)", docker_text, re.MULTILINE
            )
        )
        declared_stages: set[str] = set()
        for match in re.finditer(
            r"^FROM\s+([^\s]+)(?:\s+AS\s+([^\s]+))?",
            docker_text,
            re.MULTILINE | re.IGNORECASE,
        ):
            image = match.group(1)
            variable = re.fullmatch(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}", image)
            resolved_image = (
                build_args.get(variable.group(1), "") if variable else image
            )
            if (
                image.lower() not in declared_stages
                and image.lower() != "scratch"
                and "@sha256:" not in resolved_image
            ):
                add(
                    failures,
                    repository_name,
                    "container-reproducibility",
                    f"Dockerfile FROM source {image!r} must be pinned by sha256 digest",
                )
            if match.group(2):
                declared_stages.add(match.group(2).lower())
        runtime_users = re.findall(
            r"^USER\s+([^\s]+)", docker_text, re.MULTILINE | re.IGNORECASE
        )
        if not runtime_users or runtime_users[-1].lower() in {"0", "root", "root:root"}:
            add(
                failures,
                repository_name,
                "container",
                "runtime image must declare a non-root USER",
            )
        if not re.search(r"^HEALTHCHECK\b", docker_text, re.MULTILINE | re.IGNORECASE):
            add(
                failures,
                repository_name,
                "container",
                "runtime image must declare HEALTHCHECK",
            )

    workflows = repository / ".github" / "workflows"
    ci = workflows / "ci.yml"
    release = workflows / "release-image.yml"
    for workflow in (ci, release):
        if not workflow.is_file():
            continue
        text = read_text(workflow)
        for line_number, line in enumerate(text.splitlines(), start=1):
            action = re.search(r"\buses:\s*([^\s#]+)", line)
            if not action or action.group(1).startswith("./"):
                continue
            reference = action.group(1).rsplit("@", 1)[-1]
            if not re.fullmatch(r"[0-9a-f]{40}", reference):
                add(
                    failures,
                    repository_name,
                    "supply-chain",
                    f"{workflow.relative_to(repository)}:{line_number} action must be pinned to a full commit SHA",
                )

    if ci.is_file() and not re.search(
        r"trivy|grype|dependency-review|dependency\s+review|pnpm\s+audit|govulncheck|gitleaks",
        read_text(ci),
        re.IGNORECASE,
    ):
        add(
            failures,
            repository_name,
            "security-gate",
            ".github/workflows/ci.yml has no dependency/source/secret scan",
        )
    if release.is_file():
        release_text = read_text(release)
        required_release_markers = {
            "image vulnerability scan": r"trivy|grype",
            "SBOM": r"\bsbom\s*:",
            "build provenance": r"\bprovenance\s*:",
            "digest signature or attestation": r"cosign\s+sign|attest-build-provenance|attestation",
        }
        for description, pattern in required_release_markers.items():
            if not re.search(pattern, release_text, re.IGNORECASE):
                add(
                    failures,
                    repository_name,
                    "supply-chain",
                    f".github/workflows/release-image.yml has no {description}",
                )
        push_match = re.search(r"^\s*push:\s*true\s*$", release_text, re.MULTILINE)
        if push_match:
            before_push = release_text[: push_match.start()]
            has_local_candidate = re.search(
                r"^\s*load:\s*true\s*$|\bdocker\s+build\b",
                before_push,
                re.MULTILINE | re.IGNORECASE,
            )
            has_candidate_scan = re.search(
                r"\bimage-ref\s*:", before_push, re.IGNORECASE
            )
            if not has_local_candidate or not has_candidate_scan:
                add(
                    failures,
                    repository_name,
                    "supply-chain",
                    ".github/workflows/release-image.yml must build and scan a local candidate before push",
                )
