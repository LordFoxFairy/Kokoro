# Kokoro 单机全栈部署（docker-compose）

一台主机上用 `docker compose` 起全栈：infra（mysql/mongo/redis/minio）+ 平台七服务 + session/agent/web + litellm 网关。
编排文件：仓库根 `docker-compose.prod.yml`。变量模板：`deploy/.env.example`。

> 目标形态之一（单机）。k8s 形态见 `kokoro-platform/deploy/k8s/`（上线任务 #56 补平中）。

## 前置
- Docker + Docker Compose v2
- 域名（web 对外）+ 反代/TLS（compose 只暴露端口，TLS 由前置 nginx/caddy 承载）

## 步骤

### 1. 配置
```bash
cp deploy/.env.example deploy/.env
```
把 `deploy/.env` 里所有 `CHANGE_ME` 换成真值：

- **内部服务凭据**（6 个 `KOKORO_INTERNAL_SECRET_*`）+ **web 信封密钥** + **mock webhook secret**：各生成独立强随机
  ```bash
  openssl rand -hex 32
  ```
- **RS256 签发私钥**（`KOKORO_USER_JWT_PRIVATE_KEY`）：
  ```bash
  openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 -out user_jwt.pem
  # 填入 .env 时单行化（PEM 换行转 \n），或改用支持多行的 env 注入方式
  ```
- **MySQL 密码**：`MYSQL_ROOT_PASSWORD` 与所有 `DATABASE_URL_*` 里的密码保持一致
- **KOKORO_SITE_ID**：与下方 seed 的站点一致（`site-<key>`）
- **KOKORO_WEB_ORIGIN**：真实对外域名

### 2. 起栈
```bash
docker compose -f docker-compose.prod.yml up -d --build
```
`migrate` 一次性服务先跑完 `prisma migrate deploy`（各平台 DB），平台服务才启动。首次构建较慢（多镜像）。

### 3. 首次 provisioning（起栈后一次性）
- **站点**：调 site 服务 upsert 建站点（key 与 `KOKORO_SITE_ID` 对应），令 host→site 解析生效
- **平台内置目录**：model `seed:builtin`（内置默认模型 label）
- **首个 admin operator**：platform-admin 初期用 `KOKORO_ADMIN_AUTH_MODE=dev`（固定 operator，无真鉴权）——仅用于首次进后台；**生产务必切 `oidc` 或 `proxy`**（见 .env 注释）
- （定价/积分包 seed：接真收费前按需，参考 `scripts/closure-up.py` 的 seed 段）

### 4. 验证
```bash
docker compose -f docker-compose.prod.yml ps        # 各服务 healthy/running
curl -fsS http://<host>:4211/healthz                # user 健康
curl -fsS http://<host>:3900/metrics | head         # session 指标
# 浏览器开 http://<host>:3000 → 落地页 → 登录（magic-link 现走 log 档,链接看 user 服务日志）
docker compose -f docker-compose.prod.yml logs kokoro-user | grep magic
```

## 上线硬化清单（部署跑通后）
- [ ] `KOKORO_ADMIN_AUTH_MODE` dev → oidc/proxy（真后台鉴权）
- [ ] SMTP 接入 → `KOKORO_AUTH_MAGIC_DELIVERY=log` 改 `smtp`（登录邮件真发；任务 #57）
- [ ] 真模型：`KOKORO_LOCAL_FAKE_MODEL=1`→`0` + litellm 配 provider 凭据（GLM 等，归 kokoro-model）
- [ ] 真支付网关（有商户后；当前 mock 闭环）
- [ ] 前置 TLS 反代 + 仅暴露 web:3000 / admin:4290 到可信网络
- [ ] DB/Redis/Mongo 备份策略；卷（kokoro-mysql/mongo/redis/workspace）持久化确认

## 说明
- **存储**：workspace/deliveries/hub 包体用共享本地卷 `kokoro-workspace`（`deploy/storage.prod.yaml`，单机口径）。多机改 S3（minio 已在编排）。
- **计费**：生产 `KOKORO_BILLING_MODE=enforce`（余额不足拒 run）。
- **MCP egress**：生产 `KOKORO_MCP_EGRESS_MODE=strict`（拒私网/环回，防 SSRF）。
- **端口**：web 3000 / session 3900 / litellm 4000 / 平台 4201-4251 / admin 4290。生产只把 web、必要时 admin 暴露到公网，其余留内网。
