import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { execFile } from "node:child_process";
import { realpathSync } from "node:fs";
import { mkdtemp, mkdir, readFile, readdir, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { resolve } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";
import { promisify } from "node:util";

import {
  assertGeneratedMirrorTracked,
  GeneratedContractError,
  compareGeneratedMirror,
  parseArguments,
  pinnedPnpmSpecifier,
} from "./check-generated-contracts.mjs";
import * as generatedChecker from "./check-generated-contracts.mjs";
import {
  hardenPublicZodSchemas,
  parseArguments as parsePublicGeneratorArguments,
} from "../../contract/generate-public-openapi.mjs";

const repositoryRoot = resolve(fileURLToPath(new URL("../..", import.meta.url)));
const execFileAsync = promisify(execFile);

const adminAuthSourcePaths = [
  "kokoro/common/v1/error.proto",
  "kokoro/common/v1/receipt.proto",
  "kokoro/platform/admin/v1/admin_auth.proto",
];
const admissionSourcePaths = [
  "kokoro/common/v1/error.proto",
  "kokoro/common/v1/receipt.proto",
  "kokoro/platform/admission/v1/admission.proto",
];
const sessionAuthorizationSourcePaths = [
  "kokoro/platform/authorization/v1/session_authorization.proto",
];
const scopedSessionAuthorizationSourcePaths = [
  "kokoro/platform/authorization/v2/scoped_session_authorization.proto",
];
const dispatchOwnerEvidenceSourcePaths = [
  "kokoro/session/dispatch/v1/dispatch_owner_evidence.proto",
];

test("uses one exact pnpm release from the contract package manifest", () => {
  assert.equal(pinnedPnpmSpecifier("pnpm@11.2.2"), "pnpm@11.2.2");
  for (const invalid of [undefined, "", "npm@11.2.2", "pnpm@latest", "pnpm@11", "pnpm@0.0.0"]) {
    assert.throws(
      () => pinnedPnpmSpecifier(invalid),
      (error) =>
        error instanceof GeneratedContractError &&
        error.code === "generated_contract_package_manager_invalid",
    );
  }
});

async function sourceDigest(directory, sourcePaths) {
  const hash = createHash("sha256");
  for (const sourcePath of sourcePaths) {
    hash.update(`${sourcePath}\0`);
    hash.update(await readFile(resolve(directory, sourcePath)));
    hash.update("\0");
  }
  return hash.digest("hex");
}

async function artifactDigest(directory, current = directory) {
  const entries = await readdir(current, { withFileTypes: true });
  const chunks = [];
  for (const entry of entries.sort((left, right) => left.name.localeCompare(right.name))) {
    const path = resolve(current, entry.name);
    if (entry.isDirectory()) chunks.push(...(await artifactDigest(directory, path)));
    else if (entry.isFile() && entry.name !== "contract-metadata.ts") {
      const relativePath = path.slice(directory.length + 1).replaceAll("\\", "/");
      chunks.push(Buffer.from(`${relativePath}\0`), await readFile(path), Buffer.from("\0"));
    }
  }
  if (current !== directory) return chunks;
  return createHash("sha256").update(Buffer.concat(chunks)).digest("hex");
}

async function withTrees(run) {
  const root = await mkdtemp(resolve(tmpdir(), "kokoro-generated-contract-test-"));
  const expected = resolve(root, "expected");
  const mirror = resolve(root, "mirror");
  await mkdir(resolve(expected, "nested"), { recursive: true });
  await mkdir(resolve(mirror, "nested"), { recursive: true });
  try {
    await run({ root, expected, mirror });
  } finally {
    await rm(root, { recursive: true, force: true });
  }
}

test("accepts a byte-identical generated mirror", async () => {
  await withTrees(async ({ expected, mirror }) => {
    await writeFile(resolve(expected, "nested/service_pb.ts"), "same\n", "utf8");
    await writeFile(resolve(mirror, "nested/service_pb.ts"), "same\n", "utf8");

    await compareGeneratedMirror(expected, mirror, "fixture");
  });
});

test("rejects missing, extra and byte-different generated files", async () => {
  for (const mode of ["missing", "extra", "different"]) {
    await withTrees(async ({ expected, mirror }) => {
      await writeFile(resolve(expected, "nested/service_pb.ts"), "expected\n", "utf8");
      if (mode !== "missing") {
        await writeFile(
          resolve(mirror, "nested/service_pb.ts"),
          mode === "different" ? "different\n" : "expected\n",
          "utf8",
        );
      }
      if (mode === "extra") await writeFile(resolve(mirror, "extra.ts"), "extra\n", "utf8");

      await assert.rejects(
        compareGeneratedMirror(expected, mirror, "fixture"),
        (error) => error instanceof GeneratedContractError && error.code === "generated_contract_drift",
      );
    });
  }
});

test("rejects a byte-identical mirror that generation created only as ignored or untracked files", async () => {
  const root = await mkdtemp(resolve(tmpdir(), "kokoro-generated-tracking-test-"));
  const repository = resolve(root, "child");
  const mirror = resolve(repository, "src/generated/contracts");
  await mkdir(mirror, { recursive: true });
  await writeFile(resolve(mirror, "service.ts"), "generated\n", "utf8");
  try {
    await execFileAsync("git", ["init", "--quiet"], { cwd: repository });
    await assert.rejects(
      assertGeneratedMirrorTracked(root, "child/src/generated/contracts", "fixture"),
      (error) => error instanceof GeneratedContractError && error.code === "generated_contract_untracked",
    );
    await execFileAsync("git", ["add", "-f", "--", "src/generated/contracts/service.ts"], { cwd: repository });
    await assertGeneratedMirrorTracked(root, "child/src/generated/contracts", "fixture");
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test("production arguments are closed", () => {
  assert.deepEqual(parseArguments([]), { root: process.cwd() });
  assert.throws(() => parseArguments(["--output", "/tmp/out"]), {
    name: "GeneratedContractError",
    code: "generated_contract_arguments_invalid",
  });
});

test("public OpenAPI generation writes both registered live mirrors or one isolated temporary output", () => {
  const canonicalTemporaryRoot = realpathSync(tmpdir());
  const platformPublic = parsePublicGeneratorArguments([]);
  assert.equal(platformPublic.contract.schemaId, "platform-public-v1");
  assert.deepEqual(platformPublic.outputs, [
    resolve(repositoryRoot, "kokoro-platform/src/interfaces/http/generated/platform-public"),
    resolve(repositoryRoot, "kokoro-web/packages/site-client/src/generated/platform-public"),
  ]);

  const isolatedPlatformPublic = parsePublicGeneratorArguments([
    "--output",
    resolve(canonicalTemporaryRoot, "kokoro-public-generator-test"),
  ]);
  assert.equal(isolatedPlatformPublic.contract.schemaId, "platform-public-v1");
  assert.deepEqual(isolatedPlatformPublic.outputs, [
    resolve(canonicalTemporaryRoot, "kokoro-public-generator-test"),
  ]);

  const assetDataPlane = parsePublicGeneratorArguments([
    "--schema",
    "asset-data-plane-v1",
    "--output",
    resolve(canonicalTemporaryRoot, "kokoro-asset-data-plane-generator-test"),
  ]);
  assert.equal(assetDataPlane.contract.schemaId, "asset-data-plane-v1");
  assert.deepEqual(assetDataPlane.outputs, [
    resolve(canonicalTemporaryRoot, "kokoro-asset-data-plane-generator-test"),
  ]);
  assert.throws(
    () => parsePublicGeneratorArguments(["--output", resolve(repositoryRoot, "tmp/not-system-temp")]),
    /public_openapi_generation_output_must_be_temporary/u,
  );
});

test("public Zod generation enforces the uint64 maximum omitted by generic OpenAPI codegen", () => {
  const input = `import * as z from 'zod';\n` +
    `export const zPositiveUint64String = z.string().min(1).max(20).regex(/^[1-9][0-9]{0,19}$/);\n`;
  const output = hardenPublicZodSchemas(input);

  assert.match(output, /value\.length < 20 \|\| value <= "18446744073709551615"/u);
  assert.match(output, /must fit a positive uint64/u);
  assert.throws(
    () => hardenPublicZodSchemas("export const unrelated = 1;\n"),
    /public_openapi_domain_schema_missing:zPositiveUint64String/u,
  );
});

test("checker forwards an explicit isolated boundary and output through pnpm", () => {
  assert.equal(typeof generatedChecker.generationCommandArguments, "function");
  assert.deepEqual(
    generatedChecker.generationCommandArguments(
      "/repo/contract",
      "platform-admission@v1",
      "/tmp/generated",
    ),
    [
      "--dir",
      "/repo/contract",
      "run",
      "buf:generate",
      "--boundary",
      "platform-admission@v1",
      "--output",
      "/tmp/generated",
    ],
  );
  assert.deepEqual(
    generatedChecker.generationCommandArguments(
      "/repo/contract",
      "platform-public@v1",
      "/tmp/generated-public",
    ),
    [
      "--dir",
      "/repo/contract",
      "run",
      "openapi:generate:public",
      "--output",
      "/tmp/generated-public",
    ],
  );
});

test("privileged and public contracts have independent provider/consumer mirrors", () => {
  assert.deepEqual(generatedChecker.GENERATED_BOUNDARIES, [
    {
      id: "platform-admin-auth@v1",
      mirrors: [
        "kokoro-platform/kokoro-platform-admin/src/generated/contracts",
        "kokoro-web/apps/admin/lib/generated/contracts",
      ],
    },
    {
      id: "platform-admission@v1",
      mirrors: [
        "kokoro-platform/src/interfaces/connect/generated",
        "kokoro-session/src/platform/generated",
      ],
    },
    {
      id: "platform-asset-eligibility@v1",
      mirrors: [
        "kokoro-platform/src/interfaces/connect/generated-asset-eligibility",
        "kokoro-session/src/platform/asset-eligibility-generated",
      ],
    },
    {
      id: "platform-model-control@v1",
      mirrors: [
        "kokoro-platform/src/interfaces/connect/generated-model-control",
        "kokoro-web/apps/admin/lib/generated/model-control",
      ],
    },
    {
      id: "platform-session-authorization@v1",
      mirrors: [
        "kokoro-platform/src/interfaces/connect/generated-authorization",
        "kokoro-session/src/platform/authorization-generated",
      ],
    },
    {
      id: "session-dispatch-owner-evidence@v1",
      mirrors: [
        "kokoro-session/src/platform/evidence-generated",
        "kokoro-platform/src/interfaces/connect/generated-session-evidence",
      ],
    },
    {
      id: "platform-public@v1",
      mirrors: [
        "kokoro-platform/src/interfaces/http/generated/platform-public",
        "kokoro-web/packages/site-client/src/generated/platform-public",
      ],
    },
  ]);
  assert.deepEqual(generatedChecker.CONTRACT_ONLY_GENERATED_BOUNDARIES, [
    "platform-session-authorization@v2",
    "agent-execution-evidence@v1",
    "session-admission-owner@v1",
    "platform-media-runtime@v1",
    "model-image-effect@v1",
    "session-media-projection@v1",
    "platform-media-projection-recovery@v1",
    "platform-credit-cost-projection-recovery@v1",
  ]);
  assert.equal(adminAuthSourcePaths.includes("kokoro/platform/admission/v1/admission.proto"), false);
  assert.deepEqual(admissionSourcePaths, [
    "kokoro/common/v1/error.proto",
    "kokoro/common/v1/receipt.proto",
    "kokoro/platform/admission/v1/admission.proto",
  ]);
});

test("each isolated boundary emits its own pinned source metadata", async () => {
  const packageJson = JSON.parse(await readFile(resolve(repositoryRoot, "contract/package.json"), "utf8"));
  assert.equal(packageJson.scripts["buf:generate"], "node generate.mjs");

  const temporary = await mkdtemp(resolve(tmpdir(), "kokoro-boundary-metadata-test-"));
  try {
    for (const fixture of [
      {
        boundary: "platform-admin-auth@v1",
        schemaId: "kokoro.platform.admin.v1.AdminAuthService",
        sourcePaths: adminAuthSourcePaths,
        forbidden: "kokoro/platform/admission/v1/admission.proto",
      },
      {
        boundary: "platform-admission@v1",
        schemaId: "kokoro.platform.admission.v1.AdmissionService",
        sourcePaths: admissionSourcePaths,
        forbidden: "kokoro/platform/admin/v1/admin_auth.proto",
      },
      {
        boundary: "platform-session-authorization@v1",
        schemaId: "kokoro.platform.authorization.v1.SessionAuthorizationService",
        sourcePaths: sessionAuthorizationSourcePaths,
        forbidden: "kokoro/platform/admission/v1/admission.proto",
      },
      {
        boundary: "platform-session-authorization@v2",
        schemaId: "kokoro.platform.authorization.v2.ScopedSessionAuthorizationService",
        sourcePaths: scopedSessionAuthorizationSourcePaths,
        forbidden: "kokoro/platform/authorization/v1/session_authorization.proto",
      },
      {
        boundary: "session-dispatch-owner-evidence@v1",
        schemaId: "kokoro.session.dispatch.v1.DispatchOwnerEvidenceService",
        sourcePaths: dispatchOwnerEvidenceSourcePaths,
        forbidden: "kokoro/platform/admission/v1/admission.proto",
      },
    ]) {
      const output = resolve(temporary, fixture.boundary);
      await execFileAsync(
        process.execPath,
        [
          resolve(repositoryRoot, "contract/generate.mjs"),
          "--boundary",
          fixture.boundary,
          "--output",
          output,
        ],
        {cwd: repositoryRoot},
      );
      const metadata = await readFile(resolve(output, "contract-metadata.ts"), "utf8");
      const expectedSourceDigest = await sourceDigest(
        resolve(repositoryRoot, "contract/proto"),
        fixture.sourcePaths,
      );
      const expectedArtifactDigest = await artifactDigest(output);
      assert.match(metadata, new RegExp(`sourceDigestSha256: "${expectedSourceDigest}"`, "u"));
      assert.match(metadata, new RegExp(`artifactDigestSha256: "${expectedArtifactDigest}"`, "u"));
      assert.match(metadata, new RegExp(`schemaId: "${fixture.schemaId.replaceAll(".", "\\.")}"`, "u"));
      assert.match(metadata, /generatorVersion: "2\.13\.0"/u);
      assert.match(metadata, /runtimeVersion: "2\.13\.0"/u);
      for (const sourcePath of fixture.sourcePaths) assert.match(metadata, new RegExp(sourcePath, "u"));
      assert.doesNotMatch(metadata, new RegExp(fixture.forbidden, "u"));
    }
  } finally {
    await rm(temporary, {recursive: true, force: true});
  }
});

test("federated contract CI runs the pinned Buf and generated-mirror gates", async () => {
  const workflow = await readFile(resolve(repositoryRoot, ".github/workflows/contract.yml"), "utf8");

  assert.match(workflow, /pnpm --dir contract install --frozen-lockfile/u);
  assert.match(workflow, /pnpm --dir contract run buf:format:check/u);
  assert.match(workflow, /pnpm --dir contract run buf:lint/u);
  assert.match(workflow, /pnpm --dir contract run openapi:lint/u);
  assert.match(workflow, /git -C kokoro-platform diff --exit-code -- src\/interfaces\/http\/generated\/platform-public/u);
  assert.match(workflow, /status --porcelain --untracked-files=all -- src\/interfaces\/http\/generated\/platform-public/u);
  assert.match(workflow, /git -C kokoro-web diff --exit-code -- packages\/site-client\/src\/generated\/platform-public/u);
  assert.match(workflow, /node scripts\/repository\/check-generated-contracts\.mjs/u);
});
