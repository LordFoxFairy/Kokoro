import assert from "node:assert/strict";
import test from "node:test";

const inventoryModule = new URL("./inventory.mjs", import.meta.url);

test("summarizes Docker metadata without carrying mount paths or data", async () => {
  const { summarizeInventory } = await import(inventoryModule);
  const summary = summarizeInventory({
    containers: [{ name: "kokoro-infra-mysql-1", project: "kokoro-infra", status: "running" }],
    volumes: [
      { name: "kokoro-infra_kokoro-mysql", project: "kokoro-infra", sizeBytes: 100 },
      { name: "kokoro_kokoro-mysql", project: "kokoro", sizeBytes: 200 },
    ],
    images: [{ repository: "mysql", digest: `sha256:${"a".repeat(64)}`, sizeBytes: 300 }],
    imageTotalBytes: 700,
    containerTotalBytes: 250,
    buildCacheBytes: 400,
    forbiddenData: { mountpoint: "/private/data", contents: "secret" },
  });
  assert.deepEqual(summary.projects, ["kokoro", "kokoro-infra"]);
  assert.equal(summary.competingInfraProjects, true);
  assert.equal(summary.volumeCount, 2);
  assert.equal(summary.volumeBytes, 300);
  assert.equal(summary.imageBytes, 700);
  assert.equal(summary.imageBytesSource, "docker-system-total");
  assert.equal(summary.containerBytes, 250);
  assert.equal(summary.buildCacheBytes, 400);
  assert.doesNotMatch(JSON.stringify(summary), /private|secret|mountpoint|contents/u);
});

test("reports Docker volume totals without inventing per-volume precision", async () => {
  const { summarizeInventory } = await import(inventoryModule);
  const summary = summarizeInventory({
    containers: [],
    volumes: [
      { name: "first", project: "kokoro-infra", sizeBytes: null },
      { name: "second", project: "kokoro-infra", sizeBytes: 125 },
    ],
    volumeTotalBytes: 999,
    images: [],
  });
  assert.equal(summary.volumeBytes, 999);
  assert.equal(summary.volumeBytesSource, "docker-system-total");
  assert.equal(summary.volumes[0].sizeBytes, null);
  assert.equal(summary.volumes[0].sizeAvailable, false);
  assert.equal(summary.volumes[1].sizeBytes, 125);
  assert.equal(summary.volumes[1].sizeAvailable, true);
});
