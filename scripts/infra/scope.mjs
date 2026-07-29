import { createHash, randomBytes } from "node:crypto";
import { spawnSync } from "node:child_process";
import { mkdir, open, readFile, readdir, rm } from "node:fs/promises";
import { resolve } from "node:path";

const MYSQL_CONTEXTS = ["site", "user", "model", "credit", "payment", "admin"];
const POSTGRES_CONTEXTS = ["platform", "session"];
const POSTGRES_ROLES = Object.freeze({
  platform: Object.freeze(["api", "worker", "admin", "migrator", "test"]),
  session: Object.freeze(["api", "worker", "migrator", "test"]),
});
const RUN_ID_PATTERN = /^run_[a-z0-9][a-z0-9_-]{2,31}$/u;
const ENDPOINT_PATTERN = /^[a-z0-9][a-z0-9._-]{1,63}$/u;
const REDIS_DATABASES = [8, 9, 10, 11, 12, 13, 14, 15];
const LOCK_FILE = ".lease.lock";
const DEFAULT_DATA_RESOURCES = ["mysql", "mongo", "redis", "minio"];
const DATA_RESOURCES = [...DEFAULT_DATA_RESOURCES, "postgres"];
const CHILD_ENVIRONMENT_VARIABLES = [
  "PATH", "HOME", "USER", "LOGNAME", "TMPDIR", "TMP", "TEMP",
  "LANG", "LC_ALL", "LC_CTYPE", "SSL_CERT_FILE", "SSL_CERT_DIR", "SSH_AUTH_SOCK",
  "DOCKER_HOST", "DOCKER_CONTEXT", "DOCKER_CONFIG", "DOCKER_CERT_PATH",
  "DOCKER_TLS_VERIFY", "DOCKER_API_VERSION", "DOCKER_DEFAULT_PLATFORM",
  "COMPOSE_ANSI", "COMPOSE_PROGRESS", "COMPOSE_PARALLEL_LIMIT", "COMPOSE_STATUS_STDOUT",
  "MC_CONFIG_DIR", "MC_INSECURE", "MC_NO_COLOR", "MC_QUIET",
  "KOKORO_INFRA_SCOPE", "KOKORO_INFRA_ENVIRONMENT_SCOPE", "KOKORO_INFRA_RESTART_POLICY",
  "KOKORO_NETWORK", "KOKORO_MYSQL_PORT", "KOKORO_POSTGRES_PORT", "KOKORO_REDIS_PORT",
  "KOKORO_MONGO_PORT", "KOKORO_MINIO_PORT", "KOKORO_MINIO_CONSOLE_PORT",
];

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

function normalizeResources(resources = DEFAULT_DATA_RESOURCES) {
  if (
    !Array.isArray(resources) ||
    resources.length === 0 ||
    resources.some((resource) => !DATA_RESOURCES.includes(resource)) ||
    new Set(resources).size !== resources.length
  ) {
    throw scopeError("infra_scope_resources_invalid");
  }
  return [...resources].sort();
}

function createLease({ runId, endpointFingerprint, redisDatabase, resources }) {
  const databaseStem = `kokoro_test_${runId}`.replaceAll("-", "_");
  const bucketRun = runId.replaceAll("_", "-");
  return {
    schemaVersion: 1,
    runId,
    endpointFingerprint,
    resources: normalizeResources(resources),
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
    postgres: Object.fromEntries(
      POSTGRES_CONTEXTS.map((context) => [context, {
        database: `${databaseStem}_${context}`,
        roles: Object.fromEntries(
          POSTGRES_ROLES[context].map((role) => {
            const suffix = createHash("sha256")
              .update(`${runId}:postgres:${context}:${role}`)
              .digest("hex")
              .slice(0, 12);
            return [role, {
              username: `kt_pg_${context}${role}_${suffix}`,
              password: randomBytes(24).toString("base64url"),
            }];
          }),
        ),
      }]),
    ),
    mongo: { database: databaseStem },
    redis: redisDatabase === null ? null : {
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

export async function acquireScope({
  stateRoot,
  runId,
  endpointFingerprint,
  resources = DEFAULT_DATA_RESOURCES,
}) {
  validateIdentity({ runId, endpointFingerprint });
  const selectedResources = normalizeResources(resources);
  return withLeaseLock(stateRoot, async () => {
    try {
      await readFile(leasePath(stateRoot, runId));
      throw scopeError("infra_scope_busy");
    } catch (error) {
      if (error.code !== "ENOENT") throw error;
    }
    const used = new Set((await activeLeases(stateRoot)).map((lease) => lease.redis?.database));
    const redisDatabase = selectedResources.includes("redis")
      ? REDIS_DATABASES.find((database) => !used.has(database))
      : null;
    if (redisDatabase === undefined) throw scopeError("infra_scope_redis_exhausted");
    const lease = createLease({
      runId,
      endpointFingerprint,
      redisDatabase,
      resources: selectedResources,
    });
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
    ...Object.values(lease.postgres ?? {}).flatMap(({ database, roles }) => [
      database,
      ...Object.values(roles).map(({ username }) => username),
    ]),
    lease.mongo.database,
    lease.minio.bucket,
    lease.minio.prefix,
    ...(lease.redis ? [`redis-db-${lease.redis.database}`, lease.redis.keyPrefix] : []),
  ]);
  const prefixValid = kind === "minio"
    ? name.startsWith("kokoro-test-") || name.startsWith("run_")
    : kind === "redis"
      ? name.startsWith("redis-db-") || name.startsWith("kokoro_test_")
      : kind === "postgres"
        ? name.startsWith("kokoro_test_") || name.startsWith("kt_pg_")
      : name.startsWith("kokoro_test_");
  if (!allowed.has(name) || !prefixValid) {
    throw scopeError("infra_cleanup_target_invalid", `${kind}:${name}`);
  }
  return true;
}

function childEnvironment(environment) {
  return Object.fromEntries(CHILD_ENVIRONMENT_VARIABLES.flatMap((name) =>
    typeof environment?.[name] === "string" ? [[name, environment[name]]] : []));
}

function defaultRun(command, args, options = {}) {
  const spawn = options.spawn ?? spawnSync;
  return spawn(command, args, {
    encoding: "utf8",
    shell: false,
    input: options.input ?? "",
    maxBuffer: 1024 * 1024,
    env: childEnvironment(options.environment ?? process.env),
  });
}

function commandRunner({ run, spawn, environment }) {
  if (run) return run;
  return (command, args, options = {}) => defaultRun(command, args, {
    ...options,
    spawn,
    environment,
  });
}

function checkedRun(run, command, args, options = {}) {
  const result = run(command, args, options);
  if (result.error || result.status !== 0) {
    throw scopeError("infra_scope_command_failed", `${command} exit ${result.status ?? "error"}`);
  }
  return result;
}

function requireMysqlAdminCredential(value) {
  if (typeof value !== "string" || value.length === 0) {
    throw scopeError("infra_scope_mysql_admin_credential_missing");
  }
  if (/[\r\n\0]/u.test(value)) {
    throw scopeError("infra_scope_mysql_admin_credential_invalid");
  }
  return value;
}

function mysqlInput(rootPassword, sql) {
  return `${rootPassword}\n${sql}`;
}

function redisMarker(stdout) {
  if (typeof stdout !== "string") throw scopeError("infra_scope_redis_token_mismatch");
  if (stdout.endsWith("\n")) return stdout.slice(0, -1);
  throw scopeError("infra_scope_redis_token_mismatch");
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

function pgLiteral(value) {
  if (!/^[a-zA-Z0-9_-]+$/u.test(value)) throw scopeError("infra_scope_credential_invalid");
  return `'${value}'`;
}

function pgIdentifier(value) {
  if (!/^[a-z0-9_]+$/u.test(value)) throw scopeError("infra_scope_identifier_invalid");
  return `"${value}"`;
}

function postgresSql(lease, action) {
  const statements = [];
  for (const context of POSTGRES_CONTEXTS) {
    const allocation = lease.postgres[context];
    const contextRoles = POSTGRES_ROLES[context];
    const database = pgLiteral(allocation.database);
    const migrator = pgLiteral(allocation.roles.migrator.username);
    if (action === "create") {
      for (const role of contextRoles) {
        const { username, password } = allocation.roles[role];
        statements.push(
          `SELECT format('CREATE ROLE %I LOGIN PASSWORD %L', ${pgLiteral(username)}, ${pgLiteral(password)}) ` +
            `WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = ${pgLiteral(username)}) \\gexec`,
          `SELECT format('ALTER ROLE %I LOGIN PASSWORD %L NOSUPERUSER NOCREATEDB NOCREATEROLE ` +
            `${role === "test" ? "INHERIT" : "NOINHERIT"} NOREPLICATION NOBYPASSRLS', ` +
            `${pgLiteral(username)}, ${pgLiteral(password)}) \\gexec`,
        );
      }
      statements.push(
        `SELECT format('CREATE DATABASE %I OWNER %I', ${database}, ${migrator}) ` +
          `WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = ${database}) \\gexec`,
        `SELECT format('REVOKE CONNECT, TEMPORARY ON DATABASE %I FROM PUBLIC', ${database}) \\gexec`,
        `SELECT format('GRANT CONNECT ON DATABASE %I TO %I', ${database}, ${migrator}) \\gexec`,
        ...contextRoles.filter((role) => !["migrator", "test"].includes(role)).map((role) =>
          `SELECT format('GRANT CONNECT ON DATABASE %I TO %I', ${database}, ` +
            `${pgLiteral(allocation.roles[role].username)}) \\gexec`,
        ),
        `SELECT format('GRANT CONNECT ON DATABASE %I TO %I', ${database}, ` +
          `${pgLiteral(allocation.roles.test.username)}) \\gexec`,
        `\\connect ${pgIdentifier(allocation.database)}`,
        "REVOKE ALL ON SCHEMA public FROM PUBLIC;",
        // Root provisions identities and CONNECT only. Child migrations own
        // schema/table grants so a new module cannot inherit broad DML by
        // accident.
        `GRANT ${pgIdentifier(allocation.roles.migrator.username)} TO ` +
          `${pgIdentifier(allocation.roles.test.username)};`,
        "\\connect postgres",
      );
    } else {
      statements.push(
        `SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = ${database} AND pid <> pg_backend_pid();`,
        `SELECT format('DROP DATABASE IF EXISTS %I', ${database}) \\gexec`,
      );
      for (const role of [...contextRoles].reverse()) {
        const username = pgLiteral(allocation.roles[role].username);
        statements.push(`SELECT format('DROP ROLE IF EXISTS %I', ${username}) \\gexec`);
      }
    }
  }
  return `${statements.join("\n")}\n`;
}

const composeExec = (service, command) => [
  "compose", "--project-name", "kokoro-infra", "-f", "docker-compose.infra.yml",
  "exec", "-T", service, ...command,
];

export async function provisionScope({
  lease,
  mysqlRootPassword,
  environment = process.env,
  spawn = spawnSync,
  run,
}) {
  validateIdentity(lease);
  const resources = normalizeResources(lease.resources);
  const execute = commandRunner({ run, spawn, environment });
  const mysqlAdminCredential = resources.includes("mysql")
    ? requireMysqlAdminCredential(
      mysqlRootPassword === undefined ? environment.MYSQL_ROOT_PASSWORD : mysqlRootPassword,
    )
    : null;
  if (resources.includes("redis")) {
    const guardedSetScript = [
      'if redis.call("DBSIZE") ~= 0 then return 0 end',
      'redis.call("SET", KEYS[1], ARGV[1])',
      "return 1",
    ].join(" ");
    const redisResult = checkedRun(execute, "docker", composeExec("redis", [
      "redis-cli", "--raw", "-n", String(lease.redis.database), "-x",
      "EVAL", guardedSetScript, "1", lease.redis.markerKey,
    ]), { input: lease.leaseToken });
    if (redisResult.stdout.trim() !== "1") throw scopeError("infra_scope_redis_busy");
  }
  if (resources.includes("mysql")) {
    checkedRun(execute, "docker", composeExec("mysql", [
      "sh", "-c", 'IFS= read -r MYSQL_PWD; export MYSQL_PWD; exec mysql --protocol=TCP -h127.0.0.1 -uroot',
    ]), { input: mysqlInput(mysqlAdminCredential, mysqlSql(lease, "create")) });
  }
  if (resources.includes("postgres")) {
    checkedRun(execute, "docker", composeExec("postgres", [
      "sh", "-c", 'exec psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d postgres',
    ]), { input: postgresSql(lease, "create") });
  }

  if (resources.includes("mongo")) {
    const mongoScript = `db.getSiblingDB(${JSON.stringify(lease.mongo.database)})` +
      `.getCollection("__kokoro_scope").updateOne({_id:"lease"},{$set:{active:true}},{upsert:true});\n`;
    checkedRun(execute, "docker", composeExec("mongo", ["mongosh", "--quiet"]), { input: mongoScript });
  }

  if (resources.includes("minio")) {
    const target = `${lease.minio.alias}/${lease.minio.bucket}`;
    checkedRun(execute, "mc", ["mb", "--ignore-existing", target]);
    checkedRun(execute, "mc", ["pipe", `${target}/${lease.minio.prefix}__scope`], { input: "scope\n" });
  }
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
  mysqlRootPassword,
  environment = process.env,
  spawn = spawnSync,
  run,
}) {
  const lease = await readScope({ stateRoot, runId });
  if (lease.leaseToken !== leaseToken) throw scopeError("infra_scope_token_mismatch");
  if (lease.endpointFingerprint !== endpointFingerprint) {
    throw scopeError("infra_scope_endpoint_mismatch");
  }
  const resources = normalizeResources(lease.resources);
  const execute = commandRunner({ run, spawn, environment });
  const mysqlAdminCredential = resources.includes("mysql")
    ? requireMysqlAdminCredential(
      mysqlRootPassword === undefined ? environment.MYSQL_ROOT_PASSWORD : mysqlRootPassword,
    )
    : null;
  if (resources.includes("mysql")) {
    for (const name of Object.values(lease.mysql)) {
      assertCleanupTarget({ lease, kind: "mysql", name, endpointFingerprint });
    }
  }
  if (resources.includes("postgres")) {
    for (const { database, roles } of Object.values(lease.postgres)) {
      assertCleanupTarget({ lease, kind: "postgres", name: database, endpointFingerprint });
      for (const { username } of Object.values(roles)) {
        assertCleanupTarget({ lease, kind: "postgres", name: username, endpointFingerprint });
      }
    }
  }
  if (resources.includes("mongo")) {
    assertCleanupTarget({ lease, kind: "mongo", name: lease.mongo.database, endpointFingerprint });
  }
  if (resources.includes("redis")) {
    assertCleanupTarget({ lease, kind: "redis", name: `redis-db-${lease.redis.database}`, endpointFingerprint });
    assertCleanupTarget({ lease, kind: "redis", name: lease.redis.keyPrefix, endpointFingerprint });
  }
  if (resources.includes("minio")) {
    assertCleanupTarget({ lease, kind: "minio", name: lease.minio.bucket, endpointFingerprint });
    assertCleanupTarget({ lease, kind: "minio", name: lease.minio.prefix, endpointFingerprint });
  }

  let redisMarkerPresent = false;
  if (resources.includes("redis")) {
    const marker = redisMarker(checkedRun(execute, "docker", composeExec("redis", [
      "redis-cli", "--raw", "-n", String(lease.redis.database), "GET", lease.redis.markerKey,
    ])).stdout);
    if (marker !== "" && marker !== leaseToken) throw scopeError("infra_scope_redis_token_mismatch");
    if (marker === "") {
      const databaseSize = checkedRun(execute, "docker", composeExec("redis", [
        "redis-cli", "--raw", "-n", String(lease.redis.database), "DBSIZE",
      ])).stdout.trim();
      if (databaseSize !== "0") throw scopeError("infra_scope_redis_unowned_data");
    }
    redisMarkerPresent = marker === leaseToken;
  }

  if (resources.includes("mysql")) {
    checkedRun(execute, "docker", composeExec("mysql", [
      "sh", "-c", 'IFS= read -r MYSQL_PWD; export MYSQL_PWD; exec mysql --protocol=TCP -h127.0.0.1 -uroot',
    ]), { input: mysqlInput(mysqlAdminCredential, mysqlSql(lease, "drop")) });
  }
  if (resources.includes("postgres")) {
    checkedRun(execute, "docker", composeExec("postgres", [
      "sh", "-c", 'exec psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d postgres',
    ]), { input: postgresSql(lease, "drop") });
  }
  if (resources.includes("mongo")) {
    const mongoScript = `db.getSiblingDB(${JSON.stringify(lease.mongo.database)}).dropDatabase();\n`;
    checkedRun(execute, "docker", composeExec("mongo", ["mongosh", "--quiet"]), { input: mongoScript });
  }
  if (redisMarkerPresent) {
    const guardedFlushScript = [
      'if redis.call("GET", KEYS[1]) ~= ARGV[1] then return 0 end',
      'redis.call("FLUSHDB")',
      "return 1",
    ].join(" ");
    const flushResult = checkedRun(execute, "docker", composeExec("redis", [
      "redis-cli", "--raw", "-n", String(lease.redis.database), "-x",
      "EVAL", guardedFlushScript, "1", lease.redis.markerKey,
    ]), { input: leaseToken });
    if (flushResult.stdout.trim() !== "1") throw scopeError("infra_scope_redis_token_mismatch");
  }

  if (resources.includes("minio")) {
    const target = `${lease.minio.alias}/${lease.minio.bucket}/${lease.minio.prefix}`;
    checkedRun(execute, "mc", ["rm", "--incomplete", "--recursive", "--force", target]);
    checkedRun(execute, "mc", ["rm", "--recursive", "--force", target]);
    checkedRun(execute, "mc", ["rb", "--force", `${lease.minio.alias}/${lease.minio.bucket}`]);
  }
  await releaseScope({ stateRoot, runId, leaseToken, endpointFingerprint });
}
