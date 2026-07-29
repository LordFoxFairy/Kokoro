#!/usr/bin/env node

import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { isAbsolute, resolve } from "node:path";
import { pathToFileURL } from "node:url";
import { openApiOperations, readOpenApiDocument } from "./openapi-reader.mjs";

const PUBLIC_OPERATIONS = new Map([
  ["exchangeProductContext", ["post", "/v1/product-context:exchange"]],
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
    methods: ["PrepareCommand", "SubmitForApproval", "DecideApproval", "ExecuteApproved", "GetReceipt"],
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

const ADMISSION_SHA256 = "cfe855ad4acd481e1d1a21c3bf4d3baa4362f454b5723b76ffc57b8a8b58d583";
// The Admission wire remains byte-frozen. Its registry metadata now names the already-published
// GetCommandReceipt recovery operation so reconcile_receipt is machine-verifiable.
const ADMISSION_REGISTRY_SHA256 = "60c41c28bbf1beddceac870d9b946ad4c238421927d87547775b02e192aafc75";

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
  const requiredMutationParameters = new Set(["ContractVersion", "IdempotencyKey", "CsrfToken"]);
  for (const [operationId, { method, operation }] of parsed) {
    if (method !== "post") continue;
    const refs = new Set(
      (operation.parameters ?? [])
        .map((parameter) => parameter?.$ref?.split("/").at(-1))
        .filter(Boolean),
    );
    if ([...requiredMutationParameters].some((parameter) => !refs.has(parameter))) {
      fail(errors, `public_mutation_header_policy_drift:${operationId}`);
    }
  }
  const error = document.components?.schemas?.ErrorResponse;
  const errorFields = new Set(Object.keys(error?.properties ?? {}));
  for (const required of ["code", "retryClass", "requestId", "correlationId"]) {
    if (!errorFields.has(required)) fail(errors, `public_error_contract_missing:${required}`);
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
    if (boundary.lifecycle !== "contract-only" || boundary.sourceStatus !== "machine-readable") {
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
  if (openApiOperations(publicDocument).size !== 23) fail(errors, "public_registry_source_count");

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
    process.stdout.write("wave1_surface_ok: 23 public operations, 4 privileged services, 5 contract-only boundaries\n");
  } catch (error) {
    process.stderr.write(`wave1_surface_failed:${error.message}\n`);
    process.exitCode = 1;
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) main();
