#!/usr/bin/env python3
"""Deterministic code generator for the 13-kind event contract.

contract/events.yaml is the single source. This emits the schema mirror files
(no-compat clean regeneration; behavior-equivalence verified by each repo's test
suite + contract/verify.py + the SSE loopback gate). Run `--check` in CI to fail
on drift between generated output and the committed files.

  python3 contract/generate.py          # write the mirror files
  python3 contract/generate.py --check   # diff generated vs disk, non-zero on drift

Design: docs/superpowers/specs/2026-06-14-contract-codegen-design.md
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
YAML_PATH = Path(__file__).resolve().parent / "events.yaml"

WEB_RENDER_TS = ROOT / "kokoro-web/src/domain/session-stream-event.ts"
WEB_SCHEMA_TS = ROOT / "kokoro-web/src/infrastructure/transport-event-schema.ts"

GENERATED_HEADER_TS = (
    "// DO NOT EDIT — generated from contract/events.yaml by contract/generate.py.\n"
    "// Run `python3 contract/generate.py` after changing the contract.\n"
)


def load_spec() -> dict:
    return yaml.safe_load(YAML_PATH.read_text())


def _camel_to_snake(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def _ts_type(spec: dict, camel_field: str) -> str:
    """TS type for a render (camelCase) field, resolved via field_types."""
    snake = _camel_to_snake(camel_field)
    t = spec.get("field_types", {}).get(snake, "string_nonempty")
    if t in ("string_nonempty", "string"):
        return "string"
    if t == "boolean":
        return "boolean"
    if t == "record":
        return "Record<string, unknown>"
    if t == "unknown":
        return "unknown"
    if t == "array_unknown":
        return "unknown[]"
    if t == "todo_list":
        return "SessionTodo[]"
    if t == "enum:message_role":
        return "SessionMessageRole"
    if t == "enum:subagent_source":
        return '"built-in" | "config-custom" | "runtime-custom"'
    raise ValueError(f"unmapped field type {t!r} for field {camel_field!r}")


def _ts_union(values: list[str]) -> str:
    return " | ".join(f'"{v}"' for v in values)


def _render_arms(spec: dict) -> list[tuple[str, list[str]]]:
    """(dash-kind, camelCase payload) for every projected render arm, yaml order."""
    arms: list[tuple[str, list[str]]] = []
    for entry in spec["kinds"].values():
        r = entry.get("render")
        if not r or r.get("absent"):
            continue
        arms.append((r["kind"], list(r.get("payload") or [])))
    for node in spec["agui_only"].values():
        r = node["render"]
        if r.get("absent"):
            continue
        arms.append((r["kind"], list(r.get("payload") or [])))
    return arms


def emit_web_render(spec: dict) -> str:
    enums = spec["enums"]
    optional = set(spec.get("render_optional") or [])
    notes = spec.get("notes", {})
    env = spec["envelope"]["render"]  # [eventId, seq, sessionId, conversationId, runId]

    lines: list[str] = [GENERATED_HEADER_TS.rstrip("\n"), ""]
    lines.append(f"export type SessionMessageRole = {_ts_union(enums['message_role'])}")
    lines.append("")
    lines.append(f"export type SessionTodoStatus = {_ts_union(enums['todo_status'])}")
    lines.append("")
    lines.append("export type SessionTodo = {")
    lines.append("  content: string")
    lines.append("  status: SessionTodoStatus")
    lines.append("}")
    lines.append("")
    if "envelope.seq" in notes:
        lines.append(f"// {notes['envelope.seq']}")
    lines.append("export type SessionStreamEvent =")

    arms = _render_arms(spec)
    for i, (kind, payload) in enumerate(arms):
        lines.append("  | {")
        lines.append(f'      kind: "{kind}"')
        # envelope fields: eventId, seq (number), the rest strings
        for field_name in env:
            ts = "number" if field_name == "seq" else "string"
            lines.append(f"      {field_name}: {ts}")
        for camel in payload:
            opt = "?" if camel in optional else ""
            lines.append(f"      {camel}{opt}: {_ts_type(spec, camel)}")
        lines.append("    }")
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- #
# web transport-event-schema.ts (agui-out wire-in, Zod + web-extra optionals)
# --------------------------------------------------------------------------- #

_ENVELOPE_ZOD = {
    "event_id": "z.string().min(1)",
    "seq": "z.number().int().nonnegative()",
    "session_id": "z.string().min(1)",
    "conversation_id": "z.string().min(1)",
    "run_id": "z.string().min(1)",
    "timestamp": "z.string().datetime()",
}


def _zod_type(spec: dict, snake_field: str) -> str:
    t = spec.get("field_types", {}).get(snake_field, "string_nonempty")
    enums = spec["enums"]
    if t == "string_nonempty":
        return "z.string().min(1)"
    if t == "string":
        return "z.string()"
    if t == "boolean":
        return "z.boolean()"
    if t == "record":
        return "z.record(z.unknown())"
    if t == "unknown":
        return "z.unknown()"
    if t == "array_unknown":
        return "z.array(z.unknown())"
    if t == "todo_list":
        status = _ts_union_zod(enums["todo_status"])
        return (
            "z.array(z.object({ content: z.string(), status: "
            f"z.enum([{status}]) }}).strict())"
        )
    if t.startswith("enum:"):
        return f"z.enum([{_ts_union_zod(enums[t[5:]])}])"
    raise ValueError(f"unmapped field type {t!r} for {snake_field!r}")


def _ts_union_zod(values: list[str]) -> str:
    return ", ".join(f'"{v}"' for v in values)


def _event_const(event: str) -> str:
    parts = re.split(r"[.\-]", event)
    return parts[0] + "".join(p.capitalize() for p in parts[1:]) + "Schema"


def _agui_web_events(spec: dict) -> list[tuple[str, list[tuple[str, bool]]]]:
    """(event, [(field, optional)]) for web wire-in, agui_only first then kinds."""
    out: list[tuple[str, list[tuple[str, bool]]]] = []

    def fields(node: dict) -> list[tuple[str, bool]]:
        base = [(f, False) for f in (node.get("payload") or [])]
        extra = [(f, True) for f in (node.get("agui_out_web_extra") or [])]
        return base + extra

    for event, node in spec["agui_only"].items():
        out.append((event, fields(node["agui_out"])))
    for entry in spec["kinds"].values():
        ag = entry.get("agui_out")
        if ag and "event" in ag:
            out.append((ag["event"], fields(ag)))
    return out


def emit_web_schema(spec: dict) -> str:
    notes = spec.get("notes", {})
    events = _agui_web_events(spec)
    L: list[str] = [GENERATED_HEADER_TS.rstrip("\n"), "", 'import { z } from "zod"', ""]

    # envelope schema
    L.append("const eventEnvelopeSchema = z")
    L.append("  .object({")
    L.append("    event: z.enum([")
    for event, _ in events:
        L.append(f'      "{event}",')
    L.append("    ]),")
    for f in spec["envelope"]["agui_out"]:
        if f == "seq" and "envelope.seq" in notes:
            L.append(f"    // {notes['envelope.seq']}")
        L.append(f"    {f}: {_ENVELOPE_ZOD[f]},")
    L.append("  })")
    L.append("  .strict()")
    L.append("")

    for event, payload in events:
        L.append(f"const {_event_const(event)} = eventEnvelopeSchema.extend({{")
        L.append(f'  event: z.literal("{event}"),')
        L.append("  payload: z")
        L.append("    .object({")
        for fname, optional in payload:
            note = notes.get(f"{event}.{fname}")
            if note:
                L.append(f"      // {note}")
            opt = ".optional()" if optional else ""
            L.append(f"      {fname}: {_zod_type(spec, fname)}{opt},")
        L.append("    })")
        L.append("    .strict(),")
        L.append("})")
        L.append("")

    L.append("const sessionEventSchema = z.union([")
    for event, _ in events:
        L.append(f"  {_event_const(event)},")
    L.append("])")
    L.append("")
    L.append("export type SessionTransportEvent = z.infer<typeof sessionEventSchema>")
    L.append("")
    L.append("export function parseTransportEvent(input: unknown): SessionTransportEvent {")
    L.append("  return sessionEventSchema.parse(input)")
    L.append("}")
    return "\n".join(L) + "\n"


EMITTERS = {
    WEB_RENDER_TS: emit_web_render,
    WEB_SCHEMA_TS: emit_web_schema,
}


def main(argv: list[str]) -> int:
    spec = load_spec()
    check = "--check" in argv
    drift = False
    for path, emit in EMITTERS.items():
        generated = emit(spec)
        if check:
            current = path.read_text() if path.exists() else ""
            if current != generated:
                print(f"DRIFT: {path.relative_to(ROOT)} differs from events.yaml")
                drift = True
        else:
            path.write_text(generated)
            print(f"wrote {path.relative_to(ROOT)}")
    if check and drift:
        print("\nRun `python3 contract/generate.py` and commit the result.")
        return 1
    if check:
        print(f"OK — {len(EMITTERS)} mirror(s) match events.yaml")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
