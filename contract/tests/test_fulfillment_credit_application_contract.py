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

    canonical = _message_body(source, "CanonicalFulfillmentTransactionV1")
    assert "string site_ref" in canonical
    assert "namespace" not in canonical
    assert "FrozenAcquisitionSnapshot acquisition" in canonical
    assert "FrozenFulfillmentProgramSnapshot program" in canonical
    assert "FULFILLMENT_TRANSACTION_STATE_COMMITTED" in canonical
    assert "this.outputs.filter(n, n.output_ref == o.output_ref).size() == 1" in canonical
    assert "n.output_line_id == o.output_line_id && n.occurrence == o.occurrence" in canonical
    assert "n.output_line_id == o.output_line_id).all(n, n.output_ordinal == o.output_ordinal)" in canonical
    assert "n.output_ordinal == o.output_ordinal).all(n, n.output_line_id == o.output_line_id)" in canonical
    assert "o.occurrence <= uint(this.outputs.filter(n, n.output_line_id == o.output_line_id).size())" in canonical
    assert "n.kind == o.kind" in canonical
    assert "n.output_version == o.output_version" in canonical
    assert "n.output_digest == o.output_digest" in canonical
    assert "this.outputs[0].output_ordinal < this.outputs[1].output_ordinal" in canonical
    assert "this.outputs[30].output_ordinal < this.outputs[31].output_ordinal" in canonical
    assert "this.outputs[0].output_line_id == this.outputs[1].output_line_id" in canonical

    output = _message_body(source, "FulfillmentOutputCommitment")
    for field in ("output_line_id", "output_ordinal", "occurrence"):
        assert field in output
    assert 'pattern: "^[a-z0-9][a-z0-9._:-]{0,127}$"' in output
    assert "lte: 32" in output
    assert "lte: 65535" in output

    transaction = _message_body(source, "FulfillmentTransactionFact")
    assert "CanonicalFulfillmentTransactionV1 transaction" in transaction
    assert "string transaction_digest" in transaction
    assert "SHA-256" in source
    assert "deterministic known-field protobuf bytes" in source
    assert "outputs in strictly increasing (output_ordinal, occurrence) order" in source

    identity = _message_body(source, "FulfillmentTransactionIdentity")
    for field in ("platform_transaction_ref", "transaction_version", "transaction_digest"):
        assert field in identity

    for fact in (
        "FulfillmentReversalFact",
        "FulfillmentReplacementFact",
        "FulfillmentReconciliationFact",
    ):
        body = _message_body(source, fact)
        assert "string site_ref = 1" in body
        assert "FulfillmentTransactionIdentity original" in body
        assert "uint64 fact_version" in body
        assert "string fact_digest" in body
        assert "google.protobuf.Timestamp recorded_at" in body
    replacement = _message_body(source, "FulfillmentReplacementFact")
    assert "FulfillmentTransactionIdentity replacement" in replacement
    assert "this.original.platform_transaction_ref != this.replacement.platform_transaction_ref" in replacement


def test_agent_never_owns_or_calls_a_credit_lifecycle() -> None:
    registry = json.loads((CONTRACT / "registry/boundaries.yaml").read_text())
    assert not (CONTRACT / "proto/kokoro/platform/credit/v1/credit_application.proto").exists()
    assert "platform-credit-application" not in {item["id"] for item in registry["boundaries"]}
    agent_consumed = [
        item for item in registry["boundaries"]
        if any(consumer.get("repository") == "kokoro-agent" for consumer in item.get("consumers", []))
    ]
    assert all("credit" not in item["id"] for item in agent_consumed)
