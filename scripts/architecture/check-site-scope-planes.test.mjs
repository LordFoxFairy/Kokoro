import assert from "node:assert/strict";
import { mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";

import { run, scan } from "./check-site-scope-planes.mjs";

const DECLARATION = "  listUsers(siteId?: string, options?: ListOptions): Promise<User[]>;\n";

function fixture(files) {
  const root = mkdtempSync(join(tmpdir(), "site-scope-"));
  for (const [path, body] of Object.entries(files)) {
    const full = join(root, path);
    mkdirSync(join(full, ".."), { recursive: true });
    writeFileSync(full, body);
  }
  return root;
}

// A declaration with no unscoped caller is the shape every service should have.
test("passes when every call supplies a Site", () => {
  const root = fixture({
    "kokoro-user/src/domain/repository.ts": DECLARATION,
    "kokoro-user/src/interfaces/http/routes.ts": "const rows = await repo.listUsers(ctx.siteId);\n",
  });
  const message = run(root);
  assert.match(message, /site_scope_planes_ok: 2 sources, 1 methods take an optional Site/u);
  assert.match(message, /0 unscoped calls/u);
});

// The whole point: an unscoped read reached from a user-facing route returns every Site's rows.
test("rejects an unscoped call outside the admin plane", () => {
  const root = fixture({
    "kokoro-user/src/domain/repository.ts": DECLARATION,
    "kokoro-user/src/interfaces/http/routes.ts": "const rows = await repo.listUsers();\n",
  });
  assert.throws(() => run(root), (error) => {
    assert.equal(error.code, "site_scope_unscoped_call");
    assert.match(error.message, /routes\.ts:1: listUsers is called without a Site/u);
    // The code appears once, not doubled by the wrapper re-prefixing a message that already has it.
    assert.equal(error.message.match(/site_scope_unscoped_call/gu)?.length, 1);
    return true;
  });
});

test("allows the same call on the admin plane", () => {
  const root = fixture({
    "kokoro-user/src/domain/repository.ts": DECLARATION,
    "kokoro-user/src/interfaces/http/admin-routes.ts": "await repo.listUsers();\n",
  });
  assert.match(run(root), /1 unscoped calls, all on the admin plane/u);
});

// Passing a literal undefined is declining to scope just as much as omitting the argument.
test("rejects a literal undefined in the Site position", () => {
  const root = fixture({
    "kokoro-credit/src/domain/repository.ts":
      "  listAccounts(siteId?: string, options?: ListOptions): Promise<CreditAccount[]>;\n",
    "kokoro-credit/src/interfaces/http/routes.ts":
      "await repo.listAccounts(undefined, { includeDeleted: true });\n",
  });
  assert.throws(() => run(root), /site_scope_unscoped_call.*listAccounts/su);
});

test("accepts the union spelling of an optional key", () => {
  const root = fixture({
    "kokoro-model/src/domain/repository.ts":
      "  listSiteModelPolicies(siteId: string | undefined): Promise<SiteModelPolicy[]>;\n",
    "kokoro-model/src/interfaces/http/routes.ts": "await repo.listSiteModelPolicies();\n",
  });
  assert.throws(() => run(root), /listSiteModelPolicies/u);
});

test("covers every declared isolation key, not just siteId", () => {
  for (const key of ["ownerId", "workspaceId", "tenantId"]) {
    const root = fixture({
      "kokoro-x/src/domain/repository.ts": `  listThings(${key}?: string): Promise<Thing[]>;\n`,
      "kokoro-x/src/interfaces/http/routes.ts": "await repo.listThings();\n",
    });
    assert.throws(() => run(root), /site_scope_unscoped_call/u, `${key} not covered`);
  }
});

// Reading clean because the parser stopped matching would be worse than failing.
test("fails closed when no declaration is found", () => {
  const root = fixture({ "kokoro-user/src/domain/repository.ts": "listUsers(): Promise<User[]>;\n" });
  assert.throws(() => run(root), (error) => {
    assert.equal(error.code, "site_scope_no_declarations");
    return true;
  });
});

test("fails closed on an empty source tree", () => {
  const root = fixture({ "placeholder/keep.md": "not a source\n" });
  assert.throws(() => run(root), (error) => {
    assert.equal(error.code, "site_scope_no_sources");
    return true;
  });
});

test("reports every violation, sorted", () => {
  const root = fixture({
    "kokoro-user/src/domain/repository.ts": DECLARATION,
    "kokoro-user/src/interfaces/http/a-routes.ts": "await repo.listUsers();\n",
    "kokoro-user/src/interfaces/http/z-routes.ts": "await repo.listUsers();\n",
  });
  const { violations } = scan(root);
  assert.equal(violations.length, 2);
  assert.deepEqual([...violations].sort(), violations.sort());
});

// Test files describe intent, not shipped behaviour, so an unscoped call in one is not a finding.
test("ignores test files", () => {
  const root = fixture({
    "kokoro-user/src/domain/repository.ts": DECLARATION,
    "kokoro-user/src/interfaces/http/routes.test.ts": "await repo.listUsers();\n",
  });
  assert.match(run(root), /0 unscoped calls/u);
});

// Generated clients are regenerated from contracts; hand-editing them is not the fix.
test("ignores generated output", () => {
  const root = fixture({
    "kokoro-user/src/domain/repository.ts": DECLARATION,
    "kokoro-user/src/generated/client.ts": "await repo.listUsers();\n",
  });
  assert.match(run(root), /0 unscoped calls/u);
});
