#!/usr/bin/env python3
"""Agent-canonical wire codegen (option A: agent's envelope.py is the single source).

kokoro-agent/src/kokoro_agent/interfaces/envelope.py 的 TypedDict 即真理源。本模块
机读其 JSON Schema（Pydantic TypeAdapter）反向生成 kokoro-session 入站校验用的 Zod
（agent-event.ts）。事件↔data 形状的对应取自 agent 的构造器语义（下表），字段形状全部
来自 agent 模型自身，零手抄。
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "kokoro-agent" / "src"))

from pydantic import TypeAdapter  # noqa: E402

from kokoro_agent.interfaces import envelope as E  # noqa: E402

SESSION_AGENT_EVENT_TS = ROOT / "kokoro-session" / "src" / "domain" / "agent-event.ts"

GENERATED_HEADER_TS = (
    "// DO NOT EDIT — generated from kokoro-agent envelope.py by contract/agent_wire.py.\n"
    "// agent 是 wire 单源真理；改 envelope.py 后跑 `python3 contract/generate.py`。\n"
)

# 事件 → data TypedDict（取自 agent transformer 构造器语义；字段形状全来自模型自身）。
EVENT_DATA: dict[str, Any] = {
    "text_chunk": E.ChunkData,
    "reasoning_chunk": E.ChunkData,
    "tool_call_start": E.ToolStartData,
    "tool_call_awaiting": E.ToolStartData,
    "tool_call_end": E.ToolEndData,
    "agent_done": E.DoneData,
    "agent_error": E.ErrorData,
}
# agent_status 的 data 是按 data.status 判别的子联合。
AGENT_STATUS_VARIANTS = [
    E.StartedStatus,
    E.TodoUpdatedStatus,
    E.SubagentStartedStatus,
    E.SubagentFinishedStatus,
    E.CustomStatus,
]


def _resolve(schema: dict[str, Any], defs: dict[str, Any]) -> dict[str, Any]:
    ref = schema.get("$ref")
    if ref:
        return defs[ref.split("/")[-1]]
    return schema


def _zod_scalar(schema: dict[str, Any], defs: dict[str, Any]) -> str:
    s = _resolve(schema, defs)
    if "const" in s:
        return f'z.literal("{s["const"]}")'
    if "enum" in s:
        vals = ", ".join(f'"{v}"' for v in s["enum"])
        return f"z.enum([{vals}])"
    t = s.get("type")
    if t == "string":
        return "z.string()"
    if t == "boolean":
        return "z.boolean()"
    if t in ("number", "integer"):
        return "z.number()"
    if t == "array":
        return f"z.array({_zod_scalar(s['items'], defs)})"
    if t == "object":
        # additionalProperties=True 或指向 JsonValue → record；否则是带 properties 的具名对象。
        if "properties" in s:
            return _zod_object(s, defs)
        return "z.record(z.unknown())"
    # 无 type（JsonValue 空 schema / custom）→ 任意 JSON。
    return "z.unknown()"


def _zod_object(schema: dict[str, Any], defs: dict[str, Any]) -> str:
    required = set(schema.get("required") or [])
    parts: list[str] = []
    for name, prop in schema.get("properties", {}).items():
        opt = "" if name in required else ".optional()"
        parts.append(f"{name}: {_zod_scalar(prop, defs)}{opt}")
    return "z.object({ " + ", ".join(parts) + " }).strict()"


def _data_zod(td: Any) -> str:
    schema = TypeAdapter(td).json_schema()
    return _zod_object(schema, schema.get("$defs", {}))


def emit_agent_event_ts() -> str:
    L: list[str] = [GENERATED_HEADER_TS.rstrip("\n"), "", 'import { z } from "zod"', ""]

    # agent_status 子联合（按 data.status 判别）。
    L.append("const agentStatusData = z.discriminatedUnion(\"status\", [")
    for td in AGENT_STATUS_VARIANTS:
        L.append(f"  {_data_zod(td)},")
    L.append("])")
    L.append("")

    # 信封：{ event, request_id, timestamp(number ms), data }，按 event 判别。
    L.append("const envelope = { request_id: z.string(), timestamp: z.number() }")
    L.append("")
    L.append('export const agentEventSchema = z.discriminatedUnion("event", [')
    L.append(
        '  z.object({ event: z.literal("agent_status"), ...envelope, '
        "data: agentStatusData }).strict(),"
    )
    for event, td in EVENT_DATA.items():
        L.append(
            f'  z.object({{ event: z.literal("{event}"), ...envelope, '
            f"data: {_data_zod(td)} }}).strict(),"
        )
    L.append("])")
    L.append("")
    L.append("export type AgentEvent = z.infer<typeof agentEventSchema>")
    return "\n".join(L) + "\n"


def write() -> None:
    SESSION_AGENT_EVENT_TS.write_text(emit_agent_event_ts())


if __name__ == "__main__":
    if "--write" in sys.argv:
        write()
        print(f"wrote {SESSION_AGENT_EVENT_TS}")
    else:
        print(emit_agent_event_ts())
