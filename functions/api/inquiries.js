function sanitizeText(value, maxLength = 500) {
  return String(value || "")
    .replace(/\s+/g, " ")
    .trim()
    .slice(0, maxLength);
}

function json(status, payload) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "no-store",
    },
  });
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
    source: "cloudflare-pages",
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

function buildWebhookPayload(inquiry, providerName) {
  const provider = String(providerName || "generic").toLowerCase();
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

async function forwardWebhook(inquiry, env) {
  if (!env.INQUIRY_WEBHOOK_URL) {
    throw new Error("INQUIRY_WEBHOOK_URL is not configured");
  }

  const response = await fetch(env.INQUIRY_WEBHOOK_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(buildWebhookPayload(inquiry, env.INQUIRY_NOTIFY_PROVIDER)),
  });

  if (!response.ok) {
    throw new Error(`webhook failed with ${response.status}`);
  }
}

export async function onRequestPost({ request, env }) {
  try {
    const payload = await request.json();
    const { inquiry, errors } = validateInquiry(payload);

    if (errors.length) {
      return json(400, { ok: false, errors });
    }

    await forwardWebhook(inquiry, env);
    return json(200, { ok: true, id: inquiry.id, notified: true });
  } catch (error) {
    console.error("Inquiry handling failed:", error.message);
    return json(500, { ok: false, error: "Unable to submit inquiry" });
  }
}

export function onRequestOptions() {
  return new Response(null, {
    status: 204,
    headers: {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
    },
  });
}
