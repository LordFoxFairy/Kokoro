# Task A 清理与重构执行计划

> 当前入口：本文保留原清理次序、写区与验收约束；当前基线、进度、问题和TODO统一维护于 [Task A闭环方案](2026-11-01-task-a-c1-c4-technical-plan.md)。不据历史勾选判定当前完成。

> 状态：G0 设计门已通过（2026-10-31）；C-1 阶段提交已存在，C-1.3/C-2～C-4 按本计划继续执行。本计划不授权正常数据写入、DDL 或发布切换。

## 1. 基线与目标

- Root：`3a3b6b91faf4540a2499915698f2abbdb525ba85`
- App：`73b2df451c2604a6d1e9413bf07eb383b95219e9`
- BFF：`853ca9a5d8da3500b0c37543c72198a520e46225`
- Agent：`c43fc3f22c676b459dd45d74438a6ccb515e5abd`

目标：先完成 C-1～C-4 清理重构与 Root/子仓验证，再实现 A-01、A-02，最后实现 A-07。任何旧协议、旧字段、旧 alias、旧 fallback、双读、双写和 migration bridge 均不进入目标运行时。

## 2. 停写门与写区

### G0：设计门

进入业务写入前必须完成并审阅：

1. native-session admission contract：IAM owner、Cookie path、BFF direct credential、CSRF/logout、tenant/session revocation、失败语义；
2. C-1 真实兼容分类：删除项与当前语义保留项逐文件确认；
3. BFF Nest feature/module/provider 图；
4. Repository/Service/Port 取舍表；
5. 测试删除/重写矩阵和默认脚本入口。

G0 之前只允许修改 Root 设计文档、盘点文档和本执行计划；例外是 G0 contract writer 为固定门材料而交付的 IAM hand-authored artifact pin、README provenance 与其校验入口。IAM runtime、App/BFF/Capability consumer 和任何业务路由仍停写，直到 G0 reviewer 明确通过。

### 写区

| 阶段 | 唯一 writer | 允许路径 |
|---|---|---|
| C-1 | A | App/Agent/BFF 兼容生产源、对应测试/script/package；不改业务 owner Schema |
| G0 contract | IAM owner（A 负责 Root 集成） | `apps/kokoro-iam/contract/openapi/native-session-admission.v1.json`、IAM contract README/生成入口；只固定 wire，不实现 runtime |
| C-1.3 auth cutover | IAM owner；App/BFF/Capability 各自 owner 只写本仓路径 | IAM cookie/native-admission controller/service/credential reader；App native adapter；BFF admission consumer；Capability `global_register` direct-credential authorizer/catalog/tests；第三方 MCP OAuth 不在写区 |
| C-2 | A | BFF `package.json`、Nest bootstrap/module/config/http/database 与四个 A 依赖 feature |
| C-3 | A | BFF feature-local Repository/Service/Port 迁移文件 |
| C-4 | A | BFF/App/Agent 相关测试与 package scripts；生成物只通过 generator 更新 |
| A-01/A-02 | A | App/BFF/Agent 对应 canonical 文件及已批准 contract consumer |
| A-07 | A | BFF ProjectTask owner、生成客户端、App Project Todo 页面 |

同一阶段的 contract、Schema、lockfile、generated 目录和公共入口保持单 writer；未交接的其他工作不覆盖、不回滚。

G0 contract writer 先交付 IAM artifact/version/digest 与 BFF/App 消费边界；在该 artifact 被审阅并固定前，C-2 的 Nest 依赖/architecture gate 只能保留为预备提交，不能迁移业务路由或删除旧 listener。C-1.3 的 runtime 写入从 G0 通过后的停写基线开始，并以 IAM→BFF/App→Capability 的顺序交付。

## 3. C-1 兼容删除

### C-1.1 BFF schema-evolution 删除

顺序固定：

1. 从 `package.json`、architecture oracle、schema catalog、fixture 反向列出消费者；
2. 先删除默认脚本入口和测试注册；
3. 删除 evolution integration tests 与只服务它们的 fixture；
4. 删除 evolution scripts；
5. 反向搜索生产 import，确认零引用；
6. 删除历史文档中的运行入口描述，仅保留审计背景。

禁止先删除脚本再让默认测试失败，也不把 evolution script 改造成运行时兼容层。

### C-1.2 App/Agent canonical 清理

- 删除 App 旧 hash URL、`legacyRenderAnchor`、`cancelledRuns` 迁移、`legacyFinalId`、inline/ordered 双读和未锚定历史顺序 fallback；
- 保留 App `localDraft` canonical lifecycle、标题派生、空工作台状态，但重写其 owner create/retry/retire 边界；
- 删除 Agent `legacy_failed`、旧 source digest 特判和历史展示补偿；
- 保留 Agent frozen recipe、checkpoint/journal integrity、durable replay、lease/CAS/outbox。

### C-1.3 First-party auth cleanup

先发行 native-session admission contract，再按方案 B：

- 删除 App Auth.js/OIDC RP、OIDC transaction/token/CSRF/relay 旧实现；
- BFF relay 只保留 native sign-in/session/logout/tenant/invitation；
- 删除 Product Session cookie/store 与 refresh reservation；native admission 直接消费 IAM session，禁止保留无凭据双读/双写投影或 OAuth access/refresh；
- 删除 `global_register` workload OAuth，改为 direct service credential；
- IAM 对外 OAuth provider、MCP provider OAuth、Billing 资金授权保持独立边界。

## 4. C-2 BFF NestJS 收敛

### C-2.1 运行时

1. 加入与其他 TypeScript owner 一致的 NestJS 12 依赖和唯一 `main.ts` bootstrap；
2. 采用 `@nestjs/platform-express` 作为唯一 BFF adapter，保留 Node req/res、SSE、rawHeaders、取消和有界 body 读取语义；建立 `AppModule`、Config、Database、Health、HTTP/exception/request-context 横切模块；
3. 先迁移 Account/session、Projects、Agent Runs、AG-UI 四个 A 依赖 feature；随后按同一 provider graph 完成 Skills/MCP/Billing/System/Music/ScheduledTasks 等剩余 route；
4. 每个 feature 采用 Controller → Service/use case → feature-local Repository/client；
5. 以 Nest `main.ts` 作为唯一 listener；非 A feature 在迁移前只能挂在 Nest 内的冻结 `LegacyRoutesModule` adapter（不新增 route、不创建第二 listener），全部切换后删除该 adapter、全局 service locator 和旧三层组合器；
6. 运行时只保留一个 Nest 入口；不得保留旧 Node/Nest 双启动模式。

### C-2.2 依赖边界

- BFF 不读取 IAM/Platform/Agent/Storage/Billing 数据库；
- Web → BFF → owner，Web 不直连 owner；
- generated client 只在 adapter 层消费；
- session admission、service credential、tenant/subject context 在 HTTP boundary 一次冻结；
- 不创建通用 BaseRepository、通用 Bus、第二套网络协议或空模块。

## 5. C-3 Repository/Service/Port 收敛

### 保留独立 Repository 的条件

仅在存在真实事务、锁、CAS、lease、outbox、幂等 receipt、复杂查询、owner boundary 或第二数据源时保留。

### 删除/并入条件

- 单一实现且只有简单 CRUD：并入 feature Service/Provider；
- 只转发一次且无边界策略：删除 Service/Port；
- 巨型 Chat/Project Port：按 Account/session、Messages、RunDisplay、Archive、Share、Feedback、Projects、ProjectTasks 等 feature 拆分；
- `BffBusinessStore`、`PostgresBffRepositories`、`BffApplicationServices`：provider 图完成后删除；
- 不使用全局 `application/ports` 目录承载不相干能力。

## 6. C-4 测试清理与门禁

### 删除

- 只验证 schema-evolution、legacy/fallback、已删除 route/field/alias 的测试；
- 只保护旧实现文件结构或私有调用顺序的测试；
- 只为 preview/fake 伪装 live 成功的默认测试；
- 已无生产消费者的 generated snapshot/oracle。

### 重写

- canonical App conversation/persistence/engine tests；
- Agent RunDisplay/contract tests；
- BFF feature contract/integration tests；
- auth native-session admission tests。

### C-4 验证

每个停写基线执行：

```bash
git diff --check
python3 scripts/verify-repository-topology.py
pnpm lint
pnpm typecheck
pnpm test:architecture
pnpm test
pnpm build
```

子仓再执行自身 `format/typecheck/contract/test/build`。失败分类为新增失败、既存失败或环境缺口，不通过删断言、缩小范围或保留兼容分支解决。

## 7. C-1～C-4 完成条件

- 运行时代码无旧 route/field/alias/fallback/double-read/double-write；
- BFF 只有 Nest bootstrap 与 feature module；
- Repository/Service/Port 均有职责证据；
- 默认测试入口只验证 canonical 当前行为；
- generated artifact 由唯一来源生成；
- Root 与子仓验证证据已记录，且无业务代码混入停写边界。

## 8. 进入任务 A

### A-01

先接 canonical session create/retry/URL/history/refresh/back-forward/multi-tab/late-response；保留 localDraft 但不把它当 owner session。

### A-02

只消费 canonical AG-UI/snapshot/parts/RunDisplay；主层显示行动与正文顺序，技术参数/结果进入详情；历史缺字段不补造。

### A-07

在 BFF Nest ProjectTask feature 中先发布 create/update/status/delete、权限、CAS/幂等和生成客户端，再接 App Project Todo；Run Todo 继续作为执行进度事实。

每个切片都必须保留：绝对路径、owner、停写 SHA、contract/version/digest、实际验证、页面/HTTP/数据库证据、剩余风险和下一 owner。
