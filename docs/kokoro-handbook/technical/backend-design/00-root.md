# Root 跨仓治理设计卡

## 定位

Root 是跨仓治理和事实源，不是业务后端服务。

## 拥有

```text
contract/   Protobuf/OpenAPI 源、生成器、兼容性门禁
database/   MySQL schema、baseline、slice、owner inventory
deploy/     跨服务组合样例
scripts/    跨仓验证和本地闭环
docs/       长期架构、规范、ADR、迁移状态
```

## 不拥有

```text
业务 Application Service
领域 Entity / Aggregate
业务 Repository
中央业务 DTO
跨模块业务编排
```

## 目标结构

```text
Kokoro/
├── contract/
├── database/
├── deploy/
├── scripts/
├── docs/
└── runtime repositories/
```

## 依赖规则

- Root 可以引用各仓的公开命令和测试入口。
- 子仓不得 import Root 的业务实现。
- 生成文件只由源契约和生成命令产生。
- Root Agent contract 的目标入口只表达 `ExecutionIdentity(tenant_ref, actor, subject, identity_assertion_ref)`、Session/run/Feature/input 与 opaque refs；`RuntimeNamespace` 是 GA ingress 从 tenant + subject 派生的内部结果，不能作为 Browser/Session caller 字段。
- Root database 是物理 DDL authority；业务 owner 仍在对应仓库。

## 100 分证据

- contract consumer manifest 可生成且无幽灵 consumer。
- Root generated Launch/Cleanup contract 验证 `ActorRef`/`ExecutionSubjectRef` 的窄类型；不生成 caller namespace/thread selector。
- schema manifest hash 与 baseline 一致。
- 每张业务表有唯一 owner。
- E2E 只调用公开入口。
- scripts 不承载业务规则。


## 当前落地证据与迁移门禁

当前代码证据（只证明现状，不等于目标已完成）：

- `contract`
- `database`
- `deploy`
- `scripts`
- `docs`

迁移完成前必须同时具备：

- schema 与唯一 owner / runtime writer 清单一致；
- 公开 contract、生成物和 consumer 清单一致；
- architecture test 能阻止越界 import、跨表写入和旧入口回流；
- unit、integration、contract test 覆盖本卡的核心不变量；
- 旧入口或旧写面已删除，或有明确的兼容截止版本和回滚方案。
