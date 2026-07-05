# 测试报告：会话软删除（V2-M1）

- 日期：2026-07-06
- 规格：`docs/kokoro-handbook/technical/16-session-deletion-cascade.md`（软删除修订版）
- 范围：契约（DELETE 端点）+ session（状态位/四路闸/cancel 联动）+ web（客户端删除调用）；
  **agent 侧零改动**（裁定：删除不触碰 checkpoint/工作区/ledger）

## 执行汇总

| 层 | 套件 | 结果 |
|---|---|---|
| L1 契约/单元 session | `npm test`（190 条） | **190 passed** |
| L1 契约/单元 web | `npm test`（175 条） | **175 passed** |
| L1 agent（确认零回归） | `uv run pytest`（423 条） | **423 passed** |
| 静态 | tsc（session/web）+ ruff/pyright/mypy（agent） | 全 0 error |
| L2 跨栈 e2e | `scripts/e2e-v21-gate.py`（34 断言，含新增 7 条） | **PASS** |
| L2-L3 全量 | `scripts/verify-all.py` 六档 | 见验收报告（终局复跑） |

## 新增用例明细（全部首跑通过）

```text
SD-S1  DELETE 活跃会话：run.cancel 上 control 流 + deleted 置位 + 202 + 文档全保留   PASS
SD-S2  幂等：重复删除 / 删除不存在会话 → 同 202                                      PASS
SD-S3  deleted 四路闸：messages/snapshot/events/files → 410 session_deleted          PASS
SD-ST  store 同语义矩阵（memory + mongo）：置位幂等/不存在空操作/事件史保留          PASS×2
SD-W1  web deleteConversation：本地立即移除 + deleteSession fire-and-forget          PASS
E2E-27 终态会话删除全链：202 → 410（snapshot/新消息）→ 重删幂等 → 工作区文件仍在    PASS×5
E2E-28 暂停中删除：DELETE → run 收敛 cancelled → snapshot 410                       PASS×3
```

## 诚实记录

```text
- session 全量套件在一次并行全跑中出现 3 条既有时序 flake（selected_model 解析 /
  SSE live tail），单文件与复跑均绿；与本变更无关（涉事文件未触碰该逻辑），
  flake 治理列入 V2 待办。
- L5 浏览器走查见验收报告（删除按钮真链路 + 截图存证）。
- mongo 档 store 矩阵在本机 mongo 可达下实测（softdel 项）；CI 无 mongo 时按既有
  约定显式 skip。
```
