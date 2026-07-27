import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

import {
  parseGitmodules,
  parseManifest,
  parsePinLine,
  remoteTagTargetsPin,
  validateCompatibility,
} from "./verify-federated-repositories.mjs";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const ids = ["kokoro-agent", "kokoro-platform", "kokoro-session", "kokoro-web"];

function repository(id) {
  return {
    id,
    path: id,
    origin: `https://github.com/LordFoxFairy/${id}.git`,
    pin: "a".repeat(40),
    lockfiles: [id === "kokoro-agent" ? "uv.lock" : id === "kokoro-web" ? "pnpm-lock.yaml" : "package-lock.json"],
    requiredWorkflows: [".github/workflows/ci.yml"],
    artifacts: [{ id: `${id}-service`, descriptor: "package.json" }],
    protocols: [{ id: "runtime-v1", version: 1, role: id === "kokoro-platform" ? "provider" : "consumer" }],
    recoverableRef: `refs/tags/candidate-${id}`,
  };
}

function manifest() {
  return {
    schemaVersion: 1,
    repositoryTopology: "federated-submodules-v1",
    repositories: ids.map(repository),
  };
}

test("manifest schema is closed and requires the exact four repositories", () => {
  assert.deepEqual(parseManifest(JSON.stringify(manifest())).repositories.map(({ id }) => id), ids);
  assert.throws(() => parseManifest(JSON.stringify({ ...manifest(), extra: true })), /manifest_top_level/u);
  const missing = manifest();
  missing.repositories.pop();
  assert.throws(() => parseManifest(JSON.stringify(missing)), /manifest_inventory/u);
  const duplicate = manifest();
  duplicate.repositories[3].id = "kokoro-agent";
  assert.throws(() => parseManifest(JSON.stringify(duplicate)), /manifest_inventory/u);
});

test("gitmodules accepts only name/path/url and rejects floating controls", async () => {
  const source = ids.map((id) => `[submodule "${id}"]\n\tpath = ${id}\n\turl = https://github.com/LordFoxFairy/${id}.git\n`).join("");
  assert.equal(parseGitmodules(source).length, 4);
  assert.throws(() => parseGitmodules(`${source}\tbranch = main\n`), /gitmodules_field/u);
  assert.throws(() => parseGitmodules(`${source}\tupdate = merge\n`), /gitmodules_field/u);

  const current = await readFile(resolve(root, ".gitmodules"), "utf8");
  assert.equal(parseGitmodules(current).length, 4);
});

test("head and proposed-index gitlink formats require mode 160000", () => {
  assert.equal(parsePinLine(`160000 commit ${"a".repeat(40)}\tkokoro-agent`, "kokoro-agent"), "a".repeat(40));
  assert.equal(parsePinLine(`160000 ${"b".repeat(40)} 0\tkokoro-agent`, "kokoro-agent"), "b".repeat(40));
  assert.throws(() => parsePinLine(`100644 blob ${"a".repeat(40)}\tkokoro-agent`, "kokoro-agent"), /gitlink_invalid/u);
});

test("recoverable refs must be exact tags and annotated tags use their peeled commit", () => {
  const pin = "a".repeat(40);
  assert.equal(remoteTagTargetsPin(`bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb\trefs/tags/candidate\n${pin}\trefs/tags/candidate^{}\n`, "refs/tags/candidate", pin), true);
  assert.equal(remoteTagTargetsPin(`${pin}\trefs/tags/candidate\n`, "refs/tags/candidate", pin), true);
  assert.equal(remoteTagTargetsPin(`${"b".repeat(40)}\trefs/tags/candidate\n`, "refs/tags/candidate", pin), false);
  assert.throws(() => remoteTagTargetsPin(`${pin}\trefs/heads/main\n`, "refs/heads/main", pin), /recoverable_ref_not_tag/u);
});

test("compatibility matrix rejects undeclared or version-skewed protocols", () => {
  const parsed = parseManifest(JSON.stringify(manifest()));
  const compatible = {
    schemaVersion: 1,
    combinationId: "wave1",
    contracts: [{ id: "runtime-v1", version: 1, providers: ["kokoro-platform"], consumers: ["kokoro-agent", "kokoro-session", "kokoro-web"] }],
    requiredGates: ["contract", "runtime-smoke"],
    runtimeGate: {
      schemaVersion: 1,
      requiredServices: ["mysql", "redis", "mongo", "minio", "litellm"],
      scenarios: [{
        id: "session-platform-internal-rpc",
        commandId: "node-session-platform-internal-rpc-v1",
        required: true,
        participants: ["kokoro-agent", "kokoro-platform", "kokoro-session", "kokoro-web"],
        protocols: [{ id: "runtime-v1", version: 1 }],
        timeoutSeconds: 180,
      }],
    },
  };
  assert.doesNotThrow(() => validateCompatibility(parsed, compatible));
  const skewed = structuredClone(compatible);
  skewed.contracts[0].version = 2;
  assert.throws(() => validateCompatibility(parsed, skewed), /compatibility_protocol/u);
});

test("runtime compatibility schema is closed and every contract has required coverage", () => {
  const parsed = parseManifest(JSON.stringify(manifest()));
  const matrix = {
    schemaVersion: 1,
    combinationId: "wave1",
    contracts: [{ id: "runtime-v1", version: 1, providers: ["kokoro-platform"], consumers: ["kokoro-agent", "kokoro-session", "kokoro-web"] }],
    requiredGates: ["runtime-smoke"],
    runtimeGate: {
      schemaVersion: 1,
      requiredServices: ["mysql", "redis", "mongo", "minio", "litellm"],
      scenarios: [{
        id: "session-platform-internal-rpc",
        commandId: "node-session-platform-internal-rpc-v1",
        required: true,
        participants: ["kokoro-agent", "kokoro-platform", "kokoro-session", "kokoro-web"],
        protocols: [{ id: "runtime-v1", version: 1 }],
        timeoutSeconds: 180,
      }],
    },
  };
  assert.doesNotThrow(() => validateCompatibility(parsed, matrix));

  const uncovered = structuredClone(matrix);
  uncovered.runtimeGate.scenarios[0].protocols = [];
  assert.throws(() => validateCompatibility(parsed, uncovered), /compatibility_runtime_protocols|compatibility_contract_uncovered/u);

  const optionalOnly = structuredClone(matrix);
  optionalOnly.runtimeGate.scenarios[0].required = false;
  assert.throws(() => validateCompatibility(parsed, optionalOnly), /compatibility_contract_uncovered/u);

  const arbitraryCommand = structuredClone(matrix);
  arbitraryCommand.runtimeGate.scenarios[0].commandId = "bash-anything";
  assert.throws(() => validateCompatibility(parsed, arbitraryCommand), /compatibility_runtime_command/u);

  const unknownField = structuredClone(matrix);
  unknownField.runtimeGate.extra = true;
  assert.throws(() => validateCompatibility(parsed, unknownField), /compatibility_runtime_schema/u);

  const duplicateParticipant = structuredClone(matrix);
  duplicateParticipant.runtimeGate.scenarios[0].participants.push("kokoro-web");
  assert.throws(() => validateCompatibility(parsed, duplicateParticipant), /compatibility_runtime_participants/u);

  const excessiveTimeout = structuredClone(matrix);
  excessiveTimeout.runtimeGate.scenarios[0].timeoutSeconds = 901;
  assert.throws(() => validateCompatibility(parsed, excessiveTimeout), /compatibility_runtime_timeout/u);
});

test("root CI checks out only recorded pins and uses the root-only tooling lock", async () => {
  const workflow = await readFile(resolve(root, ".github/workflows/contract.yml"), "utf8");
  assert.match(workflow, /submodules:\s*recursive/u);
  assert.doesNotMatch(workflow, /repository:\s*LordFoxFairy\/kokoro-/u);
  assert.doesNotMatch(workflow, /ref:\s*main/u);
  assert.doesNotMatch(workflow, /submodule update --remote/u);
  assert.match(workflow, /python-version:\s*["']3\.11["']/u);
  assert.match(workflow, /astral-sh\/setup-uv/u);
  assert.match(workflow, /uv sync --locked/u);
  assert.match(workflow, /verify-federated-repositories\.mjs --tree head --remote/u);
  assert.match(workflow, /uv run python contract\/check\.py/u);
  assert.match(workflow, /uv run pytest contract\/tests -q/u);
  assert.match(workflow, /corepack enable/u);
  assert.match(workflow, /uv sync --project kokoro-agent --locked/u);
  assert.match(workflow, /npm ci --prefix kokoro-session/u);
  assert.match(workflow, /pnpm --dir kokoro-platform install --frozen-lockfile/u);
  assert.match(workflow, /pnpm --dir kokoro-web install --frozen-lockfile/u);
  assert.match(workflow, /trap cleanup EXIT INT TERM/u);
  assert.match(workflow, /manager\.mjs ensure --profiles full --scope ci-federated/u);
  assert.match(workflow, /run-pinned-compatibility\.mjs[\s\S]*--tree head/u);
  assert.match(workflow, /manager\.mjs stop --profiles full --scope ci-federated/u);
  assert.doesNotMatch(workflow, /deploy\/\.env\.dev/u);
});
