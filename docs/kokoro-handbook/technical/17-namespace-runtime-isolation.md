# Namespace 运行时隔离

状态：**历史实现说明**，2026-07-07 修订；不作为 Feature-first GA target 输入。
范围：旧 kokoro-web / kokoro-session / kokoro-agent / capability hub namespace 链路

> **目标架构更正（2026-08-23）**：外部 Browser、Session、IAM caller 不再向 GA 传递 `namespace`。
> 上游只提交服务端构造的 `ExecutionIdentity(tenant_ref, actor, subject, identity_assertion_ref)`，GA ingress 使用
> `RuntimeIdentityResolver` 派生内部、不透明 `RuntimeNamespace`。目标 request、recovery、cleanup 与 owner recheck
> 以 [GA 公共运行契约](38-ga-public-runtime-contract.md) 和
> [ADR-022](../decisions/ADR-022-run-execution-attestation-and-dynamic-capability-resolution.md) 为准；本文件以下内容仅解释 V1
> `session.namespace/context.namespace` 的旧实现记录。

## V1 基线结论（不是目标 contract）

GA 侧只认 `namespace`。

`ownerId`、`userId`、邮箱、OAuth subject、siteId、team、workspace 都是 web / session /
platform 的上游身份或业务语义。它们可以用于登录、鉴权、裁权、计费和 UI 展示，但不能作为
第二条身份轴进入 GA。

platform/user 侧不把这个值叫 namespace。正式业务概念是 `principalId`：全局唯一运行主体 id。
人、team、未来 workspace/org 都是 principal。`kokoro-session` 接收 `principalId` 后, 在自己的
运行时模型里持久化为 `session.namespace`；GA 仍只看到 `context.namespace`。

```text
web / platform:
  user, team, site, membership, auth policy, principalId
        |
        v
kokoro-session:
  persist session.namespace = principalId
        |
        v
kokoro-agent:
  context.namespace only
```

## 命名规则

namespace 是 opaque 空间 id，不加业务前缀。它的值来自 platform/user 分配的 `principalId`。

允许：

```text
namespace = principal.id   # personal principal / team principal / future workspace principal
namespace = local-user   # dev passthrough
```

禁止：

```text
user:<ownerId>
team:<teamId>
site:<siteId>:user:<userId>
GA contract userId / ownerId / workspaceId helper fields
```

如果未来要支持团队空间，仍由 platform/user 选择对应的 `principalId` 并校验 membership。
GA 不需要知道这个 namespace 代表用户、团队还是未来 workspace。

## principalId 来源

`principalId` 属于 platform/user 边界，不属于 GA，也不由 kokoro-session 分配。

建议的最小模型：

```text
Principal
  id        全局唯一主体 id，例如 prn_xxx
  kind      user | team | workspace
  ref_id    user.id / team.id / workspace.id
  site_id   所属 site，用于平台治理和查询，不进入 GA
  status
  created_at
  updated_at
```

V1 暂时没有 team，也按这个模型走：

```text
User.personal_principal_id -> Principal.id
VerifiedSessionContext.principalId = User.personal_principal_id
session.namespace = principalId
```

后续 team 只是在创建 session 时换一个 principal：

```text
Team.principal_id -> Principal.id
VerifiedSessionContext.principalId = Team.principal_id
session.namespace = principalId
```

session 和 GA 的核心模型不需要变化。

## siteId 与 namespace 的关系

`siteId` 是平台业务隔离边界：多站点、套餐、模型可见性、支付、credit、SEO 和后台权限都按
siteId 或 SiteContext 管。

`namespace` 是 GA/runtime 隔离边界：checkpoint、memory、skills、sandbox、workspace 文件和
capability resolve 都按 namespace 管。

二者是不同层级：

```text
siteId     平台业务域和产品站点
namespace 运行时工作空间和能力空间
```

不能把 siteId 当 namespace，也不能把 namespace 当 siteId。

## session 责任

session 是 namespace 进入 GA 的唯一闸门：

- 从已验证的会话上下文读取 `{ ownerId, principalId }`。
- 创建 session 时持久化 `session.namespace`。
- 构造 `RunRequest.context.namespace`。
- workspace list/read 使用 `session.namespace + sessionId`。
- snapshot 可以不向 web 暴露 namespace；web 只需要鉴权后的文件和产物投影。
- 不再让实例级 `KOKORO_NAMESPACE` 充当多用户运行时身份。

传输格式不进入业务模型：`principalId` 可以由内部 header、JWS/JWT、HMAC assertion 或服务内调用
携带。无论使用哪种载体，session 看到的都应该是已验证后的 `{ ownerId, principalId }`，而不是
把 JWT `sub` 当正式业务概念扩散。

## agent 责任

agent 只消费 namespace：

- `RunScope.namespace`
- checkpoint scoped thread id
- memory scope
- skill/capability resolve
- sandbox/workspace 归档前缀

agent 不判断 owner/user/team/site，不直接查询用户主数据，不扣积分。

## capability hub 责任

skill / mcp / subagent 共用一个 capability registry 骨架：

- namespace 归属
- per-namespace 启用态
- 官方/自定义/共享 grant
- 版本、审核、配额
- resolve 读模型

delivery 按 kind 分开：

```text
skill     文件包, agent 读对象存储后上传进沙箱
mcp       活连接和授权, agent 运行时建连接
subagent  定义, agent 编译 graph 时装配
```

## 验收

- 代码搜索不存在 `user:<` namespace 拼接。
- GA 契约没有 `userId` / `ownerId` / `workspaceId` 作为隔离字段。
- 两个 namespace 的 checkpoint、memory、workspace、skills 不串。
- session 刷新和 relay recover 后仍能拿到原 session namespace。
- platform/user 能返回全局唯一 `principalId`; user/team 不会因为不同表 id 碰撞而污染 namespace。
- 外部参考来源只在 tmp 中间产物出现，不进入正式文档或代码。
