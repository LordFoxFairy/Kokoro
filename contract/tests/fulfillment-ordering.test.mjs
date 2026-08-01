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
], { cwd: new URL("..", import.meta.url), encoding: "buffer" });
const registry = createFileRegistry(fromBinary(FileDescriptorSetSchema, descriptorBytes));
const descriptor = registry.getMessage("kokoro.platform.commerce.v1.CanonicalFulfillmentTransactionV1");
const validator = createValidator({ registry });
const digest = "a".repeat(64);
const timestamp = { seconds: 1n, nanos: 0 };
const base = {
  platformTransactionRef: "transaction-1",
  siteRef: "site-1",
  acquisition: {
    sourceKind: 1,
    sourceRef: "source-1",
    sourceVersion: 1n,
    sourceDigest: digest,
    acquiredAt: timestamp,
  },
  program: {
    fulfillmentProgramRevisionRef: "program-1",
    fulfillmentProgramRevision: 1n,
    fulfillmentProgramDigest: digest,
  },
  state: 1,
  transactionVersion: 1n,
  committedAt: timestamp,
};

function output(line, ordinal, occurrence, ref) {
  return {
    kind: 1,
    outputLineId: line,
    outputOrdinal: ordinal,
    occurrence,
    outputRef: ref,
    outputVersion: 1n,
    outputDigest: digest,
  };
}

function validate(outputs) {
  return validator.validate(descriptor, create(descriptor, { ...base, outputs }));
}

test("accepts the exact canonical line and occurrence order", () => {
  assert.equal(validate([
    output("line-a", 1, 1, "output-a1"),
    output("line-a", 1, 2, "output-a2"),
    output("line-b", 2, 1, "output-b1"),
  ]).kind, "valid");
});

test("rejects ordering, line drift, cardinality gaps, and duplicate receipts", () => {
  const invalid = [
    [output("line-b", 2, 1, "output-b1"), output("line-a", 1, 1, "output-a1")],
    [output("line-a", 1, 1, "output-a1"), output("line-b", 1, 2, "output-b1")],
    [output("line-a", 1, 2, "output-a2")],
    [output("line-a", 1, 1, "same-ref"), output("line-a", 1, 2, "same-ref")],
    [output("line-a", 1, 1, "output-a1"), output("line-a", 2, 2, "output-a2")],
  ];
  for (const outputs of invalid) assert.equal(validate(outputs).kind, "invalid");
});

test("enforces the canonical order through the thirty-two item bound", () => {
  const maximum = Array.from(
    { length: 32 },
    (_, index) => output(`line-${index + 1}`, index + 1, 1, `output-${index + 1}`),
  );
  assert.equal(validate(maximum).kind, "valid");
  const tailInversion = maximum.slice();
  [tailInversion[30], tailInversion[31]] = [tailInversion[31], tailInversion[30]];
  assert.equal(validate(tailInversion).kind, "invalid");
  assert.equal(validate([output("line-33", 33, 1, "output-33")]).kind, "invalid");
  assert.equal(validate([output("line-1", 1, 65536, "output-overflow")]).kind, "invalid");
});
