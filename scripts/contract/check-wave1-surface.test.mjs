import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

const here = dirname(fileURLToPath(import.meta.url));
const root = resolve(here, "../..");
const checker = resolve(here, "check-wave1-surface.mjs");

test("the shipped Wave 1 surface is closed and internally consistent", () => {
  const result = spawnSync(process.execPath, [checker, "--root", root], { encoding: "utf8" });

  assert.equal(result.status, 0, result.stderr);
  assert.equal(
    result.stdout,
    "wave1_surface_ok: 22 public operations, 4 privileged services, 5 contract-only boundaries\n",
  );
});

test("the checker fails closed when invoked outside a Wave 1 contract root", () => {
  const result = spawnSync(process.execPath, [checker, "--root", here], { encoding: "utf8" });

  assert.equal(result.status, 1);
  assert.match(result.stderr, /^wave1_surface_failed:/u);
});
