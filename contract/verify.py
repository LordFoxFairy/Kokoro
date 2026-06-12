#!/usr/bin/env python3
"""Drift gate for the 13-kind event contract (blueprint step9, phase 1).

Replaces scripts/check-contract-kinds.sh (whose premise — byte-identical kind
sets across the 3 repos — was false). This gate is deterministic and model-free:
it derives, from contract/events.yaml, the EXPECTED kind-set and per-kind
payload-field-name-set for each of the 6 contract files (per view), then parses
each file structurally and asserts equality. Any missing / extra / drifted kind
or field => non-zero exit + a precise report (file, kind, field).

CI: run `python3 contract/verify.py`. Exit 0 = all 6 mirrors match events.yaml.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
YAML_PATH = Path(__file__).resolve().parent / "events.yaml"

AGENT_EVENTS_PY = ROOT / "kokoro-agent/src/kokoro_agent/domain/agent_event.py"
SESSION_AGENT_EVENT_TS = ROOT / "kokoro-session/src/domain/agent-event.ts"
SESSION_EVENT_TS = ROOT / "kokoro-session/src/domain/session-event.ts"
WEB_SCHEMA_TS = ROOT / "kokoro-web/src/infrastructure/transport-event-schema.ts"
WEB_RENDER_TS = ROOT / "kokoro-web/src/domain/session-stream-event.ts"

# Envelope fields shared by every render arm — not part of the payload contract.
RENDER_ENVELOPE_FIELDS = frozenset(
    {"kind", "eventId", "seq", "sessionId", "conversationId", "runId"}
)
# Envelope fields shared by every agui wire arm (top-level, not in `payload`).
AGUI_ENVELOPE_FIELDS = frozenset(
    {"event", "event_id", "session_id", "conversation_id", "run_id", "timestamp"}
)


@dataclass
class Problem:
    file: str
    detail: str


@dataclass
class Report:
    problems: list[Problem] = field(default_factory=list)

    def fail(self, file: str, detail: str) -> None:
        self.problems.append(Problem(file, detail))

    def compare(
        self,
        file: str,
        view: str,
        expected: dict[str, set[str]],
        actual: dict[str, set[str]],
        *,
        allow_extra: dict[str, set[str]] | None = None,
    ) -> None:
        exp_kinds = set(expected)
        act_kinds = set(actual)
        for missing in sorted(exp_kinds - act_kinds):
            self.fail(file, f"[{view}] missing kind/event '{missing}'")
        for extra in sorted(act_kinds - exp_kinds):
            self.fail(file, f"[{view}] unexpected kind/event '{extra}'")
        for k in sorted(exp_kinds & act_kinds):
            want = expected[k]
            got = actual[k]
            tolerated = (allow_extra or {}).get(k, set())
            for missing in sorted(want - got):
                self.fail(file, f"[{view}] kind '{k}' missing payload field '{missing}'")
            for extra in sorted(got - want - tolerated):
                self.fail(file, f"[{view}] kind '{k}' unexpected payload field '{extra}'")


# --------------------------------------------------------------------------- #
# Derive expected per-view shapes from events.yaml
# --------------------------------------------------------------------------- #


def load_spec() -> dict:
    return yaml.safe_load(YAML_PATH.read_text())


def expected_agent_out(spec: dict) -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for entry in spec["kinds"].values():
        ao = entry.get("agent_out")
        if not ao or "kind" not in ao:
            continue
        out[ao["kind"]] = set(ao.get("payload") or [])
    return out


def _agui_event_payload(entry: dict) -> dict[str, set[str]]:
    """Return {event_name: payload_field_set} contributed by one yaml entry's agui view."""
    ag = entry.get("agui_out")
    if not ag:
        return {}
    if "event" in ag:
        return {ag["event"]: set(ag.get("payload") or [])}
    return {}


def expected_agui_out(spec: dict, *, with_web_extra: bool) -> dict[str, set[str]]:
    """agui-out event set. with_web_extra adds web-tolerated optional fields."""
    out: dict[str, set[str]] = {}

    def add(event: str, payload: list[str] | None, extra: list[str] | None) -> None:
        fields = set(payload or [])
        if with_web_extra and extra:
            fields |= set(extra)
        out[event] = fields

    for entry in spec["kinds"].values():
        ag = entry.get("agui_out")
        if not ag:
            continue
        if "event" in ag:
            add(ag["event"], ag.get("payload"), ag.get("agui_out_web_extra"))
        elif "emits" in ag:
            # run.started fans out; its target events are declared in agui_only.
            continue
    for event, node in spec["agui_only"].items():
        ag = node["agui_out"]
        add(event, ag.get("payload"), ag.get("agui_out_web_extra"))
    return out


def expected_render(spec: dict) -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for entry in spec["kinds"].values():
        r = entry.get("render")
        if not r or r.get("absent"):
            continue
        out[r["kind"]] = set(r.get("payload") or [])
    for node in spec["agui_only"].values():
        r = node["render"]
        if r.get("absent"):
            continue
        out[r["kind"]] = set(r.get("payload") or [])
    return out


# --------------------------------------------------------------------------- #
# Parse the 6 actual contract files
# --------------------------------------------------------------------------- #


def parse_events_py(text: str) -> tuple[set[str], dict[str, set[str]]]:
    """AgentKind Literal -> kind set; docstring table -> per-kind payload fields."""
    literal = re.search(r"AgentKind\s*=\s*Literal\[(.*?)\]", text, re.DOTALL)
    kinds: set[str] = set()
    if literal:
        kinds = set(re.findall(r'"([^"]+)"', literal.group(1)))

    # Docstring table: lines like `#   kind.name   {"field": ...}` or `{}`.
    payloads: dict[str, set[str]] = {}
    for kind in kinds:
        # Match the documented shape for this exact kind on its own table line.
        m = re.search(
            r"#\s+" + re.escape(kind) + r"\s+(\{.*?\})\s*(?:#.*)?$",
            text,
            re.MULTILINE,
        )
        shape = m.group(1) if m else "{}"
        payloads[kind] = _fields_from_doc_shape(shape)
    return kinds, payloads


def _fields_from_doc_shape(shape: str) -> set[str]:
    """Top-level keys of a documented dict shape `{"a": ..., "b": ...}`.

    Only the first nesting level counts (nested {} / [] are payload values, not
    payload field names). todo.updated documents {"todos": [...]} -> {todos}.
    """
    depth = 0
    out: set[str] = set()
    for m in re.finditer(r'"([^"]+)"\s*:', shape):
        prefix = shape[: m.start()]
        depth = prefix.count("{") - prefix.count("}") + prefix.count("[") - prefix.count("]")
        if depth == 1:
            out.add(m.group(1))
    return out


def parse_zod_discriminated(text: str, discriminant: str) -> dict[str, set[str]]:
    """Parse a Zod discriminated union: each `z.literal("X")` arm -> payload keys.

    Strategy: split the file into named payload schema consts, then for each arm
    resolve `payload: <name>` or an inline `payload: z.object({...})` to its keys.
    """
    consts = _zod_object_consts(text)
    arms: dict[str, set[str]] = {}
    arm_re = re.compile(
        r"z\.literal\(\"([^\"]+)\"\)(.*?)payload:\s*(.*?)\}\)\.strict\(\)",
        re.DOTALL,
    )
    for m in re.finditer(arm_re, text):
        if discriminant not in m.group(0)[: m.start(2) - m.start() + 20]:
            pass
        name = m.group(1)
        payload_expr = m.group(3).strip()
        arms[name] = _resolve_payload_fields(payload_expr, consts, text, name)
    return arms


def _zod_object_consts(text: str) -> dict[str, str]:
    """name -> raw body of `const name = z.object({ ... }).strict()` payload consts."""
    consts: dict[str, str] = {}
    for m in re.finditer(
        r"const\s+(\w+)\s*=\s*z\s*\.?\s*object\(\{(.*?)\}\)\s*\.strict\(\)",
        text,
        re.DOTALL,
    ):
        consts[m.group(1)] = m.group(2)
    return consts


def _resolve_payload_fields(
    expr: str, consts: dict[str, str], text: str, kind: str
) -> set[str]:
    # Inline z.object({...}) right at the payload position.
    inline = re.match(r"z\s*\.?\s*object\(\{(.*)$", expr, re.DOTALL)
    if inline:
        # Grab the inline arm body straight from the source around this kind.
        body = _inline_object_body(text, kind)
        if body is not None:
            return _top_level_keys(body)
    # Named const reference.
    name = expr.strip().rstrip(",")
    if name in consts:
        return _top_level_keys(consts[name])
    return set()


def _inline_object_body(text: str, kind: str) -> str | None:
    """For arms whose payload is an inline z.object, slice its brace-balanced body.

    Tolerates `z.object({` and the line-wrapped `z\n.object({` form web uses.
    """
    idx = text.find(f'literal("{kind}")')
    if idx == -1:
        return None
    pidx = text.find("payload:", idx)
    if pidx == -1:
        return None
    om = re.compile(r"z\s*\.\s*object\(\{").search(text, pidx)
    if om is None:
        return None
    start = om.end() - 1  # position of the opening `{`
    depth = 0
    for i in range(start, len(text)):
        c = text[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return text[start + 1 : i]
    return None


def _top_level_keys(body: str) -> set[str]:
    """Top-level `key:` identifiers inside a Zod object body (skip nested objects)."""
    out: set[str] = set()
    depth = 0
    i = 0
    n = len(body)
    while i < n:
        c = body[i]
        if c in "([{":
            depth += 1
            i += 1
            continue
        if c in ")]}":
            depth -= 1
            i += 1
            continue
        if depth == 0:
            m = re.match(r"\s*(\w+)\s*:", body[i:])
            if m:
                out.add(m.group(1))
                i += m.end()
                continue
        i += 1
    return out


def parse_web_envelope_enum(text: str) -> set[str]:
    m = re.search(r"event:\s*z\.enum\(\[(.*?)\]\)", text, re.DOTALL)
    if not m:
        return set()
    return set(re.findall(r'"([^"]+)"', m.group(1)))


def parse_web_schema_arms(text: str) -> dict[str, set[str]]:
    """Each `eventEnvelopeSchema.extend({ event: z.literal("X"), payload: z.object({...}) })`."""
    arms: dict[str, set[str]] = {}
    for m in re.finditer(
        r'event:\s*z\.literal\("([^"]+)"\)', text
    ):
        kind = m.group(1)
        body = _inline_object_body(text, kind)
        arms[kind] = _top_level_keys(body) if body is not None else set()
    return arms


def parse_render_union(text: str) -> dict[str, set[str]]:
    """SessionStreamEvent TS union: each `kind: "x"` arm -> non-envelope props."""
    arms: dict[str, set[str]] = {}
    # Each arm is `{ kind: "name" ...props... }` separated by `|`.
    for m in re.finditer(r'kind:\s*"([^"]+)"', text):
        kind = m.group(1)
        start = m.start()
        # Slice this arm body to the next top-level `| {` or end of union.
        rest = text[m.end():]
        # Stop at the next `kind:` arm.
        nxt = re.search(r'kind:\s*"', rest)
        body = rest[: nxt.start()] if nxt else rest
        props: set[str] = set()
        for pm in re.finditer(r"^\s*(\w+)\??\s*:", body, re.MULTILINE):
            props.add(pm.group(1))
        arms[kind] = props - RENDER_ENVELOPE_FIELDS
    return arms


# --------------------------------------------------------------------------- #
# Transport constants (CURSOR_WIDTH / REDIS_FIELD / BLOCK_MS) — a shared Py/TS
# contract declared once in events.yaml, hand-mirrored in BOTH stream ports.
# verify.py reads each side's literal and asserts it equals the yaml value.
# --------------------------------------------------------------------------- #

TRANSPORT_FILES = {
    "kokoro-session/.../stream-port.ts": (
        ROOT / "kokoro-session/src/infrastructure/stream-port.ts",
        {
            "CURSOR_WIDTH": (r"\bCURSOR_WIDTH\s*=\s*(\d+)", int),
            "REDIS_FIELD": (r'\bREDIS_FIELD\s*=\s*"([^"]+)"', str),
            "BLOCK_MS": (r"\bDEFAULT_BLOCK_MS\s*=\s*(\d+)", int),
        },
    ),
    "kokoro-agent/.../stream_port.py": (
        ROOT / "kokoro-agent/src/kokoro_agent/infrastructure/stream_port.py",
        {
            "CURSOR_WIDTH": (r"\b_CURSOR_WIDTH\s*=\s*(\d+)", int),
            "REDIS_FIELD": (r'\b_REDIS_FIELD\s*=\s*"([^"]+)"', str),
            "BLOCK_MS": (r"\b_BLOCK_MS\s*=\s*(\d+)", int),
        },
    ),
}


def check_transport(spec: dict, rep: Report) -> None:
    expected = spec["transport"]
    for label, (path, patterns) in TRANSPORT_FILES.items():
        text = path.read_text()
        for key, (pattern, cast) in patterns.items():
            m = re.search(pattern, text)
            if m is None:
                rep.fail(label, f"[transport] {key} literal not found")
                continue
            got = cast(m.group(1))
            want = expected[key]
            if got != want:
                rep.fail(label, f"[transport] {key}={got!r} != yaml {want!r}")


# --------------------------------------------------------------------------- #
# Envelope fields (shared, non-payload) — declared once in events.yaml, mirrored in
# session envelopeFields (no `event`) and web eventEnvelopeSchema (with `event`).
# --------------------------------------------------------------------------- #


def _braced_object_keys(text: str, header_re: str) -> set[str]:
    """Top-level keys of the brace-balanced object opened by the first header match."""
    m = re.search(header_re, text)
    if m is None:
        return set()
    start = text.index("{", m.start())
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return _top_level_keys(text[start + 1 : i])
    return set()


def check_envelope(spec: dict, rep: Report) -> None:
    env = spec.get("envelope")
    if not env:
        return
    agui = set(env["agui_out"])
    # session envelopeFields: plain object, no `event` (it lives in each arm's literal).
    sess = _braced_object_keys(
        SESSION_EVENT_TS.read_text(), r"const\s+envelopeFields\s*=\s*\{"
    )
    if sess != agui:
        rep.fail(
            "kokoro-session/.../session-event.ts",
            f"[envelope] envelopeFields {sorted(sess)} != yaml agui_out {sorted(agui)}",
        )
    # web eventEnvelopeSchema: z.object including the `event` discriminant.
    web = _braced_object_keys(
        WEB_SCHEMA_TS.read_text(),
        r"const\s+eventEnvelopeSchema\s*=\s*z\s*\.?\s*object\(",
    )
    want_web = agui | {"event"}
    if web != want_web:
        rep.fail(
            "kokoro-web/.../session-event-schema.ts",
            f"[envelope] eventEnvelopeSchema {sorted(web)} != yaml agui_out+event {sorted(want_web)}",
        )


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #


def main() -> int:
    spec = load_spec()
    rep = Report()

    exp_agent = expected_agent_out(spec)
    exp_agui = expected_agui_out(spec, with_web_extra=False)
    exp_agui_web = expected_agui_out(spec, with_web_extra=True)
    exp_render = expected_render(spec)

    # 1. kokoro-agent events.py (agent-out, Python)
    py_text = AGENT_EVENTS_PY.read_text()
    py_kinds, py_payloads = parse_events_py(py_text)
    rep.compare(
        "kokoro-agent/.../events.py",
        "agent-out",
        exp_agent,
        py_payloads,
    )
    if py_kinds != set(exp_agent):
        rep.fail(
            "kokoro-agent/.../events.py",
            f"[agent-out] AgentKind Literal != yaml: "
            f"missing={sorted(set(exp_agent)-py_kinds)} extra={sorted(py_kinds-set(exp_agent))}",
        )

    # 2. kokoro-session agent-event.ts (agent-out re-validation, Zod)
    rep.compare(
        "kokoro-session/.../agent-event.ts",
        "agent-out",
        exp_agent,
        parse_zod_discriminated(SESSION_AGENT_EVENT_TS.read_text(), "kind"),
    )

    # 3. kokoro-session session-event.ts (agui-out, Zod)
    rep.compare(
        "kokoro-session/.../session-event.ts",
        "agui-out",
        exp_agui,
        parse_zod_discriminated(SESSION_EVENT_TS.read_text(), "event"),
    )

    # 4. kokoro-web session-event-schema.ts (agui-out wire-in, Zod, + web extras)
    web_schema_text = WEB_SCHEMA_TS.read_text()
    rep.compare(
        "kokoro-web/.../session-event-schema.ts",
        "agui-out(web)",
        exp_agui_web,
        parse_web_schema_arms(web_schema_text),
    )
    enum_kinds = parse_web_envelope_enum(web_schema_text)
    if enum_kinds != set(exp_agui_web):
        rep.fail(
            "kokoro-web/.../session-event-schema.ts",
            f"[agui-out(web)] envelope enum != yaml: "
            f"missing={sorted(set(exp_agui_web)-enum_kinds)} "
            f"extra={sorted(enum_kinds-set(exp_agui_web))}",
        )

    # 5. kokoro-web session-stream-event.ts (render, TS union, camelCase)
    rep.compare(
        "kokoro-web/.../session-stream-event.ts",
        "render",
        exp_render,
        parse_render_union(WEB_RENDER_TS.read_text()),
    )

    # 6. transport constants in BOTH stream ports (CURSOR_WIDTH / REDIS_FIELD / BLOCK_MS)
    check_transport(spec, rep)

    # 7. shared envelope fields in session + web (CONTRACT for seq/event_id/cursor/...)
    check_envelope(spec, rep)

    if rep.problems:
        print("DRIFT DETECTED — events.yaml and repo contract files disagree:\n")
        for p in rep.problems:
            print(f"  ✗ {p.file}: {p.detail}")
        print(f"\n{len(rep.problems)} problem(s). Fix the file or update events.yaml.")
        return 1

    n_kinds = len(spec["kinds"])
    print("PASS — all 6 contract mirrors match contract/events.yaml")
    print(
        f"  agent-out : {len(exp_agent)} kinds  "
        f"(events.py + agent-event.ts)"
    )
    print(
        f"  agui-out  : {len(exp_agui)} events "
        f"(session-event.ts; web wire-in tolerates {len(exp_agui_web)} w/ optionals)"
    )
    print(f"  render    : {len(exp_render)} kinds  (session-stream-event.ts)")
    print(f"  transport : {len(spec['transport'])} consts (stream-port.ts + stream_port.py)")
    print(f"  envelope  : {len(spec['envelope']['agui_out'])} agui fields (session + web)")
    print(f"  base kinds: {n_kinds}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
