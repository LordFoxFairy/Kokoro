#!/usr/bin/env node
/** Run-owned BFF project upload -> Storage v2 -> S3/ClamAV integration smoke. */
import { createHash, randomBytes, randomUUID } from "node:crypto"
import { createServer } from "node:http"
import { createRequire } from "node:module"
import { spawn, execFileSync } from "node:child_process"
import { mkdtemp, open, rm, chmod, mkdir, copyFile, symlink } from "node:fs/promises"
import { tmpdir } from "node:os"
import { dirname, resolve, join } from "node:path"
import { fileURLToPath } from "node:url"

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../..")
const BFF = join(ROOT, "apps/kokoro-bff")
const STORAGE = join(ROOT, "apps/kokoro-storage")
const requireStorage = createRequire(join(STORAGE, "package.json"))
const EICAR = Buffer.from("X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*", "ascii")
const MAX_RESPONSE = 1_048_576

class SmokeError extends Error {}
const ensure = (condition, message) => { if (!condition) throw new SmokeError(message) }
const sha256 = (bytes) => createHash("sha256").update(bytes).digest("hex")
const origin = (value, name) => {
  const url = new URL(value)
  ensure(["http:", "https:"].includes(url.protocol) && !url.username && !url.password && !url.search && !url.hash && ["", "/"].includes(url.pathname), `${name} must be an HTTP(S) origin`)
  return url.origin
}
const databaseUrl = (source, name, schema) => {
  const url = new URL(source)
  url.pathname = `/${name}`
  url.searchParams.delete("schema")
  url.searchParams.delete("options")
  url.searchParams.delete("search_path")
  url.searchParams.set("schema", schema)
  return url.toString()
}
const redisDb = (source, db) => {
  const url = new URL(source)
  ensure(["redis:", "rediss:"].includes(url.protocol), "explicit Redis URL required")
  url.pathname = `/${db}`
  return url.toString()
}

export function checkConfiguration(env) {
  for (const key of ["KOKORO_W2_POSTGRES_ADMIN_URL", "KOKORO_W2_REDIS_URL", "KOKORO_W2_BFF_NODE_BIN", "KOKORO_W2_TEST_BUCKET", "KOKORO_W2_EXCLUSIVE_BUCKET", "KOKORO_OBJECT_STORE_ENDPOINT", "KOKORO_OBJECT_STORE_PUBLIC_ENDPOINT", "KOKORO_OBJECT_STORE_REGION", "KOKORO_OBJECT_STORE_ACCESS_KEY_ID", "KOKORO_OBJECT_STORE_SECRET_ACCESS_KEY", "KOKORO_SCANNER_HOST", "KOKORO_SCANNER_PORT"])
    ensure(env[key]?.trim(), `${key} is required`)
  ensure(env.KOKORO_W2_EXCLUSIVE_BUCKET === env.KOKORO_W2_TEST_BUCKET, "exclusive bucket confirmation must exactly match the test bucket")
  const pg = new URL(env.KOKORO_W2_POSTGRES_ADMIN_URL)
  ensure(["postgres:", "postgresql:"].includes(pg.protocol) && !pg.hash && ![...pg.searchParams.keys()].some(key => ["schema", "options", "search_path"].includes(key.toLowerCase())), "explicit PostgreSQL admin URL without owner schema or search-path options required")
  redisDb(env.KOKORO_W2_REDIS_URL, 6)
  const storageEndpoint = origin(env.KOKORO_OBJECT_STORE_ENDPOINT, "KOKORO_OBJECT_STORE_ENDPOINT")
  const publicEndpoint = origin(env.KOKORO_OBJECT_STORE_PUBLIC_ENDPOINT, "KOKORO_OBJECT_STORE_PUBLIC_ENDPOINT")
  ensure(storageEndpoint !== "" && publicEndpoint !== "", "S3 endpoints required")
  ensure(env.KOKORO_OBJECT_STORE_PROFILE === "custom", "explicit custom S3 profile required")
  ensure(env.KOKORO_OBJECT_STORE_FORCE_PATH_STYLE === "true", "path-style test bucket required")
  ensure(!env.AWS_SESSION_TOKEN && !env.KOKORO_OBJECT_STORE_SESSION_TOKEN, "explicit test credentials cannot be combined with a session token")
  ensure(/^[a-z0-9][a-z0-9.-]{2,62}$/.test(env.KOKORO_W2_TEST_BUCKET), "test bucket name invalid")
  const scannerPort = Number(env.KOKORO_SCANNER_PORT)
  ensure(Number.isInteger(scannerPort) && scannerPort > 0 && scannerPort <= 65535, "scanner port invalid")
  ensure(env.KOKORO_W2_BFF_NODE_BIN.startsWith("/"), "BFF Node path must be absolute")
  return { storageEndpoint, publicEndpoint, bucket: env.KOKORO_W2_TEST_BUCKET, scannerPort }
}

function quietVersion(command, args) {
  try { return execFileSync(command, args, { encoding: "utf8", timeout: 5000, stdio: ["ignore", "pipe", "ignore"] }).trim() }
  catch { throw new SmokeError("required owner toolchain is unavailable") }
}

async function limitedResponse(response, label) {
  const bytes = Buffer.from(await response.arrayBuffer())
  ensure(bytes.length <= MAX_RESPONSE, `${label} response exceeded smoke limit`)
  let data
  try { data = JSON.parse(bytes.toString("utf8")) }
  catch { throw new SmokeError(`${label} response is not JSON`) }
  ensure(data && typeof data === "object" && !Array.isArray(data), `${label} response is not an object`)
  return data
}

async function jsonRequest(base, path, method, headers, body, expected) {
  const response = await fetch(base + path, { method, headers, ...(body === undefined ? {} : { body }), redirect: "error", signal: AbortSignal.timeout(45000) })
  const value = await limitedResponse(response, path)
  ensure(response.status === expected, `${method} ${path} returned HTTP ${response.status}, expected ${expected}; code=${value.error?.code ?? "none"}`)
  return value
}

async function waitReady(base, label, process) {
  const deadline = Date.now() + 40000
  while (Date.now() < deadline) {
    ensure(process.exitCode === null && process.signalCode === null, `${label} exited before readiness`)
    try {
      const response = await fetch(`${base}/readyz`, { signal: AbortSignal.timeout(1500) })
      const body = await limitedResponse(response, `${label} readiness`)
      const expected = label === "Storage"
        ? body.status === "ready" && Object.keys(body).length === 1
        : body.status === "ok" && body.service === "kokoro-bff" && body.mode === "live"
      if (response.status === 200 && expected && process.exitCode === null && process.signalCode === null) return
    } catch { /* dependency readiness is bounded by the shared deadline */ }
    await new Promise(resolve => setTimeout(resolve, 200))
  }
  throw new SmokeError(`${label} did not become ready`)
}

function startIamStub(tokens, tenant, owner, other) {
  const server = createServer((request, response) => {
    const token = request.headers.authorization?.replace(/^Bearer /, "")
    const identity = token === tokens.owner ? owner : token === tokens.other ? other : null
    const status = request.method === "POST" && request.url === "/internal/v1/session-authorizations/verify" && request.headers["content-length"] === "0" && identity ? 200 : 401
    const payload = status === 200
      ? { data: { allowed: true, tenant_id: tenant, user_id: identity, session_id: `session-${identity}`, client_id: "w2-storage-smoke" } }
      : { error: { code: "UNAUTHENTICATED", message: "fixture rejected request", retryable: false, details: [] } }
    const raw = Buffer.from(JSON.stringify(payload))
    response.writeHead(status, { "content-type": "application/json", "cache-control": "no-store", "x-request-id": request.headers["x-request-id"] || randomUUID(), "content-length": raw.length, connection: "close" })
    response.end(raw)
  })
  return server
}

async function listen(server) {
  await new Promise((resolve, reject) => { server.once("error", reject); server.listen(0, "127.0.0.1", resolve) })
  return `http://127.0.0.1:${server.address().port}`
}
const closeServer = server => new Promise((resolve, reject) => server.close(error => error ? reject(error) : resolve()))

function spawnOwned(command, args, cwd, env, logFd) {
  return spawn(command, args, { cwd, env, stdin: "ignore", stdio: ["ignore", logFd, logFd], detached: true })
}
async function stopOwned(child) {
  if (!child || child.exitCode !== null || child.signalCode !== null) return
  try { process.kill(-child.pid, "SIGTERM") }
  catch (error) { if (error.code !== "ESRCH") throw error }
  const ended = new Promise(resolve => child.once("exit", resolve))
  await Promise.race([ended, new Promise(resolve => setTimeout(resolve, 15000))])
  if (child.exitCode === null && child.signalCode === null) {
    try { process.kill(-child.pid, "SIGKILL") }
    catch (error) { if (error.code !== "ESRCH") throw error }
    await Promise.race([ended, new Promise(resolve => setTimeout(resolve, 5000))])
  }
  ensure(child.exitCode !== null || child.signalCode !== null, "owned BFF process did not stop")
}

async function runCommand(command, args, cwd, env, logFd, timeout = 90000) {
  const child = spawnOwned(command, args, cwd, env, logFd)
  const completed = new Promise((resolve, reject) => { child.once("exit", (code, signal) => resolve({ code, signal })); child.once("error", reject) })
  let timer
  try {
    const result = await Promise.race([completed, new Promise((_, reject) => { timer = setTimeout(() => reject(new SmokeError("owner schema command timed out")), timeout) })])
    ensure(result.code === 0 && result.signal === null, "owner canonical schema installation failed")
  } finally { clearTimeout(timer); await stopOwned(child) }
}

function s3Client(env) {
  const { S3Client } = requireStorage("@aws-sdk/client-s3")
  return new S3Client({ endpoint: env.KOKORO_OBJECT_STORE_ENDPOINT, region: env.KOKORO_OBJECT_STORE_REGION, forcePathStyle: true, credentials: { accessKeyId: env.KOKORO_OBJECT_STORE_ACCESS_KEY_ID, secretAccessKey: env.KOKORO_OBJECT_STORE_SECRET_ACCESS_KEY }, maxAttempts: 1 })
}

async function listOwnedVersions(s3, bucket, prefix) {
  const { ListObjectVersionsCommand } = requireStorage("@aws-sdk/client-s3")
  const result = await s3.send(new ListObjectVersionsCommand({ Bucket: bucket, Prefix: prefix, MaxKeys: 1000 }), { abortSignal: AbortSignal.timeout(10000) })
  ensure(!result.IsTruncated, "owned object inventory exceeded one bounded page; retain database and object evidence")
  const versions = result.Versions ?? [], markers = result.DeleteMarkers ?? []
  ensure([...versions, ...markers].every(item => item.Key?.startsWith(prefix) && item.VersionId && item.VersionId !== "null"), "owned object inventory returned ambiguous identity")
  return { versions, markers }
}

export async function preflightS3(s3, config, prefix) {
  const { HeadBucketCommand, GetBucketVersioningCommand, GetObjectLockConfigurationCommand } = requireStorage("@aws-sdk/client-s3")
  await s3.send(new HeadBucketCommand({ Bucket: config.bucket }), { abortSignal: AbortSignal.timeout(10000) })
  const versioning = await s3.send(new GetBucketVersioningCommand({ Bucket: config.bucket }), { abortSignal: AbortSignal.timeout(10000) })
  const lock = await s3.send(new GetObjectLockConfigurationCommand({ Bucket: config.bucket }), { abortSignal: AbortSignal.timeout(10000) })
  ensure(versioning.Status === "Enabled" && versioning.MFADelete !== "Enabled" && lock.ObjectLockConfiguration?.ObjectLockEnabled === "Enabled" && !lock.ObjectLockConfiguration.Rule?.DefaultRetention,
    "exclusive test bucket requires Versioning and ObjectLock enabled, no default retention or MFA delete")
  const prior = await listOwnedVersions(s3, config.bucket, prefix)
  ensure(prior.versions.length === 0 && prior.markers.length === 0, "new run prefix was not empty before writes")
}

export async function cleanupObjects(s3, bucket, prefix) {
  const { DeleteObjectCommand, HeadObjectCommand } = requireStorage("@aws-sdk/client-s3")
  const current = await listOwnedVersions(s3, bucket, prefix)
  ensure(current.markers.length === 0, "unexpected owned delete marker; preserve run resources")
  for (const item of current.versions) {
    ensure(item.Key.startsWith(prefix) && /^([^/]+)\/(uploads|final)\//.test(item.Key) && item.ETag, "unrecognized owned object; preserve run resources")
    // The prefix was proven empty before this run. Delete only concrete version+ETag identities.
    await s3.send(new DeleteObjectCommand({ Bucket: bucket, Key: item.Key, VersionId: item.VersionId, IfMatch: item.ETag }), { abortSignal: AbortSignal.timeout(10000) })
    try {
      await s3.send(new HeadObjectCommand({ Bucket: bucket, Key: item.Key, VersionId: item.VersionId }), { abortSignal: AbortSignal.timeout(10000) })
      throw new SmokeError("exact owned version still exists after conditional delete")
    } catch (error) { if (error instanceof SmokeError || error.$metadata?.httpStatusCode !== 404) throw error }
  }
  const after = await listOwnedVersions(s3, bucket, prefix)
  ensure(after.versions.length === 0 && after.markers.length === 0, "owned object versions remain after cleanup")
}

export async function createDatabase(admin, name) {
  const existing = await admin.query("SELECT 1 FROM pg_database WHERE datname = $1", [name])
  if (existing.rowCount !== 0) throw Object.assign(new SmokeError("run database already exists; refusing adoption"), { preexisting: true })
  await admin.query(`CREATE DATABASE "${name}"`)
}
async function dropDatabase(admin, name) {
  await admin.query(`DROP DATABASE "${name}" WITH (FORCE)`)
  ensure((await admin.query("SELECT 1 FROM pg_database WHERE datname = $1", [name])).rowCount === 0, "owned database still exists")
}

async function storageReference(base, identity, asset, secret) {
  const request = { command: { commandId: `w2-download-${randomUUID()}`, requestDigest: sha256(Buffer.from(asset.asset_id)) }, assetId: asset.asset_id, contentSha256: asset.content_sha256 }
  const headers = {
    "content-type": "application/json", "connect-protocol-version": "1",
    "x-kokoro-service": "web-bff", "x-kokoro-internal-secret": secret,
    "x-kokoro-tenant-id": identity.tenant, "x-kokoro-subject-id": identity.owner,
    "x-kokoro-request-id": randomUUID(), "x-kokoro-scope-kind": "project", "x-kokoro-scope-id": identity.projectId,
  }
  const result = await jsonRequest(base, "/kokoro.storage.v2.StorageService/GetDownloadReference", "POST", headers, JSON.stringify(request), 200)
  ensure(result.downloadReference?.method === "GET" && result.assetId === asset.asset_id, "Storage download reference response drift")
  return result.downloadReference
}

async function runCases(bffBase, storageBase, publicOrigin, identity, tokens, webSecret, storageSecret, database) {
  const auth = token => ({ "x-kokoro-service": "web-bff", "x-kokoro-internal-secret": webSecret, authorization: `Bearer ${token}` })
  const created = await jsonRequest(bffBase, "/v1/projects", "POST", { ...auth(tokens.owner), "content-type": "application/json", "idempotency-key": `project-${identity.tenant}` }, JSON.stringify({ name: "W2 owned project", description: "cross-owner smoke" }), 200)
  const project = created.data?.project
  ensure(project?.id && project?.slug, "BFF project response drift")
  identity.projectId = project.id
  // Keep the status assertion outside the common request helper so 422/404 are inspectable.
  const post = async (token, key, bytes, filename) => {
    const form = new FormData()
    form.append("files", new File([bytes], filename, { type: "text/plain" }))
    const response = await fetch(`${bffBase}/v1/projects/${encodeURIComponent(project.slug)}/resources`, { method: "POST", headers: { ...auth(token), "idempotency-key": key }, body: form, redirect: "error", signal: AbortSignal.timeout(45000) })
    return { status: response.status, body: await limitedResponse(response, "project resource") }
  }
  const list = (token, query = "") => jsonRequest(
    bffBase,
    `/v1/projects/${encodeURIComponent(project.slug)}/resources${query}`,
    "GET",
    auth(token),
    undefined,
    200,
  )
  const bytes = Buffer.from(`W2 real project resource ${identity.tenant}`, "utf8")
  const key = `upload-${identity.tenant}`
  const first = await post(tokens.owner, key, bytes, "resource.txt")
  ensure(first.status === 200 && first.body.data?.resources?.length === 1, `clean upload failed: HTTP ${first.status}, code=${first.body.error?.code ?? "none"}`)
  const asset = first.body.data.resources[0]
  ensure(asset.scan_state === "clean" && asset.content_sha256 === sha256(bytes) && !JSON.stringify(first.body).includes("http://"), "clean asset metadata drift or signed URL leaked")
  const replay = await post(tokens.owner, key, bytes, "resource.txt")
  ensure(replay.status === 200 && replay.body.data?.resources?.[0]?.asset_id === asset.asset_id, "same-key replay created a different asset")
  const count = await database.query("SELECT count(*)::int AS n FROM kokoro_storage.storage_asset WHERE tenant_id = $1", [identity.tenant])
  ensure(count.rows[0]?.n === 1, "Storage persisted duplicate or missing asset")
  const reference = await storageReference(storageBase, identity, asset, storageSecret)
  ensure(new URL(reference.url).origin === publicOrigin, "Storage returned an unexpected object origin")
  const get = await fetch(reference.url, { method: "GET", headers: reference.requiredHeaders ?? {}, redirect: "error", signal: AbortSignal.timeout(15000) })
  ensure(get.status === 200, "signed GET failed")
  const downloaded = Buffer.from(await get.arrayBuffer())
  ensure(downloaded.equals(bytes), "signed GET bytes did not match BFF POST")
  const firstPageBeforeSecondUpload = await list(tokens.owner, "?limit=1")
  ensure(firstPageBeforeSecondUpload.data?.items?.length === 1 && firstPageBeforeSecondUpload.data.items[0].asset_id === asset.asset_id && firstPageBeforeSecondUpload.data.next_cursor === null, "project resource GET did not reload the persisted asset")
  const secondBytes = Buffer.from(`W2 second resource ${identity.tenant}`, "utf8")
  const second = await post(tokens.owner, `upload-second-${identity.tenant}`, secondBytes, "resource-two.txt")
  ensure(second.status === 200 && second.body.data?.resources?.length === 1, "second project upload failed")
  const secondAssetId = second.body.data.resources[0].asset_id
  const pageOne = await list(tokens.owner, "?limit=1")
  ensure(pageOne.data?.items?.length === 1 && typeof pageOne.data.next_cursor === "string" && pageOne.data.next_cursor.length > 0, "project resource pagination did not return a cursor")
  const pageTwo = await list(tokens.owner, `?limit=1&cursor=${encodeURIComponent(pageOne.data.next_cursor)}`)
  const listedIds = new Set([pageOne.data.items[0].asset_id, pageTwo.data?.items?.[0]?.asset_id])
  ensure(pageTwo.data?.items?.length === 1 && pageTwo.data.next_cursor === null && listedIds.size === 2 && listedIds.has(asset.asset_id) && listedIds.has(secondAssetId), "project resource pagination lost or duplicated an asset")
  const listedCount = await database.query("SELECT count(*)::int AS n FROM kokoro_storage.storage_asset WHERE tenant_id = $1 AND scan_state = 'clean'", [identity.tenant])
  ensure(listedCount.rows[0]?.n === 2, "project list disagrees with clean Storage assets")
  const denied = await post(tokens.other, key, bytes, "resource.txt")
  ensure(denied.status === 404 && denied.body.error?.code === "project_not_found", "other subject reached project Storage scope")
  const deniedList = await jsonRequest(bffBase, `/v1/projects/${encodeURIComponent(project.slug)}/resources`, "GET", auth(tokens.other), undefined, 404)
  ensure(deniedList.error?.code === "project_not_found", "other subject listed private project assets")
  const infected = await post(tokens.owner, `infected-${identity.tenant}`, EICAR, "eicar.txt")
  ensure(infected.status === 422 && infected.body.error?.code === "resource_file_infected" && !infected.body.data?.resources, "EICAR was not terminally denied")
  const afterInfected = await list(tokens.owner)
  ensure(afterInfected.data?.items?.length === 2 && afterInfected.data.items.every(item => item.scan_state === "clean"), "infected asset appeared in project list")
  return ["clean_project_upload", "same_key_replay", "owner_signed_get_bytes", "project_list_reload", "project_list_pagination", "cross_subject_denied", "eicar_denied"]
}

async function prepareStorageSchemaFixture(directory) {
  const fixture = join(directory, "storage-schema")
  await mkdir(join(fixture, "scripts"), { recursive: true })
  await mkdir(join(fixture, "prisma"), { recursive: true })
  for (const path of ["package.json", "prisma.config.ts", "prisma/schema.prisma", "scripts/apply-schema.ts"])
    await copyFile(join(STORAGE, path), join(fixture, path))
  await symlink(join(STORAGE, "node_modules"), join(fixture, "node_modules"), "dir")
  return fixture
}

async function main() {
  if (process.argv.includes("--check-config")) {
    checkConfiguration(process.env)
    process.stdout.write("W2 configuration shape valid; provider not contacted\n")
    return
  }
  const env = process.env
  const config = checkConfiguration(env)
  ensure(process.versions.node.startsWith("24."), "Storage smoke requires Node 24")
  ensure(quietVersion(env.KOKORO_W2_BFF_NODE_BIN, ["--version"]).startsWith("v22."), "BFF smoke requires Node 22")
  const sources = {
    bff: quietVersion("git", ["-C", BFF, "rev-parse", "HEAD"]),
    storage: quietVersion("git", ["-C", STORAGE, "rev-parse", "HEAD"]),
  }
  ensure(!quietVersion("git", ["-C", BFF, "status", "--porcelain", "--untracked-files=all"]), "BFF worktree is not frozen")
  ensure(!quietVersion("git", ["-C", STORAGE, "status", "--porcelain", "--untracked-files=all"]), "Storage worktree is not frozen")
  ensure(env.NODE_ENV !== "production", "local HTTP signed URL smoke must run in development mode")
  ensure(await import("node:fs/promises").then(fs => fs.stat(join(BFF, "dist/main.js")).then(() => true, () => false)), "BFF build is missing")
  ensure(await import("node:fs/promises").then(fs => fs.stat(join(STORAGE, "dist/main.js")).then(() => true, () => false)), "Storage build is missing")
  const { Pool } = requireStorage("pg")
  const s3 = s3Client(env)
  const runId = randomBytes(12).toString("hex")
  const tenant = `w2-${runId}`
  const prefix = `${tenant}/`
  const databaseName = `w2_bff_storage_${runId}`
  const directory = await mkdtemp(join(tmpdir(), "kokoro-w2-storage-"))
  await chmod(directory, 0o700)
  const log = await open(join(directory, "owners.log"), "wx", 0o600)
  const admin = new Pool({ connectionString: env.KOKORO_W2_POSTGRES_ADMIN_URL, max: 1, connectionTimeoutMillis: 5000 })
  const testUrl = databaseUrl(env.KOKORO_W2_POSTGRES_ADMIN_URL, databaseName, "kokoro_storage")
  const bffUrl = databaseUrl(env.KOKORO_W2_POSTGRES_ADMIN_URL, databaseName, "kokoro_bff")
  const storageSecret = randomBytes(32).toString("hex")
  const webSecret = randomBytes(32).toString("hex")
  const tokens = { owner: randomBytes(32).toString("hex"), other: randomBytes(32).toString("hex") }
  const identity = { tenant, owner: `owner-${runId}`, other: `other-${runId}`, projectId: null }
  let databaseCreated = false, databaseCreateUncertain = false, bff = null, storage = null, iam = null, objectsClean = false, processesStopped = false
  let failure = null, cleanupFailure = null, cases = []
  try {
    await preflightS3(s3, config, prefix)
    try {
      await createDatabase(admin, databaseName)
      databaseCreated = true
    } catch (error) {
      if (!error.preexisting) {
        try { databaseCreated = (await admin.query("SELECT 1 FROM pg_database WHERE datname = $1", [databaseName])).rowCount === 1 }
        catch { databaseCreateUncertain = true }
      }
      throw error
    }
    const baseEnv = { PATH: env.PATH, HOME: env.HOME, TMPDIR: env.TMPDIR, LANG: env.LANG, COREPACK_HOME: env.COREPACK_HOME }
    const storageEnv = { ...baseEnv, PATH: `${dirname(process.execPath)}:${env.PATH}`, NODE_ENV: "development", KOKORO_POSTGRES_URL: testUrl, KOKORO_REDIS_URL: redisDb(env.KOKORO_W2_REDIS_URL, 6), KOKORO_STORAGE_HOST: "127.0.0.1", KOKORO_STORAGE_PORT: "0", KOKORO_STORAGE_SERVICE_CREDENTIALS: `web-bff=${storageSecret}`, KOKORO_OBJECT_STORE_DRIVER: "s3", KOKORO_OBJECT_STORE_PROFILE: "custom", KOKORO_OBJECT_STORE_BUCKET: config.bucket, KOKORO_OBJECT_STORE_REGION: env.KOKORO_OBJECT_STORE_REGION, KOKORO_OBJECT_STORE_ENDPOINT: config.storageEndpoint, KOKORO_OBJECT_STORE_PUBLIC_ENDPOINT: config.publicEndpoint, KOKORO_OBJECT_STORE_ACCESS_KEY_ID: env.KOKORO_OBJECT_STORE_ACCESS_KEY_ID, KOKORO_OBJECT_STORE_SECRET_ACCESS_KEY: env.KOKORO_OBJECT_STORE_SECRET_ACCESS_KEY, KOKORO_OBJECT_STORE_FORCE_PATH_STYLE: "true", KOKORO_SCANNER_DRIVER: "clamav", KOKORO_SCANNER_HOST: env.KOKORO_SCANNER_HOST, KOKORO_SCANNER_PORT: env.KOKORO_SCANNER_PORT }
    const bffEnv = { ...baseEnv, PATH: `${dirname(env.KOKORO_W2_BFF_NODE_BIN)}:${env.PATH}`, NODE_ENV: "development", KOKORO_BFF_HOST: "127.0.0.1", KOKORO_BFF_MODE: "live", KOKORO_DOMAIN: "dev.kokoro.localhost", KOKORO_TENANT_ID: tenant, KOKORO_BFF_SHARED_SECRET: webSecret, KOKORO_BFF_POSTGRES_URL: bffUrl, KOKORO_BFF_REDIS_URL: redisDb(env.KOKORO_W2_REDIS_URL, 8), KOKORO_BFF_STORAGE_SECRET: storageSecret, KOKORO_STORAGE_OBJECT_ORIGIN: config.publicEndpoint }
    const storageSchemaFixture = await prepareStorageSchemaFixture(directory)
    await runCommand(process.execPath, [join(STORAGE, "node_modules/tsx/dist/cli.mjs"), "scripts/apply-schema.ts"], storageSchemaFixture, storageEnv, log.fd)
    await runCommand(join(dirname(env.KOKORO_W2_BFF_NODE_BIN), "corepack"), ["pnpm", "db:apply-schema"], BFF, bffEnv, log.fd)
    const storagePort = createServer()
    const storageBase = await listen(storagePort)
    storageEnv.KOKORO_STORAGE_PORT = new URL(storageBase).port
    await closeServer(storagePort)
    storage = spawnOwned(process.execPath, [join(STORAGE, "dist/main.js")], STORAGE, storageEnv, log.fd)
    await waitReady(storageBase, "Storage", storage)
    iam = startIamStub(tokens, tenant, identity.owner, identity.other)
    const iamBase = await listen(iam)
    bffEnv.KOKORO_IAM_BASE_URL = iamBase
    bffEnv.KOKORO_STORAGE_RPC_BASE_URL = storageBase
    const reservedPort = createServer()
    const candidateUrl = await listen(reservedPort)
    bffEnv.KOKORO_BFF_PORT = new URL(candidateUrl).port
    await closeServer(reservedPort)
    bff = spawnOwned(env.KOKORO_W2_BFF_NODE_BIN, [join(BFF, "dist/main.js")], BFF, bffEnv, log.fd)
    const bffBase = candidateUrl
    await waitReady(bffBase, "BFF", bff)
    const db = new Pool({ connectionString: testUrl, max: 1 })
    try { cases = await runCases(bffBase, storageBase, config.publicEndpoint, identity, tokens, webSecret, storageSecret, db) }
    finally { await db.end() }
  } catch (error) { failure = error }
  try {
    const stopFailures = []
    try { await stopOwned(bff) } catch (error) { stopFailures.push(error) }
    try { await stopOwned(storage) } catch (error) { stopFailures.push(error) }
    try { if (iam) await closeServer(iam) } catch (error) { stopFailures.push(error) }
    if (stopFailures.length) throw new AggregateError(stopFailures, "one or more run-owned processes did not stop; retaining objects and database")
    processesStopped = true
    if (databaseCreated && !databaseCreateUncertain) {
      await cleanupObjects(s3, config.bucket, prefix)
      objectsClean = true
      await dropDatabase(admin, databaseName)
      databaseCreated = false
    }
  } catch (error) { cleanupFailure = error }
  finally {
    const closed = await Promise.allSettled([Promise.resolve().then(() => s3.destroy()), admin.end(), log.close()])
    if (closed.some(result => result.status === "rejected")) cleanupFailure ??= new SmokeError("owned SDK, PostgreSQL, or evidence handle close failed")
  }
  if (failure || cleanupFailure) {
    // Do not destroy diagnostics or drop an owned database when object identity/cleanup is uncertain.
    process.stderr.write(JSON.stringify({ result: "failed", sources, error: failure?.message ?? null, cleanup_error: cleanupFailure?.message ?? null, run_id: runId, database_candidate: databaseName, owned_database: databaseCreated ? databaseName : null, database_create_uncertain: databaseCreateUncertain, owned_prefix: prefix, bucket: config.bucket, processes_stopped: processesStopped, objects_clean: objectsClean, evidence_dir: directory, follow_up_owner: "Root W2 smoke" }) + "\n")
    process.exitCode = 1
  } else {
    process.stdout.write(JSON.stringify({ result: "passed", sources, cases, run_id: runId, owned_database_removed: true, owned_objects_removed: true }) + "\n")
    await rm(directory, { recursive: true, force: true })
  }
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url))
  main().catch(error => { process.stderr.write(JSON.stringify({ result: "failed", error: error.message }) + "\n"); process.exitCode = 1 })
