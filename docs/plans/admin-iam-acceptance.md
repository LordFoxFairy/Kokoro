# Admin IAM/Site 测试任务清单（评审稿）

## Gate A：后端静态与契约

- [ ] Proto lint、生成和 provider drift
- [ ] RPC 方法、字段、调用方准入和稳定错误码
- [ ] TypeScript、ESLint、生产构建
- [ ] SQL 零 FK、零 cascade、零关系 trigger 扫描

## Gate B：IAM 应用与数据库

- [ ] 用户、管理员、凭证和密码重置
- [ ] Site 创建、更新、启停、软删除和恢复
- [ ] 原子 Owner 初始化与最后 Owner 保护
- [ ] Site 成员增改、停用、移除、恢复和跨 Site 隔离
- [ ] 组织、组织成员与 Site 完全独立
- [ ] 角色、权限、授权检查和即时撤权
- [ ] Session 选择 Site、失效、单个/全部撤销
- [ ] 登录日志、操作日志、安全事件和完整筛选统计
- [ ] 幂等复用、版本冲突、并发软删、恢复冲突和父记录状态竞争

## Gate C：Admin 自动化

- [ ] 登录两种方式及生产关闭开发入口
- [ ] 所有菜单权限可见性和真实 route
- [ ] 每个列表、详情、筛选、分页、创建、编辑和生命周期命令
- [ ] loading、empty、error、403、404、409 和删除态
- [ ] 错误码到字段、Toast、Alert、冲突刷新映射
- [ ] Site 管理员当前 Site 隔离与平台管理员跨 Site 能力
- [ ] i18n 完整性、可访问性、响应式和无布局跳动
- [ ] 组件、单元、集成、安全、契约、typecheck、lint、production build

## Gate D：可见浏览器 E2E

- [ ] 启动真实本地 PostgreSQL、IAM 和 Admin，不使用 Docker
- [ ] 通过 bootstrap/reset 脚本准备平台管理员
- [ ] 在 Codex 内置浏览器逐步骤执行全部业务链路，不跳过命令
- [ ] 1440×1000、1024×768、390×844 逐页视觉验收
- [ ] 每一步记录用例 ID、分类、预期、实际、本地时间、UTC 时间和耗时
- [ ] 每一步关联截图；失败关联 console、network、RPC、日志和 SQL 证据
- [ ] Fresh fixture 完成第二轮全链路复验

## Gate E：验收报告

- [ ] 分类状态与整体 PASS/FAIL/BLOCKED
- [ ] 环境、commit、契约 hash、数据库 migration 和测试开始/结束时间
- [ ] 用例总数、通过、失败、阻塞及零跳过声明
- [ ] 截图索引、证据索引、缺陷与复测记录
- [ ] IAM 子仓报告与 Admin 子仓报告分别归档
- [ ] 全部 P0 PASS 后才标记闭环
