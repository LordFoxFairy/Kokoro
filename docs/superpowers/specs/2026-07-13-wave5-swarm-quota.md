# Wave 5 · SWARM-QUOTA 子 spec——swarm 会话内移交 + 组织级配额(同 lane 串行,两项独立验收)

状态:执行稿(上级=总设计稿 §6 Wave5 + handbook 20 D6 定案原文,已获批)。

## SWARM(kokoro-agent;handbook 20 D6"功能层"逐字落地,无契约变更)

- 定案原文:swarm graph 挂全部 agents(各带自己的 prompt+tools);当前 agent **自己判断**该不该调
  handoff 工具移交主导权(模型驱动不强制,与 find_skill 同种智能);active_agent 落 checkpoint、
  共享消息历史;session/wire 不参与切换。字段层(session.agent 首条锁)已在,永不换。
- V1 实现取向:handoff 候选=本部署 personas 资产全集(目录即配置,与 AGENT-PRESET 同源);
  `handoff(agent_name)` 工具(仅候选>1 时挂载;未知名 error 文本 fail-closed);移交=切换 system
  prompt 轨(active_agent 进 graph state/checkpoint,恢复重放后仍在移交后轨);工具面/skills/MCP
  快照不变(swarm 换人格不换授权);HITL/journal/outbox 全程兼容(同 run 同图)。
- 事件可见性:移交对浏览器 V1 不新增 wire kind(D1 拒投机);模型自然语言告知即可;ledger 记
  active_agent 变迁(观测)。
- 验收:双 persona fixture 下模型驱动移交实测(local_fake 脚本扩一档 handoff 场景);恢复后
  active_agent 保持;未知名 fail-closed;单 persona 不挂工具;agent 全量只增不减三绿;e2e 回归绿
  (gate 现流单 persona 透明)。

## QUOTA(kokoro-platform/kokoro-credit + admin 面;组织级=账户级消费上限)

- 模型:credit account 增可空 `quota_micros`(周期上限,微单位字符串)+`quota_period`(V1 仅
  monthly)——admin 面设置(manifest 动作);未设=不限(现状)。
- 执行点:hold 受理前查本周期(自然月,UTC)已结算+在持 hold 累计,超限→402 专用码 quota_exceeded
  (与 credit_insufficient 区分;session 透传,web ERROR-UX 文案后补一键,本项不动 web)。
- 迁移:手写 SQL+migrate deploy(共库纪律);周期累计用既有 ledger 聚合(不建新表;性能靠
  (accountId,createdAt) 索引,缺则补)。
- 验收:credit 单测+集成(设限→打满→402/新周期恢复/未设限不影响/settle clamp 与配额互补不双算);
  admin manifest 动作接真;E2E-40 回归不破(未设限路径);gate 不加断言(配额档 e2e 留运营化后)。

## 总验收

agent/credit/admin 各自三绿;主仓 python3 scripts/e2e-v21-gate.py 全绿。**此项收口=Wave 5 全清。**
