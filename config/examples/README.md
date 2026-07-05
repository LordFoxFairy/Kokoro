# 配置参考模板（ADR-010）

复制最贴近的模板改路径即用。优先级恒为 **env > yaml > 内置默认**；凭据（api key/secret）
永远只走 env/secret 注入，写进 yaml 会 fail-loud。

| 文件 | 给谁 | 场景 |
|---|---|---|
| `agent.example.full.yaml` | agent（`KOKORO_AGENT_CONFIG`） | 全量配置树注释版（照抄裁剪） |
| `workspace.example.local.yaml` | session+agent（`KOKORO_WORKSPACE_CONFIG`） | 单节点/共享卷文件面（=不配时的默认） |
| `workspace.example.s3.yaml` | 同上 | 对象存储归档档（minio/AWS） |
| `assets.example.local.yaml` | agent（`KOKORO_ASSETS_CONFIG`） | skills/personas 资产目录档（=不配时的默认，目录走 env） |
| `assets.example.s3.yaml` | 同上 | 资产对象存储档：多 pod 免分发（另需 KOKORO_ASSETS_S3_* 凭据） |
| `namespaces.example.local.yaml` | session（`KOKORO_NAMESPACES_FILE`） | 单租户 local_shell 起步 |
| `namespaces.example.docker.yaml` | 同上 | 容器执行隔离档 |
| `namespaces.example.e2b.yaml` | 同上 | e2b 云沙箱档（另需 KOKORO_E2B_API_KEY） |
| `namespaces.example.custom.yaml` | 同上 | BYO 自带沙箱实现 |
| `namespaces.example.swarm.yaml` | 同上 | per-entry swarm 成员配置表（后续归 platform 后台） |
| `custom-backend.example.yaml` | agent（`KOKORO_CUSTOM_BACKEND_CONFIG`） | 自带工厂的自由参数 |
