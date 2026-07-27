import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, resolve } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";
import { hasCompetingActiveAuthority, requiredVariables } from "./manager.mjs";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const manager = resolve(root, "scripts/infra/manager.mjs");

function run(args) {
  return spawnSync(process.execPath, [manager, ...args], {
    cwd: root,
    encoding: "utf8",
  });
}

test("builds a sanitized canonical compose invocation for selected capabilities", async () => {
  const directory = await mkdtemp(resolve(tmpdir(), "kokoro-infra-manager-"));
  const envFile = resolve(directory, "test.env");
  const secret = "must-not-appear-in-output";
  await writeFile(envFile, `MYSQL_ROOT_PASSWORD=${secret}\nMINIO_ROOT_PASSWORD=${secret}\n`);
  try {
    const result = run([
      "config",
      "--dry-run",
      "--profiles",
      "runtime,storage",
      "--scope",
      "dev",
      "--infra-env-file",
      envFile,
      "--json",
    ]);
    assert.equal(result.status, 0, result.stderr);
    assert.doesNotMatch(result.stdout, new RegExp(secret));
    const plan = JSON.parse(result.stdout);
    assert.equal(plan.projectName, "kokoro-infra");
    assert.deepEqual(plan.profiles, ["runtime", "storage"]);
    assert.deepEqual(plan.services, ["redis", "mongo", "minio"]);
    assert.equal(plan.environmentScope, "dev");
    assert.equal(plan.resourcePrefix, "kokoro-infra_kokoro");
    assert.equal(plan.envFile, "<provided>");
    assert.equal(plan.mutatesState, false);
    assert.equal(plan.argv.includes("-p"), false);
    assert.deepEqual(
      plan.argv.slice(0, 3),
      ["compose", "--project-name", "kokoro-infra"],
    );
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
});

test("legacy entrypoints delegate infra lifecycle to the root manager", async () => {
  const provision = await readFile(resolve(root, "deploy/provision.sh"), "utf8");
  const closure = await readFile(resolve(root, "scripts/closure-up.py"), "utf8");
  assert.match(provision, /scripts\/infra\/manager\.mjs["']?\s+ensure/u);
  assert.doesNotMatch(provision, /INFRA_PROJECT|-p\s+\$?"?INFRA/u);
  assert.match(provision, /--infra-env-file/u);
  assert.doesNotMatch(provision, /manager\.mjs[^\n]*--env-file/u);
  assert.match(closure, /scripts["']?\s*\/\s*["']infra["']?\s*\/\s*["']manager\.mjs/u);
  assert.doesNotMatch(closure, /["']-p["']\s*,\s*["']kokoro-infra["']/u);
  assert.match(closure, /["']--infra-env-file["']/u);
  assert.doesNotMatch(closure, /["']--env-file["']/u);
});

test("requires only non-default credentials for the selected services", () => {
  assert.deepEqual(requiredVariables(["mysql"]), ["MYSQL_ROOT_PASSWORD", "MYSQL_PASSWORD"]);
  assert.deepEqual(requiredVariables(["redis", "mongo"]), []);
});

test("offers a fixed-project refresh path for configuration-dependent services", () => {
  const result = run([
    "refresh", "--dry-run", "--profiles", "model", "--scope", "dev", "--json",
  ]);
  assert.equal(result.status, 0, result.stderr);
  const plan = JSON.parse(result.stdout);
  assert.equal(plan.action, "refresh");
  assert.equal(plan.mutatesState, true);
  assert.ok(plan.argv.includes("--force-recreate"));
  assert.ok(plan.argv.includes("litellm"));
});

test("rejects active stateful Kokoro projects but ignores unrelated Docker projects", () => {
  assert.equal(hasCompetingActiveAuthority({
    containers: [{ project: "personal-db", service: "mysql", name: "mysql", status: "Up 1 hour" }],
  }), false);
  assert.equal(hasCompetingActiveAuthority({
    containers: [{ project: "kokoro-platform", service: "mysql", name: "db", status: "running" }],
  }), true);
});

test("rejects site-derived, unsafe, or unsupported lifecycle arguments", () => {
  for (const args of [
    ["config", "--dry-run", "--profiles", "runtime", "--scope", "site-blue"],
    ["config", "--dry-run", "--profiles", "unknown", "--scope", "dev"],
    ["config", "--dry-run", "--profiles", "runtime", "--scope", "../dev"],
    ["config", "--dry-run", "--profiles", "runtime", "--scope", "dev", "-p", "other"],
  ]) {
    const result = run(args);
    assert.notEqual(result.status, 0);
    assert.match(result.stderr, /infra_arguments_invalid|infra_scope_invalid/);
  }
});

test("root compose encodes one authority, explicit identities, profiles and bounded secrets", async () => {
  const compose = await readFile(resolve(root, "docker-compose.infra.yml"), "utf8");
  assert.match(compose, /^name:\s+kokoro-infra$/mu);
  assert.match(compose, /name:\s+"\$\{KOKORO_NETWORK:-kokoro-net\}"/u);
  assert.doesNotMatch(compose, /env_file:/u);
  assert.doesNotMatch(compose, /restart:\s+(?:always|unless-stopped)\s*$/mu);
  assert.match(compose, /restart:\s+"\$\{KOKORO_INFRA_RESTART_POLICY:-no\}"/u);
  for (const profile of ["platform", "runtime", "storage", "model"]) {
    assert.match(compose, new RegExp(`profiles:\\s*\\[[^\\]]*${profile}[^\\]]*\\]`, "u"));
  }
  for (const volume of ["mysql", "redis", "mongo", "minio"]) {
    assert.match(
      compose,
      new RegExp(`name:\\s+"?\\$\\{KOKORO_INFRA_SCOPE:-kokoro-infra_kokoro\\}-${volume}"?`, "u"),
    );
  }
  for (const image of ["mysql", "redis", "mongo", "minio/minio", "ghcr.io/berriai/litellm"]) {
    assert.match(compose, new RegExp(`image:\\s+${image.replaceAll("/", "\\/")}:[^\\s@]+@sha256:[0-9a-f]{64}`, "u"));
  }
});
