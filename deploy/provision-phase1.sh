#!/usr/bin/env bash
# Kokoro Phase 1 deployment: only PostgreSQL + Redis + Web/BFF/Agent.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
ENV_FILE="${1:-deploy/.env.phase1.prod}"
[[ -f "$ENV_FILE" ]] || { echo "环境文件不存在：$ENV_FILE（cp deploy/.env.phase1.example $ENV_FILE 后填值）" >&2; exit 1; }
ENV_FILE="$(cd "$(dirname "$ENV_FILE")" && pwd)/$(basename "$ENV_FILE")"
export KOKORO_ENV_FILE="$ENV_FILE"

COMPOSE=(docker compose --env-file "$ENV_FILE" -p "${KOKORO_PHASE1_PROJECT:-kokoro-phase1}" -f deploy/docker-compose.phase1.yml)
"${COMPOSE[@]}" up -d --build

wait_http() {
  local name="$1" url="$2" i code
  for i in $(seq 1 60); do
    # Web redirects `/` to `/app`; follow the redirect so readiness reflects the
    # actual application route rather than failing on a valid 307 response.
    code="$(curl -L -s -o /dev/null -w '%{http_code}' --max-time 5 "$url" || true)"
    [[ "$code" == "200" ]] && { echo "    $name OK"; return 0; }
    sleep 2
  done
  echo "    $name 未就绪（HTTP $code）" >&2
  return 1
}

WEB_PORT="$("${COMPOSE[@]}" port kokoro-app 3000 | tail -n 1 | awk -F: '{print $NF}')"
[[ -n "$WEB_PORT" ]] || { echo "kokoro-app 发布端口解析失败" >&2; exit 1; }
wait_http kokoro-bff "http://127.0.0.1:4300/healthz"
wait_http kokoro-app "http://127.0.0.1:${WEB_PORT}/"
echo "Phase 1 ready: http://127.0.0.1:${WEB_PORT}/ (domain is configured by KOKORO_DOMAIN in ${ENV_FILE})"
