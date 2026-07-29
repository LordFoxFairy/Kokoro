import { spawnSync } from "node:child_process";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const repositoryRoot = resolve(here, "../..");
const reader = resolve(here, "read-openapi.py");
const methods = new Set(["delete", "get", "head", "options", "patch", "post", "put", "trace"]);

export function readOpenApiDocument(source) {
  const result = spawnSync("uv", ["run", "--locked", "python", reader], {
    cwd: repositoryRoot,
    input: source,
    encoding: "utf8",
    maxBuffer: 4 * 1024 * 1024,
  });
  if (result.status !== 0) {
    const detail = result.stderr.trim() || result.error?.message || "strict OpenAPI reader failed";
    throw new Error(detail);
  }
  try {
    return JSON.parse(result.stdout);
  } catch (error) {
    throw new Error(`strict OpenAPI reader returned invalid JSON: ${error.message}`);
  }
}

export function openApiOperations(document) {
  const operations = new Map();
  for (const [path, item] of Object.entries(document.paths)) {
    for (const [rawMethod, operation] of Object.entries(item)) {
      const method = rawMethod.toLowerCase();
      if (!methods.has(method)) continue;
      operations.set(operation.operationId, { method, path, operation });
    }
  }
  return operations;
}
