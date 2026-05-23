---
status: 🟡 草稿
updated: 2026-05-20
---

# 交互模式（Patterns）

> 模式 = 比组件大、比页面小的复用块。
> 每个 pattern 包含：定义 / 触发场景 / 推荐 voice 范本 / 不该这样写。
> Voice 范本严格联动 [voice-and-tone.md](../02-personality/voice-and-tone.md)。

## 摘要

- 列出 9 个核心 pattern：empty / loading / error / success / confirmation / first-time / limit / undo / share。
- 每个 pattern 给"该这样 vs 不该这样"的对照 copy。
- 模式间共享底层动效（[motion.md](./motion.md)）和组件（[components.md](./components.md)）。

---

## 模式总表

| # | Pattern | 出现位置 | 关键组件 |
|---|---|---|---|
| 1 | Empty | 列表 / 库 / 模板库 / 最近 | Empty state |
| 2 | Loading | Streaming / Canvas 生成 / 网络请求 | Loading pulse |
| 3 | Error | 全局 / 内联 | Error toast / inline error |
| 4 | Success | 保存 / 复制 / 分享 / 完成 | inline 反馈 / toast |
| 5 | Confirmation | 删除 / 不可逆操作 | Modal / inline confirm |
| 6 | First-time | 首次进入 / 首次用新功能 | Empty state / 浮层提示 |
| 7 | Limit | 用量 / 模型限制 / 文件大小 | inline message / toast |
| 8 | Undo | 删除后 / 修改后 | Toast + 按钮 |
| 9 | Share | Canvas 产物分享 | Share button + 弹层 |

---

## 1. Empty

### 定义

列表 / 容器无内容时的占位状态。不只是"空"的展示，**也是引导用户开始的机会**。

### 触发场景

- 新用户首次进入「最近对话」
- 用户清空了所有对话
- 模板库无搜索结果
- 收藏夹空

### Voice 范本

| 场景 | ✅ 推荐 | ❌ 不要 |
|---|---|---|
| first-time 最近对话空 | "这里会装下你做过的东西。先聊一句？" | "暂无对话" / "Start your first chat!" |
| cleared 清空后 | "清空了，挺好。" | "您已删除所有对话" |
| filtered 无结果 | "这里没找到。换个词试试？" | "无搜索结果" / "Nothing matches" |
| 收藏空 | "还没收着什么。看到喜欢的就标一下。" | "Empty favorites" |

### 不该这样写

- 不用感叹号
- 不用「！」「~」「呀」
- 不放占位插画 / 卡通形象
- 不用强 CTA 按钮（"立即开始""马上试试"），用问句或邀请

---

## 2. Loading

### 定义

任何等待的视觉表达。**Kokoro 不让用户面对"沉默的等待"**，但也不用打扰式的进度展示。

### 触发场景

- Kokoro streaming 回复中
- Canvas 文档生成中
- 上传文件 / 网络请求
- 切换模型 / 加载历史对话

### Voice 范本

| 场景 | ✅ 推荐 | ❌ 不要 |
|---|---|---|
| streaming 短回复 | （无文字，只光标呼吸） | "Loading..." |
| streaming 长回复 / Canvas | "在想……" / "正在整理思路……" | "AI 正在生成回复，请稍候" |
| 上传文件 | "在读这个文件。" | "Upload 30%" |
| 较长任务（>10s） | "这件事我想得久一点，再等等。" | "处理中（已耗时 12 秒）" |
| 接力多阶段 | "先理清楚 → 再写 → 再润色。" | "Step 2 of 4" |

### 视觉

- 单点呼吸 / 三点接力 / 扫光（见 [motion.md](./motion.md)）
- 配文字时，文字本身不动，**只有 loading 指示器动**
- 不显示百分比、不显示已耗时数字

### 不该这样写

- 不用 spinner（任何形态）
- 不用 "Please wait" / "Loading"
- 不显示百分比（除非有真实进度，AI 任务通常没有）
- 不放 emoji 跳动占位

---

## 3. Error

### 定义

操作失败 / 系统异常的反馈。**承担 + 说清楚 + 给路径**。

### 触发场景

- 网络断连
- 保存失败
- API 限流 / 超时
- 用户输入无法解析
- 文件格式不支持

### Voice 范本

| 场景 | ✅ 推荐 | ❌ 不要 |
|---|---|---|
| 网络断 | "好像断网了。等连上再继续？" | "Network Error" |
| 保存失败 | "没保存上。要不要再试一次？" | "保存失败，错误码 503" |
| 限流 | "现在有点忙，给我半分钟。" | "Rate limit exceeded" |
| 输入无法解析 | "我没看懂这一步。可以再换句话告诉我吗？" | "Invalid input" |
| 文件不支持 | "这个格式我读不了。换成 PDF 或图片可以试试。" | "Unsupported file format" |
| 服务挂了 | "我这边出了点问题。已经在看了。" | "Internal Server Error" |

### 视觉

- 非阻塞：底部 Error toast（暖陶土 danger 色）
- 阻塞：inline error 直接展示在出错位置
- 永远附带**重试 / 撤销 / 改一改**入口

### 不该这样写

- 不用 "Error" / "Oops" / "Something went wrong"
- 不显示错误码（除非用户主动展开"详情"）
- 不甩锅给用户（"您输入有误"）
- 不用正红 #FF0000

---

## 4. Success

### 定义

操作完成后的反馈。**平静地说做完了，不邀功**。

### 触发场景

- 保存成功
- 复制链接成功
- 分享发出成功
- Canvas 生成完成

### Voice 范本

| 场景 | ✅ 推荐 | ❌ 不要 |
|---|---|---|
| 保存 | "存好了。" / 按钮文字变 "存好了 ✓" | "保存成功！🎉" |
| 复制链接 | "复好了。" / 按钮变 "复好了 ✓" | "已复制到剪贴板！" |
| 分享发出 | "发出去了。" | "分享成功 🎉" |
| Canvas 完成 | "做好了。看看？" | "🎉 文档已生成！" |

### 视觉

- **不弹大 toast，不撒花，不打勾跳动**
- 按钮文字短暂变化 1.5s 再回弹（"复制" → "复好了 ✓" → "复制"）
- 必要时底部小 toast（无图标，纯文字 + 可选 undo）

### 不该这样写

- 不用 🎉 / ✨ / 🎊
- 不用感叹号
- 不用"恭喜"/"完美"/"棒"等自夸 / 夸用户词

---

## 5. Confirmation

### 定义

不可逆操作前的二次确认。**少用**——能 undo 的就不要 confirm。

### 触发场景

- 删除对话 / 删除 Canvas 产物
- 退出未保存
- 清空全部历史
- 取消订阅

### Voice 范本

| 场景 | ✅ 推荐 | ❌ 不要 |
|---|---|---|
| 删除对话 | 标题："要删掉这个对话？" 正文："删了就找不回了。" 按钮：[删掉] [先留着] | "确认删除此对话？此操作不可撤销。" + [确定][取消] |
| 退出未保存 | 标题："还没存就走？" 正文："这部分我先帮你留着。" 按钮：[存一下] [不存了] | "您有未保存的更改" + [Save][Discard] |
| 清空全部 | 标题："全清掉？" 正文："这一步我不能 undo。" 按钮：[清掉] [算了] | "确定要删除全部历史记录吗？" |

### 视觉

- 居中 modal，shadow-lg
- 危险操作按钮用 danger 色但**不加粗 / 不放大**（颜色就够了）
- 取消按钮是次按钮（无填充），不是 ghost

### 不该这样写

- 不用「您」「确定」「取消」这类正式 / 冷感词
- 不用"此操作不可撤销"标语，用「删了就找不回了」
- 不要为可 undo 的操作弹 confirm（直接做 + 提供 undo）

---

## 6. First-time

### 定义

用户首次进入产品 / 首次接触某功能时的引导。**邀请式，不是教学式**。

### 触发场景

- 首次登录
- 首次进入 Canvas
- 首次进入模板库
- 首次使用某个新功能

### Voice 范本

| 场景 | ✅ 推荐 | ❌ 不要 |
|---|---|---|
| 首次登录 | "今天想做什么？" + 输入框 + 5 个 chip | "Welcome to Kokoro! Let's get started." + 多步引导 |
| 首次进入 Canvas | "右边这块是 Canvas，我会把要慢慢做的东西放这。" | "This is the Canvas panel where you can edit documents..." |
| 首次进入模板库 | "挑一个开始，或者自己想一个。" | "Choose from our curated templates!" |
| 首次分享 | "分享后，对方点进来看到的就是 Kokoro 的样子。" | "Click here to share with friends!" |

### 视觉

- 不用 onboarding 多步骤 modal / tour
- 引导文字直接出现在该位置（**就地引导**），不用箭头 / 高亮覆盖
- 用户随时可跳过 / 直接动手

### 不该这样写

- 不做"5 步教程"
- 不用「点击这里」「向下滑动」这类指令式
- 不用感叹号 / emoji 堆叠
- 不要求用户填写 profile / 偏好（除非真的必要）

---

## 7. Limit

### 定义

用户碰到限制时的提示（用量 / 模型能力 / 文件大小）。**不掩饰，不甩锅，给路径**。

### 触发场景

- 免费额度用完
- 文件超过大小限制
- 模型暂不支持某能力（如打开摄像头）
- 内容超长无法一次处理

### Voice 范本

| 场景 | ✅ 推荐 | ❌ 不要 |
|---|---|---|
| 免费额度用完 | "今天的额度用完了。明天再聊，或者升级可以接着用。" | "您已达使用上限，请立即升级！" |
| 文件太大 | "这个文件大了点（>20MB）。能不能压一下再传？" | "File size exceeds limit" |
| 能力不支持 | "我目前还不能帮你打开摄像头。" | "This feature is not available" |
| 内容超长 | "这一段太长了我吃不下。要不要分两次给我？" | "Input exceeds maximum length of 32000 tokens" |
| 没把握 | "这块我没把握做对，要不要先放一下？" | "无法处理此请求" |

### 视觉

- inline 出现在相关位置，不弹全屏
- 永远给**替代路径**（"明天""压一下""分两次""先放一下"）
- 升级 CTA 用次按钮，**不放大 / 不闪烁 / 不催**

### 不该这样写

- 不用「立即升级」「马上解锁」
- 不用"权限不足"/"未授权"这类法律感词
- 不显示技术错误（token 数 / 文件字节数）

---

## 8. Undo

### 定义

用户操作后给的"反悔机会"。**Kokoro 优先 undo 而不是 confirm**。

### 触发场景

- 删除对话 / 删除消息
- 清空模板
- 删除收藏
- 关闭 Canvas（未保存改动）

### Voice 范本

| 场景 | ✅ 推荐 | ❌ 不要 |
|---|---|---|
| 删除一条 | "删掉了。  [撤回]" | "Item deleted. [Undo]" |
| 清空模板 | "清空了。  [恢复]" | "Cleared. Click to restore." |
| 关闭未存 Canvas | "先存了一份草稿，要找的话在「库」里。" | "Auto-saved as draft" |

### 视觉

- 底部 toast，自动消失 6s（比普通 toast 长，给反悔时间）
- 按钮文字用"撤回"/"恢复"/"找回"，不用"undo"
- toast hover 时**暂停倒计时**

### 不该这样写

- 不用「您已删除…」
- 不在 toast 上加表情 / emoji
- 不要在不可 undo 的操作上假装有 undo（明确告知）

---

## 9. Share

### 定义

把 Canvas 产物分享出去。**这是 Kokoro 的核心增长入口**——分享出去的产物 = Kokoro 的名片。

### 触发场景

- Canvas 产物做好后
- 用户点 Share 按钮
- 用户右键 / 长按产物

### Voice 范本

| 场景 | ✅ 推荐 | ❌ 不要 |
|---|---|---|
| 分享弹层标题 | "分享这个" | "Share this artifact" |
| 复制链接副标 | "对方点开就能看到。" | "Anyone with the link can view" |
| 下载图片副标 | "存到本地，发朋友圈用。" | "Download as PNG image" |
| 复制成功反馈 | 按钮变"复好了 ✓"，1.5s 后回弹 | toast "Link copied to clipboard!" |
| 分享落地页标语 | "这是用 Kokoro 做的。" | "Created with Kokoro AI" |

### 视觉

- Share 按钮在 Canvas 顶栏一等公民（不藏菜单）
- 弹层结构：链接 / 下载图片 / 下载 PDF / 发到平台
- 落地页：产物本身 + 极小 Kokoro 角标 + "你也试试" 入口（不喧宾夺主）
- OG 图自带 Kokoro 视觉印记（见 [components.md](./components.md) OG image）

### 不该这样写

- 不要在分享页面催「立即注册」
- 不在 OG 图上写"由 AI 生成"标识
- 不用 "Powered by"，用 "by Kokoro" 或 "这是用 Kokoro 做的"

---

## 待你拍板

- [ ] Confirmation pattern 用得有多严？现在写的是"能 undo 就不 confirm"，但删除对话这种操作是否还是该 confirm 一下？
- [ ] First-time 真的不做 onboarding 多步引导吗？数据上引导用户激活第一次产出是关键，纯邀请式可能转化偏低
- [ ] Limit 中的升级 CTA 克制到什么程度？太克制可能影响付费转化
- [ ] Share 落地页"你也试试"入口的视觉权重？太弱拉不来人，太强又破坏产物本身的克制感

## 关联

- [voice-and-tone.md](../02-personality/voice-and-tone.md) — 所有 copy 的语气源
- [components.md](./components.md) — 模式用到的组件
- [motion.md](./motion.md) — 状态切换的动效
- [tokens.md](./tokens.md) — 色 / 圆角 / 间距
- [07-growth/sharing-first-class.md](../07-growth/sharing-first-class.md) — Share pattern 的增长意图
