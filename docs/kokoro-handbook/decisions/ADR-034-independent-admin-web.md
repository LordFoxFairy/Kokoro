# ADR-034：独立 Admin 前端工程，复用 Product 登录与会话

- 初始决定：2026-10-09；认证边界纠正：2026-10-23。
- 状态：用户已确认。本文替代旧版中独立 OAuth client、回调与 cookie/session namespace 的决定；不表示正常环境整链验收完成。
- 范围：同一 Kokoro 产品的 Admin 前端工程与公开入口，不增加身份服务或业务 owner。

## 决定

1. 后台可以独立构建、启动和部署，但与 App 属于同一产品与身份体系。当前正式工程是 `apps/kokoro-admin`，不是新增 `apps/kokoro-admin-web`。工程边界不推导出第二套登录、OAuth client、用户会话或授权中心。
2. Product 是唯一浏览器登录、会话、CSRF 与续期 owner，IAM 是身份与权限事实 owner。Admin 薄消费现有 Product 会话接口及管理员准入投影，不自行签发 cookie、保管 refresh token、实现 OAuth callback 或创建独立 session 存储。
3. 当前公开入口为 Product 同源 `/manage`，由 App 同源 adapter 接入独立 Admin 进程。内部监听地址不是第二个公开产品入口；地址由受信部署配置提供，不从 query/body 决定。将来使用子域名须验证 cookie、CSRF、重定向与代理边界，不将“配置子域名”当作会话自动可用的证明，也不因此另建认证体系。
4. Admin 通过现有 same-origin adapter、App 管理 adapter 与 BFF 访问业务 owner；没有 Admin 专属 BFF 或业务数据库。不相对导入 sibling 源码，不复制可编辑 owner contract。业务请求继续消费精确固定的 owner/BFF 契约。
5. 登录状态不等于管理权限。服务端明确取得当前管理员准入后才渲染控制台业务内容；普通用户与跨租户请求仍拒绝。可恢复会话沿 Product 既有流程处理，依赖故障与明确无权限分开，不把身份未知当成管理员、不把服务故障伪装成退出登录。
6. 保留既有 Ant 管理模块、模型配置、Skills/MCP 管理的真实能力，不另造简化壳。读取保留取消、迟到响应隔离；写入保留 fresh authorization、幂等、CAS 和未知结果恢复，不因续期自动重复业务提交。
7. 内部机器调用采用 [ADR-035](ADR-035-direct-internal-service-authentication.md) 的接收方直接服务认证，与 Product 人类登录分开。服务认证不替代用户权限或 Run 执行授权；客户端自报 tenant/user 标识不是受信身份。

## 删除与失败恢复

- 删除 Admin 独立登录、伪邮件确认页、OAuth callback、独立 CSRF/refresh/session 实现及专用旧配置；不保留 alias、fallback 或双轨认证。
- 管理页面恢复使用现有 Product session client；失败保留当前页面和显式重试，返回产品使用受信 Product 地址，不进入 Admin 私有端口的 `/app`。
- 401/403、会话竞争、依赖不可用和未知写入结果按现有契约分别处理；不循环导航、不重放未知 POST、不绕过权限 gate。
- 生产切换与发布仍遵循现有集成计划；本文不授权重启他人服务、清理共享数据或直接改 main。

## 验证与当前证据

验收覆盖：Product 登录后进入后台、后台深链及刷新、会话续期、多标签并发、退出后重新进入、撤权/普通用户/跨租户负控，以及后台真实操作与未知提交恢复。必须区分单元覆盖、隔离集成和正常浏览器结果。

当前 Admin `e35df2178905f35d3dbced3bea1e114663e9bfc7` 已删除 `/login` 与 `/auth/verify` 旧页面，并将 AppShell 限定在准入后的 console layout。源码 `lib/server/page-admission.ts` / `lib/server/product-admin-admission.ts` 消费 Product 管理员投影，未创建独立登录。该提交和正常页面的已验范围、首次热更异常及剩余登录旅程见 [CURRENT](../../CURRENT.md#admin-session-boundary-20261023)；不把局部通过称为完整登录闭环。

## 历史决定为何被替代

旧版把“独立前端工程”扩大为独立 OAuth client、redirect origin 和 cookie/session namespace，并要求后台另行登录。这超出了用户对同一产品的边界要求，与已采用的 Product 会话消费者实现冲突，现明确废止，不再用于实施或部署。

旧 `var/dev/admin-web-release` 简化壳仍只作考古材料；现有正式 Admin 模块是唯一迁移和维护基座。历史实现状态和端口探测不作为当前运行证据。
