# Kokoro 任务状态（跨会话）

> 主 agent 维护；子 agent 只读。会话开始读一次。状态以**代码为准**(handbook 状态位可能滞后,以本表校正)。
> 最后更新:2026-07-12(Wave 0 事实封存;纲领=specs/2026-07-11-cross-repo-closure-and-legacy-alignment-design.md,其 Wave 划分为执行序)。原型期旧台账见文末归档。

## P0(总设计稿 Wave 1-3;信任与一致性新 P0 来自代码审计,先于产品 P0)

**Wave 1 安全与能力基础**(顺序:TRUST-ROUTES 先冻结内部调用契约):
- [x] **TRUST-ROUTES**(150aa25/f9802f1/c4b89a1,e2e 凭据强制档绿):platform default-internal 全路由策略+per-caller 分级凭据(public/runtime-internal/web-bff/admin)+生产 fail-closed。现状纠偏:守门件只护 /admin 前缀且共享单 secret 空值直通——hub 路由完全无鉴权、namespace/scope 来自请求、credit 启 secret 后 session billing client 不带密钥。
- [x] **AUTH-P0**(e4068d6/6260da5/8c26740,浏览器六步实走+截图;SMTP 仍留位=SEC-2):web BFF 密封 cookie(浏览器不持 bearer)+magic-link web 流+nonce 防 CSRF+SMTP+日志脱敏(现 magic-link log 档把原文 token 写日志!)+/auth/sessions 收编为内部口。现状:任意邮箱直登+token 在 localStorage。
- [~] **HUB 链**:HUB-AUTHZ✓(0bccba3 三权限面+mutation 503 门)→MCP-SECRET hub 半场在飞→MCP-REVISION 契约已 spec 待切→HUB-CONSIST 待;原缺陷句留档:Hub 三权限面;McpGrant {scope,name,revision,config_hash} 版本锁+实时撤销;secret handle broker+SSRF/egress;**split-brain 修复**(hub/session/agent 默认 Mongo DB 不同!session 池解析忽略审核/运营排序——session 改调 Hub 单解析器,MCP mutation 在跨仓门通过前 503)。
- [x] **CREDIT-CACHE**(c5a8ac3):owner 正缓存键补 siteId(现跨站复用 owner active 结果)。
- [x] **MODEL-SOURCE**(3b4c743):profile.allowed 降展示过滤,platform resolve 为可用性权威(M-1 后半)。

**P0.5 结案(2026-07-12 调查完毕)**:
- [x] **MCP-REVALIDATION-HANG 调查**:单 worker 下五类忠实建模(真 FastMCP+supervisor+control,双重问四连接链)全部到终态,桥配对 trace 无误——agent 桥/连接生命周期无罪(绿钉 ed5fc62 留作护栏)。**主嫌=双 worker control 竞争**(实录第 4 条多余 MCP 连接;closure-up 曾无条件 spawn worker,残留同组消费者拿走 resume 重放)——已加独占守卫缓解;**根治归 Wave 2 R2**(control durable inbox/receipt/lease fencing,正合纲领故障矩阵"agent inbox 后 apply 前"场景)。

**Wave 2 可靠性(D5 持久意图模型,R0-R7 顺序)**:
- [x] R0 故障护栏五钉(8ca5fc6/4c154dc)+R1 契约冻结(e471822);R1 实现在飞
- [ ] request/control 在 durable claim/inbox 前 ACK、agent 终态在发布前消耗终态权、settle/release 失败无持久重试——run_dispatches CAS/durable_seq/receipt manifest/quarantine 全套(纲领 §5/§8.3 故障矩阵)。

**Wave 3 用户可感 P0(必须后端+BFF+UI 竖切)**:
- [ ] **SESS-LIST**:契约草稿已封存(c4a0718),store/route/rail 水合全未实现。
- [ ] **WEB-BILLING**(前置 CRED-BAL 窄读 API)/- [ ] **WEB-SKILLS**(认证 BFF 后)。

## P1

- [ ] TEAM-1 邀请/成员管理(user:invite 表有路由零;Team/Membership/Role 逻辑空;admin manifest 动作无后端路由——点了即败)+ web 团队切换 UX
- [ ] MCP-UX web 连接向导(hub 注册表 API 已有;agent 消费 round-4 在飞)
- [ ] MODEL-UX web 模型选择(wire model 字段已通,web 只发 thinking 布尔)+ M-1 后半(model 可用性收敛 platform 单源,profile.allowed 降展示过滤)
- [ ] AGENT-PRESET 块4(preset"加目录零代码"agent 侧未落;session 首条锁已落)+ agent 选择 UX
- [ ] ARTIFACT-LIB 跨会话作品库(读模型 (namespace,content_hash) 已预留,无页面)
- [ ] PAY-2 支付外环:stripe/alipay/wechat 真验签(注册表 501 留位)/Subscription 写路径/refund 回链/价格页购买流
- [ ] SITE-REAL 多站点真解析(host→site/域名验证流转/品牌注入;现单站点 env 常量)
- [ ] OBS-1 可观测:session/agent 零 metrics/tracing(仅 console);run 卡死/计费失败无告警
- [ ] SEC-2 签发链硬化:RS256/JWKS(现 HS256 双持共享 secret)/magic-link 限频内存→redis/MCP secret:path 档
- [ ] SHARE-1 会话只读分享(snapshot 已不暴露 namespace,有地基)

## P2

- [ ] 会话重命名/HITL 待批通知/run.failed 按码文案/错误恢复引导
- [ ] web 暗色模式(.dark 槽位已留)/移动端主路径打磨
- [ ] admin-web manifest 元数据驱动页面(现硬编码)/admin-web i18n/kokoro-i18n 复活
- [ ] session 测试 flake 治理(并发时序,单跑绿)/M-6 后续(snapshot.messages 双份另一半)
- [ ] swarm/组织级配额(handbook 定 P2)

## 文档欠账(DOC-2 在办)

- [ ] technical/23 platform 运营台册(RBAC/审批流/审计/webhook/hold 回收/多租户——已落地无主仓册)
- [ ] web 工作台形态入正式册(Canvas/三栏/四卡现只在历史入口 spec)
- [ ] 状态位刷新:20 §1§5 / 21 §2§6 / 22 §2§4 / 15+09 状态头(代码已超前文档)
- [ ] 归位七项:CURRENT.md 指 22/docs README 主线节/00 指针/CODEBASE_MAP 补 hub/modules 补 hub/platform README 补 hub(子仓)/tmp/closure 清理
- [x] hub 运营字段收编 storage.yaml 单源(39b02f2);mcp_servers/skill_revisions 同已收编

## Round-4/5 真实状态(纠偏)

- Round-4 四路代码已提交(2181938/5c937ef/f0f3c62)。ROUND4-EVIDENCE 进展:
  - [x] 证据①AGENT-MCP:E2E-33 铁证(yaml 死端口,真地址仅 Mongo 注册表,elicitation 全链通;d4cf07e)——顺手抓修跨语言 BSON 真雷(BsonInt,56523bf:hub-TS 写整数落 double,strict int 全拒)
  - [~] 证据②WEB-3 浏览器验收(2026-07-12 实走,截图 tmp/screenshots/web3-evidence-*):input 卡渲染✓/非法提交→**重问带真实 jsonschema 错误上卡**✓('abc' does not match pattern)/表单交互✓;**但发现新 bug MCP-REVALIDATION-HANG**:重问后合法提交,MCP 服务器已 accept 返回(服务器日志实锤 CallToolRequest+Terminating),agent run 悬不收口(疑 elicit 桥/adapter receive-loop 在多次 teardown 重放后 future 未回)——单仓测试未覆盖"两次 submit 跨 resume 重放链"。修复归 agent 仓,列 P0.5。
  - 附带发现:closure-up 缺 deliveries 存储节致 deliver 降级(已修,storage.yaml 节补上);浏览器全链 respond/approve/deliver pill 全部实走通过。
- Round-5 被额度墙击落,**五路零落地**;SESS-LIST 仅契约草稿。大 lane 派工方式按纲领 §11 废止,后续按 Wave 逐项单 spec/plan。

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
