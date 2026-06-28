# 迁移清单：加 siteId

## 范围

本文定义把现有全局数据安全站点化的迁移步骤。核心原则：分阶段、可灰度、先回填再约束，不一次性推翻当前 P0。适用于 user / payment / credit / agent / session / artifact 各仓加 `siteId`。

## 为什么不能一把梭

```text
R1  一次性改所有 schema，迁移风险过大。
R2  siteId 只加字段但 API 不强制传，形同虚设。
R3  先删全局 unique 又没加新约束，瞬间允许脏数据写入。
```

迁移顺序的本质是：让旧数据先有归属（default site），再让新写入受约束，最后才弱化旧的全局约束。

## 标准迁移步骤

对每个要站点化的表，按顺序执行：

1. 建 default site

   ```text
   创建一个 default Site，作为现有全局数据的归属站点。
   ```

2. 回填 siteId

   ```text
   现有 user/team/order/credit/artifact 等行回填 default siteId。
   回填完成前不得进入下一步。
   ```

3. 新 API 强制 siteId

   ```text
   写入类 API（如 POST /users/ensure）要求 siteId 必填。
   新数据从此带正确归属。
   ```

4. 老 API 灰度废弃

   ```text
   不带 siteId 的旧入口标记 deprecated，灰度引导到新 API，最终下线。
   ```

5. 新增 site scoped unique

   ```text
   unique(siteId, emailNormalized)
   unique(siteId, provider, providerSubject)
   unique(siteId, accountId, idempotencyKey)
   ……按表语义增加 site 维度唯一约束。
   ```

6. 弱化全局 unique

   ```text
   site scoped unique 生效且验证通过后，才移除或停用全局 unique 依赖
   （如全局 externalUserId unique）。
   ```

## 迁移检查清单

逐项确认：

- [ ] default site 已创建。
- [ ] 目标表全部行已回填 siteId，无 NULL siteId。
- [ ] 写入类 API 已强制 siteId 必填。
- [ ] 旧无 siteId 入口已 deprecated 且有灰度计划。
- [ ] site scoped unique 已建并通过约束校验。
- [ ] 全局 unique 仅在新约束验证后才弱化。
- [ ] 反例测试已补（见下）。

## 反例测试

每个站点化阶段必须补对应测试：

```text
same email different sites        -> different users
same OAuth subject different sites -> different users
site A subscription not visible in site B
site A credit bucket not spendable in site B
site A admin cannot query site B users
site A model policy does not allow site B model
job context cannot switch site mid-run
sitemap contains only current site URLs
```

## 禁止项

```text
禁止  先删旧唯一约束却没有新约束（瞬间允许脏数据）。
禁止  改代码加 siteId 字段却不回填历史数据。
禁止  用 email 做跨站 join（同邮箱跨站默认是不同用户）。
禁止  siteId 只加字段但 API 不强制传。
禁止  一次性改所有仓所有表的 schema。
```

## 阶段顺序

整体站点化按控制面优先推进：

```text
先引入 site 控制面（kokoro-site）。
再让 user 站点化。
再让 payment / credit 站点化。
再让 model / agent / session / artifact 继承 SiteContext。
最后完善 web / admin / SEO。
```

每阶段保持：数据可迁移、API 可灰度、测试覆盖反例、不恢复 InMemory runtime fallback、不引入中央业务契约子仓。

站点边界定义见 [../decisions/ADR-001-site-boundary](../decisions/ADR-001-site-boundary.md)；用户身份边界见 [../decisions/ADR-002-user-identity](../decisions/ADR-002-user-identity.md)。
