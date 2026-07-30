import assert from "node:assert/strict";
import { mkdtemp, mkdir, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import {
  BoundaryCoverageError,
  checkBoundaryCoverage,
} from "./check-boundary-coverage.mjs";

async function fixture() {
  const root = await mkdtemp(join(tmpdir(), "kokoro-boundary-coverage-"));
  await mkdir(join(root, "kokoro-session/src"), { recursive: true });
  await mkdir(join(root, "kokoro-agent/src"), { recursive: true });
  await mkdir(join(root, "kokoro-web/src"), { recursive: true });
  await writeFile(join(root, "kokoro-session/src/main.ts"), [
    "KOKORO_CREDIT_BASE_URL",
    "KOKORO_MODEL_BASE_URL",
  ].join("\n"));
  await writeFile(join(root, "kokoro-agent/src/config.py"), [
    "KOKORO_HUB_RPC_URL",
    "resolve_execution_assembly",
    "fetch_skill_artifact",
    "KOKORO_LITELLM_BASE_URL",
  ].join("\n"));
  await writeFile(join(root, "kokoro-web/src/ignored.ts"), "KOKORO_HUB_BASE_URL\n");
  return root;
}

function registry() {
  return {
    boundaries: [
      {
        id: "platform-runtime",
        lifecycle: "active",
        provider: { repository: "kokoro-platform", boundary: "service.platform" },
        consumers: [{ repository: "kokoro-session", boundary: "service.session" }],
      },
      {
        id: "hub-runtime",
        lifecycle: "active",
        provider: { repository: "kokoro-platform", boundary: "platform.hub" },
        consumers: [{ repository: "kokoro-agent", boundary: "service.agent" }],
      },
      {
        id: "model-gateway",
        lifecycle: "active",
        provider: { repository: "kokoro-platform", boundary: "platform.litellm" },
        consumers: [{ repository: "kokoro-agent", boundary: "service.agent" }],
      },
    ],
  };
}

test("matches every discovered consumer edge to the exact provider boundary", async () => {
  const root = await fixture();
  try {
    const result = await checkBoundaryCoverage({ root, registry: registry() });
    assert.equal(result.scannedSources, 2);
    assert.deepEqual(result.edges, [
      "kokoro-agent->platform.hub",
      "kokoro-agent->platform.litellm",
      "kokoro-session->service.platform",
    ]);
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test("a different boundary from the same provider repository cannot back the edge", async () => {
  const root = await fixture();
  const wrong = registry();
  wrong.boundaries = wrong.boundaries.filter(({ id }) => id !== "hub-runtime");
  try {
    await assert.rejects(
      checkBoundaryCoverage({ root, registry: wrong }),
      (error) =>
        error instanceof BoundaryCoverageError &&
        error.code === "boundary_coverage_missing" &&
        error.detail === "kokoro-agent->platform.hub",
    );
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test("the exact provider boundary must declare the discovered repository as a consumer", async () => {
  const root = await fixture();
  const wrong = registry();
  wrong.boundaries.find(({ id }) => id === "hub-runtime").consumers = [];
  try {
    await assert.rejects(
      checkBoundaryCoverage({ root, registry: wrong }),
      (error) =>
        error instanceof BoundaryCoverageError &&
        error.code === "boundary_coverage_missing" &&
        error.detail === "kokoro-agent->platform.hub",
    );
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test("contract-only boundaries cannot cover live source edges", async () => {
  const root = await fixture();
  const wrong = registry();
  wrong.boundaries.find(({ id }) => id === "hub-runtime").lifecycle = "contract-only";
  try {
    await assert.rejects(
      checkBoundaryCoverage({ root, registry: wrong }),
      (error) =>
        error instanceof BoundaryCoverageError &&
        error.code === "boundary_coverage_missing",
    );
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});
