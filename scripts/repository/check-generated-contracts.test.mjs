import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { mkdtemp, mkdir, readFile, readdir, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { resolve } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

import {
  GeneratedContractError,
  compareGeneratedMirror,
  parseArguments,
} from "./check-generated-contracts.mjs";
import * as generatedChecker from "./check-generated-contracts.mjs";

const repositoryRoot = resolve(fileURLToPath(new URL("../..", import.meta.url)));

const adminAuthSourcePaths = [
  "kokoro/common/v1/error.proto",
  "kokoro/common/v1/receipt.proto",
  "kokoro/platform/admin/v1/admin_auth.proto",
  "kokoro/platform/admission/v1/admission.proto",
];

async function sourceDigest(directory, sourcePaths) {
  const hash = createHash("sha256");
  for (const sourcePath of sourcePaths) {
    hash.update(`${sourcePath}\0`);
    hash.update(await readFile(resolve(directory, sourcePath)));
    hash.update("\0");
  }
  return hash.digest("hex");
}

async function artifactDigest(directory, current = directory) {
  const entries = await readdir(current, { withFileTypes: true });
  const chunks = [];
  for (const entry of entries.sort((left, right) => left.name.localeCompare(right.name))) {
    const path = resolve(current, entry.name);
    if (entry.isDirectory()) chunks.push(...(await artifactDigest(directory, path)));
    else if (entry.isFile() && entry.name !== "contract-metadata.ts") {
      const relativePath = path.slice(directory.length + 1).replaceAll("\\", "/");
      chunks.push(Buffer.from(`${relativePath}\0`), await readFile(path), Buffer.from("\0"));
    }
  }
  if (current !== directory) return chunks;
  return createHash("sha256").update(Buffer.concat(chunks)).digest("hex");
}

async function withTrees(run) {
  const root = await mkdtemp(resolve(tmpdir(), "kokoro-generated-contract-test-"));
  const expected = resolve(root, "expected");
  const mirror = resolve(root, "mirror");
  await mkdir(resolve(expected, "nested"), { recursive: true });
  await mkdir(resolve(mirror, "nested"), { recursive: true });
  try {
    await run({ root, expected, mirror });
  } finally {
    await rm(root, { recursive: true, force: true });
  }
}

test("accepts a byte-identical generated mirror", async () => {
  await withTrees(async ({ expected, mirror }) => {
    await writeFile(resolve(expected, "nested/service_pb.ts"), "same\n", "utf8");
    await writeFile(resolve(mirror, "nested/service_pb.ts"), "same\n", "utf8");

    await compareGeneratedMirror(expected, mirror, "fixture");
  });
});

test("rejects missing, extra and byte-different generated files", async () => {
  for (const mode of ["missing", "extra", "different"]) {
    await withTrees(async ({ expected, mirror }) => {
      await writeFile(resolve(expected, "nested/service_pb.ts"), "expected\n", "utf8");
      if (mode !== "missing") {
        await writeFile(
          resolve(mirror, "nested/service_pb.ts"),
          mode === "different" ? "different\n" : "expected\n",
          "utf8",
        );
      }
      if (mode === "extra") await writeFile(resolve(mirror, "extra.ts"), "extra\n", "utf8");

      await assert.rejects(
        compareGeneratedMirror(expected, mirror, "fixture"),
        (error) => error instanceof GeneratedContractError && error.code === "generated_contract_drift",
      );
    });
  }
});

test("production arguments are closed", () => {
  assert.deepEqual(parseArguments([]), { root: process.cwd() });
  assert.throws(() => parseArguments(["--output", "/tmp/out"]), {
    name: "GeneratedContractError",
    code: "generated_contract_arguments_invalid",
  });
});

test("checker forwards a single closed output argument through pnpm", () => {
  assert.equal(typeof generatedChecker.generationCommandArguments, "function");
  assert.deepEqual(
    generatedChecker.generationCommandArguments("/repo/contract", "/tmp/generated"),
    ["--dir", "/repo/contract", "run", "buf:generate", "--output", "/tmp/generated"],
  );
});

test("generation emits pinned source metadata into every committed mirror", async () => {
  const packageJson = JSON.parse(await readFile(resolve(repositoryRoot, "contract/package.json"), "utf8"));
  assert.equal(packageJson.scripts["buf:generate"], "node generate.mjs");

  const expectedDigest = await sourceDigest(resolve(repositoryRoot, "contract/proto"), adminAuthSourcePaths);
  for (const mirror of [
    "kokoro-platform/kokoro-platform-admin/src/generated/contracts",
    "kokoro-web/apps/admin/lib/generated/contracts",
  ]) {
    const metadataPath = resolve(repositoryRoot, mirror, "contract-metadata.ts");
    const metadata = await readFile(metadataPath, "utf8").catch(() => null);
    assert.notEqual(metadata, null, `${mirror} is missing contract-metadata.ts`);
    const expectedArtifactDigest = await artifactDigest(resolve(repositoryRoot, mirror));
    assert.match(metadata, new RegExp(`sourceDigestSha256: "${expectedDigest}"`, "u"));
    assert.match(metadata, new RegExp(`artifactDigestSha256: "${expectedArtifactDigest}"`, "u"));
    assert.notEqual(expectedArtifactDigest, expectedDigest);
    assert.match(metadata, /schemaId: "kokoro\.platform\.admin\.v1\.AdminAuthService"/u);
    assert.match(metadata, /generatorVersion: "2\.13\.0"/u);
    assert.match(metadata, /runtimeVersion: "2\.13\.0"/u);
    for (const sourcePath of adminAuthSourcePaths) assert.match(metadata, new RegExp(sourcePath, "u"));
    assert.doesNotMatch(metadata, /kokoro\/platform\/admin\/v2\/admin_(?:query|command)\.proto/u);
  }
});

test("federated contract CI runs the pinned Buf and generated-mirror gates", async () => {
  const workflow = await readFile(resolve(repositoryRoot, ".github/workflows/contract.yml"), "utf8");

  assert.match(workflow, /pnpm --dir contract install --frozen-lockfile/u);
  assert.match(workflow, /pnpm --dir contract run buf:format:check/u);
  assert.match(workflow, /pnpm --dir contract run buf:lint/u);
  assert.match(workflow, /pnpm --dir contract run openapi:lint/u);
  assert.match(workflow, /node scripts\/repository\/check-generated-contracts\.mjs/u);
});
