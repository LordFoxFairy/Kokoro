#!/usr/bin/env bash
set -euo pipefail

: "${KOKORO_API_BASE_URL:?Set KOKORO_API_BASE_URL}"
: "${KOKORO_API_TOKEN:?Set KOKORO_API_TOKEN}"
: "${KOKORO_NAMESPACE:?Set KOKORO_NAMESPACE}"
: "${KOKORO_PRINCIPAL_ID:?Set KOKORO_PRINCIPAL_ID}"
: "${KOKORO_SESSION_ID:?Set KOKORO_SESSION_ID}"
: "${KOKORO_RUN_ID:?Set KOKORO_RUN_ID}"

curl --silent --show-error --fail-with-body \
  --request POST \
  "${KOKORO_API_BASE_URL}/v1/sessions/${KOKORO_SESSION_ID}/runs/${KOKORO_RUN_ID}/control" \
  --header "content-type: application/json" \
  --header "x-kokoro-service: web-bff" \
  --header "x-kokoro-internal-secret: ${KOKORO_API_TOKEN}" \
  --header "x-kokoro-namespace: ${KOKORO_NAMESPACE}" \
  --header "x-kokoro-principal-id: ${KOKORO_PRINCIPAL_ID}" \
  --header "idempotency-key: example-cancel-run-001" \
  --data '{"kind":"run.cancel"}'

printf '\n'
