# 测试与工程门禁规范

状态：正式规范，2026-08-21

本规范只覆盖开发和交付前质量门禁，不包含完整生产运维体系。

## 1. 测试层级

### Domain/Application 单元测试

覆盖：

- 领域状态转换
- 业务不变量
- 非法输入
- 重复命令
- 权限边界
- 版本冲突

不连接真实 MySQL、Redis 或外部 provider。

### MySQL 集成测试

覆盖：

- fresh schema 初始化
- Foreign Key、UNIQUE、CHECK、partial index
- 事务提交和回滚
- 并发条件更新
- Repository SQL 映射
- 迁移前后兼容性

必须使用真实 MySQL，而不是只用内存 mock 证明 SQL 正确。

### RPC / Contract 测试

覆盖：

- 生成契约与实现一致
- 必填、可空、未知字段策略
- 错误 code 和状态映射
- caller/provider 版本兼容
- request_id / command_id 传递

### Architecture 测试

覆盖：

- Domain 不导入 Infrastructure/Interfaces
- Interfaces 不直接访问数据库
- 模块不导入其他模块的持久化实现
- 生成代码不被业务层反向修改
- 生产入口唯一

## 2. 每个子仓库的最低门禁

```text
format/lint
typecheck
unit tests
fresh MySQL integration
RPC/contract tests（存在跨仓契约时）
architecture dependency tests
local process smoke
```

不能通过缩小 tsconfig、pytest 路径、测试 glob 或构建入口来制造假绿。

## 3. 变更与测试对应关系

| 变更 | 最低验证 |
|---|---|
| Domain 规则 | 单元测试 + 非法状态测试 |
| Repository/SQL | MySQL 集成测试 |
| DDL/迁移 | fresh schema + migration forward/backward compatibility |
| RPC/Protobuf | 生成检查 + caller/contract tests |
| 依赖方向 | architecture tests + typecheck |
| Interface 错误映射 | 协议测试 + validation/auth/conflict cases |
| 幂等/并发 | 重复调用 + 并发集成测试 |

## 4. Review 检查表

- 这次变更属于哪个业务模块和 owner？
- 是否误用了更高等级的 DDD 模式？
- 领域规则是否被塞进 Controller、SQL 或第三方 adapter？
- 是否产生跨模块表访问？
- 是否新增了没有唯一约束保护的幂等假设？
- 是否有真实的失败路径测试？
- 是否更新了相邻 `INDEX.md`、契约或 schema manifest？
- 是否保留了旧入口的关键行为？
