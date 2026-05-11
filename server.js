const crypto = require("node:crypto");
const fs = require("node:fs");
const fsp = require("node:fs/promises");
const http = require("node:http");
const os = require("node:os");
const path = require("node:path");

const root = __dirname;
const dataDir = process.env.DATA_DIR || path.join(root, "data");
const inquiryFile = path.join(dataDir, "inquiries.jsonl");
const port = Number(process.env.PORT || 3000);
const host = process.env.HOST || "0.0.0.0";
const rateLimitWindowMs = Number(process.env.RATE_LIMIT_WINDOW_MS || 10 * 60 * 1000);
const rateLimitMax = Number(process.env.RATE_LIMIT_MAX || 8);
const persistInquiries = process.env.PERSIST_INQUIRIES !== "false";
const rateLimitStore = new Map();

const mimeTypes = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".webp": "image/webp",
  ".svg": "image/svg+xml",
  ".txt": "text/plain; charset=utf-8",
  ".xml": "application/xml; charset=utf-8",
};

function sendJson(response, statusCode, payload) {
  response.writeHead(statusCode, {
    "Content-Type": "application/json; charset=utf-8",
    "Cache-Control": "no-store",
  });
  response.end(JSON.stringify(payload));
}

function sanitizeText(value, maxLength = 500) {
  return String(value || "")
    .replace(/\s+/g, " ")
    .trim()
    .slice(0, maxLength);
}

function validateInquiry(payload) {
  const inquiry = {
    id: crypto.randomUUID(),
    createdAt: new Date().toISOString(),
    name: sanitizeText(payload.name, 80),
    phone: sanitizeText(payload.phone, 80),
    city: sanitizeText(payload.city, 80),
    quantity: sanitizeText(payload.quantity, 80),
    project: sanitizeText(payload.project, 120),
    stage: sanitizeText(payload.stage, 120),
    message: sanitizeText(payload.message, 1200),
    source: "website",
  };

  const errors = [];
  if (sanitizeText(payload.company_site, 120)) errors.push("spam detected");
  if (!inquiry.name) errors.push("name is required");
  if (!inquiry.phone) errors.push("phone is required");
  if (!inquiry.project) errors.push("project is required");
  if (inquiry.phone && !/^[0-9+\-\s()]{6,30}$/.test(inquiry.phone)) {
    errors.push("phone is invalid");
  }

  return { inquiry, errors };
}

function getClientIp(request) {
  const forwardedFor = request.headers["x-forwarded-for"];
  if (forwardedFor) return forwardedFor.split(",")[0].trim();
  return request.socket.remoteAddress || "unknown";
}

function isRateLimited(request) {
  const now = Date.now();
  const clientIp = getClientIp(request);
  const record = rateLimitStore.get(clientIp) || { count: 0, resetAt: now + rateLimitWindowMs };

  if (now > record.resetAt) {
    record.count = 0;
    record.resetAt = now + rateLimitWindowMs;
  }

  record.count += 1;
  rateLimitStore.set(clientIp, record);

  return record.count > rateLimitMax;
}

async function readRequestJson(request) {
  const chunks = [];
  let size = 0;

  for await (const chunk of request) {
    size += chunk.length;
    if (size > 1024 * 64) {
      throw new Error("payload too large");
    }
    chunks.push(chunk);
  }

  const body = Buffer.concat(chunks).toString("utf8");
  return body ? JSON.parse(body) : {};
}

function buildInquiryText(inquiry) {
  return [
    "长汉金属门新询盘",
    `姓名：${inquiry.name || "未填写"}`,
    `电话：${inquiry.phone || "未填写"}`,
    `城市：${inquiry.city || "未填写"}`,
    `数量：${inquiry.quantity || "未填写"}`,
    `项目类型：${inquiry.project || "未选择"}`,
    `工期阶段：${inquiry.stage || "未选择"}`,
    `项目说明：${inquiry.message || "未填写"}`,
    `提交时间：${inquiry.createdAt}`,
  ].join("\n");
}

function buildWebhookPayload(inquiry) {
  const provider = String(process.env.INQUIRY_NOTIFY_PROVIDER || "generic").toLowerCase();
  const text = buildInquiryText(inquiry);

  if (provider === "wecom" || provider === "wechat-work" || provider === "enterprise-wechat") {
    return {
      msgtype: "markdown",
      markdown: {
        content: text
          .split("\n")
          .map((line, index) => (index === 0 ? `**${line}**` : `> ${line}`))
          .join("\n"),
      },
    };
  }

  if (provider === "feishu" || provider === "lark") {
    return {
      msg_type: "text",
      content: {
        text,
      },
    };
  }

  if (provider === "dingtalk" || provider === "ding") {
    return {
      msgtype: "text",
      text: {
        content: text,
      },
    };
  }

  return inquiry;
}

async function forwardWebhook(inquiry) {
  if (!process.env.INQUIRY_WEBHOOK_URL) return false;

  const response = await fetch(process.env.INQUIRY_WEBHOOK_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(buildWebhookPayload(inquiry)),
  });

  if (!response.ok) {
    throw new Error(`webhook failed with ${response.status}`);
  }

  return true;
}

async function saveInquiry(inquiry) {
  if (!persistInquiries) return false;

  await fsp.mkdir(dataDir, { recursive: true });
  await fsp.appendFile(inquiryFile, `${JSON.stringify(inquiry)}\n`, "utf8");
  return true;
}

async function handleInquiry(request, response) {
  try {
    if (isRateLimited(request)) {
      sendJson(response, 429, { ok: false, error: "Too many submissions" });
      return;
    }

    const payload = await readRequestJson(request);
    const { inquiry, errors } = validateInquiry(payload);

    if (errors.length) {
      sendJson(response, 400, { ok: false, errors });
      return;
    }

    let saved = false;
    let notified = false;

    try {
      saved = await saveInquiry(inquiry);
    } catch (error) {
      console.error("Inquiry file save failed:", error.message);
      if (!process.env.INQUIRY_WEBHOOK_URL) {
        throw error;
      }
    }

    try {
      notified = await forwardWebhook(inquiry);
    } catch (error) {
      console.error("Webhook forwarding failed:", error.message);
      if (!saved) {
        throw error;
      }
    }

    if (!saved && !notified) {
      throw new Error("inquiry was not saved or forwarded");
    }

    sendJson(response, 200, { ok: true, id: inquiry.id, saved, notified });
  } catch (error) {
    console.error("Inquiry handling failed:", error);
    sendJson(response, 500, { ok: false, error: "Unable to submit inquiry" });
  }
}

async function serveStatic(request, response) {
  const requestUrl = new URL(request.url, `http://${request.headers.host}`);
  const pathname = decodeURIComponent(requestUrl.pathname);
  const safePath = path
    .normalize(pathname)
    .replace(/^(\.\.[/\\])+/, "")
    .replace(/^[/\\]/, "");
  const filePath = path.join(root, safePath || "index.html");
  const resolvedPath = path.resolve(filePath);

  if (!resolvedPath.startsWith(root)) {
    response.writeHead(403);
    response.end("Forbidden");
    return;
  }

  const finalPath = fs.existsSync(resolvedPath) && fs.statSync(resolvedPath).isDirectory()
    ? path.join(resolvedPath, "index.html")
    : resolvedPath;

  try {
    const content = await fsp.readFile(finalPath);
    const ext = path.extname(finalPath).toLowerCase();
    response.writeHead(200, {
      "Content-Type": mimeTypes[ext] || "application/octet-stream",
      "Cache-Control": ext === ".html" ? "no-cache" : "public, max-age=31536000, immutable",
    });
    response.end(content);
  } catch (error) {
    response.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
    response.end("Not found");
  }
}

const server = http.createServer(async (request, response) => {
  if (request.method === "GET" && request.url === "/healthz") {
    sendJson(response, 200, { ok: true });
    return;
  }

  if (request.method === "POST" && request.url === "/api/inquiries") {
    await handleInquiry(request, response);
    return;
  }

  if (request.method === "GET" || request.method === "HEAD") {
    await serveStatic(request, response);
    return;
  }

  response.writeHead(405, { Allow: "GET, HEAD, POST" });
  response.end("Method not allowed");
});

function getLocalNetworkUrls() {
  return Object.values(os.networkInterfaces())
    .flat()
    .filter((item) => item && item.family === "IPv4" && !item.internal)
    .map((item) => `http://${item.address}:${port}/`);
}

function startServer() {
  server.listen(port, host, () => {
    console.log(`长汉金属门官网已启动：http://localhost:${port}/`);
    console.log("同一 Wi-Fi / 局域网设备可尝试访问：");
    getLocalNetworkUrls().forEach((url) => console.log(`- ${url}`));
  });
}

if (require.main === module) {
  startServer();
}

module.exports = {
  server,
  startServer,
  validateInquiry,
  buildWebhookPayload,
  getLocalNetworkUrls,
  saveInquiry,
};
