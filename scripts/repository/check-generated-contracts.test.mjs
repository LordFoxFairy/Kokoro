import assert from "node:assert/strict";
import { mkdtemp, mkdir, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { resolve } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

import {
  GeneratedContractError,
  compareGeneratedMirror,
  parseArguments,
} from "./check-generated-contracts.mjs";

const repositoryRoot = resolve(fileURLToPath(new URL("../..", import.meta.url)));

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

test("federated contract CI runs the pinned Buf and generated-mirror gates", async () => {
  const workflow = await readFile(resolve(repositoryRoot, ".github/workflows/contract.yml"), "utf8");

  assert.match(workflow, /pnpm --dir contract install --frozen-lockfile/u);
  assert.match(workflow, /pnpm --dir contract run buf:format:check/u);
  assert.match(workflow, /pnpm --dir contract run buf:lint/u);
  assert.match(workflow, /node scripts\/repository\/check-generated-contracts\.mjs/u);
});
