import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const protoPath = new URL("../../contract/proto/kokoro/platform/model/v1/model_control.proto", import.meta.url);
const registryPath = new URL("../../contract/registry/boundaries.yaml", import.meta.url);

test("ModelControl publishes bounded typed Admin read projections without provider secret refs", async () => {
  const [proto, registryText] = await Promise.all([
    readFile(protoPath, "utf8"),
    readFile(registryPath, "utf8"),
  ]);
  for (const rpc of [
    "ListInventoryRevisions", "GetInventoryRevision", "ListInventoryProviders",
    "ListInventoryModels", "ListInventoryBindings", "ListInventoryProductRoutes",
    "ListModelOptions", "ListSiteModelPolicies", "ListSiteReleaseCatalogs",
  ]) {
    assert.match(proto, new RegExp(`rpc ${rpc}\\(`, "u"));
    assert.match(registryText, new RegExp(`"id": "${rpc}"`, "u"));
  }
  const provider = proto.match(
    /message AdminModelProvider \{[\s\S]*?\n\}\n\nmessage ListInventoryProvidersRequest/u,
  )?.[0] ?? "";
  assert.match(provider, /bool secret_reference_present/u);
  assert.doesNotMatch(provider, /string secret_ref/u);
  assert.match(proto, /message ModelAdminPage[\s\S]*uint32 page_size[\s\S]*optional string page_token/u);
  assert.match(proto, /google\.protobuf\.Timestamp as_of/u);
});
