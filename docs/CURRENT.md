# Root 当前组合

**2026-09-29 Web 文档门已过，正式 Skill 发布读回 P1 待补：** Web `74dcc101f6c457d10db4511365e6898f44f0e625` 四文档门经 Root `80060ae6` pin；独立 Node22 contract **105/105**、architecture **36/36**、终审 P0/P1/P2=0。Web 代码仍走旧 preview/confirm，BFF 六项写候选默认关。双只读调查确认 Web `scope=official|third_party` 对 BFF/Platform `scope_kind` 直接 400；Publish 不自动安装，新个人 ACTIVE 不在 pool；BFF catalog 丢 `source_ref/revision`，Publish ACK/key 刷新丢失后无用户可调用的 by-ID 读回。Agent execution Source RPC 要 proof/安装且含私有包字段，不能代替。下一关键路径先 Platform 安全 exact by-ID Product 投影→BFF public read/个人列表→Web shadcn Dialog/Chromium，见 [`task.md`](task.md)。**这是真实产品阻断，不以已有 Publish 200 冒称用户可见。**

**2026-09-29 BFF Publish 真 owner 组合已验、产品仍默认关闭：** BFF `55ca6c1d8a7fbd0a21bea8d3539667a68d67e9d9` 已有六项 Skills public 运行候选，Root `7a174002` 精确 pin；Root Node22 format/contract **161/161**/check **480 pass、1 skip**/schema **5 pass、1 skip**/build 与独立终审 P0/P1/P2=0。Root `4d338089` 的独占 IAM/BFF/Platform/Storage/PG/Redis/MinIO/ClamAV 真组合 `/tmp/kokoro-bff-publish-real.log` exit0：public 合法 ZIP Validate→Publish **200 ACTIVE**、同键同 event/revision replay、异键 active **412**、持久 outbox 精确关联、撤权 **401**/零新 Platform socket；Skill **2**/receipt **31**/outbox **2**、资源 clean、Redis DB14=0、3310 PID **81692** 不变。**Web 仍使用旧 multipart UI、Chromium signed PUT/CORS 未验，Platform v4 inactive；不是用户可用或全产品闭环。**下一片 Web 三面文档门→一次替换现有 shadcn Dialog，见 [`task.md`](task.md)。

**2026-09-29 BFF Publish 仅三面/机器候选门通过：** BFF `b357c190e6ab02fdfc217c1db3e7207bda4bb6a1` 的唯一 OpenAPI 增 user-only Publish 未激活候选，零字节 body、PERSONAL(1)、owner 3.0.0/8 向量及 strict ACTIVE/event 回执；Root `5d08f78d` 精确 pin。独立 Node22 format/contract **147/147**/check **466 pass、1 skip**/schema **5 pass、1 skip**/build PASS，独立审查 P0/P1/P2=0；topology/checkpoint PASS。**没有 BFF Publish 运行 route/真用户调用，Platform v4 仍 inactive**；下一切片先 runtime+真同 event replay，再 Web 真 Chromium 上传发布，见 [`task.md`](task.md)。

**2026-09-29 BFF Validate 真 owner 组合已验、产品仍默认关闭：** BFF `126460791fd90742bccafb1f8d17e143b56c4eb6` 的 user-only Validate 运行候选由 Root `874d2d90` 精确 pin；Root 独立 Node22 format/contract **144/144**/check **463 pass、1 skip**/schema **5 pass、1 skip**/build PASS，独立终审 P0/P1/P2=0。Root `2b3b79d9` 的隔离真 IAM/BFF/Platform/Storage/PG/Redis/MinIO/ClamAV `/tmp/kokoro-bff-validate-real.log` exit0：合法 ZIP public Validate **200**/同键 replay/Get validated、CLEAN 非 ZIP **412**/aborted/显式新 Begin 恢复、旧 attempt **412**、撤权 **401**/零新 Platform socket，旧 owner Publish 回归；Skill **2**/receipt **30**/outbox **1**、`resources=clean`、Redis DB14=0、3310 PID 81692 不变。Root 全 `scripts/tests` **968 pass/246 subtests**、checkpoint/topology PASS。兼容库存 13 条 declared broken、十仓标准 136 项既有违规仍红；**Web Chromium/CORS、BFF public Publish、v4 产品激活仍未完成**。下一切片是 Publish 文档→运行→真组合，然后 Web 一次替换，见 [`task.md`](task.md)。

**下一代码顺序：** BFF Validate/Publish 已通过默认关闭的真 owner 组合，Web 四文档门也已过；先补 Platform→BFF 当前个人 ACTIVE by-ID 读回/列表，再一次性替换 Web 旧 multipart preview/confirm 与其多候选“直接发布”假路径。真 Chromium/CORS 和产品激活仍须独立验收。详见 [`task.md`](task.md) 与 [`progress.md`](progress.md)。

**2026-09-29 BFF Complete 真组合已验、产品仍默认关闭：** BFF `1aee40265a57a120fc2ba43c1d7a5ca547690ae9` 的 user-only Complete 运行候选由 Root `036d12e7` 精确 pin；Root Node22 format/contract **127/127**/check **446 pass、1 skip**/schema **5 pass、1 skip**/build PASS。隔离真 IAM/BFF/Platform/Storage/PG/Redis/MinIO/ClamAV `/tmp/kokoro-bff-complete-final.log` exit0：public CLEAN/replay、错摘要 412、EICAR public 412/aborted/同键拒绝/显式恢复再 CLEAN、撤权 401/零新 Platform socket、旧 ZIP Validate/Publish 回归；Skill **2**/receipt **24**/outbox **1**、资源 clean、Redis DB14=0、3310 PID 81692 未变。Root runner 独立终审 P0/P1/P2=0、全 `scripts/tests` **966 pass/239 subtests**、topology/当前 checkpoint PASS；compatibility 13 条 declared broken 仍红。**Web 可见上传/Chromium CORS/PUT、Validate/Publish public、v4 激活与全产品闭环未完成**；下一切片见 [`task.md`](task.md)。

**2026-09-29 BFF Complete 仅三面/机器候选门通过：** BFF `457472dd14f26219473d30f9b763c2d345be03a0` 在唯一 OpenAPI 增 user-only Complete 未激活候选，三面文档、语义门与直接契约对齐；Root `cafdfc60` 精确 pin。Node22 contract 112/112、check 431 pass/1 skip、schema 5 pass/1 skip、format PASS，独立终审 P0/P1/P2=0；Platform v4 仍 inactive。**BFF 尚无 public Complete 运行路由/真 owner 组合，更无 Web 浏览器上传闭环。**下一切片见 [`task.md`](task.md)，先运行候选再真 IAM/Storage 验收；3310 未动。

**2026-09-29 BFF Skill Begin 真组合已验收、产品仍未激活：** BFF `571108b91084bec0be4451b8840a2d7cd9d2496a` 交付默认关闭的 public Begin；Root `0aaab19745bac32ab615869bb20d5564e9182726` 精确 pin，Node22 contract 109/109、check 428 pass/1 skip、schema 5 pass/1 skip、build/format PASS，独立终审 P0/P1/P2=0。Root 自有真实 IAM/BFF/Platform/Storage/PostgreSQL/Redis/MinIO/ClamAV 末次组合通过 default-off 503/零 Platform socket、Begin 201→current pending→直接 signed PUT、同键重放/异 body 409、显式替换 epoch 2、撤权 401/零新 socket及旧 ZIP Validate/Publish 回归；Skill 2/receipt 19/outbox 1、`resources=clean`，3310 listener 未动。**Web 可见 shadcn 上传、Chromium CORS/preflight/PUT、Complete/Validate/Publish public、Platform v4 激活和全产品闭环均未完成。**下一门是 BFF Complete 三面/机器契约，见 [`task.md`](task.md)、[`progress.md`](progress.md)。

**2026-09-29 BFF Begin 仅文档/机器候选门通过：** Root `7c29332cdbf13d6fc11373c864e40902cd7f7aa5` pin BFF `145c422c052b7409b960deeeb2d185285492e4e8` 的唯一 public OpenAPI 候选 `POST /v1/skills/{skill_id}/package-upload` 与三面文档；Platform v4 仍 inactive。Node22 独立 contract 94/94、check 412 pass/1 skip、schema 5 pass/1 skip，机器/Proto 独立审查 P0/P1 无发现、三处 Get 证据旧句 P2 已返修并由 Root diff 复核；Root topology/checkpoint PASS。**没有 BFF Begin 运行路由或浏览器签名 PUT**；下一代码片须先修现有 Get 同路径 POST 拦截，再实现幂等命令/Origin＋签名头＋expiry 校验、真 owner/Chromium CORS/PUT 组合。BFF 无 Skill SQL/receipt/新 role，3310 未动。见 [`task.md`](task.md)、[`progress.md`](progress.md)。

**2026-09-29 BFF Skill Get 默认关闭候选真组合已验：** Root `4300f4fc4a8e29d9afa64b594755035c96715fed` pin BFF `f0aaf386bc7f7ca81ff4b996b84d29f0ce05e02f`，其 Platform v4 23 件来源固定 `263a28f`。真 IAM/BFF/Platform/Storage/PG/Redis/MinIO/ClamAV 组合通过默认关闭 503/零 Platform socket、新 Draft GET `none/epoch 0`、Publish 后非 draft 412、撤销同 session 401/零新增 socket，以及旧包链回归；Skill 1/receipt 16/outbox 1/resources clean，3310 listener 未变化。Root Node22 BFF contract 91/91、check 409 pass/1 skip、schema 5 pass/1 skip；独立终审 P0/P1/P2=0。**v4 仍 inactive，Begin/Complete/Validate/Publish public、浏览器 PUT/CORS、Agent pin、孤儿退役和全产品闭环未完成**；下一切片先做 BFF Begin 文档/机器契约门。见 [`task.md`](task.md)、[`progress.md`](progress.md)。

**2026-09-29 BFF Skill Get 候选契约已过文档门：** BFF `58bcfc7da656981c1a43a9918ab9f96d207bbecc` 发布 user-only package-upload Get 的未激活 OpenAPI 候选，当前运行路由仍只有默认关闭 CreateDraft，Platform v4 尚未由 BFF pin。Root Node22 契约 80/80、全 check 397 pass/1 skip、Schema 5 pass/1 skip，独立审查 P0/P1/P2=0；尚无真实 Get 用户调用/撤权或浏览器上传链。详见 [`task.md`](task.md) 与 [`progress.md`](progress.md)。

**2026-09-29 Platform Publish 真组合已验收：** Root `aa0a757ebe5e88f0a12bd007321173dfb2d0788c` 固定 Platform 正式 Publish 代码 `391fa9a958744b0cf463484ef869ac3b37c86b3c`，后续 Platform `263a28f1e55745bd1829a61f68228d775751adbc` 仅更新当前文档。真 IAM/BFF/Platform/Storage/PostgreSQL/Redis/MinIO/ClamAV 隔离组合完成合法 ZIP Validate→Publish ACTIVE、同 event replay、错误 visibility/owner/新命令拒绝；Skill 1/receipt 16/发布 outbox 1/epoch 6 active+validated、resources clean。Root 独立 Node24 默认 985 pass/238 skip、真 PG 52/52、只读审查 P0/P1/P2=0；3310 未触碰。**BFF public 包命令、Source 的 Agent 执行证明、Agent pin、Storage 孤儿退役、危险包主动隔离、广义故障恢复及产品激活仍未闭环**；v4 inactive、广义边仍 broken。详见 [`progress.md`](progress.md)。

**2026-09-29 Platform ZIP Validate 真组合已验收：** Root `da05a65ee884d8262f480178ed0d124931b6eb05` 固定 Platform `6ae056bba74330014a94992b25cfcc1208792b7f`，独占真实 IAM/BFF/Platform/Storage/PostgreSQL/Redis/MinIO/ClamAV 跑通正式 Begin/Complete、合法 ZIP V1/manifest Validate、CLEAN 坏 ZIP 终结/恢复和感染包拒绝/恢复；Skill 1、receipt 15、最终 epoch 6 validated、`resources=clean`。Root 独立 Node24 默认 962 pass/218 skip、真 PG 32/32、Root scripts 959 pass/212 subtests、topology/checkpoint PASS；独立复审 P0/P1/P2=0。**Publish、BFF public/session、Agent pin、最终未知提交/租约接管、Storage 孤儿退役仍未闭环**，兼容库存 13 条 declared broken、十仓标准 136 既有违规、依赖审计 8 项告警；用户 3310 未触碰。详见 [`progress.md`](progress.md)。

**2026-09-29 正式 Platform Complete→真实 ClamAV 感染终结 PASS：** Root `014d6f3b` pin Platform `62417f97423007b2bd48731427e7b1ab70ef062b`，独占真 IAM/BFF/Platform/Storage/MinIO/ClamAV 组合同时保持 CLEAN 完成回归，并在 `skill_package` 范围用 EICAR 字节证明 `FAILED_PRECONDITION`、当前 attempt `aborted`、Storage 固定 Asset 当前扫描 `INFECTED`、同命令重放不变、显式新 Begin 从 aborted 恢复（epoch 4）。Skill 1/receipt 8/resources clean，独立核临时数据库/Redis/桶余量均 0；3310 未触碰。该 fixture **不是合法 ZIP**，ZIP Validate/Publish、BFF/Agent 消费、跨进程未知提交与孤儿退役均未验；广义边仍 broken。


**2026-09-29 正式 Platform Complete→真实 Storage CLEAN 纵切已验收：** Root `b602589e89a960a493d83825a62d4496cc365c61` pin Platform `80f294645d1c658ae198acb54766c37c10d314db`，Node24 全静态/default **905 pass/208 skip**/build、真 PostgreSQL Begin+Complete **22/22**、最终独立只读审查 P0/P1/P2=0。独占 IAM/BFF/Platform/Storage/MinIO/ClamAV 真组合的 Begin→PUT→替换→正式 Complete CLEAN/`uploaded`、同命令重放、新命令同 Asset 收敛、错 SHA/owner/旧 attempt 拒绝与旧 GET 原字节回归均 **PASS**；Skill 1/receipt 5/resources clean，独立资源余量 0。Root `scripts/tests` **959 pass/212 subtests**、topology/checkpoint PASS；十仓标准仍 136 既有违规、兼容库存仍 13 条 declared broken。下一门是真非 CLEAN、ZIP Validate/Publish 与产品消费；**不是全产品闭环**，用户 3310 未触碰。


**历史基线：2026-09-29 Begin 架构收口已验收，彼时 Complete 仍是下一门：** Platform `a4feaf0320946755aec0dfc16750eb048bd1657f` 将 Source/Package Connect transport 与 Begin Prisma transaction 真实分责，主 RPC 954→692 行、Begin service 780→322 行；Root 独立 Node24 默认 **894 pass/194 skip**、真 PostgreSQL Begin **8/8**、独占 app schema 的 receipt+Get **37/37**、双只读终审 P0/P1/P2=0。Root 十仓标准由新增回归 138 恢复历史 **136 violations/0 unverified**，仍 FAIL。Root `9d0d288b768c5783ee20b0508b7599b72a1685b8` 固定新 Platform 后，真 IAM/BFF/Platform/Storage/MinIO/ClamAV 的 Begin→重放/签名 PUT/Get、负例与 CLEAN GET 原字节回归再度 **PASS/resources clean**；用户 3310 未触碰。下一片正式 Complete 与恢复，不冒称 ZIP Validate/Publish/BFF public/Agent 完成。

**历史基线：Platform 正式 Begin→真实 Storage 纵切当时已过、架构尚未收口：** Platform `10fdeda5f60c478439b0743faa753e1e183b2896` 的真实 Begin RPC、v4 inactive、Skill+external receipt CAS/恢复和单一认证 Storage v2 Create/Status 已由 Root 独立 Node24 默认 **893 pass/194 skip**、真 PostgreSQL **8/8** 与两项独立终审 P0/P1/P2=0 验证。Root `3b00a40cc04a31283ee53a564244f7e6ea1c3e1d` 的独占真 IAM/BFF/Platform/Storage/MinIO/ClamAV 组合以 BFF CreateDraft 当前 Skill→IAM catalog workload→Begin→同命令重签/稳定 attempt+upload→带完整 headers 的 signed PUT→Get upload_pending 与错 digest/owner/filename/replacement 拒绝 **PASS**；旧 CLEAN 包对象/正式 adapter GET 原字节回归也 PASS，runner 报 Skill 1/receipt 2/resources clean。Root `scripts/tests` **958 pass/212 subtests**、topology/checkpoint PASS、compatibility 16 边/13 declared broken。该阶段十仓标准 FAIL **138 violations**，比旧基线 136 多的两项 Begin/RPC 职责回归后已在上段修复。**BFF 尚未发布 Begin public route；此纵切不是用户 session 撤权、Complete/ZIP Validate/Publish、Agent pin、孤儿退役或生产 HTTPS 验收。**该阶段尚待架构收口和 Platform Complete。

**历史基线：Platform→Storage v2 真实包对象纵切当时已过，Begin 当时未接：** Platform `1042bb97753507a3a534fdec6b819fe263bc40c0` 新增只用于隔离组合的 owner CLI，Root `88a7ba0af2a4d6e17074c95e258c1e324220971b` 将其接入已有独占 Skill sandbox：真实 BFF CreateDraft 的 `skill_id`→Storage v2 CreateUpload/签名 PUT/Complete+ClamAV CLEAN→正式 Platform `ConnectStoragePackageClient.verifyPackage`→带原样 headers 的签名 GET，ZIP 原字节/SHA、重放、错误 digest/scope/credential 拒绝均由同一次运行断言；runner `PASS`、`storage_v2_package_reference=PASS`、`resources=clean`。该阶段只复用本地 HTTP MinIO 的隔离 development profile，**当时未证明 production HTTPS endpoint、Platform validated 包/Source/Install、Begin/Complete/ZIP Validate/Publish 或 Agent pin**；广义边仍记 broken，用户 3310 未触碰。

**历史基线：Platform Storage v2 消费代码门通过时，跨 owner 包读取尚待验：** Platform main `cede13a679b85713779365daef3dc02293121747` 已删除 Storage v1/body tenant/裸 URL 单一路径，改用认证 `kokoro-platform`、受信 tenant/subject/`skill_package+skill_id` 的 v2 GetPackageReference；Source 返回完整短期 GET URL/header/expiry，Install 在写入事务内再核当前 validated 包与 manifest，限制性禁用/撤回走全字段窄 CAS 且不被损坏包反向锁死。旧 Source tag/name reserved、v4 仍 inactive。Root Node24 format/lint/typecheck/Prisma/contract/artifact/cutover/schema/default test **891 pass/186 skip**/build 全过，独占真 PostgreSQL/Redis integration **24 文件/260 pass**、post-schema PASS；临时库删除、Redis DB13 0→0，两轮独立复审 P0/P1/P2=0。Root `26d4c7ca` 后 topology/checkpoint 与 `scripts/tests` **957 pass/212 subtests**；真 IAM→BFF→Platform+Storage readiness CreateDraft sandbox 再次 `PASS/resources clean`。**该阶段 sandbox 尚未调用真实 Storage v2 GetPackageReference/对象健康；Agent pin、Begin/Complete/ZIP/Validate/Publish 和六 owner 产品链当时未验**；不把本次门当上传或整体闭环。

**历史基线：Platform Skill 包安全基础已发布、上传链当时未接：** Platform main `32a4f467caa2c9c8fcfa05e3e7b0cafd923b798f` 在已发布的 Get 只读 RPC/Proto/v4 inactive artifact 后，修复旧全行写在包 attempt 开始后覆盖 asset/hash 的风险，增加外部 receipt/Skill 双 fence 的恢复基础。Root Node24 默认 873 pass/182 skip，隔离真 PostgreSQL Get+Safety+MCP recovery 43 pass，独立复审 P0/P1/P2=0。后续 v2 消费代码门见上段。


**2026-09-29 Storage Skill revision 包边界已通过单仓代码门：** Storage main `16a6c1ce95832df6dc839e0d50e957405c5c7005` 已在既有 v2 十四 RPC 中实现 `skill_package + skill_id` 专用范围，仅认证 `kokoro-platform` 可用六项包操作；旧 BFF 包写读、状态、列表、下载、Artifact 与 receipt 旁路关闭，普通文件/作品路径保留。Root 独立 Node24 格式、lint、类型、契约/provenance、Prisma validate、默认测试 **468 pass/156 skip**、构建和 Buf breaking全过；自有单库 owner schema 安装/drift、真 PostgreSQL integration **23 文件/192 pass**、compiled smoke **6 pass**，临时库已删、Redis DB14 0→0。独立复审 1 P1/2 P2 已返修，最终 P0/P1/P2=0。Root 补钉 Agent/Storage 当前 inventory 原字节证据后，checkpoint PASS、`scripts/tests` **957 pass/212 subtests**、拓扑 PASS；兼容库存仍 **16 边/13 declared broken/0 额外来源错误**，全仓标准仍有 136 既有规则违例。**这只是 Storage owner 边界**：Platform 仍用 Storage v1，可信 Product 授权、持久 revision 包绑定、v2 consumer、真实外部 S3/ClamAV/六 owner 组合均待验；不改用户 3310。

**2026-09-29 Storage 包范围历史文档门：** Storage main `4f092fa3abbfbf3bb6b6a22129e1f914ff8fd3c2` 当时仅同步 F2 当前事实与 W1E `skill_package` 目标，六文档经 Root 独立格式/机器计数核对和终审 P0/P1/P2=0；**该 SHA 仅文档变更**。当时 Storage 仍只有三 scope，Platform 仅旧范围包引用资格且仍用 Storage v1 consumer；后续代码门结果见上段。

**2026-09-29 Agent Platform v3 机器消费者前置已验：** Agent main `7dfcfa936d0b51244683ffd66d16ea937fe510a6` 已将唯一 Platform Proto/完整 17 文件 v3 execution artifact 固定到 owner `5b6eb2c1532b23b9747bc4bf6ac99f69ad453de0`，删除 Agent v1 vendor；六项技术 RPC 的投影对齐 owner 向量，生成树精确拒绝残留 Platform 文件。Root 独立 `uv lock --check`、Ruff、Pyright、contract、生成校验、默认 pytest **1312 pass/6 skip/172 deselected**、wheel/sdist build 通过；独立复审 P0/P1/P2=0。此为机器来源/离线投影门，**未接入 typed Skill/MCP 产品选择、未执行真实 Agent→IAM→Platform 六 RPC**；Platform manifest 仍 inactive，库存 Agent 边保持 broken。用户 3310 未触碰。

**2026-09-29 Skill Draft 预激活真组合已通过：** Root main `f4efc66ce9b6b28ae2bf92dd8bdfe7f41b37201a` 提交后复跑 PASS，固定 IAM `eb6700c13f84a165620a6be456a25d290bd3da4a`、BFF `caa99d90f57329065eeb0e98168316b2b1874159`、Platform `5b6eb2c1532b23b9747bc4bf6ac99f69ad453de0`、Storage `d5cfc442c675e32363ae767f5ec662a9e0d9eaea` 的**同库独占 sandbox**，真实 IAM→BFF→Platform Connect + Storage readiness：默认关闭 503/Platform 零 socket；显式候选首次 201、同 key 同 Skill/Series 重放、异 body 409、IAM 撤销后同 key 401 且 Platform 零新增 socket；Platform SQL Skill/receipt 各一份。runner 报 `PASS/resources clean`，自有进程、临时库/Redis namespace、独占 S3 bucket 均经清理核对；Ruff 0.15.15、聚焦 pytest 33/33、独立复审 P0/P1/P2=0。此仅为 **user-only CreateDraft 的预激活证据**：Platform artifact 仍 inactive，正式 public 默认关闭、Web 无入口、其余 Skill/六 owner/Billing 未闭环；3310 未触碰。

**2026-09-29 Skill 真组合协议返修：** BFF main 已前移到 `caa99d90f57329065eeb0e98168316b2b1874159`。Root 用固定四 owner 在自有单库/Redis/MinIO/ClamAV 短寿组合确认 readiness、默认关闭 503 且 Platform 零 socket；启用后首请求曾返回 `502 skill_response_invalid`。根因是 BFF Connect 客户端误用 HTTP/2，而 Platform 正式 Express Connect ingress 使用 HTTP/1.1；BFF 已精确改为 HTTP/1.1，本仓 Root Node22 全门 392 pass/1 skip、独立复审 0 P0/P1/P2。**修复后的真 201/replay/撤权仍待复跑**，前段旧 SHA 只代表修复前阶段 B；3310 未触碰。

**2026-09-29 BFF Skill Draft 阶段 B 已发布、真组合待验：** BFF main `18691e646a7f54cda9e764f776a86a9f4c08fd6e` 已实现 user-only `POST /v1/skills/drafts` 的默认关闭候选：每次先 IAM admission，再由独立 catalog machine token 与 generated Connect 调 Platform；同操作在通用 BFF mutation receipt 前精确分派。Root 独立 Node22 format/lint/typecheck/contract/test/build/schema 全门 exit0，默认测试 392 pass/1 skip、Schema 5 pass/1 无库 skip；独立复审最终 P0/P1/P2=0。**未运行真实 IAM→BFF→Platform 201/replay/撤权组合**，Platform v3 artifact 仍 inactive，Web 未接、正式 public 未激活、旧 Capability 四 GET 仍在；3310 未触碰。

**2026-09-29 IAM Skill sandbox host 已发布：** IAM main `eb6700c13f84a165620a6be456a25d290bd3da4a` 只扩展测试 fixture 的显式 opt-in 协议，提供真实 Skill 用户 session、catalog/Platform 机器凭据及 IAM execution-authorization credential，并由 IAM 自己执行一次性 session 撤销；默认 Web OIDC host 协议不变。Root 独立 Node24 `pnpm verify` 102 文件/938 passed，真 PostgreSQL/Redis 聚焦 integration 28/28 passed，独立复审 P0/P1/P2=0；不代表 BFF/Platform 的真实 201 或 Web 产品入口。下文历史组合仍固定其原 SHA。

**2026-09-29 BFF Skill 阶段 A：** BFF main `5d26f09cc1b425926f49b284a31136ce8ff2da03` 已精确 pin Platform v3 Proto/完整 inactive artifact、独立 CreateDraft raw/JCS 投影，并在唯一 OpenAPI 发布 **未激活候选** `POST /v1/skills/drafts`（冻结 operation 77→78）。Root Node22 全静态/契约/测试/构建通过（376 pass/1 skip），独立复审最终零阻塞；来源库存 16 边/13 declared broken/0 provenance violation、拓扑 PASS。consumer manifest 仍 `generated-not-activated`，但 `execution_artifact` 已精确指向 inactive v3 aggregate。Platform runtime/ADR-002 §13 复核证明 `inactive/routable=false` 是发布标记而非 RPC kill switch，隔离真实 IAM/BFF/Platform 201 可作为**正式激活前**证据。BFF **runtime route/credential/Connect 尚未接入**，默认入口继续 503；真 201、Web 页面、六 owner sandbox/正式激活均未验，不称整体闭环。3310 未更新。

**2026-09-29 owner 边界：** Agent main `cbb2719` 的 General 工作区写入通过单仓组件门及一次真实模型/浏览器作品纵切。Platform main `5b6eb2c1532b23b9747bc4bf6ac99f69ad453de0` 的 v3 artifact 与 Prisma schema drift CLI 身份修复通过 Root 独立 Node24 静态/构建、verify **853 pass/179 skip**、隔离真 PostgreSQL/Redis integration **22 文件/252 pass/0 skip**，独立复审无 P0/P1/P2。此前 `d227a1d` 的 249 pass/3 fail 是历史故障基线，现已关闭；v3 aggregate 仍 inactive/routable=false，BFF/Storage/Agent 消费和六 owner 产品链未验。下文 S9 真浏览器证据固定旧 Agent SHA，只能证明当时的确定性投递组合。3310 登录预览未由这次代码门更新。

**2026-09-29 真实模型纵切更新：** Root `5b1b9a5e` 固定 gitlink 的隔离真 IAM/HTTPS Chromium→Web→BFF→System→现有 Ollama `qwen3:8b`→正式 Agent worker→Storage/MinIO/ClamAV→durable AG-UI/Chat/Canvas **PASS**：Product 202、System 1 次、模型成功 3 次、Agent `write_file`/`deliver` journal 各 1、唯一 `delivery.created`/`run.completed`、Storage FINAL CLEAN、作品原字节下载/刷新唯一卡、同租户他人 3×404。自有数据库、Redis、进程、S3 versions 均清零，独占桶删除；3310 未触碰。此前同门失败和修复详见 progress；这不是多模型稳定性、Platform v3 消费或全部 Product 能力完成。Platform schema 门已在后续 owner commit 通过。

状态日期：2026-09-29。Root 是 Git superproject，精确组合以当前提交的 gitlink、`.gitmodules` 与
[`verification/contracts/consumer-inventory.json`](../verification/contracts/consumer-inventory.json) 为准。
业务源码、canonical Schema 和可编辑契约仍由各子仓 owner 维护。实施任务见 [`task.md`](task.md)，
已执行命令与失败记录见 [`progress.md`](progress.md)。

## 当前推进边界（2026-09-29）

**S9 Chat GC/410 真浏览器门已通过（Root `7bbd836b037432a38624786040b9f6f3b5b31b65`）：** 固定 Web `317c74c`、BFF `bd1f794`、Agent `486adb1`、Storage `d5cfc44`、IAM `4d98144`，隔离真 IAM/HTTPS Chromium→Web→BFF→Agent→Storage/MinIO/ClamAV：同一浏览器先后两次 Product POST 202 和受信 Agent CLEAN 交付，首轮浏览器旧水位的原始 SSE 请求保留；BFF owner `collectGarbage` 在未来 8 日执行既定 7 日保留/30 日 tombstone，实测删除旧帧 3、插入 tombstone 3、`retention_floor=3`，旧 cursor 正式 replay 为 expired。释放原始浏览器请求后，同源 HTTP 真实返回 410 `event_cursor_expired`；Web 自动 GET 权威 snapshot 200，保留两件不同二元作品和新水位，再以新 cursor SSE 200，Chat 两卡唯一、两次 Canvas 原生保存分别与原字节 SHA 匹配。自有数据库、Redis keys、进程、S3 versions 余量 0，独占空桶删除，用户 3310 未触碰。Root 独立 `scripts/tests` **903 passed/190 subtests**、Ruff/Node、拓扑门通过；只读复审无 P0/P1/P2。全仓标准门仍 **136** 违规、合同库存 **16 边中 13 条 broken/0 来源违规**。这证明 S9 GC/410 子门，不等于其余 Product、真实模型 provider/worker、代表性大件故障恢复或整体闭环。

**3310 登录当前态（2026-09-28）：** Web main `317c74c2048829471b0c4196df98dd6d2dcf5e36` 已修正过期签名 GET、浏览器 CSRF 失效 POST，均通过 303 重启固定 `/login`；非浏览器仍 403。真实 Next HTTP 测试发现并修复曾导致 500 的相对 Location。Root 以当前 3310 运行进程和真实 Chromium 完成 IAM 表单→consent→OAuth callback→`/app`，Product Session HTTP 200、`authenticated=true`、HttpOnly cookie；新表单已在用户 IAB 标签显示。Web Node22 全门 contract 105、architecture 36、Vitest 1600、lint/typecheck/build PASS。3310 是临时测试租户登录组合，不含完整 Agent/Storage；不能由此宣称 Chat 或全产品闭环。

**S9 Chat 当前边界：** BFF main `bd1f794e7b1115d96965aa03d8a3a83a33c42fd7` 已发布本人/Project 最近 100 件作品与公开水位的 Chat snapshot；Web main `317c74c2048829471b0c4196df98dd6d2dcf5e36` 已固定新 owner OpenAPI、二元作品身份、AG-UI live/snapshot 严格消费、410 重水合与 Chat 卡片/Canvas 原生下载。Root 独立 Node22 `pnpm check` 为 contract 105、architecture 36、Vitest 1600、lint/typecheck/build PASS。隔离真 IAM/HTTPS Chromium→Web→BFF→Agent→Storage/MinIO/ClamAV 已分别通过**预投递 snapshot/Canvas、订阅后实时交付，以及 owner GC 后旧 cursor 真实 410→快照/新水位/SSE 恢复**三个子门；均仅清理测试自有资源，不触碰用户 3310。Root 相邻测试 903 passed/190 subtests；全仓标准门仍 136 违规、合同库存 13 条 declared broken。**其余 Product 边、真实模型 provider/worker、慢大件与故障恢复仍待验**，不把 S9 子门当整体闭环。

**最新 S8 边界：** BFF main `b382642affa27332e91b49078e0500c6716b820e` 已把作品原字节下载的单一 120 秒预算拆为准入 120 秒、对象取回/校验 7 分钟总及 45 秒无落盘进度、出站 28 分钟总及 25 秒无完成写入进度；异常取消仍释放临时文件和两份 spool 名额。Root 独立 Node 22 单仓门通过（默认 365 pass/1 无库 skip，Schema 5 pass/1 无库 skip），并在 Root `f9f5befa` 固定运行来源下真 IAM/HTTPS Chromium→Web→BFF→Agent→Storage/MinIO/ClamAV 两件 CLEAN 作品原生下载原字节、同租户他人 404 与自有资源清零 exit0/PASS。BFF `99b98040ed6ee21d49ddd6a04c9b645222245d1e` 只同步四文档，无运行/契约/SQL 变化。代表性 1 GiB 限速与下载时故障恢复仍待验；下文旧 BFF SHA 为历史切片。S9 Chat snapshot/Canvas 仍有真实断链，未进入新代码片。3310 用户预览不在本切片重启范围。

**W2-F2 当前切片：** Storage owner `d5cfc442c675e32363ae767f5ec662a9e0d9eaea` 已发布最终 CLEAN Agent Artifact 的稳定 ID、metadata、列表/单项/下载引用 RPC 与 Agent 窄交付操作；Agent `486adb1539dd8a06ca90684e66f91be031aa70cf` 已接入标准 worker 的受信 Run/lease→Storage v2 Connect 交付、恢复 journal、稳定 `delivery.created` critical outbox 与取消原子终态，并把 Storage 已校验的作品 `artifact_kind` 严格贯通回执、journal、持久事件与 Chat。Root 独立 Agent 静态/默认测试 1299 pass/6 skip、真实 PostgreSQL/Redis integration 130 pass/1 skip、构建均通过；增强的真实纵切 run `595608521dde76386a00bf76` 用已 claim 的 Run/lease、生产交付客户端和事件 emitter，通过 Storage ConnectRPC、MinIO、ClamAV、最终原字节下载及 durable delivery→Chat→terminal 同值九项检查，临时数据库/Redis stream/S3 版本/测试桶均清零。BFF `55d3c9cd55386d9dcc074e893cc388924dd94c13` 已在来源 pin 与同事务 Conversation↔Artifact 关联上发布本人私有 Product 作品列表、单项与原字节下载；Root 独立 Node22 默认 358 pass/1 skip、Contract 65/65、隔离真 PostgreSQL/Redis integration 44/44、Schema 6/6，临时库和键清零。**Root 自有 run `8cc05bb6e9adf87be46f9cf6` 已以真实 BFF/Agent/Storage、PostgreSQL/Redis/MinIO/ClamAV 跑通 Product 首消息→Agent pending Run 原子 claim→CLEAN 作品交付/事件→BFF 投影→本人列表/单项/原字节下载及同租户他人404/异租户403；IAM 是测试身份桩，未执行模型 worker。**该早期纵切不是完整 worker/真实模型/Web 浏览器链。当前 Web `102033e34be89ba0e9958447e4d4021fcbf257b7` 已接正式作品入口并恢复客户端断连时的上游取消链；Root `851326dc6dd7169d02bd98f521db80a44cf62483` 在只信任测试自有证书 SPKI 的真 IAM/HTTPS Chromium→Web→BFF→Agent→Storage/MinIO/ClamAV 组合中通过两件作品的真实浏览器原生保存/原字节与安全头、本人分页/详情/刷新/320px 和另一成员列表空/单项及内容 404，个人文件/Project/EICAR 回归亦通过。自有数据库、Redis 键、进程和 S3 版本剩余 0，独占桶删除，未触碰 3310。原 `canceled` 的根因是自签名测试 HTTPS 未被 Chromium 下载管理器信任，并非 IAM 或产品下载流；该浏览器作品纵切已通过，但真实模型 worker、Chat live/snapshot/Canvas、分享、慢大件/故障恢复与其他 Product 边仍未闭环。IAM 0.7 owner 授权切片不等于整个登录服务或产品完成。

**W2 个人文件下载当前证据（2026-09-28）：用户可见纵切已通过，整体仍未闭环。** Root `44ee670f9133dd1cf2c374bd62d56f4057c8343a` 固定 Web runtime `d7848de1ee053f1ec626e8858144893cf8633412`、BFF `d5c868f8ab8b8a33750e1286e9d020ca72895641`、Storage `2d87e26bbaed9a70dcd91ad1e9d126d39d275f38`、IAM `4d981441d154c83b63987f284e3a82a559595870` 的真 IAM/HTTPS Chromium/PG/Redis/MinIO/ClamAV run `fee7b756c799f6e62691e8a3` PASS：个人文件卡两次点击保存原始字节/文件名，下载安全头、列表重载、320px 可读不溢出、同租户他人内容 GET 404；Project/个人上传与 EICAR 原纵切回归。数据库、Redis keys、进程与 S3 版本剩余均0，专用空 bucket 已删除；用户 3310 原登录预览仍在、未热更新。Web 文档证据 commit `eaa7ebd56502cf05b6b402a8a013973c1904b8aa` 不改 runtime。`EDGE-WEB-BFF`/`EDGE-BFF-STORAGE` 及其他 11 条边仍 broken；Agent Artifact F2 与整体产品未完成。以下较早 W2 文字记录历史切片，不覆盖本节当前结论。

IAM `4d981441d154c83b63987f284e3a82a559595870` 的 0.7 owner 切片已发布，不等于整个登录及产品能力完成。固定 Web/BFF/IAM/Agent 组合曾通过隔离真 Chromium 的登录、OAuth 回跳、Product Session、私有聊天、AG-UI 与刷新；其中 System/模型为确定性 fixture，旧 3310 常驻实例没有在本轮热替换。因此“登录写完”是先前错误的完成口径，必须按具体来源与链路分别报告。

**3310 当前可用性（2026-09-28 当前来源真 Chromium）：登录与退出浏览器链通过。** 旧临时组合 supervisor/IAM 已退出、IAM authorize 曾实测 503；Root 仅停止已确认归属的 Web/BFF 孤儿 PID 62986/62984，未碰其他 BFF 进程。新受监督单组 IAM/BFF/Web 先验 `/login`→IAM 签名邮箱密码表单 HTTP 200，再由真 Chromium 提交凭据→consent→OAuth callback→`/app`，Product Session 200/`authenticated=true`。真实 Better Auth 在 issuer 确认 POST 返回 200 JSON 而非 fixture 的 302；Web `224d473758041928a79acfa063eadb13cd779386` 将严格成功目标转成 303 `/login`，避免裸 `/auth/sign-in` 404。Root 停止并清理上一组、以该 Web 当前源码重建 3310 后，真 Chromium 再验 Product signout 200→issuer confirm 303→`/login`→签名 IAM 表单 200，退出后 Product Session `authenticated=false`。这是临时测试租户的在线进程与真实浏览器证据，不等于正式部署、长期在线或全产品闭环。

W2 历史个人上传纵切来源为 Storage `2d87e26bbaed9a70dcd91ad1e9d126d39d275f38`、BFF `8a90fdd9ec3809000924229bfc7b986ba8ba1522`、Web `cbae94d30582e6e16f0f8a8f6b8535920af6de32`。当前 BFF `5add506becd39715dc0a469af83e148a5a354515` 只增真 PG 恢复测试/文档，Web `224d473758041928a79acfa063eadb13cd779386` 只修退出 relay；新精确 tuple 的 W2 真 Storage 浏览器组合仍待重跑。Storage 是 personal/project Asset/Upload/Scan owner；BFF 发布个人 GET 和持久同键恢复的 `POST /v1/library/files`；Web 已将 BFF public OpenAPI 原字节 `6fa107540c6cc60ec8b45f1bcc19c8930f19c803b16f4c6d418c2edc9393fc52` 固定，正式 Library 个人文件页已有 shadcn 文件选择/显式上传、CLEAN 严格回执、本人 GET 刷新、未知结果同键重试和终态区分。Root 独立隔离 Node22 `pnpm check` 为 contract 99、architecture 36、Vitest 1546、lint/typecheck/build PASS；独立端口 3447 Playwright 11 pass/1 既有 skip。此前固定 tuple `5463009f` 的真 IAM/Chromium/PG/Storage/MinIO/ClamAV 已验 Project 与个人同源 API CLEAN、同键重放/冲突、Library 列表/刷新/成员私有；后来 EICAR 422 终态也在文档门 tuple 通过。Root 固定 `0a9206969b2edfcf40bb8d5f0f2d85952995fb8f` tuple 的真 IAM→Chromium→Web→BFF→Storage/MinIO/ClamAV 已从**可见文件选择与按钮点击**验出个人 CLEAN 200、随后本人 GET/刷新持久可见、同租户第二成员空页；同次还覆盖并发同键 409/200、重放200/冲突409、EICAR 422 与同键终态重放422、Project 原纵切。BFF/Storage 持久 SQL 事实匹配，测试自有 PostgreSQL 数据库、Redis keys、进程与 S3 版本余量均为0，独占 bucket 删除。**这是 W2 个人上传纵切通过，不是 Library/W2 或全产品完成**；个人下载、Agent Artifact F2 及其他 Product 边未完成；Complete 故障恢复见下方补门。当前 3310 是独立登录临时组合，不包括本段 W2 的 Storage/MinIO/ClamAV。

**W2 历史故障恢复补门：** BFF `5add506` 与 Storage `2d87e26` 在隔离真实 PostgreSQL、Redis、MinIO、ClamAV 上，Root 故障代理只在 Storage `CompleteUpload` 返回 200 且已读完响应后断开 BFF 侧连接；随后停止原 BFF OS 进程、以同库新进程重试同一文件/幂等键。`run_id=0cc2f4bdf3407c6e7e5d4e8d` 的 12 项 smoke 通过：未知结果先为 503，恢复后 CLEAN 200，Storage Upload/Asset、S3 对象版本、Complete 调用和 BFF terminal receipt 均未重复；异文件同键 409。测试自有数据库、对象版本、进程清零并删除独占空 bucket。此 runner 使用 IAM 身份桩，不证明当前 Web/浏览器 tuple、个人下载或 Agent Artifact F2；`EDGE-BFF-STORAGE` 继续 broken。

BFF owner-only 历史切片：main `d5c868f8ab8b8a33750e1286e9d020ca72895641` 当时先发布个人下载 public OpenAPI 与受控二进制 runtime（代码提交 `318cf6a`），Web 文件卡/同源 adapter 随后已按本节当前证据接线。Root Node22 全门 347 pass/1 既有 skip、schema 5 pass/1 无库 skip；BFF `318cf6a` 与 Storage `2d87e26` 在隔离真 PostgreSQL/Redis/MinIO/ClamAV 的 Root run `5036454fc7b1397a19695361` 14/14 PASS：本人个人原字节、同租户他人 404、既有上传/列表与 Complete 应答丢失后 OS 重启恢复；自有 DB、对象版本、进程清零，独占 bucket 删除。该 runner 的 IAM 为身份桩，不证明当前 Web/浏览器下载；`EDGE-BFF-STORAGE`、`EDGE-WEB-BFF` 均继续 broken。

W2 浏览器验收前发现正式 Web “新建项目”只生成 `preview-project-*`，没有调用 BFF Project 创建 API。Web owner 已修正式侧栏与欢迎页入口：BFF POST 严格回执后按 canonical id 导航，未知结果同键重试，Direct/Project 草稿分键；预览 fixture 独立保留。Root 已从用户点击而非测试预造项目完成上述真实 Chromium 验收。当前 3310 已重建为登录临时组合，但不代表 W2 Storage 链已在该进程中启用。

W2 历史组合：Root 在 `bb6a6502` 对 Web `c140f3b`/BFF `a67ae2d`/Storage `2d87e26`/IAM `4d98144` 隔离真 Chromium 验过 Project 创建、上传、刷新、同租户成员 404；另以测试自有直接 Storage fixture 在真实 PG/MinIO/ClamAV 验过 BFF 个人文件 GET、分页、他人空页/跨人 cursor 400。当前 tuple 的个人文件浏览器正向与私有负例已见上段，但感染/未知响应恢复/并发、下载、Agent Artifact F2、其他 Product 边及 Billing 仍未闭环；详见 `task.md` 和 `progress.md`。

## IAM 0.7 与 BFF 窄消费者历史基线（2026-09-28）

IAM main `4d981441d154c83b63987f284e3a82a559595870` 已发布 Organization Skill 12 动作、user-delegated 专用 scope、同快照具名 check、`0.7.0` OpenAPI/公开 SDK 与真实 Better Auth/PostgreSQL/HTTP 测试。Root 独立 `pnpm verify` 为 102 文件/938 测试 PASS，完整 IAM integration 在原代码候选为 37 文件/280 测试 PASS；最终旧/新 refresh+Code/consent 补测后 Root 独立聚焦 OAuth 3/3 PASS、writer 全量 integration 280/280 PASS。BFF main `815cf564fcbfda9a7d83ab8bb7364fe5fe7df4ff` 已固定 IAM 0.7 窄 Skill client，现另固定 Platform 两份 Proto 并生成 Connect wire；Root Node22 `pnpm format:check && pnpm check && pnpm schema:check` 为 319 pass/1 skip、schema 5 pass/1 skip。**这不是 IAM 或 Product 全链写完**：BFF 尚无 Skill mutation route/credential/digest，Web 仍请求旧 scope，真实 IAM→BFF→Platform 用户链未验，`EDGE-BFF-IAM` 保持 broken。3310 是先前单组临时预览，未以这些新提交热替换运行进程。

BFF 的 Product Skill 四 scope/六 mutation 文档仍只是目标评审，public mutation 运行代码和机器 OpenAPI 未发布。Platform main `ae48c894d9034016a16a4cbaa60ab80743d1aab9` 的运行代码仍是前一 `f26d147` 发布的六 catalog RPC Product context/owner gate 与 execution artifact v2/2.0.0；本次仅追加 v3 机器投影目标设计文档，未写 artifact/runtime。Root 独立 Node24 前片 `pnpm format:check && pnpm verify && pnpm build` 为 819 pass/179 skip，本片 `pnpm format:check` PASS；真 PostgreSQL/Connect 因指定隔离端口不可达仍待验。Storage Begin/Complete 与 Platform 不可变包绑定未接通，因此 Validate/Publish fail closed；BFF public mutation、Web 新 scope 与跨仓消费者亦未完成。不能把 BFF IAM 窄 client、Platform 单仓发布或 BFF generated client 列作 Product 闭环。

## W2 项目资源首片历史基线（2026-09-28）

Storage main `91a8748` 仅新增真实个人附件回环测试及测试 fixture 修复，运行代码/Proto/Schema不变；本地 HTTP MinIO 的真PG/ClamAV验证不代表 production HTTPS。BFF main `815cf56` 固定 Storage v2 Proto `094847da` 的原字节（当前 Storage Proto digest相同），新增 Project 单文件 multipart→CreateUpload→受限PUT→Complete/CLEAN Asset 纵切及持久checkpoint恢复，移除该 POST 的旧503。Root Node22全门319 pass/1 skip、contract28、schema5/1 skip。独立审查指出 Web 仍允许多文件、15秒代理短于 BFF45秒、每次新幂等键且资源列表只保留本地乐观假数据；真实BFF+Storage+ObjectStore/浏览器未跑，`EDGE-BFF-STORAGE`与`EDGE-WEB-BFF`保持broken。本片不是附件/Library/Web完整闭环。

## 3310 临时登录入口历史实测（2026-09-28）

当前 Web main `a7decb69e3f29bf6d0a1988899f107e39964af99` 修复独立 HTTPS TLS 代理下登录表单 rewrite 错误；Root 独立 Node22 `pnpm check` 为 contract 69、architecture 36、unit 1481、lint/typecheck/build PASS。Root 首次以修复前 Web `40a2095` 和当前 IAM/BFF/Agent 执行隔离真 Chromium，在 `/auth/sign-in` 500 停止，Next 将表单 rewrite 错转为 `http://` 公共 TLS 端口（`ECONNRESET`）；修复后首次运行发现 Root 浏览器脚本仍匹配旧英文“Sign in”，已按当前可见中文“欢迎回来/登录”更新脚本与断言。最终固定 Web `a7decb6`、BFF `61b8074`、IAM `4d98144`、Agent `d6fcbf2` 的真 Chromium 隔离组合 **PASS**：同一浏览器完成表单、OAuth/Product Session、DOM 首消息 202、AG-UI 五帧、一次 SSE cursor 断线恢复与刷新后一对 user/assistant；同租户其他成员私有 404，跨租户准入 403。测试自有 PostgreSQL 数据库、Redis DB7/14/15 keys 与进程剩余均为0，旧 3310 未触碰。该组合使用确定性 System/模型 fixture，不是实际模型 provider、常驻 3310 更新或全产品完成证据。

旧预览的 IAM 后端退出后，`/login` 曾 302 到返回 `iam_relay_unavailable` 503 的 `/iam/oauth2/authorize`；此前截图不证明当时的当前态。Root 仅替换已确认归属的旧 Web/BFF PID 88923/88920，使用 `scripts/dev/serve_local_login.py` 重新启动单组隔离 IAM/BFF/Web（supervisor PID 62862，IAM 62935，BFF 62984，Web 62986；另一个旧 BFF PID 81924 未触碰）。新组合的 `GET /login` 经 IAM 到 `/auth/sign-in` 200，Browser 目视邮箱/密码表单、无连接中/整页重试；同一临时账户 HTTP 实测凭据提交 → consent → `/app` 200。fixture 创建独立测试数据库/Redis 前缀，未改变正式子仓发布 commit 或 Billing/Platform 状态；当前预览是进程存活时的临时开发验收，不是生产部署或长期在线保证。

| 子仓 | 该历史组合提交（非当前 gitlink） |
| --- | --- |
| `apps/kokoro-app` | `cbae94d30582e6e16f0f8a8f6b8535920af6de32` |
| `apps/kokoro-bff` | `8a90fdd9ec3809000924229bfc7b986ba8ba1522` |
| `apps/kokoro-agent` | `d6fcbf2424ea6a936bb53f4dc1be95d13f78f2e0` |
| `apps/kokoro-iam` | `4d981441d154c83b63987f284e3a82a559595870` |
| `apps/kokoro-system` | `c0a76a3a7614bf46ea6e665e523f24261862436f` |
| `apps/kokoro-storage` | `2d87e26bbaed9a70dcd91ad1e9d126d39d275f38` |
| `apps/kokoro-scheduler` | `975dee59616a1e0eda609aa69283401344900d83` |
| `apps/kokoro-capability` | `ae48c894d9034016a16a4cbaa60ab80743d1aab9` |
| `apps/kokoro-billing` | `63e0ab6e61b397f23f7ab71f5d6dc9df3d6de0fa` |
| `apps/kokoro-mori` | `ca76c2e12861a2e4a6af3049f6df8c34b417c158` |
| `libs/kokoro-web-shared` | `0c4e87ace01340aaa07bc57935f1d98b8e77af14` |

`kokoro-app` 是本轮唯一正式前端；Mori 不在本轮业务改造内。正式能力仓当前仍是
`kokoro-capability`，尚未完成向 `kokoro-platform` 的原子切换。各子仓自行持有测试；Root 的
`scripts/tests/` 只覆盖 Root 治理脚本，不是业务单元测试总目录。
子仓的 tests 不迁入 Root；业务回归仍在各自 owner 仓执行。
`verification/` 保存跨仓来源库存与验收检查点，不承载子仓业务测试代码。
Platform 已发布单一 `kokoro.platform.v1` Proto、IAM 0.6 ingress 与 `kokoro_platform` 同库 owner schema；Agent 已固定同一 Proto 的只读 vendor 输入、官方 Python Connect generated client 和 24 个 tenant operation 的 request-binding projector，并在 worker 装配租户凭据、IAM token、DB lease 证明与六个 generated Connect RPC。Agent 仍未把 typed Skill/MCP 产品声明接入此 sender；Storage 已窄放行 Platform 原 scope 干净包的 GetPackageReference，但 Platform 仍消费 v1/body tenant/裸 URL 且缺包 scope/manifest，BFF/Web 选择链与真实 IAM→Platform→Agent 三 owner 组合也未验收；不能把 transport/loopback fixture 当作能力激活。Root 库存继续校验 owner OpenAPI 的声明版本与已提交 `info.version` 一致。

## IAM 0.6 固定租户登录与 relay 历史来源

W1E IAM 0.6 历史组合：IAM main `a4c2b61` 已发布 Platform ingress 运行端点/OpenAPI/SDK；BFF main `1105553` 只把完整 IAM owner OpenAPI `0.6.0` 精确 vendor/生成来源/浏览器 policy provenance 重钉，既有 16 个 generated 文件与 browser relay 路由不变；Web main `40a2095` 当时固定 BFF policy `2.1.0` SHA-256 `8f7d4f4cb6fa0ec34d2cce8702d8882d3270a316a6cbdb2d8bdaccefb9c6b4a1`。IAM Node24 97 文件/883 unit 与 36 文件/265 真实隔离 integration、BFF Node22 292 pass/1 skip、Web Node22 1478/1478 最终全门已由 Root 独立复验；Web 首轮全量一个 OIDC refresh 真 HTTP 用例间歇失败，聚焦 38/38 与第二轮全量均通过，仍需单独稳定化。此段不代表当前 IAM/BFF gitlink；Platform 消费者和六 owner 真组合仍待执行。

以下为先前固定组合的历史验收，不是当前 IAM/BFF/Web 来源：

Web main `1fa25d2b4760dc428d3fcdf77628ba343a5bc3ff` 已发布真实 shadcn 登录表单；Root Node22 `pnpm check` exit0（contract 69、architecture 36、Vitest 1478、lint/typecheck/build），3310 临时组合已按明确文件热同步且未重启进程。全新 Chromium 实测 `/login` 302→302→200 到同一邮箱/密码表单、旧重试/连接状态 0；一次无效凭据提交后仍在表单就近报错且密码清空。下面旧三仓组合与无脚本 Route Handler 描述是此前 Root pin 的历史状态；本次仅提升 Web gitlink，不冒充 IAM 0.6/BFF 来源或 Platform 完整闭环。

W1D 历史固定 IAM `b720b6d`、BFF `c586d0b`、Web `9fc2fef`。IAM 仅为本地/测试固定 HTTP loopback 提供显式 native OAuth client，生产 web HTTPS 约束不变。`/login` 在服务端直接启动 Product OIDC，正常 302 经 BFF/IAM 到 Web 唯一签名 `/auth/sign-in` 邮箱/密码表单；没有可见“连接中”或整页重试页。表单为中文紧凑布局，遵循 Web 现有 shadcn 语义色和 Card/Input/Button 尺度；由于它同时签发 Cookie-bound 一次性 CSRF，仍由现有 script-free Route Handler 输出，不冒称直接引用 React 组件。BFF relay policy 已固定当前 IAM commit，Web 原样消费其发布字节。IAM 已发布 `platform:execute` 目录及具名 execution verifier/OpenAPI `0.5.0`/SDK，Root 独立验收 IAM 92 文件/846 单测及真实 PostgreSQL/Redis/JWKS HTTP 8/8；BFF Node22 `pnpm format:check && pnpm check` 292 项中 291 pass/1 既有 skip；Web Node22 `pnpm check` contract 69、architecture 36、Vitest 1475、lint/typecheck/build 均通过。当前三仓精确 SHA 的隔离 HTTPS Product Session S1 已实跑首登邮件→OIDC→会话→issuer logout、Team 同源 HTTP 与 Chat proxy，通过且测试自有资源清零；该 runner 使用 CookieJar/HTTP，Chromium DOM 在这一新组合仍待验。Platform ingress 身份契约、consumer 原子切换、真实 Agent signer 和六 owner 组合也仍未完成，不能将 IAM 单仓 E2 当成授权链闭环。

Root 已按进程所有权正常停止旧隔离预览并清理其自有资源，以 W1D 固定 IAM `6a55ffb`/BFF `bc45632`/Web `942d22e` 重建 3310 本地临时组合。真实 `GET /login` 经 IAM authorize 到中文签名表单为 200；Codex IAB 目视无连接/整页重试，临时账号提交到 consent 后继续进入 `/app`，页面显示工作区/输入区。当前 W1E 三仓仅更新角色权限与来源 pin，尚未重建 3310；该实例是可交互的**临时测试租户**，不是正式部署。Issuer 最终退出仍未在当前 HTTP 组合验收。后续 Chat/Storage/其他 11 条 declared broken edge 未因此闭环，Billing 仍最后。

W1D 历史组合提交 `b5738127ab98e9a2ef1cc2f4ee1d681a88e07255` 已将 IAM/BFF/Web 三 gitlink、16 edge 来源库存与 IAM `0.5.0` 验证器固定；`verify-iam-relay-policy.py`、topology、W1D checkpoint 及单独的治理验证器 36/36 均 PASS。Root 全量 `scripts/tests` 在验证器修复前为 741 passed/187 subtests；修复后全量尚待重跑，不用此前结果冒充当前提交。完整 compatibility 仍 `FAIL`：16 edges、0 illegal、11 declared broken；十仓标准门仍未通过，具体违反项以当前命令为准。

## 已验证到的边界

- Web `08ef650a` 已把两个不被当前 UI/正式 OIDC 使用的旧 magic-link browser route 实际删除；失败回调不再产出 `/login?auth=link_unavailable`。正式 Auth.js `/api/auth/callback/kokoro-iam` 保留。Root `54e18142` pin 后的隔离 HTTPS first-login smoke 再次 PASS，自有资源0；Web 隔离新目录的 Next typegen、TypeScript 和 production build PASS，未改用户 3310 共享 `.next`。旧 auth helper、Team/其他认证路径尚在，普通 IAB 3310 入口依旧未配 IAM/BFF。

- 当前固定 IAM `093b7651`、BFF `7a7f3adf`、Web `0f5aec47` 已由隔离 HTTPS Product Session runner 实测：`/login` 302 直达真实 IAM 邮箱/密码表单，无可见连接中或整页重试；新账号在未验邮件时 403，经真实 TCP SMTP 邮件中的链接由 Web→BFF→IAM GET 验证，随后以新账号/新测试 tenant 完成 OIDC、Product Session、Chat 代理与退出，自有资源剩余 0。注册与建租户由测试 setup 直连 IAM loopback；IAM host 仍预置测试 owner/tenant/client，因此这不是空库首租户开通，也不是当前仅运行 Web 的 `3310` 正式入口。Web Next typegen/build 与普通 IAB 可见 HTTPS 入口仍待单独验证。

- BFF `928ada2` 增加固定 IAM 邮箱验证 GET relay，Web `24445a1` 固定消费其 policy `1.1.0`：真 Next HTTP/Chromium fixture 验证 token query、同源 200/302、最终 `no-store`/`no-referrer`、跳转后请求不带 token Referer、Next 开发 incoming log 不输出验证 token，外域/错误方法/路径别名/重复 query 拒绝。Web Node22 本片 Root 独立聚焦测试 13/13、contract 56/56、architecture 32/32、lint、`tsc --noEmit`、全量 Vitest 1414/1414 通过；未触用户 3310 `.next`，正式 build/Next typegen、真 IAM 邮件点击与普通 IAB 可见登录仍待验证，不把 fixture 当成用户当前可用入口。
- IAM `c16a9bc` 已用真实 TCP SMTP 邮件证明新用户未验证登录拒绝、验证链接生效、持久 `emailVerified` 与后续 issuer Session；BFF `a50f987`、Web `5192ff0` 仅顺序重钉该 IAM 来源与原始 relay policy blob，路由/安全边界未变。IAM owner 全门 740/740、SMTP integration 4/4；BFF 270/1 skip、Web 1414/1414 通过。真实跨仓首次邮件点击与普通 IAB 可用入口尚待独立组合验证。
- Web `/` 是固定单租户公开首页；`/login` 已删除可见连接中/整页重试组件以及失败时共用的假登录页面，服务端启动固定 Product OIDC，
  成功后浏览器直接进入真正的 IAM `/auth/sign-in` 邮箱/密码表单；不依赖 System manifest。
  Web `a70dd24` 进一步删除 RP `signin` 失败时 303 跳回重试页的残留分支；失败返回原状态的结构化错误，不再生成失败页 Location。
  `/app` 只以 Product Session 作认证闸。仅 Web dev 在 3310 运行时，缺少常驻 BFF/IAM/RP 配置，
  `/login` 返回空 body 的 HTTP 503，不是在线登录入口；没有后端不伪造可提交的凭据表单。
- 固定上述 IAM/BFF/Web 提交运行的独占真实 HTTPS Product Session smoke 已通过：Web 同源入口、
  BFF/IAM 协议链、在线会话、Chat 列表 Bearer 代理与退出，测试自有资源剩余 0。这不是 3310 常驻
  服务的证明，也不覆盖首条消息、Agent worker、Web 重载或真实模型 provider。
- 本轮 IAM `c16a9bc`/BFF `a50f987`/Web `5192ff0` 重新执行上述真 HTTPS Product Session runner，修正 Root 对 `Cache-Control` 的过窄字面断言后 `status=passed`、自有资源剩余0；其 IAM 测试 host 预置 verified user/tenant/client，尚未证明真实邮件从 Web relay 点击到正式固定租户首次登录。
- Agent 已发布 typed `createRun`/`replaySessionEvents` 契约及空最终文本完成事件；BFF 已完成
  新会话首消息事务、assistant Message 与 AG-UI 同事务投影，并固定生成的 Agent HTTP 消费者。
  Web 已按 BFF 严格 MessageCreate 契约发送首消息。固定 BFF/Agent SHA 的 Root 真 HTTP + 独立
  CLI worker 首消息组合已通过，覆盖幂等、Agent 执行、AG-UI 与持久重载。Root R2b 进一步把真实 IAM
  Product Session、Web 同源 JSON 首发、BFF 与独立 Agent CLI worker 放在同一次隔离 HTTPS 运行：202、
  同 key 重放、改 body 409、Web 重载 snapshot 与 AG-UI 5 帧通过；测试自有 PG/Redis/进程归零。
  此处使用 Python CookieJar HTTPS 客户端，不执行真实浏览器 JavaScript；System/模型 HTTP 是严格
  确定性测试 fixture。该 R2b 证据本身不包含 Chromium/DOM 首发、跨 tenant 私有负例或真实 provider 验收。
- 固定 Web `175a6d805b69b88c1478b86164fdcbfe925f498a` 的 R2f 真 HTTPS Chromium 组合已 PASS：
  `/login` 在服务端启动 OIDC，浏览器不再请求可见 CSRF/signin 中转页，直接进入带签名 query 的 IAM
  邮箱/密码表单；同一 Chromium 原生提交凭据、选择 tenant、确认 consent，取得 Product Session
  HttpOnly/Secure/Lax cookie 与同源 session projection 并进入 `/app`。随后独立 Python CookieJar
  完成 Web/BFF/Agent worker 首消息与持久回归；自有 PostgreSQL/Redis/进程剩余0。后续 Web 文档提交
  `9794a286` 不改运行代码，Root 来源已重钉，并在该精确 SHA 复跑同一组合 `status=PASS`、资源剩余0。
  在该次验收时 Chromium 尚未发送 Chat、验证实时 AG-UI/断线恢复，真实模型 provider 仍未执行；当时 3310 仅运行 Web，
  没有常驻 RP/IAM/BFF。后续 Chat 浏览器组合与临时 HTTPS 联调入口见本文件当前状态，不以旧 HTTP 标签作登录证明。
- Web `067d7ea` 已修正真实 BFF AG-UI 终帧/工具错误字段的严格解析，并只对 Chat events SSE 采用首部连接 deadline + 可续空闲 deadline；Web 当前 Node22 单仓 `pnpm check` contract56、architecture32、unit1408、lint/typecheck/build PASS，独立只读审查0 P0/P1/P2。Root 已以此精确 SHA 真 Chromium 跑通 IAM登录→DOM首发→真实Agent worker→AG-UI助手DOM→刷新一用户一助手；随后测试自有 TLS proxy 将首次 SSE 截在一个完整帧后，浏览器携该帧 `Last-Event-ID` 重连、恢复助手DOM并保持刷新后一对消息，BFF五帧 cursor 唯一，测试自有资源清零。此证明固定 fixture 的浏览器 Chat/断线恢复，不代表3310常驻IAM/BFF、真实模型 provider、跨用户私有矩阵或全产品完成。
- Web `9e2eb73` 在同一 `/login` 路由不变的前提下，进一步删除九语种 54 条不再使用的连接中、整页重试和旧 handoff 文案；Node22 `pnpm check` contract56、architecture32、unit1408、lint/typecheck/build PASS。Root 固定该 Web gitlink 再跑真 HTTPS Chromium 登录/Chat/一次断线恢复 `status=PASS`，测试自有 PG/Redis/进程剩余 0。当时 Web-only 3310 的 `/login` 返回空 body 503；后续前台临时 HTTPS 联调入口见上文，仍不等于正式租户部署。
- 本地 PostgreSQL/Redis 复用一套实例与应用凭据，数据 owner 各自使用 schema/连接边界；
  Root 不要求此阶段拆分多个数据库角色，不允许跨 owner SQL。Storage owner schema 已有独立验证，
  但 Storage 用户文件链尚未与 Web/BFF/Agent 闭环。

## 仍未完成

1. R2c 已在固定隔离组合中证明 Chromium/DOM 首消息→BFF→Agent worker→实时 AG-UI 与一次受控断线恢复；仍需
   Web 对 BFF public contract 的全量 generated 消费、单一 AG-UI 网络协议门、默认个人私有/显式分享/跨 tenant
   负例以及真实 provider 验收。固定 fixture 不等于正式单租户常驻入口已具备完整能力。
2. Team Product 的 Web→BFF→IAM 同源 HTTP 读链已通过隔离组合；仍需 Chromium DOM、邀请邮件入口与写操作的浏览器端到端验收。
3. Storage/Platform/System/Scheduler 各自 owner 的能力调用、契约与数据闭环；Billing 最后。
4. 当前 inventory 的 13 条 broken edge 仍开放；旧 Web→IAM 非法旁路已删除并从当前 inventory 移除，不能因为局部 smoke 通过而将剩余 edge 标绿。

当前可执行门：`python3 scripts/verify-repository-topology.py`、
`python3 scripts/verify-contract-checkpoint.py --expected verification/contracts/checkpoints/w1e-iam07-bff-pin.json`、
`python3 scripts/verify-iam-relay-policy.py`、`python3 scripts/verify-main-only.py` 和
`python3 -m pytest scripts/tests`。旧 `verify-ten-repository-full.sh` 与
`run_stage2_owner_health.py` 的共享状态编排已暂停；它们不是当前全仓验收证据。
