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

test("records deterministic sanitized infrastructure identity and verifies exact drift", async () => {
  const { compareInventoryRecords, createInventoryRecord, summarizeInventory } = await import(inventoryModule);
  const inventory = summarizeInventory({
    containers: [{
      id: "container-1",
      name: "kokoro-infra-redis-1",
      project: "kokoro-infra",
      service: "redis",
      profile: "runtime",
      image: "redis:7@sha256:immutable",
      imageId: "sha256:image-id",
      ports: "127.0.0.1:6379->6379/tcp",
      status: "Up 1 minute (healthy)",
      health: "healthy",
      volumes: ["kokoro-infra_kokoro-redis:/data"],
      dataMarker: "redis-data-v1",
      secret: "must-not-survive",
      mountpoint: "/private/docker/data",
    }],
    volumes: [{
      name: "kokoro-infra_kokoro-redis",
      project: "kokoro-infra",
      composeVolume: "redis-data",
      driver: "local",
      dataMarker: "redis-data-v1",
      sizeBytes: 100,
      mountpoint: "/private/docker/volumes/redis",
    }],
    images: [{
      repository: "redis",
      tag: "7",
      digest: "sha256:immutable",
      id: "sha256:image-id",
      sizeBytes: 300,
    }],
  });
  const baseline = createInventoryRecord(inventory, { recordedAt: "2026-07-28T00:00:00.000Z" });
  const repeated = createInventoryRecord(inventory, { recordedAt: "2026-07-29T00:00:00.000Z" });
  assert.equal(baseline.inventoryDigest, repeated.inventoryDigest);
  assert.equal(baseline.schemaVersion, 1);
  assert.equal(compareInventoryRecords(baseline, repeated).matches, true);
  assert.doesNotMatch(JSON.stringify(baseline), /must-not-survive|private|mountpoint|secret/u);

  const withUnrelatedDockerResources = structuredClone(inventory);
  withUnrelatedDockerResources.containers.push({
    name: "personal-postgres",
    project: "personal-project",
    service: "postgres",
    image: "postgres:17",
    ports: "127.0.0.1:15432->5432/tcp",
  });
  withUnrelatedDockerResources.volumes.push({
    name: "personal-data",
    project: "personal-project",
    composeVolume: "data",
  });
  withUnrelatedDockerResources.images.push({ repository: "postgres", tag: "17" });
  assert.equal(
    createInventoryRecord(withUnrelatedDockerResources).inventoryDigest,
    baseline.inventoryDigest,
  );

  const changedInventory = structuredClone(repeated.inventory);
  changedInventory.containers[0].ports = "127.0.0.1:6380->6379/tcp";
  const changed = createInventoryRecord(changedInventory);
  const result = compareInventoryRecords(baseline, changed);
  assert.equal(result.matches, false);
  assert.deepEqual(result.changedServices, ["redis"]);
  assert.match(result.receiptId, /^sha256:[0-9a-f]{64}$/u);

  const tampered = structuredClone(baseline);
  tampered.inventory.containers[0].ports = "127.0.0.1:6390->6379/tcp";
  assert.throws(
    () => compareInventoryRecords(tampered, repeated),
    /infra_inventory_record_digest_mismatch/u,
  );

  const forgedBaseline = createInventoryRecord(changed.inventory);
  assert.equal(compareInventoryRecords(forgedBaseline, changed).matches, true);
  assert.throws(
    () => compareInventoryRecords(forgedBaseline, changed, {
      expectedBaselineDigest: baseline.inventoryDigest,
    }),
    /infra_inventory_expected_digest_mismatch/u,
  );
});

test("inventory record/check arguments are explicit and mutually exclusive", async () => {
  const { parseInventoryArguments } = await import(inventoryModule);
  assert.deepEqual(parseInventoryArguments(["--record", "/tmp/baseline.json"]), {
    format: "json",
    mode: "record",
    path: "/tmp/baseline.json",
    expectedDigest: null,
  });
  const expectedDigest = `sha256:${"a".repeat(64)}`;
  assert.deepEqual(parseInventoryArguments([
    "--check", "/tmp/baseline.json", "--expect-digest", expectedDigest,
  ]), {
    format: "json",
    mode: "check",
    path: "/tmp/baseline.json",
    expectedDigest,
  });
  assert.throws(
    () => parseInventoryArguments(["--check", "/tmp/baseline.json"]),
    /infra_inventory_arguments_invalid/u,
  );
  assert.throws(
    () => parseInventoryArguments(["--record", "a", "--check", "b"]),
    /infra_inventory_arguments_invalid/u,
  );
});
