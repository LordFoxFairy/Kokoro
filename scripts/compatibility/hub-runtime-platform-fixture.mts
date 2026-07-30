#!/usr/bin/env node

import { AsyncLocalStorage } from "node:async_hooks";
import { createRequire } from "node:module";
import { createSecureServer } from "node:http2";
import { readFile } from "node:fs/promises";
import { createHash, X509Certificate } from "node:crypto";
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { TLSSocket } from "node:tls";

import { createEd25519CapabilityPublicationVerifier } from
  "../../kokoro-platform/src/modules/admission/infrastructure/crypto/capability-publication-verifier.js";
import { createCapabilityCatalogProjectionConnectService } from
  "../../kokoro-platform/src/modules/admission/interfaces/connect/capability-catalog-projection-service.js";
import {
  CapabilityCatalogProjectionService,
  CatalogProjectionState,
  FreezeCatalogEffectSchema,
  HubCatalogService,
} from
  "../../kokoro-platform/kokoro-hub/src/interfaces/connect/generated-capability-catalog/kokoro/platform/capability/v1/capability_catalog_pb.js";
import { CommandDigestAlgorithm } from
  "../../kokoro-platform/kokoro-hub/src/interfaces/connect/generated-capability-catalog/kokoro/common/v1/receipt_pb.js";
import { freezeCatalogRequestDigest } from
  "../../kokoro-platform/kokoro-hub/src/interfaces/connect/capability-catalog-services.js";
import { contentHashOf } from
  "../../kokoro-platform/kokoro-hub/src/domain/package.js";
import { zipTextFiles } from
  "../../kokoro-platform/kokoro-hub/src/infrastructure/zip.js";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const platformRequire = createRequire(resolve(root, "kokoro-platform/package.json"));
const connect = await import(pathToFileURL(platformRequire.resolve("@connectrpc/connect")).href);
const connectNode = await import(pathToFileURL(platformRequire.resolve("@connectrpc/connect-node")).href);
const { create } = await import(pathToFileURL(platformRequire.resolve("@bufbuild/protobuf")).href);

const NAMESPACE = "namespace-hub-compatibility";
const SITE_ID = "site-hub-compatibility";
const RELEASE_REF = "site-release:hub-compatibility";
const SKILL_NAME = "compat-skill";
const SKILL_DESCRIPTION = "Compatibility skill";
const SKILL_OPTION_REF = "skill:compat-skill";
const SKILL_BODY = `---\nname: ${SKILL_NAME}\ndescription: ${SKILL_DESCRIPTION}\n---\n# Compatibility\n\nExact Hub artifact.\n`;

type ProjectionRecord = Readonly<{
  callerIdentity: string;
  commandId: string;
  idempotencyKey: string;
  requestDigest: string;
  siteId: string;
  agentCatalogRef: string;
  recordedAt: string;
}>;

function argumentsOf(argv: string[]): { mode: string; values: Map<string, string> } {
  const [mode, ...rest] = argv;
  if (!mode || rest.length % 2 !== 0) throw new Error("hub_runtime_fixture_arguments");
  const values = new Map<string, string>();
  for (let index = 0; index < rest.length; index += 2) {
    const name = rest[index];
    const value = rest[index + 1];
    if (!name?.startsWith("--") || !value || values.has(name)) {
      throw new Error("hub_runtime_fixture_arguments");
    }
    values.set(name, value);
  }
  return { mode, values };
}

function required(values: Map<string, string>, name: string): string {
  const value = values.get(name);
  if (!value) throw new Error(`hub_runtime_fixture_argument_missing:${name}`);
  return value;
}

async function projection(values: Map<string, string>): Promise<void> {
  const port = Number(required(values, "--port"));
  const hubIdentity = required(values, "--hub-identity");
  const signingKeyRef = required(values, "--signing-key-ref");
  const [key, cert, ca, hubCert, publicKey] = await Promise.all([
    readFile(required(values, "--tls-key"), "utf8"),
    readFile(required(values, "--tls-cert"), "utf8"),
    readFile(required(values, "--client-ca"), "utf8"),
    readFile(required(values, "--hub-cert"), "utf8"),
    readFile(required(values, "--public-key"), "utf8"),
  ]);
  const expected = new X509Certificate(hubCert);
  const callers = new AsyncLocalStorage<Readonly<{ identity: string }>>();
  const records = new Map<string, ProjectionRecord>();
  const repository = {
    project: async (input: Readonly<{
      callerIdentity: string;
      commandId: string;
      idempotencyKey: string;
      requestDigest: string;
      publication: Readonly<{ siteId: string; agentCatalogRef: string }>;
    }>) => {
      const key = `${input.commandId}\0${input.idempotencyKey}`;
      const existing = records.get(key);
      if (existing !== undefined) {
        if (existing.requestDigest !== input.requestDigest ||
            existing.agentCatalogRef !== input.publication.agentCatalogRef) {
          throw new Error("CAPABILITY_PROJECTION_CONFLICT");
        }
        return { agentCatalogRef: existing.agentCatalogRef, recordedAt: existing.recordedAt, replayed: true };
      }
      const record = Object.freeze({
        callerIdentity: input.callerIdentity,
        commandId: input.commandId,
        idempotencyKey: input.idempotencyKey,
        requestDigest: input.requestDigest,
        siteId: input.publication.siteId,
        agentCatalogRef: input.publication.agentCatalogRef,
        recordedAt: new Date().toISOString(),
      });
      records.set(key, record);
      return { agentCatalogRef: record.agentCatalogRef, recordedAt: record.recordedAt, replayed: false };
    },
    lookup: async (input: Readonly<{
      callerIdentity: string;
      commandId: string;
      idempotencyKey: string;
      requestDigest: string;
      siteId: string;
    }>) => {
      const record = records.get(`${input.commandId}\0${input.idempotencyKey}`);
      if (record === undefined || record.callerIdentity !== input.callerIdentity ||
          record.requestDigest !== input.requestDigest || record.siteId !== input.siteId) return null;
      return { agentCatalogRef: record.agentCatalogRef, recordedAt: record.recordedAt };
    },
  };
  const service = createCapabilityCatalogProjectionConnectService({
    repository,
    verifyPublication: createEd25519CapabilityPublicationVerifier({
      keys: new Map([[signingKeyRef, publicKey]]),
    }),
    caller: { resolve: () => {
      const caller = callers.getStore();
      if (caller === undefined) throw new Error("ADMISSION_VERIFIED_CALLER_REQUIRED");
      return caller;
    } },
    hubCallerIdentity: hubIdentity,
  });
  const adapter = connectNode.connectNodeAdapter({
    routes: (router: { service: (definition: unknown, implementation: unknown) => void }) => {
      router.service(CapabilityCatalogProjectionService, service);
    },
    connect: true,
    grpc: false,
    grpcWeb: false,
    acceptCompression: [],
    readMaxBytes: 2 * 1024 * 1024,
    writeMaxBytes: 2 * 1024 * 1024,
    maxTimeoutMs: 5_000,
  });
  const server = createSecureServer({
    key,
    cert,
    ca,
    requestCert: true,
    rejectUnauthorized: true,
    allowHTTP1: false,
    minVersion: "TLSv1.3",
  }, (request, response) => {
    if (request.method === "GET" && request.url === "/health/ready") {
      response.statusCode = 200;
      response.end('{"status":"ready"}');
      return;
    }
    const socket = request.socket;
    if (!(socket instanceof TLSSocket) || !socket.authorized) {
      response.statusCode = 401;
      response.end("unauthorized");
      return;
    }
    const peer = socket.getPeerCertificate();
    const san = peer.subjectaltname?.split(/,\s*/u) ?? [];
    if (peer.fingerprint256 !== expected.fingerprint256 || !san.includes(`URI:${hubIdentity}`)) {
      response.statusCode = 403;
      response.end("forbidden");
      return;
    }
    callers.run({ identity: hubIdentity }, () => {
      Promise.resolve(adapter(request, response)).catch(() => {
        if (!response.headersSent) response.statusCode = 503;
        response.end("unavailable");
      });
    });
  });
  const stop = () => server.close(() => process.exit(0));
  process.once("SIGINT", stop);
  process.once("SIGTERM", stop);
  await new Promise<void>((ready, failed) => {
    server.once("error", failed);
    server.listen(port, "127.0.0.1", () => ready());
  });
}

async function publish(values: Map<string, string>): Promise<void> {
  const httpUrl = required(values, "--http-url");
  const hubUrl = required(values, "--hub-url");
  const serverName = required(values, "--server-name");
  const adminSecret = required(values, "--admin-secret");
  const ca = await readFile(required(values, "--ca"), "utf8");
  const cert = await readFile(required(values, "--cert"), "utf8");
  const key = await readFile(required(values, "--key"), "utf8");
  const files = { "SKILL.md": SKILL_BODY };
  const contentHash = contentHashOf(files);
  const archive = zipTextFiles({ [`${SKILL_NAME}/SKILL.md`]: SKILL_BODY });
  const uploaded = await fetch(`${httpUrl}/hub/admin/skills/upload/confirm`, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      "x-kokoro-service": "admin",
      "x-kokoro-internal-secret": adminSecret,
    },
    body: JSON.stringify({ namespace: NAMESPACE, zip_base64: archive.toString("base64") }),
    signal: AbortSignal.timeout(10_000),
  });
  if (uploaded.status !== 200) throw new Error("hub_runtime_upload_failed");
  const uploadBody = await uploaded.json() as {
    data?: { results?: Array<{ name?: string; status?: string; content_hash?: string }> };
  };
  const result = uploadBody.data?.results?.[0];
  if (result?.name !== SKILL_NAME || !["published", "unchanged"].includes(result.status ?? "") ||
      result.content_hash !== contentHash) throw new Error("hub_runtime_upload_invalid");

  const transport = connectNode.createConnectTransport({
    baseUrl: hubUrl,
    httpVersion: "2",
    useBinaryFormat: true,
    defaultTimeoutMs: 5_000,
    readMaxBytes: 2 * 1024 * 1024,
    writeMaxBytes: 2 * 1024 * 1024,
    acceptCompression: [],
    nodeOptions: {
      ca,
      cert,
      key,
      servername: serverName,
      rejectUnauthorized: true,
      minVersion: "TLSv1.3",
    },
  });
  const client = connect.createClient(HubCatalogService, transport);
  const effect = create(FreezeCatalogEffectSchema, {
    siteId: SITE_ID,
    siteReleaseRef: RELEASE_REF,
    snapshot: {
      schemaVersion: 1,
      agentOptions: [],
      tools: [],
      skillOptions: [{
        optionRef: SKILL_OPTION_REF,
        label: "Compatibility",
        scope: NAMESPACE,
        name: SKILL_NAME,
        contentHash,
        description: SKILL_DESCRIPTION,
      }],
      mcpOptions: [],
      subagents: [],
    },
  });
  const requestDigest = freezeCatalogRequestDigest(effect);
  const command = {
    commandId: "hub-compatibility-freeze",
    idempotencyKey: RELEASE_REF,
    digestAlgorithm: CommandDigestAlgorithm.SHA256_PROTOBUF_V1,
    requestDigest,
  };
  const frozen = await client.freezeCatalog({ command, effect });
  const agentCatalogRef = frozen.publication?.agentCatalogRef;
  if (!agentCatalogRef) throw new Error("hub_runtime_freeze_invalid");
  const deadline = Date.now() + 15_000;
  let projectionState = frozen.projectionState;
  while (projectionState !== CatalogProjectionState.COMMITTED && Date.now() < deadline) {
    await new Promise((done) => setTimeout(done, 100));
    const current = await client.getCatalogPublication({
      commandId: command.commandId,
      idempotencyKey: command.idempotencyKey,
      digestAlgorithm: command.digestAlgorithm,
      requestDigest,
      siteId: SITE_ID,
      siteReleaseRef: RELEASE_REF,
    });
    if (current.publication?.agentCatalogRef !== agentCatalogRef) {
      throw new Error("hub_runtime_publication_changed");
    }
    projectionState = current.projectionState;
  }
  if (projectionState !== CatalogProjectionState.COMMITTED) {
    throw new Error("hub_runtime_projection_not_committed");
  }
  process.stdout.write(`${JSON.stringify({
    namespace: NAMESPACE,
    agentCatalogRef,
    projectionState: "committed",
    expectedBodySha256: createHash("sha256").update(SKILL_BODY, "utf8").digest("hex"),
    skill: {
      option_ref: SKILL_OPTION_REF,
      name: SKILL_NAME,
      content_hash: contentHash,
      description: SKILL_DESCRIPTION,
      scope: NAMESPACE,
    },
  })}\n`);
}

const parsed = argumentsOf(process.argv.slice(2));
if (parsed.mode === "projection") await projection(parsed.values);
else if (parsed.mode === "publish") await publish(parsed.values);
else throw new Error("hub_runtime_fixture_mode_invalid");
