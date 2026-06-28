# Artifact Job Result 链路

## 目标

管理生成产物的完整生命周期：创建（draft）-> 编辑 -> 发布（public URL 绑 canonical host）-> 查询（按 siteId + workspace 过滤）-> 删除（保留 usage/ledger 审计）-> 导出。全程 site scoped，公开产物绑定所属站点的 SEO。

## 参与模块

```text
kokoro-artifact                Project / Artifact / Asset / SeoPage 权威。
kokoro-session / job           生成产物，写 sourceJobId。
kokoro-site                    提供 canonicalHost 与 SiteSeoConfig（发布时）。
kokoro-credit                  保留 UsageRecord / ledger 用于审计（删除不抹除）。
```

## 前置条件

```text
SiteContext 已解析（siteId 确定）。
产物来自一次已结算的 job（sourceJobId 存在）。
发布需站点 seoPolicy 允许（indexable）。
```

## 主流程

```text
1. Create (draft)
   Artifact(siteId, workspaceId, projectId, appKey, artifactType, visibility=private,
            status=draft, sourceJobId)
   + Asset(siteId, artifactId, storageKey, mimeType, sizeBytes, checksum)。

2. Edit
   改 metadata / 重命名 / 换 Asset，仍按 siteId + workspaceId 归属。

3. Publish
   visibility private -> public/unlisted。
   public URL 只在所属 site 的 canonicalHost 下生成。
   按 SiteSeoConfig(routePattern) 生成 SeoPage（title/description/canonical/structuredData）。

4. Query
   列表/详情默认按 siteId + workspaceId 过滤；公开页按 siteId + visibility=public。

5. Delete
   Artifact status -> deleted（或软删），Asset 可回收；
   UsageRecord / CreditLedgerEntry 保留用于审计，不随产物删除。

6. Export
   按 Asset storageKey 导出原始文件。
```

## 异常流程

```text
跨站访问          site A 的 userId 查不到 site B 的 artifact（P6）。
未授权发布         站点 seoPolicy=noindex/private 时不生成可索引 SeoPage。
canonical 缺失     发布前 host 未绑定 canonicalHost -> 拒绝生成 public URL。
删除后审计         产物删除不抹除 UsageRecord/ledger，扣费记录可追溯。
```

## 数据变化

```text
Project           可新增（归集 artifact）。
Artifact          status draft -> published -> deleted；visibility private -> public/unlisted。
Asset             随创建/编辑新增或回收。
SeoPage           发布 public 时新增/更新（按 SiteSeoConfig）。
UsageRecord       不变（审计保留）。
CreditLedgerEntry 不变（审计保留）。
```

## 幂等和一致性

```text
siteId           第一过滤边界，所有读写第一条件。
sourceJobId      产物追溯到生成 job 与其 usage/ledger。
最终一致          provider callback -> job status -> artifact metadata -> web 刷新。
删除审计          产物可删，扣费与用量记录不可删，账务可追溯。
```

## 用户可见结果

```text
草稿      仅本人/workspace 可见。
发布      public URL 在站点主域名可访问，进入 SEO。
查询      只看到本站本 workspace 产物。
删除      产物消失，但后台 usage/账单仍可查。
导出      下载原始文件。
```

## 验收标准

```text
artifact 查询默认按 siteId + workspaceId。
public artifact URL 只在所属 site 的 canonicalHost 下生成。
site A 用户无法访问/导出 site B artifact。
删除产物后 UsageRecord / ledger 仍可追溯。
发布生成的 SeoPage 符合站点 SiteSeoConfig。
```

## 相关

```text
站点边界  ../decisions/ADR-001-site-boundary.md
站点解析  ./site-resolution.md
生成链路  ./music-studio-generate.md
模块     ../modules/kokoro-session.md
```
