from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).parents[2]
MANIFEST = json.loads((ROOT / "contract/slice-a-contract-manifest.yaml").read_text())
LEGACY = json.loads((ROOT / "contract/tests/fixtures/legacy-wire-v1.json").read_text())
WEB_PROMOTION_PLAN = (
    ROOT / "docs/superpowers/plans/2026-08-14-slice-a-web-e2e-promotion-plan.md"
).read_text()

RAW_RENAMES = {
    "tool.invoked": {"args": "args_json"},
    "tool.awaiting_approval": {
        "args": "args_json", "kind": "interaction_kind", "risk": "risk_json",
        "input_schema": "input_schema_json",
    },
    "tool.returned": {"summary": "summary_json"},
    "subagent.tool.invoked": {"args": "args_json"},
    "run.control.receipt": {"decision_id": "command_id", "control_status": "status"},
    "run.completed": {"token_usage": "usage"},
}
RAW_REQUIRED_ENRICHMENTS = {
    ("tool.returned", "truncated"),
    ("tool.returned", "rejected"),
    ("tool.returned", "responded"),
    ("subagent.finished", "failed"),
    ("subagent.tool.returned", "truncated"),
}
RAW_TYPE_MAP = {
    "array:enum:resume_decision": ".kokoro.common.v1.DecisionKind",
    "array:object:Todo": ".kokoro.agent.v1.Todo",
    "array:string_nonempty": "string",
    "boolean": "bool",
    "enum:awaiting_kind": ".kokoro.agent.v1.InteractionKind",
    "enum:control_receipt_status": ".kokoro.common.v1.ControlStatus",
    "enum:run_completed_status": ".kokoro.agent.v1.RunCompletionStatus",
    "enum:run_error_code": ".kokoro.agent.v1.RunFailureCode",
    "enum:subagent_source": ".kokoro.agent.v1.SubagentSource",
    "int": "uint64",
    "object:Risk": "bytes",
    "object:TokenUsage": ".kokoro.agent.v1.RunUsage",
    "record": "bytes",
    "string": "string",
    "string_nonempty": "string",
}
BROWSER_TYPE_MAP = {
    "array:enum:resume_decision": "decision-string-array",
    "array:object:Todo": "todo-array",
    "array:string_nonempty": "unique-string-array",
    "boolean": "boolean",
    "enum:awaiting_kind": "interaction-kind-string",
    "enum:run_completed_status": "completed-or-cancelled",
    "enum:run_error_code": "run-failure-code-string",
    "enum:subagent_source": "subagent-source-string",
    "int": "safe-nonnegative-integer",
    "object:Risk": "risk-object",
    "object:TokenUsage": "nullable-token-usage",
    "record": "json-object",
    "string": "string",
    "string_nonempty": "string",
}


def test_mature_agent_and_browser_event_kind_parity() -> None:
    messages = {(item["package"], item["name"]): item for item in MANIFEST["protobuf"]["messages"]}
    raw = []
    for variant in MANIFEST["agentEvents"]["variants"]:
        message = messages[("kokoro.agent.v1", variant["message"].split(".")[-1])]
        raw.append({"kind": variant["internalKind"], "authorityFields": message["fields"]})
    assert raw == [
        {"kind": item["kind"], "authorityFields": item["authorityFields"]}
        for item in LEGACY["rawEvents"]
    ]
    assert [item["kind"] for item in LEGACY["rawEvents"]] == [
        item["internalKind"] for item in MANIFEST["agentEvents"]["variants"]
    ]
    for item in LEGACY["rawEvents"]:
        kind = item["kind"]
        rename = RAW_RENAMES.get(kind, {})
        legacy_by_authority_name = {
            rename.get(field["name"], field["name"]): field for field in item["legacyFields"]
        }
        authority_by_name = {field["name"]: field for field in item["authorityFields"]}
        assert set(legacy_by_authority_name) == set(authority_by_name)
        for name, legacy_field in legacy_by_authority_name.items():
            authority_field = authority_by_name[name]
            assert authority_field["type"] == RAW_TYPE_MAP[legacy_field["abstractType"]]
            assert (authority_field["label"] == "repeated") is legacy_field["abstractType"].startswith("array:")
            is_required = authority_field["label"] != "optional"
            if (kind, name) in RAW_REQUIRED_ENRICHMENTS:
                assert legacy_field["optional"] is True and is_required
            else:
                assert is_required is not legacy_field["optional"]
    assert [
        {"kind": item["kind"], "authorityFields": item["payload"]}
        for item in MANIFEST["sse"]["browserEvents"]
    ] == [
        {"kind": item["kind"], "authorityFields": item["authorityFields"]}
        for item in LEGACY["browserEvents"]
    ]
    for item in LEGACY["browserEvents"]:
        legacy_names = {field["name"] for field in item["legacyFields"]}
        authority_names = {field["name"] for field in item["authorityFields"]}
        approved_additions = {"interaction_id", "interaction_generation"} if item["kind"] == "tool.awaiting_approval" else set()
        assert authority_names == legacy_names | approved_additions
        for field in item["legacyFields"]:
            authority = next(value for value in item["authorityFields"] if value["name"] == field["name"])
            assert authority["type"] == BROWSER_TYPE_MAP[field["abstractType"]]
            assert authority["required"] is not field["optional"]


def test_mature_control_and_run_scope_invariants_are_preserved() -> None:
    arms = MANIFEST["rules"]["controlDecisionPayloadSchemasByKind"]
    assert arms == LEGACY["control"]["authorityDecisionPayloadSchemasByKind"]
    legacy_arms = {item["type"]: item for item in LEGACY["control"]["legacyDecisionArms"]}
    assert list(arms) == list(legacy_arms)
    for kind, legacy in legacy_arms.items():
        assert legacy["fields"][0]["name"] in {"tool_id", "request_id"}
        assert [item["name"] for item in arms[kind]["properties"]] == [
            item["name"] for item in legacy["fields"][1:]
        ]
        assert arms[kind]["required"] == [
            item["name"] for item in legacy["fields"][1:] if not item.get("optional", False)
        ]
    launch = next(item for item in MANIFEST["protobuf"]["messages"] if item["name"] == "LaunchRunRequest")
    apply_control = next(item for item in MANIFEST["protobuf"]["messages"] if item["name"] == "ApplyControlRequest")
    assert launch["fields"] == [
        {"number": 1, "name": "request_id", "type": "string", "label": "required"},
        {"number": 2, "name": "run_id", "type": "string", "label": "required"},
        {"number": 3, "name": "session_id", "type": "string", "label": "required"},
        {"number": 4, "name": "feature_key", "type": "string", "label": "required"},
        {"number": 5, "name": "execution_identity", "type": ".kokoro.common.v1.ExecutionIdentity", "label": "required"},
        {"number": 6, "name": "message_id", "type": "string", "label": "required"},
        {"number": 7, "name": "content", "type": "string", "label": "required"},
        {"number": 8, "name": "requested_model_label", "type": "string", "label": "optional"},
        {"number": 9, "name": "trace_json", "type": "bytes", "label": "required"},
    ]
    assert apply_control["fields"] == LEGACY["control"]["authorityApplyControlFields"]
    names = {field["name"] for field in launch["fields"]}
    assert {"run_id", "session_id", "feature_key", "execution_identity", "message_id", "content"} <= names
    assert not ({"namespace", "thread_id", "site_id", "organization_id", "requested_agent_preset_key", "requested_capability_selectors"} & names)
    agent_messages = [item for item in MANIFEST["protobuf"]["messages"] if item["package"] == "kokoro.agent.v1"]
    assert all(
        item["name"] == "LaunchRunRequest"
        or not ({"site_id", "organization_id", "principal_id", "role_id", "permission_id"} & {field["name"] for field in item["fields"]})
        for item in agent_messages
    )


def test_magic_link_idempotency_and_stream_cursor_semantics_are_frozen() -> None:
    rules = MANIFEST["rules"]
    assert "nonce_digest" in rules["magicLinkNonceBinding"]
    refresh = rules["authCommandIdentity"]["refreshSession"]
    assert "sealed in the Web envelope" in refresh["commandId"]
    assert "missing/different command id triggers family revoke" in refresh["rotation"]
    assert (
        "The Slice A envelope contains exactly seven fields: `principalId`, `siteId`, "
        "`organizationId`, `authSessionId`, `accessToken`, `refreshToken`, and "
        "`refreshCommandId`."
    ) in WEB_PROMOTION_PLAN
    assert (
        "The unpredictable `refreshCommandId` is sealed beside the current `refreshToken` "
        "and MUST NOT be derived predictably."
    ) in WEB_PROMOTION_PLAN
    assert (
        "A lost `RefreshSession` response retries the same token and command ID; after a "
        "delivered success, Web seals a fresh random command ID beside the successor token."
    ) in WEB_PROMOTION_PLAN
    assert (
        "Presenting the old token without its command ID or with a different command ID "
        "triggers refresh-family revocation."
    ) in WEB_PROMOTION_PLAN
    assert "never resets seq" in rules["agentEventSequence"]
    stream = next(item for item in MANIFEST["http"]["operations"] if item["operationId"] == "streamConversationEvents")
    assert next(item for item in stream["parameters"] if item["name"] == "after_seq")["schema"] == {
        "type": "integer", "minimum": 0, "maximum": 9007199254740991
    }


def test_chat_stream_establishment_is_an_explicit_owner_ready_handshake() -> None:
    messages = {
        item["name"]: item
        for item in MANIFEST["protobuf"]["messages"]
        if item["package"] == "kokoro.chat.v1"
    }
    assert messages["StreamConversationEventsReady"]["fields"] == [
        {"number": 1, "name": "accepted_after_seq", "type": "uint64", "label": "required"},
        {"number": 2, "name": "watermark", "type": "uint64", "label": "required"},
    ]
    assert messages["StreamConversationEventsResponse"]["fields"] == [
        {
            "number": 1,
            "name": "event",
            "type": ".kokoro.chat.v1.BrowserSessionEvent",
            "label": "required",
            "oneof": "payload",
        },
        {
            "number": 2,
            "name": "ready",
            "type": ".kokoro.chat.v1.StreamConversationEventsReady",
            "label": "required",
            "oneof": "payload",
        },
    ]
    assert MANIFEST["rules"]["streamEstablishment"] == {
        "validationOrder": [
            "authenticate workload and caller access JWT",
            "authorize chat.conversation.read and derive ActorContext from IAM",
            "validate conversation ownership and Site/Organization scope",
            "validate after_seq against current watermark and retained cursor boundary",
        ],
        "failure": "Any typed failure, including SNAPSHOT_REQUIRED, terminates before the first response message; no ready or event is yielded.",
        "success": "Immediately yield exactly one ready as the first response, including for an idle stream where accepted_after_seq equals watermark; accepted_after_seq exactly echoes the validated request cursor and watermark is the current owner watermark observed during validation.",
        "continuation": "After ready, yield only event messages whose seq values are strictly increasing from accepted_after_seq; never yield a second ready.",
        "web": "Web consumes and validates ready before committing browser HTTP 200, never forwards ready as an SSE frame, and then pulls events with backpressure.",
        "wireCompatibility": "Field 1 remains BrowserSessionEvent and moves into payload oneof; its encoded bytes remain unchanged. Field 2 is additive ready. Old readers ignore ready, while new readers accept old event bytes as the event arm.",
    }


def test_legacy_yaml_authority_is_absent_after_parity_freeze() -> None:
    assert not list((ROOT / "contract/spec").glob("*.yaml"))
