import assert from "node:assert/strict";
import { createHash, generateKeyPairSync, sign } from "node:crypto";
import { execFile } from "node:child_process";
import { cp, mkdir, mkdtemp, readFile, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { promisify } from "node:util";
import test from "node:test";

import {
  WebReleaseContractError,
  assertFrozenV1Compatible,
  canonicalizeJsonText,
  validateRepository,
} from "./check-web-release-composition.mjs";

const here = dirname(fileURLToPath(import.meta.url));
const repositoryRoot = resolve(here, "../..");
const execFileAsync = promisify(execFile);

function canonicalBytes(value) {
  return Buffer.from(canonicalizeJsonText(JSON.stringify(value)), "utf8");
}

function canonicalDigest(value) {
  return `sha256:${createHash("sha256").update(canonicalBytes(value)).digest("hex")}`;
}

function dssePae(payloadType, payload) {
  const type = Buffer.from(payloadType, "utf8");
  return Buffer.concat([Buffer.from(`DSSEv1 ${type.length} `), type, Buffer.from(` ${payload.length} `), payload]);
}

function resignVector(corpus, caseId, privateKey) {
  const vector = corpus.dsseVectors.find((candidate) => candidate.caseId === caseId);
  const document = corpus.positiveCases.find((candidate) => candidate.id === caseId).document;
  const payload = canonicalBytes(document);
  const pae = dssePae(vector.payloadType, payload);
  vector.expectedPaeSha256 = createHash("sha256").update(pae).digest("hex");
  vector.signatureBase64 = sign(null, pae, privateKey).toString("base64");
}

function refreshSigningIdentities(corpus) {
  const privateKeys = new Map();
  for (const vector of corpus.dsseVectors) {
    const { publicKey, privateKey } = generateKeyPairSync("ed25519");
    const publicDer = publicKey.export({ format: "der", type: "spki" });
    vector.publicKeySpkiDerBase64 = publicDer.toString("base64");
    privateKeys.set(vector.caseId, privateKey);
    const contractCase = corpus.positiveCases.find(({ id }) => id === vector.caseId);
    if (["release-certification-instance.v1", "release-certification-revocation.v1"].includes(contractCase.contractId)) {
      contractCase.document.producer.publicKeyFingerprint = `sha256:${createHash("sha256").update(publicDer).digest("hex")}`;
    }
  }
  return privateKeys;
}

function authorityMaterial(snapshot) {
  return {
    activationAttemptRef: snapshot.activationAttemptRef, phase: snapshot.phase, siteRelease: snapshot.siteRelease,
    candidate: snapshot.candidate, certification: snapshot.certification, trust: snapshot.trust, readAt: snapshot.readAt,
  };
}

function eligibilityMaterial(evidence) {
  return {
    activationAttemptRef: evidence.activationAttemptRef, siteRelease: evidence.siteRelease,
    beginAuthoritySnapshot: evidence.beginAuthoritySnapshot,
    immediateBeforePointerCasAuthoritySnapshot: evidence.immediateBeforePointerCasAuthoritySnapshot,
    decision: evidence.decision, evaluatedAt: evidence.evaluatedAt,
  };
}

function refreshCoherentChain(corpus) {
  const privateKeys = refreshSigningIdentities(corpus);
  const documents = new Map(corpus.positiveCases.map(({ contractId, document }) => [contractId, document]));
  const cases = new Map(corpus.positiveCases.map(({ id, document }) => [id, document]));
  const catalog = documents.get("product-surface-catalog.v1");
  const profile = documents.get("launch-product-profile.v1");
  const candidate = documents.get("site-release-candidate.v1");
  const inventory = documents.get("surface-inventory.v1");
  const material = documents.get("web-build-material-bundle.v1");
  const toolchain = documents.get("web-build-toolchain.v1");
  const registry = documents.get("web-composition-registry.v1");
  const intent = documents.get("web-build-intent.v1");
  const manifest = documents.get("compiled-web-manifest.v1");
  const provenance = documents.get("web-artifact-provenance-profile.v1");
  const certification = cases.get("certification-site-alpha");
  const revokedCertification = cases.get("certification-obsolete");
  const revocation = cases.get("revocation-obsolete-certification");
  const siteRelease = documents.get("site-release.v1");
  const beginSnapshot = cases.get("activation-authority-begin");
  const beforeCasSnapshot = cases.get("activation-authority-before-cas");
  const activationEvidence = cases.get("activation-eligibility-alpha");

  profile.productSurfaceCatalog.digest = canonicalDigest(catalog);
  profile.journeyClosure.digest = canonicalDigest(profile.journeyClosure.journeys);
  candidate.launchProductProfile.digest = canonicalDigest(profile);
  candidate.productSurfaceCatalog.digest = canonicalDigest(catalog);
  candidate.businessBindings.webBuildMaterialBundle.digest = canonicalDigest(material);
  inventory.siteReleaseCandidate.digest = canonicalDigest(candidate);
  inventory.launchProductProfile.digest = canonicalDigest(profile);
  inventory.productSurfaceCatalog.digest = canonicalDigest(catalog);
  intent.siteReleaseCandidate.digest = canonicalDigest(candidate);
  intent.launchProductProfile.digest = canonicalDigest(profile);
  intent.productSurfaceCatalog.digest = canonicalDigest(catalog);
  intent.surfaceInventory.digest = canonicalDigest(inventory);
  intent.webBuildMaterialBundle.digest = canonicalDigest(material);
  intent.webBuildToolchain.digest = canonicalDigest(toolchain);
  intent.webCompositionRegistry.digest = canonicalDigest(registry);
  manifest.buildIntentDigest = canonicalDigest(intent);
  manifest.siteReleaseCandidate = structuredClone(intent.siteReleaseCandidate);
  manifest.catalog = structuredClone(intent.productSurfaceCatalog);
  manifest.surfaceInventory = structuredClone(intent.surfaceInventory);
  manifest.registry = structuredClone(intent.webCompositionRegistry);
  manifest.toolchain = structuredClone(intent.webBuildToolchain);

  const parameters = provenance.predicate.buildDefinition.externalParameters;
  parameters.buildIntentDigest = canonicalDigest(intent);
  parameters.compiledWebManifestDigest = canonicalDigest(manifest);
  parameters.toolchain.digest = canonicalDigest(toolchain);
  const materialDependency = provenance.predicate.buildDefinition.resolvedDependencies.find(
    ({ uri }) => uri === `kokoro:material-bundle/${intent.webBuildMaterialBundle.ref}`,
  );
  if (materialDependency !== undefined) materialDependency.digest.sha256 = canonicalDigest(material).slice("sha256:".length);

  certification.siteReleaseCandidate = structuredClone(intent.siteReleaseCandidate);
  certification.launchProductProfile = structuredClone(intent.launchProductProfile);
  certification.productSurfaceCatalog = structuredClone(intent.productSurfaceCatalog);
  certification.surfaceInventory = structuredClone(intent.surfaceInventory);
  certification.webBuildIntent = { ref: intent.intentRef, digest: canonicalDigest(intent) };
  certification.compiledWebManifest = { ref: manifest.manifestRef, digest: canonicalDigest(manifest) };
  certification.webArtifactProvenance = { ref: provenance.provenanceRef, digest: canonicalDigest(provenance) };
  for (const field of ["siteReleaseCandidate", "launchProductProfile", "productSurfaceCatalog", "surfaceInventory", "webBuildIntent", "compiledWebManifest", "webArtifactProvenance"]) {
    revokedCertification[field] = structuredClone(certification[field]);
  }
  revocation.releaseCertification = { ref: revokedCertification.certificationRef, digest: canonicalDigest(revokedCertification) };
  revocation.siteReleaseCandidate = structuredClone(revokedCertification.siteReleaseCandidate);

  siteRelease.siteReleaseCandidate = structuredClone(intent.siteReleaseCandidate);
  siteRelease.launchProductProfile = structuredClone(intent.launchProductProfile);
  siteRelease.productSurfaceCatalog = structuredClone(intent.productSurfaceCatalog);
  siteRelease.surfaceInventory = structuredClone(intent.surfaceInventory);
  siteRelease.webBuildIntent = { ref: intent.intentRef, digest: canonicalDigest(intent) };
  siteRelease.compiledWebManifest = { ref: manifest.manifestRef, digest: canonicalDigest(manifest) };
  siteRelease.webArtifactProvenance = { ref: provenance.provenanceRef, digest: canonicalDigest(provenance) };
  siteRelease.releaseCertification = { ref: certification.certificationRef, digest: canonicalDigest(certification) };
  siteRelease.businessBindings = structuredClone(candidate.businessBindings);
  siteRelease.bootstrapBindings = {
    compiledWebManifest: structuredClone(siteRelease.compiledWebManifest),
    productSurfaceCatalog: structuredClone(siteRelease.productSurfaceCatalog),
    surfaceInventory: structuredClone(siteRelease.surfaceInventory),
    webCompositionRegistry: structuredClone(intent.webCompositionRegistry),
    webBuildToolchain: structuredClone(intent.webBuildToolchain),
  };

  for (const snapshot of [beginSnapshot, beforeCasSnapshot]) {
    snapshot.siteRelease = { ref: siteRelease.siteReleaseRef, digest: canonicalDigest(siteRelease) };
    snapshot.candidate.siteReleaseCandidate = structuredClone(siteRelease.siteReleaseCandidate);
    snapshot.candidate.authorizationEpoch = siteRelease.candidateAuthorizationEpoch;
    snapshot.certification.releaseCertification = structuredClone(siteRelease.releaseCertification);
    snapshot.certification.revocationEpoch = siteRelease.certificationRevocationEpoch;
    snapshot.certification.validUntil = certification.validUntil;
    snapshot.trust = structuredClone(certification.producer);
    snapshot.authorityMaterialDigest = canonicalDigest(authorityMaterial(snapshot));
  }
  activationEvidence.siteRelease = { ref: siteRelease.siteReleaseRef, digest: canonicalDigest(siteRelease) };
  activationEvidence.beginAuthoritySnapshot = { ref: beginSnapshot.snapshotRef, digest: canonicalDigest(beginSnapshot) };
  activationEvidence.immediateBeforePointerCasAuthoritySnapshot = { ref: beforeCasSnapshot.snapshotRef, digest: canonicalDigest(beforeCasSnapshot) };
  activationEvidence.eligibilityMaterialDigest = canonicalDigest(eligibilityMaterial(activationEvidence));

  for (const vector of corpus.canonicalVectors) {
    const document = corpus.positiveCases.find(({ id }) => id === vector.caseId).document;
    vector.expectedDigest = canonicalDigest(document);
  }
  for (const vector of corpus.dsseVectors) resignVector(corpus, vector.caseId, privateKeys.get(vector.caseId));
}

async function coherentCorpusAttack(mutate, expectedCode) {
  const source = await readFile(resolve(repositoryRoot, "contract/corpus/web-release-composition-v1.json"), "utf8");
  const corpus = JSON.parse(source);
  mutate(corpus);
  refreshCoherentChain(corpus);
  const temporary = await mkdtemp(join(tmpdir(), "kokoro-web-release-coherent-"));
  const corpusPath = join(temporary, "corpus.json");
  await writeFile(corpusPath, `${JSON.stringify(corpus, null, 2)}\n`);
  await expectCode(() => validateRepository({ root: repositoryRoot, corpus: corpusPath }), expectedCode);
}

async function expectCode(action, code) {
  await assert.rejects(action, (error) => {
    assert.equal(error instanceof WebReleaseContractError, true);
    assert.equal(error.code, code);
    return true;
  });
}

test("RFC 8785 canonicalization uses UTF-16 key order and stable JSON bytes", () => {
  const result = canonicalizeJsonText('{"\ud83d\ude00":"emoji","a":"é","z":"last"}');
  assert.equal(result, '{"a":"é","z":"last","😀":"emoji"}');
});

test("I-JSON profile rejects duplicate keys before parsing", () => {
  assert.throws(
    () => canonicalizeJsonText('{"intentRef":"first","intentRef":"second"}'),
    (error) => error instanceof WebReleaseContractError && error.code === "web_release_json_duplicate_key",
  );
});

test("I-JSON profile rejects non-NFC text, lone surrogates, and unsafe numbers", () => {
  for (const [source, code] of [
    ['{"value":"e\\u0301"}', "web_release_json_non_nfc"],
    ['{"value":"\\ud800"}', "web_release_json_lone_surrogate"],
    ['{"value":9007199254740992}', "web_release_json_number_unsafe"],
  ]) {
    assert.throws(
      () => canonicalizeJsonText(source),
      (error) => error instanceof WebReleaseContractError && error.code === code,
    );
  }
});

test("checked-in registry, release authority schemas, and golden corpus close the release chain", async () => {
  const result = await validateRepository({ root: repositoryRoot });
  assert.deepEqual(result, {
    contracts: 15,
    positiveCases: 17,
    negativeCases: 58,
    canonicalVectors: 17,
    dsseVectors: 5,
  });
});

test("persisted activation authority and eligibility contracts freeze exact JCS material", async () => {
  const readSchema = async (name) => JSON.parse(await readFile(resolve(repositoryRoot, `contract/spec/${name}.yaml`), "utf8"));
  const snapshot = await readSchema("activation-authority-snapshot");
  const evidence = await readSchema("activation-eligibility-evidence");

  for (const field of ["activationAttemptRef", "phase", "siteRelease", "candidate", "certification", "trust", "readAt", "authorityMaterialDigest"]) {
    assert.ok(snapshot.required.includes(field));
  }
  for (const field of ["activationAttemptRef", "siteRelease", "beginAuthoritySnapshot", "immediateBeforePointerCasAuthoritySnapshot", "decision", "evaluatedAt", "eligibilityMaterialDigest"]) {
    assert.ok(evidence.required.includes(field));
  }
  assert.deepEqual(snapshot.properties.phase.enum, ["activation-begin", "immediate-before-pointer-cas"]);
  assert.equal(snapshot.$defs.trustTuple.properties.keyStatus.const, "active");
});

test("certification and revocation carry the complete active trust tuple and signed authority facts", async () => {
  const certification = JSON.parse(await readFile(resolve(repositoryRoot, "contract/spec/release-certification-instance.yaml"), "utf8"));
  const revocation = JSON.parse(await readFile(resolve(repositoryRoot, "contract/spec/release-certification-revocation.yaml"), "utf8"));
  const tuple = ["producerRegistry", "producerRegistryEpoch", "producerIdentityRef", "trustPolicy", "trustPolicyEpoch", "keyId", "keyVersion", "publicKeyFingerprint", "keyStatus", "keyValidFrom", "keyValidUntil", "signatureAudience", "environment"];
  assert.deepEqual([...certification.$defs.producer.required].sort(), [...tuple].sort());
  assert.deepEqual([...revocation.$defs.producer.required].sort(), [...tuple].sort());
  assert.equal(certification.$defs.producer.properties.keyStatus.const, "active");
  assert.equal(revocation.$defs.producer.properties.keyStatus.const, "active");
  assert.ok(certification.required.includes("certificationRevocationEpoch"));
  assert.ok(revocation.required.includes("certificationRevocationEpoch"));
  assert.ok(revocation.$defs.dsseEnvelope);
});

test("catalog and Profile schemas expose mandatory scope and recursive journey closure", async () => {
  const catalog = JSON.parse(await readFile(resolve(repositoryRoot, "contract/spec/product-surface-catalog.yaml"), "utf8"));
  assert.ok(catalog.$defs.surface.required.includes("scopeClass"));
  assert.deepEqual(catalog.$defs.surface.properties.scopeClass.enum, ["core-always", "profile-selectable"]);
  assert.ok(catalog.$defs.journey.required.includes("requiredJourneyRefs"));
});

test("profile candidate inventory release chain is single-direction and activation-derived", async () => {
  const readSchema = async (name) => JSON.parse(await readFile(resolve(repositoryRoot, `contract/spec/${name}.yaml`), "utf8"));
  const profile = await readSchema("launch-product-profile");
  const candidate = await readSchema("site-release-candidate");
  const inventory = await readSchema("surface-inventory");
  const certification = await readSchema("release-certification-instance");
  const revocation = await readSchema("release-certification-revocation");
  const release = await readSchema("site-release");

  assert.equal("surfaceInventoryRevisionRef" in profile.properties, false);
  assert.equal("surfaceInventory" in profile.properties, false);
  assert.equal("surfaceInventory" in candidate.properties, false);
  assert.ok(profile.required.includes("enabledSurfaceRefs"));
  assert.ok(profile.required.includes("productSurfaceCatalog"));
  assert.ok(candidate.required.includes("launchProductProfile"));
  assert.ok(candidate.required.includes("productSurfaceCatalog"));
  for (const field of ["siteRef", "siteReleaseCandidate", "launchProductProfile", "productSurfaceCatalog", "enabledSurfaceRefs", "disabledSurfaceRefs"]) {
    assert.ok(inventory.required.includes(field));
  }
  assert.ok(certification.required.includes("candidateAuthorizationEpoch"));
  assert.ok(certification.required.includes("validUntil"));
  assert.ok(revocation.required.includes("releaseCertification"));
  assert.ok(release.required.includes("releaseCertification"));
  assert.ok(release.required.includes("webArtifactDigest"));
  assert.equal("enabledSurfaceRefs" in release.properties, false);
});

test("compiled manifest distinguishes BFF authority, opaque model roles, and exact bootstrap bindings", async () => {
  const registry = JSON.parse(await readFile(resolve(repositoryRoot, "contract/spec/web-composition-registry.yaml"), "utf8"));
  const intent = JSON.parse(await readFile(resolve(repositoryRoot, "contract/spec/web-build-intent.yaml"), "utf8"));
  const manifest = JSON.parse(await readFile(resolve(repositoryRoot, "contract/spec/compiled-web-manifest.yaml"), "utf8"));
  const release = JSON.parse(await readFile(resolve(repositoryRoot, "contract/spec/site-release.yaml"), "utf8"));
  const registryBff = registry.$defs.bffGroup;
  const manifestBff = manifest.$defs.bffGroup;
  for (const schema of [registryBff, manifestBff]) {
    assert.ok(schema.required.includes("operationFamilyRef"));
    assert.ok(schema.required.includes("sameOriginHandlerOperationIds"));
    assert.ok(schema.required.includes("downstreamOperationIds"));
    assert.equal("operationIds" in schema.properties, false);
  }
  assert.ok(intent.required.includes("modelRequirements"));
  assert.equal("requiredModelCatalogs" in intent.properties, false);
  assert.ok(intent.$defs.modelRequirement.required.includes("modelRoleRef"));
  assert.ok(intent.$defs.modelRequirement.required.includes("modelInventory"));
  assert.ok(intent.$defs.modelRequirement.required.includes("modelCatalog"));
  assert.equal("enum" in intent.$defs.modelRequirement.properties.modelRoleRef, false);
  assert.ok(release.required.includes("bootstrapBindings"));
  for (const field of ["compiledWebManifest", "productSurfaceCatalog", "surfaceInventory", "webCompositionRegistry", "webBuildToolchain"]) {
    assert.ok(release.$defs.bootstrapBindings.required.includes(field));
  }
});

test("activation eligibility independently revalidates persisted begin and immediate-before-CAS authority snapshots", async () => {
  const contractGate = await import("./check-web-release-composition.mjs");
  assert.equal(typeof contractGate.assertActivationEvidenceEligible, "function");
  const corpus = JSON.parse(await readFile(resolve(repositoryRoot, "contract/corpus/web-release-composition-v1.json"), "utf8"));
  const cases = new Map(corpus.positiveCases.map(({ id, document }) => [id, document]));
  const scenario = corpus.activationEligibilityScenarios[0];
  assert.doesNotThrow(() => contractGate.assertActivationEvidenceEligible(
    cases.get(scenario.evidenceCaseId),
    cases.get(scenario.beginSnapshotCaseId),
    cases.get(scenario.immediateBeforePointerCasSnapshotCaseId),
    cases.get("site-release-alpha"),
    cases.get("certification-site-alpha"),
  ));
  assert.deepEqual(scenario.blockedImmediateBeforePointerCasReads.map(({ expectedCode }) => expectedCode), [
    "web_release_activation_certification_revoked",
    "web_release_activation_certification_expired",
  ]);
});

test("BFF same-origin and downstream operation identities are globally disjoint across groups", async () => {
  await coherentCorpusAttack((corpus) => {
    const registry = corpus.positiveCases.find(({ contractId }) => contractId === "web-composition-registry.v1").document;
    const groups = registry.units.flatMap(({ bffOperationGroups }) => bffOperationGroups);
    assert.ok(groups.length >= 2);
    groups[1].sameOriginHandlerOperationIds[0] = groups[0].downstreamOperationIds[0];
  }, "web_release_composition_registry_identity_invalid");
});

test("SiteRelease publication is ordered after certification generation and before expiry", async () => {
  await coherentCorpusAttack((corpus) => {
    const release = corpus.positiveCases.find(({ id }) => id === "site-release-alpha").document;
    const certification = corpus.positiveCases.find(({ id }) => id === "certification-site-alpha").document;
    release.publishedAt = certification.generatedAt.replace("35:00.000Z", "34:59.999Z");
  }, "web_release_site_release_certification_invalid");
});

test("semantic validation rejects an inventory that is not an exact catalog partition", async () => {
  const corpusPath = resolve(repositoryRoot, "contract/corpus/web-release-composition-v1.json");
  const corpus = JSON.parse(await readFile(corpusPath, "utf8"));
  const inventoryCase = corpus.positiveCases.find(({ contractId }) => contractId === "surface-inventory.v1");
  inventoryCase.document.disabledSurfaceRefs = [];
  const temporary = await mkdtemp(join(tmpdir(), "kokoro-web-release-corpus-"));
  const tamperedPath = join(temporary, "corpus.json");
  await writeFile(tamperedPath, `${JSON.stringify(corpus, null, 2)}\n`);
  await expectCode(
    () => validateRepository({ root: repositoryRoot, corpus: tamperedPath }),
    "web_release_inventory_partition_invalid",
  );
});

test("semantic validation rejects build intent ownership leaks and digest self-reference", async () => {
  const corpusPath = resolve(repositoryRoot, "contract/corpus/web-release-composition-v1.json");
  const corpus = JSON.parse(await readFile(corpusPath, "utf8"));
  const intentCase = corpus.positiveCases.find(({ contractId }) => contractId === "web-build-intent.v1");
  intentCase.document.unitRefs = ["web.surface.chat.v1"];
  intentCase.document.buildIntentDigest = `sha256:${"a".repeat(64)}`;
  const temporary = await mkdtemp(join(tmpdir(), "kokoro-web-release-intent-"));
  const tamperedPath = join(temporary, "corpus.json");
  await writeFile(tamperedPath, `${JSON.stringify(corpus, null, 2)}\n`);
  await expectCode(
    () => validateRepository({ root: repositoryRoot, corpus: tamperedPath }),
    "web_release_positive_schema_invalid",
  );
});

test("DSSE corpus validates the complete envelope shape, not only PAE bytes", async () => {
  const corpusPath = resolve(repositoryRoot, "contract/corpus/web-release-composition-v1.json");
  const corpus = JSON.parse(await readFile(corpusPath, "utf8"));
  corpus.dsseVectors[0].keyId = "https://untrusted.example/key";
  const temporary = await mkdtemp(join(tmpdir(), "kokoro-web-release-dsse-"));
  const tamperedPath = join(temporary, "corpus.json");
  await writeFile(tamperedPath, `${JSON.stringify(corpus, null, 2)}\n`);
  await expectCode(
    () => validateRepository({ root: repositoryRoot, corpus: tamperedPath }),
    "web_release_dsse_envelope_invalid",
  );
});

test("registry bootstrap enforces the approved business owner map", async () => {
  const registryPath = resolve(repositoryRoot, "contract/registry/web-release-composition.yaml");
  const registry = JSON.parse(await readFile(registryPath, "utf8"));
  registry.contracts.find(({ id }) => id === "product-surface-catalog.v1").businessOwner = "platform.site";
  const temporary = await mkdtemp(join(tmpdir(), "kokoro-web-release-registry-"));
  const tamperedPath = join(temporary, "registry.json");
  await writeFile(tamperedPath, `${JSON.stringify(registry, null, 2)}\n`);
  await expectCode(
    () => validateRepository({ root: repositoryRoot, registry: tamperedPath }),
    "web_release_registry_owner_invalid",
  );
});

test("manifest proves shell closure and rejects duplicate BFF authority", async () => {
  const corpusPath = resolve(repositoryRoot, "contract/corpus/web-release-composition-v1.json");
  const corpus = JSON.parse(await readFile(corpusPath, "utf8"));
  const manifestCase = corpus.positiveCases.find(({ contractId }) => contractId === "compiled-web-manifest.v1");
  manifestCase.document.bffOperationGroups.push({groupRef: "bff.duplicate", unitRef: "web.surface.chat", operationFamilyRef: "operation.chat", sameOriginHandlerOperationIds: ["siteCreateSession"], downstreamOperationIds: ["createSession"]});
  const temporary = await mkdtemp(join(tmpdir(), "kokoro-web-release-manifest-"));
  const tamperedPath = join(temporary, "corpus.json");
  await writeFile(tamperedPath, `${JSON.stringify(corpus, null, 2)}\n`);
  await expectCode(
    () => validateRepository({ root: repositoryRoot, corpus: tamperedPath }),
    "web_release_manifest_bff_conflict",
  );
});

test("provenance resolved dependencies cannot omit signed release material", async () => {
  const corpusPath = resolve(repositoryRoot, "contract/corpus/web-release-composition-v1.json");
  const corpus = JSON.parse(await readFile(corpusPath, "utf8"));
  const provenanceCase = corpus.positiveCases.find(({ contractId }) => contractId === "web-artifact-provenance-profile.v1");
  const intentCase = corpus.positiveCases.find(({ contractId }) => contractId === "web-build-intent.v1");
  provenanceCase.document.predicate.buildDefinition.resolvedDependencies = provenanceCase.document.predicate.buildDefinition.resolvedDependencies.filter(
    ({ uri }) => uri !== `kokoro:material-bundle/${intentCase.document.webBuildMaterialBundle.ref}`,
  );
  const temporary = await mkdtemp(join(tmpdir(), "kokoro-web-release-provenance-"));
  const tamperedPath = join(temporary, "corpus.json");
  await writeFile(tamperedPath, `${JSON.stringify(corpus, null, 2)}\n`);
  await expectCode(
    () => validateRepository({ root: repositoryRoot, corpus: tamperedPath }),
    "web_release_provenance_reference_invalid",
  );
});

test("v1 breaking gate freezes schema semantics and existing registry ownership", async () => {
  const registryPath = resolve(repositoryRoot, "contract/registry/web-release-composition.yaml");
  const registry = JSON.parse(await readFile(registryPath, "utf8"));
  const schemas = new Map();
  for (const entry of registry.contracts) {
    schemas.set(entry.id, JSON.parse(await readFile(resolve(repositoryRoot, entry.schemaPath), "utf8")));
  }
  assertFrozenV1Compatible({ registry, schemas }, { registry, schemas });

  const changedRegistry = structuredClone(registry);
  changedRegistry.contracts[0].businessOwner = "root.contract";
  assert.throws(
    () => assertFrozenV1Compatible({ registry, schemas }, { registry: changedRegistry, schemas }),
    (error) => error instanceof WebReleaseContractError && error.code === "web_release_v1_registry_breaking",
  );

  const changedSchemas = new Map(schemas);
  const first = structuredClone(changedSchemas.get(registry.contracts[0].id));
  first.required = first.required.filter((name) => name !== "catalogRevisionRef");
  changedSchemas.set(registry.contracts[0].id, first);
  assert.throws(
    () => assertFrozenV1Compatible({ registry, schemas }, { registry, schemas: changedSchemas }),
    (error) => error instanceof WebReleaseContractError && error.code === "web_release_v1_schema_breaking",
  );
});

test("coherent manifest cannot substitute a measured tool for the pre-frozen toolchain role", async () => {
  await coherentCorpusAttack((corpus) => {
    const manifest = corpus.positiveCases.find(({ contractId }) => contractId === "compiled-web-manifest.v1").document;
    manifest.measuredToolArtifacts.find(({ role }) => role === "compiler").digest = `sha256:${"9".repeat(64)}`;
  }, "web_release_manifest_toolchain_mismatch");
});

test("coherent provenance cannot change signed Site, candidate, or authorization epoch", async () => {
  await coherentCorpusAttack((corpus) => {
    const parameters = corpus.positiveCases.find(
      ({ contractId }) => contractId === "web-artifact-provenance-profile.v1",
    ).document.predicate.buildDefinition.externalParameters;
    parameters.siteRef = "site.evil";
    parameters.releaseCandidateRef = "release-candidate.evil.1";
    parameters.candidateAuthorizationEpoch = "999";
  }, "web_release_provenance_context_mismatch");
});

test("coherent provenance binds every resolved dependency URI to its exact digest role", async () => {
  await coherentCorpusAttack((corpus) => {
    const dependencies = corpus.positiveCases.find(
      ({ contractId }) => contractId === "web-artifact-provenance-profile.v1",
    ).document.predicate.buildDefinition.resolvedDependencies;
    const compiler = dependencies.find(({ uri }) => uri === "oci://registry.kokoro.dev/compiler/oci.kokoro.web-composition-compiler");
    const packageArtifact = dependencies.find(({ uri }) => uri === "pkg:npm/%40kokoro/chat-product@1.0.0?kokoro_package_ref=package.chat-product");
    [compiler.digest.sha256, packageArtifact.digest.sha256] = [packageArtifact.digest.sha256, compiler.digest.sha256];
  }, "web_release_provenance_dependency_mismatch");
});

test("coherent provenance rejects collisions between distinct measured tool roles", async () => {
  await coherentCorpusAttack((corpus) => {
    const documents = new Map(corpus.positiveCases.map(({ contractId, document }) => [contractId, document]));
    const toolchain = documents.get("web-build-toolchain.v1");
    const manifest = documents.get("compiled-web-manifest.v1");
    const provenance = documents.get("web-artifact-provenance-profile.v1");
    toolchain.inspectorArtifact.repositoryRef = toolchain.compilerArtifact.repositoryRef;
    manifest.measuredToolArtifacts.find(({ role }) => role === "inspector").repositoryRef = toolchain.compilerArtifact.repositoryRef;

    const dependencies = provenance.predicate.buildDefinition.resolvedDependencies;
    const compiler = dependencies.find(({ uri }) => uri.includes("web-composition-compiler"));
    const inspector = dependencies.find(({ uri }) => uri.includes("web-artifact-inspector"));
    inspector.uri = compiler.uri;
    dependencies.splice(dependencies.indexOf(compiler), 1);
  }, "web_release_provenance_reference_invalid");
});

test("coherent provenance rejects duplicate package name and version identities", async () => {
  await coherentCorpusAttack((corpus) => {
    const documents = new Map(corpus.positiveCases.map(({ contractId, document }) => [contractId, document]));
    const registry = documents.get("web-composition-registry.v1");
    const manifest = documents.get("compiled-web-manifest.v1");
    const provenance = documents.get("web-artifact-provenance-profile.v1");
    const aliasDigest = `sha256:${"b6".repeat(32)}`;
    registry.packages.push({
      packageRef: "package.chat-product-alias",
      name: "@kokoro/chat-product",
      version: "1.0.0",
      digest: aliasDigest,
    });
    registry.units.find(({ unitRef }) => unitRef === "web.surface.chat").packageRefs.push("package.chat-product-alias");
    manifest.packages.push({
      packageRef: "package.chat-product-alias",
      name: "@kokoro/chat-product",
      version: "1.0.0",
      digest: aliasDigest,
      unitRefs: ["web.surface.chat"],
    });
    manifest.units.find(({ unitRef }) => unitRef === "web.surface.chat").packageRefs.push("package.chat-product-alias");
    provenance.predicate.buildDefinition.resolvedDependencies.find(
      ({ uri }) => uri.includes("chat-product@1.0.0"),
    ).digest.sha256 = aliasDigest.slice("sha256:".length);
  }, "web_release_composition_registry_identity_invalid");
});

test("coherent manifest must be the exact registry projection with no missing BFF or model closure", async () => {
  await coherentCorpusAttack((corpus) => {
    const manifest = corpus.positiveCases.find(({ contractId }) => contractId === "compiled-web-manifest.v1").document;
    manifest.bffOperationGroups = [];
    manifest.modelCatalogRequirements = [];
  }, "web_release_manifest_registry_projection_invalid");
});

test("coherent manifest rejects pathname collisions even when page method arrays are empty", async () => {
  await coherentCorpusAttack((corpus) => {
    const manifest = corpus.positiveCases.find(({ contractId }) => contractId === "compiled-web-manifest.v1").document;
    manifest.routes[0].pathname = "/collision";
    manifest.routes[0].methods = [];
    manifest.routes[1].pathname = "/collision";
    manifest.routes[1].methods = [];
  }, "web_release_manifest_route_conflict");
});

test("coherent material rejects duplicate public config identities and a non-canonical origin", async () => {
  await coherentCorpusAttack((corpus) => {
    const material = corpus.positiveCases.find(
      ({ contractId }) => contractId === "web-build-material-bundle.v1",
    ).document;
    material.publicRuntimeConfig.push(structuredClone(material.publicRuntimeConfig[0]));
  }, "web_release_material_identity_invalid");

  await coherentCorpusAttack((corpus) => {
    const material = corpus.positiveCases.find(
      ({ contractId }) => contractId === "web-build-material-bundle.v1",
    ).document;
    material.domainPolicy.canonicalHttpsOrigin = "https://other.example.com";
  }, "web_release_material_origin_invalid");
});

test("coherent catalog enforces exact surface ownership, dependency DAGs, and published Profile input", async () => {
  await coherentCorpusAttack((corpus) => {
    const catalog = corpus.positiveCases.find(({ contractId }) => contractId === "product-surface-catalog.v1").document;
    catalog.products.find(({ productRef }) => productRef === "product.memory").surfaceRefs.push("surface.chat");
  }, "web_release_catalog_ownership_invalid");

  await coherentCorpusAttack((corpus) => {
    const catalog = corpus.positiveCases.find(({ contractId }) => contractId === "product-surface-catalog.v1").document;
    catalog.surfaces.find(({ surfaceRef }) => surfaceRef === "surface.chat").requiredSurfaceRefs = ["surface.memory"];
    catalog.surfaces.find(({ surfaceRef }) => surfaceRef === "surface.memory").requiredSurfaceRefs = ["surface.chat"];
  }, "web_release_catalog_cycle");

  await coherentCorpusAttack((corpus) => {
    const catalog = corpus.positiveCases.find(({ contractId }) => contractId === "product-surface-catalog.v1").document;
    catalog.state = "draft";
    catalog.publishedAt = null;
  }, "web_release_profile_reference_invalid");
});

test("DSSE key ids bind intent, provenance, certification, and revocation identities", async () => {
  const corpus = JSON.parse(
    await readFile(resolve(repositoryRoot, "contract/corpus/web-release-composition-v1.json"), "utf8"),
  );
  const cases = new Map(corpus.positiveCases.map(({ id, document }) => [id, document]));
  for (const vector of corpus.dsseVectors) {
    const document = cases.get(vector.caseId);
    const contractCase = corpus.positiveCases.find(({ id }) => id === vector.caseId);
    const expected = contractCase.contractId === "web-build-intent.v1"
      ? document.issuer.signingKeyId
      : ["release-certification-instance.v1", "release-certification-revocation.v1"].includes(contractCase.contractId)
        ? document.producer.keyId
        : document.predicate.runDetails.builder.kokoro_signingKeyId;
    assert.equal(vector.keyId, expected);
  }

  corpus.dsseVectors.find(({ caseId }) => caseId === "intent-site-alpha").keyId = "key.web-build-intent.4";
  const temporary = await mkdtemp(join(tmpdir(), "kokoro-web-release-dsse-identity-"));
  const corpusPath = join(temporary, "corpus.json");
  await writeFile(corpusPath, `${JSON.stringify(corpus, null, 2)}\n`);
  await expectCode(
    () => validateRepository({ root: repositoryRoot, corpus: corpusPath }),
    "web_release_dsse_keyid_mismatch",
  );
});

test("SLSA v1 byproducts use ResourceDescriptor digest maps", async () => {
  const corpus = JSON.parse(
    await readFile(resolve(repositoryRoot, "contract/corpus/web-release-composition-v1.json"), "utf8"),
  );
  const provenance = corpus.positiveCases.find(
    ({ contractId }) => contractId === "web-artifact-provenance-profile.v1",
  ).document;
  for (const byproduct of provenance.predicate.runDetails.byproducts) {
    assert.deepEqual(Object.keys(byproduct.digest), ["sha256"]);
    assert.match(byproduct.digest.sha256, /^[0-9a-f]{64}$/u);
  }
});

test("SLSA resources require global dependency URIs and strict byproduct descriptors", async () => {
  const source = await readFile(resolve(repositoryRoot, "contract/corpus/web-release-composition-v1.json"), "utf8");
  const corpus = JSON.parse(source);
  const provenance = corpus.positiveCases.find(
    ({ contractId }) => contractId === "web-artifact-provenance-profile.v1",
  ).document;
  for (const dependency of provenance.predicate.buildDefinition.resolvedDependencies) {
    assert.doesNotThrow(() => new URL(dependency.uri));
    assert.match(dependency.uri, /^[a-z][a-z0-9+.-]*:/u);
  }

  provenance.predicate.buildDefinition.resolvedDependencies[0].uri = "package.chat-product";
  const dependencyTemporary = await mkdtemp(join(tmpdir(), "kokoro-web-release-relative-dependency-"));
  const dependencyCorpusPath = join(dependencyTemporary, "corpus.json");
  await writeFile(dependencyCorpusPath, `${JSON.stringify(corpus, null, 2)}\n`);
  await expectCode(
    () => validateRepository({ root: repositoryRoot, corpus: dependencyCorpusPath }),
    "web_release_positive_schema_invalid",
  );

  const byproductCorpus = JSON.parse(source);
  const byproduct = byproductCorpus.positiveCases.find(
    ({ contractId }) => contractId === "web-artifact-provenance-profile.v1",
  ).document.predicate.runDetails.byproducts[0];
  byproduct.digest = `sha256:${"c".repeat(64)}`;
  const byproductTemporary = await mkdtemp(join(tmpdir(), "kokoro-web-release-byproduct-shape-"));
  const byproductCorpusPath = join(byproductTemporary, "corpus.json");
  await writeFile(byproductCorpusPath, `${JSON.stringify(byproductCorpus, null, 2)}\n`);
  await expectCode(
    () => validateRepository({ root: repositoryRoot, corpus: byproductCorpusPath }),
    "web_release_positive_schema_invalid",
  );
});

test("canonical and DSSE vectors uniquely and exactly cover their contract cases", async () => {
  const source = await readFile(resolve(repositoryRoot, "contract/corpus/web-release-composition-v1.json"), "utf8");
  for (const [mutate, expectedCode] of [
    [(corpus) => { corpus.canonicalVectors[1].id = corpus.canonicalVectors[0].id; }, "web_release_canonical_coverage_invalid"],
    [(corpus) => { corpus.canonicalVectors[1].caseId = corpus.canonicalVectors[0].caseId; }, "web_release_canonical_coverage_invalid"],
    [(corpus) => { corpus.dsseVectors[1].id = corpus.dsseVectors[0].id; }, "web_release_dsse_coverage_invalid"],
    [(corpus) => { corpus.dsseVectors[1].caseId = corpus.dsseVectors[0].caseId; }, "web_release_dsse_coverage_invalid"],
  ]) {
    const corpus = JSON.parse(source);
    mutate(corpus);
    const temporary = await mkdtemp(join(tmpdir(), "kokoro-web-release-vector-coverage-"));
    const corpusPath = join(temporary, "corpus.json");
    await writeFile(corpusPath, `${JSON.stringify(corpus, null, 2)}\n`);
    await expectCode(() => validateRepository({ root: repositoryRoot, corpus: corpusPath }), expectedCode);
  }
});

test("breaking comparison loads the real seven-contract predecessor before reporting schema drift", async () => {
  await assert.rejects(
    () => execFileAsync(process.execPath, [
      resolve(repositoryRoot, "scripts/contract/check-web-release-composition.mjs"),
      "--root", repositoryRoot,
      "--breaking-against", "97f9c1e",
    ], { cwd: repositoryRoot }),
    ({ stderr }) => stderr.includes("web_release_v1_schema_breaking") || stderr.includes("web_release_registry_contract_set_invalid"),
  );
});

test("breaking comparison accepts a fourteen-contract baseline when the fifteenth contract is purely additive", async () => {
  const temporary = await mkdtemp(join(tmpdir(), "kokoro-web-release-additive-baseline-"));
  await mkdir(join(temporary, "contract"), { recursive: true });
  await cp(resolve(repositoryRoot, "contract/registry"), join(temporary, "contract/registry"), { recursive: true });
  await cp(resolve(repositoryRoot, "contract/spec"), join(temporary, "contract/spec"), { recursive: true });
  await cp(resolve(repositoryRoot, "contract/corpus"), join(temporary, "contract/corpus"), { recursive: true });
  const registryPath = join(temporary, "contract/registry/web-release-composition.yaml");
  const candidateRegistry = await readFile(registryPath, "utf8");
  const baselineRegistry = JSON.parse(candidateRegistry);
  baselineRegistry.contracts = baselineRegistry.contracts.filter(({ id }) => id !== "web-composition-registry.v1");
  await writeFile(registryPath, `${JSON.stringify(baselineRegistry, null, 2)}\n`);
  const git = (...args) => execFileAsync("git", args, { cwd: temporary });
  await git("init", "-q");
  await git("config", "user.name", "Kokoro Contract Test");
  await git("config", "user.email", "contract-test@kokoro.invalid");
  await git("add", "contract");
  await git("commit", "-qm", "seven-contract baseline");
  await writeFile(registryPath, candidateRegistry);
  await git("add", "contract/registry/web-release-composition.yaml");
  await git("commit", "-qm", "add composition registry contract");

  const { stdout } = await execFileAsync(process.execPath, [
    resolve(repositoryRoot, "scripts/contract/check-web-release-composition.mjs"),
    "--root", temporary,
    "--breaking-against", "HEAD^",
  ], { cwd: temporary });
  assert.match(stdout, /^web_release_contracts_ok:15 contracts,/u);
});

test("breaking comparison reads the candidate from HEAD instead of a spoofed worktree", async () => {
  const temporary = await mkdtemp(join(tmpdir(), "kokoro-web-release-git-candidate-"));
  await mkdir(join(temporary, "contract"), { recursive: true });
  await cp(resolve(repositoryRoot, "contract/registry"), join(temporary, "contract/registry"), { recursive: true });
  await cp(resolve(repositoryRoot, "contract/spec"), join(temporary, "contract/spec"), { recursive: true });
  await cp(resolve(repositoryRoot, "contract/corpus"), join(temporary, "contract/corpus"), { recursive: true });
  const git = (...args) => execFileAsync("git", args, { cwd: temporary });
  await git("init", "-q");
  await git("config", "user.name", "Kokoro Contract Test");
  await git("config", "user.email", "contract-test@kokoro.invalid");
  await git("add", "contract");
  await git("commit", "-qm", "baseline");

  const schemaPath = join(temporary, "contract/spec/product-surface-catalog.yaml");
  const baselineSchema = await readFile(schemaPath, "utf8");
  const changed = JSON.parse(baselineSchema);
  changed.title = "Breaking candidate title";
  await writeFile(schemaPath, `${JSON.stringify(changed, null, 2)}\n`);
  await git("add", "contract/spec/product-surface-catalog.yaml");
  await git("commit", "-qm", "breaking candidate");
  await writeFile(schemaPath, baselineSchema);

  await assert.rejects(
    () => execFileAsync(process.execPath, [
      resolve(repositoryRoot, "scripts/contract/check-web-release-composition.mjs"),
      "--root", temporary,
      "--breaking-against", "HEAD^",
    ], { cwd: temporary }),
    ({ stderr }) => stderr.includes("web_release_v1_schema_breaking"),
  );
});
