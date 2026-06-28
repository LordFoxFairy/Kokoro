# 安全和权限

本文定义安全边界、权限模型、风控、审计、数据泄漏 checklist、删除保留和迁移安全。链路可观测性见 [10-observability](10-observability.md)，平台架构见 [02-platform-architecture](02-platform-architecture.md)。

## 安全边界

```text
siteId            第一业务隔离边界，所有业务表和查询的默认 filter。
workspace/team    站点内协作边界。
user              站点内身份。
service account   服务间或自动化访问身份，必须绑定 siteId（+ workspaceId）。
provider secret   只保存 secretRef，不保存明文。
```

同邮箱跨站是独立用户，业务身份默认不合并；只有风险信号可平台级聚合（见风控）。

## 权限

权限默认按 `siteId` 过滤。基本角色：

```text
owner
admin
member
viewer
```

后台 permission key 按模块划分：

```text
site.*  user.*  team.*  model.*  credit.*  payment.*  agent.*  session.*  artifact.*
```

访问边界：

```text
Platform Super Admin    可跨站，但所有操作写审计。
Site Admin              只能访问当前 site。
Workspace Owner/Admin   只能访问当前 site 当前 workspace。
Member                  只能访问授权 workspace 的资源。
Service Account         绑定 siteId/workspaceId，不能创建全平台业务 key。
```

仅 platform root admin 可跨站查询；其余一律带 `siteId`。

## 风控

业务身份默认站点隔离，但风险信号可以平台级聚合。

```text
允许平台聚合    abuse email hash、provider fraud signal、payment risk signal、
                IP/device risk score、same payment instrument across sites、
                signup velocity、free quota farming、prompt/API key abuse。
不允许默认合并  用户账户、订单、积分、workspace、artifact。
```

两者不能混淆：业务账号默认不合并，风险信号可聚合。

## 审计

必须审计的关键写操作：

```text
登录/注册、用户禁用/删除。
团队成员变更、服务账号创建/撤销/轮换。
model provider/policy 变更。
pricing rule 变更、credit grant/spend/refund、credit manual adjustment。
payment webhook replay。
site domain/policy/brand/SEO 变更、site status 变更。
artifact publish/unpublish。
```

审计字段：

```text
siteId
actorKind = user | service | provider | system
actorId
workspaceId
action
targetType
targetId
before/after summary
requestId
ipHash
userAgentHash
createdAt
```

审计落 MySQL，见 [06-data-storage](06-data-storage.md)。

## 数据泄漏 checklist

以下必须落到测试和代码审查：

```text
1. 查询忘记 siteId filter。
2. invite token 不绑定 siteId。
3. service account 不绑定 siteId。
4. artifact public URL 不绑定 canonical host。
5. job queue / run request payload 丢失 siteId。
6. webhook event 未绑定 siteId。
7. admin manifest 未声明 site scoped resource。
8. analytics 只按 user email 聚合，跨站混算。
9. 日志输出明文 token 或 provider secret。
```

## 删除和保留

站点内用户删除：

```text
停用 User -> 删除或匿名化 profile -> 保留必要订单/账本/审计
-> artifact 按策略删除或保留 -> public 页面下线。
```

站点归档：

```text
保留 financial ledger 和 audit log -> 冻结新写入 -> 清理 runtime trace
-> artifact 冷存储或删除 -> SEO noindex/410/301。
```

## 数据迁移安全

给现有记录加 `siteId`：

```text
先创建 default site -> 所有现有记录回填 default siteId
-> 新 API 强制 siteId -> 老 API 灰度废弃
-> 加 site scoped unique -> 最后移除全局 unique 假设。
```

禁止：

```text
直接删除旧唯一约束但没有新约束。
先改业务代码但不回填数据。
用 email 做跨站 join。
在日志里输出明文 token 或 provider secret。
```

## 验收标准

```text
所有业务查询都有 siteId filter 或明确 platform admin override。
service account 无法跨站使用。
webhook/payment/credit/job/artifact 都能追溯 siteId。
site admin 查不到其它 site 资源。
风控能跨站聚合信号，但不会把业务账号默认合并。
```
