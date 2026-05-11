# 长汉金属门官网部署说明

## 本地运行

如果使用 `.env.example`，可以复制一份 `.env` 并按需填写。当前服务不依赖第三方包，不会自动读取 `.env` 文件；本地测试环境变量时可在命令前传入，例如：

```bash
INQUIRY_NOTIFY_PROVIDER=wecom INQUIRY_WEBHOOK_URL=https://your-webhook-url npm start
```

```bash
npm start
```

打开：

```text
http://localhost:3000
```

使用 `file://` 直接打开页面时，询盘表单会自动生成邮件草稿。通过 `npm start` 或线上 Node 服务访问时，表单会提交到 `/api/inquiries`。

## 局域网访问

`localhost` 只代表当前电脑。手机或另一台电脑不能用 `localhost:3000` 访问你的电脑，需要使用启动日志里打印的局域网地址，例如：

```text
http://192.168.1.23:3000/
```

要求：

- 访问设备和你的电脑在同一个 Wi-Fi / 局域网。
- 终端中的 `npm start` 服务保持运行。
- 如果 macOS 弹出“是否允许 Node 接受传入连接”，请选择允许。
- 如果仍然打不开，检查系统防火墙是否阻止 Node.js。

默认监听地址为 `0.0.0.0`，允许局域网设备访问。如需修改：

```bash
HOST=0.0.0.0 PORT=3000 npm start
```

如果要让外网客户访问，需要部署到 Cloudflare Pages、云服务器、Render/Railway 等平台，或使用 Cloudflare Tunnel/ngrok 这类隧道服务，并绑定正式域名。

## 询盘数据

有效询盘会写入：

```text
data/inquiries.jsonl
```

每一行是一条 JSON 数据，包含姓名、电话、城市、数量、项目类型、工期阶段、项目说明和提交时间。该文件包含客户信息，不要提交到公开仓库。

如需把数据写到服务器上的指定目录，可设置：

```bash
DATA_DIR=/var/www/changhan-data
```

## Webhook 转发

如需将询盘同步到企业微信、飞书、钉钉、CRM 或自动化平台，可以配置：

```bash
INQUIRY_WEBHOOK_URL=https://your-webhook-url
INQUIRY_NOTIFY_PROVIDER=wecom
```

`INQUIRY_NOTIFY_PROVIDER` 可选：

- `generic`：发送完整 JSON，适合自建 CRM、Make、Zapier、自定义接口
- `wecom`：企业微信机器人 markdown 格式
- `feishu`：飞书机器人 text 格式
- `dingtalk`：钉钉机器人 text 格式

正式上线前建议接入企业微信或飞书机器人，避免只依赖本地文件。

## 防垃圾提交

后端已包含两层基础防护：

- 表单隐藏字段蜜罐：普通用户不可见，机器人填写后会被拒绝。
- IP 频率限制：默认 10 分钟内最多 8 次提交。

可通过环境变量调整：

```bash
RATE_LIMIT_WINDOW_MS=600000
RATE_LIMIT_MAX=8
```

## 上线前替换

正式上线前建议替换以下内容：

- `robots.txt` 和 `sitemap.xml` 中的域名 `https://www.changhan-door.com/`
- 微信二维码图片 `assets/wechat-qr.webp`，也可同时替换源文件 `assets/wechat-qr.png`
- 真实公司地址、备案号、营业执照或资质信息
- 真实项目案例照片和工厂照片
- 当前页面已优先使用 WebP 图片；后续替换真实照片时建议继续输出 WebP/AVIF 多尺寸版本

## 推荐部署方式

这个项目不依赖第三方 Node 包，可以部署到支持 Node 18+ 的服务器或平台。若只部署为纯静态站，询盘接口不可用，但邮件草稿兜底仍可工作。

优先推荐：

- Cloudflare Pages：适合先免费上线，静态页面速度快，并可用 Pages Functions 接收询盘。
- Render / Railway：适合需要长期 Node 服务时使用，自动读取 GitHub 仓库并运行 `npm start`。
- 云服务器 + Docker：适合后期更稳定运营，可自行配置 Nginx、HTTPS、日志和备份。
- 国内大陆服务器：若绑定大陆域名并面向国内公开访问，通常需要先完成 ICP 备案。

## Cloudflare Pages 免费上线

项目已加入 Cloudflare Pages 所需文件：

- `functions/api/inquiries.js`：线上询盘接口
- `functions/healthz.js`：健康检查
- `wrangler.toml`：Cloudflare Pages 配置
- `_headers`：基础安全头与静态资源缓存
- `_routes.json`：只让 `/api/*` 和 `/healthz` 调用 Functions，页面和图片保持静态访问

操作步骤：

1. 登录 Cloudflare。
2. 进入 Workers & Pages。
3. 选择 Create application。
4. 选择 Pages，再选择 Connect to Git。
5. 授权 GitHub，并选择仓库 `chenle030907-crypto/changhan-metal-door`。
6. 构建设置填写：

```text
Framework preset: None
Build command: 留空
Build output directory: .
```

7. 添加环境变量：

```text
INQUIRY_NOTIFY_PROVIDER=wecom
INQUIRY_WEBHOOK_URL=你的企业微信/飞书/CRM Webhook 地址
```

8. 点击 Deploy。

部署成功后，会得到一个类似下面的临时网址：

```text
https://changhan-metal-door.pages.dev
```

确认首页、产品页、案例页、联系表单都正常后，再绑定正式域名。

如果暂时没有配置 `INQUIRY_WEBHOOK_URL`，表单接口会返回失败，前端会自动生成邮件询盘草稿，客户信息不会静默丢失。

## Render 快速上线

Render 现在可作为备选方案。项目已加入 `render.yaml`，可以用 Blueprint 部署。

操作步骤：

1. 注册 GitHub，并把本项目上传为一个仓库。
2. 登录 Render，选择 New Blueprint 或 New Web Service。
3. 连接这个 GitHub 仓库。
4. 使用默认配置部署，启动命令为：

```bash
npm start
```

5. 配置环境变量：

```text
NODE_VERSION=20
HOST=0.0.0.0
PERSIST_INQUIRIES=false
INQUIRY_NOTIFY_PROVIDER=wecom
INQUIRY_WEBHOOK_URL=你的企业微信/飞书/CRM Webhook 地址
```

`PERSIST_INQUIRIES=false` 适合云平台：客户提交后必须推送到 Webhook；如果 Webhook 未配置或失败，前端会自动生成邮件询盘草稿，避免客户信息静默丢失。

部署成功后，Render 会给一个临时域名。确认网站可访问、表单可提交后，再绑定正式域名。

## 绑定域名

上线平台生成临时网址后，再做域名绑定：

1. 购买域名，例如 `changhan-door.com`。
2. 在 Render / Railway 里添加 Custom Domain。
3. 按平台提示到域名服务商后台添加 DNS 记录，通常是 `CNAME` 或 `A` 记录。
4. 等待 DNS 生效和 HTTPS 证书签发。
5. 把 `robots.txt` 和 `sitemap.xml` 里的示例域名替换为正式域名。

如果你希望客户直接访问中文品牌域名，也可以购买拼音、英文或行业关键词相关域名，例如 `changhan-door.com`、`changhanmetaldoor.com` 这类。

## Docker 部署

项目已加入 `Dockerfile`，后续上云服务器时可用：

```bash
docker build -t changhan-metal-door .
docker run -d --name changhan-metal-door -p 3000:3000 \
  -e HOST=0.0.0.0 \
  -e INQUIRY_NOTIFY_PROVIDER=wecom \
  -e INQUIRY_WEBHOOK_URL=https://your-webhook-url \
  changhan-metal-door
```

如果正式使用云服务器，建议再配置 Nginx 反向代理、HTTPS 证书和日志备份。
