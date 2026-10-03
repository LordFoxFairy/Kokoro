# ADR-033：逐实际调用用量与 Billing 单一定价 owner

- 状态：跨仓 owner、目标路径与失败/取消收费资格已接受；契约与实现尚未完成。
- 日期：2026-10-02。
- 执行入口：Root 唯一 `docs/task.md` 中 R80-W03/W05/W06；不新增计划中心。

## 背景与当前事实

用户要求正规积分流程，按模型成本乘可配置倍率计价，当前要求倍率为 `7/5`。这表示成本加价40%，不是净利润率。

本裁决基于发布基线：System `6ca96180749d4842c2ee0628328f372d114e320f`、Agent
`444684d32473c96ddbb70247081b1d1cdb8558f1`、Billing `3e27eac22a782b3c9437c0ea47922b73a3db91ad`。
当下源码尚未达到目标：System resolve 有模型/provider/revision/digest，但不是实际 gateway 落点凭据；
Agent 用量主要为 Run/lease generation 的输入输出汇总，未形成逐实际 call/attempt 严格证据链；
Billing B8-R3/SQL admission 仍采用 Feature 固定按次价及 `quantity=1`，现 settlement 可接收 caller `actualMicros`。
这三者不能冒充实际模型成本计价或正式端到端收费。

## 决策

| 事实 | 唯一 owner | 禁止承担的职责 |
| --- | --- | --- |
| 技术模型目录、供应商、模型映射、路由 revision/digest | System / Model Catalog | 不新增成本表、价格接口或任意 key/value 配置中心 |
| 真实调用/attempt、执行 fence、实际 provider/model、分类用量与完整性证据 | Agent / execution | 不定用户价格，不写余额，不用计划路由猜实际供应商 |
| 不可变采购费率 revision、零售倍率 revision、币种/Credit换算与舍入规则、报价和结算 | Billing / Metering | 不自造执行证据，不相信caller自报最终金额，不读Agent/System数据库 |
| 余额、预占、扣减、释放、退款及唯一流水 | Billing / Credit | Payment/Agent/BFF/Web不得直接写账本 |
| 用户交互、请求编排与已发布账务结果展示 | BFF / Web | 前端不得自行维护另一套倍率、计价或补造扣费结果 |

本决定替代 Billing B8-R3“固定 Feature 按次价”为未来唯一模型收费路径的目标；不同时保留固定价和成本价两套默认实现。
旧实现当前仍在源码，切换由 Billing 原 owner 完整承接有效授权、幂等、并发、事务、恢复后删除；没有旧数据迁移或兼容要求。
本裁决不改变业务事实的已有 owner，不引入新定价服务，不要求 System 授予 Billing 新的成本读取服务身份。
ADR-003 的 Credit 唯一余额权威与 Payment/Credit 分离继续有效；其中泛指的 pricing 目标按本裁决具体归 Metering。

## 契约与状态约束

1. Agent 发布严格、版本化的实际调用证据；Billing 发布严格的 admission/settlement contract。Root 不另建可编辑 wire。
   用量必须绑定受信 Run/主体/付款授权引用、call/attempt identity、lease/fence、技术路由引用及实际供应商/模型。
   精确字段和类型由对应 owner 三面与机器契约决定；泛型 dimensions/receipt 不代替用量证据。
2. Provider 执行前必须具备有效预占；报价冻结允许的采购费率集合、倍率、换算和舍入版本及受信付款身份。
   新模型、fallback、重试和动态子代理若超出已授权费率或预算，先扩额/重新授权，不事后任意套现价。
3. 供应商计划选择与真实执行落点明确分开。若 gateway 无法给出可核验的实际落点，须限定且验证固定供应商绑定；
   未确认绑定不能按推测费率结算。请求、响应或 provider 计费凭据须脱敏，禁止记录凭据、密码或敏感正文。
4. Usage profile 明确计费桶、单位和包含/互斥规则。缺少用量为 unknown，不是零；已核验零与非零分别建模。
   同一真实 attempt 重投不重复收费，不同实际尝试分别归因。不能把 journal 和 Run 汇总重复计费。
5. Billing 基于冻结费率和严格用量重新计算金额；使用整数/有理数精算。`1 Credit=10^6 micros`仅是积分单位，
   不决定现金兑换率。倍率为正的版本化有理数；每桶/每call/整次结算的舍入点必须由 Billing D0 明确。
6. Unknown outcome 持久记录并可恢复；取消/超时不自动证明供应商零成本，也不无条件释放可能已执行的金额。
   用量证据、账务幂等结果与预占终态在 Billing 自有事务边界保证一致，不跨 owner SQL/事务。
7. “冻结费率乘用量得到的成本”与供应商最终账单是不同事实；最终 invoice 在独立 reconciliation 中核对。
   Provider 成本与向用户收费的资格也必须分开，系统失败不被自动解释成用户必付或必免。

## 尚未决的业务参数

2026-10-03用户明确批准：失败/取消/部分输出仅结算已核实的实际消耗，释放其余可确认未使用的预占；未发生调用不扣积分，用量未知先待核实。该规则适用于已核实非零attempt，不以响应是否成功或正文是否展示免除已产生用量；unknown不能视为零或一律释放，已有第6条恢复约束保持。相同attempt晚到/重复证据与取消结算竞态幂等，冻结价格/倍率/换算版本保持。此为业务资格裁决，不是正式账务链已验收。
采购费率依据、现金兑换/汇率、税费和舍入的具体配置须显式记录，不能填造数值。
这些配置未决项不阻止 owner/strict evidence/费率计算与失败恢复基础设计；不得填造采购费率或现金兑换参数，正式非零账务链仍待真实验收。
超预算默认不继续未授权调用；若用户随后要求负余额或授信，须另行明确业务授权，不默默透支。

## 选项比较

- **采用：Billing Metering统一采购与零售价格。** 同一报价与结算边界冻结费率，减少跨服务快照、授权和可用性依赖。
- **淘汰：System采购费率、Billing零售倍率。** 无当前独立成本事实/团队依据，需新增成本API/身份/发布链，延长关键路径。
- **淘汰：第三定价服务或前端计算。** 前者增加新owner/进程，后者把受信财务事实交浏览器并形成重复规则。

## 实施与验收

1. 原 Agent/Billing/System owner同步现技术/API/数据文档；严格usage与admission机器契约由owner先行发布，消费者固定版本/digest。
   不把文档通过当源码/SQL/HTTP或金融结果通过；实际源码前需核三面一致。
2. 原 Billing owner逐业务切片完成费率快照、预占、用量结算、unknown恢复及唯一main/source-dist切换；保留完整24operation目标。
   Payment渠道最后，不用伪造赠送、免费或补造钱包绕过正式账务。
3. 必须覆盖错误费率/用量/供应商绑定拒绝、预占拒绝时provider零调用、历史快照、重试/fallback、重复证据、并发扣款、事务回滚、
   unknown重启恢复、释放/结算竞态及取消/失败收费的批准策略。真实PG/Redis/owner组合与浏览器路径单独验，不用替身冒充。
4. 最终用户路径：正规IAM登录→正式授权赠送/余额→预占→真实模型→strict usage→结算或批准的释放→可追溯流水→刷新一致。
   至少一次真实非零供应商成本路径才证明非零费用链；本地Ollama或纯算法测试不替代。

本ADR仅记录跨仓决策，未修改SQL、wire或业务代码，未宣称模型聊天、账务或完整Wave0–7已闭环。
