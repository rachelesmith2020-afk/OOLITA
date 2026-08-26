const ALLOWED_INTERESTS = new Set(["3d", "book", "hallazgo", "field", "textile"]);
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

function confirmationEmailHtml(spanish, confirmUrl) {
  const lang = spanish ? "es" : "en";
  const preheader = spanish ? "Confirma tu correo para seguir OOLITA." : "Confirm your email to follow OOLITA.";
  const heading = spanish ? "Confirma tu correo" : "Confirm your email";
  const intro = spanish ? "Has pedido seguir OOLITA." : "You asked to follow OOLITA.";
  const detail = spanish
    ? "Confirma tu correo para recibir noticias del proyecto."
    : "Confirm your email to receive news from the project.";
  const button = spanish ? "Confirmar correo ↗" : "Confirm email ↗";
  const promise = spanish
    ? "Una sola lista. Sin publicidad. Baja cuando quieras."
    : "One list. No advertising. Unsubscribe whenever you like.";
  const ignore = spanish
    ? "Si no has hecho esta solicitud, puedes ignorar este mensaje."
    : "If you did not make this request, you can ignore this message.";
  const markAlt = spanish ? "Marca OOLITA: gato en un laberinto" : "OOLITA mark: cat in a labyrinth";

  return `<!doctype html>
<html lang="${lang}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="x-apple-disable-message-reformatting">
  <title>${heading} · OOLITA</title>
</head>
<body style="margin:0;padding:0;background:#f1e6cf;color:#1f4f21;">
  <div style="display:none;max-height:0;overflow:hidden;opacity:0;color:transparent;mso-hide:all;">${preheader}</div>
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="width:100%;background:#f1e6cf;border-collapse:collapse;">
    <tr>
      <td align="center" style="padding:48px 20px;">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="width:100%;max-width:600px;border-collapse:collapse;">
          <tr>
            <td style="padding:0 0 44px;font-family:'Instrument Sans',Arial,sans-serif;color:#1f4f21;">
              <a href="https://oolita.es/" style="color:#1f4f21;text-decoration:none;" aria-label="OOLITA">
                <img src="https://oolita.es/favicon.svg" width="92" height="92" alt="${markAlt}" style="display:block;width:92px;height:92px;margin:0 0 22px;border:0;outline:none;text-decoration:none;">
                <span style="display:block;font-size:30px;line-height:1;letter-spacing:0.08em;font-weight:600;">OOLITA</span>
                <span style="display:block;margin-top:9px;font-size:12px;line-height:1.2;letter-spacing:0.12em;text-transform:uppercase;">Los Escullos</span>
              </a>
            </td>
          </tr>
          <tr>
            <td style="border-top:1px solid #1f4f21;padding:42px 0 0;">
              <h1 style="margin:0 0 28px;font-family:'Instrument Serif',Georgia,serif;font-size:48px;line-height:0.98;font-weight:400;letter-spacing:-0.02em;color:#1f4f21;">${heading}</h1>
              <p style="margin:0 0 10px;font-family:'Instrument Sans',Arial,sans-serif;font-size:18px;line-height:1.5;color:#1f4f21;">${intro}</p>
              <p style="margin:0 0 34px;font-family:'Instrument Sans',Arial,sans-serif;font-size:18px;line-height:1.5;color:#1f4f21;">${detail}</p>
              <table role="presentation" cellspacing="0" cellpadding="0" border="0" style="border-collapse:collapse;">
                <tr>
                  <td bgcolor="#1f4f21" style="background:#1f4f21;">
                    <a href="${confirmUrl}" style="display:inline-block;padding:15px 22px;font-family:'Instrument Sans',Arial,sans-serif;font-size:16px;line-height:1.1;font-weight:600;color:#f1e6cf;text-decoration:none;border:1px solid #1f4f21;">${button}</a>
                  </td>
                </tr>
              </table>
              <p style="margin:36px 0 0;font-family:'Instrument Sans',Arial,sans-serif;font-size:14px;line-height:1.5;color:#1f4f21;">${promise}</p>
              <p style="margin:9px 0 0;font-family:'Instrument Sans',Arial,sans-serif;font-size:14px;line-height:1.5;color:#1f4f21;">${ignore}</p>
            </td>
          </tr>
          <tr>
            <td style="padding:48px 0 0;font-family:'Instrument Sans',Arial,sans-serif;font-size:12px;line-height:1.5;color:#1f4f21;">
              <div style="border-top:1px solid #1f4f21;padding-top:16px;">OOLITA · Los Escullos</div>
              <div><a href="https://oolita.es/" style="color:#1f4f21;text-decoration:underline;text-underline-offset:3px;">oolita.es</a></div>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>`;
}

async function sendConfirmation(env, email, language, confirmationToken, requestUrl) {
  const cfg = emailConfig(env);
  if (!cfg || !TOKEN_RE.test(confirmationToken)) throw new Error("email_service_unavailable");

  const confirmUrl = `${confirmationOrigin(requestUrl)}/api/confirm?token=${encodeURIComponent(confirmationToken)}`;
  const spanish = language === "es";
  const subject = spanish ? "Confirma tu correo · OOLITA" : "Confirm your email · OOLITA";
  const text = spanish
    ? `Has pedido seguir OOLITA.\n\nConfirma tu correo para recibir noticias del proyecto:\n\n${confirmUrl}\n\nUna sola lista. Sin publicidad. Baja cuando quieras.\n\nSi no has hecho esta solicitud, puedes ignorar este mensaje.\n\nOOLITA · Los Escullos\nhttps://oolita.es/`
    : `You asked to follow OOLITA.\n\nConfirm your email to receive news from the project:\n\n${confirmUrl}\n\nOne list. No advertising. Unsubscribe whenever you like.\n\nIf you did not make this request, you can ignore this message.\n\nOOLITA · Los Escullos\nhttps://oolita.es/`;
  const html = confirmationEmailHtml(spanish, confirmUrl);

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