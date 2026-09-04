import {
  mkdirSync,
  mkdtempSync,
  renameSync,
  rmSync,
  writeFileSync,
} from 'node:fs';
import { dirname, join } from 'node:path';

const HTTP_METHODS = new Set([
  'delete',
  'get',
  'head',
  'options',
  'patch',
  'post',
  'put',
  'trace',
]);

function isRecord(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

function requireRecord(value, label) {
  if (!isRecord(value)) {
    throw new ReferenceGenerationError(`${label} must be an object`);
  }
  return value;
}

function requireString(record, key, label) {
  const value = record[key];
  if (typeof value !== 'string' || value.trim() === '') {
    throw new ReferenceGenerationError(`${label}.${key} must be a string`);
  }
  return value;
}

function slugify(value) {
  const slug = value
    .normalize('NFKD')
    .replace(/([a-z0-9])([A-Z])/g, '$1-$2')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '');
  return slug || 'reference';
}

function escapeTable(value) {
  return String(value).replaceAll('|', '\\|').replaceAll('\n', ' ');
}

function normalizeDescription(value, fallback = '—') {
  if (typeof value !== 'string' || value.trim() === '') {
    return fallback;
  }
  return value.trim().replace(/\s+/g, ' ');
}

function referenceName(reference) {
  return reference.split('/').at(-1) ?? reference;
}

function resolveReference(contract, value, label) {
  if (!isRecord(value) || typeof value.$ref !== 'string') {
    return value;
  }
  if (!value.$ref.startsWith('#/')) {
    throw new ReferenceGenerationError(
      `${label} uses unsupported external reference ${value.$ref}`,
    );
  }
  let current = contract;
  for (const rawPart of value.$ref.slice(2).split('/')) {
    const part = rawPart.replaceAll('~1', '/').replaceAll('~0', '~');
    if (!isRecord(current) || !(part in current)) {
      throw new ReferenceGenerationError(
        `${label} has unresolved reference ${value.$ref}`,
      );
    }
    current = current[part];
  }
  return current;
}

function schemaType(schema) {
  if (!isRecord(schema)) {
    return 'unknown';
  }
  if (typeof schema.$ref === 'string') {
    const name = referenceName(schema.$ref);
    return `[${name}](./schemas#${slugify(name)})`;
  }
  if (Array.isArray(schema.oneOf)) {
    return schema.oneOf.map((item) => schemaType(item)).join(' or ');
  }
  if (Array.isArray(schema.anyOf)) {
    return schema.anyOf.map((item) => schemaType(item)).join(' or ');
  }
  if (schema.type === 'array') {
    return `array of ${schemaType(schema.items)}`;
  }
  const rawType = Array.isArray(schema.type)
    ? schema.type.join(' or ')
    : typeof schema.type === 'string'
      ? schema.type
      : 'object';
  return typeof schema.format === 'string'
    ? `${rawType} (${schema.format})`
    : rawType;
}

function schemaConstraints(schema) {
  if (!isRecord(schema)) {
    return '—';
  }
  const constraints = [];
  if ('const' in schema) {
    constraints.push(`const ${JSON.stringify(schema.const)}`);
  }
  if (Array.isArray(schema.enum)) {
    constraints.push(`enum: ${schema.enum.map(String).join(', ')}`);
  }
  for (const [key, label] of [
    ['minimum', 'min'],
    ['maximum', 'max'],
    ['minLength', 'min length'],
    ['maxLength', 'max length'],
    ['minItems', 'min items'],
    ['maxItems', 'max items'],
  ]) {
    if (typeof schema[key] === 'number') {
      constraints.push(`${label}: ${schema[key]}`);
    }
  }
  if (schema.additionalProperties === false) {
    constraints.push('closed object');
  }
  return constraints.length === 0 ? '—' : constraints.join('; ');
}

function renderExample(example) {
  if (example === undefined) {
    return '';
  }
  const serialized =
    typeof example === 'string' ? example : JSON.stringify(example, null, 2);
  return `\n\n**Example**\n\n\`\`\`json\n${serialized}\n\`\`\`\n`;
}

function firstExample(mediaType) {
  if (!isRecord(mediaType)) {
    return undefined;
  }
  if ('example' in mediaType) {
    return mediaType.example;
  }
  if (isRecord(mediaType.examples)) {
    for (const candidate of Object.values(mediaType.examples)) {
      if (isRecord(candidate) && 'value' in candidate) {
        return candidate.value;
      }
    }
  }
  return undefined;
}

function renderParameters(contract, parameters) {
  if (parameters.length === 0) {
    return '';
  }
  const rows = parameters.map((parameter, index) => {
    const resolved = requireRecord(
      resolveReference(contract, parameter, `parameter[${index}]`),
      `parameter[${index}]`,
    );
    return `| \`${escapeTable(requireString(resolved, 'name', `parameter[${index}]`))}\` | ${escapeTable(requireString(resolved, 'in', `parameter[${index}]`))} | ${resolved.required === true ? 'yes' : 'no'} | ${escapeTable(schemaType(resolved.schema))} | ${escapeTable(normalizeDescription(resolved.description))} |`;
  });
  return [
    '### Parameters',
    '',
    '| Name | Location | Required | Type | Description |',
    '| --- | --- | --- | --- | --- |',
    ...rows,
    '',
  ].join('\n');
}

function renderRequestBody(requestBody) {
  if (!isRecord(requestBody)) {
    return '';
  }
  const content = requireRecord(requestBody.content, 'requestBody.content');
  const lines = ['### Request body', ''];
  for (const [mediaName, mediaValue] of Object.entries(content)) {
    const media = requireRecord(mediaValue, `requestBody.content.${mediaName}`);
    lines.push(
      `- Content type: \`${mediaName}\``,
      `- Required: ${requestBody.required === true ? 'yes' : 'no'}`,
      `- Schema: ${schemaType(media.schema)}`,
    );
    const example = renderExample(firstExample(media));
    if (example !== '') {
      lines.push(example.trimEnd());
    }
  }
  lines.push('');
  return lines.join('\n');
}

function renderResponses(contract, responses) {
  if (!isRecord(responses)) {
    return '';
  }
  const rows = Object.entries(responses)
    .sort(([left], [right]) => left.localeCompare(right, 'en'))
    .map(([status, response]) => {
      const resolved = requireRecord(
        resolveReference(contract, response, `response ${status}`),
        `response ${status}`,
      );
      const content = isRecord(resolved.content) ? resolved.content : {};
      const representations = Object.entries(content).map(
        ([mediaName, mediaValue]) => {
          const media = requireRecord(
            mediaValue,
            `response ${status}.${mediaName}`,
          );
          return `\`${mediaName}\` · ${schemaType(media.schema)}`;
        },
      );
      return `| \`${escapeTable(status)}\` | ${escapeTable(normalizeDescription(resolved.description))} | ${escapeTable(representations.join(', ') || 'No body')} |`;
    });
  return [
    '### Responses',
    '',
    '| Status | Description | Representation |',
    '| --- | --- | --- |',
    ...rows,
    '',
  ].join('\n');
}

function collectOperations(contract) {
  const paths = requireRecord(contract.paths, 'paths');
  const operations = [];
  for (const [path, pathValue] of Object.entries(paths)) {
    const pathItem = requireRecord(pathValue, `paths.${path}`);
    const pathParameters = Array.isArray(pathItem.parameters)
      ? pathItem.parameters
      : [];
    for (const [method, operationValue] of Object.entries(pathItem)) {
      if (!HTTP_METHODS.has(method.toLowerCase())) {
        continue;
      }
      const operation = requireRecord(
        operationValue,
        `${method.toUpperCase()} ${path}`,
      );
      const operationParameters = Array.isArray(operation.parameters)
        ? operation.parameters
        : [];
      operations.push({
        method: method.toUpperCase(),
        operation,
        parameters: [...pathParameters, ...operationParameters],
        path,
      });
    }
  }
  return operations;
}

export class ReferenceGenerationError extends Error {
  constructor(message) {
    super(message);
    this.name = 'ReferenceGenerationError';
  }
}

export function assertPublicContract(contractValue, catalogEntry) {
  const contract = requireRecord(contractValue, 'OpenAPI document');
  const info = requireRecord(contract.info, 'info');
  const version = requireString(info, 'version', 'info');
  if (version !== catalogEntry.version) {
    throw new ReferenceGenerationError(
      `OpenAPI version ${version} does not match catalog ${catalogEntry.version}`,
    );
  }
  if (typeof contract.openapi !== 'string' || !contract.openapi.startsWith('3.1.')) {
    throw new ReferenceGenerationError('canonical contract must use OpenAPI 3.1');
  }
  if (isRecord(contract.webhooks) && Object.keys(contract.webhooks).length > 0) {
    throw new ReferenceGenerationError(
      'webhook publication requires an explicit portal generator update',
    );
  }

  const operations = collectOperations(contract);
  if (operations.length === 0) {
    throw new ReferenceGenerationError('canonical contract has no operations');
  }
  const operationIds = new Set();
  for (const { method, operation, path } of operations) {
    const label = `${method} ${path}`;
    const operationId = requireString(operation, 'operationId', label);
    if (operationIds.has(operationId)) {
      throw new ReferenceGenerationError(
        `duplicate operationId ${operationId}`,
      );
    }
    operationIds.add(operationId);
    if (operation['x-kokoro-owner'] !== 'kokoro-bff') {
      throw new ReferenceGenerationError(
        `${operationId} must be owned by kokoro-bff`,
      );
    }
    if (operation['x-kokoro-visibility'] !== 'public') {
      throw new ReferenceGenerationError(
        `${operationId} must have public visibility`,
      );
    }
    for (const field of [
      'x-kokoro-stability',
      'x-kokoro-idempotency',
      'x-kokoro-permission',
    ]) {
      requireString(operation, field, label);
    }
    if (!Array.isArray(operation.tags) || operation.tags.length !== 1) {
      throw new ReferenceGenerationError(
        `${operationId} must declare exactly one public tag`,
      );
    }
  }
  return operations;
}

function renderOperation(contract, collectedOperation) {
  const { method, operation, parameters, path } = collectedOperation;
  const operationId = requireString(operation, 'operationId', `${method} ${path}`);
  const summary = normalizeDescription(operation.summary, operationId);
  const anchor = slugify(operationId);
  const description = normalizeDescription(operation.description, '');
  const metadata = [
    `| Operation ID | \`${operationId}\` |`,
    `| Stability | \`${operation['x-kokoro-stability']}\` |`,
    `| Idempotency | \`${operation['x-kokoro-idempotency']}\` |`,
    `| Permission | \`${operation['x-kokoro-permission']}\` |`,
  ];
  return [
    `## ${summary} {#${anchor}}`,
    '',
    `<span class="api-method api-method--${method.toLowerCase()}">${method}</span> \`${path}\``,
    '',
    ...(description === '' ? [] : [description, '']),
    '| Contract metadata | Value |',
    '| --- | --- |',
    ...metadata,
    '',
    renderParameters(contract, parameters),
    renderRequestBody(operation.requestBody),
    renderResponses(contract, operation.responses),
  ]
    .filter((part) => part !== '')
    .join('\n');
}

function renderTagPage(contract, tag, operations, entry) {
  const title = requireString(tag, 'name', 'tag');
  const description = normalizeDescription(tag.description, '');
  return [
    '<!-- Generated file. Do not edit. -->',
    '---',
    `title: ${JSON.stringify(title)}`,
    'outline: [2, 3]',
    'editLink: false',
    '---',
    '',
    `# ${title}`,
    '',
    '> Generated from the pinned canonical OpenAPI. Change the owner contract, then regenerate this page.',
    '',
    ...(description === '' ? [] : [description, '']),
    `Contract \`${entry.version}\` · source \`${entry.source.commit}\` · SHA-256 \`${entry.digest.value}\``,
    '',
    operations.map((operation) => renderOperation(contract, operation)).join('\n\n'),
    '',
  ].join('\n');
}

function renderSchemasPage(contract, entry) {
  const components = isRecord(contract.components) ? contract.components : {};
  const schemas = isRecord(components.schemas) ? components.schemas : {};
  const sections = Object.entries(schemas)
    .sort(([left], [right]) => left.localeCompare(right, 'en'))
    .map(([name, schemaValue]) => {
      const schema = requireRecord(schemaValue, `schema ${name}`);
      const lines = [
        `## ${name} {#${slugify(name)}}`,
        '',
        normalizeDescription(schema.description, `Type: ${schemaType(schema)}`),
        '',
      ];
      if (Array.isArray(schema.oneOf)) {
        lines.push(
          `One of: ${schema.oneOf.map((item) => schemaType(item)).join(', ')}.`,
          '',
        );
      }
      if (isRecord(schema.properties)) {
        const required = new Set(
          Array.isArray(schema.required) ? schema.required : [],
        );
        lines.push(
          '| Property | Required | Type | Constraints | Description |',
          '| --- | --- | --- | --- | --- |',
        );
        for (const [propertyName, propertyValue] of Object.entries(
          schema.properties,
        )) {
          const property = requireRecord(
            propertyValue,
            `schema ${name}.${propertyName}`,
          );
          lines.push(
            `| \`${escapeTable(propertyName)}\` | ${required.has(propertyName) ? 'yes' : 'no'} | ${escapeTable(schemaType(property))} | ${escapeTable(schemaConstraints(property))} | ${escapeTable(normalizeDescription(property.description))} |`,
          );
        }
        lines.push('');
      }
      const example = renderExample(schema.example);
      if (example !== '') {
        lines.push(example.trimEnd(), '');
      }
      return lines.join('\n');
    });
  return [
    '<!-- Generated file. Do not edit. -->',
    '---',
    'title: Schemas',
    'outline: [2, 3]',
    'editLink: false',
    '---',
    '',
    '# Schemas',
    '',
    '> Generated from the pinned canonical OpenAPI. These models are public wire shapes, not domain models or database rows.',
    '',
    `Contract \`${entry.version}\` · source \`${entry.source.commit}\` · SHA-256 \`${entry.digest.value}\``,
    '',
    ...sections,
    '',
  ].join('\n');
}

function tagDefinitions(contract, operations) {
  const configuredTags = Array.isArray(contract.tags) ? contract.tags : [];
  const byName = new Map();
  for (const tagValue of configuredTags) {
    const tag = requireRecord(tagValue, 'tag');
    byName.set(requireString(tag, 'name', 'tag'), tag);
  }
  for (const { operation } of operations) {
    const tagName = operation.tags[0];
    if (typeof tagName === 'string' && !byName.has(tagName)) {
      byName.set(tagName, { name: tagName });
    }
  }
  return [...byName.values()].filter((tag) =>
    operations.some(({ operation }) => operation.tags[0] === tag.name),
  );
}

export function generateReferenceFiles(contract, catalogEntry) {
  const operations = assertPublicContract(contract, catalogEntry);
  const tags = tagDefinitions(contract, operations);
  const files = new Map();
  const manifestItems = [];
  const indexRows = [];

  for (const tag of tags) {
    const tagName = requireString(tag, 'name', 'tag');
    const tagSlug = slugify(tagName);
    const tagOperations = operations.filter(
      ({ operation }) => operation.tags[0] === tagName,
    );
    files.set(
      `${tagSlug}.md`,
      renderTagPage(contract, tag, tagOperations, catalogEntry),
    );
    manifestItems.push({
      text: tagName,
      link: `/reference/v1/generated/${tagSlug}`,
    });
    for (const { method, operation, path } of tagOperations) {
      const operationId = requireString(operation, 'operationId', path);
      indexRows.push(
        `| <span class="api-method api-method--${method.toLowerCase()}">${method}</span> | [${escapeTable(normalizeDescription(operation.summary, operationId))}](/reference/v1/generated/${tagSlug}#${slugify(operationId)}) | \`${escapeTable(path)}\` |`,
      );
    }
  }

  manifestItems.push({
    text: 'Schemas',
    link: '/reference/v1/generated/schemas',
  });
  files.set('schemas.md', renderSchemasPage(contract, catalogEntry));
  files.set(
    'index-fragment.md',
    [
      '<!-- Generated file. Do not edit. -->',
      '',
      `Version \`${catalogEntry.version}\` · ${operations.length} operations · source \`${catalogEntry.source.commit}\``,
      '',
      '| Method | Operation | Path |',
      '| --- | --- | --- |',
      ...indexRows,
      '',
    ].join('\n'),
  );
  files.set(
    'manifest.json',
    `${JSON.stringify(
      {
        contract: catalogEntry.id,
        digest: catalogEntry.digest.value,
        items: manifestItems,
        operationCount: operations.length,
        sourceCommit: catalogEntry.source.commit,
        version: catalogEntry.version,
      },
      null,
      2,
    )}\n`,
  );
  return files;
}

export function writeReferenceFiles(files, outputDirectory) {
  mkdirSync(dirname(outputDirectory), { recursive: true });
  const temporaryDirectory = mkdtempSync(
    join(dirname(outputDirectory), '.reference-generate-'),
  );
  try {
    for (const [relativePath, content] of files) {
      const destination = join(temporaryDirectory, relativePath);
      mkdirSync(dirname(destination), { recursive: true });
      writeFileSync(destination, content);
    }
    rmSync(outputDirectory, { force: true, recursive: true });
    renameSync(temporaryDirectory, outputDirectory);
  } catch (error) {
    rmSync(temporaryDirectory, { force: true, recursive: true });
    throw error;
  }
}
