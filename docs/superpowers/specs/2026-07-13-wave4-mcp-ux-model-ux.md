# Wave 4 · MCP-UX 与 MODEL-UX 子 spec(同 lane 串行:两项都是 web 竖切,web 单写者)

状态:执行稿(上级=总设计稿 §6 Wave4,已获批)。两项互不为前置,同 lane 只因 web 是单写者仓;
逐项独立 commit 独立验收,不合并派工语义。

## MCP-UX(依赖已齐:MCP-SECRET/MCP-REVISION/HUB-CONSIST 全落,mutation 门=env)

- **范围**:web 连接向导竖切——namespace MCP server 的注册/编辑/启停/软删 + secret handle 管理
  (创建/列表/删除,值只进不出)+ enabled pool 自动进新会话快照的可见化(会话创建后快照里能看到)。
- BFF:走既有 /api/hub 代理(web-bff 凭据+信封 scope);hub self 面 API 已全在(mcp servers CRUD
  现 503 门,dev/closure 置 KOKORO_HUB_MCP_MUTATION=on 后即真;secrets API 已开)。
- UI:MCP 管理页(暖纸族)——列表(official 只读徽标+namespace 自有);注册向导:name/transport/url/
  allowed_tools/secret 选择(下拉选既有 handle 或新建,value 输入即换 handle,绝不回显);启停/软删;
  hub 拒绝(env: 引用/私网 URL/http)的错误信封人话化。revision/config_hash 不暴露给用户(内部
  机制),仅"已更新"语义。
- 浏览器实走:注册一个真 MCP server(closure 的 fixture server)→ 新会话快照含它 → 停用 → 再新
  会话不含;secret handle 创建即用;负向:http URL 被拒的 UI 呈现。截图 wave4-mcp-*。

## MODEL-UX(M-1 后半的 UI 面)

- **范围**:web 模型选择竖切——输入框模型选择器从"只发 thinking 布尔"升级为真模型选择,
  wire `model` 字段(MessageCreateParams 已有 optional)带真实选择;候选来源=platform 单源。
- 候选读路径:先测绘现状(session profile.allowed 展示过滤+platform model-bindings resolve 权威,
  MODEL-SOURCE 已落)。实现取向:web BFF 读候选(经 session 或直连 platform model 读面,取决于现有
  读面;**若需要新的 session 端点上根契约,停手报主控冻结,不得自造**)。候选含 provider/name/
  可用性;不可用模型不出列表(resolve 权威)。
- UI:输入框模型下拉(当前选择高亮+thinking 开关保留);选择随首条消息定死会话(session 既有锁语义,
  后续消息不允许换→UI 锁定态)。
- 浏览器实走:选非缺省模型发首条→snapshot/run 记录该 model;第二条消息 UI 锁定;截图 wave4-model-*。

## 验收

逐项:web vitest/tsc/eslint 只增不减;浏览器实走+截图;hub/其他仓不改(发现缺口报主控);
全链 e2e 回归绿(gate 不加断言,E2E-33 已覆盖 MCP 链路)。
