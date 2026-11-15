# 两笔历史 financial unknown：只读对账与处置方案

**当前状态（2026-11-15）：原两笔已完成非资金审计关闭，原usage/ACK与资金不变；结果见文末§7。下方§1–5保留只读阶段原事实。**

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

## 6. 2026-11-15 已批准实施门：仅关闭这两笔无预占残留

用户已授权原命令防迟到确认、审计关闭及PR/main交付；不授权改变任何资金或将unknown改零。本节替代§3“本片未授权实施”的历史状态，不扩大到旧held30。

### 最小职责与选择

- Billing复用永久command receipt，新命令`model.close-unreserved`存唯一非资金关闭结果；不新增Billing表，不复用或伪造model.settle/原held ACK。close沿原model.admit key/attempt永久锁和run/request锁，拒已有原receipt/admission/原hold；create在同原锁的最终事务中重核关闭事实，故close与迟到admit只能一方胜出。
- Billing只证明其拥有的“原预算未创建且已禁止迟到创建”，不独立认定Agent的terminal/usage。BFF沿现Agent专用身份与原Run实际提交者转发，不增OAuth、token、Cookie或IAM调用，不放宽Agent历史readPrepared。
- Agent仅显式operator命令触发这两笔，关闭前/后按Run→Attempt锁复核terminal、sealed not_dispatched/requested_unknown、dispatch/admission/ACK空和原head完整绑定。网络在事务外。成功后新增一条必要append-only关闭事实，关联owner closure_ref/原证据；原usage/ACK/Run完全保持。常规worker不自动调用close，现恢复扫描只排除匹配关闭事实。
- 不采用仅SELECT miss后清ACK/造0，不改recover原200/404语义，不建通用reconcile CLI/平台。Agent因现有ACK只代表真实settlement、现审计/控制表不属本事实，采用一张窄close表而不复用错误语义。数据owner通过单次显式additive expand承接现有数据，canonical SQL唯一、漂移即停、不得重建；批准例外及回退留owner ADR。

### 写区、依赖与最低充分验收

| 顺序 | writer | 写区／交付 |
| --- | --- | --- |
| 1 | 主控 | Billing metering close服务/原admit最终guard、canonical exp11及正式生成、现真实PG/admit tests、相关owner设计文档 |
| 2 | no_reservation_boundary_design | BFF既有model-admission close转发/生成消费者、内部1.4契约及现HTTP定向测试；仅在Billing正式commit后消费 |
| 并行独立本地事实 | no_reservation_agent_design | Agent窄close表/显式additive/CLI/本地事务与原pending排除；client最终消费BFF正式commit，现相关PG/transport测试和owner设计文档 |
| 最终 | 主控 | 独审/停写验收，隔离真实BFF→Billing及Agent持久事实链；原2本地命令执行前后逐字核原记录/资金不变，原PR/main精确组合和本轮分支清理 |

验收只覆盖本次独有风险：两种admit/close竞态胜序、重放/丢ACK、错身份/原binding或evidence、已有授权/hold拒绝零资金效果；Agent原evidence不变、候选排除且其他记录保留。复用现套件，不为每层复制完整矩阵，不重复模型、支付或全产品E2E。暂不执行任何capture/release/refund；一旦查到实际资金状态偏离则只暂停对应处置并确认。

### 执行 TODO

- [x] Billing原命令防迟到关闭、正规契约及定向真实PG。
- [x] BFF同可信通道及Agent独立审计关闭、显式有数据additive与最少相关门。
- [x] 主控冻结审查/真实隔离链、仅两笔实际关闭且原事实/资金保持。
- [x] 三owner各自PR已main且本轮子仓分支已清；Root精确组合/文档交付包齐备，Root自身PR/main及分支出口按实际后置核验收口。

## 7. 2026-11-15 实际闭环与交付收据

### 正常原两笔结果

U-01/U-02各有一份Billing永久`unreserved_closed`关闭凭据和Agent独立关闭事实；相同原命令重放返回同一结果。正式repository对精确两target的`next_work`均为空，不再当恢复候选。原两Run/Attempt/Evidence整行JSON摘要及`xmin`前后完全一致；原usage仍unresolved/unknown，`financial_ack_bytes`仍为空。关闭是独立事实，不是修改旧证据、供应商零用量或资金结算ACK。

对应原payer账户及其grant/hold/allocation/journal/admission/usage/settlement八类资金行摘要与`xmin`前后相同；没有reserve/capture/release/refund/补偿或模型调用。另案旧冻结/更早pending从未被本片关闭、归零或重算。

正常操作前核所有Run终态/无待派发、进程cwd归属；只对原Agent schema进行批准additive，原表不动。受控恢复本任务BFF、Billing、AgentHTTP及独立Worker，原配置/凭据/端口/数据保留，三个HTTP健康且四进程在位；不是全产品重跑或部署。没有重启共享Docker、清卷或改变其他owner数据。

### 实际证据而非数量证明

- 隔离1自建数据库、各owner独立schema、正式installer；仅复制U-01的必要持久事实。Agent显式CLI→真实BFF→真实Billing→Agent保存关闭，原键重放；迟到原admit实际409。八类资金表0，原三表行摘要/`xmin`保持；数据库已回收、独立Redis剩余0。
- Billing当前核心真实PG三场景先RED后GREEN（含close/late-admit两胜序），相关源码8文件342 PASS；新revision随后收窄为原int64及绝对行尾，定向PG/HTTP4 PASS、types/build/lint/正规生成/drift通过。旧exp10整字节逆证及其他原API不变。
- BFF主控停写SHA核等后8相关文件38 PASS/0skip，相关type/build/lint与正规生成通过，独审CLEAR；loopback和真实链分别标注，不混认。
- Agent主控停写27路径核等，5相关入口124 PASS；writer一次相关门258 PASS/0skip（包含41真实PG/77 transport等，不叠加计算）。Pyright/Ruff/format、contract/compiler、wheel/sdist与包内SQL/模块字节核等通过；原身份漂移P2已真实RED→GREEN，独审CLEAR。
- 原始收据仅在本地ignored `var/dev/historical-finance-20261114/`。隔离初期占用Redis逻辑库和显式operator配置未补原秘密配方导致setup FAIL，原库/keys未动；仅修私有接线。正常关闭helper完成实际两笔后，其后置核验漏sys导入/API调用签名误用产生FAIL；没有重新执行reload或close，只读续验后PASS。所有原失败保留，未改生产行为或放宽断言消绿。

### Git出口与剩余范围

三个owner已实际正常合main，完整merge树均等已验源，本轮local/remote topic已清：Billing [#6](https://github.com/LordFoxFairy/kokoro-billing/pull/6)→`c55abf34`，BFF [#28](https://github.com/LordFoxFairy/kokoro-bff/pull/28)→`2e0affb1`，Agent [#50](https://github.com/LordFoxFairy/kokoro-agent/pull/50)→`f231b04a`。正常进程不因同源码merge再次重启。Root只固定这三个精确gitlink及本报告/TODO/CURRENT，inventory349原引用从280个真实已提交blobs重读，新增4份实际关闭边界源码证据；不机械替摘要或修改旧消费pin，不将内部close协议混入公开API门户。最终Git状态以各PR MERGED、local main clean及本轮topic清理的后置核验为准，不以本节代替Git检查。远端CI未作为绿色依据，不循环等CI或绕分支保护；无关支付/全默认/浏览器/模型旅程未重跑。

本片唯一目标已实际关闭，无待实施的“无预占残留关闭”项；R-06、外部授权/渠道、本人语音、可选完整E2B、性能/容量/CI事项及旧资金事项仍按原边界暂存，不自动开启下一任务。
