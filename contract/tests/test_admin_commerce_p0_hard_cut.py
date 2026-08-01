import re
from pathlib import Path


CONTRACT = Path(__file__).resolve().parents[1]
COMMERCE_DIR = CONTRACT / "proto/kokoro/platform/commerce/v1"
FULFILLMENT = CONTRACT / "proto/kokoro/platform/commerce/v1/fulfillment.proto"
CREDIT = CONTRACT / "proto/kokoro/platform/credit/v1/admin_credit.proto"


def _source(path: Path) -> str:
    return path.read_text()


def _commerce_source() -> str:
    return "\n".join(path.read_text() for path in sorted(COMMERCE_DIR.glob("*.proto")))


def _body(source: str, kind: str, name: str) -> str:
    match = re.search(rf"{kind} {name} \{{(?P<body>.*?)\n\}}", source, re.DOTALL)
    assert match is not None, name
    return match.group("body")


def test_approval_authority_is_server_owned_and_decisions_are_reference_only() -> None:
    source = _commerce_source()

    assert "CommerceApprovalAnchor" not in source
    authority = _body(source, "message", "CommerceApprovalRequestFact")
    for field in (
        "site_id",
        "operation",
        "typed_effect_digest",
        "targets",
        "maker_actor_ref",
        "authority_epochs_digest",
        "expires_at",
        "request_command",
    ):
        assert field in authority
    decision = _body(source, "message", "CommerceApprovalDecisionEffect")
    assert "approval_ref" in decision
    assert "expected_approval_version" in decision
    assert "decision" in decision
    for forbidden in ("requested_by_actor_ref", "approved_by_actor_ref", "effect_digest", "target_ref"):
        assert forbidden not in decision


def test_only_inert_catalog_publication_is_synchronous() -> None:
    source = _commerce_source()

    for view in (
        "PlanRevisionView",
        "OfferRevisionView",
        "OfferPriceRevisionView",
        "FulfillmentProgramRevisionView",
        "RedemptionProgramRevisionView",
    ):
        body = _body(source, "message", view)
        assert "site_id" not in body
        assert "CATALOG_CANDIDATE_EXPOSURE_INERT" in body
    service = _body(source, "service", "AdminCommerceService")
    for method in (
        "RequestSiteCommerceAssignmentPromotion",
        "DecideSiteCommerceAssignmentPromotion",
        "RequestCodeBatchIssuance",
        "DecideCodeBatchIssuance",
        "RequestCodeBatchTransition",
        "DecideCodeBatchTransition",
        "RequestSourceCorrection",
        "DecideSourceCorrection",
        "RequestCommerceReconciliationResolution",
        "DecideCommerceReconciliationResolution",
    ):
        assert f"rpc {method}(" in service
    assert "Execute" not in service


def test_offer_price_is_an_immutable_money_and_cadence_authority() -> None:
    source = _commerce_source()
    money = _body(source, "message", "CommerceMoney")
    assert 'pattern: "^[A-Z]{3}$"' in money
    assert "int64 amount_minor" in money
    assert ".int64.gte = 0" in money
    cadence = _body(source, "message", "CommerceBillingCadence")
    assert "one-time prices have no interval" in cadence
    assert "this.kind == 2" in cadence
    price = _body(source, "message", "OfferPriceRevisionView")
    for field in ("offer_revision", "money", "tax_mode", "billing_cadence"):
        assert field in price
    publish = _body(source, "message", "PublishOfferPriceRevisionEffect")
    assert "this.target.target_revision == this.expected_version + 1u" in publish
    assert "CommerceRevisionTarget offer_revision" in publish


def test_fulfillment_output_owner_is_typed_and_total_cardinality_is_bounded() -> None:
    source = _commerce_source()
    line = _body(source, "message", "FulfillmentProgramOutputLine")

    assert "oneof owner" in line
    assert "SubscriptionTermPolicyRevisionBinding" in line
    assert "EntitlementTemplateRevisionBinding" in line
    assert "CreditProgramRevisionBinding" in line
    publish = _body(source, "message", "PublishFulfillmentProgramRevisionEffect")
    assert "occurrence_count" in publish
    assert "<= 32u" in publish


def test_secret_delivery_is_resumable_and_activation_requires_disposal_evidence() -> None:
    source = _commerce_source()

    assert "message EncryptedCodeDelivery" not in source
    assert "bytes ciphertext" not in source
    for message in (
        "EncryptedCodeArtifact",
        "SecretDeliverySessionView",
        "ReadCodeDeliveryRangeRequest",
        "AcknowledgeCodeDeliveryRangeRequest",
        "SecretDeliveryDisposalReceipt",
        "CodeBatchActivationEvidence",
    ):
        assert f"message {message}" in source
    activation = _body(source, "message", "ActivateCodeBatchExecution")
    assert "CodeBatchActivationEvidence" in activation
    assert "delivered_session" in _body(source, "message", "CodeBatchActivationEvidence")
    assert "disposal_receipt" in _body(source, "message", "CodeBatchActivationEvidence")
    assert "delivered_session.state == 4" in source
    assert "disposal_receipt.artifact_ref == this.delivered_session.artifact.artifact_ref" in source


def test_all_mutation_effects_have_a_generated_provider_verifier() -> None:
    source = _commerce_source()
    generator = (CONTRACT / "generate.mjs").read_text()

    assert "command_envelope_request_digest_mismatch" in generator
    assert "verifyPublishPlanRevisionCommand" in generator
    assert "verifyRequestCodeBatchIssuanceCommand" in generator
    assert "verifyReadCodeDeliveryRangeCommand" in generator
    assert "message CommerceGlobalCommandContext" in source
    assert "global catalog mutation requires exact Global or BreakGlass authority" in source


def test_corrections_have_durable_execution_states_and_replace_names_transaction() -> None:
    source = _commerce_source()

    enum = _body(source, "enum", "CommerceExecutionState")
    for state in ("QUEUED", "APPLYING", "APPLIED", "FAILED", "OUTCOME_UNKNOWN"):
        assert f"COMMERCE_EXECUTION_STATE_{state}" in enum
    resolution = _body(source, "message", "ReplaceReconciliationResolution")
    assert "FulfillmentTransactionIdentity replacement" in resolution
    result = _body(source, "message", "SourceCorrectionExecutionResult")
    assert "FulfillmentReversalFact" in result
    assert "FulfillmentReplacementFact" in result


def test_credit_owner_has_typed_reconciliation_exit() -> None:
    source = _source(CREDIT)
    service = _body(source, "service", "AdminCreditService")
    for method in (
        "RequestCreditReconciliationResolution",
        "DecideCreditReconciliationResolution",
        "GetCreditReconciliationResolution",
    ):
        assert f"rpc {method}(" in service
    resolution = _body(source, "message", "CreditReconciliationResolution")
    for variant in (
        "ConfirmNoUsageAndRelease",
        "ConfirmUsageAndSettle",
        "RetryCreditCommit",
        "ApplyBalancedJournalCorrection",
        "QuarantineCreditAuthority",
    ):
        assert variant in resolution
    result = _body(source, "message", "CreditReconciliationExecutionResult")
    for field in ("before", "after"):
        assert field in result
    assert "CreditAuthoritySnapshot" in result
    journal = _body(source, "message", "CreditJournalAuthoritySnapshot")
    for field in ("journal_transaction_ref", "journal_transaction_digest"):
        assert field in journal
    assert "CreditTransactionSnapshot" not in source
    assert "platform_transaction_ref" not in source


def test_fulfillment_primary_fact_has_one_immutable_version() -> None:
    source = _source(FULFILLMENT)
    transaction = _body(source, "message", "CanonicalFulfillmentTransactionV1")
    assert "uint64 transaction_version = 7 [(buf.validate.field).uint64.const = 1]" in transaction
