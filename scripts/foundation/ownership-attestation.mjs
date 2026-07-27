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
const PLACEHOLDER = /(?:pending|todo|placeholder)/iu;

export function parseOwnershipYaml(source) {
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

export function validateOwnership(attestation) {
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
