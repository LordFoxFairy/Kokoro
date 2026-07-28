import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdir, mkdtemp, readFile, rename, rm, stat, symlink, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import test from "node:test";

import { combinationDigest, framedDigest } from "../repository/generate-bom.mjs";
import {
  PreflightError,
  assertPreflightSnapshot,
  parseArguments,
  writeBaselineAtomic,
} from "./preflight.mjs";

const SHA = "1".repeat(40);
const OTHER_SHA = "2".repeat(40);
const DIGEST = "a".repeat(64);
const OTHER_DIGEST = "b".repeat(64);
const supportsPosixDirFd = process.platform !== "win32";
const repositoryRoot = resolve(import.meta.dirname, "../..");
const preflightScript = resolve(repositoryRoot, "scripts/wave1/preflight.mjs");

function run(command, arguments_, cwd) {
  const result = spawnSync(command, arguments_, {
    cwd,
    encoding: "utf8",
    shell: false,
  });
  assert.equal(
    result.status,
    0,
    `${command} ${arguments_.join(" ")} failed\nstdout: ${result.stdout}\nstderr: ${result.stderr}`,
  );
  return result.stdout.trim();
}

function canonical(value) {
  if (Array.isArray(value)) return value.map(canonical);
  if (value !== null && typeof value === "object") {
    return Object.fromEntries(
      Object.keys(value)
        .sort()
        .map((key) => [key, canonical(value[key])]),
    );
  }
  return value;
}

function canonicalJson(value) {
  return JSON.stringify(canonical(value));
}

async function writeFixtureFile(root, path, source) {
  const target = resolve(root, path);
  await mkdir(resolve(target, ".."), { recursive: true });
  await writeFile(target, source, "utf8");
}

function configureRepository(root) {
  run("git", ["init", "--quiet"], root);
  run("git", ["config", "user.name", "Kokoro Test"], root);
  run("git", ["config", "user.email", "kokoro-test@example.invalid"], root);
}

async function createChildRepository(root, id) {
  const child = resolve(root, id);
  await mkdir(child, { recursive: true });
  configureRepository(child);
  await writeFixtureFile(child, "README.md", `${id}\n`);
  if (id === "kokoro-agent") {
    await writeFixtureFile(
      child,
      "src/kokoro_agent/contract/control.py",
      "CONTROL_VERSION = 1\n",
    );
  }
  if (id === "kokoro-platform") {
    await writeFixtureFile(
      child,
      "kokoro-platform-admin/src/generated/contracts/fixture.txt",
      "generated\n",
    );
  }
  if (id === "kokoro-web") {
    await writeFixtureFile(
      child,
      "apps/admin/lib/generated/contracts/fixture.txt",
      "generated\n",
    );
  }
  run("git", ["add", "--all"], child);
  run("git", ["commit", "--quiet", "-m", "fixture"], child);
  return run("git", ["rev-parse", "HEAD"], child);
}

async function createBomFixture({ emptyEvidence }) {
  const root = await mkdtemp(join(tmpdir(), "kokoro-wave1-preflight-fixture-"));
  const evidenceSources = [
    {
      path: "docs/reports/evidence/wave-0/federated-repository-baseline.md",
      source: "# fixture repository evidence\n",
    },
    {
      path: "docs/reports/evidence/wave-0/ownership-attestation.yaml",
      source: "schemaVersion: 1\n",
    },
  ];
  configureRepository(root);

  const manifest = JSON.parse(
    await readFile(resolve(repositoryRoot, "config/repository/federated-repositories.json"), "utf8"),
  );
  const matrixSource = await readFile(
    resolve(repositoryRoot, "config/repository/compatibility-matrix.json"),
    "utf8",
  );
  const matrix = JSON.parse(matrixSource);
  for (const repository of manifest.repositories) {
    repository.pin = await createChildRepository(root, repository.id);
  }
  const manifestSource = `${JSON.stringify(manifest, null, 2)}\n`;

  await Promise.all([
    writeFixtureFile(
      root,
      "docs/superpowers/specs/2026-07-28-wave-1-platform-identity-site-policy-design.md",
      [
        "# fixture",
        "> 状态：`internally-approved`；fixture",
        "> implementationAuthorized: `true`",
        "> gaRuntimeSemanticChangeAuthorized: `false`",
        "> 父设计：`2026-07-25-platform-web-session-target-architecture-design.md` v1.5",
        "",
      ].join("\n"),
    ),
    writeFixtureFile(
      root,
      "docs/superpowers/specs/2026-07-25-platform-web-session-target-architecture-design.md",
      'version: "1.5"\n',
    ),
    writeFixtureFile(
      root,
      "docs/kokoro-handbook/decisions/ADR-012-postgresql-platform-session-boundary.md",
      [
        "# ADR-012",
        "状态：已采纳（2026-07-28）。",
        "取代：[ADR-005 fixture](ADR-005-mysql-and-mongo.md)。",
        "",
      ].join("\n"),
    ),
    writeFixtureFile(
      root,
      "docs/kokoro-handbook/decisions/ADR-005-mysql-and-mongo.md",
      "# ADR-005\n状态：已被 [ADR-012](ADR-012-postgresql-platform-session-boundary.md) 取代。\n",
    ),
    writeFixtureFile(root, "config/repository/federated-repositories.json", manifestSource),
    writeFixtureFile(root, "config/repository/compatibility-matrix.json", matrixSource),
    writeFixtureFile(root, "config/repository/bom.json", "{}\n"),
    writeFixtureFile(root, ".gitignore", "contract/node_modules/\ncontract/pnpm-lock.yaml\n"),
    writeFixtureFile(root, "contract/spec/control.yaml", "version: 1\n"),
    writeFixtureFile(
      root,
      "contract/package.json",
      `${JSON.stringify({ private: true, scripts: { "buf:generate": "node generate.mjs" } }, null, 2)}\n`,
    ),
    writeFixtureFile(
      root,
      "contract/generate.mjs",
      [
        'import { mkdir, writeFile } from "node:fs/promises";',
        'import { resolve } from "node:path";',
        "const output = process.argv.at(-1);",
        "await mkdir(output, { recursive: true });",
        'await writeFile(resolve(output, "fixture.txt"), "generated\\n", "utf8");',
        "",
      ].join("\n"),
    ),
    writeFixtureFile(
      root,
      "kokoro-platform/kokoro-platform-admin/src/generated/contracts/fixture.txt",
      "generated\n",
    ),
    writeFixtureFile(
      root,
      "kokoro-web/apps/admin/lib/generated/contracts/fixture.txt",
      "generated\n",
    ),
  ]);
  if (!emptyEvidence) {
    await Promise.all(
      evidenceSources.map(({ path, source }) => writeFixtureFile(root, path, source)),
    );
  }

  run("git", ["add", "--all"], root);
  run("git", ["commit", "--quiet", "-m", "promote fixture pins"], root);
  const promotionCommit = run("git", ["rev-parse", "HEAD"], root);
  const contracts = [...matrix.contracts]
    .sort((left, right) => left.id.localeCompare(right.id))
    .map(({ id, version, providers, consumers, artifactDigest }) => ({
      consumers: [...consumers].sort(),
      id,
      providers: [...providers].sort(),
      version,
      ...(artifactDigest === undefined ? {} : { artifactDigest }),
    }));
  const repositories = [...manifest.repositories]
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
  const evidence = emptyEvidence
    ? []
    : evidenceSources.map(({ path, source }) => ({
        digest: framedDigest([Buffer.from(source, "utf8")]),
        path,
      }));
  const evidenceParts = emptyEvidence
    ? []
    : evidenceSources.flatMap(({ path, source }) => [path, Buffer.from(source, "utf8")]);
  const bom = {
    contracts,
    contractsDigest: framedDigest(contracts.map((contract) => canonicalJson(contract))),
    evidence,
    evidenceDigest: framedDigest(evidenceParts),
    generatorVersion: 1,
    manifestDigest: framedDigest([Buffer.from(manifestSource, "utf8")]),
    matrixDigest: framedDigest([Buffer.from(matrixSource, "utf8")]),
    promotionCommit,
    repositories,
    repositoryTopology: "federated-submodules-v1",
    runtimeGate: {
      combinationDigest: combinationDigest(manifest, matrix),
      combinationId: matrix.combinationId,
      evidenceDigest: DIGEST,
      outcome: "pass",
      treeMode: "head",
    },
    schemaVersion: 1,
  };
  await writeFixtureFile(root, "config/repository/bom.json", `${JSON.stringify(canonical(bom), null, 2)}\n`);
  run("git", ["add", "config/repository/bom.json"], root);
  run("git", ["commit", "--quiet", "-m", "record fixture BOM"], root);
  return root;
}

async function advanceManifestAndBomButRestoreCheckout(root, id) {
  const manifestPath = resolve(root, "config/repository/federated-repositories.json");
  const matrixPath = resolve(root, "config/repository/compatibility-matrix.json");
  const bomPath = resolve(root, "config/repository/bom.json");
  const manifest = JSON.parse(await readFile(manifestPath, "utf8"));
  const matrix = JSON.parse(await readFile(matrixPath, "utf8"));
  const bom = JSON.parse(await readFile(bomPath, "utf8"));
  const repository = manifest.repositories.find((candidate) => candidate.id === id);
  const oldSha = repository.pin;
  const child = resolve(root, repository.path);

  await writeFixtureFile(child, "README.md", `${id} advanced\n`);
  run("git", ["add", "README.md"], child);
  run("git", ["commit", "--quiet", "-m", "advance fixture"], child);
  const newSha = run("git", ["rev-parse", "HEAD"], child);
  repository.pin = newSha;
  const manifestSource = `${JSON.stringify(manifest, null, 2)}\n`;
  await writeFile(manifestPath, manifestSource, "utf8");
  run("git", ["add", "config/repository/federated-repositories.json", id], root);
  run("git", ["commit", "--quiet", "-m", "promote advanced fixture pin"], root);
  const promotionCommit = run("git", ["rev-parse", "HEAD"], root);

  bom.manifestDigest = framedDigest([Buffer.from(manifestSource, "utf8")]);
  bom.promotionCommit = promotionCommit;
  bom.repositories.find((candidate) => candidate.id === id).pin = newSha;
  bom.runtimeGate.combinationDigest = combinationDigest(manifest, matrix);
  await writeFile(bomPath, `${JSON.stringify(canonical(bom), null, 2)}\n`, "utf8");
  run("git", ["add", "config/repository/bom.json"], root);
  run("git", ["commit", "--quiet", "-m", "record advanced fixture BOM"], root);

  run("git", ["checkout", "--quiet", "--detach", oldSha], child);
  run("git", ["add", id], root);
  run("git", ["commit", "--quiet", "-m", "restore stale fixture gitlink"], root);
  return { newSha, oldSha };
}

function validSnapshot() {
  return {
    schemaVersion: 1,
    wave: "wave-1-platform-identity-site-policy",
    specification: {
      status: "internally-approved",
      implementationAuthorized: true,
      gaRuntimeSemanticChangeAuthorized: false,
      parent: {
        declaredFile: "2026-07-25-platform-web-session-target-architecture-design.md",
        declaredVersion: "1.5",
        actualVersion: "1.5",
        exists: true,
      },
    },
    decisions: {
      adr012: { adopted: true, digest: DIGEST },
      adr005: { supersededBy: "ADR-012", reverseLink: true },
      expectedAdr012Digest: DIGEST,
    },
    repository: {
      rootStatus: "",
      manifestDigest: DIGEST,
      bomManifestDigest: DIGEST,
      contractsDigest: DIGEST,
      evidenceDigest: DIGEST,
      evidenceVerified: true,
      generatedContractsVerified: true,
      repositories: [
        { id: "kokoro-agent", expectedSha: SHA, actualSha: SHA, status: "" },
        { id: "kokoro-platform", expectedSha: SHA, actualSha: SHA, status: "" },
        { id: "kokoro-session", expectedSha: SHA, actualSha: SHA, status: "" },
        { id: "kokoro-web", expectedSha: SHA, actualSha: SHA, status: "" },
      ],
    },
    ga: {
      expectedSha: SHA,
      actualSha: SHA,
      status: "",
      expectedControlSpecSha256: DIGEST,
      controlSpecSha256: DIGEST,
      expectedControlAdapterSha256: OTHER_DIGEST,
      controlAdapterSha256: OTHER_DIGEST,
    },
  };
}

function expectCode(snapshot, code) {
  assert.throws(
    () => assertPreflightSnapshot(snapshot),
    (error) => error instanceof PreflightError && error.code === code,
  );
}

test("accepts a fully approved, clean, pinned baseline", () => {
  assert.doesNotThrow(() => assertPreflightSnapshot(validSnapshot()));
});

test("fails closed on approval, authorization, parent, and ADR drift", () => {
  const cases = [
    ["wave1_spec_unapproved", (value) => { value.specification.status = "draft"; }],
    ["wave1_implementation_unauthorized", (value) => { value.specification.implementationAuthorized = false; }],
    ["wave1_ga_semantic_change_authorized", (value) => { value.specification.gaRuntimeSemanticChangeAuthorized = true; }],
    ["wave1_parent_missing", (value) => { value.specification.parent.exists = false; }],
    ["wave1_parent_mismatch", (value) => { value.specification.parent.actualVersion = "1.4"; }],
    ["wave1_parent_mismatch", (value) => { value.specification.parent.declaredFile = "replacement-parent.md"; }],
    ["wave1_parent_mismatch", (value) => {
      value.specification.parent.declaredVersion = "1.6";
      value.specification.parent.actualVersion = "1.6";
    }],
    ["wave1_adr012_not_adopted", (value) => { value.decisions.adr012.adopted = false; }],
    ["wave1_adr012_digest_mismatch", (value) => { value.decisions.adr012.digest = null; }],
    ["wave1_adr012_digest_mismatch", (value) => { value.decisions.expectedAdr012Digest = OTHER_DIGEST; }],
    ["wave1_adr005_not_superseded", (value) => { value.decisions.adr005.supersededBy = null; }],
    ["wave1_adr005_reverse_link_missing", (value) => { value.decisions.adr005.reverseLink = false; }],
  ];

  for (const [code, mutate] of cases) {
    const snapshot = validSnapshot();
    mutate(snapshot);
    expectCode(snapshot, code);
  }
});

test("rejects unknown fields throughout the closed baseline schema", () => {
  expectCode(null, "wave1_snapshot_invalid");
  expectCode([], "wave1_snapshot_invalid");
  const mutations = [
    (value) => { value.unknown = true; },
    (value) => { value.specification.unknown = true; },
    (value) => { value.specification.parent.unknown = true; },
    (value) => { value.decisions.unknown = true; },
    (value) => { value.decisions.adr012.unknown = true; },
    (value) => { value.decisions.adr005.unknown = true; },
    (value) => { value.repository.unknown = true; },
    (value) => { value.repository.repositories[0].unknown = true; },
    (value) => { value.ga.unknown = true; },
  ];
  for (const mutate of mutations) {
    const snapshot = validSnapshot();
    mutate(snapshot);
    expectCode(snapshot, "wave1_snapshot_invalid");
  }

  const malformed = validSnapshot();
  malformed.repository.repositories = [
    malformed.repository.repositories[0],
    malformed.repository.repositories[0],
    malformed.repository.repositories[1],
    malformed.repository.repositories[2],
  ];
  expectCode(malformed, "wave1_snapshot_invalid");

  const nullRepository = validSnapshot();
  nullRepository.repository.repositories[0] = null;
  expectCode(nullRepository, "wave1_snapshot_invalid");
});

test("fails closed on absent or mismatched evidence, pins, contracts, and generated artifacts", () => {
  const cases = [
    ["wave1_manifest_digest_missing", (value) => { value.repository.manifestDigest = null; }],
    ["wave1_manifest_digest_mismatch", (value) => { value.repository.bomManifestDigest = OTHER_DIGEST; }],
    ["wave1_contract_digest_missing", (value) => { value.repository.contractsDigest = null; }],
    ["wave1_evidence_digest_missing", (value) => { value.repository.evidenceDigest = null; }],
    ["wave1_evidence_invalid", (value) => { value.repository.evidenceVerified = false; }],
    ["wave1_generated_contracts_invalid", (value) => { value.repository.generatedContractsVerified = false; }],
    ["wave1_child_pin_mismatch", (value) => { value.repository.repositories[0].expectedSha = null; }],
    ["wave1_child_pin_mismatch", (value) => { value.repository.repositories[2].actualSha = OTHER_SHA; }],
  ];

  for (const [code, mutate] of cases) {
    const snapshot = validSnapshot();
    mutate(snapshot);
    expectCode(snapshot, code);
  }
});

test("uses full porcelain status for Root, every child, and GA", () => {
  const rootDirty = validSnapshot();
  rootDirty.repository.rootStatus = "?? untracked.txt\n";
  expectCode(rootDirty, "wave1_root_dirty");

  const childDirty = validSnapshot();
  childDirty.repository.repositories[1].status = " M tracked.ts\n?? untracked.ts\n";
  expectCode(childDirty, "wave1_child_dirty");

  const gaDirty = validSnapshot();
  gaDirty.ga.status = "?? hidden-by-normal-status.txt\n";
  expectCode(gaDirty, "wave1_ga_dirty");
});

test("freezes exact GA SHA and both control hashes", () => {
  const shaDrift = validSnapshot();
  shaDrift.ga.actualSha = OTHER_SHA;
  expectCode(shaDrift, "wave1_ga_sha_mismatch");

  const missingSpecHash = validSnapshot();
  missingSpecHash.ga.controlSpecSha256 = null;
  expectCode(missingSpecHash, "wave1_ga_control_digest_missing");

  const missingAdapterHash = validSnapshot();
  missingAdapterHash.ga.controlAdapterSha256 = null;
  expectCode(missingAdapterHash, "wave1_ga_adapter_digest_missing");

  const specDrift = validSnapshot();
  specDrift.ga.controlSpecSha256 = OTHER_DIGEST;
  expectCode(specDrift, "wave1_ga_control_digest_mismatch");

  const adapterDrift = validSnapshot();
  adapterDrift.ga.controlAdapterSha256 = DIGEST;
  expectCode(adapterDrift, "wave1_ga_adapter_digest_mismatch");
});

test("CLI rejects an empty BOM evidence inventory even when its digest is self-consistent", async (t) => {
  const fixture = await createBomFixture({ emptyEvidence: true });
  t.after(() => rm(fixture, { recursive: true, force: true }));

  const result = spawnSync(
    process.execPath,
    [
      preflightScript,
      "--root",
      fixture,
      "--write-baseline",
      ".git/kokoro-wave1/baseline.json",
    ],
    { cwd: fixture, encoding: "utf8", shell: false },
  );

  assert.notEqual(result.status, 0, result.stdout);
  assert.match(
    result.stderr,
    /wave1_evidence_invalid/u,
    `fixture status after CLI:\n${run("git", ["status", "--porcelain=v1", "--untracked-files=all"], fixture)}`,
  );
  await assert.rejects(readFile(resolve(fixture, ".git/kokoro-wave1/baseline.json")), {
    code: "ENOENT",
  });
});

test("CLI writes a private baseline for an authoritative clean BOM", {
  skip: !supportsPosixDirFd,
}, async (t) => {
  const fixture = await createBomFixture({ emptyEvidence: false });
  t.after(() => rm(fixture, { recursive: true, force: true }));

  const result = spawnSync(
    process.execPath,
    [
      preflightScript,
      "--root",
      fixture,
      "--write-baseline",
      ".git/kokoro-wave1/baseline.json",
    ],
    { cwd: fixture, encoding: "utf8", shell: false },
  );

  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /wave1_preflight_ok:/u);
  const baseline = JSON.parse(
    await readFile(resolve(fixture, ".git/kokoro-wave1/baseline.json"), "utf8"),
  );
  assert.equal(baseline.repository.evidenceVerified, true);
});

test("CLI preserves a previous baseline when manifest and BOM advance past the current gitlink and child", {
  skip: !supportsPosixDirFd,
}, async (t) => {
  const fixture = await createBomFixture({ emptyEvidence: false });
  t.after(() => rm(fixture, { recursive: true, force: true }));
  const baselineArgument = ".git/kokoro-wave1/baseline.json";
  const baselinePath = resolve(fixture, baselineArgument);
  const initial = spawnSync(
    process.execPath,
    [preflightScript, "--root", fixture, "--write-baseline", baselineArgument],
    { cwd: fixture, encoding: "utf8", shell: false },
  );
  assert.equal(initial.status, 0, initial.stderr);
  const previousBaseline = await readFile(baselinePath, "utf8");

  await advanceManifestAndBomButRestoreCheckout(fixture, "kokoro-agent");
  assert.equal(run("git", ["status", "--porcelain=v1", "--untracked-files=all"], fixture), "");
  const result = spawnSync(
    process.execPath,
    [preflightScript, "--root", fixture, "--write-baseline", baselineArgument],
    { cwd: fixture, encoding: "utf8", shell: false },
  );

  assert.equal(result.status, 1, result.stdout);
  assert.match(result.stderr, /^wave1_child_pin_mismatch: kokoro-agent\s*$/u);
  assert.equal(await readFile(baselinePath, "utf8"), previousBaseline);
});

test("CLI validates a previous baseline as a closed document before replacing it", {
  skip: !supportsPosixDirFd,
}, async (t) => {
  const fixture = await createBomFixture({ emptyEvidence: false });
  t.after(() => rm(fixture, { recursive: true, force: true }));
  const baselineArgument = ".git/kokoro-wave1/baseline.json";
  const baselinePath = resolve(fixture, baselineArgument);
  const initial = spawnSync(
    process.execPath,
    [preflightScript, "--root", fixture, "--write-baseline", baselineArgument],
    { cwd: fixture, encoding: "utf8", shell: false },
  );
  assert.equal(initial.status, 0, initial.stderr);
  const malformed = JSON.parse(await readFile(baselinePath, "utf8"));
  malformed.repository.repositories[0].unknown = true;
  const malformedSource = `${JSON.stringify(malformed, null, 2)}\n`;
  await writeFile(baselinePath, malformedSource, "utf8");

  const result = spawnSync(
    process.execPath,
    [preflightScript, "--root", fixture, "--write-baseline", baselineArgument],
    { cwd: fixture, encoding: "utf8", shell: false },
  );
  assert.equal(result.status, 1, result.stdout);
  assert.match(result.stderr, /^wave1_baseline_invalid: wave1_snapshot_invalid\s*$/u);
  assert.equal(await readFile(baselinePath, "utf8"), malformedSource);
});

test("baseline arguments reject worktree paths, other absolute paths, and unknown options", async (t) => {
  const fixture = await createBomFixture({ emptyEvidence: false });
  t.after(() => rm(fixture, { recursive: true, force: true }));
  const cases = [
    ["--write-baseline", "baseline.json"],
    ["--write-baseline", resolve(fixture, "elsewhere", "baseline.json")],
    ["--verify-baseline", ".git/kokoro-wave1/baseline.json"],
  ];

  for (const arguments_ of cases) {
    assert.throws(
      () => parseArguments(["--root", fixture, ...arguments_]),
      (error) => error instanceof PreflightError && error.code === "wave1_arguments_invalid",
    );
  }
});

test("CLI rejects a symlink escape from the exact baseline location", {
  skip: process.platform === "win32",
}, async (t) => {
  const fixture = await createBomFixture({ emptyEvidence: false });
  const escaped = await mkdtemp(join(tmpdir(), "kokoro-wave1-baseline-escape-"));
  t.after(() => rm(fixture, { recursive: true, force: true }));
  t.after(() => rm(escaped, { recursive: true, force: true }));
  await symlink(escaped, resolve(fixture, ".git/kokoro-wave1"), "dir");

  const result = spawnSync(
    process.execPath,
    [
      preflightScript,
      "--root",
      fixture,
      "--write-baseline",
      ".git/kokoro-wave1/baseline.json",
    ],
    { cwd: fixture, encoding: "utf8", shell: false },
  );

  assert.equal(result.status, 1, result.stdout);
  assert.match(result.stderr, /^wave1_arguments_invalid: --write-baseline\s*$/u);
  await assert.rejects(readFile(resolve(escaped, "baseline.json")), { code: "ENOENT" });
});

test("atomic writer rejects a directory swap before rename and never touches the escape target", {
  skip: process.platform === "win32",
}, async (t) => {
  const fixture = await mkdtemp(join(tmpdir(), "kokoro-wave1-writer-race-"));
  const escaped = await mkdtemp(join(tmpdir(), "kokoro-wave1-writer-escape-"));
  t.after(() => rm(fixture, { recursive: true, force: true }));
  t.after(() => rm(escaped, { recursive: true, force: true }));
  configureRepository(fixture);
  const options = parseArguments([
    "--root",
    fixture,
    "--write-baseline",
    ".git/kokoro-wave1/baseline.json",
  ]);
  const targetDirectory = resolve(options.baselinePath, "..");
  const displaced = resolve(options.baselinePath, "..", "..", "kokoro-wave1-displaced");
  await writeFile(resolve(escaped, "baseline.json"), "sentinel\n", "utf8");

  await assert.rejects(
    () => writeBaselineAtomic(options.baselineTarget, validSnapshot(), {
      beforeRename: async () => {
        await rename(targetDirectory, displaced);
        await symlink(escaped, targetDirectory, "dir");
      },
    }),
    { code: "wave1_baseline_path_changed" },
  );
  assert.equal(await readFile(resolve(escaped, "baseline.json"), "utf8"), "sentinel\n");
  assert.deepEqual(await stat(displaced).then((value) => value.isDirectory()), true);
});

test("atomic writer cannot escape when the directory swaps after the final identity check", {
  skip: process.platform === "win32",
}, async (t) => {
  const fixture = await mkdtemp(join(tmpdir(), "kokoro-wave1-final-race-"));
  const escaped = await mkdtemp(join(tmpdir(), "kokoro-wave1-final-escape-"));
  t.after(() => rm(fixture, { recursive: true, force: true }));
  t.after(() => rm(escaped, { recursive: true, force: true }));
  configureRepository(fixture);
  const options = parseArguments([
    "--root",
    fixture,
    "--write-baseline",
    ".git/kokoro-wave1/baseline.json",
  ]);
  const targetDirectory = resolve(options.baselinePath, "..");
  const displaced = resolve(options.baselinePath, "..", "..", "kokoro-wave1-final-displaced");
  await writeFile(resolve(escaped, "baseline.json"), "sentinel\n", "utf8");

  await assert.rejects(
    () => writeBaselineAtomic(options.baselineTarget, validSnapshot(), {
      afterFinalCheck: async () => {
        await rename(targetDirectory, displaced);
        await symlink(escaped, targetDirectory, "dir");
      },
    }),
    { code: "wave1_baseline_path_changed" },
  );
  assert.equal(await readFile(resolve(escaped, "baseline.json"), "utf8"), "sentinel\n");
});

test("atomic writer targets the per-worktree git directory and persists mode 0600", {
  skip: !supportsPosixDirFd,
}, async (t) => {
  const fixture = await mkdtemp(join(tmpdir(), "kokoro-wave1-linked-worktree-"));
  const linked = resolve(fixture, "linked");
  t.after(() => rm(fixture, { recursive: true, force: true }));
  configureRepository(fixture);
  await writeFixtureFile(fixture, "README.md", "primary\n");
  run("git", ["add", "README.md"], fixture);
  run("git", ["commit", "--quiet", "-m", "primary"], fixture);
  run("git", ["worktree", "add", "--quiet", "--detach", linked], fixture);
  const options = parseArguments([
    "--root",
    linked,
    "--write-baseline",
    ".git/kokoro-wave1/baseline.json",
  ]);

  await writeBaselineAtomic(options.baselineTarget, validSnapshot());

  assert.deepEqual(JSON.parse(await readFile(options.baselinePath, "utf8")), validSnapshot());
  if (process.platform !== "win32") {
    assert.equal((await stat(options.baselinePath)).mode & 0o777, 0o600);
  }
  await assert.rejects(
    readFile(resolve(fixture, ".git/kokoro-wave1/baseline.json")),
    { code: "ENOENT" },
  );
});

test("CLI keeps the dirty Root failure authoritative and does not write a baseline", async (t) => {
  const fixture = await createBomFixture({ emptyEvidence: false });
  t.after(() => rm(fixture, { recursive: true, force: true }));
  await writeFixtureFile(fixture, "untracked.txt", "dirty\n");

  const result = spawnSync(
    process.execPath,
    [
      preflightScript,
      "--root",
      fixture,
      "--write-baseline",
      ".git/kokoro-wave1/baseline.json",
    ],
    { cwd: fixture, encoding: "utf8", shell: false },
  );

  assert.equal(result.status, 1, result.stdout);
  assert.match(result.stderr, /^wave1_root_dirty\s*$/u);
  await assert.rejects(readFile(resolve(fixture, ".git/kokoro-wave1/baseline.json")), {
    code: "ENOENT",
  });
});

test("writes a validated baseline atomically and never overwrites on validation failure", {
  skip: !supportsPosixDirFd,
}, async () => {
  const directory = await mkdtemp(join(tmpdir(), "kokoro-wave1-preflight-"));
  configureRepository(directory);
  const options = parseArguments([
    "--root",
    directory,
    "--write-baseline",
    ".git/kokoro-wave1/baseline.json",
  ]);
  const snapshot = validSnapshot();

  await writeBaselineAtomic(options.baselineTarget, snapshot);
  assert.deepEqual(JSON.parse(await readFile(options.baselinePath, "utf8")), snapshot);

  const invalid = validSnapshot();
  invalid.repository.rootStatus = "?? dirty\n";
  await assert.rejects(() => writeBaselineAtomic(options.baselineTarget, invalid), {
    code: "wave1_root_dirty",
  });
  assert.deepEqual(JSON.parse(await readFile(options.baselinePath, "utf8")), snapshot);
});
