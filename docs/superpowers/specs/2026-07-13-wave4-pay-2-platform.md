# Wave 4 · PAY-2 子 spec——支付外环 platform 半场(单 lane,不与其他项混;web 购买流另批)

状态:执行稿(上级=总设计稿 §6 Wave4,已获批)。范围:kokoro-platform/kokoro-payment(+确需的
credit 回链窄口)。web 价格页购买流依赖 provider 沙箱配置,归后批;本项先把后端外环做真。

## 现状

PAY-1 已落:webhook 面(验签接口/重放幂等/状态机/驱动确认+confirming outbox);stripe/alipay/wechat
真验签在注册表留位 501;Subscription 写路径缺;refund 回链缺。

## 范围

1. **真验签三驱动**:stripe(webhook signature v1 方案:t=timestamp,v1=HMAC-SHA256(secret,
   t.payload),容差窗口)/alipay(RSA2 异步通知验签)/wechat(APIv3 平台证书验签)。密钥全部
   env/配置注入,测试用官方文档口径的自造测试向量(自签密钥对/已知 HMAC),**不引入 SDK 巨依赖**:
   验签是纯 crypto,标准库+node:crypto 实现;确需窄依赖(如 wechat 证书链)先报再引。501 注册表
   位换真实现,未配置凭据的 provider 保持 501(fail-loud 不假绿)。
2. **Subscription 写路径**:订阅创建/续期事件→subscription 行(状态机 active/past_due/canceled)
   →credit 授予回链(经既有 credit grant 幂等面,reason 用既有枚举;周期粒度 V1=事件驱动,不做
   本地定时续费)。
3. **refund 回链**:退款事件→验签→按原 order 幂等冲正(credit 扣回经既有面;余额不足冲负=允许
   负余额还是 clamp,查 credit 现语义并遵循,注释定案)。
- 迁移:新表/字段手写 SQL+migrate deploy(共库 _prisma_migrations 禁 dev/reset;表名看 @@map)。

## 验收

payment 模块单测+集成只增不减全绿(三 provider 验签正/负向量、重放幂等、Subscription 状态机、
refund 幂等冲正);credit 侧只消费既有幂等面不改契约;未配置凭据 provider 恒 501;主仓 e2e 回归
绿(gate 不加断言,PAY 面无 e2e 环境凭据)。
