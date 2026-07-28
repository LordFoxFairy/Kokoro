#!/usr/bin/env node

import { spawnSync } from "node:child_process";
import { createHash, randomBytes } from "node:crypto";
import { mkdir, readFile, rename, rm, writeFile } from "node:fs/promises";
import { dirname, isAbsolute, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { checkGeneratedContracts } from "../repository/check-generated-contracts.mjs";
import { framedDigest, runBom } from "../repository/generate-bom.mjs";

const SCRIPT_PATH = fileURLToPath(import.meta.url);
const SPECIFICATION_PATH =
  "docs/superpowers/specs/2026-07-28-wave-1-platform-identity-site-policy-design.md";
const SPECIFICATION_DIRECTORY = "docs/superpowers/specs";
const ADR012_PATH =
  "docs/kokoro-handbook/decisions/ADR-012-postgresql-platform-session-boundary.md";
const ADR005_PATH = "docs/kokoro-handbook/decisions/ADR-005-mysql-and-mongo.md";
const MANIFEST_PATH = "config/repository/federated-repositories.json";
const BOM_PATH = "config/repository/bom.json";
const CONTROL_SPEC_PATH = "contract/spec/control.yaml";
const CONTROL_ADAPTER_PATH = "kokoro-agent/src/kokoro_agent/contract/control.py";
const EXPECTED_REPOSITORIES = [
  "kokoro-agent",
  "kokoro-platform",
  "kokoro-session",
  "kokoro-web",
];
const SHA_PATTERN = /^[0-9a-f]{40}$/u;
const DIGEST_PATTERN = /^[0-9a-f]{64}$/u;

export class PreflightError extends Error {
  constructor(code, detail = "") {
    super(`${code}${detail ? `: ${detail}` : ""}`);
    this.name = "PreflightError";
    this.code = code;
  }
}

function fail(code, detail = "") {
  throw new PreflightError(code, detail);
}

function isDigest(value) {
  return typeof value === "string" && DIGEST_PATTERN.test(value);
}

function isSha(value) {
  return typeof value === "string" && SHA_PATTERN.test(value);
}

function sha256(bytes) {
  return createHash("sha256").update(bytes).digest("hex");
}

function git(root, arguments_) {
  const result = spawnSync("git", arguments_, {
    cwd: root,
    encoding: "utf8",
    maxBuffer: 16 * 1024 * 1024,
    shell: false,
  });
  if (result.error) fail("wave1_git_failed", result.error.message);
  if (result.status !== 0) {
    fail("wave1_git_failed", `${arguments_.join(" ")}: ${result.stderr.trim()}`);
  }
  return result.stdout;
}

function requiredMatch(source, pattern, code) {
  const match = pattern.exec(source);
  if (!match) fail(code);
  return match[1];
}

function parseBooleanMetadata(source, name) {
  return requiredMatch(
    source,
    new RegExp(String.raw`^>\s*${name}:\s*\x60(true|false)\x60\s*$`, "mu"),
    `wave1_${name.replaceAll(/([A-Z])/gu, "_$1").toLowerCase()}_missing`,
  ) === "true";
}

async function readJson(root, path, code) {
  let source;
  try {
    source = await readFile(resolve(root, path), "utf8");
  } catch (error) {
    fail(code, error.code ?? error.message);
  }
  try {
    return { source, value: JSON.parse(source) };
  } catch (error) {
    fail(code, error.message);
  }
}

async function readOptionalBaseline(path) {
  try {
    const source = await readFile(path, "utf8");
    return JSON.parse(source);
  } catch (error) {
    if (error.code === "ENOENT") return null;
    fail("wave1_baseline_invalid", error.message);
  }
}

function baselineRepositorySha(baseline, id, fallback) {
  const repository = baseline?.repository?.repositories?.find((candidate) => candidate.id === id);
  return repository?.actualSha ?? fallback;
}

export function assertPreflightSnapshot(snapshot) {
  if (snapshot?.schemaVersion !== 1 || snapshot.wave !== "wave-1-platform-identity-site-policy") {
    fail("wave1_snapshot_invalid");
  }
  if (snapshot.specification?.status !== "internally-approved") fail("wave1_spec_unapproved");
  if (snapshot.specification.implementationAuthorized !== true) {
    fail("wave1_implementation_unauthorized");
  }
  if (snapshot.specification.gaRuntimeSemanticChangeAuthorized !== false) {
    fail("wave1_ga_semantic_change_authorized");
  }
  if (snapshot.specification.parent?.exists !== true) fail("wave1_parent_missing");
  if (
    snapshot.specification.parent.declaredVersion !==
      snapshot.specification.parent.actualVersion
  ) {
    fail("wave1_parent_mismatch");
  }
  if (snapshot.decisions?.adr012?.adopted !== true) fail("wave1_adr012_not_adopted");
  if (
    !isDigest(snapshot.decisions.adr012.digest) ||
    snapshot.decisions.adr012.digest !== snapshot.decisions.expectedAdr012Digest
  ) {
    fail("wave1_adr012_digest_mismatch");
  }
  if (snapshot.decisions.adr005?.supersededBy !== "ADR-012") {
    fail("wave1_adr005_not_superseded");
  }
  if (snapshot.decisions.adr005.reverseLink !== true) {
    fail("wave1_adr005_reverse_link_missing");
  }

  if (snapshot.repository?.rootStatus !== "") fail("wave1_root_dirty");
  if (!isDigest(snapshot.repository.manifestDigest)) fail("wave1_manifest_digest_missing");
  if (snapshot.repository.manifestDigest !== snapshot.repository.bomManifestDigest) {
    fail("wave1_manifest_digest_mismatch");
  }
  if (!isDigest(snapshot.repository.contractsDigest)) fail("wave1_contract_digest_missing");
  if (!isDigest(snapshot.repository.evidenceDigest)) fail("wave1_evidence_digest_missing");
  if (snapshot.repository.evidenceVerified !== true) fail("wave1_evidence_invalid");
  if (snapshot.repository.generatedContractsVerified !== true) {
    fail("wave1_generated_contracts_invalid");
  }
  if (
    !Array.isArray(snapshot.repository.repositories) ||
    snapshot.repository.repositories.length !== EXPECTED_REPOSITORIES.length
  ) {
    fail("wave1_repository_set_invalid");
  }
  for (const id of EXPECTED_REPOSITORIES) {
    const repository = snapshot.repository.repositories.find((candidate) => candidate.id === id);
    if (!repository) fail("wave1_repository_set_invalid", id);
    if (repository.status !== "") fail("wave1_child_dirty", id);
    if (
      !isSha(repository.expectedSha) ||
      !isSha(repository.actualSha) ||
      repository.expectedSha !== repository.actualSha
    ) {
      fail("wave1_child_pin_mismatch", id);
    }
  }

  if (snapshot.ga?.status !== "") fail("wave1_ga_dirty");
  if (
    !isSha(snapshot.ga.expectedSha) ||
    !isSha(snapshot.ga.actualSha) ||
    snapshot.ga.expectedSha !== snapshot.ga.actualSha
  ) {
    fail("wave1_ga_sha_mismatch");
  }
  if (!isDigest(snapshot.ga.controlSpecSha256)) fail("wave1_ga_control_digest_missing");
  if (!isDigest(snapshot.ga.controlAdapterSha256)) fail("wave1_ga_adapter_digest_missing");
  if (snapshot.ga.controlSpecSha256 !== snapshot.ga.expectedControlSpecSha256) {
    fail("wave1_ga_control_digest_mismatch");
  }
  if (snapshot.ga.controlAdapterSha256 !== snapshot.ga.expectedControlAdapterSha256) {
    fail("wave1_ga_adapter_digest_mismatch");
  }
}

export async function writeBaselineAtomic(path, snapshot) {
  assertPreflightSnapshot(snapshot);
  const directory = dirname(path);
  await mkdir(directory, { recursive: true });
  const temporary = resolve(
    directory,
    `.baseline.${process.pid}.${randomBytes(8).toString("hex")}.tmp`,
  );
  try {
    await writeFile(temporary, `${JSON.stringify(snapshot, null, 2)}\n`, {
      encoding: "utf8",
      flag: "wx",
      mode: 0o600,
    });
    await rename(temporary, path);
  } finally {
    await rm(temporary, { force: true });
  }
}

export async function collectPreflightSnapshot(root, baseline = null) {
  let bomVerified = true;
  try {
    await runBom({ root, check: true, promotionCommit: null, runtimeEvidence: null });
  } catch {
    bomVerified = false;
  }
  const [specificationSource, adr012Source, adr005Source] = await Promise.all([
    readFile(resolve(root, SPECIFICATION_PATH), "utf8"),
    readFile(resolve(root, ADR012_PATH), "utf8"),
    readFile(resolve(root, ADR005_PATH), "utf8"),
  ]);
  const status = requiredMatch(
    specificationSource,
    /^>\s*状态：`([^`]+)`/mu,
    "wave1_spec_status_missing",
  ).split("；", 1)[0];
  const rawParent = /^>\s*父设计：`([^`]+\.md)`\s+v([0-9.]+)\s*$/mu.exec(
    specificationSource,
  );
  if (!rawParent) fail("wave1_parent_declaration_missing");
  const declaredFile = rawParent[1];
  const declaredVersion = rawParent[2];
  const parentPath = resolve(root, SPECIFICATION_DIRECTORY, declaredFile);
  let parentSource = null;
  try {
    parentSource = await readFile(parentPath, "utf8");
  } catch (error) {
    if (error.code !== "ENOENT") throw error;
  }
  const actualVersion = parentSource
    ? /^version:\s*["']?([^\s"']+)["']?\s*$/mu.exec(parentSource)?.[1] ?? null
    : null;
  const [{ source: manifestSource, value: manifest }, { value: bom }] = await Promise.all([
    readJson(root, MANIFEST_PATH, "wave1_manifest_invalid"),
    readJson(root, BOM_PATH, "wave1_bom_invalid"),
  ]);
  if (!Array.isArray(manifest.repositories)) fail("wave1_manifest_invalid");

  let generatedContractsVerified = true;
  try {
    await checkGeneratedContracts({ root });
  } catch {
    generatedContractsVerified = false;
  }

  const repositories = manifest.repositories.map((repository) => {
    if (!EXPECTED_REPOSITORIES.includes(repository.id) || typeof repository.path !== "string") {
      fail("wave1_manifest_repository_invalid", repository.id ?? "unknown");
    }
    const childRoot = resolve(root, repository.path);
    return {
      id: repository.id,
      expectedSha: baselineRepositorySha(baseline, repository.id, repository.pin),
      actualSha: git(childRoot, ["rev-parse", "HEAD"]).trim(),
      status: git(childRoot, ["status", "--porcelain=v1", "--untracked-files=all"]),
    };
  });

  const adr012Digest = sha256(Buffer.from(adr012Source, "utf8"));
  const controlSpecSha256 = sha256(await readFile(resolve(root, CONTROL_SPEC_PATH)));
  const controlAdapterSha256 = sha256(await readFile(resolve(root, CONTROL_ADAPTER_PATH)));
  const agent = repositories.find((repository) => repository.id === "kokoro-agent");

  return {
    schemaVersion: 1,
    wave: "wave-1-platform-identity-site-policy",
    specification: {
      status,
      implementationAuthorized: parseBooleanMetadata(
        specificationSource,
        "implementationAuthorized",
      ),
      gaRuntimeSemanticChangeAuthorized: parseBooleanMetadata(
        specificationSource,
        "gaRuntimeSemanticChangeAuthorized",
      ),
      parent: {
        declaredFile,
        declaredVersion,
        actualVersion,
        exists: parentSource !== null,
      },
    },
    decisions: {
      adr012: {
        adopted: /^状态：已采纳（[^）]+）。\s*$/mu.test(adr012Source),
        digest: adr012Digest,
      },
      adr005: {
        supersededBy: /^状态：已被 \[ADR-012\]/mu.test(adr005Source) ? "ADR-012" : null,
        reverseLink: /^取代：\[ADR-005[^\]]*\]\(ADR-005-mysql-and-mongo\.md\)。\s*$/mu.test(
          adr012Source,
        ),
      },
      expectedAdr012Digest: baseline?.decisions?.adr012?.digest ?? adr012Digest,
    },
    repository: {
      rootStatus: git(root, ["status", "--porcelain=v1", "--untracked-files=all"]),
      manifestDigest: framedDigest([Buffer.from(manifestSource, "utf8")]),
      bomManifestDigest: bom.manifestDigest ?? null,
      contractsDigest: bom.contractsDigest ?? null,
      evidenceDigest: bom.evidenceDigest ?? null,
      evidenceVerified: bomVerified,
      generatedContractsVerified,
      repositories,
    },
    ga: {
      expectedSha: baseline?.ga?.actualSha ?? agent?.expectedSha ?? null,
      actualSha: agent?.actualSha ?? null,
      status: agent?.status ?? null,
      expectedControlSpecSha256:
        baseline?.ga?.controlSpecSha256 ?? controlSpecSha256,
      controlSpecSha256,
      expectedControlAdapterSha256:
        baseline?.ga?.controlAdapterSha256 ?? controlAdapterSha256,
      controlAdapterSha256,
    },
  };
}

export function parseArguments(argv) {
  let root = process.cwd();
  let baselineArgument = null;
  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    const value = argv[index + 1];
    if (!value) fail("wave1_arguments_invalid", argument);
    index += 1;
    if (argument === "--root") root = resolve(value);
    else if (argument === "--write-baseline") baselineArgument = value;
    else fail("wave1_arguments_invalid", argument);
  }
  if (baselineArgument === null) {
    fail("wave1_arguments_invalid", "--write-baseline is required");
  }
  let baselinePath;
  if (baselineArgument.startsWith(".git/")) {
    const gitPath = git(root, ["rev-parse", "--git-path", baselineArgument.slice(5)]).trim();
    baselinePath = isAbsolute(gitPath) ? gitPath : resolve(root, gitPath);
  } else {
    baselinePath = isAbsolute(baselineArgument)
      ? baselineArgument
      : resolve(root, baselineArgument);
  }
  return { baselinePath, root };
}

async function main() {
  try {
    const { baselinePath, root } = parseArguments(process.argv.slice(2));
    const previous = await readOptionalBaseline(baselinePath);
    const snapshot = await collectPreflightSnapshot(root, previous);
    await writeBaselineAtomic(baselinePath, snapshot);
    process.stdout.write(`wave1_preflight_ok: ${baselinePath}\n`);
  } catch (error) {
    if (error instanceof PreflightError) {
      process.stderr.write(`${error.message}\n`);
    } else {
      process.stderr.write(`wave1_preflight_failed: ${error.message ?? "unknown error"}\n`);
    }
    process.exitCode = 1;
  }
}

if (process.argv[1] && resolve(process.argv[1]) === resolve(SCRIPT_PATH)) {
  await main();
}
