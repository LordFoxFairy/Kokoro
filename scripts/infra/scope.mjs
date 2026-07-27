import { createHash, randomBytes } from "node:crypto";
import { spawnSync } from "node:child_process";
import { mkdir, open, readFile, readdir, rm } from "node:fs/promises";
import { resolve } from "node:path";

const MYSQL_CONTEXTS = ["site", "user", "model", "credit", "payment", "admin"];
const RUN_ID_PATTERN = /^run_[a-z0-9][a-z0-9_-]{2,31}$/u;
const ENDPOINT_PATTERN = /^[a-z0-9][a-z0-9._-]{1,63}$/u;
const REDIS_DATABASES = [8, 9, 10, 11, 12, 13, 14, 15];
const LOCK_FILE = ".lease.lock";

function scopeError(code, detail = "") {
  const error = new Error(`${code}${detail ? `: ${detail}` : ""}`);
  error.code = code;
  return error;
}

function validateIdentity({ runId, endpointFingerprint }) {
  if (!RUN_ID_PATTERN.test(runId)) throw scopeError("infra_scope_id_invalid", runId);
  if (!ENDPOINT_PATTERN.test(endpointFingerprint)) {
    throw scopeError("infra_scope_endpoint_invalid");
  }
}

function leasePath(stateRoot, runId) {
  return resolve(stateRoot, `${runId}.json`);
}

function sqlIdentifier(value) {
  if (!/^[a-z0-9_]+$/u.test(value)) throw scopeError("infra_scope_identifier_invalid");
  return `\`${value}\``;
}

function sqlString(value) {
  if (!/^[a-zA-Z0-9_-]+$/u.test(value)) throw scopeError("infra_scope_credential_invalid");
  return `'${value}'`;
}

function createLease({ runId, endpointFingerprint, redisDatabase }) {
  const databaseStem = `kokoro_test_${runId}`.replaceAll("-", "_");
  const bucketRun = runId.replaceAll("_", "-");
  return {
    schemaVersion: 1,
    runId,
    endpointFingerprint,
    leaseToken: randomBytes(32).toString("hex"),
    createdAt: new Date().toISOString(),
    mysql: Object.fromEntries(
      MYSQL_CONTEXTS.map((context) => [context, `${databaseStem}_${context}`]),
    ),
    mysqlUsers: Object.fromEntries(
      MYSQL_CONTEXTS.map((context) => {
        const suffix = createHash("sha256").update(`${runId}:${context}`).digest("hex").slice(0, 12);
        return [context, {
          username: `kt_${context.slice(0, 5)}_${suffix}`,
          password: randomBytes(24).toString("base64url"),
        }];
      }),
    ),
    mongo: { database: databaseStem },
    redis: {
      database: redisDatabase,
      keyPrefix: `${databaseStem}:`,
      markerKey: `${databaseStem}:__lease`,
      exclusive: true,
    },
    minio: {
      alias: "kokoro-infra",
      bucket: `kokoro-test-${bucketRun}-runtime`,
      prefix: `${runId}/`,
    },
  };
}

async function withLeaseLock(stateRoot, operation) {
  await mkdir(stateRoot, { recursive: true });
  let handle;
  for (let attempt = 0; attempt < 50; attempt += 1) {
    try {
      handle = await open(resolve(stateRoot, LOCK_FILE), "wx", 0o600);
      break;
    } catch (error) {
      if (error.code !== "EEXIST") throw error;
      await new Promise((done) => setTimeout(done, 10));
    }
  }
  if (!handle) throw scopeError("infra_scope_lock_busy");
  try {
    return await operation();
  } finally {
    await handle.close();
    await rm(resolve(stateRoot, LOCK_FILE), { force: true });
  }
}

async function activeLeases(stateRoot) {
  const entries = await readdir(stateRoot, { withFileTypes: true });
  const leases = [];
  for (const entry of entries) {
    if (!entry.isFile() || !entry.name.endsWith(".json")) continue;
    leases.push(JSON.parse(await readFile(resolve(stateRoot, entry.name), "utf8")));
  }
  return leases;
}

export async function acquireScope({ stateRoot, runId, endpointFingerprint }) {
  validateIdentity({ runId, endpointFingerprint });
  return withLeaseLock(stateRoot, async () => {
    try {
      await readFile(leasePath(stateRoot, runId));
      throw scopeError("infra_scope_busy");
    } catch (error) {
      if (error.code !== "ENOENT") throw error;
    }
    const used = new Set((await activeLeases(stateRoot)).map((lease) => lease.redis?.database));
    const redisDatabase = REDIS_DATABASES.find((database) => !used.has(database));
    if (redisDatabase === undefined) throw scopeError("infra_scope_redis_exhausted");
    const lease = createLease({ runId, endpointFingerprint, redisDatabase });
    const handle = await open(leasePath(stateRoot, runId), "wx", 0o600);
    try {
      await handle.writeFile(`${JSON.stringify(lease, null, 2)}\n`, "utf8");
    } finally {
      await handle.close();
    }
    return lease;
  });
}

export async function readScope({ stateRoot, runId }) {
  if (!RUN_ID_PATTERN.test(runId ?? "")) throw scopeError("infra_scope_id_invalid");
  try {
    return JSON.parse(await readFile(leasePath(stateRoot, runId), "utf8"));
  } catch (error) {
    if (error.code === "ENOENT") throw scopeError("infra_scope_missing");
    throw error;
  }
}

export function assertCleanupTarget({ lease, kind, name, endpointFingerprint }) {
  if (endpointFingerprint !== lease.endpointFingerprint) {
    throw scopeError("infra_cleanup_endpoint_mismatch");
  }
  const allowed = new Set([
    ...Object.values(lease.mysql),
    lease.mongo.database,
    lease.minio.bucket,
    lease.minio.prefix,
    `redis-db-${lease.redis.database}`,
    lease.redis.keyPrefix,
  ]);
  const prefixValid = kind === "minio"
    ? name.startsWith("kokoro-test-") || name.startsWith("run_")
    : kind === "redis"
      ? name.startsWith("redis-db-") || name.startsWith("kokoro_test_")
      : name.startsWith("kokoro_test_");
  if (!allowed.has(name) || !prefixValid) {
    throw scopeError("infra_cleanup_target_invalid", `${kind}:${name}`);
  }
  return true;
}

function defaultRun(command, args, options = {}) {
  return spawnSync(command, args, {
    encoding: "utf8",
    shell: false,
    input: options.input ?? "",
    maxBuffer: 1024 * 1024,
  });
}

function checkedRun(run, command, args, options = {}) {
  const result = run(command, args, options);
  if (result.error || result.status !== 0) {
    throw scopeError("infra_scope_command_failed", `${command} exit ${result.status ?? "error"}`);
  }
  return result;
}

function mysqlSql(lease, action) {
  const statements = [];
  for (const context of MYSQL_CONTEXTS) {
    const database = sqlIdentifier(lease.mysql[context]);
    const user = sqlString(lease.mysqlUsers[context].username);
    const password = sqlString(lease.mysqlUsers[context].password);
    if (action === "create") {
      statements.push(
        `CREATE DATABASE IF NOT EXISTS ${database};`,
        `CREATE USER IF NOT EXISTS ${user}@'%' IDENTIFIED BY ${password};`,
        `GRANT ALL PRIVILEGES ON ${database}.* TO ${user}@'%';`,
      );
    } else {
      statements.push(`DROP DATABASE IF EXISTS ${database};`, `DROP USER IF EXISTS ${user}@'%';`);
    }
  }
  return `${statements.join("\n")}\n`;
}

const composeExec = (service, command) => [
  "compose", "--project-name", "kokoro-infra", "-f", "docker-compose.infra.yml",
  "exec", "-T", service, ...command,
];

export async function provisionScope({ lease, run = defaultRun }) {
  validateIdentity(lease);
  checkedRun(run, "docker", composeExec("mysql", [
    "sh", "-c", 'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql --protocol=socket -uroot',
  ]), { input: mysqlSql(lease, "create") });

  const mongoScript = `db.getSiblingDB(${JSON.stringify(lease.mongo.database)})` +
    `.getCollection("__kokoro_scope").updateOne({_id:"lease"},{$set:{active:true}},{upsert:true});\n`;
  checkedRun(run, "docker", composeExec("mongo", ["mongosh", "--quiet"]), { input: mongoScript });

  const redisResult = checkedRun(run, "docker", composeExec("redis", [
    "redis-cli", "-n", String(lease.redis.database), "-x", "SET", lease.redis.markerKey, "NX",
  ]), { input: lease.leaseToken });
  if (redisResult.stdout.trim() !== "OK") throw scopeError("infra_scope_redis_busy");

  const target = `${lease.minio.alias}/${lease.minio.bucket}`;
  checkedRun(run, "mc", ["mb", "--ignore-existing", target]);
  checkedRun(run, "mc", ["pipe", `${target}/${lease.minio.prefix}__scope`], { input: "scope\n" });
}

export async function releaseScope({ stateRoot, runId, leaseToken, endpointFingerprint }) {
  const lease = await readScope({ stateRoot, runId });
  if (lease.runId !== runId) throw scopeError("infra_scope_id_mismatch");
  if (lease.leaseToken !== leaseToken) throw scopeError("infra_scope_token_mismatch");
  if (lease.endpointFingerprint !== endpointFingerprint) {
    throw scopeError("infra_scope_endpoint_mismatch");
  }
  await rm(leasePath(stateRoot, runId));
}

export async function cleanupScope({
  stateRoot,
  runId,
  leaseToken,
  endpointFingerprint,
  run = defaultRun,
}) {
  const lease = await readScope({ stateRoot, runId });
  if (lease.leaseToken !== leaseToken) throw scopeError("infra_scope_token_mismatch");
  if (lease.endpointFingerprint !== endpointFingerprint) {
    throw scopeError("infra_scope_endpoint_mismatch");
  }
  for (const name of Object.values(lease.mysql)) {
    assertCleanupTarget({ lease, kind: "mysql", name, endpointFingerprint });
  }
  assertCleanupTarget({ lease, kind: "mongo", name: lease.mongo.database, endpointFingerprint });
  assertCleanupTarget({ lease, kind: "redis", name: `redis-db-${lease.redis.database}`, endpointFingerprint });
  assertCleanupTarget({ lease, kind: "redis", name: lease.redis.keyPrefix, endpointFingerprint });
  assertCleanupTarget({ lease, kind: "minio", name: lease.minio.bucket, endpointFingerprint });
  assertCleanupTarget({ lease, kind: "minio", name: lease.minio.prefix, endpointFingerprint });

  const marker = checkedRun(run, "docker", composeExec("redis", [
    "redis-cli", "--raw", "-n", String(lease.redis.database), "GET", lease.redis.markerKey,
  ])).stdout.trim();
  if (marker !== leaseToken) throw scopeError("infra_scope_redis_token_mismatch");

  checkedRun(run, "docker", composeExec("mysql", [
    "sh", "-c", 'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql --protocol=socket -uroot',
  ]), { input: mysqlSql(lease, "drop") });
  const mongoScript = `db.getSiblingDB(${JSON.stringify(lease.mongo.database)}).dropDatabase();\n`;
  checkedRun(run, "docker", composeExec("mongo", ["mongosh", "--quiet"]), { input: mongoScript });
  const guardedFlushScript = [
    'if redis.call("GET", KEYS[1]) ~= ARGV[1] then return 0 end',
    'redis.call("FLUSHDB")',
    "return 1",
  ].join(" ");
  const flushResult = checkedRun(run, "docker", composeExec("redis", [
    "redis-cli", "--raw", "-n", String(lease.redis.database), "-x",
    "EVAL", guardedFlushScript, "1", lease.redis.markerKey,
  ]), { input: leaseToken });
  if (flushResult.stdout.trim() !== "1") throw scopeError("infra_scope_redis_token_mismatch");

  const target = `${lease.minio.alias}/${lease.minio.bucket}/${lease.minio.prefix}`;
  checkedRun(run, "mc", ["rm", "--incomplete", "--recursive", "--force", target]);
  checkedRun(run, "mc", ["rm", "--recursive", "--force", target]);
  checkedRun(run, "mc", ["rb", "--force", `${lease.minio.alias}/${lease.minio.bucket}`]);
  await releaseScope({ stateRoot, runId, leaseToken, endpointFingerprint });
}
