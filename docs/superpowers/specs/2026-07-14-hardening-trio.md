# HARDEN 子 spec——余量硬化三件(gate chaos / manifest GC / admin 网关刷新补证)

状态:执行稿(交接终稿"已知余量"清单收尾;三件独立 commit 独立验收)。

## 1. gate 进程级 chaos 脚手架(主仓 scripts/e2e-v21-gate.py)

- 新增独立 chaos 段,**env 门控 E2E_CHAOS=1 才跑**(缺省关,标准 gate 节奏与稳定性零影响);
  段内自起独立 scratch(复用既有 spawn 设施),两个场景:
  a. **kill agent 于 publish 后回执前**:起 run(local_fake)→等 run.started 回执落库→SIGKILL
     agent worker→重启→断言 run 收敛到终态且事件不重不漏(durable_seq 去重铁证);
  b. **kill session 于 settle 前**:enforce 计费 run→终态帧已发、settle 前 SIGKILL session→
     重启→断言 billing journal 收敛 settled 且 ledger 恰一笔(R6/R7 补偿铁证)。
- kill 点用确定性钩子(env 注入延迟/暂停点优先;确实做不到再用轮询窗口,禁 sleep 碰运气);
  两场景各自独立 mongo db/redis db,不污染标准段。
- 验收:E2E_CHAOS=1 连跑 3 轮全绿;缺省档 gate 行为与耗时不变。

## 2. receipt manifest 自动 GC(kokoro-session)

- finalization 已置 producer_closed(门已留):新增 GC 扫描(挂既有 reconciler 节奏)——
  producer_closed 且 updated_at 超 KOKORO_MANIFEST_GC_TTL_MS(缺省 7 天)→删该 run 的
  run_event_receipts 行+manifest 行(先行后单,幂等);未 closed 永不删(close 前 404=
  receipt_state_lost 语义不破)。
- 验收:GC 单测(closed 过期删/未过期留/未 closed 永不删);全量只增不减三绿。

## 3. admin 网关刷新 + user/hub manifest 在线补证(运维动作+截图)

- 重启 closure 的 platform-admin 网关到当前构建(精确复刻 env;含 DELETE schema);
  admin-web 实走 user 团队面与 hub 审核面(manifest 通用渲染),截图
  tmp/screenshots/wave5-admin-{user,hub}-online.png,闭合 ADMIN-MANIFEST 跟进项。

## 总验收

主仓 gate 缺省档全绿+chaos 档 3 轮绿;session 三绿;截图两张;各自 commit。
