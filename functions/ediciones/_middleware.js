const PAGE_PATH = "/ediciones/camiseta/";
const INDEX_PATH = "/ediciones/";

const SINGLE_TITLE = "Camiseta OOLITA — Stanley/Stella Blaster 2.0 · OOLITA";
const SINGLE_DESCRIPTION = "Primera edición textil OOLITA: Stanley/Stella Blaster 2.0 blanca, 200 g/m² de algodón orgánico y corte oversized unisex. Bajo demanda.";

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
    if (id === "https://oolita.es/ediciones/camiseta/#webpage") {
      data.name = SINGLE_TITLE;
      data.description = SINGLE_DESCRIPTION;
    }
    if (id === "https://oolita.es/ediciones/camiseta/#producto") {
      data["@type"] = "Product";
      data.name = "OOLITA · camiseta Blaster 2.0";
      data.description = SINGLE_DESCRIPTION;
      data.sku = "OOLITA-UK-OVERSIZED-WHITE";
      data.model = "Stanley/Stella Blaster 2.0 STTU959";
      data.material = "100% algodón orgánico peinado e hilado en anillo";
      data.size = "XXS–3XL";
      data.color = "Blanco";
      data.releaseDate = "2027-04-11";
      data.brand = { "@type": "Brand", name: "OOLITA" };
      delete data.productGroupID;
      delete data.hasVariant;
    }
    return `<script${before}type="application/ld+json"${after}>${JSON.stringify(data)}</script>`;
  });
}

function normalizeTshirtPage(html) {
  html = replaceAllLiteral(html, "Camiseta OOLITA — regular y heavy oversized · OOLITA", SINGLE_TITLE);
  html = replaceAllLiteral(html, "Primera edición textil OOLITA: RE-Creator Stanley/Stella de 180 g/m² regular o Blaster 2.0 de 200 g/m² heavy oversized, bajo demanda.", SINGLE_DESCRIPTION);
  html = replaceAllLiteral(html, "Camiseta blanca Stanley/Stella Blaster 2.0, opción heavy oversized, sin el diseño", "Camiseta blanca Stanley/Stella Blaster 2.0, corte oversized unisex, sin el diseño");
  html = replaceAllLiteral(html, "Blanca, un diseño OOLITA y dos cortes unisex: opción regular de 180 g/m² y opción heavy oversized de 200 g/m². Los detalles y la historia del diseño se irán contando domingo a domingo hasta la primavera.", "Blanca, de algodón orgánico de 200 g/m² y corte oversized unisex. Los detalles y la historia del diseño se irán contando domingo a domingo hasta la primavera.");
  html = replaceAllLiteral(html, "Qué prendas son.", "Qué prenda es.");
  html = replaceAllLiteral(html, "Hay dos opciones Stanley/Stella. Regular es la RE-Creator STTU787: 180 g/m², corte medio, 50% algodón reciclado y 50% algodón orgánico, fabricada con recortes de algodón orgánico de la propia marca. Heavy Oversized es la Blaster 2.0 STTU959: 200 g/m², 100% algodón orgánico peinado e hilado en anillo, corte oversized con hombros caídos y cuello alto de canalé 1x1. Ambas son unisex y están disponibles de XXS a 3XL.", "Es una Stanley/Stella Blaster 2.0, no una camiseta genérica: jersey sencillo de algodón orgánico peinado e hilado en anillo, 200 g/m². Corte oversized, manga montada, hombro caído, cuello alto de canalé 1x1, cinta interior del cuello y pespunte doble en puños y bajo. Disponible de XXS a 3XL.");
  html = replaceAllLiteral(html, "Stanley/Stella muestra la RE-Creator con credenciales GRS, OCS y OEKO-TEX, y la Blaster 2.0 con GOTS y OEKO-TEX; las fichas de ambas prendas también muestran Fair Wear. Las dos opciones mantienen el mismo criterio de trazabilidad y permiten elegir gramaje y corte.", "Stanley/Stella muestra la Blaster 2.0 con certificaciones GOTS y OEKO-TEX. Stanley/Stella es miembro de Fair Wear y sus productos figuran como PETA-Approved Vegan.");

  html = html.replace(/<div class="textile-choice-grid"[^>]*data-oolita-textile-choices="v1"[^>]*>[\s\S]*?<\/div>\s*/i, "");
  html = html.replace(/<style[^>]*data-oolita-textile-variants="v1"[^>]*>[\s\S]*?<\/style>\s*/i, "");

  const facts = new Map([
    ["Regular · RE-Creator STTU787 / Heavy Oversized · Blaster 2.0 STTU959", "Stanley/Stella Blaster 2.0"],
    ["Regular · 50% algodón reciclado + 50% orgánico / Heavy · 100% algodón orgánico peinado", "100 % algodón orgánico peinado"],
    ["Regular · 180 g/m² / Heavy Oversized · 200 g/m²", "200 g/m² · 20 singles"],
    ["Regular · corte medio unisex / Heavy Oversized · hombros caídos", "Oversized unisex · hombro caído"],
    ["Regular · cuello canalé 1x1 / Heavy Oversized · cuello alto canalé 1x1", "Alto, canalé 1x1 sin elastano"],
    ["RE-Creator · GRS · OCS · OEKO-TEX · Fair Wear / Blaster 2.0 · GOTS · OEKO-TEX · Fair Wear", "GOTS · OEKO-TEX · miembro de Fair Wear · PETA-Approved"],
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
    return rewriteHtml(context, (html) => replaceAllLiteral(html, "Blanca, dos cortes unisex: regular de 180 g/m² o heavy oversized de 200 g/m².", "Blanca, de algodón orgánico de 200 gramos, de corte oversized unisex."));
  }
  return context.next();
}
