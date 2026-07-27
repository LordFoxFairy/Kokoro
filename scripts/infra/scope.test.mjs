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
  const calls = [];
  const run = (command, args, options = {}) => {
    calls.push({ command, args, input: options.input ?? "" });
    if (args.includes("GET")) return { status: 0, stdout: `${options.expectedToken ?? ""}\n`, stderr: "" };
    if (args.includes("EVAL")) return { status: 0, stdout: "1\n", stderr: "" };
    return { status: 0, stdout: "OK\n", stderr: "" };
  };
  try {
    const lease = await acquireScope({ stateRoot, runId: "run_real01", endpointFingerprint: "local-dev" });
    await provisionScope({ lease, run });
    assert.equal(calls.filter(({ input }) => /CREATE DATABASE/u.test(input)).length, 1);
    assert.match(calls.find(({ input }) => /CREATE DATABASE/u.test(input)).input, /CREATE USER[\s\S]*GRANT ALL PRIVILEGES ON `kokoro_test_run_real01_site`\.\*/u);
    assert.equal(calls.filter(({ input }) => /getSiblingDB/u.test(input)).length, 1);
    assert.ok(calls.some(({ args, input }) =>
      args.includes("EVAL") && args.includes(lease.redis.markerKey) && input === lease.leaseToken));
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
      run: cleanupRun,
    });
    assert.ok(calls.slice(markerRead).some(({ input }) => /DROP DATABASE/u.test(input)));
    assert.ok(calls.slice(markerRead).some(({ args, input }) =>
      args.includes("EVAL") && /FLUSHDB/u.test(args.join(" ")) && input === lease.leaseToken));
    assert.ok(calls.slice(markerRead).every(({ args }) => args[args.length - 1] !== lease.leaseToken));
    assert.ok(calls.slice(markerRead).some(({ command, args }) => command === "mc" && args[0] === "rm"));
    assert.ok(calls.slice(markerRead).some(({ command, args }) => command === "mc" && args.includes("--incomplete")));
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
