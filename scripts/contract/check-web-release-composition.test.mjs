import assert from "node:assert/strict";
import { readFile, writeFile } from "node:fs/promises";
import { mkdtemp } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

import {
  WebReleaseContractError,
  assertFrozenV1Compatible,
  canonicalizeJsonText,
  validateRepository,
} from "./check-web-release-composition.mjs";

const here = dirname(fileURLToPath(import.meta.url));
const repositoryRoot = resolve(here, "../..");

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

test("checked-in registry, seven schemas, and golden corpus close the release chain", async () => {
  const result = await validateRepository({ root: repositoryRoot });
  assert.deepEqual(result, {
    contracts: 7,
    positiveCases: 7,
    negativeCases: 18,
    canonicalVectors: 7,
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
  provenanceCase.document.predicate.buildDefinition.resolvedDependencies = provenanceCase.document.predicate.buildDefinition.resolvedDependencies.filter(({ uri }) => uri !== "material.site-alpha");
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
