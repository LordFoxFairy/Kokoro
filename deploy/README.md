# Kokoro 单机全栈部署（docker-compose）

一台主机上用 `docker compose` 起全栈：infra（mysql/mongo/redis/minio/litellm）+ 平台七服务 + session/agent/web。
架构=基建与业务两个独立 compose 项目，经命名网络 `kokoro-net` 相连：
- 基建：`docker-compose.infra.yml`（唯一一套 mysql/redis/mongo/minio/litellm）。
- 业务：`docker-compose.app.yml`（migrate + 7 平台服务 + session/agent/web，一律 env URL 连基建）。
- **一键编排：`deploy/provision.sh`**（infra→build→migrate→服务→幂等 seed，全流程）。变量模板：`deploy/.env.example`。

> 目标形态之一（单机）。k8s 形态见 `kokoro-platform/deploy/k8s/`。

## 前置
- Docker + Docker Compose v2
- 域名（web 对外）+ 反代/TLS（compose 只暴露端口，TLS 由前置 nginx/caddy 承载）

## 步骤

### 1. 配置
```bash
cp deploy/.env.example deploy/.env.prod   # provision.sh 默认读 deploy/.env.prod（.env.* 已 gitignore）
```
把 `deploy/.env.prod` 里所有 `CHANGE_ME` 换成真值：

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

### 2. 起栈（一键）
```bash
bash deploy/provision.sh deploy/.env.prod
```
脚本按序：① 起基建 + 等 mysql healthy + 幂等建 S3 桶；② `docker compose ... build` 全镜像 + `run --rm migrate`（各平台 DB `prisma migrate deploy`）；③ 起 7 平台服务 + session/agent/web + 等 healthz；④ 幂等 seed（model 内置目录 / 运营数据 / 站点 active / 计价 / 积分包+mock 网关）。首次构建较慢（多镜像）。

> 手动分步（等价）：`docker compose --env-file deploy/.env.prod -p kokoro-infra -f docker-compose.infra.yml up -d` → `docker compose --env-file deploy/.env.prod -p kokoro -f docker-compose.app.yml build && ... run --rm migrate && ... up -d`。

### 3. 站点绑定（首次一次性；seed 已建站点，此步确认 host→site 解析）
- provision.sh 的 seed 已建站点（key 与 `KOKORO_SITE_ID` 对应）。多域名/自定义站点在 admin 后台补域名绑定。
- **首个 admin operator**：初期 `KOKORO_ADMIN_AUTH_MODE=dev`（固定 operator，无真鉴权），仅用于首次进后台；**生产务必切 `oidc`/`proxy`**（见 .env 注释）。

### 4. 验证
```bash
docker compose --env-file deploy/.env.prod -p kokoro -f docker-compose.app.yml ps   # 各服务 running
curl -fsS http://<host>:4211/healthz                # user 健康(平台服务同法:4201/4221/4231/4241/4251/4290)
curl -fsS http://<host>:3900/metrics | head         # session 指标(session 亦有 /healthz)
# 浏览器开 http://<host>:3000 → 落地页 → 登录（magic-link 现走 log 档,链接看 user 服务日志）
docker compose --env-file deploy/.env.prod -p kokoro -f docker-compose.app.yml logs kokoro-user | grep magic
```

## 上线硬化清单（部署跑通后）
- [ ] `KOKORO_ADMIN_AUTH_MODE` dev → oidc/proxy（真后台鉴权）
- [ ] SMTP 接入 → `KOKORO_AUTH_MAGIC_DELIVERY=log` 改 `smtp`（登录邮件真发；任务 #57）
- [ ] 真模型：`KOKORO_LOCAL_FAKE_MODEL=1`→`0` + litellm 配 provider 凭据（GLM 等，归 kokoro-model）
- [ ] 真支付网关（有商户后；当前 mock 闭环）
- [ ] 前置 TLS 反代 + 仅暴露 web:3000 / admin:4290 到可信网络
- [ ] DB/Redis/Mongo 备份策略；卷（kokoro-mysql/mongo/redis/workspace）持久化确认

## 说明
- **存储**：workspace/deliveries/hub 包体默认用共享本地卷（`deploy/storage.yaml`，单机口径）。横向扩展/多 pod/多机切 S3：设 `KOKORO_STORAGE_FILE=./deploy/storage.s3.yaml` + `KOKORO_WORKSPACE_S3_ACCESS_KEY/SECRET_KEY`（取 minio root 账密）；桶 `kokoro` 由 `provision.sh` 幂等创建。S3 路径已对真 minio 往返验证（package put/get+幂等、workspace archive 键布局）。
- **计费**：生产 `KOKORO_BILLING_MODE=enforce`（余额不足拒 run）。
- **MCP egress**：生产 `KOKORO_MCP_EGRESS_MODE=strict`（拒私网/环回，防 SSRF）。
- **端口**：web 3000 / session 3900 / litellm 4000 / 平台 4201-4251 / admin 4290。生产只把 web、必要时 admin 暴露到公网，其余留内网。
