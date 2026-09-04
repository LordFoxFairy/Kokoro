import { ReferenceGenerationError } from './reference-errors.mjs';

const PUBLIC_KOKORO_NAMES = new Set([
  'x-kokoro-idempotency',
  'x-kokoro-internal-secret',
  'x-kokoro-namespace',
  'x-kokoro-owner',
  'x-kokoro-permission',
  'x-kokoro-principal-id',
  'x-kokoro-request-id',
  'x-kokoro-service',
  'x-kokoro-stability',
  'x-kokoro-visibility',
]);

const SECRET_PATTERNS = Object.freeze([
  /-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----/u,
  /\bAKIA[0-9A-Z]{16}\b/u,
  /\bgh[pousr]_[A-Za-z0-9]{36,255}\b/u,
  /\b(?:sk|rk)_live_[A-Za-z0-9]{16,}\b/u,
  /\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{6,}\b/u,
  /\bBearer\s+[A-Za-z0-9._~-]{24,}\b/iu,
]);

const DANGEROUS_SCHEME_PATTERN =
  /(?:^|[\s"'(=])(?:javascript|vbscript|file):/iu;
const DANGEROUS_DATA_URL_PATTERN =
  /(?:^|[\s"'(=])data:(?:text\/html|image\/svg\+xml|application\/javascript)/iu;
const INTERNAL_OWNER_PATH =
  /(?:^|[/(\\])(?:\.\.?[/\\])*(kokoro-(?:agent|billing|capability|iam|model|scheduler|storage|system))(?:[/\\]|$)/iu;

function addViolation(violations, path, message) {
  violations.push(`${path}: ${message}`);
}

function inspectString(value, path, violations) {
  for (const pattern of SECRET_PATTERNS) {
    if (pattern.test(value)) {
      addViolation(violations, path, 'credential-shaped literal is not publishable');
      break;
    }
  }
  if (DANGEROUS_SCHEME_PATTERN.test(value) || DANGEROUS_DATA_URL_PATTERN.test(value)) {
    addViolation(violations, path, 'dangerous URL scheme is not publishable');
  }
  const internalPath = INTERNAL_OWNER_PATH.exec(value);
  if (internalPath !== null) {
    addViolation(
      violations,
      path,
      `internal owner checkout path ${internalPath[1]} is not publishable`,
    );
  }
  const headerPattern = /\b(x-kokoro-[a-z0-9-]+)\s*:/giu;
  for (const match of value.matchAll(headerPattern)) {
    const header = match[1]?.toLowerCase();
    if (header !== undefined && !PUBLIC_KOKORO_NAMES.has(header)) {
      addViolation(violations, path, `unknown Kokoro header ${header}`);
    }
  }
}

function inspectValue(value, path, violations, seen) {
  if (typeof value === 'string') {
    inspectString(value, path, violations);
    return;
  }
  if (value === null || typeof value !== 'object') {
    return;
  }
  if (seen.has(value)) {
    return;
  }
  seen.add(value);
  if (Array.isArray(value)) {
    value.forEach((item, index) => inspectValue(item, `${path}[${index}]`, violations, seen));
    return;
  }
  for (const [key, child] of Object.entries(value)) {
    const childPath = path === '' ? key : `${path}.${key}`;
    if (
      key.toLowerCase().startsWith('x-kokoro-') &&
      !PUBLIC_KOKORO_NAMES.has(key.toLowerCase())
    ) {
      addViolation(violations, childPath, `unknown Kokoro extension ${key}`);
    }
    inspectValue(child, childPath, violations, seen);
  }
}

export class PublicationPolicyError extends ReferenceGenerationError {
  constructor(label, violations) {
    super(`${label} failed publication policy:\n${violations.join('\n')}`);
    this.name = 'PublicationPolicyError';
    this.violations = violations;
  }
}

export function assertPublicationSafe(value, label = 'publication input') {
  const violations = [];
  inspectValue(value, label, violations, new Set());
  if (violations.length > 0) {
    throw new PublicationPolicyError(label, violations);
  }
  return value;
}
