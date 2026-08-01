#!/usr/bin/env node

import { createCipheriv, createHash } from "node:crypto";
import { readFile, writeFile } from "node:fs/promises";
import { resolve } from "node:path";

const defaultRoot = resolve(import.meta.dirname, "../..");
const profileRevision = "kokoro-agui-presentation.v1";
const cursorProfileRevision = "opaque-session-cursor-v1";
const keyRevision = "agui-conformance-2026-08";
const key = createHash("sha256").update("kokoro-agui-presentation-public-conformance-key-v1", "utf8").digest();
const aad = Buffer.from(`kokoro.session.browser.cursor.v1\u0000${keyRevision}`, "utf8");

function canonical(value) {
  if (value === null || typeof value === "boolean" || typeof value === "number") return JSON.stringify(value);
  if (typeof value === "string") return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map(canonical).join(",")}]`;
  return `{${Object.keys(value).sort().map((name) => `${JSON.stringify(name)}:${canonical(value[name])}`).join(",")}}`;
}

function digest(value) {
  return `sha256:${createHash("sha256").update(canonical(value), "utf8").digest("hex")}`;
}

function issueCursor({ sessionId, streamEpoch, durableSeq }) {
  const claims = {
    version: 1,
    kind: "stream",
    sessionId,
    streamEpoch,
    durableSeq,
    profileRevision,
    cursorProfileRevision,
  };
  const plaintext = Buffer.from(canonical(claims), "utf8");
  const iv = createHash("sha256").update(Buffer.concat([aad, plaintext])).digest().subarray(0, 12);
  const cipher = createCipheriv("aes-256-gcm", key, iv);
  cipher.setAAD(aad);
  const encrypted = Buffer.concat([cipher.update(plaintext), cipher.final()]);
  const tag = cipher.getAuthTag();
  return ["v1", keyRevision, iv.toString("base64url"), encrypted.toString("base64url"), tag.toString("base64url")].join(".");
}

function parseArguments(argv) {
  let check = false;
  let root = defaultRoot;
  for (let index = 0; index < argv.length; index += 1) {
    if (argv[index] === "--check") {
      check = true;
      continue;
    }
    if (argv[index] === "--root" && argv[index + 1] !== undefined) {
      root = resolve(argv[index + 1]);
      index += 1;
      continue;
    }
    throw new Error(`agui_corpus_arguments_invalid: ${argv[index]}`);
  }
  return { check, root };
}

const options = parseArguments(process.argv.slice(2));
const corpusPath = resolve(options.root, "contract/corpus/agui-presentation-v1.json");
const sourceText = await readFile(corpusPath, "utf8");
const corpus = JSON.parse(sourceText);
const parentCase = corpus.positiveCases.find(({ id }) => id === "safe-run-error");
if (parentCase === undefined) throw new Error("safe-run-error corpus case is required");
parentCase.runBindings = [
  {
    bindingRef: "run-binding.error.parent.segment.0", profileRevision, sessionId: "session.error",
    internalRunRef: "internal.run.error.parent", presentationThreadId: "thread.session.error",
    presentationRunId: "presentation.run.error.parent.segment.0", segmentOrdinal: 0,
    resumeOfPresentationRunId: null,
    parentLineage: { parentInternalRunRef: null, parentPresentationRunId: null },
    state: "finished", terminalDisposition: "success",
    openedBySourceEventId: "error-parent-source.01", terminalSourceEventId: "error-parent-source.02",
    openedAt: "2026-08-01T13:00:01.000Z", terminalAt: "2026-08-01T13:00:02.000Z",
  },
  {
    bindingRef: "run-binding.error.segment.0", profileRevision, sessionId: "session.error",
    internalRunRef: "internal.run.error", presentationThreadId: "thread.session.error",
    presentationRunId: "presentation.run.error.segment.0", segmentOrdinal: 0,
    resumeOfPresentationRunId: null,
    parentLineage: {
      parentInternalRunRef: "internal.run.error.parent",
      parentPresentationRunId: "presentation.run.error.parent.segment.0",
    },
    state: "error", terminalDisposition: "error",
    openedBySourceEventId: "error-source.03", terminalSourceEventId: "error-source.04",
    openedAt: "2026-08-01T13:00:03.000Z", terminalAt: "2026-08-01T13:00:04.000Z",
  },
];
const source = (sourceEventId, sourceKind, durableSeq, recordedAt) => ({
  sourceEventId, sourceKind, sessionId: "session.error", streamEpoch: "9", durableSeq,
  projectionVersion: Number(durableSeq), schemaRevision: 1, recordedAt,
});
const runFrame = (event, data) => ({ kind: "durable", id: "derived-by-generator", event: event.type, data: {
  profileRevision,
  source: data.source,
  presentationRunBindingRef: data.bindingRef,
  event,
} });
parentCase.frames = [
  runFrame(
    { type: "RUN_STARTED", timestamp: Date.parse("2026-08-01T13:00:01.000Z"), threadId: "thread.session.error", runId: "presentation.run.error.parent.segment.0" },
    { bindingRef: "run-binding.error.parent.segment.0", source: source("error-parent-source.01", "presentation.run.started", "1", "2026-08-01T13:00:01.000Z") },
  ),
  runFrame(
    { type: "RUN_FINISHED", timestamp: Date.parse("2026-08-01T13:00:02.000Z"), threadId: "thread.session.error", runId: "presentation.run.error.parent.segment.0" },
    { bindingRef: "run-binding.error.parent.segment.0", source: source("error-parent-source.02", "presentation.run.finished", "2", "2026-08-01T13:00:02.000Z") },
  ),
  runFrame(
    { type: "RUN_STARTED", timestamp: Date.parse("2026-08-01T13:00:03.000Z"), threadId: "thread.session.error", runId: "presentation.run.error.segment.0", parentRunId: "presentation.run.error.parent.segment.0" },
    { bindingRef: "run-binding.error.segment.0", source: source("error-source.03", "presentation.run.started", "3", "2026-08-01T13:00:03.000Z") },
  ),
  runFrame(
    { type: "RUN_ERROR", timestamp: Date.parse("2026-08-01T13:00:04.000Z"), message: "The run could not be completed.", code: "RUN_FAILED" },
    { bindingRef: "run-binding.error.segment.0", source: source("error-source.04", "presentation.run.error", "4", "2026-08-01T13:00:04.000Z") },
  ),
];
for (const contractCase of corpus.positiveCases) {
  const snapshotCursor = issueCursor({
    sessionId: contractCase.snapshot.sessionId,
    streamEpoch: contractCase.snapshot.streamEpoch,
    durableSeq: contractCase.snapshot.durableSeq,
  });
  contractCase.snapshot.cursor = snapshotCursor;
  contractCase.request.lastEventId = snapshotCursor;
  contractCase.request.queryCursor = snapshotCursor;
  for (const frame of contractCase.frames) {
    frame.id = issueCursor(frame.data.source);
  }
  contractCase.durableRows = contractCase.frames.map((frame) => ({
    rowRef: `presentation-row.${frame.data.source.sourceEventId}`,
    profileRevision: frame.data.profileRevision,
    cursorProfileRevision,
    source: structuredClone(frame.data.source),
    projectionPayload: structuredClone(frame.data),
    projectionPayloadDigest: digest(frame.data),
  }));
  contractCase.controlFrame.data.lastDurableCursor = contractCase.frames.at(-1).id;
}
const generatedText = `${JSON.stringify(corpus, null, 2)}\n`;
if (options.check) {
  if (generatedText !== sourceText) {
    process.stderr.write("agui_presentation_corpus_drift\n");
    process.exitCode = 1;
  } else {
    process.stdout.write("agui_presentation_corpus_ok\n");
  }
} else {
  await writeFile(corpusPath, generatedText);
  process.stdout.write("agui_presentation_corpus_generated\n");
}
