import assert from "node:assert/strict";
import { mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { resolve } from "node:path";
import { test } from "node:test";
import { generate } from "../../contract/generate.mjs";

const protoPath = new URL("../../contract/proto/kokoro/platform/model/v1/model_control.proto", import.meta.url);
const browserRecoveryPath = new URL("../../contract/spec/model-control-browser-recovery.yaml", import.meta.url);
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
    "ListModelOptions", "ListSiteModelPolicies", "ListSiteReleaseCatalogs", "GetCommandReceipt",
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

test("ModelControl bounds persisted integers to PostgreSQL signed storage", async () => {
  const proto = await readFile(protoPath, "utf8");
  for (const field of [
    "epoch", "expected_pointer_revision", "activated_revision", "expected_revision",
    "active_pointer_revision", "availability_epoch", "revision",
  ]) {
    const declarations = [...proto.matchAll(new RegExp(
      `(?:optional )?uint64 ${field} = \\d+ \\[\\(buf\\.validate\\.field\\)\\.uint64\\.lte = 9223372036854775807\\];`,
      "gu",
    ))];
    assert.ok(declarations.length > 0, `${field} must fit PostgreSQL BIGINT`);
  }
  for (const field of ["context_window", "providers", "models", "bindings", "product_routes"]) {
    assert.match(proto, new RegExp(
      `(?:optional )?uint32 ${field} = \\d+ \\[\\(buf\\.validate\\.field\\)\\.uint32[\\s\\S]*?lte: (?:2147483647|256|2048|4096)`,
      "u",
    ), `${field} must fit PostgreSQL INTEGER`);
  }
});

test("ModelControl exposes a typed command receipt reconciliation result", async () => {
  const [proto, registry] = await Promise.all([readFile(protoPath, "utf8"), readFile(registryPath, "utf8")]);
  const request = proto.match(/message GetCommandReceiptRequest \{[\s\S]*?\n\}/u)?.[0] ?? "";
  assert.match(request, /AuthenticatedOperatorQueryContext/u);
  assert.match(request, /string command_id/u);
  assert.match(request, /len: 36/u);
  assert.match(request, /\^\[0-9a-f\]\{8\}-\[0-9a-f\]\{4\}-4\[0-9a-f\]\{3\}-\[89ab\]\[0-9a-f\]\{3\}-\[0-9a-f\]\{12\}\$/u,
    "receipt reconciliation accepts only the canonical lowercase UUID v4 command identity");
  assert.match(request, /ModelControlCommandOperation operation/u);
  assert.match(request, /CommandDigestAlgorithmV2 digest_algorithm/u);
  assert.match(request, /string request_digest/u);
  const response = proto.match(/message GetCommandReceiptResponse \{[\s\S]*?\n\}/u)?.[0] ?? "";
  assert.match(response, /CommandReceiptV2 receipt/u);
  assert.match(response, /oneof result/u);
  assert.match(response, /option \(buf\.validate\.oneof\)\.required = true/u,
    "a reconciled receipt without its typed result must fail closed");
  for (const result of [
    "import_inventory", "activate_inventory", "change_site_policy", "materialize_model_options",
    "publish_site_release_catalog",
  ]) assert.match(proto, new RegExp(`\\b${result} =`, "u"));
  for (const operation of ["ImportInventory", "ActivateInventory", "ChangeSitePolicy",
    "MaterializeModelOptions", "PublishSiteReleaseCatalog"]) {
    assert.match(registry, new RegExp(`"id": "${operation}"[^\\n]*"recoveryOperation": "GetCommandReceipt"[^\\n]*"retryClass": "reconcile_receipt"`, "u"));
  }
});

test("ModelControl browser recovery is prepare-before-effect and owner-evidence unlocked", async () => {
  const recovery = JSON.parse(await readFile(browserRecoveryPath, "utf8"));
  assert.equal(recovery.schemaVersion, 1);
  assert.equal(recovery.protocol, "stateless-prepare-execute-reconcile");
  assert.deepEqual(recovery.prepare, {
    validatesCommand: true,
    executesEffect: false,
    returns: ["recoveryRef"],
  });
  assert.deepEqual(recovery.browser, {
    persistRecoveryRefBeforeExecute: true,
    persistCommandBody: false,
    maximumPendingCommands: 1,
  });
  assert.deepEqual(recovery.execute, {
    requires: ["recoveryRef", "command"],
    revalidatesAuthority: true,
    recomputesDigestAlgorithm: "SHA256_COMMAND_ENVELOPE",
    requiresExactOperationSiteDigestMatch: true,
    usesPreparedCommandId: true,
  });
  assert.deepEqual(recovery.recoveryReference.fieldsInCanonicalOrder, [
    "version", "commandId", "operation", "digestAlgorithm", "requestDigest", "siteId",
  ]);
  assert.equal(recovery.recoveryReference.maximumEncodedLength, 1024);
  assert.equal(recovery.recoveryReference.maximumDecodedBytes, 768);
  assert.equal(recovery.recoveryReference.commandIdFormat, "lowercase-uuid-v4");
  assert.equal(recovery.recoveryReference.digestAlgorithm, "SHA256_COMMAND_ENVELOPE");
  assert.deepEqual(recovery.reconcile, {
    queryAcceptsOnly: ["recoveryRef"],
    authoritativeOwner: "kokoro-platform",
    result: "typed-committed-command-receipt",
  });
  assert.deepEqual(recovery.unlock.retainPendingOn,
    ["not_found", "timeout", "invalid_recovery", "response_loss"]);
  assert.equal(recovery.unlock.onlyAfter, "authoritative-committed-receipt");
  assert.equal(recovery.unlock.operatorConfirmationCanUnlock, false);
  assert.equal(recovery.unlock.newCommandWhilePending, false);
  assert.deepEqual(recovery.operations.global,
    ["import_inventory", "activate_inventory", "materialize_options"]);
  assert.deepEqual(recovery.operations.site,
    ["change_site_policy", "publish_site_release_catalog"]);
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

test("ModelControl generates one provider-consumer error classification contract", async () => {
  const output = await mkdtemp(resolve(tmpdir(), "kokoro-model-errors-"));
  try {
    await generate({ boundary: "platform-model-control@v1", output });
    const source = await readFile(resolve(output, "model-control-errors.ts"), "utf8").catch(() => "");
    for (const value of [
      "inventoryRevisionNotFound", "model.inventory.not_found", "not_found", "404",
      "commandReceiptConflict", "model.command_receipt_conflict", "already_exists", "409",
      "adminPageTokenInvalid", "model.admin_page_token.invalid", "invalid_argument", "400",
      "adminSessionUnauthenticated", "admin.session.unauthenticated", "unauthenticated", "401",
      "adminPermissionDenied", "admin.permission_denied", "permission_denied", "403",
      "commandReceiptNotFound", "model.command_receipt.not_found",
      "commandReceiptMismatch", "model.command_receipt.mismatch",
    ]) assert.match(source, new RegExp(value, "u"));
    assert.match(source, /export function modelControlAdminErrorDetail/u);
    assert.doesNotMatch(source, /\? value : "model-control"/u);
  } finally {
    await rm(output, { recursive: true, force: true });
  }
});
