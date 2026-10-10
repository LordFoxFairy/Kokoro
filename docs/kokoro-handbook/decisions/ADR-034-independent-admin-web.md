# ADR-034：独立 Admin Web，复用现有 BFF 权限与业务边界

状态：目标决策已采纳，2026-10-09；实现、远端登记及 cutover 尚未完成。

## 当前实现纠偏（2026-10-10）

此前在 `var/dev/admin-web-release` 从零拼出一个简化后台壳，未迁用既有管理面的模型路由、Skills 管理、权限 gate 或布局。用户明确拒绝该方向：它不具备替代既有 Admin Web 的资格。该进程已停止；该工作目录和提交只作迁移考古，禁止再将其作为产品后台、`/manage` 入口或新增模块的基座。

当前可验证的既有管理实现位于活跃 Web 的 `src/app/admin/`：`page.tsx` 保持 server-side `platform_admin` gate，`admin-access-view.tsx` 组装模型路由和 Skills 管理模块。下一阶段必须先盘点并复用这一现有实现；若独立项目确为用户要求，则先恢复可验证的历史 Admin 源码或完成从这一实现的受控迁移设计，再建正式独立交付物。不得继续从简化壳重写。

## 当前证据与纠偏

用户明确要求后台为单独 Web 项目。历史 Wave5 的 `kokoro-admin-web` 位于退休 `kokoro-platform` 子仓，不是用户 Web 路由。最后可核 Root pin 为 `d30a16a782aca0fe131acbe8cbfbbd63fdf1b989`，Root `47ad74b8675c87d34af3d8b872bd7ec64e67a229` 删除旧 gitlink；本地没有对应 child 对象，不声明旧源码已恢复。`623c012f` 仅移除退休 Root 契约，不是旧 UI 源码删除证据。

当前 Web 正式 `d3cacda2db75ba2d8271f5289f5ea75e53967d2a` 的 `/admin`、`/admin/settings` 与用户页面共享项目、构建和 session。因此仅独立布局不满足用户要求；历史“独立后台”验收描述不得作为独立项目证据。

## 决定

1. 独立 consumer 仓唯一名称 `kokoro-admin-web`，独立构建、启动、发布、OAuth client、redirect origin、cookie/session namespace。拟正式组合路径 `apps/kokoro-admin-web`；进入 gitlink 前必须具备可获取的正式 remote 和精确 commit，沿 ADR-032，不先伪造 remote 或注册目录。
2. 先完成既有 Admin 源码与模块盘点，明确可恢复的历史源码或现有 `/admin` 迁移基座、模块边界、测试和删除清单。禁止以新的简化页面代替迁移；`var/dev/admin-web-release` 仅保留考古证据，不是可继续扩写的迁移基线。
3. 独立 frontend 不增加业务事实 owner。调用固定 `Admin Browser → Admin Web same-origin adapter → BFF → IAM/Platform/System`。不增加 Admin BFF、业务数据库、通用 manifest mutation gateway，不恢复退休 `kokoro-platform-admin`。
4. 迁用当前 Skills 和模型路由管理行为，但不相对导入用户 Web，不复制可编辑 owner contract。消费现 BFF 固定 commit/digest 的生成产物；写入保持 fresh action 授权、幂等、CAS、unknown 同 intent 恢复和 canonical 回读。
5. 本地默认候选端口 3320，本轮 lsof 无 listener；最终启动前再次检查。入口为可信部署配置 `KOKORO_ADMIN_WEB_ORIGIN`，不是 query/body 自报地址。IAM 注册独立客户端及 redirect/post-logout URI 后才跑登录；不搬运 3310 cookie 或用 machine token 替代人类身份。
6. 用户 Settings 只为可信平台管理员显示外部后台链接；Admin Web 直达独立登录及 fresh gate。普通用户、跨 tenant、撤权和迟到响应必须拒绝。当前开发账号授予 platform_admin 已获用户授权但尚未执行，不能据此冒称已是管理员。
7. 发布窗口一次 cutover：独立后台实际验收 → 用户入口切换 → 删除用户 Web admin-only 页面、adapter、client 和无消费者类型/测试。旧 `/admin` 不留代理、alias 或双轨；迁移开发期间未切换的旧页面明确记为当前态。

## 最小实施顺序（沿 T-K03.4，不新建计划中心）

- D0：盘点既有 Admin 的入口、布局、模型路由、Skills、认证和测试；若历史独立源码不可恢复，给出从既有实现迁出的精确文件/删除/验证表，而非新壳。
- A1：仅在 D0 的既有基座上接入缺少的 Skills 管理模块和固定 BFF artifact；保现有 server gate、普通用户拒绝和 session 语义。
- A2：完整迁移/独立项目只在现有模块真实 CRUD、撤权、刷新与目录同步验收后执行；其实现必须复用已验证模块，而非另写页面。
- A3：Root 对管理员和普通用户完成浏览器正/负向验收。
- A4：取得正式 remote/commit 后再组合、切换入口并删除被迁出的旧 surface；不保留双轨。

不以健康探测、默认测试数量或任何旧截图称上述链路完成。当前 Skills 分享/旧版本矩阵、视觉差异及既有 OIDC 失败仍 OPEN，不被迁移抹除。
