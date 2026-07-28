import assert from "node:assert/strict";
import { mkdtemp, readFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import {
  PreflightError,
  assertPreflightSnapshot,
  writeBaselineAtomic,
} from "./preflight.mjs";

const SHA = "1".repeat(40);
const OTHER_SHA = "2".repeat(40);
const DIGEST = "a".repeat(64);
const OTHER_DIGEST = "b".repeat(64);

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
    ["wave1_adr012_not_adopted", (value) => { value.decisions.adr012.adopted = false; }],
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

test("fails closed on absent or mismatched evidence, pins, contracts, and generated artifacts", () => {
  const cases = [
    ["wave1_manifest_digest_missing", (value) => { value.repository.manifestDigest = null; }],
    ["wave1_manifest_digest_mismatch", (value) => { value.repository.bomManifestDigest = OTHER_DIGEST; }],
    ["wave1_contract_digest_missing", (value) => { value.repository.contractsDigest = null; }],
    ["wave1_evidence_digest_missing", (value) => { value.repository.evidenceDigest = null; }],
    ["wave1_evidence_invalid", (value) => { value.repository.evidenceVerified = false; }],
    ["wave1_generated_contracts_invalid", (value) => { value.repository.generatedContractsVerified = false; }],
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

test("writes a validated baseline atomically and never overwrites on validation failure", async () => {
  const directory = await mkdtemp(join(tmpdir(), "kokoro-wave1-preflight-"));
  const target = join(directory, "nested", "baseline.json");
  const snapshot = validSnapshot();

  await writeBaselineAtomic(target, snapshot);
  assert.deepEqual(JSON.parse(await readFile(target, "utf8")), snapshot);

  const invalid = validSnapshot();
  invalid.repository.rootStatus = "?? dirty\n";
  await assert.rejects(() => writeBaselineAtomic(target, invalid), {
    code: "wave1_root_dirty",
  });
  assert.deepEqual(JSON.parse(await readFile(target, "utf8")), snapshot);
});
