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
            content: { type: 'string', minLength: 1 },
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

test('replaces stale generated output atomically', () => {
  const directory = mkdtempSync(join(tmpdir(), 'kokoro-reference-'));
  try {
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
