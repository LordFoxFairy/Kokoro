# API、RPC 与错误契约规范

状态：当前补充，2026-09-04。目录和运行时类型实现分别见 [TS](08-typescript-backend-engineering.md) 与 [Python](09-python-backend-engineering.md) 手册。

## 1. 契约所有权

- 本仓 owner 维护机器契约、生成链、测试和版本；Root 只聚合门户，不复制可编辑字段来源。
- BFF public HTTP 使用 design-first OpenAPI；内部 HTTP 可使用 schema code-first 生成只读 OpenAPI；RPC 使用 Proto。
- 先证明生成链覆盖字段、错误和序列化，再开始实现。生成物记录来源、版本和 digest，不手改。
- 每条 operation 明确 owner、visibility、stability、permission、idempotency；operationId 稳定唯一。
- 消费方在自己的 client 边界解析/映射 wire 类型；业务代码不依赖 generated message、数据库 Row 或 provider SDK。

## 2. HTTP 资源与协议

- 路径显式 `/v1`，集合用名词；真实动作使用有业务含义的操作，不设计任意表 CRUD 或万能 command-executor。
- 字段使用 `snake_case`；缺失、null、空数组、空字符串语义分别定义。PATCH 只允许字段白名单，并区分不修改与清空。
- 成功 JSON：`{ "data": ..., "meta": { "request_id": "..." } }`。
- 错误 JSON：`{ "error": { "code": "...", "message": "...", "details": ... }, "meta": { "request_id": "..." } }`，details 可省略。
- SSE/AG-UI、文件下载、HEAD 和 204 无正文按对应协议处理，不强加 JSON envelope。
- 根据实际语义选择 200/201/202/204；202 明确状态查询、终态、取消与失败结果。201 按契约提供资源标识/Location。
- 列表声明 limit 上下界、不透明 cursor、稳定排序和下一页位置；cursor 校验查询条件和授权范围，不视为权限凭据。
- 时间 instant 使用 RFC 3339 UTC；money/bigint 明确单位、精度和字符串序列化，不依赖隐式 JSON 转换。
- 查询可能受更新影响时说明分页一致性，别宣称 cursor 自动获得快照隔离。

## 3. 身份、并发与错误

- tenant/actor/service identity 来自验证后的上下文，body 和任意 header 不自报可信身份。
- 身份认证与业务授权分别实施；列表、批量、搜索、更新和删除均验证 tenant/资源范围。
- 资源存在性敏感时统一使用不可见的 404 等契约，不通过差异响应泄漏其他租户对象。
- 冲突、前置条件失败、限流、依赖故障和未知异常使用稳定机器码；message 不作为分支条件。
- 错误 details 只包含允许公开的结构；不公开 SQL、异常堆栈、secret、请求原文或 provider 内部消息。
- ETag/If-Match、版本比较或条件写只在真实并发需求时使用；具体冲突状态码固定。
- 具备外部副作用且可被重试的操作声明幂等身份、digest、保留窗口和结果重放；自然幂等操作不机械引入 receipt。
- CORS 不是身份验证；同源 cookie 写操作有 CSRF 防护。限流按身份、操作成本和资源预算设计，429 声明 Retry-After。

## 4. RPC 与消息

- 设置 deadline、取消、响应大小和有限重试；只对已证明可重试的操作自动重试。
- 受信服务上下文通过明确 metadata 传递，校验调用方身份，不把普通业务 ID 当身份凭据。
- 事件定义 producer/consumer、schema version、ordering key、delivery、重复、replay、retention 和失败处理。
- 消费方通过 owner 的固定版本 artifact/生成 client 集成；generated 类型在 client/handler 终止，不穿透内部模型。
- command/query 是读写语义，不要求为每个接口创建 Command class、Query class 或 CQRS bus。

## 5. 变更与验收

首发 clean-slate 按当前目标契约替换旧实现。对外稳定发布后的 breaking change 必须重新评审版本、弃用和消费者切换，
不把当前开发阶段的“无兼容层”无限推广到已有公开客户的服务。

每次变更同时验证：schema lint、生成 drift、breaking baseline、示例、成功/错误响应、权限、分页、幂等和适用的事件恢复。
技术方案、API 契约和数据文档先一致，再推进子仓实现；详见 Root AGENTS 的文档门。
