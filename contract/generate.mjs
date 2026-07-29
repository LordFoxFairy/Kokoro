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
    inputs: Object.freeze([
      "proto/kokoro/platform/admin/v1/admin_auth.proto",
      "proto/kokoro/platform/admission/v1/admission.proto",
    ]),
    sources: Object.freeze([
      "kokoro/common/v1/error.proto",
      "kokoro/common/v1/receipt.proto",
      "kokoro/platform/admin/v1/admin_auth.proto",
      "kokoro/platform/admission/v1/admission.proto",
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
  type CanonicalCommandEnvelopeV2,
} from "./kokoro/common/v2/command_envelope_pb.js";

export const COMMAND_ENVELOPE_DIGEST_ALGORITHM_V2 =
  CommandDigestAlgorithmV2.SHA256_COMMAND_ENVELOPE;

type TypedPayload = Readonly<{
  typeName: string;
  bytes: Uint8Array;
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
  ExecuteApprovedEffectSchema,
  PrepareCommandEffectSchema,
  SubmitForApprovalEffectSchema,
  UpdateOperatorScopeChangeSchema,
  type DecideApprovalEffect,
  type ExecuteApprovedEffect,
  type PrepareCommandEffect,
  type SubmitForApprovalEffect,
} from "./kokoro/platform/admin/v2/admin_command_pb.js";

function canonicalPrepareCommandEffect(
  context: AuthenticatedOperatorCommandContext,
  effect: PrepareCommandEffect,
): PrepareCommandEffect {
  if (effect.change.case !== "updateOperatorScope") return effect;
  const replacement = canonicalOperatorScope(effect.change.value.replacementScope, context.environment, context.region);
  return create(PrepareCommandEffectSchema, {
    change: {
      case: "updateOperatorScope",
      value: create(UpdateOperatorScopeChangeSchema, {
        operatorRef: effect.change.value.operatorRef,
        replacementScope: replacement,
      }),
    },
    reason: effect.reason,
  });
}

function prepareCommandTargets(effect: PrepareCommandEffect): string[] {
  switch (effect.change.case) {
    case "disableUser": return [effect.change.value.siteId, effect.change.value.userRef];
    case "updateOperatorScope": return [effect.change.value.operatorRef];
    case "updatePolicy": return [effect.change.value.policyRef, effect.change.value.policyRevisionRef];
    case undefined: throw new Error("command_envelope_effect_change_missing");
  }
}

export function prepareCommandRequestDigest(
  context: AuthenticatedOperatorCommandContext,
  effect: PrepareCommandEffect,
  verified: VerifiedAuthenticatedAdminAxes,
): string {
  const canonicalEffect = canonicalPrepareCommandEffect(context, effect);
  return authenticatedEnvelope(
    "platform-admin-command@v2",
    "kokoro.platform.admin.v2.AdminCommandService/PrepareCommand",
    context,
    { typeName: PrepareCommandEffectSchema.typeName, bytes: toBinary(PrepareCommandEffectSchema, canonicalEffect, { writeUnknownFields: false }) },
    prepareCommandTargets(canonicalEffect),
    verified,
  );
}

export function submitForApprovalRequestDigest(
  context: AuthenticatedOperatorCommandContext,
  effect: SubmitForApprovalEffect,
  verified: VerifiedAuthenticatedAdminAxes,
): string {
  return authenticatedEnvelope(
    "platform-admin-command@v2",
    "kokoro.platform.admin.v2.AdminCommandService/SubmitForApproval",
    context,
    { typeName: SubmitForApprovalEffectSchema.typeName, bytes: toBinary(SubmitForApprovalEffectSchema, effect, { writeUnknownFields: false }) },
    [effect.preparedCommandRef],
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

export function executeApprovedRequestDigest(
  context: AuthenticatedOperatorCommandContext,
  effect: ExecuteApprovedEffect,
  verified: VerifiedAuthenticatedAdminAxes,
): string {
  return authenticatedEnvelope(
    "platform-admin-command@v2",
    "kokoro.platform.admin.v2.AdminCommandService/ExecuteApproved",
    context,
    { typeName: ExecuteApprovedEffectSchema.typeName, bytes: toBinary(ExecuteApprovedEffectSchema, effect, { writeUnknownFields: false }) },
    [effect.preparedCommandRef, effect.approvalRef],
    verified,
  );
}
`;
}

function siteLifecycleDigestSource() {
  return `${authenticatedCommandDigestSource()}
import {
  ActivateReleaseEffectSchema,
  CancelDecommissionEffectSchema,
  CreateReleaseEffectSchema,
  ExecuteDecommissionEffectSchema,
  PlanDecommissionEffectSchema,
  ReconcileProvisioningEffectSchema,
  RequestSiteEffectSchema,
  ResumeSiteEffectSchema,
  SuspendSiteEffectSchema,
  type ActivateReleaseEffect,
  type CancelDecommissionEffect,
  type CreateReleaseEffect,
  type ExecuteDecommissionEffect,
  type PlanDecommissionEffect,
  type ReconcileProvisioningEffect,
  type RequestSiteEffect,
  type ResumeSiteEffect,
  type SuspendSiteEffect,
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

export function requestSiteRequestDigest(
  context: AuthenticatedOperatorCommandContext,
  effect: RequestSiteEffect,
  verified: VerifiedAuthenticatedAdminAxes,
): string {
  return siteDigest(
    "kokoro.platform.site.v1.SiteLifecycleService/RequestSite", context,
    { typeName: RequestSiteEffectSchema.typeName, bytes: toBinary(RequestSiteEffectSchema, effect, { writeUnknownFields: false }) },
    [effect.siteKey, effect.profileRef, effect.primaryDomain], verified,
  );
}

export function reconcileProvisioningRequestDigest(
  context: AuthenticatedOperatorCommandContext, siteId: string, effect: ReconcileProvisioningEffect,
  verified: VerifiedAuthenticatedAdminAxes,
): string {
  return siteDigest(
    "kokoro.platform.site.v1.SiteLifecycleService/ReconcileProvisioning", context,
    { typeName: ReconcileProvisioningEffectSchema.typeName, bytes: toBinary(ReconcileProvisioningEffectSchema, effect, { writeUnknownFields: false }) },
    [siteId, effect.provisioningIntentRef], verified,
  );
}

export function createReleaseRequestDigest(
  context: AuthenticatedOperatorCommandContext, siteId: string, effect: CreateReleaseEffect,
  verified: VerifiedAuthenticatedAdminAxes,
): string {
  return siteDigest(
    "kokoro.platform.site.v1.SiteLifecycleService/CreateRelease", context,
    { typeName: CreateReleaseEffectSchema.typeName, bytes: toBinary(CreateReleaseEffectSchema, effect, { writeUnknownFields: false }) },
    [siteId, effect.sourceRevision, effect.deploymentManifestRef], verified,
  );
}

export function activateReleaseRequestDigest(
  context: AuthenticatedOperatorCommandContext, siteId: string, effect: ActivateReleaseEffect,
  verified: VerifiedAuthenticatedAdminAxes,
): string {
  return siteDigest(
    "kokoro.platform.site.v1.SiteLifecycleService/ActivateRelease", context,
    { typeName: ActivateReleaseEffectSchema.typeName, bytes: toBinary(ActivateReleaseEffectSchema, effect, { writeUnknownFields: false }) },
    [siteId, effect.releaseRef, ...(effect.expectedActiveReleaseRef === undefined ? [] : [effect.expectedActiveReleaseRef])], verified,
  );
}

export function suspendSiteRequestDigest(
  context: AuthenticatedOperatorCommandContext, siteId: string, effect: SuspendSiteEffect,
  verified: VerifiedAuthenticatedAdminAxes,
): string {
  return siteDigest(
    "kokoro.platform.site.v1.SiteLifecycleService/SuspendSite", context,
    { typeName: SuspendSiteEffectSchema.typeName, bytes: toBinary(SuspendSiteEffectSchema, effect, { writeUnknownFields: false }) },
    [siteId, effect.suspensionPolicyRef], verified,
  );
}

export function resumeSiteRequestDigest(
  context: AuthenticatedOperatorCommandContext, siteId: string, effect: ResumeSiteEffect,
  verified: VerifiedAuthenticatedAdminAxes,
): string {
  return siteDigest(
    "kokoro.platform.site.v1.SiteLifecycleService/ResumeSite", context,
    { typeName: ResumeSiteEffectSchema.typeName, bytes: toBinary(ResumeSiteEffectSchema, effect, { writeUnknownFields: false }) },
    [siteId, effect.suspensionReceiptRef], verified,
  );
}

export function planDecommissionRequestDigest(
  context: AuthenticatedOperatorCommandContext, siteId: string, effect: PlanDecommissionEffect,
  verified: VerifiedAuthenticatedAdminAxes,
): string {
  const participants = uniqueSorted("effect.requiredParticipantRef", effect.requiredParticipantRefs);
  const canonicalEffect = create(PlanDecommissionEffectSchema, {
    earliestExecutionAt: effect.earliestExecutionAt,
    requiredParticipantRefs: participants,
    retentionPolicyRef: effect.retentionPolicyRef,
  });
  return siteDigest(
    "kokoro.platform.site.v1.SiteLifecycleService/PlanDecommission", context,
    { typeName: PlanDecommissionEffectSchema.typeName, bytes: toBinary(PlanDecommissionEffectSchema, canonicalEffect, { writeUnknownFields: false }) },
    [siteId, effect.retentionPolicyRef, ...participants], verified,
  );
}

export function cancelDecommissionRequestDigest(
  context: AuthenticatedOperatorCommandContext, siteId: string, effect: CancelDecommissionEffect,
  verified: VerifiedAuthenticatedAdminAxes,
): string {
  return siteDigest(
    "kokoro.platform.site.v1.SiteLifecycleService/CancelDecommission", context,
    { typeName: CancelDecommissionEffectSchema.typeName, bytes: toBinary(CancelDecommissionEffectSchema, effect, { writeUnknownFields: false }) },
    [siteId, effect.decommissionPlanRef], verified,
  );
}

export function executeDecommissionRequestDigest(
  context: AuthenticatedOperatorCommandContext, siteId: string, effect: ExecuteDecommissionEffect,
  verified: VerifiedAuthenticatedAdminAxes,
): string {
  return siteDigest(
    "kokoro.platform.site.v1.SiteLifecycleService/ExecuteDecommission", context,
    { typeName: ExecuteDecommissionEffectSchema.typeName, bytes: toBinary(ExecuteDecommissionEffectSchema, effect, { writeUnknownFields: false }) },
    [siteId, effect.decommissionPlanRef, effect.approvalRef], verified,
  );
}
`;
}

function commandEnvelopeDigestSource(kind) {
  const wrappers = {
    identity: identityCommandDigestSource,
    "admin-command": adminCommandDigestSource,
    "site-lifecycle": siteLifecycleDigestSource,
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

async function generate(options) {
  const boundary = BOUNDARIES[options.boundary];
  const mirrors = await runBufGenerate(options.output, boundary);
  if (boundary.helper === "admin-auth-effect-digest.ts") {
    const digestSource = adminAuthEffectDigestSource();
    await Promise.all(mirrors.map((mirror) => writeFile(resolve(mirror, boundary.helper), digestSource, "utf8")));
  }
  if (boundary.commandEnvelopeDigest) {
    const digestSource = commandEnvelopeDigestSource(boundary.commandEnvelopeDigest);
    await Promise.all(
      mirrors.map((mirror) => writeFile(resolve(mirror, "command-envelope-digest.ts"), digestSource, "utf8")),
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
  parseArguments,
};
