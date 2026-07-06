# 验收报告：Skills V2（V2-M1）

- 日期：2026-07-06
- 规格：`technical/15` §2；实现注记 `technical/11`（2026-07-06 Skills V2 条）
- 姊妹篇：`m1-skills-v2-test-report.md`

## 验收判据 vs 结果

| # | 判据（来自 §2.2/§2.3） | 结果 | 证据 |
|---|---|---|---|
| 1 | S1 资产规范升级：frontmatter 必填校验、整包装载、装载期 fail-loud | **通过** | 五连负例 + 整包/辅助文件用例 + s3 minio 实测 |
| 2 | S2 供给器：state 档 invoke files（FileData 官方口径）/ 真实 backend upload_files，幂等 | **通过** | 供给器矩阵三用例 + supervisor 首 invoke 注入接线 |
| 3 | S3 消费切换：原生 SkillsMiddleware 渐进披露，V1 全文注入全删不留兼容层 | **通过** | 渐进披露真图断言（description 在 / 正文哨兵不在）；render_prompt/compose skills 段已删除 |
| 4 | 子代理同机制（入口对偶性保持，授权面前缀隔离） | **通过** | SubAgent.skills 源路径用例 + 前缀隔离断言（主见不到子代理专属包） |
| 5 | 32k/skill 上限问题消解（多 skill 不再膨胀 prompt） | **通过** | 上限代码删除；prompt 只挂 name+description（结构性消解） |
| 6 | 跨栈闭环：契约 `runtime.skills` 语义不变，session/web 零改动 | **通过** | session 190 / web 175 原样全绿；E2E-29 三断言 |
| 7 | 能力供给不污染用户文件面 | **通过** | /.skills 点前缀：snapshot.files 排除断言（E2E-29）+ S3 归档隐藏目录跳过（既有语义） |
| 8 | 全量回归零破坏 | **通过** | agent 430 + verify-all 六档 PASS（含 s3/docker/docker+s3 组合档） |

## 范围裁定记录

```text
S4（personas 迁出 assets/）缓行：装载面归源、消费面已在工厂层，目录搬迁无行为
收益——随 platform 配置管理主线归位（不算未完成项，属显式裁定）。
RM-D 真模型复核挂起在"--real 走钱"既有约定上，夹具已就绪。
```

## 结论

**验收通过。** Skills V2 按三层架构完整落地：用户点破的"assets 平行造轮子"
已根治——消费面回归 deepagents 原生渐进披露，供给面按 backend 档位统一物化，
分发面保留 local/s3 单源。M1 全部工程项（会话软删除 + Skills V2）至此收口；
M1 剩余审计遗留四件（fencing/sandbox teardown/steer 原子/409 对账）单独排期。
