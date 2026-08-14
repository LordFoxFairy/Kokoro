from __future__ import annotations

import json
from pathlib import Path

import yaml


ROOT = Path(__file__).parents[2]
MANIFEST = json.loads((ROOT / "contract/slice-a-contract-manifest.yaml").read_text())
OPENAPI_PATH = ROOT / "contract/openapi/slice-a-web-v1.yaml"


def _openapi() -> dict:
    return yaml.safe_load(OPENAPI_PATH.read_text())


def test_openapi_operation_inventory_and_parameters_are_exact() -> None:
    document = _openapi()
    rendered = {
        (operation["operationId"], method, path, next(int(status) for status in operation["responses"] if int(status) < 400))
        for path, path_item in document["paths"].items()
        for method, operation in path_item.items()
    }
    expected = {
        (operation["operationId"], operation["method"], operation["path"], operation["successStatus"])
        for operation in MANIFEST["http"]["operations"]
    }
    assert rendered == expected
    for source in MANIFEST["http"]["operations"]:
        operation = document["paths"][source["path"]][source["method"]]
        assert operation["parameters"] == [
            {
                "name": parameter["name"],
                "in": parameter["in"],
                "required": parameter["required"],
                "schema": parameter["schema"],
            }
            for parameter in source["parameters"]
        ]
        if source["requestBodySchema"] is None:
            assert "requestBody" not in operation
        else:
            assert operation["requestBody"] == {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {"$ref": f"#/components/schemas/{source['requestBodySchema']}"}
                    }
                },
            }
        assert set(map(int, operation["responses"])) == {source["successStatus"], *source["errorStatuses"]}
        assert operation["security"] == (
            [{"cookieAuth": []}]
            if any(
                parameter["name"] == "kokoro_session" and parameter["required"]
                for parameter in source["parameters"]
            )
            else []
        )
        success = operation["responses"][str(source["successStatus"])]
        expected_headers = {
            name: {
                "description": " | ".join(value) if isinstance(value, list) else value,
                "schema": {"type": "string"},
            }
            for name, value in source["successHeaders"].items()
        }
        assert success.get("headers", {}) == expected_headers
        if source["alternateResponses"]:
            assert success["x-kokoro-alternate-responses"] == source["alternateResponses"]
        else:
            assert "x-kokoro-alternate-responses" not in success
        if source["responseSchema"] == "text/event-stream":
            assert success["content"] == {"text/event-stream": {"schema": {"type": "string"}}}
        elif source["responseSchema"] != "Empty" and source["successStatus"] not in {204, 303}:
            assert success["content"] == {
                "application/json": {
                    "schema": {"$ref": f"#/components/schemas/{source['responseSchema']}"}
                }
            }
        else:
            assert "content" not in success


def test_openapi_preserves_browser_security_and_minimal_surface() -> None:
    document = _openapi()
    schemas = document["components"]["schemas"]
    assert set(schemas["RequestMagicLinkHttpRequest"]["properties"]) == {"email"}
    submit = schemas["SubmitMessageHttpRequest"]
    assert not ({"generation", "command_id", "request_digest", "site_id", "organization_id", "principal_id"} & set(submit["properties"]))
    decision = schemas["ControlDecisionHttp"]
    assert len(decision["oneOf"]) == 5
    assert {arm["properties"]["kind"]["const"] for arm in decision["oneOf"]} == {"approve", "edit", "reject", "respond", "submit"}
    decide_body = schemas["DecideInteractionHttpRequest"]
    assert decide_body["properties"]["decisions"]["minItems"] == 1
    assert decide_body["properties"]["decisions"]["x-kokoro-unique-by"] == "target_id"
    stream = document["paths"]["/api/session/conversations/{conversation_id}/events"]["get"]
    assert stream["responses"]["200"]["content"] == {"text/event-stream": {"schema": {"type": "string"}}}
    assert "409" in stream["responses"]
    assert all(schema.get("additionalProperties") is False for name, schema in schemas.items() if schema.get("type") == "object" and name != "ControlDecisionHttp")
    forbidden = ("hub", "billing", "storage", "project", "payment", "admin")
    assert not any(word in path.lower() for path in document["paths"] for word in forbidden)
    assert set(schemas) == {
        "kokoro.chat.v1.ConversationState", "kokoro.chat.v1.InteractionStatus",
        "kokoro.chat.v1.MessagePartKind", "kokoro.chat.v1.MessagePartStatus",
        "kokoro.chat.v1.MessageRole", "kokoro.chat.v1.MessageStatus",
        "kokoro.chat.v1.ProjectedInteractionKind", "kokoro.chat.v1.RunViewState",
        "kokoro.chat.v1.RunViewTerminalKind", "kokoro.common.v1.ControlStatus",
        "kokoro.chat.v1.Conversation", "kokoro.chat.v1.ConversationSummary",
        "kokoro.chat.v1.CreateConversationResponse", "kokoro.chat.v1.DecideInteractionResponse",
        "kokoro.chat.v1.Interaction", "kokoro.chat.v1.ListConversationsResponse",
        "kokoro.chat.v1.Message", "kokoro.chat.v1.MessagePart",
        "kokoro.chat.v1.ReadConversationSnapshotResponse", "kokoro.chat.v1.RunView",
        "kokoro.chat.v1.SubmitMessageResponse", "kokoro.common.v1.PageResult",
        "ControlDecisionHttp", "CreateConversationHttpRequest", "DecideInteractionHttpRequest",
        "RequestMagicLinkHttpRequest", "RequestMagicLinkHttpResponse", "SessionStateHttpResponse",
        "SubmitMessageHttpRequest", "KokoroError",
    }
    serialized = json.dumps(schemas)
    assert not any(secret in serialized for secret in ("access_token", "refresh_token", "secret_handle"))
    assert not any(name.startswith(("kokoro.iam.", "kokoro.site.", "kokoro.agent.", "kokoro.model.", "kokoro.capability.")) for name in schemas)
