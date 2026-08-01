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
const pageDescriptor = registry.getMessage(
  "kokoro.agent.presentation.v1.PullCandidateBatchesResponse",
);
const acknowledgementDescriptor = registry.getMessage(
  "kokoro.agent.presentation.v1.AcknowledgeCandidateAdmissionsEffect",
);
const validator = createValidator({ registry });

const digest = (character) => `sha256:${character.repeat(64)}`;
const candidate = (character) => `agui_candidate:sha256:${character.repeat(64)}`;
const producer = {
  producerInstanceRef: "agent-instance-1",
  producerGeneration: 7n,
  producerFenceDigest: digest("f"),
};
const timestamp = { seconds: 1n, nanos: 0 };

function record(sequence, previousRecordDigest, recordDigest, producerFence = producer) {
  return {
    presentationRef: `presentation-${sequence}`,
    previousPresentationSeq: BigInt(sequence - 1),
    presentationSeq: BigInt(sequence),
    envelopeBytes: Uint8Array.of(sequence),
    envelopeDigest: digest("e"),
    candidateRef: candidate(String(sequence)),
    candidateDigest: digest(String(sequence)),
    recordedAt: timestamp,
    producer: producerFence,
    previousRecordDigest,
    recordDigest,
  };
}

const recordOne = record(1, digest("0"), digest("1"));
const recordTwo = record(2, recordOne.recordDigest, digest("2"));
const recordThree = record(3, recordTwo.recordDigest, digest("3"));

function deliveryStatus(overrides = {}) {
  return {
    runId: "agent-run-1",
    producer,
    acknowledgedThroughPresentationSeq: 0n,
    statusRevision: 1n,
    updatedAt: timestamp,
    statusDigest: digest("a"),
    ...overrides,
  };
}

function validatePage(overrides = {}) {
  const value = {
    runId: "agent-run-1",
    producer,
    pageAfterPresentationSeq: 0n,
    snapshotThroughPresentationSeq: 2n,
    records: [recordOne, recordTwo],
    hasMore: false,
    deliveryStatus: deliveryStatus(),
    snapshotHeadDigest: digest("b"),
    ...overrides,
  };
  return validator.validate(pageDescriptor, create(pageDescriptor, value));
}

function receipt(recordValue) {
  return {
    previousPresentationSeq: recordValue.previousPresentationSeq,
    presentationSeq: recordValue.presentationSeq,
    presentationRef: recordValue.presentationRef,
    recordDigest: recordValue.recordDigest,
    candidateRef: recordValue.candidateRef,
    candidateDigest: recordValue.candidateDigest,
    sessionAdmissionReceiptRef: `session-receipt-${recordValue.presentationSeq}`,
    sessionEffectDigest: digest("d"),
  };
}

function validateAcknowledgement(receipts) {
  const value = {
    runId: "agent-run-1",
    producer,
    expectedAcknowledgedThrough: 0n,
    expectedStatusRevision: 1n,
    idempotencyRef: "presentation-ack-1",
    receipts,
    effectDigestDomain: "kokoro.agent.presentation.ack.v1",
    effectDigest: digest("c"),
  };
  return validator.validate(
    acknowledgementDescriptor,
    create(acknowledgementDescriptor, value),
  );
}

test("presentation pull accepts one exact frozen contiguous page", () => {
  assert.equal(validatePage().kind, "valid");
  assert.equal(validatePage({
    pageAfterPresentationSeq: 2n,
    snapshotThroughPresentationSeq: 2n,
    records: [],
  }).kind, "valid");
});

test("presentation pull rejects gaps, reordered records and producer drift", () => {
  const driftedProducer = { ...producer, producerGeneration: 8n };
  for (const invalid of [
    { records: [recordOne, recordThree], snapshotThroughPresentationSeq: 3n },
    { records: [recordOne, recordThree, recordTwo], snapshotThroughPresentationSeq: 3n },
    { records: [recordOne, { ...recordTwo, producer: driftedProducer }] },
    { deliveryStatus: deliveryStatus({ runId: "agent-run-other" }) },
    { pageAfterPresentationSeq: 3n, snapshotThroughPresentationSeq: 2n, records: [] },
    { snapshotThroughPresentationSeq: 2n, records: [] },
    { snapshotThroughPresentationSeq: 3n, records: [recordOne, recordTwo], hasMore: false },
  ]) assert.equal(validatePage(invalid).kind, "invalid");
});

test("presentation acknowledgement accepts only the exact ordered stored-record identity chain", () => {
  assert.equal(validateAcknowledgement([receipt(recordOne), receipt(recordTwo)]).kind, "valid");
  for (const invalid of [
    [receipt(recordOne), receipt(recordThree)],
    [receipt(recordOne), receipt(recordThree), receipt(recordTwo)],
    [receipt(recordOne), { ...receipt(recordTwo), recordDigest: recordOne.recordDigest }],
  ]) assert.equal(validateAcknowledgement(invalid).kind, "invalid");
});
