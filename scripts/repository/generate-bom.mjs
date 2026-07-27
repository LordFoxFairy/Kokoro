#!/usr/bin/env node

// Root repository Bill of Materials.
//
// The BOM is the versioned record of one atomic Root pin promotion. It binds a promotion commit to
// the four exact child pins, each child's independent recoverable tag, the closed protocol/contract
// list, and length-framed digests of the manifest, contract matrix and committed evidence.
//
// A Root manifest may only reference its parent or an earlier commit, so `promotionCommit` must be
// an existing commit that is HEAD or an ancestor of HEAD, and the document may never carry a field
// naming the commit that contains it. The BOM is generated after the promotion commit and committed
// separately; `--check` therefore reuses the recorded `promotionCommit` instead of re-reading HEAD.

import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { readFile, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";

import {
  parseManifest,
  parsePinLine,
  validateCompatibility,
} from "./verify-federated-repositories.mjs";

const BOM_PATH = "config/repository/bom.json";
const MANIFEST_PATH = "config/repository/federated-repositories.json";
const MATRIX_PATH = "config/repository/compatibility-matrix.json";
const EVIDENCE_PATHS = [
  "docs/reports/evidence/wave-0/federated-repository-baseline.md",
  "docs/reports/evidence/wave-0/ownership-attestation.yaml",
];
const REPOSITORY_IDS = ["kokoro-agent", "kokoro-platform", "kokoro-session", "kokoro-web"];
const GENERATOR_VERSION = 1;
const SCHEMA_VERSION = 1;
const REPOSITORY_TOPOLOGY = "federated-submodules-v1";
const TREE_MODES = new Set(["head", "index"]);
const SHA_PATTERN = /^[0-9a-f]{40}$/u;
const DIGEST_PATTERN = /^[0-9a-f]{64}$/u;
const DIGEST_FIELDS = ["contractsDigest", "evidenceDigest", "manifestDigest", "matrixDigest"];
const SELF_REFERENCE_FIELDS = ["bomCommit", "containingCommit", "selfCommit", "verifiedCommit"];

export const BOM_KEYS = [
  "contracts",
  "contractsDigest",
  "evidence",
  "evidenceDigest",
  "generatorVersion",
  "manifestDigest",
  "matrixDigest",
  "promotionCommit",
  "repositories",
  "repositoryTopology",
  "runtimeGate",
  "schemaVersion",
];
export const BOM_REPOSITORY_KEYS = ["id", "origin", "path", "pin", "protocols", "recoverableRef"];
export const BOM_PROTOCOL_KEYS = ["id", "role", "version"];
export const BOM_CONTRACT_KEYS = ["consumers", "id", "providers", "version"];
export const BOM_ATTESTED_CONTRACT_KEYS = ["artifactDigest", ...BOM_CONTRACT_KEYS];
export const BOM_EVIDENCE_KEYS = ["digest", "path"];
export const BOM_RUNTIME_GATE_KEYS = [
  "combinationDigest",
  "combinationId",
  "evidenceDigest",
  "outcome",
  "treeMode",
];

export class BomError extends Error {
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

function canonicalJson(value) {
  return JSON.stringify(canonical(value));
}

// Length-framed SHA-256: every part is prefixed with its byte length, so no concatenation of
// different part lists can collide.
export function framedDigest(parts) {
  const hash = createHash("sha256");
  for (const part of parts) {
    const bytes = Buffer.isBuffer(part) ? part : Buffer.from(String(part), "utf8");
    hash.update(`${bytes.byteLength}:`, "utf8");
    hash.update(bytes);
  }
  return hash.digest("hex");
}

// Mirrors the combination digest written by `run-pinned-compatibility.mjs`; the runner remains the
// only producer of runtime evidence, and `generate-bom.test.mjs` guards the two against drift.
export function combinationDigest(manifest, matrix) {
  const pins = new Map(manifest.repositories.map(({ id, pin }) => [id, pin]));
  const repositories = REPOSITORY_IDS.map((id) => ({ id, sha: pins.get(id) }));
  const contracts = matrix.contracts.map(({ id, version, artifactDigest }) => ({
    id,
    version,
    ...(artifactDigest === undefined ? {} : { artifactDigest }),
  }));
  const requiredScenarios = matrix.runtimeGate.scenarios
    .filter(({ required }) => required)
    .map(({ id, protocols }) => ({ id, protocols }));
  return createHash("sha256")
    .update(canonicalJson({ repositories, contracts, requiredScenarios }))
    .digest("hex");
}

function git(root, args, { allowFailure = false } = {}) {
  const result = spawnSync("git", args, { cwd: root, encoding: "utf8", shell: false });
  if (result.error) throw result.error;
  if (result.status !== 0 && !allowFailure) {
    throw new BomError("bom_git_command", `${args.join(" ")}: ${result.stderr.trim()}`);
  }
  return result;
}

export function parseArguments(argv) {
  const options = { root: process.cwd(), check: false, promotionCommit: null, runtimeEvidence: null };
  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    if (argument === "--check") {
      options.check = true;
      continue;
    }
    const value = argv[index + 1];
    if (!value) throw new BomError("bom_arguments_invalid", argument);
    index += 1;
    if (argument === "--root") options.root = resolve(value);
    else if (argument === "--promotion-commit") options.promotionCommit = value;
    else if (argument === "--runtime-evidence") options.runtimeEvidence = resolve(value);
    else throw new BomError("bom_arguments_invalid", argument);
  }
  return options;
}

async function readSources(root) {
  const manifestSource = await readFile(resolve(root, MANIFEST_PATH), "utf8").catch((error) => {
    throw new BomError("bom_manifest_unreadable", error.message);
  });
  let manifest;
  try {
    manifest = parseManifest(manifestSource);
  } catch (error) {
    throw new BomError("bom_manifest_invalid", error.message);
  }
  const matrixSource = await readFile(resolve(root, MATRIX_PATH), "utf8").catch((error) => {
    throw new BomError("bom_matrix_unreadable", error.message);
  });
  let matrix;
  try {
    matrix = JSON.parse(matrixSource);
    validateCompatibility(manifest, matrix);
  } catch (error) {
    throw new BomError("bom_matrix_invalid", error.message);
  }
  return { manifest, manifestSource, matrix, matrixSource };
}

function resolvePromotionCommit(root, requested) {
  const commit = requested ?? git(root, ["rev-parse", "HEAD"]).stdout.trim();
  if (!SHA_PATTERN.test(commit)) {
    throw new BomError("bom_promotion_commit_invalid", "expected a full commit SHA");
  }
  if (git(root, ["rev-parse", "--verify", `${commit}^{commit}`], { allowFailure: true }).status !== 0) {
    throw new BomError("bom_promotion_commit_invalid", "commit does not exist");
  }
  if (git(root, ["merge-base", "--is-ancestor", commit, "HEAD"], { allowFailure: true }).status !== 0) {
    throw new BomError("bom_promotion_commit_invalid", "commit must be HEAD or an ancestor of HEAD");
  }
  return commit;
}

function assertPromotedPins(root, promotionCommit, manifest) {
  for (const repository of manifest.repositories) {
    const line = git(root, ["ls-tree", promotionCommit, repository.path]).stdout.trim();
    let pin;
    try {
      pin = parsePinLine(line, repository.path);
    } catch (error) {
      throw new BomError("bom_promotion_gitlink_invalid", repository.id);
    }
    if (pin !== repository.pin) throw new BomError("bom_promotion_pin_mismatch", repository.id);
  }
}

async function readRuntimeGate(path, { manifest, matrix }) {
  let source;
  try {
    source = await readFile(path, "utf8");
  } catch (error) {
    const code = error.code === "ENOENT"
      ? "bom_runtime_evidence_missing"
      : "bom_runtime_evidence_unreadable";
    throw new BomError(code, error.message);
  }
  let evidence;
  try {
    evidence = JSON.parse(source);
  } catch (error) {
    throw new BomError("bom_runtime_evidence_invalid", error.message);
  }
  if (
    evidence === null ||
    typeof evidence !== "object" ||
    Array.isArray(evidence) ||
    evidence.schemaVersion !== 1 ||
    typeof evidence.combinationId !== "string" ||
    !DIGEST_PATTERN.test(evidence.combinationDigest ?? "") ||
    !TREE_MODES.has(evidence.treeMode)
  ) {
    throw new BomError("bom_runtime_evidence_invalid", "required fields");
  }
  if (evidence.combinationId !== matrix.combinationId) {
    throw new BomError("bom_runtime_evidence_invalid", "combinationId");
  }
  if (
    evidence.outcome !== "pass" ||
    evidence.reasonCode !== "ok" ||
    evidence.preflightPinVerification !== "pass" ||
    evidence.postflightPinVerification !== "pass"
  ) {
    throw new BomError("bom_runtime_evidence_not_pass", String(evidence.reasonCode));
  }
  const pins = new Map(manifest.repositories.map(({ id, pin }) => [id, pin]));
  if (
    !Array.isArray(evidence.repositories) ||
    evidence.repositories.length !== pins.size ||
    evidence.repositories.some(({ id, sha }) => pins.get(id) !== sha)
  ) {
    throw new BomError("bom_runtime_evidence_pin_mismatch");
  }
  if (evidence.combinationDigest !== combinationDigest(manifest, matrix)) {
    throw new BomError("bom_runtime_evidence_combination_mismatch");
  }
  return {
    combinationDigest: evidence.combinationDigest,
    combinationId: evidence.combinationId,
    evidenceDigest: framedDigest([Buffer.from(source, "utf8")]),
    outcome: "pass",
    treeMode: evidence.treeMode,
  };
}

function validateRuntimeGate(runtimeGate, { manifest, matrix }) {
  if (!exactKeys(runtimeGate, BOM_RUNTIME_GATE_KEYS)) {
    throw new BomError("bom_invalid", "runtimeGate fields");
  }
  if (
    runtimeGate.outcome !== "pass" ||
    runtimeGate.combinationId !== matrix.combinationId ||
    !DIGEST_PATTERN.test(runtimeGate.combinationDigest) ||
    !DIGEST_PATTERN.test(runtimeGate.evidenceDigest) ||
    !TREE_MODES.has(runtimeGate.treeMode)
  ) {
    throw new BomError("bom_invalid", "runtimeGate values");
  }
  if (runtimeGate.combinationDigest !== combinationDigest(manifest, matrix)) {
    throw new BomError("bom_runtime_evidence_combination_mismatch");
  }
}

export function validateBom(bom, context) {
  if (bom !== null && typeof bom === "object" && !Array.isArray(bom)) {
    for (const field of SELF_REFERENCE_FIELDS) {
      if (Object.hasOwn(bom, field)) throw new BomError("bom_self_reference_forbidden", field);
    }
  }
  if (!exactKeys(bom, BOM_KEYS)) throw new BomError("bom_invalid", "top-level fields");
  if (bom.schemaVersion !== SCHEMA_VERSION || bom.generatorVersion !== GENERATOR_VERSION) {
    throw new BomError("bom_invalid", "versions");
  }
  if (bom.repositoryTopology !== REPOSITORY_TOPOLOGY) {
    throw new BomError("bom_invalid", "repositoryTopology");
  }
  if (!SHA_PATTERN.test(bom.promotionCommit)) throw new BomError("bom_invalid", "promotionCommit");
  for (const field of DIGEST_FIELDS) {
    if (!DIGEST_PATTERN.test(bom[field])) throw new BomError("bom_invalid", field);
  }
  if (!Array.isArray(bom.repositories) || bom.repositories.length !== REPOSITORY_IDS.length) {
    throw new BomError("bom_invalid", "repositories");
  }
  const ids = bom.repositories.map(({ id }) => id);
  if (ids.some((id, index) => id !== REPOSITORY_IDS[index])) {
    throw new BomError("bom_invalid", "repository inventory");
  }
  for (const repository of bom.repositories) {
    if (!exactKeys(repository, BOM_REPOSITORY_KEYS)) {
      throw new BomError("bom_invalid", `${repository.id}: fields`);
    }
    if (
      repository.path !== repository.id ||
      typeof repository.origin !== "string" ||
      !repository.origin.startsWith("https://github.com/LordFoxFairy/") ||
      !SHA_PATTERN.test(repository.pin) ||
      typeof repository.recoverableRef !== "string" ||
      !repository.recoverableRef.startsWith("refs/tags/") ||
      !Array.isArray(repository.protocols) ||
      repository.protocols.length === 0
    ) {
      throw new BomError("bom_invalid", `${repository.id}: values`);
    }
    for (const protocol of repository.protocols) {
      if (
        !exactKeys(protocol, BOM_PROTOCOL_KEYS) ||
        typeof protocol.id !== "string" ||
        !Number.isInteger(protocol.version) ||
        !["provider", "consumer"].includes(protocol.role)
      ) {
        throw new BomError("bom_invalid", `${repository.id}: protocols`);
      }
    }
  }
  const recoverableRefs = bom.repositories.map(({ recoverableRef }) => recoverableRef);
  if (new Set(recoverableRefs).size !== recoverableRefs.length) {
    throw new BomError("bom_invalid", "recoverableRef must be independent per repository");
  }
  if (!Array.isArray(bom.contracts) || bom.contracts.length === 0) {
    throw new BomError("bom_invalid", "contracts");
  }
  for (const contract of bom.contracts) {
    const keysValid =
      exactKeys(contract, BOM_CONTRACT_KEYS) || exactKeys(contract, BOM_ATTESTED_CONTRACT_KEYS);
    const digestValid =
      !Object.hasOwn(contract, "artifactDigest") || DIGEST_PATTERN.test(contract.artifactDigest);
    if (
      !keysValid ||
      !digestValid ||
      typeof contract.id !== "string" ||
      !Number.isInteger(contract.version) ||
      !Array.isArray(contract.providers) ||
      contract.providers.length === 0 ||
      !Array.isArray(contract.consumers) ||
      contract.consumers.length === 0
    ) {
      throw new BomError("bom_invalid", "contract entry");
    }
  }
  if (!Array.isArray(bom.evidence) || bom.evidence.length === 0) {
    throw new BomError("bom_invalid", "evidence");
  }
  for (const entry of bom.evidence) {
    if (
      !exactKeys(entry, BOM_EVIDENCE_KEYS) ||
      typeof entry.path !== "string" ||
      entry.path === "" ||
      entry.path.startsWith("/") ||
      entry.path.split("/").includes("..") ||
      !DIGEST_PATTERN.test(entry.digest)
    ) {
      throw new BomError("bom_invalid", "evidence entry");
    }
  }
  validateRuntimeGate(bom.runtimeGate, context);
  return bom;
}

async function composeBom({ root, promotionCommit, runtimeGate, ...context }) {
  const evidence = [];
  const evidenceParts = [];
  for (const path of [...EVIDENCE_PATHS].sort()) {
    let bytes;
    try {
      bytes = await readFile(resolve(root, path));
    } catch (error) {
      const code = error.code === "ENOENT" ? "bom_evidence_missing" : "bom_evidence_unreadable";
      throw new BomError(code, path);
    }
    evidence.push({ digest: framedDigest([bytes]), path });
    evidenceParts.push(path, bytes);
  }
  const contracts = [...context.matrix.contracts]
    .sort((left, right) => left.id.localeCompare(right.id))
    .map(({ id, version, providers, consumers, artifactDigest }) => ({
      consumers: [...consumers].sort(),
      id,
      providers: [...providers].sort(),
      version,
      ...(artifactDigest === undefined ? {} : { artifactDigest }),
    }));
  const repositories = [...context.manifest.repositories]
    .sort((left, right) => left.id.localeCompare(right.id))
    .map(({ id, origin, path, pin, protocols, recoverableRef }) => ({
      id,
      origin,
      path,
      pin,
      protocols: [...protocols]
        .sort((left, right) => left.id.localeCompare(right.id))
        .map(({ id: protocolId, role, version }) => ({ id: protocolId, role, version })),
      recoverableRef,
    }));
  return {
    contracts,
    contractsDigest: framedDigest(contracts.map((contract) => canonicalJson(contract))),
    evidence,
    evidenceDigest: framedDigest(evidenceParts),
    generatorVersion: GENERATOR_VERSION,
    manifestDigest: framedDigest([Buffer.from(context.manifestSource, "utf8")]),
    matrixDigest: framedDigest([Buffer.from(context.matrixSource, "utf8")]),
    promotionCommit,
    repositories,
    repositoryTopology: context.manifest.repositoryTopology,
    runtimeGate,
    schemaVersion: SCHEMA_VERSION,
  };
}

export function serializeBom(bom) {
  return `${JSON.stringify(canonical(bom), null, 2)}\n`;
}

export async function runBom(options) {
  const context = await readSources(options.root);
  const bomPath = resolve(options.root, BOM_PATH);
  let recorded = null;
  let recordedSource = null;
  if (options.check) {
    try {
      recordedSource = await readFile(bomPath, "utf8");
    } catch (error) {
      throw new BomError(error.code === "ENOENT" ? "bom_missing" : "bom_unreadable", error.message);
    }
    try {
      recorded = JSON.parse(recordedSource);
    } catch (error) {
      throw new BomError("bom_invalid", error.message);
    }
    validateBom(recorded, context);
  } else if (options.runtimeEvidence === null) {
    throw new BomError("bom_arguments_invalid", "--runtime-evidence is required to generate a BOM");
  }
  const promotionCommit = resolvePromotionCommit(
    options.root,
    options.promotionCommit ?? recorded?.promotionCommit ?? null,
  );
  assertPromotedPins(options.root, promotionCommit, context.manifest);
  const runtimeGate = options.runtimeEvidence === null
    ? recorded.runtimeGate
    : await readRuntimeGate(options.runtimeEvidence, context);
  const serialized = serializeBom(
    await composeBom({ root: options.root, promotionCommit, runtimeGate, ...context }),
  );
  validateBom(JSON.parse(serialized), context);
  if (options.check) {
    if (serialized !== recordedSource) throw new BomError("bom_drift", BOM_PATH);
    return `repository_bom_verified: ${BOM_PATH} promotionCommit=${promotionCommit}`;
  }
  await writeFile(bomPath, serialized, "utf8");
  return `repository_bom_written: ${BOM_PATH} promotionCommit=${promotionCommit}`;
}

if (process.argv[1] && pathToFileURL(process.argv[1]).href === import.meta.url) {
  try {
    process.stdout.write(`${await runBom(parseArguments(process.argv.slice(2)))}\n`);
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    process.stderr.write(`${message}\n`);
    process.exitCode = 1;
  }
}
