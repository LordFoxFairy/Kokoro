#!/usr/bin/env node

import {
  existsSync,
  lstatSync,
  readFileSync,
  readdirSync,
  realpathSync,
} from "node:fs";
import {
  dirname,
  extname,
  isAbsolute,
  posix,
  relative,
  resolve,
  sep,
} from "node:path";

const IGNORED_DIRECTORIES = new Set([
  ".git",
  ".next",
  ".turbo",
  ".venv",
  "build",
  "coverage",
  "dist",
  "generated",
  "node_modules",
  "tmp",
]);
const SOURCE_EXTENSIONS = new Set([
  ".cjs",
  ".cts",
  ".js",
  ".jsx",
  ".mjs",
  ".mts",
  ".ts",
  ".tsx",
]);
const PROJECT_CONFIG = /^(?:Dockerfile(?:\..+)?|jsconfig(?:\..+)?\.json|package\.json|pnpm-workspace\.yaml|pyproject\.toml|tsconfig(?:\..+)?\.json|.+\.ya?ml)$/u;
const STATIC_MODULE_SPECIFIERS = [
  /\b(?:import|export)\s+(?:[^"'\n]*?\s+from\s*)?["']([^"']+)["']/gu,
  /\b(?:import|require)\s*\(\s*["']([^"']+)["']\s*\)/gu,
];
const EXACT_ROOT_ID = /^[a-z0-9][a-z0-9.-]*$/u;

function fail(message) {
  throw new Error(message);
}

function parseArguments(argv) {
  const options = { root: process.cwd(), manifest: "config/architecture/index-roots.yaml" };
  for (let index = 0; index < argv.length; index += 1) {
    const value = argv[index];
    if (value === "--root" || value === "--manifest") {
      const next = argv[index + 1];
      if (!next) fail(`missing value for ${value}`);
      options[value.slice(2)] = next;
      index += 1;
      continue;
    }
    fail(`unknown argument: ${value}`);
  }
  return { root: resolve(options.root), manifest: resolve(options.manifest) };
}

function parseManifest(path) {
  let manifest;
  try {
    manifest = JSON.parse(readFileSync(path, "utf8"));
  } catch (error) {
    fail(`manifest must be JSON-compatible YAML: ${error.message}`);
  }
  if (manifest?.schemaVersion !== 1) fail("manifest schemaVersion must equal 1");
  if (!Array.isArray(manifest.roots) || manifest.roots.length === 0) {
    fail("manifest roots must be a non-empty array");
  }
  return manifest;
}

function isCanonicalRepositoryPath(value) {
  return (
    typeof value === "string" &&
    value.length > 0 &&
    !value.includes("\0") &&
    !value.includes("\\") &&
    !isAbsolute(value) &&
    (value === "." || (posix.normalize(value) === value && !value.startsWith("../")))
  );
}

function isInsidePath(child, parent, allowEqual = true) {
  const remainder = relative(parent, child);
  if (remainder === "") return allowEqual;
  return remainder !== ".." && !remainder.startsWith(`..${sep}`) && !isAbsolute(remainder);
}

function rootRelative(root, path) {
  const value = relative(root, path).split(sep).join("/");
  return value === "" ? "." : value;
}

function validateRoots(root, entries, errors) {
  const byId = new Map();
  for (const entry of entries) {
    if (!entry || typeof entry !== "object" || Array.isArray(entry)) {
      errors.push("root entry must be an object");
      continue;
    }
    if (typeof entry.id !== "string" || !EXACT_ROOT_ID.test(entry.id)) {
      errors.push(`invalid root id: ${String(entry.id)}`);
      continue;
    }
    if (byId.has(entry.id)) errors.push(`duplicate root id: ${entry.id}`);
    byId.set(entry.id, entry);
    if (!isCanonicalRepositoryPath(entry.path)) {
      errors.push(`root ${entry.id} path must be canonical repository-relative POSIX path: ${String(entry.path)}`);
    }
    if (entry.kind !== "boundary" && entry.kind !== "component") {
      errors.push(`root ${entry.id} kind must be boundary or component`);
    }
    if (typeof entry.boundary !== "string" || !EXACT_ROOT_ID.test(entry.boundary)) {
      errors.push(`root ${entry.id} boundary must be an exact root id`);
    }
    if (!entry.dependencies || !Array.isArray(entry.dependencies.allow)) {
      errors.push(`root ${entry.id} dependencies.allow must be an array`);
    }
  }

  const repositoryRealPath = realpathSync(root);
  for (const entry of entries) {
    if (!entry?.id) continue;
    if (isCanonicalRepositoryPath(entry.path)) {
      const absolutePath = resolve(root, entry.path);
      if (!existsSync(absolutePath) || !lstatSync(absolutePath).isDirectory()) {
        errors.push(`root ${entry.id} path must be an existing directory: ${entry.path}`);
      } else if (!isInsidePath(realpathSync(absolutePath), repositoryRealPath)) {
        errors.push(`root ${entry.id} path escapes repository through symlink: ${entry.path}`);
      }
    }

    const owner = byId.get(entry.boundary);
    if (!owner || owner.kind !== "boundary") {
      errors.push(`root ${entry.id} references unknown public boundary: ${String(entry.boundary)}`);
    } else if (entry.kind === "boundary" && entry.boundary !== entry.id) {
      errors.push(`boundary ${entry.id} must own itself`);
    } else if (
      entry.kind === "component" &&
      (!isCanonicalRepositoryPath(owner.path) ||
        !isInsidePath(resolve(root, entry.path), resolve(root, owner.path), false))
    ) {
      errors.push(`component ${entry.id} must be nested inside boundary ${entry.boundary}`);
    }
  }
  return byId;
}

function validateDeclaredDependencies(entries, byId, errors) {
  const graph = new Map(entries.filter((entry) => entry?.id).map((entry) => [entry.id, []]));
  for (const entry of entries) {
    if (!entry?.id || !Array.isArray(entry.dependencies?.allow)) continue;
    const seen = new Set();
    for (const dependency of entry.dependencies.allow) {
      if (typeof dependency !== "string" || !EXACT_ROOT_ID.test(dependency)) {
        errors.push(
          `root ${entry.id} dependency must be an exact public boundary id: ${String(dependency)}`,
        );
        continue;
      }
      if (seen.has(dependency)) errors.push(`root ${entry.id} has duplicate dependency: ${dependency}`);
      seen.add(dependency);
      if (dependency === entry.id || dependency === entry.boundary) {
        errors.push(`root ${entry.id} cannot depend on itself`);
        continue;
      }
      const target = byId.get(dependency);
      if (!target) {
        errors.push(`root ${entry.id} allows unknown dependency: ${dependency}`);
        continue;
      }
      if (target.kind !== "boundary" || target.boundary !== target.id) {
        errors.push(`root ${entry.id} dependency must target a public boundary: ${dependency}`);
        continue;
      }
      graph.get(entry.id)?.push(dependency);
    }
  }
  findCycles(graph, errors);
}

function findCycles(graph, errors) {
  const visiting = new Set();
  const visited = new Set();
  const stack = [];
  const reported = new Set();

  function visit(id) {
    if (visiting.has(id)) {
      const start = stack.indexOf(id);
      const cycle = [...stack.slice(start), id];
      const key = [...new Set(cycle.slice(0, -1))].sort().join("|");
      if (!reported.has(key)) {
        reported.add(key);
        errors.push(`dependency cycle: ${cycle.join(" -> ")}`);
      }
      return;
    }
    if (visited.has(id)) return;
    visiting.add(id);
    stack.push(id);
    for (const dependency of [...(graph.get(id) ?? [])].sort()) visit(dependency);
    stack.pop();
    visiting.delete(id);
    visited.add(id);
  }

  for (const id of [...graph.keys()].sort()) visit(id);
}

function owningBoundary(path, root, boundaryEntries) {
  const candidates = boundaryEntries
    .filter((entry) => isCanonicalRepositoryPath(entry.path))
    .map((entry) => ({ entry, absolute: resolve(root, entry.path) }))
    .filter(({ absolute }) => isInsidePath(path, absolute))
    .sort((left, right) => right.absolute.length - left.absolute.length);
  return candidates[0]?.entry;
}

function validatePackageDependencies(root, entries, boundaryEntries, errors) {
  const packages = [];
  const packageByName = new Map();
  for (const entry of entries) {
    if (!isCanonicalRepositoryPath(entry?.path)) continue;
    const packagePath = resolve(root, entry.path, "package.json");
    if (!existsSync(packagePath)) continue;
    let manifest;
    try {
      manifest = JSON.parse(readFileSync(packagePath, "utf8"));
    } catch (error) {
      errors.push(`${rootRelative(root, packagePath)}: invalid package.json: ${error.message}`);
      continue;
    }
    if (typeof manifest.name !== "string" || manifest.name.length === 0) continue;
    const existing = packageByName.get(manifest.name);
    if (existing) {
      errors.push(
        `duplicate registered package name ${manifest.name}: ${existing.relativePath}, ${rootRelative(root, packagePath)}`,
      );
      continue;
    }
    const packageEntry = {
      entry,
      manifest,
      packagePath,
      relativePath: rootRelative(root, packagePath),
    };
    packageByName.set(manifest.name, packageEntry);
    packages.push(packageEntry);
  }

  let edgeCount = 0;
  for (const source of packages) {
    const dependencyNames = new Set();
    for (const field of ["dependencies", "devDependencies", "optionalDependencies", "peerDependencies"]) {
      const dependencies = source.manifest[field];
      if (!dependencies || typeof dependencies !== "object" || Array.isArray(dependencies)) continue;
      for (const name of Object.keys(dependencies)) dependencyNames.add(name);
    }
    for (const name of [...dependencyNames].sort()) {
      const target = packageByName.get(name);
      if (!target || target === source) continue;
      const sourceBoundary = owningBoundary(dirname(source.packagePath), root, boundaryEntries);
      const targetBoundary = owningBoundary(dirname(target.packagePath), root, boundaryEntries);
      if (!sourceBoundary || !targetBoundary || sourceBoundary.id === targetBoundary.id) continue;
      if (isInsidePath(dirname(target.packagePath), dirname(source.packagePath), false)) continue;
      edgeCount += 1;
      if (!source.entry.dependencies.allow.includes(targetBoundary.id)) {
        errors.push(
          `${source.relativePath}: package ${source.manifest.name} depends on ${targetBoundary.id} but ${source.entry.id} does not allow it`,
        );
      }
    }
  }
  return edgeCount;
}

function walk(current, visitor) {
  for (const entry of readdirSync(current, { withFileTypes: true })) {
    if (entry.isDirectory() && IGNORED_DIRECTORIES.has(entry.name)) continue;
    const path = resolve(current, entry.name);
    if (entry.isSymbolicLink()) continue;
    if (entry.isDirectory()) walk(path, visitor);
    else if (entry.isFile()) visitor(path, entry.name);
  }
}

function sourceSpecifiers(source) {
  const result = [];
  for (const pattern of STATIC_MODULE_SPECIFIERS) {
    pattern.lastIndex = 0;
    for (const match of source.matchAll(pattern)) result.push(match[1]);
  }
  return result;
}

function relativePathTokens(value) {
  return [...value.matchAll(/(?:^|[\s"'=:\[(])((?:\.\.?\/)+[A-Za-z0-9_@*./-]+)/gmu)].map(
    (match) => match[1],
  );
}

function configPaths(path, name) {
  const source = readFileSync(path, "utf8");
  if (name.endsWith(".json")) {
    let document;
    try {
      document = JSON.parse(source);
    } catch {
      return [];
    }
    const values = [];
    function collect(value) {
      if (typeof value === "string") values.push(value);
      else if (Array.isArray(value)) value.forEach(collect);
      else if (value && typeof value === "object") Object.values(value).forEach(collect);
    }
    collect(document);
    return values.flatMap(relativePathTokens);
  }
  return relativePathTokens(source);
}

function resolveReference(path, specifier) {
  const clean = specifier.split(/[?#]/u, 1)[0];
  return resolve(dirname(path), clean);
}

function validateSourceBoundaries(root, boundaryEntries, errors) {
  const repositoryPath = resolve(root);
  const serviceEntries = boundaryEntries.filter((entry) => entry.id.startsWith("service."));
  walk(root, (path, name) => {
    const owner = owningBoundary(path, root, serviceEntries);
    if (!owner) return;
    if (SOURCE_EXTENSIONS.has(extname(name))) {
      const source = readFileSync(path, "utf8");
      for (const specifier of sourceSpecifiers(source)) {
        if (!specifier.startsWith(".")) continue;
        const targetPath = resolveReference(path, specifier);
        if (!isInsidePath(targetPath, repositoryPath)) {
          errors.push(`${rootRelative(root, path)}: source import escapes repository: ${specifier}`);
          continue;
        }
        const target = owningBoundary(targetPath, root, serviceEntries);
        if (target && target.id !== owner.id) {
          errors.push(
            `${rootRelative(root, path)}: cross-boundary source import ${owner.id} -> ${target.id}: ${specifier}`,
          );
        }
      }
    }

    if (!PROJECT_CONFIG.test(name) || /(?:^|-)lock\.ya?ml$/u.test(name)) return;
    for (const specifier of configPaths(path, name)) {
      const targetPath = resolveReference(path, specifier);
      if (!isInsidePath(targetPath, repositoryPath)) {
        errors.push(`${rootRelative(root, path)}: project path escapes repository: ${specifier}`);
        continue;
      }
      const target = owningBoundary(targetPath, root, serviceEntries);
      if (target && target.id !== owner.id) {
        errors.push(
          `${rootRelative(root, path)}: cross-boundary source path ${owner.id} -> ${target.id}: ${specifier}`,
        );
      }
    }
  });
}

function validateRepository(root, manifest) {
  const errors = [];
  const byId = validateRoots(root, manifest.roots, errors);
  validateDeclaredDependencies(manifest.roots, byId, errors);
  const boundaryEntries = manifest.roots.filter(
    (entry) => entry?.kind === "boundary" && entry.boundary === entry.id,
  );
  const packageEdges = validatePackageDependencies(root, manifest.roots, boundaryEntries, errors);
  validateSourceBoundaries(root, boundaryEntries, errors);
  return { errors: [...new Set(errors)].sort(), packageEdges };
}

function main() {
  try {
    const options = parseArguments(process.argv.slice(2));
    const manifest = parseManifest(options.manifest);
    const { errors, packageEdges } = validateRepository(options.root, manifest);
    if (errors.length > 0) {
      process.stderr.write(`${errors.join("\n")}\n`);
      process.exitCode = 1;
      return;
    }
    process.stdout.write(
      `Dependency boundaries OK (${manifest.roots.length} roots, ${packageEdges} internal package ${packageEdges === 1 ? "edge" : "edges"})\n`,
    );
  } catch (error) {
    process.stderr.write(`${error.message}\n`);
    process.exitCode = 1;
  }
}

main();
