# Kokoro Slice A contracts

`slice-a-contract-manifest.yaml` is the reviewed machine authority for the first SQL-backed backend closure. It renders:

- nine Protobuf files under `proto/` for Site, IAM, Chat, Agent, Model and Capability;
- the browser-only Web BFF contract at `openapi/slice-a-web-v1.yaml`;
- consumer-scoped TypeScript or Python artifacts declared by `consumers.yaml`.

Run the frozen local gates:

```bash
python3 contract/validate_slice_a_manifest.py contract/slice-a-contract-manifest.yaml
uv run python scripts/contract/render_slice_a.py --manifest contract/slice-a-contract-manifest.yaml --check
pnpm exec buf format --diff --exit-code contract/proto
pnpm exec buf lint contract
pnpm exec buf breaking contract --against contract/breaking/slice-a-v1.binpb
pnpm exec redocly lint contract/openapi/slice-a-web-v1.yaml
```

`contract/generate.py` reads only a caller-supplied clean Root commit and emits one declared consumer closure. Child repositories never modify Root Proto/OpenAPI or generated files by hand. Browser traffic remains Web BFF HTTP/SSE; service-to-service calls use generated Connect/gRPC contracts.

`root-e2e` is a test-harness consumer rather than a browser boundary. Its declared closure includes IAM authentication and authorization for the complete Refresh → Authorize → Logout lifecycle, while `kokoro-web` remains restricted to the browser-facing public closure.
