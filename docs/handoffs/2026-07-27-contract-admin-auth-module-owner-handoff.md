# Contract / Admin Auth 模块并行交接

日期：2026-07-27

工作树：`/Users/nako/.config/superpowers/worktrees/Kokoro/feat/lordfoxfairy/wave-0-foundation`

根分支：`feat/lordfoxfairy/wave-0-foundation`

## 必读

1. `docs/CODEBASE_MAP.md`
2. `docs/CURRENT.md`
3. `docs/superpowers/specs/2026-07-27-contract-transport-and-internal-rpc-design.md`
4. `docs/superpowers/plans/2026-07-27-contract-foundation-admin-auth-pilot-implementation-plan.md`

## 已完成 Root 事实

| Commit | 内容 |
|---|---|
| `367c529` | Pin Buf 1.72.0、Protobuf-ES 2.13.0、pnpm 11.2.2 与 build allowlist |
| `0a3f30f` | Admin Auth v1 Proto、common error、command identity/receipt、Buf lock |
| `6383e2c` | 临时生成后 byte-compare 的 drift checker 与 Root CI gate |

验证：

- `uv run pytest contract/tests -q`：32 passed。
- `pnpm --dir contract run buf:format:check`：passed。
- `pnpm --dir contract run buf:lint`：passed。
- `node --test scripts/repository/*.test.mjs`：46 passed。
- `node scripts/repository/check-generated-contracts.mjs`：本地当前镜像一致。
- `git -C kokoro-agent diff --exit-code`：clean；未授权且未修改 GA。

## Platform owner

只写 `kokoro-platform`：

1. 先读并保留 `codex/admin-auth-rpc` 分支中的 store/domain 测试意图。
2. 修改 `.gitignore`，只允许提交 `kokoro-platform-admin/src/generated/contracts/**`，不要开放所有 generated 目录。
3. 添加精确 Connect/Protobuf/Validate 依赖与生成镜像。
4. 按计划 Task 5-7 先写 RED tests，再实现 workload/error interceptor、receipt migration、Admin Auth Connect service。
5. 删除手写 `admin-auth-rpc.ts`、路径和 contract-version header。
6. 运行 Platform 全测试/typecheck/lint，提交并 push 子仓分支。

禁止：修改 Root/Web/Session/Agent；把 Platform-local workflow 改 Connect；输出 secret；用 `db push` 替代迁移。

## Web owner

只写 `kokoro-web`：

1. 保留现有 Auth.js port/adapter 测试意图，丢弃 hand-written fetch/Zod transport。
2. 提交 `apps/admin/lib/generated/contracts/**` 并添加精确 Connect Node runtime 依赖。
3. 用生成 client 实现 server-only `AdminAuthClient`，完成 `auth.ts`、`events.ts` 注入。
4. 删除 Admin Web Prisma client/schema/scripts/dependencies 与 `DATABASE_URL_ADMIN`。
5. 运行 Admin tests/typecheck/lint/build，提交并 push 子仓分支。

禁止：修改 Root/Platform/Session/Agent；透明 catch-all 扩张；把 internal client 打入 browser bundle。

## Session owner

只写 `kokoro-session`：

1. 新建 `src/platform/admission-port.ts` 与相邻 `INDEX.md`。
2. 用 characterization RED tests 固定当前行为。
3. 把现有 Model/Credit/Hub 业务调用收敛进唯一 `legacy-admission-adapter.ts`。
4. 调用方只依赖 `PlatformAdmissionPort`；不新增协议、不宣称 remote atomicity。
5. 运行 Session tests/typecheck/lint，证明 `kokoro-agent` 无 diff，提交并 push 子仓分支。

禁止：修改 GA、改变 HTTP/SSE、把 `siteId/userId/ownerId/workspaceId` 传入 GA、接入尚不存在的 Admission Connect provider。

## Root owner 后续

1. 对每个子仓 commit 做 spec compliance review 和 code-quality review。
2. 在主工作树重跑全部 child verification，不采信 worker exit status。
3. 建 `platform-admin-auth` registry/scenario，运行真实 provider/consumer compatibility。
4. 更新精确 child pins、recoverable refs、gitlinks 和 BOM。
5. clean recursive clone 复验后再 push Root。

当前 Root CI 若使用旧 child pins，会因生成镜像缺失而失败；这是有意的 promotion gate，不能删除或放宽。
