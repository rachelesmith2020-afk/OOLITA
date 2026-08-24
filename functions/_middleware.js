/**
 * Canonical-path middleware for OOLITA.
 *
 * Cloudflare Pages routes are case-sensitive. Redirect only literal ASCII
 * uppercase characters in the path; leave percent-encoded bytes untouched.
 */
export async function onRequest(context) {
  const url = new URL(context.request.url);
  const canonicalPath = url.pathname.replace(
    /%[0-9A-Fa-f]{2}|[A-Z]/g,
    (token) => token.startsWith("%") ? token : token.toLowerCase(),
  );

  if (canonicalPath !== url.pathname) {
    url.protocol = "https:";
    url.hostname = "oolita.es";
    url.port = "";
    url.pathname = canonicalPath;
    return Response.redirect(url.toString(), 301);
  }

  return context.next();
}
