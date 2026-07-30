#!/usr/bin/env node

import { createHash, randomBytes } from "node:crypto";
import { spawn, spawnSync } from "node:child_process";
import {
  lstat,
  mkdir,
  open,
  readFile,
  realpath,
  rename,
  rm,
} from "node:fs/promises";
import { dirname, relative, resolve, sep } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

import { acquireScope, cleanupScope, provisionScope } from "../infra/scope.mjs";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const REPOSITORY_IDS = ["kokoro-agent", "kokoro-platform", "kokoro-session", "kokoro-web"];
const RESULT_KEYS = ["assertionIds", "durationMs", "outcome", "reasonCode", "scenarioId", "schemaVersion"];
const RESULT_OUTCOMES = new Set(["pass", "fail", "incomplete", "interrupted"]);
const COMPAT_DATA_RESOURCES = ["postgres", "mongo", "redis"];
const COMMANDS = new Map([
  ["node-web-session-http-sse-v1", [process.execPath, "scripts/compatibility/web-session-http-sse.mjs"]],
  ["node-session-platform-internal-rpc-v1", [process.execPath, "scripts/compatibility/session-platform-internal-rpc.mjs"]],
  ["python-session-agent-durable-v1", ["uv", "run", "--locked", "python", "scripts/compatibility/session_agent_durable.py"]],
  ["python-agent-model-gateway-v1", ["uv", "run", "--locked", "python", "scripts/compatibility/agent_model_gateway.py"]],
  ["node-hub-runtime-v1", [process.execPath, "scripts/compatibility/hub-runtime.mjs"]],
  ["node-platform-admin-auth-connect-v1", [process.execPath, "scripts/compatibility/admin-auth-connect.mjs"]],
]);
const SHA_PATTERN = /^[0-9a-f]{40}$/u;
const SAFE_REASON = /^[a-z][a-z0-9_]{1,63}$/u;
const SAFE_ASSERTION = /^[a-z0-9][a-z0-9:._-]{1,127}$/u;
const MAX_MACHINE_RESULT_BYTES = 64 * 1024;
const PROCESS_GROUP_GRACE_MS = 5_000;
const TERMINAL_FAILURE_PRIORITY = new Map([
  ["postflight_pin_drift", 1],
  ["postflight_pin_verification_failed", 2],
  ["scope_file_cleanup_failed", 3],
  ["lease_cleanup_failed", 4],
]);

class CompatibilityError extends Error {
  constructor(code, detail = "") {
    super(`${code}${detail ? `: ${detail}` : ""}`);
    this.code = code;
  }
}

function exactKeys(value, keys) {
  if (value === null || typeof value !== "object" || Array.isArray(value)) return false;
  const actual = Object.keys(value).sort();
  const expected = [...keys].sort();
  return actual.length === expected.length && actual.every((key, index) => key === expected[index]);
}

function canonical(value) {
  if (Array.isArray(value)) return value.map(canonical);
  if (value !== null && typeof value === "object") {
    return Object.fromEntries(Object.keys(value).sort().map((key) => [key, canonical(value[key])]));
  }
  return value;
}

function digest(value) {
  const source = typeof value === "string" ? value : JSON.stringify(canonical(value));
  return createHash("sha256").update(source).digest("hex");
}

function parseRunnerArguments(argv, repositoryRoot = root) {
  const options = {
    root: resolve(repositoryRoot),
    matrixPath: resolve(repositoryRoot, "config/repository/compatibility-matrix.json"),
    manifestPath: resolve(repositoryRoot, "config/repository/federated-repositories.json"),
    tree: "head",
    evidencePath: null,
    infraEnvFile: null,
  };
  const seenArguments = new Set();
  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    const value = argv[index + 1];
    if (!value) throw new CompatibilityError("compatibility_arguments", argument);
    if (seenArguments.has(argument)) {
      throw new CompatibilityError("compatibility_arguments", argument);
    }
    seenArguments.add(argument);
    index += 1;
    if (argument === "--matrix") options.matrixPath = resolve(repositoryRoot, value);
    else if (argument === "--manifest") options.manifestPath = resolve(repositoryRoot, value);
    else if (argument === "--tree") options.tree = value;
    else if (argument === "--evidence") options.evidencePath = resolve(repositoryRoot, value);
    else if (argument === "--infra-env-file") options.infraEnvFile = resolve(repositoryRoot, value);
    else throw new CompatibilityError("compatibility_arguments", argument);
  }
  if (!["head", "index"].includes(options.tree) || options.evidencePath === null) {
    throw new CompatibilityError("compatibility_arguments");
  }
  return options;
}

function safeChildEnvironment(environment) {
  return Object.fromEntries(
    Object.entries(environment)
      .filter(([key]) => key.toLowerCase() !== "mysql_root_password"),
  );
}

function scenarioEnvironment(environment, scopeFile, scenarioId) {
  return {
    ...safeChildEnvironment(environment),
    KOKORO_COMPAT_SCOPE_FILE: scopeFile,
    KOKORO_COMPAT_SCENARIO_ID: scenarioId,
  };
}

async function existingParent(path) {
  let candidate = path;
  while (candidate !== dirname(candidate)) {
    try {
      await lstat(candidate);
      return candidate;
    } catch (error) {
      if (error.code !== "ENOENT") throw error;
      candidate = dirname(candidate);
    }
  }
  return candidate;
}

async function validateEvidenceTarget(repositoryRoot, evidencePath) {
  const resolvedRoot = resolve(repositoryRoot);
  const tmpRoot = resolve(resolvedRoot, "tmp");
  const target = resolve(evidencePath);
  if (!target.startsWith(`${tmpRoot}${sep}`)) {
    throw new CompatibilityError("compatibility_evidence_path");
  }
  const ignore = await readFile(resolve(resolvedRoot, ".gitignore"), "utf8").catch(() => "");
  if (!ignore.split(/\r?\n/u).some((line) => line.trim() === "tmp/")) {
    throw new CompatibilityError("compatibility_evidence_not_ignored");
  }
  const parent = dirname(target);
  const ancestor = await existingParent(parent);
  const realRoot = await realpath(resolvedRoot);
  const realAncestor = await realpath(ancestor);
  if (realAncestor !== realRoot && !realAncestor.startsWith(`${realRoot}${sep}`)) {
    throw new CompatibilityError("compatibility_evidence_symlink");
  }
  const relativeParent = relative(resolvedRoot, parent);
  let cursor = resolvedRoot;
  for (const segment of relativeParent.split(sep).filter(Boolean)) {
    cursor = resolve(cursor, segment);
    try {
      if ((await lstat(cursor)).isSymbolicLink()) {
        throw new CompatibilityError("compatibility_evidence_symlink");
      }
    } catch (error) {
      if (error.code === "ENOENT") break;
      throw error;
    }
  }
  try {
    if ((await lstat(target)).isSymbolicLink()) {
      throw new CompatibilityError("compatibility_evidence_symlink");
    }
  } catch (error) {
    if (error.code !== "ENOENT") throw error;
  }
  return target;
}

function sanitizeText(value) {
  return String(value)
    .replace(/Authorization:\s*Bearer\s+\S+/giu, "Authorization: [REDACTED]")
    .replace(/Bearer\s+[A-Za-z0-9._~-]+/gu, "Bearer [REDACTED]")
    .replace(/\b(?:PASSWORD|TOKEN|SECRET|API[_-]?KEY)\s*=\s*[^\s]+/giu, "credential=[REDACTED]")
    .replace(/(https?:\/\/)[^/@\s]+:[^/@\s]+@/giu, "$1[REDACTED]@")
    .replace(/-----BEGIN [^-]+-----[\s\S]*?(?:-----END [^-]+-----|$)/gu, "[REDACTED PEM]");
}

function validateScenarioResult(value, scenarioId) {
  if (
    !exactKeys(value, RESULT_KEYS) ||
    value.schemaVersion !== 1 ||
    value.scenarioId !== scenarioId ||
    !RESULT_OUTCOMES.has(value.outcome) ||
    !SAFE_REASON.test(value.reasonCode ?? "") ||
    !Array.isArray(value.assertionIds) ||
    value.assertionIds.length === 0 ||
    value.assertionIds.some((id) => typeof id !== "string" || !SAFE_ASSERTION.test(id)) ||
    new Set(value.assertionIds).size !== value.assertionIds.length ||
    !Number.isInteger(value.durationMs) ||
    value.durationMs < 0
  ) {
    throw new CompatibilityError("compatibility_scenario_result", scenarioId);
  }
  return value;
}

function repositoriesFromManifest(manifest) {
  const repositories = manifest.repositories;
  if (!Array.isArray(repositories)) throw new CompatibilityError("compatibility_manifest_repositories");
  const byId = new Map(repositories.map((repository) => [repository.id, repository.pin]));
  if (
    byId.size !== REPOSITORY_IDS.length ||
    REPOSITORY_IDS.some((id) => !SHA_PATTERN.test(byId.get(id) ?? ""))
  ) {
    throw new CompatibilityError("compatibility_manifest_repositories");
  }
  return Object.fromEntries(REPOSITORY_IDS.map((id) => [id, byId.get(id)]));
}

function samePins(left, right) {
  return REPOSITORY_IDS.every((id) => left[id] === right[id]);
}

function highestPriorityFailure(failures) {
  return failures.reduce((selected, candidate) =>
    selected === null ||
    TERMINAL_FAILURE_PRIORITY.get(candidate) > TERMINAL_FAILURE_PRIORITY.get(selected)
      ? candidate
      : selected, null);
}

async function atomicWriteJson(path, value) {
  await mkdir(dirname(path), { recursive: true });
  const temporary = resolve(dirname(path), `.${randomBytes(12).toString("hex")}.tmp`);
  const handle = await open(temporary, "wx", 0o600);
  try {
    await handle.writeFile(`${JSON.stringify(canonical(value), null, 2)}\n`, "utf8");
    await handle.sync();
  } finally {
    await handle.close();
  }
  await rename(temporary, path);
  const directory = await open(dirname(path), "r");
  try {
    await directory.sync();
  } finally {
    await directory.close();
  }
}

function docker(args, environment) {
  const result = spawnSync("docker", args, {
    encoding: "utf8",
    env: safeChildEnvironment(environment),
    shell: false,
  });
  if (result.error || result.status !== 0) {
    throw new CompatibilityError("compatibility_infra_inspection");
  }
  return result.stdout.trim();
}

async function defaultPreflightServices(services, context) {
  return services.map((id) => {
    const containerIds = docker([
      "ps", "-q",
      "--filter", "label=com.docker.compose.project=kokoro-infra",
      "--filter", `label=com.docker.compose.service=${id}`,
    ], context.environment).split(/\r?\n/u).filter(Boolean);
    if (containerIds.length !== 1) return { id, healthy: false };
    const [status = "", health = ""] = docker([
      "inspect", "--format",
      '{{.State.Status}}\t{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}',
      containerIds[0],
    ], context.environment).split("\t");
    return { id, healthy: status === "running" && ["healthy", "none"].includes(health) };
  });
}

function defaultVerifyPins({ environment, root: repositoryRoot, tree, manifestPath, matrixPath }) {
  const result = spawnSync(process.execPath, [
    resolve(repositoryRoot, "scripts/repository/verify-federated-repositories.mjs"),
    "--root", repositoryRoot,
    "--tree", tree,
    "--manifest", manifestPath,
    "--matrix", matrixPath,
  ], {
    cwd: repositoryRoot,
    encoding: "utf8",
    env: safeChildEnvironment(environment),
    shell: false,
  });
  if (result.error || result.status !== 0) {
    throw new CompatibilityError("compatibility_pin_verification");
  }
  return null;
}

async function writeLeaseFile(repositoryRoot, lease) {
  const directory = resolve(repositoryRoot, "tmp/compatibility-scopes");
  await mkdir(directory, { recursive: true });
  const path = resolve(directory, `${lease.runId}.json`);
  const handle = await open(path, "wx", 0o600);
  try {
    await handle.writeFile(`${JSON.stringify(lease)}\n`, "utf8");
    await handle.sync();
  } finally {
    await handle.close();
  }
  return path;
}

function parseMachineResult(output, scenarioId) {
  const lines = String(output ?? "").split(/\r?\n/u).filter(Boolean);
  if (lines.length !== 1) throw new CompatibilityError("compatibility_scenario_protocol", scenarioId);
  try {
    return validateScenarioResult(JSON.parse(lines[0]), scenarioId);
  } catch (error) {
    if (error instanceof CompatibilityError) throw error;
    throw new CompatibilityError("compatibility_scenario_protocol", scenarioId);
  }
}

function childExited(child) {
  return child.exitCode !== null || child.signalCode !== null;
}

async function waitForChildExit(child, timeoutMs) {
  if (childExited(child)) return true;
  return new Promise((resolveExit) => {
    const timer = setTimeout(() => {
      child.off("exit", onExit);
      resolveExit(false);
    }, timeoutMs);
    const onExit = () => {
      clearTimeout(timer);
      resolveExit(true);
    };
    child.once("exit", onExit);
  });
}

async function terminateProcessGroup(child) {
  if (child.pid === undefined || childExited(child)) return;
  try {
    process.kill(-child.pid, "SIGTERM");
  } catch (error) {
    if (error.code === "ESRCH") return;
    throw error;
  }
  if (await waitForChildExit(child, PROCESS_GROUP_GRACE_MS)) return;
  try {
    process.kill(-child.pid, "SIGKILL");
  } catch (error) {
    if (error.code !== "ESRCH") throw error;
  }
  await waitForChildExit(child, PROCESS_GROUP_GRACE_MS);
}

async function runScenarioProcess(command, { cwd, env, timeoutMs, signal }) {
  if (signal?.aborted) return { kind: "interrupted", machineOutput: "" };
  const child = spawn(command[0], command.slice(1), {
    cwd,
    env: safeChildEnvironment(env),
    detached: true,
    shell: false,
    stdio: ["ignore", "ignore", "ignore", "pipe"],
  });
  const chunks = [];
  let outputBytes = 0;
  let overflow = false;
  child.stdio[3]?.on("data", (chunk) => {
    outputBytes += chunk.length;
    if (outputBytes > MAX_MACHINE_RESULT_BYTES) {
      overflow = true;
      return;
    }
    chunks.push(chunk);
  });
  return new Promise((resolveProcess, rejectProcess) => {
    let settled = false;
    const cleanup = () => {
      clearTimeout(timer);
      signal?.removeEventListener("abort", onAbort);
      child.off("error", onError);
      child.off("exit", onExit);
    };
    const machineOutput = () => Buffer.concat(chunks).toString("utf8");
    const finishByTermination = async (kind) => {
      if (settled) return;
      settled = true;
      cleanup();
      try {
        await terminateProcessGroup(child);
        resolveProcess({ kind, machineOutput: machineOutput(), overflow });
      } catch (error) {
        rejectProcess(error);
      }
    };
    const onAbort = () => { void finishByTermination("interrupted"); };
    const onError = (error) => {
      if (settled) return;
      settled = true;
      cleanup();
      rejectProcess(error);
    };
    const onExit = (status, exitSignal) => {
      if (settled) return;
      settled = true;
      cleanup();
      resolveProcess({
        kind: "exit",
        status,
        signal: exitSignal,
        machineOutput: machineOutput(),
        overflow,
      });
    };
    const timer = setTimeout(() => { void finishByTermination("timeout"); }, timeoutMs);
    signal?.addEventListener("abort", onAbort, { once: true });
    child.once("error", onError);
    child.once("exit", onExit);
  });
}

async function defaultRunScenario(scenario, context) {
  const command = COMMANDS.get(scenario.commandId);
  if (!command) throw new CompatibilityError("compatibility_scenario_command", scenario.commandId);
  const started = Date.now();
  const result = await runScenarioProcess(command, {
    cwd: context.root,
    timeoutMs: scenario.timeoutSeconds * 1000,
    signal: context.signal,
    env: context.environment,
  });
  if (result.kind === "timeout") {
    return validateScenarioResult({
      schemaVersion: 1,
      scenarioId: scenario.id,
      outcome: "incomplete",
      reasonCode: "scenario_timeout",
      assertionIds: [`${scenario.id}:timeout`],
      durationMs: Date.now() - started,
    }, scenario.id);
  }
  if (result.kind === "interrupted") {
    return validateScenarioResult({
      schemaVersion: 1,
      scenarioId: scenario.id,
      outcome: "interrupted",
      reasonCode: "scenario_interrupted",
      assertionIds: [`${scenario.id}:interrupted`],
      durationMs: Date.now() - started,
    }, scenario.id);
  }
  if (result.overflow) throw new CompatibilityError("compatibility_scenario_protocol", scenario.id);
  const machine = parseMachineResult(result.machineOutput, scenario.id);
  if (result.status !== 0 && machine.outcome === "pass") {
    throw new CompatibilityError("compatibility_scenario_exit", scenario.id);
  }
  return machine;
}

async function defaultAcquireLease({ root: repositoryRoot }) {
  const stateRoot = resolve(repositoryRoot, "tmp/infra-scopes");
  const runId = `run_${randomBytes(8).toString("hex")}`;
  const endpointFingerprint = digest("kokoro-infra:local").slice(0, 32);
  const lease = await acquireScope({
    stateRoot,
    runId,
    endpointFingerprint,
    resources: COMPAT_DATA_RESOURCES,
  });
  return { ...lease, stateRoot, endpointFingerprint };
}

function makeEvidence({ matrix, matrixSource, manifestSource, pins, tree, now }) {
  const repositories = REPOSITORY_IDS.map((id) => ({ id, sha: pins[id] }));
  const contracts = matrix.contracts.map(({ id, version, artifactDigest }) => ({
    id,
    version,
    ...(artifactDigest === undefined ? {} : { artifactDigest }),
  }));
  const requiredScenarios = matrix.runtimeGate.scenarios
    .filter(({ required }) => required)
    .map(({ id, protocols }) => ({ id, protocols }));
  return {
    schemaVersion: 1,
    runnerVersion: 1,
    combinationId: matrix.combinationId,
    combinationDigest: digest({ repositories, contracts, requiredScenarios }),
    treeMode: tree,
    outcome: "running",
    reasonCode: "running",
    startedAt: now(),
    completedAt: null,
    durationMs: null,
    repositories,
    manifestDigest: digest(manifestSource),
    matrixDigest: digest(matrixSource),
    preflightPinVerification: "pass",
    postflightPinVerification: "pending",
    services: [],
    scenarios: [],
  };
}

async function runCompatibility(options, overrides = {}, control = {}) {
  const {
    environment = process.env,
    ...dependencyOverrides
  } = overrides;
  const evidencePath = await validateEvidenceTarget(options.root, options.evidencePath);
  const matrixSource = await readFile(options.matrixPath, "utf8");
  const manifestSource = await readFile(options.manifestPath, "utf8");
  const matrix = JSON.parse(matrixSource);
  const manifest = JSON.parse(manifestSource);
  const manifestPins = repositoriesFromManifest(manifest);
  const dependencies = {
    now: () => new Date().toISOString(),
    verifyPins: async (context) => {
      defaultVerifyPins(context);
      return { ...manifestPins };
    },
    preflightServices: defaultPreflightServices,
    acquireLease: defaultAcquireLease,
    provisionScope,
    cleanupScope,
    runScenario: defaultRunScenario,
    onEvidence: () => {},
    ...dependencyOverrides,
  };
  const context = {
    environment: safeChildEnvironment(environment),
    root: options.root,
    tree: options.tree,
    manifestPath: options.manifestPath,
    matrixPath: options.matrixPath,
    signal: control.signal,
  };
  const preflightPins = await dependencies.verifyPins(context);
  if (!samePins(preflightPins, manifestPins)) {
    throw new CompatibilityError("preflight_pin_drift");
  }
  const evidence = makeEvidence({
    matrix,
    matrixSource,
    manifestSource,
    pins: preflightPins,
    tree: options.tree,
    now: dependencies.now,
  });
  const write = async () => {
    await atomicWriteJson(evidencePath, evidence);
    dependencies.onEvidence(structuredClone(evidence));
  };
  await write();
  const startedMs = Date.parse(evidence.startedAt);
  let lease = null;
  let scopeFile = null;
  let exitCode = 3;
  const terminalFailures = [];
  try {
    evidence.services = await dependencies.preflightServices(
      matrix.runtimeGate.requiredServices,
      context,
    );
    const healthy =
      evidence.services.length === matrix.runtimeGate.requiredServices.length &&
      evidence.services.every(({ id, healthy: serviceHealthy }, index) =>
        id === matrix.runtimeGate.requiredServices[index] && serviceHealthy === true,
      );
    if (!healthy) {
      evidence.outcome = "incomplete";
      evidence.reasonCode = "required_service_unhealthy";
      exitCode = 2;
    } else {
      lease = await dependencies.acquireLease({ root: options.root, services: evidence.services });
      await dependencies.provisionScope({ lease });
      scopeFile = await writeLeaseFile(options.root, lease);
      for (const scenario of matrix.runtimeGate.scenarios) {
        const result = validateScenarioResult(
          await dependencies.runScenario(scenario, {
            ...context,
            scopeFile,
            environment: scenarioEnvironment(context.environment, scopeFile, scenario.id),
          }),
          scenario.id,
        );
        evidence.scenarios.push({
          ...result,
          required: scenario.required,
          participants: scenario.participants,
          protocols: scenario.protocols,
          commandId: scenario.commandId,
        });
        if (result.outcome === "interrupted") {
          evidence.outcome = "interrupted";
          evidence.reasonCode = result.reasonCode;
          exitCode = 130;
          break;
        }
      }
      if (evidence.outcome !== "interrupted") {
        const required = evidence.scenarios.filter(({ required }) => required);
        if (required.some(({ outcome }) => outcome === "fail")) {
          evidence.outcome = "fail";
          evidence.reasonCode = "required_scenario_failed";
          exitCode = 1;
        } else if (required.some(({ outcome }) => outcome !== "pass")) {
          evidence.outcome = "incomplete";
          evidence.reasonCode = "required_scenario_incomplete";
          exitCode = 2;
        } else {
          evidence.outcome = "pass";
          evidence.reasonCode = "ok";
          exitCode = 0;
        }
      }
    }
  } catch (error) {
    evidence.outcome = "error";
    evidence.reasonCode = error instanceof CompatibilityError ? error.code : "runner_internal_error";
    exitCode = 3;
  } finally {
    let scopeFileCleanupFailed = false;
    let leaseCleanupFailed = false;
    try {
      if (scopeFile !== null) {
        try {
          await rm(scopeFile, { force: true });
        } catch {
          scopeFileCleanupFailed = true;
        }
      }
    } finally {
      if (lease !== null) {
        try {
          await dependencies.cleanupScope({
            stateRoot: lease.stateRoot,
            runId: lease.runId,
            leaseToken: lease.leaseToken,
            endpointFingerprint: lease.endpointFingerprint,
          });
        } catch {
          leaseCleanupFailed = true;
        }
      }
    }
    if (scopeFileCleanupFailed) terminalFailures.push("scope_file_cleanup_failed");
    if (leaseCleanupFailed) terminalFailures.push("lease_cleanup_failed");
  }
  try {
    const postflightPins = await dependencies.verifyPins(context);
    if (!samePins(postflightPins, preflightPins)) {
      terminalFailures.push("postflight_pin_drift");
      evidence.postflightPinVerification = "fail";
    } else {
      evidence.postflightPinVerification = "pass";
    }
  } catch {
    terminalFailures.push("postflight_pin_verification_failed");
    evidence.postflightPinVerification = "fail";
  }
  const terminalFailure = highestPriorityFailure(terminalFailures);
  if (terminalFailure !== null) {
    evidence.outcome = "error";
    evidence.reasonCode = terminalFailure;
    exitCode = 3;
  }
  evidence.completedAt = dependencies.now();
  evidence.durationMs = Math.max(0, Date.parse(evidence.completedAt) - startedMs);
  await write();
  return { evidence, exitCode };
}

if (process.argv[1] && pathToFileURL(process.argv[1]).href === import.meta.url) {
  const controller = new AbortController();
  const interrupt = (signal) => controller.abort(signal);
  process.once("SIGINT", interrupt);
  process.once("SIGTERM", interrupt);
  try {
    const result = await runCompatibility(
      parseRunnerArguments(process.argv.slice(2)),
      {},
      { signal: controller.signal },
    );
    process.stdout.write(`pinned_compatibility_${result.evidence.outcome}: ${result.evidence.combinationId}\n`);
    process.exitCode = result.exitCode;
  } catch (error) {
    const code = error instanceof CompatibilityError ? error.code : "compatibility_runner_error";
    process.stderr.write(`${sanitizeText(code)}\n`);
    process.exitCode = 3;
  } finally {
    process.off("SIGINT", interrupt);
    process.off("SIGTERM", interrupt);
  }
}

export {
  parseRunnerArguments,
  runCompatibility,
  runScenarioProcess,
  sanitizeText,
  validateEvidenceTarget,
  validateScenarioResult,
};
