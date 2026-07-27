#!/usr/bin/env node

import { readFile } from "node:fs/promises";
import { resolve } from "node:path";

const EXPECTED_REPOSITORIES = [
  "Kokoro",
  "kokoro-agent",
  "kokoro-platform",
  "kokoro-session",
  "kokoro-web",
];
const REQUIRED_KEYS = [
  "attestedBy",
  "authority",
  "attestedAt",
  "attestationRef",
  "repositories",
  "licenseRef",
];
const PLACEHOLDER = /(?:pending|todo|placeholder)/i;

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

function parseOwnershipYaml(source) {
  const result = {};
  let listKey = null;

  for (const [lineIndex, rawLine] of source.split(/\r?\n/u).entries()) {
    if (rawLine.trim() === "") continue;

    if (rawLine.startsWith("  - ") && listKey === "repositories") {
      result.repositories.push(rawLine.slice(4).trim());
      continue;
    }

    if (/^\s/u.test(rawLine)) {
      throw new Error(`unsupported indentation on line ${lineIndex + 1}`);
    }

    const separator = rawLine.indexOf(":");
    if (separator <= 0) {
      throw new Error(`invalid mapping on line ${lineIndex + 1}`);
    }
    const key = rawLine.slice(0, separator).trim();
    const value = rawLine.slice(separator + 1).trim();
    if (Object.hasOwn(result, key)) {
      throw new Error(`duplicate key: ${key}`);
    }

    if (key === "repositories") {
      if (value !== "") throw new Error("repositories must be a block list");
      result.repositories = [];
      listKey = key;
    } else {
      if (value === "") throw new Error(`empty value: ${key}`);
      result[key] = value;
      listKey = null;
    }
  }

  return result;
}

function validateOwnership(attestation) {
  const keys = Object.keys(attestation);
  if (
    keys.length !== REQUIRED_KEYS.length ||
    REQUIRED_KEYS.some((key) => !Object.hasOwn(attestation, key))
  ) {
    return "required fields or additional properties do not match the contract";
  }

  for (const key of REQUIRED_KEYS.filter((key) => key !== "repositories")) {
    const value = attestation[key];
    if (typeof value !== "string" || value.trim() === "" || PLACEHOLDER.test(value)) {
      return `${key} is empty or contains a placeholder`;
    }
  }

  if (attestation.authority !== "repository-owner") {
    return "authority must be repository-owner";
  }
  if (attestation.licenseRef !== "LicenseRef-Kokoro-Internal-Proprietary") {
    return "licenseRef does not match the approved internal license reference";
  }
  if (
    !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$/u.test(
      attestation.attestedAt,
    ) ||
    Number.isNaN(Date.parse(attestation.attestedAt))
  ) {
    return "attestedAt must be an ISO 8601 date-time";
  }

  if (!Array.isArray(attestation.repositories)) {
    return "repositories must be a list";
  }
  const actualRepositories = [...attestation.repositories].sort();
  const expectedRepositories = [...EXPECTED_REPOSITORIES].sort();
  if (
    actualRepositories.length !== expectedRepositories.length ||
    actualRepositories.some((repository, index) => repository !== expectedRepositories[index])
  ) {
    return "repositories must contain the exact approved repository set";
  }

  return null;
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
