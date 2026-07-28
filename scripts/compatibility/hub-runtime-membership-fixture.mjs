import { createServer } from "node:http";

function json(response, statusCode, body) {
  const payload = Buffer.from(JSON.stringify(body));
  response.writeHead(statusCode, {
    "content-length": String(payload.byteLength),
    "content-type": "application/json",
  });
  response.end(payload);
}

export async function startMembershipFixture({ port, internalSecret, namespace, userId }) {
  const server = createServer((request, response) => {
    const url = new URL(request.url ?? "/", "http://127.0.0.1");
    if (request.method !== "GET" || url.pathname !== "/memberships/check") {
      json(response, 404, { error: { code: "not_found", message: "not found" } });
      return;
    }
    if (
      request.headers["x-kokoro-service"] !== "hub" ||
      request.headers["x-kokoro-internal-secret"] !== internalSecret
    ) {
      json(response, 401, { error: { code: "internal.unauthorized", message: "unauthorized" } });
      return;
    }
    const active =
      url.searchParams.get("teamId") === namespace &&
      url.searchParams.get("userId") === userId;
    json(response, 200, { data: { active, role: active ? "owner" : null } });
  });
  await new Promise((done, reject) => {
    server.once("error", reject);
    server.listen(port, "127.0.0.1", done);
  });
  const address = server.address();
  if (address === null || typeof address === "string") {
    server.close();
    throw new Error("membership_fixture_address_invalid");
  }
  return {
    baseUrl: `http://127.0.0.1:${address.port}`,
    close: () => new Promise((done, reject) => {
      server.close((error) => error === undefined ? done() : reject(error));
    }),
  };
}
