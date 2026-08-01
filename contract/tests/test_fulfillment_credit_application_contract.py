import json
import re
from pathlib import Path


CONTRACT = Path(__file__).resolve().parents[1]


def _proto(path: str) -> str:
    return (CONTRACT / "proto" / path).read_text()


def _message_body(source: str, message: str) -> str:
    body = re.search(rf"message {message} \{{(?P<body>.*?)\n\}}", source, re.DOTALL)
    assert body is not None
    return body.group("body")


def _enum_members(source: str, enum: str) -> list[str]:
    body = re.search(rf"enum {enum} \{{(?P<body>.*?)\n\}}", source, re.DOTALL)
    assert body is not None
    return re.findall(r"^\s*([A-Z][A-Z0-9_]*)\s*=", body.group("body"), re.MULTILINE)


def test_fulfillment_records_one_committed_fact_and_separate_correction_facts() -> None:
    source = _proto("kokoro/platform/commerce/v1/fulfillment.proto")

    assert _enum_members(source, "FulfillmentAcquisitionSourceKind") == [
        "FULFILLMENT_ACQUISITION_SOURCE_KIND_UNSPECIFIED",
        "FULFILLMENT_ACQUISITION_SOURCE_KIND_REDEMPTION",
        "FULFILLMENT_ACQUISITION_SOURCE_KIND_FUTURE_PAYMENT_RESERVED",
        "FULFILLMENT_ACQUISITION_SOURCE_KIND_ADMIN_GRANT",
        "FULFILLMENT_ACQUISITION_SOURCE_KIND_PROGRAM_WINDOW",
    ]
    assert _enum_members(source, "FulfillmentTransactionState") == [
        "FULFILLMENT_TRANSACTION_STATE_UNSPECIFIED",
        "FULFILLMENT_TRANSACTION_STATE_COMMITTED",
    ]
    acquisition = _message_body(source, "FrozenAcquisitionSnapshot")
    for field in ("source_kind", "source_ref", "source_version", "source_digest"):
        assert field in acquisition
    for source_owned_detail in ("code", "amount", "currency", "invoice", "charge"):
        assert source_owned_detail not in acquisition.lower()

    transaction = _message_body(source, "FulfillmentTransactionFact")
    assert "string site_ref = 2" in transaction
    assert "namespace" not in transaction
    assert "FrozenAcquisitionSnapshot acquisition" in transaction
    assert "FrozenFulfillmentProgramSnapshot program" in transaction
    assert "FULFILLMENT_TRANSACTION_STATE_COMMITTED" in transaction
    assert "reversal" not in transaction.lower()
    assert "replacement" not in transaction.lower()

    for fact in (
        "FulfillmentReversalFact",
        "FulfillmentReplacementFact",
        "FulfillmentReconciliationFact",
    ):
        body = _message_body(source, fact)
        assert "uint64 fact_version" in body
        assert "string fact_digest" in body
        assert "google.protobuf.Timestamp recorded_at" in body


def test_credit_application_binds_every_transition_to_one_opaque_cas_identity() -> None:
    source = _proto("kokoro/platform/credit/v1/credit_application.proto")

    assert _enum_members(source, "CreditTransactionState") == [
        "CREDIT_TRANSACTION_STATE_UNSPECIFIED",
        "CREDIT_TRANSACTION_STATE_RESERVED",
        "CREDIT_TRANSACTION_STATE_COMMITTED",
        "CREDIT_TRANSACTION_STATE_SETTLED",
        "CREDIT_TRANSACTION_STATE_RELEASED",
        "CREDIT_TRANSACTION_STATE_RECONCILIATION_REQUIRED",
    ]
    for operation in (
        "ReserveCredit",
        "CommitCreditReservation",
        "SettleCreditReservation",
        "ReleaseCreditReservation",
    ):
        request = _message_body(source, f"{operation}Request")
        effect = _message_body(source, f"{operation}Effect")
        response = _message_body(source, f"{operation}Response")
        assert "kokoro.common.v2.CommandIdentityV2 command = 1" in request
        assert "string namespace = 2" in request
        assert f"{operation}Effect effect = 3" in request
        assert "this.command.request_digest == this.effect.command_digest" in request
        assert "string platform_transaction_ref = 1" in effect
        assert "uint64 expected_version = 2" in effect
        assert "string command_digest = 3" in effect
        assert "kokoro.common.v2.CommandReceiptV2 receipt = 1" in response
        assert "optional CreditTransactionSnapshot transaction = 2" in response
        assert "COMMAND_RECEIPT_STATE_V2_ACCEPTED" not in response
        assert "COMMAND_RECEIPT_STATE_V2_COMMITTED" in response
        assert "COMMAND_RECEIPT_STATE_V2_REJECTED" in response
        assert "COMMAND_RECEIPT_STATE_V2_OUTCOME_UNKNOWN" in response
        assert "!has(this.transaction)" in response

    expected_states = {
        "ReserveCreditResponse": "CREDIT_TRANSACTION_STATE_RESERVED",
        "CommitCreditReservationResponse": "CREDIT_TRANSACTION_STATE_COMMITTED",
        "SettleCreditReservationResponse": "CREDIT_TRANSACTION_STATE_SETTLED",
        "ReleaseCreditReservationResponse": "CREDIT_TRANSACTION_STATE_RELEASED",
    }
    for response, state in expected_states.items():
        assert state in _message_body(source, response)

    lookup = _message_body(source, "GetCreditCommandReceiptRequest")
    for field in ("namespace", "command_id", "idempotency_key", "digest_algorithm", "request_digest"):
        assert field in lookup
    assert "site_id" not in source
    assert "user_id" not in source
    assert "amount" not in source.lower()
    assert "unit" not in source.lower()
    recovery = _message_body(source, "GetCreditCommandReceiptResponse")
    assert "COMMAND_RECEIPT_STATE_V2_ACCEPTED" not in recovery
    for state in expected_states.values():
        assert state in recovery


def test_registry_freezes_owner_consumer_recovery_and_namespace_scope() -> None:
    registry = json.loads((CONTRACT / "registry/boundaries.yaml").read_text())
    boundaries = {item["id"]: item for item in registry["boundaries"]}
    credit = boundaries["platform-credit-application"]

    assert credit["provider"] == {"boundary": "service.platform", "repository": "kokoro-platform"}
    assert credit["consumers"] == [{"boundary": "service.agent", "repository": "kokoro-agent"}]
    assert credit["lifecycle"] == "contract-only"
    assert credit["scope"] == "namespace"
    assert credit["trustPlane"] == "internal-control"
    assert credit["sources"] == [
        {
            "kind": "proto",
            "path": "contract/proto/kokoro/platform/credit/v1/credit_application.proto",
            "select": {"service": "CreditApplicationService"},
        }
    ]
    for operation in credit["operations"][:4]:
        assert operation["retryClass"] == "reconcile_receipt"
        assert operation["receipt"] == {
            "kind": "command-receipt",
            "recoveryOperation": "GetCreditCommandReceipt",
            "ref": "kokoro.common.v2.CommandReceiptV2",
        }
        assert operation["scope"] == "namespace"
        assert operation["siteBinding"] == "not-applicable"
