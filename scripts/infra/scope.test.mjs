import assert from "node:assert/strict";
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { resolve } from "node:path";
import test from "node:test";

const scopeModule = new URL("./scope.mjs", import.meta.url);

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
    await assert.rejects(
      provisionScope({ lease, mysqlRootPassword: "", run }),
      /infra_scope_mysql_admin_credential_missing/u,
    );
    await assert.rejects(
      provisionScope({ lease, mysqlRootPassword: "unsafe\ncredential", run }),
      /infra_scope_mysql_admin_credential_invalid/u,
    );
    await assert.rejects(
      cleanupScope({
        stateRoot,
        runId: lease.runId,
        leaseToken: lease.leaseToken,
        endpointFingerprint: lease.endpointFingerprint,
        mysqlRootPassword: "",
        run,
      }),
      /infra_scope_mysql_admin_credential_missing/u,
    );
    assert.equal(commandCount, 0);
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

    assert.ok(calls.some(({ input }) => /DROP DATABASE/u.test(input)));
    assert.ok(calls.some(({ input }) => /dropDatabase/u.test(input)));
    assert.equal(calls.some(({ args }) => args.includes("FLUSHDB")), false);
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
      resources: ["redis"],
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
        run,
      }),
      /infra_scope_redis_unowned_data/u,
    );

    assert.equal((await readScope({ stateRoot, runId: lease.runId })).leaseToken, lease.leaseToken);
    assert.equal(calls.some(({ args }) => args.includes("FLUSHDB")), false);
  } finally {
    await rm(stateRoot, { recursive: true, force: true });
  }
});

test("cleanup rejects a mismatched Redis marker without inspecting or deleting database contents", async () => {
  const { acquireScope, cleanupScope, readScope } = await import(scopeModule);
  const stateRoot = await mkdtemp(resolve(tmpdir(), "kokoro-infra-scope-"));
  const calls = [];
  try {
    const lease = await acquireScope({
      stateRoot,
      runId: "run_wrongmark",
      endpointFingerprint: "local-dev",
      resources: ["redis"],
    });
    const run = (command, args, options = {}) => {
      calls.push({ command, args, input: options.input ?? "" });
      if (args.includes("GET")) return { status: 0, stdout: `${"f".repeat(64)}\n`, stderr: "" };
      return { status: 0, stdout: "0\n", stderr: "" };
    };
    await assert.rejects(
      cleanupScope({
        stateRoot,
        runId: lease.runId,
        leaseToken: lease.leaseToken,
        endpointFingerprint: lease.endpointFingerprint,
        run,
      }),
      /infra_scope_redis_token_mismatch/u,
    );

    assert.equal((await readScope({ stateRoot, runId: lease.runId })).leaseToken, lease.leaseToken);
    assert.equal(calls.some(({ args }) => args.includes("DBSIZE") || args.includes("EVAL")), false);
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
