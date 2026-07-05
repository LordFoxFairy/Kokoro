# 验收报告：会话软删除（V2-M1）

- 日期：2026-07-06
- 规格：`technical/16-session-deletion-cascade.md`（软删除修订版）
- 姊妹篇：`m1-session-deletion-test-report.md`（用例明细）

## 验收判据 vs 结果

| # | 判据（来自规格） | 结果 | 证据 |
|---|---|---|---|
| 1 | DELETE 端点契约化（与 snapshot 同路径，202 {status:"deleted"}，幂等） | **通过** | contract/spec/http.yaml + 三仓 regenerate；SD-S2、E2E-27 |
| 2 | 软删除=状态位，数据全保留 | **通过** | SD-S1/SD-ST（事件史保留断言）；E2E-27 工作区文件仍在磁盘 |
| 3 | **agent 侧零改动**（裁定核心） | **通过** | agent 仓本轮零源码变更；agent 423 测试原样全绿；走查 agent 日志零异常 |
| 4 | 活跃 run 随删除正常收口（复用 cancel 链） | **通过** | SD-S1（cancel 上 control 流）；E2E-28（暂停中删除→run cancelled） |
| 5 | deleted 会话四路读写闸 410 | **通过** | SD-S3（messages/snapshot/events/files 全 410 session_deleted） |
| 6 | 幂等/多 pod 安全（条件更新语义） | **通过** | SD-S2 重删/删不存在均 202；store 双后端（memory+mongo）同语义矩阵 |
| 7 | web 删除按钮真链路 | **通过** | L5 走查：侧栏删除 → 服务端 snapshot 410 + 新消息 410 + 刷新不复活（截图 sd-l5-after-delete-refresh.png） |
| 8 | 全量回归零破坏 | **通过** | verify-all 六档 PASS（E2E-27/28 已并入四个 gate 变体）；agent 423 / session 190 / web 175 |

## 走查实抓并当场修复的缺陷

```text
CORS 预检未放行 DELETE（allow-methods 只有 GET,POST,OPTIONS）——curl/单测均测不出，
浏览器真链路首击即现：删除请求被预检拦下、服务端毫无感知。已修（放行 DELETE）
并加预检回归钉（SD-S2 内断言 allow-methods 含 DELETE）。这条是 L5 层存在价值的
直接证据：HTTP 面变更必须过一次真浏览器。
```

## 已知边界（如实入册，非本轮范围）

```text
- web DELETE 为 fire-and-forget：请求丢失时服务端残留软删前状态；对账随 P1
  会话列表服务端化（规格 §4 已注）。
- 无鉴权：任何可达者可删任意会话——P1 鉴权主线统一收口（owner 裁权）。
- 恢复入口（deleted 翻回）未做 UI/端点：数据已保留，产品需要时是一次小增量。
```

## 结论

**验收通过。** 会话软删除按裁定形态（状态位 + agent 零改动）完整闭环：
契约、session、web、测试矩阵（L1×3 + L2 双场景 + L5 走查存证）、两份报告齐备。
