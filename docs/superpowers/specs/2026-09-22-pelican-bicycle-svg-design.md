# 鹈鹕自行车 SVG 2D 动画设计

## 目标

创建一幅 16:9、可循环播放的可爱扁平卡通 SVG：鹈鹕在画面中央骑自行车，背景持续向左滚动，形成向前行驶的视觉效果。成品应为单个自包含 SVG 文件，无 JavaScript 和外部资源依赖。

## 视觉方向

- 主角：奶油白鹈鹕、橙黄色长喙、蓝色头盔，表情轻松愉快。
- 自行车：珊瑚红车架、深蓝轮胎、浅色轮毂。
- 场景：晴朗海滨道路，包含天空、云朵、远海、草丛与道路标线。
- 风格：圆角造型、粗描边、明快低饱和配色、清晰前后层级。
- 画布：`viewBox="0 0 1280 720"`，保持 16:9 比例并支持响应式缩放。

## 构图与图层

从后到前组织为：天空、云朵、海面、远景灌木、道路、循环路面标线、自行车、鹈鹕、前景草叶。鹈鹕和自行车位于画面中央略偏右，确保长喙朝向右侧并留出运动方向空间。

每组图形使用语义化 `id`，包括 `background`, `clouds`, `road`, `road-marks`, `bicycle`, `pelican`, `foreground`，方便检查和后续调整。

## 动画方案

使用 SVG 内嵌 CSS `@keyframes`，不引入脚本：

| 元素 / id | 动画 | 周期 | 位移 / 旋转 | 缓动与相位 |
| --- | --- | --- | --- | --- |
| `front-wheel`、`rear-wheel` | `wheel-spin` | 1.2s | `0deg` → `360deg` | linear，同相 |
| `crank`、`feet` | `pedal-spin` | 1.2s | `0deg` → `360deg` | linear，同相 |
| `pelican-rider` | `rider-bob` | 0.6s | `translateY(0)` → `translateY(-5px)` | ease-in-out, alternate |
| `cloud-track` | `cloud-drift` | 24s | `translateX(0)` → `translateX(-1280px)` | linear |
| `shrub-track` | `shrub-scroll` | 12s | `translateX(0)` → `translateX(-1280px)` | linear |
| `road-mark-track` | `road-scroll` | 2.4s | `translateX(0)` → `translateX(-1280px)` | linear |
| `foreground-track` | `foreground-scroll` | 6s | `translateX(0)` → `translateX(-1280px)` | linear |

背景轨道各包含两份宽度恰好为 1280px 的相同单元，第二份从 `x=1280` 开始；动画恰好左移 1280px 后复位，因此循环边界的几何内容一致。道路标线单元使用固定间隔，并让首尾间距保持相同。

主体层级固定为：`bicycle` 位于下层；`pelican-rider` 位于上层并包含 `body`、`head`、`wing-handle`；`feet` 位于身体前方、曲柄后方。`front-wheel`、`rear-wheel` 的变换原点为各自圆心，`crank` 和 `feet` 的变换原点为曲柄轴心。`wing-handle` 不做独立旋转，其末端在静止姿态与车把锚点重合；5px 的整体起伏通过弯曲翅膀造型吸收，不产生明显脱手。

在 `@media (prefers-reduced-motion: reduce)` 中对所有带动画的元素设置 `animation: none !important`。减少动态效果时显示 CSS 动画定义前的静止首帧：车轮辐条竖直、曲柄水平、鹈鹕位于最低位置、背景轨道 `translateX(0)`。

## 技术边界

- 交付文件固定为 `/Users/nako/WebstormProjects/github/thefoxfairy/Kokoro/docs/prototypes/pelican-bicycle-animation.svg`。
- 单文件、有效 XML，可在现代浏览器直接打开。
- 不使用外链图片、字体、滤镜资源或 JavaScript。
- 通过 `transform-box` 与 `transform-origin` 控制局部旋转中心。
- 重复背景元素绘制两组相邻副本，位移一个完整周期后无缝回到起点。
- 使用 `<title>` 与 `<desc>` 提供基础可访问描述。
- 目标兼容范围为 Chrome 120+、Firefox 120+、Safari 17+。若宿主不支持 SVG 元素上的 CSS 动画或局部变换，首帧仍须作为完整静态插画显示。

## 验收标准

- SVG 能通过 `python3 -c "import xml.etree.ElementTree as E; E.parse('docs/prototypes/pelican-bicycle-animation.svg')"` 解析。
- 画布比例为 16:9，缩放时不变形。
- 鹈鹕、自行车、海滨道路在静态首帧中清晰可辨。
- 文件中存在 `front-wheel`、`rear-wheel`、`crank`、`feet`、`pelican-rider`、`cloud-track`、`shrub-track`、`road-mark-track`、`foreground-track`，并分别关联上表指定动画和周期。
- 在 0ms、1150ms、2350ms、5950ms、11950ms、23950ms 检查循环边界前的画面，不出现背景空白、明显接缝或主体跳动。
- 使用 Playwright Chromium 分别以默认动画和 `reducedMotion: 'reduce'` 打开本地 SVG；减少动态效果下等待 2 秒后，两次截图像素保持一致。
- 1280×720 浏览器截图确认主体没有裁切、错层、手脚脱离或旋转中心偏移；360×203 截图确认响应式缩放不变形。
- 静态降级验收通过禁用页面动画后截图完成；画面必须仍包含完整鹈鹕、自行车和背景。
