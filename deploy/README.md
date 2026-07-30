# Kokoro single-host release

Root composes independently released artifacts; it does not merge the four child repositories into
one runtime. `docker-compose.infra.yml` owns the canonical PostgreSQL/Redis/Mongo/MinIO/LiteLLM
authority. `docker-compose.app.yml` joins its external network and starts the latest application
topology only.

## Runtime topology

- one immutable Platform image: migrator, API, Admission, Authorization, asset data plane, model
  gateway, worker, and typed Admin;
- Hub management HTTP and Hub runtime Connect as separate processes from the same Platform image;
- Session Browser v3, with browser port `3900` and owner-authority port `3901`;
- Agent worker and Agent execution-evidence provider as separate processes from one Agent image;
- one independently promoted Site image. `kokoro-web` is the Site factory and is never a shared
  multi-Site production container.

All internal HTTP/2 or HTTPS boundaries use mTLS material owned by the calling and serving workloads.
Only the Site port is public by default; operator ports bind to `127.0.0.1` for diagnostics.

## Release prerequisites

1. Copy `deploy/.env.example` to the gitignored `deploy/.env.prod` and replace every `CHANGE_ME`.
2. Provision `kokoro_platform` and the eight exact Platform LOGIN roles named in the template. Create
   `kokoro_session` and the exact Session roles from `kokoro-session/.env.example`. The service
   migrators own schemas/grants; runtime roles must not be database owners or role members.
3. Populate `deploy/secrets/<process>/` with the files referenced by the env template. Each directory
   is mounted only into that process:

   ```text
   platform-api/              platform-admission/
   platform-authorization/    platform-asset-data-plane/
   platform-model-gateway/    platform-worker/       platform-admin/
   hub-http/                  hub-runtime/
   session/                   agent-worker/          agent-evidence/
   site-release/
   ```

4. Promote a generated Site project's verified standalone image as `KOKORO_SITE_IMAGE`. The canonical
   image shape is `kokoro-web/packages/site-scaffold/templates/site/Dockerfile`; Root does not build it
   from the Web monorepo.
5. Set `KOKORO_*_ENV_FILE` overrides to process-specific protected files for production. The helper
   script deliberately defaults them to the master env only for bounded single-host bring-up.

## Start

```bash
bash deploy/provision.sh deploy/.env.prod kokoro-app
```

The script performs exactly four phases: ensure canonical infrastructure, validate/build artifacts,
run `platform-migrator`, then start independent runtime processes. It does not write business data.
Initial Site/release/model/credit-program/offer/card-batch creation belongs to typed control-plane APIs;
there is no direct SQL or retired package seed escape hatch.

For manual operation:

```bash
docker compose --env-file deploy/.env.prod -p kokoro-app -f docker-compose.app.yml config
docker compose --env-file deploy/.env.prod -p kokoro-app -f docker-compose.app.yml run --rm --no-deps platform-migrator
docker compose --env-file deploy/.env.prod -p kokoro-app -f docker-compose.app.yml up -d
```

## Verification and rollback

```bash
node --test scripts/infra/*.test.mjs
docker compose --env-file deploy/.env.prod -p kokoro-app -f docker-compose.app.yml config --quiet
docker compose --env-file deploy/.env.prod -p kokoro-app -f docker-compose.app.yml ps
```

Verify the Site's `/api/health/ready`, Session ports `3900/3901`, Agent evidence `8443`, and every
Platform port listed in `docker-compose.app.yml`. Secure Connect readiness requires a probe identity;
a TCP-open signal alone is not activation evidence.

Rollback promotes the previous verified Root BOM and child image digests. Never roll back by selecting
retired services or reversing a forward-compatible schema migration. Runtime containers may be stopped
or replaced; database, object-store, workspace, and developer volumes are preserved.

Kubernetes shape and required Secrets are documented in `deploy/k8s/README.md`.
