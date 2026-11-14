# 两笔历史 financial unknown：只读对账与处置方案

日期：2026-11-14。范围仅原登记的两条 Agent financial recovery 候选；本轮调查完成，恢复残留尚未处置，不称资金结清或产品修复。

## 1. 结论

**两笔均停在预算授权结果未知，模型未派发；当前未查得对应预占或扣款。** 它们不是“供应商 overload 导致的两笔已冻结款”。历史文字把恢复候选、另一 Run 的 overload、旧资金冻结混在一起，应纠正。

| 本轮对象 | 原始准备时间（UTC） | 当前 Agent 原事实 | 对应 Billing 原事实 |
| --- | --- | --- | --- |
| U-01：attempt `6b56cb40…c1e2` | 2026-11-12 10:11:52.842 | Run terminal；not_dispatched / requested_unknown；dispatch_started_at、admission_ref均空；sealed revision1、ACK空 | admission、原授权receipt/key binding、原attempt hold均0行 |
| U-02：attempt `a16926cd…e608` | 2026-11-12 10:15:46.513 | 同上 | 同上 |

两份 evidence 均通过当前 owner 的严格 `parse_evidence` 校验，包括规范摘要；其 usage=unresolved、totals/classification=unknown，不能改写为供应商上报的known_zero。Billing按原tenant、attempt/run/request identity及正式hold key精确读取；没有本轮对象的usage/settlement或可据以退款的扣款记录。BFF两条原提交事实存在。

这是独立 owner 的只读快照，不是跨服务原子事务，更不代表未来迟到授权永久不可能提交。原SQL/派发状态及收据未改。

## 2. 原因与证据边界

### 已确认的机制原因

1. Agent未取得确定授权，保存 `requested_unknown`；未进入唯一派发，最终封存 `not_dispatched`，而不是“已调用但供应商usage丢失”。见[执行授权→唯一dispatch](../../apps/kokoro-agent/src/kokoro_agent/model/execution.py)。
2. [financial reconciler](../../apps/kokoro-agent/src/kokoro_agent/model/financial_reconciliation.py)第75–87行：admission为空时只recover原命令；未找到原ACK就直接返回，不创建reserve，也不写最终ACK。注释明确：一次查询miss不能证明在途reserve已经取消。
3. [pending选择](../../apps/kokoro-agent/src/kokoro_agent/infrastructure/postgres_model_financial_repository.py)第291–305行继续包含 sealed、requested_unknown、ACK为空的attempt。因此即便Run终态且当前Billing无原命令，仍会保留恢复候选；单纯重启、再查404不会闭环。
4. 当前没有将“终态未派发＋原预算未创建”审计关闭的现成入口；不能伪造结算ACK、清旧evidence或直接SQL改状态来消除候选。

### 尚未查明的物理故障细因

原 `diagnostic-worker.log` 精确命中两attempt，仅保存 `connection_error → runtime_error` 的安全类别，没有足以确定DNS/TLS/loop状态或具体失败HTTP环节的原异常细节。该SDK外层日志不等于物理模型已发送；派发事实以严格持久证据为准。

另一个 `checkpoint-error-classification.json` 中的overload绑定不同Run，不能套用。当前模型正常或新QA成功也不能证明旧请求的结果。本轮不重新调用模型制造“复现”，不推测缺失原因。

## 3. 最小处置方案（未执行）

- **现在**：将这两笔标为“只读核对完成；当前无对应资金效果；恢复候选待审计关闭”。无现存扣款可据以退款，不赠送补偿、不释放无对应关系的旧hold；保留原证据。
- **后续若要清除恢复残留**：先由Billing在原request/key的同一幂等与锁边界中，形成可审计的“原预算未创建且禁止迟到admit”终局结论；单纯SELECT无行不足以替代此事实。优先核现有永久command receipt可否承接，不预设新表、新服务或通用对账框架。
- Agent只关联上述owner结论和原attempt/evidence digest，做获批的独立终态恢复关闭；原unknown和not_dispatched bytes保持，不补usage0、不伪造settlement或重开Run。当前终态普通writer拒新evidence，见[现证据writer](../../apps/kokoro-agent/src/kokoro_agent/infrastructure/postgres_model_call_evidence.py)第137–142行。
- 如实际查到原admission/hold或迟到提交，转原正式结算路径并再次确认资金操作；不自动reserve、capture、release、refund或换key。本轮没有调用恢复/结算HTTP；Billing的[recover实现](../../apps/kokoro-billing/src/modules/metering/model-admission.service.ts)使用write事务，不因名称recover就作为本次只读工具调用。

本轮只交调查和方案；上述防迟到与终态关闭属于后续小切片，未授权实施。不做供应商用量平台、通用reconciliation CLI或支付扩建。

## 4. 范围纠偏及未触碰项

原“2条恢复候选”和“历史30积分冻结”不是同一计数。为定位曾有界读取同tenant前三条更早pending admission（10月记录、各预算10）；未进一步读取其hold/总账/处置，也不由预算数推定当前冻结总额。该旧资金事项继续单列保留，不扩为本轮新任务，不能因本轮两候选无资金效果而清零。

排除：Task B新QA成功Run、其30赠送/9实扣/21余额、其他用户、旧供应商资金、真实支付、退款、外部Provider调用和业务代码修改。

## 5. 本轮证据与验证

- 基线：Root `2ef27004`；Agent `49901fd7`、Billing `afbfd790`、BFF `c43457ba`。本轮无源码/gitlink/Schema/契约变化。
- Agent/Billing/BFF分别连接自身owner schema，`REPEATABLE READ READ ONLY`；连接默认read-only，查询/锁超时受限，全部rollback关闭。无跨owner SQL/JOIN，无服务重启、无Redis写入、无模型/资金请求。
- 原登记范围来自本地ignored `own-pending-recovery-scope.json`；本轮严格快照、摘要和只读脚本存本地ignored `var/dev/historical-finance-20261114/`，不提交凭据、完整账务材料或机器日志。初始helper预设应有2条Billing admission导致断言失败；修正为允许且记录0行，没有改业务事实消除失败。
- 验证仅规范evidence解析、定点owner读取、文档diff/新增链接和独立只读审查；不跑业务全套测试或旧成功链。只读快照不是结算验收，物理细因未补造。
