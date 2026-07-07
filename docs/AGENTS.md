# docs/ agent 规则

本目录文件很多。Agent 进入 `docs/` 时不要递归读取全量目录。

默认阅读顺序：

1. `docs/CODEBASE_MAP.md`
2. `docs/README.md`
3. `docs/CURRENT.md`
4. 当前任务点名的具体文档

除非用户明确要求考古或迁移历史资料，否则不要主动展开这些目录：

```text
docs/product/
docs/prototypes/
docs/research/
docs/brainstorm/
docs/plans/
docs/superpowers/plans/
```

`docs/superpowers/specs/` 是过程方案池，只按日期/主题打开当前任务需要的文件。

`docs/kokoro-handbook/` 是稳定权威入口，但也不要整目录扫读；从
`docs/kokoro-handbook/README.md` 进入，再打开相关模块。

如果文档之间冲突：

```text
docs/kokoro-handbook/        正式技术方案和已确认长期规则优先级最高
docs/CURRENT.md              当前活跃白名单
docs/superpowers/specs/      草案/过程方案，正式后应迁入 handbook
docs/handoffs/               短期派工
历史 product/prototype/research 仅作背景
```

namespace 规则不得从旧文档推断：

```text
GA 只认 opaque namespace。
namespace 不拼 user:/team: 前缀。
GA 不接收 userId / ownerId / workspaceId 第二身份轴。
```
