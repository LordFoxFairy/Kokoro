#!/usr/bin/env node

import { spawnSync } from "node:child_process";
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
    containers: (raw.containers ?? []).map(({ name, project, service, status }) => ({
      name,
      project: project || null,
      service: service || null,
      status,
    })),
    volumes: (raw.volumes ?? []).map(({ name, project, composeVolume, sizeBytes }) => ({
      name,
      project: project || null,
      composeVolume: composeVolume || null,
      sizeBytes: Number.isFinite(sizeBytes) ? sizeBytes : null,
      sizeAvailable: Number.isFinite(sizeBytes),
    })),
    images: (raw.images ?? []).map(({ repository, digest, sizeBytes }) => ({
      repository,
      digest,
      sizeBytes: Number.isFinite(sizeBytes) ? sizeBytes : null,
      sizeAvailable: Number.isFinite(sizeBytes),
    })),
  };
}

export function collectInventory() {
  const containers = parseJsonLines(
    docker(["ps", "-a", "--format", "{{json .}}"]).stdout,
  ).map((item) => ({
    name: item.Names,
    project: item.Labels?.match(/(?:^|,)com\.docker\.compose\.project=([^,]+)/u)?.[1] ?? "",
    service: item.Labels?.match(/(?:^|,)com\.docker\.compose\.service=([^,]+)/u)?.[1] ?? "",
    status: item.Status,
  }));

  const volumeNames = docker(["volume", "ls", "--format", "{{.Name}}"])
    .stdout.split(/\r?\n/u)
    .filter(Boolean);
  const volumes = volumeNames.map((name) => {
    const fields = docker([
      "volume",
      "inspect",
      "--format",
      '{{.Name}}\t{{index .Labels "com.docker.compose.project"}}\t{{index .Labels "com.docker.compose.volume"}}',
      name,
    ]).stdout.trim().split("\t");
    return {
      name: fields[0],
      project: fields[1] === "<no value>" ? "" : fields[1],
      composeVolume: fields[2] === "<no value>" ? "" : fields[2],
      sizeBytes: null,
    };
  });

  const images = parseJsonLines(
    docker(["image", "ls", "--format", "{{json .}}"]).stdout,
  ).map((item) => ({
    repository: item.Repository,
    digest: item.Digest,
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
  const args = process.argv.slice(2);
  if (args.length > 2 || (args[0] !== undefined && args[0] !== "--format")) {
    throw new Error("infra_inventory_arguments_invalid");
  }
  const format = args[0] === "--format" ? args[1] : "json";
  if (!["json", "summary"].includes(format)) {
    throw new Error("infra_inventory_arguments_invalid");
  }
  const inventory = collectInventory();
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
