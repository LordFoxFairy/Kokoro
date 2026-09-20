# Root 当前状态

状态：2026-09-19。Root 已采用 remote-name Git submodule 组合；当前可复现组合由 `.gitmodules` 与 gitlink SHA 定义，而不是同级 checkout 或工作目录约定。

## 当前事实

- Root 子仓路径严格使用远端仓名：Web 为 `apps/kokoro-app`，而非 `kokoro/`；Mori 为 `apps/kokoro-mori`；共享前端包为 `libs/kokoro-web-shared`。
- 九个正式 runtime owner 仍是 `kokoro-app`、BFF、Agent、IAM、System、Billing、Capability、Storage、Scheduler；Mori 是独立前端产品，web-shared 是独立版本化库。
- 每个 Root/submodule local 与 `origin` 只保留 `main`。Root 更新只提升已推送的子仓 SHA，`.gitmodules branch=main` 不构成发布锁。
- 子仓的 tests 不迁入 Root。Root `scripts/tests/` 只覆盖 Root 治理脚本；跨仓行为测试保留给 Root `verification/`，不重复子仓单测。

## 当前验证入口

```bash
python3 scripts/verify-repository-topology.py
python3 scripts/verify-main-only.py
python3 -m pytest scripts/tests
```

逐仓 lint/typecheck/test/build/schema/smoke 继续由各自 submodule 运行并以其 commit 为证据。Root 静态治理 PASS 不冒充 live owner、外部 provider、发布镜像或 SLO 验收。

## 未闭合项

1. `kokoro-capability` 到 `kokoro-platform` 的仓名、remote、数据库/Redis namespace 与消费者一次性 cutover 需要独立 ADR 和发布，不通过路径 alias 提前实现。
2. Root `verification/` 的跨仓 contract/integration/e2e/smoke runner 尚未重建；旧会清理共享基础设施的 runner 保持暂停。
3. 生产组合 tag、子仓 SHA、SDK 版本、image digest 和验证结果需要在首次正式组合发布时写入 release manifest。
