# Kokoro 任务状态（跨会话）

> 主 agent 维护；子 agent 只读。会话开始读一次。状态以**代码为准**(handbook 状态位可能滞后,以本表校正)。
> 最后更新:2026-07-13(**纲领 Wave 0-6 全清+WEB-ARCH 重构收口;终局 gate 115 断言 PASS;交接终稿=handoffs/2026-07-13-full-closure**;Wave 1-3 P0 全清;Wave 0 事实封存;纲领=specs/2026-07-11-cross-repo-closure-and-legacy-alignment-design.md,其 Wave 划分为执行序)。原型期旧台账见文末归档。

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
