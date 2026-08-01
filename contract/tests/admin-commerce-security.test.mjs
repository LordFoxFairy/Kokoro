import { execFileSync } from "node:child_process";
import { strict as assert } from "node:assert";
import { test } from "node:test";

import { create, createFileRegistry, fromBinary } from "@bufbuild/protobuf";
import { FileDescriptorSetSchema } from "@bufbuild/protobuf/wkt";
import { createValidator } from "@bufbuild/protovalidate";

const descriptorBytes = execFileSync("./node_modules/.bin/buf", [
  "build",
  "proto",
  "--as-file-descriptor-set",
  "-o",
  "-",
], { cwd: new URL("..", import.meta.url), encoding: "buffer", maxBuffer: 8 * 1024 * 1024 });
const registry = createFileRegistry(fromBinary(FileDescriptorSetSchema, descriptorBytes));
const validator = createValidator({ registry });
const digest = "a".repeat(64);
const timestamp = { seconds: 1n, nanos: 0 };

function validate(typeName, value) {
  const descriptor = registry.getMessage(typeName);
  return validator.validate(descriptor, create(descriptor, value));
}

test("maker-checker approval rejects one actor in both roles", () => {
  const base = {
    approvalRef: "approval-1",
    approvalDigest: digest,
    requestCommandRef: "command-1",
    requestCommandDigest: digest,
  };
  assert.equal(validate("kokoro.platform.commerce.v1.CommerceApprovalAnchor", {
    ...base,
    requestedByActorRef: "maker",
    approvedByActorRef: "checker",
  }).kind, "valid");
  assert.equal(validate("kokoro.platform.commerce.v1.CommerceApprovalAnchor", {
    ...base,
    requestedByActorRef: "same-actor",
    approvedByActorRef: "same-actor",
  }).kind, "invalid");
});

const transaction = { targetRef: "batch-1", targetRevision: 1n, targetDigest: digest };
const batch = {
  siteId: "site-1",
  batch: transaction,
  redemptionProgramRevision: { targetRef: "redemption-1", targetRevision: 1n, targetDigest: digest },
  codeCount: 10,
  codeFingerprint: digest,
  state: 2,
  deliveryState: 3,
  deliveryVersion: 2n,
  updatedAt: timestamp,
};
const receipt = {
  identity: {
    commandId: "command-1",
    idempotencyKey: "idempotency-1",
    digestAlgorithm: 1,
    requestDigest: digest,
  },
  operation: "ClaimCodeBatchDelivery",
  state: 2,
  recordedAt: timestamp,
};
const delivery = {
  deliveryRef: "delivery-1",
  ciphertext: new Uint8Array(32),
  encryptionAlgorithm: "sealed-box-v1",
  keyRevisionRef: "key-1",
  audience: "operator:maker",
  expiresAt: timestamp,
  plaintextDigest: digest,
};

test("one-time delivery returns ciphertext once and strips it from replay", () => {
  const type = "kokoro.platform.commerce.v1.ClaimCodeBatchDeliveryResponse";
  const base = { receipt, batch, deliveryState: 3, deliveryVersion: 2n };

  assert.equal(validate(type, { ...base, replayed: false, delivery }).kind, "valid");
  assert.equal(validate(type, { ...base, replayed: true }).kind, "valid");
  assert.equal(validate(type, { ...base, replayed: false }).kind, "invalid");
  assert.equal(validate(type, { ...base, replayed: true, delivery }).kind, "invalid");
});

test("code batch delivery budget closes unary transport capacity", () => {
  const type = "kokoro.platform.commerce.v1.CodeBatchSpecification";
  const base = {
    redemptionProgramRevision: transaction,
    requesterActorRef: "maker",
    deliveryRecipientRef: "operator:maker",
    deliveryKeyRevisionRef: "key-1",
    deliveryKeyDigest: digest,
  };

  assert.equal(validate(type, { ...base, codeCount: 43690, codeLength: 16 }).kind, "valid");
  assert.equal(validate(type, { ...base, codeCount: 43691, codeLength: 16 }).kind, "invalid");
  assert.equal(validate(type, { ...base, codeCount: 1_000_000, codeLength: 128 }).kind, "invalid");

  const deliveryType = "kokoro.platform.commerce.v1.EncryptedCodeDelivery";
  assert.equal(validate(deliveryType, {
    ...delivery,
    ciphertext: new Uint8Array(2 * 1024 * 1024),
  }).kind, "valid");
  assert.equal(validate(deliveryType, {
    ...delivery,
    ciphertext: new Uint8Array(2 * 1024 * 1024 + 1),
  }).kind, "invalid");
});

test("immutable Commerce revisions are contiguous and ordered collections are canonical", () => {
  const planType = "kokoro.platform.commerce.v1.PublishPlanRevisionEffect";
  const plan = {
    target: transaction,
    expectedVersion: 0n,
    commandDigest: digest,
    definition: {
      planKey: "plan.standard",
      acquisitionKind: 2,
      termAction: 1,
      termSeconds: 0n,
      displayLabel: "Standard",
    },
    reason: "publish standard plan",
  };
  assert.equal(validate(planType, plan).kind, "valid");
  assert.equal(validate(planType, {
    ...plan,
    target: { ...transaction, targetRevision: 2n },
  }).kind, "invalid");
  assert.equal(validate(planType, {
    ...plan,
    definition: { ...plan.definition, termSeconds: 1n },
  }).kind, "invalid");

  const fulfillmentType = "kokoro.platform.commerce.v1.PublishFulfillmentProgramRevisionEffect";
  const line = (outputLineId, outputOrdinal) => ({
    outputLineId,
    outputOrdinal,
    occurrenceCount: 1,
    kind: 3,
    ownerRevision: transaction,
  });
  const fulfillment = {
    target: transaction,
    expectedVersion: 0n,
    commandDigest: digest,
    outputLines: [line("credit.primary", 1), line("credit.bonus", 2)],
    reason: "publish fulfillment program",
  };
  assert.equal(validate(fulfillmentType, fulfillment).kind, "valid");
  assert.equal(validate(fulfillmentType, {
    ...fulfillment,
    outputLines: [line("credit.primary", 1), line("credit.bonus", 3)],
  }).kind, "invalid");

  const assignmentType = "kokoro.platform.commerce.v1.PublishSiteCommerceAssignmentEffect";
  const assignment = {
    target: transaction,
    expectedVersion: 0n,
    commandDigest: digest,
    offerRevisions: [transaction],
    redemptionProgramRevisions: [],
    reason: "publish Site commerce assignment",
  };
  assert.equal(validate(assignmentType, assignment).kind, "valid");
  assert.equal(validate(assignmentType, {
    ...assignment,
    offerRevisions: [transaction, { ...transaction, targetRevision: 2n }],
  }).kind, "invalid");
});

test("correction and reconciliation views cannot express mismatched kinds or terminal shape", () => {
  const original = {
    platformTransactionRef: "fulfillment-1",
    transactionVersion: 1n,
    transactionDigest: digest,
  };
  const correctionType = "kokoro.platform.commerce.v1.SourceCorrectionView";
  const correction = {
    siteId: "site-1",
    correction: transaction,
    kind: 1,
    state: 1,
    original,
    updatedAt: timestamp,
  };
  assert.equal(validate(correctionType, correction).kind, "valid");
  assert.equal(validate(correctionType, { ...correction, replacementBatch: transaction }).kind, "invalid");
  assert.equal(validate(correctionType, { ...correction, kind: 2 }).kind, "invalid");
  assert.equal(validate(correctionType, {
    ...correction,
    kind: 2,
    replacementBatch: transaction,
  }).kind, "valid");

  const reconciliationType = "kokoro.platform.commerce.v1.CommerceReconciliationView";
  const reconciliation = {
    siteId: "site-1",
    reconciliation: transaction,
    original,
    state: 1,
    updatedAt: timestamp,
  };
  assert.equal(validate(reconciliationType, reconciliation).kind, "valid");
  assert.equal(validate(reconciliationType, { ...reconciliation, resolution: 1 }).kind, "invalid");
  assert.equal(validate(reconciliationType, {
    ...reconciliation,
    state: 2,
    resolution: 1,
  }).kind, "valid");
});

test("claimed delivery response binds the nested batch authority", () => {
  const type = "kokoro.platform.commerce.v1.ClaimCodeBatchDeliveryResponse";
  const base = {
    receipt,
    batch,
    deliveryState: 3,
    deliveryVersion: 2n,
    replayed: false,
    delivery,
  };
  assert.equal(validate(type, base).kind, "valid");
  assert.equal(validate(type, {
    ...base,
    batch: { ...batch, deliveryVersion: 3n },
  }).kind, "invalid");
  assert.equal(validate(type, {
    ...base,
    batch: { ...batch, deliveryState: 2 },
  }).kind, "invalid");
});

test("every commerce mutation response has a compilable closed-state validator", () => {
  const mutationResponses = [
    "PublishPlanRevisionResponse",
    "PublishOfferRevisionResponse",
    "PublishFulfillmentProgramRevisionResponse",
    "PublishRedemptionProgramRevisionResponse",
    "PublishSiteCommerceAssignmentResponse",
    "RequestCodeBatchIssuanceResponse",
    "ApproveCodeBatchIssuanceResponse",
    "ClaimCodeBatchDeliveryResponse",
    "ActivateCodeBatchResponse",
    "SuspendCodeBatchResponse",
    "ResumeCodeBatchResponse",
    "RevokeCodeBatchResponse",
    "RequestSourceReversalResponse",
    "ApproveSourceReversalResponse",
    "RequestCodeReplacementResponse",
    "ApproveCodeReplacementResponse",
    "ResolveCommerceReconciliationResponse",
  ];

  for (const name of mutationResponses) {
    const result = validate(`kokoro.platform.commerce.v1.${name}`, {});
    assert.equal(result.kind, "invalid", name);
  }
});
