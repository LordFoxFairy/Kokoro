# Namespace 运行时隔离

状态：2026-07-07 修订
范围：kokoro-web / kokoro-session / kokoro-agent / capability hub

## 结论

GA 侧只认 `namespace`。

`ownerId`、`userId`、邮箱、OAuth subject、siteId、team、workspace 都是 web / session /
platform 的上游身份或业务语义。它们可以用于登录、鉴权、裁权、计费和 UI 展示，但不能作为
第二条身份轴进入 GA。

```text
web / platform:
  user, team, site, membership, auth policy
        |
        v
kokoro-session:
  choose and persist namespace for this session/run
        |
        v
kokoro-agent:
  context.namespace only
```

## 命名规则

namespace 是 opaque 空间 id，不加业务前缀。

允许：

```text
namespace = kokoro-user User.id
namespace = future team/workspace namespace id
namespace = local-user   # dev passthrough
```

禁止：

```text
user:<ownerId>
team:<teamId>
site:<siteId>:user:<userId>
GA contract userId / ownerId / workspaceId helper fields
```

如果未来要支持团队空间，仍由 web/session/platform 选择一个 namespace id 并校验 membership。
GA 不需要知道这个 namespace 代表用户还是团队。

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

- 从认证上下文解析 `{ ownerId, namespace }`。
- 创建 session 时持久化 `session.namespace`。
- 构造 `RunRequest.context.namespace`。
- workspace list/read 使用 `session.namespace + sessionId`。
- snapshot 可以不向 web 暴露 namespace；web 只需要鉴权后的文件和产物投影。
- 不再让实例级 `KOKORO_NAMESPACE` 充当多用户运行时身份。

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
- 外部参考来源只在 tmp 中间产物出现，不进入正式文档或代码。
