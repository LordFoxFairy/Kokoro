# Wave 5 · web 四项子 spec(ERROR-UX / WEB-THEME / HITL-NOTIFY / WEB-MOBILE;同 lane 串行,逐项独立 commit 独立验收)

状态:执行稿(上级=总设计稿 §6 Wave5,已获批)。全部 kokoro-web(分支 agent/p2-auth-wiring),纯前端,
不碰契约不碰后端。

## ERROR-UX(run.failed 分类文案+恢复引导)

- run_error_code 闭集(7 码:token_budget_exceeded/recursion_limit_exceeded/assembly_failed/
  enqueue_failed/dispatch_exhausted/contract_incompatible/internal_error)逐码本地化文案(zh+en)
  +恢复引导(如 402 类→余额入口;dispatch_exhausted→重试按钮=重发原消息;internal_error→重试+
  反馈指引)。message 原文折叠可展开(兜底展示,绝不裸码)。
- 验收:每码组件态测试;浏览器实走至少 1 个真实失败态(如发消息给停掉 worker 的栈→dispatch_exhausted
  卡片),截图 wave5-error-*。

## WEB-THEME(暗色模式)

- .dark 槽位已留(暖纸 token 体系):补全暗色 token 值(保持暖纸气质的暗档,不做冷灰翻转);切换器
  (跟随系统/亮/暗,localStorage 记偏好=UI 偏好合法留存);全组件面过一遍对比度(pill/卡片/Canvas/
  公共分享页同步)。
- 验收:主路径亮暗双态截图各 1(wave5-theme-*);tsc/vitest/eslint 净。

## HITL-NOTIFY(待批通知)

- 会话内已有 awaiting 卡;本项=跨会话可见性:rail 会话条目上待批徽标(session list 数据含否?
  测绘 SessionListItem——无待批字段,V1 用当前打开会话集的 SSE 事件驱动;列表级徽标若需后端字段
  停手报主控,不自造)+浏览器标签页 title 前缀(●)与可选 Notification API(权限求授,拒绝静默)。
- 验收:双会话实走(A 会话触发待批,切到 B 会话看 rail 徽标+tab 标记),截图 wave5-notify-*。

## WEB-MOBILE(移动端主路径)

- 视口 ≤768px:rail 抽屉化(汉堡开合)、输入框/工具 pill/审批卡/Canvas 单栏化、公共分享页自适应。
  只做主路径(登录→对话→审批→成果),管理面板(技能/连接/团队)允许降级为可滚动但不重排。
- 验收:Playwright 移动视口(390×844)主路径实走截图 ≥3(wave5-mobile-*);桌面态回归不破
  (vitest 全量)。

## 总验收

web vitest/tsc/eslint 只增不减;四项截图齐;主仓 e2e gate 回归绿(纯前端应透明,收尾自跑一次)。
