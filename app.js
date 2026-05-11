const header = document.querySelector("[data-header]");
const navToggle = document.querySelector("[data-nav-toggle]");
const nav = document.querySelector("[data-nav]");
const revealItems = document.querySelectorAll(".reveal");
const form = document.querySelector("[data-form]");
const formStatus = document.querySelector("[data-form-status]");
const submitButton = form ? form.querySelector("[type='submit']") : null;
const mobileCta = document.querySelector(".mobile-cta");
const contactSection = document.querySelector("#contact");
const inquiryEmail = "1907375443@qq.com";
const forceSolidHeader = !document.querySelector(".hero");

const syncHeader = () => {
  header.classList.toggle("is-scrolled", forceSolidHeader || window.scrollY > 16);
};

syncHeader();
window.addEventListener("scroll", syncHeader, { passive: true });

if (navToggle) {
  navToggle.addEventListener("click", () => {
    const open = !document.body.classList.contains("nav-open");
    document.body.classList.toggle("nav-open", open);
    navToggle.setAttribute("aria-expanded", String(open));
    navToggle.setAttribute("aria-label", open ? "关闭导航" : "打开导航");
  });
}

if (nav) {
  nav.addEventListener("click", (event) => {
    if (event.target.matches("a")) {
      document.body.classList.remove("nav-open");
      navToggle.setAttribute("aria-expanded", "false");
      navToggle.setAttribute("aria-label", "打开导航");
    }
  });
}

const revealObserver = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("is-visible");
        revealObserver.unobserve(entry.target);
      }
    });
  },
  { threshold: 0.16, rootMargin: "0px 0px -8% 0px" }
);

revealItems.forEach((item) => revealObserver.observe(item));

const contactObserver = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      mobileCta.classList.toggle("is-hidden", entry.isIntersecting);
    });
  },
  { threshold: 0.16 }
);

if (mobileCta && contactSection) {
  contactObserver.observe(contactSection);
}

const createMailtoUrl = (payload) => {
  const body = [
    "长汉金属门工程询盘",
    "",
    `姓名：${payload.name || "未填写"}`,
    `电话：${payload.phone || "未填写"}`,
    `城市：${payload.city || "未填写"}`,
    `数量：${payload.quantity || "未填写"}`,
    `项目类型：${payload.project || "未选择"}`,
    `工期阶段：${payload.stage || "未选择"}`,
    "",
    "项目说明：",
    payload.message || "未填写",
  ].join("\n");

  return `mailto:${inquiryEmail}?subject=${encodeURIComponent("长汉金属门工程询盘")}&body=${encodeURIComponent(body)}`;
};

const submitToApi = async (payload) => {
  const response = await fetch("/api/inquiries", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error("Inquiry request failed");
  }

  return response.json();
};

if (form) {
  form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const payload = Object.fromEntries(new FormData(form).entries());
  const name = payload.name || "您好";
  const detail = [payload.city, payload.project, payload.quantity].filter(Boolean).join(" · ");

  submitButton.disabled = true;
  submitButton.textContent = "正在提交";
  formStatus.textContent = "正在提交询盘信息...";

  try {
    if (window.location.protocol === "file:") {
      throw new Error("Static file fallback");
    }

    await submitToApi(payload);
    formStatus.textContent = detail
      ? `${name}，${detail} 的询盘已提交，我们会尽快联系您。`
      : `${name}，询盘已提交，我们会尽快联系您。`;
    form.reset();
  } catch (error) {
    window.location.href = createMailtoUrl(payload);
    formStatus.textContent = detail
      ? `${name}，已为 ${detail} 生成邮件询盘草稿。`
      : `${name}，已生成邮件询盘草稿。`;
  } finally {
    submitButton.disabled = false;
    submitButton.innerHTML = '提交询盘<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6" /></svg>';
  }
  });
}
