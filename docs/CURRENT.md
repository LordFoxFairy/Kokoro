# Root 当前组合

状态日期：2026-09-24。Root 是 Git superproject，精确组合以当前提交的 gitlink、`.gitmodules` 与
[`verification/contracts/consumer-inventory.json`](../verification/contracts/consumer-inventory.json) 为准。
业务源码、canonical Schema 和可编辑契约仍由各子仓 owner 维护。实施任务见 [`task.md`](task.md)，
已执行命令与失败记录见 [`progress.md`](progress.md)。

| 子仓 | 当前固定提交 |
| --- | --- |
| `apps/kokoro-app` | `210ddfdd77f24143a0ed0617e2ecf1089bcf513c` |
| `apps/kokoro-bff` | `84a560abeac5b7a63f32d7064abdde849ab33cf9` |
| `apps/kokoro-agent` | `520ec181a101298b4f336aad273ce003b2735955` |
| `apps/kokoro-iam` | `b35a9a5301219654ea344c03407fd355f58c481e` |
| `apps/kokoro-system` | `c0a76a3a7614bf46ea6e665e523f24261862436f` |
| `apps/kokoro-storage` | `38be74ef7fb0b1ddd687c67434d898f8628068fb` |
| `apps/kokoro-scheduler` | `975dee59616a1e0eda609aa69283401344900d83` |
| `apps/kokoro-capability` | `9c88d0d934387b590bc74dae0179a587292e0253` |
| `apps/kokoro-billing` | `63e0ab6e61b397f23f7ab71f5d6dc9df3d6de0fa` |
| `apps/kokoro-mori` | `ca76c2e12861a2e4a6af3049f6df8c34b417c158` |
| `libs/kokoro-web-shared` | `0c4e87ace01340aaa07bc57935f1d98b8e77af14` |

`kokoro-app` 是本轮唯一正式前端；Mori 不在本轮业务改造内。正式能力仓当前仍是
`kokoro-capability`，尚未完成向 `kokoro-platform` 的原子切换。各子仓自行持有测试；Root 的
`scripts/tests/` 只验证组合工具，不是业务单元测试总目录。

## 已验证到的边界

- Web `/` 是固定单租户公开首页，`/login` 自动发起固定 Product OIDC，不依赖 System manifest；
  `/app` 只以 Product Session 作认证闸，System 暂不可达不会变成整页“配置不可用”。仅 Web dev
  在 3310 运行时，缺少常驻 BFF/IAM/RP 配置，登录显示诚实的失败重试，不等于在线登录。
- 固定上述 IAM/BFF/Web 提交运行的独占真实 HTTPS Product Session smoke 已通过：Web 同源入口、
  BFF/IAM 协议链、在线会话、Chat 列表 Bearer 代理与退出，测试自有资源剩余 0。这不是 3310 常驻
  服务的证明，也不覆盖首条消息、Agent worker、Web 重载或真实模型 provider。
- Agent 已发布 typed `createRun`/`replaySessionEvents` 契约及空最终文本完成事件；BFF 已完成
  新会话首消息事务、assistant Message 与 AG-UI 同事务投影，并固定生成的 Agent HTTP 消费者。
  Web 已按 BFF 严格 MessageCreate 契约发送首消息。三仓各自门禁通过，**尚无固定 SHA 的真
  Web→BFF→Agent worker→持久重载组合验收**。
- 本地 PostgreSQL/Redis 复用一套实例与应用凭据，数据 owner 各自使用 schema/连接边界；
  Root 不要求此阶段拆分多个数据库角色，不允许跨 owner SQL。Storage owner schema 已有独立验证，
  但 Storage 用户文件链尚未与 Web/BFF/Agent 闭环。

## 仍未完成

1. 固定 SHA 真首消息/worker/AG-UI/重载组合验收；Web 对 BFF public contract 的全量 generated
   消费与单一 AG-UI 网络协议，以及默认个人私有、显式分享、同 tenant 他人与跨 tenant 负例。
2. IAM Team 窄读到 BFF Product projection 再到 Web 的串行消费；删除 Web 旧 IAM/Team 直连。
3. Storage/Platform/System/Scheduler 各自 owner 的能力调用、契约与数据闭环；Billing 最后。
4. 当前 inventory 的 11 条 broken edge 与 1 条非法 Web→IAM 旁路，不能因为局部 smoke 通过而标绿。

当前可执行门：`python3 scripts/verify-repository-topology.py`、
`python3 scripts/verify-contract-checkpoint.py --expected verification/contracts/checkpoints/w1b-iam.json`、
`python3 scripts/verify-iam-relay-policy.py`、`python3 scripts/verify-main-only.py` 和
`python3 -m pytest scripts/tests`。旧 `verify-ten-repository-full.sh` 与
`run_stage2_owner_health.py` 的共享状态编排已暂停；它们不是当前全仓验收证据。
