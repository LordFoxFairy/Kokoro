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
  "contract/registry/agui-presentation-mapping-v1.yaml",
  "contract/registry/agui-upstream-profile.yaml",
  "contract/spec/kokoro-agui-presentation-event-v1.yaml",
  "contract/spec/presentation-message-binding-v1.yaml",
  "contract/spec/presentation-run-binding-v1.yaml",
  "contract/spec/session-agui-projection-payload-v1.yaml",
  "contract/spec/session-agui-presentation-row-v1.yaml",
  "contract/spec/session-agui-stream-v1.yaml",
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
    for (const field of ["bindingRef", "internalRunRef", "presentationThreadId", "presentationRunId", "openedBySourceEventId", "terminalSourceEventId"]) {
      if (binding[field] !== null) replacements.set(binding[field], `${binding[field]}.${suffix}`);
    }
  }
  for (const binding of base.messageBindings) {
    for (const field of ["bindingRef", "internalMessageRef", "presentationMessageId", "openedBySourceEventId", "endedBySourceEventId"]) {
      if (binding[field] !== null) replacements.set(binding[field], `${binding[field]}.${suffix}`);
    }
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
    negativeCases: 10,
    durableFrames: 30,
    mappingsCovered: 22,
  });
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

test("pins the official TypeScript schema family while keeping Python and the stock client out of the wire path", async () => {
  const profile = await readJson("contract/registry/agui-upstream-profile.yaml");
  assert.equal(profile.upstream.commit, "54f13419055b4d0f442c71e1efab18b310982ce1");
  assert.deepEqual(profile.typescript.core, {
    package: "@ag-ui/core",
    version: "0.0.57",
    integrity: "sha512-gho1OWjNE6E3Rl7ZEZ1wr2CEpUHjLFU0FqzCZZk439TicLu+BfLCMkMokB07bMGlRmbJ60hM6LW60iOVauCx+Q==",
    participant: true,
  });
  assert.equal(profile.typescript.client.participant, false);
  assert.equal(profile.python.participant, false);
  assert.equal(profile.rendering.assistantUi.version, "0.14.28");
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
  confused.runBindings[1].parentLineage.parentInternalRunRef = confused.runBindings[0].internalRunRef;
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

test("full repository gate resolves a non-null parent as one real same-Session internal/presentation pair", async () => {
  const root = await repositoryFixture();
  const corpus = JSON.parse(await readFile(resolve(root, "contract/corpus/agui-presentation-v1.json"), "utf8"));
  corpus.positiveCases[0].runBindings[0].parentLineage.parentPresentationRunId = "presentation.run.missing";
  await writeJson(root, "contract/corpus/agui-presentation-v1.json", corpus);
  await assert.rejects(validateRepository({ root }), /agui_parent_lineage_pair_invalid/u);
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
  assert.equal(result.durableFrames, 56);
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
      mutate(third, base) { third.runBindings[0].internalRunRef = base.runBindings[0].internalRunRef; },
    },
    {
      code: "agui_global_internal_message_segment_duplicate",
      sameSession: true,
      mutate(third, base) { third.messageBindings[0].internalMessageRef = base.messageBindings[0].internalMessageRef; },
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
