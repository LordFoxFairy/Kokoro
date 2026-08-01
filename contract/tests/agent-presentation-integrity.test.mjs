import { execFileSync } from "node:child_process";
import { strict as assert } from "node:assert";
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { test } from "node:test";

import { create, createFileRegistry, fromBinary, toBinary } from "@bufbuild/protobuf";
import { FileDescriptorSetSchema } from "@bufbuild/protobuf/wkt";

const descriptorBytes = execFileSync("./node_modules/.bin/buf", [
  "build", "proto", "--as-file-descriptor-set", "-o", "-",
], { cwd: new URL("..", import.meta.url), encoding: "buffer", maxBuffer: 8 * 1024 * 1024 });
const registry = createFileRegistry(fromBinary(FileDescriptorSetSchema, descriptorBytes));
const corpus = JSON.parse(readFileSync(new URL(
  "../corpus/agent-presentation-integrity-v1.json", import.meta.url,
), "utf8"));

function descriptor(name) {
  return registry.getMessage(`kokoro.agent.presentation.v1.${name}`);
}

function typedDigest(schema, value) {
  return `sha256:${createHash("sha256")
    .update(schema.typeName, "utf8")
    .update(Uint8Array.of(0))
    .update(toBinary(schema, value, { writeUnknownFields: false }))
    .digest("hex")}`;
}

test("cross-language presentation integrity golden vector is stable", () => {
  const fenceSchema = descriptor("PresentationProducerFenceDigestPayload");
  const fence = typedDigest(fenceSchema, create(fenceSchema, {
    producerInstanceRef: corpus.producer.producerInstanceRef,
    producerGeneration: BigInt(corpus.producer.producerGeneration),
  }));
  assert.equal(fence, corpus.producer.producerFenceDigest);
  const producer = {
    producerInstanceRef: corpus.producer.producerInstanceRef,
    producerGeneration: BigInt(corpus.producer.producerGeneration),
    producerFenceDigest: fence,
  };
  const genesisSchema = descriptor("PresentationRecordChainGenesisDigestPayload");
  assert.equal(typedDigest(genesisSchema, create(genesisSchema, {
    runId: corpus.runId,
    producer,
  })), corpus.genesisRecordDigest);
  const snapshotSchema = descriptor("PresentationSnapshotHeadDigestPayload");
  assert.equal(typedDigest(snapshotSchema, create(snapshotSchema, {
    runId: corpus.runId,
    producer,
    snapshotThroughPresentationSeq: 0n,
  })), corpus.emptySnapshotHeadDigest);
  assert.equal(
    `sha256:${createHash("sha256").update(corpus.canonicalCandidateEnvelopeJson).digest("hex")}`,
    corpus.canonicalCandidateDigest,
  );
});

test("delivery status digest binds the immutable stream, terminal evidence, and sealed head", () => {
  const producer = {
    producerInstanceRef: corpus.producer.producerInstanceRef,
    producerGeneration: BigInt(corpus.producer.producerGeneration),
    producerFenceDigest: corpus.producer.producerFenceDigest,
  };
  const sealSchema = descriptor("PresentationTerminalSeal");
  const payloadSchema = descriptor("PresentationDeliveryStatusDigestPayload");
  const seal = create(sealSchema, {
    sealedThroughPresentationSeq: BigInt(corpus.terminalStatus.sealedThroughPresentationSeq),
    sealedHeadRecordDigest: corpus.terminalStatus.sealedHeadRecordDigest,
    terminalEvidenceRef: corpus.terminalStatus.terminalEvidenceRef,
    terminalEvidencePayloadDigest: corpus.terminalStatus.terminalEvidencePayloadDigest,
    terminalDisposition: 1,
    sealedAt: { seconds: 1785589201n, nanos: 0 },
  });
  const payload = create(payloadSchema, {
    runId: corpus.runId,
    producer,
    acknowledgedThroughPresentationSeq: 2n,
    acknowledgedHeadRecordDigest: corpus.terminalStatus.sealedHeadRecordDigest,
    statusRevision: 3n,
    updatedAt: { seconds: 1785589201n, nanos: 0 },
    terminalSeal: seal,
  });
  assert.equal(typedDigest(payloadSchema, payload), corpus.terminalStatus.statusDigest);
});
