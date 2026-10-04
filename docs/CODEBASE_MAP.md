# Kokoro codebase map

状态：2026-09-19。以 [REPOSITORY_STATUS.md](REPOSITORY_STATUS.md) 与 [ADR-032](kokoro-handbook/decisions/ADR-032-root-submodule-composition-and-repository-identity.md) 为 Root 组合路径与 Git 标识的权威来源。

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
