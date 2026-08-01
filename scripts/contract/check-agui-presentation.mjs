#!/usr/bin/env node

import { readFile, readFileSync } from "node:fs";
import { resolve, sep } from "node:path";
import { pathToFileURL } from "node:url";

import Ajv2020 from "../../contract/node_modules/ajv/dist/2020.js";

const repositoryRoot = resolve(import.meta.dirname, "../..");
const DEFAULT_CORPUS = "contract/corpus/agui-presentation-v1.json";
const PROFILE_REVISION = "kokoro-agui-presentation.v1";
const CURSOR_PROFILE_REVISION = "opaque-session-cursor-v1";
const SESSION_CONTRACT_REVISION = "session-agui-stream.v1";
const OFFICIAL_EVENT_TYPES = [
  "TEXT_MESSAGE_START", "TEXT_MESSAGE_CONTENT", "TEXT_MESSAGE_END", "TEXT_MESSAGE_CHUNK",
  "TOOL_CALL_START", "TOOL_CALL_ARGS", "TOOL_CALL_END", "TOOL_CALL_CHUNK", "TOOL_CALL_RESULT",
  "THINKING_START", "THINKING_END", "THINKING_TEXT_MESSAGE_START", "THINKING_TEXT_MESSAGE_CONTENT", "THINKING_TEXT_MESSAGE_END",
  "STATE_SNAPSHOT", "STATE_DELTA", "MESSAGES_SNAPSHOT", "ACTIVITY_SNAPSHOT", "ACTIVITY_DELTA", "RAW", "CUSTOM",
  "RUN_STARTED", "RUN_FINISHED", "RUN_ERROR", "STEP_STARTED", "STEP_FINISHED", "REASONING_START",
  "REASONING_MESSAGE_START", "REASONING_MESSAGE_CONTENT", "REASONING_MESSAGE_END", "REASONING_MESSAGE_CHUNK",
  "REASONING_END", "REASONING_ENCRYPTED_VALUE",
];
const ALLOWED_EVENT_TYPES = [
  "RUN_STARTED", "RUN_FINISHED", "RUN_ERROR", "TEXT_MESSAGE_START", "TEXT_MESSAGE_CONTENT",
  "TEXT_MESSAGE_END", "ACTIVITY_SNAPSHOT", "CUSTOM",
];
const EVENT_FIELDS = new Map([
  ["RUN_STARTED", ["type", "timestamp", "threadId", "runId", "parentRunId"]],
  ["RUN_FINISHED", ["type", "timestamp", "threadId", "runId"]],
  ["RUN_ERROR", ["type", "timestamp", "message", "code"]],
  ["TEXT_MESSAGE_START", ["type", "timestamp", "messageId", "role"]],
  ["TEXT_MESSAGE_CONTENT", ["type", "timestamp", "messageId", "delta"]],
  ["TEXT_MESSAGE_END", ["type", "timestamp", "messageId"]],
  ["ACTIVITY_SNAPSHOT", ["type", "timestamp", "messageId", "activityType", "content", "replace"]],
  ["CUSTOM", ["type", "timestamp", "name", "value"]],
]);
const COT_KEY = /^(?:chain[_-]?of[_-]?thought|cot|private[_-]?reasoning|hidden[_-]?reasoning|reasoning[_-]?(?:content|trace|tokens))$/iu;
const TOOL_SECRET_KEY = /^(?:api[_-]?key|authorization|credential|headers?|password|private[_-]?key|provider[_-]?url|raw[_-]?(?:input|output|result)|secret|token|args|arguments|input)$/iu;
const UINT64_MAXIMUM = 18_446_744_073_709_551_615n;

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

function safePath(root, relativePath) {
  if (typeof relativePath !== "string" || relativePath.startsWith("/") || relativePath.includes("\\")) {
    fail("agui_contract_path_invalid");
  }
  const path = resolve(root, relativePath);
  if (path !== root && !path.startsWith(`${root}${sep}`)) fail("agui_contract_path_invalid");
  return path;
}

function readJsonSync(root, relativePath, code) {
  try {
    return JSON.parse(readFileSync(safePath(root, relativePath), "utf8"));
  } catch (error) {
    if (error instanceof AguiPresentationContractError) throw error;
    fail(code, relativePath);
  }
}

function loadContracts(paths, root = repositoryRoot) {
  exactKeys(paths, ["profile", "mapping", "eventSchema", "presentationRowSchema", "runBindingSchema", "messageBindingSchema", "streamSchema"], "agui_contract_paths_invalid");
  const profile = readJsonSync(root, paths.profile, "agui_profile_unreadable");
  const mapping = readJsonSync(root, paths.mapping, "agui_mapping_unreadable");
  const eventSchema = readJsonSync(root, paths.eventSchema, "agui_event_schema_unreadable");
  const presentationRowSchema = readJsonSync(root, paths.presentationRowSchema, "agui_presentation_row_schema_unreadable");
  const runBindingSchema = readJsonSync(root, paths.runBindingSchema, "agui_run_binding_schema_unreadable");
  const messageBindingSchema = readJsonSync(root, paths.messageBindingSchema, "agui_message_binding_schema_unreadable");
  const streamSchema = readJsonSync(root, paths.streamSchema, "agui_stream_schema_unreadable");
  const ajv = new Ajv2020({ allErrors: true, strict: true, validateFormats: false });
  try {
    ajv.addSchema(eventSchema);
    ajv.addSchema(presentationRowSchema);
    return {
      profile,
      mapping,
      validateEvent: ajv.getSchema(eventSchema.$id),
      validatePresentationRow: ajv.getSchema(presentationRowSchema.$id),
      validateRunBinding: ajv.compile(runBindingSchema),
      validateMessageBinding: ajv.compile(messageBindingSchema),
      validateStream: ajv.compile(streamSchema),
    };
  } catch (error) {
    fail("agui_schema_compile_invalid", error instanceof Error ? error.message : "unknown");
  }
}

function validateProfile(profile) {
  exactKeys(profile, ["profileId", "profileRevision", "lifecycle", "upstream", "typescript", "python", "rendering", "ownership", "upgradePolicy"], "agui_profile_shape_invalid");
  if (profile.profileId !== "kokoro.agui.presentation-profile.v1" || profile.profileRevision !== PROFILE_REVISION || profile.lifecycle !== "contract-only") fail("agui_profile_identity_invalid");
  if (profile.upstream?.repository !== "https://github.com/ag-ui-protocol/ag-ui" || profile.upstream?.commit !== "54f13419055b4d0f442c71e1efab18b310982ce1") fail("agui_upstream_pin_invalid");
  if (
    profile.typescript?.core?.package !== "@ag-ui/core" || profile.typescript.core.version !== "0.0.57" ||
    profile.typescript.core.integrity !== "sha512-gho1OWjNE6E3Rl7ZEZ1wr2CEpUHjLFU0FqzCZZk439TicLu+BfLCMkMokB07bMGlRmbJ60hM6LW60iOVauCx+Q==" ||
    profile.typescript.core.participant !== true
  ) fail("agui_core_pin_invalid");
  if (profile.typescript?.client?.package !== "@ag-ui/client" || profile.typescript.client.version !== "0.0.57" || profile.typescript.client.participant !== false) fail("agui_client_participation_invalid");
  if (profile.python?.package !== "ag-ui-protocol" || profile.python.versionAtCommit !== "0.1.19" || profile.python.participant !== false) fail("agui_python_participation_invalid");
  if (profile.rendering?.assistantUi?.package !== "@assistant-ui/react" || profile.rendering.assistantUi.version !== "0.14.28" || profile.rendering.assistantUi.role !== "rendering-adapter-only") fail("agui_rendering_pin_invalid");
  if (profile.ownership?.durableTruth !== "kokoro-session" || profile.ownership.projectionOwner !== "kokoro-session" || profile.ownership.agentParticipant !== false) fail("agui_owner_invalid");
  if (!Object.values(profile.upgradePolicy ?? {}).every((value) => value === true)) fail("agui_upgrade_policy_invalid");
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
    exactKeys(entry, entry.discriminator === undefined ? ["sourceKind", "eventType"] : ["sourceKind", "eventType", "discriminator"], "agui_mapping_entry_shape_invalid");
    if (sourceKinds.has(entry.sourceKind)) fail("agui_mapping_source_duplicate", entry.sourceKind);
    sourceKinds.add(entry.sourceKind);
    if (!ALLOWED_EVENT_TYPES.includes(entry.eventType)) fail("agui_mapping_event_forbidden", entry.sourceKind);
    if (entry.eventType === "ACTIVITY_SNAPSHOT" && !mapping.allowedActivityTypes.includes(entry.discriminator)) fail("agui_mapping_activity_unknown", entry.sourceKind);
    if (entry.eventType === "CUSTOM" && !mapping.allowedCustomNames.includes(entry.discriminator)) fail("agui_mapping_custom_unknown", entry.sourceKind);
    if (!['ACTIVITY_SNAPSHOT', 'CUSTOM'].includes(entry.eventType) && entry.discriminator !== undefined) fail("agui_mapping_discriminator_invalid", entry.sourceKind);
  }
  if (mapping.projectionPolicy?.durableRowToFrameCardinality !== "exactly-one" || mapping.projectionPolicy.dropDurableRows !== false || mapping.projectionPolicy.fanOutDurableRows !== false || mapping.projectionPolicy.agentRawEventParticipant !== false || mapping.projectionPolicy.providerPayloadParticipant !== false) fail("agui_projection_policy_invalid");
  if (
    mapping.transportPolicy?.sseId !== "opaque-session-cursor" || mapping.transportPolicy.sseEvent !== "exact-inner-event-type" ||
    mapping.transportPolicy.resumeHeader !== "Last-Event-ID" || mapping.transportPolicy.drainingDurability !== "non-durable" ||
    mapping.transportPolicy.stockAguiClientTransport !== "forbidden"
  ) fail("agui_transport_policy_invalid");
  exactArray(mapping.transportPolicy.cursorBindingFields, ["sessionId", "streamEpoch", "durableSeq", "profileRevision", "cursorProfileRevision"], "agui_cursor_binding_policy_invalid");
  exactArray(mapping.transportPolicy.grantBindingFields, ["sessionId", "sessionContractRevision", "presentationProfileRevision", "cursorProfileRevision"], "agui_grant_binding_policy_invalid");
  if (mapping.snapshotPolicy?.hydrateAuthority !== "session-browser-v3-http-snapshot" || mapping.snapshotPolicy.repairAuthority !== "session-browser-v3-http-snapshot" || mapping.snapshotPolicy.streamHydration !== "forbidden") fail("agui_snapshot_policy_invalid");
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
  if (event.type === "CUSTOM" && !mapping.allowedCustomNames.includes(event.name)) fail("agui_unknown_custom", String(event.name));
  if (event.type === "ACTIVITY_SNAPSHOT" && !mapping.allowedActivityTypes.includes(event.activityType)) fail("agui_unknown_activity", String(event.activityType));
  if (event.type === "ACTIVITY_SNAPSHOT" && event.activityType === "kokoro.tool-preview.v1" && findKey(event.content, TOOL_SECRET_KEY)) fail("agui_tool_secret_forbidden");
  const allowedFields = EVENT_FIELDS.get(event.type) ?? [];
  const extra = Object.keys(event).find((key) => !allowedFields.includes(key));
  if (extra !== undefined) fail("agui_event_extra_forbidden", extra);
}

function validateRunBindings(bindings, validateSchema) {
  if (!Array.isArray(bindings) || bindings.length === 0 || bindings.length > 256) fail("agui_run_bindings_invalid");
  const refs = new Map();
  const ids = new Set();
  const groups = new Map();
  for (const binding of bindings) {
    if (!validateSchema(binding)) fail("agui_run_binding_schema_invalid", validateSchema.errors?.[0]?.instancePath ?? "");
    if (refs.has(binding.bindingRef) || ids.has(binding.presentationRunId)) fail("agui_run_binding_duplicate");
    refs.set(binding.bindingRef, binding);
    ids.add(binding.presentationRunId);
    const group = groups.get(binding.internalRunRef) ?? [];
    group.push(binding);
    groups.set(binding.internalRunRef, group);
    if (Date.parse(binding.openedAt) > Date.parse(binding.terminalAt ?? binding.openedAt)) fail("agui_run_binding_time_invalid", binding.bindingRef);
  }
  for (const group of groups.values()) {
    group.sort((left, right) => left.segmentOrdinal - right.segmentOrdinal);
    for (let index = 0; index < group.length; index += 1) {
      const binding = group[index];
      if (binding.segmentOrdinal !== index) fail("agui_resume_segment_gap", binding.bindingRef);
      const previous = group[index - 1];
      if (index === 0 && binding.resumeOfPresentationRunId !== null) fail("agui_resume_parent_confused", binding.bindingRef);
      if (index > 0 && binding.resumeOfPresentationRunId !== previous.presentationRunId) fail("agui_resume_parent_confused", binding.bindingRef);
      if (binding.parentLineage.parentPresentationRunId === binding.resumeOfPresentationRunId && binding.resumeOfPresentationRunId !== null) fail("agui_resume_parent_confused", binding.bindingRef);
      if (index > 0 && JSON.stringify(binding.parentLineage) !== JSON.stringify(group[0].parentLineage)) fail("agui_resume_parent_confused", binding.bindingRef);
      if (index > 0 && (binding.presentationThreadId !== group[0].presentationThreadId || binding.sessionId !== group[0].sessionId)) fail("agui_resume_scope_conflict", binding.bindingRef);
    }
  }
  return refs;
}

function validateMessageBindings(bindings, validateSchema, runRefs) {
  if (!Array.isArray(bindings) || bindings.length > 512) fail("agui_message_bindings_invalid");
  const refs = new Map();
  const ids = new Set();
  const internalSegments = new Set();
  for (const binding of bindings) {
    if (!validateSchema(binding)) fail("agui_message_binding_schema_invalid", validateSchema.errors?.[0]?.instancePath ?? "");
    if (refs.has(binding.bindingRef) || ids.has(binding.presentationMessageId)) fail("agui_message_binding_duplicate");
    const run = runRefs.get(binding.presentationRunBindingRef);
    if (run === undefined || run.sessionId !== binding.sessionId || run.segmentOrdinal !== binding.resumeSegmentOrdinal) fail("agui_message_run_binding_invalid", binding.bindingRef);
    const segmentKey = `${binding.internalMessageRef}\u0000${binding.resumeSegmentOrdinal}`;
    if (internalSegments.has(segmentKey)) fail("agui_message_segment_duplicate", binding.bindingRef);
    internalSegments.add(segmentKey);
    if ([...refs.values()].some((other) => other.internalMessageRef === binding.internalMessageRef && other.presentationMessageId === binding.presentationMessageId)) fail("agui_message_resume_id_reused", binding.bindingRef);
    if (Date.parse(binding.openedAt) > Date.parse(binding.endedAt ?? binding.openedAt)) fail("agui_message_binding_time_invalid", binding.bindingRef);
    refs.set(binding.bindingRef, binding);
    ids.add(binding.presentationMessageId);
  }
  return refs;
}

function mappingFor(mapping, sourceKind) {
  return mapping.mappings.find((entry) => entry.sourceKind === sourceKind);
}

function validateBindingForFrame(frame, runRefs, messageRefs) {
  const event = frame.data.event;
  const runRef = frame.data.presentationRunBindingRef;
  const messageRef = frame.data.presentationMessageBindingRef;
  if (["RUN_STARTED", "RUN_FINISHED", "RUN_ERROR"].includes(event.type)) {
    if (!runRefs.has(runRef) || messageRef !== undefined) fail("agui_frame_run_binding_invalid", frame.data.source.sourceEventId);
  }
  if (["TEXT_MESSAGE_START", "TEXT_MESSAGE_CONTENT", "TEXT_MESSAGE_END", "ACTIVITY_SNAPSHOT"].includes(event.type)) {
    const message = messageRefs.get(messageRef);
    const run = runRefs.get(runRef);
    if (message === undefined || run === undefined || message.presentationRunBindingRef !== runRef || message.presentationMessageId !== event.messageId) fail("agui_frame_message_binding_invalid", frame.data.source.sourceEventId);
  }
  if (event.type === "CUSTOM") {
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
    if (["TEXT_MESSAGE_START", "TEXT_MESSAGE_CONTENT", "TEXT_MESSAGE_END"].includes(event.type)) {
      const state = messageState.get(event.messageId);
      const binding = messageRefs.get(frame.data.presentationMessageBindingRef);
      if (event.type === "TEXT_MESSAGE_START") {
        if (state !== undefined) fail("agui_message_reopened", event.messageId);
        if (binding.openedBySourceEventId !== sourceId) fail("agui_message_open_source_conflict", event.messageId);
        messageState.set(event.messageId, "open");
      } else if (event.type === "TEXT_MESSAGE_CONTENT") {
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
    if (referencedRun !== undefined && runState.get(referencedRun.presentationRunId) === "terminal") {
      fail("agui_terminal_run_revived", referencedRun.presentationRunId);
    }
    if (event.type === "RUN_STARTED") {
      const binding = runRefs.get(frame.data.presentationRunBindingRef);
      if (runState.has(binding.presentationRunId)) fail("agui_terminal_run_revived", binding.presentationRunId);
      if (binding.openedBySourceEventId !== sourceId || event.runId !== binding.presentationRunId || event.threadId !== binding.presentationThreadId) fail("agui_run_start_binding_conflict", binding.bindingRef);
      const parent = binding.parentLineage.parentPresentationRunId;
      if ((event.parentRunId ?? null) !== parent) fail("agui_run_parent_lineage_conflict", binding.bindingRef);
      runState.set(binding.presentationRunId, "open");
      continue;
    }
    if (["RUN_FINISHED", "RUN_ERROR"].includes(event.type)) {
      const binding = runRefs.get(frame.data.presentationRunBindingRef);
      if (runState.get(binding.presentationRunId) !== "open") fail("agui_terminal_run_revived", binding.presentationRunId);
      if (binding.terminalSourceEventId !== sourceId || (event.type === "RUN_FINISHED" ? binding.state !== "finished" : binding.state !== "error")) fail("agui_run_terminal_binding_conflict", binding.bindingRef);
      if (event.type === "RUN_FINISHED" && (event.runId !== binding.presentationRunId || event.threadId !== binding.presentationThreadId)) fail("agui_run_terminal_binding_conflict", binding.bindingRef);
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

export function validateConformanceCase(caseInput, contractPaths, options = {}) {
  const root = options.root ?? repositoryRoot;
  const contracts = options.loadedContracts ?? loadContracts(contractPaths, root);
  const { mapping, validateEvent, validatePresentationRow, validateRunBinding, validateMessageBinding, validateStream } = contracts;
  if (caseInput?.snapshot?.authority !== "session-browser-v3-http-snapshot" || caseInput.snapshot.hydrate !== true || caseInput.snapshot.repair !== true) fail("agui_snapshot_authority_invalid");
  if (caseInput.snapshot.profileRevision !== PROFILE_REVISION) fail("agui_snapshot_profile_invalid");
  if (caseInput.request?.lastEventId !== caseInput.snapshot.cursor || caseInput.request?.queryCursor !== caseInput.snapshot.cursor || caseInput.request?.cursorProfile !== CURSOR_PROFILE_REVISION) fail("agui_resume_cursor_invalid");
  if (
    caseInput.grantBinding?.sessionId !== caseInput.snapshot.sessionId ||
    caseInput.grantBinding?.sessionContractRevision !== SESSION_CONTRACT_REVISION ||
    caseInput.grantBinding?.presentationProfileRevision !== PROFILE_REVISION ||
    caseInput.grantBinding?.cursorProfileRevision !== CURSOR_PROFILE_REVISION
  ) fail("agui_grant_profile_binding_invalid");
  const runRefs = validateRunBindings(caseInput.runBindings, validateRunBinding);
  const messageRefs = validateMessageBindings(caseInput.messageBindings, validateMessageBinding, runRefs);
  if (!Array.isArray(caseInput.frames) || !Array.isArray(caseInput.durableRows) || caseInput.frames.length !== caseInput.durableRows.length || caseInput.frames.length === 0) fail("agui_durable_frame_cardinality_invalid");
  const cursorIds = new Set();
  const sourceIds = new Set();
  let expectedSeq = uint64(caseInput.snapshot.durableSeq, "agui_snapshot_cursor_invalid") + 1n;
  uint64(caseInput.snapshot.streamEpoch, "agui_snapshot_cursor_invalid");
  let previousRecordedAt = Date.parse(caseInput.snapshot.recordedAt ?? "1970-01-01T00:00:00.000Z");
  for (let index = 0; index < caseInput.frames.length; index += 1) {
    const frame = caseInput.frames[index];
    const event = frame?.data?.event;
    validateEventPreSchema(event, mapping);
    if (frame.event !== event.type) fail("agui_sse_event_type_mismatch", String(frame.event));
    const source = frame.data.source;
    if (uint64(source.durableSeq, "agui_cursor_gap") !== expectedSeq) fail("agui_cursor_gap", source.durableSeq);
    expectedSeq += 1n;
    uint64(source.streamEpoch, "agui_stream_epoch_invalid");
    if (source.sessionId !== caseInput.snapshot.sessionId || source.streamEpoch !== caseInput.snapshot.streamEpoch || frame.data.profileRevision !== PROFILE_REVISION) fail("agui_stream_scope_conflict", source.sourceEventId);
    const recordedAt = Date.parse(source.recordedAt);
    if (!Number.isFinite(recordedAt) || recordedAt !== event.timestamp || recordedAt < previousRecordedAt) fail("agui_event_time_invalid", source.sourceEventId);
    previousRecordedAt = recordedAt;
    if (cursorIds.has(frame.id) || sourceIds.has(source.sourceEventId)) fail("agui_stream_identity_duplicate", source.sourceEventId);
    cursorIds.add(frame.id);
    sourceIds.add(source.sourceEventId);
    const row = caseInput.durableRows[index];
    if (row.sourceEventId !== source.sourceEventId || row.sourceKind !== source.sourceKind || row.durableSeq !== source.durableSeq) fail("agui_durable_frame_cardinality_invalid", source.sourceEventId);
    const mappingEntry = mappingFor(mapping, source.sourceKind);
    if (mappingEntry === undefined || mappingEntry.eventType !== event.type) fail("agui_closed_mapping_missing", source.sourceKind);
    const discriminator = event.type === "ACTIVITY_SNAPSHOT" ? event.activityType : event.type === "CUSTOM" ? event.name : undefined;
    if ((mappingEntry.discriminator ?? undefined) !== discriminator) fail("agui_mapping_discriminator_conflict", source.sourceKind);
    enforceLimits(event, mapping.limits, mapping.limits.maximumEventBytes, "agui_event_limit_exceeded");
    enforceLimits(frame, mapping.limits, mapping.limits.maximumFrameBytes, "agui_frame_limit_exceeded");
    if (!validateEvent(event)) fail("agui_event_schema_invalid", validateEvent.errors?.[0]?.instancePath ?? "");
    if (!validatePresentationRow(frame.data)) fail("agui_presentation_row_schema_invalid", validatePresentationRow.errors?.[0]?.instancePath ?? "");
    if (!validateStream(frame)) fail("agui_stream_schema_invalid", validateStream.errors?.[0]?.instancePath ?? "");
    validateBindingForFrame(frame, runRefs, messageRefs);
  }
  validateStreamState(caseInput.frames, runRefs, messageRefs);
  if (!validateStream(caseInput.controlFrame) || caseInput.controlFrame.kind !== "control" || caseInput.controlFrame.id !== null) fail("agui_draining_not_nondurable");
  const lastFrame = caseInput.frames.at(-1);
  if (caseInput.controlFrame.data.lastDurableCursor !== lastFrame.id || caseInput.controlFrame.data.sessionId !== caseInput.snapshot.sessionId || caseInput.controlFrame.data.streamEpoch !== caseInput.snapshot.streamEpoch) fail("agui_draining_cursor_conflict");
  enforceLimits(caseInput.controlFrame, mapping.limits, mapping.limits.maximumFrameBytes, "agui_frame_limit_exceeded");
  return { durableFrames: caseInput.frames.length, sourceKinds: new Set(caseInput.frames.map((frame) => frame.data.source.sourceKind)) };
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
  frame.id = `v1.cursor-key.attack-${input.kind}.${next}`;
  frame.data.source.sourceEventId = input.sourceEventId;
  frame.data.source.sourceKind = input.sourceKind;
  frame.data.source.durableSeq = next;
  frame.data.source.projectionVersion += 1;
  frame.data.source.recordedAt = input.recordedAt;
  frame.data.event.timestamp = Date.parse(input.recordedAt);
  candidate.frames.push(frame);
  candidate.durableRows.push({ sourceEventId: input.sourceEventId, sourceKind: input.sourceKind, durableSeq: next });
}

export function applyCorpusMutation(candidate, mutation) {
  if (mutation?.operation === "set") {
    setAtPath(candidate, mutation.path, structuredClone(mutation.value));
    return candidate;
  }
  if (mutation?.operation === "terminal-revival") {
    const frame = candidate.frames.find((entry) => entry.event === "RUN_STARTED" && entry.data.presentationRunBindingRef === mutation.runBindingRef);
    if (frame === undefined) fail("agui_corpus_mutation_invalid", "terminal-revival");
    appendAttackFrame(candidate, frame, { kind: "terminal-revival", sourceEventId: "attack.source.terminal-revival", sourceKind: "presentation.run.started", recordedAt: "2026-08-01T12:00:27.000Z" });
    return candidate;
  }
  if (mutation?.operation === "reopen-message") {
    const frame = candidate.frames.find((entry) => entry.event === "TEXT_MESSAGE_CONTENT" && entry.data.presentationMessageBindingRef === mutation.messageBindingRef);
    if (frame === undefined) fail("agui_corpus_mutation_invalid", "reopen-message");
    appendAttackFrame(candidate, frame, { kind: "message-reopen", sourceEventId: "attack.source.message-reopen", sourceKind: "presentation.message.text.content", recordedAt: "2026-08-01T12:00:27.000Z" });
    return candidate;
  }
  fail("agui_corpus_mutation_invalid");
}

export async function validateRepository({ root = repositoryRoot, corpusPath = DEFAULT_CORPUS } = {}) {
  const corpus = JSON.parse(await new Promise((resolvePromise, reject) => readFile(safePath(root, corpusPath), "utf8", (error, data) => error ? reject(error) : resolvePromise(data))));
  if (corpus.corpusId !== "kokoro.agui.presentation-conformance.v1" || corpus.profileRevision !== PROFILE_REVISION) fail("agui_corpus_identity_invalid");
  const contracts = loadContracts(corpus.contracts, root);
  validateProfile(contracts.profile);
  validateMappingRegistry(contracts.mapping);
  if (!Array.isArray(corpus.positiveCases) || corpus.positiveCases.length < 2 || !Array.isArray(corpus.negativeCases) || corpus.negativeCases.length < 10) fail("agui_corpus_shape_invalid");
  const caseIds = new Set();
  const covered = new Set();
  let durableFrames = 0;
  for (const contractCase of corpus.positiveCases) {
    if (caseIds.has(contractCase.id)) fail("agui_corpus_case_duplicate", contractCase.id);
    caseIds.add(contractCase.id);
    const result = validateConformanceCase(contractCase, corpus.contracts, { root, loadedContracts: contracts });
    durableFrames += result.durableFrames;
    for (const sourceKind of result.sourceKinds) covered.add(sourceKind);
  }
  const expectedMappings = new Set(contracts.mapping.mappings.map(({ sourceKind }) => sourceKind));
  if (covered.size !== expectedMappings.size || [...expectedMappings].some((sourceKind) => !covered.has(sourceKind))) fail("agui_mapping_corpus_coverage_missing");
  const negativeIds = new Set();
  for (const attack of corpus.negativeCases) {
    if (negativeIds.has(attack.id) || !caseIds.has(attack.baseCaseId)) fail("agui_negative_case_invalid", attack.id);
    negativeIds.add(attack.id);
    const base = corpus.positiveCases.find(({ id }) => id === attack.baseCaseId);
    const candidate = applyCorpusMutation(structuredClone(base), attack.mutation);
    let observed;
    try {
      validateConformanceCase(candidate, corpus.contracts, { root, loadedContracts: contracts });
    } catch (error) {
      if (error instanceof AguiPresentationContractError) observed = error.code;
      else throw error;
    }
    if (observed !== attack.expectedCode) fail("agui_negative_case_expectation_invalid", `${attack.id}:${observed ?? "accepted"}`);
  }
  return { positiveCases: corpus.positiveCases.length, negativeCases: corpus.negativeCases.length, durableFrames, mappingsCovered: covered.size };
}

async function main(argv) {
  let root = repositoryRoot;
  let corpusPath = DEFAULT_CORPUS;
  for (let index = 0; index < argv.length; index += 2) {
    const option = argv[index];
    const value = argv[index + 1];
    if (value === undefined) fail("agui_arguments_invalid");
    if (option === "--root") root = resolve(value);
    else if (option === "--corpus") corpusPath = value;
    else fail("agui_arguments_invalid", option);
  }
  const result = await validateRepository({ root, corpusPath });
  process.stdout.write(`agui_presentation_ok: ${result.positiveCases} positive, ${result.negativeCases} negative, ${result.durableFrames} durable frames, ${result.mappingsCovered} closed mappings\n`);
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
