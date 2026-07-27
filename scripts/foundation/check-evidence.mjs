#!/usr/bin/env node

import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import { parseOwnershipYaml, validateOwnership } from "./ownership-attestation.mjs";

function fail(code, detail) {
  process.stderr.write(`${code}${detail ? `: ${detail}` : ""}\n`);
  process.exitCode = 1;
}

function parseArguments(argv) {
  let requireOwnership = false;
  let root = process.cwd();

  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    if (argument === "--require-ownership") {
      requireOwnership = true;
    } else if (argument === "--root" && argv[index + 1]) {
      root = resolve(argv[index + 1]);
      index += 1;
    } else {
      throw new Error(`unsupported argument: ${argument}`);
    }
  }

  if (!requireOwnership) {
    throw new Error("--require-ownership is required");
  }
  return { root };
}

async function main() {
  let root;
  try {
    ({ root } = parseArguments(process.argv.slice(2)));
  } catch (error) {
    fail("evidence_arguments_invalid", error.message);
    return;
  }

  const attestationPath = resolve(
    root,
    "docs/reports/evidence/wave-0/ownership-attestation.yaml",
  );
  let source;
  try {
    source = await readFile(attestationPath, "utf8");
  } catch (error) {
    if (error.code === "ENOENT") {
      fail("ownership_attestation_missing");
      return;
    }
    fail("ownership_attestation_unreadable", error.message);
    return;
  }

  try {
    const attestation = parseOwnershipYaml(source);
    const validationError = validateOwnership(attestation);
    if (validationError) {
      fail("ownership_attestation_invalid", validationError);
      return;
    }
  } catch (error) {
    fail("ownership_attestation_invalid", error.message);
    return;
  }

  process.stdout.write("ownership_attestation_valid\n");
}

await main();
