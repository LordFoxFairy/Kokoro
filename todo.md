# Kokoro · 当前维护 TODO

核对日期：2026-11-11（America/New_York）。本轮起点Root `7edca39a`；唯一执行清单为本文件，证据集中在[维护报告](docs/reports/2026-11-11-typescript-auth-admin-audit.md)。历史逐次日志从Git追溯，不再平铺为当前任务。

## 当前盘点

- R-01～R-16共16个已编号问题：当前**10项已收口、6项仍有遗留**（4项待处理、R-07／R-11部分完成）。R-05 adapter已由Mori #3合main，Root本PR承接精确组合；本轮起点9／7，不是新增故障。
- 另有2条旧代码清理候选，单独列出，不混成新故障；已接受容量／取消边界和产品验收暂存也不混入编号统计。
- Task A按用户确认口径已交付，不重开。Task B的PR、分支和工作树不操作；已合并的自有PR不反复建单。

## 本轮收口：R-05 Mori adapter

- [x] **原生认证接线**：Product已有原生会话与标准三配置、公开Host／Origin校验；旧Cookie、namespace／principal及loopback默认已删除。
- [x] **有界转发**：普通／音频上传／GET媒体SSE按现seam限额与期限，取消、Range／幂等／原字节保留；无通用代理框架。主控一次完整owner check及独占Next→BFF HTTP接线通过，替身边界明确。
- [x] **契约／文档与交付**：7份认证契约仅改Product会话scheme，业务内容／成员顺序守恒；独审CLEAR。[Mori #3](https://github.com/LordFoxFairy/kokoro-mori/pull/3)已合main，源码3a4400e3，自有分支已清。Root本PR锁精确pin及更新台账；Task B不动。

本轮只闭环R-05所列adapter债务。Mori继续preview，不新建独立登录／OAuth，不接管Music owner、BFF缺失业务路由、R-06共享迁移或Task B；不拿测试替身冒真实登录／音乐生成／播放全链。

## 未闭环编号队列（当前6项）

| ID | 遗留问题 | owner／下一动作 |
| --- | --- | --- |
| R-03 | Admin部分菜单／旧页面仍未接正式业务接口 | Task B后台owner；不接管、不造假成功页面 |
| R-06 | App私有workspace与web-shared仍双writer，规范交付未收敛 | shared＋App；App消费者与Task B重叠，先确认owner／交付方式再切换删除 |
| R-07 | **部分完成**：Storage检查已只读交付，Capability检查写副作用仍在 | Capability交其owner；Storage不重复修，Root #77已完成精确组合 |
| R-11 | **部分完成**：Mori已交付，App的Node类型仍需对齐运行环境 | App package与Task B重叠，交原owner；不重复修Mori |
| R-14 | MCP OAuth DNS pin跨独立授权驻留，公网轮换可持续拒绝 | Capability原owner；composition与Task B重叠，本轮不动 |
| R-15 | App聚合check重复执行同批contract／architecture测试 | App原owner；保generator检查与同等覆盖，只收敛编排，package与Task B重叠 |

**后继顺序：** 本轮Root精确组合经自有PR交付并清理；其余6项按原owner边界保留，不为清零抢写Task B、按扫描数字扩修或重复全产品测试。

## 已收口编号（当前10项）

| ID | 结果与交付依据 |
| --- | --- |
| R-01／R-02／R-04 | IAM可信actor限流分桶、同事务分页撤销、原生读取／响应生命周期；IAM #7，源码cee88df4，Root #72 |
| R-05 | 同源adapter原生会话／fixture隔离／有界传输已验；Mori #3，源码3a4400e3。非独立冷登录或完整Music产品验收 |
| R-08 | 已列App／Billing／BFF／IAM／Root入口事实漂移已纠正；本轮App #54／Billing #5完成余项，不泛称全仓所有文档绝无错误 |
| R-09 | 12仓profiles／协议与导入来源／未知诊断机制已本地验收；实际FAIL／unverified原样保留，不把预检当产品闭环，Root #77已交付 |
| R-10 | Admin无消费者旧认证配置／包装退役；Admin #6，源码9bed3d2a，Root #71 |
| R-12 | 持久回执不再重复留无界Map；BFF #20，源码00a9ebee，Root #71 |
| R-13 | Project业务／完成回执同事务，回滚／重放／竞争／提交响应未知已定向验；BFF #21，源码a3e19062，Root #75 |
| R-16 | 一次性main-only脚本及当前入口退役，合法detached／他人topic与错pin反例保留；Root #75，mainf0efcb87 |

详细实际命令、失败／复验、跳过与未运行边界见[报告§13～16](docs/reports/2026-11-11-typescript-auth-admin-audit.md#16-r-05-mori同源adapter修复)。不拿测试数量代替行为闭环。

## 旧代码候选（不重复立编号）

- [ ] BFF旧Admin OAuth允许表仍列已不可达项：与Task B policy写区重叠，留原owner；不能删现役原生relay或外部OAuth。
- [x] Billing旧`createBillingAuth`总factory：已通过#5退役，现役Personal／Catalog／operator／JWT保留。

## 既存本地工作的保护与交接

- [ ] 原仓App登录失败页的既存WIP已保存完整文件、基线和二进制补丁；恢复／交接状态仍需核实。保留私有归档，不当垃圾清理；未确认前不覆盖当前main或他人改动。恢复前核摘要、仅处理该路径，不整仓reset。此项不计作新增产品／代码故障。

## 已接受边界与产品暂存

- IAM原生get-session按BFF汇聚源IP共享额度仍需代表性容量核验；不随意抬限流或引入token缓存。HTTP超时不等于非合作数据库副作用硬回滚，超大撤销集合保留有界事务失败语义。
- [ ] Mori正式产品接入：当前依赖Product同源已有会话，独立冷登录返回及Music owner的上传／媒体等映射尚未提供；交后续Product／Music owner，不以R-05 adapter传输修复冒完整音乐产品闭环，不重开Task A。
- [ ] A-13：Telegram／LINE／Slack真实账号授权、收发和撤权；本地协议证据不冒充真实供应商。
- [ ] A-14：用户本人语音转写后编辑并显式发送；不保留录音或口述原文。
- [ ] 可选E2B云／完整自托管生命周期：实际使用时补创建、重连、独立回收；官方envd Docker本地真实协议链已通过，不再阻塞开发交付。
- [ ] A-15体验余量：冷态约303～306ms对100ms目标差距及历史偶发诊断，按下一轮产品需求排序。

Task A原生浏览器／附件／历史引用／定时任务／E2B收据见[当前技术总览](docs/kokoro-handbook/technical/00-system-overview.md)及[CURRENT](docs/CURRENT.md)；真实支付保持关闭，未部署。唯一证据私有归档保留；只清自有已交付分支／资源，不碰他人工作。
