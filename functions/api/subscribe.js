const ALLOWED_INTERESTS = new Set(["3d", "book", "field", "textile"]);
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function reply(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "no-store",
      "X-Robots-Tag": "noindex, nofollow",
    },
  });
}

function sameOriginAllowed(request) {
  const origin = request.headers.get("Origin");
  if (!origin) return true;
  try {
    const host = new URL(origin).hostname.toLowerCase();
    return host === "oolita.es" || host === "www.oolita.es" || host === "oolita.pages.dev" || host.endsWith(".oolita.pages.dev");
  } catch {
    return false;
  }
}

function token() {
  const bytes = new Uint8Array(24);
  crypto.getRandomValues(bytes);
  return Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("");
}

async function parsePayload(request) {
  const type = (request.headers.get("Content-Type") || "").toLowerCase();
  if (type.includes("application/json") || type.includes("text/plain")) {
    return JSON.parse((await request.text()) || "{}");
  }
  const form = await request.formData();
  return {
    email: form.get("email"),
    language: form.get("language"),
    consent: form.get("consent"),
    website: form.get("website"),
    source_path: form.get("source_path"),
    interests: form.getAll("interest"),
  };
}

export async function onRequestGet(context) {
  const url = new URL(context.request.url);
  if (url.searchParams.get("health") !== "1") {
    return new Response("Method not allowed", { status: 405, headers: { Allow: "POST", "X-Robots-Tag": "noindex, nofollow" } });
  }
  if (!context.env.OOLITA_SUBSCRIBERS) return reply({ ok: false, error: "storage_unavailable" }, 503);
  try {
    await context.env.OOLITA_SUBSCRIBERS.prepare("SELECT 1 AS ok").first();
    return new Response(null, { status: 204, headers: { "Cache-Control": "no-store", "X-Robots-Tag": "noindex, nofollow" } });
  } catch {
    return reply({ ok: false, error: "storage_unavailable" }, 503);
  }
}

export async function onRequestPost(context) {
  const { request, env } = context;
  if (!env.OOLITA_SUBSCRIBERS) return reply({ ok: false, error: "storage_unavailable" }, 503);
  if (!sameOriginAllowed(request)) return reply({ ok: false, error: "origin_rejected" }, 403);

  const declared = Number(request.headers.get("Content-Length") || "0");
  if (declared > 12000) return reply({ ok: false, error: "request_too_large" }, 413);

  let payload;
  try {
    payload = await parsePayload(request);
  } catch {
    return reply({ ok: false, error: "invalid_request" }, 400);
  }

  // Honeypot: acknowledge silently so simple bots do not learn how to bypass it.
  if (String(payload.website || "").trim()) return reply({ ok: true, state: "recorded" });

  const email = String(payload.email || "").trim().toLowerCase();
  const language = payload.language === "es" ? "es" : payload.language === "en" ? "en" : "";
  const consent = payload.consent === true || payload.consent === "true" || payload.consent === "on" || payload.consent === "yes";
  const sourcePathRaw = String(payload.source_path || "/").slice(0, 240);
  const sourcePath = sourcePathRaw.startsWith("/") ? sourcePathRaw : "/";
  const rawInterests = Array.isArray(payload.interests) ? payload.interests : payload.interests ? [payload.interests] : [];
  const interests = [...new Set(rawInterests.map(String).filter((x) => ALLOWED_INTERESTS.has(x)))];

  if (!email || email.length > 254 || !EMAIL_RE.test(email)) return reply({ ok: false, error: "invalid_email" }, 400);
  if (!language) return reply({ ok: false, error: "invalid_language" }, 400);
  if (!consent) return reply({ ok: false, error: "consent_required" }, 400);

  const now = new Date().toISOString();
  const unsubscribeToken = token();
  const consentVersion = "oolita-follow-2026-08-22";

  try {
    await env.OOLITA_SUBSCRIBERS.prepare(`
      INSERT INTO subscribers
        (email, language, interests, consent_version, consent_at, source_path, status, unsubscribe_token, verified_at, unsubscribed_at, updated_at)
      VALUES (?, ?, ?, ?, ?, ?, 'active', ?, NULL, NULL, ?)
      ON CONFLICT(email) DO UPDATE SET
        language = excluded.language,
        interests = excluded.interests,
        consent_version = excluded.consent_version,
        consent_at = excluded.consent_at,
        source_path = excluded.source_path,
        status = 'active',
        unsubscribe_token = CASE WHEN subscribers.status = 'active' THEN subscribers.unsubscribe_token ELSE excluded.unsubscribe_token END,
        verified_at = NULL,
        unsubscribed_at = NULL,
        updated_at = excluded.updated_at
    `).bind(
      email,
      language,
      JSON.stringify(interests),
      consentVersion,
      now,
      sourcePath,
      unsubscribeToken,
      now,
    ).run();
  } catch (err) {
    console.error("subscribe D1 error", err);
    return reply({ ok: false, error: "storage_error" }, 500);
  }

  return reply({ ok: true, state: "active" });
}

export function onRequest() {
  return new Response("Method not allowed", { status: 405, headers: { Allow: "GET, POST", "X-Robots-Tag": "noindex, nofollow" } });
}
