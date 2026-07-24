# 交接单:credit 三桶(L3.1)——域 + 阶段1/2/3 全部完成

日期:2026-07-24 · 状态:**L3.1(三桶信用域)已完成并全真栈验证;下一步 L3.2(Plan+权益)未开工**

## 背景与目标

用户判「整体商业设计很烂」,驱动了一轮货币化/能力架构重设计(specs/2026-07-24-*、
plans/2026-07-24-*)。共同本质:**一台通用引擎**(意图→GA→kokoro-model→artifact→credit→namespace)。
本次任务是这套重设计里 **L3.1:credit 三桶抽象**(daily/period/permanent,过期先扣,懒 materialize)。

用户原话给的两条硬约束:
- 「好好思考...心黑但合理」→ 逼出货币化 spec §3.9 十四条 house-favor 决策矩阵。
- 「卡密换积分和支付买积分是同一个吧,你应该做好抽象整体架构设计」→ 已定案(见下),**未实现**(属 L3.3,本次未动)。
- 「你按照标准实现吧...我的技术意见不重要...不然后续太难维护了」→ 后续实现细节(heldMicros 存废、
  时区方案)按行业标准直接拍板,不再逐条请示。

## 架构定案(读代码前必看)

**B1(三桶统一,非"C 胶合"方案)**:hold 时按序(daily→period→permanent,过期先扣)从三桶**直接扣走**
(decrement-at-hold),扣减明细快照进 `CreditHold`;capture 按实额分摊、release/expire 全额、
**统一走 `creditBack()` 夹紧归还到当期额度**(不复活已过期赠额,堵日界翻页竞态)。
`heldMicros` 保留,但语义从"预留判定依据"降级为"预留总额缓存"(报表 denorm,非双机制)。

**时区**:懒刷新自然日/周期边界统一按 **UTC** 计算(行业标准——存储/边界算 UTC,展示层才转本地;
与既有 `quotaPeriod="monthly"` 同口径)。换算点收在 `refreshRow()` 一处,以后接 site/用户时区只改这里。

**卡密=支付(已定案未实现)**:两者本质是同一个 **Grant** 操作(“获得一个积分包→永久桶 += 包积分”),
渠道(payment/卡密/admin/welcome/refund)只是 ledger 归因元数据,不建三套扣账实现。L3.3 落地时直接复用。

## 已完成并验证(证据)

真 DB 隔离库 `kokoro_credit_test`(127.0.0.1:3307,dev mysql 容器 `kokoro-infra-mysql-1`),
经**正式 `prisma migrate deploy`** 重建过(非 db push 临时同步)。取 DB URL:
`source scratchpad/credit-it-env.sh`(session 内脚本,读 `deploy/.env.dev` 的 root 密码构造
`DATABASE_URL_CREDIT`,不落盘密码)。

| 提交(kokoro-platform 子仓) | 内容 |
|---|---|
| `06989fc` | 域 `buckets.ts`:available/debit(过期先扣+shortfall)/refresh(reset 非累加)/creditBack。18 单测。 |
| `5c25eb6` | `creditBack` 加时间桶**夹紧到当期额度**(堵日界翻页复活过期赠额)。 |
| `75b6780` | **阶段1**:CreditAccount 加 daily/period 桶列+水位(迁移 `20260724120000`,加法迁移)。 |
| `070dce9` | **阶段2(脊柱手术)**:hold/capture/release/expire/spend 全切 B1;迁移 `20260724130000`(hold 预留明细+账户 allowance 列);顺带修真 bug(spend 漏切 B1);删死代码 `assertCreditSpendAllowed`。 |
| `d30a16a` | **阶段3**:懒刷新 `ensureAllowancesFresh` 接线,域 `reset-boundary.ts`,新 `refreshAllowances()` 只读路径 API。 |

根仓文档提交:`4b01721`(货币化 spec)→`d5f02a8`(决策矩阵)→`275860f`/`cfff6bd`(task.md 进度)。

**最终验证**(d30a16a 当次跑出):**182 单测 + 116 集成 + typecheck 净**,含全部并发 chaos
(hold 精确不超额、行锁串行化、spend 不得动用冻结资金)+ 新增证明性测试(B1 多桶按序扣/分摊守恒/
release 复原/日界夹紧/懒刷新触发-持久化-惰性不重复)。均为真跑输出,非估计。

## 改动文件(累计,已提交)

```
kokoro-credit/src/domain/buckets.ts               (新)
kokoro-credit/src/domain/reset-boundary.ts         (新)
kokoro-credit/src/domain/credit.ts                 三桶+预留明细+allowance 字段
kokoro-credit/src/domain/repository.ts             接口加 refreshAllowances,holdCredits/spendCredits 加 now 参
kokoro-credit/src/domain/credit-policy.ts          (删,死代码)
kokoro-credit/src/application/credit-service.ts    readUsageSummary 读前刷新
kokoro-credit/src/infrastructure/prisma/prisma-credit-repository.ts   核心改动(hold/capture/release/expire/spend/refreshAllowances)
kokoro-credit/prisma/schema.prisma + migrations/20260724120000_*, 20260724130000_*
kokoro-credit/test/unit/{buckets,reset-boundary,credit-policy(删),...}.test.ts
kokoro-credit/test/integration/{credit-buckets,credit-hold-cycle,credit-repository,credit-usage-billing}.test.ts
```

## 已知限制 / 待办

1. **根仓 gitlink 指针未同步**:`kokoro-platform` 已推进到 `d30a16a`,根仓 `git status` 显示
   `M kokoro-platform`(子模块指针滞后)。**尚未提交**——按仓库惯例应有一次 `chore: sync gitlink`
   收尾提交,本次未做(交接单任务范围内不擅自扩大动作)。
2. **HTTP 契约未暴露三桶细节**:`readUsageSummary`/`/credit/usage/summary` 仍只吐 4 字段
   (balanceMicros 已改为三桶之和,但 daily/period 拆分未进 API/OpenAPI contract)。故意 YAGNI——
   目前无消费方(无 Plan、无 Studio UI)需要,等 L3.2/L4 有真实消费者再扩契约,避免无谓 contract churn。
3. **allowance 恒 0**:daily/period 桶的额度来源(`dailyAllowanceMicros`/`periodAllowanceMicros`)
   目前只能手工写库验证机制;要在真实业务里生效,必须 L3.2(Plan 目录)写入非 0 值。
4. **卡密/支付 Grant 统一抽象**:已定案(见上),未写代码,属 L3.3/L3.5。

## 下一步(未开工,按 master-plan 顺序)

`plans/2026-07-24-phaseA-L3-detailed-plan.md` §L3.2 起:
1. **L3.2 Plan 目录 + 权益层**:`Plan{id,type:free|credit_pack|subscription,grant{...},entitlements{...}}`,
   `resolveEntitlements(account)` 横切引擎准入(model tier gating)与计价(multiplier)。
2. **L3.3 卡密 + L3.5 供给三渠道**:落地"卡密=支付=同一 Grant"抽象,渠道薄适配器 + ledger 归因。
3. **L3.4 订阅生命周期**:与支付分层,mock 支付下可独立跑。
4. **阶段 A-媒体**(可并行):kokoro-model 媒体 transport + GA `invoke_model` 通用签名 + artifact 产出。

## 复核命令(供下一次会话/审阅者复现)

```bash
cd kokoro-platform/kokoro-credit
source ../../scratchpad/credit-it-env.sh 2>/dev/null || {
  # 若脚本已随会话清理,手动构造(密码取自 deploy/.env.dev,不要打印/提交):
  ROOTPW=$(grep -E '^MYSQL_ROOT_PASSWORD=' ../../deploy/.env.dev | head -1 | cut -d= -f2-)
  export DATABASE_URL_CREDIT="mysql://root:${ROOTPW}@127.0.0.1:3307/kokoro_credit_test"
}
npx tsc --noEmit                                  # 应净
npm test                                          # 单测,应 182 绿
npx vitest run test/integration --no-file-parallelism   # 集成(真 DB),应 116 绿
```

若隔离库不存在:`docker exec kokoro-infra-mysql-1 mysql -uroot -p<root密码> -e "CREATE DATABASE kokoro_credit_test CHARACTER SET utf8mb4;"`
再 `npx prisma migrate deploy`。
