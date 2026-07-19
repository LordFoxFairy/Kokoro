#!/usr/bin/env bash
# Kokoro prod 一键编排：先起「唯一一套基建」，再起业务(拿 URL 连基建)，最后幂等 seed。
#
# 架构：基建(docker-compose.infra.yml)与业务(docker-compose.app.yml)是两个独立 compose 项目，
# 经命名网络 ${KOKORO_NETWORK:-kokoro-net} 相连；业务不自带任何 infra，一律 env URL 挂载。
#
# 用法：deploy/provision.sh [ENV_FILE] [APP_PROJECT] [INFRA_PROJECT]
#   ENV_FILE       默认 deploy/.env.prod（.env.* 受 .gitignore 保护，不入库）
#   APP_PROJECT    默认 kokoro
#   INFRA_PROJECT  默认 kokoro-infra
#
# dev 不用本脚本（dev 走 scripts/closure-up.py：同样起 infra.yml，再跑 host 进程）。
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

ENV_FILE="${1:-deploy/.env.prod}"
APP_PROJECT="${2:-kokoro}"
INFRA_PROJECT="${3:-kokoro-infra}"

[[ -f "$ENV_FILE" ]] || { echo "环境文件不存在：$ENV_FILE（cp deploy/.env.example $ENV_FILE 后填值）" >&2; exit 1; }
export KOKORO_ENV_FILE="$ENV_FILE"

INFRA=(docker compose --env-file "$ENV_FILE" -p "$INFRA_PROJECT" -f docker-compose.infra.yml)
APP=(docker compose --env-file "$ENV_FILE" -p "$APP_PROJECT" -f docker-compose.app.yml)

echo "==> [1/4] 起唯一一套基建（mysql/redis/mongo/minio/litellm），等 mysql 就绪"
"${INFRA[@]}" up -d
# 等 mysql 健康（migrate 要连它）。
for i in $(seq 1 60); do
  st="$("${INFRA[@]}" ps --format '{{.Health}}' mysql 2>/dev/null | head -1 || true)"
  [[ "$st" == "healthy" ]] && { echo "    mysql healthy"; break; }
  sleep 2
done

echo "==> [2/4] 迁移（业务 migrate 一次性服务，拿 URL 连基建跑 prisma migrate deploy）"
"${APP[@]}" build
"${APP[@]}" run --rm migrate

echo "==> [3/4] 起业务服务（平台 7 + session + agent + web）"
"${APP[@]}" up -d

# 等平台服务 healthz。
wait_healthz() { local n="$1" p="$2" i c; for i in $(seq 1 60); do
  c="$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 "http://localhost:${p}/healthz" 2>/dev/null || true)"
  [[ "$c" == "200" ]] && { echo "    $n OK"; return 0; }; sleep 3; done
  echo "    $n 未就绪(HTTP $c)" >&2; return 1; }
wait_healthz kokoro-site 4201 || true
wait_healthz kokoro-model 4221 || true
wait_healthz kokoro-platform-admin 4290 || true

echo "==> [4/4] 幂等 seed（模型内置 / 运营数据 / 默认站点 active）"
"${APP[@]}" exec -T kokoro-model sh -lc "pnpm --filter @kokoro/model seed:builtin"
"${APP[@]}" exec -T kokoro-platform-admin sh -lc "pnpm --filter @kokoro/platform-admin db:seed"
"${APP[@]}" exec -T kokoro-site sh -lc "pnpm --filter @kokoro/site seed:site"

echo "==> 完成。web http://localhost:${KOKORO_WEB_HOST_PORT:-3000}"
