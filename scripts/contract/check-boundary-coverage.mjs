#!/usr/bin/env node

import { readFile, readdir } from "node:fs/promises";
import { dirname, extname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const repositoryRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const SOURCE_EXTENSIONS = new Set([".js", ".mjs", ".py", ".ts", ".tsx"]);
const CONSUMER_ROOTS = [
  { repository: "kokoro-agent", path: "kokoro-agent/src" },
  { repository: "kokoro-session", path: "kokoro-session/src" },
];
const EDGE_DETECTORS = [
  {
    repository: "kokoro-session",
    providerBoundary: "service.platform",
    patterns: [/KOKORO_CREDIT_BASE_URL/u, /KOKORO_MODEL_BASE_URL/u],
  },
  {
    repository: "kokoro-agent",
    providerBoundary: "platform.hub",
    patterns: [
      /KOKORO_HUB_RPC_URL/u,
      /resolve_execution_assembly/u,
      /fetch_skill_artifact/u,
    ],
  },
  {
    repository: "kokoro-agent",
    providerBoundary: "platform.litellm",
    patterns: [/KOKORO_LITELLM_BASE_URL/u, /KOKORO_LITELLM_API_KEY/u],
  },
];

export class BoundaryCoverageError extends Error {
  constructor(code, detail = "") {
    super(`${code}${detail === "" ? "" : `: ${detail}`}`);
    this.name = "BoundaryCoverageError";
    this.code = code;
    this.detail = detail;
  }
}

async function sourceFiles(path) {
  const entries = await readdir(path, { withFileTypes: true }).catch((error) => {
    if (error.code === "ENOENT") return [];
    throw error;
  });
  const files = [];
  for (const entry of entries.sort((left, right) => left.name.localeCompare(right.name))) {
    if (entry.name === "__pycache__") continue;
    const child = resolve(path, entry.name);
    if (entry.isDirectory()) files.push(...await sourceFiles(child));
    else if (entry.isFile() && SOURCE_EXTENSIONS.has(extname(entry.name))) files.push(child);
  }
  return files;
}

function registeredEdge(boundaries, repository, providerBoundary) {
  return boundaries.some((boundary) =>
    boundary?.lifecycle === "active" &&
    boundary?.provider?.repository === "kokoro-platform" &&
    boundary.provider.boundary === providerBoundary &&
    Array.isArray(boundary.consumers) &&
    boundary.consumers.some((consumer) => consumer?.repository === repository),
  );
}

export async function checkBoundaryCoverage({ root = repositoryRoot, registry }) {
  if (registry === null || typeof registry !== "object" || !Array.isArray(registry.boundaries)) {
    throw new BoundaryCoverageError("boundary_coverage_registry");
  }
  const discovered = new Set();
  let scannedSources = 0;
  for (const consumer of CONSUMER_ROOTS) {
    const files = await sourceFiles(resolve(root, consumer.path));
    scannedSources += files.length;
    for (const file of files) {
      const source = await readFile(file, "utf8");
      for (const detector of EDGE_DETECTORS) {
        if (
          detector.repository === consumer.repository &&
          detector.patterns.some((pattern) => pattern.test(source))
        ) {
          discovered.add(`${consumer.repository}->${detector.providerBoundary}`);
        }
      }
    }
  }
  const edges = [...discovered].sort();
  const missing = edges.filter((edge) => {
    const [repository, providerBoundary] = edge.split("->");
    return !registeredEdge(registry.boundaries, repository, providerBoundary);
  });
  if (missing.length > 0) {
    throw new BoundaryCoverageError("boundary_coverage_missing", missing.join(","));
  }
  return { scannedSources, edges };
}

async function main(argv) {
  let root = repositoryRoot;
  let registryPath = resolve(repositoryRoot, "contract/registry/boundaries.yaml");
  for (let index = 0; index < argv.length; index += 2) {
    const option = argv[index];
    const value = argv[index + 1];
    if (value === undefined) throw new BoundaryCoverageError("boundary_coverage_arguments");
    if (option === "--root") root = resolve(value);
    else if (option === "--registry") registryPath = resolve(value);
    else throw new BoundaryCoverageError("boundary_coverage_arguments", option);
  }
  const registry = JSON.parse(await readFile(registryPath, "utf8"));
  const result = await checkBoundaryCoverage({ root, registry });
  process.stdout.write(
    `boundary_coverage_ok: ${result.scannedSources} sources, ${result.edges.length} internal service edges all registered\n`,
  );
}

if (process.argv[1] && pathToFileURL(process.argv[1]).href === import.meta.url) {
  try {
    await main(process.argv.slice(2));
  } catch (error) {
    const message = error instanceof BoundaryCoverageError ? error.message : "boundary_coverage_failed";
    process.stderr.write(`${message}\n`);
    process.exitCode = 1;
  }
}
