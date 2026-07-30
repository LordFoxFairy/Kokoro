import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { spawnSync } from "node:child_process";
import { access, cp, mkdir, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, resolve } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

import {
  BOM_ATTESTED_CONTRACT_KEYS,
  BOM_EVIDENCE_KEYS,
  BOM_KEYS,
  BOM_PROTOCOL_KEYS,
  BOM_REPOSITORY_KEYS,
  BOM_RUNTIME_GATE_KEYS,
  combinationDigest,
  framedDigest,
} from "./generate-bom.mjs";

const repositoryRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const generator = resolve(repositoryRoot, "scripts/repository/generate-bom.mjs");
const schemaPath = resolve(repositoryRoot, "config/repository/bom.schema.json");
const COPIED_FILES = [
  "config/repository/federated-repositories.json",
  "config/repository/compatibility-matrix.json",
  "docs/reports/evidence/wave-0/federated-repository-baseline.md",
  "docs/reports/evidence/wave-0/ownership-attestation.yaml",
];

function run(command, args, cwd, expectedStatus = 0) {
  const result = spawnSync(command, args, { cwd, encoding: "utf8" });
  assert.equal(
    result.status,
    expectedStatus,
    `${command} ${args.join(" ")}\nstdout: ${result.stdout}\nstderr: ${result.stderr}`,
  );
  return result;
}

function git(cwd, ...args) {
  return run("git", args, cwd).stdout.trim();
}

function runGenerator(fixture, ...extra) {
  return spawnSync(process.execPath, [generator, "--root", fixture.root, ...extra], {
    cwd: fixture.root,
    encoding: "utf8",
  });
}

function generateArgs(fixture) {
  return ["--runtime-evidence", fixture.runtimeEvidencePath];
}

async function readManifestAndMatrix(root) {
  return {
    manifest: JSON.parse(await readFile(resolve(root, COPIED_FILES[0]), "utf8")),
    matrix: JSON.parse(await readFile(resolve(root, COPIED_FILES[1]), "utf8")),
  };
}

function runtimeEvidence(manifest, matrix, overrides = {}) {
  return {
    schemaVersion: 1,
    runnerVersion: 1,
    combinationId: matrix.combinationId,
    combinationDigest: combinationDigest(manifest, matrix),
    treeMode: "index",
    outcome: "pass",
    reasonCode: "ok",
    startedAt: "2026-07-27T00:00:00.000Z",
    completedAt: "2026-07-27T00:01:00.000Z",
    durationMs: 60_000,
    repositories: manifest.repositories.map(({ id, pin }) => ({ id, sha: pin })),
    manifestDigest: "0".repeat(64),
    matrixDigest: "0".repeat(64),
    preflightPinVerification: "pass",
    postflightPinVerification: "pass",
    services: [],
    scenarios: [],
    ...overrides,
  };
}

async function writeRuntimeEvidence(fixture, overrides = {}) {
  const { manifest, matrix } = await readManifestAndMatrix(fixture.root);
  await writeFile(
    fixture.runtimeEvidencePath,
    JSON.stringify(runtimeEvidence(manifest, matrix, overrides)),
    "utf8",
  );
}

async function makeFixture() {
  const root = await mkdtemp(resolve(tmpdir(), "kokoro-bom-test-"));
  git(root, "init", "-b", "main");
  git(root, "config", "user.email", "test@example.com");
  git(root, "config", "user.name", "Kokoro Test");
  for (const path of COPIED_FILES) {
    const target = resolve(root, path);
    await mkdir(dirname(target), { recursive: true });
    await cp(resolve(repositoryRoot, path), target);
  }
  await writeFile(resolve(root, ".gitignore"), "tmp/\n", "utf8");
  git(root, "add", ".gitignore", "config", "docs");
  const manifest = JSON.parse(await readFile(resolve(root, COPIED_FILES[0]), "utf8"));
  for (const { path, pin } of manifest.repositories) {
    git(root, "update-index", "--add", "--cacheinfo", `160000,${pin},${path}`);
  }
  git(root, "commit", "-m", "promote verified wave 0 pins");
  const promotionCommit = git(root, "rev-parse", "HEAD");

  await mkdir(resolve(root, "tmp"), { recursive: true });
  const fixture = {
    root,
    promotionCommit,
    bomPath: resolve(root, "config/repository/bom.json"),
    runtimeEvidencePath: resolve(root, "tmp/pinned-compatibility.json"),
  };
  await writeRuntimeEvidence(fixture);
  return fixture;
}

async function withFixture(runFixture) {
  const fixture = await makeFixture();
  try {
    await runFixture(fixture);
  } finally {
    await rm(fixture.root, { recursive: true, force: true });
  }
}

async function assertNoBom(fixture) {
  await assert.rejects(access(fixture.bomPath), { code: "ENOENT" });
}

test("length-framed digest prefixes every part with its byte length", () => {
  assert.equal(
    framedDigest([Buffer.from("a", "utf8"), Buffer.from("bc", "utf8")]),
    createHash("sha256").update("1:a2:bc", "utf8").digest("hex"),
  );
  assert.notEqual(framedDigest(["ab"]), framedDigest(["a", "b"]));
  assert.equal(framedDigest([]), createHash("sha256").update("").digest("hex"));
});

test("mirrors the compatibility runner's combination digest algorithm", async () => {
  const runner = await readFile(
    resolve(repositoryRoot, "scripts/repository/run-pinned-compatibility.mjs"),
    "utf8",
  );
  assert.match(runner, /digest\(\{ repositories, contracts, requiredScenarios \}\)/u);
  assert.match(runner, /createHash\("sha256"\)\.update\(source\)\.digest\("hex"\)/u);
  assert.match(runner, /JSON\.stringify\(canonical\(value\)\)/u);
});

test("writes a canonical BOM that binds the promotion commit, pins and recoverable refs", async () => {
  await withFixture(async (fixture) => {
    const result = runGenerator(fixture, ...generateArgs(fixture));
    assert.equal(result.status, 0, result.stderr);
    assert.match(
      result.stdout,
      new RegExp(`repository_bom_written: config/repository/bom.json promotionCommit=${fixture.promotionCommit}`, "u"),
    );

    const source = await readFile(fixture.bomPath, "utf8");
    assert.equal(source.endsWith("}\n"), true);
    const bom = JSON.parse(source);
    assert.deepEqual(Object.keys(bom), [...BOM_KEYS].sort());
    assert.equal(bom.promotionCommit, fixture.promotionCommit);
    assert.equal(bom.repositoryTopology, "federated-submodules-v1");
    assert.equal(bom.runtimeGate.outcome, "pass");

    const { manifest } = await readManifestAndMatrix(fixture.root);
    const expected = [...manifest.repositories].sort((left, right) => left.id.localeCompare(right.id));
    assert.deepEqual(
      bom.repositories.map(({ id, pin, recoverableRef }) => ({ id, pin, recoverableRef })),
      expected.map(({ id, pin, recoverableRef }) => ({ id, pin, recoverableRef })),
    );
    assert.equal(new Set(bom.repositories.map(({ recoverableRef }) => recoverableRef)).size, 4);
    assert.equal(
      bom.repositories.every(({ protocols }) => protocols.length > 0),
      true,
    );
    assert.equal(
      bom.repositories.every(({ protocols }) => protocols.every((protocol) => !Object.hasOwn(protocol, "lifecycle"))),
      true,
    );
    assert.equal(
      bom.repositories.some(({ protocols }) => protocols.some(({ id }) => id === "platform-media-runtime")),
      false,
    );
    assert.deepEqual(bom.contracts.find(({ id }) => id === "hub-runtime"), {
      consumers: ["kokoro-agent"],
      id: "hub-runtime",
      providers: ["kokoro-platform"],
      version: 1,
    });
    assert.deepEqual(
      bom.repositories.find(({ id }) => id === "kokoro-agent").protocols
        .find(({ id }) => id === "hub-runtime"),
      { id: "hub-runtime", role: "consumer", version: 1 },
    );
    assert.deepEqual(
      bom.repositories.find(({ id }) => id === "kokoro-platform").protocols
        .find(({ id }) => id === "hub-runtime"),
      { id: "hub-runtime", role: "provider", version: 1 },
    );
    assert.equal(
      bom.repositories.find(({ id }) => id === "kokoro-session").protocols
        .some(({ id }) => id === "hub-runtime"),
      false,
    );
    assert.deepEqual(
      bom.evidence.map(({ path }) => path),
      [
        "docs/reports/evidence/wave-0/federated-repository-baseline.md",
        "docs/reports/evidence/wave-0/ownership-attestation.yaml",
      ],
    );
  });
});

test("check mode accepts the generated BOM and regenerates byte-identical output", async () => {
  await withFixture(async (fixture) => {
    assert.equal(runGenerator(fixture, ...generateArgs(fixture)).status, 0);
    const first = await readFile(fixture.bomPath, "utf8");

    const checked = runGenerator(fixture, "--check");
    assert.equal(checked.status, 0, checked.stderr);
    assert.match(checked.stdout, /repository_bom_verified: config\/repository\/bom\.json/u);

    assert.equal(runGenerator(fixture, ...generateArgs(fixture)).status, 0);
    assert.equal(await readFile(fixture.bomPath, "utf8"), first);
  });
});

test("check mode keeps the recorded parent commit after the BOM itself is committed", async () => {
  await withFixture(async (fixture) => {
    assert.equal(runGenerator(fixture, ...generateArgs(fixture)).status, 0);
    git(fixture.root, "add", "config/repository/bom.json");
    git(fixture.root, "commit", "-m", "record repository bom");
    const bomCommit = git(fixture.root, "rev-parse", "HEAD");

    const bom = JSON.parse(await readFile(fixture.bomPath, "utf8"));
    assert.notEqual(bom.promotionCommit, bomCommit);
    assert.equal(bom.promotionCommit, fixture.promotionCommit);

    const checked = runGenerator(fixture, "--check");
    assert.equal(checked.status, 0, checked.stderr);
    assert.match(checked.stdout, new RegExp(`promotionCommit=${fixture.promotionCommit}`, "u"));
  });
});

test("check mode fails closed when the BOM is missing or has drifted", async () => {
  await withFixture(async (fixture) => {
    const missing = runGenerator(fixture, "--check");
    assert.notEqual(missing.status, 0);
    assert.match(missing.stderr, /bom_missing/u);

    assert.equal(runGenerator(fixture, ...generateArgs(fixture)).status, 0);
    const bom = JSON.parse(await readFile(fixture.bomPath, "utf8"));
    bom.contractsDigest = "1".repeat(64);
    await writeFile(fixture.bomPath, `${JSON.stringify(bom, null, 2)}\n`, "utf8");
    const drifted = runGenerator(fixture, "--check");
    assert.notEqual(drifted.status, 0);
    assert.match(drifted.stderr, /bom_drift/u);
  });
});

test("check mode fails when a declared evidence document changes", async () => {
  await withFixture(async (fixture) => {
    assert.equal(runGenerator(fixture, ...generateArgs(fixture)).status, 0);
    const evidencePath = resolve(fixture.root, "docs/reports/evidence/wave-0/federated-repository-baseline.md");
    await writeFile(evidencePath, `${await readFile(evidencePath, "utf8")}\nappended\n`, "utf8");
    const result = runGenerator(fixture, "--check");
    assert.notEqual(result.status, 0);
    assert.match(result.stderr, /bom_drift/u);
  });
});

test("rejects a BOM that carries a field naming its own containing commit", async () => {
  await withFixture(async (fixture) => {
    assert.equal(runGenerator(fixture, ...generateArgs(fixture)).status, 0);
    const bom = JSON.parse(await readFile(fixture.bomPath, "utf8"));
    bom.bomCommit = fixture.promotionCommit;
    await writeFile(fixture.bomPath, `${JSON.stringify(bom, null, 2)}\n`, "utf8");
    const result = runGenerator(fixture, "--check");
    assert.notEqual(result.status, 0);
    assert.match(result.stderr, /bom_self_reference_forbidden: bomCommit/u);
  });
});

test("rejects an unknown, abbreviated, or non-ancestor promotion commit", async () => {
  await withFixture(async (fixture) => {
    for (const candidate of [fixture.promotionCommit.slice(0, 12), "0".repeat(40)]) {
      const result = runGenerator(
        fixture,
        ...generateArgs(fixture),
        "--promotion-commit",
        candidate,
      );
      assert.notEqual(result.status, 0);
      assert.match(result.stderr, /bom_promotion_commit_invalid/u);
      await assertNoBom(fixture);
    }
  });
});

test("rejects a promotion commit whose gitlinks differ from the manifest pins", async () => {
  await withFixture(async (fixture) => {
    const manifestPath = resolve(fixture.root, COPIED_FILES[0]);
    const manifest = JSON.parse(await readFile(manifestPath, "utf8"));
    manifest.repositories[0].pin = "b".repeat(40);
    await writeFile(manifestPath, JSON.stringify(manifest, null, 2), "utf8");
    await writeRuntimeEvidence(fixture);

    const result = runGenerator(fixture, ...generateArgs(fixture));
    assert.notEqual(result.status, 0);
    assert.match(result.stderr, /bom_promotion_pin_mismatch: kokoro-agent/u);
    await assertNoBom(fixture);
  });
});

test("rejects runtime evidence that did not pass the exact combination", async () => {
  const cases = [
    [{ outcome: "fail", reasonCode: "required_scenario_failed" }, /bom_runtime_evidence_not_pass/u],
    [{ postflightPinVerification: "fail" }, /bom_runtime_evidence_not_pass/u],
    [{ combinationDigest: "c".repeat(64) }, /bom_runtime_evidence_combination_mismatch/u],
    [{ combinationId: "other-combination" }, /bom_runtime_evidence_invalid/u],
    [{ schemaVersion: 2 }, /bom_runtime_evidence_invalid/u],
  ];
  for (const [overrides, pattern] of cases) {
    await withFixture(async (fixture) => {
      await writeRuntimeEvidence(fixture, overrides);
      const result = runGenerator(fixture, ...generateArgs(fixture));
      assert.notEqual(result.status, 0);
      assert.match(result.stderr, pattern);
      await assertNoBom(fixture);
    });
  }
});

test("rejects runtime evidence recorded against different pins", async () => {
  await withFixture(async (fixture) => {
    const { manifest, matrix } = await readManifestAndMatrix(fixture.root);
    const evidence = runtimeEvidence(manifest, matrix);
    evidence.repositories[0].sha = "d".repeat(40);
    await writeFile(fixture.runtimeEvidencePath, JSON.stringify(evidence), "utf8");
    const result = runGenerator(fixture, ...generateArgs(fixture));
    assert.notEqual(result.status, 0);
    assert.match(result.stderr, /bom_runtime_evidence_pin_mismatch/u);
    await assertNoBom(fixture);
  });
});

test("requires runtime gate evidence to generate, and rejects unknown arguments", async () => {
  await withFixture(async (fixture) => {
    const withoutEvidence = runGenerator(fixture);
    assert.notEqual(withoutEvidence.status, 0);
    assert.match(withoutEvidence.stderr, /bom_arguments_invalid: --runtime-evidence is required/u);
    await assertNoBom(fixture);

    const missingEvidence = runGenerator(
      fixture,
      "--runtime-evidence",
      resolve(fixture.root, "tmp/absent.json"),
    );
    assert.notEqual(missingEvidence.status, 0);
    assert.match(missingEvidence.stderr, /bom_runtime_evidence_missing/u);

    const unknown = runGenerator(fixture, "--promote");
    assert.notEqual(unknown.status, 0);
    assert.match(unknown.stderr, /bom_arguments_invalid/u);
  });
});

test("published schema matches the generator's declared key contract", async () => {
  const schema = JSON.parse(await readFile(schemaPath, "utf8"));
  assert.equal(schema.additionalProperties, false);
  assert.deepEqual(Object.keys(schema.properties).sort(), [...BOM_KEYS].sort());
  assert.deepEqual([...schema.required].sort(), [...BOM_KEYS].sort());

  const repository = schema.properties.repositories.items;
  assert.equal(repository.additionalProperties, false);
  assert.deepEqual(Object.keys(repository.properties).sort(), [...BOM_REPOSITORY_KEYS].sort());
  assert.deepEqual([...repository.required].sort(), [...BOM_REPOSITORY_KEYS].sort());

  const protocol = repository.properties.protocols.items;
  assert.equal(protocol.additionalProperties, false);
  assert.deepEqual(Object.keys(protocol.properties).sort(), [...BOM_PROTOCOL_KEYS].sort());

  const contract = schema.properties.contracts.items;
  assert.equal(contract.additionalProperties, false);
  assert.deepEqual(Object.keys(contract.properties).sort(), [...BOM_ATTESTED_CONTRACT_KEYS].sort());
  assert.equal([...contract.required].includes("artifactDigest"), false);

  const evidence = schema.properties.evidence.items;
  assert.equal(evidence.additionalProperties, false);
  assert.deepEqual(Object.keys(evidence.properties).sort(), [...BOM_EVIDENCE_KEYS].sort());

  const runtimeGate = schema.properties.runtimeGate;
  assert.equal(runtimeGate.additionalProperties, false);
  assert.deepEqual(Object.keys(runtimeGate.properties).sort(), [...BOM_RUNTIME_GATE_KEYS].sort());
  assert.deepEqual([...runtimeGate.required].sort(), [...BOM_RUNTIME_GATE_KEYS].sort());
});
