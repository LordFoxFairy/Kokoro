# 站点、工作空间、项目和协作

## Site

Site 是第一业务隔离边界。一个站点代表一个独立 AI 产品实例。

```text
siteId 隔离：
  用户
  套餐
  积分
  SEO
  品牌
  模型可见性
```

同邮箱跨站默认是不同用户。多站点形态见 [08-multi-site-seo-growth](08-multi-site-seo-growth.md)。

## Workspace / Team

Workspace/Team 是站点内协作边界，不跨站共享。

```text
Site
  User
  Workspace/Team
    Membership
    Role
    Project
    CreditAccount
    Subscription
```

## Project

Project 是创作对象的组织单位。

```text
General Project  对话、文档、任务、产物混合。
Music Project    歌曲、歌词、音频版本。
Video Project    素材、脚本、镜头、导出。
Image Project    prompt、图片、变体、批量结果。
Code Project     repo、任务、patch、运行结果。
```

## 用户视角

用户不应看到太多抽象名词。推荐表达：

```text
站点   当前产品。
空间   个人空间 / 团队空间。
项目   一组相关创作。
产物   已生成可复用结果。
```

## 权限

权限默认站点内生效：

```text
owner
admin
member
viewer（后续可选）
```

platform root admin 可跨站查看，但必须是后台能力，不影响普通用户。

## 设计红线

```text
不做全局 email 唯一。
不默认跨站共享 workspace。
不默认跨站共享积分。
不让 team 成为比 site 更外层的业务边界。
不把 project 做成所有模块都能随便写的公共表。
```
