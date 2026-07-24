# Kokoro 产品能力盘点：有什么 / 缺什么 / 不足

状态：2026-07-24
量尺：**对着产品自己的愿景量**（handbook product/00：AI 产品工厂 = General Chat + 专业 Studio(音乐/视频/图片/代码) + 多站点，共享底座）。
方法：结论都落到代码事实；核过 workspace/project/风控/studio/媒体的真实存在性。

---

## 一句话诚实判断

**底座/管道是真强，但作为「产品」，Kokoro 现在≈"一个通用 Chat Agent + 一套平台机器"。**
产品愿景里那些**差异化、能付费**的东西（专业 Studio、媒体创作能力）、**组织纵深**（workspace/project）、
**连贯的商业**（套餐体系）、**运营产品**（admin 不只是 CRUD）、**增长引擎**——**要么没建，要么建了一半。**
按愿景算，产品实现度约 **20-30%**：地基和一楼（通用对话+平台机器）扎实，二楼以上（真正的差异化产品）基本空着。

---

## 逐域盘点

### 1. 入口 / 外壳 / 多站点
- **有**：落地页、magic-link 登录、多站点技术底座（siteId 隔离、域名绑定+一次性 TXT 验证、品牌注入、host→site 解析）、价格页。
- **缺**：真正的 onboarding（新用户"我能干什么"引导）、SEO/增长页（handbook 08 多为规划）、**运营侧"开一个新站点=上线一个新产品"的流程**（多站点是技术能力，不是可操作的产品）。
- **不足**：落地/营销单薄；多站点能隔离但没有"工厂"式的开站体验。

### 2. General Chat（已建的核心）
- **有**：对话 agent、流式、HITL、会话、产物卡、分享、模型下拉、fast/thinking、skills/MCP 面板。
- **缺**：空态引导、会话组织（按项目/主题）。
- **不足**：**能做多少全卡在模型上**（无生产真模型，dev 靠 8B）；对话跑通了，但"能力感"弱。

### 3. Agent 能力（agent 真正能"做"什么）
- **有**：文件读写、shell(execute)、web_search/web_fetch、memory、deliver(产物)、ask_user(HITL)、subagents/swarm、MCP 工具、skills、sandbox(state/local/docker)。
- **缺（大）**：**媒体生成——音乐/视频/图片/TTS 全零。** 产品叫"音乐/视频/图片/代码 AI 工厂"，但 agent 一个媒体能力都没有。**没有浏览器自动化**（只有 web_fetch）。**没有面向用户的"能力目录"**（用户看不到"我能调用什么"）。
- **不足**：web_search **默认关**（需配 provider）；memory **无向量语义检索**（退化为子串）；工具面是**码农 agent 形状**，不是创作产品形状。

### 4. Studio（差异化、可付费的产品）
- **有**：**几乎没有。** 只有 agent-type 脚手架（agents/__init__ 提到 studio 型但只注册了 general；namespace backend 提了一嘴）。
- **缺**：**全部 Studio**（音乐/视频/图片/代码工作台）、general→studio handoff、studio agent 型、studio UI、studio 参数/预览/版本/队列/导出、studio featureKey 计费。
- **不足**：这是**最大的产品缺口**——用户会掏钱的"专业创作"根本不存在。（注：媒体/Studio 是你有意暂缓的，但结果是：商业/能力机器在服务一个只建了 1/5 的产品。）

### 5. 产物 Artifacts
- **有**：跨会话产物聚合、内容寻址下载、产物卡网格、分享只读页、多媒体/HTML 预览。
- **缺**：**按 workspace/project/类型组织**（愿景要求，但 workspace/project 没建，见 §6）；产物**编辑/版本**（studio 级）；gallery/精选。
- **不足**：是一个扁平的"我的产出"列表，不是愿景描述的**有组织的产物库**。

### 6. 组织 Teams / Workspace / Project
- **有**：team（邀请/切换/成员管理）、namespace 隔离。
- **缺（结构性）**：**workspace 和 project 层完全没建**（核实：无 Workspace/Project 实体/schema）。愿景是 team→workspace→project 挂产物/协作/计费，现在只有最外层 team。
- **不足**：协作只到 team；组织纵深缺失，导致产物、计费、协作都少一层归属。

### 7. 模型 Models
- **有**：模型目录（label/binding/provider）、litellm 网关、多模型下拉、fast/thinking、内置 claude-code 门面。
- **缺**：**生产真模型**（卡在有效 key）；provider 凭据加密管理（现在走 env）；per-team/per-site 模型策略；模型档位↔订阅权益的映射。
- **不足**：实际只有一个内置 label 真能用；模型"分档"（免费=基础、订阅=高级）没接。

### 8. 商业 Commerce（积分/套餐/支付）
- **有**：credit ledger、hold/settle、quota、积分包、mock 支付、定价规则、admin 充值/改价。
- **缺**：**统一 Plan 模型**（刚设计，未建）、订阅生命周期、**权益层**、**每日积分赠送**、真支付网关（砍了）、USD 价值化定价、按模型消费分解。
- **不足**：现模型**自相矛盾**（我们正在修）；成本加成、¥ 计价；订阅名存实亡。

### 9. 运营 Admin / Ops
- **有**：三维 RBAC、maker-checker、DB 审计、manifest 驱动资源表、计费总览卡。
- **缺**：**真运营看板**（生意健康/转化漏斗/留存/营收）、运营工作流（不只是改表）、开站流程、**风控/内容审核（零实现，核实）**、客服/工单工具。
- **不足**：admin 是**通用 CRUD 数据库编辑器**，不是运营产品；独立栈(4290)未整合。

### 10. Web / 设计
- **有**：monorepo(user/admin)、暖纸感 token、i18n(9 语)、settings 浮层、canvas 三栏、rail、composer、主题、移动档。
- **缺**：General Chat 与 Studio 的连贯 IA（Studio 不存在）、studio UI、onboarding、**真正的共享设计系统**（@kokoro/ui 刚起壳）。
- **不足**：有设计语言但不成"系统"；admin 是 antd-Pro 通用脸；版本对齐了但设计没统一。

### 11. 增长 Growth / SEO / 多站点变现
- **有**：siteId、域名绑定、品牌注入、host 解析。
- **缺**：SEO 页、营销站生成、增长闭环、邀请/裂变、分析埋点、A/B。
- **不足**：多站点是技术能力，**不是增长产品**。

### 12. 底座 Infra / 可靠性 / 安全（机器——强）
- **有**：运行时可靠性脊柱(Wave2 R0-R7，chaos 验)、RS256/JWKS 认证、namespace/siteId 隔离、可观测(/metrics+/healthz)、部署(compose 真机验证+k8s 44 资源)、S3 存储、docker 沙箱。
- **缺**：生产真模型、tracing(V1 明确不做)、告警、备份策略、限流产品化。
- **不足**：曾有一批"默认 OFF"(billing/secret broker，已处理)；可观测只到 metrics，无 tracing/日志聚合。

---

## 贯穿结论

按"机器 vs 产品"两层看：

- **机器层（强）**：可靠性、隔离、认证、hub、credit 底座、部署、契约——世界级管道。
- **产品层（弱/缺）**：
  1. **差异化产品缺席**：Studio + 媒体能力 = 0（产品的付费理由）。
  2. **组织纵深缺失**：workspace/project 没建。
  3. **商业不连贯**：套餐体系自相矛盾（修中）。
  4. **运营非产品**：admin 是 CRUD。
  5. **增长为零**：多站点没变成增长引擎。
  6. **安全缺一块**：风控/审核零实现。

**根因**：反复打磨机器，"在机器之上设计产品"这一步系统性缺席。

---

## 诚实的优先级判断（供讨论，非定论）

1. **先决**：一把有效模型 key（否则一切"能力感"都虚）。
2. **产品身份**：确认近期是"通用 Chat Agent 产品"还是"向 Studio 铺路"——决定 §3/§4 怎么投。
3. **补组织纵深**：workspace/project（§6）——它承产物/计费/协作三样。
4. **商业连贯**：统一 Plan（已设计）落地（§8）。
5. **能力目录**：给用户"我能做什么"的可见能力面（§3）。
6. **风控**：上线前的合规底线（§9）。
7. **运营/增长/设计系统**：随产品成形逐步补。
