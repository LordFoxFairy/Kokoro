# Legacy contract material

`contract/legacy/` 只保存已废弃拓扑的历史资料和兼容性遗留。这里的名称、Proto、fixture
和旧数据形状用于迁移考古、兼容性回归或解释历史边界，不是新功能的实现入口，也不是当前
owner 注册表。

## 已废弃或遗留的仓库名称

| 名称 | 当前含义 |
|---|---|
| `kokoro-credit` | 已废弃的独立仓库名称。Credit 事实和当前生产 API 的 owner 是 `kokoro-billing`，不再创建独立 Credit owner。 |
| `kokoro-session` | 已退出当前拓扑的历史 Session 仓库名称。Chat/session 的对外业务投影属于 `kokoro-bff`，执行事实属于 `kokoro-agent`。 |
| `kokoro-gateway` | 已废弃或仅作兼容性遗留的 Gateway 名称，不是当前业务入口或新的 owner。 |
| `kokoro-platform` | 迁移期保留的平台父仓名称，属于历史/兼容性遗留，不再承载新的业务域。 |
| `kokoro-web` | 旧 Web monorepo 名称，已退出当前仓库拓扑。 |

## Credit 事实归属

Credit 的唯一事实 owner 是 `kokoro-billing`。当前实现、API 和数据一致性边界以
`kokoro-billing` 的 owner contract 为准；历史 `kokoro-credit` 资料只能作为迁移或兼容性
证据，不能重新解释为独立运行仓库或数据库 owner。

## Proto 与 fixture 使用规则

历史 Proto、fixture、快照和旧路径只用于兼容性检查、回归测试和迁移参考。它们不是新功能的
权威契约，也不能据此新增 owner、路由、环境变量或持久化边界。当前跨仓 wire authority
登记在 [`goal2-cross-repository-contract-v1.json`](../goal2-cross-repository-contract-v1.json)，
其 Root 用途和 owner 关系由上层的
[`goal2-repository-contract-manifest.json`](../goal2-repository-contract-manifest.json)
统一索引；各正式业务仓再维护自己的 API/config projection。
