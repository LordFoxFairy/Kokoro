import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import test from "node:test";

const root = resolve(import.meta.dirname, "../..");

function yamlDocuments(source) {
  return source.split(/^---\s*$/mu).map((document) => document.trim()).filter(Boolean);
}

function deploymentName(document) {
  if (!/^kind:\s*Deployment$/mu.test(document)) return null;
  return document.match(/^metadata:\s*\{\s*name:\s*([^,}\s]+)/mu)?.[1] ?? null;
}

test("every workload mounting the shared workspace declares the writable pod group", async () => {
  const sources = await Promise.all([
    readFile(resolve(root, "deploy/k8s/base/app.yaml"), "utf8"),
    readFile(resolve(root, "deploy/k8s/base/platform.yaml"), "utf8"),
  ]);
  const workspaceDeployments = sources
    .flatMap(yamlDocuments)
    .filter((document) => document.includes("claimName: kokoro-workspace"))
    .map((document) => ({ name: deploymentName(document), document }));

  assert.deepEqual(
    workspaceDeployments.map(({ name }) => name).sort(),
    ["kokoro-agent-worker", "kokoro-hub", "kokoro-hub-runtime", "kokoro-session"],
  );
  for (const { name, document } of workspaceDeployments) {
    assert.match(document, /^\s{6}securityContext:\s*$/mu, `${name} must set a pod securityContext`);
    assert.match(document, /^\s{8}fsGroup:\s*1001\s*$/mu, `${name} must mount workspace as group 1001`);
    assert.match(
      document,
      /^\s{8}fsGroupChangePolicy:\s*OnRootMismatch\s*$/mu,
      `${name} must avoid recursive ownership scans after the first mount`,
    );
  }
});

test("root CI runs the complete non-container infra contract suite", async () => {
  const workflow = await readFile(resolve(root, ".github/workflows/contract.yml"), "utf8");
  assert.match(workflow, /node --test scripts\/infra\/\*\.test\.mjs/u);
});
