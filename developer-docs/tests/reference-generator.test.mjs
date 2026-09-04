import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';

import {
  assertPublicContract,
  generateReferenceFiles,
  writeReferenceFiles,
} from '../scripts/lib/reference-generator.mjs';

function fixtureContract(visibility = 'public') {
  return {
    openapi: '3.1.0',
    info: { title: 'Fixture API', version: '1.0.0' },
    tags: [{ name: 'Chat', description: 'Asynchronous conversations.' }],
    paths: {
      '/v1/sessions/{id}/messages': {
        parameters: [{ $ref: '#/components/parameters/SessionId' }],
        post: {
          tags: ['Chat'],
          operationId: 'createMessage',
          summary: 'Submit a message',
          'x-kokoro-owner': 'kokoro-bff',
          'x-kokoro-visibility': visibility,
          'x-kokoro-stability': 'beta',
          'x-kokoro-idempotency': 'required',
          'x-kokoro-permission': 'chat.message.create',
          parameters: [{ $ref: '#/components/parameters/IdempotencyKey' }],
          requestBody: {
            required: true,
            content: {
              'application/json': {
                schema: { $ref: '#/components/schemas/MessageCreateRequest' },
                example: { content: 'Review the contract.' },
              },
            },
          },
          responses: {
            202: {
              description: 'Accepted',
              headers: {
                'X-Request-Id': {
                  description: 'Request correlation identifier.',
                  schema: { type: 'string', minLength: 1 },
                  example: 'req_example',
                },
              },
              content: {
                'application/json': {
                  schema: { $ref: '#/components/schemas/MessageReceiptResponse' },
                },
              },
            },
          },
        },
      },
    },
    components: {
      parameters: {
        SessionId: {
          name: 'id',
          in: 'path',
          required: true,
          description: 'Opaque session identifier.',
          schema: { type: 'string' },
        },
        IdempotencyKey: {
          name: 'Idempotency-Key',
          in: 'header',
          required: true,
          schema: { type: 'string' },
        },
      },
      schemas: {
        MessageCreateRequest: {
          type: 'object',
          required: ['content'],
          additionalProperties: false,
          properties: {
            content: {
              type: 'string',
              minLength: 1,
              maxLength: 200,
              example: 'Review the contract.',
            },
          },
        },
        MessageReceiptResponse: {
          type: 'object',
          required: ['data'],
          properties: {
            data: { type: 'object' },
          },
        },
      },
    },
  };
}

const catalogEntry = {
  id: 'kokoro-bff-public-v1',
  owner: 'kokoro-bff',
  visibility: 'public',
  version: '1.0.0',
  source: {
    repository: 'https://github.com/LordFoxFairy/kokoro-bff.git',
    checkout: '../kokoro-bff',
    path: 'contract/openapi/v1/openapi.yaml',
    commit: '0123456789abcdef0123456789abcdef01234567',
  },
  digest: {
    algorithm: 'sha256',
    value: 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
  },
  generation: { command: 'corepack pnpm reference:generate' },
  publication: { classification: 'public', include_in_portal: true },
};

test('rejects a non-public operation before reference generation', () => {
  assert.throws(
    () => assertPublicContract(fixtureContract('internal-owner'), catalogEntry),
    /createMessage must have public visibility/,
  );
});

test('generates deterministic operation, schema, and manifest files', () => {
  const first = generateReferenceFiles(fixtureContract(), catalogEntry);
  const second = generateReferenceFiles(fixtureContract(), catalogEntry);

  assert.deepEqual([...first], [...second]);
  assert.deepEqual([...first.keys()].sort(), [
    'chat.md',
    'index-fragment.md',
    'manifest.json',
    'schemas.md',
  ]);

  const chatPage = first.get('chat.md');
  assert.match(chatPage, /POST<\/span> `\/v1\/sessions\/\{id\}\/messages`/);
  assert.match(chatPage, /Operation ID.*`createMessage`/);
  assert.match(chatPage, /Idempotency-Key/);
  assert.match(chatPage, /Review the contract\./);
  assert.doesNotMatch(chatPage, /generated_at|Date\(|timestamp/i);

  const indexFragment = first.get('index-fragment.md');
  assert.match(
    indexFragment,
    /\]\(\/reference\/v1\/generated\/chat#create-message\)/,
  );
  assert.doesNotMatch(indexFragment, /\]\(\.\//);

  const manifest = JSON.parse(first.get('manifest.json'));
  assert.deepEqual(manifest.items, [
    { text: 'Chat', link: '/reference/v1/generated/chat' },
    { text: 'Schemas', link: '/reference/v1/generated/schemas' },
  ]);
});

test('renders the complete public metadata and field-level constraints', () => {
  const contract = fixtureContract();
  contract.components.schemas.MessageReceiptResponse.properties = {
    data: {
      type: 'object',
      required: ['items'],
      properties: {
        items: {
          type: 'array',
          items: {
            type: 'object',
            required: ['id'],
            properties: {
              id: { type: 'string', minLength: 1 },
            },
          },
        },
      },
    },
  };
  const files = generateReferenceFiles(contract, catalogEntry);
  const chatPage = files.get('chat.md');
  const schemasPage = files.get('schemas.md');
  const manifest = JSON.parse(files.get('manifest.json'));

  assert.match(chatPage, /Owner.*`kokoro-bff`/);
  assert.match(chatPage, /Visibility.*`public`/);
  assert.match(chatPage, /Stability.*`beta`/);
  assert.match(chatPage, /Idempotency.*`required`/);
  assert.match(chatPage, /Max length.*200/);
  assert.match(chatPage, /Example.*`req_example`/s);
  assert.match(chatPage, /X-Request-Id/);
  assert.match(schemasPage, /`data\.items`/);
  assert.match(schemasPage, /`data\.items\[\]\.id`/);
  assert.equal(manifest.owner, 'kokoro-bff');
  assert.equal(manifest.visibility, 'public');
  assert.deepEqual(manifest.operations[0], {
    idempotency: 'required',
    method: 'POST',
    operationId: 'createMessage',
    owner: 'kokoro-bff',
    path: '/v1/sessions/{id}/messages',
    permission: 'chat.message.create',
    stability: 'beta',
    tag: 'Chat',
    visibility: 'public',
  });
});

test('rejects unsupported metadata and mismatched idempotency parameters', () => {
  const unsupported = fixtureContract();
  unsupported.paths['/v1/sessions/{id}/messages'].post['x-kokoro-stability'] =
    'not-a-state';
  assert.throws(
    () => assertPublicContract(unsupported, catalogEntry),
    /unsupported x-kokoro-stability/,
  );

  const mismatch = fixtureContract();
  mismatch.paths['/v1/sessions/{id}/messages'].post.parameters = [];
  assert.throws(
    () => assertPublicContract(mismatch, catalogEntry),
    /must reference Idempotency-Key/,
  );
});

test('rejects publication-unsafe canonical examples', () => {
  const unsafe = fixtureContract();
  unsafe.paths['/v1/sessions/{id}/messages'].post.requestBody.content[
    'application/json'
  ].example = {
    content: ['sk', 'live', '1234567890abcdefghijkl'].join('_'),
  };

  assert.throws(
    () => generateReferenceFiles(unsafe, catalogEntry),
    /publication|secret/i,
  );
});

test('rejects publication-unsafe extensions and URL schemes', () => {
  const unsafeHeader = fixtureContract();
  unsafeHeader.paths['/v1/sessions/{id}/messages'].post['x-kokoro-private'] =
    'hidden';
  assert.throws(
    () => assertPublicContract(unsafeHeader, catalogEntry),
    /publication|unknown Kokoro extension/i,
  );

  const unsafeUrl = fixtureContract();
  unsafeUrl.paths['/v1/sessions/{id}/messages'].post.description = [
    'java',
    'script:alert(1)',
  ].join('');
  assert.throws(
    () => generateReferenceFiles(unsafeUrl, catalogEntry),
    /publication|URL scheme/i,
  );
});

test('keeps reference replacement inside managed or temporary directories', () => {
  const files = generateReferenceFiles(fixtureContract(), catalogEntry);
  const unmanaged = mkdtempSync(join(tmpdir(), 'kokoro-unmanaged-'));
  try {
    writeFileSync(join(unmanaged, 'unrelated.txt'), 'do not remove');
    assert.throws(
      () => writeReferenceFiles(files, unmanaged),
      /unmanaged temporary directory/,
    );
  } finally {
    rmSync(unmanaged, { force: true, recursive: true });
  }

  assert.throws(
    () => writeReferenceFiles(files, process.cwd()),
    /must be inside/,
  );
  const escapeDirectory = mkdtempSync(join(tmpdir(), 'kokoro-escape-'));
  try {
    assert.throws(
      () =>
        writeReferenceFiles(
          new Map([['../escape.md', 'x']]),
          escapeDirectory,
        ),
      /escapes output directory/,
    );
  } finally {
    rmSync(escapeDirectory, { force: true, recursive: true });
  }
});

test('replaces stale generated output atomically', () => {
  const directory = mkdtempSync(join(tmpdir(), 'kokoro-reference-'));
  try {
    writeFileSync(
      join(directory, 'manifest.json'),
      JSON.stringify({ generatedBy: 'kokoro-developer-docs/reference-v1' }),
    );
    writeFileSync(join(directory, 'stale.md'), 'stale');

    writeReferenceFiles(
      generateReferenceFiles(fixtureContract(), catalogEntry),
      directory,
    );

    assert.throws(() => readFileSync(join(directory, 'stale.md')));
    assert.match(
      readFileSync(join(directory, 'chat.md'), 'utf8'),
      /Generated from the pinned canonical OpenAPI/,
    );
  } finally {
    rmSync(directory, { force: true, recursive: true });
  }
});
