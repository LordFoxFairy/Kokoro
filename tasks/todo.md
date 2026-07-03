# 当前任务：三仓彻底重写 + handbook 对齐 v2.1（/goal 2026-07-02 → 07-03 完成）

基准：`docs/superpowers/specs/2026-07-02-three-repo-rewrite-blueprint.md`（v2 重写）
+ `docs/superpowers/specs/2026-07-02-handbook-alignment-v2.1.md`（handbook 对齐，法源 docs/kokoro-handbook 11/12/03/ADR-004/modules）

## 阶段二：毁灭与重塑 ✅

- [x] contract/ 中枢重建（spec 四部立法 + 确定性生成器 + 字节门禁；golden 20）
- [x] kokoro-agent 重写 + v2.1 对齐（执行链路布局、TTL 租约、ToolPolicyMiddleware、skills/mcp、namespace、respond↔ask_user）
- [x] kokoro-session 重写 + v2.1 对齐（五集合、准入/幂等、pending_pauses、snapshot、control 校验、DB-first）
- [x] kokoro-web 重写 + v2.1 对齐（snapshot-first 水合、双 HITL 卡、显式状态机、decision_id）
- [x] 每仓审查回收 + findings 修复

## 阶段三：协同打磨 ✅

- [x] 跨栈 e2e 门禁 `scripts/e2e-v21-gate.py`：23 断言全绿（HITL ask_user respond + write_file 审批、幂等/409、snapshot 恢复、Last-Event-ID 续传、二轮 run）
- [x] 跨栈缺陷修复：wire null vs 缺席（agent exclude_none + 回归测试）；session 默认审批集补 write_file；LocalFake hitl 脚本开关
- [x] handbook 反哺注记（11/12/modules 三处 + spec 偏差记录）

## 门禁终值（2026-07-03）

| 仓 | 结果 |
|---|---|
| contract | golden 20 passed + check.py 14 mirrors + 双跑字节稳定 |
| agent | 208 pytest（redis/mongo 实跑）+ pyright 0 + ruff 绿 @ 83f40d0 |
| session | 127 tests + tsc + eslint 绿 @ 2d54a73 |
| web | 166 tests + tsc + eslint + build 绿 @ 8ec9932 |
| 跨栈 | e2e-v21-gate.py PASS（23/23）|

## 已明示不做 / 后续

- swarm/TeamSpec 编排（handbook P2；设计讨论已入 memory）
- music 等垂类 job 工具链（编排第一个参考实现，待 platform credit/job 接入）
- MCP live smoke（真 server）；artifact_ref/summary 生产者（P1）
- 真浏览器 × 真 session 联调走查（web 已有 preview 走查 + 全量单测，未跑真栈浏览器）
- 分支收口：四仓 rewrite/v2 全部验证绿、未合 main、未 push——**等用户定夺合入方式**
