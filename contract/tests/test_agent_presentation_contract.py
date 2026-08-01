import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROTO = ROOT / "proto/kokoro/agent/presentation/v1/agent_presentation.proto"
GENERATOR = ROOT / "generate.mjs"


def _body(source: str, kind: str, name: str) -> str:
    found = re.search(rf"{kind} {name} \{{(?P<body>.*?)\n\}}", source, re.DOTALL)
    assert found is not None, name
    return found.group("body")


def test_agent_presentation_boundary_is_durable_contiguous_and_recoverable() -> None:
    source = PROTO.read_text()
    service = _body(source, "service", "AgentPresentationService")
    assert re.findall(r"rpc (\w+)\(", service) == [
        "PullCandidateBatches",
        "AcknowledgeCandidateAdmissions",
        "QuarantineCandidateAdmission",
        "GetDeliveryStatus",
    ]
    for token in (
        "producer_generation",
        "producer_fence_digest",
        "snapshot_through_presentation_seq",
        "previous_presentation_seq + 1u",
        "record_digest",
        "envelope_digest",
        "candidate_digest",
        "PresentationCandidateRecordDigestPayload",
        "PresentationSnapshotHeadDigestPayload",
        "PresentationDeliveryStatusDigestPayload",
        "PresentationTerminalSeal",
        "sealed_through_presentation_seq",
        "sealed_head_record_digest",
        "terminal_evidence_ref",
        "terminal_evidence_payload_digest",
        "acknowledged_head_record_digest",
        "expected_acknowledged_through",
        "expected_status_revision",
        "idempotency_ref",
        "original_command",
        "PRESENTATION_REJECTION_CLASS_PERMANENT",
        "PresentationTransientErrorDetail",
        "PresentationPermanentErrorDetail",
    ):
        assert token in source


def test_ack_and_quarantine_encode_first_gap_rules() -> None:
    source = PROTO.read_text()
    ack = _body(source, "message", "AcknowledgeCandidateAdmissionsEffect")
    quarantine = _body(source, "message", "QuarantineCandidateAdmissionEffect")
    assert "receipts[0].previous_presentation_seq == this.expected_acknowledged_through" in ack
    assert ".map(r, r.previous_presentation_seq)" in ack
    assert ".map(r, r.presentation_seq)" in ack
    assert "n.record_digest == r.record_digest" in ack
    assert "this.presentation_seq == this.expected_acknowledged_through + 1u" in quarantine
    assert "does not advance" in source


def test_pull_page_closes_snapshot_chain_order_and_producer_identity() -> None:
    source = PROTO.read_text()
    page = _body(source, "message", "PullCandidateBatchesResponse")
    assert "page_after_presentation_seq <= this.snapshot_through_presentation_seq" in page
    assert "(this.records.size() == 0) == (this.page_after_presentation_seq == this.snapshot_through_presentation_seq)" in page
    assert ".map(r, r.previous_presentation_seq)" in page
    assert ".map(r, r.previous_record_digest)" in page
    assert "this.run_id == this.delivery_status.run_id" in page
    assert "this.records.all(r, r.producer == this.producer)" in page
    assert "this.has_more == (this.records[this.records.size() - 1].presentation_seq < this.snapshot_through_presentation_seq)" in page


def test_raw_agent_envelopes_remain_internal_and_never_become_web_contracts() -> None:
    source = PROTO.read_text()
    assert "bytes envelope_bytes" in source
    assert "internal-control" in source.lower()
    assert "browser" not in _body(source, "service", "AgentPresentationService").lower()


def test_ack_and_quarantine_share_one_root_generated_command_digest() -> None:
    source = GENERATOR.read_text()
    assert 'commandEnvelopeDigest: "agent-presentation"' in source
    assert "sealAcknowledgeCandidateAdmissionsEffect" in source
    assert "acknowledgeCandidateAdmissionsRequestDigest" in source
    assert "sealQuarantineCandidateAdmissionEffect" in source
    assert "quarantineCandidateAdmissionRequestDigest" in source
    assert "presentationProducerFenceDigest" in source
    assert "presentationCanonicalCandidateDigest" in source
    assert "presentationCandidateRecordDigest" in source
    assert "presentationSnapshotHeadDigest" in source
    assert "presentationDeliveryStatusDigest" in source


def test_terminal_seal_closes_the_exact_immutable_presentation_stream() -> None:
    source = PROTO.read_text()
    status = _body(source, "message", "PresentationDeliveryStatus")
    page = _body(source, "message", "PullCandidateBatchesResponse")
    seal = _body(source, "message", "PresentationTerminalSeal")
    assert "optional PresentationTerminalSeal terminal_seal" in status
    assert "sealed_through_presentation_seq" in seal
    assert "sealed_head_record_digest" in seal
    assert "terminal_evidence_ref" in seal
    assert "terminal_evidence_payload_digest" in seal
    assert "terminal_seal.sealed_through_presentation_seq" in page
    assert "terminal_seal.sealed_head_record_digest" in page
