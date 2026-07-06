# 验收报告（含测试明细）：M1 审计遗留四件

- 日期：2026-07-06
- 上游：technical/15 §1 审计清单（agent 闭环①B/③/④、跨栈④）
- 本报告合并测试明细与验收判据（四件均为点状加固，单独成对报告价值低）

## 验收判据 vs 结果

| # | 缺口（审计原文） | 修复形态 | 结果 | 证据 |
|---|---|---|---|---|
| 1 | 裂脑：假死副本被重拾后双跑，副作用工具可能双执行 | 租约 owner 维度 + renew 严格属主 + 心跳失权即让渡（不发终态）+ resume adopt 交接 | **通过** | 矩阵项 owner_fencing（sqlite/mongo 同语义）+ supervisor 让渡测试（无终态旁发）；诚实边界：双跑窗=一个心跳周期（工具级 fencing 不引入） |
| 2 | 沙箱零主动销毁，终态后容器活到 TTL | 终态统一漏斗挂 teardown（docker rm -f / e2b kill，尽力而为） | **通过** | 漏斗测试（kind+sandbox_id 透传）；失败回落 TTL 自清（原兜底保留） |
| 3 | steer 排空与 checkpoint 非原子，窄窗丢插话 | drain→peek + 下一轮见证 ack（落定才删，稳定 id 去重重注入） | **通过** | 矩阵 steer_mailbox 重写（peek 非破坏/精确 ack/重复 ack 幂等）+ 真图见证测试（不重复注入且清箱） |
| 4 | web resume 撞 409 卡死 awaiting-hitl | 终态冲突码触发 snapshot 对账（清暂存+重建）；网络错保留重试语义 | **通过** | 对账用例 + 不回归用例（web 176） |
| 5 | 全量回归零破坏 | — | **通过** | verify-all 六档 PASS（chaos 直压租约/收养/fencing 路径）；agent 434 / session 190 / web 176；静态全 0 |

## 诚实边界（入册）

```text
fencing 粒度=心跳周期：失权后至下一拍心跳前的窗口内仍可能双执行一段
（工具级 fencing token 属过度设计，暂不引入——终态单一性由原子认领兜底）。
steer 信箱在"注入轮即终态"时留残条（无下一轮见证），随 run TTL 清扫，不丢不重。
custom backend 的终态回收归 BYO 作者（升级路径已注：工厂返回 teardown 钩子）。
```

## 结论

**验收通过。V2-M1 全部四大项（会话软删除 / Skills V2 / 审计遗留加固 / 全量马具扩展）交付完毕。**
