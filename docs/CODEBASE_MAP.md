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

- `scripts/dev/serve_local_login.py`：唯一3310前台组合，IAM/BFF/Web正规登录与可选真实Chat。
- `scripts/dev/local_chat_runtime.py`：同一组合的System＋标准Agent HTTP/worker与反序清理；不拥有业务事实。
- `scripts/dev/model_provider.py`：显式外部OpenAI兼容profile的私有文件校验与HTTPS模型库存观测；无导入时网络/secret副作用。
- 原 `scripts/e2e/run_web_real_model_worker_smoke.py` 的Ollama-only guard保持，不作任意远端放行。
- `scripts/e2e/chat_snapshot_evidence.mjs`：fresh单run真实Chat验收的纯内存Message全文/身份/状态/watermark冻结与脱敏差异；正式real-model Chromium driver在RUN_FINISHED后及reload后调用，不拥有Message事实，不适用历史会话必须恰两条。
- 工具测试在既有`scripts/tests/`；正式System/Agent模型owner仍在各自仓，Root不持有第二可编辑contract/SQL。

## Root 个人安装真实组合

- `scripts/e2e/product_skill_installation_smoke.py`：仅校验BFF public本人安装五操作、原ACK/当前读、false筛选/两页、remove/reinstall及撤权证据，无进程/数据owner。
- `scripts/e2e/run_bff_skill_draft_sandbox_smoke.py --product-installation`：复用已有IAM/BFF/Platform/Storage、两已发布不同series、owned单库schemas/桶与统一回收；与`--agent-source`互斥，默认模式不变，不启动Run。

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
