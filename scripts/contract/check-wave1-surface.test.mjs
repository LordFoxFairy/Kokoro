import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { copyFile, cp, mkdir, mkdtemp, readFile, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

const here = dirname(fileURLToPath(import.meta.url));
const root = resolve(here, "../..");
const checker = resolve(here, "check-wave1-surface.mjs");

async function makeFixture() {
  const fixture = await mkdtemp(resolve(tmpdir(), "kokoro-wave1-surface-"));
  await mkdir(resolve(fixture, "contract/openapi"), { recursive: true });
  await mkdir(resolve(fixture, "contract/registry"), { recursive: true });
  await cp(resolve(root, "contract/proto"), resolve(fixture, "contract/proto"), { recursive: true });
  await copyFile(resolve(root, "contract/buf.yaml"), resolve(fixture, "contract/buf.yaml"));
  await copyFile(resolve(root, "contract/buf.lock"), resolve(fixture, "contract/buf.lock"));
  await copyFile(
    resolve(root, "contract/openapi/platform-public-v1.yaml"),
    resolve(fixture, "contract/openapi/platform-public-v1.yaml"),
  );
  await copyFile(
    resolve(root, "contract/registry/boundaries.yaml"),
    resolve(fixture, "contract/registry/boundaries.yaml"),
  );
  await copyFile(resolve(root, "contract/generate.mjs"), resolve(fixture, "contract/generate.mjs"));
  return fixture;
}

test("the shipped Wave 1 surface is closed and internally consistent", () => {
  const result = spawnSync(process.execPath, [checker, "--root", root], { encoding: "utf8" });

  assert.equal(result.status, 0, result.stderr);
  assert.equal(
    result.stdout,
    "wave1_surface_ok: 53 public operations, 4 privileged services, 1 active command boundary\n",
  );
});

test("the live command checks the Wave 1 surface from the current working directory", () => {
  const result = spawnSync(process.execPath, [checker], { cwd: root, encoding: "utf8" });

  assert.equal(result.status, 0, result.stderr);
  assert.equal(
    result.stdout,
    "wave1_surface_ok: 53 public operations, 4 privileged services, 1 active command boundary\n",
  );
});

test("an Artifact delivery bearer cannot become an idempotent replay response", async () => {
  const fixture = await makeFixture();
  const openapi = resolve(fixture, "contract/openapi/platform-public-v1.yaml");
  const source = await readFile(openapi, "utf8");
  const operationStart = source.indexOf("      operationId: issueArtifactDeliveryAuthorization");
  const operationEnd = source.indexOf("  /v1/projects/{projectRef}/artifact-delivery-authorizations/", operationStart);
  assert.notEqual(operationStart, -1);
  assert.notEqual(operationEnd, -1);
  const operation = source.slice(operationStart, operationEnd).replace(
    "        - $ref: '#/components/parameters/ContractVersion'\n        - $ref: '#/components/parameters/CsrfToken'",
    "        - $ref: '#/components/parameters/ContractVersion'\n        - $ref: '#/components/parameters/IdempotencyKey'\n        - $ref: '#/components/parameters/CsrfToken'",
  );
  await writeFile(openapi, source.slice(0, operationStart) + operation + source.slice(operationEnd));

  const result = spawnSync(process.execPath, [checker, "--root", fixture], { encoding: "utf8" });
  assert.equal(result.status, 1);
  assert.match(result.stderr, /public_ephemeral_credential_replay_policy_drift:issueArtifactDeliveryAuthorization/u);
});

test("the checker fails closed when invoked outside a Wave 1 contract root", () => {
  const result = spawnSync(process.execPath, [checker, "--root", here], { encoding: "utf8" });

  assert.equal(result.status, 1);
  assert.match(result.stderr, /^wave1_surface_failed:/u);
});

test("an operation cannot erase workload security with an empty override", async () => {
  const fixture = await makeFixture();
  const openapi = resolve(fixture, "contract/openapi/platform-public-v1.yaml");
  const source = await readFile(openapi, "utf8");
  await writeFile(
    openapi,
    source.replace(
      "      operationId: beginRegistration\n",
      "      operationId: beginRegistration\n      security: []\n",
    ),
  );

  const result = spawnSync(process.execPath, [checker, "--root", fixture], { encoding: "utf8" });

  assert.equal(result.status, 1, result.stdout);
  assert.match(result.stderr, /public_operation_security_missing:beginRegistration/u);
});

test("the Session grant cannot drop a revocation axis or widen uint64 strings", async () => {
  const fixture = await makeFixture();
  const openapi = resolve(fixture, "contract/openapi/platform-public-v1.yaml");
  const source = await readFile(openapi, "utf8");
  await writeFile(
    openapi,
    source
      .replace("        - credentialEpoch\n", "")
      .replace("      x-kokoro-maximum: '18446744073709551615'\n", "")
      .replace("        - $ref: '#/components/schemas/SessionGrantRunResource'\n", "")
      .replace("          pattern: '^[A-Za-z0-9_-]+\\.[A-Za-z0-9_-]+\\.[A-Za-z0-9_-]+$'\n", ""),
  );

  const result = spawnSync(process.execPath, [checker, "--root", fixture], { encoding: "utf8" });

  assert.equal(result.status, 1, result.stdout);
  assert.match(result.stderr, /session_access_grant_axis_missing:credentialEpoch/u);
  assert.match(result.stderr, /positive_uint64_contract_drift/u);
  assert.match(result.stderr, /session_access_grant_resource_binding_drift/u);
  assert.match(result.stderr, /session_access_grant_credential_shape_drift/u);
});

test("a published Site release must carry a safe default model option per surface", async () => {
  const fixture = await makeFixture();
  const openapi = resolve(fixture, "contract/openapi/platform-public-v1.yaml");
  const source = await readFile(openapi, "utf8");
  await writeFile(
    openapi,
    source
      .replace("        - modelOptionCatalogs\n", "")
      .replace("        - defaultModelOptionRevisionRef\n", "")
      .replace("        availability:\n", "        providerRef:\n          type: string\n        availability:\n"),
  );

  const result = spawnSync(process.execPath, [checker, "--root", fixture], { encoding: "utf8" });

  assert.equal(result.status, 1, result.stdout);
  assert.match(result.stderr, /product_context_axis_missing:modelOptionCatalogs/u);
  assert.match(result.stderr, /model_option_catalog_field_missing:defaultModelOptionRevisionRef/u);
  assert.match(result.stderr, /model_option_catalog_leaks_internal:providerRef/u);
});

test("Asset owner reads cannot drop project authority, no-store, or eligibility axes", async () => {
  const fixture = await makeFixture();
  const openapi = resolve(fixture, "contract/openapi/platform-public-v1.yaml");
  const source = await readFile(openapi, "utf8");
  await writeFile(
    openapi,
    source
      .replace(
        "  /v1/projects/{projectRef}/asset-upload-intents/{intentRef}:\n",
        "  /v1/asset-upload-intents/{intentRef}:\n",
      )
      .replace(
        "    AssetUploadStatusResponse:\n      description: The current owner-visible upload, validation, scan, and promotion state.\n      headers:\n        <<: *standardResponseHeaders\n        Cache-Control:\n          required: true\n          schema:\n            type: string\n            const: no-store\n",
        "    AssetUploadStatusResponse:\n      description: The current owner-visible upload, validation, scan, and promotion state.\n      headers: *standardResponseHeaders\n",
      )
      .replace("        - eligibilityEpoch\n        - detectedMediaType\n", "        - detectedMediaType\n"),
  );

  const result = spawnSync(process.execPath, [checker, "--root", fixture], { encoding: "utf8" });

  assert.equal(result.status, 1, result.stdout);
  assert.match(result.stderr, /asset_owner_authority_drift:getAssetUploadStatus/u);
  assert.match(result.stderr, /asset_response_cache_policy_drift:AssetUploadStatusResponse/u);
  assert.match(result.stderr, /trusted_asset_grant_axis_missing:eligibilityEpoch/u);
});

test("forbidden authority axes are found in quoted flow mappings after YAML parsing", async () => {
  const fixture = await makeFixture();
  const openapi = resolve(fixture, "contract/openapi/platform-public-v1.yaml");
  const source = await readFile(openapi, "utf8");
  await writeFile(
    openapi,
    `${source}\n# siteId: comments are not contract data\nx-structural-probe: {"siteId": "forbidden"}\n`,
  );

  const result = spawnSync(process.execPath, [checker, "--root", fixture], { encoding: "utf8" });

  assert.equal(result.status, 1, result.stdout);
  assert.match(result.stderr, /public_forbidden_surface:siteId/u);
});

test("comments containing forbidden-looking text do not change the parsed public surface", async () => {
  const fixture = await makeFixture();
  const openapi = resolve(fixture, "contract/openapi/platform-public-v1.yaml");
  const source = await readFile(openapi, "utf8");
  await writeFile(openapi, `${source}\n# siteId: /v1/payment /v1/redeem:apply\n`);

  const result = spawnSync(process.execPath, [checker, "--root", fixture], { encoding: "utf8" });

  assert.equal(result.status, 0, result.stderr);
});
