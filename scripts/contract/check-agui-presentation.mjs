#!/usr/bin/env node

import { createCipheriv, createDecipheriv, createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { readFile } from "node:fs/promises";
import { resolve, sep } from "node:path";
import { pathToFileURL } from "node:url";

import { EventSchemas, EventType } from "../../contract/node_modules/@ag-ui/core/dist/index.mjs";
import Ajv2020 from "../../contract/node_modules/ajv/dist/2020.js";

const repositoryRoot = resolve(import.meta.dirname, "../..");
const CORPUS_PATH = "contract/corpus/agui-presentation-v1.json";
const PACKAGE_PATH = "contract/package.json";
const LOCK_PATH = "contract/pnpm-lock.yaml";
const PROFILE_REVISION = "kokoro-agui-presentation.v1";
const CURSOR_PROFILE_REVISION = "opaque-session-cursor-v1";
const SESSION_CONTRACT_REVISION = "session-agui-stream.v1";
const AGUI_CORE_VERSION = "0.0.57";
const AGUI_CORE_INTEGRITY = "sha512-gho1OWjNE6E3Rl7ZEZ1wr2CEpUHjLFU0FqzCZZk439TicLu+BfLCMkMokB07bMGlRmbJ60hM6LW60iOVauCx+Q==";
const AGUI_UPSTREAM_REPOSITORY = "https://github.com/ag-ui-protocol/ag-ui";
const AGUI_UPSTREAM_COMMIT = "54f13419055b4d0f442c71e1efab18b310982ce1";
const AGENT_CANDIDATE_PROFILE_REVISION = "kokoro-agent-agui-candidate.v1";
const CURSOR_KEY_REVISION = "agui-conformance-2026-08";
const CURSOR_KEY = createHash("sha256").update("kokoro-agui-presentation-public-conformance-key-v1", "utf8").digest();
const CURSOR_AAD = Buffer.from(`kokoro.session.browser.cursor.v1\u0000${CURSOR_KEY_REVISION}`, "utf8");
const UINT64_MAXIMUM = 18_446_744_073_709_551_615n;

const CONTRACT_PATHS = Object.freeze({
  profile: "contract/registry/agui-upstream-profile.yaml",
  agentCandidateProfile: "contract/registry/agui-agent-candidate-profile-v1.yaml",
  activityAuthority: "contract/registry/agui-activity-authority-v1.yaml",
  mapping: "contract/registry/agui-presentation-mapping-v1.yaml",
  eventSchema: "contract/spec/kokoro-agui-presentation-event-v1.yaml",
  agentCandidateSchema: "contract/spec/agent-agui-event-candidate-v1.yaml",
  agentCandidateEnvelopeSchema: "contract/spec/agent-agui-candidate-envelope-v1.yaml",
  projectionPayloadSchema: "contract/spec/session-agui-projection-payload-v1.yaml",
  presentationRowSchema: "contract/spec/session-agui-presentation-row-v1.yaml",
  bindingAuthorityDeltaSchema: "contract/spec/presentation-binding-authority-delta-v1.yaml",
  runBindingSchema: "contract/spec/presentation-run-binding-v1.yaml",
  messageBindingSchema: "contract/spec/presentation-message-binding-v1.yaml",
  ownerBindingSchema: "contract/spec/presentation-owner-binding-v1.yaml",
  ownerProjectionRowSchema: "contract/spec/session-agui-owner-projection-row-v1.yaml",
  streamSchema: "contract/spec/session-agui-stream-v1.yaml",
  snapshotAuthoritySchema: "contract/spec/session-agui-snapshot-authority-v1.yaml",
});

// These are the reviewed contract sources, not caller-selected schemas carrying a familiar $id.
const CONTRACT_SOURCE_SHA256 = Object.freeze({
  profile: "9692d77ff42726598b8547c63250556232d8fcd76c0faf19e6e37079a4f0ddd5",
  agentCandidateProfile: "1a515b4c227f30c552699db1e7ac4cadd196077918e8dd83c917283fb8e5a735",
  activityAuthority: "359c23cb2a8b384b261cd59550dc10695c29948e39a14d210b9487108573b8ec",
  mapping: "8e3f14b227fc0d0f873825a0aae85211586084e0620b54ef88685b640e95c818",
  eventSchema: "b8ffd673f428e73304a8a224db8edce3ca26d74fb8c2f40ec82a540c70c27095",
  agentCandidateSchema: "6a0668591737c79ec974c070556c2211ec89e2105b682dcde2c32f9952b745f4",
  agentCandidateEnvelopeSchema: "87562d25f01a19cb21717b6d0a7f9bc5cf1bd3e45c413d7eae7270231ea123f0",
  projectionPayloadSchema: "56ce58caa5ab0fceda870e3e0fb31ed283898755df8822af189ed5dce57c6ef6",
  presentationRowSchema: "9216fcfaca063b8c7576209e7108757749a655bbd7d538b9a8acb684356e72fa",
  bindingAuthorityDeltaSchema: "df61ff36f09195f9e9ed9764c8de27f5c59a717bee495a834316cae0988772ac",
  runBindingSchema: "54d50fd4179147e5b421d5ce6c957dce8d36be68906ba19bebd6372eea4136fe",
  messageBindingSchema: "56a2b5728f6ac880eb44648f30b0a05a09cf58ae713bc4f111a02928211dd1a5",
  ownerBindingSchema: "43d6434304ea1ce483b0a8d4f87f2916135eeb3bd07ab0a7ec7e7dd04315a2c6",
  ownerProjectionRowSchema: "8a1adee9b84356945edf1ecfe93c257945ea2ce6f1439d669750d2ef01edee80",
  streamSchema: "ce51651ab17c080838547ec74c73a86574b9134aed351c7f27d92d1709441333",
  snapshotAuthoritySchema: "104c50d6c409827857bbf1264a53984bc16c30cbfa2cd9ee8e3c407c13ca3922",
});

const OFFICIAL_EVENT_TYPES = Object.freeze(Object.values(EventType));
const ALLOWED_EVENT_TYPES = Object.freeze([
  EventType.RUN_STARTED,
  EventType.RUN_FINISHED,
  EventType.RUN_ERROR,
  EventType.TEXT_MESSAGE_START,
  EventType.TEXT_MESSAGE_CONTENT,
  EventType.TEXT_MESSAGE_END,
  EventType.ACTIVITY_SNAPSHOT,
  EventType.CUSTOM,
]);
const AGENT_CANDIDATE_EVENT_TYPES = Object.freeze([
  EventType.RUN_STARTED,
  EventType.RUN_FINISHED,
  EventType.RUN_ERROR,
  EventType.TEXT_MESSAGE_START,
  EventType.TEXT_MESSAGE_CONTENT,
  EventType.TEXT_MESSAGE_END,
  EventType.ACTIVITY_SNAPSHOT,
]);
const AGENT_CANDIDATE_ACTIVITY_TYPES = Object.freeze([
  "kokoro.safe-summary.v1",
  "kokoro.tool-preview.v1",
  "kokoro.hitl.v1",
  "kokoro.plan.v1",
  "kokoro.subagent.v1",
  "kokoro.notice.v1",
  "kokoro.error.v1",
]);
const PLATFORM_OWNER_ACTIVITY_TYPES = Object.freeze([
  "kokoro.media.v1", "kokoro.artifact.v1", "kokoro.cost.v1",
]);
const ACTIVITY_DEFINITIONS = Object.freeze([
  ["kokoro.safe-summary.v1", "activitySafeSummary", "kokoro-agent"],
  ["kokoro.tool-preview.v1", "activityToolPreview", "kokoro-agent"],
  ["kokoro.hitl.v1", "activityHitl", "kokoro-agent"],
  ["kokoro.plan.v1", "activityPlan", "kokoro-agent"],
  ["kokoro.subagent.v1", "activitySubagent", "kokoro-agent"],
  ["kokoro.notice.v1", "activityNotice", "kokoro-agent"],
  ["kokoro.error.v1", "activityError", "kokoro-agent"],
  ["kokoro.media.v1", "activityMedia", "kokoro-platform"],
  ["kokoro.artifact.v1", "activityArtifact", "kokoro-platform"],
  ["kokoro.cost.v1", "activityCost", "kokoro-platform"],
]);
const AGENT_ROLE_KEYS = Object.freeze([
  "repository", "internalEventCandidateProducer", "internalEventCandidateConsumer", "strictPresentationConsumer",
  "browserEndpoint", "durableProjectionOwner", "cursorOwner", "rawPassthrough",
]);
const EVENT_FIELDS = new Map([
  [EventType.RUN_STARTED, ["type", "timestamp", "threadId", "runId", "parentRunId"]],
  [EventType.RUN_FINISHED, ["type", "timestamp", "threadId", "runId"]],
  [EventType.RUN_ERROR, ["type", "timestamp", "message", "code"]],
  [EventType.TEXT_MESSAGE_START, ["type", "timestamp", "messageId", "role"]],
  [EventType.TEXT_MESSAGE_CONTENT, ["type", "timestamp", "messageId", "delta"]],
  [EventType.TEXT_MESSAGE_END, ["type", "timestamp", "messageId"]],
  [EventType.ACTIVITY_SNAPSHOT, ["type", "timestamp", "messageId", "activityType", "content", "replace"]],
  [EventType.CUSTOM, ["type", "timestamp", "name", "value"]],
]);
const CURSOR_CLAIM_KEYS = Object.freeze([
  "version", "kind", "sessionId", "streamEpoch", "durableSeq", "profileRevision", "cursorProfileRevision",
]);
const BINDING_DELTA_KIND_BY_EVENT = Object.freeze(new Map([
  [EventType.RUN_STARTED, "run.replace"],
  [EventType.RUN_FINISHED, "run.replace"],
  [EventType.RUN_ERROR, "run.replace"],
  [EventType.TEXT_MESSAGE_START, "message.replace"],
  [EventType.TEXT_MESSAGE_END, "message.replace"],
]));
const OWNER_DELTA_CUSTOM_NAMES = Object.freeze(new Set([
  "kokoro.control.replace.v1", "kokoro.receipt.replace.v1",
]));
const OWNER_MESSAGE_ENDED_RUN_OPEN = Object.freeze([
  "safe-summary", "tool", "hitl", "plan", "subagent", "media", "artifact", "cost", "notice", "error",
]);
const OWNER_TERMINAL_MAY_CREATE = Object.freeze(["media", "artifact", "cost", "notice", "error"]);
const OWNER_TERMINAL_MAY_CONVERGE = Object.freeze(["media", "artifact", "cost", "notice", "error", "receipt"]);
const OWNER_TERMINAL_MAY_NOT_CREATE = Object.freeze(["safe-summary", "tool", "hitl", "control", "plan", "subagent"]);
const OWNER_TERMINAL_MAY_CREATE_SET = new Set(OWNER_TERMINAL_MAY_CREATE);
const OWNER_TERMINAL_MAY_CONVERGE_SET = new Set(OWNER_TERMINAL_MAY_CONVERGE);
const COT_KEY = /^(?:chain[_-]?of[_-]?thought|cot|private[_-]?reasoning|hidden[_-]?reasoning|reasoning[_-]?(?:content|trace|tokens))$/iu;
const TOOL_SECRET_KEY = /^(?:api[_-]?key|authorization|credential|headers?|password|private[_-]?key|provider[_-]?url|raw[_-]?(?:input|output|result)|secret|token|args|arguments|input)$/iu;
const PUBLIC_SOURCE_EVENT_ID = /^presentation\.event:[A-Za-z0-9][A-Za-z0-9._:-]*$/u;

export class AguiPresentationContractError extends Error {
  constructor(code, detail = "") {
    super(`${code}${detail === "" ? "" : `: ${detail}`}`);
    this.name = "AguiPresentationContractError";
    this.code = code;
    this.detail = detail;
  }
}

function fail(code, detail = "") {
  throw new AguiPresentationContractError(code, detail);
}

function exactKeys(value, expected, code) {
  if (value === null || typeof value !== "object" || Array.isArray(value)) fail(code);
  const actual = Object.keys(value).sort();
  const wanted = [...expected].sort();
  if (JSON.stringify(actual) !== JSON.stringify(wanted)) fail(code, actual.join(","));
}

function exactArray(actual, expected, code) {
  if (!Array.isArray(actual) || JSON.stringify(actual) !== JSON.stringify(expected)) fail(code);
}

function assertUnicodeScalarString(value) {
  for (let index = 0; index < value.length; index += 1) {
    const codeUnit = value.charCodeAt(index);
    if (codeUnit >= 0xd800 && codeUnit <= 0xdbff) {
      const next = value.charCodeAt(index + 1);
      if (!(next >= 0xdc00 && next <= 0xdfff)) fail("agui_canonical_unicode_invalid");
      index += 1;
    } else if (codeUnit >= 0xdc00 && codeUnit <= 0xdfff) {
      fail("agui_canonical_unicode_invalid");
    }
  }
}

function canonical(value) {
  if (typeof value === "string") {
    assertUnicodeScalarString(value);
    return JSON.stringify(value);
  }
  if (typeof value === "number" && (!Number.isFinite(value) || (Number.isInteger(value) && !Number.isSafeInteger(value)))) {
    fail("agui_canonical_number_invalid");
  }
  if (value === null || typeof value === "boolean" || typeof value === "number") {
    return JSON.stringify(value);
  }
  if (Array.isArray(value)) return `[${value.map(canonical).join(",")}]`;
  if (typeof value !== "object") fail("agui_canonical_value_invalid");
  return `{${Object.keys(value).sort().map((name) => {
    assertUnicodeScalarString(name);
    return `${JSON.stringify(name)}:${canonical(value[name])}`;
  }).join(",")}}`;
}

function sha256Bytes(value) {
  return createHash("sha256").update(value).digest("hex");
}

function projectionDigest(value) {
  return `sha256:${sha256Bytes(Buffer.from(canonical(value), "utf8"))}`;
}

function safePath(root, relativePath) {
  if (typeof relativePath !== "string" || relativePath.startsWith("/") || relativePath.includes("\\")) {
    fail("agui_contract_path_invalid");
  }
  const path = resolve(root, relativePath);
  if (path !== root && !path.startsWith(`${root}${sep}`)) fail("agui_contract_path_invalid");
  return path;
}

function readJsonSource(root, relativePath, code) {
  try {
    const source = readFileSync(safePath(root, relativePath));
    return { source, value: JSON.parse(source.toString("utf8")) };
  } catch (error) {
    if (error instanceof AguiPresentationContractError) throw error;
    fail(code, relativePath);
  }
}

function validateOfficialDependency(root) {
  let runtimePackage;
  try {
    runtimePackage = JSON.parse(readFileSync(resolve(repositoryRoot, "contract/node_modules/@ag-ui/core/package.json"), "utf8"));
  } catch {
    fail("agui_core_dependency_drift", "runtime");
  }
  if (runtimePackage.name !== "@ag-ui/core" || runtimePackage.version !== AGUI_CORE_VERSION) fail("agui_core_dependency_drift", "runtime");
  const packageJson = readJsonSource(root, PACKAGE_PATH, "agui_core_dependency_drift").value;
  if (packageJson.devDependencies?.["@ag-ui/core"] !== AGUI_CORE_VERSION) fail("agui_core_dependency_drift", "package");
  let lock;
  try {
    lock = readFileSync(safePath(root, LOCK_PATH), "utf8");
  } catch {
    fail("agui_core_dependency_drift", "lock");
  }
  const importer = /'@ag-ui\/core':\n\s+specifier: 0\.0\.57\n\s+version: 0\.0\.57/u.test(lock);
  const resolution = new RegExp(`'@ag-ui/core@0\\.0\\.57':\\n\\s+resolution: \\{integrity: ${AGUI_CORE_INTEGRITY.replaceAll("+", "\\+")}\\}`, "u").test(lock);
  const packageVersions = [...lock.matchAll(/^  '@ag-ui\/core@([^']+)':$/gmu)].map((match) => match[1]);
  if (!importer || !resolution || packageVersions.length !== 2 || packageVersions.some((version) => version !== AGUI_CORE_VERSION)) {
    fail("agui_core_dependency_drift", "lock");
  }
}

function loadContracts(root = repositoryRoot) {
  const sources = {};
  for (const [name, relativePath] of Object.entries(CONTRACT_PATHS)) {
    const loaded = readJsonSource(root, relativePath, `agui_${name}_unreadable`);
    if (sha256Bytes(loaded.source) !== CONTRACT_SOURCE_SHA256[name]) fail("agui_contract_source_drift", name);
    sources[name] = loaded.value;
  }
  const ajv = new Ajv2020({ allErrors: true, strict: true, validateFormats: false });
  try {
    ajv.addSchema(sources.eventSchema);
    ajv.addSchema(sources.runBindingSchema);
    ajv.addSchema(sources.messageBindingSchema);
    ajv.addSchema(sources.ownerBindingSchema);
    ajv.addSchema(sources.ownerProjectionRowSchema);
    ajv.addSchema(sources.bindingAuthorityDeltaSchema);
    ajv.addSchema(sources.agentCandidateSchema);
    ajv.addSchema(sources.agentCandidateEnvelopeSchema);
    ajv.addSchema(sources.projectionPayloadSchema);
    ajv.addSchema(sources.presentationRowSchema);
    return Object.freeze({
      profile: sources.profile,
      agentCandidateProfile: sources.agentCandidateProfile,
      activityAuthority: sources.activityAuthority,
      eventSchema: sources.eventSchema,
      agentCandidateSchema: sources.agentCandidateSchema,
      mapping: sources.mapping,
      validateEvent: ajv.getSchema(sources.eventSchema.$id),
      validateAgentCandidate: ajv.getSchema(sources.agentCandidateSchema.$id),
      validateAgentCandidateEnvelope: ajv.getSchema(sources.agentCandidateEnvelopeSchema.$id),
      validateProjectionPayload: ajv.getSchema(sources.projectionPayloadSchema.$id),
      validatePresentationRow: ajv.getSchema(sources.presentationRowSchema.$id),
      validateBindingAuthorityDelta: ajv.getSchema(sources.bindingAuthorityDeltaSchema.$id),
      validateRunBinding: ajv.getSchema(sources.runBindingSchema.$id),
      validateMessageBinding: ajv.getSchema(sources.messageBindingSchema.$id),
      validateOwnerBinding: ajv.getSchema(sources.ownerBindingSchema.$id),
      validateOwnerProjectionRow: ajv.getSchema(sources.ownerProjectionRowSchema.$id),
      validateStream: ajv.compile(sources.streamSchema),
      validateSnapshotAuthoritySchema: ajv.compile(sources.snapshotAuthoritySchema),
    });
  } catch (error) {
    fail("agui_schema_compile_invalid", error instanceof Error ? error.message : "unknown");
  }
}

function validateProfile(profile) {
  exactKeys(profile, ["profileId", "profileRevision", "lifecycle", "upstream", "typescript", "python", "rendering", "roles", "cursorConformance", "upgradePolicy"], "agui_profile_shape_invalid");
  if (profile.profileId !== "kokoro.agui.presentation-profile.v1" || profile.profileRevision !== PROFILE_REVISION || profile.lifecycle !== "contract-only") fail("agui_profile_identity_invalid");
  if (profile.upstream?.repository !== AGUI_UPSTREAM_REPOSITORY || profile.upstream?.commit !== AGUI_UPSTREAM_COMMIT) fail("agui_upstream_pin_invalid");
  if (
    profile.typescript?.core?.package !== "@ag-ui/core" || profile.typescript.core.version !== AGUI_CORE_VERSION ||
    profile.typescript.core.integrity !== AGUI_CORE_INTEGRITY || profile.typescript.core.schemaAuthority !== true
  ) fail("agui_core_pin_invalid");
  if (profile.typescript?.client?.package !== "@ag-ui/client" || profile.typescript.client.version !== "0.0.57" || profile.typescript.client.transportRole !== "forbidden") fail("agui_client_role_invalid");
  if (
    profile.python?.package !== "ag-ui-protocol" || profile.python.versionAtCommit !== "0.1.19" ||
    profile.python.source?.kind !== "git" || profile.python.source.repository !== AGUI_UPSTREAM_REPOSITORY ||
    profile.python.source.subdirectory !== "sdks/python" || profile.python.source.commit !== AGUI_UPSTREAM_COMMIT
  ) fail("agui_python_source_invalid");
  if (profile.rendering?.assistantUi?.package !== "@assistant-ui/react" || profile.rendering.assistantUi.version !== "0.14.28" || profile.rendering.assistantUi.role !== "rendering-adapter-only") fail("agui_rendering_pin_invalid");
  const expectedRoles = {
    agent: ["kokoro-agent", true, false, false, false, false, false, false],
    session: ["kokoro-session", false, true, false, true, true, true, false],
    web: ["kokoro-web", false, false, true, false, false, false, false],
  };
  exactKeys(profile.roles, Object.keys(expectedRoles), "agui_roles_shape_invalid");
  for (const [name, expected] of Object.entries(expectedRoles)) {
    exactKeys(profile.roles[name], AGENT_ROLE_KEYS, "agui_role_shape_invalid");
    if (canonical(AGENT_ROLE_KEYS.map((key) => profile.roles[name][key])) !== canonical(expected)) fail("agui_role_invalid", name);
  }
  exactKeys(profile.cursorConformance, ["format", "keyRevision", "aad", "claims", "keyMaterialPolicy"], "agui_cursor_profile_invalid");
  if (
    profile.cursorConformance.format !== "aes-256-gcm-closed-claims-v1" ||
    profile.cursorConformance.keyRevision !== CURSOR_KEY_REVISION ||
    profile.cursorConformance.aad !== CURSOR_AAD.toString("utf8") ||
    profile.cursorConformance.keyMaterialPolicy !== "public-conformance-fixture-only"
  ) fail("agui_cursor_profile_invalid");
  exactArray(profile.cursorConformance.claims, CURSOR_CLAIM_KEYS, "agui_cursor_profile_invalid");
  if (!Object.values(profile.upgradePolicy ?? {}).every((value) => value === true)) fail("agui_upgrade_policy_invalid");
}

function validateAgentCandidateProfile(profile) {
  exactKeys(
    profile,
    ["profileId", "profileRevision", "lifecycle", "eventSchema", "envelopeSchema", "producer", "consumer", "allowedEventTypes", "activityAuthority", "forbiddenEventTypes", "forbiddenEventFamilies", "forbiddenFields", "terminalPolicy", "projectionPolicy", "identityPolicy", "eventScopePolicy", "activation"],
    "agui_agent_candidate_profile_shape_invalid",
  );
  if (
    profile.profileId !== "kokoro.agui.agent-event-candidate-profile.v1" ||
    profile.profileRevision !== AGENT_CANDIDATE_PROFILE_REVISION || profile.lifecycle !== "contract-only" ||
    profile.eventSchema !== "https://contracts.kokoro.invalid/agent-agui-event-candidate.v1.schema.json" ||
    profile.envelopeSchema !== "https://contracts.kokoro.invalid/agent-agui-candidate-envelope.v1.schema.json" ||
    profile.producer !== "kokoro-agent" || profile.consumer !== "kokoro-session"
  ) fail("agui_agent_candidate_profile_identity_invalid");
  exactArray(profile.allowedEventTypes, AGENT_CANDIDATE_EVENT_TYPES, "agui_agent_candidate_events_invalid");
  if (profile.activityAuthority !== "kokoro.agui.activity-authority.v1") fail("agui_agent_candidate_activity_authority_invalid");
  const forbiddenExpected = OFFICIAL_EVENT_TYPES.filter((type) => !AGENT_CANDIDATE_EVENT_TYPES.includes(type));
  if (new Set(profile.forbiddenEventTypes).size !== forbiddenExpected.length || forbiddenExpected.some((type) => !profile.forbiddenEventTypes.includes(type))) {
    fail("agui_agent_candidate_forbidden_events_incomplete");
  }
  for (const family of ["raw", "state", "messages", "delta", "native-tool", "reasoning", "thinking", "step", "chunk", "custom"]) {
    if (!profile.forbiddenEventFamilies.includes(family)) fail("agui_agent_candidate_forbidden_family_missing", family);
  }
  for (const field of ["rawEvent", "raw_event", "providerEvent", "provider_event", "messages", "input", "result", "extra"]) {
    if (!profile.forbiddenFields.includes(field)) fail("agui_agent_candidate_forbidden_field_missing", field);
  }
  exactKeys(profile.terminalPolicy, ["runFinished", "runError", "canceledOrInterrupted"], "agui_agent_candidate_terminal_policy_invalid");
  if (
    profile.terminalPolicy.runFinished !== "success-only" || profile.terminalPolicy.runError !== "failure-only" ||
    profile.terminalPolicy.canceledOrInterrupted !== "session-owned-projection"
  ) fail("agui_agent_candidate_terminal_policy_invalid");
  exactKeys(profile.projectionPolicy, ["sessionAdmission", "runFinishedOutcome", "routeProjection", "ownerActivityProjection"], "agui_agent_candidate_projection_policy_invalid");
  if (
    profile.projectionPolicy.sessionAdmission !== "validate-before-durable-projection" ||
    profile.projectionPolicy.runFinishedOutcome !== "strip-after-success-validation" ||
    profile.projectionPolicy.routeProjection !== "resolve-through-session-presentation-binding" ||
    profile.projectionPolicy.ownerActivityProjection !== "session-projects-admitted-owner-facts-without-content-synthesis"
  ) fail("agui_agent_candidate_projection_policy_invalid");
  exactKeys(profile.identityPolicy, ["candidateRefDomain", "candidateRefMaterial", "sourceEventRef", "sourceOrdinal", "sourceFixtureOrder", "internalThreadRef", "recordedAt", "eventDigest", "forbiddenAxes"], "agui_agent_candidate_identity_policy_invalid");
  if (
    profile.identityPolicy.candidateRefDomain !== "agui_candidate:sha256" ||
    profile.identityPolicy.sourceEventRef !== "agent-owner-stable-ref" ||
    profile.identityPolicy.sourceOrdinal !== "uint64-decimal-string-strictly-increasing-per-run-starts-at-zero" ||
    profile.identityPolicy.sourceFixtureOrder !== "owner-log-order-within-internalRunRef" ||
    profile.identityPolicy.internalThreadRef !== "agent.thread:-branded-opaque-owner-ref-established-by-zero-run-start" ||
    profile.identityPolicy.recordedAt !== "canonical-utc-ms-equals-event-timestamp" ||
    profile.identityPolicy.eventDigest !== "sha256-rfc8785-jcs-event"
  ) fail("agui_agent_candidate_identity_policy_invalid");
  exactArray(
    profile.identityPolicy.candidateRefMaterial,
    ["profileRevision", "internalRunRef", "internalThreadRef", "internalMessageRef-or-empty", "sourceEventRef", "sourceOrdinal-decimal", "recordedAt", "eventDigest"],
    "agui_agent_candidate_identity_policy_invalid",
  );
  exactArray(profile.identityPolicy.forbiddenAxes, ["siteId", "userId", "sessionId", "cursor", "sseId", "sseEvent"], "agui_agent_candidate_identity_policy_invalid");
  exactKeys(profile.eventScopePolicy, ["runStartedAndFinished", "runError", "textAndActivity"], "agui_agent_candidate_scope_policy_invalid");
  if (
    profile.eventScopePolicy.runStartedAndFinished !== "threadId=internalThreadRef-and-runId=internalRunRef-and-no-parentRunId" ||
    profile.eventScopePolicy.runError !== "outer-route-matches-zero-run-start-thread-authority" ||
    profile.eventScopePolicy.textAndActivity !== "messageId=internalMessageRef"
  ) fail("agui_agent_candidate_scope_policy_invalid");
  exactKeys(profile.activation, ["runtimeImplemented", "compatibilityEvidence", "browserTransport"], "agui_agent_candidate_activation_invalid");
  if (Object.values(profile.activation).some((value) => value !== false)) fail("agui_agent_candidate_activation_invalid");
}

function validateActivityAuthority(authority, eventSchema, candidateSchema) {
  exactKeys(
    authority,
    ["registryId", "profileRevision", "lifecycle", "outerEventAuthority", "payloadSchema", "identityPolicy", "activities", "sessionOwnerCustomEvents"],
    "agui_activity_authority_shape_invalid",
  );
  if (
    authority.registryId !== "kokoro.agui.activity-authority.v1" || authority.profileRevision !== PROFILE_REVISION ||
    authority.lifecycle !== "contract-only" || authority.outerEventAuthority !== "official-ag-ui" ||
    authority.payloadSchema !== eventSchema.$id
  ) fail("agui_activity_authority_identity_invalid");
  exactKeys(
    authority.identityPolicy,
    ["ownerIdentity", "ownerVersion", "updatedAt", "activityMessageIdentity", "textContainer"],
    "agui_activity_authority_identity_policy_invalid",
  );
  if (
    authority.identityPolicy.ownerIdentity !== "immutable-from-first-accepted-replacement" ||
    authority.identityPolicy.ownerVersion !== "positive-uint64-decimal-string" ||
    authority.identityPolicy.updatedAt !== "canonical-utc-milliseconds" ||
    authority.identityPolicy.activityMessageIdentity !== "independent-owner-message-not-derived-from-text" ||
    authority.identityPolicy.textContainer !== "optional"
  ) fail("agui_activity_authority_identity_policy_invalid");
  if (!Array.isArray(authority.activities) || authority.activities.length !== ACTIVITY_DEFINITIONS.length) {
    fail("agui_activity_authority_activities_invalid");
  }
  for (const [index, [activityType, payloadDefinition, ownerStateSource]] of ACTIVITY_DEFINITIONS.entries()) {
    const row = authority.activities[index];
    exactKeys(row, ["activityType", "payloadDefinition", "candidateSource", "candidateStatePolicy", "forbiddenCandidateFields", "terminalOwnerStateSource", "projectionOwner"], "agui_activity_authority_row_invalid");
    const candidateSource = ownerStateSource === "kokoro-agent" ? "kokoro-agent" : null;
    const candidateStatePolicy = activityType === "kokoro.hitl.v1"
      ? "pending-proposal-only"
      : candidateSource === null ? "forbidden" : "full-owner-replacement";
    const terminalOwnerStateSource = activityType === "kokoro.hitl.v1" ? "kokoro-session" : ownerStateSource;
    const forbiddenCandidateFields = activityType === "kokoro.hitl.v1" ? ["receiptRef"] : [];
    if (
      row.activityType !== activityType || row.payloadDefinition !== payloadDefinition || row.candidateSource !== candidateSource ||
      row.candidateStatePolicy !== candidateStatePolicy || canonical(row.forbiddenCandidateFields) !== canonical(forbiddenCandidateFields) ||
      row.terminalOwnerStateSource !== terminalOwnerStateSource || row.projectionOwner !== "kokoro-session" ||
      eventSchema.$defs?.[payloadDefinition]?.properties?.activityType?.const !== activityType
    ) fail("agui_activity_authority_row_invalid", activityType);
    const content = eventSchema.$defs[payloadDefinition]?.properties?.content;
    if (
      content?.additionalProperties !== false || !content.required?.includes("ownerVersion") || !content.required?.includes("updatedAt") ||
      content.properties?.ownerVersion?.$ref !== "#/$defs/positiveUint64" || content.properties?.updatedAt?.$ref !== "#/$defs/canonicalUtcMs"
    ) fail("agui_activity_authority_payload_invalid", activityType);
  }
  const agentRows = authority.activities.filter(({ candidateSource }) => candidateSource === "kokoro-agent");
  exactArray(agentRows.map(({ activityType }) => activityType), AGENT_CANDIDATE_ACTIVITY_TYPES, "agui_activity_authority_agent_set_invalid");
  exactArray(
    authority.activities.filter(({ terminalOwnerStateSource }) => terminalOwnerStateSource === "kokoro-platform").map(({ activityType }) => activityType),
    PLATFORM_OWNER_ACTIVITY_TYPES,
    "agui_activity_authority_platform_set_invalid",
  );
  exactArray(candidateSchema.$defs.activityCandidate.properties.activityType.enum, AGENT_CANDIDATE_ACTIVITY_TYPES, "agui_activity_authority_candidate_schema_invalid");
  for (const [index, row] of agentRows.entries()) {
    const branch = candidateSchema.$defs.activityCandidate.allOf[index];
    const contentRule = branch?.then?.properties?.content;
    const expectedPayloadRef = `${eventSchema.$id}#/$defs/${row.payloadDefinition}/properties/content`;
    const actualPayloadRef = row.activityType === "kokoro.hitl.v1" ? contentRule?.allOf?.[0]?.$ref : contentRule?.$ref;
    if (
      branch?.if?.properties?.activityType?.const !== row.activityType ||
      actualPayloadRef !== expectedPayloadRef
    ) fail("agui_activity_authority_candidate_schema_invalid", row.activityType);
    if (row.activityType === "kokoro.hitl.v1") {
      const policy = contentRule?.allOf?.[1];
      if (
        policy?.type !== "object" || policy?.properties?.status?.const !== "pending" || policy?.not?.type !== "object" ||
        canonical(Object.keys(policy.not.properties ?? {})) !== canonical(["receiptRef"]) ||
        canonical(policy.not.required) !== canonical(["receiptRef"])
      ) {
        fail("agui_activity_authority_hitl_candidate_policy_invalid");
      }
    }
  }
  exactArray(
    authority.sessionOwnerCustomEvents.map(({ name }) => name),
    ["kokoro.control.replace.v1", "kokoro.receipt.replace.v1"],
    "agui_activity_authority_custom_set_invalid",
  );
  for (const [index, payloadDefinition] of ["customControl", "customReceipt"].entries()) {
    const row = authority.sessionOwnerCustomEvents[index];
    exactKeys(row, ["name", "payloadDefinition", "ownerStateSource", "projectionOwner"], "agui_activity_authority_custom_row_invalid");
    if (
      row.payloadDefinition !== payloadDefinition || row.ownerStateSource !== "kokoro-session" || row.projectionOwner !== "kokoro-session" ||
      eventSchema.$defs?.[payloadDefinition]?.properties?.name?.const !== row.name
    ) fail("agui_activity_authority_custom_row_invalid", row.name);
  }
  const hitl = eventSchema.$defs.activityHitl.properties.content;
  for (const field of ["ownerRef", "decisionGroupRef", "requiredOwnerRefs", "controlRef", "ownerVersion", "updatedAt"]) {
    if (!hitl.required.includes(field)) fail("agui_activity_authority_hitl_invalid", field);
  }
  if (Object.hasOwn(hitl.properties, "expectedVersion")) fail("agui_activity_authority_hitl_invalid", "expectedVersion");
  if (
    eventSchema.$defs.canonicalUtcMs?.minLength !== 24 || eventSchema.$defs.canonicalUtcMs?.maxLength !== 24 ||
    eventSchema.$defs.canonicalUtcMs?.pattern !== "^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\\.[0-9]{3}Z$"
  ) fail("agui_activity_authority_time_format_invalid");
  if (eventSchema.$defs.timestamp?.minimum !== 0 || eventSchema.$defs.timestamp?.maximum !== 253_402_300_799_999) {
    fail("agui_activity_authority_timestamp_range_invalid");
  }
}

function validateAgentCandidateSchemaContract(schema) {
  exactKeys(schema, ["$schema", "$id", "title", "description", "oneOf", "$defs"], "agui_agent_candidate_schema_shape_invalid");
  if (
    schema.$schema !== "https://json-schema.org/draft/2020-12/schema" ||
    schema.$id !== "https://contracts.kokoro.invalid/agent-agui-event-candidate.v1.schema.json"
  ) fail("agui_agent_candidate_schema_identity_invalid");
  const presentationSchemaId = "https://contracts.kokoro.invalid/kokoro-agui-presentation-event.v1.schema.json";
  exactArray(
    schema.oneOf,
    [
      { $ref: "#/$defs/runStartedWithoutParent" },
      { $ref: "#/$defs/runFinishedSuccess" },
      { $ref: "https://contracts.kokoro.invalid/kokoro-agui-presentation-event.v1.schema.json#/$defs/runError" },
      { $ref: "#/$defs/textStart" },
      { $ref: "#/$defs/textContent" },
      { $ref: "#/$defs/textEnd" },
      { $ref: "#/$defs/activityCandidate" },
    ],
    "agui_agent_candidate_schema_refs_invalid",
  );
  exactKeys(
    schema.$defs,
    ["runStartedWithoutParent", "runFinishedSuccess", "textStart", "textContent", "textEnd", "activityCandidate"],
    "agui_agent_candidate_schema_defs_invalid",
  );
  const started = schema.$defs.runStartedWithoutParent;
  exactKeys(started, ["type", "additionalProperties", "required", "properties"], "agui_agent_candidate_run_started_shape_invalid");
  exactArray(started.required, ["type", "timestamp", "threadId", "runId"], "agui_agent_candidate_run_started_shape_invalid");
  if (
    started.type !== "object" || started.additionalProperties !== false || started.properties?.type?.const !== EventType.RUN_STARTED ||
    Object.hasOwn(started.properties, "parentRunId")
  ) fail("agui_agent_candidate_run_started_shape_invalid");
  const success = schema.$defs.runFinishedSuccess;
  exactKeys(success, ["type", "additionalProperties", "required", "properties"], "agui_agent_candidate_run_finished_shape_invalid");
  exactArray(success.required, ["type", "timestamp", "threadId", "runId", "outcome"], "agui_agent_candidate_run_finished_shape_invalid");
  if (
    success.type !== "object" || success.additionalProperties !== false || success.properties?.type?.const !== EventType.RUN_FINISHED ||
    success.properties?.outcome?.properties?.type?.const !== "success" || success.properties.outcome.additionalProperties !== false ||
    Object.hasOwn(success.properties, "result")
  ) fail("agui_agent_candidate_run_finished_shape_invalid");
  for (const name of ["textStart", "textContent", "textEnd"]) {
    const definition = schema.$defs[name];
    if (
      definition?.type !== "object" || definition.additionalProperties !== false ||
      definition.properties?.messageId?.$ref !== `${presentationSchemaId}#/$defs/id`
    ) fail("agui_agent_candidate_schema_defs_invalid", name);
  }
  const activity = schema.$defs.activityCandidate;
  if (
    activity?.type !== "object" || activity.additionalProperties !== false ||
    activity.properties?.messageId?.$ref !== `${presentationSchemaId}#/$defs/id` ||
    activity.properties?.activityType?.enum?.length !== AGENT_CANDIDATE_ACTIVITY_TYPES.length ||
    activity.allOf?.length !== AGENT_CANDIDATE_ACTIVITY_TYPES.length
  ) fail("agui_agent_candidate_schema_defs_invalid", "activityCandidate");
}

function validateMappingRegistry(mapping) {
  exactKeys(mapping, ["registryId", "profileRevision", "lifecycle", "owner", "sourceContract", "allowedEventTypes", "allowedActivityTypes", "allowedCustomNames", "forbiddenEventTypes", "forbiddenEventFamilies", "forbiddenFields", "mappings", "projectionPolicy", "transportPolicy", "snapshotPolicy", "limits"], "agui_mapping_shape_invalid");
  if (mapping.registryId !== "kokoro.agui.presentation-mapping.v1" || mapping.profileRevision !== PROFILE_REVISION || mapping.lifecycle !== "contract-only" || mapping.owner !== "kokoro-session" || mapping.sourceContract !== "https://contracts.kokoro.invalid/session-agui-presentation-row.v1.schema.json") fail("agui_mapping_identity_invalid");
  exactArray(mapping.allowedEventTypes, ALLOWED_EVENT_TYPES, "agui_allowed_events_invalid");
  const forbiddenExpected = OFFICIAL_EVENT_TYPES.filter((type) => !ALLOWED_EVENT_TYPES.includes(type));
  if (new Set(mapping.forbiddenEventTypes).size !== forbiddenExpected.length || forbiddenExpected.some((type) => !mapping.forbiddenEventTypes.includes(type))) fail("agui_forbidden_events_incomplete");
  for (const family of ["raw", "state", "messages", "delta", "native-tool", "reasoning", "thinking", "step", "chunk", "unknown-custom"]) {
    if (!mapping.forbiddenEventFamilies.includes(family)) fail("agui_forbidden_family_missing", family);
  }
  if (!mapping.forbiddenFields.includes("rawEvent")) fail("agui_raw_event_policy_missing");
  const sourceKinds = new Set();
  for (const entry of mapping.mappings) {
    exactKeys(
      entry,
      entry.discriminator === undefined
        ? ["sourceKind", "eventType", "bindingAuthorityDeltaKind"]
        : ["sourceKind", "eventType", "discriminator", "bindingAuthorityDeltaKind"],
      "agui_mapping_entry_shape_invalid",
    );
    if (sourceKinds.has(entry.sourceKind)) fail("agui_mapping_source_duplicate", entry.sourceKind);
    sourceKinds.add(entry.sourceKind);
    if (!ALLOWED_EVENT_TYPES.includes(entry.eventType)) fail("agui_mapping_event_forbidden", entry.sourceKind);
    if (entry.eventType === EventType.ACTIVITY_SNAPSHOT && !mapping.allowedActivityTypes.includes(entry.discriminator)) fail("agui_mapping_activity_unknown", entry.sourceKind);
    if (entry.eventType === EventType.CUSTOM && !mapping.allowedCustomNames.includes(entry.discriminator)) fail("agui_mapping_custom_unknown", entry.sourceKind);
    if (![EventType.ACTIVITY_SNAPSHOT, EventType.CUSTOM].includes(entry.eventType) && entry.discriminator !== undefined) fail("agui_mapping_discriminator_invalid", entry.sourceKind);
    const requiredDeltaKind = entry.eventType === EventType.ACTIVITY_SNAPSHOT ||
      (entry.eventType === EventType.CUSTOM && OWNER_DELTA_CUSTOM_NAMES.has(entry.discriminator))
      ? "owner.replace"
      : BINDING_DELTA_KIND_BY_EVENT.get(entry.eventType) ?? "none";
    if (entry.bindingAuthorityDeltaKind !== requiredDeltaKind) fail("agui_mapping_binding_delta_policy_invalid", entry.sourceKind);
  }
  exactKeys(
    mapping.projectionPolicy,
    [
      "durableRowToFrameCardinality", "dropDurableRows", "fanOutDurableRows", "bindingAuthorityDelta",
      "sourceProjectionVersion", "publicSourceEventIdentity", "presentationIdentity", "customRunOwnerVersion",
      "ownerProjection", "agentCandidateSourceProfile", "agentRawPassthrough", "providerPayloadPassthrough",
    ],
    "agui_projection_policy_invalid",
  );
  exactArray(
    mapping.projectionPolicy.ownerProjection.lateTerminal.messageEndedRunOpen,
    OWNER_MESSAGE_ENDED_RUN_OPEN,
    "agui_projection_policy_invalid",
  );
  exactArray(
    mapping.projectionPolicy.ownerProjection.lateTerminal.terminalRunMayCreate,
    OWNER_TERMINAL_MAY_CREATE,
    "agui_projection_policy_invalid",
  );
  exactArray(
    mapping.projectionPolicy.ownerProjection.lateTerminal.terminalRunMayConvergeExisting,
    OWNER_TERMINAL_MAY_CONVERGE,
    "agui_projection_policy_invalid",
  );
  exactArray(
    mapping.projectionPolicy.ownerProjection.lateTerminal.terminalRunMayNotCreate,
    OWNER_TERMINAL_MAY_NOT_CREATE,
    "agui_projection_policy_invalid",
  );
  exactKeys(
    mapping.projectionPolicy.bindingAuthorityDelta,
    ["cardinality", "atomicity", "mutation", "patch"],
    "agui_projection_policy_invalid",
  );
  exactKeys(
    mapping.projectionPolicy.sourceProjectionVersion,
    ["wire", "semantic", "javascriptNumber"],
    "agui_projection_policy_invalid",
  );
  exactKeys(
    mapping.projectionPolicy.publicSourceEventIdentity,
    [
      "wire", "runtimeAssignment", "runtimeDerivationContract", "conformanceFixtureGenerator",
      "agentSourceEventRefEquality", "agentSourceEventRefExposure", "webDerivation",
    ],
    "agui_projection_policy_invalid",
  );
  exactKeys(
    mapping.projectionPolicy.presentationIdentity,
    [
      "wire", "runtimeAssignment", "runtimeDerivationContract", "conformanceFixtureGenerator",
      "privateRefEquality", "privateRefSubstring", "webDerivation",
    ],
    "agui_projection_policy_invalid",
  );
  exactKeys(
    mapping.projectionPolicy.customRunOwnerVersion,
    ["wire", "semantic", "legacyProjectionVersion", "javascriptNumber"],
    "agui_projection_policy_invalid",
  );
  exactKeys(
    mapping.projectionPolicy.ownerProjection,
    ["binding", "snapshotReducer", "snapshotCursorSequencing", "javascriptOwnerVersion", "lateTerminal"],
    "agui_projection_policy_invalid",
  );
  exactKeys(
    mapping.projectionPolicy.ownerProjection.lateTerminal,
    [
      "messageEndedRunOpen", "terminalRunMayCreate", "terminalRunReceiptRequiresExistingControl",
      "terminalRunMayConvergeExisting", "terminalRunMayNotCreate", "textOrRunReopen",
    ],
    "agui_projection_policy_invalid",
  );
  if (
    mapping.projectionPolicy?.durableRowToFrameCardinality !== "exactly-one" || mapping.projectionPolicy.dropDurableRows !== false ||
    mapping.projectionPolicy.fanOutDurableRows !== false || mapping.projectionPolicy.agentCandidateSourceProfile !== AGENT_CANDIDATE_PROFILE_REVISION ||
    mapping.projectionPolicy.agentRawPassthrough !== false || mapping.projectionPolicy.providerPayloadPassthrough !== false ||
    mapping.projectionPolicy.bindingAuthorityDelta.cardinality !== "exactly-one-required" ||
    mapping.projectionPolicy.bindingAuthorityDelta.atomicity !== "same-projection-payload-and-durable-row" ||
    mapping.projectionPolicy.bindingAuthorityDelta.mutation !== "complete-replacement-only" ||
    mapping.projectionPolicy.bindingAuthorityDelta.patch !== "forbidden" ||
    mapping.projectionPolicy.sourceProjectionVersion.wire !== "positive-uint64-decimal-string" ||
    mapping.projectionPolicy.sourceProjectionVersion.semantic !== "session-projection-revision" ||
    mapping.projectionPolicy.sourceProjectionVersion.javascriptNumber !== "forbidden" ||
    mapping.projectionPolicy.publicSourceEventIdentity.wire !== "presentation.event:-branded-session-owned-opaque-ref" ||
    mapping.projectionPolicy.publicSourceEventIdentity.runtimeAssignment !== "session-owner-assigned" ||
    mapping.projectionPolicy.publicSourceEventIdentity.runtimeDerivationContract !== "none" ||
    mapping.projectionPolicy.publicSourceEventIdentity.conformanceFixtureGenerator !== "root-test-only-not-runtime" ||
    mapping.projectionPolicy.publicSourceEventIdentity.agentSourceEventRefEquality !== "forbidden" ||
    mapping.projectionPolicy.publicSourceEventIdentity.agentSourceEventRefExposure !== "private-provenance-only" ||
    mapping.projectionPolicy.publicSourceEventIdentity.webDerivation !== "forbidden" ||
    mapping.projectionPolicy.presentationIdentity.wire !== "type-branded-256-bit-opaque-ref" ||
    mapping.projectionPolicy.presentationIdentity.runtimeAssignment !== "session-owner-assigned" ||
    mapping.projectionPolicy.presentationIdentity.runtimeDerivationContract !== "none" ||
    mapping.projectionPolicy.presentationIdentity.conformanceFixtureGenerator !== "root-test-only-not-runtime" ||
    mapping.projectionPolicy.presentationIdentity.privateRefEquality !== "forbidden" ||
    mapping.projectionPolicy.presentationIdentity.privateRefSubstring !== "forbidden" ||
    mapping.projectionPolicy.presentationIdentity.webDerivation !== "forbidden" ||
    mapping.projectionPolicy.customRunOwnerVersion.wire !== "positive-uint64-decimal-string" ||
    mapping.projectionPolicy.customRunOwnerVersion.semantic !== "run-owner-version" ||
    mapping.projectionPolicy.customRunOwnerVersion.legacyProjectionVersion !== "forbidden" ||
    mapping.projectionPolicy.customRunOwnerVersion.javascriptNumber !== "forbidden" ||
    mapping.projectionPolicy.ownerProjection.binding !== "complete-immutable-owner-replacement-on-every-owner-row" ||
    mapping.projectionPolicy.ownerProjection.snapshotReducer !== "same-owner-identity-version-terminal-reducer-as-live" ||
    mapping.projectionPolicy.ownerProjection.snapshotCursorSequencing !== "forbidden" ||
    mapping.projectionPolicy.ownerProjection.javascriptOwnerVersion !== "forbidden" ||
    mapping.projectionPolicy.ownerProjection.lateTerminal.textOrRunReopen !== "forbidden" ||
    mapping.projectionPolicy.ownerProjection.lateTerminal.terminalRunReceiptRequiresExistingControl !== true
  ) fail("agui_projection_policy_invalid");
  if (
    mapping.transportPolicy?.sseId !== "opaque-session-cursor" || mapping.transportPolicy.sseEvent !== "exact-inner-event-type" ||
    mapping.transportPolicy.resumeHeader !== "Last-Event-ID" || mapping.transportPolicy.drainingDurability !== "non-durable" ||
    mapping.transportPolicy.stockAguiClientTransport !== "forbidden"
  ) fail("agui_transport_policy_invalid");
  exactArray(mapping.transportPolicy.cursorBindingFields, ["sessionId", "streamEpoch", "durableSeq", "profileRevision", "cursorProfileRevision"], "agui_cursor_binding_policy_invalid");
  exactArray(mapping.transportPolicy.grantBindingFields, ["sessionId", "sessionContractRevision", "presentationProfileRevision", "cursorProfileRevision"], "agui_grant_binding_policy_invalid");
  if (
    mapping.snapshotPolicy?.hydrateAuthority !== "session-browser-v3-http-snapshot" || mapping.snapshotPolicy.repairAuthority !== "session-browser-v3-http-snapshot" ||
    mapping.snapshotPolicy.streamHydration !== "forbidden" || mapping.snapshotPolicy.timeWatermarkField !== "lastRecordedAt" ||
    mapping.snapshotPolicy.timeWatermarkAuthority !== "session-durable-head"
  ) fail("agui_snapshot_policy_invalid");
  for (const [key, expected] of [
    ["ownerBindingsMaximum", 2048], ["ownerProjectionRowsMaximum", 2048],
    ["ownerProjectionCanonicalBytesMaximum", 16777216], ["ownerBindingsPerMessageMaximum", 64],
    ["controlReceiptBindingsPerRunMaximum", 256], ["ownerLinkDepthMaximum", 2],
  ]) {
    if (mapping.snapshotPolicy?.[key] !== expected) fail("agui_snapshot_policy_invalid", key);
  }
  for (const [key, lower, upper] of [
    ["maximumFrameBytes", 1024, 262144], ["maximumEventBytes", 1024, 131072], ["maximumJsonDepth", 4, 32],
    ["maximumJsonNodes", 128, 16384], ["maximumObjectKeys", 8, 128], ["maximumArrayItems", 8, 512],
    ["maximumIdBytes", 32, 256], ["maximumCursorBytes", 128, 4096],
  ]) {
    const value = mapping.limits?.[key];
    if (!Number.isInteger(value) || value < lower || value > upper) fail("agui_limit_invalid", key);
  }
}

function jsonStats(value, depth = 0, result = { nodes: 0, depth: 0, maximumKeys: 0, maximumItems: 0 }) {
  result.nodes += 1;
  result.depth = Math.max(result.depth, depth);
  if (Array.isArray(value)) {
    result.maximumItems = Math.max(result.maximumItems, value.length);
    for (const child of value) jsonStats(child, depth + 1, result);
  } else if (value !== null && typeof value === "object") {
    const entries = Object.entries(value);
    result.maximumKeys = Math.max(result.maximumKeys, entries.length);
    for (const [, child] of entries) jsonStats(child, depth + 1, result);
  }
  return result;
}

function enforceLimits(value, limits, byteLimit, code) {
  if (Buffer.byteLength(JSON.stringify(value), "utf8") > byteLimit) fail(code, "bytes");
  const stats = jsonStats(value);
  if (stats.depth > limits.maximumJsonDepth || stats.nodes > limits.maximumJsonNodes || stats.maximumKeys > limits.maximumObjectKeys || stats.maximumItems > limits.maximumArrayItems) fail(code, "shape");
}

function uint64(value, code) {
  if (typeof value !== "string" || !/^(0|[1-9][0-9]{0,19})$/u.test(value)) fail(code, String(value));
  const parsed = BigInt(value);
  if (parsed > UINT64_MAXIMUM) fail(code, value);
  return parsed;
}

function validatePublicSourceEventId(value, source = undefined) {
  if (
    typeof value !== "string" || value.length > 128 || !PUBLIC_SOURCE_EVENT_ID.test(value) ||
    value.includes("agent.event")
  ) {
    fail("agui_public_source_event_id_invalid", String(value));
  }
  const cleartextAxes = source === undefined
    ? /^presentation\.event:[A-Za-z0-9._-]+:[0-9]+:[0-9]+$/u.test(value)
    : value.includes(`${source.sessionId}:${source.streamEpoch}:${source.durableSeq}`);
  if (cleartextAxes) fail("agui_public_source_event_axes_exposed", value);
}

function decodeBase64Url(value) {
  if (typeof value !== "string" || !/^[A-Za-z0-9_-]+$/u.test(value)) fail("agui_cursor_invalid");
  const decoded = Buffer.from(value, "base64url");
  if (decoded.toString("base64url") !== value) fail("agui_cursor_invalid");
  return decoded;
}

function decodeCursor(value, maximumBytes) {
  if (typeof value !== "string" || Buffer.byteLength(value, "utf8") > maximumBytes) fail("agui_cursor_invalid");
  const parts = value.split(".");
  if (parts.length !== 5 || parts[0] !== "v1" || parts[1] !== CURSOR_KEY_REVISION) fail("agui_cursor_invalid");
  const iv = decodeBase64Url(parts[2]);
  const ciphertext = decodeBase64Url(parts[3]);
  const tag = decodeBase64Url(parts[4]);
  if (iv.length !== 12 || ciphertext.length === 0 || tag.length !== 16) fail("agui_cursor_invalid");
  let plaintext;
  try {
    const decipher = createDecipheriv("aes-256-gcm", CURSOR_KEY, iv);
    decipher.setAAD(CURSOR_AAD);
    decipher.setAuthTag(tag);
    plaintext = Buffer.concat([decipher.update(ciphertext), decipher.final()]);
  } catch {
    fail("agui_cursor_invalid");
  }
  let claims;
  try {
    claims = JSON.parse(plaintext.toString("utf8"));
  } catch {
    fail("agui_cursor_invalid");
  }
  exactKeys(claims, CURSOR_CLAIM_KEYS, "agui_cursor_claims_invalid");
  if (Buffer.from(canonical(claims), "utf8").compare(plaintext) !== 0) fail("agui_cursor_claims_invalid", "noncanonical");
  if (claims.version !== 1 || claims.kind !== "stream" || claims.profileRevision !== PROFILE_REVISION || claims.cursorProfileRevision !== CURSOR_PROFILE_REVISION) fail("agui_cursor_claims_invalid");
  if (typeof claims.sessionId !== "string" || claims.sessionId.length === 0 || claims.sessionId.length > 128) fail("agui_cursor_claims_invalid");
  uint64(claims.streamEpoch, "agui_cursor_claims_invalid");
  uint64(claims.durableSeq, "agui_cursor_claims_invalid");
  return Object.freeze(claims);
}

function assertCursorScope(claims, expected) {
  for (const field of ["sessionId", "streamEpoch", "durableSeq", "profileRevision", "cursorProfileRevision"]) {
    if (claims[field] !== expected[field]) fail("agui_cursor_claim_scope_conflict", field);
  }
}

function issueCursor({ sessionId, streamEpoch, durableSeq }) {
  const claims = {
    version: 1,
    kind: "stream",
    sessionId,
    streamEpoch,
    durableSeq,
    profileRevision: PROFILE_REVISION,
    cursorProfileRevision: CURSOR_PROFILE_REVISION,
  };
  const plaintext = Buffer.from(canonical(claims), "utf8");
  const iv = createHash("sha256").update(Buffer.concat([CURSOR_AAD, plaintext])).digest().subarray(0, 12);
  const cipher = createCipheriv("aes-256-gcm", CURSOR_KEY, iv);
  cipher.setAAD(CURSOR_AAD);
  const ciphertext = Buffer.concat([cipher.update(plaintext), cipher.final()]);
  return ["v1", CURSOR_KEY_REVISION, iv.toString("base64url"), ciphertext.toString("base64url"), cipher.getAuthTag().toString("base64url")].join(".");
}

function createSemanticIdentityRegistries() {
  return {
    cursorIds: new Set(),
    cursorClaims: new Set(),
    sourceEventIds: new Set(),
    rowRefs: new Set(),
    runBindingRefs: new Set(),
    presentationRunIds: new Set(),
    internalRunSegments: new Set(),
    messageBindingRefs: new Set(),
    presentationMessageIds: new Set(),
    ownerBindingRefs: new Set(),
    presentationOwnerMessageIds: new Set(),
    internalMessageSegments: new Set(),
  };
}

function registerGlobalIdentity(registry, identity, code) {
  if (registry.has(identity)) fail(code, identity);
  registry.add(identity);
}

function cursorClaimIdentity(claims) {
  return canonical([
    claims.sessionId,
    claims.streamEpoch,
    claims.durableSeq,
    claims.profileRevision,
    claims.cursorProfileRevision,
  ]);
}

function parseCanonicalUtcMs(value, code = "agui_snapshot_time_watermark_invalid") {
  if (typeof value !== "string" || !/^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3}Z$/u.test(value)) {
    fail(code);
  }
  const parsed = Date.parse(value);
  if (!Number.isFinite(parsed) || new Date(parsed).toISOString() !== value) fail(code);
  return parsed;
}

function bindingTimestampWatermark(runBindings, messageBindings, ownerBindings = [], ownerProjectionRows = []) {
  let watermark = Number.NEGATIVE_INFINITY;
  for (const binding of [...runBindings, ...messageBindings]) {
    for (const field of ["openedAt", "terminalAt", "endedAt"]) {
      if (binding?.[field] === null || binding?.[field] === undefined) continue;
      const parsed = parseCanonicalUtcMs(binding[field], "agui_snapshot_binding_time_invalid");
      watermark = Math.max(watermark, parsed);
    }
  }
  for (const binding of ownerBindings) {
    watermark = Math.max(watermark, parseCanonicalUtcMs(binding.boundAt, "agui_snapshot_binding_time_invalid"));
  }
  for (const row of ownerProjectionRows) {
    watermark = Math.max(watermark, parseCanonicalUtcMs(row.recordedAt, "agui_owner_projection_time_invalid"));
  }
  return watermark;
}

function snapshotBindingEvidenceCount(runBindings, messageBindings, ownerBindings = [], ownerProjectionRows = []) {
  const evidence = new Set();
  for (const binding of runBindings) {
    evidence.add(binding.openedBySourceEventId);
    if (binding.terminalSourceEventId !== null) evidence.add(binding.terminalSourceEventId);
  }
  for (const binding of messageBindings) {
    evidence.add(binding.openedBySourceEventId);
    if (binding.endedBySourceEventId !== null) evidence.add(binding.endedBySourceEventId);
  }
  for (const binding of ownerBindings) evidence.add(binding.boundBySourceEventId);
  for (const row of ownerProjectionRows) evidence.add(row.sourceEventId);
  return BigInt(evidence.size);
}

function validateSnapshotTimeAuthority(
  snapshot,
  validateSchema,
  runBindings = [],
  messageBindings = [],
  ownerBindings = [],
  ownerProjectionRows = [],
  nextEventRecordedAt = undefined,
) {
  if (snapshot?.authority !== "session-browser-v3-http-snapshot" || snapshot.hydrate !== true || snapshot.repair !== true) {
    fail("agui_snapshot_authority_invalid");
  }
  if (snapshot.profileRevision !== PROFILE_REVISION) fail("agui_snapshot_profile_invalid");
  const durableSeq = uint64(snapshot?.durableSeq, "agui_snapshot_cursor_invalid");
  if ((durableSeq === 0n && snapshot?.lastRecordedAt !== null) || (durableSeq > 0n && snapshot?.lastRecordedAt === null)) {
    fail("agui_snapshot_time_watermark_invalid");
  }
  const watermark = durableSeq === 0n ? Number.NEGATIVE_INFINITY : parseCanonicalUtcMs(snapshot.lastRecordedAt);
  const outerAuthority = {
    ...snapshot, runBindings: [], messageBindings: [], ownerBindings: [], ownerProjectionRows: [],
  };
  if (!validateSchema(outerAuthority)) fail("agui_snapshot_authority_schema_invalid", validateSchema.errors?.[0]?.instancePath ?? "");
  if (
    durableSeq > 0n &&
    watermark < bindingTimestampWatermark(runBindings, messageBindings, ownerBindings, ownerProjectionRows)
  ) {
    fail("agui_snapshot_time_watermark_before_binding");
  }
  if (nextEventRecordedAt !== undefined && parseCanonicalUtcMs(nextEventRecordedAt, "agui_event_time_invalid") < watermark) {
    fail("agui_event_time_invalid", "snapshot-watermark");
  }
  return watermark;
}

function findKey(value, pattern) {
  if (Array.isArray(value)) return value.some((entry) => findKey(entry, pattern));
  if (value === null || typeof value !== "object") return false;
  return Object.entries(value).some(([key, child]) => pattern.test(key) || findKey(child, pattern));
}

function validateEventPreSchema(event, mapping) {
  if (event === null || typeof event !== "object" || Array.isArray(event) || typeof event.type !== "string") fail("agui_event_shape_invalid");
  if (Object.hasOwn(event, "rawEvent")) fail("agui_raw_event_forbidden");
  if (findKey(event, COT_KEY)) fail("agui_cot_forbidden");
  if (!mapping.allowedEventTypes.includes(event.type)) fail("agui_event_type_forbidden", event.type);
  if (event.type === EventType.CUSTOM && !mapping.allowedCustomNames.includes(event.name)) fail("agui_unknown_custom", String(event.name));
  if (event.type === EventType.CUSTOM && event.name === "kokoro.run.replace.v1") {
    const value = event.value;
    if (
      value === null || typeof value !== "object" || Array.isArray(value) ||
      Object.hasOwn(value, "projectionVersion") || !Object.hasOwn(value, "ownerVersion") ||
      uint64(value.ownerVersion, "agui_custom_run_owner_version_invalid") === 0n
    ) fail("agui_custom_run_owner_version_invalid");
  }
  if (event.type === EventType.ACTIVITY_SNAPSHOT && !mapping.allowedActivityTypes.includes(event.activityType)) fail("agui_unknown_activity", String(event.activityType));
  if (event.type === EventType.ACTIVITY_SNAPSHOT && event.activityType === "kokoro.tool-preview.v1" && findKey(event.content, TOOL_SECRET_KEY)) fail("agui_tool_secret_forbidden");
  const extra = Object.keys(event).find((key) => !(EVENT_FIELDS.get(event.type) ?? []).includes(key));
  if (extra !== undefined) fail("agui_event_extra_forbidden", extra);
}

function validateOwnerPresentationEvent(event) {
  if (
    event.type === EventType.CUSTOM &&
    ["kokoro.control.replace.v1", "kokoro.receipt.replace.v1"].includes(event.name)
  ) {
    const updatedAt = parseCanonicalUtcMs(event.value.updatedAt, "agui_owner_updated_at_invalid");
    if (updatedAt > event.timestamp) fail("agui_owner_updated_at_future");
    return;
  }
  if (event.type !== EventType.ACTIVITY_SNAPSHOT) return;
  const ownerVersion = uint64(event.content.ownerVersion, "agui_owner_version_invalid");
  if (ownerVersion === 0n) fail("agui_owner_version_invalid");
  const updatedAt = parseCanonicalUtcMs(event.content.updatedAt, "agui_owner_updated_at_invalid");
  if (updatedAt > event.timestamp) fail("agui_owner_updated_at_future");
  if (event.activityType === "kokoro.hitl.v1") {
    if (!event.content.requiredOwnerRefs.includes(event.content.ownerRef)) {
      fail("agui_hitl_owner_group_invalid", event.content.ownerRef);
    }
    return;
  }
  if (event.activityType === "kokoro.media.v1") {
    const candidateRefs = new Set();
    for (const [ordinal, candidate] of event.content.candidates.entries()) {
      if (candidate.ordinal !== ordinal || candidateRefs.has(candidate.candidateRef)) {
        fail("agui_media_candidate_identity_invalid", candidate.candidateRef);
      }
      candidateRefs.add(candidate.candidateRef);
      if (uint64(candidate.ownerVersion, "agui_media_candidate_version_invalid") === 0n) {
        fail("agui_media_candidate_version_invalid", candidate.candidateRef);
      }
    }
    if (
      event.content.costProjection !== undefined &&
      uint64(event.content.costProjection.ownerVersion, "agui_cost_link_version_invalid") === 0n
    ) fail("agui_cost_link_version_invalid");
    return;
  }
  if (event.activityType === "kokoro.artifact.v1" && event.content.availability === "ready") {
    if (event.content.display.kind !== event.content.mediaClass) fail("agui_artifact_display_class_invalid");
    return;
  }
  if (event.activityType === "kokoro.cost.v1" && event.content.state === "corrected") {
    if (uint64(event.content.correctsOwnerVersion, "agui_cost_correction_version_invalid") >= ownerVersion) {
      fail("agui_cost_correction_version_invalid");
    }
  }
}

const OPAQUE_PRESENTATION_IDENTITY = Object.freeze({
  runBindingRef: /^presentation\.run-binding:[0-9a-f]{64}$/u,
  threadId: /^presentation\.thread:[0-9a-f]{64}$/u,
  runId: /^presentation\.run:[0-9a-f]{64}$/u,
  messageBindingRef: /^presentation\.message-binding:[0-9a-f]{64}$/u,
  messageId: /^presentation\.message:[0-9a-f]{64}$/u,
  ownerBindingRef: /^presentation\.owner-binding:[0-9a-f]{64}$/u,
  ownerMessageId: /^presentation\.message:[0-9a-f]{64}$/u,
});

function validateOpaquePresentationIdentity(value, pattern) {
  if (typeof value !== "string" || !pattern.test(value)) {
    fail("agui_public_presentation_identity_invalid");
  }
}

function validateRunBindings(bindings, validateSchema, snapshot, identities) {
  if (!Array.isArray(bindings) || bindings.length === 0 || bindings.length > 256) fail("agui_run_bindings_invalid");
  const refs = new Map();
  const presentationIds = new Map();
  const sessionRunOwners = new Map();
  for (const binding of bindings) {
    validateOpaquePresentationIdentity(binding.bindingRef, OPAQUE_PRESENTATION_IDENTITY.runBindingRef);
    validateOpaquePresentationIdentity(binding.presentationThreadId, OPAQUE_PRESENTATION_IDENTITY.threadId);
    validateOpaquePresentationIdentity(binding.presentationRunId, OPAQUE_PRESENTATION_IDENTITY.runId);
    if (binding.resumeOfPresentationRunId !== null) {
      validateOpaquePresentationIdentity(binding.resumeOfPresentationRunId, OPAQUE_PRESENTATION_IDENTITY.runId);
    }
    if (binding.parentLineage?.parentPresentationRunId !== null) {
      validateOpaquePresentationIdentity(binding.parentLineage?.parentPresentationRunId, OPAQUE_PRESENTATION_IDENTITY.runId);
    }
    if (!validateSchema(binding)) fail("agui_run_binding_schema_invalid", validateSchema.errors?.[0]?.instancePath ?? "");
    validatePublicSourceEventId(binding.openedBySourceEventId);
    if (binding.terminalSourceEventId !== null) validatePublicSourceEventId(binding.terminalSourceEventId);
    if (binding.sessionId !== snapshot.sessionId || binding.profileRevision !== snapshot.profileRevision) fail("agui_run_binding_scope_conflict", binding.bindingRef);
    if (refs.has(binding.bindingRef) || presentationIds.has(binding.presentationRunId)) fail("agui_run_binding_duplicate");
    registerGlobalIdentity(identities.runBindingRefs, binding.bindingRef, "agui_global_run_binding_ref_duplicate");
    registerGlobalIdentity(identities.presentationRunIds, binding.presentationRunId, "agui_global_presentation_run_id_duplicate");
    refs.set(binding.bindingRef, binding);
    presentationIds.set(binding.presentationRunId, binding);
    if (binding.sessionRunId !== null && binding.segmentOrdinal === 0) {
      if (sessionRunOwners.has(binding.sessionRunId)) fail("agui_session_run_binding_duplicate", binding.sessionRunId);
      sessionRunOwners.set(binding.sessionRunId, binding.bindingRef);
    }
    if (Date.parse(binding.openedAt) > Date.parse(binding.terminalAt ?? binding.openedAt)) fail("agui_run_binding_time_invalid", binding.bindingRef);
  }
  for (const binding of refs.values()) {
    const { parentPresentationRunId } = binding.parentLineage;
    if (parentPresentationRunId === null) continue;
    if (parentPresentationRunId === binding.resumeOfPresentationRunId) fail("agui_resume_parent_confused", binding.bindingRef);
    const parent = presentationIds.get(parentPresentationRunId);
    if (
      parent === undefined || parent.sessionId !== binding.sessionId ||
      parent.bindingRef === binding.bindingRef || parent.presentationRunId === binding.presentationRunId
    ) fail("agui_parent_lineage_pair_invalid", binding.bindingRef);
  }
  for (const binding of refs.values()) {
    const visited = new Set([binding.presentationRunId]);
    let current = binding;
    while (current.parentLineage.parentPresentationRunId !== null) {
      const parentId = current.parentLineage.parentPresentationRunId;
      if (visited.has(parentId)) fail("agui_parent_lineage_cycle", binding.bindingRef);
      visited.add(parentId);
      current = presentationIds.get(parentId);
    }
  }
  for (const binding of refs.values()) {
    if (binding.segmentOrdinal === 0) continue;
    const previous = presentationIds.get(binding.resumeOfPresentationRunId);
    if (previous === undefined || previous.segmentOrdinal !== binding.segmentOrdinal - 1) {
      fail("agui_resume_segment_gap", binding.bindingRef);
    }
    if (canonical(binding.parentLineage) !== canonical(previous.parentLineage)) fail("agui_resume_parent_confused", binding.bindingRef);
    if (binding.presentationThreadId !== previous.presentationThreadId || binding.sessionId !== previous.sessionId) {
      fail("agui_resume_scope_conflict", binding.bindingRef);
    }
    if (binding.sessionRunId !== previous.sessionRunId) fail("agui_resume_session_run_conflict", binding.bindingRef);
  }
  for (const binding of refs.values()) {
    if (binding.parentLineage.parentPresentationRunId === null && binding.sessionRunId === null) {
      fail("agui_session_run_binding_missing", binding.bindingRef);
    }
    if (binding.parentLineage.parentPresentationRunId !== null && binding.sessionRunId !== null) {
      fail("agui_child_session_run_binding_forbidden", binding.bindingRef);
    }
  }
  return refs;
}

function validateM0RunBindingStates(runBindings, code) {
  for (const binding of runBindings) {
    const validState = (
      (binding.state === "open" && binding.terminalDisposition === null) ||
      (binding.state === "finished" && binding.terminalDisposition === "success") ||
      (binding.state === "error" && binding.terminalDisposition === "error")
    );
    if (!validState) fail(code, binding.bindingRef);
  }
}

function validateSnapshotBindingAuthority(snapshot, contracts) {
  const runBindings = snapshot.runBindings;
  const messageBindings = snapshot.messageBindings;
  const ownerBindings = snapshot.ownerBindings;
  const ownerProjectionRows = snapshot.ownerProjectionRows;
  const durableSeq = uint64(snapshot.durableSeq, "agui_snapshot_cursor_invalid");
  if (
    durableSeq === 0n &&
    (runBindings.length !== 0 || messageBindings.length !== 0 || ownerBindings.length !== 0 || ownerProjectionRows.length !== 0)
  ) {
    fail("agui_snapshot_zero_head_bindings_invalid");
  }
  if (snapshotBindingEvidenceCount(runBindings, messageBindings, ownerBindings, ownerProjectionRows) > durableSeq) {
    fail("agui_snapshot_binding_evidence_exceeds_head");
  }
  bindingTimestampWatermark(runBindings, messageBindings, ownerBindings, ownerProjectionRows);
  const identities = createSemanticIdentityRegistries();
  const runRefs = runBindings.length === 0
    ? new Map()
    : validateRunBindings(runBindings, contracts.validateRunBinding, snapshot, identities);
  const messageRefs = validateMessageBindings(messageBindings, contracts.validateMessageBinding, runRefs, snapshot, identities);
  const ownerRefs = validateOwnerBindings(ownerBindings, contracts, runRefs, messageRefs, snapshot, identities);
  validateOwnerProjectionRows(ownerProjectionRows, contracts, ownerRefs, snapshot);
  if (runBindings.length > 0 && new Set(runBindings.map(({ presentationThreadId }) => presentationThreadId)).size !== 1) {
    fail("agui_snapshot_thread_scope_invalid");
  }
  validateM0RunBindingStates(runBindings, "agui_snapshot_terminal_state_invalid");
}

function validateMessageBindings(bindings, validateSchema, runRefs, snapshot, identities) {
  if (!Array.isArray(bindings) || bindings.length > 512) fail("agui_message_bindings_invalid");
  const refs = new Map();
  const ids = new Set();
  const sessionMessageIds = new Set();
  const sessionTextPartIds = new Set();
  for (const binding of bindings) {
    validateOpaquePresentationIdentity(binding.bindingRef, OPAQUE_PRESENTATION_IDENTITY.messageBindingRef);
    validateOpaquePresentationIdentity(binding.presentationRunBindingRef, OPAQUE_PRESENTATION_IDENTITY.runBindingRef);
    validateOpaquePresentationIdentity(binding.presentationMessageId, OPAQUE_PRESENTATION_IDENTITY.messageId);
    if (!validateSchema(binding)) fail("agui_message_binding_schema_invalid", validateSchema.errors?.[0]?.instancePath ?? "");
    validatePublicSourceEventId(binding.openedBySourceEventId);
    if (binding.endedBySourceEventId !== null) validatePublicSourceEventId(binding.endedBySourceEventId);
    if (binding.sessionId !== snapshot.sessionId || binding.profileRevision !== snapshot.profileRevision) fail("agui_message_binding_scope_conflict", binding.bindingRef);
    if (refs.has(binding.bindingRef) || ids.has(binding.presentationMessageId)) fail("agui_message_binding_duplicate");
    const run = runRefs.get(binding.presentationRunBindingRef);
    if (run === undefined || run.sessionId !== binding.sessionId || run.segmentOrdinal !== binding.resumeSegmentOrdinal) fail("agui_message_run_binding_invalid", binding.bindingRef);
    const materialized = binding.sessionMessageId !== null;
    if (materialized !== (binding.sessionTextPartId !== null)) fail("agui_session_message_binding_partial", binding.bindingRef);
    if (materialized !== (run.sessionRunId !== null)) fail("agui_session_message_run_binding_conflict", binding.bindingRef);
    if (binding.sessionMessageId !== null) {
      if (sessionMessageIds.has(binding.sessionMessageId)) fail("agui_session_message_binding_duplicate", binding.sessionMessageId);
      sessionMessageIds.add(binding.sessionMessageId);
    }
    if (binding.sessionTextPartId !== null) {
      if (sessionTextPartIds.has(binding.sessionTextPartId)) fail("agui_session_text_part_binding_duplicate", binding.sessionTextPartId);
      sessionTextPartIds.add(binding.sessionTextPartId);
    }
    registerGlobalIdentity(identities.messageBindingRefs, binding.bindingRef, "agui_global_message_binding_ref_duplicate");
    registerGlobalIdentity(identities.presentationMessageIds, binding.presentationMessageId, "agui_global_presentation_message_id_duplicate");
    if (Date.parse(binding.openedAt) > Date.parse(binding.endedAt ?? binding.openedAt)) fail("agui_message_binding_time_invalid", binding.bindingRef);
    refs.set(binding.bindingRef, binding);
    ids.add(binding.presentationMessageId);
  }
  return refs;
}

function ownerIdentityForEvent(event) {
  if (event.type === EventType.ACTIVITY_SNAPSHOT) {
    const content = event.content;
    const identities = {
      "kokoro.safe-summary.v1": () => ({ kind: "safe-summary", partRef: content.partRef }),
      "kokoro.tool-preview.v1": () => ({ kind: "tool", toolCallRef: content.toolCallRef }),
      "kokoro.hitl.v1": () => ({
        kind: "hitl", ownerRef: content.ownerRef, decisionGroupRef: content.decisionGroupRef,
        controlRef: content.controlRef,
      }),
      "kokoro.plan.v1": () => ({ kind: "plan", planRef: content.planRef }),
      "kokoro.subagent.v1": () => ({ kind: "subagent", subagentRef: content.subagentRef }),
      "kokoro.media.v1": () => ({
        kind: "media", mediaOperationRef: content.mediaOperationRef, definitionRef: content.definitionRef,
        definitionRevisionRef: content.definitionRevisionRef,
        modelOptionRevisionRef: content.modelOptionRevisionRef ?? null,
      }),
      "kokoro.artifact.v1": () => ({
        kind: "artifact", artifactRef: content.artifactRef, artifactVersionRef: content.artifactVersionRef,
      }),
      "kokoro.cost.v1": () => ({
        kind: "cost", mediaOperationRef: content.mediaOperationRef, costProjectionRef: content.costProjectionRef,
      }),
      "kokoro.notice.v1": () => ({ kind: "notice", noticeRef: content.noticeRef }),
      "kokoro.error.v1": () => ({ kind: "error", errorRef: content.errorRef }),
    };
    const createIdentity = identities[event.activityType];
    if (createIdentity === undefined) fail("agui_owner_identity_unknown", event.activityType);
    return createIdentity();
  }
  if (event.type === EventType.CUSTOM && event.name === "kokoro.control.replace.v1") {
    return {
      kind: "control", controlRef: event.value.controlRef, ownerRef: event.value.ownerRef,
      decisionGroupRef: event.value.decisionGroupRef,
    };
  }
  if (event.type === EventType.CUSTOM && event.name === "kokoro.receipt.replace.v1") {
    return {
      kind: "receipt", receiptRef: event.value.receiptRef, controlRef: event.value.controlRef,
      ownerRef: event.value.ownerRef, decisionGroupRef: event.value.decisionGroupRef,
    };
  }
  return undefined;
}

function ownerVersionForEvent(event) {
  const value = event.type === EventType.ACTIVITY_SNAPSHOT ? event.content.ownerVersion : event.value.ownerVersion;
  const parsed = uint64(value, "agui_owner_version_invalid");
  if (parsed === 0n) fail("agui_owner_version_invalid");
  return parsed;
}

function ownerUpdatedAtForEvent(event) {
  return event.type === EventType.ACTIVITY_SNAPSHOT ? event.content.updatedAt : event.value.updatedAt;
}

function ownerStateFingerprint(event) {
  const state = structuredClone(event);
  delete state.timestamp;
  return canonical(state);
}

function ownerTerminalState(event) {
  if (event.type === EventType.CUSTOM && event.name === "kokoro.control.replace.v1") {
    return event.value.state === "pending" ? undefined : event.value.state;
  }
  if (event.type === EventType.CUSTOM && event.name === "kokoro.receipt.replace.v1") {
    return ["committed", "rejected"].includes(event.value.state) ? event.value.state : undefined;
  }
  if (event.type !== EventType.ACTIVITY_SNAPSHOT) return undefined;
  const content = event.content;
  switch (event.activityType) {
    case "kokoro.safe-summary.v1": return content.status === "streaming" ? undefined : content.status;
    case "kokoro.tool-preview.v1": return ["completed", "failed", "canceled"].includes(content.status) ? content.status : undefined;
    case "kokoro.hitl.v1": return content.status === "pending" ? undefined : content.status;
    case "kokoro.plan.v1": return ["completed", "failed", "canceled"].includes(content.status) ? content.status : undefined;
    case "kokoro.subagent.v1": return ["completed", "failed", "canceled"].includes(content.status) ? content.status : undefined;
    case "kokoro.media.v1": return ["completed", "partial", "failed", "canceled"].includes(content.state) ? content.state : undefined;
    case "kokoro.artifact.v1": return content.availability === "deleted" ? "deleted" : undefined;
    case "kokoro.notice.v1":
    case "kokoro.error.v1": return "terminal";
    case "kokoro.cost.v1": return undefined;
    default: fail("agui_owner_identity_unknown", event.activityType);
  }
}

function validateNestedOwnerTransition(current, next) {
  if (
    current.event.type === EventType.ACTIVITY_SNAPSHOT &&
    next.event.type === EventType.ACTIVITY_SNAPSHOT &&
    current.event.activityType === "kokoro.media.v1" && next.event.activityType === "kokoro.media.v1"
  ) {
    const currentCandidates = current.event.content.candidates;
    const nextCandidates = next.event.content.candidates;
    if (currentCandidates.length > nextCandidates.length) fail("agui_media_candidate_identity_conflict");
    for (let index = 0; index < currentCandidates.length; index += 1) {
      const candidate = currentCandidates[index];
      const updated = nextCandidates[index];
      if (
        updated === undefined || updated.candidateRef !== candidate.candidateRef || updated.ordinal !== candidate.ordinal
      ) fail("agui_media_candidate_identity_conflict");
      const currentVersion = uint64(candidate.ownerVersion, "agui_media_candidate_version_invalid");
      const nextVersion = uint64(updated.ownerVersion, "agui_media_candidate_version_invalid");
      if (nextVersion < currentVersion) fail("agui_media_candidate_version_regression", candidate.candidateRef);
      if (nextVersion === currentVersion && canonical(candidate) !== canonical(updated)) {
        fail("agui_media_candidate_version_conflict", candidate.candidateRef);
      }
      if (
        ["ready", "restricted", "failed", "canceled"].includes(candidate.state) &&
        updated.state !== candidate.state
      ) fail("agui_media_candidate_terminal_regression", candidate.candidateRef);
    }
  }
  if (
    current.event.type === EventType.ACTIVITY_SNAPSHOT &&
    next.event.type === EventType.ACTIVITY_SNAPSHOT &&
    current.event.activityType === "kokoro.cost.v1" && next.event.activityType === "kokoro.cost.v1" &&
    next.event.content.state === "corrected" &&
    next.event.content.correctsOwnerVersion !== current.event.content.ownerVersion
  ) fail("agui_cost_correction_ancestry_conflict");
}

function reduceOwnerProjectionRow(current, next) {
  ownerVersionForEvent(next.event);
  parseCanonicalUtcMs(ownerUpdatedAtForEvent(next.event), "agui_owner_updated_at_invalid");
  if (current === undefined) return structuredClone(next);
  if (
    current.presentationOwnerBindingRef !== next.presentationOwnerBindingRef ||
    canonical(ownerIdentityForEvent(current.event)) !== canonical(ownerIdentityForEvent(next.event))
  ) fail("agui_owner_projection_identity_conflict", next.presentationOwnerBindingRef);
  const currentVersion = ownerVersionForEvent(current.event);
  const nextVersion = ownerVersionForEvent(next.event);
  if (nextVersion < currentVersion) fail("agui_owner_version_regression", next.presentationOwnerBindingRef);
  if (nextVersion === currentVersion && ownerStateFingerprint(current.event) !== ownerStateFingerprint(next.event)) {
    fail("agui_owner_version_conflict", next.presentationOwnerBindingRef);
  }
  if (
    Date.parse(ownerUpdatedAtForEvent(next.event)) < Date.parse(ownerUpdatedAtForEvent(current.event))
  ) fail("agui_owner_updated_at_regression", next.presentationOwnerBindingRef);
  validateNestedOwnerTransition(current, next);
  const terminal = ownerTerminalState(current.event);
  if (terminal !== undefined && ownerTerminalState(next.event) !== terminal) {
    fail("agui_owner_terminal_regression", next.presentationOwnerBindingRef);
  }
  return structuredClone(next);
}

function validateOwnerBindings(bindings, contracts, runRefs, messageRefs, snapshot, identities) {
  if (!Array.isArray(bindings) || bindings.length > 2048) fail("agui_owner_bindings_invalid");
  const refs = new Map();
  const identityKeys = new Set();
  const perMessage = new Map();
  const controlReceiptPerRun = new Map();
  for (const binding of bindings) {
    validateOpaquePresentationIdentity(binding.bindingRef, OPAQUE_PRESENTATION_IDENTITY.ownerBindingRef);
    if (!contracts.validateOwnerBinding(binding)) {
      fail("agui_owner_binding_schema_invalid", contracts.validateOwnerBinding.errors?.[0]?.instancePath ?? "");
    }
    validatePublicSourceEventId(binding.boundBySourceEventId);
    parseCanonicalUtcMs(binding.boundAt, "agui_snapshot_binding_time_invalid");
    if (binding.sessionId !== snapshot.sessionId || binding.profileRevision !== snapshot.profileRevision) {
      fail("agui_owner_binding_scope_conflict", binding.bindingRef);
    }
    const run = runRefs.get(binding.presentationRunBindingRef);
    if (run === undefined) fail("agui_owner_run_binding_invalid", binding.bindingRef);
    if (binding.presentationMessageBindingRef !== null) {
      const message = messageRefs.get(binding.presentationMessageBindingRef);
      if (message === undefined || message.presentationRunBindingRef !== binding.presentationRunBindingRef) {
        fail("agui_owner_message_binding_invalid", binding.bindingRef);
      }
      perMessage.set(binding.presentationMessageBindingRef, (perMessage.get(binding.presentationMessageBindingRef) ?? 0) + 1);
      if (perMessage.get(binding.presentationMessageBindingRef) > 64) fail("agui_owner_bindings_per_message_exceeded");
    }
    if (binding.presentationOwnerMessageId !== null) {
      validateOpaquePresentationIdentity(binding.presentationOwnerMessageId, OPAQUE_PRESENTATION_IDENTITY.ownerMessageId);
      if (identities.presentationMessageIds.has(binding.presentationOwnerMessageId)) {
        fail("agui_presentation_owner_text_message_id_collision", binding.presentationOwnerMessageId);
      }
      registerGlobalIdentity(
        identities.presentationOwnerMessageIds,
        binding.presentationOwnerMessageId,
        "agui_global_presentation_owner_message_id_duplicate",
      );
    }
    const identityKey = canonical(binding.ownerIdentity);
    if (refs.has(binding.bindingRef) || identityKeys.has(identityKey)) fail("agui_owner_binding_duplicate");
    identityKeys.add(identityKey);
    refs.set(binding.bindingRef, binding);
    registerGlobalIdentity(identities.ownerBindingRefs, binding.bindingRef, "agui_global_owner_binding_ref_duplicate");
    if (["control", "receipt"].includes(binding.ownerIdentity.kind)) {
      const count = (controlReceiptPerRun.get(binding.presentationRunBindingRef) ?? 0) + 1;
      controlReceiptPerRun.set(binding.presentationRunBindingRef, count);
      if (count > 256) fail("agui_control_receipt_bindings_per_run_exceeded");
    }
  }
  for (const binding of refs.values()) {
    if (binding.ownerIdentity.kind === "control" || binding.ownerIdentity.kind === "receipt") {
      const target = refs.get(binding.targetOwnerBindingRef);
      if (
        target?.ownerIdentity.kind !== "hitl" ||
        target.presentationRunBindingRef !== binding.presentationRunBindingRef ||
        target.ownerIdentity.ownerRef !== binding.ownerIdentity.ownerRef ||
        target.ownerIdentity.decisionGroupRef !== binding.ownerIdentity.decisionGroupRef ||
        target.ownerIdentity.controlRef !== binding.ownerIdentity.controlRef
      ) fail("agui_owner_target_binding_invalid", binding.bindingRef);
    }
    if (binding.ownerIdentity.kind === "receipt") {
      const control = refs.get(binding.controlOwnerBindingRef);
      if (
        control?.ownerIdentity.kind !== "control" ||
        control.presentationRunBindingRef !== binding.presentationRunBindingRef ||
        control.ownerIdentity.controlRef !== binding.ownerIdentity.controlRef ||
        control.targetOwnerBindingRef !== binding.targetOwnerBindingRef
      ) fail("agui_owner_control_binding_invalid", binding.bindingRef);
    }
  }
  return refs;
}

function validateOwnerProjectionRows(rows, contracts, ownerRefs, snapshot) {
  if (!Array.isArray(rows) || rows.length !== ownerRefs.size || rows.length > 2048) {
    fail("agui_owner_projection_rows_invalid");
  }
  if (Buffer.byteLength(canonical(rows), "utf8") > 16_777_216) fail("agui_owner_projection_rows_size_exceeded");
  const refs = new Map();
  const watermark = snapshot.lastRecordedAt === null ? Number.NEGATIVE_INFINITY : Date.parse(snapshot.lastRecordedAt);
  for (const row of rows) {
    if (!contracts.validateOwnerProjectionRow(row)) {
      fail("agui_owner_projection_row_schema_invalid", contracts.validateOwnerProjectionRow.errors?.[0]?.instancePath ?? "");
    }
    const binding = ownerRefs.get(row.presentationOwnerBindingRef);
    if (binding === undefined || refs.has(row.presentationOwnerBindingRef)) fail("agui_owner_projection_binding_invalid");
    validatePublicSourceEventId(row.sourceEventId);
    const recordedAt = parseCanonicalUtcMs(row.recordedAt, "agui_owner_projection_time_invalid");
    if (recordedAt > watermark || recordedAt < Date.parse(binding.boundAt)) fail("agui_owner_projection_time_invalid");
    ownerVersionForEvent(row.event);
    validateOwnerPresentationEvent(row.event);
    if (canonical(ownerIdentityForEvent(row.event)) !== canonical(binding.ownerIdentity)) {
      fail("agui_owner_projection_identity_conflict", binding.bindingRef);
    }
    if (
      row.event.type === EventType.ACTIVITY_SNAPSHOT &&
      row.event.messageId !== binding.presentationOwnerMessageId
    ) fail("agui_owner_projection_message_conflict", binding.bindingRef);
    refs.set(
      row.presentationOwnerBindingRef,
      reduceOwnerProjectionRow(refs.get(row.presentationOwnerBindingRef), row),
    );
  }
  return refs;
}

function validatePrivateRouteId(value, code) {
  if (typeof value !== "string" || value.length > 128 || !/^[A-Za-z0-9][A-Za-z0-9._:-]*$/u.test(value)) {
    fail(code);
  }
}

function validatePrivateRefSeparation(privateRef, publicRefs) {
  for (const publicRef of publicRefs) {
    if (privateRef === publicRef) fail("agui_private_presentation_identity_equal", privateRef);
    if (publicRef.includes(privateRef)) fail("agui_private_presentation_identity_leak", privateRef);
  }
}

function publicMessageRefsForEvent(event) {
  if ([EventType.TEXT_MESSAGE_START, EventType.TEXT_MESSAGE_CONTENT, EventType.TEXT_MESSAGE_END, EventType.ACTIVITY_SNAPSHOT].includes(event.type)) {
    return [event.messageId];
  }
  if (event.type !== EventType.CUSTOM) return [];
  if (event.name === "kokoro.branch.replace.v1") {
    return [event.value.rootMessageId, event.value.leafMessageId].filter((value) => value !== null);
  }
  if (event.name === "kokoro.message.replace.v1") {
    return [event.value.presentationMessageId, event.value.parentPresentationMessageId].filter((value) => value !== null);
  }
  return [];
}

function validateEventPublicMessageIdentities(event, privateMessageRefs) {
  for (const publicRef of publicMessageRefsForEvent(event)) {
    for (const privateRef of privateMessageRefs) {
      if (publicRef === privateRef) fail("agui_private_presentation_identity_equal", privateRef);
      if (typeof publicRef === "string" && publicRef.includes(privateRef)) {
        fail("agui_private_presentation_identity_leak", privateRef);
      }
    }
    validateOpaquePresentationIdentity(
      publicRef,
      event.type === EventType.ACTIVITY_SNAPSHOT
        ? OPAQUE_PRESENTATION_IDENTITY.ownerMessageId
        : OPAQUE_PRESENTATION_IDENTITY.messageId,
    );
  }
}

function validateSessionPrivateRouteFixtures(contractCase, runRefs, messageRefs, identities) {
  const fixtures = contractCase.sessionPrivateRouteFixtures;
  exactKeys(fixtures, ["runs", "messages", "provenance"], "agui_private_route_fixture_shape_invalid");
  if (
    !Array.isArray(fixtures.runs) || fixtures.runs.length !== runRefs.size ||
    !Array.isArray(fixtures.messages) || fixtures.messages.length !== messageRefs.size
  ) fail("agui_private_route_fixture_coverage_invalid", contractCase.id);
  const runRoutes = new Map();
  for (const route of fixtures.runs) {
    exactKeys(
      route,
      ["presentationRunBindingRef", "internalRunRef", "parentInternalRunRef"],
      "agui_private_run_route_shape_invalid",
    );
    validatePrivateRouteId(route.internalRunRef, "agui_private_run_route_shape_invalid");
    if (route.parentInternalRunRef !== null) {
      validatePrivateRouteId(route.parentInternalRunRef, "agui_private_run_route_shape_invalid");
    }
    const binding = runRefs.get(route.presentationRunBindingRef);
    if (binding !== undefined) {
      const publicRefs = [binding.bindingRef, binding.presentationThreadId, binding.presentationRunId, binding.sessionRunId]
        .filter((value) => value !== null);
      validatePrivateRefSeparation(route.internalRunRef, publicRefs);
      if (route.parentInternalRunRef !== null) validatePrivateRefSeparation(route.parentInternalRunRef, publicRefs);
    }
    if (!runRefs.has(route.presentationRunBindingRef) || runRoutes.has(route.presentationRunBindingRef)) {
      fail("agui_private_route_fixture_coverage_invalid", route.presentationRunBindingRef);
    }
    runRoutes.set(route.presentationRunBindingRef, route);
  }
  for (const [bindingRef, binding] of runRefs) {
    const route = runRoutes.get(bindingRef);
    const parentPresentationId = binding.parentLineage.parentPresentationRunId;
    if ((route.parentInternalRunRef === null) !== (parentPresentationId === null)) {
      fail("agui_private_parent_route_conflict", bindingRef);
    }
    if (parentPresentationId !== null) {
      const parent = [...runRefs.values()].find(
        ({ presentationRunId }) => presentationRunId === parentPresentationId,
      );
      const parentRoute = parent === undefined ? undefined : runRoutes.get(parent.bindingRef);
      if (parentRoute === undefined || parentRoute.internalRunRef !== route.parentInternalRunRef) {
        fail("agui_private_parent_route_conflict", bindingRef);
      }
    }
    if (binding.segmentOrdinal > 0) {
      const previous = [...runRefs.values()].find(
        ({ presentationRunId }) => presentationRunId === binding.resumeOfPresentationRunId,
      );
      const previousRoute = previous === undefined ? undefined : runRoutes.get(previous.bindingRef);
      if (previousRoute === undefined || previousRoute.internalRunRef !== route.internalRunRef) {
        fail("agui_private_resume_route_conflict", bindingRef);
      }
    }
    registerGlobalIdentity(
      identities.internalRunSegments,
      canonical([binding.sessionId, route.internalRunRef, binding.segmentOrdinal]),
      "agui_global_internal_run_segment_duplicate",
    );
  }
  const messageRoutes = new Map();
  for (const route of fixtures.messages) {
    exactKeys(
      route,
      ["presentationMessageBindingRef", "internalMessageRef"],
      "agui_private_message_route_shape_invalid",
    );
    validatePrivateRouteId(route.internalMessageRef, "agui_private_message_route_shape_invalid");
    const binding = messageRefs.get(route.presentationMessageBindingRef);
    if (binding !== undefined) {
      validatePrivateRefSeparation(
        route.internalMessageRef,
        [binding.bindingRef, binding.presentationRunBindingRef, binding.presentationMessageId, binding.sessionMessageId, binding.sessionTextPartId]
          .filter((value) => value !== null),
      );
    }
    if (!messageRefs.has(route.presentationMessageBindingRef) || messageRoutes.has(route.presentationMessageBindingRef)) {
      fail("agui_private_route_fixture_coverage_invalid", route.presentationMessageBindingRef);
    }
    messageRoutes.set(route.presentationMessageBindingRef, route);
  }
  for (const [bindingRef, binding] of messageRefs) {
    const route = messageRoutes.get(bindingRef);
    registerGlobalIdentity(
      identities.internalMessageSegments,
      canonical([binding.sessionId, route.internalMessageRef, binding.resumeSegmentOrdinal]),
      "agui_global_internal_message_segment_duplicate",
    );
  }
  if (!Array.isArray(fixtures.provenance)) fail("agui_private_provenance_coverage_invalid", contractCase.id);
  const publicSourceEventIds = new Set(contractCase.frames.map(({ data }) => data.source.sourceEventId));
  const agentSourceEventRefs = new Set();
  const mappedPublicSourceEventIds = new Set();
  for (const provenance of fixtures.provenance) {
    exactKeys(
      provenance,
      ["sessionId", "agentSourceEventRef", "publicSourceEventId"],
      "agui_private_provenance_shape_invalid",
    );
    validatePrivateRouteId(provenance.agentSourceEventRef, "agui_private_provenance_shape_invalid");
    if (provenance.agentSourceEventRef === provenance.publicSourceEventId) {
      fail("agui_private_provenance_identity_equal", provenance.agentSourceEventRef);
    }
    if (provenance.publicSourceEventId.includes(provenance.agentSourceEventRef)) {
      fail("agui_private_provenance_identity_leak", provenance.agentSourceEventRef);
    }
    if (provenance.sessionId !== contractCase.snapshot.sessionId) {
      fail("agui_private_provenance_scope_conflict", provenance.agentSourceEventRef);
    }
    validatePublicSourceEventId(provenance.publicSourceEventId);
    if (
      agentSourceEventRefs.has(provenance.agentSourceEventRef) ||
      mappedPublicSourceEventIds.has(provenance.publicSourceEventId)
    ) fail("agui_private_provenance_duplicate", provenance.agentSourceEventRef);
    if (!publicSourceEventIds.has(provenance.publicSourceEventId)) {
      fail("agui_private_provenance_coverage_invalid", provenance.publicSourceEventId);
    }
    agentSourceEventRefs.add(provenance.agentSourceEventRef);
    mappedPublicSourceEventIds.add(provenance.publicSourceEventId);
  }
  return { runRoutes, messageRoutes, provenance: fixtures.provenance };
}

function browserInternalKey(value) {
  if (Array.isArray(value)) return value.some(browserInternalKey);
  if (value === null || typeof value !== "object") return false;
  return Object.entries(value).some(
    ([key, child]) => /^(?:internal|parentInternal)/u.test(key) || browserInternalKey(child),
  );
}

function mappingFor(mapping, sourceKind) {
  return mapping.mappings.find((entry) => entry.sourceKind === sourceKind);
}

function assertBindingDeltaTime(actual, expected) {
  parseCanonicalUtcMs(actual, "agui_binding_delta_time_conflict");
  if (actual !== expected) fail("agui_binding_delta_time_conflict");
}

function assertRunDeltaScope(binding, frame) {
  if (
    binding.bindingRef !== frame.data.presentationRunBindingRef ||
    frame.data.presentationMessageBindingRef !== undefined
  ) fail("agui_binding_delta_ref_conflict", frame.data.source.sourceEventId);
  if (
    binding.sessionId !== frame.data.source.sessionId ||
    binding.profileRevision !== frame.data.profileRevision
  ) fail("agui_binding_delta_scope_conflict", binding.bindingRef);
}

function assertMessageDeltaScope(binding, frame) {
  if (
    binding.bindingRef !== frame.data.presentationMessageBindingRef ||
    binding.presentationRunBindingRef !== frame.data.presentationRunBindingRef
  ) fail("agui_binding_delta_ref_conflict", frame.data.source.sourceEventId);
  if (
    binding.sessionId !== frame.data.source.sessionId ||
    binding.profileRevision !== frame.data.profileRevision
  ) fail("agui_binding_delta_scope_conflict", binding.bindingRef);
}

function assertRunStartDelta(frame, binding, runRefs) {
  const { event, source } = frame.data;
  assertRunDeltaScope(binding, frame);
  const existing = runRefs.get(binding.bindingRef);
  if (existing !== undefined) {
    if (existing.state !== "open") fail("agui_terminal_run_revived", binding.presentationRunId);
    fail("agui_binding_delta_run_duplicate", binding.bindingRef);
  }
  assertBindingDeltaTime(binding.openedAt, source.recordedAt);
  if (
    (binding.terminalSourceEventId !== null && binding.terminalSourceEventId !== source.sourceEventId) ||
    (binding.terminalAt !== null && parseCanonicalUtcMs(binding.terminalAt, "agui_binding_delta_time_conflict") > Date.parse(source.recordedAt))
  ) fail("agui_binding_delta_future_evidence", binding.bindingRef);
  if (binding.openedBySourceEventId !== source.sourceEventId) fail("agui_binding_delta_source_conflict", binding.bindingRef);
  if (
    binding.state !== "open" || binding.terminalDisposition !== null ||
    binding.terminalSourceEventId !== null || binding.terminalAt !== null
  ) fail("agui_binding_delta_state_conflict", binding.bindingRef);
  if (
    event.runId !== binding.presentationRunId || event.threadId !== binding.presentationThreadId ||
    (event.parentRunId ?? null) !== binding.parentLineage.parentPresentationRunId
  ) fail("agui_binding_delta_event_identity_conflict", binding.bindingRef);
  if (binding.parentLineage.parentPresentationRunId !== null) {
    const parent = [...runRefs.values()].find(
      ({ presentationRunId }) => presentationRunId === binding.parentLineage.parentPresentationRunId,
    );
    if (parent === undefined || parent.state === "open") fail("agui_binding_delta_future_evidence", binding.bindingRef);
  }
  if (binding.segmentOrdinal > 0) {
    const previous = [...runRefs.values()].find(
      ({ presentationRunId }) => presentationRunId === binding.resumeOfPresentationRunId,
    );
    if (
      previous === undefined || previous.state === "open" ||
      previous.segmentOrdinal !== binding.segmentOrdinal - 1
    ) fail("agui_binding_delta_future_evidence", binding.bindingRef);
  }
  runRefs.set(binding.bindingRef, structuredClone(binding));
}

function assertRunTerminalDelta(frame, binding, runRefs) {
  const { event, source } = frame.data;
  assertRunDeltaScope(binding, frame);
  const existing = runRefs.get(binding.bindingRef);
  if (existing === undefined || existing.state !== "open") {
    fail("agui_binding_delta_terminal_without_open", binding.bindingRef);
  }
  if (binding.terminalSourceEventId !== source.sourceEventId) fail("agui_binding_delta_source_conflict", binding.bindingRef);
  assertBindingDeltaTime(binding.terminalAt, source.recordedAt);
  const state = event.type === EventType.RUN_FINISHED ? "finished" : "error";
  const disposition = event.type === EventType.RUN_FINISHED ? "success" : "error";
  if (binding.state !== state || binding.terminalDisposition !== disposition) {
    fail("agui_binding_delta_state_conflict", binding.bindingRef);
  }
  const expected = {
    ...existing,
    state,
    terminalDisposition: disposition,
    terminalSourceEventId: source.sourceEventId,
    terminalAt: source.recordedAt,
  };
  if (canonical(binding) !== canonical(expected)) fail("agui_binding_delta_replacement_conflict", binding.bindingRef);
  if (
    event.type === EventType.RUN_FINISHED &&
    (event.runId !== binding.presentationRunId || event.threadId !== binding.presentationThreadId)
  ) fail("agui_binding_delta_event_identity_conflict", binding.bindingRef);
  runRefs.set(binding.bindingRef, structuredClone(binding));
}

function assertMessageStartDelta(frame, binding, runRefs, messageRefs) {
  const { event, source } = frame.data;
  assertMessageDeltaScope(binding, frame);
  const run = runRefs.get(binding.presentationRunBindingRef);
  if (run === undefined || run.state !== "open" || run.segmentOrdinal !== binding.resumeSegmentOrdinal) {
    fail("agui_binding_delta_future_evidence", binding.bindingRef);
  }
  const existing = messageRefs.get(binding.bindingRef);
  if (existing !== undefined) {
    if (existing.state === "ended") fail("agui_message_reopened", binding.presentationMessageId);
    fail("agui_binding_delta_message_duplicate", binding.bindingRef);
  }
  assertBindingDeltaTime(binding.openedAt, source.recordedAt);
  if (
    (binding.endedBySourceEventId !== null && binding.endedBySourceEventId !== source.sourceEventId) ||
    (binding.endedAt !== null && parseCanonicalUtcMs(binding.endedAt, "agui_binding_delta_time_conflict") > Date.parse(source.recordedAt))
  ) fail("agui_binding_delta_future_evidence", binding.bindingRef);
  if (binding.openedBySourceEventId !== source.sourceEventId) fail("agui_binding_delta_source_conflict", binding.bindingRef);
  if (binding.state !== "open" || binding.endedBySourceEventId !== null || binding.endedAt !== null) {
    fail("agui_binding_delta_state_conflict", binding.bindingRef);
  }
  if (event.messageId !== binding.presentationMessageId) {
    fail("agui_binding_delta_event_identity_conflict", binding.bindingRef);
  }
  messageRefs.set(binding.bindingRef, structuredClone(binding));
}

function assertMessageEndDelta(frame, binding, messageRefs) {
  const { event, source } = frame.data;
  assertMessageDeltaScope(binding, frame);
  const existing = messageRefs.get(binding.bindingRef);
  if (existing === undefined || existing.state !== "open") {
    fail("agui_binding_delta_message_end_without_open", binding.bindingRef);
  }
  if (binding.endedBySourceEventId !== source.sourceEventId) fail("agui_binding_delta_source_conflict", binding.bindingRef);
  assertBindingDeltaTime(binding.endedAt, source.recordedAt);
  if (binding.state !== "ended") fail("agui_binding_delta_state_conflict", binding.bindingRef);
  const expected = {
    ...existing,
    state: "ended",
    endedBySourceEventId: source.sourceEventId,
    endedAt: source.recordedAt,
  };
  if (canonical(binding) !== canonical(expected)) fail("agui_binding_delta_replacement_conflict", binding.bindingRef);
  if (event.messageId !== binding.presentationMessageId) {
    fail("agui_binding_delta_event_identity_conflict", binding.bindingRef);
  }
  messageRefs.set(binding.bindingRef, structuredClone(binding));
}

function assertOwnerReplaceDelta(frame, binding, authority, contracts) {
  const { event, source } = frame.data;
  if (!contracts.validateOwnerBinding(binding)) {
    fail("agui_owner_binding_schema_invalid", contracts.validateOwnerBinding.errors?.[0]?.instancePath ?? "");
  }
  if (
    binding.bindingRef !== frame.data.presentationOwnerBindingRef ||
    binding.presentationRunBindingRef !== frame.data.presentationRunBindingRef ||
    binding.sessionId !== source.sessionId || binding.profileRevision !== frame.data.profileRevision
  ) fail("agui_owner_binding_scope_conflict", binding.bindingRef);
  const run = authority.runRefs.get(binding.presentationRunBindingRef);
  if (run === undefined) fail("agui_owner_run_binding_invalid", binding.bindingRef);
  if (binding.presentationMessageBindingRef !== null) {
    const message = authority.messageRefs.get(binding.presentationMessageBindingRef);
    if (message === undefined || message.presentationRunBindingRef !== binding.presentationRunBindingRef) {
      fail("agui_owner_message_binding_invalid", binding.bindingRef);
    }
  }
  const eventIdentity = ownerIdentityForEvent(event);
  if (eventIdentity === undefined || canonical(eventIdentity) !== canonical(binding.ownerIdentity)) {
    fail("agui_owner_projection_identity_conflict", binding.bindingRef);
  }
  if (event.type === EventType.ACTIVITY_SNAPSHOT) {
    if (
      event.messageId !== binding.presentationOwnerMessageId ||
      (frame.data.presentationMessageBindingRef ?? null) !== binding.presentationMessageBindingRef
    ) fail("agui_owner_projection_message_conflict", binding.bindingRef);
  } else if (frame.data.presentationMessageBindingRef !== undefined) {
    fail("agui_owner_message_binding_invalid", binding.bindingRef);
  }
  const existing = authority.ownerRefs.get(binding.bindingRef);
  if (existing === undefined) {
    if (binding.boundBySourceEventId !== source.sourceEventId) fail("agui_binding_delta_source_conflict", binding.bindingRef);
    assertBindingDeltaTime(binding.boundAt, source.recordedAt);
  } else if (canonical(existing) !== canonical(binding)) {
    fail("agui_owner_binding_immutable_conflict", binding.bindingRef);
  }
  if (binding.targetOwnerBindingRef !== null) {
    const target = authority.ownerRefs.get(binding.targetOwnerBindingRef);
    if (
      target?.ownerIdentity.kind !== "hitl" ||
      target.presentationRunBindingRef !== binding.presentationRunBindingRef
    ) fail("agui_owner_target_binding_invalid", binding.bindingRef);
  }
  if (binding.controlOwnerBindingRef !== null) {
    const control = authority.ownerRefs.get(binding.controlOwnerBindingRef);
    if (
      control?.ownerIdentity.kind !== "control" ||
      control.presentationRunBindingRef !== binding.presentationRunBindingRef
    ) fail("agui_owner_control_binding_invalid", binding.bindingRef);
  }
  const ownerKind = binding.ownerIdentity.kind;
  if (run.state !== "open") {
    if (existing === undefined && ownerKind === "receipt") {
      if (authority.ownerRefs.get(binding.controlOwnerBindingRef)?.ownerIdentity.kind !== "control") {
        fail("agui_terminal_owner_create_forbidden", binding.bindingRef);
      }
    } else if (existing === undefined && !OWNER_TERMINAL_MAY_CREATE_SET.has(ownerKind)) {
      fail("agui_terminal_owner_create_forbidden", binding.bindingRef);
    }
    if (existing !== undefined && !OWNER_TERMINAL_MAY_CONVERGE_SET.has(ownerKind)) {
      fail("agui_terminal_owner_convergence_forbidden", binding.bindingRef);
    }
  }
  ownerVersionForEvent(event);
  authority.ownerRefs.set(binding.bindingRef, structuredClone(binding));
  const nextRow = {
    profileRevision: PROFILE_REVISION,
    schemaRevision: 1,
    presentationOwnerBindingRef: binding.bindingRef,
    sourceEventId: source.sourceEventId,
    projectionVersion: source.projectionVersion,
    recordedAt: source.recordedAt,
    event: structuredClone(event),
  };
  authority.ownerRows.set(
    binding.bindingRef,
    reduceOwnerProjectionRow(authority.ownerRows.get(binding.bindingRef), nextRow),
  );
}

function applyBindingAuthorityDelta(frame, mappingEntry, authority, contracts) {
  const delta = frame.data.bindingAuthorityDelta;
  if (!contracts.validateBindingAuthorityDelta(delta)) {
    fail(
      "agui_binding_delta_schema_invalid",
      contracts.validateBindingAuthorityDelta.errors?.[0]?.instancePath ?? "",
    );
  }
  if (delta.kind !== mappingEntry.bindingAuthorityDeltaKind) {
    fail("agui_binding_delta_kind_invalid", frame.data.source.sourceEventId);
  }
  if (delta.kind === "none") return;
  if (delta.kind === "run.replace") {
    if (!contracts.validateRunBinding(delta.binding)) fail("agui_run_binding_schema_invalid");
    if (frame.data.event.type === EventType.RUN_STARTED) {
      assertRunStartDelta(frame, delta.binding, authority.runRefs);
      return;
    }
    assertRunTerminalDelta(frame, delta.binding, authority.runRefs);
    return;
  }
  if (delta.kind === "owner.replace") {
    assertOwnerReplaceDelta(frame, delta.binding, authority, contracts);
    return;
  }
  if (!contracts.validateMessageBinding(delta.binding)) fail("agui_message_binding_schema_invalid");
  if (frame.data.event.type === EventType.TEXT_MESSAGE_START) {
    assertMessageStartDelta(frame, delta.binding, authority.runRefs, authority.messageRefs);
    return;
  }
  assertMessageEndDelta(frame, delta.binding, authority.messageRefs);
}

function validateRebuiltFinalSnapshot(caseInput, authority, contracts) {
  const lastFrame = caseInput.frames.at(-1);
  const rebuilt = {
    authority: "session-browser-v3-http-snapshot",
    hydrate: true,
    repair: true,
    profileRevision: PROFILE_REVISION,
    sessionId: caseInput.snapshot.sessionId,
    streamEpoch: caseInput.snapshot.streamEpoch,
    durableSeq: lastFrame.data.source.durableSeq,
    lastRecordedAt: lastFrame.data.source.recordedAt,
    cursor: lastFrame.id,
    runBindings: [...authority.runRefs.values()],
    messageBindings: [...authority.messageRefs.values()],
    ownerBindings: [...authority.ownerRefs.values()],
    ownerProjectionRows: [...authority.ownerRows.values()],
  };
  if (canonical(rebuilt) !== canonical(caseInput.expectedFinalSnapshot)) {
    fail("agui_binding_delta_snapshot_rebuild_mismatch", caseInput.id);
  }
  if (!contracts.validateSnapshotAuthoritySchema(rebuilt)) {
    fail("agui_snapshot_authority_schema_invalid", contracts.validateSnapshotAuthoritySchema.errors?.[0]?.instancePath ?? "");
  }
  validateSnapshotTimeAuthority(
    rebuilt,
    contracts.validateSnapshotAuthoritySchema,
    rebuilt.runBindings,
    rebuilt.messageBindings,
    rebuilt.ownerBindings,
    rebuilt.ownerProjectionRows,
  );
  validateSnapshotBindingAuthority(rebuilt, contracts);
}

function validateBindingForFrame(frame, runRefs, messageRefs, ownerRefs, snapshot) {
  const event = frame.data.event;
  const runRef = frame.data.presentationRunBindingRef;
  const messageRef = frame.data.presentationMessageBindingRef;
  const isOwnerEvent = event.type === EventType.ACTIVITY_SNAPSHOT ||
    (event.type === EventType.CUSTOM && OWNER_DELTA_CUSTOM_NAMES.has(event.name));
  if (!isOwnerEvent && frame.data.presentationOwnerBindingRef !== undefined) {
    fail("agui_frame_owner_binding_forbidden", frame.data.source.sourceEventId);
  }
  if (
    event.type === EventType.CUSTOM && OWNER_DELTA_CUSTOM_NAMES.has(event.name) && messageRef !== undefined
  ) fail("agui_frame_owner_message_binding_forbidden", frame.data.source.sourceEventId);
  if ([EventType.RUN_STARTED, EventType.RUN_FINISHED, EventType.RUN_ERROR].includes(event.type)) {
    if (!runRefs.has(runRef) || messageRef !== undefined) fail("agui_frame_run_binding_invalid", frame.data.source.sourceEventId);
  }
  if ([EventType.TEXT_MESSAGE_START, EventType.TEXT_MESSAGE_CONTENT, EventType.TEXT_MESSAGE_END].includes(event.type)) {
    const message = messageRefs.get(messageRef);
    const run = runRefs.get(runRef);
    if (message === undefined || run === undefined || message.presentationRunBindingRef !== runRef || message.presentationMessageId !== event.messageId) fail("agui_frame_message_binding_invalid", frame.data.source.sourceEventId);
  }
  if (event.type === EventType.ACTIVITY_SNAPSHOT) {
    const owner = ownerRefs.get(frame.data.presentationOwnerBindingRef);
    const run = runRefs.get(runRef);
    if (
      owner === undefined || run === undefined || owner.presentationRunBindingRef !== runRef ||
      owner.presentationOwnerMessageId !== event.messageId ||
      owner.presentationMessageBindingRef !== (messageRef ?? null)
    ) fail("agui_frame_owner_binding_invalid", frame.data.source.sourceEventId);
  }
  if (event.type === EventType.CUSTOM) {
    if (event.name === "kokoro.session.replace.v1" && (event.value.sessionId !== snapshot.sessionId || event.value.profileRevision !== snapshot.profileRevision)) fail("agui_custom_session_scope_conflict");
    if (event.name === "kokoro.message.replace.v1" && (!messageRefs.has(messageRef) || !runRefs.has(runRef))) fail("agui_frame_message_binding_invalid");
    if (["kokoro.run.replace.v1", "kokoro.control.replace.v1", "kokoro.receipt.replace.v1"].includes(event.name) && !runRefs.has(runRef)) fail("agui_frame_run_binding_invalid");
    if (["kokoro.control.replace.v1", "kokoro.receipt.replace.v1"].includes(event.name) && !ownerRefs.has(frame.data.presentationOwnerBindingRef)) {
      fail("agui_frame_owner_binding_invalid", frame.data.source.sourceEventId);
    }
  }
}

function validateStreamState(frames, runRefs, messageRefs) {
  const runState = new Map();
  const messageState = new Map();
  for (const frame of frames) {
    const event = frame.data.event;
    const sourceId = frame.data.source.sourceEventId;
    if ([EventType.TEXT_MESSAGE_START, EventType.TEXT_MESSAGE_CONTENT, EventType.TEXT_MESSAGE_END].includes(event.type)) {
      const state = messageState.get(event.messageId);
      const binding = messageRefs.get(frame.data.presentationMessageBindingRef);
      if (event.type === EventType.TEXT_MESSAGE_START) {
        if (state !== undefined) fail("agui_message_reopened", event.messageId);
        if (binding.openedBySourceEventId !== sourceId) fail("agui_message_open_source_conflict", event.messageId);
        messageState.set(event.messageId, "open");
      } else if (event.type === EventType.TEXT_MESSAGE_CONTENT) {
        if (state === "ended") fail("agui_message_reopened", event.messageId);
        if (state !== "open") fail("agui_message_not_open", event.messageId);
      } else {
        if (state !== "open") fail("agui_message_reopened", event.messageId);
        if (binding.endedBySourceEventId !== sourceId) fail("agui_message_end_source_conflict", event.messageId);
        messageState.set(event.messageId, "ended");
      }
      const run = runRefs.get(frame.data.presentationRunBindingRef);
      if (runState.get(run.presentationRunId) === "terminal") fail("agui_terminal_run_revived", run.presentationRunId);
      continue;
    }
    const referencedRun = runRefs.get(frame.data.presentationRunBindingRef);
    if (
      referencedRun !== undefined && runState.get(referencedRun.presentationRunId) === "terminal" &&
      ownerIdentityForEvent(event) === undefined
    ) fail("agui_terminal_run_revived", referencedRun.presentationRunId);
    if (event.type === EventType.RUN_STARTED) {
      const binding = runRefs.get(frame.data.presentationRunBindingRef);
      if (runState.has(binding.presentationRunId)) fail("agui_terminal_run_revived", binding.presentationRunId);
      if (binding.openedBySourceEventId !== sourceId || event.runId !== binding.presentationRunId || event.threadId !== binding.presentationThreadId) fail("agui_run_start_binding_conflict", binding.bindingRef);
      if ((event.parentRunId ?? null) !== binding.parentLineage.parentPresentationRunId) fail("agui_run_parent_lineage_conflict", binding.bindingRef);
      runState.set(binding.presentationRunId, "open");
      continue;
    }
    if ([EventType.RUN_FINISHED, EventType.RUN_ERROR].includes(event.type)) {
      const binding = runRefs.get(frame.data.presentationRunBindingRef);
      if (runState.get(binding.presentationRunId) !== "open") fail("agui_terminal_run_revived", binding.presentationRunId);
      if (binding.terminalSourceEventId !== sourceId || (event.type === EventType.RUN_FINISHED ? binding.state !== "finished" : binding.state !== "error")) fail("agui_run_terminal_binding_conflict", binding.bindingRef);
      if (event.type === EventType.RUN_FINISHED && (event.runId !== binding.presentationRunId || event.threadId !== binding.presentationThreadId)) fail("agui_run_terminal_binding_conflict", binding.bindingRef);
      runState.set(binding.presentationRunId, "terminal");
    }
  }
  for (const binding of runRefs.values()) {
    const observed = runState.get(binding.presentationRunId);
    if (binding.state === "open" ? observed !== "open" : observed !== "terminal") fail("agui_run_binding_state_unobserved", binding.bindingRef);
  }
  for (const binding of messageRefs.values()) {
    const observed = messageState.get(binding.presentationMessageId);
    if (binding.state === "open" ? observed !== "open" : observed !== "ended") fail("agui_message_binding_state_unobserved", binding.bindingRef);
  }
}

function validateConformanceCaseWithContracts(caseInput, contracts, identities) {
  const { mapping, validateEvent, validateProjectionPayload, validatePresentationRow, validateRunBinding, validateMessageBinding, validateStream, validateSnapshotAuthoritySchema } = contracts;
  if (!Array.isArray(caseInput.frames) || !Array.isArray(caseInput.durableRows) || caseInput.frames.length !== caseInput.durableRows.length || caseInput.frames.length === 0) fail("agui_durable_frame_cardinality_invalid");
  for (const frame of caseInput.frames) validatePublicSourceEventId(frame?.data?.source?.sourceEventId, frame?.data?.source);
  if (caseInput.request?.lastEventId !== caseInput.snapshot.cursor || caseInput.request?.queryCursor !== caseInput.snapshot.cursor || caseInput.request?.cursorProfile !== CURSOR_PROFILE_REVISION) fail("agui_resume_cursor_invalid");
  if (
    caseInput.grantBinding?.sessionId !== caseInput.snapshot.sessionId ||
    caseInput.grantBinding?.sessionContractRevision !== SESSION_CONTRACT_REVISION ||
    caseInput.grantBinding?.presentationProfileRevision !== PROFILE_REVISION ||
    caseInput.grantBinding?.cursorProfileRevision !== CURSOR_PROFILE_REVISION
  ) fail("agui_grant_profile_binding_invalid");
  const snapshotAuthority = {
    ...caseInput.snapshot,
    runBindings: caseInput.snapshot.durableSeq === "0" ? [] : caseInput.runBindings,
    messageBindings: caseInput.snapshot.durableSeq === "0" ? [] : caseInput.messageBindings,
    ownerBindings: caseInput.snapshot.durableSeq === "0" ? [] : caseInput.ownerBindings,
    ownerProjectionRows: caseInput.snapshot.durableSeq === "0" ? [] : caseInput.ownerProjectionRows,
  };

  const previousRecordedAtAuthority = validateSnapshotTimeAuthority(
    snapshotAuthority,
    validateSnapshotAuthoritySchema,
    snapshotAuthority.runBindings,
    snapshotAuthority.messageBindings,
    snapshotAuthority.ownerBindings,
    snapshotAuthority.ownerProjectionRows,
  );
  const snapshotClaims = decodeCursor(caseInput.snapshot.cursor, mapping.limits.maximumCursorBytes);
  assertCursorScope(snapshotClaims, {
    sessionId: caseInput.snapshot.sessionId,
    streamEpoch: caseInput.snapshot.streamEpoch,
    durableSeq: caseInput.snapshot.durableSeq,
    profileRevision: caseInput.snapshot.profileRevision,
    cursorProfileRevision: caseInput.grantBinding.cursorProfileRevision,
  });
  registerGlobalIdentity(identities.cursorIds, caseInput.snapshot.cursor, "agui_global_cursor_identity_duplicate");
  registerGlobalIdentity(identities.cursorClaims, cursorClaimIdentity(snapshotClaims), "agui_global_cursor_claim_identity_duplicate");

  const runRefs = validateRunBindings(caseInput.runBindings, validateRunBinding, caseInput.snapshot, identities);
  validateM0RunBindingStates(caseInput.runBindings, "agui_run_terminal_state_invalid");
  const messageRefs = validateMessageBindings(caseInput.messageBindings, validateMessageBinding, runRefs, caseInput.snapshot, identities);
  const ownerRefs = validateOwnerBindings(caseInput.ownerBindings, contracts, runRefs, messageRefs, caseInput.snapshot, identities);
  validateOwnerProjectionRows(caseInput.ownerProjectionRows, contracts, ownerRefs, caseInput.expectedFinalSnapshot);
  validateSessionPrivateRouteFixtures(caseInput, runRefs, messageRefs, identities);
  const privateMessageRefs = caseInput.sessionPrivateRouteFixtures.messages.map(({ internalMessageRef }) => internalMessageRef);
  if (browserInternalKey(caseInput.expectedFinalSnapshot)) fail("agui_browser_internal_route_forbidden", caseInput.id);
  if (!validateSnapshotAuthoritySchema(snapshotAuthority)) {
    fail("agui_snapshot_authority_schema_invalid", validateSnapshotAuthoritySchema.errors?.[0]?.instancePath ?? "");
  }
  const bindingAuthority = {
    runRefs: new Map(snapshotAuthority.runBindings.map((binding) => [binding.bindingRef, structuredClone(binding)])),
    messageRefs: new Map(snapshotAuthority.messageBindings.map((binding) => [binding.bindingRef, structuredClone(binding)])),
    ownerRefs: new Map(snapshotAuthority.ownerBindings.map((binding) => [binding.bindingRef, structuredClone(binding)])),
    ownerRows: new Map(snapshotAuthority.ownerProjectionRows.map((row) => [row.presentationOwnerBindingRef, structuredClone(row)])),
  };
  const sourceIds = new Set();
  const rowRefs = new Set();
  const localCursorIds = new Set([caseInput.snapshot.cursor]);
  let expectedSeq = uint64(caseInput.snapshot.durableSeq, "agui_snapshot_cursor_invalid") + 1n;
  uint64(caseInput.snapshot.streamEpoch, "agui_snapshot_cursor_invalid");
  let previousRecordedAt = previousRecordedAtAuthority;
  for (let index = 0; index < caseInput.frames.length; index += 1) {
    const frame = caseInput.frames[index];
    const event = frame?.data?.event;
    validateEventPreSchema(event, mapping);
    validateEventPublicMessageIdentities(event, privateMessageRefs);
    if (browserInternalKey(frame.data)) fail("agui_browser_internal_route_forbidden", frame.data.source?.sourceEventId ?? "unknown");
    if (frame.event !== event.type) fail("agui_sse_event_type_mismatch", String(frame.event));
    const source = frame.data.source;
    validatePublicSourceEventId(source.sourceEventId, source);
    if (uint64(source.durableSeq, "agui_cursor_gap") !== expectedSeq) fail("agui_cursor_gap", source.durableSeq);
    expectedSeq += 1n;
    uint64(source.streamEpoch, "agui_stream_epoch_invalid");
    if (uint64(source.projectionVersion, "agui_projection_version_invalid") === 0n) {
      fail("agui_projection_version_invalid", source.projectionVersion);
    }
    if (source.sessionId !== caseInput.snapshot.sessionId || source.streamEpoch !== caseInput.snapshot.streamEpoch || frame.data.profileRevision !== PROFILE_REVISION) fail("agui_stream_scope_conflict", source.sourceEventId);
    const recordedAt = Date.parse(source.recordedAt);
    if (!Number.isFinite(recordedAt) || recordedAt !== event.timestamp || recordedAt < previousRecordedAt) fail("agui_event_time_invalid", source.sourceEventId);
    previousRecordedAt = recordedAt;
    if (localCursorIds.has(frame.id) || sourceIds.has(source.sourceEventId)) fail("agui_stream_identity_duplicate", source.sourceEventId);
    const cursorClaims = decodeCursor(frame.id, mapping.limits.maximumCursorBytes);
    assertCursorScope(cursorClaims, {
      sessionId: source.sessionId,
      streamEpoch: source.streamEpoch,
      durableSeq: source.durableSeq,
      profileRevision: frame.data.profileRevision,
      cursorProfileRevision: caseInput.grantBinding.cursorProfileRevision,
    });
    registerGlobalIdentity(identities.cursorIds, frame.id, "agui_global_cursor_identity_duplicate");
    registerGlobalIdentity(identities.cursorClaims, cursorClaimIdentity(cursorClaims), "agui_global_cursor_claim_identity_duplicate");
    registerGlobalIdentity(
      identities.sourceEventIds,
      canonical([source.sessionId, source.sourceEventId]),
      "agui_global_source_event_id_duplicate",
    );
    localCursorIds.add(frame.id);
    sourceIds.add(source.sourceEventId);

    const row = caseInput.durableRows[index];
    if (!validatePresentationRow(row)) fail("agui_presentation_row_schema_invalid", validatePresentationRow.errors?.[0]?.instancePath ?? "");
    if (!validateProjectionPayload(frame.data)) fail("agui_projection_payload_schema_invalid", validateProjectionPayload.errors?.[0]?.instancePath ?? "");
    if (
      rowRefs.has(row.rowRef) || row.profileRevision !== frame.data.profileRevision || row.cursorProfileRevision !== caseInput.grantBinding.cursorProfileRevision ||
      canonical(row.source) !== canonical(source) || canonical(row.projectionPayload) !== canonical(frame.data) ||
      projectionDigest(row.projectionPayload) !== row.projectionPayloadDigest
    ) fail("agui_presentation_row_payload_mismatch", source.sourceEventId);
    registerGlobalIdentity(identities.rowRefs, row.rowRef, "agui_global_row_ref_duplicate");
    rowRefs.add(row.rowRef);

    const mappingEntry = mappingFor(mapping, source.sourceKind);
    if (mappingEntry === undefined || mappingEntry.eventType !== event.type) fail("agui_closed_mapping_missing", source.sourceKind);
    const discriminator = event.type === EventType.ACTIVITY_SNAPSHOT ? event.activityType : event.type === EventType.CUSTOM ? event.name : undefined;
    if ((mappingEntry.discriminator ?? undefined) !== discriminator) fail("agui_mapping_discriminator_conflict", source.sourceKind);
    applyBindingAuthorityDelta(frame, mappingEntry, bindingAuthority, contracts);
    enforceLimits(event, mapping.limits, mapping.limits.maximumEventBytes, "agui_event_limit_exceeded");
    enforceLimits(frame, mapping.limits, mapping.limits.maximumFrameBytes, "agui_frame_limit_exceeded");
    if (!validateEvent(event)) fail("agui_event_schema_invalid", validateEvent.errors?.[0]?.instancePath ?? "");
    validateOwnerPresentationEvent(event);
    if (!EventSchemas.safeParse(event).success) fail("agui_official_event_schema_invalid", event.type);
    if (!validateStream(frame)) fail("agui_stream_schema_invalid", validateStream.errors?.[0]?.instancePath ?? "");
    validateBindingForFrame(
      frame,
      bindingAuthority.runRefs,
      bindingAuthority.messageRefs,
      bindingAuthority.ownerRefs,
      caseInput.snapshot,
    );
  }
  validateStreamState(caseInput.frames, runRefs, messageRefs);
  validateRebuiltFinalSnapshot(caseInput, bindingAuthority, contracts);
  if (!validateStream(caseInput.controlFrame) || caseInput.controlFrame.kind !== "control" || caseInput.controlFrame.id !== null) fail("agui_draining_not_nondurable");
  const lastFrame = caseInput.frames.at(-1);
  if (caseInput.controlFrame.data.lastDurableCursor !== lastFrame.id || caseInput.controlFrame.data.sessionId !== caseInput.snapshot.sessionId || caseInput.controlFrame.data.streamEpoch !== caseInput.snapshot.streamEpoch || caseInput.controlFrame.data.profileRevision !== caseInput.snapshot.profileRevision) fail("agui_draining_cursor_conflict");
  enforceLimits(caseInput.controlFrame, mapping.limits, mapping.limits.maximumFrameBytes, "agui_frame_limit_exceeded");
  return {
    durableFrames: caseInput.frames.length,
    bindingReplacementDeltas: caseInput.frames.filter(
      (frame) => frame.data.bindingAuthorityDelta.kind !== "none",
    ).length,
    sourceKinds: new Set(caseInput.frames.map((frame) => frame.data.source.sourceKind)),
  };
}

// Public callers can select a repository root only. Schema paths and validators remain fixed inside this module.
export function validateConformanceCase(caseInput, { root = repositoryRoot } = {}) {
  validateOfficialDependency(root);
  const contracts = loadContracts(root);
  validateProfile(contracts.profile);
  validateMappingRegistry(contracts.mapping);
  return validateConformanceCaseWithContracts(caseInput, contracts, createSemanticIdentityRegistries());
}

function setAtPath(value, path, replacement) {
  const segments = path.split(".");
  let cursor = value;
  for (const segment of segments.slice(0, -1)) {
    if (cursor === null || typeof cursor !== "object" || !(segment in cursor)) fail("agui_corpus_mutation_invalid", path);
    cursor = cursor[segment];
  }
  cursor[segments.at(-1)] = replacement;
}

function appendAttackFrame(candidate, baseFrame, input) {
  const frame = structuredClone(baseFrame);
  const next = (BigInt(candidate.frames.at(-1).data.source.durableSeq) + 1n).toString();
  frame.data.source.sourceEventId = input.sourceEventId;
  frame.data.source.sourceKind = input.sourceKind;
  frame.data.source.durableSeq = next;
  frame.data.source.projectionVersion = (BigInt(frame.data.source.projectionVersion) + 1n).toString();
  frame.data.source.recordedAt = input.recordedAt;
  frame.data.event.timestamp = Date.parse(input.recordedAt);
  candidate.frames.push(frame);
}

function refreshDerivedConformanceData(candidate) {
  for (const frame of candidate.frames) frame.id = issueCursor(frame.data.source);
  candidate.durableRows = candidate.frames.map((frame) => ({
    rowRef: `presentation-row.${frame.data.source.sourceEventId}`,
    profileRevision: frame.data.profileRevision,
    cursorProfileRevision: CURSOR_PROFILE_REVISION,
    source: structuredClone(frame.data.source),
    projectionPayload: structuredClone(frame.data),
    projectionPayloadDigest: projectionDigest(frame.data),
  }));
  candidate.controlFrame.data.lastDurableCursor = candidate.frames.at(-1).id;
}

export function applyCorpusMutation(candidate, mutation) {
  if (mutation?.operation === "set") {
    setAtPath(candidate, mutation.path, structuredClone(mutation.value));
    refreshDerivedConformanceData(candidate);
    return candidate;
  }
  if (mutation?.operation === "terminal-revival") {
    const frame = candidate.frames.find((entry) => entry.event === EventType.RUN_STARTED && entry.data.presentationRunBindingRef === mutation.runBindingRef);
    if (frame === undefined) fail("agui_corpus_mutation_invalid", "terminal-revival");
  appendAttackFrame(candidate, frame, { sourceEventId: "presentation.event:attack.terminal-revival", sourceKind: "presentation.run.started", recordedAt: "2026-08-01T12:00:27.000Z" });
    refreshDerivedConformanceData(candidate);
    return candidate;
  }
  if (mutation?.operation === "reopen-message") {
    const frame = candidate.frames.find((entry) => entry.event === EventType.TEXT_MESSAGE_CONTENT && entry.data.presentationMessageBindingRef === mutation.messageBindingRef);
    if (frame === undefined) fail("agui_corpus_mutation_invalid", "reopen-message");
  appendAttackFrame(candidate, frame, { sourceEventId: "presentation.event:attack.message-reopen", sourceKind: "presentation.message.text.content", recordedAt: "2026-08-01T12:00:27.000Z" });
    refreshDerivedConformanceData(candidate);
    return candidate;
  }
  fail("agui_corpus_mutation_invalid");
}

function validateAgentCandidateCoverage(corpus, contracts) {
  const { agentCandidateProfile, activityAuthority, validateAgentCandidate } = contracts;
  validateAgentCandidateProfile(agentCandidateProfile);
  const allowedActivityTypes = activityAuthority.activities
    .filter(({ candidateSource }) => candidateSource === "kokoro-agent")
    .map(({ activityType }) => activityType);
  const coveredEvents = new Set();
  const coveredActivities = new Set();
  let candidates = 0;
  for (const contractCase of corpus.positiveCases) {
    const runBindings = new Map(contractCase.runBindings.map((binding) => [binding.bindingRef, binding]));
    for (const frame of contractCase.frames) {
      const { event } = frame.data;
      if (event.type === EventType.RUN_FINISHED) {
        if (validateAgentCandidate(event)) fail("agui_agent_candidate_success_outcome_missing");
        const binding = runBindings.get(frame.data.presentationRunBindingRef);
        if (binding?.terminalDisposition !== "success") continue;
        const candidate = { ...event, outcome: { type: "success" } };
        if (!validateAgentCandidate(candidate) || !EventSchemas.safeParse(candidate).success) {
          fail("agui_agent_candidate_success_outcome_invalid");
        }
        coveredEvents.add(event.type);
        candidates += 1;
        continue;
      }
      const candidateEvent = event.type === EventType.RUN_STARTED
        ? Object.fromEntries(Object.entries(event).filter(([key]) => key !== "parentRunId"))
        : event;
      const allowed = agentCandidateProfile.allowedEventTypes.includes(event.type) && (
        event.type !== EventType.ACTIVITY_SNAPSHOT || allowedActivityTypes.includes(event.activityType)
      );
      const accepted = validateAgentCandidate(candidateEvent);
      if (allowed !== accepted) fail("agui_agent_candidate_schema_profile_drift", event.type);
      if (!allowed) continue;
      if (!EventSchemas.safeParse(candidateEvent).success) fail("agui_agent_candidate_official_schema_invalid", event.type);
      coveredEvents.add(event.type);
      if (event.type === EventType.ACTIVITY_SNAPSHOT) coveredActivities.add(event.activityType);
      candidates += 1;
    }
  }
  if (coveredEvents.size !== AGENT_CANDIDATE_EVENT_TYPES.length || AGENT_CANDIDATE_EVENT_TYPES.some((type) => !coveredEvents.has(type))) {
    fail("agui_agent_candidate_event_coverage_missing");
  }
  if (coveredActivities.size !== AGENT_CANDIDATE_ACTIVITY_TYPES.length || AGENT_CANDIDATE_ACTIVITY_TYPES.some((type) => !coveredActivities.has(type))) {
    fail("agui_agent_candidate_activity_coverage_missing");
  }
  return candidates;
}

function candidateRefForEnvelope(envelope) {
  const route = envelope.source.route;
  const material = [
    envelope.profileRevision,
    route.internalRunRef,
    route.internalThreadRef,
    route.internalMessageRef ?? "",
    envelope.source.sourceEventRef,
    envelope.source.sourceOrdinal,
    envelope.source.recordedAt,
    envelope.eventDigest,
  ].join("\u0000");
  return `agui_candidate:sha256:${sha256Bytes(Buffer.from(material, "utf8"))}`;
}

function privateRunRouteFor(contractCase, bindingRef) {
  return contractCase?.sessionPrivateRouteFixtures?.runs?.find(
    (route) => route.presentationRunBindingRef === bindingRef,
  );
}

function privateMessageRouteFor(contractCase, bindingRef) {
  return contractCase?.sessionPrivateRouteFixtures?.messages?.find(
    (route) => route.presentationMessageBindingRef === bindingRef,
  );
}

function privateProvenanceFor(contractCase, agentSourceEventRef) {
  return contractCase?.sessionPrivateRouteFixtures?.provenance?.find(
    (provenance) => provenance.agentSourceEventRef === agentSourceEventRef,
  );
}

function validateAgentSourceFixtures(corpus) {
  if (!Array.isArray(corpus.agentSourceFixtures) || corpus.agentSourceFixtures.length < 6) {
    fail("agui_agent_candidate_source_fixtures_missing");
  }
  const byRef = new Map();
  const byRun = new Map();
  const provenanceByAgentRef = new Map();
  for (const contractCase of corpus.positiveCases) {
    for (const provenance of contractCase.sessionPrivateRouteFixtures.provenance) {
      if (provenanceByAgentRef.has(provenance.agentSourceEventRef)) {
        fail("agui_private_provenance_duplicate", provenance.agentSourceEventRef);
      }
      provenanceByAgentRef.set(provenance.agentSourceEventRef, { contractCase, provenance });
    }
  }
  const usedProvenanceRefs = new Set();
  for (const fixture of corpus.agentSourceFixtures) {
    exactKeys(fixture, ["baseCaseId", "source"], "agui_agent_candidate_source_fixture_shape_invalid");
    const { source } = fixture;
    exactKeys(source, ["sourceEventRef", "sourceOrdinal", "recordedAt", "route"], "agui_agent_candidate_source_fixture_shape_invalid");
    exactKeys(
      source.route,
      Object.hasOwn(source.route, "internalMessageRef")
        ? ["internalRunRef", "internalThreadRef", "internalMessageRef"]
        : ["internalRunRef", "internalThreadRef"],
      "agui_agent_candidate_source_fixture_shape_invalid",
    );
    if (byRef.has(source.sourceEventRef)) fail("agui_agent_candidate_source_ref_duplicate", source.sourceEventRef);
    const ordinal = uint64(source.sourceOrdinal, "agui_agent_candidate_source_ordinal_invalid");
    const recordedAt = parseCanonicalUtcMs(source.recordedAt, "agui_agent_candidate_recorded_at_invalid");
    const base = corpus.positiveCases.find(({ id }) => id === fixture.baseCaseId);
    const provenanceEntry = provenanceByAgentRef.get(source.sourceEventRef);
    const provenance = provenanceEntry?.provenance;
    if (
      base === undefined || provenanceEntry === undefined || provenance === undefined ||
      provenanceEntry.contractCase !== base || provenance.sessionId !== base.snapshot.sessionId ||
      provenance.agentSourceEventRef === provenance.publicSourceEventId
    ) fail("agui_private_provenance_coverage_invalid", source.sourceEventRef);
    const frame = base?.frames.find(({ data }) => data.source.sourceEventId === provenance.publicSourceEventId);
    const runBinding = base?.runBindings.find(({ bindingRef }) => bindingRef === frame?.data.presentationRunBindingRef);
    const messageBinding = base?.messageBindings.find(({ bindingRef }) => bindingRef === frame?.data.presentationMessageBindingRef);
    const runRoute = privateRunRouteFor(base, runBinding?.bindingRef);
    const messageRoute = messageBinding === undefined ? undefined : privateMessageRouteFor(base, messageBinding.bindingRef);
    if (
      frame === undefined || runBinding === undefined || runRoute === undefined ||
      frame.data.source.recordedAt !== source.recordedAt || source.route.internalRunRef !== runRoute.internalRunRef
    ) fail("agui_agent_candidate_source_fixture_projection_invalid", source.sourceEventRef);
    const activityWithoutContainer = frame.data.event.type === EventType.ACTIVITY_SNAPSHOT && messageRoute === undefined;
    if (
      activityWithoutContainer
        ? !Object.hasOwn(source.route, "internalMessageRef")
        : messageRoute === undefined
          ? Object.hasOwn(source.route, "internalMessageRef")
          : source.route.internalMessageRef !== messageRoute.internalMessageRef
    ) {
      fail("agui_agent_candidate_source_fixture_projection_invalid", source.sourceEventRef);
    }
    let group = byRun.get(source.route.internalRunRef);
    if (group === undefined) {
      if (ordinal !== 0n) fail("agui_agent_candidate_source_ordinal_start_invalid", source.route.internalRunRef);
      if (frame.data.event.type !== EventType.RUN_STARTED) fail("agui_agent_candidate_thread_authority_invalid", source.route.internalRunRef);
      if (!source.route.internalThreadRef.startsWith("agent.thread:")) {
        fail("agui_agent_candidate_thread_authority_invalid", source.route.internalRunRef);
      }
      group = { internalThreadRef: source.route.internalThreadRef, entries: [] };
      byRun.set(source.route.internalRunRef, group);
    } else if (source.route.internalThreadRef !== group.internalThreadRef) {
      fail("agui_agent_candidate_thread_authority_invalid", source.route.internalRunRef);
    }
    const previous = group.entries.at(-1);
    if (previous !== undefined && (ordinal <= previous.ordinal || recordedAt < previous.recordedAt)) {
      fail("agui_agent_candidate_source_ordinal_not_increasing", source.route.internalRunRef);
    }
    group.entries.push({ ordinal, recordedAt });
    byRef.set(source.sourceEventRef, fixture);
    usedProvenanceRefs.add(source.sourceEventRef);
  }
  if (usedProvenanceRefs.size !== provenanceByAgentRef.size) fail("agui_private_provenance_coverage_invalid");
  const agentOrdinals = corpus.agentSourceFixtures.map(({ source }) => source.sourceOrdinal);
  const sessionSequences = corpus.agentSourceFixtures.map(({ baseCaseId, source }) => {
    const base = corpus.positiveCases.find(({ id }) => id === baseCaseId);
    const provenance = privateProvenanceFor(base, source.sourceEventRef);
    return base.frames.find(({ data }) => data.source.sourceEventId === provenance.publicSourceEventId).data.source.durableSeq;
  });
  if (canonical(agentOrdinals) === canonical(sessionSequences)) fail("agui_agent_candidate_source_ordinal_series_coupled");
  return byRef;
}

function validateAgentCandidateEnvelope(envelope, contracts) {
  if (!contracts.validateAgentCandidateEnvelope(envelope)) {
    fail("agui_agent_candidate_envelope_schema_invalid", contracts.validateAgentCandidateEnvelope.errors?.[0]?.instancePath ?? "");
  }
  uint64(envelope.source.sourceOrdinal, "agui_agent_candidate_source_ordinal_invalid");
  const recordedAt = parseCanonicalUtcMs(envelope.source.recordedAt);
  if (recordedAt !== envelope.event.timestamp) fail("agui_agent_candidate_recorded_at_invalid");
  if (!contracts.validateAgentCandidate(envelope.event) || !EventSchemas.safeParse(envelope.event).success) {
    fail("agui_agent_candidate_event_invalid", envelope.event.type);
  }
  if (Buffer.byteLength(canonical(envelope.event), "utf8") > 65_536) fail("agui_agent_candidate_event_limit_exceeded");
  if (projectionDigest(envelope.event) !== envelope.eventDigest) fail("agui_agent_candidate_event_digest_invalid");
  if (candidateRefForEnvelope(envelope) !== envelope.candidateRef) fail("agui_agent_candidate_ref_invalid");

  const route = envelope.source.route;
  if ([EventType.RUN_STARTED, EventType.RUN_FINISHED].includes(envelope.event.type)) {
    if (Object.hasOwn(route, "internalMessageRef") || envelope.event.threadId !== route.internalThreadRef || envelope.event.runId !== route.internalRunRef) {
      fail("agui_agent_candidate_run_route_invalid");
    }
  } else if (envelope.event.type === EventType.RUN_ERROR) {
    if (Object.hasOwn(route, "internalMessageRef")) fail("agui_agent_candidate_run_route_invalid");
  } else {
    if (!Object.hasOwn(route, "internalMessageRef") || envelope.event.messageId !== route.internalMessageRef) {
      fail("agui_agent_candidate_message_route_invalid");
    }
  }
  if (envelope.event.type === EventType.RUN_FINISHED && canonical(envelope.event.outcome) !== canonical({ type: "success" })) {
    fail("agui_agent_candidate_success_outcome_invalid");
  }
  return envelope.event;
}

function validateAgentCandidateEnvelopeCorpus(corpus, contracts, sourceFixtures, usedSourceRefs) {
  if (!Array.isArray(corpus.agentCandidateEnvelopeCases) || corpus.agentCandidateEnvelopeCases.length < 5) {
    fail("agui_agent_candidate_envelope_corpus_missing");
  }
  const caseIds = new Set();
  const routeFamilies = new Set();
  for (const envelopeCase of corpus.agentCandidateEnvelopeCases) {
    exactKeys(envelopeCase, ["id", "baseCaseId", "sourceEventId", "candidateEnvelope"], "agui_agent_candidate_envelope_case_shape_invalid");
    if (caseIds.has(envelopeCase.id)) fail("agui_agent_candidate_envelope_case_duplicate", envelopeCase.id);
    caseIds.add(envelopeCase.id);
    const base = corpus.positiveCases.find(({ id }) => id === envelopeCase.baseCaseId);
    const frame = base?.frames.find(({ data }) => data.source.sourceEventId === envelopeCase.sourceEventId);
    const runBinding = base?.runBindings.find(({ bindingRef }) => bindingRef === frame?.data.presentationRunBindingRef);
    const messageBinding = base?.messageBindings.find(({ bindingRef }) => bindingRef === frame?.data.presentationMessageBindingRef);
    const ownerBinding = base?.ownerBindings.find(({ bindingRef }) => bindingRef === frame?.data.presentationOwnerBindingRef);
    const runRoute = privateRunRouteFor(base, runBinding?.bindingRef);
    const messageRoute = messageBinding === undefined ? undefined : privateMessageRouteFor(base, messageBinding.bindingRef);
    if (frame === undefined || runBinding === undefined || runRoute === undefined) fail("agui_agent_candidate_envelope_source_invalid", envelopeCase.id);
    const candidateEvent = validateAgentCandidateEnvelope(envelopeCase.candidateEnvelope, contracts);
    const { source } = envelopeCase.candidateEnvelope;
    const provenance = privateProvenanceFor(base, source.sourceEventRef);
    const fixture = sourceFixtures.get(source.sourceEventRef);
    if (fixture === undefined || fixture.baseCaseId !== envelopeCase.baseCaseId || canonical(fixture.source) !== canonical(source)) {
      fail("agui_agent_candidate_source_fixture_mismatch", envelopeCase.id);
    }
    usedSourceRefs.add(source.sourceEventRef);
    if (source.sourceOrdinal === "0" && candidateEvent.type !== EventType.RUN_STARTED) {
      fail("agui_agent_candidate_thread_authority_invalid", source.route.internalRunRef);
    }
    if (
      provenance?.publicSourceEventId !== frame.data.source.sourceEventId ||
      provenance?.sessionId !== base.snapshot.sessionId ||
      source.recordedAt !== frame.data.source.recordedAt || source.route.internalRunRef !== runRoute.internalRunRef
    ) fail("agui_agent_candidate_envelope_source_invalid", envelopeCase.id);
    const activityWithoutContainer = candidateEvent.type === EventType.ACTIVITY_SNAPSHOT && messageRoute === undefined;
    if (
      activityWithoutContainer
        ? !Object.hasOwn(source.route, "internalMessageRef")
        : messageRoute === undefined
          ? Object.hasOwn(source.route, "internalMessageRef")
          : source.route.internalMessageRef !== messageRoute.internalMessageRef
    ) {
      fail("agui_agent_candidate_envelope_source_invalid", envelopeCase.id);
    }
    const projected = structuredClone(candidateEvent);
    if ([EventType.RUN_STARTED, EventType.RUN_FINISHED].includes(projected.type)) {
      projected.threadId = runBinding.presentationThreadId;
      projected.runId = runBinding.presentationRunId;
    }
    if (projected.type === EventType.RUN_STARTED && runBinding.parentLineage.parentPresentationRunId !== null) {
      projected.parentRunId = runBinding.parentLineage.parentPresentationRunId;
    }
    if ([EventType.TEXT_MESSAGE_START, EventType.TEXT_MESSAGE_CONTENT, EventType.TEXT_MESSAGE_END].includes(projected.type)) {
      projected.messageId = messageBinding.presentationMessageId;
    }
    if (projected.type === EventType.ACTIVITY_SNAPSHOT) {
      if (ownerBinding === undefined) fail("agui_agent_candidate_envelope_source_invalid", envelopeCase.id);
      projected.messageId = ownerBinding.presentationOwnerMessageId;
    }
    if (projected.type === EventType.RUN_FINISHED) delete projected.outcome;
    if (canonical(projected) !== canonical(frame.data.event)) fail("agui_agent_candidate_envelope_projection_invalid", envelopeCase.id);
    if (candidateEvent.type === EventType.RUN_STARTED) routeFamilies.add("run-start");
    else if (candidateEvent.type === EventType.RUN_ERROR) routeFamilies.add("run-error");
    else if ([EventType.TEXT_MESSAGE_START, EventType.TEXT_MESSAGE_CONTENT, EventType.TEXT_MESSAGE_END].includes(candidateEvent.type)) routeFamilies.add("message-text");
    else if (candidateEvent.type === EventType.ACTIVITY_SNAPSHOT) routeFamilies.add("message-activity");
  }
  for (const family of ["run-start", "run-error", "message-text", "message-activity"]) {
    if (!routeFamilies.has(family)) fail("agui_agent_candidate_envelope_route_coverage_missing", family);
  }
  return corpus.agentCandidateEnvelopeCases.length;
}

function validateAgentCandidateNegativeCorpus(corpus, contracts) {
  if (!Array.isArray(corpus.agentCandidateNegativeCases) || corpus.agentCandidateNegativeCases.length < 5) {
    fail("agui_agent_candidate_negative_corpus_missing");
  }
  const caseIds = new Set();
  for (const negativeCase of corpus.agentCandidateNegativeCases) {
    exactKeys(negativeCase, ["id", "candidateEnvelope", "expectedCode"], "agui_agent_candidate_negative_case_shape_invalid");
    if (caseIds.has(negativeCase.id)) fail("agui_agent_candidate_negative_case_duplicate", negativeCase.id);
    caseIds.add(negativeCase.id);
    let observed;
    try {
      validateAgentCandidateEnvelope(negativeCase.candidateEnvelope, contracts);
    } catch (error) {
      if (error instanceof AguiPresentationContractError) observed = error.code;
      else throw error;
    }
    if (observed !== negativeCase.expectedCode) {
      fail("agui_agent_candidate_negative_case_expectation_invalid", `${negativeCase.id}:${observed ?? "accepted"}`);
    }
  }
  return corpus.agentCandidateNegativeCases.length;
}

function validateAgentCandidateProjectionCorpus(corpus, contracts, sourceFixtures, usedSourceRefs) {
  if (!Array.isArray(corpus.agentCandidateProjectionCases) || corpus.agentCandidateProjectionCases.length < 1) {
    fail("agui_agent_candidate_projection_corpus_missing");
  }
  const caseIds = new Set();
  for (const projectionCase of corpus.agentCandidateProjectionCases) {
    exactKeys(projectionCase, ["id", "baseCaseId", "sourceEventId", "candidateEnvelope", "expectedPresentationEvent"], "agui_agent_candidate_projection_case_shape_invalid");
    if (caseIds.has(projectionCase.id)) fail("agui_agent_candidate_projection_case_duplicate", projectionCase.id);
    caseIds.add(projectionCase.id);
    const base = corpus.positiveCases.find(({ id }) => id === projectionCase.baseCaseId);
    const frame = base?.frames.find(({ data }) => data.source.sourceEventId === projectionCase.sourceEventId);
    const binding = base?.runBindings.find(({ bindingRef }) => bindingRef === frame?.data.presentationRunBindingRef);
    const runRoute = privateRunRouteFor(base, binding?.bindingRef);
    if (frame?.data.event.type !== EventType.RUN_FINISHED || binding?.terminalDisposition !== "success" || runRoute === undefined) {
      fail("agui_agent_candidate_projection_source_invalid", projectionCase.id);
    }
    const candidateEvent = validateAgentCandidateEnvelope(projectionCase.candidateEnvelope, contracts);
    const provenance = privateProvenanceFor(base, projectionCase.candidateEnvelope.source.sourceEventRef);
    const fixture = sourceFixtures.get(projectionCase.candidateEnvelope.source.sourceEventRef);
    if (fixture === undefined || fixture.baseCaseId !== projectionCase.baseCaseId || canonical(fixture.source) !== canonical(projectionCase.candidateEnvelope.source)) {
      fail("agui_agent_candidate_source_fixture_mismatch", projectionCase.id);
    }
    usedSourceRefs.add(projectionCase.candidateEnvelope.source.sourceEventRef);
    if (
      provenance?.publicSourceEventId !== projectionCase.sourceEventId ||
      provenance?.sessionId !== base.snapshot.sessionId ||
      projectionCase.candidateEnvelope.source.recordedAt !== frame.data.source.recordedAt ||
      projectionCase.candidateEnvelope.source.route.internalRunRef !== runRoute.internalRunRef ||
      Object.hasOwn(candidateEvent, "result")
    ) {
      fail("agui_agent_candidate_projection_candidate_invalid", projectionCase.id);
    }
    const { outcome, ...projectedCandidate } = candidateEvent;
    void outcome;
    const projected = {
      ...projectedCandidate,
      threadId: binding.presentationThreadId,
      runId: binding.presentationRunId,
    };
    if (canonical(projected) !== canonical(projectionCase.expectedPresentationEvent) || canonical(projected) !== canonical(frame.data.event)) {
      fail("agui_agent_candidate_projection_strip_invalid", projectionCase.id);
    }
    if (!contracts.validateEvent(projected) || !EventSchemas.safeParse(projected).success) {
      fail("agui_agent_candidate_projection_presentation_invalid", projectionCase.id);
    }
  }
  return corpus.agentCandidateProjectionCases.length;
}

function incrementCount(counts, key) {
  counts.set(key, (counts.get(key) ?? 0) + 1);
}

function validateAgentCandidateSemanticCoverage(corpus, profile, activityAuthority) {
  const cases = [...corpus.agentCandidateEnvelopeCases, ...corpus.agentCandidateProjectionCases];
  const eventCounts = new Map();
  const activityCounts = new Map();
  const startedRunCounts = new Map();
  const successRunCounts = new Map();
  const errorRunCounts = new Map();
  for (const candidateCase of cases) {
    const { event, source } = candidateCase.candidateEnvelope;
    incrementCount(eventCounts, event.type);
    if (event.type === EventType.ACTIVITY_SNAPSHOT) incrementCount(activityCounts, event.activityType);
    if (event.type === EventType.RUN_STARTED) incrementCount(startedRunCounts, source.route.internalRunRef);
    if (event.type === EventType.RUN_FINISHED) incrementCount(successRunCounts, source.route.internalRunRef);
    if (event.type === EventType.RUN_ERROR) incrementCount(errorRunCounts, source.route.internalRunRef);
  }
  const observedEvents = [...eventCounts.keys()];
  if (
    observedEvents.length !== profile.allowedEventTypes.length ||
    observedEvents.some((eventType) => !profile.allowedEventTypes.includes(eventType))
  ) fail("agui_agent_candidate_semantic_coverage_invalid", "event-set");
  for (const eventType of profile.allowedEventTypes) {
    if ([EventType.RUN_STARTED, EventType.ACTIVITY_SNAPSHOT].includes(eventType)) continue;
    if (eventCounts.get(eventType) !== 1) fail("agui_agent_candidate_semantic_coverage_invalid", eventType);
  }
  const observedActivities = [...activityCounts.keys()];
  const allowedActivityTypes = activityAuthority.activities
    .filter(({ candidateSource }) => candidateSource === "kokoro-agent")
    .map(({ activityType }) => activityType);
  if (
    eventCounts.get(EventType.ACTIVITY_SNAPSHOT) !== allowedActivityTypes.length ||
    observedActivities.length !== allowedActivityTypes.length ||
    observedActivities.some((activityType) => !allowedActivityTypes.includes(activityType)) ||
    observedActivities.some((activityType) => activityCounts.get(activityType) !== 1)
  ) fail("agui_agent_candidate_activity_coverage_invalid");
  if (successRunCounts.size !== 1 || errorRunCounts.size !== 1) {
    fail("agui_agent_candidate_semantic_coverage_invalid", "terminal-runs");
  }
  const successRunRef = successRunCounts.keys().next().value;
  const errorRunRef = errorRunCounts.keys().next().value;
  if (
    successRunRef === errorRunRef || successRunCounts.get(successRunRef) !== 1 || errorRunCounts.get(errorRunRef) !== 1 ||
    startedRunCounts.size !== 2 || startedRunCounts.get(successRunRef) !== 1 || startedRunCounts.get(errorRunRef) !== 1
  ) fail("agui_agent_candidate_semantic_coverage_invalid", "run-start-authority");
}

function applySnapshotAuthorityMutation(authorityCase, mutation) {
  const snapshot = authorityCase.snapshot;
  if (mutation?.operation === "snapshot-terminal-owner-revival") {
    const current = snapshot.ownerProjectionRows.find(
      ({ event }) => event.type === EventType.ACTIVITY_SNAPSHOT && event.activityType === "kokoro.safe-summary.v1",
    );
    if (current === undefined) fail("agui_snapshot_authority_mutation_invalid");
    authorityCase.nextOwnerProjectionRow = structuredClone(current);
    authorityCase.nextOwnerProjectionRow.sourceEventId = `presentation.event:${"f".repeat(64)}`;
    authorityCase.nextOwnerProjectionRow.projectionVersion = String(
      uint64(snapshot.durableSeq, "agui_snapshot_cursor_invalid") + 1n,
    );
    authorityCase.nextOwnerProjectionRow.recordedAt = authorityCase.nextEventRecordedAt;
    authorityCase.nextOwnerProjectionRow.event.timestamp = Date.parse(authorityCase.nextEventRecordedAt);
    authorityCase.nextOwnerProjectionRow.event.content.ownerVersion = "2";
    authorityCase.nextOwnerProjectionRow.event.content.status = "streaming";
    authorityCase.nextOwnerProjectionRow.event.content.updatedAt = authorityCase.nextEventRecordedAt;
    return authorityCase;
  }
  if (mutation?.operation === "zero-head-retains-bindings") {
    snapshot.durableSeq = "0";
    snapshot.lastRecordedAt = null;
    return authorityCase;
  }
  if (mutation?.operation === "binding-evidence-exceeds-head") {
    snapshot.durableSeq = "1";
    return authorityCase;
  }
  if (mutation?.operation === "noncanonical-binding-time") {
    snapshot.runBindings[0].openedAt = "2026-08-01T13:00:01Z";
    return authorityCase;
  }
  if (mutation?.operation === "multiple-presentation-thread") {
    snapshot.runBindings[1].presentationThreadId = `presentation.thread:${"0".repeat(64)}`;
    return authorityCase;
  }
  if (mutation?.operation === "parent-lineage-cycle") {
    snapshot.runBindings[0].parentLineage = {
      parentPresentationRunId: snapshot.runBindings[1].presentationRunId,
    };
    snapshot.runBindings[0].sessionRunId = null;
    return authorityCase;
  }
  if (mutation?.operation === "m0-interrupted-terminal") {
    snapshot.runBindings[0].terminalDisposition = "interrupted";
    return authorityCase;
  }
  fail("agui_snapshot_authority_mutation_invalid");
}

function validateSnapshotAuthorityCase(authorityCase, corpus, contracts) {
  exactKeys(
    authorityCase,
    ["id", "baseCaseId", "snapshot", "nextEventRecordedAt", "nextOwnerProjectionRow"],
    "agui_snapshot_authority_case_shape_invalid",
  );
  const base = corpus.positiveCases.find(({ id }) => id === authorityCase.baseCaseId);
  if (base === undefined || authorityCase.snapshot.sessionId !== base.snapshot.sessionId) {
    fail("agui_snapshot_authority_case_base_invalid", authorityCase.id);
  }
  const watermark = validateSnapshotTimeAuthority(
    authorityCase.snapshot,
    contracts.validateSnapshotAuthoritySchema,
    authorityCase.snapshot.runBindings,
    authorityCase.snapshot.messageBindings,
    authorityCase.snapshot.ownerBindings,
    authorityCase.snapshot.ownerProjectionRows,
    authorityCase.nextEventRecordedAt,
  );
  if (!contracts.validateSnapshotAuthoritySchema(authorityCase.snapshot)) {
    fail("agui_snapshot_authority_schema_invalid", contracts.validateSnapshotAuthoritySchema.errors?.[0]?.instancePath ?? "");
  }
  validateSnapshotBindingAuthority(authorityCase.snapshot, contracts);
  if (watermark === Number.NEGATIVE_INFINITY) fail("agui_snapshot_authority_case_nonzero_required", authorityCase.id);
  const next = authorityCase.nextOwnerProjectionRow;
  if (!contracts.validateOwnerProjectionRow(next)) {
    fail("agui_owner_projection_row_schema_invalid", contracts.validateOwnerProjectionRow.errors?.[0]?.instancePath ?? "");
  }
  validatePublicSourceEventId(next.sourceEventId);
  validateOwnerPresentationEvent(next.event);
  if (
    next.recordedAt !== authorityCase.nextEventRecordedAt || next.event.timestamp !== Date.parse(next.recordedAt) ||
    Date.parse(next.recordedAt) <= watermark
  ) fail("agui_owner_projection_time_invalid");
  const binding = authorityCase.snapshot.ownerBindings.find(
    ({ bindingRef }) => bindingRef === next.presentationOwnerBindingRef,
  );
  const current = authorityCase.snapshot.ownerProjectionRows.find(
    ({ presentationOwnerBindingRef }) => presentationOwnerBindingRef === next.presentationOwnerBindingRef,
  );
  if (
    binding === undefined || current === undefined ||
    canonical(ownerIdentityForEvent(next.event)) !== canonical(binding.ownerIdentity) ||
    (next.event.type === EventType.ACTIVITY_SNAPSHOT && next.event.messageId !== binding.presentationOwnerMessageId)
  ) fail("agui_owner_projection_identity_conflict", next.presentationOwnerBindingRef);
  reduceOwnerProjectionRow(current, next);
  const claims = decodeCursor(authorityCase.snapshot.cursor, contracts.mapping.limits.maximumCursorBytes);
  assertCursorScope(claims, {
    sessionId: authorityCase.snapshot.sessionId,
    streamEpoch: authorityCase.snapshot.streamEpoch,
    durableSeq: authorityCase.snapshot.durableSeq,
    profileRevision: authorityCase.snapshot.profileRevision,
    cursorProfileRevision: CURSOR_PROFILE_REVISION,
  });
}

function validateSnapshotAuthorityCorpus(corpus, contracts) {
  if (!Array.isArray(corpus.snapshotAuthorityCases) || corpus.snapshotAuthorityCases.length < 1) fail("agui_snapshot_authority_corpus_missing");
  const caseIds = new Set();
  for (const authorityCase of corpus.snapshotAuthorityCases) {
    if (caseIds.has(authorityCase.id)) fail("agui_snapshot_authority_case_duplicate", authorityCase.id);
    caseIds.add(authorityCase.id);
    validateSnapshotAuthorityCase(authorityCase, corpus, contracts);
  }
  if (!Array.isArray(corpus.snapshotAuthorityNegativeCases) || corpus.snapshotAuthorityNegativeCases.length < 1) {
    fail("agui_snapshot_authority_negative_corpus_missing");
  }
  const negativeIds = new Set();
  for (const attack of corpus.snapshotAuthorityNegativeCases) {
    exactKeys(attack, ["id", "baseAuthorityCaseId", "mutation", "expectedCode"], "agui_snapshot_authority_negative_case_shape_invalid");
    exactKeys(attack.mutation, ["operation"], "agui_snapshot_authority_negative_case_shape_invalid");
    if (negativeIds.has(attack.id)) fail("agui_snapshot_authority_negative_case_duplicate", attack.id);
    negativeIds.add(attack.id);
    const base = corpus.snapshotAuthorityCases.find(({ id }) => id === attack.baseAuthorityCaseId);
    if (base === undefined) fail("agui_snapshot_authority_negative_case_base_invalid", attack.id);
    const candidate = applySnapshotAuthorityMutation(structuredClone(base), attack.mutation);
    let observed;
    try {
      validateSnapshotAuthorityCase(candidate, corpus, contracts);
    } catch (error) {
      if (error instanceof AguiPresentationContractError) observed = error.code;
      else throw error;
    }
    if (observed !== attack.expectedCode) {
      fail("agui_snapshot_authority_negative_case_expectation_invalid", `${attack.id}:${observed ?? "accepted"}`);
    }
  }
  return {
    positive: corpus.snapshotAuthorityCases.length,
    negative: corpus.snapshotAuthorityNegativeCases.length,
  };
}

export async function validateRepository({ root = repositoryRoot } = {}) {
  validateOfficialDependency(root);
  const corpus = JSON.parse(await readFile(safePath(root, CORPUS_PATH), "utf8"));
  if (corpus.corpusId !== "kokoro.agui.presentation-conformance.v1" || corpus.profileRevision !== PROFILE_REVISION) fail("agui_corpus_identity_invalid");
  exactKeys(corpus.contracts, Object.keys(CONTRACT_PATHS), "agui_contract_paths_invalid");
  if (canonical(corpus.contracts) !== canonical(CONTRACT_PATHS)) fail("agui_contract_paths_invalid");
  const contracts = loadContracts(root);
  validateProfile(contracts.profile);
  validateAgentCandidateProfile(contracts.agentCandidateProfile);
  validateAgentCandidateSchemaContract(contracts.agentCandidateSchema);
  validateActivityAuthority(contracts.activityAuthority, contracts.eventSchema, contracts.agentCandidateSchema);
  validateMappingRegistry(contracts.mapping);
  if (!Array.isArray(corpus.positiveCases) || corpus.positiveCases.length < 2 || !Array.isArray(corpus.negativeCases) || corpus.negativeCases.length < 10) fail("agui_corpus_shape_invalid");
  const caseIds = new Set();
  const covered = new Set();
  const identities = createSemanticIdentityRegistries();
  let durableFrames = 0;
  let bindingReplacementDeltas = 0;
  for (const contractCase of corpus.positiveCases) {
    if (caseIds.has(contractCase.id)) fail("agui_corpus_case_duplicate", contractCase.id);
    caseIds.add(contractCase.id);
    const result = validateConformanceCaseWithContracts(contractCase, contracts, identities);
    durableFrames += result.durableFrames;
    bindingReplacementDeltas += result.bindingReplacementDeltas;
    for (const sourceKind of result.sourceKinds) covered.add(sourceKind);
  }
  const expectedMappings = new Set(contracts.mapping.mappings.map(({ sourceKind }) => sourceKind));
  if (covered.size !== expectedMappings.size || [...expectedMappings].some((sourceKind) => !covered.has(sourceKind))) fail("agui_mapping_corpus_coverage_missing");
  const agentCandidates = validateAgentCandidateCoverage(corpus, contracts);
  const agentSourceFixtures = validateAgentSourceFixtures(corpus);
  const usedAgentSourceRefs = new Set();
  const agentCandidateEnvelopeCases = validateAgentCandidateEnvelopeCorpus(corpus, contracts, agentSourceFixtures, usedAgentSourceRefs);
  const agentCandidateProjectionCases = validateAgentCandidateProjectionCorpus(corpus, contracts, agentSourceFixtures, usedAgentSourceRefs);
  const agentCandidateNegativeCases = validateAgentCandidateNegativeCorpus(corpus, contracts);
  validateAgentCandidateSemanticCoverage(corpus, contracts.agentCandidateProfile, contracts.activityAuthority);
  if (usedAgentSourceRefs.size !== agentSourceFixtures.size || [...agentSourceFixtures.keys()].some((sourceRef) => !usedAgentSourceRefs.has(sourceRef))) {
    fail("agui_agent_candidate_source_fixture_unused");
  }
  const snapshotAuthority = validateSnapshotAuthorityCorpus(corpus, contracts);
  const negativeIds = new Set();
  for (const attack of corpus.negativeCases) {
    if (negativeIds.has(attack.id) || !caseIds.has(attack.baseCaseId)) fail("agui_negative_case_invalid", attack.id);
    negativeIds.add(attack.id);
    const base = corpus.positiveCases.find(({ id }) => id === attack.baseCaseId);
    const candidate = applyCorpusMutation(structuredClone(base), attack.mutation);
    let observed;
    try {
      validateConformanceCaseWithContracts(candidate, contracts, createSemanticIdentityRegistries());
    } catch (error) {
      if (error instanceof AguiPresentationContractError) observed = error.code;
      else throw error;
    }
    if (observed !== attack.expectedCode) fail("agui_negative_case_expectation_invalid", `${attack.id}:${observed ?? "accepted"}`);
  }
  return {
    positiveCases: corpus.positiveCases.length,
    negativeCases: corpus.negativeCases.length,
    durableFrames,
    bindingReplacementDeltas,
    mappingsCovered: covered.size,
    agentCandidates,
    agentSourceFixtures: agentSourceFixtures.size,
    agentCandidateEnvelopeCases,
    agentCandidateProjectionCases,
    agentCandidateNegativeCases,
    snapshotAuthorityCases: snapshotAuthority.positive,
    snapshotAuthorityNegativeCases: snapshotAuthority.negative,
  };
}

async function main(argv) {
  let root = repositoryRoot;
  if (argv.length !== 0) {
    if (argv.length !== 2 || argv[0] !== "--root") fail("agui_arguments_invalid");
    root = resolve(argv[1]);
  }
  const result = await validateRepository({ root });
  process.stdout.write(`agui_presentation_ok: ${result.positiveCases} positive, ${result.negativeCases} negative, ${result.durableFrames} durable frames, ${result.bindingReplacementDeltas} binding replacements, ${result.mappingsCovered} closed mappings, ${result.agentCandidates} Agent candidate events, ${result.agentSourceFixtures} Agent source fixtures, ${result.agentCandidateEnvelopeCases} Agent envelopes, ${result.agentCandidateProjectionCases} Agent projection cases, ${result.agentCandidateNegativeCases} Agent candidate attacks, ${result.snapshotAuthorityCases} snapshot authority cases, ${result.snapshotAuthorityNegativeCases} snapshot authority attacks\n`);
}

if (process.argv[1] && pathToFileURL(process.argv[1]).href === import.meta.url) {
  try {
    await main(process.argv.slice(2));
  } catch (error) {
    const message = error instanceof AguiPresentationContractError ? error.message : "agui_presentation_failed";
    process.stderr.write(`${message}\n`);
    process.exitCode = 1;
  }
}
