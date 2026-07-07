# 派工单:能力中台 + 沙箱 + 产物 + 用户面(交 code agent 执行)

> 2026-07-07。主控在 Claude,本单把已定案的活拆成可独立执行的包。
> 依据:`specs/2026-07-07-product-technical-roadmap.md` + `specs/2026-07-07-capability-hub-design.md`。
> **全局边界(每个包都适用)**:🚧 不改 kokoro-platform(另一会话的树,只读其 API/协调);GA 只认 opaque `namespace`,不开 user_id/owner_id 第二轴;外部 UI 参考只进 tmp 中间产物,路径/逐字零进正式 repo;kokoro-model 不碰;声明完成必须真跑验证并贴输出。

## WP-0 · namespace 契约地基 【READY,最先】

- **目标+验收**:`run.request` 带 `namespace`;kokoro-session 从 JWT/auth 结果得到 namespace(直通态 `local-user`;JWT 态 `sub` 即 namespace id,不加业务前缀);kokoro-agent run context 贯穿(checkpoint thread_id / Langfuse tag 带 namespace)。**验收**:契约生成双跑字节稳定;agent/session 定向单测绿;checkpoint key 里能看到 namespace。
- **可改**:contract namespace 字段(四部立法+生成器双侧)、kokoro-session 签发点、kokoro-agent `run/builder` run context。**禁改**:鉴权验签(已工作)、platform、无关文件。
- **上下文**:memory「namespace 最小落法」;session `http/auth.ts`(owner=sub)。
- **报告**:diff + 验收命令输出。

## WP-1 · skill 动态化(agent 侧)【READY,依赖 WP-0】

- **目标+验收**:`SkillLibrary` 从进程启动快照 → **按 namespace 动态查 Mongo 元数据 + S3/MinIO 字节**;`SkillPackage` 支持二进制;resolve **可降级不中断 run**;`provision`/`supply` 交付链不动。**验收**:脚本塞一个 skill 进 MinIO(`<env>/<namespace>/skills/<id>/`)+ Mongo 元数据 → 跑一次 run → skill 现于沙盒 `/.skills/`、agent 能读;pyright 0 + ruff 绿 + 定向 pytest(MinIO 实测)绿。
- **可改**:`skills/package.py`、`content_source.py`、新增 skill 取字节抽象(复用 s3 客户端写法)、tests。**禁改**:`skills/provision.py`/`supply.py` 交付链、platform。
- **上下文**:`capability-hub-design.md` §3/§4;现有 `content_source.py` 的 S3 skill 源;MinIO `:9100` 起法见 `docs/test-cases.md`。

## WP-2 · 沙箱 Daytona 后端 + 跑通(agent 侧)【READY,研判已定】

- **目标+验收**:(a) 确认 **E2B Cloud** backend 可跑通(dev,配置态);(b) 新增 **Daytona backend**(SDK:`process.exec`/`fs.upload_file`/`get(id)`+`start/stop` resume/`delete`)接 `Backend` 枚举与 `make_backend_for_run`;(c) 补**远程沙箱(e2b/daytona)文件归档拉出路径**(现 `ArchivingWritesMixin` 只覆盖 LocalShell 系)。**验收**:Daytona `docker compose` 起,一次 run 的 execute + 文件读写 + resume(stop→get→start 文件保留)绿。
- **可改**:`sandbox/`(新 `daytona_backend.py`、远程归档路径)、契约 `Backend` 枚举加 `daytona`、tests。**禁改**:其他后端语义、platform。
- **上下文**:研判结论(E2B 自托管=Firecracker 重坑不碰;Daytona=Docker+gVisor 自托管正解;docker-run 降本地兜底);Daytona 官方 SDK。

## WP-3 · web 登录/注册 + 消费者 settings(web 侧)【READY-ish,需读 kokoro-user API】

- **目标+验收**:kokoro-web 加 login/注册 UI → 调 **kokoro-user** auth API 拿 JWT → 存 `localStorage("kokoro.auth.token")`;普通用户 **settings 页**(可参考外部消费者 settings 的交互结构,重写为我们的、正式代码/文档零留痕)。**验收**:登录后 token 就位、受保护路由通;Playwright 走通 登录→进会话 主路径 + 截图;tsc/eslint 绿。
- **可改**:kokoro-web。**禁改**:kokoro-user(platform,**只读**其 auth 路由契约,不改)、session 鉴权(已工作)、token 管道(`file-fetch`/`client` 已有)。
- **上下文**:web 已有 token 管道;kokoro-user 是 platform Prisma 服务——先读它暴露的 auth 路由/请求响应形状。

## 待你拍(拍完才好派)/ 暂缓包

- **决策 A**:hub 仓结构——**skill-hub + mcp-hub 两仓分立** vs **一仓分模块**?(我倾向别让 namespace/启用态/registry 骨架在两仓各写一遍。)→ 决定后才好开 hub 服务包。
- **决策 B**:**最终产物如何判定**——agent 显式标记 / 用户在 web 勾选 / 约定产出目录?→ 卡住 **WP-4 最终产物模型**(agent+session+web:产物记录入 Mongo、最终态标记、web 分区展示)。
- **决策 C**:dev 沙箱要不要零外网?要 → WP-2 直接上 Daytona compose,跳过 E2B Cloud。
- **平台协调(不派我们的 code agent)**:skill-hub / mcp-hub 服务本体、kokoro-user 对接契约、mcp secret store 选型。

## 派发顺序

`WP-0 → WP-1`(agent 主线,存储已设计)、`WP-2`(沙箱,可与 WP-1 并行,不同文件)、`WP-3`(web,可并行)。WP-4 等决策 B。hub 服务等决策 A + 平台协调。
