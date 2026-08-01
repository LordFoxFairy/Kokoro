import json
import re
from pathlib import Path


CONTRACT = Path(__file__).resolve().parents[1]
PROTO = CONTRACT / "proto/kokoro/platform/commerce/v1/admin_commerce.proto"


def _source() -> str:
    return PROTO.read_text()


def _body(source: str, kind: str, name: str) -> str:
    match = re.search(rf"{kind} {name} \{{(?P<body>.*?)\n\}}", source, re.DOTALL)
    assert match is not None
    return match.group("body")


def _methods(source: str) -> list[str]:
    return re.findall(r"^\s*rpc (\w+)\(", _body(source, "service", "AdminCommerceService"), re.MULTILINE)


METHODS = [
    "PublishPlanRevision",
    "ListPlanRevisions",
    "GetPlanRevision",
    "PublishOfferRevision",
    "ListOfferRevisions",
    "GetOfferRevision",
    "PublishFulfillmentProgramRevision",
    "ListFulfillmentProgramRevisions",
    "GetFulfillmentProgramRevision",
    "PublishRedemptionProgramRevision",
    "ListRedemptionProgramRevisions",
    "GetRedemptionProgramRevision",
    "PublishSiteCommerceAssignment",
    "ListSiteCommerceAssignments",
    "GetSiteCommerceAssignment",
    "RequestCodeBatchIssuance",
    "ApproveCodeBatchIssuance",
    "ClaimCodeBatchDelivery",
    "ListCodeBatches",
    "GetCodeBatch",
    "ActivateCodeBatch",
    "SuspendCodeBatch",
    "ResumeCodeBatch",
    "RevokeCodeBatch",
    "RequestSourceReversal",
    "ApproveSourceReversal",
    "RequestCodeReplacement",
    "ApproveCodeReplacement",
    "ListSourceCorrections",
    "GetSourceCorrection",
    "ListCommerceReconciliations",
    "GetCommerceReconciliation",
    "ResolveCommerceReconciliation",
    "GetCommerceCommandReceipt",
]


def test_admin_commerce_has_one_closed_owner_aligned_surface() -> None:
    source = _source()

    assert _methods(source) == METHODS
    for removed in (
        "CreditProgram",
        "EntitlementTemplate",
        "PublishOffer(",
        "IssueCodeBatch",
        "AbandonCodeBatch",
    ):
        assert removed not in source
    assert "google.protobuf.Struct" not in source
    assert "message GenericAction" not in source
    assert "payment" not in source.lower()


def test_catalog_revisions_are_immutable_and_product_is_an_exact_foreign_binding() -> None:
    source = _source()

    target = _body(source, "message", "CommerceRevisionTarget")
    for field in ("target_ref", "target_revision", "target_digest"):
        assert field in target
    for operation in (
        "PublishPlanRevision",
        "PublishOfferRevision",
        "PublishFulfillmentProgramRevision",
        "PublishRedemptionProgramRevision",
        "PublishSiteCommerceAssignment",
    ):
        effect = _body(source, "message", f"{operation}Effect")
        request = _body(source, "message", f"{operation}Request")
        response = _body(source, "message", f"{operation}Response")
        assert "CommerceRevisionTarget target" in effect
        assert "uint64 expected_version" in effect
        assert "string command_digest" in effect
        assert "AuthenticatedOperatorCommandContext context" in request
        assert "this.context.command.request_digest == this.effect.command_digest" in request
        assert "CommandReceiptV2 receipt" in response
        assert f"this.receipt.operation == '{operation}'" in response
    offer = _body(source, "message", "PublishOfferRevisionEffect")
    assert "ImmutableContractRevisionBinding product_catalog_revision" in offer


def test_code_batch_is_maker_checker_and_has_requester_only_one_time_delivery() -> None:
    source = _source()

    assert re.findall(r"^\s*(CODE_BATCH_STATE_[A-Z_]+)\s*=", _body(source, "enum", "CodeBatchState"), re.MULTILINE) == [
        "CODE_BATCH_STATE_UNSPECIFIED",
        "CODE_BATCH_STATE_REQUESTED",
        "CODE_BATCH_STATE_APPROVED",
        "CODE_BATCH_STATE_ACTIVE",
        "CODE_BATCH_STATE_SUSPENDED",
        "CODE_BATCH_STATE_REVOKED",
    ]
    assert re.findall(r"^\s*(CODE_DELIVERY_STATE_[A-Z_]+)\s*=", _body(source, "enum", "CodeDeliveryState"), re.MULTILINE) == [
        "CODE_DELIVERY_STATE_UNSPECIFIED",
        "CODE_DELIVERY_STATE_PENDING_APPROVAL",
        "CODE_DELIVERY_STATE_AVAILABLE",
        "CODE_DELIVERY_STATE_CLAIMED",
    ]
    approval = _body(source, "message", "CommerceApprovalAnchor")
    assert "requested_by_actor_ref" in approval
    assert "approved_by_actor_ref" in approval
    assert "this.requested_by_actor_ref != this.approved_by_actor_ref" in approval
    delivery = _body(source, "message", "EncryptedCodeDelivery")
    for field in ("ciphertext", "encryption_algorithm", "key_revision_ref", "audience", "expires_at", "plaintext_digest"):
        assert field in delivery
    assert "raw_codes" not in source
    specification = _body(source, "message", "CodeBatchSpecification")
    assert "uint(this.code_count) * (uint(this.code_length) + 8u) <= 1048576u" in specification
    assert "max_len: 2097152" in delivery
    assert "max_len: 67108864" not in delivery
    assert "EncryptedCodeDelivery" not in _body(source, "message", "RequestCodeBatchIssuanceResponse")
    approve = _body(source, "message", "ApproveCodeBatchIssuanceResponse")
    assert "SealedCodeDeliveryReceipt delivery_receipt" in approve
    assert "EncryptedCodeDelivery" not in approve
    claim_request = _body(source, "message", "ClaimCodeBatchDeliveryRequest")
    assert "this.context.actor_ref == this.effect.requester_actor_ref" in claim_request
    claim_response = _body(source, "message", "ClaimCodeBatchDeliveryResponse")
    assert "optional EncryptedCodeDelivery delivery" in claim_response
    assert "this.replayed" in claim_response
    assert "!has(this.delivery)" in claim_response
    assert "has(this.delivery)" in claim_response
    state_by_response = {
        "RequestCodeBatchIssuanceResponse": "CODE_BATCH_STATE_REQUESTED",
        "ApproveCodeBatchIssuanceResponse": "CODE_BATCH_STATE_APPROVED",
        "ClaimCodeBatchDeliveryResponse": "CODE_BATCH_STATE_APPROVED",
        "ActivateCodeBatchResponse": "CODE_BATCH_STATE_ACTIVE",
        "SuspendCodeBatchResponse": "CODE_BATCH_STATE_SUSPENDED",
        "ResumeCodeBatchResponse": "CODE_BATCH_STATE_ACTIVE",
        "RevokeCodeBatchResponse": "CODE_BATCH_STATE_REVOKED",
    }
    for response, state in state_by_response.items():
        body = _body(source, "message", response)
        assert state in body
        assert f"this.receipt.operation == '{response.removesuffix('Response')}'" in body
    for response in ("ListCodeBatchesResponse", "GetCodeBatchResponse", "GetCommerceCommandReceiptResponse"):
        assert "EncryptedCodeDelivery" not in _body(source, "message", response)


def test_corrections_bind_exact_targets_approval_reason_and_evidence() -> None:
    source = _source()

    for operation in (
        "ApproveSourceReversal",
        "ApproveCodeReplacement",
        "ResolveCommerceReconciliation",
        "ActivateCodeBatch",
        "SuspendCodeBatch",
        "ResumeCodeBatch",
        "RevokeCodeBatch",
    ):
        effect = _body(source, "message", f"{operation}Effect")
        assert "CommerceRevisionTarget target" in effect
        assert "uint64 expected_version" in effect
        assert "string command_digest" in effect
        assert "CommerceApprovalAnchor approval" in effect
        assert "string reason" in effect
        assert "string evidence_ref" in effect
        assert "string evidence_digest" in effect
        request = _body(source, "message", f"{operation}Request")
        assert "this.context.actor_ref == this.effect.approval.approved_by_actor_ref" in request
        response = _body(source, "message", f"{operation}Response")
        assert f"this.receipt.operation == '{operation}'" in response

    assert "SOURCE_CORRECTION_STATE_REQUESTED" in _body(source, "message", "RequestSourceReversalResponse")
    assert "SOURCE_CORRECTION_STATE_APPROVED" in _body(source, "message", "ApproveSourceReversalResponse")
    assert "SOURCE_CORRECTION_STATE_REQUESTED" in _body(source, "message", "RequestCodeReplacementResponse")
    assert "SOURCE_CORRECTION_STATE_APPROVED" in _body(source, "message", "ApproveCodeReplacementResponse")
    assert "COMMERCE_RECONCILIATION_STATE_RESOLVED" in _body(source, "message", "ResolveCommerceReconciliationResponse")


def test_registry_matches_the_closed_admin_commerce_rpc_surface() -> None:
    registry = json.loads((CONTRACT / "registry/boundaries.yaml").read_text())
    commerce = next(boundary for boundary in registry["boundaries"] if boundary["id"] == "platform-admin-commerce")

    assert [operation["id"] for operation in commerce["operations"]] == METHODS
    assert commerce["provider"] == {"boundary": "service.platform", "repository": "kokoro-platform"}
    assert commerce["consumers"] == [{"boundary": "web.admin", "repository": "kokoro-web"}]
    assert all(operation["scope"] == "site" for operation in commerce["operations"])
    assert all(operation["siteBinding"] == "request-field" for operation in commerce["operations"])
