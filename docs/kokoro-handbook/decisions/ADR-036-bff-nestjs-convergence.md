# ADR-036：BFF Nest 原生运行时与按能力收敛

- 状态：Accepted；Task A交付范围内已完成。G0初始决定2026-10-31，最终事实核对2026-11-11。
- 当前技术与认证边界见[系统总览](../technical/00-system-overview.md)，实际交付与下轮项见[CURRENT](../../CURRENT.md)和[TODO](../../../todo.md)。

## 变更前的问题

原BFF由手写 `node:http` listener和bootstrap dispatcher集中承担路由、认证、owner client、PostgreSQL／Redis和worker装配，并使用全局Service／Repository locator。旧代码是迁移前基线，不代表当前运行时。

## 保留的决定

1. `src/main.ts` 通过Nest创建唯一应用／listener；`src/app.module.ts` 为唯一composition root。
2. 配置、资源、owner client、feature和worker生命周期通过Module／Provider及显式DI装配，测试按实际需要override provider。
3. 按Chat／AG-UI、Projects、ScheduledTasks、Account、Skills／MCP、Billing等业务能力聚合。Controller做wire／context／error映射；用例与事务留在实际拥有该行为的业务边界。
4. Repository只为复杂查询／锁／事务／幂等／ledger／outbox等真实边界保留；简单owner投影直接消费生成客户端。不建BaseRepository、万能CommonService或重复DTO。
5. `LegacyRoutesModule`、旧手写bootstrap dispatcher/composition和全局locator已在Task A清理中退役。不再把临时adapter列为允许保留的当前入口；不恢复alias、双读／双写或第二套listener。
6. `database/schema.sql` 保持唯一canonical schema；本决定不引入跨owner SQL、迁移链或第二份业务存储。

## 最终认证裁决

IAM拥有原生登录Session与续期；App薄adapter，BFF认证边缘鲜验后建立principal。普通IAM业务使用接收方直接服务认证＋可信actor，不转发人类Cookie／Session-ref／用户Bearer；本人账户会话管理保留专用peer＋issuer Cookie＋exact Origin例外。服务身份不取代当前权限、Run或资金授权。

采用[ADR-034](ADR-034-independent-admin-web.md)与[ADR-035](ADR-035-direct-internal-service-authentication.md)的当前边界。已否决的native-admission profile及旧hash不是有效实施前置，不恢复到机器合同。详细wire只在owner合同维护。

## 生命周期与验证

- Nest统一资源与worker关闭、readiness和drain，不用进程成功退出推断持久副作用完成。
- 保留实际HTTP／SSE预算、取消、owner传输和原生认证relay，不靠默认middleware推导完整业务保障。
- 相关完整默认、合同、类型／lint／build／架构门和指定真实PG／Redis／原生浏览器组合证据已按Task A记录交付；mock、条件跳过和真实依赖分别标明。旧G1未验叙述不再代表当前状态。
- 不为后继文档维护重跑未变源码的全量门；新变更按影响面验证。CI账单／额度未执行不写成CI通过，未部署不写上线。

初始G0材料和临时转换阶段可从[固定历史版本](https://github.com/LordFoxFairy/Kokoro/blob/bdebba56a046703400845f79ae57834d4dfa4d0a/docs/kokoro-handbook/decisions/ADR-036-bff-nestjs-convergence.md)追溯。历史门不形成第二套当前计划。
