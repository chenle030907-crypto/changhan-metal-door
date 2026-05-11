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

建议先用 Render 或 Railway 这类 Node 云平台部署，适合当前项目：不用买服务器，也不用自己配置 Nginx。

基本流程：

1. 把本项目上传到 GitHub。
2. 在 Render / Railway 新建 Node Web Service，并选择这个 GitHub 仓库。
3. 启动命令使用 `npm start`。
4. 设置环境变量：

```text
HOST=0.0.0.0
NODE_VERSION=20
PERSIST_INQUIRIES=false
INQUIRY_NOTIFY_PROVIDER=wecom
INQUIRY_WEBHOOK_URL=你的企业微信/飞书/CRM Webhook 地址
```

5. 部署成功后，平台会生成一个临时网址。
6. 购买域名后，在平台里绑定自定义域名，再按平台提示添加 DNS 解析。

项目已提供 `render.yaml`，在 Render 里可以直接按 Blueprint 方式识别部署配置。

## 询盘接收

本地运行时，询盘默认保存到：

```text
data/inquiries.jsonl
```

云平台上线时，建议使用 Webhook 接收询盘，例如企业微信、飞书、钉钉、Make/Zapier 或自建 CRM。

原因是很多云平台的本地文件不是长期稳定存储，服务重启后可能丢失。线上建议设置：

```text
PERSIST_INQUIRIES=false
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

## 常用检查

```bash
npm run check
```

检查服务是否运行：

```text
http://localhost:3000/healthz
```
