const PAGE_PATH = "/en/editions/t-shirt/";
const INDEX_PATH = "/en/editions/";

const SINGLE_TITLE = "OOLITA T-shirt — Stanley/Stella Blaster 2.0 · OOLITA";
const SINGLE_DESCRIPTION = "OOLITA's first textile edition: white Stanley/Stella Blaster 2.0, 200 gsm organic cotton, oversized unisex fit. Made on demand.";

function replaceAllLiteral(text, oldValue, newValue) {
  return text.split(oldValue).join(newValue);
}

function normalizeJsonLd(html) {
  return html.replace(/<script([^>]*)type=["']application\/ld\+json["']([^>]*)>([\s\S]*?)<\/script>/gi, (full, before, after, body) => {
    let data;
    try {
      data = JSON.parse(body.trim());
    } catch {
      return full;
    }
    if (!data || typeof data !== "object" || Array.isArray(data)) return full;

    const id = String(data["@id"] || "");
    if (id === "https://oolita.es/en/editions/t-shirt/#webpage") {
      data.name = SINGLE_TITLE;
      data.description = SINGLE_DESCRIPTION;
    }
    if (id === "https://oolita.es/en/editions/t-shirt/#producto") {
      data["@type"] = "Product";
      data.name = "OOLITA · Blaster 2.0 T-shirt";
      data.description = SINGLE_DESCRIPTION;
      data.sku = "OOLITA-UK-OVERSIZED-WHITE";
      data.model = "Stanley/Stella Blaster 2.0 STTU959";
      data.material = "100% organic ring-spun combed cotton";
      data.size = "XXS–3XL";
      data.color = "White";
      data.releaseDate = "2027-04-11";
      data.brand = { "@type": "Brand", name: "OOLITA" };
      delete data.productGroupID;
      delete data.hasVariant;
    }
    return `<script${before}type="application/ld+json"${after}>${JSON.stringify(data)}</script>`;
  });
}

function normalizeTshirtPage(html) {
  html = replaceAllLiteral(html, "OOLITA T-shirt — regular and heavy oversized · OOLITA", SINGLE_TITLE);
  html = replaceAllLiteral(html, "OOLITA's first textile edition: 180 gsm Stanley/Stella RE-Creator regular or 200 gsm Blaster 2.0 heavy oversized. Made on demand.", SINGLE_DESCRIPTION);
  html = replaceAllLiteral(html, "White Stanley/Stella Blaster 2.0, heavy oversized option, without the design", "White Stanley/Stella Blaster 2.0, oversized unisex fit, without the design");
  html = replaceAllLiteral(html, "White, one OOLITA design and two unisex cuts: a 180 gsm regular option and a 200 gsm heavy oversized option. Details and the story of the design will unfold Sunday by Sunday through to spring.", "White, 200 gsm organic cotton, an oversized unisex fit. For now just the bare garment: the design is unveiled Sunday by Sunday, through to spring.");
  html = replaceAllLiteral(html, "Which garments.", "Which garment.");
  html = replaceAllLiteral(html, "There are two Stanley/Stella choices. Regular is the RE-Creator STTU787: 180 gsm, medium fit, 50% recycled cotton and 50% organic cotton, made from Stanley/Stella's own organic cutting waste. Heavy Oversized is the Blaster 2.0 STTU959: 200 gsm, 100% organic ring-spun combed cotton, oversized with dropped shoulders and a 1x1 rib mock-neck collar. Both are unisex and available from XXS to 3XL.", "It is a Stanley/Stella Blaster 2.0, not a generic tee: 200 gsm single jersey in organic ring-spun combed cotton. Oversized unisex cut with dropped shoulders, side seams, an elastane-free 1x1 rib mock-neck collar, self-fabric back-neck tape and twin-needle stitching at cuffs and hem. Available from XXS to 3XL.");
  html = replaceAllLiteral(html, "Stanley/Stella lists the RE-Creator with GRS, OCS and OEKO-TEX credentials and the Blaster 2.0 with GOTS and OEKO-TEX; both product pages also show Fair Wear. The two options keep the same traceable-garment standard while giving a choice of weight and cut.", "Stanley/Stella lists the Blaster 2.0 with GOTS and OEKO-TEX credentials. Stanley/Stella is a Fair Wear member and its products are listed as PETA-Approved Vegan.");

  html = html.replace(/<div class="textile-choice-grid"[^>]*data-oolita-textile-choices="v1"[^>]*>[\s\S]*?<\/div>\s*/i, "");
  html = html.replace(/<style[^>]*data-oolita-textile-variants="v1"[^>]*>[\s\S]*?<\/style>\s*/i, "");

  const facts = new Map([
    ["Regular · RE-Creator STTU787 / Heavy Oversized · Blaster 2.0 STTU959", "Stanley/Stella Blaster 2.0"],
    ["Regular · 50% recycled cotton + 50% organic / Heavy · 100% organic combed cotton", "100% organic combed cotton"],
    ["Regular · 180 gsm / Heavy Oversized · 200 gsm", "200 gsm · 20 singles"],
    ["Regular · medium unisex / Heavy Oversized · dropped shoulders", "Oversized unisex · dropped shoulder"],
    ["Regular · 1x1 rib neckline / Heavy Oversized · mock-neck 1x1 rib", "Mock-neck, elastane-free 1x1 rib"],
    ["RE-Creator · GRS · OCS · OEKO-TEX · Fair Wear / Blaster 2.0 · GOTS · OEKO-TEX · Fair Wear", "GOTS · OEKO-TEX · Fair Wear member · PETA-Approved"],
  ]);
  for (const [oldValue, newValue] of facts) html = replaceAllLiteral(html, oldValue, newValue);

  html = normalizeJsonLd(html);
  return html;
}

async function rewriteHtml(context, transform) {
  const response = await context.next();
  const type = response.headers.get("content-type") || "";
  if (!type.toLowerCase().includes("text/html")) return response;

  const body = transform(await response.text());
  const headers = new Headers(response.headers);
  headers.delete("content-length");
  headers.delete("etag");
  headers.set("cache-control", "no-store, max-age=0");
  headers.set("x-oolita-textile", "single-blaster-v1");
  return new Response(body, { status: response.status, statusText: response.statusText, headers });
}

export async function onRequest(context) {
  const path = new URL(context.request.url).pathname;
  if (path === PAGE_PATH || path === PAGE_PATH.slice(0, -1)) {
    return rewriteHtml(context, normalizeTshirtPage);
  }
  if (path === INDEX_PATH || path === INDEX_PATH.slice(0, -1)) {
    return rewriteHtml(context, (html) => replaceAllLiteral(html, "White, two unisex cuts: 180 gsm regular or 200 gsm heavy oversized.", "White, 200 gsm organic cotton, an oversized unisex fit."));
  }
  return context.next();
}
