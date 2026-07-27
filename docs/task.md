# Kokoro 任务状态（跨会话）

> 主 agent 维护；子 agent 只读。会话开始读一次。状态以**代码为准**(handbook 状态位可能滞后,以本表校正)。
> 最后更新:2026-07-27(federated Wave 0 pin promotion 收口;见下节)。
> 历史:2026-07-13 纲领 Wave 0-6 全清+WEB-ARCH 重构收口;终局 gate 115 断言 PASS;交接终稿=handoffs/2026-07-13-full-closure;纲领=specs/2026-07-11-cross-repo-closure-and-legacy-alignment-design.md。原型期旧台账见文末归档。

## Federated Wave 0 收口(2026-07-27)

> 架构定案:**federated repositories**——根仓永久保留 `.gitmodules` 与四个 gitlink,四个子仓各自拥有
> source/lock/CI/artifact/deploy/rollback,跨仓只走版本化协议。**"snapshot import 成单体 monorepo"方向已废弃**
> (旧计划 plans/2026-07-26-wave-0-repository-contract-foundation-implementation-plan.md 仅存史,不要照做)。
> 传输权威=specs/2026-07-27-contract-transport-and-internal-rpc-design.md(internally-approved,
> implementationAuthorized: true)。当前事实梳理=reports/2026-07-27-kokoro-architecture-survey.md。

- [x] **真基建运行时兼容性门**(staged pins,`--tree index`):5 场景全 pass
      (web-session-http-sse / session-platform-internal-rpc / session-agent-durable / agent-model-gateway /
      platform-admin-auth-connect),走根 Infra authority(profiles=full scope=ci-federated),trap 收尾后
      `docker ps -a` 归零,未删 volume/image。
- [x] **atomic pin promotion**:commit `0f30276`,恰好 5 条路径(manifest + 四 gitlink),无工具链/契约/业务混入;
      HEAD-mode verifier pass。四子仓 remote CI 均 success。
- [x] **干净 recursive clone 复现**:`file://` + `--no-local`(无 alternates,独立 object db),四子仓从各自
      GitHub remote 初始化。19 contract mirror / 35 contract 测试 / buf format+lint / 15 architecture 测试 /
      INDEX 覆盖 57 roots / 依赖门 57 roots+13 edges / 72 repository 治理测试 / 6 Python 适配器测试,
      二次 regenerate 后根仓与四子仓 `git diff --exit-code` 全干净。
- [x] **rollback 演练**(一次性 clone,未 push):revert promotion → 四子仓回退到前一组 pin →
      reverted tree 上 verifier pass → 四个**旧** recoverableRef tag 仍远端可解析。
- [~] BOM 生成器/schema/测试 + freeze-snapshots 方向对齐(freezer 原本仍服务已废弃的单体 baseline)。
- [~] boundary registry(**T0 真缺口**:`config/` 下无此物,但 spec §13 T0 要求它冻结每 operation 唯一 transport)。
- [ ] 根仓 branch push + 根 remote CI + BOM tag(唯一对外动作,全绿后才做)。

### 内部 RPC 现状与下一步(别再重复问)

- 现状:5 条声明契约里**只有 `platform-admin-auth v1` 真走 protobuf/Connect**(带 protovalidate、
  CommandIdentity/CommandReceipt 幂等信封、GetCommandReceipt 超时对账、RetryClass 错误分类)。
  其余仍是 `contract/spec/*.yaml` 生成的 Zod mirror + `callService` 手写出站(4 处:payment→credit、
  credit→site、credit→user、hub→user),**响应 schema 由调用方自己声明,服务端改形状不会让调用方编译红**。
- **tRPC 不作为跨仓/跨语言标准**(spec §1 明确):四仓是独立仓库没有共享 TS 类型图,且 kokoro-agent 是 Python,
  `model-gateway`/`session-agent-execution` 两条契约跨语言。protobuf+buf 同时给 TS 与 Python 生成客户端并提供
  `buf breaking` 兼容门。仅允许未来同仓同发布单元内经 ADR 批准局部使用 tRPC。
- 迁移序(spec §13):T0 contract foundation → T1 Admin Auth pilot(**已完成**)→ T2 Public Admin API(OpenAPI 3.1)
  → T3 Platform Admission(**这一步才处理那 4 处 callService**:§3.2 判定其中部分本属同一 Platform workflow,
  应收拢为本地 application interface 而非包装成 RPC)→ T4 Session HTTP/SSE → T5 durable ownership → T6 legacy 删除。
- 因此**现在不要删** `callService` 的 legacy 单密钥模式:spec §6.3 允许本地开发临时兼容 per-caller static secret
  (须集中封装+标注 migration expiry),删除归 T6 且以 consumer inventory 归零为前置。

## 通用引擎重塑 campaign(2026-07-24;规划阶段,未碰代码——用户要求先思考对齐再动)

> 缘起:用户判"整体业务设计很烂"。深挖发现根因=**先造机器没设计产品**(billing 只是第一个实例)。
> **共同本质(已对齐)**:一台通用引擎——意图→GA 编排能力→调 kokoro-model 的模型(任意厂商/任意模态)
> →artifact→credit→namespace。**唯二变量:surface(Chat/Studio)× 模型;产品=配置,引擎=打磨对象。**
> 三统一:GA(一运行时)· kokoro-model(一全模态模型注册表,音乐/图片模型与 LLM 平级)· Plan(一套餐抽象)。
> 用户定向:优先 Music/Image Studio、能过快、反哺 chat(自动,同一 GA/能力池)、先打通通用基本能力。

- **总规划**:plans/2026-07-24-universal-engine-master-plan.md(分层 L1-L7 + 依赖图 + 阶段 A-G + 卡点)。
- **货币化**:specs/2026-07-24-unified-plan-monetization-design.md(Plan 免费/包/订阅 + 三桶每日/周期/永久 +
  消费过期先扣 + 懒 materialize 非 cron + **卡密兑换零支付集成** + 权益层)。
- **能力/Studio**:specs/2026-07-24-capability-and-studio-architecture.md(v3 共同本质;Studio 通用=配置;
  媒体=kokoro-model 多一模态的模型,GA 只"调某模型",无平行 job/无新服务)。
- **盘点**:reports/2026-07-24-product-capability-inventory.md(有/缺/不足;实现度~20-30%,机器强产品弱)。
- **地基事实**:model binding schema 已多模态就绪(featureKey/in-out modalities/transport);真缺=agent 只有
  make_chat_model(LLM-only)→"调非对话模型(音乐/图片→artifact)"是引擎核心新链。
- **相序**:阶段 A 引擎通用链(model 收媒体模型→GA invoke_model→artifact+featureKey 计费,e2e 为铁证)
  ∥ B 商业(三桶/Plan/权益/卡密/订阅)→ C 通用 Studio+Image/Music→ D 反哺 chat→ E 组织纵深→ F 运营+风控→ G 增长+设计系统。
- **卡点**:LLM+媒体 provider key(用户给即真,先 mock/单 provider 验证);商业收口点确认(消费顺序/订阅=权益/USD)。
- 状态:规划成型 + **已开工实现(用户批 A-媒体+L3.1 三桶,TDD 接线)**。详规=plans/2026-07-24-phaseA-L3-detailed-plan.md。
- **DeepSeek 已解真模型阻塞**:sk 用户临时给(会注销),仅存 deploy/.env.dev(gitignore),closure-up 从 env 读无字面 key;
  对话 run.completed + 真 usage 结算 + ledger model_call 带 run_id 已实证(GLM key 仍全 401,弃)。

### L3.1 三桶实现进度(TDD;真 DB=隔离库 kokoro_credit_test@3307,`scratchpad/credit-it-env.sh` source 出 DATABASE_URL_CREDIT)
> **架构定案 B1(不走 C 胶合)**:三桶统一——hold 时按序从桶扣走+明细快照到 hold,capture 拆实额、
> release 按**夹紧当期额度**归还,删 heldMicros。理由=完美/不妥协+未上线无后向兼容;clamp 补上后无日界竞态。
> **心黑但合理决策矩阵**(14 条)见货币化 spec §3.9:歧义一律 house-favor 但对用户站得住。
- [x] 域 `buckets.ts`:available/debit(过期先扣+shortfall)/refresh(reset 非累加)/**creditBack 时间桶夹紧额度**(堵日界复活过期赠额)。18 单测绿。
- [x] **阶段1**(75b6780):CreditAccount 加 daily/period 桶列+水位(加法迁移 20260724120000);实体+mapper 暴露;5 fixture 补齐。182 单测+107 集成绿。
- [x] **阶段2**(070dce9,脊柱手术):hold/capture/release/expire/spend 全切 B1 decrement-at-hold(FOR UPDATE 锁+
  域 debit/creditBack 唯一事实源+预留明细快照 CreditHold+applyBucketReturn 私有 helper 三处复用夹紧归还)。
  heldMicros 保留作预留总额缓存(唯一预留机制下的报表 denorm,非双机制胶合)。
  死代码清理:assertCreditSpendAllowed 无调用方,连同专测删除。
  TDD 新增 4 条证明 B1 真多桶行为(按序扣/分摊守恒/release 复原/**日界夹紧堵过期赠额复活**)+
  既有 6 条 mid-hold 断言按 B1 语义更新(终态不变量全保持)。174 单测+111 集成+typecheck 净,全真 DB chaos。
- [x] **阶段3**(d30a16a):懒刷新接线——域 `reset-boundary.ts`(dailyBoundary/periodBoundary 统一 UTC
  自然日/自然月,与既有 quotaPeriod=monthly 同口径;isStale 判水位)。repo `refreshRow()`唯一换算点,
  hold/spend/`refreshAllowances`(新读路径 API)三处复用;FOR UPDATE 锁内刷新+扣减一次写完。
  readUsageSummary 读前刷新,余额展示天然反映当日/当期最新额度。
  TDD 新增 5 条真实证明过期水位场景(此前测试全 allowance=0 从未真触发 stale):
  hold/spend 触发刷新、只读路径持久化、**惰性不重复刷新**、未过期不误触发。
  **时区决策**:统一按 UTC(行业标准=存储/边界算 UTC,展示层才转本地);以后接 site/用户时区
  只需换 `refreshRow` 一个换算点,不动 schema/域层。
  全绿:182 单测(+8)+116 集成(+5)+typecheck 净。

**L3.1 三桶(域+阶段1/2/3)已全部完成。** 下一步(L3.2,未开工):Plan 目录+权益层——
仅当 Plan 给账户写入非 0 allowance,懒刷新/三桶消费才在真实业务中显效;
另需落**卡密=支付=同一 Grant**抽象(渠道薄适配器,ledger 归因元数据区分,不建三套扣账实现)。

## 全面"真正 OK" campaign(2026-07-22;PRD=specs/2026-07-22-comprehensive-realness-campaign.md;审计=reports/2026-07-22-capability-debt-audit.md)

> 用户 /goal:除支付真网关外一切真实测试真正打通;核心洞察=债不是"没造"是"造好了默认 OFF"。
> GLM key 定论:Aura config 那把对 bigmodel 四端点×四模型×两头×GET/models 全 401(鉴权层拒 token,非接线);
> model 库接线本就完整(claude-code→litellm→后端,secretRef env 引用),缺的纯是有效凭据——换任意有效 key=改一处网关 env。
> web 决策:收拢为 monorepo(apps/user+apps/admin+packages/*),两独立部署,不合单 app(admin=antd+NextAuth+Prisma 直连,不能与公网面同源)。

- [x] **WS4 可观测**(platform ba7c3f4 / session 4a77f9f):platform-kit registerMetricsRoute(prom-client 默认进程指标+module 标签+fail-open),6 服务各注册+/metrics public 声明;session 补 /healthz(同信封,鉴权门前公开)。kit 110 单测绿(+2)、session observability 7 绿(+2)、全平台单测无回归。agent /metrics 保持 opt-in(端口归部署 env)。
- [x] **WS1 真模型链路**(实证):enforce 真栈 ollama qwen3:8b→全新会话 run.completed、5 帧真流式 delta、
  回"中国的首都是北京。"(非 fake 罐头)。生产级稳定仍需有效云 key(进 .env 即自动升级,GLM>ollama)。
- [x] **WS2 计费点亮**(agent 18b394d/根 52fab2e,实证):切 enforce 真测——零余额受理 **402 硬拦**、
  admin 充值到账、对话结算**真扣 20 积分**(余额 100→80)、ledger 现 model_call 带 run_id。
  **顺带修真 bug**:网关流式模型默认不回 usage→结算捕获 0→零扣费;加 stream_usage(include_usage)修复,
  对生产模型同益。summary/ledger 读面正常(直返对象非 data 包裹)。welcome 100 积分赠额确认。
- [x] **WS3 能力开门**(根 52fab2e,实证):closure-up 补 KOKORO_HUB_SECRET_MASTER_KEY 开启 secret broker
  (原默认 OFF→503→现 resolve 非 503);MCP 写面本已 mutation=on(非 capability_registration_disabled)。
  self 面完整往返受 dev membership 限(namespace=userId 非真 team 成员),归既有 MCP-SECRET e2e。
- [x] **WS4 可观测**(platform ba7c3f4/session 4a77f9f):见上;live 实证 /metrics 真出、/healthz 200。
- [~] **WS6 web 收拢**(web 9dc80f8/2c4626a):
  - [x] phase-1a monorepo 骨架:kokoro-web 从单包(npm)转 pnpm workspace;app 迁 apps/user(249 rename 保历史,
    name=@kokoro/web-user);根 package.json 委派(closure-up 不变);.npmrc node-linker=hoisted 复原 jest-dom→vitest
    peer(strict 下 53 文件全挂);pnpm-lock/workspace 转入库(原按 npm 忽略)。验证:typecheck 干净/484 测试绿/web GET 200。
  - [x] phase-1b 首个共享包 @kokoro/tsconfig:apps/user extends,证 packages/*→apps 消费。
  - [x] 生成器 contract/generate.py WEB 路径 → apps/user/src/contract(+test 路径);还原误生成的陈旧契约(session/web)保最小。
  - [x] phase-2 admin-web + i18n 迁入(web f8e044c/platform a3a8cb3):kokoro-admin-web→apps/admin(62 文件)、
    kokoro-i18n→packages/i18n(@kokoro/i18n,admin 唯一使用者)。**关键攻坚**:①两 app 版本全面分歧
    (admin R18/Next15/antd5/vitest2 vs user R19/Next16/antd6/vitest4)→ .npmrc 从 hoisted 切 isolated
    让各 app 隔离 node_modules 拿正确版本(hoisted 扁平会 React 混版破 user 渲染);②pnpm isolated 下
    jest-dom /vitest 自动集成解析到异实例致 matcher 静默不注册 → setup 改显式 expect.extend(从 /matchers)。
    platform 移除后剩 8 包全绿(1020 单测)。验证:user 484/admin 25/i18n 12 测试全绿、三方 typecheck 干净、web 200。
    遗留:platform 盘上 admin-web/i18n 产物目录待清(rm 受限,待授权)。
  - [x] phase-3 i18n 泛型化 + 版本对齐(web 61cb01d/b544aa0→35b90e0/33975c8):
    ① i18n 引擎泛型化:apps/user/src/i18n/resolve.ts 委派 @kokoro/i18n(与 admin 同引擎),公共面不变 42 处零改动,484 绿。
    ② 版本对齐:admin R18/Next15/antd5/vitest2 → **R19/Next16/antd6/vitest4 与 user 完全一致**。
       React19 补 2 处 useRef(undefined);Next16 加 force-dynamic(后台全动态,避 turbopack 预渲染模块初始化坑);
       antd6+pro-components(官方 peer 为 antd5)经 typecheck/25 测试/Next16 生产构建三验通过(build SSR 模块求值暴露缺失导出→通过=导入全满足)。
       验证:admin typecheck+25 测试+生产构建绿、user 484 绿、web 200。**版本分歧债清零**。
    - 残留(非阻塞):antd6 上 pro-components 运行时视觉 smoke 待 admin 栈浏览器验(需 platform-admin 网关+DB);ui 共享包随需再抽。
  - 注:contract/tests/test_generate.py 2 预存红(raw_kinds 18 vs spec 20、request_id 禁用词)=spec 漂移老债,非本次。
- [x] **WS5 真机总证**(全栈真起真测,不留尾巴):
  - **4 镜像全 build 成功**:platform 1.7G(修 Dockerfile 删已迁走的 admin-web/i18n COPY,9c81c41)、session 878M、
    agent 1.26G、web 401M(monorepo Dockerfile,1727f0a)。
  - **provision.sh 起全 prod 容器栈**(连同一套 infra,.env.prod 生成密钥/RS256):exit 0,7 平台服务+session+agent+web 全 Up,seed 完成。
  - **全栈烟测全 200**:7 平台 /healthz + session /healthz+/metrics(WS4) + platform /metrics(WS4) + web /。
  - **端到端对话 run.completed**:RS256/jwks 签发 + enforce+welcome 100 积分受理 + agent fake 模型 + SSE 全链(todo/delta/completed)。
  - **抓修真尾巴**:共享卷 kokoro-workspace 默认 root:root,但 session/agent 非 root(uid1001)→ agent assembly
    PermissionError。compose 加一次性 workspace-init 服务 chown 1001:999,三者依赖它。**修后对话 run.completed 验证**。
  - README 修正为 provision.sh 真入口(原引用不存在的 docker-compose.prod.yml)。
  - 剩余(非阻塞):真模型仍需有效 key(fake 罐头是 prod 预期占位);admin-web 未入 prod compose(独立部署,需 platform-admin 网关栈);k8s manifests(deploy/k8s 半成品)。
- [~] **WS7 INDEX.md**(web e063b44/根):新增 kokoro-web/INDEX.md monorepo 根架构地图(固化 phase-1/2 攻坚:
  两 app 边界/isolated linker/jest-dom 坑/扩展规则/欠账);docs/CODEBASE_MAP.md kokoro-web 条目改 monorepo+pnpm;
  packages/i18n/INDEX.md 随迁移已带(消费方含 admin,现同仓准确)。剩余局部 INDEX 随 phase-3 补。

## 第二轮全仓打磨(2026-07-16 起;用户面 + 能力运营面 + model 消费侧对齐)

> 目标(用户 /goal):所有功能打通、用户真实进来体验、GLM 注册进去、litellm 对外 claude-code 门面。
> fast/thinking=用户选的两种模式,与 model 正交,都保留(见 memory)。model 目录=kokoro-model 权威,我只做消费侧对齐。

- [x] **WEB settings 弹窗化 + 深度打磨**:settings 整页→卡片浮层;i18n 9 语数据驱动 overlays + google 免费翻译管线(config-not-code);skills/mcp 面板搜索/空态/两步确认;composer fast/thinking 标签 i18n。(web 多 commit,已 push)
- [x] **GLM + litellm claude-code 门面**:litellm 网关 claude-code 别名→GLM;session DEFAULT_MODEL=litellm:claude-code;closure-up 三级后端回落(GLM→opt-in ollama→fake)+ SIGKILL 重启防竞争。GLM 凭据只经 gitignored .env 运行时注入,绝不落提交文件。
- [x] **HUB skills 运营官方目录面**(platform 前序 commit):listOfficialCatalog + 单参 official 治理路由 + admin-web ROW_ACTION_FORMS(official-flags/curation/review)。
- [x] **HUB MCP 运营官方目录面**(platform 0558b66):listOfficialCatalog + 单参 official 启停/软删 + admin-web 注册表单(transport/allowed_tools/secret_ref)。hub 294 pass。
- [x] **MODEL ModelLabel 写侧闭环**(platform cef91ef):ensureModelLabel(幂等 upsert)+ POST /model-labels/ensure + admin manifest create 动作 + admin-web model:model-labels 表单。model 单测 105 / 集成 33(真 MySQL)pass。
- [x] **MODEL 目录 seed**(主仓 0958d76):closure-up seed 补种 kokoro-default/dev-mock 标签,兜底 binding 回填;抛弃式实例(4229 同库)验证建/幂等/列出 200。
- [x] **WEB 多模型下拉(消费侧 wire)**(model 5051b42 / session e3df799 / web df31e09):候选源从静态 profile 升为 kokoro-model 目录。leaf→根 TDD:①model 加 runtime `GET /model-labels?featureKey`(active 过滤,runtime-internal 层);②session billing client `listModelCatalog` + handleModelCandidates 优先目录源(name=label.key、display_name 透传、key 命中缺省名=is_default),**fail-open** 目录不可达/空则回落 profile 候选,可用性过滤(resolve)语义不变;③web ModelCandidate 加 display_name?、composer 三处渲染 modelLabel(display_name??name);④seed label.key 对齐 binding.labelKeys(claude-code/kokoro-dev-mock)否则被可用性过滤剔除。验证:model 108单测+33集成(真MySQL)、session 384(MODEL-5/6/7目录源+契约锁 listModelCatalog wire)、web 473(唯一红=既有 artifact-card 遗留)、model HTTP 抛弃式实例(4229)实测。
- [x] **skill 上传(bespoke)**(platform 8d49af5 / 主仓 closure-up 存储位补 hub 节):admin-web SkillUploadModal 两步流(Upload.Dragger→裸 base64→preview 候选表+冲突/勾选→confirm 逐项 published/unchanged/failed),走 /api/action 网关透传上游 UploadPreview/ConfirmResult 享 RBAC+审计;上传归属恒 namespace(官方位只 seed/管理)。**顺带修** closure-up storage.yaml 缺 hub 节导致 confirm 恒 503——补 hub 本地包体节 + 提前落盘 + hub env 传 KOKORO_WORKSPACE_CONFIG。验证:tsc/lint/Next 编译清、19 单测绿;契约 e2e 真 hub 实测 preview 200/confirm 200 published rev1/幂等 unchanged/坏包 400,形状精确吻合 schema。

## 积分（credit）定价与利润体系（2026-07-17;PRD=specs/2026-07-17-credit-pricing-strategy.md）

> 目标(用户):高利润且合理的积分策略(要赚钱)、本地 admin 手动充值测试、支付后续。吸收 hix general_agent
> 思路(credit-USD 锚点/加价倍率/ceil house-favor/计量与钱包分离),超越其短板(加价单一可配可审计、钱包侧套餐/充值我方自研)。

- [x] **研究**：参考项目钱模型(1 credit=$0.006/媒体 2×加价/ceil/无套餐充值) + Kokoro credit 架构(per-labelKey 定价/hold-settle/owner=namespace team/shadow 仍扣减)。
- [x] **PRD 定案**：1 积分=10000 micros=¥0.01;售价=真成本×margin(≥4×文本);grant(+delta)+reset(set-to-value);向上取整/套餐/免费额度/支付/媒体计费/内置定价迁 seed:builtin 留挂点。
- [x] **credit 落地**(platform b662a38)：domain/amount(MICROS_PER_CREDIT/ceilToCreditMicros/非负解析)、resetBalance(repo/service)+ POST /admin/credits/reset(set-to-value 带符号分录,不得低于 held)。单测 157/集成 105 绿。
- [x] **加价计价**(主仓 closure-up)：chat 20/60→40/120 micros/token(≥4× 毛利)。
- [x] **admin 手动充值**(platform 0f3b502)：credit-accounts 加 reset 动作 + admin-web ROW_ACTION_FORMS grant/reset(账户行,owner 预填,整数积分→micros)。契约+buildBody 单测绿。
- [x] **用户面积分展示**(web cc26b37)：billing/format formatCredits(÷10000)、计费面板显示「N 积分」。web 476 绿。
- [x] **全链 e2e 验收**(真栈,新 40/120 计价)：签→清零→发放100→重置到50(set-to-value 分录 -500000)→对话 run.completed→结算扣减 50→47.96 积分、ledger model_call -20400 带 run_id。**全绿**。
- 挂点(未做,PRD §9 记明)：向上取整(需夹具升尺度)、支付充值、套餐/免费额度周期发放、媒体计费、长上下文加价、内置定价迁 kokoro-credit seed:builtin。

## 支付充值整体闭环（2026-07-17;PRD=specs/2026-07-17-payment-topup-strategy.md）

> 目标(用户):用户自助购买积分整体闭环(浏览→下单→支付→到账→用→扣→查),与 admin 手动充值/重置并存不冲突。
> 研究结论:payment→credit 到账闭环已在代码(订单/webhook/幂等 grant order:<id>/退款/web 购买 UI),仅 3 缺口。

- [x] **研究**:payment 全景 + 缺口(startCheckout 501 / dev 无 seed plans / payment 未 boot)。
- [x] **PRD 定案**:mock provider 打通同形 dev 闭环(切真网关流程不变);积分包量折扣(¥0.01/积分,大包更省);毛利仍由消费侧 ≥4× 加价承载。
- [x] **payment**(platform 2b963ab/2b94a5a):startCheckout mock 档(建单+返回 /billing/pay/<orderId>) + web-bff caller 放行店面(/plans GET)/结账(/orders/checkout);到账走既有 confirmOrder→grant 恰一次。单测 205/集成 70+23 绿。
- [x] **web**(web 85069b6):模拟收银台页 /billing/pay/[orderId] + /api/billing/mock-pay BFF(签 mock webhook 驱动到账) + auth mockWebhookSecret(仅 dev)。web 477 绿。
- [x] **closure-up**(主仓):boot payment(4241) + seed 4 积分包 + seed mock 网关 + web KOKORO_PAYMENT_BASE_URL/mock secret。
- [x] **整体闭环全链验收**(真栈,全绿):签→清零→浏览 4 套餐→下单得 checkoutUrl→mock 支付验签→到账 100 积分(+幂等重放不双发)→对话 run.completed→扣减 100→97.96 积分→流水含到账(+)与 model_call(-)。
- 挂点(未做,PRD 记明):真网关 hosted checkout(Stripe/支付宝/微信 session)、订阅周期计费 UI、发票/税、web 支付成功页打磨。

## 上线准备（2026-07-19 起;用户 /goal:做完整 + 为上线做准备。部署目标=单机 compose(当前)+k8s(都支持);真模型后接、先 fake 跑通)

> 只读上线审计结论:安全底子强(生产 fail-closed/JWKS/RS256/无误提交 secret);6 真阻塞(部署编排不可启/Dockerfile 缺 hub/无 redis/SMTP 未实现/生产模型链路缺/缺应用层部署单元)。

- [x] **块1 单机全栈 compose 基线**(web 75c8a71/session 6c6547d/agent 6ecf473/platform f6d9217/主仓 829ed47):
  - platform Dockerfile 预拷全 workspace 成员(补 i18n/platform-admin/hub/admin-web,阻塞#2)
  - web/session/agent 各生产 Dockerfile + .dockerignore(web Next standalone/session tsx/agent uv,均非 root);web next.config output:standalone
  - 主仓 `docker-compose.prod.yml`:infra(mysql/mongo/**redis**/minio)+一次性 migrate+平台七服务+session/agent/web+litellm,env 经 `deploy/.env` 注入,存储共享本地卷,生产硬化(jwks/enforce/strict egress)
  - `deploy/.env.example`(全变量占位)+`storage.prod.yaml`+`README.md`(RS256/secret 生成/seed/硬化清单)
  - **`docker compose config` 校验通过(16 服务全解析)**;最终 build&up 真烟测需用户主机(拉基础镜像),README 记明
  - 根 .gitignore 补 .env 兜底
- [x] **块2 k8s manifests**(核验已完整):deploy/k8s/base(namespace/infra/platform/app/jobs/kustomization + kind overlay)
  带 --load-restrictor LoadRestrictionsNone 渲染出 **44 资源**(15 Deployment+14 Service+5 PVC+2 Job[migrate/provision]
  +Ingress+RBAC+Secret/ConfigMap),覆盖全 16 服务+迁移/seed,无陈旧 admin-web/i18n 引用,README 已记 flag。
  真集群部署待用户集群(与 compose 同状态)。原"补平中"台账陈旧,实早成型。
- [x] **块3 SMTP 邮件 + deliveryMode 生产硬闸**(platform defbbf7):kokoro-user 加 smtp 档(nodemailer,窄口 MagicLinkMailer,原文 token 只进邮件)+ config SMTP_*/MAGIC_LINK_BASE_URL + 路由 smtp 分支(链=<base>?token=,发信失败 502)+ main.ts 生产禁 response fail-fast/smtp 缺配拒启动。user 单测 109 绿、tsc 干净(集成 8 需 DATABASE_URL_USER,环境性)。
- [~] **块4 env.example(平台侧)+ 可观测 + 卫生**:
  - [x] env 部分(platform f866ff5):平台 5 服务(site/user/model/credit/payment).env.example 补 6 个 KOKORO_INTERNAL_SECRET_* + model provider 变量占位。
  - [ ] 可观测(剩余):平台 6 服务补 /metrics、session 补 /health(需改 session 自定义路由器)。
  - [x] 卫生(主仓):ops/langfuse/.env.local untrack(保留磁盘)+ 建 .env.local.example + 根 .gitignore 负例外 !.env.*.example。用户已确认。
- [ ] **做完整**:B3c 定价 seed 收编、B1d 按模型消费分解

## prod-realness + UX 打磨批次（2026-07-20;用户 /goal:为什么本地还是模拟、prod 怎么办;认真打磨真实走）

> 用户诉求:积分小数→整数;settings 跳/大小不一;订阅与积分面板分开;GLM 真 key 进 model 子仓;产物预览;
> sandbox+s3 真实走;docker 沙箱 + local 默认;dev debug 面板(参考 ai-collection AccountDevTool)。「你自己定顺序全做」。

- [x] **① 积分整数扣费**(credit 1e6e59f):holdForUsage/settleUsage 走 ceilToCreditMicros(每次最小 1、向上取整);夹具升到整积分尺度;164 credit 测试绿。
- [x] **⑤ settings 拆分 + 不跳 + 尺寸统一**(web a231296/f780634):积分/订阅拆两 tab(CoinIcon/SparkleIcon);.layout 固定高 min(72vh,640px) 消除按 tab 变形;contentBody 动画去 translateY 只淡入消跳动。
- [x] **⑦ 产物预览媒体/HTML**(web 28c6620):delivery 分支改用 PreviewBody 统一分派(图片/音视频不再被挡 unsupported);text/html 排除出 isTextual 落 MediaPreview sandbox iframe 真渲染。(注:audio 单测预存红,jsdom blob 环境,非本次引入)
- [x] **S3 真持久化落地实证 + 工作区清理**(主仓 bc57c3e/5370bc6):
  ① closure-up 加 dev S3 存储档(KOKORO_DEV_STORAGE=s3,三段切 minio,凭据取 .env.dev,启动幂等建桶;
     默认仍 local 向后安全)。**真跑实证**:经运行中的 hub 真发布 skill(preview→confirm published rev1)→
     包体落 minio `skills/<ns>/<name>/<content-hash>.zip`,本地 hub-packages 无新增 —— 确证 skills
     持久化走对象存储。dev 档已持久化在 .env.dev。
     口径澄清:skills **元数据真源=Mongo**(多租户),**包体(内容寻址 zip)=storage.yaml 的 hub 段**,
     与 workspace/deliveries 三段同形,一起切 S3。
  ② 工作区清理:根目录 8 张散落截图 + web 2 张 + kokoro_artifacts/kokoro_hub + kokoro-web/tmp(5.6M)
     + 全仓 __pycache__;保留 tmp/closure(运行态)与 tmp/参考。
  ③ 教训文件三处并一处(docs/lesson.md 41 条为唯一权威),移除被 docs/task.md 取代的 tasks/ 与
     claude-progress.md,并修掉 CLAUDE.md/PROTOTYPE-STATE.md 里指向已删文件的活引用。
- [x] **③ S3 真存储可零改切换**(主仓 a7ba5f3):deploy/storage.s3.yaml(三段 S3 单桶 kokoro/minio:9100)+ provision.sh minio/mc 幂等建桶 + .env.example 切换开关+WORKSPACE_S3 凭据键。**对真 minio 往返验证**:S3PackageStore put/get+幂等、S3Archiver archive_tree 键布局/隐藏跳过;storage.s3.yaml 经真 load_storage_file 校验。
- [x] **④ docker 沙箱 + 部署默认 backend**(session bc684b5/主仓 51f6677):根因=deploy 无 namespaces 文件→EMPTY_PROFILE→backend 'state'(虚拟 FS)=用户所见"模拟"。加部署级 env 兜底 KOKORO_DEFAULT_BACKEND(profile.backend>部署默认>库内 state,不改库默认;避多租户枚举冲突),deploy 设 local_shell;.env.example 补 KOKORO_DOCKER_IMAGE(注 docker.sock 权限敏感故非默认)。**docker 后端对真 docker 往返验证**(bind mount/exec/双向文件/复用/回收);namespace 32 测试绿含新优先级三档。
- [x] **测试信号治理**(web a3f56f8 / session 9ba2d21 / agent a33b2c8 / platform 2a1a5ab):跑全量才发现"绿"是假的——
  ① web 3 红(2 条我引入:面板硬编码中文、i18n 新键压破 95% 闸);
  ② **MT 管线真 bug**:哨兵 KVARn 是拉丁词,ru 音译成 КВАР0、ja/ko 拆成「KVAR は 0」,还原失配 → 7 语种 17 条坏译文
     带着 'KVAR' 字样进 UI。改无字母哨兵 %%n%% + 容错还原 + **占位符校验闸**(丢了就判失败,宁可回退中文源);
     en 长期不在 TARGET_LOCALES 从没翻过 → 补进列表 + 人工精修 20 条术语(MT 把「积分」译成 integral/Points)。8 语种现 100%;
  ③ session 8 条 / agent 10 条 S3 集成因**写死的 minio 密码**整组静默跳过(S3 链路真覆盖为零)→ 改取真源、跳过必出声,现全打真 minio 绿;
  ④ **platform 569 条集成层从没被跑过**(pnpm -r test 只含单测、集成需 DATABASE_URL_* 无人接线)→ 一跑 27 红,
     其中 9 条是我整数扣费的回归(只更了单测夹具);quota「不双算 buffer」用例因 ceil 后 hold==实收而失去区分度,
     加高价 label 造真 buffer 保住验证意图;补 scripts/integration-dev.mjs 一键入口防再空转。
  **现状:web 484 / session 387(零跳过) / agent 609(零跳过) / platform 单测 1056 + 集成 569,全绿。**
- [x] **⑥ dev debug 面板**(web 05a9ef7):右下角可拖拽/折叠 dev-only 浮层,聚合 namespace/余额(真)/引擎相位/run/会话/模式;/api/dev/status 门控靠 prod 缺失的 mockWebhookSecret 信号(与 mock-pay 同源,生产恒不渲染)、只读非机密无写入面。**Playwright 实测渲染+真数据(余额 192.86 积分)**。
- [~] **② 真实模型**:GLM key 定死(用户给的 Aura config.json 那把 = kokoro-agent/.env 现有同一把;raw+JWT×openai/anthropic×paas/coding/anthropic×glm-5/4.6 全 401,连 GET /models 纯鉴权都 401——bigmodel 侧拒,非接线)。**改接本机 ollama qwen3:8b 真模型**:litellm claude-code 别名 → host.docker.internal:11434(直调实测 claude-code→"4" 真出);dev 默认持久化(deploy/.env.dev KOKORO_DEV_LOCAL_FALLBACK=1,gitignored)。**端到端实测**:全新会话 chat 回 MANGO/PONG(流式 message.delta,非 fake 罐头)。坑:①固定会话 ses_chat_smoke 重启前残留仍出 fake,新会话才真;②8B 简单 chat 真且快,重多步工具编排慢/偶卡(小模型限,非接线)——**要稳的生产真模型仍需有效 GLM/云 key**(有效 key 进 kokoro-agent/.env 即自动升级,GLM 优先级>ollama)。

## 全仓体验打磨 + 计费管理 campaign（2026-07-18 起;用户 /goal:好好打磨、完整全面、计费管理两侧覆盖）

> 用户定调:真网关收钱砍掉(个人无商户、做海外,mock 闭环够用);两条轨——A 全仓 UI/交互打磨(我自主推)、
> B 计费管理(三切面全要,且"计费面板两处:用户 settings 里的 + 后台 admin 的"都覆盖)。
> 方法:每面 Playwright 自动化体检(横向溢出/布局抖动/热区/吸顶/字体回流)→根因→修→真栈实测→分批提交。

### 完整 UI 全流程走查（2026-07-18,Playwright 连续实走,全绿）
- [x] 一条真用户路径端到端:①匿名落地页(navbar 64px/sticky/无横滚)→②magic-link 登录→③工作台对话(消息→assistant 回复→run 完成;本地预览路径无真实模型故不计费,符合预期)→④计费面板 0 余额(**低余额预警条触发**,B1 时余额健康没验到)→⑤买入门包→**真 mock 收银台 UI**点确认→"支付成功,积分已到账"余额 100→⑥面板余额 100/预警条消失/到账流水"订阅 +100"按天分组。截图 walkthrough-billing-low-balance/after-topup。

### 轨 A：UI / 交互打磨（逐面体检）
- [x] **落地页 `/` 顶栏三缺陷**(web 86014d0):高度抖动(.page/.topbar flex-shrink:0)+不吸顶(.page>*:not(header):not(nav))+横向滚动条(.hero::before 横向 bleed 归零)+页脚热区 17→32px。真栈实测:顶栏恒 64px/sticky、滚动吸顶、桌面+375移动无横滚。
- [ ] 登录页 `/login` 体检(共用顶栏,验证修复覆盖)
- [ ] 登录后工作台体检(空态 hero / 对话线 / composer / 设置浮层)
- [ ] canvas 三栏 + 各面移动档体检

### 轨 B：计费管理（三切面 × 两侧;侦察中）
- [~] **侦察**:并行两 Explore agent 摸用户侧(web 设置计费面板+BFF+session/credit 数据链路+ledger 分录字段)与 admin 侧(admin-web 计费资源/行动作+credit/payment admin 端点+定价规则存储)现状与缺口。
- [~] **B1 用户用量透视**(用户 settings 侧):
  - [x] B1a 契约补吐(credit 9f7c82a/session 0d88bc1/web 9b18728):ledger 补 balance_after_micros、summary 补 quota_micros/quota_period(DB/domain 早有,HTTP 此前丢弃)。credit 19/session 76/web 9 单测绿。
  - [x] B1b 面板升级(web 9b18728):按天分组+当日净额、余额走势 sparkline、消费/入账筛选、run 标记、配额行;顺修 formatDate epoch ms ×1000 既有 bug。
  - [x] B1c 低余额预警(web 9b18728):可用余额<50 积分预警条引导充值。
  - [x] 全栈实测(restart 全栈,真数据):summary 经 BFF→session→credit 返 200 带新字段;两笔充值造流水→面板显示余额 4000 积分、趋势 sparkline 上升、按天分组「2026/7/18 +4000」(日期修复实证,旧 bug 显公元 5 万年)、reason/时间/±正确、低余额条与配额行按逻辑正确不显。
  - [ ] B1d 按模型分解(最重,剩余):UsageRecord 无用户端点+modelBindingId→模型名映射,需新聚合端点。归后续。
- [~] **B2 管理侧运营台**(admin 侧):
  - [x] B2a/B2b 聚合端点(platform f273336):credit GET /admin/credits/stats(账户计数+余额/冻结/发放/消费,DB aggregate)+ payment GET /admin/payments/stats(订单按状态计数+营收按币种 groupBy)。credit 164/payment 204 单测绿。**全栈实测**:credit 6账户/余额4245.92积分(=发放4700−消费454.08 自洽)/payment 5单4paid/营收¥34.50 多币种正确。
  - [x] B2c admin 总览页(platform 936d4b6):网关 getBillingOverview(直取两 stats,route 可信常量,单模块降级 null)+ server.ts GET /api/billing-overview + admin-web 运营概览首页「计费总览」卡片(营收/订单/发放/消费/余额/账户)。网关 getBillingOverview 单测 2 条+gateway 31 绿,四仓 tsc 干净。admin 全栈浏览器实测需另起网关栈(记录在案)。
- [~] **B3 定价规则治理**(纠正:无"加价倍率"字段,是平价 amountMicros 规则,毛利靠定高):
  - [x] B3a update 端点(platform 84b881f):credit domain/prisma/service/schema/route/contract 补 updatePricingRule(仅可变字段:价/状态/生效窗;身份键不可变);POST /admin/credits/pricing-rules/:id。credit 单测 115 绿。**全栈实测**:真 credit+DB 改价 120→480/disabled→持久化→404/400 负向→改回 120,全通。
  - [x] B3b admin 表单(platform cd12fa7):RESOURCE_FORMS credit:pricing-rules(create,新增 createOnly 抑制误走 create 的行内 Edit)+ ROW_ACTION_FORMS pricing update/set-quota;buildBody 单测 11 绿、tsc 干净。admin-web 浏览器实测需另起 admin 栈(4290 不在 closure-up 托管),声明式配置由单测+既有 resource-table 保障。
  - [ ] B3c seed 收编(后续,清理):散在 closure-up 的定价(chat 40/120)迁 kokoro-credit 权威 seed:builtin(仿 model)。非能力,纯架构清理。

## P0(总设计稿 Wave 1-3;信任与一致性新 P0 来自代码审计,先于产品 P0)

**Wave 1 安全与能力基础**(顺序:TRUST-ROUTES 先冻结内部调用契约):
- [x] **TRUST-ROUTES**(150aa25/f9802f1/c4b89a1,e2e 凭据强制档绿):platform default-internal 全路由策略+per-caller 分级凭据(public/runtime-internal/web-bff/admin)+生产 fail-closed。现状纠偏:守门件只护 /admin 前缀且共享单 secret 空值直通——hub 路由完全无鉴权、namespace/scope 来自请求、credit 启 secret 后 session billing client 不带密钥。
- [x] **AUTH-P0**(e4068d6/6260da5/8c26740,浏览器六步实走+截图;SMTP 仍留位=SEC-2):web BFF 密封 cookie(浏览器不持 bearer)+magic-link web 流+nonce 防 CSRF+SMTP+日志脱敏(现 magic-link log 档把原文 token 写日志!)+/auth/sessions 收编为内部口。现状:任意邮箱直登+token 在 localStorage。
- [~] **HUB 链**:HUB-AUTHZ✓(0bccba3 三权限面+mutation 503 门)→MCP-SECRET✓双半场(ed198f6/d11ae9a hub;9c8f4cd agent,e2e 绿)→MCP-REVISION 契约✓(7f8cc7f)→**HUB-CONSIST✓**(hub 9710400/session dfd1280/agent 2e30fe0/gate 560d70c:revision 簿记+config_hash 单算方=hub+runtime McpGrant 面+session 经 hub resolve 删 MongoSkillPool+agent 按 revision 快照消费 fail-closed+mutation 门 KOKORO_HUB_MCP_MUTATION+§8.2 9/14/15 断言,e2e 全绿)——**Wave 1 全项收口**;原缺陷句留档:Hub 三权限面;McpGrant {scope,name,revision,config_hash} 版本锁+实时撤销;secret handle broker+SSRF/egress;**split-brain 修复**(hub/session/agent 默认 Mongo DB 不同!session 池解析忽略审核/运营排序——session 改调 Hub 单解析器,MCP mutation 在跨仓门通过前 503)。
- [x] **CREDIT-CACHE**(c5a8ac3):owner 正缓存键补 siteId(现跨站复用 owner active 结果)。
- [x] **MODEL-SOURCE**(3b4c743):profile.allowed 降展示过滤,platform resolve 为可用性权威(M-1 后半)。

**P0.5 结案(2026-07-12 调查完毕)**:
- [x] **MCP-REVALIDATION-HANG 调查**:单 worker 下五类忠实建模(真 FastMCP+supervisor+control,双重问四连接链)全部到终态,桥配对 trace 无误——agent 桥/连接生命周期无罪(绿钉 ed5fc62 留作护栏)。**主嫌=双 worker control 竞争**(实录第 4 条多余 MCP 连接;closure-up 曾无条件 spawn worker,残留同组消费者拿走 resume 重放)——已加独占守卫缓解;**根治归 Wave 2 R2**(control durable inbox/receipt/lease fencing,正合纲领故障矩阵"agent inbox 后 apply 前"场景)。

**Wave 2 可靠性(D5 持久意图模型,R0-R7 顺序)**:
- [x] R0 故障护栏五钉(8ca5fc6/4c154dc)+R1 契约冻结(e471822)
- [x] **R1 dispatch CAS**(e40fb76/d844d5c/85aec79):session 写 pending+fence→agent CAS claim→ACK 后置;超时 reconciler 合成 dispatch_exhausted+billing release;dispatch_dlq;run.started 最小 outbox;R0 钉1 转正式绿。
- [x] **R2 control outbox/inbox+receipt**(契约 74e6dfc/24b6dd2;session c688817/4bb25be→merge 6dd62fd;agent 4a056e3):session control_outbox 先落库后 XADD+启动补发 scanner+receipt 消费+GET 回执端点;agent inbox persist→ACK→apply→applied+双时点回执+重启续办+fingerprint 防 stale;R0 钉3 转绿;gate 增 receipt applied 断言,e2e 全绿。P0.5 双 worker control 竞争根治于此。
- [x] **R3 tool effect journal**(agent 7887e0c/feb09e3):副作用工具 started/succeeded/failed 记账+重放守门(unknown-outcome 不自动重放,幂等白名单收敛);工具内 HITL interrupt 撤销 started 行放行重入(跨仓联测抓修)。
- [x] **R4 critical/terminal outbox**(agent f0a4616/6edbc23,契约 6329f8a):durable_seq/event_id 上 raw 信封(critical 集=started/control.receipt/terminal);queued→published 补发 scanner+published 无回执超宽限重发;first-terminal fence+superseded;consume/close 握手(写者分域 CAS manifest);R0 钉2 转绿。
- [x] **R5 双水位+quarantine+finalization**(session ff40c5c/01c1c9c):persisted=receipt 连续前缀/projected 逐 seq CAS;终态连续性门(跳号不收口);two-stage parse quarantine→contract_incompatible 终态权;finalization reconciler(间隔 env 可调);R0 钉5 转绿。缝合修复:control receipt 落 durable 回执(终态 deferred 卡死)。
- [x] **R6/R7 billing durable**(session f005910):billing_journal 相机 hold_pending→held→settle/release_pending→终局;崩溃窗口 adopt/孤儿释放;compensation scanner+stuck 告警;hold 临期告警;R0 钉4 转绿。**Wave 2 R0-R7 全闭环,R0 五钉清零**;gate += R2 receipt/R7 journal/R5 producer_closed 断言全绿(容器名假空转已修)。
- [x] **后续硬化**(HARDEN,spec 268c220):gate chaos 门控段(3352a95,E2E_CHAOS=1 kill agent 验 durable 去重/kill session 验 billing 补偿,3 轮绿,缺省档零影响)+manifest 自动 GC(session 0641a1e,producer_closed+TTL 才删,381 绿)+admin 网关刷新六模块 online 补证(截图 wave5-admin-{user,hub}-online)。
- [ ] 新隐患(非阻塞,harden 发现):settleRunBilling 的 settle_pending→settled 非原子——快 finalization 与 live 终态路径并发会相位回退(ledger 幂等未双花,仅 journal bookkeeping 抖动);建议后续原子化 CAS 排期。现网 4290 stale admin 网关待授权重启到当前构建。

**Wave 3 用户可感 P0(后端+BFF+UI 完整竖切,全部浏览器实走+截图 tmp/screenshots/wave3-*)**:
- [x] **SESS-LIST**(session 3125a65/web eee8320/gate 8846b07):GET /sessions owner 隔离+复合游标+软删不出+跨 owner 不可枚举;web rail 服务端水合,localStorage 退为访问缓存;§8.2-6 五断言绿。
- [x] **WEB-BILLING**(credit 5986941/session 3125a65/web 3b81166,契约 23b6f7c):credit runtime 窄读→session /billing/summary|ledger 代理(namespace 派生账户,微单位字符串直透)→web 余额卡+流水+402 专用说明(无假充值);gate 授信/settle/run_id 回填真数断言绿。
- [x] **WEB-SKILLS**(web d3403f7/e9587e3):/api/hub BFF 接通 hub self 面(web-bff 凭据+信封 scope,浏览器伪造头天然丢弃);技能池/启停/required 锁/上传 preview→confirm/配额/审核三态/pinned 接线。**Wave 1-3 P0 全清**。
- 收口备忘:dev 闭环 user 服务 magic-link 签发 500(陈旧进程/SMTP 留位,SEC-2 范围;gate E2E-30 auth 断言绿,非回归)。

## P1

- [x] **TEAM-1**(user e4cecd4/web 4ea1352+c4fb354,spec dd8f87a):/bff 团队自助面(邀请 token 只存 sha256、V1 登录后 in-app 露出;换签=活跃成员校验→teamId 重签→BFF 重密封,token 不回浏览器);web 团队面板(切换/邀请/成员管理);admin manifest 团队动作已"点了即真";双上下文五步实走+7 截图(wave4-team-*);user principal 未下 runtime。
- [x] **OBS-1**(session 079fb26/agent b22baa2,spec dd8f87a):双仓 /metrics(prom-client/prometheus_client,kokoro_ 前缀 20 项;agent 端口 env 缺省关);卡死检测(KOKORO_STUCK_RUN_THRESHOLD_MS 缺省 10min,只告警不杀 run);补偿/水位滞后指标;fail-open;V1 无 tracing(明确不镀金)。
- [x] **MCP-UX**(web df101fc,spec 89b78e8):连接面板(servers/secrets 两 tab,注册向导/启停/软删/handle 管理值只进不出);hub 错误信封人话化(http/私网拒/broker 503);secrets 503 不拖垮 servers 面(实走抓修);浏览器实走+4 截图(wave4-mcp-*)。
- [x] **MODEL-UX**(session 9f0ffde/web 00687df,契约 7bcd361):GET /models=allowed∩platform resolve 可用性(off 档退化全列,恒含缺省);web 输入框模型下拉+首条锁+wire model;gate += populated 断言(候选≥1+恰一 is_default)绿;web 组件/engine wire 测试全覆盖。配置面事实:动态 teamId 无法静态预声明(activeProfile fail-loud),真 auth 栈恒单候选;per-team 模型策略需未来运营配置源(归 MODEL-ADMIN/站点运营,非欠账)。
- [x] **AGENT-PRESET agent 半场**(agent f4e7b6b,spec 89b78e8):三源目录基建已在,补未知 preset fail-loud=assembly_failed(不再静默回退 general);gate 补 personas/poet.md(db93470)成"加文件零代码"活证据。web 选择 UX 归批3。
- [x] **ARTIFACT-LIB**(session 2f524fd+5ed8292/web 4058aeb,契约 62985d5):GET /artifacts 跨会话聚合(sessions $lookup 收窄 namespace,同 hash 收敛取最近,复合游标)+内容寻址下载(跨 namespace 404);web rail"作品"卡片网格;gate 3 断言绿。
- [x] **SHARE-1**(session 同上/web df140cd):session_shares(shr_+32hex 不可枚举,partial unique 幂等,撤销即 404);公共 /shared/:id 无 auth 只读面(鉴权门前单段精确放行,pending_pauses 恒空,不泄 namespace);web 分享按钮+公共只读页;gate 5 断言绿;公共页/撤销 404 主控 live 复证(截图 wave4-share-public-live)。
- [x] **PAY-2**(platform ac3376f+00bdcff/web 2032528):三驱动真验签+Subscription+refund(半场同前);storefront GET /plans+POST /orders/checkout(未配 provider 诚实 501);web 价格页套餐卡+"支付暂未开通"诚实态(截图 wave4-pay2web-*,payment 203+70 绿)。provider 沙箱真跑通留运营配置后(非代码欠账)。
- [x] **SITE-REAL**(site 8940841/web 8428eed/gate 6c3d5c8,spec 75eb3d1):域名子资源(一次性 TXT token,node:dns 验证,本地域 admin 直标,公网直标 400)+host→resolve 只出 verified(brand 直挂两可空列);web Host 派生 site+品牌注入(30s TTL 缓存,SITE-REAL-FALLBACK 待 Wave6 收紧);双域名双品牌实走截图(wave4-site-a/b:Kokoro Music vs Acme Studio);gate resolve 断言绿。
- [x] **SEC-2**(user 95d68c2/session 6e70b9d/gate 2f7ff59,spec 75eb3d1):user RS256 签发+kid 指纹+/.well-known/jwks.json 双 kid 轮换;session KOKORO_AUTH_MODE=jwks|hs256(生产 hs256 fail-fast,JWKS 不可达 fail-closed 401,未知 kid 强刷一次);magic-link email+ip 双维 Redis 限频(挂了 fail-open+WARN);gate E2E-40 真签发切 RS256/JWKS 档+hs256 打 jwks 401 负向,全绿。
- [x] **AGENT-PRESET web 半场**(session 263c623/web bf3973b/gate b8f30c9,契约 8ad4384):GET /agents(profile.agents+general 缺省)+输入框 agent 选择器(首条锁/单候选隐)+wire agent;gate populated 断言(poet+coder+general 恰一缺省)绿;空态截图 wave4-preset-*。**Wave 4 十项全清**。

## P2(Wave 5)

- [x] **CONV-UX 会话重命名**(session a3b4501/web 1a6191f/gate 5c83979,契约 4f20939):PATCH /sessions/:id/title 全负向(403/404/422)+侧栏内联/头部双击改题+乐观回滚;gate 5 断言绿。
- [x] **SESSION-FLAKE 根治**(session b8b8295):根因=vitest fork 复用进程致 undici 陈旧 keep-alive socket 跨文件复用("other side closed");修=setupFile 每响应 Connection: close(非调超时);5 轮 378 全绿实证。
- [x] **M6-SNAPSHOT 后半**(契约 9f33734;session 13b6f6f/web 87f422f/gate a38ac30):裁决 B 变体——属主 snapshot 省略 messages(web 水合恒丢弃=纯浪费),/shared 公共面必携(唯一内容源),回放保持属主线程唯一真源;gate 属主无/分享必携断言绿。
- [x] **ADMIN-MANIFEST**(platform e9782be):资源/动作/列头全取 manifest labelKey(删 RESOURCE_LABELS/ACTION_LABELS 硬编码表);新 /hub 能力枢纽通用页;manifest 外专属页注释标注;实走截图 wave5-admin-manifest-*。跟进:共享网关实例刷新(含 DELETE schema 构建)后补 user/hub 在线截图(源码已对,实例滞后)。
- [x] **I18N-REVIVE**(platform 69bb2e8):kokoro-i18n 复活为零依赖窄包(12 tests/100% cov);admin-web zh/en 全键+切换器;主 web 是否切共享包留 Wave6 评估。
- [x] **web 四重奏**(web 2eb57c5/fabb316/0f04c8f/fd86a2a,spec df819ed):ERROR-UX 7 码逐码文案+恢复引导+原文折叠;WEB-THEME 暖纸暗色档(非冷灰翻转)+系统/亮/暗切换;HITL-NOTIFY 跨会话待批徽标+tab 前缀+系统通知;WEB-MOBILE ≤768px rail 抽屉+主路径单栏;web 423 绿;九张实走截图(wave5-error/theme/notify/mobile-*),暗色档主控抽验成立。
- [x] **SWARM-QUOTA**(agent 7cfa48e+67d444d/platform d417a72,spec b3dcc6a):SWARM=handbook D6 逐字落地——handoff 工具(候选>1 挂载,未知名 fail-closed)+SwarmPersonaMiddleware 按 active_agent 定点换 prompt 轨(底座/技能清单保留)+active_agent 落 checkpoint(NotRequired,旧 checkpoint 兼容);QUOTA=账户 quotaMicros 月度窗(hold 前已结算+在持聚合超限→402 credit.quota_exceeded)+admin set-quota 动作+纯扩展迁移;agent 609/credit 151+104 绿。**Wave 5 七项全清**(e2e PASS)。

## 文档欠账(2026-07-13 核验刷新;终局审计归 Wave 6)

- [x] technical/23 运营台册已在;modules/ 十册已在(含 kokoro-hub);CURRENT 已指 22;CODEBASE_MAP 已含 hub;contract README 事件数改计数派生(6295f36)。
- [x] **Wave6 全册事实审计+部署面**(c79b2fa 九册状态位刷平/存疑六项裁决入终稿;compose 11b7a7a 补 mongo+minio+hub 段;.env.example 四仓补齐 b9ca96b/46d6c36/c8c4526/94d1741;credit 册 d240c15;tmp/closure 陈旧件已清含 evidence-token)。
- [x] **WEB-ARCH 重构**(用户点名;定案 b6a7a94;web f4da915→d46c138 八支):共享查询层(useResource SWR/竞态丢弃/invalidate)+七面板迁移+shell 774→364 行(7 域 controller)+规则下沉纯模块+11 张域 INDEX+FALLBACK 收紧(失败不入缓存+KOKORO_SITE_STRICT 门);web 455 绿,行为零变化(面板重开 SWR 即显=已知优化差异)。
- [x] hub 运营字段收编 storage.yaml 单源(39b02f2);mcp_servers/skill_revisions 同已收编

**终账(2026-07-13)**:纲领 Wave 0-6 全清;终局 gate 115 断言 PASS;完整交接=docs/handoffs/2026-07-13-full-closure-handoff.md。

## Round-4/5 真实状态(纠偏)

- Round-4 四路代码已提交(2181938/5c937ef/f0f3c62)。ROUND4-EVIDENCE 进展:
  - [x] 证据①AGENT-MCP:E2E-33 铁证(yaml 死端口,真地址仅 Mongo 注册表,elicitation 全链通;d4cf07e)——顺手抓修跨语言 BSON 真雷(BsonInt,56523bf:hub-TS 写整数落 double,strict int 全拒)
  - [~] 证据②WEB-3 浏览器验收(2026-07-12 实走,截图 tmp/screenshots/web3-evidence-*):input 卡渲染✓/非法提交→**重问带真实 jsonschema 错误上卡**✓('abc' does not match pattern)/表单交互✓;**但发现新 bug MCP-REVALIDATION-HANG**:重问后合法提交,MCP 服务器已 accept 返回(服务器日志实锤 CallToolRequest+Terminating),agent run 悬不收口(疑 elicit 桥/adapter receive-loop 在多次 teardown 重放后 future 未回)——单仓测试未覆盖"两次 submit 跨 resume 重放链"。修复归 agent 仓,列 P0.5。
  - 附带发现:closure-up 缺 deliveries 存储节致 deliver 降级(已修,storage.yaml 节补上);浏览器全链 respond/approve/deliver pill 全部实走通过。
- Round-5 被额度墙击落,**五路零落地**;SESS-LIST 仅契约草稿。大 lane 派工方式按纲领 §11 废止,后续按 Wave 逐项单 spec/plan。

## WEB-FACE 用户面重设计 + 对话打通(2026-07-14,全部浏览器实证+已 push)

- [x] **对话"这轮未完成"根因修复**(web 2bdc2ea):真根因=前端 localStorage 跨用户缓存越权
  activeId→session 403 session_forbidden→hydrate fail-loud 卡死;引擎遇越权码驱逐 activeId
  回退空态(非当 404)。TDD 红→绿(engine+core 200 测试),浏览器塞越权 id→自动驱逐→发消息
  端到端跑通。投递链路(session→redis→agent)本身一直健康,此前夜间误判 worker/dispatch。
- [x] **dev 脚本增强**(主仓 4271c64):closure-up 加端到端对话探针 `chat`(签发→发消息→SSE 抓
  run.completed)、`restart`、up 自动纳管 web dev。
- [x] **线 A 用户面重设计**:A1(web ae95573)rail 用户区占位身份→真实团队名+蓝渐变首字母头像、
  "像太阳"齿轮修真、settings 几何字符 ◍◐✦◆◈→SVG、主题/语言收归 settings 单一真源(移除 rail
  裸 chips);A2(web 33e87f4)Settings 两栏 overlay 浮层(rail 齿轮触发,左 SVG 导航+右分区流,
  backdrop 模糊+入场动效,复用 settings-sections,/settings 整页深链兜底),dead CSS 清理(0b0f177)。
- 遗留(非本线):artifact-card.test pre-existing 红——AUTH-P0 工作线 impl 已改同源 cookie 但 test
  未跟上,修复在 `archive/auth-p0-tests` tag(kokoro-web),不擅自接管。

## 已收口(近期,全部全链 e2e 绿;commit 详单见交接档)

- [x] 主链块1→HITL H3 / P1-P5 闭环+E2E-40 / HUB-1/2/3 / P-A/B/C / PAY-1 / CONV-1 / M-1→M-7 / WEB-1/2 / handbook 21/22
- [x] 债务核验已修:hold 过期回收/e2b 自愈测试/confirming outbox 第一刀/internal-secret 守门/requestId 统一/契约共享包/TTL 缓存

---

## 归档:原型期台账(2026-05-23 起,docs/prototypes 静态原型线;已被 kokoro-web 真实现取代,仅存史)

<details>
<summary>Canvas 全量产物矩阵 buildout(原型期,已完结)</summary>

14 类 canvas 产物页+gallery 全部完成并 Playwright 复查;第三批工具态改造(单列生成器)完成;第四批侧边栏(应用功能 1 列+案例库)完成。待续项(案例库充实/生成接结果态/小尾巴)随原型线冻结——真实现已迁 kokoro-web(暖纸感 token/三栏 Canvas/成果卡,见 handbook 22 §4 与 WEB-1/2 commit)。
教训存档:连续 3 次布局没对齐参考站才动手(输入放右→分栏→单列),根因=没先深看参考;已记 lesson。
</details>
