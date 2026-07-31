"""Public Media/Artifact contracts frozen by ADR-015 before runtime work."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
PUBLIC_OPENAPI = ROOT / "contract/openapi/platform-public-v1.yaml"
HTTP_SPEC = ROOT / "contract/spec/http.yaml"

MEDIA_ARTIFACT_OPERATIONS = {
    "listMediaOperationDefinitions": (
        "get",
        "/v1/projects/{projectRef}/media-operation-definitions",
    ),
    "getMediaOperationDefinition": (
        "get",
        "/v1/projects/{projectRef}/media-operation-definitions/{definitionRef}",
    ),
    "listMediaOperationModelOptions": (
        "get",
        "/v1/projects/{projectRef}/media-operation-definitions/{definitionRef}/model-options",
    ),
    "quoteMediaOperation": (
        "post",
        "/v1/projects/{projectRef}/media-operation-quotes",
    ),
    "submitMediaOperation": ("post", "/v1/projects/{projectRef}/media-operations"),
    "listMediaOperations": ("get", "/v1/projects/{projectRef}/media-operations"),
    "getMediaOperation": (
        "get",
        "/v1/projects/{projectRef}/media-operations/{operationRef}",
    ),
    "cancelMediaOperation": (
        "post",
        "/v1/projects/{projectRef}/media-operations/{operationRef}:cancel",
    ),
    "recoverMediaOperationCommand": (
        "get",
        "/v1/projects/{projectRef}/media-operation-commands/{commandId}",
    ),
    "listArtifacts": ("get", "/v1/projects/{projectRef}/artifacts"),
    "getArtifact": ("get", "/v1/projects/{projectRef}/artifacts/{artifactRef}"),
    "listArtifactVersions": (
        "get",
        "/v1/projects/{projectRef}/artifacts/{artifactRef}/versions",
    ),
    "getArtifactVersion": (
        "get",
        "/v1/projects/{projectRef}/artifacts/{artifactRef}/versions/{artifactVersionRef}",
    ),
    "issueArtifactDeliveryAuthorization": (
        "post",
        "/v1/projects/{projectRef}/artifacts/{artifactRef}/versions/{artifactVersionRef}/delivery-authorizations",
    ),
    "revokeArtifactDeliveryAuthorization": (
        "post",
        "/v1/projects/{projectRef}/artifact-delivery-authorizations/{authorizationRef}:revoke",
    ),
}


def _openapi() -> dict:
    return yaml.safe_load(PUBLIC_OPENAPI.read_text())


def _operations(document: dict) -> dict[str, tuple[str, str, dict]]:
    return {
        operation["operationId"]: (method, path, operation)
        for path, item in document["paths"].items()
        for method, operation in item.items()
        if isinstance(operation, dict) and "operationId" in operation
    }


def _parameter_refs(operation: dict) -> set[str]:
    return {
        parameter["$ref"].rsplit("/", 1)[-1]
        for parameter in operation.get("parameters", [])
        if "$ref" in parameter
    }


def test_public_media_and_artifact_surface_has_one_site_bff_transport() -> None:
    document = _openapi()
    operations = _operations(document)

    assert len(MEDIA_ARTIFACT_OPERATIONS) == 15
    for operation_id, (expected_method, expected_path) in MEDIA_ARTIFACT_OPERATIONS.items():
        method, path, operation = operations[operation_id]
        assert (method, path) == (expected_method, expected_path)
        assert operation.get("security", document["security"]) == [
            {"ProductWorkload": [], "UserSession": []}
        ]
        assert "ContractVersion" in _parameter_refs(operation)

    standard_mutations = {
        "quoteMediaOperation",
        "submitMediaOperation",
        "cancelMediaOperation",
        "revokeArtifactDeliveryAuthorization",
    }
    for operation_id in standard_mutations:
        refs = _parameter_refs(operations[operation_id][2])
        assert {"CommandIdentity", "IdempotencyKey", "CsrfToken"}.issubset(refs)

    issue = operations["issueArtifactDeliveryAuthorization"][2]
    assert _parameter_refs(issue) == {
        "ProjectRef",
        "ArtifactRef",
        "ArtifactVersionRef",
        "ContractVersion",
        "CsrfToken",
    }
    assert "201" in issue["responses"]

    submit = operations["submitMediaOperation"][2]
    assert "CallerRequestFingerprint" in _parameter_refs(submit)
    assert {"201", "202"}.issubset(submit["responses"])
    assert {"200", "202"}.issubset(
        operations["cancelMediaOperation"][2]["responses"]
    )


def test_public_media_and_artifact_schemas_are_closed_bounded_and_owner_safe() -> None:
    document = _openapi()
    schemas = document["components"]["schemas"]

    definition = schemas["OperationDefinition"]
    assert definition["discriminator"]["propertyName"] == "kind"
    assert definition["oneOf"] == [
        {"$ref": "#/components/schemas/ImageTextToImageOperationDefinition"}
    ]
    image_definition = schemas["ImageTextToImageOperationDefinition"]
    assert image_definition["additionalProperties"] is False
    assert image_definition["properties"]["definitionKey"]["const"] == (
        "image.text_to_image@v1"
    )
    assert image_definition["properties"]["promptMaximumUtf8Bytes"]["const"] == 32768
    assert image_definition["properties"]["maximumCandidateCount"]["maximum"] == 4

    operation_input = schemas["MediaOperationInput"]
    assert operation_input["discriminator"]["propertyName"] == "kind"
    image_input = schemas["ImageTextToImageOperationInput"]
    assert image_input["additionalProperties"] is False
    assert image_input["properties"]["promptIntent"]["x-kokoro-max-utf8-bytes"] == 32768
    assert image_input["properties"]["candidateCount"]["maximum"] == 4
    assert "modelOptionRevisionRef" in image_input["required"]
    assert "modelOptionRef" not in image_input["properties"]

    for page in (
        "MediaOperationDefinitionPage",
        "MediaDefinitionModelOptionPage",
        "MediaOperationPage",
        "ArtifactPage",
        "ArtifactVersionPage",
    ):
        assert schemas[page]["additionalProperties"] is False
        assert schemas[page]["properties"]["items"]["maxItems"] <= 100
        assert schemas[page]["properties"]["pageInfo"]["$ref"].endswith("/PageInfo")

    media_view = schemas["MediaOperationAdmissionPendingView"]
    assert media_view["properties"]["candidates"]["maxItems"] == 4
    artifact_version = schemas["ImageArtifactVersionReady"]
    assert artifact_version["properties"]["sourceArtifactVersionRefs"]["maxItems"] == 16

    exposed = yaml.safe_dump(
        {
            name: schemas[name]
            for name in (
                "MediaOperationView",
                "ArtifactSummary",
                "ImageArtifactVersion",
                "ArtifactDeliveryAuthorization",
            )
        }
    ).lower()
    for forbidden in (
        "providerurl",
        "presigned",
        "storagekey",
        "bucket",
        "secretref",
        "fallbackorder",
        "orchestrationmodelref",
    ):
        assert forbidden not in exposed


def test_artifact_delivery_is_non_replayable_no_store_and_revocable() -> None:
    document = _openapi()
    schemas = document["components"]["schemas"]
    responses = document["components"]["responses"]

    request = schemas["ArtifactDeliveryAuthorizationInput"]
    assert request["discriminator"]["propertyName"] == "purpose"
    assert len(request["oneOf"]) == 3
    authorization = schemas["ArtifactDeliveryAuthorization"]
    assert authorization["additionalProperties"] is False
    assert authorization["properties"]["audience"]["const"] == (
        "site-bff.artifact-delivery"
    )
    assert "deliveryCapability" in authorization["required"]
    assert "expiresAt" in authorization["required"]
    assert all(
        field not in authorization["properties"]
        for field in ("url", "deliveryUrl", "providerUrl", "storageKey")
    )
    assert (
        responses["ArtifactDeliveryAuthorizationResponse"]["headers"]["Cache-Control"]
        ["schema"]["const"]
        == "no-store"
    )
    revocation = schemas["ArtifactDeliveryRevocationReceipt"]
    assert revocation["properties"]["state"]["enum"] == [
        "revoked",
        "already_revoked",
        "expired",
    ]
    assert "deliveryCapability" not in revocation["properties"]


def test_media_public_errors_are_typed_and_effect_ambiguity_is_recoverable() -> None:
    document = _openapi()
    codes = set(document["components"]["schemas"]["ErrorCode"]["enum"])
    assert {
        "MEDIA_INPUT_REJECTED",
        "MEDIA_CALLER_FINGERPRINT_MISMATCH",
        "MEDIA_DEFINITION_UNAVAILABLE",
        "MEDIA_MODEL_OPTION_UNAVAILABLE",
        "MEDIA_CREDIT_INSUFFICIENT",
        "MEDIA_POLICY_REJECTED",
        "MEDIA_OPERATION_VERSION_CONFLICT",
        "MEDIA_CANCEL_NOT_ACCEPTED",
        "MEDIA_TEMPORARILY_UNAVAILABLE",
        "PAGE_CURSOR_INVALID",
        "ARTIFACT_NOT_AVAILABLE",
        "ARTIFACT_DELIVERY_NOT_ALLOWED",
        "ARTIFACT_DELIVERY_AUTHORIZATION_REJECTED",
        "ARTIFACT_TEMPORARILY_UNAVAILABLE",
    }.issubset(codes)

    receipt = document["components"]["schemas"]["MediaOperationCommandReceipt"]
    assert receipt["discriminator"]["propertyName"] == "receiptKind"
    assert len(receipt["oneOf"]) == 6
    wire = yaml.safe_dump(receipt).lower()
    for forbidden in ("ownerkeyed", "persistencehmac", "hmacversion", "ownerpreimage"):
        assert forbidden not in wire


def test_media_canonical_proto_spec_corpus_and_temp_generator(tmp_path: Path) -> None:
    proto = ROOT / "contract/proto/kokoro/platform/media/v1/media_canonical.proto"
    spec = yaml.safe_load((ROOT / "contract/spec/media-canonicalization.yaml").read_text())
    corpus = json.loads(
        (ROOT / "contract/corpus/media-canonicalization-v1.json").read_text()
    )

    source = proto.read_text()
    assert "message CanonicalMediaOperationInputV1" in source
    assert "message ImageTextToImageSpecV1" in source
    assert "model_option_revision_ref" in source
    assert "model_option_ref" not in source
    assert spec == {
        "schema_version": 1,
        "algorithm": "SHA256_DETERMINISTIC_PROTOBUF_V1",
        "domain_separator_hex": (
            "6b6f6b6f726f2e6d656469612e63616c6c65722d726571756573742d"
            "66696e6765727072696e742e763100"
        ),
        "message": "kokoro.platform.media.v1.CanonicalMediaOperationInputV1",
        "unknown_fields": "reject",
        "unicode_normalization": "none",
        "kind": "image_text_to_image",
        "input_errors": {
            "$input": "MEDIA_CANONICAL_INPUT_REQUIRED",
            "$shape": "MEDIA_CANONICAL_UNKNOWN_OR_MISSING_FIELD",
            "$accessor": "MEDIA_CANONICAL_DATA_PROPERTY_REQUIRED",
            "contractMajor": "MEDIA_CANONICAL_CONTRACT_UNSUPPORTED",
            "definitionRevisionRef": "MEDIA_CANONICAL_REFERENCE_INVALID",
            "kind": "MEDIA_CANONICAL_KIND_UNSUPPORTED",
            "promptIntent": "MEDIA_CANONICAL_PROMPT_INVALID",
            "aspectRatio": "MEDIA_CANONICAL_ASPECT_RATIO_INVALID",
            "candidateCount": "MEDIA_CANONICAL_CANDIDATE_COUNT_INVALID",
            "modelOptionRevisionRef": "MEDIA_CANONICAL_REFERENCE_INVALID",
            "outputFormat": "MEDIA_CANONICAL_OUTPUT_FORMAT_INVALID",
        },
    }
    cases = {case["id"]: case for case in corpus["cases"]}
    assert len(cases) >= 10
    minimal = cases["minimal-square-png"]
    assert minimal["canonicalHex"] == (
        "080112056465665f311a120a01781001180122076d6f64656c5f312801"
    )
    assert minimal["fingerprintSha256"] == (
        "17e00b3435bb3040a94d6297a6d5f9be16fc87333c589bc6ae39ee75ee931c93"
    )

    output = tmp_path / "media-canonical.ts"
    completed = subprocess.run(
        [
            "node",
            "contract/generate-media-canonical.mjs",
            "--validate-corpus",
            "--output",
            str(output),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    generated = output.read_text()
    assert "canonicalMediaOperationInputV1Bytes" in generated
    assert "mediaCallerRequestFingerprintPreimage" in generated
    assert "provider" not in generated.lower()


def test_browser_media_artifact_and_cost_parts_are_closed_owner_projections() -> None:
    spec = yaml.safe_load(HTTP_SPEC.read_text())
    enums = spec["enums"]
    for name in (
        "media_operation_state",
        "media_candidate_state",
        "artifact_availability",
        "artifact_media_class",
        "credit_cost_projection_state",
        "projection_freshness_state",
        "media_safe_failure_code",
        "artifact_image_format",
    ):
        assert name in enums

    objects = {item["name"]: item for item in spec["objects"]}
    media = objects["MediaOperationPartPayload"]
    assert media["discriminator"] == "state"
    media_fields = {field["name"]: field for field in media["common_fields"]}
    assert set(media_fields) == {
        "media_operation_ref",
        "definition_ref",
        "definition_revision_ref",
        "owner_version",
        "progress_bps",
        "candidates",
        "cost_projection",
        "updated_at",
    }
    assert media_fields["candidates"]["max_items"] == 4
    assert "safe_metadata" not in media_fields
    assert "status" not in media_fields

    candidate = objects["MediaCandidatePart"]
    assert candidate["discriminator"] == "state"
    artifact = objects["ArtifactPartPayload"]
    assert artifact["discriminator"] == "availability"
    cost = objects["CostPartPayload"]
    assert cost["discriminator"] == "state"
    assert {variant["value"] for variant in cost["variants"]} == {
        "pending",
        "estimated",
        "final",
        "corrected",
        "unavailable",
    }


def test_platform_public_registry_keeps_new_surface_contract_only() -> None:
    registry = json.loads((ROOT / "contract/registry/boundaries.yaml").read_text())
    boundary = next(item for item in registry["boundaries"] if item["id"] == "platform-public")
    assert boundary["lifecycle"] == "contract-only"
    by_id = {operation["id"]: operation for operation in boundary["operations"]}
    assert set(MEDIA_ARTIFACT_OPERATIONS).issubset(by_id)
    assert by_id["submitMediaOperation"]["receipt"]["recoveryOperation"] == (
        "recoverMediaOperationCommand"
    )
    assert by_id["cancelMediaOperation"]["receipt"]["recoveryOperation"] == (
        "recoverMediaOperationCommand"
    )
    assert by_id["issueArtifactDeliveryAuthorization"]["retryClass"] == "never"
    assert by_id["recoverMediaOperationCommand"]["effect"] is False
