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
const contracts = Object.freeze({
  profile: "contract/registry/agui-upstream-profile.yaml",
  agentCandidateProfile: "contract/registry/agui-agent-candidate-profile-v1.yaml",
  mapping: "contract/registry/agui-presentation-mapping-v1.yaml",
  eventSchema: "contract/spec/kokoro-agui-presentation-event-v1.yaml",
  agentCandidateSchema: "contract/spec/agent-agui-event-candidate-v1.yaml",
  agentCandidateEnvelopeSchema: "contract/spec/agent-agui-candidate-envelope-v1.yaml",
  projectionPayloadSchema: "contract/spec/session-agui-projection-payload-v1.yaml",
  presentationRowSchema: "contract/spec/session-agui-presentation-row-v1.yaml",
  runBindingSchema: "contract/spec/presentation-run-binding-v1.yaml",
  messageBindingSchema: "contract/spec/presentation-message-binding-v1.yaml",
  streamSchema: "contract/spec/session-agui-stream-v1.yaml",
  snapshotAuthoritySchema: "contract/spec/session-agui-snapshot-authority-v1.yaml",
});

function canonical(value) {
  if (value === null || typeof value === "boolean" || typeof value === "number") return JSON.stringify(value);
  if (typeof value === "string") return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map(canonical).join(",")}]`;
  return `{${Object.keys(value).sort().map((name) => `${JSON.stringify(name)}:${canonical(value[name])}`).join(",")}}`;
}

function digest(value) {
  return `sha256:${createHash("sha256").update(canonical(value), "utf8").digest("hex")}`;
}

function candidateRefFor(envelope) {
  const material = [
    envelope.profileRevision,
    envelope.source.route.internalRunRef,
    envelope.source.route.internalThreadRef,
    envelope.source.route.internalMessageRef ?? "",
    envelope.source.sourceEventRef,
    envelope.source.sourceOrdinal,
    envelope.source.recordedAt,
    envelope.eventDigest,
  ].join("\u0000");
  return `agui_candidate:sha256:${createHash("sha256").update(material, "utf8").digest("hex")}`;
}

function candidateEnvelopeFromFrame(contractCase, frame, candidateSource) {
  const runBinding = contractCase.runBindings.find(({ bindingRef }) => bindingRef === frame.data.presentationRunBindingRef);
  if (runBinding === undefined) throw new Error(`candidate run binding missing: ${frame.data.source.sourceEventId}`);
  const messageBinding = frame.data.presentationMessageBindingRef === undefined
    ? undefined
    : contractCase.messageBindings.find(({ bindingRef }) => bindingRef === frame.data.presentationMessageBindingRef);
  const event = structuredClone(frame.data.event);
  if (event.type === "RUN_STARTED" || event.type === "RUN_FINISHED") {
    event.threadId = candidateSource.route.internalThreadRef;
    event.runId = runBinding.internalRunRef;
  }
  if (event.type === "RUN_STARTED") delete event.parentRunId;
  if (event.type === "RUN_FINISHED") event.outcome = { type: "success" };
  if (["TEXT_MESSAGE_START", "TEXT_MESSAGE_CONTENT", "TEXT_MESSAGE_END", "ACTIVITY_SNAPSHOT"].includes(event.type)) {
    if (messageBinding === undefined) throw new Error(`candidate message binding missing: ${frame.data.source.sourceEventId}`);
    event.messageId = candidateSource.route.internalMessageRef;
  }
  const envelope = {
    profileRevision: "kokoro-agent-agui-candidate.v1",
    source: structuredClone(candidateSource),
    eventDigest: digest(event),
    event,
  };
  envelope.candidateRef = candidateRefFor(envelope);
  return envelope;
}

function replaceProjectionSourceRef(contractCase, previousRef, sourceEventRef) {
  const frame = contractCase.frames.find(({ data }) => data.source.sourceEventId === previousRef)
    ?? contractCase.frames.find(({ data }) => data.source.sourceEventId === sourceEventRef);
  if (frame === undefined) throw new Error(`Agent source projection frame missing: ${previousRef}`);
  frame.data.source.sourceEventId = sourceEventRef;
  for (const binding of [...contractCase.runBindings, ...contractCase.messageBindings]) {
    for (const field of ["openedBySourceEventId", "terminalSourceEventId", "endedBySourceEventId"]) {
      if (binding[field] === previousRef) binding[field] = sourceEventRef;
    }
  }
  return frame;
}

function agentSourceFixture(contractCase, frame, sourceOrdinal, internalThreadRef) {
  const runBinding = contractCase.runBindings.find(({ bindingRef }) => bindingRef === frame.data.presentationRunBindingRef);
  if (runBinding === undefined) throw new Error(`Agent source run binding missing: ${frame.data.source.sourceEventId}`);
  const messageBinding = frame.data.presentationMessageBindingRef === undefined
    ? undefined
    : contractCase.messageBindings.find(({ bindingRef }) => bindingRef === frame.data.presentationMessageBindingRef);
  return {
    baseCaseId: contractCase.id,
    source: {
      sourceEventRef: frame.data.source.sourceEventId,
      sourceOrdinal,
      recordedAt: frame.data.source.recordedAt,
      route: {
        internalRunRef: runBinding.internalRunRef,
        internalThreadRef,
        ...(messageBinding === undefined ? {} : { internalMessageRef: messageBinding.internalMessageRef }),
      },
    },
  };
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
corpus.contracts = contracts;
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
const authorityBase = corpus.positiveCases.find(({ id }) => id === "resume-with-safe-typed-presentation");
if (authorityBase === undefined) throw new Error("resume-with-safe-typed-presentation corpus case is required");
const agentSourcePlans = [
  { contractCase: authorityBase, previousRef: "source.01", sourceEventRef: "agent.event.run.01.000", sourceOrdinal: "0", internalThreadRef: "agent.thread:01JZ6Y6K8M5A3Q2R7T9V4W1X0C" },
  { contractCase: authorityBase, previousRef: "source.03", sourceEventRef: "agent.event.run.01.002", sourceOrdinal: "2", internalThreadRef: "agent.thread:01JZ6Y6K8M5A3Q2R7T9V4W1X0C" },
  { contractCase: authorityBase, previousRef: "source.04", sourceEventRef: "agent.event.run.01.003", sourceOrdinal: "3", internalThreadRef: "agent.thread:01JZ6Y6K8M5A3Q2R7T9V4W1X0C" },
  { contractCase: authorityBase, previousRef: "source.26", sourceEventRef: "agent.event.run.01.025", sourceOrdinal: "25", internalThreadRef: "agent.thread:01JZ6Y6K8M5A3Q2R7T9V4W1X0C" },
  { contractCase: parentCase, previousRef: "error-source.03", sourceEventRef: "agent.event.run.error.000", sourceOrdinal: "0", internalThreadRef: "agent.thread:01JZ6Y7B4N8C2P5S0U3W6X9Y1D" },
  { contractCase: parentCase, previousRef: "error-source.04", sourceEventRef: "agent.event.run.error.001", sourceOrdinal: "1", internalThreadRef: "agent.thread:01JZ6Y7B4N8C2P5S0U3W6X9Y1D" },
];
corpus.agentSourceFixtures = agentSourcePlans.map(({ contractCase, previousRef, sourceEventRef, sourceOrdinal, internalThreadRef }) => {
  const frame = replaceProjectionSourceRef(contractCase, previousRef, sourceEventRef);
  return agentSourceFixture(contractCase, frame, sourceOrdinal, internalThreadRef);
});
for (const contractCase of corpus.positiveCases) {
  contractCase.snapshot.lastRecordedAt = contractCase.snapshot.durableSeq === "0" ? null : contractCase.snapshot.lastRecordedAt;
  delete contractCase.snapshot.runBindings;
  delete contractCase.snapshot.messageBindings;
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
const authorityHead = authorityBase.frames.at(-1);
const successRunFinishedFrame = authorityBase.frames.find((frame) => {
  if (frame.data.event.type !== "RUN_FINISHED") return false;
  const binding = authorityBase.runBindings.find(({ bindingRef }) => bindingRef === frame.data.presentationRunBindingRef);
  return binding?.terminalDisposition === "success";
});
if (successRunFinishedFrame === undefined) throw new Error("success RUN_FINISHED corpus frame is required");
const successRunBinding = authorityBase.runBindings.find(({ bindingRef }) => bindingRef === successRunFinishedFrame.data.presentationRunBindingRef);
if (successRunBinding === undefined) throw new Error("success RUN_FINISHED binding is required");
const sourceFixtureByRef = new Map(corpus.agentSourceFixtures.map((fixture) => [fixture.source.sourceEventRef, fixture]));
const candidateEnvelopeFor = (contractCase, frame) => {
  const fixture = sourceFixtureByRef.get(frame.data.source.sourceEventId);
  if (fixture === undefined || fixture.baseCaseId !== contractCase.id) {
    throw new Error(`Agent source fixture missing: ${frame.data.source.sourceEventId}`);
  }
  return candidateEnvelopeFromFrame(contractCase, frame, fixture.source);
};
const successCandidateEnvelope = candidateEnvelopeFor(authorityBase, successRunFinishedFrame);
corpus.agentCandidateProjectionCases = [
  {
    id: "agent-success-outcome-to-browser-run-finished",
    baseCaseId: authorityBase.id,
    sourceEventId: successRunFinishedFrame.data.source.sourceEventId,
    candidateEnvelope: successCandidateEnvelope,
    expectedPresentationEvent: structuredClone(successRunFinishedFrame.data.event),
  },
];
const runStartedFrame = authorityBase.frames.find((frame) => frame.data.source.sourceEventId === "agent.event.run.01.000");
const textFrame = authorityBase.frames.find((frame) => frame.data.source.sourceEventId === "agent.event.run.01.002");
const activityFrame = authorityBase.frames.find((frame) => frame.data.source.sourceEventId === "agent.event.run.01.003");
const runErrorStartedFrame = parentCase.frames.find((frame) => frame.data.source.sourceEventId === "agent.event.run.error.000");
const runErrorFrame = parentCase.frames.find((frame) => frame.data.source.sourceEventId === "agent.event.run.error.001");
if (runStartedFrame === undefined || textFrame === undefined || activityFrame === undefined || runErrorStartedFrame === undefined || runErrorFrame === undefined) {
  throw new Error("Agent candidate route-family corpus frames are required");
}
corpus.agentCandidateEnvelopeCases = [
  { id: "agent-run-start-envelope", baseCaseId: authorityBase.id, sourceEventId: runStartedFrame.data.source.sourceEventId, candidateEnvelope: candidateEnvelopeFor(authorityBase, runStartedFrame) },
  { id: "agent-error-run-start-envelope", baseCaseId: parentCase.id, sourceEventId: runErrorStartedFrame.data.source.sourceEventId, candidateEnvelope: candidateEnvelopeFor(parentCase, runErrorStartedFrame) },
  { id: "agent-run-error-envelope", baseCaseId: parentCase.id, sourceEventId: runErrorFrame.data.source.sourceEventId, candidateEnvelope: candidateEnvelopeFor(parentCase, runErrorFrame) },
  { id: "agent-text-envelope", baseCaseId: authorityBase.id, sourceEventId: textFrame.data.source.sourceEventId, candidateEnvelope: candidateEnvelopeFor(authorityBase, textFrame) },
  { id: "agent-activity-envelope", baseCaseId: authorityBase.id, sourceEventId: activityFrame.data.source.sourceEventId, candidateEnvelope: candidateEnvelopeFor(authorityBase, activityFrame) },
];
corpus.snapshotAuthorityCases = [
  {
    id: "nonzero-head-after-binding-evidence",
    baseCaseId: authorityBase.id,
    snapshot: {
      authority: "session-browser-v3-http-snapshot",
      hydrate: true,
      repair: true,
      profileRevision,
      sessionId: authorityBase.snapshot.sessionId,
      streamEpoch: authorityBase.snapshot.streamEpoch,
      durableSeq: authorityHead.data.source.durableSeq,
      lastRecordedAt: authorityHead.data.source.recordedAt,
      cursor: authorityHead.id,
      runBindings: structuredClone(authorityBase.runBindings),
      messageBindings: structuredClone(authorityBase.messageBindings),
    },
    nextEventRecordedAt: "2026-08-01T12:00:27.000Z",
  },
];
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
