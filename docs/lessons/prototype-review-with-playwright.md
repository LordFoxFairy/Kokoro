# 操作教训 · 用 Playwright 复查 variant-a-mi-mu 原型

## 1. 浏览器会缓存改过的 CSS / HTML，`browser_navigate` 同 URL 不重取

- **场景**：用 `python3 -m http.server` 起静态服，Playwright 反复 `navigate` 同一页验证改动。
- **做错的**：改了 `components.css` 和 `index.html` 后重新 `navigate`，页面纹丝不动，一度以为是 CSS 选择器/flex 没生效，连改三版才发现是 Chromium 拿了缓存（`getComputedStyle` 显示的还是旧规则）。
- **下次怎么避免**：
  - 改完先确认磁盘内容对（`grep` 文件 / 看 `curl -I` 的 `Last-Modified`），再排查渲染。
  - 强制重取：CSS 用 `link.href = href.split('?')[0] + '?v=' + Date.now()`；HTML 用 `navigate` 到 `page.html?v=N`（换 N）。
  - 关键改动别只信肉眼，用 `browser_evaluate` 读 `getComputedStyle` / 量 `getBoundingClientRect` 确认规则真的加载了。

## 2. flex 子项的 `aspect-ratio` 会被拉伸算法吃掉

- **场景**：想让 mindmap 的 board 用 `aspect-ratio: 5/3` 自定高度。
- **做错的**：在 `display:flex` 容器里给子项设 `aspect-ratio`，配 `flex:1`（甚至 `flex:none`）都没用，board 仍被撑满高度——尤其当它内部还有个 `height:100%` 的 svg，形成循环依赖，浏览器直接丢弃 aspect-ratio。
- **下次怎么避免**：
  - 让 **svg 自己定比例**：svg 有 `viewBox` 就有固有宽高比，设 `width:100%; height:auto` 它会自算高度，父 board `shrink-wrap` 即可，绕开 flex/aspect-ratio 冲突。
  - 通用：要"按比例定高"的盒子，优先靠"有固有比例的内容（img/svg/video）+ height:auto"，而不是在 flex 子项上硬套 `aspect-ratio`。

## 3. 数字与肉眼互相校验

- 第六轮有过"截了图就以为对"的教训；这轮反过来——肉眼觉得 mindmap"挤在顶部"，量了 `getBoundingClientRect` 才发现其实大致居中（205/231），真问题是**占比小**（内容仅占 board 高 36%）。先量再改，别凭印象下刀。
