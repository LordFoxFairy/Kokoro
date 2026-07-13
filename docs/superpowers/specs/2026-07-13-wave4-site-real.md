# Wave 4 · SITE-REAL 子 spec——多站点真解析(host→site/域名验证/品牌注入)

状态:执行稿(上级=总设计稿 §6 Wave4,已获批)。仓面:platform-site + kokoro-web(删单站点 env 常量
依赖)。纪律:站点独立 lane,不与支付/团队/观测混。

## 语义

1. **site 域名模型**(platform-site):site 增 domains 子资源(admin 面 CRUD):{domain(唯一),
   status: pending|verified, verification_token(TXT 记录值,展示给运营), verified_at}。
   验证流转 V1=运营侧手动触发 verify(admin 动作→查 DNS TXT 匹配 token→verified;DNS 查询用
   node:dns,失败留 pending+原因)。dev/本地域(localhost/127.0.0.1)允许 admin 直标 verified
   (显式动作,不自动)。
2. **host→site 解析读面**(runtime-internal):GET resolve?host= → {site_id, name, brand...}——
   只返 verified 域名(pending 不解析);未命中→404;结果可缓存(TTL 短)。brand 字段按 site 现有
   schema 最小面(name+可空 logo_url/theme 色,先测绘现 schema,缺字段加迁移手写 SQL)。
3. **web 消费**(删常量):BFF/服务端从请求 Host 经 site resolve 定 site_id(替换 env 单站点常量;
   解析失败→退回 env 缺省站点+WARN,不 500——迁移期安全网,注释标注 SITE-REAL-FALLBACK 待 Wave6
   收紧);品牌注入=layout 服务端取 site name/logo 渲染(现硬编码 Kokoro 处),按 host 切换。
   浏览器实走:hosts 别名两个域名(如 127.0.0.1 与 localhost 各绑一 site)→两品牌呈现;截图
   wave4-site-*。
4. session/agent 不动(site 传播沿 BFF 既有 x-kokoro-site-id 头;若测绘发现需改 session,停手报
   主控)。

## 验收

site 模块单测+集成只增不减(域名 CRUD/验证流转/resolve 只出 verified/未命中 404);web 三绿+
双域名浏览器实走截图;gate 回归绿(E2E-40 site 段不破;可加 resolve 断言一条:host 命中返 site_id)。
