#!/usr/bin/env node

import { execFile } from "node:child_process";
import { mkdtemp, readFile, readdir, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, relative, resolve } from "node:path";
import { promisify } from "node:util";
import { fileURLToPath } from "node:url";

const execFileAsync = promisify(execFile);
const SCRIPT_PATH = fileURLToPath(import.meta.url);
export const GENERATED_BOUNDARIES = Object.freeze([
  Object.freeze({
    id: "platform-admin-auth@v1",
    mirrors: Object.freeze([
      "kokoro-platform/kokoro-platform-admin/src/generated/contracts",
    ]),
  }),
  Object.freeze({
    id: "platform-admin-identity@v1",
    mirrors: Object.freeze([
      "kokoro-platform/src/interfaces/connect/generated-admin-identity",
      "kokoro-web/apps/admin/lib/generated/admin-identity",
    ]),
  }),
  Object.freeze({
    id: "platform-admin-query@v2",
    mirrors: Object.freeze([
      "kokoro-platform/src/interfaces/connect/generated-admin-query-v2",
      "kokoro-web/apps/admin/lib/generated/admin-query-v2",
    ]),
  }),
  Object.freeze({
    id: "platform-admin-commerce@v1",
    mirrors: Object.freeze([
      "kokoro-platform/src/interfaces/connect/generated-admin-commerce",
      "kokoro-web/apps/admin/lib/generated/admin-commerce",
    ]),
  }),
  Object.freeze({
    id: "platform-admin-credit@v1",
    mirrors: Object.freeze([
      "kokoro-platform/src/interfaces/connect/generated-admin-credit",
      "kokoro-web/apps/admin/lib/generated/admin-credit",
    ]),
  }),
  Object.freeze({
    id: "platform-admission@v1",
    mirrors: Object.freeze([
      "kokoro-platform/src/interfaces/connect/generated",
      "kokoro-session/src/platform/generated",
    ]),
  }),
  Object.freeze({
    id: "platform-asset-eligibility@v1",
    mirrors: Object.freeze([
      "kokoro-platform/src/interfaces/connect/generated-asset-eligibility",
      "kokoro-session/src/platform/asset-eligibility-generated",
    ]),
  }),
  Object.freeze({
    id: "platform-model-control@v1",
    mirrors: Object.freeze([
      "kokoro-platform/src/interfaces/connect/generated-model-control",
      "kokoro-web/apps/admin/lib/generated/model-control",
    ]),
  }),
  Object.freeze({
    id: "platform-session-authorization@v2",
    mirrors: Object.freeze([
      "kokoro-platform/src/interfaces/connect/generated-authorization-v2",
      "kokoro-session/src/platform/authorization-v2-generated",
    ]),
  }),
  Object.freeze({
    id: "session-dispatch-owner-evidence@v1",
    mirrors: Object.freeze([
      "kokoro-session/src/platform/evidence-generated",
      "kokoro-platform/src/interfaces/connect/generated-session-evidence",
    ]),
  }),
  Object.freeze({
    id: "session-admission-owner@v1",
    mirrors: Object.freeze([
      "kokoro-session/src/platform/admission-owner-generated",
      "kokoro-platform/src/interfaces/connect/generated-session-admission-owner",
    ]),
  }),
  Object.freeze({
    id: "platform-public@v1",
    mirrors: Object.freeze([
      "kokoro-platform/src/interfaces/http/generated/platform-public",
      "kokoro-web/packages/site-client/src/generated/platform-public",
    ]),
  }),
]);
// Contract-only bundles are generated in isolation in CI, but have no live subrepository mirrors
// until provider, consumer, and compatibility evidence authorize promotion.
export const CONTRACT_ONLY_GENERATED_BOUNDARIES = Object.freeze([
  "platform-admin-command@v2",
  "platform-site-lifecycle@v1",
  "platform-site-provisioning@v1",
  "platform-product-catalog-publication@v1",
  "platform-site-publication@v1",
  "platform-site-evidence-admission@v1",
  "platform-session-authorization@v1",
  "agent-execution-evidence@v1",
  "platform-media-runtime@v1",
  "model-image-effect@v1",
  "session-media-projection@v1",
  "session-media-projection-ingest@v1",
  "platform-media-projection-recovery@v1",
  "platform-credit-cost-projection-recovery@v1",
]);

export class GeneratedContractError extends Error {
  constructor(code, detail = "") {
    super(detail);
    this.name = "GeneratedContractError";
    this.code = code;
  }
}

export function parseArguments(argv) {
  const options = { root: process.cwd() };
  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    const value = argv[index + 1];
    if (argument !== "--root" || !value) {
      throw new GeneratedContractError("generated_contract_arguments_invalid", argument ?? "");
    }
    options.root = resolve(value);
    index += 1;
  }
  return options;
}

async function listFiles(root, directory = root) {
  let entries;
  try {
    entries = await readdir(directory, { withFileTypes: true });
  } catch (error) {
    if (error?.code === "ENOENT") {
      throw new GeneratedContractError("generated_contract_drift", relative(root, directory) || ".");
    }
    throw error;
  }
  const files = [];
  for (const entry of entries.sort((left, right) => left.name.localeCompare(right.name))) {
    const path = resolve(directory, entry.name);
    if (entry.isDirectory()) files.push(...(await listFiles(root, path)));
    else if (entry.isFile()) files.push(relative(root, path));
    else throw new GeneratedContractError("generated_contract_drift", entry.name);
  }
  return files;
}

export async function compareGeneratedMirror(expectedRoot, mirrorRoot, label) {
  const [expectedFiles, mirrorFiles] = await Promise.all([
    listFiles(expectedRoot),
    listFiles(mirrorRoot),
  ]);
  if (
    expectedFiles.length !== mirrorFiles.length ||
    expectedFiles.some((path, index) => path !== mirrorFiles[index])
  ) {
    throw new GeneratedContractError("generated_contract_drift", label);
  }
  for (const path of expectedFiles) {
    const [expected, actual] = await Promise.all([
      readFile(resolve(expectedRoot, path)),
      readFile(resolve(mirrorRoot, path)),
    ]);
    if (!expected.equals(actual)) {
      throw new GeneratedContractError("generated_contract_drift", `${label}:${path}`);
    }
  }
}

export async function assertGeneratedMirrorTracked(root, mirror, label) {
  const [repositoryName, ...relativeParts] = mirror.split("/");
  if (!repositoryName || relativeParts.length === 0) {
    throw new GeneratedContractError("generated_contract_repository_invalid", label);
  }
  const repository = resolve(root, repositoryName);
  const relativeMirror = relativeParts.join("/");
  const files = await listFiles(resolve(root, mirror));
  let stdout;
  try {
    ({ stdout } = await execFileAsync(
      "git",
      ["-C", repository, "ls-files", "--", relativeMirror],
      { cwd: root, timeout: 10_000, maxBuffer: 1024 * 1024 },
    ));
  } catch {
    throw new GeneratedContractError("generated_contract_repository_invalid", label);
  }
  const tracked = new Set(stdout.split(/\r?\n/u).filter(Boolean));
  const missing = files
    .map((path) => `${relativeMirror}/${path}`)
    .filter((path) => !tracked.has(path));
  if (missing.length > 0) {
    throw new GeneratedContractError("generated_contract_untracked", `${label}:${missing[0]}`);
  }
}

async function generateToTemporaryDirectory(root, boundary, output) {
  const contract = resolve(root, "contract");
  const command = process.platform === "win32" ? "corepack.cmd" : "corepack";
  try {
    const packageManifest = JSON.parse(await readFile(resolve(contract, "package.json"), "utf8"));
    await execFileAsync(
      command,
      [
        pinnedPnpmSpecifier(packageManifest.packageManager),
        ...generationCommandArguments(contract, boundary, output),
      ],
      { cwd: root, timeout: 120_000, maxBuffer: 1024 * 1024 },
    );
  } catch (error) {
    const code = error?.killed ? "generated_contract_timeout" : "generated_contract_generation_failed";
    throw new GeneratedContractError(code);
  }
}

export function pinnedPnpmSpecifier(packageManager) {
  if (typeof packageManager !== "string" || !/^pnpm@[1-9][0-9]*\.[0-9]+\.[0-9]+$/u.test(packageManager)) {
    throw new GeneratedContractError("generated_contract_package_manager_invalid");
  }
  return packageManager;
}

export function generationCommandArguments(contract, boundary, output) {
  if (boundary === "platform-public@v1") {
    return [
      "--dir",
      contract,
      "run",
      "openapi:generate:public",
      "--output",
      output,
    ];
  }
  return [
    "--dir",
    contract,
    "run",
    "buf:generate",
    "--boundary",
    boundary,
    "--output",
    output,
  ];
}

export async function checkGeneratedContracts({ root }) {
  const temporary = await mkdtemp(resolve(tmpdir(), "kokoro-generated-contracts-"));
  try {
    for (const boundary of GENERATED_BOUNDARIES) {
      const output = resolve(temporary, boundary.id);
      await generateToTemporaryDirectory(root, boundary.id, output);
      for (const mirror of boundary.mirrors) {
        await compareGeneratedMirror(output, resolve(root, mirror), `${boundary.id}:${mirror}`);
        await assertGeneratedMirrorTracked(root, mirror, `${boundary.id}:${mirror}`);
      }
    }
    for (const boundary of CONTRACT_ONLY_GENERATED_BOUNDARIES) {
      await generateToTemporaryDirectory(root, boundary, resolve(temporary, boundary));
    }
  } finally {
    await rm(temporary, { recursive: true, force: true });
  }
}

async function main() {
  try {
    const options = parseArguments(process.argv.slice(2));
    await checkGeneratedContracts(options);
    process.stdout.write("OK — generated contract mirrors match\n");
  } catch (error) {
    const code = error instanceof GeneratedContractError ? error.code : "generated_contract_check_failed";
    process.stderr.write(`${code}\n`);
    process.exitCode = 1;
  }
}

if (process.argv[1] && resolve(process.argv[1]) === resolve(SCRIPT_PATH)) {
  await main();
}
