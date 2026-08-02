#!/usr/bin/env node

import { spawn, spawnSync } from "node:child_process";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { writeSync } from "node:fs";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
export const AGUI_ROOT_AUTHORITY_COMMIT = "6aa0f1487741bc9d511450cae65326485f037d26";
const PARTICIPANT_IDS = Object.freeze(["kokoro-agent", "kokoro-session", "kokoro-web"]);
const SHA_PATTERN = /^[0-9a-f]{40}$/u;
const MAXIMUM_CHILD_OUTPUT_BYTES = 17 * 1024 * 1024;
const MAXIMUM_DURATION_MS = 299_999;
const ASSERTION_IDS = Object.freeze([
  "agent-session-web-agui:official-agent-candidates",
  "agent-session-web-agui:session-durable-admission",
  "agent-session-web-agui:session-paged-replay",
  "agent-session-web-agui:web-public-decoder",
  "agent-session-web-agui:snapshot-live-reducer-converged",
  "agent-session-web-agui:run-text-terminal-covered",
  "agent-session-web-agui:participant-pins-bound",
  "agent-session-web-agui:root-contract-provenance",
  "agent-session-web-agui:process-and-file-cleanup",
]);

function fail(code) {
  throw new Error(code);
}

export function validateLease(value) {
  const session = value?.postgres?.session;
  const testRole = session?.roles?.test;
  const migratorRole = session?.roles?.migrator;
  if (
    value === null || typeof value !== "object" || value.schemaVersion !== 1 ||
    !/^run_[a-z0-9][a-z0-9_-]{2,31}$/u.test(value.runId ?? "") ||
    !Array.isArray(value.resources) || !value.resources.includes("postgres") ||
    typeof session?.database !== "string" || !/^kokoro_test_[a-z0-9_]+_session$/u.test(session.database) ||
    typeof testRole?.username !== "string" || !/^[a-z0-9_]+$/u.test(testRole.username) ||
    typeof testRole?.password !== "string" || testRole.password.length < 16 ||
    typeof migratorRole?.username !== "string" || !/^[a-z0-9_]+$/u.test(migratorRole.username) ||
    typeof migratorRole?.password !== "string" || migratorRole.password.length < 16 ||
    testRole.username === migratorRole.username
  ) fail("agui_compatibility_scope_invalid");
  return value;
}

export function validateParticipantPins(source) {
  let value;
  try { value = JSON.parse(source); } catch { fail("agui_compatibility_provenance_invalid"); }
  if (
    value === null || typeof value !== "object" || Array.isArray(value) ||
    Object.keys(value).sort().join("\0") !== [...PARTICIPANT_IDS].sort().join("\0") ||
    PARTICIPANT_IDS.some((id) => !SHA_PATTERN.test(value[id] ?? ""))
  ) fail("agui_compatibility_provenance_invalid");
  return Object.freeze(Object.fromEntries(PARTICIPANT_IDS.map((id) => [id, value[id]])));
}

export function validateRootAuthority(value) {
  if (
    value?.rootCommit !== AGUI_ROOT_AUTHORITY_COMMIT ||
    value?.sessionSnapshotRootCommit !== AGUI_ROOT_AUTHORITY_COMMIT ||
    value?.sessionProjectionRootCommit !== AGUI_ROOT_AUTHORITY_COMMIT ||
    value?.webSourceDigestsMatch !== true
  ) fail("agui_compatibility_root_provenance_invalid");
  return value;
}

export function buildResult(passed, durationMs) {
  const duration = Number.isFinite(durationMs) ? Math.trunc(durationMs) : 0;
  return Object.freeze({
    schemaVersion: 1,
    scenarioId: "agent-session-web-agui",
    outcome: passed ? "pass" : "fail",
    reasonCode: passed ? "ok" : "agent_session_web_agui_live_failed",
    assertionIds: [...ASSERTION_IDS],
    durationMs: Math.min(MAXIMUM_DURATION_MS, Math.max(0, duration)),
  });
}

function isolatedEnvironment(explicit = {}) {
  const environment = {};
  for (const key of ["PATH", "HOME", "TMPDIR", "TMP", "TEMP", "LANG", "LC_ALL", "PNPM_HOME"]) {
    if (typeof process.env[key] === "string" && process.env[key] !== "") {
      environment[key] = process.env[key];
    }
  }
  return { ...environment, ...explicit };
}

async function runCaptured(command, { cwd, env = {}, maximumBytes = MAXIMUM_CHILD_OUTPUT_BYTES }) {
  const [executable, ...arguments_] = command;
  const child = spawn(executable, arguments_, {
    cwd,
    env: isolatedEnvironment(env),
    shell: false,
    stdio: ["ignore", "pipe", process.env.KOKORO_COMPAT_DEBUG === "1" ? "inherit" : "pipe"],
  });
  const chunks = [];
  const errorChunks = [];
  let outputBytes = 0;
  let errorBytes = 0;
  child.stdout.on("data", (chunk) => {
    outputBytes += chunk.byteLength;
    if (outputBytes <= maximumBytes) chunks.push(chunk);
  });
  child.stderr?.on("data", (chunk) => {
    errorBytes += chunk.byteLength;
    if (errorBytes <= 64 * 1024) errorChunks.push(chunk);
  });
  const exitCode = await new Promise((done, reject) => {
    child.once("error", reject);
    child.once("exit", (code) => done(code));
  });
  if (exitCode !== 0 || outputBytes < 2 || outputBytes > maximumBytes || errorBytes > 64 * 1024) {
    if (process.env.KOKORO_COMPAT_DEBUG === "1" && errorChunks.length > 0) {
      process.stderr.write(Buffer.concat(errorChunks).toString("utf8"));
    }
    fail("agui_compatibility_child_failed");
  }
  const text = Buffer.concat(chunks).toString("utf8");
  if (text.split(/\r?\n/u).filter(Boolean).length !== 1) fail("agui_compatibility_child_protocol");
  return text;
}

function runOfficial(command, { cwd, env = {}, input } = {}) {
  const [executable, ...arguments_] = command;
  const result = spawnSync(executable, arguments_, {
    cwd,
    env: isolatedEnvironment(env),
    input,
    encoding: "utf8",
    maxBuffer: 4 * 1024 * 1024,
    stdio: ["pipe", process.env.KOKORO_COMPAT_DEBUG === "1" ? "inherit" : "ignore", "pipe"],
  });
  if (result.status !== 0) fail("agui_compatibility_setup_failed");
}

function runGit(arguments_, cwd) {
  const result = spawnSync("git", arguments_, {
    cwd,
    env: isolatedEnvironment(),
    encoding: "utf8",
    shell: false,
    stdio: ["ignore", "pipe", "pipe"],
  });
  if (result.status !== 0) fail("agui_compatibility_provenance_invalid");
  return result.stdout.trim();
}

function assertParticipantPins(expected) {
  for (const id of PARTICIPANT_IDS) {
    const current = runGit(["rev-parse", "HEAD"], resolve(root, id));
    if (current !== expected[id]) fail("agui_compatibility_provenance_invalid");
  }
}

function extractRootCommit(source, pattern) {
  const match = pattern.exec(source);
  if (match?.[1] === undefined) fail("agui_compatibility_root_provenance_invalid");
  return match[1];
}

async function assertRootContractProvenance() {
  const resolvedAuthority = runGit(["rev-parse", `${AGUI_ROOT_AUTHORITY_COMMIT}^{commit}`], root);
  if (resolvedAuthority !== AGUI_ROOT_AUTHORITY_COMMIT) {
    fail("agui_compatibility_root_provenance_invalid");
  }
  runOfficial([
    "git", "diff", "--quiet", AGUI_ROOT_AUTHORITY_COMMIT, "--",
    "contract/spec/presentation-run-binding-v1.yaml",
    "contract/spec/presentation-message-binding-v1.yaml",
    "contract/spec/presentation-owner-binding-v1.yaml",
    "contract/spec/presentation-binding-authority-delta-v1.yaml",
    "contract/spec/session-agui-owner-projection-row-v1.yaml",
    "contract/spec/session-agui-snapshot-authority-v1.yaml",
    "contract/spec/session-agui-projection-payload-v1.yaml",
    "contract/spec/kokoro-agui-presentation-event-v1.yaml",
  ], { cwd: root });
  const snapshotMetadata = await readFile(
    resolve(root, "kokoro-session/src/presentation/agui/snapshot-authority-contract.generated.ts"),
    "utf8",
  );
  const projectionMetadata = await readFile(
    resolve(root, "kokoro-session/src/presentation/agui/projection-payload-contract.generated.ts"),
    "utf8",
  );
  const sessionSnapshotRootCommit = extractRootCommit(
    snapshotMetadata,
    /rootSourceCommit:\s*"([0-9a-f]{40})"/u,
  );
  const sessionProjectionRootCommit = extractRootCommit(
    projectionMetadata,
    /"rootSourceCommit":\s*"([0-9a-f]{40})"/u,
  );
  runOfficial(["npm", "run", "check:agui-snapshot-contract:root"], {
    cwd: resolve(root, "kokoro-session"),
  });
  runOfficial(["npm", "run", "check:agui-projection-contract:root"], {
    cwd: resolve(root, "kokoro-session"),
  });
  runOfficial(["pnpm", "verify:agui-binding-authority"], {
    cwd: resolve(root, "kokoro-web"),
  });
  validateRootAuthority({
    rootCommit: resolvedAuthority,
    sessionSnapshotRootCommit,
    sessionProjectionRootCommit,
    webSourceDigestsMatch: true,
  });
}

function databaseUrl(lease, roleName) {
  const allocation = lease.postgres.session;
  const role = allocation.roles[roleName];
  if (role === undefined) fail("agui_compatibility_database_role_invalid");
  const port = process.env.KOKORO_POSTGRES_PORT ?? "5433";
  if (!/^[0-9]{2,5}$/u.test(port)) fail("agui_compatibility_postgres_port_invalid");
  return `postgresql://${encodeURIComponent(role.username)}:${encodeURIComponent(role.password)}` +
    `@127.0.0.1:${port}/${encodeURIComponent(allocation.database)}?schema=public`;
}

function parseClosedJson(text, profile) {
  let value;
  try { value = JSON.parse(text); } catch { fail("agui_compatibility_child_protocol"); }
  if (value === null || typeof value !== "object" || Array.isArray(value) || value.profileRevision !== profile) {
    fail("agui_compatibility_child_protocol");
  }
  return value;
}

function assertAgentBundle(value) {
  const envelopes = Array.isArray(value?.candidates)
    ? value.candidates.map((candidate) => {
      let envelope;
      try {
        const bytes = Buffer.from(candidate?.envelopeBase64 ?? "", "base64");
        if (bytes.toString("base64") !== candidate?.envelopeBase64) return null;
        envelope = JSON.parse(bytes.toString("utf8"));
      } catch { return null; }
      return envelope;
    })
    : [];
  if (
    value.scope?.siteId !== "site-agui-compat" || value.scope?.sessionId !== "session-agui-compat" ||
    value.scope?.streamEpoch !== "1" || !Array.isArray(value.candidates) || value.candidates.length !== 6 ||
    value.candidates.some((candidate, index) => (
      candidate?.binding?.expectedSourceOrdinal !== String(index) ||
      typeof candidate?.candidateRef !== "string" || !candidate.candidateRef.startsWith("agui_candidate:sha256:") ||
      typeof candidate?.envelopeBase64 !== "string" || candidate.envelopeBase64.length < 4
    )) || envelopes.length !== value.candidates.length || envelopes.some((envelope, index) => (
      envelope?.profileRevision !== "kokoro-agent-agui-candidate.v1" ||
      envelope?.event?.type !== value.candidates[index]?.binding?.eventType ||
      Object.hasOwn(envelope, "siteId") || Object.hasOwn(envelope, "sessionId")
    ))
  ) fail("agui_compatibility_agent_bundle_invalid");
}

function assertSessionOutput(value) {
  const frames = value.replay?.pages?.flatMap((page) => page.frames ?? []);
  if (
    value.initialSnapshot?.durableSeq !== "0" || value.finalSnapshot?.durableSeq !== "6" ||
    value.replay?.frameCount !== 6 || value.replay?.pages?.length !== 3 || frames?.length !== 6 ||
    value.admissions?.length !== 6 || value.receipts?.length !== 6 ||
    frames.some((frame) => frame.data.includes("internal.run") || frame.data.includes("agent.event"))
  ) fail("agui_compatibility_session_output_invalid");
}

function assertWebReceipt(value) {
  if (
    value.providerProfileRevision !== "kokoro-session-agui-compatibility-output.v1" ||
    value.consumed?.frameCount !== 6 || value.consumed?.pageCount !== 3 ||
    value.consumed?.authorityCommitCount !== 6 || value.consumed?.durableDispatchCount !== 6 ||
    value.authority?.finalDurableSeq !== "6" || value.authority?.finalSnapshotEqual !== true ||
    value.authority?.sessionSnapshotDigest !== value.authority?.localSnapshotDigest ||
    value.coverage?.bindingAuthority !== true || value.coverage?.runLifecycle !== true ||
    value.coverage?.textLifecycle !== true || value.coverage?.terminalLifecycle !== true ||
    value.coverage?.dispatchBeforeCommit !== true
  ) fail("agui_compatibility_web_receipt_invalid");
}

export async function run() {
  const started = Date.now();
  let directory;
  try {
    const scopePath = process.env.KOKORO_COMPAT_SCOPE_FILE;
    if (typeof scopePath !== "string" || scopePath === "") fail("agui_compatibility_scope_missing");
    const participantPins = validateParticipantPins(process.env.KOKORO_COMPAT_PARTICIPANT_PINS ?? "");
    assertParticipantPins(participantPins);
    await assertRootContractProvenance();
    const lease = validateLease(JSON.parse(await readFile(scopePath, "utf8")));
    const migratorUrl = databaseUrl(lease, "migrator");
    const runtimeUrl = databaseUrl(lease, "test");
    runOfficial(["npm", "run", "db:migrate"], {
      cwd: resolve(root, "kokoro-session"),
      env: { DATABASE_URL_SESSION: migratorUrl },
    });

    directory = await mkdtemp(join(tmpdir(), "kokoro-agui-compatibility-"));
    const setupPath = join(directory, "session-setup.json");
    const fixturePath = join(directory, "agent-fixture.json");
    const candidatePath = join(directory, "agent-candidates.json");
    const sessionPath = join(directory, "session-output.json");
    await writeFile(setupPath, JSON.stringify({
      profileRevision: "kokoro-session-agui-compatibility-setup-input.v1",
      siteId: "site-agui-compat",
      sessionId: "session-agui-compat",
      projectRef: "project-agui-compat",
      subjectRef: "subject-agui-compat",
      runtimeRoleName: lease.postgres.session.roles.test.username,
    }), { encoding: "utf8", mode: 0o600 });
    const setupText = await runCaptured([
      "npm", "run", "compat:agui-setup", "--", setupPath,
    ], {
      cwd: resolve(root, "kokoro-session"),
      env: { KOKORO_SESSION_AGUI_COMPAT_MIGRATOR_DATABASE_URL: migratorUrl },
      maximumBytes: 128 * 1024,
    });
    const setupReceipt = parseClosedJson(
      setupText,
      "kokoro-session-agui-compatibility-setup-receipt.v1",
    );
    if (
      setupReceipt.scope?.siteId !== "site-agui-compat" ||
      setupReceipt.scope?.sessionId !== "session-agui-compat" ||
      setupReceipt.scope?.projectRef !== "project-agui-compat" ||
      setupReceipt.scope?.subjectRef !== "subject-agui-compat" ||
      typeof setupReceipt.setupDigest !== "string" ||
      !/^sha256:[0-9a-f]{64}$/u.test(setupReceipt.setupDigest)
    ) fail("agui_compatibility_session_setup_invalid");

    await writeFile(fixturePath, JSON.stringify({
      profileRevision: "kokoro-agent-agui-compatibility-fixture.v1",
      scope: { siteId: "site-agui-compat", sessionId: "session-agui-compat", streamEpoch: "1" },
      producer: { producerInstanceRef: "agent.instance.agui-compat", producerGeneration: "1" },
      cursorAuthority: { prefix: "agui.compat.cursor." },
      replayPageLimit: 2,
      fixture: {
        internalThreadRef: "agent.thread:agui.compat",
        internalRunRef: "internal.run.agui.compat",
        internalMessageRef: "internal.message.agui.compat",
        sourceEventPrefix: "agent.event.agui.compat.",
        startedAtMs: 1_786_742_400_000,
        textDeltas: ["Hello ", "from Kokoro"],
      },
    }), { encoding: "utf8", mode: 0o600 });

    const agentText = await runCaptured([
      "uv", "run", "--locked", "python", "-m", "scripts.compat.agui_candidate_provider",
      "--input", fixturePath,
    ], { cwd: resolve(root, "kokoro-agent") });
    const agentBundle = parseClosedJson(agentText, "kokoro-session-agui-compatibility-input.v1");
    assertAgentBundle(agentBundle);
    await writeFile(candidatePath, agentText, { encoding: "utf8", mode: 0o600 });

    const sessionText = await runCaptured([
      "npm", "run", "compat:agui-provider", "--", candidatePath,
    ], {
      cwd: resolve(root, "kokoro-session"),
      env: { KOKORO_SESSION_AGUI_COMPAT_DATABASE_URL: runtimeUrl },
    });
    const sessionOutput = parseClosedJson(sessionText, "kokoro-session-agui-compatibility-output.v1");
    assertSessionOutput(sessionOutput);
    await writeFile(sessionPath, sessionText, { encoding: "utf8", mode: 0o600 });

    const webText = await runCaptured([
      "pnpm", "--filter", "@kokoro/chat-surface", "compat:agui-consumer", "--", sessionPath,
    ], { cwd: resolve(root, "kokoro-web"), maximumBytes: 128 * 1024 });
    const webReceipt = parseClosedJson(
      webText,
      "kokoro-web-agui-compatibility-consumer-receipt.v1",
    );
    assertWebReceipt(webReceipt);
    return buildResult(true, Date.now() - started);
  } catch (error) {
    if (process.env.KOKORO_COMPAT_DEBUG === "1") process.stderr.write(`${String(error)}\n`);
    return buildResult(false, Date.now() - started);
  } finally {
    if (directory !== undefined) await rm(directory, { recursive: true, force: true });
  }
}

async function main() {
  const result = await run();
  try { writeSync(3, `${JSON.stringify(result)}\n`); } catch { process.exitCode = 1; return; }
  process.exitCode = result.outcome === "pass" ? 0 : 1;
}

if (process.argv[1] && pathToFileURL(process.argv[1]).href === import.meta.url) await main();
