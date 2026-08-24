/**
 * Canonical-path and Hallazgo catalogue middleware for OOLITA.
 *
 * Cloudflare Pages routes are case-sensitive. Redirect only literal ASCII
 * uppercase characters in the path; leave percent-encoded bytes untouched.
 * The former Canva catalogue is now served as a first-party OOLITA page; any
 * surviving public link to hallazgo.my.canva.site is rewritten at the edge.
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

  const response = await context.next();
  const contentType = response.headers.get("content-type") || "";
  if (!contentType.toLowerCase().includes("text/html")) {
    return response;
  }

  const cataloguePath = url.pathname === "/en/" || url.pathname.startsWith("/en/")
    ? "/en/hallazgo-catalogue/"
    : "/catalogo-hallazgo/";

  return new HTMLRewriter()
    .on("a[href]", {
      element(element) {
        const href = element.getAttribute("href");
        if (!href) return;
        try {
          const target = new URL(href, url);
          if (target.hostname.toLowerCase() === "hallazgo.my.canva.site") {
            element.setAttribute("href", cataloguePath);
            element.removeAttribute("target");
            element.removeAttribute("rel");
          }
        } catch {
          // Leave malformed or non-URL href values unchanged.
        }
      },
    })
    .transform(response);
}
