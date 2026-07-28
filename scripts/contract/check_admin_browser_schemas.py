#!/usr/bin/env python3
"""Keep the Admin browser's hand-written readers honest against the published contract.

``kokoro-web/apps/admin/lib/schemas.ts`` validates what the browser reads from the
Admin gateway. The wire shape is owned by ``contract/openapi/admin-web-v1.yaml``.
Nothing tied the two together, so the contract could drop or rename a field and the
browser would keep reading it -- silently ``undefined`` at runtime, no build error.

Why this is a gate and not a generator
--------------------------------------
The obvious move is to generate the browser validators from the contract and delete
the hand-written file. For part of this surface that would *lose* checking. The
gateway validates downstream rows only to ``z.array(z.record(z.unknown()))``, so the
contract declares ``ResourceRow`` with no properties at all and
``additionalProperties: true`` (recorded there as open decision D4). Generating from
that yields a validator which accepts anything, while the hand-written Site, credit
account, and identity readers name the fields their screens consume. The
hand-written file currently encodes *more* field knowledge than the contract does.

So the browser keeps its lenient readers -- a dirty row degrades one row instead of
blanking the page -- and this gate proves they do not contradict the contract:

* every field the browser reads must be declared by the contract schema, and
* a browser schema mapped onto a contract schema with no field contract is counted
  and printed, never presented as verified.

When D4 is decided and rows get a real shape, that count drops and generation
becomes the better answer for those schemas.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OPENAPI = ROOT / "contract" / "openapi" / "admin-web-v1.yaml"
DEFAULT_SCHEMAS = ROOT / "kokoro-web" / "apps" / "admin" / "lib" / "schemas.ts"

# Which contract schema each browser reader mirrors. Every exported object schema must
# appear here: an unmapped one fails, so adding a reader forces this decision rather
# than quietly escaping the check.
SCHEMA_MAP = {
    "siteSchema": "ResourceRow",
    "creditAccountSchema": "ResourceRow",
    "identitySchema": "ResourceRow",
    "user360Schema": "User360",
    # The browser reads the unwrapped `data`; a deferred action carries this shape.
    "actionResultSchema": "ActionPendingApproval",
    "meSchema": "Me",
    "actionMetaSchema": "AdminActionManifest",
    "moduleManifestSchema": "ModuleStatus",
}

# Readers with no contract counterpart, and why. Hub owns these payloads; they reach
# the browser through the gateway's opaque /api/action passthrough and are not part of
# the Admin browser contract.
UNCONTRACTED = {
    "skillUploadPreviewSchema": "hub UploadPreview, proxied opaquely through /api/action",
    "skillUploadConfirmSchema": "hub ConfirmResult[], proxied opaquely through /api/action",
}

EXPORT_RE = re.compile(
    r"^export const (?P<name>\w+) = z\s*$|^export const (?P<inline>\w+) = z\.object\(\{"
)
FIELD_RE = re.compile(r"^\s{2}(?P<field>[A-Za-z_]\w*):")


class BrowserSchemaError(Exception):
    def __init__(self, code: str, detail: str, *, preformatted: bool = False) -> None:
        super().__init__(detail if preformatted else f"{code}: {detail}")
        self.code = code


def parse_browser_schemas(text: str) -> dict[str, list[str]]:
    """Top-level fields of each ``export const X = z.object({...})``.

    Only depth-one fields are read. Nested inline objects belong to the field that
    holds them and are checked through that field's own contract entry.
    """
    schemas: dict[str, list[str]] = {}
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        match = re.match(r"^export const (\w+) = z\.object\(\{\s*$", lines[index])
        if match is None:
            index += 1
            continue
        name = match.group(1)
        fields: list[str] = []
        depth = 1
        index += 1
        while index < len(lines) and depth > 0:
            line = lines[index]
            if depth == 1:
                field = FIELD_RE.match(line)
                if field is not None:
                    fields.append(field.group("field"))
            depth += (
                line.count("{") + line.count("(") - line.count("}") - line.count(")")
            )
            index += 1
        schemas[name] = fields
    return schemas


def contract_properties(schemas: dict, name: str) -> tuple[set[str], bool]:
    """Declared property names, and whether the schema models any fields at all."""
    node = schemas.get(name)
    if node is None:
        raise BrowserSchemaError("admin_browser_contract_schema_missing", name)
    if "oneOf" in node or "anyOf" in node:
        names: set[str] = set()
        modelled = False
        for branch in node.get("oneOf", node.get("anyOf", [])):
            ref = branch.get("$ref")
            target = ref.rsplit("/", 1)[-1] if ref else None
            if target is None:
                names |= set(branch.get("properties", {}))
                modelled = modelled or bool(branch.get("properties"))
                continue
            branch_names, branch_modelled = contract_properties(schemas, target)
            names |= branch_names
            modelled = modelled or branch_modelled
        return names, modelled
    properties = node.get("properties", {})
    return set(properties), bool(properties)


def run(openapi: Path, schemas_path: Path) -> str:
    document = yaml.safe_load(openapi.read_text(encoding="utf-8"))
    contract = document.get("components", {}).get("schemas", {})
    if not contract:
        raise BrowserSchemaError("admin_browser_contract_empty", str(openapi))

    browser = parse_browser_schemas(schemas_path.read_text(encoding="utf-8"))
    if not browser:
        # Reading clean because the parser stopped matching is the failure to avoid.
        raise BrowserSchemaError("admin_browser_no_schemas", str(schemas_path))

    violations: list[str] = []
    unmodelled: list[str] = []
    checked_fields = 0
    for name, fields in sorted(browser.items()):
        if name in UNCONTRACTED:
            continue
        target = SCHEMA_MAP.get(name)
        if target is None:
            violations.append(
                f"admin_browser_schema_unmapped: {name} has no contract counterpart; map it in "
                "SCHEMA_MAP or record it in UNCONTRACTED with a reason"
            )
            continue
        declared, modelled = contract_properties(contract, target)
        if not modelled:
            unmodelled.append(f"{name}->{target}")
            continue
        for field in fields:
            checked_fields += 1
            if field not in declared:
                violations.append(
                    f"admin_browser_field_undeclared: {name}.{field} is read by the browser but "
                    f"{target} does not declare it"
                )

    stale = sorted(set(SCHEMA_MAP) - set(browser)) + sorted(
        set(UNCONTRACTED) - set(browser)
    )
    for name in stale:
        violations.append(
            f"admin_browser_mapping_stale: {name} is mapped but no longer exists in the reader"
        )

    if violations:
        raise BrowserSchemaError(
            violations[0].split(":", 1)[0],
            "; ".join(sorted(violations)),
            preformatted=True,
        )

    return (
        f"admin_browser_schemas_ok: {len(browser)} browser schemas, {checked_fields} fields "
        f"proven against the contract, {len(unmodelled)} mapped to a schema with no field "
        f"contract ({', '.join(sorted(unmodelled)) or 'none'}), "
        f"{len(UNCONTRACTED)} uncontracted by design"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--openapi", type=Path, default=DEFAULT_OPENAPI)
    parser.add_argument("--schemas", type=Path, default=DEFAULT_SCHEMAS)
    args = parser.parse_args(argv)
    try:
        sys.stdout.write(run(args.openapi, args.schemas) + "\n")
    except BrowserSchemaError as exc:
        sys.stderr.write(f"{exc}\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
