#!/usr/bin/env node

import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { isAbsolute, resolve } from "node:path";
import { pathToFileURL } from "node:url";
import { openApiOperations, readOpenApiDocument } from "./openapi-reader.mjs";

const PUBLIC_OPERATIONS = new Map([
  ["exchangeProductContext", ["post", "/v1/product-context:exchange"]],
  ["issueSessionAccessGrant", ["post", "/v1/session-access-grants"]],
  ["beginRegistration", ["post", "/v1/identity/registrations"]],
  ["completeEmailVerification", ["post", "/v1/identity/verifications/{id}:complete"]],
  ["resendEmailVerification", ["post", "/v1/identity/verifications:resend"]],
  ["createIdentitySession", ["post", "/v1/identity/sessions"]],
  ["completeSessionMfa", ["post", "/v1/identity/sessions/{id}:verify-mfa"]],
  ["refreshIdentitySession", ["post", "/v1/identity/sessions:refresh"]],
  ["listIdentitySessions", ["get", "/v1/identity/sessions"]],
  ["revokeIdentitySessions", ["post", "/v1/identity/sessions:revoke"]],
  ["beginPasswordReset", ["post", "/v1/identity/password-resets"]],
  ["completePasswordReset", ["post", "/v1/identity/password-resets/{id}:complete"]],
  ["changePassword", ["post", "/v1/identity/password:change"]],
  ["beginEmailChange", ["post", "/v1/identity/email-changes"]],
  ["completeEmailChange", ["post", "/v1/identity/email-changes/{id}:complete"]],
  ["beginTotpEnrollment", ["post", "/v1/identity/totp/enroll"]],
  ["confirmTotpEnrollment", ["post", "/v1/identity/totp/confirm"]],
  ["disableTotp", ["post", "/v1/identity/totp/disable"]],
  ["regenerateRecoveryCodes", ["post", "/v1/identity/recovery-codes:regenerate"]],
  ["beginAccountRecovery", ["post", "/v1/identity/account-recoveries"]],
  ["completeAccountRecovery", ["post", "/v1/identity/account-recoveries/{id}:complete"]],
  ["reauthenticateIdentitySession", ["post", "/v1/identity/sessions:reauthenticate"]],
  ["getPersonalContext", ["get", "/v1/me/personal-context"]],
  ["previewRedemption", ["post", "/v1/redemptions:preview"]],
  ["confirmRedemption", ["post", "/v1/redemptions:confirm"]],
  ["recoverRedemptionCommand", ["get", "/v1/redemption-commands:recover"]],
  ["getRedemptionReceipt", ["get", "/v1/redemptions/{id}"]],
  ["listAccountProducts", ["get", "/v1/me/products"]],
  ["getCreditSummary", ["get", "/v1/me/credits"]],
  ["getCreditGrant", ["get", "/v1/me/credit-grants/{id}"]],
  ["getUsageDetail", ["get", "/v1/me/usage/{id}"]],
  ["createAssetUploadIntent", ["post", "/v1/projects/{projectRef}/asset-upload-intents"]],
  ["completeAssetUpload", ["post", "/v1/projects/{projectRef}/asset-upload-intents/{intentRef}:complete"]],
  ["getAssetUploadStatus", ["get", "/v1/projects/{projectRef}/asset-upload-intents/{intentRef}"]],
  ["recoverAssetUploadCommand", ["get", "/v1/projects/{projectRef}/asset-upload-commands/{commandId}"]],
  ["getTrustedAssetGrant", ["get", "/v1/projects/{projectRef}/assets/{assetRef}/versions/{assetVersionRef}/grants/{assetGrantRef}"]],
  ["getPublicCommandReceipt", ["get", "/v1/commands/{id}/receipt"]],
]);

const PRIVILEGED = Object.freeze({
  "platform-admin-identity": {
    path: "contract/proto/kokoro/platform/identity/v1/admin_identity.proto",
    service: "AdminIdentityService",
    version: 1,
    methods: [
      "BeginOperatorLogin",
      "ExchangeOidcSession",
      "GetOperatorSessionDelivery",
      "BeginStepUp",
      "CompleteStepUp",
      "SignOut",
    ],
  },
  "platform-admin-query": {
    path: "contract/proto/kokoro/platform/admin/v2/admin_query.proto",
    service: "AdminQueryService",
    version: 2,
    methods: ["GetSite", "ListSites", "GetUserWithinSite", "GetAuditWithinScope"],
  },
  "platform-admin-command": {
    path: "contract/proto/kokoro/platform/admin/v2/admin_command.proto",
    service: "AdminCommandService",
    version: 2,
    methods: ["SubmitCommand", "DecideApproval", "GetReceipt"],
  },
  "platform-site-lifecycle": {
    path: "contract/proto/kokoro/platform/site/v1/site_lifecycle.proto",
    service: "SiteLifecycleService",
    version: 1,
    methods: [
      "RequestSite",
      "GetProvisioningReceipt",
      "ReconcileProvisioning",
      "CreateRelease",
      "ActivateRelease",
      "GetActivationReceipt",
      "SuspendSite",
      "ResumeSite",
      "PlanDecommission",
      "CancelDecommission",
      "ExecuteDecommission",
      "GetDecommissionReceipt",
    ],
  },
});

// Wave 3 intentionally replaced the unused contract-only Admission v1 before any provider existed.
// Keep the approved five-command shape and its registry declaration byte-frozen from this point.
const ADMISSION_SHA256 = "f9690f6d80cf8f2f994b9573af57a59f356d2a0ae25d3b5b0686688182adf68c";
const ADMISSION_REGISTRY_SHA256 = "462730285d52aad2ce4ee2b8446d0b549c2084ae375cdaee427c025ba6e61c8b";

function fail(errors, code) {
  errors.push(code);
}

function read(root, path) {
  return readFileSync(resolve(root, path), "utf8");
}

function digest(value) {
  return createHash("sha256").update(value).digest("hex");
}

function serviceMethods(source, service) {
  const block = new RegExp(`service\\s+${service}\\s*\\{([\\s\\S]*?)\\n\\}`, "u").exec(source);
  if (!block) return [];
  return [...block[1].matchAll(/rpc\s+(\w+)\s*\(/gu)].map((match) => match[1]);
}

function parsePublicOpenApi(source, errors) {
  try {
    return readOpenApiDocument(source);
  } catch (error) {
    fail(errors, `public_openapi_unreadable:${error.message}`);
    return { paths: {}, security: [], components: {} };
  }
}

function sameJson(left, right) {
  return JSON.stringify(left) === JSON.stringify(right);
}

function hasProductWorkload(security) {
  return (
    Array.isArray(security) &&
    security.some(
      (requirement) =>
        requirement !== null &&
        typeof requirement === "object" &&
        Array.isArray(requirement.ProductWorkload),
    )
  );
}

function checkPublic(source, document, errors) {
  const parsed = openApiOperations(document);
  const actual = new Map(
    [...parsed].map(([operationId, { method, path }]) => [operationId, [method, path]]),
  );
  if (!sameJson([...actual.entries()].sort(), [...PUBLIC_OPERATIONS.entries()].sort())) {
    fail(errors, "public_surface_drift");
  }
  if (document.components?.securitySchemes?.ProductWorkload?.type !== "mutualTLS") {
    fail(errors, "public_workload_binding_missing");
  }
  if (!hasProductWorkload(document.security)) fail(errors, "public_workload_security_missing");
  for (const [operationId, { operation }] of parsed) {
    if (!hasProductWorkload(operation.security ?? document.security)) {
      fail(errors, `public_operation_security_missing:${operationId}`);
    }
  }
  const parameters = document.components?.parameters ?? {};
  if (
    parameters.IdempotencyKey?.name !== "Idempotency-Key" ||
    parameters.ContractVersion?.name !== "Kokoro-Contract-Version"
  ) {
    fail(errors, "public_command_headers_missing");
  }
  const nonIdempotentCredentialOperations = new Set(["issueSessionAccessGrant"]);
  for (const [operationId, { method, operation }] of parsed) {
    if (method !== "post") continue;
    const refs = new Set(
      (operation.parameters ?? [])
        .map((parameter) => parameter?.$ref?.split("/").at(-1))
        .filter(Boolean),
    );
    const required = nonIdempotentCredentialOperations.has(operationId)
      ? ["ContractVersion", "CsrfToken"]
      : ["ContractVersion", "IdempotencyKey", "CsrfToken"];
    if (required.some((parameter) => !refs.has(parameter))) {
      fail(errors, `public_mutation_header_policy_drift:${operationId}`);
    }
    if (
      nonIdempotentCredentialOperations.has(operationId) &&
      (refs.has("IdempotencyKey") || refs.has("CommandIdentity"))
    ) {
      fail(errors, `public_ephemeral_credential_replay_policy_drift:${operationId}`);
    }
  }
  const error = document.components?.schemas?.ErrorResponse;
  const errorFields = new Set(Object.keys(error?.properties ?? {}));
  for (const required of ["code", "retryClass", "requestId", "correlationId"]) {
    if (!errorFields.has(required)) fail(errors, `public_error_contract_missing:${required}`);
  }
  const grantOperation = parsed.get("issueSessionAccessGrant")?.operation;
  if (
    !grantOperation ||
    !sameJson(grantOperation.security, [{ ProductWorkload: [], UserSession: [] }]) ||
    !grantOperation.responses?.["201"]
  ) {
    fail(errors, "session_access_grant_operation_drift");
  }
  const schemas = document.components?.schemas ?? {};
  const requiredProductAxes = new Set(schemas.ProductContext?.required ?? []);
  for (const axis of [
    "productContextRef", "siteProjectBindingRef", "deploymentRef", "siteRef", "siteReleaseRef",
    "webArtifactDigest", "runtimeEnvironment", "region", "sessionContractRevision", "policyEpoch",
    "revocationEpoch", "modelOptionCatalogRef", "modelOptionCatalogs", "issuedAt", "expiresAt",
  ]) {
    if (!requiredProductAxes.has(axis)) fail(errors, `product_context_axis_missing:${axis}`);
  }
  const surfaceCatalogRequired = new Set(schemas.SurfaceModelOptionCatalog?.required ?? []);
  for (const field of [
    "surfaceId", "catalogRevisionRef", "defaultModelOptionRevisionRef", "options", "publishedAt",
  ]) {
    if (!surfaceCatalogRequired.has(field)) fail(errors, `model_option_catalog_field_missing:${field}`);
  }
  const publicOptionFields = new Set(Object.keys(schemas.PublishedModelOption?.properties ?? {}));
  for (const forbidden of [
    "provider", "providerRef", "route", "secretRef", "fallbackOrder", "orchestrationModelRef",
  ]) {
    if (publicOptionFields.has(forbidden)) fail(errors, `model_option_catalog_leaks_internal:${forbidden}`);
  }
  const requiredGrantAxes = new Set(schemas.SessionAccessGrantBinding?.required ?? []);
  for (const axis of [
    "productContextRef", "siteProjectBindingRef", "deploymentRef", "siteRef", "siteReleaseRef",
    "webArtifactDigest", "runtimeEnvironment", "region", "sessionContractRevision", "projectRef",
    "subjectRef", "subjectGeneration", "identitySessionRef", "issuer", "keyRevision", "notBefore",
    "siteSecurityEpoch", "identitySessionEpoch", "membershipEpoch", "authorizationEpoch",
    "restrictionEpoch", "credentialEpoch", "policyEpoch", "revocationEpoch", "issuedAt", "expiresAt",
  ]) {
    if (!requiredGrantAxes.has(axis)) fail(errors, `session_access_grant_axis_missing:${axis}`);
  }
  const uint64 = schemas.PositiveUint64String;
  if (
    uint64?.type !== "string" ||
    uint64?.minLength !== 1 ||
    uint64?.maxLength !== 20 ||
    uint64?.["x-kokoro-maximum"] !== "18446744073709551615"
  ) {
    fail(errors, "positive_uint64_contract_drift");
  }
  const resourceVariants = schemas.SessionGrantResource?.oneOf ?? [];
  if (
    resourceVariants.length !== 3 ||
    !new Set(resourceVariants.map((item) => item.$ref?.split("/").at(-1))).has("SessionGrantRunResource") ||
    !(schemas.SessionAccessGrantInput?.required ?? []).includes("resource") ||
    !(schemas.SessionAccessGrantBinding?.required ?? []).includes("resource")
  ) {
    fail(errors, "session_access_grant_resource_binding_drift");
  }
  const authorizationVariants = schemas.SessionGrantAuthorization?.oneOf ?? [];
  if (authorizationVariants.length !== 4) fail(errors, "session_access_grant_authorization_drift");
  if (
    schemas.SessionAccessGrant?.properties?.credential?.pattern !==
    "^[A-Za-z0-9_-]+\\.[A-Za-z0-9_-]+\\.[A-Za-z0-9_-]+$"
  ) {
    fail(errors, "session_access_grant_credential_shape_drift");
  }
  if (!(schemas.PersonalContext?.required ?? []).includes("productContextRef")) {
    fail(errors, "personal_context_product_binding_missing");
  }
  const previewInputFields = new Set(Object.keys(schemas.RedemptionPreviewInput?.properties ?? {}));
  if (!sameJson([...previewInputFields].sort(), ["code"])) {
    fail(errors, "redemption_preview_authority_drift");
  }
  const confirmInputFields = new Set(Object.keys(schemas.RedemptionConfirmInput?.properties ?? {}));
  if (!sameJson([...confirmInputFields].sort(), ["legalAcceptanceRefs", "previewCredential"])) {
    fail(errors, "redemption_confirm_authority_drift");
  }
  const forbiddenCommerceRequestFields = new Set([
    "siteId", "siteRef", "billingAccountId", "owner", "ownerId", "price", "provider", "paymentId",
  ]);
  for (const schemaName of ["RedemptionPreviewInput", "RedemptionConfirmInput"]) {
    const fields = Object.keys(schemas[schemaName]?.properties ?? {});
    if (fields.some((field) => forbiddenCommerceRequestFields.has(field))) {
      fail(errors, `commerce_browser_authority_forbidden:${schemaName}`);
    }
  }
  const acquisitionKinds = schemas.AcquisitionSourceSummary?.properties?.kind?.enum ?? [];
  if (
    !sameJson(acquisitionKinds, ["redemption", "admin_grant", "program_window"]) ||
    JSON.stringify(schemas).includes('"payment"')
  ) {
    fail(errors, "redeem_only_acquisition_contract_drift");
  }
  for (const code of [
    "REDEEM_NOT_ACCEPTED", "REDEEM_TEMPORARILY_UNAVAILABLE", "IDEMPOTENCY_CONFLICT",
    "ACQUISITION_CHANNEL_DISABLED",
  ]) {
    if (!(schemas.ErrorCode?.enum ?? []).includes(code)) fail(errors, `commerce_error_code_missing:${code}`);
  }
  const assetOperations = [
    "createAssetUploadIntent", "completeAssetUpload", "getAssetUploadStatus",
    "recoverAssetUploadCommand", "getTrustedAssetGrant",
  ];
  for (const operationId of assetOperations) {
    const entry = parsed.get(operationId);
    if (
      !entry || !entry.path.includes("{projectRef}") ||
      !sameJson(entry.operation.security, [{ ProductWorkload: [], UserSession: [] }])
    ) fail(errors, `asset_owner_authority_drift:${operationId}`);
  }
  for (const responseName of [
    "AssetUploadIntentResponse", "AssetUploadCommandResponse", "AssetUploadStatusResponse",
    "TrustedAssetGrantResponse",
  ]) {
    if (document.components?.responses?.[responseName]?.headers?.["Cache-Control"]?.schema?.const !== "no-store") {
      fail(errors, `asset_response_cache_policy_drift:${responseName}`);
    }
  }
  const assetReceiptFields = Object.keys(schemas.AssetUploadOwnerReceipt?.properties ?? {});
  const assetStatusFields = Object.keys(schemas.AssetUploadStatus?.properties ?? {});
  const forbiddenAssetFields = [
    "credential", "presignedUrl", "bucket", "storageKey", "quarantineObjectRef", "providerEtag",
  ];
  if (forbiddenAssetFields.some((field) => assetReceiptFields.includes(field) || assetStatusFields.includes(field))) {
    fail(errors, "asset_owner_projection_leaks_storage_authority");
  }
  const trustedGrantRequired = new Set(schemas.TrustedAssetGrant?.required ?? []);
  for (const field of [
    "assetRef", "assetVersionRef", "assetGrantRef", "projectRef", "purpose",
    "subjectGeneration", "eligibilityEpoch", "state",
  ]) {
    if (!trustedGrantRequired.has(field)) fail(errors, `trusted_asset_grant_axis_missing:${field}`);
  }
  for (const code of [
    "ASSET_NOT_ACCEPTED", "ASSET_UPLOAD_CONFLICT", "ASSET_QUOTA_EXCEEDED",
    "ASSET_TEMPORARILY_UNAVAILABLE",
  ]) {
    if (!(schemas.ErrorCode?.enum ?? []).includes(code)) fail(errors, `asset_error_code_missing:${code}`);
  }
  for (const forbidden of [
    /x-kokoro-site-id/iu,
    /^\s+siteId:/mu,
    /^\s+userId:/mu,
    /^\s+workspaceId:/mu,
    /\/v1\/redeem:apply/iu,
    /\/v1\/executions:prepare/iu,
    /chat\.execution\.prepare/iu,
    /\/checkout|\/refund|\/dispute|\/payment/iu,
  ]) {
    if (forbidden.test(source)) fail(errors, `public_forbidden_surface:${forbidden.source}`);
  }
}

function checkRegistry(root, publicDocument, registry, errors) {
  const wave1 = new Map(
    registry.boundaries
      .filter((boundary) => boundary.id === "platform-public" || boundary.id in PRIVILEGED)
      .map((boundary) => [boundary.id, boundary]),
  );
  if (wave1.size !== 5) fail(errors, "wave1_boundary_count");
  for (const [id, boundary] of wave1) {
    const expectedLifecycle = "contract-only";
    if (boundary.lifecycle !== expectedLifecycle || boundary.sourceStatus !== "machine-readable") {
      fail(errors, `wave1_boundary_lifecycle:${id}`);
    }
  }
  const publicBoundary = wave1.get("platform-public");
  if (
    !publicBoundary ||
    publicBoundary.version !== 1 ||
    publicBoundary.sources?.length !== 1 ||
    publicBoundary.sources[0].kind !== "openapi" ||
    publicBoundary.sources[0].path !== "contract/openapi/platform-public-v1.yaml" ||
    !sameJson(publicBoundary.operations.map(({ id }) => id).sort(), [...PUBLIC_OPERATIONS.keys()].sort()) ||
    publicBoundary.operations.some(({ siteBinding }) => siteBinding !== "workload-binding")
  ) {
    fail(errors, "platform_public_registry_drift");
  }
  for (const [id, definition] of Object.entries(PRIVILEGED)) {
    const boundary = wave1.get(id);
    if (
      !boundary ||
      boundary.version !== definition.version ||
      boundary.sources?.length !== 1 ||
      boundary.sources[0].path !== definition.path ||
      boundary.sources[0].select?.service !== definition.service ||
      !sameJson(boundary.operations.map(({ id: operation }) => operation), definition.methods)
    ) {
      fail(errors, `privileged_registry_drift:${id}`);
    }
  }
  if (openApiOperations(publicDocument).size !== 37) fail(errors, "public_registry_source_count");

  const admission = registry.boundaries.find((boundary) => boundary.id === "platform-admission");
  if (digest(JSON.stringify(admission)) !== ADMISSION_REGISTRY_SHA256) fail(errors, "platform_admission_registry_changed");
  if (digest(read(root, "contract/proto/kokoro/platform/admission/v1/admission.proto")) !== ADMISSION_SHA256) {
    fail(errors, "platform_admission_proto_changed");
  }
}

export function checkWave1Surface(root) {
  const errors = [];
  const publicSource = read(root, "contract/openapi/platform-public-v1.yaml");
  const publicDocument = parsePublicOpenApi(publicSource, errors);
  const registry = JSON.parse(read(root, "contract/registry/boundaries.yaml"));
  checkPublic(publicSource, publicDocument, errors);
  checkRegistry(root, publicDocument, registry, errors);

  const sources = new Map();
  for (const [id, definition] of Object.entries(PRIVILEGED)) {
    const source = sources.get(definition.path) ?? read(root, definition.path);
    sources.set(definition.path, source);
    if (!sameJson(serviceMethods(source, definition.service), definition.methods)) {
      fail(errors, `privileged_service_drift:${id}`);
    }
  }
  const identity = sources.get(PRIVILEGED["platform-admin-identity"].path);
  if (!identity.includes("authorization_code") || identity.includes("id_token")) {
    fail(errors, "platform_oidc_redeemer_drift");
  }
  const control = sources.get(PRIVILEGED["platform-admin-command"].path);
  const commandMethods = serviceMethods(control, "AdminCommandService");
  const lifecycleMethods = PRIVILEGED["platform-site-lifecycle"].methods;
  if (commandMethods.some((method) => lifecycleMethods.includes(method)) || control.includes("bytes payload")) {
    fail(errors, "generic_site_lifecycle_effect_present");
  }
  const generator = read(root, "contract/generate.mjs");
  for (const id of [
    "platform-admin-auth@v1",
    "platform-admin-identity@v1",
    "platform-admin-query@v2",
    "platform-admin-command@v2",
    "platform-site-lifecycle@v1",
  ]) {
    if (!generator.includes(id)) fail(errors, `generated_boundary_missing:${id}`);
  }
  if (generator.includes("await protoFiles(protoRoot)")) fail(errors, "whole_proto_tree_digest_present");
  return errors.sort();
}

function parseRoot(argv) {
  if (argv.length === 0) return process.cwd();
  if (argv.length !== 2 || argv[0] !== "--root" || argv[1].length === 0) throw new Error("arguments_invalid");
  return isAbsolute(argv[1]) ? argv[1] : resolve(argv[1]);
}

function main() {
  try {
    const errors = checkWave1Surface(parseRoot(process.argv.slice(2)));
    if (errors.length > 0) throw new Error(errors.join(","));
    process.stdout.write("wave1_surface_ok: 37 public operations, 4 privileged services, 1 active command boundary\n");
  } catch (error) {
    process.stderr.write(`wave1_surface_failed:${error.message}\n`);
    process.exitCode = 1;
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) main();
