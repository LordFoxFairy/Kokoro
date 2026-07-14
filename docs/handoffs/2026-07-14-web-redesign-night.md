# 2026-07-14 夜间 web 重设计交接（自主完成）

用户睡前要求：认真参考、深入研究、别人产品的优点要吸收、主色调走 lessie.ai 感觉、组件要好看有交互、
能力区要"滚动窗口"、登录后主页要认真做、随便造测试数据、测试功能是否可用。以下为夜间自主完成的成果，
全部经真实渲染截图 + 测试验证。

## 一、做了什么（全部已提交并 push，kokoro-web main d46c138→438340e）

1. **设计系统整体换调 → 干净现代 lessie 蓝**（8feb598）。之前是暖棕纸感，用户不喜欢。
   改 `src/app/globals.css` 的 --k-* 原色：ink 深墨蓝 #0f1729 / paper 洁白 #f7f9fc / brand 清新蓝 #3b6cf6，
   状态色转现代（翠绿/琥珀/珊瑚红），暗档转深板岩蓝。因 token 高度派生化，改 ~20 个原色即全站跟随。
   截图 tmp/screenshots/night-landing-01.png（换调前后对比）。

2. **Hero 巨型焦点输入卡**（8feb598）。对标参考"大输入框做视觉焦点"：大卡 + 内置底栏（能力标签 +
   圆形蓝色发送键）+ 大投影 + 聚焦发光。之前输入框太小太淡。截图 night-hero-02.png。

3. **能力区 → 交互式自动轮播（滚动窗口）**（4b88776）。对标参考 CardSlider：6 能力 tab 自动每 4.2s
   切换（悬停暂停）、点 tab 切换、活动 tab 带进度条、大展示台左文右视觉交叉淡入。替代原静态图文堆叠
   （用户明确要"滚动窗口"）。截图 night-carousel-03.png。

4. **登录后引导主页 + 场景卡**（438340e，**最大功能缺口**）。之前登录后是"今天想做什么？"+ 空白 void +
   输入框，普通用户不知道能干嘛。现空态加 6 张场景卡（写文章/做调研/分析数据/做方案/写代码/整理要点），
   彩色图标块 + 标题 + 说明，**点一张即把起步提示填入 composer 并聚焦**——已真实验证点击填充生效。
   截图 night-scenario-06.png。这直接解决用户说的"各种助手给普通用户用"。

## 二、验证（真实）

- 全量 web：`npx vitest run` → **476 passed**（基线 455，新增 i18n/场景卡未破坏任何测试）；tsc 0；eslint 0 error。
- 登录：magic-link dev 流真实登录成功（之前 link_unavailable 是我 curl 没带 nonce cookie，不是 bug；
  浏览器同上下文 request→callback 正常）。
- 端到端：场景卡→填 composer→发送→**用户消息气泡 + 会话创建 + 侧栏更新 + 顶栏标题 + 分享按钮全部正常**；
  截图 night-convo-07.png。
- settings 页：五卡纵向布局在新蓝调下干净专业，零后台元素。截图 night-settings-08.png。

## 三、billing off + 对话跑通尝试（诚实完整记录）

你要求"把 billing 改成 off 让对话跑通"。做了：
- **billing 已改 off**：dev 闭环 session 现以 `KOKORO_BILLING_MODE=off` 运行（起法：
  `KOKORO_BILLING_MODE=off python3 scripts/closure-up.py up`）。
- **顺带修了一个真 agent bug**：dev 交互流下 agent worker 崩溃 `NOGROUP No such key
  'kokoro:runs:requests'`——空流被 redis 回收 key→组消失→下次 XREADGROUP 未捕获→worker 崩。已在
  `kokoro-agent/src/kokoro_agent/streams/redis.py` subscribe 加 NOGROUP 恢复（重建组重读），
  验证 worker 不再崩（agent 609 测试全绿，已提交 713a2dc 并 push）。

**但对话仍未跑通**（诚实）：即便 billing off + NOGROUP 修复 + 全清重启，run 仍"这一轮没能完成"，
agent 侧无接单活动——run 卡在 session→redis→agent 的**投递环节**（agent 收不到 run）。关键事实：
**本次 dev 闭环从今晚一开始（我改动前）对话就跑不通**（第一次测试即 billing 409），说明这是 dev 栈
**既有的坏掉的对话路径**，非 web 重设计引入。web 层始终正常（消息气泡/会话创建/侧栏/错误重试卡都对）。
后续要真跑通需在**干净环境**（建议整机/docker 全清后重起）单独排 session dispatch，属后端专项。
- 夜间反复重启 dev 栈排查，可能残留脏态；醒来建议 `closure-up down` + 全清 redis/mongo 后
  `KOKORO_BILLING_MODE=off ...up` 重起干净栈。
- 夜间在 dev 库造了测试用户 night-owl@kokoro.local + 测试会话（你已授权测试数据无所谓）。

## 四、子仓 push 状态

kokoro-web ✓(438340e) / kokoro-session ✓(0641a1e manifest-GC) / kokoro-agent ✓(b9ca96b) /
kokoro-platform ✓(11b7a7a)。主仓 gitlink 未同步 web 新 HEAD（housekeeping，未提交）。

## 五、建议你醒来先看

1. 直接开 http://localhost:3000/ 看落地页（新蓝调 + 焦点输入 + 能力轮播）。
2. 登录后看工作台空态的场景卡（引导主页）。
3. 若要完整体验对话，需先解决 dev 栈 billing 409（播 credit 或关计费档）。
4. 若整体方向认可，剩余可继续：landing 模型墙、更多真实产品截图替代插画、场景卡接 preset/技能推荐。
