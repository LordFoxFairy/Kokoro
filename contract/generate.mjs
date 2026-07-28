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
  }),
  "platform-admin-identity@v1": Object.freeze({
    schema: "kokoro.platform.identity.v1.AdminIdentityService",
    version: 1,
    inputs: Object.freeze(["proto/kokoro/platform/identity/v1/admin_identity.proto"]),
    sources: Object.freeze([
      "kokoro/common/v1/error.proto",
      "kokoro/common/v1/receipt.proto",
      "kokoro/platform/admin/v2/admin_control.proto",
      "kokoro/platform/identity/v1/admin_identity.proto",
    ]),
    helper: null,
  }),
  "platform-admin-query@v2": Object.freeze({
    schema: "kokoro.platform.admin.v2.AdminQueryService",
    version: 2,
    inputs: Object.freeze(["proto/kokoro/platform/admin/v2/admin_control.proto"]),
    sources: Object.freeze([
      "kokoro/common/v1/error.proto",
      "kokoro/common/v1/receipt.proto",
      "kokoro/platform/admin/v2/admin_control.proto",
    ]),
    helper: null,
  }),
  "platform-admin-command@v2": Object.freeze({
    schema: "kokoro.platform.admin.v2.AdminCommandService",
    version: 2,
    inputs: Object.freeze(["proto/kokoro/platform/admin/v2/admin_control.proto"]),
    sources: Object.freeze([
      "kokoro/common/v1/error.proto",
      "kokoro/common/v1/receipt.proto",
      "kokoro/platform/admin/v2/admin_control.proto",
    ]),
    helper: null,
  }),
  "platform-site-lifecycle@v1": Object.freeze({
    schema: "kokoro.platform.site.v1.SiteLifecycleService",
    version: 1,
    inputs: Object.freeze(["proto/kokoro/platform/site/v1/site_lifecycle.proto"]),
    sources: Object.freeze([
      "kokoro/common/v1/error.proto",
      "kokoro/common/v1/receipt.proto",
      "kokoro/platform/admin/v2/admin_control.proto",
      "kokoro/platform/site/v1/site_lifecycle.proto",
    ]),
    helper: null,
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

export { adminAuthEffectDigestSource, contractMetadata, generate, metadataSource, parseArguments };
