#!/usr/bin/env node

import { spawnSync } from "node:child_process";
import { createHash, randomBytes } from "node:crypto";
import { constants, lstatSync, realpathSync } from "node:fs";
import { lstat, mkdir, open, readFile, realpath, rename, rm } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { checkGeneratedContracts } from "../repository/check-generated-contracts.mjs";
import { framedDigest, runBom } from "../repository/generate-bom.mjs";

const SCRIPT_PATH = fileURLToPath(import.meta.url);
const SPECIFICATION_PATH =
  "docs/superpowers/specs/2026-07-28-wave-1-platform-identity-site-policy-design.md";
const SPECIFICATION_DIRECTORY = "docs/superpowers/specs";
const PARENT_SPECIFICATION_FILE =
  "2026-07-25-platform-web-session-target-architecture-design.md";
const PARENT_SPECIFICATION_VERSION = "1.5";
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
const SNAPSHOT_KEYS = [
  "decisions", "ga", "repository", "schemaVersion", "specification", "wave",
];
const SPECIFICATION_KEYS = [
  "gaRuntimeSemanticChangeAuthorized", "implementationAuthorized", "parent", "status",
];
const PARENT_KEYS = ["actualVersion", "declaredFile", "declaredVersion", "exists"];
const DECISION_KEYS = ["adr005", "adr012", "expectedAdr012Digest"];
const ADR012_KEYS = ["adopted", "digest"];
const ADR005_KEYS = ["reverseLink", "supersededBy"];
const REPOSITORY_KEYS = [
  "bomManifestDigest", "contractsDigest", "evidenceDigest", "evidenceVerified",
  "generatedContractsVerified", "manifestDigest", "repositories", "rootStatus",
];
const REPOSITORY_ITEM_KEYS = ["actualSha", "expectedSha", "id", "status"];
const GA_KEYS = [
  "actualSha", "controlAdapterSha256", "controlSpecSha256",
  "expectedControlAdapterSha256", "expectedControlSpecSha256", "expectedSha", "status",
];

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

function exactKeys(value, keys) {
  if (value === null || typeof value !== "object" || Array.isArray(value)) return false;
  const actual = Object.keys(value).sort();
  const expected = [...keys].sort();
  return actual.length === expected.length && actual.every((key, index) => key === expected[index]);
}

function assertClosedSnapshotShape(snapshot) {
  if (
    !exactKeys(snapshot, SNAPSHOT_KEYS) ||
    !exactKeys(snapshot.specification, SPECIFICATION_KEYS) ||
    !exactKeys(snapshot.specification.parent, PARENT_KEYS) ||
    !exactKeys(snapshot.decisions, DECISION_KEYS) ||
    !exactKeys(snapshot.decisions.adr012, ADR012_KEYS) ||
    !exactKeys(snapshot.decisions.adr005, ADR005_KEYS) ||
    !exactKeys(snapshot.repository, REPOSITORY_KEYS) ||
    !exactKeys(snapshot.ga, GA_KEYS) ||
    !Array.isArray(snapshot.repository.repositories) ||
    snapshot.repository.repositories.length !== EXPECTED_REPOSITORIES.length ||
    snapshot.repository.repositories.some(
      (repository) => !exactKeys(repository, REPOSITORY_ITEM_KEYS),
    )
  ) {
    fail("wave1_snapshot_invalid");
  }
  const ids = snapshot.repository.repositories.map(({ id }) => id);
  if (
    new Set(ids).size !== EXPECTED_REPOSITORIES.length ||
    EXPECTED_REPOSITORIES.some((id) => !ids.includes(id))
  ) {
    fail("wave1_snapshot_invalid");
  }
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
    const baseline = JSON.parse(source);
    assertPreflightSnapshot(baseline);
    return baseline;
  } catch (error) {
    if (error.code === "ENOENT") return null;
    fail("wave1_baseline_invalid", error.message);
  }
}

function rootGitlinkSha(root, path, id) {
  const source = git(root, ["ls-tree", "HEAD", "--", path]).trim();
  const match = /^160000 commit ([0-9a-f]{40})\t([^\n]+)$/u.exec(source);
  if (!match || match[2] !== path) fail("wave1_child_pin_mismatch", id);
  return match[1];
}

function assertNoSymlinkPath(base, target) {
  let current = target;
  while (true) {
    let status;
    try {
      status = lstatSync(current);
    } catch (error) {
      if (error.code !== "ENOENT") fail("wave1_arguments_invalid", "--write-baseline");
    }
    if (status?.isSymbolicLink()) {
      fail("wave1_arguments_invalid", "--write-baseline");
    }
    if (current === base) return;
    const parent = dirname(current);
    if (parent === current) fail("wave1_arguments_invalid", "--write-baseline");
    current = parent;
  }
}

function identity(status) {
  return { dev: status.dev, ino: status.ino };
}

function sameIdentity(left, right) {
  return left.dev === right.dev && left.ino === right.ino;
}

async function checkedDirectoryIdentity(path, expectedPath, expectedIdentity = null) {
  let status;
  let actualPath;
  try {
    status = await lstat(path);
    if (status.isSymbolicLink() || !status.isDirectory()) fail("wave1_baseline_path_changed");
    actualPath = await realpath(path);
  } catch (error) {
    if (error instanceof PreflightError) throw error;
    fail("wave1_baseline_path_changed");
  }
  const actualIdentity = identity(status);
  if (
    actualPath !== expectedPath ||
    (expectedIdentity && !sameIdentity(actualIdentity, expectedIdentity))
  ) {
    fail("wave1_baseline_path_changed");
  }
  return actualIdentity;
}

async function prepareBaselineDirectory(target) {
  await checkedDirectoryIdentity(
    target.gitDirectory,
    target.gitDirectory,
    target.gitDirectoryIdentity,
  );
  if (target.directoryIdentity === null) {
    try {
      await mkdir(target.directory, { mode: 0o700 });
    } catch {
      fail("wave1_baseline_path_changed");
    }
  }
  return checkedDirectoryIdentity(
    target.directory,
    target.directory,
    target.directoryIdentity,
  );
}

async function syncDirectory(path) {
  let handle;
  try {
    handle = await open(path, constants.O_RDONLY | (constants.O_DIRECTORY ?? 0));
    await handle.sync();
  } catch (error) {
    const unsupported = ["EINVAL", "ENOTSUP", "EOPNOTSUPP", "EBADF"].includes(error.code) ||
      (process.platform === "win32" && ["EISDIR", "EPERM"].includes(error.code));
    if (!unsupported) throw error;
  } finally {
    await handle?.close();
  }
}

async function cleanupOwnedTemporary(target, temporary) {
  try {
    await checkedDirectoryIdentity(
      target.gitDirectory,
      target.gitDirectory,
      target.gitDirectoryIdentity,
    );
    await rm(temporary, { force: true });
  } catch {
    // A changed directory identity is untrusted; never follow it for cleanup.
  }
}

export function assertPreflightSnapshot(snapshot) {
  assertClosedSnapshotShape(snapshot);
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
    snapshot.specification.parent.declaredFile !== PARENT_SPECIFICATION_FILE ||
    snapshot.specification.parent.declaredVersion !== PARENT_SPECIFICATION_VERSION ||
    snapshot.specification.parent.actualVersion !== PARENT_SPECIFICATION_VERSION
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

export async function writeBaselineAtomic(target, snapshot, hooks = {}) {
  assertPreflightSnapshot(snapshot);
  if (
    !exactKeys(
      target,
      ["baselinePath", "directory", "directoryIdentity", "gitDirectory", "gitDirectoryIdentity"],
    )
  ) {
    fail("wave1_baseline_path_changed");
  }
  const directoryIdentity = await prepareBaselineDirectory(target);
  const temporary = resolve(
    target.gitDirectory,
    `.wave1-baseline.${process.pid}.${randomBytes(8).toString("hex")}.tmp`,
  );
  let handle = null;
  try {
    await hooks.beforeTemporaryOpen?.();
    await checkedDirectoryIdentity(
      target.gitDirectory,
      target.gitDirectory,
      target.gitDirectoryIdentity,
    );
    await checkedDirectoryIdentity(target.directory, target.directory, directoryIdentity);
    handle = await open(
      temporary,
      constants.O_WRONLY | constants.O_CREAT | constants.O_EXCL | (constants.O_NOFOLLOW ?? 0),
      0o600,
    );
    await handle.writeFile(`${JSON.stringify(snapshot, null, 2)}\n`, "utf8");
    await handle.sync();
    await handle.close();
    handle = null;
    await hooks.beforeRename?.();
    await checkedDirectoryIdentity(
      target.gitDirectory,
      target.gitDirectory,
      target.gitDirectoryIdentity,
    );
    await checkedDirectoryIdentity(target.directory, target.directory, directoryIdentity);
    await rename(temporary, target.baselinePath);
    await checkedDirectoryIdentity(target.directory, target.directory, directoryIdentity);
    await syncDirectory(target.directory);
  } finally {
    await handle?.close();
    await cleanupOwnedTemporary(target, temporary);
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
  if (
    declaredFile !== PARENT_SPECIFICATION_FILE ||
    declaredVersion !== PARENT_SPECIFICATION_VERSION
  ) {
    fail("wave1_parent_mismatch");
  }
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
    const actualSha = git(childRoot, ["rev-parse", "HEAD"]).trim();
    const bomSha = bom.repositories?.find((candidate) => candidate.id === repository.id)?.pin;
    const gitlinkSha = rootGitlinkSha(root, repository.path, repository.id);
    const previousRepository = baseline?.repository?.repositories?.find(
      (candidate) => candidate.id === repository.id,
    );
    const authoritativeShas = [repository.pin, bomSha, gitlinkSha, actualSha];
    if (baseline !== null) {
      authoritativeShas.push(
        previousRepository?.expectedSha,
        previousRepository?.actualSha,
      );
    }
    if (
      authoritativeShas.some(
        (candidate) => !isSha(candidate) || candidate !== repository.pin,
      )
    ) {
      fail("wave1_child_pin_mismatch", repository.id);
    }
    return {
      id: repository.id,
      expectedSha: repository.pin,
      actualSha,
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
      expectedSha: agent?.expectedSha ?? null,
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
  let rootSeen = false;
  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    const value = argv[index + 1];
    if (!value) fail("wave1_arguments_invalid", argument);
    index += 1;
    if (argument === "--root" && !rootSeen) {
      root = resolve(value);
      rootSeen = true;
    } else if (argument === "--write-baseline" && baselineArgument === null) {
      baselineArgument = value;
    } else fail("wave1_arguments_invalid", argument);
  }
  if (baselineArgument === null) {
    fail("wave1_arguments_invalid", "--write-baseline is required");
  }
  const rawGitDirectory = git(root, ["rev-parse", "--absolute-git-dir"]).trim();
  const rawGitStatus = lstatSync(rawGitDirectory);
  if (rawGitStatus.isSymbolicLink() || !rawGitStatus.isDirectory()) {
    fail("wave1_arguments_invalid", "--write-baseline");
  }
  const gitDirectory = realpathSync(rawGitDirectory);
  const baselinePath = resolve(gitDirectory, "kokoro-wave1/baseline.json");
  const directory = dirname(baselinePath);
  const parsedPath = baselineArgument === ".git/kokoro-wave1/baseline.json"
    ? baselinePath
    : resolve(root, baselineArgument);
  if (parsedPath !== baselinePath) {
    fail("wave1_arguments_invalid", "--write-baseline");
  }
  assertNoSymlinkPath(resolve(gitDirectory), baselinePath);
  let directoryIdentity = null;
  try {
    const directoryStatus = lstatSync(directory);
    if (directoryStatus.isSymbolicLink() || !directoryStatus.isDirectory()) {
      fail("wave1_arguments_invalid", "--write-baseline");
    }
    if (realpathSync(directory) !== directory) {
      fail("wave1_arguments_invalid", "--write-baseline");
    }
    directoryIdentity = identity(directoryStatus);
  } catch (error) {
    if (error instanceof PreflightError) throw error;
    if (error.code !== "ENOENT") fail("wave1_arguments_invalid", "--write-baseline");
  }
  const baselineTarget = {
    baselinePath,
    directory,
    directoryIdentity,
    gitDirectory,
    gitDirectoryIdentity: identity(lstatSync(gitDirectory)),
  };
  return { baselinePath, baselineTarget, root };
}

async function main() {
  try {
    const { baselinePath, baselineTarget, root } = parseArguments(process.argv.slice(2));
    const previous = await readOptionalBaseline(baselinePath);
    const snapshot = await collectPreflightSnapshot(root, previous);
    await writeBaselineAtomic(baselineTarget, snapshot);
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
