/**
 * Canonical-path and Hallazgo catalogue middleware for OOLITA.
 *
 * Cloudflare Pages routes are case-sensitive. Redirect only literal ASCII
 * uppercase characters in the path; leave percent-encoded bytes untouched.
 *
 * Hallazgo has two distinct destinations:
 * - https://hallazgo.my.canva.site/hallazgo is the external Hallazgo Art site.
 * - the retired Canva catalogue path is redirected to OOLITA's first-party
 *   catalogue page.
 *
 * The homepage label for Hallazgo Art is also normalized here so it cannot
 * inherit the 3D-world "virtual castle" description from legacy build layers.
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

  const isEnglish = url.pathname === "/en/" || url.pathname.startsWith("/en/");
  const cataloguePath = isEnglish
    ? "/en/hallazgo-catalogue/"
    : "/catalogo-hallazgo/";
  const hallazgoArtUrl = "https://hallazgo.my.canva.site/hallazgo";

  return new HTMLRewriter()
    .on("a[href]", {
      element(element) {
        const href = element.getAttribute("href");
        if (!href) return;
        try {
          const target = new URL(href, url);
          const host = target.hostname.toLowerCase();
          const path = target.pathname.replace(/\/+$/, "").toLowerCase();
          const isRetiredCanvaCatalogue =
            host === "hallazgo.my.canva.site" &&
            (path === "/hallazgo/catlogo" || path === "/hallazgo/catalogo");

          if (isRetiredCanvaCatalogue) {
            element.setAttribute("href", cataloguePath);
            element.removeAttribute("target");
            element.removeAttribute("rel");
          }
        } catch {
          // Leave malformed or non-URL href values unchanged.
        }
      },
    })
    .on(`a[href="${hallazgoArtUrl}"] .glo`, {
      element(element) {
        element.setInnerContent(
          isEnglish ? "Work by Raquel Costantini ↗" : "Obra de Raquel Costantini ↗",
        );
      },
    })
    .transform(response);
}
