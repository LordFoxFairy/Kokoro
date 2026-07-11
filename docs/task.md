# Kokoro 任务状态（跨会话）

> 主 agent 维护；子 agent 只读。会话开始读一次。状态以**代码为准**(handbook 状态位可能滞后,以本表校正)。
> 最后更新:2026-07-11(全域冲刺,gap-audit 四路审计合成)。原型期(2026-05)旧台账见文末归档。

## P0(用户可感的硬缺口)

- [ ] **AUTH-P0 登录冒充洞**:web dev-login 输任意邮箱即得该身份 token。magic-link 服务端半场 round-4 在飞(AUTH-2);缺 web 接线(发链→点链/输码→consume 换 token)+SMTP 投递留位。上线前必堵。
- [ ] **SESS-LIST 会话列表服务端化**:session 无 GET /sessions 列表 API,web rail 只存 localStorage,换设备即丢。需:契约端点(owner 会话分页列表)+web rail 服务端水合。
- [ ] **WEB-BILLING 余额/402/账单**:web 对 402 credit_insufficient 零处理;无余额显示、无用量账单页。前置:credit 缺终端用户余额/流水查询 API(现只有 admin 面)→ CRED-BAL 端点 + web 页。
- [ ] **WEB-SKILLS 能力池管理面**(块7):hub 全量 API(池/启停/上传/版本/配额/审核)零 UI。技能列表/启停/上传向导 + pinned_skills 输入框接线(契约字段已在,web 不发)。

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
- [ ] hub 运营字段(display_weight/pinned/category/review_status)收编 storage.yaml 单源

## 在飞(round-4;收口流程与验证口径见 handoffs/2026-07-11-mega-sprint-handoff.md)

- [ ] AGENT-MCP 注册表消费 / WEB-3 kind=input 动态表单 / HUB-4 运营位+审核 / AUTH-2 magic-link 服务端

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
