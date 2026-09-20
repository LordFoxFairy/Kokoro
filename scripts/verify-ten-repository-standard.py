#!/usr/bin/env python3
"""Audit the non-negotiable V1 engineering rules across ten child repositories.

This structural gate complements, rather than replaces, each repository's own
lint, typecheck, test, build, schema and runtime verification. A non-zero result
is the work queue until every repository converges; it is never converted into
a false green baseline.
"""

from __future__ import annotations

from dataclasses import asdict
import argparse
import json
import sys

from governance.delivery_checks import check_delivery
from governance.repository_checks import (
    check_common,
    check_docs,
    check_scheduler,
)
from governance.surface_checks import check_agent, check_bff, check_web
from governance.typescript_checks import check_typescript
from governance.ten_repository_standard import (
    REPOSITORIES,
    TS_REPOSITORIES,
    Failure,
)


def collect_audit() -> tuple[list[Failure], list[Failure]]:
    failures: list[Failure] = []
    unverified: list[Failure] = []
    check_docs(failures)
    for repository in REPOSITORIES:
        check_common(repository, failures)
        check_delivery(repository, failures)
    for repository in TS_REPOSITORIES:
        check_typescript(repository, failures, unverified)
    check_web(failures)
    check_bff(failures)
    check_agent(failures)
    check_scheduler(failures)

    def key(item: Failure) -> tuple[str, str, str]:
        return item.repository, item.rule, item.detail

    return sorted(failures, key=key), sorted(unverified, key=key)


def collect_failures() -> list[Failure]:
    """Policy violations only; toolchain availability is a separate channel."""
    return collect_audit()[0]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="stable diagnostic output format",
    )
    parser.add_argument(
        "--require-installed-tools",
        action="store_true",
        help="exit non-zero when installed TypeScript configuration cannot be verified",
    )
    args = parser.parse_args(argv)
    failures, unverified = collect_audit()
    failed = bool(failures or (args.require_installed_tools and unverified))
    status = "FAIL" if failed else "UNVERIFIED" if unverified else "PASS"
    if args.format == "json":
        print(
            json.dumps(
                {
                    "status": status,
                    "repository_count": len(REPOSITORIES),
                    "violation_count": len(failures),
                    "violations": [asdict(item) for item in failures],
                    "unverified_count": len(unverified),
                    "unverified": [asdict(item) for item in unverified],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(
            f"{status} ten-repository-standard ({len(failures)} rule violations, {len(unverified)} unverified)"
        )
        for label, items in (("violation", failures), ("unverified", unverified)):
            for item in items:
                print(f"- [{item.repository}] {label} {item.rule}: {item.detail}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
