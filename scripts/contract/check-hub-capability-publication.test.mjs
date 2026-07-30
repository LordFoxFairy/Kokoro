import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const root = new URL("../../", import.meta.url);

test("Hub capability publication is typed, signed, projected, and Agent-only at runtime", async () => {
  const [proto, registry] = await Promise.all([
    readFile(new URL("contract/proto/kokoro/platform/capability/v1/capability_catalog.proto", root), "utf8"),
    readFile(new URL("contract/registry/boundaries.yaml", root), "utf8"),
  ]);

  assert.match(proto, /service HubCatalogService/u);
  assert.match(proto, /rpc FreezeCatalog\(/u);
  assert.match(proto, /service HubRuntimeService/u);
  assert.match(proto, /rpc ResolveMcpSecrets\(/u);
  assert.match(proto, /service CapabilityCatalogProjectionService/u);
  assert.match(proto, /rpc ProjectCatalog\(/u);
  assert.match(proto, /SIGNATURE_ALGORITHM_ED25519_SHA256_V1/u);
  assert.match(proto, /string site_release_ref/u);
  assert.match(proto, /string agent_catalog_ref/u);
  assert.match(proto, /string snapshot_digest/u);

  const parsed = JSON.parse(registry);
  const runtime = parsed.boundaries.find(({ id }) => id === "hub-runtime");
  assert.deepEqual(runtime.consumers, [{ boundary: "service.agent", repository: "kokoro-agent" }]);
  assert.equal(runtime.protocol, "connect-rpc");
  assert.deepEqual(runtime.operations.map(({ id }) => id), ["ResolveMcpSecrets"]);

  const authority = parsed.boundaries.find(({ id }) => id === "hub-capability-catalog");
  assert.equal(authority.provider.boundary, "platform.hub");
  assert.deepEqual(authority.operations.map(({ id }) => id), ["FreezeCatalog", "GetCatalogPublication"]);

  const projection = parsed.boundaries.find(({ id }) => id === "platform-capability-projection");
  assert.equal(projection.provider.boundary, "service.platform");
  assert.deepEqual(projection.operations.map(({ id }) => id), ["ProjectCatalog", "GetProjectionReceipt"]);
});
