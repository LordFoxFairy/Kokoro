# 2026-07-13 全 Wave 闭环交接终稿

状态:纲领(specs/2026-07-11-cross-repo-closure-and-legacy-alignment-design.md)Wave 0-6 全部收口。
本档=总账入口;逐项 commit 锚详单在 `docs/task.md`(总台账,状态以代码为准);本档不重复抄。
接手从这里 + `docs/CURRENT.md` + `docs/task.md` 开始;旧 handoff(2026-07-11)仅存史。

## 一、收口总览(每 Wave 一行,详单见 task.md 对应节)

| Wave | 内容 | 终态 |
|---|---|---|
| 0 | 状态封存/DOC-AUTHORITY/ROUND4 证据 | ✓(2026-07-12) |
| 1 | TRUST-ROUTES/AUTH-P0/CREDIT-CACHE/MODEL-SOURCE/HUB-AUTHZ/MCP-SECRET/MCP-REVISION/HUB-CONSIST | ✓ 六项+Hub 四级链全绿,MCP mutation 门=env |
| 2 | R0-R7 持久意图全链(dispatch CAS/control outbox-inbox/tool journal/terminal outbox/双水位 quarantine/billing saga) | ✓ R0 五钉清零 |
| 3 | SESS-LIST/WEB-BILLING/WEB-SKILLS 三竖切 | ✓ 全部浏览器实走 |
| 4 | TEAM-1/OBS-1/MCP-UX/MODEL-UX/AGENT-PRESET/ARTIFACT-LIB/SHARE-1/PAY-2/SITE-REAL/SEC-2 十项 | ✓ |
| 5 | CONV-UX/SESSION-FLAKE/M6 后半/ADMIN-MANIFEST/I18N-REVIVE/web 四重奏/SWARM-QUOTA 七项 | ✓ |
| 6 | handbook 全册事实审计/部署面补齐(compose hub+mongo+minio、agent·hub·session·web .env.example)/tmp 清理/存疑裁决 | ✓(c79b2fa/11b7a7a/c8c4526/94d1741/d240c15) |
| 加 | **WEB-ARCH 重构**(用户点名对照参考;定案 spec b6a7a94) | ✓ 五阶段+FALLBACK 收紧+web env(8 commits,行为零变化) |

## 二、最终验证基线(2026-07-13 终跑,全部主控亲验)

- **e2e 总门禁**:`python3 scripts/e2e-v21-gate.py` → **E2E PASS,115 断言全绿**(断言面含:HITL 全链/
  E2E-27~33/E2E-40 十七项/R2 receipt applied/R5 producer_closed/R7 journal 终局/McpGrant §8.2-9·14·15/
  SESS-LIST 五断言/billing 真数/models·agents populated/rename 五断言/M6 属主无·分享必携/artifacts 三断言/
  share 五断言/RS256-JWKS 正负向/site resolve)。
- agent:pytest **609 passed,0 xfail**;ruff 净;pyright 0。
- session:vitest **378 passed**(5 轮防 flake 实证);tsc 0;eslint 0。
- web(分支 agent/p2-auth-wiring):vitest **455 passed**;tsc 0;eslint 0 error。
- platform:hub 289;user 86+78;site 61+47;credit 151+104;payment 203+70;platform-kit 109;
  platform-admin 80;admin-web 14+build;kokoro-i18n 12(100% cov)。
- 证据截图索引:`tmp/screenshots/`(wave3-*/wave4-*/wave5-*/webarch 在 kokoro-web/tmp/screenshots)。

## 三、关键设计裁决记录(按时序;详细语义见对应 spec)

1. HUB-CONSIST:agent 直读同库快照行=「经 hub 拥有的数据」(同库部署强制下成立;HTTP 快照端点已备作拆库切轨)。
2. R4 head-of-line 折衷:live 即发+durable 并行确认(agent 单侧 e2e 不死锁);published 无回执超
   KOKORO_OUTBOX_REPUBLISH_MS 重发堵流修剪死锁。
3. R3 守门区分 interrupt 与崩溃(GraphInterrupt 撤销 started 行放行 HITL 重入)。
4. MODEL-UX/AGENT-PRESET 配置面事实:动态 teamId 无法静态预声明→真 auth 栈恒单候选;per-team 策略归未来运营配置源(非欠账)。
5. M6 后半=B 变体:属主 snapshot 省略 messages(web 恒丢弃),/shared 公共面必携(唯一内容源);回放=属主线程唯一真源不动摇。
6. WEB-ARCH:自建窄查询层不引 react-query;BFF+Zod 优于 tRPC 思路(跨语言后端)——参考只吸收抽象思想。
7. SWARM=handbook D6 逐字:handoff 模型驱动、active_agent 落 checkpoint(NotRequired,旧 checkpoint 兼容)、换人格不换授权。
8. 支付/站点诚实态:未配置 provider 恒 501、价格页"未开通"真状态;SITE_STRICT 门缺省关(开启=解析失败 fail-closed 中性页)。

## 四、验证口径(接手照抄)

- 环境一键:`python3 scripts/closure-up.py up|down|status`(mongo 27017/redis 6379/mysql 3307
  root:kokoro_root/minio 9100 kokoro/kokoro-secret/litellm 4000);gate 前
  `lsof -ti:4601,4611,4621,4631,3902,3901,3907 | xargs kill`。
- 各仓命令与基线见上节;platform 模块 `pnpm test` + `DATABASE_URL_<MOD>=mysql://root:kokoro_root@127.0.0.1:3307/kokoro pnpm test:integration`。
- 契约纪律:`contract/spec/*.yaml` 单源→`python3 contract/generate.py`(17 镜像+`--check` 门禁);镜像禁手改;根契约主控串行。

## 五、已知余量(全部非阻塞,如实列)

- gate kill/chaos 进程级脚手架未做(单元级故障注入两仓全覆盖);receipt manifest 自动 GC 只留门。
- PAY-2 provider 沙箱真跑通、SMTP 真发信(magic-link 现 dev response 档)、HUB-4 灰度=运营配置动作,非代码欠账。
- admin 共享网关实例刷新(含 DELETE schema 构建)后补 user/hub manifest 在线截图(源码已对,payment 面已实走等价证据)。
- ~~web 主线合入~~:已合入(2026-07-13 用户指令,fast-forward fc2cc85→d46c138 零冲突,42 支;分支保留存档)。
- 主 web 是否切共享 kokoro-i18n:评估结论=不急切(主 web 键体系自洽;等下次大 web 文案波再并轨)。
- webarch 已知行为差:面板重开由 loading-flash 变 SWR 缓存即显(更优;要复刻旧感受在 open 处 invalidate)。
- 存疑存档:Daytona 远程沙箱落地态未查证(handbook 20 §5 块6 原文保留);product/00-08 册未逐字深审(抽查无漂移)。

## 六、边界与坑(血泪浓缩,接手勿重踩)

- 镜像任何仓禁手改;BsonInt 只在存储镜像容忍 double,wire 面纯 strict。
- platform 共库 `_prisma_migrations`:新迁移手写 SQL+`migrate deploy`,禁 `migrate dev/reset`;表名看 @@map。
- gate SseReader 是消费型游标,断言序=事件序;守卫式断言先验依赖真的在跑(容器名假空转教训)。
- 同子仓多路并行必须子仓内 worktree;根契约/gitlink/task/handoff 主控串行。
- GA/agent 只见不透明 namespace;user principal 只在 user↔web BFF;secret/私钥永不入日志仓库,示例全假值。
- dev 闭环重启某服务=精确复刻原 env;closure-up 有 worker 独占守卫,勿另起第二 worker。
