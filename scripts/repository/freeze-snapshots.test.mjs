import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { spawnSync } from "node:child_process";
import { access, mkdtemp, mkdir, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, resolve } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const repositoryRoot = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const freezer = resolve(repositoryRoot, "scripts/repository/freeze-snapshots.mjs");
const validAttestation = `attestedBy: kokoro-repository-owner
authority: repository-owner
attestedAt: 2026-07-26T12:00:00.000Z
attestationRef: codex-task:opaque-owner-confirmation
repositories:
  - Kokoro
  - kokoro-agent
  - kokoro-platform
  - kokoro-session
  - kokoro-web
licenseRef: LicenseRef-Kokoro-Internal-Proprietary
`;

function run(command, args, cwd, expectedStatus = 0, encoding = "utf8") {
  const result = spawnSync(command, args, { cwd, encoding });
  assert.equal(
    result.status,
    expectedStatus,
    `${command} ${args.join(" ")}\nstdout: ${String(result.stdout)}\nstderr: ${String(result.stderr)}`,
  );
  return result;
}

function git(cwd, ...args) {
  return run("git", args, cwd).stdout.trim();
}

async function writeExpected(fixture, overrides = {}) {
  const tree = git(fixture.source, "rev-parse", "HEAD^{tree}");
  const origin = git(fixture.source, "remote", "get-url", "origin");
  const archive = run("git", ["archive", "--format=tar", fixture.pin], fixture.source, 0, null)
    .stdout;
  const source = {
    id: "fixture",
    path: "source",
    origin,
    commit: fixture.pin,
    tree,
    archiveSha256: createHash("sha256").update(archive).digest("hex"),
    trackedFileCount: 3,
  };
  const expected = {
    schemaVersion: 1,
    approvedSpecCommit: fixture.rootHead,
    archiveTag: "cutover-test",
    sources: [source],
    ...overrides,
  };
  await writeFile(fixture.expected, JSON.stringify(expected), "utf8");
}

async function makeFixture() {
  const root = await mkdtemp(resolve(tmpdir(), "kokoro-freeze-test-"));
  const source = resolve(root, "source");
  const remote = resolve(root, "source.git");
  const ownerEvidence = resolve(
    root,
    "docs/reports/evidence/wave-0/ownership-attestation.yaml",
  );
  const expected = resolve(root, "config/repository/expected-snapshots.json");
  const output = resolve(root, "snapshots.yaml");

  await mkdir(source);
  git(source, "init", "-b", "main");
  git(source, "config", "user.email", "test@example.com");
  git(source, "config", "user.name", "Kokoro Test");
  await writeFile(resolve(source, ".gitignore"), "ignored.txt\n", "utf8");
  await writeFile(resolve(source, "tracked.txt"), "one\n", "utf8");
  await writeFile(resolve(source, "line\nbreak.txt"), "nul-safe\n", "utf8");
  git(source, "add", ".gitignore", "tracked.txt", "line\nbreak.txt");
  git(source, "commit", "-m", "fixture");
  git(root, "init", "--bare", remote);
  git(source, "remote", "add", "origin", remote);
  git(source, "push", "-u", "origin", "main");

  git(root, "init", "-b", "main");
  git(root, "config", "user.email", "test@example.com");
  git(root, "config", "user.name", "Kokoro Test");
  await writeFile(resolve(root, ".gitignore"), "root-ignored.txt\n", "utf8");
  git(root, "add", ".gitignore");
  const pin = git(source, "rev-parse", "HEAD");
  git(root, "update-index", "--add", "--cacheinfo", `160000,${pin},source`);
  git(root, "commit", "-m", "pin source");

  await mkdir(dirname(ownerEvidence), { recursive: true });
  await mkdir(dirname(expected), { recursive: true });
  await writeFile(ownerEvidence, validAttestation, "utf8");

  const rootHead = git(root, "rev-parse", "HEAD");
  const fixture = { root, source, remote, ownerEvidence, expected, output, pin, rootHead };
  await writeExpected(fixture);
  return fixture;
}

async function withFixture(runFixture) {
  const fixture = await makeFixture();
  try {
    await runFixture(fixture);
  } finally {
    await rm(fixture.root, { recursive: true, force: true });
  }
}

function freezeArgs(fixture, ...extra) {
  return [
    freezer,
    "--root",
    fixture.root,
    "--source",
    "fixture=source",
    "--archive-tag",
    "cutover-test",
    "--output",
    fixture.output,
    "--approved-spec-commit",
    fixture.rootHead,
    ...extra,
  ];
}

function runFreezer(fixture, ...extra) {
  return spawnSync(process.execPath, freezeArgs(fixture, ...extra), {
    cwd: fixture.root,
    encoding: "utf8",
    env: { ...process.env, KOKORO_FREEZE_TEST_ALLOW_CUSTOM_SOURCES: "1" },
  });
}

async function assertNoOutput(fixture) {
  await assert.rejects(access(fixture.output), { code: "ENOENT" });
}

test("requires the canonical in-repository ownership attestation", async () => {
  await withFixture(async (fixture) => {
    for (const replacement of ["/dev/null", resolve(fixture.root, "../outside.yaml")]) {
      const result = runFreezer(fixture, "--ownership", replacement);
      assert.notEqual(result.status, 0);
      assert.match(result.stderr, /ownership_attestation_path_invalid/);
      await assertNoOutput(fixture);
    }
  });
});

test("fails when canonical ownership evidence is missing", async () => {
  await withFixture(async (fixture) => {
    await rm(fixture.ownerEvidence);
    const result = runFreezer(fixture);
    assert.notEqual(result.status, 0);
    assert.match(result.stderr, /ownership_attestation_missing/);
    await assertNoOutput(fixture);
  });
});

test("fully validates the ownership attestation contract", async () => {
  await withFixture(async (fixture) => {
    const invalidAttestations = [
      "",
      validAttestation.replace(
        "LicenseRef-Kokoro-Internal-Proprietary",
        "LicenseRef-Wrong",
      ),
      validAttestation.replace("  - kokoro-web\n", ""),
    ];
    for (const invalid of invalidAttestations) {
      await writeFile(fixture.ownerEvidence, invalid, "utf8");
      const result = runFreezer(fixture);
      assert.notEqual(result.status, 0);
      assert.match(result.stderr, /ownership_attestation_invalid/);
      await assertNoOutput(fixture);
    }
  });
});

test("requires an existing approved spec commit", async () => {
  await withFixture(async (fixture) => {
    const args = freezeArgs(fixture);
    args.splice(args.indexOf("--approved-spec-commit"), 2);
    const result = spawnSync(process.execPath, args, {
      cwd: fixture.root,
      encoding: "utf8",
      env: { ...process.env, KOKORO_FREEZE_TEST_ALLOW_CUSTOM_SOURCES: "1" },
    });
    assert.notEqual(result.status, 0);
    assert.match(result.stderr, /approved_spec_commit_invalid/);
  });
});

test("hard-fails on staged or unstaged root tracked modifications before output", async () => {
  for (const staged of [false, true]) {
    await withFixture(async (fixture) => {
      await writeFile(resolve(fixture.root, ".gitignore"), `${staged}\n`, "utf8");
      if (staged) git(fixture.root, "add", ".gitignore");
      const result = runFreezer(fixture);
      assert.notEqual(result.status, 0);
      assert.match(result.stderr, /root_tracked_worktree_dirty/);
      await assertNoOutput(fixture);
    });
  }
});

test("allows untracked and ignored root files", async () => {
  await withFixture(async (fixture) => {
    await writeFile(resolve(fixture.root, "untracked.txt"), "allowed\n", "utf8");
    await writeFile(resolve(fixture.root, "root-ignored.txt"), "allowed\n", "utf8");
    const result = runFreezer(fixture);
    assert.equal(result.status, 0, result.stderr);
  });
});

test("fails when a gitlink pin differs from the checked-out source HEAD", async () => {
  await withFixture(async (fixture) => {
    await writeFile(resolve(fixture.source, "tracked.txt"), "two\n", "utf8");
    git(fixture.source, "commit", "-am", "advance checkout");
    const result = runFreezer(fixture);
    assert.notEqual(result.status, 0);
    assert.match(result.stderr, /gitlink_head_mismatch/);
  });
});

test("fails when a tracked source worktree is dirty", async () => {
  await withFixture(async (fixture) => {
    await writeFile(resolve(fixture.source, "tracked.txt"), "dirty\n", "utf8");
    const result = runFreezer(fixture);
    assert.notEqual(result.status, 0);
    assert.match(result.stderr, /tracked_worktree_dirty/);
  });
});

test("ignores ignored source files", async () => {
  await withFixture(async (fixture) => {
    const first = runFreezer(fixture);
    assert.equal(first.status, 0, first.stderr);
    const baseline = await readFile(fixture.output, "utf8");

    await writeFile(resolve(fixture.source, "ignored.txt"), "local only\n", "utf8");
    const second = runFreezer(fixture);
    assert.equal(second.status, 0, second.stderr);
    assert.equal(await readFile(fixture.output, "utf8"), baseline);
    assert.match(baseline, /trackedFileCount: 3/);
    assert.match(baseline, /rootTrackedDirty: false/);
    assert.match(baseline, /gitVersion: "git version /);
    assert.doesNotMatch(baseline, /cutoverParentCommit|exactSnapshotImportCommit/u);
  });
});

test("requests NUL-delimited git output for tracked file counting", async () => {
  const source = await readFile(freezer, "utf8");
  assert.match(source, /\["ls-files", "-z"\]/u);
});

test("requires the canonical expected baseline", async () => {
  await withFixture(async (fixture) => {
    await rm(fixture.expected);
    const result = runFreezer(fixture);
    assert.notEqual(result.status, 0);
    assert.match(result.stderr, /snapshot_expected_missing/);
    await assertNoOutput(fixture);
  });
});

test("rejects a non-canonical expected baseline path", async () => {
  await withFixture(async (fixture) => {
    const result = runFreezer(fixture, "--expected", resolve(fixture.root, "other.json"));
    assert.notEqual(result.status, 0);
    assert.match(result.stderr, /snapshot_expected_path_invalid/);
  });
});

test("strictly validates every expected baseline field", async () => {
  await withFixture(async (fixture) => {
    const invalidBaselines = [
      { schemaVersion: 2, approvedSpecCommit: fixture.rootHead, archiveTag: "cutover-test", sources: [] },
      { schemaVersion: 1, approvedSpecCommit: fixture.rootHead, sources: [] },
      { schemaVersion: 1, approvedSpecCommit: fixture.rootHead, archiveTag: "cutover-test", sources: [], unknown: true },
      { schemaVersion: 1, approvedSpecCommit: fixture.rootHead, archiveTag: "cutover-test", sources: [{ id: "fixture" }] },
    ];
    for (const invalid of invalidBaselines) {
      await writeFile(fixture.expected, JSON.stringify(invalid), "utf8");
      const result = runFreezer(fixture);
      assert.notEqual(result.status, 0);
      assert.match(result.stderr, /snapshot_expected_invalid/);
      await assertNoOutput(fixture);
    }
  });
});

test("fails when an exact expected source value drifts", async () => {
  await withFixture(async (fixture) => {
    const parsed = JSON.parse(await readFile(fixture.expected, "utf8"));
    parsed.sources[0].archiveSha256 = "0".repeat(64);
    await writeFile(fixture.expected, JSON.stringify(parsed), "utf8");
    const result = runFreezer(fixture);
    assert.notEqual(result.status, 0);
    assert.match(result.stderr, /snapshot_expected_mismatch/);
  });
});

test("fails when the approved spec commit differs from the expected baseline", async () => {
  await withFixture(async (fixture) => {
    const parsed = JSON.parse(await readFile(fixture.expected, "utf8"));
    parsed.approvedSpecCommit = "0".repeat(40);
    await writeFile(fixture.expected, JSON.stringify(parsed), "utf8");
    const result = runFreezer(fixture);
    assert.notEqual(result.status, 0);
    assert.match(result.stderr, /snapshot_expected_mismatch/);
  });
});

test("rejects future or self-referential provenance fields", async () => {
  await withFixture(async (fixture) => {
    const parsed = JSON.parse(await readFile(fixture.expected, "utf8"));
    parsed.exactSnapshotImportCommit = fixture.pin;
    await writeFile(fixture.expected, JSON.stringify(parsed), "utf8");
    const result = runFreezer(fixture);
    assert.notEqual(result.status, 0);
    assert.match(result.stderr, /provenance_future_commit_forbidden/);
  });
});

test("prevents custom source subsets in normal production mode", async () => {
  await withFixture(async (fixture) => {
    const result = spawnSync(process.execPath, freezeArgs(fixture), {
      cwd: fixture.root,
      encoding: "utf8",
    });
    assert.notEqual(result.status, 0);
    assert.match(result.stderr, /custom_sources_forbidden/);
    await assertNoOutput(fixture);
  });
});

test("reports remote archive-ref reachability without claiming protection", async () => {
  await withFixture(async (fixture) => {
    const preAnchor = runFreezer(fixture);
    assert.equal(preAnchor.status, 0, preAnchor.stderr);
    assert.match(
      await readFile(fixture.output, "utf8"),
      /archiveRemoteRefReachable: false/,
    );

    const required = runFreezer(fixture, "--require-archive-ref");
    assert.notEqual(required.status, 0);
    assert.match(required.stderr, /archive_remote_ref_unreachable/);

    git(fixture.source, "tag", "cutover-test", fixture.pin);
    git(fixture.source, "push", "origin", "refs/tags/cutover-test");
    const anchored = runFreezer(fixture, "--require-archive-ref");
    assert.equal(anchored.status, 0, anchored.stderr);
  });
});
