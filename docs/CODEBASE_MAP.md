# Kokoro codebase map

## R220 当前Agent接线入口（2026-10-04）

Agent R219冻结候选已实际消费固定System955bd587的3.0：`clients/system.py`负责严格同revision执行界；`model/factory.py`的ModelHttpClients拥有sync/async客户端与最终wire界；`agent_factory.py`负责构造失败和handle关闭时资源转移/释放；`system_consumer_contract.py`负责唯一固定receipt验证。Root工程与installed已复验，仍未提交/3310启用，不等于正式Billing或用户聊天闭环。下面R218 consumer2.0/未实施描述是历史RED，不覆盖此候选。当前状态以CURRENT R220与progress收据为准。

状态：2026-09-19。以 [REPOSITORY_STATUS.md](REPOSITORY_STATUS.md) 与 [ADR-032](kokoro-handbook/decisions/ADR-032-root-submodule-composition-and-repository-identity.md) 为 Root 组合路径与 Git 标识的权威来源。

## 当前产品业务入口（R200）

- `docs/kokoro-handbook/product/09-v2-prd.md`：唯一当前PRD；用户对象关系、完整范围/交互、现70组验收索引及里程碑。
- 同product的00为长期愿景，01/05/06/07为补充；`docs/INDEX.md`与handbook README提供导航。
- PRD要求不当实现证据；任务仍task、运行事实CURRENT、系统结果test-cases、证据progress，无新计划中心。

## R218 当前System消费来源与Agent真实RED

- System最终固定本地commit955bd587f46a771e43a4330d202d90a7d2d67262，3.0 artifact94ed9165/provenance5fda620c、19source；原bd09253/74c338/a2c1为历史冻结。两个生成器修metadata，uniqueAgent仍pending，Root205/16contract/fresh23/22已验，未push/3310消费。
- Agent实际consumer仍2.0；现真实`tests/integration/test_model_provider_retries.py`新增两HTTP/SDK RED，Root14旧pass/2新fail；现三测试/四D0已刷新并Root18fail/23pass边界收据RED；九source/七tests/四D0已Root准入原子Green写入，源码/installed/真实native付费链没有因此通过。
- 精确新receipt在Agent自身唯一provenance后续落地；Root临时报表不成为可编辑contract。后继必须从固定Git objects验证原件，不引入跨仓运行时import/SQL/ORM。

## BFF有限Message准入与exact-client生命周期（R217）

- 本地main交付7289b3a4ae8f2df5c249350d59b9405c33fb4083；现 `src/infrastructure/postgres/chat-turn-commit.ts`唯一拥有Message事务、Project→Conversation锁、canonical dispatch replay、4.5秒总界和checked-out client具名error listener→release→remove生命周期。`src/http/routes/chat-authorization.ts`仅Message取消无界owner预读，可信IAM与其他路由授权保持；无新SQL/契约。
- Root四真实故障矩阵及完整182PG/Redis通过；源码树395文件精确绑定门。原22protected bytes/modes全保持，现20mixed；当前3310未启用该commit，不从mixed工作树冒正式发布。
- 组合gitlink/发布/页面/Agent与Billing整链状态以RootCURRENT/progress为准，不用本仓切片冒产品闭环。

## System执行界本地交付与Agent后继（R215）

- System `model-catalog` revision/resolve是技术执行界唯一owner：现`database/schema.sql`、`revision-content.ts`/repository/service、`schemas/resolve.schema.ts`与`resolve.repository.ts`；draft可null，published两positive int32且output<=context，digest/immutable/generation同事务，首读/cache共用唯一关系校验。
- 本地源码commit `bd09253793a22dbe7503a05f8bf4e5b2af542e4c`；机器artifact `3.0.0` SHA74c338f2/provenancea2c1；Root完整202/13contract/fresh23/22已验。未push、原3310未升级、Agent依旧strict2.0消费者，不能冒模型/收费闭环。
- Agent当前R216四D0已独审通过、实际consumer仍未实现：现`src/kokoro_agent/clients/system.py`及现model caller严格固定消费与真实SDKoutput cap；缺Billing仍0 provider。Root不维护第二contract/SQL，不放宽旧consumer或伪造Admission。

## Root 职责

`Kokoro/` 是 Git superproject，不是业务源码 monorepo。它只拥有：

- `apps/`：可部署子仓的 gitlink；
- `libs/`：独立版本化共享库的 gitlink；
- `docs/`：跨仓架构、ADR、组合发布与验证证据；
- `deploy/`、`ops/`、`scripts/`：Root 组合编排和静态治理；
- `verification/`：未来跨仓行为验证的唯一位置。

Root 不保存业务数据库 schema、跨仓可编辑 contract、子仓 lockfile 或子仓 unit/integration 测试。`scripts/tests/` 是 Root Python 治理工具的测试，不是应用测试总目录。

## Root 本地受管开发入口

- `scripts/dev/serve_local_login.py`：唯一3310前台组合，IAM/BFF/Web正规登录、可选真实Chat及显式Storage profile；原运行组合未自动升级。
- `scripts/dev/local_storage_runtime.py`：同一组合的正式Storage源码/owner schema/真实S3与ClamAV装配及owned桶、进程反序清理；显式`--storage-node-bin`，不拥有文件业务事实或第二contract。
- `scripts/dev/local_chat_runtime.py`：同一组合的System＋标准Agent HTTP/worker与反序清理；不拥有业务事实。
- `scripts/dev/model_provider.py`：显式外部OpenAI兼容profile的私有文件校验与HTTPS模型库存观测；无导入时网络/secret副作用。
- 原 `scripts/e2e/run_web_real_model_worker_smoke.py` 的Ollama-only guard保持，不作任意远端放行。
- `scripts/e2e/chat_snapshot_evidence.mjs`：fresh单run真实Chat验收的纯内存Message全文/身份/状态/watermark冻结与脱敏差异；正式real-model Chromium driver在RUN_FINISHED后及reload后调用，不拥有Message事实，不适用历史会话必须恰两条。
- 工具测试在既有`scripts/tests/`；正式System/Agent模型owner仍在各自仓，Root不持有第二可编辑contract/SQL。

## Root 个人安装真实组合

- `scripts/e2e/product_skill_installation_smoke.py`：仅校验BFF public本人安装五操作、原ACK/当前读、false筛选/两页、remove/reinstall及撤权证据，无进程/数据owner。
- `scripts/e2e/run_bff_skill_draft_sandbox_smoke.py --product-installation`：复用已有IAM/BFF/Platform/Storage、两已发布不同series、owned单库schemas/桶与统一回收；与`--agent-source`互斥，默认模式不变，不启动Run。

## BFF 会话归属 Move producer（2026-10-03）

- `apps/kokoro-bff/contract/openapi/v1/openapi.yaml`：唯一 public7.1 `POST /v1/sessions/{id}/move` owner机器契约；Root不维护可编辑副本。
- `apps/kokoro-bff/src/http/routes/move-session.ts` / `src/http/move-session-input.ts`：受信请求与闭集输入，Application Chat service调用同事务repository。
- `apps/kokoro-bff/src/infrastructure/postgres/chat-repository.ts`：Chat事实与具名Move委派；Move事务唯一位于现`conversation-move.ts`，排序Project→Conversation锁、归属与final receipt同事务、same-key赢家恢复；`conversation-move-lease.ts`负责有界PoolClient/unknownCOMMIT lease销毁，现mappers纯receipt decode，无schema/contract变更。
- Move producer原源码284b/发布态0333；职责拆分源码6c5cee0/发布文档5e119cd。Web本地main21ad177已固定消费public7.1及该owner commit，包含严格client/同源adapter；当前3310运行副本仍未启用Move。ProjectDELETE/Storage释放不是本接口职责。最终Root组合身份以gitlink与CURRENT为准。

## Agent invocation-local取消边界（R207，2026-10-04）

- `apps/kokoro-agent/src/kokoro_agent/model/call_scope.py`：单invoke exact driver/model task所有权、唯一5秒默认、固定deadline与typed settlement fatal；无全局Run registry/私有SDK/SQL或费用事实。
- `apps/kokoro-agent/src/kokoro_agent/execution/run_agent.py`：显式native driver同步登记/shield，三路seal/terminal前settle；`publish_agent_events.py`避免投影重复cancel且仍join。
- `apps/kokoro-agent/src/kokoro_agent/worker/main.py`：production私有SIGTERM/budget/drain入口；Supervisor超时先stop-intake再真实exit70，不走正常cleanup/lease release。
- `apps/kokoro-agent/tests/integration/test_model_call_fatal_exit.py`：真实child fail-stop及parent SIGTERM系统门；`tests/integration/database/test_model_call_runtime_chain.py`：原生PG/checkpointer取消完整快照门。
- 本地源码commit92b802e；Root306真PG/3生命周期/完整2192默认门已验，资源deselected不冒通过；未push/原3310未消费，完整模型/费用/用户链仍按CURRENT推进。

## Agent model-call 内部持久边界（R193，2026-10-04）

- `apps/kokoro-agent/src/kokoro_agent/model/call_models.py`：不可变prepare/authorization/dispatch/evidence command、receipt与最小Protocol。
- `apps/kokoro-agent/src/kokoro_agent/model/call_artifacts.py`：具名planned/authorization/attempt canonical编码及冻结recipe peer-path验证；无SQL、env、网络或infrastructure import。
- `apps/kokoro-agent/src/kokoro_agent/infrastructure/postgres_model_call_repository.py`：Run→Attempt锁序、lease/fence/DB时间、一次dispatch CAS、原receipt重放及内部strict append委派。
- `apps/kokoro-agent/src/kokoro_agent/model/call_evidence.py`：完整usage/v1 RFC8785原bytes及冻结identity/planned/authorization/time/seal/revision纯校验。
- `apps/kokoro-agent/src/kokoro_agent/infrastructure/postgres_model_call_evidence.py`：Attempt head保护下的immutable Evidence读取、contiguous revision insert/head CAS、唯一Run completeness同事务投影；不拥有第二wire contract或provider许可。
- Agent当前本地main `c3bf769`（四D0终态封存设计），A3a实现仍绑定`2a9491e36fe5bb94a166f0cd4053e00876bd34a7`；Root实际292真PG与完整2178默认门通过（390资源deselected非业务通过）。Root组合gitlink仍须独立集成，不把本地提交冒远端发布。
- 后继finalizer、runtime caller、provider/Billing与真实用户费用未接，本图不新增第二contract/schema或归属实体。

## 子仓路径与 owner

| 仓库 | Root 路径 | owner |
|---|---|---|
| `kokoro-app` | `apps/kokoro-app` | Web UI、同源 adapter、浏览器交互状态 |
| `kokoro-mori` | `apps/kokoro-mori` | Mori 音乐产品 UI |
| `kokoro-bff` | `apps/kokoro-bff` | Conversation、Message、Share、Project、ScheduledTask、AG-UI projection |
| `kokoro-agent` | `apps/kokoro-agent` | Run、HITL、execution evidence |
| `kokoro-iam` | `apps/kokoro-iam` | identity、tenant、authorization、audit |
| `kokoro-system` | `apps/kokoro-system` | site/host/workspace/runtime/policy/model catalog |
| `kokoro-billing` | `apps/kokoro-billing` | payment、subscription、ledger、metering |
| `kokoro-capability` | `apps/kokoro-capability` | skills/MCP control plane |
| `kokoro-storage` | `apps/kokoro-storage` | object lifecycle metadata |
| `kokoro-scheduler` | `apps/kokoro-scheduler` | durable schedule/occurrence/lease/outbox |
| `kokoro-web-shared` | `libs/kokoro-web-shared` | versioned shared frontend package |

Browser → `kokoro-app` same-origin adapter → `kokoro-bff` → owner services is the fixed request direction. Web 不直连内部 owner；跨仓只使用 owner 发布的版本化 contract、API/RPC 或事件，禁止 sibling 相对路径 import。

## 开发与验证

先初始化精确 gitlink：

```bash
git submodule update --init --recursive
```

再进入目标子仓执行该仓自己的 README/ACCEPTANCE 指定门禁。Root 只执行拓扑、分支、组合 contract/integration/e2e/smoke；当前可用静态入口：

```bash
python3 scripts/verify-repository-topology.py
python3 scripts/verify-main-only.py
python3 -m pytest scripts/tests
```

`kokoro-model` 与 `kokoro-mori-p1-arrangement-recording` 不属于 Root 组合；历史文档只作为考古，不构成当前实现入口。

## Root typed Skill Source 验收入口（2026-09-30）

- `scripts/e2e/run_bff_skill_draft_sandbox_smoke.py`：沿既有IAM/BFF/Platform/Storage发布组合，显式 `--agent-source` 接独立Source测试切片；默认模式不启动Agent。
- `scripts/e2e/agent_skill_source_smoke.py`：跨owner测试driver，使用生产Agent HTTP/JWKS/installer/repository/proof/typed reader；不是业务服务、SDK或另一套模型执行器。仅显式模式、Agent安装环境和精确gitlink通过后启动；自有schema/Redis占有资源在IAM库回收前关闭。
- `scripts/tests/test_agent_skill_source_smoke.py`：Root driver协议/资源边界与纯原生组件，子仓业务测试仍各自维护。代码/单测成功不构成真实owner组合或浏览器通过，当前结果见CURRENT/task/progress。

## R194 Conversation Move 交互切片

- Web `src/engine/machine.ts`：same-scope matching ACK与view generation分离；503/409 in_progress保exact未知command，不写绑定副本。`app-frame.tsx`的owner GET刷新先于导航/焦点view fence。正式Web B+C a75345f（clean machinea3321/AppFramedda20f/systemafbbf）已本地窄集成；mixed字节保留，未同步3310。
- 唯一测试入口仍`docs/test-cases.md`与Web既有`tests/system/oidc-rp-next-http.integration.test.ts`，Root62663四真实Next/Chromiumsame-scope通过；crossscope/actor恢复后继，不用同engine邻测冒充。
- Agent A3b四D0已提交，终态源`postgres_run_leases.py::finalize_terminal`的三现文件候选已接同cursor封存，原sealed投影/denied两P1经5真实RED→11GREEN已静态关闭，最新303全PG通过；full工程仍显式资源闭包漏helper一项失败，现manifest精确5resource登记3ea5已Root44定点＋build0，完整新manifest门待重跑，未正式验收提交实现。后继仍复用现call_evidence纯规则和postgres_model_call_evidence cursor，不建第二模型契约/费用owner。

## R195 当前实现入口

- Agent8c08ea4：现model/call_evidence纯规则＋postgres_model_call_evidence cursor primitive＋postgres_run_leases原终态事务；runtime_profile_sources显式5resource闭包，不是新provider caller。真实303PG/2178工程/wheel门见CURRENT/progress。
- Web W2三D0描述page内单槽冻结command替代engine Move intent；matchingACK即时source索引精确evict与source/target版本刷新，verified auth生命周期清理；生产GREEN仅授权/待验。测试仍既有oidc-rp-next-http.integration入口，53415三真实RED见test-cases。Agent A4只文档设计，与Web独立并行。

## R196 候选接线与验证范围（2026-10-04）

- Web `apps/kokoro-app/src/ui/shell/conversation-move-coordinator.ts`：候选唯一document-memory Move命令，session/project归属仍BFF唯一事实；`page-clients.ts`只失效浏览器metadata索引。正式17路径ce40cecc已验提交；三P1/导航与full回归经Root闭到candidate，原3310尚未启用。旧engine Move路径在本候选删除，不增加Message/Project实体。
- Agent `apps/kokoro-agent/src/kokoro_agent/model/factory.py`：五实际SDK构造main814e929显式retry0，`tests/integration/test_model_provider_retries.py`以锁定SDK→自有HTTP peer验证物理请求数、stream与取消；Root14行为通过，仅sandbox，不冒真实费用。后续A4仅原生AgentMiddleware.awrap_model_call，非BaseChatModel代理；Billing正式准入/证据读ACK/结算未接。
- 当前formalBFF8e33 clean archive Root完整173真实PG/Redis门；候选工作树184历史结果不等于formalcommit覆盖。原3310仍public7.0/noMove，clean组合发布必须另验证，不散复制混合树。


### R197 运行输入身份与会话绑定

BFF唯一Conversation归属是nullable `project_ref`；正式Webce40cecc消费public7.1 Move，无第二归属实体。Root此片仅pin已验Webce40cecc/Agent814e929，其他owner pins保持；旧3310临时副本仍public7.0/noMove。`scripts/dev/serve_local_login.py`是清理自有应用/IAM库的一次性fixture，不是持久应用更新入口；切换前先确认旧测试对话保留政策并用独立clean release构建，不复制mixed/重置共享数据。研发业务闭环、Billing owner与完整Wave0–7边界不因此组合候选而完成。


### R198 原生 model-call guard 与 Billing 契约前置

- BFF Conversation仍唯一nullable `project_ref`，Web只消费归属与同ID Move，不建立第二会话事实。
- Agent `model/call_runtime.py` 候选：锁定SDK `ModelRequest.runtime.execution_info` locator确定UUIDv5，durable prepare后Billingconsumer缺席failclosed；不是provider wrapper或正式Billing client。`agent_factory.py` 在main/Swarm/GP/catalog各实际native middleware链装配；`execution/runtime_profile_plan.py` 在冻结前确定BFS shortest/lex peer path并纳入GP built-in profile；`worker/main.py`注入正式PostgresModelCallRepository。四D0前置8a3169bd；13生产/测试与四D0最终17path59034f4已验提交，正式Billingconsumer/成功模型链仍未接。
- `tests/integration/database/test_model_call_runtime_chain.py` 是正式invoke_once/PG terminal业务oracle，Root54105 main负例已验；FakeBus仅测试事件传输，owner/provider为loopback，不冒Redis/真实Billing/model成功链。完整caller/recovery仍待测。
- Billing `scripts/openapi-v2-target.ts` 是experimental producer，正常contract:generate输出 required closed subject；8path364f4ba与directSHA7d631336已独立clean门验，仅contract不等于Admission runtime。
- IAM `scripts/pack-sdk.ts` 与 `test/consumer/iam-client.consumer.test.ts` 已有正式clean owner artifact/仓外消费者路径；SDK root facade `IamClient.verifyBillingAuthorization` 为后继Billing准入唯一消费入口。开发验证不等公网Registry，长期portable lock仍需不可变可解析制品；不复制SDK源/第二JWT实现。

R198最终Agent源入口59034f4：Root实际304真PG/2182默认门及post-doc构建绑定本切片；其main缺准入负例已验，GP/catalog/Swarm实际caller/recovery继续用既有系统矩阵验收，不创建第二runtime。


### R199 当前正式与未验入口（2026-10-04）

- Billing正式26aeec6：`vendor/iam/kokoro-iam-client-0.7.0.tgz`/`provenance.json`只读owner构建制品，package根唯一消费；ADR0004及现architecture/toolchain gate核version/commit/contract/archive/lock。Rootclean完整门已验，但`src/modules/metering/iam-billing-authorization.client.ts`仍是后继方案，尚无运行接线或资金保证，勿从文件名推断已实现。
- Agent生产59034不改；现`tests/integration/database/test_model_call_runtime_chain.py`唯一未提交41fe扩公开Supervisor终态恢复及prepare锁取消，后者Root全PG真实FAIL。锁定SDKv3 stream的model-operation取消边界待最小现model/execution设计门；不复制SDK、追加第二RPC或归属模型，不冒整个graph/checkpoint drain。
- Conversation唯一nullable project_ref保持。当前3310仍旧运行副本，不因Root源码gitlink/已验候选或artifact更新自动启用Move；Root独占运行资源，原fixture数据保留待答。


## R210 当前执行边界

- BFF有界Message候选只在 `/tmp/kokoro-r205-bff-clean.path` 指向的隔离archive：具名 `src/infrastructure/postgres/chat-turn-commit.ts`（8f04afa9），outbox repo只委派，HTTP reply补受信x-request-id。Root1737完整177真实PG/Redis与全门通过，但剩余资源矩阵/原mixed集成/3310仍OPEN。不能从本地图推断原BFF源码已发布新具名文件。
- System032ff524只提交四D0设计；现runtime/API仍2.0且执行界0。目标沿现model-catalog/revision/resolve，禁止新config/pricing owner；Root独审后R211先在既有System两个test入口真实RED，不提前Agent consumer。
- R211两个唯一writer、scope与证据仍在同 `docs/task.md`，不另建计划。
