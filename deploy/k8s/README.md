# Kokoro k8s 部署

与单机 compose **同一套架构**（唯一一套基建 + URL 挂载的 app 层 + seed Jobs），翻译成 k8s。
Secret/ConfigMap 直接从 compose 用的同一批文件生成（`deploy/.env.prod` / `deploy/storage.yaml` /
litellm 配置），**k8s 与 compose 单源不漂移**。

## 拓扑（namespace `kokoro`，41 资源）

- **基建**（`infra.yaml`，各一个，Deployment+RWO PVC+Recreate+Service）：mysql / redis / mongo / minio / litellm
- **平台**（`platform.yaml`，共用 `kokoro-platform` 镜像 + `KOKORO_SERVICE_PACKAGE` 选包）：site/user/model/credit/payment/hub/platform-admin
- **应用**（`app.yaml`）：session / agent(worker,无 Service) / web + Ingress；workspace 用 **RWX PVC** 共享给 hub/session/agent
- **provisioning**（`jobs.yaml`）：`migrate` Job → `provision` Job（模型内置/运营/站点/计价/积分包，与 provision.sh 同序，幂等）

Service 名 = env URL 主机名（`mysql` / `kokoro-user` / …），故 `DATABASE_URL_*` / `*_BASE_URL` 与 compose 一字不差。

## 前置

1. **镜像**：`docker compose ... build` 出 `kokoro-platform:latest` / `kokoro-kokoro-{session,agent,web}:latest`，
   推到集群可拉的 registry（或 `kind load` / `minikube image load`）。真实 registry 在 `kustomization.yaml` 的
   `images:` 把 `newName` 改成你的仓库。
2. **env 单源**：`cp deploy/.env.example deploy/.env.prod` 填真值（服务名 URL：`mysql:3306` / `http://kokoro-user:4211`
   / `http://litellm:4000/v1`；auth=jwks + RS256 私钥；hub master key；等）。**不入库**。
3. **存储**：workspace 需 **RWX** storage class（nfs/cephfs/efs…）。单节点可用 hostPath PV 或 local-path + 单节点调度。

## 部署

```bash
# 渲染（generators 引用 deploy/ 下同源文件，需放开 load-restrictor）+ 应用：
kubectl kustomize --load-restrictor LoadRestrictionsNone deploy/k8s | kubectl apply -f -

# 观察就绪：
kubectl -n kokoro get pods -w

# provisioning：migrate/provision 是 Job；重跑需先删旧同名 Job：
kubectl -n kokoro delete job migrate provision --ignore-not-found
kubectl kustomize --load-restrictor LoadRestrictionsNone deploy/k8s | kubectl apply -f -
```

Ingress `host: kokoro.local`（`app.yaml`）按真实域名改，并与 `KOKORO_WEB_ORIGIN` / 站点 seed 对齐。

## 运维

- **改 Secret/ConfigMap 后**（`disableNameSuffixHash: true`，固定名不触发滚更）：
  `kubectl -n kokoro rollout restart deploy`（或按需重启特定 deploy）。
- **托管云库**：删 `infra.yaml` 里对应块，把 Secret 的 `DATABASE_URL_*` / redis / mongo / S3 指向云地址即可，app 层不变。
- **可观测（langfuse）**：与 compose 一致，作为独立观测栈（复用基建 redis+minio，自留 pg+ch），此处不含；
  接入见 `ops/langfuse/` 与 `deploy/.env.example` 的 `LANGFUSE_*`。

## 校验（离线，无需集群）

```bash
kubectl kustomize --load-restrictor LoadRestrictionsNone deploy/k8s | kubectl apply --dry-run=client -f -
```
