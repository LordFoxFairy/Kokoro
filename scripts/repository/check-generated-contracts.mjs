#!/usr/bin/env node

import { execFile } from "node:child_process";
import { mkdtemp, readFile, readdir, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, relative, resolve } from "node:path";
import { promisify } from "node:util";
import { fileURLToPath } from "node:url";

const execFileAsync = promisify(execFile);
const SCRIPT_PATH = fileURLToPath(import.meta.url);
const DEFAULT_MIRRORS = [
  "kokoro-platform/kokoro-platform-admin/src/generated/contracts",
  "kokoro-web/apps/admin/lib/generated/contracts",
];

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

async function generateToTemporaryDirectory(root, output) {
  const contract = resolve(root, "contract");
  const command = process.platform === "win32" ? "pnpm.cmd" : "pnpm";
  try {
    await execFileAsync(
      command,
      generationCommandArguments(contract, output),
      { cwd: root, timeout: 120_000, maxBuffer: 1024 * 1024 },
    );
  } catch (error) {
    const code = error?.killed ? "generated_contract_timeout" : "generated_contract_generation_failed";
    throw new GeneratedContractError(code);
  }
}

export function generationCommandArguments(contract, output) {
  return ["--dir", contract, "run", "buf:generate", "--output", output];
}

export async function checkGeneratedContracts({ root }) {
  const temporary = await mkdtemp(resolve(tmpdir(), "kokoro-generated-contracts-"));
  const output = resolve(temporary, "generated");
  try {
    await generateToTemporaryDirectory(root, output);
    for (const mirror of DEFAULT_MIRRORS) {
      await compareGeneratedMirror(output, resolve(root, mirror), mirror);
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
