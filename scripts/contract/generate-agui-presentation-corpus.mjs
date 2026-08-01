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
const agentCandidateProfile = JSON.parse(
  await readFile(resolve(options.root, contracts.agentCandidateProfile), "utf8"),
);
if (!Array.isArray(agentCandidateProfile.allowedActivityTypes) || agentCandidateProfile.allowedActivityTypes.length === 0) {
  throw new Error("Agent candidate profile activities are required");
}
const authorityBase = corpus.positiveCases.find(({ id }) => id === "resume-with-safe-typed-presentation");
if (authorityBase === undefined) throw new Error("resume-with-safe-typed-presentation corpus case is required");
const resumedBaseBinding = authorityBase.runBindings.find(
  ({ bindingRef }) => bindingRef === "run-binding.01.segment.0",
);
if (resumedBaseBinding === undefined || resumedBaseBinding.state !== "finished") {
  throw new Error("resume-with-safe-typed-presentation terminal base binding is required");
}
resumedBaseBinding.terminalDisposition = "success";
const activityTemplates = agentCandidateProfile.allowedActivityTypes.map((activityType) => {
  const frame = authorityBase.frames.find(
    ({ data }) => data.event.type === "ACTIVITY_SNAPSHOT" && data.event.activityType === activityType,
  );
  if (frame === undefined) throw new Error(`Agent activity template missing: ${activityType}`);
  return {
    event: structuredClone(frame.data.event),
    sourceKind: frame.data.source.sourceKind,
  };
});
const parentCase = corpus.positiveCases.find(({ id }) => id === "safe-run-error");
if (parentCase === undefined) throw new Error("safe-run-error corpus case is required");
const successRunBindingRef = "run-binding.error.parent.segment.0";
const successInternalRunRef = "internal.run.error.parent";
const successPresentationRunId = "presentation.run.error.parent.segment.0";
const successMessageBindingRef = "message-binding.error.parent.segment.0";
const successInternalMessageRef = "internal.message.error.parent.assistant.01";
const successPresentationMessageId = "presentation.message.error.parent.segment.0";
const errorRunBindingRef = "run-binding.error.segment.0";
const errorInternalRunRef = "internal.run.error";
const errorPresentationRunId = "presentation.run.error.segment.0";
const recordedAt = (sequence) => `2026-08-01T13:00:${String(sequence).padStart(2, "0")}.000Z`;
parentCase.runBindings = [
  {
    bindingRef: successRunBindingRef, profileRevision, sessionId: "session.error",
    internalRunRef: successInternalRunRef, presentationThreadId: "thread.session.error",
    presentationRunId: successPresentationRunId, segmentOrdinal: 0,
    resumeOfPresentationRunId: null,
    parentLineage: { parentInternalRunRef: null, parentPresentationRunId: null },
    state: "finished", terminalDisposition: "success",
    openedBySourceEventId: "agent.event.run.success.000", terminalSourceEventId: "agent.event.run.success.012",
    openedAt: recordedAt(1), terminalAt: recordedAt(13),
  },
  {
    bindingRef: errorRunBindingRef, profileRevision, sessionId: "session.error",
    internalRunRef: errorInternalRunRef, presentationThreadId: "thread.session.error",
    presentationRunId: errorPresentationRunId, segmentOrdinal: 0,
    resumeOfPresentationRunId: null,
    parentLineage: {
      parentInternalRunRef: successInternalRunRef,
      parentPresentationRunId: successPresentationRunId,
    },
    state: "error", terminalDisposition: "error",
    openedBySourceEventId: "agent.event.run.error.000", terminalSourceEventId: "agent.event.run.error.001",
    openedAt: recordedAt(14), terminalAt: recordedAt(15),
  },
];
parentCase.messageBindings = [
  {
    bindingRef: successMessageBindingRef,
    profileRevision,
    sessionId: "session.error",
    internalMessageRef: successInternalMessageRef,
    presentationRunBindingRef: successRunBindingRef,
    presentationMessageId: successPresentationMessageId,
    resumeSegmentOrdinal: 0,
    state: "ended",
    openedBySourceEventId: "agent.event.run.success.001",
    endedBySourceEventId: "agent.event.run.success.011",
    openedAt: recordedAt(2),
    endedAt: recordedAt(12),
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
const messageFrame = (event, data) => {
  const frame = runFrame(event, data);
  frame.data.presentationMessageBindingRef = successMessageBindingRef;
  return frame;
};
const successFrame = (event, sourceKind, sourceOrdinal, messageScoped = false) => {
  const durableSequence = sourceOrdinal + 1;
  const timestamp = recordedAt(durableSequence);
  const candidateEvent = structuredClone(event);
  candidateEvent.timestamp = Date.parse(timestamp);
  if (messageScoped) candidateEvent.messageId = successPresentationMessageId;
  const data = {
    bindingRef: successRunBindingRef,
    source: source(
      `agent.event.run.success.${String(sourceOrdinal).padStart(3, "0")}`,
      sourceKind,
      String(durableSequence),
      timestamp,
    ),
  };
  return messageScoped ? messageFrame(candidateEvent, data) : runFrame(candidateEvent, data);
};
const successFrames = [
  successFrame(
    { type: "RUN_STARTED", threadId: "thread.session.error", runId: successPresentationRunId },
    "presentation.run.started", 0,
  ),
  successFrame(
    { type: "TEXT_MESSAGE_START", role: "assistant" },
    "presentation.message.text.started", 1, true,
  ),
  successFrame(
    { type: "TEXT_MESSAGE_CONTENT", delta: "I can help with that." },
    "presentation.message.text.content", 2, true,
  ),
  ...activityTemplates.map(({ event, sourceKind }, index) => successFrame(event, sourceKind, index + 3, true)),
  successFrame(
    { type: "TEXT_MESSAGE_END" },
    "presentation.message.text.ended", 11, true,
  ),
  successFrame(
    { type: "RUN_FINISHED", threadId: "thread.session.error", runId: successPresentationRunId },
    "presentation.run.finished", 12,
  ),
];
const errorStartedAt = recordedAt(14);
const errorTerminalAt = recordedAt(15);
const errorFrames = [
  runFrame(
    {
      type: "RUN_STARTED", timestamp: Date.parse(errorStartedAt), threadId: "thread.session.error",
      runId: errorPresentationRunId, parentRunId: successPresentationRunId,
    },
    { bindingRef: errorRunBindingRef, source: source("agent.event.run.error.000", "presentation.run.started", "14", errorStartedAt) },
  ),
  runFrame(
    {
      type: "RUN_ERROR", timestamp: Date.parse(errorTerminalAt),
      message: "The run could not be completed.", code: "RUN_FAILED",
    },
    { bindingRef: errorRunBindingRef, source: source("agent.event.run.error.001", "presentation.run.error", "15", errorTerminalAt) },
  ),
];
parentCase.frames = [...successFrames, ...errorFrames];
const successAgentThreadRef = "agent.thread:01JZ6Y6K8M5A3Q2R7T9V4W1X0C";
const errorAgentThreadRef = "agent.thread:01JZ6Y7B4N8C2P5S0U3W6X9Y1D";
corpus.agentSourceFixtures = [
  ...successFrames.map((frame, sourceOrdinal) => (
    agentSourceFixture(parentCase, frame, String(sourceOrdinal), successAgentThreadRef)
  )),
  ...errorFrames.map((frame, sourceOrdinal) => (
    agentSourceFixture(parentCase, frame, String(sourceOrdinal), errorAgentThreadRef)
  )),
];
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
const parentHead = parentCase.frames.at(-1);
const successRunFinishedFrame = successFrames.at(-1);
if (parentHead === undefined || successRunFinishedFrame?.data.event.type !== "RUN_FINISHED") {
  throw new Error("complete Agent candidate corpus frames are required");
}
const sourceFixtureByRef = new Map(corpus.agentSourceFixtures.map((fixture) => [fixture.source.sourceEventRef, fixture]));
const candidateEnvelopeFor = (contractCase, frame) => {
  const fixture = sourceFixtureByRef.get(frame.data.source.sourceEventId);
  if (fixture === undefined || fixture.baseCaseId !== contractCase.id) {
    throw new Error(`Agent source fixture missing: ${frame.data.source.sourceEventId}`);
  }
  return candidateEnvelopeFromFrame(contractCase, frame, fixture.source);
};
const successCandidateEnvelope = candidateEnvelopeFor(parentCase, successRunFinishedFrame);
corpus.agentCandidateProjectionCases = [
  {
    id: "agent-success-outcome-to-browser-run-finished",
    baseCaseId: parentCase.id,
    sourceEventId: successRunFinishedFrame.data.source.sourceEventId,
    candidateEnvelope: successCandidateEnvelope,
    expectedPresentationEvent: structuredClone(successRunFinishedFrame.data.event),
  },
];
const envelopeCaseId = (frame) => {
  const event = frame.data.event;
  if (event.type === "RUN_STARTED") return "agent-run-start-envelope";
  if (event.type === "TEXT_MESSAGE_START") return "agent-text-start-envelope";
  if (event.type === "TEXT_MESSAGE_CONTENT") return "agent-text-envelope";
  if (event.type === "TEXT_MESSAGE_END") return "agent-text-end-envelope";
  if (event.type === "ACTIVITY_SNAPSHOT" && event.activityType === "kokoro.safe-summary.v1") {
    return "agent-activity-envelope";
  }
  if (event.type === "ACTIVITY_SNAPSHOT") {
    const activityName = event.activityType.replace(/^kokoro\./u, "").replace(/\.v1$/u, "");
    return `agent-activity-${activityName}-envelope`;
  }
  throw new Error(`unsupported success candidate envelope: ${event.type}`);
};
corpus.agentCandidateEnvelopeCases = [
  ...successFrames.slice(0, -1).map((frame) => ({
    id: envelopeCaseId(frame),
    baseCaseId: parentCase.id,
    sourceEventId: frame.data.source.sourceEventId,
    candidateEnvelope: candidateEnvelopeFor(parentCase, frame),
  })),
  {
    id: "agent-error-run-start-envelope",
    baseCaseId: parentCase.id,
    sourceEventId: errorFrames[0].data.source.sourceEventId,
    candidateEnvelope: candidateEnvelopeFor(parentCase, errorFrames[0]),
  },
  {
    id: "agent-run-error-envelope",
    baseCaseId: parentCase.id,
    sourceEventId: errorFrames[1].data.source.sourceEventId,
    candidateEnvelope: candidateEnvelopeFor(parentCase, errorFrames[1]),
  },
];
corpus.snapshotAuthorityCases = [
  {
    id: "nonzero-head-after-binding-evidence",
    baseCaseId: parentCase.id,
    snapshot: {
      authority: "session-browser-v3-http-snapshot",
      hydrate: true,
      repair: true,
      profileRevision,
      sessionId: parentCase.snapshot.sessionId,
      streamEpoch: parentCase.snapshot.streamEpoch,
      durableSeq: parentHead.data.source.durableSeq,
      lastRecordedAt: parentHead.data.source.recordedAt,
      cursor: parentHead.id,
      runBindings: structuredClone(parentCase.runBindings),
      messageBindings: structuredClone(parentCase.messageBindings),
    },
    nextEventRecordedAt: recordedAt(16),
  },
];
corpus.snapshotAuthorityNegativeCases = [
  {
    id: "zero-head-retains-bindings",
    baseAuthorityCaseId: "nonzero-head-after-binding-evidence",
    mutation: { operation: "zero-head-retains-bindings" },
    expectedCode: "agui_snapshot_zero_head_bindings_invalid",
  },
  {
    id: "binding-evidence-exceeds-head",
    baseAuthorityCaseId: "nonzero-head-after-binding-evidence",
    mutation: { operation: "binding-evidence-exceeds-head" },
    expectedCode: "agui_snapshot_binding_evidence_exceeds_head",
  },
  {
    id: "noncanonical-binding-time",
    baseAuthorityCaseId: "nonzero-head-after-binding-evidence",
    mutation: { operation: "noncanonical-binding-time" },
    expectedCode: "agui_snapshot_binding_time_invalid",
  },
  {
    id: "multiple-presentation-thread",
    baseAuthorityCaseId: "nonzero-head-after-binding-evidence",
    mutation: { operation: "multiple-presentation-thread" },
    expectedCode: "agui_snapshot_thread_scope_invalid",
  },
  {
    id: "parent-lineage-cycle",
    baseAuthorityCaseId: "nonzero-head-after-binding-evidence",
    mutation: { operation: "parent-lineage-cycle" },
    expectedCode: "agui_parent_lineage_cycle",
  },
  {
    id: "m0-interrupted-terminal",
    baseAuthorityCaseId: "nonzero-head-after-binding-evidence",
    mutation: { operation: "m0-interrupted-terminal" },
    expectedCode: "agui_snapshot_terminal_state_invalid",
  },
];
corpus.negativeCases = [
  ...corpus.negativeCases.filter(({ id }) => id !== "m0-interrupted-main-run"),
  {
    id: "m0-interrupted-main-run",
    baseCaseId: authorityBase.id,
    mutation: {
      operation: "set",
      path: "runBindings.0.terminalDisposition",
      value: "interrupted",
    },
    expectedCode: "agui_run_terminal_state_invalid",
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
