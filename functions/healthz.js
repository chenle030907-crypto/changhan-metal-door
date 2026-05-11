export function onRequestGet() {
  return new Response(JSON.stringify({ ok: true, platform: "cloudflare-pages" }), {
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "no-store",
    },
  });
}
