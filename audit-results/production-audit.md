# OOLITA production audit
Generated: 2026-08-23T13:29:55.303Z
Target main: 04ccf748492b8f7a741bfc5a79d809effa30688c

## Deployment
latest_main_fingerprint_live: FAIL — Unique 04ccf748 homepage overlay-reset marker present on both live homepages
cloudflare_commit_matches_main: FAIL — 5fbfa836e09a294bac22946c01f0a6c0d642c2fe

## Cloudflare
d1_binding_matches: PASS — {"OOLITA_SUBSCRIBERS":{"id":"05b1cd1d-52fd-4a11-8142-13ab92a2c712"}}
no_pages_observability_config: PASS — Pages production deployment config contains no observability field
d1_live_health: PASS — HTTP 204

## Corrections 1–9
english_dates: FAIL
follow_loading_honeypot: PASS
homepage_opening: PASS
fable_cat_explanation: PASS
free_3_january_reading: PASS
exists_now_positioning: PASS
bilingual_excerpt_illustration: PASS — Excerpt marker and cat/labyrinth image markup
sundays_archive: PASS
navigation_hierarchy: PASS

## Mobile
english_2027_clear: PASS — {"text":"2027","textDecoration":"none","bg":"rgba(0, 0, 0, 0)","before":"none","after":"none","rect":{"x":42,"right":163.484375,"width":121.484375}}
english_no_overflow: PASS — [{"width":360,"overflow":false,"scrollWidth":1280},{"width":390,"overflow":false,"scrollWidth":1280},{"width":412,"overflow":false,"scrollWidth":1280}]
spanish_no_overflow: PASS — [{"width":360,"overflow":false,"scrollWidth":1280},{"width":390,"overflow":false,"scrollWidth":1280},{"width":412,"overflow":false,"scrollWidth":1280}]
footer_layout: PASS — Footer remains within viewport at 360/390/412px

## Signup
invalid_email: PASS — {"status":400,"body":{"ok":false,"error":"invalid_email"}}
honeypot: PASS — {"response":{"status":200,"body":{"ok":true,"state":"recorded"}},"stored":0}
valid_signup: PASS — {"response":{"status":200,"body":{"ok":true,"state":"active"}},"row":{"email":"oolita-audit-32642492526@example.com","status":"active","verified_at":null,"unsubscribed_at":null,"language":"en","interests":"[\"book\",\"field\"]"}}
existing_subscriber: PASS — {"status":200,"body":{"ok":true,"state":"active"}}
double_opt_in: FAIL — Not enabled: valid consent is immediately active and verified_at remains NULL (single opt-in).
loading_runtime: PASS — {"status":"List active · choose what you want to follow.","statusHidden":false,"buttonDisabled":false,"honeypotHidden":true}
error_state: PASS — {"status":"We could not save this. Try again or write to oolita@tutamail.com.","buttonDisabled":false}

## Books
page_count_48: PASS — {"en":"48","es":"48"}
fable_copy: PASS
bilingual: PASS
dates_availability: FAIL
mobile_clean: PASS
images_loaded: PASS — {"en_bad":0,"es_bad":0}

## Sundays
count_correct: PASS
all_22_present: PASS — {"en":22,"es":22}
future_inactive: PASS — [{"n":"1","href":true},{"n":"2","href":true},{"n":"3","href":false},{"n":"4","href":false},{"n":"5","href":false},{"n":"6","href":false},{"n":"7","href":false},{"n":"8","href":false},{"n":"9","href":false},{"n":"10","href":false},{"n":"11","href":false},{"n":"12","href":false},{"n":"13","href":false},{"n":"14","href":false},{"n":"15","href":false},{"n":"16","href":false},{"n":"17","href":false},{"n":"18","href":false},{"n":"19","href":false},{"n":"20","href":false},{"n":"21","href":false},{"n":"22","href":false}]
mobile_grid_clean: PASS
published_entries_open: PASS — [{"n":"1","status":200,"url":"https://oolita.es/en/sundays/01-the-double/"},{"n":"2","status":200,"url":"https://oolita.es/en/sundays/02-the-cat-for-real/"}]

## Navigation
groups_present: PASS
numbers_01_14_preserved: FAIL — {"en":["04","05","06","07","08","09","10","11","12","13","14"],"es":["04","05","06","07","08","09","10","11","12","13","14"]}

## Quality
broken_internal_links: PASS — []
seo_metadata: PASS — []
mobile_overflow: PASS — []
images: PASS — []
javascript_console: PASS — []
accessibility_serious_critical: PASS — []
robots_sitemap: PASS — {"status":200}

## Errors
None