import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, resolve } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";
import * as managerApi from "./manager.mjs";

const { buildPlan, hasCompetingActiveAuthority, requiredVariables } = managerApi;

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
  assert.deepEqual(requiredVariables(["litellm"]), [
    "LITELLM_MASTER_KEY",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "OPENAI_COMPAT_BASE_URL",
    "OPENAI_COMPAT_API_KEY",
  ]);
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
    ["config", "--dry-run", "--profiles", "runtime", "--scope", "blue"],
    ["config", "--dry-run", "--profiles", "runtime", "--scope", "opaque-123"],
    ["config", "--dry-run", "--profiles", "runtime", "--scope", "tenant-acme"],
    ["config", "--dry-run", "--profiles", "runtime", "--scope", "workspace-demo"],
    ["config", "--dry-run", "--profiles", "unknown", "--scope", "dev"],
    ["config", "--dry-run", "--profiles", "runtime", "--scope", "../dev"],
    ["config", "--dry-run", "--profiles", "runtime", "--scope", "dev", "-p", "other"],
  ]) {
    const result = run(args);
    assert.notEqual(result.status, 0);
    assert.match(result.stderr, /infra_arguments_invalid|infra_scope_invalid/);
  }
});

test("accepts only named environment categories and bounded CI scopes", () => {
  for (const scope of ["dev", "staging", "production", "ci-federated", "ci-a1"]) {
    const result = run(["config", "--dry-run", "--profiles", "runtime", "--scope", scope]);
    assert.equal(result.status, 0, `${scope}: ${result.stderr}`);
  }
  const overlong = run([
    "config", "--dry-run", "--profiles", "runtime", "--scope", `ci-${"a".repeat(25)}`,
  ]);
  assert.notEqual(overlong.status, 0);
  assert.match(overlong.stderr, /infra_scope_invalid/u);
});

function canonicalContainer({ service, scope = "dev", source }) {
  const destinations = {
    mysql: "/var/lib/mysql",
    redis: "/data",
    mongo: "/data/db",
    minio: "/data",
  };
  return {
    service,
    scope,
    mounts: source === undefined ? [] : [{
      type: "volume",
      source,
      destination: destinations[service],
    }],
  };
}

async function plan(action, profiles = ["runtime"], scope = "dev") {
  return buildPlan({
    action,
    dryRun: false,
    json: false,
    profiles,
    scope,
    envFile: "/tmp/example.env",
    mode: "development",
  });
}

test("matching canonical scope label and stateful mount is idempotent", async () => {
  const input = await plan("ensure");
  const output = managerApi.convergeCanonicalScope(input, [
    canonicalContainer({
      service: "redis",
      source: "kokoro-infra_kokoro-redis",
    }),
  ]);
  assert.equal(output.scopeTransition, "matching");
  assert.deepEqual(output.services, ["redis", "mongo"]);
  assert.equal(output.executionArgv.includes("--no-recreate"), false);
});

test("no canonical containers requires no scope transition", async () => {
  const output = managerApi.convergeCanonicalScope(await plan("ensure"), []);
  assert.equal(output.scopeTransition, "absent");
  assert.equal(output.executionArgv.includes("--no-recreate"), false);
});

test("canonical preflight inspection projects only service, scope label, and mounts", () => {
  const calls = [];
  const runDocker = (args) => {
    calls.push(args);
    if (args[0] === "ps") return { status: 0, stdout: "container-id\n", stderr: "" };
    if (args[2].includes(".Config.Labels")) {
      return { status: 0, stdout: "redis\tdev\n", stderr: "" };
    }
    return {
      status: 0,
      stdout: "volume\tkokoro-infra_kokoro-redis\t/data\n",
      stderr: "",
    };
  };
  assert.deepEqual(managerApi.inspectCanonicalContainers(runDocker), [{
    service: "redis",
    scope: "dev",
    mounts: [{
      type: "volume",
      source: "kokoro-infra_kokoro-redis",
      destination: "/data",
    }],
  }]);
  assert.ok(calls[0].includes("label=com.docker.compose.project=kokoro-infra"));
  assert.ok(calls.slice(1).every((args) => args.includes("--format")));
  assert.doesNotMatch(JSON.stringify(calls), /\.Config\.Env|\.Config\.Cmd/u);
  const mountFormat = calls.find((args) => args.some((value) => value.includes(".Mounts")));
  assert.ok(mountFormat?.some((value) => value.includes(".Name")));
  assert.equal(mountFormat?.some((value) => value.includes(".Source")), false);
});

test("wrong scope label is a mismatch", async () => {
  const input = await plan("ensure");
  assert.throws(
    () => managerApi.convergeCanonicalScope(
      input,
      [canonicalContainer({ service: "redis", scope: "staging", source: "kokoro-infra_kokoro-redis" })],
    ),
    /infra_scope_transition_requires_full/u,
  );
});

test("correct scope label with wrong stateful mount is a mismatch", async () => {
  const input = await plan("ensure");
  assert.throws(
    () => managerApi.convergeCanonicalScope(input, [
      canonicalContainer({ service: "redis", source: "other-prefix-redis" }),
    ]),
    /infra_scope_transition_requires_full/u,
  );
});

test("full mismatch force recreates the complete service set", async () => {
  const input = await plan("ensure", ["full"], "staging");
  const output = managerApi.convergeCanonicalScope(input, [
    canonicalContainer({ service: "redis", scope: "dev", source: "kokoro-infra_kokoro-redis" }),
  ]);
  assert.equal(output.scopeTransition, "force-full-recreate");
  assert.deepEqual(output.services, ["mysql", "redis", "mongo", "minio", "litellm"]);
  assert.ok(output.executionArgv.includes("--force-recreate"));
  assert.equal(output.executionArgv.includes("--no-recreate"), false);
  for (const service of output.services) assert.ok(output.executionArgv.includes(service));
});

test("partial mismatch fails with a stable transition code", async () => {
  const input = await plan("refresh", ["model"], "staging");
  assert.throws(
    () => managerApi.convergeCanonicalScope(input, [
      canonicalContainer({ service: "litellm", scope: "dev" }),
    ]),
    /infra_scope_transition_requires_full/u,
  );
});

test("stop and status fail loudly against a mismatched canonical scope", async () => {
  for (const action of ["stop", "status"]) {
    const input = await plan(action, ["runtime"], "staging");
    assert.throws(
      () => managerApi.convergeCanonicalScope(input, [
        canonicalContainer({ service: "redis", scope: "dev", source: "kokoro-infra_kokoro-redis" }),
      ]),
      /infra_scope_mismatch/u,
    );
  }
});

test("postflight rejects a requested scope that did not converge", async () => {
  const input = await plan("ensure", ["runtime"], "staging");
  assert.throws(
    () => managerApi.assertCanonicalPostcondition(input, [
      canonicalContainer({ service: "redis", scope: "dev", source: "kokoro-infra_kokoro-redis" }),
    ]),
    /infra_scope_convergence_failed/u,
  );
  assert.doesNotThrow(() => managerApi.assertCanonicalPostcondition(input, [
    canonicalContainer({ service: "redis", scope: "staging", source: "kokoro-infra-staging-redis" }),
    canonicalContainer({ service: "mongo", scope: "staging", source: "kokoro-infra-staging-mongo" }),
  ]));
});

test("root compose encodes one authority, explicit identities, profiles and bounded secrets", async () => {
  const compose = await readFile(resolve(root, "docker-compose.infra.yml"), "utf8");
  const litellm = compose.split("  litellm:", 2)[1]?.split("\nvolumes:", 1)[0] ?? "";
  assert.match(compose, /^name:\s+kokoro-infra$/mu);
  assert.match(compose, /name:\s+"\$\{KOKORO_NETWORK:-kokoro-net\}"/u);
  assert.doesNotMatch(compose, /env_file:/u);
  assert.doesNotMatch(compose, /restart:\s+(?:always|unless-stopped)\s*$/mu);
  assert.match(compose, /restart:\s+"\$\{KOKORO_INFRA_RESTART_POLICY:-no\}"/u);
  assert.equal((compose.match(/io\.kokoro\.infra\.scope:/gu) ?? []).length, 5);
  assert.doesNotMatch(compose, /(?:^|["'])\.\/kokoro-[^:"']+/mu);
  assert.match(compose, /\.\/config\/infra\/litellm\.config\.example\.yaml/u);
  assert.doesNotMatch(litellm, /\bcurl\b/u);
  assert.match(litellm, /urllib\.request\.urlopen/u);
  for (const variable of [
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "OPENAI_COMPAT_BASE_URL",
    "OPENAI_COMPAT_API_KEY",
  ]) {
    assert.match(compose, new RegExp(`${variable}:\\s+"\\$\\{${variable}:-\\}"`, "u"));
  }
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

test("infrastructure policy derives volume identity from the canonical resource prefix", async () => {
  const policy = JSON.parse(await readFile(
    resolve(root, "config/repository/infrastructure-policy.yaml"),
    "utf8",
  ));
  assert.equal(policy.authority.volumeNameTemplate, "{resourcePrefix}-{service}");
});

test("root owns the example LiteLLM configuration", async () => {
  const config = await readFile(resolve(root, "config/infra/litellm.config.example.yaml"), "utf8");
  assert.match(config, /model_name:\s+kokoro-openai-gpt-4o-mini/u);
  assert.match(config, /master_key:\s+os\.environ\/LITELLM_MASTER_KEY/u);
  assert.doesNotMatch(config, /(?:sk-|api[_-]?key:\s+["']?[A-Za-z0-9]{16})/iu);
});
