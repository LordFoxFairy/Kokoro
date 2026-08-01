import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { cp, mkdir, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

import {
  breakingArguments,
  PrelaunchProtobufBreakingError,
} from "./check-prelaunch-protobuf-breaking.mjs";

const repositoryRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const against = "../.git#branch=HEAD,subdir=contract";

async function withCurrentContract(run) {
  const root = await mkdtemp(join(tmpdir(), "kokoro-protobuf-hard-cut-"));
  try {
    for (const path of [
      "contract/registry/prelaunch-protobuf-hard-cuts.yaml",
      "contract/proto/kokoro/platform/site/v1/site_lifecycle.proto",
      "contract/proto/kokoro/platform/site/v1/site_provisioning.proto",
      "contract/proto/kokoro/platform/site/v1/site_publication.proto",
    ]) {
      await mkdir(dirname(resolve(root, path)), { recursive: true });
      await cp(resolve(repositoryRoot, path), resolve(root, path));
    }
    execFileSync("git", ["init", "-q"], { cwd: root });
    execFileSync("git", ["config", "user.name", "Kokoro Contract Test"], { cwd: root });
    execFileSync("git", ["config", "user.email", "contract-test@kokoro.invalid"], { cwd: root });
    execFileSync("git", ["add", "contract"], { cwd: root });
    execFileSync("git", ["commit", "-qm", "current contract"], { cwd: root });
    await run(root);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
}

test("a current baseline runs full Buf breaking without persistent exclusions", async () => {
  await withCurrentContract(async (root) => {
    assert.deepEqual(breakingArguments({ root, against }), ["breaking", "--against", against]);
  });
});

test("the one-time exception rejects registry edits and candidate source drift", async () => {
  await withCurrentContract(async (root) => {
    const registryPath = resolve(root, "contract/registry/prelaunch-protobuf-hard-cuts.yaml");
    const source = await readFile(registryPath, "utf8");
    const registry = JSON.parse(source);
    registry.cuts[0].reason = "mutable waiver";
    await writeFile(registryPath, `${JSON.stringify(registry, null, 2)}\n`);
    assert.throws(
      () => breakingArguments({ root, against }),
      (error) => error instanceof PrelaunchProtobufBreakingError && error.code === "prelaunch_protobuf_hard_cut_registry_invalid",
    );
    await writeFile(registryPath, source);
    const lifecyclePath = resolve(root, "contract/proto/kokoro/platform/site/v1/site_lifecycle.proto");
    await writeFile(lifecyclePath, `${await readFile(lifecyclePath, "utf8")}\n`);
    assert.throws(
      () => breakingArguments({ root, against }),
      (error) => error instanceof PrelaunchProtobufBreakingError && error.code === "prelaunch_protobuf_hard_cut_candidate_invalid",
    );
  });
});
