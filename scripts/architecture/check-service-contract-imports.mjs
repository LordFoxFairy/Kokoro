#!/usr/bin/env node
// Peers bind a service's published contract, never its implementation.
//
// Each Platform service package exports two entry points: the root, which re-exports its
// application services, servers, repositories and domain types, and `./contract`, which exposes
// only the HTTP schemas module. A peer needs the second. Importing the first for a two-field
// response schema drags the whole service in -- `@kokoro/user` alone brings Prisma, Fastify,
// ioredis, jose and nodemailer -- and couples the caller to internals it must not see.
//
// It also decides how much survives the services being split into separate repositories. What a
// peer imports today is what has to be published tomorrow; if that is the package root, the split
// stops being a packaging change and becomes a rewrite.
//
// The sibling dependency gate reads package.json, where both spellings look identical, so this
// rule can only be enforced at the import site.
//
// `platform-kit` is exempt: it is the shared library every service builds on, not a service with a
// wire contract of its own.
//
// The workspace root is exempt too, for the reason the sibling gate already encodes: a parent that
// *contains* these packages is their composition root, not their peer. `platform-registry.ts`
// assembles module descriptors into one deployable, which is an implementation relationship by
// definition -- there is no wire between them to put a contract on.

import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative, resolve } from "node:path";

const ROOT = resolve(import.meta.dirname, "..", "..");
const DEFAULT_SOURCE = join(ROOT, "kokoro-platform");

// Shared libraries, not services. Importing these at the root is the intended use.
const SHARED_LIBRARIES = new Set(["@kokoro/platform-kit"]);

// The published narrow entry every service peer must use.
const CONTRACT_SUBPATH = "/contract";

const SKIP_DIRECTORIES = new Set(["node_modules", "generated", "dist", ".git", "prisma", ".turbo"]);

const IMPORT_RE = /(?:from|import)\s*\(?\s*["'](?<spec>@kokoro\/[^"']+)["']/gu;

class ContractImportError extends Error {
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
      else if (entry.endsWith(".ts") || entry.endsWith(".mjs")) out.push(full);
    }
  };
  walk(root);
  return out.sort();
}

// The package that owns a file, so a service importing its own root is not a cross-service edge.
function owningPackage(file, root) {
  const rel = relative(root, file);
  const [first] = rel.split("/");
  return first ?? "";
}

function packageNames(root) {
  const names = new Map();
  for (const entry of readdirSync(root)) {
    if (SKIP_DIRECTORIES.has(entry)) continue;
    const manifest = join(root, entry, "package.json");
    try {
      const parsed = JSON.parse(readFileSync(manifest, "utf8"));
      names.set(parsed.name, {
        directory: entry,
        // Whether the target actually publishes the entry a peer is required to use. A package with
        // no peers has not needed one yet; saying so beats telling the caller to import a path that
        // does not exist.
        publishesContract: Object.hasOwn(parsed.exports ?? {}, `.${CONTRACT_SUBPATH}`),
      });
    } catch {
      // Not a package directory.
    }
  }
  return names;
}

export function scan(root) {
  const files = sourceFiles(root);
  if (files.length === 0) throw new ContractImportError("contract_imports_no_sources", relative(ROOT, root));
  const directories = packageNames(root);
  if (directories.size === 0) {
    throw new ContractImportError("contract_imports_no_packages", relative(ROOT, root));
  }

  const violations = [];
  let contractImports = 0;
  let sharedImports = 0;
  let compositionImports = 0;

  for (const file of files) {
    const owner = owningPackage(file, root);
    // Not inside any child package -> workspace-root code, i.e. the composition root.
    const isCompositionRoot = ![...directories.values()].some((entry) => entry.directory === owner);
    const lines = readFileSync(file, "utf8").split(/\r?\n/u);
    for (const [index, line] of lines.entries()) {
      for (const match of line.matchAll(IMPORT_RE)) {
        const spec = match.groups?.spec ?? "";
        const base = spec.split("/").slice(0, 2).join("/");
        if (SHARED_LIBRARIES.has(base)) {
          sharedImports += 1;
          continue;
        }
        const target = directories.get(base);
        // Not a workspace service package; nothing this rule governs.
        if (target === undefined) continue;
        // A package importing itself by name still resolves to its own root; not a peer edge.
        if (target.directory === owner) continue;
        if (isCompositionRoot) {
          compositionImports += 1;
          continue;
        }
        if (spec === `${base}${CONTRACT_SUBPATH}`) {
          contractImports += 1;
          continue;
        }
        violations.push(
          target.publishesContract
            ? `contract_imports_not_narrow: ${relative(ROOT, file)}:${index + 1}: imports "${spec}"; ` +
              `a peer must bind "${base}${CONTRACT_SUBPATH}", not the package root`
            : `contract_imports_no_contract_entry: ${relative(ROOT, file)}:${index + 1}: imports ` +
              `"${spec}", but ${base} publishes no "${CONTRACT_SUBPATH}" entry; add one exposing its ` +
              `HTTP schemas module and import that, rather than reaching into the package root`,
        );
      }
    }
  }

  return { files: files.length, contractImports, sharedImports, compositionImports, violations };
}

export function run(root) {
  const { files, contractImports, sharedImports, compositionImports, violations } = scan(root);
  if (violations.length > 0) {
    throw new ContractImportError(violations[0].split(":", 1)[0], violations.sort().join("; "), {
      preformatted: true,
    });
  }
  return (
    `service_contract_imports_ok: ${files} sources, ${contractImports} cross-service imports all ` +
    `via ${CONTRACT_SUBPATH}, ${compositionImports} composition-root imports, ` +
    `${sharedImports} shared-library imports exempt`
  );
}

function main(argv) {
  const flag = argv.indexOf("--source");
  const root = flag === -1 ? DEFAULT_SOURCE : resolve(argv[flag + 1] ?? "");
  try {
    process.stdout.write(`${run(root)}\n`);
  } catch (error) {
    if (!(error instanceof ContractImportError)) throw error;
    process.stderr.write(`${error.message}\n`);
    return 1;
  }
  return 0;
}

if (process.argv[1] === import.meta.filename) {
  process.exitCode = main(process.argv.slice(2));
}
