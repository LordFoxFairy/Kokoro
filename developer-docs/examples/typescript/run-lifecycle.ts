interface JsonRecord {
  readonly [key: string]: unknown;
}

interface SseFrame {
  readonly data: JsonRecord;
  readonly id: string;
}

function requiredEnvironment(name: string): string {
  const value = process.env[name];
  if (value === undefined || value.length === 0) {
    throw new Error(`Set ${name}`);
  }
  return value;
}

function isRecord(value: unknown): value is JsonRecord {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

function requireRecord(value: unknown, label: string): JsonRecord {
  if (!isRecord(value)) throw new Error(`${label} must be an object`);
  return value;
}

function requireString(record: JsonRecord, key: string, label: string): string {
  const value = record[key];
  if (typeof value !== 'string' || value.length === 0) {
    throw new Error(`${label}.${key} must be a string`);
  }
  return value;
}

const baseUrl = requiredEnvironment('KOKORO_API_BASE_URL');
const apiToken = requiredEnvironment('KOKORO_API_TOKEN');
const namespace = requiredEnvironment('KOKORO_NAMESPACE');
const principalId = requiredEnvironment('KOKORO_PRINCIPAL_ID');
const sessionId = requiredEnvironment('KOKORO_SESSION_ID');

function serviceHeaders(): Record<string, string> {
  return {
    'x-kokoro-internal-secret': apiToken,
    'x-kokoro-namespace': namespace,
    'x-kokoro-principal-id': principalId,
    'x-kokoro-service': 'web-bff',
  };
}

async function postJson(
  path: string,
  idempotencyKey: string,
  body: JsonRecord,
): Promise<JsonRecord> {
  const response = await fetch(`${baseUrl}${path}`, {
    body: JSON.stringify(body),
    headers: {
      ...serviceHeaders(),
      'content-type': 'application/json',
      'idempotency-key': idempotencyKey,
    },
    method: 'POST',
  });
  const payload: unknown = await response.json();
  if (!response.ok) {
    throw new Error(`Kokoro request failed with ${response.status}`);
  }
  return requireRecord(payload, 'response');
}

function parseSse(text: string): SseFrame[] {
  const frames: SseFrame[] = [];
  for (const block of text.split(/\r?\n\r?\n/)) {
    if (block.trim() === '' || block.startsWith(':')) continue;
    let id: string | undefined;
    let dataText: string | undefined;
    for (const line of block.split(/\r?\n/)) {
      if (line.startsWith('id:')) id = line.slice(3).trim();
      if (line.startsWith('data:')) dataText = line.slice(5).trim();
    }
    if (id === undefined || dataText === undefined) {
      throw new Error('SSE frame must contain id and data');
    }
    const data: unknown = JSON.parse(dataText);
    frames.push({ data: requireRecord(data, 'SSE data'), id });
  }
  return frames;
}

async function readEvents(lastEventId?: string): Promise<SseFrame[]> {
  const headers: Record<string, string> = {
    ...serviceHeaders(),
    accept: 'text/event-stream',
  };
  if (lastEventId !== undefined) headers['last-event-id'] = lastEventId;
  const response = await fetch(
    `${baseUrl}/v1/sessions/${encodeURIComponent(sessionId)}/events`,
    { headers },
  );
  if (!response.ok) {
    throw new Error(`Kokoro event stream failed with ${response.status}`);
  }
  return parseSse(await response.text());
}

const messageResponse = await postJson(
  `/v1/sessions/${encodeURIComponent(sessionId)}/messages`,
  'example-typescript-create-001',
  {
    content: 'Review the public API contract.',
    model: 'default',
    project_ref: 'project_example',
  },
);
const messageData = requireRecord(messageResponse.data, 'response.data');
const runId = requireString(messageData, 'run_id', 'response.data');

const initialFrames = await readEvents();
const firstCursor = initialFrames.at(-1)?.id;
if (firstCursor === undefined) throw new Error('Expected an AG-UI frame');

await postJson(
  `/v1/sessions/${encodeURIComponent(sessionId)}/runs/${encodeURIComponent(runId)}/control`,
  'example-typescript-resume-001',
  {
    decisions: [{ tool_id: 'tool_example', type: 'approve' }],
    kind: 'run.resume',
  },
);

const resumedFrames = await readEvents(firstCursor);
const finalFrame = resumedFrames.at(-1);
if (finalFrame === undefined) throw new Error('Expected a resumed AG-UI frame');
const eventType = requireString(finalFrame.data, 'type', 'SSE data');
process.stdout.write(`${runId} ${eventType} ${finalFrame.id}\n`);

export {};
