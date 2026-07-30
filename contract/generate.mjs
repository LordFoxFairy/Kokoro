#!/usr/bin/env node

import { createHash } from "node:crypto";
import { execFile } from "node:child_process";
import { mkdtemp, readFile, readdir, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, relative, resolve } from "node:path";
import { promisify } from "node:util";
import { fileURLToPath, pathToFileURL } from "node:url";

const execFileAsync = promisify(execFile);
const contractRoot = dirname(fileURLToPath(import.meta.url));
const repositoryRoot = resolve(contractRoot, "..");
const defaultMirrors = [
  resolve(repositoryRoot, "kokoro-platform/kokoro-platform-admin/src/generated/contracts"),
  resolve(repositoryRoot, "kokoro-web/apps/admin/lib/generated/contracts"),
];

const DEFAULT_BOUNDARY = "platform-admin-auth@v1";
const BOUNDARIES = Object.freeze({
  "platform-admin-auth@v1": Object.freeze({
    schema: "kokoro.platform.admin.v1.AdminAuthService",
    version: 1,
    inputs: Object.freeze(["proto/kokoro/platform/admin/v1/admin_auth.proto"]),
    sources: Object.freeze([
      "kokoro/common/v1/error.proto",
      "kokoro/common/v1/receipt.proto",
      "kokoro/platform/admin/v1/admin_auth.proto",
    ]),
    helper: "admin-auth-effect-digest.ts",
    commandEnvelopeDigest: null,
  }),
  "platform-admin-identity@v1": Object.freeze({
    schema: "kokoro.platform.identity.v1.AdminIdentityService",
    version: 1,
    inputs: Object.freeze(["proto/kokoro/platform/identity/v1/admin_identity.proto"]),
    sources: Object.freeze([
      "kokoro/common/v1/error.proto",
      "kokoro/common/v2/command_envelope.proto",
      "kokoro/platform/admin/v2/admin_shared.proto",
      "kokoro/platform/identity/v1/admin_identity.proto",
    ]),
    helper: null,
    commandEnvelopeDigest: "identity",
  }),
  "platform-admin-query@v2": Object.freeze({
    schema: "kokoro.platform.admin.v2.AdminQueryService",
    version: 2,
    inputs: Object.freeze(["proto/kokoro/platform/admin/v2/admin_query.proto"]),
    sources: Object.freeze([
      "kokoro/common/v1/error.proto",
      "kokoro/common/v2/command_envelope.proto",
      "kokoro/platform/admin/v2/admin_shared.proto",
      "kokoro/platform/admin/v2/admin_query.proto",
    ]),
    helper: null,
    commandEnvelopeDigest: null,
  }),
  "platform-admin-command@v2": Object.freeze({
    schema: "kokoro.platform.admin.v2.AdminCommandService",
    version: 2,
    inputs: Object.freeze(["proto/kokoro/platform/admin/v2/admin_command.proto"]),
    sources: Object.freeze([
      "kokoro/common/v1/error.proto",
      "kokoro/common/v2/command_envelope.proto",
      "kokoro/platform/admin/v2/admin_shared.proto",
      "kokoro/platform/admin/v2/admin_command.proto",
    ]),
    helper: null,
    commandEnvelopeDigest: "admin-command",
  }),
  "platform-admin-commerce@v1": Object.freeze({
    schema: "kokoro.platform.commerce.v1.AdminCommerceService",
    version: 1,
    inputs: Object.freeze(["proto/kokoro/platform/commerce/v1/admin_commerce.proto"]),
    sources: Object.freeze([
      "kokoro/common/v1/error.proto",
      "kokoro/common/v2/command_envelope.proto",
      "kokoro/platform/admin/v2/admin_shared.proto",
      "kokoro/platform/commerce/v1/admin_commerce.proto",
    ]),
    helper: null,
    commandEnvelopeDigest: "admin-commerce",
  }),
  "platform-admin-credit@v1": Object.freeze({
    schema: "kokoro.platform.credit.v1.AdminCreditService",
    version: 1,
    inputs: Object.freeze(["proto/kokoro/platform/credit/v1/admin_credit.proto"]),
    sources: Object.freeze([
      "kokoro/common/v2/command_envelope.proto",
      "kokoro/platform/admin/v2/admin_shared.proto",
      "kokoro/platform/credit/v1/admin_credit.proto",
    ]),
    helper: null,
    commandEnvelopeDigest: null,
  }),
  "platform-site-lifecycle@v1": Object.freeze({
    schema: "kokoro.platform.site.v1.SiteLifecycleService",
    version: 1,
    inputs: Object.freeze(["proto/kokoro/platform/site/v1/site_lifecycle.proto"]),
    sources: Object.freeze([
      "kokoro/common/v1/error.proto",
      "kokoro/common/v2/command_envelope.proto",
      "kokoro/platform/admin/v2/admin_shared.proto",
      "kokoro/platform/site/v1/site_lifecycle.proto",
    ]),
    helper: null,
    commandEnvelopeDigest: "site-lifecycle",
  }),
  "platform-site-provisioning@v1": Object.freeze({
    schema: "kokoro.platform.site.v1.SiteProvisioningService",
    version: 1,
    inputs: Object.freeze(["proto/kokoro/platform/site/v1/site_provisioning.proto"]),
    sources: Object.freeze([
      "kokoro/common/v1/error.proto",
      "kokoro/common/v2/command_envelope.proto",
      "kokoro/platform/admin/v2/admin_shared.proto",
      "kokoro/platform/site/v1/site_provisioning.proto",
    ]),
    helper: null,
    commandEnvelopeDigest: "site-provisioning",
  }),
  "platform-model-control@v1": Object.freeze({
    schema: "kokoro.platform.model.v1.ModelControlService",
    version: 1,
    inputs: Object.freeze(["proto/kokoro/platform/model/v1/model_control.proto"]),
    sources: Object.freeze([
      "kokoro/common/v1/error.proto",
      "kokoro/common/v2/command_envelope.proto",
      "kokoro/platform/admin/v2/admin_shared.proto",
      "kokoro/platform/model/v1/model_control.proto",
    ]),
    helper: null,
    commandEnvelopeDigest: "model-control",
    errorContract: "model-control-admin",
  }),
  "platform-admission@v1": Object.freeze({
    schema: "kokoro.platform.admission.v1.AdmissionService",
    version: 1,
    inputs: Object.freeze(["proto/kokoro/platform/admission/v1/admission.proto"]),
    sources: Object.freeze([
      "kokoro/common/v1/error.proto",
      "kokoro/common/v1/receipt.proto",
      "kokoro/platform/admission/v1/admission.proto",
    ]),
    helper: null,
    commandEnvelopeDigest: null,
  }),
  "platform-asset-eligibility@v1": Object.freeze({
    schema: "kokoro.platform.asset.v1.AssetEligibilityService",
    version: 1,
    inputs: Object.freeze(["proto/kokoro/platform/asset/v1/asset_eligibility.proto"]),
    sources: Object.freeze([
      "kokoro/platform/asset/v1/asset_eligibility.proto",
    ]),
    helper: null,
    commandEnvelopeDigest: null,
  }),
  "platform-session-authorization@v1": Object.freeze({
    schema: "kokoro.platform.authorization.v1.SessionAuthorizationService",
    version: 1,
    inputs: Object.freeze(["proto/kokoro/platform/authorization/v1/session_authorization.proto"]),
    sources: Object.freeze([
      "kokoro/platform/authorization/v1/session_authorization.proto",
    ]),
    helper: null,
    commandEnvelopeDigest: null,
  }),
  "platform-session-authorization@v2": Object.freeze({
    schema: "kokoro.platform.authorization.v2.ScopedSessionAuthorizationService",
    version: 2,
    inputs: Object.freeze(["proto/kokoro/platform/authorization/v2/scoped_session_authorization.proto"]),
    sources: Object.freeze([
      "kokoro/platform/authorization/v2/scoped_session_authorization.proto",
    ]),
    helper: null,
    commandEnvelopeDigest: null,
  }),
  "session-dispatch-owner-evidence@v1": Object.freeze({
    schema: "kokoro.session.dispatch.v1.DispatchOwnerEvidenceService",
    version: 1,
    inputs: Object.freeze(["proto/kokoro/session/dispatch/v1/dispatch_owner_evidence.proto"]),
    sources: Object.freeze([
      "kokoro/session/dispatch/v1/dispatch_owner_evidence.proto",
    ]),
    helper: null,
    commandEnvelopeDigest: null,
  }),
  "session-admission-owner@v1": Object.freeze({
    schema: "kokoro.session.admission.v1.SessionAdmissionOwnerService",
    version: 1,
    inputs: Object.freeze(["proto/kokoro/session/admission/v1/session_admission_owner.proto"]),
    sources: Object.freeze([
      "kokoro/session/admission/v1/session_admission_owner.proto",
    ]),
    helper: null,
    commandEnvelopeDigest: null,
  }),
  "agent-execution-evidence@v1": Object.freeze({
    schema: "kokoro.agent.execution.v1.AgentExecutionEvidenceService",
    version: 1,
    inputs: Object.freeze([
      "proto/kokoro/agent/execution/v1/agent_execution_evidence.proto",
    ]),
    sources: Object.freeze([
      "kokoro/agent/execution/v1/agent_execution_evidence.proto",
    ]),
    helper: null,
    commandEnvelopeDigest: null,
  }),
  "platform-media-runtime@v1": Object.freeze({
    schema: "kokoro.platform.media.v1.MediaRuntimeService",
    version: 1,
    inputs: Object.freeze([
      "proto/kokoro/platform/media/v1/media_runtime.proto",
    ]),
    sources: Object.freeze([
      "kokoro/platform/media/v1/media_runtime.proto",
    ]),
    helper: null,
    commandEnvelopeDigest: null,
  }),
  "model-image-effect@v1": Object.freeze({
    schema: "kokoro.platform.model.image.v1.ImageEffectV1Service",
    version: 1,
    inputs: Object.freeze([
      "proto/kokoro/platform/model/image/v1/image_effect.proto",
    ]),
    sources: Object.freeze([
      "kokoro/platform/model/image/v1/image_effect.proto",
    ]),
    helper: null,
    commandEnvelopeDigest: null,
  }),
  "session-media-projection@v1": Object.freeze({
    schema: "kokoro.session.media.v1.SessionMediaProjectionService",
    version: 1,
    inputs: Object.freeze([
      "proto/kokoro/session/media/v1/media_projection.proto",
    ]),
    sources: Object.freeze([
      "kokoro/platform/credit/v1/cost_projection.proto",
      "kokoro/platform/media/v1/media_projection.proto",
      "kokoro/session/media/v1/media_projection.proto",
    ]),
    helper: null,
    commandEnvelopeDigest: null,
  }),
  "platform-media-projection-recovery@v1": Object.freeze({
    schema: "kokoro.platform.media.v1.MediaProjectionRecoveryService",
    version: 1,
    inputs: Object.freeze([
      "proto/kokoro/platform/media/v1/media_projection_recovery.proto",
    ]),
    sources: Object.freeze([
      "kokoro/platform/media/v1/media_projection.proto",
      "kokoro/platform/media/v1/media_projection_recovery.proto",
    ]),
    helper: null,
    commandEnvelopeDigest: null,
  }),
  "platform-credit-cost-projection-recovery@v1": Object.freeze({
    schema: "kokoro.platform.credit.v1.CreditCostProjectionRecoveryService",
    version: 1,
    inputs: Object.freeze([
      "proto/kokoro/platform/credit/v1/cost_projection_recovery.proto",
    ]),
    sources: Object.freeze([
      "kokoro/platform/credit/v1/cost_projection.proto",
      "kokoro/platform/credit/v1/cost_projection_recovery.proto",
    ]),
    helper: null,
    commandEnvelopeDigest: null,
  }),
  "platform-model-gateway@v1": Object.freeze({
    schema: "kokoro.platform.model.v1.ModelGatewayService",
    version: 1,
    inputs: Object.freeze([
      "proto/kokoro/platform/model/v1/model_gateway.proto",
    ]),
    sources: Object.freeze([
      "kokoro/platform/model/v1/model_gateway.proto",
    ]),
    helper: "model-stream-frame-digest.ts",
    commandEnvelopeDigest: null,
  }),
  "platform-capability-catalog@v1": Object.freeze({
    schema: "kokoro.platform.capability.v1.HubCatalogService+HubRuntimeService+CapabilityCatalogProjectionService",
    version: 1,
    inputs: Object.freeze([
      "proto/kokoro/platform/capability/v1/capability_catalog.proto",
    ]),
    sources: Object.freeze([
      "kokoro/common/v1/error.proto",
      "kokoro/common/v1/receipt.proto",
      "kokoro/platform/capability/v1/capability_catalog.proto",
    ]),
    helper: null,
    commandEnvelopeDigest: null,
  }),
});

function parseArguments(argv) {
  const options = { boundary: DEFAULT_BOUNDARY, output: null };
  for (let index = 0; index < argv.length; index += 2) {
    const flag = argv[index];
    const value = argv[index + 1];
    if (!value || (flag !== "--boundary" && flag !== "--output")) {
      throw new Error("contract_generation_arguments_invalid");
    }
    if (flag === "--boundary") options.boundary = value;
    else options.output = resolve(value);
  }
  if (!(options.boundary in BOUNDARIES)) throw new Error("contract_generation_boundary_unknown");
  if (options.boundary !== DEFAULT_BOUNDARY && options.output === null) {
    throw new Error("contract_generation_output_required");
  }
  return options;
}

async function artifactFiles(directory, current = directory) {
  const entries = await readdir(current, { withFileTypes: true });
  const files = [];
  for (const entry of entries.sort((left, right) => left.name.localeCompare(right.name))) {
    const path = resolve(current, entry.name);
    if (entry.isDirectory()) files.push(...(await artifactFiles(directory, path)));
    else if (entry.isFile() && entry.name !== "contract-metadata.ts") files.push(path);
  }
  return files;
}

async function sourceMetadata(boundary) {
  const protoRoot = resolve(contractRoot, "proto");
  const hash = createHash("sha256");
  for (const sourcePath of boundary.sources) {
    const path = resolve(protoRoot, sourcePath);
    hash.update(`${sourcePath}\0`);
    hash.update(await readFile(path));
    hash.update("\0");
  }
  const packageJson = JSON.parse(await readFile(resolve(contractRoot, "package.json"), "utf8"));
  return {
    schemaId: boundary.schema,
    schemaVersion: boundary.version,
    sourceDigestSha256: hash.digest("hex"),
    sourcePaths: [...boundary.sources],
    generatorVersion: packageJson.devDependencies["@bufbuild/protoc-gen-es"],
    runtimeVersion: packageJson.devDependencies["@bufbuild/protobuf"],
  };
}

async function contractMetadata(mirror = defaultMirrors[0], boundary = BOUNDARIES[DEFAULT_BOUNDARY]) {
  const metadata = await sourceMetadata(boundary);
  const hash = createHash("sha256");
  for (const path of await artifactFiles(mirror)) {
    const artifactPath = relative(mirror, path).replaceAll("\\", "/");
    hash.update(`${artifactPath}\0`);
    hash.update(await readFile(path));
    hash.update("\0");
  }
  return { ...metadata, artifactDigestSha256: hash.digest("hex") };
}

function metadataSource(metadata) {
  const paths = metadata.sourcePaths.map((path) => `    ${JSON.stringify(path)},`).join("\n");
  return `// @generated by contract/generate.mjs; DO NOT EDIT.\n` +
    `export const contractMetadata = Object.freeze({\n` +
    `  schemaId: ${JSON.stringify(metadata.schemaId)},\n` +
    `  schemaVersion: ${metadata.schemaVersion},\n` +
    `  sourceDigestSha256: ${JSON.stringify(metadata.sourceDigestSha256)},\n` +
    `  artifactDigestSha256: ${JSON.stringify(metadata.artifactDigestSha256)},\n` +
    `  sourcePaths: Object.freeze([\n${paths}\n  ]),\n` +
    `  generatorVersion: ${JSON.stringify(metadata.generatorVersion)},\n` +
    `  runtimeVersion: ${JSON.stringify(metadata.runtimeVersion)},\n` +
    `});\n`;
}

function adminAuthEffectDigestSource() {
  return `// @generated by contract/generate.mjs; DO NOT EDIT.\n` +
    `import { createHash } from "node:crypto";\n` +
    `import { create, toBinary } from "@bufbuild/protobuf";\n` +
    `import { CommandDigestAlgorithm } from "./kokoro/common/v1/receipt_pb.js";\n` +
    `import {\n` +
    `  ConsumeVerificationTokenEffectSchema,\n` +
    `  CreateVerificationTokenEffectSchema,\n` +
    `  RecordAuthEventEffectSchema,\n` +
    `  type ConsumeVerificationTokenEffect,\n` +
    `  type CreateVerificationTokenEffect,\n` +
    `  type RecordAuthEventEffect,\n` +
    `} from "./kokoro/platform/admin/v1/admin_auth_pb.js";\n\n` +
    `export const ADMIN_AUTH_COMMAND_DIGEST_ALGORITHM =\n` +
    `  CommandDigestAlgorithm.SHA256_PROTOBUF_V1;\n\n` +
    `function normalizeEmail(value: string): string {\n` +
    `  return value.trim().toLowerCase();\n` +
    `}\n\n` +
    `function digest(typeName: string, bytes: Uint8Array): string {\n` +
    `  const hash = createHash("sha256");\n` +
    `  hash.update(typeName, "utf8");\n` +
    `  hash.update(Uint8Array.of(0));\n` +
    `  hash.update(bytes);\n` +
    `  return hash.digest("hex");\n` +
    `}\n\n` +
    `export function canonicalizeCreateVerificationTokenEffect(\n` +
    `  effect: CreateVerificationTokenEffect,\n` +
    `): CreateVerificationTokenEffect {\n` +
    `  return create(CreateVerificationTokenEffectSchema, {\n` +
    `    identifier: normalizeEmail(effect.identifier),\n` +
    `    token: effect.token,\n` +
    `    ...(effect.expires === undefined ? {} : { expires: effect.expires }),\n` +
    `  });\n` +
    `}\n\n` +
    `export function createVerificationTokenEffectDigest(effect: CreateVerificationTokenEffect): string {\n` +
    `  const canonical = canonicalizeCreateVerificationTokenEffect(effect);\n` +
    `  return digest(\n` +
    `    CreateVerificationTokenEffectSchema.typeName,\n` +
    `    toBinary(CreateVerificationTokenEffectSchema, canonical, { writeUnknownFields: false }),\n` +
    `  );\n` +
    `}\n\n` +
    `export function canonicalizeConsumeVerificationTokenEffect(\n` +
    `  effect: ConsumeVerificationTokenEffect,\n` +
    `): ConsumeVerificationTokenEffect {\n` +
    `  return create(ConsumeVerificationTokenEffectSchema, {\n` +
    `    identifier: normalizeEmail(effect.identifier),\n` +
    `    token: effect.token,\n` +
    `  });\n` +
    `}\n\n` +
    `export function consumeVerificationTokenEffectDigest(effect: ConsumeVerificationTokenEffect): string {\n` +
    `  const canonical = canonicalizeConsumeVerificationTokenEffect(effect);\n` +
    `  return digest(\n` +
    `    ConsumeVerificationTokenEffectSchema.typeName,\n` +
    `    toBinary(ConsumeVerificationTokenEffectSchema, canonical, { writeUnknownFields: false }),\n` +
    `  );\n` +
    `}\n\n` +
    `export function canonicalizeRecordAuthEventEffect(effect: RecordAuthEventEffect): RecordAuthEventEffect {\n` +
    `  const reason = effect.reason === undefined || effect.reason.length === 0 ? undefined : effect.reason;\n` +
    `  return create(RecordAuthEventEffectSchema, {\n` +
    `    email: normalizeEmail(effect.email),\n` +
    `    event: effect.event,\n` +
    `    ...(reason === undefined ? {} : { reason }),\n` +
    `    ...(effect.occurredAt === undefined ? {} : { occurredAt: effect.occurredAt }),\n` +
    `  });\n` +
    `}\n\n` +
    `export function recordAuthEventEffectDigest(effect: RecordAuthEventEffect): string {\n` +
    `  const canonical = canonicalizeRecordAuthEventEffect(effect);\n` +
    `  return digest(\n` +
    `    RecordAuthEventEffectSchema.typeName,\n` +
    `    toBinary(RecordAuthEventEffectSchema, canonical, { writeUnknownFields: false }),\n` +
    `  );\n` +
    `}\n`;
}

function modelStreamFrameDigestSource() {
  return `// @generated by contract/generate.mjs; DO NOT EDIT.
import { createHash } from "node:crypto";

export type ModelStreamFrameDigestInput = Readonly<{
  invocationRef: string;
  attemptRef: string;
  sequence: bigint;
  previousFrameDigest: string;
  payloadKind: "accepted" | "content_delta" | "reasoning_delta" | "tool_call_delta" |
    "completed" | "failed" | "outcome_unknown";
  payloadBytes: Uint8Array;
}>;

const encoder = new TextEncoder();

export function modelStreamFrameDigest(input: ModelStreamFrameDigestInput): string {
  if (input.invocationRef.length < 1 || input.invocationRef.length > 256 ||
      input.attemptRef.length < 1 || input.attemptRef.length > 256 ||
      input.sequence < 1n || input.sequence > 65536n ||
      !/^[0-9a-f]{64}$/u.test(input.previousFrameDigest) ||
      input.payloadBytes.byteLength < 1 || input.payloadBytes.byteLength > 12 * 1024 * 1024) {
    throw new Error("model_stream_frame_digest_input_invalid");
  }
  const hash = createHash("sha256");
  hash.update("kokoro.platform.model.stream-frame.v1");
  for (const field of [encoder.encode(input.invocationRef), encoder.encode(input.attemptRef),
    uint64(input.sequence), encoder.encode(input.previousFrameDigest), encoder.encode(input.payloadKind),
    input.payloadBytes]) {
    hash.update(uint64(BigInt(field.byteLength)));
    hash.update(field);
  }
  return hash.digest("hex");
}

function uint64(value: bigint): Uint8Array {
  if (value < 0n || value > 18446744073709551615n) {
    throw new Error("model_stream_frame_digest_input_invalid");
  }
  const result = new Uint8Array(8);
  let remaining = value;
  for (let index = 7; index >= 0; index -= 1) {
    result[index] = Number(remaining & 255n);
    remaining >>= 8n;
  }
  return result;
}
`;
}

function modelControlAdminErrorContractSource() {
  return `// @generated by contract/generate.mjs; DO NOT EDIT.
import { create } from "@bufbuild/protobuf";
import { KokoroErrorDetailSchema, RetryClass } from "./kokoro/common/v1/error_pb.js";

export const MODEL_CONTROL_ADMIN_ERRORS = Object.freeze({
  inventoryRevisionNotFound: Object.freeze({
    connectCode: "not_found",
    domainCode: "model.inventory.not_found",
    safeMessage: "Model inventory revision not found",
    retryClass: RetryClass.NEVER,
    httpStatus: 404,
  }),
  commandReceiptConflict: Object.freeze({
    connectCode: "already_exists",
    domainCode: "model.command_receipt_conflict",
    safeMessage: "Model command identity conflicts with an existing receipt",
    retryClass: RetryClass.NEVER,
    httpStatus: 409,
  }),
  commandReceiptNotFound: Object.freeze({
    connectCode: "not_found",
    domainCode: "model.command_receipt.not_found",
    safeMessage: "Model command receipt not found",
    retryClass: RetryClass.NEVER,
    httpStatus: 404,
  }),
  commandReceiptMismatch: Object.freeze({
    connectCode: "already_exists",
    domainCode: "model.command_receipt.mismatch",
    safeMessage: "Model command receipt does not match the requested operation or scope",
    retryClass: RetryClass.NEVER,
    httpStatus: 409,
  }),
  adminPageTokenInvalid: Object.freeze({
    connectCode: "invalid_argument",
    domainCode: "model.admin_page_token.invalid",
    safeMessage: "Model administration page token is invalid",
    retryClass: RetryClass.NEVER,
    httpStatus: 400,
  }),
  adminSessionUnauthenticated: Object.freeze({
    connectCode: "unauthenticated",
    domainCode: "admin.session.unauthenticated",
    safeMessage: "Admin session authentication failed",
    retryClass: RetryClass.NEVER,
    httpStatus: 401,
  }),
  adminPermissionDenied: Object.freeze({
    connectCode: "permission_denied",
    domainCode: "admin.permission_denied",
    safeMessage: "Admin operation is not permitted",
    retryClass: RetryClass.NEVER,
    httpStatus: 403,
  }),
});

export type ModelControlAdminErrorKind = keyof typeof MODEL_CONTROL_ADMIN_ERRORS;

export function modelControlAdminErrorDetail(
  kind: ModelControlAdminErrorKind,
  requestId: string,
  correlationId = requestId,
) {
  const contract = MODEL_CONTROL_ADMIN_ERRORS[kind];
  return {
    desc: KokoroErrorDetailSchema,
    value: create(KokoroErrorDetailSchema, {
      domainCode: contract.domainCode,
      retryClass: contract.retryClass,
      requestId: safeReference(requestId),
      correlationId: safeReference(correlationId),
      safeMessage: contract.safeMessage,
    }),
  };
}

function safeReference(value: string): string {
  return /^[A-Za-z0-9._:-]{1,128}$/u.test(value) ? value : "";
}
`;
}

function commandEnvelopeDigestCoreSource() {
  return `// @generated by contract/generate.mjs; DO NOT EDIT.
import { create, toBinary } from "@bufbuild/protobuf";
import { createHash } from "node:crypto";
import {
  CanonicalCommandEnvelopeV2Schema,
  CanonicalCommandTrustAxesV2Schema,
  CanonicalSecurityEpochV2Schema,
  CanonicalTypedProtobufV2Schema,
  CommandDigestAlgorithmV2,
  OperatorAssuranceLevel,
  type CanonicalCommandEnvelopeV2,
} from "./kokoro/common/v2/command_envelope_pb.js";

export const COMMAND_ENVELOPE_DIGEST_ALGORITHM_V2 =
  CommandDigestAlgorithmV2.SHA256_COMMAND_ENVELOPE;

type TypedPayload = Readonly<{
  typeName: string;
  bytes: Uint8Array;
}>;

type CanonicalInstant = Readonly<{
  seconds: bigint;
  nanos: number;
}>;

type TrustAxes = Readonly<{
  workloadIdentityRef?: string;
  audience?: string;
  environment: string;
  region: string;
  siteRef?: string;
  actorRef?: string;
  actorSessionRef?: string;
  managedDeviceRef?: string;
  actorGeneration?: bigint;
  assuranceLevel?: OperatorAssuranceLevel;
  factorClasses?: readonly string[];
  authenticatedAt?: CanonicalInstant;
  stepUpAt?: CanonicalInstant;
  operatorAttestationRef?: string;
  operatorAttestationDigest?: string;
  securityEpochs: readonly Readonly<{ axis: string; value: bigint }>[];
}>;

type CommandEnvelopeInput = Readonly<{
  contractVersion: string;
  operation: string;
  trust: TrustAxes;
  scope?: TypedPayload;
  targetRefs: readonly string[];
  effect: TypedPayload;
}>;

function requiredAxis(label: string, value: unknown): string {
  if (typeof value !== "string" || value.length === 0) {
    throw new Error("command_envelope_axis_missing:" + label);
  }
  return value;
}

function optionalAxis(label: string, value: string | undefined): string | undefined {
  if (value === undefined) return undefined;
  if (value.length === 0) throw new Error("command_envelope_axis_empty:" + label);
  return value;
}

function assertAxisMatch(label: string, declared: string, verified: string): string {
  const canonicalDeclared = requiredAxis(label, declared);
  if (canonicalDeclared !== requiredAxis("verified." + label, verified)) {
    throw new Error("command_envelope_axis_mismatch:" + label);
  }
  return canonicalDeclared;
}

function requiredSha256(label: string, value: unknown): string {
  if (typeof value !== "string" || !/^[0-9a-f]{64}$/u.test(value)) {
    throw new Error("command_envelope_sha256_invalid:" + label);
  }
  return value;
}

function optionalSha256(label: string, value: string | undefined): string | undefined {
  return value === undefined ? undefined : requiredSha256(label, value);
}

function assertSha256Match(label: string, declared: string, verified: string): string {
  const canonicalDeclared = requiredSha256(label, declared);
  if (canonicalDeclared !== requiredSha256("verified." + label, verified)) {
    throw new Error("command_envelope_axis_mismatch:" + label);
  }
  return canonicalDeclared;
}

function requiredUint64(label: string, value: unknown): bigint {
  if (typeof value !== "bigint" || value <= 0n || value > 18446744073709551615n) {
    throw new Error("command_envelope_uint64_invalid:" + label);
  }
  return value;
}

function optionalUint64(label: string, value: bigint | undefined): bigint | undefined {
  return value === undefined ? undefined : requiredUint64(label, value);
}

function assertUint64Match(label: string, declared: bigint, verified: bigint): bigint {
  const canonicalDeclared = requiredUint64(label, declared);
  if (canonicalDeclared !== requiredUint64("verified." + label, verified)) {
    throw new Error("command_envelope_axis_mismatch:" + label);
  }
  return canonicalDeclared;
}

function requiredAssurance(label: string, value: OperatorAssuranceLevel): OperatorAssuranceLevel {
  if (
    value !== OperatorAssuranceLevel.PASSWORD &&
    value !== OperatorAssuranceLevel.MFA &&
    value !== OperatorAssuranceLevel.PHISHING_RESISTANT
  ) throw new Error("command_envelope_assurance_invalid:" + label);
  return value;
}

function assertAssuranceMatch(
  label: string,
  declared: OperatorAssuranceLevel,
  verified: OperatorAssuranceLevel,
): OperatorAssuranceLevel {
  const canonicalDeclared = requiredAssurance(label, declared);
  if (canonicalDeclared !== requiredAssurance("verified." + label, verified)) {
    throw new Error("command_envelope_axis_mismatch:" + label);
  }
  return canonicalDeclared;
}

function optionalInstant(label: string, value: CanonicalInstant | undefined): CanonicalInstant | undefined {
  if (value === undefined) return undefined;
  if (
    typeof value.seconds !== "bigint" ||
    !Number.isInteger(value.nanos) ||
    value.nanos < 0 ||
    value.nanos > 999999999
  ) throw new Error("command_envelope_instant_invalid:" + label);
  return { seconds: value.seconds, nanos: value.nanos };
}

function assertInstantMatch(
  label: string,
  declared: CanonicalInstant | undefined,
  verified: CanonicalInstant | undefined,
  required: boolean,
): CanonicalInstant | undefined {
  const canonicalDeclared = optionalInstant(label, declared);
  const canonicalVerified = optionalInstant("verified." + label, verified);
  if (required && (canonicalDeclared === undefined || canonicalVerified === undefined)) {
    throw new Error("command_envelope_axis_missing:" + label);
  }
  if (
    canonicalDeclared?.seconds !== canonicalVerified?.seconds ||
    canonicalDeclared?.nanos !== canonicalVerified?.nanos
  ) throw new Error("command_envelope_axis_mismatch:" + label);
  return canonicalDeclared;
}

function compare(left: string, right: string): number {
  return left < right ? -1 : left > right ? 1 : 0;
}

function uniqueSorted(label: string, values: readonly string[], maximum = 100): string[] {
  if (!Array.isArray(values) || values.length > maximum) {
    throw new Error("command_envelope_collection_invalid:" + label);
  }
  const sorted = values.map((value) => requiredAxis(label, value)).sort(compare);
  if (sorted.some((value, index) => index > 0 && value === sorted[index - 1])) {
    throw new Error("command_envelope_collection_duplicate:" + label);
  }
  return sorted;
}

function assertCollectionMatch(
  label: string,
  declared: readonly string[],
  verified: readonly string[],
  maximum: number,
): string[] {
  const canonicalDeclared = uniqueSorted(label, declared, maximum);
  const canonicalVerified = uniqueSorted("verified." + label, verified, maximum);
  if (canonicalDeclared.length === 0) throw new Error("command_envelope_axis_missing:" + label);
  if (
    canonicalDeclared.length !== canonicalVerified.length ||
    canonicalDeclared.some((value, index) => value !== canonicalVerified[index])
  ) throw new Error("command_envelope_axis_mismatch:" + label);
  return canonicalDeclared;
}

function canonicalTyped(label: string, input: TypedPayload) {
  if (input === undefined || input === null || !(input.bytes instanceof Uint8Array)) {
    throw new Error("command_envelope_typed_payload_invalid:" + label);
  }
  return create(CanonicalTypedProtobufV2Schema, {
    typeName: requiredAxis(label + ".typeName", input.typeName),
    knownFieldProtobuf: new Uint8Array(input.bytes),
  });
}

function canonicalSecurityEpochs(epochs: TrustAxes["securityEpochs"]) {
  if (!Array.isArray(epochs) || epochs.length > 32) {
    throw new Error("command_envelope_security_epochs_invalid");
  }
  const sorted = [...epochs].sort((left, right) => compare(left.axis, right.axis));
  const seen = new Set<string>();
  return sorted.map(({ axis, value }) => {
    const canonicalAxis = requiredAxis("securityEpoch.axis", axis);
    if (seen.has(canonicalAxis)) throw new Error("command_envelope_security_epoch_duplicate");
    if (typeof value !== "bigint" || value < 0n || value > 18446744073709551615n) {
      throw new Error("command_envelope_security_epoch_value_invalid:" + canonicalAxis);
    }
    seen.add(canonicalAxis);
    return create(CanonicalSecurityEpochV2Schema, { axis: canonicalAxis, value });
  });
}

function canonicalCommandEnvelopeV2(input: CommandEnvelopeInput): CanonicalCommandEnvelopeV2 {
  const trust = create(CanonicalCommandTrustAxesV2Schema, {
    workloadIdentityRef: optionalAxis("workloadIdentityRef", input.trust.workloadIdentityRef),
    audience: optionalAxis("audience", input.trust.audience),
    environment: requiredAxis("environment", input.trust.environment),
    region: requiredAxis("region", input.trust.region),
    siteRef: optionalAxis("siteRef", input.trust.siteRef),
    actorRef: optionalAxis("actorRef", input.trust.actorRef),
    actorSessionRef: optionalAxis("actorSessionRef", input.trust.actorSessionRef),
    managedDeviceRef: optionalAxis("managedDeviceRef", input.trust.managedDeviceRef),
    actorGeneration: optionalUint64("actorGeneration", input.trust.actorGeneration),
    assuranceLevel: input.trust.assuranceLevel,
    factorClasses: input.trust.factorClasses === undefined
      ? []
      : uniqueSorted("factorClass", input.trust.factorClasses, 16),
    authenticatedAt: optionalInstant("authenticatedAt", input.trust.authenticatedAt),
    stepUpAt: optionalInstant("stepUpAt", input.trust.stepUpAt),
    operatorAttestationRef: optionalAxis(
      "operatorAttestationRef",
      input.trust.operatorAttestationRef,
    ),
    operatorAttestationDigest: optionalSha256(
      "operatorAttestationDigest",
      input.trust.operatorAttestationDigest,
    ),
    securityEpochs: canonicalSecurityEpochs(input.trust.securityEpochs),
  });
  return create(CanonicalCommandEnvelopeV2Schema, {
    contractVersion: requiredAxis("contractVersion", input.contractVersion),
    operation: requiredAxis("operation", input.operation),
    trust,
    ...(input.scope === undefined ? {} : { scope: canonicalTyped("scope", input.scope) }),
    targetRefs: uniqueSorted("targetRef", input.targetRefs),
    effect: canonicalTyped("effect", input.effect),
  });
}

function commandEnvelopeV2Digest(input: CommandEnvelopeInput): string {
  const envelope = canonicalCommandEnvelopeV2(input);
  const hash = createHash("sha256");
  hash.update(CanonicalCommandEnvelopeV2Schema.typeName, "utf8");
  hash.update(Uint8Array.of(0));
  hash.update(toBinary(CanonicalCommandEnvelopeV2Schema, envelope, { writeUnknownFields: false }));
  return hash.digest("hex");
}
`;
}

function authenticatedCommandDigestSource() {
  return `
import {
  BreakGlassScopeSchema,
  GlobalScopeSchema,
  OperatorScopeSchema,
  SiteScopeSchema,
  type AuthenticatedOperatorCommandContext,
  type OperatorScope,
} from "./kokoro/platform/admin/v2/admin_shared_pb.js";

export type VerifiedAuthenticatedAdminAxes = Readonly<{
  workloadIdentityRef: string;
  audience: string;
  actorRef: string;
  operatorSessionRef: string;
  environment: string;
  region: string;
  managedDeviceRef: string;
  operatorGeneration: bigint;
  assuranceLevel: OperatorAssuranceLevel;
  factorClasses: readonly string[];
  authenticatedAt: CanonicalInstant;
  stepUpAt?: CanonicalInstant;
  operatorAttestationRef: string;
  operatorAttestationDigest: string;
}>;

function canonicalOperatorScope(
  scope: OperatorScope | undefined,
  environment: string,
  region: string,
): OperatorScope {
  if (scope === undefined || scope.kind.case === undefined) {
    throw new Error("command_envelope_scope_missing");
  }
  switch (scope.kind.case) {
    case "site": {
      const value = scope.kind.value;
      assertAxisMatch("scope.environment", value.environment, environment);
      assertAxisMatch("scope.region", value.region, region);
      return create(OperatorScopeSchema, {
        kind: {
          case: "site",
          value: create(SiteScopeSchema, {
            siteIds: uniqueSorted("scope.siteId", value.siteIds),
            environment: value.environment,
            region: value.region,
          }),
        },
      });
    }
    case "global": {
      const value = scope.kind.value;
      assertAxisMatch("scope.environment", value.environment, environment);
      assertAxisMatch("scope.region", value.region, region);
      return create(OperatorScopeSchema, {
        kind: {
          case: "global",
          value: create(GlobalScopeSchema, {
            grantId: requiredAxis("scope.grantId", value.grantId),
            environment: value.environment,
            region: value.region,
          }),
        },
      });
    }
    case "breakglass": {
      const value = scope.kind.value;
      assertAxisMatch("scope.environment", value.environment, environment);
      assertAxisMatch("scope.region", value.region, region);
      if (value.expiresAt === undefined) throw new Error("command_envelope_scope_expiry_missing");
      return create(OperatorScopeSchema, {
        kind: {
          case: "breakglass",
          value: create(BreakGlassScopeSchema, {
            grantId: requiredAxis("scope.grantId", value.grantId),
            incidentId: requiredAxis("scope.incidentId", value.incidentId),
            environment: value.environment,
            region: value.region,
            authorizedOperation: requiredAxis("scope.authorizedOperation", value.authorizedOperation),
            resourceRefs: uniqueSorted("scope.resourceRef", value.resourceRefs),
            fieldAllowlist: uniqueSorted("scope.field", value.fieldAllowlist),
            expiresAt: value.expiresAt,
          }),
        },
      });
    }
  }
}

function authenticatedEnvelope(
  contractVersion: string,
  operation: string,
  context: AuthenticatedOperatorCommandContext,
  effect: TypedPayload,
  targetRefs: readonly string[],
  verified: VerifiedAuthenticatedAdminAxes,
): string {
  if (context.command === undefined) throw new Error("command_envelope_command_identity_missing");
  if (context.securityEpochs === undefined) throw new Error("command_envelope_security_epochs_missing");
  const environment = assertAxisMatch("environment", context.environment, verified.environment);
  const region = assertAxisMatch("region", context.region, verified.region);
  const actorRef = assertAxisMatch("actorRef", context.actorRef, verified.actorRef);
  const actorSessionRef = assertAxisMatch(
    "operatorSessionRef",
    context.operatorSessionRef,
    verified.operatorSessionRef,
  );
  const managedDeviceRef = assertAxisMatch(
    "managedDeviceRef",
    context.managedDeviceRef,
    verified.managedDeviceRef,
  );
  const actorGeneration = assertUint64Match(
    "operatorGeneration",
    context.operatorGeneration,
    verified.operatorGeneration,
  );
  const assuranceLevel = assertAssuranceMatch(
    "assuranceLevel",
    context.assuranceLevel,
    verified.assuranceLevel,
  );
  const factorClasses = assertCollectionMatch(
    "factorClass",
    context.factorClasses,
    verified.factorClasses,
    16,
  );
  const authenticatedAt = assertInstantMatch(
    "authenticatedAt",
    context.authenticatedAt,
    verified.authenticatedAt,
    true,
  );
  const stepUpAt = assertInstantMatch("stepUpAt", context.stepUpAt, verified.stepUpAt, false);
  const operatorAttestationRef = assertAxisMatch(
    "operatorAttestationRef",
    context.operatorAttestationRef,
    verified.operatorAttestationRef,
  );
  const operatorAttestationDigest = assertSha256Match(
    "operatorAttestationDigest",
    context.operatorAttestationDigest,
    verified.operatorAttestationDigest,
  );
  const canonicalScope = canonicalOperatorScope(context.scope, environment, region);
  const epochs = context.securityEpochs;
  return commandEnvelopeV2Digest({
    contractVersion,
    operation,
    trust: {
      workloadIdentityRef: requiredAxis("verified.workloadIdentityRef", verified.workloadIdentityRef),
      audience: requiredAxis("verified.audience", verified.audience),
      environment,
      region,
      actorRef,
      actorSessionRef,
      managedDeviceRef,
      actorGeneration,
      assuranceLevel,
      factorClasses,
      ...(authenticatedAt === undefined ? {} : { authenticatedAt }),
      ...(stepUpAt === undefined ? {} : { stepUpAt }),
      operatorAttestationRef,
      operatorAttestationDigest,
      securityEpochs: [
        { axis: "operator", value: epochs.operatorSecurityEpoch },
        { axis: "policy", value: epochs.policyEpoch },
        { axis: "restriction", value: epochs.restrictionEpoch },
        { axis: "session", value: epochs.sessionEpoch },
        ...(epochs.siteSecurityEpoch === undefined
          ? []
          : [{ axis: "site", value: epochs.siteSecurityEpoch }]),
      ],
    },
    scope: {
      typeName: OperatorScopeSchema.typeName,
      bytes: toBinary(OperatorScopeSchema, canonicalScope, { writeUnknownFields: false }),
    },
    targetRefs,
    effect,
  });
}
`;
}

function identityCommandDigestSource() {
  return `${authenticatedCommandDigestSource()}
import {
  BeginOperatorLoginEffectSchema,
  BeginStepUpEffectSchema,
  CompleteStepUpEffectSchema,
  ExchangeOidcSessionEffectSchema,
  SignOutEffectSchema,
  type AdminAuthTransactionContext,
  type AdminPreLoginWorkloadContext,
  type BeginOperatorLoginEffect,
  type BeginStepUpEffect,
  type CompleteStepUpEffect,
  type ExchangeOidcSessionEffect,
  type SignOutEffect,
} from "./kokoro/platform/identity/v1/admin_identity_pb.js";

export type VerifiedAdminWorkloadAxes = Readonly<{
  workloadIdentityRef: string;
  audience: string;
  environment: string;
  region: string;
  managedDeviceRef: string;
}>;

type WorkloadContext = AdminPreLoginWorkloadContext | AdminAuthTransactionContext;

function workloadEnvelope(
  operation: string,
  context: WorkloadContext,
  effect: TypedPayload,
  targetRefs: readonly string[],
  verified: VerifiedAdminWorkloadAxes,
): string {
  if (context.command === undefined) throw new Error("command_envelope_command_identity_missing");
  return commandEnvelopeV2Digest({
    contractVersion: "platform-admin-identity@v1",
    operation,
    trust: {
      workloadIdentityRef: assertAxisMatch(
        "workloadIdentityRef",
        context.workloadIdentityRef,
        verified.workloadIdentityRef,
      ),
      audience: assertAxisMatch("audience", context.audience, verified.audience),
      environment: assertAxisMatch("environment", context.environment, verified.environment),
      region: assertAxisMatch("region", context.region, verified.region),
      managedDeviceRef: assertAxisMatch(
        "managedDeviceRef",
        context.managedDeviceRef,
        verified.managedDeviceRef,
      ),
      securityEpochs: [],
    },
    targetRefs,
    effect,
  });
}

export function beginOperatorLoginRequestDigest(
  context: AdminPreLoginWorkloadContext,
  effect: BeginOperatorLoginEffect,
  verified: VerifiedAdminWorkloadAxes,
): string {
  return workloadEnvelope(
    "kokoro.platform.identity.v1.AdminIdentityService/BeginOperatorLogin",
    context,
    { typeName: BeginOperatorLoginEffectSchema.typeName, bytes: toBinary(BeginOperatorLoginEffectSchema, effect, { writeUnknownFields: false }) },
    [effect.returnIntentRef],
    verified,
  );
}

export function exchangeOidcSessionRequestDigest(
  context: AdminAuthTransactionContext,
  effect: ExchangeOidcSessionEffect,
  verified: VerifiedAdminWorkloadAxes,
): string {
  return workloadEnvelope(
    "kokoro.platform.identity.v1.AdminIdentityService/ExchangeOidcSession",
    context,
    { typeName: ExchangeOidcSessionEffectSchema.typeName, bytes: toBinary(ExchangeOidcSessionEffectSchema, effect, { writeUnknownFields: false }) },
    [effect.transactionRef],
    verified,
  );
}

export function beginStepUpRequestDigest(
  context: AuthenticatedOperatorCommandContext,
  effect: BeginStepUpEffect,
  verified: VerifiedAuthenticatedAdminAxes,
): string {
  const resources = uniqueSorted("effect.resourceRef", effect.resourceRefs);
  const canonicalEffect = create(BeginStepUpEffectSchema, {
    requestedOperation: effect.requestedOperation,
    resourceRefs: resources,
    callbackRef: effect.callbackRef,
  });
  return authenticatedEnvelope(
    "platform-admin-identity@v1",
    "kokoro.platform.identity.v1.AdminIdentityService/BeginStepUp",
    context,
    { typeName: BeginStepUpEffectSchema.typeName, bytes: toBinary(BeginStepUpEffectSchema, canonicalEffect, { writeUnknownFields: false }) },
    resources,
    verified,
  );
}

export function completeStepUpRequestDigest(
  context: AuthenticatedOperatorCommandContext,
  effect: CompleteStepUpEffect,
  verified: VerifiedAuthenticatedAdminAxes,
): string {
  return authenticatedEnvelope(
    "platform-admin-identity@v1",
    "kokoro.platform.identity.v1.AdminIdentityService/CompleteStepUp",
    context,
    { typeName: CompleteStepUpEffectSchema.typeName, bytes: toBinary(CompleteStepUpEffectSchema, effect, { writeUnknownFields: false }) },
    [effect.transactionRef],
    verified,
  );
}

export function signOutRequestDigest(
  context: AuthenticatedOperatorCommandContext,
  effect: SignOutEffect,
  verified: VerifiedAuthenticatedAdminAxes,
): string {
  return authenticatedEnvelope(
    "platform-admin-identity@v1",
    "kokoro.platform.identity.v1.AdminIdentityService/SignOut",
    context,
    { typeName: SignOutEffectSchema.typeName, bytes: toBinary(SignOutEffectSchema, effect, { writeUnknownFields: false }) },
    [effect.operatorSessionRef],
    verified,
  );
}
`;
}

function adminCommandDigestSource() {
  return `${authenticatedCommandDigestSource()}
import {
  DecideApprovalEffectSchema,
  ChangeOperatorAuthoritySchema,
  SubmitCommandEffectSchema,
  type DecideApprovalEffect,
  type SubmitCommandEffect,
} from "./kokoro/platform/admin/v2/admin_command_pb.js";

function canonicalSubmitCommandEffect(effect: SubmitCommandEffect): SubmitCommandEffect {
  if (effect.change === undefined) throw new Error("command_envelope_effect_change_missing");
  return create(SubmitCommandEffectSchema, {
    change: create(ChangeOperatorAuthoritySchema, {
      ...effect.change,
      permissions: uniqueSorted("effect.change.permissions", effect.change.permissions),
      siteIds: uniqueSorted("effect.change.siteIds", effect.change.siteIds),
      environments: uniqueSorted("effect.change.environments", effect.change.environments),
      regions: uniqueSorted("effect.change.regions", effect.change.regions),
    }),
    reason: effect.reason,
  });
}

function submitCommandTargets(effect: SubmitCommandEffect): string[] {
  if (effect.change === undefined) throw new Error("command_envelope_effect_change_missing");
  return [effect.change.operatorRef];
}

export function submitCommandRequestDigest(
  context: AuthenticatedOperatorCommandContext,
  effect: SubmitCommandEffect,
  verified: VerifiedAuthenticatedAdminAxes,
): string {
  const canonicalEffect = canonicalSubmitCommandEffect(effect);
  return authenticatedEnvelope(
    "platform-admin-command@v2",
    "kokoro.platform.admin.v2.AdminCommandService/SubmitCommand",
    context,
    { typeName: SubmitCommandEffectSchema.typeName, bytes: toBinary(SubmitCommandEffectSchema, canonicalEffect, { writeUnknownFields: false }) },
    submitCommandTargets(canonicalEffect),
    verified,
  );
}

export function decideApprovalRequestDigest(
  context: AuthenticatedOperatorCommandContext,
  effect: DecideApprovalEffect,
  verified: VerifiedAuthenticatedAdminAxes,
): string {
  return authenticatedEnvelope(
    "platform-admin-command@v2",
    "kokoro.platform.admin.v2.AdminCommandService/DecideApproval",
    context,
    { typeName: DecideApprovalEffectSchema.typeName, bytes: toBinary(DecideApprovalEffectSchema, effect, { writeUnknownFields: false }) },
    [effect.approvalRef],
    verified,
  );
}
`;
}

function siteLifecycleDigestSource() {
  return `${authenticatedCommandDigestSource()}
import {
  ApproveAndActivateEffectSchema,
  RequestActivationApprovalEffectSchema,
  type ApproveAndActivateEffect,
  type RequestActivationApprovalEffect,
} from "./kokoro/platform/site/v1/site_lifecycle_pb.js";

function siteDigest(
  operation: string,
  context: AuthenticatedOperatorCommandContext,
  effect: TypedPayload,
  targetRefs: readonly string[],
  verified: VerifiedAuthenticatedAdminAxes,
): string {
  return authenticatedEnvelope("platform-site-lifecycle@v1", operation, context, effect, targetRefs, verified);
}

export function requestActivationApprovalRequestDigest(
  context: AuthenticatedOperatorCommandContext, siteId: string,
  effect: RequestActivationApprovalEffect,
  verified: VerifiedAuthenticatedAdminAxes,
): string {
  if (effect.activation === undefined) throw new Error("site_activation_facts_required");
  return siteDigest(
    "kokoro.platform.site.v1.SiteLifecycleService/RequestActivationApproval", context,
    { typeName: RequestActivationApprovalEffectSchema.typeName, bytes: toBinary(RequestActivationApprovalEffectSchema, effect, { writeUnknownFields: false }) },
    [siteId, effect.approvalRef, effect.activation.candidateReleaseRef,
      ...(effect.activation.expectedActiveReleaseRef === undefined ? [] : [effect.activation.expectedActiveReleaseRef])],
    verified,
  );
}

export function approveAndActivateRequestDigest(
  context: AuthenticatedOperatorCommandContext, siteId: string,
  effect: ApproveAndActivateEffect,
  verified: VerifiedAuthenticatedAdminAxes,
): string {
  if (effect.activation === undefined) throw new Error("site_activation_facts_required");
  return siteDigest(
    "kokoro.platform.site.v1.SiteLifecycleService/ApproveAndActivate", context,
    { typeName: ApproveAndActivateEffectSchema.typeName, bytes: toBinary(ApproveAndActivateEffectSchema, effect, { writeUnknownFields: false }) },
    [siteId, effect.approvalRef, effect.activationAttemptRef,
      effect.activation.candidateReleaseRef,
      ...(effect.activation.expectedActiveReleaseRef === undefined ? [] : [effect.activation.expectedActiveReleaseRef])],
    verified,
  );
}
`;
}

function adminCommerceDigestSource() {
  return `${authenticatedCommandDigestSource()}
import {
  CodeBatchActionEffectSchema,
  CreditScopePolicySchema,
  IssueCodeBatchEffectSchema,
  PublishCreditProgramRevisionEffectSchema,
  PublishEntitlementTemplateRevisionEffectSchema,
  PublishOfferEffectSchema,
  PublishRedemptionProgramEffectSchema,
  type CodeBatchActionEffect,
  type IssueCodeBatchEffect,
  type PublishCreditProgramRevisionEffect,
  type PublishEntitlementTemplateRevisionEffect,
  type PublishOfferEffect,
  type PublishRedemptionProgramEffect,
} from "./kokoro/platform/commerce/v1/admin_commerce_pb.js";

function commerceDigest(
  operation: string,
  context: AuthenticatedOperatorCommandContext,
  siteId: string,
  effect: TypedPayload,
  targetRefs: readonly string[],
  verified: VerifiedAuthenticatedAdminAxes,
): string {
  return authenticatedEnvelope(
    "platform-admin-commerce@v1", operation, context, effect, [siteId, ...targetRefs], verified,
  );
}

function canonicalCreditProgramRevisionEffect(
  effect: PublishCreditProgramRevisionEffect,
): PublishCreditProgramRevisionEffect {
  if (effect.scopePolicy === undefined) throw new Error("commerce_credit_scope_policy_required");
  return create(PublishCreditProgramRevisionEffectSchema, {
    ...effect,
    scopePolicy: create(CreditScopePolicySchema, {
      surfaceRefs: uniqueSorted("effect.scopePolicy.surfaceRefs", effect.scopePolicy.surfaceRefs),
      capabilityKeys: uniqueSorted("effect.scopePolicy.capabilityKeys", effect.scopePolicy.capabilityKeys),
      agentRefs: uniqueSorted("effect.scopePolicy.agentRefs", effect.scopePolicy.agentRefs),
      allowUnattributedAgent: effect.scopePolicy.allowUnattributedAgent,
    }),
  });
}

export function publishCreditProgramRevisionRequestDigest(
  context: AuthenticatedOperatorCommandContext, siteId: string,
  effect: PublishCreditProgramRevisionEffect, verified: VerifiedAuthenticatedAdminAxes,
): string {
  const canonicalEffect = canonicalCreditProgramRevisionEffect(effect);
  return commerceDigest(
    "kokoro.platform.commerce.v1.AdminCommerceService/PublishCreditProgramRevision", context, siteId,
    { typeName: PublishCreditProgramRevisionEffectSchema.typeName, bytes: toBinary(PublishCreditProgramRevisionEffectSchema, canonicalEffect, { writeUnknownFields: false }) },
    [canonicalEffect.creditProgramRevisionRef, canonicalEffect.programRef], verified,
  );
}

export function publishEntitlementTemplateRevisionRequestDigest(
  context: AuthenticatedOperatorCommandContext, siteId: string,
  effect: PublishEntitlementTemplateRevisionEffect, verified: VerifiedAuthenticatedAdminAxes,
): string {
  return commerceDigest(
    "kokoro.platform.commerce.v1.AdminCommerceService/PublishEntitlementTemplateRevision", context, siteId,
    { typeName: PublishEntitlementTemplateRevisionEffectSchema.typeName, bytes: toBinary(PublishEntitlementTemplateRevisionEffectSchema, effect, { writeUnknownFields: false }) },
    [effect.entitlementTemplateRevisionRef, effect.templateRef], verified,
  );
}

export function publishOfferRequestDigest(
  context: AuthenticatedOperatorCommandContext, siteId: string,
  effect: PublishOfferEffect, verified: VerifiedAuthenticatedAdminAxes,
): string {
  return commerceDigest(
    "kokoro.platform.commerce.v1.AdminCommerceService/PublishOffer", context, siteId,
    { typeName: PublishOfferEffectSchema.typeName, bytes: toBinary(PublishOfferEffectSchema, effect, { writeUnknownFields: false }) },
    [effect.productVersionRef, effect.fulfillmentProgramRevisionRef,
      ...(effect.planVersion === undefined ? [] : [effect.planVersion.planVersionRef])], verified,
  );
}

export function publishRedemptionProgramRequestDigest(
  context: AuthenticatedOperatorCommandContext, siteId: string,
  effect: PublishRedemptionProgramEffect, verified: VerifiedAuthenticatedAdminAxes,
): string {
  return commerceDigest(
    "kokoro.platform.commerce.v1.AdminCommerceService/PublishRedemptionProgram", context, siteId,
    { typeName: PublishRedemptionProgramEffectSchema.typeName, bytes: toBinary(PublishRedemptionProgramEffectSchema, effect, { writeUnknownFields: false }) },
    [effect.redemptionProgramRevisionRef], verified,
  );
}

export function issueCodeBatchRequestDigest(
  context: AuthenticatedOperatorCommandContext, siteId: string,
  effect: IssueCodeBatchEffect, verified: VerifiedAuthenticatedAdminAxes,
): string {
  return commerceDigest(
    "kokoro.platform.commerce.v1.AdminCommerceService/IssueCodeBatch", context, siteId,
    { typeName: IssueCodeBatchEffectSchema.typeName, bytes: toBinary(IssueCodeBatchEffectSchema, effect, { writeUnknownFields: false }) },
    [effect.batchRef, effect.redemptionProgramRevisionRef], verified,
  );
}

function codeBatchDigest(
  method: string, context: AuthenticatedOperatorCommandContext, siteId: string,
  effect: CodeBatchActionEffect, verified: VerifiedAuthenticatedAdminAxes,
): string {
  return commerceDigest(
    \`kokoro.platform.commerce.v1.AdminCommerceService/\${method}\`, context, siteId,
    { typeName: CodeBatchActionEffectSchema.typeName, bytes: toBinary(CodeBatchActionEffectSchema, effect, { writeUnknownFields: false }) },
    [effect.batchRef], verified,
  );
}

export const approveCodeBatchRequestDigest = (context: AuthenticatedOperatorCommandContext, siteId: string, effect: CodeBatchActionEffect, verified: VerifiedAuthenticatedAdminAxes) => codeBatchDigest("ApproveCodeBatch", context, siteId, effect, verified);
export const activateCodeBatchRequestDigest = (context: AuthenticatedOperatorCommandContext, siteId: string, effect: CodeBatchActionEffect, verified: VerifiedAuthenticatedAdminAxes) => codeBatchDigest("ActivateCodeBatch", context, siteId, effect, verified);
export const abandonCodeBatchRequestDigest = (context: AuthenticatedOperatorCommandContext, siteId: string, effect: CodeBatchActionEffect, verified: VerifiedAuthenticatedAdminAxes) => codeBatchDigest("AbandonCodeBatch", context, siteId, effect, verified);
export const suspendCodeBatchRequestDigest = (context: AuthenticatedOperatorCommandContext, siteId: string, effect: CodeBatchActionEffect, verified: VerifiedAuthenticatedAdminAxes) => codeBatchDigest("SuspendCodeBatch", context, siteId, effect, verified);
export const revokeCodeBatchRequestDigest = (context: AuthenticatedOperatorCommandContext, siteId: string, effect: CodeBatchActionEffect, verified: VerifiedAuthenticatedAdminAxes) => codeBatchDigest("RevokeCodeBatch", context, siteId, effect, verified);
`;
}

function siteProvisioningDigestSource() {
  return `${authenticatedCommandDigestSource()}
import {
  PublishSiteReleaseEffectSchema,
  RegisterSiteEffectSchema,
  type PublishSiteReleaseEffect,
  type RegisterSiteEffect,
} from "./kokoro/platform/site/v1/site_provisioning_pb.js";

export function registerSiteRequestDigest(
  context: AuthenticatedOperatorCommandContext,
  siteId: string,
  effect: RegisterSiteEffect,
  verified: VerifiedAuthenticatedAdminAxes,
): string {
  return authenticatedEnvelope(
    "platform-site-provisioning@v1",
    "kokoro.platform.site.v1.SiteProvisioningService/RegisterSite",
    context,
    { typeName: RegisterSiteEffectSchema.typeName, bytes: toBinary(RegisterSiteEffectSchema, effect, { writeUnknownFields: false }) },
    [siteId, effect.projectBindingRef, effect.repositoryRef, effect.providerProjectRef,
      effect.workloadIdentityRef],
    verified,
  );
}

export function publishSiteReleaseRequestDigest(
  context: AuthenticatedOperatorCommandContext,
  siteId: string,
  effect: PublishSiteReleaseEffect,
  verified: VerifiedAuthenticatedAdminAxes,
): string {
  return authenticatedEnvelope(
    "platform-site-provisioning@v1",
    "kokoro.platform.site.v1.SiteProvisioningService/PublishSiteRelease",
    context,
    { typeName: PublishSiteReleaseEffectSchema.typeName, bytes: toBinary(PublishSiteReleaseEffectSchema, effect, { writeUnknownFields: false }) },
    [siteId, effect.releaseRef, effect.launchProfileRef, effect.modelOptionCatalogRef,
      effect.agentCatalogRef],
    verified,
  );
}
`;
}

function modelControlDigestSource() {
  return `${authenticatedCommandDigestSource()}
import {
  ActivateInventoryEffectSchema,
  ChangeSitePolicyEffectSchema,
  ImportInventoryEffectSchema,
  MaterializeModelOptionsEffectSchema,
  PublishSiteReleaseCatalogEffectSchema,
  type ActivateInventoryEffect,
  type ChangeSitePolicyEffect,
  type ImportInventoryEffect,
  type MaterializeModelOptionsEffect,
  type PublishSiteReleaseCatalogEffect,
} from "./kokoro/platform/model/v1/model_control_pb.js";

function modelControlDigest(
  method: string,
  context: AuthenticatedOperatorCommandContext,
  effect: TypedPayload,
  targetRefs: readonly string[],
  verified: VerifiedAuthenticatedAdminAxes,
): string {
  return authenticatedEnvelope(
    "platform-model-control@v1",
    \`kokoro.platform.model.v1.ModelControlService/\${method}\`,
    context,
    effect,
    targetRefs,
    verified,
  );
}

export function importInventoryRequestDigest(
  context: AuthenticatedOperatorCommandContext,
  effect: ImportInventoryEffect,
  verified: VerifiedAuthenticatedAdminAxes,
): string {
  return modelControlDigest("ImportInventory", context,
    { typeName: ImportInventoryEffectSchema.typeName, bytes: toBinary(ImportInventoryEffectSchema, effect, { writeUnknownFields: false }) },
    [effect.inventory?.sourceReference ?? ""], verified);
}

export function activateInventoryRequestDigest(
  context: AuthenticatedOperatorCommandContext,
  effect: ActivateInventoryEffect,
  verified: VerifiedAuthenticatedAdminAxes,
): string {
  return modelControlDigest("ActivateInventory", context,
    { typeName: ActivateInventoryEffectSchema.typeName, bytes: toBinary(ActivateInventoryEffectSchema, effect, { writeUnknownFields: false }) },
    [effect.targetDigest], verified);
}

export function changeSitePolicyRequestDigest(
  context: AuthenticatedOperatorCommandContext,
  siteId: string,
  effect: ChangeSitePolicyEffect,
  verified: VerifiedAuthenticatedAdminAxes,
): string {
  return modelControlDigest("ChangeSitePolicy", context,
    { typeName: ChangeSitePolicyEffectSchema.typeName, bytes: toBinary(ChangeSitePolicyEffectSchema, effect, { writeUnknownFields: false }) },
    [siteId], verified);
}

export function materializeModelOptionsRequestDigest(
  context: AuthenticatedOperatorCommandContext,
  effect: MaterializeModelOptionsEffect,
  verified: VerifiedAuthenticatedAdminAxes,
): string {
  return modelControlDigest("MaterializeModelOptions", context,
    { typeName: MaterializeModelOptionsEffectSchema.typeName, bytes: toBinary(MaterializeModelOptionsEffectSchema, effect, { writeUnknownFields: false }) },
    [effect.inventoryDigest, ...effect.options.map(({ optionKey }) => optionKey)], verified);
}

export function publishSiteReleaseCatalogRequestDigest(
  context: AuthenticatedOperatorCommandContext,
  siteId: string,
  effect: PublishSiteReleaseCatalogEffect,
  verified: VerifiedAuthenticatedAdminAxes,
): string {
  return modelControlDigest("PublishSiteReleaseCatalog", context,
    { typeName: PublishSiteReleaseCatalogEffectSchema.typeName, bytes: toBinary(PublishSiteReleaseCatalogEffectSchema, effect, { writeUnknownFields: false }) },
    [siteId, effect.siteReleaseRef, effect.inventoryDigest], verified);
}
`;
}

function commandEnvelopeDigestSource(kind) {
  const wrappers = {
    identity: identityCommandDigestSource,
    "admin-command": adminCommandDigestSource,
    "site-lifecycle": siteLifecycleDigestSource,
    "site-provisioning": siteProvisioningDigestSource,
    "admin-commerce": adminCommerceDigestSource,
    "model-control": modelControlDigestSource,
  };
  const wrapper = wrappers[kind];
  if (wrapper === undefined) throw new Error("command_envelope_digest_boundary_unknown");
  return commandEnvelopeDigestCoreSource() + wrapper();
}

function singleOutputTemplate(output) {
  return `version: v2\nclean: true\nplugins:\n  - local: protoc-gen-es\n    out: ${JSON.stringify(output)}\n    include_imports: true\n    opt:\n      - target=ts\n      - import_extension=js\n`;
}

async function runBufGenerate(output, boundary) {
  const command = process.platform === "win32" ? "pnpm.cmd" : "pnpm";
  const paths = boundary.inputs.flatMap((path) => ["--path", path]);
  if (output === null) {
    await execFileAsync(command, ["exec", "buf", "generate", ...paths], {
      cwd: contractRoot,
      timeout: 120_000,
      maxBuffer: 1024 * 1024,
    });
    return defaultMirrors;
  }

  const temporary = await mkdtemp(resolve(tmpdir(), "kokoro-buf-template-"));
  const template = resolve(temporary, "buf.gen.yaml");
  try {
    await writeFile(template, singleOutputTemplate(output), "utf8");
    await execFileAsync(command, ["exec", "buf", "generate", "--template", template, ...paths], {
      cwd: contractRoot,
      timeout: 120_000,
      maxBuffer: 1024 * 1024,
    });
  } finally {
    await rm(temporary, { recursive: true, force: true });
  }
  return [output];
}

async function normalizeGeneratedProtobuf(mirror) {
  const files = await artifactFiles(mirror);
  await Promise.all(files.filter((path) => path.endsWith("_pb.ts")).map(async (path) => {
    const source = await readFile(path, "utf8");
    await writeFile(path, source.replace(/\n+$/u, "\n"), "utf8");
  }));
}

async function generate(options) {
  const boundary = BOUNDARIES[options.boundary];
  const mirrors = await runBufGenerate(options.output, boundary);
  await Promise.all(mirrors.map(normalizeGeneratedProtobuf));
  if (boundary.helper === "admin-auth-effect-digest.ts") {
    const digestSource = adminAuthEffectDigestSource();
    await Promise.all(mirrors.map((mirror) => writeFile(resolve(mirror, boundary.helper), digestSource, "utf8")));
  }
  if (boundary.helper === "model-stream-frame-digest.ts") {
    const digestSource = modelStreamFrameDigestSource();
    await Promise.all(mirrors.map((mirror) => writeFile(resolve(mirror, boundary.helper), digestSource, "utf8")));
  }
  if (boundary.commandEnvelopeDigest) {
    const digestSource = commandEnvelopeDigestSource(boundary.commandEnvelopeDigest);
    await Promise.all(
      mirrors.map((mirror) => writeFile(resolve(mirror, "command-envelope-digest.ts"), digestSource, "utf8")),
    );
  }
  if (boundary.errorContract === "model-control-admin") {
    const errorSource = modelControlAdminErrorContractSource();
    await Promise.all(
      mirrors.map((mirror) => writeFile(resolve(mirror, "model-control-errors.ts"), errorSource, "utf8")),
    );
  }
  const metadata = await Promise.all(mirrors.map((mirror) => contractMetadata(mirror, boundary)));
  if (metadata.some(({ artifactDigestSha256 }) => artifactDigestSha256 !== metadata[0].artifactDigestSha256)) {
    throw new Error("contract_generation_artifact_mismatch");
  }
  const source = metadataSource(metadata[0]);
  await Promise.all(mirrors.map((mirror) => writeFile(resolve(mirror, "contract-metadata.ts"), source, "utf8")));
}

if (process.argv[1] && pathToFileURL(process.argv[1]).href === import.meta.url) {
  try {
    await generate(parseArguments(process.argv.slice(2)));
  } catch {
    process.stderr.write("contract_generation_failed\n");
    process.exitCode = 1;
  }
}

export {
  adminAuthEffectDigestSource,
  commandEnvelopeDigestSource,
  contractMetadata,
  generate,
  metadataSource,
  modelControlAdminErrorContractSource,
  modelStreamFrameDigestSource,
  parseArguments,
};
