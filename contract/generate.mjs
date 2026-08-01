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
      "kokoro/platform/credit/v1/credit_catalog.proto",
    ]),
    helper: null,
    commandEnvelopeDigest: "admin-credit",
  }),
  "platform-credit-application@v1": Object.freeze({
    schema: "kokoro.platform.credit.v1.CreditApplicationService",
    version: 1,
    inputs: Object.freeze(["proto/kokoro/platform/credit/v1/credit_application.proto"]),
    sources: Object.freeze([
      "kokoro/common/v2/command_envelope.proto",
      "kokoro/platform/credit/v1/credit_application.proto",
    ]),
    helper: null,
    commandEnvelopeDigest: "credit-application",
  }),
  "platform-site-lifecycle@v1": Object.freeze({
    schema: "kokoro.platform.site.v1.SiteLifecycleService",
    version: 1,
    inputs: Object.freeze(["proto/kokoro/platform/site/v1/site_lifecycle.proto"]),
    sources: Object.freeze([
      "kokoro/common/v1/error.proto",
      "kokoro/common/v2/command_envelope.proto",
      "kokoro/platform/admin/v2/admin_shared.proto",
      "kokoro/platform/publication/v1/publication_common.proto",
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
  "platform-product-catalog-publication@v1": Object.freeze({
    schema: "kokoro.platform.product.v1.ProductCatalogPublicationService",
    version: 1,
    inputs: Object.freeze(["proto/kokoro/platform/product/v1/product_catalog_publication.proto"]),
    sources: Object.freeze([
      "kokoro/common/v1/error.proto",
      "kokoro/common/v2/command_envelope.proto",
      "kokoro/platform/admin/v2/admin_shared.proto",
      "kokoro/platform/publication/v1/publication_common.proto",
      "kokoro/platform/product/v1/product_catalog_publication.proto",
    ]),
    helper: null,
    commandEnvelopeDigest: "product-catalog-publication",
  }),
  "platform-site-publication@v1": Object.freeze({
    schema: "kokoro.platform.site.v1.SitePublicationService",
    version: 1,
    inputs: Object.freeze(["proto/kokoro/platform/site/v1/site_publication.proto"]),
    sources: Object.freeze([
      "kokoro/common/v1/error.proto",
      "kokoro/common/v2/command_envelope.proto",
      "kokoro/platform/admin/v2/admin_shared.proto",
      "kokoro/platform/publication/v1/publication_common.proto",
      "kokoro/platform/site/v1/site_publication.proto",
    ]),
    helper: null,
    commandEnvelopeDigest: "site-publication",
  }),
  "platform-site-evidence-admission@v1": Object.freeze({
    schema: "kokoro.platform.site.v1.SiteEvidenceAdmissionService",
    version: 1,
    inputs: Object.freeze(["proto/kokoro/platform/site/v1/site_publication.proto"]),
    sources: Object.freeze([
      "kokoro/common/v1/error.proto",
      "kokoro/common/v2/command_envelope.proto",
      "kokoro/platform/admin/v2/admin_shared.proto",
      "kokoro/platform/publication/v1/publication_common.proto",
      "kokoro/platform/site/v1/site_publication.proto",
    ]),
    helper: null,
    commandEnvelopeDigest: "site-evidence-admission",
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
  "agent-execution-evidence@v2": Object.freeze({
    schema: "kokoro.agent.execution.v2.AgentExecutionEvidenceService",
    version: 2,
    inputs: Object.freeze([
      "proto/kokoro/agent/execution/v2/agent_execution_evidence.proto",
    ]),
    sources: Object.freeze([
      "kokoro/agent/execution/v2/agent_execution_evidence.proto",
    ]),
    helper: null,
    commandEnvelopeDigest: null,
  }),
  "session-agent-control@v2": Object.freeze({
    schema: "kokoro.agent.control.v2.SessionAgentControlRecoveryService",
    version: 2,
    inputs: Object.freeze([
      "proto/kokoro/agent/control/v2/session_agent_control.proto",
    ]),
    sources: Object.freeze([
      "kokoro/agent/control/v2/session_agent_control.proto",
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
      "proto/kokoro/common/v2/command_envelope.proto",
      "proto/kokoro/platform/model/image/v1/image_effect.proto",
    ]),
    sources: Object.freeze([
      "kokoro/common/v1/error.proto",
      "kokoro/common/v2/command_envelope.proto",
      "kokoro/platform/model/image/v1/image_effect.proto",
    ]),
    helper: null,
    commandEnvelopeDigest: "model-image-effect",
  }),
  "session-media-projection@v1": Object.freeze({
    schema: "kokoro.session.media.v1.SessionMediaProjectionService",
    version: 1,
    inputs: Object.freeze([
      "proto/kokoro/session/media/v1/media_projection.proto",
    ]),
    sources: Object.freeze([
      "kokoro/common/v1/projection_integrity.proto",
      "kokoro/platform/credit/v1/cost_projection.proto",
      "kokoro/platform/media/v1/media_projection.proto",
      "kokoro/session/media/v1/media_projection.proto",
    ]),
    helper: null,
    commandEnvelopeDigest: null,
  }),
  "session-media-projection-ingest@v1": Object.freeze({
    schema: "kokoro.session.media.v1.SessionMediaProjectionIngestService",
    version: 1,
    inputs: Object.freeze([
      "proto/kokoro/session/media/v1/media_projection_ingest.proto",
    ]),
    sources: Object.freeze([
      "kokoro/common/v1/projection_integrity.proto",
      "kokoro/platform/credit/v1/cost_projection.proto",
      "kokoro/platform/media/v1/media_projection.proto",
      "kokoro/session/media/v1/media_projection.proto",
      "kokoro/session/media/v1/media_projection_ingest.proto",
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
      "kokoro/common/v1/error.proto",
      "kokoro/common/v1/projection_integrity.proto",
      "kokoro/common/v2/command_envelope.proto",
      "kokoro/platform/media/v1/media_projection.proto",
      "kokoro/platform/media/v1/media_projection_recovery.proto",
    ]),
    helper: null,
    commandEnvelopeDigest: "media-projection-recovery",
  }),
  "platform-credit-cost-projection-recovery@v1": Object.freeze({
    schema: "kokoro.platform.credit.v1.CreditCostProjectionRecoveryService",
    version: 1,
    inputs: Object.freeze([
      "proto/kokoro/platform/credit/v1/cost_projection_recovery.proto",
    ]),
    sources: Object.freeze([
      "kokoro/common/v1/error.proto",
      "kokoro/common/v1/projection_integrity.proto",
      "kokoro/common/v2/command_envelope.proto",
      "kokoro/platform/credit/v1/cost_projection.proto",
      "kokoro/platform/credit/v1/cost_projection_recovery.proto",
    ]),
    helper: null,
    commandEnvelopeDigest: "credit-cost-projection-recovery",
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

function commandEnvelopeDigestCoreSource(boundarySelectivePrimitives = false) {
  const lintDirective = boundarySelectivePrimitives
    ? "/* eslint-disable @typescript-eslint/no-unused-vars -- shared generated digest primitives are intentionally boundary-selective */\n"
    : "";
  return `// @generated by contract/generate.mjs; DO NOT EDIT.
${lintDirective}import { create, toBinary, type DescMessage, type MessageShape } from "@bufbuild/protobuf";
import { createHash } from "node:crypto";
import {
  CanonicalCommandEnvelopeV2Schema,
  CanonicalCommandTrustAxesV2Schema,
  CanonicalSecurityEpochV2Schema,
  CanonicalTypedProtobufV2Schema,
  CommandDigestAlgorithmV2,
  OperatorAssuranceLevel,
  type CanonicalCommandEnvelopeV2,
  type CommandIdentityV2,
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

function requiredUint64AllowZero(label: string, value: unknown): bigint {
  if (typeof value !== "bigint" || value < 0n || value > 18446744073709551615n) {
    throw new Error("command_envelope_uint64_invalid:" + label);
  }
  return value;
}

function assertUint64AllowZeroMatch(label: string, declared: bigint, verified: bigint): bigint {
  const canonicalDeclared = requiredUint64AllowZero(label, declared);
  if (canonicalDeclared !== requiredUint64AllowZero("verified." + label, verified)) {
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

function compareInstants(left: CanonicalInstant, right: CanonicalInstant): number {
  if (left.seconds !== right.seconds) return left.seconds < right.seconds ? -1 : 1;
  return left.nanos < right.nanos ? -1 : left.nanos > right.nanos ? 1 : 0;
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
  if (effect.activation.candidate === undefined || effect.activation.targetRelease === undefined ||
      effect.activation.activePointer === undefined || effect.activation.activePointer.fence === undefined ||
      effect.activation.activePointer.current.case === undefined) throw new Error("site_activation_authority_required");
  return siteDigest(
    "kokoro.platform.site.v1.SiteLifecycleService/RequestActivationApproval", context,
    { typeName: RequestActivationApprovalEffectSchema.typeName, bytes: toBinary(RequestActivationApprovalEffectSchema, effect, { writeUnknownFields: false }) },
    [siteId, effect.approvalRef, effect.activation.candidate.candidateRef,
      effect.activation.targetRelease.ref, effect.activation.activePointer.current.value.pointerRef,
      effect.activation.activePointer.fence.casCommandRef],
    verified,
  );
}

export function approveAndActivateRequestDigest(
  context: AuthenticatedOperatorCommandContext, siteId: string,
  effect: ApproveAndActivateEffect,
  verified: VerifiedAuthenticatedAdminAxes,
): string {
  if (effect.activation === undefined) throw new Error("site_activation_facts_required");
  if (effect.activation.candidate === undefined || effect.activation.targetRelease === undefined ||
      effect.activation.activePointer === undefined || effect.activation.activePointer.fence === undefined ||
      effect.activation.activePointer.current.case === undefined) throw new Error("site_activation_authority_required");
  return siteDigest(
    "kokoro.platform.site.v1.SiteLifecycleService/ApproveAndActivate", context,
    { typeName: ApproveAndActivateEffectSchema.typeName, bytes: toBinary(ApproveAndActivateEffectSchema, effect, { writeUnknownFields: false }) },
    [siteId, effect.approvalRef, effect.activationAttemptRef,
      effect.activation.candidate.candidateRef, effect.activation.targetRelease.ref,
      effect.activation.activePointer.current.value.pointerRef,
      effect.activation.activePointer.fence.casCommandRef],
    verified,
  );
}
`;
}

/* Removed pre-launch Commerce digest generator retained in this source comment
 * only while the hard-cut provider below is reviewed.
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

*/

// Hard-cut provider for the current Commerce control plane. These functions do
// not trust a caller-authored digest inside Effect. They deterministically encode
// the complete typed Effect, rebuild CanonicalCommandEnvelopeV2 from middleware-
// verified axes, and reject unless it equals CommandIdentity.request_digest.
function adminCommerceDigestSourceV2() {
  return `${authenticatedCommandDigestSource()}
import {
  PublishPlanRevisionEffectSchema,
  PublishOfferRevisionEffectSchema,
  PublishFulfillmentProgramRevisionEffectSchema,
  PublishRedemptionProgramRevisionEffectSchema,
  type CommerceGlobalCommandContext,
  type PublishPlanRevisionEffect,
  type PublishOfferRevisionEffect,
  type PublishFulfillmentProgramRevisionEffect,
  type PublishRedemptionProgramRevisionEffect,
} from "./kokoro/platform/commerce/v1/commerce_catalog_pb.js";
import {
  RequestSiteCommerceAssignmentPromotionEffectSchema,
  CommerceApprovalDecisionEffectSchema,
  RequestCodeBatchIssuanceEffectSchema,
  RequestCodeBatchTransitionEffectSchema,
  EmergencySuspendCodeBatchEffectSchema,
  BeginCodeBatchDeliveryEffectSchema,
  LeaseCodeDeliveryRangeEffectSchema,
  AcknowledgeCodeDeliveryRangeEffectSchema,
  RequestSourceCorrectionEffectSchema,
  RequestCommerceReconciliationResolutionEffectSchema,
  type CommerceSiteCommandContext,
  type RequestSiteCommerceAssignmentPromotionEffect,
  type CommerceApprovalDecisionEffect,
  type RequestCodeBatchIssuanceEffect,
  type RequestCodeBatchTransitionEffect,
  type EmergencySuspendCodeBatchEffect,
  type BeginCodeBatchDeliveryEffect,
  type LeaseCodeDeliveryRangeEffect,
  type AcknowledgeCodeDeliveryRangeEffect,
  type RequestSourceCorrectionEffect,
  type RequestCommerceReconciliationResolutionEffect,
} from "./kokoro/platform/commerce/v1/commerce_control_pb.js";

function verifyCommerceEnvelope(
  operation: string,
  context: AuthenticatedOperatorCommandContext,
  effect: TypedPayload,
  targetRefs: readonly string[],
  verified: VerifiedAuthenticatedAdminAxes,
): string {
  if (context.command === undefined) throw new Error("command_envelope_command_identity_missing");
  const recomputed = authenticatedEnvelope(
    "platform-admin-commerce@v1", operation, context, effect, targetRefs, verified,
  );
  if (recomputed !== context.command.requestDigest) {
    throw new Error("command_envelope_request_digest_mismatch");
  }
  return recomputed;
}
`;
}

function adminCreditDigestSource() {
  return `${authenticatedCommandDigestSource()}
import {
  PublishCreditProgramRevisionEffectSchema,
  type CreditGlobalCommandContext,
  type PublishCreditProgramRevisionEffect,
} from "./kokoro/platform/credit/v1/credit_catalog_pb.js";
import {
  RequestCreditReconciliationResolutionEffectSchema,
  CreditReconciliationDecisionEffectSchema,
  type CreditSiteCommandContext,
  type RequestCreditReconciliationResolutionEffect,
  type CreditReconciliationDecisionEffect,
} from "./kokoro/platform/credit/v1/admin_credit_pb.js";

function verifyCreditAdminEnvelope(operation: string, context: AuthenticatedOperatorCommandContext, effect: TypedPayload, targetRefs: readonly string[], verified: VerifiedAuthenticatedAdminAxes): string {
  if (context.command === undefined) throw new Error("command_envelope_command_identity_missing");
  const recomputed = authenticatedEnvelope("platform-admin-credit@v1", operation, context, effect, targetRefs, verified);
  if (recomputed !== context.command.requestDigest) throw new Error("command_envelope_request_digest_mismatch");
  return recomputed;
}
export function verifyPublishCreditProgramRevisionCommand(context: CreditGlobalCommandContext, effect: PublishCreditProgramRevisionEffect, verified: VerifiedAuthenticatedAdminAxes): string {
  if (context.operator === undefined) throw new Error("credit_global_authority_missing");
  return verifyCreditAdminEnvelope("kokoro.platform.credit.v1.AdminCreditService/PublishCreditProgramRevision", context.operator, {typeName: PublishCreditProgramRevisionEffectSchema.typeName, bytes: toBinary(PublishCreditProgramRevisionEffectSchema, effect, {writeUnknownFields: false})}, [effect.target?.programRef ?? ""], verified);
}
export function verifyRequestCreditReconciliationResolutionCommand(context: CreditSiteCommandContext, effect: RequestCreditReconciliationResolutionEffect, verified: VerifiedAuthenticatedAdminAxes): string {
  if (context.operator === undefined) throw new Error("credit_site_authority_missing");
  return verifyCreditAdminEnvelope("kokoro.platform.credit.v1.AdminCreditService/RequestCreditReconciliationResolution", context.operator, {typeName: RequestCreditReconciliationResolutionEffectSchema.typeName, bytes: toBinary(RequestCreditReconciliationResolutionEffectSchema, effect, {writeUnknownFields: false})}, [context.siteId, effect.platformTransactionRef], verified);
}
export function verifyCreditReconciliationDecisionCommand(context: CreditSiteCommandContext, effect: CreditReconciliationDecisionEffect, verified: VerifiedAuthenticatedAdminAxes): string {
  if (context.operator === undefined) throw new Error("credit_site_authority_missing");
  return verifyCreditAdminEnvelope("kokoro.platform.credit.v1.AdminCreditService/DecideCreditReconciliationResolution", context.operator, {typeName: CreditReconciliationDecisionEffectSchema.typeName, bytes: toBinary(CreditReconciliationDecisionEffectSchema, effect, {writeUnknownFields: false})}, [context.siteId, effect.approvalRef], verified);
}
`;
}

function creditApplicationDigestSource() {
  return `
import {
  ReserveCreditEffectSchema,
  CommitCreditReservationEffectSchema,
  SettleCreditReservationEffectSchema,
  ReleaseCreditReservationEffectSchema,
  ReconcileCreditReservationEffectSchema,
  type ReserveCreditEffect,
  type CommitCreditReservationEffect,
  type SettleCreditReservationEffect,
  type ReleaseCreditReservationEffect,
  type ReconcileCreditReservationEffect,
} from "./kokoro/platform/credit/v1/credit_application_pb.js";

export type VerifiedCreditApplicationAxes = Readonly<{
  workloadIdentityRef: string;
  audience: string;
  environment: string;
  region: string;
  siteRef: string;
}>;
function verifyCreditApplicationEnvelope(operation: string, command: CommandIdentityV2 | undefined, namespace: string, effect: TypedPayload, transactionRef: string, verified: VerifiedCreditApplicationAxes): string {
  if (command === undefined) throw new Error("command_envelope_command_identity_missing");
  const recomputed = commandEnvelopeV2Digest({
    contractVersion: "platform-credit-application@v1",
    operation,
    trust: {
      workloadIdentityRef: requiredAxis("verified.workloadIdentityRef", verified.workloadIdentityRef),
      audience: requiredAxis("verified.audience", verified.audience),
      environment: requiredAxis("verified.environment", verified.environment),
      region: requiredAxis("verified.region", verified.region),
      siteRef: requiredAxis("verified.siteRef", verified.siteRef),
      securityEpochs: [],
    },
    targetRefs: [namespace, transactionRef],
    effect,
  });
  if (recomputed !== command.requestDigest) throw new Error("command_envelope_request_digest_mismatch");
  return recomputed;
}
export const verifyReserveCreditCommand = (command: CommandIdentityV2 | undefined, namespace: string, effect: ReserveCreditEffect, verified: VerifiedCreditApplicationAxes) => verifyCreditApplicationEnvelope("kokoro.platform.credit.v1.CreditApplicationService/ReserveCredit", command, namespace, {typeName: ReserveCreditEffectSchema.typeName, bytes: toBinary(ReserveCreditEffectSchema, effect, {writeUnknownFields: false})}, effect.platformTransactionRef, verified);
export const verifyCommitCreditReservationCommand = (command: CommandIdentityV2 | undefined, namespace: string, effect: CommitCreditReservationEffect, verified: VerifiedCreditApplicationAxes) => verifyCreditApplicationEnvelope("kokoro.platform.credit.v1.CreditApplicationService/CommitCreditReservation", command, namespace, {typeName: CommitCreditReservationEffectSchema.typeName, bytes: toBinary(CommitCreditReservationEffectSchema, effect, {writeUnknownFields: false})}, effect.platformTransactionRef, verified);
export const verifySettleCreditReservationCommand = (command: CommandIdentityV2 | undefined, namespace: string, effect: SettleCreditReservationEffect, verified: VerifiedCreditApplicationAxes) => verifyCreditApplicationEnvelope("kokoro.platform.credit.v1.CreditApplicationService/SettleCreditReservation", command, namespace, {typeName: SettleCreditReservationEffectSchema.typeName, bytes: toBinary(SettleCreditReservationEffectSchema, effect, {writeUnknownFields: false})}, effect.platformTransactionRef, verified);
export const verifyReleaseCreditReservationCommand = (command: CommandIdentityV2 | undefined, namespace: string, effect: ReleaseCreditReservationEffect, verified: VerifiedCreditApplicationAxes) => verifyCreditApplicationEnvelope("kokoro.platform.credit.v1.CreditApplicationService/ReleaseCreditReservation", command, namespace, {typeName: ReleaseCreditReservationEffectSchema.typeName, bytes: toBinary(ReleaseCreditReservationEffectSchema, effect, {writeUnknownFields: false})}, effect.platformTransactionRef, verified);
export const verifyReconcileCreditReservationCommand = (command: CommandIdentityV2 | undefined, namespace: string, effect: ReconcileCreditReservationEffect, verified: VerifiedCreditApplicationAxes) => verifyCreditApplicationEnvelope("kokoro.platform.credit.v1.CreditApplicationService/ReconcileCreditReservation", command, namespace, {typeName: ReconcileCreditReservationEffectSchema.typeName, bytes: toBinary(ReconcileCreditReservationEffectSchema, effect, {writeUnknownFields: false})}, effect.platformTransactionRef, verified);
`;
}

function adminCommerceDigestSourceV2Remainder() {
  return `
function globalOperator(context: CommerceGlobalCommandContext): AuthenticatedOperatorCommandContext {
  if (context.operator === undefined) throw new Error("commerce_global_authority_missing");
  return context.operator;
}
function siteOperator(context: CommerceSiteCommandContext): AuthenticatedOperatorCommandContext {
  if (context.operator === undefined) throw new Error("commerce_site_authority_missing");
  return context.operator;
}
function globalEffect<T extends DescMessage>(operation: string, context: CommerceGlobalCommandContext, schema: T, effect: MessageShape<T>, targetRefs: readonly string[], verified: VerifiedAuthenticatedAdminAxes): string {
  return verifyCommerceEnvelope(operation, globalOperator(context), {typeName: schema.typeName, bytes: toBinary(schema, effect, {writeUnknownFields: false})}, targetRefs, verified);
}
function siteEffect<T extends DescMessage>(operation: string, context: CommerceSiteCommandContext, schema: T, effect: MessageShape<T>, targetRefs: readonly string[], verified: VerifiedAuthenticatedAdminAxes): string {
  return verifyCommerceEnvelope(operation, siteOperator(context), {typeName: schema.typeName, bytes: toBinary(schema, effect, {writeUnknownFields: false})}, [context.siteId, ...targetRefs], verified);
}

export const verifyPublishPlanRevisionCommand = (c: CommerceGlobalCommandContext, e: PublishPlanRevisionEffect, v: VerifiedAuthenticatedAdminAxes) => globalEffect("kokoro.platform.commerce.v1.AdminCommerceService/PublishPlanRevision", c, PublishPlanRevisionEffectSchema, e, [e.target?.targetRef ?? ""], v);
export const verifyPublishOfferRevisionCommand = (c: CommerceGlobalCommandContext, e: PublishOfferRevisionEffect, v: VerifiedAuthenticatedAdminAxes) => globalEffect("kokoro.platform.commerce.v1.AdminCommerceService/PublishOfferRevision", c, PublishOfferRevisionEffectSchema, e, [e.target?.targetRef ?? ""], v);
export const verifyPublishFulfillmentProgramRevisionCommand = (c: CommerceGlobalCommandContext, e: PublishFulfillmentProgramRevisionEffect, v: VerifiedAuthenticatedAdminAxes) => globalEffect("kokoro.platform.commerce.v1.AdminCommerceService/PublishFulfillmentProgramRevision", c, PublishFulfillmentProgramRevisionEffectSchema, e, [e.target?.targetRef ?? ""], v);
export const verifyPublishRedemptionProgramRevisionCommand = (c: CommerceGlobalCommandContext, e: PublishRedemptionProgramRevisionEffect, v: VerifiedAuthenticatedAdminAxes) => globalEffect("kokoro.platform.commerce.v1.AdminCommerceService/PublishRedemptionProgramRevision", c, PublishRedemptionProgramRevisionEffectSchema, e, [e.target?.targetRef ?? ""], v);
export const verifyRequestSiteCommerceAssignmentPromotionCommand = (c: CommerceSiteCommandContext, e: RequestSiteCommerceAssignmentPromotionEffect, v: VerifiedAuthenticatedAdminAxes) => siteEffect("kokoro.platform.commerce.v1.AdminCommerceService/RequestSiteCommerceAssignmentPromotion", c, RequestSiteCommerceAssignmentPromotionEffectSchema, e, [e.candidate?.target?.targetRef ?? ""], v);
export const verifyRequestCodeBatchIssuanceCommand = (c: CommerceSiteCommandContext, e: RequestCodeBatchIssuanceEffect, v: VerifiedAuthenticatedAdminAxes) => siteEffect("kokoro.platform.commerce.v1.AdminCommerceService/RequestCodeBatchIssuance", c, RequestCodeBatchIssuanceEffectSchema, e, [e.target?.targetRef ?? ""], v);
export const verifyRequestCodeBatchTransitionCommand = (c: CommerceSiteCommandContext, e: RequestCodeBatchTransitionEffect, v: VerifiedAuthenticatedAdminAxes) => siteEffect("kokoro.platform.commerce.v1.AdminCommerceService/RequestCodeBatchTransition", c, RequestCodeBatchTransitionEffectSchema, e, [e.target?.targetRef ?? ""], v);
export const verifyEmergencySuspendCodeBatchCommand = (c: CommerceSiteCommandContext, e: EmergencySuspendCodeBatchEffect, v: VerifiedAuthenticatedAdminAxes) => siteEffect("kokoro.platform.commerce.v1.AdminCommerceService/EmergencySuspendCodeBatch", c, EmergencySuspendCodeBatchEffectSchema, e, [e.target?.targetRef ?? ""], v);
export const verifyBeginCodeBatchDeliveryCommand = (c: CommerceSiteCommandContext, e: BeginCodeBatchDeliveryEffect, v: VerifiedAuthenticatedAdminAxes) => siteEffect("kokoro.platform.commerce.v1.AdminCommerceService/BeginCodeBatchDelivery", c, BeginCodeBatchDeliveryEffectSchema, e, [e.batchRef], v);
export const verifyReadCodeDeliveryRangeCommand = (c: CommerceSiteCommandContext, e: LeaseCodeDeliveryRangeEffect, v: VerifiedAuthenticatedAdminAxes) => siteEffect("kokoro.platform.commerce.v1.AdminCommerceService/ReadCodeDeliveryRange", c, LeaseCodeDeliveryRangeEffectSchema, e, [e.sessionRef], v);
export const verifyAcknowledgeCodeDeliveryRangeCommand = (c: CommerceSiteCommandContext, e: AcknowledgeCodeDeliveryRangeEffect, v: VerifiedAuthenticatedAdminAxes) => siteEffect("kokoro.platform.commerce.v1.AdminCommerceService/AcknowledgeCodeDeliveryRange", c, AcknowledgeCodeDeliveryRangeEffectSchema, e, [e.sessionRef, e.leaseRef], v);
export const verifyRequestSourceCorrectionCommand = (c: CommerceSiteCommandContext, e: RequestSourceCorrectionEffect, v: VerifiedAuthenticatedAdminAxes) => siteEffect("kokoro.platform.commerce.v1.AdminCommerceService/RequestSourceCorrection", c, RequestSourceCorrectionEffectSchema, e, [e.target?.targetRef ?? ""], v);
export const verifyRequestCommerceReconciliationResolutionCommand = (c: CommerceSiteCommandContext, e: RequestCommerceReconciliationResolutionEffect, v: VerifiedAuthenticatedAdminAxes) => siteEffect("kokoro.platform.commerce.v1.AdminCommerceService/RequestCommerceReconciliationResolution", c, RequestCommerceReconciliationResolutionEffectSchema, e, [e.target?.targetRef ?? ""], v);
export const verifyCommerceApprovalDecisionCommand = (operation: string, c: CommerceSiteCommandContext, e: CommerceApprovalDecisionEffect, v: VerifiedAuthenticatedAdminAxes) => siteEffect(operation, c, CommerceApprovalDecisionEffectSchema, e, [e.approvalRef], v);
`;
}

/* Removed pre-launch Commerce digest generator remainder.
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

*/

function siteProvisioningDigestSource() {
  return `${authenticatedCommandDigestSource()}
import {
  RegisterSiteEffectSchema,
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
`;
}

function productCatalogPublicationDigestSource() {
  return `${authenticatedCommandDigestSource()}
import {
  PublishLaunchProductProfileEffectSchema,
  PublishProductSurfaceCatalogEffectSchema,
  type PublishLaunchProductProfileEffect,
  type PublishProductSurfaceCatalogEffect,
} from "./kokoro/platform/product/v1/product_catalog_publication_pb.js";

function productCatalogPublicationDigest(
  method: string, context: AuthenticatedOperatorCommandContext, effect: TypedPayload,
  targetRefs: readonly string[], verified: VerifiedAuthenticatedAdminAxes,
): string {
  return authenticatedEnvelope(
    "platform-product-catalog-publication@v1",
    \`kokoro.platform.product.v1.ProductCatalogPublicationService/\${method}\`,
    context, effect, targetRefs, verified,
  );
}

export function publishProductSurfaceCatalogRequestDigest(
  context: AuthenticatedOperatorCommandContext, effect: PublishProductSurfaceCatalogEffect,
  verified: VerifiedAuthenticatedAdminAxes,
): string {
  if (effect.catalogRevision === undefined) throw new Error("product_catalog_revision_required");
  return productCatalogPublicationDigest("PublishProductSurfaceCatalog", context,
    { typeName: PublishProductSurfaceCatalogEffectSchema.typeName, bytes: toBinary(PublishProductSurfaceCatalogEffectSchema, effect, { writeUnknownFields: false }) },
    [effect.catalogRevision.ref], verified);
}

export function publishLaunchProductProfileRequestDigest(
  context: AuthenticatedOperatorCommandContext, effect: PublishLaunchProductProfileEffect,
  verified: VerifiedAuthenticatedAdminAxes,
): string {
  if (effect.profileRevision === undefined || effect.productSurfaceCatalog === undefined) throw new Error("launch_profile_owner_bindings_required");
  return productCatalogPublicationDigest("PublishLaunchProductProfile", context,
    { typeName: PublishLaunchProductProfileEffectSchema.typeName, bytes: toBinary(PublishLaunchProductProfileEffectSchema, effect, { writeUnknownFields: false }) },
    [effect.profileRevision.ref, effect.productSurfaceCatalog.ref], verified);
}
`;
}

function sitePublicationDigestSource() {
  return `${authenticatedCommandDigestSource()}
import {
  AuthorizeSiteReleaseCandidateEffectSchema,
  IssueWebBuildIntentEffectSchema,
  PublishReleaseCertificationEffectSchema,
  PublishSiteReleaseEffectSchema,
  PublishSurfaceInventoryEffectSchema,
  PublishWebBuildMaterialBundleEffectSchema,
  type AuthorizeSiteReleaseCandidateEffect,
  type IssueWebBuildIntentEffect,
  type PublishReleaseCertificationEffect,
  type PublishSiteReleaseEffect,
  type PublishSurfaceInventoryEffect,
  type PublishWebBuildMaterialBundleEffect,
} from "./kokoro/platform/site/v1/site_publication_pb.js";

function sitePublicationDigest(
  method: string, context: AuthenticatedOperatorCommandContext, siteId: string,
  effect: TypedPayload, targetRefs: readonly string[],
  verified: VerifiedAuthenticatedAdminAxes,
): string {
  return authenticatedEnvelope(
    "platform-site-publication@v1", \`kokoro.platform.site.v1.SitePublicationService/\${method}\`,
    context, effect, [siteId, ...targetRefs], verified,
  );
}

export function authorizeSiteReleaseCandidateRequestDigest(context: AuthenticatedOperatorCommandContext, siteId: string, effect: AuthorizeSiteReleaseCandidateEffect, verified: VerifiedAuthenticatedAdminAxes): string {
  if (effect.launchProductProfile === undefined || effect.productSurfaceCatalog === undefined) throw new Error("site_candidate_owner_bindings_required");
  return sitePublicationDigest("AuthorizeSiteReleaseCandidate", context, siteId,
    { typeName: AuthorizeSiteReleaseCandidateEffectSchema.typeName, bytes: toBinary(AuthorizeSiteReleaseCandidateEffectSchema, effect, { writeUnknownFields: false }) },
    [effect.candidateRef, effect.launchProductProfile.ref, effect.productSurfaceCatalog.ref], verified);
}

export function publishSurfaceInventoryRequestDigest(context: AuthenticatedOperatorCommandContext, siteId: string, effect: PublishSurfaceInventoryEffect, verified: VerifiedAuthenticatedAdminAxes): string {
  if (effect.candidate === undefined || effect.surfaceInventory === undefined) throw new Error("surface_inventory_owner_bindings_required");
  return sitePublicationDigest("PublishSurfaceInventory", context, siteId,
    { typeName: PublishSurfaceInventoryEffectSchema.typeName, bytes: toBinary(PublishSurfaceInventoryEffectSchema, effect, { writeUnknownFields: false }) },
    [effect.candidate.candidateRef, effect.surfaceInventory.ref], verified);
}

export function publishWebBuildMaterialBundleRequestDigest(context: AuthenticatedOperatorCommandContext, siteId: string, effect: PublishWebBuildMaterialBundleEffect, verified: VerifiedAuthenticatedAdminAxes): string {
  if (effect.candidate === undefined || effect.webBuildMaterialBundle === undefined) throw new Error("web_build_material_owner_bindings_required");
  return sitePublicationDigest("PublishWebBuildMaterialBundle", context, siteId,
    { typeName: PublishWebBuildMaterialBundleEffectSchema.typeName, bytes: toBinary(PublishWebBuildMaterialBundleEffectSchema, effect, { writeUnknownFields: false }) },
    [effect.candidate.candidateRef, effect.webBuildMaterialBundle.ref], verified);
}

export function issueWebBuildIntentRequestDigest(context: AuthenticatedOperatorCommandContext, siteId: string, effect: IssueWebBuildIntentEffect, verified: VerifiedAuthenticatedAdminAxes): string {
  if (effect.candidate === undefined || effect.webBuildIntent === undefined) throw new Error("web_build_intent_owner_bindings_required");
  return sitePublicationDigest("IssueWebBuildIntent", context, siteId,
    { typeName: IssueWebBuildIntentEffectSchema.typeName, bytes: toBinary(IssueWebBuildIntentEffectSchema, effect, { writeUnknownFields: false }) },
    [effect.candidate.candidateRef, effect.webBuildIntent.ref], verified);
}

export function publishReleaseCertificationRequestDigest(context: AuthenticatedOperatorCommandContext, siteId: string, effect: PublishReleaseCertificationEffect, verified: VerifiedAuthenticatedAdminAxes): string {
  if (effect.candidate === undefined || effect.releaseCertification === undefined) throw new Error("release_certification_owner_bindings_required");
  return sitePublicationDigest("PublishReleaseCertification", context, siteId,
    { typeName: PublishReleaseCertificationEffectSchema.typeName, bytes: toBinary(PublishReleaseCertificationEffectSchema, effect, { writeUnknownFields: false }) },
    [effect.candidate.candidateRef, effect.releaseCertification.ref], verified);
}

export function publishSiteReleaseRequestDigest(context: AuthenticatedOperatorCommandContext, siteId: string, effect: PublishSiteReleaseEffect, verified: VerifiedAuthenticatedAdminAxes): string {
  if (effect.candidate === undefined) throw new Error("site_release_candidate_binding_required");
  return sitePublicationDigest("PublishSiteRelease", context, siteId,
    { typeName: PublishSiteReleaseEffectSchema.typeName, bytes: toBinary(PublishSiteReleaseEffectSchema, effect, { writeUnknownFields: false }) },
    [effect.candidate.candidateRef], verified);
}
`;
}

function siteEvidenceAdmissionDigestSource() {
  return `
import {
  RecordReleaseEvidenceEffectSchema,
  ReleaseEvidenceProducerRole,
  WorkloadAuthorizationState,
  type AttestedReleaseEvidenceContext,
  type RecordReleaseEvidenceEffect,
} from "./kokoro/platform/site/v1/site_publication_pb.js";

export type VerifiedReleaseEvidenceWorkloadAxes = Readonly<{
  workloadIdentityRef: string;
  audience: "kokoro.site-release-evidence-admission.v1";
  environment: string;
  region: string;
  siteId: string;
  producerIdentityRef: string;
  producerRegistrationRef: string;
  producerRegistrationRevision: bigint;
  producerRegistrationDigest: string;
  producerRole: ReleaseEvidenceProducerRole.WEB_ARTIFACT_PROVENANCE_ATTESTOR;
  workloadAttestationRef: string;
  workloadAttestationRevision: bigint;
  workloadAttestationDigest: string;
  workloadAuthorizationEpoch: bigint;
  workloadRevocationEpoch: bigint;
  workloadAuthorizationState: WorkloadAuthorizationState.ACTIVE;
  workloadAuthorizationLiveReadRef: string;
  workloadAuthorizationLiveReadRevision: bigint;
  workloadAuthorizationLiveReadDigest: string;
  workloadAuthorizationObservedAt: CanonicalInstant;
  workloadAuthorizationValidUntil: CanonicalInstant;
  authoritativeNow: CanonicalInstant;
}>;

export function recordReleaseEvidenceRequestDigest(
  context: AttestedReleaseEvidenceContext,
  siteId: string,
  effect: RecordReleaseEvidenceEffect,
  verified: VerifiedReleaseEvidenceWorkloadAxes,
): string {
  if (context.command === undefined || context.producerRegistration === undefined || context.workloadAttestation === undefined || context.workloadAuthorizationLiveRead === undefined) throw new Error("release_evidence_workload_context_required");
  if (effect.candidate === undefined || effect.compiledWebManifest === undefined || effect.webArtifactProvenance === undefined || effect.artifactInspectionEvidence === undefined || effect.journeyEvidence === undefined || effect.securityEvidence === undefined) throw new Error("release_evidence_owner_bindings_required");
  const audience = assertAxisMatch("audience", context.audience, verified.audience);
  if (audience !== "kokoro.site-release-evidence-admission.v1") throw new Error("release_evidence_audience_invalid");
  const producerRegistration = context.producerRegistration;
  assertAxisMatch("producerRegistrationRef", producerRegistration.ref, verified.producerRegistrationRef);
  assertUint64Match("producerRegistrationRevision", producerRegistration.revision, verified.producerRegistrationRevision);
  assertSha256Match("producerRegistrationDigest", producerRegistration.digest, verified.producerRegistrationDigest);
  if (context.producerRole !== ReleaseEvidenceProducerRole.WEB_ARTIFACT_PROVENANCE_ATTESTOR || context.producerRole !== verified.producerRole) throw new Error("release_evidence_producer_role_invalid");
  const workloadAttestation = context.workloadAttestation;
  assertAxisMatch("workloadAttestationRef", workloadAttestation.ref, verified.workloadAttestationRef);
  assertUint64Match("workloadAttestationRevision", workloadAttestation.revision, verified.workloadAttestationRevision);
  assertSha256Match("workloadAttestationDigest", workloadAttestation.digest, verified.workloadAttestationDigest);
  const workloadAuthorizationEpoch = assertUint64Match("workloadAuthorizationEpoch", context.workloadAuthorizationEpoch, verified.workloadAuthorizationEpoch);
  const workloadRevocationEpoch = assertUint64AllowZeroMatch("workloadRevocationEpoch", context.workloadRevocationEpoch, verified.workloadRevocationEpoch);
  if (
    context.workloadAuthorizationState !== WorkloadAuthorizationState.ACTIVE ||
    context.workloadAuthorizationState !== verified.workloadAuthorizationState ||
    workloadRevocationEpoch !== 0n
  ) throw new Error("release_evidence_workload_authorization_inactive");
  const workloadAuthorizationLiveRead = context.workloadAuthorizationLiveRead;
  assertAxisMatch("workloadAuthorizationLiveReadRef", workloadAuthorizationLiveRead.ref, verified.workloadAuthorizationLiveReadRef);
  assertUint64Match("workloadAuthorizationLiveReadRevision", workloadAuthorizationLiveRead.revision, verified.workloadAuthorizationLiveReadRevision);
  assertSha256Match("workloadAuthorizationLiveReadDigest", workloadAuthorizationLiveRead.digest, verified.workloadAuthorizationLiveReadDigest);
  const workloadAuthorizationObservedAt = assertInstantMatch("workloadAuthorizationObservedAt", context.workloadAuthorizationObservedAt, verified.workloadAuthorizationObservedAt, true);
  const workloadAuthorizationValidUntil = assertInstantMatch("workloadAuthorizationValidUntil", context.workloadAuthorizationValidUntil, verified.workloadAuthorizationValidUntil, true);
  const authoritativeNow = optionalInstant("verified.authoritativeNow", verified.authoritativeNow);
  if (
    workloadAuthorizationObservedAt === undefined ||
    workloadAuthorizationValidUntil === undefined ||
    authoritativeNow === undefined ||
    compareInstants(authoritativeNow, workloadAuthorizationObservedAt) < 0 ||
    compareInstants(authoritativeNow, workloadAuthorizationValidUntil) >= 0
  ) throw new Error("release_evidence_workload_authorization_stale");
  return commandEnvelopeV2Digest({
    contractVersion: "platform-site-evidence-admission@v1",
    operation: "kokoro.platform.site.v1.SiteEvidenceAdmissionService/RecordReleaseEvidence",
    trust: {
      workloadIdentityRef: assertAxisMatch("workloadIdentityRef", context.workloadIdentityRef, verified.workloadIdentityRef),
      audience,
      environment: assertAxisMatch("environment", context.environment, verified.environment),
      region: assertAxisMatch("region", context.region, verified.region),
      siteRef: requiredAxis("siteId", verified.siteId),
      securityEpochs: [
        { axis: "workload-authorization", value: workloadAuthorizationEpoch },
        { axis: "workload-revocation", value: workloadRevocationEpoch },
      ],
    },
    targetRefs: [
      assertAxisMatch("siteId", siteId, verified.siteId),
      assertAxisMatch("producerIdentityRef", context.producerIdentityRef, verified.producerIdentityRef),
      producerRegistration.ref,
      workloadAttestation.ref,
      workloadAuthorizationLiveRead.ref,
      effect.candidate.candidateRef,
      effect.compiledWebManifest.ref,
      effect.webArtifactProvenance.ref,
      effect.artifactInspectionEvidence.ref,
      effect.journeyEvidence.ref,
      effect.securityEvidence.ref,
    ],
    effect: {
      typeName: RecordReleaseEvidenceEffectSchema.typeName,
      bytes: toBinary(RecordReleaseEvidenceEffectSchema, effect, { writeUnknownFields: false }),
    },
  });
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

function mediaProjectionRecoveryDigestSource(kind) {
  const variants = {
    "media-projection-recovery": {
      contractVersion: "platform-media-projection-recovery@v1",
      operation: "kokoro.platform.media.v1.MediaProjectionRecoveryService/RefreshProjectionRecoveryAccess",
      importPath: "./kokoro/platform/media/v1/media_projection_recovery_pb.js",
      effect: "RefreshMediaProjectionRecoveryAccessEffect",
      functionName: "mediaProjectionRecoveryRefreshRequestDigest",
      projectionRef: "operationRef",
    },
    "credit-cost-projection-recovery": {
      contractVersion: "platform-credit-cost-projection-recovery@v1",
      operation: "kokoro.platform.credit.v1.CreditCostProjectionRecoveryService/RefreshProjectionRecoveryAccess",
      importPath: "./kokoro/platform/credit/v1/cost_projection_recovery_pb.js",
      effect: "RefreshCreditCostProjectionRecoveryAccessEffect",
      functionName: "creditCostProjectionRecoveryRefreshRequestDigest",
      projectionRef: "costProjectionRef",
    },
  };
  const variant = variants[kind];
  if (variant === undefined) throw new Error("projection_recovery_digest_boundary_unknown");
  return `
import {
  ${variant.effect}Schema,
  type ${variant.effect},
} from "${variant.importPath}";

export type VerifiedProjectionRecoveryCommandAxes = Readonly<{
  workloadIdentityRef: string;
  audience: string;
  environment: string;
  region: string;
  siteRef: string;
}>;

export function ${variant.functionName}(
  effect: ${variant.effect},
  verified: VerifiedProjectionRecoveryCommandAxes,
): string {
  return commandEnvelopeV2Digest({
    contractVersion: "${variant.contractVersion}",
    operation: "${variant.operation}",
    trust: {
      workloadIdentityRef: requiredAxis("verified.workloadIdentityRef", verified.workloadIdentityRef),
      audience: requiredAxis("verified.audience", verified.audience),
      environment: requiredAxis("verified.environment", verified.environment),
      region: requiredAxis("verified.region", verified.region),
      siteRef: requiredAxis("verified.siteRef", verified.siteRef),
      securityEpochs: [],
    },
    targetRefs: [effect.bindingRef, effect.${variant.projectionRef}],
    effect: {
      typeName: ${variant.effect}Schema.typeName,
      bytes: toBinary(${variant.effect}Schema, effect, { writeUnknownFields: false }),
    },
  });
}
`;
}

function modelImageEffectDigestSource() {
  return `
import {
  AttachNextAttemptAuthorizationEffectSchema,
  CanonicalImageEffectCommandReceiptV1Schema,
  CreateImageEffectEffectSchema,
  IssueImageEffectOutputAccessEffectSchema,
  RequestCancelImageEffectEffectSchema,
  type AttachNextAttemptAuthorizationEffect,
  type CanonicalImageEffectCommandReceiptV1,
  type CreateImageEffectEffect,
  type IssueImageEffectOutputAccessEffect,
  type RequestCancelImageEffectEffect,
} from "./kokoro/platform/model/image/v1/image_effect_pb.js";

export type VerifiedModelImageEffectCommandAxes = Readonly<{
  workloadIdentityRef: string;
  audience: "platform-media-worker";
  environment: string;
  region: string;
  siteRef: string;
  callerIdentity: string;
  authorizationGeneration: bigint;
  securityEpoch: bigint;
}>;

export function imageEffectCommandReceiptDigest(
  record: CanonicalImageEffectCommandReceiptV1,
): string {
  const hash = createHash("sha256");
  hash.update(CanonicalImageEffectCommandReceiptV1Schema.typeName, "utf8");
  hash.update(Uint8Array.of(0));
  hash.update(toBinary(CanonicalImageEffectCommandReceiptV1Schema, record, { writeUnknownFields: false }));
  return hash.digest("hex");
}

export function imageEffectCommandReceiptRef(
  record: CanonicalImageEffectCommandReceiptV1,
): string {
  return "image-effect-receipt:sha256:" + imageEffectCommandReceiptDigest(record);
}

function modelImageEffectDigest(
  method: string,
  effect: TypedPayload,
  targetRefs: readonly string[],
  verified: VerifiedModelImageEffectCommandAxes,
): string {
  if (verified.audience !== "platform-media-worker") {
    throw new Error("command_envelope_axis_mismatch:audience");
  }
  return commandEnvelopeV2Digest({
    contractVersion: "model-image-effect@v1",
    operation: \`kokoro.platform.model.image.v1.ImageEffectV1Service/\${method}\`,
    trust: {
      workloadIdentityRef: requiredAxis("verified.workloadIdentityRef", verified.workloadIdentityRef),
      audience: verified.audience,
      environment: requiredAxis("verified.environment", verified.environment),
      region: requiredAxis("verified.region", verified.region),
      siteRef: requiredAxis("verified.siteRef", verified.siteRef),
      actorRef: requiredAxis("verified.callerIdentity", verified.callerIdentity),
      actorGeneration: requiredUint64("verified.authorizationGeneration", verified.authorizationGeneration),
      securityEpochs: [{
        axis: "caller-security-epoch",
        value: requiredUint64("verified.securityEpoch", verified.securityEpoch),
      }],
    },
    targetRefs,
    effect,
  });
}

export function createImageEffectRequestDigest(
  effect: CreateImageEffectEffect,
  verified: VerifiedModelImageEffectCommandAxes,
): string {
  return modelImageEffectDigest("CreateImageEffect", {
    typeName: CreateImageEffectEffectSchema.typeName,
    bytes: toBinary(CreateImageEffectEffectSchema, effect, { writeUnknownFields: false }),
  }, [effect.definitionRoleRef, effect.modelOptionRevisionRef, effect.operationInputRevisionRef], verified);
}

export function requestCancelImageEffectRequestDigest(
  effect: RequestCancelImageEffectEffect,
  verified: VerifiedModelImageEffectCommandAxes,
): string {
  return modelImageEffectDigest("RequestCancelImageEffect", {
    typeName: RequestCancelImageEffectEffectSchema.typeName,
    bytes: toBinary(RequestCancelImageEffectEffectSchema, effect, { writeUnknownFields: false }),
  }, [effect.logicalInvocationRef], verified);
}

export function issueImageEffectOutputAccessRequestDigest(
  effect: IssueImageEffectOutputAccessEffect,
  verified: VerifiedModelImageEffectCommandAxes,
): string {
  return modelImageEffectDigest("IssueImageEffectOutputAccess", {
    typeName: IssueImageEffectOutputAccessEffectSchema.typeName,
    bytes: toBinary(IssueImageEffectOutputAccessEffectSchema, effect, { writeUnknownFields: false }),
  }, [effect.logicalInvocationRef, effect.outputEvidenceRef], verified);
}

export function attachNextAttemptAuthorizationRequestDigest(
  effect: AttachNextAttemptAuthorizationEffect,
  verified: VerifiedModelImageEffectCommandAxes,
): string {
  return modelImageEffectDigest("AttachNextAttemptAuthorization", {
    typeName: AttachNextAttemptAuthorizationEffectSchema.typeName,
    bytes: toBinary(AttachNextAttemptAuthorizationEffectSchema, effect, { writeUnknownFields: false }),
  }, [effect.logicalInvocationRef, effect.modelInvocationCommandRef,
    effect.definitelyNotSubmittedReceiptRef], verified);
}
`;
}

function commandEnvelopeDigestSource(kind) {
  const wrappers = {
    identity: identityCommandDigestSource,
    "admin-command": adminCommandDigestSource,
    "site-lifecycle": siteLifecycleDigestSource,
    "site-provisioning": siteProvisioningDigestSource,
    "product-catalog-publication": productCatalogPublicationDigestSource,
    "site-publication": sitePublicationDigestSource,
    "site-evidence-admission": siteEvidenceAdmissionDigestSource,
    "admin-commerce": () => adminCommerceDigestSourceV2() + adminCommerceDigestSourceV2Remainder(),
    "admin-credit": adminCreditDigestSource,
    "credit-application": creditApplicationDigestSource,
    "model-control": modelControlDigestSource,
    "media-projection-recovery": () => mediaProjectionRecoveryDigestSource(kind),
    "credit-cost-projection-recovery": () => mediaProjectionRecoveryDigestSource(kind),
    "model-image-effect": modelImageEffectDigestSource,
  };
  const wrapper = wrappers[kind];
  if (wrapper === undefined) throw new Error("command_envelope_digest_boundary_unknown");
  const boundarySelectivePrimitives = kind === "site-evidence-admission" || kind === "model-image-effect" ||
    kind === "media-projection-recovery" || kind === "credit-cost-projection-recovery";
  return commandEnvelopeDigestCoreSource(boundarySelectivePrimitives) + wrapper();
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
  mediaProjectionRecoveryDigestSource,
  modelImageEffectDigestSource,
  parseArguments,
};
