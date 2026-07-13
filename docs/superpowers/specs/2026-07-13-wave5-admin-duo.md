# Wave 5 · admin 双项子 spec(ADMIN-MANIFEST / I18N-REVIVE;同 lane 串行,逐项独立 commit 独立验收)

状态:执行稿(上级=总设计稿 §6 Wave5,已获批)。仓面:kokoro-platform 的 admin 双件
(kokoro-platform-admin 网关 + kokoro-admin-web)与 kokoro-i18n;不碰主链仓。

## ADMIN-MANIFEST(manifest 元数据驱动页面)

- 现状:admin 网关 manifest(模块声明资源/动作)已在且动作路由已真(TEAM-1 时核过"点了即真");
  admin-web 页面仍硬编码 per-module。
- 目标:admin-web 列表/详情/动作面从 manifest 元数据渲染(资源表→通用列表页;动作→通用按钮+
  确认框+结果 toast;字段类型按 manifest 声明推断,声明缺的类型信息**补进 manifest 声明**而非
  前端硬编码猜)。硬编码页面凡 manifest 可表达的一律删除替换;确有专属交互的页(如审核 diff 视图)
  保留并在代码注释标注"manifest 外专属页"。
- 验收:admin-web 测试/构建净;至少两个模块(user 团队面/hub 审核面)经通用渲染实走截图
  wave5-admin-*;删除的硬编码页清单入 commit body。

## I18N-REVIVE(admin-web i18n + kokoro-i18n 复活)

- 现状:kokoro-i18n 死件;admin-web 无 i18n;主 web 有 zh/en 键体系(自维护)。
- 目标:kokoro-i18n 复活为共享 i18n 窄包(键值加载+插值+语言切换,不引重框架;若现存包骨架可用
  则修缮,烂了就按窄包重立);admin-web 接入(zh+en 全键,含 manifest 驱动页的动态键回退策略:
  manifest 字符串本身不翻,UI 骨架词翻);主 web 是否切换到共享包**本项不做**(避免动主链 web,
  留 Wave6 评估注记)。
- 验收:admin-web 双语切换实走截图;kokoro-i18n 包测试;硬编码中文串清扫清单。

## 总验收

admin 双件+i18n 包各自测试/构建只增不减;截图齐;主仓 e2e gate 回归绿(admin 面不在 gate 内,
应透明,收尾自跑一次)。
