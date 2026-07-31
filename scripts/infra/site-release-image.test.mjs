import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { chmod, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { delimiter, resolve } from "node:path";
import test from "node:test";

import { validateSiteReleaseImageReference } from "./site-release-image.mjs";

const root = resolve(import.meta.dirname, "../..");
const digest = "a".repeat(64);

test("accepts canonical digest-pinned Site images, including private registry ports", () => {
  for (const reference of [
    `registry.example/kokoro/product-site@sha256:${digest}`,
    `registry.example:5000/team/product_site@sha256:${"0".repeat(64)}`,
    `localhost:443/product/site.web@sha256:${"f".repeat(64)}`,
  ]) {
    assert.equal(validateSiteReleaseImageReference(reference), reference);
  }
});

test("rejects non-canonical, mutable, and ambiguous Site image references", () => {
  const invalidReferences = [
    undefined,
    "",
    "   ",
    "product-site:latest",
    "registry.example/kokoro/product-site:latest",
    `product-site@sha256:${digest}`,
    `registry.example/kokoro/Product-site@sha256:${digest}`,
    `Registry.example/kokoro/product-site@sha256:${digest}`,
    `registry.example/kokoro/product-site@sha256:${"A".repeat(64)}`,
    `registry.example/kokoro/product-site@sha256:${"a".repeat(63)}`,
    `registry.example/kokoro/product-site@sha512:${digest}`,
    `registry.example/kokoro/product-site:latest@sha256:${digest}`,
    `registry.example:0/kokoro/product-site@sha256:${digest}`,
    `registry.example:65536/kokoro/product-site@sha256:${digest}`,
    `registry.example:05000/kokoro/product-site@sha256:${digest}`,
    `https://registry.example/kokoro/product-site@sha256:${digest}`,
    ` registry.example/kokoro/product-site@sha256:${digest}`,
    `registry.example/kokoro/product-site@sha256:${digest} `,
    `registry.example/kokoro/product site@sha256:${digest}`,
  ];

  for (const reference of invalidReferences) {
    assert.throws(
      () => validateSiteReleaseImageReference(reference),
      /site_release_image_(?:missing|invalid)/u,
      String(reference),
    );
  }
});

test("rejects the known reference-site repository naming without claiming artifact provenance", () => {
  for (const reference of [
    `registry.example/kokoro/reference-site@sha256:${digest}`,
    `registry.example/apps/kokoro-reference-site@sha256:${digest}`,
  ]) {
    assert.throws(
      () => validateSiteReleaseImageReference(reference),
      (error) => error?.code === "site_release_image_forbidden_known_fixture_name",
      reference,
    );
  }
});

test("provision rejects an invalid Site image before manager or Docker can run", async () => {
  const directory = await mkdtemp(resolve(tmpdir(), "kokoro-site-image-preflight-"));
  const envFile = resolve(directory, "release.env");
  const mutationMarker = resolve(directory, "mutation-attempted");
  const fakeNode = resolve(directory, "node");
  const fakeDocker = resolve(directory, "docker");
  await writeFile(envFile, "KOKORO_SITE_IMAGE=registry.example/kokoro/product-site:latest\n");
  await writeFile(fakeNode, `#!/bin/sh
if [ "$1" = "scripts/infra/validate-site-release-image.mjs" ]; then
  exec ${JSON.stringify(process.execPath)} "$@"
fi
printf 'node %s\\n' "$*" >> "$MUTATION_MARKER"
exit 91
`);
  await writeFile(fakeDocker, `#!/bin/sh
printf 'docker %s\\n' "$*" >> "$MUTATION_MARKER"
exit 92
`);
  await Promise.all([chmod(fakeNode, 0o700), chmod(fakeDocker, 0o700)]);

  const environment = {
    ...process.env,
    MUTATION_MARKER: mutationMarker,
    PATH: `${directory}${delimiter}${process.env.PATH ?? ""}`,
  };
  delete environment.KOKORO_SITE_IMAGE;
  try {
    const result = spawnSync("bash", ["deploy/provision.sh", envFile, "test-site-preflight"], {
      cwd: root,
      encoding: "utf8",
      env: environment,
    });
    assert.notEqual(result.status, 0);
    assert.match(result.stderr, /site_release_image_invalid/u);
    await assert.rejects(readFile(mutationMarker, "utf8"), { code: "ENOENT" });
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
});
