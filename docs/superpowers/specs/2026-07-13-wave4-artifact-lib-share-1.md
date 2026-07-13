# Wave 4 · ARTIFACT-LIB 与 SHARE-1 子 spec(同 lane 串行:都是 session+web 竖切,双仓单写者)

状态:执行稿(上级=总设计稿 §6 Wave4,已获批)。逐项独立 commit 独立验收。
契约(已冻结 62985d5):ArtifactRecord/ArtifactList + GET /artifacts + GET /artifacts/{content_hash};
POST|DELETE /sessions/{id}/share(shareReceiptSchema{share_id}) + GET /shared/{share_id}(复用
SessionSnapshot 形状)。

## ARTIFACT-LIB(跨会话作品库)

- session:GET /artifacts——属主 namespace 全部 deliveries 聚合(跨 session;同 content_hash 收敛
  一条取最近,session_id=最近交付归属),created_at desc,游标分页同 /sessions 模式;GET
  /artifacts/{content_hash}——冻结副本字节(deliveries/<namespace>/<content_hash> 内容寻址已在,
  delivery_content handler 逻辑复用),namespace 守门,跨 namespace 404。store 补跨会话读法
  (listDeliveriesByNamespace;deliveries 集合已有 namespace 维度?先测绘,缺 namespace 字段则加
  读路径回填——不改写既有行,读时经 sessions join 或补索引,方案自定但禁大迁移)。
- web:作品库页(rail 入口"作品";卡片网格 mime 图标/标题/时间/来源会话跳转;点击下载/预览;
  游标翻页;空态)。
- 浏览器实走:deliver 一个成果→作品库出现→另一会话再 deliver 同内容→仍一条;跨会话回跳;
  截图 wave4-artifacts-*。

## SHARE-1(可撤销只读分享)

- session:POST /sessions/{id}/share(同属主守门;share_id=shr_+随机 32hex,**存哈希不存原文**同
  invite token 模式;幂等:活跃分享重复创建返同 id——注意返原文 id 需可逆,故落库存原文亦可但集合
  加唯一索引与不可枚举随机性,权衡后自定并注释);DELETE 撤销(revoked_at 置位,公共读 404;再创建=
  新 id);GET /shared/{share_id}(**无 auth 公共面**:路由绕过 owner 守门但绝不绕过形状约束——
  返回 SessionSnapshot 形状,pending_pauses 恒 [],files 列表照返但 file 字节端点不开放公共面
  (V1 分享只读线程与成果,不开工作区文件下载;deliveries 冻结副本可下载——公共 delivery 下载面
  V1 不做,列表仅展示,注释说明);软删会话分享同步失效 404。
- web:会话头部"分享"按钮(创建→复制链接/撤销);公共页 /shared/[id](只读线程渲染,复用消息渲染件,
  无输入框无控制面;404 态)。
- 浏览器实走:分享→无痕窗口打开公共链接看到只读线程→撤销→刷新 404;截图 wave4-share-*。
- 负向:他人 session 创建分享 403;撤销后旧链接 404;share_id 不可枚举(随机性);软删会话 404。

## 验收

双项各自:session 全量只增不减三绿(含真 mongo 行为矩阵镜像);web 三绿;浏览器实走+截图;
gate 各加最小断言(artifacts 列表含 E2E-31 交付物+跨 namespace 404;share 创建→公共读 200→撤销
→404);全链 e2e 绿。
