from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).parents[2]
MANIFEST = json.loads((ROOT / "contract/slice-a-contract-manifest.yaml").read_text())
LEGACY = json.loads((ROOT / "contract/tests/fixtures/legacy-wire-v1.json").read_text())

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
    assert launch["fields"] == LEGACY["control"]["authorityLaunchRunFields"]
    assert apply_control["fields"] == LEGACY["control"]["authorityApplyControlFields"]
    names = {field["name"] for field in launch["fields"]}
    assert {"namespace", "session_id", "thread_id", "site_id", "organization_id"} <= names
    agent_messages = [item for item in MANIFEST["protobuf"]["messages"] if item["package"] == "kokoro.agent.v1"]
    assert all(
        item["name"] == "LaunchRunRequest"
        or not ({"site_id", "organization_id", "principal_id", "role_id", "permission_id"} & {field["name"] for field in item["fields"]})
        for item in agent_messages
    )
    legacy_messages = {item["kind"]: item for item in LEGACY["control"]["legacyMessages"]}
    assert {"run.request", "run.resume", "run.cancel", "run.steer"} == set(legacy_messages)
    assert {"thread_id", "input", "runtime", "context"} <= {
        item["name"] for item in legacy_messages["run.request"]["fields"]
    }
    assert {"decisions"} <= {item["name"] for item in legacy_messages["run.resume"]["fields"]}
    assert {"message_id", "content"} <= {item["name"] for item in legacy_messages["run.steer"]["fields"]}


def test_magic_link_idempotency_and_stream_cursor_semantics_are_frozen() -> None:
    rules = MANIFEST["rules"]
    assert "nonce_digest" in rules["magicLinkNonceBinding"]
    refresh = rules["authCommandIdentity"]["refreshSession"]
    assert "sealed in the Web envelope" in refresh["commandId"]
    assert "missing/different command id triggers family revoke" in refresh["rotation"]
    assert "never resets seq" in rules["agentEventSequence"]
    stream = next(item for item in MANIFEST["http"]["operations"] if item["operationId"] == "streamConversationEvents")
    assert next(item for item in stream["parameters"] if item["name"] == "after_seq")["schema"] == {
        "type": "integer", "minimum": 0, "maximum": 9007199254740991
    }


def test_legacy_yaml_authority_is_absent_after_parity_freeze() -> None:
    assert not list((ROOT / "contract/spec").glob("*.yaml"))
