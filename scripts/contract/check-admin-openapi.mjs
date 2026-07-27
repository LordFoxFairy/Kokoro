#!/usr/bin/env node

// Fail-closed Wave T2 gate: the Admin browser API OpenAPI document and the Fastify routes it
// claims to describe are the same set, in both directions, method by method.
//
// A contract nobody mechanically checks is a contract that drifts. This gate is the only thing
// standing between contract/openapi/admin-web-v1.yaml and a document that quietly stops matching
// kokoro-platform-admin. It reads both sides and refuses to guess: anything it cannot read as a
// literal route registration or as a structural document key is an error, never a silent skip.
//
// Scope is exactly the ordinary Admin browser HTTP plane. The privileged Admin BFF -> Platform
// Connect plane (kokoro.platform.admin.v1.AdminAuthService) is a different trust plane with its
// own source of truth in contract/proto/kokoro/platform/admin/v1/admin_auth.proto, and is not
// reachable from here: it is mounted by a Fastify plugin, not by a literal app.<method>() call.

import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const SCRIPT_PATH = fileURLToPath(import.meta.url);
const DEFAULT_DOCUMENT = "contract/openapi/admin-web-v1.yaml";
const DEFAULT_ROUTES = "kokoro-platform/kokoro-platform-admin/src/server.ts";

// OpenAPI 3.1 fixed fields of a Path Item Object that are not operations.
const PATH_ITEM_FIELDS = ["description", "parameters", "servers", "summary"];
const HTTP_METHODS = ["delete", "get", "head", "options", "patch", "post", "put", "trace"];
// Fastify shorthands that register a route without naming one method and one literal path.
// The gate cannot map them onto an OpenAPI operation, so it stops rather than guessing.
const OPAQUE_ROUTE_CALLS = ["all", "route"];

/**
 * Routes that exist on the same Fastify instance but are deliberately not browser API operations.
 *
 * GET / serves the gateway's own vanilla operations console (public/index.html) as text/html. It
 * is a page, not an operation: no JSON envelope, no operationId, and a generated browser client
 * would have nothing to call. Excluding it is a decision, so it is written down here and verified
 * every run — if the route disappears (see the D14 ruling in the document header) this gate fails
 * with admin_openapi_exclusion_stale instead of letting a dead exclusion rot in place.
 *
 * GET /healthz, GET /metrics and POST /kokoro.platform.admin.v1.AdminAuthService/* never reach
 * this list: they are registered by platform-kit and by admin-auth-connect.ts, not by a literal
 * app.<method>() call in server.ts. Probes carry no JSON envelope (/metrics is Prometheus text)
 * and the Connect face belongs to the privileged trust plane, which keeps its own proto source.
 */
const EXCLUDED_ROUTES = new Map([
  ["get /", "vanilla operations console SPA (text/html), not a browser API operation"],
]);

// One path segment: a literal, or a single {name} template covering the whole segment.
const PATH_SEGMENT = String.raw`(?:[A-Za-z0-9._~-]+|\{[A-Za-z_][A-Za-z0-9_]*\})`;
const OPENAPI_PATH = new RegExp(String.raw`^\/${PATH_SEGMENT}(?:\/${PATH_SEGMENT})*$`, "u");

export class AdminOpenapiError extends Error {
  constructor(code, detail = "") {
    super(`${code}${detail ? `: ${detail}` : ""}`);
    this.name = "AdminOpenapiError";
    this.code = code;
  }
}

function fail(code, detail) {
  throw new AdminOpenapiError(code, detail);
}

export function parseArguments(argv) {
  const options = { root: process.cwd(), document: DEFAULT_DOCUMENT, routes: DEFAULT_ROUTES };
  for (let index = 0; index < argv.length; index += 1) {
    const flag = argv[index];
    const value = argv[index + 1];
    if (!flag.startsWith("--") || !(flag.slice(2) in options) || !value) {
      fail("admin_openapi_arguments_invalid", flag ?? "");
    }
    options[flag.slice(2)] = value;
    index += 1;
  }
  options.root = resolve(options.root);
  for (const key of ["document", "routes"]) options[key] = resolve(options.root, options[key]);
  return options;
}

function readText(path, code) {
  try {
    return readFileSync(path, "utf8");
  } catch (error) {
    return fail(code, `${path}: ${error.code ?? error.message}`);
  }
}

function sortedSet(values) {
  return [...new Set(values)].sort();
}

function setDifference(left, right) {
  return left.filter((value) => !right.has(value));
}

// ---------------------------------------------------------------------------------------------
// Provider side: literal Fastify route registrations in server.ts
// ---------------------------------------------------------------------------------------------

// Deliberately line-oriented rather than a JavaScript lexer. A lexer that mis-tracks one regex or
// template literal would desync and start missing routes, which fails open; a line scanner cannot.
const ROUTE_CALL = /\bapp\s*\.\s*([A-Za-z]+)\s*\(/gu;
const ROUTE_LITERAL = /^(?:"((?:[^"\\]|\\.)*)"|'((?:[^'\\]|\\.)*)'|`([^`$\\]*)`)\s*,/u;

function isCommentLine(trimmed) {
  return trimmed.startsWith("//") || trimmed.startsWith("/*") || trimmed.startsWith("*");
}

/** Fastify `/api/operators/:id/status` in OpenAPI spelling, or null when it cannot be mapped. */
export function toOpenApiPath(routePath) {
  if (routePath === "/") return "/";
  // Wildcards, regex constraints and optional params have no single OpenAPI path equivalent.
  if (/[*()?#\s]/u.test(routePath)) return null;
  const templated = routePath.replace(/:([A-Za-z_][A-Za-z0-9_]*)/gu, "{$1}");
  return OPENAPI_PATH.test(templated) ? templated : null;
}

/**
 * Every route the provider registers with a literal method and a literal path.
 *
 * Anything ambiguous stops the gate: a non-literal path, a shorthand that hides the method, or a
 * registration that is not the first thing on its line. Those are readability limits of this
 * scanner, and the honest response is to fail rather than to under-report the provider.
 */
export function parseFastifyRoutes(source) {
  const routes = [];
  const lines = source.split(/\r?\n/u);
  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index];
    const trimmed = line.trim();
    const offset = line.length - line.trimStart().length;
    ROUTE_CALL.lastIndex = 0;
    for (let match = ROUTE_CALL.exec(line); match !== null; match = ROUTE_CALL.exec(line)) {
      const method = match[1].toLowerCase();
      const known = HTTP_METHODS.includes(method);
      if (!known && !OPAQUE_ROUTE_CALLS.includes(method)) continue; // app.register, app.listen, ...
      if (isCommentLine(trimmed)) continue; // a commented-out registration is not a route
      const where = `${index + 1}`;
      if (!known) {
        fail("admin_openapi_route_source_unreadable", `line ${where}: app.${method}() hides its method or path`);
      }
      if (match.index !== offset) {
        fail("admin_openapi_route_source_unreadable", `line ${where}: app.${method}() is not a top-level registration`);
      }
      const literal = ROUTE_LITERAL.exec(line.slice(match.index + match[0].length).trim());
      if (!literal) {
        fail("admin_openapi_route_source_unreadable", `line ${where}: app.${method}() path is not a string literal`);
      }
      const routePath = literal[1] ?? literal[2] ?? literal[3];
      const path = toOpenApiPath(routePath);
      if (path === null) {
        fail("admin_openapi_route_source_unreadable", `line ${where}: unmappable route path: ${routePath}`);
      }
      routes.push({ method, path, line: index + 1 });
    }
  }
  if (routes.length === 0) fail("admin_openapi_route_source_unreadable", "no route registrations found");
  return routes;
}

// ---------------------------------------------------------------------------------------------
// Document side: a narrow structural reader for the OpenAPI YAML
// ---------------------------------------------------------------------------------------------
//
// This reads exactly two things — the `openapi` version and the shape of `paths` — because those
// are the only things this gate reconciles. It is not a YAML library and never becomes one; every
// construct it does not account for is an error, so it can never quietly mis-read the document.

function stripComment(line) {
  let quote = null;
  for (let index = 0; index < line.length; index += 1) {
    const character = line[index];
    if (quote) {
      if (character === quote) quote = null;
      continue;
    }
    if (character === '"' || character === "'") quote = character;
    else if (character === "#" && (index === 0 || /\s/u.test(line[index - 1]))) return line.slice(0, index);
  }
  return line;
}

function unquote(value) {
  const trimmed = value.trim();
  if (trimmed.length >= 2 && /^(["']).*\1$/su.test(trimmed)) return trimmed.slice(1, -1);
  return trimmed;
}

/**
 * Mapping-key lines with their indentation, skipping blank lines, comments, and the bodies of
 * block scalars. Block scalar bodies matter: `description: |` blocks in this document contain
 * prose that names paths, and a reader that did not skip them would invent operations from prose.
 */
export function structuralLines(text) {
  const raw = text.split(/\r?\n/u);
  const result = [];
  let index = 0;
  while (index < raw.length) {
    const line = raw[index];
    index += 1;
    if (line.trim() === "") continue;
    if (/^\s*\t/u.test(line)) fail("admin_openapi_document_unreadable", `line ${index}: tab indentation`);
    const content = stripComment(line).replace(/\s+$/u, "");
    if (content.trim() === "") continue;
    const indent = content.length - content.trimStart().length;
    result.push({ indent, body: content.slice(indent), line: index });
    if (!/:\s*[|>][+-]?\d*$/u.test(content)) continue;
    // A block scalar owns every following line that is blank or indented deeper than its key.
    while (index < raw.length) {
      const next = raw[index];
      if (next.trim() !== "" && next.length - next.trimStart().length <= indent) break;
      index += 1;
    }
  }
  return result;
}

function readVersion(lines) {
  const entry = lines.find((item) => item.indent === 0 && item.body.startsWith("openapi:"));
  if (!entry) fail("admin_openapi_document_unreadable", "missing top-level openapi version");
  const version = unquote(entry.body.slice("openapi:".length));
  if (!/^3\.1\.\d+$/u.test(version)) {
    fail("admin_openapi_version_unsupported", `${version} (this gate targets OpenAPI 3.1.x)`);
  }
  return version;
}

/** path -> sorted methods, read from the top-level `paths` block. */
export function readDocumentPaths(lines, errors) {
  const start = lines.findIndex((item) => item.indent === 0 && item.body === "paths:");
  if (start === -1) fail("admin_openapi_document_unreadable", "missing top-level paths");
  const section = [];
  for (let index = start + 1; index < lines.length; index += 1) {
    if (lines[index].indent === 0) break;
    section.push(lines[index]);
  }
  if (section.length === 0) fail("admin_openapi_document_unreadable", "empty paths block");

  const pathIndent = section[0].indent;
  const items = [];
  for (const entry of section) {
    if (entry.indent > pathIndent) {
      items[items.length - 1].children.push(entry);
      continue;
    }
    const key = /^(.*?):$/u.exec(entry.body);
    if (!key) fail("admin_openapi_document_unreadable", `line ${entry.line}: not a path key: ${entry.body}`);
    const path = unquote(key[1]);
    if (!OPENAPI_PATH.test(path) && path !== "/") {
      fail("admin_openapi_document_unreadable", `line ${entry.line}: unusable path: ${path}`);
    }
    items.push({ path, line: entry.line, children: [] });
  }

  const paths = new Map();
  for (const item of items) {
    if (paths.has(item.path)) {
      errors.push(`admin_openapi_duplicate_path: ${item.path}: line ${item.line}`);
      continue;
    }
    paths.set(item.path, readPathItem(item));
  }
  return paths;
}

function readPathItem(item) {
  if (item.children.length === 0) {
    fail("admin_openapi_document_unreadable", `line ${item.line}: empty path item: ${item.path}`);
  }
  const fieldIndent = Math.min(...item.children.map((child) => child.indent));
  const methods = [];
  for (const child of item.children) {
    if (child.indent !== fieldIndent) continue;
    const key = /^([$A-Za-z][A-Za-z0-9_-]*):/u.exec(child.body);
    if (!key) fail("admin_openapi_document_unreadable", `line ${child.line}: not a path item field: ${child.body}`);
    const field = key[1];
    if (HTTP_METHODS.includes(field)) {
      methods.push(field);
      continue;
    }
    // Specification extensions are allowed through; anything else — including `$ref` path items,
    // which would move the operation somewhere this reader does not follow — stops the gate.
    if (PATH_ITEM_FIELDS.includes(field) || field.startsWith("x-")) continue;
    fail("admin_openapi_document_unreadable", `line ${child.line}: unsupported path item field: ${field}`);
  }
  if (methods.length === 0) {
    fail("admin_openapi_document_unreadable", `line ${item.line}: path item declares no operation: ${item.path}`);
  }
  return sortedSet(methods);
}

// ---------------------------------------------------------------------------------------------
// Reconciliation
// ---------------------------------------------------------------------------------------------

/** Registered routes minus the documented exclusions, as path -> sorted methods. */
function providerPaths(routes, errors) {
  const paths = new Map();
  const seen = new Set();
  const usedExclusions = new Set();
  for (const route of routes) {
    const key = `${route.method} ${route.path}`;
    if (EXCLUDED_ROUTES.has(key)) {
      usedExclusions.add(key);
      continue;
    }
    if (seen.has(key)) {
      errors.push(`admin_openapi_duplicate_route: ${key}: line ${route.line}`);
      continue;
    }
    seen.add(key);
    if (!paths.has(route.path)) paths.set(route.path, []);
    paths.get(route.path).push(route.method);
  }
  for (const [key, reason] of EXCLUDED_ROUTES) {
    // An exclusion that no longer matches a real route is drift of its own: it would go on hiding
    // a route that came back under a different name.
    if (!usedExclusions.has(key)) errors.push(`admin_openapi_exclusion_stale: ${key}: ${reason}`);
  }
  for (const [path, methods] of paths) paths.set(path, sortedSet(methods));
  return paths;
}

export function checkAdminOpenapi(options) {
  const errors = [];
  const routes = parseFastifyRoutes(readText(options.routes, "admin_openapi_route_source_missing"));
  const lines = structuralLines(readText(options.document, "admin_openapi_document_missing"));
  readVersion(lines);
  const documented = readDocumentPaths(lines, errors);
  const provided = providerPaths(routes, errors);

  const documentedKeys = new Set(documented.keys());
  const providedKeys = new Set(provided.keys());
  for (const missing of setDifference([...providedKeys].sort(), documentedKeys)) {
    errors.push(`admin_openapi_path_missing: ${missing}: registered by ${options.routes}, absent from the document`);
  }
  for (const orphan of setDifference([...documentedKeys].sort(), providedKeys)) {
    errors.push(`admin_openapi_path_orphan: ${orphan}: documented but no route registers it`);
  }
  for (const path of [...providedKeys].sort()) {
    const actual = provided.get(path);
    const declared = documented.get(path);
    if (declared === undefined) continue;
    if (actual.join(",") !== declared.join(",")) {
      errors.push(`admin_openapi_method_mismatch: ${path}: server=${actual.join(",")} document=${declared.join(",")}`);
    }
  }

  let operations = 0;
  for (const methods of documented.values()) operations += methods.length;
  return { errors: sortedSet(errors), paths: documented.size, operations };
}

function main() {
  try {
    const options = parseArguments(process.argv.slice(2));
    const { errors, paths, operations } = checkAdminOpenapi(options);
    if (errors.length > 0) {
      process.stderr.write(`${errors.join("\n")}\n`);
      process.exitCode = 1;
      return;
    }
    process.stdout.write(`admin_openapi_ok: ${paths} paths, ${operations} operations\n`);
  } catch (error) {
    const code =
      error instanceof AdminOpenapiError ? error.message : `admin_openapi_check_failed: ${error.message}`;
    process.stderr.write(`${code}\n`);
    process.exitCode = 1;
  }
}

if (process.argv[1] && resolve(process.argv[1]) === resolve(SCRIPT_PATH)) {
  main();
}
