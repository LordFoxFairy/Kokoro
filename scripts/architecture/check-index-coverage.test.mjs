import assert from "node:assert/strict";
import { mkdtemp, mkdir, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { spawnSync } from "node:child_process";
import test from "node:test";

const checker = new URL("./check-index-coverage.ts", import.meta.url);

const requiredSections = [
  "Responsibilities",
  "Non-responsibilities",
  "Public boundary",
  "Callers and dependencies",
  "Data ownership and events",
  "Runtime and security",
  "Idempotency, failure, and recovery",
  "Extension rules and forbidden dependencies",
  "Current gotchas",
  "Verification",
];

async function writeIndex(root, relativePath, rootId = "root.example") {
  const path = join(root, relativePath);
  await mkdir(join(path, ".."), { recursive: true });
  const sections = requiredSections.map((section) => `## ${section}\n\nCurrent fact.\n`).join("\n");
  await writeFile(
    path,
    `---\narchitectureIndex: 1\nrootId: ${rootId}\nowners:\n  - "@owner"\n---\n\n# Example\n\n${sections}`,
  );
}

async function makeFixture(entries) {
  const root = await mkdtemp(join(tmpdir(), "kokoro-index-"));
  const manifestPath = join(root, "index-roots.yaml");
  await writeFile(
    manifestPath,
    JSON.stringify({ schemaVersion: 1, owners: ["@owner"], roots: entries }, null, 2),
  );
  return { root, manifestPath };
}

function run(root, manifestPath) {
  return spawnSync(process.execPath, [checker.pathname, "--root", root, "--manifest", manifestPath], {
    encoding: "utf8",
  });
}

function entry(overrides = {}) {
  return {
    id: "root.example",
    path: ".",
    kind: "boundary",
    index: "INDEX.md",
    owners: ["@owner"],
    boundary: "root.example",
    language: "mixed",
    signals: ["INDEX.md"],
    dependencies: { allow: [] },
    verification: [{ cwd: ".", argv: ["node", "--version"] }],
    ...overrides,
  };
}

test("accepts a complete current-fact architecture index", async () => {
  const fixture = await makeFixture([entry()]);
  await writeIndex(fixture.root, "INDEX.md");

  const result = run(fixture.root, fixture.manifestPath);

  assert.equal(result.status, 0, result.stderr);
});

test("rejects duplicate root ids and paths", async () => {
  const fixture = await makeFixture([
    entry(),
    entry({ index: "SECOND.md" }),
  ]);
  await writeIndex(fixture.root, "INDEX.md");
  await writeIndex(fixture.root, "SECOND.md");

  const result = run(fixture.root, fixture.manifestPath);

  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /duplicate root id: root\.example/);
  assert.match(result.stderr, /duplicate root path: \./);
});

test("rejects an existing unregistered INDEX", async () => {
  const fixture = await makeFixture([entry()]);
  await writeIndex(fixture.root, "INDEX.md");
  await writeIndex(fixture.root, "src/INDEX.md", "component.src");

  const result = run(fixture.root, fixture.manifestPath);

  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /unregistered INDEX: src\/INDEX\.md/);
});

test("rejects frontmatter drift, missing sections, and broken relative links", async () => {
  const fixture = await makeFixture([entry()]);
  await writeFile(
    join(fixture.root, "INDEX.md"),
    "---\narchitectureIndex: 1\nrootId: wrong.id\nowners:\n  - \"@other\"\n---\n\n# Example\n\n[missing](missing.md)\n",
  );

  const result = run(fixture.root, fixture.manifestPath);

  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /frontmatter rootId must equal root\.example/);
  assert.match(result.stderr, /frontmatter owners must equal manifest owners/);
  assert.match(result.stderr, /missing required section: Responsibilities/);
  assert.match(result.stderr, /broken relative link: missing\.md/);
});

test("rejects unregistered package and process boundaries", async () => {
  const fixture = await makeFixture([entry()]);
  await writeIndex(fixture.root, "INDEX.md");
  await mkdir(join(fixture.root, "service"), { recursive: true });
  await writeFile(join(fixture.root, "service/package.json"), '{"name":"service"}\n');
  await writeFile(join(fixture.root, "service/Dockerfile"), "FROM scratch\n");

  const result = run(fixture.root, fixture.manifestPath);

  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /unregistered boundary: service/);
});

test("ignores documentation templates and generated package artifacts", async () => {
  const fixture = await makeFixture([entry()]);
  await writeIndex(fixture.root, "INDEX.md");
  await writeIndex(fixture.root, "docs/templates/INDEX.md", "replace.with.stable.id");
  await mkdir(join(fixture.root, "service/generated/prisma"), { recursive: true });
  await writeFile(join(fixture.root, "service/generated/prisma/package.json"), '{"name":"generated"}\n');

  const result = run(fixture.root, fixture.manifestPath);

  assert.equal(result.status, 0, result.stderr);
});

test("component indexes inherit full boundary policy without duplicating every section", async () => {
  const fixture = await makeFixture([
    entry(),
    entry({
      id: "component.example",
      path: "src/component",
      kind: "component",
      index: "src/component/INDEX.md",
      boundary: "root.example",
      signals: ["src/component/INDEX.md"],
    }),
  ]);
  await writeIndex(fixture.root, "INDEX.md");
  await mkdir(join(fixture.root, "src/component"), { recursive: true });
  await writeFile(
    join(fixture.root, "src/component/INDEX.md"),
    '---\narchitectureIndex: 1\nrootId: component.example\nowners:\n  - "@owner"\n---\n\n# Component\n\nLocal current facts.\n',
  );

  const result = run(fixture.root, fixture.manifestPath);

  assert.equal(result.status, 0, result.stderr);
});
