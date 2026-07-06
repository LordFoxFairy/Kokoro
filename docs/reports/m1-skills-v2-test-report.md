# 测试报告：Skills V2（V2-M1）

- 日期：2026-07-06
- 规格：`technical/15-v2-technical-plan.md` §2（分发→供给→消费三层）
- 范围：agent 仓（assets 整包装载 + frontmatter 契约 + 供给器 + 原生渐进披露消费）；
  契约/session/web 零改动（`runtime.skills` 语义不变=授权名单）

## 执行汇总

| 层 | 套件 | 结果 |
|---|---|---|
| L1 agent | `uv run pytest`（430 条，净增 7） | **430 passed** |
| 静态 | ruff / pyright / mypy | 全 0 error |
| L2 跨栈 | `scripts/e2e-v21-gate.py`（37 断言，新增 E2E-29×3） | **PASS** |
| L2-L3 全量 | `scripts/verify-all.py` 六档 | 见验收报告（终局复跑） |
| session/web 回归 | 190 / 175 | 全绿（零改动确认） |

## 新增/改写用例明细（全部通过）

```text
S1 frontmatter 契约
  整包装载（SKILL.md+辅助文件，description 提取）                        PASS
  负例五连：无头/未闭合/name 与目录不符/空 description/缺 name           PASS×5
  快照语义（装载后盘改不外泄）/缺 SKILL.md fail-loud/未知名 fail-loud    PASS×3
  s3 源整包装载 + 缺 SKILL.md 负例 + 端到端库装配（minio 实测）          PASS×3
S2 供给器
  state 档：initial_files=FileData 口径 + 主/子代理前缀隔离 + 整包供给   PASS
  真实 backend：upload_files 调用面 + initial_files 恒空                 PASS
  未知授权名 fail-loud                                                   PASS
S3 消费切换
  渐进披露真图：system prompt 含 description、不含正文哨兵、人格保留     PASS
  子代理挂原生源路径（SubAgent.skills=/.skills/sub-<name>/）             PASS
E2E-29（跨栈）
  namespace 授权 → run 工作区 /.skills/main/<name>/SKILL.md 整包物化     PASS
  供给内容=资产整包（正文哨兵在盘）                                      PASS
  点前缀不进 snapshot.files（能力供给≠用户产物）                         PASS
```

## 诚实记录

```text
- RM-D（真模型遵循 skill）语义由"全文在 prompt"变为"按需 read_file"，夹具已带
  frontmatter；真栈行为待下次 --real 复核（走钱场景，按既有约定不在本轮自动跑）。
- S4（personas 迁出 assets/）缓行：纯目录搬迁无行为收益，随 platform 配置管理
  主线归位（technical/11 注记入册）。
- e2e gate 首跑抓到一次脚本自身缺陷（profile 授权替换因缩进静默落空致 E2E-29 红），
  修正后全绿——按"断言先红后绿"如实记录。
```
