# Kokoro 当前执行事实

核对日期：2026-10-04，R189。完整 **Wave 0–7 goal active，整体尚未闭环**。本文件只保留当前事实；历史轮次、失败与资源收据在 [progress.md](progress.md)（含R189逐字归档原CURRENT），不以历史GREEN覆盖当前失败。

## 1. 唯一计划与质量入口

- [task.md](task.md)：既有Wave 0–7、owner依赖与唯一任务卡；当前执行卡在末尾R189，不另建计划中心。
- [test-cases.md](test-cases.md)：逐页/模块系统级业务测试矩阵，记录预置、步骤、预期、优先级、类型、实际结果/证据及未验项。
- [CODEBASE_MAP.md](CODEBASE_MAP.md)、[AGENTS.md](../AGENTS.md)：目录、owner、工程规范与调用方向。
- 子仓的 tests 不迁入 Root。`scripts/tests/` 只覆盖 Root 治理脚本；跨仓集成/浏览器验收属于 `verification/` 与现有具名Root driver。组件、mock、工程门通过不冒用户业务闭环。

## 2. 当前源码与发布边界

|Owner|当前基线/候选|当前可证明范围|
|---|---|---|
|Web `apps/kokoro-app`|main `c5e925678cf80bfdc3abe76669e1febe1d5347d8`（Files窄片本地提交，未push）加混合候选；尚未整片提交|R188冻结工作树工程门2454通过、build0；三个真实Next/Chromium用例通过。当前runtime尚未包含Move候选。R189 AppFrame view fence与反馈代际隔离完整源码门2457通过、独审0；Files导航片已实际浏览器验收并窄同步运行副本；Library数据503仍OPEN。|
|BFF `apps/kokoro-bff`|main `8e33bc0a64d2f92ab2fcd113b1951f490487a8d3` 加D18 Project DELETE本地事务候选|真实PG/Redis完整182通过；本地事务不等于public DELETE/Storage释放/关联定时任务业务闭环。canonical Run上下文及Direct/创建错误边界已同完整183真PG/Redis门恢复；新resolver专项竞争门/发布/live消费仍OPEN。|
|Agent `apps/kokoro-agent`|main `81bc2ae9f872e234a4309d43e95cf6e77f1ba143` prepare窄片本地已提交、未push；Root gitlink未更新|A1 schema/catalog两表与Run completeness已验，仅持久化边界；prepare最终真PG56通过；此前9df全database267通过。去cast后完整工程2175通过/365资源deselected、lock/纯门/build0，限定持久事务已验。runtime producer、finalizer、Billing接线未完成。|
|其它运行owner|IAM0537b2d、System9a4e98e、Storage14f2bc9、Platform物理kokoro-capability da813ed、Billing e04bff9、Scheduler e8dca48|这些是本轮实际checkout短SHA，不证明远端发布/全门/用户链。Billing已有任务外变更必须保留。物理Platform cutover及所有owner组合验收仍按既有目标推进。|

Root本片起始基线为main `28a2a439c8da1b897a2a437738581e39f04cd19e`，R189台账提交由Git历史绑定；Root不暂存未发布子仓gitlink以伪装组合完成。远端/消费者发布必须另取得证据。

## 3. 最近实际验收

|范围|实际结果与终态|证据边界|
|---|---|---|
|Web|Root22564真实Next/Chromium3pass；Root81224 complete check exit0：258contract、50architecture、lint/types、2454pass/0fail/0skip、Next build0|Direct拒绝改名/非active删除/草稿、旧Move ACK结束busy、unknown同key重试。不能关闭全部CRUD、原IAB、Settings或post-confirm竞态。日志 `/tmp/kokoro-r188-web-full-check-root.log`。|
|Agent|Root86926真实schema58pass；Root16750全database254pass/0fail29.64s；Root49017默认2175pass、352资源deselected、ruff/types/build0；lock/frozen-sync/contract0|352 deselection非业务通过。manifest `/var/folders/gn/wbk8wfbd047_wvwkwtyn331r0000gn/T/kokoro-r188-agent-schema-l1q_ndx5/manifest.json`；自库回收/源码不变。schema提交500c2c26不证明模型或费用链。|
|BFF|Root16750真实PG/Redis182pass/0fail/0skip45.28s；schema/build/check/format0，默认743pass+1既定资源skip|manifest `/var/folders/gn/wbk8wfbd047_wvwkwtyn331r0000gn/T/kokoro-r185-bff-full-m48kffdh/manifest.json`；自库回收/源码不变/Redis保持。仅本地owner门。|
|R189当前门|Web Root65931 Node22完整2457pass/0skip，contract258/architecture50/lint/types/build0；Agent Root27104全部database267pass73.23s；BFF Root34000完整真PG/Redis183pass0skip46.21s（前两轮181/2、182/1错误不隐去）|Web view source45039523独审0；BFF Direct invalid与创建错误回归已同门关闭、专门scope竞争门/发布仍OPEN；Agent2174pass1fail原cast门保留历史，最终18098已2175pass/365资源deselected且build0；当前BFF本地owner完整门已通过，不等于用户链/发布。|
|Root治理|CURRENT收口后拓扑测试7pass；实际topology FAIL（两未发布gitlink）；此前两治理测试文件17pass/1fail|历史w1e IAM checkpoint与当前owner gitlinks189项漂移仍OPEN。完整Root与全标准门本轮未重跑，不宣布全绿。|

测试70组原统计仍11通过/6失败/14待复测/38未验/0旧待决/1支付后置，不因局部门上调。新增“删除项目时独立定时任务的保留/暂停/解绑规则”等待用户决定，单独记录，不阻塞其它切片。

## 4. 当前开放缺口与推进顺序

1. **Web当前页面与会话**：原IAB同页恢复未取得直接证据。R187仅独立真实登录Chromium验证原会话正文/输入/10s网络挂起可恢复/硬刷新草稿；不是原IAB恢复。R189 AppFrame confirmed/rejected视图隔离102 UI与完整工程门通过，未同步当前runtime。账户Files→/docs404经正规登录真实点击复测已修为/app/library；两tab数据读取503仍OPEN。
2. **Project/Conversation业务**：公开完整项目CRUD、Project DELETE后Storage durable释放、关联独立任务政策未闭合；项目与独立会话须清晰分离。Message canonical上下文正控通过，Direct explicit invalid和创建错误码边界已本地同门验收；新锁路径scope变化专项竞争、发布与用户链仍未验收；保持Move/删除锁序与exact幂等重放。
3. **Agent执行与能力展示**：真实prepare/ordinal/fence/evidence/finalizer→正式provider→Todo/Tools/Skills/MCP/审批→durable AG-UI恢复→取消/完成→Billing实际费用链未整体通过。先接A1事务，再依已批准owner顺序推进，不改协议为兼容fallback。
4. **Settings**：真实通知与快捷键切tab重置；Personalization无正式owner且404静默；Billing summary/ledger/by-model读失败/缺公开契约；agents404、项目resources503仍开放。Library503已定位当前launcher缺Storage runtime/config，下一Root正式组合装配，不伪装空库。不得隐藏按钮或伪造本地保存后称完成。
5. **其它页面/能力**：Home提示、独立定时任务、文件作品、审批、Skills/MCP、账号/权限、积分流水逐页验收未齐。支付渠道最后，部署运维不纳入研发扩展。

R189原负责人并行：Web agent4_lifecycle_review已冻结view fence/Files导航，Root仅Files窄片已验收提交；Agent agent_mainline_qa_owner已交接prepare窄片81bc，后继运行接线依旧待验；BFF storage_release_r175_gate_review已冻结canonical scope修复，后继真正scope竞争专门门。原生agent_prepare_final_review最终81bc typed-boundary独审0新增问题，先前4P2证据缺口保留。每仓单writer，Root资源/Git/集成验收。

## 5. 资源与业务约束

- 原组合launcher PID45606、Web PID46036本轮已实际确认live；3310运行目录 `/Users/nako/WebstormProjects/github/thefoxfairy/kokoro-local-login-cda7wvjx/next`。无重复服务、无重启、无共享数据重置。本轮自有浏览器已关闭，测试资源已回收；没有待消费Root测试句柄。
- 运行副本仅已批准窄同步：正规auth首屏、R187 snapshot总期限/分页helper/pagehide草稿、R189已验Files导航单文件；Move候选没有同步。源码通过与用户运行态分开记账。
- 一个PG实例/一个应用数据库、同一凭据、owner独立schema；一个Redis实例/独立namespace；禁止跨owner SQL或清空共享状态。
- 默认个人私有、显式分享；普通用户/管理员业务权限由IAM执行，不向普通登录堆原始内部scope展示。
- 正式积分：授权赠送→余额→预占→仅核实实际消耗结算→释放其余→流水；unknown不猜零、不提前结算，不造免费完成声明。费率由Billing owner计算，Web只展示正式结果。
- 任务外Root uv.lock SHA256 `f7e1c30d59d5743493ac6d14d02ff2ec7111c94587470fe721d50f8c08dee7b4` 保持；其它owner未交接修改不覆盖或暂存。

## 6. 闭环退出标准

所有明确页面/模块主链、边界、异常、权限、生命周期、刷新/重放、真实owner和浏览器完整用户路径通过，未解决P0/P1清零，当前commit与发布组合相符，必要完整门有真实终态，才宣布完整Wave0–7完成。Root goal保持active。
