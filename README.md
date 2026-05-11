# 长汉金属门官网

这是“长汉金属门”的商用金属门企业官网，包含首页、产品页、案例页、隐私政策、询盘表单和 Node.js 接口。

## 本地运行

先进入项目目录：

```bash
cd "/Users/chenyue/Documents/Codex/2026-05-10/1-hero-banner-2-3-4"
```

启动网站：

```bash
npm start
```

打开：

```text
http://localhost:3000/
```

## 推荐上线方式

建议先用 Cloudflare Pages 部署，适合当前项目：不用买服务器，静态页面速度快，并且可以通过 Pages Functions 接收询盘。

基本流程：

1. 把本项目上传到 GitHub。
2. 在 Cloudflare Pages 新建项目，并连接这个 GitHub 仓库。
3. 构建设置选择：

```text
Framework preset: None
Build command: 留空
Build output directory: .
```

4. 设置环境变量：

```text
INQUIRY_NOTIFY_PROVIDER=wecom
INQUIRY_WEBHOOK_URL=你的企业微信/飞书/CRM Webhook 地址
```

5. 部署成功后，Cloudflare 会生成一个 `*.pages.dev` 临时网址。
6. 购买域名后，在 Cloudflare Pages 里绑定自定义域名。

项目已提供 `functions/api/inquiries.js`，Cloudflare Pages 会自动把它作为 `/api/inquiries` 表单接口。

## 询盘接收

本地运行时，询盘默认保存到：

```text
data/inquiries.jsonl
```

Cloudflare Pages 上线时，建议使用 Webhook 接收询盘，例如企业微信、飞书、钉钉、Make/Zapier 或自建 CRM。

Cloudflare Pages 不会使用本地 `data/inquiries.jsonl` 存储客户信息，线上建议设置：

```text
INQUIRY_WEBHOOK_URL=你的 Webhook 地址
```

这样客户提交表单后，会直接推送到你的通知工具或 CRM。

如果线上没有配置 Webhook，表单会退回到邮件询盘草稿，避免客户填写的信息静默丢失。

## 上线前要换的内容

- `sitemap.xml` 和 `robots.txt` 里的正式域名
- 微信二维码图片：`assets/wechat-qr.webp`
- 真实公司地址、备案号、资质信息
- 真实项目案例图、工厂图和产品图
- 企业微信、飞书或 CRM Webhook
   
## 备选部署

项目也保留了 Node 版本的 `server.js`、`render.yaml` 和 `Dockerfile`。如果后期需要服务器长期存储询盘、接 CRM 数据库或做后台管理，可以再迁移到云服务器、Render、Railway 或 Docker 环境。

## 常用检查

```bash
npm run check
```

检查服务是否运行：

```text
http://localhost:3000/healthz
```
