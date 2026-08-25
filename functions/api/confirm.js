const TOKEN_RE = /^[a-f0-9]{48}$/;

function token() {
  const bytes = new Uint8Array(24);
  crypto.getRandomValues(bytes);
  return Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("");
}

function page(language, state) {
  const es = language === "es";
  const copy = {
    confirmed: es
      ? {
          title: "Ya estás dentro.",
          lead: "Tu correo está confirmado.",
          detail: "Recibirás noticias de OOLITA cuando haya algo que merezca ser enviado.",
          action: "Volver a OOLITA",
        }
      : {
          title: "You’re in.",
          lead: "Your email is confirmed.",
          detail: "You’ll hear from OOLITA when there is something worth sending.",
          action: "Return to OOLITA",
        },
    expired: es
      ? {
          title: "Enlace caducado",
          lead: "Este enlace de confirmación ha caducado.",
          detail: "Vuelve a introducir tu correo en OOLITA para recibir un enlace nuevo.",
          action: "Volver a OOLITA",
        }
      : {
          title: "Link expired",
          lead: "This confirmation link has expired.",
          detail: "Enter your email again on OOLITA to receive a new confirmation link.",
          action: "Return to OOLITA",
        },
    invalid: es
      ? {
          title: "Enlace no válido",
          lead: "No hemos podido confirmar este enlace.",
          detail: "Puede que no sea válido o que ya haya sido utilizado.",
          action: "Volver a OOLITA",
        }
      : {
          title: "Invalid link",
          lead: "We could not confirm this link.",
          detail: "It may be invalid or it may already have been used.",
          action: "Return to OOLITA",
        },
  }[state];
  const lang = es ? "es" : "en";
  const home = es ? "/" : "/en/";
  const markAlt = es ? "Marca OOLITA: gato en un laberinto" : "OOLITA mark: cat in a labyrinth";

  return `<!doctype html>
<html lang="${lang}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="robots" content="noindex,nofollow">
  <meta name="theme-color" content="#f1e6cf">
  <title>${copy.title} · OOLITA</title>
  <style>
    @font-face{font-family:Instrument Sans;src:url('/fonts/instrument-sans-var-latin.woff2') format('woff2');font-weight:100 900;font-style:normal;font-display:swap}
    :root{--paper:#f1e6cf;--green:#1f4f21}
    *{box-sizing:border-box}
    html,body{min-height:100%}
    body{margin:0;background:var(--paper);color:var(--green);font-family:'Instrument Sans',Arial,sans-serif}
    .page{min-height:100vh;display:flex;flex-direction:column;padding:28px clamp(22px,4vw,54px) 38px}
    .top{display:flex;align-items:center;justify-content:space-between;gap:24px;padding:0 0 22px;border-bottom:2px solid var(--green);font-size:12px;line-height:1.2;font-weight:650;letter-spacing:.12em;text-transform:uppercase}
    .top a{color:inherit;text-decoration:none}
    main{width:100%;max-width:960px;margin:auto 0;padding:9vh 0 8vh}
    .brand{display:inline-flex;align-items:center;gap:22px;color:inherit;text-decoration:none;margin-bottom:54px}
    .mark{display:block;width:104px;height:104px;border:0}
    .wordmark{display:block;font-size:clamp(38px,6vw,74px);line-height:.85;font-weight:560;letter-spacing:.015em}
    .place{display:block;margin-top:12px;font-size:12px;line-height:1.2;font-weight:650;letter-spacing:.13em;text-transform:uppercase}
    h1{max-width:900px;margin:0 0 30px;font-size:clamp(58px,11vw,132px);line-height:.84;font-weight:520;letter-spacing:-.045em}
    .lead{margin:0 0 8px;max-width:650px;font-size:clamp(20px,2.4vw,30px);line-height:1.25;font-weight:520}
    .detail{margin:0 0 38px;max-width:650px;font-size:clamp(17px,1.7vw,21px);line-height:1.5}
    .cta{display:inline-block;padding:14px 20px;border:1.5px solid var(--green);color:inherit;text-decoration:none;font-size:15px;line-height:1.1;font-weight:650;letter-spacing:.02em}
    .cta:hover,.cta:focus-visible{background:var(--green);color:var(--paper);outline:none}
    footer{padding-top:18px;border-top:1px solid var(--green);font-size:12px;line-height:1.4;font-weight:600;letter-spacing:.1em;text-transform:uppercase}
    @media (max-width:600px){.page{padding-top:20px}.top span:last-child{display:none}main{padding:7vh 0}.brand{gap:16px;margin-bottom:42px}.mark{width:78px;height:78px}.wordmark{font-size:42px}h1{font-size:clamp(54px,20vw,88px)}}
  </style>
</head>
<body>
  <div class="page">
    <div class="top"><span>Los Escullos · Cabo de Gata</span><span>OOLITA · 2027</span></div>
    <main>
      <a class="brand" href="${home}" aria-label="OOLITA">
        <img class="mark" src="https://oolita.es/favicon.svg" width="104" height="104" alt="${markAlt}">
        <span><span class="wordmark">OOLITA</span><span class="place">Los Escullos</span></span>
      </a>
      <h1>${copy.title}</h1>
      <p class="lead">${copy.lead}</p>
      <p class="detail">${copy.detail}</p>
      <p><a class="cta" href="${home}">${copy.action} ↗</a></p>
    </main>
    <footer>OOLITA · Los Escullos · Cabo de Gata</footer>
  </div>
</body>
</html>`;
}

function htmlResponse(language, state, status = 200) {
  return new Response(page(language, state), {
    status,
    headers: {
      "Content-Type": "text/html; charset=utf-8",
      "Cache-Control": "no-store",
      "X-Robots-Tag": "noindex, nofollow",
      "Referrer-Policy": "no-referrer",
    },
  });
}

export async function onRequestGet(context) {
  const { request, env } = context;
  if (!env.OOLITA_SUBSCRIBERS) return htmlResponse("en", "invalid", 503);

  const url = new URL(request.url);
  const confirmationToken = String(url.searchParams.get("token") || "").trim().toLowerCase();
  if (!TOKEN_RE.test(confirmationToken)) return htmlResponse("en", "invalid", 400);

  let row;
  try {
    row = await env.OOLITA_SUBSCRIBERS.prepare(`
      SELECT email, language, consent_at
      FROM subscribers
      WHERE unsubscribe_token = ? AND status = 'pending_confirmation'
    `).bind(confirmationToken).first();
  } catch (err) {
    console.error("confirmation lookup error", err);
    return htmlResponse("en", "invalid", 503);
  }

  if (!row) return htmlResponse("en", "invalid", 404);
  const language = row.language === "es" ? "es" : "en";

  const consentAt = Date.parse(row.consent_at || "");
  if (!Number.isFinite(consentAt) || Date.now() - consentAt > 72 * 60 * 60 * 1000) {
    try {
      await env.OOLITA_SUBSCRIBERS.prepare(
        "DELETE FROM subscribers WHERE email = ? AND status = 'pending_confirmation'"
      ).bind(row.email).run();
    } catch (err) {
      console.error("expired confirmation cleanup error", err);
    }
    return htmlResponse(language, "expired", 410);
  }

  const now = new Date().toISOString();
  const unsubscribeToken = token();
  try {
    const result = await env.OOLITA_SUBSCRIBERS.prepare(`
      UPDATE subscribers
      SET status = 'active', verified_at = ?, unsubscribe_token = ?, updated_at = ?
      WHERE email = ? AND status = 'pending_confirmation' AND unsubscribe_token = ?
    `).bind(now, unsubscribeToken, now, row.email, confirmationToken).run();
    const changes = Number(result && result.meta && result.meta.changes);
    if (!result || !result.success || !Number.isFinite(changes) || changes !== 1) {
      return htmlResponse(language, "invalid", 409);
    }
  } catch (err) {
    console.error("confirmation update error", err);
    return htmlResponse(language, "invalid", 503);
  }

  return htmlResponse(language, "confirmed", 200);
}

export function onRequest() {
  return new Response("Method not allowed", { status: 405, headers: { Allow: "GET", "X-Robots-Tag": "noindex, nofollow" } });
}
