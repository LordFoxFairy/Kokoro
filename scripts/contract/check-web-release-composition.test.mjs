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

function resignVector(corpus, caseId) {
  const vector = corpus.dsseVectors.find((candidate) => candidate.caseId === caseId);
  const document = corpus.positiveCases.find((candidate) => candidate.id === caseId).document;
  const payload = canonicalBytes(document);
  const pae = dssePae(vector.payloadType, payload);
  const { publicKey, privateKey } = generateKeyPairSync("ed25519");
  vector.expectedPaeSha256 = createHash("sha256").update(pae).digest("hex");
  vector.publicKeySpkiDerBase64 = publicKey.export({ format: "der", type: "spki" }).toString("base64");
  vector.signatureBase64 = sign(null, pae, privateKey).toString("base64");
}

function refreshCoherentChain(corpus) {
  const documents = new Map(corpus.positiveCases.map(({ contractId, document }) => [contractId, document]));
  const catalog = documents.get("product-surface-catalog.v1");
  const inventory = documents.get("surface-inventory.v1");
  const material = documents.get("web-build-material-bundle.v1");
  const toolchain = documents.get("web-build-toolchain.v1");
  const registry = documents.get("web-composition-registry.v1");
  const intent = documents.get("web-build-intent.v1");
  const manifest = documents.get("compiled-web-manifest.v1");
  const provenance = documents.get("web-artifact-provenance-profile.v1");

  inventory.catalog.digest = canonicalDigest(catalog);
  intent.productSurfaceCatalog.digest = canonicalDigest(catalog);
  intent.surfaceInventory.digest = canonicalDigest(inventory);
  intent.webBuildMaterialBundle.digest = canonicalDigest(material);
  intent.webBuildToolchain.digest = canonicalDigest(toolchain);
  intent.webCompositionRegistry.digest = canonicalDigest(registry);
  manifest.buildIntentDigest = canonicalDigest(intent);
  manifest.catalog = structuredClone(intent.productSurfaceCatalog);
  manifest.surfaceInventory = structuredClone(intent.surfaceInventory);
  manifest.registry = structuredClone(intent.webCompositionRegistry);
  manifest.toolchain = structuredClone(intent.webBuildToolchain);

  const parameters = provenance.predicate.buildDefinition.externalParameters;
  parameters.buildIntentDigest = canonicalDigest(intent);
  parameters.compiledWebManifestDigest = canonicalDigest(manifest);
  parameters.toolchain.digest = canonicalDigest(toolchain);
  const materialDependency = provenance.predicate.buildDefinition.resolvedDependencies.find(
    ({ uri }) => uri === intent.webBuildMaterialBundle.ref,
  );
  if (materialDependency !== undefined) materialDependency.digest.sha256 = canonicalDigest(material).slice("sha256:".length);

  for (const vector of corpus.canonicalVectors) {
    const document = corpus.positiveCases.find(({ id }) => id === vector.caseId).document;
    vector.expectedDigest = canonicalDigest(document);
  }
  resignVector(corpus, "intent-site-alpha");
  resignVector(corpus, "provenance-site-alpha");
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

test("checked-in registry, eight schemas, and golden corpus close the release chain", async () => {
  const result = await validateRepository({ root: repositoryRoot });
  assert.deepEqual(result, {
    contracts: 8,
    positiveCases: 8,
    negativeCases: 30,
    canonicalVectors: 8,
    dsseVectors: 2,
  });
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
  manifestCase.document.bffOperationGroups.push({groupRef: "bff.duplicate", unitRef: "web.surface.chat", operationIds: ["createSession"]});
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
    ({ uri }) => uri !== intentCase.document.webBuildMaterialBundle.ref,
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
    const compiler = dependencies.find(({ uri }) => uri === "oci.kokoro.web-composition-compiler");
    const packageArtifact = dependencies.find(({ uri }) => uri === "package.chat-product");
    [compiler.digest.sha256, packageArtifact.digest.sha256] = [packageArtifact.digest.sha256, compiler.digest.sha256];
  }, "web_release_provenance_dependency_mismatch");
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

test("coherent catalog enforces exact surface ownership, dependency DAGs, and published build input", async () => {
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
  }, "web_release_intent_unpublished_input");
});

test("DSSE key ids bind the intent issuer and provenance attestor identities", async () => {
  const corpus = JSON.parse(
    await readFile(resolve(repositoryRoot, "contract/corpus/web-release-composition-v1.json"), "utf8"),
  );
  const cases = new Map(corpus.positiveCases.map(({ id, document }) => [id, document]));
  for (const vector of corpus.dsseVectors) {
    const document = cases.get(vector.caseId);
    const expected = vector.caseId === "intent-site-alpha"
      ? document.issuer.signingKeyId
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
