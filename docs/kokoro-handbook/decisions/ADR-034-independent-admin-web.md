# ADR-034：独立 Admin 前端工程，复用 Product 登录与会话

- 初始决定：2026-10-09；认证边界纠正：2026-10-23。
- 状态：Accepted；Task A认证切换及共享登录范围已验（2026-11-11），不表示全部Admin业务或部署验收完成。本文替代独立 OAuth client、回调与 cookie/session namespace 决定。
- 范围：同一 Kokoro 产品的 Admin 前端工程与公开入口，不增加身份服务或业务 owner。

## 当前认证边界

IAM 唯一拥有原生登录 Cookie、数据库 Session与续期，BFF负责认证边缘，App负责同源薄adapter；Admin不另建认证。普通业务使用直接服务身份＋本次入口取得的可信actor，账户会话管理保留专用Cookie／Origin例外，不恢复请求内Session引用设计。详细边界见[当前技术总览](../technical/00-system-overview.md#3-原生登录与内部调用)。

## 决定

1. 后台可以独立构建、启动和部署，但与 App 属于同一产品与身份体系。当前正式工程是 `apps/kokoro-admin`，不是新增 `apps/kokoro-admin-web`。工程边界不推导出第二套登录、OAuth client、用户会话或授权中心。
2. IAM 是原生登录 Cookie、Session、CSRF与续期事实 owner；BFF是认证边缘，App提供同源adapter。Admin薄消费现有Product会话接口及管理员准入投影，不自行签发 cookie、保管 refresh token、实现 OAuth callback 或创建独立 session 存储。
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

Task A正式组合已验证原生登录／退出／撤权、共享Admin准入和负控；当前Admin #5已合main。工程源码、原生浏览器与所有管理CRUD是不同范围，不扩大为全部后台功能通过。当前证据边界见[技术总览](../technical/00-system-overview.md#7-已验范围与仍保留的限制)和[CURRENT](../../CURRENT.md)。

## 历史决定为何被替代

旧版把“独立前端工程”扩大为独立 OAuth client、redirect origin 和 cookie/session namespace，并要求后台另行登录。这超出了用户对同一产品的边界要求，与已采用的 Product 会话消费者实现冲突，现明确废止，不再用于实施或部署。

旧 `var/dev/admin-web-release` 简化壳仍只作考古材料；现有正式 Admin 模块是唯一迁移和维护基座。历史实现状态和端口探测不作为当前运行证据。
