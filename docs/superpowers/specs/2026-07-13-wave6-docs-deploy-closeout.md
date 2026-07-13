# Wave 6 子 spec——文档、部署与发布收口(终局波)

状态:执行稿(上级=总设计稿 §6 Wave6,已获批)。分工:审计/文档主体=单 lane;裁决与指针终定=主控串行。

## A. handbook 全册事实审计(lane)

- 范围:docs/kokoro-handbook/ 全册(README/technical 00-23/modules/product)。方法:逐册比对
  台账(docs/task.md,状态以代码为准)与实际代码,只改**状态位与事实句**——已落地的"进行中/待落"
  改为落地事实+commit 锚;未落的不许提前宣布。不重写结构、不动定案语义;拿不准的列"存疑清单"
  报主控裁决,不擅改。
- 重点已知漂移:README 105 行"HUB-3/4 进行中";20 §1§5/21 §2§6/22 §2§4/15+09 状态头;
  Wave1-5 大量超前(MCP-REVISION/HUB-CONSIST/R0-R7/三竖切/Wave4 十项/Wave5)。
- web 工作台形态(三栏/Canvas/四卡)从历史入口 spec 收编进 22 §4 或新 §(短小事实册,不搬原型稿)。
- 验收:diff 只含状态位/事实句/新增小节;存疑清单 ≤10 条报主控;引用的 commit 锚抽查为真。

## B. 部署面审计(lane,接 A 同 lane 串行)

- 逐仓核 closure-up/compose/K8s/CI 是否随 Wave1-5 的 env 新增同步:清单化比对(新 env 全集=
  各 spec 引入的 KOKORO_*:AUTH_MODE/JWKS/HUB_MCP_MUTATION/OUTBOX_REPUBLISH_MS/
  FINALIZATION_RECONCILE_MS/STUCK_RUN/PERSONAS_DIR/BILLING_HOLD_TTL/QUOTA 等)→缺的补进
  对应模板+文档;不新建部署体系,只补漏。
- SITE-REAL-FALLBACK 收紧评估:报告现状与建议(收紧代码改动若涉 web 且 quartet 已收口可落,
  否则只出建议)。
- tmp/closure 陈旧产物清理(pids/log 归档语义);**.gitwarp/ 永不触碰**;tmp/screenshots 保留
  (验收证据)。
- 验收:env 比对清单入报告;补漏 diff 最小;清理清单先列后删。

## C. 主控串行(lane 报告后)

- 存疑清单裁决;CURRENT/docs README/00 指针终定;主 web 切共享 i18n 的 Wave6 评估结论(记档,
  不强制实施);交接档终稿(全 Wave 收口总账);全链 gate 终跑+主仓终提交。
