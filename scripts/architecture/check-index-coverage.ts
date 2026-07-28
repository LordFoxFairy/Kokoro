#!/usr/bin/env node

import { existsSync, lstatSync, readFileSync, readdirSync } from "node:fs";
import { dirname, extname, join, normalize, relative, resolve, sep } from "node:path";

const REQUIRED_SECTIONS = [
  "Responsibilities",
  "Non-responsibilities",
  "Public boundary",
  "Callers and dependencies",
  "Data ownership and events",
  "Runtime and security",
  "Idempotency, failure, and recovery",
  "Extension rules and forbidden dependencies",
  "Current gotchas",
  "Verification",
];

const IGNORED_DIRECTORIES = new Set([
  ".git",
  ".idea",
  ".next",
  ".pytest_cache",
  ".ruff_cache",
  ".venv",
  "__pycache__",
  "generated",
  "node_modules",
  "templates",
  "tmp",
]);
const TEST_DIRECTORIES = new Set(["test", "tests"]);

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
  options.root = resolve(options.root);
  options.manifest = resolve(options.manifest);
  return options;
}

function parseManifest(path) {
  let manifest;
  try {
    manifest = JSON.parse(readFileSync(path, "utf8"));
  } catch (error) {
    fail(`manifest must be JSON-compatible YAML: ${error.message}`);
  }
  if (manifest?.schemaVersion !== 1) fail("manifest schemaVersion must equal 1");
  if (!Array.isArray(manifest.owners) || manifest.owners.length === 0) {
    fail("manifest owners must be a non-empty array");
  }
  if (!Array.isArray(manifest.roots) || manifest.roots.length === 0) {
    fail("manifest roots must be a non-empty array");
  }
  return manifest;
}

function assertRelativePath(value, label) {
  if (typeof value !== "string" || value.length === 0) fail(`${label} must be a non-empty string`);
  if (value.startsWith("/") || value.split(/[\\/]/u).includes("..")) {
    fail(`${label} must be repository-relative without '..': ${value}`);
  }
}

function normalizedRelative(value) {
  const normalized = normalize(value).split(sep).join("/");
  return normalized === "" ? "." : normalized;
}

function validateEntryShape(entry) {
  if (!entry || typeof entry !== "object" || Array.isArray(entry)) fail("root entry must be an object");
  if (typeof entry.id !== "string" || !/^[a-z0-9][a-z0-9.-]*$/u.test(entry.id)) {
    fail(`invalid root id: ${String(entry.id)}`);
  }
  assertRelativePath(entry.path, `root ${entry.id} path`);
  assertRelativePath(entry.index, `root ${entry.id} index`);
  if (entry.kind !== "boundary" && entry.kind !== "component") {
    fail(`root ${entry.id} kind must be boundary or component`);
  }
  if (!Array.isArray(entry.owners) || entry.owners.length === 0) fail(`root ${entry.id} owners required`);
  if (typeof entry.boundary !== "string" || entry.boundary.length === 0) fail(`root ${entry.id} boundary required`);
  if (typeof entry.language !== "string" || entry.language.length === 0) fail(`root ${entry.id} language required`);
  if (!Array.isArray(entry.signals) || entry.signals.length === 0) fail(`root ${entry.id} signals required`);
  for (const signal of entry.signals) assertRelativePath(signal, `root ${entry.id} signal`);
  if (!entry.dependencies || !Array.isArray(entry.dependencies.allow)) {
    fail(`root ${entry.id} dependencies.allow required`);
  }
  if (!Array.isArray(entry.verification) || entry.verification.length === 0) {
    fail(`root ${entry.id} verification required`);
  }
  for (const command of entry.verification) {
    assertRelativePath(command?.cwd, `root ${entry.id} verification cwd`);
    if (!Array.isArray(command?.argv) || command.argv.length === 0 || command.argv.some((part) => typeof part !== "string")) {
      fail(`root ${entry.id} verification argv must be a non-empty string array`);
    }
  }
}

function parseFrontmatter(markdown) {
  const match = /^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/u.exec(markdown);
  if (!match) return null;
  const result = { owners: [] };
  let listKey;
  for (const rawLine of match[1].split(/\r?\n/u)) {
    const keyValue = /^([A-Za-z][A-Za-z0-9]*):\s*(.*?)\s*$/u.exec(rawLine);
    if (keyValue) {
      const [, key, rawValue] = keyValue;
      listKey = rawValue === "" ? key : undefined;
      if (rawValue !== "") result[key] = rawValue.replace(/^['"]|['"]$/gu, "");
      else if (!(key in result)) result[key] = [];
      continue;
    }
    const item = /^\s+-\s+(.+?)\s*$/u.exec(rawLine);
    if (item && listKey) result[listKey].push(item[1].replace(/^['"]|['"]$/gu, ""));
  }
  return result;
}

function markdownLinks(markdown) {
  return [...markdown.matchAll(/!?(?:\[[^\]]*\])\(([^)\s]+)(?:\s+"[^"]*")?\)/gu)].map((match) => match[1]);
}

function sectionBody(markdown, section) {
  const escaped = section.replace(/[.*+?^${}()|[\]\\]/gu, "\\$&");
  const heading = new RegExp(`^##\\s+${escaped}\\s*$`, "imu").exec(markdown);
  if (!heading) return null;
  const rest = markdown.slice(heading.index + heading[0].length);
  const next = /^##\s+/mu.exec(rest);
  return (next ? rest.slice(0, next.index) : rest).trim();
}

function headingSlugs(markdown) {
  return [...markdown.matchAll(/^#{1,6}\s+(.+?)\s*$/gmu)].map((match) =>
    match[1].trim().toLowerCase().replace(/[^\w\s-]/gu, "").replace(/\s+/gu, "-"),
  );
}

function federatedChildPaths(root) {
  const modules = resolve(root, ".gitmodules");
  if (!existsSync(modules)) return [];
  return [...readFileSync(modules, "utf8").matchAll(/^\s*path\s*=\s*(.+?)\s*$/gmu)].map((match) =>
    normalizedRelative(match[1]),
  );
}

function isChildOwned(rootPath, childPaths) {
  return childPaths.some((child) => rootPath === child || rootPath.startsWith(`${child}/`));
}

function normalizeProse(value) {
  return value.toLowerCase().replace(/[^a-z0-9]+/gu, " ").trim();
}

function isTestFixtureRoot(root, path, entry) {
  if (!entry.isDirectory() || entry.name !== "fixtures") return false;
  const segments = normalizedRelative(relative(root, path)).split("/");
  return segments.slice(0, -1).some((segment) => TEST_DIRECTORIES.has(segment));
}

function walk(root, visitor, current = root) {
  for (const entry of readdirSync(current, { withFileTypes: true })) {
    if (entry.isDirectory() && IGNORED_DIRECTORIES.has(entry.name)) continue;
    const path = join(current, entry.name);
    if (isTestFixtureRoot(root, path, entry)) continue;
    if (entry.isSymbolicLink()) continue;
    visitor(path, entry);
    if (entry.isDirectory()) walk(root, visitor, path);
  }
}

function discover(root) {
  const indexes = new Set();
  const boundaries = new Set();
  walk(root, (path, entry) => {
    const name = entry.name;
    const relativePath = normalizedRelative(relative(root, path));
    if (entry.isFile() && name === "INDEX.md") indexes.add(relativePath);
    if (!entry.isFile()) return;
    if (name === "package.json" || name === "pyproject.toml" || name === "Dockerfile" || /^next\.config\./u.test(name)) {
      boundaries.add(normalizedRelative(dirname(relativePath)));
    }
  });
  return { indexes, boundaries };
}

function validateIndex(root, entry, errors) {
  const indexPath = resolve(root, entry.index);
  if (!existsSync(indexPath) || !lstatSync(indexPath).isFile()) {
    errors.push(`missing INDEX: ${entry.index}`);
    return;
  }
  const markdown = readFileSync(indexPath, "utf8");
  const frontmatter = parseFrontmatter(markdown);
  if (!frontmatter) {
    errors.push(`${entry.index}: missing architecture frontmatter`);
  } else {
    if (String(frontmatter.architectureIndex) !== "1") {
      errors.push(`${entry.index}: architectureIndex must equal 1`);
    }
    if (frontmatter.rootId !== entry.id) {
      errors.push(`${entry.index}: frontmatter rootId must equal ${entry.id}`);
    }
    if (JSON.stringify(frontmatter.owners) !== JSON.stringify(entry.owners)) {
      errors.push(`${entry.index}: frontmatter owners must equal manifest owners`);
    }
  }
  if (entry.kind === "boundary") {
    for (const section of REQUIRED_SECTIONS) {
      const body = sectionBody(markdown, section);
      if (body === null) {
        errors.push(`${entry.index}: missing required section: ${section}`);
        continue;
      }
      if (body.length === 0) {
        errors.push(`${entry.index}: required section is empty: ${section}`);
        continue;
      }
      // "N/A" is a legitimate answer for a genuinely inapplicable concern, but only with a stated reason.
      if (/^n\/a\b/iu.test(body) && !/^n\/a\s*[—:-]\s*\S/iu.test(body)) {
        errors.push(`${entry.index}: "N/A" section must state a reason: ${section}`);
      }
    }
    const publicBoundary = sectionBody(markdown, "Public boundary");
    if (publicBoundary && !/`[^`\n]+`/u.test(publicBoundary)) {
      errors.push(`${entry.index}: Public boundary must name at least one concrete entrypoint in backticks`);
    }
  }
  for (const target of markdownLinks(markdown)) {
    if (/^[a-z]+:/iu.test(target)) continue;
    const hash = target.indexOf("#");
    const pathOnly = decodeURIComponent(hash < 0 ? target : target.slice(0, hash));
    const anchor = hash < 0 ? "" : target.slice(hash + 1);
    const targetPath = pathOnly ? resolve(dirname(indexPath), pathOnly) : indexPath;
    if (pathOnly && !existsSync(targetPath)) {
      errors.push(`${entry.index}: broken relative link: ${target}`);
      continue;
    }
    if (anchor && !headingSlugs(readFileSync(targetPath, "utf8")).includes(anchor.toLowerCase())) {
      errors.push(`${entry.index}: broken link anchor: ${target}`);
    }
  }
}

function validateRepository(root, manifest) {
  const errors = [];
  const ids = new Set();
  const paths = new Set();
  const indexes = new Set();
  for (const entry of manifest.roots) {
    try {
      validateEntryShape(entry);
    } catch (error) {
      errors.push(error.message);
      continue;
    }
    const rootPath = normalizedRelative(entry.path);
    const indexPath = normalizedRelative(entry.index);
    if (ids.has(entry.id)) errors.push(`duplicate root id: ${entry.id}`);
    if (paths.has(rootPath)) errors.push(`duplicate root path: ${rootPath}`);
    if (indexes.has(indexPath)) errors.push(`duplicate INDEX path: ${indexPath}`);
    ids.add(entry.id);
    paths.add(rootPath);
    indexes.add(indexPath);
    const absoluteRoot = resolve(root, rootPath);
    if (!existsSync(absoluteRoot) || !lstatSync(absoluteRoot).isDirectory()) {
      errors.push(`missing root path: ${rootPath}`);
    }
    for (const signal of entry.signals) {
      if (!existsSync(resolve(root, signal))) errors.push(`root ${entry.id} missing signal: ${signal}`);
    }
    for (const command of entry.verification) {
      if (!existsSync(resolve(root, command.cwd))) {
        errors.push(`root ${entry.id} missing verification cwd: ${command.cwd}`);
      }
    }
    validateIndex(root, entry, errors);
  }
  for (const entry of manifest.roots) {
    if (entry.kind === "component" && !ids.has(entry.boundary)) {
      errors.push(`root ${entry.id} references unknown boundary: ${entry.boundary}`);
    }
    for (const dependency of entry.dependencies?.allow ?? []) {
      if (!ids.has(dependency)) errors.push(`root ${entry.id} allows unknown dependency: ${dependency}`);
    }
  }
  // Interchangeable boundary prose carries no navigational value. Root-owned boundaries only: a
  // federated child repository owns its own INDEX text and cannot be fixed from this repository.
  const childPaths = federatedChildPaths(root);
  const boundaryProse = new Map();
  for (const entry of manifest.roots) {
    if (entry.kind !== "boundary") continue;
    if (isChildOwned(normalizedRelative(entry.path), childPaths)) continue;
    const indexPath = resolve(root, entry.index);
    if (!existsSync(indexPath)) continue;
    const body = sectionBody(readFileSync(indexPath, "utf8"), "Public boundary");
    if (!body) continue;
    const key = normalizeProse(body);
    const previous = boundaryProse.get(key);
    if (previous) errors.push(`${entry.index}: Public boundary duplicates ${previous}`);
    else boundaryProse.set(key, entry.index);
  }
  const discovered = discover(root);
  for (const indexPath of discovered.indexes) {
    if (!indexes.has(indexPath)) errors.push(`unregistered INDEX: ${indexPath}`);
  }
  for (const boundaryPath of discovered.boundaries) {
    if (!paths.has(boundaryPath)) errors.push(`unregistered boundary: ${boundaryPath}`);
  }
  return [...new Set(errors)].sort();
}

function main() {
  try {
    const options = parseArguments(process.argv.slice(2));
    const manifest = parseManifest(options.manifest);
    const errors = validateRepository(options.root, manifest);
    if (errors.length > 0) {
      process.stderr.write(`${errors.join("\n")}\n`);
      process.exitCode = 1;
      return;
    }
    process.stdout.write(`INDEX coverage OK (${manifest.roots.length} roots)\n`);
  } catch (error) {
    process.stderr.write(`${error.message}\n`);
    process.exitCode = 1;
  }
}

main();
