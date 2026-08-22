const EVENT_RE = /^[a-z0-9][a-z0-9-]{0,79}$/;

function cleanPath(value) {
  if (typeof value !== "string") return "";
  const path = value.slice(0, 300);
  return path.startsWith("/") ? path : "";
}

export async function onRequestPost(context) {
  const { request, env } = context;

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

  // Analytics must never block the site. If Analytics Engine is unavailable,
  // accept the event and discard it until a supported storage layer is enabled.
  if (env.OOLITA_ANALYTICS) {
    try {
      env.OOLITA_ANALYTICS.writeDataPoint({
        indexes: ["oolita"],
        blobs: [event, path, href],
        doubles: [1],
      });
    } catch (err) {
      console.error("analytics write failed", err);
    }
  }

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
