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
  assert.deepEqual(requiredVariables(["postgres"]), ["POSTGRES_PASSWORD"]);
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

test("stateful profiles cannot use force-recreate refresh", async () => {
  await assert.rejects(
    plan("refresh", ["full"]),
    /infra_destructive_operation_forbidden: stateful refresh/u,
  );
});

test("rejects active stateful Kokoro projects and unlabeled exact authority signals", async () => {
  const input = await plan("ensure", ["platform"]);
  assert.equal(hasCompetingActiveAuthority({
    containers: [{ project: "personal-db", service: "mysql", name: "mysql", status: "Up 1 hour" }],
  }, input), false);
  assert.equal(hasCompetingActiveAuthority({
    containers: [{ project: "kokoro-platform", service: "mysql", name: "db", status: "running" }],
  }, input), true);
  for (const container of [
    { project: "", service: "", name: "kokoro-infra-mysql-1", status: "running" },
    { project: "", service: "", name: "legacy-db", status: "running", volumes: ["kokoro-infra_kokoro-mysql"] },
    { project: "", service: "", name: "legacy-db", status: "running", ports: "127.0.0.1:3307->3306/tcp" },
  ]) {
    assert.equal(hasCompetingActiveAuthority({ containers: [container] }, input), true);
  }
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

function canonicalContainer({
  service,
  scope = "dev",
  source,
  authMarker = ["mysql", "postgres", "minio"].includes(service) ? `${service}-auth-v1` : "",
  profile = {
    mysql: "platform",
    postgres: "postgres-transition",
    redis: "runtime",
    mongo: "runtime",
    minio: "storage",
    litellm: "model",
  }[service] ?? "",
  dataMarker = ["mysql", "postgres", "redis", "mongo", "minio"].includes(service)
    ? `${service}-data-v1`
    : "",
}) {
  const destinations = {
    mysql: "/var/lib/mysql",
    postgres: "/var/lib/postgresql",
    redis: "/data",
    mongo: "/data/db",
    minio: "/data",
  };
  return {
    id: `container-${service}`,
    service,
    scope,
    profile,
    dataMarker,
    authMarker,
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
  assert.equal(output.executionArgv.includes("--no-recreate"), true);
});

test("no canonical containers requires no scope transition", async () => {
  const output = managerApi.convergeCanonicalScope(await plan("ensure"), []);
  assert.equal(output.scopeTransition, "absent");
  assert.equal(output.executionArgv.includes("--no-recreate"), true);
});

test("canonical preflight inspection projects only service, scope label, and mounts", () => {
  const calls = [];
  const runDocker = (args) => {
    calls.push(args);
    if (args[0] === "ps") return { status: 0, stdout: "container-id\n", stderr: "" };
    if (args[2].includes(".Config.Labels")) {
      return {
        status: 0,
        stdout: "redis\tdev\truntime\tredis-data-v1\t<no value>\n",
        stderr: "",
      };
    }
    return {
      status: 0,
      stdout: "volume\tkokoro-infra_kokoro-redis\t/data\n",
      stderr: "",
    };
  };
  assert.deepEqual(managerApi.inspectCanonicalContainers(runDocker), [{
    id: "container-id",
    service: "redis",
    scope: "dev",
    profile: "runtime",
    dataMarker: "redis-data-v1",
    authMarker: "",
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
    /infra_scope_transition_requires_explicit_activation/u,
  );
});

test("correct scope label with wrong stateful mount is a mismatch", async () => {
  const input = await plan("ensure");
  assert.throws(
    () => managerApi.convergeCanonicalScope(input, [
      canonicalContainer({ service: "redis", source: "other-prefix-redis" }),
    ]),
    /infra_scope_transition_requires_explicit_activation/u,
  );
});

test("generic full ensure never force-recreates preserved services on a scope mismatch", async () => {
  const input = await plan("ensure", ["full"], "staging");
  assert.throws(
    () => managerApi.convergeCanonicalScope(input, [
      canonicalContainer({ service: "redis", scope: "dev", source: "kokoro-infra_kokoro-redis" }),
    ]),
    /infra_scope_transition_requires_explicit_activation/u,
  );
  assert.equal(input.executionArgv.includes("--force-recreate"), false);
  assert.equal(input.executionArgv.includes("--no-recreate"), true);
});

test("stateful and mixed ensure plans preserve all existing containers on ordinary config drift", async () => {
  for (const profiles of [["platform"], ["runtime"], ["full"], ["postgres-transition"]]) {
    const input = await plan("ensure", profiles);
    assert.ok(input.executionArgv.includes("--no-recreate"), profiles.join(","));
    assert.equal(input.executionArgv.includes("--force-recreate"), false);
  }
  assert.equal((await plan("ensure", ["model"])).executionArgv.includes("--no-recreate"), false);
});

test("persistent target inspection resolves exact volume labels and every mount user", async () => {
  const input = await plan("ensure", ["platform"]);
  const calls = [];
  const runDocker = (args) => {
    calls.push(args);
    if (args[0] === "volume") {
      return {
        status: 0,
        stdout: "kokoro-infra_kokoro-mysql\tkokoro-infra\tmysql-data\tmysql-data-v1\n",
        stderr: "",
      };
    }
    if (args[0] === "ps") return { status: 0, stdout: "mysql-id\n", stderr: "" };
    return {
      status: 0,
      stdout: "kokoro-infra\tmysql\tkokoro-infra-mysql-1\t127.0.0.1:3307->3306/tcp\n",
      stderr: "",
    };
  };
  assert.deepEqual(managerApi.inspectPersistentTargets(input, runDocker), [{
    service: "mysql",
    name: "kokoro-infra_kokoro-mysql",
    exists: true,
    project: "kokoro-infra",
    composeVolume: "mysql-data",
    dataMarker: "mysql-data-v1",
    mountUsers: [{
      id: "mysql-id",
      project: "kokoro-infra",
      service: "mysql",
      name: "kokoro-infra-mysql-1",
      ports: "127.0.0.1:3307->3306/tcp",
    }],
  }]);
  assert.ok(calls[0].includes("volume"));
  assert.ok(calls.some((args) => args.includes("volume=kokoro-infra_kokoro-mysql")));
  assert.doesNotMatch(JSON.stringify(calls), /\.Config\.Env|\.Mounts.*\.Source/u);
});

test("existing persistent targets fail closed before compose when ownership is ambiguous", async () => {
  const input = await plan("ensure", ["platform"]);
  const mysql = canonicalContainer({
    service: "mysql",
    source: "kokoro-infra_kokoro-mysql",
    authMarker: "mysql-auth-v1",
  });
  const validTarget = {
    service: "mysql",
    name: "kokoro-infra_kokoro-mysql",
    exists: true,
    project: "kokoro-infra",
    composeVolume: "mysql-data",
    dataMarker: "mysql-data-v1",
    mountUsers: [{
      id: mysql.id,
      project: "kokoro-infra",
      service: "mysql",
      name: "kokoro-infra-mysql-1",
      ports: "127.0.0.1:3307->3306/tcp",
    }],
  };
  assert.doesNotThrow(() => managerApi.assertPersistentTargetCompatibility(input, [mysql], [validTarget]));
  assert.throws(
    () => managerApi.assertPersistentTargetCompatibility(input, [], [{ ...validTarget, mountUsers: [] }]),
    /infra_persistent_volume_orphaned: mysql/u,
  );
  assert.throws(
    () => managerApi.assertPersistentTargetCompatibility(input, [mysql], [{ ...validTarget, project: "", dataMarker: "" }]),
    /infra_persistent_volume_ownership_missing: mysql/u,
  );
  assert.throws(
    () => managerApi.assertPersistentTargetCompatibility(input, [mysql], [{
      ...validTarget,
      mountUsers: [{ ...validTarget.mountUsers[0], id: "unknown", project: "" }],
    }]),
    /infra_persistent_volume_unknown_mount: mysql/u,
  );
});

test("pre-Task2A canonical volumes use explicit legacy evidence without recreating services", async () => {
  const input = await plan("ensure", ["full"]);
  const legacyContainers = [
    ["mysql", "kokoro-infra_kokoro-mysql"],
    ["redis", "kokoro-infra_kokoro-redis"],
    ["mongo", "kokoro-infra_kokoro-mongo"],
    ["minio", "kokoro-infra_kokoro-minio"],
  ].map(([service, source]) => canonicalContainer({
    service,
    source,
    authMarker: "",
    profile: "",
    dataMarker: "",
  }));
  const legacyTargets = legacyContainers.map((container) => ({
    service: container.service,
    name: container.mounts[0].source,
    exists: true,
    project: "kokoro-infra",
    composeVolume: `${container.service}-data`,
    dataMarker: "",
    mountUsers: [{
      id: container.id,
      project: "kokoro-infra",
      service: container.service,
      name: `kokoro-infra-${container.service}-1`,
      ports: "",
    }],
  }));

  const evidence = managerApi.assertPersistentTargetCompatibility(input, legacyContainers, legacyTargets);
  assert.deepEqual([...evidence.legacyServices].sort(), ["minio", "mongo", "mysql", "redis"]);
  assert.doesNotThrow(() => managerApi.assertPersistentAuthCompatibility(
    legacyContainers,
    { mysql: "mysql-auth-v1", minio: "minio-auth-v1" },
    evidence,
  ));
  assert.equal(input.executionArgv.includes("--no-recreate"), true);

  const credentialInputs = [];
  assert.doesNotThrow(() => managerApi.probePersistentCredentials(
    input,
    legacyContainers,
    {
      MYSQL_ROOT_PASSWORD: "legacy-root",
      MYSQL_USER: "kokoro",
      MYSQL_PASSWORD: "legacy-app",
      MYSQL_DATABASE: "kokoro",
    },
    (_args, options) => {
      credentialInputs.push(options.input);
      return { status: 0, stdout: "", stderr: "" };
    },
  ));
  assert.deepEqual(credentialInputs, ["legacy-root\n", "legacy-app\n"]);
});

test("missing data markers are legacy-only evidence, never a new-volume bypass", async () => {
  const input = await plan("ensure", ["platform"]);
  const currentMysql = canonicalContainer({
    service: "mysql",
    source: "kokoro-infra_kokoro-mysql",
  });
  const legacyMysql = {
    ...currentMysql,
    profile: "",
    dataMarker: "",
    authMarker: "",
  };
  const markerlessTarget = {
    service: "mysql",
    name: "kokoro-infra_kokoro-mysql",
    exists: true,
    project: "kokoro-infra",
    composeVolume: "mysql-data",
    dataMarker: "",
    mountUsers: [{
      id: currentMysql.id,
      project: "kokoro-infra",
      service: "mysql",
      name: "kokoro-infra-mysql-1",
      ports: "127.0.0.1:3307->3306/tcp",
    }],
  };
  assert.throws(
    () => managerApi.assertPersistentTargetCompatibility(input, [currentMysql], [markerlessTarget]),
    /infra_persistent_data_marker_missing: mysql/u,
  );
  assert.throws(
    () => managerApi.assertPersistentTargetCompatibility(input, [], [{
      ...markerlessTarget,
      mountUsers: [],
    }]),
    /infra_persistent_volume_orphaned: mysql/u,
  );
  assert.throws(
    () => managerApi.assertPersistentTargetCompatibility(input, [legacyMysql], [{
      ...markerlessTarget,
      dataMarker: "mysql-data-v0",
    }]),
    /infra_persistent_data_marker_drift: mysql/u,
  );
  assert.throws(
    () => managerApi.assertPersistentTargetCompatibility(input, [legacyMysql], [{
      ...markerlessTarget,
      mountUsers: [{ ...markerlessTarget.mountUsers[0], id: "unknown", project: "" }],
    }]),
    /infra_persistent_volume_unknown_mount: mysql/u,
  );
});

test("partial mismatch fails with a stable transition code", async () => {
  const input = await plan("refresh", ["model"], "staging");
  assert.throws(
    () => managerApi.convergeCanonicalScope(input, [
      canonicalContainer({ service: "litellm", scope: "dev" }),
    ]),
    /infra_scope_transition_requires_explicit_activation/u,
  );
});

test("persistent credentials fail fast when an attached volume has a different auth generation", () => {
  const mountedMysql = canonicalContainer({
    service: "mysql",
    source: "kokoro-infra_kokoro-mysql",
    authMarker: "mysql-auth-v1",
  });
  assert.doesNotThrow(() => managerApi.assertPersistentAuthCompatibility(
    [mountedMysql],
    { mysql: "mysql-auth-v1" },
  ));
  assert.throws(
    () => managerApi.assertPersistentAuthCompatibility(
      [mountedMysql],
      { mysql: "mysql-auth-v2" },
    ),
    /infra_persistent_auth_drift: mysql/u,
  );
  assert.doesNotThrow(() => managerApi.assertPersistentAuthCompatibility(
    [{ ...mountedMysql, authMarker: "" }],
    { mysql: "mysql-auth-v1" },
  ));
  assert.throws(
    () => managerApi.assertPersistentAuthCompatibility(
      [canonicalContainer({
        service: "minio",
        source: "kokoro-infra_kokoro-minio",
        authMarker: "",
      })],
      { minio: "minio-auth-v1" },
    ),
    /infra_persistent_auth_marker_missing: minio/u,
  );
});

test("existing MySQL and PostgreSQL credentials are probed via stdin without secret argv", async () => {
  const values = {
    MYSQL_ROOT_PASSWORD: "root-secret",
    MYSQL_USER: "kokoro",
    MYSQL_PASSWORD: "app-secret",
    MYSQL_DATABASE: "kokoro",
    POSTGRES_USER: "platform_admin",
    POSTGRES_PASSWORD: "pg-secret",
    POSTGRES_DB: "postgres",
  };
  const calls = [];
  const runDocker = (args, options) => {
    calls.push({ args, options });
    return { status: 0, stdout: "", stderr: "" };
  };
  await managerApi.probePersistentCredentials(
    await plan("ensure", ["platform", "postgres-transition"]),
    [
      canonicalContainer({ service: "mysql", source: "kokoro-infra_kokoro-mysql", authMarker: "" }),
      canonicalContainer({ service: "postgres", source: "kokoro-infra_kokoro-postgres", authMarker: "" }),
    ],
    values,
    runDocker,
  );
  assert.deepEqual(calls.map(({ options }) => options.input), ["root-secret\n", "app-secret\n", "pg-secret\n"]);
  assert.doesNotMatch(JSON.stringify(calls.map(({ args }) => args)), /root-secret|app-secret|pg-secret/u);
  assert.ok(calls.every(({ args }) => args.slice(0, 3).join(" ").startsWith("exec -i container-")));

  assert.throws(
    () => managerApi.probePersistentCredentials(
      { services: ["postgres"] },
      [canonicalContainer({ service: "postgres", source: "kokoro-infra_kokoro-postgres", authMarker: "" })],
      values,
      () => ({ status: 1, stdout: "", stderr: "authentication failed" }),
    ),
    /infra_persistent_auth_probe_failed: postgres/u,
  );
});

test("destructive Docker cleanup and implicit orphan removal are rejected", () => {
  for (const argv of [
    ["compose", "down", "--volumes"],
    ["compose", "--project-name", "kokoro-infra", "down"],
    ["system", "prune", "--force"],
    ["volume", "rm", "kokoro-infra_kokoro-mysql"],
    ["image", "rm", "sha256:deadbeef"],
    ["compose", "up", "--remove-orphans"],
  ]) {
    assert.throws(
      () => managerApi.assertSafeDockerArguments(argv),
      /infra_destructive_operation_forbidden/u,
    );
  }
  assert.doesNotThrow(() => managerApi.assertSafeDockerArguments([
    "compose", "up", "-d", "--wait", "postgres",
  ]));
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

test("the additive PostgreSQL candidate converges under the same canonical authority", async () => {
  const input = await plan("ensure", ["postgres-transition"], "dev");
  assert.deepEqual(input.services, ["postgres"]);
  assert.doesNotThrow(() => managerApi.assertCanonicalPostcondition(input, [
    canonicalContainer({
      service: "postgres",
      source: "kokoro-infra_kokoro-postgres",
      authMarker: "postgres-auth-v1",
    }),
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
  assert.equal((compose.match(/io\.kokoro\.infra\.scope:/gu) ?? []).length, 6);
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
  for (const profile of ["platform", "runtime", "storage", "model", "postgres-transition"]) {
    assert.match(compose, new RegExp(`profiles:\\s*\\[[^\\]]*${profile}[^\\]]*\\]`, "u"));
  }
  for (const volume of ["mysql", "postgres", "redis", "mongo", "minio"]) {
    assert.match(
      compose,
      new RegExp(`name:\\s+"?\\$\\{KOKORO_INFRA_SCOPE:-kokoro-infra_kokoro\\}-${volume}"?`, "u"),
    );
  }
  for (const image of ["mysql", "postgres", "redis", "mongo", "minio/minio", "ghcr.io/berriai/litellm"]) {
    assert.match(compose, new RegExp(`image:\\s+${image.replaceAll("/", "\\/")}:[^\\s@]+@sha256:[0-9a-f]{64}`, "u"));
  }
  const postgres = compose.split("  postgres:", 2)[1]?.split("\n  redis:", 1)[0] ?? "";
  assert.match(postgres, /image:\s+postgres:18\.4@sha256:[0-9a-f]{64}/u);
  assert.match(postgres, /127\.0\.0\.1:\$\{KOKORO_POSTGRES_PORT:-5433\}:5432/u);
  assert.match(postgres, /pg_isready/u);
  assert.match(postgres, /postgres-data:\/var\/lib\/postgresql/u);
});

test("infrastructure policy derives volume identity from the canonical resource prefix", async () => {
  const policy = JSON.parse(await readFile(
    resolve(root, "config/repository/infrastructure-policy.yaml"),
    "utf8",
  ));
  assert.equal(policy.authority.volumeNameTemplate, "{resourcePrefix}-{service}");
  assert.deepEqual(policy.profiles.platform, ["mysql"]);
  assert.deepEqual(policy.profiles.full, ["mysql", "redis", "mongo", "minio", "litellm"]);
  assert.deepEqual(policy.profiles["postgres-transition"], ["postgres"]);
  assert.equal(policy.databaseTransition.phase, "additive-2a");
  assert.equal(policy.databaseTransition.canonicalService, "mysql");
  assert.equal(policy.databaseTransition.candidateService, "postgres");
  assert.equal(policy.databaseTransition.activationAuthorized, false);
  assert.deepEqual(policy.databaseTransition.preservedServices, ["redis", "mongo", "minio", "litellm"]);
});

test("root owns the example LiteLLM configuration", async () => {
  const config = await readFile(resolve(root, "config/infra/litellm.config.example.yaml"), "utf8");
  assert.match(config, /model_name:\s+kokoro-openai-gpt-4o-mini/u);
  assert.match(config, /master_key:\s+os\.environ\/LITELLM_MASTER_KEY/u);
  assert.doesNotMatch(config, /(?:sk-|api[_-]?key:\s+["']?[A-Za-z0-9]{16})/iu);
});
