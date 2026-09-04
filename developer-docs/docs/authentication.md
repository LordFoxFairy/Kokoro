# 认证与服务上下文

Kokoro API v1 是 server-to-server Product API。调用方应由受信任的后端或同源服务端 adapter 发起；浏览器代码不持有 service credential，也不直接把 BFF 当作浏览器 API。

字段级认证事实来自 canonical OpenAPI 的 `securitySchemes` 和 operation `security`。除健康与就绪探针外，当前 public v1 使用四个 service-context header：

| Header | 作用 | 典型来源 |
| --- | --- | --- |
| `x-kokoro-service` | 标识被接纳的服务调用方 | 部署配置 |
| `x-kokoro-internal-secret` | 认证该服务调用方 | secret manager |
| `x-kokoro-namespace` | 选择受信任的产品作用域 | 服务端 session |
| `x-kokoro-principal-id` | 标识受信任的主体 | 服务端 session |

健康和就绪 operation 在 contract 中声明 `security: []`，因此不要求上述上下文。其他 operation 的准确 security requirement、header 名称和 response shape 以[生成 reference](/reference/v1/)为准。门户不会创造新的认证 header，也不会发布凭据值。

## 信任规则

- namespace 和 principal 必须从服务端认证状态推导，不能由浏览器 body 冒充。
- `Host`、`X-Domain`、`X-Forwarded-*`、tenant 或其他浏览器输入不是受信身份来源。
- share identifier 只选择共享资源，不替代服务认证。
- `scope` query 参数是过滤条件，不能改变已认证的身份范围。
- 四个上下文 header 都应从普通日志和 trace 中脱敏；示例里的值是故意虚假的 fixture 值。

## 事实源与当前边界

本页解释调用方式，不复制跨仓 DTO 或数据库结构。若 header、权限或 operation 的 metadata 发生变化，先由 BFF owner 更新 public contract，再更新 catalog、生成页和测试。当前 artifact 是唯一字段事实源；live adapter 的可用性仍需通过实际 health/ready 和 smoke 证据确认。
