#!/usr/bin/env node

import { createCipheriv, createHash, createHmac } from "node:crypto";
import { readFile, writeFile } from "node:fs/promises";
import { resolve } from "node:path";

const defaultRoot = resolve(import.meta.dirname, "../..");
const profileRevision = "kokoro-agui-presentation.v1";
const cursorProfileRevision = "opaque-session-cursor-v1";
const keyRevision = "agui-conformance-2026-08";
const key = createHash("sha256").update("kokoro-agui-presentation-public-conformance-key-v1", "utf8").digest();
const publicSourceFixtureHmacKey = createHash("sha256")
  .update("kokoro-agui-public-source-fixture-test-only-v1", "utf8")
  .digest();
const presentationIdentityFixtureHmacKey = createHash("sha256")
  .update("kokoro-agui-presentation-identity-fixture-test-only-v1", "utf8")
  .digest();
const aad = Buffer.from(`kokoro.session.browser.cursor.v1\u0000${keyRevision}`, "utf8");
const uint64Maximum = "18446744073709551615";
const contracts = Object.freeze({
  profile: "contract/registry/agui-upstream-profile.yaml",
  agentCandidateProfile: "contract/registry/agui-agent-candidate-profile-v1.yaml",
  mapping: "contract/registry/agui-presentation-mapping-v1.yaml",
  eventSchema: "contract/spec/kokoro-agui-presentation-event-v1.yaml",
  agentCandidateSchema: "contract/spec/agent-agui-event-candidate-v1.yaml",
  agentCandidateEnvelopeSchema: "contract/spec/agent-agui-candidate-envelope-v1.yaml",
  projectionPayloadSchema: "contract/spec/session-agui-projection-payload-v1.yaml",
  presentationRowSchema: "contract/spec/session-agui-presentation-row-v1.yaml",
  bindingAuthorityDeltaSchema: "contract/spec/presentation-binding-authority-delta-v1.yaml",
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

function runRouteFor(contractCase, bindingRef) {
  const route = contractCase.sessionPrivateRouteFixtures?.runs?.find(
    (candidate) => candidate.presentationRunBindingRef === bindingRef,
  );
  if (route === undefined) throw new Error(`private run route missing: ${bindingRef}`);
  return route;
}

function messageRouteFor(contractCase, bindingRef) {
  const route = contractCase.sessionPrivateRouteFixtures?.messages?.find(
    (candidate) => candidate.presentationMessageBindingRef === bindingRef,
  );
  if (route === undefined) throw new Error(`private message route missing: ${bindingRef}`);
  return route;
}

function candidateEnvelopeFromFrame(contractCase, frame, candidateSource) {
  const runBinding = contractCase.runBindings.find(({ bindingRef }) => bindingRef === frame.data.presentationRunBindingRef);
  if (runBinding === undefined) throw new Error(`candidate run binding missing: ${frame.data.source.sourceEventId}`);
  const runRoute = runRouteFor(contractCase, runBinding.bindingRef);
  const messageBinding = frame.data.presentationMessageBindingRef === undefined
    ? undefined
    : contractCase.messageBindings.find(({ bindingRef }) => bindingRef === frame.data.presentationMessageBindingRef);
  const event = structuredClone(frame.data.event);
  if (event.type === "RUN_STARTED" || event.type === "RUN_FINISHED") {
    event.threadId = candidateSource.route.internalThreadRef;
    event.runId = runRoute.internalRunRef;
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
  const runRoute = runRouteFor(contractCase, runBinding.bindingRef);
  const messageBinding = frame.data.presentationMessageBindingRef === undefined
    ? undefined
    : contractCase.messageBindings.find(({ bindingRef }) => bindingRef === frame.data.presentationMessageBindingRef);
  const messageRoute = messageBinding === undefined ? undefined : messageRouteFor(contractCase, messageBinding.bindingRef);
  return {
    baseCaseId: contractCase.id,
    source: {
      sourceEventRef: frame.data.source.sourceEventId,
      sourceOrdinal,
      recordedAt: frame.data.source.recordedAt,
      route: {
        internalRunRef: runRoute.internalRunRef,
        internalThreadRef,
        ...(messageRoute === undefined ? {} : { internalMessageRef: messageRoute.internalMessageRef }),
      },
    },
  };
}

function publicSourceEventIdFor(contractCase, frame) {
  const fixtureMaterial = [
    "kokoro.agui.public-source-event-fixture.v1",
    contractCase.snapshot.sessionId,
    frame.data.source.streamEpoch,
    frame.data.source.durableSeq,
  ].join("\u0000");
  const opaqueFixture = createHmac("sha256", publicSourceFixtureHmacKey)
    .update(fixtureMaterial, "utf8")
    .digest("hex");
  return `presentation.event:${opaqueFixture}`;
}

function presentationIdentityFor(kind, caseId, ordinal) {
  const fixtureMaterial = [
    "kokoro.agui.presentation-identity-fixture.v1",
    kind,
    caseId,
    String(ordinal),
  ].join("\u0000");
  const opaqueFixture = createHmac("sha256", presentationIdentityFixtureHmacKey)
    .update(fixtureMaterial, "utf8")
    .digest("hex");
  return `presentation.${kind}:${opaqueFixture}`;
}

function sessionPublicIdentityFor(kind, caseId, ordinal) {
  const fixtureMaterial = [
    "kokoro.agui.session-public-identity-fixture.v1",
    kind,
    caseId,
    String(ordinal),
  ].join("\u0000");
  const opaqueFixture = createHmac("sha256", presentationIdentityFixtureHmacKey)
    .update(fixtureMaterial, "utf8")
    .digest("hex");
  return `session.${kind}:${opaqueFixture}`;
}

function bindSessionPublicIdentities(contractCase) {
  const runByPresentationId = new Map();
  for (const [index, binding] of contractCase.runBindings.entries()) {
    const resumed = binding.resumeOfPresentationRunId === null
      ? undefined
      : runByPresentationId.get(binding.resumeOfPresentationRunId);
    const ownsSessionRun = binding.parentLineage.parentPresentationRunId === null;
    binding.sessionRunId = ownsSessionRun
      ? resumed?.sessionRunId ?? sessionPublicIdentityFor("run", contractCase.id, index)
      : null;
    runByPresentationId.set(binding.presentationRunId, binding);
  }
  const runByBindingRef = new Map(contractCase.runBindings.map((binding) => [binding.bindingRef, binding]));
  for (const [index, binding] of contractCase.messageBindings.entries()) {
    const run = runByBindingRef.get(binding.presentationRunBindingRef);
    const materialized = run?.sessionRunId !== null && run?.sessionRunId !== undefined;
    binding.sessionMessageId = materialized
      ? sessionPublicIdentityFor("message", contractCase.id, index)
      : null;
    binding.sessionTextPartId = materialized
      ? sessionPublicIdentityFor("part", contractCase.id, index)
      : null;
  }
}

function normalizeOwnerPresentationFacts(contractCase) {
  for (const frame of contractCase.frames) {
    const event = frame.data.event;
    const updatedAt = new Date(event.timestamp).toISOString();
    if (event.type === "ACTIVITY_SNAPSHOT") {
      const existing = event.content;
      if (event.activityType === "kokoro.hitl.v1") {
        event.content = {
          ownerRef: existing.ownerRef,
          ownerVersion: existing.ownerVersion ?? "1",
          decisionGroupRef: existing.decisionGroupRef ?? "decision-group.01",
          requiredOwnerRefs: existing.requiredOwnerRefs ?? [existing.ownerRef],
          controlRef: existing.controlRef ?? "control.01",
          kind: existing.kind,
          title: existing.title,
          description: existing.description,
          allowedActions: existing.allowedActions,
          status: existing.status,
          ...(existing.riskSummary === undefined ? {} : { riskSummary: existing.riskSummary }),
          ...(existing.inputSchemaRef === undefined ? {} : { inputSchemaRef: existing.inputSchemaRef }),
          ...(existing.deadline === undefined ? {} : { deadline: existing.deadline }),
          ...(existing.receiptRef === undefined ? {} : { receiptRef: existing.receiptRef }),
          updatedAt,
        };
      } else if (event.activityType === "kokoro.media.v1") {
        event.content = {
          mediaOperationRef: existing.mediaOperationRef ?? existing.operationRef,
          definitionRef: existing.definitionRef ?? "media-definition.image.generate",
          definitionRevisionRef: existing.definitionRevisionRef ?? "media-definition-revision.image.generate.01",
          ownerVersion: existing.ownerVersion ?? "1",
          state: existing.state === "pending" ? "admission-pending" : existing.state,
          progressBps: existing.progressBps,
          candidates: existing.candidates ?? [{
            candidateRef: "media-candidate.01",
            ordinal: 0,
            ownerVersion: "1",
            state: "producing",
          }],
          ...(existing.costProjection === undefined ? {} : { costProjection: existing.costProjection }),
          ...(existing.outcomeClass === undefined ? {} : { outcomeClass: existing.outcomeClass }),
          ...(existing.safeFailure === undefined ? {} : { safeFailure: existing.safeFailure }),
          updatedAt,
        };
      } else if (event.activityType === "kokoro.artifact.v1") {
        event.content = {
          artifactRef: existing.artifactRef,
          artifactVersionRef: existing.artifactVersionRef,
          ownerVersion: existing.ownerVersion ?? "1",
          availability: existing.availability,
          mediaClass: existing.mediaClass,
          ...(existing.availability === "ready" ? {
            display: existing.display ?? {
              kind: "image", format: "png", width: 1024, height: 1024, byteSize: "1048576",
            },
          } : {}),
          ...(existing.safeFailure === undefined ? {} : { safeFailure: existing.safeFailure }),
          ...(existing.title === undefined ? {} : { title: existing.title }),
          updatedAt,
        };
      } else if (event.activityType === "kokoro.cost.v1") {
        const existingAmount = existing.amount?.amount ?? existing.displayAmount;
        event.content = {
          mediaOperationRef: existing.mediaOperationRef ?? "media-operation.01",
          costProjectionRef: existing.costProjectionRef,
          ownerVersion: existing.ownerVersion ?? "1",
          state: existing.state,
          freshness: ["current", "stale", "rebuilding", "unavailable"].includes(existing.freshness)
            ? existing.freshness
            : "current",
          ...(existing.state === "estimated" || existing.state === "final" || existing.state === "corrected"
            ? { amount: {
              creditUnit: existing.amount?.creditUnit ?? existing.unit ?? "credit",
              amount: typeof existingAmount === "string" && /^(0|[1-9][0-9]{0,39})$/u.test(existingAmount)
                ? existingAmount
                : "12",
            } }
            : {}),
          ...(existing.correctsOwnerVersion === undefined ? {} : { correctsOwnerVersion: existing.correctsOwnerVersion }),
          ...(existing.safeReason === undefined ? {} : { safeReason: existing.safeReason }),
          updatedAt,
        };
      } else {
        event.content = { ...existing, ownerVersion: existing.ownerVersion ?? "1", updatedAt };
      }
    }
    if (event.type === "CUSTOM" && event.name === "kokoro.control.replace.v1") {
      event.value = {
        controlRef: event.value.controlRef,
        ownerRef: event.value.ownerRef ?? "decision.01",
        decisionGroupRef: event.value.decisionGroupRef ?? "decision-group.01",
        kind: event.value.kind,
        state: event.value.state,
        ownerVersion: event.value.ownerVersion ?? String(event.value.expectedVersion ?? 1),
        allowedActions: event.value.allowedActions,
        updatedAt,
      };
    }
    if (event.type === "CUSTOM" && event.name === "kokoro.receipt.replace.v1") {
      event.value = {
        receiptRef: event.value.receiptRef,
        controlRef: event.value.controlRef ?? "control.01",
        ownerRef: event.value.ownerRef ?? "decision.01",
        decisionGroupRef: event.value.decisionGroupRef ?? "decision-group.01",
        commandId: event.value.commandId,
        operation: event.value.operation,
        state: event.value.state,
        ownerVersion: event.value.ownerVersion ?? String(event.value.version ?? 1),
        updatedAt,
      };
    }
  }
}

function replaceIdentityStrings(value, replacements) {
  if (typeof value === "string") return replacements.get(value) ?? value;
  if (Array.isArray(value)) return value.map((entry) => replaceIdentityStrings(entry, replacements));
  if (value === null || typeof value !== "object") return value;
  return Object.fromEntries(
    Object.entries(value).map(([key, child]) => [key, replaceIdentityStrings(child, replacements)]),
  );
}

function collectNamedIdentityValues(value, names, output) {
  if (Array.isArray(value)) {
    for (const entry of value) collectNamedIdentityValues(entry, names, output);
    return;
  }
  if (value === null || typeof value !== "object") return;
  for (const [key, child] of Object.entries(value)) {
    if (names.has(key) && typeof child === "string" && !output.includes(child)) output.push(child);
    collectNamedIdentityValues(child, names, output);
  }
}

function customPublicMessageFields(event) {
  if (event?.type !== "CUSTOM") return [];
  if (event.name === "kokoro.branch.replace.v1") return ["rootMessageId", "leafMessageId"];
  if (event.name === "kokoro.message.replace.v1") {
    return ["presentationMessageId", "parentPresentationMessageId"];
  }
  return [];
}

function opaquifyPresentationIdentities(contractCase) {
  const replacements = new Map();
  const threadOrdinals = new Map();
  for (const [index, binding] of contractCase.runBindings.entries()) {
    replacements.set(binding.bindingRef, presentationIdentityFor("run-binding", contractCase.id, index));
    if (!threadOrdinals.has(binding.presentationThreadId)) {
      threadOrdinals.set(binding.presentationThreadId, threadOrdinals.size);
    }
    replacements.set(
      binding.presentationThreadId,
      presentationIdentityFor("thread", contractCase.id, threadOrdinals.get(binding.presentationThreadId)),
    );
    replacements.set(binding.presentationRunId, presentationIdentityFor("run", contractCase.id, index));
  }
  for (const [index, binding] of contractCase.messageBindings.entries()) {
    replacements.set(binding.bindingRef, presentationIdentityFor("message-binding", contractCase.id, index));
    replacements.set(binding.presentationMessageId, presentationIdentityFor("message", contractCase.id, index));
  }
  const additionalRunIds = [];
  collectNamedIdentityValues(contractCase.frames, new Set(["presentationRunId"]), additionalRunIds);
  for (const value of additionalRunIds) {
    if (!replacements.has(value)) replacements.set(value, presentationIdentityFor("run", contractCase.id, replacements.size));
  }
  const customMessageReplacements = new Map();
  let customMessageOrdinal = contractCase.messageBindings.length;
  for (const frame of contractCase.frames) {
    const event = frame.data.event;
    for (const field of customPublicMessageFields(event)) {
      const value = event.value[field];
      if (value === null || customMessageReplacements.has(value)) continue;
      customMessageReplacements.set(
        value,
        replacements.get(value) ?? presentationIdentityFor("message", contractCase.id, customMessageOrdinal++),
      );
    }
  }
  const replaced = replaceIdentityStrings(contractCase, replacements);
  for (const [index, frame] of contractCase.frames.entries()) {
    const event = frame.data.event;
    for (const field of customPublicMessageFields(event)) {
      if (event.value[field] !== null) {
        replaced.frames[index].data.event.value[field] = customMessageReplacements.get(event.value[field]);
      }
    }
  }
  for (const key of Object.keys(contractCase)) delete contractCase[key];
  Object.assign(contractCase, replaced);
}

function replaceSourceEvidence(bindings, sourceIds, fields) {
  for (const binding of bindings) {
    for (const field of fields) {
      if (binding[field] === null) continue;
      const replacement = sourceIds.get(binding[field]);
      if (replacement === undefined) throw new Error(`binding source evidence missing: ${binding[field]}`);
      binding[field] = replacement;
    }
  }
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

function openRunBinding(binding) {
  return {
    ...structuredClone(binding),
    state: "open",
    terminalDisposition: null,
    terminalSourceEventId: null,
    terminalAt: null,
  };
}

function openMessageBinding(binding) {
  return {
    ...structuredClone(binding),
    state: "open",
    endedBySourceEventId: null,
    endedAt: null,
  };
}

function bindingAuthorityDeltaForFrame(contractCase, frame) {
  const event = frame.data.event;
  if (["RUN_STARTED", "RUN_FINISHED", "RUN_ERROR"].includes(event.type)) {
    const binding = contractCase.runBindings.find(
      ({ bindingRef }) => bindingRef === frame.data.presentationRunBindingRef,
    );
    if (binding === undefined) throw new Error(`run binding missing: ${frame.data.source.sourceEventId}`);
    return {
      kind: "run.replace",
      binding: event.type === "RUN_STARTED" ? openRunBinding(binding) : structuredClone(binding),
    };
  }
  if (["TEXT_MESSAGE_START", "TEXT_MESSAGE_END"].includes(event.type)) {
    const binding = contractCase.messageBindings.find(
      ({ bindingRef }) => bindingRef === frame.data.presentationMessageBindingRef,
    );
    if (binding === undefined) throw new Error(`message binding missing: ${frame.data.source.sourceEventId}`);
    return {
      kind: "message.replace",
      binding: event.type === "TEXT_MESSAGE_START" ? openMessageBinding(binding) : structuredClone(binding),
    };
  }
  return { kind: "none" };
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
for (const contractCase of corpus.positiveCases) {
  if (contractCase.sessionPrivateRouteFixtures === undefined) {
    contractCase.sessionPrivateRouteFixtures = {
      runs: contractCase.runBindings.map((binding) => ({
        presentationRunBindingRef: binding.bindingRef,
        internalRunRef: binding.internalRunRef,
        parentInternalRunRef: binding.parentLineage.parentInternalRunRef,
      })),
      messages: contractCase.messageBindings.map((binding) => ({
        presentationMessageBindingRef: binding.bindingRef,
        internalMessageRef: binding.internalMessageRef,
      })),
      provenance: [],
    };
  }
  if (contractCase.sessionPrivateRouteFixtures.provenance === undefined) {
    contractCase.sessionPrivateRouteFixtures.provenance = [];
  }
  for (const binding of contractCase.runBindings) {
    delete binding.internalRunRef;
    delete binding.parentLineage.parentInternalRunRef;
  }
  for (const binding of contractCase.messageBindings) delete binding.internalMessageRef;
  bindSessionPublicIdentities(contractCase);
  normalizeOwnerPresentationFacts(contractCase);
}
const resumedBaseBinding = authorityBase.runBindings.find(
  ({ segmentOrdinal }) => segmentOrdinal === 0,
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
const successTextEndOrdinal = activityTemplates.length + 3;
const successRunFinishedOrdinal = successTextEndOrdinal + 1;
const errorRunStartedDurableSequence = successRunFinishedOrdinal + 2;
const errorRunTerminalDurableSequence = errorRunStartedDurableSequence + 1;
parentCase.runBindings = [
  {
    bindingRef: successRunBindingRef, profileRevision, sessionId: "session.error",
    presentationThreadId: "thread.session.error",
    presentationRunId: successPresentationRunId, segmentOrdinal: 0,
    resumeOfPresentationRunId: null,
    parentLineage: { parentPresentationRunId: null },
    state: "finished", terminalDisposition: "success",
    openedBySourceEventId: "agent.event.run.success.000",
    terminalSourceEventId: `agent.event.run.success.${String(successRunFinishedOrdinal).padStart(3, "0")}`,
    openedAt: recordedAt(1), terminalAt: recordedAt(successRunFinishedOrdinal + 1),
  },
  {
    bindingRef: errorRunBindingRef, profileRevision, sessionId: "session.error",
    presentationThreadId: "thread.session.error",
    presentationRunId: errorPresentationRunId, segmentOrdinal: 0,
    resumeOfPresentationRunId: null,
    parentLineage: {
      parentPresentationRunId: successPresentationRunId,
    },
    state: "error", terminalDisposition: "error",
    openedBySourceEventId: "agent.event.run.error.000", terminalSourceEventId: "agent.event.run.error.001",
    openedAt: recordedAt(errorRunStartedDurableSequence), terminalAt: recordedAt(errorRunTerminalDurableSequence),
  },
];
parentCase.messageBindings = [
  {
    bindingRef: successMessageBindingRef,
    profileRevision,
    sessionId: "session.error",
    presentationRunBindingRef: successRunBindingRef,
    presentationMessageId: successPresentationMessageId,
    resumeSegmentOrdinal: 0,
    state: "ended",
    openedBySourceEventId: "agent.event.run.success.001",
    endedBySourceEventId: `agent.event.run.success.${String(successTextEndOrdinal).padStart(3, "0")}`,
    openedAt: recordedAt(2),
    endedAt: recordedAt(successTextEndOrdinal + 1),
  },
];
parentCase.sessionPrivateRouteFixtures = {
  runs: [
    {
      presentationRunBindingRef: successRunBindingRef,
      internalRunRef: successInternalRunRef,
      parentInternalRunRef: null,
    },
    {
      presentationRunBindingRef: errorRunBindingRef,
      internalRunRef: errorInternalRunRef,
      parentInternalRunRef: successInternalRunRef,
    },
  ],
  messages: [
    {
      presentationMessageBindingRef: successMessageBindingRef,
      internalMessageRef: successInternalMessageRef,
    },
  ],
  provenance: [],
};
const source = (sourceEventId, sourceKind, durableSeq, recordedAt) => ({
  sourceEventId, sourceKind, sessionId: "session.error", streamEpoch: "9", durableSeq,
  projectionVersion: durableSeq, schemaRevision: 1, recordedAt,
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
    "presentation.message.text.ended", successTextEndOrdinal, true,
  ),
  successFrame(
    { type: "RUN_FINISHED", threadId: "thread.session.error", runId: successPresentationRunId },
    "presentation.run.finished", successRunFinishedOrdinal,
  ),
];
const errorStartedAt = recordedAt(errorRunStartedDurableSequence);
const errorTerminalAt = recordedAt(errorRunTerminalDurableSequence);
const errorFrames = [
  runFrame(
    {
      type: "RUN_STARTED", timestamp: Date.parse(errorStartedAt), threadId: "thread.session.error",
      runId: errorPresentationRunId, parentRunId: successPresentationRunId,
    },
    { bindingRef: errorRunBindingRef, source: source("agent.event.run.error.000", "presentation.run.started", String(errorRunStartedDurableSequence), errorStartedAt) },
  ),
  runFrame(
    {
      type: "RUN_ERROR", timestamp: Date.parse(errorTerminalAt),
      message: "The run could not be completed.", code: "RUN_FAILED",
    },
    { bindingRef: errorRunBindingRef, source: source("agent.event.run.error.001", "presentation.run.error", String(errorRunTerminalDurableSequence), errorTerminalAt) },
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
  bindSessionPublicIdentities(contractCase);
  normalizeOwnerPresentationFacts(contractCase);
  opaquifyPresentationIdentities(contractCase);
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
  const publicSourceIds = new Map(
    contractCase.frames.map((frame) => [frame.data.source.sourceEventId, publicSourceEventIdFor(contractCase, frame)]),
  );
  replaceSourceEvidence(
    contractCase.runBindings,
    publicSourceIds,
    ["openedBySourceEventId", "terminalSourceEventId"],
  );
  replaceSourceEvidence(
    contractCase.messageBindings,
    publicSourceIds,
    ["openedBySourceEventId", "endedBySourceEventId"],
  );
  for (const frame of contractCase.frames) {
    frame.data.source.sourceEventId = publicSourceIds.get(frame.data.source.sourceEventId);
    frame.data.source.projectionVersion = String(frame.data.source.projectionVersion);
    if (frame.data.event.name === "kokoro.run.replace.v1") {
      frame.data.event.value.ownerVersion = uint64Maximum;
      delete frame.data.event.value.projectionVersion;
    }
    frame.data.bindingAuthorityDelta = bindingAuthorityDeltaForFrame(contractCase, frame);
    frame.id = issueCursor(frame.data.source);
  }
  contractCase.sessionPrivateRouteFixtures.provenance = corpus.agentSourceFixtures
    .filter(({ baseCaseId }) => baseCaseId === contractCase.id)
    .map(({ source: agentSource }) => {
      const publicSourceEventId = publicSourceIds.get(agentSource.sourceEventRef);
      if (publicSourceEventId === undefined) {
        throw new Error(`Agent private provenance target missing: ${agentSource.sourceEventRef}`);
      }
      return {
        sessionId: contractCase.snapshot.sessionId,
        agentSourceEventRef: agentSource.sourceEventRef,
        publicSourceEventId,
      };
    });
  contractCase.durableRows = contractCase.frames.map((frame) => ({
    rowRef: `presentation-row.${frame.data.source.sourceEventId}`,
    profileRevision: frame.data.profileRevision,
    cursorProfileRevision,
    source: structuredClone(frame.data.source),
    projectionPayload: structuredClone(frame.data),
    projectionPayloadDigest: digest(frame.data),
  }));
  const lastFrame = contractCase.frames.at(-1);
  contractCase.expectedFinalSnapshot = {
    authority: "session-browser-v3-http-snapshot",
    hydrate: true,
    repair: true,
    profileRevision,
    sessionId: contractCase.snapshot.sessionId,
    streamEpoch: contractCase.snapshot.streamEpoch,
    durableSeq: lastFrame.data.source.durableSeq,
    lastRecordedAt: lastFrame.data.source.recordedAt,
    cursor: lastFrame.id,
    runBindings: structuredClone(contractCase.runBindings),
    messageBindings: structuredClone(contractCase.messageBindings),
  };
  contractCase.controlFrame.data.lastDurableCursor = contractCase.frames.at(-1).id;
}
const parentHead = parentCase.frames.at(-1);
const projectedSuccessFrames = parentCase.frames.slice(0, successFrames.length);
const projectedErrorFrames = parentCase.frames.slice(successFrames.length);
const successRunFinishedFrame = projectedSuccessFrames.at(-1);
if (parentHead === undefined || successRunFinishedFrame?.data.event.type !== "RUN_FINISHED") {
  throw new Error("complete Agent candidate corpus frames are required");
}
const sourceFixtureByRef = new Map(corpus.agentSourceFixtures.map((fixture) => [fixture.source.sourceEventRef, fixture]));
const candidateEnvelopeFor = (contractCase, frame) => {
  const provenance = contractCase.sessionPrivateRouteFixtures.provenance.find(
    ({ publicSourceEventId }) => publicSourceEventId === frame.data.source.sourceEventId,
  );
  const fixture = provenance === undefined ? undefined : sourceFixtureByRef.get(provenance.agentSourceEventRef);
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
  ...projectedSuccessFrames.slice(0, -1).map((frame) => ({
    id: envelopeCaseId(frame),
    baseCaseId: parentCase.id,
    sourceEventId: frame.data.source.sourceEventId,
    candidateEnvelope: candidateEnvelopeFor(parentCase, frame),
  })),
  {
    id: "agent-error-run-start-envelope",
    baseCaseId: parentCase.id,
    sourceEventId: projectedErrorFrames[0].data.source.sourceEventId,
    candidateEnvelope: candidateEnvelopeFor(parentCase, projectedErrorFrames[0]),
  },
  {
    id: "agent-run-error-envelope",
    baseCaseId: parentCase.id,
    sourceEventId: projectedErrorFrames[1].data.source.sourceEventId,
    candidateEnvelope: candidateEnvelopeFor(parentCase, projectedErrorFrames[1]),
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
    nextEventRecordedAt: recordedAt(errorRunTerminalDurableSequence + 1),
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
  ...corpus.negativeCases.filter(({ id }) => (
    id !== "m0-interrupted-main-run" &&
    !id.startsWith("binding-delta-") &&
    !id.startsWith("browser-private-") &&
    !id.startsWith("public-source-") &&
    !id.startsWith("custom-run-owner-") &&
    !id.startsWith("session-binding-")
  )),
  {
    id: "session-binding-root-run-missing",
    baseCaseId: parentCase.id,
    mutation: { operation: "set", path: "runBindings.0.sessionRunId", value: null },
    expectedCode: "agui_session_run_binding_missing",
  },
  {
    id: "session-binding-resume-run-conflict",
    baseCaseId: authorityBase.id,
    mutation: {
      operation: "set",
      path: "runBindings.1.sessionRunId",
      value: sessionPublicIdentityFor("run", "attack", 1),
    },
    expectedCode: "agui_resume_session_run_conflict",
  },
  {
    id: "session-binding-message-run-conflict",
    baseCaseId: authorityBase.id,
    mutation: { operation: "set", path: "messageBindings.0.sessionMessageId", value: null },
    expectedCode: "agui_message_binding_schema_invalid",
  },
  {
    id: "session-binding-private-run-equality",
    baseCaseId: parentCase.id,
    mutation: {
      operation: "set",
      path: "runBindings.0.sessionRunId",
      value: parentCase.sessionPrivateRouteFixtures.runs[0].internalRunRef,
    },
    expectedCode: "agui_private_presentation_identity_equal",
  },
  {
    id: "binding-delta-wrong-kind",
    baseCaseId: authorityBase.id,
    mutation: {
      operation: "set",
      path: "frames.0.data.bindingAuthorityDelta",
      value: {
        kind: "message.replace",
        binding: openMessageBinding(authorityBase.messageBindings[0]),
      },
    },
    expectedCode: "agui_binding_delta_kind_invalid",
  },
  {
    id: "binding-delta-wrong-ref",
    baseCaseId: authorityBase.id,
    mutation: {
      operation: "set",
      path: "frames.0.data.bindingAuthorityDelta.binding.bindingRef",
      value: `presentation.run-binding:${"0".repeat(64)}`,
    },
    expectedCode: "agui_binding_delta_ref_conflict",
  },
  {
    id: "binding-delta-wrong-source",
    baseCaseId: authorityBase.id,
    mutation: {
      operation: "set",
      path: "frames.0.data.bindingAuthorityDelta.binding.openedBySourceEventId",
      value: "presentation.event:attack",
    },
    expectedCode: "agui_binding_delta_source_conflict",
  },
  {
    id: "binding-delta-wrong-time",
    baseCaseId: authorityBase.id,
    mutation: {
      operation: "set",
      path: "frames.0.data.bindingAuthorityDelta.binding.openedAt",
      value: "2026-08-01T12:00:00.000Z",
    },
    expectedCode: "agui_binding_delta_time_conflict",
  },
  {
    id: "binding-delta-wrong-state",
    baseCaseId: authorityBase.id,
    mutation: {
      operation: "set",
      path: "frames.0.data.bindingAuthorityDelta.binding",
      value: {
        ...openRunBinding(authorityBase.runBindings[0]),
        state: "finished",
        terminalDisposition: "success",
        terminalSourceEventId: authorityBase.frames[0].data.source.sourceEventId,
        terminalAt: authorityBase.frames[0].data.source.recordedAt,
      },
    },
    expectedCode: "agui_binding_delta_state_conflict",
  },
  {
    id: "binding-delta-future-binding",
    baseCaseId: authorityBase.id,
    mutation: {
      operation: "set",
      path: "frames.0.data.bindingAuthorityDelta.binding",
      value: structuredClone(authorityBase.runBindings[0]),
    },
    expectedCode: "agui_binding_delta_future_evidence",
  },
  {
    id: "browser-private-run-route-smuggling",
    baseCaseId: authorityBase.id,
    mutation: {
      operation: "set",
      path: "frames.0.data.bindingAuthorityDelta.binding.internalRunRef",
      value: "internal.run.smuggled",
    },
    expectedCode: "agui_browser_internal_route_forbidden",
  },
  {
    id: "browser-private-message-route-smuggling",
    baseCaseId: authorityBase.id,
    mutation: {
      operation: "set",
      path: "frames.1.data.bindingAuthorityDelta.binding.internalMessageRef",
      value: "internal.message.smuggled",
    },
    expectedCode: "agui_browser_internal_route_forbidden",
  },
  {
    id: "browser-private-parent-route-smuggling",
    baseCaseId: authorityBase.id,
    mutation: {
      operation: "set",
      path: "frames.0.data.bindingAuthorityDelta.binding.parentLineage.parentInternalRunRef",
      value: "internal.run.parent.smuggled",
    },
    expectedCode: "agui_browser_internal_route_forbidden",
  },
  {
    id: "public-source-agent-prefix-leak",
    baseCaseId: authorityBase.id,
    mutation: {
      operation: "set",
      path: "frames.0.data.source.sourceEventId",
      value: "presentation.event:agent.event.run.leaked",
    },
    expectedCode: "agui_public_source_event_id_invalid",
  },
  {
    id: "public-source-private-ref-equality",
    baseCaseId: parentCase.id,
    mutation: {
      operation: "set",
      path: "sessionPrivateRouteFixtures.provenance.0.publicSourceEventId",
      value: parentCase.sessionPrivateRouteFixtures.provenance[0].agentSourceEventRef,
    },
    expectedCode: "agui_private_provenance_identity_equal",
  },
  {
    id: "public-source-cleartext-axes",
    baseCaseId: authorityBase.id,
    mutation: {
      operation: "set",
      path: "frames.0.data.source.sourceEventId",
      value: `presentation.event:${authorityBase.frames[0].data.source.sessionId}:${authorityBase.frames[0].data.source.streamEpoch}:${authorityBase.frames[0].data.source.durableSeq}`,
    },
    expectedCode: "agui_public_source_event_axes_exposed",
  },
  {
    id: "custom-run-owner-old-projection-version",
    baseCaseId: authorityBase.id,
    mutation: {
      operation: "set",
      path: `frames.${authorityBase.frames.findIndex(({ data }) => data.event.name === "kokoro.run.replace.v1")}.data.event.value`,
      value: {
        presentationRunId: authorityBase.runBindings.at(-1).presentationRunId,
        state: "waiting",
        projectionVersion: 4,
      },
    },
    expectedCode: "agui_custom_run_owner_version_invalid",
  },
  {
    id: "custom-run-owner-version-overflow",
    baseCaseId: authorityBase.id,
    mutation: {
      operation: "set",
      path: `frames.${authorityBase.frames.findIndex(({ data }) => data.event.name === "kokoro.run.replace.v1")}.data.event.value.ownerVersion`,
      value: "18446744073709551616",
    },
    expectedCode: "agui_custom_run_owner_version_invalid",
  },
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
const terminalRevival = corpus.negativeCases.find(({ id }) => id === "terminal-run-revival");
if (terminalRevival !== undefined) terminalRevival.mutation.runBindingRef = authorityBase.runBindings[0].bindingRef;
const endedMessageReopen = corpus.negativeCases.find(({ id }) => id === "ended-message-reopen");
if (endedMessageReopen !== undefined) endedMessageReopen.mutation.messageBindingRef = authorityBase.messageBindings[0].bindingRef;
const resumeParentConfusion = corpus.negativeCases.find(({ id }) => id === "resume-parent-lineage-confusion");
if (resumeParentConfusion !== undefined) {
  resumeParentConfusion.mutation.value = authorityBase.runBindings[0].presentationRunId;
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
