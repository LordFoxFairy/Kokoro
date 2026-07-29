import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { copyFile, cp, mkdir, mkdtemp, readFile, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

const here = dirname(fileURLToPath(import.meta.url));
const root = resolve(here, "../..");
const checker = resolve(here, "check-wave1-surface.mjs");

async function makeFixture() {
  const fixture = await mkdtemp(resolve(tmpdir(), "kokoro-wave1-surface-"));
  await mkdir(resolve(fixture, "contract/openapi"), { recursive: true });
  await mkdir(resolve(fixture, "contract/registry"), { recursive: true });
  await cp(resolve(root, "contract/proto"), resolve(fixture, "contract/proto"), { recursive: true });
  await copyFile(
    resolve(root, "contract/openapi/platform-public-v1.yaml"),
    resolve(fixture, "contract/openapi/platform-public-v1.yaml"),
  );
  await copyFile(
    resolve(root, "contract/registry/boundaries.yaml"),
    resolve(fixture, "contract/registry/boundaries.yaml"),
  );
  await copyFile(resolve(root, "contract/generate.mjs"), resolve(fixture, "contract/generate.mjs"));
  return fixture;
}

test("the shipped Wave 1 surface is closed and internally consistent", () => {
  const result = spawnSync(process.execPath, [checker, "--root", root], { encoding: "utf8" });

  assert.equal(result.status, 0, result.stderr);
  assert.equal(
    result.stdout,
    "wave1_surface_ok: 23 public operations, 4 privileged services, 5 contract-only boundaries\n",
  );
});

test("the live command checks the Wave 1 surface from the current working directory", () => {
  const result = spawnSync(process.execPath, [checker], { cwd: root, encoding: "utf8" });

  assert.equal(result.status, 0, result.stderr);
  assert.equal(
    result.stdout,
    "wave1_surface_ok: 23 public operations, 4 privileged services, 5 contract-only boundaries\n",
  );
});

test("the checker fails closed when invoked outside a Wave 1 contract root", () => {
  const result = spawnSync(process.execPath, [checker, "--root", here], { encoding: "utf8" });

  assert.equal(result.status, 1);
  assert.match(result.stderr, /^wave1_surface_failed:/u);
});

test("an operation cannot erase workload security with an empty override", async () => {
  const fixture = await makeFixture();
  const openapi = resolve(fixture, "contract/openapi/platform-public-v1.yaml");
  const source = await readFile(openapi, "utf8");
  await writeFile(
    openapi,
    source.replace(
      "      operationId: beginRegistration\n",
      "      operationId: beginRegistration\n      security: []\n",
    ),
  );

  const result = spawnSync(process.execPath, [checker, "--root", fixture], { encoding: "utf8" });

  assert.equal(result.status, 1, result.stdout);
  assert.match(result.stderr, /public_operation_security_missing:beginRegistration/u);
});
