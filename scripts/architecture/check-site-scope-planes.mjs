#!/usr/bin/env node
// Keep unscoped reads on the operator plane.
//
// Some Platform repository and service methods take their Site key optionally, so that operators
// can list across every Site. That is legitimate on the admin plane and nowhere else: the same
// method reached from a user-facing route returns every Site's rows to one Site's user.
//
// Three fail-opens have already shipped in this shape -- a missing isolation value degrading to
// *no isolation* rather than a refusal, each one documented in a comment as intended:
//
//   1. KOKORO_SITE_ID falling back to "site-local"
//   2. resolveModelBindings treating an absent site as "hide nothing"
//   3. GET /model-labels applying no Site filter at all
//
// All three were found by reading, not by a gate. This one freezes the currently-clean state: every
// call that *declines to scope* -- omitting the Site argument or passing a literal `undefined` --
// must sit in an admin-plane file.
//
// Blind spot, recorded rather than hidden: a call passing a variable that happens to be undefined at
// runtime reads as scoped here. This gate proves intent at the callsite, not the value on the wire.

import { readdirSync, readFileSync, statSync } from "node:fs";
import { basename, join, relative, resolve } from "node:path";

const ROOT = resolve(import.meta.dirname, "..", "..");
const DEFAULT_SOURCE = join(ROOT, "kokoro-platform");

// Platform isolation keys. A method taking one of these optionally is an unscoped read.
const ISOLATION_KEYS = ["siteId", "ownerId", "workspaceId", "tenantId"];

// Files allowed to make an unscoped call. The operator plane is declared per service with
// declareRouteAccess(app, "/admin", "admin"); these are the modules that plane routes to.
const ADMIN_PLANE_FILES = ["admin-routes.ts", "admin-contract.ts"];

const SKIP_DIRECTORIES = new Set(["node_modules", "generated", "dist", ".git", "prisma"]);

class SiteScopeError extends Error {
  // Violations already carry their own code, so `preformatted` stops it being printed twice.
  constructor(code, detail, { preformatted = false } = {}) {
    super(preformatted ? detail : `${code}: ${detail}`);
    this.code = code;
  }
}

function sourceFiles(root) {
  const out = [];
  const walk = (dir) => {
    for (const entry of readdirSync(dir)) {
      if (SKIP_DIRECTORIES.has(entry)) continue;
      const full = join(dir, entry);
      if (statSync(full).isDirectory()) walk(full);
      else if (entry.endsWith(".ts") && !entry.includes(".test.")) out.push(full);
    }
  };
  walk(root);
  return out.sort();
}

// A declaration whose first parameter is an optionally-supplied isolation key:
//   listUsers(siteId?: string, options?: ListOptions)
//   listSiteModelPolicies(siteId: string | undefined)
const OPTIONAL_KEY_RE = new RegExp(
  String.raw`(?:^|\s)(?:async\s+)?(\w+)\s*\(\s*(?:${ISOLATION_KEYS.join("|")})\s*(?:\?\s*:|:\s*string\s*\|\s*undefined)`,
  "u",
);

function declaredUnscopedMethods(files) {
  const methods = new Map();
  for (const file of files) {
    for (const [index, line] of readFileSync(file, "utf8").split(/\r?\n/u).entries()) {
      const match = OPTIONAL_KEY_RE.exec(line);
      if (match?.[1] === undefined) continue;
      if (!methods.has(match[1])) methods.set(match[1], []);
      methods.get(match[1]).push(`${relative(ROOT, file)}:${index + 1}`);
    }
  }
  return methods;
}

// A call that declines to scope: no arguments at all, or `undefined` in the Site position.
function unscopedCallRe(method) {
  return new RegExp(String.raw`\.${method}\s*\(\s*(?:\)|undefined\s*[,)])`, "u");
}

function isAdminPlane(file) {
  return ADMIN_PLANE_FILES.includes(basename(file));
}

export function scan(root) {
  const files = sourceFiles(root);
  if (files.length === 0) throw new SiteScopeError("site_scope_no_sources", relative(ROOT, root));

  const methods = declaredUnscopedMethods(files);
  if (methods.size === 0) {
    // Reading clean because the parser stopped matching is the failure this gate exists to avoid.
    throw new SiteScopeError("site_scope_no_declarations", "no optional-isolation-key method found");
  }

  const violations = [];
  let unscopedCalls = 0;
  for (const file of files) {
    const lines = readFileSync(file, "utf8").split(/\r?\n/u);
    for (const [index, line] of lines.entries()) {
      for (const method of methods.keys()) {
        if (!unscopedCallRe(method).test(line)) continue;
        unscopedCalls += 1;
        if (isAdminPlane(file)) continue;
        violations.push(
          `site_scope_unscoped_call: ${relative(ROOT, file)}:${index + 1}: ${method} is called ` +
            "without a Site; unscoped reads belong on the admin plane",
        );
      }
    }
  }

  return { files: files.length, methods, unscopedCalls, violations };
}

export function run(root) {
  const { files, methods, unscopedCalls, violations } = scan(root);
  if (violations.length > 0) {
    throw new SiteScopeError(violations[0].split(":", 1)[0], violations.sort().join("; "), {
      preformatted: true,
    });
  }
  return (
    `site_scope_planes_ok: ${files} sources, ${methods.size} methods take an optional Site, ` +
    `${unscopedCalls} unscoped calls, all on the admin plane`
  );
}

function main(argv) {
  const flag = argv.indexOf("--source");
  const root = flag === -1 ? DEFAULT_SOURCE : resolve(argv[flag + 1] ?? "");
  try {
    process.stdout.write(`${run(root)}\n`);
  } catch (error) {
    if (!(error instanceof SiteScopeError)) throw error;
    process.stderr.write(`${error.message}\n`);
    return 1;
  }
  return 0;
}

if (process.argv[1] === import.meta.filename) {
  process.exitCode = main(process.argv.slice(2));
}
