const EVENT_RE = /^[a-z0-9][a-z0-9-]{0,79}$/;

function cleanPath(value) {
  if (typeof value !== "string") return "";
  const path = value.slice(0, 300);
  return path.startsWith("/") ? path : "";
}

export async function onRequestPost(context) {
  const { request, env } = context;
  if (!env.OOLITA_ANALYTICS) {
    return new Response("Analytics binding unavailable", { status: 503 });
  }

  let payload;
  try {
    const text = await request.text();
    payload = JSON.parse(text || "{}");
  } catch {
    return new Response("Invalid JSON", { status: 400 });
  }

  const event = typeof payload.event === "string" ? payload.event : "";
  if (!EVENT_RE.test(event)) {
    return new Response("Invalid event", { status: 400 });
  }

  const path = cleanPath(payload.path);
  const href = cleanPath(payload.href);

  // Deliberately store no email, IP address, cookie value, user-agent or full referrer.
  env.OOLITA_ANALYTICS.writeDataPoint({
    indexes: ["oolita"],
    blobs: [event, path, href],
    doubles: [1],
  });

  return new Response(null, {
    status: 204,
    headers: {
      "Cache-Control": "no-store",
      "X-Robots-Tag": "noindex, nofollow",
    },
  });
}

export function onRequest() {
  return new Response("Method not allowed", {
    status: 405,
    headers: { Allow: "POST", "X-Robots-Tag": "noindex, nofollow" },
  });
}
