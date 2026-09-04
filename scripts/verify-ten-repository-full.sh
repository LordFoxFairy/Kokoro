#!/usr/bin/env bash
set -Eeuo pipefail

# Full local gate for the ten active repositories.
#
# This is an orchestration entrypoint, not a second source of truth for a
# child repository. Each child owns its commands, contract and schema; this
# script only supplies isolated test databases/Redis logical databases and
# invokes those commands in a deterministic order. PostgreSQL and Redis are
# deliberately shared: an existing endpoint is reused and only a missing
# default fixture is started by this script.

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

PG_ADMIN_URL="${KOKORO_VERIFY_POSTGRES_ADMIN_URL:-postgresql://kokoro:kokoro@127.0.0.1:55433/postgres}"
REDIS_BASE_URL="${KOKORO_VERIFY_REDIS_URL:-redis://127.0.0.1:56380}"
S3_ENDPOINT="${KOKORO_VERIFY_S3_ENDPOINT:-http://127.0.0.1:39190}"
S3_ACCESS_KEY_ID="${KOKORO_VERIFY_S3_ACCESS_KEY_ID:-kokoro-test}"
S3_SECRET_ACCESS_KEY="${KOKORO_VERIFY_S3_SECRET_ACCESS_KEY:-kokoro-test-secret}"
SCANNER_HOST="${KOKORO_VERIFY_SCANNER_HOST:-127.0.0.1}"
SCANNER_PORT="${KOKORO_VERIFY_SCANNER_PORT:-43310}"
TRIVY_IMAGE="${KOKORO_VERIFY_TRIVY_IMAGE:-aquasec/trivy@sha256:bcc376de8d77cfe086a917230e818dc9f8528e3c852f7b1aff648949b6258d1c}"
TRIVY_CACHE_VOLUME="${KOKORO_VERIFY_TRIVY_CACHE_VOLUME:-kokoro-ten-repository-trivy-cache}"
POSTGRES_IMAGE="${KOKORO_VERIFY_POSTGRES_IMAGE:-postgres@sha256:cf78e76683b9ca8c5733cbbdce6c9262b45b6767934dd0a95e671f9a0fc20685}"
REDIS_IMAGE="${KOKORO_VERIFY_REDIS_IMAGE:-redis@sha256:ff02b58f971e7d7d156a1267e283fcbbeee91773b6aa36c49dac28ecfe28eadf}"
POSTGRES_CONTAINER="${KOKORO_VERIFY_POSTGRES_CONTAINER:-kokoro-v1-verify-postgres}"
REDIS_CONTAINER="${KOKORO_VERIFY_REDIS_CONTAINER:-kokoro-v1-verify-redis}"

readonly DEFAULT_PG_ADMIN_URL="postgresql://kokoro:kokoro@127.0.0.1:55433/postgres"
readonly DEFAULT_REDIS_BASE_URL="redis://127.0.0.1:56380"

readonly DATABASES=(
  kokoro_gate_bff
  kokoro_gate_agent
  kokoro_gate_iam
  kokoro_gate_system
  kokoro_gate_model
  kokoro_gate_billing
  kokoro_gate_capability
  kokoro_gate_storage
)

declare -A DATABASE_URLS=()
declare -a CREATED_DATABASES=()
declare -a CREATED_CONTAINERS=()

KEEP_DATABASES="${KOKORO_FULL_KEEP_DATABASES:-0}"
SKIP_STATIC="${KOKORO_FULL_SKIP_STATIC:-0}"
SKIP_IMAGES="${KOKORO_FULL_SKIP_IMAGES:-0}"
SKIP_EXTERNAL="${KOKORO_FULL_SKIP_EXTERNAL_SMOKE:-0}"
SKIP_E2E="${KOKORO_FULL_SKIP_E2E:-0}"

log() {
  printf '\n[%s] %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$*"
}

die() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || die "required command is missing: $1"
}

database_url() {
  python3 - "$PG_ADMIN_URL" "$1" <<'PY'
import sys
from urllib.parse import urlsplit, urlunsplit

source = urlsplit(sys.argv[1])
if source.scheme not in {"postgres", "postgresql"}:
    raise SystemExit("PostgreSQL admin URL must use postgres:// or postgresql://")
print(urlunsplit((source.scheme, source.netloc, f"/{sys.argv[2]}", source.query, source.fragment)))
PY
}

redis_url_for_db() {
  python3 - "$REDIS_BASE_URL" "$1" <<'PY'
import sys
from urllib.parse import urlsplit, urlunsplit

source = urlsplit(sys.argv[1])
if source.scheme not in {"redis", "rediss"}:
    raise SystemExit("Redis URL must use redis:// or rediss://")
print(urlunsplit((source.scheme, source.netloc, f"/{sys.argv[2]}", source.query, source.fragment)))
PY
}

postgres_ready() {
  psql "$PG_ADMIN_URL" -v ON_ERROR_STOP=1 -Atqc 'SELECT 1' >/dev/null 2>&1
}

redis_ready() {
  redis-cli -u "$(redis_url_for_db 0)" PING 2>/dev/null | grep -qx PONG
}

wait_for() {
  local description="$1"
  local probe="$2"
  shift 2
  local attempt
  for attempt in $(seq 1 60); do
    if "$probe" "$@"; then
      log "$description ready"
      return 0
    fi
    sleep 1
  done
  die "$description did not become ready within 60 seconds"
}

container_exists() {
  docker container inspect "$1" >/dev/null 2>&1
}

container_running() {
  [[ "$(docker inspect -f '{{.State.Running}}' "$1" 2>/dev/null || true)" == "true" ]]
}

ensure_postgres() {
  if postgres_ready; then
    log "reuse PostgreSQL at ${PG_ADMIN_URL}"
    return
  fi
  [[ "$PG_ADMIN_URL" == "$DEFAULT_PG_ADMIN_URL" ]] || die "PostgreSQL is unavailable at ${PG_ADMIN_URL}; custom endpoints are never started automatically"
  if container_exists "$POSTGRES_CONTAINER"; then
    if ! container_running "$POSTGRES_CONTAINER"; then
      log "start existing PostgreSQL fixture ${POSTGRES_CONTAINER}"
      docker start "$POSTGRES_CONTAINER" >/dev/null
    fi
  else
    log "start one PostgreSQL fixture ${POSTGRES_CONTAINER}"
    docker run --detach --name "$POSTGRES_CONTAINER" \
      --label com.kokoro.verification=ten-repository \
      --publish 127.0.0.1:55433:5432 \
      --env POSTGRES_USER=kokoro \
      --env POSTGRES_PASSWORD=kokoro \
      --env POSTGRES_DB=postgres \
      "$POSTGRES_IMAGE" >/dev/null
    CREATED_CONTAINERS+=("$POSTGRES_CONTAINER")
  fi
  wait_for "PostgreSQL" postgres_ready
}

ensure_redis() {
  if redis_ready; then
    log "reuse Redis at ${REDIS_BASE_URL}"
    return
  fi
  [[ "$REDIS_BASE_URL" == "$DEFAULT_REDIS_BASE_URL" ]] || die "Redis is unavailable at ${REDIS_BASE_URL}; custom endpoints are never started automatically"
  if container_exists "$REDIS_CONTAINER"; then
    if ! container_running "$REDIS_CONTAINER"; then
      log "start existing Redis fixture ${REDIS_CONTAINER}"
      docker start "$REDIS_CONTAINER" >/dev/null
    fi
  else
    log "start one Redis fixture ${REDIS_CONTAINER}"
    docker run --detach --name "$REDIS_CONTAINER" \
      --label com.kokoro.verification=ten-repository \
      --publish 127.0.0.1:56380:6379 \
      "$REDIS_IMAGE" >/dev/null
    CREATED_CONTAINERS+=("$REDIS_CONTAINER")
  fi
  wait_for "Redis" redis_ready
}

assert_database_reset_is_explicit() {
  if [[ "$PG_ADMIN_URL" != "$DEFAULT_PG_ADMIN_URL" && "${KOKORO_FULL_ALLOW_DATABASE_RESET:-0}" != "1" ]]; then
    die "refusing to drop kokoro_gate_* databases on a custom PostgreSQL endpoint; set KOKORO_FULL_ALLOW_DATABASE_RESET=1 for an explicitly disposable fixture"
  fi
}

reset_database() {
  local database="$1"
  # Database names are constants from this file, never user input.
  psql "$PG_ADMIN_URL" -v ON_ERROR_STOP=1 \
    -c "DROP DATABASE IF EXISTS \"${database}\" WITH (FORCE)" \
    -c "CREATE DATABASE \"${database}\"" >/dev/null
  CREATED_DATABASES+=("$database")
  DATABASE_URLS["$database"]="$(database_url "$database")"
}

flush_verification_redis() {
  local db
  if [[ "$REDIS_BASE_URL" != "$DEFAULT_REDIS_BASE_URL" && "${KOKORO_FULL_ALLOW_SHARED_REDIS_FLUSH:-0}" != "1" ]]; then
    die "refusing to FLUSHDB on a custom Redis endpoint; set KOKORO_FULL_ALLOW_SHARED_REDIS_FLUSH=1 for an explicitly disposable fixture"
  fi
  for db in $(seq 1 9); do
    redis-cli -u "$(redis_url_for_db "$db")" FLUSHDB >/dev/null
  done
}

cleanup() {
  local database container
  if [[ "$KEEP_DATABASES" != "1" ]]; then
    for database in "${CREATED_DATABASES[@]}"; do
      psql "$PG_ADMIN_URL" -v ON_ERROR_STOP=1 \
        -c "DROP DATABASE IF EXISTS \"${database}\" WITH (FORCE)" >/dev/null 2>&1 || true
    done
  else
    log "keeping verification databases because KOKORO_FULL_KEEP_DATABASES=1"
  fi
  for container in "${CREATED_CONTAINERS[@]}"; do
    docker rm --force "$container" >/dev/null 2>&1 || true
  done
}
trap cleanup EXIT

for command in psql redis-cli python3 pnpm uv go docker; do
  require_command "$command"
done

log "validate Root topology and ten-repository structural standard"
if [[ "$SKIP_STATIC" == "1" ]]; then
  log "SKIP static standard requested by KOKORO_FULL_SKIP_STATIC=1"
else
  python3 "$ROOT/scripts/verify-ten-repository-standard.py"
  python3 "$ROOT/scripts/verify-repository-topology.py"
fi

ensure_postgres
ensure_redis
assert_database_reset_is_explicit
flush_verification_redis
for database in "${DATABASES[@]}"; do
  reset_database "$database"
done

BFF_DATABASE_URL="${DATABASE_URLS[kokoro_gate_bff]}"
AGENT_DATABASE_URL="${DATABASE_URLS[kokoro_gate_agent]}"
IAM_DATABASE_URL="${DATABASE_URLS[kokoro_gate_iam]}"
SYSTEM_DATABASE_URL="${DATABASE_URLS[kokoro_gate_system]}"
MODEL_DATABASE_URL="${DATABASE_URLS[kokoro_gate_model]}"
BILLING_DATABASE_URL="${DATABASE_URLS[kokoro_gate_billing]}"
CAPABILITY_DATABASE_URL="${DATABASE_URLS[kokoro_gate_capability]}"
STORAGE_DATABASE_URL="${DATABASE_URLS[kokoro_gate_storage]}"
BFF_REDIS_URL="$(redis_url_for_db 8)"
AGENT_REDIS_URL="$(redis_url_for_db 9)"

log "Web quality, contract, architecture and browser gates"
(
  cd "$ROOT/kokoro"
  pnpm install --frozen-lockfile --prefer-offline
  pnpm contract
  pnpm test:architecture
  pnpm lint
  pnpm typecheck
  pnpm test
  pnpm build
  if [[ "$SKIP_E2E" != "1" ]]; then
    pnpm exec playwright install chromium
    pnpm test:e2e
  fi
)

log "BFF fresh schema and quality/integration gates"
(
  cd "$ROOT/kokoro-bff"
  pnpm install --frozen-lockfile --prefer-offline
  KOKORO_BFF_POSTGRES_URL="$BFF_DATABASE_URL" pnpm db:apply-schema
  KOKORO_BFF_MODE=mock KOKORO_BFF_POSTGRES_URL="$BFF_DATABASE_URL" KOKORO_BFF_REDIS_URL="$BFF_REDIS_URL" pnpm lint
  KOKORO_BFF_MODE=mock KOKORO_BFF_POSTGRES_URL="$BFF_DATABASE_URL" KOKORO_BFF_REDIS_URL="$BFF_REDIS_URL" pnpm typecheck
  pnpm contract:check
  KOKORO_BFF_MODE=mock KOKORO_BFF_POSTGRES_URL="$BFF_DATABASE_URL" KOKORO_BFF_REDIS_URL="$BFF_REDIS_URL" pnpm test
  KOKORO_BFF_MODE=live KOKORO_BFF_POSTGRES_URL="$BFF_DATABASE_URL" KOKORO_BFF_REDIS_URL="$BFF_REDIS_URL" \
    KOKORO_TEST_POSTGRES_URL="$BFF_DATABASE_URL" KOKORO_TEST_REDIS_URL="$BFF_REDIS_URL" pnpm test:integration
  pnpm build
)

log "Agent schema, strict Python and real PostgreSQL/Redis gates"
(
  cd "$ROOT/kokoro-agent"
  uv sync --frozen
  KOKORO_AGENT_DATABASE_URL="$AGENT_DATABASE_URL" KOKORO_AGENT_DATABASE_SCHEMA=kokoro_agent \
    KOKORO_REDIS_URL="$AGENT_REDIS_URL" uv run kokoro-agent-db-apply-schema
  uv run ruff check src tests
  uv run pyright
  uv run pytest -q
  uv run kokoro-agent-contract-check
  KOKORO_AGENT_DATABASE_URL="$AGENT_DATABASE_URL" KOKORO_AGENT_DATABASE_SCHEMA=kokoro_agent \
    KOKORO_REDIS_URL="$AGENT_REDIS_URL" uv run pytest -q -o addopts='' -m 'integration or acceptance'
  uv build --wheel --sdist
)

log "IAM fresh schema and owner gates"
(
  cd "$ROOT/kokoro-iam"
  pnpm install --frozen-lockfile --prefer-offline
  KOKORO_POSTGRES_URL="$IAM_DATABASE_URL" pnpm db:apply-schema
  KOKORO_POSTGRES_URL="$IAM_DATABASE_URL" KOKORO_REDIS_URL="$(redis_url_for_db 1)" pnpm verify
  KOKORO_POSTGRES_URL="$IAM_DATABASE_URL" KOKORO_REDIS_URL="$(redis_url_for_db 1)" pnpm test:integration
)

log "System fresh schema and owner gates"
(
  cd "$ROOT/kokoro-system"
  pnpm install --frozen-lockfile --prefer-offline
  DATABASE_URL="$SYSTEM_DATABASE_URL" pnpm db:apply-schema
  pnpm verify
  DATABASE_URL="$SYSTEM_DATABASE_URL" TEST_DATABASE_URL="$SYSTEM_DATABASE_URL" \
    REDIS_URL="$(redis_url_for_db 2)" TEST_REDIS_URL="$(redis_url_for_db 2)" \
    pnpm test:runtime-real-system
)

log "Model fresh schema and owner gates"
(
  cd "$ROOT/kokoro-model"
  pnpm install --frozen-lockfile --prefer-offline
  DATABASE_URL_MODEL="$MODEL_DATABASE_URL" pnpm db:apply-schema
  pnpm check
  pnpm verify:release
  DATABASE_URL_MODEL="$MODEL_DATABASE_URL" KOKORO_REDIS_URL="$(redis_url_for_db 3)" pnpm test:integration
)

log "Billing fresh schema and owner gates"
(
  cd "$ROOT/kokoro-billing"
  pnpm install --frozen-lockfile --prefer-offline
  DATABASE_URL="$BILLING_DATABASE_URL" pnpm db:apply-schema
  DATABASE_URL="$BILLING_DATABASE_URL" REDIS_URL="$(redis_url_for_db 4)" pnpm verify
  DATABASE_URL="$BILLING_DATABASE_URL" REDIS_URL="$(redis_url_for_db 4)" \
    REDIS_TEST_URL="$(redis_url_for_db 4)" pnpm test:integration
)

log "Capability fresh schema and owner gates"
(
  cd "$ROOT/kokoro-capability"
  pnpm install --frozen-lockfile --prefer-offline
  KOKORO_POSTGRES_URL="$CAPABILITY_DATABASE_URL" pnpm db:apply-schema
  KOKORO_POSTGRES_URL="$CAPABILITY_DATABASE_URL" KOKORO_REDIS_URL="$(redis_url_for_db 5)" pnpm verify
  KOKORO_POSTGRES_URL="$CAPABILITY_DATABASE_URL" KOKORO_REDIS_URL="$(redis_url_for_db 5)" pnpm smoke:production
)

log "Storage fresh schema and real infrastructure gates"
(
  cd "$ROOT/kokoro-storage"
  pnpm install --frozen-lockfile --prefer-offline
  KOKORO_POSTGRES_URL="$STORAGE_DATABASE_URL" pnpm db:apply-schema
  KOKORO_TEST_POSTGRES_URL="$STORAGE_DATABASE_URL" KOKORO_TEST_REDIS_URL="$(redis_url_for_db 6)" pnpm verify
  if [[ "$SKIP_EXTERNAL" != "1" ]]; then
    KOKORO_SMOKE_POSTGRES_URL="$STORAGE_DATABASE_URL" KOKORO_SMOKE_REDIS_URL="$(redis_url_for_db 6)" \
      KOKORO_SMOKE_S3_ENDPOINT="$S3_ENDPOINT" KOKORO_SMOKE_S3_ACCESS_KEY_ID="$S3_ACCESS_KEY_ID" \
      KOKORO_SMOKE_S3_SECRET_ACCESS_KEY="$S3_SECRET_ACCESS_KEY" pnpm smoke:infra
    KOKORO_SMOKE_S3_ENDPOINT="$S3_ENDPOINT" KOKORO_SMOKE_S3_ACCESS_KEY_ID="$S3_ACCESS_KEY_ID" \
      KOKORO_SMOKE_S3_SECRET_ACCESS_KEY="$S3_SECRET_ACCESS_KEY" KOKORO_SMOKE_SCANNER_HOST="$SCANNER_HOST" \
      KOKORO_SMOKE_SCANNER_PORT="$SCANNER_PORT" pnpm smoke:scanner
    KOKORO_OBJECT_STORE_ENDPOINT="$S3_ENDPOINT" KOKORO_OBJECT_STORE_BUCKET=kokoro \
      KOKORO_OBJECT_STORE_ACCESS_KEY_ID="$S3_ACCESS_KEY_ID" KOKORO_OBJECT_STORE_SECRET_ACCESS_KEY="$S3_SECRET_ACCESS_KEY" \
      pnpm smoke:s3
    KOKORO_SMOKE_POSTGRES_URL="$STORAGE_DATABASE_URL" KOKORO_SMOKE_REDIS_URL="$(redis_url_for_db 6)" \
      KOKORO_SMOKE_S3_ENDPOINT="$S3_ENDPOINT" KOKORO_SMOKE_S3_ACCESS_KEY_ID="$S3_ACCESS_KEY_ID" \
      KOKORO_SMOKE_S3_SECRET_ACCESS_KEY="$S3_SECRET_ACCESS_KEY" KOKORO_SMOKE_SCANNER_HOST="$SCANNER_HOST" \
      KOKORO_SMOKE_SCANNER_PORT="$SCANNER_PORT" pnpm smoke:capability-package
  fi
)

log "Scheduler format, race, vet, build and Redis gates"
(
  cd "$ROOT/kokoro-scheduler"
  test -z "$(gofmt -l .)"
  go mod verify
  SCHEDULER_REDIS_TEST_URL="$(redis_url_for_db 7)" go test ./...
  SCHEDULER_REDIS_TEST_URL="$(redis_url_for_db 7)" go test -race ./...
  go vet ./...
  go build -trimpath -o /tmp/kokoro-scheduler-ten-repository-gate ./cmd/scheduler
)

database_invariants() {
  local database="$1"
  local url="$2"
  local result
  result="$(psql "$url" -At -F '|' -v ON_ERROR_STOP=1 <<'SQL'
WITH user_namespaces AS (
  SELECT oid
  FROM pg_namespace
  WHERE nspname NOT IN ('pg_catalog', 'information_schema')
    AND nspname !~ '^pg_toast'
)
SELECT
  (SELECT count(*) FROM pg_class WHERE relnamespace IN (SELECT oid FROM user_namespaces) AND relkind = 'r'),
  (SELECT count(*) FROM pg_constraint WHERE connamespace IN (SELECT oid FROM user_namespaces) AND contype = 'f'),
  (SELECT count(*) FROM information_schema.columns WHERE table_schema NOT IN ('pg_catalog', 'information_schema') AND column_name ~ '_at$' AND data_type <> 'timestamp with time zone'),
  (SELECT count(*) FROM pg_constraint WHERE connamespace IN (SELECT oid FROM user_namespaces) AND contype = 'c' AND conname !~ '^ck_'),
  (SELECT count(*) FROM pg_constraint WHERE connamespace IN (SELECT oid FROM user_namespaces) AND contype = 'u' AND conname !~ '^uq_');
SQL
  )"
  local table_count foreign_key_count bad_time_count bad_check_count bad_unique_count
  IFS='|' read -r table_count foreign_key_count bad_time_count bad_check_count bad_unique_count <<<"$result"
  if [[ "$table_count" == "0" || "$foreign_key_count" != "0" || "$bad_time_count" != "0" || "$bad_check_count" != "0" || "$bad_unique_count" != "0" ]]; then
    die "database invariant failure ${database}: ${result}"
  fi
  printf 'database invariant pass %s: tables=%s fk=%s bad_time=%s bad_ck=%s bad_uq=%s\n' \
    "$database" "$table_count" "$foreign_key_count" "$bad_time_count" "$bad_check_count" "$bad_unique_count"
}

log "PostgreSQL schema invariants"
database_invariants kokoro_gate_bff "$BFF_DATABASE_URL"
database_invariants kokoro_gate_agent "$AGENT_DATABASE_URL"
database_invariants kokoro_gate_iam "$IAM_DATABASE_URL"
database_invariants kokoro_gate_system "$SYSTEM_DATABASE_URL"
database_invariants kokoro_gate_model "$MODEL_DATABASE_URL"
database_invariants kokoro_gate_billing "$BILLING_DATABASE_URL"
database_invariants kokoro_gate_capability "$CAPABILITY_DATABASE_URL"
database_invariants kokoro_gate_storage "$STORAGE_DATABASE_URL"

build_and_scan_images() {
  local image repository index
  local -a images=(
    kokoro-web:local-gate
    kokoro-bff:local-gate
    kokoro-agent:local-gate
    kokoro-iam:local-gate
    kokoro-system:local-gate
    kokoro-model:local-gate
    kokoro-billing:local-gate
    kokoro-capability:local-gate
    kokoro-storage:local-gate
    kokoro-scheduler:local-gate
  )
  local -a repositories=(
    kokoro
    kokoro-bff
    kokoro-agent
    kokoro-iam
    kokoro-system
    kokoro-model
    kokoro-billing
    kokoro-capability
    kokoro-storage
    kokoro-scheduler
  )
  docker volume create "$TRIVY_CACHE_VOLUME" >/dev/null
  for index in "${!repositories[@]}"; do
    repository="${repositories[$index]}"
    image="${images[$index]}"
    log "build candidate image ${image}"
    docker build --tag "$image" "$ROOT/$repository"
  done
  for image in "${images[@]}"; do
    log "scan candidate image ${image}"
    docker run --rm \
      --volume /var/run/docker.sock:/var/run/docker.sock \
      --volume "${TRIVY_CACHE_VOLUME}:/root/.cache" \
      "$TRIVY_IMAGE" image --scanners vuln --severity HIGH,CRITICAL --ignore-unfixed \
      --exit-code 1 --format table "$image"
  done
}

if [[ "$SKIP_IMAGES" == "1" ]]; then
  log "SKIP candidate image build/scan requested by KOKORO_FULL_SKIP_IMAGES=1"
else
  build_and_scan_images
fi

if [[ "$SKIP_E2E" != "1" ]]; then
  log "Root loopback BFF E2E"
  uv run --frozen python "$ROOT/scripts/e2e/run_stage2_bff_mock.py" \
    --evidence "${KOKORO_BFF_E2E_EVIDENCE:-/tmp/kokoro-stage2-bff-mock-e2e.json}"
fi

log "PASS full ten-repository verification"
