import { strict as assert } from "node:assert";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

import {
  AGUI_ROOT_AUTHORITY_COMMIT,
  buildResult,
  validateLease,
  validateParticipantPins,
  validateRootAuthority,
} from "./agent-session-web-agui.mjs";

const lease = {
  schemaVersion: 1,
  runId: "run_agui_compat",
  resources: ["postgres"],
  postgres: {
    session: {
      database: "kokoro_test_run_agui_compat_session",
      roles: {
        test: { username: "kt_pg_sessiontest_abc", password: "a-closed-password" },
        migrator: { username: "kt_pg_sessionmigrator_abc", password: "another-closed-password" },
      },
    },
  },
};

test("AG-UI scenario accepts only its lease-scoped Session database identity", () => {
  assert.equal(validateLease(lease), lease);
  assert.throws(() => validateLease({ ...lease, resources: [] }), /agui_compatibility_scope_invalid/u);
  assert.throws(() => validateLease({
    ...lease,
    postgres: { session: { ...lease.postgres.session, database: "session" } },
  }), /agui_compatibility_scope_invalid/u);
  assert.throws(() => validateLease({
    ...lease,
    postgres: {
      session: {
        ...lease.postgres.session,
        roles: { ...lease.postgres.session.roles, migrator: lease.postgres.session.roles.test },
      },
    },
  }), /agui_compatibility_scope_invalid/u);
});

test("AG-UI scenario emits the closed FD3 result contract", () => {
  assert.deepEqual(buildResult(true, 12), {
    schemaVersion: 1,
    scenarioId: "agent-session-web-agui",
    outcome: "pass",
    reasonCode: "ok",
    assertionIds: [
      "agent-session-web-agui:official-agent-candidates",
      "agent-session-web-agui:session-durable-admission",
      "agent-session-web-agui:session-paged-replay",
      "agent-session-web-agui:web-public-decoder",
      "agent-session-web-agui:snapshot-live-reducer-converged",
      "agent-session-web-agui:run-text-terminal-covered",
      "agent-session-web-agui:participant-pins-bound",
      "agent-session-web-agui:root-contract-provenance",
      "agent-session-web-agui:process-and-file-cleanup",
    ],
    durationMs: 12,
  });
  assert.equal(buildResult(false, Number.MAX_SAFE_INTEGER).durationMs, 299_999);
});

test("AG-UI scenario closes participant pin and Root authority inputs", () => {
  const pins = {
    "kokoro-agent": "1".repeat(40),
    "kokoro-session": "2".repeat(40),
    "kokoro-web": "3".repeat(40),
  };
  assert.deepEqual(validateParticipantPins(JSON.stringify(pins)), pins);
  assert.throws(
    () => validateParticipantPins(JSON.stringify({ ...pins, "kokoro-platform": "4".repeat(40) })),
    /agui_compatibility_provenance_invalid/u,
  );
  assert.throws(
    () => validateParticipantPins(JSON.stringify({ ...pins, "kokoro-web": "HEAD" })),
    /agui_compatibility_provenance_invalid/u,
  );
  assert.equal(AGUI_ROOT_AUTHORITY_COMMIT, "6aa0f1487741bc9d511450cae65326485f037d26");
  assert.doesNotThrow(() => validateRootAuthority({
    rootCommit: AGUI_ROOT_AUTHORITY_COMMIT,
    sessionSnapshotRootCommit: AGUI_ROOT_AUTHORITY_COMMIT,
    sessionProjectionRootCommit: AGUI_ROOT_AUTHORITY_COMMIT,
    webSourceDigestsMatch: true,
  }));
  assert.throws(() => validateRootAuthority({
    rootCommit: AGUI_ROOT_AUTHORITY_COMMIT,
    sessionSnapshotRootCommit: AGUI_ROOT_AUTHORITY_COMMIT,
    sessionProjectionRootCommit: AGUI_ROOT_AUTHORITY_COMMIT,
    webSourceDigestsMatch: false,
  }), /agui_compatibility_root_provenance_invalid/u);
});

test("Root composes child-owned CLIs and never seeds a child private table", async () => {
  const source = await readFile(new URL("./agent-session-web-agui.mjs", import.meta.url), "utf8");
  assert.doesNotMatch(source, /INSERT\s+INTO|UPDATE\s+[a-z_]+|DELETE\s+FROM/iu);
  assert.doesNotMatch(source, /docker|agui_presentation_|session_database_role_authority/iu);
  assert.match(source, /scripts\.compat\.agui_candidate_provider/u);
  assert.match(source, /compat:agui-setup/u);
  assert.match(source, /compat:agui-provider/u);
  assert.match(source, /compat:agui-consumer/u);
  assert.match(source, /databaseUrl\(lease, "migrator"\)/u);
  assert.match(source, /databaseUrl\(lease, "test"\)/u);
  assert.doesNotMatch(source, /owner-(?:activity|control|receipt)-covered/u);
});
