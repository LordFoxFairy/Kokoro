# Kokoro 产品化技术主图(问题梳理 + 我们要什么)

> 2026-07-07 讨论态。把当前所有技术线头梳成一张图:每块**要什么 / 已有什么(实测) / 缺什么 / 边界**。
> 标记:✅已有 ⚠️缺口 🚧边界(另一会话的树/纪律)。

## 北极星(一句话)

**一个真实多用户产品**:用户登录后有**自己的 namespace**;在 hub 里管理**自己的能力**(skills / mcp 工具);agent 在**真隔离沙箱**里用这些能力干活;沙箱产出(中间件 + **最终产物**)在 web 里**可预览、可下载**;一切按**单轴 namespace**圈定。

---

## 1. 身份与归属(auth + namespace)—— 一切的根

**要什么**:真实 login/注册 → JWT → session 得到个人 namespace(单轴)。

- ✅ session 已验签 JWT(`http/auth.ts` HS256/node:crypto;未配 secret=直通 `local-user`,配了=全路由 Bearer,owner=`sub`)。
- ✅ web 已带 token(`file-fetch.ts`/`client.ts` 从 localStorage `kokoro.auth.token` 发 Bearer)。
- ✅ kokoro-user 服务存在(platform,Prisma);kokoro-admin-web 已有 auth(那是**后台**admin,不是消费者)。
- ⚠️ **web 没有 login/注册 UI**(只有 token 管道,拿不到 token);普通用户 **settings 页**缺;namespace 还没进代码。
- 🚧 kokoro-user 是 **platform 的树**:web 调它的 auth API、理解它,**不改它**。签发归它,session 只验(注释已写明)。

**关键接线**:JWT `sub` 在个人空间闭环中就是 namespace id。web/session/platform 可以理解 user/team/site,GA 不理解这些身份语义。

## 2. 能力中台(skill-hub + mcp-hub,在 platform 下)

**要什么**:两个控制面 hub;用户自管 skill/mcp;agent 按 namespace 解析装配。

- ✅ **skill 存储设计已定案**(见 `2026-07-07-capability-hub-design.md`):字节→S3/MinIO(`<env>/<namespace>/skills/<id>/`)、元数据→Mongo、agent 搬运进沙盒、GridFS 不用、R2 作生产后端候选。
- ✅ agent 侧已有一半:`content_source.py` 有 S3 skill 源、boto3 依赖、`provision`/`supply` 交付链、MinIO 测试先例。
- ⚠️ 缺:库来源从**启动快照**→**按 namespace 动态查 Mongo+S3**;Mongo catalog 两表;**hub 服务本体**;**mcp 深设计**(活连接+密钥,非文件);**web hub UI**。
- 🚧 hub 落 platform(需与那条会话协调);skill/mcp/subagent 共享的骨架(namespace 归属/启用态/registry CRUD/发布流)**不该在两个 repo 里各写一遍**。采用一个 capability hub 边界,内部按 kind 分模块。

## 3. 执行沙箱(sandbox)—— 选型研判中

**要什么**:真隔离、官方标准、可自托管、支持 e2b、docker 能跑通。

- ✅ 代码后端全在:`docker_backend`/`e2b_backend`(e2b>=2.30.0,**带 sandbox_id resume**)/`custom_backend`/local;契约 `Backend=Literal[state,local_shell,docker,e2b,custom]`;选择点 `make_backend_for_run`。**不用从零造。**
- ✅ **选型已定案(研判)**:E2B 自托管=重坑(Firecracker+KVM+Nomad+GCP,纯 docker 起不来,不碰);**Daytona = 自托管正解**(Docker+gVisor,`docker compose` 单机可起,SDK 覆盖 exec/文件/`get(id)`resume/delete,平滑上 K8s)。
- **定案**:dev 跑通 = **E2B Cloud**(现有 SDK backend 零改)**或 Daytona compose**(要零外网就它);生产 = **Daytona 自托管**;手搓 docker-run **降级为本地无网兜底**。
- ⚠️ 缺:新增 **Daytona backend**(接 `Backend` 枚举);e2b/远程沙箱的**文件归档拉出路径**(见 §4 缺口1)。

## 4. 产物与画布(artifacts + canvas)—— 已铺一半

**要什么**:沙箱产出在 web 可见/预览/下载;**区分最终产物**;最终产物落 S3。

- ✅ **整条链路已建**(ADR-009):沙箱写 →`ArchivingWritesMixin` 增量+全量归档进 S3(`{prefix}/{rel}`,尽力而为不阻塞)→ session `WorkspaceReader`(local/s3)读 → `snapshot.files` → web canvas 渲染 + 鉴权 fetch + 下载(`canvas-panel`/`artifact-card`/`file-fetch`)。
- ⚠️ 缺口1:归档 Mixin 叠在 **LocalShellBackend**(含 docker 变体,文件留宿主)。**e2b 是远程 `BaseSandbox`,不是 LocalShell** → 远程沙箱的文件**拉出来那条路要单独接**。
- ⚠️ 缺口2:**"最终产物"还没被区分**——现在所有 workspace 文件平等罗列。要一个**产物记录(Mongo)+ "标记为最终" + 按 namespace 归库 + web 里最终产物 vs 中间文件分开展示**。接 memory「产物统一归库」。

## 5. 前端 web(所有上面的 UI 面)

**要什么**:login/注册、消费者 settings、能力 hub UI(skill/mcp 管理 + composer 选用 + HITL 卡)、canvas/最终产物展示。外部 UI 参考只进 tmp 中间产物,正式方案/代码不写来源路径、分支名、命名或逐字文案。

- ✅ token 管道、canvas 面板、artifact-card、鉴权 file-fetch 已有。
- ⚠️ 缺:login/注册 UI、settings 页、hub 管理界面、最终产物展示区。

---

## 跨切边界(始终守)

- 🚧 **platform(kokoro-user / skill-hub / mcp-hub)= 另一会话的树**:设计意见 + web/agent 对接,**不擅自改**。
- **单轴 namespace**:GA 只认 opaque `namespace`,**永不开 user_id/owner_id 第二轴**。
- **参考纪律**:外部参考只吸收交互与思路,**路径/分支名/逐字零进正式 repo**。
- **kokoro-model 独立**,不碰。

## 依赖与建议顺序

```
根:auth+namespace——不落这个,下面全悬空
 ├─ Phase 0:web login/注册 UI 接 kokoro-user + session 从 JWT/auth 结果得到 namespace + 消费者 settings
 ├─ Phase 1:skill 动态化(agent)+ skill-hub(platform 协调)+ web skill hub UI   ← 存储已设计,起手最实
 ├─ Phase 2:沙箱选型定案(研判回来)+ 产物"最终态"区分与展示(补 e2b 拉出路径)
 └─ Phase 3:mcp-hub(活连接+密钥,secret store)+ web mcp UI
```

## 待定案(需你拍 / 研判回填)

1. 沙箱生产选型(研判中):docker 镜像 / E2B 自托管 / Daytona。
2. hub 仓结构:两仓(skill-hub+mcp-hub)分立 vs 一仓分模块 —— 我倾向别让骨架重复。
3. "最终产物"如何判定:agent 显式标记 / 用户在 web 勾选 / 约定产出目录?
