#!/usr/bin/env bash
set -euo pipefail

: "${KOKORO_API_BASE_URL:?Set KOKORO_API_BASE_URL}"
: "${KOKORO_API_TOKEN:?Set KOKORO_API_TOKEN}"
: "${KOKORO_NAMESPACE:?Set KOKORO_NAMESPACE}"
: "${KOKORO_PRINCIPAL_ID:?Set KOKORO_PRINCIPAL_ID}"
: "${KOKORO_PROJECT_ID:?Set KOKORO_PROJECT_ID}"
: "${EXAMPLE_FILE:?Set EXAMPLE_FILE to a local file}"

curl --silent --show-error --fail-with-body \
  --request POST \
  "${KOKORO_API_BASE_URL}/v1/projects/${KOKORO_PROJECT_ID}/resources" \
  --header "x-kokoro-service: web-bff" \
  --header "x-kokoro-internal-secret: ${KOKORO_API_TOKEN}" \
  --header "x-kokoro-namespace: ${KOKORO_NAMESPACE}" \
  --header "x-kokoro-principal-id: ${KOKORO_PRINCIPAL_ID}" \
  --header "idempotency-key: example-upload-resource-001" \
  --form "files=@${EXAMPLE_FILE}"

printf '\n'
