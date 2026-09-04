import { readFileSync } from 'node:fs';

import { parseDocument } from 'yaml';

const PUBLIC_CONTRACT = Object.freeze({
  owner: 'kokoro-bff',
  repository: 'https://github.com/LordFoxFairy/kokoro-bff.git',
  sourcePath: 'contract/openapi/v1/openapi.yaml',
});

function assertRecord(value, label) {
  if (value === null || typeof value !== 'object' || Array.isArray(value)) {
    throw new CatalogError(`${label} must be a mapping`);
  }
  return value;
}

function assertKeys(record, allowedKeys, label) {
  const unknownKeys = Object.keys(record).filter(
    (key) => !allowedKeys.includes(key),
  );
  if (unknownKeys.length > 0) {
    throw new CatalogError(
      `${label} contains unknown keys: ${unknownKeys.sort().join(', ')}`,
    );
  }
}

function requiredString(record, key, label) {
  const value = record[key];
  if (typeof value !== 'string' || value.trim() === '') {
    throw new CatalogError(`${label}.${key} must be a non-empty string`);
  }
  return value;
}

function parseEntry(value, index) {
  const label = `contracts[${index}]`;
  const entry = assertRecord(value, label);
  assertKeys(
    entry,
    [
      'id',
      'owner',
      'visibility',
      'version',
      'source',
      'digest',
      'generation',
      'publication',
    ],
    label,
  );

  const id = requiredString(entry, 'id', label);
  const owner = requiredString(entry, 'owner', label);
  const visibility = requiredString(entry, 'visibility', label);
  const version = requiredString(entry, 'version', label);
  if (id !== 'kokoro-bff-public-v1') {
    throw new CatalogError(`${label}.id must be kokoro-bff-public-v1`);
  }
  if (owner !== PUBLIC_CONTRACT.owner) {
    throw new CatalogError(`${label}.owner must be kokoro-bff`);
  }
  if (visibility !== 'public') {
    throw new CatalogError(`${label}.visibility must be public`);
  }
  if (!/^\d+\.\d+\.\d+$/.test(version)) {
    throw new CatalogError(`${label}.version must be a semantic version`);
  }

  const source = assertRecord(entry.source, `${label}.source`);
  assertKeys(
    source,
    ['repository', 'checkout', 'path', 'commit'],
    `${label}.source`,
  );
  const repository = requiredString(source, 'repository', `${label}.source`);
  const checkout = requiredString(source, 'checkout', `${label}.source`);
  const sourcePath = requiredString(source, 'path', `${label}.source`);
  const commit = requiredString(source, 'commit', `${label}.source`);
  if (repository !== PUBLIC_CONTRACT.repository) {
    throw new CatalogError(
      `${label}.source repository must be ${PUBLIC_CONTRACT.repository}`,
    );
  }
  if (sourcePath !== PUBLIC_CONTRACT.sourcePath) {
    throw new CatalogError(
      `${label}.source path must be ${PUBLIC_CONTRACT.sourcePath}`,
    );
  }
  if (!/^[0-9a-f]{40}$/.test(commit)) {
    throw new CatalogError(`${label}.source.commit must be a full Git SHA`);
  }

  const digest = assertRecord(entry.digest, `${label}.digest`);
  assertKeys(digest, ['algorithm', 'value'], `${label}.digest`);
  const algorithm = requiredString(digest, 'algorithm', `${label}.digest`);
  const digestValue = requiredString(digest, 'value', `${label}.digest`);
  if (algorithm !== 'sha256') {
    throw new CatalogError(`${label}.digest.algorithm must be sha256`);
  }
  if (!/^[0-9a-f]{64}$/.test(digestValue)) {
    throw new CatalogError(
      `${label}.digest.value must be a lowercase SHA-256 digest`,
    );
  }

  const generation = assertRecord(entry.generation, `${label}.generation`);
  assertKeys(generation, ['command'], `${label}.generation`);
  const command = requiredString(
    generation,
    'command',
    `${label}.generation`,
  );

  const publication = assertRecord(
    entry.publication,
    `${label}.publication`,
  );
  assertKeys(
    publication,
    ['classification', 'include_in_portal'],
    `${label}.publication`,
  );
  const classification = requiredString(
    publication,
    'classification',
    `${label}.publication`,
  );
  if (classification !== 'public') {
    throw new CatalogError(
      `${label}.publication.classification must be public`,
    );
  }
  if (publication.include_in_portal !== true) {
    throw new CatalogError(
      `${label}.publication.include_in_portal must be true`,
    );
  }

  return {
    id,
    owner,
    visibility,
    version,
    source: { repository, checkout, path: sourcePath, commit },
    digest: { algorithm, value: digestValue },
    generation: { command },
    publication: { classification, include_in_portal: true },
  };
}

export class CatalogError extends Error {
  constructor(message) {
    super(message);
    this.name = 'CatalogError';
  }
}

export function parseCatalogText(text, sourceLabel = 'contracts.yaml') {
  const document = parseDocument(text, { uniqueKeys: true });
  if (document.errors.length > 0) {
    throw new CatalogError(
      `${sourceLabel} is invalid YAML: ${document.errors[0]?.message ?? 'unknown parse error'}`,
    );
  }

  const root = assertRecord(document.toJS(), sourceLabel);
  assertKeys(root, ['schema_version', 'contracts'], sourceLabel);
  if (root.schema_version !== 1) {
    throw new CatalogError(`${sourceLabel}.schema_version must be 1`);
  }
  if (!Array.isArray(root.contracts) || root.contracts.length !== 1) {
    throw new CatalogError(
      `${sourceLabel}.contracts must contain exactly one public BFF contract`,
    );
  }

  return {
    schemaVersion: 1,
    contracts: root.contracts.map((entry, index) => parseEntry(entry, index)),
  };
}

export function loadCatalog(catalogPath) {
  return parseCatalogText(readFileSync(catalogPath, 'utf8'), catalogPath);
}

export { PUBLIC_CONTRACT };
