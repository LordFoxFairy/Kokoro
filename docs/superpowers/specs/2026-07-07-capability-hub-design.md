# 能力中台(Capability Hub)设计 — skill / mcp / subagent

> 状态:**设计已定案,未实施**(用户 2026-07-07 拍板"按此方案")。分阶段;跨仓,部分落 platform 需协调。
> 法源:`docs/kokoro-handbook`(存储分层 §8/§9/§10、依赖方向、单轴 namespace)。

## 1. 目标与三形态

给 agent 的能力资产(**skill / mcp / subagent** 三形态)一套统一的**归属、启用、版本、交付**治理,支持:用户自管的 hub、平台侧后台管理、以及 agent 运行时的确定性装配(任意 pod 数一致)。

三形态共用**一张 registry 骨架**,但**交付机制各异**:

- **skill** = 内容 → 物化文件进沙盒。
- **mcp** = 活连接 + 密钥 → 运行时建连接、注授权,不进沙盒文件面。
- **subagent** = 定义 → 装进 compiled graph。

## 2. 边界(硬约束)

- **控制面独立**:能力治理是**控制面**,不塞进 agent 运行时(数据面)、不塞进 web/session(聊天链路)。它归 **platform 的"agent 能力域"**——与业务域(site/user/credit/payment)并列的第二个有界上下文。
- **platform 是另一会话的树**:registry/能力服务的后端实现落 platform,**本线不动 platform**,需协调。
- **kokoro-model 独立**:模型 provider/凭据/注册归未来 kokoro-model,本设计不碰。
- **单轴 namespace**:registry 主键、启用态 key、归属、跨空间共享(grant)**全部 keyed by namespace**;**永不开 user_id 第二身份轴**。official = 平台保留 namespace;"我的" = 某 personal namespace 所有;共享 = namespace 间 grant。

## 3. 存储决定(定案)

组织原则:**能力资产按 namespace 属主前缀存**——skill/mcp/subagent 是 namespace 拥有的资产,字节落 `<namespace>/skills/<id>/…` 等。namespace 既是隔离边界,又是存储前缀(单轴法的物理落地):删 namespace = 删前缀,presigned/authed URL 按前缀授权。

> 范围界定:本 spec 只定**能力资产**(skill/mcp/subagent)的布局。session workspace 产物当前按 `${sessionKey}/${rel}` 存,要不要 re-root 到 namespace 下是 **workspace 域自己的决定**,不在本设计范围内、不在此捆绑。

| 数据 | 落哪 | 依据 |
|---|---|---|
| skill 包**字节**(含二进制) | **S3 兼容对象存储**(已有,见下),`<namespace>/skills/<id>/…` | 产物要浏览器 URL 直取,GridFS 给不了;我们生产已在用 S3;单轴 namespace = 路径前缀 |
| 能力元数据(种类/版本/hash/归属/对象指针/frontmatter 快照) | **Mongo** | 索引 + resolve 单次读;handbook §9 产物记录侧 |
| per-namespace 启用态(enabled/官方 visible/read_only/required) | **Mongo**(稀疏,与元数据同域) | 与 resolve 同一跳读完,不制造热路径跨库 |
| mcp 密钥/授权 grant | **secret store(加密)** | handbook §7,绝不进明文库 |

**S3 我们本来就有(不是新依赖,是复用)**:`kokoro-session/src/workspace/s3.ts` 的 `createS3WorkspaceReader`(`@aws-sdk/client-s3`,bucket + path-style)已在生产托产物字节。skill 字节落同一套 S3 API。

**后端选型倾向 Cloudflare R2**:S3 完美兼容(换 endpoint 即用,代码零改)、**0 流量费**(正打在产物 URL/浏览器下载的 egress 大头)、10GB 免费额度对 skill(prompt+少量模板)够用。它只是躲在 S3 抽象后的部署选型——minio/R2/aws 对代码同一套 API,不锁死。

**GridFS 不用**:我们本就有真 S3,GridFS 无法原生给浏览器 URL。

**护栏本就在代码里**:`WorkspaceReader` 已有 `local` 与 `s3` 两实现;skill 取字节**复用这个 S3 抽象**,不另造(不建 handbook §7 禁的 `ports/` 目录)。

## 4. 交付两面

### 4a. 进沙盒(agent 当搬运工,被远程沙盒逼定)

远程沙盒**无 DB/存储凭据、不出网**。字节路径:

```
run-start:
  namespace ─查 Mongo 元数据→ 授权 skill id 集
  每个 id ─读 S3 <namespace>/skills/<id>/…→ bundle 字节 (agent 进程,有 S3 权限)
  bundle ─backend.upload_files→ 沙盒 /.skills/main/<id>/… 或 /.skills/sub-<name>/…
```

- 复用现有:`skills/provision.py`(物化进 backend)、`skills/supply.py`(`/.skills/main/`、`/.skills/sub-<name>/` 前缀隔离,点前缀避开用户产物清单/归档)、deepagents SkillsMiddleware(渐进披露)。
- **安全增益**:沙盒不拿存储凭据、不出网(agent 从 S3 读了 courier 进去,不给沙盒发 presigned URL、不开 egress)。
- **eager baseline**:run-start 全量物化授权 skill。**hash 缓存(接 e2b 复用 ADR)**:复用沙盒里用 `skill_hash` 比对 `.hash`,命中跳过重传。**lazy(后续)**:start 只传 SKILL.md,辅助/二进制首读时 agent 从 S3 补货——需 read-on-miss 接缝,不进第一版。

### 4b. 产物访问(浏览器,与 workspace 同款)

skill 是产物:预览文件树、下载、分享 → **presigned / 现有 authed reader 按 `<namespace>/…` 前缀授权**,与 web 现取 workspace 文件(`canvas-panel.tsx` `downloadFile(url)`)**同一套机制**。这正是 GridFS 给不了、非用对象存储不可的那一面。

## 5. Registry 骨架与 resolve

- `CapabilityEntry{ kind: skill|mcp|subagent, namespace, id, version, source: official|custom|github, enabled + 官方状态位(visible/read_only/required), content_ref | config_ref | secret_ref, hash, size }`。主键 **namespace**。
- 启用态单独稀疏表:本体全局共享,启/禁 per-namespace 私有,无记录回退默认;required 型拒写、恒可用。配额 = count(该 namespace 自有条目)。
- **resolve 拓扑(CQRS)**:**写**(publish/import/校验/配额)走 platform 能力服务独占;**读**(run-start resolve)由 agent 运行时**直读 registry(Mongo)**——单跳、不加运行时 HTTP 依赖,与 agent 现直读 checkpoint/memory 一致。
- **resolve 可降级(不 fail-loud)**:registry 抖、单项被删/禁,记日志跳过、其余照跑。对比:config 是启动 fail-loud,能力 resolve 是运行时 degrade——分界明确。
- **产出 RuntimeConfig**:数据流 = session/身份签发 namespace → registry 解析 → 产出 `RuntimeConfig{skills, mcp, subagents}` → 喂**现有**装配。不新造执行内核、不造第二条 skill 路径。

## 6. 现有代码接缝(要改的就这些)

1. `skills/package.py` `SkillPackage.files: Mapping[str,str]` → 放宽承二进制(bytes/对象存储引用);`SkillLibrary` 从**进程启动快照**换成**按 namespace 查 Mongo 元数据 + S3 兼容对象存储字节**的动态源(经 §3 抽象接口)。
2. `skills/provision.py` / `supply.py` / SkillsMiddleware:**不动**(交付链已 remote-ready)。
3. `contract`:沿用 `run.request.context.namespace`;重点是修正 session 的 namespace 来源和持久化,不是给 GA 增加 user/owner 字段。
4. `subagents/catalog.py` / `assemble.py`:custom subagent 走同一张 registry。

## 7. 分阶段

0. **namespace 地基**:wire 加 `namespace`;checkpoint/registry/tag 带前缀。**前置,没它全悬空**。
1. **skill hub(打头阵)**:Mongo 两表 + S3/对象存储包(抽象接口)+ 写序安全发布(platform)+ agent 直读 resolve + SkillLibrary 动态化 + 二进制/hash 缓存 + degrade;web hub UI(管理面 我的/官方 tabs、上传、详情、删除 + composer 选用 + agent 工具 HITL 卡)。
2. **mcp 管理**:同骨架,配置进 registry、密钥进 secret store、运行时建连;不碰沙盒物化。
3. **subagent registry**:custom 创建走同表,接现有 catalog/assemble。
4. **后台管理**:同一 registry 的跨 namespace + 官方策展 + 审核 + 配额权限镜头。

## 8. 待协调 / 未决

- Phase 0 的 `namespace` 契约改动 + Phase 1 的 platform 能力服务后端 → 需与 platform/contract 那条会话协调。
- 官方 skill 来源:用户上传 + 平台预置(优先) vs github 导入管线(后续)。
- secret store 选型(mcp 阶段再定)。
