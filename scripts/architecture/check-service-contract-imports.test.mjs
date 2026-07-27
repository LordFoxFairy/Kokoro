import assert from "node:assert/strict";
import { mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";

import { run, scan } from "./check-service-contract-imports.mjs";

function fixture(files) {
  const root = mkdtempSync(join(tmpdir(), "contract-imports-"));
  for (const [path, body] of Object.entries(files)) {
    const full = join(root, path);
    mkdirSync(join(full, ".."), { recursive: true });
    writeFileSync(full, typeof body === "string" ? body : JSON.stringify(body));
  }
  return root;
}

const USER_PKG = {
  "kokoro-user/package.json": {
    name: "@kokoro/user",
    exports: { ".": "./src/index.ts", "./contract": "./src/contract.ts" },
  },
};
const HUB_PKG = { "kokoro-hub/package.json": { name: "@kokoro/hub" } };

test("passes when a peer binds the narrow contract entry", () => {
  const root = fixture({
    ...USER_PKG,
    ...HUB_PKG,
    "kokoro-hub/src/a.ts": 'import { x } from "@kokoro/user/contract";\n',
  });
  const message = run(root);
  assert.match(message, /1 cross-service imports all via \/contract/u);
});

// The whole point: the package root drags the implementation along and is what a repo split breaks.
test("rejects a peer importing the package root", () => {
  const root = fixture({
    ...USER_PKG,
    ...HUB_PKG,
    "kokoro-hub/src/a.ts": 'import { x } from "@kokoro/user";\n',
  });
  assert.throws(() => run(root), (error) => {
    assert.equal(error.code, "contract_imports_not_narrow");
    assert.match(error.message, /kokoro-hub\/src\/a\.ts:1: imports "@kokoro\/user"/u);
    assert.match(error.message, /must bind "@kokoro\/user\/contract"/u);
    // Printed once, not doubled by re-prefixing a message that already carries the code.
    assert.equal(error.message.match(/contract_imports_not_narrow/gu)?.length, 1);
    return true;
  });
});

// A deeper subpath is not the published contract either.
test("rejects a peer reaching into a private subpath", () => {
  const root = fixture({
    ...USER_PKG,
    ...HUB_PKG,
    "kokoro-hub/src/a.ts": 'import { x } from "@kokoro/user/src/domain/user.js";\n',
  });
  assert.throws(() => run(root), /contract_imports_not_narrow/u);
});

// Telling a caller to import a path that does not exist is a worse error than naming the real gap.
test("names the missing contract entry rather than the root import", () => {
  const root = fixture({
    "kokoro-model/package.json": { name: "@kokoro/model", exports: { ".": "./src/index.ts" } },
    ...HUB_PKG,
    "kokoro-hub/src/a.ts": 'import { x } from "@kokoro/model";\n',
  });
  assert.throws(() => run(root), (error) => {
    assert.equal(error.code, "contract_imports_no_contract_entry");
    assert.match(error.message, /@kokoro\/model publishes no "\/contract" entry/u);
    return true;
  });
});

test("exempts the shared library", () => {
  const root = fixture({
    ...HUB_PKG,
    "kokoro-platform-kit/package.json": { name: "@kokoro/platform-kit" },
    "kokoro-hub/src/a.ts": 'import { callService } from "@kokoro/platform-kit";\n',
  });
  assert.match(run(root), /1 shared-library imports exempt/u);
});

// A parent that contains these packages is their composition root, not their peer.
test("exempts workspace-root code composing the modules", () => {
  const root = fixture({
    ...USER_PKG,
    "src/platform-registry.ts": 'import { userPlatformModule } from "@kokoro/user";\n',
  });
  const message = run(root);
  assert.match(message, /1 composition-root imports/u);
  assert.match(message, /0 cross-service imports/u);
});

test("a package importing itself by name is not a peer edge", () => {
  const root = fixture({
    ...USER_PKG,
    "kokoro-user/src/a.ts": 'import { x } from "@kokoro/user";\n',
  });
  assert.match(run(root), /0 cross-service imports/u);
});

test("ignores specifiers that are not workspace packages", () => {
  const root = fixture({
    ...HUB_PKG,
    "kokoro-hub/src/a.ts": 'import { z } from "@kokoro/not-a-package";\n',
  });
  assert.match(run(root), /0 cross-service imports/u);
});

test("catches a dynamic import too", () => {
  const root = fixture({
    ...USER_PKG,
    ...HUB_PKG,
    "kokoro-hub/src/a.ts": 'const m = await import("@kokoro/user");\n',
  });
  assert.throws(() => run(root), /contract_imports_not_narrow/u);
});

test("scans .mjs as well as .ts", () => {
  const root = fixture({
    ...USER_PKG,
    ...HUB_PKG,
    "kokoro-hub/src/a.mjs": 'import { x } from "@kokoro/user";\n',
  });
  assert.throws(() => run(root), /a\.mjs:1/u);
});

// Reading clean because the walk found nothing would be worse than failing.
test("fails closed on a tree with no sources", () => {
  const root = fixture({ "notes.md": "not source\n" });
  assert.throws(() => run(root), (error) => {
    assert.equal(error.code, "contract_imports_no_sources");
    return true;
  });
});

test("fails closed when no package manifest is found", () => {
  const root = fixture({ "src/a.ts": 'import { x } from "@kokoro/user";\n' });
  assert.throws(() => run(root), (error) => {
    assert.equal(error.code, "contract_imports_no_packages");
    return true;
  });
});

test("reports every violation, sorted", () => {
  const root = fixture({
    ...USER_PKG,
    ...HUB_PKG,
    "kokoro-hub/src/z.ts": 'import { x } from "@kokoro/user";\n',
    "kokoro-hub/src/a.ts": 'import { y } from "@kokoro/user";\n',
  });
  const { violations } = scan(root);
  assert.equal(violations.length, 2);
  assert.deepEqual([...violations].sort(), violations.sort());
});

test("generated output is skipped", () => {
  const root = fixture({
    ...USER_PKG,
    ...HUB_PKG,
    "kokoro-hub/generated/client.ts": 'import { x } from "@kokoro/user";\n',
    "kokoro-hub/src/a.ts": 'import { x } from "@kokoro/user/contract";\n',
  });
  assert.match(run(root), /1 cross-service imports all via \/contract/u);
});

test("real repository passes", () => {
  const repoRoot = join(import.meta.dirname, "..", "..");
  assert.match(run(join(repoRoot, "kokoro-platform")), /^service_contract_imports_ok:/u);
});
