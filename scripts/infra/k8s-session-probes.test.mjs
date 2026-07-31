import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import test from "node:test";

const root = resolve(import.meta.dirname, "../..");

function deployment(source, name) {
  return source.split(/^---\s*$/mu).find((document) =>
    /^kind:\s*Deployment$/mu.test(document) &&
    new RegExp(String.raw`^metadata:\s*\{\s*name:\s*${name}\s*\}$`, "mu").test(document));
}

function service(source, name) {
  return source.split(/^---\s*$/mu).find((document) =>
    /^kind:\s*Service$/mu.test(document) &&
    new RegExp(String.raw`^metadata:\s*\{\s*name:\s*${name}\s*\}$`, "mu").test(document));
}

function block(source, key) {
  const lines = source.split("\n");
  const pattern = new RegExp(`^\\s+${key}:`, "u");
  const start = lines.findIndex((line) => pattern.test(line));
  assert.notEqual(start, -1, `missing ${key}`);
  if (lines[start].slice(lines[start].indexOf(":") + 1).trim().length > 0) return lines[start];
  const indentation = lines[start].search(/\S/u);
  const selected = [lines[start]];
  for (const line of lines.slice(start + 1)) {
    if (line.trim().length > 0 && line.search(/\S/u) <= indentation) break;
    selected.push(line);
  }
  return selected.join("\n");
}

test("Session probes use a dedicated Pod-only listener and preserve browser mTLS", async () => {
  const app = await readFile(resolve(root, "deploy/k8s/base/app.yaml"), "utf8");
  const session = deployment(app, "kokoro-session");
  const sessionService = service(app, "kokoro-session");
  assert(session);
  assert(sessionService);

  const env = block(session, "env");
  assert.match(env, /name:\s*KOKORO_SESSION_PROBE_HOST,\s*value:\s*"0\.0\.0\.0"/u);
  assert.match(env, /name:\s*KOKORO_SESSION_PROBE_PORT,\s*value:\s*"3902"/u);

  const ports = block(session, "ports");
  assert.match(ports, /name:\s*browser,\s*containerPort:\s*3900/u);
  assert.match(ports, /name:\s*owner-authority,\s*containerPort:\s*3901/u);
  assert.match(ports, /name:\s*probe,\s*containerPort:\s*3902/u);

  const readiness = block(session, "readinessProbe");
  assert.match(readiness, /httpGet:\s*\{\s*path:\s*\/readyz,\s*port:\s*probe\s*\}/u);
  assert.match(readiness, /timeoutSeconds:\s*3/u);
  assert.match(readiness, /periodSeconds:\s*5/u);
  assert.match(readiness, /failureThreshold:\s*3/u);
  assert.doesNotMatch(readiness, /tcpSocket|\/healthz/u);

  const liveness = block(session, "livenessProbe");
  assert.match(liveness, /httpGet:\s*\{\s*path:\s*\/healthz,\s*port:\s*probe\s*\}/u);
  assert.match(liveness, /timeoutSeconds:\s*2/u);
  assert.match(liveness, /periodSeconds:\s*10/u);
  assert.match(liveness, /failureThreshold:\s*3/u);
  assert.doesNotMatch(liveness, /tcpSocket|\/readyz/u);

  const startup = block(session, "startupProbe");
  assert.match(startup, /httpGet:\s*\{\s*path:\s*\/healthz,\s*port:\s*probe\s*\}/u);
  assert.match(startup, /timeoutSeconds:\s*2/u);
  assert.match(startup, /periodSeconds:\s*2/u);
  assert.match(startup, /failureThreshold:\s*30/u);
  assert.doesNotMatch(startup, /tcpSocket|\/readyz/u);

  assert.match(sessionService, /name:\s*browser,\s*port:\s*3900,\s*targetPort:\s*browser/u);
  assert.match(sessionService, /name:\s*owner-authority,\s*port:\s*3901,\s*targetPort:\s*owner-authority/u);
  assert.doesNotMatch(sessionService, /\bprobe\b|3902/u);
});

test("probe implementation is health-only while the browser listener remains mutual TLS", async () => {
  const [probeSource, browserSource, mainSource] = await Promise.all([
    readFile(resolve(root, "kokoro-session/src/browser/probe-server.ts"), "utf8"),
    readFile(resolve(root, "kokoro-session/src/browser/server.ts"), "utf8"),
    readFile(resolve(root, "kokoro-session/src/main.ts"), "utf8"),
  ]);

  assert.match(probeSource, /createServer/u);
  assert.match(probeSource, /pathname === "\/healthz"/u);
  assert.match(probeSource, /pathname === "\/readyz"/u);
  assert.match(probeSource, /status:\s*"not_found"/u);
  assert.match(probeSource, /status:\s*"method_not_allowed"/u);
  assert.doesNotMatch(probeSource, /browser\/routes|owner-authority|\/sessions|\/v3\//u);

  assert.match(mainSource, /ready:\s*\(\) => production\.runtime\.ready\(\)/u);
  assert.match(browserSource, /requestCert:\s*true/u);
  assert.match(browserSource, /rejectUnauthorized:\s*true/u);
  assert.match(browserSource, /minVersion:\s*"TLSv1\.3"/u);
  assert.match(browserSource, /maxVersion:\s*"TLSv1\.3"/u);
});

test("secure Connect probes remain TCP and documentation distinguishes both probe contracts", async () => {
  const [app, readme] = await Promise.all([
    readFile(resolve(root, "deploy/k8s/base/app.yaml"), "utf8"),
    readFile(resolve(root, "deploy/k8s/README.md"), "utf8"),
  ]);
  const evidence = deployment(app, "kokoro-agent-evidence");
  assert(evidence);
  const readiness = block(evidence, "readinessProbe");
  assert.match(readiness, /tcpSocket:\s*\{\s*port:\s*connect\s*\}/u);
  assert.doesNotMatch(readiness, /httpGet/u);

  assert.match(readme, /Session[^\n]*3902[^\n]*\/healthz[^\n]*\/readyz/iu);
  assert.match(readme, /3902[^\n]*Pod-only/iu);
  assert.match(readme, /3900[^\n]*mTLS/iu);
  assert.match(readme, /not[^\n]*Service/iu);
  assert.match(readme, /\/healthz[^\n]*process liveness/iu);
  assert.match(readme, /\/readyz[^\n]*(?:aggregated|dependency) readiness/iu);
  assert.match(readme, /secure Connect[^\n]*TCP readiness/iu);
  assert.match(readme, /TCP[^\n]*not[^\n]*semantic readiness/iu);
});
