# Developer API 门户地图

## Owner 与边界

门户只拥有展示、编排和验证。`kokoro-bff` 是 public Product API 的事实 owner；`developer-docs/catalog/contracts.yaml` 只记录版本化 artifact 的来源与 provenance。IAM、Agent、Storage、Scheduler 等 internal-owner contract、数据库 schema、ORM Entity、generated internal DTO、凭据和私有 payload 都不进入本目录的发布输入。

字段级事实只有一个来源：固定 commit 上的 BFF OpenAPI。`docs/` 中的手写说明是调用指导和当前状态说明；`docs/reference/v1/generated/` 是由脚本重建的只读产物，不是第二份 contract。

## 阅读入口

1. [`docs/introduction.md`](/introduction)：产品 API 边界、版本状态和异步模型。
2. [`docs/quickstart.md`](/quickstart)：服务端首次请求、receipt、SSE 和断线恢复。
3. [`docs/authentication.md`](/authentication)：四个 canonical service-context header 与信任边界。
4. [`docs/concepts/`](/concepts/projects)：资源、run、生命周期、AG-UI 和时间模型。
5. [`docs/guides/`](/guides/create-run)：可复制的创建、控制、分页、上传和恢复流程。
6. [`docs/platform/`](/platform/responses-errors)：响应、错误、幂等、重试、版本和安全。
7. [`docs/reference/v1/index.md`](/reference/v1/)：由 artifact 生成的 operation 与 schema 全量索引。
8. [`docs/provenance.md`](/provenance)：目录 pin、digest、来源 checkout 和验证证据。

## 目录职责

| 路径 | 职责 |
| --- | --- |
| `catalog/contracts.yaml` | owner、visibility、版本、commit、SHA-256、生成命令和发布分类。 |
| `docs/` | 中文手写入口、概念、指南、平台行为和变更记录。 |
| `docs/reference/v1/generated/` | 被忽略的生成参考页、schema 页和 manifest。 |
| `examples/` | 无真实凭据的 cURL、TypeScript、Python 示例，以及 fixture 运行描述。 |
| `scripts/` | provenance、引用生成、发布策略、示例、架构和链接门禁。 |
| `tests/` | 生成器、来源一致性、示例、输出安全、架构和构建链接测试。 |

## 发布门禁

- catalog 只接受 `kokoro-bff`、`public`、canonical v1 路径的 contract。
- provenance 将当前文件字节和 immutable Git blob 绑定到同一个 SHA-256；BFF 其他未涉及 canonical 文件的 dirty 状态会如实报告。
- 生成器拒绝错误的 owner、visibility、stability、idempotency、permission、security reference 和 `Idempotency-Key` 一致性。
- canonical 输入和最终生成树都经过 secret、危险 URL scheme、内部 owner 路径和未知 Kokoro header 发布策略。
- 架构检查拒绝复制的 OpenAPI、数据库 schema、内部 generated DTO、秘密字面量和跨仓 checkout 链接。
- 两次隔离生成必须逐字节一致；生成目录只能由受管路径替换。
- 示例通过 OpenAPI 请求体校验，并在本地无凭据 fixture 上实际执行。
- VitePress 构建后检查内部 route、fragment 和 asset link。

## 代码粒度例外

`scripts/lib/reference-generator.mjs` 暂时把 public contract 校验、递归 Markdown 渲染和 publication policy 调用保持在同一条确定性 pipeline 中，避免第二个 renderer 绕过来源白名单。当前文件低于 800 行阻断线；若引入第二个 contract 版本或输出格式，应按校验、模型遍历和渲染职责拆分，并同步更新 architecture test。

## 扩展规则

1. 先由 `kokoro-bff` 修改自己的 public contract；门户不手写同名字段作为替代来源。
2. owner contract 提交后，更新 catalog 的真实 commit 和 SHA-256，并运行 provenance。
3. 通过 generator 生成 operation/schema 参考；手写页面只添加链接和边界说明。
4. 新增示例必须声明 operationId、请求体和运行时，并使用 fixture 测试，不放真实 credential。
5. 运行 `corepack pnpm run ci`；失败项保持可见，不用 alias、双读或空测试消除差异。
6. 生成物、缓存、dist 和临时数据库不得提交；根仓及任何子仓的既有变更不在本专项范围内。
