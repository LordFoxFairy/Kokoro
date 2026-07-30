#!/usr/bin/env bash
# Latest-only single-host release orchestration: canonical infra -> immutable builds -> migrator ->
# independent runtime processes. Business catalog/Site bootstrap is an explicit typed control-plane
# operation and is never performed through retired seed packages.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

ENV_FILE="${1:-deploy/.env.prod}"
APP_PROJECT="${2:-kokoro-app}"
[[ -f "$ENV_FILE" ]] || {
  echo "missing release environment: $ENV_FILE" >&2
  exit 1
}

# A single-host bring-up may intentionally use one protected master env file. Production promotion
# should override each variable with a least-privilege per-process file; Compose already has those
# boundaries and Kubernetes requires them.
for variable in \
  KOKORO_PLATFORM_MIGRATOR_ENV_FILE \
  KOKORO_PLATFORM_API_ENV_FILE \
  KOKORO_PLATFORM_ADMISSION_ENV_FILE \
  KOKORO_PLATFORM_AUTHORIZATION_ENV_FILE \
  KOKORO_PLATFORM_ASSET_DATA_PLANE_ENV_FILE \
  KOKORO_PLATFORM_MODEL_GATEWAY_ENV_FILE \
  KOKORO_PLATFORM_WORKER_ENV_FILE \
  KOKORO_PLATFORM_ADMIN_ENV_FILE \
  KOKORO_HUB_HTTP_ENV_FILE \
  KOKORO_HUB_RUNTIME_ENV_FILE \
  KOKORO_SESSION_ENV_FILE \
  KOKORO_AGENT_WORKER_ENV_FILE \
  KOKORO_AGENT_EVIDENCE_ENV_FILE \
  KOKORO_SITE_ENV_FILE; do
  if [[ -z "${!variable:-}" ]]; then
    printf -v "$variable" '%s' "$ENV_FILE"
    export "$variable"
  fi
done

APP=(docker compose --env-file "$ENV_FILE" -p "$APP_PROJECT" -f docker-compose.app.yml)
RUNTIMES=(
  platform-api
  platform-admission
  platform-authorization
  platform-asset-data-plane
  platform-model-gateway
  platform-worker
  platform-admin
  kokoro-hub
  kokoro-hub-runtime
  kokoro-agent-evidence
  kokoro-session
  kokoro-agent-worker
  kokoro-site-release
)

echo "==> [1/5] ensure canonical infrastructure"
node scripts/infra/manager.mjs ensure \
  --profiles full \
  --scope production \
  --mode production \
  --infra-env-file "$ENV_FILE"

echo "==> [2/5] validate and build release artifacts"
"${APP[@]}" config --quiet
"${APP[@]}" build \
  platform-migrator \
  platform-api \
  kokoro-session \
  kokoro-agent-worker

echo "==> [3/5] apply Platform schema and role grants"
"${APP[@]}" run --rm --no-deps platform-migrator

echo "==> [4/5] install and seal initial Admin authorities when explicitly requested"
if [[ -n "${KOKORO_ADMIN_AUTHORITY_BOOTSTRAP_FILE:-}" ]]; then
  [[ -f "$KOKORO_ADMIN_AUTHORITY_BOOTSTRAP_FILE" ]] || {
    echo "missing Admin authority bootstrap file: $KOKORO_ADMIN_AUTHORITY_BOOTSTRAP_FILE" >&2
    exit 1
  }
  KOKORO_ADMIN_AUTHORITY_BOOTSTRAP_UID="$(id -u)"
  KOKORO_ADMIN_AUTHORITY_BOOTSTRAP_GID="$(id -g)"
  export KOKORO_ADMIN_AUTHORITY_BOOTSTRAP_UID KOKORO_ADMIN_AUTHORITY_BOOTSTRAP_GID
  "${APP[@]}" run --rm --no-deps platform-admin-bootstrap
else
  echo "skip: export KOKORO_ADMIN_AUTHORITY_BOOTSTRAP_FILE for a fresh installation"
fi

echo "==> [5/5] start independent runtime processes"
"${APP[@]}" run --rm --no-deps workspace-init
"${APP[@]}" up -d --no-deps "${RUNTIMES[@]}"
"${APP[@]}" ps

echo "release processes started; Site endpoint: http://localhost:${KOKORO_SITE_HOST_PORT:-3000}"
