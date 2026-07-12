# Wave 1 · CREDIT-CACHE 与 MODEL-SOURCE 子 spec(小项合册,分属两 worker)

状态:执行稿(上级=总设计稿 §6 Wave1-2/-8,已获批)

## CREDIT-CACHE(kokoro-platform 主树,先落)

现状缺陷(纲领 §2.3):owner 正缓存键=`ownerKind:ownerId`,缺 siteId——site A 暖缓存后,site B 同 owner id 复用 active 结果,跨站串。
改法:owner 缓存键改 `(siteId, ownerKind, ownerId)` 三元组;site 缓存键不变(本就 siteId)。
验收:既有 139+85 只增不减;新负向钉(纲领 §8.2-4):site A 对 (team,X) 暖缓存后,site B 同 (team,X) 必须重新出站校验且按 B 站结果裁决(fetch spy 断言二次出站+结果不串)。

## MODEL-SOURCE(kokoro-session)

现状缺陷:model 允许集三处漂移;profile.allowed 是硬闸而 platform resolve 才是可用性权威。
改法(D 系"单源"):
1. resolveRuntime 的 model_policy.allowed 降级为**展示/预选过滤**:不再作为受理硬拒绝依据——具体:billing 启用(shadow/enforce)时,选择子合法性以 platform resolve 结果为准(resolve 无绑定:enforce 拒 503(已落 M-1)/shadow 放行);billing off(纯 dev)保留 allowed 硬闸(无 platform 可询时的唯一防线)。
2. `model_not_allowed` 语义保留但只在 billing off 档触发;INDEX/注释写明"可用性权威=platform model resolve,profile.allowed=展示过滤+dev 兜底"。
验收:session 263 起点只增不减;新钉:billing shadow 下 allowed 外的选择子不再被 session 硬拒(交 resolve 裁决);billing off 下仍拒;既有断言不改(检查 e2e 的 model_not_allowed 断言是否 billing off 语境——是,gate 无 billing env,行为不变)。
