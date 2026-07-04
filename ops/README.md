# 本地基础设施（docker）

## searxng（web_search 开放标准 provider，零 key）
    docker run -d --name kokoro-searxng --restart unless-stopped -p 8888:8080 \
      -v "$PWD/ops/searxng/settings.yml:/etc/searxng/settings.yml:ro" searxng/searxng
agent .env: KOKORO_WEB_SEARCH_PROVIDER=searxng + KOKORO_WEB_SEARCH_URL=http://127.0.0.1:8888

## langfuse（trace，自托管 v3，headless init 密钥）
    cd ops/langfuse && cp .env.local .env && docker compose -p kokoro-langfuse up -d
UI http://localhost:3310（dev@kokoro.local / kokoro-dev-password）；
agent .env: LANGFUSE_PUBLIC_KEY/SECRET_KEY=pk/sk-lf-kokoro-local + LANGFUSE_HOST=http://127.0.0.1:3310
.env.local 仅本地开发凭据（非生产秘密）。

## e2e 依赖
    docker run -d --name kokoro-e2e-redis -p 6379:6379 redis:7-alpine
    docker run -d --name kokoro-e2e-mongo -p 27017:27017 mongo:7
