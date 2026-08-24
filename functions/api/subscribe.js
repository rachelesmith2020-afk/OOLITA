const ALLOWED_INTERESTS = new Set(["3d", "book", "field", "textile"]);
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const TOKEN_RE = /^[a-f0-9]{48}$/;

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

function emailConfig(env) {
  const apiKey = String(env.OOLITA_RESEND_API_KEY || "").trim();
  const from = String(env.OOLITA_EMAIL_FROM || "follow@oolita.es").trim();
  if (!apiKey || !EMAIL_RE.test(from)) return null;
  return { apiKey, from };
}

function confirmationOrigin(requestUrl) {
  try {
    const url = new URL(requestUrl);
    const host = url.hostname.toLowerCase();
    if (host === "oolita.pages.dev" || host.endsWith(".oolita.pages.dev")) return url.origin;
  } catch {
    // Production origin below is the safe fallback.
  }
  return "https://oolita.es";
}

async function sendConfirmation(env, email, language, confirmationToken, requestUrl) {
  const cfg = emailConfig(env);
  if (!cfg || !TOKEN_RE.test(confirmationToken)) throw new Error("email_service_unavailable");

  const confirmUrl = `${confirmationOrigin(requestUrl)}/api/confirm?token=${encodeURIComponent(confirmationToken)}`;
  const spanish = language === "es";
  const subject = spanish ? "Confirma tu correo · OOLITA" : "Confirm your email · OOLITA";
  const text = spanish
    ? `Has pedido seguir OOLITA. Confirma tu correo abriendo este enlace:\n\n${confirmUrl}\n\nSi no has hecho esta solicitud, puedes ignorar este mensaje.`
    : `You asked to follow OOLITA. Confirm your email by opening this link:\n\n${confirmUrl}\n\nIf you did not make this request, you can ignore this message.`;
  const html = spanish
    ? `<p>Has pedido seguir OOLITA.</p><p><a href="${confirmUrl}">Confirma tu correo</a></p><p>Si no has hecho esta solicitud, puedes ignorar este mensaje.</p>`
    : `<p>You asked to follow OOLITA.</p><p><a href="${confirmUrl}">Confirm your email</a></p><p>If you did not make this request, you can ignore this message.</p>`;

  const response = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${cfg.apiKey}`,
      "Content-Type": "application/json",
      "User-Agent": "OOLITA/1.0 (https://oolita.es)",
      "Idempotency-Key": `oolita-confirm-${confirmationToken}`,
    },
    body: JSON.stringify({
      from: `OOLITA <${cfg.from}>`,
      to: [email],
      subject,
      text,
      html,
      reply_to: "oolita@tutamail.com",
    }),
  });

  const body = await response.json().catch(() => null);
  if (!response.ok || !body || typeof body.id !== "string" || !body.id) {
    console.error("Resend confirmation failed", response.status, body || null);
    throw new Error("confirmation_send_failed");
  }
}

export async function onRequestGet(context) {
  const url = new URL(context.request.url);
  if (url.searchParams.get("health") !== "1") {
    return new Response("Method not allowed", { status: 405, headers: { Allow: "POST", "X-Robots-Tag": "noindex, nofollow" } });
  }
  if (!context.env.OOLITA_SUBSCRIBERS) return reply({ ok: false, error: "storage_unavailable" }, 503);
  if (!emailConfig(context.env)) return reply({ ok: false, error: "email_service_unavailable" }, 503);
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
  if (!emailConfig(env)) return reply({ ok: false, error: "email_service_unavailable" }, 503);
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
  const confirmationToken = token();
  const consentVersion = "oolita-follow-double-opt-in-2026-08-24";

  let existing = null;
  try {
    existing = await env.OOLITA_SUBSCRIBERS.prepare(`
      SELECT email, language, interests, consent_version, consent_at, source_path,
             status, unsubscribe_token, verified_at, unsubscribed_at, updated_at
      FROM subscribers WHERE email = ?
    `).bind(email).first();

    // Already-confirmed subscribers remain confirmed. A repeat submission only
    // refreshes their stated preferences and consent record.
    if (existing && existing.status === "active") {
      await env.OOLITA_SUBSCRIBERS.prepare(`
        UPDATE subscribers
        SET language = ?, interests = ?, consent_version = ?, consent_at = ?, source_path = ?, updated_at = ?
        WHERE email = ? AND status = 'active'
      `).bind(language, JSON.stringify(interests), consentVersion, now, sourcePath, now, email).run();
      return reply({ ok: true, state: "active" });
    }

    await env.OOLITA_SUBSCRIBERS.prepare(`
      INSERT INTO subscribers
        (email, language, interests, consent_version, consent_at, source_path, status, unsubscribe_token, verified_at, unsubscribed_at, updated_at)
      VALUES (?, ?, ?, ?, ?, ?, 'pending_confirmation', ?, NULL, NULL, ?)
      ON CONFLICT(email) DO UPDATE SET
        language = excluded.language,
        interests = excluded.interests,
        consent_version = excluded.consent_version,
        consent_at = excluded.consent_at,
        source_path = excluded.source_path,
        status = 'pending_confirmation',
        unsubscribe_token = excluded.unsubscribe_token,
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
      confirmationToken,
      now,
    ).run();

    await sendConfirmation(env, email, language, confirmationToken, request.url);
  } catch (err) {
    console.error("subscribe double-opt-in error", err);
    try {
      if (!existing) {
        await env.OOLITA_SUBSCRIBERS.prepare(
          "DELETE FROM subscribers WHERE email = ? AND status = 'pending_confirmation' AND unsubscribe_token = ?"
        ).bind(email, confirmationToken).run();
      } else {
        await env.OOLITA_SUBSCRIBERS.prepare(`
          UPDATE subscribers
          SET language = ?, interests = ?, consent_version = ?, consent_at = ?, source_path = ?,
              status = ?, unsubscribe_token = ?, verified_at = ?, unsubscribed_at = ?, updated_at = ?
          WHERE email = ?
        `).bind(
          existing.language,
          existing.interests,
          existing.consent_version,
          existing.consent_at,
          existing.source_path,
          existing.status,
          existing.unsubscribe_token,
          existing.verified_at,
          existing.unsubscribed_at,
          existing.updated_at,
          email,
        ).run();
      }
    } catch (rollbackErr) {
      console.error("subscribe rollback error", rollbackErr);
    }
    return reply({ ok: false, error: "confirmation_unavailable" }, 503);
  }

  return reply({ ok: true, state: "pending_confirmation" });
}

export function onRequest() {
  return new Response("Method not allowed", { status: 405, headers: { Allow: "GET, POST", "X-Robots-Tag": "noindex, nofollow" } });
}
