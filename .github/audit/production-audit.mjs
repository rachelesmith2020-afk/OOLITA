import { chromium } from 'playwright';
import AxeBuilder from '@axe-core/playwright';
import fs from 'node:fs/promises';

const BASE = 'https://oolita.es';
const ACCOUNT = process.env.CLOUDFLARE_ACCOUNT_ID;
const TOKEN = process.env.CLOUDFLARE_API_TOKEN;
const DB = '05b1cd1d-52fd-4a11-8142-13ab92a2c712';
const TARGET = process.env.TARGET_MAIN_SHA;
const RUN = process.env.GITHUB_RUN_ID || String(Date.now());
const auditEmail = `oolita-audit-${RUN}@example.com`;
const botEmail = `oolita-audit-bot-${RUN}@example.com`;
const report = { generated_at: new Date().toISOString(), target_main_sha: TARGET, deployment: {}, cloudflare: {}, corrections: {}, mobile: {}, signup: {}, books: {}, sundays: {}, navigation: {}, quality: {}, errors: [] };

const cleanText = s => (s || '').replace(/\s+/g, ' ').trim();
const pass = (obj, key, ok, detail = null) => { obj[key] = { pass: Boolean(ok), detail }; return Boolean(ok); };
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function cf(path, options = {}) {
  const r = await fetch(`https://api.cloudflare.com/client/v4${path}`, {
    ...options,
    headers: { Authorization: `Bearer ${TOKEN}`, 'Content-Type': 'application/json', ...(options.headers || {}) },
  });
  const text = await r.text();
  let body = null;
  try { body = JSON.parse(text); } catch { body = { raw: text.slice(0, 500) }; }
  if (!r.ok || body?.success === false) throw new Error(`Cloudflare ${r.status}: ${JSON.stringify(body?.errors || body).slice(0,500)}`);
  return body.result;
}

async function d1(sql, params = []) {
  const result = await cf(`/accounts/${ACCOUNT}/d1/database/${DB}/query`, { method: 'POST', body: JSON.stringify({ sql, params }) });
  return Array.isArray(result) ? result[0] : result;
}

function deploymentSummary(d) {
  if (!d) return null;
  return {
    id: d.id, url: d.url, environment: d.environment, created_on: d.created_on,
    latest_stage: d.latest_stage?.status || null,
    aliases: d.aliases || [],
    branch: d.deployment_trigger?.metadata?.branch || null,
    commit_hash: d.deployment_trigger?.metadata?.commit_hash || null,
    commit_message: d.deployment_trigger?.metadata?.commit_message || null,
  };
}

async function liveSource(path) {
  const r = await fetch(BASE + path, { redirect: 'follow', headers: { 'User-Agent': 'OOLITA-production-audit/1.0' } });
  return { status: r.status, url: r.url, html: await r.text(), headers: Object.fromEntries([...r.headers].filter(([k]) => ['content-type','cache-control','cf-cache-status','last-modified'].includes(k.toLowerCase()))) };
}

async function inspectPage(browser, path, viewport = { width: 390, height: 844 }, axe = true) {
  const page = await browser.newPage({ viewportSize: viewport });
  const consoleErrors = [];
  const pageErrors = [];
  page.on('console', m => { if (m.type() === 'error') consoleErrors.push(m.text().slice(0,300)); });
  page.on('pageerror', e => pageErrors.push(String(e).slice(0,300)));
  const resp = await page.goto(BASE + path, { waitUntil: 'networkidle', timeout: 45000 });
  await sleep(250);
  const data = await page.evaluate(() => {
    const rect = el => { if (!el) return null; const r = el.getBoundingClientRect(); return { x:r.x,y:r.y,width:r.width,height:r.height,right:r.right,bottom:r.bottom }; };
    const imgs = [...document.images].map(i => ({ src:i.currentSrc||i.src, complete:i.complete, naturalWidth:i.naturalWidth, alt:i.getAttribute('alt') }));
    const canonical = document.querySelector('link[rel="canonical"]')?.href || null;
    const alternates = [...document.querySelectorAll('link[rel="alternate"][hreflang]')].map(x => ({lang:x.hreflang,href:x.href}));
    return {
      title: document.title,
      description: document.querySelector('meta[name="description"]')?.content || null,
      canonical, alternates,
      h1_count: document.querySelectorAll('h1').length,
      scrollWidth: document.documentElement.scrollWidth,
      innerWidth: window.innerWidth,
      overflow: document.documentElement.scrollWidth > window.innerWidth + 1,
      header: rect(document.querySelector('header')),
      footer: rect(document.querySelector('footer,.pie')),
      images: imgs,
      bodyText: document.body.innerText.replace(/\s+/g,' ').trim(),
      styleMarkers: [...document.querySelectorAll('style[id]')].map(x=>x.id),
      sundayCount: document.querySelector('[data-sunday-count]')?.textContent?.trim() || null,
      sundayTiles: [...document.querySelectorAll('[data-sunday-tile]')].map(x=>({n:x.dataset.sunday,date:x.dataset.date,href:x.getAttribute('href'),disabled:x.getAttribute('aria-disabled'),published:x.classList.contains('is-published'),current:x.classList.contains('is-current')})),
      menuGroups: [...document.querySelectorAll('.menu-group-label')].map(x=>x.textContent.trim()),
      numbered: [...document.querySelectorAll('a.fila')].map(a=>({text:a.innerText.replace(/\s+/g,' ').trim(),href:a.getAttribute('href')})),
      bookSpec: [...document.querySelectorAll('.k')].map(k=>({k:k.textContent.trim(),v:k.nextElementSibling?.textContent?.trim()||''})),
      excerpt: Boolean(document.querySelector('[data-book-excerpt],.book-excerpt,.oolita-book-excerpt')),
      excerptImages: [...document.querySelectorAll('img')].filter(i => /gato|cat|laberinto|labyrinth/i.test(`${i.alt||''} ${i.src||''}`)).map(i=>({alt:i.alt,src:i.currentSrc||i.src,naturalWidth:i.naturalWidth})),
    };
  });
  if (path === '/en/') {
    data.year2027 = await page.evaluate(() => {
      const e = document.querySelector('.mobile-2027-clear'); if (!e) return null;
      const c = getComputedStyle(e), b = getComputedStyle(e,'::before'), a=getComputedStyle(e,'::after'), r=e.getBoundingClientRect();
      return { text:e.textContent, textDecoration:c.textDecorationLine, bg:c.backgroundColor, before:b.content, after:a.content, rect:{x:r.x,right:r.right,width:r.width} };
    });
  }
  if (axe) {
    try {
      const ax = await new AxeBuilder({ page }).analyze();
      data.axe = { count: ax.violations.length, violations: ax.violations.map(v=>({id:v.id,impact:v.impact,nodes:v.nodes.length})) };
    } catch (e) { data.axe = { error: String(e) }; }
  }
  data.http_status = resp?.status() || null;
  data.console_errors = consoleErrors;
  data.page_errors = pageErrors;
  await page.close();
  return data;
}

try {
  if (!ACCOUNT || !TOKEN) throw new Error('Missing Cloudflare credentials in workflow environment');

  // Cloudflare control-plane verification.
  const project = await cf(`/accounts/${ACCOUNT}/pages/projects/oolita`);
  const deployments = await cf(`/accounts/${ACCOUNT}/pages/projects/oolita/deployments?env=production&per_page=10`);
  const latest = Array.isArray(deployments) ? deployments[0] : null;
  report.deployment.latest_production = deploymentSummary(latest);
  report.deployment.production_branch = project.production_branch || null;
  report.cloudflare.pages = {
    name: project.name,
    production_branch: project.production_branch,
    canonical_deployment: deploymentSummary(project.canonical_deployment),
    compatibility_date: project.deployment_configs?.production?.compatibility_date || null,
    compatibility_flags: project.deployment_configs?.production?.compatibility_flags || [],
    d1_databases: project.deployment_configs?.production?.d1_databases || null,
    analytics_engine_datasets: project.deployment_configs?.production?.analytics_engine_datasets || null,
  };
  const d1BindingString = JSON.stringify(report.cloudflare.pages.d1_databases || {});
  pass(report.cloudflare, 'd1_binding_matches', d1BindingString.includes('OOLITA_SUBSCRIBERS') && d1BindingString.includes(DB), report.cloudflare.pages.d1_databases);
  pass(report.cloudflare, 'no_pages_observability_config', !JSON.stringify(project.deployment_configs?.production || {}).toLowerCase().includes('observability'), 'Pages production deployment config contains no observability field');

  const health = await fetch(`${BASE}/api/subscribe?health=1`, { redirect:'follow' });
  pass(report.cloudflare, 'd1_live_health', health.status === 204, `HTTP ${health.status}`);

  // Live source fingerprints and reader-facing corrections.
  const [esSrc,enSrc,esBookSrc,enBookSrc,esSunSrc,enSunSrc] = await Promise.all(['/','/en/','/ediciones/libro/','/en/editions/book/','/domingos/','/en/sundays/'].map(liveSource));
  pass(report.deployment, 'latest_main_fingerprint_live', enSrc.html.includes('oolita-home-overlay-reset-v1') && esSrc.html.includes('oolita-home-overlay-reset-v1'), 'Unique 04ccf748 homepage overlay-reset marker present on both live homepages');
  const cfCommit = latest?.deployment_trigger?.metadata?.commit_hash || project.canonical_deployment?.deployment_trigger?.metadata?.commit_hash || null;
  pass(report.deployment, 'cloudflare_commit_matches_main', !cfCommit ? null : cfCommit === TARGET, cfCommit || 'Cloudflare API did not expose a commit hash');

  const corr = report.corrections;
  pass(corr,'english_dates', enSrc.html.includes('3 Jan 2027') && !enSrc.html.includes('03.01.2027'));
  pass(corr,'follow_loading_honeypot', enSrc.html.includes('data-follow-status aria-live="polite" hidden') && enSrc.html.includes('class="follow-honeypot" hidden aria-hidden="true"') && esSrc.html.includes('class="follow-honeypot" hidden aria-hidden="true"'));
  pass(corr,'homepage_opening', enSrc.html.includes('OOLITA begins with a three-metre classical labyrinth') && esSrc.html.includes('OOLITA comienza con un laberinto clásico de tres metros'));
  pass(corr,'fable_cat_explanation', enBookSrc.html.includes('The fable follows a real cat') && esBookSrc.html.includes('La fábula sigue a un gato de verdad'));
  pass(corr,'free_3_january_reading', enSrc.html.includes('From 3 January the whole book can be read free inside the 3D world') && esSrc.html.includes('Desde el 3 de enero se podrá leer entero, gratis, dentro del mundo 3D'));
  pass(corr,'exists_now_positioning', enSrc.html.includes('The stone labyrinth is already at Los Escullos') && esSrc.html.includes('El laberinto de piedra ya está en Los Escullos'));
  pass(corr,'bilingual_excerpt_illustration', enBookSrc.html.includes('oolita-book-excerpt') && esBookSrc.html.includes('oolita-book-excerpt') && /<img[^>]+(?:cat|gato|labyrinth|laberinto)/i.test(enBookSrc.html + esBookSrc.html), 'Excerpt marker and cat/labyrinth image markup');
  pass(corr,'sundays_archive', enSunSrc.html.includes('id="sunday-field"') && esSunSrc.html.includes('id="sunday-field"') && enSunSrc.html.includes('the archive grows each Sunday'));
  pass(corr,'navigation_hierarchy', enSrc.html.includes('Read and understand') && enSrc.html.includes('Elsewhere') && enSrc.html.includes('Project') && esSrc.html.includes('Leer y entender') && esSrc.html.includes('Fuera de este sitio'));

  const browser = await chromium.launch({ headless: true });
  try {
    // Representative live mobile audits.
    for (const [lang,path] of [['en','/en/'],['es','/']]) {
      const widths = [360,390,412];
      report.mobile[lang] = [];
      for (const width of widths) {
        const d = await inspectPage(browser,path,{width,height:844}, width === 390);
        report.mobile[lang].push({ width, status:d.http_status, overflow:d.overflow, scrollWidth:d.scrollWidth, innerWidth:d.innerWidth, footer:d.footer, header:d.header, year2027:d.year2027 || null, axe:d.axe || null, console_errors:d.console_errors, page_errors:d.page_errors });
      }
    }
    const en390 = report.mobile.en.find(x=>x.width===390);
    pass(report.mobile,'english_2027_clear', en390?.year2027?.text === '2027' && en390?.year2027?.textDecoration === 'none' && ['none','normal'].includes(en390?.year2027?.before) && ['none','normal'].includes(en390?.year2027?.after), en390?.year2027 || null);
    pass(report.mobile,'english_no_overflow', report.mobile.en.every(x=>!x.overflow), report.mobile.en.map(x=>({width:x.width,overflow:x.overflow,scrollWidth:x.scrollWidth})));
    pass(report.mobile,'spanish_no_overflow', report.mobile.es.every(x=>!x.overflow), report.mobile.es.map(x=>({width:x.width,overflow:x.overflow,scrollWidth:x.scrollWidth})));
    pass(report.mobile,'footer_layout', [...report.mobile.en,...report.mobile.es].every(x=>x.footer && x.footer.width <= x.innerWidth + 1 && x.footer.x >= -1), 'Footer remains within viewport at 360/390/412px');

    // Book presentation and content.
    const enBook = await inspectPage(browser,'/en/editions/book/',{width:390,height:844});
    const esBook = await inspectPage(browser,'/ediciones/libro/',{width:390,height:844});
    report.books.mobile = { en: {status:enBook.http_status,overflow:enBook.overflow,axe:enBook.axe}, es:{status:esBook.http_status,overflow:esBook.overflow,axe:esBook.axe} };
    const enPages = enBook.bookSpec.find(x=>/^pages$/i.test(x.k))?.v;
    const esPages = esBook.bookSpec.find(x=>/^páginas$/i.test(x.k))?.v;
    pass(report.books,'page_count_48', enPages === '48' && esPages === '48', {en:enPages,es:esPages});
    pass(report.books,'fable_copy', enBook.bodyText.includes('The fable follows a real cat') && esBook.bodyText.includes('La fábula sigue a un gato de verdad'));
    pass(report.books,'bilingual', /Spanish and English at once/i.test(enBook.bodyText) && /español y en inglés a la vez/i.test(esBook.bodyText));
    pass(report.books,'dates_availability', enBook.bodyText.includes('31 Jan 27') && !enBook.bodyText.includes('31.01.27'));
    pass(report.books,'mobile_clean', !enBook.overflow && !esBook.overflow && enBook.http_status===200 && esBook.http_status===200);
    pass(report.books,'images_loaded', [...enBook.images,...esBook.images].every(i=>i.complete && i.naturalWidth>0), {en_bad:enBook.images.filter(i=>!i.complete||i.naturalWidth===0).length,es_bad:esBook.images.filter(i=>!i.complete||i.naturalWidth===0).length});

    // Sundays accumulating archive.
    const enSun = await inspectPage(browser,'/en/sundays/',{width:390,height:844});
    const esSun = await inspectPage(browser,'/domingos/',{width:390,height:844});
    const expectedPublished = Date.now() < Date.parse('2026-08-23T17:00:00Z') ? 2 : 3;
    const active = enSun.sundayTiles.filter(t=>t.href && t.published);
    report.sundays = { expected_published_now: expectedPublished, live_count_en: Number(enSun.sundayCount), live_count_es:Number(esSun.sundayCount), active:active.map(t=>({n:t.n,date:t.date,href:t.href})), inactive:enSun.sundayTiles.filter(t=>!t.href).map(t=>t.n), mobile_overflow_en:enSun.overflow,mobile_overflow_es:esSun.overflow,axe_en:enSun.axe,axe_es:esSun.axe };
    pass(report.sundays,'count_correct', Number(enSun.sundayCount)===expectedPublished && Number(esSun.sundayCount)===expectedPublished);
    pass(report.sundays,'all_22_present', enSun.sundayTiles.length===22 && esSun.sundayTiles.length===22, {en:enSun.sundayTiles.length,es:esSun.sundayTiles.length});
    pass(report.sundays,'future_inactive', enSun.sundayTiles.every(t=> Number(t.n)<=expectedPublished ? Boolean(t.href) : !t.href), enSun.sundayTiles.map(t=>({n:t.n,href:Boolean(t.href)})));
    pass(report.sundays,'mobile_grid_clean', !enSun.overflow && !esSun.overflow);
    const activeStatuses = [];
    for (const t of active) { const r=await fetch(new URL(t.href,BASE),{redirect:'follow'}); activeStatuses.push({n:t.n,status:r.status,url:r.url}); }
    report.sundays.active_statuses = activeStatuses;
    pass(report.sundays,'published_entries_open', activeStatuses.every(x=>x.status>=200&&x.status<400), activeStatuses);

    // Navigation hierarchy: preserve numbered run and grouping.
    const enHome = await inspectPage(browser,'/en/',{width:1280,height:900},false);
    const esHome = await inspectPage(browser,'/',{width:1280,height:900},false);
    report.navigation = { en_groups:enHome.menuGroups, es_groups:esHome.menuGroups, en_numbered:enHome.numbered, es_numbered:esHome.numbered };
    const nums = arr => arr.map(x => (x.text.match(/^(\d{2})\b/)||[])[1]).filter(Boolean);
    const enNums=nums(enHome.numbered), esNums=nums(esHome.numbered);
    pass(report.navigation,'groups_present', ['Read and understand','Elsewhere','Project'].every(x=>enHome.menuGroups.includes(x)) && ['Leer y entender','Fuera de este sitio','Proyecto'].every(x=>esHome.menuGroups.includes(x)));
    pass(report.navigation,'numbers_01_14_preserved', Array.from({length:14},(_,i)=>String(i+1).padStart(2,'0')).every(n=>enNums.includes(n)&&esNums.includes(n)), {en:enNums,es:esNums});

    // Signup: API behavior + browser states. Cleanup is guaranteed below.
    const apiPost = async payload => {
      const r=await fetch(`${BASE}/api/subscribe`,{method:'POST',headers:{'Content-Type':'application/json','Origin':BASE},body:JSON.stringify(payload)});
      let body={}; try{body=await r.json();}catch{} return {status:r.status,body};
    };
    const invalid=await apiPost({email:'not-an-email',language:'en',consent:true,website:'',source_path:'/en/',interests:[]});
    const bot=await apiPost({email:botEmail,language:'en',consent:true,website:'https://bot.invalid',source_path:'/en/',interests:[]});
    const valid=await apiPost({email:auditEmail,language:'en',consent:true,website:'',source_path:'/en/',interests:['book']});
    const existing=await apiPost({email:auditEmail,language:'en',consent:true,website:'',source_path:'/en/',interests:['book','field']});
    const row=(await d1('SELECT email,status,verified_at,unsubscribed_at,language,interests FROM subscribers WHERE email = ?', [auditEmail]))?.results || [];
    const botRow=(await d1('SELECT email FROM subscribers WHERE email = ?', [botEmail]))?.results || [];
    report.signup.api = { invalid, bot, valid, existing, stored_row:row, bot_stored_count:botRow.length };
    pass(report.signup,'invalid_email', invalid.status===400 && invalid.body?.error==='invalid_email',invalid);
    pass(report.signup,'honeypot', bot.status===200 && bot.body?.state==='recorded' && botRow.length===0,{response:bot,stored:botRow.length});
    pass(report.signup,'valid_signup', valid.status===200 && valid.body?.state==='active' && row[0]?.status==='active',{response:valid,row:row[0]||null});
    pass(report.signup,'existing_subscriber', existing.status===200 && existing.body?.state==='active',existing);
    pass(report.signup,'double_opt_in', false, 'Not enabled: valid consent is immediately active and verified_at remains NULL (single opt-in).');

    const formPage=await browser.newPage({viewportSize:{width:390,height:844}});
    await formPage.goto(`${BASE}/en/`,{waitUntil:'networkidle'});
    const runtime=await formPage.evaluate(()=>({status:document.querySelector('[data-follow-status]')?.textContent?.trim(),statusHidden:document.querySelector('[data-follow-status]')?.hidden,buttonDisabled:document.querySelector('.follow-submit')?.disabled,honeypotHidden:document.querySelector('.follow-honeypot')?.hidden}));
    report.signup.runtime_health_state=runtime;
    pass(report.signup,'loading_runtime', runtime.status==='List active · choose what you want to follow.' && runtime.statusHidden===false && runtime.buttonDisabled===false && runtime.honeypotHidden===true,runtime);
    await formPage.route('**/api/subscribe', async route => {
      if (route.request().method()==='POST') return route.fulfill({status:500,contentType:'application/json',body:JSON.stringify({ok:false,error:'audit_simulated'})});
      return route.continue();
    });
    await formPage.fill('input[name="email"]','ui-error-audit@example.com');
    await formPage.check('input[name="consent"]');
    await formPage.click('button[type="submit"]');
    await formPage.waitForFunction(()=>document.querySelector('[data-follow-status]')?.textContent?.includes('We could not save this'));
    const errorState=await formPage.evaluate(()=>({status:document.querySelector('[data-follow-status]')?.textContent?.trim(),buttonDisabled:document.querySelector('.follow-submit')?.disabled}));
    report.signup.ui_error_state=errorState;
    pass(report.signup,'error_state', /We could not save this/.test(errorState.status||'') && errorState.buttonDisabled===false,errorState);
    await formPage.close();

    // Site-wide internal link, SEO, images and representative accessibility checks.
    const sitemapResp=await fetch(`${BASE}/sitemap.xml`); const sitemapText=await sitemapResp.text();
    const locs=[...sitemapText.matchAll(/<loc>\s*([^<]+)\s*<\/loc>/gi)].map(m=>m[1].trim());
    const internalStatuses=[];
    for (const url of locs) {
      try { const r=await fetch(url,{redirect:'follow'}); internalStatuses.push({url,status:r.status,final:r.url}); } catch(e){ internalStatuses.push({url,status:0,error:String(e).slice(0,200)}); }
    }
    const keyPages=['/','/en/','/ediciones/libro/','/en/editions/book/','/domingos/','/en/sundays/','/laberinto/','/en/labyrinth/'];
    const representative=[];
    for (const path of keyPages) {
      const d=await inspectPage(browser,path,{width:390,height:844});
      representative.push({path,status:d.http_status,title:Boolean(d.title),description:Boolean(d.description),canonical:d.canonical,hreflang:d.alternates,h1_count:d.h1_count,overflow:d.overflow,bad_images:d.images.filter(i=>!i.complete||i.naturalWidth===0).length,missing_alt:d.images.filter(i=>i.alt===null).length,axe:d.axe,console_errors:d.console_errors,page_errors:d.page_errors});
    }
    const robots=await fetch(`${BASE}/robots.txt`); const robotsText=await robots.text();
    report.quality = { sitemap_status:sitemapResp.status,sitemap_count:locs.length,internal_statuses:internalStatuses,representative,robots_status:robots.status,robots_has_sitemap:/sitemap:/i.test(robotsText) };
    pass(report.quality,'broken_internal_links', internalStatuses.every(x=>x.status>=200&&x.status<400), internalStatuses.filter(x=>x.status<200||x.status>=400));
    pass(report.quality,'seo_metadata', representative.every(x=>x.title&&x.description&&x.canonical&&x.hreflang.length>=2), representative.filter(x=>!x.title||!x.description||!x.canonical||x.hreflang.length<2));
    pass(report.quality,'mobile_overflow', representative.every(x=>!x.overflow), representative.filter(x=>x.overflow));
    pass(report.quality,'images', representative.every(x=>x.bad_images===0&&x.missing_alt===0), representative.filter(x=>x.bad_images||x.missing_alt));
    pass(report.quality,'javascript_console', representative.every(x=>x.console_errors.length===0&&x.page_errors.length===0), representative.filter(x=>x.console_errors.length||x.page_errors.length));
    const serious = representative.flatMap(x=>(x.axe?.violations||[]).filter(v=>['serious','critical'].includes(v.impact||'')).map(v=>({path:x.path,...v})));
    pass(report.quality,'accessibility_serious_critical', serious.length===0, serious);
    pass(report.quality,'robots_sitemap', robots.status===200 && /sitemap:/i.test(robotsText),{status:robots.status});
  } finally {
    await browser.close();
  }
} catch (e) {
  report.errors.push(String(e?.stack || e));
} finally {
  try { if (ACCOUNT && TOKEN) await d1('DELETE FROM subscribers WHERE email IN (?, ?)', [auditEmail, botEmail]); } catch (e) { report.errors.push(`D1 cleanup failed: ${String(e)}`); }
  await fs.mkdir('audit-results',{recursive:true});
  await fs.writeFile('audit-results/production-audit.json', JSON.stringify(report,null,2));
  const flatten = (obj,prefix='') => Object.entries(obj||{}).flatMap(([k,v]) => v && typeof v==='object' && 'pass' in v ? [`${prefix}${k}: ${v.pass===true?'PASS':v.pass===false?'FAIL':'UNKNOWN'}${v.detail?` — ${typeof v.detail==='string'?v.detail:JSON.stringify(v.detail)}`:''}`] : []);
  const summary=[
    `# OOLITA production audit`,
    `Generated: ${report.generated_at}`,
    `Target main: ${TARGET}`,
    '',
    '## Deployment',...flatten(report.deployment),
    '', '## Cloudflare',...flatten(report.cloudflare),
    '', '## Corrections 1–9',...flatten(report.corrections),
    '', '## Mobile',...flatten(report.mobile),
    '', '## Signup',...flatten(report.signup),
    '', '## Books',...flatten(report.books),
    '', '## Sundays',...flatten(report.sundays),
    '', '## Navigation',...flatten(report.navigation),
    '', '## Quality',...flatten(report.quality),
    '', '## Errors', ...(report.errors.length?report.errors:['None'])
  ].join('\n');
  await fs.writeFile('audit-results/production-audit.md', summary);
}
