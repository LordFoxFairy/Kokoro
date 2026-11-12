# Composer 体验与页面请求：本批诊断／方案

基线：Root `4d6c29f4`／App `46ea8bc3`／BFF `05a10749`。用户优先模型菜单的定位、间距、选中态、长名称；同时关注接口性能。以下是一次有边界的真实读路径核验，不是全站缺陷总表或生产压测。

## 事实与测量口径

- 正常已登录Chrome `/app`，1000px默认视口、同一个既有Next dev进程，无模型调用。菜单288×74px、两行各32px、padding4px，触发器上方8px并带12px碰撞保护；当前短名可读，长label CSS强制ellipsis。
- 两个选项的`name`不同，可能指向同revision；这是正常配置事实，不据截图删模型／改默认值。上方展开本身不是缺陷；优化保锚定／碰撞，不另造定位器。
- 成功空目录无可见状态；锁定的显式选择A离开目录后，当前组件可回退显示默认B却未修改真实选择。这是可复现的条件路径，需要用例承接，不能只改样式。
- 真实完整HTTP缓存启用／禁用样本各17个业务请求，其中3个启动取消请求。Custom API分别`limit=100/50`各返回200；overlay还提前读providers/connectors。样本buffer无截断。最初截断片段／不完整捕获不作为基线。
- 暖样本Network timing：models响应头77ms，其中sendStart约44ms、发送后等待约34ms；pins140ms，其中发送前约70ms。冷样本仅禁浏览器HTTP缓存，不清登录／服务器缓存：models86ms（sendStart58／发送后28）。单样本不是p95／SLO，不能把排队全归服务端。使用response.timing，不把可能晚到的responseReceived事件时间冒TTFB。

## 决策与最小实施

| 项 | 方案／边界 | writer |
| --- | --- | --- |
| UI-05 菜单体验 | 局部菜单按内容宽度并有viewport上限，标签自然换行、可滚动；行距更清晰，checked常驻字重／原radio标记与hover区分。保原Radix键盘／Esc回焦、top/anchor/collision，不改选择身份或新增框架 | composer_ui_audit：Composer菜单／选择展示／局部CSS／相关单测和必要locale键 |
| UI-06 目录状态 | 可见区分成功空目录；锁定显式A缺席不冒显示锁定B，保真实engine选择、草稿与提交。不为读取状态改命令／执行事实 | 同上 |
| PERF-01 多余预热 | 删除AppFrameOverlaySurfaces未打开Settings/目录时的connector预热effect和两个imports；保Composer原reader、Settings自身warm、打开目录后的真实读，不加cache／store／新API。预期Custom API 2→1，取消首页providers/connectors预读，须实测验证 | api_perf_audit：单生产文件＋相关AppFrame测试；避Task B receipt/detail hunk |

读前提与恢复：原subject／generation／分页／取消／late-response、项目默认选择、恢复与chips由现Composer reader保持；本批不碰它。移除预热后原失效测试用显式测试自有warm制造pending读取，保原迟到覆盖风险，而非保生产无用预热。只补对应RED／GREEN和原风险，不跑模型／资金／沙箱。

## 待原owner／后继，不塞进本批

- PERF-02：pins GET源码三次完整准入、成功路径六次IAM HTTP。ADR-035只承诺撤权后下一在线保护请求拒绝，不保证跨owner在途原子排序；重复读取不是原子屏障。可设计为入口一次认证＋本request可信context／本人tenant/active Project SQL，但`project-pin.ts`与Task B #17实质hunk交叉，交原owner沿其PR收敛。不得改PUT未知写保障或只删旧断言。
- PERF-03：模型目录BFF取消／绝对预算未贯通owner request，有断连后继续工作的源码路径。文件不在Task B实际hunk，后继可独立补请求生命周期；需延迟HTTP peer证明取消前不发送／在途终止，不能冒本次已修。
- 不做`limit=100`：当前两项单页，改它没有本次性能收益。模型hook已有同身份复用，不重复造缓存／重试框架。

## 验收与集成

菜单桌面／窄屏／代表语言、长公共label可辨认、checked／键盘／Esc／边界、空目录与锁定缺席状态；不靠CSS源码字符串断言。无原始reasoning／凭据或假成功UI。

正常本地页同条件对照请求数量与timing：首屏无菜单、首次进入Settings／目录、关闭重开；区分缓存条件、开发构建成本、取消、失败。性能收益优先以消除的真实读请求为证，不编百分比。只保脱敏统计到Git；原始trace／机器材料ignored。

两writer不碰同文件；主控唯一Root文档／TODO／Git／浏览器验收。Task B PR只读核hunk，不改／合入；各仓本批一个自有PR、最终精确gitlink与main清理，不部署。

## 本批实际结果（主控停写验收）

- UI-05／06已实现：正常native-auth菜单从288×74变232×88px，行36px、padding6px、checked600／其他400；锚点横差0，上方间距约8px，原Escape回焦。两种原模型选项保持。长label不省略、容器可滚动；触屏行至少44px。空目录和锁定缺席仅基于成功目录事实显示。九语言两新键完整，未冒全词条翻译／全站UI完工。
- 主控focused411 PASS、完整ESLint／非增量TS／production build PASS；新增现runner预览E2E8 PASS（中英1000／320、fine／coarse、255字符公共前缀、完整label、选中与键盘／碰撞）。首轮4个键盘失败来自测试脚本未等待Radix异步focus；增加逐步focus等待及原标签身份检查后通过，未改生产消解失败。17个源码／测试输入在最终门禁前后SHA核等。
- 正常页before／after单次暖对照：基线17个API请求；候选原始15个，其中一个独立auth session读取；同口径页面读14。Custom API仅保limit50，limit100与providers／connectors列表共三次无用预读已消除；Composer必要的connector单项读保持。首次Settings三目录200，关闭重开无目录GET，未增加cache。
- 同一暖样本model响应头77→38ms，sendStart44→8ms、发送后等待34→30ms；pins140→83ms，sendStart70→37ms、发送后70→45ms。主要硬证据是减少三次请求；这些数值仅本地Next dev单样本，不承诺稳定降幅／p95。修改后未再采HTTP缓存禁用样本；浏览器缓存已恢复启用。
- 首次Settings同时观察到既有MCP icon404。未确定owner归因／未修；不据此修改Task B图标链，也不称全部读请求绿色。需原App/BFF/目录owner按具体资源路径核对，和本批三目录200分开。
- 未跑完整默认／全部E2E／contract generation／architecture独立套件；本批没有wire、engine、依赖或边界变化，只补受影响读与UI风险，不拿旧全门冒当前证据。原PG／Redis／MinIO／Scanner与后端未动；App仅为预览／build短停后恢复正常配置。

交付采用本批一个App自有PR和Root精确组合PR，最终提交与main出口记录于唯一TODO。API wire未变，无canonical／生成物／公开API说明重复副本；更新相邻INDEX／当前设计和本报告。PERF-02／03及icon观察仍未交付，不与本批完成混算。

App [#62](https://github.com/LordFoxFairy/kokoro-app/pull/62)正常合main `59d412c9`，树核等已验 `179b6412`；实际CI annotation是账户账单／额度导致任务未启动，不冒测试绿、不付费或绕保护。Root只更新该精确gitlink，并从85个已提交Git blobs重算93个App声明引用，其他owner不动。

Root最终暂存组合的拓扑／兼容15边0违例／原checkpoint全部PASS。初次调用尚未暂存新gitlink导致旧index与新inventory不配对；暂存唯一App gitlink后原命令重跑通过，没有改验证规则或其他owner。Root自有 [#90](https://github.com/LordFoxFairy/Kokoro/pull/90)负责最终main出口与topic清理，实际状态以MERGED／clean核验为准。
