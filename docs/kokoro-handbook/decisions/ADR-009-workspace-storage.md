# ADR-009 Workspace 文件面的多 Pod 存储与访问

## 状态

Accepted（2026-07-05；technical/06、08 与 operations/docker-and-k8s 已同步引用）

## 背景

工作区是 agent 工具真实写文件的目录，约定 `{WORKSPACE_ROOT}/{namespace:session_id}/`；
session 直读同一约定（snapshot.files 走目录 walk，`GET /sessions/:sid/files/:path` 直读字节），
web 的 canvas 预览与文件树全部经 session 端点，从不触存储本身。

单机（本地开发、单 pod docker）同根挂载即成立，已被 L2 gate 与 L5 走查全量验证。
多 pod 下 agent pod 与 session pod 不共享本地盘，文件面需要一个"两侧看见同一份数据"的载体。

已有法典约束：

- ADR-006：sandbox 四策略 `state / local_shell / e2b / custom`，backend 能力边界含创建
  workspace、写输入、读结果、清理。
- technical/06：Object Storage 承载"大文件和导出文件"；SQLite 不作为 V1 runtime 存储策略。
- technical/08 多 Pod 红线：关键状态不进单进程、不依赖单机文件。

## 决策

**固定点：契约与接口不动。** `snapshot.files` + files 端点是 web 唯一入口；session 侧
`WorkspaceReader`（list/read）是唯一读接缝；agent 侧 `make_backend` 是唯一写接缝。
一切形态差异都是这两个接缝后面的实现替换 + 部署配置，web 与契约零感知。

**单节点 = 本地目录，永久默认档。** 本地开发与单节点 docker 部署下，agent 与 session
同根（进程同机即同目录；docker 则两容器挂同一个 volume），零额外配置、零外部依赖。
S3/对象存储只属于 e2b 云档，绝不上抬为默认或单节点要求。

三档部署矩阵（按环境递进，不是三选一）：

| 档位 | agent 写 | session 读 | 配置 |
| --- | --- | --- | --- |
| dev 单机 | `local_shell` 本地目录 | 本地目录 walk（现状） | `KOKORO_WORKSPACE_ROOT` 同根，零额外配置 |
| 自托管多 pod | `local_shell` + RWX 共享卷（NFS/EFS/PVC） | 同一共享卷 | 纯部署配置：两类 pod 挂同一卷，代码零改动 |
| 云生产 | `e2b` sandbox（远端统一挂载） | 活跃期经 sandbox files API 直读；sandbox 收敛后读对象存储归档 | `KOKORO_WORKSPACE_BACKEND=local\|s3` + e2b 凭据 |

### 云生产档的关键设计

- **写侧**：e2b sandbox 就是 workspace（ADR-006 既定）。工具写文件即写 sandbox 文件系统，
  无镜像、无同步机械——与真目录直读的既有哲学一致。
- **读侧切换点 = sandbox 收敛**：run 活跃期间 `WorkspaceReader` 的 e2b 实现直读 sandbox
  files API；run 终态/超时触发一次归档（workspace 整树 → 对象存储
  `{bucket}/{namespace}/{session_id}/...`），此后读走 S3 实现。活跃只读 sandbox、归档后只
  读 S3，单向切换，无双写竞态。
- **一致性语义**：文件可变、最新写为准（现契约已如此：files 端点不设 immutable 缓存）。
- **安全**：路径穿越防御保持在 reader 层（本地档 safeResolve，S3 档 key 规范化拒绝
  `..`）；namespace 隔离 = key 前缀 + 桶策略；files 端点鉴权随 auth 上线（ADR-002 域）。

### 配置面：`type` 判别式结构化配置

沿 namespaces profile 的既有模式（`backend` 字段即先例）：存储形态用一个 `type` 判别对象
声明，Zod discriminatedUnion + strict 校验，未知 type / 缺字段 fail-loud。加一档新后端 =
加一个 type 分支，声明式、可审计、不散落。

```yaml
# KOKORO_WORKSPACE_CONFIG 指向的 yaml（Phase 1 随 e2b 引入）
workspace:
  type: local            # local | s3（e2b 归档读档）
  root: /data/workspace
---
workspace:
  type: s3
  endpoint: https://…    # minio 与 AWS 同协议
  bucket: kokoro-workspace
  # 凭据走 env/secret 注入，不进配置文件
```

单节点零配置语义不变：不给 `KOKORO_WORKSPACE_CONFIG` 即 `type: local` + 默认根
`./kokoro_workspace`；现有 `KOKORO_WORKSPACE_ROOT` 继续作为 local 档根的快捷覆盖。
凭据永远不进配置文件（env/secret 注入），配置文件只声明形态与非敏感参数。

agent 写侧不新增配置：backend 选择本就由 namespace profile 每请求决定（ADR-006）。

## 范围外（显式 YAGNI）

- 文件版本历史、分片上传、CDN 分发：无场景不做。
- 音乐/视频等大产物：属 platform artifact 域（technical/06 已分域），workspace 不承载。
- PostgreSQL：维持 technical/06 决策不引入。

## 实施顺序

1. **Phase 0（零代码，本 ADR 采纳即生效）**：operations 补部署说明——单节点默认本地/
   同 volume；自托管多 pod = RWX 共享卷。前两档即刻可用。
2. **Phase 1（与 e2b 同期，等外部件排期）**：e2b backend（`make_backend` e2b 分支）+
   收敛归档器 + `WorkspaceReader` 的 e2b/S3 组合实现 + compose 加 minio，L2 文件面用例
   （E2E-17/18/19）参数化跑 local/s3 两档。读写必须同期落地——先做 S3 读实现而无归档写侧，
   是没有真实数据流的空中楼阁，验证只能自欺，故不拆分。
3. **Phase 2**：files 端点鉴权（随 auth 主线）。

## 影响

正向：三档共用同一契约与测试面；自托管当下零代码可上多 pod；e2b 落地时读路径已备好归档形态。

代价：Phase 2 归档器引入"run 终态触发副作用"，需要幂等（重复归档无害）与失败可见
（归档失败上日志与告警，不阻塞 run 终态收口）。

## 强制规则

- web 永不直连对象存储或 sandbox：文件面唯一入口是 session files 端点。
- 归档必须幂等且失败可见；归档失败不得阻塞 run 终态。
- 任何档位的 reader 必须保留路径穿越防御与 namespace 隔离。
- `local_shell` + 共享卷仅限自托管受控环境，不作为公有云多租户的安全边界（ADR-006 红线）。
