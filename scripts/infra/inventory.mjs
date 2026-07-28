#!/usr/bin/env node

import { createHash } from "node:crypto";
import { spawnSync } from "node:child_process";
import { readFile, rename, writeFile } from "node:fs/promises";
import { pathToFileURL } from "node:url";

function docker(args, { allowFailure = false } = {}) {
  const result = spawnSync("docker", args, {
    encoding: "utf8",
    shell: false,
    maxBuffer: 16 * 1024 * 1024,
  });
  if (result.error) throw result.error;
  if (result.status !== 0 && !allowFailure) {
    throw new Error(`infra_inventory_docker_failed: ${result.stderr.trim()}`);
  }
  return result;
}

function parseJsonLines(source) {
  return source
    .split(/\r?\n/u)
    .filter(Boolean)
    .map((line) => JSON.parse(line));
}

function parseByteSize(value) {
  if (typeof value === "number") return value;
  const match = /^([0-9.]+)\s*(B|kB|MB|GB|TB)$/iu.exec(value ?? "");
  if (!match) return 0;
  const factors = { b: 1, kb: 1e3, mb: 1e6, gb: 1e9, tb: 1e12 };
  return Math.round(Number(match[1]) * factors[match[2].toLowerCase()]);
}

export function summarizeInventory(raw) {
  const projects = [
    ...new Set(
      [...(raw.containers ?? []), ...(raw.volumes ?? [])]
        .map(({ project }) => project)
        .filter(Boolean),
    ),
  ].sort();
  const infraProjects = projects.filter(
    (project) => project === "kokoro" || project.startsWith("kokoro-infra"),
  );
  const individuallyKnownVolumeBytes = (raw.volumes ?? []).reduce(
    (total, volume) => total + (volume.sizeBytes ?? 0),
    0,
  );
  const hasDockerVolumeTotal = Number.isFinite(raw.volumeTotalBytes);
  const hasDockerImageTotal = Number.isFinite(raw.imageTotalBytes);
  const knownImageBytes = (raw.images ?? []).reduce(
    (total, image) => total + (image.sizeBytes ?? 0),
    0,
  );
  return {
    schemaVersion: 1,
    containerCount: raw.containers?.length ?? 0,
    volumeCount: raw.volumes?.length ?? 0,
    imageCount: raw.images?.length ?? 0,
    containerBytes: Number.isFinite(raw.containerTotalBytes) ? raw.containerTotalBytes : null,
    volumeBytes: hasDockerVolumeTotal ? raw.volumeTotalBytes : individuallyKnownVolumeBytes,
    volumeBytesSource: hasDockerVolumeTotal ? "docker-system-total" : "known-items-sum",
    imageBytes: hasDockerImageTotal ? raw.imageTotalBytes : knownImageBytes,
    imageBytesSource: hasDockerImageTotal ? "docker-system-total" : "known-items-sum",
    buildCacheBytes: raw.buildCacheBytes ?? 0,
    projects,
    competingInfraProjects: new Set(infraProjects).size > 1,
    containers: (raw.containers ?? []).map(({
      id, name, project, service, profile, image, imageId, ports, status, health, volumes, dataMarker,
    }) => ({
      id: id || null,
      name,
      project: project || null,
      service: service || null,
      profile: profile || null,
      image: image || null,
      imageId: imageId || null,
      ports: ports || null,
      status,
      health: health || null,
      volumes: [...(volumes ?? [])].sort(),
      dataMarker: dataMarker || null,
    })),
    volumes: (raw.volumes ?? []).map(({
      name, project, composeVolume, driver, dataMarker, sizeBytes,
    }) => ({
      name,
      project: project || null,
      composeVolume: composeVolume || null,
      driver: driver || null,
      dataMarker: dataMarker || null,
      sizeBytes: Number.isFinite(sizeBytes) ? sizeBytes : null,
      sizeAvailable: Number.isFinite(sizeBytes),
    })),
    images: (raw.images ?? []).map(({ repository, tag, digest, id, sizeBytes }) => ({
      repository,
      tag: tag || null,
      digest,
      id: id || null,
      sizeBytes: Number.isFinite(sizeBytes) ? sizeBytes : null,
      sizeAvailable: Number.isFinite(sizeBytes),
    })),
  };
}

function inventoryIdentity(inventory) {
  const projectName = inventory.projectName ?? "kokoro-infra";
  const containers = (inventory.containers ?? []).filter(({ project }) => project === projectName);
  const imageReferences = containers.flatMap(({ image, imageId }) => [image, imageId]).filter(Boolean);
  return {
    projectName,
    containers: containers.map(({
      id, name, project, service, profile, image, imageId, ports, health, volumes, dataMarker,
    }) => ({
      id, name, project, service, profile, image, imageId, ports, health,
      volumes: [...(volumes ?? [])].sort(),
      dataMarker,
    })).sort((left, right) =>
      `${left.service}:${left.name}`.localeCompare(`${right.service}:${right.name}`)),
    volumes: (inventory.volumes ?? []).filter(({ project }) => project === projectName).map(({
      name, project, composeVolume, driver, dataMarker,
    }) => ({ name, project, composeVolume, driver, dataMarker }))
      .sort((left, right) => left.name.localeCompare(right.name)),
    images: (inventory.images ?? []).filter(({ repository, tag, digest, id }) =>
      imageReferences.some((reference) =>
        reference === id ||
        reference.startsWith(`${repository}:${tag}`) ||
        (digest && digest !== "<none>" && reference.includes(digest))))
      .map(({ repository, tag, digest, id }) => ({
      repository, tag, digest, id,
    })).sort((left, right) =>
      `${left.repository}:${left.tag}`.localeCompare(`${right.repository}:${right.tag}`)),
  };
}

function digest(value) {
  return `sha256:${createHash("sha256").update(JSON.stringify(value)).digest("hex")}`;
}

export function createInventoryRecord(inventory, { recordedAt = new Date().toISOString() } = {}) {
  const identity = inventoryIdentity(inventory);
  return {
    schemaVersion: 1,
    recordedAt,
    inventoryDigest: digest(identity),
    inventory: identity,
  };
}

export function compareInventoryRecords(baseline, current) {
  if (baseline?.schemaVersion !== 1 || current?.schemaVersion !== 1) {
    throw new Error("infra_inventory_record_invalid");
  }
  const baselineDigest = digest(inventoryIdentity(baseline.inventory));
  const currentDigest = digest(inventoryIdentity(current.inventory));
  if (baseline.inventoryDigest !== baselineDigest || current.inventoryDigest !== currentDigest) {
    throw new Error("infra_inventory_record_digest_mismatch");
  }
  const baselineByService = new Map(
    (baseline.inventory.containers ?? []).map((container) => [container.service, container]),
  );
  const currentByService = new Map(
    (current.inventory.containers ?? []).map((container) => [container.service, container]),
  );
  const changedServices = [...new Set([
    ...baselineByService.keys(),
    ...currentByService.keys(),
  ])].filter((service) =>
    JSON.stringify(baselineByService.get(service) ?? null) !==
    JSON.stringify(currentByService.get(service) ?? null))
    .sort();
  const receipt = { baselineDigest, currentDigest, changedServices };
  return {
    matches: baselineDigest === currentDigest,
    ...receipt,
    receiptId: digest(receipt),
  };
}

export function parseInventoryArguments(args) {
  const options = { format: "json", mode: "print", path: null };
  for (let index = 0; index < args.length; index += 1) {
    const argument = args[index];
    const value = args[index + 1];
    if (argument === "--format" && ["json", "summary"].includes(value)) {
      options.format = value;
      index += 1;
      continue;
    }
    if (["--record", "--check"].includes(argument) && value && options.mode === "print") {
      options.mode = argument.slice(2);
      options.path = value;
      index += 1;
      continue;
    }
    throw new Error("infra_inventory_arguments_invalid");
  }
  if (options.mode !== "print" && options.format !== "json") {
    throw new Error("infra_inventory_arguments_invalid");
  }
  return options;
}

export function collectInventory() {
  const containers = parseJsonLines(
    docker(["ps", "-a", "--format", "{{json .}}"]).stdout,
  ).map((item) => ({
    id: item.ID,
    name: item.Names,
    project: item.Labels?.match(/(?:^|,)com\.docker\.compose\.project=([^,]+)/u)?.[1] ?? "",
    service: item.Labels?.match(/(?:^|,)com\.docker\.compose\.service=([^,]+)/u)?.[1] ?? "",
    profile: item.Labels?.match(/(?:^|,)io\.kokoro\.infra\.profile=([^,]+)/u)?.[1] ?? "",
    image: item.Image,
    imageId: item.ImageID,
    ports: item.Ports,
    status: item.Status,
    health: item.Status?.match(/\((healthy|unhealthy|starting)\)/iu)?.[1]?.toLowerCase() ?? "",
    volumes: (item.Mounts ?? "").split(",").filter(Boolean),
    dataMarker: item.Labels?.match(/(?:^|,)io\.kokoro\.infra\.data-marker=([^,]+)/u)?.[1] ?? "",
  }));

  const volumeNames = docker(["volume", "ls", "--format", "{{.Name}}"])
    .stdout.split(/\r?\n/u)
    .filter(Boolean);
  const volumes = volumeNames.map((name) => {
    const fields = docker([
      "volume",
      "inspect",
      "--format",
      '{{.Name}}\t{{index .Labels "com.docker.compose.project"}}\t{{index .Labels "com.docker.compose.volume"}}\t{{.Driver}}\t{{index .Labels "io.kokoro.infra.data-marker"}}',
      name,
    ]).stdout.trim().split("\t");
    return {
      name: fields[0],
      project: fields[1] === "<no value>" ? "" : fields[1],
      composeVolume: fields[2] === "<no value>" ? "" : fields[2],
      driver: fields[3],
      dataMarker: fields[4] === "<no value>" ? "" : fields[4],
      sizeBytes: null,
    };
  });

  const images = parseJsonLines(
    docker(["image", "ls", "--format", "{{json .}}"]).stdout,
  ).map((item) => ({
    repository: item.Repository,
    tag: item.Tag,
    digest: item.Digest,
    id: item.ID,
    sizeBytes: parseByteSize(item.Size),
  }));

  const systemRows = parseJsonLines(
    docker(["system", "df", "--format", "{{json .}}"], { allowFailure: true }).stdout,
  );
  const volumeRow = systemRows.find(({ Type }) => Type === "Local Volumes");
  const imageRow = systemRows.find(({ Type }) => Type === "Images");
  const containerRow = systemRows.find(({ Type }) => Type === "Containers");
  const cacheRow = systemRows.find(({ Type }) => Type === "Build Cache");
  return summarizeInventory({
    containers,
    volumes,
    images,
    ...(volumeRow ? { volumeTotalBytes: parseByteSize(volumeRow.Size) } : {}),
    ...(imageRow ? { imageTotalBytes: parseByteSize(imageRow.Size) } : {}),
    ...(containerRow ? { containerTotalBytes: parseByteSize(containerRow.Size) } : {}),
    buildCacheBytes: cacheRow ? parseByteSize(cacheRow.Size) : null,
  });
}

async function main() {
  const { format, mode, path } = parseInventoryArguments(process.argv.slice(2));
  const inventory = collectInventory();
  if (mode === "record") {
    const record = createInventoryRecord(inventory);
    const temporaryPath = `${path}.${process.pid}.tmp`;
    await writeFile(temporaryPath, `${JSON.stringify(record, null, 2)}\n`, { mode: 0o600 });
    await rename(temporaryPath, path);
    process.stdout.write(`${JSON.stringify({ recorded: true, inventoryDigest: record.inventoryDigest })}\n`);
    return;
  }
  if (mode === "check") {
    const baseline = JSON.parse(await readFile(path, "utf8"));
    const result = compareInventoryRecords(baseline, createInventoryRecord(inventory));
    process.stdout.write(`${JSON.stringify(result)}\n`);
    if (!result.matches) throw new Error("infra_inventory_drift");
    return;
  }
  if (format === "json") {
    process.stdout.write(`${JSON.stringify(inventory, null, 2)}\n`);
  } else {
    process.stdout.write(
      `containers=${inventory.containerCount} volumes=${inventory.volumeCount} ` +
        `images=${inventory.imageCount} projects=${inventory.projects.join(",") || "none"} ` +
        `competing=${inventory.competingInfraProjects}\n`,
    );
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    process.stderr.write(`${error.message}\n`);
    process.exitCode = 1;
  });
}
