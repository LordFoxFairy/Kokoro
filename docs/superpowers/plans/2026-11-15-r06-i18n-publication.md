# R-06：GitHub 单一发行与 App 单一消费源

日期：2026-11-15。用户已确认 `@lordfoxfairy/i18n`；源码和本地验收收口。只用 GitHub，无新平台、组织、长期 CI secret 或运行时抽象。执行状态见 [唯一 TODO](../../../todo.md)；Root Git 出口由承载本文件的 PR 完成。

## 范围与最小决定

- 唯一引擎 owner 为 shared，App 保留自己的词典/overlays/React绑定；不改翻译行为、Next配置、Mori、tsconfig、web-core、业务认证或部署。
- GitHub npm scope 跟随现有账号，正式包名 `@lordfoxfairy/i18n`；不建组织或兼容alias。使用现 TypeScript 输出 ESM JS/声明，pnpm正规pack，不加bundler或第二manifest。
- 固定 `https://npm.pkg.github.com`；包保持 private、关联真实 shared 仓。发行版本不覆盖，修正另发新版本。
- 本地临时复用现GitHub登录；Actions用自动 `GITHUB_TOKEN`＋`packages: read`。已在包设置给 App 仓 **Read**，source仓Admin保持；不新建PAT/npm读取secret。
- Docker仅在 frozen ignore-scripts install 挂 npmrc/token 两个BuildKit secret，后续approve/rebuild不挂秘密；不经ARG/ENV/COPY落层。保现三workflow触发/部署条件，fork读取失败不跳过冒绿、不改pull_request_target。
- 前片曾在其它私有registry发行过旧名制品；本轮已移除全部该发行接线/说明，不再使用或访问它，也不擅删远端制品/用户原有其它scope配置。

## 已验交付组合

| owner | 正式出口 | 内容 |
| --- | --- | --- |
| shared | [PR2](https://github.com/LordFoxFairy/kokoro-web-shared/pull/2)，main `e0ca7221b17a7d9ca3624aaa664e3f792433b7cb` | 包名与GitHub发行纠正；前片PR1的JS/声明pack沿用 |
| GitHub Package | `@lordfoxfairy/i18n@0.1.0`，private | 从上述main正式发布，真实拉取核等 |
| App | [PR64](https://github.com/LordFoxFairy/kokoro-app/pull/64)，main `75af734b360d68ab235e16c49ac0ab8af31dc6bf` | 精确依赖/正规lock/唯一import、删七文件副本与旧Docker COPY，安装接线及必要文档 |

SRI：`sha512-iJT1C1VYPCvs+KcfU1KG6Q/6jnV2FPN/MfdsW2uVspdncsODxltC1JzAhY5aUf2lr3FPBD0nhS3tP4v08Pnrsg==`。
App保留的lock package/snapshot逐项不变；只删旧副本独有工具链，并由pnpm为可信新精确版本生成min-age放行。没有第二源码、file/link/workspace/alias fallback。

## 实际验收与边界

- Node22.23.4，shared pnpm11.2.2：i18n lint/types/原12tests/build/pack、独立Node/NodeNext类型正负例PASS。真实GitHub fresh-cache下载、SRI、三文件allowlist及dist与源构建逐字核等PASS。
- App pnpm11.25.0：App-only Git archive＋精确停写源码、无sibling/旧node_modules、独立空store frozen install和compiled包import PASS；原resolver/runtime-manifest/governance三文件115 PASS，完整lint/typecheck/production build PASS，独审CLEAR。
- 真实Docker build、隔离standalone候选HTTP200/nosniff、运行镜像无认证文件/环境及history无凭据PASS；候选容器已移除。初次仅本地smoke helper日志参数导致125、应用未启动，修正helper后同镜像通过，未改生产代码。
- App正常main checkout正式frozen install/import PASS；正常 `.next`、服务、卷/数据/资金不动。Root从424个真实提交blob重读，97个App引用配对main，只有package.json/lock摘要改变；拓扑、15边0违例及原checkpoint PASS。
- App远端CI job无steps：账户支付/额度条件导致**未启动**，不是测试运行失败或绿色。未重跑全默认、全产品E2E/模型/支付或部署；这些不是本次依赖来源替换的验收声称。

## 收尾与回退

shared/App原本轮topic远近已核无新增提交并清理；Root本轮PR后置合main并清topic，实际Git状态由最终回执核对，不预写未来merge SHA。只清本轮自建fixture/候选与临时配置，保留收据/日志；不动其它工作树、WIP、原全局凭据或共享builder缓存。
回退整个App来源切换提交，不恢复双来源；已发行版本保留，不覆盖或自动删除。

依据：[GitHub npm registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-npm-registry)、[包 Actions 读取授权](https://docs.github.com/en/packages/learn-github-packages/configuring-a-packages-access-control-and-visibility)。
