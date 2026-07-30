#!/usr/bin/env node

import { spawnSync } from "node:child_process";
import { access, readFile } from "node:fs/promises";
import { dirname, relative, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const REPOSITORY_IDS = ["kokoro-agent", "kokoro-platform", "kokoro-session", "kokoro-web"];
const TOP_LEVEL_KEYS = ["repositories", "repositoryTopology", "schemaVersion"];
const REPOSITORY_KEYS = [
  "artifacts",
  "id",
  "lockfiles",
  "origin",
  "path",
  "pin",
  "protocols",
  "recoverableRef",
  "requiredWorkflows",
];
const ARTIFACT_KEYS = ["descriptor", "id"];
const PROTOCOL_KEYS = ["id", "role", "version"];
const MATRIX_KEYS = ["combinationId", "contracts", "requiredGates", "runtimeGate", "schemaVersion"];
const CONTRACT_KEYS = ["consumers", "id", "providers", "version"];
const ATTESTED_CONTRACT_KEYS = ["artifactDigest", ...CONTRACT_KEYS];
const RUNTIME_GATE_KEYS = ["requiredServices", "scenarios", "schemaVersion"];
const SCENARIO_KEYS = ["commandId", "id", "participants", "protocols", "required", "timeoutSeconds"];
const SCENARIO_PROTOCOL_KEYS = ["id", "version"];
const RUNTIME_SERVICES = new Set(["postgres", "redis", "mongo", "minio", "litellm"]);
const SCENARIO_COMMANDS = new Map([
  ["web-session-http-sse", "node-web-session-http-sse-v1"],
  ["session-platform-internal-rpc", "node-session-platform-internal-rpc-v1"],
  ["session-agent-durable-localfake", "python-session-agent-durable-v1"],
  ["agent-model-gateway-localfake", "python-agent-model-gateway-v1"],
  ["hub-runtime", "node-hub-runtime-v1"],
  ["platform-admin-auth-connect", "node-platform-admin-auth-connect-v1"],
]);
const SHA_PATTERN = /^[0-9a-f]{40}$/u;
const ARTIFACT_DIGEST_PATTERN = /^[0-9a-f]{64}$/u;

class RepositoryError extends Error {
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

function nonEmptyStrings(value) {
  return Array.isArray(value) && value.length > 0 && value.every((item) => typeof item === "string" && item !== "");
}

function uniqueStrings(value) {
  return nonEmptyStrings(value) && new Set(value).size === value.length;
}

export function parseManifest(source) {
  let manifest;
  try {
    manifest = JSON.parse(source);
  } catch (error) {
    throw new RepositoryError("manifest_json", error.message);
  }
  if (!exactKeys(manifest, TOP_LEVEL_KEYS)) throw new RepositoryError("manifest_top_level");
  if (manifest.schemaVersion !== 1 || manifest.repositoryTopology !== "federated-submodules-v1") {
    throw new RepositoryError("manifest_topology");
  }
  if (!Array.isArray(manifest.repositories)) throw new RepositoryError("manifest_inventory");
  const actualIds = manifest.repositories.map(({ id }) => id).sort();
  if (actualIds.length !== REPOSITORY_IDS.length || actualIds.some((id, index) => id !== [...REPOSITORY_IDS].sort()[index])) {
    throw new RepositoryError("manifest_inventory");
  }
  for (const repository of manifest.repositories) {
    if (!exactKeys(repository, REPOSITORY_KEYS)) throw new RepositoryError("manifest_repository_fields", repository.id);
    if (
      typeof repository.id !== "string" ||
      repository.path !== repository.id ||
      typeof repository.origin !== "string" ||
      !repository.origin.startsWith("https://github.com/LordFoxFairy/") ||
      !SHA_PATTERN.test(repository.pin) ||
      !repository.recoverableRef.startsWith("refs/tags/") ||
      !nonEmptyStrings(repository.lockfiles) ||
      !nonEmptyStrings(repository.requiredWorkflows) ||
      !Array.isArray(repository.artifacts) || repository.artifacts.length === 0 ||
      !Array.isArray(repository.protocols) || repository.protocols.length === 0
    ) throw new RepositoryError("manifest_repository_values", repository.id);
    for (const artifact of repository.artifacts) {
      if (!exactKeys(artifact, ARTIFACT_KEYS) || typeof artifact.id !== "string" || typeof artifact.descriptor !== "string") {
        throw new RepositoryError("manifest_artifact", repository.id);
      }
    }
    for (const protocol of repository.protocols) {
      if (
        !exactKeys(protocol, PROTOCOL_KEYS) ||
        typeof protocol.id !== "string" ||
        !Number.isInteger(protocol.version) ||
        !["provider", "consumer"].includes(protocol.role)
      ) throw new RepositoryError("manifest_protocol", repository.id);
    }
  }
  return manifest;
}

export function parseGitmodules(source) {
  const repositories = [];
  let current = null;
  for (const rawLine of source.split(/\r?\n/u)) {
    const line = rawLine.trim();
    if (line === "") continue;
    const section = /^\[submodule "([^"]+)"\]$/u.exec(line);
    if (section) {
      current = { name: section[1] };
      repositories.push(current);
      continue;
    }
    const field = /^(\w+)\s*=\s*(.+)$/u.exec(line);
    if (!current || !field) throw new RepositoryError("gitmodules_syntax", line);
    if (!["path", "url"].includes(field[1])) throw new RepositoryError("gitmodules_field", field[1]);
    if (Object.hasOwn(current, field[1])) throw new RepositoryError("gitmodules_duplicate", field[1]);
    current[field[1]] = field[2];
  }
  const ids = repositories.map(({ name }) => name).sort();
  if (ids.length !== REPOSITORY_IDS.length || ids.some((id, index) => id !== [...REPOSITORY_IDS].sort()[index])) {
    throw new RepositoryError("gitmodules_inventory");
  }
  for (const repository of repositories) {
    if (repository.path !== repository.name || typeof repository.url !== "string") {
      throw new RepositoryError("gitmodules_values", repository.name);
    }
  }
  return repositories;
}

export function parsePinLine(line, path) {
  const tree = /^160000\s+commit\s+([0-9a-f]{40})\t(.+)$/u.exec(line);
  const index = /^160000\s+([0-9a-f]{40})\s+0\t(.+)$/u.exec(line);
  const match = tree ?? index;
  if (!match || match[2] !== path) throw new RepositoryError("gitlink_invalid", path);
  return match[1];
}

function parseRemoteRefs(source) {
  const refs = new Map();
  for (const line of source.split(/\r?\n/u)) {
    if (!line) continue;
    const [sha, ref] = line.split(/\s+/u);
    if (SHA_PATTERN.test(sha ?? "") && ref) refs.set(ref, sha);
  }
  return refs;
}

export function remoteTagTargetsPin(source, ref, pin) {
  if (!ref.startsWith("refs/tags/")) throw new RepositoryError("recoverable_ref_not_tag", ref);
  const refs = parseRemoteRefs(source);
  const peeled = refs.get(`${ref}^{}`);
  return peeled === undefined ? refs.get(ref) === pin : peeled === pin;
}

export function validateCompatibility(manifest, matrix) {
  if (!exactKeys(matrix, MATRIX_KEYS) || matrix.schemaVersion !== 1 || typeof matrix.combinationId !== "string" || !nonEmptyStrings(matrix.requiredGates) || !Array.isArray(matrix.contracts)) {
    throw new RepositoryError("compatibility_schema");
  }
  const contracts = new Map();
  for (const contract of matrix.contracts) {
    const keysValid = exactKeys(contract, CONTRACT_KEYS) || exactKeys(contract, ATTESTED_CONTRACT_KEYS);
    const digestValid = !Object.hasOwn(contract, "artifactDigest") || ARTIFACT_DIGEST_PATTERN.test(contract.artifactDigest);
    if (!keysValid || !digestValid || typeof contract.id !== "string" || !Number.isInteger(contract.version) || !nonEmptyStrings(contract.providers) || !nonEmptyStrings(contract.consumers)) {
      throw new RepositoryError("compatibility_contract");
    }
    if (contract.id === "platform-admin-auth" && !Object.hasOwn(contract, "artifactDigest")) {
      throw new RepositoryError("compatibility_contract", contract.id);
    }
    if (contracts.has(contract.id)) throw new RepositoryError("compatibility_duplicate", contract.id);
    contracts.set(contract.id, contract);
  }
  for (const repository of manifest.repositories) {
    for (const protocol of repository.protocols) {
      const contract = contracts.get(protocol.id);
      const participants = protocol.role === "provider" ? contract?.providers : contract?.consumers;
      if (contract?.version !== protocol.version || !participants?.includes(repository.id)) {
        throw new RepositoryError("compatibility_protocol", `${repository.id}:${protocol.id}`);
      }
    }
  }
  for (const contract of contracts.values()) {
    for (const id of [...contract.providers, ...contract.consumers]) {
      const repository = manifest.repositories.find((candidate) => candidate.id === id);
      const role = contract.providers.includes(id) ? "provider" : "consumer";
      if (!repository?.protocols.some((protocol) => protocol.id === contract.id && protocol.version === contract.version && protocol.role === role)) {
        throw new RepositoryError("compatibility_participant", `${id}:${contract.id}`);
      }
    }
  }
  const runtime = matrix.runtimeGate;
  if (
    !exactKeys(runtime, RUNTIME_GATE_KEYS) ||
    runtime.schemaVersion !== 1 ||
    !uniqueStrings(runtime.requiredServices) ||
    !runtime.requiredServices.every((service) => RUNTIME_SERVICES.has(service)) ||
    !Array.isArray(runtime.scenarios) ||
    runtime.scenarios.length === 0
  ) {
    throw new RepositoryError("compatibility_runtime_schema");
  }
  const scenarioIds = new Set();
  const commandIds = new Set();
  for (const scenario of runtime.scenarios) {
    if (!exactKeys(scenario, SCENARIO_KEYS)) {
      throw new RepositoryError("compatibility_runtime_scenario");
    }
    if (
      typeof scenario.id !== "string" ||
      SCENARIO_COMMANDS.get(scenario.id) !== scenario.commandId ||
      typeof scenario.commandId !== "string"
    ) {
      throw new RepositoryError("compatibility_runtime_command", scenario.id);
    }
    if (scenarioIds.has(scenario.id) || commandIds.has(scenario.commandId)) {
      throw new RepositoryError("compatibility_runtime_duplicate", scenario.id);
    }
    scenarioIds.add(scenario.id);
    commandIds.add(scenario.commandId);
    if (
      typeof scenario.required !== "boolean" ||
      !uniqueStrings(scenario.participants) ||
      !scenario.participants.every((id) => REPOSITORY_IDS.includes(id))
    ) {
      throw new RepositoryError("compatibility_runtime_participants", scenario.id);
    }
    if (
      !Number.isInteger(scenario.timeoutSeconds) ||
      scenario.timeoutSeconds < 10 ||
      scenario.timeoutSeconds > 900
    ) {
      throw new RepositoryError("compatibility_runtime_timeout", scenario.id);
    }
    if (!Array.isArray(scenario.protocols) || scenario.protocols.length === 0) {
      throw new RepositoryError("compatibility_runtime_protocols", scenario.id);
    }
    const seenProtocols = new Set();
    for (const protocol of scenario.protocols) {
      if (
        !exactKeys(protocol, SCENARIO_PROTOCOL_KEYS) ||
        typeof protocol.id !== "string" ||
        !Number.isInteger(protocol.version) ||
        seenProtocols.has(protocol.id)
      ) {
        throw new RepositoryError("compatibility_runtime_protocols", scenario.id);
      }
      seenProtocols.add(protocol.id);
      const contract = contracts.get(protocol.id);
      if (
        contract?.version !== protocol.version ||
        ![...contract.providers, ...contract.consumers].every((id) => scenario.participants.includes(id))
      ) {
        throw new RepositoryError("compatibility_runtime_protocol", `${scenario.id}:${protocol.id}`);
      }
    }
  }
  for (const contract of contracts.values()) {
    const covered = runtime.scenarios.some(
      (scenario) =>
        scenario.required &&
        scenario.protocols.some(
          (protocol) => protocol.id === contract.id && protocol.version === contract.version,
        ),
    );
    if (!covered) throw new RepositoryError("compatibility_contract_uncovered", contract.id);
  }
}

function git(cwd, args, { allowFailure = false } = {}) {
  const result = spawnSync("git", args, { cwd, encoding: "utf8", shell: false });
  if (result.error) throw result.error;
  if (result.status !== 0 && !allowFailure) throw new RepositoryError("git_command", `${args.join(" ")}: ${result.stderr.trim()}`);
  return result;
}

function gitText(cwd, args) {
  return git(cwd, args).stdout.trim();
}

function parseArguments(argv) {
  const options = { root: process.cwd(), tree: "head", remote: false, manifest: null, matrix: null };
  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    if (argument === "--remote") { options.remote = true; continue; }
    const value = argv[index + 1];
    if (!value) throw new RepositoryError("arguments", argument);
    index += 1;
    if (argument === "--root") options.root = resolve(value);
    else if (argument === "--tree") options.tree = value;
    else if (argument === "--manifest") options.manifest = resolve(value);
    else if (argument === "--matrix") options.matrix = resolve(value);
    else throw new RepositoryError("arguments", argument);
  }
  if (!["head", "index"].includes(options.tree)) throw new RepositoryError("arguments", "tree");
  options.manifest ??= resolve(options.root, "config/repository/federated-repositories.json");
  options.matrix ??= resolve(options.root, "config/repository/compatibility-matrix.json");
  return options;
}

async function verify(options) {
  const manifest = parseManifest(await readFile(options.manifest, "utf8"));
  const matrix = JSON.parse(await readFile(options.matrix, "utf8"));
  validateCompatibility(manifest, matrix);
  const modules = parseGitmodules(await readFile(resolve(options.root, ".gitmodules"), "utf8"));
  const modulesByName = new Map(modules.map((entry) => [entry.name, entry]));

  for (const repository of manifest.repositories) {
    const module = modulesByName.get(repository.id);
    if (module?.path !== repository.path || module.url !== repository.origin) throw new RepositoryError("gitmodules_manifest", repository.id);
    const line = options.tree === "head"
      ? gitText(options.root, ["ls-tree", "HEAD", repository.path])
      : gitText(options.root, ["ls-files", "--stage", repository.path]);
    const pin = parsePinLine(line, repository.path);
    if (pin !== repository.pin) throw new RepositoryError("manifest_pin_mismatch", repository.id);
    const child = resolve(options.root, repository.path);
    if (gitText(child, ["rev-parse", "HEAD"]) !== pin) throw new RepositoryError("checkout_pin_mismatch", repository.id);
    if (gitText(child, ["status", "--porcelain=v1", "--untracked-files=no"]) !== "") throw new RepositoryError("child_tracked_dirty", repository.id);
    if (gitText(child, ["remote", "get-url", "origin"]) !== repository.origin) throw new RepositoryError("child_origin", repository.id);
    for (const path of [...repository.lockfiles, ...repository.requiredWorkflows, ...repository.artifacts.map(({ descriptor }) => descriptor)]) {
      const absolute = resolve(child, path);
      if (!absolute.startsWith(`${child}/`)) throw new RepositoryError("child_path", `${repository.id}:${path}`);
      await access(absolute).catch(() => { throw new RepositoryError("child_file_missing", `${repository.id}:${path}`); });
    }
    if (options.remote) {
      const refs = gitText(child, ["ls-remote", repository.origin, repository.recoverableRef, `${repository.recoverableRef}^{}`]);
      if (!remoteTagTargetsPin(refs, repository.recoverableRef, pin)) throw new RepositoryError("recoverable_ref_mismatch", repository.id);
    }
  }
  const relativeManifest = relative(options.root, options.manifest).replaceAll("\\", "/");
  process.stdout.write(`federated_repositories_verified: ${manifest.repositories.length} tree=${options.tree} manifest=${relativeManifest}\n`);
}

if (process.argv[1] && pathToFileURL(process.argv[1]).href === import.meta.url) {
  try {
    await verify(parseArguments(process.argv.slice(2)));
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    process.stderr.write(`${message}\n`);
    process.exitCode = 1;
  }
}
