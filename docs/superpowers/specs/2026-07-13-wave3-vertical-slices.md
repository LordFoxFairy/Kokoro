# Wave 3 子 spec——用户可感 P0 三竖切(SESS-LIST / WEB-BILLING / WEB-SKILLS)

状态:执行稿(上级=总设计稿 §6 Wave3/§8.2 6·7·11·12,已获批)。铁则(纲领原文):三项各自形成
后端、BFF/client、UI、真实浏览器验收的完整竖切,不接受"只交 API"或"只交 UI";P0 不放假充值按钮。
契约(已冻结 23b6f7c/c4a0718):SessionList/sessionsPath;BillingSummary/BillingLedger +
billingSummaryPath/billingLedgerPath。web 在分支 agent/p2-auth-wiring 上继续(主线合入时机用户定)。

## SESS-LIST(session 后端 + web rail)

- session:`GET /sessions`(契约 sessionListSchema)——owner 隔离(既有 auth 面同 snapshot 守门),
  updated_at desc,软删不出;复合游标 cursor=(updated_at,session_id) 稳定分页(query limit 缺省 50,
  上限 200;cursor 不合法=400)。store 补 listSessionsByOwner(Mongo 复合索引 {owner_id, updated_at
  desc, session_id};memory-store/行为矩阵镜像)。updated_at 推进点=append/ensureSession 既有语义,
  不新增写放大。
- web:rail 改服务端水合(BFF 经 session 代理取列表;localStorage 只保留 UI 偏好如折叠态,会话清单
  不再本地存);滚动到底翻页(cursor);换浏览器可见同列表(§8.2-6);跨 owner 不可枚举(负向)。

## WEB-BILLING(platform-credit 窄读 + session 代理 + web UI)

- credit(runtime-internal 面,per-caller 凭据既有):新增窄读 GET(账户余额+held 聚合、ledger 分页,
  owner=(siteId,ownerKind,ownerId) 入参同既有 hold 面)。只读不建账:无账户→零额+空流水。
- session:`GET /billing/summary`/`GET /billing/ledger`(契约形状)——账户从已验 namespace 派生
  (与 billing hold 同一派生逻辑,billing/client.ts 复用),代理 credit 窄读;billing off 档→零额空
  流水(不 503,展示层可判)。金额微单位字符串直透,不换算。
- web:余额卡+流水列表(±着色,reason 本地化文案)+402 专用说明(run 被 credit_insufficient 拒时
  指向价格/联系入口;PAY-2 前不放假充值按钮)。

## WEB-SKILLS(web ← BFF → hub self 面,hub API 已在)

- BFF:/api/hub 代理从 403 骨架接通 self 面(web-bff caller 凭据,scope 恒=密封信封 namespace)。
- UI:技能池列表(official+namespace 合并视图,required lock 不可停)、启停、上传 preview→confirm
  两段(hub 既有)、配额展示、版本/审核状态(review_status 三态)、与输入框 pinned_skills 接线
  (现有 pinned 机制,池里启用的技能可 pin)。负向:member 只读(TEAM-1 前 personal owner 全权,
  留 UI 态位不硬造成员体系)。

## 验收

- 各仓全量只增不减三绿;e2e gate 全绿+新断言:SESS-LIST 列表/分页/软删不出/跨 owner 不可枚举
  (§8.2-6);billing summary/ledger 经真 credit 返真数(E2E-40 段顺延);web 竖切=真实浏览器
  Playwright 主路径+截图(rail 水合/余额流水/技能启停上传),截图落 tmp/screenshots/。
- 纲领 §8.2-7:402 UI、技能上传/启停走真实后端,不用 mock 完成验收。
