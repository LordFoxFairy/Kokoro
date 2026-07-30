import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const protoPath = new URL("../../contract/proto/kokoro/platform/model/v1/model_control.proto", import.meta.url);
const registryPath = new URL("../../contract/registry/boundaries.yaml", import.meta.url);
const contractIndexPath = new URL("./INDEX.md", import.meta.url);

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

test("ModelControl bounds every repeated identifier and revision reference item", async () => {
  const proto = await readFile(protoPath, "utf8");
  const identifierFields = new Map([
    ["input_modalities", 3], ["output_modalities", 3], ["capabilities", 2],
    ["required_capabilities", 3], ["fallback_model_keys", 1], ["supported_efforts", 1], ["badges", 1],
  ]);
  for (const [field, expected] of identifierFields) {
    const blocks = [...proto.matchAll(new RegExp(
      `repeated string ${field} = \\d+ \\[\\(buf\\.validate\\.field\\)\\.repeated = \\{([\\s\\S]*?)\\n  \\}\\];`, "gu",
    ))].map((match) => match[1] ?? "");
    assert.equal(blocks.length, expected, `${field} declaration count`);
    for (const block of blocks) {
      assert.match(block, /unique: true/u, `${field} must reject duplicates`);
      assert.match(block, /items:[\s\S]*string:[\s\S]*min_len: 1[\s\S]*max_len: 128/u,
        `${field} must bound each identifier`);
    }
  }
  for (const field of ["option_revision_refs", "allowed_option_revision_refs"]) {
    const block = proto.match(new RegExp(
      `repeated string ${field} = \\d+ \\[\\(buf\\.validate\\.field\\)\\.repeated = \\{([\\s\\S]*?)\\n  \\}\\];`, "u",
    ))?.[1] ?? "";
    assert.match(block, /unique: true/u, `${field} must reject duplicates`);
    assert.match(block, /items:[\s\S]*string:[\s\S]*min_len: 3[\s\S]*max_len: 256/u,
      `${field} must bound each reference`);
  }
});

test("ModelControl documents one end-to-end Admin unary transport budget", async () => {
  const index = await readFile(contractIndexPath, "utf8");
  assert.match(index, /requests are limited to 16 MiB/u);
  assert.match(index, /responses to 8 MiB/u);
  assert.match(index, /above the former 64 KiB ceiling/u);
  assert.match(index, /HTTP 413 `request\.payload_too_large`/u);
  assert.match(index, /Buf Validate failures remain HTTP 400/u);
});
