import assert from "node:assert/strict";
import { execFile } from "node:child_process";
import { createCipheriv, createHash, randomBytes } from "node:crypto";
import { cp, mkdir, mkdtemp, readFile, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { resolve } from "node:path";
import test from "node:test";
import { promisify } from "node:util";

import {
  AguiPresentationContractError,
  applyCorpusMutation,
  validateConformanceCase,
  validateRepository,
} from "./check-agui-presentation.mjs";

const repositoryRoot = resolve(import.meta.dirname, "../..");
const execFileAsync = promisify(execFile);
const corpusGenerator = resolve(import.meta.dirname, "generate-agui-presentation-corpus.mjs");
const cursorKeyRevision = "agui-conformance-2026-08";
const cursorProfileRevision = "opaque-session-cursor-v1";
const profileRevision = "kokoro-agui-presentation.v1";
const cursorKey = createHash("sha256").update("kokoro-agui-presentation-public-conformance-key-v1", "utf8").digest();
const cursorAad = Buffer.from(`kokoro.session.browser.cursor.v1\u0000${cursorKeyRevision}`, "utf8");

async function readJson(path) {
  return JSON.parse(await readFile(resolve(repositoryRoot, path), "utf8"));
}

const fixtureFiles = [
  "contract/package.json",
  "contract/pnpm-lock.yaml",
  "contract/corpus/agui-presentation-v1.json",
  "contract/registry/agui-agent-candidate-profile-v1.yaml",
  "contract/registry/agui-presentation-mapping-v1.yaml",
  "contract/registry/agui-upstream-profile.yaml",
  "contract/spec/kokoro-agui-presentation-event-v1.yaml",
  "contract/spec/agent-agui-event-candidate-v1.yaml",
  "contract/spec/agent-agui-candidate-envelope-v1.yaml",
  "contract/spec/presentation-binding-authority-delta-v1.yaml",
  "contract/spec/presentation-message-binding-v1.yaml",
  "contract/spec/presentation-run-binding-v1.yaml",
  "contract/spec/session-agui-projection-payload-v1.yaml",
  "contract/spec/session-agui-presentation-row-v1.yaml",
  "contract/spec/session-agui-stream-v1.yaml",
  "contract/spec/session-agui-snapshot-authority-v1.yaml",
];

async function repositoryFixture() {
  const root = await mkdtemp(resolve(tmpdir(), "kokoro-agui-contract-"));
  for (const relative of fixtureFiles) {
    const target = resolve(root, relative);
    await mkdir(resolve(target, ".."), { recursive: true });
    await cp(resolve(repositoryRoot, relative), target);
  }
  return root;
}

async function writeJson(root, relative, value) {
  await writeFile(resolve(root, relative), `${JSON.stringify(value, null, 2)}\n`);
}

function clone(value) {
  return structuredClone(value);
}

function canonical(value) {
  if (value === null || typeof value === "boolean" || typeof value === "number" || typeof value === "string") return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map(canonical).join(",")}]`;
  return `{${Object.keys(value).sort().map((name) => `${JSON.stringify(name)}:${canonical(value[name])}`).join(",")}}`;
}

function projectionDigest(value) {
  return `sha256:${createHash("sha256").update(canonical(value), "utf8").digest("hex")}`;
}

function resignCandidateEnvelope(envelope) {
  envelope.eventDigest = projectionDigest(envelope.event);
  const route = envelope.source.route;
  const material = [
    envelope.profileRevision,
    route.internalRunRef,
    route.internalThreadRef,
    route.internalMessageRef ?? "",
    envelope.source.sourceEventRef,
    envelope.source.sourceOrdinal,
    envelope.source.recordedAt,
    envelope.eventDigest,
  ].join("\u0000");
  envelope.candidateRef = `agui_candidate:sha256:${createHash("sha256").update(material, "utf8").digest("hex")}`;
}

function issueRandomCursor({ sessionId, streamEpoch, durableSeq }) {
  const claims = { version: 1, kind: "stream", sessionId, streamEpoch, durableSeq, profileRevision, cursorProfileRevision };
  const iv = randomBytes(12);
  const cipher = createCipheriv("aes-256-gcm", cursorKey, iv);
  cipher.setAAD(cursorAad);
  const ciphertext = Buffer.concat([cipher.update(Buffer.from(canonical(claims), "utf8")), cipher.final()]);
  return ["v1", cursorKeyRevision, iv.toString("base64url"), ciphertext.toString("base64url"), cipher.getAuthTag().toString("base64url")].join(".");
}

function transformStrings(value, replacements) {
  if (typeof value === "string") return replacements.get(value) ?? value;
  if (Array.isArray(value)) return value.map((entry) => transformStrings(entry, replacements));
  if (value === null || typeof value !== "object") return value;
  return Object.fromEntries(Object.entries(value).map(([key, child]) => [key, transformStrings(child, replacements)]));
}

function distinctPositiveCase(base, { suffix, sessionId, streamEpoch }) {
  const replacements = new Map();
  if (base.snapshot.sessionId !== sessionId) replacements.set(base.snapshot.sessionId, sessionId);
  for (const binding of base.runBindings) {
    for (const field of ["bindingRef", "presentationThreadId", "presentationRunId", "openedBySourceEventId", "terminalSourceEventId"]) {
      if (binding[field] !== null) replacements.set(binding[field], `${binding[field]}.${suffix}`);
    }
  }
  for (const binding of base.messageBindings) {
    for (const field of ["bindingRef", "presentationMessageId", "openedBySourceEventId", "endedBySourceEventId"]) {
      if (binding[field] !== null) replacements.set(binding[field], `${binding[field]}.${suffix}`);
    }
  }
  for (const route of base.sessionPrivateRouteFixtures.runs) {
    for (const field of ["internalRunRef", "parentInternalRunRef"]) {
      if (route[field] !== null) replacements.set(route[field], `${route[field]}.${suffix}`);
    }
  }
  for (const route of base.sessionPrivateRouteFixtures.messages) {
    replacements.set(route.internalMessageRef, `${route.internalMessageRef}.${suffix}`);
  }
  for (const frame of base.frames) replacements.set(frame.data.source.sourceEventId, `${frame.data.source.sourceEventId}.${suffix}`);
  for (const row of base.durableRows) replacements.set(row.rowRef, `${row.rowRef}.${suffix}`);

  const candidate = transformStrings(clone(base), replacements);
  candidate.id = `${base.id}.${suffix}`;
  candidate.snapshot.sessionId = sessionId;
  candidate.snapshot.streamEpoch = streamEpoch;
  candidate.grantBinding.sessionId = sessionId;
  for (const frame of candidate.frames) {
    frame.data.source.sessionId = sessionId;
    frame.data.source.streamEpoch = streamEpoch;
    frame.id = issueRandomCursor(frame.data.source);
  }
  candidate.snapshot.cursor = issueRandomCursor({ sessionId, streamEpoch, durableSeq: candidate.snapshot.durableSeq });
  candidate.request.lastEventId = candidate.snapshot.cursor;
  candidate.request.queryCursor = candidate.snapshot.cursor;
  candidate.durableRows = candidate.frames.map((frame, index) => ({
    rowRef: candidate.durableRows[index].rowRef,
    profileRevision,
    cursorProfileRevision,
    source: clone(frame.data.source),
    projectionPayload: clone(frame.data),
    projectionPayloadDigest: projectionDigest(frame.data),
  }));
  candidate.controlFrame.data.sessionId = sessionId;
  candidate.controlFrame.data.streamEpoch = streamEpoch;
  candidate.controlFrame.data.lastDurableCursor = candidate.frames.at(-1).id;
  candidate.expectedFinalSnapshot.sessionId = sessionId;
  candidate.expectedFinalSnapshot.streamEpoch = streamEpoch;
  candidate.expectedFinalSnapshot.cursor = candidate.frames.at(-1).id;
  return candidate;
}

function resignCaseCursors(contractCase) {
  contractCase.snapshot.cursor = issueRandomCursor({
    sessionId: contractCase.snapshot.sessionId,
    streamEpoch: contractCase.snapshot.streamEpoch,
    durableSeq: contractCase.snapshot.durableSeq,
  });
  contractCase.request.lastEventId = contractCase.snapshot.cursor;
  contractCase.request.queryCursor = contractCase.snapshot.cursor;
  for (const frame of contractCase.frames) frame.id = issueRandomCursor(frame.data.source);
  contractCase.controlFrame.data.lastDurableCursor = contractCase.frames.at(-1).id;
}

test("validates the pinned upstream profile and complete presentation corpus", async () => {
  const result = await validateRepository({ root: repositoryRoot });
  assert.deepEqual(result, {
    positiveCases: 2,
    negativeCases: 20,
    durableFrames: 41,
    bindingReplacementDeltas: 14,
    mappingsCovered: 22,
    agentCandidates: 33,
    agentSourceFixtures: 15,
    agentCandidateEnvelopeCases: 14,
    agentCandidateProjectionCases: 1,
    snapshotAuthorityCases: 1,
    snapshotAuthorityNegativeCases: 6,
  });
});

test("requires one closed full-replacement binding authority delta in every durable payload", async () => {
  const payloadSchema = await readJson("contract/spec/session-agui-projection-payload-v1.yaml");
  const deltaSchema = await readJson("contract/spec/presentation-binding-authority-delta-v1.yaml");
  assert.ok(payloadSchema.required.includes("bindingAuthorityDelta"));
  assert.deepEqual(
    deltaSchema.oneOf.map(({ $ref }) => $ref),
    ["#/$defs/none", "#/$defs/runReplace", "#/$defs/messageReplace"],
  );
  assert.deepEqual(
    [deltaSchema.$defs.none, deltaSchema.$defs.runReplace, deltaSchema.$defs.messageReplace]
      .map(({ properties }) => properties.kind.const),
    ["none", "run.replace", "message.replace"],
  );
  assert.equal(deltaSchema.$defs.runReplace.properties.binding.$ref, "https://contracts.kokoro.invalid/presentation-run-binding.v1.schema.json");
  assert.equal(deltaSchema.$defs.messageReplace.properties.binding.$ref, "https://contracts.kokoro.invalid/presentation-message-binding.v1.schema.json");
});

test("keeps Agent internal route topology out of browser binding snapshots and deltas", async () => {
  const runSchema = await readJson("contract/spec/presentation-run-binding-v1.yaml");
  const messageSchema = await readJson("contract/spec/presentation-message-binding-v1.yaml");
  assert.equal(Object.hasOwn(runSchema.properties, "internalRunRef"), false);
  assert.equal(Object.hasOwn(runSchema.properties.parentLineage.properties, "parentInternalRunRef"), false);
  assert.equal(Object.hasOwn(messageSchema.properties, "internalMessageRef"), false);

  const containsInternalKey = (value) => {
    if (Array.isArray(value)) return value.some(containsInternalKey);
    if (value === null || typeof value !== "object") return false;
    return Object.entries(value).some(
      ([key, child]) => /^(?:internal|parentInternal)/u.test(key) || containsInternalKey(child),
    );
  };
  const corpus = await readJson("contract/corpus/agui-presentation-v1.json");
  for (const contractCase of corpus.positiveCases) {
    assert.equal(containsInternalKey(contractCase.expectedFinalSnapshot), false, contractCase.id);
    for (const frame of contractCase.frames) {
      assert.equal(containsInternalKey(frame.data), false, `${contractCase.id}:${frame.data.source.durableSeq}`);
    }
    assert.ok(contractCase.sessionPrivateRouteFixtures.runs.length > 0, contractCase.id);
  }

  for (const [field, value] of [
    ["internalRunRef", "internal.run.leaked"],
    ["internalMessageRef", "internal.message.leaked"],
    ["parentInternalRunRef", "internal.run.parent.leaked"],
  ]) {
    const candidate = clone(corpus.positiveCases[0]);
    const frame = field === "internalMessageRef" ? candidate.frames[1] : candidate.frames[0];
    if (field === "parentInternalRunRef") frame.data.bindingAuthorityDelta.binding.parentLineage[field] = value;
    else frame.data.bindingAuthorityDelta.binding[field] = value;
    assert.throws(() => validateConformanceCase(candidate), /agui_browser_internal_route_forbidden/u, field);
  }
});

test("uses decimal positive-uint64 projection revisions on every Session-owned source envelope", async () => {
  const payloadSchema = await readJson("contract/spec/session-agui-projection-payload-v1.yaml");
  const rowSchema = await readJson("contract/spec/session-agui-presentation-row-v1.yaml");
  assert.deepEqual(payloadSchema.properties.source.properties.projectionVersion, { $ref: "#/$defs/positiveUint64" });
  assert.deepEqual(rowSchema.properties.source.properties.projectionVersion, { $ref: "#/$defs/positiveUint64" });

  const corpus = await readJson("contract/corpus/agui-presentation-v1.json");
  for (const contractCase of corpus.positiveCases) {
    for (const frame of contractCase.frames) {
      assert.match(frame.data.source.projectionVersion, /^[1-9][0-9]{0,19}$/u);
    }
  }

  for (const illegal of [1, "0", "01", "18446744073709551616"]) {
    const candidate = clone(corpus.positiveCases[0]);
    candidate.frames[0].data.source.projectionVersion = illegal;
    assert.throws(
      () => validateConformanceCase(candidate),
      (error) => error instanceof AguiPresentationContractError && error.code === "agui_projection_version_invalid",
      String(illegal),
    );
  }
});

test("freezes binding authority delta policy per source mapping and rebuilds from an empty snapshot", async () => {
  const registry = await readJson("contract/registry/agui-presentation-mapping-v1.yaml");
  const expectedKind = (entry) => {
    if (["RUN_STARTED", "RUN_FINISHED", "RUN_ERROR"].includes(entry.eventType)) return "run.replace";
    if (["TEXT_MESSAGE_START", "TEXT_MESSAGE_END"].includes(entry.eventType)) return "message.replace";
    return "none";
  };
  for (const entry of registry.mappings) {
    assert.equal(entry.bindingAuthorityDeltaKind, expectedKind(entry), entry.sourceKind);
  }
  assert.deepEqual(registry.projectionPolicy.bindingAuthorityDelta, {
    cardinality: "exactly-one-required",
    atomicity: "same-projection-payload-and-durable-row",
    mutation: "complete-replacement-only",
    patch: "forbidden",
  });
  assert.deepEqual(registry.projectionPolicy.sourceProjectionVersion, {
    wire: "positive-uint64-decimal-string",
    semantic: "session-projection-revision",
    javascriptNumber: "forbidden",
  });

  const corpus = await readJson("contract/corpus/agui-presentation-v1.json");
  for (const contractCase of corpus.positiveCases) {
    assert.equal(contractCase.snapshot.durableSeq, "0", contractCase.id);
    const runBindings = new Map();
    const messageBindings = new Map();
    for (const frame of contractCase.frames) {
      const delta = frame.data.bindingAuthorityDelta;
      assert.ok(delta, `${contractCase.id}:${frame.data.source.durableSeq}`);
      if (delta.kind === "run.replace") runBindings.set(delta.binding.bindingRef, delta.binding);
      if (delta.kind === "message.replace") messageBindings.set(delta.binding.bindingRef, delta.binding);
    }
    assert.deepEqual([...runBindings.values()], contractCase.expectedFinalSnapshot.runBindings, contractCase.id);
    assert.deepEqual([...messageBindings.values()], contractCase.expectedFinalSnapshot.messageBindings, contractCase.id);
    assert.equal(contractCase.expectedFinalSnapshot.durableSeq, contractCase.frames.at(-1).data.source.durableSeq);
    assert.equal(contractCase.expectedFinalSnapshot.lastRecordedAt, contractCase.frames.at(-1).data.source.recordedAt);
    assert.equal(contractCase.expectedFinalSnapshot.cursor, contractCase.frames.at(-1).id);
  }
});

test("freezes independent binding delta attacks for kind, ref, source, time, state and future evidence", async () => {
  const corpus = await readJson("contract/corpus/agui-presentation-v1.json");
  assert.deepEqual(
    corpus.negativeCases
      .filter(({ id }) => id.startsWith("binding-delta-"))
      .map(({ id, expectedCode }) => [id, expectedCode]),
    [
      ["binding-delta-wrong-kind", "agui_binding_delta_kind_invalid"],
      ["binding-delta-wrong-ref", "agui_binding_delta_ref_conflict"],
      ["binding-delta-wrong-source", "agui_binding_delta_source_conflict"],
      ["binding-delta-wrong-time", "agui_binding_delta_time_conflict"],
      ["binding-delta-wrong-state", "agui_binding_delta_state_conflict"],
      ["binding-delta-future-binding", "agui_binding_delta_future_evidence"],
    ],
  );
});

test("freezes browser attacks that smuggle Session-private routes through binding replacements", async () => {
  const corpus = await readJson("contract/corpus/agui-presentation-v1.json");
  assert.deepEqual(
    corpus.negativeCases
      .filter(({ id }) => id.startsWith("browser-private-"))
      .map(({ id, expectedCode }) => [id, expectedCode]),
    [
      ["browser-private-run-route-smuggling", "agui_browser_internal_route_forbidden"],
      ["browser-private-message-route-smuggling", "agui_browser_internal_route_forbidden"],
      ["browser-private-parent-route-smuggling", "agui_browser_internal_route_forbidden"],
    ],
  );
});

test("checks deterministic corpus generation without writing and reports byte drift", async () => {
  const corpusPath = resolve(repositoryRoot, "contract/corpus/agui-presentation-v1.json");
  const before = await readFile(corpusPath, "utf8");
  const checked = await execFileAsync(process.execPath, [corpusGenerator, "--check", "--root", repositoryRoot]);
  assert.match(checked.stdout, /agui_presentation_corpus_ok/u);
  assert.equal(await readFile(corpusPath, "utf8"), before);

  const root = await repositoryFixture();
  const corpus = JSON.parse(await readFile(resolve(root, "contract/corpus/agui-presentation-v1.json"), "utf8"));
  corpus.positiveCases[0].frames[0].id = "drifted-cursor";
  await writeJson(root, "contract/corpus/agui-presentation-v1.json", corpus);
  await assert.rejects(
    execFileAsync(process.execPath, [corpusGenerator, "--check", "--root", root]),
    (error) => error.code === 1 && /agui_presentation_corpus_drift/u.test(error.stderr),
  );
});

test("pins one official upstream commit and assigns explicit Agent, Session and Web roles", async () => {
  const profile = await readJson("contract/registry/agui-upstream-profile.yaml");
  assert.equal(profile.upstream.commit, "54f13419055b4d0f442c71e1efab18b310982ce1");
  assert.deepEqual(profile.typescript.core, {
    package: "@ag-ui/core",
    version: "0.0.57",
    integrity: "sha512-gho1OWjNE6E3Rl7ZEZ1wr2CEpUHjLFU0FqzCZZk439TicLu+BfLCMkMokB07bMGlRmbJ60hM6LW60iOVauCx+Q==",
    schemaAuthority: true,
  });
  assert.equal(profile.typescript.client.transportRole, "forbidden");
  assert.deepEqual(profile.python.source, {
    kind: "git",
    repository: "https://github.com/ag-ui-protocol/ag-ui",
    subdirectory: "sdks/python",
    commit: "54f13419055b4d0f442c71e1efab18b310982ce1",
  });
  assert.deepEqual(profile.roles.agent, {
    repository: "kokoro-agent",
    internalEventCandidateProducer: true,
    internalEventCandidateConsumer: false,
    strictPresentationConsumer: false,
    browserEndpoint: false,
    durableProjectionOwner: false,
    cursorOwner: false,
    rawPassthrough: false,
  });
  assert.equal(profile.roles.session.internalEventCandidateConsumer, true);
  assert.equal(profile.roles.session.durableProjectionOwner, true);
  assert.equal(profile.roles.session.cursorOwner, true);
  assert.equal(profile.roles.web.strictPresentationConsumer, true);
  assert.equal(profile.rendering.assistantUi.version, "0.14.28");
});

test("freezes the Agent event-candidate profile below the browser presentation subset", async () => {
  const candidate = await readJson("contract/registry/agui-agent-candidate-profile-v1.yaml");
  assert.deepEqual(candidate.allowedEventTypes, [
    "RUN_STARTED", "RUN_FINISHED", "RUN_ERROR",
    "TEXT_MESSAGE_START", "TEXT_MESSAGE_CONTENT", "TEXT_MESSAGE_END",
    "ACTIVITY_SNAPSHOT",
  ]);
  assert.deepEqual(candidate.allowedActivityTypes, [
    "kokoro.safe-summary.v1", "kokoro.tool-preview.v1", "kokoro.hitl.v1", "kokoro.plan.v1",
    "kokoro.subagent.v1", "kokoro.media.v1", "kokoro.notice.v1", "kokoro.error.v1",
  ]);
  assert.ok(candidate.forbiddenEventTypes.includes("CUSTOM"));
  assert.deepEqual(candidate.forbiddenOwnerActivityTypes, ["kokoro.artifact.v1", "kokoro.cost.v1"]);
  for (const field of ["rawEvent", "input", "result", "extra"]) assert.ok(candidate.forbiddenFields.includes(field));
  assert.equal(candidate.terminalPolicy.runFinished, "success-only");
  assert.equal(candidate.identityPolicy.sourceOrdinal, "uint64-decimal-string-strictly-increasing-per-run-starts-at-zero");
  assert.equal(candidate.identityPolicy.sourceFixtureOrder, "owner-log-order-within-internalRunRef");
  assert.equal(candidate.identityPolicy.internalThreadRef, "agent.thread:-branded-opaque-owner-ref-established-by-zero-run-start");
  assert.equal(candidate.eventScopePolicy.runError, "outer-route-matches-zero-run-start-thread-authority");
  assert.equal(candidate.eventScopePolicy.runStartedAndFinished, "threadId=internalThreadRef-and-runId=internalRunRef-and-no-parentRunId");
  assert.equal(candidate.activation.runtimeImplemented, false);
  assert.equal(candidate.envelopeSchema, "https://contracts.kokoro.invalid/agent-agui-candidate-envelope.v1.schema.json");
});

test("freezes a closed Agent candidate envelope without browser or business identity axes", async () => {
  const corpus = await readJson("contract/corpus/agui-presentation-v1.json");
  assert.ok(Array.isArray(corpus.agentCandidateProjectionCases));
  assert.equal(corpus.agentSourceFixtures.length, 15);
  assert.equal(corpus.agentCandidateEnvelopeCases.length, 14);
  assert.deepEqual(
    corpus.agentCandidateEnvelopeCases.map(({ candidateEnvelope }) => candidateEnvelope.event.type),
    [
      "RUN_STARTED", "TEXT_MESSAGE_START", "TEXT_MESSAGE_CONTENT",
      "ACTIVITY_SNAPSHOT", "ACTIVITY_SNAPSHOT", "ACTIVITY_SNAPSHOT", "ACTIVITY_SNAPSHOT",
      "ACTIVITY_SNAPSHOT", "ACTIVITY_SNAPSHOT", "ACTIVITY_SNAPSHOT", "ACTIVITY_SNAPSHOT",
      "TEXT_MESSAGE_END", "RUN_STARTED", "RUN_ERROR",
    ],
  );
  const envelope = corpus.agentCandidateProjectionCases[0].candidateEnvelope;
  assert.equal(envelope.profileRevision, "kokoro-agent-agui-candidate.v1");
  assert.deepEqual(envelope.event.outcome, { type: "success" });
  assert.match(envelope.eventDigest, /^sha256:[0-9a-f]{64}$/u);
  for (const forbidden of ["siteId", "userId", "sessionId", "cursor", "sseId", "result"]) {
    assert.equal(Object.hasOwn(envelope, forbidden), false, forbidden);
  }
});

test("requires one canonical Agent envelope for every declared text event arm", async () => {
  const root = await repositoryFixture();
  const corpus = JSON.parse(await readFile(resolve(root, "contract/corpus/agui-presentation-v1.json"), "utf8"));
  const removedIndex = corpus.agentCandidateEnvelopeCases.findIndex(
    ({ candidateEnvelope }) => candidateEnvelope.event.type === "TEXT_MESSAGE_START",
  );
  const [removed] = corpus.agentCandidateEnvelopeCases.splice(removedIndex, 1);
  corpus.agentSourceFixtures = corpus.agentSourceFixtures.filter(
    ({ source }) => source.sourceEventRef !== removed.sourceEventId,
  );
  await writeJson(root, "contract/corpus/agui-presentation-v1.json", corpus);

  await assert.rejects(validateRepository({ root }), /agui_agent_candidate_semantic_coverage_invalid/u);
});

test("requires one canonical Agent envelope for every declared activity discriminator", async () => {
  const root = await repositoryFixture();
  const corpus = JSON.parse(await readFile(resolve(root, "contract/corpus/agui-presentation-v1.json"), "utf8"));
  const removedIndex = corpus.agentCandidateEnvelopeCases.findIndex(
    ({ candidateEnvelope }) => candidateEnvelope.event.activityType === "kokoro.hitl.v1",
  );
  const [removed] = corpus.agentCandidateEnvelopeCases.splice(removedIndex, 1);
  corpus.agentSourceFixtures = corpus.agentSourceFixtures.filter(
    ({ source }) => source.sourceEventRef !== removed.sourceEventId,
  );
  await writeJson(root, "contract/corpus/agui-presentation-v1.json", corpus);

  await assert.rejects(validateRepository({ root }), /agui_agent_candidate_activity_coverage_invalid/u);
});

test("keeps Agent source identity and ordinal authority independent from Session durable sequence", async () => {
  const corpus = await readJson("contract/corpus/agui-presentation-v1.json");
  const baseById = new Map(corpus.positiveCases.map((entry) => [entry.id, entry]));
  const byRun = new Map();
  const agentOrdinals = [];
  const sessionSequences = [];
  for (const fixture of corpus.agentSourceFixtures) {
    assert.match(fixture.source.sourceEventRef, /^agent\.event\./u);
    const base = baseById.get(fixture.baseCaseId);
    assert.match(fixture.source.route.internalThreadRef, /^agent\.thread:[A-Za-z0-9][A-Za-z0-9._:-]*$/u);
    const frame = base.frames.find(({ data }) => data.source.sourceEventId === fixture.source.sourceEventRef);
    assert.ok(frame, fixture.source.sourceEventRef);
    agentOrdinals.push(fixture.source.sourceOrdinal);
    sessionSequences.push(frame.data.source.durableSeq);
    const run = fixture.source.route.internalRunRef;
    const group = byRun.get(run) ?? { threadRef: fixture.source.route.internalThreadRef, ordinals: [] };
    assert.equal(fixture.source.route.internalThreadRef, group.threadRef);
    group.ordinals.push(BigInt(fixture.source.sourceOrdinal));
    byRun.set(run, group);
  }
  assert.notDeepEqual(agentOrdinals, sessionSequences);
  for (const { ordinals } of byRun.values()) {
    assert.equal(ordinals[0], 0n);
    for (let index = 1; index < ordinals.length; index += 1) assert.ok(ordinals[index] > ordinals[index - 1]);
  }
});

test("binds every same-run candidate to the zero-ordinal RUN_STARTED thread authority", async () => {
  const root = await repositoryFixture();
  const corpus = JSON.parse(await readFile(resolve(root, "contract/corpus/agui-presentation-v1.json"), "utf8"));
  const envelopeCase = corpus.agentCandidateEnvelopeCases.find(({ id }) => id === "agent-run-error-envelope");
  const fixture = corpus.agentSourceFixtures.find(({ source }) => source.sourceEventRef === envelopeCase.sourceEventId);
  fixture.source.route.internalThreadRef = "agent.thread:attacker";
  envelopeCase.candidateEnvelope.source.route.internalThreadRef = "agent.thread:attacker";
  resignCandidateEnvelope(envelopeCase.candidateEnvelope);
  await writeJson(root, "contract/corpus/agui-presentation-v1.json", corpus);
  await assert.rejects(validateRepository({ root }), /agui_agent_candidate_thread_authority_invalid/u);
});

test("rejects a Session-shaped ref at the Agent owner-thread boundary", async () => {
  const root = await repositoryFixture();
  const corpus = JSON.parse(await readFile(resolve(root, "contract/corpus/agui-presentation-v1.json"), "utf8"));
  const envelopeCase = corpus.agentCandidateEnvelopeCases.find(({ id }) => id === "agent-run-start-envelope");
  const fixture = corpus.agentSourceFixtures.find(({ source }) => source.sourceEventRef === envelopeCase.sourceEventId);
  fixture.source.route.internalThreadRef = "thread.session.01";
  envelopeCase.candidateEnvelope.source.route.internalThreadRef = "thread.session.01";
  envelopeCase.candidateEnvelope.event.threadId = "thread.session.01";
  resignCandidateEnvelope(envelopeCase.candidateEnvelope);
  await writeJson(root, "contract/corpus/agui-presentation-v1.json", corpus);
  await assert.rejects(validateRepository({ root }), /agui_agent_candidate_thread_authority_invalid/u);
});

test("rejects duplicate, nonzero-starting and non-increasing Agent source fixtures", async () => {
  for (const [mutate, code] of [
    [
      (fixtures) => { fixtures[0].source.sourceOrdinal = "1"; },
      /agui_agent_candidate_source_ordinal_start_invalid/u,
    ],
    [
      (fixtures) => { fixtures[1].source.sourceOrdinal = fixtures[0].source.sourceOrdinal; },
      /agui_agent_candidate_source_ordinal_not_increasing/u,
    ],
    [
      (fixtures) => { fixtures[1].source.sourceEventRef = fixtures[0].source.sourceEventRef; },
      /agui_agent_candidate_source_ref_duplicate/u,
    ],
  ]) {
    const root = await repositoryFixture();
    const corpus = JSON.parse(await readFile(resolve(root, "contract/corpus/agui-presentation-v1.json"), "utf8"));
    mutate(corpus.agentSourceFixtures);
    await writeJson(root, "contract/corpus/agui-presentation-v1.json", corpus);
    await assert.rejects(validateRepository({ root }), code);
  }
});

test("recomputes Agent candidate digest, identity, time and route semantics fail closed", async () => {
  const attacks = [
    {
      code: /agui_agent_candidate_event_digest_invalid/u,
      mutate(envelope) { envelope.eventDigest = `sha256:${"0".repeat(64)}`; },
    },
    {
      code: /agui_agent_candidate_ref_invalid/u,
      mutate(envelope) { envelope.candidateRef = `agui_candidate:sha256:${"0".repeat(64)}`; },
    },
    {
      code: /agui_agent_candidate_recorded_at_invalid/u,
      mutate(envelope) { envelope.source.recordedAt = "2026-08-01T12:00:27.000Z"; resignCandidateEnvelope(envelope); },
    },
    {
      code: /agui_agent_candidate_run_route_invalid/u,
      mutate(envelope) { envelope.source.route.internalRunRef = "internal.run.other"; resignCandidateEnvelope(envelope); },
    },
    {
      code: /agui_agent_candidate_message_route_invalid/u,
      mutate(envelope) {
        envelope.source.route.internalMessageRef = "internal.message.other";
        envelope.event = {
          type: "TEXT_MESSAGE_START",
          timestamp: Date.parse(envelope.source.recordedAt),
          messageId: "internal.message.expected",
          role: "assistant",
        };
        resignCandidateEnvelope(envelope);
      },
    },
    {
      code: /agui_agent_candidate_envelope_schema_invalid/u,
      mutate(envelope) { envelope.source.sourceOrdinal = "01"; resignCandidateEnvelope(envelope); },
    },
    {
      code: /agui_canonical_unicode_invalid/u,
      mutate(envelope) {
        envelope.source.route.internalMessageRef = "internal.message.unicode";
        envelope.event = {
          type: "TEXT_MESSAGE_CONTENT",
          timestamp: Date.parse(envelope.source.recordedAt),
          messageId: "internal.message.unicode",
          delta: "\ud800",
        };
        resignCandidateEnvelope(envelope);
      },
    },
  ];
  for (const attack of attacks) {
    const root = await repositoryFixture();
    const corpus = JSON.parse(await readFile(resolve(root, "contract/corpus/agui-presentation-v1.json"), "utf8"));
    attack.mutate(corpus.agentCandidateProjectionCases[0].candidateEnvelope);
    await writeJson(root, "contract/corpus/agui-presentation-v1.json", corpus);
    await assert.rejects(validateRepository({ root }), attack.code);
  }

  for (const field of ["siteId", "userId", "sessionId", "cursor", "sseId", "sseEvent"]) {
    const root = await repositoryFixture();
    const corpus = JSON.parse(await readFile(resolve(root, "contract/corpus/agui-presentation-v1.json"), "utf8"));
    corpus.agentCandidateProjectionCases[0].candidateEnvelope[field] = "forbidden";
    await writeJson(root, "contract/corpus/agui-presentation-v1.json", corpus);
    await assert.rejects(validateRepository({ root }), /agui_agent_candidate_envelope_schema_invalid/u);
  }
});

test("forbids Agent RUN_STARTED parentRunId until Session binding authority derives it", async () => {
  const checkedIn = await readJson("contract/corpus/agui-presentation-v1.json");
  const derived = checkedIn.agentCandidateEnvelopeCases.find(({ id }) => id === "agent-error-run-start-envelope");
  assert.equal(Object.hasOwn(derived.candidateEnvelope.event, "parentRunId"), false);
  const base = checkedIn.positiveCases.find(({ id }) => id === derived.baseCaseId);
  const projectedFrame = base.frames.find(({ data }) => data.source.sourceEventId === derived.sourceEventId);
  assert.equal(projectedFrame.data.event.parentRunId, "presentation.run.error.parent.segment.0");

  const root = await repositoryFixture();
  const corpus = JSON.parse(await readFile(resolve(root, "contract/corpus/agui-presentation-v1.json"), "utf8"));
  const envelope = corpus.agentCandidateEnvelopeCases.find(({ candidateEnvelope }) => candidateEnvelope.event.type === "RUN_STARTED").candidateEnvelope;
  envelope.event.parentRunId = "internal.run.untrusted-parent";
  resignCandidateEnvelope(envelope);
  await writeJson(root, "contract/corpus/agui-presentation-v1.json", corpus);
  await assert.rejects(validateRepository({ root }), /agui_agent_candidate_envelope_schema_invalid/u);
});

test("freezes snapshot lastRecordedAt as the durable head time watermark", async () => {
  const corpus = await readJson("contract/corpus/agui-presentation-v1.json");
  assert.equal(corpus.positiveCases[0].snapshot.durableSeq, "0");
  assert.equal(corpus.positiveCases[0].snapshot.lastRecordedAt, null);
  const snapshotSchema = await readJson("contract/spec/session-agui-snapshot-authority-v1.yaml");
  assert.ok(snapshotSchema.required.includes("runBindings"));
  assert.ok(snapshotSchema.required.includes("messageBindings"));
  assert.equal(snapshotSchema.properties.runBindings.maxItems, 256);
  assert.equal(snapshotSchema.properties.messageBindings.maxItems, 512);
  assert.ok(Array.isArray(corpus.snapshotAuthorityCases));
  assert.equal(corpus.snapshotAuthorityCases[0].baseCaseId, "safe-run-error");
  assert.deepEqual(
    corpus.snapshotAuthorityCases[0].snapshot.runBindings.map(({ state, terminalDisposition }) => [state, terminalDisposition]),
    [["finished", "success"], ["error", "error"]],
  );
  assert.equal(corpus.snapshotAuthorityCases[0].snapshot.lastRecordedAt, "2026-08-01T13:00:15.000Z");
  assert.equal(corpus.snapshotAuthorityCases[0].nextEventRecordedAt, "2026-08-01T13:00:16.000Z");

  const illegalZeroHead = clone(corpus.positiveCases[0]);
  illegalZeroHead.snapshot.lastRecordedAt = "2026-08-01T12:00:00.000Z";
  assert.throws(() => validateConformanceCase(illegalZeroHead), /agui_snapshot_time_watermark_invalid/u);

  const missingNonzeroHead = clone(corpus.positiveCases[0]);
  missingNonzeroHead.snapshot.durableSeq = "1";
  missingNonzeroHead.snapshot.lastRecordedAt = null;
  assert.throws(() => validateConformanceCase(missingNonzeroHead), /agui_snapshot_time_watermark_invalid/u);
});

test("keeps every M0 conformance run on Session-producible terminal states", async () => {
  const corpus = await readJson("contract/corpus/agui-presentation-v1.json");
  for (const contractCase of corpus.positiveCases) {
    for (const binding of contractCase.runBindings) {
      assert.ok(
        (binding.state === "open" && binding.terminalDisposition === null) ||
        (binding.state === "finished" && binding.terminalDisposition === "success") ||
        (binding.state === "error" && binding.terminalDisposition === "error"),
        `${contractCase.id}:${binding.bindingRef}`,
      );
    }
  }

  const illegal = clone(corpus.positiveCases[0]);
  illegal.runBindings[0].terminalDisposition = "interrupted";
  assert.throws(() => validateConformanceCase(illegal), /agui_run_terminal_state_invalid/u);
  assert.deepEqual(
    corpus.negativeCases.find(({ id }) => id === "m0-interrupted-main-run"),
    {
      id: "m0-interrupted-main-run",
      baseCaseId: "resume-with-safe-typed-presentation",
      mutation: {
        operation: "set",
        path: "runBindings.0.terminalDisposition",
        value: "interrupted",
      },
      expectedCode: "agui_run_terminal_state_invalid",
    },
  );
});

test("rejects snapshot watermarks before binding evidence and next-event time regression", async () => {
  for (const [mutate, code] of [
    [
      (authorityCase) => { authorityCase.snapshot.lastRecordedAt = "2026-08-01T12:00:25.000Z"; },
      /agui_snapshot_time_watermark_before_binding/u,
    ],
    [
      (authorityCase) => { authorityCase.nextEventRecordedAt = "2026-08-01T12:00:25.000Z"; },
      /agui_event_time_invalid/u,
    ],
    [
      (authorityCase) => { authorityCase.nextEventRecordedAt = "not-a-date"; },
      /agui_event_time_invalid/u,
    ],
    [
      (authorityCase) => { authorityCase.nextEventRecordedAt = "2026-08-01T12:00:27.000+00:00"; },
      /agui_event_time_invalid/u,
    ],
    [
      (authorityCase) => { authorityCase.snapshot.lastRecordedAt = "2026-08-01T12:00:26.000+00:00"; },
      /agui_snapshot_time_watermark_invalid/u,
    ],
  ]) {
    const root = await repositoryFixture();
    const corpus = JSON.parse(await readFile(resolve(root, "contract/corpus/agui-presentation-v1.json"), "utf8"));
    mutate(corpus.snapshotAuthorityCases[0]);
    await writeJson(root, "contract/corpus/agui-presentation-v1.json", corpus);
    await assert.rejects(validateRepository({ root }), code);
  }
});

test("freezes shared snapshot authority attacks with stable fail-closed codes", async () => {
  const corpus = await readJson("contract/corpus/agui-presentation-v1.json");
  assert.deepEqual(
    corpus.snapshotAuthorityNegativeCases.map(({ id, expectedCode }) => [id, expectedCode]),
    [
      ["zero-head-retains-bindings", "agui_snapshot_zero_head_bindings_invalid"],
      ["binding-evidence-exceeds-head", "agui_snapshot_binding_evidence_exceeds_head"],
      ["noncanonical-binding-time", "agui_snapshot_binding_time_invalid"],
      ["multiple-presentation-thread", "agui_snapshot_thread_scope_invalid"],
      ["parent-lineage-cycle", "agui_parent_lineage_cycle"],
      ["m0-interrupted-terminal", "agui_snapshot_terminal_state_invalid"],
    ],
  );
});

test("freezes a closed first-phase event, activity and custom vocabulary", async () => {
  const registry = await readJson("contract/registry/agui-presentation-mapping-v1.yaml");
  assert.deepEqual(registry.allowedEventTypes, [
    "RUN_STARTED", "RUN_FINISHED", "RUN_ERROR",
    "TEXT_MESSAGE_START", "TEXT_MESSAGE_CONTENT", "TEXT_MESSAGE_END",
    "ACTIVITY_SNAPSHOT", "CUSTOM",
  ]);
  assert.equal(registry.mappings.length, 22);
  assert.ok(registry.forbiddenEventTypes.includes("RAW"));
  assert.ok(registry.forbiddenFields.includes("rawEvent"));
  assert.ok(registry.forbiddenEventFamilies.includes("native-tool"));
  assert.equal(new Set(registry.mappings.map(({ sourceKind }) => sourceKind)).size, 22);
});

test("rejects every checked-in attack vector with its stable failure code", async () => {
  const corpus = await readJson("contract/corpus/agui-presentation-v1.json");
  const baseById = new Map(corpus.positiveCases.map((entry) => [entry.id, entry]));
  for (const attack of corpus.negativeCases) {
    const candidate = applyCorpusMutation(clone(baseById.get(attack.baseCaseId)), attack.mutation);
    assert.throws(
      () => validateConformanceCase(candidate),
      (error) => error instanceof AguiPresentationContractError && error.code === attack.expectedCode,
      attack.id,
    );
  }
});

test("does not trust expected attack labels: terminal runs, ended messages and lineage are independently fenced", async () => {
  const corpus = await readJson("contract/corpus/agui-presentation-v1.json");
  const base = corpus.positiveCases[0];

  const revival = applyCorpusMutation(clone(base), {
    operation: "terminal-revival",
    runBindingRef: "run-binding.01.segment.0",
  });
  assert.throws(() => validateConformanceCase(revival), /agui_terminal_run_revived/u);

  const reopened = applyCorpusMutation(clone(base), {
    operation: "reopen-message",
    messageBindingRef: "message-binding.01.segment.0",
  });
  assert.throws(() => validateConformanceCase(reopened), /agui_message_reopened/u);

  const confused = clone(base);
  confused.runBindings[1].parentLineage.parentPresentationRunId = confused.runBindings[0].presentationRunId;
  assert.throws(() => validateConformanceCase(confused), /agui_resume_parent_confused/u);
});

test("requires HTTP snapshot to be the only hydrate and repair authority and keeps draining non-durable", async () => {
  const corpus = await readJson("contract/corpus/agui-presentation-v1.json");
  const candidate = clone(corpus.positiveCases[0]);
  candidate.snapshot.authority = "stream";
  assert.throws(() => validateConformanceCase(candidate), /agui_snapshot_authority_invalid/u);

  const durableDrain = clone(corpus.positiveCases[0]);
  durableDrain.controlFrame.id = "v1.cursor-key.illegal-drain";
  assert.throws(() => validateConformanceCase(durableDrain), /agui_draining_not_nondurable/u);
});

test("rejects every forbidden upstream family instead of inheriting the upstream passthrough", async () => {
  const corpus = await readJson("contract/corpus/agui-presentation-v1.json");
  const registry = await readJson("contract/registry/agui-presentation-mapping-v1.yaml");
  for (const eventType of registry.forbiddenEventTypes) {
    const candidate = clone(corpus.positiveCases[0]);
    candidate.frames[0].data.event.type = eventType;
    candidate.frames[0].event = eventType;
    assert.throws(
      () => validateConformanceCase(candidate),
      (error) => error instanceof AguiPresentationContractError && error.code === "agui_event_type_forbidden",
      eventType,
    );
  }
});

test("binds the presentation profile into grant/cursor policy and proves row-to-frame bijection", async () => {
  const corpus = await readJson("contract/corpus/agui-presentation-v1.json");
  const wrongGrant = clone(corpus.positiveCases[0]);
  wrongGrant.grantBinding.presentationProfileRevision = "kokoro-agui-presentation.v0";
  assert.throws(() => validateConformanceCase(wrongGrant), /agui_grant_profile_binding_invalid/u);

  const missingRow = clone(corpus.positiveCases[0]);
  missingRow.durableRows.pop();
  assert.throws(() => validateConformanceCase(missingRow), /agui_durable_frame_cardinality_invalid/u);

  const wrongProfile = clone(corpus.positiveCases[0]);
  wrongProfile.frames[0].data.profileRevision = "kokoro-agui-presentation.v0";
  assert.throws(() => validateConformanceCase(wrongProfile), /agui_stream_scope_conflict/u);
});

test("full repository gate rejects a cross-Session cursor swap after decoding closed claims", async () => {
  const root = await repositoryFixture();
  const corpus = JSON.parse(await readFile(resolve(root, "contract/corpus/agui-presentation-v1.json"), "utf8"));
  corpus.positiveCases[0].frames[0].id = corpus.positiveCases[1].frames[0].id;
  await writeJson(root, "contract/corpus/agui-presentation-v1.json", corpus);
  await assert.rejects(validateRepository({ root }), /agui_cursor_claim_scope_conflict/u);
});

test("full repository gate rejects a frame payload change whose persisted row digest did not change", async () => {
  const root = await repositoryFixture();
  const corpus = JSON.parse(await readFile(resolve(root, "contract/corpus/agui-presentation-v1.json"), "utf8"));
  corpus.positiveCases[0].frames[2].data.event.delta = "tampered but schema-valid delta";
  await writeJson(root, "contract/corpus/agui-presentation-v1.json", corpus);
  await assert.rejects(validateRepository({ root }), /agui_presentation_row_payload_mismatch/u);
});

test("full repository gate forbids private route fields even when injected into a binding replacement", async () => {
  const root = await repositoryFixture();
  const corpus = JSON.parse(await readFile(resolve(root, "contract/corpus/agui-presentation-v1.json"), "utf8"));
  corpus.positiveCases[0].frames[0].data.bindingAuthorityDelta.binding.internalRunRef = "internal.run.tampered";
  await writeJson(root, "contract/corpus/agui-presentation-v1.json", corpus);
  await assert.rejects(validateRepository({ root }), /agui_browser_internal_route_forbidden/u);
});

test("full repository gate includes browser-safe binding replacement bytes in the persisted row digest", async () => {
  const root = await repositoryFixture();
  const corpus = JSON.parse(await readFile(resolve(root, "contract/corpus/agui-presentation-v1.json"), "utf8"));
  corpus.positiveCases[0].frames[0].data.bindingAuthorityDelta.binding.presentationThreadId = "thread.tampered";
  await writeJson(root, "contract/corpus/agui-presentation-v1.json", corpus);
  await assert.rejects(validateRepository({ root }), /agui_presentation_row_payload_mismatch/u);
});

test("full repository gate resolves a non-null parent through browser-safe presentation lineage", async () => {
  const root = await repositoryFixture();
  const corpus = JSON.parse(await readFile(resolve(root, "contract/corpus/agui-presentation-v1.json"), "utf8"));
  corpus.positiveCases[0].runBindings[0].parentLineage.parentPresentationRunId = "presentation.run.missing";
  await writeJson(root, "contract/corpus/agui-presentation-v1.json", corpus);
  await assert.rejects(validateRepository({ root }), /agui_parent_lineage_pair_invalid/u);
});

test("full repository gate checks matching Agent parent topology only in Session-private route fixtures", async () => {
  const root = await repositoryFixture();
  const corpus = JSON.parse(await readFile(resolve(root, "contract/corpus/agui-presentation-v1.json"), "utf8"));
  const contractCase = corpus.positiveCases.find(({ id }) => id === "safe-run-error");
  const childRoute = contractCase.sessionPrivateRouteFixtures.runs.find(({ parentInternalRunRef }) => parentInternalRunRef !== null);
  childRoute.parentInternalRunRef = "internal.run.attacker";
  await writeJson(root, "contract/corpus/agui-presentation-v1.json", corpus);
  await assert.rejects(validateRepository({ root }), /agui_private_parent_route_conflict/u);
});

test("full repository gate cannot be pointed at a permissive branded replacement schema", async () => {
  const root = await repositoryFixture();
  const schema = JSON.parse(await readFile(resolve(root, "contract/spec/kokoro-agui-presentation-event-v1.yaml"), "utf8"));
  schema.oneOf = [{ "type": "object" }];
  await writeJson(root, "contract/spec/kokoro-agui-presentation-event-v1.yaml", schema);
  await assert.rejects(validateRepository({ root }), /agui_contract_source_drift/u);
});

test("full repository gate rejects package and lock source drift from the exact official SDK", async () => {
  const root = await repositoryFixture();
  const packageJson = JSON.parse(await readFile(resolve(root, "contract/package.json"), "utf8"));
  packageJson.devDependencies["@ag-ui/core"] = "0.0.58";
  await writeJson(root, "contract/package.json", packageJson);
  await assert.rejects(validateRepository({ root }), /agui_core_dependency_drift/u);
});

test("full repository gate rejects an exact copied positive case by global cursor identity", async () => {
  const root = await repositoryFixture();
  const corpus = JSON.parse(await readFile(resolve(root, "contract/corpus/agui-presentation-v1.json"), "utf8"));
  const copied = clone(corpus.positiveCases[0]);
  copied.id = `${copied.id}.copied`;
  corpus.positiveCases.push(copied);
  await writeJson(root, "contract/corpus/agui-presentation-v1.json", corpus);
  await assert.rejects(validateRepository({ root }), /agui_global_cursor_identity_duplicate/u);
});

test("full repository gate rejects randomized cursor encodings of already-used closed claims", async () => {
  const root = await repositoryFixture();
  const corpus = JSON.parse(await readFile(resolve(root, "contract/corpus/agui-presentation-v1.json"), "utf8"));
  const copied = clone(corpus.positiveCases[0]);
  copied.id = `${copied.id}.resigned`;
  resignCaseCursors(copied);
  corpus.positiveCases.push(copied);
  await writeJson(root, "contract/corpus/agui-presentation-v1.json", corpus);
  await assert.rejects(validateRepository({ root }), /agui_global_cursor_claim_identity_duplicate/u);
});

test("full repository gate accepts a coherent third Session with fresh semantic identities", async () => {
  const root = await repositoryFixture();
  const corpus = JSON.parse(await readFile(resolve(root, "contract/corpus/agui-presentation-v1.json"), "utf8"));
  corpus.positiveCases.push(distinctPositiveCase(corpus.positiveCases[0], {
    suffix: "legal-third",
    sessionId: "session.legal.third",
    streamEpoch: "41",
  }));
  await writeJson(root, "contract/corpus/agui-presentation-v1.json", corpus);
  const result = await validateRepository({ root });
  assert.equal(result.positiveCases, 3);
  assert.equal(result.durableFrames, 67);
});

test("full repository gate rejects every cross-case durable and binding semantic identity collision", async () => {
  const attacks = [
    {
      code: "agui_global_row_ref_duplicate",
      mutate(third, base) { third.durableRows[0].rowRef = base.durableRows[0].rowRef; },
    },
    {
      code: "agui_global_run_binding_ref_duplicate",
      mutate(third, base) { third.runBindings[0].bindingRef = base.runBindings[0].bindingRef; },
    },
    {
      code: "agui_global_presentation_run_id_duplicate",
      mutate(third, base) { third.runBindings[0].presentationRunId = base.runBindings[0].presentationRunId; },
    },
    {
      code: "agui_global_message_binding_ref_duplicate",
      mutate(third, base) { third.messageBindings[0].bindingRef = base.messageBindings[0].bindingRef; },
    },
    {
      code: "agui_global_presentation_message_id_duplicate",
      mutate(third, base) { third.messageBindings[0].presentationMessageId = base.messageBindings[0].presentationMessageId; },
    },
    {
      code: "agui_global_internal_run_segment_duplicate",
      sameSession: true,
      mutate(third, base) {
        third.sessionPrivateRouteFixtures.runs[0].internalRunRef = base.sessionPrivateRouteFixtures.runs[0].internalRunRef;
      },
    },
    {
      code: "agui_global_internal_message_segment_duplicate",
      sameSession: true,
      mutate(third, base) {
        third.sessionPrivateRouteFixtures.messages[0].internalMessageRef = base.sessionPrivateRouteFixtures.messages[0].internalMessageRef;
      },
    },
    {
      code: "agui_global_source_event_id_duplicate",
      sameSession: true,
      mutate(third, base) {
        third.frames[0].data.source.sourceEventId = base.frames[0].data.source.sourceEventId;
        third.durableRows[0].source = clone(third.frames[0].data.source);
        third.durableRows[0].projectionPayload = clone(third.frames[0].data);
        third.durableRows[0].projectionPayloadDigest = projectionDigest(third.frames[0].data);
      },
    },
  ];
  for (const attack of attacks) {
    const root = await repositoryFixture();
    const corpus = JSON.parse(await readFile(resolve(root, "contract/corpus/agui-presentation-v1.json"), "utf8"));
    const base = corpus.positiveCases[0];
    const third = distinctPositiveCase(base, {
      suffix: `attack-${attack.code}`,
      sessionId: attack.sameSession === true ? base.snapshot.sessionId : `session.${attack.code}`,
      streamEpoch: attack.sameSession === true ? "42" : base.snapshot.streamEpoch,
    });
    attack.mutate(third, base);
    corpus.positiveCases.push(third);
    await writeJson(root, "contract/corpus/agui-presentation-v1.json", corpus);
    await assert.rejects(
      validateRepository({ root }),
      (error) => error instanceof AguiPresentationContractError && error.code === attack.code,
      attack.code,
    );
  }
});
