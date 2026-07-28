import assert from "node:assert/strict";
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { resolve } from "node:path";
import test from "node:test";

const scopeModule = new URL("./scope.mjs", import.meta.url);

function isRedisFlushCall({ args }) {
  const evalIndex = args.indexOf("EVAL");
  return evalIndex >= 0 && args[evalIndex + 1]?.includes('redis.call("FLUSHDB")');
}

function evaluateRedisClaim(script, database, markerKey, token) {
  const normalized = script.replace(/\s+/gu, " ").trim();
  assert.equal(normalized, [
    'if redis.call("DBSIZE") ~= 0 then return 0 end',
    'redis.call("SET", KEYS[1], ARGV[1])',
    "return 1",
  ].join(" "));
  if (database.size !== 0) return 0;
  database.set(markerKey, token);
  return 1;
}

test("leases concurrent run-scoped allocations with exclusive Redis databases", async () => {
  const { acquireScope, releaseScope } = await import(scopeModule);
  const stateRoot = await mkdtemp(resolve(tmpdir(), "kokoro-infra-scope-"));
  try {
    const lease = await acquireScope({
      stateRoot,
      runId: "run_a1b2c3",
      endpointFingerprint: "local-dev",
    });
    assert.deepEqual(Object.keys(lease.mysql).sort(), [
      "admin",
      "credit",
      "model",
      "payment",
      "site",
      "user",
    ]);
    for (const name of Object.values(lease.mysql)) {
      assert.match(name, /^kokoro_test_run_a1b2c3_(?:site|user|model|credit|payment|admin)$/u);
    }
    assert.equal(lease.mongo.database, "kokoro_test_run_a1b2c3");
    assert.deepEqual(Object.keys(lease.mysqlUsers).sort(), [
      "admin", "credit", "model", "payment", "site", "user",
    ]);
    assert.match(lease.minio.bucket, /^kokoro-test-run-a1b2c3-runtime$/u);
    assert.ok(lease.redis.database >= 8 && lease.redis.database <= 15);
    assert.match(lease.leaseToken, /^[0-9a-f]{64}$/u);

    const second = await acquireScope({
      stateRoot,
      runId: "run_second",
      endpointFingerprint: "local-dev",
    });
    assert.notEqual(second.redis.database, lease.redis.database);
    await releaseScope({
      stateRoot,
      runId: lease.runId,
      leaseToken: lease.leaseToken,
      endpointFingerprint: lease.endpointFingerprint,
    });
    await releaseScope({
      stateRoot,
      runId: second.runId,
      leaseToken: second.leaseToken,
      endpointFingerprint: second.endpointFingerprint,
    });
  } finally {
    await rm(stateRoot, { recursive: true, force: true });
  }
});

test("provisions and cleans databases, Redis marker, and MinIO prefix through bounded commands", async () => {
  const { acquireScope, cleanupScope, provisionScope } = await import(scopeModule);
  const stateRoot = await mkdtemp(resolve(tmpdir(), "kokoro-infra-scope-"));
  const mysqlRootPassword = "scope-root-secret";
  const calls = [];
  const run = (command, args, options = {}) => {
    calls.push({ command, args, input: options.input ?? "" });
    if (args.includes("GET")) return { status: 0, stdout: `${options.expectedToken ?? ""}\n`, stderr: "" };
    if (args.includes("EVAL")) return { status: 0, stdout: "1\n", stderr: "" };
    return { status: 0, stdout: "OK\n", stderr: "" };
  };
  try {
    const lease = await acquireScope({ stateRoot, runId: "run_real01", endpointFingerprint: "local-dev" });
    await provisionScope({ lease, mysqlRootPassword, run });
    const mysqlProvision = calls.find(({ input }) => /CREATE DATABASE/u.test(input));
    assert.equal(calls.filter(({ input }) => /CREATE DATABASE/u.test(input)).length, 1);
    assert.match(mysqlProvision.input, new RegExp(`^${mysqlRootPassword}\\n`, "u"));
    assert.match(mysqlProvision.input, /CREATE USER[\s\S]*GRANT ALL PRIVILEGES ON `kokoro_test_run_real01_site`\.\*/u);
    assert.doesNotMatch(JSON.stringify(mysqlProvision.args), new RegExp(mysqlRootPassword, "u"));
    assert.doesNotMatch(JSON.stringify(mysqlProvision.args), /MYSQL_ROOT_PASSWORD/u);
    assert.equal(calls.filter(({ input }) => /getSiblingDB/u.test(input)).length, 1);
    assert.ok(calls.some(({ args, input }) =>
      args.includes("EVAL") && args.includes(lease.redis.markerKey) &&
      args.some((argument) => argument.includes("DBSIZE")) && input === lease.leaseToken));
    assert.ok(
      calls.findIndex(({ args }) => args.includes("EVAL")) <
      calls.findIndex(({ input }) => /CREATE DATABASE/u.test(input)),
    );
    assert.ok(calls.some(({ command, args }) => command === "mc" && args[0] === "mb"));
    assert.ok(calls.every(({ args }) => !args.includes(lease.leaseToken)));

    const markerRead = calls.length;
    const cleanupRun = (command, args, options = {}) => {
      calls.push({ command, args, input: options.input ?? "" });
      if (args.includes("GET")) return { status: 0, stdout: `${lease.leaseToken}\n`, stderr: "" };
      if (args.includes("EVAL")) return { status: 0, stdout: "1\n", stderr: "" };
      return { status: 0, stdout: "OK\n", stderr: "" };
    };
    await cleanupScope({
      stateRoot,
      runId: lease.runId,
      leaseToken: lease.leaseToken,
      endpointFingerprint: lease.endpointFingerprint,
      mysqlRootPassword,
      run: cleanupRun,
    });
    const mysqlCleanup = calls.slice(markerRead).find(({ input }) => /DROP DATABASE/u.test(input));
    assert.ok(mysqlCleanup);
    assert.match(mysqlCleanup.input, new RegExp(`^${mysqlRootPassword}\\n`, "u"));
    assert.doesNotMatch(JSON.stringify(mysqlCleanup.args), new RegExp(mysqlRootPassword, "u"));
    assert.doesNotMatch(JSON.stringify(mysqlCleanup.args), /MYSQL_ROOT_PASSWORD/u);
    assert.ok(calls.slice(markerRead).some(({ args, input }) =>
      args.includes("EVAL") && /FLUSHDB/u.test(args.join(" ")) && input === lease.leaseToken));
    assert.ok(calls.slice(markerRead).every(({ args }) => args[args.length - 1] !== lease.leaseToken));
    assert.ok(calls.slice(markerRead).some(({ command, args }) => command === "mc" && args[0] === "rm"));
    assert.ok(calls.slice(markerRead).some(({ command, args }) => command === "mc" && args.includes("--incomplete")));
  } finally {
    await rm(stateRoot, { recursive: true, force: true });
  }
});

test("MySQL scope operations fail closed before commands with a missing or unsafe host admin credential", async () => {
  const { acquireScope, cleanupScope, provisionScope } = await import(scopeModule);
  const stateRoot = await mkdtemp(resolve(tmpdir(), "kokoro-infra-scope-"));
  let commandCount = 0;
  const run = () => {
    commandCount += 1;
    return { status: 0, stdout: "OK\n", stderr: "" };
  };
  try {
    const lease = await acquireScope({
      stateRoot,
      runId: "run_nocred",
      endpointFingerprint: "local-dev",
      resources: ["mysql"],
    });
    for (const { password, error } of [
      { password: "", error: /infra_scope_mysql_admin_credential_missing/u },
      { password: "unsafe\rcredential", error: /infra_scope_mysql_admin_credential_invalid/u },
      { password: "unsafe\ncredential", error: /infra_scope_mysql_admin_credential_invalid/u },
      { password: "unsafe\0credential", error: /infra_scope_mysql_admin_credential_invalid/u },
    ]) {
      await assert.rejects(provisionScope({ lease, mysqlRootPassword: password, run }), error);
      await assert.rejects(
        cleanupScope({
          stateRoot,
          runId: lease.runId,
          leaseToken: lease.leaseToken,
          endpointFingerprint: lease.endpointFingerprint,
          mysqlRootPassword: password,
          run,
        }),
        error,
      );
    }
    assert.equal(commandCount, 0);
  } finally {
    await rm(stateRoot, { recursive: true, force: true });
  }
});

test("default scope commands use process-environment credentials without inheriting secrets", async () => {
  const { acquireScope, cleanupScope, provisionScope } = await import(scopeModule);
  const stateRoot = await mkdtemp(resolve(tmpdir(), "kokoro-infra-scope-"));
  const mysqlRootPassword = "process-environment-secret";
  const environment = {
    PATH: "/test/bin",
    HOME: "/test/home",
    LANG: "C",
    DOCKER_HOST: "unix:///test/docker.sock",
    DOCKER_CONTEXT: "scope-context",
    DOCKER_CONFIG: "/test/docker-config",
    COMPOSE_PROGRESS: "plain",
    MC_CONFIG_DIR: "/test/mc",
    MYSQL_ROOT_PASSWORD: mysqlRootPassword,
    OTHER_API_TOKEN: "other-sensitive-value",
  };
  const calls = [];
  const spawn = (command, args, options) => {
    calls.push({ command, args, options });
    return { status: 0, stdout: "OK\n", stderr: "" };
  };
  try {
    const lease = await acquireScope({
      stateRoot,
      runId: "run_envpath",
      endpointFingerprint: "local-dev",
      resources: ["mysql", "minio"],
    });
    await provisionScope({ lease, environment, spawn });
    await cleanupScope({
      stateRoot,
      runId: lease.runId,
      leaseToken: lease.leaseToken,
      endpointFingerprint: lease.endpointFingerprint,
      environment,
      spawn,
    });

    assert.deepEqual(calls.map(({ command }) => command), [
      "docker", "mc", "mc", "docker", "mc", "mc", "mc",
    ]);
    for (const { args, options } of calls) {
      assert.equal(options.env.PATH, environment.PATH);
      assert.equal(options.env.HOME, environment.HOME);
      assert.equal(options.env.DOCKER_HOST, environment.DOCKER_HOST);
      assert.equal(options.env.DOCKER_CONTEXT, environment.DOCKER_CONTEXT);
      assert.equal(options.env.DOCKER_CONFIG, environment.DOCKER_CONFIG);
      assert.equal(options.env.COMPOSE_PROGRESS, environment.COMPOSE_PROGRESS);
      assert.equal(options.env.MC_CONFIG_DIR, environment.MC_CONFIG_DIR);
      assert.equal("MYSQL_ROOT_PASSWORD" in options.env, false);
      assert.equal("OTHER_API_TOKEN" in options.env, false);
      assert.equal(JSON.stringify(args).includes(mysqlRootPassword), false);
    }
    const mysqlCalls = calls.filter(({ command }) => command === "docker");
    assert.equal(mysqlCalls.length, 2);
    assert.ok(mysqlCalls.every(({ options }) => options.input.startsWith(`${mysqlRootPassword}\n`)));
    assert.equal(calls.filter(({ command }) => command === "mc")
      .some(({ options }) => options.input.includes(mysqlRootPassword)), false);
  } finally {
    await rm(stateRoot, { recursive: true, force: true });
  }
});

test("omitting environment reads the MySQL credential from process.env without child inheritance", async () => {
  const { acquireScope, provisionScope } = await import(scopeModule);
  const stateRoot = await mkdtemp(resolve(tmpdir(), "kokoro-infra-scope-"));
  const mysqlRootPassword = "temporary-process-env-secret";
  const previousMysqlRootPassword = process.env.MYSQL_ROOT_PASSWORD;
  const calls = [];
  const spawn = (command, args, options) => {
    calls.push({ command, args, options });
    return { status: 0, stdout: "OK\n", stderr: "" };
  };
  process.env.MYSQL_ROOT_PASSWORD = mysqlRootPassword;
  try {
    const lease = await acquireScope({
      stateRoot,
      runId: "run_realenv",
      endpointFingerprint: "local-dev",
      resources: ["mysql"],
    });
    await provisionScope({ lease, spawn });

    assert.equal(calls.length, 1);
    assert.equal(calls[0].command, "docker");
    assert.match(calls[0].options.input, new RegExp(`^${mysqlRootPassword}\\n`, "u"));
    assert.equal(JSON.stringify(calls[0].args).includes(mysqlRootPassword), false);
    assert.equal("MYSQL_ROOT_PASSWORD" in calls[0].options.env, false);
    assert.equal(JSON.stringify(calls[0].options.env).includes(mysqlRootPassword), false);
  } finally {
    if (previousMysqlRootPassword === undefined) delete process.env.MYSQL_ROOT_PASSWORD;
    else process.env.MYSQL_ROOT_PASSWORD = previousMysqlRootPassword;
    await rm(stateRoot, { recursive: true, force: true });
  }
});

test("scope command failures do not expose credentials from child errors or output", async () => {
  const { acquireScope, provisionScope } = await import(scopeModule);
  const stateRoot = await mkdtemp(resolve(tmpdir(), "kokoro-infra-scope-"));
  const mysqlRootPassword = "failure-path-secret";
  const calls = [];
  const spawn = (command, args, options) => {
    calls.push({ command, args, options });
    return {
      error: new Error(mysqlRootPassword),
      status: null,
      stdout: `${mysqlRootPassword}\n`,
      stderr: `${mysqlRootPassword}\n`,
    };
  };
  try {
    const lease = await acquireScope({
      stateRoot,
      runId: "run_errsafe",
      endpointFingerprint: "local-dev",
      resources: ["mysql"],
    });
    const error = await provisionScope({
      lease,
      environment: { PATH: "/test/bin", MYSQL_ROOT_PASSWORD: mysqlRootPassword },
      spawn,
    }).then(
      () => null,
      (failure) => failure,
    );

    assert.equal(error.code, "infra_scope_command_failed");
    assert.equal(error.message.includes(mysqlRootPassword), false);
    assert.equal(JSON.stringify(calls[0].args).includes(mysqlRootPassword), false);
    assert.equal(JSON.stringify(calls[0].options.env).includes(mysqlRootPassword), false);
    assert.match(calls[0].options.input, new RegExp(`^${mysqlRootPassword}\\n`, "u"));
  } finally {
    await rm(stateRoot, { recursive: true, force: true });
  }
});

test("Redis refuses to claim a nonempty database before provisioning MySQL or Mongo", async () => {
  const { acquireScope, provisionScope } = await import(scopeModule);
  const stateRoot = await mkdtemp(resolve(tmpdir(), "kokoro-infra-scope-"));
  const calls = [];
  try {
    const lease = await acquireScope({
      stateRoot,
      runId: "run_busydb",
      endpointFingerprint: "local-dev",
      resources: ["mysql", "mongo", "redis"],
    });
    const run = (command, args, options = {}) => {
      calls.push({ command, args, input: options.input ?? "" });
      return { status: 0, stdout: args.includes("EVAL") ? "0\n" : "OK\n", stderr: "" };
    };
    await assert.rejects(
      provisionScope({ lease, mysqlRootPassword: "scope-root-secret", run }),
      /infra_scope_redis_busy/u,
    );

    assert.equal(calls.length, 1);
    assert.ok(calls[0].args.includes("EVAL"));
    assert.ok(calls[0].args.some((argument) => argument.includes("DBSIZE")));
    assert.equal(calls.some(({ input }) => /CREATE DATABASE|getSiblingDB/u.test(input)), false);
  } finally {
    await rm(stateRoot, { recursive: true, force: true });
  }
});

test("Redis claim state controls marker ownership and all later provision mutations", async () => {
  const { acquireScope, provisionScope } = await import(scopeModule);
  const stateRoot = await mkdtemp(resolve(tmpdir(), "kokoro-infra-scope-"));
  const databases = new Map();
  const calls = [];
  const claimResults = [];
  const run = (command, args, options = {}) => {
    calls.push({ command, args, input: options.input ?? "" });
    if (!args.includes("EVAL")) return { status: 0, stdout: "OK\n", stderr: "" };
    const databaseNumber = Number(args[args.indexOf("-n") + 1]);
    const database = databases.get(databaseNumber) ?? new Map();
    databases.set(databaseNumber, database);
    const script = args[args.indexOf("EVAL") + 1];
    const result = evaluateRedisClaim(script, database, args.at(-1), options.input);
    claimResults.push(result);
    return { status: 0, stdout: `${result}\n`, stderr: "" };
  };
  try {
    const [emptyLease, usedLease, markedLease] = await Promise.all([
      "run_claimempty", "run_claimused", "run_claimmarked",
    ].map((runId) => acquireScope({
      stateRoot,
      runId,
      endpointFingerprint: "local-dev",
      resources: ["mysql", "mongo", "redis"],
    })));
    databases.set(usedLease.redis.database, new Map([["foreign:key", "foreign-value"]]));
    databases.set(markedLease.redis.database, new Map([
      [markedLease.redis.markerKey, "another-lease-token"],
    ]));

    let start = calls.length;
    await provisionScope({ lease: emptyLease, mysqlRootPassword: "scope-root-secret", run });
    const emptyCalls = calls.slice(start);
    assert.deepEqual(emptyCalls.map(({ args, input }) => {
      if (args.includes("EVAL")) return "redis:claim";
      if (/CREATE DATABASE/u.test(input)) return "mysql:create";
      if (/getSiblingDB/u.test(input)) return "mongo:create";
      return "unexpected";
    }), ["redis:claim", "mysql:create", "mongo:create"]);
    assert.equal(
      databases.get(emptyLease.redis.database).get(emptyLease.redis.markerKey),
      emptyLease.leaseToken,
    );

    start = calls.length;
    await assert.rejects(
      provisionScope({ lease: usedLease, mysqlRootPassword: "scope-root-secret", run }),
      /infra_scope_redis_busy/u,
    );
    assert.equal(calls.length - start, 1);
    assert.deepEqual([...databases.get(usedLease.redis.database)], [["foreign:key", "foreign-value"]]);
    assert.equal(databases.get(usedLease.redis.database).has(usedLease.redis.markerKey), false);

    start = calls.length;
    await assert.rejects(
      provisionScope({ lease: markedLease, mysqlRootPassword: "scope-root-secret", run }),
      /infra_scope_redis_busy/u,
    );
    assert.equal(calls.length - start, 1);
    assert.equal(
      databases.get(markedLease.redis.database).get(markedLease.redis.markerKey),
      "another-lease-token",
    );
    assert.deepEqual(claimResults, [1, 0, 0]);
  } finally {
    await rm(stateRoot, { recursive: true, force: true });
  }
});

test("cleanup recovers lease-owned resources when provision failed before the Redis marker", async () => {
  const { acquireScope, cleanupScope, readScope } = await import(scopeModule);
  const stateRoot = await mkdtemp(resolve(tmpdir(), "kokoro-infra-scope-"));
  const calls = [];
  try {
    const lease = await acquireScope({
      stateRoot,
      runId: "run_partial",
      endpointFingerprint: "local-dev",
      resources: ["mysql", "mongo", "redis"],
    });
    const run = (command, args, options = {}) => {
      calls.push({ command, args, input: options.input ?? "" });
      if (args.includes("GET")) return { status: 0, stdout: "\n", stderr: "" };
      if (args.includes("DBSIZE")) return { status: 0, stdout: "0\n", stderr: "" };
      return { status: 0, stdout: "OK\n", stderr: "" };
    };
    await cleanupScope({
      stateRoot,
      runId: lease.runId,
      leaseToken: lease.leaseToken,
      endpointFingerprint: lease.endpointFingerprint,
      mysqlRootPassword: "scope-root-secret",
      run,
    });

    assert.deepEqual(calls.map(({ args, input }) => {
      if (args.includes("GET")) return "redis:get-marker";
      if (args.includes("DBSIZE")) return "redis:database-size";
      if (/DROP DATABASE/u.test(input)) return "mysql:drop";
      if (/dropDatabase/u.test(input)) return "mongo:drop";
      return "unexpected";
    }), ["redis:get-marker", "redis:database-size", "mysql:drop", "mongo:drop"]);
    assert.equal(calls.some(isRedisFlushCall), false);
    await assert.rejects(readScope({ stateRoot, runId: lease.runId }), /infra_scope_missing/u);
  } finally {
    await rm(stateRoot, { recursive: true, force: true });
  }
});

test("cleanup preserves the lease when a markerless Redis database contains unowned data", async () => {
  const { acquireScope, cleanupScope, readScope } = await import(scopeModule);
  const stateRoot = await mkdtemp(resolve(tmpdir(), "kokoro-infra-scope-"));
  const calls = [];
  try {
    const lease = await acquireScope({
      stateRoot,
      runId: "run_stale",
      endpointFingerprint: "local-dev",
      resources: ["mysql", "mongo", "redis", "minio"],
    });
    const run = (command, args, options = {}) => {
      calls.push({ command, args, input: options.input ?? "" });
      if (args.includes("GET")) return { status: 0, stdout: "\n", stderr: "" };
      if (args.includes("DBSIZE")) return { status: 0, stdout: "2\n", stderr: "" };
      return { status: 0, stdout: "1\n", stderr: "" };
    };
    await assert.rejects(
      cleanupScope({
        stateRoot,
        runId: lease.runId,
        leaseToken: lease.leaseToken,
        endpointFingerprint: lease.endpointFingerprint,
        mysqlRootPassword: "scope-root-secret",
        run,
      }),
      /infra_scope_redis_unowned_data/u,
    );

    assert.deepEqual(calls.map(({ args }) => {
      if (args.includes("GET")) return "redis:get-marker";
      if (args.includes("DBSIZE")) return "redis:database-size";
      return "unexpected";
    }), ["redis:get-marker", "redis:database-size"]);
    assert.equal((await readScope({ stateRoot, runId: lease.runId })).leaseToken, lease.leaseToken);
    assert.equal(calls.some(isRedisFlushCall), false);
  } finally {
    await rm(stateRoot, { recursive: true, force: true });
  }
});

test("cleanup accepts only exact Redis marker bytes and preserves the lease on any mismatch", async () => {
  const { acquireScope, cleanupScope, readScope } = await import(scopeModule);
  const stateRoot = await mkdtemp(resolve(tmpdir(), "kokoro-infra-scope-"));
  const calls = [];
  try {
    const lease = await acquireScope({
      stateRoot,
      runId: "run_wrongmark",
      endpointFingerprint: "local-dev",
      resources: ["mysql", "mongo", "redis", "minio"],
    });
    for (const marker of ["f".repeat(64), `${lease.leaseToken} `, `${lease.leaseToken}\r`, " "]) {
      calls.length = 0;
      const run = (command, args, options = {}) => {
        calls.push({ command, args, input: options.input ?? "" });
        if (args.includes("GET")) return { status: 0, stdout: `${marker}\n`, stderr: "" };
        return { status: 0, stdout: "1\n", stderr: "" };
      };
      await assert.rejects(
        cleanupScope({
          stateRoot,
          runId: lease.runId,
          leaseToken: lease.leaseToken,
          endpointFingerprint: lease.endpointFingerprint,
          mysqlRootPassword: "scope-root-secret",
          run,
        }),
        /infra_scope_redis_token_mismatch/u,
      );

      assert.equal((await readScope({ stateRoot, runId: lease.runId })).leaseToken, lease.leaseToken);
      assert.equal(calls.length, 1);
      assert.ok(calls[0].args.includes("GET"));
      assert.equal(calls.some(({ args }) => args.includes("DBSIZE") || args.includes("EVAL")), false);
      assert.equal(calls.some(isRedisFlushCall), false);
    }
  } finally {
    await rm(stateRoot, { recursive: true, force: true });
  }
});

test("refuses unsafe cleanup identity, prefix or endpoint", async () => {
  const { acquireScope, assertCleanupTarget, releaseScope } = await import(scopeModule);
  const stateRoot = await mkdtemp(resolve(tmpdir(), "kokoro-infra-scope-"));
  try {
    const lease = await acquireScope({
      stateRoot,
      runId: "run_cleanup",
      endpointFingerprint: "local-dev",
    });
    assert.throws(
      () => assertCleanupTarget({ lease, kind: "mongo", name: "kokoro", endpointFingerprint: "local-dev" }),
      /infra_cleanup_target_invalid/u,
    );
    assert.throws(
      () => assertCleanupTarget({ lease, kind: "mysql", name: lease.mysql.site, endpointFingerprint: "other" }),
      /infra_cleanup_endpoint_mismatch/u,
    );
    await assert.rejects(
      releaseScope({
        stateRoot,
        runId: lease.runId,
        leaseToken: "0".repeat(64),
        endpointFingerprint: lease.endpointFingerprint,
      }),
      /infra_scope_token_mismatch/u,
    );
  } finally {
    await rm(stateRoot, { recursive: true, force: true });
  }
});

test("a selective lease provisions and cleans only its declared resources", async () => {
  const { acquireScope, cleanupScope, provisionScope } = await import(scopeModule);
  const stateRoot = await mkdtemp(resolve(tmpdir(), "kokoro-infra-scope-"));
  const calls = [];
  const run = (command, args, options = {}) => {
    calls.push({ command, args, input: options.input ?? "" });
    if (args.includes("GET")) return { status: 0, stdout: `${lease.leaseToken}\n`, stderr: "" };
    if (args.includes("EVAL")) return { status: 0, stdout: "1\n", stderr: "" };
    return { status: 0, stdout: "OK\n", stderr: "" };
  };
  let lease;
  try {
    lease = await acquireScope({
      stateRoot,
      runId: "run_runtime",
      endpointFingerprint: "local-dev",
      resources: ["redis", "mongo"],
    });
    assert.deepEqual(lease.resources, ["mongo", "redis"]);
    await provisionScope({ lease, run });
    assert.ok(calls.some(({ input }) => /getSiblingDB/u.test(input)));
    assert.ok(calls.some(({ args, input }) =>
      args.includes("EVAL") && args.includes(lease.redis.markerKey) && input === lease.leaseToken));
    assert.equal(calls.some(({ input }) => /CREATE DATABASE/u.test(input)), false);
    assert.equal(calls.some(({ command }) => command === "mc"), false);

    calls.length = 0;
    await cleanupScope({
      stateRoot,
      runId: lease.runId,
      leaseToken: lease.leaseToken,
      endpointFingerprint: lease.endpointFingerprint,
      run,
    });
    assert.ok(calls.some(({ input }) => /dropDatabase/u.test(input)));
    assert.ok(calls.some(({ args }) => args.includes("EVAL")));
    assert.equal(calls.some(({ input }) => /DROP DATABASE/u.test(input)), false);
    assert.equal(calls.some(({ command }) => command === "mc"), false);
  } finally {
    await rm(stateRoot, { recursive: true, force: true });
  }
});

test("an additive PostgreSQL lease isolates platform and session databases with bounded roles", async () => {
  const { acquireScope, cleanupScope, provisionScope } = await import(scopeModule);
  const stateRoot = await mkdtemp(resolve(tmpdir(), "kokoro-infra-scope-"));
  const calls = [];
  const run = (command, args, options = {}) => {
    calls.push({ command, args, input: options.input ?? "" });
    return { status: 0, stdout: "OK\n", stderr: "" };
  };
  try {
    const lease = await acquireScope({
      stateRoot,
      runId: "run_pgcut1",
      endpointFingerprint: "local-dev",
      resources: ["postgres"],
    });
    assert.deepEqual(lease.resources, ["postgres"]);
    assert.equal(lease.redis, null);
    assert.deepEqual(Object.keys(lease.postgres).sort(), ["platform", "session"]);
    for (const context of ["platform", "session"]) {
      assert.match(lease.postgres[context].database, new RegExp(`^kokoro_test_run_pgcut1_${context}$`, "u"));
      assert.deepEqual(Object.keys(lease.postgres[context].roles).sort(), ["migrator", "runtime", "test"]);
      for (const role of Object.values(lease.postgres[context].roles)) {
        assert.match(role.username, /^kt_pg_[a-z]+_[a-f0-9]{12}$/u);
        assert.match(role.password, /^[A-Za-z0-9_-]{24,}$/u);
      }
    }

    await provisionScope({ lease, run });
    assert.equal(calls.length, 1);
    assert.deepEqual(calls[0].args.slice(-3), [
      "sh", "-c", 'exec psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d postgres',
    ]);
    assert.doesNotMatch(JSON.stringify(calls[0].args), /-U["',\s]+postgres/u);
    assert.match(calls[0].input, /CREATE ROLE[\s\S]*CREATE DATABASE/u);
    assert.match(calls[0].input, /REVOKE CONNECT, TEMPORARY ON DATABASE[\s\S]*FROM PUBLIC/u);
    assert.match(calls[0].input, /REVOKE ALL ON SCHEMA public FROM PUBLIC/u);
    assert.match(calls[0].input, /GRANT CONNECT ON DATABASE[\s\S]*migrator/u);
    assert.match(calls[0].input, /ALTER DEFAULT PRIVILEGES[\s\S]*GRANT SELECT, INSERT, UPDATE, DELETE/u);
    assert.match(calls[0].input, /GRANT "kt_pg_platformmigrator_[a-f0-9]{12}" TO "kt_pg_platformtest_[a-f0-9]{12}"/u);
    assert.doesNotMatch(calls[0].input, /CREATE USER|mysql/u);

    calls.length = 0;
    await cleanupScope({
      stateRoot,
      runId: lease.runId,
      leaseToken: lease.leaseToken,
      endpointFingerprint: lease.endpointFingerprint,
      run,
    });
    assert.equal(calls.length, 1);
    assert.match(calls[0].input, /pg_terminate_backend[\s\S]*DROP DATABASE[\s\S]*DROP ROLE/u);
    assert.match(calls[0].args.at(-1), /\$POSTGRES_USER/u);
  } finally {
    await rm(stateRoot, { recursive: true, force: true });
  }
});
