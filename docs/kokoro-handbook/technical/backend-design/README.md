# 后端逐仓库设计卡

这些文件是当前 Feature-first 总体架构的执行级拆分。每张设计卡只回答一个仓库的真实边界，不是通用模板；Agent/Session 的
产品会话与 GA owner 以 [36 GA 整体方案](../36-ga-final-agent-technical-plan.md) 和
[38 公共运行契约](../38-ga-public-runtime-contract.md) 为准。

## 当前目标仓库

```text
00-root.md
01-iam.md
02-model.md
03-credit.md (migration history)
04-payment.md (migration history)
05-billing.md
05-capability.md
06-storage.md
08-session.md
09-agent.md
10-design-audit.md
```

机器可校验清单：`backend-design-manifest.json`。`07-chat.md` 是历史独立分仓提案，保留考古，不进入目标仓库清单。

```bash
python3 scripts/verify-backend-design.py
```

除 manifest 完整性外，该命令还校验 Agent 的 100 分设计卡章节、专项方案的执行/owner/
迁移验收章节、真实 source tree、文档相对链接，以及历史 Agent 文档到当前权威入口的
authority-routing 标记。

## 设计卡统一审查项

每张卡都必须明确：

```text
职责 / 不负责
业务模块和领域复杂度
数据 owner / runtime writer
入口和公开契约
依赖方向
目标目录
测试边界
当前证据 / 迁移步骤
```

设计卡的 100 分是设计完整度目标；实现是否达到 100 分，必须由 schema、contract、architecture test、integration test 和旧入口删除证据确认。
