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

  // Use the same EU-jurisdiction first-party D1 store as Follow OOLITA once it
  // is bound. Store only event name, local paths and timestamp: no email, IP,
  // cookie value, user-agent or full referrer is written by this endpoint.
  if (env.OOLITA_SUBSCRIBERS) {
    try {
      await env.OOLITA_SUBSCRIBERS.prepare(
        "INSERT INTO site_events (event, path, href, created_at) VALUES (?, ?, ?, ?)"
      ).bind(event, path, href, new Date().toISOString()).run();
    } catch (err) {
      console.error("D1 analytics write failed", err);
    }
  } else if (env.OOLITA_ANALYTICS) {
    // Backward-compatible fallback only; this binding is intentionally absent
    // while the account-level Analytics Engine feature is disabled.
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

  // Measurement must never break navigation or form submission. Before D1 is
  // available this is an intentional no-op with a successful response.
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
