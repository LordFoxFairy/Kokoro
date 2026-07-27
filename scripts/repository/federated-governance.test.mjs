import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const manifestPath = resolve(root, "config/repository/authority-documents.json");
const expectedDocuments = [
  "README.md",
  "docs/CODEBASE_MAP.md",
  "docs/CURRENT.md",
  "docs/kokoro-handbook/decisions/ADR-007-kokoro-platform-submodule.md",
  "docs/kokoro-handbook/technical/01-repository-map.md",
  "docs/superpowers/plans/2026-07-25-kokoro-production-delivery-program.md",
  "docs/superpowers/plans/2026-07-26-wave-0-repository-contract-foundation-implementation-plan.md",
  "docs/superpowers/plans/2026-07-27-federated-repository-governance-correction-implementation-plan.md",
  "docs/superpowers/specs/2026-07-25-platform-web-session-target-architecture-design.md",
  "docs/superpowers/specs/2026-07-25-wave-0-repository-contract-foundation-design.md",
];

const executableCutoverPatterns = [
  /^\s*(?:[$>]\s*)?git\s+rm[^\n]*\.gitmodules/imu,
  /^\s*-\s*Delete:\s*`?\.gitmodules/imu,
  /^\s*-\s*(?:\[[ x]\]\s*)?replace gitlinks? with ordinary tracked trees/imu,
  /repository:\s*LordFoxFairy\/kokoro-[\s\S]{0,160}?ref:\s*main/iu,
  /^\s*-\s*\[[ x]\]\s*(?:delete|remove|删除)[^\n]*(?:child|子仓)[^\n]*(?:lock|CI)/imu,
];

test("authority inventory is complete and closed", async () => {
  const manifest = JSON.parse(await readFile(manifestPath, "utf8"));
  assert.deepEqual(Object.keys(manifest).sort(), ["documents", "repositoryTopology"]);
  assert.equal(manifest.repositoryTopology, "federated-submodules-v1");
  assert.deepEqual([...manifest.documents].sort(), [...expectedDocuments].sort());
});

test("every active authority declares the settled topology without executable cutover steps", async () => {
  for (const path of expectedDocuments) {
    const source = await readFile(resolve(root, path), "utf8");
    assert.match(source, /repositoryTopology:\s*federated-submodules-v1/u, `${path} topology`);
    for (const pattern of executableCutoverPatterns) {
      assert.doesNotMatch(source, pattern, `${path} contains ${pattern}`);
    }
  }
});

test("canonical authorities state deployment and remote-protocol ownership", async () => {
  const map = await readFile(resolve(root, "docs/CODEBASE_MAP.md"), "utf8");
  assert.match(map, /独立(?:构建|部署)[\s\S]{0,120}独立(?:发布|回滚)/u);
  assert.match(map, /跨(?:子)?仓[\s\S]{0,120}(?:HTTP|RPC)[\s\S]{0,120}SSE/u);
  assert.match(map, /不得[\s\S]{0,80}(?:兄弟仓源码|跨服务直写数据库)/u);

  const current = await readFile(resolve(root, "docs/CURRENT.md"), "utf8");
  assert.match(current, /2026-07-27-federated-repository-governance-correction-implementation-plan\.md/u);
  assert.match(current, /ADR-007-kokoro-platform-submodule\.md/u);
});

test("negated historical terminology is not treated as an executable cutover", () => {
  const valid = "repositoryTopology: federated-submodules-v1\n不得删除 `.gitmodules`，snapshot import 已取消。";
  for (const pattern of executableCutoverPatterns) assert.doesNotMatch(valid, pattern);
});
