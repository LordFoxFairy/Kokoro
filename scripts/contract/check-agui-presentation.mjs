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
  mapping: "contract/registry/agui-presentation-mapping-v1.yaml",
  eventSchema: "contract/spec/kokoro-agui-presentation-event-v1.yaml",
  agentCandidateSchema: "contract/spec/agent-agui-event-candidate-v1.yaml",
  agentCandidateEnvelopeSchema: "contract/spec/agent-agui-candidate-envelope-v1.yaml",
  projectionPayloadSchema: "contract/spec/session-agui-projection-payload-v1.yaml",
  presentationRowSchema: "contract/spec/session-agui-presentation-row-v1.yaml",
  bindingAuthorityDeltaSchema: "contract/spec/presentation-binding-authority-delta-v1.yaml",
  runBindingSchema: "contract/spec/presentation-run-binding-v1.yaml",
  messageBindingSchema: "contract/spec/presentation-message-binding-v1.yaml",
  streamSchema: "contract/spec/session-agui-stream-v1.yaml",
  snapshotAuthoritySchema: "contract/spec/session-agui-snapshot-authority-v1.yaml",
});

// These are the reviewed contract sources, not caller-selected schemas carrying a familiar $id.
const CONTRACT_SOURCE_SHA256 = Object.freeze({
  profile: "9692d77ff42726598b8547c63250556232d8fcd76c0faf19e6e37079a4f0ddd5",
  agentCandidateProfile: "55097c5ab3aa8700be601074f0d8dc78871cdbbf9250af6a311c341f55570743",
  mapping: "59ff197cc52c0cbcacaec38aff0f5ae0dd12b241dc6df658f47c33b6e66d6888",
  eventSchema: "e9873b1fabdc180aeee782e61243285321ec20c0f37670ea7a79d95f9a62b8d9",
  agentCandidateSchema: "b203876638e975bd3899bef09b8afdf8f183a6f9cd7939d67ddf8f7d90ac3731",
  agentCandidateEnvelopeSchema: "87562d25f01a19cb21717b6d0a7f9bc5cf1bd3e45c413d7eae7270231ea123f0",
  projectionPayloadSchema: "12a93a3b799601b2743dbfa96bd6c1833bd7a837914f481dc5a4d940d9c6de16",
  presentationRowSchema: "bc2286f915ed7f0c5281fb6210c3ce7fd9dac0d397cff849edb01a106cfc430f",
  bindingAuthorityDeltaSchema: "9fd30b734e2aa5f52be50eb1442eaf16843de8baa8098fcc996bc5e057f9dd2d",
  runBindingSchema: "d507453e4e5458720476c61c9b013c8f2ec1d3f25a516b41f245e083c60615e6",
  messageBindingSchema: "2a8a00e9f94da0b3792428a9dcfbead6e6e1ea9057f273792965c0f8714d261f",
  streamSchema: "ce51651ab17c080838547ec74c73a86574b9134aed351c7f27d92d1709441333",
  snapshotAuthoritySchema: "6c2ee288041cf29ea4dccd318c58bbaa4d19e1577de0acaf00aae076479e39e8",
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
  "kokoro.media.v1",
  "kokoro.notice.v1",
  "kokoro.error.v1",
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
    ajv.addSchema(sources.bindingAuthorityDeltaSchema);
    ajv.addSchema(sources.agentCandidateSchema);
    ajv.addSchema(sources.agentCandidateEnvelopeSchema);
    ajv.addSchema(sources.projectionPayloadSchema);
    ajv.addSchema(sources.presentationRowSchema);
    return Object.freeze({
      profile: sources.profile,
      agentCandidateProfile: sources.agentCandidateProfile,
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
    ["profileId", "profileRevision", "lifecycle", "eventSchema", "envelopeSchema", "producer", "consumer", "allowedEventTypes", "allowedActivityTypes", "forbiddenEventTypes", "forbiddenEventFamilies", "forbiddenOwnerActivityTypes", "forbiddenFields", "terminalPolicy", "projectionPolicy", "identityPolicy", "eventScopePolicy", "activation"],
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
  exactArray(profile.allowedActivityTypes, AGENT_CANDIDATE_ACTIVITY_TYPES, "agui_agent_candidate_activities_invalid");
  const forbiddenExpected = OFFICIAL_EVENT_TYPES.filter((type) => !AGENT_CANDIDATE_EVENT_TYPES.includes(type));
  if (new Set(profile.forbiddenEventTypes).size !== forbiddenExpected.length || forbiddenExpected.some((type) => !profile.forbiddenEventTypes.includes(type))) {
    fail("agui_agent_candidate_forbidden_events_incomplete");
  }
  for (const family of ["raw", "state", "messages", "delta", "native-tool", "reasoning", "thinking", "step", "chunk", "custom"]) {
    if (!profile.forbiddenEventFamilies.includes(family)) fail("agui_agent_candidate_forbidden_family_missing", family);
  }
  exactArray(profile.forbiddenOwnerActivityTypes, ["kokoro.artifact.v1", "kokoro.cost.v1"], "agui_agent_candidate_owner_activity_invalid");
  for (const field of ["rawEvent", "raw_event", "providerEvent", "provider_event", "messages", "input", "result", "extra"]) {
    if (!profile.forbiddenFields.includes(field)) fail("agui_agent_candidate_forbidden_field_missing", field);
  }
  exactKeys(profile.terminalPolicy, ["runFinished", "runError", "canceledOrInterrupted"], "agui_agent_candidate_terminal_policy_invalid");
  if (
    profile.terminalPolicy.runFinished !== "success-only" || profile.terminalPolicy.runError !== "failure-only" ||
    profile.terminalPolicy.canceledOrInterrupted !== "session-owned-projection"
  ) fail("agui_agent_candidate_terminal_policy_invalid");
  exactKeys(profile.projectionPolicy, ["sessionAdmission", "runFinishedOutcome", "routeProjection", "ownerActivitySynthesis"], "agui_agent_candidate_projection_policy_invalid");
  if (
    profile.projectionPolicy.sessionAdmission !== "validate-before-durable-projection" ||
    profile.projectionPolicy.runFinishedOutcome !== "strip-after-success-validation" ||
    profile.projectionPolicy.routeProjection !== "resolve-through-session-presentation-binding" ||
    profile.projectionPolicy.ownerActivitySynthesis !== "session-owner-facts-only"
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

function validateAgentCandidateSchemaContract(schema) {
  exactKeys(schema, ["$schema", "$id", "title", "description", "oneOf", "$defs"], "agui_agent_candidate_schema_shape_invalid");
  if (
    schema.$schema !== "https://json-schema.org/draft/2020-12/schema" ||
    schema.$id !== "https://contracts.kokoro.invalid/agent-agui-event-candidate.v1.schema.json"
  ) fail("agui_agent_candidate_schema_identity_invalid");
  const presentationSchemaId = "https://contracts.kokoro.invalid/kokoro-agui-presentation-event.v1.schema.json";
  const definitions = [
    null, null, "runError", "textStart", "textContent", "textEnd", "activitySafeSummary",
    "activityToolPreview", "activityHitl", "activityPlan", "activitySubagent", "activityMedia", "activityNotice", "activityError",
  ];
  exactArray(
    schema.oneOf,
    definitions.map((definition, index) => ({ $ref: definition === null ? (index === 0 ? "#/$defs/runStartedWithoutParent" : "#/$defs/runFinishedSuccess") : `${presentationSchemaId}#/$defs/${definition}` })),
    "agui_agent_candidate_schema_refs_invalid",
  );
  exactKeys(schema.$defs, ["runStartedWithoutParent", "runFinishedSuccess"], "agui_agent_candidate_schema_defs_invalid");
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
    const requiredDeltaKind = BINDING_DELTA_KIND_BY_EVENT.get(entry.eventType) ?? "none";
    if (entry.bindingAuthorityDeltaKind !== requiredDeltaKind) fail("agui_mapping_binding_delta_policy_invalid", entry.sourceKind);
  }
  exactKeys(
    mapping.projectionPolicy,
    [
      "durableRowToFrameCardinality", "dropDurableRows", "fanOutDurableRows", "bindingAuthorityDelta",
      "sourceProjectionVersion", "publicSourceEventIdentity", "customRunOwnerVersion",
      "agentCandidateSourceProfile", "agentRawPassthrough", "providerPayloadPassthrough",
    ],
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
    ["wire", "agentSourceEventRefEquality", "agentSourceEventRefExposure", "webDerivation"],
    "agui_projection_policy_invalid",
  );
  exactKeys(
    mapping.projectionPolicy.customRunOwnerVersion,
    ["wire", "semantic", "legacyProjectionVersion", "javascriptNumber"],
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
    mapping.projectionPolicy.publicSourceEventIdentity.agentSourceEventRefEquality !== "forbidden" ||
    mapping.projectionPolicy.publicSourceEventIdentity.agentSourceEventRefExposure !== "private-provenance-only" ||
    mapping.projectionPolicy.publicSourceEventIdentity.webDerivation !== "forbidden" ||
    mapping.projectionPolicy.customRunOwnerVersion.wire !== "positive-uint64-decimal-string" ||
    mapping.projectionPolicy.customRunOwnerVersion.semantic !== "run-owner-version" ||
    mapping.projectionPolicy.customRunOwnerVersion.legacyProjectionVersion !== "forbidden" ||
    mapping.projectionPolicy.customRunOwnerVersion.javascriptNumber !== "forbidden"
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

function validatePublicSourceEventId(value) {
  if (
    typeof value !== "string" || value.length > 128 || !PUBLIC_SOURCE_EVENT_ID.test(value) ||
    value.includes("agent.event")
  ) {
    fail("agui_public_source_event_id_invalid", String(value));
  }
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

function bindingTimestampWatermark(runBindings, messageBindings) {
  let watermark = Number.NEGATIVE_INFINITY;
  for (const binding of [...runBindings, ...messageBindings]) {
    for (const field of ["openedAt", "terminalAt", "endedAt"]) {
      if (binding?.[field] === null || binding?.[field] === undefined) continue;
      const parsed = parseCanonicalUtcMs(binding[field], "agui_snapshot_binding_time_invalid");
      watermark = Math.max(watermark, parsed);
    }
  }
  return watermark;
}

function snapshotBindingEvidenceCount(runBindings, messageBindings) {
  const evidence = new Set();
  for (const binding of runBindings) {
    evidence.add(binding.openedBySourceEventId);
    if (binding.terminalSourceEventId !== null) evidence.add(binding.terminalSourceEventId);
  }
  for (const binding of messageBindings) {
    evidence.add(binding.openedBySourceEventId);
    if (binding.endedBySourceEventId !== null) evidence.add(binding.endedBySourceEventId);
  }
  return BigInt(evidence.size);
}

function validateSnapshotTimeAuthority(snapshot, validateSchema, runBindings = [], messageBindings = [], nextEventRecordedAt = undefined) {
  if (snapshot?.authority !== "session-browser-v3-http-snapshot" || snapshot.hydrate !== true || snapshot.repair !== true) {
    fail("agui_snapshot_authority_invalid");
  }
  if (snapshot.profileRevision !== PROFILE_REVISION) fail("agui_snapshot_profile_invalid");
  const durableSeq = uint64(snapshot?.durableSeq, "agui_snapshot_cursor_invalid");
  if ((durableSeq === 0n && snapshot?.lastRecordedAt !== null) || (durableSeq > 0n && snapshot?.lastRecordedAt === null)) {
    fail("agui_snapshot_time_watermark_invalid");
  }
  const watermark = durableSeq === 0n ? Number.NEGATIVE_INFINITY : parseCanonicalUtcMs(snapshot.lastRecordedAt);
  const outerAuthority = { ...snapshot, runBindings: [], messageBindings: [] };
  if (!validateSchema(outerAuthority)) fail("agui_snapshot_authority_schema_invalid", validateSchema.errors?.[0]?.instancePath ?? "");
  if (durableSeq > 0n && watermark < bindingTimestampWatermark(runBindings, messageBindings)) {
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

function validateRunBindings(bindings, validateSchema, snapshot, identities) {
  if (!Array.isArray(bindings) || bindings.length === 0 || bindings.length > 256) fail("agui_run_bindings_invalid");
  const refs = new Map();
  const presentationIds = new Map();
  for (const binding of bindings) {
    if (!validateSchema(binding)) fail("agui_run_binding_schema_invalid", validateSchema.errors?.[0]?.instancePath ?? "");
    if (binding.sessionId !== snapshot.sessionId || binding.profileRevision !== snapshot.profileRevision) fail("agui_run_binding_scope_conflict", binding.bindingRef);
    if (refs.has(binding.bindingRef) || presentationIds.has(binding.presentationRunId)) fail("agui_run_binding_duplicate");
    registerGlobalIdentity(identities.runBindingRefs, binding.bindingRef, "agui_global_run_binding_ref_duplicate");
    registerGlobalIdentity(identities.presentationRunIds, binding.presentationRunId, "agui_global_presentation_run_id_duplicate");
    refs.set(binding.bindingRef, binding);
    presentationIds.set(binding.presentationRunId, binding);
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
  const durableSeq = uint64(snapshot.durableSeq, "agui_snapshot_cursor_invalid");
  if (durableSeq === 0n && (runBindings.length !== 0 || messageBindings.length !== 0)) {
    fail("agui_snapshot_zero_head_bindings_invalid");
  }
  if (snapshotBindingEvidenceCount(runBindings, messageBindings) > durableSeq) {
    fail("agui_snapshot_binding_evidence_exceeds_head");
  }
  bindingTimestampWatermark(runBindings, messageBindings);
  if (runBindings.length === 0) return;
  const identities = createSemanticIdentityRegistries();
  const runRefs = validateRunBindings(runBindings, contracts.validateRunBinding, snapshot, identities);
  validateMessageBindings(messageBindings, contracts.validateMessageBinding, runRefs, snapshot, identities);
  if (new Set(runBindings.map(({ presentationThreadId }) => presentationThreadId)).size !== 1) {
    fail("agui_snapshot_thread_scope_invalid");
  }
  validateM0RunBindingStates(runBindings, "agui_snapshot_terminal_state_invalid");
}

function validateMessageBindings(bindings, validateSchema, runRefs, snapshot, identities) {
  if (!Array.isArray(bindings) || bindings.length > 512) fail("agui_message_bindings_invalid");
  const refs = new Map();
  const ids = new Set();
  for (const binding of bindings) {
    if (!validateSchema(binding)) fail("agui_message_binding_schema_invalid", validateSchema.errors?.[0]?.instancePath ?? "");
    if (binding.sessionId !== snapshot.sessionId || binding.profileRevision !== snapshot.profileRevision) fail("agui_message_binding_scope_conflict", binding.bindingRef);
    if (refs.has(binding.bindingRef) || ids.has(binding.presentationMessageId)) fail("agui_message_binding_duplicate");
    const run = runRefs.get(binding.presentationRunBindingRef);
    if (run === undefined || run.sessionId !== binding.sessionId || run.segmentOrdinal !== binding.resumeSegmentOrdinal) fail("agui_message_run_binding_invalid", binding.bindingRef);
    registerGlobalIdentity(identities.messageBindingRefs, binding.bindingRef, "agui_global_message_binding_ref_duplicate");
    registerGlobalIdentity(identities.presentationMessageIds, binding.presentationMessageId, "agui_global_presentation_message_id_duplicate");
    if (Date.parse(binding.openedAt) > Date.parse(binding.endedAt ?? binding.openedAt)) fail("agui_message_binding_time_invalid", binding.bindingRef);
    refs.set(binding.bindingRef, binding);
    ids.add(binding.presentationMessageId);
  }
  return refs;
}

function validatePrivateRouteId(value, code) {
  if (typeof value !== "string" || value.length > 128 || !/^[A-Za-z0-9][A-Za-z0-9._:-]*$/u.test(value)) {
    fail(code);
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
  );
  validateSnapshotBindingAuthority(rebuilt, contracts);
}

function validateBindingForFrame(frame, runRefs, messageRefs, snapshot) {
  const event = frame.data.event;
  const runRef = frame.data.presentationRunBindingRef;
  const messageRef = frame.data.presentationMessageBindingRef;
  if ([EventType.RUN_STARTED, EventType.RUN_FINISHED, EventType.RUN_ERROR].includes(event.type)) {
    if (!runRefs.has(runRef) || messageRef !== undefined) fail("agui_frame_run_binding_invalid", frame.data.source.sourceEventId);
  }
  if ([EventType.TEXT_MESSAGE_START, EventType.TEXT_MESSAGE_CONTENT, EventType.TEXT_MESSAGE_END, EventType.ACTIVITY_SNAPSHOT].includes(event.type)) {
    const message = messageRefs.get(messageRef);
    const run = runRefs.get(runRef);
    if (message === undefined || run === undefined || message.presentationRunBindingRef !== runRef || message.presentationMessageId !== event.messageId) fail("agui_frame_message_binding_invalid", frame.data.source.sourceEventId);
  }
  if (event.type === EventType.CUSTOM) {
    if (event.name === "kokoro.session.replace.v1" && (event.value.sessionId !== snapshot.sessionId || event.value.profileRevision !== snapshot.profileRevision)) fail("agui_custom_session_scope_conflict");
    if (event.name === "kokoro.message.replace.v1" && (!messageRefs.has(messageRef) || !runRefs.has(runRef))) fail("agui_frame_message_binding_invalid");
    if (["kokoro.run.replace.v1", "kokoro.control.replace.v1", "kokoro.receipt.replace.v1"].includes(event.name) && !runRefs.has(runRef)) fail("agui_frame_run_binding_invalid");
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
    if (referencedRun !== undefined && runState.get(referencedRun.presentationRunId) === "terminal") fail("agui_terminal_run_revived", referencedRun.presentationRunId);
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
  for (const frame of caseInput.frames) validatePublicSourceEventId(frame?.data?.source?.sourceEventId);
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
  };

  const previousRecordedAtAuthority = validateSnapshotTimeAuthority(
    snapshotAuthority,
    validateSnapshotAuthoritySchema,
    snapshotAuthority.runBindings,
    snapshotAuthority.messageBindings,
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
  validateSessionPrivateRouteFixtures(caseInput, runRefs, messageRefs, identities);
  if (browserInternalKey(caseInput.expectedFinalSnapshot)) fail("agui_browser_internal_route_forbidden", caseInput.id);
  if (!validateSnapshotAuthoritySchema(snapshotAuthority)) {
    fail("agui_snapshot_authority_schema_invalid", validateSnapshotAuthoritySchema.errors?.[0]?.instancePath ?? "");
  }
  const bindingAuthority = {
    runRefs: new Map(snapshotAuthority.runBindings.map((binding) => [binding.bindingRef, structuredClone(binding)])),
    messageRefs: new Map(snapshotAuthority.messageBindings.map((binding) => [binding.bindingRef, structuredClone(binding)])),
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
    if (browserInternalKey(frame.data)) fail("agui_browser_internal_route_forbidden", frame.data.source?.sourceEventId ?? "unknown");
    if (frame.event !== event.type) fail("agui_sse_event_type_mismatch", String(frame.event));
    const source = frame.data.source;
    validatePublicSourceEventId(source.sourceEventId);
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
    if (!EventSchemas.safeParse(event).success) fail("agui_official_event_schema_invalid", event.type);
    if (!validateStream(frame)) fail("agui_stream_schema_invalid", validateStream.errors?.[0]?.instancePath ?? "");
    validateBindingForFrame(frame, bindingAuthority.runRefs, bindingAuthority.messageRefs, caseInput.snapshot);
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
  const { agentCandidateProfile, validateAgentCandidate } = contracts;
  validateAgentCandidateProfile(agentCandidateProfile);
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
        event.type !== EventType.ACTIVITY_SNAPSHOT || agentCandidateProfile.allowedActivityTypes.includes(event.activityType)
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
    if (messageRoute === undefined ? Object.hasOwn(source.route, "internalMessageRef") : source.route.internalMessageRef !== messageRoute.internalMessageRef) {
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
    if (messageRoute === undefined ? Object.hasOwn(source.route, "internalMessageRef") : source.route.internalMessageRef !== messageRoute.internalMessageRef) {
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
    if ([EventType.TEXT_MESSAGE_START, EventType.TEXT_MESSAGE_CONTENT, EventType.TEXT_MESSAGE_END, EventType.ACTIVITY_SNAPSHOT].includes(projected.type)) {
      projected.messageId = messageBinding.presentationMessageId;
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

function validateAgentCandidateSemanticCoverage(corpus, profile) {
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
  if (
    eventCounts.get(EventType.ACTIVITY_SNAPSHOT) !== profile.allowedActivityTypes.length ||
    observedActivities.length !== profile.allowedActivityTypes.length ||
    observedActivities.some((activityType) => !profile.allowedActivityTypes.includes(activityType)) ||
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
    snapshot.runBindings[1].presentationThreadId = "thread.session.other";
    return authorityCase;
  }
  if (mutation?.operation === "parent-lineage-cycle") {
    snapshot.runBindings[0].parentLineage = {
      parentPresentationRunId: snapshot.runBindings[1].presentationRunId,
    };
    return authorityCase;
  }
  if (mutation?.operation === "m0-interrupted-terminal") {
    snapshot.runBindings[0].terminalDisposition = "interrupted";
    return authorityCase;
  }
  fail("agui_snapshot_authority_mutation_invalid");
}

function validateSnapshotAuthorityCase(authorityCase, corpus, contracts) {
  exactKeys(authorityCase, ["id", "baseCaseId", "snapshot", "nextEventRecordedAt"], "agui_snapshot_authority_case_shape_invalid");
  const base = corpus.positiveCases.find(({ id }) => id === authorityCase.baseCaseId);
  if (base === undefined || authorityCase.snapshot.sessionId !== base.snapshot.sessionId) {
    fail("agui_snapshot_authority_case_base_invalid", authorityCase.id);
  }
  const watermark = validateSnapshotTimeAuthority(
    authorityCase.snapshot,
    contracts.validateSnapshotAuthoritySchema,
    authorityCase.snapshot.runBindings,
    authorityCase.snapshot.messageBindings,
    authorityCase.nextEventRecordedAt,
  );
  if (!contracts.validateSnapshotAuthoritySchema(authorityCase.snapshot)) {
    fail("agui_snapshot_authority_schema_invalid", contracts.validateSnapshotAuthoritySchema.errors?.[0]?.instancePath ?? "");
  }
  validateSnapshotBindingAuthority(authorityCase.snapshot, contracts);
  if (watermark === Number.NEGATIVE_INFINITY) fail("agui_snapshot_authority_case_nonzero_required", authorityCase.id);
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
  validateAgentCandidateSemanticCoverage(corpus, contracts.agentCandidateProfile);
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
  process.stdout.write(`agui_presentation_ok: ${result.positiveCases} positive, ${result.negativeCases} negative, ${result.durableFrames} durable frames, ${result.bindingReplacementDeltas} binding replacements, ${result.mappingsCovered} closed mappings, ${result.agentCandidates} Agent candidate events, ${result.agentSourceFixtures} Agent source fixtures, ${result.agentCandidateEnvelopeCases} Agent envelopes, ${result.agentCandidateProjectionCases} Agent projection cases, ${result.snapshotAuthorityCases} snapshot authority cases, ${result.snapshotAuthorityNegativeCases} snapshot authority attacks\n`);
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
