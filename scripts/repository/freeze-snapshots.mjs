#!/usr/bin/env node

import { createHash } from "node:crypto";
import { spawnSync } from "node:child_process";
import { lstat, mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, relative, resolve } from "node:path";
import {
  parseOwnershipYaml,
  validateOwnership,
} from "../foundation/ownership-attestation.mjs";

const DEFAULT_SOURCES = [
  ["kokoro-agent", "kokoro-agent"],
  ["kokoro-platform", "kokoro-platform"],
  ["kokoro-session", "kokoro-session"],
  ["kokoro-web", "kokoro-web"],
];
const FUTURE_COMMIT_FIELDS = [
  "exactSnapshotImportCommit",
  "implementationCommit",
  "finalHeadCommit",
  "verifiedCommit",
];
const EXPECTED_KEYS = ["schemaVersion", "approvedSpecCommit", "archiveTag", "sources"];
const EXPECTED_SOURCE_KEYS = [
  "id",
  "path",
  "origin",
  "commit",
  "tree",
  "archiveSha256",
  "trackedFileCount",
];
const MAX_GIT_OUTPUT_BYTES = 128 * 1024 * 1024;

class FreezeError extends Error {
  constructor(code, detail = "") {
    super(detail);
    this.code = code;
  }
}

function fail(error) {
  const code = error instanceof FreezeError ? error.code : "snapshot_freeze_failed";
  process.stderr.write(`${code}${error.message ? `: ${error.message}` : ""}\n`);
  process.exitCode = 1;
}

function exactKeys(value, expectedKeys) {
  if (value === null || typeof value !== "object" || Array.isArray(value)) return false;
  const keys = Object.keys(value).sort();
  const expected = [...expectedKeys].sort();
  return keys.length === expected.length && keys.every((key, index) => key === expected[index]);
}

function parseArguments(argv) {
  const options = {
    root: process.cwd(),
    sources: [],
    ownership: null,
    archiveTag: null,
    output: null,
    expected: null,
    approvedSpecCommit: null,
    requireArchiveRef: false,
  };

  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    if (argument === "--require-archive-ref") {
      options.requireArchiveRef = true;
      continue;
    }
    const value = argv[index + 1];
    if (!value) throw new FreezeError("snapshot_arguments_invalid", `missing value for ${argument}`);
    index += 1;
    switch (argument) {
      case "--root":
        options.root = resolve(value);
        break;
      case "--source": {
        const separator = value.indexOf("=");
        if (separator <= 0 || separator === value.length - 1) {
          throw new FreezeError("snapshot_arguments_invalid", "--source must be id=path");
        }
        options.sources.push([value.slice(0, separator), value.slice(separator + 1)]);
        break;
      }
      case "--ownership":
        options.ownership = resolve(value);
        break;
      case "--archive-tag":
        options.archiveTag = value;
        break;
      case "--output":
        options.output = resolve(value);
        break;
      case "--expected":
        options.expected = resolve(value);
        break;
      case "--approved-spec-commit":
        options.approvedSpecCommit = value;
        break;
      default:
        throw new FreezeError("snapshot_arguments_invalid", `unsupported argument: ${argument}`);
    }
  }

  const canonicalOwnership = resolve(
    options.root,
    "docs/reports/evidence/wave-0/ownership-attestation.yaml",
  );
  if (options.ownership !== null && options.ownership !== canonicalOwnership) {
    throw new FreezeError("ownership_attestation_path_invalid", options.ownership);
  }
  options.ownership = canonicalOwnership;

  const canonicalExpected = resolve(options.root, "config/repository/expected-snapshots.json");
  if (options.expected !== null && options.expected !== canonicalExpected) {
    throw new FreezeError("snapshot_expected_path_invalid", options.expected);
  }
  options.expected = canonicalExpected;

  if (
    options.sources.length > 0 &&
    process.env.KOKORO_FREEZE_TEST_ALLOW_CUSTOM_SOURCES !== "1"
  ) {
    throw new FreezeError("custom_sources_forbidden", "--source is test-only");
  }
  options.sources = options.sources.length > 0 ? options.sources : DEFAULT_SOURCES;
  options.output ??= resolve(options.root, "config/repository/frozen-submodules.yaml");
  options.archiveTag ??= "kokoro-monorepo-cutover-2026-07-26";
  const ids = options.sources.map(([id]) => id);
  if (new Set(ids).size !== ids.length) {
    throw new FreezeError("snapshot_arguments_invalid", "source ids must be unique");
  }
  return options;
}

function git(cwd, args, { encoding = "utf8", allowFailure = false } = {}) {
  const result = spawnSync("git", args, {
    cwd,
    encoding,
    maxBuffer: MAX_GIT_OUTPUT_BYTES,
    shell: false,
  });
  if (result.error) throw result.error;
  if (result.status !== 0 && !allowFailure) {
    const stderr = Buffer.isBuffer(result.stderr)
      ? result.stderr.toString("utf8")
      : result.stderr;
    throw new FreezeError("git_command_failed", `${args.join(" ")}: ${stderr.trim()}`);
  }
  return result;
}

function gitText(cwd, args, options) {
  return git(cwd, args, options).stdout.trim();
}

function parseGitlink(line, expectedPath) {
  const match = /^(\d{6})\s+commit\s+([0-9a-f]{40})\t(.+)$/u.exec(line);
  if (!match || match[1] !== "160000" || match[3] !== expectedPath) {
    throw new FreezeError("gitlink_invalid", expectedPath);
  }
  return match[2];
}

function parseRemoteRefs(output) {
  const refs = new Map();
  for (const line of output.split(/\r?\n/u)) {
    if (!line) continue;
    const [sha, ref] = line.split(/\s+/u);
    if (sha && ref) refs.set(ref, sha);
  }
  return refs;
}

function yamlScalar(value) {
  if (value === null) return "null";
  if (typeof value === "boolean" || typeof value === "number") return String(value);
  return JSON.stringify(value);
}

function renderManifest(manifest) {
  const lines = [
    `schemaVersion: ${manifest.schemaVersion}`,
    `gitVersion: ${yamlScalar(manifest.gitVersion)}`,
    `freezeParentCommit: ${yamlScalar(manifest.freezeParentCommit)}`,
    `approvedSpecCommit: ${yamlScalar(manifest.approvedSpecCommit)}`,
    `rootTrackedDirty: ${manifest.rootTrackedDirty}`,
    `rootTrackedStatusSha256: ${yamlScalar(manifest.rootTrackedStatusSha256)}`,
    `ownershipAttestationRef: ${yamlScalar(manifest.ownershipAttestationRef)}`,
    `ownershipAttestationSha256: ${yamlScalar(manifest.ownershipAttestationSha256)}`,
    `archiveTag: ${yamlScalar(manifest.archiveTag)}`,
    "sources:",
  ];
  for (const source of manifest.sources) {
    lines.push(
      `  - id: ${yamlScalar(source.id)}`,
      `    path: ${yamlScalar(source.path)}`,
      `    origin: ${yamlScalar(source.origin)}`,
      `    commit: ${yamlScalar(source.commit)}`,
      `    tree: ${yamlScalar(source.tree)}`,
      `    archiveSha256: ${yamlScalar(source.archiveSha256)}`,
      "    archiveCommandVersion: 1",
      `    trackedFileCount: ${source.trackedFileCount}`,
      `    remoteMainRef: ${yamlScalar(source.remoteMainRef)}`,
      `    remoteMainCommit: ${yamlScalar(source.remoteMainCommit)}`,
      `    archiveRef: ${yamlScalar(source.archiveRef)}`,
      `    archiveRemoteRefReachable: ${source.archiveRemoteRefReachable}`,
      '    licenseRef: "LicenseRef-Kokoro-Internal-Proprietary"',
    );
  }
  return `${lines.join("\n")}\n`;
}

function validateExpectedShape(expected) {
  for (const field of FUTURE_COMMIT_FIELDS) {
    if (expected !== null && typeof expected === "object" && Object.hasOwn(expected, field)) {
      throw new FreezeError("provenance_future_commit_forbidden", field);
    }
  }
  if (!exactKeys(expected, EXPECTED_KEYS)) {
    throw new FreezeError("snapshot_expected_invalid", "top-level fields");
  }
  if (expected.schemaVersion !== 1) {
    throw new FreezeError("snapshot_expected_invalid", "schemaVersion");
  }
  if (!/^[0-9a-f]{40}$/u.test(expected.approvedSpecCommit)) {
    throw new FreezeError("snapshot_expected_invalid", "approvedSpecCommit");
  }
  if (typeof expected.archiveTag !== "string" || expected.archiveTag === "") {
    throw new FreezeError("snapshot_expected_invalid", "archiveTag");
  }
  if (!Array.isArray(expected.sources) || expected.sources.length === 0) {
    throw new FreezeError("snapshot_expected_invalid", "sources");
  }

  const ids = new Set();
  for (const source of expected.sources) {
    if (!exactKeys(source, EXPECTED_SOURCE_KEYS)) {
      throw new FreezeError("snapshot_expected_invalid", "source fields");
    }
    if (
      typeof source.id !== "string" ||
      source.id === "" ||
      typeof source.path !== "string" ||
      source.path === "" ||
      typeof source.origin !== "string" ||
      source.origin === "" ||
      !/^[0-9a-f]{40}$/u.test(source.commit) ||
      !/^[0-9a-f]{40}$/u.test(source.tree) ||
      !/^[0-9a-f]{64}$/u.test(source.archiveSha256) ||
      !Number.isInteger(source.trackedFileCount) ||
      source.trackedFileCount < 0
    ) {
      throw new FreezeError("snapshot_expected_invalid", `${source.id || "source"}: values`);
    }
    if (ids.has(source.id)) {
      throw new FreezeError("snapshot_expected_invalid", `duplicate source: ${source.id}`);
    }
    ids.add(source.id);
  }
}

function validateExpected(expected, { approvedSpecCommit, archiveTag, sources }) {
  validateExpectedShape(expected);
  if (expected.approvedSpecCommit !== approvedSpecCommit) {
    throw new FreezeError("snapshot_expected_mismatch", "approvedSpecCommit");
  }
  if (expected.archiveTag !== archiveTag) {
    throw new FreezeError("snapshot_expected_mismatch", "archiveTag");
  }

  const expectedIds = expected.sources.map(({ id }) => id).sort();
  const actualIds = sources.map(({ id }) => id).sort();
  if (
    expectedIds.length !== actualIds.length ||
    expectedIds.some((id, index) => id !== actualIds[index])
  ) {
    throw new FreezeError("snapshot_expected_mismatch", "source inventory");
  }
  const actualById = new Map(sources.map((source) => [source.id, source]));
  for (const expectedSource of expected.sources) {
    const actual = actualById.get(expectedSource.id);
    for (const field of EXPECTED_SOURCE_KEYS.filter((field) => field !== "id")) {
      if (expectedSource[field] !== actual[field]) {
        throw new FreezeError("snapshot_expected_mismatch", `${expectedSource.id}.${field}`);
      }
    }
  }
}

async function readOwnership(options) {
  let stats;
  let bytes;
  try {
    stats = await lstat(options.ownership);
    bytes = await readFile(options.ownership);
  } catch (error) {
    if (error.code === "ENOENT") throw new FreezeError("ownership_attestation_missing");
    throw new FreezeError("ownership_attestation_unreadable", error.message);
  }
  if (!stats.isFile() || stats.isSymbolicLink()) {
    throw new FreezeError("ownership_attestation_path_invalid", options.ownership);
  }
  try {
    const validationError = validateOwnership(parseOwnershipYaml(bytes.toString("utf8")));
    if (validationError) throw new Error(validationError);
  } catch (error) {
    throw new FreezeError("ownership_attestation_invalid", error.message);
  }
  return bytes;
}

async function readExpected(options) {
  let source;
  try {
    source = await readFile(options.expected, "utf8");
  } catch (error) {
    if (error.code === "ENOENT") throw new FreezeError("snapshot_expected_missing");
    throw new FreezeError("snapshot_expected_unreadable", error.message);
  }
  let expected;
  try {
    expected = JSON.parse(source);
  } catch (error) {
    throw new FreezeError("snapshot_expected_invalid", error.message);
  }
  validateExpectedShape(expected);
  return expected;
}

async function freeze(options) {
  const ownershipBytes = await readOwnership(options);
  const expected = await readExpected(options);

  const rootTrackedStatus = gitText(options.root, [
    "status",
    "--porcelain=v1",
    "-z",
    "--untracked-files=no",
    "--ignore-submodules=all",
  ]);
  if (rootTrackedStatus !== "") {
    throw new FreezeError("root_tracked_worktree_dirty");
  }

  const freezeParentCommit = gitText(options.root, ["rev-parse", "HEAD"]);
  if (!/^[0-9a-f]{40}$/u.test(options.approvedSpecCommit ?? "")) {
    throw new FreezeError("approved_spec_commit_invalid", "expected a full commit SHA");
  }
  const approvedCommit = git(
    options.root,
    ["rev-parse", "--verify", `${options.approvedSpecCommit}^{commit}`],
    { allowFailure: true },
  );
  const approvedIsAncestor = git(
    options.root,
    ["merge-base", "--is-ancestor", options.approvedSpecCommit, freezeParentCommit],
    { allowFailure: true },
  );
  if (approvedCommit.status !== 0 || approvedIsAncestor.status !== 0) {
    throw new FreezeError(
      "approved_spec_commit_invalid",
      "commit must exist and be an ancestor of the freeze parent",
    );
  }
  const sources = [];

  for (const [id, sourcePath] of [...options.sources].sort(([left], [right]) =>
    left.localeCompare(right),
  )) {
    const absoluteSourcePath = resolve(options.root, sourcePath);
    const rootRelativePath = relative(options.root, absoluteSourcePath).replaceAll("\\", "/");
    if (rootRelativePath.startsWith("../") || rootRelativePath === "..") {
      throw new FreezeError("source_path_outside_root", sourcePath);
    }

    const gitlinkLine = gitText(options.root, ["ls-tree", "HEAD", rootRelativePath]);
    const pin = parseGitlink(gitlinkLine, rootRelativePath);
    const head = gitText(absoluteSourcePath, ["rev-parse", "HEAD"]);
    if (pin !== head) throw new FreezeError("gitlink_head_mismatch", id);

    const sourceTrackedStatus = gitText(absoluteSourcePath, [
      "status",
      "--porcelain=v1",
      "-z",
      "--untracked-files=no",
    ]);
    if (sourceTrackedStatus !== "") {
      throw new FreezeError("tracked_worktree_dirty", id);
    }

    const tree = gitText(absoluteSourcePath, ["rev-parse", "HEAD^{tree}"]);
    const origin = gitText(absoluteSourcePath, ["remote", "get-url", "origin"]);
    const trackedFiles = git(absoluteSourcePath, ["ls-files", "-z"], {
      encoding: null,
    }).stdout;
    let trackedFileCount = 0;
    for (const byte of trackedFiles) {
      if (byte === 0) trackedFileCount += 1;
    }
    const archive = git(absoluteSourcePath, ["archive", "--format=tar", pin], {
      encoding: null,
    }).stdout;
    const archiveSha256 = createHash("sha256").update(archive).digest("hex");
    const archiveRef = `refs/tags/${options.archiveTag}`;
    const remoteMainRef = "refs/heads/main";
    const remoteRefs = parseRemoteRefs(
      gitText(absoluteSourcePath, [
        "ls-remote",
        origin,
        remoteMainRef,
        archiveRef,
        `${archiveRef}^{}`,
      ]),
    );
    const archiveRemoteRefReachable =
      remoteRefs.get(archiveRef) === pin || remoteRefs.get(`${archiveRef}^{}`) === pin;
    if (options.requireArchiveRef && !archiveRemoteRefReachable) {
      throw new FreezeError("archive_remote_ref_unreachable", id);
    }

    sources.push({
      id,
      path: rootRelativePath,
      origin,
      commit: pin,
      tree,
      archiveSha256,
      trackedFileCount,
      remoteMainRef,
      remoteMainCommit: remoteRefs.get(remoteMainRef) ?? null,
      archiveRef,
      archiveRemoteRefReachable,
    });
  }

  validateExpected(expected, {
    approvedSpecCommit: options.approvedSpecCommit,
    archiveTag: options.archiveTag,
    sources,
  });

  const manifest = {
    schemaVersion: 1,
    gitVersion: gitText(options.root, ["--version"]),
    freezeParentCommit,
    approvedSpecCommit: options.approvedSpecCommit,
    rootTrackedDirty: false,
    rootTrackedStatusSha256: createHash("sha256").update("").digest("hex"),
    ownershipAttestationRef: relative(options.root, options.ownership).replaceAll("\\", "/"),
    ownershipAttestationSha256: createHash("sha256").update(ownershipBytes).digest("hex"),
    archiveTag: options.archiveTag,
    sources,
  };
  await mkdir(dirname(options.output), { recursive: true });
  await writeFile(options.output, renderManifest(manifest), "utf8");
  process.stdout.write(`snapshots_frozen: ${sources.length} source(s)\n`);
}

try {
  await freeze(parseArguments(process.argv.slice(2)));
} catch (error) {
  fail(error);
}
