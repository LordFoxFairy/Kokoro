#!/usr/bin/env node

import { execFileSync } from "node:child_process";
import { createHash, createPublicKey, verify } from "node:crypto";
import { closeSync, constants, fstatSync, openSync, readSync, realpathSync } from "node:fs";
import { tmpdir } from "node:os";
import { basename, dirname, isAbsolute, relative, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

import { create, createFileRegistry, fromBinary, isFieldSet, ScalarType, toBinary } from "@bufbuild/protobuf";
import { createValidator } from "@bufbuild/protovalidate";
import { FileDescriptorSetSchema } from "@bufbuild/protobuf/wkt";

const CONTRACT = dirname(fileURLToPath(import.meta.url));
const DEFAULT_CORPUS = resolve(CONTRACT, "corpus/projection-integrity-v1.json");
const MANIFEST_PATH = resolve(CONTRACT, "spec/projection-integrity.yaml");
const BUF = resolve(CONTRACT, "node_modules/.bin/buf");
const HEX = /^(?:[0-9a-f]{2})+$/u;
const BASE64 = /^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/u;
const DIGEST = /^[0-9a-f]{64}$/u;
const REFERENCE = /^[A-Za-z0-9][A-Za-z0-9._:@-]{0,255}$/u;

function reject(code) { const error = new Error(code); error.code = code; throw error; }
function boundedJson(path, maximum, code) {
  let file;
  try { file = openSync(path, constants.O_RDONLY | constants.O_NOFOLLOW); }
  catch { reject(`${code}_UNREADABLE`); }
  try {
    let before;
    try { before = fstatSync(file); } catch { reject(`${code}_UNREADABLE`); }
    if (!before.isFile()) reject(`${code}_UNREADABLE`);
    if (before.size > maximum) reject(`${code}_TOO_LARGE`);
    const bytes = Buffer.allocUnsafe(maximum + 1);
    let offset = 0;
    while (offset < bytes.length) {
      let count;
      try { count = readSync(file, bytes, offset, bytes.length - offset, null); }
      catch { reject(`${code}_UNREADABLE`); }
      if (count === 0) break;
      offset += count;
    }
    if (offset > maximum) reject(`${code}_TOO_LARGE`);
    let after;
    try { after = fstatSync(file); } catch { reject(`${code}_UNREADABLE`); }
    if (after.size > maximum) reject(`${code}_TOO_LARGE`);
    if (after.size !== before.size || after.size !== offset) reject(`${code}_CHANGED_DURING_READ`);
    let source;
    try { source = new TextDecoder("utf-8", { fatal: true }).decode(bytes.subarray(0, offset)); }
    catch { reject(`${code}_INVALID`); }
    try { return JSON.parse(source); } catch { reject(`${code}_INVALID`); }
  } finally {
    try { closeSync(file); } catch { /* preserve the stable read/parse result */ }
  }
}

const rawManifest = boundedJson(MANIFEST_PATH, 64 * 1024, "PROJECTION_INTEGRITY_MANIFEST");
const RESOURCE_CAPS = Object.freeze({
  corpus_bytes: 1_048_576,
  positive_cases: 16,
  negative_cases: 64,
  record_bytes: 524_288,
  descriptor_bytes: 4_194_304,
  message_depth: 32,
  repeated_items: 1_024,
  identifier_bytes: 1_024,
  public_key_bytes: 4_096,
  signature_bytes: 64,
  buf_timeout_ms: 30_000,
});
if (rawManifest.schema_version !== 1 || rawManifest.digest_algorithm !== "SHA256" || rawManifest.signature_algorithm !== "ED25519" || rawManifest.canonical_encoding !== "DETERMINISTIC_PROTOBUF" || !HEX.test(rawManifest.signature_domain_hex) || !Array.isArray(rawManifest.surfaces) || !Array.isArray(rawManifest.forbidden_signed_field_fragments) || rawManifest.limits === null || typeof rawManifest.limits !== "object" || Array.isArray(rawManifest.limits)) reject("PROJECTION_INTEGRITY_MANIFEST_INVALID");
if (JSON.stringify(Object.keys(rawManifest.limits).sort()) !== JSON.stringify(Object.keys(RESOURCE_CAPS).sort())) reject("PROJECTION_INTEGRITY_MANIFEST_INVALID");
for (const [name, cap] of Object.entries(RESOURCE_CAPS)) {
  const value = rawManifest.limits[name];
  if (!Number.isSafeInteger(value) || value < 1 || value > cap) reject("PROJECTION_INTEGRITY_MANIFEST_INVALID");
}
if (rawManifest.limits.signature_bytes !== 64) reject("PROJECTION_INTEGRITY_MANIFEST_INVALID");
const MANIFEST = Object.freeze(rawManifest);
const LIMITS = Object.freeze(MANIFEST.limits);
if (
  MANIFEST.forbidden_signed_field_fragments.length === 0 ||
  new Set(MANIFEST.forbidden_signed_field_fragments).size !== MANIFEST.forbidden_signed_field_fragments.length ||
  MANIFEST.forbidden_signed_field_fragments.some(
    (fragment) => typeof fragment !== "string" || !/^[a-z][a-z0-9_]*$/u.test(fragment),
  )
) reject("PROJECTION_INTEGRITY_MANIFEST_INVALID");
const POLICIES = new Map();
for (const surface of MANIFEST.surfaces) {
  if (
    surface === null ||
    typeof surface !== "object" ||
    Array.isArray(surface) ||
    JSON.stringify(Object.keys(surface).sort()) !== JSON.stringify(["digest_fields", "domain_separator", "message_type", "signature_field"]) ||
    typeof surface.message_type !== "string" ||
    !REFERENCE.test(surface.message_type) ||
    typeof surface.domain_separator !== "string" ||
    Buffer.byteLength(surface.domain_separator) < 1 ||
    Buffer.byteLength(surface.domain_separator) > LIMITS.identifier_bytes ||
    !Array.isArray(surface.digest_fields) ||
    surface.digest_fields.length < 1 ||
    new Set(surface.digest_fields).size !== surface.digest_fields.length ||
    surface.digest_fields.some((field) => typeof field !== "string" || !/^[a-z][a-z0-9_]*$/u.test(field)) ||
    typeof surface.signature_field !== "string" ||
    !/^[a-z][a-z0-9_]*$/u.test(surface.signature_field) ||
    surface.digest_fields.includes(surface.signature_field) ||
    POLICIES.has(surface.message_type)
  ) reject("PROJECTION_INTEGRITY_MANIFEST_INVALID");
  POLICIES.set(surface.message_type, Object.freeze(surface));
}
if (POLICIES.size !== LIMITS.positive_cases) reject("PROJECTION_INTEGRITY_MANIFEST_INVALID");

function boundedHex(hex, field, maximumBytes) {
  if (typeof hex !== "string" || hex.length > maximumBytes * 2 || !HEX.test(hex)) reject(`PROJECTION_INTEGRITY_${field}_INVALID`);
  return Buffer.from(hex, "hex");
}
function boundedBase64(value, maximumBytes, field) {
  if (typeof value !== "string" || value.length > Math.ceil(maximumBytes / 3) * 4 || !BASE64.test(value)) reject(`PROJECTION_INTEGRITY_${field}_INVALID`);
  const result = Buffer.from(value, "base64");
  if (result.length > maximumBytes || result.toString("base64") !== value) reject(`PROJECTION_INTEGRITY_${field}_INVALID`);
  return result;
}

function descriptorRegistry() {
  let descriptorBytes;
  try {
    descriptorBytes = execFileSync(BUF, ["build", "proto", "--as-file-descriptor-set", "-o", "-"], {
      cwd: CONTRACT,
      encoding: "buffer",
      timeout: LIMITS.buf_timeout_ms,
      maxBuffer: LIMITS.descriptor_bytes,
      stdio: ["ignore", "pipe", "pipe"],
    });
  } catch { reject("PROJECTION_INTEGRITY_DESCRIPTOR_BUILD_FAILED"); }
  if (descriptorBytes.length > LIMITS.descriptor_bytes) reject("PROJECTION_INTEGRITY_DESCRIPTOR_SET_TOO_LARGE");
  try { return createFileRegistry(fromBinary(FileDescriptorSetSchema, descriptorBytes)); }
  catch { reject("PROJECTION_INTEGRITY_DESCRIPTOR_SET_INVALID"); }
}

function selectedFieldValue(message, field) {
  if (field.oneof !== undefined) {
    const selected = message[field.oneof.localName];
    return selected?.case === field.localName ? selected.value : undefined;
  }
  return message[field.localName];
}
function eachMessageValue(value, field, callback) {
  if (value === undefined) return;
  if (field.listKind !== undefined) { for (const item of value) callback(item, field.message); return; }
  if (field.mapKind !== undefined) { if (field.message !== undefined) for (const item of Object.values(value)) callback(item, field.message); return; }
  callback(value, field.message);
}
function rejectUnknownFields(message, descriptor) {
  if (Array.isArray(message.$unknown) && message.$unknown.length > 0) reject("PROJECTION_INTEGRITY_UNKNOWN_FIELD");
  for (const field of descriptor.fields) {
    if (field.message !== undefined && isFieldSet(message, field)) eachMessageValue(selectedFieldValue(message, field), field, rejectUnknownFields);
  }
}
function enforceMessageBudget(message, descriptor, depth = 0) {
  if (depth > LIMITS.message_depth) reject("PROJECTION_INTEGRITY_MESSAGE_DEPTH_EXCEEDED");
  for (const field of descriptor.fields) {
    if (!isFieldSet(message, field)) continue;
    const value = selectedFieldValue(message, field);
    if (field.listKind !== undefined && value.length > LIMITS.repeated_items) reject("PROJECTION_INTEGRITY_REPEATED_ITEMS_EXCEEDED");
    if (field.mapKind !== undefined && Object.keys(value).length > LIMITS.repeated_items) reject("PROJECTION_INTEGRITY_REPEATED_ITEMS_EXCEEDED");
    if (field.message !== undefined) eachMessageValue(value, field, (item, nested) => enforceMessageBudget(item, nested, depth + 1));
  }
}
function assertNoForbiddenSignedFields(descriptor, depth = 0, ancestors = new Set()) {
  if (depth > LIMITS.message_depth || ancestors.has(descriptor.typeName)) reject("PROJECTION_INTEGRITY_SIGNED_SCHEMA_RECURSIVE");
  const next = new Set(ancestors); next.add(descriptor.typeName);
  for (const field of descriptor.fields) {
    const normalized = field.name.toLowerCase();
    if (MANIFEST.forbidden_signed_field_fragments.some((fragment) => normalized.includes(fragment))) reject("PROJECTION_INTEGRITY_FORBIDDEN_SIGNED_FIELD");
    if (field.message !== undefined) assertNoForbiddenSignedFields(field.message, depth + 1, next);
  }
}
function assertPolicyDescriptors(registry) {
  for (const policy of POLICIES.values()) {
    const descriptor = registry.getMessage(policy.message_type);
    if (descriptor === undefined) reject("PROJECTION_INTEGRITY_MESSAGE_DESCRIPTOR_MISSING");
    assertNoForbiddenSignedFields(descriptor);
    for (const name of policy.digest_fields) {
      const field = descriptor.fields.find((candidate) => candidate.name === name);
      if (field?.fieldKind !== "scalar" || field.scalar !== ScalarType.STRING) reject("PROJECTION_INTEGRITY_POLICY_INVALID");
    }
    const signature = descriptor.fields.find((field) => field.name === policy.signature_field);
    if (signature?.fieldKind !== "message" || signature.message.typeName !== "kokoro.common.v1.ProjectionSignature") reject("PROJECTION_INTEGRITY_POLICY_INVALID");
  }
}

function decodeCanonicalRecord(registry, messageType, domainHex, recordHex) {
  const policy = POLICIES.get(messageType);
  if (policy === undefined) reject("PROJECTION_INTEGRITY_MESSAGE_TYPE_INVALID");
  if (domainHex !== undefined && Buffer.from(policy.domain_separator).toString("hex") !== domainHex) reject("PROJECTION_INTEGRITY_DOMAIN_MISMATCH");
  const descriptor = registry.getMessage(messageType);
  if (descriptor === undefined) reject("PROJECTION_INTEGRITY_MESSAGE_DESCRIPTOR_MISSING");
  const record = boundedHex(recordHex, "RECORD", LIMITS.record_bytes);
  let message;
  try { message = fromBinary(descriptor, record); } catch { reject("PROJECTION_INTEGRITY_PROTOBUF_INVALID"); }
  rejectUnknownFields(message, descriptor);
  enforceMessageBudget(message, descriptor);
  for (const name of policy.digest_fields) {
    const field = descriptor.fields.find((candidate) => candidate.name === name);
    if (isFieldSet(message, field)) reject("PROJECTION_INTEGRITY_EXCLUDED_FIELD");
  }
  const signatureField = descriptor.fields.find((candidate) => candidate.name === policy.signature_field);
  if (isFieldSet(message, signatureField)) reject("PROJECTION_INTEGRITY_SIGNATURE_FIELD");
  let canonical;
  try { canonical = Buffer.from(toBinary(descriptor, message, { writeUnknownFields: false })); }
  catch { reject("PROJECTION_INTEGRITY_PROTOBUF_INVALID"); }
  if (!canonical.equals(record)) reject("PROJECTION_INTEGRITY_NON_CANONICAL_PROTOBUF");
  return { policy, descriptor, message, record };
}

function restoreAuthenticatedFields(decoded, testCase, digest, signature) {
  const { policy, descriptor, message } = decoded;
  for (const name of policy.digest_fields) {
    const field = descriptor.fields.find((candidate) => candidate.name === name);
    message[field.localName] = digest.toString("hex");
  }
  const signatureField = descriptor.fields.find((candidate) => candidate.name === policy.signature_field);
  message[signatureField.localName] = create(signatureField.message, { algorithm: 1, keyRevision: testCase.keyRevision, signature });
}
function validateWithProtovalidate(validator, descriptor, message) {
  let result;
  try { result = validator.validate(descriptor, message); }
  catch { reject("PROJECTION_INTEGRITY_VALIDATION_ENGINE_ERROR"); }
  if (result.kind === "error") reject("PROJECTION_INTEGRITY_VALIDATION_ENGINE_ERROR");
  if (result.kind === "invalid") reject("PROJECTION_INTEGRITY_CONSTRAINT_VIOLATION");
}
function authenticateDecoded(testCase, decoded, signatureDomain) {
  if (typeof testCase.keyRevision !== "string" || Buffer.byteLength(testCase.keyRevision) > LIMITS.identifier_bytes) reject("PROJECTION_INTEGRITY_CASE_INVALID");
  const digest = createHash("sha256").update(boundedHex(testCase.domainSeparatorHex, "DOMAIN", LIMITS.identifier_bytes)).update(decoded.record).digest();
  if (!DIGEST.test(testCase.digestSha256) || digest.toString("hex") !== testCase.digestSha256) reject(`PROJECTION_INTEGRITY_DIGEST_MISMATCH:${testCase.id}`);
  const signature = boundedBase64(testCase.signatureBase64, LIMITS.signature_bytes, "SIGNATURE");
  if (signature.length !== LIMITS.signature_bytes) reject(`PROJECTION_INTEGRITY_SIGNATURE_LENGTH:${testCase.id}`);
  const publicKeyBytes = boundedBase64(testCase.publicKeySpkiBase64, LIMITS.public_key_bytes, "PUBLIC_KEY");
  let publicKey;
  try { publicKey = createPublicKey({ key: publicKeyBytes, format: "der", type: "spki" }); }
  catch { reject(`PROJECTION_INTEGRITY_PUBLIC_KEY_INVALID:${testCase.id}`); }
  let verified;
  try { verified = verify(null, Buffer.concat([signatureDomain, digest]), publicKey, signature); }
  catch { reject(`PROJECTION_INTEGRITY_CRYPTO_FAILURE:${testCase.id}`); }
  if (!verified) reject(`PROJECTION_INTEGRITY_SIGNATURE_INVALID:${testCase.id}`);
  restoreAuthenticatedFields(decoded, testCase, digest, signature);
}

function validateCorpus(path) {
  const corpus = boundedJson(path, LIMITS.corpus_bytes, "PROJECTION_INTEGRITY_CORPUS");
  if (corpus.schemaVersion !== 1 || !Array.isArray(corpus.cases) || corpus.cases.length !== LIMITS.positive_cases || !Array.isArray(corpus.negativeCases) || corpus.negativeCases.length > LIMITS.negative_cases || corpus.signatureDomainHex !== MANIFEST.signature_domain_hex) reject("PROJECTION_INTEGRITY_CORPUS_SHAPE_INVALID");
  const registry = descriptorRegistry();
  assertPolicyDescriptors(registry);
  const validator = createValidator({ registry, failFast: false });
  const signatureDomain = boundedHex(corpus.signatureDomainHex, "SIGNATURE_DOMAIN", LIMITS.identifier_bytes);
  const identifiers = new Set();
  for (const testCase of corpus.cases) {
    if (testCase === null || typeof testCase !== "object" || typeof testCase.id !== "string" || Buffer.byteLength(testCase.id) > LIMITS.identifier_bytes || identifiers.has(testCase.id)) reject("PROJECTION_INTEGRITY_DUPLICATE_OR_INVALID_ID");
    identifiers.add(testCase.id);
    if (typeof testCase.messageType !== "string" || Buffer.byteLength(testCase.messageType) > LIMITS.identifier_bytes) reject("PROJECTION_INTEGRITY_CASE_INVALID");
    const decoded = decodeCanonicalRecord(registry, testCase.messageType, testCase.domainSeparatorHex, testCase.canonicalRecordHex);
    authenticateDecoded(testCase, decoded, signatureDomain);
    validateWithProtovalidate(validator, decoded.descriptor, decoded.message);
  }
  if (new Set(corpus.cases.map(({ messageType }) => messageType)).size !== POLICIES.size) reject("PROJECTION_INTEGRITY_SURFACE_COVERAGE_INVALID");
  for (const testCase of corpus.negativeCases) {
    if (testCase === null || typeof testCase !== "object" || typeof testCase.id !== "string" || identifiers.has(testCase.id) || typeof testCase.expectedErrorCode !== "string") reject("PROJECTION_INTEGRITY_NEGATIVE_CASE_INVALID");
    identifiers.add(testCase.id);
    try {
      const decoded = decodeCanonicalRecord(registry, testCase.messageType, testCase.authenticated === true ? testCase.domainSeparatorHex : undefined, testCase.canonicalRecordHex);
      if (testCase.authenticated === true) authenticateDecoded(testCase, decoded, signatureDomain);
      validateWithProtovalidate(validator, decoded.descriptor, decoded.message);
      reject("PROJECTION_INTEGRITY_NEGATIVE_ACCEPTED");
    } catch (error) { if (error.code !== testCase.expectedErrorCode && error.message !== testCase.expectedErrorCode) throw error; }
  }
  process.stdout.write(`projection_integrity_corpus_ok:${corpus.cases.length}+${corpus.negativeCases.length}\n`);
}

function parseCorpusPath(argv) {
  if (argv.length === 1 && argv[0] === "--validate-corpus") return DEFAULT_CORPUS;
  if (argv.length !== 2 || argv[0] !== "--validate-corpus-file" || !isAbsolute(argv[1])) reject("PROJECTION_INTEGRITY_ARGUMENT_INVALID");
  let candidate;
  let temporaryRoot;
  try {
    candidate = resolve(realpathSync(dirname(argv[1])), basename(argv[1]));
    temporaryRoot = realpathSync(tmpdir());
  } catch { reject("PROJECTION_INTEGRITY_CORPUS_PATH_INVALID"); }
  const relativePath = relative(temporaryRoot, candidate);
  if (relativePath.startsWith("..") || isAbsolute(relativePath)) reject("PROJECTION_INTEGRITY_CORPUS_PATH_INVALID");
  return candidate;
}

export { validateCorpus };
if (import.meta.url === pathToFileURL(process.argv[1] ?? "").href) {
  try { validateCorpus(parseCorpusPath(process.argv.slice(2))); }
  catch (error) {
    process.stderr.write(`${error?.code ?? "PROJECTION_INTEGRITY_INTERNAL_ERROR"}\n`);
    process.exitCode = 1;
  }
}
