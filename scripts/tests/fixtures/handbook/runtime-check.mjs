// Only for verifying extracted handbook examples against a temporary database.
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import path from "node:path";
import { test } from "node:test";
import { pathToFileURL } from "node:url";

const root = path.resolve(process.argv[2]);
const { buildApp } = await import(
  pathToFileURL(path.join(root, "dist/app.js"))
);
const { loadConfig } = await import(
  pathToFileURL(path.join(root, "dist/config/env.js"))
);
const { SiteRepository } = await import(
  pathToFileURL(path.join(root, "dist/modules/sites/site.repository.js"))
);
const require = createRequire(path.join(root, "package.json"));
const { Pool } = require("pg");
const tenantId = "00000000-0000-4000-8000-000000000001";
const config = loadConfig({
  APP_ENV: "test",
  PORT: "3000",
  DATABASE_POOL_MAX: "2",
  DATABASE_URL: process.env.HANDBOOK_DATABASE_URL,
});
// Synthetic credentials are confined to this test double; they are not an authentication implementation.
const security = {
  async authenticate(request) {
    return request.headers.authorization === "Bearer fixture"
      ? { tenantId, actorId: "fixture-actor" }
      : null;
  },
  async canCreate() {
    return true;
  },
};
const app = buildApp(config, security);
const pool = new Pool({ connectionString: config.databaseUrl });
const body = { site_key: "manual-test", display_name: "Handbook test" };
try {
  await test("configuration validates the typed boundary", () => {
    assert.equal(config.port, 3000);
    assert.throws(() => loadConfig({ APP_ENV: "test" }));
  });
  await test("missing authentication stops before a write", async () => {
    const response = await app.inject({
      method: "POST",
      url: "/v1/sites",
      payload: body,
    });
    assert.equal(response.statusCode, 401);
    assert.equal(response.json().error.code, "UNAUTHENTICATED");
    const count = await pool.query(
      "SELECT count(*)::int AS total FROM system_site",
    );
    assert.equal(count.rows[0].total, 0);
  });
  await test("unknown input fields are rejected", async () => {
    const response = await app.inject({
      method: "POST",
      url: "/v1/sites",
      headers: { authorization: "Bearer fixture" },
      payload: { ...body, tenant_id: "forged" },
    });
    assert.equal(response.statusCode, 400);
    assert.equal(response.json().error.code, "INVALID_REQUEST");
  });
  await test("invalid JSON, oversized input and unsupported media use safe error codes", async () => {
    for (const [payload, type, status] of [
      ["{", "application/json", 400],
      [
        JSON.stringify({ display_name: "x".repeat(70_000) }),
        "application/json",
        413,
      ],
      ["x", "application/unknown", 415],
    ]) {
      const response = await app.inject({
        method: "POST",
        url: "/v1/sites",
        headers: { authorization: "Bearer fixture", "content-type": type },
        payload,
      });
      assert.equal(response.statusCode, status);
      assert.ok(response.json().error.code);
    }
  });
  await test("real SQL write uses trusted tenant; soft deletion hides the row", async () => {
    const response = await app.inject({
      method: "POST",
      url: "/v1/sites",
      headers: { authorization: "Bearer fixture", "x-tenant-id": "forged" },
      payload: body,
    });
    assert.equal(response.statusCode, 201);
    const data = response.json().data;
    assert.deepEqual(Object.keys(data).sort(), [
      "display_name",
      "site_id",
      "site_key",
    ]);
    const repository = new SiteRepository(pool);
    const site = await repository.findById(tenantId, data.site_id);
    assert.equal(site.tenantId, tenantId);
    assert.ok(site.createdAt instanceof Date);
    assert.equal(site.deletedAt, null);
    assert.equal(
      await repository.findById(
        "00000000-0000-4000-8000-000000000002",
        data.site_id,
      ),
      null,
    );
    await pool.query(
      "UPDATE system_site SET deleted_at = CURRENT_TIMESTAMP(3), updated_at = CURRENT_TIMESTAMP(3) WHERE id = $1",
      [data.site_id],
    );
    assert.equal(await repository.findById(tenantId, data.site_id), null);
  });
  await test("owner permission denial and unknown errors do not leak details", async () => {
    for (const [canCreate, status, code] of [
      [async () => false, 403, "FORBIDDEN"],
      [
        async () => {
          throw new Error("private_provider_secret");
        },
        500,
        "INTERNAL_ERROR",
      ],
    ]) {
      const denied = buildApp(config, { ...security, canCreate });
      try {
        const response = await denied.inject({
          method: "POST",
          url: "/v1/sites",
          headers: { authorization: "Bearer fixture" },
          payload: body,
        });
        assert.equal(response.statusCode, status);
        assert.equal(response.json().error.code, code);
        assert.ok(!response.body.includes("private_provider_secret"));
      } finally {
        await denied.close();
      }
    }
  });
  await test("unknown routes have the same error envelope", async () => {
    const response = await app.inject({ method: "GET", url: "/not-a-route" });
    assert.equal(response.statusCode, 404);
    assert.equal(response.json().error.code, "NOT_FOUND");
    assert.ok(response.json().meta.request_id);
  });
} finally {
  await app.close();
  await pool.end();
}
