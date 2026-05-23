# Kokoro · Variant C — 苔绿 + 米（自然调）

低保真静态 HTML 原型，服务"心"路线，C 套色板。**非生产代码**。

## 怎么看

直接在浏览器打开 `index.html`，不需要构建 / 服务器。Sidebar、chip、Canvas 卡都可点击跳到对应页。

## 4 个页面

| 页面 | 文件 | 对应文档 |
|---|---|---|
| 首屏（新对话） | `index.html` | `docs/product/06-screens/home.md` |
| 对话（含 Plan / Canvas 卡） | `chat.html` | `docs/product/06-screens/chat.md` |
| Canvas（Chat + Canvas 三栏） | `canvas.html` | `docs/product/06-screens/canvas.md` |
| 分享落地页 | `share.html` | `docs/product/06-screens/share.md` |

## C 套 token 实现

`styles.css` 头部把 `docs/product/05-design-system/tokens.md` 中"色板：候选 C — 苔绿 + 米"那一组 hex 全量落进 CSS 变量。关键值：

- `--color-bg #F7F4ED` · `--color-bg-subtle #EEEAE0`
- `--color-accent #6B7F5C`（苔绿） · `--color-accent-soft #DDE4D2`
- `--color-text-primary #2A2E26`（带绿调深灰）
- 圆角 24/16/8/4、阴影 ≤ `0 8px 32px rgba(45,50,35,0.05)`、动效 `cubic-bezier(0.16, 1, 0.3, 1)` 入场、loading 用 1.8s 呼吸而非 spinner

## 字体

system stack：`PingFang SC` 主体 + `Songti SC` serif（标题 / 引用）+ `Caveat / Kalam` 手写点缀（品牌副标 / 引导句 / 落款）。无需外网字体加载。

## 已知缺漏 / 没做的

- 暗色主题没做（tokens.md 还没拍）
- 没有交互逻辑（chip 都是装饰）
- 字体回退到 system，未必跟终态完全一致
- Canvas 文档区是单文档示例（信件），没演示海报 / 落地页类型

## 截图

`screenshots/` 下 4 张 PNG 是 Playwright 1440×900 截的视觉证据。
