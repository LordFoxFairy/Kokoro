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
SESSION_AGENT_EVENT_TS = ROOT / "kokoro-session/src/domain/agent-event.ts"
SESSION_EVENT_TS = ROOT / "kokoro-session/src/domain/session-event.ts"
AGENT_EVENT_PY = ROOT / "kokoro-agent/src/kokoro_agent/domain/agent_event.py"

GENERATED_HEADER_TS = (
    "// DO NOT EDIT — generated from contract/events.yaml by contract/generate.py.\n"
    "// Run `python3 contract/generate.py` after changing the contract.\n"
)
GENERATED_HEADER_PY = (
    "# DO NOT EDIT — generated from contract/events.yaml by contract/generate.py.\n"
    "# Run `python3 contract/generate.py` after changing the contract.\n"
)


def load_spec() -> dict:
    return yaml.safe_load(YAML_PATH.read_text())


def _camel_to_snake(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def _field_type(spec: dict, snake_field: str, view: str) -> str:
    """Abstract type for a field in a view: view override > field_types > default."""
    override = spec.get("view_field_types", {}).get(view, {})
    if snake_field in override:
        return override[snake_field]
    return spec.get("field_types", {}).get(snake_field, "string_nonempty")


def _ts_of(spec: dict, t: str) -> str:
    enums = spec["enums"]
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
    if t.startswith("enum:"):
        return " | ".join(f'"{v}"' for v in enums[t[5:]])
    raise ValueError(f"unmapped field type {t!r}")


def _ts_type(spec: dict, camel_field: str, view: str = "render") -> str:
    return _ts_of(spec, _field_type(spec, _camel_to_snake(camel_field), view))


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


def _zod_of(spec: dict, t: str) -> str:
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
    raise ValueError(f"unmapped field type {t!r}")


def _zod_type(spec: dict, snake_field: str, view: str) -> str:
    return _zod_of(spec, _field_type(spec, snake_field, view))


def _ts_union_zod(values: list[str]) -> str:
    return ", ".join(f'"{v}"' for v in values)


def _event_const(event: str) -> str:
    parts = re.split(r"[.\-]", event)
    return parts[0] + "".join(p.capitalize() for p in parts[1:]) + "Schema"


def _agui_events(spec: dict, *, web_extra: bool) -> list[tuple[str, list[tuple[str, bool]]]]:
    """(event, [(field, optional)]) for the agui-out view, agui_only first then kinds.

    web_extra=True appends web-tolerated optional fields (web wire-in only).
    """
    out: list[tuple[str, list[tuple[str, bool]]]] = []

    def fields(node: dict) -> list[tuple[str, bool]]:
        base = [(f, False) for f in (node.get("payload") or [])]
        extra = (
            [(f, True) for f in (node.get("agui_out_web_extra") or [])]
            if web_extra
            else []
        )
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
    events = _agui_events(spec, web_extra=True)
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
        payload_optional = set(spec.get("payload_optional") or [])
        for fname, optional in payload:
            note = notes.get(f"{event}.{fname}")
            if note:
                L.append(f"      // {note}")
            opt = ".optional()" if optional or fname in payload_optional else ""
            L.append(f"      {fname}: {_zod_type(spec, fname, 'web')}{opt},")
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
    L.append("")
    # Single source for the live EventSource's named listeners: a hand-kept parallel
    # list silently drops any event kind it forgets (the live stream uses named SSE
    # events), so derive it from the contract here.
    L.append("export const transportEventNames = [")
    for event, _ in events:
        L.append(f'  "{event}",')
    L.append("] as const")
    return "\n".join(L) + "\n"


# --------------------------------------------------------------------------- #
# session agent-event.ts (agent-out re-validation, Zod by "kind") +
# session session-event.ts (agui-out, Zod by "event")
# --------------------------------------------------------------------------- #

_ENVELOPE_ZOD_SESSION = {
    "event_id": "z.string().min(1)",
    "seq": "z.number().int().nonnegative()",
    "session_id": "z.string().min(1)",
    "conversation_id": "z.string().min(1)",
    "run_id": "z.string().min(1)",
    "timestamp": "z.string().min(1)",  # session keeps timestamp a plain non-empty string
}


def _zod_obj_inline(spec: dict, field_names: list[str], view: str) -> str:
    if not field_names:
        return "z.object({}).strict()"
    optional = set(spec.get("payload_optional") or [])
    parts = ", ".join(
        f"{f}: {_zod_type(spec, f, view)}{'.optional()' if f in optional else ''}"
        for f in field_names
    )
    return f"z.object({{ {parts} }}).strict()"


def _agent_events(spec: dict) -> list[tuple[str, list[str]]]:
    out: list[tuple[str, list[str]]] = []
    for entry in spec["kinds"].values():
        ao = entry.get("agent_out")
        if ao and "kind" in ao:
            out.append((ao["kind"], list(ao.get("payload") or [])))
    return out


def emit_session_agent_event(spec: dict) -> str:
    L: list[str] = [GENERATED_HEADER_TS.rstrip("\n"), "", 'import { z } from "zod"', ""]
    L.append(
        "const envelope = { run_id: z.string().min(1), "
        "seq: z.number().int().nonnegative() }"
    )
    L.append("")
    L.append('export const agentEventSchema = z.discriminatedUnion("kind", [')
    for kind, payload in _agent_events(spec):
        p = _zod_obj_inline(spec, payload, "agent_out")
        L.append(
            f'  z.object({{ kind: z.literal("{kind}"), ...envelope, '
            f"payload: {p} }}).strict(),"
        )
    L.append("])")
    L.append("")
    L.append("export type AgentEvent = z.infer<typeof agentEventSchema>")
    return "\n".join(L) + "\n"


def emit_session_event(spec: dict) -> str:
    notes = spec.get("notes", {})
    env = spec["envelope"]["agui_out"]
    L: list[str] = [GENERATED_HEADER_TS.rstrip("\n"), "", 'import { z } from "zod"', ""]
    L.append('export type SessionEventName = z.infer<typeof sessionEventSchema>["event"]')
    L.append("")
    L.append("export type SessionEvent = {")
    L.append("  event: SessionEventName")
    for f in env:
        if f == "seq" and "envelope.seq" in notes:
            L.append(f"  // {notes['envelope.seq']}")
        L.append(f"  {f}: {'number' if f == 'seq' else 'string'}")
    L.append("  payload: Record<string, unknown>")
    L.append("}")
    L.append("")
    L.append("const envelopeFields = {")
    for f in env:
        L.append(f"  {f}: {_ENVELOPE_ZOD_SESSION[f]},")
    L.append("}")
    L.append("")
    L.append('const sessionEventSchema = z.discriminatedUnion("event", [')
    for event, payload in _agui_events(spec, web_extra=False):
        names = [f for f, _opt in payload]
        p = _zod_obj_inline(spec, names, "agui_out")
        L.append(
            f'  z.object({{ event: z.literal("{event}"), ...envelopeFields, '
            f"payload: {p} }}).strict(),"
        )
    L.append("])")
    L.append("")
    L.append("type SessionEventUnion = z.infer<typeof sessionEventSchema>")
    L.append("export type AguiPayload<E extends SessionEventName> = Extract<")
    L.append("  SessionEventUnion,")
    L.append("  { event: E }")
    L.append('>["payload"]')
    L.append("")
    L.append("export function parseSessionEvent(input: unknown): SessionEvent {")
    L.append("  return sessionEventSchema.parse(input)")
    L.append("}")
    return "\n".join(L) + "\n"


# --------------------------------------------------------------------------- #
# agent agent_event.py (agent-out, Python: AgentKind Literal + payload doc table)
# --------------------------------------------------------------------------- #


def _py_type(spec: dict, snake_field: str) -> str:
    t = _field_type(spec, snake_field, "agent_out")
    enums = spec["enums"]
    if t in ("string_nonempty", "string"):
        return "str"
    if t == "boolean":
        return "bool"
    if t == "record":
        return "dict[str, object]"
    if t == "unknown":
        return "object"
    if t == "array_unknown":
        return "list[object]"
    if t == "todo_list":
        status = "|".join(f'"{v}"' for v in enums["todo_status"])
        return '[{"content": str, "status": ' + status + "}]"
    if t.startswith("enum:"):
        return "|".join(f'"{v}"' for v in enums[t[5:]])
    raise ValueError(f"unmapped field type {t!r}")


def _py_doc_shape(spec: dict, payload: list[str]) -> str:
    if not payload:
        return "{}"
    parts = ", ".join(f'"{f}": {_py_type(spec, f)}' for f in payload)
    return "{" + parts + "}"


def emit_agent_event_py(spec: dict) -> str:
    events = _agent_events(spec)
    kinds = [k for k, _ in events]
    width = max(len(k) for k in kinds)
    L: list[str] = [
        GENERATED_HEADER_PY.rstrip("\n"),
        "from __future__ import annotations",
        "",
        "from typing import Literal, TypeGuard, get_args",
        "",
        "from pydantic import BaseModel, ConfigDict",
        "",
        "AgentKind = Literal[",
    ]
    for k in kinds:
        L.append(f'    "{k}",')
    L.append("]")
    L.append("")
    L.append("_AGENT_KINDS: frozenset[str] = frozenset(get_args(AgentKind))")
    L.append("")
    L.append("")
    L.append("def is_agent_kind(kind: str) -> TypeGuard[AgentKind]:")
    L.append("    return kind in _AGENT_KINDS")
    L.append("")
    L.append("# Per-kind ``payload`` shapes (the payload stays a loose dict here; strict")
    L.append("# per-kind validation is kokoro-session's job at the Zod boundary). Documented")
    L.append("# so the DeepAgents emitter and the session normalizer share one contract:")
    for k, payload in events:
        L.append(f"#   {k.ljust(width)}  {_py_doc_shape(spec, payload)}")
    L.append("")
    L.append("")
    L.append("class AgentEvent(BaseModel):")
    L.append('    """A raw execution-side event authored by kokoro-agent.')
    L.append("")
    L.append("    The agent only fills execution semantics: ``kind``, ``run_id`` and a")
    L.append("    monotonic ``seq``. It never assigns ``event_id`` / ``timestamp`` / ``owner_id``")
    L.append("    — those belong to kokoro-session's normalization layer.")
    L.append('    """')
    L.append("")
    L.append('    model_config = ConfigDict(strict=True, extra="forbid")')
    L.append("")
    L.append("    kind: AgentKind")
    L.append("    run_id: str")
    L.append("    seq: int")
    L.append("    payload: dict[str, object]")
    return "\n".join(L) + "\n"


EMITTERS = {
    WEB_RENDER_TS: emit_web_render,
    WEB_SCHEMA_TS: emit_web_schema,
    SESSION_AGENT_EVENT_TS: emit_session_agent_event,
    SESSION_EVENT_TS: emit_session_event,
    AGENT_EVENT_PY: emit_agent_event_py,
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
