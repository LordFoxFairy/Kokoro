import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import test from "node:test";

import {
  AguiPresentationContractError,
  applyCorpusMutation,
  validateConformanceCase,
  validateRepository,
} from "./check-agui-presentation.mjs";

const repositoryRoot = resolve(import.meta.dirname, "../..");

async function readJson(path) {
  return JSON.parse(await readFile(resolve(repositoryRoot, path), "utf8"));
}

function clone(value) {
  return structuredClone(value);
}

test("validates the pinned upstream profile and complete presentation corpus", async () => {
  const result = await validateRepository({ root: repositoryRoot });
  assert.deepEqual(result, {
    positiveCases: 2,
    negativeCases: 10,
    durableFrames: 28,
    mappingsCovered: 22,
  });
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
      () => validateConformanceCase(candidate, corpus.contracts),
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
  assert.throws(() => validateConformanceCase(revival, corpus.contracts), /agui_terminal_run_revived/u);

  const reopened = applyCorpusMutation(clone(base), {
    operation: "reopen-message",
    messageBindingRef: "message-binding.01.segment.0",
  });
  assert.throws(() => validateConformanceCase(reopened, corpus.contracts), /agui_message_reopened/u);

  const confused = clone(base);
  confused.runBindings[1].parentLineage.parentPresentationRunId = confused.runBindings[0].presentationRunId;
  assert.throws(() => validateConformanceCase(confused, corpus.contracts), /agui_resume_parent_confused/u);
});

test("requires HTTP snapshot to be the only hydrate and repair authority and keeps draining non-durable", async () => {
  const corpus = await readJson("contract/corpus/agui-presentation-v1.json");
  const candidate = clone(corpus.positiveCases[0]);
  candidate.snapshot.authority = "stream";
  assert.throws(() => validateConformanceCase(candidate, corpus.contracts), /agui_snapshot_authority_invalid/u);

  const durableDrain = clone(corpus.positiveCases[0]);
  durableDrain.controlFrame.id = "v1.cursor-key.illegal-drain";
  assert.throws(() => validateConformanceCase(durableDrain, corpus.contracts), /agui_draining_not_nondurable/u);
});

test("rejects every forbidden upstream family instead of inheriting the upstream passthrough", async () => {
  const corpus = await readJson("contract/corpus/agui-presentation-v1.json");
  const registry = await readJson("contract/registry/agui-presentation-mapping-v1.yaml");
  for (const eventType of registry.forbiddenEventTypes) {
    const candidate = clone(corpus.positiveCases[0]);
    candidate.frames[0].data.event.type = eventType;
    candidate.frames[0].event = eventType;
    assert.throws(
      () => validateConformanceCase(candidate, corpus.contracts),
      (error) => error instanceof AguiPresentationContractError && error.code === "agui_event_type_forbidden",
      eventType,
    );
  }
});

test("binds the presentation profile into grant/cursor policy and proves row-to-frame bijection", async () => {
  const corpus = await readJson("contract/corpus/agui-presentation-v1.json");
  const wrongGrant = clone(corpus.positiveCases[0]);
  wrongGrant.grantBinding.presentationProfileRevision = "kokoro-agui-presentation.v0";
  assert.throws(() => validateConformanceCase(wrongGrant, corpus.contracts), /agui_grant_profile_binding_invalid/u);

  const missingRow = clone(corpus.positiveCases[0]);
  missingRow.durableRows.pop();
  assert.throws(() => validateConformanceCase(missingRow, corpus.contracts), /agui_durable_frame_cardinality_invalid/u);

  const wrongProfile = clone(corpus.positiveCases[0]);
  wrongProfile.frames[0].data.profileRevision = "kokoro-agui-presentation.v0";
  assert.throws(() => validateConformanceCase(wrongProfile, corpus.contracts), /agui_stream_scope_conflict/u);
});
