#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PG_ADMIN_URL="${KOKORO_VERIFY_POSTGRES_ADMIN_URL:-postgresql://kokoro:kokoro@127.0.0.1:55433/postgres}"
REDIS_BASE_URL="${KOKORO_VERIFY_REDIS_URL:-redis://127.0.0.1:56380}"
S3_ENDPOINT="${KOKORO_VERIFY_S3_ENDPOINT:-http://127.0.0.1:39190}"
S3_ACCESS_KEY_ID="${KOKORO_VERIFY_S3_ACCESS_KEY_ID:-kokoro-test}"
S3_SECRET_ACCESS_KEY="${KOKORO_VERIFY_S3_SECRET_ACCESS_KEY:-kokoro-test-secret}"
SCANNER_HOST="${KOKORO_VERIFY_SCANNER_HOST:-127.0.0.1}"
SCANNER_PORT="${KOKORO_VERIFY_SCANNER_PORT:-43310}"
STORAGE_DOCKER_NETWORK="${KOKORO_VERIFY_STORAGE_DOCKER_NETWORK:-storage-deps_default}"
TRIVY_IMAGE="${KOKORO_VERIFY_TRIVY_IMAGE:-aquasec/trivy@sha256:bcc376de8d77cfe086a917230e818dc9f8528e3c852f7b1aff648949b6258d1c}"
TRIVY_CACHE_VOLUME="${KOKORO_VERIFY_TRIVY_CACHE_VOLUME:-kokoro-seven-repository-trivy-cache}"

readonly DATABASES=(
  kokoro_gate_iam
  kokoro_gate_system
  kokoro_gate_model
  kokoro_gate_billing
  kokoro_gate_capability
  kokoro_gate_storage
)

database_url() {
  python3 - "$PG_ADMIN_URL" "$1" <<'PY'
import sys
from urllib.parse import urlsplit, urlunsplit

source = urlsplit(sys.argv[1])
print(urlunsplit((source.scheme, source.netloc, f"/{sys.argv[2]}", source.query, source.fragment)))
PY
}

reset_database() {
  local database="$1"
  psql "$PG_ADMIN_URL" -v ON_ERROR_STOP=1 \
    -c "DROP DATABASE IF EXISTS \"${database}\" WITH (FORCE)" \
    -c "CREATE DATABASE \"${database}\"" >/dev/null
}

cleanup() {
  for database in "${DATABASES[@]}"; do
    psql "$PG_ADMIN_URL" -v ON_ERROR_STOP=1 \
      -c "DROP DATABASE IF EXISTS \"${database}\" WITH (FORCE)" >/dev/null 2>&1 || true
  done
  rm -f /tmp/kokoro-{iam,system,model,billing,capability,storage}-reapply.log
}
trap cleanup EXIT

for command in psql redis-cli python3 pnpm go docker; do
  command -v "$command" >/dev/null || {
    printf 'required command is missing: %s\n' "$command" >&2
    exit 1
  }
done

docker volume create "$TRIVY_CACHE_VOLUME" >/dev/null

redis-cli -u "${REDIS_BASE_URL}/15" PING >/dev/null
for redis_database in {1..7}; do
  redis-cli -u "${REDIS_BASE_URL}/${redis_database}" FLUSHDB >/dev/null
done
for database in "${DATABASES[@]}"; do
  reset_database "$database"
done

IAM_DATABASE_URL="$(database_url kokoro_gate_iam)"
SYSTEM_DATABASE_URL="$(database_url kokoro_gate_system)"
MODEL_DATABASE_URL="$(database_url kokoro_gate_model)"
BILLING_DATABASE_URL="$(database_url kokoro_gate_billing)"
CAPABILITY_DATABASE_URL="$(database_url kokoro_gate_capability)"
STORAGE_DATABASE_URL="$(database_url kokoro_gate_storage)"
STORAGE_DOCKER_DATABASE_URL="${STORAGE_DATABASE_URL/127.0.0.1/host.docker.internal}"
STORAGE_DOCKER_REDIS_URL="${REDIS_BASE_URL/127.0.0.1/host.docker.internal}/6"

python3 "$ROOT/scripts/verify-ten-repository-standard.py"
python3 "$ROOT/scripts/verify-repository-topology.py"

(
  cd "$ROOT/kokoro-iam"
  KOKORO_POSTGRES_URL="$IAM_DATABASE_URL" pnpm db:apply-schema
  if KOKORO_POSTGRES_URL="$IAM_DATABASE_URL" pnpm db:apply-schema >/tmp/kokoro-iam-reapply.log 2>&1; then
    echo "IAM schema reapply unexpectedly succeeded" >&2; exit 1
  fi
  grep -q "requires a blank database" /tmp/kokoro-iam-reapply.log
  KOKORO_POSTGRES_URL="$IAM_DATABASE_URL" KOKORO_REDIS_URL="${REDIS_BASE_URL}/1" pnpm verify
  KOKORO_POSTGRES_URL="$IAM_DATABASE_URL" KOKORO_REDIS_URL="${REDIS_BASE_URL}/1" pnpm test:integration
  docker build --tag kokoro-iam:local-gate .
)

(
  cd "$ROOT/kokoro-system"
  DATABASE_URL="$SYSTEM_DATABASE_URL" pnpm db:apply-schema
  if DATABASE_URL="$SYSTEM_DATABASE_URL" pnpm db:apply-schema >/tmp/kokoro-system-reapply.log 2>&1; then
    echo "System schema reapply unexpectedly succeeded" >&2; exit 1
  fi
  grep -q "requires a blank database" /tmp/kokoro-system-reapply.log
  pnpm verify
  DATABASE_URL="$SYSTEM_DATABASE_URL" TEST_DATABASE_URL="$SYSTEM_DATABASE_URL" \
    REDIS_URL="${REDIS_BASE_URL}/2" TEST_REDIS_URL="${REDIS_BASE_URL}/2" \
    pnpm test:runtime-real-system
  docker build --tag kokoro-system:local-gate .
)

(
  cd "$ROOT/kokoro-model"
  DATABASE_URL_MODEL="$MODEL_DATABASE_URL" pnpm db:apply-schema
  if DATABASE_URL_MODEL="$MODEL_DATABASE_URL" pnpm db:apply-schema >/tmp/kokoro-model-reapply.log 2>&1; then
    echo "Model schema reapply unexpectedly succeeded" >&2; exit 1
  fi
  grep -q "requires a blank database" /tmp/kokoro-model-reapply.log
  pnpm check
  pnpm verify:release
  DATABASE_URL_MODEL="$MODEL_DATABASE_URL" KOKORO_REDIS_URL="${REDIS_BASE_URL}/3" \
    pnpm test:integration
  docker build --tag kokoro-model:local-gate .
)

(
  cd "$ROOT/kokoro-billing"
  DATABASE_URL="$BILLING_DATABASE_URL" pnpm db:apply-schema
  if DATABASE_URL="$BILLING_DATABASE_URL" pnpm db:apply-schema >/tmp/kokoro-billing-reapply.log 2>&1; then
    echo "Billing schema reapply unexpectedly succeeded" >&2; exit 1
  fi
  grep -q "requires a blank database" /tmp/kokoro-billing-reapply.log
  pnpm verify
  DATABASE_URL="$BILLING_DATABASE_URL" REDIS_URL="${REDIS_BASE_URL}/4" \
    REDIS_TEST_URL="${REDIS_BASE_URL}/4" pnpm test:integration
  docker build --tag kokoro-billing:local-gate .
)

(
  cd "$ROOT/kokoro-capability"
  KOKORO_POSTGRES_URL="$CAPABILITY_DATABASE_URL" pnpm db:apply-schema
  if KOKORO_POSTGRES_URL="$CAPABILITY_DATABASE_URL" pnpm db:apply-schema >/tmp/kokoro-capability-reapply.log 2>&1; then
    echo "Capability schema reapply unexpectedly succeeded" >&2; exit 1
  fi
  grep -q "requires a blank database" /tmp/kokoro-capability-reapply.log
  pnpm verify
  KOKORO_POSTGRES_URL="$CAPABILITY_DATABASE_URL" KOKORO_REDIS_URL="${REDIS_BASE_URL}/5" \
    pnpm test:integration
  pnpm lint
  pnpm build
  KOKORO_POSTGRES_URL="$CAPABILITY_DATABASE_URL" KOKORO_REDIS_URL="${REDIS_BASE_URL}/5" \
    pnpm smoke:production
  docker build --tag kokoro-capability:local-gate .
)

(
  cd "$ROOT/kokoro-storage"
  KOKORO_POSTGRES_URL="$STORAGE_DATABASE_URL" pnpm db:apply-schema
  if KOKORO_POSTGRES_URL="$STORAGE_DATABASE_URL" pnpm db:apply-schema >/tmp/kokoro-storage-reapply.log 2>&1; then
    echo "Storage schema reapply unexpectedly succeeded" >&2; exit 1
  fi
  grep -q "requires a blank database" /tmp/kokoro-storage-reapply.log
  KOKORO_TEST_POSTGRES_URL="$STORAGE_DATABASE_URL" \
    KOKORO_TEST_REDIS_URL="${REDIS_BASE_URL}/6" \
    pnpm verify
  pnpm lint
  pnpm build
  KOKORO_SMOKE_POSTGRES_URL="$STORAGE_DATABASE_URL" \
    KOKORO_SMOKE_REDIS_URL="${REDIS_BASE_URL}/6" \
    KOKORO_SMOKE_S3_ENDPOINT="$S3_ENDPOINT" \
    KOKORO_SMOKE_S3_ACCESS_KEY_ID="$S3_ACCESS_KEY_ID" \
    KOKORO_SMOKE_S3_SECRET_ACCESS_KEY="$S3_SECRET_ACCESS_KEY" \
    pnpm smoke:infra
  KOKORO_SMOKE_S3_ENDPOINT="$S3_ENDPOINT" \
    KOKORO_SMOKE_S3_ACCESS_KEY_ID="$S3_ACCESS_KEY_ID" \
    KOKORO_SMOKE_S3_SECRET_ACCESS_KEY="$S3_SECRET_ACCESS_KEY" \
    KOKORO_SMOKE_SCANNER_HOST="$SCANNER_HOST" \
    KOKORO_SMOKE_SCANNER_PORT="$SCANNER_PORT" \
    pnpm smoke:scanner
  KOKORO_OBJECT_STORE_ENDPOINT="$S3_ENDPOINT" \
    KOKORO_OBJECT_STORE_BUCKET=kokoro \
    KOKORO_OBJECT_STORE_ACCESS_KEY_ID="$S3_ACCESS_KEY_ID" \
    KOKORO_OBJECT_STORE_SECRET_ACCESS_KEY="$S3_SECRET_ACCESS_KEY" \
    pnpm smoke:s3
  KOKORO_SMOKE_POSTGRES_URL="$STORAGE_DATABASE_URL" \
    KOKORO_SMOKE_REDIS_URL="${REDIS_BASE_URL}/6" \
    KOKORO_SMOKE_S3_ENDPOINT="$S3_ENDPOINT" \
    KOKORO_SMOKE_S3_ACCESS_KEY_ID="$S3_ACCESS_KEY_ID" \
    KOKORO_SMOKE_S3_SECRET_ACCESS_KEY="$S3_SECRET_ACCESS_KEY" \
    KOKORO_SMOKE_SCANNER_HOST="$SCANNER_HOST" \
    KOKORO_SMOKE_SCANNER_PORT="$SCANNER_PORT" \
    pnpm smoke:capability-package
  docker build --tag kokoro-storage:local-gate .
  KOKORO_DOCKER_SMOKE_NETWORK="$STORAGE_DOCKER_NETWORK" \
    KOKORO_DOCKER_SMOKE_POSTGRES_URL="$STORAGE_DOCKER_DATABASE_URL" \
    KOKORO_DOCKER_SMOKE_REDIS_URL="$STORAGE_DOCKER_REDIS_URL" \
    KOKORO_DOCKER_SMOKE_HOST_POSTGRES_URL="$STORAGE_DATABASE_URL" \
    KOKORO_DOCKER_SMOKE_HOST_REDIS_URL="${REDIS_BASE_URL}/6" \
    KOKORO_DOCKER_SMOKE_HOST_S3_ENDPOINT="$S3_ENDPOINT" \
    KOKORO_DOCKER_SMOKE_S3_ACCESS_KEY_ID="$S3_ACCESS_KEY_ID" \
    KOKORO_DOCKER_SMOKE_S3_SECRET_ACCESS_KEY="$S3_SECRET_ACCESS_KEY" \
    ./scripts/docker-smoke.sh kokoro-storage:local-gate
)

(
  cd "$ROOT/kokoro-scheduler"
  test -z "$(gofmt -l .)"
  go mod verify
  SCHEDULER_REDIS_TEST_URL="${REDIS_BASE_URL}/7" go test ./...
  SCHEDULER_REDIS_TEST_URL="${REDIS_BASE_URL}/7" go test -race ./...
  go vet ./...
  go build -trimpath -o /tmp/kokoro-scheduler-gate ./cmd/scheduler
  docker build --tag kokoro-scheduler:local-gate .
)

for image in \
  kokoro-iam:local-gate \
  kokoro-system:local-gate \
  kokoro-model:local-gate \
  kokoro-billing:local-gate \
  kokoro-capability:local-gate \
  kokoro-storage:local-gate \
  kokoro-scheduler:local-gate; do
  docker run --rm \
    --volume /var/run/docker.sock:/var/run/docker.sock \
    --volume "${TRIVY_CACHE_VOLUME}:/root/.cache" \
    "$TRIVY_IMAGE" image \
      --scanners vuln \
      --severity HIGH,CRITICAL \
      --ignore-unfixed \
      --exit-code 1 \
      --format table \
      "$image"
done

for mapping in \
  "kokoro_gate_iam:$IAM_DATABASE_URL" \
  "kokoro_gate_system:$SYSTEM_DATABASE_URL" \
  "kokoro_gate_model:$MODEL_DATABASE_URL" \
  "kokoro_gate_billing:$BILLING_DATABASE_URL" \
  "kokoro_gate_capability:$CAPABILITY_DATABASE_URL" \
  "kokoro_gate_storage:$STORAGE_DATABASE_URL"; do
  database="${mapping%%:*}"
  url="${mapping#*:}"
  result="$(psql "$url" -At -F '|' <<'SQL'
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
  IFS='|' read -r table_count foreign_key_count bad_time_count bad_check_count bad_unique_count <<<"$result"
  if [[ "$table_count" == "0" || "$foreign_key_count" != "0" || "$bad_time_count" != "0" || "$bad_check_count" != "0" || "$bad_unique_count" != "0" ]]; then
    printf 'database invariant failure %s: %s\n' "$database" "$result" >&2
    exit 1
  fi
  printf 'database invariant pass %s: tables=%s fk=%s bad_time=%s bad_ck=%s bad_uq=%s\n' \
    "$database" "$table_count" "$foreign_key_count" "$bad_time_count" "$bad_check_count" "$bad_unique_count"
done

printf 'PASS full seven-repository verification\n'
