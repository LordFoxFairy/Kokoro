#!/usr/bin/env python3
"""Deterministic codegen: contract/spec/*.yaml -> the three repos' contract/ mirrors."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SPEC = HERE / "spec"

AGENT = ROOT / "kokoro-agent/src/kokoro_agent/contract"
SESSION = ROOT / "kokoro-session/src/contract"
WEB = ROOT / "kokoro-web/src/contract"

EVENTS_SRC = "contract/spec/events.yaml"
CONTROL_SRC = "contract/spec/control.yaml"
STREAMS_SRC = "contract/spec/streams.yaml"
HTTP_SRC = "contract/spec/http.yaml"


def load(name: str) -> dict:
    return yaml.safe_load((SPEC / name).read_text())


def py_header(src: str) -> str:
    return (
        f"# GENERATED — DO NOT EDIT. Source: {src}\n"
        "# Regenerate: python3 contract/generate.py\n"
    )


def ts_header(src: str) -> str:
    return (
        f"// GENERATED — DO NOT EDIT. Source: {src}\n"
        "// Regenerate: python3 contract/generate.py\n"
    )


def pascal(name: str) -> str:
    return "".join(p.capitalize() for p in _split(name))


def camel(name: str) -> str:
    parts = _split(name)
    head = parts[0][:1].lower() + parts[0][1:]
    return head + "".join(p.capitalize() for p in parts[1:])


def _split(name: str) -> list[str]:
    out: list[str] = []
    for part in name.replace(".", "_").split("_"):
        out.append(part)
    return out


def enum_lit(values: list[str]) -> str:
    return ", ".join(f'"{v}"' for v in values)


# --------------------------------------------------------------------------- #
# abstract type system: scalar | enum:<n> | array:<inner> | object:<Name>
# --------------------------------------------------------------------------- #

_ZOD_SCALAR = {
    "string_nonempty": "z.string().min(1)",
    "string": "z.string()",
    "boolean": "z.boolean()",
    "int": "z.number().int()",
    "record": "z.record(z.unknown())",
    "string_map": "z.record(z.string())",
    "unknown": "z.unknown()",
    "literal_true": "z.literal(true)",
}
_PY_SCALAR = {
    "string_nonempty": "NonEmptyStr",
    "string": "str",
    "boolean": "bool",
    "int": "int",
    "record": "dict[str, JsonValue]",
    "string_map": "dict[str, str]",
    "unknown": "JsonValue",
}


def zod_type(t: str, enums: dict) -> str:
    if t in _ZOD_SCALAR:
        return _ZOD_SCALAR[t]
    if t.startswith("enum:"):
        return f"z.enum([{enum_lit(enums[t[5:]])}])"
    if t.startswith("array:"):
        return f"z.array({zod_type(t[6:], enums)})"
    if t.startswith("object:"):
        return f"{camel(t[7:])}Schema"
    raise ValueError(f"unmapped zod type {t!r}")


def enum_alias(name: str) -> str:
    # allowed_decisions reuses resume_decision but reads clearer as AllowedDecision.
    return "AllowedDecision" if name == "resume_decision" else pascal(name)


def py_type(t: str, aliases: dict[str, str]) -> str:
    if t in _PY_SCALAR:
        return _PY_SCALAR[t]
    if t.startswith("enum:"):
        return aliases[t[5:]]
    if t.startswith("array:"):
        return f"list[{py_type(t[6:], aliases)}]"
    if t.startswith("object:"):
        return t[7:]
    raise ValueError(f"unmapped python type {t!r}")


def enum_names_in(types: list[str]) -> list[str]:
    seen: list[str] = []
    for t in types:
        inner = t
        while inner.startswith("array:"):
            inner = inner[6:]
        if inner.startswith("enum:"):
            name = inner[5:]
            if name not in seen:
                seen.append(name)
    return seen


# --------------------------------------------------------------------------- #
# field emission
# --------------------------------------------------------------------------- #


def py_field(f: dict, aliases: dict[str, str]) -> str:
    base = py_type(f["type"], aliases)
    if f.get("optional") or f.get("nullable"):
        base = f"{base} | None"
    suffix = " = None" if f.get("optional") else ""
    return f"    {f['name']}: {base}{suffix}"


def ts_field(f: dict, enums: dict) -> str:
    z = zod_type(f["type"], enums)
    if f.get("nullable"):
        z += ".nullable()"
    if f.get("optional"):
        z += ".optional()"
    return f"{f['name']}: {z}"


# --------------------------------------------------------------------------- #
# object emission
# --------------------------------------------------------------------------- #


def py_object(obj: dict, aliases: dict[str, str]) -> list[str]:
    L = [f"class {obj['name']}(StrictModel):"]
    fields = obj.get("fields") or []
    if not fields:
        L.append("    pass")
        return L
    L += [py_field(f, aliases) for f in fields]
    return L


def ts_object(obj: dict, enums: dict, *, export: bool) -> list[str]:
    const = f"{camel(obj['name'])}Schema"
    kw = "export const" if export else "const"
    fields = obj.get("fields") or []
    if not fields:
        L = [f"{kw} {const} = z.object({{}}).strict()"]
    else:
        L = [f"{kw} {const} = z", "  .object({"]
        L += [f"    {ts_field(f, enums)}," for f in fields]
        L += ["  })", "  .strict()"]
    if export:
        L.append(f"export type {obj['name']} = z.infer<typeof {const}>")
    return L


# --------------------------------------------------------------------------- #
# events: payload field resolution
# --------------------------------------------------------------------------- #


def event_field_type(spec: dict, field: str) -> str:
    return spec["field_types"].get(field, "string_nonempty")


def event_payload_fields(spec: dict, payload: list[str]) -> list[dict]:
    optional = set(spec.get("payload_optional") or [])
    nullable = set(spec.get("payload_nullable") or [])
    fields: list[dict] = []
    for entry in payload:
        # 尾缀 `?` = 仅该 kind 局部可选（payload_optional 是全局按字段名生效，二者互补）。
        local_optional = entry.endswith("?")
        name = entry[:-1] if local_optional else entry
        fields.append(
            {
                "name": name,
                "type": event_field_type(spec, name),
                "optional": local_optional or name in optional,
                "nullable": name in nullable,
            }
        )
    return fields


def events_enum_aliases(spec: dict) -> dict[str, str]:
    types = [f["type"] for obj in spec["objects"] for f in obj["fields"]]
    for entry in spec["raw_kinds"]:
        types += [event_field_type(spec, f) for f in (entry.get("payload") or [])]
    return {name: enum_alias(name) for name in enum_names_in(types)}


# --------------------------------------------------------------------------- #
# agent/contract/events.py
# --------------------------------------------------------------------------- #

_PY_PREAMBLE = [
    "from typing import Annotated, Literal, Union",
    "",
    "from pydantic import BaseModel, ConfigDict, Field, JsonValue, StringConstraints, TypeAdapter",
    "",
    "NonEmptyStr = Annotated[str, StringConstraints(min_length=1)]",
]


def emit_events_py(spec: dict) -> str:
    enums = spec["enums"]
    notes = spec.get("notes", {})
    aliases = events_enum_aliases(spec)

    L = [py_header(EVENTS_SRC).rstrip("\n"), "from __future__ import annotations", ""]
    L += _PY_PREAMBLE
    L.append("NonNegInt = Annotated[int, Field(ge=0)]")
    L.append("")
    for name, alias in aliases.items():
        L.append(f"{alias} = Literal[{enum_lit(enums[name])}]")
    L += ["", "", "class StrictModel(BaseModel):", '    model_config = ConfigDict(strict=True, extra="forbid")']

    for obj in spec["objects"]:
        L += ["", ""] + py_object(obj, aliases)

    for entry in spec["raw_kinds"]:
        kind = entry["kind"]
        fields = event_payload_fields(spec, entry.get("payload") or [])
        L += ["", "", f"class {pascal(kind)}Payload(StrictModel):"]
        if not fields:
            L.append("    pass")
            continue
        for f in fields:
            note = notes.get(f"{kind}.{f['name']}")
            if note:
                L.append(f"    # {note}")
            L.append(py_field(f, aliases))

    for entry in spec["raw_kinds"]:
        name = pascal(entry["kind"])
        L += [
            "",
            "",
            f"class {name}(StrictModel):",
            f'    kind: Literal["{entry["kind"]}"]',
            "    run_id: NonEmptyStr",
            "    index: NonNegInt",
            "    timestamp: int",
            f"    payload: {name}Payload",
        ]

    names = [pascal(e["kind"]) for e in spec["raw_kinds"]]
    L += ["", "", "AgentEvent = Annotated[", "    Union["]
    L += [f"        {n}," for n in names]
    L += ["    ],", '    Field(discriminator="kind"),', "]", ""]
    L.append("agent_event_adapter: TypeAdapter[AgentEvent] = TypeAdapter(AgentEvent)")
    return "\n".join(L) + "\n"


# --------------------------------------------------------------------------- #
# agent/contract/control.py
# --------------------------------------------------------------------------- #


def control_enum_aliases(spec: dict) -> dict[str, str]:
    types = [f["type"] for obj in spec["objects"] for f in obj["fields"]]
    for msg in spec["messages"]:
        types += [f["type"] for f in msg["fields"] if f["type"] != "decision_message_list"]
    return {name: enum_alias(name) for name in enum_names_in(types)}


def emit_control_py(spec: dict) -> str:
    enums = spec["enums"]
    aliases = control_enum_aliases(spec)

    L = [py_header(CONTROL_SRC).rstrip("\n"), "from __future__ import annotations", ""]
    L += _PY_PREAMBLE
    L.append("")
    for name, alias in aliases.items():
        L.append(f"{alias} = Literal[{enum_lit(enums[name])}]")
    L += ["", "", "class StrictModel(BaseModel):", '    model_config = ConfigDict(strict=True, extra="forbid")']

    for obj in spec["objects"]:
        L += ["", ""] + py_object(obj, aliases)

    arm_names = []
    for arm in spec["resume_decisions"]:
        cls = f"{arm['type'].capitalize()}Decision"
        arm_names.append(cls)
        L += ["", "", f"class {cls}(StrictModel):", f'    type: Literal["{arm["type"]}"]']
        L += [py_field(f, aliases) for f in arm["fields"]]

    L += ["", "", "ResumeDecision = Annotated[", "    Union[" + ", ".join(arm_names) + "],", '    Field(discriminator="type"),', "]"]

    msg_names = []
    for msg in spec["messages"]:
        cls = pascal(msg["kind"])
        msg_names.append(cls)
        L += ["", "", f"class {cls}(StrictModel):", f'    kind: Literal["{msg["kind"]}"]']
        for f in msg["fields"]:
            if f["type"] == "decision_message_list":
                L.append(f"    {f['name']}: Annotated[list[ResumeDecision], Field(min_length=1)]")
            else:
                L.append(py_field(f, aliases))

    L += ["", "", "InboundMessage = Annotated[", "    Union[" + ", ".join(msg_names) + "],", '    Field(discriminator="kind"),', "]", ""]
    L.append("inbound_adapter: TypeAdapter[InboundMessage] = TypeAdapter(InboundMessage)")
    return "\n".join(L) + "\n"


# --------------------------------------------------------------------------- #
# agent/contract/streams.py
# --------------------------------------------------------------------------- #


def emit_streams_py(spec: dict) -> str:
    s = spec["streams"]
    L = [py_header(STREAMS_SRC).rstrip("\n"), "from __future__ import annotations", ""]
    L += [
        f'{s["requests"]["const"]} = "{s["requests"]["name"]}"',
        f'CONSUMER_GROUP = "{spec["consumer_group"]}"',
        f'REQUESTS_MAXLEN = {s["requests"]["maxlen"]}',
        f'RUN_EVENTS_MAXLEN = {s["run_events"]["maxlen"]}',
        f'RUN_CONTROL_MAXLEN = {s["run_control"]["maxlen"]}',
        f'LIVE_MAXLEN = {s["live"]["maxlen"]}',
        f'BLOCK_MS = {spec["block_ms"]}',
        "",
        "",
        "def run_events_stream(run_id: str) -> str:",
        f'    return f"{s["run_events"]["template"]}"',
        "",
        "",
        "def run_control_stream(run_id: str) -> str:",
        f'    return f"{s["run_control"]["template"]}"',
        "",
        "",
        "def live_stream(session_id: str) -> str:",
        f'    return f"{s["live"]["template"]}"',
        "",
        "",
        "def event_id(run_id: str, index: int) -> str:",
        '    return f"{run_id}:{index}"',
        "",
        "",
        "def lease_key(run_id: str) -> str:",
        f'    return f"{spec["lease_key_template"]}"',
    ]
    return "\n".join(L) + "\n"


# --------------------------------------------------------------------------- #
# TS events: shared payload consts + discriminated envelope union
# --------------------------------------------------------------------------- #


def _ts_payload_const(spec: dict, kind: str, fields: list[dict]) -> tuple[str, list[str]]:
    enums = spec["enums"]
    notes = spec.get("notes", {})
    const = f"{camel(kind)}Payload"
    if not fields:
        return const, [f"const {const} = z.object({{}}).strict()"]
    L = [f"const {const} = z", "  .object({"]
    for f in fields:
        note = notes.get(f"{kind}.{f['name']}")
        if note:
            L.append(f"    // {note}")
        L.append(f"    {ts_field(f, enums)},")
    L += ["  })", "  .strict()"]
    return const, L


def _ts_events_file(spec: dict, *, kinds: list[str], payloads: dict[str, list[dict]], export_const: str, envelope: list[str]) -> list[str]:
    enums = spec["enums"]
    L: list[str] = []
    for obj in spec["objects"]:
        L += ts_object(obj, enums, export=False)
        L.append("")
    consts: dict[str, str] = {}
    for kind in kinds:
        const, defn = _ts_payload_const(spec, kind, payloads[kind])
        consts[kind] = const
        L += defn
        L.append("")
    L.append("const envelope = z")
    L.append("  .object({")
    L += [f"    {line}" for line in envelope]
    L += ["  })", "  .strict()", ""]
    L.append(f'export const {export_const} = z.discriminatedUnion("kind", [')
    for kind in kinds:
        L.append(f'  envelope.extend({{ kind: z.literal("{kind}"), payload: {consts[kind]} }}),')
    L.append("])")
    return L


def emit_wire_events_ts(spec: dict) -> str:
    kinds = [e["kind"] for e in spec["raw_kinds"]]
    payloads = {e["kind"]: event_payload_fields(spec, e.get("payload") or []) for e in spec["raw_kinds"]}
    envelope = [
        "run_id: z.string().min(1),",
        "index: z.number().int().nonnegative(),",
        "timestamp: z.number().int(),",
    ]
    L = [ts_header(EVENTS_SRC).rstrip("\n"), "", 'import { z } from "zod"', ""]
    L += _ts_events_file(spec, kinds=kinds, payloads=payloads, export_const="wireEventSchema", envelope=envelope)
    L += [
        "",
        "export type WireEvent = z.infer<typeof wireEventSchema>",
        'export type WireEventKind = WireEvent["kind"]',
        "",
        "export function parseWireEvent(input: unknown): WireEvent {",
        "  return wireEventSchema.parse(input)",
        "}",
    ]
    return "\n".join(L) + "\n"


def _browser_payloads(spec: dict) -> dict[str, list[dict]]:
    by_kind = {e["kind"]: e.get("payload") or [] for e in spec["raw_kinds"]}
    by_kind.update({e["kind"]: e.get("payload") or [] for e in spec["synthetic_kinds"]})
    return {k: event_payload_fields(spec, by_kind[k]) for k in spec["browser_order"]}


def emit_session_events_ts(spec: dict) -> str:
    kinds = list(spec["browser_order"])
    payloads = _browser_payloads(spec)
    envelope = [
        "event_id: z.string().min(1),",
        "seq: z.number().int().nonnegative(),",
        "session_id: z.string().min(1),",
        "run_id: z.string().min(1),",
        "timestamp: z.string().min(1),",
    ]
    L = [ts_header(EVENTS_SRC).rstrip("\n"), "", 'import { z } from "zod"', ""]
    L += _ts_events_file(spec, kinds=kinds, payloads=payloads, export_const="sessionEventSchema", envelope=envelope)
    L += [
        "",
        "export type SessionEvent = z.infer<typeof sessionEventSchema>",
        'export type SessionEventKind = SessionEvent["kind"]',
        "",
        "export function parseSessionEvent(input: unknown): SessionEvent {",
        "  return sessionEventSchema.parse(input)",
        "}",
    ]
    return "\n".join(L) + "\n"


def emit_event_names_ts(spec: dict) -> str:
    L = [ts_header(EVENTS_SRC).rstrip("\n"), "", "export const SESSION_EVENT_NAMES = ["]
    for kind in spec["browser_order"]:
        L.append(f'  "{kind}",')
    L += ["] as const", "", "export type SessionEventName = (typeof SESSION_EVENT_NAMES)[number]"]
    return "\n".join(L) + "\n"


# --------------------------------------------------------------------------- #
# session + web /contract/control.ts  (byte-identical)
# --------------------------------------------------------------------------- #


def emit_control_ts(spec: dict) -> str:
    enums = spec["enums"]
    L = [ts_header(CONTROL_SRC).rstrip("\n"), "", 'import { z } from "zod"', ""]

    for obj in spec["objects"]:
        L += ts_object(obj, enums, export=True)
        L.append("")

    arm_consts = []
    for arm in spec["resume_decisions"]:
        const = f"{arm['type']}DecisionSchema"
        arm_consts.append(const)
        parts = [f'type: z.literal("{arm["type"]}")']
        parts += [ts_field(f, enums) for f in arm["fields"]]
        L.append(f"const {const} = z.object({{ {', '.join(parts)} }}).strict()")
    L.append('export const resumeDecisionSchema = z.discriminatedUnion("type", [')
    L += [f"  {c}," for c in arm_consts]
    L += [
        "])",
        "export type ResumeDecision = z.infer<typeof resumeDecisionSchema>",
        'export type ResumeDecisionType = ResumeDecision["type"]',
        "",
    ]

    for msg in spec["messages"]:
        const = f"{camel(msg['kind'])}Schema"
        L.append(f"export const {const} = z")
        L.append("  .object({")
        L.append(f'    kind: z.literal("{msg["kind"]}"),')
        for f in msg["fields"]:
            if f["type"] == "decision_message_list":
                L.append(f"    {f['name']}: z.array(resumeDecisionSchema).min(1),")
            else:
                L.append(f"    {ts_field(f, enums)},")
        L += ["  })", "  .strict()"]
        L.append(f"export type {pascal(msg['kind'])} = z.infer<typeof {const}>")
        L.append("")

    L.append('export const inboundMessageSchema = z.discriminatedUnion("kind", [')
    L += [f"  {camel(m['kind'])}Schema," for m in spec["messages"]]
    L += ["])", "export type InboundMessage = z.infer<typeof inboundMessageSchema>"]
    return "\n".join(L) + "\n"


# --------------------------------------------------------------------------- #
# session/contract/streams.ts
# --------------------------------------------------------------------------- #


def _ts_template(tmpl: str, params: list[str]) -> str:
    out = tmpl
    for p in params:
        out = out.replace("{" + p + "}", "${" + camel(p) + "}")
    return out


def emit_streams_ts(spec: dict) -> str:
    s = spec["streams"]
    L = [ts_header(STREAMS_SRC).rstrip("\n"), ""]
    L += [
        f'export const {s["requests"]["const"]} = "{s["requests"]["name"]}"',
        f'export const CONSUMER_GROUP = "{spec["consumer_group"]}"',
        f'export const REQUESTS_MAXLEN = {s["requests"]["maxlen"]}',
        f'export const RUN_EVENTS_MAXLEN = {s["run_events"]["maxlen"]}',
        f'export const RUN_CONTROL_MAXLEN = {s["run_control"]["maxlen"]}',
        f'export const LIVE_MAXLEN = {s["live"]["maxlen"]}',
        f'export const BLOCK_MS = {spec["block_ms"]}',
        "",
        "export function runEventsStream(runId: string): string {",
        f'  return `{_ts_template(s["run_events"]["template"], ["run_id"])}`',
        "}",
        "",
        "export function runControlStream(runId: string): string {",
        f'  return `{_ts_template(s["run_control"]["template"], ["run_id"])}`',
        "}",
        "",
        "export function liveStream(sessionId: string): string {",
        f'  return `{_ts_template(s["live"]["template"], ["session_id"])}`',
        "}",
        "",
        "export function eventId(runId: string, index: number): string {",
        "  return `${runId}:${index}`",
        "}",
        "",
        "export function leaseKey(runId: string): string {",
        f'  return `{_ts_template(spec["lease_key_template"], ["run_id"])}`',
        "}",
    ]
    return "\n".join(L) + "\n"


# --------------------------------------------------------------------------- #
# session + web /contract/http.ts  (byte-identical)
# --------------------------------------------------------------------------- #


def emit_http_ts(spec: dict) -> str:
    enums = spec["enums"]
    ep = spec["endpoints"]
    L = [ts_header(HTTP_SRC).rstrip("\n"), "", 'import { z } from "zod"']
    L.append('import { resumeDecisionSchema } from "./control"')
    L.append("")

    for obj in spec["objects"]:
        L += ts_object(obj, enums, export=True)
        L.append("")

    snap = ep["snapshot"]
    L.append(
        f"export function parseSessionSnapshot(input: unknown): {snap['response_object']} {{"
    )
    L.append(f"  return {snap['response_const']}.parse(input)")
    L.append("}")
    L.append("")

    start = ep["create_message"]
    L.append(f"export const {start['body_const']} = z")
    L.append("  .object({")
    L += [f"    {ts_field(f, enums)}," for f in start["body"]]
    L += ["  })", "  .strict()"]
    L.append(f"export type MessageCreateParams = z.infer<typeof {start['body_const']}>")
    L.append("")
    L.append(f"export const {start['receipt_const']} = z")
    L.append("  .object({")
    L += [f"    {ts_field(f, enums)}," for f in start["receipt"]]
    L += ["  })", "  .strict()"]
    L.append(f"export type MessageCreateReceipt = z.infer<typeof {start['receipt_const']}>")
    L.append("")

    ctrl = ep["run_control"]
    L.append(f'export const {ctrl["body_const"]} = z.discriminatedUnion("kind", [')
    L.append(
        '  z.object({ kind: z.literal("run.cancel"), decision_id: z.string().min(1) }).strict(),'
    )
    L.append(
        '  z.object({ kind: z.literal("run.resume"), decision_id: z.string().min(1), '
        "decisions: z.array(resumeDecisionSchema).min(1) }).strict(),"
    )
    L.append("])")
    L.append(f"export type RunControlBody = z.infer<typeof {ctrl['body_const']}>")
    L.append("")
    receipt = ", ".join(ts_field(f, enums) for f in ctrl["receipt"])
    L.append(f"export const {ctrl['receipt_const']} = z.object({{ {receipt} }}).strict()")
    L.append(f"export type RunControlReceipt = z.infer<typeof {ctrl['receipt_const']}>")
    L.append("")

    dele = ep["delete_session"]
    dele_receipt = ", ".join(ts_field(f, enums) for f in dele["receipt"])
    L.append(f"export const {dele['receipt_const']} = z.object({{ {dele_receipt} }}).strict()")
    L.append(f"export type DeleteSessionReceipt = z.infer<typeof {dele['receipt_const']}>")
    L.append("")

    err = ", ".join(ts_field(f, enums) for f in spec["error"])
    L.append(f"export const {spec['error_const']} = z.object({{ {err} }}).strict()")
    L.append(f"export type ErrorResponse = z.infer<typeof {spec['error_const']}>")
    L.append(f'export const SESSION_RUN_ACTIVE = "{spec["error_conflict_code"]}"')
    L.append(f'export const LAST_EVENT_ID_HEADER = "{spec["last_event_id_header"]}"')
    L.append("")

    for key in ("create_message", "snapshot", "stream", "file", "run_control"):
        e = ep[key]
        sig = ", ".join(f"{camel(p)}: string" for p in e["params"])
        body = _ts_template(e["path_template"], e["params"])
        L.append(f"export function {e['path_fn']}({sig}): string {{")
        L.append(f"  return `{body}`")
        L.append("}")
    return "\n".join(L) + "\n"


# --------------------------------------------------------------------------- #
# agent/contract/__init__.py
# --------------------------------------------------------------------------- #


def emit_init_py(events: dict, control: dict, streams: dict) -> str:
    events_names = [
        "AgentEvent",
        "agent_event_adapter",
        *events_enum_aliases(events).values(),
        *(o["name"] for o in events["objects"]),
        *(pascal(e["kind"]) for e in events["raw_kinds"]),
        *(f"{pascal(e['kind'])}Payload" for e in events["raw_kinds"]),
    ]
    control_names = [
        "InboundMessage",
        "inbound_adapter",
        "ResumeDecision",
        *control_enum_aliases(control).values(),
        *(o["name"] for o in control["objects"]),
        *(f"{a['type'].capitalize()}Decision" for a in control["resume_decisions"]),
        *(pascal(m["kind"]) for m in control["messages"]),
    ]
    s = streams["streams"]
    streams_names = [
        s["requests"]["const"],
        "CONSUMER_GROUP",
        "REQUESTS_MAXLEN",
        "RUN_EVENTS_MAXLEN",
        "RUN_CONTROL_MAXLEN",
        "LIVE_MAXLEN",
        "BLOCK_MS",
        "run_events_stream",
        "run_control_stream",
        "live_stream",
        "event_id",
        "lease_key",
    ]

    def block(module: str, names: list[str]) -> list[str]:
        out = [f"from kokoro_agent.contract.{module} import ("]
        out += [f"    {n}," for n in names]
        out.append(")")
        return out

    L = [py_header("contract/spec/*.yaml").rstrip("\n"), "from __future__ import annotations", ""]
    L += block("events", events_names)
    L += block("control", control_names)
    L += block("streams", streams_names)
    L.append("")
    L.append("__all__ = [")
    L += [f'    "{n}",' for n in (*events_names, *control_names, *streams_names)]
    L.append("]")
    return "\n".join(L) + "\n"


# --------------------------------------------------------------------------- #
# contract/README.md
# --------------------------------------------------------------------------- #


def emit_readme(events: dict, control: dict, streams: dict, http: dict) -> str:
    optional = set(events.get("payload_optional") or [])
    payload_by_kind = {e["kind"]: e.get("payload") or [] for e in events["raw_kinds"]}
    payload_by_kind.update({e["kind"]: e.get("payload") or [] for e in events["synthetic_kinds"]})

    L = [
        "<!-- GENERATED — DO NOT EDIT. Source: contract/spec/*.yaml -->",
        "<!-- Regenerate: python3 contract/generate.py -->",
        "",
        "# Kokoro wire contract",
        "",
        "One vocabulary (snake_case fields + dot-kind) travels agent -> session -> web.",
        "`spec/` is the only truth; `generate.py` renders every mirror and this doc;",
        "`check.py` gates drift. Never hand-edit a generated file.",
        "",
        "## Envelopes",
        "",
        "- agent -> session (raw): `{ kind, run_id, index, timestamp, payload }` — `index` per-run monotonic.",
        "- session -> web (browser): `{ kind, event_id, seq, session_id, run_id, timestamp, payload }`",
        "  — `event_id = f(run_id, index)`; `seq` per-session monotonic (store-assigned). run.started is",
        "  replaced by the synthetic session.created + run.created; the other 13 raw kinds pass through.",
        "",
        "## Raw events (agent -> session, 14)",
        "",
        "| kind | payload |",
        "| --- | --- |",
    ]
    for entry in events["raw_kinds"]:
        fields = entry.get("payload") or []
        rendered = ", ".join(f"{f}?" if f in optional else f for f in fields) or "(none)"
        L.append(f"| `{entry['kind']}` | {rendered} |")

    L += ["", "## Browser events (session -> web, 15)", "", "| kind | payload |", "| --- | --- |"]
    for kind in events["browser_order"]:
        fields = payload_by_kind[kind]
        rendered = ", ".join(f"{f}?" if f in optional else f for f in fields) or "(none)"
        L.append(f"| `{kind}` | {rendered} |")

    L += ["", "## Control plane (session -> agent)", "", "| message | fields |", "| --- | --- |"]
    for msg in control["messages"]:
        names = ", ".join(f["name"] for f in msg["fields"])
        L.append(f"| `{msg['kind']}` | {names} |")
    L += ["", "ResumeDecision (discriminated on `type`):", ""]
    for arm in control["resume_decisions"]:
        fields = ", ".join(f"{f['name']}?" if f.get("optional") else f["name"] for f in arm["fields"])
        L.append(f"- `{arm['type']}`: {fields}")

    L += ["", "## Streams", "", "| stream | owner | reader | maxlen |", "| --- | --- | --- | --- |"]
    for node in streams["streams"].values():
        name = node.get("name") or node.get("template")
        L.append(f"| `{name}` | {node['owner']} | {node['reader']} | {node['maxlen']} |")
    L += [
        "",
        f"Consumer group `{streams['consumer_group']}`; BLOCK {streams['block_ms']}ms; "
        f"`event_id = {streams['event_id_format']}`; lease `{streams['lease_key_template']}`.",
        "",
        "## HTTP (session)",
        "",
        "| method | path |",
        "| --- | --- |",
    ]
    for e in http["endpoints"].values():
        L.append(f"| {e['method']} | `{e['path_template']}` |")
    L += [
        "",
        "POST messages -> 202 `{ run_id, user_message_id, assistant_message_id }`; a non-matching",
        f"idempotency_key against an active run returns 409 `{http['error_conflict_code']}`.",
        "GET /sessions/:id returns the snapshot; SSE resumes from `Last-Event-ID` = last `seq`.",
    ]
    return "\n".join(L) + "\n"


# --------------------------------------------------------------------------- #
# driver
# --------------------------------------------------------------------------- #


def build() -> dict[Path, str]:
    events = load("events.yaml")
    control = load("control.yaml")
    streams = load("streams.yaml")
    http = load("http.yaml")

    session_events = emit_session_events_ts(events)
    control_ts = emit_control_ts(control)
    http_ts = emit_http_ts(http)

    return {
        HERE / "README.md": emit_readme(events, control, streams, http),
        AGENT / "__init__.py": emit_init_py(events, control, streams),
        AGENT / "events.py": emit_events_py(events),
        AGENT / "control.py": emit_control_py(control),
        AGENT / "streams.py": emit_streams_py(streams),
        SESSION / "wire-events.ts": emit_wire_events_ts(events),
        SESSION / "session-events.ts": session_events,
        SESSION / "control.ts": control_ts,
        SESSION / "streams.ts": emit_streams_ts(streams),
        SESSION / "http.ts": http_ts,
        WEB / "session-events.ts": session_events,
        WEB / "control.ts": control_ts,
        WEB / "http.ts": http_ts,
        WEB / "event-names.ts": emit_event_names_ts(events),
    }


def main(argv: list[str]) -> int:
    outputs = build()
    check = "--check" in argv
    drift = False
    for path, content in outputs.items():
        rel = path.relative_to(ROOT)
        if check:
            current = path.read_text() if path.exists() else ""
            if current != content:
                print(f"DRIFT: {rel}")
                drift = True
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
            print(f"wrote {rel}")
    if check and drift:
        print("\nRun `python3 contract/generate.py` and commit the regenerated mirrors.")
        return 1
    if check:
        print(f"OK — {len(outputs)} mirror(s) match contract/spec/")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
