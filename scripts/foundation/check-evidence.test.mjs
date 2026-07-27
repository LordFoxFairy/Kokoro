import assert from "node:assert/strict";
import { mkdtemp, mkdir, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, resolve } from "node:path";
import { spawnSync } from "node:child_process";
import test from "node:test";
import { fileURLToPath } from "node:url";

const repositoryRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const checker = resolve(repositoryRoot, "scripts/foundation/check-evidence.mjs");
const schemaPath = resolve(
  repositoryRoot,
  "docs/reports/evidence/wave-0/ownership-attestation.schema.json",
);

const validAttestation = `attestedBy: kokoro-repository-owner
authority: repository-owner
attestedAt: 2026-07-26T12:00:00.000Z
attestationRef: codex-task:opaque-owner-confirmation
repositories:
  - Kokoro
  - kokoro-agent
  - kokoro-platform
  - kokoro-session
  - kokoro-web
licenseRef: LicenseRef-Kokoro-Internal-Proprietary
`;

async function withFixture(attestation, run) {
  const root = await mkdtemp(resolve(tmpdir(), "kokoro-evidence-test-"));
  const evidenceDirectory = resolve(root, "docs/reports/evidence/wave-0");
  await mkdir(evidenceDirectory, { recursive: true });
  if (attestation !== undefined) {
    await writeFile(
      resolve(evidenceDirectory, "ownership-attestation.yaml"),
      attestation,
      "utf8",
    );
  }
  try {
    await run(root);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
}

function runChecker(root) {
  return spawnSync(
    process.execPath,
    [checker, "--require-ownership", "--root", root],
    { encoding: "utf8" },
  );
}

test("reports a stable code when ownership attestation is missing", async () => {
  await withFixture(undefined, (root) => {
    const result = runChecker(root);
    assert.notEqual(result.status, 0);
    assert.match(result.stderr, /ownership_attestation_missing/);
  });
});

test("reports a stable code for placeholder or incomplete ownership evidence", async () => {
  const invalid = validAttestation
    .replace("kokoro-repository-owner", "TODO")
    .replace("  - kokoro-web\n", "  - kokoro-agent\n");

  await withFixture(invalid, (root) => {
    const result = runChecker(root);
    assert.notEqual(result.status, 0);
    assert.match(result.stderr, /ownership_attestation_invalid/);
  });
});

test("accepts complete ownership evidence", async () => {
  await withFixture(validAttestation, (root) => {
    const result = runChecker(root);
    assert.equal(result.status, 0, result.stderr);
    assert.match(result.stdout, /ownership_attestation_valid/);
  });
});

test("ownership schema closes the object and requires the exact repository set", async () => {
  const schema = JSON.parse(await readFile(schemaPath, "utf8"));
  assert.equal(schema.additionalProperties, false);
  assert.deepEqual(schema.required, [
    "attestedBy",
    "authority",
    "attestedAt",
    "attestationRef",
    "repositories",
    "licenseRef",
  ]);
  assert.equal(schema.properties.authority.const, "repository-owner");
  assert.equal(
    schema.properties.licenseRef.const,
    "LicenseRef-Kokoro-Internal-Proprietary",
  );
  assert.equal(schema.properties.repositories.minItems, 5);
  assert.equal(schema.properties.repositories.maxItems, 5);
  assert.equal(schema.properties.repositories.uniqueItems, true);
  assert.deepEqual(
    schema.properties.repositories.allOf.map(({ contains }) => contains.const),
    ["Kokoro", "kokoro-agent", "kokoro-platform", "kokoro-session", "kokoro-web"],
  );

  for (const property of ["attestedBy", "attestedAt", "attestationRef"]) {
    const pattern = new RegExp(schema.properties[property].pattern);
    assert.equal(pattern.test("Pending"), false, `${property} accepted Pending`);
    assert.equal(pattern.test("ToDo"), false, `${property} accepted ToDo`);
    assert.equal(pattern.test("placeHolder"), false, `${property} accepted placeHolder`);
  }
});
