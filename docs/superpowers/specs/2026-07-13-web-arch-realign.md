# WEB-ARCH 子 spec——kokoro-web 代码设计重构(对照参考定案;行为零变化)

状态:执行稿(用户点名"参考 ai collection 的代码设计";诊断定案 2026-07-13)。铁则:行为保持重构
——组件测试断言语义不变(仅装配位移),浏览器主路径回归,分五阶段各自可验证提交。

## 诊断定案(吸收思想不抄实现;参考仓路径不入档)

强项保持(不动):contract Zod 单源边界校验/src/core 纯核心隔离/BFF 同源代理凭据不出浏览器/
`--k-*` 语义 token 单源/轻量外部 store 惯用法。表面差异不动:app router、BFF+Zod(跨语言后端下
优于 tRPC 思路)、样式方案。

结构短板(重构对象,两主因互相放大):
A. 无共享 server-state 层——各域 client 手搓 loading/error/refetch,无缓存/失活/去重约定;
B. `src/ui/shell/session-shell.tsx` 747 行 god-component 独揽全域装配(33 hook);
C. billing/team/hub 跨面板业务规则散在 UI;D. ui/ 18 子域零 INDEX.md;E. 异步契约未沉淀 hook。

## 五阶段(顺序执行,每阶段独立 commit+全量三绿)

1. **共享查询层**:自建窄约定 `src/lib/query/`(不引 react-query——吸收"统一服务态契约"思想,
   规模不需要库;留后评估注记):`useResource(key, fetcher)`(模块级缓存+in-flight 去重+
   `invalidate(keyPrefix)`+error/loading 统一形状)与 `useAsyncAction`(提交态+错误归一)。
   单测覆盖缓存/去重/失活/竞态(先发后至丢弃)。
2. **面板迁移**:hub/team/billing/artifacts/share/models/agents 各面板的取数与提交全部迁到
   查询层;各域 `client.ts` 收口为纯请求函数(无 React 无状态);变更后按 keyPrefix 失活
   (如启停技能→invalidate('hub/skills'))。删除各面板手搓 useState 取数样板。
3. **shell 拆解**:每能力域抽 controller hook(`use<Domain>Panel`,自持查询+store+回调),
   `session-shell.tsx` 降为插槽接线(目标 ≤200 行);面板挂载语义/快捷键/布局行为不变。
4. **业务规则下沉**:散在 UI 的跨面板规则(billing 金额/周期格式与 402 判定、team 角色权限判定、
   hub required-lock/配额判定)移入各域纯模块(零 React 零 I/O)+单测;UI 只消费。
5. **ui/ INDEX.md**:被稳定装配的域(shell/composer/thread/rail/canvas/hitl+四大面板)各补
   最小地图(职责/公开件/协作者/陷阱);对照自身 CLAUDE.md §2 验收。

## 验收(每阶段+总)

- 每阶段:web vitest 全量只增不减(断言语义不变)/tsc/eslint 0 error;阶段 commit 独立可 review。
- 总:浏览器主路径实走(登录→对话→HITL→成果→四面板开合)+截图 tmp/screenshots/webarch-*;
  `python3 scripts/e2e-v21-gate.py` 全绿;session-shell 行数与面板样板代码削减量入报告。
- 排程:在 quartet-lane(WEB-THEME/NOTIFY/MOBILE)收口后执行(其余项全在本重构爆炸半径内,
  不并行);web 单写者。
