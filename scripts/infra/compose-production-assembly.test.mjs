import assert from "node:assert/strict";
import { access, readFile } from "node:fs/promises";
import { resolve } from "node:path";
import test from "node:test";

const root = resolve(import.meta.dirname, "../..");

function composeService(source, name) {
  return `${source}\n  __end__:\n`.match(
    new RegExp(`^  ${name}:\\n([\\s\\S]*?)(?=^  [a-z0-9_][a-z0-9_-]*:\\n)`, "mu"),
  )?.[0];
}

function selectedPackages(source) {
  return new Set([
    ...source.matchAll(/KOKORO_SERVICE_PACKAGE\s*:\s*["']?([^"'\s},]+)["']?/gu),
  ].map((match) => match[1]));
}

test("Compose selects every current Platform deployable and no retired package", async () => {
  const [deployables, entrypoint, compose] = await Promise.all([
    readFile(resolve(root, "kokoro-platform/deployables.yaml"), "utf8"),
    readFile(resolve(root, "kokoro-platform/deploy/docker/runtime-entrypoint.mjs"), "utf8"),
    readFile(resolve(root, "docker-compose.app.yml"), "utf8"),
  ]);
  const expected = new Set([
    ...deployables.matchAll(/selectorEnvironment:\s*KOKORO_SERVICE_PACKAGE=([^\s]+)/gu),
  ].map((match) => match[1]));
  expected.add("@kokoro/hub");
  const runtimeEntries = new Set([
    ...entrypoint.matchAll(/^\s{2}"([^"]+)":\s*\{/gmu),
  ].map((match) => match[1]));
  for (const selector of expected) assert(runtimeEntries.has(selector), selector);
  assert.deepEqual([...selectedPackages(compose)].sort(), [...expected].sort());
  assert.doesNotMatch(
    compose,
    /@kokoro\/(?:site|user|model|credit|payment|platform-admin)(?:["'\s},]|$)/u,
  );
});

test("Compose exposes every independent network process on its source-owned port", async () => {
  const compose = await readFile(resolve(root, "docker-compose.app.yml"), "utf8");
  for (const [service, port] of [
    ["platform-api", 4100],
    ["platform-admin", 4101],
    ["platform-authorization", 4143],
    ["platform-admission", 4244],
    ["platform-asset-data-plane", 4246],
    ["platform-model-gateway", 4247],
    ["kokoro-hub", 4251],
    ["kokoro-hub-runtime", 4252],
    ["kokoro-session", 3900],
    ["kokoro-session", 3901],
    ["kokoro-agent-evidence", 8443],
    ["kokoro-site-release", 3000],
  ]) {
    assert.match(
      composeService(compose, service),
      new RegExp(`(?:^|[^0-9])${port}(?:[^0-9]|$)`, "u"),
      `${service}:${port}`,
    );
  }
  assert(composeService(compose, "platform-worker"));
  assert(composeService(compose, "kokoro-agent-worker"));
  assert.match(composeService(compose, "kokoro-agent-evidence"), /kokoro-agent-evidence/u);
});

test("Compose builds real backend Dockerfiles and consumes an independent Site release image", async () => {
  const compose = await readFile(resolve(root, "docker-compose.app.yml"), "utf8");
  for (const [context, dockerfile] of [
    ["kokoro-platform", "deploy/docker/Dockerfile"],
    ["kokoro-session", "Dockerfile"],
    ["kokoro-agent", "Dockerfile"],
  ]) {
    await access(resolve(root, context, dockerfile));
    assert.match(compose, new RegExp(`context:\\s*\\.?/${context}`, "u"));
  }
  const site = composeService(compose, "kokoro-site-release");
  assert.match(site, /image:\s*\$\{KOKORO_SITE_IMAGE/u);
  assert.doesNotMatch(site, /build:/u);
  await access(resolve(root, "kokoro-web/packages/site-scaffold/templates/site/Dockerfile"));
  assert.doesNotMatch(compose, /apps\/user\/Dockerfile/u);
});

test("Compose mounts file credentials into each owning process only", async () => {
  const compose = await readFile(resolve(root, "docker-compose.app.yml"), "utf8");
  for (const name of [
    "platform-api",
    "platform-admission",
    "platform-authorization",
    "platform-asset-data-plane",
    "platform-model-gateway",
    "platform-worker",
    "platform-admin",
    "kokoro-hub",
    "kokoro-hub-runtime",
    "kokoro-session",
    "kokoro-agent-worker",
    "kokoro-agent-evidence",
    "kokoro-site-release",
  ]) {
    assert.match(composeService(compose, name), /:\/run\/secrets\/kokoro:ro/u, name);
  }
});

test("fresh installs expose an explicit sealed Admin authority bootstrap job", async () => {
  const [compose, provision, kubernetes] = await Promise.all([
    readFile(resolve(root, "docker-compose.app.yml"), "utf8"),
    readFile(resolve(root, "deploy/provision.sh"), "utf8"),
    readFile(resolve(root, "deploy/k8s/bootstrap/admin-authority-job.yaml"), "utf8"),
  ]);
  const service = composeService(compose, "platform-admin-bootstrap");
  assert.match(service, /dist\/src\/process\/admin-authority-bootstrap\.js/u);
  assert.match(service, /PLATFORM_DATABASE_CREDENTIAL_CLASS:\s*migrator/u);
  assert.match(service, /admin-authority-bootstrap\.json[^\n]*:\/run\/secrets\/kokoro\/admin-authority-bootstrap\.json:ro/u);
  assert.match(provision, /KOKORO_ADMIN_AUTHORITY_BOOTSTRAP_FILE/u);
  assert.match(provision, /run --rm --no-deps platform-admin-bootstrap/u);
  assert.match(kubernetes, /kind:\s*Job/u);
  assert.match(kubernetes, /admin-authority-bootstrap\.js/u);
  assert.doesNotMatch(kubernetes, /stringData:|bootstrap_admin_authorities/u);
});
