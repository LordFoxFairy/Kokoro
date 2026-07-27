#!/usr/bin/env python3
"""Enforce the isolation rule that separates the GA runtime from Platform modules.

Kokoro has two isolation keys and they are not interchangeable:

* ``siteId`` is the Platform business boundary. Platform modules resolve it,
  narrow it hop by hop, and enforce it at the effect point.
* ``namespace`` is the GA runtime's *only* isolation key. It is opaque: GA never
  learns which Site, user, owner or workspace it belongs to, and never parses
  business meaning out of it.

That asymmetry is what lets GA stay a general execution runtime instead of a
tenant-aware business service. It is easy to erode: one convenience field on a
run request, one ``user:{id}`` namespace prefix, and GA quietly becomes a second
place where tenancy is decided -- with none of the Platform's enforcement.

The rule was written down in the codebase map but nothing checked it, so this
gate freezes the currently-clean state. It reads GA source only; the Platform
side is governed by the boundary registry, which independently rejects a
``namespace``-scoped operation carrying any of these fields.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE = ROOT / "kokoro-agent" / "src"

# Platform identity axes. GA consumes none of them.
FORBIDDEN_AXES = (
    "site_id",
    "siteId",
    "owner_id",
    "ownerId",
    "workspace_id",
    "workspaceId",
    "user_id",
    "userId",
)

# A namespace is opaque. Composing one from a business identity re-introduces the
# tenancy GA is supposed not to know, just spelled as a string.
NAMESPACE_PREFIX_RE = re.compile(r"""["'](?:user|team|site|workspace|owner|tenant):\{?""")

# ``namespace`` is GA's *only* isolation key, so an absent one is not a weaker scope -- it is no
# scope. Typing it optional, or giving it a default, makes "a run belonging to nobody" expressible,
# and every Platform fail-open found so far began exactly there: a missing isolation value degrading
# to no isolation instead of a refusal. Today every occurrence is ``str`` or ``NonEmptyStr``; this
# freezes that.
#
# ``namespace: list[str]`` is deliberately still allowed: LangGraph streams use that name for a node
# path, which is not an isolation key and never reaches a tenancy decision.
# The annotation only: everything up to the comma, closing paren or end of line that ends it.
# Scanning further would read a function's ``-> None`` return type as if it were the parameter's.
NAMESPACE_OPTIONAL_RE = re.compile(r"\bnamespace\s*:\s*(?P<annotation>[^,)\n]+)")


def namespace_is_optional(annotation: str) -> bool:
    annotation = annotation.strip()
    if "=" in annotation:  # a default makes the argument omittable
        return True
    return bool(re.search(r"\b(?:None|Optional)\b", annotation))

AXIS_RE = re.compile(r"\b(?P<axis>%s)\b" % "|".join(FORBIDDEN_AXES))

SKIP_DIRECTORIES = {"__pycache__", ".venv", "node_modules", ".git"}


class GaIsolationError(Exception):
    def __init__(self, code: str, detail: str, *, preformatted: bool = False) -> None:
        super().__init__(detail if preformatted else f"{code}: {detail}")
        self.code = code


def python_sources(root: Path) -> list[Path]:
    if not root.is_dir():
        raise GaIsolationError("ga_isolation_source_missing", str(root))
    files = [
        path
        for path in sorted(root.rglob("*.py"))
        if not any(part in SKIP_DIRECTORIES for part in path.parts)
    ]
    if not files:
        raise GaIsolationError("ga_isolation_no_sources", str(root))
    return files


def scan(root: Path) -> tuple[int, list[str]]:
    violations: list[str] = []
    files = python_sources(root)
    for path in files:
        rel = path.relative_to(root.parent.parent) if root.parent.parent in path.parents else path
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            for match in AXIS_RE.finditer(line):
                violations.append(
                    f"ga_isolation_identity_axis: {rel}:{number}: {match.group('axis')} "
                    "is a Platform identity axis; GA consumes only the opaque namespace"
                )
            if NAMESPACE_PREFIX_RE.search(line):
                violations.append(
                    f"ga_isolation_namespace_composed: {rel}:{number}: a namespace must stay "
                    "opaque and must not be built from a business identity prefix"
                )
            optional = NAMESPACE_OPTIONAL_RE.search(line)
            if optional is not None and namespace_is_optional(optional.group("annotation")):
                violations.append(
                    f"ga_isolation_namespace_optional: {rel}:{number}: namespace is GA's only "
                    "isolation key; typing it optional or defaulting it makes an unscoped run "
                    "expressible"
                )
    return len(files), violations


def run(source: Path) -> str:
    scanned, violations = scan(source)
    if violations:
        # Each violation already carries its own code, so do not prefix again.
        raise GaIsolationError(
            violations[0].split(":", 1)[0], "; ".join(violations), preformatted=True
        )
    return (
        f"ga_isolation_ok: {scanned} GA source files, "
        f"0 of {len(FORBIDDEN_AXES)} Platform identity axes present, "
        "namespace never optional"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    args = parser.parse_args(argv)
    try:
        sys.stdout.write(run(args.source) + "\n")
    except GaIsolationError as exc:
        sys.stderr.write(f"{exc}\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
