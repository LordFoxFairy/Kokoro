# Wave 4 · 批5 子 spec——PAY-2 web 购买流 + AGENT-PRESET web 半场(web 单写者同 lane 串行)

状态:执行稿(上级=总设计稿 §6 Wave4,已获批)。逐项独立 commit 独立验收。

## PAY-2 web 购买流(诚实态优先,不放假按钮)

- 先测绘 kokoro-payment 的下单/收银台面(PAY-1/PAY-2 已落 orders/webhook/subscription;查有无
  create-order/checkout-url 面与套餐目录)。**套餐目录若无**:V1 由 payment 模块加最小 packages
  读面(静态表或配置,运营化归后续),不在 web 里硬编码价格。
- web:价格页(套餐卡+权益列表+购买按钮)→BFF 创建 order(经 payment 面,site/owner 从信封派生)→
  拿 provider checkout 跳转(仅当 provider 已配置);**未配置 provider(501)→按钮禁用+"支付暂未
  开通,请联系站点"诚实态**(这不是假按钮:状态真实来自后端 501)。WEB-BILLING 的 402 说明页价格
  入口指到这里(闭环 Wave3 留的入口)。
- 浏览器实走:价格页渲染+未开通诚实态(dev 无 provider 凭据,就走这条真路径);截图 wave4-pay2web-*。
- 负向:未登录访问价格页可看不可买(购买要求登录);订单创建的 site/owner 不可伪造(信封派生)。

## AGENT-PRESET web 半场

- 契约已冻结(8ad4384):AgentCandidate{name,description,is_default}+GET /agents。
- session 端点(本 lane 落,session 现无他写者):候选=profile.agents(+general 缺省 is_default);
  无 profile 档=[general] 单候选;路由同 /models 样板(owner 守门)。session 三绿独立 commit。
- web:输入框 agent 选择器(同模型下拉模式:候选经 BFF、首条锁定态、单候选 general 时隐选择器);
  wire agent 字段(MessageCreateParams.agent 已有)。
- gate 断言一条:GET /agents 含 poet+coder+general 且恰一 is_default(gate profile 已声明双
  agent,populated 真证)。
- 浏览器实走:真 auth 栈=单候选隐选择器(同 MODEL-UX 配置面事实,截图空态即可);populated 交给
  gate 断言+组件测试。

## 验收

逐项:web vitest/tsc/eslint 只增不减;session 三绿(agents 端点);payment 模块若加 packages 面则
其测试只增不减;浏览器实走+截图;python3 scripts/e2e-v21-gate.py 全绿(含新 /agents 断言)。
