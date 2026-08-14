#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

SCALARS = {"double","float","int32","int64","uint32","uint64","sint32","sint64","fixed32","fixed64","sfixed32","sfixed64","bool","string","bytes"}
LABELS = {"required","optional","repeated"}
GOOGLE_TYPES = {".google.protobuf.Timestamp"}
GOOGLE_IMPORTS = {"google/protobuf/timestamp.proto"}
EXPECTED_AGENT_KINDS = [
    "run.started","thinking.delta","message.delta","message.completed","tool.invoked","tool.output.delta",
    "tool.awaiting_approval","tool.returned","todo.updated","subagent.started","subagent.finished",
    "subagent.thinking.delta","subagent.text.delta","subagent.text.completed","subagent.tool.invoked",
    "subagent.tool.returned","delivery.created","run.control.receipt","run.completed","run.failed",
]
EXPECTED_NORMALIZED_MANIFEST_SHA256 = "fd8258bf38fc1f7f1246a99b6e55db2d10261f1b0d388279e6860a6d83479791"
EXPECTED_ACCESS_JWT = {
    "header": {"alg": "RS256", "typ": "JWT", "kid": "nonempty active JWKS key id"},
    "claims": {
        "iss": "kokoro-iam", "aud": "kokoro-user-backend", "sub": "canonical principal UUID",
        "site_id": "canonical Site UUID", "organization_id": "canonical Organization UUID",
        "auth_session_id": "canonical IAM auth-session UUID", "iat": "NumericDate", "exp": "NumericDate",
    },
    "nbf": "absent", "maxTtlSeconds": 900, "clockSkewSeconds": 30,
    "validation": "Chat and IAM reject any non-RS256 alg, missing/unknown kid, invalid signature, wrong typ/iss/aud, expired or future-issued token, overlong TTL or malformed UUID claim. IAM additionally proves the auth session is active and bound to the same principal/Site/Organization; Chat derives ActorContext only from a successful IAM Authorize response, never from unverified claims.",
}
EXPECTED_STREAM_AUTHORIZATION_EXPIRY = "Chat closes StreamConversationEvents no later than access JWT exp + 30-second clock skew and emits zero frames after that deadline. Web refreshes the sealed IAM session and reconnects from the last committed seq; membership revocation exposure is therefore bounded by the 900-second JWT TTL plus skew."
EXPECTED_BROWSER_JSON_MAPPING = {
    "uint64": "JSON safe nonnegative integer, reject values above 9007199254740991 before browser response",
    "enum": "lower_snake string with the type prefix removed",
    "bytesPayloadJson": "BFF decodes canonical UTF-8 JSON bytes, validates the declared strict payload schema and returns JSON object/value; never base64 in browser DTO",
    "timestamp": "RFC3339 UTC string", "uuid": "canonical lowercase UUID string",
    "optional": "property omitted when absent, never invented default",
}
EXPECTED_SNAPSHOT_MATERIALIZATION = {
    "session.created": "chat_conversation owner fact; no MessagePart",
    "run.created": "chat_run_launch plus synthesized/projected RunView; no MessagePart",
    "message.user": "user Message plus TEXT MessagePart with the exact browser payload",
    "message.delta": "append assistant TEXT MessagePart payload in producer-seq order",
    "message.completed": "update assistant Message/part terminal status",
    "thinking.delta": "append THINKING MessagePart payload in producer-seq order",
    "tool.invoked": "upsert TOOL_CALL MessagePart by tool_call_id",
    "tool.output.delta": "append TOOL_RESULT MessagePart payload by tool_call_id",
    "tool.awaiting_approval": "persist complete chat_interaction payload and mark the matching TOOL_CALL pending",
    "tool.returned": "finalize TOOL_RESULT MessagePart and matching TOOL_CALL status",
    "delivery.created": "append DELIVERY MessagePart containing the exact browser payload",
    "todo.updated": "replace the run-scoped TODO MessagePart with the exact ordered browser payload",
    "subagent.started": "upsert SUBAGENT MessagePart by subagent_id",
    "subagent.finished": "finalize SUBAGENT MessagePart by subagent_id",
    "subagent.thinking.delta": "append thinking content to SUBAGENT MessagePart by subagent_id",
    "subagent.text.delta": "append text content to SUBAGENT MessagePart by subagent_id",
    "subagent.text.completed": "finalize subagent text in SUBAGENT MessagePart by subagent_id",
    "subagent.tool.invoked": "upsert nested tool fact in SUBAGENT MessagePart by subagent_id/tool_call_id",
    "subagent.tool.returned": "finalize nested tool fact in SUBAGENT MessagePart by subagent_id/tool_call_id",
    "run.completed": "finalize chat_run_view and assistant Message; no new MessagePart",
    "run.failed": "finalize chat_run_view and assistant Message with failure; no new MessagePart",
    "retentionRule": "A stream row is deletable only after its mapped owner facts commit and snapshot watermark is at least that seq. Unknown or not-yet-materialized kinds are retained, never silently dropped.",
}
EXPECTED_ERROR_STATUS_BY_CODE = {
    "invalid_argument": 400, "unauthenticated": 401, "permission_denied": 403, "not_found": 404,
    "command_digest_mismatch": 409, "conflict": 409, "precondition_failed": 409,
    "stale_generation": 409, "snapshot_required": 409, "dependency_unavailable": 503,
    "rate_limited": 429, "internal": 500, "magic_link_invalid": 400,
    "magic_link_expired": 410, "magic_link_consumed": 409, "auth_session_replayed": 401,
    "auth_session_revoked": 401, "conversation_run_active": 409,
    "conversation_scope_mismatch": 403, "interaction_not_pending": 409,
    "agent_admission_rejected": 409,
}
EXPECTED_OPERATION_ERROR_STATUSES = {
    "requestMagicLink": [400, 403, 429, 503, 500], "consumeMagicLink": [], "logout": [403],
    "getSessionState": [500], "createConversation": [400, 401, 403, 409, 503, 500],
    "listConversations": [400, 401, 403, 503, 500],
    "readConversationSnapshot": [400, 401, 403, 404, 503, 500],
    "submitMessage": [400, 401, 403, 404, 409, 503, 500],
    "decideInteraction": [400, 401, 403, 404, 409, 503, 500],
    "streamConversationEvents": [400, 401, 403, 404, 409, 503, 500],
}

class ManifestError(ValueError):
    pass

def require(condition: bool, message: str) -> None:
    if not condition:
        raise ManifestError(message)

def load_manifest(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestError(f"manifest unreadable: {exc}") from exc
    require(isinstance(data, dict), "manifest root must be object")
    return data

def duplicates(values: list[Any]) -> list[Any]:
    return sorted(value for value, count in Counter(values).items() if count > 1)

def validate(manifest: dict[str, Any]) -> None:
    require(manifest.get("artifact") == "slice-a-contract-manifest", "unexpected artifact")
    require(manifest.get("version") == 1, "unexpected manifest version")
    require(manifest.get("status") == "reviewed-frozen", "manifest status must be reviewed-frozen")
    require(manifest.get("authority") == "machine", "authority must be machine")
    proto = manifest.get("protobuf")
    require(isinstance(proto, dict), "protobuf must be object")
    files = proto.get("files", []); enums = proto.get("enums", []); messages = proto.get("messages", []); services = proto.get("services", [])
    require(len(files) == 9, "expected 9 proto files")
    require(len(services) == 8, "expected 8 services")
    require(sum(len(service.get("methods", [])) for service in services) == 19, "expected 19 methods")

    declarations: dict[tuple[str,str,str], dict[str,Any]] = {}
    package_symbols: dict[str,list[str]] = defaultdict(list)
    known_types = set(GOOGLE_TYPES)
    for kind, group in (("enum",enums),("message",messages),("service",services)):
        for item in group:
            key=(kind,item["package"],item["name"])
            require(key not in declarations, f"duplicate declaration {key}")
            declarations[key]=item
            package_symbols[item["package"]].append(item["name"])
            if kind in {"enum","message"}: known_types.add(f'.{item["package"]}.{item["name"]}')

    for enum in enums:
        values=enum.get("values",[])
        require(values and values[0].get("number") == 0, f"enum {enum['name']} must start at zero")
        names=[value.get("name") for value in values]; numbers=[value.get("number") for value in values]
        prefix=re.sub(r"(?<!^)(?=[A-Z])","_",enum["name"]).upper()+"_"
        require(all(isinstance(name,str) and name.startswith(prefix) for name in names), f"enum value prefix drift in {enum['name']}")
        require(not duplicates(names), f"duplicate enum value name in {enum['name']}")
        require(not duplicates(numbers), f"duplicate enum value number in {enum['name']}")
        package_symbols[enum["package"]].extend(names)
    for package,symbols in package_symbols.items():
        require(not duplicates(symbols), f"duplicate package symbol in {package}: {duplicates(symbols)}")

    for message in messages:
        fields=message.get("fields",[])
        require(not duplicates([field.get("number") for field in fields]), f"duplicate field number in {message['name']}")
        require(not duplicates([field.get("name") for field in fields]), f"duplicate field name in {message['name']}")
        for field in fields:
            expected_keys={"number","name","type","label"} | ({"oneof"} if "oneof" in field else set())
            require(set(field)==expected_keys, f"incomplete field or unknown key in {message['name']}")
            require(field["label"] in LABELS, f"invalid field label in {message['name']}.{field['name']}")
            require(field["type"] in SCALARS or field["type"] in known_types, f"unknown protobuf type {field['type']}")
            if "oneof" in field:
                require(field["label"] == "required", f"oneof field must be required: {message['name']}.{field['name']}")

    file_paths=[file.get("path") for file in files]
    require(not duplicates(file_paths), "duplicate proto file path")
    file_by_path={file["path"]:file for file in files}
    declaration_file: dict[str,str] = {}
    assigned=[]
    for file in files:
        imports=file.get("imports",[])
        require(not duplicates(imports), f"duplicate import in {file.get('path')}")
        for imported in imports:
            require(imported in file_paths or imported in GOOGLE_IMPORTS, f"unknown import {imported}")
        for declaration in file.get("declarations",[]):
            key=(declaration.get("kind"),file.get("package"),declaration.get("name"))
            require(key in declarations, f"unknown assigned declaration {key}")
            assigned.append(key)
            declaration_file[f".{file['package']}.{declaration['name']}"]=file["path"]
    require(not duplicates(assigned), f"declaration assigned twice: {duplicates(assigned)}")
    require(set(assigned)==set(declarations), f"unassigned declaration: {sorted(set(declarations)-set(assigned))}")

    for file in files:
        required_imports: set[str] = set()
        for declaration in file["declarations"]:
            item=declarations[(declaration["kind"],file["package"],declaration["name"])]
            references=[]
            if declaration["kind"]=="message":
                references=[field["type"] for field in item.get("fields",[]) if field["type"] not in SCALARS]
            elif declaration["kind"]=="service":
                references=[ref for method in item.get("methods",[]) for ref in (method["input"],method["output"])]
            for reference in references:
                if reference in GOOGLE_TYPES:
                    required_imports.add("google/protobuf/timestamp.proto")
                else:
                    target=declaration_file[reference]
                    if target != file["path"]:
                        required_imports.add(target)
        require(set(file.get("imports",[]))==required_imports, f"direct imports drift for {file['path']}")

    for service in services:
        for method in service.get("methods",[]):
            require(set(method) <= {"name","input","output","caller","serverStreaming"}, f"unknown method key for {service['name']}.{method.get('name')}")
            require(method.get("caller") in {"web","chat","agent"}, f"invalid caller for {service['name']}.{method.get('name')}")
            require(method.get("input") in known_types and method.get("output") in known_types, f"unknown method type for {service['name']}.{method.get('name')}")
            require(isinstance(method.get("serverStreaming",False),bool), f"invalid streaming flag for {service['name']}.{method.get('name')}")
            expected_stream = service["name"] == "ChatQueryService" and method.get("name") == "StreamConversationEvents"
            require(method.get("serverStreaming",False) is expected_stream, f"streaming method drift for {service['name']}.{method.get('name')}")

    caller_map=manifest.get("consumerCallerMap",{})
    expected_caller_map: dict[str,list[str]] = defaultdict(list)
    for service in services:
        callers={method["caller"] for method in service.get("methods",[])}
        require(len(callers)==1, f"mixed callers for {service['name']}")
        expected_caller_map[next(iter(callers))].append(service["name"])
    require(set(caller_map)=={"web","chat","agent","public"}, "unexpected caller-map keys")
    for caller in ("web","chat","agent"):
        require(not duplicates(caller_map.get(caller,[])), f"duplicate caller-map service for {caller}")
        require(set(caller_map.get(caller,[]))==set(expected_caller_map[caller]), f"caller map drift for {caller}")
    require(caller_map.get("public")==["GET /.well-known/jwks.json"], "public caller map drift")

    closures=manifest.get("consumerFileClosure",{})
    require(set(closures)=={"kokoro-site","kokoro-iam","kokoro-model","kokoro-capability","kokoro-chat","kokoro-agent","kokoro-web","root-e2e"}, "unexpected consumer set")
    owner_packages={
        "kokoro-site":"kokoro.site.v1", "kokoro-iam":"kokoro.iam.v1", "kokoro-model":"kokoro.model.v1",
        "kokoro-capability":"kokoro.capability.v1", "kokoro-chat":"kokoro.chat.v1", "kokoro-agent":"kokoro.agent.v1",
    }
    consumer_caller={"kokoro-chat":"chat","kokoro-agent":"agent","kokoro-web":"web","root-e2e":"web"}
    common_path="kokoro/common/v1/common.proto"
    for consumer,closure in closures.items():
        require(not duplicates(closure), f"duplicate file in {consumer} closure")
        require(set(closure)<=set(file_paths), f"unknown file in {consumer} closure")
        seeds={common_path}
        owner_package=owner_packages.get(consumer)
        if owner_package:
            seeds.update(file["path"] for file in files if file["package"]==owner_package)
        caller=consumer_caller.get(consumer)
        if caller:
            for service_name in caller_map[caller]:
                seeds.add(declaration_file[next(name for name in declaration_file if name.endswith(f".{service_name}"))])
        expected=set(seeds); pending=list(seeds)
        while pending:
            current=pending.pop()
            for imported in file_by_path[current].get("imports",[]):
                if imported in GOOGLE_IMPORTS or imported in expected:
                    continue
                expected.add(imported); pending.append(imported)
        require(set(closure)==expected, f"consumer closure drift for {consumer}")
    forbidden=("kokoro/agent/","kokoro/model/","kokoro/capability/")
    for consumer in ("kokoro-web","root-e2e"):
        require(not any(path.startswith(forbidden) for path in closures[consumer]), f"private owner proto in {consumer}")

    events=manifest.get("agentEvents",{}).get("variants",[])
    require(len(events)==20, "expected 20 Agent event variants")
    require([event.get("fieldNumber") for event in events]==list(range(20,40)), "Agent event field numbers must be 20..39")
    agent_event=next(message for message in messages if message["package"]=="kokoro.agent.v1" and message["name"]=="AgentEvent")
    require(len(agent_event["fields"])==25, "AgentEvent field inventory drift")
    require({field.get("oneof") for field in agent_event["fields"] if "oneof" in field}=={"payload"}, "AgentEvent oneof inventory drift")
    event_fields=[field for field in agent_event["fields"] if field.get("oneof")=="payload"]
    require(
        [(event["fieldNumber"],event["fieldName"],event["message"]) for event in events]
        == [(field["number"],field["name"],field["type"]) for field in event_fields],
        "Agent event oneof drift",
    )
    require([event["internalKind"] for event in events]==EXPECTED_AGENT_KINDS, "Agent event kind drift")

    http=manifest.get("http",{}); operations=http.get("operations",[])
    require(len(operations)==10, "expected 10 HTTP operations")
    require(not duplicates([op.get("operationId") for op in operations]), "duplicate operationId")
    for op in operations:
        parameters=op.get("parameters",[])
        require(not duplicates([(parameter.get("name"),parameter.get("in")) for parameter in parameters]), f"duplicate parameter in {op['operationId']}")
        for parameter in parameters:
            require(parameter.get("in") in {"path","query","header","cookie"}, f"invalid parameter location in {op['operationId']}")
            require(isinstance(parameter.get("required"),bool) and isinstance(parameter.get("schema"),dict), f"incomplete parameter in {op['operationId']}")
        path_names=set(re.findall(r"{([^}]+)}",op.get("path","")))
        declared={parameter["name"] for parameter in parameters if parameter["in"]=="path" and parameter["required"]}
        require(path_names==declared, f"path parameter drift in {op['operationId']}")
        require(isinstance(op.get("errorStatuses"), list) and all(isinstance(x,int) for x in op["errorStatuses"]), f"invalid error statuses in {op['operationId']}")
    require({op["operationId"]:op["errorStatuses"] for op in operations}==EXPECTED_OPERATION_ERROR_STATUSES, "operation error status drift")
    uint64_request_names={field["name"] for message in messages if message["name"].endswith("Request") for field in message.get("fields",[]) if field["type"]=="uint64"}
    safe_max=9007199254740991
    for schema in http.get("schemas",[]):
        for prop in schema.get("properties",[]):
            if prop.get("name") in uint64_request_names:
                require(prop.get("type")=="integer" and prop.get("minimum")==0 and prop.get("maximum")==safe_max, f"unsafe HTTP uint64 in {schema['name']}.{prop['name']}")
    for op in operations:
        for parameter in op.get("parameters",[]):
            schema=parameter.get("schema",{})
            if parameter.get("name") in uint64_request_names:
                require(schema.get("type")=="integer" and schema.get("minimum")==0 and schema.get("maximum")==safe_max, f"unsafe HTTP uint64 in {op['operationId']}.{parameter['name']}")
    error_body=http.get("errorBody",{})
    require(error_body.get("type")=="object" and error_body.get("additionalProperties") is False, "error body must be strict object")
    error_enum=next(enum for enum in enums if enum["name"]=="ErrorCode")
    codes={value["name"].lower().removeprefix("error_code_") for value in error_enum["values"] if value["number"]}
    require(set(EXPECTED_ERROR_STATUS_BY_CODE)==codes, "ErrorCode HTTP status map incomplete")
    require(http.get("errorStatusByCode")==EXPECTED_ERROR_STATUS_BY_CODE, "ErrorCode HTTP status map drift")
    require(http.get("browserJsonMapping")==EXPECTED_BROWSER_JSON_MAPPING, "browser JSON mapping drift")

    submit=next(message for message in messages if message["name"]=="SubmitMessageRequest")
    submit_names={field["name"] for field in submit["fields"]}
    require(not ({"message_id","expected_conversation_generation"}&submit_names), "SubmitMessage contains client identity/generation")
    run_view=next(message for message in messages if message["package"]=="kokoro.chat.v1" and message["name"]=="RunView")
    require(run_view["fields"][0]=={"number":1,"name":"launch_id","type":"string","label":"required"}, "RunView launch identity drift")
    require(run_view["fields"][1]=={"number":2,"name":"agent_run_id","type":"string","label":"optional"}, "RunView pre-admission identity drift")
    agent_messages=[message for message in messages if message["package"]=="kokoro.agent.v1"]
    for message in agent_messages:
        tenant={field["name"] for field in message["fields"]}&{"site_id","organization_id"}
        require(not tenant or message["name"]=="LaunchRunRequest", f"tenant axis leaked into {message['name']}")

    sse=manifest.get("sse",{})
    require(len(sse.get("browserEvents",[]))==21, "expected 21 browser event kinds")
    require([field["name"] for field in sse.get("dataFields",[])]==["event_id","seq","session_id","run_id","timestamp","kind","payload"], "browser SSE envelope drift")
    run_id=next(field for field in sse["dataFields"] if field["name"]=="run_id")
    require(run_id.get("mapsFrom")=="chat_run_launch.launch_id", "browser run_id must map launch_id")
    awaiting=next(event for event in sse["browserEvents"] if event["kind"]=="tool.awaiting_approval")
    awaiting_names={field["name"] for field in awaiting["payload"] if field.get("required")}
    require({"interaction_id","interaction_generation"}<=awaiting_names, "HITL browser identity incomplete")
    rules=manifest.get("rules",{})
    require("globally monotonic" in rules.get("agentEventSequence","") and "never resets seq" in rules.get("agentEventSequence",""), "Agent event cursor semantics missing")
    require(rules.get("projectionConsumers",{}).get("sliceA")==["chat"], "projection consumer allowlist drift")
    arms=rules.get("controlDecisionPayloadSchemasByKind",{})
    require(set(arms)=={"approve","edit","reject","respond","submit"}, "control decision arms incomplete")
    require(all(arm.get("additionalProperties") is False for arm in arms.values()), "control decision arm must be strict")
    require("HMAC-SHA256" in rules.get("magicLinkNonceDerivation",""), "magic-link nonce derivation missing")
    require(rules.get("accessJwt")==EXPECTED_ACCESS_JWT, "access JWT contract drift")
    require(rules.get("streamAuthorizationExpiry")==EXPECTED_STREAM_AUTHORIZATION_EXPIRY, "stream authorization deadline drift")
    require(rules.get("sessionCookiePolicy",{}).get("maxAgeSeconds")==2592000, "session cookie cap drift")
    require(rules.get("paginationDefaults",{}).get("listConversationsLimit")==50, "list conversation default drift")
    require("Array.from(content).slice(0, 80)" in rules.get("firstConversationTitle",{}).get("algorithm",""), "first conversation title rule missing")
    materialization=rules.get("snapshotMaterialization",{})
    require(materialization==EXPECTED_SNAPSHOT_MATERIALIZATION, "snapshot materialization map drift")
    require(set(materialization)-{"retentionRule"}=={event["kind"] for event in sse["browserEvents"]}, "snapshot materialization map incomplete")
    definitions=sse.get("typeDefinitions",{})
    primitives={"string","boolean","json-object","safe-nonnegative-integer"}
    unresolved={(event["kind"],field["type"]) for event in sse["browserEvents"] for field in event["payload"] if field["type"] not in primitives and field["type"] not in definitions}
    require(not unresolved, f"unresolved SSE types: {sorted(unresolved)}")
    mapping=sse.get("projectionMappings",{})
    require(mapping.get("interactionKind",{}).get("INTERACTION_KIND_APPROVAL")=="tool_approval", "approval projection drift")
    require(mapping.get("subagentSource",{}).get("SUBAGENT_SOURCE_BUILT_IN")=="built-in", "subagent source projection drift")
    normalized=json.dumps(manifest,ensure_ascii=False,separators=(",",":"),sort_keys=True).encode()
    require(hashlib.sha256(normalized).hexdigest()==EXPECTED_NORMALIZED_MANIFEST_SHA256, "reviewed manifest digest drift")

def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument('manifest',type=Path)
    args=parser.parse_args()
    validate(load_manifest(args.manifest))
    print('slice_a_manifest_valid')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
