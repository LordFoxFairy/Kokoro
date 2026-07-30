import assert from "node:assert/strict";
import { access, readFile } from "node:fs/promises";
import { resolve } from "node:path";
import test from "node:test";

const root = resolve(import.meta.dirname, "../..");

const retiredSelectors = Object.freeze([
  "@kokoro/site",
  "@kokoro/user",
  "@kokoro/model",
  "@kokoro/credit",
  "@kokoro/payment",
  "@kokoro/platform-admin",
]);

const networkProcesses = Object.freeze([
  { service: "platform-api", port: 4100, source: "kokoro-platform/src/process/api.ts", marker: '"4100"' },
  { service: "platform-admin", port: 4101, source: "kokoro-platform/src/process/admin.ts", marker: '"4101"' },
  {
    service: "platform-authorization",
    port: 4143,
    source: "kokoro-platform/src/process/authorization.ts",
    marker: '"4143"',
  },
  {
    service: "platform-admission",
    port: 4244,
    source: "kokoro-platform/src/process/admission.ts",
    marker: '"4244"',
  },
  {
    service: "platform-asset-data-plane",
    port: 4246,
    source: "kokoro-platform/src/process/asset-data-plane.ts",
    marker: '"4246"',
  },
  {
    service: "platform-model-gateway",
    port: 4247,
    source: "kokoro-platform/src/process/model-gateway.ts",
    marker: '"4247"',
  },
  {
    service: "kokoro-hub",
    port: 4251,
    source: "kokoro-platform/kokoro-hub/src/config/env.ts",
    marker: "default(4251)",
  },
  {
    service: "kokoro-hub-runtime",
    port: 4252,
    source: "kokoro-platform/kokoro-hub/src/interfaces/connect/main.ts",
    marker: '"4252"',
  },
  {
    service: "kokoro-session",
    port: 3900,
    source: "kokoro-session/Dockerfile",
    marker: "KOKORO_SESSION_PORT=3900",
  },
  {
    service: "kokoro-session",
    port: 3901,
    source: "kokoro-session/src/main.ts",
    marker: "catch(3901)",
  },
  {
    service: "kokoro-agent-evidence",
    port: 8443,
    source: "kokoro-agent/src/kokoro_agent/config.py",
    marker: "default=8443",
  },
  {
    service: "kokoro-site-release",
    port: 3000,
    source: "kokoro-web/packages/site-scaffold/templates/site/deploy/site-deployment.json",
    marker: '"port": 3000',
  },
]);

function yamlDocuments(source) {
  return source.split(/^---\s*$/mu).map((document) => document.trim()).filter(Boolean);
}

function workloadDocument(source, kind, name) {
  return yamlDocuments(source).find((document) =>
    new RegExp(`^kind:\\s*${kind}$`, "mu").test(document) &&
    new RegExp(`^metadata:(?:\\s*\\{\\s*name:\\s*${name}(?:[,}\\s])|\\s*\\n\\s+name:\\s*${name}\\s*$)`, "mu")
      .test(document));
}

function composeService(source, name) {
  return `${source}\n  __end__:\n`.match(
    new RegExp(`^  ${name}:\\n([\\s\\S]*?)(?=^  [a-z0-9_][a-z0-9_-]*:\\n)`, "mu"),
  )?.[0];
}

function selectedPackages(...sources) {
  return new Set(sources.flatMap((source) => [
    ...source.matchAll(/KOKORO_SERVICE_PACKAGE(?:\s*:\s*|,\s*value:\s*)["']?([^"'\s},]+)["']?/gu),
  ].map((match) => match[1])));
}

test("Compose and Kubernetes select every current Platform deployable and no retired package", async () => {
  const [deployables, entrypoint, compose, platform, jobs] = await Promise.all([
    readFile(resolve(root, "kokoro-platform/deployables.yaml"), "utf8"),
    readFile(resolve(root, "kokoro-platform/deploy/docker/runtime-entrypoint.mjs"), "utf8"),
    readFile(resolve(root, "docker-compose.app.yml"), "utf8"),
    readFile(resolve(root, "deploy/k8s/base/platform.yaml"), "utf8"),
    readFile(resolve(root, "deploy/k8s/base/jobs.yaml"), "utf8"),
  ]);
  const expected = new Set([
    ...deployables.matchAll(/selectorEnvironment:\s*KOKORO_SERVICE_PACKAGE=([^\s]+)/gu),
  ].map((match) => match[1]));
  expected.add("@kokoro/hub");

  const runtimeEntries = new Set([
    ...entrypoint.matchAll(/^\s{2}"([^"]+)":\s*\{/gmu),
  ].map((match) => match[1]));
  for (const selector of expected) {
    assert(runtimeEntries.has(selector), `${selector} must resolve through the immutable Platform entrypoint`);
  }
  assert.deepEqual([...selectedPackages(compose)].sort(), [...expected].sort());
  assert.deepEqual([...selectedPackages(platform, jobs)].sort(), [...expected].sort());
  for (const selector of retiredSelectors) {
    assert.doesNotMatch(compose, new RegExp(selector.replaceAll("/", "\\/"), "u"));
    assert.doesNotMatch(`${platform}\n${jobs}`, new RegExp(selector.replaceAll("/", "\\/"), "u"));
  }
});

test("production manifests contain the independent runtime processes and their real ports", async () => {
  const [compose, platform, app] = await Promise.all([
    readFile(resolve(root, "docker-compose.app.yml"), "utf8"),
    readFile(resolve(root, "deploy/k8s/base/platform.yaml"), "utf8"),
    readFile(resolve(root, "deploy/k8s/base/app.yaml"), "utf8"),
  ]);
  const kubernetes = `${platform}\n---\n${app}`;

  for (const process of networkProcesses) {
    const source = await readFile(resolve(root, process.source), "utf8");
    assert(source.includes(process.marker), `${process.source} must still own port ${process.port}`);

    const composeDefinition = composeService(compose, process.service);
    assert(composeDefinition, `Compose is missing ${process.service}`);
    assert.match(composeDefinition, new RegExp(`(?:^|[^0-9])${process.port}(?:[^0-9]|$)`, "u"));

    const deployment = workloadDocument(kubernetes, "Deployment", process.service);
    assert(deployment, `Kubernetes is missing Deployment/${process.service}`);
    assert.match(deployment, new RegExp(`containerPort:\\s*${process.port}(?:[^0-9]|$)`, "u"));

    const service = workloadDocument(kubernetes, "Service", process.service);
    assert(service, `Kubernetes is missing Service/${process.service}`);
    assert.match(service, new RegExp(`(?:port|targetPort):\\s*${process.port}(?:[^0-9]|$)`, "u"));
  }

  for (const name of ["platform-worker", "kokoro-agent-worker"]) {
    assert(composeService(compose, name), `Compose is missing ${name}`);
    assert(workloadDocument(kubernetes, "Deployment", name), `Kubernetes is missing Deployment/${name}`);
  }
  assert.match(composeService(compose, "kokoro-agent-evidence"), /kokoro-agent-evidence/u);
  assert.match(
    workloadDocument(app, "Deployment", "kokoro-agent-evidence"),
    /kokoro-agent-evidence/u,
  );
});

test("Root builds only real backend Dockerfiles and consumes Site as an independent release image", async () => {
  const compose = await readFile(resolve(root, "docker-compose.app.yml"), "utf8");
  const buildTargets = [
    { context: "kokoro-platform", dockerfile: "deploy/docker/Dockerfile" },
    { context: "kokoro-session", dockerfile: "Dockerfile" },
    { context: "kokoro-agent", dockerfile: "Dockerfile" },
  ];
  for (const target of buildTargets) {
    await access(resolve(root, target.context, target.dockerfile));
    assert.match(compose, new RegExp(`context:\\s*\\.?/${target.context}`, "u"));
    if (target.dockerfile !== "Dockerfile") {
      assert.match(compose, new RegExp(`dockerfile:\\s*${target.dockerfile.replaceAll("/", "\\/")}`, "u"));
    }
  }

  const site = composeService(compose, "kokoro-site-release");
  assert(site);
  assert.match(site, /image:\s*\$\{KOKORO_SITE_IMAGE/u);
  assert.doesNotMatch(site, /build:/u);
  await access(resolve(root, "kokoro-web/packages/site-scaffold/templates/site/Dockerfile"));
  assert.match(
    await readFile(resolve(root, "kokoro-web/packages/site-scaffold/templates/site/Dockerfile"), "utf8"),
    /CMD \["node", "server\.js"\]/u,
  );
  assert.doesNotMatch(compose, /apps\/user\/Dockerfile/u);
});

test("file-backed credentials are mounted only into their owning runtime process", async () => {
  const [compose, platform, app] = await Promise.all([
    readFile(resolve(root, "docker-compose.app.yml"), "utf8"),
    readFile(resolve(root, "deploy/k8s/base/platform.yaml"), "utf8"),
    readFile(resolve(root, "deploy/k8s/base/app.yaml"), "utf8"),
  ]);
  const kubernetes = `${platform}\n---\n${app}`;
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
    assert.match(composeService(compose, name), /:\/run\/secrets\/kokoro:ro/u, `${name} Compose secret mount`);
    assert.match(
      workloadDocument(kubernetes, "Deployment", name),
      /mountPath:\s*\/run\/secrets\/kokoro[\s\S]*secretName:/u,
      `${name} Kubernetes secret mount`,
    );
  }
});

test("Kubernetes defaults to the current PostgreSQL authority and has no retired seed job", async () => {
  const [infra, jobs] = await Promise.all([
    readFile(resolve(root, "deploy/k8s/base/infra.yaml"), "utf8"),
    readFile(resolve(root, "deploy/k8s/base/jobs.yaml"), "utf8"),
  ]);
  assert(workloadDocument(infra, "Deployment", "postgres"));
  assert(workloadDocument(infra, "Service", "postgres"));
  assert.equal(workloadDocument(infra, "Deployment", "mysql"), undefined);
  assert.equal(workloadDocument(infra, "Service", "mysql"), undefined);
  assert(workloadDocument(jobs, "Job", "platform-migrator"));
  assert.equal(workloadDocument(jobs, "Job", "provision"), undefined);
  assert.doesNotMatch(jobs, /seed:|db:seed|@kokoro\/(?:site|model|credit|payment|platform-admin)/u);
});

test("operator entrypoints describe only latest runtime and typed bootstrap paths", async () => {
  const sources = await Promise.all([
    readFile(resolve(root, "deploy/provision.sh"), "utf8"),
    readFile(resolve(root, "deploy/.env.example"), "utf8"),
    readFile(resolve(root, "deploy/README.md"), "utf8"),
    readFile(resolve(root, "deploy/k8s/README.md"), "utf8"),
  ]);
  const combined = sources.join("\n");
  assert.doesNotMatch(combined, /@kokoro\/(?:site|user|model|credit|payment|platform-admin)/u);
  assert.doesNotMatch(combined, /DATABASE_URL_(?:SITE|USER|MODEL|CREDIT|PAYMENT|ADMIN)=mysql:/u);
  assert.doesNotMatch(combined, /(?:seed:builtin|seed:site|seed:pricing|seed:packs|db:seed)/u);
  assert.match(combined, /typed control-plane/u);
  assert.match(combined, /independent Site/u);
});
