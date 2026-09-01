# Billing CI 与迁移门禁

## CI 必须证明

1. `pnpm install --frozen-lockfile` 可复现；
2. `pnpm lint`、`pnpm typecheck`、`pnpm build` 通过；`dist/src` 与 `dist/scripts` 可运行，并能使用不携带 secrets、测试文件和 `node_modules` 的 Docker context 构建 image；
3. MySQL 8.4 上所有 numbered migration 可重复执行且 checksum 稳定；
4. 真实 MySQL integration 覆盖 settlement、fulfillment、reversal、usage、checkout、webhook、admin、reconcile、outbox；
5. 真实 Redis integration 覆盖幂等 hint；
6. OpenAPI 可解析，且实现路由与 OpenAPI route parity 检查通过；`git diff --check` 通过；根仓库另行校验
   migration manifest、Kubernetes 和 Compose composition；
7. Billing bootstrap 使用显式 `ALLOW_BILLING_SEED=true`、稳定 JSON 摘要和 MySQL command receipt，重复执行不得
   生成第二个 revision；
8. GitHub Actions 权限最小化，第三方 action 固定完整 commit SHA。

Billing CI 不依赖根仓库的 `../docs`、`../deploy` 或 Compose 文件，因此可以作为独立子仓库直接 checkout 和运行。
本地子仓库的实现验收止于上述代码、schema、contract 和真实依赖测试；writer 切换门禁不因本地测试通过而自动勾选。
部署编排、旧库 source connection、shadow 观察窗口和 operator sign-off 是独立的发布阶段证据。

迁移 runner 在 MySQL 上使用 `GET_LOCK('kokoro-billing:migrations', 30)` 串行化并发发布；DDL 仍遵循 MySQL
隐式提交语义，checksum 表用于检测人工修改，失败发布必须由 operator 按 runbook 复核后继续。

## writer 切换门禁

- [ ] `kokoro-billing` schema owner inventory 与实际 writer 一致；
- [ ] Payment/Credit 旧 writer 双读对账连续通过；
- [ ] purchase、refund、usage、webhook 重放无重复事实；
- [ ] unknown provider/payment exposure 有 reconcile report；
- [ ] 所有消费者已切到 Billing contract；
- [ ] 旧跨仓 grant/reverse client 已停止写入；
- [ ] 可回滚窗口内保留旧只读查询，禁止旧 writer 恢复写入；
- [ ] CI、migration、observability、runbook 和 owner rotation 完成评审。
