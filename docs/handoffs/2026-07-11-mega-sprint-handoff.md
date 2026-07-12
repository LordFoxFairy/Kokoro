# 2026-07-11 全域冲刺交接档

状态:活文档,每轮收口更新。接手者从这里 + `docs/CURRENT.md` + `docs/task.md` 开始,不要翻旧 handoff。

## 一、已落库(全部经全链 e2e 验证,`python3 scripts/e2e-v21-gate.py` 全绿)

### 主链(此前会话+本冲刺)
- 块1-块B:namespace 持久化/契约命名/skills 工具/MCP 三恒定工具面/Skills Hub(agent 侧)/会话能力快照
- 块C/D:物化账本进 graph state;deliver 交付冻结全链(E2E-31)
- HITL H1/H2/H3:request_human 原语/submit 决策臂/MCP elicitation(E2E-32)
- P1-P5 闭环:user 签发(HS256,namespace=teamId)/web 登录闸(分支)/litellm 网关档/计费三档(hold-settle-release)/closure-up 一键起环/E2E-40(真签发+enforce 计费+ledger 落账 17 断言)
- SkillGrant.scope 关死同名遮蔽;workspace key 契约单源;M-2 依赖反转;M-6 读模型压缩(delta 只 live 不落库,回放纯完整帧,gate 断言已同步)

### platform 域
- kokoro-hub 能力中台(新模块,4251):HUB-1 管理面(启停/官方位/软删/配额)+HUB-2 上传 preview→confirm+版本历史(skill_revisions)+HUB-3 MCP 注册表(secret_ref 拒明文)+admin 网关 manifest 已接
- P-B 四洞:internal-secret 入站守门/payment 裸 fetch 归队/requestId 统一/payment 确认 outbox(confirming+sweep)
- P-A 契约共享包(手抄镜像清零,编译期漂移信号);P-C credit TTL 缓存
- credit hold 过期回收(sweep 原子条件转移);PAY-1 webhook 面(验签/重放幂等/状态机/驱动确认)
- 五 prisma 模块+admin 双件 postinstall=prisma generate(新环境不再踩过期 client)
- CONV-1:agent list_pool/resolve_cards 删除,池查询权威归 hub

### web(分支 `agent/p2-auth-wiring`,主线归外部 shell 会话,合入时机用户定)
- P2 登录闸(email 直登换签)+WEB-1 语义 token/暖纸感归队/工具 pill/计划卡+WEB-2 Canvas 第三栏+成果卡全链+M-7 lint 债清零

### 文档
- handbook technical/21(闭环)/22(能力中台+tRPC 不换定案)正式册;specs 转历史入口;8+ 份 INDEX.md 边界地图

## 一点五、Wave 0 已收口(2026-07-12,纲领=specs/2026-07-11-cross-repo-closure-and-legacy-alignment-design.md)

用户投放项目级总设计稿(待评审)后,已按其 Wave 0 完成:镜像/契约/gitlink 封存(7193bff/9a06e69/c4a0718/19b29cf)、
DOC-AUTHORITY 纠偏(06bc181:handbook 20/21/22 状态与不可执行链路、CURRENT 纲领入链、task.md 新 P0 台账)、
ROUND4-EVIDENCE①E2E-33 注册表铁证+BsonInt 跨语言修复(d4cf07e/56523bf)、证据②浏览器实录+新 bug
MCP-REVALIDATION-HANG 记档(4560b33,修复在飞 fixRevalidationHang)。**后续执行序以该纲领 Wave 1-6 为准,
大 lane workflow 派工方式废止;根契约/gitlink/task/handoff 主控串行。**

## 二、在飞(接手先收这两个 workflow)

结果文件在 `/private/tmp/claude-501/-Users-nako-WebstormProjects-github-thefoxfairy-Kokoro/4185abf7-*/tasks/` 下:
1. **round-4**(写,task woy1d0qpi):AGENT-MCP(agent 消费 mcp_servers 注册表,双源合并)/WEB-3(kind=input 动态表单卡)/HUB-4(运营位+审核三态)/AUTH-2(user magic-link 服务端)。各 lane 汇报含 verify 真实尾行与 notes 偏差。
2. **gap-audit**(读,task wffukzjv3):能力缺口矩阵/PRD 覆盖三列/文档归位/工程债台账——结果用于合成 `docs/task.md` 总台账与 round-5 排块。

**收口流程(每轮铁律)**:逐 lane `git diff` 自审+全量测试自跑(不信 lane 汇报数字)→ 全链 `python3 scripts/e2e-v21-gate.py` 必须 PASS → 按仓分主题 commit(中文 conventional,行为+验证入 body)→ 汇报。lane 越界=回滚重派。

## 三、验证口径(接手照抄)
- agent:`uv run pytest -q`(当前基线 485)/`ruff check .`/`pyright` 0
- session:`npm run typecheck`/`npx vitest run`(263)/`npx eslint .`(0 error)
- web:同上(231;`npm run lint` 管道会吞退出码,务必看 error 计数)
- platform 各模块:`pnpm test` + `DATABASE_URL_<MOD>=mysql://root:kokoro_root@127.0.0.1:3307/kokoro pnpm test:integration`(hub 用 mongo 27017+minio 9100)
- 环境:mongo 27017/redis 6379/minio 9100(kokoro/kokoro-secret)/mysql 3307(root:kokoro_root)/litellm dev 4000;一键 `python3 scripts/closure-up.py up|down|status`
- e2e gate 前先 `lsof -ti:4601,4611,4621,4631,3902,3901,3907 | xargs kill`

## 四、backlog(审计台账出来后以 docs/task.md 为准;当前已知)
- HUB-4 运营字段收编 storage.yaml 单源(lane 用旁注记模式,同 mcp-storage 收编路径)
- AGENT-MCP 落地后:e2e 扩注册表场景;stripe/alipay/wechat 真验签(注册表留位 501)
- WEB-3 的 Playwright 端到端(需 MCP elicitation 环境,组件级已覆盖);web 暗色模式(token 结构已留);web 分支合入主线(等 shell 会话)
- RS256/JWKS 轮换;Subscription 写路径;ModelLabel.defaultBinding 消费;admin-web manifest 元数据驱动页面;kokoro-i18n 复活;session relay 偶发 flake(263 并发套件时序,复跑即绿,待钉)
- M-1 后半:model 可用性收敛 platform 单源(profile.allowed 降展示过滤)

## 五、边界与坑(血泪,勿重踩)
- wire 契约=`contract/spec/*.yaml` 单源,改前先 spec 再 `python3 contract/generate.py`(17 镜像,`--check` 门禁);镜像文件任何仓禁手改
- kokoro-web 主线是外部 shell 会话的地盘,我们的一切 web 工作在 `agent/p2-auth-wiring` 分支;`.gitwarp/` 永不触碰
- platform 共库 `_prisma_migrations` 跨模块共表:`migrate dev` 会要求 reset(禁!),新迁移手写 SQL+`migrate deploy`;表名看 @@map(踩过 `payment_orders`)
- e2e gate 的 SseReader 是消费型游标:断言顺序必须匹配事件顺序
- 同子仓多路并行必须在子仓内开 git worktree(主仓 worktree 不含 gitignored 嵌套子仓);跨仓互斥写区可裸并行
- GA/agent 只消费不透明 namespace;session 禁身份前缀;secret 永不落日志/明文
