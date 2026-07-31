#!/usr/bin/env node

import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { readFileSync, realpathSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { basename, dirname, isAbsolute, relative, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

import { create, createFileRegistry, fromBinary, getOption, toBinary } from "@bufbuild/protobuf";
import { FileDescriptorSetSchema } from "@bufbuild/protobuf/wkt";

const CONTRACT = dirname(fileURLToPath(import.meta.url));
const MANIFEST_PATH = resolve(CONTRACT, "spec/media-canonicalization.yaml");
const CORPUS = resolve(CONTRACT, "corpus/media-canonicalization-v1.json");
const BUF = resolve(CONTRACT, "node_modules/.bin/buf");
const HEX = /^(?:[0-9a-f]{2})+$/u;

function reject(code) {
  const error = new Error(code);
  error.code = code;
  throw error;
}

function descriptorRegistry() {
  let bytes;
  try {
    bytes = execFileSync(BUF, ["build", "proto", "--as-file-descriptor-set", "-o", "-"], {
      cwd: CONTRACT,
      encoding: "buffer",
      timeout: 10_000,
      maxBuffer: 4 * 1024 * 1024,
      stdio: ["ignore", "pipe", "pipe"],
    });
  } catch {
    reject("MEDIA_CANONICAL_DESCRIPTOR_BUILD_FAILED");
  }
  try {
    return createFileRegistry(fromBinary(FileDescriptorSetSchema, bytes));
  } catch {
    reject("MEDIA_CANONICAL_DESCRIPTOR_INVALID");
  }
}
const REGISTRY = descriptorRegistry();

function own(value, key) { return Object.hasOwn(value, key) ? value[key] : undefined; }
function numericRule(rules, name) {
  const direct = own(rules, name);
  if (direct !== undefined) return Number(direct);
  if (rules.greaterThan?.case === name || rules.lessThan?.case === name) return Number(rules.greaterThan?.case === name ? rules.greaterThan.value : rules.lessThan.value);
  return undefined;
}
function enumLabels(field) {
  const unspecified = field.enum.values.find(({ number }) => number === 0);
  if (unspecified === undefined || !unspecified.name.endsWith("_UNSPECIFIED")) reject("MEDIA_CANONICAL_DESCRIPTOR_PARITY");
  const prefix = unspecified.name.slice(0, -"UNSPECIFIED".length);
  return Object.fromEntries(field.enum.values.filter(({ number }) => number !== 0).map(({ name, number }) => {
    if (!name.startsWith(prefix)) reject("MEDIA_CANONICAL_DESCRIPTOR_PARITY");
    return [name.slice(prefix.length).toLowerCase(), number];
  }));
}
function fieldModel(field, extension, error) {
  const rules = getOption(field, extension).type;
  if (field.fieldKind === "enum" && rules.case === "enum") {
    const values = enumLabels(field);
    if (!rules.value.definedOnly || !rules.value.notIn.includes(0)) reject("MEDIA_CANONICAL_DESCRIPTOR_PARITY");
    return { key: field.jsonName, localName: field.localName, number: field.number, kind: "enum", values, error };
  }
  if (field.fieldKind !== "scalar") reject("MEDIA_CANONICAL_DESCRIPTOR_PARITY");
  if (rules.case === "string" && field.scalar === 9) {
    const value = rules.value;
    return {
      key: field.jsonName, localName: field.localName, number: field.number, kind: "string", error,
      minBytes: Number(value.minBytes ?? 0n), maxBytes: Number(value.maxBytes ?? 0n),
      minLength: Number(value.minLen ?? 0n), maxLength: Number(value.maxLen ?? 0n),
      pattern: value.pattern ?? "",
    };
  }
  if (rules.case === "uint32" && field.scalar === 13) {
    return {
      key: field.jsonName, localName: field.localName, number: field.number, kind: "uint32", error,
      constValue: own(rules.value, "const") === undefined ? undefined : Number(rules.value.const),
      minimum: numericRule(rules.value, "gte"), maximum: numericRule(rules.value, "lte"),
    };
  }
  reject("MEDIA_CANONICAL_DESCRIPTOR_PARITY");
}

function loadModel() {
  let manifest;
  try { manifest = JSON.parse(readFileSync(MANIFEST_PATH, "utf8")); }
  catch { reject("MEDIA_CANONICAL_MANIFEST_INVALID"); }
  if (manifest.schema_version !== 1 || manifest.algorithm !== "SHA256_DETERMINISTIC_PROTOBUF_V1" || manifest.unknown_fields !== "reject" || manifest.unicode_normalization !== "none" || !HEX.test(manifest.domain_separator_hex)) reject("MEDIA_CANONICAL_MANIFEST_INVALID");
  const registry = REGISTRY;
  const extension = registry.getExtension("buf.validate.field");
  const root = registry.getMessage(manifest.message);
  if (extension === undefined || root === undefined) reject("MEDIA_CANONICAL_DESCRIPTOR_PARITY");
  const rootFields = new Map(root.fields.map((field) => [field.name, field]));
  const contract = rootFields.get("contract_major");
  const definition = rootFields.get("definition_revision_ref");
  const spec = rootFields.get(manifest.kind);
  if (root.fields.length !== 3 || contract === undefined || definition === undefined || spec?.fieldKind !== "message" || spec.oneof === undefined || spec.oneof.fields.length !== 1) reject("MEDIA_CANONICAL_DESCRIPTOR_PARITY");
  const errors = manifest.input_errors;
  if (errors === null || typeof errors !== "object") reject("MEDIA_CANONICAL_MANIFEST_INVALID");
  const contractModel = fieldModel(contract, extension, errors[contract.jsonName]);
  const definitionModel = fieldModel(definition, extension, errors[definition.jsonName]);
  const nestedFields = spec.message.fields.map((field) => fieldModel(field, extension, errors[field.jsonName]));
  const inputKeys = [contract.jsonName, definition.jsonName, "kind", ...nestedFields.map(({ key }) => key)].sort();
  const expectedErrors = ["$input", "$shape", "$accessor", ...inputKeys].sort();
  if (JSON.stringify(Object.keys(errors).sort()) !== JSON.stringify(expectedErrors) || Object.values(errors).some((code) => typeof code !== "string" || !/^MEDIA_CANONICAL_[A-Z_]+$/u.test(code))) reject("MEDIA_CANONICAL_MANIFEST_INVALID");
  return Object.freeze({
    domainSeparator: [...Buffer.from(manifest.domain_separator_hex, "hex")],
    kind: manifest.kind,
    errors,
    inputKeys,
    root: {
      typeName: root.typeName,
      contract: contractModel,
      definition: definitionModel,
      specNumber: spec.number,
      specLocalName: spec.localName,
      specOneofLocalName: spec.oneof.localName,
    },
    nested: { typeName: spec.message.typeName, fields: nestedFields },
  });
}

function deepFreeze(value) {
  if (value !== null && typeof value === "object" && !Object.isFrozen(value)) {
    for (const nested of Object.values(value)) deepFreeze(nested);
    Object.freeze(value);
  }
  return value;
}
const MEDIA_CANONICAL_MODEL = deepFreeze(loadModel());

function plainOwnObject(value) {
  if (value === null || typeof value !== "object" || Array.isArray(value)) return false;
  const prototype = Object.getPrototypeOf(value);
  return prototype === Object.prototype || prototype === null;
}
function unicodeScalars(value) {
  for (let index = 0; index < value.length; index += 1) {
    const unit = value.charCodeAt(index);
    if (unit >= 0xd800 && unit <= 0xdbff) {
      const next = value.charCodeAt(index + 1);
      if (!(next >= 0xdc00 && next <= 0xdfff)) return false;
      index += 1;
    } else if (unit >= 0xdc00 && unit <= 0xdfff) return false;
  }
  return true;
}
function validateField(value, field) {
  if (field.kind === "string") {
    if (typeof value !== "string" || !unicodeScalars(value)) reject(field.error);
    const bytes = new TextEncoder().encode(value).length;
    const length = [...value].length;
    if ((field.minBytes && bytes < field.minBytes) || (field.maxBytes && bytes > field.maxBytes) || (field.minLength && length < field.minLength) || (field.maxLength && length > field.maxLength) || (field.pattern && !new RegExp(field.pattern, "u").test(value))) reject(field.error);
  } else if (field.kind === "uint32") {
    if (!Number.isInteger(value) || value < 0 || value > 0xffff_ffff || (field.constValue !== undefined && value !== field.constValue) || (field.minimum !== undefined && value < field.minimum) || (field.maximum !== undefined && value > field.maximum)) reject(field.error);
  } else if (typeof value !== "string" || !Object.hasOwn(field.values, value)) reject(field.error);
}
function snapshotInput(input) {
  if (!plainOwnObject(input)) reject(MEDIA_CANONICAL_MODEL.errors.$input);
  const descriptors = Object.getOwnPropertyDescriptors(input);
  const keys = Reflect.ownKeys(descriptors);
  if (keys.some((key) => typeof key !== "string")) reject(MEDIA_CANONICAL_MODEL.errors.$shape);
  const sorted = keys.sort();
  if (JSON.stringify(sorted) !== JSON.stringify(MEDIA_CANONICAL_MODEL.inputKeys)) reject(MEDIA_CANONICAL_MODEL.errors.$shape);
  const snapshot = Object.create(null);
  for (const key of MEDIA_CANONICAL_MODEL.inputKeys) {
    const descriptor = descriptors[key];
    if (descriptor === undefined || !("value" in descriptor)) reject(MEDIA_CANONICAL_MODEL.errors.$accessor);
    Object.defineProperty(snapshot, key, { value: descriptor.value, enumerable: true });
  }
  return Object.freeze(snapshot);
}
function validatedInput(input) {
  const value = snapshotInput(input);
  validateField(value[MEDIA_CANONICAL_MODEL.root.contract.key], MEDIA_CANONICAL_MODEL.root.contract);
  validateField(value[MEDIA_CANONICAL_MODEL.root.definition.key], MEDIA_CANONICAL_MODEL.root.definition);
  if (value.kind !== MEDIA_CANONICAL_MODEL.kind) reject(MEDIA_CANONICAL_MODEL.errors.kind);
  for (const field of MEDIA_CANONICAL_MODEL.nested.fields) validateField(value[field.key], field);
  return value;
}

export function canonicalMediaOperationInputV1Bytes(input) {
  const value = validatedInput(input);
  const root = REGISTRY.getMessage(MEDIA_CANONICAL_MODEL.root.typeName);
  const nestedDescriptor = REGISTRY.getMessage(MEDIA_CANONICAL_MODEL.nested.typeName);
  const nested = {};
  for (const field of MEDIA_CANONICAL_MODEL.nested.fields) nested[field.localName] = field.kind === "enum" ? field.values[value[field.key]] : value[field.key];
  const message = create(root, {
    [MEDIA_CANONICAL_MODEL.root.contract.localName]: value[MEDIA_CANONICAL_MODEL.root.contract.key],
    [MEDIA_CANONICAL_MODEL.root.definition.localName]: value[MEDIA_CANONICAL_MODEL.root.definition.key],
    [MEDIA_CANONICAL_MODEL.root.specOneofLocalName]: {
      case: MEDIA_CANONICAL_MODEL.root.specLocalName,
      value: create(nestedDescriptor, nested),
    },
  });
  return toBinary(root, message, { writeUnknownFields: false });
}
export function mediaCallerRequestFingerprintPreimage(input) { return Uint8Array.from([...MEDIA_CANONICAL_MODEL.domainSeparator, ...canonicalMediaOperationInputV1Bytes(input)]); }
export function mediaCallerRequestFingerprintSha256(input) { return createHash("sha256").update(mediaCallerRequestFingerprintPreimage(input)).digest("hex"); }

function typescriptType(model) {
  const properties = [];
  for (const field of [model.root.contract, model.root.definition]) {
    const type = field.constValue !== undefined ? String(field.constValue) : "string";
    properties.push(`${field.key}: ${type}`);
  }
  properties.push(`kind: ${JSON.stringify(model.kind)}`);
  for (const field of model.nested.fields) {
    let type = field.kind === "string" ? "string" : "number";
    if (field.kind === "enum") type = Object.keys(field.values).map(JSON.stringify).join(" | ");
    else if (field.kind === "uint32" && field.minimum !== undefined && field.maximum !== undefined && field.maximum - field.minimum <= 32) type = Array.from({ length: field.maximum - field.minimum + 1 }, (_, index) => field.minimum + index).join(" | ");
    properties.push(`${field.key}: ${type}`);
  }
  return `Readonly<{ ${properties.join("; ")} }>`;
}
function runtimeSharedTypescript(model) {
  return `const model = ${JSON.stringify(model)} as const;
export class MediaCanonicalError extends Error { readonly code: string; constructor(code: string) { super(code); this.name = "MediaCanonicalError"; this.code = code; } }
function reject(code: string): never { throw new MediaCanonicalError(code); }
function concat(...parts: Uint8Array[]): Uint8Array { const result = new Uint8Array(parts.reduce((total, part) => total + part.length, 0)); let offset = 0; for (const part of parts) { result.set(part, offset); offset += part.length; } return result; }
function varint(value: number): Uint8Array { const encoded: number[] = []; let remaining = value; while (remaining > 127) { encoded.push((remaining & 127) | 128); remaining = Math.floor(remaining / 128); } encoded.push(remaining); return Uint8Array.from(encoded); }
function scalar(field: number, value: number): Uint8Array { return concat(varint(field << 3), varint(value)); }
function bytes(field: number, value: string | Uint8Array): Uint8Array { const encoded = typeof value === "string" ? new TextEncoder().encode(value) : value; return concat(varint((field << 3) | 2), varint(encoded.length), encoded); }
function unicodeScalars(value: string): boolean { for (let index = 0; index < value.length; index += 1) { const unit = value.charCodeAt(index); if (unit >= 0xd800 && unit <= 0xdbff) { const next = value.charCodeAt(index + 1); if (!(next >= 0xdc00 && next <= 0xdfff)) return false; index += 1; } else if (unit >= 0xdc00 && unit <= 0xdfff) return false; } return true; }
function validateField(value: unknown, field: any): void { if (field.kind === "string") { if (typeof value !== "string" || !unicodeScalars(value)) reject(field.error); const byteLength = new TextEncoder().encode(value).length; const length = [...value].length; if ((field.minBytes && byteLength < field.minBytes) || (field.maxBytes && byteLength > field.maxBytes) || (field.minLength && length < field.minLength) || (field.maxLength && length > field.maxLength) || (field.pattern && !new RegExp(field.pattern, "u").test(value))) reject(field.error); } else if (field.kind === "uint32") { if (!Number.isInteger(value) || (value as number) < 0 || (value as number) > 0xffff_ffff || (field.constValue !== undefined && value !== field.constValue) || (field.minimum !== undefined && (value as number) < field.minimum) || (field.maximum !== undefined && (value as number) > field.maximum)) reject(field.error); } else if (typeof value !== "string" || !Object.hasOwn(field.values, value)) reject(field.error); }
function snapshot(input: unknown): Readonly<Record<string, unknown>> { if (input === null || typeof input !== "object" || Array.isArray(input) || ![Object.prototype,null].includes(Object.getPrototypeOf(input))) reject(model.errors.$input); const descriptors = Object.getOwnPropertyDescriptors(input); const keys = Reflect.ownKeys(descriptors); if (keys.some((key) => typeof key !== "string") || JSON.stringify((keys as string[]).sort()) !== JSON.stringify(model.inputKeys)) reject(model.errors.$shape); const result = Object.create(null) as Record<string,unknown>; for (const key of model.inputKeys) { const descriptor = descriptors[key]; if (descriptor === undefined || !("value" in descriptor)) reject(model.errors.$accessor); Object.defineProperty(result,key,{value:descriptor.value,enumerable:true}); } return Object.freeze(result); }
function validated(input: unknown): Readonly<Record<string,unknown>> { const value=snapshot(input); validateField(value[model.root.contract.key],model.root.contract); validateField(value[model.root.definition.key],model.root.definition); if(value.kind!==model.kind) reject(model.errors.kind); for(const field of model.nested.fields) validateField(value[field.key],field); return value; }
`;
}
function typescriptSource(model) {
  return `// Generated by contract/generate-media-canonical.mjs from Buf descriptors + media-canonicalization.yaml. Do not edit.
export type CanonicalMediaOperationInputV1 = ${typescriptType(model)};
${runtimeSharedTypescript(model)}
export function canonicalMediaOperationInputV1Bytes(input: unknown): Uint8Array { const value=validated(input); const nested=[...model.nested.fields].sort((a,b)=>a.number-b.number).map((field)=>field.kind==="string"?bytes(field.number,value[field.key] as string):scalar(field.number,field.kind==="enum"?field.values[value[field.key] as keyof typeof field.values]:value[field.key] as number)); const root=[scalar(model.root.contract.number,value[model.root.contract.key] as number),bytes(model.root.definition.number,value[model.root.definition.key] as string),bytes(model.root.specNumber,concat(...nested))]; return concat(...root); }
export function mediaCallerRequestFingerprintPreimage(input: unknown): Uint8Array { return concat(Uint8Array.from(model.domainSeparator),canonicalMediaOperationInputV1Bytes(input)); }
export async function mediaCallerRequestFingerprintSha256(input: unknown): Promise<string> { const preimage=mediaCallerRequestFingerprintPreimage(input); const owned=new ArrayBuffer(preimage.byteLength); new Uint8Array(owned).set(preimage); const digest=await crypto.subtle.digest("SHA-256",owned); return Array.from(new Uint8Array(digest),(byte)=>byte.toString(16).padStart(2,"0")).join(""); }
export type MediaCallerRequestFingerprintHeaders = Readonly<{ "X-Kokoro-Caller-Request-Fingerprint": string }>;
export async function mediaCallerRequestFingerprintHeaders(input: unknown): Promise<MediaCallerRequestFingerprintHeaders> { return {"X-Kokoro-Caller-Request-Fingerprint":await mediaCallerRequestFingerprintSha256(input)}; }
`;
}

function pythonSource(model) {
  const serialized = JSON.stringify(model);
  return `# Generated by contract/generate-media-canonical.mjs from Buf descriptors + media-canonicalization.yaml. Do not edit.\nfrom __future__ import annotations\nimport hashlib\nimport json\nimport re\nfrom typing import Any\n\nMODEL = json.loads(${JSON.stringify(serialized)})\n\nclass MediaCanonicalError(ValueError):\n    def __init__(self, code: str) -> None:\n        self.code = code\n        super().__init__(code)\n\ndef _reject(code: str) -> None:\n    raise MediaCanonicalError(code)\n\ndef _varint(value: int) -> bytes:\n    result=bytearray()\n    while value>127:\n        result.append((value&127)|128); value >>= 7\n    result.append(value); return bytes(result)\n\ndef _scalar(field: int, value: int) -> bytes:\n    return _varint(field<<3)+_varint(value)\n\ndef _bytes(field: int, value: str|bytes) -> bytes:\n    encoded=value.encode("utf-8","strict") if isinstance(value,str) else value\n    return _varint((field<<3)|2)+_varint(len(encoded))+encoded\n\ndef _validate_field(value: Any, field: dict[str,Any]) -> None:\n    if field["kind"]=="string":\n        if type(value) is not str or any(0xD800 <= ord(c) <= 0xDFFF for c in value): _reject(field["error"])\n        try: byte_length=len(value.encode("utf-8","strict"))\n        except UnicodeEncodeError: _reject(field["error"])\n        length=len(value)\n        if (field.get("minBytes") and byte_length<field["minBytes"]) or (field.get("maxBytes") and byte_length>field["maxBytes"]) or (field.get("minLength") and length<field["minLength"]) or (field.get("maxLength") and length>field["maxLength"]) or (field.get("pattern") and re.fullmatch(field["pattern"],value,flags=re.ASCII) is None): _reject(field["error"])\n    elif field["kind"]=="uint32":\n        if type(value) is not int or value<0 or value>0xFFFFFFFF or ("constValue" in field and value!=field["constValue"]) or ("minimum" in field and value<field["minimum"]) or ("maximum" in field and value>field["maximum"]): _reject(field["error"])\n    elif type(value) is not str or value not in field["values"]: _reject(field["error"])\n\ndef _validated(input_value: object) -> dict[str,Any]:\n    if type(input_value) is not dict: _reject(MODEL["errors"]["$input"])\n    value=input_value.copy()\n    if not all(type(key) is str for key in value) or sorted(value)!=MODEL["inputKeys"]: _reject(MODEL["errors"]["$shape"])\n    _validate_field(value[MODEL["root"]["contract"]["key"]],MODEL["root"]["contract"]); _validate_field(value[MODEL["root"]["definition"]["key"]],MODEL["root"]["definition"])\n    if value["kind"]!=MODEL["kind"]: _reject(MODEL["errors"]["kind"])\n    for field in MODEL["nested"]["fields"]: _validate_field(value[field["key"]],field)\n    return value\n\ndef canonical_media_operation_input_v1_bytes(input_value: object) -> bytes:\n    value=_validated(input_value); nested=[]\n    for field in sorted(MODEL["nested"]["fields"],key=lambda item:item["number"]):\n        encoded=value[field["key"]] if field["kind"]!="enum" else field["values"][value[field["key"]]]\n        nested.append(_bytes(field["number"],encoded) if field["kind"]=="string" else _scalar(field["number"],encoded))\n    root=MODEL["root"]\n    return _scalar(root["contract"]["number"],value[root["contract"]["key"]])+_bytes(root["definition"]["number"],value[root["definition"]["key"]])+_bytes(root["specNumber"],b"".join(nested))\n\ndef media_caller_request_fingerprint_sha256(input_value: object) -> str:\n    return hashlib.sha256(bytes(MODEL["domainSeparator"])+canonical_media_operation_input_v1_bytes(input_value)).hexdigest()\n`;
}

export const MEDIA_CANONICAL_TYPESCRIPT_SOURCE = typescriptSource(MEDIA_CANONICAL_MODEL);
export const MEDIA_CANONICAL_PYTHON_SOURCE = pythonSource(MEDIA_CANONICAL_MODEL);

function materialize(testCase) { return testCase.promptRepeat ? { ...testCase.input, promptIntent: testCase.promptRepeat.scalar.repeat(testCase.promptRepeat.count) } : testCase.input; }
function validateCorpus() {
  const corpus = JSON.parse(readFileSync(CORPUS, "utf8"));
  if (corpus.schemaVersion !== 1 || !Array.isArray(corpus.cases) || corpus.cases.length < 16) reject("MEDIA_CANONICAL_CORPUS_SHAPE_INVALID");
  const ids = new Set();
  for (const testCase of corpus.cases) {
    if (ids.has(testCase.id)) reject("MEDIA_CANONICAL_CORPUS_DUPLICATE_ID"); ids.add(testCase.id);
    try {
      const input = materialize(testCase); const encoded = canonicalMediaOperationInputV1Bytes(input);
      if (testCase.errorCode) reject("MEDIA_CANONICAL_CORPUS_EXPECTED_REJECTION");
      if (testCase.canonicalHex && Buffer.from(encoded).toString("hex") !== testCase.canonicalHex) reject(`MEDIA_CANONICAL_CORPUS_BYTES_MISMATCH:${testCase.id}`);
      if (testCase.canonicalLength !== undefined && encoded.length !== testCase.canonicalLength) reject(`MEDIA_CANONICAL_CORPUS_LENGTH_MISMATCH:${testCase.id}`);
      if (mediaCallerRequestFingerprintSha256(input) !== testCase.fingerprintSha256) reject(`MEDIA_CANONICAL_CORPUS_FINGERPRINT_MISMATCH:${testCase.id}`);
    } catch (error) { if (!testCase.errorCode || error.code !== testCase.errorCode) throw error; }
  }
}
function parseArgs(argv) {
  let output; let validate = false; let language = "typescript";
  for (let index=0; index<argv.length; index+=1) {
    if (argv[index] === "--output") output=argv[++index];
    else if (argv[index] === "--validate-corpus") validate=true;
    else if (argv[index] === "--language") language=argv[++index];
    else reject(`MEDIA_CANONICAL_ARGUMENT_UNKNOWN:${argv[index]}`);
  }
  if (!output || !isAbsolute(output) || !["typescript","python"].includes(language)) reject("MEDIA_CANONICAL_OUTPUT_REQUIRED");
  const canonicalOutput=resolve(realpathSync(dirname(resolve(output))),basename(output)); const relativeOutput=relative(realpathSync(tmpdir()),canonicalOutput);
  if (relativeOutput.startsWith("..") || isAbsolute(relativeOutput)) reject("MEDIA_CANONICAL_OUTPUT_MUST_BE_TEMPORARY");
  return {output:canonicalOutput,validate,language};
}
function main() { const {output,validate,language}=parseArgs(process.argv.slice(2)); if(validate) validateCorpus(); writeFileSync(output,language==="python"?MEDIA_CANONICAL_PYTHON_SOURCE:MEDIA_CANONICAL_TYPESCRIPT_SOURCE,{encoding:"utf8",flag:"wx"}); process.stdout.write(`media_canonical_generated:${output}\n`); }
if (import.meta.url === pathToFileURL(process.argv[1] ?? "").href) main();
