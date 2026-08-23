# OOLITA final production audit
Generated: 2026-08-23T13:42:20.522Z
Target main: 3d9caa9a1b8e763bd3be5a921963e942fb627c22

## deployment
exact_main_is_production: PASS — {"target":"3d9caa9a1b8e763bd3be5a921963e942fb627c22","latest":{"id":"12c789b4-a31f-4d44-93d5-491e4eb92cae","url":"https://12c789b4.oolita.pages.dev","environment":"production","created_on":"2026-08-23T13:42:10.405338Z","status":"success","branch":"main","commit_hash":"3d9caa9a1b8e763bd3be5a921963e942fb627c22","commit_message":"Make production date normalization idempotent","aliases":["https://oolita.es","https://www.oolita.es"]}}
production_branch_main: PASS — main
latest_main_live_fingerprint: PASS — Latest-main homepage overlay-reset marker is live in EN and ES

## cloudflare
d1_binding: PASS — {"OOLITA_SUBSCRIBERS":{"id":"05b1cd1d-52fd-4a11-8142-13ab92a2c712"}}
tracing_observability_clean: PASS — No Pages production observability/tracing field
wrangler_clean: PASS — wrangler.toml has D1 production binding and no [observability] table
live_d1_health: PASS — HTTP 204

## corrections
english_dates: PASS — {"sample":"til the digital path opens. 22 SUNDAYS 22 DOMINGOS THE 3D WORLD OPENS 3 Jan 2027 00:00 CET 132 DAYS / DÍAS 09 HOURS / HORAS 17 MIN 37 SEC / SEG 22 SUNDAYS The same path, "}
follow_loading_honeypot: PASS
homepage_opening: PASS
fable_cat: PASS
free_3_january_reading: PASS
exists_now: PASS
bilingual_excerpt_illustration: PASS
sundays_archive: PASS
navigation_hierarchy: PASS — {"en":["Read and understand","Elsewhere","Project"],"es":["Leer y entender","Fuera de este sitio","Proyecto"]}

## mobile
english_2027_line_gone: PASS — {"text":"2027","textDecoration":"none","background":"rgb(241, 231, 212)","before":"none","after":"none","rect":{"left":94.09375,"right":174.09375,"top":1568.890625,"bottom":1600.796875,"width":80,"height":31.90625}}
english_spacing_overflow: FAIL — [{"width":360,"innerWidth":360,"scrollWidth":360,"outside":[{"tag":"A","cls":"salta","text":"Skip to content","left":-9999,"right":-9884}],"collisions":[]},{"width":390,"innerWidth":390,"scrollWidth":390,"outside":[{"tag":"A","cls":"salta","text":"Skip to content","left":-9999,"right":-9884}],"collisions":[]},{"width":412,"innerWidth":412,"scrollWidth":412,"outside":[{"tag":"A","cls":"salta","text":"Skip to content","left":-9999,"right":-9884}],"collisions":[]}]
spanish_spacing_overflow: FAIL — [{"width":360,"innerWidth":360,"scrollWidth":360,"outside":[{"tag":"A","cls":"salta","text":"Saltar al contenido","left":-9999,"right":-9858}],"collisions":[]},{"width":390,"innerWidth":390,"scrollWidth":390,"outside":[{"tag":"A","cls":"salta","text":"Saltar al contenido","left":-9999,"right":-9858}],"collisions":[]},{"width":412,"innerWidth":412,"scrollWidth":412,"outside":[{"tag":"A","cls":"salta","text":"Saltar al contenido","left":-9999,"right":-9858}],"collisions":[]}]
footer_layout: PASS — [{"width":360,"footer":{"left":0,"right":360,"top":9245.78125,"bottom":9490.234375,"width":360,"height":244.453125},"overlaps":[]},{"width":390,"footer":{"left":0,"right":390,"top":9258.09375,"bottom":9502.546875,"width":390,"height":244.453125},"overlaps":[]},{"width":412,"footer":{"left":0,"right":412,"top":9169.0625,"bottom":9399.328125,"width":412,"height":230.265625},"overlaps":[]},{"width":360,"footer":{"left":0,"right":360,"top":9552.203125,"bottom":9850.4375,"width":360,"height":298.234375},"overlaps":[]},{"width":390,"footer":{"left":0,"right":390,"top":9459.90625,"bottom":9690.171875,"width":390,"height":230.265625},"overlaps":[]},{"width":412,"footer":{"left":0,"right":412,"top":9412.75,"bottom":9643.015625,"width":412,"height":230.265625},"overlaps":[]}]

## signup
invalid_email: PASS — {"status":400,"body":{"ok":false,"error":"invalid_email"}}
honeypot: PASS — {"response":{"status":200,"body":{"ok":true,"state":"recorded"}},"stored":0}
loading_state: PASS — {"status":"List active · choose what you want to follow.","statusHidden":false,"buttonDisabled":false,"honeypotHidden":true}
saving_state: PASS — {"status":"Saving…","disabled":true}
success_state: PASS — {"status":"You’re in · thank you for following OOLITA.","disabled":false}
valid_signup: PASS — {"row":{"email":"oolita-final-audit-32643120020@example.com","status":"active","verified_at":null,"unsubscribed_at":null,"language":"en","interests":"[\"book\",\"field\"]"}}
existing_subscriber: PASS — {"status":200,"body":{"ok":true,"state":"active"}}
error_state: PASS — {"status":"We could not save this. Try again or write to oolita@tutamail.com.","disabled":false}
double_opt_in_enabled: FAIL — {"status":"active","verified_at":null,"note":"Current implementation is single opt-in if status is active immediately with verified_at NULL."}

## books
page_count_48: PASS — {"en":[{"k":"Pages","v":"48"},{"k":"Languages","v":"Bilingual ES / EN"},{"k":"Format","v":"210 × 210 mm · hardcover"},{"k":"Author","v":"Raquel Costantini"},{"k":"Publisher","v":"Vestini Tribe"},{"k":"Year","v":"2027"},{"k":"Printing","v":"On demand, one at a time"}],"es":[{"k":"Páginas","v":"48"},{"k":"Idiomas","v":"Bilingüe ES / EN"},{"k":"Formato","v":"210 × 210 mm · tapa dura"},{"k":"Autora","v":"Raquel Costantini"},{"k":"Editorial","v":"Vestini Tribe"},{"k":"Año","v":"2027"},{"k":"Impresión","v":"Bajo demanda, uno a uno"}]}
bilingual_excerpt: PASS
cat_fable: PASS
dates_availability: PASS — {"en":"actly what the text asks for. How long it takes to arrive. The print edition comes out on 31 January 2027, a month after the three-dimensional world opens. That order is deliberate: first you walk the labyrinth, then you hold the book.","es":"acio, que es justo lo que pide el texto. Qué tarda en llegar. La edición en papel sale el 31 de enero de 2027, un mes después de que abra el mundo en tres dimensiones. Ese orden es deliberado: primero se camina el laberinto y después se ti"}
mobile_clean: FAIL — {"enOutside":[{"tag":"A","cls":"salta","text":"Skip to content","left":-9999,"right":-9884}],"esOutside":[{"tag":"A","cls":"salta","text":"Saltar al contenido","left":-9999,"right":-9858}],"enCollisions":[],"esCollisions":[]}
images_loaded: PASS — {"enBad":[],"esBad":[]}

## sundays
count_correct: PASS — {"expected":2,"en":"2","es":"2"}
dates_correct: PASS — [{"n":1,"date":"2026-08-09"},{"n":2,"date":"2026-08-16"},{"n":3,"date":"2026-08-23"},{"n":4,"date":"2026-08-30"},{"n":5,"date":"2026-09-06"},{"n":6,"date":"2026-09-13"},{"n":7,"date":"2026-09-20"},{"n":8,"date":"2026-09-27"},{"n":9,"date":"2026-10-04"},{"n":10,"date":"2026-10-11"},{"n":11,"date":"2026-10-18"},{"n":12,"date":"2026-10-25"},{"n":13,"date":"2026-11-01"},{"n":14,"date":"2026-11-08"},{"n":15,"date":"2026-11-15"},{"n":16,"date":"2026-11-22"},{"n":17,"date":"2026-11-29"},{"n":18,"date":"2026-12-06"},{"n":19,"date":"2026-12-13"},{"n":20,"date":"2026-12-20"},{"n":21,"date":"2026-12-27"},{"n":22,"date":"2027-01-03"}]
published_open: PASS — [{"n":1,"status":200,"url":"https://oolita.es/en/sundays/01-the-double/"},{"n":2,"status":200,"url":"https://oolita.es/en/sundays/02-the-cat-for-real/"}]
future_inactive: PASS — [{"n":1,"href":true},{"n":2,"href":true},{"n":3,"href":false},{"n":4,"href":false},{"n":5,"href":false},{"n":6,"href":false},{"n":7,"href":false},{"n":8,"href":false},{"n":9,"href":false},{"n":10,"href":false},{"n":11,"href":false},{"n":12,"href":false},{"n":13,"href":false},{"n":14,"href":false},{"n":15,"href":false},{"n":16,"href":false},{"n":17,"href":false},{"n":18,"href":false},{"n":19,"href":false},{"n":20,"href":false},{"n":21,"href":false},{"n":22,"href":false}]
mobile_grid: FAIL — {"en":{"left":17.15625,"right":372.84375,"top":917.515625,"bottom":1454.640625,"width":355.6875,"height":537.125},"es":{"left":17.15625,"right":372.84375,"top":917.515625,"bottom":1454.640625,"width":355.6875,"height":537.125}}

## navigation
numbers_01_14: PASS — {"missingEn":[],"missingEs":[],"en":[{"n":"01","text":"01 Los Escullos The walkable labyrinth · Cabo de Gata-Níjar →","href":"/en/labyrinth/"},{"n":"02","text":"02 22 Sundays The series archive · 9 Aug 26 → 3 Jan 27 →","href":"/en/sundays/"},{"n":"03","text":"03 Cabo de Gata Field publications, materials and collaborations →","href":"/en/cabo-de-gata/"},{"n":"04","text":"04 Editions Books, textiles and tools for looking closely","href":"/en/editions/"},{"n":"05","text":"05 What is a labyrinth One path. One centre. One return.","href":"/en/what-is-a-labyrinth/"},{"n":"06","text":"06 What is an ooid The grain of stone the project is named after","href":"/en/what-is-an-ooid/"},{"n":"07","text":"07 The posters The nine posters that opened the account","href":"/en/posters/"},{"n":"08","text":"08 Labyrinth Locator Entry in the world labyrinth directory ↗","href":"https://labyrinthlocator.org/labyrinth/oolita"},{"n":"09","text":"09 Instagram @oolita.es · one image every Sunday ↗","href":"https://www.instagram.com/oolita.es/"},{"n":"10","text":"10 Hallazgo · Art Virtual castle · free to enter · opens 16 May 27 · 19:00 CEST ↗","href":"https://hallazgo.my.canva.site/hallazgo"},{"n":"11","text":"11 Catalogue In the castle: full catalogue with a key · hardback 16 Sep 27 · public launch 19 Sep 27","href":"https://hallazgo.my.canva.site/hallazgo/catlogo"},{"n":"12","text":"12 About OOLITA Raquel Costantini · provenance and practice","href":"/en/about/"},{"n":"13","text":"13 Work with OOLITA Bookshops · education · culture · materials","href":"/en/work-with-oolita/"},{"n":"14","text":"14 Contact oolita@tutamail.com","href":"mailto:oolita@tutamail.com"}],"es":[{"n":"01","text":"01 Los Escullos El laberinto caminable · Cabo de Gata-Níjar →","href":"/laberinto/"},{"n":"02","text":"02 22 domingos El archivo de la serie · 09.08.26 → 03.01.27 →","href":"/domingos/"},{"n":"03","text":"03 Cabo de Gata Publicaciones de campo, materiales y colaboraciones →","href":"/cabo-de-gata/"},{"n":"04","text":"04 Ediciones Libros, textiles y herramientas para mirar de cerca","href":"/ediciones/"},{"n":"05","text":"05 Qué es un laberinto Un camino. Un centro. Un regreso.","href":"/que-es-un-laberinto/"},{"n":"06","text":"06 Qué es un oolito El grano de piedra que da nombre al proyecto","href":"/que-es-un-oolito/"},{"n":"07","text":"07 Los carteles Los nueve carteles de la apertura de la cuenta","href":"/carteles/"},{"n":"08","text":"08 Labyrinth Locator Ficha en el directorio mundial ↗","href":"https://labyrinthlocator.org/labyrinth/oolita"},{"n":"09","text":"09 Instagram @oolita.es · una imagen cada domingo ↗","href":"https://www.instagram.com/oolita.es/"},{"n":"10","text":"10 Hallazgo · Arte Castillo virtual · entrada libre · abre 16.05.27 · 19:00 CEST ↗","href":"https://hallazgo.my.canva.site/hallazgo"},{"n":"11","text":"11 Catálogo En el castillo: catálogo completo con clave · tapa dura 16.09.27 · presentación pública ","href":"https://hallazgo.my.canva.site/hallazgo/catlogo"},{"n":"12","text":"12 Sobre OOLITA Raquel Costantini · procedencia y práctica","href":"/sobre-oolita/"},{"n":"13","text":"13 Colaborar Librerías · educación · cultura · materiales","href":"/colaborar/"},{"n":"14","text":"14 Contacto oolita@tutamail.com","href":"mailto:oolita@tutamail.com"}]}
groups_clear: PASS — {"en":["Read and understand","Elsewhere","Project"],"es":["Leer y entender","Fuera de este sitio","Proyecto"]}

## quality
broken_internal_links: PASS — []
english_spanish_hreflang: PASS — []
seo_metadata: PASS — []
mobile_overflow: FAIL — [{"path":"/","overflow":false,"outside":[{"tag":"A","cls":"salta","text":"Saltar al contenido","left":-9999,"right":-9858}]},{"path":"/en/","overflow":false,"outside":[{"tag":"A","cls":"salta","text":"Skip to content","left":-9999,"right":-9884}]},{"path":"/ediciones/libro/","overflow":false,"outside":[{"tag":"A","cls":"salta","text":"Saltar al contenido","left":-9999,"right":-9858}]},{"path":"/en/editions/book/","overflow":false,"outside":[{"tag":"A","cls":"salta","text":"Skip to content","left":-9999,"right":-9884}]},{"path":"/domingos/","overflow":false,"outside":[{"tag":"A","cls":"salta","text":"Saltar al contenido","left":-9999,"right":-9858}]},{"path":"/en/sundays/","overflow":false,"outside":[{"tag":"A","cls":"salta","text":"Skip to content","left":-9999,"right":-9884}]},{"path":"/laberinto/","overflow":false,"outside":[{"tag":"A","cls":"salta","text":"Saltar al contenido","left":-9999,"right":-9858}]},{"path":"/en/labyrinth/","overflow":false,"outside":[{"tag":"A","cls":"salta","text":"Skip to content","left":-9999,"right":-9884}]},{"path":"/sobre-oolita/","overflow":false,"outside":[{"tag":"A","cls":"salta","text":"Saltar al contenido","left":-9999,"right":-9858}]},{"path":"/en/about/","overflow":false,"outside":[{"tag":"A","cls":"salta","text":"Skip to content","left":-9999,"right":-9884}]}]
forms_images: PASS — []
header_footer_consistency: PASS — []
javascript_clean: PASS — []
accessibility_no_serious_critical: FAIL — [{"path":"/","id":"color-contrast","impact":"serious","nodes":8,"help":"Elements must meet minimum color contrast ratio thresholds"},{"path":"/en/","id":"color-contrast","impact":"serious","nodes":8,"help":"Elements must meet minimum color contrast ratio thresholds"},{"path":"/ediciones/libro/","id":"color-contrast","impact":"serious","nodes":3,"help":"Elements must meet minimum color contrast ratio thresholds"},{"path":"/en/editions/book/","id":"color-contrast","impact":"serious","nodes":3,"help":"Elements must meet minimum color contrast ratio thresholds"},{"path":"/domingos/","id":"color-contrast","impact":"serious","nodes":68,"help":"Elements must meet minimum color contrast ratio thresholds"},{"path":"/en/sundays/","id":"color-contrast","impact":"serious","nodes":68,"help":"Elements must meet minimum color contrast ratio thresholds"}]
robots_sitemap: PASS — {"status":200}

## Errors
None