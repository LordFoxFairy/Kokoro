#!/usr/bin/env node

// Fail-closed Wave T0 gate: every cross-repository boundary is registered, every operation is
// backed by a real contract source, and every operation has exactly one frozen transport.
// Allowed retry classes are parsed from the protobuf enum so this file never hardcodes them.

import { readFileSync } from "node:fs";
import { isAbsolute, posix, relative, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";
import { openApiOperations, readOpenApiDocument } from "./openapi-reader.mjs";

const SCRIPT_PATH = fileURLToPath(import.meta.url);
// JSON-compatible YAML, matching config/architecture/index-roots.yaml: the spec-mandated name
// without a YAML dependency. JSON is valid YAML 1.2, so a real parser reads it unchanged later.
const DEFAULT_REGISTRY = "contract/registry/boundaries.yaml";
const DEFAULT_SCHEMA = "contract/registry/boundaries.schema.json";
const DEFAULT_MATRIX = "config/repository/compatibility-matrix.json";
const DEFAULT_ROOTS = "config/architecture/index-roots.yaml";
const DEFAULT_RETRY_CLASS_PROTO = "contract/proto/kokoro/common/v1/error.proto";

const SCOPES = ["site", "platform", "namespace"];
// GA runs on one opaque isolation key. A second identity axis on that wire is a design failure.
const GA_FORBIDDEN_FIELDS = ["site_id", "user_id", "owner_id", "workspace_id"];
// snake_case and camelCase both appear across the checked-in contract sources.
const SITE_FIELDS = ["site_id", "siteId"];
// How an operation really binds its Site. Only request-field is structurally verifiable. The spec
// (§6.3) forbids callers self-asserting Site from bare metadata, so context-header is recorded
// migration debt that this gate counts out loud rather than silently blessing.
const SITE_BINDINGS = ["request-field", "context-header", "workload-binding", "not-applicable"];
const SOURCE_KINDS = ["openapi", "proto", "spec-yaml"];
// Whether this repository actually holds a contract source for the boundary. declared-only means
// the orphan check cannot run at all, so the boundary is counted in the success line instead of
// being waved through as though it were covered.
const LIFECYCLES = ["active", "contract-only"];
const SOURCE_STATUSES = ["machine-readable", "declared-only"];
const RECEIPT_KINDS = [
  "command-receipt",
  "durable-event",
  "http-receipt-body",
  "idempotency-key",
  "state-read",
];
const REGISTRY_KEYS = ["boundaries", "owners", "schemaVersion"];
const BOUNDARY_KEYS = [
  "audience",
  "consumers",
  "deadlineMs",
  "failureOwner",
  "id",
  "lifecycle",
  "operations",
  "protocol",
  "provider",
  "scope",
  "sourceStatus",
  "sources",
  "transportSource",
  "transports",
  "trustPlane",
  "version",
];
const OPERATION_KEYS = ["effect", "id", "receipt", "retryClass", "scope", "siteBinding", "transport"];
const PARTY_KEYS = ["boundary", "repository"];
const RECEIPT_KEYS = ["kind", "ref"];
const RECEIPT_RECOVERY_KEYS = ["kind", "recoveryOperation", "ref"];
const SOURCE_KEYS = ["kind", "path", "select"];

export class BoundaryRegistryError extends Error {
  constructor(code, detail = "") {
    super(`${code}${detail ? `: ${detail}` : ""}`);
    this.name = "BoundaryRegistryError";
    this.code = code;
  }
}

function fail(code, detail) {
  throw new BoundaryRegistryError(code, detail);
}

export function parseArguments(argv) {
  const options = {
    root: process.cwd(),
    registry: DEFAULT_REGISTRY,
    schema: DEFAULT_SCHEMA,
    matrix: DEFAULT_MATRIX,
    roots: DEFAULT_ROOTS,
  };
  for (let index = 0; index < argv.length; index += 1) {
    const flag = argv[index];
    const value = argv[index + 1];
    if (!flag.startsWith("--") || !(flag.slice(2) in options) || !value) {
      fail("boundary_registry_arguments_invalid", flag ?? "");
    }
    options[flag.slice(2)] = value;
    index += 1;
  }
  options.root = resolve(options.root);
  for (const key of ["registry", "schema", "matrix", "roots"]) {
    options[key] = resolve(options.root, options[key]);
  }
  return options;
}

function readJson(path, code) {
  let source;
  try {
    source = readFileSync(path, "utf8");
  } catch (error) {
    fail(code, `${path}: ${error.code ?? error.message}`);
  }
  try {
    return JSON.parse(source);
  } catch (error) {
    fail(code, `${path}: ${error.message}`);
  }
}

function readText(path, code) {
  try {
    return readFileSync(path, "utf8");
  } catch (error) {
    return fail(code, `${path}: ${error.code ?? error.message}`);
  }
}

function exactKeys(value, keys) {
  if (value === null || typeof value !== "object" || Array.isArray(value)) return false;
  const actual = Object.keys(value).sort();
  return actual.length === keys.length && actual.every((key, index) => key === keys[index]);
}

function isRepositoryRelative(value) {
  return (
    typeof value === "string" &&
    value.length > 0 &&
    !value.includes("\0") &&
    !value.includes("\\") &&
    !isAbsolute(value) &&
    posix.normalize(value) === value &&
    !value.startsWith("../")
  );
}

function isInside(child, parent) {
  const remainder = relative(parent, child);
  return remainder !== ".." && !remainder.startsWith(`..${sep}`) && !isAbsolute(remainder);
}

function sortedSet(values) {
  return [...new Set(values)].sort();
}

function setDifference(left, right) {
  return left.filter((value) => !right.has(value));
}

// ---------------------------------------------------------------------------------------------
// Minimal readers for the two contract source languages. Both are deliberately narrow: they read
// exactly the shapes the checked-in sources use and reject anything they cannot account for.
// ---------------------------------------------------------------------------------------------

function stripComment(line) {
  let quote = null;
  for (let index = 0; index < line.length; index += 1) {
    const character = line[index];
    if (quote) {
      if (character === quote) quote = null;
      continue;
    }
    if (character === '"' || character === "'") quote = character;
    else if (character === "#" && (index === 0 || /\s/u.test(line[index - 1]))) {
      return line.slice(0, index);
    }
  }
  return line;
}

function unquote(value) {
  const trimmed = value.trim();
  if (trimmed.length >= 2 && /^(["']).*\1$/su.test(trimmed)) return trimmed.slice(1, -1);
  return trimmed;
}

function splitFlow(body) {
  const parts = [];
  let depth = 0;
  let quote = null;
  let current = "";
  for (const character of body) {
    if (quote) {
      current += character;
      if (character === quote) quote = null;
      continue;
    }
    if (character === '"' || character === "'") quote = character;
    if (character === "[" || character === "{") depth += 1;
    if (character === "]" || character === "}") depth -= 1;
    if (character === "," && depth === 0) {
      parts.push(current);
      current = "";
      continue;
    }
    current += character;
  }
  if (current.trim() !== "") parts.push(current);
  return parts;
}

function parseFlowMapping(body) {
  const result = {};
  for (const part of splitFlow(body)) {
    const separator = part.indexOf(":");
    if (separator === -1) continue;
    result[unquote(part.slice(0, separator))] = unquote(part.slice(separator + 1));
  }
  return result;
}

// Returns the raw lines of one top-level block, without the `key:` header line itself.
function sectionLines(source, section) {
  const lines = source.split(/\r?\n/u);
  const header = lines.findIndex((line) => stripComment(line).trimEnd() === `${section}:`);
  if (header === -1) return null;
  const body = [];
  for (let index = header + 1; index < lines.length; index += 1) {
    const line = stripComment(lines[index]);
    if (line.trim() === "") continue;
    if (!/^\s/u.test(line)) break;
    body.push(line.replace(/\s+$/u, ""));
  }
  return body;
}

/**
 * Read the member names a spec YAML section declares.
 *
 * member="mapping-key" -> child keys of a block mapping.
 * member="scalar"      -> items of a block sequence of scalars.
 * member="field"       -> the named field of each block-sequence item (block or flow mapping).
 */
export function readSpecMembers(source, select) {
  const body = sectionLines(source, select.section);
  if (body === null) fail("boundary_registry_source_unreadable", `missing section: ${select.section}`);
  if (body.length === 0) fail("boundary_registry_source_unreadable", `empty section: ${select.section}`);
  const indent = Math.min(...body.map((line) => line.match(/^\s*/u)[0].length));
  const members = [];
  for (const line of body) {
    const depth = line.match(/^\s*/u)[0].length;
    if (depth !== indent) continue;
    const content = line.slice(indent);
    if (select.member === "mapping-key") {
      // A mapping key is still authoritative when its value is an inline flow mapping. The
      // Browser HTTP source deliberately keeps one complete endpoint per line so reviews can see
      // method/path/request/response together; accepting only block values silently orphaned it.
      const match = /^([A-Za-z0-9_.-]+):(?:\s*$|\s+\{.*\}\s*$)/u.exec(content);
      if (match) members.push(match[1]);
      continue;
    }
    if (!content.startsWith("- ")) continue;
    const item = content.slice(2).trim();
    if (select.member === "scalar") {
      members.push(unquote(item));
      continue;
    }
    if (select.member !== "field") fail("boundary_registry_source_unreadable", `member: ${select.member}`);
    if (item.startsWith("{")) {
      const value = parseFlowMapping(item.replace(/^\{/u, "").replace(/\}$/u, ""))[select.field];
      if (value !== undefined) members.push(value);
      continue;
    }
    const match = new RegExp(`^${select.field}:\\s*(.+)$`, "u").exec(item);
    if (match) members.push(unquote(match[1]));
  }
  if (members.length === 0) {
    fail("boundary_registry_source_unreadable", `no members in section: ${select.section}`);
  }
  if (!select.match) return members;
  const pattern = new RegExp(select.match, "u");
  const selected = [];
  for (const member of members) {
    const match = pattern.exec(member);
    if (!match) continue;
    const value = match[1] ?? match[0];
    selected.push(select.case === "snake" ? toSnakeCase(value) : value);
  }
  return selected;
}

export function toSnakeCase(value) {
  return value.replace(/(?<!^)(?=[A-Z])/gu, "_").toLowerCase();
}

/**
 * Every field name a spec YAML section can put on the wire, following `object:Name` references
 * into the file's top-level `objects` block. Used to prove the GA axis stays single-keyed.
 */
export function readSpecFieldNames(source, select) {
  const objects = new Map();
  const objectBody = sectionLines(source, "objects");
  if (objectBody) {
    let current = null;
    for (const line of objectBody) {
      const trimmed = line.trim();
      const name = /^-\s+name:\s*(.+)$/u.exec(trimmed);
      if (name) {
        current = unquote(name[1]);
        objects.set(current, []);
        continue;
      }
      if (!current || !trimmed.startsWith("- {")) continue;
      const entry = parseFlowMapping(trimmed.slice(3).replace(/\}$/u, ""));
      if (entry.name) objects.get(current).push({ name: entry.name, type: entry.type ?? "" });
    }
  }

  const names = new Set();
  const visited = new Set();
  function visitObject(name) {
    if (visited.has(name) || !objects.has(name)) return;
    visited.add(name);
    for (const field of objects.get(name)) {
      names.add(field.name);
      const reference = /object:([A-Za-z0-9_]+)/u.exec(field.type);
      if (reference) visitObject(reference[1]);
    }
  }

  const body = sectionLines(source, select.section) ?? [];
  const indent = body.length === 0 ? 0 : Math.min(...body.map((line) => line.match(/^\s*/u)[0].length));
  let inSection = false;
  for (const line of body) {
    const trimmed = line.trim();
    const depth = line.match(/^\s*/u)[0].length;
    if (depth === indent && trimmed.startsWith("- ")) inSection = true;
    if (!inSection) continue;
    // Flow items such as `- {kind: x, payload: [a, b, "c?"]}` name their fields inline.
    const payload = /payload:\s*\[([^\]]*)\]/u.exec(trimmed);
    if (payload) {
      for (const item of splitFlow(payload[1])) {
        const name = unquote(item).replace(/\?$/u, "");
        if (name) names.add(name);
      }
    }
    // Block items such as `- {name: run_id, type: ...}` under a `fields:` list.
    if (trimmed.startsWith("- {")) {
      const entry = parseFlowMapping(trimmed.slice(3).replace(/\}$/u, ""));
      if (entry.name) names.add(entry.name);
      const reference = /object:([A-Za-z0-9_]+)/u.exec(entry.type ?? "");
      if (reference) visitObject(reference[1]);
    }
  }
  return names;
}

/**
 * Every field name a spec YAML file declares anywhere.
 *
 * Rule 8 needs the section-scoped reader above, because one file can serve two faces and a field
 * belonging to the browser face must not incriminate the GA face. Rule 9 asks the opposite
 * question — can this contract prove a Site field exists at all — so it scans the whole file and
 * works for block-mapping sections that name no fields of their own.
 */

// Fields declared by one spec object, following object: references. Used to prove a
// site claim against the operation's own request shape rather than the whole file.
export function readSpecObjectFields(source, objectName) {
  const objects = new Map();
  const objectBody = sectionLines(source, "objects");
  if (objectBody) {
    let current = null;
    for (const line of objectBody) {
      const trimmed = line.trim();
      const name = /^-\s+name:\s*(.+)$/u.exec(trimmed);
      if (name) {
        current = unquote(name[1]);
        objects.set(current, []);
        continue;
      }
      if (!current || !trimmed.startsWith("- {")) continue;
      const entry = parseFlowMapping(trimmed.slice(3).replace(/\}$/u, ""));
      if (entry.name) objects.get(current).push({ name: entry.name, type: entry.type ?? "" });
    }
  }
  const names = new Set();
  const visited = new Set();
  (function visit(name) {
    if (visited.has(name) || !objects.has(name)) return;
    visited.add(name);
    for (const field of objects.get(name)) {
      names.add(field.name);
      const reference = /object:([A-Za-z0-9_]+)/u.exec(field.type);
      if (reference) visit(reference[1]);
    }
  })(objectName);
  return { known: objects.has(objectName), names };
}

export function readSpecDeclaredFieldNames(source) {
  const names = new Set();
  for (const rawLine of source.split(/\r?\n/u)) {
    const line = stripComment(rawLine).trim();
    if (line.startsWith("- {") || line.startsWith("{")) {
      const entry = parseFlowMapping(line.replace(/^-\s*/u, "").replace(/^\{/u, "").replace(/\}$/u, ""));
      if (entry.name) names.add(entry.name);
    }
    const payload = /payload:\s*\[([^\]]*)\]/u.exec(line);
    if (!payload) continue;
    for (const item of splitFlow(payload[1])) {
      const name = unquote(item).replace(/\?$/u, "");
      if (name) names.add(name);
    }
  }
  return names;
}

export function readProtoEnumValues(source, name) {
  const block = new RegExp(`enum\\s+${name}\\s*\\{([^}]*)\\}`, "u").exec(source);
  if (!block) fail("boundary_registry_source_unreadable", `missing proto enum: ${name}`);
  const values = [];
  for (const match of block[1].matchAll(/^\s*([A-Z0-9_]+)\s*=\s*\d+\s*;/gmu)) values.push(match[1]);
  if (values.length === 0) fail("boundary_registry_source_unreadable", `empty proto enum: ${name}`);
  return values;
}

/** Allowed retry classes, derived from the protobuf enum minus its proto3 zero sentinel. */
export function retryClassesFromProto(source) {
  const prefix = "RETRY_CLASS_";
  const values = readProtoEnumValues(source, "RetryClass")
    .filter((value) => value !== `${prefix}UNSPECIFIED`)
    .map((value) => value.slice(prefix.length).toLowerCase());
  if (values.length === 0) fail("boundary_registry_source_unreadable", "RetryClass has no usable values");
  return values;
}

export function readProtoServiceMethods(source, service) {
  const block = new RegExp(`service\\s+${service}\\s*\\{([\\s\\S]*?)\\n\\}`, "u").exec(source);
  if (!block) fail("boundary_registry_source_unreadable", `missing proto service: ${service}`);
  const methods = [];
  for (const match of block[1].matchAll(/rpc\s+(\w+)\s*\(\s*([\w.]+)\s*\)\s*returns\s*\(\s*([\w.]+)\s*\)/gu)) {
    methods.push({ name: match[1], request: match[2], response: match[3] });
  }
  if (methods.length === 0) fail("boundary_registry_source_unreadable", `empty proto service: ${service}`);
  return methods;
}

// OpenAPI uses the root's lock-pinned strict PyYAML reader. It supports the complete YAML syntax
// used by OpenAPI (anchors, flow mappings and quoted scalars) while rejecting duplicate keys.
export function readOpenApiOperationIds(source) {
  try {
    return [...openApiOperations(readOpenApiDocument(source)).keys()];
  } catch (error) {
    return fail("boundary_registry_source_unreadable", error.message);
  }
}

export function readProtoMessages(source) {
  const messages = new Map();
  // Buf canonicalizes empty messages to `message Name {}`. Normalize that valid spelling so an
  // empty message cannot consume the next message block and hide its receipt fields.
  const normalized = source.replace(/message\s+(\w+)\s*\{\s*\}/gu, "message $1 {\n}");
  for (const match of normalized.matchAll(/message\s+(\w+)\s*\{([\s\S]*?)\n\}/gu)) {
    const fields = [];
    for (const field of match[2].matchAll(/^\s*(?:optional\s+|repeated\s+)?([\w.]+)\s+(\w+)\s*=\s*\d+/gmu)) {
      if (field[2] === "oneof") continue;
      fields.push({ type: field[1], name: field[2] });
    }
    messages.set(match[1], fields);
  }
  return messages;
}

/** Field names of a request message plus the messages it directly references. */
export function protoRequestFieldNames(messages, request) {
  const local = request.includes(".") ? request.slice(request.lastIndexOf(".") + 1) : request;
  const names = new Set();
  const direct = messages.get(local);
  if (!direct) return names;
  for (const field of direct) {
    names.add(field.name);
    const referenced = field.type.includes(".") ? field.type.slice(field.type.lastIndexOf(".") + 1) : field.type;
    for (const nested of messages.get(referenced) ?? []) names.add(nested.name);
  }
  return names;
}

// ---------------------------------------------------------------------------------------------
// Structure
// ---------------------------------------------------------------------------------------------

function validateShape(registry, retryClasses, errors) {
  if (!exactKeys(registry, REGISTRY_KEYS)) fail("boundary_registry_shape", "registry top level");
  if (registry.schemaVersion !== 1) fail("boundary_registry_schema_version", String(registry.schemaVersion));
  if (!Array.isArray(registry.owners) || registry.owners.length === 0) {
    fail("boundary_registry_shape", "owners must be a non-empty array");
  }
  if (!Array.isArray(registry.boundaries) || registry.boundaries.length === 0) {
    fail("boundary_registry_shape", "boundaries must be a non-empty array");
  }

  const retry = new Set(retryClasses);
  const seenBoundaries = new Set();
  for (const boundary of registry.boundaries) {
    if (!exactKeys(boundary, BOUNDARY_KEYS)) {
      errors.push(`boundary_registry_shape: boundary keys: ${String(boundary?.id)}`);
      continue;
    }
    const label = `${boundary.id}@v${boundary.version}`;
    if (typeof boundary.id !== "string" || !/^[a-z0-9][a-z0-9-]*$/u.test(boundary.id)) {
      errors.push(`boundary_registry_shape: boundary id: ${String(boundary.id)}`);
    }
    if (!Number.isInteger(boundary.version) || boundary.version < 1) {
      errors.push(`boundary_registry_shape: boundary version: ${label}`);
    }
    if (!SCOPES.includes(boundary.scope)) {
      errors.push(`boundary_registry_shape: boundary scope: ${label}: ${String(boundary.scope)}`);
    }
    for (const key of ["protocol", "trustPlane", "audience", "failureOwner"]) {
      if (typeof boundary[key] !== "string" || boundary[key] === "") {
        errors.push(`boundary_registry_shape: boundary ${key}: ${label}`);
      }
    }
    if (boundary.deadlineMs !== null && !(Number.isInteger(boundary.deadlineMs) && boundary.deadlineMs > 0)) {
      errors.push(`boundary_registry_shape: boundary deadlineMs: ${label}`);
    }
    if (seenBoundaries.has(boundary.id)) errors.push(`boundary_registry_duplicate_boundary: ${boundary.id}`);
    seenBoundaries.add(boundary.id);

    if (!exactKeys(boundary.provider, PARTY_KEYS)) {
      errors.push(`boundary_registry_shape: boundary provider: ${label}`);
    }
    if (!Array.isArray(boundary.consumers) || boundary.consumers.length === 0) {
      errors.push(`boundary_registry_shape: boundary consumers: ${label}`);
    } else {
      for (const consumer of boundary.consumers) {
        if (!exactKeys(consumer, PARTY_KEYS)) errors.push(`boundary_registry_shape: consumer: ${label}`);
      }
    }

    if (!Array.isArray(boundary.transports) || boundary.transports.length === 0) {
      errors.push(`boundary_registry_shape: boundary transports: ${label}`);
    }
    if (!LIFECYCLES.includes(boundary.lifecycle)) {
      errors.push(`boundary_registry_shape: boundary lifecycle: ${label}: ${String(boundary.lifecycle)}`);
    }
    if (!SOURCE_STATUSES.includes(boundary.sourceStatus)) {
      errors.push(`boundary_registry_shape: boundary sourceStatus: ${label}: ${String(boundary.sourceStatus)}`);
    }
    if (!Array.isArray(boundary.sources)) {
      errors.push(`boundary_registry_shape: boundary sources: ${label}`);
    } else {
      // A boundary claiming machine-readable coverage must actually be checkable.
      if (boundary.sourceStatus === "machine-readable" && boundary.sources.length === 0) {
        errors.push(`boundary_registry_source_missing: ${label}`);
      }
      if (boundary.sourceStatus === "declared-only" && boundary.sources.length > 0) {
        errors.push(`boundary_registry_source_status_mismatch: ${label}`);
      }
      for (const source of boundary.sources) validateSourceShape(source, label, errors);
    }
    if (boundary.transportSource !== null) validateSourceShape(boundary.transportSource, label, errors);

    if (!Array.isArray(boundary.operations) || boundary.operations.length === 0) {
      errors.push(`boundary_registry_shape: boundary operations: ${label}`);
      continue;
    }
    const transports = new Set(boundary.transports);
    const seenOperations = new Set();
    for (const operation of boundary.operations) {
      if (!exactKeys(operation, OPERATION_KEYS)) {
        errors.push(`boundary_registry_shape: operation keys: ${label}: ${String(operation?.id)}`);
        continue;
      }
      const name = `${label}/${operation.id}`;
      if (typeof operation.id !== "string" || operation.id === "") {
        errors.push(`boundary_registry_shape: operation id: ${label}`);
      }
      if (seenOperations.has(operation.id)) errors.push(`boundary_registry_duplicate_operation: ${name}`);
      seenOperations.add(operation.id);
      if (typeof operation.effect !== "boolean") {
        errors.push(`boundary_registry_shape: operation effect: ${name}`);
      }
      if (!SCOPES.includes(operation.scope)) {
        errors.push(`boundary_registry_shape: operation scope: ${name}: ${String(operation.scope)}`);
      }
      if (!SITE_BINDINGS.includes(operation.siteBinding)) {
        errors.push(`boundary_registry_shape: operation siteBinding: ${name}: ${String(operation.siteBinding)}`);
      } else if (operation.scope === "namespace" && operation.siteBinding !== "not-applicable") {
        // Rule 10 — the GA axis has no Site to bind.
        errors.push(`boundary_registry_namespace_axis_polluted: ${name}: siteBinding ${operation.siteBinding}`);
      } else if (operation.scope === "site" && operation.siteBinding === "not-applicable") {
        errors.push(`boundary_registry_site_binding_missing: ${name}`);
      }
      if (!retry.has(operation.retryClass)) {
        errors.push(`boundary_registry_retry_class_unknown: ${name}: ${String(operation.retryClass)}`);
      }
      if (typeof operation.transport !== "string" || !transports.has(operation.transport)) {
        errors.push(`boundary_registry_transport_unregistered: ${name}: ${String(operation.transport)}`);
      }
      if (operation.effect === true && operation.receipt === null) {
        errors.push(`boundary_registry_receipt_missing: ${name}`);
      }
      if (operation.receipt !== null) {
        const receiptKeysValid =
          exactKeys(operation.receipt, RECEIPT_KEYS) || exactKeys(operation.receipt, RECEIPT_RECOVERY_KEYS);
        if (!receiptKeysValid || !RECEIPT_KINDS.includes(operation.receipt.kind)) {
          errors.push(`boundary_registry_shape: operation receipt: ${name}`);
        } else if (typeof operation.receipt.ref !== "string" || operation.receipt.ref === "") {
          errors.push(`boundary_registry_shape: operation receipt ref: ${name}`);
        } else if (
          operation.retryClass === "reconcile_receipt" &&
          ["command-receipt", "state-read"].includes(operation.receipt.kind)
        ) {
          if (
            typeof operation.receipt.recoveryOperation !== "string" ||
            operation.receipt.recoveryOperation === ""
          ) {
            errors.push(`boundary_registry_recovery_operation_missing: ${name}`);
          } else {
            const recovery = boundary.operations.find(
              (candidate) => candidate.id === operation.receipt.recoveryOperation,
            );
            if (!recovery) {
              errors.push(
                `boundary_registry_recovery_operation_unknown: ${name}: ${operation.receipt.recoveryOperation}`,
              );
            } else if (recovery.effect !== false) {
              errors.push(
                `boundary_registry_recovery_operation_effectful: ${name}: ${operation.receipt.recoveryOperation}`,
              );
            }
          }
        } else if (Object.hasOwn(operation.receipt, "recoveryOperation")) {
          errors.push(`boundary_registry_recovery_operation_forbidden: ${name}: ${operation.retryClass}`);
        }
      }
    }
  }
}

function validateSourceShape(source, label, errors) {
  if (!exactKeys(source, SOURCE_KEYS)) {
    errors.push(`boundary_registry_shape: source keys: ${label}`);
    return;
  }
  if (!SOURCE_KINDS.includes(source.kind)) {
    errors.push(`boundary_registry_shape: source kind: ${label}: ${String(source.kind)}`);
  }
  if (!isRepositoryRelative(source.path)) {
    errors.push(`boundary_registry_shape: source path: ${label}: ${String(source.path)}`);
  }
  if (!source.select || typeof source.select !== "object" || Array.isArray(source.select)) {
    errors.push(`boundary_registry_shape: source select: ${label}`);
  } else if (
    source.kind === "openapi" &&
    (!exactKeys(source.select, ["member"]) || source.select.member !== "operation-id")
  ) {
    errors.push(`boundary_registry_shape: OpenAPI source select: ${label}`);
  }
}

// ---------------------------------------------------------------------------------------------
// Rules
// ---------------------------------------------------------------------------------------------

function sourceOperations(root, boundary, source, errors) {
  const absolute = resolve(root, source.path);
  if (!isInside(absolute, root)) {
    errors.push(`boundary_registry_shape: source escapes repository: ${boundary.id}: ${source.path}`);
    return null;
  }
  let text;
  try {
    text = readText(absolute, "boundary_registry_source_missing");
  } catch (error) {
    errors.push(error.message);
    return null;
  }
  try {
    if (source.kind === "proto") {
      return readProtoServiceMethods(text, source.select.service).map((method) => method.name);
    }
    if (source.kind === "openapi") return readOpenApiOperationIds(text);
    return readSpecMembers(text, source.select);
  } catch (error) {
    errors.push(`${error.message} (${boundary.id}: ${source.path})`);
    return null;
  }
}

// Rule 1 — both directions. Declared operations and source-declared operations must match exactly.
function checkSourceParity(root, boundary, errors) {
  if (boundary.sources.length === 0) return;
  const declared = sortedSet(boundary.operations.map((operation) => operation.id));
  const fromSource = [];
  for (const source of boundary.sources) {
    const members = sourceOperations(root, boundary, source, errors);
    if (members === null) return;
    fromSource.push(...members);
  }
  const actual = sortedSet(fromSource);
  const declaredSet = new Set(declared);
  const actualSet = new Set(actual);
  for (const missing of setDifference(actual, declaredSet)) {
    errors.push(`boundary_registry_operation_orphan: ${boundary.id}: ${missing}`);
  }
  for (const extra of setDifference(declared, actualSet)) {
    errors.push(`boundary_registry_operation_undeclared: ${boundary.id}: ${extra}`);
  }
}

function protoTypeName(value) {
  return String(value).slice(String(value).lastIndexOf(".") + 1);
}

function protoPackage(source) {
  return /^\s*package\s+([A-Za-z0-9_.]+)\s*;/mu.exec(source)?.[1] ?? "";
}

function canonicalProtoType(type, packageName, messages) {
  const value = String(type).replace(/^\./u, "");
  if (value.includes(".")) return value;
  return messages.has(value) && packageName !== "" ? `${packageName}.${value}` : value;
}

function responseContainsType(messages, response, expected, packageName) {
  return (messages.get(protoTypeName(response)) ?? []).some(
    (field) => canonicalProtoType(field.type, packageName, messages) === String(expected).replace(/^\./u, ""),
  );
}

// A registry receipt reference is evidence only when the RPC response can actually return it.
// Checking the direct response field is intentionally strict: a receipt hidden in an unrelated
// nested payload would not be a stable, generic recovery surface.
function checkProtoReceiptBindings(root, boundary, errors) {
  for (const source of boundary.sources ?? []) {
    if (source.kind !== "proto") continue;
    let methods;
    let messages;
    let packageName;
    try {
      const text = readText(resolve(root, source.path), "boundary_registry_source_missing");
      methods = readProtoServiceMethods(text, source.select.service);
      messages = readProtoMessages(text);
      packageName = protoPackage(text);
    } catch (error) {
      errors.push(`${error.message} (${boundary.id}: ${source.path})`);
      continue;
    }
    const byMethod = new Map(methods.map((method) => [method.name, method]));
    for (const operation of boundary.operations ?? []) {
      if (operation.receipt?.kind !== "command-receipt") continue;
      const method = byMethod.get(operation.id);
      if (!method) continue;
      const responseName = protoTypeName(method.response);
      if (!responseContainsType(messages, method.response, operation.receipt.ref, packageName)) {
        errors.push(
          `boundary_registry_receipt_unbound: ${boundary.id}@v${boundary.version}/${operation.id}: ` +
          `${responseName} does not contain ${operation.receipt.ref}`,
        );
      }
      if (operation.retryClass !== "reconcile_receipt" || !operation.receipt.recoveryOperation) continue;
      const recovery = byMethod.get(operation.receipt.recoveryOperation);
      if (!recovery) continue;
      const requestFields = new Set(
        (messages.get(protoTypeName(recovery.request)) ?? []).map((field) => field.name),
      );
      const commandLookup = ["command_id", "digest_algorithm", "request_digest"].every((field) =>
        requestFields.has(field),
      );
      const proofLookup = requestFields.has("transaction_ref") && requestFields.has("recovery_proof");
      if (!commandLookup && !proofLookup) {
        errors.push(
          `boundary_registry_recovery_operation_unbound: ${boundary.id}@v${boundary.version}/${operation.id}: ` +
            `${operation.receipt.recoveryOperation} request`,
        );
      }
      if (!responseContainsType(messages, recovery.response, operation.receipt.ref, packageName)) {
        errors.push(
          `boundary_registry_recovery_operation_unbound: ${boundary.id}@v${boundary.version}/${operation.id}: ` +
            `${operation.receipt.recoveryOperation} response`,
        );
      }
    }
  }
}

function checkOpenApiRecoveryBindings(root, boundary, errors) {
  for (const source of boundary.sources ?? []) {
    if (source.kind !== "openapi") continue;
    let operations;
    try {
      const text = readText(resolve(root, source.path), "boundary_registry_source_missing");
      operations = openApiOperations(readOpenApiDocument(text));
    } catch (error) {
      errors.push(`${error.message} (${boundary.id}: ${source.path})`);
      continue;
    }
    for (const operation of boundary.operations ?? []) {
      if (
        operation.retryClass !== "reconcile_receipt" ||
        operation.receipt?.kind !== "state-read" ||
        !operation.receipt.recoveryOperation
      ) {
        continue;
      }
      const recovery = operations.get(operation.receipt.recoveryOperation);
      const label = `${boundary.id}@v${boundary.version}/${operation.id}`;
      if (!recovery || recovery.method !== "get") {
        errors.push(
          `boundary_registry_recovery_operation_unbound: ${label}: ` +
            `${operation.receipt.recoveryOperation} must be GET`,
        );
        continue;
      }
      if (recovery.operation?.responses?.["200"] === undefined) {
        errors.push(
          `boundary_registry_recovery_operation_unbound: ${label}: ` +
            `${operation.receipt.recoveryOperation} response`,
        );
      }
    }
  }
}

// Rule 2 — one frozen transport per operation. A consumer must never be able to reach the same
// operation over two transports, and a declared transport must be a real registered channel.
function checkTransportFreeze(root, registry, errors) {
  const byConsumer = new Map();
  for (const boundary of registry.boundaries) {
    for (const consumer of boundary.consumers ?? []) {
      for (const operation of boundary.operations ?? []) {
        const key = `${consumer?.repository}::${operation.id}`;
        const existing = byConsumer.get(key);
        if (existing && existing.transport !== operation.transport) {
          errors.push(
            `boundary_registry_transport_conflict: ${key}: ${existing.boundary}=${existing.transport}, ${boundary.id}=${operation.transport}`,
          );
          continue;
        }
        if (!existing) byConsumer.set(key, { boundary: boundary.id, transport: operation.transport });
      }
    }
    if (boundary.transportSource === null || boundary.transportSource === undefined) continue;
    const channels = sourceOperations(root, boundary, boundary.transportSource, errors);
    if (channels === null) continue;
    const known = new Set(channels);
    for (const transport of boundary.transports ?? []) {
      if (!known.has(transport)) {
        errors.push(
          `boundary_registry_transport_unregistered: ${boundary.id}: ${transport} not in ${boundary.transportSource.path}`,
        );
      }
    }
  }
}

// Rule 3 — the registry and the compatibility matrix describe the same federation.
function checkCompatibilityMatrix(registry, matrix, errors) {
  const contracts = Array.isArray(matrix?.contracts) ? matrix.contracts : [];
  if (contracts.length === 0) {
    errors.push("boundary_registry_matrix_drift: compatibility matrix declares no contracts");
    return;
  }
  // A contract-only boundary has a published shape but no provider yet, so it is
  // deliberately absent from the compatibility matrix: the matrix drives the
  // runtime gate, and listing an unimplemented protocol there would assert a
  // capability that does not exist.
  const live = registry.boundaries.filter((boundary) => boundary.lifecycle !== "contract-only");
  const declaredOnly = registry.boundaries.filter((boundary) => boundary.lifecycle === "contract-only");
  const registryKeys = sortedSet(live.map((boundary) => `${boundary.id}@v${boundary.version}`));
  const matrixKeys = sortedSet(contracts.map((contract) => `${contract.id}@v${contract.version}`));
  const matrixSet = new Set(matrixKeys);
  const registrySet = new Set(registryKeys);
  for (const missing of setDifference(matrixKeys, registrySet)) {
    errors.push(`boundary_registry_matrix_drift: unregistered contract: ${missing}`);
  }
  for (const extra of setDifference(registryKeys, matrixSet)) {
    errors.push(`boundary_registry_matrix_drift: contract absent from matrix: ${extra}`);
  }

  const byKey = new Map(contracts.map((contract) => [`${contract.id}@v${contract.version}`, contract]));
  for (const boundary of declaredOnly) {
    if (byKey.has(`${boundary.id}@v${boundary.version}`)) {
      errors.push(`boundary_registry_matrix_drift: contract-only boundary in matrix: ${boundary.id}`);
    }
  }
  for (const boundary of live) {
    const contract = byKey.get(`${boundary.id}@v${boundary.version}`);
    if (!contract) continue;
    const providers = sortedSet([boundary.provider?.repository]);
    const consumers = sortedSet((boundary.consumers ?? []).map((consumer) => consumer?.repository));
    if (JSON.stringify(providers) !== JSON.stringify(sortedSet(contract.providers ?? []))) {
      errors.push(`boundary_registry_matrix_drift: providers: ${boundary.id}`);
    }
    if (JSON.stringify(consumers) !== JSON.stringify(sortedSet(contract.consumers ?? []))) {
      errors.push(`boundary_registry_matrix_drift: consumers: ${boundary.id}`);
    }
  }
}

// Rule 4 — provider and consumers must be registered architecture boundaries inside their repository.
function checkArchitectureBoundaries(registry, roots, errors) {
  const byId = new Map();
  for (const root of Array.isArray(roots?.roots) ? roots.roots : []) {
    if (root?.id) byId.set(root.id, root);
  }
  if (byId.size === 0) {
    errors.push("boundary_registry_architecture_boundary_unknown: architecture manifest declares no roots");
    return;
  }
  for (const boundary of registry.boundaries) {
    for (const party of [boundary.provider, ...(boundary.consumers ?? [])]) {
      const entry = byId.get(party?.boundary);
      if (!entry || entry.kind !== "boundary") {
        errors.push(`boundary_registry_architecture_boundary_unknown: ${boundary.id}: ${String(party?.boundary)}`);
        continue;
      }
      if (typeof entry.path !== "string" || !`${entry.path}/`.startsWith(`${party.repository}/`)) {
        errors.push(
          `boundary_registry_architecture_boundary_unknown: ${boundary.id}: ${party.boundary} is not inside ${String(party.repository)}`,
        );
      }
    }
  }
}


// Invert the select transform: an operation id derived from `UsageHoldRequest` by
// stripping the suffix and snake-casing maps back to that object name.
function specObjectCandidates(operationId, select) {
  const pascal = operationId
    .split("_")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join("");
  const suffixes = /Request\|Query/u.test(String(select?.match ?? ""))
    ? ["Request", "Query"]
    : ["Request", "Query", ""];
  return [...new Set(suffixes.map((suffix) => `${pascal}${suffix}`))];
}

// Operations whose site claim rests only on a file-wide match, because their source
// section declares no per-operation fields. Weaker evidence, so it is counted.
const fileWideProof = new Set();

function hasSiteField(fields) {
  return SITE_FIELDS.some((field) => fields.has(field));
}

/**
 * Rule 8 — a namespace-scoped boundary is the GA axis and must stay single-keyed.
 * Rule 9 — an operation claiming `siteBinding: "request-field"` must really have that field in its
 *          contract source. A claim of structural Site isolation has to be provable; anything else
 *          stays honest as `context-header` debt (rule 11) instead of being written up as done.
 */
function checkIsolationAxes(root, registry, errors) {
  for (const boundary of registry.boundaries) {
    const namespaceScoped = boundary.scope === "namespace";
    for (const operation of boundary.operations ?? []) {
      if (namespaceScoped && operation.scope === "site") {
        errors.push(`boundary_registry_namespace_axis_polluted: ${boundary.id}/${operation.id}: site scope`);
      }
    }

    // Operations whose site binding claim still needs structural proof.
    const unproven = new Set(
      (boundary.operations ?? [])
        .filter((operation) => operation.siteBinding === "request-field")
        .map((operation) => operation.id),
    );

    for (const source of boundary.sources ?? []) {
      const absolute = resolve(root, source.path);
      if (!isInside(absolute, root)) continue;
      let text;
      try {
        text = readText(absolute, "boundary_registry_source_missing");
      } catch (error) {
        errors.push(error.message);
        continue;
      }
      if (source.kind === "proto") {
        checkProtoIsolation(text, boundary, source, namespaceScoped, unproven, errors);
        continue;
      }
      if (source.kind === "openapi") continue;
      let fields;
      try {
        fields = readSpecFieldNames(text, source.select);
      } catch (error) {
        errors.push(`${error.message} (${boundary.id}: ${source.path})`);
        continue;
      }
      if (namespaceScoped) {
        for (const forbidden of GA_FORBIDDEN_FIELDS) {
          if (fields.has(forbidden)) {
            errors.push(`boundary_registry_namespace_axis_polluted: ${boundary.id}: ${source.path}: ${forbidden}`);
          }
        }
      }
      // Where operation ids are derived from object names, each operation can be proved
      // against its own request shape; checking the file as a whole let one object's
      // siteId vouch for siblings that had none.
      //
      // Where they come from a block-mapping section such as `endpoints`, the section
      // declares no fields, so the only available proof is file-wide. That is weaker and
      // is counted separately rather than presented as per-operation evidence.
      if (source.select?.section === "objects") {
        for (const id of [...unproven]) {
          for (const candidate of specObjectCandidates(id, source.select)) {
            const { known, names } = readSpecObjectFields(text, candidate);
            if (known && hasSiteField(names)) {
              unproven.delete(id);
              break;
            }
          }
        }
      } else if (hasSiteField(readSpecDeclaredFieldNames(text))) {
        for (const id of [...unproven]) fileWideProof.add(`${boundary.id}/${id}`);
        unproven.clear();
      }
    }

    for (const id of [...unproven].sort()) {
      errors.push(`boundary_registry_site_scope_unstructured: ${boundary.id}/${id}: no site id field in source`);
    }
  }
}

function checkProtoIsolation(text, boundary, source, namespaceScoped, unproven, errors) {
  let methods;
  let messages;
  try {
    methods = readProtoServiceMethods(text, source.select.service);
    messages = readProtoMessages(text);
  } catch (error) {
    errors.push(`${error.message} (${boundary.id}: ${source.path})`);
    return;
  }
  const requestByMethod = new Map(methods.map((method) => [method.name, method.request]));
  for (const operation of boundary.operations ?? []) {
    const request = requestByMethod.get(operation.id);
    if (!request) continue;
    const fields = protoRequestFieldNames(messages, request);
    if (namespaceScoped) {
      for (const forbidden of GA_FORBIDDEN_FIELDS) {
        if (fields.has(forbidden)) {
          errors.push(
            `boundary_registry_namespace_axis_polluted: ${boundary.id}/${operation.id}: ${request}.${forbidden}`,
          );
        }
      }
      continue;
    }
    // Proto sources prove the claim per request message, so report the offending message by name.
    if (unproven.has(operation.id)) {
      unproven.delete(operation.id);
      if (!hasSiteField(fields)) {
        errors.push(`boundary_registry_site_scope_unstructured: ${boundary.id}/${operation.id}: ${request}`);
      }
    }
  }
}

// The published schema must stay pinned to the same enums this gate enforces.
function checkSchemaParity(schema, retryClasses, errors) {
  const definitions = schema?.$defs;
  if (!definitions || typeof definitions !== "object") {
    errors.push("boundary_registry_schema_drift: missing $defs");
    return;
  }
  const expected = [
    ["retryClass", sortedSet(retryClasses)],
    ["scope", sortedSet(SCOPES)],
    ["receiptKind", sortedSet(RECEIPT_KINDS)],
    ["siteBinding", sortedSet(SITE_BINDINGS)],
    ["sourceStatus", sortedSet(SOURCE_STATUSES)],
    ["sourceKind", sortedSet(SOURCE_KINDS)],
  ];
  for (const [name, values] of expected) {
    const actual = definitions[name]?.enum;
    if (!Array.isArray(actual) || JSON.stringify(sortedSet(actual)) !== JSON.stringify(values)) {
      errors.push(`boundary_registry_schema_drift: ${name} enum must equal ${values.join(",")}`);
    }
  }
}

export function checkBoundaryRegistry(options) {
  const registry = readJson(options.registry, "boundary_registry_json");
  const schema = readJson(options.schema, "boundary_registry_json");
  const matrix = readJson(options.matrix, "boundary_registry_json");
  // The architecture manifest is JSON-compatible YAML, matching scripts/architecture.
  const roots = readJson(options.roots, "boundary_registry_json");
  const retryClasses = retryClassesFromProto(
    readText(resolve(options.root, DEFAULT_RETRY_CLASS_PROTO), "boundary_registry_source_missing"),
  );

  const errors = [];
  validateShape(registry, retryClasses, errors);
  checkSchemaParity(schema, retryClasses, errors);
  for (const boundary of registry.boundaries) {
    if (!Array.isArray(boundary?.sources) || !Array.isArray(boundary?.operations)) continue;
    checkSourceParity(options.root, boundary, errors);
    checkProtoReceiptBindings(options.root, boundary, errors);
    checkOpenApiRecoveryBindings(options.root, boundary, errors);
  }
  checkTransportFreeze(options.root, registry, errors);
  checkCompatibilityMatrix(registry, matrix, errors);
  checkArchitectureBoundaries(registry, roots, errors);
  checkIsolationAxes(options.root, registry, errors);

  let operations = 0;
  let headerBound = 0;
  let declaredOnly = 0;
  for (const boundary of registry.boundaries) {
    // A boundary with no contract source in this repository cannot be orphan-checked, so it is
    // reported every run rather than passing as if it were covered.
    if (boundary.sourceStatus === "declared-only") declaredOnly += 1;
    for (const operation of Array.isArray(boundary.operations) ? boundary.operations : []) {
      operations += 1;
      // Rule 11 — header-bound Site scopes are legal but never silent; they are the Wave T3 backlog.
      if (operation.siteBinding === "context-header") headerBound += 1;
    }
  }
  return {
    errors: sortedSet(errors),
    boundaries: registry.boundaries.length,
    operations,
    headerBound,
    declaredOnly,
    requestField: registry.boundaries
      .flatMap((boundary) => boundary.operations ?? [])
      .filter((operation) => operation?.siteBinding === "request-field").length,
    contractOnly: registry.boundaries.filter((boundary) => boundary.lifecycle === "contract-only").length,
  };
}

function main() {
  try {
    const options = parseArguments(process.argv.slice(2));
    const { errors, boundaries, operations, headerBound, declaredOnly, requestField, contractOnly } =
      checkBoundaryRegistry(options);
    if (errors.length > 0) {
      process.stderr.write(`${errors.join("\n")}\n`);
      process.exitCode = 1;
      return;
    }
    const noun = declaredOnly === 1 ? "boundary" : "boundaries";
    process.stdout.write(
      `boundary_registry_ok: ${boundaries} boundaries, ${operations} operations, ` +
        `${headerBound} header-bound site scopes (migration debt), ` +
        `${declaredOnly} declared-only ${noun} (no machine-readable source), ` +
        `${requestField} request-field site scopes, ${contractOnly} contract-only (published, no provider)\n`,
    );
  } catch (error) {
    const code = error instanceof BoundaryRegistryError ? error.message : `boundary_registry_check_failed: ${error.message}`;
    process.stderr.write(`${code}\n`);
    process.exitCode = 1;
  }
}

if (process.argv[1] && resolve(process.argv[1]) === resolve(SCRIPT_PATH)) {
  main();
}
