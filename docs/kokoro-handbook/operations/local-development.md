# 本地开发

## 启动顺序

按依赖自底向上启动，先基础设施，再平台，再运行时：

```text
1. 基础设施   MySQL、Redis、Mongo（可选）。
2. 平台服务   kokoro-site / user / model / credit / payment。
3. 会话层     kokoro-session。
4. 执行层     kokoro-agent（先 fake model）。
5. 界面层     kokoro-web（先 simulator 降级）。
```

## 依赖就绪

```text
- [ ] MySQL 可连接，database=kokoro 已建。
- [ ] Redis 可连接。
- [ ] Mongo 可连接（需要持久化 session/产物时）。
- [ ] 各 TS 仓 pnpm install / 各服务依赖就绪。
- [ ] kokoro-agent 用 uv sync（Python）。
- [ ] 平台各服务 GET /healthz 返回 ready。
```

## 调试顺序

逐层确认，避免一次性接真实 provider 难以定位：

```text
1. platform healthz   各平台服务 /healthz。
2. session health     session 起得来、能连 Redis/Mongo。
3. agent fake model    用 fake model 跑通 run 主链路，不烧 token。
4. web simulator       后端不可达时确认 simulator 降级正常。
5. 真实 provider       接入真实 model/provider，验证扣费闭环。
```

## 常见 env

```text
平台:
  KOKORO_SITE_BASE_URL / KOKORO_USER_BASE_URL / KOKORO_MODEL_BASE_URL /
  KOKORO_CREDIT_BASE_URL / KOKORO_PAYMENT_BASE_URL
  DATABASE_URL_*（各子仓独立连接串，指向同一 database=kokoro）

运行时:
  NEXT_PUBLIC_KOKORO_SESSION_BASE_URL
  KOKORO_STREAM_BACKEND / KOKORO_REDIS_URL
  KOKORO_MESSAGE_STORE_BACKEND / KOKORO_MESSAGE_STORE_MONGO_URL
  KOKORO_AGENT_RUN_STATE_BACKEND
```

具体端口/服务名见 [docker-and-k8s](docker-and-k8s.md) 与 [deployment](../technical/08-deployment.md)。

## 红线

```text
不要新增 kokoro-contracts。
不要创建 ports/ 目录命名。
不要引入 PostgreSQL。
不要把积分余额、payment event 状态、agent run 放进单进程内存。
```
