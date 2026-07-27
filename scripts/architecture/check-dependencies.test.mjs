import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdtemp, mkdir, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

const checker = new URL("./check-dependencies.ts", import.meta.url);

function boundary(id, path, allow = []) {
  return {
    id,
    path,
    kind: "boundary",
    index: `${path}/INDEX.md`,
    owners: ["@owner"],
    boundary: id,
    language: "typescript",
    signals: [`${path}/INDEX.md`],
    dependencies: { allow },
    verification: [{ cwd: path, argv: ["node", "--version"] }],
  };
}

function component(id, path, ownerBoundary, allow = []) {
  return {
    ...boundary(id, path, allow),
    kind: "component",
    boundary: ownerBoundary,
  };
}

async function makeFixture(entries) {
  const root = await mkdtemp(join(tmpdir(), "kokoro-dependencies-"));
  const manifestPath = join(root, "index-roots.yaml");
  await writeFile(
    manifestPath,
    JSON.stringify({ schemaVersion: 1, owners: ["@owner"], roots: entries }, null, 2),
  );
  for (const entry of entries) await mkdir(join(root, entry.path), { recursive: true });
  return { root, manifestPath };
}

function run(root, manifestPath) {
  return spawnSync(process.execPath, [checker.pathname, "--root", root, "--manifest", manifestPath], {
    encoding: "utf8",
  });
}

async function writePackage(root, path, name, dependencies = {}) {
  await writeFile(join(root, path, "package.json"), JSON.stringify({ name, dependencies }, null, 2));
}

test("accepts exact directed dependencies declared by public boundary id", async () => {
  const fixture = await makeFixture([
    boundary("service.foundation", "foundation"),
    boundary("service.feature", "feature", ["service.foundation"]),
    component("feature.component", "feature/src/component", "service.feature", ["service.foundation"]),
  ]);
  await writePackage(fixture.root, "foundation", "@example/foundation");
  await writePackage(fixture.root, "feature", "@example/feature", {
    "@example/foundation": "workspace:*",
  });

  const result = run(fixture.root, fixture.manifestPath);

  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /Dependency boundaries OK \(3 roots, 1 internal package edge\)/);
});

test("rejects unknown, duplicate, self, and wildcard dependency exemptions", async () => {
  const fixture = await makeFixture([
    boundary("service.feature", "feature", [
      "service.missing",
      "service.feature",
      "service.*",
      "service.missing",
    ]),
  ]);

  const result = run(fixture.root, fixture.manifestPath);

  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /root service\.feature allows unknown dependency: service\.missing/);
  assert.match(result.stderr, /root service\.feature dependency must be an exact public boundary id: service\.\*/);
  assert.match(result.stderr, /root service\.feature cannot depend on itself/);
  assert.match(result.stderr, /root service\.feature has duplicate dependency: service\.missing/);
});

test("rejects reciprocal and transitive dependency cycles", async () => {
  const fixture = await makeFixture([
    boundary("service.a", "a", ["service.b"]),
    boundary("service.b", "b", ["service.c"]),
    boundary("service.c", "c", ["service.a"]),
  ]);

  const result = run(fixture.root, fixture.manifestPath);

  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /dependency cycle: service\.a -> service\.b -> service\.c -> service\.a/);
});

test("rejects non-canonical paths and components outside their owning boundary", async () => {
  const fixture = await makeFixture([
    boundary("service.a", "service-a"),
    component("service.a.component", "service-a/../service-b/component", "service.a"),
  ]);

  const result = run(fixture.root, fixture.manifestPath);

  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /root service\.a\.component path must be canonical repository-relative POSIX path/);
  assert.match(result.stderr, /component service\.a\.component must be nested inside boundary service\.a/);
});

test("rejects undeclared dependencies between registered workspace packages", async () => {
  const fixture = await makeFixture([
    boundary("service.foundation", "foundation"),
    boundary("service.feature", "feature"),
  ]);
  await writePackage(fixture.root, "foundation", "@example/foundation");
  await writePackage(fixture.root, "feature", "@example/feature", {
    "@example/foundation": "workspace:*",
  });

  const result = run(fixture.root, fixture.manifestPath);

  assert.notEqual(result.status, 0);
  assert.match(
    result.stderr,
    /feature\/package\.json: package @example\/feature depends on service\.foundation but service\.feature does not allow it/,
  );
});

test("rejects relative imports into another registered boundary's private source", async () => {
  const fixture = await makeFixture([
    boundary("service.a", "service-a", ["service.b"]),
    boundary("service.b", "service-b"),
  ]);
  await mkdir(join(fixture.root, "service-a/src"), { recursive: true });
  await mkdir(join(fixture.root, "service-b/src"), { recursive: true });
  await writeFile(
    join(fixture.root, "service-a/src/index.ts"),
    'import { privateValue } from "../../service-b/src/private.js";\n',
  );
  await writeFile(join(fixture.root, "service-b/src/private.ts"), "export const privateValue = 1;\n");

  const result = run(fixture.root, fixture.manifestPath);

  assert.notEqual(result.status, 0);
  assert.match(
    result.stderr,
    /service-a\/src\/index\.ts: cross-boundary source import service\.a -> service\.b: \.\.\/\.\.\/service-b\/src\/private\.js/,
  );
});

test("rejects sibling source paths hidden in project configuration", async () => {
  const fixture = await makeFixture([
    boundary("service.a", "service-a", ["service.b"]),
    boundary("service.b", "service-b"),
  ]);
  await writeFile(
    join(fixture.root, "service-a/tsconfig.json"),
    JSON.stringify({ compilerOptions: { paths: { "@private/*": ["../service-b/src/*"] } } }, null, 2),
  );

  const result = run(fixture.root, fixture.manifestPath);

  assert.notEqual(result.status, 0);
  assert.match(
    result.stderr,
    /service-a\/tsconfig\.json: cross-boundary source path service\.a -> service\.b: \.\.\/service-b\/src\/\*/,
  );
});

test("rejects sibling paths embedded in package scripts", async () => {
  const fixture = await makeFixture([
    boundary("service.a", "service-a", ["service.b"]),
    boundary("service.b", "service-b"),
  ]);
  await writeFile(
    join(fixture.root, "service-a/package.json"),
    JSON.stringify({ name: "service-a", scripts: { unsafe: "tsx ../service-b/src/private.ts" } }),
  );

  const result = run(fixture.root, fixture.manifestPath);

  assert.notEqual(result.status, 0);
  assert.match(
    result.stderr,
    /service-a\/package\.json: cross-boundary source path service\.a -> service\.b: \.\.\/service-b\/src\/private\.ts/,
  );
});
