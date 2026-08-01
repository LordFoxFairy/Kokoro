#!/usr/bin/env node

import { createHash } from "node:crypto";
import { execFileSync, spawnSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const REGISTRY_PATH = "contract/registry/prelaunch-protobuf-hard-cuts.yaml";
const EXPECTED_REGISTRY = {
  schemaVersion: 1,
  registryId: "kokoro.prelaunch-protobuf-hard-cuts.v1",
  authority: "root.contract",
  lifecycle: "contract-only",
  cuts: [
    {
      id: "site-lifecycle-activation-authority-r0a",
      sourcePath: "proto/kokoro/platform/site/v1/site_lifecycle.proto",
      baselineSourceDigest: "sha256:879f599f1d8a3737f0da7ab3c84d6f9c9c3420ff0b8f2f4b254502e2811c345e",
      candidateSourceDigest: "sha256:47be4c0c11bb00db3ad883194c9740db16c45a6f17d2c3939e41672158894f81",
      reason: "Pre-launch R0a hard cut: replace ambiguous release strings with typed candidate/version/epoch, active-pointer generation/CAS, and eligibility evidence references.",
    },
    {
      id: "site-provisioning-responsibility-cut-r0a",
      sourcePath: "proto/kokoro/platform/site/v1/site_provisioning.proto",
      baselineSourceDigest: "sha256:bbfa026b107cf4d2307e4af2b1c426171128f2097a4a6aa373d343af3d244c2e",
      candidateSourceDigest: "sha256:3c2a9876b814d8e65c0ebf44747749f38cf401d1a394d35b50bd01de34f2b177",
      reason: "Pre-launch R0a hard cut: keep platform-site-provisioning at registration only and move immutable publication commands to the Site publication authority.",
    },
    {
      id: "site-publication-authority-r0a",
      sourcePath: "proto/kokoro/platform/site/v1/site_publication.proto",
      baselineSourceDigest: "absent",
      candidateSourceDigest: "sha256:7950624409ec3e37f07226fc7a88f46aeb0b3a285f2c45f535a6b0838e832ffa",
      reason: "Pre-launch R0a hard cut: introduce typed operator publication and separate attested-workload evidence admission operations.",
    },
  ],
};

export class PrelaunchProtobufBreakingError extends Error {
  constructor(code, detail = "") {
    super(`${code}${detail ? `: ${detail}` : ""}`);
    this.code = code;
  }
}

const fail = (code, detail = "") => { throw new PrelaunchProtobufBreakingError(code, detail); };
const canonicalize = (value) => value === null || typeof value !== "object"
  ? JSON.stringify(value)
  : Array.isArray(value)
    ? `[${value.map(canonicalize).join(",")}]`
    : `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${canonicalize(value[key])}`).join(",")}}`;
const sourceDigest = (bytes) => `sha256:${createHash("sha256").update(bytes).digest("hex")}`;

function parseArguments(argv) {
  if (argv.length !== 2 || argv[0] !== "--against" || argv[1].length === 0) fail("prelaunch_protobuf_breaking_arguments_invalid");
  return argv[1];
}

function baselineRevision(against) {
  const match = against.match(/(?:^|#)branch=([^,]+)/u);
  if (match === null || !against.includes("subdir=contract")) fail("prelaunch_protobuf_breaking_against_invalid", against);
  return match[1];
}

function gitSource(root, revision, repositoryPath) {
  try {
    return execFileSync("git", ["show", `${revision}:${repositoryPath}`], { cwd: root, encoding: null, stdio: ["ignore", "pipe", "ignore"] });
  } catch {
    return null;
  }
}

export function breakingArguments({ root, against }) {
  let registry;
  try {
    registry = JSON.parse(readFileSync(resolve(root, REGISTRY_PATH), "utf8"));
  } catch (error) {
    fail("prelaunch_protobuf_hard_cut_registry_invalid", error.message);
  }
  if (canonicalize(registry) !== canonicalize(EXPECTED_REGISTRY)) fail("prelaunch_protobuf_hard_cut_registry_invalid");
  const revision = baselineRevision(against);
  let predecessorCount = 0;
  let currentCount = 0;
  const candidateSources = [];
  for (const cut of registry.cuts) {
    const repositoryPath = `contract/${cut.sourcePath}`;
    const candidateBytes = readFileSync(resolve(root, repositoryPath));
    const headBytes = gitSource(root, "HEAD", repositoryPath);
    if (headBytes === null || sourceDigest(candidateBytes) !== sourceDigest(headBytes)) {
      fail("prelaunch_protobuf_hard_cut_candidate_invalid", cut.id);
    }
    candidateSources.push({ cut, candidateDigest: sourceDigest(candidateBytes) });
    const baselineBytes = gitSource(root, revision, repositoryPath);
    const actualBaselineDigest = baselineBytes === null ? "absent" : sourceDigest(baselineBytes);
    if (actualBaselineDigest === cut.baselineSourceDigest) predecessorCount += 1;
    else if (actualBaselineDigest === cut.candidateSourceDigest) currentCount += 1;
    else fail("prelaunch_protobuf_hard_cut_baseline_invalid", cut.id);
  }
  if (predecessorCount !== 0 && currentCount !== 0) fail("prelaunch_protobuf_hard_cut_baseline_invalid", "mixed baseline");
  const args = ["breaking", "--against", against];
  if (predecessorCount === registry.cuts.length) {
    for (const { cut, candidateDigest } of candidateSources) {
      if (candidateDigest !== cut.candidateSourceDigest) fail("prelaunch_protobuf_hard_cut_candidate_invalid", cut.id);
      args.push("--exclude-path", cut.sourcePath);
    }
  }
  return args;
}

export function run({ root, against }) {
  const args = breakingArguments({ root, against });
  const result = spawnSync(resolve(root, "contract/node_modules/.bin/buf"), args, {
    cwd: resolve(root, "contract"),
    stdio: "inherit",
  });
  if (result.error) fail("prelaunch_protobuf_breaking_execution_failed", result.error.message);
  return result.status ?? 1;
}

function main() {
  const root = resolve(fileURLToPath(new URL("../..", import.meta.url)));
  process.exitCode = run({ root, against: parseArguments(process.argv.slice(2)) });
}

if (import.meta.url === pathToFileURL(process.argv[1] ?? "").href) {
  try { main(); }
  catch (error) {
    process.stderr.write(`${error instanceof Error ? error.message : String(error)}\n`);
    process.exitCode = 1;
  }
}
