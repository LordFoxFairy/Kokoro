#!/usr/bin/env python3
"""Audit the non-negotiable V1 engineering rules across ten child repositories.

This structural gate complements, rather than replaces, each repository's own
lint, typecheck, test, build, schema and runtime verification. A non-zero result
is the work queue until every repository converges; it is never converted into
a false green baseline.
"""

from __future__ import annotations

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


def collect_failures() -> list[Failure]:
    failures: list[Failure] = []
    check_docs(failures)
    for repository in REPOSITORIES:
        check_common(repository, failures)
        check_delivery(repository, failures)
    for repository in TS_REPOSITORIES:
        check_typescript(repository, failures)
    check_web(failures)
    check_bff(failures)
    check_agent(failures)
    check_scheduler(failures)
    return sorted(
        failures, key=lambda failure: (failure.repository, failure.rule, failure.detail)
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="stable diagnostic output format",
    )
    args = parser.parse_args(argv)
    failures = collect_failures()

    if failures:
        if args.format == "json":
            print(
                json.dumps(
                    {
                        "status": "FAIL",
                        "repository_count": len(REPOSITORIES),
                        "violation_count": len(failures),
                        "violations": [
                            {
                                "repository": failure.repository,
                                "rule": failure.rule,
                                "detail": failure.detail,
                            }
                            for failure in failures
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
        else:
            print(f"FAIL ten-repository-standard ({len(failures)} rule violations)")
            for failure in failures:
                print(f"- [{failure.repository}] {failure.rule}: {failure.detail}")
        return 1

    if args.format == "json":
        print(
            json.dumps(
                {
                    "status": "PASS",
                    "repository_count": len(REPOSITORIES),
                    "violation_count": 0,
                    "violations": [],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(f"PASS ten-repository-standard ({len(REPOSITORIES)} repositories)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
