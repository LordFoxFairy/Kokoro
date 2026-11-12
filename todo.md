# Kokoro · 当前维护 TODO

核对日期：2026-11-11（America/New_York）。本轮起点Root `9957b41d`；唯一执行清单为本文件，证据集中在[维护报告](docs/reports/2026-11-11-typescript-auth-admin-audit.md)。历史逐次日志从Git追溯，不再平铺为当前任务。

## 当前盘点

- 原审计16个编号是历史全仓盘点，不是本轮全部实施目标。Mori R-05移出主线；其余**15项主线编号中11项已收口、4项有遗留**（R-03／R-06／R-14待处理，R-07部分完成）。不将Mori交付计作本轮主线进度。
- 另有2条旧代码清理候选，单独列出，不混成新故障；已接受容量／取消边界和产品验收暂存也不混入编号统计。
- Task A按用户确认口径已交付，不重开。Task B的PR、分支和工作树不操作；已合并的自有PR不反复建单。

## 当前推进：主工作台／BFF／IAM认证与旧代码清理

- [x] App R-11／R-15已通过自有PR #55合main：Node22类型对齐，保22项生成检查，本地／CI／release验证默认测试只跑一次，独立入口和覆盖不减。主控一次完整check通过；Task B实际hunk与共享CURRENT未动。
- [x] BFF不可达的旧Admin OAuth允许表已删除，自有PR #22合main；Web原生登录／Admin业务／外部OAuth保留，主控44项相关回归与build／lint／types通过。
- [x] IAM过期0.20待接线指引已纠正，主链不换OAuth token、现役外部OAuth配置保留；自有PR #8合main，主控22链接／机器版本与摘要事实通过。

三名聚焦代理分摊App、BFF与IAM，源码独立审查CLEAR；主控已复验并串行交付，不重复十轮扫描或全产品测试。Mori后续及Music产品待办退出本轮；已合版本只保留历史事实，不擅自回滚main。

## 未闭环编号队列（当前4项）

| ID | 遗留问题 | owner／下一动作 |
| --- | --- | --- |
| R-03 | Admin部分菜单／旧页面仍未接正式业务接口 | Task B后台owner；不接管、不造假成功页面 |
| R-06 | App私有workspace与web-shared仍双writer，规范交付未收敛 | shared＋App；App消费者与Task B重叠，先确认owner／交付方式再切换删除 |
| R-07 | **部分完成**：Storage检查已只读交付，Capability检查写副作用仍在 | Capability交其owner；Storage不重复修，Root #77已完成精确组合 |
| R-14 | MCP OAuth DNS pin跨独立授权驻留，公网轮换可持续拒绝 | Capability原owner；composition与Task B重叠，本轮不动 |

**后继边界：** 剩余4项按原owner／Task B交接，未获独立写区不抢改；不为清零扩产品、不按扫描数字扩修。本轮Root自有PR承接精确组合与台账，子仓自有分支已清理。

## 主线已收口编号（当前11项）

| ID | 结果与交付依据 |
| --- | --- |
| R-01／R-02／R-04 | IAM可信actor限流分桶、同事务分页撤销、原生读取／响应生命周期；IAM #7，源码cee88df4，Root #72 |
| R-08 | 已列App／Billing／BFF／IAM／Root入口事实漂移已纠正；本轮App #54／Billing #5完成余项，不泛称全仓所有文档绝无错误 |
| R-09 | 12仓profiles／协议与导入来源／未知诊断机制已本地验收；实际FAIL／unverified原样保留，不把预检当产品闭环，Root #77已交付 |
| R-10 | Admin无消费者旧认证配置／包装退役；Admin #6，源码9bed3d2a，Root #71 |
| R-11／R-15 | App #55，源码906f9c01；Node22类型与锁图对齐，原22项生成检查／Vitest覆盖保持，聚合与CI重复调用去重，完整owner check通过 |
| R-12 | 持久回执不再重复留无界Map；BFF #20，源码00a9ebee，Root #71 |
| R-13 | Project业务／完成回执同事务，回滚／重放／竞争／提交响应未知已定向验；BFF #21，源码a3e19062，Root #75 |
| R-16 | 一次性main-only脚本及当前入口退役，合法detached／他人topic与错pin反例保留；Root #75，mainf0efcb87 |

详细实际命令、失败／复验、跳过与未运行边界见[报告§13～17](docs/reports/2026-11-11-typescript-auth-admin-audit.md#17-主线范围纠偏与最小清理)。不拿测试数量代替行为闭环。

## 旧代码候选（不重复立编号）

- [x] BFF旧Admin OAuth允许表：已核与Task B账务实际hunk不重叠，经#22退役；现役原生relay与外部OAuth保留。
- [x] Billing旧`createBillingAuth`总factory：已通过#5退役，现役Personal／Catalog／operator／JWT保留。

## 既存本地工作的保护与交接

- [ ] 原仓App登录失败页的既存WIP已保存完整文件、基线和二进制补丁；恢复／交接状态仍需核实。保留私有归档，不当垃圾清理；未确认前不覆盖当前main或他人改动。恢复前核摘要、仅处理该路径，不整仓reset。此项不计作新增产品／代码故障。

## 已接受边界与产品暂存

- IAM原生get-session按BFF汇聚源IP共享额度仍需代表性容量核验；不随意抬限流或引入token缓存。HTTP超时不等于非合作数据库副作用硬回滚，超大撤销集合保留有界事务失败语义。
- [ ] A-13：Telegram／LINE／Slack真实账号授权、收发和撤权；本地协议证据不冒充真实供应商。
- [ ] A-14：用户本人语音转写后编辑并显式发送；不保留录音或口述原文。
- [ ] 可选E2B云／完整自托管生命周期：实际使用时补创建、重连、独立回收；官方envd Docker本地真实协议链已通过，不再阻塞开发交付。
- [ ] A-15体验余量：冷态约303～306ms对100ms目标差距及历史偶发诊断，按下一轮产品需求排序。

Task A原生浏览器／附件／历史引用／定时任务／E2B收据见[当前技术总览](docs/kokoro-handbook/technical/00-system-overview.md)及[CURRENT](docs/CURRENT.md)；真实支付保持关闭，未部署。唯一证据私有归档保留；只清自有已交付分支／资源，不碰他人工作。
